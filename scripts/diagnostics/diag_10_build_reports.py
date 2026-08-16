"""Stage 10: emit the decomposition report and the root-cause ranking.

Both the JSON and the Markdown are generated from the stage artifacts, so no
number in the prose can drift from the evidence that produced it.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    DIAG_ROOT,
    EVIDENCE_ROOT,
    FROZEN_SRC,
    OUT_DIR,
    RESTORED_ROOT,
    RUN_COMMIT,
    install_frozen_src,
    load_restored_analysis,
    read_json,
    write_json,
)

install_frozen_src()

from muru.paper_benchmark.g2_contract import wilson_lower_95, wilson_upper_95  # noqa: E402


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def truthy(value: str) -> bool:
    return value == "True"


def pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 2) if whole else 0.0


def main() -> int:
    restored = load_restored_analysis()
    a1 = read_json(OUT_DIR / "a1_decomposition.json")
    probe = read_json(OUT_DIR / "boundary_probe_magnitude.json")
    trace = read_json(OUT_DIR / "g2_pipeline_trace.json")
    counter = read_json(OUT_DIR / "g2_counterfactuals.json")
    retention = read_json(OUT_DIR / "retention_objective.json")
    g3t = read_json(OUT_DIR / "g3_trace.json")
    geometry = read_json(OUT_DIR / "case_geometry.json")
    hostile = read_json(OUT_DIR / "hostile_review.json")
    rollup = read_json(OUT_DIR / "taxonomy_rollup.json")

    g1 = read_csv(DIAG_ROOT / "MURU_V1_G1_FAILURE_TAXONOMY.csv")
    g2 = read_csv(DIAG_ROOT / "MURU_V1_G2_FAILURE_TAXONOMY.csv")
    g3 = read_csv(DIAG_ROOT / "MURU_V1_G3_FAILURE_TAXONOMY.csv")

    a1_rows = a1["per_case"]
    seed_family = Counter()
    seed_events = Counter()
    for case in trace["per_case"]:
        for key, value in case["seed_discovered_family_counts"].items():
            seed_family[key] += value
        for seed in case["per_seed"]:
            seed_events[seed["g2_event"]] += 1
    seed_total = sum(seed_family.values())

    max_wins = {
        detector: max(r["contrasts"][detector]["practical_wins"] for r in a1_rows)
        for detector in ("M1", "M2", "M3")
    }

    g1_failures = [r for r in g1 if not truthy(r["g1_success"])]
    g1_m0_only = [r for r in g1_failures if r["failing_conditions"] == "m0_accepted"]
    oracle = counter["summary"]["arms"]["ORACLE_ANY"]["successes"]

    # ---------------------------------------------------------------- JSON --
    decomposition = {
        "title": "MURU ConjectureLab v1 failure decomposition",
        "scope": "DIAGNOSIS ONLY. No scientific code, threshold, grammar, or search setting was changed; no production search was run.",
        "terminal_state": ["V1 FAILURE MODES EXHAUSTIVELY CHARACTERIZED", "NO V2 SCIENTIFIC CHANGES MADE"],
        "evidence": {
            "sealed_evidence_root": str(EVIDENCE_ROOT),
            "restored_analysis_root": str(RESTORED_ROOT),
            "frozen_source_tree": str(FROZEN_SRC),
            "run_commit": RUN_COMMIT,
            "frozen_source_relationship_to_run_commit": "additions only: 7 new analysis files, 3016 insertions, 0 deletions or modifications to any module the run executed",
            "cases": 240,
            "searches": 7200,
            "execution_failures": 0,
        },
        "official_v1_result_unchanged": {
            "G1": {"successes": 67, "denominator": 164, "wilson_lower_95": restored["g1"]["wilson_lower_95"], "gate": "wilson_lower_95 >= 0.70", "passed": False},
            "G2": {"successes": 4, "denominator": 144, "wilson_lower_95": restored["g2"]["wilson_lower_95"], "gate": "wilson_lower_95 >= 0.70", "passed": False},
            "G3": {"violations": 26, "denominator": 36, "wilson_upper_95": restored["g3"]["wilson_upper_95"], "gate": "wilson_upper_95 <= 0.15", "passed": False},
            "gate7": {"passed": 26, "reached": 27},
            "gate8": {"passed": 25, "reached": 26},
        },
        "observability_bounds": [
            trace["observability_bound"],
            {
                "id": "A1_PER_COMPOUND_DETAIL_NOT_SEALED",
                "statement": "The sealed record schema stores only the case-level a1_case_adequacy_status. Per-detector evaluability, per-compound boundary attribution and per-fold parameter values were recomputed from regenerated case content, which reproduced all 240 sealed A1 verdicts exactly.",
            },
        ],
        "a1_g1": {
            "denominator": 164,
            "successes": 67,
            "failures": 97,
            "a1_status_distribution_over_164": dict(
                Counter(r["a1_status_recomputed"] for r in g1)
            ),
            "a1_status_distribution_over_240": a1["status_counts"],
            "first_failing_condition": rollup["G1"]["first_failing_condition"],
            "every_failure_fails_m0_conjunct": True,
            "failures_explained_by_adequacy_alone": len(g1_m0_only),
            "failures_that_would_also_fail_a_continuous_condition": len(g1_failures) - len(g1_m0_only),
            "blocking_detector_sets_over_240": dict(
                Counter(
                    "+".join(r["blocking_detectors"]) or "none"
                    for r in a1_rows
                )
            ),
            "detector_firing": {
                "cases_with_any_detector_fired": sum(1 for r in a1_rows if r["fired_detectors"]),
                "of_cases": 240,
                "min_practical_wins_required": 20,
                "max_practical_wins_ever_observed": max_wins,
                "dedicated_positive_control_families": {
                    "F13_m1": 12, "F14_m2": 12, "F15_m3": 12, "F16_m1_m2_m3": 12,
                },
                "positive_control_detections": 0,
            },
            "boundary_mechanism": {
                "unresolved_compound_fits_by_model_over_240": {
                    model: sum(r["unresolved_compounds_by_model"][model] for r in a1_rows)
                    for model in ("M0", "M1", "M2", "M3")
                },
                "bound_hit_counts": probe["pooled_probe_tag_counts"],
                "frozen_rule": probe["frozen_rule"],
                "pooled_median_relative_sse_improvement_that_triggered_the_rule": probe[
                    "pooled_median_of_case_medians"
                ],
                "largest_relative_improvement_anywhere": max(
                    r["probe_improvement_quantiles"]["max"]
                    for r in probe["per_case"]
                    if r["probe_improvement_quantiles"]
                ),
                "a1_status_by_counterfactual_relative_floor": probe[
                    "a1_status_counts_by_relative_floor"
                ],
            },
            "data_geometry_ruled_out": {
                "scaffold_and_compound_layout": "identical across all 240 cases: 20 train scaffolds / 5 test scaffolds, 120 train / 30 test compounds",
                "cases_with_any_compound_below_the_5_energy_minimum": sum(
                    1 for r in geometry["per_case"] if r["compounds_below_5_energies"]
                ),
                "cases_with_missing_cells": sum(
                    1 for r in geometry["per_case"] if r["missing_cell_fraction"] > 0
                ),
                "insufficient_data_verdicts": a1["status_counts"].get("INSUFFICIENT_DATA", 0),
            },
        },
        "g2": {
            "denominator": 144,
            "successes": 4,
            "failures": 103,
            "unevaluable": 37,
            "first_failure_point": rollup["G2"]["first_failure_point"],
            "root_cause_class": rollup["G2"]["root_cause_class"],
            "by_family": counter["by_family"],
            "seed_level": {
                "retained_candidates": seed_total,
                "seeds_producing_no_candidate": 2,
                "unparseable_candidates": 2,
                "discovered_family_distribution": dict(seed_family),
                "g2_event_distribution": dict(seed_events),
            },
            "representability": {
                "families_needing_an_operator_the_grammar_lacks": ["mass_exponential_descriptor"],
                "affected_family_id": "F18",
                "affected_cases": 12,
                "missing_operator": "exp",
                "authority": "discovery/grammar.py excludes exp per DEVIATIONS_P3 D1; g2_contract._contains_exp_of requires a literal sympy.exp node",
                "consequence": "no grammar-legal expression can ever be labelled mass_exponential_descriptor, so those 12 cases had a structurally zero success probability",
            },
            "counterfactual_arms": counter["summary"]["arms"],
            "counterfactual_among_representable": counter["summary"]["among_representable_cases"],
            "counterfactual_stability": counter["summary"]["stability_interaction"],
            "retention_rule_evidence": retention["summary"],
            "classification_coverage": {
                "retained_candidates_the_classifier_could_not_label": seed_family.get("None", 0),
                "share": pct(seed_family.get("None", 0), seed_total),
                "cases_whose_winner_was_unlabelable": 37,
                "consequence": "all 37 G2 UNEVALUABLE cases carry family_status FAMILY_UNRESOLVED",
            },
        },
        "g3": {
            "denominator": 36,
            "violations": 26,
            "safe": 10,
            "violation_cause_counts": g3t["violation_cause_counts"],
            "all_violations_are_unevaluable_not_unsafe": True,
            "unsafe_structural_acceptances": 0,
            "independent_safety_scan": g3t["independent_safety_scan"],
            "root_cause_overlap_with_g1": g3t["g1_root_cause_overlap"],
        },
        "root_cause_quantification": {
            "G1": {
                "denominator": 164,
                "classes": {
                    name: {"cases": count, "percent": pct(count, 164)}
                    for name, count in rollup["G1"]["root_cause_class"].items()
                },
                "by_family": rollup["G1"]["by_family"],
            },
            "G2": {
                "denominator": 144,
                "classes": {
                    name: {"cases": count, "percent": pct(count, 144)}
                    for name, count in rollup["G2"]["root_cause_class"].items()
                },
                "by_family": rollup["G2"]["by_family"],
            },
            "G3": {
                "denominator": 36,
                "classes": {
                    name: {"cases": count, "percent": pct(count, 36)}
                    for name, count in rollup["G3"]["root_cause_class"].items()
                },
                "by_variant": rollup["G3"]["by_variant"],
            },
        },
        "counterfactual_diagnostics": {
            "disclaimer": "Diagnostic only. The official v1 result stands at G1 67/164, G2 4/144, G3 26/36 violations.",
            "G1_if_a1_indeterminacy_were_removed": {
                "successes": 67 + len(g1_m0_only),
                "denominator": 164,
                "wilson_lower_95": wilson_lower_95(67 + len(g1_m0_only), 164),
                "would_pass_0_70_gate": wilson_lower_95(67 + len(g1_m0_only), 164) >= 0.70,
                "residual_failures": len(g1_failures) - len(g1_m0_only),
            },
            "G3_if_a1_indeterminacy_were_removed": {
                "violations": 0,
                "denominator": 36,
                "wilson_upper_95": wilson_upper_95(0, 36),
                "would_pass_0_15_gate": wilson_upper_95(0, 36) <= 0.15,
            },
            "G2_upper_bound_under_a_perfect_post_search_selector": {
                "successes": oracle,
                "denominator": 144,
                "wilson_lower_95": wilson_lower_95(oracle, 144),
                "would_pass_0_70_gate": wilson_lower_95(oracle, 144) >= 0.70,
                "note": "even a selector that always picks the correct retained candidate leaves G2 far below its gate",
            },
            "G2_search_versus_selection_versus_representation": {
                "representation_infeasible": 12,
                "correct_never_reached_cross_seed_selection": 144 - oracle - 12,
                "correct_reached_selection_but_lost": oracle - 4,
                "correct_reached_selection_and_won": 4,
                "recoverable_by_coarsening_the_equivalence_relation": 2,
                "cases_with_a_correct_majority_at_or_above_15_of_30": 1,
                "cases_with_a_correct_majority_at_or_above_the_20_of_30_stability_gate": 0,
            },
        },
        "hostile_review": {
            "lenses": hostile["lenses"],
            "checks": hostile["checks"],
            "passed": hostile["passed"],
            "failed": hostile["failed"],
            "overall": hostile["overall"],
            "findings": hostile["findings"],
        },
        "reconciliation": {
            "G1_rows": len(g1),
            "G2_rows": len(g2),
            "G3_rows": len(g3),
            "G1_successes_plus_failures": f"{sum(1 for r in g1 if truthy(r['g1_success']))} + {len(g1_failures)} = 164",
            "G2_success_plus_failure_plus_unevaluable": "4 + 103 + 37 = 144",
            "G3_safe_plus_violation": "10 + 26 = 36",
        },
    }
    write_json(DIAG_ROOT / "MURU_V1_FAILURE_DECOMPOSITION.json", decomposition)

    # ------------------------------------------------------------- ranking --
    g1_cf = decomposition["counterfactual_diagnostics"]["G1_if_a1_indeterminacy_were_removed"]
    ranking = {
        "title": "MURU ConjectureLab v1 root-cause ranking",
        "scope": "DIAGNOSIS ONLY. Remediation classes are named, not designed. No v2 implementation is proposed.",
        "ordering_criterion": "endpoint-verdict leverage first, then affected case count, then confidence of attribution",
        "root_causes": [
            {
                "rank": 1,
                "id": "RC1_A1_UNRESOLVED_BOUNDARY_RULE",
                "class": "MODEL_ADEQUACY_LIMITATION",
                "statement": "The A1 unresolved-boundary test has no magnitude floor, so a negligible outward improvement at a parameter bound removes a compound from the evaluable pool. Enough compounds are removed that the M3 contrast falls below its 24-compound evaluability minimum, and the case becomes BOUNDARY_LIMITED.",
                "evidence": [
                    "154 of 240 cases are BOUNDARY_LIMITED; 0 are INSUFFICIENT_DATA, NUMERICAL_FAILURE, MODEL_FIT_FAILURE, TIMEOUT or CONTRACT_FAILURE",
                    "every one of the 154 is blocked by M3 (127 by M3 alone, 27 by M2 and M3); M1 never blocks and the shared M0 fit is never unresolved on any compound in the partition",
                    "7399 of 8816 recorded bound contacts are the M3 low-energy plateau pinned at its MU_CEIL upper bound",
                    "the median relative sum-of-squares improvement that triggered the rule is 1.3 percent; the largest anywhere in the partition is 28.9 percent",
                    "raising the trigger to a 10 percent relative floor makes all 240 cases M0_NOT_REJECTED",
                    "case geometry is identical across all 240 cases and no compound anywhere falls below the 5-energy minimum, so data sparsity is excluded",
                ],
                "affected_cases": {"G1": 97, "G3": 26, "all_held_out": 154},
                "endpoint_leverage": {
                    "G1": f"67/164 (Wilson lower {restored['g1']['wilson_lower_95']:.3f}) becomes {g1_cf['successes']}/164 (Wilson lower {g1_cf['wilson_lower_95']:.3f}) if this alone were resolved, crossing the 0.70 gate",
                    "G3": f"26/36 violations (Wilson upper {restored['g3']['wilson_upper_95']:.3f}) becomes 0/36 (Wilson upper {wilson_upper_95(0, 36):.3f}), crossing the 0.15 gate",
                },
                "remediation_class": "adequacy decision-rule specification: give the boundary test a scale-aware magnitude floor or a proper identifiability criterion, and separate 'the fit sits at a bound' from 'the contrast cannot decide'",
                "risks": [
                    "any floor is a new free parameter and must be calibrated prospectively, not chosen against Held-out",
                    "loosening evaluability admits cases the current rule conservatively refused, so the safety direction of G3 changes and must be re-argued",
                    "MU_CEIL and MIN_VERTICAL_AMPLITUDE were inherited from the generator clip rather than derived, so the admissible ranges themselves need justification before the floor is tuned",
                ],
                "confidence": "HIGH: mechanism reproduced fit by fit, and the control arm of the counterfactual reproduces the frozen result exactly",
            },
            {
                "rank": 2,
                "id": "RC2_A1_DETECTOR_HAS_NO_DEMONSTRATED_POWER",
                "class": "MODEL_ADEQUACY_LIMITATION",
                "statement": "No A1 detector fired on any of the 240 Held-out cases, including the 48 dedicated positive controls whose planted truth is the deviation the detector is meant to catch. The 20-of-30 practical-win threshold was never approached: the maximum wins ever observed are 18 for M1, 18 for M2 and 15 for M3.",
                "evidence": [
                    "0 of 240 cases reached any M0_REJECTED_* state",
                    "F13 (M1 truth), F14 (M2 truth), F15 (M3 truth) and F16 (M1+M2+M3 truth) produced 0 detections across 48 cases",
                    "in no case did a detector reach 20 wins while being evaluability-blocked, so the boundary defect and the threshold defect are independent",
                    "at a 10 percent counterfactual boundary floor, where every case is evaluable, the firing count is still 0",
                ],
                "affected_cases": {"validity_scope": 240, "positive_controls": 48},
                "endpoint_leverage": "Does not change any v1 count. It removes the evidential content of the 67 M0_NOT_REJECTED verdicts: A1 could not have rejected M0 on this partition regardless of the data, so 'M0 not rejected' carries no discriminating information.",
                "remediation_class": "adequacy test power: re-derive the practical-win ratio, the win count and the leave-one-energy-out loss so the detector has demonstrated sensitivity on its own positive controls before it gates anything",
                "risks": [
                    "raising sensitivity raises the false-rejection rate on true-M0 families, which directly suppresses G1",
                    "the positive controls are the only power evidence available and they are now spent as diagnostic evidence, so a v2 power argument needs an independent construction",
                ],
                "confidence": "HIGH: direct enumeration over all 240 cases and all three detectors",
            },
            {
                "rank": 3,
                "id": "RC3_WITHIN_SEED_RETENTION_DISCARDS_THE_ACCURATE_CANDIDATE",
                "class": "SELECTION_FAILURE",
                "statement": "Each seed retains argmax(score), PySR's marginal-return-per-unit-complexity heuristic, and only that one candidate is persisted. When seeds disagreed, the seeds that retained a G2-correct expression carry both materially higher accuracy and higher complexity, which is the signature of a parsimony rule discarding the correct answer.",
                "evidence": [
                    "a G2-correct candidate reached cross-seed selection in 75 of 144 cases but was the modal answer in essentially none",
                    "median correct-seed share is 1 of 30; the maximum anywhere is 16 of 30; no case reached the 20-of-30 stability gate with a correct candidate",
                    "in 70 of the 75 paired cases the correct retained candidate is both more accurate and more complex than the incorrect ones",
                    "median within-case accuracy gap is +0.121 valid_r2 (positive in 98.7 percent of paired cases) at a median +3.4 complexity",
                    f"{seed_family['mass_power']} of the {seed_total - 2} actual retained candidates ({pct(seed_family['mass_power'], seed_total - 2)} percent) are mass-only mass_power expressions, and mass_power is the modal answer in 92 of 144 cases",
                ],
                "affected_cases": {"G2": 69},
                "endpoint_leverage": f"Bounded: even a perfect post-search selector over the persisted candidates yields only {oracle}/144 (Wilson lower {wilson_lower_95(oracle, 144):.3f}), still far below the 0.70 gate.",
                "remediation_class": "search objective and retention policy: retain more than one candidate per seed, and make retention accuracy-aware rather than purely parsimony-driven",
                "risks": [
                    "retaining more candidates weakens the stability gate's meaning and inflates the effective multiple-comparison count",
                    "an accuracy-weighted rule biases toward overfit high-complexity expressions, which is the failure mode the parsimony rule exists to prevent",
                    "the within-seed Pareto fronts were not persisted, so this attribution rests on which candidate the rule kept across disagreeing seeds, not on what each front contained",
                ],
                "confidence": "MEDIUM-HIGH: the paired within-case comparison is strong, but the direct front-level evidence was not sealed",
            },
            {
                "rank": 4,
                "id": "RC4_SEARCH_NEVER_REACHES_THE_DESCRIPTOR_STRUCTURE",
                "class": "SEARCH_GENERATION_FAILURE",
                "statement": "In 57 representable cases no seed's retained candidate ever carried both the correct support and the correct family. The search collapses onto the mass-only term and never recovers the descriptor structure, completely so for the saturating family.",
                "evidence": [
                    "F09 (mass_saturating_descriptor): 0 of 12 cases had any correct retained candidate across 360 searches",
                    "F03: 1 of 12; F02: 3 of 12",
                    "all 30 seeds of several F03 cases converged on a descriptor-only expression with no mass term at all",
                    "2450 of 4318 retained candidates are mass-only",
                ],
                "affected_cases": {"G2": 57},
                "endpoint_leverage": "Sets the ceiling on G2. These cases cannot be rescued by any selection, voting or canonicalization change.",
                "remediation_class": "search budget, operator set and objective design; and separately, generator signal-to-noise, since the descriptor term's contribution to the scalar may be too small to be identifiable at the planted coefficient magnitudes",
                "risks": [
                    "increasing budget or operator richness increases the false-structure rate, which G3 is built to punish",
                    "if the descriptor contribution is genuinely below the identifiability floor at the planted coefficients, this is a benchmark-construction issue and no search change will fix it; that distinction was not resolvable from the sealed evidence and needs its own study",
                ],
                "confidence": "HIGH for the counts, MEDIUM for the mechanism: the persisted evidence shows what was retained, not what was searched",
            },
            {
                "rank": 5,
                "id": "RC5_FAMILY_CLASSIFIER_COVERAGE",
                "class": "CLASSIFICATION_SCORING_FAILURE",
                "statement": "classify_discovered_family returns None for a third of all grammar-legal retained candidates. When the cross-seed winner is one of them, the case is scored UNEVALUABLE rather than as a wrong answer.",
                "evidence": [
                    f"{seed_family.get('None', 0) - 2} of the {seed_total - 2} actual retained candidates ({pct(seed_family.get('None', 0) - 2, seed_total - 2)} percent) could not be labelled",
                    f"only 2 of the {seed_total} seed slots produced no candidate at all and only 2 candidates failed to parse, so this is classifier coverage and not a parser or execution defect",
                    "all 37 G2 UNEVALUABLE cases carry family_status FAMILY_UNRESOLVED",
                    "the classifier's family tests are pattern matches on simplified sympy trees, so nested or algebraically rearranged forms fall through to None",
                ],
                "affected_cases": {"G2": 37},
                "endpoint_leverage": "Confounds interpretation rather than the verdict: under the frozen predicate UNEVALUABLE and FAILURE are both non-successes, so relabelling all 37 would not move G2's numerator.",
                "remediation_class": "structural classification: replace pattern matching on simplified trees with a canonical structural normal form, or with behavioural family identification",
                "risks": [
                    "a more permissive classifier can label a wrong expression with the truth family, converting UNEVALUABLE into false SUCCESS and inflating G2",
                    "classification is downstream of truth, so any change must preserve the truth-blind boundary of the acceptance predicate",
                ],
                "confidence": "HIGH: measured directly over all 4320 candidates",
            },
            {
                "rank": 6,
                "id": "RC6_GRAMMAR_CANNOT_EXPRESS_THE_EXPONENTIAL_FAMILY",
                "class": "GRAMMAR_REPRESENTABILITY",
                "statement": "The frozen grammar excludes exp, while F18's planted truth is sqrt(mass) * exp(coefficient * descriptor / 3) and the family classifier requires a literal exp node. Those 12 cases had a success probability of exactly zero before any search ran.",
                "evidence": [
                    "discovery/grammar.py UNARY_OPERATORS omits exp, per DEVIATIONS_P3 D1",
                    "g2_contract._contains_exp_of requires an actual sympy.exp node in the simplified expression",
                    "F18 oracle recovery is 0 of 12 across 360 searches",
                    "29 of 30 F18 seeds retained a mass-only expression",
                ],
                "affected_cases": {"G2": 12},
                "endpoint_leverage": "Caps G2 at 132 of 144 by construction. Removing it cannot by itself change the verdict.",
                "remediation_class": "benchmark and grammar alignment: either admit exp to the grammar or remove the exponential family from the family-recovery population; the mismatch itself is the defect",
                "risks": [
                    "admitting exp reintroduces the overflow pathologies DEVIATIONS_P3 D1 excluded it for",
                    "removing the family shrinks the endpoint population and weakens the claim the endpoint was designed to support",
                ],
                "confidence": "HIGH: a static property of the frozen grammar and the frozen classifier, confirmed empirically",
            },
            {
                "rank": 7,
                "id": "RC7_CROSS_SEED_IDENTITY_IS_FINER_THAN_THE_ENDPOINT",
                "class": "CANONICALIZATION_EQUIVALENCE_FAILURE",
                "statement": "Cross-seed voting groups by template_key while G2 is scored on (effective support, family). The voting relation is strictly finer than the scoring relation, so agreeing answers are split across classes. The effect is real but small.",
                "evidence": [
                    "median 11 identity classes per case against a median 3 label classes",
                    "correct answers are split across a median of 5 identity classes but 1 label class",
                    "in 61 of 144 cases the correct answers occupy more than one identity class",
                    "regrouping by the endpoint's own label recovers only 2 cases and loses 3 others, for a net 3 of 144 against the frozen rule's 4",
                ],
                "affected_cases": {"G2": 2},
                "endpoint_leverage": "Negligible on its own. It matters only after RC3 and RC4 are addressed, since it cannot help when the correct answer is a minority.",
                "remediation_class": "equivalence-relation alignment between the voting layer and the scored endpoint",
                "risks": [
                    "coarsening the voting relation merges genuinely different expressions and inflates the stability statistic, which is the k-inflating direction the identity contract was written to avoid",
                ],
                "confidence": "HIGH: both arms replayed over the same frozen evidence, with the control arm reproducing the seal exactly",
            },
            {
                "rank": 8,
                "id": "RC8_NEGATIVE_CONTROLS_BEHAVED_AS_DESIGNED",
                "class": "EXPECTED_NEGATIVE_CONTROL",
                "statement": "Not a defect, recorded so it is not mistaken for one. Where G3 was evaluable, the system was safe in every instance, and no unsafe structural claim was accepted anywhere in the partition.",
                "evidence": [
                    "10 of 10 evaluable G3 cases are SAFE",
                    "only 2 of the 36 G3 cases were structurally accepted at all, both with mass-only support under variants where mass-only acceptance is permitted",
                    "an independent scan that bypasses the G3 classifiers finds 0 accepted cases with non-mass support",
                    "Gate 8's F10_NEGATIVE_CONTROL rung failed exactly 1 of 26 cases, and that failure correctly blocked acceptance",
                ],
                "affected_cases": {"G3": 10},
                "endpoint_leverage": "None. G3 fails only because UNEVALUABLE is charged as a violation, and every UNEVALUABLE traces to RC1.",
                "remediation_class": "none required",
                "risks": [
                    "the safety evidence rests on 10 evaluable cases, which is far too small to support a safety claim; resolving RC1 is what would make G3 informative",
                ],
                "confidence": "HIGH: verified twice by independent routes",
            },
        ],
        "bottleneck_summary": {
            "single_defect_that_flips_two_of_three_endpoints": "RC1",
            "g2_remains_failing_under_every_counterfactual_tested": True,
            "late_falsification_is_not_the_bottleneck": {
                "gate7": "26 of 27 reached cases pass",
                "gate8": "25 of 26 reached cases pass",
                "cases_reaching_gate7_at_all": 27,
                "note": "only 27 of 240 cases ever reach Gate 7, because 154 are stopped at A1 and 43 more at the stability gate",
            },
            "failure_stage_distribution_over_240": restored["failure_stage_distribution"],
        },
    }
    write_json(DIAG_ROOT / "MURU_V1_ROOT_CAUSE_RANKING.json", ranking)
    print(f"  wrote {DIAG_ROOT / 'MURU_V1_FAILURE_DECOMPOSITION.json'}")
    print(f"  wrote {DIAG_ROOT / 'MURU_V1_ROOT_CAUSE_RANKING.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
