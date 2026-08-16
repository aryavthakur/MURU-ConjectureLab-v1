# MURU Held-out Rescue — Independent Scoring Result

**Phase C artifact. Derived strictly from the frozen authority matrix and the sealed raw
evidence, BEFORE any post-run analysis artifact was opened.**

Bound to authority matrix:
- `MURU_HELDOUT_RESCUE_AUTHORITY_MATRIX.md` = `2e9b0534ff42fb45ce4e90c8e4854b50c914902c8a0572719be21834ca60a8bf`
- `muru_heldout_rescue_authority_matrix.json` = `b11af625f72dba3121ec26a2d59cfb8e7ebcf9c0af6aace4922d960bd1f16c5c`

Method: frozen scoring functions were **invoked directly**, never reimplemented —
`rc3_scoring.score_g2`, `rc3_scoring.score_g3`, `g3_contract.classify_g3_event`,
`g2_contract.evaluate_g2_event`, `structural_acceptance.evaluate_structural_acceptance`,
`structural_acceptance.check_gate8`, `registry.endpoint_case_count`. Glue code lived outside the
evidence tree and wrote nothing into it.

## 0. Contract-fidelity check (performed first)

The full frozen acceptance predicate was re-evaluated for **all 240 cases** from stored
`StructuralCandidate` inputs plus the recovered frozen null-threshold table (digest
`b9b6148…`, matching the digest recorded in every case record).

| Metric | Value |
|---|---|
| Cases recomputed | 240 |
| Disagreements vs stored `acceptance_status` / `acceptance_gate_reached` | **0** |

**The sealed raw records are exactly faithful to the frozen A3.5 acceptance predicate.** The
execution applied the correct contract. Anything that later went wrong is downstream of this.

## 1. G1 — scalar competence

| Quantity | Value |
|---|---|
| Frozen denominator | **164** (asserted; population built = 164) |
| G1 observables in sealed records | **none** |
| Recoverable conjunct | `m0_accepted ⟺ a1_case_adequacy_status == M0_NOT_REJECTED` |
| A1 distribution over the 164 | `M0_NOT_REJECTED` 67, `BOUNDARY_LIMITED` 97 |
| **Rigorous upper bound on successes** | **67 / 164** |
| Wilson lower 95% at that upper bound | **0.336234** |
| Gate threshold | ≥ 0.70 |
| **Gate verdict** | **FAIL — determinate** |

**Why the verdict is determinate despite missing observables.** `scalar_competent` is a
conjunction whose third term is `m0_accepted`. At most 67 of 164 cases satisfy it, so successes
≤ 67 regardless of `g_spearman` and `trajectory_mae`. Wilson lower at 67/164 is 0.336234, far
below 0.70, and Wilson lower is monotone in successes. **G1 fails for every possible value of
the unrecoverable conjuncts.**

**What is not recoverable**: the exact competent count (somewhere in [0, 67]) and the two
continuous observables. Recovering them requires recomputing G1 from frozen case content and the
frozen training-only `Phi` — **which requires zero searches**, since A3.5 §8.2 records that G1's
inputs are search-independent. **No part of the 7,200-search execution needs rerunning for this.**

## 2. G2 — family recovery

| Quantity | Value |
|---|---|
| Frozen denominator | **144** (asserted; population built = 144) |
| Stored `g2_event` vs recomputed via `evaluate_g2_event` | **0 mismatches** |
| Successes | **4** |
| Failures | 103 |
| Unevaluable | 37 |
| Success rate | 0.027778 |
| Wilson lower 95% | **0.010854** |
| Gate threshold | ≥ 0.70 |
| **Gate verdict** | **FAIL** |

Success case IDs (4): `PB|held_out|F01|r002`, `PB|held_out|F01|r005`, `PB|held_out|F11|r010`,
`PB|held_out|F12|r000` — families F01 ×2, F11 ×1, F12 ×1.

## 3. G3 — principal structural safety

Scored with the frozen sole authority (`g3_contract.classify_g3_event` + `rc3_scoring.score_g3`).
`analysis.classify_negative_control` was **not** used, per A3.5 §8.3.

| Quantity | Value |
|---|---|
| Frozen denominator | **36** (asserted; F07 ×12, F19 ×12, F20 ×12) |
| Violations | **26** |
| Safe | 10 |
| Violation rate | 0.722222 |
| Wilson upper 95% | **0.841518** |
| Gate threshold | ≤ 0.15 |
| **Gate verdict** | **FAIL** |

Driver: 24 of the 26 violations are `UNEVALUABLE` cases, which the frozen contract counts as
violations conservatively. All 12 F20 cases are UNEVALUABLE ⇒ violations. Full per-case event
list is in the JSON companion.

## 4. Gate 7 (ceiling, position 7)

| Quantity | Value |
|---|---|
| Cases reaching Gate 7 | **27** |
| Cases passing Gate 7 | **26** |
| Cases failing Gate 7 | **1** — `PB|held_out|F02|r004` |
| Passed via `ceiling_pass` branch | **26** |
| Passed via `ceiling_waiver` branch | **0** |

**The F5 folded-in floor was never load-bearing in this partition.** No case entered the
low-ceiling waiver regime, so the amended Gate 7 and the pre-amendment Gate 7 produce identical
results on this evidence. The A3.5 Gate-7 amendment is outcome-invariant here as a matter of fact.

Failure-stage distribution across all 240 cases:

| Gate reached | Cases |
|---|---|
| `a1_adequacy` | 154 |
| `stability` | 43 |
| `null_threshold` | 16 |
| `ceiling` | 1 |
| `falsification` | 1 |
| `all_passed` | 25 |

## 5. Gate 8 (four hard rungs, fail-closed)

`REQUIRED_HARD_GATES = {F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT, F7_INFLUENCE_DROP, F10_NEGATIVE_CONTROL}`

| Quantity | Value |
|---|---|
| Cases reaching Gate 8 (denominator) | **26** |
| Gate 8 PASS | **25** |
| Gate 8 FAIL | **1** — `PB|held_out|F07|r005` |

Per-rung status among the 26 cases reaching Gate 8:

| Rung | PASS | FAIL |
|---|---|---|
| F1_REPRODUCIBILITY | 26 | 0 |
| F4_COMPOUND_HOLDOUT | 26 | 0 |
| F7_INFLUENCE_DROP | 26 | 0 |
| F10_NEGATIVE_CONTROL | 25 | **1** |

The single Gate-8 rejection is driven solely by `F10_NEGATIVE_CONTROL`.
**G1 was not appended to Gate 8**, per frozen authority.

## 6. Structural acceptance

**`STRUCTURAL_ACCEPTED` = 25 of 240 cases** (gates 1–8 all passed).

By family: F18 ×7, F10 ×6, F09 ×4, F04 ×2, F02 ×1, F05 ×1, F07 ×1, F08 ×1, F12 ×1, F19 ×1.

This is an **acceptance count, not an endpoint rate**. It has no frozen denominator of 240 and
must never be reported as one.

## 7. F5 — role verification

Rung keys ever emitted across all 240 sealed records:
`{F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT, F7_INFLUENCE_DROP, F10_NEGATIVE_CONTROL}`

**`F5_SCAFFOLD_HOLDOUT` appears in zero records.** Confirmed superseded exactly as A3.5 §6.9.2
requires. It is also absent from the `FalsificationRung` enum's hard set.

## 8. F9 — secondary, non-gating

| Quantity | Value |
|---|---|
| Present in `falsification_results` | **No** (correctly excluded from the rung mapping) |
| `f9_stress_test_result` over all 240 | `null` 214, `PASS` 26 |
| Among the 26 cases reaching Gate 8 | `PASS` 26, `FAIL` 0 |
| `f9_acceptance_calibration_status` | `NOT_PROVEN_FOR_HARD_GATE` (uniform, all 240) |

F9 was computed for exactly the 26 cases reaching Gate 8 and `null` elsewhere — precisely the
frozen behaviour. It affected no acceptance decision.

**Binding drafting guard (A3.5 §6.9.4): this 26/26 PASS may NOT be cited in any report or paper
as evidence of validated robustness.** It is recorded here only as the mandated secondary
observable.

## 9. Mandatory execution-failure disclosure (A3.5 §8.2)

| Endpoint | Execution-failure-poisoned cases |
|---|---|
| G1 | **0** of 164 |
| G2 | **0** of 144 |
| G3 | **0** of 36 |

Seed statuses across all 7,200: `COMPLETED_WITH_CANDIDATES` 7,136, `COMPLETED_NO_CANDIDATE` 64,
`EXECUTION_FAILURE` **0**. No case was poisoned; every UNEVALUABLE arose from A1 adequacy or a
missing candidate, not from execution failure.

## 10. Independent bottom line

| Endpoint | Result | Gate | Verdict |
|---|---|---|---|
| **G1** | ≤ 67/164, Wilson lower ≤ 0.336234 | ≥ 0.70 | **FAIL** (determinate) |
| **G2** | 4/144, Wilson lower 0.010854 | ≥ 0.70 | **FAIL** |
| **G3** | 26/36 violations, Wilson upper 0.841518 | ≤ 0.15 | **FAIL** |

**All three primary endpoints fail under the frozen contract.** The dominant driver is not any
gate subtlety but A1 adequacy: 154 of 240 cases terminate at `a1_adequacy`, and 97 of the 164 G1
cases are `BOUNDARY_LIMITED`.

---

**INDEPENDENT HELD-OUT SCORING SEALED**
