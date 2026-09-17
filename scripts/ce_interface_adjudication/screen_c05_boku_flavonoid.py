"""C05 screen (CE interface adjudication, task S5): metadata-only overlap and feasibility screen of the BOKU/Masaryk
in-house flavonoid and prenylated flavonoid MS/MS library (Zenodo 16762591; Rypar et al., Metabolites 2025, 15, 616).

Input (metadata only): Table S1 "List of reference standards included in the in-house MS/MS library", extracted by
screen_c05_boku_flavonoid_fetch.py from Supplementary Material File S3.xlsx (PMC12471768 supplementary zip) into
artifacts/ce_interface_adjudication/screen/c05_boku_flavonoid/downloads/supp_S3_table_S1_raw.csv.
The library spectra file (in-house_MSMS_library.mgf) is never read. No model is run.

Exclusion sets and the MURU key/scaffold definition come from task P5
(artifacts/ce_interface_adjudication/exclusion/, scripts/ce_interface_adjudication/scaffold_key.py).

Outputs in artifacts/ce_interface_adjudication/screen/c05_boku_flavonoid/:
  c05_compounds_screen.csv   one row per Table S1 entry with key, scaffold group, flags
  c05_screen_summary.json    counts per criterion
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

A = W / "artifacts/ce_interface_adjudication"
E = A / "exclusion"
OUT = A / "screen/c05_boku_flavonoid"
T1 = OUT / "downloads/supp_S3_table_S1_raw.csv"
PROTON = 1.007276
DEV_MH_RANGE = (70.0, 1042.6)  # P5 note section 4 (msnlib_design.py:27 DEV_MH_RANGE, rounded as recorded there)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def keys(name: str) -> set[str]:
    return {l.strip() for l in (E / name).read_text().splitlines() if l.strip()}


def main() -> int:
    raw = pd.read_csv(T1, header=None, dtype=str)
    hdr_row = raw.index[raw.iloc[:, 0].eq("ID")][0]
    t = raw.iloc[hdr_row + 1:].copy()
    t.columns = [str(c).strip() for c in raw.iloc[hdr_row]]
    t = t[t["Name"].notna() | t["SMILES"].notna()].reset_index(drop=True)

    msg_all = keys("msg15_keys_all.txt") | keys("msg15_parent_keys_all.txt")
    msg_fold = {f: keys(f"msg15_keys_{f}.txt") | keys(f"msg15_parent_keys_{f}.txt") for f in ("train", "val", "test")}
    msg_sim = keys("msg15_simchallenge_keys_all.txt")
    msg_groups = keys("msg15_scaffold_groups_all.txt")
    reg = keys("muru_exposure_registry_keys.txt")
    reg_direct = keys("muru_exposure_registry_keys_direct_reason.txt")
    reg_groups = keys("muru_exposure_registry_scaffold_groups.txt")
    pop_files = sorted(E.glob("muru_exposure_registry_population_*_keys.txt"))
    pops = {p.name[len("muru_exposure_registry_population_"):-len("_keys.txt")]: keys(p.name) for p in pop_files}
    pop_union = set().union(*pops.values())
    s2 = keys("msnlib_study2_population_keys.txt")
    s2_groups = keys("msnlib_study2_population_scaffold_groups.txt")
    cmp_ = keys("comparator_common_population_keys.txt")
    cmp_groups = keys("comparator_common_population_scaffold_groups.txt")
    msn9 = keys("msnlib_9lib_keys.txt")
    msn4 = keys("msnlib_v1_0_4lib_keys.txt")
    mm2 = keys("multims2_reserved_validation_secondary_keys.txt")

    # MSG rows for overlapping keys (metadata only): folds, instrument, CE, adduct, and first-identifier region
    mem = pd.read_parquet(E / "msg_row_msnlib_membership.parquet",
                          columns=["identifier_num", "inchikey14", "parent_key14", "fold", "simulation_challenge",
                                   "adduct", "instrument_type", "collision_energy", "key_first_identifier_num"])

    rows = []
    for d0 in t.to_dict("records"):
        d = {k: (v if isinstance(v, str) else None) for k, v in d0.items()}
        smi = d.get("SMILES")
        key, grp = SK.key_and_group(smi)
        rec_ik = d.get("InChIKey")
        rec_block = SK.first_block(rec_ik) if isinstance(rec_ik, str) else None
        inchi_block = None
        if isinstance(d.get("InChI"), str) and d["InChI"].startswith("InChI="):
            ik = inchi.InchiToInchiKey(d["InChI"].strip())
            inchi_block = ik.split("-")[0] if ik else None
        m = SK.parent_mol(smi) if isinstance(smi, str) else None
        mono = Descriptors.ExactMolWt(m) if m is not None else None
        elements = sorted({a.GetSymbol() for a in m.GetAtoms()}) if m is not None else []
        charge = Chem.GetFormalCharge(m) if m is not None else None
        nfrag = len(Chem.GetMolFrags(Chem.MolFromSmiles(smi))) if isinstance(smi, str) and Chem.MolFromSmiles(smi) else None
        formula = rdMolDescriptors.CalcMolFormula(m) if m is not None else None
        cand = {k for k in (key, rec_block, inchi_block) if k}
        in_msg = bool(cand & msg_all)
        folds = sorted(f for f, s in msg_fold.items() if cand & s)
        out = {
            "table_id": d.get("ID"), "name": d.get("Name"), "provider": d.get("Provider"),
            "compound_class": d.get("compound_class"), "flavonoid_class": d.get("flavonoid_class"),
            "prenylation_type": d.get("Prenylation.type"), "cas": (d.get("CAS") or "").strip() or None,
            "smiles": smi, "recorded_inchikey": rec_ik, "key": key, "scaffold_group": grp,
            "recorded_inchikey_block": rec_block, "inchi_derived_block": inchi_block,
            "key_agrees_recorded": (rec_block == key) if rec_block else None,
            "key_agrees_inchi": (inchi_block == key) if inchi_block else None,
            "table_formula": d.get("formula"), "parent_formula": formula,
            "formula_agrees": (formula == d.get("formula").strip()) if isinstance(d.get("formula"), str) and formula else None,
            "parent_monoisotopic": mono, "mh_mz": (mono + PROTON) if mono else None,
            "mh_in_dev_range": (DEV_MH_RANGE[0] <= mono + PROTON <= DEV_MH_RANGE[1]) if mono else None,
            "elements": ";".join(elements), "parent_formal_charge": charge, "n_fragments_raw": nfrag,
            "in_msg15_any": in_msg, "msg15_folds": ";".join(folds), "in_msg15_simchallenge": bool(cand & msg_sim),
            "scaffold_in_msg15": grp in msg_groups if grp else None,
            "in_muru_registry": bool(cand & reg), "in_muru_registry_direct": bool(cand & reg_direct),
            "muru_exposed_populations": ";".join(sorted(n for n, s in pops.items() if cand & s)),
            "scaffold_in_muru_registry": grp in reg_groups if grp else None,
            "in_study2_pop": bool(cand & s2), "scaffold_in_study2_pop": grp in s2_groups if grp else None,
            "in_comparator_pop": bool(cand & cmp_), "scaffold_in_comparator_pop": grp in cmp_groups if grp else None,
            "in_msnlib_9lib": bool(cand & msn9), "in_msnlib_v1_0": bool(cand & msn4), "in_multims2_reserved": bool(cand & mm2),
        }
        sub = mem[mem.inchikey14.isin(cand) | mem.parent_key14.isin(cand)]
        out["msg15_n_rows"] = len(sub)
        out["msg15_n_rows_orbitrap_ce"] = int(((sub.instrument_type == "Orbitrap") & sub.collision_energy.notna()).sum())
        out["msg15_adducts"] = ";".join(sorted(sub.adduct.dropna().unique()))
        out["msg15_key_first_identifier_num"] = int(sub.key_first_identifier_num.min()) if len(sub) else None
        rows.append(out)
    df = pd.DataFrame(rows)
    df["is_prenylated"] = df.prenylation_type.fillna("none").str.strip().str.lower().ne("none")
    df["is_isolated_noncommercial"] = df.provider.fillna("").str.contains("isolat", case=False)

    # Exclusion ladders (compound level, then scaffold level)
    ok_key = df.key.notna()
    exA = ok_key & ~df.in_muru_registry & ~df.in_study2_pop & ~df.in_comparator_pop            # criteria 1-3 keys
    exB = exA & ~df.in_msg15_any                                                                # + criterion 4 keys
    exC = exB & ~df.scaffold_in_muru_registry.fillna(False) & ~df.scaffold_in_study2_pop.fillna(False) \
        & ~df.scaffold_in_comparator_pop.fillna(False)                                           # + MURU/PR7/comparator scaffold groups
    exD = exC & ~df.scaffold_in_msg15.fillna(False)                                              # + scaffold absent from MSG 1.5
    exE = exC & df.mh_in_dev_range.fillna(False) & df.parent_formal_charge.eq(0) & df.n_fragments_raw.eq(1)
    # Lenient variant (P5 note 2.1 scope caution): key exclusion against the exposed-population union (not the full
    # registry) plus PR #7 and comparator keys; scaffold exclusion limited to PR #7 and comparator groups because
    # per-population scaffold groups of the exposed populations are not available without their SMILES.
    exL1 = ok_key & df.muru_exposed_populations.eq("") & ~df.in_study2_pop & ~df.in_comparator_pop
    exL2 = exL1 & ~df.in_msg15_any
    exL3 = exL2 & ~df.scaffold_in_study2_pop.fillna(False) & ~df.scaffold_in_comparator_pop.fillna(False)
    df["pass_L2_lenient_keys_plus_msg15"] = exL2
    # Hidden-identity proxy: MSG 1.5 distinct keys sharing the molecular formula AND MURU scaffold group
    j = pd.read_parquet(A / "massspecgym15_identity_metadata_joined.parquet", columns=["identifier", "formula"])
    rk = pd.read_parquet(E / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    fk = j.merge(rk, on="identifier").dropna(subset=["parent_key"]).drop_duplicates(["parent_key"])
    by_f = fk.groupby("formula").parent_key.nunique()
    by_fg = fk.groupby(["formula", "scaffold_group"]).parent_key.nunique()
    df["msg15_keys_same_formula"] = [int(by_f.get(f, 0)) if isinstance(f, str) else 0 for f in df.parent_formula]
    df["msg15_keys_same_formula_and_scaffold"] = [int(by_fg.get((f, g), 0)) if isinstance(f, str) else 0
                                                  for f, g in zip(df.parent_formula, df.scaffold_group)]
    df["pass_A_keys_muru_pr7_cmp"] = exA
    df["pass_B_plus_msg15_key"] = exB
    df["pass_C_plus_scaffold_muru_pr7_cmp"] = exC
    df["pass_D_plus_scaffold_not_in_msg15"] = exD
    df["pass_E_C_plus_mh_range_neutral_single"] = exE

    def cnt(mask):
        s = df[mask]
        return {"compounds_rows": int(len(s)), "distinct_keys": int(s.key.nunique()),
                "scaffold_groups": int(s.scaffold_group.nunique()),
                "prenylated_keys": int(s[s.is_prenylated].key.nunique()),
                "acyclic_groups": int(s.scaffold_group.fillna("").str.startswith("__ACYCLIC__").sum())}

    grp_sizes = df[exC].groupby("scaffold_group").key.nunique().sort_values(ascending=False)
    summary = {
        "script": "scripts/ce_interface_adjudication/screen_c05_boku_flavonoid.py",
        "rdkit": rdBase.rdkitVersion, "frozen_rdkit": SK.FROZEN_RDKIT,
        "input_table_s1": {"path": str(T1.relative_to(W)), "sha256": sha(T1)},
        "exclusion_manifest_sha256": sha(E / "exclusion_manifest.json"),
        "n_table_rows": int(len(df)), "n_key_formed": int(ok_key.sum()), "n_distinct_keys": int(df.key.nunique()),
        "n_scaffold_groups_all": int(df.scaffold_group.nunique()),
        "n_duplicate_key_rows": int(df[ok_key].key.duplicated().sum()),
        "key_vs_recorded_inchikey": dict(Counter(map(str, df.key_agrees_recorded))),
        "key_vs_inchi": dict(Counter(map(str, df.key_agrees_inchi))),
        "formula_agrees": dict(Counter(map(str, df.formula_agrees))),
        "provider_counts": dict(Counter(df.provider.fillna("NA").str.strip())),
        "compound_class_counts": dict(Counter(df.compound_class.fillna("NA").str.strip())),
        "prenylated_distinct_keys": int(df[df.is_prenylated].key.nunique()),
        "elements": dict(Counter(e for s in df.elements for e in s.split(";") if e)),
        "mh_mz_min_max": [float(df.mh_mz.min()), float(df.mh_mz.max())],
        "mh_in_dev_range": dict(Counter(map(str, df.mh_in_dev_range))),
        "formal_charge_nonzero": int(df.parent_formal_charge.ne(0).sum()),
        "multi_fragment_raw": int(df.n_fragments_raw.gt(1).sum()),
        "overlap_distinct_keys": {
            "muru_exposure_registry_full": int(df[df.in_muru_registry].key.nunique()),
            "muru_exposure_registry_direct_reason": int(df[df.in_muru_registry_direct].key.nunique()),
            "muru_exposed_population_union": int(df[df.muru_exposed_populations.ne("")].key.nunique()),
            "muru_exposed_populations_hit": dict(Counter(p for s in df.drop_duplicates("key").muru_exposed_populations for p in s.split(";") if p)),
            "pr7_study2_population": int(df[df.in_study2_pop].key.nunique()),
            "comparator_common_population": int(df[df.in_comparator_pop].key.nunique()),
            "msg15_any_fold": int(df[df.in_msg15_any].key.nunique()),
            "msg15_by_fold": dict(Counter(f for s in df.drop_duplicates("key").msg15_folds for f in s.split(";") if f)),
            "msg15_simulation_challenge": int(df[df.in_msg15_simchallenge].key.nunique()),
            "msnlib_9lib": int(df[df.in_msnlib_9lib].key.nunique()),
            "msnlib_v1_0_4lib": int(df[df.in_msnlib_v1_0].key.nunique()),
            "multims2_reserved": int(df[df.in_multims2_reserved].key.nunique()),
            "prenylated_in_msg15_or_msnlib9": int(df[df.is_prenylated & (df.in_msg15_any | df.in_msnlib_9lib)].key.nunique()),
            "prenylated_not_in_msg15_nor_msnlib9": int(df[df.is_prenylated & ~(df.in_msg15_any | df.in_msnlib_9lib)].key.nunique()),
        },
        "overlap_scaffold_groups": {
            "in_muru_registry_groups": int(df[df.scaffold_in_muru_registry.fillna(False)].scaffold_group.nunique()),
            "in_study2_groups": int(df[df.scaffold_in_study2_pop.fillna(False)].scaffold_group.nunique()),
            "in_comparator_groups": int(df[df.scaffold_in_comparator_pop.fillna(False)].scaffold_group.nunique()),
            "in_msg15_groups": int(df[df.scaffold_in_msg15.fillna(False)].scaffold_group.nunique()),
        },
        "ladder": {
            "all_key_formed": cnt(ok_key),
            "A_keys_not_in_muru_registry_pr7_comparator": cnt(exA),
            "B_A_and_key_not_in_msg15": cnt(exB),
            "C_B_and_scaffold_not_in_muru_registry_pr7_comparator": cnt(exC),
            "D_C_and_scaffold_not_in_msg15": cnt(exD),
            "E_C_and_mh_in_dev_range_neutral_single_component": cnt(exE),
        },
        "lenient_L1_keys_not_in_exposed_population_union_pr7_comparator": cnt(exL1),
        "lenient_L2_L1_and_key_not_in_msg15": cnt(exL2),
        "lenient_L3_L2_and_scaffold_not_in_pr7_comparator": cnt(exL3),
        "L2_scaffold_group_sizes": {str(k): int(v) for k, v in df[exL2].groupby("scaffold_group").key.nunique().sort_values(ascending=False).items()},
        "B_hidden_identity_proxy": {
            "B_keys_with_msg15_same_formula": int((df[exB].msg15_keys_same_formula > 0).sum()),
            "B_keys_with_msg15_same_formula_and_scaffold": int((df[exB].msg15_keys_same_formula_and_scaffold > 0).sum()),
            "C_keys_with_msg15_same_formula": int((df[exC].msg15_keys_same_formula > 0).sum()),
            "C_keys_with_msg15_same_formula_and_scaffold": int((df[exC].msg15_keys_same_formula_and_scaffold > 0).sum()),
        },
        "C_scaffold_group_sizes": {str(k): int(v) for k, v in grp_sizes.items()},
        "B_scaffold_group_sizes": {str(k): int(v) for k, v in df[exB].groupby("scaffold_group").key.nunique().sort_values(ascending=False).items()},
        "msg15_overlap_first_identifier_nums": sorted(int(x) for x in df.msg15_key_first_identifier_num.dropna().unique()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "c05_compounds_screen.csv", index=False)
    (OUT / "c05_screen_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
