"""Corrected Morgan permutation controls (5 distinct seeds) for EXP08A and EXP08B."""
import json
from pathlib import Path
from muru.wur_v2 import runner as RU, models as MO, ledger as LG
ROOT = Path(__file__).resolve().parents[2]
d = RU.load_data()
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
out = {}
for name, make in {"MORGAN_RIDGE": lambda: MO.RidgeModel("MORGAN", alphas=MO.RIDGE_ALPHAS_FP, model_id="MORGAN_RIDGE"),
                   "TA_MORGAN_JOINT": lambda: MO.JointRidge("MORGAN", "TA_MORGAN_JOINT")}.items():
    for s in range(5):
        pm = MO.PermutedFeatures(make(), "MORGAN", s)
        r = RU.run(pm, d, "PRIMARY", tag="_v2fix")
        out[pm.id] = RU.compare(d, r.pred, ta.pred, "PRIMARY", None, boot=False)["P1_ratio"]
        print(pm.id, round(out[pm.id], 4), flush=True)
(ROOT / "artifacts/wur_v2/exp08/permutation_controls_corrected.json").write_text(json.dumps(out, indent=1) + "\n")
LG.append({"experiment_id": "V2-EXP08P-PERMUTATION-CONTROLS-CORRECTED", "generation": "v2-G1", "parent_model": "MORGAN_RIDGE, TA_MORGAN_JOINT",
 "hypothesis": "Morgan gains vanish when fingerprint rows are permuted across compounds through the full nested pipeline.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "Morgan block permuted (5 distinct seeds)",
 "endpoint": "aligned mu 30-90", "hyperparameters_and_space": "as the unpermuted arms", "tuning_process": "nested",
 "results": out, "uncertainty": "5 permutations", "tail_metrics": {},
 "interpretation": "Correction: the controls recorded inside V2-EXP08A reused one permutation for all five seeds (PermutedFeatures cached the permuted block under a seed-free name; fixed, regression test test_permutation_seeds_are_distinct). These are the valid controls.",
 "decision": "diagnostic", "reason": "negative control for admission criterion c4", "informed_later_decisions": "c4 re-read for EXP08A/B"})
