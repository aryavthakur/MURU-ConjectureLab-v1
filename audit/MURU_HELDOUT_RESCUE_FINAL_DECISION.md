# MURU Held-out Rescue — Final Forensic Decision

Audit branch `audit/muru-heldout-forensic-rescue`, rooted at
`engineering-rc5-1-heldout-authorization` = `8d87143d4280602323aa33ee0b5481aaef0fb4a8`.

Artifact chain (append-only; nothing prior overwritten or deleted):

| Artifact | SHA-256 |
|---|---|
| `MURU_HELDOUT_RESCUE_AUTHORITY_MATRIX.md` | `2e9b0534ff42fb45ce4e90c8e4854b50c914902c8a0572719be21834ca60a8bf` |
| `muru_heldout_rescue_authority_matrix.json` | `b11af625f72dba3121ec26a2d59cfb8e7ebcf9c0af6aace4922d960bd1f16c5c` |
| `MURU_HELDOUT_RESCUE_RAW_INTEGRITY.md` | `a8d97a5400b4119212a42db54ceda9cc60f4afe885959aa2a96d2f3a60d30e04` |
| `MURU_HELDOUT_RESCUE_INDEPENDENT_RESULT.md` | `2c7b2529dc516a426c5283a33b8b3b4c3cfddbbc2dd9d7d63c65bdcac3799862` |
| `muru_heldout_rescue_independent_result.json` | `b750d5c0af738a1226c293e8d13c3030d1d2c3cfbd7a5fd9dd6834b100416363` |

## 1. Validity classifications

| # | Object | Classification |
|---|---|---|
| A | **Search execution** | **VALID WITH DISCLOSED OPERATIONAL DEVIATION** |
| B | **Raw sealed evidence** | **VALID** |
| C | **Existing post-run analysis** | **INVALID** |
| D | **Existing hostile audit** | **INVALID** |
| E | **Corrected Held-out analysis** | **VALID UNDER FROZEN CONTRACT** (G2, G3, Gate 7, Gate 8, F9 complete; G1 gate verdict determinate, G1 point estimate pending a zero-search recomputation) |

**A** — 7,200 searches, 240 cases, correct commit, correct global plan, injective seeds verified,
zero execution failures. One case (`PB|held_out|F14|r008`) ran 24,216 s against a 117 s median;
single provenance entry, no re-run, scientifically inert (F14 carries no primary endpoint and the
case is UNEVALUABLE at A1).

**B** — 482/482 sealed files re-hash correctly; manifest and global-plan digests recompute; no raw
file modified after sealing. Decisively: **re-running the frozen acceptance predicate over all 240
cases reproduces the stored `acceptance_status` and `acceptance_gate_reached` with 0
disagreements.** The raw records are faithful to the frozen A3.5 contract.

**C** — every primary quantity deviates, always permissively; the reported verdict is inverted.

**D** — 6 checkpoints claimed as 7, none independent, two are anti-checks that certify the defect.

## 2. Corrected Held-out outcome under the frozen contract

| Endpoint | Denominator | Result | Gate | Verdict |
|---|---|---|---|---|
| **G1** scalar competence | **164** | ≤ 67 competent; Wilson lower ≤ 0.336234 | ≥ 0.70 | **FAIL** (determinate) |
| **G2** family recovery | **144** | 4 successes; Wilson lower 0.010854 | ≥ 0.70 | **FAIL** |
| **G3** structural safety | **36** | 26 violations; Wilson upper 0.841518 | ≤ 0.15 | **FAIL** |

| Gate | Result |
|---|---|
| **Gate 7** (ceiling) | 27 reached, **26 pass**, 1 fail; 26 via `ceiling_pass`, **0 via waiver** |
| **Gate 8** (4 hard rungs) | 26 reached, **25 pass**, 1 fail (`F10_NEGATIVE_CONTROL`) |
| **STRUCTURAL_ACCEPTED** | **25 of 240** (an acceptance count, not an endpoint rate) |

Secondary: F9 `PASS` 26/26 among Gate-8 reachers, non-gating,
`NOT_PROVEN_FOR_HARD_GATE`; **may not be cited as evidence of validated robustness** (A3.5 §6.9.4).
Execution-failure disclosure: 0 poisoned cases in every endpoint.

**All three primary endpoints fail.** The dominant driver is A1 adequacy, not any gate subtlety:
154 of 240 cases terminate at `a1_adequacy`, and 97 of the 164 G1 cases are `BOUNDARY_LIMITED`.

## 3. Provenance disposition

The following are **preserved, not deleted**, and marked:

**`SUPERSEDED - POST-RUN ANALYSIS CONTRACT DRIFT`**

- `results/held_out/held_out_formal_analysis.json`
- `results/held_out/held_out_hostile_audit_report.md`
- `src/muru/paper_benchmark/held_out_analyzer.py`
- `src/muru/paper_benchmark/independent_recomputation.py`
- `src/muru/paper_benchmark/hostile_reviewer.py`
- `src/muru/paper_benchmark/pipeline.py`
- `scripts/run_post_held_out_pipeline.py`

Neither superseded output file is inside the seal, so superseding them touches no sealed evidence.

**Authoritative**: the five rescue artifacts listed above, plus the sealed raw evidence
(`records/`, `seed_records/`, `provenance/`, `execution_manifest.json`,
`execution_seal_receipt.json`) and the frozen authorities (A3.5, A3.6, RC5.1 source,
`artifacts/muru_rc5_global_science_plan.json`).

## 4. Whether searches must be rerun

**No. No search, and no seed, requires rerunning.** The defect is entirely downstream of a raw
execution that is cryptographically intact and contract-faithful. Rerunning would consume the
partition a second time for no scientific gain and is expressly forbidden.

The one outstanding quantity — G1's exact competent count within its proven ≤ 67 bound — is
**search-independent** (A3.5 §8.2) and recomputable from frozen case content and the frozen
training-only `Phi` with **zero searches**. It cannot change the G1 gate verdict, which is already
determinate.

## 5. Required code repair — specification for a separate session

Substantive repair is required and is **deliberately not performed here**. Specification for a
separate Claude Opus 5 Ultracode session:

**Objective.** Replace the post-run analysis layer with one that invokes frozen scorers rather
than reimplementing them.

**Hard requirements.**

1. **Never compute an endpoint denominator from `len(case_ids)`.** Build each population via
   `registry.endpoint_applies_to_variant(endpoint, variant)` and assert its size against
   `registry.endpoint_case_count(endpoint)` before scoring.
2. **Invoke the frozen scorers directly** — `rc5_g1_bridge.score_g1`, `rc3_scoring.score_g2`,
   `rc3_scoring.score_g3`, `g2_contract.evaluate_g2_event`, `g3_contract.classify_g3_event`,
   `structural_acceptance.evaluate_structural_acceptance`, `structural_acceptance.check_gate8`.
   Their length assertions are the intended guard and must be allowed to fire.
3. **Gate 7** is the ceiling test at position 7 (`ceiling_pass OR ceiling_waiver`), never
   structural acceptance and never a falsification cascade.
4. **Gate 8** is `check_gate8` over `{F1, F4, F7, F10}`, fail-closed. **G1 must not appear in it.**
5. **G3** must count violations over 36 with Wilson **upper** ≤ 0.15, with UNEVALUABLE ⇒ VIOLATION.
6. **A1 adequacy**: only `M0_NOT_REJECTED` is permitted. `BOUNDARY_LIMITED` is UNEVALUABLE.
7. **F9** reports `f9_stress_test_result` / `f9_stress_test_metric`, non-gating, with the A3.5
   §6.9.4 drafting guard attached.
8. **Decision rule**: G1 Wilson lower ≥ 0.70 AND G2 Wilson lower ≥ 0.70 AND G3 Wilson upper ≤ 0.15.
   No existence tests.
9. **Persist G1 observables** (`g_spearman`, `trajectory_mae`, `per_energy_mean_mae`,
   `m0_accepted`) in a record-schema successor, so G1 is auditable from sealed evidence in future
   partitions. Recompute G1 for Held-out **without any search**.
10. **Branch on no field absent from the record schema.** Add a schema-conformance test asserting
    that every key read by the analyzer exists in `muru-rc5-case-record-2.0.0`.
11. A genuine independent recomputation **must not import the primary analyzer**, must be written
    against the frozen contract text, and should be authored before outcomes are inspected.
12. Hostile review must instantiate genuinely independent lenses that reconstruct endpoint
    populations, Gate 7, and Gate 8 from frozen authority — never assert a hard-coded 240.

**Acceptance test.** The repaired analyzer must reproduce, exactly, the sealed independent result
`b750d5c0af738a1226c293e8d13c3030d1d2c3cfbd7a5fd9dd6834b100416363` for G2, G3, Gate 7, Gate 8,
F9, and the failure-stage distribution, and must satisfy the G1 bound (successes ≤ 67, gate FAIL).

## 6. Challenge

**Challenge remains prohibited and was not touched.** No authorization granted, no
`AUTHORISED_PARTITIONS` modification, no A3.7, no RC5.2, no Challenge outcome generated or scored,
no Confirmation opened.

Challenge is **not** safe to consider next. The Held-out analysis contract must first be repaired,
the corrected analysis frozen under review, and the three primary-endpoint failures adjudicated
scientifically. Opening Challenge against a benchmark whose Held-out endpoints all fail — and
whose failure was until now masked by a defective analyzer — would consume a second sealed
partition before the first has been correctly interpreted.

---

**HELD-OUT RESCUE COMPLETE - RAW EXECUTION VALID, CORRECTED ANALYSIS FROZEN**
