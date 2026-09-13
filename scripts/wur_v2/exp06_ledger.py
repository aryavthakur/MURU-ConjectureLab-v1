import json
from pathlib import Path
import pandas as pd
from muru.wur_v2 import ledger as LG, runner as RU
ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "artifacts/wur_v2/exp06/exp06_results.json").read_text())
F = RU.folds()
LG.append({"experiment_id": "V2-EXP06-LEARNING-CURVES", "generation": "v2-G0", "parent_model": "B1, TA_RIDGE, MORGAN_RIDGE",
 "hypothesis": "Tier A is representation-limited (flat with more groups) while a fixed Morgan ridge keeps improving; random-split gains exceed structural-split gains.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": {p: F["partitions"][p]["assignment_sha256"] for p in ("PRIMARY", "STRICT", "RANDOM")},
 "representation": "precursor m/z; TIER_A; MORGAN r2 2048 log1p counts", "endpoint": "aligned mu 30-90, pooled OOF P1 over all 1,325 compounds",
 "hyperparameters_and_space": "TA alpha {0.01..100}; MORGAN alpha {0.1..300}", "tuning_process": "nested inner grouped folds on each subsample; fractions 25/50/75/100 of training groups, seeds 0-2",
 "results": r["slopes"], "uncertainty": "SD over 3 subsample seeds reported in learning_curves_summary.csv (0.0004-0.0037)", "tail_metrics": {},
 "interpretation": "Tier A flattens by 50 percent of groups (PRIMARY 0.1327 -> 0.1305 at 100 percent; STRICT 0.1356 -> 0.1327): representation-limited. Morgan is worse than Tier A at 25 percent, overtakes it by 50 percent, and still improves to 100 percent on PRIMARY (0.1288, 0.1254, 0.1239) while flattening from 75 percent on STRICT (0.1305, 0.1305). Morgan's advantage over Tier A at full data is 11 percent on RANDOM (0.1162 vs 0.1306), 5.1 percent on PRIMARY (0.1239 vs 0.1305) and 1.7 percent on STRICT (0.1305 vs 0.1327): local structure carries real scale information, a large part of it is transfer from close chemical neighbours, and less generalizes to structurally novel clusters.",
 "decision": "diagnostic", "reason": "representation-limited Tier A; Morgan partly coverage-limited", "informed_later_decisions": "Experiment 8 must pass STRICT and GIANT; MORGAN_RIDGE at 100 percent PRIMARY is Experiment 8 arm A"})
