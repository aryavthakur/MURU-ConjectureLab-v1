"""Experiment 1, part A: reproduce the v1 Stage 3 predictions from committed
code and artifacts (no sealed first-access function is called), then audit
the estimands and compare the historical interval procedure with the
cluster bootstrap that recomputes P1."""
import json, os, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_stage2 import arms_v1, cv as CV, holdcheck as HC
from muru.wur_stage2.descriptors2 import TIER_A2
from muru.wur_v2 import metrics as M
from muru.wur_v2.exposure import assert_wur_exposed
from muru.wur_v2 import identity as ID

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/wur_v2/exp01"; OUT.mkdir(parents=True, exist_ok=True)
assert_wur_exposed()
t0 = time.time()
data_dir = ROOT / "data/external/wur"
long_dev, cov_dev, _ = CV.load_dev2b()
hold_long, hold_cov, _, _ = HC.hold_tables(data_dir)            # HOLD is exposed; v1 aggregation
long = pd.concat([long_dev, hold_long], ignore_index=True)
cov = pd.concat([cov_dev, hold_cov[cov_dev.columns]], ignore_index=True)
a2 = pd.concat([pd.read_csv(arms_v1.A2_PATH), hold_cov[["group_key", *TIER_A2]]], ignore_index=True)
S3 = ROOT / "artifacts/wur_stage3"
sealed_long = pd.read_csv(S3 / "sealed_long_aligned.csv"); cov_s = pd.read_csv(S3 / "sealed_covariates.csv")
keys = sorted(cov_s.group_key); cov_s = cov_s.set_index("group_key").loc[keys].reset_index()
Y = CV.wide(sealed_long, keys)
arms_v1._a2 = lambda: pd.concat([a2, cov_s[["group_key", *TIER_A2]]], ignore_index=True)
ctx = {"repeat": 3, "outer_fold": 0}
arms = {"V1B_RIDGE_TIERA": CV.LinRidge, "S2A_FROZEN_PIPELINE": lambda: CV.S2AFrozen(S3 / "ckpt_s2a_stage3"),
        "B0_NULL_PROFILE": CV.B0NullProfile, "B1_MASS_ONLY_ISOTONIC": CV.B1MassOnly,
        "V1A_STABLE_LAW": arms_v1.StableLaw, "V1C_RICH_RIDGE_24": arms_v1.RichRidge}
preds, diag = {}, {}
for name, make in arms.items():
    arm = make(); arm.fit(long, cov, ctx); preds[name] = arm.predict_mu(cov_s); diag[name] = arm.diagnostics()
wur_train = long[long["source"] == "WUR"]
arm = CV.LinRidge(); arm.fit(wur_train, cov[cov.group_key.isin(set(wur_train.group_key))], ctx)
preds["V1B_WUR_ONLY_TRAINED"] = arm.predict_mu(cov_s)
np.savez_compressed(OUT / "stage3_reproduced_predictions.npz", keys=np.array(keys), Y=Y, **preds)

# ---- reproduction check against the committed Stage 3 record ----
hist = json.loads((S3 / "stage3_result.json").read_text()); pc_hist = pd.read_csv(S3 / "stage3_percompound.csv").set_index("group_key").loc[keys]
repro = {}
for name in preds:
    r = M.compound_rmse(M.errors(preds[name], Y))
    repro[name] = {"P1_reproduced": M.p1(M.errors(preds[name], Y)), "P1_recorded": hist["arms"][name]["P1"],
                   "max_abs_percompound_rmse_diff": float(np.max(np.abs(r - pc_hist[f"rmse_{name}"].to_numpy())))}

# ---- estimand audit ----
b0 = preds["B0_NULL_PROFILE"]
est = {name: M.summary(p, Y, b0) for name, p in preds.items()}
for name in est:
    est[name]["per_rung"] = M.per_rung(preds[name], Y, (30., 45., 60., 75., 90.))

# ---- intervals: historical procedure vs corrected ----
smiles_by_key = {}
ident = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv").set_index("group_key")
v2_scaffold = ident.loc[keys, "scaffold_group"].to_numpy()
stereo = cov_s["stereo_scaffold"].to_numpy()
pairs = [("V1B_RIDGE_TIERA", "S2A_FROZEN_PIPELINE"), ("V1B_RIDGE_TIERA", "B1_MASS_ONLY_ISOTONIC"),
         ("V1B_RIDGE_TIERA", "B0_NULL_PROFILE"), ("B1_MASS_ONLY_ISOTONIC", "S2A_FROZEN_PIPELINE"),
         ("V1A_STABLE_LAW", "S2A_FROZEN_PIPELINE"), ("V1A_STABLE_LAW", "V1B_RIDGE_TIERA"),
         ("V1C_RICH_RIDGE_24", "V1B_RIDGE_TIERA"), ("V1B_WUR_ONLY_TRAINED", "V1B_RIDGE_TIERA")]
comp = {}
for c, r in pairs:
    rc, rr = M.compound_rmse(M.errors(preds[c], Y)), M.compound_rmse(M.errors(preds[r], Y))
    dc = rc - rr
    old = hist["comparisons"][f"{c}_vs_{r}"]
    comp[f"{c}_vs_{r}"] = {
        "historical_recorded": {k: old[k] for k in ("P1_cand", "P1_ref", "rel_improvement", "mean_paired_rmse_diff", "ci95_compound", "ci95_cluster_stereo_scaffold")},
        "historical_procedure_recomputed": {"estimand": "mean paired per-compound RMSE difference",
            "ci95_compound": M.compound_mean_rmse_bootstrap(dc), "ci95_cluster_stereo": M.compound_mean_rmse_bootstrap(dc, stereo)},
        "corrected_cluster_v2_scaffold": M.cluster_bootstrap(preds[c], preds[r], Y, v2_scaffold),
        "corrected_cluster_stereo_scaffold": M.cluster_bootstrap(preds[c], preds[r], Y, stereo),
        "corrected_compound_unit": M.cluster_bootstrap(preds[c], preds[r], Y, np.array(keys))}
res = {"experiment": "EXP01_ESTIMAND_AUDIT_PART_A", "population": {"n": len(keys), "n_cells": int(np.isfinite(Y).sum()),
       "n_v2_scaffold_groups": int(len(set(v2_scaffold))), "n_stereo_scaffold_groups": int(len(set(stereo)))},
       "training_population": {"n": int(cov.group_key.nunique())}, "reproduction": repro, "estimands": est,
       "comparisons": comp, "diagnostics": diag, "seconds": time.time() - t0}
(OUT / "part_a_stage3_estimands.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps(repro, indent=1))
for k, v in comp.items():
    cc = v["corrected_cluster_v2_scaffold"]
    print(k, "P1 %.4f/%.4f ratio %.3f %s diff %s | MRMSE diff %.4f %s | hist mean-rmse ci %s" % (
        cc["P1_cand"], cc["P1_ref"], cc["P1_ratio"], np.round(cc["P1_ratio_ci"], 3), np.round(cc["P1_diff_ci"], 4),
        cc["MRMSE_diff"], np.round(cc["MRMSE_diff_ci"], 4), np.round(v["historical_recorded"]["ci95_compound"], 4)))
for k, v in est.items():
    print(k, {x: round(v[x], 4) for x in ("P1", "MRMSE", "MED", "Q90", "Q95", "CVaR95", "AF", "AF_max", "S4")})
