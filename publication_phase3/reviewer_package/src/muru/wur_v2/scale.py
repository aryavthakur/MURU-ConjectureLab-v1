"""Per-trajectory scale fits against a fixed profile, with identifiability summaries.

`fit_scale` reproduces the frozen estimator's grid search and parabolic
refinement for one trajectory. `profile_sse` returns the whole SSE curve on
the frozen log g grid so identifiability can be read from it rather than
from local curvature: a scale is flagged BOUNDARY when the grid minimum is at
an edge, and its likelihood interval is the set of grid values whose SSE is
within `delta` of the minimum, with `delta = chi2_1(0.95) * sigma^2` for an
empirical repeatability sigma.
"""
from __future__ import annotations

import numpy as np

from muru.discovery.estimate import ENERGY_SCALE, LOG_G_GRID, CollapseFit, _best_log_g, _phi_eval

CHI2_1_95 = 3.841458820694124


def profile_sse(fit: CollapseFit, E: np.ndarray, Y: np.ndarray, grid: np.ndarray = LOG_G_GRID) -> np.ndarray:
    """SSE over the grid for each row of Y (n_compounds x n_grid)."""
    Es = np.asarray(E, float) / ENERGY_SCALE
    obs = np.isfinite(Y)
    out = np.empty((Y.shape[0], len(grid)))
    for k, lg in enumerate(grid):
        pred = _phi_eval(fit.phi_u, fit.phi_v, Es / np.exp(lg))
        r = np.where(obs, Y - pred[None, :], 0.0)
        out[:, k] = (r * r).sum(1)
    return out


def fit_scale(fit: CollapseFit, E: np.ndarray, Y: np.ndarray) -> np.ndarray:
    return _best_log_g(np.asarray(E, float), Y, fit.phi_u, fit.phi_v)


def identifiability(fit: CollapseFit, E: np.ndarray, Y: np.ndarray, sigma: float,
                    grid: np.ndarray = LOG_G_GRID) -> dict:
    S = profile_sse(fit, E, Y, grid)
    kmin = S.argmin(1)
    delta = CHI2_1_95 * sigma ** 2
    inside = S <= (S.min(1, keepdims=True) + delta)
    lo = np.array([grid[np.where(r)[0].min()] for r in inside])
    hi = np.array([grid[np.where(r)[0].max()] for r in inside])
    return {"log_g": fit_scale(fit, E, Y), "boundary_low": kmin == 0, "boundary_high": kmin == len(grid) - 1,
            "interval_lo": lo, "interval_hi": hi, "interval_width": hi - lo,
            "interval_touches_edge": (lo <= grid[0]) | (hi >= grid[-1]), "sse_min": S.min(1)}


def sensitivity(fit: CollapseFit, log_g: np.ndarray, E: np.ndarray, h: float = 0.05) -> np.ndarray:
    """d mu / d log g at each energy by central finite differences of the profile (n x n_E)."""
    Es = np.asarray(E, float) / ENERGY_SCALE
    up = _phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(np.asarray(log_g) + h)[:, None])
    dn = _phi_eval(fit.phi_u, fit.phi_v, Es[None, :] / np.exp(np.asarray(log_g) - h)[:, None])
    return (up - dn) / (2 * h)
