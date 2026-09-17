"""TASK V: independent exclusion re-run for the PARTIAL_OR_SUPPORTING_ONLY verdicts.

For every candidate that stored per-compound identity, recompute the MURU parent key and scaffold
group from the stored SMILES (where available) and re-run every membership test from the raw key
lists, then recompute the post-exclusion counts the verdict asserts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

WT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = WT / "artifacts/ce_interface_adjudication"
EXC = ART / "exclusion"
SCR = ART / "screen"
sys.path.insert(0, str(WT / "scripts/ce_interface_adjudication"))
from scaffold_key import key_and_group  # noqa: E402


def S(n):
    return {l.strip() for l in (EXC / n).read_text().splitlines() if l.strip()}


MSG = S("msg15_keys_all.txt") | S("msg15_parent_keys_all.txt")
MSG_REC = S("msg15_keys_all.txt")
MSG_SIM = S("msg15_simchallenge_keys_all.txt")
FOLD = {f: S(f"msg15_keys_{f}.txt") for f in ("train", "val", "test")}
REG = S("muru_exposure_registry_keys.txt")
DEV = S("muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys.txt")
POPU = set().union(*[S(p.name) for p in EXC.glob("muru_exposure_registry_population_*_keys.txt")])
PR7 = S("msnlib_study2_population_keys.txt")
CMP = S("comparator_common_population_keys.txt")
SG_MSG = S("msg15_scaffold_groups_all.txt")
SG_REG = S("muru_exposure_registry_scaffold_groups.txt")
SG_PR7 = S("msnlib_study2_population_scaffold_groups.txt")
SG_CMP = S("comparator_common_population_scaffold_groups.txt")
SG_DEV = set(pd.read_csv(WT / "artifacts/wur_v2/data/compounds.csv", usecols=["scaffold_group"])["scaffold_group"].dropna())
MSN9 = S("msnlib_9lib_keys.txt")

OUT = {}


def annotate(df, smiles_col=None, key_col=None, sg_col=None):
    """Recompute key/sg from SMILES when we have SMILES; otherwise trust the stored key/sg."""
    if smiles_col is not None:
        uniq = sorted(set(df[smiles_col].dropna().astype(str)))
        kg = {s: key_and_group(s) for s in uniq}
        df["v_key"] = df[smiles_col].map(lambda s: kg.get(str(s), (None, None))[0] if pd.notna(s) else None)
        df["v_sg"] = df[smiles_col].map(lambda s: kg.get(str(s), (None, None))[1] if pd.notna(s) else None)
    else:
        df["v_key"] = df[key_col]
        df["v_sg"] = df[sg_col]
    df["m_msg"] = df["v_key"].isin(MSG)
    df["m_msg_sim"] = df["v_key"].isin(MSG_SIM)
    df["m_msg_train"] = df["v_key"].isin(FOLD["train"])
    df["m_msg_val"] = df["v_key"].isin(FOLD["val"])
    df["m_msg_test"] = df["v_key"].isin(FOLD["test"])
    df["m_reg"] = df["v_key"].isin(REG)
    df["m_dev"] = df["v_key"].isin(DEV)
    df["m_popu"] = df["v_key"].isin(POPU)
    df["m_pr7"] = df["v_key"].isin(PR7)
    df["m_cmp"] = df["v_key"].isin(CMP)
    df["m_msn9"] = df["v_key"].isin(MSN9)
    df["g_msg"] = df["v_sg"].isin(SG_MSG)
    df["g_reg"] = df["v_sg"].isin(SG_REG)
    df["g_dev"] = df["v_sg"].isin(SG_DEV)
    df["g_pr7"] = df["v_sg"].isin(SG_PR7)
    df["g_cmp"] = df["v_sg"].isin(SG_CMP)
    return df


def u(df, mask, kcol="v_key", gcol="v_sg"):
    s = df[mask]
    return int(s[kcol].nunique()), int(s[gcol].nunique())


# ------------------------------------------------------------------ C02 CyanoMetDB
d = pd.read_csv(SCR / "c02_cyanometdb/compounds.csv")
d = annotate(d, smiles_col="smiles")
c02 = {"rows": int(len(d)),
       "key_agrees_stored": int((d["v_key"] == d["muru_key"]).sum()),
       "sg_agrees_stored": int((d["v_sg"] == d["scaffold_group"]).sum())}
mh = d[d["has_mh"].fillna(False) & (d["n_mh_distinct_nce"] >= 3)] if "has_mh" in d else d
c02["MH_ge3nce_rows"] = int(len(mh))
c02["MH_ge3nce_keys"] = int(mh["v_key"].nunique())
for lab, m in (("in_msg15", mh["m_msg"]), ("in_msg15_sim", mh["m_msg_sim"]), ("in_registry", mh["m_reg"]),
               ("in_devpop", mh["m_dev"]), ("in_exposed_pops", mh["m_popu"]),
               ("in_pr7", mh["m_pr7"]), ("in_comparator", mh["m_cmp"]),
               ("sg_in_registry", mh["g_reg"]), ("sg_in_pr7", mh["g_pr7"]), ("sg_in_comparator", mh["g_cmp"])):
    c02[lab] = int(m.sum())
keep = ~(mh["m_msg"] | mh["m_reg"] | mh["m_pr7"] | mh["m_cmp"])
c02["P2_key_clean_rows"], _ = int(keep.sum()), None
c02["P2_key_clean_keys"] = int(mh.loc[keep, "v_key"].nunique())
keep3 = keep & ~(mh["g_reg"] | mh["g_pr7"] | mh["g_cmp"])
c02["P3_keys"], c02["P3_groups"] = u(mh, keep3)
c02["P3_rows"] = int(keep3.sum())
OUT["C02"] = c02

# ------------------------------------------------------------------ C05 BOKU flavonoids
d = pd.read_csv(SCR / "c05_boku_flavonoid/c05_compounds_screen.csv")
d = annotate(d, smiles_col="smiles")
c05 = {"rows": int(len(d)), "key_agrees_stored": int((d["v_key"] == d["key"]).sum()),
       "sg_agrees_stored": int((d["v_sg"] == d["scaffold_group"]).sum()),
       "distinct_keys": int(d["v_key"].nunique())}
dd = d.drop_duplicates("v_key")
for lab, m in (("in_msg15", dd["m_msg"]), ("in_msg15_sim", dd["m_msg_sim"]), ("in_registry", dd["m_reg"]),
               ("in_exposed_pops", dd["m_popu"]), ("in_pr7", dd["m_pr7"]), ("in_comparator", dd["m_cmp"]),
               ("sg_in_registry", dd["g_reg"]), ("sg_in_pr7", dd["g_pr7"]), ("sg_in_comparator", dd["g_cmp"])):
    c05[lab] = int(m.sum())
c05["distinct_groups"] = int(dd["v_sg"].nunique())
strict = ~(dd["m_reg"] | dd["m_pr7"] | dd["m_cmp"]) & ~dd["m_msg"] & ~(dd["g_reg"] | dd["g_pr7"] | dd["g_cmp"])
c05["strict_keys"], c05["strict_groups"] = u(dd, strict)
c05["strict_plus_msg_scaffold"] = int((strict & ~dd["g_msg"]).sum())
lenient = ~(dd["m_popu"] | dd["m_pr7"] | dd["m_cmp"]) & ~dd["m_msg"]
c05["lenient_keys"], c05["lenient_groups"] = u(dd, lenient)
OUT["C05"] = c05

# ------------------------------------------------------------------ C11 ExpoLib
d = pd.read_csv(SCR / "c11_expolib/c11_compounds_screen.csv")
d = annotate(d, smiles_col="smiles")
c11 = {"rows": int(len(d)), "key_agrees_stored": int((d["v_key"] == d["parent_key"]).sum()),
       "sg_agrees_stored": int((d["v_sg"] == d["scaffold_group"]).sum())}
mh = d[d["has_mh"].fillna(False)].drop_duplicates("v_key")
c11["MH_keys"] = int(len(mh))
c11["MH_groups"] = int(mh["v_sg"].nunique())
for lab, m in (("in_msg15", mh["m_msg"]), ("in_msg15_sim", mh["m_msg_sim"]), ("in_registry", mh["m_reg"]),
               ("in_devpop", mh["m_dev"]), ("in_exposed_pops", mh["m_popu"]),
               ("in_pr7", mh["m_pr7"]), ("in_comparator", mh["m_cmp"]),
               ("sg_in_registry", mh["g_reg"]), ("sg_in_msg", mh["g_msg"]),
               ("sg_in_pr7", mh["g_pr7"]), ("sg_in_comparator", mh["g_cmp"])):
    c11[lab] = int(m.sum())
keyclean = ~(mh["m_reg"] | mh["m_pr7"] | mh["m_cmp"] | mh["m_msg"])
c11["key_level_survivors"] = int(keyclean.sum())
c11["key_level_groups"] = int(mh.loc[keyclean, "v_sg"].nunique())
c11["after_registry_only"] = int((~mh["m_reg"]).sum())
sgclean = keyclean & ~(mh["g_reg"] | mh["g_pr7"] | mh["g_cmp"] | mh["g_msg"])
c11["key_and_scaffold_survivors"] = int(sgclean.sum())
c11["survivor_names"] = sorted(mh.loc[keyclean, "compound"].astype(str))
OUT["C11"] = c11

# ------------------------------------------------------------------ C06 PharmMet (keys only)
d = pd.read_csv(SCR / "c06_pharmmet/c06_deposited_union.csv")
d = annotate(d, key_col="key", sg_col="scaffold_group")
dd = d.drop_duplicates("v_key")
c06 = {"rows": int(len(d)), "distinct_keys": int(dd["v_key"].nunique()),
       "distinct_groups": int(dd["v_sg"].nunique())}
for lab, m in (("in_msg15", dd["m_msg"]), ("in_msg15_sim", dd["m_msg_sim"]), ("in_msg_train", dd["m_msg_train"]),
               ("in_registry", dd["m_reg"]), ("in_devpop", dd["m_dev"]), ("in_exposed_pops", dd["m_popu"]),
               ("in_pr7", dd["m_pr7"]), ("in_comparator", dd["m_cmp"])):
    c06[lab] = int(m.sum())
after_msg = ~dd["m_msg"]
c06["after_msg_keys"], c06["after_msg_groups"] = u(dd, after_msg)
after_muru = after_msg & ~(dd["m_popu"] | dd["m_pr7"] | dd["m_cmp"]) & ~(dd["g_dev"] | dd["g_pr7"] | dd["g_cmp"])
c06["after_msg_and_muru_exposed_keys"], c06["after_msg_and_muru_exposed_groups"] = u(dd, after_muru)
after_muru_pop_only = after_msg & ~(dd["m_popu"] | dd["m_pr7"] | dd["m_cmp"])
c06["after_msg_and_muru_keys_only"] = int(after_muru_pop_only.sum())
c06["conservative_full_registry"] = int((after_msg & ~(dd["m_reg"] | dd["m_pr7"] | dd["m_cmp"])
                                         & ~(dd["g_reg"] | dd["g_pr7"] | dd["g_cmp"])).sum())
OUT["C06"] = c06

# ------------------------------------------------------------------ C10 BAFG (keys only)
d = pd.read_csv(SCR / "c10_bafg/c10_compounds_screen.csv")
d = annotate(d, key_col="key", sg_col="scaffold_group")
c10 = {"positive_keys": int(len(d)), "groups": int(d["v_sg"].nunique())}
for lab, m in (("in_msg15", d["m_msg"]), ("in_msg15_sim", d["m_msg_sim"]), ("in_msg_train", d["m_msg_train"]),
               ("in_registry", d["m_reg"]), ("in_exposed_pops", d["m_popu"]), ("in_devpop", d["m_dev"]),
               ("in_pr7", d["m_pr7"]), ("in_comparator", d["m_cmp"]),
               ("sg_in_registry", d["g_reg"]), ("sg_in_msg", d["g_msg"])):
    c10[lab] = int(m.sum())
neutral = d["charge_neutral_parent"].fillna(False).astype(bool)
c10["charge_neutral"] = int(neutral.sum())
s1 = neutral & ~d["m_msg"]
c10["minus_msg_keys"], c10["minus_msg_groups"] = u(d, s1)
s2 = s1 & ~(d["m_reg"] | d["m_popu"])
c10["minus_muru_keys"], c10["minus_muru_groups"] = u(d, s2)
s3 = s2 & ~(d["g_reg"] | d["g_pr7"] | d["g_cmp"])
c10["minus_sg_keys"], c10["minus_sg_groups"] = u(d, s3)
s4 = s3 & (d["n_distinct_ce"] >= 2) & d["in_range_70_1042_6"].fillna(False).astype(bool)
c10["final_keys"], c10["final_groups"] = u(d, s4)
s5 = s4 & ~d["g_msg"]
c10["final_strict_keys"], c10["final_strict_groups"] = u(d, s5)
OUT["C10"] = c10

# ------------------------------------------------------------------ C03 MassBank in-training HCD
d = pd.read_parquet(SCR / "c03_massbank_hcd/compounds_design_rows.parquet")
kc = [c for c in d.columns if c in ("parent_key", "key", "muru_key")]
gc = [c for c in d.columns if "scaffold" in c]
c03 = {"rows": int(len(d)), "key_col": kc, "sg_col": gc, "cols": list(d.columns)[:40]}
if kc:
    d = annotate(d, key_col=kc[0], sg_col=(gc[0] if gc else kc[0]))
    dd = d.drop_duplicates("v_key")
    c03["distinct_keys"] = int(dd["v_key"].nunique())
    for lab, m in (("in_msg15", dd["m_msg"]), ("in_msg15_sim", dd["m_msg_sim"]), ("in_registry", dd["m_reg"]),
                   ("in_devpop", dd["m_dev"]), ("in_pr7", dd["m_pr7"]), ("in_comparator", dd["m_cmp"])):
        c03[lab] = int(m.sum())
    surv = ~(dd["m_msg"] | dd["m_reg"] | dd["m_pr7"] | dd["m_cmp"])
    c03["survivors_keys"], c03["survivors_groups"] = u(dd, surv)
    surv2 = surv & ~(dd["g_reg"] | dd["g_pr7"] | dd["g_cmp"] | dd["g_msg"])
    c03["survivors_after_sg"] = int(surv2.sum())
OUT["C03"] = c03

print(json.dumps(OUT, indent=1, default=str))
Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-stability-study-6537d5/c50bb7b0-c2aa-4e0b-bd11-bc34c1ea3cbc/scratchpad/vscreen/v_partials.json").write_text(
    json.dumps(OUT, indent=1, default=str))
