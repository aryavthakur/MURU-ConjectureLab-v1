# MURU ConjectureLab v1: Pre-Results Figure & Table Source Traceability Map

This document establishes the comprehensive element-by-element source traceability for every pre-results figure and table in the MURU ConjectureLab v1 benchmark package.

---

## 1. Figures Traceability Map

| Figure / Panel | Description | Source File | Source Commit / Tag | Scientific Status | Frozen Status |
|---|---|---|---|---|---|
| **Figure 1** | **MURU Computational Architecture** | `scripts/pb_10_preflight.py`, `src/muru/paper_benchmark/protocol.py`, `MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` | `c8938e8` / `benchmark-content-freeze-a3-1` | Class B (Frozen Design) | **FROZEN** |
| Panel 1A | Energy observations $\mu_i(E)$ & collapse hypothesis $M_0$ | `src/muru/paper_benchmark/generator.py` | `80a7803` / `benchmark-content-freeze-a2-1` | Class B (Design Illustration) | **FROZEN** |
| Panel 1B | Two-stage fold-local target estimation | `MURU_PAPER_BENCHMARK_PROTOCOL.md`, `src/muru/paper_benchmark/structural_acceptance.py` | `d94d2c9` / `c8938e8` | Class B (Frozen Contract) | **FROZEN** |
| Panel 1C | Symbolic search & 8-stage acceptance predicate | `src/muru/paper_benchmark/structural_acceptance.py`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md` | `c8938e8` / `benchmark-content-freeze-a3-1` | Class B (Frozen Contract) | **FROZEN** |
| Panel 1D | Truth barrier, primary gates (G1-G3), secondary endpoints | `src/muru/paper_benchmark/g2_contract.py`, `src/muru/paper_benchmark/g3_contract.py`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Frozen Contract) | **FROZEN** |
| **Figure 2** | **Prospective-Governance Timeline & Seals** | Git commit graph, annotated tags, `artifacts/paper_benchmark_amendment_*.json` | `220c9cb` / `a3-4-temporal-provenance-erratum` | Class B (Governance Ledger) | **FROZEN** |
| Panel 2A | Historical Class A → Methods Class B → Results Class C timeline | `PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md`, `MURU_PAPER_BENCHMARK_FREEZE.md` | `d94d2c9` through `220c9cb` | Class A / Class B / Class C | **FROZEN** |
| Panel 2B | Partition seal state tracker (Held-Out & Confirmation sealed) | `artifacts/paper_benchmark_partition_manifest.json`, `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md` | `d94d2c9` / `benchmark-content-freeze-v1` | Class B (Seal State) | **FROZEN** |
| Panel 2C | Amendment lineage (V1, A1, A2, A2.1, A3.1, A3.2, A3.3, A3.4, Erratum) | Amendment documents A1..A3.4, `MURU_MANUSCRIPT_PRE_RESULTS.md` | `d94d2c9` through `220c9cb` | Class B (Amendment Lineage) | **FROZEN** |
| **Figure 3** | **Synthetic Benchmark Architecture** | `src/muru/paper_benchmark/registry.py`, `src/muru/paper_benchmark/generator.py` | `80a7803` / `benchmark-content-freeze-a2-1` | Class B (Frozen Architecture) | **FROZEN** |
| Panel 3A | 20 Case families map & 380-case partition hierarchy | `src/muru/paper_benchmark/registry.py`, `artifacts/paper_benchmark_case_manifest.json` | `d94d2c9` / `benchmark-content-freeze-v1` | Class B (Frozen Taxonomy) | **FROZEN** |
| Panel 3B | Within-case geometry (180 cmpds, 30 scaffolds, 20/5/5 split) | `src/muru/paper_benchmark/generator.py`, `MURU_PAPER_BENCHMARK_FREEZE.md` | `d94d2c9` / `benchmark-content-freeze-v1` | Class B (Frozen Geometry) | **FROZEN** |
| Panel 3C | 5 Truth-family taxonomy mathematical curves | `src/muru/paper_benchmark/generator.py`, `MURU_PAPER_BENCHMARK_CASE_FAMILIES.md` | `80a7803` / `benchmark-content-freeze-a2-1` | Class B (Truth Formulas) | **FROZEN** |
| Panel 3D | Adequacy violation models (M1, M2, M3, F16) & Covariates | `src/muru/paper_benchmark/adequacy.py`, `MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md` | `03cc4d3` / `benchmark-content-freeze-a2` | Class B (Violation Constants) | **FROZEN** |
| **Figure 4** | **Null-Calibration Architecture** | `src/muru/paper_benchmark/calibration_contract.py`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md` | `1194fcb` / `benchmark-content-freeze-a3-2` | Class B (Calibration Protocol) | **FROZEN** |
| Panel 4A | Rationale for complexity-indexed thresholding (unscaled) | `NULL_CALIBRATION.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md` | `c8938e8` / `benchmark-content-freeze-a3-1` | Class B (Design Concept) | **FROZEN** |
| Panel 4B | 100 Structural-null worlds (34/33/33) & 18/6/6 scaffold split | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md` | `1194fcb` / `benchmark-content-freeze-a3-2` | Class B (Frozen Spec) | **FROZEN** |
| Panel 4C | A3.2 Base-target permutation vs rejected design | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md` | `1194fcb` / `benchmark-content-freeze-a3-2` | Class B (Algorithm Repair) | **FROZEN** |
| Panel 4D | Monotonic $Q_{95}$ accumulation & prospective shell | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`, `MURU_TABLE_SHELLS.md` | `c8938e8` / `benchmark-content-freeze-a3-1` | Class C (Shell Only) | **UNRENDERED** |
| **Figure 5** | **Secondary Endpoint Design (A3.4)** | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`, `artifacts/paper_benchmark_amendment_a3_4.json` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Secondary Contracts) | **FROZEN** |
| Panel 5A | Parameter recovery contract ($p_{\text{mass}}, c_{\text{desc}}$ at $\mathbf{x}_0$) | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_3.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` | `71f5369` / `be23b80` | Class B (Derivative Formulas) | **FROZEN** |
| Panel 5B | Predictive equivalence (12 reference frames, 2,160 rows) | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Reference Frames) | **FROZEN** |
| Panel 5C | Predictive approximation vs exact algebra distinction | `MURU_PAPER_BENCHMARK_METRICS.md`, `PHASE3_DECISION.md` | `d94d2c9` / `benchmark-content-freeze-v1` | Class B (Concept) | **FROZEN** |
| Panel 5D | Prospective Held-out secondary outcomes shell | `MURU_TABLE_SHELLS.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class C (Shell Only) | **UNRENDERED** |
| **Figure 6** | **Evidence Hierarchy & Claim Boundaries** | `MURU_CLAIM_MATRIX.md`, `MURU_EVIDENCE_LEDGER.json`, `MURU_MANUSCRIPT_PRE_RESULTS.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Governance Framework) | **FROZEN** |
| Panel 6A | Four-tier evidence classification framework | `MURU_MANUSCRIPT_PRE_RESULTS.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Framework) | **FROZEN** |
| Panel 6B | Ladder of scientific claims (Support → Family → Algebra) | `MURU_CLAIM_MATRIX.md`, `MURU_PAPER_BENCHMARK_METRICS.md` | `d94d2c9` / `be23b80` | Class B (Hierarchy) | **FROZEN** |
| Panel 6C | Historical Class A development observations | `PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md` | Historical commits | Class A (Historical Context) | **HISTORICAL** |
| Panel 6D | Strict governance boundaries & forbidden overclaims | `MURU_CLAIM_MATRIX.md` Section 13 | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Claim Rules) | **FROZEN** |

---

## 2. Tables Traceability Map

| Table | Name | Source File | Source Commit / Tag | Scientific Status | Frozen Status |
|---|---|---|---|---|---|
| **Table 1** | `table_01_case_families` | `src/muru/paper_benchmark/registry.py`, `artifacts/paper_benchmark_case_manifest.json` | `d94d2c9` / `benchmark-content-freeze-v1` | Class B (Case Manifest) | **FROZEN** |
| **Table 2** | `table_02_endpoints` | `MURU_PAPER_BENCHMARK_METRICS.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`, `A3_4.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Endpoint Contract) | **FROZEN** |
| **Table 3** | `table_03_primary_gates` | `src/muru/paper_benchmark/g2_contract.py`, `src/muru/paper_benchmark/g3_contract.py` | `c8938e8` / `benchmark-content-freeze-a3-1` | Class B (Gate Definitions) | **FROZEN (Shell Numerators)** |
| **Table 4** | `table_04_secondary_endpoints` | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`, `MURU_TABLE_SHELLS.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Secondary Definitions) | **FROZEN (Shell Numerators)** |
| **Table 5** | `table_05_calibration_design` | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md`, `src/muru/paper_benchmark/calibration_contract.py` | `1194fcb` / `benchmark-content-freeze-a3-2` | Class B (Calibration Spec) | **FROZEN (Shell Thresholds)** |
| **Table 6** | `table_06_reference_frames` | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`, `artifacts/paper_benchmark_amendment_a3_4.json` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Frame Manifest) | **FROZEN** |
| **Table 7** | `table_07_governance_amendments` | Git log, `artifacts/paper_benchmark_amendment_*.json`, Erratum tag `a3-4-temporal-provenance-erratum` | `220c9cb` / `a3-4-temporal-provenance-erratum` | Class B (Governance Audit) | **FROZEN** |
| **Table 8** | `table_08_reproducibility_dependencies` | `requirements.lock.txt`, `src/muru/paper_benchmark/rc3_provenance.py` | `07c64c8` / `engineering-rc3-1-a3-2` | Class B (Environment Spec) | **FROZEN** |
| **Table 9** | `table_09_claim_boundaries` | `MURU_CLAIM_MATRIX.md`, `MURU_MANUSCRIPT_PRE_RESULTS.md` | `be23b80` / `benchmark-content-freeze-a3-4` | Class B (Claim Matrix) | **FROZEN** |

---

## 3. Verification Confirmations

1. **No Prospective Results Visualized:** All panels/tables requiring calibration outcomes, Development scores, Held-out metrics, or Confirmation results are rendered as formal pre-results design shells with `[PROSPECTIVE RESULT PANEL — DO NOT RENDER]` or `[PROSPECTIVE RESULT TO INSERT]`.
2. **No Fake / Placeholder Data:** No simulated synthetic outcome curves or fictitious scatter plots were fabricated.
3. **No Scientific Code Modified:** All generation scripts operate in read-only mode against frozen benchmark contracts and formulas.
4. **Complete Regenerability:** All 6 figures (SVG, PDF, PNG) and 9 tables (MD, TEX, JSON) can be 100% regenerated by executing:
   - `python3 paper/figures/scripts/generate_all_figures.py`
   - `python3 paper/figures/scripts/generate_all_tables.py`
