"""Exact estimands: P1 is not mean RMSE; the bootstrap resamples clusters and recomputes P1."""
import numpy as np
import pytest

from muru.wur_v2 import metrics as M


def _toy():
    Y = np.array([[0.9, 0.5, 0.3], [0.8, 0.6, np.nan], [0.7, 0.4, 0.2], [0.95, 0.9, 0.85]])
    pred = Y + np.array([[0.1, -0.1, 0.0], [0.3, 0.3, 0.0], [0.0, 0.0, 0.05], [-0.4, 0.2, 0.1]])
    return Y, pred


def test_p1_pools_cells_and_differs_from_mean_rmse():
    Y, pred = _toy()
    E = M.errors(pred, Y)
    cells = E[np.isfinite(E)]
    assert M.p1(E) == pytest.approx(np.sqrt(np.mean(cells ** 2)))
    s = M.summary(pred, Y)
    per = [np.sqrt(np.nanmean(r ** 2)) for r in E]
    assert s["MRMSE"] == pytest.approx(np.mean(per))
    assert abs(s["P1"] - s["MRMSE"]) > 1e-3          # mutation guard: confusing the two must fail


def test_missing_cells_are_excluded_not_zero():
    Y, pred = _toy()
    E = M.errors(pred, Y)
    assert np.isnan(E[1, 2])
    assert M.summary(pred, Y)["n_cells"] == 11


def test_absolute_failure_thresholds():
    Y = np.zeros((3, 5))
    pred = np.vstack([np.full(5, 0.21), np.array([0.31, 0, 0, 0, 0]), np.full(5, 0.1)])
    s = M.summary(pred, Y)
    assert s["AF"] == pytest.approx(1 / 3)
    assert s["AF_max"] == pytest.approx(1 / 3)
    assert s["AF_union"] == pytest.approx(2 / 3)


def test_bootstrap_point_values_and_cluster_unit():
    rng = np.random.default_rng(0)
    Y = rng.uniform(0.2, 0.9, size=(60, 5))
    pc, pr = Y + rng.normal(0, 0.05, Y.shape), Y + rng.normal(0, 0.08, Y.shape)
    clusters = np.repeat(np.arange(12), 5)
    b = M.cluster_bootstrap(pc, pr, Y, clusters, n=400)
    assert b["P1_cand"] == pytest.approx(M.p1(M.errors(pc, Y)))
    assert b["P1_ratio"] == pytest.approx(b["P1_cand"] / b["P1_ref"])
    assert b["P1_ratio_ci"][0] < b["P1_ratio"] < b["P1_ratio_ci"][1]
    assert b["n_clusters"] == 12
    # one cluster per compound gives narrower intervals than 12 clusters of 5 correlated compounds
    Yc = np.repeat(rng.uniform(0.2, 0.9, size=(12, 5)), 5, axis=0)
    shift = np.repeat(rng.normal(0, 0.1, size=(12, 1)), 5, axis=0)
    pc2 = Yc + shift
    pr2 = Yc + 0.5 * shift + rng.normal(0, 0.02, Yc.shape)
    wide = M.cluster_bootstrap(pc2, pr2, Yc, clusters, n=800)
    narrow = M.cluster_bootstrap(pc2, pr2, Yc, np.arange(60), n=800)
    w = wide["P1_diff_ci"][1] - wide["P1_diff_ci"][0]
    nw = narrow["P1_diff_ci"][1] - narrow["P1_diff_ci"][0]
    assert w > nw


def test_bootstrap_recomputes_p1_not_mean_rmse():
    # construct a case where P1 difference and mean RMSE difference have opposite signs
    Y = np.zeros((4, 4))
    pc = np.vstack([np.full(4, 0.5), np.zeros((3, 4))])           # one large error, rest perfect
    pr = np.full((4, 4), 0.2)                                        # uniform moderate error
    b = M.cluster_bootstrap(pc, pr, Y, np.arange(4), n=200)
    assert b["P1_diff"] > 0 > b["MRMSE_diff"]
