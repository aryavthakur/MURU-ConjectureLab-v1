"""Experiment 4: precursor survival versus fragment depth in the out-of-fold errors.

mu = s * r_p + (1 - s) * d, with s the precursor intensity fraction, r_p the
observed/declared precursor mass ratio and d the normalized mean mass of the
non-precursor ions. d is undefined for a precursor-only spectrum and is never
filled. Analysis is at native rungs where no interpolation touches s or d:
LCSB-primary compounds at 30-90 (native = aligned coordinate) and WUR-primary
compounds at their native rungs 30-90 with the model evaluated at the
map-inverted energy (E_WUR - a) / b.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, ledger as LG
from muru.wur_v2.population import bridge

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp04"
E = EN.POOLED_ENERGIES
d = RU.load_data(False); a = RU.assignment("PRIMARY")
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
nat = pd.read_csv(ROOT / "artifacts/wur_v2/data/native_cells.csv")
A, B = bridge()
fits = {f: EN.collapse_for(d, sorted(a.index[a != f])) for f in range(5)}
rows = []
for src in ("LCSB", "WUR"):
    keys = d.cov.index[d.cov.primary_source == src]
    sub = nat[(nat.source == src) & nat.connectivity_key.isin(keys) & nat.ce_numeric.isin(E)]
    for k, g in sub.groupby("connectivity_key"):
        f = fits[int(a.loc[k])]
        e_native = g.ce_numeric.to_numpy()
        e_model = e_native if src == "LCSB" else (e_native - A) / B
        pred = EN.mu_from_log_g(f, np.array([ta.log_g_pred.loc[k]]), e_model)[0]
        for (_, r), p, em in zip(g.iterrows(), pred, e_model):
            rows.append({"group_key": k, "source": src, "E_native": r.ce_numeric, "E_model": em, "mu": r.mu, "pred": p,
                         "s": r.survival_yield, "d": r.fragment_depth, "rp": r.precursor_mass_ratio})
t = pd.DataFrame(rows); t["e"] = t.pred - t.mu
t["regime"] = np.select([t.d.isna(), t.s >= 0.5, t.s >= 0.05], ["precursor_only", "survival_dominated", "mixed"], "fragment_dominated")
t["identity_residual"] = t.mu - (t.s * t.rp.fillna(1.0) + (1 - t.s) * t.d.fillna(0.0))
t.to_parquet(OUT / "cells.parquet")
out = {"n_cells": len(t), "identity_max_abs_residual_defined_cells": float(t.loc[t.d.notna() & t.rp.notna(), "identity_residual"].abs().max()),
       "precursor_only_cells_by_rung": t[t.regime == "precursor_only"].groupby("E_native").size().to_dict()}
reg = t.groupby(["source", "E_native", "regime"]).apply(lambda g: pd.Series({"n": len(g), "RMSE": np.sqrt((g.e ** 2).mean()), "bias": g.e.mean()})).reset_index()
out["by_regime"] = reg.to_dict("records")
# partial R2 of the error on centred s and d, per rung, cells with defined d
pr = []
for (src, e), g in t[t.d.notna()].groupby(["source", "E_native"]):
    y = g.e.to_numpy()
    def r2(X):
        X = np.column_stack([np.ones(len(y)), X]); beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return 1 - ((y - X @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    rs, rd, rb = r2(g.s), r2(g.d), r2(np.column_stack([g.s, g.d]))
    pr.append({"source": src, "E": e, "n": len(g), "R2_s": rs, "R2_d": rd, "R2_both": rb, "unique_s": rb - rd, "unique_d": rb - rs,
               "corr_e_s": np.corrcoef(y, g.s)[0, 1], "corr_e_d": np.corrcoef(y, g.d)[0, 1], "frac_s_ge_0.5": float((g.s >= 0.5).mean())})
out["partial_R2"] = pr
# squared-error contribution: how much of each rung's MSE comes from survival-dominated vs fragment-dominated cells
sh = t.groupby(["E_native", "regime"]).apply(lambda g: (g.e ** 2).sum()).unstack(fill_value=0)
out["mse_share_by_regime"] = (sh.div(sh.sum(1), axis=0)).round(3).reset_index().to_dict("records")
(OUT / "exp04_results.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps({k: out[k] for k in ("n_cells", "identity_max_abs_residual_defined_cells", "precursor_only_cells_by_rung")}, default=float))
print(pd.DataFrame(pr).round(3).to_string()); print(pd.DataFrame(out["mse_share_by_regime"]).to_string())
print(reg[reg.E_native.isin([30.0, 90.0])].round(3).to_string())
LG.append({"experiment_id": "V2-EXP04-SURVIVAL-DEPTH", "generation": "v2-G0", "parent_model": "TA_RIDGE (PRIMARY OOF)",
 "hypothesis": "Early-energy error is associated mainly with precursor survival/onset and late-energy error with fragment depth.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "TIER_A", "endpoint": "native mu with exact s/d decomposition",
 "hyperparameters_and_space": "none", "tuning_process": "none", "results": out, "uncertainty": "descriptive",
 "tail_metrics": {}, "interpretation": "see exp04_results.json; summarized in the v2 experiments report",
 "decision": "diagnostic", "reason": "decides whether an onset or a tail-shape experiment is warranted", "informed_later_decisions": "decision gate question 5/6"})
