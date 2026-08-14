# Development Execution Blocker: RC4 Has No Executable Case Path

**Status:** BLOCKER. Development was NOT opened. No partition was constructed,
executed, scored or inspected.
**Classification (Amendment-style, per the post-RC4 taxonomy):**
`IMPLEMENTATION_DEFECT` - discovered *before* Development was opened, so no
result-dependent risk exists and no outcome influenced this finding.
**Found at:** RC4.1 environment closure, on top of RC4 `c800e7a`.

## 1. Finding

The RC4 engineering freeze is a **contracts, scorers and calibration** freeze.
It cannot execute a benchmark case end to end. Development therefore cannot be
run "under the frozen pipeline", because the frozen pipeline contains no case
execution path.

This is not a missing convenience wrapper. The components that turn a case into
a `CaseExecutionRecord` are absent from the lineage.

## 2. Evidence

Each of the following is independently sufficient.

| # | Check | Result |
|---|---|---|
| 1 | `grep -rn 'CaseExecutionRecord(' src/ scripts/` | no match outside tests. Nothing constructs the record its own docstring says is "constructed once by the pipeline". |
| 2 | `grep -rln 'CompoundContrastRecord(' src/ scripts/` | no match. Nothing produces the per-compound M0-vs-alternative MAEs that `adequacy.decide_case_adequacy` consumes, so the A1 adequacy verdict cannot be reached. |
| 3 | `grep -rn 'selection_count' src/` | only the field name in `rc3_record` / `rc3_acceptance`. Nothing computes k-out-of-30, `valid_r2`, `complexity` or `invalid_fraction`. |
| 4 | `check_falsification_harness(results)` | consumes a precomputed `Mapping[FalsificationRung, FalsificationResult]`. No rung executor exists. |
| 5 | `PySRBackend.search(world, seed)` | typed on `CalibrationWorld` (`design_matrix` / `split_masks` / `target`). No adapter builds those from a benchmark case. |
| 6 | `git ls-tree -r c800e7a \| grep -i 'runner\|pipeline'` | only `rc3_calibration_runner.py` (calibration worlds) and `tests/test_ov_pipeline.py`. The Development runbook's commanded entry point `python -m muru.paper_benchmark.runner` does not exist. |
| 7 | Development search-seed derivation | `derive_calibration_seeds` is calibration-band only (`PB\|NCAL\|...`, band 2_110_000_000+). No frozen rule derives 30 search seeds per Development case, and no seed band is declared for Development. |
| 8 | `src/muru/paper_benchmark/contract.py` | its own docstring: "Strict evaluator input contract for a **future locked MURU engine**". `validate_candidate` accepts predictions that were computed elsewhere; it evaluates nothing. |

### Why the components are missing

The executable engine and the frozen benchmark science have been on divergent
branches since `d9e2795`:

| Branch / commit | `src/muru/paper_benchmark/` | `src/muru/pipeline.py` + engine |
|---|---|---|
| `prep/executable-integration-a2-1` `d9e2795` | 12 modules (pre-A3.1) | present |
| `freeze/muru-paper-executable` `cefc799` | 11 modules (pre-A3.1) | present, recorded as BLOCKED |
| `engineering/muru-completion` `c7c2332` / `5235f81` (RC2) | **absent** | present, blockers resolved |
| `eng/muru-rc4-a3-4` `c800e7a` (RC4) | 26 modules, all A3.x contracts | **absent** |

RC2 resolved the two `cefc799` blockers (a callable strict fold-local adequacy
stage, and declared runtime limits) on a branch that deliberately does not
contain `muru.paper_benchmark` - its own commit message says so and proves
conformance by materialising the frozen decision module from git at test time.
The RC3/RC4 line then built the A3.1-A3.4 contracts, the scorers and the
calibration runner on a branch that never carried the engine. **No branch
currently holds both at their current versions.**

RC3's own commit message is consistent with this: it lists
`rc3_scoring / rc3_record / rc3_acceptance / rc3_ceiling /
rc3_calibration_worlds / rc3_calibration_runner / rc3_provenance` - everything
*downstream* of a completed case execution, plus calibration. Not the execution.

## 3. What RC4 *can* do

This is a scope gap, not a broken freeze. Case **content** generation is
healthy: `pb_31`'s row comparison rebuilds all **380** case records
deterministically and reports `case_records_total: 380`,
`case_records_changed: 19` (the F16 repair, as designed),
`non_f16_case_records_changed: 0`, `row_integrity_verified: true`. It is
specifically case **execution** that is absent.

Present, frozen and callable:

* case content generation and hashing (`generator`, `artifacts.build_all`, truth manifests)
* registry population, partition counts (20 families x 4 = 80 Development), endpoint applicability
* expression parse, effective support, family classification, G2 event (`g2_contract`)
* G3 safety events and scoring (`g3_contract`, `rc3_scoring`)
* structural acceptance predicate and its re-derivation from a record's own inputs (`structural_acceptance`, `rc3_acceptance`)
* ceiling estimator with its sklearn pin (`rc3_ceiling`)
* A1 adequacy **decision** given contrast records (`adequacy`)
* A3.4 parameter recovery and predictive equivalence scorers (`a34_*`)
* PySR search at the frozen settings digest `36c1ef3c...` (`rc3_calibration_runner.PySRBackend`)
* the A3.2 null calibration, executed once and VALID

## 4. What must be built before Development can run

Every item below is currently unwritten. Each is a scientific implementation
decision surface, which is why it must not be improvised during an execution
task.

1. **Development search-seed derivation** and a declared seed band disjoint from the calibration band (2_110_000_000..2_146_999_929) and the engineering smoke band (1_900_000_000..1_900_999_999).
2. **Case-to-search adapter**: build the design matrix, target and train/validation split for one benchmark case, so the frozen `PySRBackend` can run on it.
3. **Per-case multi-seed driver** with the calibration runner's failure and resume semantics, producing 30 seed records per case.
4. **Selection rule** across the 30 seeds yielding `selection_count`, `valid_r2`, `complexity`, `invalid_fraction`.
5. **Fold-local scalar target construction** wired into the case. `protocol.fit_training_scalar` / `estimate_one` are compliant helpers but are called by tests only.
6. **M0/M1/M2/M3 fitter and leave-one-energy-out stage** producing `CompoundContrastRecord`s. The executable stage exists only as `src/muru/adequacy/` on `engineering/muru-completion`, a branch without `paper_benchmark`.
7. **Falsification rung executor** for `REQUIRED_FALSIFICATION_RUNGS`.
8. **Ceiling input assembly** per case (`compounds` frame, target, candidate test R2).
9. **`CaseExecutionRecord` assembly** and its provenance sidecar.
10. **Secondary endpoint invocation** per case for the A3.4 scorers.
11. **Threshold-table binding**: load the VALID A3.2 table and stamp its digest.

## 5. Consequence for FM-06 and FM-07

The executable-freeze gate asks for production-path conformance and explicitly
warns that a compliant helper is not sufficient. The trace resolves as:

* **FM-06 (fold-local, non-transductive target construction).** `muru.paper_benchmark.protocol.fit_training_scalar` refuses non-training rows and `estimate_one` refuses more than one compound, so the helpers are structurally fold-local. Their only callers are `tests/test_paper_benchmark_protocol.py` and `tests/test_paper_benchmark_adequacy.py`. **No production caller exists.**
* **FM-07 (strict evaluator semantics).** `contract.validate_candidate` / `StrictCandidate` are called only by `tests/test_paper_benchmark_contract.py`. The real parse-and-evaluate surface (`g2_contract._safe_parse`, the `sympy.lambdify` path in `a34_predictive_equivalence`) is exercised only by `tests/test_a34_*`. **No production caller exists.**

Both gates are therefore **UNRESOLVABLE, not failed**: there is no production
call graph to trace. Held-out path identity (same backend, settings, grammar,
selection rules, threshold, representation, endpoints, failure semantics,
differing only in partition identity and seeds) likewise cannot be established
against a Development path that does not exist.

## 6. Recommended disposition

Development stays UNOPENED. The next authorization should be an engineering
release (RC5) that merges the executable engine into the RC4 contract lineage
and supplies items 1-11 above, blind to every partition, followed by a fresh
Development authorization. Executing Development through an improvised pipeline
would defeat its only purpose, which is to validate the exact path Held-out will
later use.
