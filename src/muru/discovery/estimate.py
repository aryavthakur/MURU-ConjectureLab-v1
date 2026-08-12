"""Collapse estimation: the T1 alternating fit and the T2 search target.

The master plan's primary target T1 is the joint pair `(Phi, g)` in
`mu_ij ~ Phi(E_j / g(z_i))`, fitted by alternating a shared monotone `Phi`
against per-compound scales `g_i`. The governed symbolic search then runs on
T2 -- the estimated per-compound scale `g_i`, inverse-variance weighted -- which
is exactly what the master plan prescribes for T2 and what makes the planted
exponent in G1 directly testable.

`g` is identified only up to a positive multiplicative constant, so the fitted
scales are normalized to unit geometric mean and every downstream comparison is
made up to positive scaling.

This module reads data. It never reads a planted law.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

ENERGY_SCALE = 30.0
N_ALTERNATIONS = 3
LOG_G_GRID = np.linspace(-1.6, 1.6, 241)


@dataclass
class CollapseFit:
    compounds: np.ndarray          # group_key order
    g_hat: np.ndarray              # per-compound scale, unit geometric mean
    g_var: np.ndarray              # asymptotic variance of g_hat
    weights: np.ndarray            # inverse-variance weights, mean 1
    phi_u: np.ndarray              # Phi knots (u)
    phi_v: np.ndarray              # Phi knots (value)
    resid_sd: float
    n_energies: np.ndarray
    hmain: dict                    # H-MAIN adequacy diagnostics


def _wide(long: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(compounds, E matrix, mu matrix) with NaN for missing cells."""
    p = long.pivot_table(index="group_key", columns="ce_numeric", values="mu")
    p = p.sort_index()
    return p.index.to_numpy(), p.columns.to_numpy(float), p.to_numpy(float)


def _fit_phi(u: np.ndarray, y: np.ndarray, n_knots: int = 60
             ) -> tuple[np.ndarray, np.ndarray]:
    """Shared monotone decreasing shape, as isotonic knots on log-u."""
    ok = np.isfinite(u) & np.isfinite(y) & (u > 0)
    lu, yy = np.log(u[ok]), y[ok]
    order = np.argsort(lu)
    lu, yy = lu[order], yy[order]
    iso = IsotonicRegression(increasing=False, out_of_bounds="clip")
    fitted = iso.fit_transform(lu, yy)
    knots = np.linspace(lu[0], lu[-1], n_knots)
    vals = np.interp(knots, lu, fitted)
    vals = np.minimum.accumulate(vals)  # enforce monotonicity on the knot grid
    return knots, vals


def _phi_eval(knots: np.ndarray, vals: np.ndarray, u: np.ndarray) -> np.ndarray:
    return np.interp(np.log(np.clip(u, 1e-9, 1e9)), knots, vals,
                     left=vals[0], right=vals[-1])


def _best_log_g(E: np.ndarray, Y: np.ndarray, knots: np.ndarray,
                vals: np.ndarray, grid: np.ndarray = LOG_G_GRID) -> np.ndarray:
    """Per-compound scale by vectorized grid search plus parabolic refinement."""
    Es = E / ENERGY_SCALE
    obs = np.isfinite(Y)
    sse = np.empty((Y.shape[0], len(grid)))
    for k, lg in enumerate(grid):
        pred = _phi_eval(knots, vals, Es / np.exp(lg))   # shape (n_energies,)
        r = np.where(obs, Y - pred[None, :], 0.0)
        sse[:, k] = (r * r).sum(1)
    k = np.argmin(sse, axis=1)
    out = grid[k]
    # parabolic refinement on the interior minimum
    interior = (k > 0) & (k < len(grid) - 1)
    if interior.any():
        i = np.where(interior)[0]
        a, b, c = sse[i, k[i] - 1], sse[i, k[i]], sse[i, k[i] + 1]
        denom = a - 2 * b + c
        step = np.where(np.abs(denom) > 1e-15, 0.5 * (a - c) / denom, 0.0)
        out[i] = grid[k[i]] + np.clip(step, -1, 1) * (grid[1] - grid[0])
    return out


def fit_collapse(long: pd.DataFrame, n_alternations: int = N_ALTERNATIONS,
                 n_knots: int = 60, with_hmain: bool = True) -> CollapseFit:
    """Alternating (Phi, g) fit. Two to three alternations, per master plan 13.2.

    `n_knots` controls the resolution of the shared shape and is the knob F2
    varies to test that a conclusion does not depend on an arbitrary choice in
    the estimation pipeline.
    """
    comps, E, Y = _wide(long)
    Es = E / ENERGY_SCALE
    obs = np.isfinite(Y)
    log_g = np.zeros(len(comps))

    for _ in range(n_alternations):
        u = Es[None, :] / np.exp(log_g)[:, None]
        knots, vals = _fit_phi(u[obs], Y[obs], n_knots=n_knots)
        log_g = _best_log_g(E, Y, knots, vals)
        log_g -= log_g.mean()  # unit geometric mean; g is scale-identified only

    u = Es[None, :] / np.exp(log_g)[:, None]
    knots, vals = _fit_phi(u[obs], Y[obs], n_knots=n_knots)
    pred = _phi_eval(knots, vals, u)
    resid = np.where(obs, Y - pred, np.nan)
    n_obs = obs.sum()
    sigma2 = float(np.nansum(resid ** 2) / max(1, n_obs - len(comps) - 1))

    # asymptotic variance of g_i from the local curvature of its own fit
    g = np.exp(log_g)
    h = 1e-3
    d = (_phi_eval(knots, vals, Es[None, :] / (g * np.exp(h))[:, None])
         - _phi_eval(knots, vals, Es[None, :] / (g * np.exp(-h))[:, None])) / (2 * h)
    fisher = np.where(obs, d * d, 0.0).sum(1)
    g_var = sigma2 / np.maximum(fisher, 1e-9)          # variance of log g
    w = 1.0 / np.maximum(g_var, 1e-9)
    w = w / w.mean()

    return CollapseFit(
        compounds=comps, g_hat=g, g_var=g_var, weights=w,
        phi_u=knots, phi_v=vals, resid_sd=float(np.sqrt(sigma2)),
        n_energies=obs.sum(1),
        hmain=hmain_adequacy(long, n_boot=400) if with_hmain else {})


# --------------------------------------------------------------------------
# H-MAIN adequacy: does ONE shared shape with ONE scale per compound suffice?
# --------------------------------------------------------------------------
def _loeo_sq_errors(long: pd.DataFrame, free_shape: bool) -> np.ndarray:
    """Leave-one-energy-out squared errors per compound.

    `free_shape=False` is the collapse model (one scale per compound).
    `free_shape=True` additionally frees a per-compound shape exponent, so the
    comparison charges the extra parameter honestly out of sample.
    """
    comps, E, Y = _wide(long)
    Es = E / ENERGY_SCALE
    obs = np.isfinite(Y)
    out = np.zeros(len(comps))
    counts = np.zeros(len(comps))
    p_grid = np.linspace(0.5, 3.0, 11) if free_shape else np.array([1.0])

    for j_out in range(Y.shape[1]):
        tr = obs.copy()
        tr[:, j_out] = False
        Ytr = np.where(tr, Y, np.nan)
        log_g = np.zeros(len(comps))
        for _ in range(2):
            u = Es[None, :] / np.exp(log_g)[:, None]
            knots, vals = _fit_phi(u[tr], Ytr[tr])
            log_g = _best_log_g(E, Ytr, knots, vals)
            log_g -= log_g.mean()
        u = Es[None, :] / np.exp(log_g)[:, None]
        knots, vals = _fit_phi(u[tr], Ytr[tr])

        best = np.full(len(comps), np.inf)
        best_pred = np.zeros(len(comps))
        for p in p_grid:
            uu = (Es[None, :] / np.exp(log_g)[:, None]) ** p
            pred = _phi_eval(knots, vals, uu)
            r = np.where(tr, Ytr - pred, 0.0)
            sse = (r * r).sum(1)
            take = sse < best
            best = np.where(take, sse, best)
            best_pred = np.where(take, pred[:, j_out], best_pred)

        held = obs[:, j_out]
        out += np.where(held, (Y[:, j_out] - best_pred) ** 2, 0.0)
        counts += held
    return out / np.maximum(counts, 1)


def hmain_adequacy(long: pd.DataFrame, n_boot: int = 400, seed: int = 12345) -> dict:
    """Is a single shared shape with one scale per compound adequate?

    Compares leave-one-energy-out error of the collapse model against the same
    model with a per-compound shape exponent freed. H-MAIN is rejected when the
    lower bound of a compound-clustered bootstrap interval on the ratio exceeds
    1.0 -- an assumption-light rule with no arbitrary inflation constant.
    """
    a = _loeo_sq_errors(long, free_shape=False)
    b = _loeo_sq_errors(long, free_shape=True)
    ratio = float(np.sqrt(a.mean() / max(b.mean(), 1e-15)))

    rng = np.random.default_rng(seed)
    n = len(a)
    boots = np.empty(n_boot)
    for k in range(n_boot):
        idx = rng.integers(0, n, n)
        boots[k] = np.sqrt(a[idx].mean() / max(b[idx].mean(), 1e-15))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "collapse_loeo_rmse": float(np.sqrt(a.mean())),
        "free_shape_loeo_rmse": float(np.sqrt(b.mean())),
        "ratio": ratio,
        "ci": [float(lo), float(hi)],
        "h_main_rejected": bool(lo > 1.0),
        "rule": ("H-MAIN rejected when the lower bound of the 95% compound-"
                 "bootstrap interval on collapse/free-shape LOEO RMSE exceeds 1"),
    }
