# MURU ConjectureLab v1 — Exact-Lineage Reproducibility Audit

**Audit Date (UTC):** 2026-08-14T18:35:00Z  
**Auditor:** Antigravity / Gemini 3.7 Flash (High Reasoning)  
**Execution Mode:** READ ONLY — Zero scientific code modified; zero prospective outcomes inspected.  
**Repository:** `/Users/aryav/Documents/MURU-ConjectureLab-v1`  
**Supersedes:** Provisional Clean-Clone Audit (`audit/MURU_CLEAN_CLONE_REPRODUCIBILITY_AUDIT.md`)

---

## 1. Executive Summary & Audit Mandate

This audit performs an exact-lineage reproducibility re-evaluation of MURU ConjectureLab v1 across three prospective commit lineages, strictly avoiding substitution of `origin/main` or any default remote branch.

### Audited Lineages

1. **Lineage A (A3.4 Science Content Freeze):**  
   Commit: `be23b80d63fbd30227f0ab8f200dddc2121f3bfe`  
   Tag: `benchmark-content-freeze-a3-4`  
   Status: **FROZEN IMMUTABLE SCIENCE**
2. **Lineage B (A3.4 Temporal Provenance Erratum):**  
   Commit: `220c9cb679e03865f1b2a02b975397de9f4c7b46`  
   Tag: `a3-4-temporal-provenance-erratum`  
   Status: **FROZEN AUDIT ERRATUM**
3. **Lineage C (Current Engineering RC4 HEAD):**  
   Commit: `64ddefc8e03684b2fccf5596a6da241223e4ed49` (prior evaluated commit: `b3581d08d322d409fa641d0f52416b10577ec20b`)  
   Branch: `eng/muru-rc4-a3-4`  
   Status: **PROVISIONAL** (Subject to formal engineering freeze by Codex)

---

## 2. Dependency Lock & SymPy Status Audit

### 2.1 Exact Lockfile Verification (`requirements.lock.txt`)

Using `git show <commit>:requirements.lock.txt`, all three exact prospective lineages track an identical lockfile:

| Metric / Property | Lineage A (`be23b80`) | Lineage B (`220c9cb`) | Lineage C (`64ddefc` / `b3581d0`) |
|---|---|---|---|
| **Lockfile Path** | `requirements.lock.txt` | `requirements.lock.txt` | `requirements.lock.txt` |
| **SHA-256 Digest** | `1a6e61d6e006110e1afd8b2d065332107a8b2d05dec537ee5f4fc570887e13cb` | `1a6e61d6e006110e1afd8b2d065332107a8b2d05dec537ee5f4fc570887e13cb` | `1a6e61d6e006110e1afd8b2d065332107a8b2d05dec537ee5f4fc570887e13cb` |
| **Line Count (`wc -l`)** | 39 | 39 | 39 |
| **Pinned Distributions** | 39 | 39 | 39 |
| **`pyproject.toml` Tracked?** | No (`pyproject.toml` absent) | No (`pyproject.toml` absent) | No (`pyproject.toml` absent) |

### 2.2 Target Distribution Matrix

| Package | Status in Exact Lock | Locked Version | Required By Codebase? | Scope of Requirement |
|---|---|---|---|---|
| **`sympy`** | **ABSENT** | — | **YES** | Prospective G2/G3/Secondary contracts, Phase 3 grammar |
| **`mpmath`** | **ABSENT** | — | **YES** | Transitive runtime dependency of `sympy` |
| **`pysr`** | **ABSENT** | — | Conditional | Actual execution of calibration search and Dev/Held-out runs |
| **`gplearn`** | **ABSENT** | — | Historical | Historical baseline search (`scripts/t2_05_baselines.py`) |
| **`numpy`** | **PRESENT** | `numpy==2.5.2` | **YES** | Universal numerical core |
| **`scipy`** | **PRESENT** | `scipy==1.18.0` | **YES** | Statistical estimators, optimization, Wilson bounds |
| **`pandas`** | **PRESENT** | `pandas==3.0.5` | **YES** | Benchmark tables, split partitions, records |
| **`scikit-learn`**| **PRESENT** | `scikit-learn==1.9.0` | **YES** | Cross-validation, Butina clustering, baselines |
| **`rdkit`** | **PRESENT** | `rdkit==2026.3.5` | Historical | Historical Phase 1/2 structure and descriptor pipelines |

### 2.3 SymPy Lineage Determination & Discrepancy Analysis

- **Exact Lineage Determination:** **`UNPINNED_AT_EXACT_LINEAGE`**  
  `sympy` and `mpmath` are omitted from `requirements.lock.txt` at Lineage A, Lineage B, and Lineage C.
- **Repository Branch Variance:** **`DIFFERS_BY_BRANCH`**  
  In the wider git graph, branch `engineering/muru-completion` (at commit `c7c2332`) updated `requirements.lock.txt` to 50 pinned packages (including `sympy==1.14.0`, `mpmath==1.3.0`, and `pysr==1.5.10`). However, the science amendment branches (`science/muru-paper-benchmark-a3-1` through `a3-4`) and the subsequent `eng/muru-rc4-a3-4` branch inherited the earlier Phase 2 lockfile of 39 packages.
- **Trace of Discrepancy with Provisional Audit:**  
  The provisional audit text casually referenced "40 pinned packages" due to counting an index entry / header; precise verification confirms exactly 39 lines and 39 pinned distributions (SHA-256 `1a6e61d...`).

---

## 3. Prospective PySR, Julia & SymbolicRegression.jl Usage Trace

A granular path-by-path inspection establishes the exact runtime boundaries for PySR and Julia:

| Workflow / Subsystem | Requires `pysr`? | Requires Julia runtime? | Requires `SymbolicRegression.jl`? | Rationale & Code Boundary |
|---|---|---|---|---|
| **Prospective Paper Benchmark Generation** | **NO** | **NO** | **NO** | Purely numerical generators (`src/muru/paper_benchmark/generator.py`, `scripts/pb_00_build.py`). Only imports `numpy`, `pandas`, `hashlib`, `json`. |
| **Benchmark Evaluators & Contracts** | **NO** | **NO** | **NO** | `g2_contract.py`, `g3_contract.py`, `adequacy_contract.py`, `secondary_endpoints.py`. Evaluates pre-existing ASTs/equations using `sympy` and `scipy`. |
| **Integrity & Preflight Verification** | **NO** | **NO** | **NO** | `pb_10_preflight.py`, `pb_30`–`pb_35_*.py`. Validates static AST boundaries, hashes, and schema without booting Julia. |
| **RC3.1 Calibration Unit Tests** | **NO** | **NO** | **NO** | `tests/test_rc3_*.py` execute synthetic mock backends (`SyntheticBackend`, `PrecomputedBackend`, `RaisingBackend`) and verify deterministic error isolation without invoking Julia. |
| **RC3.1 Calibration Execution (Search)** | **YES** | **YES** | **YES** | `rc3_calibration_runner.py::PySRBackend` instantiates `PySRRegressor` to run genetic search over calibration worlds. |
| **A3.2 3,000-Seed Calibration (Protocol)**| **YES** | **YES** | **YES** | The 100-world $\times$ 30-seed search protocol frozen in `calibration_contract.py` specifies PySR 1.5.10 and `SymbolicRegression.jl` v1.11.x. |
| **Development Partition Execution** | **YES** | **YES** | **YES** | Prospective candidate generation across the 80 Development cases (30 seeds/case = 2,400 runs) executes PySR search. |
| **Held-Out Partition Execution** | **YES** | **YES** | **YES** | Prospective candidate generation across the 240 Held-out cases executes PySR search. |

---

## 4. Re-Audit of `artifacts/p2_compounds.parquet`

### 4.1 Prospective vs. Historical Reconfirmation

| Prospective / Historical Subsystem | Requires `p2_compounds.parquet`? | Mechanistic Proof |
|---|---|---|
| **Prospective Benchmark Generation** | **NO** | Fully synthetic. Generates 180 synthetic compounds directly via `generator.py`. |
| **Prospective Calibration** | **NO** | Generates 100 synthetic calibration worlds via `rc3_calibration_worlds.py`. |
| **A3.4 Secondary Endpoint Scoring** | **NO** | Uses synthetic 12-frame reference distributions and candidate parameter estimators. |
| **Development Partition (80 cases)** | **NO** | Generates all 80 cases from pure synthetic equations and features. |
| **Held-Out Partition (240 cases)** | **NO** | Generates all 240 cases from pure synthetic equations and features. |
| **Historical Phase 1/2 Pipelines** | **YES** | Summarizes 550 MassBank real-data compounds extracted from LCSB mzML records. |
| **Historical Objective Validation (OV) Tests** | **YES (Defect)** | `tests/test_ov_pipeline.py` and `tests/test_ov_blinding.py` call `load_dev_covariates()` without `pytest.skip` guards. |

### 4.2 Formal Classification

- **`HISTORICAL_ONLY_REPRODUCIBILITY_GAP`**: The file is an intermediate derived table from MassBank raw data (`scripts/t2_02_splits.py`), excluded from git by `.gitignore` (`artifacts/*`, `*.parquet`).
- **`TEST_FIXTURE_PACKAGING_GAP`**: The 17 test failures/errors in `test_ov_*` are due to the omission of `pytest.skip` guards (which already exist in `tests/test_p3_generators.py` and `tests/test_confirmation_seal.py`).
- **Zero Impact on Paper Benchmark:** Does not impede prospective paper benchmark generation, calibration analysis, contract evaluation, or Development/Held-out runs.

---

## 5. Clean Environment Test Execution Matrix

All tests were executed in pristine isolated virtual environments on Python 3.13.12 (macOS Darwin arm64) using detached worktrees at each exact commit.

### 5.1 Environment Definitions

1. **Canonical Tracked Environment (Strict):**  
   Built strictly using `pip install -r requirements.lock.txt` (39 pinned distributions, omitting `sympy`, `mpmath`, `pysr`).
2. **Non-Canonical Diagnostic Environment:**  
   Built with `requirements.lock.txt` + `sympy==1.14.0`, `mpmath==1.3.0`, `pysr==1.5.10`, `gplearn==0.4.3`, `juliacall==0.9.26`, `juliapkg==0.1.25`.

---

### 5.2 Test Results by Lineage and Scope

#### Lineage A: Science Content Freeze (`be23b80d63fbd30227f0ab8f200dddc2121f3bfe`)

| Environment | Test Scope | Collected | Passed | Skipped | Failed | Errors | Duration | Verdict / Root Cause |
|---|---|---|---|---|---|---|---|---|
| **Canonical Tracked** | Full Test Suite | 571 | 0 | 0 | 0 | 7 | 42.57s | **COLLECTION ERROR** (`ModuleNotFoundError: No module named 'sympy'`) |
| **Canonical Tracked** | Paper Benchmark Suite | 280 | 0 | 0 | 0 | 2 | 2.10s | **COLLECTION ERROR** (`g2_contract.py`, `g3_contract.py` import `sympy`) |
| **Diagnostic Venv** | Prospective Paper Benchmark | 326 | **326** | 0 | 0 | 0 | 34.78s | **100% PASS** (All contracts, generators, invariants verified) |
| **Diagnostic Venv** | Historical Full Repository Suite | 749 | 672 | 60 | 3 | 14 | 67.26s | **17 Gaps** (Missing historical `p2_compounds.parquet` in `test_ov_*`) |

---

#### Lineage B: Temporal Provenance Erratum (`220c9cb679e03865f1b2a02b975397de9f4c7b46`)

| Environment | Test Scope | Collected | Passed | Skipped | Failed | Errors | Duration | Verdict / Root Cause |
|---|---|---|---|---|---|---|---|---|
| **Canonical Tracked** | Full Test Suite | 590 | 0 | 0 | 0 | 13 | 1.46s | **COLLECTION ERROR** (`ModuleNotFoundError: No module named 'sympy'`) |
| **Diagnostic Venv** | Paper Benchmark & Calibration | 576 | **576** | 0 | 0 | 0 | 30.38s | **100% PASS** (All A1–A3.4 & RC3 calibration tests pass) |
| **Diagnostic Venv** | Historical Full Repository Suite | 999 | 922 | 60 | 3 | 14 | 38.00s | **17 Gaps** (Missing historical `p2_compounds.parquet` in `test_ov_*`) |

---

#### Lineage C: Current Engineering RC4 HEAD (`64ddefc8e03684b2fccf5596a6da241223e4ed49`, PROVISIONAL)

| Environment | Test Scope | Collected | Passed | Skipped | Failed | Errors | Duration | Verdict / Root Cause |
|---|---|---|---|---|---|---|---|---|
| **Canonical Tracked** | Full Test Suite | 610 | 0 | 0 | 0 | 16 | 1.87s | **COLLECTION ERROR** (`ModuleNotFoundError: No module named 'sympy'`) |
| **Diagnostic Venv** | Benchmark, Calibration & RC4 Suite | 664 | **664** | 0 | 0 | 0 | 36.99s | **100% PASS** (All A1–A3.4, RC3, and A3.4 RC4 secondary endpoints pass) |
| **Diagnostic Venv** | Historical Full Repository Suite | 1076 | 999 | 60 | 3 | 14 | 44.46s | **17 Gaps** (Missing historical `p2_compounds.parquet` in `test_ov_*`) |

*(Note on Lineage C prior commit `b3581d0`: At commit `b3581d0`, `test_a3_4_temporal_provenance_erratum.py` tested `git rev-parse HEAD == TAG`, which failed by 1 test because HEAD had advanced past the erratum tag; this was resolved in `64ddefc` where all 664 prospective tests pass cleanly).*

---

## 6. Comparison Against Earlier Provisional Audit

| Audit Property / Finding | Provisional Clean-Clone Audit (`ca9c05a`) | Exact-Lineage Reproducibility Audit (This Report) | Resolution / Clarification |
|---|---|---|---|
| **Target Commit Lineage** | Broad worktree state | Separated Lineages A (`be23b80`), B (`220c9cb`), and C (`64ddefc` / `b3581d0`) | Exact lineage isolation confirmed |
| **`requirements.lock.txt` Count** | Reported as "40 packages" | Exactly 39 lines / 39 distributions (SHA-256 `1a6e61d...`) | Corrected exact count |
| **SymPy Lineage Scope** | Identified as missing from lock | Classed as `UNPINNED_AT_EXACT_LINEAGE` & `DIFFERS_BY_BRANCH` | Provenance discrepancy mapped to Phase 2 vs Engineering branches |
| **Paper Benchmark Tests** | 326 / 326 passed (Lineage A) | 326 / 326 (Lineage A), 576 / 576 (Lineage B), 664 / 664 (Lineage C) | Exact test suite growth tracked across amendments |
| **PySR / Julia Trace** | High-level summary | Exhaustively partitioned across 8 subsystems | Proved benchmark generation & contracts require 0 Julia |
| **`p2_compounds.parquet`** | Identified as historical gap | Reconfirmed 100% independent of prospective paper benchmark | Confirmed purely a test fixture defect in historical tests |

---

## 7. Final Classification

### Exact Verdict:
# **MIXED_HISTORICAL_VS_PROSPECTIVE_GAPS**

### Detailed Sub-Classifications:
1. **Prospective Benchmark Science:** `EXACT_LINEAGE_DEPENDENCY_GAP`  
   The prospective paper benchmark code, generators, and contracts are 100% complete and self-contained with zero artifact gaps, but require the explicit pinning of `sympy==1.14.0` (and `mpmath==1.3.0`) in `requirements.lock.txt`.
2. **Historical Phase 2/3 Repository:** `HISTORICAL_ONLY_REPRODUCIBILITY_GAP`  
   Historical objective-validation test fixtures lack `pytest.skip` guards for derived intermediate MassBank tables.
3. **Partition Clearance:**  
   Neither Development nor Held-out execution is blocked by missing scientific artifacts.

MIXED_HISTORICAL_VS_PROSPECTIVE_GAPS
