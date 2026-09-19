#!/usr/bin/env python3
"""High-mass replication (C02 CyanoMetDB, MassBank 2026.03): metadata-only population construction.

Outcome-blind. No record file, no peak list, no spectrum, no prediction is opened. Inputs:
  screen/c02_cyanometdb/records.csv      frozen C02 header table (3,126 record files of tag 2026.03)
  screen/c02_cyanometdb/compounds.csv    frozen C02 identity table (Table S4: SMILES, level, purity, source)
  high_mass/metadata/qc_fragments_all_partitions.jsonl   header fragments (FRAGMENTATION_MODE, COLLISION_ENERGY)
  exclusion/*.txt                        frozen P5 exclusion key and scaffold-group sets
  ms-pred msg labels.tsv, MassSpecGym 1.5 SMILES, MURU dev / PR #7 / PR #8 / Design A populations (tautomer route)

Record rules H1..H7, compound rules H8 (identity exclusions) and H9 (energy grid), then H10 one compound per
scaffold group. Every record gets exactly one first failed rule or PASS in the ledger.

Usage:  python3 10_build_population.py [--explore]    (--explore prints grid/tier tables and writes nothing)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import scaffold_key as SK  # noqa: E402

_spec = importlib.util.spec_from_file_location("taut", HERE.parent / "screen_c01_eawag_eq_tautomer.py")
TAUT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TAUT)

ADJ = ROOT / "artifacts/ce_interface_adjudication"
C02 = ADJ / "screen/c02_cyanometdb"
EX = ADJ / "exclusion"
OUT = ADJ / "high_mass/population"
QC_JSONL = ADJ / "high_mass/metadata/qc_fragments_all_partitions.jsonl"
MSPRED_LABELS = Path("/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv")
MSG_META = ADJ / "massspecgym15_metadata_columns.parquet"
DEV_POP = ROOT / "artifacts/wur_v2/data/compounds.csv"
PR7_POP = ROOT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv"
PR8_POP = ROOT / "artifacts/comparator_benchmark/population/common_population.csv"
DESIGN_A_POP = ADJ / "design_a/population/design_a_compounds.csv"

# ---------------------------------------------------------------- frozen constants (inherited from Design A)
PROTON_MASS = 1.00727646688                      # design_a/10_build_population.py
MSPRED_VALID_ELEMENTS = frozenset(["C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe",
                                   "Co", "As", "Na", "K"])
MSPRED_MAX_ATOM_CT = 160
PRECURSOR_BOUND = 995.556                        # ICEBERG/GLACIER training-label max, Design A R7
MH_ERROR_TOL_DA = 0.01                           # Design A R6
ORBITRAP_TYPES = ("LC-ESI-QFT", "LC-ESI-ITFT")
CE_FIELD_RE = re.compile(r"^\s*(\d+(?:\.\d+)?) % \(nominal\)\s*$")
MODAL_LADDER = (15, 20, 25, 30, 40, 50, 60, 70, 80)
LEVEL_TIER = {"1": "T1_level1", "2a": "T2_level2a", "2b": "T3_level2b_3", "3": "T3_level2b_3"}
TIER_RANK = {"T1_level1": 1, "T2_level2a": 2, "T3_level2b_3": 3}
# Primary identity scope: the set of tiers admitted to the primary population (see the preregistration).
PRIMARY_TIERS = ("T1_level1", "T2_level2a", "T3_level2b_3")
# Grid rule: largest grid G (subset of MODAL_LADDER, >= 2 levels) whose scaffold-group count within the primary
# tiers is at least GRID_RETENTION x the maximum over all grids; ties -> more groups, then lexicographically smallest.
GRID_RETENTION = 0.95


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def readset(name: str) -> set[str]:
    return {x.strip() for x in (EX / name).read_text().splitlines() if x.strip()}


def qc_fields() -> pd.DataFrame:
    """Per record file: FRAGMENTATION_MODE and COLLISION_ENERGY from the complete QC harvest, plus the blob seen."""
    rows = {}
    for line in QC_JSONL.open():
        j = json.loads(line)
        for it in j["items"]:
            fn = it["path"].split("/")[-1]
            d = rows.setdefault(fn, {"file": fn, "qc_blob_sha": set()})
            d["qc_blob_sha"].add(it["blob_sha"])
            for frag in it["fragments"]:
                for ln in frag.split("\n"):
                    m = re.match(r"^AC\$MASS_SPECTROMETRY: (FRAGMENTATION_MODE|COLLISION_ENERGY) (.*)$", ln)
                    if m:
                        d.setdefault(m.group(1), set()).add(m.group(2).strip())
    out = []
    for fn, d in rows.items():
        out.append({"file": fn,
                    "qc_blob_sha": "|".join(sorted(d["qc_blob_sha"])),
                    "qc_frag_mode": "|".join(sorted(d.get("FRAGMENTATION_MODE", set()))) or None,
                    "qc_ce_str": "|".join(sorted(d.get("COLLISION_ENERGY", set()))) or None})
    return pd.DataFrame(out)


def element_ok(smiles: str) -> tuple[bool, int]:
    m = SK.parent_mol(smiles) if isinstance(smiles, str) else None
    if m is None:
        return False, -1
    els = {a.GetSymbol() for a in Chem.AddHs(m).GetAtoms()}
    return els <= MSPRED_VALID_ELEMENTS, m.GetNumHeavyAtoms()


def tautomer_hits(cmp: pd.DataFrame) -> pd.DataFrame:
    """Formula-restricted parent/tautomer/skeleton key matches against the five comparison populations."""
    enum = rdMolStandardize.TautomerEnumerator()
    k = [TAUT.keys_for(s, enum) for s in cmp["smiles"]]
    cmp = cmp.assign(taut_key=[x[1] for x in k], skel_key=[x[2] for x in k], formula_calc=[x[3] for x in k])
    formulas = set(cmp["formula_calc"].dropna())
    sources = {
        "msg15": pd.read_parquet(MSG_META, columns=["smiles"])["smiles"],
        "muru_dev_pop": pd.read_csv(DEV_POP, usecols=["smiles"])["smiles"],
        "pr7": pd.read_csv(PR7_POP, usecols=["smiles"])["smiles"],
        "pr8_comparator": pd.read_csv(PR8_POP, usecols=["model_smiles"])["model_smiles"],
        "design_a": pd.read_csv(DESIGN_A_POP, usecols=["representative_smiles"])["representative_smiles"],
    }
    for name, ser in sources.items():
        tk, sk = set(), set()
        for s in ser.dropna().drop_duplicates():
            pm = SK.parent_mol(s)
            if pm is None or rdMolDescriptors.CalcMolFormula(pm) not in formulas:
                continue
            _p, t, kk, f = TAUT.keys_for(s, enum)
            if t:
                tk.add((f, t))
            if kk:
                sk.add((f, kk))
        cmp[f"{name}_taut_hit"] = [(f, t) in tk for f, t in zip(cmp["formula_calc"], cmp["taut_key"])]
        cmp[f"{name}_skel_hit"] = [(f, t) in sk for f, t in zip(cmp["formula_calc"], cmp["skel_key"])]
    return cmp


def compound_table() -> pd.DataFrame:
    C = pd.read_csv(C02 / "compounds.csv")
    C["level"] = C["level"].astype(str)
    kg = [SK.key_and_group(s) for s in C["smiles"]]
    C["parent_key"] = [x[0] for x in kg]
    C["scaffold_group"] = [x[1] for x in kg]
    pm = [SK.parent_mol(s) if isinstance(s, str) else None for s in C["smiles"]]
    C["theoretical_mh"] = [float(Descriptors.ExactMolWt(m) + PROTON_MASS) if m is not None else float("nan") for m in pm]
    eo = [element_ok(s) for s in C["smiles"]]
    C["elements_ok"] = [x[0] for x in eo]
    C["heavy_atoms_parent"] = [x[1] for x in eo]
    C["tier"] = C["level"].map(LEVEL_TIER).fillna("T3_level2b_3")
    return C


def build(explore: bool = False):
    R = pd.read_csv(C02 / "records.csv")
    Q = qc_fields()
    R = R.merge(Q, on="file", how="left")
    C = compound_table()

    # unit -> compounds; a unit that is an isomer group maps to several structures
    unit_members = C.groupby("unit_id")["parent_key"].agg(lambda s: sorted(set(s.dropna())))
    unit_is_group = C.groupby("unit_id")["unit_is_group"].any()

    failed = pd.Series([None] * len(R), index=R.index, dtype=object)
    reason = pd.Series([None] * len(R), index=R.index, dtype=object)
    steps = [{"rule": "H0", "description": "C02 record files in MassBank tag 2026.03 (EAWAG-EC, EAWAG-ED, MLU-ED)",
              "records": len(R)}]

    def mark(bad, rule, why):
        hit = failed.isna() & bad.fillna(True)
        failed.loc[hit] = rule
        reason.loc[hit] = why if isinstance(why, str) else why[hit]
        steps.append({"rule": rule, "description": RULES[rule], "records": int(failed.isna().sum())})

    R["nce_field"] = R["qc_ce_str"].map(lambda s: float(CE_FIELD_RE.match(s).group(1))
                                        if isinstance(s, str) and "|" not in s and CE_FIELD_RE.match(s) else None)
    R["nce_title"] = R["title_ce"].map(lambda s: float(s.rstrip("%")) if isinstance(s, str) and re.fullmatch(r"\d+(\.\d+)?%", s) else None)

    mark(~((R["precursor_type"] == "[M+H]+") & (R["title_adduct"] == "[M+H]+")), "H1", "not [M+H]+ (positive mode)")
    mark(~((R["ms_type"] == "MS2") & R["instrument_type"].isin(ORBITRAP_TYPES)), "H2", "not MS2 on an Orbitrap instrument type")
    mark(~(R["qc_frag_mode"] == "HCD"), "H3", "FRAGMENTATION_MODE not explicitly HCD in the header")
    mark(~(R["nce_field"].notna() & (R["nce_field"] == R["nce_title"])), "H4",
         "COLLISION_ENERGY not a single 'N % (nominal)' value equal to the title CE")
    mark(~((R["blob_sha_tag"] == R["blob_sha_dev"]) & (R["qc_blob_sha"] == R["blob_sha_tag"])
           & R["fragment_matches_tag_blob"].astype(bool)), "H5",
         "header evidence not from the pinned 2026.03 blob (file changed on dev after the tag)")
    single = R["unit"].map(lambda u: (u in unit_members.index) and (not bool(unit_is_group.get(u, True)))
                           and len(unit_members.get(u, [])) == 1)
    mark(~single, "H6", "record not mapped to exactly one Table S4 structure (isomer group or unlisted)")
    R["parent_key"] = R["unit"].map(lambda u: unit_members[u][0] if u in unit_members.index and len(unit_members[u]) == 1 else None)
    cc = C.dropna(subset=["parent_key"]).drop_duplicates("parent_key").set_index("parent_key")
    R["theoretical_mh"] = R["parent_key"].map(cc["theoretical_mh"])
    R["mh_error_da"] = R["precursor_mz"] - R["theoretical_mh"]
    ik_ok = R.apply(lambda r: isinstance(r["inchikey_record"], str) and r["parent_key"] is not None
                    and r["inchikey_record"].split("-")[0] == r["parent_key"], axis=1)
    mark(~((R["mh_error_da"].abs() <= MH_ERROR_TOL_DA) & ik_ok), "H7",
         "structural integrity: |precursor - theoretical [M+H]+| > 0.01 Da or record InChIKey block != parent key")
    sup = R["parent_key"].map(lambda k: bool(k in cc.index and cc.loc[k, "elements_ok"]
                                              and cc.loc[k, "heavy_atoms_parent"] <= MSPRED_MAX_ATOM_CT
                                              and cc.loc[k, "theoretical_mh"] <= PRECURSOR_BOUND))
    mark(~sup, "H8", "model support: element set, heavy atoms <= 160, theoretical [M+H]+ <= 995.556")

    # ---------------- H9 identity exclusions (compound level, sub-rules in fixed order)
    live = sorted(R.loc[failed.isna(), "parent_key"].unique())
    cl = cc.loc[live, ["smiles", "scaffold_group", "inchikey_s4"]].reset_index()
    cl = tautomer_hits(cl)
    rec_ik14 = R.groupby("parent_key")["inchikey_record"].agg(lambda s: {x.split("-")[0] for x in s.dropna()})
    labels_ik = set(pd.read_csv(MSPRED_LABELS, sep="\t", usecols=["inchikey"])["inchikey"].astype(str).str[:14])
    da = pd.read_csv(DESIGN_A_POP)
    sets = {
        "msg15_recorded": readset("msg15_keys_all.txt"),
        "msg15_parent": readset("msg15_parent_keys_all.txt"),
        "mspred_labels": labels_ik,
        "muru_registry": readset("muru_exposure_registry_keys.txt"),
        "muru_exposed_union": readset("muru_exposed_union_keys.txt"),
        "muru_dev_pop": set(pd.read_csv(DEV_POP, usecols=["parent_key"])["parent_key"]),
        "pr7": set(pd.read_csv(PR7_POP, usecols=["key"])["key"]),
        "pr8_comparator": readset("comparator_common_population_keys.txt"),
        "design_a": set(da["compound_id"]),
    }
    sg_sets = {
        "sg_muru_registry": readset("muru_exposure_registry_scaffold_groups.txt"),
        "sg_muru_dev_pop": set(pd.read_csv(DEV_POP, usecols=["scaffold_group"])["scaffold_group"]),
        "sg_pr7": readset("msnlib_study2_population_scaffold_groups.txt"),
        "sg_pr8_comparator": readset("comparator_common_population_scaffold_groups.txt"),
        "sg_design_a": set(da["scaffold_group"]),
    }
    sub = []
    for name, s in sets.items():
        sub.append((f"key:{name}", cl["parent_key"].map(lambda k: k in s or bool(rec_ik14.get(k, set()) & s))))
    for name in ("msg15", "muru_dev_pop", "pr7", "pr8_comparator", "design_a"):
        sub.append((f"tautomer:{name}", cl[f"{name}_taut_hit"]))
    for name, s in sg_sets.items():
        sub.append((f"scaffold:{name}", cl["scaffold_group"].isin(s)))
    removed, h9_detail = {}, []
    for rid, fires in sub:
        new = [k for k, f in zip(cl["parent_key"], fires) if f and k not in removed]
        h9_detail.append({"sub_rule": rid, "flagged": int(fires.sum()), "newly_removed": len(new)})
        for k in new:
            removed[k] = rid
    skel_any = cl[[c for c in cl.columns if c.endswith("_skel_hit")]].any(axis=1)
    h9_detail.append({"sub_rule": "skeleton (REPORTED, NOT APPLIED, as Design A)",
                      "flagged": int(skel_any.sum()),
                      "newly_removed_if_applied": int(sum(1 for k, f in zip(cl["parent_key"], skel_any) if f and k not in removed))})
    rm = R["parent_key"].map(removed)
    mark(rm.notna(), "H9", "identity exclusion: " + rm.fillna(""))
    return R, C, cc, failed, reason, steps, h9_detail, cl


RULES = {
    "H1": "precursor type [M+H]+ (positive mode) in field and title",
    "H2": "MS2 on an Orbitrap instrument type (LC-ESI-QFT or LC-ESI-ITFT)",
    "H3": "FRAGMENTATION_MODE HCD stated explicitly in the header",
    "H4": "single explicit 'N % (nominal)' COLLISION_ENERGY equal to the title CE",
    "H5": "header evidence taken from the pinned MassBank 2026.03 blob",
    "H6": "record maps to exactly one Table S4 structure",
    "H7": "structural integrity (precursor within 0.01 Da of theoretical [M+H]+, InChIKey block agrees)",
    "H8": "model support (ms-pred elements, heavy atoms <= 160, [M+H]+ <= 995.556)",
    "H9": "identity exclusions (MassSpecGym 1.5, ms-pred labels, MURU registry/exposed/dev, PR #7, PR #8, Design A)",
    "H10": "energy-grid completeness",
}


def grid_table(R, failed, cc):
    alive = R[failed.isna()]
    have = alive.groupby("parent_key")["nce_field"].agg(lambda s: set(int(x) for x in s))
    comp = pd.DataFrame({"nces": have})
    comp["scaffold_group"] = cc.loc[comp.index, "scaffold_group"]
    comp["tier"] = cc.loc[comp.index, "tier"]
    comp["mh"] = cc.loc[comp.index, "theoretical_mh"]
    return comp


def explore():
    R, C, cc, failed, reason, steps, h9, cl = build()
    for s in steps:
        print(s)
    for d in h9:
        print(d)
    comp = grid_table(R, failed, cc)
    print("compounds after H9", len(comp), "groups", comp.scaffold_group.nunique())
    print(comp.tier.value_counts())
    print(collections.Counter(tuple(sorted(x)) for x in comp.nces).most_common(12))
    res = []
    for r in range(2, len(MODAL_LADDER) + 1):
        for g in itertools.combinations(MODAL_LADDER, r):
            ok = comp[comp.nces.map(lambda s: set(g) <= s)]
            res.append((r, g, len(ok), ok.scaffold_group.nunique(),
                        ok[ok.tier == "T1_level1"].scaffold_group.nunique(),
                        ok[ok.tier.isin(["T1_level1", "T2_level2a"])].scaffold_group.nunique()))
    df = pd.DataFrame(res, columns=["k", "grid", "compounds", "groups", "groups_T1", "groups_T1T2"])
    print(df.sort_values(["k", "groups"], ascending=[True, False]).groupby("k").head(3).to_string())


def choose_grid(comp: pd.DataFrame) -> tuple[tuple[int, ...], list[dict]]:
    table = []
    for r in range(2, len(MODAL_LADDER) + 1):
        for g in itertools.combinations(MODAL_LADDER, r):
            ok = comp[comp["nces"].map(lambda s: set(g) <= s)]
            table.append({"grid": list(g), "k": r, "compounds": int(len(ok)), "groups": int(ok["scaffold_group"].nunique())})
    nmax = max(t["groups"] for t in table)
    admissible = [t for t in table if t["groups"] >= GRID_RETENTION * nmax]
    best = sorted(admissible, key=lambda t: (-t["k"], -t["groups"], t["grid"]))[0]
    return tuple(best["grid"]), table


def write():
    R, C, cc, failed, reason, steps, h9, cl = build()
    comp = grid_table(R, failed, cc)
    comp = comp[comp["tier"].isin(PRIMARY_TIERS)]
    grid, grid_table_all = choose_grid(comp)
    complete = set(comp.index[comp["nces"].map(lambda s: set(grid) <= s)])
    alive = failed.isna()
    tier_ok = R["parent_key"].map(lambda k: k in cc.index and cc.loc[k, "tier"] in PRIMARY_TIERS)
    failed.loc[alive & ~tier_ok] = "H10"
    reason.loc[alive & ~tier_ok] = "identity tier outside the primary tiers"
    steps.append({"rule": "H10", "description": "identity tier in PRIMARY_TIERS", "records": int(failed.isna().sum())})
    alive = failed.isna()
    bad = alive & ~(R["parent_key"].isin(complete) & R["nce_field"].isin(grid))
    failed.loc[bad] = "H11"
    reason.loc[bad] = R.loc[bad].apply(lambda r: "NCE outside the frozen grid" if r["parent_key"] in complete
                                       else "compound incomplete on the frozen grid", axis=1)
    steps.append({"rule": "H11", "description": f"frozen NCE grid {list(grid)}: record NCE in grid, compound complete",
                  "records": int(failed.isna().sum())})
    # H12 one compound per scaffold group: best tier, then lexicographically smallest parent key
    cand = cc.loc[sorted(complete)].reset_index().assign(tr=lambda d: d["tier"].map(TIER_RANK))
    chosen = cand.sort_values(["tr", "parent_key"]).groupby("scaffold_group").head(1)
    alive = failed.isna()
    bad = alive & ~R["parent_key"].isin(set(chosen["parent_key"]))
    failed.loc[bad] = "H12"
    reason.loc[bad] = "not the frozen representative of its scaffold group"
    steps.append({"rule": "H12", "description": "one compound per scaffold group (best tier, then smallest key)",
                  "records": int(failed.isna().sum())})
    failed = failed.fillna("PASS")
    reason = reason.where(failed != "PASS", "eligible")

    pop = R[failed == "PASS"].copy()
    arm = pop.groupby("parent_key")["series"].agg(lambda s: "+".join(sorted(set(x.replace("MSBNK-", "") for x in s))))
    comps = chosen.set_index("parent_key")
    out_c = pd.DataFrame({
        "compound_id": comps.index, "name": comps["name"].values, "scaffold_group": comps["scaffold_group"].values,
        "representative_smiles": comps["smiles"].values, "theoretical_mh": comps["theoretical_mh"].values,
        "level": comps["level"].values, "purity": comps["purity"].fillna("NA").values, "tier": comps["tier"].values,
        "contributor_arm": arm.reindex(comps.index).values,
        "n_records": pop.groupby("parent_key").size().reindex(comps.index).values,
    }).sort_values("compound_id")
    out_r = pd.DataFrame({
        "record_id": pop["accession"], "compound_id": pop["parent_key"], "scaffold_group": pop["parent_key"].map(comps["scaffold_group"]),
        "nce": pop["nce_field"].astype(int), "theoretical_mh": pop["theoretical_mh"], "source_file": pop["file"],
        "blob_sha": pop["blob_sha_tag"], "series": pop["series"], "instrument": pop["instrument"],
        "scan_mode": pop["scan_mode"], "deposited_precursor_mz": pop["precursor_mz"],
    }).sort_values("record_id")
    ledger = pd.DataFrame({"record_id": R["accession"], "file": R["file"], "series": R["series"],
                           "parent_key": R["parent_key"], "first_failed_rule": failed, "reason": reason}).sort_values("record_id")
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {"high_mass_compounds.csv": out_c, "high_mass_records.csv": out_r, "high_mass_exclusion_ledger.csv": ledger}
    for n, df in paths.items():
        df.to_csv(OUT / n, index=False, lineterminator="\n")
    cl.to_csv(OUT / "high_mass_identity_checks.csv", index=False, lineterminator="\n")
    counts = {
        "rdkit": rdBase.rdkitVersion, "steps": steps, "h9_identity_subrules": h9,
        "frozen": {"primary_tiers": list(PRIMARY_TIERS), "grid_rule_retention": GRID_RETENTION, "nce_grid": list(grid),
                   "precursor_bound": PRECURSOR_BOUND, "mh_error_tol_da": MH_ERROR_TOL_DA,
                   "representative_rule": "best tier (1 < 2a < 2b/3), then lexicographically smallest parent key"},
        "grid_candidates_top": sorted(grid_table_all, key=lambda t: (-t["k"], -t["groups"]))[:12],
        "final": {"compounds": int(len(out_c)), "scaffold_groups": int(out_c["scaffold_group"].nunique()),
                  "records": int(len(out_r)),
                  "mh_min": float(out_c["theoretical_mh"].min()), "mh_median": float(out_c["theoretical_mh"].median()),
                  "mh_max": float(out_c["theoretical_mh"].max()),
                  "n_mh_above_500": int((out_c["theoretical_mh"] > 500).sum()),
                  "n_mh_450_550": int(out_c["theoretical_mh"].between(450, 550).sum()),
                  "tier_counts": out_c["tier"].value_counts().to_dict(),
                  "level_by_purity": pd.crosstab(out_c["level"], out_c["purity"]).to_dict(),
                  "contributor_arms": out_c["contributor_arm"].value_counts().to_dict(),
                  "records_by_series_instrument": out_r.groupby(["series", "instrument"]).size().rename("n").reset_index().to_dict("records"),
                  "records_per_compound_cell": {str(k): int(v) for k, v in out_r.groupby(["compound_id", "nce"]).size().value_counts().items()}},
    }
    (OUT / "high_mass_counts.json").write_text(json.dumps(counts, indent=1, default=str) + "\n")
    inputs = [C02 / "records.csv", C02 / "compounds.csv", QC_JSONL, MSPRED_LABELS, MSG_META, DEV_POP, PR7_POP, PR8_POP, DESIGN_A_POP]
    inputs += sorted(EX.glob("*.txt"))
    rel = lambda p: str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)  # noqa: E731
    man = {"generator": {rel(Path(__file__)): sha256_file(Path(__file__))},
           "inputs_read": {rel(p): sha256_file(p) for p in inputs},
           "outputs_written": {rel(OUT / n): sha256_file(OUT / n) for n in list(paths) + ["high_mass_identity_checks.csv", "high_mass_counts.json"]}}
    (OUT / "high_mass_manifest_sha256.json").write_text(json.dumps(man, indent=1) + "\n")
    print(json.dumps(counts["final"], indent=1, default=str))
    for s_ in steps:
        print(s_)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--explore", action="store_true")
    a = ap.parse_args()
    if a.explore:
        explore()
    else:
        write()
