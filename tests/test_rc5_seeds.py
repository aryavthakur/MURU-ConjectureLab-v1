"""A3.5 section 8.1: the production case-search seed derivation.

Every number asserted here is quoted from the frozen amendment, never chosen
by this test.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.registry import PARTITIONS, iter_case_ids
from muru.paper_benchmark.rc3_provenance import SIGNED_32BIT_MAX
from muru.paper_benchmark.rc5_seeds import (
    A35_BAND_NAME,
    A35_SEARCH_SEED_BASE,
    A35_SEARCH_SEED_MAX,
    A35_SEARCH_SEED_MIN,
    A35_SEEDS_PER_CASE,
    A35_TOTAL_CASES,
    SearchSeedInvariantError,
    all_case_ids,
    case_id_for_ordinal,
    case_ordinal,
    case_search_seeds,
    iter_all_search_seeds,
    search_seed,
    verify_search_seed_invariants,
)
from muru.paper_benchmark.seed_band_registry import DECLARED_BANDS


# -----------------------------------------------------------------------
# Frozen constants
# -----------------------------------------------------------------------

def test_constants_are_the_frozen_a3_5_values():
    assert A35_SEARCH_SEED_BASE == 2_100_000_000
    assert A35_SEEDS_PER_CASE == 30


def test_case_population_is_the_frozen_380():
    assert A35_TOTAL_CASES == 380
    assert len(list(iter_case_ids("development"))) == 80
    assert len(list(iter_case_ids("held_out"))) == 240
    assert len(list(iter_case_ids("challenge"))) == 60


def test_occupied_band_is_exactly_the_amendment_s_declared_extent():
    # "Occupied range: [2,100,000,000 , 2,100,011,399] -- 11,400 consecutive
    # integers" (A3.5 section 8.1).
    assert (A35_SEARCH_SEED_MIN, A35_SEARCH_SEED_MAX) == (2_100_000_000, 2_100_011_399)
    assert A35_SEARCH_SEED_MAX - A35_SEARCH_SEED_MIN + 1 == 11_400


# -----------------------------------------------------------------------
# Enumeration order
# -----------------------------------------------------------------------

def test_enumeration_is_partition_major_then_registry_order():
    ids = all_case_ids()
    assert len(ids) == 380
    expected: list[str] = []
    for partition in PARTITIONS:
        expected.extend(iter_case_ids(partition))
    assert list(ids) == expected
    assert ids[0] == "PB|development|F01|r000"
    assert ids[79].startswith("PB|development|")
    assert ids[80].startswith("PB|held_out|")
    assert ids[319].startswith("PB|held_out|")
    assert ids[320].startswith("PB|challenge|")
    assert ids[-1] == "PB|challenge|F20|r002"


def test_case_ordinal_round_trips():
    for ordinal, case_id in enumerate(all_case_ids()):
        assert case_ordinal(case_id) == ordinal
        assert case_id_for_ordinal(ordinal) == case_id


def test_case_ordinal_rejects_a_non_registry_id():
    with pytest.raises(ValueError):
        case_ordinal("PB|development|F99|r000")
    with pytest.raises(ValueError):
        case_ordinal("not a case id")


def test_case_id_for_ordinal_is_range_checked():
    with pytest.raises(ValueError):
        case_id_for_ordinal(-1)
    with pytest.raises(ValueError):
        case_id_for_ordinal(A35_TOTAL_CASES)


# -----------------------------------------------------------------------
# The seed function itself
# -----------------------------------------------------------------------

def test_search_seed_is_the_frozen_arithmetic():
    assert search_seed(0, 0) == 2_100_000_000
    assert search_seed(0, 29) == 2_100_000_029
    assert search_seed(1, 0) == 2_100_000_030
    assert search_seed(379, 29) == 2_100_011_399


def test_search_seed_raises_rather_than_returning_out_of_band():
    # "Implementations MUST bound k and MUST range-check the result, raising
    # rather than returning an out-of-band value" (A3.5 section 8.1).
    with pytest.raises(ValueError):
        search_seed(-1, 0)
    with pytest.raises(ValueError):
        search_seed(A35_TOTAL_CASES, 0)
    with pytest.raises(ValueError):
        search_seed(0, -1)
    with pytest.raises(ValueError):
        search_seed(0, A35_SEEDS_PER_CASE)


def test_case_search_seeds_returns_thirty_consecutive_seeds():
    seeds = case_search_seeds("PB|development|F01|r000")
    assert len(seeds) == 30
    assert list(seeds) == list(range(2_100_000_000, 2_100_000_030))


# -----------------------------------------------------------------------
# Exhaustive invariants over the whole 380 x 30 domain
# -----------------------------------------------------------------------

def test_all_11400_seeds_are_distinct_and_collision_free():
    seeds = [seed for _, _, seed in iter_all_search_seeds()]
    assert len(seeds) == 11_400
    assert len(set(seeds)) == 11_400


def test_the_map_is_injective_and_densely_occupies_its_band():
    seeds = sorted(seed for _, _, seed in iter_all_search_seeds())
    assert seeds[0] == A35_SEARCH_SEED_MIN
    assert seeds[-1] == A35_SEARCH_SEED_MAX
    assert seeds == list(range(A35_SEARCH_SEED_MIN, A35_SEARCH_SEED_MAX + 1))


def test_every_seed_is_positive_and_int32_safe():
    for _, _, seed in iter_all_search_seeds():
        assert seed > 0
        assert seed <= SIGNED_32BIT_MAX


def test_seed_namespaces_are_disjoint_by_declared_extent():
    # Not by realised-seed intersection: A3.5 section 8.1 makes that
    # distinction load-bearing, because 63bbcce's overlap went undetected
    # exactly by testing realised seeds only.
    others = [b for b in DECLARED_BANDS if b.name != A35_BAND_NAME]
    assert others, "the registry must declare bands other than A3.5's own"
    for band in others:
        overlaps = band.min_seed <= A35_SEARCH_SEED_MAX and A35_SEARCH_SEED_MIN <= band.max_seed
        assert not overlaps, f"A3.5 band overlaps {band.name} by declared extent"


def test_the_registry_entry_agrees_with_this_module():
    declared = next(b for b in DECLARED_BANDS if b.name == A35_BAND_NAME)
    assert (declared.min_seed, declared.max_seed) == (
        A35_SEARCH_SEED_MIN,
        A35_SEARCH_SEED_MAX,
    )


def test_verify_search_seed_invariants_reports_the_frozen_guards():
    report = verify_search_seed_invariants()
    assert report["total_seeds"] == 11_400
    assert report["distinct_seeds"] == 11_400
    assert report["cases"] == 380
    assert report["seeds_per_case"] == 30
    assert report["band_min"] == 2_100_000_000
    assert report["band_max"] == 2_100_011_399
    assert report["disjointness_method"] == "declared_extent_comparison"
    guards = report["guards_by_band"]
    # The exact guards A3.5 section 8.1's disjointness table states.
    assert guards["objval_plan2"] == 71
    assert guards["a3_1_a3_2_structural_null_calibration"] == 9_988_601
    assert guards["phase3_discovery"] == 421_378_471
    assert report["signed_32bit_headroom"] == 47_472_248


def test_the_guard_is_hard_failing_not_advisory():
    # It must raise, not warn or return False, when an invariant breaks.
    import muru.paper_benchmark.rc5_seeds as mod

    original = mod.A35_SEARCH_SEED_MAX
    try:
        mod.A35_SEARCH_SEED_MAX = original + 1
        with pytest.raises(SearchSeedInvariantError):
            verify_search_seed_invariants()
    finally:
        mod.A35_SEARCH_SEED_MAX = original
    # And it passes again once restored, so the test left no residue.
    verify_search_seed_invariants()


def test_no_partition_conditional_behaviour_in_the_derivation():
    # One shared band across partitions is correct (A3.5 section 8.1): the
    # seed is a pure function of (ordinal, k), and the ordinal comes from the
    # frozen enumeration. Two cases at adjacent ordinals across the
    # development/held_out boundary get adjacent seed blocks, with no gap,
    # offset, or namespace change at the boundary.
    ids = all_case_ids()
    last_dev = ids[79]
    first_held = ids[80]
    assert last_dev.startswith("PB|development|")
    assert first_held.startswith("PB|held_out|")
    assert case_search_seeds(last_dev)[-1] + 1 == case_search_seeds(first_held)[0]
