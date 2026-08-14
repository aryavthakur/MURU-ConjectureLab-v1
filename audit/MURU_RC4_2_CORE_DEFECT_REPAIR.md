# MURU RC4.2 Core Engineering Defect Repair

**Classification:** `ENGINEERING_RELEASE_CANDIDATE_FREEZE`
**Branch:** `eng/muru-rc4-2-core-defect-repair`
**Tag:** `engineering-rc4-2-core-defect-repair`
**Status:** `FROZEN_CLEAN`

This is **not** Amendment A3.5. No new scientific choice was made anywhere in this repair.

## Development status wording

- `HISTORICAL DEVELOPMENT EXECUTED UNDER SUPERSEDED A2.1/RC2 CONTRACT`
- `CURRENT-CONTRACT DEVELOPMENT RERUN NOT OPENED`

## Purpose

Repairs four independently-confirmed implementation defects (R1-R4), adjudicated as engineering, not scientific-contract changes, in `audit/muru_benchmark_core_defect_adjudication.json` (branch `audit/muru-benchmark-core-defect-adjudication`, terminal status `BENCHMARK CORE DEFECTS CONFIRMED — ENGINEERING REPAIR ONLY`). No RC5 execution semantics were implemented, no Development rerun was executed, and Held-out, Challenge, and Confirmation were not opened. Calibration was not rerun.

## Parent lineage

| Item | Identifier |
|---|---|
| Repair base commit | `a605120242594d23a5fc36d2e622d7d3084356fb` (RC5 Gate 1 stop) |
| A3.4 science freeze | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` (tag `benchmark-content-freeze-a3-4`) |
| RC4 engineering freeze | `c800e7a59eca904ee32231e43ce3d1ddda4a26ee` (tag `engineering-rc4-a3-4`) |
| RC4.1 environment closure | tag `engineering-rc4-1-environment-closure` → `8c5dd413264fa6661982ae70fbeb323d4a647a27` |
| Calibration preservation | `44e5e3661aba39b360ef60ed842381c9426c0c82` |
| Authorized calibration guard | `6a6798273d00af374b7a62976a80cea1ae7df32c` |
| Defect adjudication | branch `audit/muru-benchmark-core-defect-adjudication` |

Ancestry independently re-verified via `git merge-base --is-ancestor`: `be23b80`, `c800e7a5`, `44e5e36`, and `6a67982` are all ancestors of `a605120`, confirming it as the correct single most-downstream authoritative source tree.

**Starting-worktree note (confirms the adjudication's own finding):** this task's starting branch and `main` both sit at `5049a1a`, an unrelated wet-lab-track lineage that shares no history with the paper-benchmark apparatus beyond being its distant ancestor. The engineering repair was built on a fresh branch, `eng/muru-rc4-2-core-defect-repair`, forked directly from `a605120`, not from the stale starting branch or `main`.

**Mandatory-reading gap, reported transparently:** `audit/MURU_CORE_DEFECT_CALIBRATION_IMPACT_MATRIX.md` / `.json` does not exist anywhere in this repository's git history (searched every ref). A companion branch, `claude/muru-defect-calibration-impact-220641`, exists but was never advanced past the stale pre-lineage commit. This did not block the repair: the adjudication JSON already carries a per-defect `calibration_impact: {affects_calibration: false}` assessment for all four defects, and this task independently re-derived and verified calibration non-interference from first principles rather than trusting either document (see below).

## R1 — G1 scalar estimator orientation (DEFECT_A)

`src/muru/paper_benchmark/protocol.py::estimate_one` computed `log_g = clip(-residual, *support)`. Analytic derivation from the frozen M0 generator (`generator.py::_response_matrix`: `u = (E/45)/g`, `mu = mu_inf + (1-mu_inf)*exp(-(u**phi_p))`, with `mu_inf ∈ (0.15, 0.30)` always `< 1` and `phi_p ∈ (1.20, 1.70)` always `> 0`) shows `mu` is **strictly increasing in `g`** for fixed `E`, for every valid parameter draw. The pre-repair sign made the estimate anti-monotone. The minimum correction removes the negation: `log_g = clip(residual, *support)`.

Unchanged: fold-locality, the `(-2.0, 2.0)` clip range, the estimator's domain, and G1's thresholds (0.80 Spearman, 0.70 Wilson lower bound).

Tests added (`tests/test_paper_benchmark_protocol.py`, 6 new): hand-built canaries spanning six true-`g` values (0.75-2.50), reproducing the M0 law directly with fixed constants — no `case_id`, registry, `generate_case`, or partition anywhere in the file. Cover positive monotonicity, exact orientation (Spearman = +1.0 against the canaries), degenerate-case behavior (log_g = 0 exactly when the held-out compound matches the training center), boundary-clip direction, and FM-06 fold-locality across the full sweep. Verified adversarially: temporarily re-inverting the sign in a throwaway copy fails 4 of the 6 new tests; the degenerate-case and fold-locality tests correctly stay green either way, since they're sign-invariant by construction.

## R2 — G3 F07 dispatcher (DEFECT_B3)

`g3_contract.py::classify_g3_event` raised `ValueError` for variant `"F07"`. `analysis.py::classify_negative_control` — the function `analysis.umbrella_decision` actually calls for the production G3 gate — already implements F07 correctly: mass-only acceptance permitted, an accepted unsupported non-mass variable or richer family is unsafe. The repair adds `classify_f07_event`, structurally identical to `classify_f19a_event`/`classify_f19b_event`, and wires it as the dispatcher's first branch.

Unchanged: `classify_f19a_event` through `classify_f20c_event` (byte-identical), `G3_HELD_OUT_DENOMINATOR = 36`, `G3_WILSON_UPPER_GATE = 0.15`, the Wilson rule, F19/F20 meaning.

Tests added: `tests/test_a3_1_g3_contract.py` gains `TestF07` (5 unit tests) and 3 dispatch tests, plus `"F07"` in the existing `test_all_variants` loop. New file `tests/test_g3_f07_dispatcher_equivalence.py` proves `classify_f07_event`, the dispatcher, and `analysis.classify_negative_control` agree across accept/reject/mass-only/non-mass/richer-family scenarios.

## R3 — G2 parser / support / feature mapping (DEFECT_C)

`g2_contract.py::_safe_parse` left `square`/`cube`/`inv` unbound in its `sympify` locals (`sqrt`/`log` already resolve via sympy's own builtin namespace). Sympy treated them as opaque undefined functions, which broke cancellation (`mass*inv(mass)` → `{mass}` instead of `{}`) and reordering invariance (`mass/descriptor` vs. the algebraically identical `inv(descriptor)*mass` classified differently). Unmapped raw symbols (PySR-default `x0`/`x1`/...) silently reported empty support instead of `SUPPORT_UNRESOLVED`.

Repair: bound `square=x**2, cube=x**3, inv=1/x`, reproduced verbatim from the sibling frozen module `src/muru/discovery/grammar.py::_SYMPY_LOCALS`. Aliased `x{i}` to the *same* `Symbol` object as `GRAMMAR_PRIMITIVES[i]`, the covariate order already frozen as the design-matrix column order in `rc3_calibration_worlds.py::CALIBRATION_COVARIATE_ORDER` and `rc3_ceiling.py::CEILING_COVARIATE_ORDER` — not a new naming choice. Any symbol outside that known set now fails closed (`None`) rather than silently reporting less support than the truth.

Unchanged: `GRAMMAR_PRIMITIVES`, `classify_support`, `evaluate_g2_event`, `G2_HELD_OUT_DENOMINATOR = 144`, `G2_WILSON_LOWER_GATE = 0.70`. No new broad symbolic-equivalence contract was added — `discovery/equivalence.py::algebraically_equivalent` is neither imported nor duplicated.

Tests added (`tests/test_a3_1_g2_contract.py`, `TestR3ParserSupportFeatureMapping`, 20 tests): the exact mission-mandated fixture set (`mass/mass`, `mass*inv(mass)`, `descriptor/descriptor`, `descriptor*inv(descriptor)`, `mass/descriptor`, `inv(descriptor)*mass`, `mass*square(inv(mass))`, `x0`, `x1`, `x2`) plus reordered/factored equivalents and fail-closed unknown-symbol cases.

**Known out-of-scope gap (backlog, not repaired this cycle):** adversarial review (E3) found that an unmapped *function* name (not symbol) — e.g. `weird_op(mass)` — still returns `{mass}` rather than failing closed, because sympy's `free_symbols` on a `Function` application only inspects its argument symbols, never the function name itself. Verified byte-identical on the pre-repair base commit; not a regression, and outside the defect the adjudication named (which was specifically "square/cube/inv unbound" and "x0/x1 unmapped raw symbols," not arbitrary function-call syntax).

## R4 — G2 truth support producer (DEFECT_D)

`classify_support(discovered_support, truth_support)` always required a `truth_support` operand that nothing in the repository produced. `generator.py::_law`'s `active_variables` (written for every case) is the single, unique source of truth: four of five G2-applicable law shapes already use exact `GRAMMAR_PRIMITIVES` names; the fifth (`mass_interaction`, family F10) uses block labels `interaction_left`/`interaction_right`, which the same `_law` call that writes the law string `"...*descriptor*descriptor2..."` returns positionally in that same order — a mechanical reading, not a new naming choice, and the only reading generator.py supports (verified: a single grep hit for the labels).

Repair: added `truth_support_for_case(truth: TruthRecord) -> frozenset[str]`, gated on `TruthRecord.symbolic_truth_kind == "defined"` (per-variant frozen registry metadata, already carried onto every generated `TruthRecord`). Read directly off the record rather than re-resolved via `registry.resolve_case_id` — see the sealed-boundary note below for why. Raises rather than guessing for every non-applicable family, unrecognized `mathematical_family`, or unmapped label.

Unchanged: G2 denominator (144), `classify_support` itself. No partition-dependent logic — structurally proven (`"partition" not in truth_support_for_case.__code__.co_names`).

Tests added (`tests/test_r4_g2_truth_support.py`, new, 18 tests): hand-built block-label mapping unit tests; exhaustive parametrized coverage of all 12 G2-applicable families via `generate_case` on the **development partition only**, proving support is produced, deterministic, and matches a hand-derived expected-support table per family (an independent cross-check, not a restatement of the function's own logic); proof every non-applicable family raises; and integration with the untouched `classify_support`.

## Sealed-boundary correction made during this repair

An earlier draft of the R4 producer imported `registry.resolve_case_id` directly into `g2_contract.py`. Since `a34_parameter_recovery.py` and `a34_predictive_equivalence.py` both import from `g2_contract.py`, this import was reachable from the A3.4 secondary-scorer closure that `scripts/pb_35_a3_4_integrity.py` statically, recursively scans — and `"registry"` is a `FORBIDDEN_MODULE_TOKEN`. Running the script surfaced `SEALED_BOUNDARY_IMPORT`/`SEALED_BOUNDARY_MODULE`/`SEALED_BOUNDARY_REFERENCE` violations. This was caught and fixed **before** the freeze (not by a reviewer): the producer was redesigned to read `TruthRecord.symbolic_truth_kind` directly off the record it already receives, which carries identical information without adding any cross-module import. Re-running `scripts/pb_35_a3_4_integrity.py` after the fix: section 3, "A3.4 endpoint static sealed-boundary scan" → `VERIFIED`, no violation.

## Calibration non-interference

Proven by import/call-graph plus a digest comparison, per the mission's requirement to independently verify rather than trust prior claims:

- `grep -rn "estimate_one|fit_training_scalar|classify_g3_event|classify_f07_event|extract_effective_support|classify_discovered_family|truth_support_for_case" src/muru/paper_benchmark/rc3_calibration_runner.py src/muru/paper_benchmark/rc3_calibration_worlds.py src/muru/paper_benchmark/calibration_contract.py` → **zero matches**.
- `rc3_calibration_worlds.py` imports only `GRAMMAR_PRIMITIVES` from `g2_contract.py` — an untouched frozen tuple, defined before every R3/R4 addition in the diff.
- `PySRBackend.search` and `CalibrationWorld` construction read only `world.split_masks()`/`design_matrix()`/`target` and PySR internals; `rc3_scoring.py` imports only frozen denominator/gate constants and event enums, none of the four changed functions, and is not imported by the calibration runner/worlds modules at all.
- `calibration/a3_2/threshold_table.json` digest — `sha256:f36864aaec1b0afb10b6d6b691ace07ab71cda4a1e6d337885390e8de27ae3d3` — is **byte-identical** across the current working tree, the calibration-preservation commit `44e5e36`, and this repair's own base commit `a605120`. `git status --porcelain -- calibration/` is empty.
- No calibration rerun, Development rerun, Held-out open, Challenge run, or Confirmation open occurred anywhere in this repair or its tests.

## Protected science changes (engineering exception, transparently recorded)

Six files sit inside two different frozen protected-path sets (A3.4's `artifacts/paper_benchmark_amendment_a3_4.json::protected_paths`, and A2.1's pin of `protocol.py`/`test_paper_benchmark_protocol.py` in `pb_32_amendment_a2_1_integrity.py`). Every byte-identity integrity script correctly flags all six as changed — that detection is expected, not suppressed, and none of those scripts were modified.

| File | Old blob (git hash-object) | New blob | Defect repaired |
|---|---|---|---|
| `src/muru/paper_benchmark/protocol.py` | `a913a71ef17f41fba3c102b898cf2536b2b740f8` | `8a8e3c548c8e6f25ab21974bd0a1be9159f5093b` | R1 / DEFECT_A |
| `src/muru/paper_benchmark/g3_contract.py` | `a2b2bc75a517f580af0ead97287b360b081b5693` | `f327ad709f131f65253abb36efa2947e4b7ae16c` | R2 / DEFECT_B3 |
| `src/muru/paper_benchmark/g2_contract.py` | `3abc095ee58bce3bd5630a5680104c6f1220f765` | `d2ee5ebc77c55498c94cb4c06256b6ab308f1562` | R3 / DEFECT_C + R4 / DEFECT_D |
| `tests/test_paper_benchmark_protocol.py` | `804bc13c9b0a206c8d83a5c63843eb88107f5abe` | `63b1f7443fdeadc21a8a97bcf2f3f64d1ca35874` | R1 tests |
| `tests/test_a3_1_g3_contract.py` | `fd9e4fbb9d2e56279928b6a949a74b529304a2e8` | `49ffff2fa305df0effd06e9921f52035ca6e4360` | R2 tests |
| `tests/test_a3_1_g2_contract.py` | `d156c128e1e1e7eb3c275cd5ba4e8a078fee61b8` | `835323660555a7ecfbdc9a12909952997e5b52e2` | R3 tests |

New (unprotected, purely additive) files: `tests/test_g3_f07_dispatcher_equivalence.py` (`95d4b57609e69134f8ac82524765885fb5ca4b1c`), `tests/test_r4_g2_truth_support.py` (`7b534971bbc5c08624fdd3d8660af65a1097f7b2`).

Why scientific semantics are unchanged for each: see the corresponding R1-R4 section above; each repair is either a minimal sign correction, a mechanical reuse of an already-frozen sibling pattern/module's exact semantics, or a mechanical, uniquely-determined derivation from existing frozen source — never a new definition invented for this repair.

## Test summary

| Suite | Result |
|---|---|
| Focused R1 (`test_paper_benchmark_protocol.py`) | 8 passed |
| Focused R2 (`test_a3_1_g3_contract.py`, `test_g3_f07_dispatcher_equivalence.py`) | 45 passed |
| Focused R3+R4 (`test_a3_1_g2_contract.py`, `test_r4_g2_truth_support.py`) | 122 passed |
| **R1-R4 focused total** | **175 passed** |
| A3.4 secondary-scorer regression check (`test_a34_*.py`) | 68 passed |
| Widest repository suite (excluding 5 files that fail to import for missing `sklearn`/`rdkit`, a pre-existing environment gap) | **1018 passed**, 34 failed, 58 skipped, 14 errors |

Failure classification (via `git stash` of all R1-R4 changes and a pristine rerun against `a605120`, then diffed against the post-repair run):

- **27 pre-existing, environment-caused, confirmed identical pre- and post-repair:** `sklearn` not installed (`test_rc3_ceiling.py`, 20 tests), dependency mismatch against the pinned lock (`test_rc3_provenance.py` 3, `test_a3_2_calibration_design.py` 1), and missing `pyarrow`/`fastparquet` for the historical `p2_compounds.parquet` gap (`test_ov_blinding.py` 2, `test_ov_pipeline.py` 1 test + 13 collection errors) — **kept separately classified** per the mission's instruction.
- **7 new, expected, confirmed absent on the pristine baseline:** exactly the byte-identity/protected-path checks reacting to the 6 intentionally-repaired files (`test_a3_4_integrity.py` 1, `test_eng_environment_closure.py` 1, `test_paper_benchmark_amendment_a2_1_integrity.py` 2, `test_paper_benchmark_amendment_integrity.py` 3). No other, unexplained failure was introduced.

## Independent reviewers

All four fresh, read-only reviewers returned **PASS**. Full reports in `audit/muru_rc4_2_core_defect_repair.json::independent_reviewers`.

| Reviewer | Scope | Verdict |
|---|---|---|
| E1 | G1 numerical orientation / FM-06 | PASS |
| E2 | G3 F07 conformance | PASS |
| E3 | G2 parser/support adversary | PASS |
| E4 | Calibration non-interference + governance | PASS |

No reviewer found that any repair changes scientific meaning.

## Sealed status

`SEALED_CLEAN_NO_BLOCKING_FINDING`

---

# RC4.2 CORE ENGINEERING REPAIRS FROZEN — CALIBRATION UNCHANGED
