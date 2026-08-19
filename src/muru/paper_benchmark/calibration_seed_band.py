"""Calibration search-seed band — MURU v2 re-entry, Route R-B (protocol v2 section 5.2).

The band base is set by a REGISTERED RULE and derived from it, never chosen:

    CALIBRATION_SEARCH_SEED_BASE = rc5_seeds.A35_SEARCH_SEED_MAX + 1

`seed_band_registry.DECLARED_BANDS` is NOT mutated. `seed_band_registry.py` is
pinned by the closed RC5 authorized-delta ledger, and editing it would be exactly
the unauthorised drift that ledger exists to prevent. Disjointness is instead
checked with the frozen registry's OWN checker, applied to a tuple constructed
here at runtime.
"""
from __future__ import annotations

from . import rc5_seeds, seed_band_registry
from .calibration_surface import (
    CALIBRATION_FAMILIES, CALIBRATION_REPLICATES, calibration_ordinal,
)

CALIBRATION_SEARCH_SEED_BASE = rc5_seeds.A35_SEARCH_SEED_MAX + 1   # derived, never a literal
CALIBRATION_SEEDS_PER_CASE = rc5_seeds.A35_SEEDS_PER_CASE          # imported (= 30)

N_CALIBRATION_WORLDS = len(CALIBRATION_FAMILIES) * CALIBRATION_REPLICATES   # 1,932
N_CALIBRATION_SEARCHES = N_CALIBRATION_WORLDS * CALIBRATION_SEEDS_PER_CASE  # 57,960

CALIBRATION_SEARCH_SEED_MIN = CALIBRATION_SEARCH_SEED_BASE
CALIBRATION_SEARCH_SEED_MAX = CALIBRATION_SEARCH_SEED_BASE + N_CALIBRATION_SEARCHES - 1

SIGNED_32BIT_MAX = 2_147_483_647


def search_seed(ordinal: int, k: int) -> int:
    if not 0 <= ordinal < N_CALIBRATION_WORLDS:
        raise ValueError(f"calibration ordinal {ordinal} out of range")
    if not 0 <= k < CALIBRATION_SEEDS_PER_CASE:
        raise ValueError(f"seed index {k} out of range")
    return CALIBRATION_SEARCH_SEED_BASE + ordinal * CALIBRATION_SEEDS_PER_CASE + k


def search_seed_for_case(case_id: str, k: int) -> int:
    return search_seed(calibration_ordinal(case_id), k)


def _band_tuple() -> "seed_band_registry.SeedBand":
    """Build the candidate band using the frozen registry's OWN SeedBand type,
    WITHOUT mutating DECLARED_BANDS. Its __post_init__ enforces positivity,
    ordering and the signed-32-bit ceiling for us."""
    return seed_band_registry.SeedBand(
        name="v2_calibration_surface",
        min_seed=CALIBRATION_SEARCH_SEED_MIN,
        max_seed=CALIBRATION_SEARCH_SEED_MAX,
        source="src/muru/paper_benchmark/calibration_seed_band.py",
        derivation="rc5_seeds.A35_SEARCH_SEED_MAX + 1 + ordinal*30 + k, "
                   "ordinal in [0,1932), k in [0,30)",
    )


def verify_band() -> dict:
    """Disjointness via the frozen registry's own checker, plus the 32-bit bound."""
    candidate = _band_tuple()
    combined = tuple(seed_band_registry.DECLARED_BANDS) + (candidate,)
    overlaps = seed_band_registry.find_overlaps(combined)
    # only overlaps involving the new band are ours to answer for
    ours = [o for o in overlaps
            if "v2_calibration_surface" in (o.band_a, o.band_b)]
    return {
        "base_rule": "rc5_seeds.A35_SEARCH_SEED_MAX + 1",
        "base_value": CALIBRATION_SEARCH_SEED_BASE,
        "band": [CALIBRATION_SEARCH_SEED_MIN, CALIBRATION_SEARCH_SEED_MAX],
        "n_searches": N_CALIBRATION_SEARCHES,
        "n_worlds": N_CALIBRATION_WORLDS,
        "declared_bands_mutated": False,
        "preexisting_unacknowledged_overlaps": [repr(o) for o in
                                                seed_band_registry.unacknowledged_overlaps()],
        "overlaps_involving_calibration_band": [repr(o) for o in ours],
        "within_signed_32bit": CALIBRATION_SEARCH_SEED_MAX <= SIGNED_32BIT_MAX,
        "passed": not ours and CALIBRATION_SEARCH_SEED_MAX <= SIGNED_32BIT_MAX,
    }
