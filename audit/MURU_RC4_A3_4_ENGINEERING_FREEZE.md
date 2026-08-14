# MURU RC4 A3.4 Engineering Freeze Record

**Classification:** `ENGINEERING_RELEASE_CANDIDATE_FREEZE`
**Tag:** `engineering-rc4-a3-4`
**Status:** `FROZEN_VALID`
**Branch:** `eng/muru-rc4-a3-4`

## Purpose

This document and its paired canonical ledger `audit/muru_rc4_a3_4_engineering_freeze.json` record the formal engineering freeze of MURU Release Candidate 4 (RC4), incorporating Amendment A3.4 secondary endpoint contracts (Parameter Recovery and Predictive Equivalence), the additive outcome-blind temporal provenance erratum, the frozen metadata attestation advisory, and the recursive static sealed-boundary integrity gate.

No calibration outcome, Development partition, Held-out partition, or Confirmation partition was opened or evaluated during this engineering cycle.

## Lineage and Provenance Bindings

| Item | Identifier / Digest | Note |
|---|---|---|
| RC3.1 exact parent commit | `07c64c862cb32a306f5081582dacf73e09211c0a` | Tag `engineering-rc3-1-a3-2` |
| A3.4 science freeze commit | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` | Tag `benchmark-content-freeze-a3-4` |
| A3.4 merge commit | `5055f69097aa0c6ce2ded6a3e57f0edfaea69faf` | Lineage merge into RC4 worktree |
| Temporal provenance erratum | `220c9cb679e03865f1b2a02b975397de9f4c7b46` | Tag `a3-4-temporal-provenance-erratum` |
| Reference aggregate digest | `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44` | 12 frames, 2,160 rows |
| Protected science paths count | `31` | All 31 blobs byte-identical to `be23b80` |
| Recorded aggregate convention | `d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8` | No terminal newline |
| Derived aggregate convention | `55ebd0b92ba07ad828983f4e7add5163f49377255dfcf47bdd9f1af98174f16a` | Terminal newline |

## Implementation Architecture

1. **A3.4 Reference Distribution Contract (`src/muru/paper_benchmark/a34_contract.py`)**:
   - Implements prospective reference covariates for 12 frames (`PB|PRED_EQUIV|FRAME|000` through `011`), 180 rows/frame (30 scaffolds x 6 compounds) = 2,160 rows.
   - Verifies per-frame SHA-256 digests and the canonical aggregate SHA-256 digest `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`.
   - Strictly covariate-only via frozen `_synthetic_compounds` primitive.

2. **Parameter Recovery Scorer (`src/muru/paper_benchmark/a34_parameter_recovery.py`)**:
   - Evaluates symbolic candidate derivative at neutral anchor $(m=250, d=0, d_2=0, \text{distractor}=0, \text{corr\_distractor}=0)$.
   - Base normalization: $p_{\text{mass}} = \frac{250}{\text{base}} \left.\frac{\partial f}{\partial m}\right|_{\text{anchor}}$.
   - Descriptors: $c_{\text{desc}} = \frac{1}{\text{base}} \left.\frac{\partial f}{\partial d}\right|_{\text{anchor}}$ (or second derivative for F10, or $\times 3$ for F18).
   - Tolerances: $\pm 0.15$ for $p_{\text{mass}}$, $\pm 0.10$ for $c_{\text{desc}}$ without epsilon widening.
   - Fixed denominators: 156 for mass recovery / joint recovery, 84 for descriptor coupling. No gating. Wilson 95% confidence intervals.

3. **Predictive Equivalence Scorer (`src/muru/paper_benchmark/a34_predictive_equivalence.py`)**:
   - Evaluates parsed candidate on 2,160 reference rows.
   - Valid subset $V$: $\hat{y} > 0 \land \text{isfinite}(\hat{y}) \land y_{\text{true}} > 0 \land \text{isfinite}(y_{\text{true}})$.
   - Requires $|V| \ge 2,150$ ($\text{valid\_fraction} \ge 0.995$).
   - Computes optimal positive scalar $c^* = \frac{y_{\text{true}} \cdot \hat{y}}{\hat{y} \cdot \hat{y}} > 0$.
   - Metric thresholds: $\text{REL\_RMSE} = \frac{\text{RMSE}_V}{\text{RMS}(y_{\text{true}})_V} \le 0.05$ and Pearson $r \ge 0.990$.
   - Fails closed with $r=0.0$ on zero-variance.
   - Fixed denominator: 144 across the 12 non-F07 parameter recovery families.

4. **Candidate Binding Sidecar (`src/muru/paper_benchmark/a34_record.py`)**:
   - Binds source case record digest, candidate expression grammar digest, truth snapshot digest, contract identity, reference digest, and score result into immutable canonical JSON.

5. **Static Sealed-Boundary Integrity Gate (`scripts/pb_35_a3_4_integrity.py`)**:
   - Byte-pins all 31 protected science files against freeze commit `be23b80`.
   - AST-based recursive static import analyzer: traverses internal import graph, fails closed on forbidden modules, forbidden APIs, unbounded packages, relative star imports (`from . import *`), parent-package escapes (`..`, `...`), and module escapes.

## Independent Engineering Review Findings

### Reviewer A: Science-to-Code Conformance
- **Verdict: PASS (Clean)**
- Verified exact reference frame IDs `PB|PRED_EQUIV|FRAME|000`–`011`, 12 frames, 2,160 rows.
- Verified aggregate reference digest `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`.
- Verified parameter anchor `(250, 0, 0, 0, 0)` and derivatives for all 13 families.
- Verified parameter tolerances (0.15 / 0.10) and fixed denominators (156 / 84).
- Verified predictive valid threshold (2,150 / 2,149 boundary), positive scalar $c^* > 0$, relative RMSE $\le 0.05$, Pearson $r \ge 0.990$, and denominator 144.
- Verified no coefficient refit, no intercept alignment, no structure refit, and no candidate reselection.

### Reviewer B: Numerical and Symbolic Adversary Analysis
- **Verdict: PASS (Clean)**
- Tested algebraically equivalent expressions, rationalized decimal literals, and extreme positive scales ($10^{-12}$ to $10^{12}$).
- Verified negative scale failure ($c^* \le 0$), constant candidate zero-variance failure ($r=0.0$), NaN/Inf rejection, and near-threshold RMSE/Pearson boundaries.
- Verified F09 no-pole evaluation on reference distribution and immutability of candidate binding sidecar.

### Reviewer C: Contamination and Reproducibility
- **Verdict: PASS (Clean)**
- Verified no calibration outcome, Development partition, Held-out partition, or Confirmation partition was opened or executed.
- Verified reference distribution contains covariates only.
- Verified recursive static import guard prevents prospective outcome leakage.
- Verified all 31 protected science paths match `be23b80` byte-for-byte.

## Test Summary

- **Targeted RC4 Suite**: 90 passed, 0 failed.
- **Paper Benchmark Suite**: 663 passed, 0 failed.
- **Full Repository Suite (excluding pre-existing fixture-dependent tests)**: 988 passed, 60 skipped, 0 failed.
- **Pre-existing Historical Fixture Limitation**: 3 failures / 14 errors in `test_ov_blinding.py` and `test_ov_pipeline.py` strictly due to missing untracked historical file `artifacts/p2_compounds.parquet`.
