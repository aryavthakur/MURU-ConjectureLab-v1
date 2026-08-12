# RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md

**Exact nested arithmetic and measured benchmark for the governed
objective-validation run.**

Computed **from** `muru.objval.plan2` by `scripts/ov_01_runtime_budget.py`, so
the counts cannot drift from what is executed and nested loops cannot be
miscounted by hand — the failure that cost Phase 2 (`BACKLOG.md` I4). Machine
readable: `artifacts/ov_runtime_budget.json`.

---

## Hardware

| Item | Value |
|---|---|
| Machine | 2024 MacBook Air, fanless |
| Memory | 16 GB (17 179 869 184 B) |
| Logical CPUs | 8 — **4 performance + 4 efficiency** |
| Thread caps | `OMP`, `OPENBLAS`, `MKL`, `VECLIB`, `NUMEXPR` = 1 |
| Workers | **4 independent single-process shards** |

Parallelism is independent processes rather than a worker pool: `juliacall` does
not survive multiprocessing teardown, and per-seed checkpointing already makes
the work safe to split and resume.

## Nested expansion — products, never sums

Every count below is one loop level. **Worlds × seeds**, per block:

| Block | Worlds | × Seeds | = PySR runs |
|---|---|---|---|
| `NCAL` null calibration | 100 | 30 | **3 000** |
| `G4` pure null | 100 | 30 | **3 000** |
| `G4M` mass-conditional null | 30 | 30 | **900** |
| `G1A` analytic sanity | 6 | 30 | **180** |
| `G1B` realistic conditional law | 40 | 30 | **1 200** |
| `G1C` near-degenerate challenge | 10 | 30 | **300** |
| `G2` non-collapsing | 8 | 30 | **240** |
| `G3` mass-only | 8 | 30 | **240** |
| `G5` confounded | 8 | 30 | **240** |
| `GC` measurement coupling | 9 | 30 | **270** |
| `GRT` retention-time surrogate | 4 | 30 | **120** |
| **Total** | **323** | **30** | **9 690** |

Comparison arm: **88 worlds × 10 seeds = 880 gplearn runs**
(`G1B` 40 + `G1C` 10 + `G3` 8 + first 30 `G4`).

Per world, once each and **not** per seed: one world build, one collapse fit
with H-MAIN adequacy, one Type 2 selection over the 30 stored fronts, one
flexible-ceiling fit, one F1–F12 harness on the reported representative, one
recovery scoring pass.

| Stage | Unit | Count | Loop level |
|---|---|---|---|
| world build + collapse fit | per world | 323 | 1 |
| symbolic search | per (world, seed) | 9 690 | 2 |
| comparison-arm search | per (world, seed) | 880 | 2 |
| Type 2 selection | per world | 323 | 1 |
| candidate signature | per band member | ~30–200 per world | 3 |
| falsification harness | per world | 323 | 1 |
| F10 permutations | per world | 323 × 20 = 6 460 | 2 |
| recovery scoring | per world | 323 | 1 |

## Benchmark, measured

Structured worlds are benchmarked as well as nulls, because Phase 3 found
structured worlds slower and it is true here too.

| Family | World build | Collapse fit + H-MAIN | PySR per seed, serial | gplearn per seed, serial |
|---|---|---|---|---|
| `G1B` structured | 0.00 s | 0.12 s | **2.46 s** | 3.21 s |
| `G4` null | 0.00 s | 0.12 s | **2.00 s** | 3.26 s |
| `G2` non-collapsing | 0.00 s | 0.12 s | **2.63 s** | 3.20 s |

The first PySR call in a process costs ~6.9 s because Julia JIT-compiles the
search kernels. That is paid **once per shard**, not once per run, so a warm-up
seed is discarded before timing; charging it to all 9 690 runs would overstate
the budget by more than a factor of two.

### Concurrency

Each worker warms up, then times 8 steady-state runs.

| Workers | s/seed per worker | Wall s per run | Speed-up vs serial | Verdict |
|---|---|---|---|---|
| 2 | 3.75 | 1.877 | 1.25× | rejected |
| **4** | **3.50** | **0.874** | **2.70×** | **adopted** |
| 6 | 11.33 | 1.888 | 1.24× | rejected |

Six workers are *slower*, not merely less efficient: the machine has 4
performance cores and 4 efficiency cores, so the fifth and sixth workers land on
E-cores and slow the first four. Phase 3 rejected 6 workers on memory and thermal
grounds and measured 2.97× at 4; this study reaches the same configuration by
measurement.

**Thermal caveat, stated because it is real.** Repeated back-to-back benchmarks
on a fanless machine degraded the 4-worker figure to 2.375 s/run. The 0.874 s/run
above was measured after a cool-down and is consistent with Phase 3's recorded
0.775 s/run and with its *actual* sustained run (7 200 + 680 runs in 1.69 h ≈
0.79 s/run). The projection below uses 0.874 s/run and the honest range is
**0.87–1.12 s/run**.

## Projection

```
PySR                      9 690 runs × 0.874 s              = 2.35 h
gplearn comparison arm      880 runs × 3.221 s / 4 workers  = 0.20 h
world build + collapse fit  323 worlds × 0.12 s / 4 workers = 0.00 h
select + adjudicate + recover
                            323 worlds × 3.12 s / 4 workers = 0.07 h
------------------------------------------------------------------
total                                                        2.62 h
```

At the pessimistic 1.124 s/run the total is **3.22 h**; at Phase 3's sustained
0.79 s/run it is **2.40 h**.

| Quantity | Value |
|---|---|
| Projected wall time | **2.6 h** (range 2.4–3.3 h) |
| Projected peak memory | ~4.6 GB (4 workers × ~1.15 GB, unchanged from Phase 3's measurement of the same engine at the same settings) |
| Checkpoint unit | one `(block, world, seed)` symbolic run |
| Checkpoint write | tmp file then `os.replace`, atomic on POSIX |
| Worst case lost to a crash | the 4 units in flight, ≈ 14 s |
| Progress visibility | one unbuffered line per world per shard, with elapsed and ETA |

## The 2-hour threshold

**The projection exceeds 2 hours, so the governed run does not start without
explicit approval.** The scope-reduction options, and what each costs
scientifically:

| Option | Saving | What is lost |
|---|---|---|
| `NCAL` 100 → 40 (Phase 3's size) | −1 800 runs, −0.44 h | reinstates `BACKLOG.md` I8: a 95th percentile resting on its top two or three, with intervals too wide to adjudicate a marginal candidate. This is the specific weakness the study was asked to fix |
| `G1B` moderate 20 → 10 | −300 runs, −0.07 h | the governing 80% gate resolves only to 0.1 |
| drop `G5` and `G1A` | −420 runs, −0.10 h | loses the confounding adversary and the analytic sanity anchor |
| drop the gplearn arm | −0.20 h | removes independent corroboration, which the study terms forbid removing because it is inconvenient |
| `G4` 100 → fewer | — | **not available**: the master plan requires 100 replicates |
| seeds 30 → fewer | — | **not available**: master plan §13.4 minimum |

Applying every available reduction reaches roughly **1.8 h** and gives up the
null-calibration improvement, the gate resolution, one adversary, the sanity
anchor and the corroboration arm — that is, most of what distinguishes this study
from a re-run of Phase 3 with a different selector.

**Recommendation: run the full scope.** The two blocks that dominate the cost,
`G4` (3 000 runs) and `NCAL` (3 000 runs), are the two that carry the
false-positive gate and the threshold table, which are exactly the parts of the
machinery a Type 2 claim rests on.
