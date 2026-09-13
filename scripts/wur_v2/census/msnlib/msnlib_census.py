"""Outcome-blind MSnLib identity/metadata/acquisition eligibility census.

Reads only files saved by msnlib_fetch.py (and the footer / central-directory
helpers) under data/external/msnlib_metadata/: pre-acquisition plate metadata
(MERLIN cleaned compound tables), the Zenodo v8 compound-detection parquet
(identity columns plus 'polarity' and 'detected' only), repository listings,
Zenodo zip central directories, and method documentation. No spectral peak,
intensity or peak-derived value is read. No library MGF/JSON, raw or mzML
file is opened or downloaded.

Frames:
  DESIGN    all plated compounds joined to the public positive-mode acquisition
            files by unique sample id (outcome-free).
  DETECTED  DESIGN restricted to compound-well pairs the authors' mzmine workflow
            annotated in positive mode (Zenodo v8 parquet, polarity in
            {positive, both}); conditioned on an MS1/trigger/annotation outcome.

Run: PYTHONPATH=src /opt/miniconda3/bin/python3 msnlib_census.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/recursive-executor-framework-07dd81")
import sys
sys.path.insert(0, str(ROOT / "src"))
from muru.io.wur_provenance import canonical_key_hash  # noqa: E402
from muru.wur_v2 import identity as ID  # noqa: E402

MD = ROOT / "data" / "external" / "msnlib_metadata"
ART = ROOT / "artifacts"
OUT = ART / "wur_v2" / "external_census" / "msnlib_census.json"
PROTON = 1.007276
ELECTRON = 0.00054858
SHIFTS_OTHER = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
                "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355}
ISO_TOL = 0.7          # half of the 1.2 m/z MS2 isolation window plus 0.1 margin (MultiMS2 R3 used 0.7)
MS2_PRECURSOR_RANGE = (115.0, 2000.0)   # Supplementary Table 2, MS2 precursor selection mass range
DEV_MH_RANGE = (70.0, 1042.6)           # development precursor range (MultiMS2 protocol R5)
MS2_FIRST_MASS = 40.0                   # Supplementary Table 2
FIXED_RUNGS_NCE = (20.0, 60.0)
ASSISTED_STEPS_NCE = (15.0, 30.0, 45.0, 60.0, 75.0)
T_MAP = (-5.95552603907965, 0.8618030610784555)  # WUR nominal = a + b * LCSB nominal (frozen Stage 1 map)
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
PARQUET_LIB = {"mcebio": "mcebio", "mcescaf": "mcescaf", "nihnp": "nihnp", "otavapep": "otavapep", "enamdisc": "enamdisc",
               "enammol": "enammol", "mcedrug": "mcedrug", "mcediv_50k": "mcediv_50k_sub", "tmhtsnp": "targetmolhtsnp"}
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]
PARQUET_COLS = ["library", "unique_sample_id", "inchikey", "split_inchikey", "smiles", "polarity", "detected"]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CM = load_module("multims2_census", ROOT / "scripts/wur_v2/census/multims2_census.py")
from muru.wur_v2.external_multims2 import neutral_scaffold  # noqa: E402


def groups_summary(s: pd.Series) -> dict:
    return CM.groups_summary(s)


# ----------------------------------------------------------------------------
# chemistry per SMILES
# ----------------------------------------------------------------------------
_c: dict = {}


def chem(smi: str) -> dict:
    if smi in _c:
        return _c[smi]
    rec = CM.chem(smi) if isinstance(smi, str) and smi else {"parse_ok": False, "raw_key": None, "parent_key": None, "scaffold": None}
    rec = dict(rec)
    m = ID.parent_mol(smi) if rec.get("parse_ok") else None
    if m is not None:
        rec["parent_charge"] = int(Chem.GetFormalCharge(m))
        rec["parent_formula"] = rdMolDescriptors.CalcMolFormula(m)
        mw = float(Descriptors.ExactMolWt(m))
        rec["parent_mass"] = mw
        # [M+H]+ for neutral parents; permanent cations are [M]+ (mass of the cation)
        rec["mh"] = mw + PROTON if rec["parent_charge"] == 0 else float("nan")
        rec["m_plus"] = mw - ELECTRON * rec["parent_charge"] if rec["parent_charge"] > 0 else float("nan")
        rec["n_heavy"] = m.GetNumHeavyAtoms()
    _c[smi] = rec
    return rec


# ----------------------------------------------------------------------------
# inputs
# ----------------------------------------------------------------------------
def load_design() -> tuple[pd.DataFrame, dict]:
    parts, info = [], {}
    for lib in LIBS:
        p = MD / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        d = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
        d["library"] = LIB_LABEL[lib]
        d["lib"] = lib
        info[LIB_LABEL[lib]] = {"file": p.name, "sha256": sha256_file(p), "rows": int(len(d)),
                                "rows_missing_smiles": int(d.smiles.isna().sum()),
                                "distinct_unique_sample_ids": int(d.unique_sample_id.nunique())}
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    return d, info


def load_detected() -> tuple[pd.DataFrame, dict]:
    p = MD / "zenodo_21105617_20250828_9libraries_only_detected_cleaned.parquet"
    q = pd.read_parquet(p, columns=PARQUET_COLS)
    q["lib"] = q.library.map(PARQUET_LIB)
    info = {"file": p.name, "sha256": sha256_file(p), "rows": int(len(q)), "columns_read": PARQUET_COLS,
            "columns_not_read": "all other 356 columns (compound annotation metadata); none carries peaks or spectrum quality",
            "polarity_counts": q.polarity.value_counts().to_dict(), "detected_values": q.detected.value_counts().to_dict()}
    return q, info


def load_files() -> tuple[pd.DataFrame, dict]:
    lst = pd.read_csv(MD / "gnps2_datasetcache_MSV000094528.csv")
    lst["fn"] = lst.filepath.str.rsplit("/", n=1).str[-1]
    lst["ext"] = lst.fn.str.extract(r"\.([A-Za-z0-9]+)$")[0].str.lower()
    rows = []
    for r in lst[lst.ext.isin(["raw", "mzml"])].itertuples(index=False):
        coll = r.collection
        pol = "positive" if "positive" in coll else ("negative" if "negative" in coll else None)
        rows.append({"source": "MassIVE", "format": "raw" if r.ext == "raw" else "mzML", "fn": r.fn, "path": r.filepath,
                     "bytes": int(r.size), "polarity": pol, "collection": coll})
    zen = {}
    for p in sorted(MD.glob("zenodo_zip_central_directory_15683784_*.json")):
        z = json.loads(p.read_text())
        pol = "positive" if "positive" in z["zip"] else "negative"
        zen[z["zip"]] = {"zip_bytes": z["zip_bytes"], "members": len(z["members"])}
        for m in z["members"]:
            if m["name"].lower().endswith(".mzml"):
                rows.append({"source": "Zenodo15683784", "format": "mzML(zip member)", "fn": m["name"].rsplit("/", 1)[-1], "path": z["zip"] + "!" + m["name"],
                             "bytes": int(m["compressed"]), "bytes_uncompressed": int(m["uncompressed"]), "polarity": pol, "collection": z["zip"]})
    f = pd.DataFrame(rows)
    f["usid"] = f.fn.str.extract(r"(pluskal_.*?_id)(?=_|\.)")[0]
    f["run_date"] = f.fn.str.extract(r"^(\d{8})_")[0]
    f["variant"] = f.fn.str.extract(r"^\d{8}_(.*?)\d?pluskal_")[0].fillna("")
    f["blank_or_other"] = f.usid.isna()
    info = {"massive_rows": int(len(lst)), "massive_raw_mzml_rows": int(lst.ext.isin(["raw", "mzml"]).sum()),
            "zenodo_zip_central_directories": zen,
            "files_without_unique_sample_id": int(f.usid.isna().sum())}
    return f, info


# ----------------------------------------------------------------------------
# chain
# ----------------------------------------------------------------------------
def step(name, desc, keys, key_scaf, extra=None, per_lib=None):
    rec = {"step": name, "description": desc, "n_compounds": len(keys),
           **groups_summary(pd.Series([key_scaf[k] for k in keys], dtype=str))}
    if per_lib is not None:
        rec["per_library_compounds"] = per_lib
    if extra:
        rec.update(extra)
    return rec


def per_lib(pairs: pd.DataFrame, keys: set) -> dict:
    s = pairs[pairs.key.isin(keys)]
    return {k: int(v) for k, v in s.groupby("library").key.nunique().items()}


def run_chain(label: str, pairs: pd.DataFrame, muru: dict, ctx: dict) -> dict:
    """pairs: one row per (library, unique_sample_id, smiles) plated compound, with chemistry columns."""
    steps = []
    key_scaf = ctx["key_scaf"]
    all_keys = set(pairs.key.dropna())
    n_unparsed_rows = int(pairs.key.isna().sum())
    steps.append(step("1_all_compounds", "distinct parent connectivity keys among plated compound rows in this frame (rows with an unparseable or missing structure are counted separately)",
                      all_keys, key_scaf, per_lib=per_lib(pairs, all_keys),
                      extra={"n_rows": int(len(pairs)), "n_rows_unparseable_or_missing_structure": n_unparsed_rows}))
    # 2: positive-mode acquisition exists for a well containing the compound
    pos = pairs[pairs.has_positive_file]
    s2 = set(pos.key.dropna())
    steps.append(step("2_positive_mode_acquisition", "a positive-mode injection of a well containing the compound is publicly listed (MassIVE raw/mzML or Zenodo mzML zip member)",
                      s2, key_scaf, per_lib=per_lib(pos, s2)))
    # 3: [M+H]+ structurally formable and inside the MS2 precursor selection range
    p3 = pos[(pos.parent_charge == 0) & pos.mh.between(*MS2_PRECURSOR_RANGE)]
    s3 = set(p3.key) & s2
    perm_cation = set(pos[pos.parent_charge > 0].key)
    out_range = set(pos[(pos.parent_charge == 0) & ~pos.mh.between(*MS2_PRECURSOR_RANGE)].key) - s3
    steps.append(step("3_positive_MplusH_eligible", "parent is charge-neutral so [M+H]+ is the target ion (permanent cations excluded) and theoretical [M+H]+ lies in the documented MS2 precursor selection range 115 to 2,000 m/z; realized [M+H]+ formation and DDA triggering are NOT verifiable without scan headers",
                      s3, key_scaf, per_lib=per_lib(p3, s3),
                      extra={"n_removed_permanent_cation_parent": len(perm_cation - s3), "n_removed_MplusH_outside_115_2000": len(out_range - perm_cation)}))
    # 4: two fixed unmerged NCE rungs by design
    s4 = s3
    steps.append(step("4_two_fixed_unmerged_NCE_rungs_by_design", "every positive injection used the flow-injection MSn method whose MS2 block is Exp.1 fixed NCE 20, Exp.2 Assisted (outcome-adaptive, excluded) and Exp.3 fixed NCE 60, each a separate Orbitrap scan (Supplementary Table 2). No compound is removed at this step; whether [M+H]+ was actually triggered at both fixed rungs is a scan-header fact not read here",
                      s4, key_scaf, extra={"status": "DESIGN_LEVEL_ONLY"}))
    # 5: identifiable parent
    g = p3.groupby("key")
    cls = {}
    for k, gg in g:
        rec = set(gg.recorded_block1.dropna())
        if not gg.parse_ok.all():
            c = "UNPARSEABLE"
        elif not rec:
            c = "NO_RECORDED_INCHIKEY"
        elif len({x for x in gg.raw_key}) > 1 and not (rec & {k}):
            c = "MULTIPLE_STRUCTURES"
        elif rec == {k}:
            c = "CONSISTENT"
        elif rec & set(gg.raw_key):
            c = "CONSISTENT_PARENT_NORMALIZATION_CHANGED_KEY"
        else:
            c = "SMILES_INCHIKEY_DISAGREE"
        cls[k] = c
    cls_s = pd.Series(cls, dtype=str)
    s5 = set(cls_s[cls_s.isin(["CONSISTENT", "CONSISTENT_PARENT_NORMALIZATION_CHANGED_KEY", "NO_RECORDED_INCHIKEY"])].index) & s4
    steps.append(step("5_identifiable_parent", "cleaned SMILES parses to a parent (largest organic fragment, uncharged); recorded InChIKey first block equals the SMILES-derived or parent key (rows with no recorded InChIKey but a parseable SMILES are kept)",
                      s5, key_scaf, extra={"class_counts": cls_s.value_counts().to_dict(), "excluded_keys": sorted(set(cls_s.index) - s5)}))
    # 6: raw/unmerged data accessible
    p6 = p3[p3.key.isin(s5)]
    raw_keys = set(p6[p6.has_positive_raw].key)
    s6 = s5
    steps.append(step("6_unmerged_data_accessible", "unmerged per-injection data are public: vendor .raw (MassIVE, 7 libraries) or centroided mzML (MassIVE and/or Zenodo zip member, all 9 libraries)",
                      s6, key_scaf, extra={"n_with_vendor_raw": len(raw_keys & s6), "n_mzml_only": len(s6 - raw_keys),
                                            "mzml_only_libraries": sorted(set(p6[~p6.has_positive_raw].library))}))
    # 7: precursor-preserving endpoint possible (documentation flag)
    s7 = s6
    steps.append(step("7_precursor_preserving_endpoint_possible", "documentation-level: MS2 first mass 40 m/z and last mass automatic from the precursor (Supplementary Table 2) so [M+H]+ is inside the MS2 window; raw/mzML scans are unmerged and unfiltered. Released library spectra keep the precursor (no precursor removal; 'export explained signals only' false) but are denoised (2.5x lowest signal) and require >= 2 signals, which censors precursor-only spectra",
                      s7, key_scaf, extra={"status": "POSSIBLE_FROM_RAW_OR_MZML; LIBRARY_SPECTRA_CENSOR_LOW_SIGNAL_COUNT"}))
    # 8: exact overlap
    exposed = ctx["exposed_union"]
    rec_block = p3.groupby("key").recorded_block1.apply(lambda s: set(s.dropna())).to_dict()
    s8 = {k for k in s7 if k not in exposed and not (rec_block.get(k, set()) & exposed)}
    per_pop = {name: int(len({k for k in s7 if k in keys or (rec_block.get(k, set()) & keys)})) for name, keys in ctx["exposed_by_pop"].items()}
    steps.append(step("8_no_exact_connectivity_overlap", "parent connectivity key and recorded InChIKey first block absent from every exposed MURU population (manifest populations, v2 development, MultiMS2 ANCHOR)",
                      s8, key_scaf, extra={"overlap_by_population": per_pop, "n_removed": len(s7 - s8), "population_sha256": canonical_key_hash(sorted(s8))}))
    # 9: normalized parent overlap
    key_smiles = p3.groupby("key").smiles.apply(lambda s: sorted(set(s))).to_dict()
    hit_p, hit_t = set(), set()
    for k in s8:
        for smi in key_smiles[k]:
            c = chem(smi)
            if c["parent_key"] in ctx["muru_norm"] or c["raw_key"] in ctx["muru_norm"]:
                hit_p.add(k)
            if c.get("parent_formula") in ctx["muru_formulas"]:
                t = CM.tautomer_parent_key(smi)
                if t and (t in ctx["muru_taut"] or t in ctx["muru_norm"]):
                    hit_t.add(k)
    s9 = s8 - hit_p - hit_t
    steps.append(step("9_no_normalized_parent_overlap", "no match after parent normalization or RDKit canonical-tautomer normalization of both sides (tautomer check run for compounds sharing a parent molecular formula with an exposed record, which is exact because tautomers share formula)",
                      s9, key_scaf, extra={"removed_parent_normalization": sorted(hit_p), "removed_tautomer_normalization": sorted(hit_t - hit_p),
                                            "population_sha256": canonical_key_hash(sorted(s9))}))
    # 10: scaffold new vs v2 development
    v2s = ctx["v2_scaffolds"]
    s10 = {k for k in s9 if key_scaf[k] not in v2s}
    seen = s9 - s10
    s10b = {k for k in s10 if ctx["key_neutral_scaf"][k] not in ctx["v2_scaffolds_with_neutral"]}
    steps.append(step("10_scaffold_new_vs_v2_development", "v2 primary scaffold group (stereo-free Bemis-Murcko scaffold of the parent; acyclic parent its own group) absent from the 1,325-compound v2 development population",
                      s10, key_scaf, per_lib=per_lib(p3, s10),
                      extra={"population_sha256": canonical_key_hash(sorted(s10)),
                             "identity_new_scaffold_seen": {"n_compounds": len(seen), **groups_summary(pd.Series([key_scaf[k] for k in seen], dtype=str)),
                                                            "population_sha256": canonical_key_hash(sorted(seen))}}))
    steps.append(step("10b_charge_neutral_scaffold_new", "additionally, the charge-neutral scaffold (N-oxide oxygens and formal charges removed, rule R7 / leakage finding L-03) is absent from the v2 development primary and charge-neutral scaffolds",
                      s10b, key_scaf, per_lib=per_lib(p3, s10b), extra={"n_removed": len(s10 - s10b), "population_sha256": canonical_key_hash(sorted(s10b))}))
    g11 = pd.Series([key_scaf[k] for k in s10b], dtype=str)
    steps.append(step("11_independent_scaffold_groups", "v2 scaffold groups among the charge-neutral scaffold-new survivors (no compound removed)",
                      s10b, key_scaf, extra={"compounds_in_size_1_groups": int((g11.map(g11.value_counts()) == 1).sum()),
                                             "population_sha256": canonical_key_hash(sorted(s10b))}))
    # eligibility refinements after step 11 (structure / plate-map only)
    p11 = p3[p3.key.isin(s10b)]
    conflict_free = set(p11.groupby("key").iso_conflict.apply(lambda s: not s.all()).pipe(lambda s: s[s].index))
    single_well = set(p11.groupby("key").unique_sample_id.nunique().pipe(lambda s: s[s == 1].index))
    dev_range = set(p11[p11.mh.between(*DEV_MH_RANGE)].key)
    r_a = s10b & conflict_free
    r_b = r_a & dev_range
    r_c = r_b & single_well
    refinements = [
        step("12a_no_same_well_isolation_conflict", f"at least one positive well in which no other plated compound has an [M+H]+, [M+NH4]+, [M+Na]+, [M+K]+, [M-H2O+H]+ or 13C [M+H]+ ion (or a permanent-cation [M]+) within {ISO_TOL} m/z of the compound's [M+H]+, and no same-well isomer",
             r_a, key_scaf, per_lib=per_lib(p11, r_a)),
        step("12b_development_precursor_range", "theoretical [M+H]+ within the development precursor range 70.0 to 1,042.6 m/z", r_b, key_scaf, per_lib=per_lib(p11, r_b),
             extra={"population_sha256": canonical_key_hash(sorted(r_b))}),
        step("12c_single_positive_well", "compound plated in exactly one positive-acquired well across all nine libraries (sensitivity; multi-well compounds need a replicate rule)", r_c, key_scaf,
             per_lib=per_lib(p11, r_c), extra={"population_sha256": canonical_key_hash(sorted(r_c))}),
    ]
    # strict similarity sensitivity on 12b
    near, maxsim = set(), {}
    for k in r_b:
        fp = CM.count_fp(key_smiles[k][0])
        if fp is None:
            continue
        ms = max(DataStructs.BulkTanimotoSimilarity(fp, ctx["v2fps"]))
        maxsim[k] = ms
        if ms >= 0.55:
            near.add(k)
    sens = {"12b_with_max_morgan_count_tanimoto_ge_0p55_to_v2_dev": len(near),
            "12b_below_0p55": len(r_b - near), **{f"12b_below_0p55_{kk}": vv for kk, vv in groups_summary(pd.Series([key_scaf[k] for k in r_b - near], dtype=str)).items()},
            "max_tanimoto_quantiles": {str(q): float(np.quantile(list(maxsim.values()), q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)} if maxsim else {}}
    mz = p11[p11.key.isin(r_b)].drop_duplicates("key").mh
    return {"label": label, "steps": steps, "refinements": refinements, "strict_similarity_sensitivity": sens,
            "MplusH_mz_of_12b": {"min": float(mz.min()), "median": float(mz.median()), "max": float(mz.max())} if len(mz) else {},
            "survivors": {"step12b_keys": sorted(r_b), "note": "steps 8, 9, 10, 10b and 12c are identified by population_sha256 only (sorted keys joined by newline)"},
            "sets": {"s6": s6, "s8": s8, "s10b": s10b, "r_b": r_b, "r_c": r_c}}


def volume(pairs: pd.DataFrame, files: pd.DataFrame, keys: set) -> dict:
    """one preferred positive file per well for the wells holding these keys."""
    wells = set(pairs[pairs.key.isin(keys) & pairs.has_positive_file].unique_sample_id)
    pf = files[(files.polarity == "positive") & files.usid.isin(wells)].copy()
    # prefer the production run: for MCEBIO the 20220613 '100AGC_60000Res_' acquisition; otherwise the latest run date
    pf["pref"] = pf.variant.eq("100AGC_60000Res_").astype(int)
    out = {"n_wells": len(wells)}
    for fmt, sub in [("raw_MassIVE", pf[pf.format == "raw"]), ("mzML_MassIVE", pf[(pf.format == "mzML")]),
                     ("mzML_Zenodo_zip_member_compressed", pf[pf.format == "mzML(zip member)"])]:
        if len(sub) == 0:
            out[fmt] = {"n_wells_covered": 0, "n_files": 0, "gb": 0.0}
            continue
        one = sub.sort_values(["usid", "pref", "run_date"], ascending=[True, False, False]).drop_duplicates("usid")
        out[fmt] = {"n_wells_covered": int(one.usid.nunique()), "n_files": int(len(one)), "gb": round(one.bytes.sum() / 1e9, 3),
                    "all_variant_files_n": int(len(sub)), "all_variant_files_gb": round(sub.bytes.sum() / 1e9, 3)}
        if fmt.startswith("mzML_Zenodo"):
            out[fmt]["gb_uncompressed"] = round(one.bytes_uncompressed.sum() / 1e9, 3)
    # best available unmerged format per well: raw if on MassIVE else Zenodo mzML
    raw_w = set(pf[pf.format == "raw"].usid)
    z = pf[(pf.format == "mzML(zip member)") & ~pf.usid.isin(raw_w)].sort_values(["usid", "run_date"], ascending=[True, False]).drop_duplicates("usid")
    out["mzml_only_wells"] = int(z.usid.nunique())
    out["mzml_only_wells_zip_members_gb"] = round(z.bytes.sum() / 1e9, 3)
    out["zenodo_zips_touched"] = sorted(set(z.collection))
    return out


QUALIFICATION = {
    "claim_evaluated": "two-rung (or more) fixed-NCE transfer of the frozen v2 candidate to an independent Orbitrap instrument, >= 400 compounds in >= 250 independent scaffold groups",
    "verdict": "CONDITIONALLY_ELIGIBLE_FOR_TWO_RUNG_CLAIM_ONLY; NOT_QUALIFIED_UNTIL_HEADER_GATE_AND_ANCHOR_GATE",
    "rungs_available": "two fixed MS2 rungs, NCE 20 and NCE 60, each a separate unmerged scan; the third MS2 experiment is Thermo Assisted CE (outcome-adaptive energy selection) and cannot be a rung; no three-rung claim is possible",
    "size_margin": "design frame 39,238 compounds / 29,562 groups and detected frame 32,154 / 25,671 after all structure-only rules; the 400/250 floor survives any plausible header-level attrition",
    "blockers": [
        "B1 realized [M+H]+ MS2 at both fixed rungs is unverified: requires a frozen header-only pass over positive mzML (13.2 GB compressed Zenodo members, or 36.1 GB MassIVE mzML) that reads precursor m/z, collision energy, activation, scan window and filter string",
        "B2 energy coordinate: ID-X NCE is not the development coordinate; under the untested assumption ID-X NCE equals the WUR IQ-X NCE, NCE 20 maps to LCSB 30.12 (0.12 above the lowest development rung) and NCE 60 to 76.53; an anchor-calibrated adapter and gate must be frozen before any validation decode, and NCE 20 sits at the clamp boundary",
        "B3 unmerged scans must be re-extracted from raw or mzML with a frozen rule: released library spectra are denoised (2.5x lowest signal), need >= 2 signals, pick the highest-TIC scan, and ALL_ENERGIES merges include the Assisted scan",
        "B4 centroiding: raw MS2 is profile; the mzML conversion settings are undocumented (msconvert.bat on MassIVE unreadable, HTTP 429); a centroid and noise-threshold rule matching the development library spectra must be frozen",
        "B5 pooled flow injection (8 to 10 compounds per well, no chromatography): 17 percent of scaffold-new compounds have a theoretical same-well isolation conflict; in-source fragments and chimeric precursors need a frozen MS1-level purity rule",
        "B6 replicates: 5,091 compounds sit in more than one positive well, MCEBIO has pilot re-runs, and a precursor can be triggered more than once per injection; a replicate aggregation rule is needed",
        "B7 access: MCEDIV and TargetMol (2,218 wells, about 40 percent of the population) exist only as mzML inside Zenodo zips (no raw); MassIVE HTTPS downloads were rate-limited during this census",
        "B8 the DETECTED frame is outcome-conditioned and must not define populations, strata, exclusions or anchors",
        "B9 chemistry scope: the scaffold-new population is dominated by commercial screening and diversity sets (MCEDIV, ENAMDISC), and any claim is scoped to that chemistry",
    ],
    "anchors": "402 v2 five-rung compounds (281 groups) are plated with a public positive injection, a conflict-free well and development-range [M+H]+ (design frame), 340 (245 groups) in the detected frame; 96 of them are MultiMS2 ANCHOR compounds",
}


def main():
    t0 = time.time()
    muru = CM.load_muru()
    pops = json.loads((ART / "wur_v2/external/populations.json").read_text())
    mm2_anchor = {r["key"] for r in pops["populations"]["ANCHOR"]}
    mm2_val = {r["key"] for r in pops["populations"]["VALIDATION"]}
    exposed_by_pop = {n: p["keys"] for n, p in muru["pops"].items()}
    v2keys = set(muru["compounds"].group_key)
    exposed_by_pop["V2-DEVELOPMENT-POPULATION"] = v2keys
    exposed_by_pop["MultiMS2-ANCHOR"] = mm2_anchor
    exposed_union = set().union(*exposed_by_pop.values())
    ss = muru["smiles_sources"]
    muru_norm, muru_taut, muru_formulas = set(exposed_union), set(), set()
    for smi in ss.smiles.unique():
        c = chem(smi)
        if c.get("parent_key"):
            muru_norm.add(c["parent_key"])
        if c.get("raw_key"):
            muru_norm.add(c["raw_key"])
        if c.get("parent_formula"):
            muru_formulas.add(c["parent_formula"])
        t = CM.tautomer_parent_key(smi)
        if t:
            muru_taut.add(t)
    # MultiMS2 anchor SMILES are exposed too
    for r in pops["populations"]["ANCHOR"]:
        c = chem(r["smiles"])
        muru_norm.update(x for x in (c.get("parent_key"), c.get("raw_key")) if x)
        if c.get("parent_formula"):
            muru_formulas.add(c["parent_formula"])
        t = CM.tautomer_parent_key(r["smiles"])
        if t:
            muru_taut.add(t)
    v2 = muru["compounds"]
    v2_scaf = set(v2.scaffold_group)
    v2_scaf_neutral = v2_scaf | {neutral_scaffold(s, k) for k, s in zip(v2.smiles, v2.group_key)}
    v2fps = [fp for fp in (CM.count_fp(s) for s in v2.smiles) if fp is not None]
    long = pd.read_csv(ART / "wur_v2/data/long_aligned.csv", usecols=["group_key", "ce_numeric"])  # rung identity only
    five = set(long.groupby("group_key").ce_numeric.nunique().pipe(lambda s: s[s == 5]).index)

    design, design_info = load_design()
    det, det_info = load_detected()
    files, files_info = load_files()

    # chemistry
    uniq = design.smiles.dropna().unique()
    for smi in uniq:
        chem(smi)
    for col in ["parse_ok", "raw_key", "parent_key", "scaffold", "parent_charge", "mh", "m_plus", "parent_formula"]:
        design[col] = [chem(s).get(col) if isinstance(s, str) else None for s in design.smiles]
    design["parse_ok"] = design.parse_ok.fillna(False).astype(bool)
    design["key"] = design.parent_key
    design["recorded_block1"] = design.split_inchikey.where(design.split_inchikey.notna(), design.inchikey.str.split("-").str[0])
    design["mh"] = pd.to_numeric(design.mh, errors="coerce")
    design["m_plus"] = pd.to_numeric(design.m_plus, errors="coerce")
    design["parent_charge"] = pd.to_numeric(design.parent_charge, errors="coerce")
    # files per well
    posf = files[(files.polarity == "positive") & files.usid.notna()]
    design["has_positive_file"] = design.unique_sample_id.isin(set(posf.usid))
    design["has_positive_raw"] = design.unique_sample_id.isin(set(posf[posf.format == "raw"].usid))
    # same-well isolation conflicts
    iso = []
    for usid, g in design.groupby("unique_sample_id"):
        ions = []
        for r in g.itertuples(index=False):
            if r.key is None or not isinstance(r.key, str):
                continue
            if r.parent_charge == 0 and not np.isnan(r.mh):
                ions.append((r.key, r.parent_formula, np.array([r.mh - PROTON + s for s in SHIFTS_OTHER.values()])))
            elif not np.isnan(r.m_plus):
                ions.append((r.key, r.parent_formula, np.array([r.m_plus])))
        for r in g.itertuples(index=False):
            if not isinstance(r.key, str) or np.isnan(r.mh):
                iso.append(True)
                continue
            other = [x for x in ions if x[0] != r.key]
            clash = any(np.any(np.abs(x[2] - r.mh) <= ISO_TOL) for x in other) or any(x[1] == r.parent_formula for x in other)
            iso.append(bool(clash))
    order = design.sort_values("unique_sample_id", kind="stable").index
    # recompute in groupby order
    iso_series = pd.Series(iso, index=[i for _, g in design.groupby("unique_sample_id") for i in g.index])
    design["iso_conflict"] = iso_series.reindex(design.index).fillna(True).astype(bool)

    key_scaf = {}
    key_neutral = {}
    for k, smi in design.dropna(subset=["key"]).drop_duplicates("key")[["key", "smiles"]].itertuples(index=False):
        key_scaf[k] = chem(smi)["scaffold"] or f"__UNPARSED__{k}"
        key_neutral[k] = neutral_scaffold(smi, k)
    ctx = {"key_scaf": key_scaf, "key_neutral_scaf": key_neutral, "exposed_union": exposed_union, "exposed_by_pop": exposed_by_pop,
           "muru_norm": muru_norm, "muru_taut": muru_taut, "muru_formulas": muru_formulas, "v2_scaffolds": v2_scaf,
           "v2_scaffolds_with_neutral": v2_scaf_neutral, "v2fps": v2fps}

    design_chain = run_chain("DESIGN", design, muru, ctx)
    # detected frame
    det_pos = det[det.polarity.isin(["positive", "both"])]
    dkey = set(zip(det_pos.unique_sample_id, det_pos.split_inchikey))
    design["detected_positive"] = [(u, b) in dkey for u, b in zip(design.unique_sample_id, design.recorded_block1)]
    join_cov = {"parquet_positive_or_both_rows": int(len(det_pos)),
                "parquet_rows_matched_to_design_rows": int(len(dkey & set(zip(design.unique_sample_id, design.recorded_block1)))),
                "distinct_usid_block_pairs_in_parquet_positive": len(dkey)}
    detected_chain = run_chain("DETECTED_POSITIVE", design[design.detected_positive], muru, ctx)

    # anchors (identity-exposed compounds with the fixed-rung design and accessible data)
    def anchor_block(chain, frame):
        s6 = chain["sets"]["s6"]
        fr = frame[frame.key.isin(s6)]
        conflict_free = set(fr.groupby("key").iso_conflict.apply(lambda s: not s.all()).pipe(lambda s: s[s].index))
        devr = set(fr[fr.mh.between(*DEV_MH_RANGE)].key)
        out = {}
        for name, ks in [("v2_dev_five_rung", five), ("v2_dev_any", v2keys), ("MultiMS2_ANCHOR", mm2_anchor), ("any_exposed_population", exposed_union)]:
            base = s6 & ks
            a = base & conflict_free & devr
            out[name] = {"n_step6": len(base), "n_no_isolation_conflict_and_dev_range": len(a),
                         **{f"groups_{k}": v for k, v in groups_summary(pd.Series([key_scaf[x] for x in a], dtype=str)).items()},
                         "per_library": per_lib(fr, a), "population_sha256": canonical_key_hash(sorted(a)),
                         **({"keys": sorted(a)} if name in ("v2_dev_five_rung",) else {})}
        out["v2_dev_five_rung_by_historical_source"] = {}
        comp = pd.read_csv(ART / "wur_v2/data/compounds.csv", usecols=["group_key", "historical_class", "measured_lcsb", "measured_wur"]).set_index("group_key")
        a5 = s6 & five & conflict_free & devr
        sub = comp.loc[sorted(a5)]
        out["v2_dev_five_rung_by_historical_source"] = {"historical_class": sub.historical_class.value_counts().to_dict(),
                                                          "measured_on_both_orbitraps": int((sub.measured_lcsb & sub.measured_wur).sum())}
        return out, a5

    anchors_design, a5_design = anchor_block(design_chain, design)
    anchors_detected, a5_det = anchor_block(detected_chain, design[design.detected_positive])
    overlap_mm2 = {"design_12b_in_MultiMS2_VALIDATION": len(design_chain["sets"]["r_b"] & mm2_val),
                   "detected_12b_in_MultiMS2_VALIDATION": len(detected_chain["sets"]["r_b"] & mm2_val)}

    vol = {
        "all_positive_public_files": {
            "raw_MassIVE": {"n": int((posf.format == "raw").sum()), "gb": round(posf[posf.format == "raw"].bytes.sum() / 1e9, 2)},
            "mzML_MassIVE": {"n": int((posf.format == "mzML").sum()), "gb": round(posf[posf.format == "mzML"].bytes.sum() / 1e9, 2)},
            "mzML_Zenodo_zip_members": {"n": int((posf.format == "mzML(zip member)").sum()), "gb_compressed": round(posf[posf.format == "mzML(zip member)"].bytes.sum() / 1e9, 2),
                                         "gb_uncompressed": round(posf[posf.format == "mzML(zip member)"].bytes_uncompressed.sum() / 1e9, 2)}},
        "design_anchors_v2_five_rung": volume(design, files, a5_design),
        "design_validation_12b": volume(design, files, design_chain["sets"]["r_b"]),
        "design_anchors_plus_validation_12b": volume(design, files, a5_design | design_chain["sets"]["r_b"]),
        "detected_anchors_v2_five_rung": volume(design, files, a5_det),
        "detected_validation_12b": volume(design, files, detected_chain["sets"]["r_b"]),
        "detected_anchors_plus_validation_12b": volume(design, files, a5_det | detected_chain["sets"]["r_b"]),
    }
    per_library_files = posf.groupby(["format", "collection"]).agg(n=("bytes", "size"), gb=("bytes", lambda s: round(s.sum() / 1e9, 3))).reset_index().to_dict("records")
    wells_pos = {LIB_LABEL[l]: {"plated_wells": int(design[design.lib == l].unique_sample_id.nunique()),
                                "wells_with_positive_file": int(design[(design.lib == l) & design.has_positive_file].unique_sample_id.nunique()),
                                "wells_with_positive_raw": int(design[(design.lib == l) & design.has_positive_raw].unique_sample_id.nunique())} for l in LIBS}
    multiwell = design[design.has_positive_file].dropna(subset=["key"]).groupby("key").unique_sample_id.nunique()

    for ch in (design_chain, detected_chain):
        ch.pop("sets")
    fetch_log = [json.loads(l) for l in (MD / "fetch_log.jsonl").read_text().splitlines() if l.strip()]
    energy_map = {f"IDX_NCE_{int(e)}": {"LCSB_coordinate_if_IDX_NCE_equals_WUR_IQX_NCE": round((e - T_MAP[0]) / T_MAP[1], 3)} for e in (15, 20, 30, 45, 60, 75)}
    out = {
        "census": "MSnLib outcome-blind identity/metadata/acquisition eligibility census",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outcome_blind_declaration": {
            "peaks_or_intensities_accessed": False,
            "files_not_downloaded": ["Zenodo 21105617: all 72 MGF/JSON spectral library files (17.6 GB; carry peaks)",
                                      "Zenodo 13785391 / 13891125: raw zips (77.9 GB positive, 43.4 GB negative)",
                                      "Zenodo 15683784: all 18 mzML zips (21.6 GB); only their ZIP central directories (member names and sizes) were range-read",
                                      "MassIVE MSV000094528: every .raw and .mzML file, ccms_parameters/params.xml",
                                      "GNPS2 MSNLIB-POSITIVE / MSNLIB-NEGATIVE libraries"],
            "partial_reads": ["Zenodo v8 parquet footer (schema only) range-read before the full download; the parquet was then downloaded because its 363 columns are compound metadata plus 'polarity' and 'detected'",
                              "ZIP central directories of the 9 positive mzML zips in Zenodo 15683784 (names and sizes only)"],
            "columns_read": {"MERLIN cleaned compound tables": ID_COLS, "Zenodo v8 detected parquet": PARQUET_COLS},
            "columns_dropped_unseen": "none of the read tables carries a peak, intensity, entropy, peak-count or explained-intensity column; unread columns are compound annotation metadata (database identifiers, classifications, vendor plate/stock metadata including an ENAMMOL vendor 'QUALITY CONTROL' column about the compound stock)",
            "outcome_conditioning_disclosure": "the DETECTED frame is conditioned on the authors' mzmine annotation in positive mode (MS1 ion formation, DDA trigger at intensity >= 6e5 and MSn-tree annotation for some adduct). It must not define any validation population, exclusion, stratum or anchor (leakage finding L-02 analogue). The DESIGN frame is outcome-free.",
        },
        "sources": {
            "paper": {"doi": "10.1038/s41592-025-02813-0", "citation": "Brungs, Schmid, Heuckeroth et al., Nat Methods 22, 2028-2031 (2025)", "pmcid": "PMC12510872", "pmid": "40954295",
                      "read": "PMC BioC full text (main text, methods, data and code availability) and Supplementary Information MOESM1 (Supplementary Notes 3-4, Supplementary Tables 1-2)"},
            "zenodo_spectral_libraries": {"concept_doi": "10.5281/zenodo.11163380", "current_version_doi": "10.5281/zenodo.21105617", "version_index": 7, "versions_total": 8,
                                          "publication_date": "2026-07-01", "files": 73, "gb": 17.62, "license": "cc-by-4.0",
                                          "note": "Zenodo reports no version string; v8 is version index 7 of 8 in the concept record"},
            "zenodo_raw_positive": {"concept_doi": "10.5281/zenodo.10966404", "latest_doi": "10.5281/zenodo.13785391", "zips": 7, "gb": 77.94, "license": "cc-by-4.0", "libraries": "7 original (no MCEDIV, no TargetMol)"},
            "zenodo_raw_negative": {"concept_doi": "10.5281/zenodo.10967081", "latest_doi": "10.5281/zenodo.13891125", "zips": 7, "gb": 43.41, "license": "cc-by-4.0"},
            "zenodo_mzml": {"concept_doi": "10.5281/zenodo.10966280", "latest_doi": "10.5281/zenodo.15683784", "zips": 18, "gb": 21.63, "license": "cc-by-4.0", "libraries": "all 9"},
            "massive": {"accession": "MSV000094528", "files_reported": 18281, "gb_reported": 254.17, "instrument": "Orbitrap ID-X (MS:1003112)", "license_per_paper": "CC0 1.0",
                        "libraries": "7 original, raw and mzML per injection; MCEDIV and TargetMol not deposited"},
            "github": {"merlin": {"repo": "https://github.com/merlin-ms/mass-spectral-library-network", "commit": "ed7f85ff395259dfa1e74bb58b1133909de433a1", "license": "MIT"},
                       "msn_tree_library": {"repo": "https://github.com/corinnabrungs/msn_tree_library", "commit": "eec6911dd767eb24dbc987e27b6a9a3cd1124f65", "license": "MIT"}},
        },
        "acquisition": {
            "instrument": "Thermo Orbitrap ID-X Tribrid, Vanquish Horizon dual-pump flow injection (3 min run, about 1.5 min plateau), H-ESI 3,000 V positive",
            "pools": "8 to 10 compounds per well (NIHNP up to 7); one positive and one negative injection per well",
            "ms1": "Orbitrap 30k, 115 to 2,000 m/z, top-3 DDA, MS2 intensity threshold 6e5 (positive), dynamic exclusion 3 times within 200 s then 70 s, 0.2 m/z",
            "ms2": {"isolation": "quadrupole, 1.2 m/z", "activation": "HCD", "energy_type": "Normalized (%) for all experiments",
                    "experiments": {"Exp.1": "Fixed NCE 20", "Exp.2": "Assisted NCE 15, 30, 45, 60, 75", "Exp.3": "Fixed NCE 60"},
                    "assisted_definition": "Thermo Tribrid Assisted Collision Energy: hidden ion-trap scans build a precursor breakdown curve and the analytical scan uses the first energy at which unreacted precursor falls below a user threshold (Thermo poster PO65258, ASMS 2018). Outcome-adaptive; not a fixed rung.",
                    "separate_scans": "each experiment is its own Orbitrap scan (up to 9 MS2 scans per precursor); nothing is merged at acquisition",
                    "orbitrap_resolution": 15000, "first_mass": MS2_FIRST_MASS, "last_mass": "automatic (not stated)", "agc_target": 1.2e4, "max_it_ms": 50, "data_type": "profile",
                    "precursor_selection_range": list(MS2_PRECURSOR_RANGE)},
            "msn": "MS3 top-5 from the Assisted MS2 scan at NCE 20/40/60, MS4 top-2 from 40, MS5 top-1 at 40/60 (not relevant to MURU)",
            "pilot_variants": "MCEBIO 20220601 pilot runs (Methods 1 and 2, 24 wells) and the 20220613 production run (Method 3); per Supplementary Note 3 the MS1 and MS2 settings are unchanged across methods",
            "fixed_rungs_nce": list(FIXED_RUNGS_NCE),
            "energy_coordinate_note": energy_map,
        },
        "processing_qc_facts": {
            "mzmine_batch": "MERLIN libraries/MSnLib/FI_MSn/config/mzmine_msn_library_pos.mzbatch",
            "mass_detection": "factor of lowest signal, noise factor 2.5, denormalize fragment scans (traps) true",
            "scan_signal_removal": "149.665-149.737 and 173.509-173.541 m/z for MS level >= 2",
            "adducts_searched_positive": ["[M]+ (intrinsic)", "[M+H]+", "[M+Na]+", "[M+NH4]+", "[M-H2O]+", "[M-H2O+H]+", "[M-2H2O+H]+"],
            "annotation_tolerance": "0.0015 m/z or 8 ppm; restricted to compounds of the well by unique_sample_id",
            "library_export": {"spectype_single_best_scan": "highest TIC scan per precursor and energy", "SAME_ENERGY": "merge of repeated scans at one energy (max signal height)",
                               "ALL_ENERGIES": "merge across the three MS2 experiments, including the Assisted scan", "ALL_MSN_TO_PSEUDO_MS2": "whole tree merged",
                               "min_signals": 2, "explained_intensity_filter": "off", "explained_signals_filter": "off", "export_explained_signals_only": False,
                               "precursor_removal": "none", "chimeric": "flagged, not removed (purity 0.75, 0.6 m/z isolation tolerance)"},
            "consequence_for_mu": "released library spectra include the precursor but are denoised at 2.5x the lowest signal and drop spectra with fewer than 2 signals; single-best-scan selection by TIC is outcome-dependent; the ALL_ENERGIES merge contains the outcome-adaptive Assisted scan. A MURU endpoint should be re-extracted from unmerged raw/mzML scans with a pre-registered rule.",
        },
        "muru_exposure": {"populations": {n: len(k) for n, k in exposed_by_pop.items()}, "union_keys": len(exposed_union),
                          "normalized_key_universe": len(muru_norm), "tautomer_key_universe": len(muru_taut),
                          "v2_dev_compounds": int(len(v2)), "v2_dev_scaffold_groups": int(len(v2_scaf)), "v2_dev_five_rung_keys": len(five),
                          "manifest_hashes_verified": {n: p["hash_verified"] for n, p in muru["pops"].items()},
                          "v2_scaffold_group_recomputation_matches": f"{muru['scaffold_repro']}/{len(v2)}"},
        "inputs": {"design_tables": design_info, "detected_parquet": det_info, "files": files_info, "detected_join": join_cov},
        "listing": {"positive_wells_per_library": wells_pos, "positive_files_per_collection": per_library_files,
                    "compounds_with_multiple_positive_wells": int((multiwell > 1).sum()), "compounds_with_positive_wells": int(len(multiwell))},
        "design_frame": design_chain,
        "detected_frame": detected_chain,
        "anchors": {"definition": "step-6 compounds (positive injection public, [M+H]+ eligible, identifiable parent, unmerged data public) that are identity-exposed, with a conflict-free well and [M+H]+ in 70.0 to 1,042.6",
                    "design": anchors_design, "detected": anchors_detected, "overlap_with_MultiMS2_VALIDATION_not_exposed": overlap_mm2},
        "volume": vol,
        "qualification": QUALIFICATION,
        "environment": {"python": platform.python_version(), "rdkit": rdkit.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "scripts": {"fetch": "msnlib_fetch.py", "parquet_footer": "parquet_footer.py", "zip_central_directory": "zip_cd.py", "zip_preview": "zip_preview.py", "census": "msnlib_census.py",
                    "copies": "data/external/msnlib_metadata/_scripts/"},
        "provenance_fetch_log": fetch_log,
        "provenance_outside_logger": [
            {"url": "https://zenodo.org/api/records/21105617", "saved": "session scratchpad (curl preview), re-fetched through the logger"},
            {"url": "header-only Range reads (first 8 KB) of the 18 MERLIN compound TSVs on raw.githubusercontent.com at commit ed7f85f", "saved": "nothing (column names only)"},
            {"url": "https://documents.thermofisher.com/TFS-Assets/CMD/posters/po-65258-lc-assisted-ce-asms2018-po65258-en.pdf via WebFetch", "saved": "tool cache; re-fetched through the logger"},
            {"url": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-025-02813-0/MediaObjects/41592_2025_2813_MOESM{1..5}_ESM.pdf", "saved": "nothing (HTTP status probe; MOESM4/5 returned 403)"},
            {"url": "NCBI PMC ID converter via PubMed tool, DOI 10.1038/s41592-025-02813-0", "saved": "nothing", "note": "PMCID PMC12510872, PMID 40954295"},
            {"url": "https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?file=f.MSV000094528/updates/.../20240405_MSn_positive/{msconvert.bat, *_seq_combined.csv, excl_pos.csv}", "saved": "nothing", "note": "HTTP 429 rate limit"},
        ],
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else (o.item() if hasattr(o, "item") else str(o))) + "\n")
    print(f"wrote {OUT} in {out['runtime_s']} s")


if __name__ == "__main__":
    main()
