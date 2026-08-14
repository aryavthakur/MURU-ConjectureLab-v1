# A3.4 Temporal Adjudication and RC4 Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze an outcome-blind temporal erratum and implement A3.4's two fixed secondary endpoint scorers without modifying protected science or opening sealed partitions.

**Architecture:** Merge the frozen A3.4 science lineage into the RC3.1 engineering branch, then add independent post-hoc contract, scorer, record, and integrity modules. All APIs consume a final candidate snapshot plus truth only after an authorized scoring stage; none can run search, select candidates, materialize a partition, or access calibration results.

**Tech Stack:** Python 3.13, NumPy, SymPy, pandas, pytest, frozen MURU benchmark modules.

**Spec:** `docs/superpowers/specs/2026-08-14-a3-4-temporal-adjudication-engineering-design.md`

## Global Constraints

- Branch: `eng/muru-rc4-a3-4`, created from RC3.1 `07c64c862cb32a306f5081582dacf73e09211c0a`.
- Merge A3.4 `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` as a real merge commit; never modify its science paths.
- Preserve all A3.1/A3.2/A3.3/A3.4 definitions, generator, manifests, primary denominators, grammar, search settings, calibration procedure, and thresholds.
- The calibration directory, Development, Held-out, and Confirmation must not be opened or scored during implementation.
- Parameter Recovery: anchor `(250, 0, 0, 0, 0)`, denominators `joint/156`, `p_mass/156`, `c_desc/84`, tolerances `0.15` and `0.10`, Wilson 95% intervals, no gate.
- Predictive Equivalence: IDs `PB|PRED_EQUIV|FRAME|000` through `011`, 2,160 rows, reference digest `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`, valid count >= 2150, positive scalar only, `REL_RMSE <= 0.05`, `r >= 0.990`.
- Never reselect a candidate, refit a coefficient, or apply an affine intercept alignment.

---

### Task 1: Merge A3.4 and freeze the additive temporal erratum

**Files:**
- Create: `audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md`
- Create: `audit/muru_a3_4_temporal_provenance_erratum.json`
- Create: `tests/test_a3_4_temporal_provenance_erratum.py`
- Modify: Git history only through `git merge --no-ff be23b80d63fbd30227f0ab8f200dddc2121f3bfe`

**Interfaces:**
- Consumes: frozen RC3.1/A3.4 commits and read-only provenance timestamps.
- Produces: an additive, tagged governance record that neither replaces nor edits A3.4.

- [ ] **Step 1: Write the failing erratum-identity test**

```python
def test_erratum_is_additive_and_leaves_a34_bytes_unchanged():
    assert ERRATUM["classification"] == "TEMPORAL_PROVENANCE_ERRATUM_REQUIRED_OUTCOME_BLIND"
    assert sha256_path("MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md") == A34_SHA
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a3_4_temporal_provenance_erratum.py -q`

Expected: FAIL because the erratum artifacts do not exist.

- [ ] **Step 3: Merge then write the additive erratum and test**

```bash
git merge --no-ff be23b80d63fbd30227f0ab8f200dddc2121f3bfe -m "Merge frozen A3.4 science lineage into RC4"
git tag -a a3-4-temporal-provenance-erratum -m "Freeze outcome-blind A3.4 temporal provenance erratum"
```

The Markdown and JSON must state exact 2026-08-14 EDT event chronology, the
frozen first-durable-seed definition, no outcome inspection, and no scientific
change. The tag is created only after the erratum commit and test are green.

- [ ] **Step 4: Run the test to verify it passes**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a3_4_temporal_provenance_erratum.py -q`

Expected: PASS.

- [ ] **Step 5: Commit and annotate the ledger**

```bash
git add audit tests
git commit -m "audit: freeze A3.4 temporal provenance erratum"
```

### Task 2: Bind the A3.4 reference contract and frame generator

**Files:**
- Create: `src/muru/paper_benchmark/a34_contract.py`
- Create: `tests/test_a34_contract.py`

**Interfaces:**
- Consumes: `_synthetic_compounds(frame_id)` and frozen A3.4 artifact constants.
- Produces: `build_reference_rows() -> tuple[Mapping[str, object], ...]`, `reference_digest() -> str`, `verify_reference_distribution() -> None`, and denominator/threshold constants.

- [ ] **Step 1: Write failing reference-contract tests**

```python
def test_all_twelve_frame_hashes_and_aggregate_digest_match_a34():
    rows, frame_digests = build_reference_rows()
    assert len(rows) == 2160
    assert frame_digests == EXPECTED_FRAME_DIGESTS
    assert reference_digest(rows) == EXPECTED_REFERENCE_DIGEST
```

Also test canonical sort order, 180 rows/30 scaffolds per frame, exact seeds,
and F09's reference rows never hit the descriptor `-1` pole.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_contract.py -q`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the smallest frozen contract adapter**

```python
def canonical_reference_json(rows: Sequence[Mapping[str, object]]) -> bytes:
    ordered = sorted(rows, key=lambda row: (str(row["frame_id"]), str(row["compound_id"])))
    return json.dumps(ordered, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
```

Generate every frame exclusively with the unchanged generator's covariate
primitive, append `frame_id`, check frame/aggregate hashes, and raise a
dedicated error on any mismatch.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_contract.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/muru/paper_benchmark/a34_contract.py tests/test_a34_contract.py
git commit -m "feat: bind A3.4 reference distribution"
```

### Task 3: Implement Parameter Recovery with fixed denominators

**Files:**
- Create: `src/muru/paper_benchmark/a34_parameter_recovery.py`
- Create: `tests/test_a34_parameter_recovery.py`

**Interfaces:**
- Consumes: `expression: str | None`, `TruthRecord`, and A3.4 constants.
- Produces: `ParameterRecoveryResult`, `summarize_parameter_recovery`, and `wilson_interval_95`.

- [ ] **Step 1: Write failing parameter-recovery tests**

```python
def test_exact_interaction_truth_recovers_p_mass_and_c_desc():
    result = score_parameter_recovery(
        "sqrt(mass / 250) * (1 + 0.4 * descriptor * descriptor2)",
        interaction_truth(0.4),
    )
    assert result.joint_success and result.p_mass_success and result.c_desc_success
```

Cover exact affine/F07/F09/F10/F18 truths, expansion, positive rescaling,
both inclusive tolerance boundaries and just-outside failures, parse failure,
non-finite derivative, nonpositive anchor, and c-desc exclusion from `/84`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_parameter_recovery.py -q`

Expected: FAIL because the scorer does not exist.

- [ ] **Step 3: Implement minimal symbolic differentiation**

```python
p_mass = anchor["mass"] / base * float(sympy.diff(expr, mass).subs(anchor))
```

Use `(1/base) * d/d descriptor`, `(1/base) * d2/d descriptor d descriptor2`,
or `(3/base) * d/d descriptor` exactly by frozen truth family. Reject every
parse/evaluation/derivative error and preserve denominators at 156/84.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_parameter_recovery.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/muru/paper_benchmark/a34_parameter_recovery.py tests/test_a34_parameter_recovery.py
git commit -m "feat: implement A3.4 parameter recovery"
```

### Task 4: Implement Predictive Equivalence and candidate binding

**Files:**
- Create: `src/muru/paper_benchmark/a34_predictive_equivalence.py`
- Create: `src/muru/paper_benchmark/a34_record.py`
- Create: `tests/test_a34_predictive_equivalence.py`
- Create: `tests/test_a34_record.py`

**Interfaces:**
- Consumes: final candidate expression, `TruthRecord`, `build_reference_rows()`, and source case-record digest.
- Produces: `PredictiveEquivalenceResult`, canonical endpoint sidecar, and fixed `/144` Wilson summary.

- [ ] **Step 1: Write failing predictive and binding tests**

```python
def test_positive_scalar_truth_passes_without_reselection_or_refit():
    result = score_predictive_equivalence("2 * sqrt(mass / 250) * (1 + 0.4 * descriptor)", truth)
    assert result.success and result.c_star == pytest.approx(0.5)
```

Cover exact truth, positive/negative scalar, constant candidate, wrong shape,
affine-offset failure, no coefficient-refit API, 2150/2149 valid count,
inclusive/exclusive RMSE and r boundaries, zero truth/candidate variance,
F09 no-pole verification, and nonfinite points only through frozen `V`.
The sidecar tests must prove source-record/contract/reference/candidate digest
sensitivity and deterministic output independent of time/path.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_predictive_equivalence.py tests/test_a34_record.py -q`

Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Implement score-only evaluation**

```python
valid = np.isfinite(y_hat) & (y_hat > 0) & np.isfinite(y_true) & (y_true > 0)
c_star = float(np.dot(y_true[valid], y_hat[valid]) / np.dot(y_hat[valid], y_hat[valid]))
```

Require 2,150 valid rows before scaling, use no intercept term, compute RMSE
and Pearson over exactly `valid`, fail zero variance as `r=0.0`, and expose no
candidate-selection/refit function.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_predictive_equivalence.py tests/test_a34_record.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/muru/paper_benchmark/a34_predictive_equivalence.py src/muru/paper_benchmark/a34_record.py tests/test_a34_predictive_equivalence.py tests/test_a34_record.py
git commit -m "feat: implement A3.4 predictive equivalence"
```

### Task 5: Add A3.4 science and sealed-boundary integrity gate

**Files:**
- Create: `scripts/pb_35_a3_4_integrity.py`
- Create: `tests/test_a3_4_integrity.py`

**Interfaces:**
- Consumes: parent RC3 integrity gate and `be23b80` byte identities.
- Produces: a zero-exit verifier or explicit nonzero failure for any frozen-path drift or sealed-boundary import.

- [ ] **Step 1: Write failing integrity tests**

```python
def test_a34_integrity_script_accepts_clean_checkout():
    assert run_integrity().returncode == 0

def test_endpoint_modules_cannot_import_partition_or_candidate_selection():
    assert forbidden_imports(endpoint_sources()) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a3_4_integrity.py -q`

Expected: FAIL because the integrity verifier does not exist.

- [ ] **Step 3: Implement the strict verifier**

```python
subprocess.run([sys.executable, "scripts/pb_34_rc3_integrity.py"], check=True)
for path in A34_PROTECTED_PATHS:
    require_sha256(path, git_show_bytes("be23b80d...", path))
```

Scan only new A3.4 endpoint modules for imports of `generate_partition`,
`iter_case_ids`, `rc3_acceptance`, `rc3_calibration`, and search/selection
modules. Do not weaken RC3's existing verifier.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a3_4_integrity.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/pb_35_a3_4_integrity.py tests/test_a3_4_integrity.py
git commit -m "test: guard A3.4 science and sealed boundaries"
```

### Task 6: Review, verify, and freeze RC4

**Files:**
- Modify: `audit/MURU_RC4_A3_4_ENGINEERING_FREEZE.md`
- Create: `audit/muru_rc4_a3_4_engineering_freeze.json`

**Interfaces:**
- Consumes: clean targeted tests, full-suite result, integrity output, protected digest, reference digest, and the temporal erratum tag.
- Produces: immutable RC4 freeze metadata and annotated `engineering-rc4-a3-4` tag.

- [ ] **Step 1: Run targeted tests and integrity checks**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest tests/test_a34_contract.py tests/test_a34_parameter_recovery.py tests/test_a34_predictive_equivalence.py tests/test_a34_record.py tests/test_a3_4_integrity.py -q`

Run: `PYTHONPATH=src /Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/python scripts/pb_35_a3_4_integrity.py`

Expected: PASS and exit 0.

- [ ] **Step 2: Run the full suite and record its exact result**

Run: `/Users/aryav/Documents/MURU-ConjectureLab-v1/.venv/bin/pytest`

Expected: either PASS, or only the demonstrated pre-existing missing
untracked-artifact failures, explicitly separated from RC4 regressions.

- [ ] **Step 3: Perform the three independent reviews**

Reviewers must cover science-to-code conformance, symbolic/numerical adversary
cases, and contamination/reproducibility. Fix all Critical/Important findings
before freezing.

- [ ] **Step 4: Write freeze metadata and create the annotated tag**

```bash
git add audit
git commit -m "audit: freeze RC4 A3.4 engineering"
git tag -a engineering-rc4-a3-4 -m "Freeze A3.4 engineering RC4"
git status --short
```

The record must include RC3.1 parent, A3.4 merge, engineering commit,
environment, exact tests, protected/reference digests, and provenance
adjudication.
