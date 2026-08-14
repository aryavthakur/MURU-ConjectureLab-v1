"""Constructed checks for the A3.4 parameter-recovery endpoint.

These tests use hand-built ``TruthRecord`` instances only.  They never
materialize a benchmark case, partition, calibration world, or outcome record.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.a34_parameter_recovery import (
    C_DESC_DENOMINATOR,
    PARAMETER_RECOVERY_DENOMINATOR,
    ParameterRecoveryResult,
    score_parameter_recovery,
    summarize_parameter_recovery,
    wilson_interval_95,
)
from muru.paper_benchmark.truth import TruthRecord


def constructed_truth(
    family: str,
    *,
    p_mass: float = 0.5,
    coefficient: float = 0.4,
    mathematical_family: str | None = "constructed",
) -> TruthRecord:
    """Return a complete synthetic truth record with no generated outcome."""
    return TruthRecord(
        case_id=f"PB|constructed|{family}|r000",
        partition="constructed",
        family=family,
        variant="constructed",
        seeds={},
        phi={},
        g_definition=None,
        g_by_compound={},
        descriptor_relationship=None,
        active_variables=["mass"],
        mathematical_family=mathematical_family,
        coefficients={"coefficient": coefficient},
        exponents={"mass": p_mass},
        noise={},
        missingness={},
        scalar_truth_defined=True,
        m0_adequacy_truth="constructed",
        symbolic_truth_kind="constructed",
        applicable_endpoints=[],
        expected_behavior="constructed fixture",
    )


@pytest.mark.parametrize(
    ("expression", "truth"),
    [
        (
            "sqrt(mass / 250) * (1 + 0.4 * descriptor)",
            constructed_truth("F08"),
        ),
        (
            "(mass / 250) ** 0.6",
            constructed_truth("F07", p_mass=0.6),
        ),
        (
            "sqrt(mass / 250) * (1 + 0.4 * descriptor / (1 + descriptor))",
            constructed_truth("F09"),
        ),
        (
            "sqrt(mass / 250) * (1 + 0.4 * descriptor * descriptor2)",
            constructed_truth("F10"),
        ),
        (
            "sqrt(mass / 250) * exp(0.4 * descriptor / 3)",
            constructed_truth("F18"),
        ),
    ],
)
def test_exact_a34_family_truth_recovers_its_applicable_parameters(
    expression: str,
    truth: TruthRecord,
):
    """Using the wrong frozen family operator must break this recovery."""
    result = score_parameter_recovery(expression, truth)

    assert result.p_mass_success
    assert result.joint_success
    if truth.family == "F07":
        assert result.c_desc_applicable is False
        assert result.c_desc_success is None
    else:
        assert result.c_desc_applicable is True
        assert result.c_desc_success is True


def test_expanded_positive_rescaling_preserves_recovered_parameters():
    """Dropping normalization would make an equivalent positive scale fail."""
    result = score_parameter_recovery(
        "7.25 * (sqrt(mass / 250) + 0.4 * sqrt(mass / 250) * descriptor)",
        constructed_truth("F08"),
    )

    assert result.p_mass == pytest.approx(0.5)
    assert result.c_desc == pytest.approx(0.4)
    assert result.joint_success


def test_c_desc_operator_comes_from_truth_family_not_mathematical_family():
    """A metadata-family shortcut would use the wrong derivative operator."""
    interaction = "sqrt(mass / 250) * (1 + 0.4 * descriptor * descriptor2)"

    f08 = score_parameter_recovery(
        interaction,
        constructed_truth("F08", mathematical_family="mass_interaction"),
    )
    f10 = score_parameter_recovery(
        interaction,
        constructed_truth("F10", mathematical_family="mass_affine_descriptor"),
    )

    assert f08.p_mass_success
    assert f08.c_desc_success is False
    assert f08.joint_success is False
    assert f10.c_desc_success is True
    assert f10.joint_success is True


def test_mass_tolerance_boundary_is_inclusive_but_next_value_fails():
    """Widening the stated 0.15 mass tolerance would admit the second law."""
    truth = constructed_truth("F07", p_mass=0.5)

    at_boundary = score_parameter_recovery("(mass / 250) ** (13 / 20)", truth)
    outside = score_parameter_recovery(
        "(mass / 250) ** (650001 / 1000000)",
        truth,
    )

    assert at_boundary.p_mass == pytest.approx(0.65)
    assert at_boundary.p_mass_success is True
    assert at_boundary.joint_success is True
    assert outside.p_mass_success is False
    assert outside.joint_success is False


def test_c_desc_tolerance_boundary_is_inclusive_but_next_value_fails():
    """Widening the stated 0.10 descriptor tolerance admits the second law."""
    truth = constructed_truth("F08", coefficient=0.4)

    at_boundary = score_parameter_recovery(
        "sqrt(mass / 250) * (1 + 0.5 * descriptor)", truth
    )
    outside = score_parameter_recovery(
        "sqrt(mass / 250) * (1 + 0.5000000000000001 * descriptor)", truth
    )

    assert at_boundary.c_desc == pytest.approx(0.5)
    assert at_boundary.c_desc_success is True
    assert at_boundary.joint_success is True
    assert outside.c_desc_success is False
    assert outside.joint_success is False


@pytest.mark.parametrize(
    "expression",
    [
        None,
        "(mass",
        "sqrt(mass / 250) * unknown",
        "sqrt(mass / 250) * (1 + sqrt(descriptor))",
        "-sqrt(mass / 250)",
    ],
)
def test_missing_unknown_nonfinite_or_nonpositive_candidate_is_not_a_success(
    expression: str | None,
):
    """Invalid parsing, anchor, or derivative data must never shrink a rate."""
    result = score_parameter_recovery(expression, constructed_truth("F08"))

    assert result.joint_success is False
    if expression in (
        None,
        "(mass",
        "sqrt(mass / 250) * unknown",
        "-sqrt(mass / 250)",
    ):
        assert result.p_mass_success is False
        assert result.c_desc_success is False
    else:
        assert result.c_desc_success is False


def test_summary_keeps_fixed_denominators_and_excludes_mass_only_c_desc():
    """Filtering unevaluable or mass-only records must not change /156 or /84."""
    mass_only = score_parameter_recovery(
        "(mass / 250) ** 0.6", constructed_truth("F07", p_mass=0.6)
    )
    descriptor = score_parameter_recovery(
        "sqrt(mass / 250) * (1 + 0.4 * descriptor)", constructed_truth("F08")
    )

    summary = summarize_parameter_recovery((mass_only, descriptor))

    assert isinstance(mass_only, ParameterRecoveryResult)
    assert summary.joint_successes == 2
    assert summary.p_mass_successes == 2
    assert summary.c_desc_successes == 1
    assert summary.joint_denominator == PARAMETER_RECOVERY_DENOMINATOR == 156
    assert summary.p_mass_denominator == PARAMETER_RECOVERY_DENOMINATOR == 156
    assert summary.c_desc_denominator == C_DESC_DENOMINATOR == 84
    assert summary.joint_rate == pytest.approx(2 / 156)
    assert summary.p_mass_rate == pytest.approx(2 / 156)
    assert summary.c_desc_rate == pytest.approx(1 / 84)
    assert summary.joint_interval.lower < summary.joint_interval.upper
    assert summary.p_mass_interval.lower < summary.p_mass_interval.upper
    assert summary.c_desc_interval.lower < summary.c_desc_interval.upper
    assert not hasattr(summary, "gate_passed")


def test_wilson_interval_is_a_two_sided_95_percent_interval():
    """Reporting must not quietly substitute a one-sided gate bound."""
    empty = wilson_interval_95(0, 156)
    perfect = wilson_interval_95(156, 156)

    assert empty.lower == 0.0
    assert 0.0 < empty.upper < 0.1
    assert 0.9 < perfect.lower < 1.0
    assert perfect.upper == pytest.approx(1.0)
