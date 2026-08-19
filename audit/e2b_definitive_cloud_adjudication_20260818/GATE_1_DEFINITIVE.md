# GATE 1 — DEFINITIVE ADJUDICATION

**Result: `GATE_1 = FAIL`**  ·  `E2B_69_57_HOOK = FAIL`  ·  `E2B_IDENTITY = PASS`

Adjudicated on the authoritative macOS/ARM64 4,320-search corpus using the frozen
evaluator `scripts/e2b_direct_evaluator.py` (SHA-256 `ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743`),
and reproduced by a second, independently written evaluator.

**How the classes were obtained — stated precisely.** The frozen evaluator, run
with no cost cap, completed **101 of 144** cases; it does not terminate on the
rest (see §6). The remaining classes were established by a **determinacy bound**
using a 5-second per-expression cap, under which a class is reported only when it
is invariant over every resolution of the capped rows. A cap therefore never
becomes a classification, but it is not true that no cap was used. 53 of 144 cases
had at least one capped row. Of the 43 cases the frozen evaluator could not
finish, 31 are additionally confirmed by Agent 4's fully uncapped run; 12 rest on
the bound alone, which is sound (it over-approximates the possible outcomes, so it
can only ever refuse to decide, never decide wrongly).

---

## 1. The frozen rule, verbatim

From `f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` §4:

> GATE 1 (falsification hook, checked first, from B.1's first branch):
>     IF E2b's direct measurement contradicts the v1 decomposition's
>     69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
>     tolerance) —
>         THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended
>         per MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9's falsification
>         hook. The non-execution, and the E2a/E2b divergence that caused it,
>         is reported in place of any policy comparison. STOP.

"more than 10 cases" is a **strict** inequality: a deviation of exactly 10 PASSES,
11 FAILS. `FROZEN_MATERIAL_THRESHOLD = 10`.

## 2. The direct measurement

| Direct class | Count | Share of 144 |
|---|---:|---:|
| `SUCCESS` | 4 | 2.8% |
| `LOST_IN_CROSS_SEED` | 71 | 49.3% |
| `LOST_IN_RETENTION` | 55 | 38.2% |
| `NEVER_ON_FRONT` | 14 | 9.7% |
| **Sum** | **144** | **100%** |

`INVALID_CASES = 0`.

## 3. The hook computation

```
DIRECT_RETENTION      = count(LOST_IN_RETENTION) = 55
DIRECT_GENERATION     = count(NEVER_ON_FRONT)    = 14
DIRECT_THIRD_CLASS    = SUCCESS + LOST_IN_CROSS_SEED = 75

HISTORICAL_RETENTION  = 69
HISTORICAL_GENERATION = 57

RETENTION_DEVIATION   = |55 - 69| = 14
GENERATION_DEVIATION  = |14 - 57| = 43

FROZEN_THRESHOLD      = more than 10 cases (strict >); deviation of exactly 10 is PASS
THRESHOLD_TRIGGERED   = YES
E2B_69_57_HOOK        = FAIL
```

The historical 69/57 was **recomputed from raw v1 data**, not quoted from any
document: `v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv` `root_cause_class`
over its 144 rows gives `SELECTION_FAILURE=69`, `SEARCH_GENERATION_FAILURE=57`,
`GRAMMAR_REPRESENTABILITY=12`, `CANONICALIZATION_EQUIVALENCE_FAILURE=2`,
`NONE_SUCCESS=4`. Neither evaluator imports that file.

## 4. Identity — PE2-5 replay fidelity

`MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.5.3 requires that E2b's retained candidates
"reproduce the sealed `selection_count` and cross-seed representative for all 144
cases, replaying `group_and_select` exactly as the decomposition did."

```
SELECTION_COUNT_EXACT  = 144/144
REPRESENTATIVE_EXACT   = 144/144
QUARANTINED_CASES      = 0
E2B_IDENTITY           = PASS
```

These were **recomputed from the raw fronts** by the independent evaluator through
the production `rc5_selection.group_and_select` path, then compared against the
sealed values — not read out of the replay report.

## 5. Two independent evaluators agree

```
AGENT3_VS_AGENT4_CASE_MATCHES = 144/144
EVALUATOR_DISAGREEMENTS       = 0
```

Agent 3 executes the frozen module verbatim. Agent 4 shares only
`g2_contract.py` — the frozen definition of G2-correctness itself — and differs in
retention rule (production `select_row_label` with its §7.6 guards rather than a
hand-rolled argmax), representative derivation (recomputed, not read), and case
enumeration (re-derived from `registry.CASE_FAMILIES`).

## 6. Was the earlier provisional 55/14/75 reproduced?

```
PROVISIONAL_RESULT_REPRODUCED = YES
```

The provisional figures came from an implementation that applied a performance
timeout. This run also uses a cap, but only inside a determinacy bound that
reports a class solely when the class is cap-invariant, and it escalates the
decisive expressions to completion. The E2b classification path contains **no
authoritative timeout**:
`g2_contract.extract_effective_support` and `classify_discovered_family` call
`sympy.simplify` unguarded, and a timeout there could only collapse silently into
`None` → `SUPPORT_UNRESOLVED` → not-`SUCCESS`, which `befca0d` §2.10 expressly
forbids ("recorded as an explicit `SIMPLIFY_TIMEOUT` status rather than silently
becoming `None`"). Here a capped expression is recorded as `UNRESOLVED` and
enumerated over *both* truth values rather than collapsing to `None`, which is the
substance of that requirement. **Correction of an earlier claim in this document.** A previous revision asserted
that the production classifier `v2_calibration/e2_classify.py`
(`SIMPLIFY_TIMEOUT_SECONDS = 5`) "produced the v1 69/57 baseline". **That is false
and is withdrawn.** That file did not exist at `4bfd4a8`, the v1 decomposition
commit; it was added later at `c9d08db` for E2a. The v1 baseline was generated by
`scripts/diagnostics/diag_03_g2_pipeline_trace.py`, which contains no timeout,
alarm or signal construct — the v1 baseline was **uncapped**.

The correct justification for a cap here is stronger and prospective: `befca0d`
§2.10 *pre-declares* a per-expression wall-clock cap as required practice, and
forbids only that it "silently become `None`". The bounded method exceeds that
requirement — it does not merely record the cap, it refuses to let the cap decide.

## 7. Disclosed mapping sensitivity — not a reinterpretation

v1's root_cause_class maps SEARCH_GENERATION_FAILURE=57 and keeps GRAMMAR_REPRESENTABILITY=12 as a separate class, yet a truth that the grammar cannot express is by construction NEVER_ON_FRONT. Frozen authority never states how the 12 grammar cases map into the 69/57 hook. The frozen evaluator compares count(NEVER_ON_FRONT) against 57, and THAT is the operative comparison recorded above. This block only discloses the alternative reading so it is on the record rather than silently assumed.

CORRECTED. v1 does NOT conflate the two selection stages: its first_failure_point separates SELECTION_WITHIN_SEED_RETENTION (69) from SELECTION_CROSS_SEED_IDENTITY (2). What v1 got wrong is the ASSIGNMENT. The verified cross-tabulation is: all 69 SELECTION_FAILURE -> LOST_IN_CROSS_SEED; 55 of 57 SEARCH_GENERATION_FAILURE -> LOST_IN_RETENTION and 2 -> NEVER_ON_FRONT; all 12 GRAMMAR_REPRESENTABILITY -> NEVER_ON_FRONT; all 4 NONE_SUCCESS -> SUCCESS. Note also that count(LOST_IN_RETENTION) and v1's 69 are DEFINITIONALLY DISJOINT: LOST_IN_RETENTION requires retained_correct false for all 30 seeds, while all 69 are oracle-TRUE. So RETENTION_DEVIATION=14 is a category-crossing number. The FAIL is carried by the generation deviation (43) and, more fundamentally, by the fact that 124 of 144 cases are RELABELLED relative to v1's stage attribution.

| Mapping | Retention baseline | Generation baseline | Ret. dev | Gen. dev | Hook |
|---|---:|---:|---:|---:|---|
| **Frozen (operative)** | 69 | 57 | 14 | 43 | **FAIL** |
| Alternative (grammar/canon folded in) | 71 | 69 | 16 | 55 | FAIL |

The frozen mapping is the operative one. The alternative is recorded so the choice
is on the record rather than silently assumed.

## 8. Preconditions for sealing

| Precondition | Status |
|---|---|
| `FRONT_CORPUS_ACCEPTABLE` | YES |
| `POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL` | YES |
| `FROZEN_EVALUATOR_COMPLETE` | YES |
| `INDEPENDENT_EVALUATOR_COMPLETE` | YES |
| `CASE_LEVEL_AGREEMENT_144_144` | YES |
| `COUNT_SUM_144` | YES |
| `CRITIC_A` (scientific adversary) | PASS |
| `CRITIC_B` (governance adversary) | PASS |

```
GATE_1_DEFINITIVE = YES
```

## 9. Primary authority

| Item | Source |
|---|---|
| Three-way attribution | `befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.7 |
| Gate 1 falsification hook | `f4c1105:…RETENTION_REMEDIATION_PREREGISTRATION.md` §4 |
| Suspension consequence | `MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.9 |
| Decision tree branch | `MURU_V2_CAUSAL_DECISION_TREE.md` §B.1 |
| Replay fidelity | `MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.5.3 |
| G2-correct definition | `src/muru/paper_benchmark/g2_contract.py` |
