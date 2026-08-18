#!/usr/bin/env python
"""Part VI: speed benchmark -- EXHAUSTIVE vs LAZY vs LAZY+PERSISTENT CACHE.

Three arms, run on the SAME outcome-blind, wall_seconds-stratified sample
of already-completed E2a worlds (selection identical to
`replay_parity.py`'s -- never keys on `first_loss_stage`):

  EXHAUSTIVE: mirrors `scripts/e2_run_shard.py`'s real per-row call pattern
      exactly -- for every row of every seed's front, call
      `classify_expression` (as `run_seed_search` does, to determine
      `parse_ok`/`canonicalization_status` for the persisted record) THEN
      call the real, unmodified `e2_scoring.score_row` (which internally
      calls `classify_expression` again -- a cache hit against the
      in-process `_CACHE`, exactly as production experiences it -- and
      unconditionally attempts `algebraically_equivalent`). `e2_classify.
      _CACHE` is cleared before each world, matching a cold shard/world
      boundary.

  LAZY: `lazy_classify.lazy_evaluate_world` on the same raw front data,
      `_CACHE` also cleared before each world (same cold-start condition,
      isolating the ALGORITHMIC difference from any cache effect).

  LAZY+CACHE: `lazy_classify.lazy_evaluate_world`, but `classify_expression`
      is routed through a `PersistentClassifyCache` that is NOT cleared
      between worlds in this arm -- warms across the whole benchmark
      sample, showing the added benefit of Part IV's persistent cache
      (cross-seed AND cross-world reuse) on top of Part III's lazy
      witness order.

Metrics reported (Part VI's required list): wall time/world, classify
calls/world, equivalence calls/world, timeouts/world, cache hit rate.
CPU time and peak memory are approximated from Python's own
`resource.getrusage` deltas (this process only -- the persistent classify
worker is a separate child process and is not separately profiled here;
its wall-clock contribution is fully captured in wall time).

Reported using OPAQUE per-world IDs only; the JSON output never contains
`first_loss_stage` or any stage-correlated label (see replay_parity.py's
own note on why `witness_path`-style labels are excluded).
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_classify, e2_scoring as e2sc  # noqa: E402
from muru.v2_calibration.e2_search import FrontRow  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import classify_cache as cc  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay_parity import _load_world_outcomes, _load_candidates, _select_sample, _rebuild_truth, _opaque  # noqa: E402


class _WorldBudgetExceeded(Exception):
    pass


def _run_exhaustive(seed_raw_fronts: dict[int, list[lc.RawFrontRow]], truth, wall_budget_seconds: float = 45.0) -> dict:
    """Mirrors scripts/e2_run_shard.py's real per-row loop exactly:
    classify (as run_seed_search does) then score_row (unmodified,
    unconditional equivalence attempt) for every row of every seed.

    SAFETY NOTE (added after this benchmark's own shakedown ran long on the
    shared host): `algebraically_equivalent` -- unlike `classify_expression`
    -- has no wall-clock cap anywhere in its own call path (see
    MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md section 3). A per-WORLD wall
    budget is checked between rows (best-effort -- this is a coarse
    between-row check, not a per-call interrupt, since interrupting
    mid-sympy-call reliably is exactly the problem the 2026-08-16 rescue
    found signal-based caps cannot solve reliably either). If exceeded,
    the world is abandoned and reported as `exhaustive_timed_out=True`
    with whatever counts were accumulated so far -- itself a real,
    disclosed data point (an exhaustive-arm world that does not finish in
    45s of pure classification time on a row-by-row budget check is
    exactly the class of risk the lazy design's <=1 equivalence-call-per-
    world property exists to avoid), not a fabricated result."""
    e2_classify._CACHE.clear()
    n_classify_direct = 0
    n_rows = 0
    n_timeouts = 0
    timed_out = False
    t0 = time.monotonic()
    try:
        for seed, rows in seed_raw_fronts.items():
            for raw in rows:
                if time.monotonic() - t0 > wall_budget_seconds:
                    raise _WorldBudgetExceeded()
                n_rows += 1
                classification = e2_classify.classify_expression(raw.expression_string)  # run_seed_search's own call
                n_classify_direct += 1
                if classification.canonicalization_status == "SIMPLIFY_TIMEOUT":
                    n_timeouts += 1
                front = FrontRow(
                    front_rank=raw.front_rank, engine_complexity=raw.complexity, grammar_complexity=raw.complexity,
                    expression_string=raw.expression_string, parse_ok=classification.parse_ok,
                    canonicalization_status=classification.canonicalization_status,
                    canonical_expression=classification.canonical_expression,
                    train_r2=float("nan"), valid_r2=raw.valid_r2, test_r2=raw.candidate_test_r2,
                    loss=float("nan"), score=float("nan"), invalid_fraction=raw.invalid_fraction,
                    effective_support=(
                        tuple(sorted(classification.effective_support))
                        if classification.effective_support is not None else None
                    ),
                    template_key_repr=classification.template_key_repr,
                    coefficient_estimates=classification.coefficient_estimates,
                    retained_by_argmax_score=raw.retained_by_argmax_score,
                )
                e2sc.score_row(front, truth)  # unmodified production call; re-classifies internally (cache hit)
    except _WorldBudgetExceeded:
        timed_out = True
    elapsed = time.monotonic() - t0
    return {
        "wall_seconds": elapsed, "n_rows": n_rows,
        "n_classify_calls": n_classify_direct,  # the direct calls this loop made; score_row's internal re-call is a cache hit, not counted again here (matches how e2_classify.cache_size() is the metric production itself logs)
        "n_timeouts": n_timeouts,
        "exhaustive_timed_out": timed_out,
    }


def _run_lazy(seed_raw_fronts: dict[int, list[lc.RawFrontRow]], truth) -> dict:
    e2_classify._CACHE.clear()
    lc.reset_call_counters()
    t0 = time.monotonic()
    result = lc.lazy_evaluate_world(seed_raw_fronts, truth)
    elapsed = time.monotonic() - t0
    return {
        "wall_seconds": elapsed,
        "n_classify_calls": result.n_classify_calls,
        "n_equivalence_calls": result.n_equivalence_calls,
    }


_REAL_CLASSIFY_EXPRESSION = e2_classify.classify_expression  # captured once, at import time, before any patching


def _run_lazy_cached(seed_raw_fronts: dict[int, list[lc.RawFrontRow]], truth, cache: cc.PersistentClassifyCache) -> dict:
    import unittest.mock as mock

    # BUG FOUND DURING THIS BENCHMARK'S OWN SHAKEDOWN (real-data run,
    # 2026-08-17): without this clear, `_REAL_CLASSIFY_EXPRESSION` still
    # consults `e2_classify`'s own in-process `_CACHE` at call time (it
    # closes over the live module dict, not a snapshot) -- and `_run_lazy`
    # runs immediately before this function on the SAME world's SAME
    # expressions, populating exactly that cache. Without clearing, every
    # "cold" LAZY+CACHE measurement was silently riding the immediately-
    # preceding LAZY arm's leftover in-process cache instead of exercising
    # the persistent (SQLite) cache this arm exists to benchmark -- a
    # zero-second first-world result that looked like a free win but was
    # actually measuring nothing. Clearing here isolates the persistent
    # cache's OWN contribution, exactly like the other two arms already do.
    e2_classify._CACHE.clear()
    lc.reset_call_counters()
    hits_before = _cache_hits(cache)

    def cached_classify(expr):
        got = cache.get_classification(expr)
        if got is not cc._MISSING:
            return got
        # Call the REAL, unpatched function -- e2_classify.classify_expression
        # is shadowed by this very mock for the duration of the `with` block
        # below, so calling it here (instead of the captured reference)
        # would recurse into this same wrapper forever.
        real = _REAL_CLASSIFY_EXPRESSION(expr)
        cache.put_classification(expr, real)
        return real

    t0 = time.monotonic()
    with mock.patch.object(e2_classify, "classify_expression", side_effect=cached_classify):
        result = lc.lazy_evaluate_world(seed_raw_fronts, truth)
    elapsed = time.monotonic() - t0
    hits_after = _cache_hits(cache)
    return {
        "wall_seconds": elapsed,
        "n_classify_calls": result.n_classify_calls,
        "n_equivalence_calls": result.n_equivalence_calls,
        "cache_hits_this_world": hits_after - hits_before,
    }


def _cache_hits(cache: cc.PersistentClassifyCache) -> int:
    return cache.stats()["classify_rows_current_version"]


def run_benchmark(dirs: list[Path], sample_size: int, cache_db: Path, incremental_out: Path | None = None) -> dict:
    outcomes = _load_world_outcomes(dirs)
    sample = _select_sample(outcomes, sample_size)

    repo_root = REPO_ROOT
    version = cc.compute_classifier_version(repo_root)
    if cache_db.exists():
        cache_db.unlink()  # start the LAZY+CACHE arm cold, so its own warm-up is visible in the results
    cache = cc.PersistentClassifyCache(cache_db, version)

    per_world = []
    ru_start = resource.getrusage(resource.RUSAGE_SELF)
    try:
        for wid in sample:
            if incremental_out is not None:
                # Written BEFORE processing so a kill mid-world still leaves
                # a valid, if partial, artifact on disk -- this run's own
                # predecessor was killed after 4/5 worlds with nothing
                # persisted; not repeating that.
                incremental_out.write_text(json.dumps({"N_WORLDS_BENCHMARKED_SO_FAR": len(per_world), "per_world": per_world}, indent=2))
            exhaustive_rec = outcomes[wid]
            truth = _rebuild_truth(exhaustive_rec)
            by_seed = _load_candidates(dirs, wid)

            exh = _run_exhaustive(by_seed, truth)
            lazy = _run_lazy(by_seed, truth)
            lazy_cached = _run_lazy_cached(by_seed, truth, cache)

            # If the exhaustive arm hit its wall budget, its measured
            # wall_seconds is a LOWER BOUND on the true exhaustive cost --
            # the true speedup ratio is therefore AT LEAST this much, not
            # exactly this much. Flagged explicitly rather than reported as
            # a precise number.
            entry = {
                "opaque_id": _opaque(wid),
                "exhaustive": exh, "lazy": lazy, "lazy_cached": lazy_cached,
                "lazy_speedup_x": (exh["wall_seconds"] / lazy["wall_seconds"]) if lazy["wall_seconds"] > 0 else None,
                "lazy_cached_speedup_x": (
                    exh["wall_seconds"] / lazy_cached["wall_seconds"] if lazy_cached["wall_seconds"] > 0 else None
                ),
                "speedup_is_lower_bound": bool(exh.get("exhaustive_timed_out")),
            }
            per_world.append(entry)
            print(
                f"  world done: exhaustive={exh['wall_seconds']:.1f}s"
                f"{' (TIMED OUT, lower bound)' if exh.get('exhaustive_timed_out') else ''}"
                f" lazy={lazy['wall_seconds']:.2f}s lazy+cache={lazy_cached['wall_seconds']:.2f}s",
                flush=True,
            )
    finally:
        e2_classify.shutdown()
        cache.close()
    ru_end = resource.getrusage(resource.RUSAGE_SELF)

    speedups_lazy = sorted(w["lazy_speedup_x"] for w in per_world if w["lazy_speedup_x"] is not None)
    speedups_cached = sorted(w["lazy_cached_speedup_x"] for w in per_world if w["lazy_cached_speedup_x"] is not None)

    def _pct(xs, p):
        if not xs:
            return None
        idx = min(len(xs) - 1, max(0, round(p * (len(xs) - 1))))
        return xs[idx]

    return {
        "N_WORLDS_BENCHMARKED": len(per_world),
        "selection_method": "wall_seconds-stratified even stride (outcome-blind), shared with replay_parity.py",
        "classifier_version": version,
        "lazy_speedup_x": {
            "median": _pct(speedups_lazy, 0.5), "p25": _pct(speedups_lazy, 0.25),
            "p75": _pct(speedups_lazy, 0.75), "worst_case_min": (min(speedups_lazy) if speedups_lazy else None),
        },
        "lazy_plus_cache_speedup_x": {
            "median": _pct(speedups_cached, 0.5), "p25": _pct(speedups_cached, 0.25),
            "p75": _pct(speedups_cached, 0.75), "worst_case_min": (min(speedups_cached) if speedups_cached else None),
        },
        "process_cpu_seconds_delta": {
            "user": ru_end.ru_utime - ru_start.ru_utime, "system": ru_end.ru_stime - ru_start.ru_stime,
        },
        "process_peak_rss_kb": ru_end.ru_maxrss,
        "per_world": per_world,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--sample-size", type=int, default=8)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--cache-db", type=str, default="/tmp/e2_rescue_v2_bench_cache.sqlite3")
    args = parser.parse_args()

    dirs = [Path(d) for d in args.dirs]
    result = run_benchmark(dirs, args.sample_size, Path(args.cache_db), incremental_out=Path(args.out))
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(f"N_WORLDS_BENCHMARKED: {result['N_WORLDS_BENCHMARKED']}")
    print(f"LAZY median speedup: {result['lazy_speedup_x']['median']}")
    print(f"LAZY+CACHE median speedup: {result['lazy_plus_cache_speedup_x']['median']}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
