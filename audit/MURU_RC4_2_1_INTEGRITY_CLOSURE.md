# MURU RC4.2.1 — Engineering Integrity + Development-Boundary Closure

**Classification:** `ENGINEERING_INTEGRITY_CLOSURE`
**Branch:** `eng/muru-rc4-2-1-integrity-closure`
**Tag:** `engineering-rc4-2-1-integrity-closure`
**Parent:** `engineering-rc4-2-core-defect-repair` (`e8f0f4e9e80befc5a3180abd7c3996d443119a32`) — **not moved**
**Status:** `FROZEN_CLEAN`

RC4.2's R1-R4 repairs are not reopened here, scientifically or otherwise. This
closure is engineering and governance bookkeeping only: it teaches the
project's existing integrity tooling to correctly recognize RC4.2's already-
authorized delta, reconciles the executable environment, forensically audits
one test file's Development-partition access, and disposes of one defense-
in-depth gap. No science surface (`src/muru/paper_benchmark/*.py` semantics,
`tests/test_a3_*`/`tests/test_paper_benchmark*` assertions beyond bookkeeping,
any `artifacts/*.json` content, calibration) was touched.

---

## Issue 1 — RC4.2 was tagged FROZEN_CLEAN while its own integrity suite was red

### Diagnosis

At the RC4.2 tag, seven tests failed for the reason RC4.2's own report
predicted (protected-path byte-identity reacting to R1-R4's six intentionally
repaired files) — and an independent re-audit here found **one more the
original report missed**: `tests/test_a3_4_frozen_metadata_attestation_advisory.py`,
an additive hostile-review artifact that independently re-implements the same
byte-identity check pb_35 performs, and was not part of the report's "7".

| # | Test | Underlying script |
|---|---|---|
| 1 | `test_a3_4_integrity.py::test_a34_integrity_script_accepts_clean_checkout` | `pb_35_a3_4_integrity.py` |
| 2 | `test_eng_environment_closure.py::test_the_closure_verifier_passes_in_this_environment` | `pb_37_environment_closure.py` |
| 3-4 | `test_paper_benchmark_amendment_a2_1_integrity.py` (2 tests) | `pb_32_amendment_a2_1_integrity.py` |
| 5-7 | `test_paper_benchmark_amendment_integrity.py` (3 tests) | `pb_30_amendment_a1_integrity.py` |
| **8 (found here, not in RC4.2's report)** | `test_a3_4_frozen_metadata_attestation_advisory.py::test_advisory_attests_blob_identity_and_serialization_convention_without_rehashing` | independent hostile re-check, no script |

Two further integrity **scripts** that have no pytest wrapper at all (so
`pytest` alone never exercised them) were also found red when run directly,
during this closure's own "run every verifier" pass:

| Script | Symptom |
|---|---|
| `pb_31_amendment_a2_integrity.py` | `unexpected change: protocol.py, test_paper_benchmark_protocol.py` |
| `pb_33_amendment_a3_1_integrity.py` | `MODIFIED: protocol.py` |
| `pb_34_rc3_integrity.py` | delegates to pb_33 (fails transitively) and independently flags 5 files itself, plus its own `A3.2 governance artifacts` re-check |

All ten symptoms have the same single root cause: every one of these checks
was written before RC4.2 existed, and correctly detects that RC4.2's six
repaired files differ from their frozen historical bytes. **That detection is
correct behavior, not a bug** — none of it was disabled, weakened, or
silenced. What was missing was a way for current-lineage verification to
distinguish *"an unlisted, unauthorized change"* from *"the one specific,
adjudicated, byte-pinned repair this project already froze."*

### Repair: a closed, hash-pinned authorized-delta ledger

New file: `scripts/pb_rc4_2_authorized_delta.py`. It is a **closed tuple** of
exactly eight `(path, defect_id, old_sha256, new_sha256, semantic_scope)`
entries — six protected-path modifications plus two purely additive new test
files — transcribed from `audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md` /
`audit/muru_rc4_2_core_defect_repair.json` (independently re-verified against
`git show a605120:<path> | sha256` and the current tree, not trusted from the
prior document):

| Path | Defect | Old SHA-256 (prefix) | New SHA-256 (prefix) |
|---|---|---|---|
| `src/muru/paper_benchmark/protocol.py` | R1/DEFECT_A | `63c77d57...` | `cb35289f...` |
| `src/muru/paper_benchmark/g3_contract.py` | R2/DEFECT_B3 | `c09d849c...` | `dcf5382e...` |
| `src/muru/paper_benchmark/g2_contract.py` | R3/DEFECT_C + R4/DEFECT_D | `502b1a65...` | `29af866c...` |
| `tests/test_paper_benchmark_protocol.py` | R1 tests | `4ee7ccbd...` | `0919378a...` |
| `tests/test_a3_1_g3_contract.py` | R2 tests | `bcbc51af...` | `7fe99f80...` |
| `tests/test_a3_1_g2_contract.py` | R3 tests | `a74c6fa0...` | `16c90fb4...` |
| `tests/test_g3_f07_dispatcher_equivalence.py` (new) | R2 tests | — | `6e6b05d5...` |
| `tests/test_r4_g2_truth_support.py` (new) | R4 tests | — | `e2259507...` |

The classifier (`classify_path`, `check_byte_identity_lineage_aware`,
`split_unexpected_changed`, `classify_blob_sha1`) accepts a path's drift
**only** when both the observed old bytes and the observed new bytes match
the ledger entry exactly. Any other pattern — an unledgered path, a ledgered
path whose old bytes don't match (wrong historical baseline), or a ledgered
path whose new bytes don't match (further, unauthorized drift beyond the
repair) — is still rejected identically to before this closure. No historical
digest (`RECORDED_PROTECTED_AGGREGATE`, any `protected_sha256` value, any
`content_hash`) was edited anywhere; the ledger is consulted as an
independent, additive second question ("is this specific divergence from
history the one authorized one?"), never by relaxing what the first question
("is this byte-identical to history?") means.

**Bootstrapping note, disclosed transparently:** teaching `pb_33` (A3.1's own
integrity script) to import this ledger necessarily changes `pb_33`'s own
bytes — and `pb_33` is itself one of A3.1's 11 protected-forever paths,
checked by `pb_34` and by `pb_35` (A3.4 inherits A3.1's protected set). This
closure's own tooling change to `pb_33` is therefore *also* ledgered, in a
second, clearly-separated tuple (`RC4_2_1_TOOLING_DELTA`) with its own old/new
SHA-256 pair, labeled distinctly from the R1-R4 science-defect-repair ledger
and scoped only to `scripts/` (never `src/muru/paper_benchmark/` or
`tests/test_a3_*`/`tests/test_paper_benchmark*`, so it can never be misread as
a science change). This is the same bootstrapping pattern the R1-R4 repair
itself hit and disclosed (the sealed-boundary import correction recorded in
`MURU_RC4_2_CORE_DEFECT_REPAIR.md`).

Seven scripts were wired to consult the ledger: `pb_30`, `pb_31`, `pb_32`,
`pb_33`, `pb_34`, `pb_35`, `pb_37`. Each wiring is additive — the existing
comparison function's signature grew a second return value
(`rc4_2_authorized_delta`) reported alongside `errors`, never replacing the
error computation. Every one of the ten originally-red symptoms above now
passes; three tracked artifacts that these scripts self-write
(`artifacts/paper_benchmark_amendment_a1.json`, `_a2.json`, `_a2_1.json`,
`configs/rc4_1_environment_manifest.json`) were regenerated by re-running
their owning scripts, not hand-edited.

**What was explicitly NOT done:** no test was skipped or xfailed; no
assertion was weakened to `True`; no protected-path enforcement was loosened
for any file outside the eight-plus-one ledger entries; the historical A2.1
and A3.4 freeze records (`RECORDED_PROTECTED_AGGREGATE`, the A3.4 artifact's
`protected_sha256`, A2.1's `03cc4d3`-relative comparison) were read, never
rewritten, and still correctly state that the historical blobs were
byte-identical *at those freezes* — a claim this closure never touches.

---

## Issue 2 — canonical environment reconciliation

A fresh, disposable venv was built strictly from `requirements.lock.txt` (the
RC4.1-frozen 50-pin lock, byte-identical to the enforced pin source
`configs/rc3_requirements_lock_c7c2332.txt`):

```
python3 -m venv /tmp/muru_rc421_env
/tmp/muru_rc421_env/bin/pip install -r requirements.lock.txt
```

Verified, independently, in that environment:

| Check | Result |
|---|---|
| `pip install -r requirements.lock.txt` | exit 0, all 50 distributions resolved from cache/PyPI, no build failures |
| `pip check` | exit 0, "No broken requirements found" |
| `pip freeze` vs. `requirements.lock.txt` | exact match, all 50 pins (case-insensitive names), only `pip`/`setuptools`/`wheel` bootstrap extras present beyond the lock |
| `import pysr; from pysr.julia_import import jl` | succeeds; juliapkg auto-installed Julia and resolved SymbolicRegression.jl from `pysr`'s own compatibility range |
| Live Julia identity | `julia` = **1.12.6**, `SymbolicRegression.jl` = **1.11.3** — both **exactly** the frozen identity `pb_37_environment_closure.py` pins (`FROZEN_JULIA_VERSION`, `FROZEN_SYMBOLICREGRESSION_JL_VERSION`) |
| `import sklearn` | succeeds (`scikit-learn==1.9.0`, as pinned) |
| `import rdkit` | succeeds (`rdkit==2026.3.5`, as pinned) |

**Conclusion: sklearn/rdkit failures were execution-environment mismatch, not
a repository defect.** They import cleanly and at the exact pinned versions
in an environment built strictly from the tracked lock. RC4.2's provenance
wording describing them as a "pre-existing environment gap" is corrected here
to state the stronger, now-verified fact: the gap is closed by installing
from the tracked lock; nothing about the repository itself needs to change.

### Full suite in the fresh environment

`/tmp/muru_rc421_env/bin/python -m pytest -q` (1210 tests collected):
**17 failed/errored, all seventeen tracing to one single cause** —
`FileNotFoundError: ... artifacts/p2_compounds.parquet` — confirmed by
grepping the traceback of every one of the 17 (`test_ov_blinding.py` ×2,
`test_ov_pipeline.py` ×15). Every other collected test passes.

### `p2_compounds.parquet` — historical-only, kept separately classified

- `*.parquet` is gitignored (`.gitignore:59`); this file has **never** been
  tracked in this repository's git history (`git log --all -- artifacts/p2_compounds.parquet` → empty).
- It is written by `scripts/t2_02_splits.py` (line 185), a stage of the
  wet-lab-track Phase 2 local build pipeline (`t1_*`/`t2_*`), unrelated to the
  RC4.x paper-benchmark lineage this closure covers.
- The tests that need it (`test_ov_blinding.py`, `test_ov_pipeline.py`) are
  Phase 3 objective-validation "G1a/b/c real-chemistry blinding" tests —
  historical, not part of RC4.2's R1-R4 or of any RC4.x integrity gate.
- **This is a local-artifact regeneration gap, not a Python/Julia environment
  defect and not a repository defect.** It is kept separately classified per
  this mission's explicit instruction and is out of scope for RC4.2.1's
  environment closure.

---

## Issue 3 — Development partition materialization by R4's tests

### Exactly what was read

`git grep -n "generate_case" tests/` across every RC4.2-touched/added test
file shows exactly one file calls it: `tests/test_r4_g2_truth_support.py`.
The other four (`test_paper_benchmark_protocol.py`, `test_a3_1_g3_contract.py`,
`test_a3_1_g2_contract.py`, `test_g3_f07_dispatcher_equivalence.py`) contain
no `case_id`, `registry`, `generate_case`, or `partition` reference anywhere,
confirmed by direct grep, not by trusting their docstrings.

Within `test_r4_g2_truth_support.py`, `generate_case(case_id)` is called only
with `case_id` of the form `PB|development|{family}|r{replicate:03d}` —
**56 distinct development-partition case IDs** total:

- The 12 G2-applicable families (`F01,F02,F03,F04,F05,F08,F09,F10,F11,F12,F17,F18`)
  × all 4 development replicates each (`family.partition_counts["development"] == 4`
  for each, independently confirmed by reading `registry.py`'s `CASE_FAMILIES`) = 48.
- The 8 G2-inapplicable families (`F06,F07,F13,F14,F15,F16,F19,F20`) × replicate 0
  only = 8.
- Total: 56 of the partition's 80 cases (20 families × 4 development
  replicates each).

`generate_case` (`generator.py:228`) is a **pure, deterministic, in-process
function of `case_id` alone**: seeds derive from `_rng(case_id, stage)` /
`derive_seed`, synthetic covariates come from `_synthetic_compounds` (pure
`numpy.random.Generator` synthesis — no file read, no `p2_compounds.parquet`,
no real chemistry), and the response trajectory is computed from the frozen
generative law. There is no disk I/O, no read of any historical execution
artifact (`inputs/development.jsonl`, `truth/development.jsonl`, or the
committed `d9e2795`/`bc741e3` historical row files were never opened), and no
network or database access.

Of every `GeneratedCase` produced, the test file reads **only** `.truth`
(`active_variables`, `mathematical_family`, `symbolic_truth_kind`, and the
echo fields `case_id`/`family`/`variant`) — never `.inputs` (the synthetic
covariates and generated `mu` trajectories), and never any numeric truth
parameter (`coefficients`, `exponents`, `phi`, `g_definition`, `g_by_compound`,
`noise`, `missingness`). The strongest cross-check
(`test_truth_support_matches_the_planted_family_definition`) compares against
an expected-support table that was **hand-derived by reading `generator.py`'s
`_law` dispatch source directly**, not by inspecting generated output — so
even that comparison introduces no information the frozen, already-public
source code didn't already carry.

This exact access pattern — `generate_case("PB|development|...").truth`,
reading only truth-generation structural metadata — is **pre-existing frozen
precedent**: `tests/test_paper_benchmark_truth.py` has done the identical
thing since commit `89a2d4e` ("Generate deterministic paper benchmark
cases"), long before RC4.2. R4 introduces no new *kind* of Development access,
only a larger count (56 vs. 2) of an already-accepted pattern.

No `held_out`/`challenge` partition case was ever generated anywhere in these
five files (confirmed: zero occurrences of `generate_case` with those
partition labels). The one place `"held_out"`/`"challenge"` literals appear
in `test_r4_g2_truth_support.py` is inside a hand-built `TruthRecord`'s
cosmetic `partition=` field, in a test that explicitly proves the label alone
(not real Held-out/Challenge data) doesn't change `truth_support_for_case`'s
output — the test's own docstring says so, and this was independently
verified from the code, not merely re-quoted.

### Classification

**`DEVELOPMENT_ENGINEERING_FIXTURE_MATERIALIZATION_ONLY`.**

Not `DEVELOPMENT_SCIENTIFIC_INPUT_EXPOSURE`: no numeric input observation
(mass, descriptor, generated `mu`) was ever read, printed, or asserted upon;
only structural truth-generation metadata was read, and that metadata is
itself already public in the frozen, committed `generator.py` source — R4's
tests reveal nothing a reader of that file couldn't already derive by
inspection. Not `CURRENT_DEVELOPMENT_EXECUTION_OPENED`: no search, discovery,
PySR/gplearn run, acceptance predicate, or scoring/outcome computation ever
touched Development here; RC5 Gate 1 (no executable case path) remains
exactly as recorded, unaffected by this test suite.

### Disposition: not replaced with hand-built-only fixtures

The mission's conditional ("replace ... if the real Development partition is
not necessary") does not apply here: the `generate_case`-based tests are the
*only* thing in this file that independently cross-checks
`truth_support_for_case` against the actual frozen generator's dispatch
behavior, rather than merely restating the function's own logic back at
itself. The file already follows the correct hybrid design — six purely
hand-built unit tests for the block-label mapping logic in isolation
(`test_mass_and_descriptor_map_identically` and five siblings, no
`generate_case` anywhere), *plus* the `generate_case`-based tests for
integration-level agreement with the real generator. Replacing the latter
with additional hand-built fixtures would make those specific tests
tautological (asserting the function agrees with a value the test itself
declared) and would be a **reduction** in verification rigor, not an
improvement, while buying no governance benefit — the partition accessed is
fully synthetic, code-regenerable, and non-secret in a way Held-out and
Confirmation are not. No code change was made here. Replacement would not
and does not "erase" the 56-case access recorded above; that materialization
happened at the RC4.2 freeze and is recorded as fact regardless.

### Governance wording going forward — four states, not two

| State | Status |
|---|---|
| `HISTORICAL_DEVELOPMENT_EXECUTED_UNDER_SUPERSEDED_A2_1_RC2_CONTRACT` | True, unaffected: `d9e2795`/`bc741e3`, 2026-08-13, 80/80 cases, scalar-adequacy stage only, 0 search seeds executed. |
| **`CURRENT_CONTRACT_DEVELOPMENT_CASES_PARTIALLY_MATERIALIZED_FOR_ENGINEERING_TESTS`** (new, precise, RC4.2-specific) | True: 56/80 development cases freshly regenerated (not read from any historical file) as `test_r4_g2_truth_support.py` engineering fixtures; classified `DEVELOPMENT_ENGINEERING_FIXTURE_MATERIALIZATION_ONLY` above. |
| `CURRENT_CONTRACT_SYMBOLIC_DEVELOPMENT_EXECUTION_NOT_RUN` | True, unaffected: no search/discovery has ever executed against Development under the current (RC4.x) contract; RC5 Gate 1 stop stands. |
| `HELD_OUT_AND_CONFIRMATION_SEALED_NOT_OPENED` | True, unaffected: never touched by RC4.2 or this closure. |

---

## Issue 4 — unknown-function fail-closed gap

RC4.2 recorded (as an out-of-scope, non-repaired finding): `weird_op(mass)`
still parses to support `{mass}` in `g2_contract.py::_resolved_support`,
rather than failing closed, because sympy's `free_symbols` on an unbound
`Function` application inspects only its argument symbols, never the
function name itself.

### Reachability under the frozen grammar: verified unreachable

- `src/muru/paper_benchmark/calibration_contract.py::SEARCH_SETTINGS` pins
  `"unary_operators": ["sqrt", "log", "square", "cube", "inv"]` and
  `"binary_operators": ["+", "-", "*", "/"]` — a closed, five-name unary set.
- `rc3_calibration_runner.py::PySRBackend._make_regressor` passes exactly
  `unary_operators=list(SEARCH_SETTINGS["unary_operators"])` to
  `PySRRegressor`, with a runtime guard (`overlap = excluded.intersection(unary)`)
  that refuses to even construct the regressor if the frozen exclusion list
  (`exp`, `sin`, `cos`, `tan`) and the operator list ever overlapped. No
  `extra_sympy_mappings` or custom-operator injection is configured anywhere.
- PySR/SymbolicRegression.jl's expression trees are built exclusively by
  composing the operators passed at construction — the search space contains
  no notion of an operator string outside that fixed array. It is
  mechanically impossible for a PySR search under this configuration to ever
  emit a node labeled `weird_op` (or any name outside the five unary + four
  binary primitives).
- `g2_contract.py::_safe_parse`'s locals bind exactly `square`/`cube`/`inv`
  (plus sympy's own `sqrt`/`log` builtins) and the `GRAMMAR_PRIMITIVES`
  symbols/`x{i}` aliases — the identical closed set.
- **Additional finding:** `extract_effective_support`/`classify_support` (the
  functions the gap lives in) have **no caller anywhere in `src/`** outside
  their own definition module — confirmed by `grep -rn "extract_effective_support\|classify_support\b" src/ scripts/`.
  The module's own docstring already states this ("does not integrate into
  the production execution path; Engineering RC3 does that"), and this was
  independently re-verified, not merely re-quoted. So today, `weird_op(mass)`
  can only ever reach this function via a direct manual/test call — never via
  real PySR output flowing through a live execution path, because no such
  path exists yet.

### Classification

**`NONBLOCKING_DEFENSE_IN_DEPTH_GAP`.** Unreachable under the frozen grammar
(the operator whitelist is closed and mechanically enforced by construction,
with no injection point in this codebase), and additionally unreachable in
practice today because the scoring function it lives in has no live caller.
No repair was made, per the mission's own instruction for the unreachable
case, and no symbolic-equivalence science was expanded. **Recorded for the
future:** if `g2_contract.py`'s support extraction is ever wired into a live
prospective execution path (RC5+), this specific gap (the function-name half
of `free_symbols`) should be revisited before that wiring is trusted, since
the reachability argument here rests specifically on "PySR is the only thing
that can produce these strings, and it currently has the closed operator
set" — a fact about today's configuration, not an invariant of the parser
itself.

---

## Verification

| Suite | Environment | Result |
|---|---|---|
| RC4.2 focused (`test_paper_benchmark_protocol.py`, `test_a3_1_g3_contract.py`, `test_g3_f07_dispatcher_equivalence.py`, `test_a3_1_g2_contract.py`, `test_r4_g2_truth_support.py`) | system python | **175 passed** |
| New authorized-delta integrity suite (all 10 originally-red symptoms, §Issue 1) | system python / fresh venv (pb_34 only) | **all pass** |
| All 7 integrity verifier scripts run directly (`pb_30`, `pb_31`, `pb_32`, `pb_33`, `pb_34`, `pb_35`, `pb_37`) | system python / fresh venv (pb_34) | **all exit 0** |
| A3.x + paper-benchmark broad suite (`-k "a3_1 or a3_2 or a3_3 or a3_4 or paper_benchmark or rc3 or eng_environment"`) | fresh venv | **655 passed** |
| Fresh-environment full suite | fresh venv, 1210 collected | **17 failed/errored, all traced to `p2_compounds.parquet` (historical-only, out of scope); everything else passed** |
| Independent reviewers | — | **I1 PASS, I2 PASS — both below** |

### I1 — freeze/integrity lineage (fresh reviewer, PASS)

Independently enumerated the entire uncommitted diff by blob hash (not by
trusting a stated file list) and confirmed it matched exactly. Re-derived all
9 ledger entries' old/new SHA-256 pairs directly from `git show` rather than
trusting this document. Traced the classifier logic and then **adversarially
tested it live**: temporarily edited an unledgered file (`registry.py`) and,
separately, edited a ledgered file (`protocol.py`) beyond its authorized new
hash — confirmed both are still correctly rejected by `pb_33`, then reverted
and reconfirmed a clean tree. Ran `pb_30`/`pb_31`/`pb_32`/`pb_33`/`pb_35`/`pb_37`
directly (all exit 0) and the 6 pytest wrapper files (110 tests, all pass).
Found no historical digest edited, no test weakened, and no other silently-
broken frozen byte-comparison beyond the ones this closure already found and
fixed.

### I2 — Development-boundary + canonical-environment (fresh reviewer, PASS)

Independently re-read `generator.py` and `test_r4_g2_truth_support.py` from
source (confirmed zero I/O in the generator by grep, confirmed the test reads
`.truth` 6 times and `.inputs` 0 times), independently confirmed the
`generate_case("PB|development|...").truth` pattern predates RC4.2 in four
frozen files including `test_paper_benchmark_truth.py` (ancestor-verified),
and independently arrived at the same `DEVELOPMENT_ENGINEERING_FIXTURE_MATERIALIZATION_ONLY`
classification and the same recommendation not to replace the tests with
hand-built-only fixtures. Separately built its **own** fresh venv at
`/tmp/i2_review_env` from `requirements.lock.txt`, confirmed `pip install`/
`check`/`freeze` clean, confirmed Julia 1.12.6 / SymbolicRegression.jl 1.11.3
/ PythonCall.jl 0.9.26 all match the frozen identity, ran the full suite
**twice** for determinism (identical 17 failures both times, all traced to
`p2_compounds.parquet`), and confirmed the sklearn/rdkit environment-mismatch
contrast against bare system Python.

Failure classification is now exactly two categories, both honestly
separated per the mission's instruction:

- **Zero** new, unexplained failures.
- **17** true historical/local-artifact gaps (`p2_compounds.parquet`,
  gitignored, never tracked, regenerable via the unrelated wet-lab `t2_*`
  pipeline) — kept separately classified, not folded into "pre-existing
  environment" language now that the actual Python/Julia environment gap
  (sklearn/rdkit) is closed.

---

## Sealed status

`SEALED_CLEAN_NO_BLOCKING_FINDING`

---

# RC4.2.1 INTEGRITY CLOSED — READY AS RC5 ENGINEERING PARENT
