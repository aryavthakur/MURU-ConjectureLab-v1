"""FRESH HOLDOUT — frozen PySR search over every fresh world.

Blind: receives World.search_inputs() only. Never opens the truth manifest.
Checkpointed at one (block, world, seed) unit; a completed unit is never
recomputed and an interruption loses at most the units in flight.

    python scripts/fh_20_search.py --shard 0 --nshards 8
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
CKPT = ROOT / "artifacts" / "fh_ckpt"
FAILLOG = ROOT / "artifacts" / "fresh_holdout" / "search_failures.jsonl"

import fh_lib as fh  # noqa: E402


def run_world(spec, store, cov) -> dict:
    from muru.discovery import protocol
    block = f"{spec.block}_pysr"
    seeds = fh.fh_seed_list(spec.world_id)
    pending = store.pending(block, spec.world_id, seeds)
    if not pending:
        return {"world": spec.world_id, "ran": 0, "skipped": len(seeds)}

    t0 = time.time()
    world = fh.build_fh_world(spec, cov)
    long, covw = world.search_inputs()
    wd = protocol.build_world_data(spec.world_id, long, covw)

    if not store.done(block, spec.world_id, "_world"):
        store.write(block, spec.world_id, "_world", {
            "world_id": spec.world_id, "block": spec.block,
            "family": spec.family, "index": spec.index,
            "replicate": spec.replicate, "noise_regime": spec.noise_regime,
            "cutoff_da": spec.cutoff_da,
            "null_construction": spec.null_construction,
            "manifest": world.manifest(),
            "collapse": {"resid_sd": wd.fit.resid_sd, "hmain": wd.fit.hmain,
                         "n_compounds": int(len(wd.y)),
                         "phi_u": [float(x) for x in wd.fit.phi_u],
                         "phi_v": [float(x) for x in wd.fit.phi_v]},
            "split_counts": {k: int((wd.split == k).sum())
                             for k in ("train", "valid", "test")}})

    ran = 0
    for s in pending:
        try:
            cands = protocol.run_seed(wd, s, which="pysr")
        except Exception:
            FAILLOG.parent.mkdir(parents=True, exist_ok=True)
            with FAILLOG.open("a") as fp:
                fp.write(f'{{"world_id": "{spec.world_id}", "seed": {s}, '
                         f'"error": {traceback.format_exc()!r}}}\n')
            continue
        store.write(block, spec.world_id, s, {
            "seed": s, "engine": "pysr",
            "candidates": [c.as_dict() for c in cands]})
        ran += 1
    return {"world": spec.world_id, "ran": ran,
            "skipped": len(seeds) - len(pending), "sec": time.time() - t0}


def main() -> int:
    from muru.discovery.checkpoint import Store
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--worlds", default="")
    a = ap.parse_args()

    specs = fh.all_worlds()
    if a.worlds:
        want = set(a.worlds.split(","))
        specs = [s for s in specs if s.world_id in want]
    if a.limit:
        specs = specs[:a.limit]
    if a.nshards > 1:
        specs = [s for i, s in enumerate(specs) if i % a.nshards == a.shard]

    store = Store(CKPT)
    cov = load_dev_covariates()
    total = len(specs) * fh.N_SEEDS
    print(f"[fh20] shard={a.shard}/{a.nshards} worlds={len(specs)} "
          f"units={total}", flush=True)

    t0, ran, skipped = time.time(), 0, 0
    for i, spec in enumerate(specs, 1):
        r = run_world(spec, store, cov)
        ran += r["ran"]; skipped += r["skipped"]
        el = time.time() - t0
        rate = ran / el if el > 0 and ran else 0.0
        left = (total - ran - skipped) / rate if rate > 0 else float("nan")
        print(f"[s{a.shard} {i:3d}/{len(specs)}] {r['world']:44s} "
              f"ran={r['ran']} skip={r['skipped']} "
              f"el={el/60:5.1f}m eta={left/60:5.1f}m", flush=True)
    print(f"[fh20] shard {a.shard} done: {ran} run, {skipped} present, "
          f"{(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
