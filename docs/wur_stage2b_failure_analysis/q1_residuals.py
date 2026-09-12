import sys; sys.path.insert(0, '/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/failure_analysis')
from fa_common import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import stats
REP_SD = 0.0295
results = {}
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
for ai, a in enumerate(ANALYSES):
    D = load(a); long, g, cov, comp, col = D['long'], D['g'], D['cov'], D['comp'], D['col']
    comps, E, Y = wide(long)
    gg = g.set_index('group_key').loc[comps]
    ghat = gg['g_hat'].to_numpy()
    knots, vals = np.array(col['phi_u']), np.array(col['phi_v'])
    u = (E[None, :] / ENERGY_SCALE) / ghat[:, None]
    pred = phi_eval(knots, vals, u)
    R = Y - pred
    obs = np.isfinite(Y)
    r = R[obs]
    print(f'\n===== {a}: n={len(comps)} obs={obs.sum()} resid SD={r.std():.4f} (doc {col["resid_sd"]:.4f}) mean={r.mean():+.4f} MAD-SD={1.4826*np.median(np.abs(r-np.median(r))):.4f} ratio to repeat SD={r.std()/REP_SD:.2f}')
    # by energy
    src = comp.set_index('group_key').loc[comps, 'source'].to_numpy()
    mz = cov.set_index('group_key').loc[comps, 'precursor_mz'].to_numpy()
    lg = np.log(ghat)
    gterc = pd.qcut(lg, 3, labels=['g_lo', 'g_mid', 'g_hi'])
    mterc = pd.qcut(mz, 3, labels=['mz_lo', 'mz_mid', 'mz_hi'])
    rows = []
    for j, e in enumerate(E):
        rj = R[:, j]; ok = np.isfinite(rj)
        rows.append(dict(E=e, n=ok.sum(), mean=rj[ok].mean(), sd=rj[ok].std(), q10=np.quantile(rj[ok], .1), q90=np.quantile(rj[ok], .9), frac_pos=(rj[ok] > 0).mean(),
                         t=stats.ttest_1samp(rj[ok], 0).statistic, mean_mu=np.nanmean(Y[:, j]), mean_pred=np.nanmean(pred[:, j])))
    te = pd.DataFrame(rows); print('by energy:\n', te.round(4).to_string(index=False))
    def by_group(labels, name):
        out = []
        for lab in pd.unique(labels):
            m = (labels == lab)
            row = dict(group=lab, n=m.sum())
            for j, e in enumerate(E):
                rj = R[m, j]; ok = np.isfinite(rj); row[f'E{int(e)}'] = rj[ok].mean()
            rr = R[m][obs[m]]; row['sd_all'] = rr.std(); row['mean_all'] = rr.mean()
            out.append(row)
        t = pd.DataFrame(out); print(f'by {name} (mean residual per energy):\n', t.round(4).to_string(index=False)); return t
    ts = by_group(src, 'source') if len(set(src)) > 1 else None
    tg = by_group(np.asarray(gterc).astype(str), 'g tercile')
    tm = by_group(np.asarray(mterc).astype(str), 'mz tercile')
    # per-compound residual pattern: fraction of residual variance that is between-compound (offset) vs within
    rc_mean = np.nanmean(R, 1)
    within = np.nanvar(R - rc_mean[:, None]); between = np.var(rc_mean)
    # slope of residual vs energy per compound (linear trend in log E)
    lE = np.log(E)
    slopes = np.array([np.polyfit(lE[np.isfinite(R[i])], R[i][np.isfinite(R[i])], 1)[0] if np.isfinite(R[i]).sum() >= 3 else np.nan for i in range(len(comps))])
    curv = np.array([np.polyfit(lE[np.isfinite(R[i])], R[i][np.isfinite(R[i])], 2)[0] if np.isfinite(R[i]).sum() >= 4 else np.nan for i in range(len(comps))])
    print(f'residual variance decomposition: total {r.var():.5f}, between-compound offset {between:.5f} ({between/r.var():.1%}), within {within:.5f}')
    print(f'per-compound residual slope vs lnE: mean {np.nanmean(slopes):+.4f} sd {np.nanstd(slopes):.4f}; |slope|>0.05: {(np.abs(slopes)>0.05).mean():.1%}; curvature mean {np.nanmean(curv):+.4f} sd {np.nanstd(curv):.4f}')
    # correlation of residual slope with log g and mz
    print(f'corr(resid slope, log g) = {stats.spearmanr(slopes, lg, nan_policy="omit").statistic:+.3f}; corr(resid slope, mz) = {stats.spearmanr(slopes, mz, nan_policy="omit").statistic:+.3f}; corr(resid mean, log g) = {stats.spearmanr(rc_mean, lg, nan_policy="omit").statistic:+.3f}')
    # residual by u (position along Phi): bins on log u
    lu = np.log(u)[obs]; rr = R[obs]
    bins = np.quantile(lu, np.linspace(0, 1, 11))
    idx = np.clip(np.searchsorted(bins, lu, side='right') - 1, 0, 9)
    tu = pd.DataFrame({'bin': idx, 'lu': lu, 'r': rr, 'mu': Y[obs]}).groupby('bin').agg(lu_mid=('lu', 'median'), n=('r', 'size'), mean_r=('r', 'mean'), sd_r=('r', 'std'), mean_mu=('mu', 'mean'))
    print('residual by log-u decile:\n', tu.round(4).to_string())
    # SD by energy relative to repeatability and heteroscedasticity vs mu level
    mu_bins = pd.cut(Y[obs], [0, .3, .5, .7, .9, 1.01])
    th = pd.DataFrame({'mu_bin': mu_bins, 'r': rr}).groupby('mu_bin', observed=True)['r'].agg(['size', 'mean', 'std'])
    print('residual by mu level:\n', th.round(4).to_string())
    results[a] = dict(resid_sd=float(r.std()), by_energy=te.to_dict('records'), between_frac=float(between / r.var()), slope_sd=float(np.nanstd(slopes)))
    # plots
    ax = axes[ai, 0]
    for lab, c in zip(['g_lo', 'g_mid', 'g_hi'], ['C0', 'C1', 'C2']):
        m = np.asarray(gterc).astype(str) == lab
        ax.errorbar(E, np.nanmean(R[m], 0), yerr=np.nanstd(R[m], 0), label=lab, color=c, capsize=3)
    ax.axhline(0, color='k', lw=.5); ax.set_title(f'{a}: mean resid by E, g tercile'); ax.legend(); ax.set_xlabel('E'); ax.set_ylabel('mu - Phi(u)')
    ax = axes[ai, 1]
    ax.scatter(lu, rr, s=2, alpha=.15); ax.plot(tu['lu_mid'], tu['mean_r'], 'r-o'); ax.axhline(0, color='k', lw=.5); ax.set_title('resid vs log u'); ax.set_xlabel('log u'); ax.set_ylim(-.4, .4)
    ax = axes[ai, 2]
    ax.plot(knots, vals, 'k-', label='Phi'); ax.scatter(lu, Y[obs], s=2, alpha=.1); ax.set_title('Phi and collapsed data'); ax.set_xlabel('log u'); ax.legend()
plt.tight_layout(); plt.savefig(f'{OUT}/q1_residuals.png', dpi=110)
json.dump(results, open(f'{OUT}/q1_results.json', 'w'), indent=1, default=float)
