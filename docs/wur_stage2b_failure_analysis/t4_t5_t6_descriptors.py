from common import *
from muru.discovery.estimate import fit_collapse, _best_log_g, ENERGY_SCALE
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
import statsmodels.api as sm
out = {}
D = load('A_POOLED_ALIGNED'); long, cov, comp, gdf = D['long'], D['cov'], D['comp'], D['g']
cov = cov.merge(gdf[['group_key', 'g_hat', 'weight']], on='group_key'); cov['log_g'] = np.log(cov.g_hat)
# T4a Spearman per descriptor with in-sample log g
out['spearman_logg'] = {c: round(sp(cov[c], cov.log_g), 3) for c in FEATURES}
out['spearman_logg_by_source'] = {s: {c: round(sp(g[c], g.log_g), 3) for c in FEATURES} for s, g in cov.groupby('source')}
# T4b CV R2 on folds repeat 0, target = per-fold training collapse log g; held-out target = oracle log g under the training Phi (wide grid)
F = folds(); asg = F['repeats'][0]['assignment']; E = np.array([30., 45., 60., 75., 90.])
def feats_ext(c):
    X = X_of(c); names = list(FEATURES)
    logs = np.column_stack([np.log(c[k].to_numpy(float) + (1 if k in ('rotatable_bonds','ring_count','aromatic_ring_count','n_N','n_O','n_S','n_halogen') else 0.0)) for k in FEATURES]); 
    logs = np.where(np.isfinite(logs), logs, 0)
    inv_atoms = 1.0 / c['total_atom_count'].to_numpy(float); inv_mz = 1.0 / c['precursor_mz'].to_numpy(float)
    return np.column_stack([X, logs, inv_atoms * 37, inv_mz * 500])
models = {
 'ridge12': lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
 'ridge12_a10': lambda: make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
 'ridge_mass3': lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
 'ridge_nonmass9': lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
 'ridge_ext_log_inv': lambda: make_pipeline(StandardScaler(), Ridge(alpha=3.0)),
 'ridge_poly2': lambda: make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), StandardScaler(), Ridge(alpha=30.0)),
 'hgb': lambda: HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=3, min_samples_leaf=15, l2_regularization=1.0, random_state=0),
 'gbr_small': lambda: GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=2, subsample=0.8, random_state=0),
}
mass_idx = [FEATURES.index(c) for c in MASS_BLOCK]; nonmass_idx = [i for i in range(12) if i not in mass_idx]
rows = []; predstore = {}
S2A = json.load(open(f'{B2}/ledger/S2A_FROZEN_PIPELINE.json'))['folds']
def eval_expr(expr, c):
    env = {k: c[k].to_numpy(float) / SCALE[k] for k in FEATURES}
    env.update(dict(sqrt=np.sqrt, log=np.log, inv=lambda x: 1.0 / x, square=np.square, exp=np.exp))
    with np.errstate(all='ignore'): return eval(expr, {'__builtins__': {}}, env)
for f in range(5):
    tr = [k for k, v in asg.items() if v != f]; te = [k for k, v in asg.items() if v == f]
    fit = fit_collapse(long[long.group_key.isin(tr)], with_hmain=False)
    ctr = cov.set_index('group_key').loc[fit.compounds].reset_index(); ytr = np.log(fit.g_hat); wtr = fit.weights
    W = long[long.group_key.isin(te)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E)
    cte = cov.set_index('group_key').loc[W.index].reset_index()
    yte = _best_log_g(E, W.to_numpy(float), fit.phi_u, fit.phi_v, grid=np.linspace(-4, 4, 641))
    yte_frozen = _best_log_g(E, W.to_numpy(float), fit.phi_u, fit.phi_v)
    b0 = long[long.group_key.isin(tr)].groupby('ce_numeric').mu.mean().reindex(E).to_numpy()
    def mu_rmse(lg):
        u = (E/ENERGY_SCALE)[None, :]/np.exp(lg)[:, None]; P = phi_eval(fit.phi_u, fit.phi_v, u); return float(np.sqrt(np.nanmean((P - W.to_numpy(float))**2)))
    Xtr_full, Xte_full = feats_ext(ctr), feats_ext(cte); Xtr, Xte = X_of(ctr), X_of(cte)
    for name, mk in models.items():
        if name == 'ridge_mass3': A_, B_ = Xtr[:, mass_idx], Xte[:, mass_idx]
        elif name == 'ridge_nonmass9': A_, B_ = Xtr[:, nonmass_idx], Xte[:, nonmass_idx]
        elif name == 'ridge_ext_log_inv': A_, B_ = Xtr_full, Xte_full
        else: A_, B_ = Xtr, Xte
        m = mk(); 
        try: m.fit(A_, ytr, **({'ridge__sample_weight': wtr} if 'ridge' in name and 'poly' not in name else {}))
        except TypeError: m.fit(A_, ytr)
        p = m.predict(B_)
        r2 = 1 - np.sum((yte - p)**2)/np.sum((yte - yte.mean())**2); r2w = 1 - np.sum((yte_frozen - p)**2)/np.sum((yte_frozen - yte_frozen.mean())**2)
        rows.append(dict(fold=f, model=name, r2_logg_heldout=r2, r2_logg_frozen_target=r2w, spearman=sp(yte, p), mu_rmse=mu_rmse(p)))
        predstore[(f, name)] = p
    # S2A fold expression evaluated on this held-out fold (g scale: fit a multiplicative constant, i.e. intercept in log)
    ex = [d for d in S2A if d['repeat'] == 0 and d['fold'] == f][0]['diagnostics']['expr']
    ge = eval_expr(ex, cte); ok = np.isfinite(ge) & (ge > 0); lg = np.where(ok, np.log(np.where(ok, ge, 1)), 0.0)
    # as used in production: log(pred) directly (no rescale) and also with optimal intercept
    lg_c = lg - lg[ok].mean() + yte[ok].mean()
    rows.append(dict(fold=f, model='S2A_expr_raw', r2_logg_heldout=1 - np.sum((yte - lg)**2)/np.sum((yte - yte.mean())**2), r2_logg_frozen_target=np.nan, spearman=sp(yte, lg), mu_rmse=mu_rmse(lg)))
    rows.append(dict(fold=f, model='S2A_expr_recentred', r2_logg_heldout=1 - np.sum((yte - lg_c)**2)/np.sum((yte - yte.mean())**2), r2_logg_frozen_target=np.nan, spearman=sp(yte, lg_c), mu_rmse=mu_rmse(lg_c)))
    # what R2 is obtainable on g itself in training (in-sample ridge R2) - the selector's validation R2 is on g not log g
    m = Ridge(alpha=1.0).fit(StandardScaler().fit_transform(Xtr), ytr); 
    rows.append(dict(fold=f, model='_train_insample_ridge12', r2_logg_heldout=m.score(StandardScaler().fit_transform(Xtr), ytr), r2_logg_frozen_target=np.nan, spearman=np.nan, mu_rmse=np.nan))
    # oracle: variance of yte explained ceiling = 1; B0 and oracle mu rmse
    rows.append(dict(fold=f, model='_oracle_g', r2_logg_heldout=1.0, r2_logg_frozen_target=1.0, spearman=1.0, mu_rmse=mu_rmse(yte)))
    rows.append(dict(fold=f, model='_B0', r2_logg_heldout=0.0, r2_logg_frozen_target=0.0, spearman=0.0, mu_rmse=float(np.sqrt(np.nanmean((b0[None, :] - W.to_numpy(float))**2)))))
    # R2 on g (not log g), weighted, as the frozen selector scores it: compare ridge-on-log-g prediction exp(p) vs the expression
    gte = np.exp(yte); wte = np.ones(len(gte))
    for name in ['ridge12', 'hgb']:
        p = np.exp(predstore[(f, name)]); rows.append(dict(fold=f, model=f'_{name}_r2_on_g', r2_logg_heldout=1 - np.sum((gte-p)**2)/np.sum((gte-gte.mean())**2), r2_logg_frozen_target=np.nan, spearman=np.nan, mu_rmse=np.nan))
    p = np.where(ok, ge, 1.0); rows.append(dict(fold=f, model='_S2A_expr_r2_on_g', r2_logg_heldout=1 - np.sum((gte-p)**2)/np.sum((gte-gte.mean())**2), r2_logg_frozen_target=np.nan, spearman=np.nan, mu_rmse=np.nan))
R = pd.DataFrame(rows); R.to_csv(f'{S}/t4_cv_r2.csv', index=False)
summ = R.groupby('model')[['r2_logg_heldout', 'r2_logg_frozen_target', 'spearman', 'mu_rmse']].agg(['mean', 'std']).round(4)
print(summ); out['cv_repeat0'] = {m: {f'{a}_{b}': float(v) for (a, b), v in summ.loc[m].items()} for m in summ.index}
out['S2A_ledger_valid_r2_repeat0'] = [d['diagnostics']['valid_r2'] for d in S2A if d['repeat'] == 0]
out['S2A_ledger_P1_repeat0'] = [d['P1'] for d in S2A if d['repeat'] == 0]
out['LIN_ledger_P1_repeat0'] = [d['P1'] for d in json.load(open(f'{B2}/ledger/LIN_RIDGE_TIERA.json'))['folds'] if d['repeat'] == 0]
# ---- T4 global: in-sample fits on the full collapse (no CV) to bound the feature set
Xs = StandardScaler().fit_transform(X_of(cov)); y = cov.log_g.to_numpy()
out['insample_r2_ridge12_full'] = float(Ridge(alpha=1.0).fit(Xs, y).score(Xs, y))
out['insample_r2_hgb_full'] = float(models['hgb']().fit(X_of(cov), y).score(X_of(cov), y))
# residual variance in log g attributable to estimation noise: median g_var (variance of log g) vs total var
out['logg_var_total'] = float(y.var()); out['logg_est_var_median'] = float(gdf.g_var.median()); out['logg_est_var_mean'] = float(gdf.g_var.mean())
out['reliability_ceiling_R2_est_noise'] = float(1 - gdf.g_var.median()/y.var())
# ---- T5 selector ----
sel = D['sel']; bm = pd.DataFrame(sel['band_members_heldout']); rep = sel['selection']
out['T5'] = dict(n_band=len(bm), representative=rep['expr'], rep_valid_r2=rep.get('heldout_valid'), rep_test=rep.get('heldout_test'),
                 best_test_member=bm.loc[bm.test_r2_weighted.idxmax()].to_dict(), spearman_valid_test_w=sp(bm.valid_r2, bm.test_r2_weighted),
                 spearman_valid_test_unw=sp(bm.valid_r2, bm.test_r2_unweighted), spearman_complexity_test=sp(bm.complexity, bm.test_r2_weighted),
                 test_r2_quantiles=bm.test_r2_weighted.quantile([0, .25, .5, .75, 1]).round(3).tolist(), valid_r2_quantiles=bm.valid_r2.quantile([0, .25, .5, .75, 1]).round(3).tolist(),
                 n_members_test_gt_rep=int((bm.test_r2_weighted > sel['selection']['heldout_test']['r2_weighted']).sum()) if isinstance(rep.get('heldout_test'), dict) else None,
                 gate=rep.get('gate'))
bm.to_csv(f'{S}/t5_band_members_A.csv', index=False)
# structure census of 15 S2A fold expressions
import re
ex15 = [d['diagnostics']['expr'] for d in S2A]
cens = {v: sum(1 for e in ex15 if v in e) for v in FEATURES}
out['T5_fold_expr_variable_census'] = cens
out['T5_fold_expr_has_inv_atoms_or_mz'] = sum(1 for e in ex15 if re.search(r'/ *total_atom_count|inv\(total_atom_count\)|/ *precursor_mz|inv\(precursor_mz\)|/ *\(\(\(rotatable_bonds \* precursor_mz', e))
out['T5_fold_expr_has_ring'] = sum(1 for e in ex15 if 'ring_count' in e); out['T5_fold_expr_has_het'] = sum(1 for e in ex15 if 'heteroatom_fraction' in e)
# a 'stable law' test: fit the canonical form  g = c * sqrt(ring + 1/het) / atoms  and g = c*log(arom+1.5)/mz on each held-out fold and get R2, plus a 3-term linear model in log space
rows = []
for f in range(5):
    tr = [k for k, v in asg.items() if v != f]; te = [k for k, v in asg.items() if v == f]
    fit = fit_collapse(long[long.group_key.isin(tr)], with_hmain=False)
    ctr = cov.set_index('group_key').loc[fit.compounds].reset_index(); ytr = np.log(fit.g_hat)
    W = long[long.group_key.isin(te)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E); cte = cov.set_index('group_key').loc[W.index].reset_index()
    yte = _best_log_g(E, W.to_numpy(float), fit.phi_u, fit.phi_v, grid=np.linspace(-4, 4, 641))
    def canon(c):
        return np.column_stack([np.log(np.sqrt(c.ring_count + 1/c.heteroatom_fraction)), np.log(c.total_atom_count), np.log(c.precursor_mz), np.log(c.aromatic_ring_count + 1.5), np.log(c.rdbe.clip(lower=0.5)), c.heteroatom_fraction])
    for name, cols in [('law_sqrt_ring_het_over_atoms', [0, 1]), ('law_log_arom_over_mz', [3, 2]), ('law_both_4', [0, 1, 3, 2]), ('law_all6_loglinear', [0, 1, 2, 3, 4, 5])]:
        m = Ridge(alpha=0.01).fit(canon(ctr)[:, cols], ytr); p = m.predict(canon(cte)[:, cols])
        rows.append(dict(fold=f, model=name, r2=1 - np.sum((yte-p)**2)/np.sum((yte-yte.mean())**2), coefs=np.round(m.coef_, 3).tolist()))
Lw = pd.DataFrame(rows); out['T5_stable_law_cv'] = Lw.groupby('model').r2.agg(['mean', 'std']).round(4).to_dict('index'); out['T5_stable_law_coefs'] = Lw.groupby('model').coefs.apply(list).to_dict()
# ---- T6 source effects in A ----
Xs = sm.add_constant(np.column_stack([StandardScaler().fit_transform(X_of(cov)), (cov.source == 'WUR').astype(float)]))
ols = sm.OLS(cov.log_g, Xs).fit(); 
out['T6_logg_source_coef'] = dict(coef=float(np.asarray(ols.params)[-1]), se=float(np.asarray(ols.bse)[-1]), p=float(np.asarray(ols.pvalues)[-1]), r2_with=float(ols.rsquared), r2_without=float(sm.OLS(cov.log_g, Xs[:, :-1]).fit().rsquared))
out['T6_logg_by_source_raw'] = cov.groupby('source').log_g.agg(['mean', 'median', 'std']).round(3).to_dict('index')
# residual by source per energy, controlling for descriptors: residual res = mu - Phi(u) from the full collapse; regress on descriptors + source per energy
ku, kv = np.array(D['collapse']['phi_u']), np.array(D['collapse']['phi_v'])
L = long.drop(columns=['source']).merge(cov, on='group_key'); L['res'] = L.mu - phi_eval(ku, kv, (L.ce_numeric/ENERGY_SCALE)/L.g_hat)
t6 = {}
for e, g in L.groupby('ce_numeric'):
    Xe = sm.add_constant(np.column_stack([StandardScaler().fit_transform(X_of(g)), (g.source == 'WUR').astype(float)]))
    m = sm.OLS(g.res, Xe).fit(); t6[str(e)] = dict(source_coef=round(float(np.asarray(m.params)[-1]), 4), p=round(float(np.asarray(m.pvalues)[-1]), 4), raw_diff=round(float(g[g.source=='WUR'].res.mean() - g[g.source=='LCSB'].res.mean()), 4))
out['T6_residual_source_effect_per_energy'] = t6
# sign of residual: logistic
Xs2 = np.column_stack([StandardScaler().fit_transform(X_of(L)), (L.source == 'WUR').astype(float)]); lr = LogisticRegression(max_iter=2000).fit(Xs2, (L.res > 0).astype(int))
out['T6_resid_sign_logit_source_coef'] = float(lr.coef_[0, -1]); 
# per-compound tilt (slope of residual in log E) by source
w = L.pivot_table(index='group_key', columns='ce_numeric', values='res'); lE = np.log(w.columns.to_numpy(float)); lE -= lE.mean()
tilt = (w.sub(w.mean(1), axis=0) * lE).sum(1)/(lE**2).sum(); tilt = tilt.to_frame('tilt').join(cov.set_index('group_key')[['source'] + list(FEATURES)])
out['T6_tilt_by_source'] = tilt.groupby('source').tilt.agg(['mean', 'std']).round(4).to_dict('index')
Xt = sm.add_constant(np.column_stack([StandardScaler().fit_transform(X_of(tilt)), (tilt.source == 'WUR').astype(float)])); mt = sm.OLS(tilt.tilt, Xt).fit()
out['T6_tilt_source_coef_controlled'] = dict(coef=float(np.asarray(mt.params)[-1]), p=float(np.asarray(mt.pvalues)[-1]), r2_desc_for_tilt=float(sm.OLS(tilt.tilt, Xt[:, :-1]).fit().rsquared))
out['T6_tilt_spearman_desc'] = {c: round(sp(tilt.tilt, tilt[c]), 3) for c in FEATURES}
out['T6_tilt_sd'] = float(tilt.tilt.std())
# does the 124-key overlap (LCSB copy kept) matter: WUR-native vs LCSB-native g for the same keys
gB = load('B_WUR_NATIVE')['g'].set_index('group_key').g_hat; gC = load('C_LCSB_NATIVE')['g'].set_index('group_key').g_hat
common = gB.index.intersection(gC.index); out['T6_overlap_n'] = len(common)
out['T6_overlap_logg_corr_B_vs_C'] = float(np.corrcoef(np.log(gB.loc[common]), np.log(gC.loc[common]))[0, 1]); out['T6_overlap_logg_spearman'] = sp(np.log(gB.loc[common]), np.log(gC.loc[common]))
out['T6_overlap_logg_diff_sd'] = float((np.log(gB.loc[common]) - np.log(gC.loc[common])).std()); out['T6_overlap_logg_diff_mean'] = float((np.log(gB.loc[common]) - np.log(gC.loc[common])).mean())
json.dump(out, open(f'{S}/t4_t5_t6_results.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in out.items() if k != 'cv_repeat0'}, indent=1, default=float))
