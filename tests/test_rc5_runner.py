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
    FalsificationResult,
)

from rc5_synthetic import (
    ENGINE_VERSIONS,
    NULL_THRESHOLD,
    StubBackend,
    synthetic_content,
)

DEV_CASE = "PB|development|F01|r000"


def _outcome(case_id: str = DEV_CASE, backend=None, **kwargs):
    return execute_case(
        content=synthetic_content(case_id),
        a1_status=kwargs.pop("a1_status", CaseAdequacyStatus.M0_NOT_REJECTED),
        backend=backend or StubBackend(),
        null_threshold=NULL_THRESHOLD,
        engine_versions=ENGINE_VERSIONS,
        **kwargs,
    )


def _execute(case_id: str = DEV_CASE, backend=None, **kwargs):
    return _outcome(case_id, backend, **kwargs).record


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


def test_run_partition_refuses_an_unauthorised_partition_before_anything_else(tmp_path):
    with pytest.raises(PartitionNotAuthorised):
        run_partition(
            "held_out", {}, {}, {}, StubBackend(), NULL_THRESHOLD, ENGINE_VERSIONS,
            artifact_dir=tmp_path, output_root=tmp_path,
            lock=ImplementationLock.pending(), run_commit="abc",
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
    assert backend.seen[:30] == expected
    assert list(record.seeds_used) == expected
    assert len(record.per_seed_status) == 30


def test_f1_replays_the_same_thirty_seeds_verbatim():
    """A3.5 section 6.1: universal scope, no sampling, identity perturbation.

    "F1 runs for every case reaching Gate 8 ... one full 30-seed re-execution
    per Gate-8-reaching case", with "its seeds reused verbatim and its
    perturbation the identity".  So a Gate-8-reaching case drives the backend
    exactly 60 times: 30 to search, 30 to replay the same seeds in the same
    order.
    """
    backend = StubBackend()
    record = _execute(backend=backend)
    expected = list(case_search_seeds(DEV_CASE))
    assert record.acceptance_gate_reached in {"falsification", "all_passed"}
    assert len(backend.seen) == 60
    assert backend.seen[:30] == expected
    assert backend.seen[30:] == expected


def test_a_deterministic_backend_passes_f1_and_reaches_acceptance():
    """Without a real re-execution driver F1 would always FAIL, making
    STRUCTURAL_ACCEPTED unreachable for every case."""
    from muru.paper_benchmark.structural_acceptance import FalsificationRung

    record = _execute()
    assert (
        record.falsification_results[FalsificationRung.F1_REPRODUCIBILITY]
        is FalsificationResult.PASS
    )
    assert record.acceptance_status is AcceptanceStatus.STRUCTURAL_ACCEPTED


def test_a_non_deterministic_backend_fails_f1():
    """The replay must be able to disagree, or F1 measures nothing."""
    from muru.paper_benchmark.structural_acceptance import FalsificationRung

    class _Drifting(StubBackend):
        def __init__(self):
            super().__init__()
            self._calls = 0

        def search(self, design, seed):
            self._calls += 1
            if self._calls > 30:      # the replay finds a different form
                self.expressions = ("descriptor2", "descriptor2", "mass * descriptor")
                self.columns = (2, 2, 0)
                self.scales = (1.0, 1.0, 0.004)
            return super().search(design, seed)

    record = _execute(backend=_Drifting())
    assert (
        record.falsification_results[FalsificationRung.F1_REPRODUCIBILITY]
        is FalsificationResult.FAIL
    )
    assert record.acceptance_status is AcceptanceStatus.REJECTED_FALSIFICATION


def test_the_f1_replay_writes_nothing_to_the_seed_store(tmp_path):
    """The replay is a determinism probe, not a second result.

    If it appended, every seed would gain a duplicate record -- the exact
    selective-retry violation A3.5 sections 8.2 and 12 forbid.
    """
    store = CaseSeedRecordStore(tmp_path)
    content = synthetic_content(DEV_CASE)
    execute_case(
        content=content,
        a1_status=CaseAdequacyStatus.M0_NOT_REJECTED,
        backend=StubBackend(),
        null_threshold=NULL_THRESHOLD,
        engine_versions=ENGINE_VERSIONS,
        seed_store=store,
    )
    assert len(store.recorded_seeds(DEV_CASE)) == 30
    loaded = store.load(DEV_CASE, content.content_hash)
    assert len(loaded) == 30


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

def _plan_and_manifest(tmp_path, case_ids):
    """A real plan and a real, verifying partition manifest.

    The manifest's case list is what run_partition executes, so the fixture
    narrows the plan's development inventory to the cases under test rather
    than passing a separate sequence -- which is the point of the change.
    """
    from muru.paper_benchmark.rc5_manifest import (
        EnvironmentIdentity,
        build_global_science_plan,
        build_partition_manifest,
        manifest_digest,
        resolve_tag_commit,
    )

    plan = build_global_science_plan(
        engineering_parent_commit=resolve_tag_commit(
            "engineering-rc4-2-1-integrity-closure"
        ),
        a3_5_tag="benchmark-content-freeze-a3-5",
        a3_5_tag_object="533777b73748e3c45dd1ecbda07098ba9837c587",
        a3_5_commit=resolve_tag_commit("benchmark-content-freeze-a3-5"),
        null_threshold=NULL_THRESHOLD,
        calibration_manifest_digest="c" * 64,
        code_provenance={"test": "fixture"},
    )
    plan = json.loads(json.dumps(plan))
    inventory = plan["case_inventory"]["development"]
    inventory["case_ids"] = list(case_ids)
    inventory["case_count"] = len(case_ids)
    plan["digest"] = manifest_digest(plan)

    environment = EnvironmentIdentity(
        platform="TestOS", machine="arm64", python_version="3.13.12",
        python_implementation="CPython", environment_lock_digest="d" * 64,
    )
    manifest = build_partition_manifest(
        plan, "development", environment, str(tmp_path), "abc123", True
    )
    return plan, manifest


def _artifact_dir(tmp_path):
    from muru.paper_benchmark.artifacts import build_partition

    root = tmp_path / "artifacts"
    build_partition("development", root)
    return root


def _run(tmp_path, case_ids, backend=None):
    plan, manifest = _plan_and_manifest(tmp_path, case_ids)
    return run_partition(
        "development",
        plan,
        manifest,
        {c: CaseAdequacyStatus.M0_NOT_REJECTED for c in case_ids},
        backend or StubBackend(),
        NULL_THRESHOLD,
        ENGINE_VERSIONS,
        artifact_dir=_artifact_dir(tmp_path),
        output_root=tmp_path / "out",
        lock=ImplementationLock.locked("abc", "sev", "gram", "pysr"),
        run_commit="abc123",
    )


def test_a_completed_case_is_never_re_executed(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)

    first = _run(tmp_path, [DEV_CASE])
    assert first["executed"] == [DEV_CASE]
    assert completed_case_ids(tmp_path / "out") == frozenset({DEV_CASE})

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

    assert not list((tmp_path / "out" / "records").glob("*.tmp"))
    payload = json.loads(
        (tmp_path / "out" / "records" / "PB_development_F01_r000.json").read_text()
    )
    flat = json.dumps(payload)
    assert "started_utc" not in flat
    assert "host_platform" not in flat
    assert "abc123" not in flat

    provenance = (tmp_path / "out" / "provenance" / "case_provenance.jsonl").read_text()
    assert "abc123" in provenance
    assert payload["case_id"] in provenance


def test_per_seed_records_are_appended_for_resume(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    _run(tmp_path, [DEV_CASE])

    store = CaseSeedRecordStore(tmp_path / "out" / "seed_records")
    loaded = store.load(DEV_CASE, "s" * 64)
    assert set(loaded) == set(case_search_seeds(DEV_CASE))


def test_a_case_without_an_a1_verdict_is_refused(tmp_path, monkeypatch):
    import muru.paper_benchmark.rc5_runner as runner

    monkeypatch.setattr(runner, "materialize_case", synthetic_content)
    plan, manifest = _plan_and_manifest(tmp_path, [DEV_CASE])
    with pytest.raises(ValueError, match="no A1 adequacy status"):
        run_partition(
            "development", plan, manifest, {}, StubBackend(), NULL_THRESHOLD,
            ENGINE_VERSIONS, artifact_dir=_artifact_dir(tmp_path),
            output_root=tmp_path / "out",
            lock=ImplementationLock.locked("a", "b", "c", "d"),
            run_commit="abc123",
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
