"""Experiment 1 ledger entries: estimand audit (A) and v2 baseline refit (B)."""
import json
from pathlib import Path
import numpy as np
from muru.wur_v2 import runner as RU, models as MO, ledger as LG
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/wur_v2/exp01"
A = json.loads((OUT / "part_a_stage3_estimands.json").read_text())
pop = json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"]
F = RU.folds()
d = RU.load_data(False)
res_b = {}
for part in ("PRIMARY", "PARTITION_S1", "PARTITION_S2", "STRICT", "GIANT", "RANDOM"):
    b0 = RU.b0(d, part)
    ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, part)
    v1 = RU.run(MO.RidgeV1Selection(), d, part)
    b1 = RU.run(MO.MassIsotonic(), d, part)
    res_b[part] = {"TA_RIDGE": RU.compare(d, ta.pred, b1.pred, part, b0, boot=(part == "PRIMARY")),
                   "TA_RIDGE_V1SEL_vs_TA_RIDGE": RU.compare(d, v1.pred, ta.pred, part, b0, boot=(part == "PRIMARY")),
                   "B0": RU.compare(d, b0, b0, part, b0, boot=False)["cand"], "alphas_TA": ta.cfgs}
(OUT / "part_b_v2_baselines.json").write_text(json.dumps(res_b, indent=1, default=float) + "\n")
p = res_b["PRIMARY"]
c = A["comparisons"]
LG.append({"experiment_id": "V2-EXP01A-ESTIMAND-AUDIT-STAGE3", "generation": "v2-G0", "parent_model": "V1B_RIDGE_TIERA (frozen)",
  "hypothesis": "The v1 Stage 3 ordering is robust to replacing the mean per-compound RMSE bootstrap with a cluster bootstrap that recomputes P1; P1 and mean compound RMSE are distinct estimands.",
  "population_sha256": "6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52 (WUR-SEALED, now exposed)", "partition": "Stage 3 train DEV2B+HOLD -> SEALED",
  "representation": "v1 arms as frozen", "endpoint": "aligned mu, rungs 30-90", "hyperparameters_and_space": "as frozen", "tuning_process": "none (reproduction)",
  "results": {"reproduction": A["reproduction"], "estimands": {k: {x: v[x] for x in ("P1", "MRMSE", "MED", "Q90", "Q95", "CVaR95", "AF", "AF_max", "S4")} for k, v in A["estimands"].items()}},
  "uncertainty": {k: {"P1_ratio_ci_v2scaffold": v["corrected_cluster_v2_scaffold"]["P1_ratio_ci"], "P1_diff_ci_v2scaffold": v["corrected_cluster_v2_scaffold"]["P1_diff_ci"],
                      "MRMSE_diff_ci_v2scaffold": v["corrected_cluster_v2_scaffold"]["MRMSE_diff_ci"], "historical_ci95_compound_mean_rmse": v["historical_recorded"]["ci95_compound"]} for k, v in c.items()},
  "tail_metrics": {k: {"AF": v["AF"], "AF_max": v["AF_max"], "S4": v["S4"], "CVaR95": v["CVaR95"]} for k, v in A["estimands"].items()},
  "interpretation": "Reproduction is exact (per-compound RMSE within 5e-16). Corrected P1 intervals keep every historical conclusion: V1B beats S2A (P1 ratio 0.849, 95% [0.807, 0.891]) and mass-only (0.882 [0.826, 0.939]); B1 vs S2A ratio interval includes 1; V1C vs V1B includes 1; V1A vs V1B lower bound touches 1.00. Cluster intervals are wider than the historical compound-level ones (e.g. V1B-B1 P1 diff [-0.025, -0.008] vs historical mean-RMSE [-0.021, -0.010]). P1 (0.1251) exceeds mean compound RMSE (0.1080) because P1 weights large-error compounds more. V1B AF 9.4% vs S2A 16.8%, B1 14.4%, B0 21.3%.",
  "decision": "diagnostic", "reason": "estimand correction; historical interpretation unchanged", "informed_later_decisions": "all v2 comparisons use metrics.cluster_bootstrap"})
LG.append({"experiment_id": "V2-EXP01B-BASELINES-V2-POPULATION", "generation": "v2-G0", "parent_model": "V1B_RIDGE_TIERA family",
  "hypothesis": "v1-family references refit under v2 nesting on the 1,325-compound population give the fair baseline; v1's alpha selection approximation (outer labels, log g loss) does not change it materially.",
  "population_sha256": pop, "partition": {k: F["partitions"][k]["assignment_sha256"] for k in res_b},
  "representation": "TIER_A (12, protocol.SCALE); B1 precursor m/z; B0", "endpoint": "aligned mu, rungs 30-90",
  "hyperparameters_and_space": "TA alpha in {0.01,0.1,1,10,100}", "tuning_process": "nested inner grouped 4-fold, inner collapse refit, trajectory SSE; V1SEL outer labels weighted log g SSE",
  "results": {k: {"TA_RIDGE": v["TA_RIDGE"]["cand"], "B1": v["TA_RIDGE"]["ref"], "B0": v["B0"], "V1SEL_P1": v["TA_RIDGE_V1SEL_vs_TA_RIDGE"]["cand"]["P1"], "alphas": v["alphas_TA"]} for k, v in res_b.items()},
  "uncertainty": {"TA_vs_B1_PRIMARY": p["TA_RIDGE"]["bootstrap"], "V1SEL_vs_TA_PRIMARY": p["TA_RIDGE_V1SEL_vs_TA_RIDGE"]["bootstrap"]},
  "tail_metrics": {k: {"TA_AF": v["TA_RIDGE"]["cand"]["AF"], "TA_AF_max": v["TA_RIDGE"]["cand"]["AF_max"], "TA_S4": v["TA_RIDGE"]["cand"].get("S4")} for k, v in res_b.items()},
  "interpretation": "TA_RIDGE PRIMARY P1 %.4f (MRMSE %.4f, AF %.3f); B1 %.4f; B0 %.4f. STRICT %.4f, RANDOM %.4f, GIANT(benzene) %.4f: no random-vs-scaffold gap for a 12-descriptor ridge. v1 selection gives P1 within 0.001 on every partition: the nesting approximation does not matter for this model." % (
      p["TA_RIDGE"]["cand"]["P1"], p["TA_RIDGE"]["cand"]["MRMSE"], p["TA_RIDGE"]["cand"]["AF"], p["TA_RIDGE"]["ref"]["P1"], p["B0"]["P1"],
      res_b["STRICT"]["TA_RIDGE"]["cand"]["P1"], res_b["RANDOM"]["TA_RIDGE"]["cand"]["P1"], res_b["GIANT"]["TA_RIDGE"]["cand"]["P1"]),
  "decision": "accepted", "reason": "TA_RIDGE is the fair v2 baseline for admission", "informed_later_decisions": "reference arm for Experiments 6-10"})
print(json.dumps({k: round(v["TA_RIDGE"]["cand"]["P1"], 4) for k, v in res_b.items()}), p["TA_RIDGE"]["bootstrap"]["P1_ratio_ci"], p["TA_RIDGE_V1SEL_vs_TA_RIDGE"]["bootstrap"]["P1_ratio_ci"])
