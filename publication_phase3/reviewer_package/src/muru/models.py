"""Phase 2 baseline ladder, nested grouped CV, and compound-level bootstrap.

Every model answers a distinct scientific question (Phase 2 instruction 15).
There is no leaderboard and no model family beyond the pre-registered ones.

The flexible gradient-boosted model is called the FLEXIBLE PREDICTIVE BENCHMARK,
never a ceiling: it is one pre-registered family with one frozen search space,
not an information-theoretic bound (MASTER_PLAN_CLARIFICATIONS C2).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import SplineTransformer

ENERGIES = (15, 30, 45, 60, 75, 90)
SEED = 20260811


# ---------------------------------------------------------------------------
# Feature builders
# ---------------------------------------------------------------------------
def energy_onehot(e: np.ndarray) -> np.ndarray:
    return np.column_stack([(e == v).astype(float) for v in ENERGIES])


def _spline(n_knots: int) -> SplineTransformer:
    return SplineTransformer(n_knots=n_knots, degree=3,
                             extrapolation="linear", include_bias=False)


def row_tensor(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Row-wise Khatri-Rao product: the tensor-product interaction basis."""
    n, a = A.shape
    b = B.shape[1]
    return (A[:, :, None] * B[:, None, :]).reshape(n, a * b)


# ---------------------------------------------------------------------------
# Models. Each exposes fit(df) / predict(df) over a row-level frame carrying
# `ce_numeric`, `mu`, and whatever feature columns it needs.
# ---------------------------------------------------------------------------
class GlobalMean:
    """B0 -- the floor."""

    def fit(self, df, feats=None):
        self.m_ = float(df.mu.mean())
        return self

    def predict(self, df):
        return np.full(len(df), self.m_)


class PerEnergyMean:
    """B1 -- structure-blind, energy-aware. The K4A comparator."""

    def fit(self, df, feats=None):
        self.by_ = df.groupby("ce_numeric").mu.mean().to_dict()
        self.g_ = float(df.mu.mean())
        return self

    def predict(self, df):
        return df.ce_numeric.map(self.by_).fillna(self.g_).to_numpy(float)


class MassSimple:
    """B2 / MASS SIMPLE -- energy factor + LINEAR precursor m/z.

    The Phase 1 carry-forward competitor, unchanged.
    """

    def fit(self, df, feats=None):
        X = np.column_stack([energy_onehot(df.ce_numeric.to_numpy()),
                             df.precursor_mz.to_numpy(float)])
        self.b_, *_ = np.linalg.lstsq(X, df.mu.to_numpy(float), rcond=None)
        return self

    def predict(self, df):
        X = np.column_stack([energy_onehot(df.ce_numeric.to_numpy()),
                             df.precursor_mz.to_numpy(float)])
        return X @ self.b_


class MassFlex:
    """MASS FLEX -- tensor-product smooth in (NCE, precursor m/z).

    Nonlinear in energy, nonlinear in mass, with a full energy-by-mass
    interaction. Deliberately strong: it is the adversarial explanation the
    structure model must beat, so making it weak would rig K4B.
    """

    def __init__(self, alpha: float = 1.0, n_knots_e: int = 5,
                 n_knots_m: int = 6):
        self.alpha, self.ke, self.km = alpha, n_knots_e, n_knots_m

    def _basis(self, df, fit: bool):
        e = df.ce_numeric.to_numpy(float).reshape(-1, 1)
        m = df.precursor_mz.to_numpy(float).reshape(-1, 1)
        if fit:
            self.se_ = _spline(self.ke).fit(e)
            self.sm_ = _spline(self.km).fit(m)
        E, M = self.se_.transform(e), self.sm_.transform(m)
        return np.column_stack([E, M, row_tensor(E, M)])

    def fit(self, df, feats=None):
        X = self._basis(df, fit=True)
        self.mdl_ = Ridge(alpha=self.alpha).fit(X, df.mu.to_numpy(float))
        return self

    def predict(self, df):
        return self.mdl_.predict(self._basis(df, fit=False))


class TierAModel:
    """Interpretable structure model: energy spline x Tier A descriptors.

    Main effects plus the full energy-by-descriptor interaction, so a descriptor
    is allowed to change the SHAPE of the trajectory, not merely shift it.
    """

    def __init__(self, alpha: float = 1.0, n_knots_e: int = 5):
        self.alpha, self.ke = alpha, n_knots_e

    def _basis(self, df, feats, fit: bool):
        e = df.ce_numeric.to_numpy(float).reshape(-1, 1)
        Z = df[feats].to_numpy(float)
        if fit:
            self.se_ = _spline(self.ke).fit(e)
            self.mu_ = Z.mean(0)
            self.sd_ = np.where(Z.std(0) > 0, Z.std(0), 1.0)
        E = self.se_.transform(e)
        Zs = (Z - self.mu_) / self.sd_
        return np.column_stack([E, Zs, row_tensor(E, Zs)])

    def fit(self, df, feats):
        X = self._basis(df, feats, fit=True)
        self.mdl_ = Ridge(alpha=self.alpha).fit(X, df.mu.to_numpy(float))
        return self

    def predict(self, df):
        return self.mdl_.predict(self._basis(df, self.feats_, fit=False))


class FlexibleBenchmark:
    """FLEXIBLE PREDICTIVE BENCHMARK (Tier B gradient boosting).

    Estimates how much nonlinear predictive information a pre-registered
    flexible family recovers from molecular representation. NOT a ceiling.
    """

    def __init__(self, **kw):
        self.kw = kw

    def fit(self, df, feats):
        self.feats_ = list(feats)
        self.mdl_ = HistGradientBoostingRegressor(
            random_state=SEED, early_stopping=False, **self.kw)
        X = df[["ce_numeric", *self.feats_]].to_numpy(float)
        self.mdl_.fit(X, df.mu.to_numpy(float))
        return self

    def predict(self, df):
        X = df[["ce_numeric", *self.feats_]].to_numpy(float)
        return self.mdl_.predict(X)


# ---------------------------------------------------------------------------
# Nested grouped cross-validation
# ---------------------------------------------------------------------------
@dataclass
class Spec:
    """One pre-registered model: constructor, features, and frozen grid."""
    name: str
    ctor: object
    feats: list[str] = field(default_factory=list)
    grid: list[dict] = field(default_factory=lambda: [{}])
    needs_feats: bool = False


def _mae(y, p):
    return float(np.mean(np.abs(y - p)))


# Columns any downstream consumer needs from a prediction frame. Everything
# else -- notably the ~718 Tier B feature columns -- is dropped before the frame
# is returned, so accumulating 30 of them costs megabytes rather than hundreds
# of megabytes. Projection only; no value is altered.
PRED_COLS = ("group_key", "inchikey_first_block", "scaffold_group",
             "cluster_group", "ce_numeric", "mu", "mix", "retention_time_min")


def nested_cv(df: pd.DataFrame, spec: Spec, fold_col: str,
              inner_folds: int = 4, seed: int = SEED,
              keep_cols: tuple[str, ...] = PRED_COLS) -> pd.DataFrame:
    """Outer folds evaluate; inner folds select hyperparameters. Never both.

    Returns one row per observation with its out-of-fold prediction and the
    hyperparameters chosen by the inner loop of its outer fold, projected down
    to `keep_cols` plus the prediction bookkeeping columns.
    """
    from muru.splits import grouped_folds

    group_map = {"fold_S1": "inchikey_first_block", "fold_S2": "scaffold_group",
                 "fold_S3": "cluster_group", "fold_S0": None}
    gcol = group_map[fold_col]

    out = []
    for of in sorted(df[fold_col].unique()):
        tr = df[df[fold_col] != of].copy()
        te = df[df[fold_col] == of].copy()

        if len(spec.grid) > 1:
            if gcol is None:
                rng = np.random.default_rng(seed)
                inner = pd.Series(rng.integers(0, inner_folds, len(tr)),
                                  index=tr.index)
            else:
                inner = grouped_folds(tr[gcol], n_folds=inner_folds, seed=seed)
            scores = []
            for hp in spec.grid:
                errs = []
                for i_f in sorted(inner.unique()):
                    itr, ite = tr[inner != i_f], tr[inner == i_f]
                    m = spec.ctor(**hp)
                    m.fit(itr, spec.feats) if spec.needs_feats else m.fit(itr)
                    if spec.needs_feats:
                        m.feats_ = spec.feats
                    errs.append(_mae(ite.mu.to_numpy(float), m.predict(ite)))
                scores.append(float(np.mean(errs)))
            best = spec.grid[int(np.argmin(scores))]
        else:
            best = spec.grid[0]

        m = spec.ctor(**best)
        m.fit(tr, spec.feats) if spec.needs_feats else m.fit(tr)
        if spec.needs_feats:
            m.feats_ = spec.feats
        pred = m.predict(te)
        cols = [c for c in keep_cols if c in te.columns]
        out.append(te[cols].assign(pred=pred, model=spec.name,
                                   outer_fold=of, hp=str(best)))

    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Compound-level aggregation and bootstrap
# ---------------------------------------------------------------------------
def compound_errors(pred: pd.DataFrame,
                    key: str = "inchikey_first_block") -> pd.DataFrame:
    """Mean |error| per compound. The compound is the unit of analysis."""
    d = pred.assign(ae=(pred.mu - pred.pred).abs(),
                    se=(pred.mu - pred.pred) ** 2)
    return d.groupby(key).agg(mae=("ae", "mean"), mse=("se", "mean"),
                              n=("ae", "size")).reset_index()


def bootstrap_paired(a: pd.DataFrame, b: pd.DataFrame, unit: pd.Series | None = None,
                     n_boot: int = 2000, seed: int = SEED) -> dict:
    """Paired compound-level bootstrap of MAE(a) - MAE(b).

    Resamples the UNIT (compound by default, or scaffold/cluster when the claim
    concerns generalization to unseen scaffolds/clusters). Never resamples
    spectra: all six energies of a molecule move together by construction,
    because the compound is already the aggregation unit.
    """
    m = a.merge(b, on="inchikey_first_block", suffixes=("_a", "_b"))
    if unit is not None:
        m = m.merge(unit.rename("unit").reset_index()
                    .rename(columns={"index": "inchikey_first_block"}),
                    on="inchikey_first_block", how="left")
    else:
        m["unit"] = m.inchikey_first_block

    diff_by_unit = m.groupby("unit").apply(
        lambda g: g.mae_a.mean() - g.mae_b.mean(), include_groups=False)
    units = diff_by_unit.index.to_numpy()
    vals = diff_by_unit.to_numpy(float)

    rng = np.random.default_rng(seed)
    boots = np.array([vals[rng.integers(0, len(vals), len(vals))].mean()
                      for _ in range(n_boot)])
    obs = float(np.mean(m.mae_a) - np.mean(m.mae_b))
    return {
        "diff": obs,
        "lo": float(np.percentile(boots, 2.5)),
        "hi": float(np.percentile(boots, 97.5)),
        "n_units": int(len(units)),
        "frac_units_favouring_a": float((vals < 0).mean()),
    }


def bootstrap_metric(ce: pd.DataFrame, unit: pd.Series | None = None,
                     n_boot: int = 2000, seed: int = SEED) -> dict:
    d = ce.copy()
    d["unit"] = (d.inchikey_first_block if unit is None
                 else d.inchikey_first_block.map(unit).fillna(d.inchikey_first_block))
    per = d.groupby("unit").agg(mae=("mae", "mean"), mse=("mse", "mean"))
    mae, mse = per.mae.to_numpy(), per.mse.to_numpy()
    rng = np.random.default_rng(seed)
    idx = [rng.integers(0, len(mae), len(mae)) for _ in range(n_boot)]
    bm = np.array([mae[i].mean() for i in idx])
    return {"mae": float(mae.mean()),
            "mae_lo": float(np.percentile(bm, 2.5)),
            "mae_hi": float(np.percentile(bm, 97.5)),
            "rmse": float(np.sqrt(mse.mean())),
            "n_units": int(len(mae))}


def grouped_r2(pred: pd.DataFrame) -> float:
    y = pred.mu.to_numpy(float)
    return float(1 - ((y - pred.pred.to_numpy(float)) ** 2).sum()
                 / ((y - y.mean()) ** 2).sum())
