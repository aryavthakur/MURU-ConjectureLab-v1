# MURU v2 — E2a INSTRUMENT DIAGNOSTIC (D-INST)

**Prospective post-Gate-1 protocol-owner amendment created under the
maximum-authorization instruction. NOT historically preregistered.**

**Frozen before any diagnostic result is computed.** Written and hash-frozen prior
to execution; the result is not known to the author at freeze time.

---

## 1. PURPOSE

Determine whether the E2a corpus's sealed `first_loss_stage` attribution is
**determinate** under the same determinacy standard the sealed Gate 1 adjudication
used, or whether it is partly an artifact of a wall-clock instrument.

This is a **diagnostic**, not a gate. It licenses nothing. It cannot re-qualify E2a
(D5 stands; re-qualification requires all eight D3 conditions). Its sole output is
a determinacy interval and a statement of whether E2a's routing plurality is
invariant. It exists to inform the *design* of the replacement surface — the role
the protocol owner's D5 explicitly preserves for E2a: "synthetic-domain diagnostic
evidence."

**It does not reopen Gate 1.** Gate 1 compared E2b against the v1 historical 69/57
and is sealed, FAILED, and closed. This diagnostic concerns E2a's own internal
attribution and touches no Gate 1 quantity.

## 2. AUTHORITY

| Element | Source |
|---|---|
| Determinacy standard | The sealed Gate 1 adjudication's bounded-determinacy method (`GATE_1_DEFINITIVE.json`, `FROZEN_EVALUATOR_EXECUTION_MANIFEST.json`) — reused verbatim, no new rule |
| Four-way partition | `befca0d` §2.7 / `MURU_V2_E2_PREDECLARATION.md` §6 witness order |
| G2-correctness | `src/muru/paper_benchmark/g2_contract.py`, unmodified |
| E2a's role as diagnostic evidence | D5, ratified |
| Prohibition on a cap deciding a label | `befca0d` §2.10; Gate 1 precedent |

**No new threshold is introduced by this protocol.** The only decision rule is
determinacy, taken verbatim from Gate 1.

## 3. THE DEFECT UNDER TEST

`lazy_classify._g2_correct` passes `classification.effective_support = None` into
`classify_support` whenever canonicalization did not return `OK`. A
`SIMPLIFY_TIMEOUT` therefore yields `SUPPORT_UNRESOLVED` → not `SUCCESS` →
`g2_correct = False`, **deterministically**. A wall-clock timer decides a
scientific label, and does so monotonically toward "no correct row" — i.e. toward
earlier-stage loss.

Observed contamination by sealed stage (recomputed for this protocol):

| Stage | Worlds with ≥1 timed-out front row | Total | % |
|---|---:|---:|---:|
| A | 73 | 122 | 59.8 |
| B | 20 | 196 | 10.2 |
| C | 3 | 102 | 2.9 |
| E | 1 | 119 | 0.8 |

## 4. SCOPE — exactly what is recomputed

**Zero new symbolic search.** No world is re-run. No front is regenerated.

The witness order is `A if n_correct_on_front == 0`, so a timed-out row can only
change a world's stage by turning out to be **correct**. Only worlds sealed as
stage **A** can therefore change class on this evidence:

- affected stage-A worlds: **73**
- timed-out front rows within them: **314**
- of those, rows that are the seed's retained (`retained_by_argmax_score`) row: **2**

Rows in stage-B/C/E worlds are recomputed as a **control** (their stage cannot move
upward on this evidence) and reported, but are not part of the primary statement.

## 5. METHOD

For each affected (world, expression) pair:

1. Recover the world's truth via `e2_worlds.build_world(family, regime, noise, replicate)`.
2. Evaluate G2-correctness with `g2_contract`'s own primitives —
   `extract_effective_support`, `classify_discovered_family`, `classify_support`,
   `classify_family_match`, `evaluate_g2_event` — **unmodified**.
3. Run each evaluation in a **dedicated subprocess** with a generous budget
   (`DIAGNOSTIC_ESCALATION_SECONDS = 1800`), isolated so a pathological expression
   cannot take down the run.
4. Outcome per pair ∈ {`CORRECT`, `INCORRECT`, `UNRESOLVED`}. `UNRESOLVED` means the
   generous budget was exhausted. **`UNRESOLVED` is never a classification.**

Then, for each affected world, recompute the stage under the frozen witness order at
**both** extremes of the unresolved set:

- `LOWER`: every `UNRESOLVED` treated as INCORRECT
- `UPPER`: every `UNRESOLVED` treated as CORRECT

## 6. PRIMARY STATEMENT (the only claim this diagnostic makes)

```
E2A_ATTRIBUTION_DETERMINATE ⟺ for every affected world, the recomputed stage is
                               identical under LOWER and UPPER
```

and, separately:

```
E2A_PLURALITY_INVARIANT ⟺ the predicate (B > A) AND (B > C+D)
                           holds identically under LOWER and UPPER
```

Both are reported with the full interval on each stage count. If the plurality is
**not** invariant, then E2a's `LOCKED_EXECUTE_E4A` routing was never determinate on
its own corpus — a factual statement about determinacy, carrying no licence either
way.

## 7. WHAT THIS DIAGNOSTIC MAY AND MAY NOT CONCLUDE

**MAY:** report the corrected/interval attribution; state whether E2a's plurality is
determinate; inform the replacement surface's design (composition control, instrument
choice).

**MAY NOT:** re-qualify E2a as a calibration surface; restore `LOCKED_EXECUTE_E4A`;
license any E4 arm; alter any sealed Gate 1 quantity; alter the ratified D1
attribution.

## 8. HANDLING AND HONESTY RULES

- A subprocess kill, OOM, or budget exhaustion is recorded as `UNRESOLVED` and is
  **never** converted into `INCORRECT`.
- Every affected pair is reported, including those that do not move a stage.
- The count of pairs that remain `UNRESOLVED` after escalation is reported
  prominently; if it is non-zero the primary statement is made only in interval form.
- The result is reported whichever way it comes out. A finding that the attribution
  **is** determinate is as publishable as one that it is not.

## 9. TERMINAL STATES OF THIS DIAGNOSTIC

| State | Meaning |
|---|---|
| `D-INST-DETERMINATE` | Every affected world's stage is invariant; E2a's attribution stands as sealed |
| `D-INST-INDETERMINATE` | ≥1 affected world's stage is not invariant; the interval is reported |
| `D-INST-PLURALITY-NOT-INVARIANT` | The routing predicate itself differs between LOWER and UPPER |

## 10. PRE-RECORDED EXPECTATION (results-blind, for the record)

Recorded before execution so the record shows the design was not chosen for its
answer: given 73 of 122 stage-A worlds carry an abandoned row and the mechanism is
monotone, I expect **`D-INST-INDETERMINATE`** to be more likely than not, and I
consider `D-INST-PLURALITY-NOT-INVARIANT` plausible but not established. I record
now that I will report the opposite outcome with equal prominence if it occurs.
