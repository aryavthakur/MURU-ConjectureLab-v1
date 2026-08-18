"""E2: cross-seed grouping, per-case metrics, and the A-E first-loss label.

Cross-seed grouping reuses `rc5_selection.group_and_select` unmodified, fed
the SAME `RetainedCandidate` objects production would have retained (one per
seed, the `argmax(score)` row) -- constructed here from E2's own captured
front rather than by re-running the search, so this is a replay of the
frozen v1 retention/grouping rule used as a CONTROL, never a new rule.

The A-E mapping is `v2_design_reference/MURU_V2_E2_PREDECLARATION.md`
section 6, applied mechanically.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.rc5_selection import (
    CrossSeedSelection,
    RetainedCandidate,
    SeedSelection,
    group_and_select,
)

from .e2_scoring import ScoredRow
from .e2_search import FrontRow, SeedFrontResult
from .e2_worlds import WorldContent

__all__ = [
    "FIRST_LOSS_STAGES", "SeedOutcome", "WorldOutcome",
    "build_seed_selections", "evaluate_world",
]

FIRST_LOSS_STAGES = ("A", "B", "C", "D", "E")


@dataclass(frozen=True)
class SeedOutcome:
    """One seed's role in the case's attribution, truth-joined."""

    seed_ordinal_k: int
    seed: int
    status: str
    front_size: int
    correct_on_front: bool
    best_correct_rank: Optional[int]
    best_correct_score: Optional[float]
    retained_rank: Optional[int]
    retained_correct: bool
    score_gap: Optional[float]          # retained.score - best_correct.score, when a correct row exists
    complexity_gap: Optional[int]       # best_correct.complexity - retained.complexity
    r2_gap: Optional[float]             # best_correct.valid_r2 - retained.valid_r2


def build_seed_selections(
    seed_results: Sequence[SeedFrontResult],
) -> list[SeedSelection]:
    """The `argmax(score)`-retained candidate per seed, as a `SeedSelection`
    sequence `rc5_selection.group_and_select` accepts unmodified -- the
    frozen v1 retention rule replayed as a CONTROL against E2's own captured
    fronts, not a new rule."""
    selections: list[SeedSelection] = []
    for sr in seed_results:
        if sr.status != "COMPLETED_WITH_FRONT" or sr.argmax_score_label_position is None:
            status = SeedStatus.EXECUTION_FAILURE if sr.status == "EXECUTION_FAILURE" else SeedStatus.COMPLETED_NO_CANDIDATE
            selections.append(SeedSelection(
                k=sr.seed_ordinal_k, seed=sr.seed, status=status,
                candidate=None, error_message=sr.error_message,
            ))
            continue
        retained_row = next((r for r in sr.rows if r.retained_by_argmax_score), None)
        if retained_row is None:  # defensive; should be unreachable given argmax_score_label_position is set
            selections.append(SeedSelection(
                k=sr.seed_ordinal_k, seed=sr.seed, status=SeedStatus.COMPLETED_NO_CANDIDATE,
                candidate=None, error_message="no row flagged retained_by_argmax_score",
            ))
            continue
        candidate = RetainedCandidate(
            k=sr.seed_ordinal_k, seed=sr.seed,
            expression_string=retained_row.expression_string,
            complexity=retained_row.engine_complexity,
            valid_r2=retained_row.valid_r2,
            invalid_fraction=retained_row.invalid_fraction,
            candidate_test_r2=retained_row.test_r2,
        )
        selections.append(SeedSelection(
            k=sr.seed_ordinal_k, seed=sr.seed,
            status=SeedStatus.COMPLETED_WITH_CANDIDATES, candidate=candidate,
        ))
    return selections


@dataclass(frozen=True)
class WorldOutcome:
    world_id: str
    cell_id: str
    family: str
    regime: str
    noise_level: str
    replicate: int
    first_loss_stage: str                 # A | B | C | D | E
    seed_outcomes: tuple[SeedOutcome, ...]
    cross_seed: CrossSeedSelection
    representative_g2_correct: Optional[bool]
    representative_truth_equivalent: Optional[bool]
    n_seeds_completed_with_front: int
    n_seeds_execution_failure: int
    n_seeds_no_candidate: int
    n_seeds_correct_on_front: int
    n_seeds_retained_correct: int


def evaluate_world(
    world: WorldContent,
    seed_results: Sequence[SeedFrontResult],
    scored_by_seed: dict[int, Sequence[ScoredRow]],
) -> WorldOutcome:
    """Section 6 of the predeclaration, applied mechanically and in order."""
    seed_outcomes: list[SeedOutcome] = []
    n_failure = n_no_candidate = n_with_front = 0
    n_correct_on_front = n_retained_correct = 0

    for sr in seed_results:
        if sr.status == "EXECUTION_FAILURE":
            n_failure += 1
            seed_outcomes.append(SeedOutcome(
                seed_ordinal_k=sr.seed_ordinal_k, seed=sr.seed, status=sr.status,
                front_size=0, correct_on_front=False, best_correct_rank=None,
                best_correct_score=None, retained_rank=None, retained_correct=False,
                score_gap=None, complexity_gap=None, r2_gap=None,
            ))
            continue
        if sr.status == "COMPLETED_NO_CANDIDATE" or not sr.rows:
            n_no_candidate += 1
            seed_outcomes.append(SeedOutcome(
                seed_ordinal_k=sr.seed_ordinal_k, seed=sr.seed, status=sr.status,
                front_size=len(sr.rows), correct_on_front=False, best_correct_rank=None,
                best_correct_score=None, retained_rank=None, retained_correct=False,
                score_gap=None, complexity_gap=None, r2_gap=None,
            ))
            continue

        n_with_front += 1
        scored_rows = scored_by_seed[sr.seed]
        assert len(scored_rows) == len(sr.rows)

        correct_rows = [(fr, sc) for fr, sc in zip(sr.rows, scored_rows) if sc.g2_correct]
        correct_on_front = len(correct_rows) > 0
        if correct_on_front:
            n_correct_on_front += 1

        best_correct = max(correct_rows, key=lambda pair: pair[0].score) if correct_rows else None
        retained = next(((fr, sc) for fr, sc in zip(sr.rows, scored_rows) if fr.retained_by_argmax_score), None)
        retained_correct = bool(retained is not None and retained[1].g2_correct)
        if retained_correct:
            n_retained_correct += 1

        score_gap = complexity_gap = r2_gap = None
        if best_correct is not None and retained is not None:
            score_gap = retained[0].score - best_correct[0].score
            complexity_gap = best_correct[0].engine_complexity - retained[0].engine_complexity
            r2_gap = best_correct[0].valid_r2 - retained[0].valid_r2

        seed_outcomes.append(SeedOutcome(
            seed_ordinal_k=sr.seed_ordinal_k, seed=sr.seed, status=sr.status,
            front_size=len(sr.rows), correct_on_front=correct_on_front,
            best_correct_rank=(best_correct[0].front_rank if best_correct else None),
            best_correct_score=(best_correct[0].score if best_correct else None),
            retained_rank=(retained[0].front_rank if retained else None),
            retained_correct=retained_correct,
            score_gap=score_gap, complexity_gap=complexity_gap, r2_gap=r2_gap,
        ))

    selections = build_seed_selections(seed_results)
    cross = group_and_select(selections)

    representative_g2_correct: Optional[bool] = None
    representative_truth_equivalent: Optional[bool] = None
    if cross.representative is not None:
        rep_seed = cross.representative.seed
        rep_expr = cross.representative.expression_string
        rep_scored = next(
            (sc for fr, sc in zip(
                next(sr.rows for sr in seed_results if sr.seed == rep_seed),
                scored_by_seed[rep_seed],
            ) if fr.expression_string == rep_expr and fr.retained_by_argmax_score),
            None,
        )
        if rep_scored is not None:
            representative_g2_correct = rep_scored.g2_correct
            representative_truth_equivalent = rep_scored.truth_equivalent

    # --- section 6 decision sequence ---
    if n_correct_on_front == 0:
        stage = "A"
    elif n_retained_correct == 0:
        stage = "B"
    elif representative_g2_correct:
        stage = "E"
    elif representative_truth_equivalent:
        stage = "D"
    else:
        stage = "C"

    return WorldOutcome(
        world_id=world.world_id, cell_id=world.cell_id, family=world.truth.family,
        regime=world.truth.regime, noise_level=world.truth.noise_level,
        replicate=world.replicate, first_loss_stage=stage,
        seed_outcomes=tuple(seed_outcomes), cross_seed=cross,
        representative_g2_correct=representative_g2_correct,
        representative_truth_equivalent=representative_truth_equivalent,
        n_seeds_completed_with_front=n_with_front, n_seeds_execution_failure=n_failure,
        n_seeds_no_candidate=n_no_candidate, n_seeds_correct_on_front=n_correct_on_front,
        n_seeds_retained_correct=n_retained_correct,
    )
