# MURU Held-out Analysis Restoration — Requirement-to-Code Map

Repair worktree: `.claude/worktrees/heldout-analysis-restoration`
Branch: `eng/muru-heldout-analysis-restoration`
Rooted at: `b16d274` (`audit/muru-heldout-forensic-rescue`, which preserves the five sealed
rescue artifacts), whose parent is `8d87143d4280602323aa33ee0b5481aaef0fb4a8`
(`engineering-rc5-1-heldout-authorization`) — the exact commit the Held-out searches ran under.

This document maps every one of the 12 hard requirements in
`MURU_HELDOUT_RESCUE_FINAL_DECISION.md` §5 to the frozen code object that discharges it and to
the restoration module that invokes it. **No frozen scorer is reimplemented anywhere.**

## 0. Frozen authority inventory (read-only; nothing in this list is edited)

| Frozen object | Module | Role |
|---|---|---|
| `endpoint_applies_to_variant` | `registry.py:193` | per-case endpoint eligibility |
| `endpoint_case_count` | `registry.py:197` | endpoint denominator (164 / 144 / 36) |
| `resolve_case_id` | `registry.py:201` | case id → (family, variant, replicate) |
| `iter_case_ids` | `registry.py:219` | the 240-case Held-out population |
| `ENDPOINTS` | `registry.py:179` | the three primary endpoints, and only three |
| `evaluate_g2_event` | `g2_contract.py:402` | G2 per-case event, `support MATCH ∧ family MATCH` |
| `score_g2` | `rc3_scoring.py:78` | G2 aggregate; **raises unless len == 144** |
| `classify_g3_event` | `g3_contract.py:210` | G3 per-case event, variant-dispatched |
| `score_g3` | `rc3_scoring.py:119` | G3 aggregate; **raises unless len == 36**; type-checked |
| `evaluate_structural_acceptance` | `structural_acceptance.py:231` | the ordered 8-gate predicate |
| `check_gate8` | `structural_acceptance.py:169` | 4 hard rungs, fail-closed |
| `REQUIRED_HARD_GATES` | `structural_acceptance.py:146` | `{F1, F4, F7, F10}` — exactly four |
| `SECONDARY_REPORTED_RUNGS` | `structural_acceptance.py:154` | `{F9}`, import-guarded disjoint |
| `candidate_from_record` | `rc3_acceptance.py:69` | truth-blind projection to `StructuralCandidate` |
| `null_threshold_digest` | `rc3_acceptance.py:56` | identity of the calibration table |
| `score_g1` / `CaseG1` | `rc5_g1_bridge.py:423 / 291` | G1 aggregate; **raises unless len == 164** |
| `adequacy_satisfies_g1` | `adequacy.py:521` | `m0_accepted ⟺ M0_NOT_REJECTED` |
| `wilson_lower_95` / `wilson_upper_95` | `g2_contract.py:450 / 462` | the only interval arithmetic |
| `guard_analysis_boundary` | `post_execution_sealer.py:254` | refuses to analyze an unsealed/mutated run |

`post_execution_sealer.py` is carried into this worktree unmodified from the execution worktree.
The forensic diff establishes it was authored 00:43 and never edited after outcomes became
visible; it is the one post-run module with clean provenance. SHA-256 of the copy:
`37eab2f7799cac24c368d5d93e4d472520908819e91ff1d42b0cb272714009dc`.

## 1. The 12 requirements

| # | Requirement | Frozen object that discharges it | Restoration site |
|---|---|---|---|
| 1 | Never compute a denominator from `len(case_ids)`; build populations via `endpoint_applies_to_variant` and assert against `endpoint_case_count` | `registry.endpoint_applies_to_variant`, `registry.endpoint_case_count` | `heldout_endpoint_populations.build_endpoint_population` — asserts set size and raises `PopulationError` on any mismatch |
| 2 | Invoke the frozen scorers directly; let their length assertions fire | `score_g1`, `score_g2`, `score_g3`, `evaluate_g2_event`, `classify_g3_event`, `evaluate_structural_acceptance`, `check_gate8` | `heldout_contract_analysis` — every endpoint number is the return value of a frozen scorer |
| 3 | Gate 7 is the ceiling test at position 7 (`ceiling_pass OR ceiling_waiver`), never structural acceptance, never a falsification cascade | `structural_acceptance` gate-7 block (lines 316–326), constants `CEILING_FRACTION_GATE`, `CEILING_WAIVER_THRESHOLD` | `heldout_contract_analysis.evaluate_gate7` — reached-set from short-circuit order, branch attribution (`ceiling_pass` vs `ceiling_waiver`) |
| 4 | Gate 8 is `check_gate8` over `{F1,F4,F7,F10}`, fail-closed; **G1 must not appear in it** | `check_gate8`, `REQUIRED_HARD_GATES` | `heldout_contract_analysis.evaluate_gate8` — calls `check_gate8`; a test asserts no G1 symbol is reachable from the Gate-8 path |
| 5 | G3 counts violations over 36 with Wilson **upper** ≤ 0.15, UNEVALUABLE ⇒ VIOLATION | `classify_g3_event` + `rc3_scoring.score_g3` (sole authority; `analysis.classify_negative_control` forbidden) | `heldout_contract_analysis.score_g3_endpoint` |
| 6 | A1 adequacy: only `M0_NOT_REJECTED` permitted; `BOUNDARY_LIMITED` is UNEVALUABLE | `structural_acceptance._A1_PERMITTED`, `_A1_UNEVALUABLE_STATES`, `adequacy.adequacy_satisfies_g1` | never re-encoded; reached only through the frozen predicate and `adequacy_satisfies_g1` |
| 7 | F9 reports `f9_stress_test_result` / `f9_stress_test_metric`, non-gating, with the §6.9.4 drafting guard attached | `SECONDARY_REPORTED_RUNGS`, `F9_ACCEPTANCE_CALIBRATION_STATUS` | `heldout_contract_analysis.report_f9` — carries `citation_prohibition` in its output |
| 8 | Decision rule: G1 Wilson lower ≥ 0.70 **AND** G2 Wilson lower ≥ 0.70 **AND** G3 Wilson upper ≤ 0.15. No existence tests | `G1Score.gate_passed`, `G2Score.gate_passed`, `G3Score.gate_passed` | `heldout_contract_analysis.frozen_decision` — a conjunction of the three frozen `gate_passed` flags; the invented global `decision_passed` is gone |
| 9 | Persist G1 observables in a record-schema successor; recompute G1 for Held-out without any search | new `muru-rc5-case-record-2.1.0` adds `g_spearman`, `trajectory_mae`, `per_energy_mean_mae`, `m0_accepted` | `rc5_record_schema_2_1.py` (schema successor, forward-only) + `heldout_g1_recovery.py` (zero-search recomputation) |
| 10 | Branch on no field absent from the record schema; schema-conformance test | `rc3_record.RECORD_SCHEMA_VERSION` = `muru-rc5-case-record-2.0.0` | `rc5_record_payload.SEALED_RECORD_KEYS` + `require()` accessor that raises on a missing key; `test_schema_conformance` asserts every key the analyzer reads is in the sealed schema |
| 11 | Independent recomputation must not import the primary analyzer; written against frozen contract text | — | `heldout_independent_scoring.py` — module-level guard asserting `heldout_contract_analysis` is not in its import closure; own Wilson implementation from the contract formula |
| 12 | Hostile review must instantiate genuinely independent lenses reconstructing populations, Gate 7, Gate 8 from frozen authority; never assert a hard-coded 240 | — | `heldout_hostile_lenses.py` — seven lenses, each rebuilding what it audits; a test asserts no literal `240` is used as a denominator anywhere in the restoration modules |

## 2. Defects being rejected (each gets a regression test)

| Defect (superseded analyzer) | Regression test |
|---|---|
| denominator 240 for every endpoint | `test_endpoint_denominators_are_registry_derived`, `test_no_literal_240_denominator` |
| G2 `SUCCESS **OR** support==MATCH` | `test_g2_requires_support_and_family_match` |
| `candidate_test_r2 >= 0.80` used as G1 | `test_candidate_test_r2_is_not_g1` |
| G3 over 240 / direction inverted (counts successes) | `test_g3_counts_violations_over_36_with_wilson_upper` |
| Gate 8 = Gate 7 AND G1 | `test_gate8_is_four_rungs_and_excludes_g1` |
| F5 treated as hard-gating | `test_f5_is_not_a_hard_rung` |
| F9 gating | `test_f9_is_never_gating` |
| missing hard rung silently passing | `test_gate8_fail_closed_on_missing_rung` |
| wrong endpoint membership (F07/F19 credited on G2) | `test_endpoint_membership_matches_registry` |
| silent defaults on absent fields | `test_no_silent_defaults`, `test_schema_conformance` |
| `BOUNDARY_LIMITED` accepted as adequate | `test_boundary_limited_is_unevaluable` |
| existence-only `decision_passed` | `test_decision_rule_is_three_wilson_gates` |

## 3. What this restoration explicitly does **not** touch

Thresholds, grammar, seeds, search budget, A1, the G1/G2/G3 definitions, Gate 7/Gate 8, the
F5/F9 roles, calibration, family definitions, Confirmation, `AUTHORISED_PARTITIONS`. No search is
rerun. No sealed file is read except read-only, and nothing is written into the evidence root.

---

**REQUIREMENT MAP COMPLETE**
