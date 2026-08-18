# MURU V2 E4a Prerequisite Verification

Mechanical answer to Step 2, derived from source text only -- no inference,
no bypass, no invented threshold.

## 1. The actual frozen trigger (verbatim structure, not assumed)

`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 4 ("Execution
trigger (results-blind, mechanical)") is unambiguous about composition:
**Gate 1 is checked first, sequentially, and Gate 2 is only reached if
Gate 1 does not stop execution.** Quoted verbatim:

```
GATE 1 (falsification hook, checked first, from B.1's first branch):
    IF E2b's direct measurement contradicts the v1 decomposition's
    69/57 retention-vs-generation split by more than 10 cases --
        THEN this protocol DOES NOT EXECUTE. ... STOP.

GATE 2 (retention-dominance, B.1's second and fifth branches):
    IF B is the strict plurality of {A, B, C+D} ...
        THEN this protocol EXECUTES. ...
```

This is a sequential AND, not an OR and not two independent switches: Gate
2 is never reached at all if Gate 1 fires. `routing_lock.py`'s own module
docstring restates this identically: "The gate is a two-part sequential
predicate," with "GATE 1 ... needs E2b's direct measurement (Held-out
replay, a *separate*, not-yet-run study, out of E2a's scope) ... E2a
completion, however complete, CANNOT resolve Gate 1. Reported as
PENDING_E2B always."

**`evaluate_gate2`'s `LOCKED_EXECUTE_E4A` note states this itself, in the
return value's own text** (not an external inference): *"This locks Gate 2
only. Gate 1 (E2b falsification hook) is a separate, out-of-scope
precondition for actually running E4a."* This is proof from source, not an
interpretation: Rescue-v2's `LOCKED_EXECUTE_E4A` semantics do **not**
include or resolve Gate 1, and the module's own text says so explicitly.

## 2. E2b's actual status

Searched the full repository (all branches, all worktrees) for any E2b
execution artifact: zero found.

- `git log --all --oneline -i --grep="E2b"` returns only design/planning
  commits (the preregistration itself, the remediation plan, Rescue-v2's
  own routing-lock design) -- none is an execution record.
- No `held*out*replay`/`e2b`-named result directory exists anywhere under
  `.claude/worktrees`.
- `MURU_V2_MASTER_EVIDENCE_LEDGER.md` (the reconciliation's 73-finding,
  8-parallel-agent sweep of the *entire* repository, completed the day
  before this migration) contains **zero** mentions of E2b anywhere.

E2b (Held-out replay) has not been run. Gate 1 is therefore neither
confirmed clear nor confirmed triggered -- it is undetermined, exactly the
`PENDING_E2B` state the routing-lock module always reports for it.

## 3. Mechanical answers

```
E2A_ROUTE_LOCK_SATISFIED: YES
```
Gate 2 branch 1 (B strict plurality) is proven locked, irreversibly, per
`MURU_V2_E2_ROUTING_LOCK_FREEZE.md`.

```
E2B_PRECONDITION_SATISFIED: WAITING
```
E2b has not been executed. Gate 1 is checked *before* Gate 2 in the frozen
predicate, so a locked Gate 2 does not supersede or bypass it. This is a
genuine, currently-unsatisfied, sequentially-prior blocking precondition,
not a formality.

```
OTHER_E4A_PREREQUISITES:
  1. Full 540-case E2a population complete with persisted front data
     (section 6: "Population. All 540 E2a cases"). This is a DIFFERENT,
     LARGER requirement than the routing lock, and is NOT the same
     population as Rescue-v2's "balanced n=270 sample" -- that sample is a
     Rescue-v2 migration-only construct for accelerating the ROUTING
     decision specifically; it appears nowhere in
     MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md, and the frozen
     protocol's own population definition (section 6) is simply "All 540
     E2a cases," un-sampled. Sealing the balanced sample does not seal E2a.
     Currently 458/540 (see MURU_V2_E2_ROUTING_LOCK_FREEZE.md); 82
     outstanding.
  2. The quarantined poison world (V2C|E2|mass_affine_descriptor|c_low|
     n_noiseless|r000) has no scheduled resolution path as of this
     verification. Its own diagnosis document is explicit: "E2 completion
     accounting must treat this world as 539 ordinary + 1 pending ... No
     scientific analysis proceeds on a corpus that omits it as though it
     were absent by design." A literal reading of "all 540" cannot be
     satisfied while it remains unresolved, and this document does not
     invent an exception for it.
  3. E4a scoring implementation (Step 4) -- did not exist before this
     session; being built now.
  4. Results-blind amendment (Step 3) frozen.
  5. Control/replay tests (Step 5) passing.
  6. Equivalence-defect reachability (Step 6) resolved or disclosed.
```

```
E4A_EXECUTION_CURRENTLY_ALLOWED: NO
```
Blocked on Gate 1 (E2b, WAITING) and on full-population completion
(prerequisite 1, currently 458/540) at minimum, independent of whether
Steps 3-6's engineering work is finished.

## 4. Explicit non-bypass statement

No number was invented for Gate 1. No exoneration threshold was invented
(`routing_lock.py`'s `ExonerationRatification` remains unconstructed, per
the migration's own Step 13). No substitute population was accepted in
place of "all 540." The balanced-sample distinction in prerequisite 1 above
is reported as a finding, not used to relax anything.
