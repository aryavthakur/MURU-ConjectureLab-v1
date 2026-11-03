"""Amendment A3.1: structural-null calibration contract and runner interface.

This module defines the calibration protocol, seed derivation, failure
semantics, and threshold computation.  It does NOT execute calibration.
Execution belongs to Engineering RC3.

Calibration worlds: exactly 100
Allocation:
  - target_permuted_across_compounds: 34
  - descriptors_permuted_across_compounds: 33
  - gaussian_targets_with_observed_variance: 33

Within-compound energy permutation is EXCLUDED because it preserves
compound mean level, the scalar quantity being estimated.

Each world: 180 compounds, 30 scaffold groups, same five synthetic
covariates, same frozen correlation structure, scaffold-disjoint
60/20/20 split.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

import numpy as np

# -----------------------------------------------------------------------
# Frozen calibration parameters
# -----------------------------------------------------------------------

N_CALIBRATION_WORLDS = 100
N_COMPOUNDS = 180
N_SCAFFOLD_GROUPS = 30
MAX_COMPLEXITY = 20
N_SEEDS_PER_WORLD = 30

CONSTRUCTION_ALLOCATION: dict[str, int] = {
    "target_permuted_across_compounds": 34,
    "descriptors_permuted_across_compounds": 33,
    "gaussian_targets_with_observed_variance": 33,
}

assert sum(CONSTRUCTION_ALLOCATION.values()) == N_CALIBRATION_WORLDS

# Excluded construction
EXCLUDED_CONSTRUCTIONS: frozenset[str] = frozenset({
    "within_compound_energy_permutation",
})

# -----------------------------------------------------------------------
# Search settings (frozen, not tunable)
# -----------------------------------------------------------------------

SEARCH_SETTINGS = {
    "engine": "PySR",
    "engine_version": "1.5.10",
    "julia_package": "SymbolicRegression.jl",
    "julia_package_version": "1.11.x",
    "binary_operators": ["+", "-", "*", "/"],
    "unary_operators": ["sqrt", "log", "square", "cube", "inv"],
    "excluded_unary": ["exp", "sin", "cos", "tan"],
    "maxsize": MAX_COMPLEXITY,
    "niterations": 40,
    "populations": 15,
    "population_size": 33,
    "parsimony": 0.0032,
    "adaptive_parsimony_scaling": 20.0,
    "deterministic": True,
    "procs": 0,  # serial
    "seeds_per_world": N_SEEDS_PER_WORLD,
}

# -----------------------------------------------------------------------
# Seed derivation
# -----------------------------------------------------------------------

PB_SEED_BASE = 2_110_000_000
PB_SEED_SPREAD = 370_000


def derive_world_id(construction_name: str, index: int) -> str:
    """Derive the world ID for a calibration world."""
    if index < 0 or index >= N_CALIBRATION_WORLDS:
        raise ValueError(f"index must be 0..{N_CALIBRATION_WORLDS - 1}, got {index}")
    return f"PB|NCAL|{construction_name}|r{index:03d}"


def derive_calibration_seeds(world_id: str) -> list[int]:
    """Derive 30 search seeds from a world ID, byte-exactly as frozen."""
    h = int.from_bytes(
        hashlib.sha256(world_id.encode("utf-8")).digest()[:4],
        byteorder="big",
        signed=False,
    )
    base = PB_SEED_BASE + (h % PB_SEED_SPREAD) * 100
    return [base + k for k in range(N_SEEDS_PER_WORLD)]


def all_world_ids() -> list[str]:
    """Return all 100 calibration world IDs in allocation order."""
    ids = []
    for construction, count in CONSTRUCTION_ALLOCATION.items():
        for i in range(count):
            ids.append(derive_world_id(construction, i))
    return ids


def verify_seed_invariants() -> dict[str, bool]:
    """Verify the frozen seed invariants.

    Returns a dict of invariant names to pass/fail status.
    """
    world_ids = all_world_ids()
    all_seeds: list[int] = []
    bases: list[int] = []

    for wid in world_ids:
        seeds = derive_calibration_seeds(wid)
        all_seeds.extend(seeds)
        h = int.from_bytes(
            hashlib.sha256(wid.encode("utf-8")).digest()[:4],
            byteorder="big",
            signed=False,
        )
        bases.append(PB_SEED_BASE + (h % PB_SEED_SPREAD) * 100)

    return {
        "unique_world_ids": len(set(world_ids)) == N_CALIBRATION_WORLDS,
        "unique_base_buckets": len(set(bases)) == N_CALIBRATION_WORLDS,
        "unique_seeds": len(set(all_seeds)) == N_CALIBRATION_WORLDS * N_SEEDS_PER_WORLD,
        "signed_32bit_safe": all(0 <= s <= 2**31 - 1 for s in all_seeds),
        "total_worlds": len(world_ids) == N_CALIBRATION_WORLDS,
        "total_seeds": len(all_seeds) == N_CALIBRATION_WORLDS * N_SEEDS_PER_WORLD,
    }


# -----------------------------------------------------------------------
# Per-seed execution status
# -----------------------------------------------------------------------

class SeedStatus(str, Enum):
    COMPLETED_WITH_CANDIDATES = "COMPLETED_WITH_CANDIDATES"
    COMPLETED_NO_CANDIDATE = "COMPLETED_NO_CANDIDATE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"


@dataclass(frozen=True)
class SeedResult:
    """Result from one PySR search seed."""
    seed: int
    status: SeedStatus
    best_valid_r2_by_complexity: dict[int, float] | None = None
    error_message: str = ""


# -----------------------------------------------------------------------
# Null statistic computation
# -----------------------------------------------------------------------

def compute_seed_complexity_curve(
    best_r2_by_complexity: dict[int, float],
) -> dict[int, float]:
    """Compute prefix-monotone complexity curve for one seed.

    For complexity c=1..20, the best validation R2 attainable at
    complexity <= c is the cumulative max.

    Contract canary: once finite at c, later c may not become non-finite.
    """
    curve: dict[int, float] = {}
    running_max = float("-inf")
    seen_finite = False

    for c in range(1, MAX_COMPLEXITY + 1):
        r2 = best_r2_by_complexity.get(c, float("-inf"))
        if np.isfinite(r2):
            seen_finite = True
        elif seen_finite and not np.isfinite(r2):
            # Once finite, must stay finite - use running_max
            r2 = running_max

        running_max = max(running_max, r2)
        curve[c] = running_max

    return curve


def compute_world_null_statistic(
    seed_results: Sequence[SeedResult],
) -> dict[int, float]:
    """Compute S(w, c) for one calibration world.

    S(w, c) = max over 30 seeds of best validation R2 at complexity <= c.

    If ANY seed has EXECUTION_FAILURE, the entire row becomes +1.0.
    COMPLETED_NO_CANDIDATE legitimately contributes -inf.
    """
    if len(seed_results) != N_SEEDS_PER_WORLD:
        raise ValueError(
            f"expected {N_SEEDS_PER_WORLD} seed results, got {len(seed_results)}"
        )

    # Check for execution failures
    has_failure = any(
        sr.status == SeedStatus.EXECUTION_FAILURE for sr in seed_results
    )
    if has_failure:
        return {c: 1.0 for c in range(1, MAX_COMPLEXITY + 1)}

    # Compute per-seed curves, then take max across seeds
    world_stat: dict[int, float] = {c: float("-inf") for c in range(1, MAX_COMPLEXITY + 1)}

    for sr in seed_results:
        if sr.status == SeedStatus.COMPLETED_NO_CANDIDATE:
            # Legitimate -inf contribution
            continue
        if sr.best_valid_r2_by_complexity is None:
            continue
        curve = compute_seed_complexity_curve(sr.best_valid_r2_by_complexity)
        for c in range(1, MAX_COMPLEXITY + 1):
            world_stat[c] = max(world_stat[c], curve[c])

    return world_stat


# -----------------------------------------------------------------------
# Calibration validity
# -----------------------------------------------------------------------

MIN_VALID_WORLDS = 95


def count_failed_worlds(
    world_results: Mapping[str, Sequence[SeedResult]],
) -> int:
    """Count worlds that contain at least one execution-failure seed."""
    failed = 0
    for world_id, seed_results in world_results.items():
        if any(sr.status == SeedStatus.EXECUTION_FAILURE for sr in seed_results):
            failed += 1
    return failed


class CalibrationValidity(str, Enum):
    VALID = "VALID"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    NOT_EXECUTED = "NOT_EXECUTED"


def check_calibration_validity(
    world_results: Mapping[str, Sequence[SeedResult]],
) -> CalibrationValidity:
    """Check whether calibration is valid.

    At least 95/100 worlds must have zero execution-failure seeds.
    If more than 5 worlds contain execution failures: CALIBRATION_INVALID.
    No selective retries or replacement worlds.
    """
    if len(world_results) != N_CALIBRATION_WORLDS:
        return CalibrationValidity.CALIBRATION_INVALID

    failed = count_failed_worlds(world_results)
    if failed > N_CALIBRATION_WORLDS - MIN_VALID_WORLDS:
        return CalibrationValidity.CALIBRATION_INVALID

    return CalibrationValidity.VALID


# -----------------------------------------------------------------------
# Threshold table computation
# -----------------------------------------------------------------------

QUANTILE_LEVEL = 0.95
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20260812


def compute_threshold_table(
    world_statistics: Mapping[str, dict[int, float]],
) -> dict[int, float]:
    """Compute the 95th percentile threshold table.

    For each complexity c=1..20, compute Q95 of the S(w,c) values
    across all 100 worlds, then enforce non-decreasing thresholds
    via np.maximum.accumulate.

    Quantile: numpy.quantile(..., 0.95, method="linear")
    For N=100 ascending x: Q95 = x[94] + 0.05 * (x[95] - x[94])
    """
    if len(world_statistics) != N_CALIBRATION_WORLDS:
        raise ValueError(
            f"expected {N_CALIBRATION_WORLDS} worlds, got {len(world_statistics)}"
        )

    thresholds = np.empty(MAX_COMPLEXITY, dtype=np.float64)

    for c in range(1, MAX_COMPLEXITY + 1):
        values = np.array(
            [world_statistics[wid][c] for wid in world_statistics],
            dtype=np.float64,
        )
        thresholds[c - 1] = np.quantile(values, QUANTILE_LEVEL, method="linear")

    # Enforce non-decreasing
    thresholds = np.maximum.accumulate(thresholds)

    return {c: float(thresholds[c - 1]) for c in range(1, MAX_COMPLEXITY + 1)}


def compute_bootstrap_uncertainty(
    world_statistics: Mapping[str, dict[int, float]],
) -> dict[int, tuple[float, float]]:
    """Compute bootstrap CI for the threshold table.

    2000 world-level resamples, seed 20260812.
    Returns {complexity: (lower_2.5, upper_97.5)} for reporting only.
    """
    if len(world_statistics) != N_CALIBRATION_WORLDS:
        raise ValueError(
            f"expected {N_CALIBRATION_WORLDS} worlds, got {len(world_statistics)}"
        )

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    world_ids = list(world_statistics.keys())
    n = len(world_ids)

    boot_thresholds = np.empty((BOOTSTRAP_RESAMPLES, MAX_COMPLEXITY), dtype=np.float64)

    for b in range(BOOTSTRAP_RESAMPLES):
        indices = rng.integers(0, n, size=n)
        resampled_ids = [world_ids[i] for i in indices]
        for c in range(1, MAX_COMPLEXITY + 1):
            values = np.array(
                [world_statistics[wid][c] for wid in resampled_ids],
                dtype=np.float64,
            )
            boot_thresholds[b, c - 1] = np.quantile(
                values, QUANTILE_LEVEL, method="linear"
            )
        boot_thresholds[b] = np.maximum.accumulate(boot_thresholds[b])

    result: dict[int, tuple[float, float]] = {}
    for c in range(1, MAX_COMPLEXITY + 1):
        col = boot_thresholds[:, c - 1]
        result[c] = (float(np.percentile(col, 2.5)), float(np.percentile(col, 97.5)))

    return result
