from common import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from muru.discovery.estimate import fit_collapse, _best_log_g, _fit_phi, ENERGY_SCALE, LOG_G_GRID
out = {}
fig, axes = plt.subplots(3, 3, figsize=(15, 11))
for ai, an in enumerate(['A_POOLED_ALIGNED', 'B_WUR_NATIVE', 'C_LCSB_NATIVE']):
    D = load(an); L = D['long'].merge(D['g'][['group_key','g_hat']], on='group_key').merge(D['cov'][['group_key','precursor_mz']], on='group_key')
    ku, kv = np.array(D['collapse']['phi_u']), np.array(D['collapse']['phi_v'])
    L['u'] = (L.ce_numeric/ENERGY_SCALE)/L.g_hat; L['pred'] = phi_eval(ku, kv, L.u.values); L['res'] = L.mu - L.pred
    L['g_terc'] = pd.qcut(L.g_hat, 3, labels=['g_lo','g_mid','g_hi']); L['m_terc'] = pd.qcut(L.precursor_mz, 3, labels=['m_lo','m_mid','m_hi'])
    r = {}
    r['resid_sd_all'] = float(L.res.std()); r['resid_sd_over_repeat'] = float(L.res.std()/REPEAT_SD)
    r['by_energy'] = L.groupby('ce_numeric').res.agg(['mean','std','count']).round(4).to_dict('index')
    r['by_source'] = L.groupby('source').res.agg(['mean','std','count']).round(4).to_dict('index')
    r['by_energy_source_mean'] = L.pivot_table(index='ce_numeric', columns='source', values='res', aggfunc='mean').round(4).to_dict()
    r['by_energy_gterc_mean'] = L.pivot_table(index='ce_numeric', columns='g_terc', values='res', aggfunc='mean', observed=True).round(4).to_dict()
    r['by_energy_gterc_sd'] = L.pivot_table(index='ce_numeric', columns='g_terc', values='res', aggfunc='std', observed=True).round(4).to_dict()
    r['by_energy_mterc_mean'] = L.pivot_table(index='ce_numeric', columns='m_terc', values='res', aggfunc='mean', observed=True).round(4).to_dict()
    # systematic vs random: per-compound mean residual (systematic) vs within-compound deviation
    pc = L.groupby('group_key').res.agg(['mean','std'])
    r['between_compound_sd_of_mean_resid'] = float(pc['mean'].std()); r['within_compound_resid_sd'] = float(np.sqrt((L.groupby('group_key').res.var()).mean()))
    # residual vs u (position along the profile): binned by u
    L['lu_bin'] = pd.cut(np.log(L.u), bins=[-5,-2,-1.5,-1,-0.5,0,0.5,1,1.5,2,5])
    r['by_logu_bin'] = L.groupby('lu_bin', observed=True).res.agg(['mean','std','count']).round(4).reset_index().astype({'lu_bin':str}).to_dict('records')
    # signed pattern: residual at lowest E vs highest E within compound, correlation (shape mismatch signature)
    w = L.pivot_table(index='group_key', columns='ce_numeric', values='res')
    r['corr_res_lowE_highE'] = float(w.iloc[:, 0].corr(w.iloc[:, -1]))
    r['corr_res_lowE_midE'] = float(w.iloc[:, 0].corr(w.iloc[:, len(w.columns)//2]))
    # fraction of residual variance that is a per-compound linear-in-logE trend
    lE = np.log(w.columns.to_numpy(float)); lE = lE - lE.mean()
    slopes = (w.sub(w.mean(1), axis=0) * lE).sum(1)/ (lE**2).sum()
    fitted = np.outer(slopes, lE) + w.mean(1).values[:, None]
    tot = np.nansum((w.values)**2); expl = np.nansum((np.where(np.isfinite(w.values), fitted, 0))**2)
    r['frac_resid_ss_explained_by_compound_mean_plus_logE_slope'] = float(expl/tot)
    r['frac_resid_ss_explained_by_compound_mean_only'] = float(np.nansum(np.where(np.isfinite(w.values), w.mean(1).values[:, None], 0)**2)/tot)
    out[an] = r
    ax = axes[ai, 0]; 
    for s, g in L.groupby('source'): ax.plot(g.groupby('ce_numeric').res.mean(), 'o-', label=s)
    ax.axhline(0, c='k', lw=.5); ax.set_title(f'{an}: mean residual by E and source'); ax.legend()
    ax = axes[ai, 1]
    for t, g in L.groupby('g_terc', observed=True): ax.plot(g.groupby('ce_numeric').res.mean(), 'o-', label=str(t))
    ax.axhline(0, c='k', lw=.5); ax.set_title('mean residual by E and g tercile'); ax.legend()
    ax = axes[ai, 2]; ax.scatter(np.log(L.u), L.res, s=2, alpha=.2); ax.axhline(0, c='k', lw=.5); ax.set_title('residual vs log u'); ax.set_xlabel('log u')
plt.tight_layout(); plt.savefig(f'{S}/t1_residuals.png', dpi=110)

# ---- decomposition of S1 per-energy held-out error: oracle g vs predicted g (repeat 0 folds) ----
from sklearn.linear_model import Ridge
D = load('A_POOLED_ALIGNED'); long, cov, frame = D['long'], D['cov'], D['comp']
F = folds(); asg = F['repeats'][0]['assignment']
E = np.array([30., 45., 60., 75., 90.])
dec = {}
rows = []
for f in range(5):
    tr_keys = [k for k, v in asg.items() if v != f]; te_keys = [k for k, v in asg.items() if v == f]
    ltr = long[long.group_key.isin(tr_keys)]; fit = fit_collapse(ltr, with_hmain=False)
    W = long[long.group_key.isin(te_keys)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E)
    keys = W.index.to_numpy(); Y = W.to_numpy(float)
    # oracle g (own spectra, training Phi), on the frozen grid and on a wide grid
    lg_or = _best_log_g(E, Y, fit.phi_u, fit.phi_v)
    lg_or_wide = _best_log_g(E, Y, fit.phi_u, fit.phi_v, grid=np.linspace(-4, 4, 641))
    # oracle free shape exponent (per-compound p) with wide g grid
    best = np.full(len(keys), np.inf); pred_fs = np.zeros_like(Y); 
    for p in np.linspace(0.5, 3.0, 11):
        for lg in np.linspace(-4, 4, 161):
            uu = ((E/ENERGY_SCALE)/np.exp(lg))**p; pr = phi_eval(fit.phi_u, fit.phi_v, uu)
            sse = np.nansum((Y - pr[None, :])**2, 1); take = sse < best; best = np.where(take, sse, best); pred_fs[take] = pr[None, :]
    # predicted g: ridge (alpha 1) on training in-sample log g
    ctr = cov.set_index('group_key').loc[fit.compounds]; cte = cov.set_index('group_key').loc[keys]
    m = Ridge(alpha=1.0).fit(X_of(ctr), np.log(fit.g_hat), sample_weight=fit.weights); lg_pr = m.predict(X_of(cte))
    b0 = ltr.groupby('ce_numeric').mu.mean().reindex(E).to_numpy()
    def pe(lg): 
        u = (E/ENERGY_SCALE)[None, :]/np.exp(lg)[:, None]; return phi_eval(fit.phi_u, fit.phi_v, u)
    preds = {'B0': np.tile(b0, (len(keys), 1)), 'ridge_g': pe(lg_pr), 'oracle_g_frozen_grid': pe(lg_or), 'oracle_g_wide_grid': pe(lg_or_wide), 'oracle_g_and_shape': pred_fs}
    for name, P in preds.items():
        d = P - Y
        rows.append(dict(fold=f, arm=name, P1=float(np.sqrt(np.nanmean(d**2))), **{f'E{int(e)}': float(np.sqrt(np.nanmean(d[:, j]**2))) for j, e in enumerate(E)}))
    # variance of log g prediction error
    rows.append(dict(fold=f, arm='_loggerr_sd_ridge_vs_oracle', P1=float(np.std(lg_pr - lg_or_wide)), E30=float(np.corrcoef(lg_pr, lg_or_wide)[0,1])))
    rows.append(dict(fold=f, arm='_loggerr_sd_oracle_frozen_vs_wide', P1=float(np.std(lg_or - lg_or_wide)), E30=float(np.mean(np.abs(lg_or) > 1.59))))
df = pd.DataFrame(rows); df.to_csv(f'{S}/t1_s1_decomposition.csv', index=False)
summ = df[~df.arm.str.startswith('_')].groupby('arm')[['P1','E30','E45','E60','E75','E90']].mean().round(4)
print(summ); out['s1_decomposition_mean_over_folds_repeat0'] = summ.to_dict('index')
out['loggerr'] = df[df.arm.str.startswith('_')].groupby('arm')[['P1','E30']].mean().round(4).to_dict('index')
# fraction of held-out (ridge) MSE at each energy attributable to profile shape (oracle g) vs g prediction
sq = summ**2
out['s1_share_of_ridge_mse_from_shape_oracle_g_wide'] = (sq.loc['oracle_g_wide_grid']/sq.loc['ridge_g']).round(3).to_dict()
out['s1_share_of_ridge_mse_from_shape_oracle_g_and_shape'] = (sq.loc['oracle_g_and_shape']/sq.loc['ridge_g']).round(3).to_dict()
json.dump(out, open(f'{S}/t1_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in out.items() if k != 's1_decomposition_mean_over_folds_repeat0'}, indent=1, default=float))
