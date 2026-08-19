# MURU AUTONOMOUS CLOUD ADJUDICATION — FINAL TERMINAL REPORT

> **`DECISION_INADMISSIBLE`** (`befca0d` §2.3/§2.4). E2b outputs may corroborate or
> contradict a conclusion already reached on E2a. They may **not** license any v2
> threshold, retention rule, grammar change, classifier change, benchmark change, or
> forward experiment.

**Terminal state: `A. GATE_1_FAIL_DEFINITIVELY_SEALED_AND_FORWARD_PATH_RESOLVED`**

---

## 1. The result

| | |
|---|---|
| `E2B_69_57_HOOK` | **FAIL** |
| `E2B_IDENTITY` | **PASS** (144/144 selection_count, 144/144 representative, 0 quarantined) |
| `GATE_1` | **FAIL** |
| `GATE_1_DEFINITIVE` | **YES** |
| `CRITIC_A` / `CRITIC_B` | PASS / PASS |

| Direct class | Count | Share |
|---|---:|---:|
| `LOST_IN_CROSS_SEED` | 71 | 49.31% |
| `LOST_IN_RETENTION` | 55 | 38.19% |
| `NEVER_ON_FRONT` | 14 | 9.72% |
| `SUCCESS` | 4 | 2.78% |
| **Sum** | **144** | |

```
DIRECT_RETENTION  = 55  vs historical 69 -> deviation 14
DIRECT_GENERATION = 14  vs historical 57 -> deviation 43
FROZEN_THRESHOLD  = more than 10 cases (strict >)   -> HOOK = FAIL
AGENT3_VS_AGENT4_CASE_MATCHES = 144/144, disagreements 0, invalid 0
PROVISIONAL_RESULT_REPRODUCED = YES (55/14/75)
```

## 2. What actually went wrong with the v1 decomposition

Not noise — a **systematic one-stage mislabel**. The direct classes cross-tabulate
against v1's `root_cause_class` almost as a bijection:

| Direct class | v1 called it | n |
|---|---|---:|
| `LOST_IN_CROSS_SEED` | `SELECTION_FAILURE` 69 + `CANONICALIZATION` 2 | 71 |
| `LOST_IN_RETENTION` | **`SEARCH_GENERATION_FAILURE` 55** | 55 |
| `NEVER_ON_FRONT` | `SEARCH_GENERATION_FAILURE` 2 + `GRAMMAR` 12 | 14 |
| `SUCCESS` | `NONE_SUCCESS` 4 | 4 |

- All **69** of v1's "within-seed retention failures" are in fact **cross-seed voting**
  failures.
- **55 of v1's 57** "generation failures" are in fact **retention** failures — the
  truth-recovering expression *was* generated and *was* on the front.
- **124 of 144 cases are relabelled**; only 20 keep their v1 stage attribution.

This is the design's own pre-declared **H_partial** (`befca0d` §2.1), stated
first-class "so it cannot be discovered and then quietly absorbed."

**Crucially, this is not a replication failure.** E2b reproduces everything v1 could
observe, exactly: v1 `seeds_with_g2_success` == E2b `seeds_with_retained_correct` on
**144/144** cases at integer granularity, and the oracle partition matches 75/69. E2b
diverges from v1 *only* where E2b added information v1 never had — the front itself.

## 3. The two frozen defects, resolved

**Defect A — post-freeze serialization patch.** `git diff dabcb4b..6b18dd8 -- src/muru/`
is **zero bytes**; only the replay runner changed, entirely inside
`_to_json_safe`/`_serialize_front`/`_json_default`. The one real subtlety —
`np.float64` subclasses `float`, so `score`/`loss` take a *different* branch post-patch
and are emitted unconverted — was closed by machine proof: **0 JSON differences across
300,009 uniform-random IEEE-754 bit patterns** plus int64/str/bool. `sympy_format` and
`lambda_format` have zero consumers repo-wide.
`POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL = YES`.

**Defect B — the evaluator "failed or became impractically slow".** The root cause was
never slowness: the frozen evaluator **does not terminate** on a large minority of the
corpus. Observed directly — workers pegged at 99.9% CPU with under 1 GB RSS for 34–62
minutes with zero completions, and two cases killed by the kernel OOM killer above
25 GB. `befca0d` §2.10 names it: *"simplify is unbounded in the worst case."*

It was resolved **without letting a cost limit become a classification**: every front
row resolves to `CORRECT` / `INCORRECT` / `UNRESOLVED`, and a case receives a class
only when the frozen decision tree returns that same class under *every* resolution of
its unresolved rows. 140/144 were invariant outright; the remaining 4 hinged on 6
expressions, which were then evaluated individually to completion (5.5–21.8 s each,
all `False`). Validation against uncapped ground truth: **101/101**. Rows unresolved at
the cap: **158 / 51,411 = 0.31%**.

## 4. Why the FAIL is robust

1. **Invariant to unresolved computation.** Before escalation the gate was evaluated
   over all 2⁴ resolutions of the indeterminate cases: generation deviation 43–47.
   FAIL under every assignment.
2. **Invariant across the exhaustive mapping space.** Every mapping using E2b's
   front-level information FAILs. The four PASSes are two name-inversions, one
   v1-against-v1 comparison, and one ad-hoc grammar subtraction; without the
   subtraction that mapping reads 69 vs 57, deviation 12, FAIL. Even the mapping that
   reads E2b as *vindicating* retention (126 vs 69) trips the threshold — the v1
   attribution is contradicted in **both** directions.
3. **Independently replicated.** A separate evaluator using production
   `rc5_selection.select_row_label` and a from-scratch recomputation of the cross-seed
   representative reproduces all 144 classes.
4. **Two hostile adversaries.** Neither moved a single case. CRITIC_A broke through on
   the mapping; CRITIC_B refuted the break-through; CRITIC_A withdrew.

## 5. Forward path — determined by frozen authority

`f4c1105` §4: *"this protocol DOES NOT EXECUTE. All E4 ablations are suspended… The
non-execution, and the E2a/E2b divergence that caused it, is reported in place of any
policy comparison. **STOP**."*  B.1: *"SUSPEND ALL E4 ABLATIONS until the contradiction
is resolved. **Republish the root-cause attribution first**."*  §4 terminal leaf:
*"No v2 architecture is proposed at all."*

| Experiment | Status |
|---|---|
| E4a | **SUSPENDED** — does not execute (Gate 1 is checked *first* and overrides Gate 2's `LOCKED_EXECUTE_E4A`) |
| E4b–E4f | **SUSPENDED** — the hook suspends *all* E4 ablations |
| E4f (the only cross-seed arm) | Suspended; additionally **cannot be licensed by E2b** (`DECISION_INADMISSIBLE`), and §2.9's licensing table is keyed to the **E2a** attribution where B (retention) is the sealed plurality — its predicate is measured **false** |
| E0, E1, E3 | **ALREADY COMPLETE** and hostile-audited (`bdbcea6`, `4841f11`, `1d20731`, `94abf97`) |
| E6 | **SELF-BLOCKED** by its own README pending exactly this hook |
| E5 | Gated by E3, informed by E4d (suspended) — the sole live gap |
| M2 / M3 | **NOT APPLICABLE** — the G1 adequacy-ladder models, not G2 repair families |

E3's completed verdicts compound the STOP: `mass_affine_descriptor` and
`mass_exponential_descriptor` are **MARGINAL** with `search_side_attribution_licensed:
false`. E2b's 14 `NEVER_ON_FRONT` are 12 F18 (exponential) + 2 — so even the search-side
route was already foreclosed by a completed experiment.

**No prospectively authorized experiment is executable now.**

## 6. What requires the protocol owner

The republication's *content* is preregistered (population §2.8, statistic §2.7, freeze
discipline §2.5) and is computed and sealed in `ATTRIBUTION_REVISION.md`. What is
absent from every commit on every branch is an **acceptance rule**, an **adjudicator**,
and any definition of what discharges *"until the contradiction is resolved"*.

| ID | Decision required |
|---|---|
| D1 | Ratify the republished attribution (71 / 55 / 14 / 4) |
| D2 | Ratify the class-name mapping as the operative reading of the 69/57 hook |
| D2-ext | Rule on the §2.9-vs-§2.11 posture difference (governs re-entry only) |
| D3 | Define "resolved" and commission the republication protocol |
| D4 | Rule on E5 |
| D5 | Rule on E2a's status as a calibration surface (§2.3) |
| D6 | Disposition of the corpus-level §2.3/§2.4 schema omission |

## 7. Self-check

| Question | Answer |
|---|---|
| All 4,320 authoritative Mac fronts used? | Yes — 0 hash mismatches, 0 torn, 51,411 rows |
| New symbolic search avoided? | Yes — none performed |
| Post-freeze serialization proven neutral? | Yes — 0 JSON diffs over 300,009 patterns |
| Frozen classifier produced all case labels? | Yes — 144/144, 0 indeterminate |
| Independent classifier reproduced every label? | Yes — 144/144 |
| Counts reconcile exactly? | Yes — sum 144, 0 invalid |
| Two hostile critics found no unresolved defect? | Yes — both PASS |
| Gate 1 genuinely definitive? | Yes |
| Frozen consequence followed? | Yes — E4a not executed; all E4 suspended |
| Stopping only at a real governance boundary? | Yes |
