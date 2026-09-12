"""Optimism / fragility checks: fresh fold seeds, winner's curse over a law family, V1C controls."""
import sys, itertools, json, time
sys.path.insert(0, 'src')
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
import muru.wur_stage2.arms_v1 as A, muru.wur_stage2.cv as CV, muru.wur_stage2.folds as FO
from muru.discovery import protocol
from muru.splits import grouped_folds
S = '/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_stats/'
long, cov, frame = CV.load_dev2b()
frozen = FO.load_folds()

def folds_with_seeds(seeds):
    reps = []
    for r, seed in enumerate(seeds):
        f = grouped_folds(frame["scaffold_group"], n_folds=5, seed=seed)
        reps.append({"repeat": r, "seed": seed, "assignment": dict(zip(frame["group_key"], (int(x) for x in f.to_numpy())))})
    return {"k": 5, "repeats": reps}

def p1(make, folds, reps=None):
    return CV.run_cv(make, long, cov, frame, folds, with_loeo=False, repeats=reps).p1_vector()

# ---- (a) ten fresh seeds, deterministic arms
t = time.time()
F10 = folds_with_seeds([777001 + i for i in range(10)])
res = {}
for make in [CV.B1MassOnly, CV.LinRidge, A.StableLaw, A.RichRidge, CV.B0NullProfile]:
    res[make.id] = p1(make, F10)
print("fresh-seed 50 folds (10 repeats x 5), fold-0 = 183-group each time:", round(time.time() - t, 1), "s")
for k, v in res.items():
    print(f"  {k:24s} mean {v.mean():.4f} sd {v.std(ddof=1):.4f}  fold0 {v.reshape(10,5)[0,0]:.4f}")
def cmp(a, b):
    d = res[a] - res[b]; d5 = d.reshape(10, 5)
    rep_means = d5.mean(1)
    print(f"  {a} - {b}: wins {(d<0).sum()}/50, excl fold0 {(d5[:,1:]<0).sum()}/40, mean {d.mean():+.5f}, per-repeat means {np.round(rep_means,5)}; "
          f"repeat-level SE (n=10) {rep_means.std(ddof=1)/np.sqrt(10):.5f}; rel {((res[b]-res[a])/res[b]).mean():+.3%}")
cmp("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA"); cmp("V1A_STABLE_LAW", "LIN_RIDGE_TIERA"); cmp("V1C_RICH_RIDGE_24", "V1A_STABLE_LAW"); cmp("LIN_RIDGE_TIERA", "B1_MASS_ONLY_ISOTONIC"); cmp("V1A_STABLE_LAW", "B1_MASS_ONLY_ISOTONIC")

# ---- (b) winner's curse: family of 2-feature and 3-feature log-linear laws on Tier A, refit per fold, frozen folds
class LogLinLaw(CV.CollapseArm):
    id = "LOGLIN"
    feats = ()
    def _Z(self, c):
        return np.column_stack([np.log1p(np.maximum(c[f].to_numpy(float), 0)) for f in self.feats])
    def fit_g(self, cov, log_g, w, ctx):
        Z = self._Z(cov.reset_index()); Aa = np.column_stack([np.ones(len(Z)), Z]); sw = np.sqrt(w)
        self.coef_, *_ = np.linalg.lstsq(Aa * sw[:, None], log_g * sw, rcond=None)
    def predict_log_g(self, cov):
        Z = self._Z(cov.reset_index()); return self.coef_[0] + Z @ self.coef_[1:]
feats = list(protocol.FEATURES)
laws = []
t = time.time()
for k in (2, 3):
    for combo in itertools.combinations(feats, k):
        cls = type("L", (LogLinLaw,), {"feats": combo, "id": "LOGLIN"})
        v = p1(cls, frozen)
        laws.append((k, combo, v.mean(), v))
print("law family evaluated:", len(laws), "laws in", round(time.time() - t, 1), "s")
v1a = p1(A.StableLaw, frozen); lin = p1(CV.LinRidge, frozen)
for k in (2, 3):
    ms = np.array([l[2] for l in laws if l[0] == k])
    print(f"  {k}-feature log-linear laws (n={len(ms)}): best {ms.min():.4f}, 5th pct {np.percentile(ms,5):.4f}, median {np.median(ms):.4f}, worst {ms.max():.4f}; V1A {v1a.mean():.4f}, LIN {lin.mean():.4f}")
    top = sorted([l for l in laws if l[0] == k], key=lambda l: l[2])[:5]
    for l in top: print("     ", l[1], round(l[2], 4))
# how many of the laws would pass c1&c2 vs S2A and c3 vs B1/B0 on the frozen folds?
led = lambda i: np.array([f["P1"] for f in json.load(open(f"artifacts/wur_stage2b/ledger/{i}.json"))["folds"]])
s2a, b1, b0 = led("S2A_FROZEN_PIPELINE"), led("B1_MASS_ONLY_ISOTONIC"), led("B0_NULL_PROFILE")
def passes(v):
    return ((v < s2a).sum() >= 12) and (((s2a - v) / s2a).mean() >= 0.05) and ((v < b0).sum() >= 13) and ((v < b1).sum() >= 12)
npass = sum(passes(l[3]) for l in laws)
print(f"  laws passing c1-c3 vs S2A/B0/B1 on the frozen folds: {npass}/{len(laws)}")
print(f"  laws with mean P1 <= V1A's: {sum(l[2] <= v1a.mean() for l in laws)}/{len(laws)}")

# ---- (c) V1C controls on frozen folds
rng = np.random.default_rng(1)
a2 = pd.read_csv(A.A2_PATH)
class RichRidgeShuffled(A.RichRidge):
    id = "V1C_SHUFFLED_A2"
class RichRidgeLinGrid(A.RichRidge):
    id = "V1C_LIN_ALPHAS"; ALPHAS = CV.LinRidge.ALPHAS
class LinRidgeV1CGrid(CV.LinRidge):
    id = "LIN_V1C_ALPHAS"; ALPHAS = A.RichRidge.ALPHAS
v1c = p1(A.RichRidge, frozen)
print(f"  V1C frozen {v1c.mean():.4f}; LIN {lin.mean():.4f}; V1C-LIN {(v1c-lin).mean():+.5f}")
vg = p1(RichRidgeLinGrid, frozen); lg = p1(LinRidgeV1CGrid, frozen)
print(f"  V1C with LIN's alpha grid {vg.mean():.4f}; LIN with V1C's alpha grid {lg.mean():.4f}; same-grid diffs: {(vg-lin).mean():+.5f} (LIN grid), {(v1c-lg).mean():+.5f} (V1C grid)")
shuf = []
for i in range(5):
    perm = rng.permutation(len(a2))
    a2s = a2.copy(); a2s[list(A.TIER_A2)] = a2[list(A.TIER_A2)].to_numpy()[perm]
    A._a2 = lambda a2s=a2s: a2s
    shuf.append(p1(RichRidgeShuffled, frozen).mean())
A._a2 = lambda: pd.read_csv(A.A2_PATH)
print(f"  V1C with row-shuffled Tier A2 (5 draws) mean P1: {np.round(shuf,4)}  vs LIN {lin.mean():.4f}")
# subsets: drop each single A2 feature; random 6-of-12 A2 subsets
sub = []
for i in range(20):
    keep = tuple(rng.choice(list(A.TIER_A2), size=6, replace=False))
    cls = type("R", (A.RichRidge,), {"id": "V1C_SUB6"})
    orig = A.TIER_A2; A.TIER_A2 = keep; A.FEATURES_24 = tuple(protocol.FEATURES) + keep
    def _X(cov, keep=keep):
        d = pd.read_csv(A.A2_PATH).set_index("group_key").loc[cov["group_key"]]
        return np.column_stack([cov[c].to_numpy(float) / A.SCALE_24[c] for c in protocol.FEATURES] + [d[c].to_numpy(float) / A.SCALE_24[c] for c in keep])
    old = A._X24; A._X24 = _X
    sub.append(p1(cls, frozen).mean()); A._X24 = old; A.TIER_A2 = orig
print(f"  random 6-of-12 Tier A2 subsets (n=20): best {min(sub):.4f} median {np.median(sub):.4f} worst {max(sub):.4f}; full 24 = {v1c.mean():.4f}")
