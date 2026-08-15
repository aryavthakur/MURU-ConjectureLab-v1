"""Engineering RC5: per-seed retention, cross-seed identity, grouping,
``selection_count``, and representative selection.

Bound by A3.5 sections 7.1 and 7.3-7.6.

Per-seed retention (section 7.1)
--------------------------------
Exactly **one** candidate is retained per seed: the row of ``equations_`` at
``argmax(score)`` -- PySR-native ``model_selection = "score"``, the engine's own
negated derivative of log-loss with respect to complexity.  ``model_selection``
is **not set on the regressor** (obligation 6); retention is applied to the
emitted frame, so the engine's ``.predict()`` path is never implicitly
re-selected.

Two things the frozen engine does that this module refuses to inherit:

* ``idx_model_selection`` silently falls back to ``"accuracy"``
  (``loss.idxmin()``) when the ``score`` column is absent.  Section 7.6 makes an
  absent ``score`` column an ``EXECUTION_FAILURE`` instead -- never a silent
  change of selection rule.
* A non-finite ``loss`` value is load-bearing: ``DataFrame.query`` silently
  drops NaN rows while ``idxmax`` over a score column containing ``inf`` does
  not, so ``"score"`` and ``"best"`` can diverge on exactly that input.  Section
  7.6 makes it an ``EXECUTION_FAILURE``.

Cross-seed identity (section 7.3, as replaced)
-----------------------------------------------
Grouping uses :mod:`muru.paper_benchmark.identity_contract` --
``template_key``/``positive_scale_equivalent``, the final positive-scale-
invariant contract frozen at Session 3 Decision 1 (``IDENTITY_CONTRACT_PASS``,
``audit/MURU_A3_5_IDENTITY_FINAL_CONTRACT.md``, named as the closed contract by
amendment section 14.1).  The superseded seven/eight-step ``TEMPLATE_KEY``
placeholder-canonicalisation recipe, whose global-scale-strip step was proven
unsound for rational-function candidates, is **not** implemented here and must
not return.

Every candidate reaching the contract is a **freshly parsed string** --
``equations_["equation"]`` through ``parse_candidate`` -- never an in-process
scalar multiple of another candidate's parsed object.  That is precisely the
production construction the identity contract's disclosed limitation 2 does not
apply to (0 failures on a 6,912-item corpus under this construction; the 9.2%
failure mode requires the non-production construction, which occurs nowhere).

Grouping, ``selection_count``, representative (sections 7.4-7.6)
-----------------------------------------------------------------
* **One seed, one vote.**  Each seed's single retained candidate joins exactly
  one class -- never a fraction, never two classes, never counted twice.
* **Largest class wins**; ties break toward the class containing the **lowest
  seed ordinal**.  Because each seed belongs to exactly one class, per-class
  minimum ordinals are unique across classes, so the tie-break is **total**.
  It never inspects ``valid_r2``, ``complexity``, ``loss``, ``score``,
  ``variable_support``, or any G2 output.
* ``selection_count`` is the winning class's member count, 0..30, against the
  frozen ``selection_denominator = 30``.  A failed or barren seed retains
  nothing and cannot vote while the denominator stays 30 -- which depresses
  ``selection_fraction``, the conservative direction.
* The **representative** is the winning class's member at the lowest seed
  ordinal.  Its own emitted values are used **verbatim**: nothing is
  recomputed, averaged, pooled across the class, or refit.
* Two **non-gating** diagnostics are recorded because merging is the
  ``k``-inflating direction: distinct as-emitted expression strings within the
  winning class, and distinct coefficient vectors within it.  Neither enters
  any gate.

Nothing here reads planted truth, the generative family, or the partition
label.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import sympy as sp

from .calibration_contract import SeedStatus
from .identity_contract import parse_candidate, template_key
from .structural_acceptance import (
    MAX_COMPLEXITY,
    MAX_INVALID_FRACTION,
    STABILITY_DENOMINATOR,
    STABILITY_GATE,
)

__all__ = [
    "SEEDS_PER_CASE",
    "SeedExecutionFailure",
    "SeedNoCandidate",
    "select_row_label",
    "RetainedCandidate",
    "SeedSelection",
    "coefficient_vector",
    "EquivalenceClass",
    "CrossSeedSelection",
    "group_and_select",
]

#: A3.5 section 8.1 / structural_acceptance's frozen denominator.
SEEDS_PER_CASE = STABILITY_DENOMINATOR


class SeedExecutionFailure(RuntimeError):
    """Genuine computational breakdown for one seed (section 6.0's narrow sense)."""


class SeedNoCandidate(RuntimeError):
    """The seed completed but retains nothing (section 7.6)."""


# -----------------------------------------------------------------------
# Per-seed retention
# -----------------------------------------------------------------------

def select_row_label(equations: Any) -> Any:
    """``argmax(score)`` over the emitted frame, with section 7.6's guards.

    Returns a pandas **label**, not a position; callers must convert through
    ``rc5_adapter.row_position`` before ``predict(index=...)`` or ``.iloc[]``.
    """
    if equations is None or len(equations) == 0:
        raise SeedNoCandidate("equations_ is empty or absent")
    columns = set(equations.columns)
    if "score" not in columns:
        raise SeedExecutionFailure(
            "equations_ has no 'score' column, which would mean loss_scale is not "
            "the frozen default 'log'; refusing the engine's silent fallback to "
            "'accuracy' (A3.5 section 7.6)"
        )
    if "loss" not in columns:
        raise SeedExecutionFailure("equations_ has no 'loss' column")
    losses = np.asarray(equations["loss"], dtype=np.float64)
    if not np.all(np.isfinite(losses)):
        raise SeedExecutionFailure(
            "equations_ carries a non-finite loss; 'score' and 'best' diverge "
            "silently on exactly this input (A3.5 section 7.6)"
        )
    return equations["score"].idxmax()


@dataclass(frozen=True)
class RetainedCandidate:
    """The single candidate one seed contributes, with its own emitted values."""

    k: int                       # seed ordinal 0..29
    seed: int
    expression_string: str
    complexity: int
    valid_r2: float
    invalid_fraction: float
    candidate_test_r2: float

    def __post_init__(self) -> None:
        if not (0 <= self.k < SEEDS_PER_CASE):
            raise ValueError(f"seed ordinal {self.k} outside [0, {SEEDS_PER_CASE})")


@dataclass(frozen=True)
class SeedSelection:
    """One seed's outcome: a retained candidate, or why there is none."""

    k: int
    seed: int
    status: SeedStatus
    candidate: RetainedCandidate | None = None
    error_message: str = ""

    @property
    def votes(self) -> bool:
        return self.candidate is not None


# -----------------------------------------------------------------------
# Diagnostics (non-gating)
# -----------------------------------------------------------------------

def coefficient_vector(expression_string: str) -> tuple[float, ...] | None:
    """The numeric literals of an expression, in deterministic preorder.

    A **reporting** convention only.  Section 7.4 requires the count of
    distinct coefficient vectors inside the winning class to be recorded so
    class heterogeneity cannot hide behind ``selection_count``; it enters no
    gate, and nothing downstream branches on it.  ``None`` for an expression
    the frozen parser cannot read, which then forms its own bucket rather than
    being merged into any other.
    """
    try:
        parsed = parse_candidate(expression_string)
    except Exception:
        return None
    numbers: list[float] = []
    for node in sp.preorder_traversal(parsed):
        if node.is_Number:
            try:
                numbers.append(float(node))
            except (TypeError, ValueError):  # pragma: no cover - complex/inf atoms
                return None
    return tuple(numbers)


# -----------------------------------------------------------------------
# Cross-seed grouping
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class EquivalenceClass:
    """One positive-scale-equivalence class of retained candidates."""

    key: tuple
    members: tuple[RetainedCandidate, ...]   # ordered by seed ordinal

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def min_ordinal(self) -> int:
        return self.members[0].k

    @property
    def representative(self) -> RetainedCandidate:
        """The member at the lowest seed ordinal.  Never refitted."""
        return self.members[0]


@dataclass(frozen=True)
class CrossSeedSelection:
    """The case-level result of grouping 30 seeds' retained candidates."""

    classes: tuple[EquivalenceClass, ...]
    winning: EquivalenceClass | None
    selection_count: int
    selection_denominator: int
    representative: RetainedCandidate | None
    distinct_expression_strings: int
    distinct_coefficient_vectors: int
    voting_seeds: int

    @property
    def selection_fraction(self) -> float:
        return self.selection_count / self.selection_denominator

    @property
    def stability_gate_passed(self) -> bool:
        """Gate 3, restated only as executable enforcement.

        ``k = 20`` passes by exact float equality of ``20/30`` with itself.
        """
        return self.selection_fraction >= STABILITY_GATE / STABILITY_DENOMINATOR

    def diagnostics(self) -> dict[str, int]:
        return {
            "winning_class_distinct_expression_strings": self.distinct_expression_strings,
            "winning_class_distinct_coefficient_vectors": self.distinct_coefficient_vectors,
            "voting_seeds": self.voting_seeds,
        }


def group_and_select(
    seed_selections: Sequence[SeedSelection],
    selection_denominator: int = SEEDS_PER_CASE,
) -> CrossSeedSelection:
    """Group by the frozen identity contract, then pick winner and representative.

    Deterministic and replayable: class order follows first-appearance by seed
    ordinal, members are sorted by ordinal, and the winner is chosen by
    ``(size desc, min ordinal asc)`` -- a total order, since per-class minimum
    ordinals are unique.
    """
    ordinals = [s.k for s in seed_selections]
    if len(set(ordinals)) != len(ordinals):
        raise ValueError("two selections claim the same seed ordinal: one seed, one vote")

    voters = sorted(
        (s for s in seed_selections if s.votes), key=lambda s: s.k
    )

    buckets: dict[tuple, list[RetainedCandidate]] = {}
    order: list[tuple] = []
    for selection in voters:
        candidate = selection.candidate
        assert candidate is not None  # `votes` guarantees it
        key = template_key(parse_candidate(candidate.expression_string))
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(candidate)

    classes = tuple(
        EquivalenceClass(key=key, members=tuple(sorted(buckets[key], key=lambda c: c.k)))
        for key in order
    )

    if not classes:
        return CrossSeedSelection(
            classes=(),
            winning=None,
            selection_count=0,
            selection_denominator=selection_denominator,
            representative=None,
            distinct_expression_strings=0,
            distinct_coefficient_vectors=0,
            voting_seeds=0,
        )

    winning = min(classes, key=lambda c: (-c.size, c.min_ordinal))

    strings = {m.expression_string for m in winning.members}
    vectors = {coefficient_vector(m.expression_string) for m in winning.members}

    return CrossSeedSelection(
        classes=classes,
        winning=winning,
        selection_count=winning.size,
        selection_denominator=selection_denominator,
        representative=winning.representative,
        distinct_expression_strings=len(strings),
        distinct_coefficient_vectors=len(vectors),
        voting_seeds=len(voters),
    )
