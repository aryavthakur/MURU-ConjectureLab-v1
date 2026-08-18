"""Engineering RC5: the A3.5 production case-search seed derivation.

Amendment A3.5 section 8.1 binds this derivation exactly::

    A35_SEARCH_SEED_BASE = 2_100_000_000
    A35_SEEDS_PER_CASE   = 30

    search_seed(case_ordinal, k) = A35_SEARCH_SEED_BASE
                                 + case_ordinal * A35_SEEDS_PER_CASE
                                 + k
        case_ordinal in [0, 380)   # deterministic position of the case ID in
                                   # the frozen registry enumeration order
                                   # (partition-major, family, replicate)
        k            in [0, 30)

Occupied range: ``[2_100_000_000, 2_100_011_399]`` -- 11,400 consecutive
integers, one per (case, seed) pair across all 380 cases.

**Why ordinal, not hashed.**  A3.5 section 8.1 corrects ``63bbcce``'s
bucket+stride scheme, whose band overlapped ``objval/plan2`` across
194,718,530 integers.  Under an ordinal scheme a collision is
*arithmetically impossible*, so collision-freedom is structural rather than
probabilistic and the "discover a collision, change a constant" repair path
-- which would be seed-shopping -- never arises.

**Why a new module.**  A3.5 implementation obligation 9: A3.5's constants
MUST live in a new module importing the frozen ones, because
``rc3_provenance.py``, ``registry.py`` and ``analysis.py`` are byte-pinned by
``pb_30``/``pb_33``/``pb_34`` and the RC4.2 ``AUTHORIZED_DELTA`` ledger is a
closed 8-entry tuple.  Nothing here mutates a frozen module.

**One shared band across partitions is correct**, per section 8.1: partition
identity is already the second field of the case ID that determines
``case_ordinal``, cross-partition distinctness is structural under an
injective map, and no consumer infers a partition from a bare seed value.
This module therefore contains **no partition-conditional behaviour** beyond
the enumeration order the frozen registry itself defines.
"""
from __future__ import annotations

from typing import Iterator

from .registry import PARTITIONS, iter_case_ids, resolve_case_id
from .rc3_provenance import SIGNED_32BIT_MAX
from .seed_band_registry import DECLARED_BANDS, SeedBand

__all__ = [
    "A35_SEARCH_SEED_BASE",
    "A35_SEEDS_PER_CASE",
    "A35_TOTAL_CASES",
    "A35_SEARCH_SEED_MIN",
    "A35_SEARCH_SEED_MAX",
    "A35_BAND_NAME",
    "all_case_ids",
    "case_ordinal",
    "case_id_for_ordinal",
    "search_seed",
    "case_search_seeds",
    "iter_all_search_seeds",
    "SearchSeedInvariantError",
    "verify_search_seed_invariants",
]

#: A3.5 section 8.1, verbatim.  Neither constant is derived from, tuned
#: against, or adjusted by any observed benchmark outcome.
A35_SEARCH_SEED_BASE = 2_100_000_000
A35_SEEDS_PER_CASE = 30

#: The closed case population, computed from the frozen registry rather than
#: restated: 80 development + 240 held-out + 60 challenge.
A35_TOTAL_CASES = sum(len(list(iter_case_ids(p))) for p in PARTITIONS)

A35_SEARCH_SEED_MIN = A35_SEARCH_SEED_BASE
A35_SEARCH_SEED_MAX = (
    A35_SEARCH_SEED_BASE + A35_TOTAL_CASES * A35_SEEDS_PER_CASE - 1
)

#: The name this band carries in the frozen governance registry.
A35_BAND_NAME = "a3_5_case_search_reserved"


def all_case_ids() -> tuple[str, ...]:
    """The frozen 380-case enumeration, partition-major then registry order.

    ``PARTITIONS`` fixes the partition order; ``iter_case_ids`` fixes the
    family-then-replicate order inside each partition.  Both are frozen, so
    this sequence is a pure function of the registry.
    """
    out: list[str] = []
    for partition in PARTITIONS:
        out.extend(iter_case_ids(partition))
    return tuple(out)


_CASE_IDS: tuple[str, ...] = all_case_ids()
_ORDINAL_BY_CASE_ID: dict[str, int] = {c: i for i, c in enumerate(_CASE_IDS)}

if len(_ORDINAL_BY_CASE_ID) != len(_CASE_IDS):  # pragma: no cover - registry is frozen
    raise ImportError("the frozen registry enumeration contains a duplicate case ID")
if len(_CASE_IDS) != A35_TOTAL_CASES:  # pragma: no cover - arithmetic identity
    raise ImportError("case enumeration length disagrees with A35_TOTAL_CASES")


def case_ordinal(case_id: str) -> int:
    """The case ID's deterministic position in the frozen enumeration.

    Raises on any string that is not one of the 380 frozen case IDs, rather
    than returning an out-of-band value.  ``resolve_case_id`` is called first
    so a malformed ID reports the registry's own diagnostic.
    """
    resolve_case_id(case_id)
    try:
        return _ORDINAL_BY_CASE_ID[case_id]
    except KeyError:  # pragma: no cover - resolve_case_id already rejects these
        raise ValueError(f"case id not in the frozen enumeration: {case_id}") from None


def case_id_for_ordinal(ordinal: int) -> str:
    """Inverse of :func:`case_ordinal`, range-checked."""
    if not (0 <= ordinal < A35_TOTAL_CASES):
        raise ValueError(
            f"case_ordinal {ordinal} outside [0, {A35_TOTAL_CASES})"
        )
    return _CASE_IDS[ordinal]


def search_seed(case_ordinal_value: int, k: int) -> int:
    """A3.5 section 8.1's injective ordinal seed.

    Both indices are bounded and the result is range-checked, raising rather
    than returning an out-of-band value -- exactly as
    ``rc3_provenance.smoke_seed`` and ``seed_band_registry.falsv2_seed`` do.
    """
    if not (0 <= case_ordinal_value < A35_TOTAL_CASES):
        raise ValueError(
            f"case_ordinal {case_ordinal_value} outside [0, {A35_TOTAL_CASES})"
        )
    if not (0 <= k < A35_SEEDS_PER_CASE):
        raise ValueError(f"k {k} outside [0, {A35_SEEDS_PER_CASE})")
    seed = A35_SEARCH_SEED_BASE + case_ordinal_value * A35_SEEDS_PER_CASE + k
    if not (A35_SEARCH_SEED_MIN <= seed <= A35_SEARCH_SEED_MAX):
        # Unreachable given the two checks above; defence in depth, mirroring
        # smoke_seed's own belt-and-braces range check.
        raise ValueError(f"seed {seed} escapes the A3.5 case-search band")
    return seed


def case_search_seeds(case_id: str) -> tuple[int, ...]:
    """The 30 frozen search seeds for one case, in ordinal order k = 0..29."""
    ordinal = case_ordinal(case_id)
    return tuple(search_seed(ordinal, k) for k in range(A35_SEEDS_PER_CASE))


def iter_all_search_seeds() -> Iterator[tuple[str, int, int]]:
    """Yield ``(case_id, k, seed)`` for all 11,400 production search seeds."""
    for ordinal, case_id in enumerate(_CASE_IDS):
        for k in range(A35_SEEDS_PER_CASE):
            yield case_id, k, search_seed(ordinal, k)


class SearchSeedInvariantError(RuntimeError):
    """A frozen A3.5 search-seed invariant does not hold."""


def _a35_band() -> SeedBand:
    for band in DECLARED_BANDS:
        if band.name == A35_BAND_NAME:
            return band
    raise SearchSeedInvariantError(  # pragma: no cover - registry is frozen
        f"{A35_BAND_NAME} is absent from the frozen seed-band registry"
    )


def verify_search_seed_invariants() -> dict[str, object]:
    """A3.5 section 8.1's mandatory guard, hard-failing.

    Asserts, in the amendment's own words: 11,400 distinct seeds;
    injectivity; range containment; positivity; int32 safety; and pairwise
    disjointness against **every** declared band, **by extent comparison and
    not by realised-seed intersection**.

    Implementation obligation 10 requires this to run before any manifest is
    written.  It raises :class:`SearchSeedInvariantError`; it never warns and
    never repairs.
    """
    expected_total = A35_TOTAL_CASES * A35_SEEDS_PER_CASE

    seeds: list[int] = []
    seen: dict[int, tuple[str, int]] = {}
    for case_id, k, seed in iter_all_search_seeds():
        if seed in seen:
            raise SearchSeedInvariantError(
                f"seed {seed} produced by both {seen[seed]} and ({case_id}, {k}): "
                f"the ordinal map is not injective"
            )
        seen[seed] = (case_id, k)
        seeds.append(seed)

    if len(seeds) != expected_total:
        raise SearchSeedInvariantError(
            f"expected {expected_total} seeds, derived {len(seeds)}"
        )
    if len(set(seeds)) != expected_total:  # pragma: no cover - injectivity proven above
        raise SearchSeedInvariantError("derived seeds are not distinct")

    lo, hi = min(seeds), max(seeds)
    if lo != A35_SEARCH_SEED_MIN or hi != A35_SEARCH_SEED_MAX:
        raise SearchSeedInvariantError(
            f"realised extent [{lo}, {hi}] is not the declared band "
            f"[{A35_SEARCH_SEED_MIN}, {A35_SEARCH_SEED_MAX}]"
        )
    if hi - lo + 1 != expected_total:
        raise SearchSeedInvariantError(  # pragma: no cover - arithmetic identity
            "the band is not densely occupied by the ordinal map"
        )
    if lo <= 0:
        raise SearchSeedInvariantError("seeds must be strictly positive")
    if hi > SIGNED_32BIT_MAX:
        raise SearchSeedInvariantError(
            f"seed {hi} exceeds the signed 32-bit max {SIGNED_32BIT_MAX}; "
            f"Julia consumes these as PySRRegressor(random_state=int(seed))"
        )

    # The declared governance entry must agree with this module's constants,
    # so the registry and the implementation cannot drift apart silently.
    declared = _a35_band()
    if (declared.min_seed, declared.max_seed) != (
        A35_SEARCH_SEED_MIN,
        A35_SEARCH_SEED_MAX,
    ):
        raise SearchSeedInvariantError(
            f"{A35_BAND_NAME} declares [{declared.min_seed}, {declared.max_seed}] "
            f"but this module derives [{A35_SEARCH_SEED_MIN}, {A35_SEARCH_SEED_MAX}]"
        )

    # Disjointness by declared extent, never by realised-seed intersection.
    guards: dict[str, int] = {}
    for band in DECLARED_BANDS:
        if band.name == A35_BAND_NAME:
            continue
        if band.min_seed <= A35_SEARCH_SEED_MAX and A35_SEARCH_SEED_MIN <= band.max_seed:
            raise SearchSeedInvariantError(
                f"A3.5 case-search band [{A35_SEARCH_SEED_MIN}, "
                f"{A35_SEARCH_SEED_MAX}] overlaps declared band {band.name} "
                f"[{band.min_seed}, {band.max_seed}] by extent"
            )
        guards[band.name] = (
            A35_SEARCH_SEED_MIN - band.max_seed
            if band.max_seed < A35_SEARCH_SEED_MIN
            else band.min_seed - A35_SEARCH_SEED_MAX
        )

    return {
        "total_seeds": expected_total,
        "distinct_seeds": len(set(seeds)),
        "cases": A35_TOTAL_CASES,
        "seeds_per_case": A35_SEEDS_PER_CASE,
        "band_min": A35_SEARCH_SEED_MIN,
        "band_max": A35_SEARCH_SEED_MAX,
        "signed_32bit_headroom": SIGNED_32BIT_MAX - A35_SEARCH_SEED_MAX,
        "guards_by_band": dict(sorted(guards.items())),
        "disjointness_method": "declared_extent_comparison",
    }
