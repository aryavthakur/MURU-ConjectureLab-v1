"""v2 scale models (protocol sections 8 and 9)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge

from muru.discovery import protocol
from muru.wur_v2 import folds as FO
from muru.wur_v2.engine import POOLED_ENERGIES, ScaleModel, TrainSet, mu_from_log_g, trainset

RIDGE_ALPHAS_TA = (0.01, 0.1, 1.0, 10.0, 100.0)
RIDGE_ALPHAS_FP = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)
BLOCK_WEIGHTS = (0.1, 0.3, 1.0)
KERNEL_ALPHAS = (0.01, 0.03, 0.1, 0.3, 1.0)


def tier_a_scaled(cov: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({c: cov[c].astype(float) / protocol.SCALE[c] for c in protocol.FEATURES}, index=cov.index)


class B0Null(ScaleModel):
    """Per-rung training mean; bypasses the profile."""
    id = "B0"


class MassIsotonic(ScaleModel):
    id = "B1_MASS_ISOTONIC"

    def fit(self, ts, cfg):
        x = ts.data.cov.loc[ts.keys, "precursor_mz"].to_numpy(float)
        return IsotonicRegression(increasing="auto", out_of_bounds="clip").fit(x, ts.log_g, sample_weight=ts.w)

    def predict(self, m, ts, keys):
        return m.predict(ts.data.cov.loc[keys, "precursor_mz"].to_numpy(float))


class RidgeModel(ScaleModel):
    """Ridge of log g on one feature block with curvature sample weights."""

    def __init__(self, feature: str, alphas=RIDGE_ALPHAS_TA, model_id: str | None = None):
        self.feature, self.alphas = feature, alphas
        self.id = model_id or f"RIDGE_{feature}"

    def grid(self):
        return list(self.alphas)

    def fit(self, ts, alpha):
        return Ridge(alpha=alpha).fit(ts.X(self.feature), ts.log_g, sample_weight=ts.w)

    def predict(self, m, ts, keys):
        return m.predict(ts.X(self.feature, keys))


class RidgeV1Selection(ScaleModel):
    """TA_RIDGE with v1's alpha selection: outer-collapse labels, weighted log g loss."""
    id = "TA_RIDGE_V1SEL"

    def grid(self):
        return [None]

    def fit(self, ts, cfg):
        X = ts.X("TIER_A")
        inner = FO.inner_folds(ts.data.cov.loc[ts.keys].reset_index(), ts.group_col, ts.outer_fold)
        best = None
        for a in RIDGE_ALPHAS_TA:
            sse = 0.0
            for k in range(FO.INNER_K):
                tr, va = inner != k, inner == k
                m = Ridge(alpha=a).fit(X[tr], ts.log_g[tr], sample_weight=ts.w[tr])
                sse += float(np.sum(ts.w[va] * (ts.log_g[va] - m.predict(X[va])) ** 2))
            if best is None or sse < best[0]:
                best = (sse, a)
        m = Ridge(alpha=best[1]).fit(X, ts.log_g, sample_weight=ts.w)
        m.alpha_selected_ = best[1]
        return m

    def predict(self, m, ts, keys):
        return m.predict(ts.X("TIER_A", keys))


class JointRidge(ScaleModel):
    """Training-standardized Tier A block plus a weighted fingerprint block, one ridge."""

    def __init__(self, fp: str, model_id: str):
        self.fp, self.id = fp, model_id

    def grid(self):
        return [(a, b) for b in BLOCK_WEIGHTS for a in RIDGE_ALPHAS_FP]

    def _design(self, ts, keys, stats, bw):
        A = ts.X("TIER_A", keys)
        A = (A - stats[0]) / stats[1]
        return np.hstack([A, bw * ts.X(self.fp, keys)])

    def fit(self, ts, cfg):
        a, bw = cfg
        A = ts.X("TIER_A")
        stats = (A.mean(0), A.std(0) + 1e-12)
        m = Ridge(alpha=a).fit(self._design(ts, ts.keys, stats, bw), ts.log_g, sample_weight=ts.w)
        return (m, stats, bw)

    def predict(self, mm, ts, keys):
        m, stats, bw = mm
        return m.predict(self._design(ts, keys, stats, bw))


class TwoStage(ScaleModel):
    """Tier A ridge (alpha selected as TA_RIDGE would, on the same training set), then a
    fingerprint ridge on residuals cross-fitted inside the training set."""

    def __init__(self, fp: str, model_id: str):
        self.fp, self.id = fp, model_id

    def grid(self):
        return list(RIDGE_ALPHAS_FP)

    def _stage1_alpha(self, ts):
        # nested selection of the Tier A alpha on this training set's own inner folds (log g loss on
        # its labels; cheap and label-consistent inside the stage that uses it)
        return RidgeV1Selection().fit(ts, None).alpha_selected_

    def fit(self, ts, alpha2):
        a1 = self._stage1_alpha(ts)
        XA = ts.X("TIER_A")
        inner = FO.inner_folds(ts.data.cov.loc[ts.keys].reset_index(), ts.group_col, ts.outer_fold + 777)
        resid = np.zeros(len(ts.keys))
        for k in range(FO.INNER_K):
            tr, va = inner != k, inner == k
            m1 = Ridge(alpha=a1).fit(XA[tr], ts.log_g[tr], sample_weight=ts.w[tr])
            resid[va] = ts.log_g[va] - m1.predict(XA[va])
        m1 = Ridge(alpha=a1).fit(XA, ts.log_g, sample_weight=ts.w)
        m2 = Ridge(alpha=alpha2).fit(ts.X(self.fp), resid, sample_weight=ts.w)
        return (m1, m2)

    def predict(self, mm, ts, keys):
        m1, m2 = mm
        return m1.predict(ts.X("TIER_A", keys)) + m2.predict(ts.X(self.fp, keys))


def minmax_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Count Tanimoto (MinMax) similarity between rows of A and rows of B (nonnegative counts)."""
    out = np.empty((A.shape[0], B.shape[0]))
    for i in range(A.shape[0]):
        mn = np.minimum(A[i][None, :], B).sum(1)
        mx = np.maximum(A[i][None, :], B).sum(1)
        out[i] = np.where(mx > 0, mn / np.maximum(mx, 1e-12), 0.0)
    return out


class KernelRidgeMinMax(ScaleModel):
    """Weighted kernel ridge with the MinMax kernel on raw fingerprint counts.

    The kernel is structure-only and precomputed once over all compounds
    (`Data.kernels[name]`); fitting uses only the training-by-training block
    and prediction the test-by-training block.
    """

    def __init__(self, kernel: str, model_id: str):
        self.kernel, self.id = kernel, model_id

    def grid(self):
        return list(KERNEL_ALPHAS)

    def fit(self, ts, alpha):
        K = kernel_block(ts.data, self.kernel, ts.keys, ts.keys)
        w = ts.w
        mu0 = float(np.sum(w * ts.log_g) / np.sum(w))
        coef = np.linalg.solve(K + alpha * np.diag(1.0 / np.maximum(w, 1e-6)), ts.log_g - mu0)
        return (coef, mu0)

    def predict(self, mm, ts, keys):
        coef, mu0 = mm
        return mu0 + kernel_block(ts.data, self.kernel, np.asarray(keys), ts.keys) @ coef


def kernel_block(data, name, rows, cols) -> np.ndarray:
    index, K = data.kernels[name]
    return K[np.ix_(index.get_indexer(rows), index.get_indexer(cols))]


class KNNResidual(ScaleModel):
    """Base Tier A ridge plus the similarity-weighted mean of cross-fitted residuals of the
    k most similar training compounds (MinMax on raw counts)."""

    def __init__(self, kernel: str, model_id: str, k: int = 10):
        self.kernel, self.id, self.k = kernel, model_id, k

    def fit(self, ts, cfg):
        two = TwoStage("TIER_A", "_")
        a1 = two._stage1_alpha(ts)
        XA = ts.X("TIER_A")
        inner = FO.inner_folds(ts.data.cov.loc[ts.keys].reset_index(), ts.group_col, ts.outer_fold + 777)
        resid = np.zeros(len(ts.keys))
        for j in range(FO.INNER_K):
            tr, va = inner != j, inner == j
            m1 = Ridge(alpha=a1).fit(XA[tr], ts.log_g[tr], sample_weight=ts.w[tr])
            resid[va] = ts.log_g[va] - m1.predict(XA[va])
        m1 = Ridge(alpha=a1).fit(XA, ts.log_g, sample_weight=ts.w)
        return (m1, resid)

    def predict(self, mm, ts, keys):
        m1, resid = mm
        S = kernel_block(ts.data, self.kernel, np.asarray(keys), ts.keys)
        idx = np.argsort(-S, axis=1)[:, :self.k]
        s = np.take_along_axis(S, idx, 1)
        corr = (s * resid[idx]).sum(1) / np.maximum(s.sum(1), 1e-12)
        return m1.predict(ts.X("TIER_A", keys)) + corr


class PermutedFeatures(ScaleModel):
    """Negative control: the wrapped model with feature rows permuted across compounds.

    Each seed gets its own permuted block (`<feature>__perm<seed>`); an earlier
    version cached one block under a seed-free name, so every seed reused the
    first permutation.
    """

    def __init__(self, inner: ScaleModel, feature: str, seed: int):
        self.inner, self.feature, self.seed = inner, feature, seed
        self.id = f"{inner.id}_PERMUTED_s{seed}"
        self.perm_name = f"{feature}__perm{seed}"

    def grid(self):
        return self.inner.grid()

    def _ensure(self, data):
        if self.perm_name not in data.features:
            F = data.features[self.feature]
            rng = np.random.default_rng(self.seed)
            data.features[self.perm_name] = pd.DataFrame(F.iloc[rng.permutation(len(F))].to_numpy(), index=F.index, columns=F.columns)

    def _call(self, fn, data, *args):
        self._ensure(data)
        orig = self.inner.__dict__.copy()
        for attr in ("feature", "fp"):
            if getattr(self.inner, attr, None) == self.feature:
                setattr(self.inner, attr, self.perm_name)
        try:
            return fn(*args)
        finally:
            self.inner.__dict__.update(orig)

    def fit(self, ts, cfg):
        return self._call(self.inner.fit, ts.data, ts, cfg)

    def predict(self, m, ts, keys):
        return self._call(self.inner.predict, ts.data, m, ts, keys)


def b0_predictions(data, assignment: pd.Series) -> pd.DataFrame:
    out = []
    for f in sorted(assignment.unique()):
        test = sorted(assignment.index[assignment == f]); train = sorted(assignment.index[assignment != f])
        m = data.Y.loc[train].mean(0)
        out.append(pd.DataFrame(np.tile(m.to_numpy(), (len(test), 1)), index=test, columns=data.Y.columns))
    return pd.concat(out).sort_index()
