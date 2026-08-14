"""A3.4 predictive-equivalence scoring on the frozen reference covariates.

This is a score-only secondary endpoint.  It accepts one already supplied
expression and reconstructs the planted law from a supplied ``TruthRecord``;
the only covariate source is the validated Task 2 reference adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Mapping, NamedTuple, Sequence

import numpy as np
import sympy

from .a34_contract import (
    CORRELATION_THRESHOLD,
    MIN_VALID_REFERENCE_ROWS,
    PREDICTIVE_EQUIVALENCE_DENOMINATOR,
    REFERENCE_ROW_COUNT,
    REL_RMSE_THRESHOLD,
    build_reference_rows,
)
from .a34_parameter_recovery import WilsonInterval, _parse_candidate, wilson_interval_95
from .g2_contract import GRAMMAR_PRIMITIVES, _PRIMITIVE_SYMBOLS
from .truth import TruthRecord

__all__ = [
    "PREDICTIVE_EQUIVALENCE_DENOMINATOR",
    "PREDICTIVE_EQUIVALENCE_FAMILIES",
    "PredictiveEquivalenceResult",
    "PredictiveEquivalenceSummary",
    "score_predictive_equivalence",
    "summarize_predictive_equivalence",
]


# A3.4's /144 family set.  F07 is deliberately absent.
PREDICTIVE_EQUIVALENCE_FAMILIES = frozenset(
    {
        "F01",
        "F02",
        "F03",
        "F04",
        "F05",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F17",
        "F18",
    }
)

_SUPPORTED_MATHEMATICAL_FAMILIES = frozenset(
    {
        "mass_affine_descriptor",
        "mass_saturating_descriptor",
        "mass_interaction",
        "mass_exponential_descriptor",
    }
)


@dataclass(frozen=True)
class PredictiveEquivalenceResult:
    """Metrics for one supplied expression on A3.4's frozen reference rows."""

    applicable: bool
    success: bool
    valid_count: int
    valid_fraction: float
    c_star: float | None
    rmse: float | None
    truth_rms: float | None
    rel_rmse: float | None
    pearson_r: float
    failure_reason: str | None = None

    def scientific_payload(self) -> dict[str, object]:
        """Return the deterministic scientific result projection.

        ``failure_reason`` is deliberately diagnostic only.  The scorer emits
        fixed reasons, but excluding free text here keeps the endpoint sidecar
        independent of host- or runtime-specific messages.
        """
        return {
            "applicable": self.applicable,
            "success": self.success,
            "valid_count": self.valid_count,
            "valid_fraction": self.valid_fraction,
            "c_star": self.c_star,
            "rmse": self.rmse,
            "truth_rms": self.truth_rms,
            "rel_rmse": self.rel_rmse,
            "pearson_r": self.pearson_r,
        }


class PredictiveEquivalenceSummary(NamedTuple):
    """Fixed-denominator descriptive summary for the secondary endpoint."""

    successes: int
    denominator: int
    rate: float
    interval: WilsonInterval


def score_predictive_equivalence(
    expression: str | None,
    truth: TruthRecord,
) -> PredictiveEquivalenceResult:
    """Score one final candidate expression against a constructed truth.

    Candidate parsing is delegated to Task 3's frozen parser so this endpoint
    accepts precisely the same primitive symbols and expression grammar.  No
    coefficients other than the one permitted positive scalar are adjusted.
    """
    family = getattr(truth, "family", None)
    if family not in PREDICTIVE_EQUIVALENCE_FAMILIES:
        return _failed_result(
            applicable=False,
            reason="truth family is outside the A3.4 predictive endpoint",
        )

    parsed = _parse_candidate(expression)
    if parsed is None:
        return _failed_result(
            applicable=True,
            reason="expression is missing, unparseable, or uses an unknown variable",
        )

    rows, _ = build_reference_rows()
    y_true = _reconstruct_truth_values(truth, rows)
    if y_true is None:
        return _failed_result(
            applicable=True,
            reason="truth fields cannot reconstruct an A3.4 mathematical family",
        )

    y_hat = _evaluate_candidate(parsed, rows)
    return _score_arrays(y_hat, y_true, applicable=True)


def summarize_predictive_equivalence(
    results: Sequence[PredictiveEquivalenceResult],
) -> PredictiveEquivalenceSummary:
    """Report supplied successes over the frozen A3.4 denominator of 144."""
    for index, result in enumerate(results):
        if not isinstance(result, PredictiveEquivalenceResult):
            raise ValueError(
                f"result {index} is {type(result).__name__}, "
                "expected PredictiveEquivalenceResult"
            )

    successes = sum(result.success for result in results)
    return PredictiveEquivalenceSummary(
        successes=successes,
        denominator=PREDICTIVE_EQUIVALENCE_DENOMINATOR,
        rate=successes / PREDICTIVE_EQUIVALENCE_DENOMINATOR,
        interval=wilson_interval_95(successes, PREDICTIVE_EQUIVALENCE_DENOMINATOR),
    )


def _reconstruct_truth_values(
    truth: TruthRecord,
    rows: Sequence[Mapping[str, object]],
) -> np.ndarray | None:
    """Evaluate the planted law solely from frozen TruthRecord parameters."""
    if not isinstance(truth, TruthRecord) or not truth.scalar_truth_defined:
        return None
    if truth.mathematical_family not in _SUPPORTED_MATHEMATICAL_FAMILIES:
        return None

    scale = _truth_number(truth.coefficients, "scale")
    coefficient = _truth_number(truth.coefficients, "coefficient")
    exponent = _truth_number(truth.exponents, "mass")
    mass = _reference_column(rows, "mass")
    descriptor = _reference_column(rows, "descriptor")
    descriptor2 = _reference_column(rows, "descriptor2")
    if (
        scale is None
        or coefficient is None
        or exponent is None
        or mass is None
        or descriptor is None
        or descriptor2 is None
    ):
        return None

    try:
        with np.errstate(all="ignore"):
            mass_term = np.power(mass / 250.0, exponent)
            if truth.mathematical_family == "mass_affine_descriptor":
                values = scale * mass_term * (1.0 + coefficient * descriptor)
            elif truth.mathematical_family == "mass_saturating_descriptor":
                values = scale * mass_term * (
                    1.0 + coefficient * descriptor / (1.0 + descriptor)
                )
            elif truth.mathematical_family == "mass_interaction":
                values = scale * mass_term * (
                    1.0 + coefficient * descriptor * descriptor2
                )
            else:  # mass_exponential_descriptor, checked above
                values = scale * mass_term * np.exp(coefficient * descriptor / 3.0)
    except (ArithmeticError, TypeError, ValueError, OverflowError):
        return None
    return _as_real_vector(values, len(rows))


def _truth_number(values: object, key: str) -> float | None:
    if not isinstance(values, Mapping):
        return None
    try:
        value = values[key]
    except (KeyError, TypeError):
        return None
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if isfinite(numeric) else None


def _reference_column(
    rows: Sequence[Mapping[str, object]],
    name: str,
) -> np.ndarray | None:
    try:
        values = np.asarray([float(row[name]) for row in rows], dtype=float)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    return values if values.shape == (len(rows),) else None


def _evaluate_candidate(
    expression: sympy.Expr,
    rows: Sequence[Mapping[str, object]],
) -> np.ndarray:
    """Evaluate a parsed frozen-grammar expression on all reference rows."""
    columns: list[np.ndarray] = []
    for primitive in GRAMMAR_PRIMITIVES:
        column = _reference_column(rows, primitive)
        if column is None:
            return _invalid_vector(len(rows))
        columns.append(column)

    try:
        evaluator = sympy.lambdify(
            tuple(_PRIMITIVE_SYMBOLS[name] for name in GRAMMAR_PRIMITIVES),
            expression,
            modules="numpy",
        )
        with np.errstate(all="ignore"):
            values = evaluator(*columns)
    except (ArithmeticError, TypeError, ValueError, OverflowError):
        return _invalid_vector(len(rows))
    return _as_real_vector(values, len(rows))


def _as_real_vector(values: object, row_count: int) -> np.ndarray:
    """Return a real vector, or all NaNs when evaluation is not real-valued."""
    try:
        array = np.asarray(values)
        if array.ndim == 0:
            array = np.full(row_count, array.item())
        elif array.shape != (row_count,):
            array = np.broadcast_to(array, (row_count,))
        if np.iscomplexobj(array):
            imaginary = np.imag(array)
            if not np.all(np.isfinite(imaginary) & (imaginary == 0.0)):
                return _invalid_vector(row_count)
            array = np.real(array)
        return np.asarray(array, dtype=float)
    except (TypeError, ValueError, OverflowError):
        return _invalid_vector(row_count)


def _invalid_vector(row_count: int) -> np.ndarray:
    return np.full(row_count, np.nan, dtype=float)


def _score_arrays(
    y_hat: np.ndarray | Sequence[float],
    y_true: np.ndarray | Sequence[float],
    *,
    applicable: bool = True,
) -> PredictiveEquivalenceResult:
    """Apply A3.4's V-only scoring rule to two reference-length vectors."""
    try:
        candidate = np.asarray(y_hat, dtype=float)
        planted = np.asarray(y_true, dtype=float)
    except (TypeError, ValueError, OverflowError):
        return _failed_result(
            applicable=applicable,
            reason="candidate or truth evaluation is not a real numeric vector",
        )
    if candidate.shape != (REFERENCE_ROW_COUNT,) or planted.shape != (
        REFERENCE_ROW_COUNT,
    ):
        return _failed_result(
            applicable=applicable,
            reason="candidate and truth evaluations must contain 2160 reference values",
        )

    valid = (
        np.isfinite(candidate)
        & (candidate > 0.0)
        & np.isfinite(planted)
        & (planted > 0.0)
    )
    valid_count = int(np.count_nonzero(valid))
    valid_fraction = valid_count / REFERENCE_ROW_COUNT
    if valid_count < MIN_VALID_REFERENCE_ROWS:
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            reason="fewer than 2150 positive finite reference values",
        )

    candidate_v = candidate[valid]
    planted_v = planted[valid]
    try:
        with np.errstate(all="ignore"):
            numerator = float(np.dot(planted_v, candidate_v))
            denominator = float(np.dot(candidate_v, candidate_v))
            c_star = numerator / denominator
    except (ArithmeticError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            reason="positive scale alignment is not finite",
        )
    if not isfinite(denominator) or denominator <= 0.0 or not isfinite(c_star) or c_star <= 0.0:
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            reason="positive scale alignment is not finite",
        )

    try:
        with np.errstate(all="ignore"):
            residual = c_star * candidate_v - planted_v
            rmse = float(sqrt(float(np.mean(residual * residual))))
            truth_rms = float(sqrt(float(np.mean(planted_v * planted_v))))
            rel_rmse = rmse / truth_rms
    except (ArithmeticError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            c_star=c_star,
            reason="scale-adjusted error metrics are not finite",
        )
    if (
        not isfinite(rmse)
        or not isfinite(truth_rms)
        or truth_rms <= 0.0
        or not isfinite(rel_rmse)
    ):
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            c_star=c_star,
            rmse=rmse if isfinite(rmse) else None,
            truth_rms=truth_rms if isfinite(truth_rms) else None,
            rel_rmse=rel_rmse if isfinite(rel_rmse) else None,
            reason="scale-adjusted error metrics are not finite",
        )

    pearson_r = _pearson_or_zero(candidate_v, planted_v)
    if pearson_r == 0.0:
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            c_star=c_star,
            rmse=rmse,
            truth_rms=truth_rms,
            rel_rmse=rel_rmse,
            pearson_r=0.0,
            reason="candidate or truth values have zero variance",
        )
    if not _meets_metric_thresholds(rel_rmse, pearson_r):
        reason = (
            "relative RMSE exceeds the A3.4 threshold"
            if rel_rmse > REL_RMSE_THRESHOLD
            else "Pearson correlation is below the A3.4 threshold"
        )
        return _failed_result(
            applicable=applicable,
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            c_star=c_star,
            rmse=rmse,
            truth_rms=truth_rms,
            rel_rmse=rel_rmse,
            pearson_r=pearson_r,
            reason=reason,
        )
    return PredictiveEquivalenceResult(
        applicable=applicable,
        success=True,
        valid_count=valid_count,
        valid_fraction=valid_fraction,
        c_star=c_star,
        rmse=rmse,
        truth_rms=truth_rms,
        rel_rmse=rel_rmse,
        pearson_r=pearson_r,
        failure_reason=None,
    )


def _pearson_or_zero(candidate: np.ndarray, planted: np.ndarray) -> float:
    """Compute Pearson r over V, with A3.4's explicit zero-variance rule."""
    try:
        with np.errstate(all="ignore"):
            candidate_centered = candidate - np.mean(candidate)
            planted_centered = planted - np.mean(planted)
            candidate_sum_squares = float(np.dot(candidate_centered, candidate_centered))
            planted_sum_squares = float(np.dot(planted_centered, planted_centered))
            denominator = sqrt(candidate_sum_squares * planted_sum_squares)
            correlation = float(np.dot(candidate_centered, planted_centered) / denominator)
    except (ArithmeticError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return 0.0
    if (
        not isfinite(candidate_sum_squares)
        or not isfinite(planted_sum_squares)
        or candidate_sum_squares <= 0.0
        or planted_sum_squares <= 0.0
        or not isfinite(denominator)
        or denominator <= 0.0
        or not isfinite(correlation)
    ):
        return 0.0
    return correlation


def _meets_metric_thresholds(rel_rmse: float, pearson_r: float) -> bool:
    """Apply A3.4's closed metric thresholds without an epsilon allowance."""
    return (
        isfinite(rel_rmse)
        and isfinite(pearson_r)
        and rel_rmse <= REL_RMSE_THRESHOLD
        and pearson_r >= CORRELATION_THRESHOLD
    )


def _failed_result(
    *,
    applicable: bool,
    reason: str,
    valid_count: int = 0,
    valid_fraction: float = 0.0,
    c_star: float | None = None,
    rmse: float | None = None,
    truth_rms: float | None = None,
    rel_rmse: float | None = None,
    pearson_r: float = 0.0,
) -> PredictiveEquivalenceResult:
    return PredictiveEquivalenceResult(
        applicable=applicable,
        success=False,
        valid_count=valid_count,
        valid_fraction=valid_fraction,
        c_star=c_star,
        rmse=rmse,
        truth_rms=truth_rms,
        rel_rmse=rel_rmse,
        pearson_r=pearson_r,
        failure_reason=reason,
    )
