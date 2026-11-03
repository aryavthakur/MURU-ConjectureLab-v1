"""Amendment A3.1: G3 structural-safety endpoint contract.

G3 monitors whether the structural acceptance predicate admits unsafe
structural claims.  It operates on the 36 Held-out G3 opportunities
(families F07, F19, and F20: F07 has 12 held-out replicates on its own
single variant, F19 and F20 each contribute 3 variants x 4 held-out
replicates = 12; 12 + 12 + 12 = 36 total).

Key rules:
  - Unsafe structural acceptance contributes 1.
  - Safe evaluable non-acceptance contributes 0.
  - UNEVALUABLE contributes a G3 VIOLATION (conservative).
  - UNEVALUABLE does not receive safety credit.
  - UNEVALUABLE remains in denominator 36.

Criterion: upper 95% Wilson <= 0.15

This module is the REFERENCE CONTRACT.  Production integration is RC3.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .structural_acceptance import AcceptanceResult, AcceptanceStatus
from .g2_contract import wilson_upper_95


# -----------------------------------------------------------------------
# G3 frozen parameters
# -----------------------------------------------------------------------

G3_HELD_OUT_DENOMINATOR = 36
G3_WILSON_UPPER_GATE = 0.15


# -----------------------------------------------------------------------
# Unsafe event classification
# -----------------------------------------------------------------------

class G3Event(str, Enum):
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    VIOLATION = "VIOLATION"


class G3VariantSafety(str, Enum):
    """Per-variant safety classification for the G3 event."""
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNEVALUABLE = "UNEVALUABLE"


# -----------------------------------------------------------------------
# F07 semantics
# -----------------------------------------------------------------------

def classify_f07_event(
    acceptance: AcceptanceResult,
    effective_support: frozenset[str] | None,
) -> G3Event:
    """F07: mass-only g truth (false extra-structure acceptance).

    Mass-only law; mass-only acceptance permitted.  Accepted unsupported
    non-mass structure (or a richer family) is unsafe.  Frozen design
    authority: "F07 errors are false extra-structure acceptance: the system
    accepts an unsupported non-mass variable or richer family despite a
    mass-only law." -- structurally identical to the F19A/F19B mass-only-
    permitted rule below, reused here rather than redefined.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if not acceptance.accepted:
        return G3Event.SAFE

    # Accepted - check if support is mass-only
    if effective_support is not None and effective_support <= {"mass"}:
        return G3Event.SAFE

    return G3Event.UNSAFE


# -----------------------------------------------------------------------
# F19 variant semantics
# -----------------------------------------------------------------------

def classify_f19a_event(
    acceptance: AcceptanceResult,
    effective_support: frozenset[str] | None,
) -> G3Event:
    """F19A: descriptor link destroyed.

    Mass-only acceptance permitted.
    Accepted unsupported non-mass structure is unsafe.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if not acceptance.accepted:
        return G3Event.SAFE

    # Accepted - check if support is mass-only
    if effective_support is not None and effective_support <= {"mass"}:
        return G3Event.SAFE

    return G3Event.UNSAFE


def classify_f19b_event(
    acceptance: AcceptanceResult,
    effective_support: frozenset[str] | None,
) -> G3Event:
    """F19B: mass-preserving null.

    Mass-only permitted.
    Accepted non-mass structure is unsafe.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if not acceptance.accepted:
        return G3Event.SAFE

    # Accepted - check if support is mass-only
    if effective_support is not None and effective_support <= {"mass"}:
        return G3Event.SAFE

    return G3Event.UNSAFE


def classify_f19c_event(
    acceptance: AcceptanceResult,
) -> G3Event:
    """F19C: response cell resampling (trajectory destruction).

    Accepted structural claim is unsafe.
    Legitimate non-acceptance is safe.
    Unevaluable remains a violation.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if acceptance.accepted:
        return G3Event.UNSAFE

    return G3Event.SAFE


# -----------------------------------------------------------------------
# F20 variant semantics
# -----------------------------------------------------------------------

def classify_f20a_event(
    acceptance: AcceptanceResult,
) -> G3Event:
    """F20A: latent driver.

    Accepted structural claim is unsafe.
    Non-acceptance is safe.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if acceptance.accepted:
        return G3Event.UNSAFE

    return G3Event.SAFE


def classify_f20b_event(
    acceptance: AcceptanceResult,
) -> G3Event:
    """F20B: measurement coupling.

    Accepted structural claim is unsafe.
    Non-acceptance is safe.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if acceptance.accepted:
        return G3Event.UNSAFE

    return G3Event.SAFE


def classify_f20c_event(
    acceptance: AcceptanceResult,
) -> G3Event:
    """F20C: out-of-grammar trap.

    Accepted structural claim is unsafe.
    Non-acceptance is safe.
    """
    if acceptance.status == AcceptanceStatus.UNEVALUABLE:
        return G3Event.VIOLATION

    if acceptance.accepted:
        return G3Event.UNSAFE

    return G3Event.SAFE


# -----------------------------------------------------------------------
# G3 event dispatch
# -----------------------------------------------------------------------

def classify_g3_event(
    variant: str,
    acceptance: AcceptanceResult,
    effective_support: frozenset[str] | None = None,
) -> G3Event:
    """Dispatch to the correct variant-specific G3 classifier."""
    if variant == "F07":
        return classify_f07_event(acceptance, effective_support)
    elif variant == "F19A":
        return classify_f19a_event(acceptance, effective_support)
    elif variant == "F19B":
        return classify_f19b_event(acceptance, effective_support)
    elif variant == "F19C":
        return classify_f19c_event(acceptance)
    elif variant == "F20A":
        return classify_f20a_event(acceptance)
    elif variant == "F20B":
        return classify_f20b_event(acceptance)
    elif variant == "F20C":
        return classify_f20c_event(acceptance)
    else:
        raise ValueError(f"unknown G3 variant: {variant}")


# -----------------------------------------------------------------------
# G3 aggregate scoring
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class G3Score:
    """Aggregate G3 score across all G3 opportunities."""
    violations: int
    denominator: int
    wilson_upper: float
    gate_passed: bool

    @property
    def violation_rate(self) -> float:
        if self.denominator == 0:
            return 0.0
        return self.violations / self.denominator


def score_g3(events: Sequence[G3Event]) -> G3Score:
    """Score G3 across all opportunities.

    Violations (UNSAFE or VIOLATION) count as 1.
    SAFE counts as 0.
    Denominator is fixed at 36.
    """
    if len(events) != G3_HELD_OUT_DENOMINATOR:
        raise ValueError(
            f"expected {G3_HELD_OUT_DENOMINATOR} G3 events, got {len(events)}"
        )

    violations = sum(
        1 for e in events
        if e in (G3Event.UNSAFE, G3Event.VIOLATION)
    )

    upper = wilson_upper_95(violations, G3_HELD_OUT_DENOMINATOR)

    return G3Score(
        violations=violations,
        denominator=G3_HELD_OUT_DENOMINATOR,
        wilson_upper=upper,
        gate_passed=upper <= G3_WILSON_UPPER_GATE,
    )
