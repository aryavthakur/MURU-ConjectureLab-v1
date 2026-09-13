"""Experiment 5: acquisition and ion effects, matched identities first.

(a) Paired cross-instrument: 124 compounds with both copies; per-rung mean
    WUR-minus-LCSB mu after the frozen map, cluster bootstrap 90% CI, TOST-style
    equivalence against +/-0.02 (two-thirds of the inter-mixture repeatability
    SD); log g difference versus precursor m/z (source x mass).
(b) Unpaired: TA_RIDGE out-of-fold signed trajectory bias and log g error by
    primary source, adjusted for mass, with a source x mass term.
(c) Adduct strata and WUR operator campaigns.
(d) Native versus aligned scoring for WUR-primary compounds: the model is
    evaluated at the map-inverted energy for each native rung; bridge residual =
    native error minus aligned error at the pooled rungs.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, scale as SC, metrics as M, ledger as LG
from muru.wur_v2.population import bridge

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp05"
E = EN.POOLED_ENERGIES; TOL = 0.02; rng = np.random.default_rng(20260926)
d = RU.load_data(False); a = RU.assignment("PRIMARY"); cov = d.cov
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
fits = {f: EN.collapse_for(d, sorted(a.index[a != f])) for f in range(5)}

def boot_mean(x, groups, n=2000, level=0.90):
    uniq, codes = np.unique(np.asarray(groups).astype(str), return_inverse=True); G = len(uniq); x = np.asarray(x, float)
    S, C = np.bincount(codes, x, G), np.bincount(codes, minlength=G).astype(float)
    W = rng.multinomial(G, np.full(G, 1 / G), size=n)
    m = (W @ S) / (W @ C); al = (1 - level) / 2 * 100
    return [float(v) for v in np.percentile(m, [al, 100 - al])]

res = {}
# (a) paired
both = cov.index[cov.measured_lcsb & cov.measured_wur]
wal = pd.read_csv(ROOT / "artifacts/wur_v2/data/wur_aligned_all.csv").pivot(index="group_key", columns="ce_numeric", values="mu").reindex(index=both, columns=E)
YL = d.Y.loc[both]; diff = wal - YL
grp = cov.loc[both, "scaffold_group"].to_numpy()
pa = {}
for e in E:
    x = diff[e].to_numpy(); ok = np.isfinite(x)
    ci = boot_mean(x[ok], grp[ok])
    pa[str(e)] = {"n": int(ok.sum()), "mean_diff": float(x[ok].mean()), "ci90": ci, "equivalent_within_0.02": bool(ci[0] > -TOL and ci[1] < TOL),
                  "sd_diff": float(x[ok].std(ddof=1))}
lg = {}
for k in both:
    f = fits[int(a.loc[k])]
    yl, yw = YL.loc[[k]].to_numpy(), wal.loc[[k]].to_numpy()
    lg[k] = (SC.fit_scale(f, E, yl)[0], SC.fit_scale(f, E, yw)[0])
dl = pd.Series({k: v[1] - v[0] for k, v in lg.items()})
mz = cov.loc[dl.index, "precursor_mz"]
X = np.column_stack([np.ones(len(dl)), (mz - mz.mean()) / 100.0]); beta, *_ = np.linalg.lstsq(X, dl.to_numpy(), rcond=None)
bs = []
codes = pd.factorize(cov.loc[dl.index, "scaffold_group"])[0]
for _ in range(2000):
    pick = rng.integers(0, codes.max() + 1, codes.max() + 1); idx = np.concatenate([np.where(codes == p)[0] for p in pick])
    b, *_ = np.linalg.lstsq(X[idx], dl.to_numpy()[idx], rcond=None); bs.append(b)
bs = np.array(bs)
res["a_paired_cross_instrument"] = {"per_rung_mu_WUR_minus_LCSB": pa, "logg_WUR_minus_LCSB_mean": float(dl.mean()),
    "logg_diff_intercept_ci90": np.percentile(bs[:, 0], [5, 95]).tolist(), "logg_diff_slope_per_100mz": float(beta[1]),
    "logg_diff_slope_ci90": np.percentile(bs[:, 1], [5, 95]).tolist(),
    "note": "bridge fitted on these compounds' median signed deltas, so a zero mean is partly by construction; the slope on mass is not"}
# (b) unpaired source effect in out-of-fold errors
Y = d.Y.loc[ta.pred.index].to_numpy(); P = ta.pred.to_numpy()
bias = pd.Series(np.nanmean(P - Y, axis=1), index=ta.pred.index)
rm = pd.Series(M.compound_rmse(M.errors(P, Y)), index=ta.pred.index)
c2 = cov.loc[bias.index]
src = (c2.primary_source == "WUR").astype(float).to_numpy(); m100 = ((c2.precursor_mz - c2.precursor_mz.mean()) / 100).to_numpy()
Xb = np.column_stack([np.ones(len(src)), src, m100, src * m100])
beta_b, *_ = np.linalg.lstsq(Xb, bias.to_numpy(), rcond=None)
codes = pd.factorize(c2.scaffold_group)[0]; G = codes.max() + 1; bb = []
groups_idx = [np.where(codes == g)[0] for g in range(G)]
for _ in range(1000):
    idx = np.concatenate([groups_idx[p] for p in rng.integers(0, G, G)])
    b, *_ = np.linalg.lstsq(Xb[idx], bias.to_numpy()[idx], rcond=None); bb.append(b)
bb = np.array(bb)
res["b_unpaired_source"] = {"model": "mean signed trajectory error ~ 1 + WUR + mass/100 + WUR x mass/100",
    "coef": dict(zip(["intercept", "WUR", "mass", "WUR_x_mass"], beta_b.tolist())),
    "ci90": {n: np.percentile(bb[:, i], [5, 95]).tolist() for i, n in enumerate(["intercept", "WUR", "mass", "WUR_x_mass"])},
    "WUR_effect_equivalent_within_0.02": bool(np.percentile(bb[:, 1], 5) > -TOL and np.percentile(bb[:, 1], 95) < TOL),
    "P1_by_source": {s: M.p1(M.errors(ta.pred.loc[c2.index[c2.primary_source == s]].to_numpy(), d.Y.loc[c2.index[c2.primary_source == s]].to_numpy())) for s in ("LCSB", "WUR")},
    "AF_by_source": {s: float((rm[c2.primary_source == s] > 0.2).mean()) for s in ("LCSB", "WUR")}}
# (c) adducts and operators
spec = pd.read_parquet(ROOT / "artifacts/wur_v2/data/wur_pos_spectra.parquet")
op = spec.groupby("connectivity_key").operator.agg(lambda s: ";".join(sorted(set(s))))
c2 = c2.assign(operator=op.reindex(c2.index).fillna("LCSB"))
strat = {}
for col in ("adduct", "operator"):
    for v, g in c2.groupby(col):
        ks = g.index
        strat[f"{col}={v}"] = {"n": int(len(ks)), "P1": M.p1(M.errors(ta.pred.loc[ks].to_numpy(), d.Y.loc[ks].to_numpy())),
                               "mean_bias": float(bias.loc[ks].mean()), "AF": float((rm.loc[ks] > 0.2).mean()),
                               "bias_ci90": boot_mean(bias.loc[ks].to_numpy(), c2.loc[ks, "scaffold_group"].to_numpy()) if len(ks) >= 8 else None}
res["c_strata"] = strat
# (d) native scoring for WUR-primary
A, B = bridge()
nat = pd.read_csv(ROOT / "artifacts/wur_v2/data/native_cells.csv")
wk = cov.index[cov.primary_source == "WUR"]
nw = nat[(nat.source == "WUR") & nat.connectivity_key.isin(wk)].pivot(index="connectivity_key", columns="ce_numeric", values="mu").reindex(index=wk)
native_E = np.array([15.0, 30.0, 45.0, 60.0, 75.0, 90.0])
pred_nat = np.vstack([EN.mu_from_log_g(fits[int(a.loc[k])], np.array([ta.log_g_pred.loc[k]]), (native_E - A) / B)[0] for k in wk])
Yn = nw[native_E].to_numpy()
u_min = {f: float(np.exp(fits[f].phi_u[0])) for f in fits}; u_max = {f: float(np.exp(fits[f].phi_u[-1])) for f in fits}
uu = np.vstack([((native_E - A) / B / 30.0) / np.exp(ta.log_g_pred.loc[k]) for k in wk])
outside = np.array([[(x < u_min[int(a.loc[k])]) or (x > u_max[int(a.loc[k])]) for x in row] for k, row in zip(wk, uu)])
res["d_native_vs_aligned_WUR_primary"] = {
    "P1_aligned_pooled_rungs": M.p1(M.errors(ta.pred.loc[wk].to_numpy(), d.Y.loc[wk].to_numpy())),
    "P1_native_30_90_map_inverted": M.p1(M.errors(pred_nat[:, 1:], Yn[:, 1:])),
    "P1_native_per_rung": {str(e): float(np.sqrt(np.nanmean((pred_nat[:, j] - Yn[:, j]) ** 2))) for j, e in enumerate(native_E)},
    "model_energy_for_native_rungs": dict(zip([str(e) for e in native_E], ((native_E - A) / B).round(2).tolist())),
    "fraction_cells_outside_profile_support": {str(e): float(outside[:, j].mean()) for j, e in enumerate(native_E)},
    "note": "native E15 maps to model energy 24.3, below the pooled 30-90 range; its prediction uses the training profile outside the energies the collapse saw for those compounds and is reported separately"}
(OUT / "exp05_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps(res, indent=1, default=lambda o: round(float(o), 4))[:6000])
LG.append({"experiment_id": "V2-EXP05-ACQUISITION-ION", "generation": "v2-G0", "parent_model": "TA_RIDGE (PRIMARY OOF), frozen map",
 "hypothesis": "Source, adduct and source x mass effects remain after the frozen bridge and could masquerade as missing chemistry.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "TIER_A", "endpoint": "aligned and native mu",
 "hyperparameters_and_space": "equivalence tolerance +/-0.02 mu", "tuning_process": "none", "results": res,
 "uncertainty": "scaffold-cluster bootstrap 90% intervals", "tail_metrics": {"AF_by_source": res["b_unpaired_source"]["AF_by_source"]},
 "interpretation": "see exp05_results.json; summarized in the v2 experiments report", "decision": "diagnostic",
 "reason": "decides between an acquisition adapter, ion-domain restriction, or chemistry representation", "informed_later_decisions": "trust domain flag; decision gate"})
