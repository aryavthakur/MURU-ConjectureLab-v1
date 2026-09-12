from common import *
from muru.discovery.estimate import fit_collapse, _best_log_g, ENERGY_SCALE
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
D = load('A_POOLED_ALIGNED'); long, cov = D['long'], D['cov']; F = folds(); E = np.array([30., 45., 60., 75., 90.]); Es = E / ENERGY_SCALE
rows = []; lgg = np.linspace(-4, 4, 161)
for rep in range(3):
    asg = F['repeats'][rep]['assignment']
    for f in range(5):
        tr = [k for k, v in asg.items() if v != f]; te = [k for k, v in asg.items() if v == f]
        Ltr = long[long.group_key.isin(tr)]; fit = fit_collapse(Ltr, with_hmain=False)
        a_lo, a_hi = fit.phi_v[0], fit.phi_v[-1]
        def Sfun(u): return np.clip((phi_eval(fit.phi_u, fit.phi_v, u) - a_hi) / (a_lo - a_hi), 0, 1)
        Wtr = Ltr.pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E); Wte = long[long.group_key.isin(te)].pivot_table(index='group_key', columns='ce_numeric', values='mu').reindex(columns=E)
        ctr = cov.set_index('group_key').loc[Wtr.index]; cte = cov.set_index('group_key').loc[Wte.index]
        sc = StandardScaler().fit(X_of(ctr)); Xtr, Xte = sc.transform(X_of(ctr)), sc.transform(X_of(cte)); Ytr, Yte = Wtr.to_numpy(float), Wte.to_numpy(float)
        # per-compound (g, b): mu = b + (a_lo - b) S(u); b closed form given g
        def fit_gb(Y):
            best = np.full(len(Y), np.inf); bg = np.zeros(len(Y)); bb = np.full(len(Y), a_hi)
            for l in lgg:
                s = Sfun(Es / np.exp(l))[None, :]; obs = np.isfinite(Y); Y0 = np.where(obs, Y, 0)
                # minimise sum (Y - b - (a_lo - b) s)^2 = sum (Y - a_lo s - b(1 - s))^2 -> b = sum((Y - a_lo s)(1-s)) / sum((1-s)^2)
                num = (np.where(obs, (Y0 - a_lo * s) * (1 - s), 0)).sum(1); den = (np.where(obs, (1 - s)**2, 0)).sum(1); b = np.clip(num / np.maximum(den, 1e-9), 0.0, a_lo - 0.05)
                pr = b[:, None] + (a_lo - b[:, None]) * s; sse = np.nansum((Y - pr)**2, 1); t = sse < best; best[t] = sse[t]; bg[t] = l; bb[t] = b[t]
            return bg, bb
        gtr, btr = fit_gb(Ytr); gte_or, bte_or = fit_gb(Yte)
        mg = Ridge(alpha=1.0).fit(Xtr, gtr); mb = Ridge(alpha=1.0).fit(Xtr, btr); lg2, b2 = mg.predict(Xte), np.clip(mb.predict(Xte), 0, a_lo - 0.05)
        b0 = np.nanmean(Ytr, 0)
        def score(name, P):
            d = P - Yte; rc = np.sqrt(np.nanmean(d**2, 1)); rb = np.sqrt(np.nanmean((b0[None, :] - Yte)**2, 1))
            rows.append(dict(rep=rep, fold=f, arm=name, P1=float(np.sqrt(np.nanmean(d**2))), S2=float(np.mean(rc <= 0.9 * rb)), S4=float(np.mean(rc > 2 * rb)), **{f'E{int(e)}': float(np.sqrt(np.nanmean(d[:, j]**2))) for j, e in enumerate(E)}))
        def pred(lg, b): s = Sfun(Es[None, :] / np.exp(lg)[:, None]); return b[:, None] + (a_lo - b[:, None]) * s
        score('gb_ridge_both', pred(lg2, b2)); score('gb_oracle_both', pred(gte_or, bte_or)); score('gb_oracle_g_ridge_b', pred(gte_or, b2)); score('gb_ridge_g_oracle_b', pred(lg2, bte_or))
        m1 = Ridge(alpha=1.0).fit(sc.transform(X_of(cov.set_index('group_key').loc[fit.compounds])), np.log(fit.g_hat), sample_weight=fit.weights); score('collapse_ridge_g', phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(m1.predict(Xte))[:, None]))
        if rep == 0:
            rows.append(dict(rep=rep, fold=f, arm='_r2_b_ridge', P1=float(1 - np.sum((bte_or - b2)**2) / np.sum((bte_or - bte_or.mean())**2)), S2=float(btr.std()), S4=float(np.corrcoef(gtr, btr)[0, 1])))
            rows.append(dict(rep=rep, fold=f, arm='_r2_g_in_gb_ridge', P1=float(1 - np.sum((gte_or - lg2)**2) / np.sum((gte_or - gte_or.mean())**2)), S2=float(gtr.std()), S4=float(np.mean(np.abs(gtr) > 1.59))))
        print(rep, f, flush=True)
R = pd.DataFrame(rows); R.to_csv(f'{S}/t10_asymptote_folds.csv', index=False)
summ = R[~R.arm.str.startswith('_')].groupby('arm')[['P1', 'S2', 'S4', 'E30', 'E90']].agg(['mean', 'std']).round(4); print(summ.to_string()); print(R[R.arm.str.startswith('_')].groupby('arm')[['P1', 'S2', 'S4']].mean().round(3))
piv = R[~R.arm.str.startswith('_')].pivot_table(index=['rep', 'fold'], columns='arm', values='P1'); print('wins vs collapse_ridge_g:', {c: int((piv[c] < piv['collapse_ridge_g']).sum()) for c in piv.columns}); print('rel impr', ((piv['collapse_ridge_g'] - piv.T).T / piv['collapse_ridge_g'].values[:, None]).mean().round(4).to_dict())
