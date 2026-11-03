"""Engineering RC3: G2 aggregate scorer.

This module is NEW in RC3.  It does not modify, shadow, or re-declare any
frozen A3.1 constant; it imports every binding value from
``g2_contract`` and every G3 value from ``g3_contract``.

Binding semantics for G2 (frozen by Amendment A3.1, restated here only as
executable enforcement):

  - the denominator is ALWAYS ``G2_HELD_OUT_DENOMINATOR`` (144)
  - it never shrinks, for any reason, under any outcome
  - ``G2Event.SUCCESS`` is the only numerator contribution
  - ``G2Event.FAILURE`` and ``G2Event.UNEVALUABLE`` are both non-successes
  - the gate is ``wilson_lower_95(successes, 144) >= G2_WILSON_LOWER_GATE``

The consequence that ``UNEVALUABLE`` is never dropped is what makes the
endpoint honest: an unevaluable case costs exactly as much as a failure.

This module reads no case data, no partition, and no planted truth.  It
consumes an already-classified event sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .g2_contract import (
    G2_HELD_OUT_DENOMINATOR,
    G2_WILSON_LOWER_GATE,
    G2Event,
    wilson_lower_95,
)
from .g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
    G3Score,
)
from .g3_contract import score_g3 as _frozen_score_g3

__all__ = [
    "G2Score",
    "score_g2",
    "score_g3",
    "G2_HELD_OUT_DENOMINATOR",
    "G2_WILSON_LOWER_GATE",
    "G3_HELD_OUT_DENOMINATOR",
    "G3_WILSON_UPPER_GATE",
]


@dataclass(frozen=True)
class G2Score:
    """Aggregate G2 score across all G2 opportunities.

    ``denominator`` is carried explicitly so that any downstream reader can
    see that it is 144 and not a post-hoc evaluable count.
    """

    successes: int
    failures: int
    unevaluable: int
    denominator: int
    wilson_lower: float
    gate_passed: bool

    @property
    def success_rate(self) -> float:
        if self.denominator == 0:
            return 0.0
        return self.successes / self.denominator

    @property
    def non_successes(self) -> int:
        return self.denominator - self.successes


def score_g2(events: Sequence[G2Event]) -> G2Score:
    """Score G2 across all opportunities.

    Mirrors :func:`muru.paper_benchmark.g3_contract.score_g3`: the event
    sequence must be exactly the frozen denominator in length, so a run that
    silently lost cases cannot be scored at all.

    Raises
    ------
    ValueError
        If ``len(events) != 144``, or if any element is not a ``G2Event``.
    """
    if len(events) != G2_HELD_OUT_DENOMINATOR:
        raise ValueError(
            f"expected {G2_HELD_OUT_DENOMINATOR} G2 events, got {len(events)}"
        )

    for index, event in enumerate(events):
        if not isinstance(event, G2Event):
            raise ValueError(
                f"event {index} is {type(event).__name__}, expected G2Event"
            )

    successes = sum(1 for e in events if e == G2Event.SUCCESS)
    failures = sum(1 for e in events if e == G2Event.FAILURE)
    unevaluable = sum(1 for e in events if e == G2Event.UNEVALUABLE)

    # Denominator is the frozen constant, never len(events) filtered by
    # evaluability, and never a recomputed evaluable count.
    lower = wilson_lower_95(successes, G2_HELD_OUT_DENOMINATOR)

    return G2Score(
        successes=successes,
        failures=failures,
        unevaluable=unevaluable,
        denominator=G2_HELD_OUT_DENOMINATOR,
        wilson_lower=lower,
        gate_passed=lower >= G2_WILSON_LOWER_GATE,
    )


def score_g3(events: Sequence[G3Event]) -> G3Score:
    """Score G3, with the same element-type discipline as :func:`score_g2`.

    The frozen ``g3_contract.score_g3`` counts violations by membership
    testing against a ``str``-Enum, so a bare string element is accepted and
    anything unrecognized scores as SAFE.  A G3 sequence built from typo'd or
    stringified variant labels would then pass the safety gate: drift in the
    permissive direction.  RC3 type-checks first and delegates the arithmetic
    unchanged.
    """
    if len(events) != G3_HELD_OUT_DENOMINATOR:
        raise ValueError(
            f"expected {G3_HELD_OUT_DENOMINATOR} G3 events, got {len(events)}"
        )
    for index, event in enumerate(events):
        if not isinstance(event, G3Event):
            raise ValueError(
                f"event {index} is {type(event).__name__}, expected G3Event"
            )
    return _frozen_score_g3(events)
