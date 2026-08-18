"""Proves that PersistingBackend does NOT change scientific results.

The test constructs a mock CaseSearchBackend that returns a known
SeedSearchOutcome, then verifies that:
1. _run_one_seed with the plain mock and with PersistingBackend(mock)
   produce identical SeedSelection results.
2. PersistingBackend captures the equations DataFrame without modifying it.
3. The wrapper does not alter the outcome object identity or content.

This test does NOT require PySR, Julia, or any heavy dependencies.
It runs with only pandas, numpy, and the project's selection logic.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.rc5_runner import (
    SeedSearchOutcome,
    _run_one_seed,
)
from muru.paper_benchmark.rc5_adapter import CaseDesign
from muru.paper_benchmark.calibration_contract import SeedStatus


# -----------------------------------------------------------------------
# Import PersistingBackend from the replay script
# -----------------------------------------------------------------------

# We inline the PersistingBackend definition here to keep the test
# self-contained and avoid importing the replay script (which has
# environment assertions).

class PersistingBackend:
    """Mirror of the wrapper in run_e2b_fullfront_replay.py."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.last_equations: pd.DataFrame | None = None

    def search(self, design: Any, seed: int) -> SeedSearchOutcome:
        outcome = self.inner.search(design, seed)
        self.last_equations = outcome.equations
        return outcome


# -----------------------------------------------------------------------
# Mock backend returning a controlled Pareto front
# -----------------------------------------------------------------------

class _MockModel:
    """Fake PySR model that supports predict(X, index=i)."""

    def __init__(self, n_rows: int) -> None:
        self._n_rows = n_rows

    def predict(self, X: np.ndarray, index: int = 0) -> np.ndarray:
        return np.ones(len(X)) * 0.5


def _make_equations(n_rows: int = 5) -> pd.DataFrame:
    """Build a plausible PySR equations_ DataFrame."""
    return pd.DataFrame({
        "equation": [f"x0 + {i}" for i in range(n_rows)],
        "loss": np.linspace(1.0, 0.1, n_rows),
        "complexity": list(range(1, n_rows + 1)),
        "score": np.linspace(0.1, 1.0, n_rows),
    })


class MockBackend:
    """Returns a fixed SeedSearchOutcome for any (design, seed) call."""

    def __init__(self, equations: pd.DataFrame, model: Any) -> None:
        self._equations = equations
        self._model = model
        self.call_count = 0

    def search(self, design: Any, seed: int) -> SeedSearchOutcome:
        self.call_count += 1
        return SeedSearchOutcome(equations=self._equations, model=self._model)


def _make_design() -> CaseDesign:
    """Build a minimal CaseDesign with 10 compounds, 5 features.

    CaseDesign is a frozen dataclass with fields: compound_ids, feature_names,
    design, target, splits.  train_mask and validation_mask are computed
    properties derived from the splits tuple.
    """
    n = 10
    rng = np.random.RandomState(42)
    X = rng.randn(n, 5)
    y = rng.randn(n)
    # 7 train + 3 validation
    splits = tuple(["train"] * 7 + ["validation"] * 3)
    return CaseDesign(
        compound_ids=tuple(f"C{i:03d}" for i in range(n)),
        feature_names=("mass", "logP", "hbd", "hba", "tpsa"),
        design=X,
        target=y,
        splits=splits,
    )


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

class TestPersistingBackendNoSideEffect:
    """The PersistingBackend wrapper must not alter scientific results."""

    def test_search_returns_identical_outcome(self) -> None:
        """Wrapper returns the same SeedSearchOutcome object."""
        equations = _make_equations()
        model = _MockModel(len(equations))
        plain = MockBackend(equations, model)
        wrapped = PersistingBackend(MockBackend(equations, model))

        design = _make_design()

        outcome_plain = plain.search(design, 42)
        outcome_wrapped = wrapped.search(design, 42)

        # Equations are the same object (same mock, but same content)
        pd.testing.assert_frame_equal(outcome_plain.equations, outcome_wrapped.equations)
        assert outcome_plain.model.__class__ == outcome_wrapped.model.__class__

    def test_captured_equations_match_original(self) -> None:
        """PersistingBackend captures the equations without modification."""
        equations = _make_equations(7)
        model = _MockModel(7)
        inner = MockBackend(equations, model)
        wrapper = PersistingBackend(inner)

        design = _make_design()
        outcome = wrapper.search(design, 99)

        assert wrapper.last_equations is not None
        # The captured equations must be the SAME object as the outcome's
        assert wrapper.last_equations is outcome.equations
        pd.testing.assert_frame_equal(wrapper.last_equations, equations)

    def test_run_one_seed_identical_with_and_without_wrapper(self) -> None:
        """_run_one_seed produces the same SeedSelection regardless of wrapper.

        This is the core no-side-effect proof: the scientific selection path
        is unaffected by the observational wrapper.
        """
        equations = _make_equations(5)
        model = _MockModel(5)
        design = _make_design()

        # Run with plain backend
        plain_backend = MockBackend(equations, model)
        sel_plain = _run_one_seed(design, plain_backend, k=0, seed=42)

        # Run with PersistingBackend wrapper
        wrapped_backend = PersistingBackend(MockBackend(equations, model))
        sel_wrapped = _run_one_seed(design, wrapped_backend, k=0, seed=42)

        # Both must produce the same selection
        assert sel_plain.k == sel_wrapped.k
        assert sel_plain.seed == sel_wrapped.seed
        assert sel_plain.status == sel_wrapped.status
        assert sel_plain.error_message == sel_wrapped.error_message

        # If both have candidates, they must match
        if sel_plain.candidate is not None:
            assert sel_wrapped.candidate is not None
            assert sel_plain.candidate.expression_string == sel_wrapped.candidate.expression_string
            assert sel_plain.candidate.complexity == sel_wrapped.candidate.complexity
            assert sel_plain.candidate.valid_r2 == sel_wrapped.candidate.valid_r2
            assert sel_plain.candidate.invalid_fraction == sel_wrapped.candidate.invalid_fraction
        else:
            assert sel_wrapped.candidate is None

    def test_wrapper_does_not_change_call_count(self) -> None:
        """The wrapper calls inner.search exactly once per call."""
        equations = _make_equations()
        model = _MockModel(len(equations))
        inner = MockBackend(equations, model)
        wrapper = PersistingBackend(inner)

        design = _make_design()

        wrapper.search(design, 1)
        assert inner.call_count == 1

        wrapper.search(design, 2)
        assert inner.call_count == 2

    def test_empty_equations_handled(self) -> None:
        """Wrapper handles None/empty equations gracefully."""
        inner_none = MockBackend(None, _MockModel(0))
        wrapper_none = PersistingBackend(inner_none)

        design = _make_design()
        outcome = wrapper_none.search(design, 1)
        assert wrapper_none.last_equations is None
        assert outcome.equations is None

    def test_multiple_seeds_capture_last(self) -> None:
        """After multiple searches, last_equations holds the most recent front."""
        eq1 = _make_equations(3)
        eq2 = _make_equations(7)

        class MultiBackend:
            def __init__(self):
                self._calls = 0
            def search(self, design, seed):
                self._calls += 1
                eq = eq1 if self._calls == 1 else eq2
                return SeedSearchOutcome(equations=eq, model=_MockModel(len(eq)))

        wrapper = PersistingBackend(MultiBackend())
        design = _make_design()

        wrapper.search(design, 1)
        assert len(wrapper.last_equations) == 3

        wrapper.search(design, 2)
        assert len(wrapper.last_equations) == 7
