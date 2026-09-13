import json
from pathlib import Path
from muru.wur_v2 import ledger as LG, runner as RU
ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "artifacts/wur_v2/exp02/exp02_results.json").read_text())
pop = json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"]
r1, r2, idf, vb = r["R1_LCSB_inter_preparation"], r["R2_cross_instrument"], r["identifiability"], r["variance_budget"]
LG.append({"experiment_id": "V2-EXP02-REPEATABILITY-IDENTIFIABILITY", "generation": "v2-G0", "parent_model": "TA_RIDGE (PRIMARY OOF), frozen collapse",
 "hypothesis": "A material fraction of the log g error beyond Tier A is reproducible between independent acquisitions (so potentially learnable), and scales are mostly identifiable on the 30-90 rungs.",
 "population_sha256": pop, "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"],
 "representation": "none (scale fits against out-of-fold profiles)", "endpoint": "aligned mu 30-90; raw-branch mu for LCSB duplicates",
 "hyperparameters_and_space": "frozen log g grid; identifiability delta = chi2_1(0.95) * 0.0295^2", "tuning_process": "none",
 "results": {"R1": {k: r1[k] for k in ("n", "logg_icc", "logg_within_sd", "logg_between_sd", "trajectory_P1_repeat_A_to_B", "trajectory_P1_oracle_B_on_B", "mu_rmsd_A_vs_B_direct", "ta_ridge_oof_P1_same_compounds", "curvature_logg_sd_median_same_compounds", "mu_within_sd_per_rung")},
             "R2": {k: r2[k] for k in ("n", "logg_icc", "logg_within_sd", "trajectory_P1_repeat_A_to_B", "trajectory_P1_oracle_B_on_B", "mu_rmsd_A_vs_B_direct")},
             "R3_isomers": r["R3_wur_isomer_groups"], "identifiability": idf, "variance_budget": vb},
 "uncertainty": "R1 n=26 compounds (2 preparations), R2 n=124 (bridge fitted on them); ICC point estimates only",
 "tail_metrics": {"ta_AF_weakly_identified": idf["ta_oof_AF_weak"], "ta_AF_identified": idf["ta_oof_AF_identified"]},
 "interpretation": "Independent-preparation duplicates (Q Exactive, 26 compounds) give log g ICC 0.97 with a per-measurement within-compound SD of 0.116, 1.6x the curvature SD v1 used (0.073): curvature understates empirical scale noise, and the 0.988 'reliability' was not a repeatability. Cross-instrument pairs give ICC 0.94 (SD 0.147). Repeat noise accounts for only 6.5 percent (inter-preparation) to 10.3 percent (cross-instrument) of the variance of TA_RIDGE's out-of-fold log g error (0.210), so roughly 90 percent of the Tier A scale error is reproducible compound-specific variation. With a scale measured on an independent preparation, trajectory P1 is 0.065 (A to B), against TA_RIDGE 0.158 on the same compounds and 0.1305 overall: a large learnable gap remains. Scales are identifiable: 42 of 1,325 hit the grid edge (39 heavy compounds at the low-g edge, median m/z 748), median likelihood-interval width 0.15 log units, 0.3 percent wider than 0.5, and the weakly identified compounds carry no absolute failures. WUR has no technical replicates; isomer groups (41 keys) show a within-key log g SD of 0.069, not a repeatability.",
 "decision": "diagnostic", "reason": "measurement noise does not dominate; scale is identifiable; representation work is licensed",
 "informed_later_decisions": "stop condition 'repeat variability dominates' does not fire; stop condition 'scale unidentifiable' does not fire; proceed to Experiments 3-10"})
