"""FRESH HOLDOUT — population plan and world construction (namespace FH).

The scientific generators are the ESTABLISHED MURU generators
(`muru.objval.generators2` / `muru.objval.truth2`), unchanged. Freshness comes
from three mechanically-verified separations:

* a replicate namespace (`FH_REP_BASE = 700000`) never used by any historical
  MURU population, which changes `world_seed2`'s sha256 input and therefore
  every drawn constant, every nuisance draw, every noise realisation and every
  dropout mask;
* a world-id namespace prefix `FH|`, disjoint from `OV|` and from every
  Phase 1-3 identifier;
* a symbolic-seed band [2_110_000_000, 2_147_483_647) that lies strictly above
  the objective-validation band (max 2_100_000_029) and strictly above the
  Phase 3 theoretical max (1_678_621_529), while remaining inside signed int32.

Nothing in this module is imported by any selection, gating or scoring code.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

FH_PLAN_VERSION = "fh-plan-1.0.0"
FH_REP_BASE = 700_000
N_SEEDS = 6

FH_SEED_BASE = 2_110_000_000
FH_SEED_SPREAD = 370_000
INT32_MAX = 2_147_483_647
OV_SEED_THEORETICAL_MAX = 2_100_000_029
P3_SEED_THEORETICAL_MAX = 1_678_621_529

NULL_CONSTRUCTIONS = (
    "target_permuted_across_compounds",
    "target_permuted_across_energy_within_compound",
    "descriptors_permuted_across_compounds",
    "gaussian_targets_with_observed_variance",
)

POSITIVE_BLOCKS = {"G1A", "G1B", "G1C"}
NULL_BLOCKS = {"G4", "G4M", "NCAL"}
REFUSAL_BLOCKS = {"G2", "G3", "G5", "GC", "GRT"}


def category(block: str) -> str:
    if block in POSITIVE_BLOCKS:
        return "positive"
    if block in NULL_BLOCKS:
        return "null"
    return "refusal"


def fh_seed_list(world_id: str) -> list[int]:
    h = int.from_bytes(hashlib.sha256(world_id.encode()).digest()[:4], "big")
    base = FH_SEED_BASE + (h % FH_SEED_SPREAD) * 100
    return [base + k for k in range(N_SEEDS)]


@dataclass(frozen=True)
class FHSpec:
    block: str
    family: str
    index: int                       # 0-based within the block
    noise_regime: str
    cutoff_da: float | None = None
    null_construction: str | None = None

    @property
    def replicate(self) -> int:
        return FH_REP_BASE + self.index

    @property
    def world_id(self) -> str:
        if self.null_construction:
            return (f"FH|NULL|{self.null_construction}|"
                    f"r{self.replicate:06d}")
        wid = f"FH|{self.family}|r{self.replicate:06d}|{self.noise_regime}"
        if self.cutoff_da is not None:
            wid += f"|cut{self.cutoff_da:g}"
        return wid


# ---------------------------------------------------------------- the plan --
# 96 worlds: 48 positive, 36 null, 12 refusal/challenge.
N_G1A_PER_REGIME = 2
G1A_REGIMES = ("low", "moderate", "adverse")
G1B_REPLICATES = {"low": 10, "moderate": 14, "adverse": 10}
N_G1C = 8

N_NCAL_PER_CONSTRUCTION = 4        # 16 total
N_G4 = 12
N_G4M = 8

N_G2 = N_G3 = N_G5 = 3
GC_CUTOFFS = (30.0, 80.0)
N_GC_PER_CUTOFF = 1
N_GRT = 1


def all_worlds() -> list[FHSpec]:
    w: list[FHSpec] = []
    # --- positive ---------------------------------------------------------
    i = 0
    for regime in G1A_REGIMES:
        for _ in range(N_G1A_PER_REGIME):
            w.append(FHSpec("G1A", "G1A", i, regime)); i += 1
    i = 0
    for regime in ("low", "moderate", "adverse"):
        for _ in range(G1B_REPLICATES[regime]):
            w.append(FHSpec("G1B", "G1B", i, regime)); i += 1
    for i in range(N_G1C):
        w.append(FHSpec("G1C", "G1C", i, "moderate"))
    # --- null -------------------------------------------------------------
    i = 0
    for c in NULL_CONSTRUCTIONS:
        for _ in range(N_NCAL_PER_CONSTRUCTION):
            w.append(FHSpec("NCAL", "NULL", i, "moderate", null_construction=c))
            i += 1
    for i in range(N_G4):
        w.append(FHSpec("G4", "G4", i, "moderate"))
    for i in range(N_G4M):
        w.append(FHSpec("G4M", "G4M", i, "moderate"))
    # --- refusal / challenge ---------------------------------------------
    for i in range(N_G2):
        w.append(FHSpec("G2", "G2", i, "moderate"))
    for i in range(N_G3):
        w.append(FHSpec("G3", "G3", i, "moderate"))
    for i in range(N_G5):
        w.append(FHSpec("G5", "G5", i, "moderate"))
    i = 0
    for cut in GC_CUTOFFS:
        for _ in range(N_GC_PER_CUTOFF):
            w.append(FHSpec("GC", "GC", i, "moderate", cutoff_da=cut)); i += 1
    for i in range(N_GRT):
        w.append(FHSpec("GRT", "GRT", i, "moderate"))
    return w


def build_fh_world(spec: FHSpec, cov=None):
    """Build one fresh world with the ESTABLISHED generator, then stamp the
    FH identity. No generator logic is altered."""
    from muru.objval.generators2 import build_null_world2, build_world2
    from muru.synth.generators import load_dev_covariates
    if cov is None and spec.family != "G1A":
        cov = load_dev_covariates()
    if spec.null_construction:
        w = build_null_world2(spec.replicate, spec.null_construction, cov)
    else:
        w = build_world2(spec.family, spec.replicate, spec.noise_regime,
                         cov=None if spec.family == "G1A" else cov,
                         cutoff_da=spec.cutoff_da)
    w.world_id = spec.world_id
    return w


# ---- deterministic outcome-blind reduction order (time-budget fallback) ----
def reduction_rank(spec: FHSpec) -> str:
    """Sort key used ONLY by the pre-scoring time-budget fallback. Depends on
    the frozen world identity alone."""
    return hashlib.sha256(("fh-reduce|" + spec.world_id).encode()).hexdigest()
