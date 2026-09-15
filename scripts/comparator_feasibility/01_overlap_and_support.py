"""Comparator feasibility audit (outcome-blind): training overlap and support of the frozen PR #7 population.

Reads only structure and identity: the frozen population (key, scaffold group, [M+H]+, wells, SMILES), the frozen
novelty bins, the frozen MURU model JSONs (for the protocol's support rule, which uses no measurement) and the MSnLib
compound-metadata parquet (identity columns only). It never opens artifacts/wur_v2_confirmation_v2/result/ or
access/, and it never reads a peak, intensity or mu value from any source.

Optional input: the MassSpecGym 1.5 identity table written by 02_fetch_massspecgym_identity.py. Without it every
MassSpecGym-dependent status is PENDING.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import candidate as CA            # noqa: E402
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import identity as ID             # noqa: E402

RDLogger.DisableLog("rdApp.*")
OUT = ROOT / "artifacts/comparator_feasibility"
A0 = (-5.95552603907965, 0.8618030610784555)       # frozen PR #7 deployment map (protocol V2 section 2)
NCE_RUNGS = (20.0, 60.0)

# MSnLib compound metadata, Zenodo record 21105617 (identical library MGF/JSON md5 to record 16984129).
MSNLIB_PARQUET_MD5 = "fe0fd40f75eebe8a09247a370da81c86"
# Libraries in Zenodo 11163381 (MSnLib v1.0, 2024-05-09): the MSnLib portion of MassSpecGym (dataset construction
# notebook 1) and the training library of FIORA OS v0.1.0 ("trained on the MSnLib v1.0").
MSNLIB_V1_LIBS = {"mcebio", "nihnp", "mcescaf", "otavapep"}
# Libraries in Zenodo 16984129 (2025-08-28): the "MSnLib v7" download URL of FIORA OS v1.0.0.
MSNLIB_16984129_LIBS = MSNLIB_V1_LIBS | {"enamdisc", "enammol", "mcedrug", "mcediv_50k", "tmhtsnp"}

# ms-pred (coleygroup/ms-pred @ ed8311f) documented limits, src/ms_pred/common/chem_utils.py
MSPRED_VALID_ELEMENTS = {"C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe", "Co", "As", "Na", "K"}
MSPRED_MAX_ATOM_CT = 160
MSG_MAX_PRECURSOR_MZ = 1000.0      # MassSpecGym construction notebook 4 ("Threshold precursor m/z")
FIORA_MW_MAX = 1000.0              # FIORA covariate normalisation (value/1000, clamped) and training filter
FIORA_CE_MAX = 100.0               # FIORA training filter 1 < CE <= 100 and covariate normalisation


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def mol_facts(smiles: str) -> dict:
    m = ID.parent_mol(smiles)
    if m is None:
        return {"parse_ok": False}
    mh = Chem.AddHs(m)
    elements = {a.GetSymbol() for a in mh.GetAtoms()}
    return {"parse_ok": True, "parent_exact_mass": Descriptors.ExactMolWt(m), "n_atoms_with_h": mh.GetNumAtoms(),
            "elements": ",".join(sorted(elements)), "mspred_elements_ok": elements <= MSPRED_VALID_ELEMENTS,
            "multi_component": "." in Chem.MolToSmiles(m)}


def summarize(df: pd.DataFrame, mask: pd.Series, label: str) -> dict:
    sub = df[mask]
    groups = sub.scaffold_group.value_counts()
    return {"label": label, "n_compounds": int(len(sub)), "n_scaffold_groups": int(len(groups)),
            "largest_group": int(groups.max()) if len(groups) else 0,
            "per_rung_cells": int(2 * len(sub)),
            "novelty_bin_counts": {k: int(v) for k, v in sub.novelty_bin.value_counts().sort_index().items()},
            "max_similarity_to_dev_quantiles": ({q: float(sub.max_similarity_to_dev.quantile(q))
                                                 for q in (0.1, 0.25, 0.5, 0.75, 0.9)} if len(sub) else {}),
            "plated_library_counts": {k: int(v) for k, v in
                                      sub.plated_libraries.str.split(";").explode().value_counts().items()}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msnlib-parquet", required=True, type=Path)
    ap.add_argument("--msg-identity", type=Path, default=OUT / "massspecgym15_identity.parquet")
    args = ap.parse_args()

    got = md5(args.msnlib_parquet)
    if got != MSNLIB_PARQUET_MD5:
        raise SystemExit(f"MSnLib parquet md5 {got} != Zenodo {MSNLIB_PARQUET_MD5}")

    pop = pd.read_csv(ROOT / DA.POPULATION_CSV)
    nov = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/novelty_bins_per_compound.csv")
    df = pop.merge(nov[["key", "max_similarity_to_dev", "novelty_bin"]], on="key", how="left", validate="1:1")
    assert len(df) == 1794 and df.novelty_bin.notna().all()

    # MURU support: the frozen protocol rule, structure-only (no measurement enters it).
    E = (np.array(NCE_RUNGS) - A0[0]) / A0[1]
    cand = json.loads((ROOT / DA.CANDIDATE_JSON).read_text())
    comp = json.loads((ROOT / DA.COMPARATOR_JSON).read_text())
    df["muru_supported"] = (CA.supported(cand, df.smiles, df.mh, E).all(1)
                            & CA.supported(comp, df.smiles, df.mh, E).all(1))

    # MSnLib identity: library of every plated well, and every library holding the same parent connectivity key.
    meta = pq.read_table(args.msnlib_parquet, columns=["library", "unique_sample_id", "split_inchikey"]).to_pandas()
    usid_lib = meta.drop_duplicates("unique_sample_id").set_index("unique_sample_id").library.to_dict()
    key_libs = {k: set(v) for k, v in meta.groupby("split_inchikey").library.unique().items()}
    plated, unmapped = [], 0
    for wells in df.wells:
        libs = set()
        for w in wells.split(";"):
            if w in usid_lib:
                libs.add(usid_lib[w])
            else:
                unmapped += 1
        plated.append(libs)
    df["plated_libraries"] = [";".join(sorted(s)) for s in plated]
    df["key_libraries"] = [";".join(sorted(key_libs.get(k, set()))) for k in df.key]
    all_libs = [p | key_libs.get(k, set()) for p, k in zip(plated, df.key)]
    df["in_msnlib_v1_0"] = [bool(s & MSNLIB_V1_LIBS) for s in all_libs]
    df["in_msnlib_16984129"] = [bool(s & MSNLIB_16984129_LIBS) for s in all_libs]

    facts = pd.DataFrame([mol_facts(s) for s in df.smiles])
    df = pd.concat([df, facts], axis=1)
    df["fiora_supported"] = df.parse_ok & (df.parent_exact_mass <= FIORA_MW_MAX)
    df["mspred_supported"] = (df.parse_ok & df.mspred_elements_ok & ~df.multi_component
                              & (df.n_atoms_with_h <= MSPRED_MAX_ATOM_CT) & (df.mh <= MSG_MAX_PRECURSOR_MZ))
    df["iceberg_ev_nce20"] = 20.0 * df.mh / 500.0
    df["iceberg_ev_nce60"] = 60.0 * df.mh / 500.0

    # MassSpecGym 1.5 overlap (identity only), if fetched.
    msg_available = args.msg_identity.exists()
    if msg_available:
        msg = pd.read_parquet(args.msg_identity)
        msg["key"] = msg.inchikey.str.split("-").str[0]
        folds = msg.groupby("key").fold.agg(lambda s: ";".join(sorted(set(s)))).to_dict()
        df["msg_folds"] = [folds.get(k, "") for k in df.key]
        df["in_msg_any"] = df.msg_folds != ""
        df["in_msg_train_or_val"] = df.msg_folds.str.contains("train|val")
    else:
        df["msg_folds"], df["in_msg_any"], df["in_msg_train_or_val"] = "PENDING", np.nan, np.nan

    base = df.muru_supported
    pops = {
        "pr7_frozen_population": pd.Series(True, index=df.index),
        "pr7_scored_muru_supported": base,
        "fiora_os_v1_0_0_default_clean": base & df.fiora_supported & ~df.in_msnlib_16984129,
        "fiora_os_v0_1_0_clean": base & df.fiora_supported & ~df.in_msnlib_v1_0,
        "mspred_supported_not_in_msnlib_v1_0": base & df.mspred_supported & ~df.in_msnlib_v1_0,
    }
    if msg_available:
        pops["iceberg21_msg_strict_clean_absent_from_msg"] = base & df.mspred_supported & ~df.in_msg_any
        pops["iceberg21_msg_foldaware_clean_not_train_val"] = base & df.mspred_supported & ~df.in_msg_train_or_val
        pops["glacier_msg_strict_clean_absent_from_msg"] = pops["iceberg21_msg_strict_clean_absent_from_msg"]
        pops["all_model_intersection_fiora_v0_1_0_iceberg_glacier_strict"] = (
            pops["fiora_os_v0_1_0_clean"] & pops["iceberg21_msg_strict_clean_absent_from_msg"])

    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["key", "scaffold_group", "mh", "muru_supported", "plated_libraries", "key_libraries", "in_msnlib_v1_0",
            "in_msnlib_16984129", "parse_ok", "parent_exact_mass", "n_atoms_with_h", "elements", "mspred_elements_ok",
            "multi_component", "fiora_supported", "mspred_supported", "iceberg_ev_nce20", "iceberg_ev_nce60",
            "msg_folds", "in_msg_any", "in_msg_train_or_val", "max_similarity_to_dev", "novelty_bin"]
    df[cols].sort_values("key").to_csv(OUT / "overlap_support_per_compound.csv", index=False)
    summary = {
        "inputs": {"population_csv": DA.POPULATION_CSV, "msnlib_parquet_md5": got, "wells_unmapped": unmapped,
                   "msg_identity_available": msg_available},
        "counts": {
            "n_population": int(len(df)), "n_muru_unsupported": int((~df.muru_supported).sum()),
            "n_in_msnlib_v1_0": int(df.in_msnlib_v1_0.sum()), "n_in_msnlib_16984129": int(df.in_msnlib_16984129.sum()),
            "n_fiora_unsupported": int((~df.fiora_supported).sum()),
            "n_mspred_unsupported": int((~df.mspred_supported).sum()),
            "n_mspred_bad_elements": int((df.parse_ok & ~df.mspred_elements_ok).sum()),
            "n_mh_above_1000": int((df.mh > MSG_MAX_PRECURSOR_MZ).sum()),
            "n_parent_mass_above_1000": int((df.parent_exact_mass > FIORA_MW_MAX).sum()),
            "iceberg_ev_range_nce20": [float(df.iceberg_ev_nce20.min()), float(df.iceberg_ev_nce20.max())],
            "iceberg_ev_range_nce60": [float(df.iceberg_ev_nce60.min()), float(df.iceberg_ev_nce60.max())],
        },
        "populations": {k: summarize(df, m.astype(bool), k) for k, m in pops.items()},
    }
    if msg_available:
        summary["counts"]["msg_fold_membership"] = {k: int(v) for k, v in df.msg_folds.replace("", "absent").value_counts().items()}
    (OUT / "overlap_support_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary["counts"], indent=1))
    for k, v in summary["populations"].items():
        print(f"{k}: n={v['n_compounds']} groups={v['n_scaffold_groups']} bins={v['novelty_bin_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
