"""The frozen governed discovery protocol.

One code path, used identically for every synthetic world, for the null
calibration, and — after Phase 3 closes — for Phase 4. Nothing in it may be
changed after seeing recovery performance without a `DEVIATIONS_P3.md` entry
and a full recalibration.

This module reads data. It never reads a planted law.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

from muru.discovery import engine, equivalence, grammar
from muru.discovery.estimate import CollapseFit, fit_collapse

PROTOCOL_VERSION = "p3-protocol-1.0.0"

FEATURES = ("precursor_mz", "total_atom_count", "rotatable_bonds", "ring_count",
            "aromatic_ring_count", "rdbe", "tpsa", "heteroatom_fraction",
            "n_N", "n_O", "n_S", "n_halogen")

SCALE = {"precursor_mz": 500.0, "total_atom_count": 37.0, "rotatable_bonds": 4.0,
         "ring_count": 2.0, "aromatic_ring_count": 2.0, "rdbe": 8.5,
         "tpsa": 54.5, "heteroatom_fraction": 0.25, "n_N": 2.0, "n_O": 2.0,
         "n_S": 1.0, "n_halogen": 1.0}

# The Phase 2 mass block, removed together (DESCRIPTORS.md): dropping the named
# mass variable alone leaves its proxies in place and understates how much of
# the effect mass carries.
MASS_BLOCK = ("precursor_mz", "total_atom_count", "rdbe")

# Frozen seed schedule: 30 symbolic seeds (master plan 13.4 minimum).
N_SEEDS = 30
SEED_BASE = 900_000


def seed_list(world_id: str) -> list[int]:
    """Deterministic per-world seed list, frozen before any governed run."""
    h = int.from_bytes(hashlib.sha256(world_id.encode()).digest()[:3], "big")
    return [SEED_BASE + h * 100 + k for k in range(N_SEEDS)]


# --- ranking rule (frozen) ---------------------------------------------------
# Master plan 13.4: "The reported candidate is chosen by the complexity elbow,
# not by best fit." Elbow = the SMALLEST complexity whose validation R^2 is
# within ELBOW_TOL of the best achieved on the front.
ELBOW_TOL = 0.01

# Master plan L4: recovered by at least 20 of 30 seeds.
MIN_SELECTION_FRACTION = 20.0 / 30.0


@dataclass
class WorldData:
    world_id: str
    variables: list[str]
    X: np.ndarray                 # dimensionless descriptors, compound order
    y: np.ndarray                 # T2 target: estimated collapse scale g_hat
    w: np.ndarray                 # inverse-variance weights
    groups: np.ndarray            # scaffold group per compound
    split: np.ndarray             # 'train' | 'valid' | 'test'
    fit: CollapseFit
    long: pd.DataFrame
    cov: pd.DataFrame

    def part(self, name: str):
        m = self.split == name
        return self.X[m], self.y[m], self.w[m]


def group_split(groups: np.ndarray, world_id: str,
                fracs=(0.60, 0.20, 0.20)) -> np.ndarray:
    """Scaffold-group-disjoint three-way split.

    Whole trajectories move together and no scaffold group straddles a
    boundary, so the held-out parts represent unseen chemistry. Groups are
    filled largest-first into the currently smallest part, the same rule Phase 2
    used, so one large scaffold cannot dominate a partition.
    """
    seed = int.from_bytes(hashlib.sha256(("split|" + world_id).encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    uniq, counts = np.unique(groups, return_counts=True)
    order = np.argsort(-counts + rng.random(len(counts)) * 0.5)
    targets = np.array(fracs) * len(groups)
    filled = np.zeros(3)
    assign: dict[str, int] = {}
    for gi in order:
        k = int(np.argmax(targets - filled))
        assign[uniq[gi]] = k
        filled[k] += counts[gi]
    names = np.array(["train", "valid", "test"])
    return names[np.array([assign[g] for g in groups])]


def build_world_data(world_id: str, long: pd.DataFrame, cov: pd.DataFrame,
                     features: tuple[str, ...] = FEATURES) -> WorldData:
    """Estimate the collapse scale and assemble the T2 search problem."""
    fit = fit_collapse(long)
    cov = cov.set_index("group_key").loc[fit.compounds].reset_index()
    X = np.column_stack([cov[c].to_numpy(float) / SCALE[c] for c in features])
    groups = cov.scaffold_group.to_numpy()
    return WorldData(world_id=world_id, variables=list(features), X=X,
                     y=fit.g_hat.copy(), w=fit.weights.copy(), groups=groups,
                     split=group_split(groups, world_id), fit=fit,
                     long=long, cov=cov)


# --------------------------------------------------------------------------
# one seed
# --------------------------------------------------------------------------
def run_seed(wd: WorldData, seed: int, which: str = "pysr") -> list[engine.Candidate]:
    Xtr, ytr, wtr = wd.part("train")
    Xva, yva, wva = wd.part("valid")
    fn = engine.run_pysr if which == "pysr" else engine.run_gplearn
    return fn(Xtr, ytr, wtr, Xva, yva, wva, wd.variables, seed)


def elbow_pick(cands: list[engine.Candidate]) -> engine.Candidate | None:
    """Complexity elbow over one seed's Pareto front."""
    ok = [c for c in cands if c.valid and np.isfinite(c.valid_r2)
          and c.complexity <= grammar.MAX_COMPLEXITY]
    if not ok:
        return None
    best = max(c.valid_r2 for c in ok)
    near = [c for c in ok if c.valid_r2 >= best - ELBOW_TOL]
    return sorted(near, key=lambda c: (c.complexity, c.expr_str))[0]


def best_r2_by_complexity(cands: list[engine.Candidate],
                          max_c: int = grammar.MAX_COMPLEXITY) -> np.ndarray:
    """Best validation R^2 achievable at complexity <= c, for c = 1..max_c.

    This is the statistic the null calibration is built from, so a real
    candidate is always compared against nulls at its OWN complexity.
    """
    out = np.full(max_c + 1, -np.inf)
    for c in cands:
        if not c.valid or not np.isfinite(c.valid_r2):
            continue
        cc = min(c.complexity, max_c)
        out[cc] = max(out[cc], c.valid_r2)
    return np.maximum.accumulate(out)


# --------------------------------------------------------------------------
# across seeds
# --------------------------------------------------------------------------
@dataclass
class WorldResult:
    world_id: str
    engine: str
    candidate: engine.Candidate | None
    stability: dict
    per_seed_best: list[engine.Candidate]
    r2_by_complexity_max: np.ndarray     # max over seeds, per complexity
    n_seeds_run: int


def aggregate(wd: WorldData, per_seed: dict[int, list[engine.Candidate]],
              which: str = "pysr") -> WorldResult:
    """Combine seeds: elbow per seed, then the dominant expression family."""
    bests, curves = [], []
    for s in sorted(per_seed):
        cands = per_seed[s]
        curves.append(best_r2_by_complexity(cands))
        b = elbow_pick(cands)
        if b is not None:
            bests.append(b)

    curve = (np.max(np.vstack(curves), axis=0) if curves
             else np.full(grammar.MAX_COMPLEXITY + 1, -np.inf))

    D = equivalence.latin_hypercube(
        equivalence.domain_bounds(wd.X, wd.variables), wd.variables,
        equivalence.N_LHC_CLUSTER, seed=7)
    stab = equivalence.selection_frequency(bests, wd.variables, D)

    cand = None
    if bests and stab["top_index"] is not None:
        clusters = equivalence.cluster_by_fingerprint(bests, wd.variables, D)
        sizes = [len(c) for c in clusters]
        members = clusters[int(np.argmax(sizes))]
        cand = sorted((bests[i] for i in members),
                      key=lambda c: (c.complexity, -c.valid_r2, c.expr_str))[0]

    return WorldResult(world_id=wd.world_id, engine=which, candidate=cand,
                       stability=stab, per_seed_best=bests,
                       r2_by_complexity_max=curve, n_seeds_run=len(per_seed))


# --------------------------------------------------------------------------
# acceptance
# --------------------------------------------------------------------------
def is_mass_only(support: tuple[str, ...] | list[str]) -> bool:
    return bool(support) and set(support) <= set(MASS_BLOCK)


def has_non_mass_support(support: tuple[str, ...] | list[str]) -> bool:
    return bool(set(support) - set(MASS_BLOCK))


def accept(result: WorldResult, null_threshold: np.ndarray,
           harness: dict | None) -> dict:
    """The frozen acceptance rule. All conditions are necessary."""
    c = result.candidate
    if c is None:
        return {"accepted": False, "reason": "no valid candidate",
                "conditions": {}}
    thr = float(null_threshold[min(c.complexity, len(null_threshold) - 1)])
    cond = {
        "exceeds_null_threshold": bool(c.valid_r2 > thr),
        "seed_stability": bool(result.stability["fraction"] >= MIN_SELECTION_FRACTION),
        "complexity_within_budget": bool(c.complexity <= grammar.MAX_COMPLEXITY),
        "numerically_valid": bool(c.invalid_fraction <= grammar.MAX_INVALID_FRACTION),
        "falsification_passed": bool(harness["passed"]) if harness else False,
    }
    return {
        "accepted": all(cond.values()),
        "conditions": cond,
        "null_threshold": thr,
        "valid_r2": c.valid_r2,
        "complexity": c.complexity,
        "selection_fraction": result.stability["fraction"],
        "support": list(c.support),
        "expr": c.expr_str,
        "claims_non_mass_structure": has_non_mass_support(c.support),
        "mass_only": is_mass_only(c.support),
    }
