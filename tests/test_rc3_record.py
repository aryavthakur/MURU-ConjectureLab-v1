"""RC3 per-case execution record: schema completeness and serialization determinism.

Every record here is constructed.  No real case, partition or outcome is read.
"""
from __future__ import annotations

import json
import math

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import FamilyStatus, G2Event, SupportStatus
from muru.paper_benchmark.rc3_record import (
    FALSIFICATION_RUNG_ORDER,
    HARD_GATE_ORDER,
    LEGACY_FALSIFICATION_RUNG_NAMES,
    LEGACY_RECORD_SCHEMA_VERSIONS,
    RECORD_SCHEMA_VERSION,
    CaseExecutionRecord,
    PerSeedStatusEntry,
    ProvenanceSidecar,
    SchemaVersionError,
    canonical_json,
    record_schema_generation,
)
from muru.paper_benchmark.structural_acceptance import (
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
)


def make_record(**overrides) -> CaseExecutionRecord:
    base = dict(
        case_id="PB|constructed|F01|r000",
        family_id="F01",
        partition_label="constructed",
        truth_family="mass_affine_descriptor",
        truth_support=frozenset({"mass", "descriptor"}),
        discovered_expression_string="sqrt(mass) * (1 + 0.3 * descriptor)",
        effective_support=frozenset({"descriptor", "mass"}),
        support_status=SupportStatus.MATCH,
        family_status=FamilyStatus.MATCH,
        discovered_family="mass_affine_descriptor",
        g2_event=G2Event.SUCCESS,
        a1_case_adequacy_status=CaseAdequacyStatus.M0_NOT_REJECTED,
        valid_r2=0.8123456789012345,
        complexity=9,
        selection_count=27,
        selection_denominator=30,
        invalid_fraction=0.0,
        ceiling_r2=0.9,
        ceiling_fraction=0.902606309,
        falsification_results={
            rung: FalsificationResult.PASS for rung in HARD_GATE_ORDER
        },
        candidate_test_r2=0.77,
        f9_stress_test_result=FalsificationResult.PASS,
        f9_stress_test_metric=0.41,
        acceptance_status=AcceptanceStatus.STRUCTURAL_ACCEPTED,
        acceptance_gate_reached="all_passed",
        per_seed_status=[
            PerSeedStatusEntry(seed=1, status=SeedStatus.COMPLETED_WITH_CANDIDATES),
            PerSeedStatusEntry(seed=2, status=SeedStatus.COMPLETED_NO_CANDIDATE),
            PerSeedStatusEntry(
                seed=3, status=SeedStatus.EXECUTION_FAILURE, error_message="boom"
            ),
        ],
        seeds_used=[1, 2, 3],
        engine_versions={"pysr": "1.5.10", "scikit-learn": "1.9.0"},
    )
    base.update(overrides)
    return CaseExecutionRecord(**base)


# -----------------------------------------------------------------------
# Schema completeness
# -----------------------------------------------------------------------

REQUIRED_FIELDS = {
    "case_id", "family_id", "partition_label",
    "truth_family", "truth_support",
    "discovered_expression_string", "effective_support",
    "support_status", "family_status", "g2_event",
    "a1_case_adequacy_status",
    "valid_r2", "complexity", "selection_fraction", "invalid_fraction",
    "ceiling_r2", "ceiling_fraction",
    "falsification_results",
    "acceptance_status", "acceptance_gate_reached",
    "per_seed_status", "engine_versions", "seeds_used",
}


def test_payload_carries_every_contract_field():
    payload = make_record().scientific_payload()
    assert REQUIRED_FIELDS <= set(payload)


def test_the_four_hard_gates_are_present_in_fixed_order():
    """A3.5 section 6.9.4 narrowed the gating set from six rungs to four."""
    payload = make_record().scientific_payload()
    assert list(payload["falsification_results"]) == [
        r.value for r in HARD_GATE_ORDER
    ]
    assert len(HARD_GATE_ORDER) == 4
    for rung in (
        FalsificationRung.F1_REPRODUCIBILITY,
        FalsificationRung.F4_COMPOUND_HOLDOUT,
        FalsificationRung.F7_INFLUENCE_DROP,
        FalsificationRung.F10_NEGATIVE_CONTROL,
    ):
        assert rung in HARD_GATE_ORDER
    assert FalsificationRung.F9_ENERGY_SUBSET not in HARD_GATE_ORDER
    assert not hasattr(FalsificationRung, "F5_SCAFFOLD_HOLDOUT")
    # The historical spelling still resolves, to the same tuple.
    assert FALSIFICATION_RUNG_ORDER is HARD_GATE_ORDER


def test_f9_is_recorded_as_a_reported_secondary_not_a_gate():
    payload = make_record().scientific_payload()
    assert "F9_ENERGY_SUBSET" not in payload["falsification_results"]
    assert payload["f9_stress_test_result"] == "PASS"
    assert payload["f9_stress_test_metric"] == 0.41
    assert payload["f9_acceptance_calibration_status"] == "NOT_PROVEN_FOR_HARD_GATE"


def test_f9_is_still_stored_and_reportable_when_it_fails():
    record = make_record(f9_stress_test_result=FalsificationResult.FAIL,
                         f9_stress_test_metric=-2.5)
    payload = record.scientific_payload()
    assert payload["f9_stress_test_result"] == "FAIL"
    assert payload["f9_stress_test_metric"] == -2.5
    # And the case is still recorded as accepted: F9 cannot reject it.
    assert payload["acceptance_status"] == "STRUCTURAL_ACCEPTED"


def test_a_non_hard_gate_rung_may_not_enter_the_gate8_mapping():
    smuggled = {rung: FalsificationResult.PASS for rung in HARD_GATE_ORDER}
    smuggled[FalsificationRung.F9_ENERGY_SUBSET] = FalsificationResult.PASS
    with pytest.raises(ValueError, match="non-hard-gate rungs"):
        make_record(falsification_results=smuggled)


def test_a_case_reaching_gate8_must_record_the_f9_secondary():
    with pytest.raises(ValueError, match="obligation 19"):
        make_record(f9_stress_test_result=None, f9_stress_test_metric=None)
    with pytest.raises(ValueError, match="requires both"):
        make_record(f9_stress_test_metric=None)


def test_a_case_that_never_reached_gate8_records_no_f9_result():
    record = make_record(
        acceptance_status=AcceptanceStatus.REJECTED_UNSTABLE,
        acceptance_gate_reached="stability",
        f9_stress_test_result=None,
        f9_stress_test_metric=None,
    )
    assert record.scientific_payload()["f9_stress_test_result"] is None
    with pytest.raises(ValueError, match="did not reach Gate 8"):
        make_record(
            acceptance_status=AcceptanceStatus.REJECTED_UNSTABLE,
            acceptance_gate_reached="stability",
        )


def test_f9_may_never_be_recorded_as_not_applicable():
    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        make_record(f9_stress_test_result=FalsificationResult.NOT_APPLICABLE)


def test_candidate_test_r2_is_carried_and_affects_the_digest():
    baseline = make_record().scientific_digest()
    assert make_record(candidate_test_r2=0.12).scientific_digest() != baseline
    assert make_record().scientific_payload()["candidate_test_r2"] == 0.77


# -----------------------------------------------------------------------
# Schema version bump (A3.5 section 6.9.4, RC5 obligations 14/18/19)
# -----------------------------------------------------------------------

def test_the_schema_version_is_bumped_and_the_old_one_is_known_legacy():
    assert RECORD_SCHEMA_VERSION == "muru-rc5-case-record-2.0.0"
    assert "muru-rc3-case-record-1.0.0" in LEGACY_RECORD_SCHEMA_VERSIONS
    assert RECORD_SCHEMA_VERSION not in LEGACY_RECORD_SCHEMA_VERSIONS
    assert make_record().scientific_payload()["schema_version"] == RECORD_SCHEMA_VERSION


def test_an_old_record_is_identifiable_and_is_never_read_as_a_new_one():
    legacy = {
        "schema_version": "muru-rc3-case-record-1.0.0",
        "falsification_results": {n: "PASS" for n in LEGACY_FALSIFICATION_RUNG_NAMES},
    }
    assert record_schema_generation(legacy) == "legacy"
    assert record_schema_generation(make_record().scientific_payload()) == "current"
    # The legacy mapping carries two rungs the current generation forbids, so
    # reading it as current would silently change what the record means.
    assert "F5_SCAFFOLD_HOLDOUT" in legacy["falsification_results"]
    assert "F9_ENERGY_SUBSET" in legacy["falsification_results"]


def test_an_unversioned_or_unknown_record_is_refused_rather_than_guessed():
    with pytest.raises(SchemaVersionError):
        record_schema_generation({})
    with pytest.raises(SchemaVersionError):
        record_schema_generation({"schema_version": "muru-rc9-case-record-9.9.9"})


def test_selection_fraction_is_k_over_30():
    assert make_record(selection_count=20).selection_fraction == 20 / 30
    assert make_record(selection_count=30).selection_fraction == 1.0


# -----------------------------------------------------------------------
# Serialization determinism
# -----------------------------------------------------------------------

def test_serialization_is_byte_identical_across_constructions():
    assert make_record().to_canonical_json() == make_record().to_canonical_json()
    assert make_record().scientific_digest() == make_record().scientific_digest()


def test_set_ordering_does_not_affect_bytes():
    a = make_record(
        truth_support=frozenset({"mass", "descriptor"}),
        effective_support=frozenset({"mass", "descriptor"}),
    )
    b = make_record(
        truth_support=frozenset({"descriptor", "mass"}),
        effective_support=frozenset({"descriptor", "mass"}),
    )
    assert a.to_canonical_json() == b.to_canonical_json()


def test_mapping_insertion_order_does_not_affect_bytes():
    forward = dict.fromkeys(HARD_GATE_ORDER, FalsificationResult.PASS)
    reverse = dict.fromkeys(reversed(HARD_GATE_ORDER), FalsificationResult.PASS)
    a = make_record(falsification_results=forward,
                    engine_versions={"pysr": "1.5.10", "scikit-learn": "1.9.0"})
    b = make_record(falsification_results=reverse,
                    engine_versions={"scikit-learn": "1.9.0", "pysr": "1.5.10"})
    assert a.to_canonical_json() == b.to_canonical_json()


def test_json_keys_are_sorted():
    payload = json.loads(make_record().to_canonical_json())
    assert list(payload) == sorted(payload)


def test_no_timestamp_in_the_scientific_payload():
    blob = make_record().to_canonical_json().lower()
    for banned in ("timestamp", "started", "finished", "wall_seconds",
                   "utc", "hostname", "elapsed", "duration"):
        assert banned not in blob


def test_non_finite_floats_round_trip_as_sentinels():
    record = make_record(valid_r2=float("-inf"), ceiling_fraction=float("nan"))
    payload = json.loads(record.to_canonical_json())
    assert payload["valid_r2"] == "-Infinity"
    assert payload["ceiling_fraction"] == "NaN"
    # strict JSON: no bare NaN/Infinity literals
    assert "NaN," not in record.to_canonical_json().replace('"NaN"', "")


def test_float_formatting_is_fixed():
    """A float must serialize to exactly one representation, always."""
    value = 0.1 + 0.2
    a = canonical_json({"x": value})
    b = canonical_json({"x": 0.30000000000000004})
    assert a == b == '{"x":0.30000000000000004}'


def test_digest_changes_when_science_changes():
    baseline = make_record().scientific_digest()
    one_ulp_up = math.nextafter(0.8123456789012345, math.inf)
    assert one_ulp_up != 0.8123456789012345
    assert make_record(valid_r2=one_ulp_up).scientific_digest() != baseline
    assert make_record(g2_event=G2Event.FAILURE).scientific_digest() != baseline
    assert make_record(selection_count=26).scientific_digest() != baseline


def test_per_seed_statuses_are_recorded_verbatim():
    payload = make_record().scientific_payload()
    assert [e["status"] for e in payload["per_seed_status"]] == [
        "COMPLETED_WITH_CANDIDATES",
        "COMPLETED_NO_CANDIDATE",
        "EXECUTION_FAILURE",
    ]


# -----------------------------------------------------------------------
# Provenance sidecar separation
# -----------------------------------------------------------------------

def test_sidecar_holds_the_timestamps_and_does_not_touch_the_digest():
    record = make_record()
    digest = record.scientific_digest()

    early = ProvenanceSidecar(
        case_id=record.case_id, scientific_digest=digest,
        started_utc="2026-01-01T00:00:00+00:00",
        finished_utc="2026-01-01T00:01:00+00:00",
        wall_seconds=60.0, host_platform="darwin", commit="abc",
    )
    late = ProvenanceSidecar(
        case_id=record.case_id, scientific_digest=digest,
        started_utc="2027-06-06T12:00:00+00:00",
        finished_utc="2027-06-06T13:00:00+00:00",
        wall_seconds=3600.0, host_platform="linux", commit="def",
    )

    assert early.to_json() != late.to_json()
    assert record.scientific_digest() == digest
    assert early.scientific_digest == late.scientific_digest == digest


def test_record_is_frozen():
    record = make_record()
    with pytest.raises(Exception):
        record.valid_r2 = 0.0  # type: ignore[misc]


def test_canonical_json_rejects_unencodable_types():
    with pytest.raises(TypeError):
        canonical_json({"x": object()})


# -----------------------------------------------------------------------
# Free text must not reach the scientific digest
# -----------------------------------------------------------------------

def test_exception_message_does_not_enter_the_scientific_digest():
    """Two runs whose failures differ only by a temp path must agree.

    A full exception message carries temp directories and PIDs, which would
    make identical science produce different digests.
    """
    def with_message(message):
        return make_record(per_seed_status=[
            PerSeedStatusEntry(
                seed=1, status=SeedStatus.EXECUTION_FAILURE, error_message=message
            )
        ])

    a = with_message("RuntimeError: julia died in /var/folders/xy/T/tmp8x2k/run.log")
    b = with_message("RuntimeError: julia died in /var/folders/zz/T/tmpZZ99/run.log")

    assert a.scientific_digest() == b.scientific_digest()
    assert "tmp8x2k" not in a.to_canonical_json()
    assert "/var/folders" not in a.to_canonical_json()


def test_the_exception_type_is_still_recorded():
    record = make_record(per_seed_status=[
        PerSeedStatusEntry(
            seed=1, status=SeedStatus.EXECUTION_FAILURE,
            error_message="MemoryError: out of memory at 0x7f",
        )
    ])
    entry = record.scientific_payload()["per_seed_status"][0]
    assert entry["error_type"] == "MemoryError"
    assert "error_message" not in entry


def test_a_different_exception_type_does_change_the_digest():
    def with_type(message):
        return make_record(per_seed_status=[
            PerSeedStatusEntry(
                seed=1, status=SeedStatus.EXECUTION_FAILURE, error_message=message
            )
        ])
    assert (
        with_type("MemoryError: x").scientific_digest()
        != with_type("RuntimeError: x").scientific_digest()
    )


def test_full_message_survives_in_the_diagnostic_projection():
    entry = PerSeedStatusEntry(
        seed=1, status=SeedStatus.EXECUTION_FAILURE,
        error_message="RuntimeError: julia died in /tmp/abc",
    )
    assert entry.to_diagnostic_payload()["error_message"] == (
        "RuntimeError: julia died in /tmp/abc"
    )


# -----------------------------------------------------------------------
# Numeric canonicalization
# -----------------------------------------------------------------------

def test_negative_zero_and_zero_are_one_representation():
    assert canonical_json({"x": -0.0}) == canonical_json({"x": 0.0})
    a = make_record(invalid_fraction=-0.0)
    b = make_record(invalid_fraction=0.0)
    assert a.scientific_digest() == b.scientific_digest()


def test_str_enum_mapping_keys_encode_as_their_value():
    encoded = canonical_json({"r": {FalsificationRung.F1_REPRODUCIBILITY: "PASS"}})
    assert "F1_REPRODUCIBILITY" in encoded
    assert "FalsificationRung." not in encoded


# -----------------------------------------------------------------------
# Record validation
# -----------------------------------------------------------------------

def test_selection_denominator_must_be_the_frozen_thirty():
    """k/20 must not be able to clear a gate k/30 would fail."""
    with pytest.raises(ValueError, match="selection_denominator"):
        make_record(selection_count=14, selection_denominator=20)
    with pytest.raises(ValueError, match="selection_denominator"):
        make_record(selection_count=0, selection_denominator=0)


def test_selection_count_must_be_within_the_denominator():
    with pytest.raises(ValueError, match="selection_count"):
        make_record(selection_count=31)
    with pytest.raises(ValueError, match="selection_count"):
        make_record(selection_count=-1)


def test_a_missing_hard_gate_fails_loudly():
    for rung in HARD_GATE_ORDER:
        partial = {
            other: FalsificationResult.PASS
            for other in HARD_GATE_ORDER
            if other != rung
        }
        with pytest.raises(ValueError, match=rung.value):
            make_record(falsification_results=partial)


def test_an_unknown_acceptance_gate_is_rejected():
    with pytest.raises(ValueError, match="acceptance_gate_reached"):
        make_record(acceptance_gate_reached="whatever_i_like")


def test_rung_order_matches_the_frozen_required_hard_set():
    from muru.paper_benchmark.structural_acceptance import (
        REQUIRED_HARD_GATES,
        SECONDARY_REPORTED_RUNGS,
    )
    assert set(HARD_GATE_ORDER) == set(REQUIRED_HARD_GATES)
    assert not set(HARD_GATE_ORDER) & SECONDARY_REPORTED_RUNGS


def test_null_threshold_digest_is_carried_and_affects_the_digest():
    baseline = make_record().scientific_digest()
    assert make_record(null_threshold_digest="abc123").scientific_digest() != baseline
    assert "null_threshold_digest" in make_record().scientific_payload()
