"""Experiment 3: is the E30 -> E90 error gradient amplification of scale error
where the out-of-fold profile is steep?

For each compound (PRIMARY OOF, TA_RIDGE): predicted scale zhat, oracle scale
z* fitted to its own trajectory with the SAME out-of-fold profile (a labelled
ORACLE diagnostic), scale-only error e_s = Phi(zhat) - Phi(z*), shape residual
r = Phi(z*) - y, observed error e = e_s + r. Per rung: MSE(e) = MSE(e_s) +
MSE(r) + 2 cov-term. Linearized check: e_lin = s(z*) (zhat - z*) with s the
finite-difference sensitivity of the training profile.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, scale as SC, metrics as M, ledger as LG

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp03"
E = EN.POOLED_ENERGIES
d = RU.load_data(False); a = RU.assignment("PRIMARY")
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
rows = []
for f in range(5):
    fit = EN.collapse_for(d, sorted(a.index[a != f]))
    ks = sorted(a.index[a == f]); Y = d.Y.loc[ks].to_numpy()
    zhat = ta.log_g_pred.loc[ks].to_numpy(); zs = SC.fit_scale(fit, E, Y)
    p_hat, p_or = EN.mu_from_log_g(fit, zhat), EN.mu_from_log_g(fit, zs)
    s = SC.sensitivity(fit, zs, E); s_hat = SC.sensitivity(fit, zhat, E)
    for i, k in enumerate(ks):
        for j, e in enumerate(E):
            if not np.isfinite(Y[i, j]):
                continue
            rows.append({"group_key": k, "E": e, "y": Y[i, j], "pred": p_hat[i, j], "oracle": p_or[i, j], "zhat": zhat[i], "zstar": zs[i],
                         "sens_star": s[i, j], "sens_hat": s_hat[i, j]})
t = pd.DataFrame(rows)
t["e"] = t.pred - t.y; t["e_scale"] = t.pred - t.oracle; t["r_shape"] = t.oracle - t.y
t["dz"] = t.zhat - t.zstar; t["e_lin"] = t.sens_star * t.dz; t["e_lin_hat"] = t.sens_hat * t.dz
t.to_parquet(OUT / "cells.parquet")
per = []
for e, g in t.groupby("E"):
    mse = (g.e ** 2).mean(); ms = (g.e_scale ** 2).mean(); mr = (g.r_shape ** 2).mean(); cross = 2 * (g.e_scale * g.r_shape).mean()
    per.append({"E": e, "RMSE_obs": np.sqrt(mse), "MSE_obs": mse, "MSE_scale": ms, "MSE_shape": mr, "cross": cross,
                "scale_share": ms / mse, "shape_share": mr / mse, "cross_share": cross / mse,
                "RMSE_scale_linearized": np.sqrt((g.e_lin ** 2).mean()),
                "R2_elin_vs_escale": 1 - ((g.e_scale - g.e_lin) ** 2).sum() / ((g.e_scale - g.e_scale.mean()) ** 2).sum(),
                "mean_abs_sensitivity": g.sens_star.abs().mean(), "corr_abs_e_vs_abs_sens_dz": np.corrcoef(g.e.abs(), (g.sens_hat * g.dz).abs())[0, 1]})
per = pd.DataFrame(per)
lo, hi = per.iloc[0], per.iloc[-1]
grad = {"MSE_gradient_obs_E30_minus_E90": lo.MSE_obs - hi.MSE_obs, "MSE_gradient_scale_component": lo.MSE_scale - hi.MSE_scale,
        "MSE_gradient_shape_component": lo.MSE_shape - hi.MSE_shape, "MSE_gradient_cross_component": lo.cross - hi.cross}
grad["fraction_of_gradient_explained_by_scale"] = grad["MSE_gradient_scale_component"] / grad["MSE_gradient_obs_E30_minus_E90"]
grad["fraction_explained_by_scale_plus_cross"] = (grad["MSE_gradient_scale_component"] + grad["MSE_gradient_cross_component"]) / grad["MSE_gradient_obs_E30_minus_E90"]
# pre-measurement version: predicted |sens(zhat)| times a constant scale-error SD
sd_dz = t.groupby("group_key").dz.first().std()
per["RMSE_premeasurement_sens_times_sd"] = t.assign(v=(t.sens_hat * sd_dz) ** 2).groupby("E").v.mean().pipe(np.sqrt).to_numpy()
# low-sensitivity check at E30
g30 = t[t.E == 30.0].copy(); g30["sens_tercile"] = pd.qcut(g30.sens_star.abs(), 3, labels=["low", "mid", "high"])
terc = g30.groupby("sens_tercile", observed=True).apply(lambda g: pd.Series({"n": len(g), "RMSE_obs": np.sqrt((g.e ** 2).mean()), "RMSE_shape": np.sqrt((g.r_shape ** 2).mean()),
                                                              "RMSE_scale": np.sqrt((g.e_scale ** 2).mean()), "mean_y": g.y.mean()})).reset_index()
# pooled trajectory decomposition
tot = {"P1_obs": np.sqrt((t.e ** 2).mean()), "P1_scale_only": np.sqrt((t.e_scale ** 2).mean()), "P1_oracle_shape_residual": np.sqrt((t.r_shape ** 2).mean()),
       "share_scale": (t.e_scale ** 2).mean() / (t.e ** 2).mean(), "share_shape": (t.r_shape ** 2).mean() / (t.e ** 2).mean(),
       "share_cross": 2 * (t.e_scale * t.r_shape).mean() / (t.e ** 2).mean()}
res = {"per_rung": per.to_dict("records"), "gradient": grad, "E30_by_sensitivity_tercile": terc.to_dict("records"), "pooled": tot,
       "scale_error_sd_log_units": float(sd_dz)}
(OUT / "exp03_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(per.round(4).to_string()); print(json.dumps(grad, indent=1, default=float)); print(terc.round(4).to_string()); print(json.dumps(tot, default=float))
LG.append({"experiment_id": "V2-EXP03-DERIVATIVE-AMPLIFICATION", "generation": "v2-G0", "parent_model": "TA_RIDGE (PRIMARY OOF)",
 "hypothesis": "The E30->E90 error gradient is mainly scale error amplified where the out-of-fold profile is steep.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "TIER_A", "endpoint": "aligned mu 30-90",
 "hyperparameters_and_space": "finite-difference step 0.05 log units", "tuning_process": "none; oracle scale is a diagnostic",
 "results": res, "uncertainty": "descriptive; per-rung decomposition includes the cross term",
 "tail_metrics": {"E30_low_sensitivity_RMSE": float(terc.RMSE_obs.iloc[0]), "E30_high_sensitivity_RMSE": float(terc.RMSE_obs.iloc[-1])},
 "interpretation": "see exp03_results.json; summarized in the v2 experiments report",
 "decision": "diagnostic", "reason": "decides whether E30 error licenses a shape model", "informed_later_decisions": "shape-phase gate (protocol section 13a)"})
