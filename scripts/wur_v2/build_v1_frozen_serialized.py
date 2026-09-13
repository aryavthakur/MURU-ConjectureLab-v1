"""Serialize the historical MURU-WUR-v1 final candidate (V1B_RIDGE_TIERA as trained for Stage 3 on
DEV2B + HOLD) for use as a historical secondary comparator; verify it reproduces the Stage 3 predictions."""
import json, os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_stage2 import cv as CV, holdcheck as HC
from muru.wur_v2 import candidate as CA
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/candidate"
long_dev, cov_dev, _ = CV.load_dev2b()
hold_long, hold_cov, _, _ = HC.hold_tables(ROOT / "data/external/wur")
long = pd.concat([long_dev, hold_long], ignore_index=True); cov = pd.concat([cov_dev, hold_cov[cov_dev.columns]], ignore_index=True)
arm = CV.LinRidge(); arm.fit(long, cov, {"repeat": 3, "outer_fold": 0})
m = {"kind": "tier_a_ridge", "historical": "MURU-WUR-v1 V1B_RIDGE_TIERA as trained for Stage 3 (921 compounds, v1 aggregation)",
     "profile": {"knots_log_u": arm.fit_.phi_u.tolist(), "values": arm.fit_.phi_v.tolist(), "energy_scale": 30.0},
     "cfg": {"alpha": arm.alpha_}, "coef_tier_a": arm.model_.coef_.tolist(), "intercept": float(arm.model_.intercept_),
     "n_training": int(len(arm.fit_.compounds))}
m["feature_spec"] = CA.feature_spec(); m["canary_smiles"] = list(CA.CANARY_SMILES)
m["canary_log_g"] = CA._predict_log_g_raw(m, CA.CANARY_SMILES, CA.CANARY_MZ).tolist()
S3 = ROOT / "artifacts/wur_stage3"
cov_s = pd.read_csv(S3 / "sealed_covariates.csv")
from muru.wur_stage2.world import POOLED_ENERGIES
ident = pd.read_csv(ROOT / "artifacts/wur_v2/data/wur_pos_identity.csv").set_index("connectivity_key")
mu_json = CA.predict_mu(m, ident.loc[cov_s.group_key, "smiles"], cov_s.precursor_mz, POOLED_ENERGIES)
mu_arm = arm.predict_mu(cov_s)
parity = float(np.max(np.abs(mu_json - mu_arm)))
(OUT / "V1B_RIDGE_TIERA_FROZEN.json").write_text(CA.canonical_json(m) + "\n")
man = json.loads((OUT / "candidate_manifest.json").read_text())
man["V1B_RIDGE_TIERA_FROZEN"] = {"sha256": CA.sha256_of(m), "cfg": m["cfg"], "n_training": m["n_training"], "stage3_prediction_parity_max_abs_mu": parity}
(OUT / "candidate_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
print(parity, man["V1B_RIDGE_TIERA_FROZEN"])
assert parity < 1e-9
