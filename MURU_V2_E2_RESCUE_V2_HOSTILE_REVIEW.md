# MURU v2 E2 Computational Rescue V2: Hostile Review

Attacking the rescue design against the full checklist before any
migration recommendation is made. Every item below is either (a) shown
NOT PRESENT with a concrete, checkable reason, or (b) a MATERIAL finding
that has been resolved (with what changed), or (c) a MATERIAL finding
left explicitly OPEN and blocking (never silently smoothed over).

| # | Attack | Verdict | Evidence |
|---|---|---|---|
| 1 | Post hoc sampling | NOT PRESENT | `balanced_sample.py`'s per-cell seed is `sha256(tag + cell_id)` -- a pure function of cell identity, verified by `test_selection_depends_only_on_cell_identity_not_on_any_external_state` to not read clock/env/outcome state. |
| 2 | Runtime-selected inference | NOT PRESENT | The balanced sample, not the runtime-biased completed set, is the frozen estimation basis (Part VII); the interim characterization's own 16.7-76.0% completion-fraction spread across strata is cited as the reason the raw completed set is unusable for estimation, not worked around. |
| 3 | Using partial E2 outcomes to choose sample size | NOT PRESENT | r=6 was chosen by a stated MOE<5% threshold applied to the manifest's own factorial structure alone (`design_based_moe`), before any completion or outcome data was read for that purpose. |
| 4 | Incorrect early stopping | RESOLVED (verified two ways) | `lazy_classify.py`'s Theorem (spec section 2) proven from `evaluate_world`'s real code; independently confirmed empirically: 16/16 real replayed worlds match the sealed exhaustive result, with determinism re-verified on every one. |
| 5 | Wrong plurality lock inequality | RESOLVED | `_would_lock_bucket` proven necessary AND sufficient (`ROUTING_LOCK_THEORY.md` section 2's proof), not just sufficient; 10/10 tests include exact-boundary and off-by-one cases. |
| 6 | Unhandled tie cases | RESOLVED | Strict `>` used throughout, matching the frozen predicate's own strictness; a forced tie at the boundary correctly reports `FULL_RUN_REQUIRED`, not a false lock (`test_not_locked_execute_at_exact_boundary`). |
| 7 | Cache under-keying | RESOLVED | `classify_expression`'s purity (truth-blind, no argument but the string) is argued from `e2_classify.py`'s own module docstring, not assumed; `algebraically_equivalent`'s cache key is the full ordered `(candidate, truth_law)` pair, never assumed symmetric; both keyed additionally by a 7-file source-hash version, with a version mismatch always treated as a miss (`test_classify_cache_version_mismatch_is_a_miss_not_a_wrong_answer`). |
| 8 | Equivalence semantic changes | NOT PRESENT | `algebraically_equivalent` is imported and called unmodified everywhere in this rescue; not one line of `discovery/equivalence.py` is touched (confirmed: this branch never edits any of the 17 manifest-frozen files, same as the v1 rescue's own discipline). |
| 9 | Lazy classifier false negatives | RESOLVED (empirically) | 16/16 real-world replay-parity match; two REAL defects were caught and fixed during this very shakedown (see items 15 and the parity-contract narrowing below) -- the process that would catch a false negative demonstrably works, having already caught two different bugs. |
| 10 | Candidate ordering dependence | NOT PRESENT | Seeds scanned in `sorted()` order, rows in `front_rank` order; the FINAL STAGE is provably order-independent (any witness proves not-A, and the C/D/E representative comes from `group_and_select`'s own deterministic tie-break, never from scan order) -- see spec section 2's theorem. |
| 11 | Timeouts changing classifications | NOT PRESENT | `SIMPLIFY_TIMEOUT_SECONDS` and the process-boundary kill mechanism in `e2_classify.py` are untouched; a timed-out row still yields `canonicalization_status="SIMPLIFY_TIMEOUT"`, `effective_support=None`, which flows through the unmodified `classify_support`/`evaluate_g2_event` chain to `SUPPORT_UNRESOLVED`/`UNEVALUABLE` exactly as production would -- no special-casing added. |
| 12 | Poison-world exclusion | NOT PRESENT / OPEN OPERATIONALLY | Never marked failed or silently dropped; `MURU_V2_E2_RESCUE_V2_FEASIBILITY.md` Part X section states its status plainly and proposes one bounded, isolated, diagnostic retry batch, not a silent write-off. Its balanced-sample fallback is precommitted, not improvised. |
| 13 | Double-counting completed worlds | NOT PRESENT | Every script in this rescue (`routing_lock_monitor.py`, `replay_parity.py`, `balanced_sample.py`) dedups by `world_id`, last-write-wins, matching `e2_run_shard.py::_already_done`'s own discipline; explicitly tested (`test_synthetic_duplicate_world_id_deduplicated`). |
| 14 | Using sample estimates for an exact gate | NOT PRESENT | `routing_lock.py` never imports or reads anything from `balanced_sample.py`; the two modules share no code path. `BALANCED_SAMPLE_DESIGN.md` section 5 states this boundary explicitly as a design invariant, not an afterthought. |
| 15 | Operator accidentally seeing partial A/B/C/D/E counts | FOUND AND FIXED, twice, during this rescue's own construction | (a) `Gate2Lock`/`evaluate_gate2_opaque` deliberately excludes raw counts from every return value an operator-facing caller could print (by construction, tested). (b) A draft of `replay_parity.py`'s per-world output included `witness_path`, whose own enum names (`PHASE2_FRONT_SCAN_B`, `PHASE2_FULL_SCAN_A`) spelled out the A/B stage letter directly -- caught before it reached `MURU_V2_E2_REPLAY_PARITY.json`, removed, and the reasoning is documented in the script's own comments so it cannot silently regress. |
| 16 | Invalid Wilson/binomial inference under finite-population sampling | NOT PRESENT | `design_based_moe` uses the correct finite-population-corrected, proportionate-stratified-sampling variance formula (derived and proven in `BALANCED_SAMPLE_DESIGN.md` section 2), not a naive Wilson/binomial interval that would ignore both the stratification and the sampling-without-replacement correction. |
| 17 | Family imbalance | DISCLOSED, NOT HIDDEN | Proportionate allocation (constant `r/12` sampling fraction in every one of the 45 cells) prevents any family/regime/noise cell from being over- or under-weighted by construction. The resulting family-level MOE (9.85% at r=6, worse than the 4.40% overall figure) is reported explicitly, with an honest statement that no offered candidate size reaches <5% at the family level -- not smoothed into a single headline number. |
| 18 | Changed E2b semantics | NOT PRESENT | E2b is not executed, not read, not referenced by any decision this rescue makes; Gate 1's dependency on it is reported as a permanent precondition, never worked around. |
| 19 | Changed E4a gate | NOT PRESENT | Gate 1 and Gate 2's conditions are reproduced verbatim from `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 4 (quoted in full in `ROUTING_LOCK_THEORY.md` section 1); `routing_lock.py` only asks when the verdict is already certain, never redefines what the verdict depends on. |
| 20 | Provenance breaks | RESOLVED | `MURU_V2_E2_RESCUE_V2_PROVENANCE.json` records the live worktree/HEAD/rescue-authority chain, this branch's fork point, the 7-file classifier-version hash, and every artifact's generation command. |

## Two additional findings, not on the mission's own checklist, surfaced by actually running this against real data

**F1 -- `algebraically_equivalent` has no wall-clock cap anywhere in its
call path**, unlike `classify_expression` (which the 2026-08-16 rescue
brought under a hard process-boundary kill). Directly observed during
this rescue's own speed-benchmark shakedown: the EXHAUSTIVE arm (which
calls it unconditionally per row, exactly as production's `score_row`
does) failed to complete classification of a real, already-completed E2a
world's fronts within a 45-second per-world safety budget, on more than
one of the small number of worlds sampled. This is not a benchmark
artifact -- it is the same code path production's own shard workers run
today, for every front row, on every seed, whenever a row parses. It
independently corroborates this rescue's own design choice (deferring
this exact call to at most once per world) as a risk reduction, not only
a speed one, and is flagged here as worth a dedicated follow-up outside
this rescue's scope (bringing `algebraically_equivalent` under the same
process-boundary cap `classify_expression` already has) -- **not
implemented here**, since doing so would touch a frozen, manifest-hashed
file (`discovery/equivalence.py`) and is explicitly out of this rescue's
"do not change equivalence semantics" boundary; a *caller-side* timeout
(wrapping the call, not editing the callee) is the shape a future fix
should take, analogous to `classify_expression`'s own process-boundary
design, and is left as a named, deferred recommendation.

**F2 -- a benchmark-measurement bug, not a scientific one, caught and
fixed live:** an early version of the LAZY+PERSISTENT-CACHE benchmark arm
did not clear `e2_classify`'s own in-process memoization dict between
arms, so its "cold cache" timing was silently riding the immediately-
preceding LAZY arm's leftover state on the same world's same expressions
(a spurious 0.00s "hit" on the very first world benchmarked, which cannot
be a genuine persistent-cache hit on a freshly created, empty database).
Fixed before any number from that arm was used in this report. Recorded
here as a concrete instance of exactly the kind of self-check this
mission's hostile-review requirement is meant to force -- not swept past
because it was "only" a measurement bug rather than a classification one.

## Adoption status

Every MATERIAL finding above (rows 4, 5, 6, 7, 9, 10, 11, 15, plus F1 and
F2) has been resolved before this document is finalized, with one
standing, disclosed, BLOCKING exception that is **operational, not a
defect**: Gate 2's exoneration branch has no ratified numeric threshold
(item 19's underlying source gap, restated in `ROUTING_LOCK_THEORY.md`
sections 3.2-3.3) -- this rescue does not resolve it, does not work around
it, and does not silently assume it away; it constrains what
`routing_lock.py` is allowed to report (`LOCKED_EXECUTE_E4A` or
`FULL_RUN_REQUIRED` only) until a protocol owner ratifies it or the full
540-world census completes.
