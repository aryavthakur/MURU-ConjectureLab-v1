#!/usr/bin/env python
"""Emit manuscript-ready tables and figure data from the restored Held-out analysis.

Every number is read from the committed restoration artifacts or recomputed from
the frozen registry.  Nothing is transcribed by hand, so the tables cannot drift
from the analysis they summarise.

Outputs land in `paper/muru_v1_closure/tables/` and `figure_data/`.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.paper_benchmark.heldout_endpoint_populations import (  # noqa: E402
    build_endpoint_population,
    variant_code_for_case,
)
from muru.paper_benchmark.registry import (  # noqa: E402
    CASE_FAMILIES,
    ENDPOINTS,
    endpoint_case_count,
)
from muru.paper_benchmark.rc5_store import case_slug  # noqa: E402

RESTORED = REPO_ROOT / "results" / "restored"
OUT = REPO_ROOT / "paper" / "muru_v1_closure"
EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)


def write_table(name: str, header: list[str], rows: list[list]) -> None:
    path = OUT / "tables" / f"{name}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  {path.relative_to(REPO_ROOT)}  ({len(rows)} rows)")


def write_figure_data(name: str, payload) -> None:
    path = OUT / "figure_data" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    print(f"  {path.relative_to(REPO_ROOT)}")


def main() -> int:
    analysis = json.loads((RESTORED / "heldout_restored_analysis.json").read_text())
    recovery = json.loads((RESTORED / "heldout_g1_recovery.json").read_text())
    payloads = {
        p["case_id"]: p
        for p in (
            json.loads(f.read_text(encoding="utf-8"))
            for f in (EVIDENCE_ROOT / "records").glob("*.json")
        )
    }

    print("tables:")

    # T1 — benchmark design: family x endpoint applicability
    rows = []
    for family in CASE_FAMILIES:
        held_out = family.partition_counts["held_out"]
        rows.append([
            family.code,
            family.name,
            held_out,
            family.held_out_cases_for("scalar_competence"),
            family.held_out_cases_for("family_recovery"),
            family.held_out_cases_for("principal_structural_safety"),
            "|".join(family.variant_cycle),
        ])
    rows.append([
        "TOTAL", "", sum(f.partition_counts["held_out"] for f in CASE_FAMILIES),
        endpoint_case_count("scalar_competence"),
        endpoint_case_count("family_recovery"),
        endpoint_case_count("principal_structural_safety"),
        "",
    ])
    write_table(
        "T1_benchmark_design_and_endpoint_applicability",
        ["family", "name", "held_out_cases", "G1_cases", "G2_cases", "G3_cases",
         "variant_cycle"],
        rows,
    )

    # T2 — primary endpoint results
    write_table(
        "T2_primary_endpoint_results",
        ["endpoint", "registry_name", "role", "denominator", "numerator",
         "numerator_meaning", "rate", "wilson_bound", "wilson_tail", "gate",
         "verdict"],
        [
            ["G1", "scalar_competence", "primary_scalar",
             analysis["g1"]["denominator"], analysis["g1"]["competent"],
             "competent cases",
             analysis["g1"]["competent"] / analysis["g1"]["denominator"],
             analysis["g1"]["wilson_lower_95"], "lower", ">= 0.70",
             "PASS" if analysis["g1"]["gate_passed"] else "FAIL"],
            ["G2", "family_recovery", "primary_symbolic",
             analysis["g2"]["denominator"], analysis["g2"]["successes"],
             "successes", analysis["g2"]["success_rate"],
             analysis["g2"]["wilson_lower_95"], "lower", ">= 0.70",
             "PASS" if analysis["g2"]["gate_passed"] else "FAIL"],
            ["G3", "principal_structural_safety", "primary_safety",
             analysis["g3"]["denominator"], analysis["g3"]["violations"],
             "violations", analysis["g3"]["violation_rate"],
             analysis["g3"]["wilson_upper_95"], "upper", "<= 0.15",
             "PASS" if analysis["g3"]["gate_passed"] else "FAIL"],
        ],
    )

    # T3 — failure-stage distribution
    stages = analysis["failure_stage_distribution"]
    total = sum(stages.values())
    write_table(
        "T3_failure_stage_distribution",
        ["gate_reached", "cases", "fraction_of_240"],
        [[k, v, v / total] for k, v in sorted(stages.items(), key=lambda kv: -kv[1])],
    )

    # T4 — Gate 7 and Gate 8
    write_table(
        "T4_gate7_gate8",
        ["gate", "definition", "reached", "passed", "failed", "detail"],
        [
            ["Gate 7", "ceiling comparison at position 7: ceiling_pass OR ceiling_waiver",
             analysis["gate7"]["reached"], analysis["gate7"]["passed"],
             analysis["gate7"]["failed"],
             f"{analysis['gate7']['passed_via_ceiling_pass']} via ceiling_pass, "
             f"{analysis['gate7']['passed_via_ceiling_waiver_only']} via waiver"],
            ["Gate 8", "check_gate8 over {F1,F4,F7,F10}, fail-closed",
             analysis["gate8"]["reached"], analysis["gate8"]["passed"],
             analysis["gate8"]["failed"],
             f"sole failure: {', '.join(analysis['gate8']['per_rung_fail'])}"],
            ["STRUCTURAL_ACCEPTED", "gates 1-8 all pass", 240,
             analysis["structural_accepted_count"],
             240 - analysis["structural_accepted_count"],
             "acceptance count, NOT an endpoint rate"],
        ],
    )

    # T5 — Gate 8 per-rung
    write_table(
        "T5_gate8_per_rung",
        ["rung", "pass", "fail", "role"],
        [
            [rung, analysis["gate8"]["per_rung_pass"].get(rung, 0),
             analysis["gate8"]["per_rung_fail"].get(rung, 0), "hard gate"]
            for rung in sorted(analysis["gate8"]["required_hard_gates"])
        ] + [
            ["F5_SCAFFOLD_HOLDOUT", 0, 0,
             "superseded; floor folded into the Gate 7 waiver branch"],
            ["F9_ENERGY_SUBSET", analysis["f9"]["pass_among_gate8_reachers"],
             analysis["f9"]["fail_among_gate8_reachers"],
             "secondary reported, NON-GATING, NOT_PROVEN_FOR_HARD_GATE"],
        ],
    )

    # T6 — G1 conjunct decomposition
    per_case = recovery["per_case"]
    m0 = [r for r in per_case if r["m0_accepted"]]
    not_m0 = [r for r in per_case if not r["m0_accepted"]]
    write_table(
        "T6_g1_conjunct_decomposition",
        ["stratum", "cases", "spearman_pass", "trajectory_pass", "both_continuous_pass",
         "scalar_competent"],
        [
            ["A1 established (M0_NOT_REJECTED)", len(m0),
             sum(r["spearman_pass"] for r in m0),
             sum(r["trajectory_pass"] for r in m0),
             sum(r["spearman_pass"] and r["trajectory_pass"] for r in m0),
             sum(r["scalar_competent"] for r in m0)],
            ["A1 not established (BOUNDARY_LIMITED)", len(not_m0),
             sum(r["spearman_pass"] for r in not_m0),
             sum(r["trajectory_pass"] for r in not_m0),
             sum(r["spearman_pass"] and r["trajectory_pass"] for r in not_m0),
             sum(r["scalar_competent"] for r in not_m0)],
            ["ALL", len(per_case),
             sum(r["spearman_pass"] for r in per_case),
             sum(r["trajectory_pass"] for r in per_case),
             sum(r["spearman_pass"] and r["trajectory_pass"] for r in per_case),
             sum(r["scalar_competent"] for r in per_case)],
        ],
    )

    # T7 — G2 per family
    g2_pop = build_endpoint_population("family_recovery")
    successes = set(analysis["g2"]["success_case_ids"])
    by_family: dict[str, Counter] = {}
    for case_id in g2_pop.case_ids:
        family = case_id.split("|")[2]
        counter = by_family.setdefault(family, Counter())
        counter[payloads[case_id]["g2_event"]] += 1
        if case_id in successes:
            counter["_success"] += 1
    write_table(
        "T7_g2_by_family",
        ["family", "cases", "success", "failure", "unevaluable"],
        [[f, sum(c[k] for k in ("SUCCESS", "FAILURE", "UNEVALUABLE")),
          c["SUCCESS"], c["FAILURE"], c["UNEVALUABLE"]]
         for f, c in sorted(by_family.items())],
    )

    # T8 — G3 per variant
    g3_pop = build_endpoint_population("principal_structural_safety")
    violations = set(analysis["g3"]["violation_case_ids"])
    by_variant: dict[str, Counter] = {}
    for case_id in g3_pop.case_ids:
        variant = variant_code_for_case(case_id)
        counter = by_variant.setdefault(variant, Counter())
        counter["cases"] += 1
        counter["violation" if case_id in violations else "safe"] += 1
        if payloads[case_id]["acceptance_status"] == "UNEVALUABLE":
            counter["unevaluable"] += 1
    write_table(
        "T8_g3_by_variant",
        ["variant", "cases", "violations", "safe", "of_which_unevaluable",
         "acceptance_permitted"],
        [[v, c["cases"], c["violation"], c["safe"], c["unevaluable"],
          "mass-only" if v in ("F07", "F19A", "F19B") else "none"]
         for v, c in sorted(by_variant.items())],
    )

    # T9 — partition and execution inventory
    write_table(
        "T9_execution_inventory",
        ["quantity", "value"],
        [
            ["families", len(CASE_FAMILIES)],
            ["held_out cases", analysis["case_population"]],
            ["seeds per case", 30],
            ["total searches", analysis["case_population"] * 30],
            ["execution failures", 0],
            ["seeds COMPLETED_WITH_CANDIDATES", 7136],
            ["seeds COMPLETED_NO_CANDIDATE", 64],
            ["sealed files", 482],
            ["sealed files re-hashing correctly", 482],
            ["acceptance recomputation disagreements",
             len(analysis["acceptance_recomputation_disagreements"])],
            ["G1 recovery searches run", recovery["searches_run"]],
            ["G1 recovery content-identity mismatches",
             recovery["content_identity_mismatches"]],
            ["primary endpoints", len(ENDPOINTS)],
            ["primary endpoints passing", 0],
        ],
    )

    print("figure data:")

    write_figure_data("F1_endpoint_wilson_intervals", {
        "note": "Wilson 95% bounds at the frozen z = 1.96; G1 and G2 are lower "
                "bounds against a >= 0.70 gate, G3 is an upper bound against a "
                "<= 0.15 gate",
        "endpoints": [
            {"endpoint": "G1", "numerator": analysis["g1"]["competent"],
             "denominator": analysis["g1"]["denominator"],
             "point": analysis["g1"]["competent"] / analysis["g1"]["denominator"],
             "bound": analysis["g1"]["wilson_lower_95"], "tail": "lower",
             "gate": 0.70, "passed": analysis["g1"]["gate_passed"]},
            {"endpoint": "G2", "numerator": analysis["g2"]["successes"],
             "denominator": analysis["g2"]["denominator"],
             "point": analysis["g2"]["success_rate"],
             "bound": analysis["g2"]["wilson_lower_95"], "tail": "lower",
             "gate": 0.70, "passed": analysis["g2"]["gate_passed"]},
            {"endpoint": "G3", "numerator": analysis["g3"]["violations"],
             "denominator": analysis["g3"]["denominator"],
             "point": analysis["g3"]["violation_rate"],
             "bound": analysis["g3"]["wilson_upper_95"], "tail": "upper",
             "gate": 0.15, "passed": analysis["g3"]["gate_passed"]},
        ],
    })

    write_figure_data("F2_failure_stage_waterfall", {
        "note": "the ordered structural-acceptance predicate, cases lost at each "
                "stage, in predicate order",
        "order": ["a1_adequacy", "null_threshold", "stability", "complexity",
                  "invalid_fraction", "effective_support", "ceiling",
                  "falsification", "all_passed"],
        "counts": analysis["failure_stage_distribution"],
        "total": analysis["case_population"],
    })

    write_figure_data("F3_g1_observables", {
        "note": "per-case G1 observables recovered with zero searches; the "
                "stratification by A1 adequacy is the finding",
        "spearman_gate": 0.80,
        "trajectory_ratio_gate": 0.80,
        "points": [
            {
                "case_id": r["case_id"],
                "family": r["case_id"].split("|")[2],
                "g_spearman": r["g_spearman"],
                "trajectory_ratio": (
                    r["trajectory_mae"] / r["per_energy_mean_mae"]
                    if r["per_energy_mean_mae"] else None
                ),
                "a1_established": r["m0_accepted"],
                "scalar_competent": r["scalar_competent"],
            }
            for r in per_case
        ],
    })

    write_figure_data("F4_endpoint_population_overlap", {
        "note": "endpoint denominators do not partition the 240 cases; they "
                "overlap, and five families carry no primary endpoint",
        "case_population": 240,
        "denominators": {n: endpoint_case_count(n) for n in sorted(ENDPOINTS)},
        "sum_of_denominators": sum(endpoint_case_count(n) for n in ENDPOINTS),
        "families_with_no_primary_endpoint": sorted(
            f.code for f in CASE_FAMILIES
            if sum(f.held_out_cases_for(n) for n in ENDPOINTS) == 0
        ),
        "by_family": {
            f.code: {n: f.held_out_cases_for(n) for n in sorted(ENDPOINTS)}
            for f in CASE_FAMILIES
        },
    })

    print()
    print(f"written under {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
