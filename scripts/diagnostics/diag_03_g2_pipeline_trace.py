"""Stage 3: trace all 144 G2-eligible cases through the symbolic-recovery pipeline.

The sealed record reports only the *final* ``support_status`` / ``family_status``
pair.  This stage reconstructs every stage that could have destroyed a correct
answer, using the frozen predicates unmodified:

1. **Representability** -- can the frozen grammar even express the planted
   relationship, and can the frozen classifier ever emit its family label?
2. **Generation** -- replay ``extract_effective_support`` and
   ``classify_discovered_family`` over each case's 30 sealed per-seed retained
   candidates, so "was the right thing ever produced" is answered per seed
   rather than assumed.
3. **Cross-seed voting** -- rebuild the identity-contract grouping with the
   frozen ``group_and_select`` and check it reproduces the sealed
   ``selection_count`` / representative.  Then ask whether a truth-correct
   candidate existed in a *losing* class.
4. **Acceptance** -- read the sealed gate the case stopped at.
5. **First irreversible failure point** -- the earliest stage above at which the
   correct answer became unreachable.

## What the sealed evidence cannot show

``rc5_selection`` section 7.1 retains exactly **one** row per seed --
``argmax(score)`` of that seed's PySR Pareto front -- and only that row is
persisted.  The front itself is gone.  So "truth was never generated" is
established here at the granularity of *the 30 candidates cross-seed selection
actually chose between*, which is the population every later stage saw.  A
truth-equivalent expression that sat on a Pareto front but lost the within-seed
``score`` argmax would be invisible to this replay, and is reported as the
explicitly bounded quantity ``WITHIN_SEED_PARETO_NOT_OBSERVABLE`` rather than
silently folded into "search failure".
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    eligible_case_ids,
    install_frozen_src,
    load_case_manifest,
    load_sealed_records,
    load_seed_records,
    load_truth,
    write_json,
)

install_frozen_src()

import sympy  # noqa: E402

from muru.discovery.grammar import (  # noqa: E402
    BINARY_OPERATORS,
    UNARY_OPERATORS,
)
from muru.paper_benchmark.calibration_contract import SeedStatus  # noqa: E402
from muru.paper_benchmark.g2_contract import (  # noqa: E402
    TRUTH_FAMILIES,
    FamilyStatus,
    SupportStatus,
    _safe_parse,
    classify_discovered_family,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
    extract_effective_support,
)
from muru.paper_benchmark.rc5_selection import (  # noqa: E402
    RetainedCandidate,
    SeedSelection,
    group_and_select,
)

#: Which grammar constructs each truth family needs, read off the frozen
#: ``descriptor_relationship`` strings and the frozen classifier's own tests.
FAMILY_REQUIREMENTS: dict[str, dict] = {
    "mass_affine_descriptor": {
        "relationship": "sqrt(mass) * (1 + coefficient * descriptor)",
        "operators_needed": ("sqrt", "*", "+"),
        "classifier_test": "_is_linear_in(expr, descriptor)",
    },
    "mass_saturating_descriptor": {
        "relationship": "sqrt(mass) * (1 + coefficient * descriptor/(1+descriptor))",
        "operators_needed": ("sqrt", "*", "+", "/"),
        "classifier_test": "_contains_saturating: a Pow with exp == -1 whose base is affine in descriptor",
    },
    "mass_interaction": {
        "relationship": "sqrt(mass) * (1 + coefficient * descriptor * descriptor2)",
        "operators_needed": ("sqrt", "*", "+"),
        "classifier_test": "_contains_product(expr, descriptor, descriptor2)",
    },
    "mass_exponential_descriptor": {
        "relationship": "sqrt(mass) * exp(coefficient * descriptor / 3)",
        "operators_needed": ("sqrt", "*", "exp"),
        "classifier_test": "_contains_exp_of: a literal sympy.exp node containing descriptor",
    },
    "mass_power": {
        "relationship": "mass ** exponent",
        "operators_needed": ("sqrt",),
        "classifier_test": "support == {mass}",
    },
}

GRAMMAR_OPERATORS = frozenset(BINARY_OPERATORS) | frozenset(UNARY_OPERATORS)


def representability(truth_family: str) -> dict:
    """Can the frozen grammar produce an expression the frozen classifier will
    label ``truth_family``?"""
    spec = FAMILY_REQUIREMENTS[truth_family]
    missing = [op for op in spec["operators_needed"] if op not in GRAMMAR_OPERATORS]
    return {
        "truth_family": truth_family,
        "relationship": spec["relationship"],
        "operators_needed": list(spec["operators_needed"]),
        "operators_missing_from_grammar": missing,
        "grammar_representable": not missing,
        "classifier_test": spec["classifier_test"],
        "classifier_label_reachable": not missing,
    }


def replay_seed(expr: str, truth_support: frozenset[str], truth_family: str) -> dict:
    """Apply the frozen G2 predicates to one seed's retained candidate."""
    parsed = _safe_parse(expr)
    support = extract_effective_support(expr)
    family = classify_discovered_family(expr)
    support_status = classify_support(support, truth_support)
    family_status = classify_family_match(family, truth_family)
    event = evaluate_g2_event(support_status, family_status)
    contains_exp = False
    if parsed is not None:
        try:
            contains_exp = any(
                isinstance(node, sympy.exp)
                for node in sympy.preorder_traversal(sympy.simplify(parsed))
            )
        except Exception:
            contains_exp = False
    return {
        "expression": expr,
        "parsed": parsed is not None,
        "effective_support": sorted(support) if support is not None else None,
        "discovered_family": family,
        "support_status": support_status.value,
        "family_status": family_status.value,
        "g2_event": event.value,
        "contains_exp_after_simplify": contains_exp,
    }


def _first_failure_point(case: dict) -> tuple[str, str]:
    """Earliest stage at which a G2 success became unreachable."""
    if case["g2_event_sealed"] == "SUCCESS":
        return "NONE", "case is a G2 success"

    if not case["representability"]["classifier_label_reachable"]:
        missing = ",".join(case["representability"]["operators_missing_from_grammar"])
        return (
            "REPRESENTATION",
            f"frozen grammar lacks {missing}; the classifier can never emit "
            f"{case['truth_family']}, so no search outcome could have succeeded",
        )

    if case["seeds_with_g2_success"] == 0:
        if case["seeds_with_family_match"] == 0 and case["seeds_with_support_match"] == 0:
            return (
                "GENERATION",
                "no seed's retained candidate matched truth support or truth family",
            )
        if case["seeds_with_support_match"] == 0:
            return (
                "GENERATION_SUPPORT",
                f"{case['seeds_with_family_match']}/30 seeds reached the right family "
                f"but no seed reached the right effective support",
            )
        return (
            "GENERATION_FAMILY",
            f"{case['seeds_with_support_match']}/30 seeds reached the right support "
            f"but no seed reached the right family",
        )

    if case["winning_class_g2_event"] == "SUCCESS":
        return (
            "ACCEPTANCE",
            f"cross-seed winner was G2-correct; the case stopped at the "
            f"{case['acceptance_gate_reached']} gate "
            f"({case['acceptance_status']})",
        )

    return (
        "SELECTION_VOTING",
        f"{case['seeds_with_g2_success']}/30 seeds produced a G2-correct candidate "
        f"but the largest identity class was a different expression "
        f"(winner held {case['selection_count_replayed']} votes)",
    )


def main() -> int:
    manifest = load_case_manifest()
    sealed = load_sealed_records()
    seeds = load_seed_records()
    truth = load_truth()

    case_ids = eligible_case_ids("G2", manifest)
    if len(case_ids) != 144:
        raise SystemExit(f"expected 144 G2 cases, got {len(case_ids)}")

    rows = []
    replay_mismatches = []
    for index, case_id in enumerate(case_ids, start=1):
        record = sealed[case_id]
        planted = truth[case_id]
        truth_family = planted["mathematical_family"]
        if truth_family not in TRUTH_FAMILIES:
            raise SystemExit(f"{case_id}: unknown truth family {truth_family!r}")
        truth_support = frozenset(record["truth_support"])

        rep = representability(truth_family)

        seed_rows = sorted(seeds[case_id], key=lambda r: r["seed"])
        if len(seed_rows) != 30:
            raise SystemExit(f"{case_id}: {len(seed_rows)} seed rows, expected 30")

        replays = []
        selections = []
        for ordinal, row in enumerate(seed_rows):
            expression = row.get("selected_expression_string") or ""
            status = row["status"]
            if status == "COMPLETED_WITH_CANDIDATES" and expression:
                replays.append(replay_seed(expression, truth_support, truth_family))
                selections.append(
                    SeedSelection(
                        k=ordinal,
                        seed=row["seed"],
                        status=SeedStatus.COMPLETED_WITH_CANDIDATES,
                        candidate=RetainedCandidate(
                            k=ordinal,
                            seed=row["seed"],
                            expression_string=expression,
                            complexity=int(row["complexity"]),
                            valid_r2=float(row["valid_r2"]),
                            invalid_fraction=float(row["invalid_fraction"]),
                            candidate_test_r2=float("nan"),
                        ),
                    )
                )
            else:
                replays.append(
                    {
                        "expression": expression,
                        "parsed": False,
                        "effective_support": None,
                        "discovered_family": None,
                        "support_status": "SUPPORT_UNRESOLVED",
                        "family_status": "FAMILY_UNRESOLVED",
                        "g2_event": "UNEVALUABLE",
                        "contains_exp_after_simplify": False,
                        "seed_status": status,
                    }
                )
                selections.append(
                    SeedSelection(k=ordinal, seed=row["seed"], status=SeedStatus(status))
                )

        cross = group_and_select(selections)
        replayed_count = cross.selection_count
        representative = (
            cross.representative.expression_string if cross.representative else ""
        )
        replay_ok = (
            replayed_count == record["selection_count"]
            and representative == record["discovered_expression_string"]
        )
        if not replay_ok:
            replay_mismatches.append(case_id)

        winner_replay = (
            replay_seed(representative, truth_support, truth_family)
            if representative
            else None
        )

        # Losing classes that nonetheless held a G2-correct candidate.
        correct_ordinals = {
            ordinal for ordinal, r in enumerate(replays) if r["g2_event"] == "SUCCESS"
        }
        winning_ordinals = (
            {m.k for m in cross.winning.members} if cross.winning else set()
        )
        correct_outside_winner = sorted(correct_ordinals - winning_ordinals)

        class_sizes = sorted((c.size for c in cross.classes), reverse=True)
        best_correct_class_size = 0
        for klass in cross.classes:
            if {m.k for m in klass.members} & correct_ordinals:
                best_correct_class_size = max(best_correct_class_size, klass.size)

        event_counter = Counter(r["g2_event"] for r in replays)
        support_counter = Counter(r["support_status"] for r in replays)
        family_counter = Counter(r["family_status"] for r in replays)

        row = {
            "case_id": case_id,
            "family_id": record["family_id"],
            "variant": manifest[case_id]["variant"],
            "truth_family": truth_family,
            "truth_support": sorted(truth_support),
            "representability": rep,
            "a1_status": record["a1_case_adequacy_status"],
            "acceptance_status": record["acceptance_status"],
            "acceptance_gate_reached": record["acceptance_gate_reached"],
            "sealed_support_status": record["support_status"],
            "sealed_family_status": record["family_status"],
            "g2_event_sealed": record["g2_event"],
            "sealed_discovered_expression": record["discovered_expression_string"],
            "sealed_discovered_family": record["discovered_family"],
            "sealed_selection_count": record["selection_count"],
            "selection_count_replayed": replayed_count,
            "cross_seed_replay_reproduces_seal": replay_ok,
            "seed_status_counts": dict(Counter(r["status"] for r in seed_rows)),
            "seeds_parsed": sum(1 for r in replays if r["parsed"]),
            "seeds_with_support_match": support_counter.get("MATCH", 0),
            "seeds_with_family_match": family_counter.get("MATCH", 0),
            "seeds_with_g2_success": event_counter.get("SUCCESS", 0),
            "seeds_unevaluable": event_counter.get("UNEVALUABLE", 0),
            "seed_support_status_counts": dict(support_counter),
            "seed_family_status_counts": dict(family_counter),
            "seed_discovered_family_counts": dict(
                Counter(str(r["discovered_family"]) for r in replays)
            ),
            "seeds_containing_exp": sum(
                1 for r in replays if r["contains_exp_after_simplify"]
            ),
            "identity_class_count": len(cross.classes),
            "identity_class_sizes": class_sizes,
            "largest_class_size": class_sizes[0] if class_sizes else 0,
            "voting_seeds": cross.voting_seeds,
            "winning_class_g2_event": winner_replay["g2_event"] if winner_replay else "UNEVALUABLE",
            "winning_class_support_status": winner_replay["support_status"] if winner_replay else "SUPPORT_UNRESOLVED",
            "winning_class_family_status": winner_replay["family_status"] if winner_replay else "FAMILY_UNRESOLVED",
            "correct_candidates_in_losing_classes": len(correct_outside_winner),
            "largest_class_containing_correct_candidate": best_correct_class_size,
            "winning_class_distinct_expression_strings": record[
                "winning_class_distinct_expression_strings"
            ],
            "winning_class_distinct_coefficient_vectors": record[
                "winning_class_distinct_coefficient_vectors"
            ],
            "per_seed": replays,
        }
        row["first_failure_point"], row["first_failure_detail"] = _first_failure_point(row)
        rows.append(row)

        if index % 12 == 0 or index == len(case_ids):
            print(f"  g2 trace: {index}/{len(case_ids)}", flush=True)

    if replay_mismatches:
        raise SystemExit(
            f"cross-seed replay diverged from the seal on {len(replay_mismatches)} "
            f"cases: {replay_mismatches[:5]}"
        )

    sealed_events = Counter(r["g2_event_sealed"] for r in rows)
    failure_points = Counter(r["first_failure_point"] for r in rows)

    write_json(
        OUT_DIR / "g2_pipeline_trace.json",
        {
            "method": (
                "frozen g2_contract predicates replayed over the 30 sealed "
                "per-seed retained candidates; frozen rc5_selection."
                "group_and_select replayed for cross-seed voting"
            ),
            "searches_run": 0,
            "pysr_imported": "pysr" in sys.modules,
            "denominator": len(rows),
            "cross_seed_replay_reproduced_seal_for": sum(
                1 for r in rows if r["cross_seed_replay_reproduces_seal"]
            ),
            "sealed_g2_event_counts": dict(sealed_events),
            "first_failure_point_counts": dict(failure_points),
            "observability_bound": {
                "id": "WITHIN_SEED_PARETO_NOT_OBSERVABLE",
                "statement": (
                    "rc5_selection retains and persists only argmax(score) per "
                    "seed.  Per-seed Pareto fronts are not in the seal, so a "
                    "truth-equivalent expression that lost the within-seed score "
                    "argmax cannot be distinguished here from one that was never "
                    "generated.  Every GENERATION verdict below is therefore "
                    "'never reached cross-seed selection', not 'never existed "
                    "anywhere in the search'."
                ),
            },
            "grammar": {
                "binary_operators": list(BINARY_OPERATORS),
                "unary_operators": list(UNARY_OPERATORS),
                "exp_excluded": "exp" not in GRAMMAR_OPERATORS,
                "exclusion_authority": "DEVIATIONS_P3 D1, via discovery/grammar.py",
            },
            "per_case": rows,
        },
    )
    print(f"\n  sealed G2 events : {dict(sealed_events)}")
    print(f"  first failure pt : {dict(failure_points)}")
    print(f"  wrote {OUT_DIR / 'g2_pipeline_trace.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
