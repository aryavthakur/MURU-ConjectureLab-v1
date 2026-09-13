"""Revalidate every cached run against a fresh recomputation and record its input fingerprint (review I-1)."""
import json, os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from ast import literal_eval
from pathlib import Path
import pandas as pd
from muru.wur_v2 import runner as RU, models as MO
d = RU.load_data()
ion = pd.read_csv(RU.ROOT / "artifacts/wur_v2/exp07/ion_env_block.csv").set_index("group_key").loc[d.cov.index]
kept = json.loads((RU.ROOT / "artifacts/wur_v2/exp07/ion_env_audit.json").read_text())["kept"]
d.features["TIER_A_ION"] = pd.concat([d.features["TIER_A"], ion[kept]], axis=1)
from muru.discovery import protocol
is_w = (d.cov.primary_source == "WUR").astype(float)
d.features["TIER_A_SOURCE"] = d.features["TIER_A"].assign(is_wur=is_w, wur_x_mass=is_w * d.cov.precursor_mz / protocol.SCALE["precursor_mz"])
ION_ALPHAS = (0.01, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)
makers = {"TA_RIDGE": lambda p: MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), "TA_RIDGE_V1SEL": lambda p: MO.RidgeV1Selection(),
 "B1_MASS_ISOTONIC": lambda p: MO.MassIsotonic(), "EXP07_TA_IONENV": lambda p: MO.RidgeModel("TIER_A_ION", alphas=ION_ALPHAS, model_id="EXP07_TA_IONENV"),
 "MORGAN_RIDGE": lambda p: MO.RidgeModel("MORGAN", alphas=MO.RIDGE_ALPHAS_FP, model_id="MORGAN_RIDGE"),
 "TA_MORGAN_JOINT": lambda p: MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), "TA_THEN_MORGAN": lambda p: MO.TwoStage("MORGAN", "TA_THEN_MORGAN"),
 "MINMAX_KRR_MORGAN": lambda p: MO.KernelRidgeMinMax("MINMAX_MORGAN", "MINMAX_KRR_MORGAN"),
 "ATOMPAIR_RIDGE": lambda p: MO.RidgeModel("ATOMPAIR", alphas=MO.RIDGE_ALPHAS_FP, model_id="ATOMPAIR_RIDGE"),
 "MACCS_RIDGE": lambda p: MO.RidgeModel("MACCS", alphas=MO.RIDGE_ALPHAS_FP, model_id="MACCS_RIDGE"),
 "KNN10_RESIDUAL_MORGAN": lambda p: MO.KNNResidual("MINMAX_MORGAN", "KNN10_RESIDUAL_MORGAN"),
 "TA_ATOMPAIR_JOINT": lambda p: MO.JointRidge("ATOMPAIR", "TA_ATOMPAIR_JOINT"),
 "TA_ION_MORGAN_JOINT": lambda p: MO.JointRidge("MORGAN", "TA_ION_MORGAN_JOINT", base="TIER_A_ION"),
 "DIAG_TA_RIDGE_SOURCE_X_MASS": lambda p: MO.RidgeModel("TIER_A_SOURCE", model_id="DIAG_TA_RIDGE_SOURCE_X_MASS"),
 "JOINT_PLUS_SHAPE": lambda p: MO.ShapeCorrectedJoint({int(k): literal_eval(v) for k, v in RU.run(MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), d, p).cfgs.items()})}
done, skipped = [], []
for meta_path in sorted(RU.RUNS.glob("*/*.json")):
    meta = json.loads(meta_path.read_text()); mid, part = meta["model_id"], meta["partition"]
    tag = "_v2fix" if "_v2fix__" in meta_path.name else ""
    if "PERMUTED" in mid:
        base, seed = mid.split("_PERMUTED_s"); m = MO.PermutedFeatures(makers[base](part), "MORGAN", int(seed))
    elif mid in makers:
        m = makers[mid](part)
    else:
        skipped.append(meta_path.name); continue
    RU.run(m, d, part, tag=tag)
    done.append(meta_path.name); print("ok", meta_path.name, flush=True)
print(len(done), "validated;", "skipped", skipped)
