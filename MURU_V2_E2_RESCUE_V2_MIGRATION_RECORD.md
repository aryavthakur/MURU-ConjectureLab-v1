# MURU V2 E2 Rescue-v2 Migration Record

Migration executed 2026-08-17, following the already-frozen procedure in
`MURU_V2_E2_RESCUE_V2_FEASIBILITY.md`, after the full-corpus parity gate
passed (`N_REPLAYABLE=369, N_MATCH=369, N_MISMATCH=0, ERROR_COUNT=0,
PARITY_PASS=TRUE, DETERMINISM_PASS=TRUE`) and the user accepted
`SAFE_TO_MIGRATE_FROM_CURRENT_E2`. This document records what was actually
done, in the 16-step required order, including the one unplanned incident
that occurred mid-migration.

No scientific definition, protocol, or MURU decision changed. No partial
A/B/C/D/E stage frequency, rate, or count is recorded anywhere in this
document or its companion provenance JSON.

## Steps 1-2: Atomic snapshot and inventory

Old E2 production worktree at time of snapshot:
`.claude/worktrees/exp-v2-e2-pareto-observability`, branch
`exp/v2-e2-pareto-observability`, HEAD `f271b99` ("E2: record and recover
from a total simultaneous process-group loss" -- itself a record of the
incident described in step 3-4 below, committed by a *different* session
before this migration's own shutdown).

First checkpoint (`checkpoint_manifest.json` + `checkpoint_summary.json`,
world-ID/timing/hash fields only, no scientific outcome read): 409/540
unique world_ids, 45 result files hashed across the 5 healthy directories
(`run`, `run_shard1_healthy`, `run_shard3_healthy`, `run_shard4_healthy`,
`run_shard5_healthy`).

## Steps 3-4: Clean shutdown and verification

Old E2 supervisors and workers were stopped with SIGTERM only; no SIGKILL
was needed anywhere. Verified after shutdown: zero worker/supervisor/
classify-child processes remained, no file was mid-write, no torn final
JSONL record, and the completed-world inventory reconciled exactly against
the step-2 checkpoint.

**Unplanned incident.** Within 5 seconds of this clean shutdown, a
*different* Claude Code session (same user, same repository) -- which held
a standing "recover E2 if all shards stop" instruction from earlier in the
project's history -- treated the shutdown as an accidental total
process-group loss and auto-restarted the old run's supervisors. This was
a genuine cross-session coordination gap, not a defect in this migration's
own shutdown procedure: the shutdown itself had already been verified
clean and complete before the other session intervened. This migration's
own `chmod 444` immutability protection (already applied to all 45 result
files before the restart) prevented any data corruption during the
several minutes this was unresolved -- the restarted processes hit
`Permission denied` on every write attempt, confirmed via their own log
output.

Presented to the user via `AskUserQuestion`; the user selected "stand down
the other session first, then retry," and after confirming the other
session was stood down, explicitly said to proceed. This migration then:
re-verified process state (found 8 orphaned worker/classify-child
processes with PPID=1, i.e. no supervisor left to restart them),
re-verified data integrity (every scientific-data-file hash still
byte-identical to the pre-incident checkpoint -- only error/log files had
changed, confirming zero corruption throughout), sent SIGTERM to the 8
orphans (7 exited directly, 1 had already self-terminated), inspected one
additional read-only watcher script found running
(`watch_for_genuine_completion.sh`, self-documented and code-verified as
"Never restarts, never recovers, never touches results") and left it
running as harmless, and took a new, authoritative final checkpoint.

## Step 5: Old run directory preserved as immutable provenance

The old run's 5 healthy output directories remain exactly where they were,
`chmod 444` on every result file, **not** repurposed as Rescue-v2 output.
Three additional pre-existing directories under the same
`results/e2/` tree were inspected and confirmed to hold no
`worlds_shard_*.jsonl`/`candidates_shard_*.jsonl` data usable by this
migration: `run_poison_world` and `run_stuck_worlds` (diagnostic logs
only, described in step 14 below), and
`run_PRERESCUE_INVALIDATED_2026-08-16` (explicitly invalidated by its own
name before this migration began, excluded on that basis).

**Final, authoritative checkpoint** (taken after the incident above was
fully resolved), at
`/tmp/e2_rescue_v2_checkpoint_TRULY_FINAL_20260817_165554/`:
- `n_unique_world_ids`: **409/540**
- `n_files_hashed`: 48 (45 original + 3 that only gained content during the
  incident's error/log churn -- no scientific data file among them)
- All world_ids confirmed byte-identical to the pre-incident checkpoint;
  only error/log file hashes changed.

## Steps 6-8: Balanced sample, overlap, import

The already-frozen balanced estimation manifest was reused verbatim, not
re-selected: `r=6/n=270` per-cell RNG order, seeded
`sha256(SEED_TAG+cell_id)`, file
`/tmp/e2_rescue_v2_out/FROZEN_BALANCED_MANIFEST_n270.json`. (Its embedded
`manifest_sha256` field -- `028b17c5...` -- is a content hash computed
over the manifest's canonical payload at freeze time, before that field
was inserted, so it legitimately differs from a whole-file hash taken now;
the file itself has only ever been read, never written, by this
migration.)

Overlap against the 409/540 final checkpoint:
- **N_COMPLETED_TOTAL: 409**
- **N_ESTIMATION_SAMPLE_ALREADY_COMPLETE: 202**
- **N_ESTIMATION_SAMPLE_REMAINING: 68**

Every world in the checkpoint was imported by reference (no data copy):
Rescue-v2's world runner treats each old healthy directory as a
`--prior-result-dir` and skips any `world_id` already present there,
exactly as the old run's own `_already_done` logic already worked. Zero
worlds were recomputed.

## Step 9: Persistent cache seeded from old-run classifications

`classifier_version` for this worktree: `90a3b5ea3a83b0e9587e3b1e4e54e18`
`8afb8e893fabc9293d9177bc767089e7a` (source-hash of the 7 files
`classify_cache.compute_classifier_version` covers). `seed_cache_from_old_run.py`
imported every valid `classify_expression` output from the old run's
candidate rows (excluding `ROW_ERROR:`-prefixed rows, which came from the
old run's outer exception handler, not from `classify_expression` itself):

- n_candidate_rows_seen: 143,232
- n_skipped_row_error: 0
- n_skipped_dup_conflict: 0 (no case where the same expression string
  classified two different ways was found -- consistent with
  `classify_expression`'s proven purity)
- n_cache_put_calls: 143,232
- n_distinct_expressions_cached (seed step): 119,448

## Step 10: Rescue-v2 lazy workers started

**Bug found and fixed live, during this step's own smoke test** (see
`e2_run_shard_lazy.py`'s `_cached_classify_expression` docstring): the
cache-miss fallback called the *module attribute*
`e2_classify.classify_expression`, which is itself monkey-patched to that
same wrapper for the duration of `_run_one_world`'s `with` block --
recursing forever on any genuine cache miss (`RecursionError`, reproduced
on 2/2 tested new worlds). This is the exact same defect class this
rescue already found once, live, in `speed_benchmark.py`'s cache arm
(documented in the hostile review as F2); same root cause, same fix:
capture the real function once, at import time, before any patching.
Fixed and re-verified: both previously-failed smoke worlds
(`mass_affine_descriptor|low|noiseless|r011`, stage C, 30 classify calls,
65.8s; `mass_saturating_descriptor|high|noiseless|r011`, stage B, 326
classify calls, 69.8s) now complete cleanly with well-formed,
schema-correct output and zero errors.

Host capacity at launch: 8 cores, load average 2.67/3.15/5.56 (1/5/15-min)
immediately before launch, with zero old-E2 or prior rescue processes
running. `build_case_regressor` uses `parallelism="serial"` (frozen,
required by `deterministic=True`), so each world's PySR fit is
single-threaded; `cap_threads()` pins BLAS/OMP threads to 1. **4 concurrent
shards** were launched (not the old run's 5-6, which the hostile review
already implicated in the oversubscription episode reaching load average
63) -- each shard observed at ~85-120% CPU, aggregate load average settled
at 5-10 (1-min) with 4/8 cores nominally busy, comfortably inside the
"do not materially consume shared host resources" constraint, and leaving
headroom the old run's higher shard count did not.

Launched: PIDs 77974-77977, `out-dir=/tmp/e2_rescue_v2_production_out`,
`cache-db=/tmp/e2_rescue_v2_cache/classify_cache.sqlite3`,
`prior-result-dir` = the 5 old healthy directories +
`/tmp/e2_rescue_v2_smoke_output` (so the 2 smoke-verified worlds above are
reused, not recomputed).

## Step 11: Prioritization

`WORLD_PRIORITY_ORDER_PRODUCTION.json` (539 worlds -- the original frozen
540-world priority order with the poison world, see step 14, removed) is
sample-remaining-first (the 68 `N_ESTIMATION_SAMPLE_REMAINING` worlds),
then the rest of the original 540-world manifest, both in the
already-frozen `world_ordinal` order within each section. No
outcome-adaptive reordering: the second priority tier ("worlds needed to
resolve the routing gate") collapses to this same deterministic remainder
order, since which specific worlds resolve the gate cannot be known
without classifying them, per the routing-lock theory
(`MURU_V2_E2_ROUTING_LOCK_THEORY.md`).

## Step 12: Route-lock monitor started

`routing_lock_monitor.py` polls the combined old+new result population
every 5 minutes (`/tmp/e2_rescue_v2_routing_monitor_loop.sh`, PID 78088,
log at `/tmp/e2_rescue_v2_routing_monitor.log`). It prints only
`ROUTING_LOCK_STATE`, `N_CLASSIFIED`, and `R_REMAINING` -- never A/B/C/D
counts. First reading, immediately after launch:

```
ROUTING_LOCK_STATE: FULL_RUN_REQUIRED
N_CLASSIFIED: 411/540
R_REMAINING: 129
```

(411 = 409 checkpoint + 2 smoke-verified worlds; consistent with the
shards' own reported "already done" totals, 121+86+120+84 = 411, against
539 assigned.)

## Step 13: Exoneration threshold preserved as unresolved

`routing_lock.py`'s `evaluate_gate2`/`evaluate_gate2_opaque` cannot report
the exoneration-branch outcome (`WITHDRAWN`) without an explicit
`ExonerationRatification` object, and nothing anywhere in this codebase
constructs one -- the gap is preserved structurally, not by convention.
Any route this ambiguity would otherwise gate reports `FULL_RUN_REQUIRED`.
No number was invented at this step.

## Step 14: Poison-world handling

`V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000` (world_ordinal 0)
has an existing, dedicated diagnosis
(`results/e2/run_poison_world/PENDING_EXECUTION_DIAGNOSIS.md`, on the old,
now-preserved worktree): 80 attempts across the old run's shard 0 and an
isolated one-world supervisor, 100% SIGKILL (exit 137) at a strikingly
consistent ~6-7.5 minutes each, with system load at 111 and 100% CPU at
the time retries were stopped -- consistent with an OOM-class condition
specific to this one world, not a general slowness. That diagnosis's own
stated resolution path requires re-attempting it "alone, in a clean
one-worker environment with minimal competing load."

This migration honors that precondition rather than overriding it: the
poison world was **excluded from `WORLD_PRIORITY_ORDER_PRODUCTION.json`**
(540 -> 539 entries) so it cannot serialize-block the other 4 shards, and
was **not** attempted concurrently with the main production launch, since
running it alongside 4 other active shards would recreate exactly the
contended conditions the diagnosis blames for its 80/80 failure rate. It
remains quarantined, tracked as "539 ordinary + 1 pending" (mirroring the
old diagnosis's own "539 ordinary + 1 pending" framing), to be
re-attempted in isolation once the main queue reaches a genuinely
uncontended window -- a decision left open, not resolved here, per the
same document's own explicit resolution criteria.

## Step 15: Post-launch health verification

| Check | Result |
|---|---|
| Imported-world accounting exact | 539 assigned across 4 shards (134+135+135+135); 411 already-done, matching the route monitor's N_CLASSIFIED exactly |
| Balanced sample manifest unchanged | Read-only throughout this migration; never opened for write |
| Lazy worker processes healthy | 4/4 PIDs alive, 0 errors, first world each completed cleanly (wall 104-109s) |
| Cache version/hash correct | Fresh `compute_classifier_version()` == cache's stored `classifier_version`, 0 stale rows, row count grew 119,448 -> 119,959 as new worlds classified |
| Route monitor healthy | Running, first opaque reading captured (above) |
| No old E2 process remains | Confirmed by process-table scan (`e2_run_shard.py`/`e2_shard_supervisor`/`e2_staleness_watchdog` all absent) both post-shutdown and again post-launch |
| No scientific definition changed | 0 files touched under `e2_classify.py`, `e2_scoring.py`, `e2_search.py`, `e2_aggregate.py`, `e2_worlds.py`, or `paper_benchmark`/`discovery`; `raw_search.py` is a byte-identical-verified transcription (`tests/test_raw_search_identity.py`) |
| No partial scientific aggregate exposed | This document and its companion JSON contain zero A/B/C/D/E frequencies, rates, or per-cell breakdowns; the one place stage labels appear is 4 individual, engineering-verification log lines (smoke test + step-15 spot check), never aggregated |

## Step 16: This document and its companion

This file and `MURU_V2_E2_RESCUE_V2_MIGRATION_PROVENANCE.json` (recording
both the old checkpoint and the new run's authority) are the required
step-16 deliverables.

## Rollback

Fully available at all times: the old run's 5 output directories are
untouched, `chmod 444`, at their original paths, with a byte-verified
final checkpoint. Reverting means simply stopping the Rescue-v2 shards
(SIGTERM) and resuming old-architecture execution against the same
checkpoint -- no data was moved, deleted, or overwritten to enable this
migration.
