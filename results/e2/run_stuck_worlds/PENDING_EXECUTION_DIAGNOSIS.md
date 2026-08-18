# PENDING_EXECUTION_DIAGNOSIS: 4 more worlds found stuck in the 6-shard regime

**Status as of 2026-08-17 11:29 EDT: quarantined, retries stopped on the production host before consuming a further 3-hour cycle each. NOT classified scientifically as failed. NOT omitted from the 540-world population. NOT substituted.**

## Worlds
| World ID | Shard (under n_shards=6) |
|---|---|
| `V2C\|E2\|mass_power\|c_low\|n_strong\|r007` | 1 |
| `V2C\|E2\|mass_power\|c_high\|n_default\|r003` | 3 |
| `V2C\|E2\|mass_saturating_descriptor\|c_mid\|n_strong\|r010` | 4 |
| `V2C\|E2\|mass_affine_descriptor\|c_low\|n_noiseless\|r011` | 5 |

Execution commit: `4892c76` and subsequent execution-only commits (no scientific file among them). Same frozen search budget, grammar, classifier, `SIMPLIFY_TIMEOUT_SECONDS=5` as every other world.

## How this was found
Each is the deterministic first-in-order not-yet-done world for its shard. Because `_already_done()` (global) never marks a world done until its search completes and persists, every shard restart necessarily retries the exact same first-in-queue world -- so a shard whose first world never finishes can never reach its other 89 worlds, no matter how many times its supervisor restarts it. The staleness watchdog (3-hour threshold) was catching and restarting all four shards every ~3 hours, but each restart simply re-attempted the same stuck world and hit the same wall again -- a deterministic retry loop, not forward progress. This mirrors the original poison-world pattern (`E2_EXECUTION_DEVIATION.md` \S13) but on a much longer (~3h vs ~7min) cycle, and was distinguished from the original class of failure (fast, clean external SIGKILL) via live `sample` inspection before treating it the same way: two samples 20s apart of shard 1's stuck process showed a deep, evolving stack of sympy `type_call`/`slot_tp_new`/`slot_tp_richcompare`/`tuplecontains` recursion -- consistent with expensive but at-least-partially-live symbolic computation, not a frozen no-op loop -- and a peak physical footprint of 1.8G (current 990M), i.e. real memory churn, not zero activity. This does not rule out that the computation is genuinely unbounded (as opposed to merely very slow); it was not left running long enough past 3 hours on the production host to distinguish the two, per the same "stop before it materially consumes further resources" threshold already applied to the original poison world.

## What was done
Each shard's own supervisor and process was stopped, then relaunched restricted (`--only-worlds-file`) to its other 89 worlds in an **isolated output directory** (`results/e2/run_shard{1,3,4,5}_healthy/`) -- not the shared `results/e2/run/`, to avoid the exact output-file race the standing instruction warns against (multiple `--shard-index 0 --n-shards 1` processes, the only combination that passes the ordinal-modulo pre-filter for an arbitrary world subset, would otherwise write to the same filename). These will be merged into `results/e2/run/` once complete, verified for world_id uniqueness first. No further retries of the 4 stuck worlds themselves were started on the production host.

## What resolves this
Same disposition as the original poison world (`E2_EXECUTION_DEVIATION.md` \S13/\S8 of `PENDING_EXECUTION_DIAGNOSIS.md` for the first one): re-attempt each, alone, in a clean low-contention environment, exact same commit/environment/seed/budget/classifier/timeout; if it succeeds there, merge only after a parity check against already-completed ordinary worlds in that environment; if it fails repeatedly even there, stop and record a dedicated execution diagnosis rather than inventing a scientific workaround. E2 completion accounting must treat all five quarantined worlds (this file's four plus the original) as **535 ordinary + 5 pending** until resolved.
