# RUNTIME_BUDGET_P3.md

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
| Concurrent CPU-heavy symbolic workers | **4** |
| PySR parallelism | `parallelism="serial"`, `deterministic=True`, one Julia thread per worker |
| Numerical-library threads | `OMP`, `OPENBLAS`, `MKL`, `VECLIB`, `NUMEXPR` all pinned to **1** |

## Benchmark — measured, not assumed

One representative expensive unit: a T2 search on the 439-compound development
covariate matrix, 12 dimensionless features, `maxsize=20`, the frozen grammar.

| Configuration | Per-run latency | Effective throughput | Speedup |
|---|---|---|---|
| 1 process (serial) | 2.30 s | 2.30 s/run | 1.00× |
| **4 workers** | 3.10 s | **0.775 s/run** | **2.97×** |
| 6 workers | 4.20 s | 0.700 s/run | 3.29× |

Six workers were benchmarked before being rejected: they return only
**11%** more throughput for 50% more
resident memory and more sustained heat on a fanless machine. The documented cap
of 4 concurrent symbolic workers therefore stands.

Peak resident memory: 1.16 GB per worker ×
4 workers = **4.6 GB** of 16 GB.

Per-seed overhead beyond the engine itself (sympy parse, complexity, support,
protected evaluation of the whole Pareto front) was profiled at **0.07 s**:
full `run_seed` 2.34 s against a pure PySR fit of 2.27 s.

## Expansion of the nesting

Every world runs **30 independent symbolic seeds** (master plan 13.4
minimum). The count is `worlds × seeds`, a product:

| Block | Worlds | × seeds | = PySR runs | Projected wall (min) |
|---|---|---|---|---|
| `NCAL` | 40 | 30 | **1200** | 15.5 |
| `G4` | 100 | 30 | **3000** | 38.8 |
| `G4M` | 30 | 30 | **900** | 11.6 |
| `G1` | 30 | 30 | **900** | 11.6 |
| `G2` | 8 | 30 | **240** | 3.1 |
| `G3` | 8 | 30 | **240** | 3.1 |
| `G5` | 8 | 30 | **240** | 3.1 |
| `GC` | 9 | 30 | **270** | 3.5 |
| `GRT` | 4 | 30 | **120** | 1.6 |
| `GA` | 3 | 30 | **90** | 1.2 |
| **Total** | **240** | **30** | **7200** | **93.0** |

gplearn comparison arm, pre-registered limited scope:
68 worlds × 10 seeds =
**680** runs ≈ 6.5 min.

Collapse estimation and the F1–F12 harness:
240 worlds × 2.15 s ÷
4 workers ≈ 2.1 min.

## Total projection

| Component | Wall time |
|---|---|
| PySR search | 93.0 min |
| gplearn comparison arm | 6.5 min |
| Estimation and falsification harness | 2.1 min |
| **Total** | **1.69 h** |

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
| Worst case lost to a crash | the **4** units in flight ≈ **12 s** |

No single non-checkpointable computation approaches 45 minutes: the largest
indivisible unit is one 2.3-second symbolic run. Progress is printed per world,
unbuffered, so execution state is visible while the job runs.

## As executed — measured, against the projection

| Component | Projected | **Actual** |
|---|---|---|
| PySR search | 102 min (whole run) | **162 min** |
| gplearn comparison arm | — | **17 min** |
| **Total wall time** | **1.69 h** | **2.98 h** |

The run took **1.8×** the projection. Two
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


## Seed manifest

`artifacts/p3_seed_manifest.json`, sha256 of the schedule
`eff5a1bb17eb482844ac217248935925f3a094c7602667045d2e48b11de951e9`.
240 worlds × 30 seeds, derived as
`900000 + sha256(world_id)[:3] × 100 + k`, frozen before any
governed run.
