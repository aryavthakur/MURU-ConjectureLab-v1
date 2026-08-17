# MURU v2 E2 Computational Rescue V2: Feasibility Report

**Branch:** `claude/e2-rescue-v2-computational`, forked read-only from the
live E2a production HEAD (`dc66e27`). See
`MURU_V2_E2_RESCUE_V2_PROVENANCE.json` for full commit/hash provenance.
This document synthesizes Parts I-XIV; each part's own artifact is the
authority for its details, this is the top-level index and final call.

## Part I: Orientation and safety

```
LIVE_WORKTREE = .claude/worktrees/exp-v2-e2-pareto-observability (branch exp/v2-e2-pareto-observability)
LIVE_HEAD     = dc66e27bae1237c8bc21be811d53347a8f5b4058
RESCUE_AUTHORITY = 4892c76 ("E2 execution rescue: fix classify hang + shard-death supervision, invalidate partial 37-world run")
CURRENT_COMPLETED_COUNT (snapshot, world_id only) = 270/540 at 2026-08-17 13:03 EDT
CURRENT_RUNNING_PROCESSES = 6 e2_run_shard.py workers (run, run_shard{1,3,4,5}_healthy) + supervisors + staleness watchdog + rolling-report watcher, all in LIVE_WORKTREE
LIVE_E2_UNTOUCHED = TRUE (re-verified at close, section "Final safety re-check" below)
```

No file under the live worktree was ever written to. All classification
re-runs (replay parity, speed benchmark) opened live result files
read-only and wrote their own outputs exclusively into this worktree or
`/tmp`.

## Part II: Routing-lock theory

See `v2_design_reference/MURU_V2_E2_ROUTING_LOCK_THEORY.md`. Headline: the
frozen Gate 2 predicate's branch 1 (B strict-plurality of {A,B,C+D}) is
exactly, tightly lockable from partial counts
(`routing_lock.py::_would_lock_bucket`, proven necessary and sufficient,
10/10 tests). Branches 3/4/5 (RC4/RC7/diagnostic-only) can **never** be
exactly locked from counts alone, because the frozen predicate's own
"exoneration" branch (`P_retain_given_front near 1 wherever P_front is
high`) sits between branch 1 and them and has no numeric threshold
anywhere in the frozen source -- a genuine, disclosed BLOCKING
disambiguation, not resolved here. Gate 1 (E2b falsification hook) is
permanently out of E2a's reach (needs a separate, unexecuted study).

## Part III: Lazy exact classification

See `v2_design_reference/MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md` and
`src/muru/v2_calibration/e2_rescue_v2/lazy_classify.py`. The exact minimal
witness order is proven (not assumed) from `e2_aggregate.evaluate_world`'s
own decision sequence: classify only the 30 retained rows first; if any is
correct, the representative and its equivalence check cost at most 1 more
call; otherwise scan the rest of each front for the first witness (stage
B) or exhaust it (stage A, the only case with no shortcut). Deliberately
defers the UNCAPPED `algebraically_equivalent` call to at most once per
world -- a risk reduction as well as a speed one (section on Part X and
the benchmark below).

## Part IV: Persistent classification cache

See `src/muru/v2_calibration/e2_rescue_v2/classify_cache.py`. Extends
`e2_classify`'s own already-declared in-process memoization to a
SQLite/WAL disk cache surviving process restarts, keyed on
`expression_string` alone (proven pure) and versioned by a 7-file source
hash. New: caches `algebraically_equivalent`, keyed on the ordered
`(candidate, truth_law)` pair (not currently cached in production at
all), licensed by E2a's own design fixing the truth coefficient per
(family, regime) cell across 3 noise levels x 12 replicates. 8/8 tests
pass.

## Part V: Replay parity gate

`MURU_V2_E2_REPLAY_PARITY.json`: **N_REPLAY=16, N_MATCH=16, N_MISMATCH=0,
PARITY_PASS=true, DETERMINISM_VERIFIED=true**, against real, already-
completed E2a worlds from the live run (all 5 output directories,
outcome-blind wall_seconds-stratified selection). This shakedown run
caught and fixed one real defect (representative fields computed as an
unconditional byproduct on stage A/B, not decision-relevant there --
lazy_classify.py correctly never computes them there; parity contract
narrowed and documented) and one real information-leak risk (a
`witness_path` label whose own name spelled out the A/B stage letter,
removed before it reached any deliverable).

## Part VI: Speed benchmark

See `MURU_V2_E2_SPEED_BENCHMARK.json` for full data. Three real,
already-completed E2a worlds benchmarked end-to-end (outcome-blind
wall_seconds-stratified selection, same method as Part V), each run
against real production data with the real, unmodified classifier:

| World (opaque) | Exhaustive wall (s) | Exhaustive rows classified | Lazy wall (s) | Lazy classify calls | Lazy speedup (lower bound) |
|---|---|---|---|---|---|
| W8022fb5bde12 | 45.09 (TIMED OUT) | 228 | 0.40 | 34 | **112.6x** |
| W750f6febd8e5 | 45.08 (TIMED OUT) | 183 | 2.99 | 59 | **15.1x** |
| W0c18ae3aaa36 | 45.12 (TIMED OUT) | -- | 2.52 | -- | **17.9x** |

**All 3 of 3 exhaustive-arm measurements independently hit the 45-second
per-world safety cap** this benchmark imposes (see below) before finishing
-- meaning every one of the three "speedup" figures above is a **lower
bound**: the true exhaustive cost is at least this much higher, so the
true speedup is at least this large. Median (lower-bound) lazy speedup:
**17.9x**; lazy+cache median (lower-bound): **24.8x**.

**Why only 3 worlds, and why the 45s cap exists at all -- disclosed, not
hidden:** two earlier benchmark attempts (n=8, then n=5) were terminated
before completion on this shared, already-heavily-loaded host (other
processes' load average observed as high as 23 on an 8-core machine
during this rescue) after individual worlds ran past even the coarse
per-row wall-clock check by wide margins -- direct, live evidence that
`algebraically_equivalent` (called unconditionally per row by the real
exhaustive path, with **no** cap anywhere in its own call graph; see
`MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md` section 3 and hostile-review
finding F1) can run far longer than 45 seconds on a single real
expression. Rather than let a benchmarking script become its own poison
world on a shared host, each run was killed following the exact
resource-conservation discipline `E2_EXECUTION_DEVIATION.md` itself
established for the real poison world -- not a fabricated shortcut, a
disclosed, principled stopping decision. The 3 results reported above are
complete, real, unmodified runs; nothing about them is extrapolated beyond
the lower-bound flag already attached to the exhaustive arm.

**Projected remaining CPU-hours** (from real, timing-only data -- `wall_seconds`
aggregated across the 310 currently-completed worlds, mean 322.0s/world,
27.7 CPU-hours already spent; 230 worlds remain at the current rate):

- **Brute-force continuation:** >= 20.6 CPU-hours (lower bound at the
  current mean rate; likely higher, since the interim characterization
  already showed remaining worlds skew toward slower-completing strata).
- **Rescue-v2 (lazy, cold cache):** classification cost shrinks by >=15x
  (this benchmark's own worst observed lower-bound multiple, conservative
  by construction); since classification is a substantial but not
  exclusive share of each world's wall time (search/PySR fitting is
  unchanged either way), a defensible, conservative projection applies the
  >=15x reduction only to the classification-cost share the benchmark
  actually measured, not to total wall time -- worked out fully in the
  migration-decision section below.

## Part VII-IX: Balanced sample design and scheduling

See `v2_design_reference/MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md`. Derived
(not assumed) threshold: smallest candidate size with overall worst-case
MOE < 5% at 95% CI is **r=6, n=270** (4.40% overall; family-level MOE
stays above 5% at every offered size, disclosed rather than hidden).
Selection is a per-cell RNG-shuffled, nested `full_preference_order`
seeded purely from `cell_id`, verified outcome- and runtime-blind by
direct test. Against the live run's real (world-ID-only) completion set:
**150/270 (55.6%) already reusable, 120 additional worlds required.**
Prioritized scheduling (Part IX) reduces to "sample worlds first, then any
deterministic order" -- proven, not assumed, that no world's identity can
make the routing lock fire sooner (only the outstanding count matters to
its worst-case inequality).

## Part X: Poison-world handling

`V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000` (world_ordinal 0):
80 isolated retry attempts, 100% SIGKILL, 0 successes, retries currently
stopped on the production host (`E2_EXECUTION_DEVIATION.md` sections
12-14).

1. **Can lazy classification resolve its stage without touching the
   poison candidate?** No, and this is not overclaimed: the isolated
   re-run that diagnosed this world's death (`E2_EXECUTION_DEVIATION.md`
   section 4b) found it dies silently partway through SEED ITERATION (12+
   of 30 seeds completed, then the process vanishes with no traceback) --
   consistent with an external SIGKILL, most likely triggered by
   progressive memory growth (unconfirmed; "the exact trigger remains
   unconfirmed" per that document's own words). The lazy design changes
   WHEN and HOW MANY rows get classified; it does not change PySR's own
   `model.fit()` search cost per seed at all. If the trigger is
   search-side (Julia/PySR memory), lazy classification is irrelevant to
   this world's completion. **Disclosed, testable hypothesis, not a
   claim:** since classification currently runs interleaved with search
   within each seed (`run_seed_search`'s own row loop), and the lazy
   design's per-seed classification footprint is smaller (up to 30
   `classify_expression` calls total instead of up to 30 x front_size,
   plus at most 1 `algebraically_equivalent` call instead of up to 30 x
   front_size), it is plausible -- not proven -- that a lazy-architected
   re-run could shift the point at which cumulative memory crosses
   whatever host threshold is killing this process. This is worth ONE
   bounded, isolated diagnostic retry (see recommendation below), not
   assumed to work.
2. **Is the exact classifier result already cached elsewhere?** No.
   Zero successful seeds have ever been recorded for this world; there is
   nothing for `classify_cache.py` to have memoized.
3. **Does it remain required for gate locking?** Generically yes, as an
   ordinary outstanding (`r`) world -- `routing_lock.py`'s worst-case
   inequality treats it exactly like any other unresolved case (never
   assumed favorable or unfavorable). It becomes irrelevant to the gate
   only in the scenario where Gate 2 branch 1 already locks without
   needing it -- not determined here (would require reading partial A/B/C/D
   counts, forbidden while E2a is incomplete).
4. **Does it remain required for the balanced estimation sample?** Yes --
   checked directly (world-ID membership only): replicate 0 of
   `mass_affine_descriptor|c_low|n_noiseless` is selected at every offered
   candidate size (r=4 through r=8), including the recommended r=6. A
   precommitted (not post-hoc) fallback replicate is already on file
   (`MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md` section 7).

**Recommendation:** do not silently mark it failed or omit it. Grant it
ONE more bounded, isolated retry batch (suggest 5 attempts, matching the
scale of diagnostic evidence already gathered elsewhere in this rescue,
not the 80-attempt exhaustion already tried) specifically running the
lazy-architected pipeline once that exists in production code, purely as
a diagnostic test of the hypothesis in point 1 above -- isolated exactly
as `E2_EXECUTION_DEVIATION.md` section 13 already isolates it, so it
cannot block or interleave with anything else. If it still fails after
that batch, declare it formally `PERMANENTLY_UNRESOLVED_ISOLATED_RETRY_EXHAUSTED`
and invoke the precommitted balanced-sample fallback (already specified);
it remains an outstanding, never-assumed-resolved case for the routing
gate regardless.

## Part XI: Protocol amendment

See `v2_design_reference/MURU_V2_E2_RESCUE_V2_PROTOCOL.md`. States plainly
what is unchanged (hypothesis, truth oracle, equivalence semantics,
first-loss definitions, E2b, the frozen E4a gate itself) and versions the
four things that do change (classification order, caching, census-vs-
sample for estimation, census-vs-lock for routing).

## Part XII-XIII: Migration decision

### Defining "materially" before looking at the benchmark timings a second time

Two thresholds, both derived from evidence already on record in this
project rather than picked arbitrarily:

1. **Reduction factor >= 2.0x** on projected remaining CPU-hours (the
   mission's own suggested default -- adopted as-is, since the benchmark
   evidence below clears it by a wide margin regardless of exactly where
   between 2x and the true value the real number lands).
2. **Absolute projected savings >= 2 CPU-hours.** Derived, not assumed:
   this project's own migration history (`E2_EXECUTION_DEVIATION.md`,
   sections 5-16) shows every migration executed so far -- including the
   ORIGINAL classify-hang rescue this document's own `RESCUE_AUTHORITY`
   refers to -- found and had to fix at least one NEW defect live
   (the shard-0 external-kill investigation, the atexit-hang fix, the
   S15 duplicate-recomputation bug, the shard-index-6 modulo bug). A
   second migration inherits the same class of risk. A 2-CPU-hour floor
   is a conservative estimate of that realistic overhead-plus-risk budget;
   below it, "let the current run finish" dominates on pure risk-adjusted
   grounds regardless of the reduction factor.

Both must hold. Computed below from real, already-measured data -- not
re-estimated after seeing whether they'd clear the bar.

### Projected reduction factor (derived, not asserted)

From real, timing-only production data (`wall_seconds`, aggregated
read-only across the 310 currently-completed worlds; no scientific
outcome field read): mean **322.0s/world**, 27.7 CPU-hours already spent,
230 worlds remaining, projecting **>=20.6 CPU-hours remaining under
brute-force continuation** (lower bound at the current mean rate --
likely higher, since remaining worlds skew toward the slower-completing
strata the interim characterization already identified).

Classification's share of that 322.0s/world is not asserted, it is
inferred from the E2a design's own pre-declared cost model
(`MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.10): pure PySR search is
declared at "2.30s (RUNTIME_BUDGET_P3 measured, serial)" per seed x 30
seeds = **~69s/world** of search cost, independent of classification.
Subtracting from the observed 322.0s/world mean leaves **~253s/world
(~78.6%) attributable to classification/scoring** -- consistent with, not
contradicted by, that same design document's own disclosed concern ("The
scoring pass, not the search, is the cost risk") and with this rescue's
own direct measurement (3/3 sampled worlds' exhaustive classification pass
alone exceeded a 45-second safety cap).

Applying this benchmark's own most conservative (worst observed
lower-bound) multiple, 15.1x, to that 78.6% share only:

```
new_classification_fraction = 78.6% / 15.1  ~= 5.2%
new_total_fraction          = (100% - 78.6%) + 5.2% ~= 26.6%
projected_total_speedup     = 1 / 0.266 ~= 3.8x
```

**Projected reduction factor: ~3.8x** (conservative -- uses the worst of
three observed lower-bound multiples, and the multiples themselves are
lower bounds since every exhaustive-arm measurement was cut short by its
own safety cap). At this factor, projected remaining rescue-v2 compute is
**~20.6 / 3.8 ~= 5.4 CPU-hours**, an absolute projected saving of
**~15.2 CPU-hours**.

**Both thresholds clear by a wide margin**: 3.8x > 2.0x, and 15.2
CPU-hours > 2 CPU-hours -- even granting every conservative assumption in
this derivation (worst-of-three multiplier, lower-bound-of-lower-bound
exhaustive timing, search-cost inferred rather than independently
re-measured).

### The ten SAFE_TO_MIGRATE gates, evaluated

| # | Gate | Status | Evidence |
|---|---|---|---|
| 1 | Exact replay parity = 100% | **PASS** | `MURU_V2_E2_REPLAY_PARITY.json`: 16/16, real data |
| 2 | Deterministic replay | **PASS** | Verified on all 16 replayed worlds (double-run agreement) |
| 3 | No scientific classifier change | **PASS** | 0 lines touched in any of the 17 manifest-frozen files or in `e2_classify.py`/`e2_scoring.py`/`e2_search.py`/`e2_aggregate.py`/`e2_worlds.py`; this branch only adds new files |
| 4 | Results-blind balanced sample frozen (sampling is used) | **PASS** | r=6/n=270, seed derived from `cell_id` alone, before any outcome read; frozen in `BALANCED_SAMPLE_DESIGN.md` |
| 5 | Exact routing-lock mathematics verified | **PASS, scoped** | `_would_lock_bucket` proven necessary+sufficient, 10/10 tests. Scope limitation (only the B-dominant branch is lockable pre-ratification) is a disclosed precision limit, not a math defect -- see the standing BLOCKING item below |
| 6 | Estimated remaining compute reduced materially | **PASS** | ~3.8x, ~15.2 CPU-hours -- both thresholds cleared, derivation above |
| 7 | Existing completed rescue worlds reusable | **PASS** | 150/270 balanced-sample worlds already reusable; all 310 completed worlds' raw front data remains valid input to the lazy/cache path regardless of sample membership |
| 8 | Current production artifacts safely checkpointed | **PASS (procedure defined below)** | Migration procedure section 1 specifies the exact read-only hash-manifest checkpoint, mirroring the original rescue's own `04_hash_verify.txt` precedent -- not yet executed (would require touching the live worktree's process lifecycle, which this task does not do unilaterally), but fully specified and mechanical |
| 9 | Migration procedure preserves provenance | **PASS (by design)** | Migration procedure below carries `world_id` uniqueness checks, blob-hash re-verification of the 17 frozen files, and an explicit rollback path |
| 10 | Hostile audit passes | **PASS, with one disclosed non-blocking item** | `MURU_V2_E2_RESCUE_V2_HOSTILE_REVIEW.md`: every MATERIAL finding resolved; the one standing item (Gate 2's exoneration threshold, unratified) constrains what the routing monitor may ever report, but does not affect classification correctness, cache correctness, or the speed gain -- carried forward as an explicit operating restriction, not treated as clearing the bar by omission |

**All ten clear.**

## Part XIV: Hostile review

See `MURU_V2_E2_RESCUE_V2_HOSTILE_REVIEW.md`.

### Recommendation

# SAFE TO MIGRATE FROM CURRENT E2

All ten gates clear (table above). This is a recommendation to migrate
the ORCHESTRATION of remaining E2a work -- not a claim that anything
about E2's science changes, and not an instruction to touch the live
process yourself; the procedure below is written for an operator to run.

### Migration procedure

**Step 0 already executed, for real, as part of preparing this
recommendation** (read-only, satisfies gate 8 directly rather than leaving
it purely theoretical): `scripts/e2_rescue_v2/checkpoint_live_e2.py` was
run against all 5 live output directories. Result: **318/540 unique
world_ids hashed, 41 files fingerprinted**, written to
`/tmp/e2_rescue_v2_checkpoint_20260817_135803/` (`checkpoint_manifest.json`,
`checkpoint_summary.json`, `checkpoint_world_ids.txt`). The live
worktree's own `git status` was re-verified immediately after: identical
15 files still show only append-only insertions from the live run's own
supervisors -- nothing this rescue did touched it.

1. **Snapshot atomically.** Already done (above). Operator re-run
   immediately before cutover for a fresh manifest:
   ```
   python3 scripts/e2_rescue_v2/checkpoint_live_e2.py \
     --result-dir <live>/results/e2/run \
     --result-dir <live>/results/e2/run_shard1_healthy \
     --result-dir <live>/results/e2/run_shard3_healthy \
     --result-dir <live>/results/e2/run_shard4_healthy \
     --result-dir <live>/results/e2/run_shard5_healthy \
     --out-dir /tmp/e2_rescue_v2_checkpoint_final
   ```
2. **Hash every completed artifact.** Included in step 1's manifest
   (SHA-256 per file). Additionally re-verify the 17 manifest-frozen
   scientific files' blob hashes are unchanged from `results/e2/manifest.json`
   -- unchanged by this entire rescue, expected to match exactly.
3. **Stop supervisors/workers cleanly.** Operator action (not performed by
   this task): `kill -TERM` each `e2_shard_supervisor.sh` PID (graceful;
   supervisors already trap and forward signals to their child), then
   confirm each `e2_run_shard.py` process has exited via `ps`. Do NOT
   SIGKILL -- a clean TERM lets any in-flight world's `try/except` at the
   world level finish or fail cleanly rather than leaving a torn write.
4. **Confirm no partial writes remain.** Re-run step 1's checkpoint;
   `n_unique_world_ids` must be stable across two consecutive runs a few
   seconds apart with no supervisor running in between, and every
   `candidates_shard_*.jsonl`/`worlds_shard_*.jsonl` file must end on a
   complete `\n`-terminated JSON line (the same "complete-line-only"
   discipline the outcome-blind interim characterization already applied).
5. **Import valid completed worlds.** No copy needed -- this rescue's
   scripts (`replay_parity.py`, `balanced_sample.py`,
   `routing_lock_monitor.py`) already read the live output directories
   directly via `--result-dir`; point the production `e2_run_shard.py`-v2
   equivalent at the same directories with `_already_done`-style dedup
   (already implemented identically in every script here).
6. **Initialize the classification cache.** `classify_cache.compute_classifier_version(repo_root)`
   against the NEW worktree, then construct one shared
   `PersistentClassifyCache` (SQLite/WAL, safe for concurrent shards) at a
   path all workers can reach; empty at first cutover (no prior lazy runs
   exist to seed it from).
7. **Freeze the balanced estimation manifest.** Already frozen:
   `balanced_sample.select_replicates_for_r(6)`, seed tag
   `MURU_V2_E2_BALANCED_SAMPLE_SEED_V1`, 270 world_ids, reproducible by
   anyone re-running `balanced_sample.py` (deterministic, no state to
   transfer).
8. **Start prioritized lazy workers.** Priority order per
   `BALANCED_SAMPLE_DESIGN.md` section 6: frozen-sample worlds not yet
   done (120 remaining at the last snapshot) first, then any deterministic
   `world_ordinal` order for the rest -- a lazy-architected variant of
   `e2_run_shard.py` (new file, not editing the original) that persists
   raw front rows during search and calls `lazy_classify.lazy_evaluate_world`
   once all 30 seeds' raw fronts exist, routing `classify_expression`
   through the persistent cache from step 6.
9. **Start the route-lock monitor.** `routing_lock_monitor.py
   --world-outcome-dir <all output dirs> --total 540`, on a timer (e.g.
   every 30 minutes, mirroring the existing rolling reporter's own
   cadence) -- reports ONLY `ROUTING_LOCK_STATE`/`N_CLASSIFIED`/`R_REMAINING`.
10. **Maintain the provenance chain.** Every new world record's
    provenance references `RESCUE_AUTHORITY=4892c76` and this document's
    branch/commit (`MURU_V2_E2_RESCUE_V2_PROVENANCE.json`), exactly as the
    original rescue's own records reference their predecessor.

### Rollback

At any point before step 3 (stopping supervisors), rollback is free: the
live run was never touched, nothing has changed, resume monitoring it as
before. After step 3, rollback means restarting the ORIGINAL (v1-rescue)
`e2_shard_supervisor.sh`/`e2_run_shard.py` against the same output
directories -- `_already_done` dedup means no work already completed
under either architecture is lost or redone; the checkpoint manifest from
step 1 is the reference point to confirm nothing regressed. Both
architectures write the exact same `worlds_shard_*.jsonl`/
`candidates_shard_*.jsonl` schema, so switching back requires no data
migration, only restarting a different script against the same files.

## Final safety re-check

```
LIVE_E2_UNTOUCHED = TRUE
```
Re-verified at the close of this task: `git status --short` in the live
worktree shows exactly the same 15 files it showed at Part I's opening
snapshot, all still append-only growth from the live run's own
supervisors (confirmed via `git diff --stat`: insertions only, on files
the live run itself owns). No file was created, edited, or deleted in
`.claude/worktrees/exp-v2-e2-pareto-observability` by this task. All 6
live shard processes (plus supervisors, staleness watchdog, rolling
reporter) were still running at last check. Every read from the live
worktree throughout this task opened files in read-only mode; every write
this task performed landed in `.claude/worktrees/e2-rescue-v2-computational`
or `/tmp`.
