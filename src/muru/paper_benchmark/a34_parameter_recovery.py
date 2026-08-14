"""A3.4 fixed-denominator parameter-recovery scorer.

This secondary endpoint accepts only a supplied candidate expression and a
``TruthRecord``.  It deliberately contains no candidate search, selection,
partition materialization, calibration, or outcome-record access.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from numbers import Integral
from typing import Mapping, NamedTuple, Sequence

import sympy

from .g2_contract import GRAMMAR_PRIMITIVES, _PRIMITIVE_SYMBOLS, _safe_parse
from .truth import TruthRecord

__all__ = [
    "CANONICAL_ANCHOR",
    "PARAMETER_RECOVERY_DENOMINATOR",
    "P_MASS_DENOMINATOR",
    "C_DESC_DENOMINATOR",
    "P_MASS_TOLERANCE",
    "C_DESC_TOLERANCE",
    "PARAMETER_RECOVERY_FAMILIES",
    "C_DESC_FAMILIES",
    "WilsonInterval",
    "ParameterRecoveryResult",
    "ParameterRecoverySummary",
    "score_parameter_recovery",
    "summarize_parameter_recovery",
    "wilson_interval_95",
]


# These values are bound by A3.4.  They are descriptive reporting constants,
# not decision gates.
PARAMETER_RECOVERY_DENOMINATOR = 156
P_MASS_DENOMINATOR = PARAMETER_RECOVERY_DENOMINATOR
C_DESC_DENOMINATOR = 84
P_MASS_TOLERANCE = 0.15
C_DESC_TOLERANCE = 0.10

CANONICAL_ANCHOR: dict[str, float] = {
    "mass": 250.0,
    "descriptor": 0.0,
    "descriptor2": 0.0,
    "distractor": 0.0,
    "correlated_distractor": 0.0,
}

PARAMETER_RECOVERY_FAMILIES = frozenset(
    {
        "F01",
        "F02",
        "F03",
        "F04",
        "F05",
        "F07",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F17",
        "F18",
    }
)

# This is intentionally keyed by TruthRecord.family, not by mathematical
# family metadata or by the expression's apparent shape.
C_DESC_FAMILIES = frozenset({"F08", "F09", "F10", "F11", "F12", "F17", "F18"})

_ANCHOR_SUBSTITUTIONS = {
    _PRIMITIVE_SYMBOLS["mass"]: sympy.Integer(250),
    _PRIMITIVE_SYMBOLS["descriptor"]: sympy.Integer(0),
    _PRIMITIVE_SYMBOLS["descriptor2"]: sympy.Integer(0),
    _PRIMITIVE_SYMBOLS["distractor"]: sympy.Integer(0),
    _PRIMITIVE_SYMBOLS["correlated_distractor"]: sympy.Integer(0),
}
_ALLOWED_SYMBOLS = frozenset(_PRIMITIVE_SYMBOLS[name] for name in GRAMMAR_PRIMITIVES)
_P_MASS_SYMBOL = _PRIMITIVE_SYMBOLS["mass"]
_DESCRIPTOR_SYMBOL = _PRIMITIVE_SYMBOLS["descriptor"]
_DESCRIPTOR2_SYMBOL = _PRIMITIVE_SYMBOLS["descriptor2"]
_WILSON_Z_95 = 1.959963984540054


class WilsonInterval(NamedTuple):
    """Two-sided 95% Wilson score interval."""

    lower: float
    upper: float


@dataclass(frozen=True)
class ParameterRecoveryResult:
    """One supplied expression scored at the A3.4 neutral anchor."""

    p_mass: float | None
    c_desc: float | None
    p_mass_success: bool
    c_desc_success: bool | None
    c_desc_applicable: bool
    joint_success: bool
    failure_reason: str | None = None


@dataclass(frozen=True)
class ParameterRecoverySummary:
    """Descriptive fixed-denominator parameter-recovery report."""

    joint_successes: int
    p_mass_successes: int
    c_desc_successes: int
    joint_denominator: int
    p_mass_denominator: int
    c_desc_denominator: int
    joint_rate: float
    p_mass_rate: float
    c_desc_rate: float
    joint_interval: WilsonInterval
    p_mass_interval: WilsonInterval
    c_desc_interval: WilsonInterval


def wilson_interval_95(successes: int, total: int) -> WilsonInterval:
    """Return the two-sided 95% Wilson score interval for a valid count."""
    if (
        isinstance(successes, bool)
        or isinstance(total, bool)
        or not isinstance(successes, Integral)
        or not isinstance(total, Integral)
        or total <= 0
        or successes < 0
        or successes > total
    ):
        raise ValueError("successes and total must be valid non-negative binomial counts")

    p_hat = successes / total
    denominator = 1.0 + _WILSON_Z_95**2 / total
    center = (p_hat + _WILSON_Z_95**2 / (2.0 * total)) / denominator
    margin = (
        _WILSON_Z_95
        * sqrt(
            (p_hat * (1.0 - p_hat) + _WILSON_Z_95**2 / (4.0 * total))
            / total
        )
        / denominator
    )
    return WilsonInterval(
        lower=max(0.0, center - margin),
        upper=min(1.0, center + margin),
    )


def score_parameter_recovery(
    expression: str | None,
    truth: TruthRecord,
) -> ParameterRecoveryResult:
    """Score a frozen candidate expression against one constructed truth.

    Parsing is delegated to the frozen G2 parser and its fixed primitive
    symbols.  Any unknown free variable, failed evaluation, non-real or
    non-finite result, or nonpositive anchor value is a non-success.
    """
    family = getattr(truth, "family", None)
    c_desc_applicable = family in C_DESC_FAMILIES

    if family not in PARAMETER_RECOVERY_FAMILIES:
        return _failed_result(
            c_desc_applicable=c_desc_applicable,
            reason="truth family is outside the A3.4 parameter-recovery endpoint",
        )

    parsed = _parse_candidate(expression)
    if parsed is None:
        return _failed_result(
            c_desc_applicable=c_desc_applicable,
            reason="expression is missing, unparseable, or uses an unknown variable",
        )

    base_expression = _at_anchor(parsed)
    base = _finite_real_expression(base_expression)
    if base is None or base <= 0.0:
        return _failed_result(
            c_desc_applicable=c_desc_applicable,
            reason="anchor value is not a finite, strictly positive real number",
        )

    p_mass_expression = _scaled_derivative(parsed, _P_MASS_SYMBOL, factor=250)
    p_mass = _finite_real_expression(p_mass_expression / base_expression)
    p_truth = _truth_parameter(truth, "exponents", "mass")
    p_mass_success = (
        p_mass is not None
        and p_truth is not None
        and _within_absolute_tolerance(
            p_mass_expression / base_expression,
            p_truth[1],
            P_MASS_TOLERANCE,
        )
    )

    c_desc: float | None = None
    c_desc_success: bool | None = None
    if c_desc_applicable:
        c_desc_expression = _c_desc_expression(parsed, family)
        c_desc = _finite_real_expression(c_desc_expression / base_expression)
        c_truth = _truth_parameter(truth, "coefficients", "coefficient")
        c_desc_success = (
            c_desc is not None
            and c_truth is not None
            and _within_absolute_tolerance(
                c_desc_expression / base_expression,
                c_truth[1],
                C_DESC_TOLERANCE,
            )
        )

    joint_success = p_mass_success and (
        not c_desc_applicable or c_desc_success is True
    )
    return ParameterRecoveryResult(
        p_mass=p_mass,
        c_desc=c_desc,
        p_mass_success=p_mass_success,
        c_desc_success=c_desc_success,
        c_desc_applicable=c_desc_applicable,
        joint_success=joint_success,
        failure_reason=None if joint_success else _failure_reason(
            p_mass=p_mass,
            p_truth=p_truth,
            p_success=p_mass_success,
            c_desc=c_desc,
            c_desc_applicable=c_desc_applicable,
            c_success=c_desc_success,
        ),
    )


def summarize_parameter_recovery(
    results: Sequence[ParameterRecoveryResult],
) -> ParameterRecoverySummary:
    """Summarize supplied per-case results with A3.4's fixed denominators.

    The sequence is never used as a denominator.  In particular, mass-only
    records cannot contribute to the descriptor numerator or alter its /84.
    """
    for index, result in enumerate(results):
        if not isinstance(result, ParameterRecoveryResult):
            raise ValueError(
                f"result {index} is {type(result).__name__}, "
                "expected ParameterRecoveryResult"
            )

    joint_successes = sum(result.joint_success for result in results)
    p_mass_successes = sum(result.p_mass_success for result in results)
    c_desc_successes = sum(
        result.c_desc_applicable and result.c_desc_success is True
        for result in results
    )

    return ParameterRecoverySummary(
        joint_successes=joint_successes,
        p_mass_successes=p_mass_successes,
        c_desc_successes=c_desc_successes,
        joint_denominator=PARAMETER_RECOVERY_DENOMINATOR,
        p_mass_denominator=P_MASS_DENOMINATOR,
        c_desc_denominator=C_DESC_DENOMINATOR,
        joint_rate=joint_successes / PARAMETER_RECOVERY_DENOMINATOR,
        p_mass_rate=p_mass_successes / P_MASS_DENOMINATOR,
        c_desc_rate=c_desc_successes / C_DESC_DENOMINATOR,
        joint_interval=wilson_interval_95(
            joint_successes, PARAMETER_RECOVERY_DENOMINATOR
        ),
        p_mass_interval=wilson_interval_95(
            p_mass_successes, P_MASS_DENOMINATOR
        ),
        c_desc_interval=wilson_interval_95(
            c_desc_successes, C_DESC_DENOMINATOR
        ),
    )


def _failed_result(
    *,
    c_desc_applicable: bool,
    reason: str,
) -> ParameterRecoveryResult:
    return ParameterRecoveryResult(
        p_mass=None,
        c_desc=None,
        p_mass_success=False,
        c_desc_success=False if c_desc_applicable else None,
        c_desc_applicable=c_desc_applicable,
        joint_success=False,
        failure_reason=reason,
    )


def _parse_candidate(expression: str | None) -> sympy.Expr | None:
    if not isinstance(expression, str) or not expression.strip():
        return None
    parsed = _safe_parse(expression)
    if parsed is None or not isinstance(parsed, sympy.Expr):
        return None
    if not parsed.free_symbols.issubset(_ALLOWED_SYMBOLS):
        return None
    return _rationalize_decimal_literals(parsed)


def _rationalize_decimal_literals(expression: sympy.Expr) -> sympy.Expr:
    """Preserve decimal candidate literals for exact closed-boundary checks.

    G2's frozen parser is still the sole parser.  This only represents its
    already parsed decimal constants as their written rational values, so a
    stated closed tolerance is neither widened nor narrowed by binary float
    roundoff.
    """
    replacements: dict[sympy.Float, sympy.Rational] = {}
    for value in expression.atoms(sympy.Float):
        try:
            replacements[value] = sympy.Rational(str(value))
        except (TypeError, ValueError, ZeroDivisionError):
            # Leave NaN/infinite literals in place; finite evaluation rejects
            # them deterministically below.
            continue
    return expression.xreplace(replacements)


def _at_anchor(expression: sympy.Expr) -> sympy.Expr:
    try:
        return expression.subs(_ANCHOR_SUBSTITUTIONS)
    except Exception:
        return sympy.nan


def _scaled_derivative(
    expression: sympy.Expr,
    symbol: sympy.Symbol,
    *,
    factor: int,
) -> sympy.Expr:
    try:
        return sympy.Integer(factor) * _at_anchor(sympy.diff(expression, symbol))
    except Exception:
        return sympy.nan


def _c_desc_expression(expression: sympy.Expr, family: str) -> sympy.Expr:
    try:
        if family == "F10":
            return _at_anchor(sympy.diff(expression, _DESCRIPTOR_SYMBOL, _DESCRIPTOR2_SYMBOL))
        derivative = _at_anchor(sympy.diff(expression, _DESCRIPTOR_SYMBOL))
        return 3 * derivative if family == "F18" else derivative
    except Exception:
        return sympy.nan


def _finite_real_expression(expression: sympy.Expr) -> float | None:
    if not isinstance(expression, sympy.Basic) or expression.is_real is False:
        return None
    if expression.free_symbols:
        return None
    try:
        numeric = float(expression)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if isfinite(numeric) else None


def _truth_parameter(
    truth: TruthRecord,
    attribute: str,
    key: str,
) -> tuple[float, sympy.Rational] | None:
    values = getattr(truth, attribute, None)
    if not isinstance(values, Mapping):
        return None
    try:
        raw_value = values[key]
    except (KeyError, TypeError):
        return None
    if isinstance(raw_value, bool):
        return None
    try:
        numeric = float(raw_value)
        exact = sympy.Rational(str(raw_value))
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if not isfinite(numeric):
        return None
    return numeric, exact


def _within_absolute_tolerance(
    estimate: sympy.Expr,
    truth: sympy.Rational,
    tolerance: float,
) -> bool:
    """Check the exact closed A3.4 interval without an epsilon allowance."""
    try:
        difference = sympy.Abs(estimate - truth)
        within = difference <= sympy.Rational(str(tolerance))
    except Exception:
        return False
    return within is True or within is sympy.S.true


def _failure_reason(
    *,
    p_mass: float | None,
    p_truth: tuple[float, sympy.Rational] | None,
    p_success: bool,
    c_desc: float | None,
    c_desc_applicable: bool,
    c_success: bool | None,
) -> str:
    if p_mass is None:
        return "mass derivative is not finite and real at the anchor"
    if p_truth is None:
        return "mass truth exponent is not finite and real"
    if not p_success:
        return "mass exponent is outside the A3.4 tolerance"
    if c_desc_applicable and c_desc is None:
        return "descriptor derivative is not finite and real at the anchor"
    if c_desc_applicable and c_success is not True:
        return "descriptor coupling is outside the A3.4 tolerance or truth is invalid"
    return "parameter recovery failed"
