# MURU ConjectureLab v1 — A3.5 Pre-Freeze Hostile Review Execution Template
**Document ID:** `MURU-AUDIT-A35-PREFREEZE-REVIEW-01`
**Classification:** `PROSPECTIVE_HOSTILE_AUTHORIZATION_REVIEW`
**Status:** TEMPLATE / EXECUTION PROTOCOL — fill in once an actual A3.5 draft exists. Do not use this to draft A3.5.
**Scored against:** [`MURU_A3_5_PRE_FREEZE_REVIEW_MATRIX.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_A3_5_PRE_FREEZE_REVIEW_MATRIX.md) / [`muru_a3_5_pre_freeze_review_matrix.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/muru_a3_5_pre_freeze_review_matrix.json)
**Governing Authorities:** Amendments A3.1–A3.4 and the RC5 Execution Semantics Authority Audit (`audit/MURU_RC5_EXECUTION_SEMANTICS_AUTHORITY_AUDIT.md`)

---

## 1. Mandate

This is the adversarial protocol an auditor executes against a real A3.5 draft, before RC5 engineering (the executable Development/Held-out case-execution path) is authorized. Zero trust: no claim of conformance in the draft's own prose is accepted without independent verification.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ HOSTILE GATE DECISION:                                                                 │
│ [   ] AUTHORIZE RC5 ENGINEERING     (All 34 BLOCKING criteria PASS)                    │
│ [   ] REFUSE RC5 ENGINEERING        (One or more BLOCKING criteria FAIL or NOT_PROVEN) │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**A3.5 draft under review:** `______________________________` (path)
**A3.5 draft commit hash:** `______________________________`
**Reviewer:** `______________________________`
**Review date (UTC):** `YYYY-MM-DD`

---

## 2. Pre-Review Integrity Checks (run before scoring any criterion)

```bash
# 1. Confirm A3.5 does not predate its own claimed creation commit (R1.4)
git log -1 --format="%H %aI" -- <A3_5_DOCUMENT_PATH>

# 2. Confirm no execution artifact predates the A3.5 freeze commit (R1.1)
git log --all --format="%H %aI %s" -- artifacts/development artifacts/held_out | tail -20

# 3. Confirm Development/Held-out remain uninspected (R1.3)
find artifacts -iname "*held_out*" -newer <A3_5_DOCUMENT_PATH> 2>/dev/null
git log --since="<A3_5_DRAFTING_START>" --all -- 'artifacts/inputs/held_out.jsonl' 'artifacts/inputs/development.jsonl'

# 4. Re-run the RC5 execution semantics authority audit's own method against A3.5
# to confirm the 12 UNFROZEN_SCIENTIFIC_DECISION items were actually addressed in code/text,
# not merely mentioned.
grep -n "valid_r2\|invalid_fraction\|selection_count" <A3_5_DOCUMENT_PATH>
```

- **Auditor Findings:**
  - *A3.5 creation commit matches claim:* `[ YES | NO ]`
  - *No execution artifact predates freeze:* `[ YES | NO ]`
  - *Zero Development/Held-out inspection evidence:* `[ CONFIRMED | CONTAMINATION SUSPECTED ]`

---

## 3. Evidence Ledger — 37 Criteria

| # | Criterion | Verdict | Blocker? | Evidence Location |
|---|---|---|---|---|
| R1.1 | Freeze-before-execution ordering | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R1.2 | No historical-performance-informed rule choice | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R1.3 | Development/Held-out non-inspection | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R1.4 | Amendment self-binds creation commit | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R1.5 | Environment/hardware footprint recorded | `[PASS / FAIL / NOT_PROVEN]` | `NONBLOCKING` | |
| R2.1 | `valid_r2` single deterministic definition | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R2.2 | `selection_count` / cross-seed selection pure function | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R2.3 | Zero remaining `UNFROZEN_SCIENTIFIC_DECISION` items | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R2.4 | New DoF preserve calibrated gate meaning | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R3.1 | Exact target matches scientific estimand | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R3.2 | Symbolic covariates bound to one rule | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R3.3 | Selection not tuned for G2 | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R3.4 | Selection uniform across families/partitions | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R4.1 | Adapter builds train-fold-only | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R4.2 | No validation/test leakage into Phi or fitting | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R4.3 | Split scope stated per new computation | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R5.1 | Search-seed derivation is a pure function | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R5.2 | Namespace disjoint, reseeding prohibited | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R5.3 | Band disjointness import-time checkable | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R5.4 | 30-seeds/case count unchanged | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R5.5 | PID/inode telemetry descriptive only | `[PASS / FAIL / NOT_PROVEN]` | `NONBLOCKING` | |
| R6.1 | Single `invalid_fraction` numerator/denominator | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R6.2 | Uses the frozen FM-07 strict evaluator | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R6.3 | Frozen 0.005 threshold unchanged | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R7.1 | All six rungs get a concrete pass/fail procedure | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R7.2 | Rung membership/order unchanged | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R7.3 | No rung is vacuously satisfiable | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R8.1 | Search settings demonstrated identical, not asserted | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R8.2 | Complexity computed identically | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R8.3 | New computations shown compatible with calibration | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R9.1 | Zero partition-conditional branching | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R9.2 | Failure/resume semantics partition-independent | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R9.3 | Execution manifest locks identical settings | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R9.4 | Hardware/OS identity not required | `[PASS / FAIL / NOT_PROVEN]` | `NONBLOCKING` | |
| R10.1 | Exact-algebra descriptive-only disposition restated | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R10.2 | No silent promotion without prospective rationale | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |
| R10.3 | Consistent "law" representation with primary search | `[PASS / FAIL / NOT_PROVEN]` | **`BLOCKING`** | |

---

## 4. Detailed Forensic Sections (fill in per domain)

### 4.1 R1 — Prospective governance / temporal cleanliness
- *A3.5 freeze commit:* `________________________________________`
- *First execution artifact timestamp (if any exists):* `________________________________________`
- *Ordering satisfied (freeze precedes execution):* `[ YES | NO | N/A — no execution artifacts yet ]`
- *Any semantic choice whose rationale references an observed result:* `[ NONE FOUND | FOUND: _____________ ]`
- *Development/Held-out inspection evidence:* `[ NONE FOUND | FOUND: _____________ ]`

### 4.2 R2 — Statistical degrees of freedom
- *`valid_r2` definition as stated in A3.5:* `________________________________________`
- *Matches calibration's actual computed quantity:* `[ YES | NO | UNVERIFIABLE ]`
- *`selection_count` equivalence rule as stated:* `________________________________________`
- *Count of the 12 RC5-audit `UNFROZEN_SCIENTIFIC_DECISION` items resolved:* `____ / 12`
- *Items still unresolved:* `________________________________________`

### 4.3 R3 — Symbolic-regression target and selection bias
- *Stated symbolic target representation:* `________________________________________`
- *Prospective rationale given (quote):* `________________________________________`
- *Covariate set/order/representation as stated:* `________________________________________`
- *Selection-rule rationale references G2/G3 outcome:* `[ NO | YES: _____________ ]`

### 4.4 R4 — Fold-local / non-transductive construction
- *Adapter fold-locality claim:* `[ TRAIN-ONLY | AMBIGUOUS | TRANSDUCTIVE ]`
- *Non-transductive canary specified:* `[ YES | NO ]`
- *Any fitting step reading validation/test rows:* `[ NONE FOUND | FOUND: _____________ ]`

### 4.5 R5 — Seed identity and randomness
- *Seed derivation formula as stated:* `________________________________________`
- *Declared Development/Held-out seed band range:* `________________________________________`
- *Disjoint from smoke (1.9e9+) and calibration (2.11e9–2.147e9):* `[ YES | NO | OVERLAP FOUND ]`
- *Reseeding explicitly prohibited:* `[ YES | NO ]`
- *`assert_seed_band_separation()`-style extension specified:* `[ YES | NO ]`

### 4.6 R6 — `invalid_fraction` and strict-evaluator consistency
- *Numerator as stated:* `________________________________________`
- *Denominator as stated:* `________________________________________`
- *Validity check routes through frozen evaluator:* `[ YES | NO | SEPARATE PATH FOUND ]`
- *Threshold value used:* `____` (must equal `0.005`)

### 4.7 R7 — Falsification-rung completeness
```bash
# Verify rung set/order against the frozen enum
python -c "
from muru.paper_benchmark.structural_acceptance import FALSIFICATION_RUNG_ORDER
print(FALSIFICATION_RUNG_ORDER)
"
```
| Rung | Tolerance/perturbation stated | Pass/fail rule stated | Worked failing example given |
|---|---|---|---|
| F1_REPRODUCIBILITY | | | |
| F4_COMPOUND_HOLDOUT | | | |
| F5_SCAFFOLD_HOLDOUT | | | |
| F7_INFLUENCE_DROP | | | |
| F9_ENERGY_SUBSET | | | |
| F10_NEGATIVE_CONTROL | | | |

### 4.8 R8 — Calibration compatibility
```bash
# Verify shared settings object, not a re-declared copy
python -c "
from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS
print(SEARCH_SETTINGS)
"
```
- *Real-search settings source:* `[ SHARED IMPORT | RE-DECLARED COPY | UNSPECIFIED ]`
- *Complexity source for real search:* `[ SAME PySR FIELD AS CALIBRATION | DIVERGENT | UNSPECIFIED ]`
- *Compatibility argument given for `valid_r2`/`invalid_fraction`/`selection_count`:* `[ YES | NO ]`

### 4.9 R9 — Development/Held-out path identity
- *Partition-conditional branches found in A3.5's procedures:* `[ NONE | FOUND: _____________ ]`
- *Failure/resume mechanism shared across partitions:* `[ YES | NO | DIVERGENT ]`
- *Execution manifest settings-digest computation partition-independent:* `[ YES | NO | UNSPECIFIED ]`

### 4.10 R10 — Exact-algebra endpoint disposition
- *Exact-algebra role as stated in A3.5:* `[ DESCRIPTIVE-ONLY (unchanged) | PROMOTED TO BLOCKING: rationale ___________ ]`
- *Target representation used for exact-algebra scoring vs R3.1's primary target:* `[ SAME | DIFFERENT — mapping stated: ___________ | DIFFERENT — unmapped ]`

---

## 5. Complete Defect Ledger

| Defect ID | Criterion | Finding | Must Fix Before Authorization? |
|---|---|---|:---:|
| | | | |

---

## 6. Formal Authorization Sign-Off Block

| Role | Name / Identifier | Attestation Statement | Date (UTC) | Signature / Digest |
|---|---|---|---|---|
| **Lead Hostile Auditor** | `____________________` | *I certify all 34 BLOCKING criteria were independently audited against A3.5's actual text/code, not its self-description.* | `YYYY-MM-DD` | `____________________` |
| **Scientific Governance Custodian** | `____________________` | *I certify no A3.5 semantic was chosen with reference to an observed Development, calibration, or historical result, and Development/Held-out remain sealed.* | `YYYY-MM-DD` | `____________________` |

```
FINAL REVIEW STATUS:        [ REFUSED | AUTHORIZED ]
A3.5 DRAFT COMMIT:          [ ________________________________ ]
BLOCKING CRITERIA PASSED:   [ ____ / 34 ]
NONBLOCKING NOTES RECORDED: [ ____ / 3  ]
```
