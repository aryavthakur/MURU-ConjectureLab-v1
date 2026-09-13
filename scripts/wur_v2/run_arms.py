"""Experiments 7-9: evaluate registered representation arms against TA_RIDGE and ledger them.

Usage: run_arms.py ARM_ID [ARM_ID ...]
"""
import json, os, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, admission as AD, ledger as LG
from muru.wur_v2 import ion_env as IE

ROOT = Path(__file__).resolve().parents[2]
d = RU.load_data()
ion = pd.read_csv(ROOT / "artifacts/wur_v2/exp07/ion_env_block.csv").set_index("group_key").loc[d.cov.index]
audit = json.loads((ROOT / "artifacts/wur_v2/exp07/ion_env_audit.json").read_text())
d.features["TIER_A_ION"] = pd.concat([d.features["TIER_A"], ion[audit["kept"]]], axis=1)
ION_ALPHAS = (0.01, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)
REF = MO.RidgeModel("TIER_A", model_id="TA_RIDGE")
ARMS = {
 "EXP07_TA_IONENV": dict(model=lambda: MO.RidgeModel("TIER_A_ION", alphas=ION_ALPHAS, model_id="EXP07_TA_IONENV"), gen="v2-G1",
     rep="TIER_A (12, protocol.SCALE) + ION_ENV (12 audited counts/proximities)", space="alpha in " + str(ION_ALPHAS),
     hyp="Audited basic-site, carbonyl-class and charge-to-labile-bond features add scale information beyond Tier A's elemental totals."),
 "EXP08A_MORGAN_RIDGE": dict(model=lambda: MO.RidgeModel("MORGAN", alphas=MO.RIDGE_ALPHAS_FP, model_id="MORGAN_RIDGE"), gen="v2-G1",
     rep="Morgan r2 2048 hashed counts, log1p, no chirality, no filtering", space="alpha in " + str(MO.RIDGE_ALPHAS_FP),
     hyp="Local connectivity alone predicts the scale better than Tier A.",
     perm=lambda: [MO.PermutedFeatures(MO.RidgeModel("MORGAN", alphas=MO.RIDGE_ALPHAS_FP, model_id="MORGAN_RIDGE"), "MORGAN", s) for s in range(5)]),
 "EXP08B_TA_MORGAN_JOINT": dict(model=lambda: MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), gen="v2-G1",
     rep="training-standardized TIER_A + block-weighted Morgan log1p counts", space="alpha {0.1..300} x block weight {0.1,0.3,1}",
     hyp="Tier A trend plus Morgan environments in one ridge beats Tier A."),
 "EXP08C_TA_THEN_MORGAN": dict(model=lambda: MO.TwoStage("MORGAN", "TA_THEN_MORGAN"), gen="v2-G1",
     rep="TIER_A ridge then Morgan ridge on residuals cross-fitted inside the training set", space="stage-2 alpha {0.1..300}",
     hyp="A Morgan correction of cross-fitted Tier A residuals beats Tier A."),
 "EXP08D_MINMAX_KRR": dict(model=lambda: MO.KernelRidgeMinMax("MINMAX_MORGAN", "MINMAX_KRR_MORGAN"), gen="v2-G1",
     rep="kernel ridge, MinMax (count Tanimoto) kernel on Morgan r2 2048 counts", space="alpha in " + str(MO.KERNEL_ALPHAS),
     hyp="A Tanimoto-kernel scale model beats Tier A."),
 "EXP09A_ATOMPAIR_RIDGE": dict(model=lambda: MO.RidgeModel("ATOMPAIR", alphas=MO.RIDGE_ALPHAS_FP, model_id="ATOMPAIR_RIDGE"), gen="v2-G1",
     rep="atom-pair 2048 hashed counts, log1p", space="alpha in " + str(MO.RIDGE_ALPHAS_FP),
     hyp="A distance-aware structural metric (atom pairs) predicts the scale at least as well as Morgan."),
 "EXP09B_MACCS_RIDGE": dict(model=lambda: MO.RidgeModel("MACCS", alphas=MO.RIDGE_ALPHAS_FP, model_id="MACCS_RIDGE"), gen="v2-G1",
     rep="MACCS 167 keys", space="alpha in " + str(MO.RIDGE_ALPHAS_FP), hyp="Compact predefined functional keys carry the structural signal."),
 "EXP09C_KNN_RESIDUAL_MORGAN": dict(model=lambda: MO.KNNResidual("MINMAX_MORGAN", "KNN10_RESIDUAL_MORGAN"), gen="v2-G1",
     rep="TIER_A ridge + similarity-weighted mean of cross-fitted residuals of 10 nearest training compounds (MinMax Morgan)", space="none (k=10 fixed)",
     hyp="Scale residuals are locally smooth in Morgan similarity space."),
}
pop = json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"]
F = RU.folds()
for arm_id in sys.argv[1:]:
    spec = ARMS[arm_id]; t0 = time.time()
    perm = spec["perm"]() if "perm" in spec else []
    res = AD.evaluate(d, spec["model"](), REF, perm)
    out = ROOT / "artifacts/wur_v2" / arm_id.split("_")[0].lower().replace("exp0", "exp0")[:5]
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{arm_id}.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    s = res["summary"]; pb = res["comparisons"]["PRIMARY"]["bootstrap"]
    print(arm_id, "admitted" if res["admitted"] else "NOT admitted", {p: round(v["ratio"], 4) for p, v in s.items()},
          "PRIMARY P1 %.4f ratio CI %s" % (s["PRIMARY"]["P1_cand"], np.round(pb["P1_ratio_ci"], 4)),
          "AF %.3f vs %.3f" % (s["PRIMARY"]["AF_cand"], s["PRIMARY"]["AF_ref"]), {k: v for k, v in res["criteria"].items() if not v},
          {k: round(v["P1_ratio"], 3) for k, v in res["strata_primary"].items()}, res["permutation_P1_ratios"], "%.0fs" % (time.time() - t0), flush=True)
    LG.append({"experiment_id": f"V2-{arm_id}", "generation": spec["gen"], "parent_model": "TA_RIDGE", "hypothesis": spec["hyp"],
               "population_sha256": pop, "partition": {p: F["partitions"][p]["assignment_sha256"] for p in AD.PARTITIONS},
               "representation": spec["rep"], "endpoint": "aligned mu 30-90, pooled OOF", "hyperparameters_and_space": spec["space"],
               "tuning_process": "nested inner grouped 4-fold with inner collapse refits, trajectory SSE",
               "compute_seconds": time.time() - t0,
               "results": {"summary": s, "strata_primary": res["strata_primary"], "cfgs_primary": res["comparisons"]["PRIMARY"]["cand_cfgs"],
                           "primary_cand": res["comparisons"]["PRIMARY"]["cand"], "primary_ref": res["comparisons"]["PRIMARY"]["ref"],
                           "permutation_P1_ratios": res["permutation_P1_ratios"]},
               "uncertainty": {"PRIMARY": pb, "STRICT": res["comparisons"]["STRICT"]["bootstrap"]},
               "tail_metrics": {p: {k: res["comparisons"][p]["cand"][k] for k in ("AF", "AF_max", "Q95", "CVaR95", "S4")} for p in ("PRIMARY", "STRICT")},
               "interpretation": "admission criteria: " + json.dumps(res["criteria"]),
               "decision": "accepted" if res["admitted"] else "rejected",
               "reason": "all protocol section 12 criteria hold" if res["admitted"] else "fails: " + ", ".join(k for k, v in res["criteria"].items() if not v),
               "informed_later_decisions": "candidate set for selection" if res["admitted"] else "not carried forward"})
