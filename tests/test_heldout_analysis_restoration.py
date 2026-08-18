"""Regression tests that reject every defect the superseded analysis carried.

Each test names the specific superseded behaviour it forbids.  A test that
would have *passed* against the superseded analyzer is not a regression test
for it, so several of these assert the negation directly: the superseded rule
is constructed and shown to produce a different, wrong answer.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

from muru.paper_benchmark import (
    heldout_contract_analysis as primary,
    heldout_endpoint_populations as populations,
    heldout_independent_scoring as independent,
    rc5_record_payload as payload_mod,
)
from muru.paper_benchmark.g2_contract import (
    FamilyStatus,
    G2Event,
    SupportStatus,
    evaluate_g2_event,
)
from muru.paper_benchmark.g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
)
from muru.paper_benchmark.rc3_scoring import score_g2, score_g3
from muru.paper_benchmark.rc5_g1_bridge import (
    G1_DENOMINATOR,
    G1_SPEARMAN_GATE,
    G1_TRAJECTORY_RATIO_GATE,
    CaseG1,
    score_g1,
)
from muru.paper_benchmark.registry import ENDPOINTS, endpoint_case_count
from muru.paper_benchmark.structural_acceptance import (
    REQUIRED_HARD_GATES,
    SECONDARY_REPORTED_RUNGS,
    FalsificationResult,
    FalsificationRung,
    check_gate8,
)

RESTORATION_MODULES = (
    primary,
    populations,
    independent,
    payload_mod,
)


def _executable_source(obj) -> str:
    """The source of ``obj`` with every docstring removed.

    These tests assert things about *code*, not about prose.  A docstring that
    names a forbidden object in order to explain why it is forbidden must not
    trip a check aimed at an actual reference to it.
    """
    tree = ast.parse(inspect.getsource(obj).lstrip())
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


# ---------------------------------------------------------------------------
# denominators
# ---------------------------------------------------------------------------

def test_endpoint_denominators_are_registry_derived():
    """Superseded defect: every endpoint scored over 240."""
    built = populations.build_all_primary_populations()
    assert built["scalar_competence"].denominator == 164
    assert built["family_recovery"].denominator == 144
    assert built["principal_structural_safety"].denominator == 36
    for name, population in built.items():
        assert population.denominator == endpoint_case_count(name)
        assert len(population.case_ids) == population.denominator


def test_case_population_is_not_an_endpoint_denominator():
    """240 is the case count.  No frozen endpoint has that denominator."""
    assert len(populations.held_out_case_ids()) == 240
    for name in ENDPOINTS:
        assert endpoint_case_count(name) != 240


def test_frozen_scorers_reject_a_240_length_sequence():
    """The guard that would have caught the superseded defect must still fire."""
    with pytest.raises(ValueError):
        score_g1([_competent_case(f"c{i}") for i in range(240)])
    with pytest.raises(ValueError):
        score_g2([G2Event.SUCCESS] * 240)
    with pytest.raises(ValueError):
        score_g3([G3Event.SAFE] * 240)


def test_no_literal_240_denominator_in_restoration_modules():
    """No restoration module may use 240 as a denominator or comparison bound."""
    for module in RESTORATION_MODULES:
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == 240:
                pytest.fail(
                    f"{module.__name__} contains the literal 240 at line "
                    f"{node.lineno}; endpoint sizes must come from the registry"
                )


def test_endpoint_membership_matches_registry():
    """Superseded defect: F07 and F19 credited on G2, which they do not carry."""
    g2 = populations.build_endpoint_population("family_recovery")
    families = {case_id.split("|")[2] for case_id in g2.case_ids}
    assert "F07" not in families
    assert "F19" not in families
    assert "F20" not in families

    g3 = populations.build_endpoint_population("principal_structural_safety")
    assert {case_id.split("|")[2] for case_id in g3.case_ids} == {"F07", "F19", "F20"}


def test_families_without_primary_endpoints_are_excluded_everywhere():
    """F06, F13, F14, F15, F16 carry no primary endpoint at all."""
    barren = {"F06", "F13", "F14", "F15", "F16"}
    for name in ENDPOINTS:
        population = populations.build_endpoint_population(name)
        assert not ({c.split("|")[2] for c in population.case_ids} & barren)


# ---------------------------------------------------------------------------
# G1
# ---------------------------------------------------------------------------

def _competent_case(case_id: str, m0: bool = True) -> CaseG1:
    return CaseG1(
        case_id=case_id,
        g_spearman=1.0,
        trajectory_mae=0.0,
        per_energy_mean_mae=1.0,
        m0_accepted=m0,
        cells=1,
        evaluable_compounds=30,
        contract_failure=False,
    )


def test_candidate_test_r2_is_not_g1():
    """Superseded defect: G1 computed as ``candidate_test_r2 >= 0.80``.

    ``candidate_test_r2`` is Gate 7's waiver input.  It is not one of G1's
    three conjuncts, and no restoration module may read it for G1.
    """
    g1_source = inspect.getsource(primary.assess_g1)
    assert "candidate_test_r2" not in g1_source
    assert inspect.getsource(primary._bounding_case_g1).count("candidate_test_r2") == 0


def test_g1_predicate_is_the_three_frozen_conjuncts():
    assert G1_SPEARMAN_GATE == 0.80
    assert G1_TRAJECTORY_RATIO_GATE == 0.80
    assert G1_DENOMINATOR == 164

    # each conjunct alone is sufficient to deny competence
    assert not CaseG1("c", 0.79, 0.0, 1.0, True, 1, 30, False).scalar_competent
    assert not CaseG1("c", 1.0, 0.81, 1.0, True, 1, 30, False).scalar_competent
    assert not CaseG1("c", 1.0, 0.0, 1.0, False, 1, 30, False).scalar_competent
    assert CaseG1("c", 1.0, 0.0, 1.0, True, 1, 30, False).scalar_competent


def test_g1_upper_bound_mode_is_bounded_by_m0_accepted():
    """The bounding construction must reduce competence exactly to m0_accepted."""
    bounded = primary._bounding_case_g1("c", m0_accepted=True)
    assert bounded.scalar_competent is True
    denied = primary._bounding_case_g1("c", m0_accepted=False)
    assert denied.scalar_competent is False


# ---------------------------------------------------------------------------
# G2
# ---------------------------------------------------------------------------

def test_g2_requires_support_and_family_match():
    """Superseded defect: ``g2_event == SUCCESS OR support_status == MATCH``."""
    assert evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.MATCH) == G2Event.SUCCESS
    # support MATCH alone must NOT be a success -- this is the superseded OR
    assert (
        evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.MISMATCH)
        == G2Event.FAILURE
    )
    assert (
        evaluate_g2_event(SupportStatus.MISMATCH, FamilyStatus.MATCH)
        == G2Event.FAILURE
    )


def test_g2_unevaluable_stays_in_the_denominator():
    events = [G2Event.UNEVALUABLE] * 143 + [G2Event.SUCCESS]
    score = score_g2(events)
    assert score.denominator == 144
    assert score.successes == 1
    assert score.non_successes == 143


# ---------------------------------------------------------------------------
# G3
# ---------------------------------------------------------------------------

def test_g3_counts_violations_over_36_with_wilson_upper():
    """Superseded defect: G3 counted 'successes' over 240, direction inverted."""
    assert G3_HELD_OUT_DENOMINATOR == 36
    assert G3_WILSON_UPPER_GATE == 0.15
    all_safe = score_g3([G3Event.SAFE] * 36)
    assert all_safe.violations == 0
    assert all_safe.gate_passed is True

    mostly_violating = score_g3([G3Event.VIOLATION] * 26 + [G3Event.SAFE] * 10)
    assert mostly_violating.violations == 26
    # the gate is an UPPER bound: many violations must FAIL
    assert mostly_violating.gate_passed is False
    assert mostly_violating.wilson_upper > G3_WILSON_UPPER_GATE


def test_g3_unevaluable_is_a_violation():
    from muru.paper_benchmark.g3_contract import classify_g3_event
    from muru.paper_benchmark.structural_acceptance import (
        AcceptanceResult,
        AcceptanceStatus,
    )

    unevaluable = AcceptanceResult(AcceptanceStatus.UNEVALUABLE, "a1_adequacy")
    for variant in ("F07", "F19A", "F19B", "F19C", "F20A", "F20B", "F20C"):
        assert classify_g3_event(variant, unevaluable, frozenset()) == G3Event.VIOLATION


def test_g3_sole_authority_is_g3_contract():
    """A3.5 §8.3: ``analysis.classify_negative_control`` must not score G3."""
    code = _executable_source(primary)
    assert "classify_negative_control" not in code
    assert "classify_g3_event" in code


# ---------------------------------------------------------------------------
# Gate 7 / Gate 8 / F5 / F9
# ---------------------------------------------------------------------------

def test_gate8_is_four_rungs_and_excludes_g1():
    """Superseded defect: ``gate8_pass = gate7_pass and g1_pass``."""
    assert REQUIRED_HARD_GATES == frozenset({
        FalsificationRung.F1_REPRODUCIBILITY,
        FalsificationRung.F4_COMPOUND_HOLDOUT,
        FalsificationRung.F7_INFLUENCE_DROP,
        FalsificationRung.F10_NEGATIVE_CONTROL,
    })
    assert len(REQUIRED_HARD_GATES) == 4

    gate8_code = _executable_source(primary.evaluate_gate8)
    for forbidden in ("g1", "G1", "scalar_competence", "score_g1", "CaseG1"):
        assert forbidden not in gate8_code, (
            f"Gate 8 evaluation references {forbidden!r}; G1 is an endpoint, "
            f"not a gate"
        )


def test_gate8_fail_closed_on_missing_rung():
    """Superseded ambiguity: a missing or NOT_APPLICABLE rung must not pass."""
    complete = {rung: FalsificationResult.PASS for rung in REQUIRED_HARD_GATES}
    assert check_gate8(complete) is True

    for rung in REQUIRED_HARD_GATES:
        missing = dict(complete)
        del missing[rung]
        assert check_gate8(missing) is False, f"missing {rung.value} passed"

        not_applicable = dict(complete)
        not_applicable[rung] = FalsificationResult.NOT_APPLICABLE
        assert check_gate8(not_applicable) is False


def test_gate7_is_the_ceiling_test_not_structural_acceptance():
    """Superseded defect: Gate 7 read as ``acceptance_status == STRUCTURAL_ACCEPTED``."""
    assert primary.GATE7_REACHED_STAGES == frozenset(
        {"ceiling", "falsification", "all_passed"}
    )
    assert primary.GATE7_PASSED_STAGES == frozenset({"falsification", "all_passed"})
    # Gate 7 passing is strictly weaker than structural acceptance
    assert primary.GATE8_PASSED_STAGES < primary.GATE7_PASSED_STAGES
    source = inspect.getsource(primary.evaluate_gate7)
    assert "STRUCTURAL_ACCEPTED" not in source


def test_f5_is_not_a_hard_rung():
    """A3.5 §6.9.2: F5 is superseded and absent from the enum entirely."""
    assert not hasattr(FalsificationRung, "F5_SCAFFOLD_HOLDOUT")
    assert "F5_SCAFFOLD_HOLDOUT" not in {r.value for r in FalsificationRung}
    assert "F5_SCAFFOLD_HOLDOUT" not in {r.value for r in REQUIRED_HARD_GATES}


def test_f9_is_never_gating():
    """A3.5 §6.9.4: F9 may never enter the hard set, structurally."""
    assert SECONDARY_REPORTED_RUNGS == frozenset({FalsificationRung.F9_ENERGY_SUBSET})
    assert not (REQUIRED_HARD_GATES & SECONDARY_REPORTED_RUNGS)

    # F9 PASS cannot rescue a failing hard rung, and F9 FAIL cannot sink a passing one
    with_f9_fail = {rung: FalsificationResult.PASS for rung in REQUIRED_HARD_GATES}
    with_f9_fail[FalsificationRung.F9_ENERGY_SUBSET] = FalsificationResult.FAIL
    assert check_gate8(with_f9_fail) is True


def test_f9_report_carries_the_drafting_guard():
    assert "NOT be cited" in primary.F9_CITATION_PROHIBITION
    assert "NOT_PROVEN_FOR_HARD_GATE" in primary.F9_CITATION_PROHIBITION


def test_f9_calibration_status_field_is_not_the_f9_observable():
    """Superseded defect: F9 read from ``f9_acceptance_calibration_status``.

    That field is fixed to NOT_PROVEN_FOR_HARD_GATE by the record contract, so
    testing it against PROVEN_FOR_HARD_GATE is always false.
    """
    source = inspect.getsource(primary.report_f9)
    assert "PROVEN_FOR_HARD_GATE" not in source.replace(
        "NOT_PROVEN_FOR_HARD_GATE", ""
    )
    assert "f9_stress_test_result" in source


# ---------------------------------------------------------------------------
# A1 adequacy
# ---------------------------------------------------------------------------

def test_boundary_limited_is_unevaluable_not_adequate():
    """Superseded defect: BOUNDARY_LIMITED (and a fictitious M1_NOT_REJECTED)
    were accepted as adequate, making ``is_adequate`` true for all 240 cases."""
    from muru.paper_benchmark.adequacy import (
        CaseAdequacyStatus,
        adequacy_satisfies_g1,
    )
    from muru.paper_benchmark.structural_acceptance import (
        _A1_PERMITTED,
        _A1_UNEVALUABLE_STATES,
    )

    assert _A1_PERMITTED == frozenset({CaseAdequacyStatus.M0_NOT_REJECTED})
    assert CaseAdequacyStatus.BOUNDARY_LIMITED in _A1_UNEVALUABLE_STATES
    assert adequacy_satisfies_g1(CaseAdequacyStatus.M0_NOT_REJECTED) is True
    assert adequacy_satisfies_g1(CaseAdequacyStatus.BOUNDARY_LIMITED) is False
    assert "M1_NOT_REJECTED" not in {s.value for s in CaseAdequacyStatus}


# ---------------------------------------------------------------------------
# schema conformance / silent defaults
# ---------------------------------------------------------------------------

def test_no_silent_defaults_in_restoration_modules():
    """No ``.get(key, default)`` on a record payload anywhere."""
    for module in (primary, payload_mod):
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and len(node.args) == 2
            ):
                pytest.fail(
                    f"{module.__name__}:{node.lineno} uses a two-argument .get(); "
                    f"a defaulted read of an absent field is what produced the "
                    f"superseded numbers"
                )


def test_require_raises_on_absent_field():
    record = payload_mod.SealedRecord(case_id="c", payload={"a": 1})
    assert record.require("a") == 1
    with pytest.raises(payload_mod.MissingRecordField):
        record.require("gate7_pass")


def test_fields_the_superseded_analyzer_invented_are_absent_from_the_schema():
    invented = {
        "gate7_pass", "gate8_pass", "g1_pass", "g1_wilson_lower", "g2_recovered",
        "g3_pass", "g3_event", "f9_pass", "adequate", "status", "stability_score",
    }
    assert not (invented & payload_mod.SEALED_RECORD_KEYS)


def test_schema_conformance_rejects_a_wrong_key_set():
    record = payload_mod.SealedRecord(
        case_id="c",
        payload={"schema_version": "muru-rc5-case-record-2.0.0"},
    )
    with pytest.raises(payload_mod.SchemaConformanceError):
        record.assert_schema_conformance()


# ---------------------------------------------------------------------------
# decision rule
# ---------------------------------------------------------------------------

def test_decision_rule_is_three_wilson_gates_not_existence():
    """Superseded defect: ``g1>0 and g2>0 and gate8>0`` -> ``decision_passed: true``."""
    assert not hasattr(primary.HeldOutContractAnalysis, "decision_passed")
    source = inspect.getsource(primary)
    assert "decision_passed" not in source

    assert primary.FrozenDecision(True, True, True).all_primary_endpoints_pass
    for triple in ((False, True, True), (True, False, True), (True, True, False)):
        assert not primary.FrozenDecision(*triple).all_primary_endpoints_pass


def test_gate8_count_is_not_a_primary_endpoint():
    """Structural acceptance is an acceptance count, never an endpoint rate."""
    fields = primary.FrozenDecision.__dataclass_fields__
    assert set(fields) == {"g1_gate_passed", "g2_gate_passed", "g3_gate_passed"}


# ---------------------------------------------------------------------------
# independence
# ---------------------------------------------------------------------------

def test_independent_recomputation_does_not_import_the_primary_analyzer():
    """Superseded defect: the 'independent' module imported the analyzer."""
    tree = ast.parse(inspect.getsource(independent))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "heldout_contract_analysis"
            assert "heldout_contract_analysis" not in (node.module or "")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "heldout_contract_analysis" not in alias.name
    independent._assert_independence()


def test_independence_guard_actually_fires():
    """The guard must be a real check, not decoration."""
    independent.__dict__["_smuggled"] = primary.evaluate_gate7
    try:
        with pytest.raises(independent.IndependenceViolation):
            independent._assert_independence()
    finally:
        del independent.__dict__["_smuggled"]

    independent.__dict__["_smuggled_module"] = primary
    try:
        with pytest.raises(independent.IndependenceViolation):
            independent._assert_independence()
    finally:
        del independent.__dict__["_smuggled_module"]

    independent._assert_independence()


# ---------------------------------------------------------------------------
# sealed-evidence acceptance test
# ---------------------------------------------------------------------------

EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)
RESTORED = Path(__file__).resolve().parents[1] / "results" / "restored"

requires_restored = pytest.mark.skipif(
    not (RESTORED / "heldout_restored_analysis.json").exists(),
    reason="restored analysis not yet produced",
)


@requires_restored
def test_restored_analysis_matches_the_sealed_forensic_result():
    """The acceptance test from the rescue decision, §5."""
    result = json.loads((RESTORED / "heldout_restored_analysis.json").read_text())

    assert result["endpoint_denominators"] == {
        "scalar_competence": 164,
        "family_recovery": 144,
        "principal_structural_safety": 36,
    }
    assert result["acceptance_recomputation_disagreements"] == []
    assert result["failure_stage_distribution"] == {
        "a1_adequacy": 154,
        "all_passed": 25,
        "ceiling": 1,
        "falsification": 1,
        "null_threshold": 16,
        "stability": 43,
    }
    assert result["structural_accepted_count"] == 25

    assert result["g2"]["successes"] == 4
    assert result["g2"]["denominator"] == 144
    assert result["g2"]["gate_passed"] is False
    assert result["g2"]["success_case_ids"] == [
        "PB|held_out|F01|r002",
        "PB|held_out|F01|r005",
        "PB|held_out|F11|r010",
        "PB|held_out|F12|r000",
    ]

    assert result["g3"]["violations"] == 26
    assert result["g3"]["denominator"] == 36
    assert result["g3"]["gate_passed"] is False

    assert result["gate7"]["reached"] == 27
    assert result["gate7"]["passed"] == 26
    assert result["gate7"]["passed_via_ceiling_waiver_only"] == 0
    assert result["gate7"]["failed_case_ids"] == ["PB|held_out|F02|r004"]

    assert result["gate8"]["reached"] == 26
    assert result["gate8"]["passed"] == 25
    assert result["gate8"]["failed_case_ids"] == ["PB|held_out|F07|r005"]
    assert result["gate8"]["per_rung_fail"] == {"F10_NEGATIVE_CONTROL": 1}
    assert result["gate8"]["rung_keys_ever_emitted"] == [
        "F10_NEGATIVE_CONTROL",
        "F1_REPRODUCIBILITY",
        "F4_COMPOUND_HOLDOUT",
        "F7_INFLUENCE_DROP",
    ]

    assert result["f9"]["pass_among_gate8_reachers"] == 26
    assert result["f9"]["fail_among_gate8_reachers"] == 0
    assert result["f9"]["gating"] is False

    assert result["execution_failure_poisoned_by_endpoint"] == {
        "scalar_competence": 0,
        "family_recovery": 0,
        "principal_structural_safety": 0,
    }

    # G1 must satisfy the proven bound and fail the gate
    assert result["g1"]["competent"] <= 67
    assert result["g1"]["denominator"] == 164
    assert result["g1"]["gate_passed"] is False

    assert result["decision"]["all_primary_endpoints_pass"] is False


@requires_restored
def test_independent_recomputation_agrees_with_primary_on_sealed_evidence():
    result = json.loads(
        (RESTORED / "heldout_independent_recomputation.json").read_text()
    )
    assert result["disagreement_count"] == 0, result["disagreements_vs_primary"]


@requires_restored
def test_g1_recovery_ran_zero_searches_and_verified_content_identity():
    recovery = json.loads((RESTORED / "heldout_g1_recovery.json").read_text())
    assert recovery["searches_run"] == 0
    assert recovery["pysr_imported"] is False
    assert recovery["cases"] == 164
    assert recovery["content_identity_mismatches"] == 0
    assert recovery["competent"] <= 164
