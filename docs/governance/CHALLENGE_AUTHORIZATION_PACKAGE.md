# MURU Prospective Challenge Authorization Package (Pre-Results Draft)

**Document ID**: `MURU-GOV-CHALLENGE-PROSPECTIVE-AUTH-01`  
**Status**: `PREPARED (OUTCOME-INDEPENDENT)`  
**Trigger Condition**: To be formally authorized only after Held-out partition execution is complete, sealed, analyzed, and audited.  
**Governing Authority**: Amendment A3.5 / A3.6 Science Contract & Engineering RC5.1.

---

## 1. Executive Summary & Authorization Scope

Under the frozen prospective benchmark design (Amendment A3.5, Section 8), the synthetic benchmark comprises three partitioned datasets:
1. **Development**: 80 cases (Completed)
2. **Held-out**: 240 cases (Active / In Execution)
3. **Challenge**: 60 cases (Quarantined / Awaiting prospective authorization)

This package prepares the outcome-independent authorization for the Challenge partition, ensuring that no scientific parameter, seed, or threshold is modified post-hoc.

---

## 2. Frozen Challenge Partition Inventory

- **Case Count**: Exactly **60 cases** across all **20 families** (`F01` through `F20`).
- **Realisations per Family**: 3 cases per family (`r000`, `r001`, `r002`).
- **Search Seeds**: Exactly **1,800 searches** (30 seeds per case).
- **Seed Domain**:
  - Base: `2,100,009,600`
  - Max: `2,100,011,399`
  - Fully disjoint from Development, Held-out, and Calibration seed bands.
- **Search Settings**: 100% byte-identical to frozen settings (`FROZEN_SETTINGS_DIGEST`).
- **Null Threshold Table**: 100% byte-identical to frozen null calibration (`9950b964...`).

---

## 3. Engineering Permission Delta (RC5.2)

To authorize execution of the Challenge partition:
1. `src/muru/paper_benchmark/rc5_authorization.py`:
   ```python
   AUTHORISED_PARTITIONS: frozenset[str] = frozenset({"development", "held_out", "challenge"})
   ```
2. Build Challenge Partition Pre-Execution Manifest (`results/challenge/execution_manifest.json`):
   - Derives purely from the frozen Layer-1 Global Science Plan.
   - Zero parameter injection.
3. Runner Invocation:
   ```bash
   python scripts/run_challenge_production.py --workers 4
   ```

---

## 4. Confirmation Boundary Clause

- **Confirmation Partition**: The Confirmation partition (real-world experimental data / prospective LC-MS/MS qualification) remains **STRICTLY SEALED** and independent of synthetic benchmark execution.
- No synthetic benchmark outcome opens the Confirmation seal automatically.

---

## 5. Formal Declaration

```
======================================================================
MURU PROSPECTIVE CHALLENGE AUTHORIZATION PACKAGE: READY FOR TRIGGER
======================================================================
```
