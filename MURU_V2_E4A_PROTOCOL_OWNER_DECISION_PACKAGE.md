# MURU V2 E4a — Protocol-Owner Decision Package (draft, uncommitted)

Consolidates the `SMALLEST_JUSTIFIED_NEXT_ACTION` items from the three
results-blind audits already on this branch:

- `MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md`
- `MURU_V2_E4A_BLOCKER_RESOLUTION_AUDIT.md`
- `MURU_V2_E4A_READINESS_DECISION.md` (HEAD, `c1bea6c`)

No frozen document is amended by this package. It exists to put five decisions
in front of the protocol owner in one pass. Nothing here is scientific
compute, and nothing here is committed or pushed without explicit sign-off.

---

## Current state, in one line each

- **Gate 1 identity**: PASS, 144/144, on the authoritative macOS/ARM64 replay.
- **Gate 1 falsification hook (69/57)**: never produced — the authoritative
  replay persisted `selection_count`/`representative` only, no fronts, no
  scoring pass. Not PASS, not FAIL — unevaluated.
- **Condition 3b**: 539/540 literal fronts. One world
  (`V2C|E2|mass_power|c_low|n_default|r000`) is diagnosed unrunnable on this
  host (4 independent OOM kills, clean isolated retries exhausted).
- **Conditions 6/7 (scoring inputs)**: the sealed x86 corpus has no `score`
  or `loss` column, so R0, R2, R6 all raise `InsufficientRowData`. R0 is the
  control every arm is compared against — this blocks the whole comparison,
  not two arms.
- **Preregistration**: `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`
  (authority for the "materially" threshold, the k/eps values, and R5/R6's
  status) is not recoverable anywhere on this host or in git history. Most
  plausible location: the macOS/ARM64 machine.

---

## Decision (i) — Gate 1's falsification hook

The hook ("if E2b's direct measurement contradicts the 69/57 split by more
than 10 cases, STOP") cannot fire or clear without a measurement that doesn't
exist yet. Three options, none of which I can pick autonomously:

| Option | What it means | Cost |
|---|---|---|
| **A. Authorize a front-persisted E2b re-run** | Re-run the same 144×30 frozen search, but with full per-seed front persistence turned on (the E2 design's actual point), then the scoring pass, on the macOS/ARM64 host | New compute (4,320 searches), architecture-bound to Mac |
| **B. Rule Gate 1 unevaluable and decide E4a's fate on that basis** | Formally record `E2B_69_57_HOOK = UNEVALUABLE` and rule whether E4a stays suspended, proceeds conditionally, or waits | No compute; a governance ruling only |
| **C. Ratify a different criterion** | e.g. treat identity PASS as sufficient without the hook, or substitute a weaker proxy | Amends a frozen criterion — needs explicit owner sign-off, evidence already recorded results-blind if you want to look at it |

I have no basis to prefer one — this is squarely a protocol-owner call. Note the causal decision tree's reopening clause matters here regardless of which you pick: *"CHANGE: SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. Republish the root-cause attribution first."* — so even under (A), if the hook does fire, E4a doesn't come back until a re-published attribution.

**Separately, and not conditioned on the above**: "materially" (the word carrying the >10-case threshold) has no binding definition anywhere recoverable — it's only in the missing preregistration. If you pick (A), you'd also need to either rule how "materially" is bound, or accept the >10-case reading from the routing-lock theory quotation as authoritative despite being second-hand.

## Decision (ii) — Preregistration recovery

This is an operator action, not something executable from here: the file most
plausibly lives at
`/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/...` on the
macOS machine. If you have access to that machine, locating and re-committing
that file (with a recorded hash this time) would resolve part of (i), all of
condition 3b's k/eps ambiguity, and R5/R6's arm status in one action. Worth
doing before deciding (i) or (iv), since it could change what's even in play.

## Decision (iii) — Condition 3b (the missing 540th front)

Reading confirmed mechanically: 3b requires *literal* front data for all 540
worlds — there is no frozen quarantine/exclusion carve-out for E4a's analysis
population (that device, `r_remaining`, is defined only for Gate-2 routing).
Only two routes remain open, both requiring new governance:

1. **Cross-host qualified execution** — re-attempt the one world on a
   higher-memory host, but only after that host passes a 100%-agreement
   parity replay against already-completed worlds. The one prior attempt at
   this (a different cross-host run) failed parity for a host-speed reason
   (`SIMPLIFY_TIMEOUT_SECONDS` wall-clock boundary), and the merge target
   (`results/e2/run/`) is the pre-rescue corpus namespace, superseded by the
   x86-only single-host decision. This route is technically available but
   nontrivial and would need its own qualification pass before it produces
   anything usable.
2. **Explicit ratification of what "all 540" means** for a world diagnosed
   unrunnable (i.e., formally accept 539/540 as complete for E4a purposes).

Or: **rule that E4a does not proceed** on this corpus at all.

## Decision (iv) — Scoring inputs (R0/R2/R6) and arm definitions (R5/R6, k, eps)

- **R0 rewiring**: the sealed corpus already carries
  `retained_by_argmax_score` (a boolean, computed at search time by the same
  frozen selection function) even though it doesn't carry raw `score`.
  Rewiring `retain_r0` to read that flag instead of recomputing argmax(score)
  would reuse a frozen precedent rather than invent one — but it edits a
  Step-4 artifact sealed under condition 5, so it needs your authorization,
  not mine.
- **R2/R6**: need *ranks* 2..k by score, not just the rank-1 flag. Not
  recoverable without re-running the E2a searches to capture `loss`/`score`
  (new scientific compute, out of scope without separate authorization).
  Decision needed: authorize that re-run, or rule R2/R6 out of scope for
  this E4a pass (with the consequence that the frozen arm set is then
  incomplete — R2 is declared mandatory in the design pack, not optional).
- **R5/R6 status, k, eps values**: unrecoverable without the missing
  preregistration (decision ii).

## Decision (v) — Confirm downstream blocks

M2/M3, integration, and E6 all sit downstream of E4a producing a result.
Nothing in the current state changes that. Recommend simply confirming: **yes,
they remain blocked**, no action needed here beyond acknowledgment.

---

## What I am *not* proposing

- No E2b re-run, no E2a re-run, no poison-world execution, no scoring-code
  edit — none of that happens without your answers above.
- No change to the 69/57 historical figures, no invented "materially"
  threshold, no waiver for condition 3b, no R0/R2/R6 substitution.
- This package itself is not committed or pushed. If you want it in the
  history, say so and I'll commit it (and only it — no other file changes).
