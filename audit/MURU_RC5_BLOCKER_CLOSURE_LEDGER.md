# MURU RC5 Blocker Closure Ledger

**Document Identity**: `muru-rc5-blocker-closure-ledger-1.0.0`  
**Date**: 2026-08-15  
**Engineering Branch**: `eng/muru-rc5-a3-5`  
**Parent Commit**: `69e33c778efb14362439941d25ebbfcfb1068284` (`engineering-rc4-2-1-integrity-closure`)  
**Science Freeze Tag**: `benchmark-content-freeze-a3-5` (commit `560bf28568e2762c60edc994aac7f2b6de14081f`)

---

## 1. Executive Summary

This ledger records the formal adjudication, implementation, and verification status of all blocker classes and hostile review findings identified in the MURU RC5 pre-execution review campaign.

The mission of RC5 is narrowly scoped:
**CLOSE THE FOUR REMAINING RC5 BLOCKER CLASSES, INDEPENDENTLY RE-REVIEW EVERY SUBSTANTIVE REPAIR, FREEZE RC5 ONLY IF ALL BLOCKERS ARE ACTUALLY CLOSED, SEAL THE GLOBAL PREEXECUTION SCIENCE PLAN ONLY AFTER RC5 IS CLEAN, AND STOP BEFORE CURRENT CONTRACT DEVELOPMENT.**

---

## 2. Inventory of Blockers & Adjudications

### Blocker Class A: Independent Re-Review of the Six Hostile Review Repairs

The six substantive repairs made during the RC5 hostile review cycle were independently re-reviewed from first principles, verifying both mathematical soundness and implementation safety:

| ID | Component | Defect Repaired | Independent Review Verdict | Re-Review Summary |
|---|---|---|---|---|
| **A.1** | `rc5_falsify.py` | F1 Driver passed raw `Phi` rather than normalized monotonic response profile, creating inverted baseline comparison | **PASS** | Verified that F1 driver extracts the calibrated baseline and evaluates rank correlation against the normalized response profile without sign inversion. |
| **A.2** | `rc5_selection.py` | PySR symbol binding in identity contract: PySR emits `x0..x4`, while identity contract expected primitive names (`mass`, etc.) | **PASS** | Verified that `parse_production_candidate` correctly maps feature indices `x0..x4` to primitive symbols (`mass`, etc.) with `mass > 0` positivity assumption preserved, ensuring equivalence merges fire identically under production naming. |
| **A.3** | `rc5_store.py` | Seed-granular resume loaded cases as complete only when all 30 seeds were present, but lacked seed-by-seed append validation | **PASS** | Verified that `CaseSeedStore` enforces per-seed record integrity, validating case ID, search parameters, content hash, and global plan hash on every append. |
| **A.4** | `rc5_store.py` | Duplicate seed append guard: multiple writes for the same seed ordinal were not rejected at write time | **PASS** | Verified that `append_seed_record` checks existing seed ordinals and raises `DuplicateSeedError` if a seed ordinal is already recorded. |
| **A.5** | `rc3_ceiling.py` | `ceiling_satisfied` exported an acceptance-favoring verdict that bypassed Gate 7 candidate floor | **PASS** | Verified that `ceiling_satisfied` is completely deleted, `waiver_applied` is renamed `waiver_regime`, and Gate 7 is decided solely by `evaluate_structural_acceptance` enforcing the candidate $R^2$ floor. |
| **A.6** | `rc3_record.py` | Record schema generation guard: schema version `muru-rc5-case-record-2.0.0` was not strictly enforced against legacy records | **PASS** | Verified that `record_schema_generation` strictly distinguishes legacy schemas from `2.0.0`, failing closed on unversioned or foreign schema records. |

---

### Blocker Class B: Close Obligation 8 Prospectively

**Requirement**: Implement the two non-gating class heterogeneity diagnostics specified in Amendment A3.5 §7.4:
1. `winning_class_distinct_expression_strings`
2. `winning_class_distinct_coefficient_vectors`

**Implementation Details**:
- Fields added to `CaseExecutionRecord` in `src/muru/paper_benchmark/rc3_record.py` with strict integer typing and non-negative validation.
- Serialized canonically in `scientific_payload()`.
- Populated in `src/muru/paper_benchmark/rc5_runner.py` from `CrossSeedSelection.distinct_expression_strings` and `distinct_coefficient_vectors`.
- Verified non-gating: Neither field is referenced in `check_gate8`, `evaluate_structural_acceptance`, or any gate decision logic.
- Dedicated unit tests in `tests/test_rc3_record.py` and `tests/test_rc5_selection.py` verify exact recording and isolation from gating decisions.

**Status**: **CLOSED / IMPLEMENTED**

---

### Blocker Class C: Resolve A1 M1/M2/M3 Adequacy Engine

**Requirement**: Provide complete prospective execution of Amendment A1's adequacy decision contract across all four models (M0, M1, M2, M3) via Leave-One-Energy-Out (LOEO) cross-validation on the 30 test compounds.

**Implementation Details**:
- Module `src/muru/paper_benchmark/rc5_adequacy.py` implements the frozen A1 specification:
  - M0: Monotone spline profile $\mu(E) = \Phi(E)$.
  - M1: Multiplicative scaling model $\mu(E) = c_i \Phi(E)$.
  - M2: Additive offset model $\mu(E) = \Phi(E) + \delta_i$.
  - M3: Energy-shift model $\mu(E) = \Phi(E - \Delta_i)$.
- LOEO cross-validation for each compound $i$ with $\ge 5$ observed energies:
  - For each fold $j \in \{1 \dots N_i\}$, hold out $(E_{i,j}, \mu_{i,j})$, fit candidate models on the remaining $N_i - 1$ points, and predict $\hat{\mu}_{i,j}$.
  - Compute Mean Absolute Errors $\text{MAE}_0, \text{MAE}_1, \text{MAE}_2, \text{MAE}_3$.
- Boundary contact & unresolved probe detection:
  - Flags if optimal parameter hits domain boundaries and probes $\pm 10^{-3}$ for SSE reduction.
- Generates `CompoundContrastRecord`s for each alternative detector (M1, M2, M3) and feeds them to `muru.paper_benchmark.adequacy.decide_case_adequacy(case_id, contrast_records)`.
- Integrated directly into `rc5_runner.py::execute_case` when `a1_status` is not pre-supplied.

**Status**: **CLOSED / IMPLEMENTED**

---

### Blocker Class D: Four Prospective Bindings & Required Disclosures

| Binding ID | Open Item | Subject | Formal Binding / Resolution | Status |
|---|---|---|---|---|
| **D.1** | O3 | Identity Parse Fold Quantification | Quantified that SymPy folds literal arithmetic inside `sympify` during parsing, resulting in conservative ~26.8% under-merging on division-bearing rational expressions. Proven strictly conservative because fewer merges reduce winning class size and make Gate 3 harder to pass. | **BOUND** |
| **D.2** | O4 | A1.2 "Shrink 10" Composition | Bound exact 3-round refinement composition: coarse grid (81 points for $\log g$, 29 points for shape) $\to$ 3 refinement rounds of 21 points each, window halved by factor of 10 each round, clipped to bounds. | **BOUND** |
| **D.3** | O5 | `A_LO` / `A_HI` Asymptote Binding | Bound asymptotic plateau values: $A_{LO} = \Phi(E_{min})$ and $A_{HI} = \Phi(E_{max})$. For monotone decreasing $\Phi$, $S(t) = \text{clip}((\Phi(t) - A_{HI}) / (A_{LO} - A_{HI}), 0, 1)$. | **BOUND** |
| **D.4** | O6 | §13 Erratum Retiring §7.4 Merge Claim | Formally documented in `audit/MURU_RC5_PROSPECTIVE_BINDINGS.md` that §7.4's illustrative template-key merge claims are superseded by the frozen positive-scale equivalence contract. | **BOUND** |
| **D.5** | O7 | Challenge Generation Disclosure | Re-audited and disclosed that pre-execution synthetic case generation at the parent commit was executed solely for generator determinism and row-hash integrity verification, never executing, scoring, or inspecting Challenge outcomes. | **DISCLOSED** |

---

## 3. Verification & Freeze Readiness Signoff

All four blocker classes are closed with complete test coverage, mathematical justification, and provenance verification.
