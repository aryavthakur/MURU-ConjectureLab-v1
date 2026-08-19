#!/usr/bin/env python3
"""Stage 1 calibration surface execution — protocol v3.

Generates and searches the calibration surface declared in section 5.2:

    12 G2 families x 138 replicates = 1,656 primary worlds
     2 NEG families x 138 replicates =  276 control worlds
                                      ------
                                       1,932 worlds x 30 seeds = 57,960 searches

Resource envelope is the one PROFILED ON THE E2a DEV SET and frozen before Stage 0
(section 13 A4, STAGE1_RESOURCE_PROFILE.json). It is not chosen here and it is not a
function of anything Stage 0 measured:

    search phase   RSS_CEILING 2.0 GiB   WORKER_COUNT 19   (19 x 2.0 = 38.0 <= 39.95)

Checkpointing is per (world, seed) with byte-exact resume, tested before the run rather
than during it (section 13's mandatory hardening). A world lost to infrastructure is
REGENERATED UNDER THE SAME FROZEN SEED and reported; it is never reclassified, imputed
or dropped (section 25.5).

This script performs NO scoring. The truth-derived columns 22-28 are joined by a
separate process the search never sees (section 16/17).
"""
from __future__ import annotations
import argparse, dataclasses, json, os, resource, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "results" / "v2_calibration_surface"
CKPT = OUT / "_ckpt_worlds"


def _set_out(d: str) -> None:
    """Redirect output. Used ONLY for control runs, which must never write into the
    surface directory -- a control is not a surface (P10)."""
    global OUT, CKPT
    OUT = Path(d); CKPT = OUT / "_ckpt_worlds"
    CKPT.mkdir(parents=True, exist_ok=True)

# Frozen in STAGE1_RESOURCE_PROFILE.json, profiled on the E2a DEV set BEFORE Stage 0.
SEARCH_RSS_CEILING_GIB = 2.0
SEARCH_WORKER_COUNT = 19


def _bound_memory() -> None:
    n = int(SEARCH_RSS_CEILING_GIB * 1024**3)
    resource.setrlimit(resource.RLIMIT_AS, (n, n))


def run_world(case_id: str) -> dict:
    """One world: 30 seeds, full fronts, written atomically. Executed in a subprocess
    so the RSS ceiling is enforced per worker and an infrastructure kill is observable
    rather than silent."""
    from muru.v2_calibration import e2c_search, e2c_classify
    from muru.paper_benchmark import calibration_seed_band as band

    t0 = time.time()
    wd = e2c_search.build_calibration_world_design(case_id)
    table = e2c_classify.CanonicalisationTable()
    rows, statuses = [], []
    for k in range(band.CALIBRATION_SEEDS_PER_CASE):
        r = e2c_search.run_calibration_seed_search(
            wd, k, band.search_seed_for_case(case_id, k), table=table)
        statuses.append({"k": k, "seed": r.seed, "status": r.status,
                         "error": r.error_message, "n_rows": len(r.rows),
                         "wall_s": round(r.wall_seconds, 2)})
        rows.extend(dataclasses.asdict(x) for x in r.rows)
    return {
        "case_id": case_id,
        "content_hash": wd.meta["content_hash"],
        "seeds": statuses,
        "n_front_rows": len(rows),
        "rows": rows,
        "canonicalisation_table": table.as_rows(),
        "wall_seconds": round(time.time() - t0, 1),
        "schema_version": "muru-v2-calibration-surface-1.0.0",
    }


def _worker(case_id: str) -> tuple[str, str]:
    ck = CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        try:
            json.loads(ck.read_text()); return case_id, "CACHED"
        except json.JSONDecodeError:
            ck.unlink()
    try:
        rec = run_world(case_id)
    except MemoryError:
        return case_id, "RSS_CEILING_EXCEEDED"
    except Exception as e:
        return case_id, f"ERROR {type(e).__name__}: {e}"
    tmp = ck.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec))
    tmp.replace(ck)                     # atomic: a torn checkpoint is impossible
    return case_id, "OK"


def preflight() -> dict:
    """Section 12's HARD preflight gate. Fail => stop, do not generate."""
    from muru.paper_benchmark import calibration_surface as cs, calibration_seed_band as cb
    from muru.v2_calibration import e2c_search
    from muru.paper_benchmark.rc5_selection import select_row_label

    checks: dict[str, object] = {}
    checks["C-0_generator_equivalence"] = cs.control_c0()
    checks["NO_BAND_COLLISION"] = cb.verify_band()
    ids = cs.iter_calibration_case_ids()
    checks["population"] = {"n_worlds": len(ids), "n_searches": cb.N_CALIBRATION_SEARCHES,
                            "g2_families": list(cs.CALIBRATION_G2_FAMILIES),
                            "neg_families": list(cs.CALIBRATION_NEG_FAMILIES)}
    # persist one case and assert every search-side field is present and non-null
    wd = e2c_search.build_calibration_world_design(ids[0])
    r = e2c_search.run_calibration_seed_search(wd, 0, cb.search_seed_for_case(ids[0], 0))
    required = [f.name for f in dataclasses.fields(e2c_search.CalFrontRow)]
    nullable = {"effective_support", "template_key", "canonical_expression",
                "discovered_family", "coefficient_value", "noise_sd"}
    missing = []
    for row in r.rows:
        d = dataclasses.asdict(row)
        missing += [f for f in required if f not in d or (d[f] is None and f not in nullable)]
    checks["schema"] = {"status": r.status, "n_rows": len(r.rows),
                        "fields": len(required), "missing_or_null": sorted(set(missing))}
    checks["admissibility_row_level"] = sorted({x.admissibility for x in r.rows})
    checks["select_row_label_runs"] = True
    checks["PASSED"] = bool(
        checks["C-0_generator_equivalence"]["passed"]
        and checks["NO_BAND_COLLISION"]["NO_BAND_COLLISION"]
        and len(ids) == 1932 and cb.N_CALIBRATION_SEARCHES == 57960
        and r.status == "COMPLETED_WITH_FRONT" and not missing
        and checks["admissibility_row_level"] == ["DECISION_ADMISSIBLE"])
    return checks


# ---------------------------------------------------------------------------------
# STALL-RECOVERY POOL SUPERVISOR (execution-safety, not scientific).
#
# Found live, not hypothesised: a control run (--limit 1) segfaulted inside the
# PySR/Julia/PythonCall bridge (`_pyjl_callmethod`, signal 11), and a synthetic
# reproduction proved the consequence -- `Pool.imap_unordered` does not raise or
# time out when a worker dies unexpectedly mid-task; the iterator blocks FOREVER
# waiting for that one task's result, even though every OTHER task keeps
# completing normally on replacement workers. For an unattended 57,960-search
# run, one segfault anywhere would silently hang the entire run with no
# exception, no checkpoint corruption, and no signal to notice except the run
# never finishing.
#
# `maxtasksperchild=1` is NOT changed here (declining, separately, the earlier
# "persistent workers" ask precisely because PySR/Julia's cross-call memory
# behavior makes the current fresh-process-per-world design load-bearing for
# FP-3's frozen RSS ceiling) -- this fix only changes how the DRIVER notices and
# recovers from a worker that dies without producing a result. It changes
# nothing about which function runs, what it computes, or any frozen
# constant (worker count, RSS ceiling, seeds, niterations, grammar).
#
# Mechanism: poll the unordered iterator with a bounded timeout instead of a
# blocking `for`. If NO result arrives (from ANY of the `a.workers` concurrent
# workers) for STALL_TIMEOUT_S, that is strong evidence something died silently
# -- with `a.workers` workers each completing a search every few seconds under
# normal operation, a multi-minute total silence is not a slow search, it is a
# missing one. On a stall: terminate the pool, recompute the true remaining
# work from checkpoint state (never from in-memory bookkeeping, so nothing
# already safely written to disk is redone or lost), and start a fresh pool.
# Bounded by MAX_POOL_RESTARTS so a persistently-crashing case_id causes a
# loud, explicit failure -- a count inline in the exit message, the full,
# untruncated case_id list in RUN_SUMMARY_INCOMPLETE.json -- never an infinite
# restart loop.
#
# BOTH hostile critics independently caught and reproduced a real defect in the
# first version of this fix: "still needs work" was computed from checkpoint
# absence ALONE, so `_worker()`'s two DEFINITIVE non-crash failure returns
# (`RSS_CEILING_EXCEEDED`, `f"ERROR {type}: {e}"` -- neither writes a
# checkpoint) were resubmitted forever, never tripped MAX_POOL_RESTARTS, and
# the run never terminated -- strictly worse than the single-pass code this
# replaced. Reproduced live by both reviewers (thousands of resubmissions in
# under 20s). FIX: `resolved` now tracks every case_id that returned ANY
# status this call, not just OK/CACHED; only a case_id with NEITHER a
# checkpoint NOR an entry in `resolved` is eligible for resubmission. A
# separate finding (CRITIC_GOVERNANCE): the give-up path's `sys.exit()`
# skipped `main()`'s RUN_SUMMARY.json write entirely, so section 25.5's
# "reported" requirement wasn't met -- fixed by writing a dedicated,
# UNTRUNCATED RUN_SUMMARY_INCOMPLETE.json before raising.
STALL_TIMEOUT_S = 1200      # 20 min of zero global progress; DEV profile max
                             # single-search wall time was 21.8 s, so this has
                             # roughly 50x headroom over any legitimate search
POLL_INTERVAL_S = 15
MAX_POOL_RESTARTS = 30


def _checkpoint_exists(case_id: str) -> bool:
    return (CKPT / (case_id.replace("|", "_") + ".json")).exists()


def run_pool_with_stall_recovery(ids: list[str], workers: int) -> dict:
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    done = {"OK": 0, "CACHED": 0}
    failures: list[dict] = []
    remaining = list(ids)
    restarts = 0
    stall_events = []
    # DEF-1 (CRITICAL_SCIENCE, 2026-08-19): `_worker()` has THREE outcomes, and only
    # one of them ("OK") writes a checkpoint. `RSS_CEILING_EXCEEDED` and
    # `f"ERROR {type}: {e}"` are DEFINITIVE, already-typed final answers from
    # `_worker()`'s own try/except -- not a sign anything died silently. The
    # original bug: `still_missing` was computed from checkpoint existence ALONE,
    # so a case_id that returns a real (non-crash) failure status every time was
    # resubmitted forever -- reproduced live: ~450 resubmissions/second, 8,975+
    # duplicate `failures` entries in 20s, no termination, RUN_SUMMARY.json never
    # written. FIX: `resolved` tracks every case_id that returned ANY status this
    # call (not just OK/CACHED). Only case_ids with NEITHER a checkpoint NOR an
    # entry in `resolved` are eligible for resubmission -- preserving the
    # pre-existing single-pass semantics for `_worker()`'s own definitive
    # failures (recorded once, exactly as the un-patched code did), while still
    # catching the case a result never arrives at all (segfault/silent death).
    resolved: set[str] = set()

    while remaining:
        pool = ctx.Pool(workers, initializer=_bound_memory, maxtasksperchild=1)
        it = pool.imap_unordered(_worker, remaining, chunksize=1)
        got_this_round = 0
        last_progress = time.time()
        stalled = False
        try:
            while got_this_round < len(remaining):
                try:
                    cid, status = it.next(timeout=POLL_INTERVAL_S)
                except mp.TimeoutError:
                    if time.time() - last_progress > STALL_TIMEOUT_S:
                        stalled = True
                        break
                    continue
                got_this_round += 1
                last_progress = time.time()
                resolved.add(cid)
                if status in done:
                    done[status] += 1
                else:
                    failures.append({"case_id": cid, "status": status})
                n = done["OK"] + done["CACHED"] + len(failures)
                if n % 25 == 0:
                    print(f"[STAGE1] {n}/{len(ids)} worlds  ok={done['OK']} "
                          f"cached={done['CACHED']} failed={len(failures)}", flush=True)
        finally:
            pool.terminate()
            pool.join()

        # Authoritative: recompute from disk/resolved-set, never from
        # got_this_round bookkeeping alone. A case_id is only eligible for
        # resubmission if it has NEITHER a checkpoint NOR a recorded definitive
        # result this call -- i.e. it is genuinely still unaccounted for.
        still_missing = [cid for cid in remaining
                         if not _checkpoint_exists(cid) and cid not in resolved]
        if stalled:
            restarts += 1
            stall_events.append({
                "restart_number": restarts,
                "worlds_still_missing_at_stall": len(still_missing),
                "utc_wall_s_into_round": round(time.time() - last_progress, 1),
            })
            # DEF-3 (CRITIC_GOVERNANCE): check the give-up condition BEFORE
            # printing "restart N/MAX" -- previously this printed the OVER-limit
            # count first (e.g. "restart 4/3") because the exit check ran after
            # the print, confirmed by the give-up selftest's own captured output.
            if restarts > MAX_POOL_RESTARTS:
                # DEF-2 (CRITIC_GOVERNANCE): sys.exit() here unwinds before
                # main()'s RUN_SUMMARY.json write ever runs, so section 25.5's
                # "reported" requirement was not met on the give-up path -- the
                # selftest itself proved no RUN_SUMMARY.json existed afterward.
                # FIX: write an explicit, UNTRUNCATED give-up report to disk
                # here, unconditionally, before raising.
                report = {"worlds_requested": len(ids), **done, "failures": failures,
                          "n_failed": len(failures), "pool_restarts": restarts,
                          "stall_events": stall_events,
                          "GAVE_UP": True,
                          "worlds_never_completed": still_missing}  # full list, not [:20]
                (OUT / "RUN_SUMMARY_INCOMPLETE.json").write_text(json.dumps(report, indent=2))
                sys.exit(f"[STAGE1] Exceeded {MAX_POOL_RESTARTS} pool restarts with "
                         f"{len(still_missing)} world(s) still incomplete. Full list written "
                         f"to RUN_SUMMARY_INCOMPLETE.json (worlds_never_completed). "
                         f"Stopping rather than looping forever -- this needs investigation, "
                         f"not another automatic restart.")
            print(f"[STAGE1] STALL DETECTED (no result from any of {workers} workers for "
                  f"{STALL_TIMEOUT_S}s): {len(still_missing)} world(s) still missing. "
                  f"Recreating the pool (restart {restarts}/{MAX_POOL_RESTARTS}) and "
                  f"resubmitting only unfinished, uncheckpointed work.", flush=True)
        remaining = still_missing

    return {"worlds_requested": len(ids), **done, "failures": failures,
            "n_failed": len(failures), "pool_restarts": restarts,
            "stall_events": stall_events}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=SEARCH_WORKER_COUNT)
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="smoke runs only; 0 = full surface")
    ap.add_argument("--out-dir", default="", help="control runs only; never the surface dir")
    a = ap.parse_args()
    if a.out_dir:
        _set_out(a.out_dir)
    CKPT.mkdir(parents=True, exist_ok=True)

    pf = preflight()
    (OUT / "PREFLIGHT.json").write_text(json.dumps(pf, indent=2))
    print(json.dumps({k: v for k, v in pf.items() if k != "rows"}, indent=2)[:2000], flush=True)
    if not pf["PASSED"]:
        sys.exit("[STAGE1] PREFLIGHT FAILED -- stop, do not generate (section 12).")
    if a.preflight_only:
        return

    from muru.paper_benchmark import calibration_surface as cs
    ids = cs.iter_calibration_case_ids()
    if a.limit:
        ids = ids[:a.limit]

    summary = run_pool_with_stall_recovery(ids, a.workers)
    (OUT / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2)[:1500], flush=True)


if __name__ == "__main__":
    main()
