"""The RC5 production runner: composition, authorisation, resume, provenance.

Every case here is synthetic (``tests/rc5_synthetic.py``).  No benchmark
partition is executed and no PySR search runs.
"""
from __future__ import annotations

import ast
import json

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.governance import ImplementationLock
from muru.paper_benchmark.rc5_runner import (
    AUTHORISED_PARTITIONS,
    PartitionNotAuthorised,
    assert_partition_authorised,
    execute_case,
    materialize_case,
    run_partition,
)
from muru.paper_benchmark.rc5_seeds import case_search_seeds
from muru.paper_benchmark.rc5_store import CaseSeedRecordStore, completed_case_ids
from muru.paper_benchmark.structural_acceptance import (
    REQUIRED_HARD_GATES,
    AcceptanceStatus,
)

from rc5_synthetic import (
    ENGINE_VERSIONS,
    NULL_THRESHOLD,
    StubBackend,
    synthetic_content,
)

DEV_CASE = "PB|development|F01|r000"


def _execute(case_id: str = DEV_CASE, backend=None, **kwargs):
    return execute_case(
        content=synthetic_content(case_id),
        a1_status=kwargs.pop("a1_status", CaseAdequacyStatus.M0_NOT_REJECTED),
        backend=backend or StubBackend(),
        null_threshold=NULL_THRESHOLD,
        engine_versions=ENGINE_VERSIONS,
        **kwargs,
    )


# =======================================================================
# Authorisation
# =======================================================================

def test_only_development_is_authorised():
    assert AUTHORISED_PARTITIONS == frozenset({"development"})
    assert_partition_authorised("development")
    for refused in ("held_out", "challenge"):
        with pytest.raises(PartitionNotAuthorised, match="Development partition only"):
            assert_partition_authorised(refused)
    with pytest.raises(ValueError, match="unknown partition"):
        assert_partition_authorised("confirmation")


def test_materialising_an_unauthorised_partition_is_refused():
    with pytest.raises(PartitionNotAuthorised):
        materialize_case("PB|held_out|F01|r000")
    with pytest.raises(PartitionNotAuthorised):
        materialize_case("PB|challenge|F01|r000")


def test_run_partition_refuses_an_unauthorised_partition_before_anything_else():
    with pytest.raises(PartitionNotAuthorised):
        run_partition(
            "held_out", [], {}, StubBackend(), NULL_THRESHOLD, ENGINE_VERSIONS,
            output_root="/tmp/nowhere", run_commit="abc",
        )


# =======================================================================
# Composition: one case, end to end
# =======================================================================

def test_a_clean_case_runs_end_to_end_and_produces_a_record():
    record = _execute()
    assert record.case_id == DEV_CASE
    assert record.partition_label == "development"
    assert record.discovered_expression_string == "mass"
    # A3.5 section 7.1's corrected worked example: argmax(score) selects
    # complexity 4 on this front, not 13 and not the first row.
    assert record.complexity == 4
    assert record.selection_count == 30
    assert record.selection_denominator == 30
    assert set(record.falsification_results) == set(REQUIRED_HARD_GATES)
    assert record.null_threshold_digest
    assert record.scientific_digest()


def test_all_thirty_frozen_seeds_are_used_in_order():
    backend = StubBackend()
    record = _execute(backend=backend)
    expected = list(case_search_seeds(DEV_CASE))
    assert backend.seen == expected
    assert list(record.seeds_used) == expected
    assert len(record.per_seed_status) == 30


def test_candidate_test_r2_is_computed_once_and_feeds_both_consumers():
    """A3.5 obligation 13, verified on the produced record.

    The ceiling estimator consumes the value as its ``candidate_r2``, and Gate
    7's waiver floor reads the record's ``candidate_test_r2``.  Both must be
    the same number.
    """
    record = _execute()
    from muru.paper_benchmark.rc3_ceiling import estimate_ceiling
    from muru.paper_benchmark.rc5_estimate import fit_case_scalars

    content = synthetic_content(DEV_CASE)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    ceiling = estimate_ceiling(content.compounds, scalars.g, record.candidate_test_r2)
    assert ceiling.candidate_r2 == record.candidate_test_r2
    assert ceiling.ceiling_r2 == record.ceiling_r2
    assert ceiling.ceiling_fraction == record.ceiling_fraction


def test_the_representatives_own_values_reach_the_record_verbatim():
    record = _execute()
    # The stub's argmax(score) row is complexity 4, expression "mass".
    assert record.complexity == 4
    assert record.discovered_expression_string == "mass"
    assert record.effective_support == frozenset({"mass"})


def test_one_seed_execution_failure_makes_the_whole_case_unevaluable():
    """A3.5 section 8.2: no replacement seed, no 29/30 denominator."""
    seeds = case_search_seeds(DEV_CASE)
    backend = StubBackend(seed_behaviour={seeds[17]: "raise"})
    record = _execute(backend=backend)
    assert record.acceptance_status is AcceptanceStatus.UNEVALUABLE
    assert record.selection_count == 0
    assert record.selection_denominator == 30
    assert record.discovered_expression_string is None
    statuses = [e.status for e in record.per_seed_status]
    assert statuses.count(SeedStatus.EXECUTION_FAILURE) == 1
    assert record.f9_stress_test_result is None


def test_a_missing_score_column_is_an_execution_failure_and_poisons_the_case():
    seeds = case_search_seeds(DEV_CASE)
    backend = StubBackend(seed_behaviour={seeds[0]: "no_score"})
    record = _execute(backend=backend)
    assert record.acceptance_status is AcceptanceStatus.UNEVALUABLE
    assert record.per_seed_status[0].status is SeedStatus.EXECUTION_FAILURE


def test_barren_seeds_depress_the_fraction_without_poisoning_the_case():
    seeds = case_search_seeds(DEV_CASE)
    backend = StubBackend(seed_behaviour={s: "empty" for s in seeds[:6]})
    record = _execute(backend=backend)
    assert record.acceptance_status is not AcceptanceStatus.UNEVALUABLE
    assert record.selection_count == 24
    assert record.selection_denominator == 30


def test_every_seed_barren_yields_unevaluable_at_no_candidate():
    seeds = case_search_seeds(DEV_CASE)
    backend = StubBackend(seed_behaviour={s: "empty" for s in seeds})
    record = _execute(backend=backend)
    assert record.acceptance_status is AcceptanceStatus.UNEVALUABLE
    assert record.acceptance_gate_reached == "no_candidate"
    assert record.selection_count == 0


def test_a1_rejection_short_circuits_before_any_gate():
    record = _execute(a1_status=CaseAdequacyStatus.M0_REJECTED_M1)
    assert record.acceptance_status is AcceptanceStatus.REJECTED_A1_INADEQUATE
    assert record.acceptance_gate_reached == "a1_adequacy"


def test_the_f9_secondary_is_recorded_exactly_when_gate8_was_reached():
    record = _execute()
    reached = record.acceptance_gate_reached in {"falsification", "all_passed"}
    assert (record.f9_stress_test_result is not None) is reached
    assert (record.f9_stress_test_metric is not None) is reached
    if reached:
        assert "F9_ENERGY_SUBSET" not in {
            r.value for r in record.falsification_results
        }


# =======================================================================
# The runner defines no science of its own
# =======================================================================

def test_the_runner_declares_no_scientific_constant():
    import muru.paper_benchmark.rc5_runner as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    module_level_numbers = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
                module_level_numbers.append(value.value)
    assert not module_level_numbers, (
        f"the runner declares module-level numeric constants {module_level_numbers}; "
        f"every scientific number must live in the module that owns it"
    )


def test_the_runner_imports_its_thresholds_rather_than_restating_them():
    import muru.paper_benchmark.rc5_runner as module

    source = open(module.__file__, encoding="utf-8").read()
    for restated in ("0.80", "0.05", "0.005", "20 / 30", "0.70", "45.0", "2_100_000_000"):
        assert restated not in source, f"the runner restates {restated}"


def test_the_runner_never_reaches_the_permissive_g3_path():
    import muru.paper_benchmark.rc5_runner as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
        elif isinstance(node, ast.Import):
            modules |= {a.name for a in node.names}
    assert not any(m.endswith("analysis") for m in modules)
    assert not any(m.endswith("discovery.engine") for m in modules)


def test_the_a1_status_is_required_and_never_derived():
    import inspect

    params = inspect.signature(execute_case).parameters
    assert params["a1_status"].default is inspect.Parameter.empty

    import muru.paper_benchmark.rc5_runner as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "decide_case_adequacy" not in names
    assert "evaluate_contrast" not in names


# =======================================================================
# Resume, atomicity, provenance
# =======================================================================

def _run(tmp_path, case_ids, backend=None):
    return run_partition(
        "development",
        case_ids,
        {c: CaseAdequacyStatus.M0_NOT_REJECTED for c in case_ids},
        backend or StubBackend(),
        NULL_THRESHOLD,
        ENGINE_VERSIONS,
        output_root=tmp_path,
        run_commit="abc123",
    )


def test_a_completed_case_is_never_re_executed(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)

    first = _run(tmp_path, [DEV_CASE])
    assert first["executed"] == [DEV_CASE]
    assert completed_case_ids(tmp_path) == frozenset({DEV_CASE})

    second = _run(tmp_path, [DEV_CASE])
    assert second["executed"] == []
    assert second["already_complete"] == [DEV_CASE]


def test_resume_is_deterministic_in_manifest_order(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    cases = [DEV_CASE, "PB|development|F01|r001", "PB|development|F01|r002"]

    _run(tmp_path, cases[:1])
    resumed = _run(tmp_path, cases)
    assert resumed["already_complete"] == [DEV_CASE]
    assert resumed["executed"] == cases[1:]


def test_records_are_written_atomically_and_provenance_stays_separate(
    tmp_path, monkeypatch
):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    _run(tmp_path, [DEV_CASE])

    assert not list((tmp_path / "records").glob("*.tmp"))
    payload = json.loads(
        (tmp_path / "records" / "PB_development_F01_r000.json").read_text()
    )
    flat = json.dumps(payload)
    assert "started_utc" not in flat
    assert "host_platform" not in flat
    assert "abc123" not in flat

    provenance = (tmp_path / "provenance" / "case_provenance.jsonl").read_text()
    assert "abc123" in provenance
    assert payload["case_id"] in provenance


def test_per_seed_records_are_appended_for_resume(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    _run(tmp_path, [DEV_CASE])

    store = CaseSeedRecordStore(tmp_path / "seed_records")
    loaded = store.load(DEV_CASE, "s" * 64)
    assert set(loaded) == set(case_search_seeds(DEV_CASE))


def test_a_case_without_an_a1_verdict_is_refused(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    with pytest.raises(ValueError, match="no A1 adequacy status"):
        run_partition(
            "development", [DEV_CASE], {}, StubBackend(), NULL_THRESHOLD,
            ENGINE_VERSIONS, output_root=tmp_path, run_commit="abc123",
        )


# =======================================================================
# Preconditions
# =======================================================================

def test_preconditions_refuse_an_unauthorised_partition_before_reading_artifacts(
    tmp_path,
):
    from muru.paper_benchmark.rc5_runner import check_preconditions

    with pytest.raises(PartitionNotAuthorised):
        check_preconditions(
            "held_out", tmp_path, ImplementationLock.pending(), {}, {}
        )
    # Nothing was read: the directory is still empty.
    assert not list(tmp_path.iterdir())
