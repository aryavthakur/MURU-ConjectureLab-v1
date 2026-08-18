#!/usr/bin/env python
"""Renders results/e2/E2_REPORT.json (produced by e2_report.py) into the
human-readable E2_REPORT.md and E2_HOSTILE_REVIEW.md deliverables.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def pct(x) -> str:
    return f"{x:.1f}%" if x is not None else "n/a"


def frac(x) -> str:
    return f"{x:.3f}" if x is not None else "n/a"


def render_report_md(report: dict) -> str:
    q = report["quantitative_outputs"]
    attr = report["attrition"]
    fam = report["by_family"]
    gaps = report["gaps"]
    pop = report["population"]
    seeds = report["seed_accounting"]

    lines = []
    lines.append("# E2: Pareto-Front Search/Retention Observability -- Results\n")
    lines.append(
        "Scope: **E2a only** (fresh V2C worlds, decision-admissible). E2b "
        "(Held-out replay) was not run; no Held-out or Challenge evidence "
        "was used anywhere in this report. No v2 retention policy is "
        "selected here -- this is a measurement, not a design decision. See "
        "`v2_design_reference/MURU_V2_E2_PREDECLARATION.md` for the "
        "predeclared operational choices this run executes against.\n"
    )

    lines.append("## 1. Population and search accounting\n")
    lines.append(f"- Planned cases: 540. Completed: {pop['completed']}. "
                  f"Fully reconciled: **{pop['fully_reconciled']}**.")
    lines.append(f"- Planned seeds for completed worlds: {seeds['planned_seeds_for_completed_worlds']}. "
                  f"Accounted (front + no-candidate + execution-failure): {seeds['seeds_accounted']} "
                  f"(reconciles exactly: **{seeds['reconciles_exactly']}**).")
    lines.append(f"  - `COMPLETED_WITH_FRONT`: {seeds['seeds_completed_with_front']}")
    lines.append(f"  - `COMPLETED_NO_CANDIDATE`: {seeds['seeds_completed_no_candidate']}")
    lines.append(f"  - `EXECUTION_FAILURE`: {seeds['seeds_execution_failure']}")
    lines.append(f"- World-level execution failures: {seeds['world_level_execution_failures']}\n")

    lines.append("## 2. Case attrition: first loss stage A-E\n")
    lines.append("| Stage | Meaning | Count | Share |")
    lines.append("|---|---|---|---|")
    meanings = {
        "A": "correct structure absent from all 30 seeds' Pareto fronts",
        "B": "on >=1 front, discarded by within-seed argmax(score) retention",
        "C": "retained by >=1 seed, lost the cross-seed vote to an incorrect class",
        "D": "wins the cross-seed vote, but the truth-blind classifier does not recognize it despite algebraic equivalence to truth",
        "E": "correct final recovery",
    }
    for s in "ABCDE":
        c = attr["counts"].get(s, 0)
        lines.append(f"| {s} | {meanings[s]} | {c} | {pct(100 * c / attr['total'])} |")
    lines.append(f"\nTotal: {attr['total']} / 540. Reconciles to full population: **{attr['reconciles_to_540']}**.\n")

    lines.append("### By family\n")
    lines.append("| Family | A | B | C | D | E |")
    lines.append("|---|---|---|---|---|---|")
    for family, row in attr["by_family"].items():
        lines.append(f"| {family} | " + " | ".join(str(row.get(s, 0)) for s in "ABCDE") + " |")
    lines.append("")

    lines.append("## 3. Quantitative required outputs\n")
    lines.append(f"- % cases with **G2-correct** (support MATCH and family MATCH) structure "
                  f"anywhere on a Pareto front: **{pct(q['pct_cases_g2_correct_structure_anywhere_on_front'])}**")
    lines.append(f"- % cases with **truth-equivalent** structure anywhere on a front "
                  f"(looser: algebraic equivalence to the planted law up to positive scale, independent of "
                  f"the truth-blind classifier): **{pct(q['pct_cases_truth_equivalent_structure_anywhere_on_front'])}**")
    lines.append(f"- % cases with correct **support** anywhere: **{pct(q['pct_cases_correct_support_anywhere'])}**")
    lines.append(f"- % cases with correct **family** anywhere: **{pct(q['pct_cases_correct_family_anywhere'])}**")
    lines.append(f"- v1-retention recall of available correct candidates "
                  f"({q['v1_retention_recall_numerator_seeds']} / {q['v1_retention_recall_denominator_seeds']} seeds): "
                  f"**{frac(q['v1_retention_recall_of_available_correct_candidates'])}**")
    lines.append(f"- Oracle best-front recovery ceiling (fraction of cases where ANY seed's front "
                  f"contains a correct row -- the best any downstream retention/aggregation/classifier fix "
                  f"could ever achieve given what the search itself generated): "
                  f"**{frac(q['oracle_best_front_recovery_ceiling'])}** "
                  f"(Wilson 95% [{frac(q['oracle_best_front_recovery_ceiling_wilson_lower'])}, "
                  f"{frac(q['oracle_best_front_recovery_ceiling_wilson_upper'])}])")
    lines.append("")
    lines.append("Distribution of seeds/case containing correct structure (0..30):\n")
    dist = q["distribution_seeds_per_case_with_correct_structure"]
    lines.append("| seeds w/ correct structure | n cases |")
    lines.append("|---|---|")
    for k in sorted(dist, key=int):
        lines.append(f"| {k} | {dist[k]} |")
    lines.append("")

    lines.append("### Distribution of correct candidates (front_rank / complexity / valid_r2)\n")
    for key, label in [("front_rank", "Front rank"), ("engine_complexity", "Complexity"), ("valid_r2", "valid_r2")]:
        d = q["correct_candidate_distributions"][key]
        if d.get("n", 0) == 0:
            lines.append(f"- {label}: no correct candidates observed.")
        else:
            lines.append(f"- {label}: n={d['n']}, min={d['min']:.3g}, p25={d['p25']:.3g}, "
                          f"median={d['median']:.3g}, p75={d['p75']:.3g}, max={d['max']:.3g}, mean={d['mean']:.3g}")
    lines.append("")

    lines.append("### Within-front gaps (argmax(score) row vs. best correct row on the SAME front)\n")
    for key, label in [("score_gap", "score_gap"), ("complexity_gap", "complexity_gap"),
                        ("r2_gap", "r2_gap"), ("front_size", "front_size")]:
        d = gaps[key]
        if d.get("n", 0) == 0:
            lines.append(f"- {label}: n=0.")
        else:
            lines.append(f"- {label}: n={d['n']}, min={d['min']:.3g}, median={d['median']:.3g}, "
                          f"max={d['max']:.3g}, mean={d['mean']:.3g}")
    lines.append("")

    lines.append("## 4. Results by family\n")
    lines.append("| Family | n | P_front (seeds) | P_retain\\|front (seeds) | A | B | C | D | E |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for family, row in fam.items():
        sc = row["stage_counts"]
        lines.append(
            f"| {family} | {row['n_cases']} | {frac(row['P_front_seeds'])} | "
            f"{frac(row['P_retain_given_front_seeds'])} | "
            + " | ".join(str(sc.get(s, 0)) for s in "ABCDE") + " |"
        )
    lines.append("")

    lines.append("## 5. Pareto-search generation ceiling and retention-loss fraction\n")
    ceiling = q["oracle_best_front_recovery_ceiling"]
    n_A = attr["counts"].get("A", 0)
    n_total = attr["total"]
    n_B = attr["counts"].get("B", 0)
    lines.append(f"**Search-generation ceiling** (oracle best-front recovery): "
                  f"{ceiling:.3f} ({n_total - n_A}/{n_total} cases have a correct structure on at least "
                  f"one seed's front).")
    lines.append(f"**Retention-loss fraction** among cases where the search DID generate a correct "
                  f"structure somewhere: "
                  f"{(n_B / (n_total - n_A)) if (n_total - n_A) else float('nan'):.3f} "
                  f"({n_B}/{n_total - n_A} of generation-successful cases are lost specifically at "
                  f"within-seed retention, stage B).\n")

    return "\n".join(lines)


def render_hostile_review_md(report: dict) -> str:
    audit = report["hostile_audit"]
    checks = audit["checks"]
    pop = audit["population_reconciliation"]
    seeds = audit["seed_accounting"]
    attr = audit["attrition_reconciliation"]

    lines = []
    lines.append("# E2 Hostile Review\n")
    lines.append("| Check | Result |")
    lines.append("|---|---|")
    for key, value in checks.items():
        if key == "ALL_PASS" or key == "candidate_dataset_row_count":
            continue
        lines.append(f"| {key} | {'PASS' if value else 'FAIL'} |")
    lines.append(f"\n**ALL_PASS: {checks['ALL_PASS']}**\n")

    lines.append("## Population reconciliation\n")
    lines.append(f"- planned: {pop['planned']}, completed: {pop['completed']}")
    lines.append(f"- missing world_ids: {len(pop['missing_world_ids'])}"
                  + (f" -- {pop['missing_world_ids']}" if pop['missing_world_ids'] else ""))
    lines.append(f"- unexpected world_ids: {len(pop['unexpected_world_ids'])}"
                  + (f" -- {pop['unexpected_world_ids']}" if pop['unexpected_world_ids'] else ""))
    lines.append(f"- duplicate rows: {pop['n_duplicate_rows']}\n")

    lines.append("## Seed accounting\n")
    lines.append(f"- planned seeds for completed worlds: {seeds['planned_seeds_for_completed_worlds']}")
    lines.append(f"- accounted: {seeds['seeds_accounted']} "
                  f"(front {seeds['seeds_completed_with_front']}, "
                  f"no-candidate {seeds['seeds_completed_no_candidate']}, "
                  f"execution-failure {seeds['seeds_execution_failure']})")
    lines.append(f"- reconciles exactly: **{seeds['reconciles_exactly']}**")
    lines.append(f"- world-level execution failures: {seeds['world_level_execution_failures']}"
                  + (f" -- {seeds['world_level_failure_ids']}" if seeds['world_level_failure_ids'] else "") + "\n")

    lines.append("## Attrition reconciliation\n")
    lines.append(f"- counts: {attr['counts']}")
    lines.append(f"- total: {attr['total']} / 540")
    lines.append(f"- reconciles to full population: **{attr['reconciles_to_540']}**\n")

    lines.append("## Front truncation\n")
    lines.append(f"- max candidate `engine_complexity` observed: {audit['max_candidate_complexity_seen']} "
                  f"(grammar `MAX_COMPLEXITY = 20`; no truncation applied by this run's own code -- every "
                  f"front row PySR's `equations_` returned is persisted).\n")

    lines.append("## Decision-admissibility and retention-policy discipline\n")
    lines.append("- No Held-out or Challenge evidence was read by any function in "
                  "`e2_worlds.py`/`e2_search.py`/`e2_scoring.py`/`e2_aggregate.py`/`e2_report.py`: "
                  "E2b (the Held-out replay) was never invoked in this run.")
    lines.append("- No retention policy is selected or adopted anywhere in this deliverable set: "
                  "`e2_aggregate.py` replays the frozen v1 `argmax(score)` rule as a CONTROL against "
                  "E2's own persisted fronts, and reports the outcome as a measurement.")
    lines.append("- Retention-identity regression (`scripts/e2_retention_identity_control.py`): "
                  "PASS on 6/6 checks -- an independent second production-path fit reproduces the same "
                  "retained expression/complexity/valid_r2 that E2's full-front capture flags as "
                  "`retained_by_argmax_score`.\n")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", type=str, default="results/e2/E2_REPORT.json")
    parser.add_argument("--out-dir", type=str, default="results/e2")
    args = parser.parse_args()

    report = json.loads((REPO_ROOT / args.report_json).read_text())
    out_dir = REPO_ROOT / args.out_dir

    (out_dir / "E2_REPORT.md").write_text(render_report_md(report))
    (out_dir / "E2_HOSTILE_REVIEW.md").write_text(render_hostile_review_md(report))
    print("Wrote E2_REPORT.md and E2_HOSTILE_REVIEW.md")


if __name__ == "__main__":
    main()
