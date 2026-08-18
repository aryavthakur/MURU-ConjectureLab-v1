"""Governed symbolic search over every FRESH objective-validation world.

Checkpointed at one `(block, world, seed)` symbolic run, exactly as Phase 3 was:
a completed unit is never recomputed, an interrupted run resumes at the next
incomplete unit, and the worst case lost to a crash is the units in flight.

Blinding: this script receives `World2.search_inputs()` — the long response
frame and the covariate frame — and `World2.manifest()`, which carries no
planted law. The truth manifest is written by `ov_10_build_worlds.py` to a
separate artifact and is not opened here or by anything this imports.

Parallelism is N independent single-process shards rather than a worker pool,
because `juliacall` does not survive multiprocessing teardown (Phase 3 recorded
the same finding). Per-seed checkpointing already makes the work safe to split
and resume.

    python scripts/ov_20_search.py [--blocks G1B,G4] [--engine pysr|gplearn]
                                   [--shard 0 --nshards 4] [--limit N]
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

CKPT = ROOT / "artifacts" / "ov_ckpt"


def build_search_world(spec, cov=None):
    """Rebuild one world deterministically and return only the search inputs."""
    from muru.objval.generators2 import build_null_world2, build_world2
    from muru.synth.generators import load_dev_covariates
    if cov is None and spec.family != "G1A":
        cov = load_dev_covariates()
    if spec.null_construction:
        return build_null_world2(spec.replicate, spec.null_construction, cov)
    return build_world2(spec.family, spec.replicate, spec.noise_regime,
                        cov=None if spec.family == "G1A" else cov,
                        cutoff_da=spec.cutoff_da)


def run_world(spec, engine_name: str, n_seeds: int, cov=None) -> dict:
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store
    from muru.objval.plan2 import seed_list2

    store = Store(CKPT)
    block = f"{spec.block}_{engine_name}"
    seeds = seed_list2(spec.world_id)[:n_seeds]
    pending = store.pending(block, spec.world_id, seeds)
    if not pending:
        return {"world": spec.world_id, "ran": 0, "skipped": len(seeds)}

    t0 = time.time()
    world = build_search_world(spec, cov)
    long, covw = world.search_inputs()
    wd = protocol.build_world_data(spec.world_id, long, covw)

    if not store.done(block, spec.world_id, "_world"):
        store.write(block, spec.world_id, "_world", {
            "world_id": spec.world_id, "block": spec.block,
            "family": spec.family, "replicate": spec.replicate,
            "noise_regime": spec.noise_regime, "cutoff_da": spec.cutoff_da,
            "null_construction": spec.null_construction,
            # manifest() deliberately excludes the planted law
            "manifest": world.manifest(),
            "collapse": {"resid_sd": wd.fit.resid_sd, "hmain": wd.fit.hmain,
                         "n_compounds": int(len(wd.y)),
                         "phi_u": [float(x) for x in wd.fit.phi_u],
                         "phi_v": [float(x) for x in wd.fit.phi_v]},
            "split_counts": {k: int((wd.split == k).sum())
                             for k in ("train", "valid", "test")},
        })

    for s in pending:
        cands = protocol.run_seed(wd, s, which=engine_name)
        store.write(block, spec.world_id, s, {
            "seed": s, "engine": engine_name,
            "candidates": [c.as_dict() for c in cands]})
    return {"world": spec.world_id, "ran": len(pending),
            "skipped": len(seeds) - len(pending), "sec": time.time() - t0}


def main() -> int:
    from muru.objval.plan2 import (N_GPLEARN_SEEDS, N_SEEDS, all_worlds2,
                                   gplearn_worlds2)
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="")
    ap.add_argument("--engine", default="pysr", choices=("pysr", "gplearn"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()

    specs = gplearn_worlds2() if a.engine == "gplearn" else all_worlds2()
    n_seeds = a.seeds or (N_GPLEARN_SEEDS if a.engine == "gplearn" else N_SEEDS)
    if a.blocks:
        want = set(a.blocks.split(","))
        specs = [s for s in specs if s.block in want]
    if a.limit:
        specs = specs[:a.limit]
    if a.nshards > 1:
        specs = [s for i, s in enumerate(specs) if i % a.nshards == a.shard]

    cov = load_dev_covariates()
    total = len(specs) * n_seeds
    print(f"[ov20] engine={a.engine} shard={a.shard}/{a.nshards} "
          f"worlds={len(specs)} seeds={n_seeds} units={total}", flush=True)

    t0, ran, skipped = time.time(), 0, 0
    for i, spec in enumerate(specs, 1):
        r = run_world(spec, a.engine, n_seeds, cov)
        ran += r["ran"]
        skipped += r["skipped"]
        el = time.time() - t0
        rate = ran / el if el > 0 and ran else 0.0
        left = (total - ran - skipped) / rate if rate > 0 else float("nan")
        print(f"[s{a.shard} {i:4d}/{len(specs)}] {r['world']:46s} "
              f"ran={r['ran']:3d} skip={r['skipped']:3d} "
              f"elapsed={el/60:6.1f}m eta={left/60:6.1f}m", flush=True)

    print(f"[ov20] shard {a.shard} done: {ran} run, {skipped} present, "
          f"{(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
