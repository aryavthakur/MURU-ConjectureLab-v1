"""Determine the exact anchor wells/files needed for parser preflight (Step 6),
using the same identity tables already fetched and verified for the DESIGN 12b
reconstruction. Structure/identity/acquisition metadata only."""
from __future__ import annotations
import hashlib
import json
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
ZENODO_DIR = Path("/Users/aryav/muru-msnlib/zenodo")

PROTON = 1.007276
SHIFTS_OTHER = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
                "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355}
ISO_TOL = 0.7
DEV_MH_RANGE = (70.0, 1042.6)
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]

_c: dict = {}


def chem(smi):
    if smi in _c:
        return _c[smi]
    rec = {"parse_ok": False, "parent_key": None, "scaffold": None}
    m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) and smi else None
    if m0 is not None:
        pk = ID.parent_connectivity_key(smi)
        rec.update(parse_ok=pk is not None, parent_key=pk)
        if pk is not None:
            rec["scaffold"] = ID.scaffold_group_v2(smi, pk)
    m = ID.parent_mol(smi) if rec.get("parse_ok") else None
    if m is not None:
        rec["parent_charge"] = int(Chem.GetFormalCharge(m))
        rec["parent_formula"] = rdMolDescriptors.CalcMolFormula(m)
        mw = float(Descriptors.ExactMolWt(m))
        rec["mh"] = mw + PROTON if rec["parent_charge"] == 0 else float("nan")
        rec["m_plus"] = mw - 0.00054858 * rec["parent_charge"] if rec["parent_charge"] > 0 else float("nan")
    _c[smi] = rec
    return rec


def load_design():
    parts = []
    for lib in LIBS:
        p = MD / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        d = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
        d["library"] = LIB_LABEL[lib]
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def main():
    design = load_design()
    uniq = design.smiles.dropna().unique()
    for smi in uniq:
        chem(smi)
    for col in ["parse_ok", "parent_key", "scaffold", "parent_charge", "mh", "m_plus", "parent_formula"]:
        design[col] = [chem(s).get(col) if isinstance(s, str) else None for s in design.smiles]
    design["key"] = design.parent_key
    design["mh"] = pd.to_numeric(design.mh, errors="coerce")
    design["m_plus"] = pd.to_numeric(design.m_plus, errors="coerce")
    design["parent_charge"] = pd.to_numeric(design.parent_charge, errors="coerce")

    census = json.loads((REPO / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    anchor_keys = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
    print(f"anchor keys: {len(anchor_keys)}", file=sys.stderr)

    relevant_wells = set(design[design.key.isin(anchor_keys)].dropna(subset=["unique_sample_id"]).unique_sample_id)
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

    asub = design[design.key.isin(anchor_keys)].dropna(subset=["unique_sample_id"]).copy()
    asub["iso_conflict"] = [iso_flag.get((u, k), True) for u, k in zip(asub.unique_sample_id, asub.key)]
    asub["in_dev_mh_range"] = asub.mh.between(*DEV_MH_RANGE)
    conflict_free = asub[(~asub.iso_conflict) & asub.in_dev_mh_range]
    keys_with_well = set(conflict_free.key)
    missing = anchor_keys - keys_with_well
    print(f"anchor keys with >=1 conflict-free dev-range well: {len(keys_with_well)} (missing: {len(missing)})", file=sys.stderr)

    required = pd.concat([conflict_free, asub[asub.key.isin(missing)]], ignore_index=True) if len(missing) else conflict_free
    required_wells = sorted(required.unique_sample_id.dropna().unique())
    print(f"required anchor wells: {len(required_wells)}", file=sys.stderr)

    # match against MassIVE inventory
    inv = pd.read_csv(DOWNLOADS / "MSnLib_positive_mzML_file_inventory.csv")
    inv["usid"] = inv.filename.str.extract(r"(pluskal_.*?_id)(?=_|\.)")[0]
    fn_base = inv.filename.str.rsplit("/", n=1).str[-1]
    inv["run_date"] = fn_base.str.extract(r"^(\d{8})_")[0]
    inv["variant"] = fn_base.str.extract(r"^\d{8}_(.*?)\d?pluskal_")[0].fillna("")
    inv["pref"] = inv.variant.eq("100AGC_60000Res_")
    inv["has_resubmit_suffix"] = fn_base.str.contains(r"_\d{10,}(?:_MSn_positive)?\.mzML$", regex=True)

    def pick_one(g):
        g = g.sort_values(["pref", "run_date", "has_resubmit_suffix", "filename"], ascending=[False, False, True, True])
        c = g.iloc[0]
        return pd.Series({"filename": c.filename, "n_candidates": len(g)})

    well_to_file = inv.groupby("usid").apply(pick_one)

    # zenodo zip members (already extracted for MCEDIV/TARGETMOL wells; check anchor wells against them too)
    zdf = pd.read_parquet(MD / "zenodo_zip_members.parquet") if (MD / "zenodo_zip_members.parquet").exists() else pd.DataFrame(columns=["usid", "member"])

    avail_massive, avail_zenodo, unavail = [], [], []
    for usid in required_wells:
        if usid in well_to_file.index:
            avail_massive.append({"unique_sample_id": usid, "filename": well_to_file.loc[usid, "filename"]})
        elif usid in set(zdf.usid):
            avail_zenodo.append({"unique_sample_id": usid, "member": zdf[zdf.usid == usid].iloc[0]["member"],
                                  "zip": zdf[zdf.usid == usid].iloc[0]["zip"]})
        else:
            unavail.append(usid)

    print(f"anchor wells available via MassIVE: {len(avail_massive)}", file=sys.stderr)
    print(f"anchor wells already extracted via local Zenodo zips: {len(avail_zenodo)}", file=sys.stderr)
    print(f"anchor wells UNAVAILABLE: {len(unavail)}", file=sys.stderr)
    if unavail:
        print(unavail[:20], file=sys.stderr)

    out = {"n_anchor_keys": len(anchor_keys), "n_required_wells": len(required_wells),
           "avail_massive": avail_massive, "avail_zenodo": avail_zenodo, "unavailable_wells": unavail,
           "keys_missing_conflict_free_well": sorted(missing)}
    (MD / "anchor_file_manifest.json").write_text(json.dumps(out, indent=1))
    pd.DataFrame(avail_massive).to_csv(MD / "anchor_massive_files_needed.csv", index=False)
    print(f"wrote {MD / 'anchor_file_manifest.json'}")


if __name__ == "__main__":
    main()
