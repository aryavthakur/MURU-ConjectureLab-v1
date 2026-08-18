# MURU v2 E2 Rescue V2: Exact Routing-Lock Theory

**Status:** design document, part of the E2 computational rescue v2 feasibility
study. Written on branch `claude/e2-rescue-v2-computational`, forked read-only
from the live E2a production HEAD (`dc66e27`, see `PROVENANCE.json`). Changes
nothing under `src/muru/paper_benchmark`, `src/muru/discovery`, or
`src/muru/v2_calibration/e2_*.py` -- adds one new module,
`src/muru/v2_calibration/e2_rescue_v2/routing_lock.py`, plus a CLI and tests.

This document does not decide anything about E2's science. It answers one
narrow, mechanical question: **given partial E2a completion, when can the
frozen E4a routing gate's eventual verdict already be certain, and when can
it not?**

---

## 1. The frozen gate, recovered from source (not paraphrased)

The frozen gate is defined in two places that must agree, and do:

- `v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.9
  ("Decision criterion"), the original declaration.
- `v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` section B.1, the
  causal-tree restatement.
- `v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`
  section 4 ("Execution trigger, results-blind, mechanical"), which is
  explicitly "restat[ing] it as an executable predicate" -- this is the
  version treated as authoritative here, because it is the only one written
  as an ordered, executable if/elif chain rather than an unordered table.

Reproduced verbatim (not summarized) from the preregistration:

```
Let A, B, C, D, E = case counts of the five stages over all 540 E2a cases.
Let NONSUCCESS = A + B + C + D.

GATE 1 (falsification hook, checked first):
    IF E2b's direct measurement contradicts the v1 decomposition's
    69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
    tolerance) -- THEN this protocol DOES NOT EXECUTE. All E4 ablations are
    suspended. STOP.

GATE 2 (retention-dominance):
    IF B is the strict plurality of {A, B, C+D} -- i.e. B > A AND B > C+D --
        THEN EXECUTES. RC3 confirmed. E4a enabled.
    ELSE IF P_retain_given_front is near 1 wherever P_front is high --
        THEN DOES NOT EXECUTE. RC3 WITHDRAWN. STOP.
    ELSE IF A is the strict plurality --
        THEN DOES NOT EXECUTE. RC4 confirmed, E3-gated next (E4b/c/d). STOP.
    ELSE IF C+D is the strict plurality --
        THEN DOES NOT EXECUTE as adoption-relevant; RC7, E4f licensed. STOP.
    ELSE (no strict plurality) --
        THEN EXECUTES in DIAGNOSTIC-ONLY mode, adoption suspended.
```

Two facts about this text drive everything below:

1. **Gate 1 needs E2b.** E2b (Held-out replay) is a *separate* study,
   explicitly out of scope for the E2a run this rescue accelerates (E2
   predeclaration, "Scope" paragraph: "E2b ... is out of scope for this
   run"). No amount of E2a completion can resolve Gate 1. It is reported as
   a standing precondition, not something the E2a monitor can ever lock.
2. **Gate 2 branch 2 ("exoneration") has no numeric definition anywhere.**
   Grepped clean across the preregistration, its `PROTOCOL.json`, and the
   causal decision tree: "near 1" and "wherever P_front is high" are never
   given an epsilon or a per-stratum floor. Contrast with Gate 1's tolerance,
   which *is* pinned exactly ("more than 10 cases (PE2-4's own tolerance)").
   This asymmetry is not an oversight this document may paper over --
   section 3 works out its exact consequence for locking.

---

## 2. Exact worst-case lock inequalities (proof)

Fix the population at 540 E2a cases. Let `n` = number of cases with a
resolved stage (A/B/C/D/E), `r = 540 - n` = number outstanding (this
includes any quarantined-but-unresolved world, e.g. the poison world --
its eventual stage is exactly as unknown as any ordinary outstanding
world's and must never be assumed to resolve favorably). Let `A_n, B_n,
C_n, D_n` be the current counts of each non-success stage, and
`CD_n = C_n + D_n`.

**Claim.** For any of the three competing buckets `X in {A, B, CD}` with
rivals `Y, Z` (the other two), `X` is *guaranteed* to be the eventual
strict plurality of `{A, B, CD}` -- for every possible assignment of the
`r` outstanding cases to stages A/B/C/D/E -- if and only if

```
X_n > Y_n + r   AND   X_n > Z_n + r
```

**Proof.**
*(Sufficiency.)* Any assignment of the `r` outstanding cases gives
`Y_final = Y_n + r_Y <= Y_n + r` and `Z_final = Z_n + r_Z <= Z_n + r`
(since `r_Y, r_Z >= 0` and `r_Y + r_Z <= r`), while `X_final = X_n + r_X
>= X_n` (since `r_X >= 0`). So `X_final >= X_n > Y_n + r >= Y_final` and
symmetrically for `Z`, for every possible split. `X` wins strictly no
matter what.

*(Necessity/tightness.)* Suppose `X_n <= Y_n + r`. The adversary sets
`r_Y = r` (routes every outstanding case to `Y`, none to `X`). Then
`Y_final = Y_n + r >= X_n = X_final`, so `X` is not a *strict* plurality
under this realizable assignment. Symmetrically if `X_n <= Z_n + r`. Hence
the inequality is exactly tight, not merely a conservative sufficient
condition. QED.

This is the mission's suggested form (`B_n > A_n + r AND B_n > CD_n + r`
for a B-route lock) -- but it is derived here from the actual gate
semantics, not assumed; the general form applies identically to A and to
C+D once (and only if -- section 3) they become the relevant branch.

A companion claim, used for locking "no bucket can ever win" (relevant to
branch 5, DIAGNOSTIC_ONLY, once Gate 2 branch 2 is ratified -- section
3.4): bucket `X` **can possibly** win under *some* assignment iff
`X_n + r > Y_n AND X_n + r > Z_n` (the single most-favorable-to-`X`
assignment, `r_X = r`, is both necessary and sufficient to check by the
same monotonicity argument -- giving `X` less of `r` only weakens its own
case and does not change `Y` or `Z`, whose finals depend only on their own
share of `r`).

`src/muru/v2_calibration/e2_rescue_v2/routing_lock.py::_would_lock_bucket`
and `_bucket_can_ever_win` implement exactly these two predicates; ten
synthetic-count unit tests (`tests/test_routing_lock.py`) exercise the
boundary cases (exact ties, off-by-one, r=0, negative-input rejection).

---

## 3. What this proof does -- and does NOT -- license

### 3.1 Branch 1 (EXECUTE / B-dominant) is exactly lockable

Branch 1 is checked *first*, before the non-mechanical branch 2. If
`_would_lock_bucket(B_n, A_n, CD_n, r)` holds, no later branch -- mechanical
or not -- can ever fire instead, because the frozen predicate is a
sequential if/elif chain and branch 1's condition is guaranteed true at
final tally regardless of the outstanding `r` cases. This is a complete,
unconditional, exact lock: `LOCKED_EXECUTE_E4A`.

### 3.2 Branches 3, 4, 5 (RC4 / RC7 / DIAGNOSTIC_ONLY) are NOT exactly
lockable from counts alone -- ever, without a ratification decision

Branch 2 sits between branch 1 and branches 3/4/5 in the frozen if/elif
order. Reaching branch 3 requires branch 2's condition to be *false*.
Branch 2's condition is a **stratified** statement ("wherever P_front is
high") about `P_retain_given_front` computed *per family x regime x noise
cell*, not a function of the four pooled scalars `A_n, B_n, C_n, D_n` this
module receives, and it carries no ratified numeric threshold anywhere in
the frozen source.

Consequence: even a count-pattern that looks unambiguously A-dominant
(e.g. `A_n = 500, B_n = 10, C_n+D_n = 30` at full `r=0` completion) **must
not** be reported as `LOCKED_RC4`, because branch 2 might independently be
true (exoneration) and would fire first, overriding to WITHDRAWN --
something no reading of the four pooled counts can rule out. This is
verified directly: `test_a_or_cd_dominant_never_locks_without_ratified_exoneration`
and `test_cd_dominant_never_locks_without_ratified_exoneration` construct
exactly this scenario at `r=0` (full synthetic completion) and assert the
monitor still reports `FULL_RUN_REQUIRED`.

**This is reported here as a disambiguation that must be ratified by a
protocol owner before this rescue can ever report anything other than
`LOCKED_EXECUTE_E4A` or `FULL_RUN_REQUIRED`** -- consistent with this
project's own established practice of surfacing (not silently resolving)
frozen-document ambiguities that gate a licensing decision (cf.
`[[muru-v2-recoverability-ceiling]]`'s three BLOCKING disambiguations).

### 3.3 What ratification would need to specify

Not decided here -- offered only as the shape a ratification would take,
so a protocol owner has a concrete artifact to approve or reject:

```
near_one_floor:    minimum P_retain_given_front, within a "high P_front"
                   stratum, that counts as "near 1"          (e.g. 0.95)
high_front_floor:  minimum per-stratum P_front that counts as
                   "P_front is high" (defines which of the 45
                   family x regime x noise cells are even in scope)  (e.g. 0.5)
```

`routing_lock.ExonerationRatification` is the (currently unconstructable
by any caller in this module's own API without an explicit, separate
ratification step) container for exactly these two numbers, plus
`ratified_by`/`ratified_on` provenance fields.

### 3.4 Even ratified, branch 2 stays a stratified check this pooled
monitor does not attempt to reduce

Section 2's inequalities operate on pooled 540-case totals. Branch 2 is
evaluated per stratum. A ratified `(near_one_floor, high_front_floor)`
pair does not, by itself, tell a pooled-counts monitor whether *some*
stratum's outstanding cases could still flip that stratum's own
`P_retain_given_front` across the floor. `evaluate_gate2` therefore still
returns `FULL_RUN_REQUIRED` even with a ratified threshold supplied --
see the function's own docstring. A genuine early lock on branches 3/4/5
would require a **second, per-stratum monitor** (out of scope for this
rescue's Part II deliverable; noted as a possible follow-on in the
hostile-review document, not built here, so as not to silently invent a
tie-break after the fact).

### 3.5 Gate 1 is permanently out of this monitor's reach

`LOCKED_EXECUTE_E4A` locks Gate 2 only. Actually running E4a additionally
requires Gate 1 to clear (E2b's direct measurement staying within 10 cases
of the v1 69/57 split) -- a separate, not-yet-executed study. Every
operator-facing report from this rescue states this explicitly (see
`routing_lock.Gate2Lock.note`) rather than implying `LOCKED_EXECUTE_E4A`
alone licenses E4a.

---

## 4. Handling ties, exclusions, invalid worlds

- **Ties.** The frozen predicate uses strict `>` throughout; a tie for the
  max across two or three buckets falls through to branch 5
  (DIAGNOSTIC_ONLY), never to branches 1/3/4. Section 2's inequalities also
  use strict `>` consistently, so a boundary case where the adversary can
  force an exact tie (`X_n == Y_n + r`) correctly reports "not locked" (see
  `test_not_locked_execute_at_exact_boundary`).
- **Invalid/excluded worlds.** The E2 predeclaration section 6 states every
  one of the 540 E2a cases receives exactly one of A/B/C/D/E, "with no case
  left unclassified and no case double-counted" -- there is no separate
  "invalid" or "excluded" category for E2a proper. `E` (SUCCESS) is
  irrelevant to the three-way competition but is still counted toward
  `n_classified` for completion-progress reporting.
- **Quarantined worlds.** A quarantined world (poison or stuck-retry) that
  has no resolved stage yet is simply part of `r`, exactly like any other
  outstanding world -- see Part X's dedicated document for the operational
  side of this; the lock math already treats it correctly by construction
  (adversarial worst case makes no assumption about *why* a case is
  outstanding).
- **Duplicate world_id records.** `E2_EXECUTION_DEVIATION.md` section 16
  documents a real (already-fixed) duplicate-recomputation bug that
  produced two byte-identical records for the same `world_id`. The CLI
  monitor (`routing_lock_monitor.py`) deduplicates by `world_id`
  (last-write-wins) before counting, exactly mirroring
  `e2_run_shard.py::_already_done`'s own dedup discipline, and this is
  covered by `test_synthetic_duplicate_world_id_deduplicated`.

---

## 5. Operator-facing surface (what the monitor is allowed to reveal)

`routing_lock.evaluate_gate2_opaque()` and `routing_lock_monitor.py`'s
`main()` print exactly:

```
ROUTING_LOCK_STATE: <UNLOCKED | LOCKED_EXECUTE_E4A | FULL_RUN_REQUIRED>
N_CLASSIFIED: n/540
R_REMAINING: r
```

(`LOCKED_RC4`, `LOCKED_RC7`, `LOCKED_DIAGNOSTIC_ONLY` exist in the
`LockState` enum for completeness and for the day branch 2 is ratified, but
per section 3.2 no code path in this module can currently produce them.)

Never printed, by construction (verified by
`test_never_exposes_raw_counts_in_state_value` and the two synthetic-CLI
tests that grep the literal count values out of stdout): `A_n, B_n, C_n,
D_n`, any derived rate, or any per-family/per-cell breakdown.

---

## 6. This document's own results-blindness

No function in `routing_lock.py` or `routing_lock_monitor.py` was run
against the live E2a run's actual (still-incomplete, 270/540 as of this
writing) output during this rescue-v2 design task. All demonstrations use
either (a) purely synthetic integer counts with no connection to real
world IDs or stages (`tests/test_routing_lock.py`), or (b) a
schema-faithful but fabricated `worlds_shard_*.jsonl` file with invented
`SYNTH|world|NNNN` IDs (`tests/test_routing_lock_monitor_synthetic.py`) --
mirroring the outcome-blind interim characterization's own precedent
(`muru-e2-interim-characterization`, step 9: dry-running `e2_report.py`
against synthetic schema-faithful data). This satisfies the mission's
results-blindness requirement without needing to inspect any partial E2a
scientific aggregate to prove the monitor works.
