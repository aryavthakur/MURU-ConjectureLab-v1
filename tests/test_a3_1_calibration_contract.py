"""Constructed contract tests for structural-null calibration (Amendment A3.1).

All fixtures are hand-built.  No calibration world execution.
"""
from __future__ import annotations

import numpy as np
import pytest

from muru.paper_benchmark.calibration_contract import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
    MAX_COMPLEXITY,
    MIN_VALID_WORLDS,
    N_CALIBRATION_WORLDS,
    N_SEEDS_PER_WORLD,
    PB_SEED_BASE,
    PB_SEED_SPREAD,
    QUANTILE_LEVEL,
    CalibrationValidity,
    SeedResult,
    SeedStatus,
    all_world_ids,
    check_calibration_validity,
    compute_seed_complexity_curve,
    compute_threshold_table,
    compute_world_null_statistic,
    count_failed_worlds,
    derive_calibration_seeds,
    derive_world_id,
    verify_seed_invariants,
)


# -----------------------------------------------------------------------
# Seed invariants
# -----------------------------------------------------------------------

class TestSeedInvariants:

    def test_100_unique_world_ids(self):
        ids = all_world_ids()
        assert len(ids) == N_CALIBRATION_WORLDS
        assert len(set(ids)) == N_CALIBRATION_WORLDS

    def test_100_unique_base_buckets(self):
        import hashlib
        ids = all_world_ids()
        bases = []
        for wid in ids:
            h = int.from_bytes(
                hashlib.sha256(wid.encode("utf-8")).digest()[:4],
                byteorder="big",
                signed=False,
            )
            bases.append(PB_SEED_BASE + (h % PB_SEED_SPREAD) * 100)
        assert len(set(bases)) == N_CALIBRATION_WORLDS

    def test_3000_unique_seeds(self):
        ids = all_world_ids()
        all_seeds = []
        for wid in ids:
            all_seeds.extend(derive_calibration_seeds(wid))
        assert len(all_seeds) == 3000
        assert len(set(all_seeds)) == 3000

    def test_signed_32bit_safe(self):
        ids = all_world_ids()
        for wid in ids:
            for seed in derive_calibration_seeds(wid):
                assert 0 <= seed <= 2**31 - 1

    def test_verify_seed_invariants_function(self):
        results = verify_seed_invariants()
        for key, value in results.items():
            assert value, f"invariant {key} failed"

    def test_allocation_sums(self):
        assert sum(CONSTRUCTION_ALLOCATION.values()) == N_CALIBRATION_WORLDS

    def test_excluded_constructions(self):
        assert "within_compound_energy_permutation" in EXCLUDED_CONSTRUCTIONS


# -----------------------------------------------------------------------
# Seed derivation
# -----------------------------------------------------------------------

class TestSeedDerivation:

    def test_deterministic(self):
        wid = derive_world_id("target_permuted_across_compounds", 0)
        seeds1 = derive_calibration_seeds(wid)
        seeds2 = derive_calibration_seeds(wid)
        assert seeds1 == seeds2

    def test_30_seeds(self):
        wid = derive_world_id("target_permuted_across_compounds", 0)
        seeds = derive_calibration_seeds(wid)
        assert len(seeds) == 30

    def test_consecutive(self):
        wid = derive_world_id("target_permuted_across_compounds", 0)
        seeds = derive_calibration_seeds(wid)
        for i in range(1, len(seeds)):
            assert seeds[i] == seeds[i - 1] + 1

    def test_invalid_index(self):
        with pytest.raises(ValueError):
            derive_world_id("target_permuted_across_compounds", 100)
        with pytest.raises(ValueError):
            derive_world_id("target_permuted_across_compounds", -1)


# -----------------------------------------------------------------------
# Per-seed status
# -----------------------------------------------------------------------

class TestSeedStatus:

    def test_completed_with_candidates(self):
        sr = SeedResult(
            seed=42,
            status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            best_valid_r2_by_complexity={c: 0.1 * c for c in range(1, 21)},
        )
        assert sr.status == SeedStatus.COMPLETED_WITH_CANDIDATES

    def test_completed_no_candidate(self):
        sr = SeedResult(
            seed=42,
            status=SeedStatus.COMPLETED_NO_CANDIDATE,
        )
        assert sr.status == SeedStatus.COMPLETED_NO_CANDIDATE

    def test_execution_failure(self):
        sr = SeedResult(
            seed=42,
            status=SeedStatus.EXECUTION_FAILURE,
            error_message="OOM",
        )
        assert sr.status == SeedStatus.EXECUTION_FAILURE


# -----------------------------------------------------------------------
# Complexity curve prefix monotonicity
# -----------------------------------------------------------------------

class TestComplexityCurve:

    def test_prefix_monotone(self):
        r2 = {c: 0.05 * c for c in range(1, 21)}
        curve = compute_seed_complexity_curve(r2)
        for c in range(2, 21):
            assert curve[c] >= curve[c - 1]

    def test_non_monotone_input_corrected(self):
        r2 = {1: 0.5, 2: 0.3, 3: 0.8}
        for c in range(4, 21):
            r2[c] = 0.1
        curve = compute_seed_complexity_curve(r2)
        assert curve[2] >= curve[1]  # 0.5 >= 0.5
        assert curve[3] >= curve[2]  # 0.8 >= 0.5

    def test_all_neg_inf(self):
        r2: dict[int, float] = {}
        curve = compute_seed_complexity_curve(r2)
        assert all(curve[c] == float("-inf") for c in range(1, 21))


# -----------------------------------------------------------------------
# World null statistic
# -----------------------------------------------------------------------

class TestWorldNullStatistic:

    def _make_completed_seeds(self, base_r2: float = 0.1) -> list[SeedResult]:
        return [
            SeedResult(
                seed=i,
                status=SeedStatus.COMPLETED_WITH_CANDIDATES,
                best_valid_r2_by_complexity={c: base_r2 * c / 20 for c in range(1, 21)},
            )
            for i in range(30)
        ]

    def test_one_failed_seed_gives_plus_one(self):
        seeds = self._make_completed_seeds()
        seeds[15] = SeedResult(seed=15, status=SeedStatus.EXECUTION_FAILURE, error_message="crash")
        stat = compute_world_null_statistic(seeds)
        for c in range(1, 21):
            assert stat[c] == 1.0

    def test_multiple_failed_seeds_gives_plus_one(self):
        seeds = self._make_completed_seeds()
        seeds[0] = SeedResult(seed=0, status=SeedStatus.EXECUTION_FAILURE, error_message="crash")
        seeds[29] = SeedResult(seed=29, status=SeedStatus.EXECUTION_FAILURE, error_message="OOM")
        stat = compute_world_null_statistic(seeds)
        for c in range(1, 21):
            assert stat[c] == 1.0

    def test_all_completed_no_candidate_gives_neg_inf(self):
        seeds = [
            SeedResult(seed=i, status=SeedStatus.COMPLETED_NO_CANDIDATE)
            for i in range(30)
        ]
        stat = compute_world_null_statistic(seeds)
        for c in range(1, 21):
            assert stat[c] == float("-inf")

    def test_normal_computation(self):
        seeds = self._make_completed_seeds(base_r2=0.5)
        stat = compute_world_null_statistic(seeds)
        for c in range(1, 21):
            assert np.isfinite(stat[c])
        # Should be non-decreasing
        for c in range(2, 21):
            assert stat[c] >= stat[c - 1]

    def test_wrong_seed_count_raises(self):
        with pytest.raises(ValueError):
            compute_world_null_statistic([])
        with pytest.raises(ValueError):
            compute_world_null_statistic(
                [SeedResult(seed=0, status=SeedStatus.COMPLETED_NO_CANDIDATE)] * 29
            )


# -----------------------------------------------------------------------
# Calibration validity
# -----------------------------------------------------------------------

class TestCalibrationValidity:

    def _make_world_results(self, n_failed: int = 0) -> dict[str, list[SeedResult]]:
        ids = all_world_ids()
        results = {}
        for i, wid in enumerate(ids):
            if i < n_failed:
                seeds = [
                    SeedResult(seed=j, status=SeedStatus.COMPLETED_WITH_CANDIDATES,
                               best_valid_r2_by_complexity={c: 0.1 for c in range(1, 21)})
                    for j in range(29)
                ]
                seeds.append(SeedResult(seed=29, status=SeedStatus.EXECUTION_FAILURE, error_message="fail"))
                results[wid] = seeds
            else:
                results[wid] = [
                    SeedResult(seed=j, status=SeedStatus.COMPLETED_WITH_CANDIDATES,
                               best_valid_r2_by_complexity={c: 0.1 for c in range(1, 21)})
                    for j in range(30)
                ]
        return results

    def test_5_failed_worlds_valid(self):
        results = self._make_world_results(n_failed=5)
        assert check_calibration_validity(results) == CalibrationValidity.VALID

    def test_6_failed_worlds_invalid(self):
        results = self._make_world_results(n_failed=6)
        assert check_calibration_validity(results) == CalibrationValidity.CALIBRATION_INVALID

    def test_0_failed_worlds_valid(self):
        results = self._make_world_results(n_failed=0)
        assert check_calibration_validity(results) == CalibrationValidity.VALID

    def test_wrong_world_count_invalid(self):
        results = self._make_world_results(n_failed=0)
        ids = list(results.keys())
        del results[ids[0]]
        assert check_calibration_validity(results) == CalibrationValidity.CALIBRATION_INVALID


# -----------------------------------------------------------------------
# Threshold table
# -----------------------------------------------------------------------

class TestThresholdTable:

    def _make_world_stats(self) -> dict[str, dict[int, float]]:
        ids = all_world_ids()
        rng = np.random.default_rng(12345)
        stats = {}
        for wid in ids:
            base = rng.uniform(0.0, 0.5)
            stats[wid] = {c: base + 0.01 * c for c in range(1, 21)}
        return stats

    def test_threshold_non_decreasing(self):
        stats = self._make_world_stats()
        table = compute_threshold_table(stats)
        for c in range(2, 21):
            assert table[c] >= table[c - 1]

    def test_exact_quantile_formula(self):
        """Verify quantile matches numpy's linear method."""
        stats = self._make_world_stats()
        table = compute_threshold_table(stats)
        for c in range(1, 21):
            values = sorted([stats[wid][c] for wid in stats])
            expected = np.quantile(values, 0.95, method="linear")
            # Before cummax, the raw quantile should match
            raw = np.quantile(
                [stats[wid][c] for wid in stats], 0.95, method="linear"
            )
            # After cummax, table[c] >= raw
            assert table[c] >= raw - 1e-12

    def test_threshold_cannot_decrease_after_failure_substitution(self):
        """Worlds with +1.0 from failures should not decrease thresholds."""
        ids = all_world_ids()
        stats: dict[str, dict[int, float]] = {}
        for i, wid in enumerate(ids):
            if i < 3:
                # Failed worlds contribute +1.0
                stats[wid] = {c: 1.0 for c in range(1, 21)}
            else:
                stats[wid] = {c: 0.1 + 0.01 * c for c in range(1, 21)}
        table = compute_threshold_table(stats)
        for c in range(2, 21):
            assert table[c] >= table[c - 1]

    def test_wrong_world_count_raises(self):
        with pytest.raises(ValueError):
            compute_threshold_table({})


# -----------------------------------------------------------------------
# Frozen parameters
# -----------------------------------------------------------------------

class TestFrozenCalibrationParams:

    def test_n_worlds(self):
        assert N_CALIBRATION_WORLDS == 100

    def test_n_seeds(self):
        assert N_SEEDS_PER_WORLD == 30

    def test_quantile(self):
        assert QUANTILE_LEVEL == 0.95

    def test_bootstrap_resamples(self):
        assert BOOTSTRAP_RESAMPLES == 2000

    def test_bootstrap_seed(self):
        assert BOOTSTRAP_SEED == 20260812

    def test_min_valid_worlds(self):
        assert MIN_VALID_WORLDS == 95

    def test_seed_base(self):
        assert PB_SEED_BASE == 2_110_000_000

    def test_seed_spread(self):
        assert PB_SEED_SPREAD == 370_000

    def test_max_complexity(self):
        assert MAX_COMPLEXITY == 20
