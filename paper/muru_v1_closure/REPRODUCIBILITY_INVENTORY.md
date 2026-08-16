# MURU ConjectureLab v1 — Reproducibility Inventory

Everything needed to re-derive the reported result from the sealed bytes, and the digests that pin
each piece.

## 1. Identity of the executed run

| Object | Value |
|---|---|
| Run commit | `8d87143d4280602323aa33ee0b5481aaef0fb4a8` (`engineering-rc5-1-heldout-authorization`) |
| Tree state at execution | clean |
| Science freeze in force | `560bf28568e2762c60edc994aac7f2b6de14081f` (`benchmark-content-freeze-a3-5`) |
| Engineering parent | `69e33c778efb14362439941d25ebbfcfb1068284` |
| Partition | `held_out`, 240 cases, 30 seeds each, 7,200 searches |
| Record schema | `muru-rc5-case-record-2.0.0` |

## 2. Digests

| Object | SHA-256 |
|---|---|
| Execution manifest | `bcd197dce732f2b2ad156d04ac4285ab23371a8dce40cb1f98281615a01afd08` |
| Seal receipt | `df128cd9356a31e0350fbf0dcc5a359c4e9116dcebbf30bb5381ab80b2c5e9c4` |
| Global science plan | `f2a81a91346b7607f4bff5bf673eaadf60e5d058d7b9625a9e49f4d7a9732334` |
| Grammar identity | `e7c1468473e1bee32696022bf714767a2e994ee88803964f503c4804eef9097e` |
| Calibration manifest | `9950b964346581d104bf3069c992eec2599c88235f6598b2aed1bb31ac58fe0f` |
| Null-threshold table (as consumed) | `b9b6148276160ea84f223ff9cba3db0fb93fd974efa3e790bcacab312fe59425` |

The manifest digest recomputes under the declared canonical convention. The null-threshold digest
recomputes from `calibration/a3_2/threshold_table.json` and matches the digest carried by **every one
of the 240** sealed records — the link that makes Gate 2 and Gate 7 reproducible from a record alone.

## 3. Sealed evidence

| Item | Count |
|---|---|
| Case records | 240 |
| Seed-record files | 240 (7,200 seed entries) |
| Provenance log | 1 |
| Execution manifest | 1 |
| **Total sealed files** | **482** |
| Files re-hashing to their recorded SHA-256 | **482 / 482** |
| Raw files outside the seal | 0 |

Location: `.claude/worktrees/muru-heldout-a3-6/results/held_out/`. Read-only for all analysis;
nothing in this closure writes into it.

Seeds occupy a frozen band disjoint from every other partition's; all 11,400 seeds across all 380
cases are distinct, and each case's stored seeds match `rc5_seeds.case_search_seeds` exactly.

## 4. Environment

| Component | Version |
|---|---|
| Python | 3.13.12 |
| numpy | 2.5.2 |
| scipy | 1.18.0 |
| sympy | 1.14.0 |
| PySR | 1.5.10 |
| SymbolicRegression.jl | ~1.11.0 |
| scikit-learn | 1.9.0 (ceiling estimator) |
| Platform at execution | macOS 26.1, arm64 |

Full pins: `requirements.lock.txt`. The manifest records an `environment_lock_digest` alongside the
resolved package set and Julia graph.

## 5. Reproducing the analysis

The analysis is deterministic and requires no search. From the repair worktree:

```bash
PYTHONPATH=src python scripts/run_heldout_restored_analysis.py
```

writes `heldout_g1_recovery.json`, `heldout_restored_analysis.json` and
`heldout_independent_recomputation.json` into `results/restored/`, and exits non-zero if the
independent recomputation disagrees with the primary on any compared quantity.

```bash
PYTHONPATH=src python scripts/run_heldout_hostile_lenses.py
```

writes `heldout_hostile_review.json` and exits non-zero if any lens fails.

```bash
PYTHONPATH=src python scripts/build_muru_v1_manuscript_tables.py
```

regenerates every table and figure-data file under `paper/muru_v1_closure/` from those artifacts.

Runtime: the G1 recovery takes roughly 75 s for 164 cases; everything else is seconds.

## 6. Committed analysis artifacts

| File | SHA-256 |
|---|---|
| `results/restored/heldout_restored_analysis.json` | `32891d1c9354785ce7d5fdd98d6a631386d9c1d31f8f9c850e66afa376ac40a3` |
| `results/restored/heldout_independent_recomputation.json` | `5e79e5592448cb790fda370aafd9973e629aaf8374ddd5ab43b677f044bbac7c` |
| `results/restored/heldout_g1_recovery.json` | `b75725297acc0e50b78c3696f7922c72a6e1dba328352da352d9143a59cd777d` |
| `results/restored/heldout_hostile_review.json` | `264ae24dfedea27d583a0074ed29b7370a3f59f90aed83329cd3740930ce280e` |

Module and test hashes are listed in `audit/MURU_HELDOUT_RESTORATION_FINAL_DISPOSITION.md` §8.

## 7. Verification a reader can perform independently

| Claim | How to check it without trusting this repository's prose |
|---|---|
| The raw evidence is intact | re-hash all 482 files against `execution_seal_receipt.json` |
| The records are faithful to the frozen contract | re-run `evaluate_structural_acceptance` over all 240 from their own stored inputs; expect 0 disagreements |
| The denominators are 164 / 144 / 36 | call `registry.endpoint_case_count` for each of the three endpoints, and separately sum `held_out_cases_for` across the 20 families |
| No endpoint has a 240 denominator | the frozen scorers raise on a wrong-length sequence; feed one 240 long |
| G1's gate verdict | `m0_accepted` is recoverable directly from the sealed `a1_case_adequacy_status`; it alone caps competence at 67 of 164, and Wilson lower is monotone in successes |
| The G1 point estimate | re-run the recovery; A1 must reproduce all 164 sealed verdicts, which is the content-identity test |
| The two routes agree | `run_heldout_restored_analysis.py` exits non-zero on any disagreement |
| The checks can fail | `pytest tests/test_heldout_hostile_lenses_have_teeth.py` — 13 mutation tests |
| The repair is not a relabelling | `pytest tests/test_heldout_superseded_rules_differ.py` — reruns the superseded rules on the same bytes |

## 8. Test inventory

| Suite | Tests | Result |
|---|---|---|
| `tests/test_heldout_analysis_restoration.py` | 33 | pass |
| `tests/test_heldout_superseded_rules_differ.py` | 6 | pass |
| `tests/test_heldout_hostile_lenses_have_teeth.py` | 13 | pass |
| **restoration total** | **52** | **pass** |

Two pre-existing failures in the wider repository suite, both established as predating this work:

- `tests/test_rc5_authorized_delta.py::test_every_pinned_post_change_hash_matches_the_working_tree` —
  the A3.5 ledger pins `rc5_authorization.py` at `fd1dfe74…`, its content at `7cdd5a6`; A3.6 changed
  it to `e8fc53c5…` at the run commit without an A3.6 ledger entry. Governance bookkeeping, not
  science. Deliberately not repaired: editing a frozen A3.5 ledger to accommodate a later amendment
  would falsify what it attests.
- `tests/test_ov_pipeline.py` — errors on a missing `artifacts/p2_compounds.parquet`, a large data
  artifact absent from this worktree. Environmental.

## 9. Known reproducibility gaps

1. **No per-case content digest.** The execution manifest pins the global plan, grammar and
   calibration, but no per-case content hash. Content identity for the G1 recovery is therefore
   established empirically, by re-deriving A1 adequacy and matching all 164 sealed verdicts, rather
   than by digest comparison. Adding a per-case content digest to the manifest is a v2 requirement.
2. **G1 observables are not persisted.** `muru-rc5-case-record-2.0.0` carries no `g_spearman`,
   `trajectory_mae` or `per_energy_mean_mae`. A schema successor persisting all four G1 observables
   is specified but unexercised, because no partition may be rerun.
3. **The evidence root is an absolute path** recorded in the manifest and defaulted in the driver
   scripts. Both accept `--evidence-root`, so relocation is supported, but the recorded value is
   machine-specific.
