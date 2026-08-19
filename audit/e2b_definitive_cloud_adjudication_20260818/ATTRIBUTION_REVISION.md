# ATTRIBUTION REVISION — republished root-cause ranking from direct measurement

> **`DECISION_INADMISSIBLE`** (`befca0d` §2.3/§2.4). E2b outputs may corroborate or
> contradict a conclusion already reached on E2a. They may **not** license any v2
> threshold, retention rule, grammar change, classifier change, benchmark change, or
> forward experiment. `RANK_1 = LOST_IN_CROSS_SEED` does **not** license E4f.

**Trigger.** `GATE_1 = FAIL`. `MURU_V2_CAUSAL_DECISION_TREE.md` §B.1 requires:
"SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. **Republish the
root-cause attribution first.**" This document is that republication's *content*.
It is not, and does not claim to be, the republication *protocol* — see §6.

---

## 1. The republished ranking (direct, n = 144)

| Rank | Direct class | Count | Share |
|---:|---|---:|---:|
| 1 | `LOST_IN_CROSS_SEED` | 71 | 49.31% |
| 2 | `LOST_IN_RETENTION` | 55 | 38.19% |
| 3 | `NEVER_ON_FRONT` | 14 | 9.72% |
| 4 | `SUCCESS` | 4 | 2.78% |

Superseded v1 decomposition: `SELECTION_FAILURE` 69, `SEARCH_GENERATION_FAILURE` 57,
`GRAMMAR_REPRESENTABILITY` 12, `CANONICALIZATION_EQUIVALENCE_FAILURE` 2, `NONE_SUCCESS` 4.

## 2. Why the decomposition failed — a systematic one-stage mislabel

The direct classes cross-tabulate against v1's `root_cause_class` almost as a
**bijection**, which is the central finding: the v1 attribution was not noisy, it
was *systematically* wrong.

| Direct class | v1 `root_cause_class` | n |
|---|---|---:|
| `LOST_IN_CROSS_SEED` (71) | `SELECTION_FAILURE` 69 · `CANONICALIZATION_EQUIVALENCE_FAILURE` 2 | 71 |
| `LOST_IN_RETENTION` (55) | **`SEARCH_GENERATION_FAILURE` 55** | 55 |
| `NEVER_ON_FRONT` (14) | `SEARCH_GENERATION_FAILURE` 2 · `GRAMMAR_REPRESENTABILITY` 12 | 14 |
| `SUCCESS` (4) | `NONE_SUCCESS` 4 | 4 |

Read plainly:

1. **Every one of v1's 69 "selection failures" is in fact a cross-seed voting
   failure.** The correct candidate survived within-seed retention; it was the
   cross-seed identity-grouping vote that discarded it. v1's single
   `SELECTION_VOTING` stage (71 cases) conflates within-seed retention with
   cross-seed voting, so it could not distinguish these.
2. **55 of v1's 57 "generation failures" are in fact retention failures.** The
   truth-recovering expression *was* generated and *was* on the Pareto front —
   it was discarded by within-seed `argmax(score)` retention. Only 2 of the 57
   are genuinely never-generated.
3. The 12 `GRAMMAR_REPRESENTABILITY` cases map to `NEVER_ON_FRONT` exactly as
   expected: a truth the grammar cannot express can never appear on a front.

So the historical 69 "retention" figure and the historical 57 "generation" figure
are each attributed **one pipeline stage away** from where the loss actually occurs.

## 3. Independent corroboration that this is a re-attribution, not a re-measurement

v1's own `oracle_any_seed_correct` column records whether any of the 30 per-seed
retained candidates was correct. The direct partition implies the same predicate
(`SUCCESS` or `LOST_IN_CROSS_SEED`). They agree **144/144**:

```
v1 oracle TRUE  = 75      direct retained-correct-ever   = 75
v1 oracle FALSE = 69      direct retained-correct-never  = 69
case-level agreement = 144/144, disagreements = 0
```

This is decisive for interpreting the failure. v1 and E2b agree *perfectly* on the
underlying observable — whether a correct candidate ever survived retention. They
disagree only on **which stage to blame**. The v1 measurement was sound; the v1
*attribution* was not.

## 4. Gate 1 arithmetic

```
DIRECT_RETENTION   = count(LOST_IN_RETENTION) = 55   vs 69 -> deviation 14
DIRECT_GENERATION  = count(NEVER_ON_FRONT)    = 14   vs 57 -> deviation 43
DIRECT_THIRD_CLASS = SUCCESS + LOST_IN_CROSS_SEED = 75
FROZEN_THRESHOLD   = more than 10 cases (strict >)
E2B_69_57_HOOK     = FAIL
```

## 5. Robustness of the FAIL

The verdict does not depend on any contested reading:

- **Mapping ambiguity.** Frozen authority never states how v1's 12
  `GRAMMAR_REPRESENTABILITY` cases enter the 69/57 hook. The frozen comparison is
  against 57 literally. Folding the grammar cases in (57+12=69) makes the
  generation deviation *larger* (55, not 43). Both readings FAIL.
- **Unresolved computation.** Before expression-level escalation, 4 cases were
  indeterminate. The gate was evaluated over all 2^4 = 16 resolutions:
  `DIRECT_RETENTION` ranged 55–59 and `DIRECT_GENERATION` 10–14, giving generation
  deviations of 43–47. **FAIL under every assignment.**
- **Independent replication.** A separate evaluator using the production
  `rc5_selection` retention rule and a from-scratch recomputation of the cross-seed
  representative reproduces all 144 classes: `AGENT3_VS_AGENT4_CASE_MATCHES = 144/144`.

## 6. What this document is NOT — and precisely what authority is missing

`MURU_V2_CAUSAL_DECISION_TREE.md` §B.1 orders the attribution "republished". This
document supplies that republication's **content**, computed from sealed evidence
under the frozen four-way partition. It does not claim to be the republication
*protocol*, and ratifying it is a protocol-owner act, not an analyst act.

An earlier draft of this section claimed the frozen corpus defines *no* population,
statistic, acceptance rule, freeze discipline, adjudicator or template. **That
overstated the gap and is corrected here.** Three of those six are in fact
preregistered, results-blind:

| Element | Status | Frozen source |
|---|---|---|
| Population | **FROZEN** | §2.8: "**E2b.** 144 Held-out G2 cases x 30 seeds = **4,320 searches**." |
| Statistic | **FROZEN** | §2.7: "Every case is assigned exactly one label, forming a partition" |
| Freeze discipline | **FROZEN** | §2.5.3 replay fidelity (quarantine-not-drop) + the evaluator's own "FROZEN BEFORE REPLAY", SHA-pinned at `dabcb4b` |
| Mandate and deadline | **FROZEN** | §2.11: "the root-cause ranking's ordering of RC3 and RC4 is recomputed **before E4 proceeds**" |
| Acceptance rule | **ABSENT** | — |
| Adjudicator / template | **ABSENT** | — |
| Definition of "resolved"; re-licensing predicate | **ABSENT** | — |

So the republication's *content* is preregistered and is not an analyst invention.
What is genuinely missing is an acceptance rule, an adjudicator, and any definition
of what discharges "until the contradiction is resolved". Those, and the mapping
conflict in §7, are the protocol-owner boundary.

## 7. The mapping question — raised, adjudicated, and settled

An earlier revision of this section presented three mappings as live alternatives
"blocking ratification", two of them yielding PASS. **That framing was wrong and is
corrected here.** The question was raised by the scientific adversary, adjudicated
against it by the governance adversary, and the scientific adversary withdrew. It
does not block Gate 1.

### 7.1 What was asked

Frozen authority states the numbers 69 and 57 and the tolerance, but never says
*which* E2b class is the "retention-class". The mapping used —
`retention ← LOST_IN_RETENTION`, `generation ← NEVER_ON_FRONT` — lives in
`e2b_direct_evaluator.py:27-28`, frozen prospectively at `dabcb4b`, not in any
authority text. That is a real observation and it stays on the record.

### 7.2 Why it does not change the verdict — the exhaustive mapping space

| Mapping | Direct | Baseline | Dev | Hook |
|---|---:|---:|---:|---|
| `retention ← LOST_IN_RETENTION` | 55 | 69 | 14 | **FAIL** |
| `retention ← LOST_IN_RETENTION` | 55 | 71 | 16 | **FAIL** |
| `retention ← LOST_IN_CROSS_SEED` | 71 | 69 | 2 | PASS — *name inversion* |
| `retention ← LOST_IN_CROSS_SEED` | 71 | 71 | 0 | PASS — *name inversion* |
| `retention ← LIR + LICS` | 126 | 69 | 57 | **FAIL** |
| `generation ← NEVER_ON_FRONT` | 14 | 57 | 43 | **FAIL** |
| `generation ← NEVER_ON_FRONT` | 14 | 69 | 55 | **FAIL** |
| `generation ← NOF + LIR` | 69 | 57 | 12 | **FAIL** |
| `generation ← NOF + LIR` | 69 | 69 | 0 | PASS — *v1 compared to itself* |
| `generation ← NOF + LIR − 12 grammar` | 57 | 57 | 0 | PASS — *ad-hoc subtraction* |

**Every mapping that uses E2b's new front-level information reads FAIL.** The four
PASSes are two name-inversions (scoring "reproduced" precisely on the 69 cases where
the taxonomies disagree about mechanism), one comparison of v1 against itself, and
one that reaches 57 only by subtracting exactly the 12 grammar cases — a step chosen
after observing that it lands on 57. Without that subtraction the same mapping reads
69 vs 57, deviation 12, FAIL.

Note also `retention ← LIR + LICS` = 126 vs 69, deviation 57: even the mapping that
reads E2b as *vindicating* the retention diagnosis more strongly than v1 claimed
still trips the threshold. **The v1 attribution is contradicted in both directions.**

### 7.3 Why the PASS mappings are uninformative

The two "reproduced" readings track set identities that already hold:
v1 `SELECTION_VOTING` is the same 71 case IDs as `LOST_IN_CROSS_SEED`; v1
oracle-FALSE is the same 69 case IDs as `LIR ∪ NEVER_ON_FRONT`.

**What does *not* pin them: the identity gate.** An earlier draft claimed these
identities are entailed by `E2B_IDENTITY = PASS` on any dataset — a "theorem". That
was an overstatement and is withdrawn. `E2B_IDENTITY` (§2.5 control 3) constrains
only the sealed `selection_count` and the cross-seed representative — properties of
the **winning class alone**. The four-way partition turns on
`seeds_with_retained_correct ≥ 1`, a predicate over **all 30 seeds**. A constraint on
the winner cannot entail a predicate quantified over every seed. Constructibly so:
**13 `LOST_IN_CROSS_SEED` cases sit at `seeds_with_retained_correct = 1`** (e.g.
`F04|r000` at `selection_count = 4` of 30). Each such case's single correct-retaining
seed votes in a *losing* class, so swapping it for another losing expression leaves
the winning class, its membership and its representative untouched — identity still
passes 144/144 — while the case moves `LOST_IN_CROSS_SEED → LOST_IN_RETENTION` and
the set identity breaks by one.

**What does pin them: per-seed retention fidelity — a *separately measured* premise.**
The operative hypothesis is
`v1.seeds_with_g2_success == E2b.seeds_with_retained_correct` per case. That is
*stronger* than the identity gate and is precisely the thing identity does **not**
check; it is measured here independently, at **144/144**. Under that measured premise
a genuine conditional result does hold: predeclaration §6 *defines*
`SUCCESS ∪ LOST_IN_CROSS_SEED ≡ {retained_correct ≥ 1}` and
`LIR ∪ NEVER_ON_FRONT ≡ {retained_correct = 0}`, while v1's `SELECTION_VOTING` is its
own oracle-true non-success set — so both alternative deviations are **exactly** zero
on this corpus, provably, from a measured premise rather than an assumed one.

The conclusion is therefore not that those mappings are tautological in the abstract,
but that **they measure replay↔seal fidelity in per-seed retention, not attribution
correctness**. Their reading is fixed by a quantity already confirmed at 144/144, so
they carry no information about what §2.9 says the hook tests: whether *"the
decomposition's **attribution** is wrong"*. Only the class-name mapping measures that,
and it measures it decisively — **124 of 144 cases relabelled**.

### 7.4 §2.9 and §2.11 are the same instruction

An earlier draft read §2.11 as licensing "E4 proceeds" against B.1's suspension.
That was a mis-paraphrase. The frozen text is *"recomputed **before** E4
proceeds"* — a precedence constraint, not a licence — and B.1 supplies the interim
posture: *"SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. Republish
the root-cause attribution first."* Both issue the **same** instruction today:
republish first; E4a does not execute. Both adversaries converged on this.

What remains is a difference of *posture* — §2.11 treats this as an anticipated
revision the programme continues through, §2.9/B.1/§4 as a falsification that halts
it — which governs only the **re-entry path after republication**, not the present.
That is docket item D2-extended.
