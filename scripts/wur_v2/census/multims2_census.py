"""Outcome-blind MultiMS2 identity/metadata/acquisition eligibility census.

Reads only files saved by multims2_fetch.py under data/external/multims2_metadata/
(identity TSVs, pre-acquisition plate metadata, repository listings, method
documentation). No spectral peak, intensity or peak-derived value is read.

Two frames are censused:
  LIBRARY  the released, QC-filtered library, described by the five peak-free
           GNPS batch identity tables (one row per released spectrum).
  DESIGN   the plated positive-mode compound lists (pre-acquisition metadata)
           joined to the public file listing by pool position. This frame is
           outcome-free; the LIBRARY frame is conditioned on the authors' QC,
           which is a function of the spectra (see report).

Run: PYTHONPATH=src /opt/miniconda3/bin/python3 scripts/wur_v2/census/multims2_census.py
"""
from __future__ import annotations

import glob
import hashlib
import json
import platform
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import inchi, rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize

from muru.io.wur_provenance import canonical_key_hash
from muru.wur_v2.identity import parent_connectivity_key, parent_mol, scaffold_group_v2

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[3]
MD = ROOT / "data" / "external" / "multims2_metadata"
ART = ROOT / "artifacts"
OUT = ART / "wur_v2" / "external_census" / "multims2_census.json"
RUNGS3 = (20.0, 40.0, 60.0)
SUBSETS2 = {"20_40": (20.0, 40.0), "20_60": (20.0, 60.0), "40_60": (40.0, 60.0)}
TARGET_ADDUCT = "[M+H]+"
PROTON = 1.007276
# Dropped on load without inspecting values. LIBQUALITY is written as the
# constant "1" by notebooks/convert_spectra_to_tsv.py; it is dropped anyway
# because its name denotes a quality flag. SELFIES is redundant with SMILES.
DROP_ON_LOAD = ["LIBQUALITY", "SELFIES"]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------
# chemistry helpers (cached per SMILES)
# ----------------------------------------------------------------------------
_chem: dict[str, dict] = {}
_taut = rdMolStandardize.TautomerEnumerator()
_taut.SetMaxTautomers(256)
_taut.SetMaxTransforms(256)


def chem(smiles: str) -> dict:
    if smiles in _chem:
        return _chem[smiles]
    rec = {"parse_ok": False, "raw_key": None, "parent_key": None, "scaffold": None}
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
    if m is not None:
        rk = inchi.MolToInchiKey(m)
        pk = parent_connectivity_key(smiles)
        rec.update(parse_ok=bool(rk) and pk is not None, raw_key=rk.split("-")[0] if rk else None,
                   parent_key=pk, n_fragments=len(Chem.GetMolFrags(m)),
                   formal_charge=Chem.GetFormalCharge(m))
        if pk is not None:
            rec["scaffold"] = scaffold_group_v2(smiles, pk)
    _chem[smiles] = rec
    return rec


_tautkey: dict[str, str | None] = {}


def tautomer_parent_key(smiles: str) -> str | None:
    """Connectivity key of the RDKit canonical tautomer of the parent."""
    if smiles in _tautkey:
        return _tautkey[smiles]
    out = None
    m = parent_mol(smiles)
    if m is not None:
        try:
            t = _taut.Canonicalize(m)
            k = inchi.MolToInchiKey(t)
            out = k.split("-")[0] if k else None
        except Exception:
            out = None
    _tautkey[smiles] = out
    return out


_fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def count_fp(smiles: str):
    m = parent_mol(smiles)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    return _fpgen.GetCountFingerprint(m)


def groups_summary(scaffolds: pd.Series) -> dict:
    vc = scaffolds.value_counts()
    return {"n_scaffold_groups": int(vc.size), "n_groups_size_1": int((vc == 1).sum()),
            "n_acyclic_groups": int(vc.index.str.startswith("__ACYCLIC__").sum()),
            "largest_group_size": int(vc.max()) if vc.size else 0}


# ----------------------------------------------------------------------------
# MURU exposed identity universe
# ----------------------------------------------------------------------------
def load_muru() -> dict:
    em = json.loads((ART / "wur_v2" / "exposure_manifest.json").read_text())
    pops = {}
    for name, p in em["populations"].items():
        keys = set(p["connectivity_keys"])
        ok = canonical_key_hash(sorted(keys)) == p["connectivity_keys_sha256"] and len(keys) == p["n_keys"]
        pops[name] = {"keys": keys, "hash_verified": ok, "exposure_class": p["exposure_class"]}
    comp = pd.read_csv(ART / "wur_v2" / "data" / "compounds.csv", usecols=["group_key", "smiles", "scaffold_group"])
    p2 = pd.read_parquet(ART / "p2_compounds.parquet", columns=["inchikey_first_block", "smiles", "in_confirmation"])
    wid = pd.read_csv(ART / "wur_v2" / "data" / "wur_pos_identity.csv", usecols=["connectivity_key", "smiles"])
    traj = pd.read_parquet(ART / "trajectories.parquet", columns=["inchikey_first_block", "smiles_raw"]).drop_duplicates()
    smiles_sources = pd.concat([
        comp.rename(columns={"group_key": "key"})[["key", "smiles"]].assign(src="wur_v2/compounds.csv"),
        p2.rename(columns={"inchikey_first_block": "key"})[["key", "smiles"]].assign(src="p2_compounds.parquet"),
        wid.rename(columns={"connectivity_key": "key"})[["key", "smiles"]].assign(src="wur_pos_identity.csv"),
        traj.rename(columns={"inchikey_first_block": "key", "smiles_raw": "smiles"}).assign(src="trajectories.parquet"),
    ]).dropna(subset=["smiles"]).drop_duplicates(subset=["key", "smiles"])
    # v2 scaffold-group reproducibility check
    recomputed = comp.apply(lambda r: scaffold_group_v2(r.smiles, r.group_key), axis=1)
    scaffold_repro = int((recomputed == comp.scaffold_group).sum())
    return {"manifest": em, "pops": pops, "compounds": comp, "p2": p2, "smiles_sources": smiles_sources,
            "scaffold_repro": scaffold_repro}


# ----------------------------------------------------------------------------
# frames
# ----------------------------------------------------------------------------
def collection_from_filename(fn: str) -> str:
    s = fn.lower()
    if "_nexus_" in s:
        return "NEXUS"
    if "_selleck_" in s:
        return "SELLECK"
    if re.search(r"_plate_\d+_column_", s):
        return "MSMLS"
    if "_blank_" in s:
        return "BLANK"
    return "UNKNOWN"


def parse_ce(s: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", str(s))]


def load_library() -> tuple[pd.DataFrame, dict]:
    files = sorted(glob.glob(str(MD / "MULTIMS2-PARTITION-*.identity.tsv")))
    parts = []
    for f in files:
        d = pd.read_csv(f, sep="\t", dtype=str, keep_default_na=False)
        d = d.drop(columns=[c for c in DROP_ON_LOAD if c in d.columns])
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    d["collection"] = d.FILENAME.map(collection_from_filename)
    ces = d.COLLISION_ENERGY.map(parse_ce)
    d["ce_n_values"] = ces.map(len)
    d["ce"] = ces.map(lambda v: v[0] if len(v) == 1 else np.nan)
    d["recorded_block1"] = d.INCHIAUX.str.split("-").str[0]
    info = {"files": [Path(f).name for f in files], "n_rows": int(len(d)),
            "columns_kept": [c for c in d.columns], "columns_dropped_unseen": DROP_ON_LOAD,
            "ce_multi_value_rows": int((d.ce_n_values != 1).sum()),
            "ce_label_counts": d.COLLISION_ENERGY.value_counts().to_dict(),
            "collection_counts_records": d.collection.value_counts().to_dict(),
            "instrument_counts": d.INSTRUMENT.value_counts().to_dict(),
            "ionsource_counts": d.IONSOURCE.value_counts().to_dict()}
    for smi in d.SMILES.unique():
        chem(smi)
    d["parse_ok"] = d.SMILES.map(lambda s: _chem[s]["parse_ok"])
    d["parent_key"] = d.SMILES.map(lambda s: _chem[s]["parent_key"])
    d["raw_key"] = d.SMILES.map(lambda s: _chem[s]["raw_key"])
    d["key"] = d.parent_key.where(d.parent_key.notna(), d.recorded_block1)
    d["scaffold"] = [(_chem[s]["scaffold"] or f"__UNPARSED__{k}") for s, k in zip(d.SMILES, d.key)]
    # InChI string consistency with the recorded InChIKey
    ik = {}
    for s in d.INCHI.unique():
        try:
            ik[s] = inchi.InchiToInchiKey(s)
        except Exception:
            ik[s] = None
    d["inchi_to_key_ok"] = [ik[s] == k for s, k in zip(d.INCHI, d.INCHIAUX)]
    return d, info


def load_listing() -> dict:
    lst = pd.read_csv(MD / "massive_filelist_gnps2cache.csv")
    peak = lst[lst.filepath.str.startswith("peak/centroided/") & lst.filepath.str.endswith(".mzML")].copy()
    peak["stem"] = peak.filepath.str.rsplit("/", n=1).str[1].str.replace(r"\.mzML$", "", regex=True)
    mzx = lst[lst.filepath.str.endswith(".mzXML")].copy()
    mzx["stem"] = mzx.filepath.str.rsplit("/", n=1).str[1].str.replace(r"\.mzXML$", "", regex=True)
    z = json.loads((MD / "zenodo_17250693.json").read_text())
    zkeys = {f["key"]: f["size"] for f in z["files"]}

    def meta(stem: str) -> dict:
        s = stem
        coll = collection_from_filename(s)
        pol = "pos" if re.search(r"_pos(_|$)", s) else ("neg" if re.search(r"_neg(_|$)", s) else None)
        mth = "CID" if "_CID_" in s else ("EAD" if "_EAD_" in s else None)
        e = re.search(r"_(?:CID|EAD)_(\d+)(?:ev|eV|KE)", s)
        return {"collection": coll, "polarity": pol, "method": mth, "energy": float(e.group(1)) if e else np.nan}

    pm = pd.DataFrame([meta(s) for s in peak.stem], index=peak.index)
    peak = pd.concat([peak.drop(columns=["collection"]), pm], axis=1)
    return {"listing": lst, "peak": peak, "mzxml_stems": set(mzx.stem), "zenodo_files": zkeys,
            "summary": {
                "massive_listing_rows": int(len(lst)),
                "by_top_dir": lst.assign(top=lst.filepath.str.extract(r"^(peak/centroided|ccms_peak/centroided|ccms_metadata/ccms_peak/centroided|updates/[^/]+/peak/mzXML|ccms_metadata|ccms_parameters)")[0])
                .groupby("top").agg(n_files=("filepath", "size"), bytes=("size", "sum")).reset_index().to_dict("records"),
                "extensions": lst.filepath.str.extract(r"(\.[A-Za-z]+(?:\.[A-Za-z]+)?)$")[0].value_counts().to_dict(),
                "has_wiff": bool(lst.filepath.str.contains(r"\.wiff", case=False).any()),
                "has_profile_dir": bool(lst.filepath.str.contains("profile", case=False).any()),
                "centroided_mzml_files_by_collection_polarity_method_energy":
                    peak.groupby(["collection", "polarity", "method", "energy"]).size().rename("n").reset_index().to_dict("records"),
                "zenodo_17250693_zip_files": zkeys,
            }}


def position_regex(pos: str) -> re.Pattern:
    p = pos.strip("_")
    return re.compile(r"(?:^|_)" + re.escape(p) + r"(?=_|$)")


def pool_members(files_by_coll: dict, design: pd.DataFrame) -> pd.DataFrame:
    """position -> file stems per collection (boundary-aware substring match, as mzmine's
    filename-header filter but without the A1/A12 prefix ambiguity)."""
    rows = []
    for (coll, pos), _ in design.groupby(["collection", "position"]):
        rx = position_regex(pos)
        for stem, e, mth in files_by_coll.get(coll, []):
            if rx.search(stem):
                rows.append({"collection": coll, "position": pos, "stem": stem, "energy": e, "method": mth})
    return pd.DataFrame(rows)


def load_design(listing: dict) -> tuple[pd.DataFrame, dict]:
    parts = []
    for coll, fn in [("NEXUS", "nexus_metadata_pos.tsv"), ("SELLECK", "selleck_metadata_pos.tsv"), ("MSMLS", "msmls_metadata_pos.tsv")]:
        d = pd.read_csv(MD / fn, sep="\t", dtype=str, keep_default_na=False)
        d = d.drop(columns=[c for c in DROP_ON_LOAD if c in d.columns])
        d["collection"] = coll
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    for smi in d.smiles.unique():
        chem(smi)
    d["recorded_block1"] = d.inchikey.str.split("-").str[0]
    d["parse_ok"] = d.smiles.map(lambda s: _chem[s]["parse_ok"])
    d["parent_key"] = d.smiles.map(lambda s: _chem[s]["parent_key"])
    d["raw_key"] = d.smiles.map(lambda s: _chem[s]["raw_key"])
    d["key"] = d.parent_key.where(d.parent_key.notna(), d.recorded_block1)
    d["scaffold"] = [(_chem[s]["scaffold"] or f"__UNPARSED__{k}") for s, k in zip(d.smiles, d.key)]
    peak = listing["peak"]
    pc = peak[(peak.polarity == "pos") & (peak.method == "CID")]
    files_by_coll = {c: list(zip(g.stem, g.energy, g.method)) for c, g in pc.groupby("collection")}
    pm = pool_members(files_by_coll, d)
    e_by_pos = pm.groupby(["collection", "position"]).energy.apply(lambda s: sorted(set(s))).to_dict()
    nfile_by_pos = pm.groupby(["collection", "position"]).stem.nunique().to_dict()
    d["pos_cid_energies"] = [e_by_pos.get((c, p), []) for c, p in zip(d.collection, d.position)]
    d["pos_cid_n_files"] = [nfile_by_pos.get((c, p), 0) for c, p in zip(d.collection, d.position)]
    # same-pool [M+H]+ precursor conflicts (identity arithmetic only)
    d["mass_f"] = pd.to_numeric(d["mass"], errors="coerce")
    conflict_50mda, conflict_07da = [], []
    for (c, p), g in d.groupby(["collection", "position"]):
        m = g.mass_f.to_numpy()
        keys = g.key.to_numpy()
        for i, idx in enumerate(g.index):
            other = (keys != keys[i])
            dm = np.abs(m - m[i])
            conflict_50mda.append((idx, bool(((dm <= 0.05) & other).any())))
            conflict_07da.append((idx, bool(((dm <= 0.7) & other).any())))
    d["pool_conflict_50mDa"] = pd.Series(dict(conflict_50mda))
    d["pool_conflict_0p7Da"] = pd.Series(dict(conflict_07da))
    info = {"rows_by_collection": d.collection.value_counts().to_dict(),
            "positions_by_collection": d.groupby("collection").position.nunique().to_dict(),
            "positions_without_any_pos_cid_file": {c: int(g.drop_duplicates("position").pos_cid_n_files.eq(0).sum())
                                                    for c, g in d.groupby("collection")},
            "columns": list(d.columns[:8])}
    return d, info


# ----------------------------------------------------------------------------
# attrition engine
# ----------------------------------------------------------------------------
def step_record(name: str, desc: str, frame: pd.DataFrame, keys: set, key_col="key", scaffold_col="scaffold",
                record_count: int | None = None, per_collection: dict | None = None, extra: dict | None = None) -> dict:
    sub = frame[frame[key_col].isin(keys)].drop_duplicates(key_col)
    rec = {"step": name, "description": desc, "n_compounds": len(keys),
           "n_records": record_count, **groups_summary(sub[scaffold_col])}
    if per_collection is not None:
        rec["per_collection_compounds"] = per_collection
    if extra:
        rec.update(extra)
    return rec


def run_chain(frame: pd.DataFrame, candidate_keys: set, rung_records: pd.DataFrame, muru: dict, label: str,
              key_to_smiles: dict, listing: dict, is_library: bool, steps: list) -> dict:
    """Steps 5-11 on a candidate key set. rung_records: the rows that constitute the rungs."""
    out = {}
    # step 5: identifiable parent structure
    rr = rung_records[rung_records.key.isin(candidate_keys)]
    smi_col = "SMILES" if is_library else "smiles"
    rec_col = "INCHIAUX" if is_library else "inchikey"
    cls = {}
    for k, g in rr.groupby("key"):
        ok_parse = bool(g.parse_ok.all())
        raw_match = bool((g.raw_key == g.recorded_block1).all())
        parent_match = bool((g.parent_key == g.recorded_block1).all())
        inchi_ok = bool(g.inchi_to_key_ok.all()) if "inchi_to_key_ok" in g else True
        n_full = g[rec_col].nunique()
        if not ok_parse:
            c = "UNPARSEABLE"
        elif not raw_match:
            c = "SMILES_INCHIKEY_DISAGREE"
        elif not inchi_ok:
            c = "INCHI_INCHIKEY_DISAGREE"
        elif parent_match:
            c = "CONSISTENT"
        else:
            c = "CONSISTENT_PARENT_NORMALIZATION_CHANGED_KEY"
        cls[k] = {"class": c, "n_full_inchikeys_in_rungs": int(n_full)}
    cls_s = pd.Series({k: v["class"] for k, v in cls.items()})
    s5 = set(cls_s[cls_s.isin(["CONSISTENT", "CONSISTENT_PARENT_NORMALIZATION_CHANGED_KEY"])].index)
    steps.append(step_record("5_identifiable_parent", "SMILES parses; InChIKey of the recorded SMILES matches the recorded InChIKey first block (and InChI->InChIKey where available); parent normalization applied",
                             frame, s5, record_count=int(rr[rr.key.isin(s5)].shape[0]),
                             extra={"class_counts": cls_s.value_counts().to_dict(),
                                    "keys_with_multiple_full_inchikeys_across_rungs": int(sum(v["n_full_inchikeys_in_rungs"] > 1 for k, v in cls.items() if k in s5)),
                                    "excluded_keys": sorted(set(cls_s.index) - s5)}))
    # step 6: data accessibility from listings
    if is_library:
        rr5 = rr[rr.key.isin(s5)].copy()
        rr5["stem"] = rr5.FILENAME.str.replace(r"\.mzXML$", "", regex=True)
        peak_stems = set(listing["peak"].stem)
        rr5["mzml_listed"] = rr5.stem.isin(peak_stems)
        rr5["mzxml_listed"] = rr5.stem.isin(listing["mzxml_stems"])
        rr5["zenodo_zip"] = [f"{c.lower()}_mzml_centroided_pos_cid_{int(e)}.zip" in listing["zenodo_files"] for c, e in zip(rr5.collection, rr5.ce)]
        acc = rr5.groupby("key").apply(lambda g: bool((g.mzml_listed & g.zenodo_zip).all()), include_groups=False)
        s6 = set(acc[acc].index)
        extra6 = {"rung_records_mzml_listed_on_massive": int(rr5.mzml_listed.sum()), "rung_records_mzxml_listed": int(rr5.mzxml_listed.sum()),
                  "rung_records_zenodo_zip_present": int(rr5.zenodo_zip.sum()), "rung_records_total": int(len(rr5)),
                  "raw_wiff_public": listing["summary"]["has_wiff"], "profile_mzml_public": listing["summary"]["has_profile_dir"]}
        nrec6 = int(rr5[rr5.key.isin(s6)].shape[0])
    else:
        s6 = s5
        extra6 = {"note": "design frame: every surviving key already required a listed centroided mzML for each rung (step 4)",
                  "raw_wiff_public": listing["summary"]["has_wiff"], "profile_mzml_public": listing["summary"]["has_profile_dir"]}
        nrec6 = None
    steps.append(step_record("6_centroid_data_accessible", "every rung spectrum's source file is listed as centroided mzML on MassIVE MSV000099369 and the matching Zenodo 17250693 zip exists (listings only; nothing downloaded)",
                             frame, s6, record_count=nrec6, extra=extra6))
    # step 7: precursor-preserving endpoint (documentation only; not a per-compound filter)
    s7 = s6
    steps.append(step_record("7_precursor_preserving_endpoint", "documentation-level determination, applied as a status flag, not a filter; see precursor_endpoint_status",
                             frame, s7, record_count=nrec6,
                             extra={"status": "UNDETERMINED_WITHOUT_OPENING_SPECTRA" if not is_library else "LIBRARY_QC_CENSORS_PRECURSOR_RICH_SPECTRA; MS2_WINDOW_UNDOCUMENTED"}))
    # step 8: exact connectivity overlap with any exposed population
    exposed_union = set().union(*[p["keys"] for p in muru["pops"].values()])
    rec_block1 = rr.groupby("key").recorded_block1.apply(set).to_dict()
    s8 = {k for k in s7 if k not in exposed_union and not (rec_block1.get(k, set()) & exposed_union)}
    per_pop = {name: int(len({k for k in s7 if k in p["keys"] or (rec_block1.get(k, set()) & p["keys"])})) for name, p in muru["pops"].items()}
    steps.append(step_record("8_no_exact_connectivity_overlap", "parent connectivity key and recorded InChIKey first block absent from every exposed MURU population",
                             frame, s8, extra={"overlap_by_population": per_pop, "n_removed": len(s7) - len(s8),
                                               "population_sha256": canonical_key_hash(sorted(s8))}))
    # step 9: normalized parent overlap (parent + canonical tautomer on both sides)
    ss = muru["smiles_sources"]
    muru_norm = set(exposed_union)
    for smi in ss.smiles.unique():
        c = chem(smi)
        if c["parent_key"]:
            muru_norm.add(c["parent_key"])
        if c["raw_key"]:
            muru_norm.add(c["raw_key"])
    muru_taut = set()
    for smi in ss.smiles.unique():
        t = tautomer_parent_key(smi)
        if t:
            muru_taut.add(t)
    hit_parent, hit_taut = set(), set()
    for k in s8:
        smis = key_to_smiles.get(k, [])
        for smi in smis:
            c = chem(smi)
            if c["parent_key"] in muru_norm or c["raw_key"] in muru_norm:
                hit_parent.add(k)
            t = tautomer_parent_key(smi)
            if t and (t in muru_taut or t in muru_norm):
                hit_taut.add(k)
    s9 = s8 - hit_parent - hit_taut
    steps.append(step_record("9_no_normalized_parent_overlap", "no match after parent normalization (largest organic fragment, uncharged) or RDKit canonical-tautomer normalization of both MultiMS2 and all SMILES-bearing MURU exposed records",
                             frame, s9, extra={"removed_parent_normalization": sorted(hit_parent), "removed_tautomer_normalization": sorted(hit_taut - hit_parent),
                                               "muru_smiles_records_normalized": int(ss.smiles.nunique()),
                                               "population_sha256": canonical_key_hash(sorted(s9))}))
    # step 10: primary scaffold overlap with v2 development population
    v2_scaf = set(muru["compounds"].scaffold_group)
    key_scaf = frame.drop_duplicates("key").set_index("key").scaffold.to_dict()
    s10 = {k for k in s9 if key_scaf[k] not in v2_scaf}
    seen = s9 - s10
    # sensitivity: scaffold groups of every SMILES-bearing exposed MURU record (not only v2 dev)
    all_muru_scaf = {chem(s)["scaffold"] for s in ss.smiles.unique() if chem(s)["scaffold"]}
    s10_all = {k for k in s9 if key_scaf[k] not in all_muru_scaf}
    # sensitivity: strict Morgan-count Tanimoto >= 0.55 to any v2 development compound
    v2fps = [fp for fp in (count_fp(s) for s in muru["compounds"].smiles) if fp is not None]
    near = set()
    maxsim = {}
    for k in s10:
        fp = count_fp(key_to_smiles[k][0])
        if fp is None:
            continue
        ms = max(DataStructs.BulkTanimotoSimilarity(fp, v2fps))
        maxsim[k] = ms
        if ms >= 0.55:
            near.add(k)
    steps.append(step_record("10_no_primary_scaffold_overlap", "v2 primary structural group (stereo-free Bemis-Murcko scaffold of the parent; acyclic parent is its own group) absent from the 1,325-compound v2 development population's scaffold groups",
                             frame, s10, extra={"population_sha256": canonical_key_hash(sorted(s10)),
                                                "identity_new_scaffold_seen": {"n_compounds": len(seen), **groups_summary(pd.Series([key_scaf[k] for k in seen], dtype=str)),
                                                                               "population_sha256": canonical_key_hash(sorted(seen)), "keys": sorted(seen)},
                                                "sensitivity_scaffold_new_vs_all_smiles_bearing_exposed_records": {"n_compounds": len(s10_all), **groups_summary(pd.Series([key_scaf[k] for k in s10_all], dtype=str))},
                                                "sensitivity_strict_similarity": {"n_scaffold_new_with_max_tanimoto_ge_0p55_to_v2_dev": len(near),
                                                                                  "n_scaffold_new_below_0p55": len(s10) - len(near),
                                                                                  **{f"groups_below_0p55_{kk}": vv for kk, vv in groups_summary(pd.Series([key_scaf[k] for k in s10 - near], dtype=str)).items()},
                                                                                  "max_tanimoto_quantiles": {q: float(np.quantile(list(maxsim.values()), q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)} if maxsim else {}}}))
    # step 11: remaining independent structural groups
    g11 = pd.Series([key_scaf[k] for k in s10], dtype=str)
    steps.append(step_record("11_independent_structural_groups", "v2-style scaffold groups among the scaffold-new survivors (no compound removed at this step)",
                             frame, s10, extra={"population_sha256": canonical_key_hash(sorted(s10)),
                                                "compounds_in_size_1_groups": int((g11.map(g11.value_counts()) == 1).sum())}))
    out.update(s8=s8, s9=s9, s10=s10, seen=seen)
    return out


def library_census(lib: pd.DataFrame, muru: dict, listing: dict) -> dict:
    res = {}
    key_to_smiles = lib.groupby("key").SMILES.apply(lambda s: sorted(set(s))).to_dict()
    coll_keys = lambda f: {c: int(g.key.nunique()) for c, g in f.groupby("collection")}
    verification = {"recorded_inchikey_first_block_distinct": int(lib.recorded_block1.nunique()),
                    "parent_key_distinct": int(lib.key.nunique()),
                    "full_inchikey_distinct": int(lib.INCHIAUX.nunique()), "records": int(len(lib)),
                    "polarity_counts": lib.IONMODE.value_counts().to_dict(),
                    "method_counts": lib.FRAGMENTATION_METHOD.value_counts().to_dict()}
    res["claim_verification"] = verification

    chains = {}
    for chain_name, rungs in [("CID_3RUNG_20_40_60", RUNGS3), ("CID_2RUNG_40_60", SUBSETS2["40_60"])]:
        steps = []
        s1 = set(lib.key)
        steps.append(step_record("1_all_compounds", "all released library spectra (GNPS identity tables), connectivity keys after parent normalization",
                                 lib, s1, record_count=len(lib), per_collection=coll_keys(lib)))
        pc = lib[(lib.IONMODE == "Positive") & (lib.FRAGMENTATION_METHOD == "CID")]
        steps.append(step_record("2_positive_CID", "IONMODE Positive and FRAGMENTATION_METHOD CID", lib, set(pc.key),
                                 record_count=len(pc), per_collection=coll_keys(pc),
                                 extra={"records_by_collection_energy": pc.groupby(["collection", "ce"]).size().rename("n").reset_index().to_dict("records")}))
        mh = pc[pc.ADDUCT == TARGET_ADDUCT]
        other = pc[pc.ADDUCT != TARGET_ADDUCT]
        other_keys_only = set(other.key) - set(mh.key)
        steps.append(step_record("3_target_ion_MplusH", "ADDUCT == [M+H]+", lib, set(mh.key), record_count=len(mh), per_collection=coll_keys(mh),
                                 extra={"other_adducts_records": other.ADDUCT.value_counts().to_dict(),
                                        "other_adducts_compounds": other.groupby("ADDUCT").key.nunique().sort_values(ascending=False).to_dict(),
                                        "compounds_with_other_adducts_but_no_MplusH": len(other_keys_only),
                                        "M+_radical_or_permanent_cation_compounds": int(pc[pc.ADDUCT == "[M]+"].key.nunique()),
                                        "M+Na_compounds": int(pc[pc.ADDUCT == "[M+Na]+"].key.nunique()),
                                        "M+NH4_compounds": int(pc[pc.ADDUCT == "[M+NH4]+"].key.nunique())}))
        # step 4: energy completeness within one collection (same identity, same ion, same sample campaign)
        eset = mh.groupby(["collection", "key"]).ce.apply(lambda s: set(s)).reset_index()
        eset_pool = mh.groupby("key").ce.apply(lambda s: set(s))
        comp = {}
        for c, g in eset.groupby("collection"):
            comp[c] = {"compounds_MplusH": int(len(g)), "3rung_20_40_60": int(g.ce.map(lambda s: set(RUNGS3) <= s).sum()),
                       **{f"2rung_{n}": int(g.ce.map(lambda s, r=r: set(r) <= s).sum()) for n, r in SUBSETS2.items()},
                       "energies_present_any": sorted({e for s in g.ce for e in s})}
        pooled = {"3rung_20_40_60": int(eset_pool.map(lambda s: set(RUNGS3) <= s).sum()),
                  **{f"2rung_{n}": int(eset_pool.map(lambda s, r=r: set(r) <= s).sum()) for n, r in SUBSETS2.items()}}
        ok = eset[eset.ce.map(lambda s: set(rungs) <= s)]
        s4 = set(ok.key)
        within_pairs = set(zip(ok.collection, ok.key))
        in_pair = pd.Series([(c, k) in within_pairs for c, k in zip(mh.collection, mh.key)], index=mh.index)
        rung_records = mh[in_pair & mh.ce.isin(rungs)]
        # replicate spectra per rung (multiple scans kept by the authors' QC)
        reps = rung_records.groupby(["collection", "key", "ce"]).size()
        steps.append(step_record("4_fixed_energy_completeness", f"[M+H]+ present at every rung {list(rungs)} for the same connectivity key within one collection",
                                 lib, s4, record_count=len(rung_records),
                                 per_collection={c: int(g.key.nunique()) for c, g in ok.groupby("collection")},
                                 extra={"completeness_by_collection": comp, "completeness_pooled_across_collections": pooled,
                                        "keys_complete_in_more_than_one_collection": int(ok.key.value_counts().gt(1).sum()),
                                        "records_per_rung_distribution": reps.value_counts().sort_index().to_dict()}))
        tail = run_chain(lib, s4, rung_records, muru, chain_name, key_to_smiles, listing, True, steps)
        chains[chain_name] = {"steps": steps,
                              "survivors": {"step8_no_exact_overlap": sorted(tail["s8"]), "step9_no_normalized_overlap": sorted(tail["s9"]),
                                            "step10_scaffold_new": sorted(tail["s10"]), "step11_scaffold_new": sorted(tail["s10"]),
                                            "identity_new_scaffold_seen": sorted(tail["seen"])}}
        # survivors per collection at step 10 and pool-conflict flag via position mapping is design-only
        surv = rung_records[rung_records.key.isin(tail["s10"])]
        chains[chain_name]["step10_per_collection_compounds"] = surv.groupby("collection").key.nunique().to_dict()
        s8r = rung_records[rung_records.key.isin(tail["s8"])]
        chains[chain_name]["step8_per_collection_compounds"] = s8r.groupby("collection").key.nunique().to_dict()
    res["chains"] = chains
    return res


def design_census(des: pd.DataFrame, muru: dict, listing: dict) -> dict:
    steps = []
    key_to_smiles = des.groupby("key").smiles.apply(lambda s: sorted(set(s))).to_dict()
    coll_keys = lambda f: {c: int(g.key.nunique()) for c, g in f.groupby("collection")}
    s1 = set(des.key)
    steps.append(step_record("1_all_plated_positive_compounds", "positive-mode pre-acquisition plate metadata (metadata/*_metadata_pos.tsv)", des, s1,
                             record_count=len(des), per_collection=coll_keys(des)))
    has_file = des[des.pos_cid_n_files > 0]
    steps.append(step_record("2_positive_CID_file_exists_for_pool", "pool position matched to at least one listed positive CID centroided mzML", des, set(has_file.key),
                             record_count=len(has_file), per_collection=coll_keys(has_file)))
    steps.append(step_record("3_target_ion", "not applicable in the design frame: ion formation is an MS1 acquisition outcome; [M+H]+ is the intended extraction target",
                             des, set(has_file.key), record_count=len(has_file), per_collection=coll_keys(has_file)))
    chains = {}
    for chain_name, rungs in [("CID_3RUNG_20_40_60", RUNGS3), ("CID_2RUNG_40_60", SUBSETS2["40_60"])]:
        st = list(steps)
        ok = des[des.pos_cid_energies.map(lambda s, r=rungs: set(r) <= set(s))]
        st.append(step_record("4_fixed_energy_files_present", f"pool position has listed positive CID files at every rung {list(rungs)}", des, set(ok.key),
                              record_count=len(ok), per_collection=coll_keys(ok),
                              extra={"completeness_by_collection": {c: {"compounds": int(g.key.nunique()),
                                                                        "3rung": int(g[g.pos_cid_energies.map(lambda s: set(RUNGS3) <= set(s))].key.nunique()),
                                                                        **{f"2rung_{n}": int(g[g.pos_cid_energies.map(lambda s, r=r: set(r) <= set(s))].key.nunique()) for n, r in SUBSETS2.items()}}
                                                                    for c, g in has_file.groupby("collection")}}))
        rr = ok.assign(inchi_to_key_ok=True)
        tail = run_chain(des, set(ok.key), rr, muru, chain_name, key_to_smiles, listing, False, st)
        surv = ok[ok.key.isin(tail["s10"])].drop_duplicates("key")
        chains[chain_name] = {"steps": st,
                              "survivors": {"step8_no_exact_overlap": sorted(tail["s8"]), "step10_scaffold_new": sorted(tail["s10"]),
                                            "identity_new_scaffold_seen": sorted(tail["seen"])},
                              "step10_survivors_with_same_pool_precursor_conflict_50mDa": int(ok[ok.key.isin(tail["s10"])].groupby("key").pool_conflict_50mDa.any().sum()),
                              "step10_survivors_with_same_pool_precursor_conflict_0p7Da": int(ok[ok.key.isin(tail["s10"])].groupby("key").pool_conflict_0p7Da.any().sum()),
                              "step10_per_collection_compounds": surv.groupby("collection").key.nunique().to_dict()}
    return {"chains": chains}


def main():
    t0 = time.time()
    muru = load_muru()
    listing = load_listing()
    lib, lib_info = load_library()
    des, des_info = load_design(listing)
    lib_res = library_census(lib, muru, listing)
    des_res = design_census(des, muru, listing)

    fetch_log = [json.loads(l) for l in (MD / "fetch_log.jsonl").read_text().splitlines() if l.strip()]
    for r in fetch_log:
        p = ROOT / r["file"]
        r["sha256_verified_now"] = p.exists() and sha256_file(p) == r["sha256"]
    out = {
        "census": "MultiMS2 outcome-blind identity/metadata/acquisition eligibility census",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outcome_blind_declaration": {
            "peaks_or_intensities_accessed": False,
            "files_refused_by_denylist": ["data/multims2_spectra.mgf (GitHub, peaks)", "data/MULTIMS2-PARTITION-1.tsv via plain fetcher (then fetched only through the header-verified identity path)"],
            "files_not_downloaded": ["Zenodo 17250693: 33 centroided mzML zips (6.82 GB)", "Zenodo 17417089: MultiMS2-0.0.1.zip (repository archive containing the MGF; metadata not separable from peaks)",
                                     "MassIVE MSV000099369: all mzML/mzXML, ccms_metadata .mzML.scans per-scan tables, ccms_parameters/params.xml, summary.tsv",
                                     "GitHub data/multims2_spectra.mgf"],
            "columns_dropped_unseen": {"GNPS identity TSVs": DROP_ON_LOAD, "plate metadata TSVs": []},
            "outcome_summary_columns_present_in_downloaded_tables": "none besides LIBQUALITY (dropped unseen; per the generating code a constant '1')",
            "outcome_conditioning_disclosure": "row presence in the released library is a function of the authors' spectrum QC (min 3 signals, explained intensity/signals, precursor height/purity, >=2 modalities); library-frame counts at steps 1-4 are therefore QC-conditioned. The design frame is not.",
        },
        "sources": {
            "paper": {"doi": "10.1093/gigascience/giag069", "pmcid": "PMC13312951", "pmid": "42271568", "year": 2026, "journal": "GigaScience",
                      "fulltext_retrieved": "NCBI BioC JSON (methods, table, data-availability passages read)"},
            "github": {"repo": "https://github.com/zamboni-lab/MultiMS2", "commit": "659bd9b608408a75ecbb4b03295ed4c03ba52539",
                       "commit_date": "2026-08-24", "tag": "0.0.1 (b6e1db2)", "zenodo_json_version": "0.0.2",
                       "metadata_dir_last_changed": "ae66078 2025-10-04", "data_dir_last_changed": "104eb88 2026-07-08"},
            "zenodo_mzml": {"record": 17250693, "doi": "10.5281/zenodo.17250693", "concept_doi": "10.5281/zenodo.14218308", "version": "2.0.0",
                            "publication_date": "2025-10-02", "license": "cc-zero", "n_files": 33, "total_bytes": 6818196784,
                            "previous_version": {"record": 14218309, "version": "1.0.0", "license": "cc-by-4.0", "n_files": 6}},
            "zenodo_processing": {"record": 17417089, "doi": "10.5281/zenodo.17417089", "version": "0.0.1", "publication_date": "2025-10-22",
                                  "license": "mit-license", "files": {"zamboni-lab/MultiMS2-0.0.1.zip": 23821215}},
            "massive": {"accession": "MSV000099369", "doi": "10.25345/C5GQ6RF85", "instrument": "ZenoTOF 7600 (MS:1003293)",
                        "ftp": "ftp://massive.ucsd.edu/v11/MSV000099369", "file_count_reported": 22903, "size_gb_reported": 41.0,
                        "listing_source": "GNPS2 datasetcache filename table"},
        },
        "license": {"data": "CC0 1.0 (GitHub data/LICENSE; LICENSE 'Data License (CC0)' section; Zenodo 17250693 v2.0.0 license=cc-zero; paper Data availability)",
                    "code": "MIT (GitHub LICENSE; Zenodo 17417089 mit-license)",
                    "caveat": "Zenodo mzML v1.0.0 (14218309) was CC-BY-4.0; v2.0.0 is CC0. The paper article itself is CC BY."},
        "acquisition": {
            "instrument": "SCIEX ZenoTOF 7600 with Agilent Infinity II LC stack (paper); library INSTRUMENT='qTof', INSTRUMENT_NAME ZENOTOF7600 (mzmine batch)",
            "introduction": "direct injection, 5 uL, 50:50 water:methanol 0.1% formic acid, 0.2 mL/min; IONSOURCE DI-ESI; 0.6 min method",
            "pooling": "compounds pooled about 10 per injection; pools designed to minimize precursor mass overlap",
            "ms1": "TOF MS 50-1500 m/z, 50 ms accumulation, DP 50 V, CE 10 V",
            "ms2_selection": "IDA, up to 2 precursors per cycle, dynamic background subtraction, 50 mDa target tolerance, 2 s exclusion, Zeno pulsing threshold 20,000 cps",
            "cid_energies": "20, 40, 60 V (paper). README and file names use eV/ev; for singly charged precursors the lab-frame energy in eV equals the voltage numerically",
            "ead": "12, 16, 24 electron kinetic energy (KE), 30 ms activation",
            "collision_energy_spread": "not mentioned in the paper, README or processing code; library records a single CE value per spectrum (0 multi-valued CE rows); whether the instrument method used CES cannot be confirmed without opening mzML headers",
            "ms2_scan_range": "NOT DOCUMENTED in paper, README or repository; only the MS1 range (50-1500 m/z) is stated",
            "precursor_isolation_width": "not documented (Q1 resolution unstated); mzmine chimeric check used a 0.6 Da isolation tolerance and flagged, not removed, chimeric spectra",
            "separate_injection_per_energy": True,
        },
        "processing_qc_facts": {
            "mzmine_version": "4.7.27 (paper)", "mass_detection": "Factor of lowest signal, noise factor 5.0, all MS levels",
            "fragment_scan_selection": "input_scans / all_scans (no merging)",
            "mzmine_quality_parameters": "min signals 3 / explained signals / explained intensity all DESELECTED in the batch (not applied at export)",
            "precursor_removal": "no precursor-removal option in the batch; 'Export explained signals only' = false",
            "post_export_filters_notebook_filter_spectra_consistent.py": {"charge consistency": True, "min_precursor_height": 1000.0, "min_precursor_purity": 0.9, "min_signals(num_peaks)": 3,
                                                                         "min_explained_intensity": 0.4, "min_explained_signals": 0.05, "min_intensity_ratio_to_group_max": 0.8,
                                                                         "min_signals_ratio_to_group_max": 0.4, "min_modalities": "2 (paper, README); code default 3",
                                                                         "modality": "(collision_energy, fragmentation_method) per (inchi_aux, adduct)"},
            "validate_losses.py": "adduct/loss chemical plausibility check, 47,630 -> 43,728 spectra (README)",
            "censoring_assessment": "min_signals=3 on num_peaks and min_explained_intensity=0.4 remove spectra with few signals, which at low CID energy are preferentially precursor-dominated spectra; the >=2-modality rule then removes a compound-adduct entirely when too few energies survive. The released library therefore selects on fragmentation outcome; a precursor-preserving external validation would need re-extraction from the centroided mzML over an outcome-independent frame.",
        },
        "muru_exposure": {"populations": {k: {"n_keys": len(v["keys"]), "hash_verified": v["hash_verified"], "exposure_class": v["exposure_class"]} for k, v in muru["pops"].items()},
                          "union_keys": len(set().union(*[p["keys"] for p in muru["pops"].values()])),
                          "v2_dev_compounds": int(len(muru["compounds"])), "v2_dev_scaffold_groups": int(muru["compounds"].scaffold_group.nunique()),
                          "v2_scaffold_group_recomputation_matches": f"{muru['scaffold_repro']}/{len(muru['compounds'])}",
                          "smiles_bearing_exposed_records_for_normalized_checks": int(muru["smiles_sources"].smiles.nunique())},
        "listing": listing["summary"],
        "library_frame": {"load_info": lib_info, **lib_res},
        "design_frame": {"load_info": des_info, **des_res},
        "environment": {"python": platform.python_version(), "rdkit": rdkit.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "provenance_fetch_log": fetch_log,
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else (o.item() if hasattr(o, "item") else str(o))) + "\n")
    print(f"wrote {OUT} in {out['runtime_s']} s")


if __name__ == "__main__":
    main()
