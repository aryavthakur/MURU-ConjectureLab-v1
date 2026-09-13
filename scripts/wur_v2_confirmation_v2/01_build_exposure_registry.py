"""MSnLib confirmation study 2, step 2: the permanent exposure exclusion registry.

Structure, identity and acquisition HEADERS only. Binary peak arrays are never decoded: the only mzML access is
muru.wur_v2.external_mzml.scan_headers (arrays removed before any parameter is read). No mu, intensity, peak
count or model value is read, computed or printed. No random draw of any kind happens here; sample 1 is
identified from its tracked artifact and cross-checked against the design frame, not re-drawn.

Exclusion components (reason codes), each deduplicated per compound key, then expanded to whole scaffold groups:

  SAMPLE1_DRAW_GROUP              every compound of the 2,000 scaffold groups of burned confirmation sample 1
  DECODED_SAME_WELL_ION_0p7       compound plated in the well of a decoded spectrum with any theoretical ion
                                  ([M+H]+, NH4, Na, K, -H2O, 13C, or M+) within 0.7 Da of its selected ion
  DECODED_SAME_PLATE_ION_0p01     any compound plated anywhere on the SAME plate (library, plate_id) as a decoded
                                  well with any theoretical ion within 0.01 Da of a decoded spectrum's selected
                                  ion (carryover from earlier injections of that plate; this covers the surfaced
                                  value, whose attributed compound sits in the adjacent well of the same plate)
  COPLATED_IN_DECODED_WELL        every compound plated in a well whose mzML file had any array decoded
  DECODED_SAME_PLATE_EXTENDED_ION_5PPM  any compound on the same plate whose multiply charged, cluster, solvent or
                                  in-source ion (anchor_scope.ION_FORMS) is within 5 ppm of a decoded selected ion
                                  (review REG-1: real carryover spectra triggered on [M+2H]2+, [M+3H]3+, [M+H-NH3]+)
  SURFACED_VALUE_ATTRIBUTED_WELL  every compound plated in any well of a compound attributed (same plate, any ion,
                                  0.01 Da) to one of the three spectra whose mu was printed to the operator
  SURFACED_VALUE_ANY_LIBRARY_OWNER_5PPM  any compound in ANY library with any ion within 5 ppm of a printed
                                  spectrum's selected ion (review REG-2: one printed spectrum has an off-plate owner)
  ORPHAN_SPECTRUM_SAME_LIBRARY_OWNER_3PPM  for a decoded spectrum with no same-well or same-plate owner, any compound
                                  of the same library, any plate, with any ion within 3 ppm (review REG-6)
  HEADER_READ_WELL_STUDY1         every compound plated in any of the wells whose scan headers were parsed during
                                  study 1 (the 2,402 sample-1 transport wells and the 561 anchor wells, 2,811 local
                                  files): headers carry the outcome-adaptive Assisted collision energy and MS3+
                                  precursor m/z values, which are MS2 fragment masses (review F-MSn, REG-3)

Rejected rule, reported as a sensitivity count only: matching every decoded precursor to [M+H]+ of compounds in ANY
well of ANY library at 0.01 Da (the incident record's attribution rule). The registry review measured it against
an m/z-shifted null: for spectra with no in-well or same-plate owner, other-plate owner rates sit at null level
(same library 50 vs null 51.7; other libraries 148 vs 138), so the blanket rule adds thousands of coincidental
exclusions. It is NOT true that off-plate owners never occur (one printed spectrum has one); those cases are
covered by the narrower SURFACED and ORPHAN rules above.
  MSNLIB_ANCHOR_*                 census design/detected anchors and anchor-gate calibration keys
  MULTIMS2_ANCHOR_CALIBRATION     MultiMS2 anchor keys (decoded 2026-09-13)
  EXPOSED_POPULATION:<name>       every previously exposed MURU development/holdout/external population

Decode events reconstructed (header replay, each verified against its access record or reported count):
  E_anchor_gate_attempt1 (4 ids requested, 1 m/z array likely decoded), E_anchor_gate_attempt2 (1,935),
  E_buggy_preflight (3,366; the incident), E_fixed_preflight_rerun (1,816; its two crashed runs are prefixes).

Scaffold groups: identity.scaffold_group_v2 of every available SMILES variant of an excluded key (MERLIN rows,
v2 compounds.csv, LCSB trajectories, WUR identity, MultiMS2 populations, ENTACT mix lists), plus the census
key->scaffold map. A 12b compound is excluded if its census scaffold group is in the excluded set, or if that
group's scaffold is the same RDKit canonical tautomer as an excluded scaffold (review REG-5). MultiMS2 VALIDATION
and SECONDARY SMILES are used only as scaffold variants of keys already excluded for another reason.

Usage:
  PYTHONPATH=src python3 scripts/wur_v2_confirmation_v2/01_build_exposure_registry.py \
      --anchor-mzml-dir <dir holding the 561 anchor-well mzML files> \
      --lcsb-trajectories <main checkout artifacts/trajectories.parquet>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import external_msnlib as L       # noqa: E402
from muru.wur_v2 import external_mzml as X         # noqa: E402
from muru.wur_v2 import identity as ID             # noqa: E402
from muru.wur_v2.anchor_scope import ISO_TOL, PROTON, SHIFTS, ion_mzs   # noqa: E402
from rdkit.Chem.MolStandardize import rdMolStandardize                # noqa: E402

ELECTRON = 0.00054858
SEL_TOL = 0.01
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]
USID_RE = re.compile(r"(pluskal_.*?_id)(?=_|\.)")
EXPECTED = {
    "design12b_keys_sha256": "8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e",
    "eligible_group_list_sha256": "809f14c4d2528661be39e169aacf67b8618f736db6d1d17afd2a7914c67f07b9",
    "n_design12b_groups": 29562,
    "n_sample1_groups": 2000, "n_sample1_keys": 2690,
    "buggy_spectra": 3366, "buggy_files": 561, "fixed_spectra": 1816, "fixed_files": 472,
    "gate2_spectra": 1935, "gate2_files": 470, "gate1_ids": 4,
    "incident_affected_pairs": 964,
}
OUT_REL = "artifacts/wur_v2_confirmation_v2/exposure_registry"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lines(items) -> str:
    return sha256_bytes("\n".join(sorted(items)).encode())


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


# --------------------------------------------------------------------------------------------- identity

_chem: dict = {}


def chem(smi: str) -> dict:
    """Byte-for-byte the rule in scripts/wur_v2_confirmation/01_build_sample_and_massive_manifest.py."""
    if smi in _chem:
        return _chem[smi]
    rec = {"parse_ok": False, "parent_key": None, "scaffold": None, "parent_charge": None, "parent_formula": None,
           "mh": float("nan"), "m_plus": float("nan")}
    m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) and smi else None
    if m0 is not None:
        rk = inchi.MolToInchiKey(m0)
        pk = ID.parent_connectivity_key(smi)
        rec.update(parse_ok=bool(rk) and pk is not None, parent_key=pk)
        if pk is not None:
            rec["scaffold"] = ID.scaffold_group_v2(smi, pk)
    m = ID.parent_mol(smi) if rec["parse_ok"] else None
    if m is not None:
        rec["parent_charge"] = int(Chem.GetFormalCharge(m))
        rec["parent_formula"] = rdMolDescriptors.CalcMolFormula(m)
        mw = float(Descriptors.ExactMolWt(m))
        rec["mh"] = mw + PROTON if rec["parent_charge"] == 0 else float("nan")
        rec["m_plus"] = mw - ELECTRON * rec["parent_charge"] if rec["parent_charge"] > 0 else float("nan")
    _chem[smi] = rec
    return rec


def design_rows(merlin: Path, census: dict, cache: Path) -> pd.DataFrame:
    tables = census["inputs"]["design_tables"]
    input_hashes = {}
    for lib in LIBS:
        p = merlin / f"compounds__{lib}_cleaned.tsv"
        got = sha256_file(p)
        want = tables[LIB_LABEL[lib]]["sha256"]
        if got != want:
            raise SystemExit(f"MERLIN table {p.name} sha256 {got} != census {want}")
        input_hashes[p.name] = got
    id_sha = sha256_file(ROOT / "src/muru/wur_v2/identity.py")
    tag = sha256_bytes(json.dumps([input_hashes, id_sha, rdBase.rdkitVersion], sort_keys=True).encode())[:16]
    cp = cache / f"design_identity_{tag}.pkl"
    if cp.is_file():
        log(f"design identity from cache {cp.name}")
        return pd.read_pickle(cp), input_hashes
    parts = []
    for lib in LIBS:
        p = merlin / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        d = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
        d["library"] = LIB_LABEL[lib]
        parts.append(d)
    design = pd.concat(parts, ignore_index=True)
    uniq = design.smiles.dropna().unique()
    log(f"design rows {len(design)}, unique SMILES {len(uniq)}: computing identity (RDKit, several minutes)")
    for i, smi in enumerate(uniq):
        chem(smi)
        if i and i % 10000 == 0:
            log(f"  {i}/{len(uniq)}")
    for col in ("parse_ok", "parent_key", "scaffold", "parent_charge", "parent_formula", "mh", "m_plus"):
        design[col] = [chem(s)[col] if isinstance(s, str) else None for s in design.smiles]
    design["key"] = design.parent_key
    design["mh"] = pd.to_numeric(design.mh, errors="coerce")
    design["m_plus"] = pd.to_numeric(design.m_plus, errors="coerce")
    cache.mkdir(parents=True, exist_ok=True)
    design.to_pickle(cp)
    return design, input_hashes


def ions(row) -> list[float]:
    """Census singly charged set (used by the 0.01 Da rules)."""
    return ion_mzs(row.parent_charge, row.mh, row.m_plus, forms=SHIFTS)


def ions_extended(row) -> list[float]:
    return ion_mzs(row.parent_charge, row.mh, row.m_plus)


# --------------------------------------------------------------------------------------------- decode events

def read_headers(files: list[Path], cache: Path, file_sha: dict) -> dict:
    tag = sha256_lines(f"{p.name}:{file_sha[p.name]}" for p in files)[:16]
    cp = cache / f"anchor_headers_{tag}.pkl"
    if cp.is_file():
        log(f"anchor headers from cache {cp.name}")
        return pd.read_pickle(cp)
    out = {}
    for i, p in enumerate(files):
        rows = X.scan_headers(p)                                  # arrays removed before any parameter is read
        keep = ["spectrum_id", "index", "ms_level", "selected_ion_mz", "collision_energy",
                "scan_window_lower_limit", "scan_window_upper_limit"]
        h = pd.DataFrame(rows)
        out[p.name] = h[[c for c in keep if c in h.columns]]
        if i and i % 100 == 0:
            log(f"  headers {i}/{len(files)}")
    cache.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(out, cp)
    return out


def reconstruct_events(anchor_dir: Path, design: pd.DataFrame, census: dict, merlin: Path, cache: Path) -> tuple:
    aw = pd.read_csv(ROOT / "artifacts/wur_v2/external_msnlib/anchor_wells.csv")
    manifest_path = merlin / "anchor_file_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    m_rows = ([{"unique_sample_id": e["unique_sample_id"], "fn": e["filename"].rsplit("/", 1)[-1]} for e in manifest["avail_massive"]]
              + [{"unique_sample_id": e["unique_sample_id"], "fn": e["member"].rsplit("/", 1)[-1]} for e in manifest["avail_zenodo"]])
    files_df = pd.DataFrame(m_rows)
    if set(files_df.fn) != set(aw.fn):
        raise SystemExit("anchor_file_manifest.json file set differs from tracked anchor_wells.csv")
    names = sorted(set(aw.fn))
    paths = [anchor_dir / n for n in names]
    missing = [p.name for p in paths if not p.is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} anchor files missing under {anchor_dir}, e.g. {missing[:3]}")
    log(f"hashing {len(paths)} anchor-well files")
    file_sha = {p.name: sha256_file(p) for p in paths}
    headers = read_headers(paths, cache, file_sha)
    rung = {n: L.fixed_rung_scans(h) for n, h in headers.items()}
    sel_mz = {(n, r.spectrum_id): float(r.selected_ion_mz) for n, h in headers.items()
              for r in h[h.ms_level == 2].itertuples(index=False)}

    events = []   # (event, file, spectrum_id, surfaced)

    # E_buggy_preflight: first 6 rung-tagged scans by position in each sorted anchor file, + first 3 of files[0]
    for n in names:
        rs = rung[n][rung[n].rung.notna()]
        for sid in rs.spectrum_id.tolist()[:6]:
            events.append(("E_buggy_preflight", n, sid, False))
    rs0 = rung[names[0]][rung[names[0]].rung.notna()]
    surfaced = rs0.spectrum_id.tolist()[:3]
    for sid in surfaced:
        events.append(("E_buggy_preflight_surfaced_sanity_check", names[0], sid, True))

    # E_fixed_preflight_rerun: match_compounds against anchor keys plated in each well, window_ok, sorted(set)[:6]
    anchor_keys = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
    key_mh = design.dropna(subset=["key"]).drop_duplicates("key").set_index("key").mh
    well_keys = design[design.unique_sample_id.isin(files_df.unique_sample_id) & design.key.isin(anchor_keys)]
    wells = files_df.merge(well_keys[["unique_sample_id", "key"]].drop_duplicates(), on="unique_sample_id", how="inner")
    wells["mh"] = wells.key.map(key_mh)
    wells = wells.dropna(subset=["mh"])
    n_fixed_files = 0
    for fn, g in wells.groupby("fn"):
        matched = L.match_compounds(g[["key", "unique_sample_id", "fn", "mh"]], {fn: rung[fn]})
        ids = sorted(set(matched[matched.window_ok].spectrum_id))[:6] if not matched.empty else []
        n_fixed_files += bool(ids)
        for sid in ids:
            events.append(("E_fixed_preflight_rerun", fn, sid, False))
    sample_fn = sorted(wells.fn.unique())[0]
    matched = L.match_compounds(wells[wells.fn == sample_fn][["key", "unique_sample_id", "fn", "mh"]], {sample_fn: rung[sample_fn]})
    if not matched.empty and matched.window_ok.any():
        for sid in sorted(set(matched[matched.window_ok].spectrum_id))[:3]:
            events.append(("E_fixed_preflight_rerun", sample_fn, sid, False))

    # E_anchor_gate_attempt2 / attempt1 (ext11): match_compounds -> eligible -> window_ok
    matched = L.match_compounds(aw, rung)
    elig = L.eligible(matched)
    gate = matched[matched.key.isin(elig) & matched.window_ok]
    gate_pairs = sorted(set(zip(gate.file, gate.spectrum_id)))
    for fn, sid in gate_pairs:
        events.append(("E_anchor_gate_attempt2", fn, sid, False))
    acc1 = json.loads((ROOT / "artifacts/wur_v2/external_msnlib/anchor_calibration_access.json").read_text())
    acc2 = json.loads((ROOT / "artifacts/wur_v2/external_msnlib/anchor_calibration_access_attempt2.json").read_text())
    f1 = acc1["decodes"][0]["file"]
    gate1 = [(fn, sid) for fn, sid in gate_pairs if fn == f1]
    for fn, sid in gate1:
        events.append(("E_anchor_gate_attempt1", fn, sid, False))

    ev = pd.DataFrame(events, columns=["event", "file", "spectrum_id", "surfaced_to_operator"]).drop_duplicates()
    ev["selected_ion_mz"] = [sel_mz[(f, s)] for f, s in zip(ev.file, ev.spectrum_id)]
    rung_of = {(n, r.spectrum_id): r.rung for n, h in rung.items() for r in h[h.rung.notna()].itertuples(index=False)}
    ev["rung"] = [rung_of.get((f, s)) for f, s in zip(ev.file, ev.spectrum_id)]
    ev["unique_sample_id"] = [USID_RE.search(f).group(1) for f in ev.file]

    # ---- verification against recorded counts
    def n_pairs(e):
        return ev[ev.event == e][["file", "spectrum_id"]].drop_duplicates()
    checks = {
        "buggy_spectra": len(n_pairs("E_buggy_preflight")), "buggy_files": n_pairs("E_buggy_preflight").file.nunique(),
        "fixed_spectra": len(n_pairs("E_fixed_preflight_rerun")), "fixed_files": n_fixed_files,
        "gate2_spectra": len(gate_pairs), "gate2_files": len({f for f, _ in gate_pairs}), "gate1_ids": len(gate1),
    }
    for k, v in checks.items():
        if v != EXPECTED[k]:
            raise SystemExit(f"decode-event reconstruction mismatch: {k} = {v}, expected {EXPECTED[k]}")
    per_file = gate.drop_duplicates(["file", "spectrum_id"]).groupby("file").size().to_dict()
    if per_file != {d["file"]: d["n"] for d in acc2["decodes"]}:
        raise SystemExit("anchor gate attempt 2 per-file counts differ from its access record")
    if acc1["decodes"][0]["n"] != len(gate1):
        raise SystemExit("anchor gate attempt 1 request count differs from its access record")
    q = ROOT / "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13"
    aff = pd.read_csv(q / "affected_spectra_full_list.csv", usecols=["file", "spectrum_id"])
    bug = set(map(tuple, n_pairs("E_buggy_preflight").to_numpy()))
    if len(aff) != EXPECTED["incident_affected_pairs"] or not set(map(tuple, aff.to_numpy())) <= bug:
        raise SystemExit("incident affected_spectra_full_list.csv is not a subset of the reconstructed buggy decode set")
    tainted = json.loads((q / "parser_preflight_TAINTED.json").read_text())
    if [r["spectrum_id"] for r in tainted["sample_mu_sanity_check"]] != surfaced:
        raise SystemExit("reconstructed surfaced sanity-check spectrum ids differ from the quarantined record")
    rec = json.loads((q / "incident_record.json").read_text())
    surf_files = {v.get("file") for v in rec.get("values_surfaced_to_operator", []) if isinstance(v, dict) and v.get("file")}
    if surf_files and surf_files != {names[0]}:
        raise SystemExit(f"surfaced spectra file {names[0]} differs from the incident record {surf_files}")
    checks["surfaced_file_matches_incident_record"] = bool(surf_files)
    checks["incident_affected_pairs_subset_of_buggy_set"] = True
    checks["surfaced_spectrum_ids_match_quarantine"] = True
    checks["gate2_per_file_counts_match_access_record"] = True
    checks["verification_level"] = {
        "E_buggy_preflight": "exact ids: 964 incident pairs must be a subset, count 3,366, 6 per file",
        "E_buggy_preflight_surfaced_sanity_check": "exact ids and file against the quarantined record",
        "E_anchor_gate_attempt2": "per-file counts equal the access record (ids not recorded there)",
        "E_anchor_gate_attempt1": "count equals the access record",
        "E_fixed_preflight_rerun": "total and file counts only (no id-level record exists)",
        "consequence": "every compound plated in all 561 wells is excluded regardless (COPLATED_IN_DECODED_WELL); "
                       "only the carryover rules depend on exact ids",
    }

    decoded_files = pd.DataFrame({"file": names, "file_sha256": [file_sha[n] for n in names],
                                  "unique_sample_id": [USID_RE.search(n).group(1) for n in names]})
    ev_by_file = ev.groupby("file").event.apply(lambda s: ";".join(sorted(set(s))))
    decoded_files["events"] = decoded_files.file.map(ev_by_file)
    # every anchor-well file was opened by the burned preflight; keep all 561 as exposed files
    decoded_files["events"] = decoded_files.events.fillna("E_buggy_preflight")
    return ev, decoded_files, checks, sha256_file(manifest_path)


# --------------------------------------------------------------------------------------------- populations

def exposed_populations(trajectories: Path) -> tuple[dict, dict]:
    """name -> set(keys); key -> set(SMILES variants) from every identity source in the program."""
    pops: dict[str, set] = {}
    smiles: dict[str, set] = {}

    def add_smiles(key, smi):
        if isinstance(key, str) and isinstance(smi, str) and smi:
            smiles.setdefault(key, set()).add(smi)

    em = json.loads((ROOT / "artifacts/wur_v2/exposure_manifest.json").read_text())
    for name, p in em["populations"].items():
        keys = set(p["connectivity_keys"])
        if sha256_lines(keys) != p["connectivity_keys_sha256"]:
            raise SystemExit(f"exposure_manifest {name} key hash mismatch")
        pops[name] = keys
    comp = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv", usecols=["group_key", "smiles"])
    pops["V2-DEVELOPMENT-POPULATION"] = set(comp.group_key)
    pm = json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())
    want = pm.get("keys_sha256") or em["v2"]["V2-DEVELOPMENT-POPULATION"]["connectivity_keys_sha256"]
    if sha256_lines(pops["V2-DEVELOPMENT-POPULATION"]) != want:
        raise SystemExit("v2 development population key hash mismatch")
    for k, s in zip(comp.group_key, comp.smiles):
        add_smiles(k, s)
    t = pd.read_parquet(trajectories, columns=["inchikey_first_block", "smiles_raw"])
    pops["LCSB-ALL-MASSBANK-V1-EXPOSURE-SET"] = set(t.inchikey_first_block.dropna())
    for k, s in zip(t.inchikey_first_block, t.smiles_raw):
        add_smiles(k, s)
    lps = pd.read_parquet(ROOT / "artifacts/wur_v2/data/lcsb_pos_spectra.parquet", columns=["connectivity_key", "smiles_raw"])
    pops["LCSB-POS-V2-SPECTRA"] = set(lps.connectivity_key.dropna())
    for k, s in zip(lps.connectivity_key, lps.smiles_raw):
        add_smiles(k, s)
    wpi = pd.read_csv(ROOT / "artifacts/wur_v2/data/wur_pos_identity.csv")
    wk = next(c for c in ("connectivity_key", "group_key", "key") if c in wpi.columns)
    pops["WUR-POS-IDENTITY"] = set(wpi[wk].dropna())
    if "smiles" in wpi.columns:
        for k, s in zip(wpi[wk], wpi.smiles):
            add_smiles(k, s)
    mm = json.loads((ROOT / "artifacts/wur_v2/external/populations.json").read_text())
    pops["MultiMS2-ANCHOR"] = {r["key"] for r in mm["populations"]["ANCHOR"]}
    for pop in ("ANCHOR", "VALIDATION", "SECONDARY"):      # VALIDATION/SECONDARY: scaffold variants only, never exclusions
        for r in mm["populations"][pop]:
            add_smiles(r["key"], r.get("smiles"))
    entact = set()
    for f in sorted((ROOT / "data/massive/compound_lists").glob("mix*_compounds.csv")):
        d = pd.read_csv(f)
        scol = next(c for c in d.columns if c.lower() in ("smiles", "canonical_smiles", "qsar_ready_smiles"))
        for s in d[scol].dropna():
            k = ID.parent_connectivity_key(s)
            if k:
                entact.add(k)
                add_smiles(k, s)
    pops["ENTACT-MIX-LISTS-499-503-505"] = entact
    rep = json.loads((ROOT / "artifacts/replicate_compound_keys.json").read_text())
    rep_keys = rep if isinstance(rep, list) else next(v for v in rep.values() if isinstance(v, list))
    pops["LCSB-RAW-MIX-REPLICATE-SET-92"] = set(rep_keys)
    return pops, smiles


# --------------------------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msnlib-home", default=os.environ.get("MURU_MSNLIB_HOME", str(Path.home() / "muru-msnlib")))
    ap.add_argument("--anchor-mzml-dir", required=True)
    ap.add_argument("--lcsb-trajectories", required=True)
    args = ap.parse_args()
    home = Path(args.msnlib_home)
    merlin, cache = home / "merlin_metadata", home / "cache" / "confirmation_v2"
    out = ROOT / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    census = json.loads((ROOT / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    step12b = set(census["design_frame"]["survivors"]["step12b_keys"])
    if sha256_lines(step12b) != EXPECTED["design12b_keys_sha256"]:
        raise SystemExit("design 12b key hash mismatch")
    design, merlin_hashes = design_rows(merlin, census, cache)
    key_scaf = {}   # first occurrence in LIBS concat order, exactly the census map
    for k, sc in design.dropna(subset=["key"]).drop_duplicates("key")[["key", "scaffold"]].itertuples(index=False):
        key_scaf[k] = sc if isinstance(sc, str) and sc else f"__UNPARSED__{k}"
    groups12b = sorted({key_scaf[k] for k in step12b})
    if len(groups12b) != EXPECTED["n_design12b_groups"] or sha256_lines(groups12b) != EXPECTED["eligible_group_list_sha256"]:
        raise SystemExit("design 12b scaffold group list mismatch")
    groups12b_set = set(groups12b)
    keys_by_group: dict[str, set] = {}
    for k in step12b:
        keys_by_group.setdefault(key_scaf[k], set()).add(k)
    log(f"design 12b verified: {len(step12b)} keys, {len(groups12b)} groups")

    reasons: dict[str, set] = {}

    def mark(keys, reason):
        for k in keys:
            if isinstance(k, str) and k:
                reasons.setdefault(k, set()).add(reason)

    # ---- (1) sample 1, identified from its tracked artifact (no draw)
    nb = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation/novelty_bins_per_compound.csv", usecols=["key", "scaffold_group"])
    s1_keys, s1_groups = set(nb.key), set(nb.scaffold_group)
    if (len(s1_keys), len(s1_groups)) != (EXPECTED["n_sample1_keys"], EXPECTED["n_sample1_groups"]):
        raise SystemExit("sample 1 artifact counts differ from the frozen 2,690 / 2,000")
    if not s1_groups <= groups12b_set or set().union(*(keys_by_group[g] for g in s1_groups)) != s1_keys:
        raise SystemExit("sample 1 keys are not exactly the 12b members of its 2,000 scaffold groups")
    if any(key_scaf[k] != g for k, g in zip(nb.key, nb.scaffold_group)):
        raise SystemExit("sample 1 scaffold labels disagree with the census key->scaffold map")
    mark(s1_keys, "SAMPLE1_DRAW_GROUP")
    log("sample 1 identified and verified from tracked artifact")

    # ---- (2) decode events and spectrum-derived exposure
    ev, decoded_files, event_checks, manifest_sha = reconstruct_events(Path(args.anchor_mzml_dir), design, census, merlin, cache)
    log(f"decode events verified: {event_checks}")
    ok = design.dropna(subset=["key"])
    by_well = {u: g for u, g in ok.groupby("unique_sample_id")}
    spectra = ev.drop_duplicates(["file", "spectrum_id"])
    same_well = set()
    for r in spectra.itertuples(index=False):
        g = by_well.get(r.unique_sample_id)
        if g is None:
            continue
        for row in g.itertuples(index=False):
            if any(abs(i - r.selected_ion_mz) <= ISO_TOL for i in ions(row)):
                same_well.add(row.key)
    mark(same_well, "DECODED_SAME_WELL_ION_0p7")
    mh_tab = ok[np.isfinite(ok.mh)][["mh", "key"]].sort_values("mh")
    mh_arr, mh_keys = mh_tab.mh.to_numpy(), mh_tab.key.to_numpy()

    def mh_matches_any_well(mz):
        lo, hi = np.searchsorted(mh_arr, mz - SEL_TOL, "left"), np.searchsorted(mh_arr, mz + SEL_TOL, "right")
        return set(mh_keys[lo:hi])

    ok = ok.assign(plate=ok.library.astype(str) + "|" + ok.plate_id.astype(str))
    plate_of_well = ok.drop_duplicates("unique_sample_id").set_index("unique_sample_id").plate
    by_plate = {pl: g for pl, g in ok.groupby("plate")}
    plate_ions: dict[str, tuple] = {}

    def plate_matches(well, mz):
        pl = plate_of_well.get(well)
        if pl is None:
            return set()
        if pl not in plate_ions:
            vals, keys = [], []
            for row in by_plate[pl].itertuples(index=False):
                for i in ions(row):
                    vals.append(i)
                    keys.append(row.key)
            order = np.argsort(vals)
            plate_ions[pl] = (np.asarray(vals)[order], np.asarray(keys, dtype=object)[order])
        v, k = plate_ions[pl]
        return set(k[np.searchsorted(v, mz - SEL_TOL, "left"):np.searchsorted(v, mz + SEL_TOL, "right")])

    same_plate = set().union(*(plate_matches(w, mz) for w, mz in zip(spectra.unique_sample_id, spectra.selected_ion_mz)))
    mark(same_plate, "DECODED_SAME_PLATE_ION_0p01")
    rejected_any_well = set().union(*(mh_matches_any_well(mz) for mz in spectra.selected_ion_mz))
    decoded_wells = set(decoded_files.unique_sample_id)
    coplated = set(ok[ok.unique_sample_id.isin(decoded_wells)].key)
    mark(coplated, "COPLATED_IN_DECODED_WELL")
    surf = ev[ev.surfaced_to_operator]
    surf_keys = set().union(*(plate_matches(w, mz) for w, mz in zip(surf.unique_sample_id, surf.selected_ion_mz))) if len(surf) else set()
    surf_wells = set(ok[ok.key.isin(surf_keys)].unique_sample_id) | set(surf.unique_sample_id)
    surf_well_keys = set(ok[ok.unique_sample_id.isin(surf_wells)].key)
    mark(surf_well_keys, "SURFACED_VALUE_ATTRIBUTED_WELL")

    # extended-ion index (anchor_scope.ION_FORMS) over all design rows, for ppm rules
    ext_v, ext_k, ext_pl, ext_lib = [], [], [], []
    for row in ok.itertuples(index=False):
        for mzv in ions_extended(row):
            ext_v.append(mzv); ext_k.append(row.key); ext_pl.append(row.plate); ext_lib.append(row.library)
    order = np.argsort(ext_v)
    ext_v = np.asarray(ext_v)[order]
    ext_k, ext_pl, ext_lib = (np.asarray(a, dtype=object)[order] for a in (ext_k, ext_pl, ext_lib))

    def ppm_matches(mz, ppm, plate=None, library=None):
        tol = mz * ppm * 1e-6
        lo, hi = np.searchsorted(ext_v, mz - tol, "left"), np.searchsorted(ext_v, mz + tol, "right")
        sel = np.ones(hi - lo, bool)
        if plate is not None:
            sel &= ext_pl[lo:hi] == plate
        if library is not None:
            sel &= ext_lib[lo:hi] == library
        return set(ext_k[lo:hi][sel])

    lib_of_well = ok.drop_duplicates("unique_sample_id").set_index("unique_sample_id").library
    same_plate_ext = set()
    orphan_owners = set()
    for w, mz in zip(spectra.unique_sample_id, spectra.selected_ion_mz):
        hits = ppm_matches(mz, 5.0, plate=plate_of_well.get(w))
        same_plate_ext |= hits
        in_well = {r.key for r in by_well.get(w, pd.DataFrame(columns=ok.columns)).itertuples(index=False)
                   if any(abs(i - mz) <= mz * 5e-6 for i in ions_extended(r))}
        if not hits and not in_well and not plate_matches(w, mz):
            orphan_owners |= ppm_matches(mz, 3.0, library=lib_of_well.get(w))
    mark(same_plate_ext, "DECODED_SAME_PLATE_EXTENDED_ION_5PPM")
    mark(orphan_owners, "ORPHAN_SPECTRUM_SAME_LIBRARY_OWNER_3PPM")
    surf_any = set().union(*(ppm_matches(mz, 5.0) for mz in surf.selected_ion_mz)) if len(surf) else set()
    mark(surf_any, "SURFACED_VALUE_ANY_LIBRARY_OWNER_5PPM")

    # wells whose full scan headers were parsed during study 1
    tp = json.loads((ROOT / "artifacts/wur_v2_confirmation/transport_provenance_manifest.json").read_text())
    header_wells = {r["unique_sample_id"] for r in tp["rows"]} | decoded_wells
    listing = sorted(p.name for p in Path(args.anchor_mzml_dir).glob("*.mzML"))
    listing_wells = {m.group(1) for m in (USID_RE.search(n) for n in listing) if m}
    if not listing_wells <= header_wells:
        raise SystemExit(f"{len(listing_wells - header_wells)} locally present study-1 wells are not in the tracked lists")
    header_keys = set(ok[ok.unique_sample_id.isin(header_wells)].key)
    mark(header_keys, "HEADER_READ_WELL_STUDY1")

    # ---- (3) anchors and calibration
    mark(census["anchors"]["design"]["v2_dev_five_rung"]["keys"], "MSNLIB_ANCHOR_CENSUS_DESIGN")
    mark(census["anchors"]["detected"]["v2_dev_five_rung"]["keys"], "MSNLIB_ANCHOR_CENSUS_DETECTED")
    mark(pd.read_csv(ROOT / "artifacts/wur_v2/external_msnlib/anchor_mu.csv", usecols=["key"]).key, "MSNLIB_ANCHOR_GATE_CALIBRATION")

    # ---- (4) previously exposed MURU populations
    pops, pop_smiles = exposed_populations(Path(args.lcsb_trajectories))
    for name, keys in sorted(pops.items()):
        mark(keys, "MULTIMS2_ANCHOR_CALIBRATION" if name == "MultiMS2-ANCHOR" else f"EXPOSED_POPULATION:{name}")

    # ---- scaffold-group expansion
    merlin_smiles: dict[str, set] = {}
    for k, s in zip(ok.key, ok.smiles):
        if isinstance(s, str):
            merlin_smiles.setdefault(k, set()).add(s)
    group_reasons: dict[str, set] = {}
    scaffold_cache: dict[tuple, str] = {}
    for k, rs in reasons.items():
        strings = set()
        if k in key_scaf:
            strings.add(key_scaf[k])
        for s in merlin_smiles.get(k, set()) | pop_smiles.get(k, set()):
            if (s, k) not in scaffold_cache:
                scaffold_cache[(s, k)] = ID.scaffold_group_v2(s, k)
            strings.add(scaffold_cache[(s, k)])
        for g in strings:
            group_reasons.setdefault(g, set()).update(rs)
    taut = rdMolStandardize.TautomerEnumerator()
    taut_cache: dict[str, str] = {}

    def canon_taut(scaffold: str) -> str:
        if scaffold.startswith("__"):
            return scaffold
        if scaffold not in taut_cache:
            m = Chem.MolFromSmiles(scaffold)
            try:
                taut_cache[scaffold] = Chem.MolToSmiles(taut.Canonicalize(m)) if m is not None else scaffold
            except Exception:
                taut_cache[scaffold] = scaffold
        return taut_cache[scaffold]

    log("tautomer closure over scaffold groups")
    excluded_taut = {}
    for g, rs in group_reasons.items():
        excluded_taut.setdefault(canon_taut(g), set()).update(rs)
    for g in groups12b:
        if g not in group_reasons and canon_taut(g) in excluded_taut:
            group_reasons[g] = {"TAUTOMER_OF_EXCLUDED_SCAFFOLD"}
    excluded_12b_groups = groups12b_set & set(group_reasons)
    for g in excluded_12b_groups:
        for k in keys_by_group[g]:
            reasons.setdefault(k, set()).add("SCAFFOLD_GROUP_EXCLUDED")

    # ---- outputs
    comp_rows = [{"key": k, "scaffold_group_census": key_scaf.get(k, ""), "in_design12b": k in step12b,
                  "reasons": ";".join(sorted(rs))} for k, rs in sorted(reasons.items())]
    comp_df = pd.DataFrame(comp_rows)
    grp_rows = [{"scaffold_group": g, "in_design12b": g in groups12b_set,
                 "n_design12b_keys": len(keys_by_group.get(g, ())), "reasons": ";".join(sorted(rs))}
                for g, rs in sorted(group_reasons.items())]
    grp_df = pd.DataFrame(grp_rows)
    excluded_12b_keys = {k for k in step12b if k in reasons}
    remaining_groups = groups12b_set - excluded_12b_groups
    if any(k in reasons for g in remaining_groups for k in keys_by_group[g]):
        raise SystemExit("a remaining 12b group still contains an excluded key")
    if decoded_wells & set(ok[ok.key.isin({k for g in remaining_groups for k in keys_by_group[g]})].unique_sample_id):
        raise SystemExit("a remaining 12b compound is plated in a decoded well")

    files = {
        "excluded_compounds.csv": comp_df, "excluded_scaffold_groups.csv": grp_df,
        "exposed_files.csv": decoded_files[["file", "file_sha256", "unique_sample_id", "events"]],
        "decoded_spectra.csv": ev.sort_values(["event", "file", "spectrum_id"])[
            ["event", "file", "unique_sample_id", "spectrum_id", "selected_ion_mz", "rung", "surfaced_to_operator"]],
    }
    file_hashes = {}
    for name, df in files.items():
        p = out / name
        df.to_csv(p, index=False)
        file_hashes[name] = sha256_file(p)
    (out / "excluded_compound_keys.txt").write_text("\n".join(sorted(reasons)) + "\n")
    (out / "excluded_scaffold_groups.txt").write_text("\n".join(sorted(group_reasons)) + "\n")
    for name in ("excluded_compound_keys.txt", "excluded_scaffold_groups.txt"):
        file_hashes[name] = sha256_file(out / name)

    reason_counts = {}
    for rs in reasons.values():
        for r in rs:
            reason_counts[r] = reason_counts.get(r, 0) + 1
    manifest = {
        "study_id": "muru-v2-msnlib-confirmation-2.0",
        "registry": "permanent exposure exclusion registry (study 2, step 2)",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rule": "a compound or scaffold group listed here may never enter an MSnLib confirmatory pool",
        "counts": {
            "excluded_compound_keys_all_sources": len(reasons),
            "excluded_scaffold_groups_all_sources": len(group_reasons),
            "design12b_keys": len(step12b), "design12b_groups": len(groups12b),
            "excluded_design12b_keys": len(excluded_12b_keys), "excluded_design12b_groups": len(excluded_12b_groups),
            "remaining_design12b_groups_count_only": len(remaining_groups),
            "decoded_msnlib_files": int(len(decoded_files)), "decoded_msnlib_wells": len(decoded_wells),
            "decoded_msnlib_spectra_unique": int(len(spectra)),
            "per_reason_compounds": dict(sorted(reason_counts.items())),
            "per_event_spectra": ev.groupby("event").size().to_dict(),
        },
        "hashes_sorted_newline_joined": {
            "excluded_compound_keys_sha256": sha256_lines(reasons),
            "excluded_scaffold_groups_sha256": sha256_lines(group_reasons),
            "excluded_design12b_keys_sha256": sha256_lines(excluded_12b_keys),
            "excluded_design12b_groups_sha256": sha256_lines(excluded_12b_groups),
            "sample1_groups_sha256": sha256_lines(s1_groups), "sample1_keys_sha256": sha256_lines(s1_keys),
        },
        "output_file_sha256": file_hashes,
        "decode_event_verification": event_checks,
        "inputs": {
            "merlin_tables_sha256_verified_against_census": merlin_hashes,
            "anchor_file_manifest_sha256": manifest_sha,
            "lcsb_trajectories_sha256": sha256_file(Path(args.lcsb_trajectories)),
            "census_sha256": sha256_file(ROOT / "artifacts/wur_v2/external_census/msnlib_census.json"),
            "population_key_counts": {n: len(k) for n, k in sorted(pops.items())},
            "identity_py_sha256": sha256_file(ROOT / "src/muru/wur_v2/identity.py"),
            "rdkit": rdBase.rdkitVersion, "numpy": np.__version__, "pandas": pd.__version__,
            "python": sys.version.split()[0],
        },
        "rejected_rule_sensitivity": {
            "rule": "decoded precursor within 0.01 Da of [M+H]+ of a compound in ANY well of ANY library",
            "n_compounds_it_would_flag": len(rejected_any_well),
            "n_additional_design12b_groups_it_would_exclude": len({key_scaf[k] for k in rejected_any_well if k in step12b}
                                                                 - excluded_12b_groups),
            "why_rejected": "no exposure mechanism: cross-library, cross-year mass coincidences (both independent audits)",
        },
        "not_excluded_disclosures": {
            "MultiMS2-VALIDATION and SECONDARY": "reserved, never decoded; not previously exposed, so not excluded (the census kept them in 12b)",
            "prospective acquisition target lists": "design-only, never measured; not excluded",
            "header-only reads": "scan headers of the 2,811 locally extracted wells were read for population construction; "
                                 "headers are acquisition metadata, not outcomes, by program precedent; not excluded",
            "WUR negative-mode keys without SMILES": "excluded by exact key; scaffold groups cannot be computed (no SMILES in repo)",
        },
    }
    (out / "registry_manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n")
    print(json.dumps(manifest["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
