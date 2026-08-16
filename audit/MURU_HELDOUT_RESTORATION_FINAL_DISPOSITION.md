# MURU Held-out — Restoration Final Disposition

Branch `eng/muru-heldout-analysis-restoration`, rooted at `b16d274`, whose parent
`8d87143d4280602323aa33ee0b5481aaef0fb4a8` is the commit the 7,200 Held-out searches ran under.

## 1. Disposition

| Object | Classification |
|---|---|
| Search execution (7,200 searches, 240 cases) | **VALID WITH DISCLOSED OPERATIONAL DEVIATION** — unchanged from the forensic rescue |
| Raw sealed evidence (482 files) | **VALID** — re-verified independently by this restoration |
| Superseded post-run analysis layer | **SUPERSEDED - POST-RUN ANALYSIS CONTRACT DRIFT** — preserved, not deleted |
| **Restored Held-out analysis** | **VALID AND COMPLETE UNDER THE FROZEN CONTRACT** |

The forensic rescue left one quantity open: G1's exact competent count, provable only as ≤ 67. That
is now closed. **The Held-out analysis is complete on every primary endpoint and every gate.**

## 2. Frozen scientific result

| Endpoint | Denominator | Result | Gate | Verdict |
|---|---|---|---|---|
| **G1** scalar competence | 164 | 67 competent, Wilson lower 0.336233 | ≥ 0.70 | **FAIL** |
| **G2** family recovery | 144 | 4 successes, Wilson lower 0.010854 | ≥ 0.70 | **FAIL** |
| **G3** structural safety | 36 | 26 violations, Wilson upper 0.841518 | ≤ 0.15 | **FAIL** |

**All three primary endpoints fail, independently and by wide margins.** No single correction would
change any verdict: G1 misses by 0.36, G2 by 0.69, G3 by 0.69.

| Gate | Result |
|---|---|
| Gate 7 (ceiling, position 7) | 27 reached, 26 pass, 0 via waiver |
| Gate 8 (four hard rungs, fail-closed) | 26 reached, 25 pass; sole failure `F10_NEGATIVE_CONTROL` |
| STRUCTURAL_ACCEPTED | 25 of 240 — an acceptance count, never an endpoint rate |

F5 superseded, absent from all 240 records. F9 secondary and non-gating, PASS 26/26 among Gate-8
reachers, `NOT_PROVEN_FOR_HARD_GATE`, **not citable as evidence of validated robustness**.
Execution-failure-poisoned cases: 0 in every endpoint.

## 3. Dominant failure mechanism

**A1 adequacy, not gate subtlety and not scalar-estimation quality.**

154 of 240 cases terminate at `a1_adequacy`. Within G1's 164, 97 are `BOUNDARY_LIMITED` — UNEVALUABLE
under the frozen contract. The exact G1 recovery makes the mechanism unambiguous:

- Of the 67 cases whose A1 adequacy was established, **67 passed both continuous conjuncts.** Not
  one failed on `g_spearman` or on `trajectory_mae`.
- Of the 97 that were not established, **87 would have passed both** had adequacy been established.
- Cases failing on `g_spearman` alone: **0**. On `trajectory_mae` alone: **0**. Contract failures:
  **0**.

G1 does not fail because the scalar pipeline is inaccurate. It fails because A1 could not establish
adequacy for 59% of the population.

G3's failure is dominated by the same mechanism through the conservative `UNEVALUABLE ⇒ VIOLATION`
rule: all twelve F20 cases are violations, and the violation count is driven by unevaluability
rather than by observed unsafe acceptance (UNSAFE events: 0).

G2 is the one endpoint that fails on its own terms: 4 successes from 144 with 103 outright failures
and 37 unevaluable. Symbolic family recovery failed on this partition independently of adequacy.

## 4. Discharge of the 12 rescue requirements

| # | Requirement | Discharged by | Evidence |
|---|---|---|---|
| 1 | populations from the registry, never `len(case_ids)` | `heldout_endpoint_populations` | 164/144/36 asserted by two frozen routes; lens 2 rebuilds by a third |
| 2 | invoke frozen scorers; let length assertions fire | `heldout_contract_analysis` | `test_frozen_scorers_reject_a_240_length_sequence` |
| 3 | Gate 7 is the ceiling test at position 7 | `evaluate_gate7` | reconstructed independently by lens 6 |
| 4 | Gate 8 is `check_gate8` over 4 rungs; no G1 | `evaluate_gate8` | AST test: no G1 symbol reachable; counterfactual shows "Gate 7 AND G1" differs |
| 5 | G3 violations over 36, Wilson upper, UNEVALUABLE ⇒ VIOLATION | `score_g3_endpoint` | 7-variant counterfactual in lens 5 |
| 6 | only `M0_NOT_REJECTED` is adequate | never re-encoded; frozen path only | `test_boundary_limited_is_unevaluable_not_adequate` |
| 7 | F9 reported, non-gating, with the drafting guard | `report_f9` | guard string asserted; F9 FAIL shown not to reject |
| 8 | three Wilson gates conjoined; no existence tests | `FrozenDecision` | `decision_passed` absent from the entire module |
| 9 | persist G1 observables; recompute without search | `heldout_g1_recovery` | 164 cases, 0 searches, PySR never imported, 164/164 content identity |
| 10 | branch on no absent field; schema-conformance test | `rc5_record_payload` | `require()` has no default; AST test forbids 2-arg `.get()` |
| 11 | genuinely independent recomputation | `heldout_independent_scoring` | import guard + AST test + the guard's own failure test; **produced a real disagreement on first run** |
| 12 | genuinely independent hostile lenses | `heldout_hostile_lenses` | 7 lenses, 66 checks, 13 mutation tests proving each can fail |

Requirement 9's forward half — a record-schema successor persisting the four G1 observables — is
**specified but not exercised**, because exercising it would require executing a partition and no
partition may be rerun. Recorded as a forward obligation, not as discharged.

## 5. Acceptance test

The rescue decision required the repaired analyzer to reproduce the sealed independent result
`b750d5c0d5…` exactly for G2, G3, Gate 7, Gate 8, F9 and the failure-stage distribution, and to
satisfy the G1 bound.

**Met.** All eight determinate quantities reproduce exactly, including case-level identity of the
G2 success set, the Gate-7 failing case, the Gate-8 failing case and the structural-acceptance
family split. G1 satisfies the bound with equality (67 ≤ 67) and fails the gate. The forensic result
was sealed before this repair was written, so the agreement cannot have been tuned toward.

One numerical difference is disclosed: G1's Wilson lower is `0.336233` here versus `0.336234` in the
forensic artifact, because the rescue hand-computed that one interval at `z = 1.959963984540054`
while the frozen scorers use `z = 1.96`. Immaterial (1.3 × 10⁻⁶ against a 0.36 margin); the frozen
scorer's value is reported.

## 6. Governance attestations

- **No search rerun.** `searches_run = 0`, `pysr_imported = False`, both recorded as data.
- **No sealed evidence modified.** 482/482 files re-hash to their recorded SHA-256. Nothing was
  written into the evidence root; all output is in this worktree's `results/restored/`.
- **No frozen source modified.** `git diff 8d87143 HEAD -- src/` is empty; the restoration is
  entirely new modules.
- **No threshold, denominator, grammar, seed, budget, calibration, family definition, or A1/G1/G2/G3
  /Gate7/Gate8/F5/F9 role changed.** 14 frozen constants verified against their amendment values.
- **Challenge not opened.** `AUTHORISED_PARTITIONS = {"development", "held_out"}`. No A3.7, no RC5.2,
  no Challenge record, no Challenge outcome.
- **Confirmation not opened.** Real-data Confirmation remains sealed.

## 7. Tests

| Suite | Result |
|---|---|
| `tests/test_heldout_analysis_restoration.py` | 33 passed |
| `tests/test_heldout_superseded_rules_differ.py` | 6 passed |
| `tests/test_heldout_hostile_lenses_have_teeth.py` | 13 passed |
| **Restoration total** | **52 passed, 0 failed** |

Two pre-existing failures in the wider suite, both established as predating this session and
documented in the supersession ledger §5: the A3.5 authorized-delta ledger pin (A3.6 changed a
pinned file without an A3.6 ledger entry) and `test_ov_pipeline.py` (missing
`artifacts/p2_compounds.parquet`).

## 8. Artifact hashes

| File | SHA-256 |
|---|---|
| `src/muru/paper_benchmark/rc5_record_payload.py` | `407cc3a5728a0435f009cdbea785ef1f83e9cf97735b4a7b3e8a2cec3cd284cf` |
| `src/muru/paper_benchmark/heldout_endpoint_populations.py` | `2aaa0541090f2e0da50fe8f93ad7aac09d661e24e11ec07bbaa69a47dd14ae93` |
| `src/muru/paper_benchmark/heldout_contract_analysis.py` | `84f4a22fb94ce9033d03f9c70eb9ef556f04a277ef9417c2ff7be534a5f1639f` |
| `src/muru/paper_benchmark/heldout_g1_recovery.py` | `92b9cdc9bf217a9e5efb49ed84d86b315c1f061e5f22f1bda71e0a157fe6adcb` |
| `src/muru/paper_benchmark/heldout_independent_scoring.py` | `305051a45991bf370d0103d84e9f8cd38d77ed4b042227e397c77d54ec1f875a` |
| `src/muru/paper_benchmark/heldout_hostile_lenses.py` | `3fcd44e575f4907c4b319fbda0515e532c6be03061803b707fcff4857b1af279` |
| `src/muru/paper_benchmark/post_execution_sealer.py` | `37eab2f7799cac24c368d5d93e4d472520908819e91ff1d42b0cb272714009dc` |
| `scripts/run_heldout_restored_analysis.py` | `1baf79c4f35b65cea5cfeb23d0ee3345a4094fd27220144b65e0c2f3cf3f3743` |
| `scripts/run_heldout_hostile_lenses.py` | `32c148d70ba54200b063dad5f87f08647b7c2a10ab01ce358f2455931f5988f3` |
| `tests/test_heldout_analysis_restoration.py` | `ddc137372509e5c19639dc9c9f2997008ed139a8346d8b749c91e9c49e23413f` |
| `tests/test_heldout_superseded_rules_differ.py` | `4aea3731e4cfcf784f9a3d27d6e4034279fc0879f43220f872057bfbd8a1cd1e` |
| `tests/test_heldout_hostile_lenses_have_teeth.py` | `6792991485039ba50889b1aedcff9b00a2b982930c8eb0e9ba9fc46f2e4d9a8c` |
| `results/restored/heldout_restored_analysis.json` | `32891d1c9354785ce7d5fdd98d6a631386d9c1d31f8f9c850e66afa376ac40a3` |
| `results/restored/heldout_independent_recomputation.json` | `5e79e5592448cb790fda370aafd9973e629aaf8374ddd5ab43b677f044bbac7c` |
| `results/restored/heldout_g1_recovery.json` | `b75725297acc0e50b78c3696f7922c72a6e1dba328352da352d9143a59cd777d` |
| `results/restored/heldout_hostile_review.json` | `264ae24dfedea27d583a0074ed29b7370a3f59f90aed83329cd3740930ce280e` |

Reproduce with:

```bash
PYTHONPATH=src python scripts/run_heldout_restored_analysis.py && PYTHONPATH=src python scripts/run_heldout_hostile_lenses.py
```

## 9. What this disposition does not decide

Whether the Challenge partition should be opened is **not** adjudicated here and must not be
inferred from these results. That question is being answered in a separate, outcome-blind context
that has been given only the pre-Held-out frozen authorities, precisely because this context knows
the outcome and therefore cannot answer it credibly.

---

**HELD-OUT ANALYSIS CONTRACT RESTORED AND FROZEN**
