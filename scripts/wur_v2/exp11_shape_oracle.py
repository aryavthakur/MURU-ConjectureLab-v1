"""Experiment 11 (optional shape phase, step 1): is there a reproducible, predictable
one-degree-of-freedom shape residual after the best scale model?

Basis: first principal component of training-fold collapse residuals after each
compound's own scale tangent is projected out (training data only). For a
held-out compound with the joint model's predicted scale zhat, the basis is
orthogonalized against the tangent at zhat and a coefficient c is fitted to its
own trajectory (ORACLE). Honest variants: held-energy (fit c on 4 rungs,
predict the 5th); reproducibility of c across independent preparations (R1)
and instruments (R2); predictability of c from structure (nested ridge on the
joint design, out-of-fold R2).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from muru.wur_v2 import runner as RU, models as MO, engine as EN, scale as SC, metrics as M, ledger as LG
from muru.wur_v2.exposure import lcsb_confirmation_keys

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp11"
E = EN.POOLED_ENERGIES
d = RU.load_data(); a = RU.assignment("PRIMARY")
J = RU.run(MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), d, "PRIMARY")

def ortho(b, t):
    tt = (t * t).sum(-1, keepdims=True)
    return b - ((b * t).sum(-1, keepdims=True) / np.maximum(tt, 1e-12)) * t

def coef(res, bt, mask):
    num = np.nansum(np.where(mask, res * bt, 0), -1); den = np.nansum(np.where(mask, bt * bt, 0), -1)
    return num / np.maximum(den, 1e-12)

bases, rows = {}, []
for f in range(5):
    tr = sorted(a.index[a != f]); te = sorted(a.index[a == f])
    fit = EN.collapse_for(d, tr)
    zt = np.log(fit.g_hat); Yt = d.Y.loc[fit.compounds].to_numpy()
    rt = Yt - EN.mu_from_log_g(fit, zt); tt = SC.sensitivity(fit, zt, E)
    rt_o = np.where(np.isfinite(rt), ortho(np.nan_to_num(rt), tt), 0.0)
    _, _, Vt = np.linalg.svd(rt_o - rt_o.mean(0), full_matrices=False)
    b = Vt[0] * np.sign(Vt[0][-1] if Vt[0][-1] != 0 else 1)
    bases[f] = {"basis": b.tolist(), "var_explained_pc1": float((np.linalg.svd(rt_o - rt_o.mean(0), compute_uv=False)[0] ** 2) / (np.linalg.svd(rt_o - rt_o.mean(0), compute_uv=False) ** 2).sum())}
    zh = J.log_g_pred.loc[te].to_numpy(); Y = d.Y.loc[te].to_numpy(); obs = np.isfinite(Y)
    p = EN.mu_from_log_g(fit, zh); th = SC.sensitivity(fit, zh, E); bt = ortho(np.tile(b, (len(te), 1)), th)
    res = np.where(obs, Y - p, np.nan)
    c_all = coef(res, bt, obs)
    p_desc = p + c_all[:, None] * bt
    p_held = np.full_like(p, np.nan)
    for j in range(len(E)):
        m = obs.copy(); m[:, j] = False
        cj = coef(res, bt, m); p_held[:, j] = p[:, j] + cj * bt[:, j]
    # oracle scale (refit z on own trajectory) for reference
    zs = SC.fit_scale(fit, E, Y); p_zs = EN.mu_from_log_g(fit, zs)
    for i, k in enumerate(te):
        rows.append({"group_key": k, "fold": f, "c": c_all[i], **{f"p_{e}": p[i, j] for j, e in enumerate(E)},
                     **{f"pd_{e}": p_desc[i, j] for j, e in enumerate(E)}, **{f"ph_{e}": p_held[i, j] for j, e in enumerate(E)},
                     **{f"pzs_{e}": p_zs[i, j] for j, e in enumerate(E)}})
t = pd.DataFrame(rows).set_index("group_key").loc[d.cov.index]
Y = d.Y.to_numpy()
cols = lambda pre: [f"{pre}_{e}" for e in E]
P1 = {"predicted_scale_only": M.p1(M.errors(t[cols("p")].to_numpy(), Y)),
      "plus_shape_descriptive_oracle": M.p1(M.errors(t[cols("pd")].to_numpy(), Y)),
      "plus_shape_held_energy_oracle": M.p1(M.errors(t[cols("ph")].to_numpy(), Y)),
      "oracle_scale_only": M.p1(M.errors(t[cols("pzs")].to_numpy(), Y))}
held_scale_only = P1["predicted_scale_only"]
gain = {"descriptive_oracle_gain": 1 - P1["plus_shape_descriptive_oracle"] / held_scale_only,
        "held_energy_oracle_gain": 1 - P1["plus_shape_held_energy_oracle"] / held_scale_only}
# predictability of c from structure (nested: ridge on joint design standardized within training fold, alpha by inner CV on c)
Xa, Xm = d.features["TIER_A"], d.features["MORGAN"]
cpred = pd.Series(np.nan, index=d.cov.index)
for f in range(5):
    tr = a.index[a != f]; te = a.index[a == f]
    A = Xa.loc[tr].to_numpy(); mu, sd = A.mean(0), A.std(0) + 1e-12
    Xtr = np.hstack([(A - mu) / sd, 0.3 * Xm.loc[tr].to_numpy()]); Xte = np.hstack([(Xa.loc[te].to_numpy() - mu) / sd, 0.3 * Xm.loc[te].to_numpy()])
    # inner selection on the training compounds' oracle coefficients from this outer run is not available (c is held-out only),
    # so c for training compounds is taken from the other outer folds' held-out fits: every c used to train is itself out-of-fold
    ytr = t.loc[tr, "c"].to_numpy()
    best = min((((Ridge(alpha=al).fit(Xtr[:int(0.8 * len(tr))], ytr[:int(0.8 * len(tr))]).predict(Xtr[int(0.8 * len(tr)):]) - ytr[int(0.8 * len(tr)):]) ** 2).mean(), al) for al in (1, 10, 100, 1000))[1]
    cpred.loc[te] = Ridge(alpha=best).fit(Xtr, ytr).predict(Xte)
c = t["c"]
r2_c = 1 - ((c - cpred) ** 2).sum() / ((c - c.mean()) ** 2).sum()
tb = np.vstack([ortho(np.array(bases[int(a.loc[k])]["basis"])[None, :], SC.sensitivity(EN.collapse_for(d, sorted(a.index[a != int(a.loc[k])])), np.array([J.log_g_pred.loc[k]]), E))[0] for k in d.cov.index])
p_pred_shape = t[cols("p")].to_numpy() + cpred.to_numpy()[:, None] * tb
P1["plus_predicted_shape"] = M.p1(M.errors(p_pred_shape, Y))
# reproducibility of c: R1 duplicates and R2 cross-instrument, oracle scale fitted per copy, same fold profile and basis
def c_for(k, y):
    f = int(a.loc[k]); fit = EN.collapse_for(d, sorted(a.index[a != f])); z = SC.fit_scale(fit, E, y[None, :])
    p = EN.mu_from_log_g(fit, z)[0]; bt = ortho(np.array(bases[f]["basis"])[None, :], SC.sensitivity(fit, z, E))[0]
    m = np.isfinite(y); return float(np.sum(((y - p) * bt)[m]) / np.sum((bt * bt)[m]))
conf = lcsb_confirmation_keys()
raw = pd.read_parquet(ROOT / "artifacts/raw_branch_merged.parquet"); raw = raw[~raw.inchikey_first_block.isin(conf) & raw.ce_numeric.isin(E)]
W = raw.pivot_table(index="inchikey_first_block", columns=["mix", "ce_numeric"], values="mu")
k1 = [k for k in W.index if k in d.cov.index and W.loc[k, 499].notna().all() and W.loc[k, 503].notna().all()]
cA = np.array([c_for(k, W.loc[k, 499][E].to_numpy()) for k in k1]); cB = np.array([c_for(k, W.loc[k, 503][E].to_numpy()) for k in k1])
both = d.cov.index[d.cov.measured_lcsb & d.cov.measured_wur]
wal = pd.read_csv(ROOT / "artifacts/wur_v2/data/wur_aligned_all.csv").pivot(index="group_key", columns="ce_numeric", values="mu").reindex(index=both, columns=E)
ok = [k for k in both if np.isfinite(d.Y.loc[k].to_numpy()).sum() == 5]
cL = np.array([c_for(k, d.Y.loc[k].to_numpy()) for k in ok]); cW = np.array([c_for(k, wal.loc[k].to_numpy()) for k in ok])
res = {"P1": P1, "gain": gain, "basis_by_fold": bases, "c_sd": float(c.std()), "c_predictability_R2_oof": float(r2_c),
       "reproducibility": {"R1_n": len(k1), "R1_corr_cA_cB": float(np.corrcoef(cA, cB)[0, 1]), "R1_sd_diff_over_sd": float(np.std(cA - cB) / np.std(np.r_[cA, cB])),
                           "R2_n": len(ok), "R2_corr_cLCSB_cWUR": float(np.corrcoef(cL, cW)[0, 1]), "R2_sd_diff_over_sd": float(np.std(cL - cW) / np.std(np.r_[cL, cW]))},
       "gate": {"stop_if_held_energy_oracle_gain_lt_0.03": gain["held_energy_oracle_gain"] < 0.03, "stop_if_predictability_R2_lt_0.10": r2_c < 0.10}}
(OUT / "exp11_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps(res, indent=1, default=lambda o: round(float(o), 4)))
LG.append({"experiment_id": "V2-EXP11-SHAPE-ORACLE", "generation": "v2-G3", "parent_model": "TA_MORGAN_JOINT",
 "hypothesis": "After the best scale model, one tangent-orthogonal shape coefficient is reproducible, improves held-energy prediction by >= 3 percent, and is predictable from structure (R2 >= 0.10).",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "training-fold PC1 of tangent-orthogonal collapse residuals; ridge on Tier A + 0.3 Morgan for c",
 "endpoint": "aligned mu 30-90", "hyperparameters_and_space": "c ridge alpha {1,10,100,1000} on a training hold-back", "tuning_process": "basis from training folds only; c oracle per held-out compound",
 "results": res, "uncertainty": "descriptive", "tail_metrics": {},
 "interpretation": "admission reason: protocol section 13(a) fired on the strict reading of Experiment 3 (scale-only term explains 72.5 percent of the E30-E90 MSE gradient under TA_RIDGE, below the 75 percent bar); this step measures the oracle and predictability gates",
 "decision": "diagnostic", "reason": "shape-phase gate", "informed_later_decisions": "continue or stop the shape phase"})
