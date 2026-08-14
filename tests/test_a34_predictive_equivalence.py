"""Constructed checks for the A3.4 predictive-equivalence endpoint.

The fixtures are hand-built truth records.  They never materialize a case,
partition, calibration run, or response outcome.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from muru.paper_benchmark import a34_predictive_equivalence as predictive
from muru.paper_benchmark.a34_contract import build_reference_rows
from muru.paper_benchmark.truth import TruthRecord


def constructed_truth(
    family: str = "F08",
    *,
    mathematical_family: str = "mass_affine_descriptor",
    scale: float = 1.0,
    coefficient: float = 0.4,
    mass_exponent: float = 0.5,
    g_by_compound: dict[str, float] | None = None,
) -> TruthRecord:
    """Return a complete constructed truth record with no generated values."""
    return TruthRecord(
        case_id=f"PB|constructed|{family}|r000",
        partition="constructed",
        family=family,
        variant="constructed",
        seeds={},
        phi={},
        g_definition=None,
        g_by_compound={} if g_by_compound is None else g_by_compound,
        descriptor_relationship=None,
        active_variables=["mass", "descriptor"],
        mathematical_family=mathematical_family,
        coefficients={"scale": scale, "coefficient": coefficient},
        exponents={"mass": mass_exponent},
        noise={},
        missingness={},
        scalar_truth_defined=True,
        m0_adequacy_truth="constructed",
        symbolic_truth_kind="constructed",
        applicable_endpoints=[],
        expected_behavior="constructed fixture",
    )


@pytest.fixture(scope="module")
def validated_reference():
    """Build the real Task 2 reference once, including its digest checks."""
    return build_reference_rows()


@pytest.fixture
def fixed_reference(monkeypatch: pytest.MonkeyPatch, validated_reference):
    """Keep scorer tests on the validated frozen rows without regenerating them."""
    monkeypatch.setattr(predictive, "build_reference_rows", lambda: validated_reference)


@pytest.mark.parametrize(
    ("family", "mathematical_family", "expression"),
    [
        ("F01", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F02", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F03", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F04", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F05", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F08", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F09", "mass_saturating_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor / (1 + descriptor))"),
        ("F10", "mass_interaction", "sqrt(mass / 250) * (1 + 0.4 * descriptor * descriptor2)"),
        ("F11", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F12", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F17", "mass_affine_descriptor", "sqrt(mass / 250) * (1 + 0.4 * descriptor)"),
        ("F18", "mass_exponential_descriptor", "sqrt(mass / 250) * exp(0.4 * descriptor / 3)"),
    ],
)
def test_every_a34_predictive_family_scores_its_reconstructed_truth(
    fixed_reference,
    family: str,
    mathematical_family: str,
    expression: str,
):
    """A wrong family law or field reconstruction must not pass this table."""
    result = predictive.score_predictive_equivalence(
        expression,
        constructed_truth(family, mathematical_family=mathematical_family),
    )

    assert result.applicable is True
    assert result.success is True
    assert result.valid_count == 2160
    assert result.c_star == pytest.approx(1.0)
    assert result.rel_rmse == pytest.approx(0.0)
    assert result.pearson_r == pytest.approx(1.0)


def test_positive_scalar_truth_passes_without_reselection_or_refit(fixed_reference):
    """Scale alignment may multiply only; the supplied expression stays fixed."""
    result = predictive.score_predictive_equivalence(
        "2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)",
        constructed_truth(),
    )

    assert result.success is True
    assert result.c_star == pytest.approx(0.5)


def test_reconstruction_uses_truth_fields_not_per_compound_values(fixed_reference):
    """A planted per-compound value would silently leak generated outcomes."""
    result = predictive.score_predictive_equivalence(
        "sqrt(mass / 250) * (1 + 0.4 * descriptor)",
        constructed_truth(g_by_compound={"C000": 1e100, "C001": 1e-100}),
    )

    assert result.success is True
    assert result.c_star == pytest.approx(1.0)


def test_f07_is_not_predictively_applicable():
    """The F07 mass-only safety family never joins the fixed /144 endpoint."""
    result = predictive.score_predictive_equivalence(
        "(mass / 250) ** 0.5",
        constructed_truth(
            "F07", mathematical_family="mass_power", coefficient=0.0
        ),
    )

    assert result.applicable is False
    assert result.success is False
    assert result.failure_reason == "truth family is outside the A3.4 predictive endpoint"


def test_negative_scalar_has_no_positive_valid_points(fixed_reference):
    """A negative multiplier must not be rescued by a negative scale factor."""
    result = predictive.score_predictive_equivalence(
        "-2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)",
        constructed_truth(),
    )

    assert result.success is False
    assert result.valid_count == 0
    assert result.c_star is None


def test_constant_candidate_fails_the_zero_variance_rule(fixed_reference):
    """A constant can align in scale but cannot meet the Pearson condition."""
    result = predictive.score_predictive_equivalence("1.0", constructed_truth())

    assert result.success is False
    assert result.c_star is not None and result.c_star > 0.0
    assert result.pearson_r == 0.0
    assert result.failure_reason == "candidate or truth values have zero variance"


@pytest.mark.parametrize(
    "expression",
    [
        "sqrt(mass / 250) * (1 + 0.4 * descriptor2)",
        "sqrt(mass / 250) * (1 + 0.9 * descriptor)",
        "1 + 2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)",
    ],
)
def test_wrong_shape_wrong_coefficient_and_affine_offset_fail_as_supplied(
    fixed_reference,
    expression: str,
):
    """Selection, coefficient repair, or an intercept fit would make these pass."""
    result = predictive.score_predictive_equivalence(expression, constructed_truth())

    assert result.success is False
    assert result.valid_count == 2160


def test_only_the_one_supplied_expression_controls_the_score(fixed_reference):
    """A better expression elsewhere cannot influence the wrong supplied score."""
    truth = constructed_truth()
    supplied_wrong = predictive.score_predictive_equivalence(
        "sqrt(mass / 250) * (1 + 0.9 * descriptor)", truth
    )
    supplied_exact = predictive.score_predictive_equivalence(
        "sqrt(mass / 250) * (1 + 0.4 * descriptor)", truth
    )

    assert supplied_wrong.success is False
    assert supplied_exact.success is True


@pytest.mark.parametrize(
    "expression",
    [None, "(mass", "sqrt(mass / 250) * unknown", "sqrt(-mass)"],
)
def test_missing_unparseable_unknown_or_nonreal_candidates_fail(fixed_reference, expression):
    """A parser or numerical failure is a failed endpoint observation."""
    result = predictive.score_predictive_equivalence(expression, constructed_truth())

    assert result.success is False
    assert result.c_star is None


def test_valid_set_excludes_only_nonfinite_nonpositive_values_before_scaling():
    """Changing invalid points must not alter the scale or metrics over V."""
    truth = np.linspace(1.0, 2.0, 2160)
    candidate = truth.copy()
    candidate[:4] = (np.nan, np.inf, 0.0, -1.0)
    truth[4:6] = (np.nan, 0.0)

    result = predictive._score_arrays(candidate, truth)

    assert result.success is True
    assert result.valid_count == 2154
    assert result.valid_fraction == pytest.approx(2154 / 2160)
    assert result.c_star == pytest.approx(1.0)
    assert result.rel_rmse == pytest.approx(0.0)
    assert result.pearson_r == pytest.approx(1.0)


def test_2150_valid_points_pass_but_2149_fail_before_scale_alignment():
    """Shrinking V by one point must cross the fixed coverage boundary."""
    truth = np.linspace(1.0, 2.0, 2160)
    at_boundary = truth.copy()
    at_boundary[:10] = np.nan
    outside = truth.copy()
    outside[:11] = np.nan

    passing = predictive._score_arrays(at_boundary, truth)
    failing = predictive._score_arrays(outside, truth)

    assert passing.success is True
    assert passing.valid_count == 2150
    assert passing.c_star == pytest.approx(1.0)
    assert failing.success is False
    assert failing.valid_count == 2149
    assert failing.c_star is None
    assert failing.failure_reason == "fewer than 2150 positive finite reference values"


def test_rmse_and_correlation_thresholds_are_closed_without_tolerance_expansion():
    """A strict comparison on either side of the published boundary is observable."""
    assert predictive._meets_metric_thresholds(0.05, 0.990) is True
    assert predictive._meets_metric_thresholds(math.nextafter(0.05, math.inf), 0.990) is False
    assert predictive._meets_metric_thresholds(0.05, math.nextafter(0.990, -math.inf)) is False


def test_zero_truth_variance_is_formally_a_zero_correlation_failure():
    """A degenerate constructed truth must not yield NaN-dependent behavior."""
    truth = np.ones(2160)
    candidate = np.linspace(1.0, 2.0, 2160)

    result = predictive._score_arrays(candidate, truth)

    assert result.success is False
    assert result.valid_count == 2160
    assert result.pearson_r == 0.0
    assert result.failure_reason == "candidate or truth values have zero variance"


def test_f09_reference_never_evaluates_its_descriptor_pole(fixed_reference, validated_reference):
    """The repaired reference distribution keeps F09 away from descriptor=-1."""
    rows, _ = validated_reference
    result = predictive.score_predictive_equivalence(
        "sqrt(mass / 250) * (1 + 0.4 * descriptor / (1 + descriptor))",
        constructed_truth("F09", mathematical_family="mass_saturating_descriptor"),
    )

    assert all(float(row["descriptor"]) > -1.0 for row in rows)
    assert result.success is True


def test_fixed_denominator_summary_counts_supplied_failures_without_shrinking_144():
    """An unevaluable per-case result can change only the numerator."""
    truth = np.linspace(1.0, 2.0, 2160)
    passed = predictive._score_arrays(truth, truth)
    failed = predictive._score_arrays(-truth, truth)

    summary = predictive.summarize_predictive_equivalence((passed, failed))

    assert summary.successes == 1
    assert summary.denominator == predictive.PREDICTIVE_EQUIVALENCE_DENOMINATOR == 144
    assert summary.rate == pytest.approx(1 / 144)
    assert summary.interval.lower < summary.interval.upper
    assert not hasattr(summary, "gate_passed")
