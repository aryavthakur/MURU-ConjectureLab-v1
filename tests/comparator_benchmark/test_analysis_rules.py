"""Synthetic-only tests of the frozen comparator-benchmark decision rules (no MURU or benchmark data)."""
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cb_analysis", ROOT / "scripts/comparator_benchmark/analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def _data(seed=0, n=300):
    rng = np.random.default_rng(seed)
    groups = np.array([f"g{i // 2}" for i in range(n)])
    Y = rng.normal(0.5, 0.1, size=(n, 2))
    return rng, groups, Y


def test_decide_rules():
    assert A.decide([0.90, 0.99]) == "MURU_SUPERIOR"
    assert A.decide([1.01, 1.20]) == "COMPARATOR_SUPERIOR"
    assert A.decide([0.95, 1.05]) == "NO_DEMONSTRATED_DIFFERENCE"
    assert A.decide([0.90, 1.00]) == "NO_DEMONSTRATED_DIFFERENCE"


def test_practical_descriptor_is_separate():
    assert "MURU advantage" in A.practical(0.94)
    assert "comparator advantage" in A.practical(1.06)
    assert "equivalence band" in A.practical(0.97)


def test_ratio_orientation_and_bonferroni_and_shared_replicates():
    rng, groups, Y = _data()
    muru = Y + rng.normal(0, 0.05, Y.shape)
    preds = {"good": Y + rng.normal(0, 0.03, Y.shape), "bad": Y + rng.normal(0, 0.15, Y.shape),
             "same": Y + rng.normal(0, 0.05, Y.shape)}
    out = A.primary_contrasts(muru, preds, Y, groups, n=2000, seed=20260915)
    assert out["bad"]["ratio"] < 1 and out["bad"]["decision"] == "MURU_SUPERIOR"
    assert out["good"]["ratio"] > 1 and out["good"]["decision"] == "COMPARATOR_SUPERIOR"
    for v in out.values():
        assert v["k"] == 3 and abs(v["adjusted_level"] - (1 - 0.05 / 3)) < 1e-12
        lo95, hi95 = v["ratio_ci95"]
        lo, hi = v["ratio_ci_adjusted"]
        assert lo <= lo95 and hi >= hi95
    # shared replicates: identical weights -> a comparator identical to MURU gives a degenerate interval at 1
    same = A.primary_contrasts(muru, {"a": muru.copy(), "b": muru.copy()}, Y, groups, n=500, seed=20260915)
    assert same["a"]["ratio_ci95"] == [1.0, 1.0] == same["b"]["ratio_ci95"]


def test_single_comparator_uses_95():
    rng, groups, Y = _data(1)
    out = A.primary_contrasts(Y + 0.01, {"only": Y + 0.02}, Y, groups, n=200)
    assert out["only"]["adjusted_level"] == 0.95
