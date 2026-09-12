from common import *
from muru.discovery.estimate import fit_collapse, _best_log_g, ENERGY_SCALE
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
D = load('A_POOLED_ALIGNED'); long, cov = D['long'], D['cov']
F = folds(); E = np.array([30., 45., 60., 75., 90.]); Es = E / ENERGY_SCALE
rows = []
def hgb(): return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=3, min_samples_leaf=15, l2_regularization=1.0, random_state=0)
for rep in range(3):
    asg = F['repeats'][rep]['assignment']
    for f in range(5):
        tr = [k for k, v in asg.items() if v != f]; te = [k for k, v in asg.items() if v == f]
        Ltr = long[long.group_key.isin(tr)]; fit = fit_collapse(Ltr, with_hmain=False)
        Wtr = Ltr.pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E); Wte = long[long.group_key.isin(te)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E)
        ctr = cov.set_index('group_key').loc[Wtr.index]; cte = cov.set_index('group_key').loc[Wte.index]
        sc = StandardScaler().fit(X_of(ctr)); Xtr, Xte = sc.transform(X_of(ctr)), sc.transform(X_of(cte)); Ytr, Yte = Wtr.to_numpy(float), Wte.to_numpy(float)
        b0 = np.nanmean(Ytr, 0)
        def score(name, P):
            d = P - Yte; rc = np.sqrt(np.nanmean(d**2, 1)); rb = np.sqrt(np.nanmean((b0[None, :] - Yte)**2, 1))
            rows.append(dict(rep=rep, fold=f, arm=name, P1=float(np.sqrt(np.nanmean(d**2))), S2=float(np.mean(rc <= 0.9 * rb)), S4=float(np.mean(rc > 2 * rb)), **{f'E{int(e)}': float(np.sqrt(np.nanmean(d[:, j]**2))) for j, e in enumerate(E)}))
        score('B0', np.tile(b0, (len(Yte), 1)))
        # direct per-energy ridge (impute missing training cells by row-wise interpolation is unnecessary: drop NaN rows per energy)
        P = np.zeros_like(Yte)
        for j in range(5):
            ok = np.isfinite(Ytr[:, j]); m = Ridge(alpha=1.0).fit(Xtr[ok], Ytr[ok, j]); P[:, j] = m.predict(Xte)
        score('direct_ridge_per_energy', np.clip(P, 0, 1))
        P = np.zeros_like(Yte)
        for j in range(5):
            ok = np.isfinite(Ytr[:, j]); m = hgb().fit(Xtr[ok], Ytr[ok, j]); P[:, j] = m.predict(Xte)
        score('direct_hgb_per_energy', np.clip(P, 0, 1))
        # collapse + ridge g
        lgtr = np.log(fit.g_hat); ctr2 = cov.set_index('group_key').loc[fit.compounds]; Xtr2 = sc.transform(X_of(ctr2))
        m = Ridge(alpha=1.0).fit(Xtr2, lgtr, sample_weight=fit.weights); lg = m.predict(Xte)
        score('collapse_ridge_g', phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(lg)[:, None]))
        mh = hgb().fit(Xtr2, lgtr); lgh = mh.predict(Xte)
        score('collapse_hgb_g', phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(lgh)[:, None]))
        # collapse + per-compound shape exponent p (training: fit (g,p) per compound against training Phi; predict both by ridge)
        pg = np.linspace(0.4, 3.0, 27); lgg = np.linspace(-4, 4, 161)
        def fit_gp(Y):
            best = np.full(len(Y), np.inf); bg = np.zeros(len(Y)); bp = np.ones(len(Y))
            for p in pg:
                for l in lgg:
                    pr = phi_eval(fit.phi_u, fit.phi_v, (Es / np.exp(l))**p); sse = np.nansum((Y - pr[None, :])**2, 1); t = sse < best; best[t] = sse[t]; bg[t] = l; bp[t] = p
            return bg, bp
        gtr, ptr = fit_gp(Ytr); gte_or, pte_or = fit_gp(Yte)
        mg = Ridge(alpha=1.0).fit(Xtr, gtr); mp = Ridge(alpha=1.0).fit(Xtr, np.log(ptr))
        lg2, lp2 = mg.predict(Xte), np.exp(mp.predict(Xte))
        score('collapse_gp_ridge_both', phi_eval(fit.phi_u, fit.phi_v, (Es[None, :] / np.exp(lg2)[:, None])**lp2[:, None]))
        score('collapse_gp_ridge_g_oracle_p', phi_eval(fit.phi_u, fit.phi_v, (Es[None, :] / np.exp(lg2)[:, None])**pte_or[:, None]))
        score('collapse_gp_oracle_g_ridge_p', phi_eval(fit.phi_u, fit.phi_v, (Es[None, :] / np.exp(gte_or)[:, None])**lp2[:, None]))
        score('collapse_gp_oracle_both', phi_eval(fit.phi_u, fit.phi_v, (Es[None, :] / np.exp(gte_or)[:, None])**pte_or[:, None]))
        score('collapse_oracle_g_only', phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(_best_log_g(E, Yte, fit.phi_u, fit.phi_v, grid=lgg))[:, None]))
        if rep == 0:
            rows.append(dict(rep=rep, fold=f, arm='_r2_logp_ridge', P1=float(1 - np.sum((np.log(pte_or) - np.log(lp2))**2) / np.sum((np.log(pte_or) - np.log(pte_or).mean())**2)), S2=float(np.log(ptr).std()), S4=float(np.corrcoef(gtr, np.log(ptr))[0, 1])))
        # mass-only isotonic-like: per-energy mean within precursor_mz decile bins of training
        bins = np.quantile(ctr.precursor_mz, np.linspace(0, 1, 11)); ib = np.clip(np.searchsorted(bins, ctr.precursor_mz.to_numpy(), side='right') - 1, 0, 9); ibt = np.clip(np.searchsorted(bins, cte.precursor_mz.to_numpy(), side='right') - 1, 0, 9)
        means = np.array([np.nanmean(Ytr[ib == b], 0) for b in range(10)]); score('mass_decile_per_energy_mean', means[ibt])
        print(rep, f, 'done', flush=True)
R = pd.DataFrame(rows); R.to_csv(f'{S}/t9_direct_tilt_folds.csv', index=False)
summ = R[~R.arm.str.startswith('_')].groupby('arm')[['P1', 'S2', 'S4', 'E30', 'E45', 'E60', 'E75', 'E90']].agg(['mean', 'std']).round(4)
print(summ.to_string()); print(R[R.arm.str.startswith('_')].groupby('arm')[['P1', 'S2', 'S4']].mean().round(3))
# paired fold wins vs collapse_ridge_g
piv = R[~R.arm.str.startswith('_')].pivot_table(index=['rep', 'fold'], columns='arm', values='P1')
print('wins vs collapse_ridge_g (of 15):', {c: int((piv[c] < piv['collapse_ridge_g']).sum()) for c in piv.columns}); print('mean rel improvement vs collapse_ridge_g:', ((piv['collapse_ridge_g'] - piv.T).T / piv['collapse_ridge_g'].values[:, None]).mean().round(4).to_dict())
json.dump(dict(summary={a: {f'{x}_{y}': float(v) for (x, y), v in summ.loc[a].items()} for a in summ.index}, wins={c: int((piv[c] < piv['collapse_ridge_g']).sum()) for c in piv.columns}, rel_impr=((piv['collapse_ridge_g'] - piv.T).T / piv['collapse_ridge_g'].values[:, None]).mean().round(4).to_dict()), open(f'{S}/t9_results.json', 'w'), indent=1)
