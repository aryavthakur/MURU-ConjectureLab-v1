# MURU ConjectureLab v1 Root-Cause Ranking

**Status:** DIAGNOSIS ONLY. Remediation classes are named, not designed. No v2 implementation is proposed here.

Machine-readable twin: `MURU_V1_ROOT_CAUSE_RANKING.json`
Full evidence: `MURU_V1_FAILURE_DECOMPOSITION.md` / `.json` and the three taxonomy CSVs.

**Ordering criterion:** endpoint-verdict leverage first, then affected case count, then confidence of attribution.

---

## Summary table

| Rank | Root cause | Class | Cases | Verdict leverage |
|---|---|---|---|---|
| 1 | A1 unresolved-boundary rule has no magnitude floor | MODEL_ADEQUACY_LIMITATION | G1 97, G3 26, all 154 | **flips G1 and G3 from FAIL to PASS** |
| 2 | A1 detectors have no demonstrated power | MODEL_ADEQUACY_LIMITATION | validity over 240, 48 positive controls | none on counts; voids the evidential content of 67 verdicts |
| 3 | Within-seed retention discards the accurate candidate | SELECTION_FAILURE | G2 69 | bounded; G2 still fails |
| 4 | Search never reaches the descriptor structure | SEARCH_GENERATION_FAILURE | G2 57 | sets G2's ceiling |
| 5 | Family classifier coverage | CLASSIFICATION_SCORING_FAILURE | G2 37 | interpretation only |
| 6 | Grammar cannot express the exponential family | GRAMMAR_REPRESENTABILITY | G2 12 | caps G2 at 132/144 |
| 7 | Cross-seed identity is finer than the endpoint | CANONICALIZATION_EQUIVALENCE_FAILURE | G2 2 | negligible alone |
| 8 | Negative controls behaved as designed | EXPECTED_NEGATIVE_CONTROL | G3 10 | not a defect |

**The single most consequential fact in this ranking: RC1 alone flips two of the three primary endpoints from FAIL to PASS, and G2 remains failing under every counterfactual tested, including a perfect post-search selector.**

---

## RC1. A1 unresolved-boundary rule has no magnitude floor

**Class:** MODEL_ADEQUACY_LIMITATION
**Affected:** 97 of 164 G1 cases, 26 of 36 G3 cases, 154 of 240 cases overall

### Statement

The A1 boundary test declares a compound fit `unresolved` when a parameter sits on a bound and a single outward probe improves the sum of squared residuals by any amount at all (`obj < best_obj - 1e-12`). There is no relative-magnitude floor, no scale normalisation and no significance test. Enough compounds are removed from the evaluable pool that the M3 contrast falls below its 24-of-30 minimum, and the case becomes `BOUNDARY_LIMITED`. From there, `structural_acceptance` gate 1 maps every A1 indeterminate state to `UNEVALUABLE`, and `g3_contract` charges `UNEVALUABLE` as a G3 violation by design.

### Evidence

- 154 of 240 cases are `BOUNDARY_LIMITED`; 0 are `INSUFFICIENT_DATA`, `NUMERICAL_FAILURE`, `MODEL_FIT_FAILURE`, `TIMEOUT` or `CONTRACT_FAILURE`.
- Every one of the 154 is blocked by M3: 127 by M3 alone, 27 by M2 and M3. M1 never blocks. The shared M0 fit is unresolved on zero compounds anywhere in the partition.
- 7,399 of the 8,816 recorded bound contacts (84 percent) are the M3 low-energy plateau pinned at its `MU_CEIL` upper bound.
- The median relative sum-of-squares improvement that triggered the rule is **1.3 percent**. The largest anywhere in the partition is 28.9 percent.
- Raising the trigger to a 10 percent relative floor makes all 240 cases `M0_NOT_REJECTED`; the 0.0 control arm reproduces the frozen 86/154 split exactly.
- Case geometry is identical across all 240 cases and no compound anywhere falls below the 5-energy minimum, so data sparsity is excluded. The strongest predictor of M3 evaluability is `mu_max` at r = -0.55: how close the low-energy response saturates toward the fixed ceiling.

### Endpoint leverage

| Endpoint | Official v1 | If RC1 alone were resolved |
|---|---|---|
| G1 | 67/164, Wilson lower 0.336, FAIL | 154/164, Wilson lower **0.891**, passes 0.70 |
| G3 | 26/36 violations, Wilson upper 0.842, FAIL | 0/36 violations, Wilson upper **0.096**, passes 0.15 |

### Remediation class

Adequacy decision-rule specification. Give the boundary test a scale-aware magnitude floor or a proper identifiability criterion, and separate "the fit sits at a bound" from "the contrast cannot decide".

### Risks

- Any floor is a new free parameter and must be calibrated prospectively, never chosen against Held-out.
- Loosening evaluability admits cases the current rule conservatively refused, so G3's safety direction changes and must be re-argued from scratch rather than inherited.
- `MU_CEIL` and `MIN_VERTICAL_AMPLITUDE` were inherited from the generator's response clip rather than derived from an identifiability argument. The admissible ranges themselves need justification before any floor is tuned, or the fix relocates the artifact instead of removing it.

### Confidence

**HIGH.** The mechanism was reproduced fit by fit, and the counterfactual's control arm reproduces the frozen result exactly.

---

## RC2. A1 detectors have no demonstrated power

**Class:** MODEL_ADEQUACY_LIMITATION
**Affected:** validity scope over all 240 cases; 48 dedicated positive controls

### Statement

No A1 detector fired on any of the 240 Held-out cases, including the 48 whose planted truth is the deviation the detector exists to catch. The 20-of-30 practical-win threshold was never approached.

### Evidence

- 0 of 240 cases reached any `M0_REJECTED_*` state.
- F13 (M1 truth), F14 (M2 truth), F15 (M3 truth) and F16 (M1+M2+M3 truth) produced 0 detections across 48 cases.
- Maximum practical wins ever observed: M1 18, M2 18, M3 15, against a required 20.
- **Independent of RC1.** In no case did a detector reach 20 wins while being evaluability-blocked, and at the 10 percent counterfactual floor, where every case is evaluable, the firing count is still 0.

### Endpoint leverage

None on any v1 count. This is a validity finding: it removes the evidential content of the 67 `M0_NOT_REJECTED` verdicts. A1 could not have rejected M0 on this partition regardless of the data, so "M0 not rejected" carries no discriminating information. As executed, A1 is an evaluability filter, not a model-adequacy test.

### Remediation class

Adequacy test power. Re-derive the practical-win ratio, the required win count and the leave-one-energy-out loss so the detector has demonstrated sensitivity on its own positive controls before it gates anything.

### Risks

- Raising sensitivity raises the false-rejection rate on true-M0 families, which directly suppresses G1. RC1 and RC2 pull in opposite directions and cannot be tuned independently.
- The positive controls are the only power evidence available and they are now spent as diagnostic evidence. A v2 power argument needs an independent construction.

### Confidence

**HIGH.** Direct enumeration over all 240 cases and all three detectors.

---

## RC3. Within-seed retention discards the accurate candidate

**Class:** SELECTION_FAILURE
**Affected:** 69 of 144 G2 cases

### Statement

Each seed retains `argmax(score)`, PySR's marginal-return-per-unit-complexity heuristic, and only that one candidate is persisted. When seeds disagreed, the seeds that retained a G2-correct expression carry both materially higher accuracy and higher complexity: the signature of a parsimony rule discarding the correct answer.

### Evidence

- A G2-correct candidate reached cross-seed selection in 75 of 144 cases but was the modal answer in essentially none.
- Median correct-seed share is 1 of 30. Maximum anywhere is 16 of 30. **No case reached the 20-of-30 stability gate with a correct candidate.**
- In **70 of 75** paired cases the correct retained candidate is both more accurate and more complex than the incorrect ones.
- Median within-case accuracy gap is **+0.121 `valid_r2`**, positive in 98.7 percent of paired cases, at a median **+3.4** complexity.
- 2,450 of the 4,318 actual retained candidates (56.7 percent) are mass-only `mass_power` expressions, and `mass_power` is the modal answer in 92 of 144 cases.

### Endpoint leverage

Bounded. Even a perfect post-search selector over the persisted candidates yields only 75/144, Wilson lower **0.440**, still far below the 0.70 gate. Fixing selection alone cannot make G2 pass.

### Remediation class

Search objective and retention policy. Retain more than one candidate per seed, and make retention accuracy-aware rather than purely parsimony-driven.

### Risks

- Retaining more candidates weakens the stability gate's meaning and inflates the effective multiple-comparison count.
- An accuracy-weighted rule biases toward overfit high-complexity expressions, which is exactly the failure mode the parsimony rule exists to prevent.
- The within-seed Pareto fronts were not persisted. This attribution rests on which candidate the rule kept across disagreeing seeds, not on what each front contained.

### Confidence

**MEDIUM-HIGH.** The paired within-case comparison is strong; the direct front-level evidence was never sealed.

---

## RC4. Search never reaches the descriptor structure

**Class:** SEARCH_GENERATION_FAILURE
**Affected:** 57 of 144 G2 cases

### Statement

In 57 representable cases no seed's retained candidate ever carried both the correct support and the correct family. The search collapses onto the mass-only term and never recovers the descriptor structure, completely so for the saturating family.

### Evidence

- F09 (`mass_saturating_descriptor`): **0 of 12** cases had any correct retained candidate across 360 searches.
- F03: 1 of 12. F02: 3 of 12.
- All 30 seeds of several F03 cases converged on a descriptor-only expression with no mass term at all.
- 2,450 of 4,318 retained candidates are mass-only.

### Endpoint leverage

Sets the ceiling on G2. These cases cannot be rescued by any selection, voting or canonicalization change.

### Remediation class

Search budget, operator set and objective design. Separately and independently: generator signal-to-noise, since the descriptor term's contribution to the scalar may be too small to be identifiable at the planted coefficient magnitudes.

### Risks

- Increasing budget or operator richness increases the false-structure rate, which G3 exists to punish. RC4 and G3 pull in opposite directions.
- If the descriptor contribution is genuinely below the identifiability floor at the planted coefficients, this is a benchmark-construction issue and no search change will fix it. That distinction was **not** resolvable from the sealed evidence and needs its own study.

### Confidence

**HIGH for the counts, MEDIUM for the mechanism.** The persisted evidence shows what was retained, not what was searched.

---

## RC5. Family classifier coverage

**Class:** CLASSIFICATION_SCORING_FAILURE
**Affected:** 37 of 144 G2 cases

### Statement

`classify_discovered_family` returns `None` for a third of all grammar-legal retained candidates. When the cross-seed winner is one of them, the case is scored `UNEVALUABLE` rather than as a wrong answer.

### Evidence

- **1,475 of the 4,318** actual retained candidates (34.2 percent) could not be labelled.
- Only 2 of the 4,320 seed slots produced no candidate at all and only 2 candidates failed to parse, so this is classifier coverage and not a parser or execution defect.
- All 37 G2 `UNEVALUABLE` cases carry `family_status = FAMILY_UNRESOLVED`.
- The classifier's family tests are pattern matches on simplified sympy trees, so nested or algebraically rearranged forms fall through to `None`.

### Endpoint leverage

Confounds interpretation rather than the verdict. Under the frozen predicate `UNEVALUABLE` and `FAILURE` are both non-successes, so relabelling all 37 would not move G2's numerator.

### Remediation class

Structural classification. Replace pattern matching on simplified trees with a canonical structural normal form, or with behavioural family identification.

### Risks

- A more permissive classifier can label a wrong expression with the truth family, converting `UNEVALUABLE` into false `SUCCESS` and inflating G2. This risk is in the direction that flatters the result.
- Classification is downstream of truth, so any change must preserve the truth-blind boundary of the acceptance predicate.

### Confidence

**HIGH.** Measured directly over all 4,320 candidates.

---

## RC6. Grammar cannot express the exponential family

**Class:** GRAMMAR_REPRESENTABILITY
**Affected:** 12 of 144 G2 cases

### Statement

The frozen grammar excludes `exp`, while F18's planted truth is `sqrt(mass) * exp(coefficient * descriptor / 3)` and the family classifier requires a literal `exp` node. Those 12 cases had a success probability of exactly zero before any search ran.

### Evidence

- `discovery/grammar.py` `UNARY_OPERATORS` omits `exp`, per DEVIATIONS_P3 D1.
- `g2_contract._contains_exp_of` requires an actual `sympy.exp` node in the simplified expression.
- F18 oracle recovery is 0 of 12 across 360 searches.
- 29 of 30 F18 seeds in a typical case retained a mass-only expression.

### Endpoint leverage

Caps G2 at 132 of 144 by construction. Removing it cannot by itself change the verdict.

### Remediation class

Benchmark and grammar alignment. Either admit `exp` to the grammar or remove the exponential family from the family-recovery population. The mismatch itself is the defect, and it is a governance defect as much as a technical one: a family was preregistered into an endpoint that the preregistered grammar could not express.

### Risks

- Admitting `exp` reintroduces the overflow pathologies DEVIATIONS_P3 D1 excluded it for.
- Removing the family shrinks the endpoint population and weakens the claim the endpoint was designed to support.

### Confidence

**HIGH.** A static property of the frozen grammar and the frozen classifier, confirmed empirically.

---

## RC7. Cross-seed identity is finer than the endpoint

**Class:** CANONICALIZATION_EQUIVALENCE_FAILURE
**Affected:** 2 of 144 G2 cases

### Statement

Cross-seed voting groups by `template_key` while G2 is scored on `(effective support, family)`. The voting relation is strictly finer than the scoring relation, so agreeing answers are split across classes. The effect is real but small.

### Evidence

- Median 11 identity classes per case against a median 3 label classes.
- Correct answers are split across a median of 5 identity classes but 1 label class.
- In 61 of 144 cases the correct answers occupy more than one identity class.
- Regrouping by the endpoint's own label recovers 2 cases and loses 3 others, for a net **3 of 144** against the frozen rule's 4.

### Endpoint leverage

Negligible on its own, and slightly negative when applied naively. It matters only after RC3 and RC4 are addressed, since no equivalence relation can help when the correct answer is a small minority.

### Remediation class

Equivalence-relation alignment between the voting layer and the scored endpoint.

### Risks

- Coarsening the voting relation merges genuinely different expressions and inflates the stability statistic, which is the k-inflating direction the identity contract was deliberately written to avoid.

### Confidence

**HIGH.** Both arms replayed over the same frozen evidence, with the control arm reproducing the seal exactly.

---

## RC8. Negative controls behaved as designed

**Class:** EXPECTED_NEGATIVE_CONTROL
**Affected:** 10 of 36 G3 cases

### Statement

Not a defect. Recorded so it is not mistaken for one. Where G3 was evaluable, the system was safe in every instance, and no unsafe structural claim was accepted anywhere in the partition.

### Evidence

- 10 of 10 evaluable G3 cases are SAFE.
- Only 2 of the 36 G3 cases were structurally accepted at all, both with mass-only support under variants where mass-only acceptance is permitted.
- An independent scan that bypasses the G3 classifiers entirely finds 0 accepted cases with non-mass support and 0 acceptances under F19C, F20A, F20B or F20C.
- Gate 8's `F10_NEGATIVE_CONTROL` rung failed exactly 1 of 26 cases, and that failure correctly blocked acceptance.

### Endpoint leverage

None. G3 fails only because `UNEVALUABLE` is charged as a violation, and every `UNEVALUABLE` traces to RC1.

### Remediation class

None required.

### Risks

- The safety evidence rests on 10 evaluable opportunities, far too few to support a safety claim in either direction. Resolving RC1 is what would make G3 informative.

### Confidence

**HIGH.** Verified twice by independent routes.

---

## Bottleneck reading

1. **Late falsification is not the bottleneck, and the evidence is stronger than "it mostly passes": it is barely exercised.** Only 27 of 240 cases ever reach Gate 7 and only 26 reach Gate 8, because 154 stop at A1 and 43 more at the stability gate. Gate 7 passes 26 of 27 and Gate 8 passes 25 of 26.

2. **G1 and G3 are one problem, not two.** Both fail entirely through A1 indeterminacy, and both would pass their gates if that one rule were corrected.

3. **G2 is a genuinely separate and harder problem.** It fails through representation, search generation and within-seed retention, in that causal order, and it remains far below its gate even under a perfect post-search selector. Nothing about fixing A1 helps it.

4. **RC1 and RC2 are coupled and must be addressed together.** RC1 says adequacy refuses to decide too often; RC2 says that when it does decide, it always decides the same way. Fixing either in isolation risks converting a systematic non-decision into a systematic wrong decision.

5. **The v1 evidence base is exhausted for two of these questions.** Whether F09-style cases are unsearchable or unidentifiable (RC4), and whether the retained-candidate pattern reflects the Pareto fronts (RC3), cannot be settled from the seal. Both need instrumentation that v1 did not persist.
