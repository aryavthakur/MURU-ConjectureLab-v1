"""Nesting and leakage guards for the v2 engine: a held-out compound never
enters a collapse, a label, a feature fit or an inner validation set it is
scored on; group splits are disjoint; results are deterministic."""
import numpy as np
import pandas as pd
import pytest

from muru.wur_v2 import engine as EN
from muru.wur_v2 import folds as FO
from muru.wur_v2 import models as MO


def synthetic(n=120, groups=30, seed=0):
    rng = np.random.default_rng(seed)
    keys = [f"K{i:04d}" for i in range(n)]
    x = rng.normal(size=n)
    log_g = 0.5 * x + rng.normal(0, 0.1, n)
    E = EN.POOLED_ENERGIES
    u = (E / 30.0)[None, :] / np.exp(log_g)[:, None]
    Y = 1.0 / (1.0 + u ** 2) + rng.normal(0, 0.01, (n, len(E)))
    cov = pd.DataFrame({"scaffold_group": [f"G{i % groups}" for i in range(n)],
                        "strict_cluster": [f"S{i % (groups // 2)}" for i in range(n)],
                        "precursor_mz": 200 + 50 * x}, index=pd.Index(keys, name="group_key"))
    long = pd.DataFrame([(k, e, Y[i, j]) for i, k in enumerate(keys) for j, e in enumerate(E)],
                        columns=["group_key", "ce_numeric", "mu"])
    d = EN.Data(cov=cov, Y=pd.DataFrame(Y, index=keys, columns=E), long=long)
    d.features["X"] = pd.DataFrame({"x": x, "noise": rng.normal(size=n)}, index=keys)
    d.features["TIER_A"] = d.features["X"]
    return d


class Spy(MO.RidgeModel):
    def __init__(self):
        super().__init__("X", alphas=(0.1, 1.0), model_id="SPY")
        self.seen = []

    def fit(self, ts, cfg):
        self.seen.append(("fit", set(ts.keys), set(ts.fit.compounds)))
        return super().fit(ts, cfg)

    def predict(self, m, ts, keys):
        self.seen.append(("predict", set(keys), set(ts.keys)))
        return super().predict(m, ts, keys)


def test_heldout_never_in_training_collapse_or_fit():
    EN._COLLAPSE_CACHE.clear()
    d = synthetic()
    a = FO.grouped(d.cov.reset_index(), "scaffold_group", 1)
    for f in range(FO.K):
        test = set(a.index[a == f])
        spy = Spy()
        EN.run_fold(spy, d, np.array(sorted(a.index[a != f])), np.array(sorted(test)), "scaffold_group", f)
        for kind, s1, s2 in spy.seen:
            if kind == "fit":
                assert not (s1 & test) and not (s2 & test)
            else:
                assert not (s2 & test)            # predicting never uses a held-out compound as training
                assert not (s1 & s2)              # predicted keys are never in the fitted set


def test_inner_validation_keys_excluded_from_inner_collapse():
    EN._COLLAPSE_CACHE.clear()
    d = synthetic()
    a = FO.grouped(d.cov.reset_index(), "scaffold_group", 2)
    spy = Spy()
    EN.run_fold(spy, d, np.array(sorted(a.index[a != 0])), np.array(sorted(a.index[a == 0])), "scaffold_group", 0)
    fits = [s for s in spy.seen if s[0] == "fit"]
    preds = [s for s in spy.seen if s[0] == "predict"]
    # every inner prediction set is disjoint from the collapse the model was trained on
    for kind, pk, trained in preds:
        assert not (pk & trained)
    assert len(fits) == 2 * FO.INNER_K + 1


def test_group_disjoint_partitions_and_mutation():
    d = synthetic()
    cov = d.cov.reset_index()
    a = FO.grouped(cov, "scaffold_group", 3)
    FO.check_disjoint(cov, a, "scaffold_group")
    bad = a.copy()
    g0 = cov.loc[cov.scaffold_group == "G0", "group_key"].tolist()
    bad.loc[g0[0]] = (bad.loc[g0[1]] + 1) % FO.K
    with pytest.raises(ValueError):
        FO.check_disjoint(cov, bad, "scaffold_group")


def test_run_cv_deterministic_and_complete():
    EN._COLLAPSE_CACHE.clear()
    d = synthetic()
    a = FO.grouped(d.cov.reset_index(), "scaffold_group", 4)
    r1 = EN.run_cv(MO.RidgeModel("X", model_id="R"), d, a, "T", "scaffold_group")
    EN._COLLAPSE_CACHE.clear()
    r2 = EN.run_cv(MO.RidgeModel("X", model_id="R"), d, a, "T", "scaffold_group")
    assert set(r1.pred.index) == set(d.cov.index)
    assert np.array_equal(r1.pred.to_numpy(), r2.pred.to_numpy())


def test_signal_is_recovered_and_permutation_destroys_it():
    EN._COLLAPSE_CACHE.clear()
    d = synthetic(n=200, groups=50)
    a = FO.grouped(d.cov.reset_index(), "scaffold_group", 5)
    real = EN.run_cv(MO.RidgeModel("X", model_id="R"), d, a, "T", "scaffold_group")
    perm = EN.run_cv(MO.PermutedFeatures(MO.RidgeModel("X", model_id="R"), "X", 0), d, a, "T", "scaffold_group")
    err = lambda r: float(np.sqrt(np.nanmean((r.pred.loc[d.Y.index].to_numpy() - d.Y.to_numpy()) ** 2)))
    assert err(real) < 0.7 * err(perm)


def test_permutation_seeds_are_distinct():
    d = synthetic(n=60, groups=20)
    base = MO.RidgeModel("X", model_id="R")
    blocks = []
    for s in range(3):
        pm = MO.PermutedFeatures(base, "X", s)
        pm._ensure(d)
        blocks.append(d.features[pm.perm_name].to_numpy())
    assert not np.array_equal(blocks[0], blocks[1]) and not np.array_equal(blocks[1], blocks[2])
