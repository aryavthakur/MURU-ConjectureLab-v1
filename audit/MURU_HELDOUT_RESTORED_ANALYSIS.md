# MURU Held-out — Restored Analysis Under the Frozen Contract

Repair branch `eng/muru-heldout-analysis-restoration`, rooted at `b16d274`
(`audit/muru-heldout-forensic-rescue`), whose parent `8d87143d4280602323aa33ee0b5481aaef0fb4a8`
is the exact commit the 7,200 Held-out searches ran under.

**No tracked source file was modified.** `git diff 8d87143 HEAD -- src/` is empty; the restoration
is entirely new modules. No search was rerun. Nothing was written into the sealed evidence root.

## 1. What was repaired

The superseded post-run analysis layer reimplemented every endpoint instead of invoking the frozen
scorers, and every reimplementation deviated permissively. The restored layer decides nothing: each
number below is the return value of a frozen scorer, and each frozen scorer's length assertion —
`score_g1` ≠ 164, `score_g2` ≠ 144, `score_g3` ≠ 36 — is allowed to fire. Those guards exist
precisely to catch the denominator drift that produced the superseded analysis, and they went
unfired only because the frozen scorers were never called.

Endpoint populations are built from `registry.endpoint_applies_to_variant` and asserted against
`registry.endpoint_case_count` before any scoring occurs.

## 2. Contract-fidelity check, performed first

The full frozen acceptance predicate was re-evaluated for all 240 cases from their own stored
`StructuralCandidate` inputs plus the frozen A3.2 null-threshold table.

| Quantity | Value |
|---|---|
| Cases recomputed | 240 |
| Disagreements vs stored `acceptance_status` / `acceptance_gate_reached` | **0** |
| Distinct `null_threshold_digest` across records | 1 (`b9b6148…`) |
| Recomputed digest of `calibration/a3_2/threshold_table.json` | `b9b6148…` — matches |

**The sealed raw records are exactly faithful to the frozen A3.5 acceptance predicate.** Everything
that went wrong is strictly downstream of the execution.

## 3. Primary endpoints

| Endpoint | Registry name | Denominator | Result | Gate | Verdict |
|---|---|---|---|---|---|
| **G1** scalar competence | `scalar_competence` | **164** | **67** competent, Wilson lower **0.336233** | ≥ 0.70 | **FAIL** |
| **G2** family recovery | `family_recovery` | **144** | **4** successes, Wilson lower **0.010854** | ≥ 0.70 | **FAIL** |
| **G3** structural safety | `principal_structural_safety` | **36** | **26** violations, Wilson upper **0.841518** | ≤ 0.15 | **FAIL** |

164 + 144 + 36 = 344 ≠ 240. The endpoints overlap, and five families (F06, F13, F14, F15, F16)
carry no primary endpoint at all. **No frozen endpoint has a denominator of 240.**

**Decision rule** (A3.5, no existence tests): G1 Wilson lower ≥ 0.70 **AND** G2 Wilson lower ≥ 0.70
**AND** G3 Wilson upper ≤ 0.15 → **`all_primary_endpoints_pass = false`**. All three fail
independently; no single repair would change the verdict.

### 3.1 G1 is now exact, not a bound

The sealed record schema `muru-rc5-case-record-2.0.0` persists no G1 observable. The forensic
rescue could therefore prove only `successes ≤ 67` and a determinate FAIL. That gap has been closed:

- G1's inputs are search-independent (A3.5 §8.2), so all 164 cases were rescored via
  `materialize_case → fit_case_scalars → score_case_g1 → score_g1`.
- **0 searches were run and PySR was never imported** (asserted programmatically, not claimed).
- **Content identity was verified, not assumed**: `run_case_adequacy` is itself search-independent,
  so each regenerated case's A1 verdict was recomputed and compared against its sealed
  `a1_case_adequacy_status`. **164/164 matched, 0 mismatches.**

The exact count is **67 of 164** — the upper bound is attained.

| G1 conjunct decomposition | Cases |
|---|---|
| `m0_accepted` (sealed A1 = `M0_NOT_REJECTED`) | 67 |
| of those, also passing `g_spearman ≥ 0.80` | **67** |
| of those, also passing `trajectory_mae ≤ 0.80 · per_energy_mean_mae` | **67** |
| **competent** | **67** |
| failing on `m0_accepted` alone, both continuous conjuncts passing | **87** |
| failing on `g_spearman` alone | 0 |
| failing on `trajectory_mae` alone | 0 |
| `contract_failure` | 0 |

This is the single most informative result in the partition. **Every case whose A1 adequacy was
established passed both continuous conjuncts — 67 of 67.** G1 does not fail because the scalar
pipeline is inaccurate; it fails because A1 could not establish adequacy for 97 of 164 cases, all
of them `BOUNDARY_LIMITED`, and `BOUNDARY_LIMITED` is UNEVALUABLE under the frozen contract.

Observable ranges across all 164: `g_spearman` min 0.6725 / median 0.9806 / max 1.0000;
`trajectory_mae / per_energy_mean_mae` min 0.0013 / median 0.3622 / max 0.9712 against a 0.80 gate.

**Diagnostic counterfactual, explicitly not an endpoint**: had A1 adequacy been established for all
164, the competent count implied by the two continuous conjuncts would be 67 + 87 = 154. That number
is a mechanism diagnostic for the failure analysis and **may not be reported as a G1 result**, cited
as a rate, or used in any gate. The frozen endpoint is 67/164.

### 3.2 G2

4 successes / 144. Success requires `support_status == MATCH` **AND** `family_status == MATCH`; the
frozen `evaluate_g2_event` was invoked per case and agreed with every stored `g2_event` (0
mismatches). Successes: `PB|held_out|F01|r002`, `PB|held_out|F01|r005`, `PB|held_out|F11|r010`,
`PB|held_out|F12|r000` — families F01 ×2, F11 ×1, F12 ×1. Failures 103, unevaluable 37; the 37
unevaluable remain in the fixed 144 and cost exactly what a failure costs.

### 3.3 G3

26 violations / 36, Wilson **upper** 0.841518 against a ≤ 0.15 gate. Scored through the sole frozen
authority `g3_contract.classify_g3_event` + `rc3_scoring.score_g3`;
`analysis.classify_negative_control` was not imported (A3.5 §8.3 — it drifts permissively on 20 of
these 36 opportunities). Events: VIOLATION 26, SAFE 10, UNSAFE 0. By family: F20 ×12 (all twelve),
F07 ×8, F19 ×6. The dominant driver is the conservative `UNEVALUABLE ⇒ VIOLATION` rule.

## 4. Gates

| Gate | Definition | Result |
|---|---|---|
| **Gate 7** | ceiling comparison at position 7: `ceiling_pass OR ceiling_waiver` | **27 reached, 26 pass, 1 fail** (`PB\|held_out\|F02\|r004`) |
| — via `ceiling_pass` | `ceiling_fraction ≥ 0.80` | **26** |
| — via `ceiling_waiver` only | `ceiling_r2 < 0.05 AND candidate_test_r2 > null_threshold[·]` | **0** |
| **Gate 8** | `check_gate8` over `{F1, F4, F7, F10}`, fail-closed | **26 reached, 25 pass, 1 fail** (`PB\|held_out\|F07\|r005`) |
| **STRUCTURAL_ACCEPTED** | gates 1–8 all pass | **25 of 240** |

Gate 7 is **not** structural acceptance and **not** `F7_INFLUENCE_DROP` (A3.5 §6.9.3 — "they share
a digit by coincidence, not by relation"). Gate 8 is **not** Gate 7 + G1: **G1 is an endpoint, not a
gate**, and no G1 symbol is reachable from the Gate-8 code path.

Per-rung status among the 26 Gate-8 reachers: F1 26/0, F4 26/0, F7 26/0, **F10 25/1**. The single
Gate-8 rejection is driven solely by `F10_NEGATIVE_CONTROL`.

`STRUCTURAL_ACCEPTED = 25` is an **acceptance count, not an endpoint rate**. It has no frozen
denominator of 240 and must never be reported as one. By family: F18 ×7, F10 ×6, F09 ×4, F04 ×2,
F02 ×1, F05 ×1, F07 ×1, F08 ×1, F12 ×1, F19 ×1.

Failure-stage distribution across all 240: `a1_adequacy` **154**, `stability` 43, `null_threshold`
16, `ceiling` 1, `falsification` 1, `all_passed` 25.

## 5. F5 and F9

**F5** — `F5_SCAFFOLD_HOLDOUT` appears in **zero** of the 240 sealed records and is absent from the
`FalsificationRung` enum entirely, exactly as A3.5 §6.9.2 requires. Its one non-redundant
contribution, the raw `candidate_test_r2` floor, survives only inside Gate 7's waiver branch.
**Zero cases entered that branch**, so the A3.5 Gate-7 amendment is outcome-invariant on this
partition as a matter of fact.

**F9** — secondary, reported, non-gating. `f9_stress_test_result`: PASS 26, null 214; among the 26
Gate-8 reachers, PASS 26 / FAIL 0. `f9_stress_test_metric` ranges 0.7460 to 0.9804.
`f9_acceptance_calibration_status` is uniformly `NOT_PROVEN_FOR_HARD_GATE` across all 240.

> **Binding drafting guard (A3.5 §6.9.4).** This 26/26 PASS may **NOT** be cited in any report or
> paper as evidence of validated robustness. F9 is the only rung that re-estimates the `g` pipeline,
> a strictly larger perturbation than §6.7's conservatism proof covers; its bias direction is
> unproven in *either* direction.

## 6. Mandatory execution-failure disclosure (A3.5 §8.2)

| Endpoint | Execution-failure-poisoned cases |
|---|---|
| G1 | **0** of 164 |
| G2 | **0** of 144 |
| G3 | **0** of 36 |

Seed statuses across all 7,200: `COMPLETED_WITH_CANDIDATES` 7,136, `COMPLETED_NO_CANDIDATE` 64,
`EXECUTION_FAILURE` **0**. Every UNEVALUABLE arose from A1 adequacy or a missing candidate, never
from execution failure.

## 7. One disclosed numerical difference from the forensic artifact

The sealed forensic result recorded G1's Wilson lower at the bound as `0.336234`. The restored value
is `0.3362326347636318`, which rounds to `0.336233`.

Cause: the forensic rescue could not invoke `score_g1` (no observables were available to it), so it
computed that one interval by hand using `z = 1.959963984540054`, the exact standard-normal 97.5th
percentile used by `analysis.wilson_interval` and the A3.4 secondary endpoints. The **frozen
primary-endpoint scorers** — `g2_contract.wilson_lower_95` / `wilson_upper_95`, which `score_g1`,
`score_g2` and `score_g3` all route through — use `z = 1.96`. The restored analysis uses the frozen
scorers, hence `z = 1.96`.

The difference is 1.3 × 10⁻⁶ and immaterial: both values are far below the 0.70 gate. G2 and G3
matched the forensic artifact exactly because those endpoints *were* scored through the frozen
functions. Sensitivity at both conventions is recorded in
`results/restored/heldout_independent_recomputation.json`:

| Endpoint | z = 1.96 (frozen) | z = 1.959963984540054 | Gate | Verdict at both |
|---|---|---|---|---|
| G1 | 0.3362326347636318 | 0.3362338964284562 | ≥ 0.70 | FAIL |
| G2 | 0.010853942365456266 | 0.01085411795640967 | ≥ 0.70 | FAIL |
| G3 | 0.841518299741862 | 0.8415166205986538 | ≤ 0.15 | FAIL |

No threshold, denominator or constant was changed to obtain this. The frozen scorer was invoked and
its value reported.

## 8. Agreement with the pre-repair sealed forensic result

Every determinate quantity the forensic rescue established is reproduced exactly. That result was
cryptographically sealed (`b750d5c0…`) **before** this repair was written, so the agreement could
not have been tuned toward.

| Quantity | Forensic | Restored |
|---|---|---|
| G2 successes / denominator | 4 / 144 | **4 / 144** |
| G2 success case ids | 4 listed | **identical set** |
| G3 violations / denominator | 26 / 36 | **26 / 36** |
| Gate 7 reached / pass / waiver | 27 / 26 / 0 | **27 / 26 / 0** |
| Gate 7 failing case | `F02\|r004` | **identical** |
| Gate 8 reached / pass | 26 / 25 | **26 / 25** |
| Gate 8 failing case | `F07\|r005` | **identical** |
| Gate 8 rung failures | F10 ×1 | **identical** |
| Structural accepted | 25 (by family) | **25, identical family split** |
| Failure-stage distribution | 6 stages | **identical** |
| F9 among Gate-8 reachers | PASS 26 | **PASS 26** |
| Poisoned per endpoint | 0 / 0 / 0 | **0 / 0 / 0** |
| G1 | ≤ 67 / 164, FAIL | **= 67 / 164, FAIL** (bound attained, now exact) |

## 9. Artifacts

| File | Contents |
|---|---|
| `results/restored/heldout_restored_analysis.json` | the primary restored analysis |
| `results/restored/heldout_independent_recomputation.json` | the independent recomputation and its comparison |
| `results/restored/heldout_g1_recovery.json` | per-case G1 observables and content-identity evidence |
| `results/restored/heldout_hostile_review.json` | seven hostile lenses, 66 checks |

---

**HELD-OUT ANALYSIS CONTRACT RESTORED — ALL THREE PRIMARY ENDPOINTS FAIL**
