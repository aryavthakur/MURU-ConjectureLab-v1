# RC4.1 Environment Closure

**Status:** ENGINEERING ONLY. No scientific definition changed.
**Parent:** RC4 engineering freeze `c800e7a59eca904ee32231e43ce3d1ddda4a26ee`
(tag `engineering-rc4-a3-4`).
**Identity:** `muru-rc4.1-environment-closure-1.0.0`

## 1. The defect

A hostile exact-lineage reproducibility audit found that the tracked
`requirements.lock.txt` was a reduced Phase-1 lock of **39** distributions
(sha256 `1a6e61d6e006110e1afd8b2d065332107a8b2d05dec537ee5f4fc570887e13cb`).
It omitted SymPy, mpmath, PySR, gplearn and the Julia bridge, while
`README.md` line 55 instructs a replicator to build the environment with:

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

SymPy is a top-level import in the strict evaluator and eleven other modules,
so a fresh clone followed literally could not import the evaluation layer,
let alone execute a prospective search. The environment the repository could
actually be built from and the environment the science requires were not the
same environment.

The engineering lineage already knew this. `rc3_provenance` reads its pins
from `configs/rc3_requirements_lock_c7c2332.txt` and its module docstring
states outright that the tree's own lock "cannot serve as the RC3 pin
source". The gap was therefore not a hidden bug but an unrepaired packaging
split: the enforced pin source and the documented bootstrap were different
files.

## 2. The repair

`requirements.lock.txt` is now **byte-identical** to
`configs/rc3_requirements_lock_c7c2332.txt`:

| | before | after |
|---|---|---|
| pinned distributions | 39 | 50 |
| sha256 | `1a6e61d6...87e13cb` | `13b21b8c...553c357fa8` |

The 39 prior pins are unchanged; the repair is purely additive. The eleven
added distributions are `click`, `filelock`, `gplearn`, `juliacall`,
`juliapkg`, `mpmath`, `pysr`, `semver`, `sympy`, `tomli`, `tomlkit`.

No version was chosen here. The 50-pin lock is the one the **audited A3.2
null calibration declared in its own frozen execution manifest**
(`dependency_lock_commit = c7c2332`, `dependency_lock_sha256 =
13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8`), and it is
what the working engineering environment contains exactly. Adopting it
introduces no new resolution decision.

`c7c2332` was **not** cherry-picked. That commit also carries the RC2
adequacy package, `src/muru/budget.py`, pipeline integration and a
`pyproject.toml` that does not exist in the RC4 lineage; only its dependency
closure is relevant, and the 39 RC4 pins are a strict subset of its 50 with
no version moved.

## 3. Closure proof

A disposable interpreter was built from the repaired lock alone, without
reusing the project `.venv`:

```
/opt/miniconda3/bin/python3.13 -m venv <fresh>
<fresh>/bin/pip install -r requirements.lock.txt
```

* install exit 0, `pip check` exit 0
* `pip freeze` diffed against the lock: **empty**. Nothing extra was pulled
  in and nothing was missing, so the lock is transitively closed with no
  unpinned transitive escape.
* every prospective import resolves: numpy, pandas, scipy, sklearn, sympy,
  mpmath, rdkit, gplearn, yaml, pymzml, statsmodels, matplotlib, pysr
* PySR imported, Julia started, `SymbolicRegression.jl` loaded
* the frozen production backend `rc3_calibration_runner.PySRBackend` ran a
  real search at settings digest
  `36c1ef3c0791ccc931a2f1d5f6e277515f002d3581961cd5bfe265411f9ce89d`,
  identical to `FROZEN_SETTINGS_DIGEST`, and returned candidates

No Development, Held-out, Challenge or Confirmation case was constructed,
executed or inspected during the proof. The search probe ran on synthetic
noise that is not any benchmark case, at a seed inside the quarantined
engineering band.

## 4. Julia binding

The Python lock is not sufficient. `juliapkg` resolves the Julia runtime and
`SymbolicRegression.jl` from **compatibility ranges**, not pins:

```
julia               "=1.10.0, 1.10.3"
SymbolicRegression  "~1.11.0"
PythonCall          "=0.9.26"
```

A fresh install months from now can therefore legally resolve a different
patch of either. Pinning is not available through that path, so the identity
is frozen and enforced instead:

| component | frozen identity |
|---|---|
| Julia | 1.12.6 |
| SymbolicRegression.jl | 1.11.3 |
| PythonCall.jl | 0.9.26 |

* `configs/julia/Project.toml` (sha256 `2549db49...9689a27c54d7`) and
  `configs/julia/Manifest.toml` (sha256 `75fc2d89...780c8a6b280705`) vendor
  the exact resolved graph: 115 Julia packages, each with its version and
  `git-tree-sha1`.
* `pb_37_environment_closure.assert_julia_identity()` boots Julia through
  PySR and **raises** when the live stack is not the frozen one. It fails
  closed.
* `configs/rc4_1_julia_identity_proof.json` records a live reading of the
  loaded Julia module versions, not a declaration copied from a config file.
  It is written only by `--start-julia`, so a later run that never boots
  Julia cannot quietly replace a real proof with an assertion.

These are the versions the audited calibration environment reports when
booted. The calibration's own manifest recorded `julia: NOT_STARTED` because
building a manifest must not boot a Julia runtime; that is a recording
limitation of the manifest, not evidence that Julia was absent, and the
calibration ran through `PySRBackend`, which imports `PySRRegressor`.

The fresh environment independently resolved to the same Julia 1.12.6 and
SymbolicRegression.jl 1.11.3, which corroborates the identity but does not
replace the gate, since range resolution is time-dependent.

## 5. gplearn scope

`gplearn==0.4.3` is **retained, and is not a prospective search engine.**

* No module under `src/muru/paper_benchmark/` imports it. Its scientific use
  is the historical Phase-3 and objective-validation baseline
  (`muru.discovery.*`, `scripts/ov_*`, `scripts/t3_*`).
* It is nonetheless **mandatory to install**, because the frozen prospective
  provenance guard `rc3_provenance.REQUIRED_PACKAGES` lists it and
  `verify_dependencies()` refuses to build a provenance manifest when it is
  absent. That guard runs before the first prospective seed.

Removing it would change a frozen guard, so it stays, with its scope stated.

## 6. Integrity ledger

`requirements.lock.txt` is one of the 247 tracked paths frozen at the
original content freeze `d94d2c9`, so repairing it moves the A1 integrity
count from 237 to 236 byte-identical protected paths.

The change is declared as **engineering**, not as a science amendment.
`pb_30_amendment_a1_integrity.py` now reports `changed_by_engineering`
separately from `changed_by_amendment`, and
`_assert_engineering_paths_carry_no_science()` refuses any engineering-
declared path under `src/muru/paper_benchmark/`, `artifacts/`,
`MURU_PAPER_BENCHMARK*`, `tests/test_a3_*`, `tests/test_paper_benchmark*` or
the dataset configs. An engineering exemption therefore cannot be used to
launder a science change, which was not previously enforced at all.

## 7. What did not change

Benchmark science, case families, truth definitions, A3.1/A3.2/A3.3/A3.4,
calibration science, the threshold table, G1/G2/G3, secondary endpoint
definitions, the search grammar and the search budget are all untouched.
The A3.4 protected set remains 31/31 byte-identical.

## 8. Verification

```bash
python scripts/pb_37_environment_closure.py
python scripts/pb_30_amendment_a1_integrity.py
python scripts/pb_34_rc3_integrity.py
python scripts/pb_35_a3_4_integrity.py
pytest tests/test_eng_environment_closure.py tests/test_paper_benchmark_amendment_integrity.py
```

To verify the Julia side as well, add `--start-julia` to
`pb_37_environment_closure.py`. That boots a Julia runtime and takes seconds.
