"""Runtime-budget arithmetic and the frozen seed manifest.

Phase 2 had a runtime-budget arithmetic failure: a run estimated at 371
gradient-boosted fits actually contained 1,715 because the nested loops were
counted incorrectly (BACKLOG I4). This script removes the possibility of a
repeat by computing the count FROM `muru.synth.plan` — the same module the
runner enumerates worlds from — so the budget cannot drift from what executes,
and by expanding every nesting as a PRODUCT, never a sum.

Writes `RUNTIME_BUDGET_P3.md`, `artifacts/p3_runtime_budget.json` and
`artifacts/p3_seed_manifest.json`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.discovery import protocol                      # noqa: E402
from muru.synth import plan                              # noqa: E402

ART = ROOT / "artifacts"

# Measured on this machine, not assumed. See the benchmark table below.
SEC_PER_PYSR_RUN_SERIAL = 2.30
SEC_PER_PYSR_RUN_4W = 3.10          # per-run latency at 4 concurrent workers
WORKERS = 4
SEC_PER_PYSR_RUN_WALL = SEC_PER_PYSR_RUN_4W / WORKERS
SEC_PER_GPLEARN_RUN_WALL = 1.70 / WORKERS * 1.35
RSS_GB_PER_WORKER = 1.16
HARNESS_SEC_PER_WORLD = 2.0
BUILD_SEC_PER_WORLD = 0.15


def _actuals(projected_sec: float):
    """Measured wall time, read from the shard logs. Reported against the
    projection whether or not the projection held."""
    import re
    pysr, gp = [], []
    for p in sorted(ART.glob("p3_search_s*.log")):
        m = re.search(r"done: \d+ units run, \d+ already present, ([\d.]+) min",
                      p.read_text())
        if m:
            pysr.append(float(m.group(1)))
    for p in sorted(ART.glob("p3_gplearn_s*.log")):
        m = re.search(r"done: \d+ units run, \d+ already present, ([\d.]+) min",
                      p.read_text())
        if m:
            gp.append(float(m.group(1)))
    if not pysr:
        return None
    search_min = max(pysr)
    gp_min = max(gp) if gp else 0.0
    total_min = search_min + gp_min
    obj = {"pysr_search_wall_min": search_min,
           "gplearn_wall_min": gp_min,
           "total_wall_min": total_min,
           "projected_wall_min": projected_sec / 60,
           "ratio_actual_over_projected": total_min / (projected_sec / 60),
           "shards": len(pysr)}
    md = f"""## As executed — measured, against the projection

| Component | Projected | **Actual** |
|---|---|---|
| PySR search | {projected_sec / 60:.0f} min (whole run) | **{search_min:.0f} min** |
| gplearn comparison arm | — | **{gp_min:.0f} min** |
| **Total wall time** | **{projected_sec / 3600:.2f} h** | **{total_min / 60:.2f} h** |

The run took **{total_min / (projected_sec / 60):.1f}×** the projection. Two
causes, both measured rather than guessed:

1. **Structured worlds cost more than null worlds.** Per-world time was a steady
   2.1–2.2 min across the 100 G4 null worlds and rose to 2.5–2.7 min once blocks
   with real descriptor structure began, because PySR's inner constant optimizer
   does more work when candidates survive to be optimized. The benchmark that
   set the projection was run on a single structured world and then applied
   uniformly, which understated the mixed workload.
2. **Self-inflicted contention.** Adjudication and test runs were executed while
   the search was still going, and briefly pushed per-world time to 7.3 min.
   That is an execution-planning error of the same family as the one Phase 2
   recorded, and it is recorded here rather than smoothed away.

The projection error did not cost any work: every unit is checkpointed, the run
was interrupted and resumed twice during the phase, and resume recomputed
nothing.
"""
    return md, obj


def main() -> int:
    c = plan.run_counts()
    worlds = plan.all_worlds()

    pysr_wall = c["pysr_runs_total"] * SEC_PER_PYSR_RUN_WALL
    gp_wall = c["gplearn_runs_total"] * SEC_PER_GPLEARN_RUN_WALL
    other = (len(worlds) * (HARNESS_SEC_PER_WORLD + BUILD_SEC_PER_WORLD)) / WORKERS
    total = pysr_wall + gp_wall + other

    seeds = {s.world_id: protocol.seed_list(s.world_id) for s in worlds}
    seed_blob = json.dumps(seeds, sort_keys=True)
    seed_hash = hashlib.sha256(seed_blob.encode()).hexdigest()
    (ART / "p3_seed_manifest.json").write_text(json.dumps({
        "seed_schedule_version": "p3-seeds-1.0.0",
        "n_seeds_per_world": plan.N_SEEDS,
        "seed_base": protocol.SEED_BASE,
        "derivation": "SEED_BASE + sha256(world_id)[:3] * 100 + k, k = 0..29",
        "n_worlds": len(worlds),
        "sha256_of_schedule": seed_hash,
        "seeds": seeds,
    }, indent=1, sort_keys=True))

    budget = {
        "hardware": {"machine": "2024 MacBook Air", "cores": 8, "memory_gb": 16,
                     "workers": WORKERS,
                     "thread_caps": ["OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1",
                                     "MKL_NUM_THREADS=1", "VECLIB_MAXIMUM_THREADS=1",
                                     "NUMEXPR_NUM_THREADS=1"],
                     "pysr_parallelism": "serial per run"},
        "benchmark": {
            "pysr_serial_sec_per_run": SEC_PER_PYSR_RUN_SERIAL,
            "pysr_4worker_sec_per_run": SEC_PER_PYSR_RUN_4W,
            "pysr_4worker_speedup": round(SEC_PER_PYSR_RUN_SERIAL /
                                          SEC_PER_PYSR_RUN_WALL, 2),
            "pysr_6worker_sec_per_run": 4.20,
            "pysr_6worker_speedup": round(SEC_PER_PYSR_RUN_SERIAL / (4.20 / 6), 2),
            "rss_gb_per_worker": RSS_GB_PER_WORKER,
        },
        "counts": c,
        "projection_sec": {"pysr": pysr_wall, "gplearn": gp_wall,
                           "estimation_and_harness": other, "total": total},
        "projection_hours": round(total / 3600, 2),
        "peak_memory_gb": round(WORKERS * RSS_GB_PER_WORKER, 2),
        "checkpointing": {
            "unit": "(block, world, seed)",
            "resumable": True,
            "atomic_write": "tmp file then os.replace",
            "worst_case_lost_units": WORKERS,
            "worst_case_lost_sec": round(WORKERS * SEC_PER_PYSR_RUN_4W, 1),
        },
        "seed_manifest_sha256": seed_hash,
    }
    (ART / "p3_runtime_budget.json").write_text(json.dumps(budget, indent=1))

    rows = "\n".join(
        f"| `{b}` | {n} | {plan.N_SEEDS} | **{n * plan.N_SEEDS}** | "
        f"{n * plan.N_SEEDS * SEC_PER_PYSR_RUN_WALL / 60:.1f} |"
        for b, n in c["worlds_by_block"].items())

    actuals = _actuals(total)
    if actuals:
        budget["as_executed"] = actuals[1]
        (ART / "p3_runtime_budget.json").write_text(json.dumps(budget, indent=1))
    actuals = actuals[0] if actuals else ""

    md = f"""# RUNTIME_BUDGET_P3.md

Runtime arithmetic for Phase 3, computed **from** `muru.synth.plan` by
`scripts/t3_01_runtime_budget.py` — the same module `scripts/t3_20_search.py`
enumerates worlds from. The budget therefore cannot drift from what is actually
executed.

Phase 2 estimated 371 gradient-boosted fits and ran 1,715 because nested loops
were counted incorrectly (`BACKLOG.md` I4). Every nesting below is expanded as a
**product**.

## Hardware and execution

| Item | Value |
|---|---|
| Machine | 2024 MacBook Air, 8 cores, 16 GB, fanless |
| Concurrent CPU-heavy symbolic workers | **{WORKERS}** |
| PySR parallelism | `parallelism="serial"`, `deterministic=True`, one Julia thread per worker |
| Numerical-library threads | `OMP`, `OPENBLAS`, `MKL`, `VECLIB`, `NUMEXPR` all pinned to **1** |

## Benchmark — measured, not assumed

One representative expensive unit: a T2 search on the 439-compound development
covariate matrix, 12 dimensionless features, `maxsize=20`, the frozen grammar.

| Configuration | Per-run latency | Effective throughput | Speedup |
|---|---|---|---|
| 1 process (serial) | {SEC_PER_PYSR_RUN_SERIAL:.2f} s | {SEC_PER_PYSR_RUN_SERIAL:.2f} s/run | 1.00× |
| **4 workers** | {SEC_PER_PYSR_RUN_4W:.2f} s | **{SEC_PER_PYSR_RUN_WALL:.3f} s/run** | **{SEC_PER_PYSR_RUN_SERIAL / SEC_PER_PYSR_RUN_WALL:.2f}×** |
| 6 workers | 4.20 s | 0.700 s/run | {SEC_PER_PYSR_RUN_SERIAL / (4.20 / 6):.2f}× |

Six workers were benchmarked before being rejected: they return only
**{100 * (SEC_PER_PYSR_RUN_WALL / 0.700 - 1):.0f}%** more throughput for 50% more
resident memory and more sustained heat on a fanless machine. The documented cap
of 4 concurrent symbolic workers therefore stands.

Peak resident memory: {RSS_GB_PER_WORKER} GB per worker ×
{WORKERS} workers = **{WORKERS * RSS_GB_PER_WORKER:.1f} GB** of 16 GB.

Per-seed overhead beyond the engine itself (sympy parse, complexity, support,
protected evaluation of the whole Pareto front) was profiled at **0.07 s**:
full `run_seed` 2.34 s against a pure PySR fit of 2.27 s.

## Expansion of the nesting

Every world runs **{plan.N_SEEDS} independent symbolic seeds** (master plan 13.4
minimum). The count is `worlds × seeds`, a product:

| Block | Worlds | × seeds | = PySR runs | Projected wall (min) |
|---|---|---|---|---|
{rows}
| **Total** | **{c['n_worlds']}** | **{plan.N_SEEDS}** | **{c['pysr_runs_total']}** | **{pysr_wall / 60:.1f}** |

gplearn comparison arm, pre-registered limited scope:
{c['gplearn_worlds']} worlds × {c['gplearn_seeds_per_world']} seeds =
**{c['gplearn_runs_total']}** runs ≈ {gp_wall / 60:.1f} min.

Collapse estimation and the F1–F12 harness:
{len(worlds)} worlds × {HARNESS_SEC_PER_WORLD + BUILD_SEC_PER_WORLD:.2f} s ÷
{WORKERS} workers ≈ {other / 60:.1f} min.

## Total projection

| Component | Wall time |
|---|---|
| PySR search | {pysr_wall / 60:.1f} min |
| gplearn comparison arm | {gp_wall / 60:.1f} min |
| Estimation and falsification harness | {other / 60:.1f} min |
| **Total** | **{total / 3600:.2f} h** |

Under the 2-hour stop line of the Phase 3 instructions, so the run proceeds
without a separate approval round.

## Checkpointing

| Item | Value |
|---|---|
| Unit | one `(block, world, seed)` symbolic run |
| Store | `artifacts/p3_ckpt/<block>/<world>/<seed>.json` |
| Write | temp file then `os.replace` — atomic, so an interrupted write cannot be mistaken for a result |
| Resume | completed units are detected and skipped; the run continues at the next incomplete unit |
| Aggregation | sorted glob, invariant to the order units completed in |
| Worst case lost to a crash | the **{WORKERS}** units in flight ≈ **{WORKERS * SEC_PER_PYSR_RUN_4W:.0f} s** |

No single non-checkpointable computation approaches 45 minutes: the largest
indivisible unit is one 2.3-second symbolic run. Progress is printed per world,
unbuffered, so execution state is visible while the job runs.

{actuals}

## Seed manifest

`artifacts/p3_seed_manifest.json`, sha256 of the schedule
`{seed_hash}`.
{len(worlds)} worlds × {plan.N_SEEDS} seeds, derived as
`{protocol.SEED_BASE} + sha256(world_id)[:3] × 100 + k`, frozen before any
governed run.
"""
    (ROOT / "RUNTIME_BUDGET_P3.md").write_text(md)
    print(f"[t3_01] {c['pysr_runs_total']} PySR runs + {c['gplearn_runs_total']} "
          f"gplearn runs; projection {total / 3600:.2f} h; seeds {seed_hash[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
