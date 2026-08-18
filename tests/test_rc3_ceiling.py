"""RC3 ceiling estimator wiring.

Data is constructed.  No real case is read.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES
from muru.paper_benchmark.rc3_ceiling import (
    CEILING_COVARIATE_ORDER,
    REQUIRED_SKLEARN_VERSION,
    SklearnVersionError,
    assert_sklearn_version,
    build_ceiling_estimator,
    estimate_ceiling,
)
from muru.paper_benchmark.structural_acceptance import (
    CEILING_ESTIMATOR_SPEC,
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
)


def make_frame(n: int = 180, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    scaffold = np.repeat(np.arange(30), n // 30)
    split_by_group = np.array(["train"] * 20 + ["validation"] * 5 + ["test"] * 5)
    frame = pd.DataFrame({
        "split": split_by_group[scaffold],
        "mass": rng.normal(250, 40, n),
        "descriptor": rng.uniform(0, 1, n),
        "descriptor2": rng.uniform(0, 1, n),
        "distractor": rng.normal(0, 1, n),
        "correlated_distractor": rng.normal(0, 1, n),
    })
    return frame


# -----------------------------------------------------------------------
# Frozen spec is imported, not restated
# -----------------------------------------------------------------------

def test_pin_and_params_come_from_the_frozen_spec():
    assert REQUIRED_SKLEARN_VERSION == "1.9.0"
    assert CEILING_ESTIMATOR_SPEC["params"] == {
        "max_iter": 150, "max_depth": 3, "min_samples_leaf": 20, "random_state": 0,
    }
    assert CEILING_ESTIMATOR_SPEC["train_partition"] == "train"
    assert CEILING_ESTIMATOR_SPEC["score_partition"] == "test"


def test_covariate_order_is_the_frozen_grammar_order():
    assert CEILING_COVARIATE_ORDER == GRAMMAR_PRIMITIVES
    assert CEILING_COVARIATE_ORDER == (
        "mass", "descriptor", "descriptor2", "distractor", "correlated_distractor",
    )


def test_estimator_is_built_with_the_frozen_hyperparameters():
    model = build_ceiling_estimator()
    assert type(model).__name__ == "HistGradientBoostingRegressor"
    for key, value in CEILING_ESTIMATOR_SPEC["params"].items():
        assert getattr(model, key) == value


# -----------------------------------------------------------------------
# Version guard
# -----------------------------------------------------------------------

def test_version_guard_passes_on_the_pinned_version():
    assert assert_sklearn_version() == REQUIRED_SKLEARN_VERSION


@pytest.mark.parametrize("wrong", ["1.8.0", "1.9.1", "1.10.0", "2.0.0", "1.9"])
def test_version_guard_triggers_on_any_other_version(monkeypatch, wrong):
    import sklearn
    monkeypatch.setattr(sklearn, "__version__", wrong, raising=False)
    with pytest.raises(SklearnVersionError, match=wrong):
        assert_sklearn_version()


def test_version_guard_triggers_before_the_estimator_is_built(monkeypatch):
    import sklearn
    monkeypatch.setattr(sklearn, "__version__", "1.8.0", raising=False)
    with pytest.raises(SklearnVersionError):
        build_ceiling_estimator()


def test_version_guard_triggers_before_any_ceiling_number_exists(monkeypatch):
    import sklearn
    monkeypatch.setattr(sklearn, "__version__", "0.24.2", raising=False)
    frame = make_frame()
    with pytest.raises(SklearnVersionError):
        estimate_ceiling(frame, np.zeros(len(frame)), 0.5)


def test_missing_sklearn_is_a_loud_failure(monkeypatch):
    # A None entry in sys.modules makes `import sklearn` raise ImportError.
    monkeypatch.setitem(sys.modules, "sklearn", None)
    with pytest.raises(SklearnVersionError, match="not installed"):
        assert_sklearn_version()


# -----------------------------------------------------------------------
# Train / score partitions and gate arithmetic
# -----------------------------------------------------------------------

def test_trains_on_train_and_scores_on_test():
    """A ceiling fit on train must not be a fit on test.

    Poisoning only the test rows moves the ceiling R2; poisoning only the
    validation rows, which are used by neither partition, must not.
    """
    frame = make_frame()
    rng = np.random.default_rng(1)
    target = 2.0 * frame["descriptor"].to_numpy() + rng.normal(0, 0.05, len(frame))

    baseline = estimate_ceiling(frame, target, 0.5).ceiling_r2

    validation_poisoned = target.copy()
    validation_poisoned[frame["split"].to_numpy() == "validation"] += 50.0
    assert estimate_ceiling(frame, validation_poisoned, 0.5).ceiling_r2 == baseline

    test_poisoned = target.copy()
    test_poisoned[frame["split"].to_numpy() == "test"] += 50.0
    assert estimate_ceiling(frame, test_poisoned, 0.5).ceiling_r2 != baseline


def test_ceiling_fraction_and_gate_use_the_frozen_inequalities():
    frame = make_frame()
    rng = np.random.default_rng(2)
    target = 2.0 * frame["descriptor"].to_numpy() + rng.normal(0, 0.05, len(frame))

    estimate = estimate_ceiling(frame, target, candidate_test_r2=0.5)
    assert estimate.ceiling_r2 > 0.05
    assert estimate.ceiling_fraction == pytest.approx(0.5 / estimate.ceiling_r2)
    assert estimate.gate_passed == (estimate.ceiling_fraction >= CEILING_FRACTION_GATE)
    assert estimate.waiver_regime is False


def test_gate_boundary_is_inclusive_at_0_80():
    frame = make_frame()
    rng = np.random.default_rng(3)
    target = 2.0 * frame["descriptor"].to_numpy() + rng.normal(0, 0.05, len(frame))
    ceiling_r2 = estimate_ceiling(frame, target, 0.0).ceiling_r2

    at_gate = estimate_ceiling(frame, target, CEILING_FRACTION_GATE * ceiling_r2)
    assert at_gate.ceiling_fraction == pytest.approx(CEILING_FRACTION_GATE)
    assert at_gate.gate_passed

    below = estimate_ceiling(frame, target, 0.5 * ceiling_r2)
    assert not below.gate_passed


def test_the_low_ceiling_regime_is_detected_strictly_below_0_05():
    """A pure-noise target gives a near-zero ceiling: the waiver REGIME holds.

    A3.5 section 6.9.3 (obligation 17): the regime is only the ceiling half of
    the amended waiver.  The waiver itself additionally requires
    ``candidate_test_r2 > null_threshold[min(complexity, 20)]``, and this
    module deliberately cannot evaluate that -- it has neither the threshold
    table nor the complexity.  Gate 7 is decided only by
    ``evaluate_structural_acceptance``.
    """
    frame = make_frame()
    rng = np.random.default_rng(4)
    target = rng.normal(0, 1, len(frame))

    estimate = estimate_ceiling(frame, target, candidate_test_r2=0.01)
    assert estimate.ceiling_r2 < CEILING_WAIVER_THRESHOLD
    assert estimate.waiver_regime
    assert estimate.in_low_ceiling_waiver_regime


def test_this_module_no_longer_offers_a_gate7_verdict():
    """The superseded unconditional waiver must not be reachable.

    Obligation 17 names ``rc3_ceiling.py``'s previous unconditional form as
    precisely what must NOT be implemented.  A ``ceiling_satisfied`` property
    computed without the candidate floor would be that rule, and would be
    acceptance-favouring wherever the floor fails -- so it does not exist.
    """
    frame = make_frame()
    rng = np.random.default_rng(4)
    estimate = estimate_ceiling(frame, rng.normal(0, 1, len(frame)), 0.01)
    assert not hasattr(estimate, "ceiling_satisfied")
    assert not hasattr(estimate, "waiver_applied")


def test_the_low_ceiling_regime_alone_does_not_decide_gate_7():
    """The regime holds, the floor fails, and Gate 7 must still reject."""
    from muru.paper_benchmark.adequacy import CaseAdequacyStatus
    from muru.paper_benchmark.structural_acceptance import (
        AcceptanceStatus,
        FalsificationResult,
        REQUIRED_HARD_GATES,
        StructuralCandidate,
        evaluate_structural_acceptance,
    )

    frame = make_frame()
    rng = np.random.default_rng(4)
    estimate = estimate_ceiling(frame, rng.normal(0, 1, len(frame)), 0.01)
    assert estimate.waiver_regime

    threshold = {c: 0.10 for c in range(1, 21)}
    candidate = StructuralCandidate(
        valid_r2=0.9,
        complexity=5,
        selection_fraction=25 / 30,
        invalid_fraction=0.0,
        effective_support=frozenset({"mass"}),
        ceiling_fraction=estimate.ceiling_fraction,
        ceiling_r2=estimate.ceiling_r2,
        falsification_results={r: FalsificationResult.PASS for r in REQUIRED_HARD_GATES},
        candidate_test_r2=0.01,   # below the 0.10 bar
    )
    result = evaluate_structural_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED, candidate, threshold
    )
    assert result.status is AcceptanceStatus.REJECTED_CEILING


def test_a_constant_scoring_target_fails_loudly_rather_than_passing_the_waiver():
    """A degenerate test partition is a data defect, not a satisfied gate.

    Returning -inf here would flow into `ceiling_r2 < 0.05` and silently
    satisfy the frozen waiver.
    """
    frame = make_frame()
    target = np.zeros(len(frame))
    target[frame["split"].to_numpy() != "test"] = np.arange(
        (frame["split"].to_numpy() != "test").sum()
    )
    with pytest.raises(ValueError, match="constant on the 'test' partition"):
        estimate_ceiling(frame, target, 0.5)


def test_estimator_params_are_verified_on_the_constructed_object():
    model = build_ceiling_estimator()
    assert type(model).__name__ == "HistGradientBoostingRegressor"
    assert model.max_iter == 150 and model.max_depth == 3
    assert model.min_samples_leaf == 20 and model.random_state == 0


def test_non_positive_ceiling_yields_minus_inf_fraction_not_a_pass():
    frame = make_frame()
    rng = np.random.default_rng(5)
    target = rng.normal(0, 1, len(frame))
    estimate = estimate_ceiling(frame, target, candidate_test_r2=0.9)
    if estimate.ceiling_r2 <= 0.0:
        assert estimate.ceiling_fraction == float("-inf")
        assert not estimate.gate_passed


def test_missing_covariate_is_a_loud_failure():
    frame = make_frame().drop(columns=["distractor"])
    with pytest.raises(ValueError, match="distractor"):
        estimate_ceiling(frame, np.zeros(len(frame)), 0.5)


def test_missing_split_column_is_a_loud_failure():
    frame = make_frame().drop(columns=["split"])
    with pytest.raises(ValueError, match="split"):
        estimate_ceiling(frame, np.zeros(len(frame)), 0.5)


def test_target_length_mismatch_is_a_loud_failure():
    frame = make_frame()
    with pytest.raises(ValueError, match="rows"):
        estimate_ceiling(frame, np.zeros(len(frame) - 1), 0.5)


def test_ceiling_is_deterministic():
    frame = make_frame()
    rng = np.random.default_rng(6)
    target = 2.0 * frame["descriptor"].to_numpy() + rng.normal(0, 0.05, len(frame))
    a = estimate_ceiling(frame, target, 0.5)
    b = estimate_ceiling(frame, target, 0.5)
    assert a == b
