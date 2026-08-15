# MURU reproducibility inventory

Companion to `MURU_MANUSCRIPT_PRE_RESULTS.md`, Section 12.

**Scope rule.** Engineering smoke is infrastructure, not scientific evidence,
and is marked as such throughout. Nothing in this inventory records a
prospective outcome; where an artifact will exist only after execution, it is
listed with the status `NOT YET CREATED`.

Governance base of this inventory: **`560bf28568e2762c60edc994aac7f2b6de14081f`** (tag `benchmark-content-freeze-a3-5`, annotated tag object `533777b7`), following `be23b80` (`benchmark-content-freeze-a3-4`) with the A3.4 Temporal Provenance Erratum at `220c9cb` (`a3-4-temporal-provenance-erratum`). Engineering parent `69e33c778efb14362439941d25ebbfcfb1068284` (tag `engineering-rc4-2-1-integrity-closure`); A3.5's executable implementation is Engineering RC5 on `eng/muru-rc5-a3-5`. The science and engineering lineages are siblings, not one merged history.

---

## 1. Branch structure

The repository separates science governance branches from engineering
implementation branches, and merges the science lineage into the engineering
lineage rather than the reverse.

| Branch | Role |
|---|---|
| `main` | Phase 1 baseline; real-data arm only, no discovery engine |
| `phase2`, `phase3-discovery-engine` | historical real-data and discovery phases |
| `objective-validation-type2` | historical prospective Type 2 study |
| `science/muru-paper-benchmark` | prospective benchmark content freeze V1 |
| `science/muru-paper-benchmark-adequacy-amendment` | Amendment A1 |
| `science/muru-paper-benchmark-f16-amendment` | Amendments A2 and A2.1 |
| `science/muru-paper-g2-g3-contract-audit` | pre-A3.1 G2/G3 contract audit |
| `science/muru-paper-benchmark-a3-1` | Amendment A3.1 |
| `science/muru-paper-benchmark-a3-2` | Amendment A3.2 |
| `science/muru-paper-benchmark-a3-3` | Amendment A3.3 |
| **`science/muru-paper-benchmark-a3-4`** | Amendment A3.4, current science content freeze |
| `engineering/muru-completion` | strict evaluator and engineering completeness |
| `prep/executable-integration-a2-1` | Engineering RC2 integration, Development preflight |
| `eng/muru-rc3-a3-1` | Engineering RC3 |
| `eng/muru-rc3-1-a3-2` | Engineering RC3.1 |
| **`eng/muru-rc4-a3-4`** | Engineering RC4 (in progress; executable freeze pending) |
| `science/historical-synthetic-consolidation` | historical evidence dossier, claim matrix, failure catalog |
| `audit/engine-competence` | prospective gplearn competence audit |
| `audit/frozen-evaluator-complex-reach` | complex-cast evaluator reach audit |
| `audit/muru-development-adequacy-diagnostic` | development adequacy diagnostic |
| `audit/muru-a3-3-mathematical-audit` | mathematical audit of A3.3 evaluation domain |
| `audit/muru-a3-4-integrity-audit` | mathematical and code integrity review of A3.4 |
| `audit/a3-4-temporal-provenance-erratum` | temporal provenance erratum adjudicating A3.4 EDT chronology |
| `science/wfsr-external-preregistration` | external validation preregistration |
| `claude/muru-paper-env-audit-bf067b` | execution environment readiness audit |
| **`writing/muru-preresults-manuscript-a3-4`** | this manuscript synchronization work; writing only |

**Branch discipline for this work.** The manuscript branch is an isolated
writing branch branching from `6e3dbc9` (`claude/muru-preresults-manuscript-ba5ca5`).
It modifies files under `paper/` only. It is not merged into any active
calibration, evidence, or engineering branch.

## 2. Frozen science commits and tags

| Designation | Commit | Tag |
|---|---|---|
| Benchmark content freeze V1 | `d94d2c9` | none; preserved permanently, never rewritten |
| Amendment A1, adequacy decision rule | `2ac86c5` | `benchmark-content-freeze-a1` |
| A2 F16 governance review (no repair applied) | `4dae072` | none |
| Amendment A2, F16 generator repair | `03cc4d3` | `benchmark-content-freeze-a2` |
| Amendment A2.1, GENERATOR_VERSION bump | `80a7803` | `benchmark-content-freeze-a2-1` |
| G2/G3 contract audit | `34dee8e` | none |
| Amendment A3.1, G2/G3 endpoints and calibration contract | `c8938e8` | `benchmark-content-freeze-a3-1` |
| Amendment A3.2 creation | `5fc7eee` | none |
| Amendment A3.2, commit binding | `1194fcb` | `benchmark-content-freeze-a3-2` |
| **Amendment A3.3**, candidate evaluation domain contract | `71f5369` | `benchmark-content-freeze-a3-3` |
| **Amendment A3.4**, parameter recovery and predictive equivalence contracts | `be23b80` | `benchmark-content-freeze-a3-4` |
| **Amendment A3.5**, symbolic-discovery execution semantics and the corrective Gate-8 architecture | `560bf28` | `benchmark-content-freeze-a3-5` |

## 3. Engineering and audit commits and tags

| Designation | Commit | Tag |
|---|---|---|
| Engineering RC2 | `c7c2332` | none |
| RC2 record | `5235f81` | none |
| RC2 integration verification | `dc95d56` | none |
| Development preflight, all 80 cases executed | `d9e2795` | none |
| Development adequacy diagnostic (closed: low discrimination) | `bc741e3` | none |
| Engineering RC3, A3.1 executable integration | `adfdec0` | `engineering-rc3-a3-1` |
| A3.2 science merge into RC3.1 lineage | `25f58fe` | none |
| Engineering RC3.1, A3.2 implementation | `63632ec` | none |
| Engineering RC3.1 tip, seed-record world binding and settings gate closed | `07c64c8` | `engineering-rc3-1-a3-2` |
| A3.3 mathematical audit | `78cc7c2` | none |
| A3.4 mathematical & code integrity audit | `f1fb943` | none |
| **A3.4 Temporal Provenance Erratum** | `220c9cb` | `a3-4-temporal-provenance-erratum` |
| **Engineering RC4** (A3.4 implementation) | `[RC4 EXECUTABLE FREEZE TO INSERT]` | pending on `eng/muru-rc4-a3-4` |

Historical study commits, for CLASS A traceability:

| Study | Commit |
|---|---|
| Phase 1 close | `5049a1a` (tag `phase1-complete`) |
| Phase 2 close | `0b5e13b` (tag `phase2-complete`) |
| Phase 3 pre-registration freeze | `9ca09e9` |
| Type 2 pre-registration freeze | `307e4e0` |
| Type 2 study close | `adf7b3b` |
| Engine competence audit | `fac0118` |
| Complex-reach audit | `18581a7` |
| Strict evaluator, engineering completeness | `d125f7d` |
| Historical evidence dossier | `f42cc0d` |
| Execution environment audit | `c443a7f` |

## 4. Dependency locks

| Lock | Path | Role |
|---|---|---|
| **RC3 pin source** | `configs/rc3_requirements_lock_c7c2332.txt` | byte-identical copy of `requirements.lock.txt` at RC2 `c7c2332`; SHA-256 `13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8`; **50 pins**, including `pysr==1.5.10`, `sympy==1.14.0`, `gplearn==0.4.3`, `juliacall==0.9.26`, `juliapkg==0.1.25`, `scikit-learn==1.9.0` |
| Phase 1 lock | `requirements.lock.txt` | 39 pins; **omits PySR, SymPy, gplearn and the Julia bridge**; cannot serve as the RC3 pin source |

The RC3 lock lives under `configs/` rather than `artifacts/` because
`artifacts/` is gitignored wholesale, and a runtime dependency guard that reads a
file absent from a fresh clone is not a guard
(`src/muru/paper_benchmark/rc3_provenance.py`).

Version verification reads installed distribution metadata and never imports the
module, because importing `juliacall` ahead of `pysr` segfaults the interpreter.
A mismatch fails loudly.

## 5. Runtime versions

Verified operationally in the execution environment audit (`c443a7f`), and
enforced at runtime by `rc3_provenance.verify_dependencies`.

| Component | Version | Notes |
|---|---|---|
| Python | 3.13.12 | master plan named 3.12; nothing in the lockfiles or the PySR/Julia stack caps below 3.13; deviation recorded, not absorbed |
| PySR | 1.5.10 | exact match to the pin |
| Julia | 1.12.6 | bootstrapped privately by `juliacall`/`juliapkg` under `.venv/julia_env`; no system Julia required |
| SymbolicRegression.jl | 1.11.3 | matches the frozen pin of "SymbolicRegression.jl 1.11" |
| PythonCall.jl | 0.9.26 | |
| gplearn | 0.4.3 | historical comparison arm only; not in the prospective acceptance predicate |
| SymPy | 1.14.0 | used by the G2 support contract for algebraic normalisation |
| scikit-learn | 1.9.0 | **binds the ceiling estimator**; pin parsed from the frozen `CEILING_ESTIMATOR_SPEC` |
| numpy | 2.5.2 | |
| scipy | 1.18.0 | |
| pandas | 3.0.5 | |
| RDKit | 2026.03.5 | real-data arm; the lock writes the same release as `rdkit==2026.3.5`, so a byte comparison against the lock is not a mismatch |
| pyarrow | 25.0.1 | parquet round trip verified |

## 6. Seed namespaces

All randomness is derived, never global.

| Purpose | Namespace or constant | Source |
|---|---|---|
| Benchmark case generation | `derive_seed(case_id, stage)`, prefix `paper-benchmark-v1\|` | `generator.derive_seed`, `generator._rng` |
| Benchmark root seed | `ROOT_SEED = 20260813` | `registry.py` |
| Calibration base-target permutation | `PB\|NCAL\|<world_id>\|BASE_TARGET` | A3.2 Decision 1 |
| Calibration scaffold split | `PB\|NCAL\|<world_id>\|SPLIT` | A3.2 Decision 2 |
| Calibration null-family transformation | `PB\|NCAL\|<world_id>\|null_construction` | `rc3_calibration_worlds.py` |
| Calibration frozen-law draw | `PB\|NCAL\|<world_id>\|law` | `rc3_calibration_worlds.py` |
| Calibration search seeds | `PB_SEED_BASE = 2_110_000_000`, `PB_SEED_SPREAD = 370_000`, 30 seeds per world | `calibration_contract.derive_calibration_seeds` |
| Calibration world ID | `PB\|NCAL\|{construction}\|r{index:03d}`, index 0..99 | A3.1 |
| Predictive equivalence reference frames | `PB\|PRED_EQUIV\|FRAME\|{index:03d}`, index 0..11 | A3.4 |
| Threshold bootstrap | seed `20260812`, 2,000 world-level resamples | A3.1; reporting only |
| Ceiling estimator | `random_state = 0` | `CEILING_ESTIMATOR_SPEC` |
| Engineering smoke | band strictly below the calibration band, wide guard gap, signed-32-bit safe | `rc3_provenance.smoke_seed`, `assert_seed_band_separation` |

Verified seed invariants (A3.1, A3.4): 100 unique world IDs, 100 unique base buckets,
3,000 unique calibration seeds, 12 unique predictive equivalence reference frames, all signed-32-bit safe.

## 7. Benchmark manifests and protected-path digests

### 7.1 Tracked manifests

| Artifact | Contents |
|---|---|
| `artifacts/paper_benchmark_partition_manifest.json` | partition case counts (80 / 240 / 60), version `paper-benchmark-manifest-1.0.0` |
| `artifacts/paper_benchmark_case_manifest.json` | 380 cases with `case_id`, `family`, `variant`, `partition`, `applicable_endpoints`, `content_hash`; version `paper-benchmark-case-manifest-1.0.0` |
| `artifacts/paper_benchmark_truth_manifest.json` | frozen truth payload digests |
| `artifacts/paper_benchmark_hash_inventory.json` | nine SHA-256 digests, version `paper-benchmark-hash-inventory-1.0.0` |
| `artifacts/paper_benchmark_preflight.json` | Development-only preflight record; SHA-256 `fb83d19d3070acd43d562f7d9e76deb57769de4b0341ea6bde03f934130b239a` |
| `artifacts/paper_benchmark_content_freeze.json` | status `WAITING_FOR_LOCKED_IMPLEMENTATION`; `final_executable_freeze: false`; `hashes_verified: true` |
| `artifacts/paper_benchmark_amendment_a1.json` ... `_a3_4.json` | per-amendment integrity records |
| `audit/muru_a3_4_temporal_provenance_erratum.json` | A3.4 Temporal Provenance Erratum audit record |
| `artifacts/confirmation_set_sealed.json` | real-data confirmation seal |

### 7.2 Hash inventory (nine digests)

| Path | SHA-256 |
|---|---|
| `inputs/development.jsonl` | `4f9b51ce477d2833aef42f4703554c5c9462348f199ed95cfae609eaeb40df9f` |
| `inputs/held_out.jsonl` | `7d05d5ab77a5a3a26008c777aea46ee103a7ee63a4fd704a913ae38ecdbe7759` |
| `inputs/challenge.jsonl` | `ed747896deef624a5e884a13c36b78c86348a94c2ebb9883a1e5f015fb6c3b84` |
| `truth/development.jsonl` | `d496ad044317ae495e93a2232eae13011e27d4cc91ce77f5e1b9c1f8fbc87e83` |
| `truth/held_out.jsonl` | `279efb68ada3ad3492c6da8b4c89ab7f4cef6c4869d3bda50df70850d7462aa2` |
| `truth/challenge.jsonl` | `cabf3942045b95b45c2f0fdbb0ecd1cfb3e3d9fe27d55f77cdde85be5e25ec82` |
| `paper_benchmark_case_manifest.json` | `c98b426ade1085abd4c87ab2195e358f83cf9ad1e1a77710f9493f5710b5bdba` |
| `paper_benchmark_partition_manifest.json` | `8aaebb748af0645de95ef056b934396ff72870852c5d7ca25393dbb7bb3d5f10` |
| `paper_benchmark_truth_manifest.json` | `c26595a1a34f59adac54b91a1f8c13cccd5ec0fd924d7af81dff2952027ce477` |

The `inputs/` and `truth/` row-level JSONL files are untracked regenerable bytes
under `.gitignore`. Their digests are the seal: the held-out and challenge rows
are reproduced by re-running the generator and verified against these values,
without any need to read their contents.

### 7.3 Protected paths

| Record | Paths | Aggregate |
|---|---:|---|
| `scientific_contract_protected_paths.json` at `d9e2795` (freeze `80a7803`) | 52 Class-A paths | SHA-256 `4b2280c9a15810908cd548133c8d185938e338356d3b9cd020dc8cf985b5050e` |
| `artifacts/paper_benchmark_amendment_a3_1.json` | 16 protected paths with per-path SHA-256; 11 added paths with per-path SHA-256 | |
| `artifacts/paper_benchmark_amendment_a3_2.json` | 2 added paths; declares A3.1 protected content byte-identical | |
| `artifacts/paper_benchmark_amendment_a3_3.json` | 2 added paths; candidate evaluation domain contract | |
| `artifacts/paper_benchmark_amendment_a3_4.json` | 2 added paths; parameter recovery & predictive equivalence contracts; 12 reference frames | SHA-256 `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44` (aggregate frames digest) |

Each amendment record asserts that every frozen scientific artifact unrelated to
that amendment is byte-identical to its parent, and carries the per-path
verification to support it.

## 8. Governance flags in machine-readable form

`artifacts/paper_benchmark_amendment_a3_1.json`:

```
temporal_position: post_development=true, pre_g2_g3_development_scoring=true,
                   pre_calibration=true, pre_held_out=true
calibration_executed: false
development_g2_g3_scored: false
held_out_sealed: true
test_accounting: a3_1_tests_passed=165, existing_paper_benchmark_tests_passed=161,
                 total_passed=326
```

`artifacts/paper_benchmark_amendment_a3_2.json`, `governance_form`:

```
prospective: true
additive: true
detected_before_calibration_execution: true
informed_by_development_results: false
informed_by_threshold_results: false
informed_by_held_out_results: false
informed_by_confirmation_results: false
a3_1_protected_content_historically_preserved: true
a3_1_scientific_content_otherwise_unchanged: true
```

`artifacts/paper_benchmark_amendment_a3_4.json`, `governance_form`:

```
prospective: true
additive: true
parameter_recovery_applicable_denominator: 156
predictive_equivalence_applicable_denominator: 144
predictive_equivalence_reference_points: 2160 (12 frames x 180 rows)
reference_aggregate_digest: 4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44
temporal_adjudication: A3.4 committed 2026-08-13T15:58:39-04:00 (EDT), preceding
                       A3.4 calibration start 2026-08-13T16:34:55-04:00 (EDT)
```

## 9. Execution manifests

| Manifest | Emitted by | Status |
|---|---|---|
| Dependency provenance manifest | `rc3_provenance.build_provenance_manifest` | emitted at run time; records installed versions, the commit, and the lock digest |
| A3.2 world construction record | `rc3_provenance.a3_2_world_construction` | emitted at run time |
| Calibration seed records, one per `(world, seed)` | calibration runner | **NOT YET CREATED** |
| Calibration threshold table | calibration runner | **NOT YET CREATED** |
| Development run record under A3.4 | Development runner | **NOT YET CREATED** |
| Executable freeze record | freeze machinery | **NOT YET CREATED** (`[RC4 EXECUTABLE FREEZE TO INSERT]`) |
| Held-out scoring record | Held-out runner | **NOT YET CREATED**; guarded, refuses until executable freeze |
| Challenge scoring record | Challenge runner | **NOT YET CREATED** |

## 10. Expected result artifacts

Named here so a reader knows what must appear, and so that their current absence
is explicit.

| Expected artifact | Populates |
|---|---|
| calibration threshold table with bootstrap intervals | Manuscript 7.1, Table 3c, Figure 4D |
| per-construction calibration breakdown | Table 3d |
| calibration validity record (worlds with zero failure seeds, against the 95/100 floor) | Manuscript 7.1, Table 3b |
| Development run summary under A3.4 | Manuscript 7.2, Table 4 |
| Held-out G1/G2/G3 scoring with Wilson intervals | Manuscript 7.3, Table 5, Figure 7A |
| Held-out secondary endpoint scoring (parameter recovery, predictive equivalence, exact algebra) | Manuscript 7.8 to 7.10, Table 5a, Figure 7B |
| Held-out per-family and per-truth-family breakdown | Table 6, Figure 7C |
| G3 component and variant breakdown | Manuscript 7.11, Table 7 |
| Challenge scoring | Manuscript 7.15, Table 8 |
| typed failure census | Manuscript 7.16, Figure 8B |
| executable freeze record and clean-tree confirmation | Manuscript 7.17 |

## 11. Reproduction commands

**Environment.**

```bash
python3 -m venv .venv && .venv/bin/pip install -r configs/rc3_requirements_lock_c7c2332.txt
```

**Rebuild the benchmark from the frozen generator.**

```bash
.venv/bin/python scripts/pb_00_build.py
```

**Development-only preflight.**

```bash
.venv/bin/python scripts/pb_10_preflight.py
```

**Prepare the content freeze record.**

```bash
.venv/bin/python scripts/pb_20_prepare_freeze.py
```

**Engineering smoke.** Infrastructure only; not scientific evidence.

```bash
.venv/bin/python scripts/rc3_smoke.py
```

Calibration, Development rerun, Held-out and Challenge runner entry points:
`[METHOD DETAIL REQUIRES VERIFIED SOURCE]`. The runner API exists in
`src/muru/paper_benchmark/rc3_calibration_runner.py`
(`run_seed`, `run_world`, `run_calibration`); the corresponding `scripts/`
entry point was not present at `07c64c8` and must be recorded here once it is.

## 12. Test commands

```bash
.venv/bin/python -m pytest
```

Fifty-one test modules under `tests/`, with `pythonpath = src` and
`testpaths = tests` from `pytest.ini`. Contract-specific suites:

```bash
.venv/bin/python -m pytest tests/test_a3_1_g2_contract.py tests/test_a3_1_g3_contract.py tests/test_a3_1_structural_acceptance.py tests/test_a3_1_calibration_contract.py tests/test_a3_2_calibration_design.py
```

```bash
.venv/bin/python -m pytest tests/test_rc3_acceptance.py tests/test_rc3_calibration.py tests/test_rc3_ceiling.py tests/test_rc3_provenance.py tests/test_rc3_record.py tests/test_rc3_scoring.py
```

```bash
.venv/bin/python -m pytest tests/test_paper_benchmark_freeze.py tests/test_paper_benchmark_governance.py tests/test_paper_benchmark_denominators.py tests/test_paper_benchmark_truth.py tests/test_confirmation_seal.py
```

Recorded test accounting at A3.1: 165 A3.1 tests passed, 161 existing
paper-benchmark tests passed, 326 total
(`artifacts/paper_benchmark_amendment_a3_1.json`, `test_accounting`).

## 13. Artifact verification commands

```bash
.venv/bin/python scripts/pb_30_amendment_a1_integrity.py
```

```bash
.venv/bin/python scripts/pb_31_amendment_a2_integrity.py && .venv/bin/python scripts/pb_32_amendment_a2_1_integrity.py
```

```bash
.venv/bin/python scripts/pb_33_amendment_a3_1_integrity.py && .venv/bin/python scripts/pb_34_rc3_integrity.py
```

An A3.2 integrity script analogous to `pb_33`/`pb_34` was not present at
`07c64c8`: `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`. A3.2's own record
(`artifacts/paper_benchmark_amendment_a3_2.json`) carries the per-path digests
and governance flags, and `tests/test_a3_2_calibration_design.py` covers the
design contract.

Seal verification for the real-data confirmation set:

```bash
.venv/bin/python -m pytest tests/test_confirmation_seal.py
```

Expected SHA-256, unchanged across every prior study:
`d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07`.

## 14. Artifact matrix

Columns: **Created before or after outcome** distinguishes artifacts fixed
before any prospective number existed from those that can only exist afterwards.
**Evidentiary status** uses the historical dossier's vocabulary plus
`PROSPECTIVE PRIMARY` for the new endpoints.

| Artifact | Purpose | Before / after outcome | Hashed | Tracked | Required for reproduction | Evidentiary status |
|---|---|---|---|---|---|---|
| `src/muru/paper_benchmark/registry.py` | case population authority, metadata only | **before** | yes (protected path) | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/generator.py` | fully synthetic case generation | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/truth.py` | truth schema | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/adequacy.py` | A1 adequacy contract | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/g2_contract.py` | G2 support and family contract | **before** | yes (A3.1 record) | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/structural_acceptance.py` | truth-blind acceptance predicate | **before** | yes (A3.1 record) | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/calibration_contract.py` | calibration protocol and failure semantics | **before** | yes (A3.1 record) | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/g3_contract.py` | G3 unsafe-event classification | **before** | yes (A3.1 record) | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/rc3_calibration_worlds.py` | A3.2 null world construction | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/rc3_calibration_runner.py` | calibration execution, resume semantics | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/rc3_ceiling.py` | ceiling estimator wiring, sklearn pin guard | **before** | yes | yes | yes | CLASS B frozen method |
| `src/muru/paper_benchmark/rc3_provenance.py` | dependency guard, seed-band separation | **before** | yes | yes | yes | CLASS B infrastructure |
| `src/muru/paper_benchmark/rc3_record.py`, `rc3_scoring.py`, `rc3_acceptance.py` | record schema, scoring, acceptance wiring | **before** | yes | yes | yes | CLASS B frozen method |
| `MURU_PAPER_BENCHMARK_PROTOCOL.md` | protocol and execution boundary | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_METRICS.md` | denominators and the three gates | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_CASE_FAMILIES.md` | family definitions | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_FREEZE.md` | freeze definitions and required artifacts | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` | adequacy decision rule | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md`, `_A2_1_...md` | F16 repair and version bump | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md` | G2/G3 endpoints, calibration contract | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md` | null base target and calibration split | **before** | yes | yes | no | CLASS B governance |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A3_3.md` | candidate evaluation domain contract | **before** | yes (`71f5369`) | yes | no | CLASS B governance |
| `audit/MURU_A3_3_MATHEMATICAL_AUDIT.md` | A3.3 mathematical audit | **before** | yes (`78cc7c2`) | yes | no | CLASS B audit |
| `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` | parameter recovery and predictive equivalence contracts | **before** | yes (`be23b80`) | yes | no | CLASS B governance |
| `audit/MURU_A3_4_INTEGRITY_AUDIT.md` | A3.4 mathematical and code integrity audit | **before** | yes (`f1fb943`) | yes | no | CLASS B audit |
| `audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md` | A3.4 temporal provenance adjudication | **before** | yes (`220c9cb`) | yes | no | CLASS B audit erratum |
| `artifacts/paper_benchmark_case_manifest.json` | 380 case hashes and applicability | **before** | yes | yes | yes | CLASS B frozen content |
| `artifacts/paper_benchmark_partition_manifest.json` | partition counts | **before** | yes | yes | yes | CLASS B frozen content |
| `artifacts/paper_benchmark_truth_manifest.json` | truth digests | **before** | yes | yes | yes | CLASS B frozen content |
| `artifacts/paper_benchmark_hash_inventory.json` | nine input/truth/manifest digests | **before** | self | yes | yes | CLASS B seal evidence |
| `artifacts/paper_benchmark_content_freeze.json` | freeze status | **before** | yes | yes | no | CLASS B governance |
| `artifacts/paper_benchmark_preflight.json` | Development-only preflight | **before** | yes | yes | no | CLASS B infrastructure |
| `artifacts/paper_benchmark_amendment_a1..a3_4.json` | per-amendment integrity and governance flags | **before** | yes | yes | yes (verification) | CLASS B provenance |
| `audit/muru_a3_4_temporal_provenance_erratum.json` | A3.4 Temporal Provenance Erratum machine-readable record | **before** | yes | yes | yes (verification) | CLASS B provenance |
| `configs/rc3_requirements_lock_c7c2332.txt` | RC3 dependency pin source | **before** | yes | yes | yes | CLASS B infrastructure |
| `inputs/*.jsonl`, `truth/*.jsonl` | generated case rows | **before** | yes (in inventory) | no, gitignored, regenerable | yes | CLASS B frozen content |
| `scripts/pb_30..pb_34_*.py` | integrity verification | **before** | yes | yes | yes (verification) | CLASS B infrastructure |
| `scripts/rc3_smoke.py` | engineering smoke | **before** | yes | yes | no | **infrastructure, NOT scientific evidence** |
| `tests/` (51 modules) | contract enforcement | **before** | partly | yes | yes | CLASS B infrastructure |
| Dependency provenance manifest | observed versions against the pin | at run time | yes | emitted | yes | CLASS B provenance |
| Calibration seed records | one per `(world, seed)`, append-only | **after** | yes (settings digest, world binding) | **NOT YET CREATED** | yes | CLASS C prospective |
| Calibration threshold table | `T(1..20)` and bootstrap band | **after** | to be hashed | **NOT YET CREATED** | yes | CLASS B/C boundary; calibration |
| Development run record (A3.1/A3.2) | sanity and feasibility | **after** | to be hashed | **NOT YET CREATED** | yes | CLASS C prospective, non-gating |
| Held-out scoring record | G1/G2/G3 and secondaries | **after** | to be hashed | **NOT YET CREATED** | yes | **CLASS C PROSPECTIVE PRIMARY** |
| Challenge scoring record | stress outcomes | **after** | to be hashed | **NOT YET CREATED** | yes | CLASS C prospective, descriptive |
| Executable freeze record | lock verification, clean tree | **after** | to be hashed | **NOT YET CREATED** | yes | CLASS B/C boundary; provenance |
| `artifacts/p3_*.json` | Phase 3 historical | already after (historical) | yes | yes | for CLASS A only | CLASS A historical |
| `artifacts/ov_*.json` | Type 2 historical | already after (historical) | yes | yes | for CLASS A only | CLASS A historical |
| `artifacts/p2_*.json` | Phase 2 real-data historical | already after (historical) | yes | yes | for CLASS A only | CLASS A historical, real data |
| `MURU_HISTORICAL_SYNTHETIC_EVIDENCE.md`, `_CLAIM_MATRIX.md`, `_FAILURE_MODE_CATALOG.md` | historical consolidation | historical | no | yes (`f42cc0d`) | no | CLASS A governance |
| `audit/ENGINE_COMPETENCE_AUDIT_REPORT.md` | comparison-arm competence | historical | no | yes (`fac0118`) | no | CLASS A limitation evidence |
| `artifacts/confirmation_set_sealed.json` | real-data seal | **before**, and unopened since | yes | yes | yes (verification) | seal evidence |
| `artifacts/paper_benchmark_development_*.json` at `d9e2795` | pre-A3.1 Development record | after (pre-A3.1) | yes | yes | no | CLASS C historical Development; **not opened for this manuscript**; G2/G3 do not exist in it |
| `paper/*` (this work) | manuscript scaffold | **before** all prospective outcomes | no | yes | no | writing artifact, not evidence |

## 15. Known gaps in this inventory

Recorded rather than filled with a guess.

1. Calibration, Development, Held-out and Challenge runner **script** entry
   points under `scripts/` were not present at `07c64c8`. The runner API exists
   in `src/muru/paper_benchmark/rc3_calibration_runner.py`.
   `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
2. No `pb_35`-style A3.2 integrity script exists at `07c64c8`; A3.2's own record
   and `tests/test_a3_2_calibration_design.py` cover the contract.
   `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
3. **Not a gap; an upstream error corrected here.** The execution environment
   audit at `c443a7f` states that SymPy is "not pinned anywhere". That is wrong.
   `configs/rc3_requirements_lock_c7c2332.txt` line 44 is `sympy==1.14.0`, and
   that file is byte-identical to `requirements.lock.txt` at RC2 `c7c2332`
   (verified: both hash to `13b21b8c...57fa8`), so SymPy was pinned at RC2 and
   is pinned in the file the RC3 dependency guard actually reads. SymPy is
   absent only from the repository-root `requirements.lock.txt`, which is the
   reduced Phase-1 lock and is explicitly not the RC3 pin source. Since the G2
   support contract depends on SymPy `simplify`, the pin matters; it exists.
   The upstream audit document should be corrected on
   `claude/muru-paper-env-audit-bf067b`, which is out of scope for this writing
   branch.
4. Per-family noise levels, F04 missingness pattern and F05 boundary parameters
   are frozen in the generator and truth payloads but are not yet extracted into
   a manuscript-ready table. `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
5. The mapping from case family (F01 to F18) to truth-family taxonomy member is
   a frozen property of the truth payloads and must be read from
   `artifacts/paper_benchmark_truth_manifest.json` before Table 6 can be
   completed. `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
6. **Resolved by Amendment A3.4.** Parameter recovery is evaluated at anchor
   $\mathbf{x}_0 = (250, 0, 0, 0, 0)$ across 156 cases (mass exponent tolerance
   $\pm 0.15$, descriptor coupling tolerance $\pm 0.10$ on 84 cases); Predictive
   equivalence is evaluated across 2,160 reference points (12 frames $\times$ 180 rows,
   aggregate digest `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`)
   across 144 cases (validity $\ge 0.995$, positive scale $c^* > 0$, relative RMSE
   $\le 0.05$, Pearson $r \ge 0.990$ with zero-variance failure semantics).
