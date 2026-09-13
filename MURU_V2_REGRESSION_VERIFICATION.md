# MURU-WUR-v2 Full-Repository Regression Verification (Phase 1)

## 1. Targeted suite (as explicitly requested)

```
python3 -m pytest tests/wur_v2 tests/test_wur_stage2_*.py -p no:warnings -rs
```

Run on branch `claude/muru-v2-msnlib-confirmation` (HEAD at the time,
`1be9d54`, i.e. `dc1f04d0...` plus the Phase 0 preflight/gitignore commits,
neither of which touches any source or test file).

**Result: 116 passed, 0 failed, 0 skipped, 68.16s.**

(The mandate's cited prior figure of "289 passed" reflects a different,
larger targeted selection from an earlier point in the program; the glob
`tests/wur_v2 tests/test_wur_stage2_*.py`, run exactly as specified, matches
116 tests in the current tree. This is reported rather than reconciled to
289.)

## 2. Full repository suite — HEAD

```
python3 -m pytest -p no:warnings -rs
```

Branch `claude/muru-v2-msnlib-confirmation`, HEAD `1be9d54`.

**Result: 11 failed, 2014 passed, 60 skipped, 14 errors, 600.59s (10m 0.6s).**

## 3. Full repository suite — PR #5 base

Same command, run in a separate detached worktree
(`/tmp/muru_base_comparison_17027e1`) at
`17027e13614cc850d88bcb72b3e8b8c2458eb00a` (`fable/wur-stage2-muru-development`,
PR #5's base), same machine, same Python interpreter and site-packages (no
per-worktree virtualenv — package versions below are identical by
construction).

**Result: 11 failed, 1967 passed, 60 skipped, 14 errors, 583.14s (9m 43.1s).**

## 4. Classification

The extra 47 passed tests on HEAD (2014 vs 1967) are new WUR v2 tests added
between the base and PR #5 head — none of them fail.

Every failing/erroring test name was extracted from both logs and compared
directly.

**All 11 failures and all 14 errors are byte-identical in name and order
between HEAD and BASE.** Classification per the mandate's four buckets:

| Bucket | Count | Basis |
|---|---|---|
| Pre-existing on base | 11 failed + 14 errors (100% of both) | identical test-name sets on HEAD and BASE |
| Newly introduced by v2 | 0 | — |
| Ambiguous | 0 | — |

Two distinct root causes account for all 25:

1. **`ENVIRONMENT_CLOSURE` / RC4 lock drift (4 of the 11 failures)** —
   `tests/test_eng_environment_closure.py`. These compare *this sandbox's*
   installed package set against a historical frozen lock
   (`muru-rc4.1-environment-closure-1.0.0`, RC4 parent
   `c800e7a59eca904ee32231e43ce3d1ddda4a26ee`) from an earlier phase of the
   MURU program (predates WUR v2 entirely). The verifier reports 7
   undeclared-hard-import distributions (e.g. `lxml`, `fixtures`, and
   several intra-repo test/script module names it mistakes for
   third-party packages) and a Julia/`SymbolicRegression.jl` identity gate
   that has since grown a caller (`scripts/cloud_e6/preflight_e6.py`) the
   frozen test doesn't yet know about. None of this is WUR v2 code, none of
   it changed between base and head, and it is an environment-identity
   check against a years-old snapshot, not a functional regression.
2. **Missing Phase-2/Phase-3 synthetic-benchmark data (7 of the 11
   failures + all 14 errors)** — `tests/test_ov_*.py`,
   `tests/test_p3_*.py` and friends require large generated artifacts
   (`artifacts/p2_compounds.parquet`, a checkpoint store, `trajectories.parquet`,
   etc.) that are deliberately not present in this checkout (correctly —
   they are multi-gigabyte, regenerable-by-convenience, and irrelevant to
   WUR v2). Every one of these fails or errors identically on base, before
   any WUR v2 work existed.

No genuine software or reproducibility defect attributable to WUR v2 or to
this study's own changes was found. No fix was needed and none was made;
per the mandate ("Historical/pre-existing failures may remain if they are
genuinely unrelated, but document them precisely"), they are left as-is.
**No candidate re-freeze or re-audit is triggered.**

## 5. Environment

| Component | Version |
|---|---|
| Python | 3.13.12 |
| OS | Darwin 25.1.0 arm64 (macOS, Apple Silicon) |
| numpy | 2.5.2 |
| scipy | 1.18.0 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| rdkit | 2026.03.5 |
| pymzml | 2.6.1 |

Identical for the HEAD and BASE runs (same interpreter/site-packages, no
per-worktree environment). Full logs preserved at
`/tmp/muru_regression/head_full_suite.log` and
`/tmp/muru_regression/base_full_suite.log` for this session (not committed —
ephemeral scratch, ~600 lines each; the material facts are captured above
and in `artifacts/wur_v2_confirmation/regression_verification.json`).
