# MURU Paper Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and content-freeze a self-contained 380-case prospective synthetic benchmark that refuses held-out evaluation until the MURU implementation lock and governance gates are complete.

**Architecture:** A new `muru.paper_benchmark` package owns the registry, fully synthetic generation, artifact hashing, endpoint reconstruction, strict evaluator contract, governance refusal, and development-only preflight. It receives normalized outcomes from a future locked MURU implementation; it does not implement or invoke an unlocked search engine.

**Tech Stack:** Python 3.13, NumPy, pandas, pytest, standard-library JSON, hashlib, resource, and time.

**Spec:** `docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md`

## Global Constraints

- Keep 380 cases: Development 80, Held-out 240, Challenge 60; 20 families; four/twelve/three cases per family.
- Use 180 fully synthetic compounds, 30 scaffold groups, a 20/5/5 group split, the six-energy grid, and root seed `20260813`.
- Derive streams with SHA-256 labels. Do not read real covariates, response data, confirmation identifiers, historical worlds, or prior-suite artifacts.
- Held-out artifacts may be generated and hashed, but development tests, preflight, logs, and reports may not load or enumerate held-out IDs, truths, or outcomes.
- Hold all held-out evaluation behind a complete implementation lock, verified hashes, a complete engine preflight, clean tree, and reconstructed denominators.
- Preserve F19A/F19B as scalar M0 variants and exclude F19C from scalar/M0/symbolic endpoints.
- The positive claim requires G1, G2, and G3. G1/G2 lower Wilson bounds are 0.70; G3 upper Wilson bound is 0.15.
- Never execute a held-out result in this plan.

---

### Task 1: Freeze registry, F19 variants, and endpoint applicability

**Files:**
- Create: `src/muru/paper_benchmark/__init__.py`
- Create: `src/muru/paper_benchmark/registry.py`
- Test: `tests/test_paper_benchmark_registry.py`

**Interfaces:**
- Produces immutable `VariantSpec`, `FamilySpec`, `EndpointSpec`, `CASE_FAMILIES`, `ENDPOINTS`, `ROOT_SEED`, `ENERGY_GRID`, `resolve_case_id(case_id)`, and `endpoint_case_count(name)`.
- Later code derives all case counts and applicability from this registry.

- [ ] **Step 1: Write the failing registry test**

```python
def test_frozen_registry_reconstructs_partitions_and_f19():
    assert sum(f.partition_counts["development"] for f in CASE_FAMILIES) == 80
    assert sum(f.partition_counts["held_out"] for f in CASE_FAMILIES) == 240
    f19 = next(f for f in CASE_FAMILIES if f.code == "F19")
    assert f19.variants["F19A"].scalar_truth_defined
    assert f19.variants["F19C"].m0_adequacy_truth == "not_applicable"
    assert endpoint_case_count("scalar_competence") == 164
```

- [ ] **Step 2: Run it and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_registry.py -q`

Expected: FAIL because `muru.paper_benchmark.registry` does not exist.

- [ ] **Step 3: Implement minimal registry records**

```python
@dataclass(frozen=True)
class VariantSpec:
    code: str
    scalar_truth_defined: bool
    m0_adequacy_truth: str
    symbolic_truth_kind: str
    endpoint_names: frozenset[str]

def endpoint_case_count(name: str) -> int:
    return sum(spec.held_out_cases_for(name) for spec in CASE_FAMILIES)
```

Encode F01–F20 and all F19/F20 variants in one table. Encode the 164/144/36 denominators as effects of applicability, never as duplicated constants.

- [ ] **Step 4: Run it and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_registry.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/__init__.py src/muru/paper_benchmark/registry.py tests/test_paper_benchmark_registry.py && git commit -m "Add frozen paper benchmark registry"`

### Task 2: Generate deterministic fully synthetic cases and truths

**Files:**
- Create: `src/muru/paper_benchmark/generator.py`
- Create: `src/muru/paper_benchmark/truth.py`
- Test: `tests/test_paper_benchmark_generator.py`
- Test: `tests/test_paper_benchmark_truth.py`

**Interfaces:**
- Consumes `resolve_case_id` from the registry.
- Produces `GeneratedCase(case_id, inputs, truth, content_hash)`, `generate_case(case_id)`, and `generate_partition(partition)`.

- [ ] **Step 1: Write failing generator tests**

```python
def test_development_case_is_deterministic_and_has_frozen_shape():
    first = generate_case("PB|development|F01|r000")
    second = generate_case("PB|development|F01|r000")
    assert first.content_hash == second.content_hash
    assert len(first.inputs.compounds) == 180
    assert first.inputs.compounds.scaffold_id.nunique() == 30

def test_f19c_truth_excludes_scalar_and_m0_endpoints():
    truth = generate_case("PB|development|F19|r008").truth
    assert truth.variant == "F19C"
    assert not truth.scalar_truth_defined
    assert truth.m0_adequacy_truth == "not_applicable"
```

- [ ] **Step 2: Run them and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_generator.py tests/test_paper_benchmark_truth.py -q`

Expected: FAIL because generator and truth modules do not exist.

- [ ] **Step 3: Implement generator and truth schema**

```python
def derive_seed(*parts: str) -> int:
    payload = "paper-benchmark-v1|" + "|".join(parts)
    digest = hashlib.sha256(payload.encode()).digest()
    return int.from_bytes(digest[:8], "big")

def generate_case(case_id: str) -> GeneratedCase:
    spec, variant, replicate = resolve_case_id(case_id)
    compounds = _make_synthetic_compounds(spec, variant, replicate)
    inputs, truth = _make_synthetic_response(spec, variant, compounds, replicate)
    return GeneratedCase(case_id, inputs, truth, canonical_hash(inputs, truth))
```

Assign 30 correlated synthetic scaffold groups before response generation. Implement M0 and declared M1/M2/M3 truth mechanisms. Store `Phi`, `g`, active variables, family, coefficients, exponents, noise, missingness, and per-variant applicability. Do not import `muru.synth`, `muru.discovery`, or a real-data loader.

- [ ] **Step 4: Run them and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_generator.py tests/test_paper_benchmark_truth.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/generator.py src/muru/paper_benchmark/truth.py tests/test_paper_benchmark_generator.py tests/test_paper_benchmark_truth.py && git commit -m "Generate deterministic paper benchmark cases"`

### Task 3: Create sealed artifacts and reconstructable hashes

**Files:**
- Create: `src/muru/paper_benchmark/artifacts.py`
- Create: `scripts/pb_00_build.py`
- Test: `tests/test_paper_benchmark_artifacts.py`

**Interfaces:**
- Produces `BuildReceipt`, `build_partition(partition, output_dir)`, `build_all(output_dir)`, and `verify_hash_inventory(output_dir)`.
- Writes required manifests and partition input/truth JSONL atomically.

- [ ] **Step 1: Write the failing artifact test**

```python
def test_development_artifacts_hash_reconstruct():
    receipt = build_partition("development", tmp_path)
    assert receipt.case_count == 80
    assert verify_hash_inventory(tmp_path) == receipt.hashes

def test_development_build_does_not_request_held_out_cases(monkeypatch):
    monkeypatch.setattr("muru.paper_benchmark.artifacts.generate_partition", _development_only)
    build_partition("development", tmp_path)
```

- [ ] **Step 2: Run it and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_artifacts.py -q`

Expected: FAIL because `artifacts.py` does not exist.

- [ ] **Step 3: Implement atomic writers and SHA-256 inventory**

```python
def build_partition(partition: str, output_dir: Path) -> BuildReceipt:
    writer = _PartitionWriter(output_dir, partition)
    for generated in generate_partition(partition):
        writer.write_generated_case(generated)
    return writer.finish()
```

For held-out content, write directly from generator to sealed files, retain only aggregate count and hashes in normal command output, and never deserialize the sealed content in a development code path.

- [ ] **Step 4: Run it and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_artifacts.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/artifacts.py scripts/pb_00_build.py tests/test_paper_benchmark_artifacts.py && git commit -m "Write sealed paper benchmark artifacts"`

### Task 4: Enforce strict candidate semantics and held-out refusal

**Files:**
- Create: `src/muru/paper_benchmark/contract.py`
- Create: `src/muru/paper_benchmark/governance.py`
- Test: `tests/test_paper_benchmark_contract.py`
- Test: `tests/test_paper_benchmark_governance.py`

**Interfaces:**
- Produces `StrictCandidate`, `validate_candidate`, `ImplementationLock`, `HeldOutAccessRefused`, and `assert_held_out_execution_allowed`.

- [ ] **Step 1: Write failing semantic and refusal tests**

```python
def test_complex_or_nonfinite_candidate_is_rejected():
    with pytest.raises(ValueError, match="finite real"):
        validate_candidate(StrictCandidate("sqrt(-1)", [1 + 0j]))

def test_pending_lock_refuses_held_out_execution():
    with pytest.raises(HeldOutAccessRefused, match="PENDING_LOCK"):
        assert_held_out_execution_allowed(ImplementationLock.pending(), {}, {}, True)
```

- [ ] **Step 2: Run them and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_contract.py tests/test_paper_benchmark_governance.py -q`

Expected: FAIL because contract and governance modules do not exist.

- [ ] **Step 3: Implement the strict contract and guard**

```python
def validate_candidate(candidate: StrictCandidate) -> None:
    values = np.asarray(candidate.predictions)
    if np.iscomplexobj(values) or not np.isfinite(values).all():
        raise ValueError("candidate must evaluate to finite real values")

def assert_held_out_execution_allowed(lock, hashes, preflight, tree_clean):
    if lock.status == "PENDING_LOCK":
        raise HeldOutAccessRefused("implementation lock is PENDING_LOCK")
```

Reject complex casts, non-finite predictions, incomplete grammar/version metadata, failed hashes, incomplete preflight, and dirty trees. Define the interface only; do not add a substitute search engine.

- [ ] **Step 4: Run them and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_contract.py tests/test_paper_benchmark_governance.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/contract.py src/muru/paper_benchmark/governance.py tests/test_paper_benchmark_contract.py tests/test_paper_benchmark_governance.py && git commit -m "Guard paper benchmark held-out execution"`

### Task 5: Reconstruct endpoint denominators and score G1/G2/G3

**Files:**
- Create: `src/muru/paper_benchmark/analysis.py`
- Test: `tests/test_paper_benchmark_denominators.py`
- Test: `tests/test_paper_benchmark_decision.py`

**Interfaces:**
- Consumes registry and normalized `CaseOutcome` records.
- Produces `endpoint_denominator`, `endpoint_applies`, `classify_negative_control`, `wilson_interval`, `scalar_case_competent`, and `umbrella_decision`.

- [ ] **Step 1: Write failing F19, negative-control, and umbrella tests**

```python
def test_variant_applicability_reconstructs_primary_denominators():
    assert endpoint_denominator("scalar_competence") == 164
    assert endpoint_denominator("family_recovery") == 144
    assert endpoint_denominator("principal_structural_safety") == 36
    assert not endpoint_applies("m0_specificity", "PB|held_out|F19|r008")

def test_each_negative_control_uses_its_own_error_rule():
    assert classify_negative_control(_f07_nonmass_acceptance()) == "false_extra_structure"
    assert classify_negative_control(_f19c_unflagged()) == "false_null_structure"
    assert classify_negative_control(_f20_accepted_trap()) == "false_adversarial_structure"

def test_umbrella_claim_fails_if_scalar_gate_fails():
    assert not umbrella_decision(_outcomes(g1=False, g2=True, g3=True)).positive_claim
```

- [ ] **Step 2: Run them and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_denominators.py tests/test_paper_benchmark_decision.py -q`

Expected: FAIL because `analysis.py` does not exist.

- [ ] **Step 3: Implement denominator and decision analysis**

```python
def scalar_case_competent(outcome: CaseOutcome) -> bool:
    return (outcome.g_spearman >= 0.80 and
            outcome.trajectory_mae <= 0.80 * outcome.per_energy_mean_mae and
            outcome.m0_accepted)

def umbrella_decision(outcomes: Sequence[CaseOutcome]) -> DecisionReport:
    g1 = _lower_wilson_at_least(_scalar_successes(outcomes), 164, 0.70)
    g2 = _lower_wilson_at_least(_family_successes(outcomes), 144, 0.70)
    g3 = _upper_wilson_at_most(_safety_errors(outcomes), 36, 0.15)
    return DecisionReport(positive_claim=g1 and g2 and g3, gates={"G1": g1, "G2": g2, "G3": g3})
```

Keep separate F07, F19, and F20 numerator/denominator/interval records even when calculating the equal-weighted 36-case principal safety rate.

- [ ] **Step 4: Run them and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_denominators.py tests/test_paper_benchmark_decision.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/analysis.py tests/test_paper_benchmark_denominators.py tests/test_paper_benchmark_decision.py && git commit -m "Score paper benchmark decision gates"`

### Task 6: Define fold-local scalar integration and development-only preflight

**Files:**
- Create: `src/muru/paper_benchmark/protocol.py`
- Create: `src/muru/paper_benchmark/preflight.py`
- Create: `src/muru/paper_benchmark/freeze.py`
- Create: `scripts/pb_10_preflight.py`
- Create: `scripts/pb_20_prepare_freeze.py`
- Test: `tests/test_paper_benchmark_protocol.py`
- Test: `tests/test_paper_benchmark_preflight.py`
- Test: `tests/test_paper_benchmark_freeze.py`

**Interfaces:**
- Produces `ScalarEstimatorProtocol.fit_training_scalar`, `estimate_one`, `PreflightReport`, `run_preflight`, and `prepare_content_freeze`.

- [ ] **Step 1: Write failing leakage and preflight tests**

```python
def test_test_compound_b_cannot_change_a_estimate():
    frozen = fit_training_scalar(_training_rows())
    before = estimate_one(frozen, _test_rows("A"))
    _mutate(_test_rows("B"))
    assert estimate_one(frozen, _test_rows("A")) == before

def test_preflight_is_development_only_and_pending_without_lock(tmp_path):
    report = run_preflight(_development_inputs(tmp_path), ImplementationLock.pending())
    assert (report.partition, report.case_count, report.engine_status) == ("development", 80, "not_run_pending_lock")
```

- [ ] **Step 2: Run them and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_protocol.py tests/test_paper_benchmark_preflight.py tests/test_paper_benchmark_freeze.py -q`

Expected: FAIL because protocol, preflight, and freeze modules do not exist.

- [ ] **Step 3: Implement protocol, preflight, and freeze preparation**

```python
class ScalarEstimatorProtocol(Protocol):
    def fit_training_scalar(self, training_rows: pd.DataFrame) -> FrozenScalarObjects: ...
    def estimate_one(self, frozen: FrozenScalarObjects, compound_rows: pd.DataFrame) -> ScalarEstimate: ...

def run_preflight(development_inputs: Path, lock: ImplementationLock) -> PreflightReport:
    _assert_development_path(development_inputs)
    return _measure_generator_contract_serialization(development_inputs, lock)
```

The protocol exposes no all-compounds fitting method. The preflight records wall time, CPU time, resident memory, artifact bytes, candidate/engine status, and failures. It reports engine burden as unavailable, rather than borrowing historical results, while the implementation lock is pending. Freeze preparation can verify content hashes but reports `WAITING_FOR_LOCKED_IMPLEMENTATION` until the complete engine preflight is available.

- [ ] **Step 4: Run them and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_protocol.py tests/test_paper_benchmark_preflight.py tests/test_paper_benchmark_freeze.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/muru/paper_benchmark/protocol.py src/muru/paper_benchmark/preflight.py src/muru/paper_benchmark/freeze.py scripts/pb_10_preflight.py scripts/pb_20_prepare_freeze.py tests/test_paper_benchmark_protocol.py tests/test_paper_benchmark_preflight.py tests/test_paper_benchmark_freeze.py && git commit -m "Prepare development-only benchmark preflight"`

### Task 7: Publish required benchmark documents and test documentation consistency

**Files:**
- Create: `MURU_PAPER_BENCHMARK_PROTOCOL.md`
- Create: `MURU_PAPER_BENCHMARK_CASE_FAMILIES.md`
- Create: `MURU_PAPER_BENCHMARK_METRICS.md`
- Create: `MURU_PAPER_BENCHMARK_FREEZE.md`
- Test: `tests/test_paper_benchmark_docs.py`

**Interfaces:**
- Documents use the registry and analysis names exactly.
- The freeze document contains no held-out case ID or truth values.

- [ ] **Step 1: Write failing document consistency test**

```python
def test_metrics_document_states_frozen_thresholds_and_denominators():
    text = Path("MURU_PAPER_BENCHMARK_METRICS.md").read_text()
    assert "164" in text and "144" in text and "36" in text
    assert "lower 95% Wilson bound >= 0.70" in text
    assert "upper 95% Wilson bound <= 0.15" in text
```

- [ ] **Step 2: Run it and verify RED**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_docs.py -q`

Expected: FAIL because required documents do not exist.

- [ ] **Step 3: Write protocol documents**

Document the exact F19 table, separate F07/F19/F20 error definitions, G1/G2/G3, all endpoint denominators, strict-evaluator contract, development-only preflight, PENDING_LOCK refusal, and historical boundaries. State that the preparation is not a held-out result and does not authorize Phase 4.

- [ ] **Step 4: Run it and verify GREEN**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_docs.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add MURU_PAPER_BENCHMARK_PROTOCOL.md MURU_PAPER_BENCHMARK_CASE_FAMILIES.md MURU_PAPER_BENCHMARK_METRICS.md MURU_PAPER_BENCHMARK_FREEZE.md tests/test_paper_benchmark_docs.py && git commit -m "Document paper benchmark protocol"`

### Task 8: Build content, preflight Development only, and prepare content freeze

**Files:**
- Create: `artifacts/paper_benchmark_partition_manifest.json`
- Create: `artifacts/paper_benchmark_case_manifest.json`
- Create: `artifacts/paper_benchmark_truth_manifest.json`
- Create: `artifacts/paper_benchmark_hash_inventory.json`
- Create: `artifacts/paper_benchmark_content_freeze.json`
- Create: `artifacts/paper_benchmark_preflight.json`

**Interfaces:**
- Uses only the new scripts. It emits held-out aggregate counts and hashes, never held-out identities, truths, candidates, or outcomes.

- [ ] **Step 1: Run benchmark-specific tests**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_*.py -q`

Expected: PASS without skips, failures, or errors.

- [ ] **Step 2: Generate frozen content without evaluating held-out outcomes**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python scripts/pb_00_build.py --output artifacts --quiet-held-out`

Expected: writes all required artifacts, reports only partition counts and hashes, and makes no evaluator call.

- [ ] **Step 3: Run the Development-only preflight**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python scripts/pb_10_preflight.py --artifacts artifacts --output artifacts/paper_benchmark_preflight.json`

Expected: records only Development wall/CPU/memory/artifact measurements and `not_run_pending_lock`.

- [ ] **Step 4: Prepare freeze status**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python scripts/pb_20_prepare_freeze.py --artifacts artifacts --output artifacts/paper_benchmark_content_freeze.json`

Expected: verifies hashes and records `WAITING_FOR_LOCKED_IMPLEMENTATION`; it refuses final executable-freeze status.

- [ ] **Step 5: Run required correction tests and full suite**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest tests/test_paper_benchmark_denominators.py tests/test_paper_benchmark_registry.py tests/test_paper_benchmark_decision.py tests/test_paper_benchmark_governance.py tests/test_paper_benchmark_preflight.py -q && /Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python -m pytest -q`

Expected: all paper-benchmark tests pass. The historical `ov_*` tests may retain their known failure/error state caused only by absent gitignored real-data parquet files; record them separately without changing their code.

- [ ] **Step 6: Verify inventory and commit**

Run: `git diff --check && git add artifacts/paper_benchmark_partition_manifest.json artifacts/paper_benchmark_case_manifest.json artifacts/paper_benchmark_truth_manifest.json artifacts/paper_benchmark_hash_inventory.json artifacts/paper_benchmark_content_freeze.json artifacts/paper_benchmark_preflight.json docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md docs/superpowers/plans/2026-08-13-muru-paper-benchmark.md && git commit -m "Prepare prospective paper benchmark content freeze"`

## Plan self-review

- Task 1 fixes F19 variant applicability and derives denominators. Task 5 separates the three safety error types and encodes G1/G2/G3. Tasks 2–3 create fully synthetic data, truth, manifests, and hashes. Tasks 4 and 6 enforce strict evaluation, fold-local integration, no held-out execution, and development-only preflight. Tasks 7–8 create all required documents and content-freeze preparation artifacts.
- The plan has no deferred engineering item. `PENDING_LOCK` is an explicit, tested governance state until a future locked implementation arrives.
- All later interfaces originate in a prior task: registry before generator and analysis; generator before artifacts; governance before preflight; analysis before documents and freeze preparation.
