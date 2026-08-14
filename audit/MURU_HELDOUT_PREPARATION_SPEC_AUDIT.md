# MURU ConjectureLab v1 — Held-Out Preparation Spec-vs-Invention Hostile Audit

**Document ID:** `MURU-AUDIT-HELDOUT-PREPARATION-SPEC-01`  
**Classification:** `HOSTILE_SPEC_VS_INVENTION_AUDIT`  
**Status:** `AUDIT_COMPLETE`  
**Audit Branch:** `audit/muru-heldout-preparation-spec-audit`  
**Mode:** `READ_ONLY_AUDIT` (Packets were not modified; Development not run; Held-out not opened)  
**Governing Authorities:**
- Amendment A3.4 Science Content Freeze ([`be23b80`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md) / `benchmark-content-freeze-a3-4`)
- Engineering RC4 Release Candidate Freeze ([`c800e7a`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_RC4_A3_4_ENGINEERING_FREEZE.md) / `engineering-rc4-a3-4`)
- Outcome-Blind A3.4 Temporal Provenance Erratum ([`220c9cb`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md) / `a3-4-temporal-provenance-erratum`)
- Amendment A3.1 Structural Endpoints & Calibration Contract ([`c8938e8`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md) / `benchmark-content-freeze-a3-1`)
- Amendment A3.2 Null Calibration Base Target & Scaffold Split ([`363b517`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md) / `benchmark-content-freeze-a3-2`)
- Amendment A3.3 Secondary Endpoints Contract ([`363e1c5`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_3.md) / `benchmark-content-freeze-a3-3`)
- Engineering RC3.1 Implementation Freeze ([`0b4a5a4`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py) / `engineering-rc3-1-a3-2`)

---

## 1. Executive Summary & Audit Charter

This hostile audit provides an exhaustive, adversarial verification of the two preparation packets created for prospective Held-out validation:
1. **Pre-Held-Out Authorization Matrix & Review Templates** (`audit/templates/`):
   - [`MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md)
   - [`muru_pre_heldout_authorization_matrix.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/muru_pre_heldout_authorization_matrix.json)
   - [`MURU_DEVELOPMENT_RETURN_HOSTILE_REVIEW.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_DEVELOPMENT_RETURN_HOSTILE_REVIEW.md)
2. **Held-Out Preparation Artifacts** (`ops/heldout_ready/`):
   - [`MURU_HELDOUT_AUDIT_CHECKLIST.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_AUDIT_CHECKLIST.md)
   - [`MURU_HELDOUT_EXECUTION_MANIFEST_TEMPLATE.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_EXECUTION_MANIFEST_TEMPLATE.json)
   - [`MURU_HELDOUT_FAILURE_RESUME_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_FAILURE_RESUME_MATRIX.md)
   - [`MURU_HELDOUT_ONE_SHOT_RUNBOOK.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_ONE_SHOT_RUNBOOK.md)
   - [`MURU_HELDOUT_RESULT_SCHEMA.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md)
   - [`PROMPT_CLAUDE_HELDOUT_EXECUTION.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/PROMPT_CLAUDE_HELDOUT_EXECUTION.md)

### Audit Standard & Objective
The audit distinguishes six precise epistemic categories for every requirement and factual assertion:
- **`FROZEN_BINDING_REQUIREMENT`**: Directly frozen by existing science, governance, or engineering contracts.
- **`ENGINEERING_DERIVED_REQUIREMENT`**: Valid derived consequence of frozen repository rules.
- **`OPTIONAL_HARDENING_NOT_BINDING`**: Legitimate reproducibility hardening, but not a binding retrospective gate.
- **`NEW_REQUIREMENT_NOT_AUTHORIZED`**: Newly invented requirement not supported by frozen repository authority.
- **`FACTUALLY_INCORRECT`**: Directly contradicts frozen mathematical, syntactic, or geometric repository authority.

---

## 2. PASS 1 — Factual & Numerical Verification

Every benchmark parameter, case count, replicate count, seed count, denominator, tolerance, and syntax rule was traced to its immutable code implementation:

| Dimension / Fact | Claimed Value in Packets | Frozen Repository Authority | Correct Frozen Rule / Value | Verification Verdict |
|---|---|---|---|---|
| **Development Case Count** | 80 cases | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `PARTITION_CASE_COUNTS["development"] = 4` $\times 20$ families | Exactly **80 cases** | **`VERIFIED_CORRECT`** |
| **Held-Out Case Count** | 240 cases | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `PARTITION_CASE_COUNTS["held_out"] = 12` $\times 20$ families | Exactly **240 cases** | **`VERIFIED_CORRECT`** |
| **Benchmark Families** | 20 families (`F01`–`F20`) | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `CASE_FAMILIES` | Exactly **20 families** | **`VERIFIED_CORRECT`** |
| **Replicates / Family (Dev)** | 4 replicates (`r000`–`r003`) | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py) | **4 replicates** per family | **`VERIFIED_CORRECT`** |
| **Replicates / Family (Held-out)** | 12 replicates (`r000`–`r011`) | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py) | **12 replicates** per family | **`VERIFIED_CORRECT`** |
| **Compounds / Case** | **`30 compounds`** *(Matrix Criterion 5)* vs `180` *(Schema/Runbook)* | [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py): `N_COMPOUNDS = 180` | **180 compounds** across 30 scaffolds (6 compounds/scaffold) | **`FACTUALLY_INCORRECT` in Matrix Criterion 5** |
| **Scaffolds / Case** | 30 scaffolds | [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py): `N_SCAFFOLDS = 30` | **30 scaffolds** (20 train, 5 val, 5 test) | **`VERIFIED_CORRECT`** |
| **Compounds / Scaffold** | 6 compounds | [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py): `180 // 30 = 6` | **6 compounds per scaffold** | **`VERIFIED_CORRECT`** |
| **Energies / Case** | 6 energies (15, 30, 45, 60, 75, 90) | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `ENERGY_GRID` | **6 energies** standard (1,080 rows); F04 has 5 (900 rows) | **`VERIFIED_CORRECT`** |
| **Development Seeds** | 2,400 seeds | $80 \text{ cases} \times 30 \text{ seeds}$ | Exactly **2,400 seeds** | **`VERIFIED_CORRECT`** |
| **Held-Out Seeds** | 7,200 seeds | $240 \text{ cases} \times 30 \text{ seeds}$ | Exactly **7,200 seeds** | **`VERIFIED_CORRECT`** |
| **Gate 1 (G1) Denominator** | **164 cases** | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `endpoint_case_count("scalar_competence")` | Exactly **164 cases** (13 fams $\times 12 + 8$ from F19) | **`VERIFIED_CORRECT`** |
| **Gate 2 (G2) Denominator** | **144 cases** | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `endpoint_case_count("family_recovery")` | Exactly **144 cases** (12 fams $\times 12$) | **`VERIFIED_CORRECT`** |
| **Gate 3 (G3) Denominator** | **36 opportunities** | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `endpoint_case_count("principal_structural_safety")` | Exactly **36 opportunities** (F07, F19, F20 $\times 12$) | **`VERIFIED_CORRECT`** |
| **Parameter Recovery (Joint)** | **156 cases** | [`a34_parameter_recovery.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_parameter_recovery.py): `PARAMETER_RECOVERY_DENOMINATOR` | Exactly **156 cases** (13 fams $\times 12$) | **`VERIFIED_CORRECT`** |
| **Parameter Recovery ($p_{\text{mass}}$)** | **156 cases** | [`a34_parameter_recovery.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_parameter_recovery.py): `P_MASS_DENOMINATOR` | Exactly **156 cases** (13 fams $\times 12$) | **`VERIFIED_CORRECT`** |
| **Parameter Recovery ($c_{\text{desc}}$)** | **84 cases** | [`a34_parameter_recovery.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_parameter_recovery.py): `C_DESC_DENOMINATOR` | Exactly **84 cases** (7 fams $\times 12$) | **`VERIFIED_CORRECT`** |
| **Predictive Equivalence** | **144 cases** | [`a34_contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_contract.py): `PREDICTIVE_EQUIVALENCE_DENOMINATOR` | Exactly **144 cases** (12 fams $\times 12$) | **`VERIFIED_CORRECT`** |
| **Exact Algebra** | **60 cases** | 5 families (F01, F08, F09, F10, F17) $\times 12$ cases | Exactly **60 cases** | **`VERIFIED_CORRECT`** |
| **Wilson Scoring Rules** | G1 $\ge 0.70$, G2 $\ge 0.70$, G3 $\le 0.15$ | [`analysis.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/analysis.py): `wilson_interval`, $z=1.959963984540054$ | G1/G2 Lower 95% $\ge 0.70$; G3 Upper 95% $\le 0.15$ | **`VERIFIED_CORRECT`** |
| **Parameter Tolerances** | $|\Delta p_{\text{mass}}| \le 0.15$, $|\Delta c_{\text{desc}}| \le 0.10$ | [`a34_parameter_recovery.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_parameter_recovery.py): exact rational tolerance checks | $|\Delta p| \le 0.15$, $|\Delta c| \le 0.10$ without $\varepsilon$ widening | **`VERIFIED_CORRECT`** |
| **Predictive Thresholds** | $|V| \ge 2,150$, $c^* > 0$, $\text{rel\_RMSE} \le 0.05$, $r \ge 0.990$ | [`a34_predictive_equivalence.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_predictive_equivalence.py) | 2,160 rows, $|V| \ge 2150$, $c^* > 0$, $\text{rel\_RMSE} \le 0.05$, $r \ge 0.990$ | **`VERIFIED_CORRECT`** |
| **Case-ID Syntax** | **`PB\|DEV\|F01\|000`** *(Matrix Criterion 5)* vs `PB\|held_out\|F01\|r000` | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py): `resolve_case_id`, `iter_case_ids` | `PB\|{partition}\|{family}\|r{replicate:03d}` | **`FACTUALLY_INCORRECT` in Matrix Criterion 5** |

### Critical Investigation: Known Suspect ("30 compounds x 6 energies")
The pre-Held-Out authorization matrix (Criterion 5 in [`MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md) and [`muru_pre_heldout_authorization_matrix.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/muru_pre_heldout_authorization_matrix.json)) asserts that a Development case contains:
> *"30 compounds x 6 energies per case"*

**Authoritative Finding:**
Inspection of [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py) lines 30–31 and 100–123 demonstrates:
- `N_COMPOUNDS = 180`
- `N_SCAFFOLDS = 30`
- `scaffold = np.repeat(np.arange(30), 180 // 30)` (6 compounds per scaffold).
- Split: 20 scaffolds = 120 compounds train, 5 scaffolds = 30 compounds validation, 5 scaffolds = 30 compounds test.
- The number 30 is the number of *scaffolds* (or the number of test compounds), NOT the total compounds per case.
- **Classification:** **`FACTUALLY_INCORRECT`** (Must be corrected to: *"180 compounds across 30 scaffolds (6 compounds/scaffold) x 6 energies"*).

---

## 3. PASS 2 — Requirement Provenance for 20-Point Authorization Matrix

Every one of the 20 criteria in the pre-Held-out matrix was evaluated for historical provenance and epistemic classification:

| # | Criterion | Stated Scope & Evidence Standard | Provenance Anchor | Classification | Epistemic Assessment |
|---|---|---|---|---|---|
| **1** | **Environment Closure** | OS kernel, LLVM/Clang, Python, Julia, Thread caps (`JULIA_NUM_THREADS=1`, `OMP_NUM_THREADS=1`), Hardware envelope | [`protocol.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/protocol.py), [`preflight.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/preflight.py) | **`OPTIONAL_HARDENING_NOT_BINDING`** *(for OS/Compiler/Hardware)* / **`ENGINEERING_DERIVED_REQUIREMENT`** *(for Threads/Python/Julia)* | Python/Julia versions and thread limits are binding engineering determinism contracts. Upgrading OS kernel, LLVM/Clang compiler version, and hardware allocation to retrospective blocking governance gates is unauthorizable hardening. |
| **2** | **Dependency Transitive Closure** | `requirements.lock.txt`, Julia `Manifest.toml`, wheel hashes, zero network, `sympy==1.14.0`, `mpmath==1.3.0` | [`requirements.lock.txt`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/requirements.lock.txt) at `c7c2332` (RC2) | **`FROZEN_BINDING_REQUIREMENT`** *(Lockfile/Zero-Network/SymPy)* / **`OPTIONAL_HARDENING_NOT_BINDING`** *(Wheel hashes)* | `requirements.lock.txt` and zero network access are frozen binding contracts. Transitive wheel hash verification is desirable hardening. |
| **3** | **PySR / Julia Engine Identity** | PySR version, Julia UUIDs, parsimony, loss functions, operator grammar (`+`, `-`, `*`, `/`, `^`, `log`, `exp`, `sqrt`) | [`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md), [`calibration_contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/calibration_contract.py) | **`FROZEN_BINDING_REQUIREMENT`** *(with `FACTUALLY_INCORRECT` text in criterion)* | Engine versions and parsimony are frozen. **Defect:** Criterion 3 lists `exp` in the grammar and omits `square, cube, inv`; A3.1 explicitly excluded `exp` and `trig`. |
| **4** | **Dev Manifest Frozen Pre-Seed** | Manifest committed and hashed prior to `started_utc` and first durable seed record | [`MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md) (`220c9cb`) | **`ENGINEERING_DERIVED_REQUIREMENT`** *(with `INVENTED_PATH`)* | The precedence of input manifest creation over seed execution is an established engineering requirement. **Defect:** The path `artifacts/inputs/development_manifest.json` is invented. |
| **5** | **80 Exact Development Cases** | 80 cases (4x20 families), 2,400 seeds, case IDs `PB\|DEV\|F01\|000`, 30 compounds x 6 energies | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py), [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py) | **`FROZEN_BINDING_REQUIREMENT`** *(80 cases/2400 seeds)* / **`FACTUALLY_INCORRECT`** *(Case ID syntax & compound geometry)* | 80 cases and 2,400 seeds are binding. Case ID syntax (`PB\|DEV\|...`) and compound geometry (`30 compounds`) are factually incorrect. |
| **6** | **Exact Search Budget** | `niterations`, `timeout_in_seconds`, `maxsize`, population size, peak RSS ceiling (< 4 GB) | [`calibration_contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/calibration_contract.py), A3.1 | **`FROZEN_BINDING_REQUIREMENT`** *(Search budget)* / **`OPTIONAL_HARDENING_NOT_BINDING`** *(RSS ceiling)* | Search iterations (40), populations (15), size (33), and maxsize (20) are binding. Peak RSS < 4 GB is operational telemetry, not a frozen gate. |
| **7** | **Calibration Threshold Binding** | Signed threshold digest (`null_threshold_table.json`), calibrated on 100 worlds $\times$ 30 seeds, $\ge 95$ valid worlds | [`calibration_contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/calibration_contract.py), [`rc3_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_acceptance.py), A3.1/A3.2 | **`FROZEN_BINDING_REQUIREMENT`** | Exact binding of the signed null threshold table digest from a valid calibration run is a frozen scientific requirement. |
| **8** | **No Selective Retries** | Monotonic execution logs, PIDs, filesystem inode creation times, sequential run telemetry | [`MURU_HELDOUT_FAILURE_RESUME_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_FAILURE_RESUME_MATRIX.md), Protocol V1 | **`FROZEN_BINDING_REQUIREMENT`** *(No scientific retries)* / **`OPTIONAL_HARDENING_NOT_BINDING`** *(Inode/PID gating)* | Scientific failures must never be retried. Mandating monotonic inode creation times or process IDs as blocking gates is unauthorizable hardening. |
| **9** | **No Result-Dependent Science Changes** | Cryptographic diff of all 31 protected science files against frozen A3.4 `be23b80` | [`pb_35_a3_4_integrity.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/scripts/pb_35_a3_4_integrity.py), [`MURU_RC4_A3_4_ENGINEERING_FREEZE.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_RC4_A3_4_ENGINEERING_FREEZE.md) (`c800e7a`) | **`FROZEN_BINDING_REQUIREMENT`** | Byte-for-byte immutability of all 31 protected science files is a binding requirement. |
| **10** | **Dev Raw-Record Completeness** | 80 records, 80 sidecars, 2,400 seeds, 80 secondary, full Pareto traces | [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py), [`a34_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/a34_record.py) | **`FROZEN_BINDING_REQUIREMENT`** *(Records/Seeds/Sidecars)* / **`OPTIONAL_HARDENING_NOT_BINDING`** *(Full Pareto traces)* | Completeness of raw JSON records and sidecars is binding. Mandatory retention of internal intermediate Pareto evolution histories is optional hardening. |
| **11** | **Independent Reconstruction** | Standalone verification script parsing 80 raw records, re-deriving acceptance against calibration digest | [`rc3_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_acceptance.py) (`verify_record_acceptance`), [`analysis.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/analysis.py) | **`FROZEN_BINDING_REQUIREMENT`** | Automated truth-blind acceptance re-derivation and endpoint reconstruction from raw files is binding. |
| **12** | **FM-06 Production Conformance** | Fold-local scalar fit (`split == 'train'`), immutable objects, non-transductive canary ($0.0$ leak) | [`protocol.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/protocol.py), Protocol V1 | **`FROZEN_BINDING_REQUIREMENT`** | Strictly fold-local scalar curve estimation without cross-compound leakage is a binding scientific contract. |
| **13** | **FM-07 Production Conformance** | Evaluator rejects complex values ($\sqrt{-x}$), poles, NaN; zero `.real` casting | [`g2_contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/g2_contract.py), [`contract.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/contract.py), A3.1 | **`FROZEN_BINDING_REQUIREMENT`** | Strict typed rejection of complex outputs and algebraic poles is a binding scientific contract. |
| **14** | **Dev / Held-Out Path Identity** | 100% identical code paths, classes, and pipelines across partitions | [`protocol.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/protocol.py), [`runner.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/runner.py) | **`FROZEN_BINDING_REQUIREMENT`** | Partition-agnostic execution pipeline is a binding requirement. |
| **15** | **Sealed Held-Out Status** | `held_out.jsonl` unopened/unread; zero output artifacts | [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py), Governance Charter | **`FROZEN_BINDING_REQUIREMENT`** *(with non-binding phrasing)* | Held-out partition unread status is binding. "Cryptographic proof of unread status" is an unattainable phrasing on standard filesystems. |
| **16** | **Executable Freeze Commit / Tag** | Tag `muru-executable-freeze-v1` pointing to locked commit with `paper_benchmark_executable_freeze.json` | [`freeze.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/freeze.py), [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py) | **`FROZEN_BINDING_REQUIREMENT`** *(Lock & Commit)* / **`TEMPLATE_PLACEHOLDER`** *(Tag name spelling)* | Implementation locking is binding. Specific tag spelling `muru-executable-freeze-v1` is a template placeholder. |
| **17** | **Clean Git Working Tree** | `git status --porcelain` completely empty across entire repository | [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py): `tree_clean: bool` | **`FROZEN_BINDING_REQUIREMENT`** *(Execution worktree)* / **`NEW_REQUIREMENT_NOT_AUTHORIZED`** *(Entire repository across all branches)* | Execution worktree cleanliness is binding. Demanding that unrelated parallel worktrees and branches be empty is an unauthorizable requirement. |
| **18** | **Unresolved Engineering Defects** | Full prospective test suite passes 100% clean; static AST scan clean | [`pb_35_a3_4_integrity.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/scripts/pb_35_a3_4_integrity.py), [`MURU_RC4_A3_4_ENGINEERING_FREEZE.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_RC4_A3_4_ENGINEERING_FREEZE.md) | **`FROZEN_BINDING_REQUIREMENT`** | Zero prospective benchmark test failures and clean static sealed boundary are binding. |
| **19** | **Defect vs Weakness Distinction** | Formal separation of software defects from scientific weaknesses | Governance Charter, A3.1 | **`FROZEN_BINDING_REQUIREMENT`** | Software bugs may be fixed on engineering branches; scientific weaknesses strictly prohibit methodology revision. |
| **20** | **No Methodology Feedback** | Zero methodology, grammar, or threshold changes informed by Development results | Governance Charter, A3.1 | **`FROZEN_BINDING_REQUIREMENT`** | Outcome-blindness of scientific methodology is a binding governance contract. |

---

## 4. PASS 3 — Execution Semantics Audit

### 4.1 Aggregation Hierarchy & Separation of Concerns
The audit verified the exact multi-tiered aggregation hierarchy frozen across [`structural_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/structural_acceptance.py), [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py), [`rc3_scoring.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_scoring.py), and [`analysis.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/analysis.py):

$$\text{Stage 1: Seed Level (30 seeds)} \to \text{Stage 2: Case Candidate Selection} \to \text{Stage 3: Case Acceptance Predicate} \to \text{Stage 4: Endpoint Scoring} \to \text{Stage 5: Primary Gate Decision}$$

1. **Seed-Level Outcome:**
   - Evaluates search execution per seed ($0 \le s \le 29$).
   - Returns typed `SeedStatus`: `COMPLETED_WITH_CANDIDATES`, `COMPLETED_NO_CANDIDATE`, or `EXECUTION_FAILURE`.
   - Seed outcomes do **not** directly determine primary gates.
2. **Case-Level Selection:**
   - Extracts the modal discovered expression string across all 30 seeds.
   - Computes selection count $k$ and selection fraction $k / 30$.
3. **Case-Level Acceptance Predicate (8 Sequential Gates):**
   - Gate 1: A1 Adequacy Prerequisite (`M0_NOT_REJECTED` proceeds; rejections yield `REJECTED_A1_INADEQUATE`).
   - Gate 2: Null Threshold ($\text{valid\_r2} > \tau(\min(\text{complexity}, 20))$; fails to `REJECTED_BELOW_NULL`).
   - Gate 3: Stability Selection ($k / 30 \ge 20 / 30$; fails to `REJECTED_UNSTABLE`).
   - Gate 4: Complexity ($\text{complexity} \le 20$; fails to `REJECTED_OVERCOMPLEX`).
   - Gate 5: Invalid Fraction ($\text{invalid\_fraction} \le 0.005$; fails to `REJECTED_INVALID_FRACTION`).
   - Gate 6: Effective Support (non-empty; fails to `REJECTED_EMPTY_SUPPORT`).
   - Gate 7: Ceiling ($\text{ceiling\_fraction} \ge 0.80 \lor \text{ceiling\_r2} < 0.05$; fails to `REJECTED_CEILING`).
   - Gate 8: Reduced Falsification Harness (6 rungs pass; fails to `REJECTED_FALSIFICATION`).
   - Terminal success: `STRUCTURAL_ACCEPTED`.
4. **Primary Gate Scoring:**
   - Evaluates fixed denominators: G1 (/164), G2 (/144), G3 (/36).
   - Computes exact 95% Wilson confidence intervals.
5. **Secondary Descriptive Endpoints:**
   - Parameter Recovery: Joint (/156), Mass Exponent (/156), Descriptor Coupling (/84).
   - Predictive Equivalence: /144.
   - Exact Algebra: /60.
   - **Isolation Rule:** Secondary endpoints are purely descriptive and can **NEVER** rescue a failed primary gate.

### 4.2 Schema & Enum Drift Inconsistencies
The audit uncovered severe schema drift between the preparation templates and the frozen codebase:

1. **AcceptanceStatus Enum Drift:**
   - [`MURU_HELDOUT_RESULT_SCHEMA.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md) declared: `[ACCEPTED_STRUCTURE, REJECTED_STABILITY, REJECTED_NULL_CALIBRATION, REJECTED_FALSIFICATION, REJECTED_NON_FINITE, REJECTED_HIGH_COMPLEXITY]`.
   - Frozen codebase ([`structural_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/structural_acceptance.py) / [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py)) defines:
     `STRUCTURAL_ACCEPTED`, `REJECTED_A1_INADEQUATE`, `REJECTED_BELOW_NULL`, `REJECTED_UNSTABLE`, `REJECTED_OVERCOMPLEX`, `REJECTED_INVALID_FRACTION`, `REJECTED_EMPTY_SUPPORT`, `REJECTED_CEILING`, `REJECTED_FALSIFICATION`, `UNEVALUABLE`.
   - **Classification:** **`FACTUALLY_INCORRECT`** (Defect DEF-04).
2. **Falsification Rungs Drift:**
   - [`MURU_HELDOUT_RESULT_SCHEMA.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md) and [`MURU_HELDOUT_AUDIT_CHECKLIST.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_AUDIT_CHECKLIST.md) (Check C.05) declared 3 rungs: `[RUNG_1_PERMUTATION, RUNG_2_TARGET_PERTURBATION, RUNG_3_SPURIOUS_CORRELATION]`.
   - Frozen codebase ([`structural_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/structural_acceptance.py) / [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py)) defines 6 rungs:
     `F1_REPRODUCIBILITY`, `F4_COMPOUND_HOLDOUT`, `F5_SCAFFOLD_HOLDOUT`, `F7_INFLUENCE_DROP`, `F9_ENERGY_SUBSET`, `F10_NEGATIVE_CONTROL`.
   - **Classification:** **`FACTUALLY_INCORRECT`** (Defect DEF-05).
3. **Record Schema Version Drift:**
   - [`MURU_HELDOUT_RESULT_SCHEMA.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md) declared: `"schema_version": "muru-paper-benchmark-record-1.0.0"`.
   - Frozen codebase ([`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py)) defines: `RECORD_SCHEMA_VERSION = "muru-rc3-case-record-1.0.0"`.
   - **Classification:** **`FACTUALLY_INCORRECT`** (Defect DEF-06).

---

## 5. PASS 4 — Path & Artifact Naming Audit

Every path asserted across the preparation documents was categorized according to its canonical status:

| Path / Pattern | Packet Location | Exact Status / Classification | Notes / Frozen Canonical Counterpart |
|---|---|---|---|
| `artifacts/inputs/held_out.jsonl` | Runbook, Schema, Checklist | **`FROZEN_FUTURE_PATH`** | Canonical sealed input dataset path generated by [`artifacts.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/artifacts.py) `build_partition('held_out')`. |
| `artifacts/inputs/development.jsonl` | Protocol, Preflight | **`EXISTING_CANONICAL_PATH`** | Canonical input dataset for the 80 Development cases. |
| `artifacts/inputs/development_manifest.json` | Matrix Criterion 4 | **`INVENTED_PATH`** | Invented path. Canonical manifests are [`artifacts/paper_benchmark_case_manifest.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/artifacts/paper_benchmark_case_manifest.json) and `artifacts/inputs/development.jsonl`. |
| `artifacts/development/` | Runbook, Review | **`FROZEN_FUTURE_PATH`** | Output directory for Development execution artifacts. |
| `artifacts/calibration/null_threshold_table.json` | Runbook, Checklist | **`FROZEN_FUTURE_PATH`** | Canonical output path for the calibrated null threshold table. |
| `artifacts/paper_benchmark_executable_freeze.json` | Runbook, Matrix | **`FROZEN_FUTURE_PATH`** | Canonical JSON output from [`freeze.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/freeze.py) (`prepare_content_freeze`). |
| `artifacts/held_out/held_out_execution_manifest.json` | Runbook, Schema | **`FROZEN_FUTURE_PATH`** | Pre-execution manifest locking all 240 cases and 7,200 seeds before execution. |
| `artifacts/held_out/paper_benchmark_heldout_audit.json` | Checklist, Schema | **`FROZEN_FUTURE_PATH`** | Final signed audit dossier for Held-out execution. |
| `artifacts/held_out/case_records/{case_id}.json` | Schema, Runbook | **`FROZEN_FUTURE_PATH`** | 240 canonical scientific case records (`CaseExecutionRecord`). |
| `artifacts/held_out/provenance_sidecars/{case_id}.json` | Schema, Runbook | **`FROZEN_FUTURE_PATH`** | 240 non-scientific operational sidecars (`ProvenanceSidecar`). |
| `artifacts/held_out/seed_records/{case_id}/seed_{s:02d}.json` | Schema, Runbook | **`FROZEN_FUTURE_PATH`** | 7,200 individual search seed outcome records. |
| `artifacts/held_out/candidate_bindings/{case_id}.json` | Schema, Runbook | **`FROZEN_FUTURE_PATH`** | Candidate-to-grammar and truth binding records for secondary endpoints. |

---

## 6. PASS 5 — Tag & Freeze Naming Analysis

### Audit of Git Tag References
The preparation templates extensively refer to git tag `muru-executable-freeze-v1` as if it were an established, frozen authority.

**Repository Tag Audit:**
- `git tag -l` reveals the following existing annotated tags:
  - `benchmark-content-freeze-a3-4`
  - `engineering-rc4-a3-4`
  - `a3-4-temporal-provenance-erratum`
  - `benchmark-content-freeze-a3-1`
  - `benchmark-content-freeze-a3-2`
  - `benchmark-content-freeze-a3-3`
  - `engineering-rc3-1-a3-2`
  - `engineering-rc3-a3-1`
- **Finding:** No tag named `muru-executable-freeze-v1` or `paper-benchmark-executable-freeze-v1` currently exists in the repository.
- **Epistemic Ruling:** The exact tag name `muru-executable-freeze-v1` is a **`TEMPLATE_PLACEHOLDER`**, not a pre-existing frozen tag. Templates must use `<EXECUTABLE_FREEZE_TAG>` with `muru-executable-freeze-v1` declared as the *proposed* tag name to be created upon formal freeze authorization.

---

## 7. PASS 6 — Parallel Worktree Cleanliness Analysis

### Epistemic Boundary of Cleanliness
Criterion 17 in [`MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md) and [`muru_pre_heldout_authorization_matrix.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/muru_pre_heldout_authorization_matrix.json) states:
> *"git status --porcelain executed across the entire repository produces zero output (no untracked files, no unstaged modifications, no staged changes, no stashes)."*

**Audit Analysis:**
1. **Scientific Cleanliness Contract:**
   [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py) enforces `assert_held_out_execution_allowed(lock, hashes, preflight, tree_clean=True)`. This ensures that the code executing the benchmark in the active execution worktree is 100% committed, immutable, and matches the tagged commit hash.
2. **Parallel Worktree Isolation:**
   In modern multi-agent git environments, concurrent worktrees exist in separate directories (e.g. `.claude/worktrees/*`, `writing/*`, `design/*`, `audit/*`) for audit reports, manuscript drafting, and external dataset qualification.
3. **Ruling:**
   Untracked files or modifications in **unrelated parallel worktrees** or separate branches do not constitute execution contamination, provided that the execution worktree and its commit are pristine. Treating unrelated worktrees as blocking contamination is classified as **`NEW_REQUIREMENT_NOT_AUTHORIZED`**. Criterion 17 should explicitly specify the *execution worktree*.

---

## 8. Complete Defect & Action Ledger

The following ledger lists all 10 discrepancies identified across the preparation artifacts and authorization matrix:

| Defect ID | Location | Current Wording / Value | Classification | Authoritative Source | Correct Frozen Rule / Value | Must Fix Before Use? |
|---|---|---|---|---|---|:---:|
| **DEF-01** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 5), `muru_pre_heldout_authorization_matrix.json` (Crit 5) | `30 compounds * 6 energies per case` | **`FACTUALLY_INCORRECT`** | [`generator.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/generator.py) L30–31 (`N_COMPOUNDS = 180`, `N_SCAFFOLDS = 30`) | **180 compounds across 30 scaffolds** (6 compounds/scaffold) x 6 energies (1,080 trajectory rows) | **YES** |
| **DEF-02** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 5), `muru_pre_heldout_authorization_matrix.json` (Crit 5) | `case IDs PB\|DEV\|F01\|000 through PB\|DEV\|F20\|003` | **`FACTUALLY_INCORRECT`** | [`registry.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/registry.py) L201–226 (`resolve_case_id`) | **`PB\|development\|F01\|r000` through `PB\|development\|F20\|r003`** | **YES** |
| **DEF-03** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 3), `muru_pre_heldout_authorization_matrix.json` (Crit 3) | `operator grammar (+, -, *, /, ^, log, exp, sqrt)` | **`FACTUALLY_INCORRECT`** | [`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md) L156–158 | **binary (+, -, *, /), unary (sqrt, log, square, cube, inv); exp & trig excluded** | **YES** |
| **DEF-04** | `ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md` (Sec 3.2), `MURU_HELDOUT_FAILURE_RESUME_MATRIX.md` (Sec 2) | `acceptance_status` enum: `[ACCEPTED_STRUCTURE, REJECTED_STABILITY, REJECTED_NULL_CALIBRATION, ...]` | **`FACTUALLY_INCORRECT`** | [`structural_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/structural_acceptance.py) L31–43 (`AcceptanceStatus` enum) | **`[STRUCTURAL_ACCEPTED, REJECTED_A1_INADEQUATE, REJECTED_BELOW_NULL, REJECTED_UNSTABLE, REJECTED_OVERCOMPLEX, REJECTED_INVALID_FRACTION, REJECTED_EMPTY_SUPPORT, REJECTED_CEILING, REJECTED_FALSIFICATION, UNEVALUABLE]`** | **YES** |
| **DEF-05** | `ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md` (Sec 3.2), `MURU_HELDOUT_FAILURE_RESUME_MATRIX.md` (Sec 2), `MURU_HELDOUT_AUDIT_CHECKLIST.md` (Check C.05) | `falsification_results`: `[RUNG_1_PERMUTATION, RUNG_2_TARGET_PERTURBATION, RUNG_3_SPURIOUS_CORRELATION]` | **`FACTUALLY_INCORRECT`** | [`structural_acceptance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/structural_acceptance.py) L79–103, [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py) L59–66 | **6 rungs: `[F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT, F5_SCAFFOLD_HOLDOUT, F7_INFLUENCE_DROP, F9_ENERGY_SUBSET, F10_NEGATIVE_CONTROL]`** | **YES** |
| **DEF-06** | `ops/heldout_ready/MURU_HELDOUT_RESULT_SCHEMA.md` (Sec 3.2) | `schema_version: 'muru-paper-benchmark-record-1.0.0'` | **`FACTUALLY_INCORRECT`** | [`rc3_record.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_record.py) L53 (`RECORD_SCHEMA_VERSION`) | **`schema_version: 'muru-rc3-case-record-1.0.0'`** | **YES** |
| **DEF-07** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 4), `muru_pre_heldout_authorization_matrix.json` (Crit 4) | `artifacts/inputs/development_manifest.json` | **`INVENTED_PATH`** | [`artifacts.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/artifacts.py) L69–78 | **`artifacts/paper_benchmark_case_manifest.json` and `artifacts/inputs/development.jsonl`** | **YES** |
| **DEF-08** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 1), `muru_pre_heldout_authorization_matrix.json` (Crit 1) | OS kernel, LLVM/Clang compiler, hardware envelope as `BLOCKING` gates | **`OPTIONAL_HARDENING_NOT_BINDING`** | [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py), [`preflight.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/preflight.py) | Pinned Python/Julia and thread caps are binding; OS kernel, compiler, and hardware envelope are non-blocking descriptive metadata | NO |
| **DEF-09** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 8), `muru_pre_heldout_authorization_matrix.json` (Crit 8) | Monotonic PIDs and inode creation times as `BLOCKING` gates | **`OPTIONAL_HARDENING_NOT_BINDING`** | [`rc3_provenance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/rc3_provenance.py) | No retrying scientific failures is binding; inode creation time and PID monotonicity are non-binding operational metrics | NO |
| **DEF-10** | `audit/templates/MURU_PRE_HELDOUT_AUTHORIZATION_MATRIX.md` (Crit 17), `muru_pre_heldout_authorization_matrix.json` (Crit 17) | `git status --porcelain` across entire repository produces zero output | **`NEW_REQUIREMENT_NOT_AUTHORIZED`** | [`governance.py`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/src/muru/paper_benchmark/governance.py) (`tree_clean: bool`) | Execution worktree must be 100% clean; unrelated parallel worktrees and branches do not contaminate execution | NO |

---

## 9. Final Classification

Based on the identification of multiple direct contradictions of frozen scientific contracts (including search operator grammar in A3.1, case compound geometry in `generator.py`, acceptance status enums in `structural_acceptance.py`, and falsification rungs in `rc3_record.py`), this audit concludes with the following exact ruling:

```
======================================================================
FINAL CLASSIFICATION:
HELD-OUT PREPARATION PACK CONTAINS SCIENTIFIC CONTRACT ERROR
======================================================================
```
