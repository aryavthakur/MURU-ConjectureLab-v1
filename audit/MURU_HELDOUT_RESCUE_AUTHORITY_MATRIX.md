# MURU Held-out Rescue — Frozen Authority Matrix

**Phase A artifact. Reconstructed before any Held-out scientific outcome was inspected.**

Audit worktree: `audit/muru-heldout-forensic-rescue`
Rooted at: `engineering-rc5-1-heldout-authorization` = `8d87143d4280602323aa33ee0b5481aaef0fb4a8`
Parent: `7cdd5a6b74b1051935ad0eb86c7d8770cd725236` (`engineering-rc5-a3-5`)
Science authority: `benchmark-content-freeze-a3-6` = `327b55536b7d6ee8b8693091fa7180491e2c0a38`
Prior science freeze: `benchmark-content-freeze-a3-5` = `560bf28568e2762c60edc994aac7f2b6de14081f`
Tree state at reconstruction: clean.

## 0. Authorization-delta verification (independent)

`git diff 7cdd5a6b 8d87143d` touches 8 files. The only non-test, non-audit source change is
`src/muru/paper_benchmark/rc5_authorization.py`, whose sole semantic edit is:

```
-AUTHORISED_PARTITIONS = frozenset({"development"})
+AUTHORISED_PARTITIONS = frozenset({"development", "held_out"})
```

No endpoint, gate, falsification, scoring, registry, selection, or manifest module is modified.
**The A3.6 / RC5.1 delta is authorization-only. Verified, not assumed.**

A3.6 §A3.6.5 independently binds "zero scientific changes" and enumerates NO-change bindings for
Gate 7, Gate 8, F5, F9, G1, G2, G3, and all denominators. This corroborates the code-level finding.

## 1. Partition topology

| Quantity | Value | Source |
|---|---|---|
| Held-out total cases | **240** | `registry.iter_case_ids("held_out")`, 20 families × 12 replicates |
| Seeds per case | 30 | `STABILITY_DENOMINATOR` |
| Total searches | 7,200 | 240 × 30 |

**240 is the case population, not any endpoint denominator.** No frozen endpoint uses 240.

## 2. Primary endpoints

`registry.ENDPOINTS` defines exactly three primary endpoints. Denominators are computed by
`registry.endpoint_case_count(name) = sum(family.held_out_cases_for(name))` — held-out-specific
by construction.

| Endpoint | Registry name | Role | **Denominator** | Gate rule |
|---|---|---|---|---|
| **G1** | `scalar_competence` | `primary_scalar` | **164** | Wilson lower 95% ≥ **0.70** |
| **G2** | `family_recovery` | `primary_symbolic` | **144** | Wilson lower 95% ≥ **0.70** |
| **G3** | `principal_structural_safety` | `primary_safety` | **36** | Wilson upper 95% ≤ **0.15** |

164 + 144 + 36 = 344 ≠ 240. Endpoints **overlap** (a case may serve G1 and G2), and families
F06, F13, F14, F15, F16 carry **no primary endpoint at all** (0 in every column).
Any construction that scores an endpoint over all 240 case records is therefore
definitionally wrong.

### 2.1 Per-family held-out endpoint applicability

| Family | Held-out cases | G1 | G2 | G3 |
|---|---|---|---|---|
| F01 | 12 | 12 | 12 | 0 |
| F02 | 12 | 12 | 12 | 0 |
| F03 | 12 | 12 | 12 | 0 |
| F04 | 12 | 12 | 12 | 0 |
| F05 | 12 | 12 | 12 | 0 |
| F06 | 12 | 0 | 0 | 0 |
| F07 | 12 | 12 | 0 | **12** |
| F08 | 12 | 12 | 12 | 0 |
| F09 | 12 | 12 | 12 | 0 |
| F10 | 12 | 12 | 12 | 0 |
| F11 | 12 | 12 | 12 | 0 |
| F12 | 12 | 12 | 12 | 0 |
| F13 | 12 | 0 | 0 | 0 |
| F14 | 12 | 0 | 0 | 0 |
| F15 | 12 | 0 | 0 | 0 |
| F16 | 12 | 0 | 0 | 0 |
| F17 | 12 | 12 | 12 | 0 |
| F18 | 12 | 12 | 12 | 0 |
| F19 | 12 | 8 | 0 | **12** |
| F20 | 12 | 0 | 0 | **12** |
| **Total** | **240** | **164** | **144** | **36** |

G3 population = F07 (12) + F19 (12) + F20 (12) = 36, matching A3.5 §8.3 and `g3_contract` docstring.

## 3. G1 — scalar competence

- **Authority**: A3.5 §5.1/§5.2 (frozen content-freeze text, blob `80f20e2f`); `rc5_g1_bridge.py`.
- **Population**: the 164 held-out cases with `scalar_competence` applicability.
- **Per-case success predicate** (`CaseG1.scalar_competent`), all three conjuncts:
  1. `g_spearman >= 0.80` (Spearman of fold-local `g` vs true `log g`, 30 test compounds)
  2. `trajectory_mae <= 0.80 * per_energy_mean_mae` (skill score vs training-only per-energy-mean baseline)
  3. `m0_accepted` (A1 adequacy ladder does not reject M0)
- **Estimator**: A1's M0 under **within-compound leave-one-energy-out** (A1.3), fitted with
  A1.2's frozen protocol (`log_g ∈ [-2,2]`, 81-point grid, 3×21 refinement, shrink 10).
  **Not** the PySR expression; **not** `estimate._best_log_g`.
- **Denominator type**: **fixed** (164). `score_g1` raises if `len(outcomes) != 164`.
- **UNEVALUABLE**: **no credit**, remains in the 164 denominator (A3.5 §8.2).
- **EXECUTION_FAILURE**: any one of 30 seeds failing ⇒ whole case UNEVALUABLE ⇒ no credit.
- **Primary / gating**: primary, gating.
- **Mandatory disclosure**: execution-failure-poisoned count must be reported per endpoint (§8.2).

## 4. G2 — family recovery

- **Authority**: `g2_contract.evaluate_g2_event`; `rc3_scoring.score_g2` (type-checking wrapper).
- **Population**: the 144 held-out cases with `family_recovery` applicability.
- **Per-case event**:
  - `SUPPORT_UNRESOLVED` ⇒ `UNEVALUABLE`
  - `FAMILY_UNRESOLVED` or `FAMILY_AMBIGUOUS` ⇒ `UNEVALUABLE`
  - `support_status == MATCH AND family_status == MATCH` ⇒ `SUCCESS`
  - otherwise ⇒ `FAILURE`
- **Denominator type**: **fixed** (144), explicitly "never `len(events)` filtered by evaluability,
  and never a recomputed evaluable count" (`rc3_scoring.py`).
- **UNEVALUABLE**: **no credit** — non-success within the fixed 144 (A3.5 §8.2).
- **Gate**: `wilson_lower_95(successes, 144) >= 0.70`.
- **Primary / gating**: primary, gating.

## 5. G3 — principal structural safety

- **Authority**: `g3_contract.classify_g3_event` + `rc3_scoring.score_g3` are the **sole** G3
  authority (A3.5 §8.3, hard binding).
- **`analysis.classify_negative_control` MUST NOT be used to score G3.** It disagrees on 20 of
  36 opportunities (F07 ×12, F19A ×4, F19B ×4) and drifts in the **permissive** direction,
  granting safety credit to UNEVALUABLE cases.
- **Population**: 36 = F07 (12) + F19 (12) + F20 (12).
- **Scoring**: violations = events in `{UNSAFE, VIOLATION}`; counted as 1.
- **UNEVALUABLE ⇒ VIOLATION** (conservative), remains in denominator 36.
- **Denominator type**: **fixed** (36); `score_g3` raises on length mismatch and on non-`G3Event`
  elements (a bare string would otherwise score as SAFE — permissive drift).
- **Gate**: `wilson_upper_95(violations, 36) <= 0.15`.
- **Primary / gating**: primary, gating. **Direction is inverted** — low is good.

## 6. Gate 7 — the ceiling gate

**Gate 7 is NOT a falsification cascade and NOT related to `F7_INFLUENCE_DROP`.**
A3.5 §6.9.3 states this explicitly: "Gate 7 here means the ceiling comparison at position 7 of
the ordered structural-acceptance predicate, never `F7_INFLUENCE_DROP` … The two share a digit
by coincidence, not by relation."

Gate 7 is position 7 of an ordered, short-circuiting 8-gate predicate in
`structural_acceptance.evaluate_structural_acceptance`:

| # | Gate | Reject status |
|---|---|---|
| 1 | A1 adequacy prerequisite | `REJECTED_A1_INADEQUATE` / `UNEVALUABLE` |
| — | candidate is None | `UNEVALUABLE` (`no_candidate`) |
| 2 | `valid_r2 > null_threshold[min(complexity,20)]` | `REJECTED_BELOW_NULL` |
| 3 | stability `selection_fraction >= STABILITY_GATE/30` | `REJECTED_UNSTABLE` |
| 4 | `complexity <= MAX_COMPLEXITY` | `REJECTED_OVERCOMPLEX` |
| 5 | `invalid_fraction <= MAX_INVALID_FRACTION` | `REJECTED_INVALID_FRACTION` |
| 6 | effective support non-empty | `REJECTED_EMPTY_SUPPORT` |
| **7** | **ceiling (below)** | `REJECTED_CEILING` |
| 8 | four hard rungs, fail-closed | `REJECTED_FALSIFICATION` |

**Frozen Gate 7 predicate (A3.5 §6.9.3, amended):**

```
ceiling_pass   = ceiling_fraction >= CEILING_FRACTION_GATE      # 0.80
floor_pass     = candidate_test_r2 > null_threshold[min(complexity, 20)]
ceiling_waiver = (ceiling_r2 < CEILING_WAIVER_THRESHOLD) and floor_pass   # 0.05
Gate7_PASS     = ceiling_pass or ceiling_waiver
```

- `threshold` is the **same value already looked up at Gate 2** — same table, same index.
- Gates 1–6 must have passed to reach Gate 7 (short-circuit order).
- The null ceiling enters via `ceiling_fraction = candidate_r2 / ceiling_r2` from
  `rc3_ceiling.estimate_ceiling`.
- **Low-ceiling waiver regime**: when `ceiling_r2 < 0.05` the ceiling ratio is uninformative, so
  the waiver substitutes a raw candidate R² floor — this is F5's folded-in content.
- **Candidate R² floor**: `candidate_test_r2 > null_threshold[...]`, appearing **exactly once**
  in the whole predicate, inside the waiver branch only.
- Complexity and invalid fraction are **separate earlier gates** (4 and 5), not part of Gate 7.

## 7. Gate 8 — hard falsification

```
REQUIRED_HARD_GATES = {F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT,
                       F7_INFLUENCE_DROP, F10_NEGATIVE_CONTROL}
```

**Exactly four rungs. Not six. Not five.**

```python
def check_gate8(results):
    for rung in REQUIRED_HARD_GATES:
        result = results.get(rung)
        if result is None:   return False   # missing: fail closed
        if result != PASS:   return False   # FAIL and stray NOT_APPLICABLE alike
    return True
```

- The predicate is `result != PASS`, **not** `result == FAIL`. That difference *is* the A3.5 repair.
- `EXECUTION_FAILURE` resolves to `FAIL` **before** entering the mapping; never reaches `check_gate8`.
- `NOT_APPLICABLE` is forbidden on emission; if it occurs by defect it is treated as non-passing.
- **`UNEVALUABLE` cases never reach Gate 8 at all.** Gate 8 grants no safety credit to a case that
  never produced rung results.
- Module-import guard: `REQUIRED_HARD_GATES & SECONDARY_REPORTED_RUNGS` raises `ImportError`,
  structurally forbidding F9 from ever entering the hard set.

**Relationship between Gate 7, Gate 8, and G1 — authoritative:**
Gate 8 is **position 8 of the structural-acceptance predicate**. Gate 8 ≠ Gate 7 + G1.
**G1 is an endpoint, not a gate**, and appears nowhere in `evaluate_structural_acceptance`.
A case is `STRUCTURAL_ACCEPTED` iff gates 1–8 all pass. G1 is scored independently over its own
164-case population by `rc5_g1_bridge.score_g1`. Appending G1 to Gate 8 is unauthorized.

## 8. F5 — superseded

- **Final frozen role after A3.5**: `F5_SCAFFOLD_HOLDOUT` is **removed** from
  `FalsificationRung` / `REQUIRED_HARD_GATES`. "It is never again independently evaluated as a
  Gate-8 rung" (§6.9.2).
- Its one non-redundant contribution — the raw `candidate_test_r2` floor — is folded into
  **Gate 7's waiver branch only**, not into the whole of Gate 7.
- Rationale: F7's exhaustive 20-fold leave-one-scaffold-out floor ordinarily implies F5's floor,
  except in the low-signal waiver regime where the implication is not formally guaranteed.
- **Disclosed residual gap**: `{ceiling_pass = True, candidate_test_r2 <= null_threshold}` is
  reachable and is accepted, not hidden (§6.9.3).
- **F5 is NOT independently hard-gating.** Any implementation treating it as a Gate 8 rung is wrong.

## 9. F9 — secondary, non-gating

- **Final frozen role**: `F9_ENERGY_SUBSET` is **computed for every case reaching Gate 8**,
  per §6.5's leave-one-energy-out construction, and recorded as two fields:
  - `f9_stress_test_result ∈ {PASS, FAIL}`
  - `f9_stress_test_metric` — raw `min_k(R2_k)` over six leave-one-energy-out folds
- **Neither field is read by `REQUIRED_HARD_GATES` or `check_gate8`.**
  `f9_stress_test_result` cannot, alone or in combination, produce `REJECTED_FALSIFICATION`.
- **Calibration status: `NOT_PROVEN_FOR_HARD_GATE`** — F9 is the only rung that re-estimates the
  `g` pipeline, a strictly larger perturbation than the affine refit §6.7's conservatism proof
  covers. Bias direction unproven in **either** direction.
- **Binding drafting guard**: no report or paper claim may cite `f9_stress_test_result`'s
  PASS/FAIL as evidence of validated robustness.
- **F9 is NOT gating.** Promotion requires a future amendment with a prospectively frozen,
  F9-specific calibration against a never-before-drawn population.

## 10. Case scientific-failure semantics (A3.5 §8.2)

If **any one** of a case's 30 scientific search seeds ends in `EXECUTION_FAILURE`, the
**whole case is `UNEVALUABLE`**.

- No replacement seed (the derivation admits no attempt index).
- No 29/30 denominator — `STABILITY_DENOMINATOR = 30` is global, never case-conditional.
- No retry erases a prior failure; the record is append-only.

| Endpoint | UNEVALUABLE treatment | Denominator |
|---|---|---|
| G1 | no credit, not competent | stays in fixed 164 |
| G2 | no credit, non-success | stays in fixed 144 |
| G3 | counts as a **VIOLATION** | stays in fixed 36 |

## 11. Summary of falsification-rung roles

| Rung | Role after A3.5 | Gating? |
|---|---|---|
| F1_REPRODUCIBILITY | hard gate | **yes** |
| F4_COMPOUND_HOLDOUT | hard gate | **yes** |
| F5_SCAFFOLD_HOLDOUT | superseded; floor folded into Gate 7 waiver branch | **no** |
| F7_INFLUENCE_DROP | hard gate | **yes** |
| F9_ENERGY_SUBSET | secondary reported stress test, NOT_PROVEN_FOR_HARD_GATE | **no** |
| F10_NEGATIVE_CONTROL | hard gate | **yes** |

## 12. Ambiguities remaining

**None material to scoring.** Every quantity required for Phase C resolved to a single frozen
definition, corroborated independently by (a) the A3.5 amendment text, (b) the RC5.1 engineering
source, and (c) A3.6's zero-scientific-change binding. The three sources agree.

---

**FROZEN HELD-OUT RESCUE AUTHORITY RECONSTRUCTION COMPLETE**

After this point the authority interpretation is not to be altered on account of any observed
Held-out result.
