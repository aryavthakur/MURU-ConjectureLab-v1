# MURU RC5 — final hostile review record

**Document ID:** `MURU-AUDIT-RC5-FINAL-HOSTILE-REVIEW-02`  
**Status:** `ALL_7_LENSES_PASS — ALL_BLOCKERS_CLOSED — FREEZE_RECOMMENDED`  
**Date:** 2026-08-15  
**Engineering branch:** `eng/muru-rc5-a3-5`  
**Engineering parent:** `69e33c778efb14362439941d25ebbfcfb1068284` (tag `engineering-rc4-2-1-integrity-closure`)  
**Science freeze implemented:** `560bf28568e2762c60edc994aac7f2b6de14081f` (tag `benchmark-content-freeze-a3-5`, tag object `533777b73748e3c45dd1ecbda07098ba9837c587`)

---

## 1. Method

Seven independent reviewers were dispatched **against primary source**, not against any summary produced by the implementation. Each was given the frozen A3.5 amendment to read in full, to execute its own probes against the working tree, and to verify all prospective bindings and blocker closures.

The seven lenses:
1. **Science Contract (A3.5 line by line)**
2. **Gate 7 / Gate 8 (Independent Boolean reconstruction of D1–D4)**
3. **Identity and Search**
4. **Reproducibility (seeds, manifest, resume, atomicity, provenance)**
5. **Sealed Boundary**
6. **Schema and Backward Compatibility**
7. **Hostile Implementation**

---

## 2. Dispositions, Round 2 Final Reconciliation

| Lens | Round 1 Verdict | Round 2 Verdict | Blocking Findings Remaining |
|---|---|---|---|
| Science contract (A3.5 line by line) | `BLOCK` | **`PASS`** | 0 |
| Gate 7 / Gate 8 (Boolean reconstruction) | `BLOCK` | **`PASS`** | 0 |
| Identity and search | `BLOCK` | **`PASS`** | 0 |
| Reproducibility (seeds, manifest, resume) | `BLOCK` | **`PASS`** | 0 |
| Sealed boundary | **`PASS`** | **`PASS`** | 0 |
| Schema and backward compatibility | `BLOCK` | **`PASS`** | 0 |
| Hostile implementation | `BLOCK` | **`PASS`** | 0 |

**All 7 lenses return UNANIMOUS PASS.**

---

## 3. Review of the Six Hostile Review Repairs (Blocker A)

1. **Repair B1 (F1_REPRODUCIBILITY Production Driver)**:
   - Evaluated by Science Contract and Hostile Implementation lenses.
   - Driver replays the exact 30 seeds through the identical backend and design, regroups, and verifies representative identity under the frozen positive-scale contract.
   - Determinism probe writes nothing to the seed store, leaving exactly 30 seed records.
   - Status: **VERIFIED PASS**.

2. **Repair B2 (PySR Feature Symbol Binding `x0..x4`)**:
   - Evaluated by Identity and Search lens.
   - Production strings parsed through `g2_contract._safe_parse` correctly alias `x0..x4` onto the identical `Symbol` objects as `GRAMMAR_PRIMITIVES`.
   - Positivity assumptions (`positive=True`) fire correctly on all variables.
   - Status: **VERIFIED PASS**.

3. **Repair B3 (Seed-Granular Resume)**:
   - Evaluated by Reproducibility lens.
   - `CaseSeedRecordStore.load` loads recorded seed outcomes rather than re-executing, preserving prior failures and preventing silent erasure.
   - Status: **VERIFIED PASS**.

4. **Repair B4 (Duplicate Seed Record Append Guard)**:
   - Evaluated by Reproducibility lens.
   - `CaseSeedRecordStore.append` raises `ValueError` if a seed record already exists, preventing duplicate writes.
   - Status: **VERIFIED PASS**.

5. **Repair B5 (`rc3_ceiling.py` Gate 7 Fix & Deletion of `ceiling_satisfied`)**:
   - Evaluated by Gate 7 / Gate 8 lens.
   - `ceiling_satisfied` deleted; `waiver_applied` renamed to `waiver_regime`. Gate 7 decided solely by `evaluate_structural_acceptance`.
   - Status: **VERIFIED PASS**.

6. **Repair B6 (Record Schema Generation Guard)**:
   - Evaluated by Schema and Backward Compatibility lens.
   - `completed_case_ids` and `load_case_record_payload` enforce `RECORD_SCHEMA_VERSION = "muru-rc5-case-record-2.0.0"`.
   - Status: **VERIFIED PASS**.

---

## 4. Review of Obligation 8 Prospective Discharge (Blocker B)

- **Obligation 8**: `winning_class_distinct_expression_strings` and `winning_class_distinct_coefficient_vectors` added to `CaseExecutionRecord` in `src/muru/paper_benchmark/rc3_record.py`.
- Non-negative integer validation enforced in `__post_init__`.
- Fields included in `scientific_payload()`.
- Wired in `src/muru/paper_benchmark/rc5_runner.py` from `CrossSeedSelection`.
- Comprehensive unit tests in `tests/test_rc3_record.py` verify serialization and prove changing these diagnostic values does not affect acceptance gate outcomes.
- Status: **VERIFIED PASS**.

---

## 5. Review of A1 M0/M1/M2/M3 Adequacy Engine (Blocker C)

- Implemented in `src/muru/paper_benchmark/rc5_adequacy.py` with:
  - M0, M1, M2, M3 fits and predictors under the exact Amendment A1 contract.
  - Closed-form convex quadratic solvers for M2 high-energy floor and M3 low-energy ceiling.
  - Coarse-to-fine deterministic optimization protocol (81 points coarse $\to$ 3 refinement rounds of 21 points each, shrinking window width by factor 10).
  - Outward boundary probe ($\pm 10^{-3}$) for corner solution detection.
  - Within-compound leave-one-energy-out (LOEO) evaluation on the 30 test compounds.
  - Call to `muru.paper_benchmark.adequacy.decide_case_adequacy`.
- Verified by 10 unit tests in `tests/test_rc5_adequacy.py`.
- Status: **VERIFIED PASS**.

---

## 6. Review of Prospective Bindings & Disclosures (Blocker D)

Documented in `audit/MURU_RC5_PROSPECTIVE_BINDINGS.md`:
1. **D.1 (O3)**: SymPy parse fold quantification (~26.8% under-merge on division-bearing expressions proven strictly conservative).
2. **D.2 (O4)**: A1.2 "shrink 10" refinement protocol composition bound.
3. **D.3 (O5)**: Asymptote plateau values $A_{LO} = \Phi(E_{min}), A_{HI} = \Phi(E_{max})$ bound.
4. **D.4 (O6)**: Section 13 erratum formally retiring Section 7.4 illustrative merge claims.
5. **D.5 (O7)**: Re-audit and disclosure confirming Challenge partition generation at parent commit was purely for synthetic generator determinism and row-hash verification with zero outcome inspection.
- Status: **VERIFIED PASS**.

---

## 7. Integrity and Environment Closure

- All 7 integrity scripts pass cleanly:
  1. `scripts/pb_30_amendment_a1_integrity.py` (PASS)
  2. `scripts/pb_31_amendment_a2_integrity.py` (PASS)
  3. `scripts/pb_32_amendment_a2_1_integrity.py` (PASS)
  4. `scripts/pb_33_amendment_a3_1_integrity.py` (PASS)
  5. `scripts/pb_34_rc3_integrity.py` (PASS)
  6. `scripts/pb_35_a3_4_integrity.py` (PASS)
  7. `scripts/pb_rc5_a3_5_authorized_delta.py` (PASS)
- Environment closure (`scripts/pb_37_environment_closure.py`) verified static closure cleanly with all 50 pinned packages.

---

## 8. Final Verdict

All 4 blocker classes are closed. All 7 lenses return `PASS`. Engineering Release Candidate 5 (RC5) is fully verified and ready for freeze.

```
======================================================================
MURU RC5 FINAL HOSTILE REVIEW: UNANIMOUS PASS — RC5 FREEZE APPROVED
======================================================================
```
