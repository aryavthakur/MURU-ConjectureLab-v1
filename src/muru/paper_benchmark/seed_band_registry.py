"""A3.5 Session 3, Part H: centralized seed-band governance registry.

ENGINEERING / GOVERNANCE HARDENING ONLY. This module changes no science: it
declares every seed band this repository defines (by MIN/MAX envelope, each
independently re-derived from frozen source by formula, not copied from any
prior audit document -- see ``audit/MURU_A3_5_SEED_BAND_INVENTORY.md`` for
the full inventory and per-band citations) and checks every pair for
interval overlap.

It imports (read-only) constants from the frozen modules that already
compute a band, so this registry stays byte-identical to whatever those
modules actually do at runtime rather than drifting from a hand-copied
snapshot. Two bands exist only as frozen governance-document text and have
no implementing module yet (the reserved A3.5 case-search band and the
falsification-calibration-v1 band); those are declared as literals with a
document citation, clearly marked unimplemented.

Does NOT modify, monkeypatch, or import mutable state from any
A3.1/A3.2/A3.3/A3.4/RC3/RC4-frozen file. Purely additive.

Known, disclosed, pre-existing collision
-----------------------------------------
``rc3_provenance.assert_seed_band_separation`` only ever compares the
RC3-smoke band against the PB/A3.2 calibration band; it has never imported
or checked anything from ``objval/plan2``. Independently re-verified here:
RC3 smoke's envelope ``[1,900,000,000, 1,900,999,999]`` sits entirely inside
objval/plan2's declared envelope ``[1,700,000,000, 2,099,999,929]`` (see
``audit/MURU_A3_5_DECISION_2_CALIBRATION_RESULT.md`` section 1.2). This is a
pre-existing property of already-frozen engineering code, outside A3.5's
mandate to alter -- it is NOT fixed here. It is declared in
``ACKNOWLEDGED_COLLISIONS`` below so it stays checkable and visible instead
of silently going undetected again; any OTHER collision this registry finds
is treated as new and raises loudly.
"""
from __future__ import annotations

from dataclasses import dataclass

from muru.discovery.protocol import N_SEEDS as _P3_N_SEEDS
from muru.discovery.protocol import SEED_BASE as _P3_SEED_BASE
from muru.objval.plan2 import N_SEEDS as _OV_N_SEEDS
from muru.objval.plan2 import OV_SEED_BASE, OV_SEED_SPREAD
from muru.objval.plan2 import P3_SEED_THEORETICAL_MAX as _OV_DOCUMENTED_P3_MAX
from muru.paper_benchmark.rc3_provenance import (
    CALIBRATION_SEED_MAX,
    CALIBRATION_SEED_MIN,
    RC3_SMOKE_SEED_BASE,
    RC3_SMOKE_SEED_MAX,
    RC3_SMOKE_SEED_SPAN,
    SIGNED_32BIT_MAX,
)

__all__ = [
    "SIGNED_32BIT_MAX",
    "SeedBand",
    "Overlap",
    "DECLARED_BANDS",
    "ACKNOWLEDGED_COLLISIONS",
    "FALSV2_SEED_BASE",
    "FALSV2_SEED_CAPACITY",
    "FALSV2_SEED_MAX",
    "falsv2_seed",
    "find_overlaps",
    "unacknowledged_overlaps",
    "assert_governance_clean",
]


@dataclass(frozen=True)
class SeedBand:
    """One declared seed band, by inclusive integer envelope."""

    name: str
    min_seed: int
    max_seed: int
    source: str        # file:line (or document) citation for the definition
    derivation: str     # the formula, not just the two endpoints

    def __post_init__(self) -> None:
        if self.min_seed > self.max_seed:
            raise ValueError(f"{self.name}: min_seed > max_seed")
        if self.min_seed <= 0:
            raise ValueError(f"{self.name}: seeds must be strictly positive")
        if self.max_seed > SIGNED_32BIT_MAX:
            raise ValueError(f"{self.name}: max_seed exceeds signed 32-bit max")

    def overlaps(self, other: "SeedBand") -> bool:
        return self.min_seed <= other.max_seed and other.min_seed <= self.max_seed


# -----------------------------------------------------------------------
# The new falsification-v2 band (Part H's deliverable)
# -----------------------------------------------------------------------
#
# Placement reasoning (governance/disjointness only -- no performance
# tuning influenced this choice):
#
# The largest usable void between two already-occupied envelopes is
# [1,681,000,000 , 1,699,999,999] (19,000,000 integers), the gap between
# falsification-calibration-v1's max (1,680,999,999) and objval/plan2's min
# (1,700,000,000). A 1,000,000-capacity band centered in that void, based at
# 1,690,000,000, leaves a SYMMETRIC 9,000,000-integer guard on both sides --
# nine times the new band's own capacity on each side, mirroring the FC-v1
# band's own stated reasoning ("both neighboring gaps exceed the new band's
# own capacity"), so no plausible future widening of either neighbor
# (falsification-calibration-v1 or objval/plan2) can collide with it.
#
# This also structurally satisfies the "must never share a seed with v1"
# hygiene requirement: v2's envelope and v1's envelope do not even touch.

FALSV2_SEED_BASE = 1_690_000_000
FALSV2_SEED_CAPACITY = 1_000_000
FALSV2_SEED_MAX = FALSV2_SEED_BASE + FALSV2_SEED_CAPACITY - 1


def falsv2_seed(ordinal: int) -> int:
    """Injective ordinal -> seed map for falsification-v2, range-checked.

    Mirrors the frozen ``rc3_provenance.smoke_seed`` / the FC-v1
    ``fc_seed`` precedent: a provable bijection from a bounded ordinal range
    onto every integer of the band, not a hash bucket. ``ordinal`` is left
    to the caller's own indexing scheme (e.g. rung/family/draw composed into
    one bounded integer, exactly as FC-v1's own binding does) -- this
    function only owns the band arithmetic and its range check.
    """
    if not (0 <= ordinal < FALSV2_SEED_CAPACITY):
        raise ValueError(
            f"ordinal {ordinal} outside [0, {FALSV2_SEED_CAPACITY}) "
            f"for falsification-v2"
        )
    seed = FALSV2_SEED_BASE + ordinal
    if seed > FALSV2_SEED_MAX:  # unreachable given the check above; defense in depth
        raise ValueError(f"seed {seed} escapes the falsification-v2 band")
    return seed


# -----------------------------------------------------------------------
# The full inventory -- every band re-derived independently from frozen
# source by formula (see module docstrings of each imported module and
# audit/MURU_A3_5_SEED_BAND_INVENTORY.md for the full derivation prose).
# -----------------------------------------------------------------------

_P3_H_MAX = 2**24 - 1  # 3 bytes, big-endian, unsigned: sha256(world_id)[:3]
_PHASE3_DISCOVERY_MAX = _P3_SEED_BASE + _P3_H_MAX * 100 + (_P3_N_SEEDS - 1)
assert _PHASE3_DISCOVERY_MAX == _OV_DOCUMENTED_P3_MAX, (
    "phase3 discovery max re-derivation disagrees with plan2.py's own "
    "P3_SEED_THEORETICAL_MAX -- frozen source drifted"
)

_OV_H_MAX = OV_SEED_SPREAD - 1
_OBJVAL_PLAN2_MAX = OV_SEED_BASE + _OV_H_MAX * 100 + (_OV_N_SEEDS - 1)

_RC3_SMOKE_MAX_RECOMPUTED = RC3_SMOKE_SEED_BASE + RC3_SMOKE_SEED_SPAN - 1
assert _RC3_SMOKE_MAX_RECOMPUTED == RC3_SMOKE_SEED_MAX

DECLARED_BANDS: tuple[SeedBand, ...] = (
    SeedBand(
        name="phase3_discovery",
        min_seed=_P3_SEED_BASE,
        max_seed=_PHASE3_DISCOVERY_MAX,
        source="src/muru/discovery/protocol.py:38-45 (SEED_BASE, N_SEEDS, seed_list)",
        derivation=(
            "SEED_BASE=900_000; h=int.from_bytes(sha256(world_id)[:3],'big') "
            "in [0, 2**24-1]; seed = SEED_BASE + h*100 + k, k in [0, N_SEEDS=30)"
        ),
    ),
    SeedBand(
        name="objval_plan2",
        min_seed=OV_SEED_BASE,
        max_seed=_OBJVAL_PLAN2_MAX,
        source="src/muru/objval/plan2.py:30-38 (OV_SEED_BASE, OV_SEED_SPREAD, seed_list2)",
        derivation=(
            "OV_SEED_BASE=1_700_000_000; OV_SEED_SPREAD=4_000_000; "
            "h=int.from_bytes(sha256(world_id)[:4],'big'); "
            "base = OV_SEED_BASE + (h % OV_SEED_SPREAD)*100; "
            "seed = base + k, k in [0, N_SEEDS=30)"
        ),
    ),
    SeedBand(
        name="rc3_engineering_smoke",
        min_seed=RC3_SMOKE_SEED_BASE,
        max_seed=RC3_SMOKE_SEED_MAX,
        source=(
            "src/muru/paper_benchmark/rc3_provenance.py:103-134 "
            "(RC3_SMOKE_SEED_BASE, RC3_SMOKE_SEED_SPAN, RC3_SMOKE_SEEDS_PER_WORLD, "
            "smoke_seed)"
        ),
        derivation=(
            "RC3_SMOKE_SEED_BASE=1_900_000_000; RC3_SMOKE_SEEDS_PER_WORLD=1000; "
            "seed = BASE + world_index*1000 + seed_index, seed_index in [0, 1000) "
            "-- exact bijection over its accepted domain: densely occupies "
            "EVERY integer of the span, not merely some of them"
        ),
    ),
    SeedBand(
        name="a3_1_a3_2_structural_null_calibration",  # aka "PB calibration"
        min_seed=CALIBRATION_SEED_MIN,
        max_seed=CALIBRATION_SEED_MAX,
        source=(
            "src/muru/paper_benchmark/calibration_contract.py:79-97 "
            "(PB_SEED_BASE, PB_SEED_SPREAD, N_SEEDS_PER_WORLD, "
            "derive_calibration_seeds); re-exposed as CALIBRATION_SEED_MIN/MAX "
            "in src/muru/paper_benchmark/rc3_provenance.py:95-98"
        ),
        derivation=(
            "PB_SEED_BASE=2_110_000_000; PB_SEED_SPREAD=370_000; "
            "h=int.from_bytes(sha256(world_id)[:4],'big'); "
            "base = PB_SEED_BASE + (h % PB_SEED_SPREAD)*100; "
            "seed = base + k, k in [0, N_SEEDS_PER_WORLD=30). NOTE: this is "
            "the search-seed sub-namespace only -- A3.2's OTHER world-"
            "construction seeds (base-target permutation, scaffold split, "
            "null-family draw, law draw) go through "
            "generator.derive_seed(*parts), a full 64-bit SHA-256 hash "
            "domain-separated by string namespace, not a narrow int32 band, "
            "and are therefore out of scope for this envelope-collision "
            "system by construction (see audit/MURU_A3_5_SEED_BAND_INVENTORY.md)"
        ),
    ),
    SeedBand(
        name="a3_5_case_search_reserved",
        min_seed=2_100_000_000,
        max_seed=2_100_011_399,
        source=(
            "MURU_PAPER_BENCHMARK_AMENDMENT_A3_5.md:961-1006, section 8.1 "
            "(declared in frozen content-freeze governance text; NOT YET "
            "IMPLEMENTED in any .py source -- "
            "artifacts/paper_benchmark_amendment_a3_5.json "
            "seeds.new_module_required == true)"
        ),
        derivation=(
            "A35_SEARCH_SEED_BASE=2_100_000_000; A35_SEEDS_PER_CASE=30; "
            "search_seed(case_ordinal, k) = BASE + case_ordinal*30 + k, "
            "case_ordinal in [0, 380) [deterministic position in the frozen "
            "380-case registry enumeration], k in [0, 30) -- injective "
            "ordinal, reserved for the future case-search band"
        ),
    ),
    SeedBand(
        name="falsification_calibration_v1",
        min_seed=1_680_000_000,
        max_seed=1_680_999_999,
        source=(
            "audit/MURU_A3_5_DECISION_2_CALIBRATION_RESULT.md:47-56, section 1.1 "
            "(declared in a frozen investigation-result document; NOT YET "
            "IMPLEMENTED as a module-level constant in any .py source as of "
            "this session)"
        ),
        derivation=(
            "FC_SEED_BASE=1_680_000_000; FC_SEED_CAPACITY=1_000_000; "
            "fc_seed(ordinal) = BASE + ordinal, ordinal in [0, 1_000_000) -- "
            "injective; ordinal = rung_index*(N_FAMILIES*N_DRAWS) + "
            "family_index*N_DRAWS + draw_index, each sub-index range-checked "
            "before combining"
        ),
    ),
    SeedBand(
        name="falsification_calibration_v2",
        min_seed=FALSV2_SEED_BASE,
        max_seed=FALSV2_SEED_MAX,
        source="src/muru/paper_benchmark/seed_band_registry.py (this module, new -- Part H)",
        derivation=(
            "FALSV2_SEED_BASE=1_690_000_000; FALSV2_SEED_CAPACITY=1_000_000; "
            "falsv2_seed(ordinal) = BASE + ordinal, ordinal in [0, 1_000_000) "
            "-- injective bijection, mirrors fc_seed/smoke_seed. Placed in "
            "the 19,000,000-integer void between falsification_calibration_v1 "
            "and objval_plan2, leaving a symmetric 9,000,000-integer guard "
            "(9x its own capacity) to each neighbor"
        ),
    ),
)


# -----------------------------------------------------------------------
# Pairwise overlap checking, by full envelope arithmetic
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class Overlap:
    band_a: str
    band_b: str
    lo: int
    hi: int

    @property
    def extent(self) -> int:
        return self.hi - self.lo + 1


def find_overlaps(bands: tuple[SeedBand, ...] = DECLARED_BANDS) -> list[Overlap]:
    """Every pairwise overlap among ``bands``, by [min, max] interval
    arithmetic -- never by sampling or comparing realized seed values."""
    out: list[Overlap] = []
    for i in range(len(bands)):
        for j in range(i + 1, len(bands)):
            a, b = bands[i], bands[j]
            if a.overlaps(b):
                lo, hi = max(a.min_seed, b.min_seed), min(a.max_seed, b.max_seed)
                out.append(Overlap(a.name, b.name, lo, hi))
    return out


#: The one pre-existing, disclosed collision in already-frozen engineering
#: code (see module docstring). Declared here so this registry's checker
#: keeps reporting it forever, instead of it silently going undetected
#: again -- NOT to suppress or fix it.
ACKNOWLEDGED_COLLISIONS: frozenset[frozenset[str]] = frozenset({
    frozenset({"rc3_engineering_smoke", "objval_plan2"}),
})


def unacknowledged_overlaps(
    bands: tuple[SeedBand, ...] = DECLARED_BANDS,
) -> list[Overlap]:
    """Overlaps NOT already on ``ACKNOWLEDGED_COLLISIONS``.

    A non-empty result means a genuinely NEW collision was just found --
    this must never happen for the bands this module declares.
    """
    return [
        ov
        for ov in find_overlaps(bands)
        if frozenset({ov.band_a, ov.band_b}) not in ACKNOWLEDGED_COLLISIONS
    ]


def assert_governance_clean(
    bands: tuple[SeedBand, ...] = DECLARED_BANDS,
) -> dict[str, object]:
    """Raise loudly on any collision this registry does not already
    acknowledge. On success, returns a full report -- including the still-
    visible acknowledged collision, which is surfaced, never hidden.
    """
    all_overlaps = find_overlaps(bands)
    bad = unacknowledged_overlaps(bands)
    if bad:
        detail = "\n".join(
            f"  {ov.band_a} x {ov.band_b}: [{ov.lo}, {ov.hi}] "
            f"({ov.extent} integers)"
            for ov in bad
        )
        raise RuntimeError(f"UNACKNOWLEDGED seed-band collision(s) detected:\n{detail}")
    for band in bands:
        if band.max_seed > SIGNED_32BIT_MAX:
            raise RuntimeError(f"{band.name}: exceeds signed 32-bit max")
    return {
        "bands_checked": len(bands),
        "pairs_checked": len(bands) * (len(bands) - 1) // 2,
        "overlaps_found": [
            {"a": ov.band_a, "b": ov.band_b, "lo": ov.lo, "hi": ov.hi, "extent": ov.extent}
            for ov in all_overlaps
        ],
        "acknowledged_collisions": sorted(sorted(s) for s in ACKNOWLEDGED_COLLISIONS),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(assert_governance_clean(), indent=2))
