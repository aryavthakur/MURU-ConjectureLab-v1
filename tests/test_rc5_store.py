"""RC5 case-scoped record store, atomic writes, and deterministic resume."""
from __future__ import annotations

import json

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import FamilyStatus, G2Event, SupportStatus
from muru.paper_benchmark.rc3_record import (
    CaseExecutionRecord,
    PerSeedStatusEntry,
    ProvenanceSidecar,
)
from muru.paper_benchmark.rc5_store import (
    CaseRecordExists,
    CaseSeedRecordStore,
    append_provenance,
    case_slug,
    completed_case_ids,
    load_case_record_payload,
    resume_plan,
    write_case_record,
)
from muru.paper_benchmark.structural_acceptance import (
    REQUIRED_HARD_GATES,
    AcceptanceStatus,
    FalsificationResult,
)

CASE_A = "PB|development|F01|r000"
CASE_B = "PB|development|F01|r001"
CONTENT_A = "a" * 64
CONTENT_B = "b" * 64


def _record(case_id: str, **overrides) -> CaseExecutionRecord:
    base = dict(
        case_id=case_id,
        family_id="F01",
        partition_label="development",
        truth_family="mass_affine_descriptor",
        truth_support=frozenset({"mass", "descriptor"}),
        discovered_expression_string="mass * descriptor",
        effective_support=frozenset({"mass", "descriptor"}),
        support_status=SupportStatus.MATCH,
        family_status=FamilyStatus.MATCH,
        discovered_family="mass_affine_descriptor",
        g2_event=G2Event.SUCCESS,
        a1_case_adequacy_status=CaseAdequacyStatus.M0_NOT_REJECTED,
        valid_r2=0.9,
        complexity=5,
        selection_count=25,
        selection_denominator=30,
        invalid_fraction=0.0,
        ceiling_r2=0.8,
        ceiling_fraction=0.95,
        falsification_results={
            rung: FalsificationResult.PASS for rung in REQUIRED_HARD_GATES
        },
        candidate_test_r2=0.71,
        f9_stress_test_result=FalsificationResult.PASS,
        f9_stress_test_metric=0.33,
        acceptance_status=AcceptanceStatus.STRUCTURAL_ACCEPTED,
        acceptance_gate_reached="all_passed",
        per_seed_status=(),
        seeds_used=(),
        engine_versions={"pysr": "1.5.10"},
    )
    base.update(overrides)
    return CaseExecutionRecord(**base)


# -----------------------------------------------------------------------
# case_slug
# -----------------------------------------------------------------------

def test_case_slug_is_filesystem_safe_and_injective():
    from muru.paper_benchmark.rc5_seeds import all_case_ids

    slugs = {case_slug(c) for c in all_case_ids()}
    assert len(slugs) == 380
    assert case_slug(CASE_A) == "PB_development_F01_r000"
    assert all("|" not in s and "/" not in s for s in slugs)


# -----------------------------------------------------------------------
# Per-seed store
# -----------------------------------------------------------------------

def _retained(store, case_id, seed, expression="mass"):
    store.append(
        case_id,
        PerSeedStatusEntry(seed, SeedStatus.COMPLETED_WITH_CANDIDATES, expression),
        CONTENT_A,
        complexity=4,
        valid_r2=0.9,
        invalid_fraction=0.0,
    )


def test_seed_records_round_trip(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    _retained(store, CASE_A, 2_100_000_000)
    store.append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_001, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_A,
    )
    loaded = store.load(CASE_A, CONTENT_A)
    assert set(loaded) == {2_100_000_000, 2_100_000_001}
    assert loaded[2_100_000_000].entry.selected_expression_string == "mass"
    assert loaded[2_100_000_000].retained is True
    assert loaded[2_100_000_001].entry.status is SeedStatus.COMPLETED_NO_CANDIDATE
    assert loaded[2_100_000_001].retained is False


def test_a_retained_candidate_must_carry_its_own_decided_values(tmp_path):
    """Without them a resumed run would recompute a decided number."""
    store = CaseSeedRecordStore(tmp_path)
    with pytest.raises(ValueError, match="decided values"):
        store.append(
            CASE_A,
            PerSeedStatusEntry(
                2_100_000_000, SeedStatus.COMPLETED_WITH_CANDIDATES, "mass"
            ),
            CONTENT_A,
        )


def test_the_decided_values_survive_a_reload(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    _retained(store, CASE_A, 2_100_000_000)
    stored = store.load(CASE_A, CONTENT_A)[2_100_000_000]
    assert stored.complexity == 4
    assert stored.valid_r2 == 0.9
    assert stored.invalid_fraction == 0.0


def test_an_absent_case_file_loads_as_empty(tmp_path):
    assert CaseSeedRecordStore(tmp_path).load(CASE_A, CONTENT_A) == {}


def test_a_duplicate_seed_record_is_refused_at_write_time(tmp_path):
    """The guard must fire on APPEND, not only on load.

    A load-only guard lets the writer commit the violation and continue, and
    the file then becomes unreadable by its only reader -- so an auditor cannot
    even enumerate the seed history without destroying evidence.
    """
    store = CaseSeedRecordStore(tmp_path)
    failure = PerSeedStatusEntry(
        2_100_000_000, SeedStatus.EXECUTION_FAILURE, None, "RuntimeError: boom"
    )
    store.append(CASE_A, failure, CONTENT_A)

    with pytest.raises(RuntimeError, match="already has a record"):
        _retained(store, CASE_A, 2_100_000_000)

    # The recorded failure is intact and still loadable.
    loaded = store.load(CASE_A, CONTENT_A)
    assert loaded[2_100_000_000].entry.status is SeedStatus.EXECUTION_FAILURE


def test_a_duplicate_written_out_of_band_is_still_refused_on_load(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    store.append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_000, SeedStatus.EXECUTION_FAILURE, None, "x"),
        CONTENT_A,
    )
    with store.path_for(CASE_A).open("r", encoding="utf-8") as handle:
        line = handle.read()
    with store.path_for(CASE_A).open("a", encoding="utf-8") as handle:
        handle.write(line)
    with pytest.raises(RuntimeError, match="selective retry"):
        store.load(CASE_A, CONTENT_A)


def test_a_truncated_tail_is_discarded_not_adopted(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    _retained(store, CASE_A, 2_100_000_000)
    with store.path_for(CASE_A).open("a", encoding="utf-8") as handle:
        handle.write('{"case_id": "PB|develo')
    loaded = store.load(CASE_A, CONTENT_A)
    assert set(loaded) == {2_100_000_000}


def test_a_corrupt_interior_line_raises_rather_than_being_dropped(tmp_path):
    """Dropping it could hide a recorded EXECUTION_FAILURE.

    A later clean record for the same seed would then appear to be the only
    one, and the duplicate guard would never fire -- silently superseding the
    failure A3.5 section 8.2 says must poison the case.
    """
    store = CaseSeedRecordStore(tmp_path)
    store.append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_000, SeedStatus.EXECUTION_FAILURE, None, "x"),
        CONTENT_A,
    )
    store.append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_001, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_A,
    )
    lines = store.path_for(CASE_A).read_text(encoding="utf-8").splitlines()
    lines[0] = "{corrupt"
    store.path_for(CASE_A).write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not the final line"):
        store.load(CASE_A, CONTENT_A)


def test_a_record_for_another_case_is_refused(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    store.append(
        CASE_B,
        PerSeedStatusEntry(2_100_000_030, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_B,
    )
    store.path_for(CASE_B).rename(store.path_for(CASE_A))
    with pytest.raises(RuntimeError, match="renamed or copied"):
        store.load(CASE_A, CONTENT_B)


def test_a_record_under_different_search_settings_is_refused(tmp_path):
    CaseSeedRecordStore(tmp_path, settings_digest="other").append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_000, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_A,
    )
    with pytest.raises(RuntimeError, match="different\n?\\s*settings|different settings"):
        CaseSeedRecordStore(tmp_path).load(CASE_A, CONTENT_A)


def test_a_record_against_different_case_content_is_refused(tmp_path):
    store = CaseSeedRecordStore(tmp_path)
    store.append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_000, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_A,
    )
    with pytest.raises(RuntimeError, match="inputs differ"):
        store.load(CASE_A, CONTENT_B)


def test_a_record_under_a_different_global_plan_is_refused(tmp_path):
    CaseSeedRecordStore(tmp_path, plan_digest="plan-1").append(
        CASE_A,
        PerSeedStatusEntry(2_100_000_000, SeedStatus.COMPLETED_NO_CANDIDATE),
        CONTENT_A,
    )
    with pytest.raises(RuntimeError, match="global science plan"):
        CaseSeedRecordStore(tmp_path, plan_digest="plan-2").load(CASE_A, CONTENT_A)


# -----------------------------------------------------------------------
# Atomic case-record write
# -----------------------------------------------------------------------

def test_case_record_writes_atomically_and_round_trips(tmp_path):
    record = _record(CASE_A)
    digest = write_case_record(record, tmp_path)
    assert digest == record.scientific_digest()
    payload = load_case_record_payload(tmp_path, CASE_A)
    assert payload["case_id"] == CASE_A
    assert payload == json.loads(record.to_canonical_json())
    assert not list((tmp_path / "records").glob("*.tmp"))


def test_rewriting_a_completed_case_record_is_refused(tmp_path):
    write_case_record(_record(CASE_A), tmp_path)
    with pytest.raises(CaseRecordExists):
        write_case_record(_record(CASE_A), tmp_path)


def test_provenance_is_a_separate_append_only_file(tmp_path):
    record = _record(CASE_A)
    write_case_record(record, tmp_path)
    for i in range(2):
        append_provenance(
            ProvenanceSidecar(
                case_id=CASE_A,
                scientific_digest=record.scientific_digest(),
                started_utc=f"2026-08-15T0{i}:00:00Z",
                finished_utc=f"2026-08-15T0{i}:01:00Z",
                wall_seconds=60.0,
                host_platform="test",
                commit="deadbeef",
            ),
            tmp_path,
        )
    lines = (tmp_path / "provenance" / "case_provenance.jsonl").read_text().splitlines()
    assert len(lines) == 2
    # The scientific record carries no timestamp, host, or commit.
    payload = load_case_record_payload(tmp_path, CASE_A)
    flat = json.dumps(payload)
    assert "2026-08-15T0" not in flat
    assert "host_platform" not in flat
    assert "deadbeef" not in flat


# -----------------------------------------------------------------------
# Resume
# -----------------------------------------------------------------------

def test_resume_skips_completed_cases_in_manifest_order(tmp_path):
    write_case_record(_record(CASE_B), tmp_path)
    plan = resume_plan(tmp_path, [CASE_A, CASE_B, "PB|development|F01|r002"])
    assert plan.already_complete == (CASE_B,)
    assert plan.to_execute == (CASE_A, "PB|development|F01|r002")
    assert plan.requested == (CASE_A, CASE_B, "PB|development|F01|r002")


def test_resume_is_deterministic_across_invocations(tmp_path):
    write_case_record(_record(CASE_A), tmp_path)
    requested = [CASE_B, CASE_A, "PB|development|F01|r002"]
    first = resume_plan(tmp_path, requested).to_dict()
    second = resume_plan(tmp_path, requested).to_dict()
    assert first == second
    assert first["to_execute"] == [CASE_B, "PB|development|F01|r002"]


def test_a_legacy_record_is_refused_rather_than_counted_as_complete(tmp_path):
    """The schema bump must actually be enforced on the read path.

    A 1.0.0 record was scored under the superseded six-rung Gate 8. Counting it
    as complete would make resume skip that case permanently, leaving the old
    verdict standing under the amended rules.
    """
    from muru.paper_benchmark.rc5_store import SchemaGenerationRefused

    record = _record(CASE_A)
    write_case_record(record, tmp_path)
    path = tmp_path / "records" / "PB_development_F01_r000.json"
    payload = json.loads(path.read_text())
    payload["schema_version"] = "muru-rc3-case-record-1.0.0"
    path.write_text(json.dumps(payload))

    with pytest.raises(SchemaGenerationRefused, match="legacy"):
        completed_case_ids(tmp_path)
    with pytest.raises(SchemaGenerationRefused, match="legacy"):
        load_case_record_payload(tmp_path, CASE_A)
    with pytest.raises(SchemaGenerationRefused):
        resume_plan(tmp_path, [CASE_A])


def test_an_unversioned_record_is_refused(tmp_path):
    from muru.paper_benchmark.rc3_record import SchemaVersionError

    write_case_record(_record(CASE_A), tmp_path)
    path = tmp_path / "records" / "PB_development_F01_r000.json"
    payload = json.loads(path.read_text())
    del payload["schema_version"]
    path.write_text(json.dumps(payload))
    with pytest.raises(SchemaVersionError):
        completed_case_ids(tmp_path)


def test_a_record_cannot_be_written_under_a_foreign_schema_version():
    from muru.paper_benchmark.rc3_record import SchemaVersionError

    with pytest.raises(SchemaVersionError, match="may only be written"):
        _record(CASE_A, schema_version="muru-rc3-case-record-1.0.0")


def test_a_hard_gate_may_not_carry_not_applicable():
    from muru.paper_benchmark.structural_acceptance import FalsificationRung

    results = {r: FalsificationResult.PASS for r in REQUIRED_HARD_GATES}
    results[FalsificationRung.F1_REPRODUCIBILITY] = FalsificationResult.NOT_APPLICABLE
    with pytest.raises(ValueError, match="only PASS or FAIL"):
        _record(CASE_A, falsification_results=results)


def test_f9_calibration_status_cannot_self_declare_proven():
    with pytest.raises(ValueError, match="NOT_PROVEN_FOR_HARD_GATE"):
        _record(CASE_A, f9_acceptance_calibration_status="PROVEN_FOR_HARD_GATE")


def test_completed_case_ids_reads_the_recorded_id_not_the_filename(tmp_path):
    write_case_record(_record(CASE_A), tmp_path)
    assert completed_case_ids(tmp_path) == frozenset({CASE_A})
    assert completed_case_ids(tmp_path / "nowhere") == frozenset()
