from common import *
from muru.discovery.estimate import fit_collapse, _best_log_g, ENERGY_SCALE
from scipy.interpolate import PchipInterpolator
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
out = {}
fw = pd.read_csv(f'{B2}/features_wur.csv'); fl = pd.read_csv(f'{B2}/features_lcsb.csv')
SUMS = ["mu", "survival_yield", "fragment_depth", "spectral_entropy", "normalized_entropy", "peak_count", "base_peak_fraction", "x_wsd", "x_wq25", "x_wq50", "x_wq75", "frac_x_lt_025", "frac_x_025_050", "frac_x_050_075", "frac_x_ge_075", "n_peaks_1pct", "log_tic"]
A, B = -5.9555, 0.8618; E5 = np.array([30., 45., 60., 75., 90.]); TE = A + B * E5
# (0) interface check: A's WUR mu at pooled rungs vs PCHIP of features_wur mu at T(E)
D = load('A_POOLED_ALIGNED'); LA = D['long']; wurA = LA[LA.source == 'WUR']
chk = []
for k, g in fw.groupby('connectivity_key'):
    if k not in set(wurA.group_key): continue
    g = g.sort_values('ce_numeric'); p = PchipInterpolator(g.ce_numeric, g.mu)(TE)
    a = wurA[wurA.group_key == k].set_index('ce_numeric').mu.reindex(E5).to_numpy()
    chk.append(np.nanmax(np.abs(p - a)))
out['interface_check_A_vs_pchip_features_wur'] = dict(n=len(chk), max_abs_diff=float(np.max(chk)), median_abs_diff=float(np.median(chk)))
lcA = LA[LA.source == 'LCSB']; chk2 = []
for k, g in fl.groupby('connectivity_key'):
    if k not in set(lcA.group_key): continue
    a = lcA[lcA.group_key == k].set_index('ce_numeric').mu.reindex(E5); b = g.set_index('ce_numeric').mu.reindex(E5)
    chk2.append(np.nanmax(np.abs(a - b)))
out['interface_check_A_vs_features_lcsb'] = dict(n=len(chk2), max_abs_diff=float(np.nanmax(chk2)))
# (i) monotonicity and smoothness per summary, per corpus (native axes)
def mono_smooth(f, name):
    res = {}
    for s in SUMS:
        W = f.pivot_table(index='connectivity_key', columns='ce_numeric', values=s)
        v = W.to_numpy(float); ok = np.isfinite(v).all(1); v = v[ok]
        E = np.log(W.columns.to_numpy(float))
        rho = np.array([sp(E, r) for r in v]); rng = np.nanmedian(v.max(1) - v.min(1))
        # roughness: RMS second difference relative to trajectory range (per compound), median
        d2 = np.diff(v, 2, axis=1); rough = np.sqrt((d2**2).mean(1)) / np.maximum(v.max(1) - v.min(1), 1e-9)
        # fraction of strictly monotone trajectories
        dm = np.diff(v, axis=1); fm = float(np.mean((dm <= 0).all(1) | (dm >= 0).all(1)))
        # spread across compounds relative to range within (signal to noise proxy)
        res[s] = dict(n=int(ok.sum()), median_abs_spearman_E=float(np.nanmedian(np.abs(rho))), frac_monotone=fm, median_roughness=float(np.median(rough)), median_range=float(rng), pop_sd=float(np.nanstd(v)))
    return res
out['mono_smooth_wur'] = mono_smooth(fw, 'wur'); out['mono_smooth_lcsb'] = mono_smooth(fl, 'lcsb')
# (ii) collapse under a shared shape per summary, pooled aligned world (WUR read at T(E) by PCHIP), rungs 30..90
def pooled_long_for(s):
    rows = []
    for k, g in fw.groupby('connectivity_key'):
        if k not in set(wurA.group_key): continue
        g = g.sort_values('ce_numeric'); v = g[s].to_numpy(float)
        if not np.isfinite(v).all(): continue
        p = PchipInterpolator(g.ce_numeric, v)(TE)
        rows += [dict(group_key=k, ce_numeric=e, mu=x, source='WUR') for e, x in zip(E5, p)]
    for k, g in fl.groupby('connectivity_key'):
        if k not in set(lcA.group_key): continue
        g = g[g.ce_numeric.isin(E5)]
        rows += [dict(group_key=k, ce_numeric=e, mu=x, source='LCSB') for e, x in zip(g.ce_numeric, g[s]) if np.isfinite(x)]
    return pd.DataFrame(rows)
cov = D['cov']; F = folds(); asg = F['repeats'][0]['assignment']
coll = {}; gstore = {}
for s in ['mu', 'survival_yield', 'fragment_depth', 'spectral_entropy', 'normalized_entropy', 'base_peak_fraction', 'x_wq50', 'frac_x_ge_075', 'peak_count', 'log_tic']:
    L = pooled_long_for(s)
    # decreasing-in-E orientation: flip increasing summaries
    W = L.pivot_table(index='group_key', columns='ce_numeric', values='mu'); rho = np.nanmedian([sp(np.log(E5), r) for r in W.to_numpy(float) if np.isfinite(r).all()])
    sign = -1.0 if rho > 0 else 1.0; L2 = L.copy(); L2['mu'] = sign * L2.mu
    # scale to [0,1]-ish range for comparability: divide by population range
    rng = float(np.nanpercentile(L2.mu, 99) - np.nanpercentile(L2.mu, 1)); L2['mu'] = (L2.mu - np.nanpercentile(L2.mu, 1)) / rng
    fit = fit_collapse(L2, with_hmain=True)
    hm = fit.hmain
    coll[s] = dict(n=len(fit.compounds), orientation_sign=sign, resid_sd_scaled=float(fit.resid_sd), collapse_loeo_rmse_scaled=hm['collapse_loeo_rmse'], free_shape_loeo_rmse_scaled=hm['free_shape_loeo_rmse'], hmain_ratio=hm['ratio'], hmain_ci=hm['ci'], rejected=hm['h_main_rejected'], sd_log_g=float(np.log(fit.g_hat).std()), frac_edge=float((np.abs(np.log(fit.g_hat)) > 1.59).mean()), pop_range_used=rng)
    # signal-to-noise: between-compound spread of trajectories (scaled) vs resid
    coll[s]['total_sd_scaled'] = float(L2.mu.std()); coll[s]['frac_var_explained_by_collapse'] = float(1 - fit.resid_sd**2 / L2.mu.var())
    gstore[s] = (L2, fit)
    # (iii) CV ridge R2 of log g from descriptors, folds repeat 0, target from per-fold training collapse; held-out oracle g under training Phi
    r2s = []; mu_rmse = []
    for f in range(5):
        tr = [k for k, v in asg.items() if v != f]; te = [k for k, v in asg.items() if v == f]
        ff = fit_collapse(L2[L2.group_key.isin(tr)], with_hmain=False)
        ctr = cov.set_index('group_key').loc[ff.compounds]; Wt = L2[L2.group_key.isin(te)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E5)
        cte = cov.set_index('group_key').loc[Wt.index]
        yte = _best_log_g(E5, Wt.to_numpy(float), ff.phi_u, ff.phi_v, grid=np.linspace(-4, 4, 641))
        sc = StandardScaler().fit(X_of(ctr)); m = Ridge(alpha=1.0).fit(sc.transform(X_of(ctr)), np.log(ff.g_hat), sample_weight=ff.weights); p = m.predict(sc.transform(X_of(cte)))
        r2s.append(1 - np.sum((yte-p)**2)/np.sum((yte-yte.mean())**2))
        P = phi_eval(ff.phi_u, ff.phi_v, (E5/ENERGY_SCALE)[None, :]/np.exp(p)[:, None]); mu_rmse.append(float(np.sqrt(np.nanmean((P - Wt.to_numpy(float))**2))))
    coll[s]['cv_ridge_r2_logg'] = float(np.mean(r2s)); coll[s]['cv_ridge_r2_sd'] = float(np.std(r2s)); coll[s]['cv_heldout_rmse_scaled'] = float(np.mean(mu_rmse))
    coll[s]['cv_heldout_rmse_over_total_sd'] = float(np.mean(mu_rmse) / L2.mu.std())
    print(s, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in coll[s].items()}, flush=True)
out['collapse_by_summary'] = coll
# cross-summary g agreement
gm = {s: pd.Series(np.log(f.g_hat), index=f.compounds) for s, (L2, f) in gstore.items()}
out['logg_corr_between_summaries'] = {s: round(float(gm['mu'].corr(gm[s])), 3) for s in gm}
# (iv) cross-corpus consistency for overlapping keys after T(E)
common = sorted(set(fw.connectivity_key) & set(fl.connectivity_key)); out['n_overlap_keys'] = len(common)
cc = {}
for s in SUMS:
    d = []; 
    for k in common:
        g = fw[fw.connectivity_key == k].sort_values('ce_numeric'); h = fl[fl.connectivity_key == k].set_index('ce_numeric')[s].reindex(E5)
        v = g[s].to_numpy(float)
        if not np.isfinite(v).all() or h.isna().any(): continue
        p = PchipInterpolator(g.ce_numeric, v)(TE); d.append(np.column_stack([p, h.to_numpy(), E5]))
    if not d: continue
    d = np.vstack(d); x, y = d[:, 0], d[:, 1]
    sdpop = np.nanstd(np.concatenate([fw[s].to_numpy(float), fl[s].to_numpy(float)]))
    cc[s] = dict(n_pairs=len(d), n_keys=len(d)//5, pearson=float(np.corrcoef(x, y)[0, 1]), spearman=sp(x, y), mean_diff_wur_minus_lcsb=float((x-y).mean()), rmsd=float(np.sqrt(((x-y)**2).mean())), rmsd_over_pop_sd=float(np.sqrt(((x-y)**2).mean())/sdpop),
                 per_energy_mean_diff={str(int(e)): round(float((x-y)[d[:, 2] == e].mean()), 4) for e in E5}, per_energy_corr={str(int(e)): round(float(np.corrcoef(x[d[:, 2]==e], y[d[:, 2]==e])[0, 1]), 3) for e in E5})
out['cross_corpus'] = cc
json.dump(out, open(f'{S}/t8_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in out.items() if k not in ('collapse_by_summary',)}, indent=1, default=float))
