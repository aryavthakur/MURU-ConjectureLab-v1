# ATTRIBUTION REVISION — republished root-cause ranking from direct measurement

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

## 6. What this document is NOT

`MURU_V2_CAUSAL_DECISION_TREE.md` §B.1 orders the attribution "republished" but no
commit in the frozen corpus defines a republication *protocol*: no population, no
statistic, no acceptance rule, no freeze discipline, no adjudicator, no template.
This document therefore supplies the republication's **content** computed from
sealed evidence under the frozen four-way partition. Ratifying it as *the*
republished attribution is a protocol-owner act, not an analyst act — see
`FORWARD_AUTHORITY_MAP.md` and `FINAL_TERMINAL_REPORT.md`.
