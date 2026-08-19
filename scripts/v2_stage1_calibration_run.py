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

    import multiprocessing as mp
    ctx = mp.get_context("fork")
    done = {"OK": 0, "CACHED": 0}
    failures = []
    with ctx.Pool(a.workers, initializer=_bound_memory, maxtasksperchild=1) as pool:
        for cid, status in pool.imap_unordered(_worker, ids, chunksize=1):
            if status in done:
                done[status] += 1
            else:
                failures.append({"case_id": cid, "status": status})
            n = done["OK"] + done["CACHED"] + len(failures)
            if n % 25 == 0:
                print(f"[STAGE1] {n}/{len(ids)} worlds  ok={done['OK']} "
                      f"cached={done['CACHED']} failed={len(failures)}", flush=True)
    summary = {"worlds_requested": len(ids), **done, "failures": failures,
               "n_failed": len(failures)}
    (OUT / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2)[:1500], flush=True)


if __name__ == "__main__":
    main()
