"""MURU-WUR-v1 candidate arms: same shared-profile collapse as the frozen
method, different descriptor-to-scale models. Hypotheses are in the ledger
registrations at the bottom.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from muru.discovery import protocol
from muru.wur_stage2 import candidates as CA
from muru.wur_stage2 import cv as CV
from muru.wur_stage2 import folds as FO
from muru.wur_stage2.descriptors2 import SCALE_A2, TIER_A2
from muru.wur_stage2.profile2 import TwoParamRidge

A2_PATH = CV.ART / "wur_stage2b" / "descriptors_a2.csv"
FEATURES_24 = tuple(protocol.FEATURES) + TIER_A2
SCALE_24 = {**protocol.SCALE, **SCALE_A2}


def _a2() -> pd.DataFrame:
    return pd.read_csv(A2_PATH)


def _X24(cov: pd.DataFrame) -> np.ndarray:
    a2 = _a2().set_index("group_key").loc[cov["group_key"]]
    cols = [cov[c].to_numpy(float) / SCALE_24[c] for c in protocol.FEATURES]
    cols += [a2[c].to_numpy(float) / SCALE_24[c] for c in TIER_A2]
    return np.column_stack(cols)


class StableLaw(CV.CollapseArm):
    """log g = c + p * log(ring_count + 1/heteroatom_fraction) - q * log(total_atom_count)."""
    id = "V1A_STABLE_LAW"
    complexity = {"n_features": 3, "n_free_params": 3}

    def _Z(self, cov):
        r = cov["ring_count"].to_numpy(float)
        h = cov["heteroatom_fraction"].to_numpy(float)
        n = cov["total_atom_count"].to_numpy(float)
        return np.column_stack([np.log(r + 1.0 / np.maximum(h, 1e-3)), np.log(n)])

    def fit_g(self, cov, log_g, w, ctx):
        Z = self._Z(cov.reset_index())
        A = np.column_stack([np.ones(len(Z)), Z])
        sw = np.sqrt(w)
        self.coef_, *_ = np.linalg.lstsq(A * sw[:, None], log_g * sw, rcond=None)

    def predict_log_g(self, cov):
        Z = self._Z(cov.reset_index())
        return self.coef_[0] + Z @ self.coef_[1:]

    def diagnostics(self):
        return {"c": float(self.coef_[0]), "p": float(self.coef_[1]), "minus_q": float(self.coef_[2])}


class RichRidge(CV.CollapseArm):
    """Ridge on Tier A + Tier A2 (24 features) with an out-of-fold confidence."""
    id = "V1C_RICH_RIDGE_24"
    complexity = {"n_features": 24, "n_free_params": 25}
    ALPHAS = (0.1, 1.0, 3.0, 10.0, 30.0, 100.0)

    def fit_g(self, cov, log_g, w, ctx):
        c = cov.reset_index()
        X = _X24(c)
        inner = FO.inner_folds(c, ctx["outer_fold"]).to_numpy()
        best, oof = None, {}
        for a in self.ALPHAS:
            sse, o = 0.0, np.zeros(len(X))
            for k in range(FO.INNER_K):
                tr, va = inner != k, inner == k
                m = Ridge(alpha=a).fit(X[tr], log_g[tr], sample_weight=w[tr])
                o[va] = m.predict(X[va])
                sse += float(np.sum(w[va] * (log_g[va] - o[va]) ** 2))
            if best is None or sse < best[0]:
                best = (sse, a); oof = o
        self.alpha_ = best[1]
        self.model_ = Ridge(alpha=self.alpha_).fit(X, log_g, sample_weight=w)
        # confidence: predicted out-of-fold absolute residual, negated
        self.err_model_ = Ridge(alpha=10.0).fit(X, np.abs(log_g - oof))

    def predict_log_g(self, cov):
        return self.model_.predict(_X24(cov.reset_index()))

    def confidence(self, cov):
        return -self.err_model_.predict(_X24(cov.reset_index()))

    def diagnostics(self):
        return {"alpha": self.alpha_}


class RichHGB(CV.CollapseArm):
    """Histogram gradient boosting on 24 features; a black box."""
    id = "V1D_RICH_HGB_24"
    complexity = {"n_features": 24, "n_free_params": "tree ensemble"}
    GRID = ((2, 0.05, 200), (3, 0.05, 200), (3, 0.1, 100), (4, 0.05, 150))

    def fit_g(self, cov, log_g, w, ctx):
        c = cov.reset_index()
        X = _X24(c)
        inner = FO.inner_folds(c, ctx["outer_fold"]).to_numpy()
        best = None
        for depth, lr, n in self.GRID:
            sse = 0.0
            for k in range(FO.INNER_K):
                tr, va = inner != k, inner == k
                m = HistGradientBoostingRegressor(max_depth=depth, learning_rate=lr, max_iter=n,
                                                  random_state=0).fit(X[tr], log_g[tr], sample_weight=w[tr])
                sse += float(np.sum(w[va] * (log_g[va] - m.predict(X[va])) ** 2))
            if best is None or sse < best[0]:
                best = (sse, (depth, lr, n))
        self.params_ = best[1]
        d, lr, n = self.params_
        self.model_ = HistGradientBoostingRegressor(max_depth=d, learning_rate=lr, max_iter=n,
                                                    random_state=0).fit(X, log_g, sample_weight=w)

    def predict_log_g(self, cov):
        return self.model_.predict(_X24(cov.reset_index()))

    def diagnostics(self):
        return {"params": list(self.params_)}


# ---------------------------------------------------------- registrations --
CA.register("V1A_STABLE_LAW", StableLaw, parent="S2A_FROZEN_PIPELINE",
            hypothesis="H-L: the three-input law that recurred in 14/15 frozen-pipeline fold "
                       "searches, refit log-linearly, matches the 12-feature ridge and beats S2A "
                       "by >= 5% with 3 features.",
            rationale="Failure analysis section 5: the gate refused a stable law; selection and "
                      "gate, not the grammar, lost the signal. Form chosen after seeing its "
                      "exploratory CV R2 (0.496), so optimism is possible; the HOLD check guards.",
            generation="MURU-WUR-v1", features={"n_features": 3, "n_free_params": 3},
            model_family="log-linear law on ring_count, heteroatom_fraction, total_atom_count")
CA.register("V1C_RICH_RIDGE_24", RichRidge, parent="LIN_RIDGE_TIERA",
            hypothesis="H-R: twelve labile-bond / H-bonding / saturation descriptors (Tier A2) "
                       "raise held-out log g R2 above the 0.50 Tier A ceiling and lower P1 by "
                       ">= 5% relative to LIN (>= 17% relative to S2A).",
            rationale="Failure analysis: the ceiling is a feature-set limit (all families 0.49-0.50, "
                      "reliability 0.988); n_O and rotatable bonds are the strongest non-size signals.",
            generation="MURU-WUR-v1", features={"n_features": 24, "n_free_params": 25},
            model_family="ridge, alpha by inner scaffold folds; confidence = negated OOF |residual| model",
            tuning_space="alpha in {0.1,1,3,10,30,100}")
CA.register("V1D_RICH_HGB_24", RichHGB, parent="V1C_RICH_RIDGE_24",
            hypothesis="H-NL: nonlinear interactions among the 24 descriptors add >= 15% over S2A "
                       "(the black-box bar) and beat the ridge on the same features.",
            rationale="Boosting matched ridge on Tier A (0.486 vs 0.488); with richer features "
                      "interactions may matter. Black box: interpretable=False.",
            generation="MURU-WUR-v1", features={"n_features": 24, "n_free_params": "tree ensemble"},
            model_family="HistGradientBoosting, grid by inner folds", interpretable=False,
            tuning_space="depth {2,3,4}, lr {0.05,0.1}, iters {100,150,200}")
CA.register("V2A_TWOPARAM_RIDGE", TwoParamRidge, parent="LIN_RIDGE_TIERA",
            hypothesis="H-P2: a second per-compound profile parameter (floor) predicted from "
                       "descriptors lowers held-out trajectory error versus the one-scale collapse.",
            rationale="Stage 2A: H-MAIN rejected, M2/M3 wins. The failure analysis predicts this "
                      "fails (shape parameters are not descriptor-predictable and alias with g); "
                      "run to record the result formally.",
            generation="MURU-WUR-v2", features={"n_features": 12, "n_free_params": 26},
            model_family="two-parameter collapse + two ridges", tuning_space="alpha per target")
