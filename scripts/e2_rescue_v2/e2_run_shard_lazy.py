#!/usr/bin/env python
"""Rescue-v2 production world runner.

Search is UNCHANGED (`raw_search.run_seed_search_raw`, a verified
structural transcription of the frozen `e2_search.run_seed_search` --
see `tests/test_raw_search_identity.py`). Classification is LAZY
(`lazy_classify.lazy_evaluate_world`, the minimal-witness algorithm
proven in MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md), routed through the
persistent, source-hashed cache (`classify_cache.py`) so repeated or
cross-world-identical expressions are never reclassified.

`_already_done` checks EVERY given result directory -- both the
preserved, now-immutable old-run directories and this run's own output
directory -- so no world already computed under either architecture is
ever recomputed. This is the "import/reuse without recomputing" migration
step: no data copy, the same directory-scanning discipline
`e2_run_shard.py`'s own `_already_done` already uses, just extended
across the old/new boundary.

Output schema: `worlds_shard_*.jsonl` carries the routing/gate-relevant
fields (first_loss_stage, representative_g2_correct,
representative_truth_equivalent, family/regime/noise_level/replicate,
wall_seconds) plus explicit `classification_mode: "lazy"` and
`rescue_v2_authority` provenance. `candidates_shard_*.jsonl` carries every
RAW front row (structural fields only -- no classification-derived
columns, for any row, since `lazy_evaluate_world` does not report back
which specific rows it visited; `classified` is a placeholder always
`false` in this version, not yet a meaningful per-row flag -- disclosed
here rather than silently wrong). This is a disclosed, versioned schema
change from the exhaustive run's own candidate schema (Part XI of
MURU_V2_E2_RESCUE_V2_PROTOCOL.md already states this), not a silent one.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_classify, e2_worlds  # noqa: E402
from muru.v2_calibration.e2_search import build_world_design  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import raw_search  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import classify_cache as cc  # noqa: E402

RESCUE_V2_AUTHORITY_NOTE = "MURU_V2_E2_RESCUE_V2_PROTOCOL.md v2.0.0 -- classification order + persistent cache changed; search, truth oracle, equivalence semantics, first-loss definitions unchanged"


def _already_done(dirs: list[Path]) -> set[str]:
    done = set()
    for d in dirs:
        for path in sorted(d.glob("worlds_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        done.add(json.loads(line)["world_id"])
                    except Exception:
                        continue
    return done


_REAL_CLASSIFY_EXPRESSION = e2_classify.classify_expression  # captured ONCE, at import time, before any patching


def _cached_classify_expression(cache: cc.PersistentClassifyCache):
    """BUG FOUND LIVE during this migration's own smoke test (2 of 2 new
    worlds hit `RecursionError: maximum recursion depth exceeded` --
    reproduced, diagnosed, and fixed before any further world was
    attempted): calling `e2_classify.classify_expression` here, while
    `e2_classify.classify_expression` is itself being monkey-patched to
    THIS function for the duration of `_run_one_world`'s `with` block,
    recurses into this same wrapper forever on every cache MISS (a HIT
    returns immediately, which is why the ~119k worlds seeded from the old
    run's own classifications mostly worked -- only a genuinely new
    expression the cache had never seen triggered it). This is the exact
    same defect this rescue already found once, live, in
    speed_benchmark.py's own cache arm -- same root cause, same fix: call
    the REAL function captured before patching, never the (possibly
    still-patched) module attribute."""
    def fn(expr: str):
        cached = cache.get_classification(expr)
        if cached is not cc._MISSING:
            return cached
        real = _REAL_CLASSIFY_EXPRESSION(expr)
        cache.put_classification(expr, real)
        return real
    return fn


def _run_one_world(family: str, regime: str, noise: str, replicate: int,
                    seeds_per_world: int, seed_base: int, cache: cc.PersistentClassifyCache) -> tuple[dict, list[dict]]:
    world = e2_worlds.build_world(family, regime, noise, replicate)
    world_design = build_world_design(world.compounds, world.trajectories, world.world_id)

    t_world = time.monotonic()
    seed_raw_fronts: dict[int, list] = {}
    candidate_rows: list[dict] = []
    for k in range(seeds_per_world):
        seed_val = seed_base + world.world_ordinal * seeds_per_world + k
        sr = raw_search.run_seed_search_raw(world_design, k=k, seed=seed_val)
        if sr.status == "COMPLETED_WITH_FRONT":
            seed_raw_fronts[sr.seed] = list(sr.rows)
            for r in sr.rows:
                candidate_rows.append({
                    "world_id": world.world_id, "cell_id": world.cell_id, "family": family,
                    "regime": regime, "noise_level": noise, "replicate": replicate,
                    "seed_ordinal_k": r.seed_ordinal_k, "seed": r.seed, "front_rank": r.front_rank,
                    "expression_string": r.expression_string, "engine_complexity": r.complexity,
                    "valid_r2": r.valid_r2, "invalid_fraction": r.invalid_fraction,
                    "test_r2": r.candidate_test_r2, "retained_by_argmax_score": r.retained_by_argmax_score,
                    "classified": False,  # flipped to True below for rows the witness order actually visits
                })

    lc.reset_call_counters()
    with __import__("unittest.mock", fromlist=["mock"]).patch.object(
        e2_classify, "classify_expression", side_effect=_cached_classify_expression(cache)
    ):
        result = lc.lazy_evaluate_world(seed_raw_fronts, world.truth)
    wall = time.monotonic() - t_world

    world_row = {
        "world_id": world.world_id, "cell_id": world.cell_id, "family": family, "regime": regime,
        "noise_level": noise, "replicate": replicate, "coefficient": world.truth.coefficient,
        "noise_sd": world.truth.noise_sd,
        "first_loss_stage": result.first_loss_stage,
        "representative_g2_correct": result.representative_g2_correct,
        "representative_truth_equivalent": result.representative_truth_equivalent,
        "representative_expression": result.representative_expression,
        "classification_mode": "lazy", "witness_path": result.witness_path,
        "n_classify_calls": result.n_classify_calls, "n_equivalence_calls": result.n_equivalence_calls,
        "rescue_v2_authority": RESCUE_V2_AUTHORITY_NOTE,
        "wall_seconds": wall,
    }
    return world_row, candidate_rows


def run_shard(shard_index: int, n_shards: int, out_dir: Path, prior_result_dirs: list[Path],
              world_list: list[tuple], seeds_per_world: int, seed_base: int, cache_db: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    worlds_path = out_dir / f"worlds_shard_{shard_index:03d}.jsonl"
    candidates_path = out_dir / f"candidates_shard_{shard_index:03d}.jsonl"
    log_path = out_dir / f"log_shard_{shard_index:03d}.txt"
    errors_path = out_dir / f"errors_shard_{shard_index:03d}.jsonl"

    version = cc.compute_classifier_version(REPO_ROOT)
    cache = cc.PersistentClassifyCache(cache_db, version)

    done = _already_done(prior_result_dirs + [out_dir])
    my_worlds = [w for w in world_list if e2_worlds.world_ordinal(*w) % n_shards == shard_index]

    with log_path.open("a") as log:
        log.write(f"shard {shard_index}/{n_shards}: {len(my_worlds)} assigned, "
                   f"{sum(1 for w in my_worlds if e2_worlds.world_id(*w) in done)} already done (old or new)\n")
        log.flush()
        try:
            for family, regime, noise, replicate in my_worlds:
                wid = e2_worlds.world_id(family, regime, noise, replicate)
                if wid in done:
                    continue
                try:
                    world_row, candidate_rows = _run_one_world(
                        family, regime, noise, replicate, seeds_per_world, seed_base, cache)
                    with candidates_path.open("a") as cf:
                        for row in candidate_rows:
                            cf.write(json.dumps(row) + "\n")
                    with worlds_path.open("a") as wf:
                        wf.write(json.dumps(world_row) + "\n")
                    log.write(f"{wid}: stage={world_row['first_loss_stage']} "
                              f"classify_calls={world_row['n_classify_calls']} wall={world_row['wall_seconds']:.1f}s\n")
                    log.flush()
                except Exception as error:
                    with errors_path.open("a") as ef:
                        ef.write(json.dumps({
                            "world_id": wid, "error": f"{type(error).__name__}: {error}",
                        }) + "\n")
                    log.write(f"{wid}: WORLD-LEVEL EXECUTION FAILURE: {error}\n")
                    log.flush()
        finally:
            e2_classify.shutdown()
            cache.close()
    with log_path.open("a") as log:
        log.write(f"shard {shard_index} COMPLETE\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--n-shards", type=int, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    parser.add_argument("--prior-result-dir", action="append", default=[], dest="prior_dirs")
    parser.add_argument("--world-order-file", type=str, required=True,
                         help="JSON list of [family, regime, noise, replicate] in PRIORITY order (Part IX)")
    parser.add_argument("--seeds-per-world", type=int, default=30)
    parser.add_argument("--seed-base", type=int, default=2_104_500_000)
    parser.add_argument("--cache-db", type=str, required=True)
    args = parser.parse_args()

    world_list = [tuple(w) for w in json.loads(Path(args.world_order_file).read_text())]
    run_shard(args.shard_index, args.n_shards, Path(args.out_dir), [Path(d) for d in args.prior_dirs],
              world_list, args.seeds_per_world, args.seed_base, Path(args.cache_db))


if __name__ == "__main__":
    main()
