"""RC3 provenance and seed-band separation."""
from __future__ import annotations

import pytest

from muru.paper_benchmark.calibration_contract import (
    N_SEEDS_PER_WORLD,
    PB_SEED_BASE,
    PB_SEED_SPREAD,
    all_world_ids,
    derive_calibration_seeds,
)
from muru.paper_benchmark.rc3_provenance import (
    CALIBRATION_SEED_MAX,
    CALIBRATION_SEED_MIN,
    RC2_LOCK_COMMIT,
    RC2_LOCK_SHA256,
    RC3_SMOKE_SEED_BASE,
    RC3_SMOKE_SEED_MAX,
    REQUIRED_PACKAGES,
    SIGNED_32BIT_MAX,
    DependencyMismatch,
    assert_seed_band_separation,
    build_provenance_manifest,
    read_lock_pins,
    smoke_seed,
    verify_dependencies,
)


# -----------------------------------------------------------------------
# Seed-band separation
# -----------------------------------------------------------------------

def test_calibration_band_is_derived_from_the_frozen_constants():
    assert CALIBRATION_SEED_MIN == PB_SEED_BASE
    assert CALIBRATION_SEED_MAX == (
        PB_SEED_BASE + (PB_SEED_SPREAD - 1) * 100 + (N_SEEDS_PER_WORLD - 1)
    )


def test_bands_are_disjoint():
    bands = assert_seed_band_separation()
    assert bands["smoke_seed_max"] < bands["calibration_seed_min"]
    assert bands["gap"] > 0


def test_no_calibration_seed_lands_in_the_smoke_band():
    """Exhaustive over all 3000 real calibration seeds."""
    seeds = set()
    for world_id in all_world_ids():
        seeds.update(derive_calibration_seeds(world_id))
    assert len(seeds) == 3000
    assert not any(RC3_SMOKE_SEED_BASE <= s <= RC3_SMOKE_SEED_MAX for s in seeds)
    assert min(seeds) >= CALIBRATION_SEED_MIN
    assert max(seeds) <= CALIBRATION_SEED_MAX


def test_no_smoke_seed_lands_in_the_calibration_band():
    calibration = set()
    for world_id in all_world_ids():
        calibration.update(derive_calibration_seeds(world_id))
    smoke = {smoke_seed(w, k) for w in range(20) for k in range(20)}
    assert not smoke & calibration
    assert all(s < CALIBRATION_SEED_MIN for s in smoke)


def test_every_seed_is_signed_32_bit_safe():
    seeds = {smoke_seed(w, k) for w in range(20) for k in range(20)}
    for world_id in all_world_ids():
        seeds.update(derive_calibration_seeds(world_id))
    assert all(0 <= s <= SIGNED_32BIT_MAX for s in seeds)


def test_smoke_seeds_are_unique_across_the_whole_accepted_domain():
    """Injective everywhere it accepts, not merely on a sampled corner."""
    from muru.paper_benchmark.rc3_provenance import RC3_SMOKE_SEEDS_PER_WORLD

    seeds = [
        smoke_seed(w, k)
        for w in range(50)
        for k in (0, 1, RC3_SMOKE_SEEDS_PER_WORLD - 1)
    ]
    assert len(set(seeds)) == len(seeds)


def test_the_aliasing_input_is_rejected_rather_than_colliding():
    """smoke_seed(0, 1000) previously equalled smoke_seed(1, 0)."""
    from muru.paper_benchmark.rc3_provenance import RC3_SMOKE_SEEDS_PER_WORLD

    with pytest.raises(ValueError, match="seed_index"):
        smoke_seed(0, RC3_SMOKE_SEEDS_PER_WORLD)


def test_smoke_seed_cannot_escape_its_band():
    with pytest.raises(ValueError, match="escapes"):
        smoke_seed(10_000, 0)
    with pytest.raises(ValueError, match="non-negative"):
        smoke_seed(-1, 0)


# -----------------------------------------------------------------------
# Dependency provenance
# -----------------------------------------------------------------------

def test_lock_is_the_byte_copy_of_the_rc2_lock():
    pins = read_lock_pins()
    assert pins["scikit-learn"] == "1.9.0"
    assert pins["pysr"] == "1.5.10"
    assert len(RC2_LOCK_SHA256) == 64
    assert len(RC2_LOCK_COMMIT) == 40


def test_every_number_moving_package_is_pinned():
    pins = read_lock_pins()
    for dist in REQUIRED_PACKAGES:
        assert dist.lower() in pins, dist


def test_installed_environment_matches_the_lock():
    installed = verify_dependencies()
    assert installed["scikit-learn"] == "1.9.0"
    assert installed["pysr"] == "1.5.10"


def test_a_tampered_lock_is_rejected(tmp_path):
    bad = tmp_path / "lock.txt"
    bad.write_text("scikit-learn==9.9.9\npysr==1.5.10\n")
    with pytest.raises(DependencyMismatch, match="scikit-learn"):
        verify_dependencies(lock_path=bad)


def test_a_missing_pin_is_rejected(tmp_path):
    bad = tmp_path / "lock.txt"
    bad.write_text("scikit-learn==1.9.0\n")
    with pytest.raises(DependencyMismatch, match="not pinned"):
        verify_dependencies(lock_path=bad)


def test_a_missing_lock_file_is_rejected(tmp_path):
    with pytest.raises(DependencyMismatch, match="not found"):
        verify_dependencies(lock_path=tmp_path / "absent.txt")


# -----------------------------------------------------------------------
# Manifest
# -----------------------------------------------------------------------

def test_manifest_records_the_full_stack():
    payload = build_provenance_manifest(strict=True).to_payload()
    assert set(payload) == {
        "commit", "dirty", "lock_relpath", "lock_commit", "lock_sha256",
        "python_packages", "julia", "seed_bands",
    }
    for dist in REQUIRED_PACKAGES:
        assert dist in payload["python_packages"]
    assert "SymbolicRegression.jl" in payload["julia"]
    assert "julia" in payload["julia"]
    assert len(payload["commit"]) == 40


def test_manifest_does_not_boot_julia_by_default():
    payload = build_provenance_manifest(strict=True).to_payload()
    assert payload["julia"]["julia"] == "NOT_STARTED"
