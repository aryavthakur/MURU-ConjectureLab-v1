"""Deterministic Wilson score confidence interval and Clopper-Pearson calculation."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


STANDARD_Z_95 = 1.959963984540054


@dataclass(frozen=True)
class ScoreInterval:
    lower: float
    upper: float
    center: float
    margin: float
    point_estimate: float
    successes: int
    total: int

    def to_dict(self) -> dict[str, float]:
        return {
            "lower": float(self.lower),
            "upper": float(self.upper),
            "center": float(self.center),
            "margin": float(self.margin),
            "point_estimate": float(self.point_estimate),
        }

    def format_bracket(self, digits: int = 4) -> str:
        return f"[{self.lower:.{digits}f}, {self.upper:.{digits}f}]"


def wilson_score_interval(successes: int, total: int, z: float = STANDARD_Z_95) -> ScoreInterval:
    """Compute the two-sided 95% Wilson score interval from numerator and denominator.

    Rules:
    - Never copies intervals blindly from external sources.
    - Recomputed strictly from integer numerator and exact frozen denominator.
    - Handles edge counts k=0 and k=n with exact continuity.
    """
    if total <= 0:
        raise ValueError(f"Total denominator must be strictly positive, got {total}")
    if not (0 <= successes <= total):
        raise ValueError(f"Successes {successes} must be between 0 and total {total}")

    p_hat = successes / total
    denom = 1.0 + (z * z) / total
    center = (p_hat + (z * z) / (2.0 * total)) / denom
    variance_term = (p_hat * (1.0 - p_hat)) / total + (z * z) / (4.0 * total * total)
    margin = (z * sqrt(max(0.0, variance_term))) / denom

    lower = 0.0 if successes == 0 else max(0.0, center - margin)
    upper = 1.0 if successes == total else min(1.0, center + margin)

    return ScoreInterval(
        lower=float(lower),
        upper=float(upper),
        center=float(center),
        margin=float(margin),
        point_estimate=float(p_hat),
        successes=successes,
        total=total,
    )


def wilson_lower_95(successes: int, total: int) -> float:
    """Convenience accessor for lower 95% bound."""
    return wilson_score_interval(successes, total).lower


def wilson_upper_95(successes: int, total: int) -> float:
    """Convenience accessor for upper 95% bound."""
    return wilson_score_interval(successes, total).upper


def clopper_pearson_upper_bound(total: int, alpha: float = 0.05) -> float:
    """Two-sided Clopper-Pearson exact upper bound for zero observed events (k = 0).

    Formula: 1 - (alpha / 2)**(1 / total)
    For n=100 and alpha=0.05, yields 0.0362 (reproducing historical Class A records).
    """
    if total <= 0:
        raise ValueError(f"Total must be strictly positive, got {total}")
    return 1.0 - (alpha / 2.0) ** (1.0 / total)
