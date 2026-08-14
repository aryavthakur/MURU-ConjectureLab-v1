"""RC3 acceptance wiring: a record's verdict must match its own inputs.

All records here are constructed.  No real case or outcome is read.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.rc3_acceptance import (
    TRUTH_BLIND_FIELDS,
    AcceptanceMismatch,
    candidate_from_record,
    derive_acceptance,
    null_threshold_digest,
    verify_record_acceptance,
)
from muru.paper_benchmark.structural_acceptance import (
    MAX_COMPLEXITY,
    AcceptanceStatus,
)

from test_rc3_record import make_record

THRESHOLD = {c: 0.10 for c in range(1, MAX_COMPLEXITY + 1)}


# -----------------------------------------------------------------------
# Re-derivation agrees with a well-formed record
# -----------------------------------------------------------------------

def test_a_consistent_record_verifies():
    record = make_record(null_threshold_digest=null_threshold_digest(THRESHOLD))
    check = verify_record_acceptance(record, THRESHOLD)
    assert check.agrees
    assert check.derived_status == AcceptanceStatus.STRUCTURAL_ACCEPTED
    assert check.derived_gate == "all_passed"


def test_derivation_uses_the_frozen_predicate_gate_order():
    record = make_record(valid_r2=0.05)  # below the threshold
    result = derive_acceptance(record, THRESHOLD)
    assert result.status == AcceptanceStatus.REJECTED_BELOW_NULL
    assert result.gate_reached == "null_threshold"


# -----------------------------------------------------------------------
# Contradictions are caught
# -----------------------------------------------------------------------

def test_an_accepted_verdict_contradicting_the_ceiling_is_caught():
    """The exact scenario review named: ACCEPTED recorded, ceiling 0.4."""
    record = make_record(
        ceiling_fraction=0.4,
        ceiling_r2=0.9,
        acceptance_status=AcceptanceStatus.STRUCTURAL_ACCEPTED,
        acceptance_gate_reached="all_passed",
    )
    with pytest.raises(AcceptanceMismatch, match="REJECTED_CEILING"):
        verify_record_acceptance(record, THRESHOLD)


def test_an_accepted_verdict_contradicting_stability_is_caught():
    record = make_record(selection_count=14)  # 14/30 < 20/30
    with pytest.raises(AcceptanceMismatch, match="REJECTED_UNSTABLE"):
        verify_record_acceptance(record, THRESHOLD)


def test_an_accepted_verdict_contradicting_a1_adequacy_is_caught():
    record = make_record(
        a1_case_adequacy_status=CaseAdequacyStatus.M0_REJECTED_M1
    )
    with pytest.raises(AcceptanceMismatch, match="REJECTED_A1_INADEQUATE"):
        verify_record_acceptance(record, THRESHOLD)


def test_strict_false_reports_rather_than_raises():
    record = make_record(selection_count=14)
    check = verify_record_acceptance(record, THRESHOLD, strict=False)
    assert not check.agrees
    assert check.recorded_status == AcceptanceStatus.STRUCTURAL_ACCEPTED
    assert check.derived_status == AcceptanceStatus.REJECTED_UNSTABLE


def test_a_record_scored_against_another_threshold_table_is_caught():
    record = make_record(null_threshold_digest="a" * 64)
    with pytest.raises(AcceptanceMismatch, match="threshold table"):
        verify_record_acceptance(record, THRESHOLD)


def test_a_record_with_no_digest_is_still_verified_on_its_inputs():
    record = make_record(null_threshold_digest="")
    assert verify_record_acceptance(record, THRESHOLD).agrees


# -----------------------------------------------------------------------
# Truth-blindness
# -----------------------------------------------------------------------

def test_the_candidate_projection_carries_no_planted_truth():
    candidate = candidate_from_record(make_record())
    fields = set(vars(candidate)) if hasattr(candidate, "__dict__") else set(
        candidate.__dataclass_fields__
    )
    assert "truth_family" not in fields
    assert "truth_support" not in fields


def test_changing_planted_truth_cannot_change_the_verdict():
    baseline = derive_acceptance(make_record(), THRESHOLD)
    altered = derive_acceptance(
        make_record(truth_family="mass_power", truth_support=frozenset({"mass"})),
        THRESHOLD,
    )
    assert baseline == altered


def test_truth_blind_field_list_excludes_truth():
    assert "truth_family" not in TRUTH_BLIND_FIELDS
    assert "truth_support" not in TRUTH_BLIND_FIELDS
    assert "valid_r2" in TRUTH_BLIND_FIELDS


def test_no_candidate_is_unevaluable_not_rejected():
    record = make_record(
        discovered_expression_string=None,
        acceptance_status=AcceptanceStatus.UNEVALUABLE,
        acceptance_gate_reached="no_candidate",
    )
    assert candidate_from_record(record) is None
    assert verify_record_acceptance(record, THRESHOLD).agrees


# -----------------------------------------------------------------------
# Threshold digest
# -----------------------------------------------------------------------

def test_threshold_digest_is_stable_and_order_independent():
    forward = {c: 0.1 * c for c in range(1, MAX_COMPLEXITY + 1)}
    reverse = dict(reversed(list(forward.items())))
    assert null_threshold_digest(forward) == null_threshold_digest(reverse)


def test_threshold_digest_changes_with_any_threshold():
    base = {c: 0.10 for c in range(1, MAX_COMPLEXITY + 1)}
    moved = {**base, 7: 0.1000000001}
    assert null_threshold_digest(base) != null_threshold_digest(moved)
