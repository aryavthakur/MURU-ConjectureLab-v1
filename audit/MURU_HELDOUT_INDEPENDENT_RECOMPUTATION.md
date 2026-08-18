# MURU Held-out — Independent Recomputation

Machine-readable result: `results/restored/heldout_independent_recomputation.json`.

**Disagreements with the primary restored analysis: 0.**

## 1. What "independent" has to mean here

The superseded independent recomputation was independent in name only. It imported
`HeldOutAnalysisReport` from the analyzer it was meant to check, shared its `WILSON_Z_95` constant
and its `case_slug`/`iter_case_ids` usage, was edited in the *same second* as that analyzer once
outcomes were visible, and cloned every rule line for line. Its `compare_analysis_reports` therefore
compared two encodings of one rule set: it could detect a transcription slip and could not, even in
principle, detect a contract error. Its "0 discrepancies" is exactly what two copies of the same
wrong rule must produce.

Three properties are required, and all three are enforced structurally rather than promised.

**No shared objects.** `heldout_independent_scoring` binds nothing whose `__module__` is
`heldout_contract_analysis`. This is checked at import time, again on every call, and again by an
AST test that walks the module's import statements. The guard is itself tested: a test smuggles a
function from the primary analyzer into the module's globals and requires `IndependenceViolation` to
be raised — and repeats it with a module object, since the two leak differently.

**A genuinely different derivation.** This is the deliberate inversion of the primary analyzer's
discipline, and the difference is the whole point:

| | primary | independent |
|---|---|---|
| endpoint scoring | **invokes** the frozen scorers, so their 164/144/36 length assertions fire | **re-derives** each rule from the frozen contract text |
| acceptance verdict | calls `evaluate_structural_acceptance` | re-implements the ordered 8-gate predicate from §6.9 |
| population construction | scans the 240 case ids asking `endpoint_applies_to_variant` per case | walks the family table, cycling variants, cross-checked against `held_out_cases_for` per family |
| Gate 7 / Gate 8 membership | reads the frozen predicate's own `gate_reached` | derives the stopping stage itself |
| Wilson intervals | frozen `wilson_lower_95` / `wilson_upper_95` | written from the formula, evaluated at both z conventions |

Neither discipline is sufficient alone. Invoking the frozen scorers cannot catch a defect *inside*
the shared frozen path; re-deriving from text cannot claim the authority of the frozen
implementation. The pair is the check.

**An additional check the primary does not perform.** The independent module re-derives
`(acceptance_status, gate_reached)` for all 240 cases and requires exact agreement with the sealed
values before it scores anything, raising if any record disagrees. 0 disagreements.

## 2. What was compared

Twenty quantities, all in exact agreement:

| Quantity | Value |
|---|---|
| denominators (G1 / G2 / G3) | 164 / 144 / 36 |
| failure-stage distribution | `a1_adequacy` 154, `stability` 43, `null_threshold` 16, `ceiling` 1, `falsification` 1, `all_passed` 25 |
| structural accepted | 25 |
| G1 `m0_accepted` | 67 |
| G1 Wilson lower / gate | 0.3362326347636318 / FAIL |
| G2 successes / unevaluable | 4 / 37 |
| G2 Wilson lower / gate | 0.010853942365456266 / FAIL |
| G3 violations | 26 |
| G3 Wilson upper / gate | 0.841518299741862 / FAIL |
| Gate 7 reached / passed | 27 / 26 |
| Gate 8 reached / passed | 26 / 25 |
| Gate 8 rung failures | `F10_NEGATIVE_CONTROL` ×1 |
| F9 PASS among Gate-8 reachers | 26 |
| F5 present in any record | **false** |
| poisoned per endpoint | 0 / 0 / 0 |

## 3. The disagreement it produced on its first run, and what that establishes

The first cross-check **failed**: the independent route reported 27 G3 violations against the
primary's 26.

The fault was in the independent module. It dispatched the G3 classifier on the `variant_cycle`
key rather than on the variant's own `code` field. For F19 and F20 those coincide (`F19A`, `F20A`,
…), but for every single-variant family the cycle key is `BASE` while the code is the family code —
so an F07 case fell through to the branch for variants that permit no acceptance at all, and one
genuinely safe mass-only acceptance was counted unsafe. Investigating it surfaced a second latent
fault: the module was collapsing `REJECTED_A1_INADEQUATE` and `UNEVALUABLE` into a single stage
label, and G3 treats those two oppositely — VIOLATION for the second, SAFE for the first. Both were
repaired; the module now carries `(status, stage)` as a pair throughout.

Two things follow. The cross-check has demonstrated, on live evidence, that it can produce a
disagreement — which is the property the superseded version provably lacked. And the disagreement
ran in the **conservative** direction: the buggy route over-counted violations. A cross-check whose
only observed error made the result look worse is not a check that was tuned toward agreement.

## 4. Wilson z sensitivity

The frozen primary-endpoint scorers use `z = 1.96`. `analysis.wilson_interval` and the A3.4
secondary endpoints use `z = 1.959963984540054`. Both are reported so no reader has to trust that
the choice is immaterial:

| Endpoint | z = 1.96 (frozen) | z = 1.959963984540054 | Gate | Verdict |
|---|---|---|---|---|
| G1 | 0.3362326347636318 | 0.3362338964284562 | ≥ 0.70 | **FAIL** at both |
| G2 | 0.010853942365456266 | 0.01085411795640967 | ≥ 0.70 | **FAIL** at both |
| G3 | 0.841518299741862 | 0.8415166205986538 | ≤ 0.15 | **FAIL** at both |

The three gate verdicts are invariant to the convention by margins of 0.36, 0.69 and 0.69
respectively. The restored analysis reports the frozen `z = 1.96` values.

---

**INDEPENDENT RECOMPUTATION COMPLETE — 0 DISAGREEMENTS, STRUCTURALLY INDEPENDENT**
