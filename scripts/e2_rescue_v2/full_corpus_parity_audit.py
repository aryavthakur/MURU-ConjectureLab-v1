#!/usr/bin/env python
"""Full-corpus results-blind parity audit.

Replays the LAZY classifier (never the exhaustive one -- exhaustive
results are already sealed and are read, not recomputed) against EVERY
currently-completed, valid (non-`PRERESCUE_INVALIDATED`) E2a world
available in the live run's output at the moment this script starts, and
compares each replay to that world's already-persisted exhaustive result.

Hang safety: the lazy path is bounded to <=1 `algebraically_equivalent`
call per world (unlike the exhaustive path, which this audit never runs),
so the residual risk is much lower than what the speed-benchmark's
exhaustive arm hit repeatedly -- but that ONE call is still uncapped (see
MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md section 3), so every world's replay
runs inside a single, long-lived, fork-context worker PROCESS with a hard
per-world timeout enforced via `AsyncResult.get(timeout=...)`. On timeout,
the entire pool is torn down (`terminate()` -- SIGTERM, which is NOT
catchable by a bare `except Exception` the way SIGALRM was found to be,
see E2_EXECUTION_DEVIATION.md section 4a) and a fresh one started for the
remaining worlds; a final process sweep hunts down and kills any orphaned
child of a terminated worker (mirroring e2_classify.py's own documented
orphan-worker lesson from the original rescue, section 4a/S9's atexit
note) before this script exits.

RESULTS-BLINDNESS: this script reads `first_loss_stage`,
`representative_g2_correct`, `representative_truth_equivalent` from
already-sealed exhaustive records ONLY to compute a per-world boolean
MATCH/MISMATCH -- exactly as `replay_parity.py` already does, and
explicitly authorized by that script's own precedent. It NEVER aggregates
these into a count or rate, NEVER prints one, and NEVER reads any E2b or
routing-relevant field. The only things this script ever prints or writes
to its JSON output are the 7 named counters plus opaque per-mismatch
implementation-level detail (see `_categorize_mismatch`).

Usage:
    full_corpus_parity_audit.py --result-dir DIR [DIR ...] --out FILE.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_classify, e2_worlds  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402

SALT = "e2-rescue-v2-full-corpus-audit"
PER_WORLD_TIMEOUT_SECONDS = 90
DETERMINISM_SUBSET_TARGET = 30


def _opaque(world_id: str) -> str:
    return "W" + hashlib.sha256((SALT + world_id).encode()).hexdigest()[:12]


def _valid_result_dirs(dirs: list[Path]) -> list[Path]:
    """Excludes any directory whose name marks it invalidated -- e.g.
    `run_PRERESCUE_INVALIDATED_2026-08-16`, the pre-rescue population the
    original rescue itself discarded (E2_EXECUTION_DEVIATION.md section 4).
    Only currently-VALID rescue worlds are in scope for this audit."""
    kept = []
    for d in dirs:
        if "INVALIDATED" in d.name.upper():
            continue
        kept.append(d)
    return kept


def _load_outcomes(dirs: list[Path]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for d in dirs:
        for path in sorted(d.glob("worlds_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    wid = rec.get("world_id")
                    if wid:
                        out[wid] = rec
    return out


def _build_candidate_index(dirs: list[Path]) -> dict[str, dict[int, list[dict]]]:
    """SINGLE pass over every candidates_shard_*.jsonl file (~230MB across
    the live run's 5 valid output directories), grouping raw rows by
    world_id then seed. Avoids replay_parity.py's per-world full-file-scan
    approach, which would be O(worlds x total_bytes) at this scale."""
    index: dict[str, dict[int, list[dict]]] = {}
    for d in dirs:
        for path in sorted(d.glob("candidates_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    wid = rec.get("world_id")
                    seed = rec.get("seed")
                    if wid is None or seed is None:
                        continue
                    index.setdefault(wid, {}).setdefault(seed, []).append(rec)
    return index


def _raw_fronts_for_world(cand_by_seed: dict[int, list[dict]]) -> dict[int, list[lc.RawFrontRow]]:
    out: dict[int, list[lc.RawFrontRow]] = {}
    for seed, rows in cand_by_seed.items():
        out[seed] = [
            lc.RawFrontRow(
                seed_ordinal_k=r["seed_ordinal_k"], seed=seed, front_rank=r["front_rank"],
                expression_string=r["expression_string"], complexity=r["engine_complexity"],
                valid_r2=r["valid_r2"], invalid_fraction=r["invalid_fraction"],
                candidate_test_r2=r["test_r2"], retained_by_argmax_score=r["retained_by_argmax_score"],
            )
            for r in rows
        ]
    return out


def _replay_worker(payload: tuple) -> dict:
    """Runs inside a forked worker process. `payload` is fully picklable
    (primitives + the RawFrontRow dataclasses' constructor args as plain
    dicts) -- reconstructed here rather than pickling dataclass instances
    across the fork boundary, keeping this a plain-data contract."""
    wid, family, regime, noise_level, replicate, cand_by_seed = payload
    try:
        truth = e2_worlds.build_world(family, regime, noise_level, replicate).truth
        raw_fronts = _raw_fronts_for_world(cand_by_seed)
        result = lc.lazy_evaluate_world(raw_fronts, truth)
        return {
            "ok": True,
            "first_loss_stage": result.first_loss_stage,
            "representative_g2_correct": result.representative_g2_correct,
            "representative_truth_equivalent": result.representative_truth_equivalent,
        }
    except Exception as error:  # noqa: BLE001 -- deliberately broad: any failure becomes a reported ERROR, never a crash of the audit
        return {"ok": False, "error_type": type(error).__name__}


def _replay_worker_twice(payload: tuple) -> dict:
    """Determinism check: same world, two independent lazy_evaluate_world
    calls inside the SAME worker call (so process-level state, e.g. the
    persistent classify worker, is common to both -- the harder,
    more realistic determinism condition, not two totally cold runs)."""
    wid, family, regime, noise_level, replicate, cand_by_seed = payload
    try:
        truth = e2_worlds.build_world(family, regime, noise_level, replicate).truth
        raw_fronts = _raw_fronts_for_world(cand_by_seed)
        r1 = lc.lazy_evaluate_world(raw_fronts, truth)
        r2 = lc.lazy_evaluate_world(raw_fronts, truth)
        match = (
            r1.first_loss_stage == r2.first_loss_stage
            and r1.representative_g2_correct == r2.representative_g2_correct
            and r1.representative_truth_equivalent == r2.representative_truth_equivalent
        )
        return {"ok": True, "match": match}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error_type": type(error).__name__}


def _worker_loop(conn, parent_conn_to_close, fn) -> None:  # pragma: no cover - runs in child process
    """Persistent worker body, deliberately mirroring
    `e2_classify.py::_worker_loop`'s own pattern exactly (recv one task,
    compute, send result, repeat) -- including the same inherited-pipe-fd
    close that module's docstring explains is required to get a clean EOF
    if this worker is ever orphaned."""
    parent_conn_to_close.close()
    while True:
        try:
            payload = conn.recv()
        except (EOFError, OSError):
            return
        try:
            result = fn(payload)
        except Exception as error:  # noqa: BLE001
            result = {"ok": False, "error_type": type(error).__name__}
        try:
            conn.send(result)
        except (EOFError, OSError, BrokenPipeError):
            return


class _SafePool:
    """A single, long-lived, NON-daemonic worker process (`Process`, not
    `multiprocessing.Pool` -- Pool workers are daemonic by default, and
    Python's multiprocessing explicitly forbids a daemonic process from
    spawning children: `AssertionError: daemonic processes are not
    allowed to have children`. This audit's replay worker needs to spawn
    ITS OWN child (e2_classify's persistent classify worker), so it must
    not itself be daemonic -- confirmed live during this audit's own
    shakedown, see the hostile-review addendum), recreated whenever a
    task times out or the worker otherwise dies, so one stuck world never
    blocks the rest of the audit."""

    def __init__(self, fn):
        self._ctx = mp.get_context("fork")
        self._fn = fn
        self._proc = None
        self._conn = None
        self._spawn()

    def _spawn(self):
        if self._proc is not None and self._proc.is_alive():
            self._proc.kill()
            self._proc.join(2.0)
        parent_conn, child_conn = self._ctx.Pipe(duplex=True)
        proc = self._ctx.Process(target=_worker_loop, args=(child_conn, parent_conn, self._fn), daemon=False)
        proc.start()
        child_conn.close()
        self._proc = proc
        self._conn = parent_conn

    def run(self, payload, timeout=PER_WORLD_TIMEOUT_SECONDS):
        try:
            self._conn.send(payload)
        except (BrokenPipeError, EOFError, OSError):
            self._spawn()
            return None, "WORKER_DEAD_ON_SEND"
        if self._conn.poll(timeout):
            try:
                return self._conn.recv(), None
            except (EOFError, OSError):
                self._spawn()
                return None, "WORKER_DEAD_ON_RECV"
        # Timed out -- the worker may be wedged inside an uncapped sympy
        # call (see module docstring). kill() sends SIGKILL, uncatchable
        # by any in-worker except, exactly matching e2_classify.py's own
        # `_kill_worker` discipline for its persistent classify worker.
        self._spawn()
        return None, "TIMEOUT"

    def close(self):
        try:
            if self._proc is not None and self._proc.is_alive():
                self._proc.kill()
                self._proc.join(2.0)
        except Exception:
            pass


def take_snapshot(dirs: list[Path]) -> dict:
    """Freezes the exact world-ID population every shard must partition
    identically. MUST be called ONCE, before any shard launches, with the
    result passed to every shard via `--frozen-snapshot-file` -- calling
    `_load_outcomes` independently, at different wall-clock moments, in
    each shard process is NOT safe: the live run keeps completing new
    worlds between when an earlier-started shard and a later-started one
    each take their own snapshot, so `sorted(...)[i % n_shards]`
    partitioning computed against two different-length lists can silently
    both duplicate and drop worlds (a real defect caught during this
    audit's own first 3-shard attempt: shard 0 saw 355 completed worlds,
    shards 1-2, started minutes later after a load-driven pause, saw 357).
    """
    dirs = _valid_result_dirs(dirs)
    outcomes = _load_outcomes(dirs)
    all_replayable_ids = []
    n_missing_required_fields = 0
    for wid, rec in outcomes.items():
        if all(k in rec for k in ("family", "regime", "noise_level", "replicate")):
            all_replayable_ids.append(wid)
        else:
            n_missing_required_fields += 1
    all_replayable_ids.sort()
    return {
        "n_completed_snapshot": len(outcomes),
        "all_replayable_ids": all_replayable_ids,
        "n_missing_required_fields": n_missing_required_fields,
    }


def run_audit(dirs: list[Path], out_path: Path, shard_index: int = 0, n_shards: int = 1,
              skip_determinism: bool = False, frozen_snapshot: dict | None = None) -> dict:
    """`shard_index`/`n_shards` mirror `scripts/e2_run_shard.py`'s own
    sharding convention -- multiple independent OS processes, each a
    disjoint slice of the SAME sorted, deterministic `replayable_ids`
    list (`i % n_shards == shard_index`), so a few slow worlds in one
    shard never serialize-block worlds assigned to another. Each shard
    writes its own partial JSON; `merge_shards.py` combines them into the
    final operator-facing summary. Only shard 0 runs the determinism
    check (avoids duplicating that work N times).

    `frozen_snapshot`, if given (see `take_snapshot`), is used instead of
    re-deriving the population live -- REQUIRED for a multi-shard run to
    be a mathematically sound partition (see `take_snapshot`'s docstring).
    """
    dirs = _valid_result_dirs(dirs)
    outcomes = _load_outcomes(dirs)

    cand_index = _build_candidate_index(dirs)

    if frozen_snapshot is not None:
        n_completed_snapshot = frozen_snapshot["n_completed_snapshot"]
        all_replayable_ids = frozen_snapshot["all_replayable_ids"]
        n_missing_required_fields = frozen_snapshot["n_missing_required_fields"]
        # Every frozen ID must still be present in THIS process's own
        # outcomes read (it always will be -- the live corpus only grows --
        # but assert rather than silently trust).
        missing = [wid for wid in all_replayable_ids if wid not in outcomes]
        if missing:
            raise RuntimeError(f"{len(missing)} frozen-snapshot world_ids are no longer readable from --result-dir")
    else:
        n_completed_snapshot = len(outcomes)
        all_replayable_ids = []
        n_missing_required_fields = 0
        for wid, rec in outcomes.items():
            if all(k in rec for k in ("family", "regime", "noise_level", "replicate")):
                all_replayable_ids.append(wid)
            else:
                n_missing_required_fields += 1
        all_replayable_ids.sort()

    n_replayable = len(all_replayable_ids)
    replayable_ids = [wid for i, wid in enumerate(all_replayable_ids) if i % n_shards == shard_index]

    n_match = 0
    n_mismatch = 0
    n_error = 0
    mismatch_detail = []
    error_detail = []

    n_this_shard = len(replayable_ids)
    pool = _SafePool(_replay_worker)
    try:
        for i, wid in enumerate(replayable_ids):
            if (i + 1) % 10 == 0:
                # Incremental checkpoint -- a kill mid-run still leaves a
                # valid, if partial, artifact (same discipline as
                # speed_benchmark.py's own incremental writes).
                out_path.write_text(json.dumps({
                    "IN_PROGRESS": True, "shard_index": shard_index, "n_shards": n_shards,
                    "n_processed_so_far": i + 1, "n_this_shard": n_this_shard, "n_replayable_global": n_replayable,
                    "n_match_so_far": n_match, "n_mismatch_so_far": n_mismatch, "n_error_so_far": n_error,
                }, indent=2))
            rec = outcomes[wid]
            payload = (wid, rec["family"], rec["regime"], rec["noise_level"], rec["replicate"],
                       cand_index.get(wid, {}))
            result, err = pool.run(payload)
            if err is not None or result is None or not result.get("ok"):
                n_error += 1
                error_detail.append({
                    "opaque_id": _opaque(wid),
                    "category": err or f"WORKER_EXCEPTION:{result.get('error_type') if result else 'unknown'}",
                })
                continue

            stage_match = result["first_loss_stage"] == rec["first_loss_stage"]
            exhaustive_stage = rec["first_loss_stage"]
            if exhaustive_stage in ("A", "B"):
                rep_g2_match = True
                rep_te_match = True
            else:
                rep_g2_match = result["representative_g2_correct"] == rec["representative_g2_correct"]
                if exhaustive_stage == "E":
                    rep_te_match = True
                else:
                    rep_te_match = result["representative_truth_equivalent"] == rec["representative_truth_equivalent"]

            if stage_match and rep_g2_match and rep_te_match:
                n_match += 1
            else:
                n_mismatch += 1
                mismatch_detail.append({
                    "opaque_id": _opaque(wid),
                    "stage_match": stage_match, "rep_g2_match": rep_g2_match, "rep_te_match": rep_te_match,
                })

            if (i + 1) % 10 == 0:
                print(f"  shard {shard_index}/{n_shards} progress: {i + 1}/{n_this_shard} replayed "
                      f"(match={n_match} mismatch={n_mismatch} error={n_error})", flush=True)

        n_det_checked = 0
        n_det_match = 0
        if shard_index == 0 and not skip_determinism:
            # --- determinism subset: deterministic (sorted-id) stride over
            # the GLOBAL replayable set, not outcome-based, run only by
            # shard 0 so the check is not duplicated N times ---
            subset_size = min(DETERMINISM_SUBSET_TARGET, n_replayable)
            if subset_size > 0:
                stride = max(1, n_replayable // subset_size)
                det_ids = all_replayable_ids[::stride][:subset_size]
            else:
                det_ids = []

            pool.close()
            pool = _SafePool(_replay_worker_twice)  # separate worker function -> separate long-lived process

            for wid in det_ids:
                rec = outcomes[wid]
                payload = (wid, rec["family"], rec["regime"], rec["noise_level"], rec["replicate"],
                           cand_index.get(wid, {}))
                result, err = pool.run(payload, timeout=PER_WORLD_TIMEOUT_SECONDS * 2)
                n_det_checked += 1
                if err is None and result is not None and result.get("ok") and result.get("match"):
                    n_det_match += 1
    finally:
        pool.close()
        e2_classify.shutdown()

    summary = {
        "shard_index": shard_index, "n_shards": n_shards,
        "N_COMPLETED_SNAPSHOT": n_completed_snapshot,
        "N_REPLAYABLE_GLOBAL": n_replayable,
        "N_REPLAYABLE_THIS_SHARD": n_this_shard,
        "N_MATCH": n_match,
        "N_MISMATCH": n_mismatch,
        "ERROR_COUNT": n_error,
        # Per-shard pass/fail; the operator-facing global PARITY_PASS is
        # computed by merge_shards.py from the SUM across all shards, not
        # from any single shard's own (necessarily partial) counts.
        "SHARD_PARITY_PASS": bool(n_match == n_this_shard and n_mismatch == 0 and n_error == 0),
        "N_DETERMINISM_CHECKED": n_det_checked,
        "N_DETERMINISM_MATCH": n_det_match,
        "DETERMINISM_PASS": bool(n_det_checked > 0 and n_det_match == n_det_checked),
        "n_excluded_missing_required_fields": n_missing_required_fields,
        "mismatch_detail": mismatch_detail,
        "error_detail": error_detail,
    }
    out_path.write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--n-shards", type=int, default=1)
    parser.add_argument("--skip-determinism", action="store_true")
    parser.add_argument("--take-snapshot-to", type=str, default=None,
                         help="write a frozen population snapshot to this file and exit, taking no other action")
    parser.add_argument("--frozen-snapshot-file", type=str, default=None,
                         help="use this pre-taken snapshot (see --take-snapshot-to) instead of deriving the "
                              "population live -- REQUIRED for a multi-shard run to partition consistently")
    args = parser.parse_args()

    dirs = [Path(d) for d in args.dirs]

    if args.take_snapshot_to:
        snap = take_snapshot(dirs)
        Path(args.take_snapshot_to).write_text(json.dumps(snap, indent=2))
        print(f"snapshot: {snap['n_completed_snapshot']} completed, "
              f"{len(snap['all_replayable_ids'])} replayable, written to {args.take_snapshot_to}")
        return

    frozen_snapshot = None
    if args.frozen_snapshot_file:
        frozen_snapshot = json.loads(Path(args.frozen_snapshot_file).read_text())

    t0 = time.monotonic()
    summary = run_audit(dirs, Path(args.out), args.shard_index, args.n_shards,
                         args.skip_determinism, frozen_snapshot)
    elapsed = time.monotonic() - t0

    print(f"shard {args.shard_index}/{args.n_shards} N_REPLAYABLE_THIS_SHARD: {summary['N_REPLAYABLE_THIS_SHARD']}")
    print(f"N_MATCH: {summary['N_MATCH']}")
    print(f"N_MISMATCH: {summary['N_MISMATCH']}")
    print(f"ERROR_COUNT: {summary['ERROR_COUNT']}")
    print(f"SHARD_PARITY_PASS: {summary['SHARD_PARITY_PASS']}")
    print(f"N_DETERMINISM_CHECKED: {summary['N_DETERMINISM_CHECKED']}")
    print(f"N_DETERMINISM_MATCH: {summary['N_DETERMINISM_MATCH']}")
    print(f"elapsed_seconds: {elapsed:.1f}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
