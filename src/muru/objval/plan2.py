"""The frozen fresh-world plan: exactly which validation worlds exist.

Frozen by `TYPE2_VALIDATION_PREREGISTRATION.md`. The nested run arithmetic in
`RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md` is computed FROM this file, so the
budget cannot drift from what is executed and loops cannot be miscounted by
hand — the failure that cost Phase 2 (`BACKLOG.md` I4) and that Phase 3 fixed
the same way.

Seed policy
-----------
Symbolic seeds live in a band provably disjoint from Phase 3's. Phase 3 used
`900000 + sha256(world_id)[:3] * 100 + k`, whose realized range was
[11 258 400, 1 678 023 829] and whose theoretical maximum is 1 678 621 529. This
study starts at 1 700 000 000 and its maximum is 2 100 000 029, which is inside
the signed 32-bit range the engine accepts. `tests/test_ov_freshness.py` asserts
both the band separation and the emptiness of the realized intersection.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from muru.objval.generators2 import NULL_CONSTRUCTIONS2

PLAN2_VERSION = "ov-plan-1.0.0"

N_SEEDS = 30                       # master plan 13.4 minimum, unchanged

# --- symbolic seed band, disjoint from Phase 3 -------------------------------
OV_SEED_BASE = 1_700_000_000
OV_SEED_SPREAD = 4_000_000
P3_SEED_THEORETICAL_MAX = 900_000 + 16_777_215 * 100 + 29


def seed_list2(world_id: str) -> list[int]:
    """Deterministic per-world seed list in the fresh band."""
    h = int.from_bytes(hashlib.sha256(world_id.encode()).digest()[:4], "big")
    base = OV_SEED_BASE + (h % OV_SEED_SPREAD) * 100
    return [base + k for k in range(N_SEEDS)]


# --- world counts ------------------------------------------------------------
# Null calibration. Phase 3 used 40 and recorded the consequence as an open
# issue (`BACKLOG.md` I8): a 95th percentile from 40 worlds rests on its top two
# or three, giving intervals so wide the table could not adjudicate a marginal
# candidate. 100 worlds puts the quantile on its top five.
N_NULL_CAL = 100

# The master plan's own requirement: 100 null replicates for the K6-equivalent
# false-positive gate (§18.3, §20 Phase 3 acceptance).
N_G4 = 100
N_G4M = 30

# Positive controls.
N_G1A_PER_REGIME = 2               # analytic sanity; cheap, and only a sanity anchor
G1A_REGIMES = ("low", "moderate", "adverse")
# The governing gate is stated on the MODERATE regime, so it carries twice the
# replicates: a rate of 0.80 estimated from 10 worlds resolves only to 0.1.
G1B_REPLICATES = {"low": 10, "moderate": 20, "adverse": 10}
N_G1C = 10                         # near-degeneracy challenge, moderate regime

# Refusal worlds.
N_G2 = N_G3 = N_G5 = 8
GC_CUTOFFS = (30.0, 50.0, 80.0)
N_GC_PER_CUTOFF = 3
N_GRT = 4


@dataclass(frozen=True)
class WorldSpec2:
    block: str
    family: str
    replicate: int
    noise_regime: str
    cutoff_da: float | None = None
    null_construction: str | None = None

    @property
    def world_id(self) -> str:
        if self.null_construction:
            return f"OV|NULL|{self.null_construction}|r{self.replicate:03d}"
        wid = f"OV|{self.family}|r{self.replicate:03d}|{self.noise_regime}"
        if self.cutoff_da is not None:
            wid += f"|cut{self.cutoff_da:g}"
        return wid


def all_worlds2() -> list[WorldSpec2]:
    """Every world this study runs, in a fixed order."""
    w: list[WorldSpec2] = []
    for i in range(N_NULL_CAL):
        w.append(WorldSpec2("NCAL", "NULL", i, "moderate",
                            null_construction=NULL_CONSTRUCTIONS2[
                                i % len(NULL_CONSTRUCTIONS2)]))
    for i in range(N_G4):
        w.append(WorldSpec2("G4", "G4", i, "moderate"))
    for i in range(N_G4M):
        w.append(WorldSpec2("G4M", "G4M", i, "moderate"))

    for regime in G1A_REGIMES:
        for i in range(N_G1A_PER_REGIME):
            w.append(WorldSpec2("G1A", "G1A", i, regime))
    for regime, n in G1B_REPLICATES.items():
        for i in range(n):
            w.append(WorldSpec2("G1B", "G1B", i, regime))
    for i in range(N_G1C):
        w.append(WorldSpec2("G1C", "G1C", i, "moderate"))

    for i in range(N_G2):
        w.append(WorldSpec2("G2", "G2", i, "moderate"))
    for i in range(N_G3):
        w.append(WorldSpec2("G3", "G3", i, "moderate"))
    for i in range(N_G5):
        w.append(WorldSpec2("G5", "G5", i, "moderate"))
    for cut in GC_CUTOFFS:
        for i in range(N_GC_PER_CUTOFF):
            w.append(WorldSpec2("GC", "GC", i, "moderate", cutoff_da=cut))
    for i in range(N_GRT):
        w.append(WorldSpec2("GRT", "GRT", i, "moderate"))
    return w


# --- independent-engine corroboration arm ------------------------------------
# Pre-registered limited scope, frozen before any result is seen. Master plan
# 13.3 makes the second engine a comparison arm on T2, not a second full engine.
# Scope is chosen to cover both structured worlds (where corroboration is the
# scientific question) and nulls (where agreement about noise is the control).
GPLEARN_BLOCKS2 = ("G1B", "G1C", "G3")
N_GPLEARN_G4 = 30
N_GPLEARN_SEEDS = 10


def gplearn_worlds2() -> list[WorldSpec2]:
    out = [s for s in all_worlds2() if s.block in GPLEARN_BLOCKS2]
    out += [s for s in all_worlds2() if s.block == "G4"][:N_GPLEARN_G4]
    return out


def run_counts2() -> dict:
    """Explicit nested arithmetic. Products, never sums."""
    worlds = all_worlds2()
    by_block: dict[str, int] = {}
    for s in worlds:
        by_block[s.block] = by_block.get(s.block, 0) + 1
    pysr = {b: n * N_SEEDS for b, n in by_block.items()}
    gp = len(gplearn_worlds2())
    return {
        "plan_version": PLAN2_VERSION,
        "worlds_by_block": by_block,
        "n_worlds": len(worlds),
        "n_seeds_per_world": N_SEEDS,
        "pysr_runs_by_block": pysr,
        "pysr_runs_total": sum(pysr.values()),
        "gplearn_worlds": gp,
        "gplearn_seeds_per_world": N_GPLEARN_SEEDS,
        "gplearn_runs_total": gp * N_GPLEARN_SEEDS,
        "expansion": {b: f"{n} worlds x {N_SEEDS} seeds = {n * N_SEEDS} runs"
                      for b, n in by_block.items()},
        "gplearn_expansion": (f"{gp} worlds x {N_GPLEARN_SEEDS} seeds = "
                              f"{gp * N_GPLEARN_SEEDS} runs"),
    }
