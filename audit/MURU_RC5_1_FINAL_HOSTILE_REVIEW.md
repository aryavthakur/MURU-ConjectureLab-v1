# MURU Engineering RC5.1 — Final Hostile Review

**Document ID**: `MURU-AUDIT-RC5-1-FINAL-HOSTILE-REVIEW-01`  
**Date**: 2026-08-16  
**Engineering Release**: RC5.1 (`engineering-rc5-1-heldout-authorization`)  
**Parent Engineering Freeze**: `7cdd5a6b74b1051935ad0eb86c7d8770cd725236` (tag `engineering-rc5-a3-5`)  
**Parent Science Freeze**: `327b55536b7d6ee8b8693091fa7180491e2c0a38` (tag `benchmark-content-freeze-a3-6`)

---

## 1. Executive Summary

An engineering hostile review was conducted to verify that the implementation delta of RC5.1 is strictly restricted to partition authorization expansion as mandated by Amendment A3.6.

**Overall Disposition**: **UNANIMOUS PASS (4/4 Lenses PASS, 0 BLOCK)**

---

## 2. Review Lenses

### Lens 1: Scientific Byte Equivalence
- **Scope**: Verify that all scientific and governance modules are byte-identical to `engineering-rc5-a3-5`.
- **Finding**: Evaluated SHA-256 digests across all 27 scientific and governance modules (`identity_contract.py`, `seed_band_registry.py`, `structural_acceptance.py`, `rc3_acceptance.py`, `rc3_ceiling.py`, `rc3_record.py`, `rc5_adapter.py`, `rc5_adequacy.py`, `rc5_case_scoring.py`, `rc5_estimate.py`, `rc5_falsify.py`, `rc5_g1_bridge.py`, `rc5_manifest.py`, `rc5_runner.py`, `rc5_seeds.py`, `rc5_selection.py`, `rc5_store.py`, `registry.py`, `adequacy.py`, `calibration_contract.py`, `g2_contract.py`, `g3_contract.py`, `generator.py`, `governance.py`, `preflight.py`, `protocol.py`, `truth.py`). Zero byte changes detected.
- **Verdict**: **PASS**

### Lens 2: Authorization Scope Conformance
- **Scope**: Verify `rc5_authorization.py` authorizes only `development` and `held_out`.
- **Finding**: `AUTHORISED_PARTITIONS = frozenset({"development", "held_out"})`. `challenge` raises `PartitionNotAuthorised`. `confirmation` raises `ValueError("unknown partition")`.
- **Verdict**: **PASS**

### Lens 3: Test Verification
- **Scope**: Focused test suite execution.
- **Finding**: 81 unit tests across runner, preflight, manifest, and partition identity pass cleanly (100%).
- **Verdict**: **PASS**

### Lens 4: Quarantine & Unopened Partitions
- **Scope**: Confirm Challenge remains unexecutable and Confirmation remains sealed.
- **Finding**: Verified.
- **Verdict**: **PASS**

---

## 3. Decision

RC5.1 is approved for engineering freeze.
