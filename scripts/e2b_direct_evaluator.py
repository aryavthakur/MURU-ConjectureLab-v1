#!/usr/bin/env python3
"""E2b direct three-way attribution evaluator.

FROZEN BEFORE REPLAY. This script implements the deterministic E2b attribution
defined in befca0d section 2.7 and the Gate 1 falsification hook defined in
f4c1105 section 4.

Primary authority chain:
  1. befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.7  (three-way attribution)
  2. f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md
     section 4  (Gate 1 falsification hook, PE2-4 tolerance)
  3. src/muru/paper_benchmark/g2_contract.py  (G2-correct definition)

The four-way partition (befca0d section 2.7):
  SUCCESS:            cross-seed selection returns a G2-correct representative
  NEVER_ON_FRONT:     0 of 30 seeds' fronts contain any G2-correct row
  LOST_IN_RETENTION:  >= 1 front has a correct row, 0 seeds' argmax(score)
                      retained candidates are correct (all lost in within-seed
                      retention)
  LOST_IN_CROSS_SEED: >= 1 seed retains a correct candidate via argmax(score),
                      but the winning equivalence class's representative is not
                      G2-correct

These are exhaustive and mutually exclusive by construction.

Gate 1 (f4c1105 section 4):
  DIRECT_RETENTION  = count(LOST_IN_RETENTION)
  DIRECT_GENERATION = count(NEVER_ON_FRONT)
  HISTORICAL_RETENTION = 69  (v1 decomposition)
  HISTORICAL_GENERATION = 57  (v1 decomposition)
  "more than 10 cases" means deviation > 10 (strict), so deviation of exactly
  10 is PASS.

This module does NOT import any historical v1 decomposition labels for
classification. It classifies from front artifacts and truth only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.g2_contract import (
    TRUTH_FAMILIES,
    FamilyStatus,
    G2Event,
    SupportStatus,
    classify_discovered_family,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
    extract_effective_support,
    truth_support_for_case,
)
from muru.paper_benchmark.registry import (
    CASE_FAMILIES,
    endpoint_applies_to_variant,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("e2b_direct_evaluator")


# -----------------------------------------------------------------------
# Constants: frozen historical values and thresholds
# -----------------------------------------------------------------------

HISTORICAL_RETENTION: int = 69
HISTORICAL_GENERATION: int = 57
FROZEN_MATERIAL_THRESHOLD: int = 10  # "more than 10" => deviation > 10
SEEDS_PER_CASE: int = 30
EXPECTED_G2_CASES: int = 144


# -----------------------------------------------------------------------
# Attribution labels
# -----------------------------------------------------------------------

class DirectClass(str, Enum):
    """The four-way E2b attribution from befca0d section 2.7."""
    SUCCESS = "SUCCESS"
    NEVER_ON_FRONT = "NEVER_ON_FRONT"
    LOST_IN_RETENTION = "LOST_IN_RETENTION"
    LOST_IN_CROSS_SEED = "LOST_IN_CROSS_SEED"


# -----------------------------------------------------------------------
# G2-correctness evaluation for a single expression
# -----------------------------------------------------------------------

def is_row_g2_correct(
    expression_string: str,
    truth_support: frozenset[str],
    truth_family: str,
) -> bool:
    """Determine whether a single front row is G2-correct.

    A row is G2-correct if its expression recovers the truth's support AND
    family.  Uses the frozen g2_contract.py functions exactly:
      1. extract_effective_support(expression_string) -> effective_support
      2. classify_discovered_family(expression_string) -> discovered_family
      3. classify_support(effective_support, truth_support) -> support_status
      4. classify_family_match(discovered_family, truth_family) -> family_status
      5. evaluate_g2_event(support_status, family_status) -> g2_event
      6. G2-correct iff g2_event == SUCCESS
    """
    effective_support = extract_effective_support(expression_string)
    discovered_family = classify_discovered_family(expression_string)
    support_status = classify_support(effective_support, truth_support)
    family_status = classify_family_match(discovered_family, truth_family)
    g2_event = evaluate_g2_event(support_status, family_status)
    return g2_event == G2Event.SUCCESS


# -----------------------------------------------------------------------
# Per-seed front evaluation
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class SeedFrontResult:
    """Result of evaluating one seed's full Pareto front for G2-correctness."""
    seed_ordinal: int
    seed: int
    front_size: int
    correct_on_front: bool       # any row on this seed's front is G2-correct
    retained_correct: bool       # the argmax(score) row is G2-correct
    correct_row_count: int       # how many rows on front are G2-correct


def evaluate_seed_front(
    front_rows: list[dict[str, Any]],
    truth_support: frozenset[str],
    truth_family: str,
) -> SeedFrontResult:
    """Evaluate a single seed's Pareto front for G2-correctness.

    Args:
        front_rows: list of dicts, each representing one row of the Pareto front.
                    Must contain 'equation' (expression string) and 'score' fields.
        truth_support: the case's truth support variables
        truth_family: the case's truth mathematical family

    Returns:
        SeedFrontResult with correct_on_front and retained_correct flags.
    """
    if not front_rows:
        return SeedFrontResult(
            seed_ordinal=front_rows[0]["_seed_ordinal"] if front_rows else -1,
            seed=front_rows[0]["_seed"] if front_rows else -1,
            front_size=0,
            correct_on_front=False,
            retained_correct=False,
            correct_row_count=0,
        )

    seed_ordinal = front_rows[0].get("_seed_ordinal", -1)
    seed = front_rows[0].get("_seed", -1)

    # Determine which row is the argmax(score) retained candidate
    best_score_idx = 0
    best_score = float("-inf")
    for i, row in enumerate(front_rows):
        score = row.get("score", float("-inf"))
        if score is None:
            continue
        score = float(score)
        if score > best_score:
            best_score = score
            best_score_idx = i

    # Check each row for G2-correctness
    any_correct = False
    retained_correct = False
    correct_count = 0

    for i, row in enumerate(front_rows):
        expr = row.get("equation", "")
        if not expr:
            continue

        correct = is_row_g2_correct(expr, truth_support, truth_family)
        if correct:
            any_correct = True
            correct_count += 1
            if i == best_score_idx:
                retained_correct = True

    return SeedFrontResult(
        seed_ordinal=seed_ordinal,
        seed=seed,
        front_size=len(front_rows),
        correct_on_front=any_correct,
        retained_correct=retained_correct,
        correct_row_count=correct_count,
    )


# -----------------------------------------------------------------------
# Three-way attribution for one case
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseAttribution:
    """E2b three-way attribution result for one case."""
    case_id: str
    direct_class: DirectClass
    seeds_with_correct_on_front: int
    seeds_with_retained_correct: int
    representative_correct: bool
    valid: bool
    invalid_reason: str | None
    seed_results: tuple[SeedFrontResult, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "direct_class": self.direct_class.value,
            "seeds_with_correct_on_front": self.seeds_with_correct_on_front,
            "seeds_with_retained_correct": self.seeds_with_retained_correct,
            "representative_correct": self.representative_correct,
            "valid": self.valid,
            "invalid_reason": self.invalid_reason,
        }


def classify_case(
    case_id: str,
    seed_results: Sequence[SeedFrontResult],
    representative_expression: str | None,
    truth_support: frozenset[str],
    truth_family: str,
) -> CaseAttribution:
    """Apply the befca0d section 2.7 four-way attribution to one case.

    Decision tree (exhaustive, mutually exclusive):
    1. SUCCESS: the cross-seed representative is G2-correct
    2. NEVER_ON_FRONT: 0 of 30 seeds' fronts contain any G2-correct row
    3. LOST_IN_CROSS_SEED: >= 1 seed retains a correct candidate (argmax(score)),
       but the winning class's representative is not correct
    4. LOST_IN_RETENTION: >= 1 front has a correct row, but 0 seeds retain
       a correct candidate (all lost in within-seed argmax(score) selection)

    This module classifies from front artifacts and truth only. It does NOT
    import or use any historical v1 decomposition labels.
    """
    seeds_with_correct_on_front = sum(
        1 for sr in seed_results if sr.correct_on_front
    )
    seeds_with_retained_correct = sum(
        1 for sr in seed_results if sr.retained_correct
    )

    # Determine if the cross-seed representative is G2-correct
    representative_correct = False
    if representative_expression is not None:
        representative_correct = is_row_g2_correct(
            representative_expression, truth_support, truth_family
        )

    # Validate: we expect exactly SEEDS_PER_CASE seed results
    if len(seed_results) != SEEDS_PER_CASE:
        return CaseAttribution(
            case_id=case_id,
            direct_class=DirectClass.NEVER_ON_FRONT,  # placeholder
            seeds_with_correct_on_front=seeds_with_correct_on_front,
            seeds_with_retained_correct=seeds_with_retained_correct,
            representative_correct=representative_correct,
            valid=False,
            invalid_reason=(
                f"Expected {SEEDS_PER_CASE} seed results, got {len(seed_results)}"
            ),
            seed_results=tuple(seed_results),
        )

    # Apply the four-way partition (befca0d section 2.7)
    if representative_correct:
        direct_class = DirectClass.SUCCESS
    elif seeds_with_correct_on_front == 0:
        direct_class = DirectClass.NEVER_ON_FRONT
    elif seeds_with_retained_correct >= 1:
        # Correct rows survived retention in at least one seed, but the
        # winning class's representative is not correct => lost in cross-seed
        direct_class = DirectClass.LOST_IN_CROSS_SEED
    else:
        # seeds_with_correct_on_front >= 1 AND seeds_with_retained_correct == 0
        # Correct rows on fronts but NONE survived argmax(score) retention
        direct_class = DirectClass.LOST_IN_RETENTION

    return CaseAttribution(
        case_id=case_id,
        direct_class=direct_class,
        seeds_with_correct_on_front=seeds_with_correct_on_front,
        seeds_with_retained_correct=seeds_with_retained_correct,
        representative_correct=representative_correct,
        valid=True,
        invalid_reason=None,
        seed_results=tuple(seed_results),
    )


# -----------------------------------------------------------------------
# Gate 1: falsification hook
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class GateResult:
    """Result of the Gate 1 falsification hook (f4c1105 section 4)."""
    direct_retention: int      # count(LOST_IN_RETENTION)
    direct_generation: int     # count(NEVER_ON_FRONT)
    direct_third_class: int    # count(SUCCESS) + count(LOST_IN_CROSS_SEED)
    invalid_cases: int
    retention_deviation: int   # abs(direct_retention - 69)
    generation_deviation: int  # abs(direct_generation - 57)
    threshold_triggered: bool  # True if EITHER deviation > 10
    e2b_69_57_hook: str       # "PASS" or "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "DIRECT_RETENTION": self.direct_retention,
            "DIRECT_GENERATION": self.direct_generation,
            "DIRECT_THIRD_CLASS": self.direct_third_class,
            "INVALID_CASES": self.invalid_cases,
            "HISTORICAL_RETENTION": HISTORICAL_RETENTION,
            "HISTORICAL_GENERATION": HISTORICAL_GENERATION,
            "RETENTION_DEVIATION": self.retention_deviation,
            "GENERATION_DEVIATION": self.generation_deviation,
            "FROZEN_MATERIAL_THRESHOLD": FROZEN_MATERIAL_THRESHOLD,
            "THRESHOLD_TRIGGERED": "YES" if self.threshold_triggered else "NO",
            "E2B_69_57_HOOK": self.e2b_69_57_hook,
        }


def evaluate_gate_1(attributions: Sequence[CaseAttribution]) -> GateResult:
    """Evaluate Gate 1: the 69/57 falsification hook.

    From f4c1105 section 4:
    "IF E2b's direct measurement contradicts the v1 decomposition's
    69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
    tolerance) -- THEN this protocol DOES NOT EXECUTE."

    "more than 10 cases" means > 10 (strict inequality), so:
    - deviation of 10 is PASS (within tolerance)
    - deviation of 11 is FAIL (more than 10)
    """
    valid = [a for a in attributions if a.valid]
    invalid_count = sum(1 for a in attributions if not a.valid)

    direct_retention = sum(
        1 for a in valid if a.direct_class == DirectClass.LOST_IN_RETENTION
    )
    direct_generation = sum(
        1 for a in valid if a.direct_class == DirectClass.NEVER_ON_FRONT
    )
    direct_success = sum(
        1 for a in valid if a.direct_class == DirectClass.SUCCESS
    )
    direct_cross_seed = sum(
        1 for a in valid if a.direct_class == DirectClass.LOST_IN_CROSS_SEED
    )
    direct_third_class = direct_success + direct_cross_seed

    retention_deviation = abs(direct_retention - HISTORICAL_RETENTION)
    generation_deviation = abs(direct_generation - HISTORICAL_GENERATION)

    # "more than 10 cases" => > 10 (strict), not >= 10
    threshold_triggered = (
        retention_deviation > FROZEN_MATERIAL_THRESHOLD
        or generation_deviation > FROZEN_MATERIAL_THRESHOLD
    )
    e2b_hook = "FAIL" if threshold_triggered else "PASS"

    return GateResult(
        direct_retention=direct_retention,
        direct_generation=direct_generation,
        direct_third_class=direct_third_class,
        invalid_cases=invalid_count,
        retention_deviation=retention_deviation,
        generation_deviation=generation_deviation,
        threshold_triggered=threshold_triggered,
        e2b_69_57_hook=e2b_hook,
    )


# -----------------------------------------------------------------------
# Front artifact loading
# -----------------------------------------------------------------------

def load_front_rows(front_path: Path) -> list[dict[str, Any]]:
    """Load a single seed's Pareto front from a JSONL file."""
    rows = []
    with open(front_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_case_fronts(
    fronts_dir: Path,
    case_id: str,
) -> dict[int, list[dict[str, Any]]]:
    """Load all 30 seeds' fronts for a single case.

    Returns: {seed_ordinal: [row_dicts]}
    """
    case_dir_name = case_id.replace("|", "_")
    case_dir = fronts_dir / case_dir_name

    if not case_dir.is_dir():
        return {}

    fronts_by_ordinal: dict[int, list[dict[str, Any]]] = {}

    for jsonl_file in sorted(case_dir.glob("*.jsonl")):
        rows = load_front_rows(jsonl_file)
        if not rows:
            continue
        # Determine seed ordinal from the first row's _seed_ordinal field
        # or from filename (seed value)
        ordinal = rows[0].get("_seed_ordinal")
        if ordinal is not None:
            fronts_by_ordinal[int(ordinal)] = rows
        else:
            # fallback: use filename-based ordering
            seed_val = int(jsonl_file.stem)
            fronts_by_ordinal[seed_val] = rows

    return fronts_by_ordinal


# -----------------------------------------------------------------------
# Case enumeration (frozen G2 case IDs)
# -----------------------------------------------------------------------

def get_g2_case_ids() -> list[str]:
    """Return the frozen 144 G2 (family_recovery) case IDs.

    Replicates the same logic as run_e2b_fullfront_replay.py::get_g2_case_ids(),
    using registry-level enumeration.
    """
    cases = []
    for fam in CASE_FAMILIES:
        for r in range(fam.partition_counts.get("held_out", 0)):
            case_id = f"PB|held_out|{fam.code}|r{r:03d}"
            variant = fam.variant_for_replicate(r)
            if endpoint_applies_to_variant("family_recovery", variant):
                cases.append(case_id)
    assert len(cases) == EXPECTED_G2_CASES, (
        f"Expected {EXPECTED_G2_CASES} G2 cases, got {len(cases)}"
    )
    return cases


# -----------------------------------------------------------------------
# Full evaluation pipeline
# -----------------------------------------------------------------------

def evaluate_all_cases(
    fronts_dir: Path,
    replay_report_path: Path | None = None,
) -> tuple[list[CaseAttribution], GateResult]:
    """Run the full E2b direct attribution on all 144 G2 cases.

    Args:
        fronts_dir: directory containing per-case front subdirectories
        replay_report_path: optional path to E2B_FULLFRONT_REPLAY_REPORT.json
                           for representative expression lookup

    Returns:
        (list of CaseAttribution, GateResult)
    """
    from muru.paper_benchmark.generator import generate_case

    case_ids = get_g2_case_ids()

    # Load representative expressions from replay report if available
    representatives: dict[str, str | None] = {}
    if replay_report_path and replay_report_path.exists():
        report = json.loads(replay_report_path.read_text(encoding="utf-8"))
        for detail in report.get("comparison_details", []):
            cid = detail.get("case_id", "")
            representatives[cid] = detail.get("representative_replayed")

    attributions: list[CaseAttribution] = []

    for case_id in case_ids:
        logger.info(f"Evaluating {case_id}...")

        # Generate truth for this case
        generated = generate_case(case_id)
        truth = generated.truth

        if truth.mathematical_family not in TRUTH_FAMILIES:
            attributions.append(CaseAttribution(
                case_id=case_id,
                direct_class=DirectClass.NEVER_ON_FRONT,
                seeds_with_correct_on_front=0,
                seeds_with_retained_correct=0,
                representative_correct=False,
                valid=False,
                invalid_reason=(
                    f"Truth family {truth.mathematical_family!r} not in TRUTH_FAMILIES"
                ),
            ))
            continue

        truth_support = truth_support_for_case(truth)
        truth_family = truth.mathematical_family

        # Load all seed fronts for this case
        case_fronts = load_case_fronts(fronts_dir, case_id)

        if not case_fronts:
            attributions.append(CaseAttribution(
                case_id=case_id,
                direct_class=DirectClass.NEVER_ON_FRONT,
                seeds_with_correct_on_front=0,
                seeds_with_retained_correct=0,
                representative_correct=False,
                valid=False,
                invalid_reason="No front artifacts found for this case",
            ))
            continue

        # Evaluate each seed's front
        seed_results: list[SeedFrontResult] = []
        for ordinal in range(SEEDS_PER_CASE):
            front_rows = case_fronts.get(ordinal, [])
            if not front_rows:
                seed_results.append(SeedFrontResult(
                    seed_ordinal=ordinal,
                    seed=-1,
                    front_size=0,
                    correct_on_front=False,
                    retained_correct=False,
                    correct_row_count=0,
                ))
            else:
                seed_results.append(
                    evaluate_seed_front(front_rows, truth_support, truth_family)
                )

        # Get the representative expression
        rep_expr = representatives.get(case_id)

        # Classify the case
        attribution = classify_case(
            case_id=case_id,
            seed_results=seed_results,
            representative_expression=rep_expr,
            truth_support=truth_support,
            truth_family=truth_family,
        )
        attributions.append(attribution)

    gate = evaluate_gate_1(attributions)
    return attributions, gate


# -----------------------------------------------------------------------
# Evaluator hash (results blindness)
# -----------------------------------------------------------------------

def compute_evaluator_sha256() -> str:
    """Compute SHA-256 of this evaluator script for results-blindness verification."""
    script_path = Path(__file__).resolve()
    content = script_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


# -----------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="E2b direct three-way attribution evaluator"
    )
    parser.add_argument(
        "--fronts-dir",
        type=Path,
        default=ROOT / "results" / "e2b_macos_fullfront_replay_20260818" / "fronts",
        help="Directory containing per-case front subdirectories",
    )
    parser.add_argument(
        "--replay-report",
        type=Path,
        default=ROOT / "results" / "e2b_macos_fullfront_replay_20260818" / "E2B_FULLFRONT_REPLAY_REPORT.json",
        help="Path to E2B_FULLFRONT_REPLAY_REPORT.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "e2b_direct_attribution.json",
        help="Output path for attribution results",
    )
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Only compute and print the evaluator SHA-256, then exit",
    )
    args = parser.parse_args()

    evaluator_sha = compute_evaluator_sha256()

    if args.hash_only:
        print(f"EVALUATOR_SHA256: {evaluator_sha}")
        return 0

    logger.info("=" * 70)
    logger.info("E2b DIRECT THREE-WAY ATTRIBUTION EVALUATOR")
    logger.info(f"EVALUATOR_SHA256: {evaluator_sha}")
    logger.info("=" * 70)

    attributions, gate = evaluate_all_cases(
        fronts_dir=args.fronts_dir,
        replay_report_path=args.replay_report,
    )

    # Emit per-case results
    per_case = [a.to_dict() for a in attributions]

    # Emit aggregate
    aggregate = gate.to_dict()

    output = {
        "schema": "e2b-direct-attribution-1.0.0",
        "evaluator_sha256": evaluator_sha,
        "primary_authority": {
            "three_way_attribution": "befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.7",
            "gate_1_falsification": "f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md section 4",
            "g2_correct_definition": "src/muru/paper_benchmark/g2_contract.py",
        },
        "cases": per_case,
        "aggregate": aggregate,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Results written to {args.output}")

    # Print summary
    logger.info("=" * 70)
    logger.info("AGGREGATE RESULTS")
    for k, v in aggregate.items():
        logger.info(f"  {k}: {v}")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
