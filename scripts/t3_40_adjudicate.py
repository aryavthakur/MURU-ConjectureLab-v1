"""Adjudicate every synthetic world against the frozen rules.

For each world: reconstruct it deterministically, load its checkpointed
candidates, apply the frozen ranking rule, run the complete F1-F12 harness,
apply the frozen acceptance rule, and — only afterwards, in this reporting path
— score recovery against the planted law.

This script may import `muru.synth.truth`; the discovery code path may not, and
`tests/test_p3_import_graph.py` enforces that separation.

Writes `artifacts/p3_worlds.json`, `artifacts/p3_candidates.json`,
`artifacts/p3_false_positives.json`.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                        # noqa: E402
import sympy as sp                                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

ART = ROOT / "artifacts"
CKPT = ART / "p3_ckpt"


def _candidates(payload, variables):
    from muru.discovery.engine import Candidate
    out = []
    for c in payload["candidates"]:
        try:
            expr = sp.sympify(c["expr"])
        except Exception:
            continue
        out.append(Candidate(
            expr_str=c["expr_str"], expr=expr, complexity=int(c["complexity"]),
            support=tuple(c["support"]), engine=c["engine"], seed=int(c["seed"]),
            train_r2=float(c["train_r2"]), valid_r2=float(c["valid_r2"]),
            invalid_fraction=float(c["invalid_fraction"]), valid=bool(c["valid"]),
            meta=c.get("meta", {})))
    return out


def mass_exponent(expr, variables, X) -> float:
    """d log g / d log m with every other descriptor held at its median.

    Isolates the mass term's exponent, which is the quantity master plan 18.3
    requires within +/-0.15 of the planted 0.5.
    """
    from muru.discovery import grammar
    j = variables.index("precursor_mz")
    med = np.median(X, axis=0)
    grid = np.exp(np.linspace(np.log(max(X[:, j].min(), 1e-3)),
                              np.log(X[:, j].max()), 120))
    D = np.tile(med, (len(grid), 1))
    D[:, j] = grid
    v, ok = grammar.evaluate(expr, variables, D)
    ok &= v > 0
    if ok.sum() < 20:
        return float("nan")
    return float(np.polyfit(np.log(grid[ok]), np.log(v[ok]), 1)[0])


def adjudicate_world(spec) -> dict:
    from muru.discovery import equivalence, falsify, grammar, protocol
    from muru.discovery.checkpoint import Store
    from muru.synth.generators import (build_null_world, build_world,
                                       load_dev_covariates)
    from muru.synth.truth import planted

    thr = np.array(json.loads((ART / "p3_null_calibration.json").read_text())
                   ["threshold_by_complexity"], float)
    store = Store(CKPT)
    block = f"{spec.block}_pysr"
    units = store.read_world(block, spec.world_id)
    seeds = {int(k): v for k, v in units.items() if k != "_world"}
    if not seeds:
        return {"world_id": spec.world_id, "block": spec.block,
                "status": "no_units"}

    cov = None if spec.family == "GA" else load_dev_covariates()
    world = (build_null_world(spec.replicate, spec.null_construction, cov)
             if spec.null_construction else
             build_world(spec.family, spec.replicate, spec.noise_regime,
                         cov=cov, cutoff_da=spec.cutoff_da))
    wd = protocol.build_world_data(spec.world_id, world.long, world.cov)

    per_seed = {s: _candidates(p, wd.variables) for s, p in seeds.items()}
    res = protocol.aggregate(wd, per_seed)

    rec = {
        "world_id": spec.world_id, "block": spec.block, "family": spec.family,
        "replicate": spec.replicate, "noise_regime": spec.noise_regime,
        "cutoff_da": spec.cutoff_da, "null_construction": spec.null_construction,
        "status": "ok",
        "n_seeds": res.n_seeds_run,
        "stability": res.stability,
        "collapse": {"resid_sd": wd.fit.resid_sd, "hmain": wd.fit.hmain},
        "generator": {"seed": world.seed, "sha256": world.output_sha256,
                      "generator_version": world.generator_version,
                      "truth_version": world.truth_version,
                      "planted_expr": world.planted_expr,
                      "planted_support": list(world.planted_support),
                      "collapses": world.collapses,
                      "structural_beyond_mass": world.structural_beyond_mass,
                      "params": world.params},
        "r2_by_complexity_max": [float(x) if np.isfinite(x) else None
                                 for x in res.r2_by_complexity_max],
    }

    if res.candidate is None:
        rec["candidate"] = None
        rec["harness"] = None
        rec["acceptance"] = protocol.accept(res, thr, None)
        return rec

    c = res.candidate
    harness = falsify.run_harness(wd, c.expr, c.complexity, c.support, thr,
                                  res.stability)
    acc = protocol.accept(res, thr, harness)
    rec["candidate"] = {**c.as_dict(), "expr": c.expr_str}
    rec["harness"] = harness
    rec["acceptance"] = acc

    # recovery scoring — reporting path only, after adjudication is fixed
    law = planted(spec.family) if spec.family in ("G1", "G1B", "G3", "GA") else None
    if law is not None:
        D = equivalence.latin_hypercube(
            equivalence.domain_bounds(wd.X, wd.variables), wd.variables,
            equivalence.N_LHC_ADJUDICATE, seed=99)
        truth_expr = grammar.parse(_truth_string(spec.family), wd.variables)
        eq = equivalence.equivalence(c.expr, truth_expr, wd.variables, D)
        rec["recovery"] = {
            **eq,
            "mass_exponent_recovered": mass_exponent(c.expr, wd.variables, wd.X),
            "mass_exponent_planted": 0.5 if spec.family in ("G1", "G1B") else
                                     (0.6 if spec.family == "G3" else None),
        }
        me, mp = rec["recovery"]["mass_exponent_recovered"], \
            rec["recovery"]["mass_exponent_planted"]
        rec["recovery"]["exponent_within_0.15"] = bool(
            mp is not None and np.isfinite(me) and abs(me - mp) <= 0.15)
    return rec


def _truth_string(family: str) -> str:
    """The planted law rewritten in the search's variable names."""
    return {
        "G1": "1.7017*sqrt(precursor_mz)",
        "G1B": "1.7017*sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)",
        "G3": "1.7017*precursor_mz**0.6",
        "GA": "1.5*precursor_mz + 0.5*heteroatom_fraction**2",
    }[family]


def main() -> int:
    import argparse
    import multiprocessing as mp
    from muru.discovery import nulls
    from muru.synth import plan

    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--blocks", default="")
    a = ap.parse_args()

    specs = plan.all_worlds()
    if a.blocks:
        specs = [s for s in specs if s.block in set(a.blocks.split(","))]

    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.workers) as pool:
        recs = []
        for i, r in enumerate(pool.imap_unordered(adjudicate_world, specs), 1):
            recs.append(r)
            if i % 20 == 0 or i == len(specs):
                print(f"[t3_40] {i}/{len(specs)} worlds "
                      f"({(time.time()-t0)/60:.1f}m)", flush=True)

    recs.sort(key=lambda r: r["world_id"])
    (ART / "p3_worlds.json").write_text(json.dumps(recs, indent=1, default=str))

    ok = [r for r in recs if r.get("status") == "ok"]
    g4 = [r for r in ok if r["block"] == "G4"]
    if not g4:
        # a filtered partial run has nothing to adjudicate K6 on; that is not a
        # result and must not be written as one
        print(f"[t3_40] {len(ok)}/{len(recs)} worlds adjudicated; no G4 worlds "
              "in this selection, so K6 was not computed", flush=True)
        return 0
    n_acc = sum(1 for r in g4 if r["acceptance"]["accepted"])
    fp = nulls.false_positive_rate(n_acc, len(g4))
    k6 = nulls.adjudicate_k6(fp)

    g4m = [r for r in ok if r["block"] == "G4M"]
    n_struct = sum(1 for r in g4m if r["acceptance"]["accepted"]
                   and r["acceptance"]["claims_non_mass_structure"])
    fp_struct = (nulls.false_positive_rate(n_struct, len(g4m)) if g4m else None)

    (ART / "p3_false_positives.json").write_text(json.dumps({
        "G4_pure_null": {**fp, "accepted_world_ids": [
            r["world_id"] for r in g4 if r["acceptance"]["accepted"]]},
        "K6": k6,
        "G4M_mass_conditional_null": {
            "n_worlds": len(g4m),
            "n_accepted_any": sum(1 for r in g4m if r["acceptance"]["accepted"]),
            "n_accepted_claiming_structure_beyond_mass": n_struct,
            "rate_structure_beyond_mass": fp_struct,
            "note": ("supplementary to the master plan's G4; this is the null "
                     "matched to the Phase 2 question, structure beyond energy "
                     "and mass"),
        },
    }, indent=1))

    cands = [{"world_id": r["world_id"], "block": r["block"],
              "expr": r["candidate"]["expr"],
              "complexity": r["candidate"]["complexity"],
              "support": r["candidate"]["support"],
              "valid_r2": r["candidate"]["valid_r2"],
              "selection_fraction": r["stability"]["fraction"],
              "accepted": r["acceptance"]["accepted"],
              "failed_rungs": (r["harness"] or {}).get("failed_rungs", []),
              "claims_non_mass_structure":
                  r["acceptance"].get("claims_non_mass_structure")}
             for r in ok if r.get("candidate")]
    (ART / "p3_candidates.json").write_text(json.dumps(cands, indent=1))

    print(f"[t3_40] {len(ok)}/{len(recs)} worlds adjudicated in "
          f"{(time.time()-t0)/60:.1f} min")
    print(f"[t3_40] G4: {n_acc}/{len(g4)} accepted -> rate {fp['rate']:.4f} "
          f"CI {np.round(fp['ci'], 4).tolist()} -> {k6['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
