"""
Reconstruct the frozen DESIGN 12b MSnLib population, draw the frozen one-time
sample, and map it to required positive-mode mzML files against the user-
provided MassIVE MSV000094528 file inventory. Structure/identity/acquisition
metadata only. No peak array is opened; no mu is computed.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
sys.path.insert(0, str(REPO / "src"))
from muru.wur_v2 import identity as ID  # noqa: E402

MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
DOWNLOADS = Path("/Users/aryav/Downloads")

PROTON = 1.007276
ELECTRON = 0.00054858
SHIFTS_OTHER = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
                "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355}
ISO_TOL = 0.7
MS2_PRECURSOR_RANGE = (115.0, 2000.0)
DEV_MH_RANGE = (70.0, 1042.6)

LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]

_c: dict = {}


def chem(smi: str) -> dict:
    if smi in _c:
        return _c[smi]
    rec = {"parse_ok": False, "raw_key": None, "parent_key": None, "scaffold": None}
    m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) and smi else None
    if m0 is not None:
        from rdkit.Chem import inchi
        rk = inchi.MolToInchiKey(m0)
        pk = ID.parent_connectivity_key(smi)
        rec.update(parse_ok=bool(rk) and pk is not None, raw_key=rk.split("-")[0] if rk else None, parent_key=pk)
        if pk is not None:
            rec["scaffold"] = ID.scaffold_group_v2(smi, pk)
    m = ID.parent_mol(smi) if rec.get("parse_ok") else None
    if m is not None:
        rec["parent_charge"] = int(Chem.GetFormalCharge(m))
        rec["parent_formula"] = rdMolDescriptors.CalcMolFormula(m)
        mw = float(Descriptors.ExactMolWt(m))
        rec["parent_mass"] = mw
        rec["mh"] = mw + PROTON if rec["parent_charge"] == 0 else float("nan")
        rec["m_plus"] = mw - ELECTRON * rec["parent_charge"] if rec["parent_charge"] > 0 else float("nan")
    _c[smi] = rec
    return rec


def load_design() -> pd.DataFrame:
    parts = []
    for lib in LIBS:
        p = MD / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        d = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
        d["library"] = LIB_LABEL[lib]
        d["lib"] = lib
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def main():
    print("loading design tables (identity/plate only)...", file=sys.stderr)
    design = load_design()
    print(f"design rows: {len(design)}", file=sys.stderr)

    uniq = design.smiles.dropna().unique()
    print(f"unique SMILES: {len(uniq)}; computing chem()...", file=sys.stderr)
    for smi in uniq:
        chem(smi)
    for col in ["parse_ok", "raw_key", "parent_key", "scaffold", "parent_charge", "mh", "m_plus", "parent_formula"]:
        design[col] = [chem(s).get(col) if isinstance(s, str) else None for s in design.smiles]
    design["parse_ok"] = design.parse_ok.fillna(False).astype(bool)
    design["key"] = design.parent_key
    design["mh"] = pd.to_numeric(design.mh, errors="coerce")
    design["m_plus"] = pd.to_numeric(design.m_plus, errors="coerce")
    design["parent_charge"] = pd.to_numeric(design.parent_charge, errors="coerce")

    # key -> scaffold, first occurrence in LIBS concat order (matches msnlib_census.py exactly)
    key_scaf = {}
    for k, smi in design.dropna(subset=["key"]).drop_duplicates("key")[["key", "smiles"]].itertuples(index=False):
        key_scaf[k] = chem(smi)["scaffold"] or f"__UNPARSED__{k}"

    # --- load the frozen, already-verified DESIGN 12b key list ---
    census = json.loads((REPO / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    step12b_keys = census["design_frame"]["survivors"]["step12b_keys"]
    expected_pop_hash = "8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e"
    recomputed_pop_hash = hashlib.sha256("\n".join(sorted(step12b_keys)).encode()).hexdigest()
    assert recomputed_pop_hash == expected_pop_hash, (recomputed_pop_hash, expected_pop_hash)
    print(f"DESIGN 12b population hash verified: {recomputed_pop_hash}", file=sys.stderr)

    missing = [k for k in step12b_keys if k not in key_scaf]
    print(f"step12b keys missing a scaffold from freshly-fetched tables: {len(missing)}", file=sys.stderr)
    assert not missing, missing[:20]

    # --- STEP 3/4: exact sorted eligible scaffold-group list + its hash, BEFORE sampling ---
    eligible_group_ids = sorted({key_scaf[k] for k in step12b_keys})
    group_list_sha256 = hashlib.sha256("\n".join(eligible_group_ids).encode()).hexdigest()
    print(f"n eligible groups: {len(eligible_group_ids)}", file=sys.stderr)
    print(f"eligible-group-list sha256 (recorded BEFORE sampling): {group_list_sha256}", file=sys.stderr)

    # --- STEP 5: draw exactly one sample, exactly as pinned ---
    rng = np.random.default_rng(20261010)
    sampled_groups = rng.choice(np.array(eligible_group_ids, dtype=object), size=2000, replace=False)
    sampled_groups_set = set(sampled_groups.tolist())
    print(f"sampled groups: {len(sampled_groups_set)} (should be 2000, no duplicates)", file=sys.stderr)
    assert len(sampled_groups_set) == 2000

    sampled_keys = sorted(k for k in step12b_keys if key_scaf[k] in sampled_groups_set)
    print(f"sampled compounds (design 12b keys in sampled groups): {len(sampled_keys)}", file=sys.stderr)

    # --- gather every positive well each sampled compound is plated in ---
    dsub = design[design.key.isin(sampled_keys)].copy()
    dsub = dsub.dropna(subset=["unique_sample_id"])

    # --- iso-conflict recomputation restricted to wells touching a sampled compound,
    #     to identify which specific well(s) are conflict-free (12a), matching msnlib_census.py exactly ---
    relevant_wells = set(dsub.unique_sample_id)
    well_rows = design[design.unique_sample_id.isin(relevant_wells)].copy()
    iso_flag = {}
    for usid, g in well_rows.groupby("unique_sample_id"):
        ions = []
        for r in g.itertuples(index=False):
            if r.key is None or not isinstance(r.key, str):
                continue
            if r.parent_charge == 0 and not np.isnan(r.mh):
                ions.append((r.key, r.parent_formula, np.array([r.mh - PROTON + s for s in SHIFTS_OTHER.values()])))
            elif not np.isnan(r.m_plus):
                ions.append((r.key, r.parent_formula, np.array([r.m_plus])))
        for r in g.itertuples(index=False):
            idx = (usid, r.key)
            if not isinstance(r.key, str) or np.isnan(r.mh):
                iso_flag[idx] = True
                continue
            other = [x for x in ions if x[0] != r.key]
            clash = any(np.any(np.abs(x[2] - r.mh) <= ISO_TOL) for x in other) or any(x[1] == r.parent_formula for x in other)
            iso_flag[idx] = bool(clash)

    dsub["iso_conflict"] = [iso_flag.get((u, k), True) for u, k in zip(dsub.unique_sample_id, dsub.key)]
    dsub["scaffold_group"] = dsub.key.map(key_scaf)
    dsub["in_dev_mh_range"] = dsub.mh.between(*DEV_MH_RANGE)

    # per compound: does it have >=1 conflict-free, dev-range well? (this is exactly what admitted it to 12b)
    conflict_free_wells = dsub[(~dsub.iso_conflict) & dsub.in_dev_mh_range]
    keys_with_conflict_free_well = set(conflict_free_wells.key)
    keys_missing_conflict_free_well = sorted(set(sampled_keys) - keys_with_conflict_free_well)
    print(f"sampled compounds with >=1 conflict-free dev-range well: {len(keys_with_conflict_free_well)} "
          f"(missing: {len(keys_missing_conflict_free_well)})", file=sys.stderr)

    # required wells = minimal (conflict-free) wells per compound; fall back to all its wells if none is conflict-free
    # (should not happen for true 12b members, but disclosed rather than silently dropped if it does)
    required_rows = pd.concat([
        conflict_free_wells,
        dsub[dsub.key.isin(keys_missing_conflict_free_well)],
    ], ignore_index=True) if keys_missing_conflict_free_well else conflict_free_wells

    required_wells = sorted(required_rows.unique_sample_id.dropna().unique())
    print(f"required distinct wells (unique_sample_id): {len(required_wells)}", file=sys.stderr)

    # --- match wells to the user-provided MassIVE positive mzML inventory ---
    inv = pd.read_csv(DOWNLOADS / "MSnLib_positive_mzML_file_inventory.csv")
    inv["usid"] = inv.filename.str.extract(r"(pluskal_.*?_id)(?=_|\.)")[0]
    fn_base = inv.filename.str.rsplit("/", n=1).str[-1]
    # primary tie-break: exactly the rule already used by scripts/wur_v2/census/msnlib/msnlib_census.py
    # volume() (production variant '100AGC_60000Res_', else latest run_date) -- reused, not reinvented.
    inv["run_date"] = fn_base.str.extract(r"^(\d{8})_")[0]
    inv["variant"] = fn_base.str.extract(r"^\d{8}_(.*?)\d?pluskal_")[0].fillna("")
    inv["pref"] = inv.variant.eq("100AGC_60000Res_")
    # secondary tie-break, only for candidates the rule above still leaves tied (a duplicate-
    # acquisition pattern -- a plain file plus a later resubmission-timestamped file at the same
    # run_date -- that no existing frozen code in this program has had to resolve before): prefer
    # the plain filename (no trailing resubmission timestamp); flagged, never silently dropped.
    inv["has_resubmit_suffix"] = fn_base.str.contains(r"_\d{10,}(?:_MSn_positive)?\.mzML$", regex=True)

    def pick_one(g: pd.DataFrame) -> pd.Series:
        g = g.sort_values(["pref", "run_date", "has_resubmit_suffix", "filename"],
                          ascending=[False, False, True, True])
        chosen = g.iloc[0]
        return pd.Series({"filename": chosen.filename, "collection": chosen.collection, "size_mb": chosen.size_mb,
                           "n_candidates": len(g), "candidate_filenames": ";".join(g.filename)})

    well_to_file = inv.groupby("usid").apply(pick_one)

    avail_rows, unavail_rows = [], []
    for _, r in required_rows.drop_duplicates(["unique_sample_id", "key"]).iterrows():
        usid = r.unique_sample_id
        if usid in well_to_file.index:
            f = well_to_file.loc[usid]
            avail_rows.append({
                "scaffold_group": r.scaffold_group, "compound_key": r.key, "library": r.library,
                "plate_id": r.plate_id, "well_location": r.well_location, "unique_sample_id": usid,
                "filename": f["filename"], "collection": f["collection"], "size_mb": f["size_mb"],
                "duplicate_acquisition_at_well": bool(f["n_candidates"] > 1),
                "candidate_filenames_if_duplicate": f["candidate_filenames"] if f["n_candidates"] > 1 else "",
            })
        else:
            unavail_rows.append({
                "scaffold_group": r.scaffold_group, "compound_key": r.key, "library": r.library,
                "plate_id": r.plate_id, "well_location": r.well_location, "unique_sample_id": usid,
            })

    avail_df = pd.DataFrame(avail_rows).drop_duplicates()
    unavail_df = pd.DataFrame(unavail_rows).drop_duplicates()

    required_files = avail_df.drop_duplicates("filename") if len(avail_df) else avail_df
    n_files_available = required_files.filename.nunique() if len(required_files) else 0
    total_size_mb = required_files.size_mb.sum() if len(required_files) else 0
    n_duplicate_wells = int(avail_df.duplicate_acquisition_at_well.sum()) if len(avail_df) else 0

    unavail_wells = sorted(unavail_df.unique_sample_id.unique()) if len(unavail_df) else []
    unavail_libs = sorted(unavail_df.library.unique()) if len(unavail_df) else []
    unavail_compounds = sorted(unavail_df.compound_key.unique()) if len(unavail_df) else []
    unavail_groups = sorted(unavail_df.scaffold_group.unique()) if len(unavail_df) else []

    # write outputs: CSV keeps one row per (compound, well/file) -- a well can be shared by
    # more than one sampled compound (pooled-well acquisition) -- the TXT is the deduplicated
    # file list actually needed for download.
    OUT_CSV = REPO / "MSnLib_required_mzML_downloads.csv"
    OUT_TXT = REPO / "MSnLib_required_mzML_downloads.txt"
    if len(avail_df):
        avail_df.sort_values(["collection", "filename", "compound_key"]).to_csv(OUT_CSV, index=False)
        OUT_TXT.write_text("\n".join(sorted(avail_df.filename.unique())) + "\n")
    else:
        pd.DataFrame(columns=["scaffold_group", "compound_key", "library", "plate_id", "well_location",
                               "unique_sample_id", "filename", "collection", "size_mb",
                               "duplicate_acquisition_at_well", "candidate_filenames_if_duplicate"]).to_csv(OUT_CSV, index=False)
        OUT_TXT.write_text("")

    summary = {
        "design_12b_population": {"n_compounds": len(step12b_keys), "n_groups": len(eligible_group_ids),
                                   "population_sha256_expected": expected_pop_hash, "population_sha256_recomputed": recomputed_pop_hash},
        "eligible_group_list": {"n_groups": len(eligible_group_ids), "sha256": group_list_sha256},
        "sample": {"seed": 20261010, "n_groups_sampled": len(sampled_groups_set), "n_compounds_in_sampled_groups": len(sampled_keys)},
        "required_wells": {"n_distinct_wells": len(required_wells)},
        "required_files": {"n_required_wells_total": len(required_wells), "n_files_available_on_massive": int(n_files_available),
                            "n_wells_with_duplicate_acquisition_needing_tiebreak": n_duplicate_wells,
                            "total_expected_download_mb": float(total_size_mb),
                            "total_expected_download_gb": round(float(total_size_mb) / 1000, 3)},
        "unavailable": {"n_wells_unavailable_on_massive": len(unavail_wells), "n_compounds_touching_unavailable_wells": len(unavail_compounds),
                         "n_scaffold_groups_touching_unavailable_wells": len(unavail_groups), "libraries": unavail_libs},
        "keys_missing_conflict_free_well_in_resample": keys_missing_conflict_free_well,
    }
    (REPO / "artifacts" / "wur_v2_confirmation").mkdir(parents=True, exist_ok=True)
    (MD / "manifest_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

    # save intermediate state for further inspection
    dsub.to_parquet(MD / "sampled_compound_wells.parquet")
    pd.Series(sorted(sampled_groups_set)).to_csv(MD / "sampled_groups.csv", index=False, header=["scaffold_group"])
    pd.Series(sampled_keys).to_csv(MD / "sampled_keys.csv", index=False, header=["compound_key"])
    if len(unavail_df):
        unavail_df.to_csv(MD / "unavailable_wells.csv", index=False)


if __name__ == "__main__":
    main()
