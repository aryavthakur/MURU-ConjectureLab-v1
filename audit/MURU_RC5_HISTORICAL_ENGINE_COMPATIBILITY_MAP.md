# MURU RC5 — Historical Engine Compatibility Map

ENGINEERING FORENSICS ONLY. READ ONLY. No cherry-picking, merging, implementation
or Development execution was performed to produce this document.

Scope: `engineering/muru-completion` at `c7c2332` (Engineering RC2) compared
against current prospective authority — Amendments A3.1–A3.4, Engineering RC3 /
RC3.1, RC4, RC4.1 environment closure (tags `engineering-rc3-a3-1`,
`engineering-rc3-1-a3-2`, `engineering-rc4-a3-4`,
`engineering-rc4-1-environment-closure`).

---

## 0. Method

Every historical file discussed below was read from `c7c2332` via
`git show c7c2332:<path>`. Every current-authority file was read from
`engineering-rc4-1-environment-closure`, the newest RC tag, via the same
mechanism. File identity was established with `git rev-parse <ref>:<path>`
hash comparison, not by name or docstring similarity. No file was checked out
or modified; no test was run.

---

## 1. The load-bearing forensic finding: two lineages from one ancestor

`git merge-base HEAD c7c2332` = `adf7b3b` ("Objective-alignment validation
complete: DO NOT AUTHORIZE PHASE 4"). **`c7c2332` is NOT an ancestor of the
current authority lineage.** The two branches diverged at `adf7b3b` and were
never merged back together.

A full comparison of every `src/muru/**` path present in *both* trees shows
the divergence with unusual cleanliness:

| Category | Files | Status |
|---|---|---|
| Phase 1/2/3 substrate present in both trees | `io/manifest.py`, `io/massbank.py`, `io/mzml.py`, `discovery/__init__.py`, `discovery/checkpoint.py`, `discovery/engine.py`, `discovery/equivalence.py`, `discovery/estimate.py`, `discovery/falsify.py`, `discovery/grammar.py`, `discovery/nulls.py`, `discovery/phase_boundary.py`, `discovery/protocol.py`, `energy.py`, `features.py`, `identity.py`, `models.py`, `molecules.py`, `objval/*` (9 files), `screen.py`, `spectra.py`, `splits.py`, `synth/*` (4 files) | **byte-identical** (`git rev-parse` hash equal) in both trees |
| `src/muru/__init__.py` | 1 file | differs (docstring/version only — current authority stripped the module inventory docstring) |
| Historical-only, added by Engineering RC2 (`c7c2332`) | `pipeline.py`, `budget.py`, `provenance.py`, `runtime.py`, `governance.py`, `cli.py`, `adequacy/*` (6 files), `estimators/*` (2 files), `symbolic/*` (6 files), `evaluation/*` (3 files) | **absent** from current authority `src/muru/` |
| Current-authority-only, added by A3.1–RC4.1 | `paper_benchmark/*` (24 files: `contract.py`, `adequacy.py`, `structural_acceptance.py`, `g2_contract.py`, `g3_contract.py`, `calibration_contract.py`, `rc3_*.py` ×8, `registry.py`, `governance.py`, `freeze.py`, `preflight.py`, `protocol.py`, `generator.py`, `truth.py`, `artifacts.py`, `analysis.py`) | **absent** from historical `c7c2332` |

**Reading:** everything built before the divergence (raw data I/O, molecule/
identity/descriptor plumbing, the frozen Phase 3 discovery/falsification
stack, the Type‑2 objective-validation study, synthetic generators) is shared,
untouched, common ancestry — it is not "historical engine to port," it is
already the same code in both trees. Everything built *after* the divergence
is where the two lineages solved the same problems independently and wrote
different code: Engineering RC2 built `pipeline.py` + `adequacy/` +
`estimators/` + `symbolic/` + `evaluation/` as free-standing packages: the
current authority instead built one `paper_benchmark` package containing its
own decision contract, its own ceiling estimator, its own PySR backend, and
its own atomic-artifact writer. **RC5 is the first point at which these two
post-divergence branches must be reconciled** — which is the reason this audit
exists.

A second, decisive piece of evidence: `paper_benchmark/protocol.py` and
`paper_benchmark/contract.py` in current authority are literally named
*"Minimal fold-local scalar adapter boundary **for the locked implementation**"*
and *"Strict evaluator input contract **for a future locked MURU engine**"* —
placeholder stub interfaces (a few dozen lines each) that current authority
already committed as the seam where a real fold-local estimator and a real
strict symbolic evaluator are expected to be plugged in. Separately,
`paper_benchmark/structural_acceptance.py`'s `CEILING_ESTIMATOR_SPEC` records
its own dependency pin provenance as `"requirements.lock.txt at
c7c23324d40cd432bdd14bf9d3292b5a2867ef9e"` — i.e. current authority already
cites `c7c2332` by hash as the source of an engineering constant. Both are
independent confirmations, from current authority's own source, that
Engineering RC2's fold-local/strict-evaluator code is the intended donor for
this exact reconciliation.

---

## 2. Classification legend

- **DIRECTLY_REUSABLE_ENGINEERING** — same code already runs unchanged in both
  trees, or is generic engineering with no science-bearing constant that could
  drift.
- **REUSABLE_AFTER_MECHANICAL_ADAPTER** — the algorithm/contract is
  scientifically identical or explicitly awaited by a current-authority stub;
  only import paths, type re-homing, or a narrow signature change are needed.
- **SEMANTICS_CHANGED_DO_NOT_REUSE** — the historical module encodes a
  decision/threshold/freeze that current authority has superseded; reusing it
  would import stale scientific content even though the code still runs.
- **HISTORICAL_ONLY_NO_PROSPECTIVE_AUTHORITY** — frozen to a track that is
  immutably closed (Phase 3, "STOP BEFORE PHASE 4") or superseded within its
  own historical lineage; no current authority exists for it and none should
  be manufactured by reuse.
- **UNRELATED** — no correspondence; listed only where a name collision could
  cause a reviewer to wrongly assume one.

---

## 3. Component-by-component map

### 3.1 Provenance, atomic writes, manifests — DIRECTLY_REUSABLE_ENGINEERING

| Symbol | Source | Evidence |
|---|---|---|
| `sha256_file`, `sha256_bytes`, `FileRecord`, `Manifest` (build/write/verify/corpus_digest) | `c7c2332:src/muru/io/manifest.py` | **Byte-identical** to `engineering-rc4-1-environment-closure:src/muru/io/manifest.py` (hash equal). Already the current-authority file; nothing to port. |
| `ExperimentManifest` (git_state, source_hash, environment, dependency_lock, capture/write/read, `deterministic_view`/`manifest_hash`, `reproducibility_report`, `matches`) | `c7c2332:src/muru/provenance.py` | Absent by name from current authority, but the atomic-write idiom (`tmp = p.with_suffix(".tmp"); ...; os.replace(tmp, p)`) is independently reimplemented verbatim in `paper_benchmark/artifacts.py:_write_atomic` and in `rc3_calibration_runner.py`'s `SeedRecordStore.append`. Pattern convergence confirms the idiom is correct for this codebase; the class itself (git+source+env+dependency-lock capture in one object) has no current-authority equivalent and is a clean drop-in for RC5's own experiment manifests. |
| `Store` (`discovery/checkpoint.py`): unit-level checkpoint tree, atomic tmp+`os.replace` write, `pending()`/`read_world()` resume | `c7c2332:src/muru/discovery/checkpoint.py` | Byte-identical, present unchanged in current authority tree — but see §3.7: it is Phase‑3‑scoped legacy, carried along, not wired into `paper_benchmark`. The **atomic-write mechanism** is DIRECTLY_REUSABLE; the **class as the resume mechanism for RC5's Development-case search** is REUSABLE_AFTER_MECHANICAL_ADAPTER (§3.7), since current authority's own `SeedRecordStore` independently converged on the same append-only, resume-by-omission design for calibration, validating the pattern for the not-yet-built Development search loop. |

### 3.2 Runtime, budget, seed orchestration — DIRECTLY_REUSABLE_ENGINEERING

| Symbol | Source | Notes |
|---|---|---|
| `cap_threads`, `derive_seed`, `seed_list`, `seed_manifest`, `get_logger`/`setup_logging` | `c7c2332:src/muru/runtime.py` | Generic engineering: SHA-256-derived deterministic seed offsets from a `SEED_BASE` chosen to be non-colliding with every *other* historical seed band, numerical-thread pinning, stderr logging setup. No scientific threshold. Current authority derives its **own** disjoint seed base for `paper_benchmark` (`PB_SEED_BASE = 2_110_000_000`, `PB_SEED_SPREAD = 370_000` in `calibration_contract.py`) using the identical `hashlib.sha256(...)[:4] % spread` construction — same algorithm, different band, by design (`runtime.py`'s own docstring: "deliberately not bit-compatible... so a new experiment cannot silently collide with a recorded one"). RC5 should either adopt `runtime.py` directly and derive a fourth disjoint band, or continue the current-authority pattern; either is a direct port of the *algorithm*, not an adapter. |
| `RuntimePolicy`, `Deadline`, `BudgetExceeded`, `BUDGETED_OPERATIONS` | `c7c2332:src/muru/budget.py` | Declared/enforced, versioned, serializable wall-clock budgets with monotonic clock, explicit `unlimited()`, and a typed `TIMEOUT` failure mode rather than truncated-success. No scientific content — this is exactly the runtime-governance layer RC5's Development execution needs and does not yet have anywhere in `paper_benchmark`. No current-authority equivalent exists (`rc3_calibration_runner.py` has an ad hoc `signal.alarm`-based `_wall_clock_budget` context manager for one seed only — narrower, not a general declared-budget object). Direct port. |

### 3.3 Real-data governance boundary — REUSABLE_AFTER_MECHANICAL_ADAPTER (narrow)

| Symbol | Source | Notes |
|---|---|---|
| `real_data_allowed`, `require_real_data`, `real_data_authorized`, `classifies_as_real_data`, `guard_path`, `status` | `c7c2332:src/muru/governance.py` | General-purpose, env-var-gated (`MURU_REAL_DATA_ALLOWED`) real-data read boundary, distinct from and layered under phase-gate logic. **No top-level `src/muru/governance.py` exists in current authority** (`git ls-tree` returns empty). Current authority instead has `paper_benchmark/governance.py`, a narrower, purpose-built *"Held-out execution refusal gate"* (`HeldOutAccessRefused`, `ImplementationLock`, `assert_held_out_execution_allowed`) that checks an implementation-commit lock plus content hashes plus a clean tree — a different, more specific mechanism for a different question ("may Held-out be touched" vs. "may any real measurement be read"). These are complementary, not duplicative: RC5 will need the historical general real-data gate back if it reads real MassBank/mzML data anywhere outside the Held-out path (e.g. Development case construction). Adapter needed: re-add `src/muru/governance.py` as a general module; do not conflate it with `paper_benchmark.governance`, which must stay narrowly scoped to the Held-out lock. |

### 3.4 The M0/M1/M2/M3 adequacy ladder — mixed: decision contract REUSABLE, fitter REUSABLE_AFTER_ADAPTER, freeze pointer SEMANTICS_CHANGED

This is the most consequential and most easily mis-classified area in the
whole audit, so it is split by exactly what each historical file owns.

**a) `adequacy/contract.py` — frozen constants and enums — SEMANTICS_CHANGED_DO_NOT_REUSE as written, but values themselves are unchanged**

`c7c2332:src/muru/adequacy/contract.py` hard-codes
`EFFECTIVE_BENCHMARK_FREEZE = "80a7803"` (tag `benchmark-content-freeze-a2-1`)
and `ORIGINAL_BENCHMARK_FREEZE_V1 = "d94d2c9"`. That freeze is superseded:
current prospective authority is Amendment A3.1 (`c8938e8`, tag
`benchmark-content-freeze-a3-1`, "G2/G3 structural endpoints and calibration
contract") and beyond, through A3.4. Importing `adequacy/contract.py`
unmodified would silently bind RC5 to a stale freeze pointer in every
provenance record it writes. **Do not reuse the module as-is.**

However — the *numeric values* the module carries did not change across the
freeze bump. Diffed field-by-field against
`c7c2332:src/muru/adequacy/contract.py` (transcribing A1 at 80a7803), current
authority's `paper_benchmark/adequacy.py` (transcribing A1 for the current
lineage) carries: `MIN_EVALUABLE_COMPOUNDS=24`, `MIN_PRACTICAL_WINS=20`,
`PRACTICAL_WIN_RATIO=0.90`, `MIN_OBSERVED_ENERGIES=5`,
`LOG_G_BOUNDS=(-2.0, 2.0)`, `LOG_SHAPE_BOUNDS=(-ln 2, +ln 2)`,
`MU_FLOOR=1e-4`, `MU_CEIL=1-1e-4`, `MIN_VERTICAL_AMPLITUDE=0.05`,
`E_REF=45.0`, `COARSE_LOG_G_POINTS=81`, `COARSE_LOG_SHAPE_POINTS=29`,
`REFINEMENT_ROUNDS=3`, `REFINEMENT_POINTS=21`, `REFINEMENT_SHRINK=10`,
`FIT_OBJECTIVE="unweighted_sum_of_squared_mu_residuals"`,
`BOUNDARY_CONTACT_TOL=1e-9`, `BOUNDARY_OUTWARD_PROBE=1e-3` — **identical, every
field**, to `paper_benchmark/adequacy.py`. Amendment A2/A2.1 (the F16
generator fix) did not touch the decision contract, only `generator.py`; the
adequacy math itself is untouched from A1 through the current freeze.

**b) `adequacy/decision.py` — the executable decision rule — REUSABLE_AFTER_MECHANICAL_ADAPTER, verified-conformant already**

`c7c2332:src/muru/adequacy/decision.py` states in its own docstring: *"This is
the executable counterpart of the frozen A1 decision contract... **
`tests/test_eng_adequacy_conformance.py` runs identical constructed records
through this module and through `muru.paper_benchmark.adequacy` and requires
the same typed verdict on every case in the frozen coverage list**."* That is
Engineering RC2's own test-verified claim of behavioral parity with what is
*now, still,* `paper_benchmark/adequacy.py` in current authority (functions
`classify_compound_contrast`, `evaluate_contrast`, `decide_case_adequacy`,
enums `CompoundContrastStatus`/`CaseAdequacyStatus`, `INDETERMINATE_SEVERITY`
precedence, `adequacy_satisfies_g1` — all structurally and numerically
matched, symbol-for-symbol, against the current file). Adapter needed: retarget
imports from `muru.adequacy.contract` to `muru.paper_benchmark.adequacy`;
current `evaluate_contrast` requires the supplied record count to equal
`N_TEST_COMPOUNDS_EXPECTED` exactly (raises `ContractFailure` on
under/over-count) where the historical `run_adequacy_stage` additionally
accepted a caller-supplied `population` override for engineering fixtures —
that override path must be dropped or fenced off from any paper-capable run.
Current authority also layers new functionality on top (`EndpointScore`,
`sensitivity_score`, `m0_specificity_score`, `_held_out_applicable` — the G2/G3
endpoint-scoring machinery, driven by `paper_benchmark.registry`) which has no
historical counterpart and is additive, not something to port.

**c) `adequacy/models.py`, `adequacy/fit.py`, `adequacy/loeo.py` — the fitter and LOEO engine — REUSABLE_AFTER_MECHANICAL_ADAPTER, explicitly awaited**

`paper_benchmark/adequacy.py` states its own scope boundary: *"This module
owns the decision contract. It deliberately contains no fitter, no optimiser,
and no numerical model evaluation: **the locked engine supplied by Engineering
RC 2 performs the leave-one-energy-out fits and reports
`CompoundContrastRecord` values back here**."* That sentence names Engineering
RC2 as the intended source. The three historical modules it refers to:

- `adequacy/models.py`: `ParameterSpec`, `ModelSpec`, `ProfileShape`
  (`from_curve`, `amplitude`, `usable`, `contract_blocker`, `phi`, `s`),
  `model_specs`, `profile_argument`, `predict` — the M0/M1/M2/M3 formula
  definitions against a frozen training-side profile.
- `adequacy/fit.py`: `FitResult`, `_grid_objective`, `objective_at`,
  `_boundary_flags`, `fit_model`, `predict_at` — the frozen deterministic
  coarse-to-fine grid fitter (closed-form for M2/M3, no library optimiser, no
  random restart, lexicographic tie-break), A1.2 verbatim.
- `adequacy/loeo.py`: `CompoundContrastRecord`, `observed_energies`,
  `evaluate_compound_contrast` — the within-compound leave-one-energy-out fold
  loop that produces exactly the `CompoundContrastRecord` type
  `paper_benchmark/adequacy.py`'s `evaluate_contrast` consumes.

`CompoundContrastRecord`'s field set in `c7c2332:src/muru/adequacy/loeo.py`
(`compound_id, detector, observed_energy_count, mae_m0, mae_alt,
execution_state, boundary_contact, unresolved_boundary`) is field-for-field
identical to the dataclass of the same name now defined in
`paper_benchmark/adequacy.py`. Adapter needed: re-home the record type import
(two independent definitions of the same dataclass currently exist; RC5 should
collapse to one, most naturally the `paper_benchmark` one since that is what
the decision layer already imports), and repoint `adequacy/contract.py`
constant imports the same way as in (b). The formula/algorithm content itself
requires no scientific change.

**d) `adequacy/stage.py` — orchestration — REUSABLE_AFTER_MECHANICAL_ADAPTER**

`run_adequacy_stage(curve, trajectories, *, case_id, policy, population,
detectors)` wires (b)+(c) together against a `RuntimePolicy` deadline, turning
an exhausted budget into the frozen `TIMEOUT` state per A1.6 rather than a
truncated success. Its shape (frozen-curve-in, typed-verdict-out, budget-aware)
is exactly what RC5's Development-case adequacy stage needs and does not yet
have as a callable unit anywhere in `paper_benchmark`. Depends on (b), (c),
`budget.py` (§3.2), and `estimators/{base,foldlocal}.py` (§3.5) for the `curve`
argument.

### 3.5 Fold-local scalar estimation — REUSABLE_AFTER_MECHANICAL_ADAPTER, explicitly awaited

| Symbol | Source | Notes |
|---|---|---|
| `SharedCurve` (frozen training-side curve + fingerprint), `ScaleEstimate`, `ScaleTable`, `CurvatureUncertainty`/`UncertaintyModel`, `curvature` | `c7c2332:src/muru/estimators/base.py` | Non-transductive by construction: `estimate_one` is a pure function of one trajectory plus the frozen curve, enforced structurally (array write-protection, one-trajectory-in/one-estimate-out signature) rather than by convention. |
| `FoldLocalCollapse` (`fit`), `CollapseModel` (`estimate_one`, `estimate`) | `c7c2332:src/muru/estimators/foldlocal.py` | Isotonic-knot alternating fit for the shared shape `Phi`, grid + parabolic-refinement search for per-compound `log g`, frozen normalization convention (training compounds at unit geometric-mean scale). This **is** the executable form of `mu_i(E) ~ Phi(E/g_i)` — the MURU core model per the project's own framing. |

Current authority's `paper_benchmark/protocol.py` is titled *"Minimal
fold-local scalar adapter boundary **for the locked implementation**"* and
defines a deliberately tiny placeholder — `FrozenScalarObjects(energy,
training_mean, support)`, `ScalarEstimate(compound_id, log_g, boundary_hit)`,
`fit_training_scalar`, `estimate_one` — whose current implementation is a
crude per-energy mean-residual stand-in (`residual = observed - training_mean;
log_g = clip(-residual, *support)`), nothing like the isotonic/grid-search
machinery of `FoldLocalCollapse`. The field names line up directly:
`FrozenScalarObjects.support` ↔ `SharedCurve.support_log_u`/`log_g_grid`
bounds; `ScalarEstimate.log_g`/`boundary_hit` ↔
`ScaleEstimate.log_g`/`boundary_hit`. This is a stub explicitly waiting to be
filled by the real fitter. Adapter needed: replace the stub's two functions
with calls into `FoldLocalCollapse.fit`/`CollapseModel.estimate_one`, and
either widen `FrozenScalarObjects` to the full `SharedCurve` shape or keep it
as a narrow view constructed from one. No scientific decision is implied by
this port — A3.1–A3.4 do not redefine the collapse model itself, only the
acceptance predicate built on top of it (§3.4, §3.8).

### 3.6 Symbolic search infrastructure (engine-agnostic layer) — REUSABLE_AFTER_MECHANICAL_ADAPTER

| Symbol | Source | Notes |
|---|---|---|
| `Candidate` (round-trippable via `srepr`, `to_dict`/`from_dict`), `pareto_front`, `best_by_complexity`, `elbow_pick` | `c7c2332:src/muru/symbolic/candidate.py` | Fixes a real defect in the frozen Phase 3 `discovery.engine.Candidate` (`as_dict` with no inverse). Pareto handling: best validation score at each complexity, monotone-ceiling front. Elbow rule (master plan 13.4): simplest candidate within `tol` of best, string-tiebroken for reproducibility. No current-authority equivalent exists anywhere in `paper_benchmark` — RC5 has not yet built a Development-case candidate search loop. |
| `canonical_form`, `rationalize_exponents`, `canonical_key`, `key_lattice`, `numeric_key`, `equivalence_key`, `group_equivalent`, `dedupe`, `DuplicateGroup` | `c7c2332:src/muru/symbolic/canonical.py` | Two-key dedup (syntactic `canonical_key`, cheap/conservative; behavioral `numeric_key` on a fixed deterministic Latin-hypercube lattice, positive-scale-normalized). The positive-scale (not affine) normalization is a direct encoding of the collapse model's own identifiability ("`g` is identified only up to positive multiplicative constant") — this is the *same* structural assumption `estimators/base.py`'s `SharedCurve` encodes, and it has not changed in A3.1–A3.4 (only the acceptance predicate downstream of the model changed). No science content is added by porting this file; it needs it unchanged. |
| `evaluate_strict`, `compile_expr`, `apply_compiled`, `is_real_valued`, `finite_mask`, `comparison` | `c7c2332:src/muru/symbolic/protected.py` | Documents and fixes a real defect in the frozen `discovery.grammar.evaluate`: sympy constant-folding a sub-expression to a complex number (`sqrt(-1.5)*x`) silently discards the imaginary part under `np.asarray(..., float)`, scoring an expression that left the reals as valid. `discovery.grammar` is left untouched (frozen, Phase-3-baked); this is the strict replacement for new code. |
| `SymbolicEngine` (protocol), `BaseEngine`, `register_engine`, `get_engine`, `available_engines`, `engine_report`, `EngineUnavailable` | `c7c2332:src/muru/symbolic/engines.py` | Availability-as-first-class-answer registry: importing the package never fails because PySR/gplearn/Julia are absent; only *running* an unavailable engine raises. |
| `PySREngine`, `GPLearnEngine`, `RandomSearchEngine` | `c7c2332:src/muru/symbolic/adapters.py` | `PySREngine` explicitly delegates to `muru.discovery.engine.PYSR_CONFIG` rather than restating it (see §3.6.1 below for the numeric comparison). `RandomSearchEngine` exists solely so the orchestration/ranking/report path has an executable, dependency-free test double — genuinely useful for RC5 CI regardless of which real engine is wired in. |
| `SearchProblem`, `Objective`, `WeightedR2Objective`, `Score` | `c7c2332:src/muru/symbolic/problem.py` | The train/valid/weight/objective contract every engine receives; replaces an eight-positional-argument ad hoc signature. Independent of any specific benchmark freeze. |

Directly analogous to §3.5: `paper_benchmark/contract.py`
(*"Strict evaluator input contract **for a future locked MURU engine**"* —
`StrictCandidate(expression, predictions, grammar_version)`,
`validate_candidate`) is a deliberately minimal placeholder occupying exactly
the seam `symbolic/protected.py` + `symbolic/candidate.py` would fill.
`validate_candidate`'s two checks (non-complex, all-finite) are a strict
subset of what `evaluate_strict`/`finite_mask` already do at full strength.

**3.6.1 PySR invocation — numeric hyperparameter comparison (the one place the mission explicitly demands checking inputs/defaults/optimization/randomness):**

| Parameter | Historical `PYSR_CONFIG` (`discovery/engine.py`, "master plan 13.3") | Current `SEARCH_SETTINGS` (`calibration_contract.py`, "Amendment A3.1 frozen search settings") |
|---|---|---|
| `niterations` | 40 | 40 |
| `populations` | 15 | 15 |
| `population_size` | 33 | 33 |
| `parsimony` | 0.0032 | 0.0032 |
| `adaptive_parsimony_scaling` | 20.0 | 20.0 |
| `deterministic` | True | True |
| `binary_operators` | `["+","-","*","/"]` (`grammar.BINARY_OPERATORS`) | `["+","-","*","/"]` |
| `unary_operators` | `["sqrt","log","square","cube","inv"]` (`grammar.UNARY_OPERATORS`) | `["sqrt","log","square","cube","inv"]` |
| `maxsize` | `grammar.MAX_COMPLEXITY` | `MAX_COMPLEXITY` |
| parallelism | `"serial"` | `"serial"` (`procs=0`) |
| `nested_constraints` | `dict(grammar.NESTED_CONSTRAINTS)` — **passed to `PySRRegressor`** | **not passed** by `PySRBackend._make_regressor` — no `nested_constraints` kwarg present |

**Every scored hyperparameter is an exact numeric match.** This is unusually
strong evidence: the frozen Phase‑3 PySR configuration was carried forward
verbatim into Amendment A3.1's "frozen search settings" rather than being
re-derived. Classification: `run_pysr`/`PYSR_CONFIG` in `discovery/engine.py`
and the `PySREngine` adapter in `symbolic/adapters.py` are
**REUSABLE_AFTER_MECHANICAL_ADAPTER** for RC5's Development-case search
engine — retarget the config source from `discovery.engine.PYSR_CONFIG` to
`paper_benchmark.calibration_contract.SEARCH_SETTINGS`, and **close the one
real gap**: current authority's `PySRBackend` does not pass
`nested_constraints` to `PySRRegressor` at all, where the historical engine
does. This is a genuine, checkable difference in the searched grammar (nesting
depth constraints on unary operators) and must be resolved as a named decision
before RC5 relies on either path — it is flagged here as an open item, not
silently reconciled by this audit (§5).

`discovery/engine.py`'s `GPLEARN_CONFIG` (comparison-arm hyperparameters) has
no current-authority counterpart at all — `paper_benchmark` has no gplearn
backend of any kind. If RC5 needs a gplearn comparison arm, `GPLEARN_CONFIG` +
`run_gplearn` + `GPLearnEngine` are REUSABLE_AFTER_MECHANICAL_ADAPTER on the
same terms as the PySR path, with no current-authority frozen settings to
cross-check against (a scientific decision, not an engineering one, would be
needed to freeze one).

### 3.7 Falsification — split verdict

| Symbol | Source | Classification |
|---|---|---|
| `run_harness` (F1–F12), `affine_refit`, `r2_after_refit`, `_cluster_holdout`, `_influence`, `_ablations`, `_energy_subsets`, `_negative_controls`, `_mass_only_reference` | `c7c2332:src/muru/discovery/falsify.py` | **HISTORICAL_ONLY_NO_PROSPECTIVE_AUTHORITY as a whole harness.** Runs on the frozen Phase 3 `grammar.evaluate`/`estimate.fit_collapse` path and answers "is this discovered-on-real-data candidate an artifact" — a question scoped to Phase 3, which carries the immutable verdict **"STOP BEFORE PHASE 4,"** never reopened. `adequacy/stage.py`'s own docstring is explicit that this harness and the M0/M1/M2/M3 ladder "are different systems and neither substitutes for the other." Byte-identical, present unchanged in current authority's tree, but not imported by anything in `paper_benchmark` — it is carried-along legacy, exercised only by `tests/test_p3_falsify.py`. |
| Individual rung *procedures* (not the harness as a whole) | same file | **Plausibly REUSABLE_AFTER_MECHANICAL_ADAPTER, unverified at function-body level.** `paper_benchmark/structural_acceptance.py` defines a `FalsificationRung` enum for its own Gate 8 ("reduced falsification harness"): `F1_REPRODUCIBILITY`, `F4_COMPOUND_HOLDOUT`, `F5_SCAFFOLD_HOLDOUT`, `F7_INFLUENCE_DROP`, `F9_ENERGY_SUBSET`, `F10_NEGATIVE_CONTROL` — a *named subset* of the historical F1–F12 numbering, and the historical file's private helpers correspond by evident purpose (`_cluster_holdout`→F5, `_influence`→F7, `_energy_subsets`→F9, `_negative_controls`→F10, `_ablations`→F4-shaped, `affine_refit`/`r2_after_refit`→F1-shaped). `structural_acceptance.py` currently implements only the pass/fail *aggregation* (`check_falsification_harness`) and states it is "the REFERENCE CONTRACT; production integration is RC3" — i.e. it does not yet compute any rung's PASS/FAIL itself. This is a real, non-obvious reuse opportunity but **requires verification the audit did not complete**: `discovery/falsify.py`'s rungs run against the Phase-3 `grammar.evaluate`/transductive `estimate.fit_collapse` path (§3.4/§3.5's superseded, leaky estimator), so each procedure would need its data plumbing re-pointed to the fold-local, non-transductive path before reuse — a materially larger adapter than a re-import. Flagged for a follow-up read of `run_harness`'s body against each `FalsificationRung`, not resolved here. |

| `Store` as RC5's Development-search resume mechanism | `c7c2332:src/muru/discovery/checkpoint.py` | **REUSABLE_AFTER_MECHANICAL_ADAPTER.** See §3.1: current authority's `rc3_calibration_runner.SeedRecordStore` independently reinvented an append-only, resume-by-omission JSON store for calibration seeds — different concrete layout (one growing append file per world vs. one file per `(block, world, unit)`), same principle, same atomic-write idiom. RC5's Development-case search (many cases × many seeds, not yet built anywhere in `paper_benchmark`) is a closer structural match to `Store`'s per-unit granularity than to `SeedRecordStore`'s per-world append log, since Development seeds are not required to be strictly ordered/appended the way calibration's monotonicity canary requires. Either is defensible; `Store` is offered as the more directly reusable of the two for this specific use. |
| `discovery/protocol.py` (`WorldData`, `build_world_data`, `run_seed`, `aggregate`, `accept`), `discovery/estimate.py` (`fit_collapse`, transductive) | same commit | **HISTORICAL_ONLY_NO_PROSPECTIVE_AUTHORITY**, and already superseded *within the historical lineage itself* — `estimators/foldlocal.py`'s own docstring names `discovery.estimate.fit_collapse` as the transductive predecessor it replaces because of a measured leakage defect (perturbing one compound moves another compound's `g_hat` by up to 0.099). `discovery/protocol.py`'s seed derivation and group-splitting are likewise already superseded within `c7c2332` by `runtime.py` (§3.2) and `evaluation/splits.py` (§3.8). Do not resurrect either file; their replacements are what to port. |
| `discovery/grammar.py` (`BINARY_OPERATORS`, `UNARY_OPERATORS`, `NESTED_CONSTRAINTS`, `evaluate`, `complexity`, `parse`, `variable_support`) | same commit | **Split verdict.** Frozen by `PHASE3_PREREGISTRATION.md`, not to be edited or reused *as the scored evaluator* (superseded by `symbolic/protected.py`'s strict evaluator, §3.6). But its **constants** (`BINARY_OPERATORS`, `UNARY_OPERATORS`, `MAX_COMPLEXITY`) are exactly what current authority's `SEARCH_SETTINGS` transcribes verbatim (§3.6.1) — as *data*, unattached to the frozen evaluator's behavior, these constants are DIRECTLY_REUSABLE (indeed already reused, independently, by current authority). `complexity()` and `parse()` are generic sympy utilities with no frozen-evaluator dependency and are reasonable to reuse directly by `symbolic/candidate.py`, which already does so historically. |

### 3.8 Evaluation utilities — DIRECTLY_REUSABLE_ENGINEERING / REUSABLE_AFTER_MECHANICAL_ADAPTER

| Symbol | Source | Notes |
|---|---|---|
| `weighted_r2`, `weighted_mae`, `weighted_rmse`, `per_unit_errors`, `cluster_bootstrap`, `paired_bootstrap` | `c7c2332:src/muru/evaluation/metrics.py` | Single-implementation consolidation of a statistic that existed three times historically (and disagreed with none of them per its own conformance test). No frozen scientific threshold; DIRECTLY_REUSABLE. |
| `Split`, `greedy_group_assignment`, `kfold_by_group`, `holdout_by_group`, `split_for_scheme`, `verify_no_leakage` | `c7c2332:src/muru/evaluation/splits.py` | `kfold_by_group` explicitly delegates to `muru.splits.grouped_folds` (part of the shared, byte-identical substrate, §1) for bit-identical Phase 2 behavior; `holdout_by_group` is new, scaffold-size-aware greedy assignment. Generic, DIRECTLY_REUSABLE. |
| `ModelSpec`, `standard_ladder`, `ComparisonPlan`, `ComparisonResult`, `run_comparison` | `c7c2332:src/muru/evaluation/compare.py` | **Caution — name collision, not the same M0/M1/M2/M3.** This module's docstring says *"the M0/M1/M2/M3 ladder as data"*, but it is the Phase 2 **FLEXIBLE PREDICTIVE BENCHMARK** baseline ladder (`BASELINES.md`), a declarative comparison-plan abstraction for predictive baselines — a different object from the adequacy M0/M1/M2/M3 generative-model ladder in §3.4. The declarative `ComparisonPlan`/`run_comparison` *pattern* is REUSABLE_AFTER_MECHANICAL_ADAPTER as generic comparison infrastructure if RC5 needs a baseline ladder; it must not be assumed to be, or wired as, the adequacy engine. |

### 3.9 Pipeline orchestration and CLI — REUSABLE_AFTER_MECHANICAL_ADAPTER (pattern), not a drop-in

| Symbol | Source | Notes |
|---|---|---|
| `ExperimentConfig`, `ExperimentResult`, `run_experiment`, `_search_contract`, `_null_curve`, `_rank`, `_score_recovery`, `_write` | `c7c2332:src/muru/pipeline.py` | The end-to-end shape — registry-lookup-driven stages, budget-`Deadline` checks between stages, a single `to_dict()`/`report()` pair so the human-readable report cannot drift from the machine artifact, atomic `_write` — is sound orchestration engineering with no current-authority equivalent (`paper_benchmark` has no single case-level orchestrator yet; RC3/RC3.1 built `rc3_calibration_runner.py`, which orchestrates *calibration worlds*, not Development cases). **Not a drop-in**: every science-bearing call site is stale or absent in current authority — `sources.load`/`nulls.get_null` (historical-only, not audited above; out of the mission's named focus areas but noted as a dependency), the `muru.adequacy` import path (§3.4, needs retargeting), and the acceptance logic in `_rank` (uses the historical `falsification_harness`/`model_adequacy` boolean pair, which must be replaced by a call into `paper_benchmark.structural_acceptance.evaluate_structural_acceptance`, an 8-gate predicate with no historical equivalent — `_rank`'s 4-condition check is a strict subset). Recommendation: use `pipeline.py` as an architectural reference when writing RC5's Development-case orchestrator, not as code to import. |
| `build_parser`, `cmd_info`, `cmd_check`, `cmd_run`, `cmd_manifest`, `main` | `c7c2332:src/muru/cli.py` | Thin argparse wrapper entirely over `pipeline.run_experiment`; inherits `pipeline.py`'s classification exactly. `cmd_check`'s "resolve every registry name and report authorization without executing anything" pattern is worth keeping independent of the rest. |

---

## 4. Implementation dependency graph

```
historical symbol                          prospective interface                    required adapter                                  authority source
────────────────────────────────────────    ──────────────────────────────────────  ─────────────────────────────────────────────────  ──────────────────────────────────
estimators/foldlocal.FoldLocalCollapse   →  paper_benchmark/protocol.py stub      →  replace fit_training_scalar/estimate_one bodies   →  paper_benchmark/protocol.py's own
  .fit / CollapseModel.estimate_one           (FrozenScalarObjects,                    with FoldLocalCollapse.fit /                        docstring: "for the locked
                                               ScalarEstimate)                          CollapseModel.estimate_one; widen or map            implementation"
                                                                                        field names
                                                                                                                                          ↳ produces the SharedCurve that:

adequacy/models.ProfileShape,            →  paper_benchmark/adequacy.py           →  retarget constant imports from                    →  paper_benchmark/adequacy.py's own
  adequacy/fit.fit_model,                    (decision layer only — declares         adequacy/contract → paper_benchmark.adequacy;        docstring: "the locked engine
  adequacy/loeo.evaluate_compound_            "no fitter, no optimiser")             collapse the duplicate CompoundContrastRecord         supplied by Engineering RC 2
  contrast → CompoundContrastRecord                                                  dataclass to one definition                          performs the LOEO fits"

adequacy/stage.run_adequacy_stage        →  (no current-authority equivalent      →  new thin RC5 orchestrator combining the           →  Amendment A1 (frozen, unchanged
                                              callable unit exists yet)                adapters above + budget.RuntimePolicy                math) + budget.py (generic)

symbolic/protected.evaluate_strict       →  paper_benchmark/contract.py stub      →  StrictCandidate.predictions ← evaluate_strict's   →  paper_benchmark/contract.py's own
                                              (StrictCandidate, validate_candidate)   output; validate_candidate becomes a special         docstring: "for a future locked
                                                                                      case of finite_mask + is_real_valued                 MURU engine"

symbolic/adapters.PySREngine,            →  paper_benchmark/calibration_contract  →  retarget PYSR_CONFIG source to                    →  calibration_contract.SEARCH_SETTINGS
  discovery/engine.run_pysr,                 .SEARCH_SETTINGS +                       SEARCH_SETTINGS (already numerically              (Amendment A3.1) — proven byte-for-
  discovery/engine.PYSR_CONFIG               rc3_calibration_runner.PySRBackend       identical, §3.6.1); ADD the missing               byte identical to master-plan-13.3
                                                                                      nested_constraints kwarg (open item, §5)             PYSR_CONFIG on every scored field

symbolic/candidate.Candidate,            →  (no current-authority equivalent      →  direct port; no science-bearing constant          →  none needed — generic engineering
  canonical.{numeric_key,dedupe},             exists — no Development candidate       to reconcile
  pareto_front, elbow_pick                    search loop has been built yet)

discovery/checkpoint.Store               →  rc3_calibration_runner                →  either reuse Store's per-unit layout for          →  pattern validated by
                                              .SeedRecordStore (independent,          Development-case resume, or extend                   SeedRecordStore's independent
                                              narrower — per-world append log)         SeedRecordStore's pattern to per-case grain          convergence on the same idea

provenance.ExperimentManifest,           →  paper_benchmark/artifacts.py          →  direct port for RC5's own experiment-level        →  none needed — generic engineering,
  runtime.RuntimePolicy/derive_seed,          ._write_atomic (independent,             manifests; RC5 derives its own disjoint             already independently validated
  budget.RuntimePolicy                        narrower — partition artifacts only)     PB_SEED_BASE-style band if reusing runtime.py       by artifacts.py / SeedRecordStore
```

---

## 5. Open items this audit surfaces but does not resolve (engineering, not scientific, decisions for RC5 to make explicitly)

1. **`nested_constraints` gap (§3.6.1).** The historical PySR invocation passes
   `nested_constraints=dict(grammar.NESTED_CONSTRAINTS)`; current authority's
   `PySRBackend._make_regressor` does not pass this kwarg at all. Every other
   scored PySR hyperparameter matches exactly. This needs a named decision
   before RC5 treats either path as "the" frozen search settings — it is not
   this audit's place to decide it.
2. **Duplicate `CompoundContrastRecord` definitions.** The historical
   `adequacy/loeo.py` and current `paper_benchmark/adequacy.py` each define
   their own copy of this dataclass, field-identical. RC5 should collapse to
   one canonical definition (recommend `paper_benchmark.adequacy`'s, since the
   decision layer already imports it) rather than carrying two.
3. **Falsification rung reuse (§3.7) is plausible but unverified.** The
   `FalsificationRung` subset in `structural_acceptance.py` names-match a
   subset of historical F1–F12 procedures in `discovery/falsify.py`, but
   confirming reuse requires reading `run_harness`'s body against each rung
   and re-plumbing every rung off the transductive `estimate.fit_collapse`
   path onto the fold-local one — this audit read signatures and docstrings
   only for this file, not full rung-by-rung bodies.
4. **`src/muru/governance.py` (general real-data gate) has no current-authority
   home.** If RC5 reads any real measurement data outside the already-governed
   Held-out lock, this module (or an equivalent) needs to be reintroduced —
   it must not be conflated with the narrower `paper_benchmark.governance`
   Held-out-specific lock.
5. **`sources.py`, `nulls.py`, `models.py` (Phase-2 baseline ladder) and how
   Development-case data actually gets loaded were out of the mission's named
   focus areas and were not audited here** — `pipeline.py`'s `_null_curve`
   and stage 1 (`sources.load`) depend on them, and any adapter that reuses
   `pipeline.py`'s shape will need a parallel audit of those modules against
   `paper_benchmark/generator.py`/`registry.py` before it can run.

---

**RC5 HISTORICAL ENGINE COMPATIBILITY MAP READY**
