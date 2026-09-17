"""TASK V (v_screen): independent re-derivation of the SCREEN lens overlap/exclusion verdicts.

Re-runs, from the stored per-record / per-compound identity columns and NOTHING that the screen
phase computed, the InChIKey14 exclusion against
  - MassSpecGym 1.5, all folds, both key routes (recorded block + MURU parent key)
  - the MURU exposure registry (and its exposed-population union, and the v2 development population)
  - the PR #7 (MSnLib confirmation study 2) frozen population
  - the comparator benchmark common population
plus the scaffold-group variants, and recomputes every post-exclusion count the verdicts assert.

Reads ONLY identity material. No model, no prediction, no result file.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

WT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = WT / "artifacts/ce_interface_adjudication"
EXC = ART / "exclusion"
SCR = ART / "screen"
sys.path.insert(0, str(WT / "scripts/ce_interface_adjudication"))
from scaffold_key import key_and_group, first_block  # noqa: E402

OUT = {}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def load_set(name: str) -> set[str]:
    p = EXC / name
    vals = [l.strip() for l in p.read_text().splitlines() if l.strip()]
    return set(vals)


# ---------------------------------------------------------------- exclusion sets
print("== exclusion set integrity ==")
SETS = {}
for nm in ["msg15_keys_all", "msg15_keys_train", "msg15_keys_val", "msg15_keys_test",
           "msg15_parent_keys_all", "msg15_simchallenge_keys_all", "msg15_scaffold_groups_all",
           "muru_exposure_registry_keys", "muru_exposure_registry_scaffold_groups",
           "muru_exposed_union_keys",
           "muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys",
           "msnlib_study2_population_keys", "msnlib_study2_population_scaffold_groups",
           "comparator_common_population_keys", "comparator_common_population_scaffold_groups",
           "msnlib_9lib_keys", "msnlib_v1_0_4lib_keys"]:
    s = load_set(nm + ".txt")
    SETS[nm] = s
    print(f"  {nm}: n={len(s)}")

MSG_ALL = SETS["msg15_keys_all"] | SETS["msg15_parent_keys_all"]
MSG_FOLD = {f: SETS[f"msg15_keys_{f}"] for f in ("train", "val", "test")}
REG = SETS["muru_exposure_registry_keys"]
EXPU = SETS["muru_exposed_union_keys"]
DEVP = SETS["muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys"]
PR7 = SETS["msnlib_study2_population_keys"]
CMP = SETS["comparator_common_population_keys"]
SG_MSG = SETS["msg15_scaffold_groups_all"]
SG_REG = SETS["muru_exposure_registry_scaffold_groups"]
SG_PR7 = SETS["msnlib_study2_population_scaffold_groups"]
SG_CMP = SETS["comparator_common_population_scaffold_groups"]

OUT["exclusion_sets"] = {
    "sizes": {k: len(v) for k, v in SETS.items()},
    "msg15_union_both_routes": len(MSG_ALL),
    "fold_disjoint": (len(MSG_FOLD["train"] & MSG_FOLD["val"]) == 0
                      and len(MSG_FOLD["train"] & MSG_FOLD["test"]) == 0
                      and len(MSG_FOLD["val"] & MSG_FOLD["test"]) == 0),
    "folds_cover_all": len(MSG_FOLD["train"] | MSG_FOLD["val"] | MSG_FOLD["test"]) == len(SETS["msg15_keys_all"]),
    "all_keys_14char": {k: all(len(x) == 14 for x in v) for k, v in SETS.items() if k.endswith("keys")
                        or "keys" in k},
    "comparator_subset_of_pr7": CMP <= PR7,
    "pr7_disjoint_from_registry": len(PR7 & REG) == 0,
    "sha256": {nm: sha256_file(EXC / (nm + ".txt")) for nm in
               ["msg15_keys_all", "muru_exposure_registry_keys", "msnlib_study2_population_keys",
                "comparator_common_population_keys"]},
}
print("  comparator subset of PR7:", CMP <= PR7, "| PR7 disjoint from registry:", len(PR7 & REG) == 0)


def memberships(key: str, sg: str | None) -> dict:
    return {
        "in_msg15": key in MSG_ALL,
        "in_msg15_recorded_route": key in SETS["msg15_keys_all"],
        "in_msg15_parent_route": key in SETS["msg15_parent_keys_all"],
        "in_msg15_sim": key in SETS["msg15_simchallenge_keys_all"],
        "msg_folds": ",".join(f for f in ("train", "val", "test") if key in MSG_FOLD[f]),
        "in_registry": key in REG,
        "in_exposed_union": key in EXPU,
        "in_devpop": key in DEVP,
        "in_pr7": key in PR7,
        "in_comparator": key in CMP,
        "in_msnlib9": key in SETS["msnlib_9lib_keys"],
        "sg_in_msg15": (sg in SG_MSG) if sg else False,
        "sg_in_registry": (sg in SG_REG) if sg else False,
        "sg_in_pr7": (sg in SG_PR7) if sg else False,
        "sg_in_comparator": (sg in SG_CMP) if sg else False,
    }


# ---------------------------------------------------------------- C01
print("\n== C01 Eawag EQ ==")
rec = pd.read_csv(SCR / "c01_eawag_eq/c01_record_metadata.csv.gz")
c01 = {"records_total": int(len(rec))}

# re-derive identity from the stored SMILES, independent of the screen's own columns
uniq_smi = sorted(set(rec["smiles"].dropna().astype(str)))
kg = {s: key_and_group(s) for s in uniq_smi}
rec["v_key"] = rec["smiles"].map(lambda s: kg.get(s, (None, None))[0] if isinstance(s, str) else None)
rec["v_sg"] = rec["smiles"].map(lambda s: kg.get(s, (None, None))[1] if isinstance(s, str) else None)
rec["v_recorded14"] = rec["inchikey"].map(first_block)

c01["key_agrees_with_screen"] = int((rec["v_key"] == rec["parent_key"]).sum())
c01["sg_agrees_with_screen"] = int((rec["v_sg"] == rec["scaffold_group"]).sum())
c01["key_null"] = int(rec["v_key"].isna().sum())
c01["recorded14_equals_parent_key"] = int((rec["v_recorded14"] == rec["v_key"]).sum())

# record-level filters, re-applied from the raw metadata columns
mh = rec[(rec["precursor_type"] == "[M+H]+") & (rec["ion_mode"] == "POSITIVE") & (rec["ms_type"] == "MS2")].copy()
c01["records_MH_pos_MS2"] = int(len(mh))
c01["records_by_precursor_type"] = rec["precursor_type"].value_counts(dropna=False).to_dict()
c01["records_MH_frag_mode"] = mh["frag_mode"].value_counts(dropna=False).to_dict()
c01["records_MH_instrument_type"] = mh["instrument_type"].value_counts(dropna=False).to_dict()
c01["records_MH_instrument"] = mh["instrument"].value_counts(dropna=False).to_dict()
c01["records_MH_resolution"] = mh["resolution"].value_counts(dropna=False).to_dict()
c01["ce_string_forms_all"] = rec["ce_form"].value_counts(dropna=False).to_dict()
c01["ce_raw_examples"] = sorted(set(rec["ce"].dropna().astype(str)))[:12]
c01["ce_raw_nonstandard"] = sorted(set(rec.loc[rec["ce_form"] != "N % (nominal)", "ce"].dropna().astype(str)))[:20]
c01["records_MH_license"] = mh["license"].value_counts(dropna=False).to_dict()
c01["records_MH_confidence"] = mh["confidence"].value_counts(dropna=False).to_dict()
c01["first_release_counts"] = rec["first_ref"].value_counts(dropna=False).to_dict()

# compound-level rebuild, grouping by re-derived key
g = mh.dropna(subset=["v_key"]).groupby("v_key")
comp = pd.DataFrame({
    "n_records": g.size(),
    "n_nce": g["nce"].nunique(),
    "nce_ladder": g["nce"].apply(lambda s: ",".join(str(int(x)) if float(x).is_integer() else str(x)
                                                    for x in sorted(set(s.dropna())))),
    "sg": g["v_sg"].apply(lambda s: sorted(set(s.dropna()))[0] if s.notna().any() else None),
    "n_sg": g["v_sg"].nunique(),
    "smiles": g["smiles"].first(),
    "name": g["name"].first(),
    "mh_calc": g["mh_calc"].first(),
    "releases": g["first_ref"].apply(lambda s: ",".join(sorted(set(s.dropna().astype(str))))),
    "uchem_ids": g["uchem_id_filename"].apply(lambda s: ",".join(str(x) for x in sorted(set(s.dropna())))),
    "instruments": g["instrument"].apply(lambda s: "|".join(sorted(set(s.dropna().astype(str))))),
    "confidence": g["confidence"].apply(lambda s: "|".join(sorted(set(s.dropna().astype(str))))),
}).reset_index().rename(columns={"v_key": "key"})
c01["compounds_MH"] = int(len(comp))
comp["ge3"] = comp["n_nce"] >= 3
c01["compounds_MH_ge3_nce"] = int(comp["ge3"].sum())

m = pd.DataFrame([memberships(r.key, r.sg) for r in comp.itertuples(index=False)])
comp = pd.concat([comp.reset_index(drop=True), m], axis=1)
cand = comp[comp["ge3"]].copy()
c01["cand_in_msg15"] = int(cand["in_msg15"].sum())
c01["cand_in_msg15_by_fold"] = cand["msg_folds"].value_counts().to_dict()
c01["cand_in_registry"] = int(cand["in_registry"].sum())
c01["cand_in_exposed_union"] = int(cand["in_exposed_union"].sum())
c01["cand_in_devpop"] = int(cand["in_devpop"].sum())
c01["cand_in_pr7"] = int(cand["in_pr7"].sum())
c01["cand_in_comparator"] = int(cand["in_comparator"].sum())
c01["cand_sg_in_devpop_or_pr7_or_cmp"] = int((cand["sg_in_registry"] | cand["sg_in_pr7"] | cand["sg_in_comparator"]).sum())

# tiers exactly as the verdict defines them
tau = pd.read_csv(SCR / "c01_eawag_eq/c01_tautomer_recheck.csv")
c01["tautomer_csv_cols"] = list(tau.columns)
excl_by_tautomer = set()
for cn in tau.columns:
    if cn.startswith("taut_hit") or cn.startswith("skel_hit") or "hit" in cn.lower():
        pass
c01["tautomer_recheck_json"] = json.loads((SCR / "c01_eawag_eq/c01_tautomer_recheck.json").read_text())

devpop_sg = set(pd.read_csv(WT / "artifacts/wur_v2/data/compounds.csv", usecols=["scaffold_group"])["scaffold_group"].dropna())
cand["sg_in_devpop_file"] = cand["sg"].isin(devpop_sg)

key_clean = ~(cand["in_msg15"] | cand["in_registry"] | cand["in_pr7"] | cand["in_comparator"])
c01["tier_key_clean_before_tautomer"] = int(key_clean.sum())
prim = key_clean & ~(cand["sg_in_devpop_file"] | cand["sg_in_pr7"] | cand["sg_in_comparator"])
cons = key_clean & ~(cand["sg_in_registry"] | cand["sg_in_pr7"] | cand["sg_in_comparator"])
strict = cons & ~cand["sg_in_msg15"]
c01["tier_primary_before_tautomer"] = int(prim.sum())
c01["tier_conservative_before_tautomer"] = int(cons.sum())
c01["tier_strict_before_tautomer"] = int(strict.sum())
c01["tier_primary_groups"] = int(cand.loc[prim, "sg"].nunique())
c01["tier_conservative_groups"] = int(cand.loc[cons, "sg"].nunique())
c01["tier_strict_groups"] = int(cand.loc[strict, "sg"].nunique())
c01["tier_key_clean_groups"] = int(cand.loc[key_clean, "sg"].nunique())
c01["tier_key_clean_records"] = int(cand.loc[key_clean, "n_records"].sum())
c01["tier_primary_records"] = int(cand.loc[prim, "n_records"].sum())
c01["tier_conservative_records"] = int(cand.loc[cons, "n_records"].sum())

# tagged-release-only variant
tagged = cand["releases"].map(lambda s: "dev" not in str(s))
c01["tagged_key_clean"] = int((key_clean & tagged).sum())
c01["tagged_primary"] = int((prim & tagged).sum())
c01["tagged_conservative"] = int((cons & tagged).sum())
c01["tagged_strict"] = int((strict & tagged).sum())

# NCE rung availability on the surviving tiers
def rung(sub, val):
    return int(sub["nce_ladder"].map(lambda s: str(val) in str(s).split(",")).sum())
for tname, mask in (("key_clean", key_clean), ("primary", prim), ("conservative", cons)):
    sub = cand[mask]
    c01[f"nce_rungs_{tname}"] = {
        "n": int(len(sub)), "has_nce20": rung(sub, 20), "has_nce60": rung(sub, 60),
        "has_nce30": rung(sub, 30), "has_nce15": rung(sub, 15),
        "median_rungs_in_15_90": float(sub["nce_ladder"].map(
            lambda s: sum(1 for x in str(s).split(",") if x and 15 <= float(x) <= 90)).median()) if len(sub) else None,
        "ladder_modes": sub["nce_ladder"].value_counts().head(5).to_dict(),
    }
c01["primary_mh_mz_ge500"] = int((cand.loc[prim, "mh_calc"] >= 500).sum())
c01["conservative_mh_mz_ge500"] = int((cand.loc[cons, "mh_calc"] >= 500).sum())
c01["primary_mh_mz_range"] = [float(cand.loc[prim, "mh_calc"].min()), float(cand.loc[prim, "mh_calc"].max())]
c01["primary_confidence"] = cand.loc[prim, "confidence"].value_counts().to_dict()
c01["primary_instruments_multi"] = int((cand.loc[prim, "instruments"].str.contains(r"\|")).sum())
c01["compounds_with_multiple_scaffold_groups_in_records"] = int((comp["n_sg"] > 1).sum())

cand.to_csv("/tmp/v_c01_cand.csv", index=False)
OUT["C01"] = c01
print(json.dumps({k: v for k, v in c01.items() if not isinstance(v, dict)}, indent=1))

Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-stability-study-6537d5/c50bb7b0-c2aa-4e0b-bd11-bc34c1ea3cbc/scratchpad/vscreen/v_part1.json").write_text(
    json.dumps(OUT, indent=1, default=str))
print("\nwrote v_part1.json")
