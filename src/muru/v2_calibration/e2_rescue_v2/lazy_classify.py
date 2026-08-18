"""E2 rescue v2: lazy exact classification.

Derives the MINIMUM set of candidate rows that must be run through the
frozen, unmodified classifier (`e2_classify.classify_expression`) and the
frozen, unmodified truth-equivalence check
(`discovery.equivalence.algebraically_equivalent`) to determine a world's
exact `first_loss_stage`, `representative_g2_correct` and
`representative_truth_equivalent` -- the three fields Gate 2 of the frozen
E4a routing rule actually consumes (`e2_aggregate.evaluate_world`'s own
decision sequence, reproduced below).

NOTHING here reimplements classification, scoring, grouping, or
equivalence. Every scientific call is imported from the same modules
`e2_run_shard.py` already uses, decomposed at the exact seam
`e2_scoring.score_row` itself already composes them at (see section "why
g2_correct and truth_equivalent are split apart" below) rather than
re-derived:

    e2_classify.classify_expression        (unmodified)
    g2_contract.classify_support/
        classify_family_match/
        evaluate_g2_event                  (unmodified -- the exact 3 calls
                                             score_row itself makes for
                                             g2_correct)
    discovery.equivalence.algebraically_equivalent  (unmodified -- the exact
                                             call score_row itself makes for
                                             truth_equivalent, same guard)
    rc5_selection.parse_production_candidate / group_and_select
                                            (unmodified, frozen)
    e2_scoring._parse_truth                (unmodified -- reused directly,
                                             not copied, so the truth-parse
                                             cache is shared with production)

WITNESS ORDER -- derived from `e2_aggregate.evaluate_world`'s real decision
sequence (`v2_design_reference/MURU_V2_E2_PREDECLARATION.md` section 6), not
assumed:

    if n_correct_on_front == 0:      stage = A
    elif n_retained_correct == 0:    stage = B
    elif representative_g2_correct:  stage = E
    elif representative_truth_equivalent: stage = D
    else:                            stage = C

Key algebraic facts this witness order exploits (see
`MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md` section 2 for the full proof):

1. `retained_by_argmax_score` rows are BY CONSTRUCTION members of the
   front (`e2_search.run_seed_search` marks the row it retains from among
   the same list it persists as the front). So `retained_correct(seed) =>
   correct_on_front(seed)`. Classifying only the 30 retained rows already
   tells us, for free, whether `n_correct_on_front > 0` for every seed
   whose retained row happens to be correct.
2. `group_and_select`'s winner and representative are a deterministic
   function of the 30 retained candidates alone (their `expression_string`
   for template-key grouping, `k` for tie-breaking) -- it never looks at
   the rest of any front. So if ANY retained row is correct, the
   representative can be computed, and it is trivially already classified
   (it IS one of the 30 retained rows), so `representative_g2_correct` is
   already known with zero extra classification cost.
3. Only ONE equivalence check (`algebraically_equivalent`) is EVER needed
   per world, on the representative, only if it is not itself `g2_correct`.
4. Stage A is a universal negative ("no seed's front contains a correct
   row, anywhere") and is the ONLY stage that can require classifying
   every row of every front -- proving a negative existential over an
   unbounded-in-principle front has no shortcut. This is disclosed, not
   hidden: the benchmark (Part VI) reports the A-world classification cost
   separately, and it is not expected to shrink.

Why `g2_correct` and `truth_equivalent` are computed via two separate calls
here instead of one call to `e2_scoring.score_row`: `score_row` itself
*always* attempts `algebraically_equivalent` for every row it is given
(whenever that row parses), regardless of whether the row is g2_correct or
will ever become a representative. `algebraically_equivalent` runs
`sympy.simplify` up to twice per call (`discovery/equivalence.py`) with NO
wall-clock cap anywhere in its call path (only a cheap `count_ops`
early-out) -- unlike `classify_expression`, it was never brought under the
2026-08-16 rescue's process-boundary timeout. Piping every witness row
through `score_row` would therefore (a) do systematically wasted symbolic
work `evaluate_world` never uses (only the single representative's
`truth_equivalent` is ever read), and (b) reintroduce, on the lazy path,
exactly the class of unbounded-symbolic-computation risk the rescue
already had to fix once for `classify_expression`. This module instead
calls the SAME three sub-functions `score_row` composes for `g2_correct`
on every witness row, and calls `algebraically_equivalent` -- via the SAME
guard, SAME parser, SAME truth-parse cache -- exactly once, only for the
row that turns out to need it. This is a decomposition of production code
at its own internal seam, not a new formula; `tests/test_lazy_classify_control_flow.py`
and the Part V replay-parity gate both verify it reproduces `score_row`'s
own `g2_correct`/`truth_equivalent` values exactly wherever it computes
them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from muru.discovery.equivalence import algebraically_equivalent
from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import (
    G2Event,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
)
from muru.paper_benchmark.rc5_selection import (
    RetainedCandidate,
    SeedSelection,
    group_and_select,
    parse_production_candidate,
)

from muru.v2_calibration import e2_classify
from muru.v2_calibration.e2_scoring import _parse_truth  # reused, not copied -- shares production's truth-parse cache
from muru.v2_calibration.e2_worlds import WorldTruth

__all__ = [
    "RawFrontRow", "LazyWorldResult", "lazy_evaluate_world",
    "reset_call_counters", "call_counters",
]


@dataclass(frozen=True)
class RawFrontRow:
    """The part of a front row available with ZERO classification cost --
    straight off PySR's `equations_` frame, no `sympy.simplify` involved."""

    seed_ordinal_k: int
    seed: int
    front_rank: int
    expression_string: str
    complexity: int
    valid_r2: float
    invalid_fraction: float
    candidate_test_r2: float
    retained_by_argmax_score: bool


@dataclass(frozen=True)
class LazyWorldResult:
    first_loss_stage: str                       # A | B | C | D | E -- IDENTICAL to evaluate_world's
    representative_g2_correct: Optional[bool]
    representative_truth_equivalent: Optional[bool]
    representative_expression: Optional[str]
    witness_path: str                            # diagnostic only, not routing-relevant
    n_classify_calls: int                        # calls THIS evaluation made
    n_equivalence_calls: int                      # algebraically_equivalent calls THIS evaluation made (<=1, always)


# Process-local counters, reset per benchmark/replay run. Diagnostic only --
# never read by any stage decision.
_calls = {"classify": 0, "equivalence": 0}


def reset_call_counters() -> None:
    _calls["classify"] = 0
    _calls["equivalence"] = 0


def call_counters() -> dict:
    return dict(_calls)


def _classify(expr: str):
    _calls["classify"] += 1
    return e2_classify.classify_expression(expr)


def _g2_correct(classification, truth: WorldTruth) -> bool:
    """The EXACT three-call composition `e2_scoring.score_row` uses for
    `g2_correct` -- reproduced here (not re-derived) so it can be evaluated
    without also paying for the equivalence check `score_row` always
    bundles alongside it."""
    effective_support = (
        frozenset(classification.effective_support) if classification.effective_support is not None else None
    )
    support_status = classify_support(effective_support, truth.support)
    family_status = classify_family_match(classification.discovered_family, truth.family)
    event = evaluate_g2_event(support_status, family_status)
    return event == G2Event.SUCCESS


def _truth_equivalent(expr: str, classification, truth: WorldTruth) -> Optional[bool]:
    """The EXACT guard and call `e2_scoring.score_row` uses for
    `truth_equivalent`. Called at most once per world by this module."""
    _calls["equivalence"] += 1
    if not (classification.parse_ok and classification.canonicalization_status == "OK"):
        # score_row's own guard would not have attempted the call either;
        # this counts as an attempted (guarded) call for benchmarking
        # symmetry with score_row's cost, even though no sympy work runs.
        return None
    try:
        candidate_expr = parse_production_candidate(expr)
        truth_expr = _parse_truth(truth.law_string)
        if truth_expr is None:
            return None
        return algebraically_equivalent(candidate_expr, truth_expr)
    except Exception:
        return None


def lazy_evaluate_world(
    seed_raw_fronts: dict[int, Sequence[RawFrontRow]],
    truth: WorldTruth,
) -> LazyWorldResult:
    """`seed_raw_fronts`: seed -> ordered sequence of that seed's raw front
    rows (any order; sorted internally by `front_rank`), for all seeds that
    completed with a front. Seeds with no candidate/execution failure are
    simply absent -- exactly as `evaluate_world` already treats a seed with
    no rows: it cannot contribute a correct-on-front or retained-correct
    witness.
    """
    ordered_seeds = sorted(seed_raw_fronts.keys())

    # --- Phase 1: classify only the retained row of each seed (<=30 calls) ---
    retained_classified: dict[int, tuple[RawFrontRow, object, bool]] = {}  # seed -> (raw, classification, g2_correct)
    selections: list[SeedSelection] = []
    for seed in ordered_seeds:
        rows = seed_raw_fronts[seed]
        retained = next((r for r in rows if r.retained_by_argmax_score), None)
        if retained is None:
            selections.append(SeedSelection(
                k=(rows[0].seed_ordinal_k if rows else 0),
                seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE, candidate=None,
            ))
            continue
        classification = _classify(retained.expression_string)
        g2_correct = _g2_correct(classification, truth)
        retained_classified[seed] = (retained, classification, g2_correct)
        selections.append(SeedSelection(
            k=retained.seed_ordinal_k, seed=seed, status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            candidate=RetainedCandidate(
                k=retained.seed_ordinal_k, seed=seed, expression_string=retained.expression_string,
                complexity=retained.complexity, valid_r2=retained.valid_r2,
                invalid_fraction=retained.invalid_fraction, candidate_test_r2=retained.candidate_test_r2,
            ),
        ))

    any_retained_correct = any(g2 for _, _, g2 in retained_classified.values())

    if any_retained_correct:
        # Facts 1+2: not-A and not-B both proved. Representative is one of
        # the already-classified retained rows -- zero extra classify cost.
        cross = group_and_select(selections)
        rep = cross.representative
        if rep is None:  # defensive; unreachable given any_retained_correct
            raise AssertionError("group_and_select returned no representative despite a correct retained row")
        rep_data = retained_classified.get(rep.seed)
        if rep_data is None:  # defensive
            raise AssertionError("representative's seed not found among classified retained rows")
        rep_raw, rep_classification, rep_g2_correct = rep_data
        if rep_g2_correct:
            return LazyWorldResult(
                first_loss_stage="E",
                representative_g2_correct=True,
                representative_truth_equivalent=None,  # not needed for E; score_row would compute it but evaluate_world never reads it when g2_correct is True
                representative_expression=rep.expression_string,
                witness_path="PHASE1_RETAINED_ONLY",
                n_classify_calls=_calls["classify"], n_equivalence_calls=_calls["equivalence"],
            )
        truth_equiv = _truth_equivalent(rep_raw.expression_string, rep_classification, truth)
        stage = "D" if truth_equiv else "C"
        return LazyWorldResult(
            first_loss_stage=stage,
            representative_g2_correct=False,
            representative_truth_equivalent=truth_equiv,
            representative_expression=rep.expression_string,
            witness_path="PHASE1_RETAINED_ONLY",
            n_classify_calls=_calls["classify"], n_equivalence_calls=_calls["equivalence"],
        )

    # --- Phase 2: no retained row anywhere is correct. Scan the rest of
    # each seed's front (excluding the already-classified retained row) for
    # a witness. Short-circuit on the FIRST correct row found anywhere. ---
    for seed in ordered_seeds:
        rows = seed_raw_fronts[seed]
        for raw in sorted(rows, key=lambda r: r.front_rank):
            if raw.retained_by_argmax_score:
                continue  # already classified in Phase 1
            classification = _classify(raw.expression_string)
            if _g2_correct(classification, truth):
                # correct_on_front(seed) true, n_retained_correct still 0
                # (proved in Phase 1) => stage B, immediately, no matter
                # how many rows/seeds remain unclassified. No equivalence
                # call is ever needed for stage B.
                return LazyWorldResult(
                    first_loss_stage="B",
                    representative_g2_correct=None,
                    representative_truth_equivalent=None,
                    representative_expression=None,
                    witness_path="PHASE2_FRONT_SCAN_B",
                    n_classify_calls=_calls["classify"], n_equivalence_calls=_calls["equivalence"],
                )

    # Every row of every front classified, none correct: proves the
    # universal negative. Stage A, and this is the one case that pays the
    # same classification cost as the exhaustive pipeline (still zero
    # equivalence calls -- A never reaches the representative step).
    return LazyWorldResult(
        first_loss_stage="A",
        representative_g2_correct=None,
        representative_truth_equivalent=None,
        representative_expression=None,
        witness_path="PHASE2_FULL_SCAN_A",
        n_classify_calls=_calls["classify"], n_equivalence_calls=_calls["equivalence"],
    )
