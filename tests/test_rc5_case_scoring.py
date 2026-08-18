"""RC5's per-case scoring wiring over already-frozen scorers.

All fixtures are hand-built.  No benchmark case is generated, so neither the
development engineering-fixture footprint nor the "challenge not constructed"
attestation moves.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.g3_contract import G3Event
from muru.paper_benchmark.rc3_acceptance import null_threshold_digest
from muru.paper_benchmark.rc5_case_scoring import (
    case_acceptance,
    case_g3_event,
    score_case_secondaries,
    score_partition_g3,
)
from muru.paper_benchmark.structural_acceptance import (
    AcceptanceResult,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
    StructuralCandidate,
)
from muru.paper_benchmark.truth import TruthRecord

NULL_THRESHOLD = {c: 0.10 + 0.01 * c for c in range(1, 21)}


def _candidate(**overrides) -> StructuralCandidate:
    base = dict(
        valid_r2=0.9,
        complexity=5,
        selection_fraction=25 / 30,
        invalid_fraction=0.0,
        effective_support=frozenset({"mass", "descriptor"}),
        ceiling_fraction=0.95,
        ceiling_r2=0.8,
        falsification_results={
            rung: FalsificationResult.PASS for rung in FalsificationRung
        },
    )
    base.update(overrides)
    return StructuralCandidate(**base)


def _truth(case_id: str = "PB|development|F01|r000") -> TruthRecord:
    """A hand-built truth record in the A3.4 parameter-recovery family."""
    return TruthRecord(
        case_id=case_id,
        partition=case_id.split("|")[1],
        family="F01",
        variant="F01",
        seeds={"compounds": 1, "law": 2, "response": 3},
        phi={"family": "stretched_exponential", "mu_inf": 0.2, "phi_p": 1.4},
        g_definition="sqrt(mass) * (1 + coefficient * descriptor)",
        g_by_compound={},
        descriptor_relationship="sqrt(mass) * (1 + coefficient * descriptor)",
        active_variables=["mass", "descriptor"],
        mathematical_family="mass_affine_descriptor",
        coefficients={"scale": 1.5, "coefficient": 0.4},
        exponents={"mass": 0.5},
        noise={"mechanism": "additive_gaussian", "sd": 0.0},
        missingness={"mechanism": "none", "rate": 0.0},
        scalar_truth_defined=True,
        m0_adequacy_truth="M0",
        symbolic_truth_kind="defined",
        applicable_endpoints=["family_recovery", "scalar_competence"],
        expected_behavior="recover scalar and family",
    )


# -----------------------------------------------------------------------
# Acceptance wiring
# -----------------------------------------------------------------------

def test_case_acceptance_returns_the_verdict_and_stamps_the_table():
    result = case_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED, _candidate(), NULL_THRESHOLD
    )
    assert result.result.status is AcceptanceStatus.STRUCTURAL_ACCEPTED
    assert result.result.gate_reached == "all_passed"
    assert result.null_threshold_digest == null_threshold_digest(NULL_THRESHOLD)
    assert len(result.null_threshold_digest) == 64


def test_the_digest_changes_with_the_table_and_only_with_the_table():
    a = case_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED, _candidate(), NULL_THRESHOLD
    ).null_threshold_digest
    b = case_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED,
        _candidate(valid_r2=0.99),
        NULL_THRESHOLD,
    ).null_threshold_digest
    other = dict(NULL_THRESHOLD)
    other[5] = other[5] + 1e-12
    c = case_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED, _candidate(), other
    ).null_threshold_digest
    assert a == b
    assert a != c


def test_no_candidate_is_unevaluable_and_still_carries_a_digest():
    result = case_acceptance(
        CaseAdequacyStatus.M0_NOT_REJECTED, None, NULL_THRESHOLD
    )
    assert result.result.status is AcceptanceStatus.UNEVALUABLE
    assert result.result.gate_reached == "no_candidate"
    assert result.null_threshold_digest == null_threshold_digest(NULL_THRESHOLD)


def test_the_predicate_input_type_cannot_carry_truth():
    # Structural, not behavioural: StructuralCandidate has no truth slot, so a
    # caller cannot hand planted truth to the acceptance predicate at all.
    fields = set(StructuralCandidate.__dataclass_fields__)
    assert not {f for f in fields if "truth" in f or "family" in f}


# -----------------------------------------------------------------------
# A3.4 secondaries, per case
# -----------------------------------------------------------------------

def test_secondaries_are_scored_per_case_by_the_frozen_scorers():
    accepted = AcceptanceResult(AcceptanceStatus.STRUCTURAL_ACCEPTED, "all_passed")
    result = score_case_secondaries(
        "PB|development|F01|r000",
        "1.5 * sqrt(mass / 250.0) * (1 + 0.4 * descriptor)",
        _truth(),
        accepted,
    )
    assert result.case_id == "PB|development|F01|r000"
    assert result.parameter_recovery.p_mass == pytest.approx(0.5, abs=1e-6)
    assert result.predictive_equivalence.applicable is True


def test_secondaries_refuse_a_truth_record_for_another_case():
    accepted = AcceptanceResult(AcceptanceStatus.STRUCTURAL_ACCEPTED, "all_passed")
    with pytest.raises(ValueError, match="truth record is for"):
        score_case_secondaries(
            "PB|development|F01|r001", "mass", _truth("PB|development|F01|r000"), accepted
        )


def test_a_missing_expression_is_a_scored_non_success_not_a_crash():
    accepted = AcceptanceResult(AcceptanceStatus.STRUCTURAL_ACCEPTED, "all_passed")
    result = score_case_secondaries(
        "PB|development|F01|r000", None, _truth(), accepted
    )
    assert result.parameter_recovery.joint_success is False
    assert result.predictive_equivalence.success is False


def test_scoring_secondaries_requires_an_existing_acceptance_verdict():
    # The ordering constraint is enforced by the signature: the truth-reading
    # scorer cannot be called without an AcceptanceResult already in hand.
    import inspect

    params = inspect.signature(score_case_secondaries).parameters
    assert "acceptance" in params
    assert params["acceptance"].default is inspect.Parameter.empty


# -----------------------------------------------------------------------
# G3, through the sole authority
# -----------------------------------------------------------------------

def test_g3_event_uses_the_registry_variant():
    unevaluable = AcceptanceResult(AcceptanceStatus.UNEVALUABLE, "no_candidate")
    assert case_g3_event("PB|held_out|F07|r000", unevaluable, None) is G3Event.VIOLATION

    accepted = AcceptanceResult(AcceptanceStatus.STRUCTURAL_ACCEPTED, "all_passed")
    assert (
        case_g3_event("PB|held_out|F07|r000", accepted, frozenset({"mass"}))
        is G3Event.SAFE
    )
    assert (
        case_g3_event(
            "PB|held_out|F07|r000", accepted, frozenset({"mass", "descriptor"})
        )
        is G3Event.UNSAFE
    )


def test_g3_scoring_enforces_its_frozen_denominator():
    with pytest.raises(ValueError, match="expected 36"):
        score_partition_g3([G3Event.SAFE] * 35)
