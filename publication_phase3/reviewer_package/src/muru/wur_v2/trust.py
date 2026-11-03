"""Pre-measurement trust signals and selective-prediction evaluation (protocol section 11).

Signals for a query compound relative to a training set, from structure and
training data only: maximum MinMax Morgan similarity, ridge leverage and
Mahalanobis distance on the training-standardized Tier A design, disagreement
between the Tier A and the structural scale predictions, profile sensitivity
at the predicted scale, and an acquisition-domain flag. No spectrum of the
query compound enters.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge

from muru.wur_v2 import engine as EN, metrics as M, scale as SC
from muru.wur_v2.models import kernel_block

SIGNALS = ("dist_1_minus_maxsim", "leverage", "mahalanobis", "disagreement", "sensitivity", "domain_flag")


def signals(data: EN.Data, train_keys, query_keys, logg_ta: np.ndarray, logg_struct: np.ndarray,
            fit: EN.CollapseFit) -> pd.DataFrame:
    train_keys, query_keys = np.asarray(train_keys), np.asarray(query_keys)
    S = kernel_block(data, "MINMAX_MORGAN", query_keys, train_keys)
    same = query_keys[:, None] == train_keys[None, :]
    S = np.where(same, -np.inf, S)                      # a compound is never its own neighbour
    maxsim = S.max(1)
    A = data.features["TIER_A"].loc[train_keys].to_numpy(float)
    mu, sd = A.mean(0), A.std(0) + 1e-12
    Z = (A - mu) / sd
    Q = (data.features["TIER_A"].loc[query_keys].to_numpy(float) - mu) / sd
    G = Z.T @ Z + 1.0 * np.eye(Z.shape[1])
    Ginv = np.linalg.inv(G)
    lev = np.einsum("ij,jk,ik->i", Q, Ginv, Q)
    C = np.cov(Z, rowvar=False) + 1e-3 * np.eye(Z.shape[1])
    Cinv = np.linalg.inv(C)
    mah = np.sqrt(np.einsum("ij,jk,ik->i", Q, Cinv, Q))
    sens = np.sqrt(np.mean(SC.sensitivity(fit, logg_struct, EN.POOLED_ENERGIES) ** 2, axis=1))
    cov = data.cov
    pm = cov.loc[train_keys, "precursor_mz"]
    qm = cov.loc[query_keys, "precursor_mz"].to_numpy()
    flag = ((cov.loc[query_keys, "adduct"].to_numpy() != "[M+H]+") | (qm < pm.min()) | (qm > pm.max())).astype(float)
    return pd.DataFrame({"dist_1_minus_maxsim": 1 - maxsim, "leverage": lev, "mahalanobis": mah,
                         "disagreement": np.abs(np.asarray(logg_ta) - np.asarray(logg_struct)),
                         "sensitivity": sens, "domain_flag": flag}, index=query_keys)


class LearnedTrust:
    """Ridge on log(RMSE + 0.01) and L2 logistic for AF, on standardized signals."""

    def fit(self, X: pd.DataFrame, rmse: np.ndarray):
        self.cols = list(X.columns)
        self.mu, self.sd = X.mean(0).to_numpy(), X.std(0).to_numpy() + 1e-12
        Z = (X.to_numpy() - self.mu) / self.sd
        self.reg = Ridge(alpha=1.0).fit(Z, np.log(rmse + 0.01))
        y = (rmse > M.AF_RMSE).astype(int)
        self.clf = LogisticRegression(C=1.0, max_iter=1000).fit(Z, y) if 0 < y.sum() < len(y) else None
        return self

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        Z = (X[self.cols].to_numpy() - self.mu) / self.sd
        out = pd.DataFrame({"pred_log_rmse": self.reg.predict(Z)}, index=X.index)
        out["p_af"] = self.clf.predict_proba(Z)[:, 1] if self.clf is not None else np.nan
        return out


def selective(pred: np.ndarray, Y: np.ndarray, risk: np.ndarray, coverages=(0.9, 0.8, 0.7)) -> dict:
    """Metrics on the lowest-risk fraction of compounds (ties broken by index order)."""
    order = np.argsort(risk, kind="stable")
    out = {}
    for c in coverages:
        keep = order[: int(round(c * len(order)))]
        s = M.summary(pred[keep], Y[keep])
        out[str(c)] = {"coverage": len(keep) / len(order), "P1": s["P1"], "MRMSE": s["MRMSE"], "AF": s["AF"], "AF_max": s["AF_max"]}
    return out


def pr_auc(score: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(-score, kind="stable")
    y = y[order]
    tp = np.cumsum(y)
    precision = tp / np.arange(1, len(y) + 1)
    return float(np.sum(precision * y) / max(y.sum(), 1))


def calibration(p: np.ndarray, y: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    logit = np.log(p / (1 - p))
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(logit[:, None], y)
    return {"brier": float(np.mean((p - y) ** 2)), "brier_constant": float(np.mean((y.mean() - y) ** 2)),
            "calibration_slope": float(lr.coef_[0, 0]), "calibration_intercept": float(lr.intercept_[0]),
            "mean_p": float(p.mean()), "prevalence": float(y.mean())}
