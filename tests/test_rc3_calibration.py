"""RC3 calibration runner: failure semantics, aggregation, thresholds, resume.

Every world statistic, seed result and curve here is constructed.  No test
executes a real search, and none reads a real outcome.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from muru.paper_benchmark.calibration_contract import (
    MAX_COMPLEXITY,
    MIN_VALID_WORLDS,
    N_CALIBRATION_WORLDS,
    N_SEEDS_PER_WORLD,
    QUANTILE_LEVEL,
    SEARCH_SETTINGS,
    CalibrationValidity,
    SeedResult,
    SeedStatus,
    all_world_ids,
    check_calibration_validity,
    compute_threshold_table,
    compute_world_null_statistic,
    count_failed_worlds,
)
from muru.paper_benchmark.rc3_calibration_runner import (
    ENGINEERING_SMOKE_MARKER,
    FROZEN_SETTINGS_DIGEST,
    PrefixMonotonicityViolation,
    SearchOutcome,
    SeedRecordStore,
    SeedTimeout,
    check_prefix_monotonicity,
    run_calibration,
    run_seed,
    run_world,
    search_settings_digest,
)
from muru.paper_benchmark.rc3_calibration_worlds import (
    ADMITTED_CONSTRUCTIONS,
    CALIBRATION_SCAFFOLD_COUNTS,
    EXPECTED_SPLIT_COUNTS,
    ExcludedConstructionError,
    build_world,
    iter_world_ids,
)


# -----------------------------------------------------------------------
# Constructed backends
# -----------------------------------------------------------------------

class _FrozenSettingsBackend:
    """Base for constructed backends.

    Declares the frozen search settings, because ``run_world`` and
    ``run_calibration`` now fail CLOSED: a backend that cannot say what it
    runs is refused rather than trusted.
    """

    @property
    def effective_settings(self):
        return dict(SEARCH_SETTINGS)


class FlatBackend(_FrozenSettingsBackend):
    """Returns a fixed curve for every seed."""

    def __init__(self, curve, n_candidates=5):
        self.curve = dict(curve)
        self.n_candidates = n_candidates
        self.calls = 0

    def search(self, world, seed):
        self.calls += 1
        return SearchOutcome(
            best_valid_r2_by_complexity=dict(self.curve),
            n_candidates=self.n_candidates,
        )


class RaisingBackend(_FrozenSettingsBackend):
    def __init__(self, exc):
        self.exc = exc
        self.calls = 0

    def search(self, world, seed):
        self.calls += 1
        raise self.exc


class NoCandidateBackend(_FrozenSettingsBackend):
    def search(self, world, seed):
        return SearchOutcome(best_valid_r2_by_complexity={}, n_candidates=0)


class MalformedBackend(_FrozenSettingsBackend):
    def search(self, world, seed):
        return {"not": "a SearchOutcome"}


def full_curve(value: float) -> dict[int, float]:
    return {c: value for c in range(1, MAX_COMPLEXITY + 1)}


def world_row(value: float) -> dict[int, float]:
    return {c: value for c in range(1, MAX_COMPLEXITY + 1)}


# -----------------------------------------------------------------------
# Per-seed status assignment
# -----------------------------------------------------------------------

def test_completed_with_candidates_status():
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, FlatBackend(full_curve(0.3), n_candidates=4))
    assert result.status == SeedStatus.COMPLETED_WITH_CANDIDATES
    assert result.best_valid_r2_by_complexity is not None


def test_completed_no_candidate_status():
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, NoCandidateBackend())
    assert result.status == SeedStatus.COMPLETED_NO_CANDIDATE
    assert result.best_valid_r2_by_complexity is None


@pytest.mark.parametrize("exc", [
    RuntimeError("crash"),
    MemoryError("OOM"),
    TimeoutError("timeout"),
    ValueError("malformed result"),
    SeedTimeout("budget exceeded"),
])
def test_every_exception_maps_to_execution_failure(exc):
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, RaisingBackend(exc))
    assert result.status == SeedStatus.EXECUTION_FAILURE
    assert result.error_message


@pytest.mark.parametrize("exc", [KeyboardInterrupt(), SystemExit()])
def test_operator_abort_propagates_and_is_not_recorded(exc, tmp_path):
    """Ctrl-C aborts the run; it must not poison the world.

    Recording an operator interrupt as EXECUTION_FAILURE would force that
    world's whole row to +1.0, and the no-retry rule would make it
    unrecoverable: six interrupts would irreversibly invalidate calibration.
    """
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    backend = RaisingBackend(exc)

    with pytest.raises(type(exc)):
        run_world(world, backend, store, seeds=[world.seeds[0]])

    # Nothing was written, so a resumed run simply re-executes the seed.
    assert store.load(world.world_id) == {}


def test_a_seed_that_outlives_its_budget_is_an_execution_failure():
    """The contract names timeout as an EXECUTION_FAILURE source."""
    import time

    class SlowBackend:
        def search(self, world, seed):
            time.sleep(3.0)
            return SearchOutcome(best_valid_r2_by_complexity={1: 0.5}, n_candidates=1)

    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, SlowBackend(), timeout_seconds=0.25)
    assert result.status == SeedStatus.EXECUTION_FAILURE
    assert "SeedTimeout" in result.error_message


def test_malformed_backend_result_is_execution_failure():
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, MalformedBackend())
    assert result.status == SeedStatus.EXECUTION_FAILURE
    assert "malformed" in result.error_message


def test_status_is_not_determined_by_finiteness():
    """A completed search whose every value is -inf is COMPLETED, not a failure.

    This is the case where ``np.isfinite`` would give the wrong answer.
    """
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, FlatBackend(full_curve(float("-inf")), n_candidates=3))
    assert result.status == SeedStatus.COMPLETED_WITH_CANDIDATES
    assert all(
        not np.isfinite(v) for v in result.best_valid_r2_by_complexity.values()
    )


def test_a_crash_that_returns_finite_looking_nothing_is_still_a_failure():
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, RaisingBackend(RuntimeError("julia died")))
    assert result.status == SeedStatus.EXECUTION_FAILURE
    assert result.best_valid_r2_by_complexity is None


# -----------------------------------------------------------------------
# Prefix monotonicity canary
# -----------------------------------------------------------------------

def test_sparse_pareto_front_is_not_a_violation():
    """A Pareto front does not populate every complexity.  That is normal."""
    check_prefix_monotonicity({1: -0.01, 4: 0.007, 6: 0.005, 8: float("-inf")})


def test_all_minus_inf_is_not_a_violation():
    check_prefix_monotonicity(full_curve(float("-inf")))


def test_nan_is_a_violation():
    with pytest.raises(PrefixMonotonicityViolation, match="NaN"):
        check_prefix_monotonicity({1: 0.5, 3: float("nan")})


def test_positive_infinity_is_a_violation():
    with pytest.raises(PrefixMonotonicityViolation, match=r"\+inf"):
        check_prefix_monotonicity({1: 0.5, 3: float("inf")})


@pytest.mark.parametrize("bad", [0, -1, 21, 100])
def test_out_of_range_complexity_is_a_violation(bad):
    with pytest.raises(PrefixMonotonicityViolation, match="complexity"):
        check_prefix_monotonicity({bad: 0.5})


def test_prefix_monotonicity_violation_becomes_execution_failure():
    world = build_world("target_permuted_across_compounds", 0)
    result = run_seed(world, 1, FlatBackend({1: 0.5, 3: float("nan")}))
    assert result.status == SeedStatus.EXECUTION_FAILURE
    assert "PrefixMonotonicityViolation" in result.error_message


# -----------------------------------------------------------------------
# World aggregation
# -----------------------------------------------------------------------

def make_seed_results(n_failures: int = 0, value: float = 0.2) -> list[SeedResult]:
    results = []
    for i in range(N_SEEDS_PER_WORLD):
        if i < n_failures:
            results.append(SeedResult(seed=i, status=SeedStatus.EXECUTION_FAILURE))
        else:
            results.append(SeedResult(
                seed=i,
                status=SeedStatus.COMPLETED_WITH_CANDIDATES,
                best_valid_r2_by_complexity=full_curve(value),
            ))
    return results


def test_one_execution_failure_forces_the_whole_world_row_to_plus_one():
    clean = compute_world_null_statistic(make_seed_results(0, value=0.2))
    assert all(v == pytest.approx(0.2) for v in clean.values())

    poisoned = compute_world_null_statistic(make_seed_results(1, value=0.2))
    assert set(poisoned) == set(range(1, MAX_COMPLEXITY + 1))
    assert all(v == 1.0 for v in poisoned.values())


def test_one_failure_out_of_thirty_is_enough():
    for n in (1, 2, 15, 30):
        stat = compute_world_null_statistic(make_seed_results(n))
        assert all(v == 1.0 for v in stat.values()), n


def test_completed_no_candidate_contributes_minus_inf_not_failure():
    results = [
        SeedResult(seed=i, status=SeedStatus.COMPLETED_NO_CANDIDATE)
        for i in range(N_SEEDS_PER_WORLD)
    ]
    stat = compute_world_null_statistic(results)
    assert all(v == float("-inf") for v in stat.values())
    assert count_failed_worlds({"w": results}) == 0


def test_a_failure_row_raises_the_threshold_it_can_never_lower_it():
    clean = {f"w{i:03d}": world_row(0.2) for i in range(N_CALIBRATION_WORLDS)}
    baseline = compute_threshold_table(clean)

    poisoned = dict(clean)
    poisoned["w000"] = world_row(1.0)
    raised = compute_threshold_table(poisoned)

    assert all(raised[c] >= baseline[c] for c in range(1, MAX_COMPLEXITY + 1))


# -----------------------------------------------------------------------
# Calibration validity, both sides of the 95/100 boundary
# -----------------------------------------------------------------------

def make_world_results(n_failed_worlds: int) -> dict[str, list[SeedResult]]:
    world_ids = all_world_ids()
    return {
        wid: make_seed_results(1 if i < n_failed_worlds else 0)
        for i, wid in enumerate(world_ids)
    }


def test_min_valid_worlds_is_95_of_100():
    assert MIN_VALID_WORLDS == 95
    assert N_CALIBRATION_WORLDS == 100


@pytest.mark.parametrize("n_failed", [0, 1, 4, 5])
def test_at_most_five_failed_worlds_is_valid(n_failed):
    results = make_world_results(n_failed)
    assert count_failed_worlds(results) == n_failed
    assert check_calibration_validity(results) == CalibrationValidity.VALID


@pytest.mark.parametrize("n_failed", [6, 7, 50, 100])
def test_more_than_five_failed_worlds_is_calibration_invalid(n_failed):
    results = make_world_results(n_failed)
    assert count_failed_worlds(results) == n_failed
    assert check_calibration_validity(results) == CalibrationValidity.CALIBRATION_INVALID


def test_the_boundary_is_exactly_at_five_versus_six():
    assert check_calibration_validity(make_world_results(5)) == CalibrationValidity.VALID
    assert (
        check_calibration_validity(make_world_results(6))
        == CalibrationValidity.CALIBRATION_INVALID
    )


def test_a_short_world_set_is_invalid_not_silently_scored():
    partial = dict(list(make_world_results(0).items())[:99])
    assert check_calibration_validity(partial) == CalibrationValidity.CALIBRATION_INVALID


# -----------------------------------------------------------------------
# Threshold construction
# -----------------------------------------------------------------------

def test_quantile_matches_the_frozen_linear_formula():
    """Q95 of 100 ascending values is x[94] + 0.05 * (x[95] - x[94])."""
    values = [i / 100.0 for i in range(100)]
    stats = {
        f"w{i:03d}": {c: values[i] for c in range(1, MAX_COMPLEXITY + 1)}
        for i in range(100)
    }
    table = compute_threshold_table(stats)
    ascending = sorted(values)
    expected = ascending[94] + 0.05 * (ascending[95] - ascending[94])
    assert expected == pytest.approx(np.quantile(values, QUANTILE_LEVEL, method="linear"))
    for c in range(1, MAX_COMPLEXITY + 1):
        assert table[c] == pytest.approx(expected)


def test_cumulative_max_enforces_non_decreasing_thresholds():
    """A deliberately decreasing per-complexity quantile must be flattened up."""
    descending = {c: 1.0 - 0.01 * c for c in range(1, MAX_COMPLEXITY + 1)}
    stats = {f"w{i:03d}": dict(descending) for i in range(100)}
    table = compute_threshold_table(stats)

    values = [table[c] for c in range(1, MAX_COMPLEXITY + 1)]
    assert values == sorted(values)
    assert all(v == pytest.approx(descending[1]) for v in values)


def test_thresholds_are_non_decreasing_on_a_random_constructed_array():
    rng = np.random.default_rng(11)
    stats = {
        f"w{i:03d}": {
            c: float(rng.normal(0, 1)) for c in range(1, MAX_COMPLEXITY + 1)
        }
        for i in range(100)
    }
    table = compute_threshold_table(stats)
    values = [table[c] for c in range(1, MAX_COMPLEXITY + 1)]
    assert values == sorted(values)


def test_threshold_table_requires_exactly_100_worlds():
    stats = {f"w{i:03d}": world_row(0.1) for i in range(99)}
    with pytest.raises(ValueError, match="expected 100"):
        compute_threshold_table(stats)


# -----------------------------------------------------------------------
# World construction
# -----------------------------------------------------------------------

def test_hundred_unique_worlds_with_the_frozen_allocation():
    ids = iter_world_ids()
    assert len(ids) == 100
    assert len(set(ids)) == 100
    for construction, expected in (
        ("target_permuted_across_compounds", 34),
        ("descriptors_permuted_across_compounds", 33),
        ("gaussian_targets_with_observed_variance", 33),
    ):
        assert sum(1 for i in ids if construction in i) == expected


def test_world_geometry_matches_the_contract():
    world = build_world("target_permuted_across_compounds", 0)
    assert len(world.compounds) == 180
    assert world.compounds["scaffold_id"].nunique() == 30
    assert world.design_matrix().shape == (180, 5)
    assert len(world.seeds) == N_SEEDS_PER_WORLD


def test_the_split_is_the_a3_2_sixty_twenty_twenty():
    """A3.2 Decision 2: 18/6/6 scaffolds, 108/36/36 compounds."""
    world = build_world("target_permuted_across_compounds", 0)
    counts = world.compounds["split"].value_counts().to_dict()
    assert counts == EXPECTED_SPLIT_COUNTS == {
        "train": 108, "validation": 36, "test": 36,
    }
    assert counts["train"] / 180 == pytest.approx(0.60)
    assert counts["validation"] / 180 == pytest.approx(0.20)
    assert counts["test"] / 180 == pytest.approx(0.20)
    assert CALIBRATION_SCAFFOLD_COUNTS == {"train": 18, "validation": 6, "test": 6}


def test_splits_are_scaffold_disjoint():
    world = build_world("gaussian_targets_with_observed_variance", 0)
    by_scaffold = world.compounds.groupby("scaffold_id")["split"].nunique()
    assert set(by_scaffold.unique()) == {1}


def test_within_compound_energy_permutation_is_unconstructible():
    with pytest.raises(ExcludedConstructionError):
        build_world("within_compound_energy_permutation", 0)
    assert "within_compound_energy_permutation" not in ADMITTED_CONSTRUCTIONS


def test_unknown_construction_is_rejected():
    with pytest.raises(ValueError, match="unknown construction"):
        build_world("some_other_null", 0)


def test_world_construction_is_deterministic():
    a = build_world("descriptors_permuted_across_compounds", 7)
    b = build_world("descriptors_permuted_across_compounds", 7)
    assert np.array_equal(a.target, b.target)
    assert a.compounds.equals(b.compounds)
    assert a.seeds == b.seeds


# -----------------------------------------------------------------------
# Resumability
# -----------------------------------------------------------------------

def test_completed_seeds_are_not_re_executed_on_resume(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    seeds = list(world.seeds[:4])
    store = SeedRecordStore(tmp_path / "records")

    backend = FlatBackend(full_curve(0.3))
    first = run_world(world, backend, store, seeds=seeds)
    assert backend.calls == 4

    resumed_backend = FlatBackend(full_curve(0.9))
    second = run_world(world, resumed_backend, store, seeds=seeds)
    assert resumed_backend.calls == 0
    assert [r.status for r in second] == [r.status for r in first]
    assert second[0].best_valid_r2_by_complexity == first[0].best_valid_r2_by_complexity


def test_interruption_mid_world_resumes_without_redoing_work(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    seeds = list(world.seeds[:6])
    store = SeedRecordStore(tmp_path / "records")

    backend = FlatBackend(full_curve(0.25))
    run_world(world, backend, store, seeds=seeds[:3])
    assert backend.calls == 3

    run_world(world, backend, store, seeds=seeds)
    assert backend.calls == 6  # only the three new seeds ran


def test_a_truncated_final_record_is_discarded_not_trusted(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    backend = FlatBackend(full_curve(0.25))
    run_world(world, backend, store, seeds=list(world.seeds[:2]))

    path = store.path_for(world.world_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"world_id": "PB|NCAL", "seed": 99, "sta')

    loaded = store.load(world.world_id)
    assert set(loaded) == set(world.seeds[:2])


def test_execution_failures_are_not_retried_on_resume(tmp_path):
    """No selective retries: a failed seed stays failed."""
    world = build_world("target_permuted_across_compounds", 0)
    seeds = list(world.seeds[:3])
    store = SeedRecordStore(tmp_path / "records")

    run_world(world, RaisingBackend(RuntimeError("boom")), store, seeds=seeds)

    healthy = FlatBackend(full_curve(0.4))
    resumed = run_world(world, healthy, store, seeds=seeds)
    assert healthy.calls == 0
    assert all(r.status == SeedStatus.EXECUTION_FAILURE for r in resumed)


def test_records_are_written_incrementally(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    seen: list[int] = []

    def on_seed(world_id, result):
        # the record for this seed must already be on disk
        seen.append(len(store.load(world_id)))

    run_world(world, FlatBackend(full_curve(0.2)), store,
              seeds=list(world.seeds[:3]), on_seed=on_seed)
    assert seen == [1, 2, 3]


def test_minus_infinity_round_trips_through_the_store(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    curve = {1: 0.1, 5: float("-inf")}
    run_world(world, FlatBackend(curve), store, seeds=[world.seeds[0]])

    loaded = store.load(world.world_id)[world.seeds[0]]
    assert loaded.best_valid_r2_by_complexity == {1: 0.1, 5: float("-inf")}


# -----------------------------------------------------------------------
# Smoke quarantine
# -----------------------------------------------------------------------

def test_quarantined_store_marks_every_record(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "smoke", quarantined=True)
    run_world(world, FlatBackend(full_curve(0.2)), store, seeds=list(world.seeds[:2]))

    for line in store.path_for(world.world_id).read_text().splitlines():
        assert json.loads(line)["marker"] == ENGINEERING_SMOKE_MARKER


def test_a_scientific_store_refuses_to_read_smoke_records(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    smoke = SeedRecordStore(tmp_path / "shared", quarantined=True)
    run_world(world, FlatBackend(full_curve(0.2)), smoke, seeds=[world.seeds[0]])

    scientific = SeedRecordStore(tmp_path / "shared", quarantined=False)
    with pytest.raises(RuntimeError, match="engineering-smoke"):
        scientific.load(world.world_id)


def test_run_calibration_refuses_a_quarantined_store(tmp_path):
    store = SeedRecordStore(tmp_path / "smoke", quarantined=True)
    with pytest.raises(RuntimeError, match="quarantined"):
        run_calibration(FlatBackend(full_curve(0.2)), store, world_specs=[])


def test_run_calibration_refuses_a_reduced_iteration_backend(tmp_path):
    """Clearing the flag must not buy a pass: the settings are digested."""
    from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS
    from muru.paper_benchmark.rc3_calibration_runner import PySRBackend

    backend = PySRBackend(niterations_override=2, engineering_smoke=True)
    backend.engineering_smoke = False  # the flag is just an attribute
    assert backend.niterations == 2

    store = SeedRecordStore(tmp_path / "records")
    with pytest.raises(RuntimeError, match="non-frozen search settings"):
        run_calibration(backend, store, world_specs=ALL_SPECS)


def test_run_calibration_refuses_a_store_bound_to_other_settings(tmp_path):
    store = SeedRecordStore(tmp_path / "records", settings_digest="deadbeef")
    with pytest.raises(RuntimeError, match="non-frozen search settings"):
        run_calibration(FlatBackend(full_curve(0.2)), store, world_specs=ALL_SPECS)


def test_pysr_backend_refuses_niterations_override_outside_smoke():
    from muru.paper_benchmark.rc3_calibration_runner import PySRBackend

    with pytest.raises(ValueError, match="engineering smoke"):
        PySRBackend(niterations_override=2)


def test_pysr_backend_uses_the_frozen_niterations_by_default():
    from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS
    from muru.paper_benchmark.rc3_calibration_runner import PySRBackend

    backend = PySRBackend()
    assert backend.niterations == SEARCH_SETTINGS["niterations"] == 40
    assert search_settings_digest(backend.effective_settings) == FROZEN_SETTINGS_DIGEST


# -----------------------------------------------------------------------
# Record-store integrity
# -----------------------------------------------------------------------

def _append_raw(store, world_id, payload):
    with store.path_for(world_id).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _world_digest(world):
    return world.construction_digest()


def test_a_second_record_for_a_seed_is_rejected(tmp_path):
    """Appending one line must not un-poison a failed seed."""
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    seed = world.seeds[0]
    run_world(world, RaisingBackend(RuntimeError("boom")), store, seeds=[seed])
    assert store.load(world.world_id)[seed].status == SeedStatus.EXECUTION_FAILURE

    _append_raw(store, world.world_id, {
        "world_id": world.world_id, "seed": seed,
        "status": "COMPLETED_NO_CANDIDATE",
        "best_valid_r2_by_complexity": None, "error_message": "",
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
    })
    with pytest.raises(RuntimeError, match="duplicate record"):
        store.load(world.world_id)


def test_a_record_for_another_world_is_rejected(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    _append_raw(store, world.world_id, {
        "world_id": "PB|NCAL|somewhere_else|r000", "seed": 1,
        "status": "COMPLETED_NO_CANDIDATE",
        "best_valid_r2_by_complexity": None, "error_message": "",
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
    })
    with pytest.raises(RuntimeError, match="record for"):
        store.load(world.world_id)


def test_a_record_from_other_search_settings_is_rejected(tmp_path):
    """Deleting the smoke marker does not launder a reduced-budget record."""
    world = build_world("target_permuted_across_compounds", 0)
    smoke_digest = search_settings_digest({**SEARCH_SETTINGS, "niterations": 2})
    store = SeedRecordStore(tmp_path / "records")
    _append_raw(store, world.world_id, {
        "world_id": world.world_id, "seed": 1,
        "status": "COMPLETED_WITH_CANDIDATES",
        "best_valid_r2_by_complexity": {"1": 0.9}, "error_message": "",
        "search_settings_digest": smoke_digest,
    })
    with pytest.raises(RuntimeError, match="search settings"):
        store.load(world.world_id)


def test_every_record_carries_the_settings_digest(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    run_world(world, FlatBackend(full_curve(0.2)), store, seeds=[world.seeds[0]])
    line = json.loads(store.path_for(world.world_id).read_text().splitlines()[0])
    assert line["search_settings_digest"] == FROZEN_SETTINGS_DIGEST


# -----------------------------------------------------------------------
# Allocation and threshold-table guards
# -----------------------------------------------------------------------

ALL_SPECS = [
    (construction, index)
    for construction, count in [
        ("target_permuted_across_compounds", 34),
        ("descriptors_permuted_across_compounds", 33),
        ("gaussian_targets_with_observed_variance", 33),
    ]
    for index in range(count)
]



def test_a_lopsided_world_set_is_refused(tmp_path):
    """100 worlds of one construction must not build a VALID table."""
    store = SeedRecordStore(tmp_path / "records")
    specs = [("target_permuted_across_compounds", i) for i in range(34)]
    with pytest.raises(RuntimeError, match="allocation"):
        run_calibration(FlatBackend(full_curve(0.2)), store, world_specs=specs)


def test_a_short_world_set_is_refused(tmp_path):
    store = SeedRecordStore(tmp_path / "records")
    with pytest.raises(RuntimeError, match="allocation"):
        run_calibration(
            FlatBackend(full_curve(0.2)), store,
            world_specs=[("target_permuted_across_compounds", 0)],
        )


def test_build_world_rejects_an_index_outside_its_allocation():
    with pytest.raises(ValueError, match="outside"):
        build_world("descriptors_permuted_across_compounds", 33)
    with pytest.raises(ValueError, match="outside"):
        build_world("target_permuted_across_compounds", 34)
    build_world("target_permuted_across_compounds", 33)  # last valid


def test_build_all_worlds_no_longer_needs_an_acknowledgement():
    """A3.2 resolved the base target, so the RC3 gate is gone."""
    from muru.paper_benchmark.rc3_calibration_worlds import build_all_worlds

    worlds = build_all_worlds()
    assert len(worlds) == N_CALIBRATION_WORLDS
    assert len({w.world_id for w in worlds}) == N_CALIBRATION_WORLDS


def test_a_minus_inf_quantile_produces_a_nan_table_and_is_refused(tmp_path):
    """The failure mode that would otherwise ship a table of NaNs.

    np.quantile interpolates a + 0.05*(b - a). With a = -inf and b finite
    that is -inf + inf = NaN, and maximum.accumulate spreads it everywhere.
    Reachable in normal operation: COMPLETED_NO_CANDIDATE contributes -inf
    and a Pareto front often has nothing at complexity 1.
    """
    # 96 worlds at -inf, 4 finite: the 95th order statistic is -inf.
    stats = {}
    for i in range(96):
        stats[f"w{i:03d}"] = world_row(float("-inf"))
    for i in range(96, 100):
        stats[f"w{i:03d}"] = world_row(0.5)
    table = compute_threshold_table(stats)
    assert all(math.isnan(v) for v in table.values())

    from muru.paper_benchmark.rc3_calibration_runner import (
        _assert_threshold_table_defined,
    )
    with pytest.raises(RuntimeError, match="undefined at complexities"):
        _assert_threshold_table_defined(table, stats)


def test_a_defined_table_passes_the_guard():
    from muru.paper_benchmark.rc3_calibration_runner import (
        _assert_threshold_table_defined,
    )
    stats = {f"w{i:03d}": world_row(0.2) for i in range(100)}
    _assert_threshold_table_defined(compute_threshold_table(stats), stats)


# -----------------------------------------------------------------------
# Full-run wiring, with a constructed backend (no real search)
# -----------------------------------------------------------------------

def test_a_clean_hundred_world_run_is_valid_and_builds_a_table(tmp_path):
    """The VALID path, end to end, with no real search."""
    store = SeedRecordStore(tmp_path / "records")
    result = run_calibration(
        FlatBackend(full_curve(0.2)), store,
        world_specs=ALL_SPECS, compute_bootstrap=False,
    )
    assert result.validity == CalibrationValidity.VALID
    assert result.failed_worlds == 0
    assert result.clean_worlds == 100
    assert result.threshold_table_active()
    assert set(result.thresholds) == set(range(1, MAX_COMPLEXITY + 1))
    values = [result.thresholds[c] for c in range(1, MAX_COMPLEXITY + 1)]
    assert values == sorted(values)
    assert all(v == pytest.approx(0.2) for v in values)
    assert result.search_settings["niterations"] == 40


def test_six_failed_worlds_in_a_full_run_yield_no_table(tmp_path):
    class FailFirstSix(_FrozenSettingsBackend):
        def search(self, world, seed):
            index = ALL_SPECS.index((world.construction, world.index))
            if index < 6:
                raise RuntimeError("crash")
            return SearchOutcome(
                best_valid_r2_by_complexity=full_curve(0.2), n_candidates=3
            )

    store = SeedRecordStore(tmp_path / "records")
    result = run_calibration(
        FailFirstSix(), store, world_specs=ALL_SPECS, compute_bootstrap=False
    )
    assert result.failed_worlds == 6
    assert result.validity == CalibrationValidity.CALIBRATION_INVALID
    assert result.thresholds is None
    assert not result.threshold_table_active()
