"""Stage 5: does the per-seed retention rule trade accuracy for parsimony?

Stage 4 showed that a G2-correct candidate reached cross-seed selection in 75 of
144 cases but was the modal answer in essentially none.  The obvious suspect is
the *within-seed* retention rule.

``rc5_selection`` section 7.1 retains ``argmax(score)`` of each seed's Pareto
front, where ``score`` is PySR's own negated derivative of log-loss with respect
to complexity -- a marginal-return-per-unit-complexity heuristic, not an accuracy
criterion.  If that rule is systematically preferring a short, low-accuracy
mass-only expression over a longer, high-accuracy correct-family one, then
within each case the *correct* retained candidates should carry both higher
``valid_r2`` and higher ``complexity`` than the incorrect ones, and the gap
should be large.

This stage measures that gap case by case, paired within case so that
case-to-case difficulty cannot confound it.  It reads only sealed per-seed
values (``valid_r2``, ``complexity``) -- nothing is refitted and no search runs.

The within-seed Pareto front is not persisted (``WITHIN_SEED_PARETO_NOT_
OBSERVABLE``), so this is evidence about which candidate the rule *kept* when
seeds disagreed, not proof about what each individual front contained.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    load_seed_records,
    read_json,
    write_json,
)

import numpy as np  # noqa: E402


def main() -> int:
    trace = read_json(OUT_DIR / "g2_pipeline_trace.json")
    seed_records = load_seed_records()

    rows = []
    paired_r2: list[float] = []
    paired_complexity: list[float] = []

    for case in trace["per_case"]:
        case_id = case["case_id"]
        seeds = sorted(seed_records[case_id], key=lambda r: r["seed"])
        replays = case["per_seed"]
        if len(seeds) != len(replays):
            raise SystemExit(f"{case_id}: seed/replay length mismatch")

        correct_r2, wrong_r2 = [], []
        correct_cx, wrong_cx = [], []
        for seed, replay in zip(seeds, replays):
            if seed["status"] != "COMPLETED_WITH_CANDIDATES":
                continue
            bucket_r2 = correct_r2 if replay["g2_event"] == "SUCCESS" else wrong_r2
            bucket_cx = correct_cx if replay["g2_event"] == "SUCCESS" else wrong_cx
            bucket_r2.append(float(seed["valid_r2"]))
            bucket_cx.append(int(seed["complexity"]))

        row = {
            "case_id": case_id,
            "family_id": case["family_id"],
            "truth_family": case["truth_family"],
            "n_correct_seeds": len(correct_r2),
            "n_incorrect_seeds": len(wrong_r2),
            "mean_valid_r2_correct": float(np.mean(correct_r2)) if correct_r2 else None,
            "mean_valid_r2_incorrect": float(np.mean(wrong_r2)) if wrong_r2 else None,
            "mean_complexity_correct": float(np.mean(correct_cx)) if correct_cx else None,
            "mean_complexity_incorrect": float(np.mean(wrong_cx)) if wrong_cx else None,
            "max_valid_r2_any_seed": float(max(correct_r2 + wrong_r2))
            if (correct_r2 or wrong_r2)
            else None,
        }
        if correct_r2 and wrong_r2:
            row["delta_valid_r2"] = row["mean_valid_r2_correct"] - row["mean_valid_r2_incorrect"]
            row["delta_complexity"] = (
                row["mean_complexity_correct"] - row["mean_complexity_incorrect"]
            )
            paired_r2.append(row["delta_valid_r2"])
            paired_complexity.append(row["delta_complexity"])
        else:
            row["delta_valid_r2"] = None
            row["delta_complexity"] = None
        rows.append(row)

    def describe(values: list[float]) -> dict:
        array = np.asarray(values, dtype=float)
        return {
            "n": int(array.size),
            "mean": float(array.mean()),
            "median": float(np.median(array)),
            "p05": float(np.quantile(array, 0.05)),
            "p95": float(np.quantile(array, 0.95)),
            "fraction_positive": float((array > 0).mean()),
        }

    # Sign test on the paired within-case deltas: how often is the correct
    # candidate the more accurate *and* the more complex one?
    both_ways = sum(
        1
        for r in rows
        if r["delta_valid_r2"] is not None
        and r["delta_valid_r2"] > 0
        and r["delta_complexity"] > 0
    )

    summary = {
        "paired_cases": len(paired_r2),
        "delta_valid_r2_correct_minus_incorrect": describe(paired_r2),
        "delta_complexity_correct_minus_incorrect": describe(paired_complexity),
        "cases_where_correct_is_both_more_accurate_and_more_complex": both_ways,
        "interpretation_guard": (
            "A positive r2 delta paired with a positive complexity delta is "
            "consistent with argmax(score) discarding the accurate candidate for "
            "the parsimonious one.  It is not proof: the per-seed Pareto fronts "
            "are not persisted, so this measures which candidate the rule kept "
            "across disagreeing seeds, not what each front held."
        ),
    }

    write_json(
        OUT_DIR / "retention_objective.json",
        {"summary": summary, "per_case": rows},
    )
    print("  delta valid_r2 :", summary["delta_valid_r2_correct_minus_incorrect"])
    print("  delta complexity:", summary["delta_complexity_correct_minus_incorrect"])
    print(
        f"  correct is both more accurate and more complex in "
        f"{both_ways}/{len(paired_r2)} paired cases"
    )
    print(f"  wrote {OUT_DIR / 'retention_objective.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
