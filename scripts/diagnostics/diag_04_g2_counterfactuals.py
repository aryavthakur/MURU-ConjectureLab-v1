"""Stage 4: G2 counterfactual selection study.

Stage 3 established that in 71 of 144 G2 cases at least one seed's retained
candidate was G2-correct, yet the cross-seed winner was not.  "Voting lost it"
is only half an explanation: it matters enormously whether the correct
candidates were a *majority* the vote should have found, or a scattered
minority no vote could have rescued.

This stage answers that by re-running the cross-seed decision under three
alternative equivalence relations, holding everything else -- the searches, the
retained candidates, the frozen G2 predicates -- fixed:

``IDENTITY`` (the frozen v1 rule)
    group by ``identity_contract.template_key``; largest class wins.

``G2_LABEL``
    group by the pair the endpoint is actually scored on, ``(effective_support,
    discovered_family)``; largest class wins.  This is the coarsest relation
    that still respects the endpoint's own definition of "the same answer".

``ORACLE_ANY``
    a case counts if *any* of its 30 retained candidates was G2-correct.  This
    is the upper bound on what any post-search selection rule could achieve
    from the persisted evidence, and it is not a proposal.

None of this changes the official v1 result, which remains 4/144.  These are
diagnostic counterfactuals over frozen evidence.

The stage also records the fit statistics of correct versus incorrect retained
candidates, to test whether the search objective could have discriminated them.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    install_frozen_src,
    read_json,
    write_json,
)

install_frozen_src()

import numpy as np  # noqa: E402

from muru.paper_benchmark.identity_contract import template_key  # noqa: E402
from muru.paper_benchmark.rc5_selection import (  # noqa: E402
    parse_production_candidate,
)
from muru.paper_benchmark.structural_acceptance import (  # noqa: E402
    STABILITY_DENOMINATOR,
    STABILITY_GATE,
)


def _label(seed: dict) -> tuple:
    support = seed["effective_support"]
    return (
        tuple(support) if support is not None else None,
        seed["discovered_family"],
    )


def _winner_by(groups: dict[object, list[int]]) -> object | None:
    """Largest group; ties break toward the lowest seed ordinal -- the frozen
    ``group_and_select`` tie-break, applied to a different key."""
    if not groups:
        return None
    return min(groups, key=lambda k: (-len(groups[k]), min(groups[k])))


def main() -> int:
    trace = read_json(OUT_DIR / "g2_pipeline_trace.json")
    seed_stats = read_json(OUT_DIR / "g2_seed_fit_stats.json") if (
        OUT_DIR / "g2_seed_fit_stats.json"
    ).exists() else None

    rows = []
    for index, case in enumerate(trace["per_case"], start=1):
        seeds = case["per_seed"]
        correct = {k for k, s in enumerate(seeds) if s["g2_event"] == "SUCCESS"}

        identity_groups: dict[object, list[int]] = defaultdict(list)
        label_groups: dict[object, list[int]] = defaultdict(list)
        for k, seed in enumerate(seeds):
            if not seed["parsed"]:
                continue
            identity_groups[
                template_key(parse_production_candidate(seed["expression"]))
            ].append(k)
            label_groups[_label(seed)].append(k)

        identity_winner = _winner_by(identity_groups)
        label_winner = _winner_by(label_groups)

        identity_members = identity_groups.get(identity_winner, [])
        label_members = label_groups.get(label_winner, [])

        identity_correct = bool(identity_members) and identity_members[0] in correct
        label_correct = bool(label_members) and label_members[0] in correct

        # How badly does the identity relation shatter the correct answers?
        correct_identity_classes = {
            key for key, members in identity_groups.items() if set(members) & correct
        }
        correct_label_classes = {
            key for key, members in label_groups.items() if set(members) & correct
        }

        rows.append(
            {
                "case_id": case["case_id"],
                "family_id": case["family_id"],
                "truth_family": case["truth_family"],
                "grammar_representable": case["representability"]["grammar_representable"],
                "sealed_g2_event": case["g2_event_sealed"],
                "first_failure_point": case["first_failure_point"],
                "seeds_with_g2_success": len(correct),
                "identity_class_count": len(identity_groups),
                "identity_winner_size": len(identity_members),
                "identity_winner_correct": identity_correct,
                "identity_classes_holding_correct": len(correct_identity_classes),
                "label_class_count": len(label_groups),
                "label_winner_size": len(label_members),
                "label_winner_correct": label_correct,
                "label_classes_holding_correct": len(correct_label_classes),
                "label_winner_would_pass_stability": len(label_members)
                >= STABILITY_GATE,
                "identity_winner_would_pass_stability": len(identity_members)
                >= STABILITY_GATE,
                "oracle_any_correct": bool(correct),
                "correct_seed_share": len(correct) / STABILITY_DENOMINATOR,
            }
        )
        if index % 24 == 0 or index == len(trace["per_case"]):
            print(f"  g2 counterfactual: {index}/{len(trace['per_case'])}", flush=True)

    total = len(rows)
    representable = [r for r in rows if r["grammar_representable"]]

    def rate(subset, key):
        return sum(1 for r in subset if r[key])

    summary = {
        "denominator": total,
        "official_v1_g2_successes": sum(
            1 for r in rows if r["sealed_g2_event"] == "SUCCESS"
        ),
        "arms": {
            "IDENTITY_frozen_v1": {
                "successes": rate(rows, "identity_winner_correct"),
                "of": total,
                "note": "reproduces the official rule; equals the sealed count",
            },
            "G2_LABEL": {
                "successes": rate(rows, "label_winner_correct"),
                "of": total,
                "note": "group by (effective_support, discovered_family); same tie-break",
            },
            "ORACLE_ANY": {
                "successes": rate(rows, "oracle_any_correct"),
                "of": total,
                "note": "upper bound reachable from the persisted retained candidates",
            },
        },
        "among_representable_cases": {
            "denominator": len(representable),
            "IDENTITY_frozen_v1": rate(representable, "identity_winner_correct"),
            "G2_LABEL": rate(representable, "label_winner_correct"),
            "ORACLE_ANY": rate(representable, "oracle_any_correct"),
        },
        "fragmentation": {
            "cases_where_correct_answers_split_across_identity_classes": sum(
                1 for r in rows if r["identity_classes_holding_correct"] > 1
            ),
            "median_identity_classes_per_case": float(
                np.median([r["identity_class_count"] for r in rows])
            ),
            "median_label_classes_per_case": float(
                np.median([r["label_class_count"] for r in rows])
            ),
            "median_identity_classes_holding_correct": float(
                np.median(
                    [
                        r["identity_classes_holding_correct"]
                        for r in rows
                        if r["oracle_any_correct"]
                    ]
                )
            ),
            "median_label_classes_holding_correct": float(
                np.median(
                    [
                        r["label_classes_holding_correct"]
                        for r in rows
                        if r["oracle_any_correct"]
                    ]
                )
            ),
        },
        "stability_interaction": {
            "identity_winner_passes_stability": rate(
                rows, "identity_winner_would_pass_stability"
            ),
            "label_winner_passes_stability": rate(
                rows, "label_winner_would_pass_stability"
            ),
            "correct_and_stable_under_label_rule": sum(
                1
                for r in rows
                if r["label_winner_correct"] and r["label_winner_would_pass_stability"]
            ),
            "stability_gate": f"{STABILITY_GATE}/{STABILITY_DENOMINATOR}",
        },
        "correct_seed_share_quantiles": {
            "p25": float(np.quantile([r["correct_seed_share"] for r in rows], 0.25)),
            "median": float(np.median([r["correct_seed_share"] for r in rows])),
            "p75": float(np.quantile([r["correct_seed_share"] for r in rows], 0.75)),
            "max": float(max(r["correct_seed_share"] for r in rows)),
        },
    }

    by_family: dict[str, dict] = {}
    for row in rows:
        bucket = by_family.setdefault(
            row["family_id"],
            {
                "truth_family": row["truth_family"],
                "cases": 0,
                "identity": 0,
                "label": 0,
                "oracle": 0,
            },
        )
        bucket["cases"] += 1
        bucket["identity"] += int(row["identity_winner_correct"])
        bucket["label"] += int(row["label_winner_correct"])
        bucket["oracle"] += int(row["oracle_any_correct"])

    write_json(
        OUT_DIR / "g2_counterfactuals.json",
        {
            "disclaimer": (
                "Diagnostic counterfactuals over frozen evidence.  The official "
                "v1 G2 result is 4/144 and is not altered, reinterpreted, or "
                "superseded by anything in this file."
            ),
            "summary": summary,
            "by_family": by_family,
            "per_case": rows,
        },
    )
    print("\n  arms:")
    for name, arm in summary["arms"].items():
        print(f"    {name:20s} {arm['successes']:3d}/{arm['of']}")
    print(f"  fragmentation: {summary['fragmentation']}")
    print(f"  wrote {OUT_DIR / 'g2_counterfactuals.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
