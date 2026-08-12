"""The Type 2 candidate-selection rule.

Phase 3's defect was specific and reproducible: the search put the planted law on
the Pareto front and the ranking rule then committed to ONE cheaper expression
per seed, discarding everything else. The repair here is not a different
tolerance. It is a different OBJECT: the rule retains the whole Pareto band and
reports an equation FAMILY, defined by variable support and scaling behaviour,
adjudicated across seeds.

The band tolerance is Phase 3's own 0.01, unchanged and deliberately so — the
tolerance was never the problem, and moving it would be exactly the arbitrary
substitution this study exists to avoid.

What changed:

* the band is RETAINED, not collapsed to its cheapest member;
* candidates are grouped by Type 2 family (support, sign, exponent,
  monotonicity, dense predictive agreement) instead of by exact numerical
  fingerprint;
* the number of distinct algebraic forms inside the reported family is measured
  and reported, so non-identifiability is a statable outcome rather than a
  silent choice of the simplest form.

This module reads candidates. It never reads a planted law.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from muru.discovery import equivalence, grammar
from muru.objval import equiv, signature

SELECT_VERSION = "ov-select-1.0.0"

# Phase 3's frozen elbow tolerance, reused UNCHANGED as the band half-width.
BAND_TOL = 0.01

# Master plan L4 / PHASE3_PREREGISTRATION §11: recovered by at least 20 of 30
# independent symbolic seeds. Unchanged.
MIN_SELECTION_FRACTION = 20.0 / 30.0

# Dense independently generated lattice for signature and within-world family
# comparison. 2,000 points is Phase 3's own within-world clustering size
# (`equivalence.N_LHC_CLUSTER`); the 10,000-point master-plan 13.5 lattice is
# used for the final truth adjudication, which runs once per world.
N_LATTICE = 2_000
LATTICE_SEED = 20260812


@dataclass
class BandMember:
    seed: int
    index: int
    expr_str: str
    expr: object
    complexity: int
    valid_r2: float
    train_r2: float
    invalid_fraction: float
    engine: str


def pareto_band(cands: list, tol: float = BAND_TOL) -> list:
    """Every candidate within `tol` validation R^2 of that seed's front best.

    Phase 3 took `min(complexity)` of exactly this set and threw the rest away.
    """
    ok = [c for c in cands if c.valid and np.isfinite(c.valid_r2)
          and c.complexity <= grammar.MAX_COMPLEXITY]
    if not ok:
        return []
    best = max(c.valid_r2 for c in ok)
    return [c for c in ok if c.valid_r2 >= best - tol]


def lattice(X: np.ndarray, variables: list[str], n: int = N_LATTICE,
            seed: int = LATTICE_SEED) -> np.ndarray:
    """Independently generated evaluation domain, never the training points."""
    return equivalence.latin_hypercube(
        equivalence.domain_bounds(X, variables), variables, n, seed=seed)


@dataclass
class Type2Result:
    world_id: str
    engine: str
    n_seeds: int
    families: list          # every family, largest first
    reported: dict | None   # the reported family, or None
    band_sizes: list
    lattice_n: int


def _order_key(m: BandMember):
    return (m.seed, m.complexity, m.expr_str)


def select(world_id: str, per_seed: dict[int, list], variables: list[str],
           X: np.ndarray, engine: str = "pysr",
           tol: float = BAND_TOL) -> Type2Result:
    """Run the frozen Type 2 selection rule over one world's 30 seeds."""
    D = lattice(X, variables)

    members: list[BandMember] = []
    band_sizes: list[int] = []
    for s in sorted(per_seed):
        band = pareto_band(per_seed[s], tol)
        band_sizes.append(len(band))
        for k, c in enumerate(band):
            members.append(BandMember(seed=s, index=k, expr_str=c.expr_str,
                                      expr=c.expr, complexity=c.complexity,
                                      valid_r2=float(c.valid_r2),
                                      train_r2=float(c.train_r2),
                                      invalid_fraction=float(c.invalid_fraction),
                                      engine=getattr(c, "engine", engine)))
    members.sort(key=_order_key)

    if not members:
        return Type2Result(world_id, engine, len(per_seed), [], None, band_sizes,
                           len(D))

    sigs, vals, oks = [], [], []
    for m in members:
        sigs.append(signature.signature(m.expr, variables, D))
        v, o = signature._eval(m.expr, variables, D)
        vals.append(v), oks.append(o)

    usable = [i for i in range(len(members)) if sigs[i]["usable"]]
    if not usable:
        return Type2Result(world_id, engine, len(per_seed), [], None, band_sizes,
                           len(D))

    clusters = equiv.cluster_families([sigs[i] for i in usable],
                                      [vals[i] for i in usable],
                                      [oks[i] for i in usable])
    clusters = [[usable[j] for j in c] for c in clusters]

    n_seeds = len(per_seed)
    families = []
    for c in clusters:
        seeds = sorted({members[i].seed for i in c})
        rep = min(c, key=lambda i: (members[i].complexity, -members[i].valid_r2,
                                    members[i].expr_str))
        # how many algebraically distinct forms sit inside this family?
        fclusters = equiv.cluster_functional([vals[i] for i in c],
                                             [oks[i] for i in c])
        exps = {}
        for v in sigs[rep]["effective_support_blocks"]:
            e = [sigs[i]["block_exponents"].get(v, np.nan) for i in c]
            e = [x for x in e if np.isfinite(x)]
            exps[v] = {"median": float(np.median(e)) if e else float("nan"),
                       "min": float(np.min(e)) if e else float("nan"),
                       "max": float(np.max(e)) if e else float("nan"),
                       "n": len(e)}
        # which variable-level supports the family's members actually used, so
        # proxy substitution inside a block is visible rather than hidden
        var_supports = sorted({tuple(sorted(sigs[i]["effective_support"]))
                               for i in c})
        families.append({
            "n_members": len(c),
            "n_seeds": len(seeds),
            "selection_fraction": len(seeds) / max(1, n_seeds),
            "representative": {
                "expr": members[rep].expr_str,
                "complexity": members[rep].complexity,
                "valid_r2": members[rep].valid_r2,
                "train_r2": members[rep].train_r2,
                "invalid_fraction": members[rep].invalid_fraction,
                "seed": members[rep].seed,
                "engine": members[rep].engine,
            },
            "effective_support": sigs[rep]["effective_support"],
            "symbolic_support": sigs[rep]["symbolic_support"],
            "signs": sigs[rep]["signs"],
            "monotone": sigs[rep]["monotone"],
            "exponents": sigs[rep]["exponents"],
            "effective_support_blocks": sigs[rep]["effective_support_blocks"],
            "block_exponents": sigs[rep]["block_exponents"],
            "block_signs": sigs[rep]["block_signs"],
            "variable_supports_in_family": [list(x) for x in var_supports],
            "exponent_spread_across_members": exps,
            "n_distinct_algebraic_forms": len(fclusters),
            "algebraic_form_identified": len(fclusters) == 1,
            "member_complexities": sorted(members[i].complexity for i in c),
            "member_r2_range": [float(min(members[i].valid_r2 for i in c)),
                                float(max(members[i].valid_r2 for i in c))],
            "_member_indices": c,
            "_rep_index": rep,
        })

    families.sort(key=lambda f: (-f["selection_fraction"],
                                 f["representative"]["complexity"],
                                 f["representative"]["expr"]))
    reported = families[0]
    reported["_members"] = members
    reported["_sigs"] = sigs

    return Type2Result(world_id=world_id, engine=engine, n_seeds=n_seeds,
                       families=families, reported=reported,
                       band_sizes=band_sizes, lattice_n=len(D))
