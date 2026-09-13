"""Protocol section 12: admission of a candidate against TA_RIDGE on the same cells."""
from __future__ import annotations

from muru.wur_v2 import runner as RU

PARTITIONS = ("PRIMARY", "PARTITION_S1", "PARTITION_S2", "STRICT", "GIANT", "RANDOM")


def evaluate(data, cand_model, ref_model, perm_models=()) -> dict:
    runs, comps = {}, {}
    for p in PARTITIONS:
        c = RU.run(cand_model, data, p)
        r = RU.run(ref_model, data, p)
        b0 = RU.b0(data, p)
        comps[p] = RU.compare(data, c.pred, r.pred, p, b0, boot=(p in ("PRIMARY", "STRICT")))
        comps[p]["cand_cfgs"] = c.cfgs
        runs[p] = (c, r)
    prim = comps["PRIMARY"]
    strata = RU.strata(data, runs["PRIMARY"][0].pred, runs["PRIMARY"][1].pred)
    perm = {}
    for pm in perm_models:
        pr = RU.run(pm, data, "PRIMARY")
        perm[pm.id] = RU.compare(data, pr.pred, runs["PRIMARY"][1].pred, "PRIMARY", None, boot=False)["P1_ratio"]
    crit = {
        "c1_primary_ratio_le_0.98": prim["P1_ratio"] <= 0.98,
        "c1_primary_ratio_ci_upper_lt_1": prim["bootstrap"]["P1_ratio_ci"][1] < 1.0,
        "c2_S1_ratio_lt_1": comps["PARTITION_S1"]["P1_ratio"] < 1.0,
        "c2_S2_ratio_lt_1": comps["PARTITION_S2"]["P1_ratio"] < 1.0,
        "c2_STRICT_ratio_lt_1": comps["STRICT"]["P1_ratio"] < 1.0,
        "c2_LCSB_stratum_lt_1": strata["LCSB_primary"]["P1_ratio"] < 1.0,
        "c2_WUR_stratum_lt_1": strata["WUR_primary"]["P1_ratio"] < 1.0,
        "c2_non_benzene_lt_1": strata["non_benzene"]["P1_ratio"] < 1.0,
        "c2_GIANT_ratio_le_1.02": comps["GIANT"]["P1_ratio"] <= 1.02,
        "c3_MRMSE_lower": prim["cand"]["MRMSE"] < prim["ref"]["MRMSE"],
        "c3_AF_not_worse_by_1pp": prim["cand"]["AF"] <= prim["ref"]["AF"] + 0.01,
    }
    if perm:
        crit["c4_permutation_loses"] = all(v > prim["P1_ratio"] and v >= 1.0 for v in perm.values())
    return {"criteria": crit, "admitted": all(crit.values()), "comparisons": comps, "strata_primary": strata,
            "permutation_P1_ratios": perm,
            "summary": {p: {"P1_cand": comps[p]["cand"]["P1"], "P1_ref": comps[p]["ref"]["P1"], "ratio": comps[p]["P1_ratio"],
                            "AF_cand": comps[p]["cand"]["AF"], "AF_ref": comps[p]["ref"]["AF"]} for p in PARTITIONS}}
