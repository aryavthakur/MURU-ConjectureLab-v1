"""Hostile statistical review of Stage 2B selection: dependence, corrected tests, null of the rule, power."""
import json, numpy as np, pandas as pd
from scipy import stats
S = '/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_stats/'
W = pd.read_pickle(S + 'W.pkl')
ARMS = ["B0_NULL_PROFILE", "B1_MASS_ONLY_ISOTONIC", "S2A_FROZEN_PIPELINE", "LIN_RIDGE_TIERA",
        "V1A_STABLE_LAW", "V1C_RICH_RIDGE_24", "V1D_RICH_HGB_24", "V2A_TWOPARAM_RIDGE"]
SH = {"B0_NULL_PROFILE": "B0", "B1_MASS_ONLY_ISOTONIC": "B1", "S2A_FROZEN_PIPELINE": "S2A", "LIN_RIDGE_TIERA": "LIN",
      "V1A_STABLE_LAW": "V1A", "V1C_RICH_RIDGE_24": "V1C", "V1D_RICH_HGB_24": "V1D", "V2A_TWOPARAM_RIDGE": "V2A"}
W = W.sort_values(['rep', 'fold', 'key']).reset_index(drop=True)
rep = W.rep.to_numpy(); fold = W.fold.to_numpy(); nc = W.ncell.to_numpy(float)
groups = W.group.to_numpy(); ug, ginv = np.unique(groups, return_inverse=True)
fid = rep * 5 + fold  # 0..14
BIG = ug[np.argmax(np.bincount(ginv))]

def fold_p1(sq):  # sq = ncell * rmse^2 per row -> 15 fold P1s
    num = np.bincount(fid, weights=sq, minlength=15); den = np.bincount(fid, weights=nc, minlength=15)
    return np.sqrt(num / den)

SQ = {a: nc * W[a].to_numpy() ** 2 for a in ARMS}
P1 = {a: fold_p1(SQ[a]) for a in ARMS}

def fold_stats(a, b):
    d = P1[a] - P1[b]; rel = (P1[b] - P1[a]) / P1[b]
    return dict(wins=int((d < 0).sum()), mean_diff=d.mean(), se_naive=d.std(ddof=1) / np.sqrt(15),
                rel=rel.mean(), t_naive=d.mean() / (d.std(ddof=1) / np.sqrt(15)))

def p1_from_rows(a, idx_rows, weights=None):
    """P1 per repeat over a set of rows (pooled RMSE over cells), then mean over repeats."""
    out = []
    for r in range(3):
        m = rep[idx_rows] == r
        w = nc[idx_rows][m] if weights is None else nc[idx_rows][m] * weights[m]
        out.append(np.sqrt(np.sum(w * W[a].to_numpy()[idx_rows][m] ** 2) / np.sum(w)))
    return np.mean(out)

print("=" * 80); print("A. Fold-level dependence")
for a, b in [("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA"), ("V1A_STABLE_LAW", "LIN_RIDGE_TIERA")]:
    d = P1[a] - P1[b]
    print(SH[a], "-", SH[b], "fold diffs by repeat:\n", d.reshape(3, 5).round(5))
# per-compound difference correlation across repeats
for a, b in [("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA"), ("V1C_RICH_RIDGE_24", "S2A_FROZEN_PIPELINE"), ("V1A_STABLE_LAW", "LIN_RIDGE_TIERA")]:
    D = W.assign(d=W[a] - W[b]).pivot(index='key', columns='rep', values='d')
    c = D.corr().to_numpy()
    print(f"{SH[a]}-{SH[b]}: per-compound diff corr across repeats r01={c[0,1]:.3f} r02={c[0,2]:.3f} r12={c[1,2]:.3f}; "
          f"share of |d| variance between compounds (ICC over repeats)={D.var(axis=1).mean()/D.stack().var():.3f} within/total")

print("=" * 80); print("B. Cluster bootstrap (scaffold groups, all repeats travel with the group) on the P1 difference and on mean per-compound RMSE diff")
rng = np.random.default_rng(20260912)
NB = 4000
G = len(ug)
rows_by_g = [np.where(ginv == g)[0] for g in range(G)]
def cluster_boot(a, b, nb=NB, drop_big=False):
    da = W[a].to_numpy(); db = W[b].to_numpy()
    sqa, sqb = SQ[a], SQ[b]
    gs = [g for g in range(G) if not (drop_big and ug[g] == BIG)]
    out_p1, out_mean, out_wins, out_fold = [], [], [], []
    for _ in range(nb):
        pick = rng.choice(gs, size=len(gs), replace=True)
        cnt = np.bincount(pick, minlength=G).astype(float)
        wrow = cnt[ginv]
        if drop_big: wrow[ginv == np.where(ug == BIG)[0][0]] = 0
        # P1 diff pooled per repeat then averaged
        pa = np.sqrt(np.bincount(rep, weights=wrow * sqa) / np.bincount(rep, weights=wrow * nc))
        pb = np.sqrt(np.bincount(rep, weights=wrow * sqb) / np.bincount(rep, weights=wrow * nc))
        out_p1.append((pa - pb).mean())
        out_mean.append(np.sum(wrow * (da - db)) / np.sum(wrow))
        fa = np.sqrt(np.bincount(fid, weights=wrow * sqa, minlength=15) / np.bincount(fid, weights=wrow * nc, minlength=15))
        fb = np.sqrt(np.bincount(fid, weights=wrow * sqb, minlength=15) / np.bincount(fid, weights=wrow * nc, minlength=15))
        out_fold.append((fa - fb).mean()); out_wins.append(int((fa < fb).sum()))
    return np.array(out_p1), np.array(out_mean), np.array(out_wins), np.array(out_fold)

def iid_boot(a, b, nb=NB):
    """the ledger's estimator: iid compounds within repeat, mean per-compound RMSE diff"""
    res = []
    for r in range(3):
        m = rep == r; d = (W[a] - W[b]).to_numpy()[m]
        idx = rng.integers(0, len(d), size=(nb, len(d))); res.append(d[idx].mean(1))
    return res

def perm_test(a, b, nperm=4000):
    """cluster label-swap: swap arm labels for a whole scaffold group (all its compounds, all repeats)."""
    sqa, sqb = SQ[a], SQ[b]
    obs_d = (P1[a] - P1[b]); obs_mean = obs_d.mean(); obs_wins = int((obs_d < 0).sum()); obs_rel = ((P1[b] - P1[a]) / P1[b]).mean()
    ms, ws, rels, passes = [], [], [], 0
    for _ in range(nperm):
        flip = rng.integers(0, 2, size=G).astype(bool)[ginv]
        xa = np.where(flip, sqb, sqa); xb = np.where(flip, sqa, sqb)
        fa, fb = fold_p1(xa), fold_p1(xb); d = fa - fb
        ms.append(d.mean()); ws.append(int((d < 0).sum())); rel = ((fb - fa) / fb).mean(); rels.append(rel)
        passes += int(((d < 0).sum() >= 12) and rel >= 0.05)
    ms, ws, rels = np.array(ms), np.array(ws), np.array(rels)
    return dict(obs_mean=obs_mean, obs_wins=obs_wins, obs_rel=obs_rel,
                p_mean=float(np.mean(ms <= obs_mean)), p_wins=float(np.mean(ws >= obs_wins)),
                p_wins_ge12=float(np.mean(ws >= 12)), p_wins_ge13=float(np.mean(ws >= 13)), p_rule_pass=passes / nperm,
                null_wins_dist=np.bincount(ws, minlength=16) / nperm, null_sd_mean=ms.std())

PAIRS = [("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA"), ("V1C_RICH_RIDGE_24", "V1A_STABLE_LAW"), ("V1A_STABLE_LAW", "LIN_RIDGE_TIERA"),
         ("LIN_RIDGE_TIERA", "S2A_FROZEN_PIPELINE"), ("V1C_RICH_RIDGE_24", "S2A_FROZEN_PIPELINE"), ("V1A_STABLE_LAW", "S2A_FROZEN_PIPELINE"),
         ("V1D_RICH_HGB_24", "S2A_FROZEN_PIPELINE"), ("V1C_RICH_RIDGE_24", "B1_MASS_ONLY_ISOTONIC"), ("V1A_STABLE_LAW", "B1_MASS_ONLY_ISOTONIC"),
         ("V1D_RICH_HGB_24", "V1C_RICH_RIDGE_24"), ("V1D_RICH_HGB_24", "LIN_RIDGE_TIERA"), ("LIN_RIDGE_TIERA", "B1_MASS_ONLY_ISOTONIC")]
summary = {}
for a, b in PAIRS:
    fs = fold_stats(a, b)
    bp1, bmean, bwins, bfold = cluster_boot(a, b)
    bp1n, _, _, _ = cluster_boot(a, b, nb=1500, drop_big=True)
    pt = perm_test(a, b)
    # per-repeat paired t over 5 folds; and t on the 5 fold diffs averaged over repeats
    d = (P1[a] - P1[b]).reshape(3, 5)
    t_rep = [stats.ttest_1samp(d[r], 0).pvalue for r in range(3)]
    davg = d.mean(0); t_avg = stats.ttest_1samp(davg, 0)
    d13 = np.concatenate([d[:, 0][:1], d[:, 1:].ravel()])  # 13 distinct folds
    t13 = stats.ttest_1samp(d13, 0)
    d12 = d[:, 1:].ravel()
    n_eff = 15 * (fs['se_naive'] / bfold.std()) ** 2
    key = f"{SH[a]} vs {SH[b]}"
    summary[key] = dict(wins=fs['wins'], wins_excl_fold0=int((d12 < 0).sum()), mean_diff=fs['mean_diff'], rel=fs['rel'],
                        se_naive=fs['se_naive'], se_clusterboot_folddiff=bfold.std(), n_eff_folds=n_eff,
                        p1diff_cb_ci95=np.percentile(bp1, [2.5, 97.5]), p1diff_cb_ci90=np.percentile(bp1, [5, 95]),
                        p1diff_cb_ci95_dropbig=np.percentile(bp1n, [2.5, 97.5]),
                        meandiff_cb_ci95=np.percentile(bmean, [2.5, 97.5]),
                        p_perm_mean=pt['p_mean'], p_perm_wins=pt['p_wins'], p_null_wins_ge12=pt['p_wins_ge12'], p_null_wins_ge13=pt['p_wins_ge13'],
                        p_null_rule_pass=pt['p_rule_pass'], null_wins_dist=pt['null_wins_dist'],
                        t_avg5_p=t_avg.pvalue, t_rep_p=t_rep, t13_p=t13.pvalue, cb_wins_ge12_frac=float(np.mean(bwins >= 12)),
                        cb_wins_ge13_frac=float(np.mean(bwins >= 13)))
    s = summary[key]
    print(f"\n{key}: wins {s['wins']}/15 (excl fold0: {s['wins_excl_fold0']}/12), mean fold diff {s['mean_diff']:+.5f} (rel {s['rel']:+.3%})")
    print(f"   naive fold SE {s['se_naive']:.5f} | cluster-bootstrap SE of same statistic {s['se_clusterboot_folddiff']:.5f} | n_eff folds {n_eff:.1f}")
    print(f"   P1 diff cluster-boot 95% CI {s['p1diff_cb_ci95'].round(5)}  90% {s['p1diff_cb_ci90'].round(5)}  (drop 183-group: {s['p1diff_cb_ci95_dropbig'].round(5)})")
    print(f"   mean per-compound RMSE diff cluster-boot 95% CI {s['meandiff_cb_ci95'].round(5)}")
    print(f"   cluster permutation: p(mean diff) {s['p_perm_mean']:.4f}, p(wins>=obs) {s['p_perm_wins']:.4f}; NULL P(wins>=12) {s['p_null_wins_ge12']:.3f}, P(wins>=13) {s['p_null_wins_ge13']:.3f}, P(rule c1&c2 pass | H0) {s['p_null_rule_pass']:.4f}")
    print(f"   null wins distribution (0..15): {np.round(s['null_wins_dist'],3)}")
    print(f"   paired t on 5 repeat-averaged folds p={s['t_avg5_p']:.4f}; per-repeat p={np.round(t_rep,4)}; t on 13 distinct folds p={s['t13_p']:.4f}")
    print(f"   cluster-bootstrap P(wins>=12)={s['cb_wins_ge12_frac']:.3f}, P(wins>=13)={s['cb_wins_ge13_frac']:.3f}")

print("=" * 80); print("B2. ledger-style iid bootstrap (V1C-LIN) for comparison")
for r, x in enumerate(iid_boot("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA")):
    print(f"  rep{r}: mean {x.mean():+.5f} 95% CI {np.percentile(x,[2.5,97.5]).round(5)} 90% {np.percentile(x,[5,95]).round(5)}")

print("=" * 80); print("C. Binomial reference for the 12/15 rule if folds were iid: P(>=12)=", 1 - stats.binom.cdf(11, 15, .5), " P(>=13)=", 1 - stats.binom.cdf(12, 15, .5),
      " ; 13 distinct: P(>=12 of 13)", 1 - stats.binom.cdf(11, 13, .5), " ; 5 iid: P(5/5)", .5 ** 5)

print("=" * 80); print("D. Where does V1C's gain over S2A / LIN live? by fold 0 (183-group) vs rest, by source")
for a, b in [("V1C_RICH_RIDGE_24", "S2A_FROZEN_PIPELINE"), ("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA"), ("V1A_STABLE_LAW", "LIN_RIDGE_TIERA"), ("LIN_RIDGE_TIERA", "B1_MASS_ONLY_ISOTONIC")]:
    for name, m in [("fold0/183-group", fold == 0), ("other 608", fold != 0), ("WUR", W.source.to_numpy() == "WUR"), ("LCSB", W.source.to_numpy() == "LCSB")]:
        idx = np.where(m)[0]
        print(f"  {SH[a]}-{SH[b]} {name:16s}: P1 {p1_from_rows(a, idx):.4f} vs {p1_from_rows(b, idx):.4f}  diff {p1_from_rows(a, idx)-p1_from_rows(b, idx):+.4f}")

print("=" * 80); print("E. S4 / S2 diagnostics: dependence on B0 per-compound RMSE")
b0 = W["B0_NULL_PROFILE"].to_numpy()
for a in ["S2A_FROZEN_PIPELINE", "LIN_RIDGE_TIERA", "V1A_STABLE_LAW", "V1C_RICH_RIDGE_24", "V1D_RICH_HGB_24", "B1_MASS_ONLY_ISOTONIC"]:
    x = W[a].to_numpy(); cat = x > 2 * b0; win = x <= 0.9 * b0
    print(f"  {SH[a]}: S4 {cat.mean():.3f}; of flagged, B0 rmse median {np.median(b0[cat]):.3f}, share with B0 rmse<0.06 {np.mean(b0[cat]<0.06):.2f}; "
          f"candidate rmse among flagged median {np.median(x[cat]):.3f}; S2 {win.mean():.3f}; corr(rmse, b0 rmse) {np.corrcoef(x,b0)[0,1]:.2f}")
print("  B0 per-compound rmse quantiles:", np.quantile(b0, [.05, .1, .25, .5, .75, .9]).round(3))
print("  P1 of B0 =", P1["B0_NULL_PROFILE"].mean().round(4), "; mean per-compound rmse B0 =", b0.mean().round(4))
for a in ARMS:
    print(f"  {SH[a]}: P1 {P1[a].mean():.4f} | mean per-compound RMSE {W[a].mean():.4f} | median {W[a].median():.4f} | 90% {W[a].quantile(.9):.4f}")

print("=" * 80); print("F. HOLD power: per-compound paired SD, ICC by scaffold group, design effect")
def icc_groups(d, g):
    df = pd.DataFrame({'d': d, 'g': g}); df = df[df.groupby('g')['d'].transform('size') > 1]
    # one-way ANOVA ICC
    grp = df.groupby('g')['d']; k = grp.size(); n = len(df); G_ = len(k)
    msb = np.sum(k * (grp.mean() - df.d.mean()) ** 2) / (G_ - 1)
    msw = np.sum(grp.apply(lambda s: ((s - s.mean()) ** 2).sum())) / (n - G_)
    k0 = (n - np.sum(k ** 2) / n) / (G_ - 1)
    return (msb - msw) / (msb + (k0 - 1) * msw)
pow_rows = {}
for a, b in [("V1C_RICH_RIDGE_24", "S2A_FROZEN_PIPELINE"), ("V1C_RICH_RIDGE_24", "B1_MASS_ONLY_ISOTONIC"), ("V1A_STABLE_LAW", "S2A_FROZEN_PIPELINE"), ("V1A_STABLE_LAW", "B1_MASS_ONLY_ISOTONIC"), ("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA")]:
    sds, iccs, iccs_nb, means = [], [], [], []
    for r in range(3):
        m = rep == r; d = (W[a] - W[b]).to_numpy()[m]; g = groups[m]
        sds.append(d.std(ddof=1)); means.append(d.mean()); iccs.append(icc_groups(d, g)); iccs_nb.append(icc_groups(d[g != BIG], g[g != BIG]))
    sd, icc, iccnb, mu = np.mean(sds), np.mean(iccs), np.mean(iccs_nb), np.mean(means)
    # HOLD: 130 compounds, 94 groups -> mean cluster size 1.383; design effect 1+(m-1)*icc (approx; unknown size distribution)
    mbar = 130 / 94; de = 1 + (mbar - 1) * max(iccnb, 0); n_eff = 130 / de
    ref_p1 = P1[b].mean()
    for label, delta in [("2.5% of P1(ref) on mean per-compound diff", 0.025 * W[b].mean()), ("observed DEV mean per-compound diff", -mu), ("2.5% rel of P1", 0.025 * ref_p1)]:
        se = sd / np.sqrt(n_eff); z = delta / se
        power_1sided_05 = 1 - stats.norm.cdf(1.645 - z)
        print(f"  {SH[a]}-{SH[b]}: paired SD {sd:.4f}, ICC(all) {icc:.3f}, ICC(no 183-group) {iccnb:.3f}, DE {de:.2f}, n_eff {n_eff:.0f}; "
              f"delta[{label}]={delta:.4f}, SE {se:.4f}, z {z:.2f}, power(one-sided 5%) {power_1sided_05:.2f}")
    # minimal detectable effect at 80% power
    mde = (1.645 + 0.84) * sd / np.sqrt(n_eff)
    print(f"     MDE at 80% power: {mde:.4f} = {mde/W[b].mean():.1%} of ref mean per-compound RMSE ({W[b].mean():.4f})")

print("=" * 80); print("G. S2A search variance: S2A fold P1 spread vs V1C; the HOLD S2A arm is one search draw")
d = P1["S2A_FROZEN_PIPELINE"] - P1["V1C_RICH_RIDGE_24"]
print("  S2A P1 per fold:", P1["S2A_FROZEN_PIPELINE"].round(4)); print("  S2A - V1C per fold:", d.round(4), " min rel gain of V1C:", ((d) / P1["S2A_FROZEN_PIPELINE"]).min().round(4))
print("  S2A fold0 (identical held-out and training set, only PySR seed differs):", P1["S2A_FROZEN_PIPELINE"].reshape(3, 5)[:, 0].round(4), " -> search-only SD", P1["S2A_FROZEN_PIPELINE"].reshape(3, 5)[:, 0].std(ddof=1).round(4))
print("  S2A within-repeat spread over non-fold0 folds SD:", P1["S2A_FROZEN_PIPELINE"].reshape(3, 5)[:, 1:].std(ddof=1).round(4), " LIN:", P1["LIN_RIDGE_TIERA"].reshape(3, 5)[:, 1:].std(ddof=1).round(4))

print("=" * 80); print("H. Effect size vs recoverable MSE (oracle-g P1 0.051 from the failure analysis)")
orc = 0.051
for a in ARMS:
    p = P1[a].mean(); b0p = P1["B0_NULL_PROFILE"].mean()
    print(f"  {SH[a]}: P1 {p:.4f}; MSE {p**2:.5f}; share of recoverable MSE (B0->oracle) closed: {(b0p**2 - p**2)/(b0p**2 - orc**2):.2%}")
json.dump({k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()} for k, v in summary.items()}, open(S + 'summary.json', 'w'), indent=1, default=float)
