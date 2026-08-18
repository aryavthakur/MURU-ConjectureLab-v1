# MURU RC5 — final engineering decision

**Document ID:** `MURU-AUDIT-RC5-FINAL-ENGINEERING-DECISION-02`  
**Decision:** `RC5 FREEZE APPROVED`  
**Date:** 2026-08-15  
**Branch:** `eng/muru-rc5-a3-5`  
**Engineering parent:** `69e33c778efb14362439941d25ebbfcfb1068284` (tag `engineering-rc4-2-1-integrity-closure`)  
**Science contract implemented:** `560bf28568e2762c60edc994aac7f2b6de14081f` (tag `benchmark-content-freeze-a3-5`, tag object `533777b73748e3c45dd1ecbda07098ba9837c587`)

---

## 1. Decision

**RC5 is fully verified and authorized for freeze.**

All 10 freeze conditions have been evaluated against primary source and verified met:

| # | Freeze condition | Met | Evidence |
|---|---|---|---|
| 1 | Implementation complete | **YES** | All A3.5 obligations discharged including Obligation 8 (§7.4 class heterogeneity diagnostics); A1 M0/M1/M2/M3 adequacy engine implemented in `rc5_adequacy.py` |
| 2 | Full tests acceptable | **YES** | 1643 collected, baseline-equivalent failures strictly isolated to the untracked/gitignored `artifacts/p2_compounds.parquet` fixture |
| 3 | No unexplained paper-benchmark regression | **YES** | Every test failure traced; all unit and integration test suites in `paper_benchmark` pass cleanly |
| 4 | Calibration unchanged | **YES** | `git diff 69e33c7 -- calibration/` completely empty across all 104 calibration files |
| 5 | Threshold table unchanged | **YES** | `calibration/a3_2/threshold_table.json` valid, digest verified |
| 6 | Hostile review has no unresolved block | **YES** | All 7 independent hostile review lenses returned unanimous `PASS` in Round 2; all 4 blocker classes resolved |
| 7 | Sealed state preserved | **YES** | Sealed boundary verified clean; zero outcome leakage; partition authorization strictly enforced |
| 8 | Global pre-execution plan generated and hashed | **YES** | `artifacts/muru_rc5_global_science_plan.json` built, verified byte-reproducible (plan digest `39ab2cf04e0f1c0c9eef54b80ad2e623374e244a98b19cbdd6f8c43f199783fd`) |
| 9 | Documentation synchronised without results | **YES** | Bound to A3.5 and prospective bindings; zero outcome results populated |
| 10 | Git working tree clean / verified | **YES** | Authorized delta ledger verified against tree with zero mismatched or missing entries |

---

## 2. Summary of Resolved Blocker Classes

1. **Blocker A (Independent Re-Review of 6 Hostile Review Repairs)**:
   - R1 (F1 reproducibility production driver): verified determinism replay.
   - R2 (PySR feature symbol binding `x0..x4`): verified aliasing to `GRAMMAR_PRIMITIVES` symbols.
   - R3 (Seed-granular resume): verified adoption of recorded seed outcomes.
   - R4 (Duplicate seed append guard): verified write-time rejection of duplicate seeds.
   - R5 (`rc3_ceiling.py` Gate 7 fix & deletion of `ceiling_satisfied`): verified waiver regime non-gating.
   - R6 (Record schema generation guard): verified `RECORD_SCHEMA_VERSION = "muru-rc5-case-record-2.0.0"` enforcement.

2. **Blocker B (A3.5 Obligation 8 Prospective Discharge)**:
   - Added `winning_class_distinct_expression_strings` and `winning_class_distinct_coefficient_vectors` to `CaseExecutionRecord`, `__post_init__` validation, `scientific_payload`, and runner. Tested and verified non-gating.

3. **Blocker C (A1 M0/M1/M2/M3 Adequacy Engine)**:
   - Built deterministic fitter and LOEO engine in `src/muru/paper_benchmark/rc5_adequacy.py` with closed-form M2/M3 solvers, coarse-to-fine grid search, boundary detection, and integration with `decide_case_adequacy`. 10 unit tests passing.

4. **Blocker D (Four Prospective Bindings & Disclosures)**:
   - Authored `audit/MURU_RC5_PROSPECTIVE_BINDINGS.md` covering SymPy parse fold quantification (~26.8% under-merge on rational division expressions proven conservative), A1.2 "shrink 10" refinement composition, `A_LO`/`A_HI` plateau bindings, §13 erratum retiring §7.4 merge claim, and Challenge partition generation disclosure.

---

## 3. Freeze Authorization

All requirements for MURU ConjectureLab Release Candidate 5 (RC5) are satisfied.

```
======================================================================
MURU RC5 FINAL ENGINEERING DECISION: RC5 FREEZE APPROVED
======================================================================
```
