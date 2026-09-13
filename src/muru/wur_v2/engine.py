"""Nested cross-validation engine for shared-profile scale models (protocol section 5).

For each outer fold the frozen v1 collapse is fit on the training compounds
only. Hyperparameters are chosen by inner grouped folds in which every inner
training set refits its own collapse and the loss is pooled trajectory
squared error of inner-validation compounds through the inner profile. The
selected configuration is refit on the outer training set and predicts the
held-out compounds from structure alone.

A model is a `ScaleModel`: `grid()` lists configurations, `fit(ctx, cfg)`
learns from a `TrainSet`, `predict(model, keys)` returns log g. Collapse fits
are cached by training key set, so every model on a partition shares them.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from muru.discovery.estimate import ENERGY_SCALE, CollapseFit, _phi_eval, fit_collapse
from muru.wur_v2 import folds as FO

POOLED_ENERGIES = np.array([30.0, 45.0, 60.0, 75.0, 90.0])


@dataclass
class Data:
    cov: pd.DataFrame                 # one row per compound, index group_key
    Y: pd.DataFrame                   # compound x rung mu, index group_key, columns POOLED_ENERGIES
    long: pd.DataFrame                # group_key, ce_numeric, mu
    features: dict = field(default_factory=dict)   # name -> DataFrame indexed by group_key
    kernels: dict = field(default_factory=dict)    # name -> (Index of group_key, full similarity matrix)

    @classmethod
    def load(cls, root) -> "Data":
        cov = pd.read_csv(root / "artifacts/wur_v2/data/compounds.csv").set_index("group_key")
        long = pd.read_csv(root / "artifacts/wur_v2/data/long_aligned.csv")[["group_key", "ce_numeric", "mu"]]
        Y = long.pivot(index="group_key", columns="ce_numeric", values="mu").reindex(index=cov.index,
                                                                                  columns=POOLED_ENERGIES)
        return cls(cov=cov, Y=Y, long=long)


@dataclass
class TrainSet:
    keys: np.ndarray
    log_g: np.ndarray
    w: np.ndarray
    fit: CollapseFit
    data: Data
    group_col: str
    outer_fold: int

    def X(self, name: str, keys=None) -> np.ndarray:
        return self.data.features[name].loc[self.keys if keys is None else keys].to_numpy(float)


class ScaleModel:
    id = "MODEL"

    def grid(self) -> list:
        return [None]

    def fit(self, ts: TrainSet, cfg):
        raise NotImplementedError

    def predict(self, model, ts: TrainSet, keys) -> np.ndarray:
        raise NotImplementedError


_COLLAPSE_CACHE: dict[str, CollapseFit] = {}


def collapse_for(data: Data, keys) -> CollapseFit:
    keys = sorted(keys)
    h = hashlib.sha256("\n".join(keys).encode()).hexdigest()
    if h not in _COLLAPSE_CACHE:
        sub = data.long[data.long["group_key"].isin(set(keys))]
        _COLLAPSE_CACHE[h] = fit_collapse(sub, with_hmain=False)
    return _COLLAPSE_CACHE[h]


def trainset(data: Data, keys, group_col: str, outer_fold: int) -> TrainSet:
    fit = collapse_for(data, keys)
    order = pd.Index(fit.compounds)
    return TrainSet(keys=fit.compounds, log_g=np.log(fit.g_hat), w=fit.weights, fit=fit, data=data,
                    group_col=group_col, outer_fold=outer_fold)


def mu_from_log_g(fit: CollapseFit, log_g: np.ndarray, energies=POOLED_ENERGIES) -> np.ndarray:
    u = (np.asarray(energies, float) / ENERGY_SCALE)[None, :] / np.exp(np.asarray(log_g))[:, None]
    return _phi_eval(fit.phi_u, fit.phi_v, u)


def _sse(pred, Y):
    d = np.where(np.isfinite(Y), pred - Y, 0.0)
    return float((d * d).sum())


@dataclass
class FoldResult:
    test_keys: np.ndarray
    pred: np.ndarray
    log_g_pred: np.ndarray
    cfg: object
    inner_loss: dict
    inner_oof: pd.DataFrame          # training compounds: inner cross-fitted predictions at the chosen cfg


def run_fold(model: ScaleModel, data: Data, train_keys, test_keys, group_col: str, outer_fold: int,
             select: str = "nested") -> FoldResult:
    ts = trainset(data, train_keys, group_col, outer_fold)
    grid = model.grid()
    inner_loss, inner_preds = {}, {}
    train_cov = data.cov.loc[ts.keys].reset_index()
    inner = FO.inner_folds(train_cov, group_col, outer_fold)
    if len(grid) > 1 or select == "nested":
        inner_sets = []
        for k in range(FO.INNER_K):
            tr, va = ts.keys[inner != k], ts.keys[inner == k]
            inner_sets.append((trainset(data, tr, group_col, outer_fold * 10 + k), va))
        for gi, cfg in enumerate(grid):
            sse, rows = 0.0, []
            for its, va in inner_sets:
                m = model.fit(its, cfg)
                lg = model.predict(m, its, va)
                p = mu_from_log_g(its.fit, lg)
                sse += _sse(p, data.Y.loc[va].to_numpy())
                rows.append(pd.DataFrame(p, index=va, columns=POOLED_ENERGIES).assign(log_g_pred=lg))
            inner_loss[gi] = sse
            inner_preds[gi] = pd.concat(rows)
        best = min(inner_loss, key=inner_loss.get)
    else:
        best = 0
    cfg = grid[best]
    m = model.fit(ts, cfg)
    lg = model.predict(m, ts, np.asarray(test_keys))
    pred = mu_from_log_g(ts.fit, lg)
    return FoldResult(test_keys=np.asarray(test_keys), pred=pred, log_g_pred=lg, cfg=cfg,
                      inner_loss={str(grid[i]): v for i, v in inner_loss.items()},
                      inner_oof=inner_preds.get(best, pd.DataFrame()))


@dataclass
class CVRun:
    model_id: str
    partition: str
    pred: pd.DataFrame               # OOF mu, index group_key
    log_g_pred: pd.Series
    fold_of: pd.Series
    cfgs: dict
    inner_oof: pd.DataFrame
    seconds: float


def run_cv(model: ScaleModel, data: Data, assignment: pd.Series, partition: str, group_col: str,
           keys_subset=None) -> CVRun:
    t0 = time.time()
    a = assignment if keys_subset is None else assignment.loc[list(keys_subset)]
    preds, lgs, cfgs, inner = [], [], {}, []
    for f in sorted(a.unique()):
        test = np.array(sorted(a.index[a == f]))
        train = np.array(sorted(a.index[a != f]))
        if len(test) == 0 or len(train) == 0:
            continue
        r = run_fold(model, data, train, test, group_col, int(f))
        preds.append(pd.DataFrame(r.pred, index=r.test_keys, columns=POOLED_ENERGIES))
        lgs.append(pd.Series(r.log_g_pred, index=r.test_keys))
        cfgs[int(f)] = str(r.cfg)
        if len(r.inner_oof):
            inner.append(r.inner_oof.assign(outer_fold=int(f)))
    pred = pd.concat(preds).sort_index()
    return CVRun(model_id=model.id, partition=partition, pred=pred, log_g_pred=pd.concat(lgs).sort_index(),
                 fold_of=a.loc[pred.index], cfgs=cfgs,
                 inner_oof=pd.concat(inner) if inner else pd.DataFrame(), seconds=time.time() - t0)
