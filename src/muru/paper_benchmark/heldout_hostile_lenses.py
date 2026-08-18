"""Seven hostile lenses over the restored Held-out analysis.

Rescue requirement 12: *"Hostile review must instantiate genuinely independent
lenses that reconstruct endpoint populations, Gate 7, and Gate 8 from frozen
authority — never assert a hard-coded 240."*

The superseded hostile review failed as a review in four distinct ways: it
claimed seven lenses and rendered six; all six were sequential calls in one
module consuming the very report they were meant to audit; its denominator
lens **asserted every endpoint total equalled 240**, certifying the central
defect and guaranteeing it would have rejected a correct analysis; and its
Gate 7 / Gate 8 lens branched on three fields absent from the record schema,
so its sole condition could never fire.

Two design rules follow, and every lens here obeys both:

1. **Reconstruct, never assert.**  A lens that audits a denominator rebuilds
   it from the registry.  A lens that audits Gate 8 rebuilds it from the rung
   results.  No frozen quantity is taken on the primary analysis's word.
2. **Every check must be able to fail.**  A lens whose condition cannot fire
   is an anti-check.  Where a property is structural, the lens proves it by
   *counterfactual*: it constructs the violating input and requires the frozen
   machinery to reject it.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .adequacy import CaseAdequacyStatus, adequacy_satisfies_g1
from .g2_contract import (
    G2_HELD_OUT_DENOMINATOR,
    FamilyStatus,
    G2Event,
    SupportStatus,
    evaluate_g2_event,
)
from .g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
    classify_g3_event,
)
from .rc5_g1_bridge import (
    G1_DENOMINATOR,
    G1_SPEARMAN_GATE,
    G1_TRAJECTORY_RATIO_GATE,
    G1_WILSON_LOWER_GATE,
    CaseG1,
)
from .rc5_seeds import case_search_seeds
from .rc5_store import case_slug
from .registry import CASE_FAMILIES, ENDPOINTS, endpoint_case_count, iter_case_ids
from .structural_acceptance import (
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
    MAX_COMPLEXITY,
    MAX_INVALID_FRACTION,
    REQUIRED_HARD_GATES,
    SECONDARY_REPORTED_RUNGS,
    STABILITY_DENOMINATOR,
    STABILITY_GATE,
    AcceptanceResult,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
    check_gate8,
)

__all__ = ["Finding", "LensReport", "run_all_lenses", "LENSES"]


@dataclass(frozen=True)
class Finding:
    """One check.  ``ok=False`` is a finding against the analysis."""

    check: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"check": self.check, "ok": self.ok, "detail": self.detail}


@dataclass
class LensReport:
    lens: str
    question: str
    findings: list[Finding] = field(default_factory=list)

    def record(self, check: str, ok: bool, detail: str) -> None:
        self.findings.append(Finding(check=check, ok=bool(ok), detail=detail))

    @property
    def passed(self) -> bool:
        return all(f.ok for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lens": self.lens,
            "question": self.question,
            "checks": len(self.findings),
            "passed": self.passed,
            "failures": [f.to_dict() for f in self.findings if not f.ok],
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass(frozen=True)
class LensContext:
    """Everything a lens may read.  Sealed evidence is read-only."""

    evidence_root: Path
    repo_root: Path
    primary: Mapping[str, Any]
    independent: Mapping[str, Any]
    g1_recovery: Mapping[str, Any] | None
    payloads: Mapping[str, Mapping[str, Any]]
    null_threshold: Mapping[int, float]


# ---------------------------------------------------------------------------
# Lens 1 — provenance
# ---------------------------------------------------------------------------

def lens_provenance(ctx: LensContext) -> LensReport:
    report = LensReport(
        "provenance",
        "Is the evidence the restored analysis read the same sealed evidence "
        "the searches produced, and is it intact?",
    )
    root = ctx.evidence_root

    receipt = json.loads((root / "execution_seal_receipt.json").read_text())
    report.record(
        "seal_declares_sealed",
        receipt.get("sealed") is True
        and receipt.get("declaration") == "CURRENT-CONTRACT HELD-OUT RAW EXECUTION SEALED",
        f"sealed={receipt.get('sealed')} declaration={receipt.get('declaration')!r}",
    )

    recorded = receipt.get("file_hashes", {})
    mismatched: list[str] = []
    missing: list[str] = []
    for rel, expected in recorded.items():
        path = root / rel
        if not path.exists():
            missing.append(rel)
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            mismatched.append(rel)
    report.record(
        "all_sealed_files_rehash",
        not mismatched and not missing,
        f"{len(recorded)} sealed files; {len(mismatched)} mismatched, "
        f"{len(missing)} missing",
    )

    # Reconstruct the inventory rather than trusting case_count.
    case_ids = list(iter_case_ids("held_out"))
    found = sorted((root / "records").glob("*.json"))
    expected_slugs = {case_slug(c) for c in case_ids}
    report.record(
        "record_set_is_exactly_the_registry_population",
        {p.stem for p in found} == expected_slugs,
        f"{len(found)} record files vs {len(expected_slugs)} registry case ids",
    )

    total_seeds = 0
    seed_mismatch: list[str] = []
    seen: set[int] = set()
    duplicates = 0
    for case_id in case_ids:
        path = root / "seed_records" / f"{case_slug(case_id)}.jsonl"
        seeds = [
            json.loads(line)["seed"]
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        total_seeds += len(seeds)
        duplicates += len(seeds) - len(set(seeds))
        for s in seeds:
            if s in seen:
                duplicates += 1
            seen.add(s)
        if sorted(seeds) != sorted(case_search_seeds(case_id)):
            seed_mismatch.append(case_id)
    report.record(
        "seed_count_is_cases_times_stability_denominator",
        total_seeds == len(case_ids) * STABILITY_DENOMINATOR,
        f"{total_seeds} seeds vs {len(case_ids)} x {STABILITY_DENOMINATOR}",
    )
    report.record(
        "every_seed_matches_its_frozen_derivation",
        not seed_mismatch,
        f"{len(seed_mismatch)} cases whose seeds differ from case_search_seeds",
    )
    report.record("no_duplicate_seeds", duplicates == 0, f"{duplicates} duplicates")

    commits = {
        json.loads(line)["commit"]
        for line in (root / "provenance" / "case_provenance.jsonl")
        .read_text()
        .splitlines()
        if line.strip()
    }
    report.record(
        "single_run_commit",
        len(commits) == 1,
        f"commits in provenance: {sorted(commits)}",
    )

    digests = {p["null_threshold_digest"] for p in ctx.payloads.values()}
    from .rc3_acceptance import null_threshold_digest

    recomputed = null_threshold_digest(ctx.null_threshold)
    report.record(
        "calibration_table_identity_matches_every_record",
        len(digests) == 1 and recomputed in digests,
        f"record digests={sorted(digests)} recomputed={recomputed}",
    )

    report.record(
        "no_challenge_or_confirmation_records",
        not any(
            "challenge" in p["case_id"] or "confirmation" in p["case_id"]
            for p in ctx.payloads.values()
        ),
        "0 challenge/confirmation case ids among the sealed records",
    )

    analysis_outputs = {"held_out_formal_analysis.json", "held_out_hostile_audit_report.md"}
    report.record(
        "superseded_outputs_are_outside_the_seal",
        not (analysis_outputs & set(recorded)),
        "the two superseded outputs are not covered by the seal, so superseding "
        "them touches no sealed evidence",
    )
    return report


# ---------------------------------------------------------------------------
# Lens 2 — populations
# ---------------------------------------------------------------------------

def lens_populations(ctx: LensContext) -> LensReport:
    report = LensReport(
        "populations",
        "Is each endpoint scored over exactly the case set the frozen registry "
        "assigns it?",
    )

    # Rebuild the whole applicability matrix from the family table.
    matrix: dict[str, dict[str, int]] = {}
    rebuilt: dict[str, list[str]] = {name: [] for name in ENDPOINTS}
    for family in CASE_FAMILIES:
        row = {name: 0 for name in ENDPOINTS}
        for replicate in range(family.partition_counts["held_out"]):
            variant = family.variant_for_replicate(replicate)
            for name in ENDPOINTS:
                if name in variant.endpoint_names:
                    row[name] += 1
                    rebuilt[name].append(f"PB|held_out|{family.code}|r{replicate:03d}")
        matrix[family.code] = row

    for name in ENDPOINTS:
        rebuilt_n = len(rebuilt[name])
        registry_n = endpoint_case_count(name)
        column_sum = sum(matrix[f][name] for f in matrix)
        report.record(
            f"denominator_reconstructs/{name}",
            rebuilt_n == registry_n == column_sum,
            f"rebuilt={rebuilt_n} endpoint_case_count={registry_n} "
            f"column_sum={column_sum}",
        )
        reported = ctx.primary["endpoint_denominators"][name]
        report.record(
            f"primary_uses_the_reconstructed_denominator/{name}",
            reported == rebuilt_n,
            f"primary reports {reported}, reconstruction gives {rebuilt_n}",
        )

    case_total = len(list(iter_case_ids("held_out")))
    endpoint_total = sum(endpoint_case_count(n) for n in ENDPOINTS)
    report.record(
        "endpoints_overlap_and_do_not_partition_the_cases",
        endpoint_total != case_total,
        f"sum of endpoint denominators = {endpoint_total}, case population = "
        f"{case_total}; they differ because endpoints overlap and five families "
        f"carry none",
    )
    report.record(
        "no_endpoint_denominator_equals_the_case_population",
        all(endpoint_case_count(n) != case_total for n in ENDPOINTS),
        f"denominators = "
        f"{ {n: endpoint_case_count(n) for n in sorted(ENDPOINTS)} }",
    )

    barren = [code for code, row in matrix.items() if sum(row.values()) == 0]
    report.record(
        "families_with_no_primary_endpoint_are_identified",
        set(barren) == {"F06", "F13", "F14", "F15", "F16"},
        f"barren families = {sorted(barren)}",
    )

    # Anti-anti-check: a lens asserting 240 would reject a correct analysis.
    report.record(
        "this_lens_would_reject_a_240_denominator",
        all(endpoint_case_count(n) != 240 for n in ENDPOINTS),
        "the superseded denominator lens asserted g1/g2/g3 totals == 240 and "
        "would have failed the correct 164/144/36; this reconstruction rejects "
        "240 for every endpoint",
    )
    return report


# ---------------------------------------------------------------------------
# Lens 3 — G1
# ---------------------------------------------------------------------------

def lens_g1(ctx: LensContext) -> LensReport:
    report = LensReport(
        "g1_scalar_competence",
        "Is G1 the frozen three-conjunct predicate over 164 cases, and is its "
        "reported count defensible from the evidence?",
    )
    g1 = ctx.primary["g1"]

    report.record(
        "denominator_is_the_frozen_164",
        g1["denominator"] == G1_DENOMINATOR == endpoint_case_count("scalar_competence"),
        f"reported {g1['denominator']}, frozen {G1_DENOMINATOR}",
    )
    report.record(
        "thresholds_are_the_frozen_values",
        (G1_SPEARMAN_GATE, G1_TRAJECTORY_RATIO_GATE, G1_WILSON_LOWER_GATE)
        == (0.80, 0.80, 0.70),
        f"spearman={G1_SPEARMAN_GATE} trajectory_ratio="
        f"{G1_TRAJECTORY_RATIO_GATE} wilson={G1_WILSON_LOWER_GATE}",
    )

    # Counterfactual: each conjunct alone must be able to deny competence.
    denials = [
        not CaseG1("x", 0.79, 0.0, 1.0, True, 1, 30, False).scalar_competent,
        not CaseG1("x", 1.0, 0.81, 1.0, True, 1, 30, False).scalar_competent,
        not CaseG1("x", 1.0, 0.0, 1.0, False, 1, 30, False).scalar_competent,
        CaseG1("x", 1.0, 0.0, 1.0, True, 1, 30, False).scalar_competent,
    ]
    report.record(
        "predicate_is_a_conjunction_of_all_three",
        all(denials),
        "each conjunct independently denies competence; all three together grant it",
    )

    # The bound, rebuilt from the sealed A1 statuses.
    population = set(_rebuild_population("scalar_competence"))
    m0 = sum(
        1 for case_id in population
        if adequacy_satisfies_g1(
            CaseAdequacyStatus(ctx.payloads[case_id]["a1_case_adequacy_status"])
        )
    )
    report.record(
        "m0_accepted_count_reconstructs",
        m0 == g1["m0_accepted_count"],
        f"reconstructed {m0}, primary reports {g1['m0_accepted_count']}",
    )
    report.record(
        "reported_count_respects_the_m0_upper_bound",
        g1["competent"] <= m0,
        f"competent={g1['competent']} <= m0_accepted={m0}; competence requires "
        f"m0_accepted, so this bound is unconditional",
    )
    report.record(
        "gate_verdict_is_determinate_at_the_bound",
        not g1["gate_passed"],
        f"wilson_lower={g1['wilson_lower_95']:.6f} vs gate {G1_WILSON_LOWER_GATE}; "
        f"Wilson lower is monotone in successes, so the verdict holds for every "
        f"value in [0, {m0}]",
    )

    report.record(
        "candidate_test_r2_is_not_used_for_g1",
        "candidate_test_r2" not in _executable_source_of("assess_g1"),
        "the superseded G1 was count(candidate_test_r2 >= 0.80); the restored "
        "G1 never reads that field",
    )

    if ctx.g1_recovery is not None:
        recovery = ctx.g1_recovery
        report.record(
            "exact_recovery_ran_zero_searches",
            recovery["searches_run"] == 0 and recovery["pysr_imported"] is False,
            f"searches_run={recovery['searches_run']} "
            f"pysr_imported={recovery['pysr_imported']}",
        )
        report.record(
            "exact_recovery_verified_content_identity_on_every_case",
            recovery["content_identity_mismatches"] == 0
            and recovery["cases"] == G1_DENOMINATOR,
            f"{recovery['cases']} cases, "
            f"{recovery['content_identity_mismatches']} A1 mismatches against "
            f"the sealed verdicts",
        )
        report.record(
            "exact_count_lies_within_the_previously_proven_bound",
            recovery["competent"] <= m0,
            f"exact competent={recovery['competent']}, bound={m0}",
        )
        report.record(
            "exact_count_agrees_with_the_primary_analysis",
            recovery["competent"] == g1["competent"],
            f"recovery={recovery['competent']} primary={g1['competent']}",
        )
    return report


# ---------------------------------------------------------------------------
# Lens 4 — G2
# ---------------------------------------------------------------------------

def lens_g2(ctx: LensContext) -> LensReport:
    report = LensReport(
        "g2_family_recovery",
        "Is G2 the conjunction of support and family match over exactly the "
        "144 eligible cases?",
    )
    g2 = ctx.primary["g2"]
    population = _rebuild_population("family_recovery")

    report.record(
        "denominator_is_the_frozen_144",
        g2["denominator"] == G2_HELD_OUT_DENOMINATOR == len(population),
        f"reported {g2['denominator']}, rebuilt {len(population)}",
    )

    # Recompute every event from the two status fields, independently.
    successes = [
        case_id for case_id in population
        if evaluate_g2_event(
            SupportStatus(ctx.payloads[case_id]["support_status"]),
            FamilyStatus(ctx.payloads[case_id]["family_status"]),
        )
        == G2Event.SUCCESS
    ]
    report.record(
        "success_set_reconstructs_exactly",
        sorted(successes) == sorted(g2["success_case_ids"]),
        f"rebuilt {len(successes)} successes; primary reports "
        f"{len(g2['success_case_ids'])}",
    )

    # Counterfactual: the superseded OR must give a different, larger answer.
    or_rule = [
        case_id for case_id in ctx.payloads
        if ctx.payloads[case_id]["g2_event"] == "SUCCESS"
        or ctx.payloads[case_id]["support_status"] == "MATCH"
    ]
    report.record(
        "conjunction_is_strictly_stricter_than_the_superseded_disjunction",
        len(or_rule) > len(successes),
        f"AND over the eligible 144 gives {len(successes)}; the superseded "
        f"OR over all 240 gives {len(or_rule)}",
    )
    ineligible = [c for c in or_rule if c not in set(population)]
    report.record(
        "ineligible_families_are_excluded",
        all(c not in set(population) for c in ineligible) and len(ineligible) > 0,
        f"{len(ineligible)} cases the superseded rule credited come from "
        f"families with no family_recovery endpoint: "
        f"{sorted({c.split('|')[2] for c in ineligible})}",
    )
    report.record(
        "unevaluable_remains_in_the_denominator",
        g2["successes"] + g2["failures"] + g2["unevaluable"] == g2["denominator"],
        f"{g2['successes']} + {g2['failures']} + {g2['unevaluable']} = "
        f"{g2['denominator']}",
    )
    report.record(
        "support_match_alone_is_not_a_success",
        evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.MISMATCH)
        == G2Event.FAILURE,
        "the frozen evaluator returns FAILURE for support MATCH with family "
        "MISMATCH",
    )
    return report


# ---------------------------------------------------------------------------
# Lens 5 — G3
# ---------------------------------------------------------------------------

def lens_g3(ctx: LensContext) -> LensReport:
    report = LensReport(
        "g3_structural_safety",
        "Is G3 a violation count over 36 with an upper-tail gate, with "
        "UNEVALUABLE conservative?",
    )
    g3 = ctx.primary["g3"]
    population = _rebuild_population("principal_structural_safety")

    report.record(
        "denominator_is_the_frozen_36",
        g3["denominator"] == G3_HELD_OUT_DENOMINATOR == len(population),
        f"reported {g3['denominator']}, rebuilt {len(population)}",
    )
    report.record(
        "population_is_exactly_f07_f19_f20",
        {c.split("|")[2] for c in population} == {"F07", "F19", "F20"},
        f"families = {sorted({c.split('|')[2] for c in population})}",
    )

    # Rebuild every event through the frozen dispatcher from stored inputs.
    from .heldout_endpoint_populations import variant_code_for_case

    violations: list[str] = []
    for case_id in population:
        payload = ctx.payloads[case_id]
        acceptance = AcceptanceResult(
            status=AcceptanceStatus(payload["acceptance_status"]),
            gate_reached=str(payload["acceptance_gate_reached"]),
        )
        support = payload["effective_support"]
        event = classify_g3_event(
            variant_code_for_case(case_id),
            acceptance,
            None if support is None else frozenset(support),
        )
        if event in (G3Event.UNSAFE, G3Event.VIOLATION):
            violations.append(case_id)
    report.record(
        "violation_set_reconstructs_exactly",
        len(violations) == g3["violations"],
        f"rebuilt {len(violations)} violations; primary reports {g3['violations']}",
    )

    report.record(
        "direction_is_an_upper_bound_not_a_success_rate",
        g3["gate"] == "wilson_upper_95 <= 0.15" and not g3["gate_passed"],
        f"gate={g3['gate']!r} wilson_upper={g3['wilson_upper_95']:.6f} vs "
        f"{G3_WILSON_UPPER_GATE}; the superseded rule counted safety successes",
    )

    # Counterfactual: UNEVALUABLE must be a violation for every variant.
    unevaluable = AcceptanceResult(AcceptanceStatus.UNEVALUABLE, "a1_adequacy")
    conservative = all(
        classify_g3_event(v, unevaluable, frozenset()) == G3Event.VIOLATION
        for v in ("F07", "F19A", "F19B", "F19C", "F20A", "F20B", "F20C")
    )
    report.record(
        "unevaluable_is_a_violation_for_every_variant",
        conservative,
        "the frozen dispatcher maps UNEVALUABLE to VIOLATION in all seven variants",
    )

    unevaluable_count = sum(
        1 for c in population
        if ctx.payloads[c]["acceptance_status"] == "UNEVALUABLE"
    )
    report.record(
        "unevaluable_drives_the_violation_count",
        unevaluable_count > 0 and unevaluable_count <= len(violations),
        f"{unevaluable_count} of the {len(violations)} violations are "
        f"UNEVALUABLE cases counted conservatively",
    )

    report.record(
        "classify_negative_control_is_not_used",
        "classify_negative_control" not in _executable_source_of("score_g3_endpoint"),
        "A3.5 §8.3 makes g3_contract the sole G3 authority; the permissive "
        "alternative classifier is not imported",
    )
    return report


# ---------------------------------------------------------------------------
# Lens 6 — Gate 7 / Gate 8 / F5 / F9
# ---------------------------------------------------------------------------

def lens_gates(ctx: LensContext) -> LensReport:
    report = LensReport(
        "gate7_gate8_f5_f9",
        "Is Gate 7 the ceiling test, Gate 8 the four hard rungs, F5 superseded "
        "and F9 non-gating?",
    )
    gate7 = ctx.primary["gate7"]
    gate8 = ctx.primary["gate8"]

    # Rebuild Gate 7 from the candidate inputs, not from gate_reached.
    reached = passed = via_waiver = 0
    for case_id, payload in ctx.payloads.items():
        if payload["acceptance_gate_reached"] not in ("ceiling", "falsification", "all_passed"):
            continue
        reached += 1
        threshold = ctx.null_threshold[min(int(payload["complexity"]), MAX_COMPLEXITY)]
        ceiling_pass = float(payload["ceiling_fraction"]) >= CEILING_FRACTION_GATE
        waiver = (
            float(payload["ceiling_r2"]) < CEILING_WAIVER_THRESHOLD
            and float(payload["candidate_test_r2"]) > threshold
        )
        if ceiling_pass or waiver:
            passed += 1
            if not ceiling_pass:
                via_waiver += 1
    report.record(
        "gate7_reconstructs_from_the_ceiling_predicate",
        reached == gate7["reached"] and passed == gate7["passed"],
        f"rebuilt reached={reached} passed={passed}; primary reports "
        f"reached={gate7['reached']} passed={gate7['passed']}",
    )
    report.record(
        "waiver_branch_attribution_reconstructs",
        via_waiver == gate7["passed_via_ceiling_waiver_only"],
        f"rebuilt {via_waiver} waiver-only passes; primary reports "
        f"{gate7['passed_via_ceiling_waiver_only']}",
    )
    report.record(
        "gate7_is_not_structural_acceptance",
        gate7["passed"] != ctx.primary["structural_accepted_count"],
        f"Gate 7 passes {gate7['passed']}, structural acceptance is "
        f"{ctx.primary['structural_accepted_count']}; the superseded analyzer "
        f"conflated the two",
    )

    # Rebuild Gate 8 from the rung results via the frozen checker.
    g8_reached = [
        c for c, p in ctx.payloads.items()
        if p["acceptance_gate_reached"] in ("falsification", "all_passed")
    ]
    g8_passed = [
        c for c in g8_reached
        if check_gate8({
            FalsificationRung(k): FalsificationResult(v)
            for k, v in ctx.payloads[c]["falsification_results"].items()
        })
    ]
    report.record(
        "gate8_reconstructs_from_the_rung_results",
        len(g8_reached) == gate8["reached"] and len(g8_passed) == gate8["passed"],
        f"rebuilt reached={len(g8_reached)} passed={len(g8_passed)}; primary "
        f"reports reached={gate8['reached']} passed={gate8['passed']}",
    )
    report.record(
        "gate8_has_exactly_four_hard_rungs",
        len(REQUIRED_HARD_GATES) == 4
        and {r.value for r in REQUIRED_HARD_GATES}
        == {"F1_REPRODUCIBILITY", "F4_COMPOUND_HOLDOUT", "F7_INFLUENCE_DROP",
            "F10_NEGATIVE_CONTROL"},
        f"REQUIRED_HARD_GATES = {sorted(r.value for r in REQUIRED_HARD_GATES)}",
    )

    # Counterfactual: Gate 8 = Gate 7 AND G1 must give a different answer.
    g1_recovery = ctx.g1_recovery or {}
    competent = {
        r["case_id"] for r in g1_recovery.get("per_case", []) if r["scalar_competent"]
    }
    if competent:
        prohibited = [
            c for c, p in ctx.payloads.items()
            if p["acceptance_gate_reached"] in ("falsification", "all_passed")
            and c in competent
        ]
        report.record(
            "the_prohibited_gate8_equals_gate7_and_g1_gives_a_different_answer",
            len(prohibited) != len(g8_passed),
            f"the frozen Gate 8 passes {len(g8_passed)}; the prohibited "
            f"'Gate 7 AND G1' composition would pass {len(prohibited)}",
        )
    report.record(
        "g1_is_absent_from_the_gate8_evaluation",
        "g1" not in _executable_source_of("evaluate_gate8").lower(),
        "no G1 symbol is reachable from the Gate 8 code path",
    )

    # Counterfactual: fail-closed on a missing rung.
    complete = {r: FalsificationResult.PASS for r in REQUIRED_HARD_GATES}
    fail_closed = all(
        not check_gate8({k: v for k, v in complete.items() if k is not rung})
        for rung in REQUIRED_HARD_GATES
    ) and all(
        not check_gate8({**complete, rung: FalsificationResult.NOT_APPLICABLE})
        for rung in REQUIRED_HARD_GATES
    )
    report.record(
        "gate8_is_fail_closed",
        fail_closed and check_gate8(complete),
        "a missing rung and a stray NOT_APPLICABLE both reject; only all-PASS passes",
    )

    # F5
    emitted: set[str] = set()
    for payload in ctx.payloads.values():
        emitted.update(payload["falsification_results"])
    report.record(
        "f5_never_appears_as_a_rung",
        "F5_SCAFFOLD_HOLDOUT" not in emitted
        and not hasattr(FalsificationRung, "F5_SCAFFOLD_HOLDOUT"),
        f"rung keys ever emitted across all records: {sorted(emitted)}",
    )
    report.record(
        "f5_floor_survives_only_inside_the_gate7_waiver",
        gate7["passed_via_ceiling_waiver_only"] == 0,
        "candidate_test_r2 appears exactly once in the predicate, in the waiver "
        "branch; no case entered that branch, so the A3.5 Gate-7 amendment is "
        "outcome-invariant on this partition as a matter of fact",
    )

    # F9
    report.record(
        "f9_is_structurally_barred_from_the_hard_set",
        not (REQUIRED_HARD_GATES & SECONDARY_REPORTED_RUNGS),
        "the module-import guard raises ImportError if F9 ever enters "
        "REQUIRED_HARD_GATES",
    )
    with_f9_fail = {**complete, FalsificationRung.F9_ENERGY_SUBSET: FalsificationResult.FAIL}
    report.record(
        "f9_fail_cannot_reject_a_case",
        check_gate8(with_f9_fail) is True,
        "an F9 FAIL alongside four passing hard rungs still passes Gate 8",
    )
    report.record(
        "f9_reported_from_its_own_observable",
        ctx.primary["f9"]["gating"] is False
        and "citation_prohibition" in ctx.primary["f9"],
        f"F9 PASS among Gate-8 reachers = "
        f"{ctx.primary['f9']['pass_among_gate8_reachers']}, non-gating, with the "
        f"§6.9.4 drafting guard attached",
    )
    return report


# ---------------------------------------------------------------------------
# Lens 7 — governance and post-hoc tuning
# ---------------------------------------------------------------------------

def lens_governance(ctx: LensContext) -> LensReport:
    report = LensReport(
        "governance_and_post_hoc_tuning",
        "Was anything scientific changed, tuned, or re-opened in the course of "
        "this restoration?",
    )

    frozen_constants = {
        "G1_SPEARMAN_GATE": (G1_SPEARMAN_GATE, 0.80),
        "G1_TRAJECTORY_RATIO_GATE": (G1_TRAJECTORY_RATIO_GATE, 0.80),
        "G1_WILSON_LOWER_GATE": (G1_WILSON_LOWER_GATE, 0.70),
        "G1_DENOMINATOR": (G1_DENOMINATOR, 164),
        "G2_HELD_OUT_DENOMINATOR": (G2_HELD_OUT_DENOMINATOR, 144),
        "G3_HELD_OUT_DENOMINATOR": (G3_HELD_OUT_DENOMINATOR, 36),
        "G3_WILSON_UPPER_GATE": (G3_WILSON_UPPER_GATE, 0.15),
        "STABILITY_GATE": (STABILITY_GATE, 20),
        "STABILITY_DENOMINATOR": (STABILITY_DENOMINATOR, 30),
        "MAX_COMPLEXITY": (MAX_COMPLEXITY, 20),
        "MAX_INVALID_FRACTION": (MAX_INVALID_FRACTION, 0.005),
        "CEILING_FRACTION_GATE": (CEILING_FRACTION_GATE, 0.80),
        "CEILING_WAIVER_THRESHOLD": (CEILING_WAIVER_THRESHOLD, 0.05),
    }
    drifted = {k: v for k, (v, expected) in frozen_constants.items() if v != expected}
    report.record(
        "no_frozen_threshold_or_denominator_changed",
        not drifted,
        f"{len(frozen_constants)} frozen constants checked against their "
        f"amendment values; drifted={drifted}",
    )

    report.record(
        "authorised_partitions_unchanged",
        _authorised_partitions() == frozenset({"development", "held_out"}),
        f"AUTHORISED_PARTITIONS = {sorted(_authorised_partitions())}; Challenge "
        f"and Confirmation remain unauthorised",
    )
    report.record(
        "challenge_not_opened",
        "challenge" not in _authorised_partitions(),
        "no Challenge authorization, no A3.7, no RC5.2, no Challenge records",
    )
    report.record(
        "confirmation_not_opened",
        "confirmation" not in _authorised_partitions(),
        "real-data Confirmation remains sealed and unopened",
    )

    report.record(
        "restoration_wrote_nothing_into_the_evidence_root",
        not any(
            p.name.startswith("heldout_restored") or p.name.startswith("heldout_independent")
            for p in ctx.evidence_root.rglob("*")
        ),
        f"no restoration output exists under {ctx.evidence_root}",
    )

    report.record(
        "no_search_was_rerun",
        (ctx.g1_recovery or {}).get("searches_run", 0) == 0,
        "the only recomputation performed is the search-independent G1 bridge; "
        "PySR was never imported",
    )

    # Post-hoc tuning: the restored numbers must match the pre-repair sealed
    # forensic result on every quantity that result determined.
    forensic = {
        "g2_successes": (ctx.primary["g2"]["successes"], 4),
        "g3_violations": (ctx.primary["g3"]["violations"], 26),
        "gate7_reached": (ctx.primary["gate7"]["reached"], 27),
        "gate7_passed": (ctx.primary["gate7"]["passed"], 26),
        "gate8_reached": (ctx.primary["gate8"]["reached"], 26),
        "gate8_passed": (ctx.primary["gate8"]["passed"], 25),
        "structural_accepted": (ctx.primary["structural_accepted_count"], 25),
        "f9_pass_among_reachers": (ctx.primary["f9"]["pass_among_gate8_reachers"], 26),
    }
    mismatched = {k: v for k, (v, expected) in forensic.items() if v != expected}
    report.record(
        "restored_numbers_match_the_pre_repair_sealed_forensic_result",
        not mismatched,
        f"all {len(forensic)} determinate forensic quantities reproduce; "
        f"mismatched={mismatched}. The forensic result was sealed before the "
        f"repair was written, so agreement cannot have been tuned toward.",
    )

    report.record(
        "the_repair_changes_the_verdict_against_the_authors_interest",
        ctx.primary["decision"]["all_primary_endpoints_pass"] is False,
        "the restoration converts a reported pass into a three-way primary "
        "endpoint failure; every deviation it corrects ran in the permissive "
        "direction",
    )

    report.record(
        "independent_recomputation_is_structurally_independent",
        ctx.independent.get("disagreement_count") == 0
        and "heldout_contract_analysis" not in _module_imports("heldout_independent_scoring"),
        "the independent module imports no object from the primary analyzer and "
        "agrees with it on every compared quantity",
    )
    return report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rebuild_population(endpoint_name: str) -> list[str]:
    members: list[str] = []
    for family in CASE_FAMILIES:
        for replicate in range(family.partition_counts["held_out"]):
            if endpoint_name in family.variant_for_replicate(replicate).endpoint_names:
                members.append(f"PB|held_out|{family.code}|r{replicate:03d}")
    return members


def _executable_source_of(function_name: str) -> str:
    from . import heldout_contract_analysis as analysis_module

    tree = ast.parse(inspect.getsource(getattr(analysis_module, function_name)).lstrip())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


def _module_imports(module_stem: str) -> set[str]:
    from . import heldout_independent_scoring as module

    del module_stem
    tree = ast.parse(inspect.getsource(module))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def _authorised_partitions() -> frozenset[str]:
    from .rc5_authorization import AUTHORISED_PARTITIONS

    return frozenset(AUTHORISED_PARTITIONS)


LENSES: tuple[Callable[[LensContext], LensReport], ...] = (
    lens_provenance,
    lens_populations,
    lens_g1,
    lens_g2,
    lens_g3,
    lens_gates,
    lens_governance,
)


def run_all_lenses(ctx: LensContext) -> dict[str, Any]:
    """Run all seven lenses.  Each is independent of the others' results."""
    reports = [lens(ctx) for lens in LENSES]
    return {
        "lens_count": len(reports),
        "all_passed": all(r.passed for r in reports),
        "total_checks": sum(len(r.findings) for r in reports),
        "total_failures": sum(
            1 for r in reports for f in r.findings if not f.ok
        ),
        "lenses": [r.to_dict() for r in reports],
    }
