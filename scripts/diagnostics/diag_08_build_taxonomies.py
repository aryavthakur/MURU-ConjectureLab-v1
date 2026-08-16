"""Stage 8: assemble the three per-case failure taxonomies.

One CSV per primary endpoint, one row per eligible case, no aggregation.  Every
column is either copied from sealed evidence or derived by an earlier stage that
reproduced the seal exactly.

Each taxonomy carries a ``first_failure_point`` (the earliest stage at which the
endpoint became unreachable) and a ``root_cause_class`` drawn from the fixed
vocabulary the decomposition report uses.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    DIAG_ROOT,
    OUT_DIR,
    eligible_case_ids,
    load_case_manifest,
    load_g1_recovery,
    load_sealed_records,
    read_json,
    write_json,
)

ROOT_CAUSE_CLASSES = (
    "MODEL_ADEQUACY_LIMITATION",
    "GRAMMAR_REPRESENTABILITY",
    "SEARCH_GENERATION_FAILURE",
    "SELECTION_FAILURE",
    "STABILITY_VOTING_FAILURE",
    "CANONICALIZATION_EQUIVALENCE_FAILURE",
    "CLASSIFICATION_SCORING_FAILURE",
    "EXPECTED_NEGATIVE_CONTROL",
    "NONE_SUCCESS",
)

#: G1's success predicate, in the order the restored analysis states it.
G1_SPEARMAN_GATE = 0.80
G1_TRAJECTORY_RATIO = 0.80


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise SystemExit(f"refusing to write an empty taxonomy: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    for row in rows:
        if list(row) != fields:
            raise SystemExit(f"inconsistent columns in {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# G1
# ---------------------------------------------------------------------------


def build_g1(manifest, sealed, a1, geometry) -> list[dict]:
    recovery = load_g1_recovery()
    rows = []
    for case_id in eligible_case_ids("G1", manifest):
        obs = recovery[case_id]
        detail = a1[case_id]
        geo = geometry[case_id]
        record = sealed[case_id]

        ratio = (
            obs["trajectory_mae"] / obs["per_energy_mean_mae"]
            if obs["per_energy_mean_mae"]
            else float("inf")
        )
        conjuncts = [
            ("g_spearman", obs["spearman_pass"]),
            ("trajectory_mae_ratio", obs["trajectory_pass"]),
            ("m0_accepted", obs["m0_accepted"]),
        ]
        failed = [name for name, ok in conjuncts if not ok]
        first_failure = failed[0] if failed else "NONE"

        if not failed:
            root_cause = "NONE_SUCCESS"
            mechanism = "all three G1 conjuncts satisfied"
        elif failed == ["m0_accepted"]:
            root_cause = "MODEL_ADEQUACY_LIMITATION"
            mechanism = (
                f"A1 returned {detail['recomputed_a1_status']}; blocked by "
                f"{'+'.join(detail['blocking_detectors'])} on evaluability, not by "
                f"any detector firing.  Both continuous competence conditions passed."
            )
        elif "m0_accepted" in failed:
            root_cause = "MODEL_ADEQUACY_LIMITATION"
            mechanism = (
                f"A1 returned {detail['recomputed_a1_status']} (blocked by "
                f"{'+'.join(detail['blocking_detectors'])}) and the case also failed "
                f"{', '.join(n for n in failed if n != 'm0_accepted')}"
            )
        else:
            root_cause = "CLASSIFICATION_SCORING_FAILURE"
            mechanism = f"continuous competence failure on {', '.join(failed)}"

        m1, m2, m3 = (detail["contrasts"][d] for d in ("M1", "M2", "M3"))
        rows.append(
            {
                "case_id": case_id,
                "family_id": detail["family_id"],
                "variant": manifest[case_id]["variant"],
                "truth_family": geo["truth_family"] or "",
                "g1_success": not failed,
                "first_failing_condition": first_failure,
                "failing_conditions": "|".join(failed),
                "root_cause_class": root_cause,
                "mechanism": mechanism,
                "g_spearman": obs["g_spearman"],
                "g_spearman_gate": G1_SPEARMAN_GATE,
                "spearman_pass": obs["spearman_pass"],
                "trajectory_mae": obs["trajectory_mae"],
                "per_energy_mean_mae": obs["per_energy_mean_mae"],
                "trajectory_mae_ratio": ratio,
                "trajectory_ratio_gate": G1_TRAJECTORY_RATIO,
                "trajectory_pass": obs["trajectory_pass"],
                "a1_status_sealed": record["a1_case_adequacy_status"],
                "a1_status_recomputed": detail["recomputed_a1_status"],
                "a1_status_reproduced": detail["a1_status_reproduced"],
                "m0_accepted": obs["m0_accepted"],
                "a1_fired_detectors": "|".join(detail["fired_detectors"]),
                "a1_blocking_detectors": "|".join(detail["blocking_detectors"]),
                "m1_evaluable": m1["evaluable"],
                "m1_practical_wins": m1["practical_wins"],
                "m1_fired": m1["fired"],
                "m2_evaluable": m2["evaluable"],
                "m2_practical_wins": m2["practical_wins"],
                "m2_fired": m2["fired"],
                "m3_evaluable": m3["evaluable"],
                "m3_practical_wins": m3["practical_wins"],
                "m3_fired": m3["fired"],
                "min_evaluable_required": 24,
                "min_practical_wins_required": 20,
                "boundary_limited_compounds_m1": m1["status_counts"].get("BOUNDARY_LIMITED", 0),
                "boundary_limited_compounds_m2": m2["status_counts"].get("BOUNDARY_LIMITED", 0),
                "boundary_limited_compounds_m3": m3["status_counts"].get("BOUNDARY_LIMITED", 0),
                "unresolved_compounds_m0_fit": detail["unresolved_compounds_by_model"]["M0"],
                "unresolved_compounds_m1_fit": detail["unresolved_compounds_by_model"]["M1"],
                "unresolved_compounds_m2_fit": detail["unresolved_compounds_by_model"]["M2"],
                "unresolved_compounds_m3_fit": detail["unresolved_compounds_by_model"]["M3"],
                "dominant_bound_hit": max(
                    detail["bound_hit_counts"], key=detail["bound_hit_counts"].get
                )
                if detail["bound_hit_counts"]
                else "",
                "shape_a_lo": detail["shape_a_lo"],
                "shape_a_hi": detail["shape_a_hi"],
                "shape_amplitude": detail["shape_amplitude"],
                "mu_max": geo["mu_max"],
                "scaffolds_train": geo["scaffolds_train"],
                "scaffolds_test": geo["scaffolds_test"],
                "compounds_train": geo["compounds_train"],
                "compounds_test": geo["compounds_test"],
                "observed_energies_min": geo["observed_energies_min"],
                "missing_cell_fraction": geo["missing_cell_fraction"],
                "mass_range_ratio": geo["mass_range_ratio"],
                "descriptor_sd": geo["descriptor_sd"],
                "acceptance_status": record["acceptance_status"],
                "acceptance_gate_reached": record["acceptance_gate_reached"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# G2
# ---------------------------------------------------------------------------

_G2_ROOT_CAUSE = {
    "NONE": "NONE_SUCCESS",
    "REPRESENTATION": "GRAMMAR_REPRESENTABILITY",
    "GENERATION": "SEARCH_GENERATION_FAILURE",
    "GENERATION_SUPPORT": "SEARCH_GENERATION_FAILURE",
    "GENERATION_FAMILY": "SEARCH_GENERATION_FAILURE",
    "SELECTION_VOTING": "SELECTION_FAILURE",
    "ACCEPTANCE": "CLASSIFICATION_SCORING_FAILURE",
}


def build_g2(manifest, sealed, trace, counterfactual, retention, geometry) -> list[dict]:
    rows = []
    for case in trace:
        case_id = case["case_id"]
        record = sealed[case_id]
        cf = counterfactual[case_id]
        ret = retention[case_id]
        geo = geometry[case_id]

        point = case["first_failure_point"]
        root_cause = _G2_ROOT_CAUSE[point]

        # Refine SELECTION_FAILURE: stage 4 proved no majority rule recovers
        # these, so attribute them to the layer that actually discarded the
        # correct candidate rather than to cross-seed voting.
        refined = point
        if point == "SELECTION_VOTING":
            if cf["label_winner_correct"]:
                refined = "SELECTION_CROSS_SEED_IDENTITY"
                root_cause = "CANONICALIZATION_EQUIVALENCE_FAILURE"
            elif case["seeds_with_g2_success"] >= 15:
                refined = "SELECTION_CROSS_SEED_TIEBREAK"
                root_cause = "STABILITY_VOTING_FAILURE"
            else:
                refined = "SELECTION_WITHIN_SEED_RETENTION"
                root_cause = "SELECTION_FAILURE"

        rows.append(
            {
                "case_id": case_id,
                "family_id": case["family_id"],
                "variant": case["variant"],
                "truth_family": case["truth_family"],
                "truth_support": "|".join(case["truth_support"]),
                "truth_relationship": case["representability"]["relationship"],
                "g2_event_sealed": case["g2_event_sealed"],
                "g2_success": case["g2_event_sealed"] == "SUCCESS",
                "first_failure_point": refined,
                "first_failure_stage_coarse": point,
                "root_cause_class": root_cause,
                "first_failure_detail": case["first_failure_detail"],
                "grammar_representable": case["representability"]["grammar_representable"],
                "classifier_label_reachable": case["representability"][
                    "classifier_label_reachable"
                ],
                "operators_missing_from_grammar": "|".join(
                    case["representability"]["operators_missing_from_grammar"]
                ),
                "seeds_completed": case["seed_status_counts"].get(
                    "COMPLETED_WITH_CANDIDATES", 0
                ),
                "seeds_parsed": case["seeds_parsed"],
                "seeds_with_support_match": case["seeds_with_support_match"],
                "seeds_with_family_match": case["seeds_with_family_match"],
                "seeds_with_g2_success": case["seeds_with_g2_success"],
                "seeds_unevaluable": case["seeds_unevaluable"],
                "truth_equivalent_ever_generated": case["seeds_with_g2_success"] > 0,
                "best_truth_equivalent_seed_share": case["seeds_with_g2_success"] / 30.0,
                "identity_class_count": case["identity_class_count"],
                "identity_classes_holding_correct": cf["identity_classes_holding_correct"],
                "largest_identity_class_size": case["largest_class_size"],
                "selection_count_sealed": case["sealed_selection_count"],
                "selection_count_replayed": case["selection_count_replayed"],
                "cross_seed_replay_reproduces_seal": case["cross_seed_replay_reproduces_seal"],
                "survived_cross_seed_selection": case["winning_class_g2_event"] == "SUCCESS",
                "label_rule_would_have_won": cf["label_winner_correct"],
                "label_class_count": cf["label_class_count"],
                "label_winner_size": cf["label_winner_size"],
                "oracle_any_seed_correct": cf["oracle_any_correct"],
                "winning_class_support_status": case["winning_class_support_status"],
                "winning_class_family_status": case["winning_class_family_status"],
                "sealed_support_status": case["sealed_support_status"],
                "sealed_family_status": case["sealed_family_status"],
                "sealed_discovered_family": case["sealed_discovered_family"] or "",
                "sealed_discovered_expression": case["sealed_discovered_expression"],
                "modal_discovered_family": max(
                    case["seed_discovered_family_counts"],
                    key=case["seed_discovered_family_counts"].get,
                ),
                "parser_lost_candidate": case["seeds_parsed"] < case[
                    "seed_status_counts"
                ].get("COMPLETED_WITH_CANDIDATES", 0),
                "mean_valid_r2_correct_seeds": ret["mean_valid_r2_correct"],
                "mean_valid_r2_incorrect_seeds": ret["mean_valid_r2_incorrect"],
                "mean_complexity_correct_seeds": ret["mean_complexity_correct"],
                "mean_complexity_incorrect_seeds": ret["mean_complexity_incorrect"],
                "delta_valid_r2_correct_minus_incorrect": ret["delta_valid_r2"],
                "delta_complexity_correct_minus_incorrect": ret["delta_complexity"],
                "coefficient_fit_indicator_winning_class_distinct_coef_vectors": case[
                    "winning_class_distinct_coefficient_vectors"
                ],
                "winning_class_distinct_expression_strings": case[
                    "winning_class_distinct_expression_strings"
                ],
                "a1_status": case["a1_status"],
                "acceptance_status": case["acceptance_status"],
                "acceptance_gate_reached": case["acceptance_gate_reached"],
                "valid_r2": record["valid_r2"],
                "complexity": record["complexity"],
                "descriptor_sd": geo["descriptor_sd"],
                "mass_range_ratio": geo["mass_range_ratio"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# G3
# ---------------------------------------------------------------------------


def build_g3(manifest, g3, geometry) -> list[dict]:
    rows = []
    for case in g3:
        geo = geometry[case["case_id"]]
        if case["violation_cause"] == "A1_INDETERMINATE":
            root_cause = "MODEL_ADEQUACY_LIMITATION"
        elif case["violation_cause"] == "UNSAFE_ACCEPTANCE":
            root_cause = "CLASSIFICATION_SCORING_FAILURE"
        elif case["violation_cause"] == "OTHER_UNEVALUABLE":
            root_cause = "CLASSIFICATION_SCORING_FAILURE"
        else:
            root_cause = "EXPECTED_NEGATIVE_CONTROL"
        rows.append(
            {
                "case_id": case["case_id"],
                "family_id": case["family_id"],
                "variant": case["variant"],
                "g3_event": case["g3_event"],
                "is_violation": case["is_violation"],
                "violation_cause": case["violation_cause"],
                "root_cause_class": root_cause,
                "mechanism": case["mechanism"],
                "unsafe_structural_acceptance": case["g3_event"] == "UNSAFE",
                "acceptance_status": case["acceptance_status"],
                "acceptance_gate_reached": case["acceptance_gate_reached"],
                "a1_status_sealed": case["a1_status_sealed"],
                "a1_status_recomputed": case["a1_status_recomputed"],
                "a1_blocking_detectors": "|".join(case["a1_blocking_detectors"]),
                "shares_g1_root_cause": case["violation_cause"] == "A1_INDETERMINATE",
                "effective_support": "|".join(case["effective_support"] or []),
                "discovered_expression": case["discovered_expression"],
                "selection_count": case["selection_count"],
                "valid_r2": case["valid_r2"],
                "complexity": case["complexity"],
                "mu_max": geo["mu_max"],
                "missing_cell_fraction": geo["missing_cell_fraction"],
            }
        )
    return rows


def main() -> int:
    manifest = load_case_manifest()
    sealed = load_sealed_records()
    a1 = {r["case_id"]: r for r in read_json(OUT_DIR / "a1_decomposition.json")["per_case"]}
    geometry = {r["case_id"]: r for r in read_json(OUT_DIR / "case_geometry.json")["per_case"]}
    trace = read_json(OUT_DIR / "g2_pipeline_trace.json")["per_case"]
    counterfactual = {
        r["case_id"]: r
        for r in read_json(OUT_DIR / "g2_counterfactuals.json")["per_case"]
    }
    retention = {
        r["case_id"]: r for r in read_json(OUT_DIR / "retention_objective.json")["per_case"]
    }
    g3 = read_json(OUT_DIR / "g3_trace.json")["per_case"]

    g1_rows = build_g1(manifest, sealed, a1, geometry)
    g2_rows = build_g2(manifest, sealed, trace, counterfactual, retention, geometry)
    g3_rows = build_g3(manifest, g3, geometry)

    for name, rows, expected in (
        ("G1", g1_rows, 164),
        ("G2", g2_rows, 144),
        ("G3", g3_rows, 36),
    ):
        if len(rows) != expected:
            raise SystemExit(f"{name} taxonomy has {len(rows)} rows, expected {expected}")
        if len({r["case_id"] for r in rows}) != expected:
            raise SystemExit(f"{name} taxonomy has duplicate case ids")

    _write_csv(DIAG_ROOT / "MURU_V1_G1_FAILURE_TAXONOMY.csv", g1_rows)
    _write_csv(DIAG_ROOT / "MURU_V1_G2_FAILURE_TAXONOMY.csv", g2_rows)
    _write_csv(DIAG_ROOT / "MURU_V1_G3_FAILURE_TAXONOMY.csv", g3_rows)

    write_json(
        OUT_DIR / "taxonomy_rollup.json",
        {
            "root_cause_vocabulary": list(ROOT_CAUSE_CLASSES),
            "G1": {
                "rows": len(g1_rows),
                "successes": sum(1 for r in g1_rows if r["g1_success"]),
                "first_failing_condition": dict(
                    Counter(r["first_failing_condition"] for r in g1_rows)
                ),
                "root_cause_class": dict(Counter(r["root_cause_class"] for r in g1_rows)),
                "by_family": {
                    family: dict(
                        Counter(
                            r["root_cause_class"] for r in g1_rows if r["family_id"] == family
                        )
                    )
                    for family in sorted({r["family_id"] for r in g1_rows})
                },
            },
            "G2": {
                "rows": len(g2_rows),
                "successes": sum(1 for r in g2_rows if r["g2_success"]),
                "first_failure_point": dict(
                    Counter(r["first_failure_point"] for r in g2_rows)
                ),
                "root_cause_class": dict(Counter(r["root_cause_class"] for r in g2_rows)),
                "by_family": {
                    family: dict(
                        Counter(
                            r["root_cause_class"] for r in g2_rows if r["family_id"] == family
                        )
                    )
                    for family in sorted({r["family_id"] for r in g2_rows})
                },
            },
            "G3": {
                "rows": len(g3_rows),
                "violations": sum(1 for r in g3_rows if r["is_violation"]),
                "violation_cause": dict(Counter(r["violation_cause"] for r in g3_rows)),
                "root_cause_class": dict(Counter(r["root_cause_class"] for r in g3_rows)),
                "by_variant": {
                    variant: dict(
                        Counter(r["g3_event"] for r in g3_rows if r["variant"] == variant)
                    )
                    for variant in sorted({r["variant"] for r in g3_rows})
                },
            },
        },
    )
    print(f"  G1 taxonomy: {len(g1_rows)} rows")
    print(f"  G2 taxonomy: {len(g2_rows)} rows")
    print(f"  G3 taxonomy: {len(g3_rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
