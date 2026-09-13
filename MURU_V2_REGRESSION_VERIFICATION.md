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
   undeclared-hard-import distributions and a Julia/`SymbolicRegression.jl`
   identity gate that has since grown a caller
   (`scripts/cloud_e6/preflight_e6.py`) the frozen test doesn't yet know
   about. The binary pass/fail outcome of these 4 tests is unchanged
   between base and head, and the check itself is a years-old
   environment-identity snapshot comparison, not new WUR v2 functionality
   under test.

   **Correction, found by independent review and not present in this
   document's first draft:** one of the 7 undeclared-hard-import items,
   `lxml`, is *not* pre-existing — it is a genuine new gap introduced by
   this WUR v2 generation. `src/muru/wur_v2/external_mzml.py` (new since
   PR #5's base) does `from lxml import etree`, and `lxml` is not pinned
   in `requirements.lock.txt`; anyone rebuilding the environment from that
   lock file alone would not get `lxml` and this WUR v2 module would fail
   to import. It does not flip this test's pass/fail status (the test was
   already failing on base for 4 unrelated reasons), so it produced no
   *new* red/green transition for Phase 1's classification purposes — but
   describing it, as an earlier draft did, as "none of it changed between
   base and head" was wrong, and is corrected here.

   This study attempted the direct fix (adding `lxml==6.0.2` to
   `requirements.lock.txt`) and then reverted it after discovering the
   lock file is itself under a frozen, cross-file hash contract in this
   same test module: `test_the_lock_pins_every_distribution_exactly_once_with_an_equality`
   hardcodes a distribution count (50); `test_the_tracked_bootstrap_is_the_same_bytes_as_the_enforced_pin_source`
   requires `requirements.lock.txt`'s sha256 to equal a separately tracked
   snapshot (`configs/rc3_requirements_lock_c7c2332.txt`); and
   `test_the_tracked_environment_manifest_matches_this_tree` requires it to
   equal a `tracked_lock_sha256` recorded in a manifest file. Editing the
   lock file without a coordinated update to those two other tracked
   artifacts turned 2 pre-existing failures into 2 *different* failures
   (still failing, but for a new reason) rather than fixing anything net —
   confirmed by rerunning `tests/test_eng_environment_closure.py` before
   and after the edit. This is exactly the class of change the mandate's
   "if fixing a defect changes anything material, STOP" principle argues
   against attempting casually: the lock file is governed by an
   RC4-era freeze whose update procedure this study does not have context
   for, and getting it wrong would leave the repository in a worse,
   internally-inconsistent state than leaving the disclosed gap alone. The
   edit was reverted (`git checkout -- requirements.lock.txt`); the
   working tree is clean of it. **The `lxml` pinning gap remains, is
   disclosed here precisely, and is left for whoever owns the RC4
   environment-closure contract to fix correctly** — it does not touch
   WUR v2's candidate, comparator, endpoint, or any scientific code path,
   only a packaging manifest.

2. **Missing Phase-2/Phase-3 synthetic-benchmark data (7 of the 11
   failures + all 14 errors)** — `tests/test_ov_*.py`,
   `tests/test_p3_*.py` and friends require large generated artifacts
   (`artifacts/p2_compounds.parquet`, a checkpoint store, `trajectories.parquet`,
   etc.) that are deliberately not present in this checkout (correctly —
   they are multi-gigabyte, regenerable-by-convenience, and irrelevant to
   WUR v2). Every one of these fails or errors identically on base, before
   any WUR v2 work existed.

No fix was made to any test-outcome-changing defect (the one genuine defect
found, the `lxml` pin, does not change any test's pass/fail outcome and was
left disclosed rather than half-fixed into a worse state). Per the mandate
("Historical/pre-existing failures may remain if they are genuinely
unrelated, but document them precisely"), the 25 pre-existing
failures/errors are left as-is. **No candidate re-freeze or re-audit is
triggered**, and nothing in this section touches the candidate, comparator,
endpoint, or any scientific code path.

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
