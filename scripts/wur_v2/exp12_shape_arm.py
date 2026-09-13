"""Amendment A-2: the single nested shape arm, evaluated against TA_RIDGE (section 12) and TA_MORGAN_JOINT (A-2 bar)."""
import json, os, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from ast import literal_eval
from pathlib import Path
import numpy as np
from muru.wur_v2 import runner as RU, models as MO, admission as AD, ledger as LG
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp12"; OUT.mkdir(parents=True, exist_ok=True)
d = RU.load_data(); t0 = time.time()
joint = MO.JointRidge("MORGAN", "TA_MORGAN_JOINT")
res_parts = {}
class Factory:
    """Shape arm whose joint configuration follows the nested joint run of the same partition."""
for p in AD.PARTITIONS:
    jr = RU.run(joint, d, p)
    cfgs = {int(k): literal_eval(v) for k, v in jr.cfgs.items()}
    sm = MO.ShapeCorrectedJoint(cfgs)
    sr = RU.run(sm, d, p)
    b0 = RU.b0(d, p)
    res_parts[p] = {"vs_joint": RU.compare(d, sr.pred, jr.pred, p, b0, boot=(p in ("PRIMARY", "STRICT"))),
                    "vs_ta": RU.compare(d, sr.pred, RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, p).pred, p, b0, boot=(p == "PRIMARY")),
                    "shape_alphas": sr.cfgs}
    print(p, round(res_parts[p]["vs_joint"]["cand"]["P1"], 4), "vs joint", round(res_parts[p]["vs_joint"]["P1_ratio"], 4), "vs TA", round(res_parts[p]["vs_ta"]["P1_ratio"], 4), sr.cfgs, flush=True)
st = RU.strata(d, RU.run(MO.ShapeCorrectedJoint({int(k): literal_eval(v) for k, v in RU.run(joint, d, "PRIMARY").cfgs.items()}), d, "PRIMARY").pred, RU.run(joint, d, "PRIMARY").pred)
pj = res_parts["PRIMARY"]["vs_joint"]
bar = {"i_section12_vs_TA_primary_ratio_le_0.98": res_parts["PRIMARY"]["vs_ta"]["P1_ratio"] <= 0.98,
       "ii_primary_vs_joint_ratio_le_0.98": pj["P1_ratio"] <= 0.98, "ii_ci_upper_lt_1": pj["bootstrap"]["P1_ratio_ci"][1] < 1.0,
       **{f"iii_{p}_vs_joint_lt_1": res_parts[p]["vs_joint"]["P1_ratio"] < 1.0 for p in ("PARTITION_S1", "PARTITION_S2", "STRICT", "GIANT")},
       "iii_LCSB_vs_joint_lt_1": st["LCSB_primary"]["P1_ratio"] < 1.0, "iii_WUR_vs_joint_lt_1": st["WUR_primary"]["P1_ratio"] < 1.0,
       "iv_AF_not_higher": pj["cand"]["AF"] <= pj["ref"]["AF"]}
out = {"partitions": res_parts, "strata_vs_joint": st, "A2_bar": bar, "selected_over_joint": all(bar.values()), "seconds": time.time() - t0}
(OUT / "exp12_shape_arm.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps(bar, indent=1), "SELECTED" if out["selected_over_joint"] else "NOT SELECTED", pj["bootstrap"]["P1_ratio_ci"], {k: round(v["P1_ratio"], 3) for k, v in st.items()})
LG.append({"experiment_id": "V2-EXP12-JOINT-PLUS-SHAPE", "generation": "v2-G3", "parent_model": "TA_MORGAN_JOINT",
 "hypothesis": "Amendment A-2: one structure-predicted, tangent-orthogonal shape coefficient improves unseen-compound trajectories by >= 2 percent over the joint one-scale model, stably.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": {p: RU.folds()["partitions"][p]["assignment_sha256"] for p in AD.PARTITIONS}, "representation": "joint Tier A + Morgan scale; shape coefficient ridge on the same design",
 "endpoint": "aligned mu 30-90", "hyperparameters_and_space": "shape ridge alpha {10,100,1000}; joint cfg from the nested joint run per fold",
 "tuning_process": "nested; shape coefficients cross-fitted inside each training set", "compute_seconds": out["seconds"],
 "results": {p: {"P1": v["vs_joint"]["cand"]["P1"], "ratio_vs_joint": v["vs_joint"]["P1_ratio"], "ratio_vs_TA": v["vs_ta"]["P1_ratio"], "AF": v["vs_joint"]["cand"]["AF"], "AF_joint": v["vs_joint"]["ref"]["AF"]} for p, v in res_parts.items()},
 "uncertainty": {"PRIMARY_vs_joint": pj["bootstrap"], "STRICT_vs_joint": res_parts["STRICT"]["vs_joint"]["bootstrap"]},
 "tail_metrics": {"strata_vs_joint": st}, "interpretation": "A-2 bar: " + json.dumps(bar),
 "decision": "accepted" if out["selected_over_joint"] else "rejected", "reason": "A-2 selection bar " + ("met" if out["selected_over_joint"] else "not met"),
 "informed_later_decisions": "architecture choice: one scale versus scale plus one shape coefficient"})
