from common import *
from muru.discovery.estimate import fit_collapse, _best_log_g, ENERGY_SCALE
from scipy.interpolate import PchipInterpolator
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
fw = pd.read_csv(f'{B2}/features_wur.csv'); fl = pd.read_csv(f'{B2}/features_lcsb.csv'); A, B = -5.9555, 0.8618; E5 = np.array([30., 45., 60., 75., 90.]); TE = A + B * E5
D = load('A_POOLED_ALIGNED'); LA = D['long']; wk = set(LA[LA.source == 'WUR'].group_key); lk = set(LA[LA.source == 'LCSB'].group_key); cov = D['cov']
out = {}
for s in ['survival_yield', 'mu', 'frac_x_ge_075']:
    rows = []
    for k, g in fw.groupby('connectivity_key'):
        if k not in wk: continue
        g = g.sort_values('ce_numeric'); v = g[s].to_numpy(float)
        if not np.isfinite(v).all(): continue
        rows += [dict(group_key=k, ce_numeric=e, mu=x) for e, x in zip(E5, PchipInterpolator(g.ce_numeric, v)(TE))]
    for k, g in fl.groupby('connectivity_key'):
        if k not in lk: continue
        g = g[g.ce_numeric.isin(E5)]; rows += [dict(group_key=k, ce_numeric=e, mu=x) for e, x in zip(g.ce_numeric, g[s]) if np.isfinite(x)]
    L = pd.DataFrame(rows); W = L.pivot_table(index='group_key', columns='ce_numeric', values='mu')
    r = dict(frac_all_rungs_lt_0p05=float((W.max(1) < 0.05).mean()), frac_all_rungs_lt_0p1=float((W.max(1) < 0.1).mean()), frac_range_lt_0p1=float(((W.max(1) - W.min(1)) < 0.1).mean()), frac_first_rung_lt_0p2=float((W.iloc[:, 0] < 0.2).mean()), frac_first_rung_gt_0p9=float((W.iloc[:, 0] > 0.9).mean()), median_traj=W.median().round(3).tolist())
    fit = fit_collapse(L, with_hmain=False); lg = np.log(fit.g_hat)
    r['logg_quantiles'] = np.quantile(lg, [0, .05, .25, .5, .75, .95, 1]).round(2).tolist(); r['median_g_var'] = float(np.median(fit.g_var)); r['frac_g_var_gt_1'] = float((fit.g_var > 1).mean())
    r['reliability_R2_ceiling'] = float(1 - np.median(fit.g_var) / lg.var())
    # descriptor predictability: in-sample ridge R2 (weighted and unweighted) and Spearman
    c = cov.set_index('group_key').loc[fit.compounds]; X = StandardScaler().fit_transform(X_of(c))
    r['insample_ridge_r2_unw'] = float(Ridge(1.0).fit(X, lg).score(X, lg)); r['insample_ridge_r2_w'] = float(Ridge(1.0).fit(X, lg, sample_weight=fit.weights).score(X, lg, sample_weight=fit.weights))
    r['spearman_logg_vs_mz'] = sp(lg, c.precursor_mz); r['spearman_logg_vs_atoms'] = sp(lg, c.total_atom_count)
    # restrict to well-identified compounds (g_var < median): CV-free in-sample R2
    ok = fit.g_var < np.median(fit.g_var); r['insample_ridge_r2_wellidentified_half'] = float(Ridge(1.0).fit(X[ok], lg[ok]).score(X[ok], lg[ok]))
    out[s] = r; print(s, json.dumps(r, default=float))
json.dump(out, open(f'{S}/t8b_results.json', 'w'), indent=1, default=float)
