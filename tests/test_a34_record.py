"""Deterministic candidate-binding checks for the A3.4 endpoint sidecar."""
from __future__ import annotations

import json

import pytest

from muru.paper_benchmark.a34_contract import EXPECTED_REFERENCE_DIGEST
from muru.paper_benchmark.a34_predictive_equivalence import (
    PredictiveEquivalenceResult,
)
from muru.paper_benchmark.a34_record import (
    A34_CONTRACT_IDENTITY,
    CandidateBindingSidecar,
    candidate_expression_grammar_digest,
    truth_record_snapshot_digest,
)
from muru.paper_benchmark.truth import TruthRecord


def successful_result(**overrides) -> PredictiveEquivalenceResult:
    values = dict(
        applicable=True,
        success=True,
        valid_count=2160,
        valid_fraction=1.0,
        c_star=0.5,
        rmse=0.0,
        truth_rms=1.5,
        rel_rmse=0.0,
        pearson_r=1.0,
        failure_reason=None,
    )
    values.update(overrides)
    return PredictiveEquivalenceResult(**values)


def binding_truth(
    *,
    scale: float = 1.0,
    coefficient: float = 0.4,
    mass_exponent: float = 0.5,
    per_compound: dict[str, float] | None = None,
) -> TruthRecord:
    """Make the scalar law fields that A3.4 reconstructs and binds."""
    return TruthRecord(
        case_id="PB|constructed|F08|r000",
        partition="constructed",
        family="F08",
        variant="constructed",
        seeds={},
        phi={},
        g_definition=None,
        g_by_compound={} if per_compound is None else per_compound,
        descriptor_relationship=None,
        active_variables=["mass", "descriptor"],
        mathematical_family="mass_affine_descriptor",
        coefficients={"scale": scale, "coefficient": coefficient},
        exponents={"mass": mass_exponent},
        noise={},
        missingness={},
        scalar_truth_defined=True,
        m0_adequacy_truth="constructed",
        symbolic_truth_kind="constructed",
        applicable_endpoints=[],
        expected_behavior="constructed fixture",
    )


def sidecar(**overrides) -> CandidateBindingSidecar:
    values = dict(
        case_id="PB|constructed|F08|r000",
        source_case_record_digest="a" * 64,
        candidate_expression="2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)",
        grammar_version="g2-protected-primitives-1.0.0",
        truth=binding_truth(),
        result=successful_result(),
        contract_identity=A34_CONTRACT_IDENTITY,
        reference_digest=EXPECTED_REFERENCE_DIGEST,
    )
    values.update(overrides)
    return CandidateBindingSidecar(**values)


def test_sidecar_binds_the_expression_and_grammar_by_a_deterministic_digest():
    """Changing candidate text or grammar must invalidate the endpoint record."""
    record = sidecar()
    payload = record.scientific_payload()

    assert payload["candidate_expression_grammar_digest"] == candidate_expression_grammar_digest(
        "2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)",
        "g2-protected-primitives-1.0.0",
    )
    assert "candidate_expression" not in payload
    assert "grammar_version" not in payload
    assert sidecar(candidate_expression="sqrt(mass / 250)").scientific_digest() != record.scientific_digest()
    assert sidecar(grammar_version="g2-protected-primitives-2.0.0").scientific_digest() != record.scientific_digest()


def test_sidecar_digest_is_sensitive_to_every_frozen_binding_and_result():
    """A stale source, contract, reference, or result cannot share a digest."""
    baseline = sidecar().scientific_digest()

    assert sidecar(source_case_record_digest="b" * 64).scientific_digest() != baseline
    assert sidecar(contract_identity="paper-benchmark-secondary-endpoints-1.1.1").scientific_digest() != baseline
    assert sidecar(reference_digest="c" * 64).scientific_digest() != baseline
    assert sidecar(truth=binding_truth(scale=1.1)).scientific_digest() != baseline
    assert sidecar(truth=binding_truth(coefficient=0.5)).scientific_digest() != baseline
    assert sidecar(truth=binding_truth(mass_exponent=0.6)).scientific_digest() != baseline
    assert sidecar(result=successful_result(success=False, failure_reason="metric threshold missed")).scientific_digest() != baseline


def test_truth_snapshot_binds_scalar_law_fields_without_per_compound_values():
    """The sidecar must bind the truth used by reconstruction, not outcomes."""
    baseline = binding_truth()
    changed_values = binding_truth(per_compound={"C000": 1e100})
    payload = sidecar(truth=baseline).scientific_payload()

    assert payload["truth_record_snapshot_digest"] == truth_record_snapshot_digest(baseline)
    assert truth_record_snapshot_digest(changed_values) == truth_record_snapshot_digest(baseline)
    assert "per_compound" not in sidecar(truth=changed_values).to_canonical_json()


def test_sidecar_freezes_the_truth_snapshot_when_input_maps_mutate_after_creation():
    """An old score must retain the exact truth snapshot it was adjudicated on."""
    truth = binding_truth()
    record = sidecar(truth=truth)
    original_json = record.to_canonical_json()
    original_digest = record.scientific_digest()
    original_truth_digest = record.truth_record_snapshot_digest

    truth.coefficients["scale"] = 1.7
    truth.coefficients["coefficient"] = 0.9
    truth.exponents["mass"] = 0.6

    assert record.to_canonical_json() == original_json
    assert record.scientific_digest() == original_digest
    assert record.truth_record_snapshot_digest == original_truth_digest
    assert sidecar(truth=truth).scientific_digest() != original_digest


def test_sidecar_serialization_is_byte_stable_and_excludes_time_path_and_diagnostics():
    """Runtime metadata must not perturb the scientific endpoint hash."""
    record = sidecar(
        candidate_expression="candidate text from /tmp/run-7/output",
        result=successful_result(success=False, failure_reason="failed under /tmp/run-7"),
    )
    duplicate = sidecar(
        candidate_expression="candidate text from /tmp/run-7/output",
        result=successful_result(success=False, failure_reason="failed under /tmp/run-7"),
    )
    blob = record.to_canonical_json().lower()

    assert record.to_canonical_json() == duplicate.to_canonical_json()
    assert record.scientific_digest() == duplicate.scientific_digest()
    for forbidden in ("timestamp", "started", "finished", "elapsed", "duration", "hostname", "path", "/tmp", "run-7"):
        assert forbidden not in blob


def test_sidecar_payload_is_strict_canonical_json_with_sorted_keys():
    """Equivalent records must serialize independently of construction order."""
    record = sidecar()
    payload = json.loads(record.to_json())

    assert list(payload) == sorted(payload)
    assert record.to_json() == record.to_canonical_json()
    assert "NaN" not in record.to_canonical_json()
    assert "Infinity" not in record.to_canonical_json()


def test_sidecar_is_frozen_and_requires_digest_like_bindings():
    """Mutable or malformed binding data would defeat the audit chain."""
    record = sidecar()

    with pytest.raises(Exception):
        record.reference_digest = "b" * 64  # type: ignore[misc]
    with pytest.raises(ValueError):
        sidecar(source_case_record_digest="not-a-sha256")
    with pytest.raises(ValueError):
        sidecar(reference_digest="not-a-sha256")


def test_sidecar_rejects_a_case_identifier_that_disagrees_with_its_truth():
    """A binding record cannot pair one score's case ID with another truth law."""
    with pytest.raises(ValueError, match="case ID must match truth case ID"):
        sidecar(case_id="PB|constructed|F09|r000")
