# MURU V2 E2 Routing-Lock Freeze (v1.0.0)

Persists the `LOCKED_EXECUTE_E4A` evidence per the user's explicit Step-1
instruction, results-blind: this document exposes **only**
`ROUTING_LOCK_STATE`, completion-progress counts (`N_CLASSIFIED`,
`R_REMAINING`), and the mathematical proof that the state cannot reverse.
It contains **zero** A/B/C/D/E case counts, rates, or per-family/per-cell
breakdowns anywhere, including in the proof itself (the proof is generic
over the unexposed counts -- see section 3).

## 1. Frozen conclusion

```
LOCKED_EXECUTE_E4A
```

This is Gate 2 branch 1 of the frozen routing predicate
(`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 4: "B is the
strict plurality of {A, B, C+D}") -- confirmed mathematically guaranteed
regardless of how the still-outstanding E2a worlds resolve. **This locks
Gate 2 only.** Gate 1 (the E2b falsification hook) is a separate
precondition this document does not resolve -- see
`MURU_V2_E4A_PREREQUISITE_VERIFICATION.md` (Step 2).

## 2. Evidence record

| Field | Value |
|---|---|
| Rescue-v2 authority commit | `c4e75d0ed1c1afc3482ccf3a5d2d89d4e74c5592` (`.claude/worktrees/e2-rescue-v2-computational`, branch `claude/e2-rescue-v2-computational`) |
| classifier_version (7-file source hash) | `90a3b5ea3a83b0e9587e3b1e4e54e188afb8e893fabc9293d9177bc767089e7a` |
| Routing-lock module | `src/muru/v2_calibration/e2_rescue_v2/routing_lock.py`, unchanged since Phase 1 (`evaluate_gate2`/`evaluate_gate2_opaque`) |
| Mathematical lock proof / version | `ROUTING_LOCK_PROOF_v1.0.0` -- `routing_lock.py::_would_lock_bucket`, exact necessary-and-sufficient worst-case-margin inequality (section 3 below); unchanged since first committed Phase 1, no threshold or tolerance in it |
| Source E2 checkpoint (population underlying the counts below) | Old E2 final checkpoint (409/540, `/tmp/e2_rescue_v2_checkpoint_TRULY_FINAL_20260817_165554/`) + 2 Rescue-v2 smoke-verified worlds (`/tmp/e2_rescue_v2_smoke_output/`) + Rescue-v2 production output (`/tmp/e2_rescue_v2_production_out/`, growing) |
| First observed at | `2026-08-17T21:16:xx-04:00` (task notification), `N_CLASSIFIED=445/540`, `R_REMAINING=95` |
| Reconfirmed (independently, fresh read) at | `2026-08-17T17:56:xx-04:00` local (`2026-08-17T21:52:08Z`), `N_CLASSIFIED=458/540`, `R_REMAINING=82` |
| `ROUTING_LOCK_STATE` | `LOCKED_EXECUTE_E4A` at both readings, unchanged |

No A/B/C/D/E count is recorded here or anywhere in this document.

## 3. Irreversibility proof

**Claim.** Once `evaluate_gate2_opaque` reports `LOCKED_EXECUTE_E4A` at any
checkpoint with `r` worlds still outstanding, (a) the eventual verdict over
all 540 E2a cases is guaranteed to be Gate 2 branch 1 (B strict plurality),
for *every* possible resolution of the outstanding worlds, and (b)
re-evaluating the same monitor at any *later* checkpoint (more worlds
resolved, `r` smaller) is guaranteed to report the same
`LOCKED_EXECUTE_E4A` state, never anything else.

**Proof of (a) -- already established, restated for completeness.**
`_would_lock_bucket(B_n, A_n, CD_n, r)` is proven in `routing_lock.py`
(lines 96-119) to be the exact necessary-and-sufficient condition for B to
be the *unique* strict plurality of `{A, B, C+D}` over the full 540-case
population, under every possible assignment of the `r` outstanding cases:

```
LOCK(B)  <=>  B_n > A_n + r   AND   B_n > (C_n+D_n) + r
```

Necessity: if `B_n <= A_n + r`, an adversary can route all `r` outstanding
cases to A, realizing `A_final = A_n + r >= B_n = B_final`, breaking B's
plurality (symmetrically for C+D). Sufficiency: A's and (C+D)'s *most*
favorable final counts are `A_n + r` and `CD_n + r` respectively (routing
all of `r` to that one bucket); B's *least* favorable final count is `B_n`
(routing none of `r` to B) -- and this single worst-case assignment is
simultaneously worst-case for both comparisons, since B's own final count
does not depend on how the rivals split `r` between themselves. If B still
exceeds both rivals' most-favorable totals, no assignment can undo it. This
is the exact proof already in the frozen module; this freeze does not
re-derive it, only cites and applies it.

**Proof of (b) -- monotonic persistence across checkpoints (the
corollary this freeze adds).** Let the lock hold at checkpoint 1:
`B_n > A_n + r` and `B_n > CD_n + r`. At any later checkpoint 2, some
non-negative amount of the outstanding `r` has resolved: `a_delta` cases to
A, `b_delta` to B, `cd_delta` to C+D, with `a_delta + b_delta + cd_delta
<= r` and all three `>= 0` (E-stage resolutions reduce `r` without moving
any of A/B/CD, which only relaxes the inequalities further and is folded
into "≤ r" here). The new state is:

```
B_n' = B_n + b_delta                                    ( >= B_n )
A_n' + r' = (A_n + a_delta) + (r - a_delta - b_delta - cd_delta)
          = A_n + r - b_delta - cd_delta                ( <= A_n + r )
```

So `B_n' >= B_n > A_n + r >= A_n' + r'`, i.e. `B_n' > A_n' + r'` still
holds -- strictly, since the original inequality was strict and every step
above is a non-strict (`>=`/`<=`) preservation. The identical argument
applies to `CD_n' + r' <= CD_n + r < B_n <= B_n'`. **Both inequalities are
preserved under every possible resolution of outstanding cases, for every
subsequent checkpoint, all the way to `r=0`.** The lock cannot revert to
`FULL_RUN_REQUIRED` or flip to any other state once it has fired, regardless
of what the remaining worlds turn out to be.

**Consequence.** No classification of the 82 (or, at first observation, 95)
worlds still outstanding as of this freeze -- however they resolve, in any
combination across A, B, C, D, or E -- can reverse `LOCKED_EXECUTE_E4A`.
This was independently corroborated empirically as well: the state was
observed unchanged (`LOCKED_EXECUTE_E4A`) across two independent readings
13 worlds apart in classification progress (445 -> 458 of 540), exactly as
the proof predicts.

## 4. What this freeze does not establish

Per `routing_lock.py`'s own docstring (quoted in
`MURU_V2_E4A_PREREQUISITE_VERIFICATION.md` section 1): this locks **Gate 2
only**. It says nothing about Gate 1 (the E2b falsification hook), which
is a separate, sequentially-prior, out-of-scope precondition this module
cannot resolve from E2a data at any completeness. See the companion
prerequisite-verification document for the full mechanical answer on
whether E4a may actually execute.
