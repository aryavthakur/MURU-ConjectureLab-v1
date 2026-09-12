"""MURU-WUR-v2 profile family: a shared shape with TWO per-compound parameters.

    mu_i(E) = a_i + (1 - a_i) * Phi( (E / ENERGY_SCALE) / g_i )        (affine-low)

`Phi` is the shared monotone decreasing shape on log u with Phi -> 1 at
u -> 0 and Phi -> phi_inf at u -> inf, fitted by the same alternating
isotonic scheme as `estimate.fit_collapse`; `g_i` is the horizontal scale
and `a_i` in [0, 1) a per-compound floor that lets a compound's curve sit
above the shared asymptote. Both are estimated per compound on a grid, then
a descriptor model predicts (log g_i, logit a_i) for held-out compounds.

Hypothesis H-P2 (Stage 2B): the H-MAIN rejection and the M2/M3 wins in
Stage 2A come from vertical heterogeneity a single scale cannot absorb,
and a second per-compound parameter that is itself predictable from
descriptors lowers held-out trajectory error.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge

from muru.discovery import protocol
from muru.discovery.estimate import ENERGY_SCALE, _phi_eval
from muru.wur_stage2 import cv as CV
from muru.wur_stage2 import folds as FO

LOG_G_GRID = np.linspace(-2.0, 2.0, 161)
A_GRID = np.linspace(0.0, 0.9, 46)
N_ALT = 3


@dataclass
class Fit2:
    compounds: np.ndarray
    log_g: np.ndarray
    a: np.ndarray
    phi_u: np.ndarray
    phi_v: np.ndarray
    resid_sd: float


def _fit_phi_floor(u, y, a, n_knots=60):
    """Isotonic decreasing shape on log u of the floor-corrected response
    (y - a) / (1 - a), clipped to [0, 1]."""
    z = np.clip((y - a) / np.maximum(1 - a, 1e-6), 0.0, 1.0)
    ok = np.isfinite(u) & np.isfinite(z) & (u > 0)
    lu, zz = np.log(u[ok]), z[ok]
    order = np.argsort(lu)
    lu, zz = lu[order], zz[order]
    iso = IsotonicRegression(increasing=False, out_of_bounds="clip")
    fitted = iso.fit_transform(lu, zz)
    knots = np.linspace(lu[0], lu[-1], n_knots)
    vals = np.minimum.accumulate(np.interp(knots, lu, fitted))
    return knots, vals


def _best_params(E, Y, knots, vals):
    """Joint grid over (log g, a) per compound, unweighted SSE."""
    Es = E / ENERGY_SCALE
    obs = np.isfinite(Y)
    n = Y.shape[0]
    best = np.full(n, np.inf); bg = np.zeros(n); ba = np.zeros(n)
    for lg in LOG_G_GRID:
        s = _phi_eval(knots, vals, Es / np.exp(lg))[None, :]        # (1, nE)
        for a in A_GRID:
            pred = a + (1 - a) * s
            r = np.where(obs, Y - pred, 0.0)
            sse = (r * r).sum(1)
            take = sse < best
            best = np.where(take, sse, best); bg = np.where(take, lg, bg); ba = np.where(take, a, ba)
    return bg, ba


def fit_collapse2(long: pd.DataFrame) -> Fit2:
    p = long.pivot_table(index="group_key", columns="ce_numeric", values="mu").sort_index()
    comps, E, Y = p.index.to_numpy(), p.columns.to_numpy(float), p.to_numpy(float)
    Es = E / ENERGY_SCALE
    obs = np.isfinite(Y)
    log_g = np.zeros(len(comps)); a = np.zeros(len(comps))
    for _ in range(N_ALT):
        u = Es[None, :] / np.exp(log_g)[:, None]
        knots, vals = _fit_phi_floor(u[obs], Y[obs], np.broadcast_to(a[:, None], Y.shape)[obs])
        log_g, a = _best_params(E, Y, knots, vals)
        log_g -= log_g.mean()
    u = Es[None, :] / np.exp(log_g)[:, None]
    knots, vals = _fit_phi_floor(u[obs], Y[obs], np.broadcast_to(a[:, None], Y.shape)[obs])
    pred = a[:, None] + (1 - a[:, None]) * _phi_eval(knots, vals, u)
    resid = np.where(obs, Y - pred, np.nan)
    return Fit2(comps, log_g, a, knots, vals, float(np.sqrt(np.nanmean(resid ** 2))))


class TwoParamRidge(CV.Arm):
    """MURU-WUR-v2a: two-parameter profile, ridge for both parameters."""
    id = "V2A_TWOPARAM_RIDGE"
    complexity = {"n_features": 12, "n_free_params": 26}
    ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)

    def _X(self, cov):
        return np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c] for c in protocol.FEATURES])

    def fit(self, long, cov, ctx):
        self.fit_ = fit_collapse2(long)
        c = cov.set_index("group_key").loc[self.fit_.compounds].reset_index()
        X = self._X(c)
        ta = np.log((self.fit_.a + 0.01) / (1.01 - self.fit_.a))          # logit with guard
        inner = FO.inner_folds(c, ctx["outer_fold"]).to_numpy()
        self.models_ = {}
        for name, t in (("log_g", self.fit_.log_g), ("logit_a", ta)):
            best = None
            for al in self.ALPHAS:
                sse = 0.0
                for k in range(FO.INNER_K):
                    tr, va = inner != k, inner == k
                    m = Ridge(alpha=al).fit(X[tr], t[tr])
                    sse += float(np.sum((t[va] - m.predict(X[va])) ** 2))
                if best is None or sse < best[0]:
                    best = (sse, al)
            self.models_[name] = (Ridge(alpha=best[1]).fit(X, t), best[1])

    def predict_mu(self, cov, energies=CV.POOLED_ENERGIES):
        X = self._X(cov.reset_index() if "group_key" not in cov.columns else cov)
        lg = self.models_["log_g"][0].predict(X)
        a = 1.01 / (1 + np.exp(-self.models_["logit_a"][0].predict(X))) - 0.01
        a = np.clip(a, 0.0, 0.9)
        u = (np.asarray(energies, float) / ENERGY_SCALE)[None, :] / np.exp(lg)[:, None]
        return a[:, None] + (1 - a[:, None]) * _phi_eval(self.fit_.phi_u, self.fit_.phi_v, u)

    def loeo_mae(self, keys, Y, energies=CV.POOLED_ENERGIES):
        """Within-compound LOEO of the two-parameter model on its own grid."""
        E = np.asarray(energies, float)
        out = np.full(len(keys), np.nan)
        for i in range(len(keys)):
            obs = np.where(np.isfinite(Y[i]))[0]
            if len(obs) < 3:
                continue
            errs = []
            for j in obs:
                keep = obs[obs != j]
                yy = np.full_like(Y[i], np.nan); yy[keep] = Y[i][keep]
                lg, a = _best_params(E, yy[None, :], self.fit_.phi_u, self.fit_.phi_v)
                pred = a[0] + (1 - a[0]) * _phi_eval(self.fit_.phi_u, self.fit_.phi_v,
                                                     np.array([E[j] / ENERGY_SCALE / np.exp(lg[0])]))[0]
                errs.append(abs(Y[i][j] - pred))
            out[i] = float(np.mean(errs))
        return out

    def diagnostics(self):
        return {"alpha_log_g": self.models_["log_g"][1], "alpha_logit_a": self.models_["logit_a"][1],
                "resid_sd": self.fit_.resid_sd, "a_median": float(np.median(self.fit_.a)),
                "a_q90": float(np.quantile(self.fit_.a, 0.9))}
