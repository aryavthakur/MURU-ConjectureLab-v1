"""The frozen Phase 3 experiment plan: exactly which worlds exist.

Frozen by `PHASE3_PREREGISTRATION.md`. The run-count arithmetic in
`RUNTIME_BUDGET_P3.md` is computed FROM this file by
`scripts/t3_01_runtime_budget.py`, so the budget cannot drift from what is
actually executed and nested loops cannot be miscounted by hand — the failure
that cost Phase 2 (BACKLOG I4).
"""
from __future__ import annotations

from dataclasses import dataclass

from muru.synth.generators import NULL_CONSTRUCTIONS

N_SEEDS = 30                      # master plan 13.4 minimum

# G4 is the master plan's own requirement: 100 null replicates for K6.
N_G4 = 100
# Calibration worlds, disjoint from G4 so the threshold is not fitted to the
# data that measures the false-positive rate.
N_NULL_CAL = 40
# Supplementary mass-conditional null, matched to the Phase 2 question.
N_G4M = 30

N_G1_PER_REGIME = 10
G1_REGIMES = ("low", "moderate", "adverse")
N_G2 = N_G3 = N_G5 = 8
GC_CUTOFFS = (30.0, 50.0, 80.0)
N_GC_PER_CUTOFF = 3
N_GRT = 4
N_GA = 3


@dataclass(frozen=True)
class WorldSpec:
    block: str
    family: str
    replicate: int
    noise_regime: str
    cutoff_da: float | None = None
    null_construction: str | None = None

    @property
    def world_id(self) -> str:
        if self.null_construction:
            return f"NULL|{self.null_construction}|r{self.replicate:03d}"
        wid = f"{self.family}|r{self.replicate:03d}|{self.noise_regime}"
        if self.cutoff_da is not None:
            wid += f"|cut{self.cutoff_da:g}"
        return wid


def all_worlds() -> list[WorldSpec]:
    """Every world Phase 3 runs, in a fixed order."""
    w: list[WorldSpec] = []

    # null calibration: cycle the four 13.6 constructions so each contributes
    for i in range(N_NULL_CAL):
        w.append(WorldSpec("NCAL", "NULL", i, "moderate",
                           null_construction=NULL_CONSTRUCTIONS[i % len(NULL_CONSTRUCTIONS)]))

    for i in range(N_G4):
        w.append(WorldSpec("G4", "G4", i, "moderate"))
    for i in range(N_G4M):
        w.append(WorldSpec("G4M", "G4M", i, "moderate"))

    for regime in G1_REGIMES:
        for i in range(N_G1_PER_REGIME):
            w.append(WorldSpec("G1", "G1B", i, regime))

    for i in range(N_G2):
        w.append(WorldSpec("G2", "G2", i, "moderate"))
    for i in range(N_G3):
        w.append(WorldSpec("G3", "G3", i, "moderate"))
    for i in range(N_G5):
        w.append(WorldSpec("G5", "G5", i, "moderate"))

    for cut in GC_CUTOFFS:
        for i in range(N_GC_PER_CUTOFF):
            w.append(WorldSpec("GC", "GC", i, "moderate", cutoff_da=cut))

    for i in range(N_GRT):
        w.append(WorldSpec("GRT", "GRT", i, "moderate"))
    for i in range(N_GA):
        w.append(WorldSpec("GA", "GA", i, "moderate"))
    return w


# gplearn comparison arm: pre-registered LIMITED representative scope, frozen
# before any result was seen. Full duplication of every PySR experiment would
# multiply compute without additional scientific value (master plan 13.3 makes
# gplearn a comparison arm on T2, not a second full engine).
GPLEARN_BLOCKS = ("G1", "G3")
N_GPLEARN_G4 = 30
N_GPLEARN_SEEDS = 10


def gplearn_worlds() -> list[WorldSpec]:
    out = [s for s in all_worlds() if s.block in GPLEARN_BLOCKS]
    out += [s for s in all_worlds() if s.block == "G4"][:N_GPLEARN_G4]
    return out


def run_counts() -> dict:
    """Explicit nested arithmetic. Products, never sums."""
    worlds = all_worlds()
    by_block: dict[str, int] = {}
    for s in worlds:
        by_block[s.block] = by_block.get(s.block, 0) + 1
    pysr = {b: n * N_SEEDS for b, n in by_block.items()}
    gp_worlds = len(gplearn_worlds())
    return {
        "worlds_by_block": by_block,
        "n_worlds": len(worlds),
        "n_seeds_per_world": N_SEEDS,
        "pysr_runs_by_block": pysr,
        "pysr_runs_total": sum(pysr.values()),
        "gplearn_worlds": gp_worlds,
        "gplearn_seeds_per_world": N_GPLEARN_SEEDS,
        "gplearn_runs_total": gp_worlds * N_GPLEARN_SEEDS,
        "expansion": {
            b: f"{n} worlds x {N_SEEDS} seeds = {n * N_SEEDS} runs"
            for b, n in by_block.items()},
    }
