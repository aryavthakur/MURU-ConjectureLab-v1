import json
from pathlib import Path
from muru.wur_v2 import ledger as LG, runner as RU
ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "artifacts/wur_v2/exp10/exp10_results.json").read_text())
p, s = r["PRIMARY"], r["STRICT"]
LG.append({"experiment_id": "V2-EXP10-TRUST", "generation": "v2-G2", "parent_model": "TA_MORGAN_JOINT (point model), TA_RIDGE (for disagreement)",
 "hypothesis": "Pre-measurement novelty, leverage, representation disagreement, profile sensitivity or a small learned combination identifies compounds with absolute failure (RMSE > 0.20) better than random rejection and better than distance alone.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": {q: RU.folds()["partitions"][q]["assignment_sha256"] for q in ("PRIMARY", "STRICT")},
 "representation": "signals: 1-max MinMax Morgan similarity, Tier A ridge leverage, Mahalanobis, |logg_TA - logg_joint|, profile sensitivity, domain flag",
 "endpoint": "per-compound trajectory RMSE and AF of the point model", "hyperparameters_and_space": "ridge alpha 1 on log(RMSE+0.01); logistic C=1",
 "tuning_process": "trust targets from inner cross-fitting inside each outer training set; signals for training rows computed against their inner training sets",
 "results": {q: {"af_prevalence": r[q]["af_prevalence"], "full": r[q]["full_population"],
                 "rankers": {k: {"spearman": v["spearman_with_rmse"], "pr_auc": v["af_pr_auc"], "AF_at_80": v["selective"]["0.8"]["AF"], "AF_at_90": v["selective"]["0.9"]["AF"], "P1_at_80": v["selective"]["0.8"]["P1"]} for k, v in r[q]["rankers"].items()},
                 "threshold_q80": r[q]["threshold_q80"], "calibration": r[q]["calibration_learned_p_af"]} for q in ("PRIMARY", "STRICT")},
 "uncertainty": {q: r[q]["learned_vs_distance_bootstrap"] for q in ("PRIMARY", "STRICT")},
 "tail_metrics": {"source_strata_80": p["source_strata_80"]},
 "interpretation": "Trust fails. On PRIMARY the joint model's AF prevalence is 6.3 percent; the best AF PR-AUC is 0.084 (domain flag then distance) against a random 0.063; the learned model's Spearman with RMSE is 0.14 and its retained AF at 80 percent coverage is 6.0 percent (random 6.3, distance-only 5.8); relative reduction versus distance -5 percent, 95 percent interval [-24, +10]. The AF logistic has Brier 0.0597 against 0.0594 for a constant and calibration slope 0.20. STRICT is no better. Profile sensitivity is the strongest single signal (Spearman 0.17) but does not lower retained AF. No trust claim is supportable; Route B is closed.",
 "decision": "rejected", "reason": "no signal beats random or distance-only rejection at 70-90 percent coverage", "informed_later_decisions": "no trust output in the v2 candidate; adduct domain restriction documented only"})
