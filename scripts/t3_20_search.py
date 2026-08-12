"""Governed symbolic search over every Phase 3 synthetic world.

Checkpointed at the finest unit that exists — one (block, world, seed) symbolic
run. A completed unit is never recomputed; an interrupted run resumes at the
next incomplete unit; the worst case lost to a crash is the units in flight.

Parallelism is 4 worker processes, each running PySR single-threaded with the
numerical libraries pinned to one thread. Measured: 3.1 s per run at 4 workers
against 2.3 s serial, i.e. 2.97x, for 0.775 s per run of wall time. Six workers
were benchmarked and returned only 11% more throughput for 50% more memory and
more heat on a fanless machine, so 4 stands (RUNTIME_BUDGET_P3.md).

Progress is printed per world, unbuffered, so execution state is visible while
the job runs rather than only at exit.

    python scripts/t3_20_search.py [--blocks G1,G4] [--engine pysr|gplearn]
                                   [--workers 4] [--limit N]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CKPT = ROOT / "artifacts" / "p3_ckpt"


def _build(spec):
    """Rebuild a world deterministically from its spec."""
    from muru.synth.generators import build_null_world, build_world, load_dev_covariates
    cov = None if spec.family == "GA" else load_dev_covariates()
    if spec.null_construction:
        return build_null_world(spec.replicate, spec.null_construction, cov)
    return build_world(spec.family, spec.replicate, spec.noise_regime,
                       cov=cov, cutoff_da=spec.cutoff_da)


def run_world(args) -> dict:
    """Process every pending seed of one world. Seeds checkpoint individually."""
    spec, engine_name, n_seeds = args
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store

    store = Store(CKPT)
    block = f"{spec.block}_{engine_name}"
    seeds = protocol.seed_list(spec.world_id)[:n_seeds]
    pending = store.pending(block, spec.world_id, seeds)
    if not pending:
        return {"world": spec.world_id, "block": block, "ran": 0, "skipped": len(seeds)}

    t0 = time.time()
    world = _build(spec)
    wd = protocol.build_world_data(spec.world_id, world.long, world.cov)

    # world-level facts, written once and independent of seeds
    if not store.done(block, spec.world_id, "_world"):
        store.write(block, spec.world_id, "_world", {
            "world_id": spec.world_id, "block": spec.block,
            "family": spec.family, "replicate": spec.replicate,
            "noise_regime": spec.noise_regime, "cutoff_da": spec.cutoff_da,
            "null_construction": spec.null_construction,
            "manifest": world.manifest(),
            "collapse": {"resid_sd": wd.fit.resid_sd,
                         "hmain": wd.fit.hmain,
                         "n_compounds": int(len(wd.y))},
            "split_counts": {k: int((wd.split == k).sum())
                             for k in ("train", "valid", "test")},
        })

    for s in pending:
        cands = protocol.run_seed(wd, s, which=engine_name)
        store.write(block, spec.world_id, s, {
            "seed": s, "engine": engine_name,
            "candidates": [c.as_dict() for c in cands]})
    return {"world": spec.world_id, "block": block, "ran": len(pending),
            "skipped": len(seeds) - len(pending), "sec": time.time() - t0}


def main() -> int:
    from muru.synth.plan import (N_GPLEARN_SEEDS, N_SEEDS, all_worlds,
                                 gplearn_worlds)

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="")
    ap.add_argument("--engine", default="pysr", choices=("pysr", "gplearn"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    specs = gplearn_worlds() if a.engine == "gplearn" else all_worlds()
    n_seeds = N_GPLEARN_SEEDS if a.engine == "gplearn" else N_SEEDS
    if a.blocks:
        want = set(a.blocks.split(","))
        specs = [s for s in specs if s.block in want]
    if a.limit:
        specs = specs[:a.limit]

    if a.workers > 4:
        print(f"WARNING: {a.workers} workers exceeds the documented cap of 4; "
              "see RUNTIME_BUDGET_P3.md", flush=True)

    total = len(specs) * n_seeds
    print(f"[t3_20] engine={a.engine} worlds={len(specs)} seeds={n_seeds} "
          f"units={total} workers={a.workers}", flush=True)

    import multiprocessing as mp
    ctx = mp.get_context("spawn")
    t0 = time.time()
    ran = skipped = 0
    with ctx.Pool(a.workers) as pool:
        jobs = [(s, a.engine, n_seeds) for s in specs]
        for i, r in enumerate(pool.imap_unordered(run_world, jobs), 1):
            ran += r["ran"]
            skipped += r["skipped"]
            el = time.time() - t0
            rate = ran / el if el > 0 and ran else 0.0
            left = (total - ran - skipped) / rate if rate > 0 else float("nan")
            print(f"[{i:4d}/{len(specs)}] {r['world']:38s} ran={r['ran']:3d} "
                  f"skip={r['skipped']:3d} elapsed={el/60:6.1f}m "
                  f"eta={left/60:6.1f}m", flush=True)

    print(f"[t3_20] done: {ran} units run, {skipped} already present, "
          f"{(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
