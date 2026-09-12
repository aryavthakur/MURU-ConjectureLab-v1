from common import *
from scipy.optimize import least_squares
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
out = {}
def logistic(p, lE): a, b, m, k = p; return b + (a - b) / (1 + np.exp(k * (lE - m)))
def fit4(E, y):
    lE = np.log(E); 
    p0 = [y.max(), y.min(), np.median(lE), 3.0]
    lb = [0, 0, lE.min() - 1.5, 0.2]; ub = [1.05, 1.0, lE.max() + 1.5, 20]
    p0 = np.clip(p0, np.array(lb) + 1e-6, np.array(ub) - 1e-6)
    best = None
    for k0 in (1.5, 3.0, 6.0):
        for m0 in (lE.min(), np.median(lE), lE.max()):
            p = np.clip([p0[0], p0[1], m0, k0], np.array(lb)+1e-6, np.array(ub)-1e-6)
            r = least_squares(lambda p: logistic(p, lE) - y, p, bounds=(lb, ub))
            if best is None or r.cost < best.cost: best = r
    return best.x, np.sqrt(2 * best.cost / len(y))
for an in ['A_POOLED_ALIGNED', 'B_WUR_NATIVE', 'C_LCSB_NATIVE']:
    D = load(an); W = D['long'].pivot_table(index='group_key', columns='ce_numeric', values='mu')
    E = W.columns.to_numpy(float); rows = []
    for k, row in W.iterrows():
        y = row.to_numpy(float); ok = np.isfinite(y)
        if ok.sum() < 5: continue
        p, rmse = fit4(E[ok], y[ok]); rows.append(dict(group_key=k, a=p[0], b=p[1], m=p[2], k=p[3], rmse=rmse, mu_lo=y[ok][0], mu_hi=y[ok][-1], rng=y[ok].max()-y[ok].min()))
    P = pd.DataFrame(rows).merge(D['cov'], on='group_key').merge(D['g'][['group_key','g_hat']], on='group_key')
    P.to_csv(f'{S}/t3_logistic_{an}.csv', index=False)
    r = dict(n=len(P), rmse_median=float(P.rmse.median()), rmse_q90=float(P.rmse.quantile(.9)))
    for c in ['a', 'b', 'm', 'k']:
        r[f'{c}_q'] = P[c].quantile([.05, .25, .5, .75, .95]).round(3).tolist()
    r['frac_a_lt_0p9'] = float((P.a < 0.9).mean()); r['frac_a_lt_0p8'] = float((P.a < 0.8).mean()); r['frac_b_gt_0p4'] = float((P.b > 0.4).mean()); r['frac_b_lt_0p2'] = float((P.b < 0.2).mean())
    r['frac_m_at_bound'] = float(((P.m < np.log(E.min()) - 1.4) | (P.m > np.log(E.max()) + 1.4)).mean()); r['frac_k_at_ub'] = float((P.k > 19).mean())
    r['sd_log_k'] = float(np.log(P.k).std()); r['corr_m_logg'] = float(np.corrcoef(P.m, np.log(P.g_hat))[0, 1]); r['spearman_m_logg'] = sp(P.m, np.log(P.g_hat))
    r['spearman_desc'] = {c: {d: round(sp(P[c], P[d]), 2) for d in FEATURES} for c in ['a', 'b', 'm', 'k']}
    r['by_source'] = P.groupby('source')[['a', 'b', 'm', 'k']].median().round(3).to_dict('index') if P.source.nunique() > 1 else {}
    if P.source.nunique() > 1:
        from scipy.stats import mannwhitneyu
        r['mwu_p_source'] = {c: float(mannwhitneyu(P[P.source == 'WUR'][c], P[P.source == 'LCSB'][c])[1]) for c in ['a', 'b', 'm', 'k']}
    # attribution of shared-shape inadequacy: constrained fits with a,b,k fixed at population medians (only m free), then free each in turn
    lE = np.log(E); am, bm, km = P.a.median(), P.b.median(), P.k.median()
    def sse_fit(y, free):
        # free: subset of 'abk'; m always free
        def f(q):
            a = q[0] if 'a' in free else am; b = q[1] if 'b' in free else bm; k = q[3] if 'k' in free else km; m = q[2]
            return logistic([a, b, m, k], lE) - y
        best = None
        for m0 in (lE.min(), np.median(lE), lE.max()):
            q0 = np.array([am, bm, m0, km]); res = least_squares(f, q0, bounds=([0, 0, lE.min()-1.5, 0.2], [1.05, 1.0, lE.max()+1.5, 20]))
            if best is None or res.cost < best.cost: best = res
        return 2 * best.cost
    att = []
    Wk = W.loc[P.group_key]
    for k, row in Wk.iterrows():
        y = row.to_numpy(float)
        if not np.all(np.isfinite(y)): continue
        s0 = sse_fit(y, ''); sa = sse_fit(y, 'a'); sb = sse_fit(y, 'b'); sk = sse_fit(y, 'k'); sall = sse_fit(y, 'abk')
        att.append(dict(group_key=k, s0=s0, da=s0-sa, db=s0-sb, dk=s0-sk, dall=s0-sall))
    A = pd.DataFrame(att); A.to_csv(f'{S}/t3_attribution_{an}.csv', index=False)
    tot = A[['da', 'db', 'dk']].clip(lower=0)
    r['attribution_pooled_share_of_SSE_reduction'] = (tot.sum() / tot.sum().sum()).round(3).to_dict()
    r['attribution_sse'] = dict(s0=float(A.s0.sum()), free_a=float((A.s0-A.da).sum()), free_b=float((A.s0-A.db).sum()), free_k=float((A.s0-A.dk).sum()), free_all=float((A.s0-A.dall).sum()))
    r['attribution_winner_frac'] = tot.idxmax(1).value_counts(normalize=True).round(3).to_dict()
    r['rmse_shared_abk_only_m'] = float(np.sqrt(A.s0.sum() / (len(A) * len(E)))); r['rmse_all_free'] = float(np.sqrt((A.s0-A.dall).sum() / (len(A) * len(E))))
    # relation to ladder wins (test compounds)
    lad = D['ladder']['records']; rel = {}
    for d in ['M1', 'M2', 'M3']:
        df = pd.DataFrame(lad[d]); df['win'] = (df.mae_alt <= 0.9 * df.mae_m0) & ~df.unresolved_boundary
        df = df.merge(P, left_on='compound_id', right_on='group_key')
        ev = df[~df.unresolved_boundary]
        rel[d] = {c: dict(win_median=float(ev[ev.win][c].median()), nowin_median=float(ev[~ev.win][c].median())) for c in ['a', 'b', 'k']}
    r['ladder_win_vs_params'] = rel
    out[an] = r
    fig, ax = plt.subplots(1, 4, figsize=(16, 3.5))
    for i, c in enumerate(['a', 'b', 'm', 'k']): ax[i].hist(P[c], bins=40); ax[i].set_title(f'{an} {c}')
    plt.tight_layout(); plt.savefig(f'{S}/t3_logistic_{an}.png', dpi=100)
json.dump(out, open(f'{S}/t3_results.json', 'w'), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
