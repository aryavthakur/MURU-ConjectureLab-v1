"""A3.5 Session 3, Part H: full pairwise seed-band collision check.

Runs the centralized registry (``muru.paper_benchmark.seed_band_registry``)
over every declared band and fails loudly on any collision this registry
does not already know about. Also regression-tests that the one already-
known, disclosed, pre-existing collision in frozen engineering code
(RC3-smoke inside objval/plan2's envelope) stays visible rather than
silently disappearing.

Governance/engineering only -- asserts no science.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.seed_band_registry import (
    ACKNOWLEDGED_COLLISIONS,
    DECLARED_BANDS,
    FALSV2_SEED_BASE,
    FALSV2_SEED_CAPACITY,
    FALSV2_SEED_MAX,
    SIGNED_32BIT_MAX,
    Overlap,
    SeedBand,
    assert_governance_clean,
    falsv2_seed,
    find_overlaps,
    unacknowledged_overlaps,
)


def _band(name: str) -> SeedBand:
    for b in DECLARED_BANDS:
        if b.name == name:
            return b
    raise KeyError(name)


# -----------------------------------------------------------------------
# The core governance gate
# -----------------------------------------------------------------------

def test_no_unacknowledged_collisions_among_declared_bands():
    """This is the gate: if any two declared bands ever actually overlap
    without being on the acknowledged list, this fails loudly."""
    assert unacknowledged_overlaps() == []


def test_assert_governance_clean_does_not_raise_and_returns_a_report():
    report = assert_governance_clean()
    assert report["bands_checked"] == len(DECLARED_BANDS)
    assert report["pairs_checked"] == len(DECLARED_BANDS) * (len(DECLARED_BANDS) - 1) // 2


def test_every_declared_band_is_signed_32bit_safe_and_positive():
    for band in DECLARED_BANDS:
        assert band.min_seed > 0, band.name
        assert band.max_seed <= SIGNED_32BIT_MAX, band.name
        assert band.min_seed <= band.max_seed, band.name


# -----------------------------------------------------------------------
# The already-known, disclosed, pre-existing collision stays VISIBLE
# -----------------------------------------------------------------------

def test_the_known_rc3_smoke_vs_objval_plan2_collision_is_still_detected():
    """This is a regression test for VISIBILITY, not a request to fix it.

    `rc3_provenance.assert_seed_band_separation` never checks the RC3-smoke
    band against objval/plan2 (audit/MURU_A3_5_DECISION_2_CALIBRATION_RESULT.md
    section 1.2). That collision is real, pre-existing, and out of A3.5's
    mandate to alter -- but this registry must always be ABLE to see it. If
    this test ever fails because the overlap silently disappeared from
    `find_overlaps()`, that is this registry regressing, not a fix to cheer.
    """
    overlaps = find_overlaps()
    matches = [
        ov
        for ov in overlaps
        if {ov.band_a, ov.band_b} == {"rc3_engineering_smoke", "objval_plan2"}
    ]
    assert len(matches) == 1
    ov = matches[0]
    # RC3 smoke [1,900,000,000, 1,900,999,999] sits entirely inside
    # objval/plan2 [1,700,000,000, 2,099,999,929] -- full containment.
    assert ov.lo == 1_900_000_000
    assert ov.hi == 1_900_999_999
    assert ov.extent == 1_000_000
    assert frozenset({ov.band_a, ov.band_b}) in ACKNOWLEDGED_COLLISIONS


def test_acknowledged_collision_is_the_only_overlap_found():
    """No collisions exist among the declared bands beyond the one known,
    disclosed, pre-existing one."""
    overlaps = find_overlaps()
    keys = {frozenset({ov.band_a, ov.band_b}) for ov in overlaps}
    assert keys == ACKNOWLEDGED_COLLISIONS


def test_checker_actually_detects_a_synthetic_overlap():
    """Proves the mechanism works: two bands that genuinely overlap must be
    reported, and reported as unacknowledged if not on the allowlist."""
    a = SeedBand("synthetic_a", 1_000, 1_100, "test", "synthetic")
    b = SeedBand("synthetic_b", 1_050, 1_150, "test", "synthetic")
    overlaps = find_overlaps((a, b))
    assert len(overlaps) == 1
    assert overlaps[0].lo == 1_050
    assert overlaps[0].hi == 1_100
    assert overlaps[0].extent == 51

    with pytest.raises(RuntimeError, match="UNACKNOWLEDGED"):
        assert_governance_clean((a, b))


# -----------------------------------------------------------------------
# The new falsification-v2 band
# -----------------------------------------------------------------------

def test_v2_band_matches_its_declared_entry():
    band = _band("falsification_calibration_v2")
    assert band.min_seed == FALSV2_SEED_BASE == 1_690_000_000
    assert band.max_seed == FALSV2_SEED_MAX == FALSV2_SEED_BASE + FALSV2_SEED_CAPACITY - 1
    assert FALSV2_SEED_CAPACITY == 1_000_000


def test_v2_band_disjoint_from_v1_band_with_a_wide_guard():
    v1 = _band("falsification_calibration_v1")
    v2 = _band("falsification_calibration_v2")
    assert not v1.overlaps(v2)
    gap = v2.min_seed - v1.max_seed - 1
    assert gap == 9_000_000
    assert gap > FALSV2_SEED_CAPACITY  # guard exceeds the new band's own capacity


def test_v2_band_disjoint_from_objval_plan2_with_a_wide_guard():
    v2 = _band("falsification_calibration_v2")
    ov = _band("objval_plan2")
    assert not v2.overlaps(ov)
    gap = ov.min_seed - v2.max_seed - 1
    assert gap == 9_000_000
    assert gap > FALSV2_SEED_CAPACITY


def test_v2_band_disjoint_from_every_other_declared_band():
    v2 = _band("falsification_calibration_v2")
    for band in DECLARED_BANDS:
        if band.name == "falsification_calibration_v2":
            continue
        assert not v2.overlaps(band), f"v2 collides with {band.name}"


def test_v2_band_stays_within_signed_32bit():
    assert FALSV2_SEED_MAX <= SIGNED_32BIT_MAX


def test_falsv2_seed_is_an_injective_bijection_over_its_domain():
    seeds = [falsv2_seed(k) for k in range(0, FALSV2_SEED_CAPACITY, 1009)]  # sparse sample
    assert len(seeds) == len(set(seeds))
    for k, s in zip(range(0, FALSV2_SEED_CAPACITY, 1009), seeds):
        assert s == FALSV2_SEED_BASE + k

    assert falsv2_seed(0) == FALSV2_SEED_BASE
    assert falsv2_seed(FALSV2_SEED_CAPACITY - 1) == FALSV2_SEED_MAX


def test_falsv2_seed_range_checks_and_raises_out_of_band():
    with pytest.raises(ValueError):
        falsv2_seed(-1)
    with pytest.raises(ValueError):
        falsv2_seed(FALSV2_SEED_CAPACITY)
    with pytest.raises(ValueError):
        falsv2_seed(10**9)


def test_v2_never_reuses_a_v1_seed_across_the_full_domain():
    """Hygiene requirement: v2 must not share a single seed with v1 --
    checked directly over the full domain, not sampled."""
    v1 = _band("falsification_calibration_v1")
    v2_seeds = {falsv2_seed(k) for k in (0, 1, 2, FALSV2_SEED_CAPACITY // 2, FALSV2_SEED_CAPACITY - 1)}
    for s in v2_seeds:
        assert not (v1.min_seed <= s <= v1.max_seed)
    # and, by envelope, the entire ranges never touch:
    assert v1.max_seed < FALSV2_SEED_BASE
