# MURU-WUR-v2 reproducibility review

Reviewer role: reproducibility reviewer. Date: 2026-09-12 (local), run timestamps 2026-09-13T01:3xZ UTC.

## Verdict

Every item reproduced exactly. All rebuilt data tables, the fold file, the committed representation files, the four candidate JSON files and their manifest, the committed OOF prediction parquet files for TA_RIDGE and TA_MORGAN_JOINT on PRIMARY and STRICT, and the Experiment 1 part A outputs are byte-identical to the committed copies. The only differences anywhere are the wall-clock fields (`seconds`, `created_utc`) that the scripts write into JSON sidecars, which cannot match by construction. No numeric discrepancy was found. The test suite passes (30 passed, 0 failed, 0 skipped).

Scope caveat: this is a same-host, same-environment reproduction (the Apple M3 machine and the /opt/miniconda3 environment the development program used). It proves that the committed outputs follow deterministically from the committed code plus the restored inputs. It does not prove cross-platform or cross-version stability. A second caveat is that Experiment 1 part A reuses the tracked PySR checkpoint store for the S2A arm, so S2A is reproduced from cached symbolic-search fronts, not from a fresh PySR search.

## Setup

Worktree: `.claude/worktrees/agent-abf68aa92d6dffc65`, detached at `52967a0` ("wur v2 run state: M5") on branch claude/muru-wur-v2-generation-b2ffa1. Nothing was committed, pushed or stashed.

Environment:

* Python 3.13.12 (Anaconda, Clang 20.1.8), macOS 26.1 arm64, Apple M3, 8 cores
* numpy 2.5.2, pandas 3.0.5, scipy 1.18.0, scikit-learn 1.9.0, rdkit 2026.03.5, pyarrow 25.0.1
* PYTHONPATH=src, OMP_NUM_THREADS=4 (Experiment 1 part A sets its own thread variables to 1, as committed)

Data restored (untracked by design):

1. WUR release: `/Users/aryav/Downloads/20552933.zip` (203,752,342 bytes) unzipped flat into `data/external/wur/`. `build_manifest` reported 20 files, `missing = []`, `hash_mismatches = []`.
2. LCSB artifacts copied from the main checkout's `artifacts/` into the worktree's `artifacts/` (none existed there beforehand). SHA-256 of the copies:
   * p2_compounds.parquet 59d54748a9888be0029490bae39a22462f8ccef1114386d1f00fa467c60f2119
   * p2_descriptors_tierA.parquet a270c2d220d229102e7f42c2dcc1d313362358433b395cd2a561644a437a969c
   * p2_dev_corpus.parquet 4fd90dfe0691cf6386c64e325725c50fa8b1299c9c5e0720b5b162637357cd72
   * p2_splits.parquet 1a7d39db4fdcacec3c89b8b3ea6a539af22c48019858ca334fb34a1618609c7e
   * trajectories.parquet 0b2ea8302485fdb91e96b3d7e6bbb673a014f05b314d61e1c434fb3ae88c5881
   * raw_branch_merged.parquet 3f46b5450151f921abda4453ab7557270a576fb9e110411bdf07259fef774cb7
   * raw_branch_scans.parquet 9049dbc75c8eb7e7280d13009028a495ea1c7cf73e66fbd2f576e84e5b726867

Before any builder ran, the committed derived outputs `artifacts/wur_v2/data/` (all tables and representations), `artifacts/wur_v2/folds.json`, `artifacts/wur_v2/candidate/`, `artifacts/wur_v2/runs/` (entire directory) and `artifacts/wur_v2/exp01/` were moved to a scratch folder outside the repository. Every builder therefore read only upstream inputs, never a committed v2 output. After all comparisons, the moved-aside files that were not rebuilt (the other cached runs and `exp01/part_b_v2_baselines.json`) were copied back so the worktree matches the commit except for the timing fields noted below.

Scratch code written for this review lives in `docs/wur_v2_reviews/repro_scratch/` (compare_representations.py, repro_oof_runs.py plus its result JSON, compare_exp01.py plus exp01_stdout.txt, thread_sensitivity.py). None of it calls `ledger.append`, and no ledger-writing script was run; `artifacts/wur_v2/ledger/ledger.jsonl` is unmodified.

## a. Spectra and population

`build_v2_spectra.py` (wall 8 s, script reports 7.3 s): 1,010 WUR keys, 12,432 WUR spectra, 0 defects, 6,060 cells, 2,741 LCSB spectra.
`build_v2_population.py` (wall 3 s): 1,325 compounds (439 LCSB primary, 886 WUR primary, 124 on both instruments), 765 scaffold groups, 558 strict clusters, 6,604 aligned cells, bridge a = -5.95552603907965, b = 0.8618030610784555, 0 parent-key mismatches, 0 confirmation keys present.

`keys_sha256` = 81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd, as expected.

All nine data files are byte-identical to the committed copies (SHA-256):

* compounds.csv 87d79ab7f9e02eb7c99c4ea9b7e12a87568d0b2c8c81c372b22d44bec862e34c
* long_aligned.csv 2e86f74198af956e494e6157a8ef2ded8a683035458205dfaad7c5da4cdc9c6f
* native_cells.csv 9aa09a1d040ea6d4687224881623e5050008b2fccd1743bdec1deafeaa6a653e
* population_manifest.json 55ee99a7cab8f4d51c80146a4154cf38e002e35ec5f10568c7bee3cfd44735f5
* wur_aligned_all.csv 60f3f8bb6cdec4b3beec97931aeb50017c6f91c7ace73185c00cb5c94f41f107
* wur_pos_cells.csv c5c36fb2df5707ae5b39dc52acfc6e9eaf44627c0260fca2de0d7082928fd40c
* wur_pos_identity.csv ec5c3bd5204daa6e76be6cf2995ab84b3d90fede51dfef235b1c49aa33b86c36
* wur_pos_spectra.parquet df806afdc6f81365da6f8575cd605551a0d7e558a760af76411600bfd3993dc5
* lcsb_pos_spectra.parquet ce11ff7c3be574ca375ec1abab46c6c2efe728d797859e877263db9899051061

## b. Folds

`build_v2_folds.py` (wall under 1 s). The rebuilt `folds.json` is byte-identical to the committed file (SHA-256 53a9a8c5accf6d86a8701f842e53f705a6e0608dec8c0cc6fa337d116ef3d58e), so every assignment hash matches:

* PRIMARY 48b94e86efb34d25fe7464a336efedfb9c21a3a8698c333c3b78decbcfd0a8b4
* PARTITION_S1 a4f44ae2f31b6590eb3518cc319d1fae36259d17eece1fdab90c72215b83fd63
* PARTITION_S2 0b0cb158753750876ee3a3d4e3483d7c04dcb7f437473fcb94943a7347842c1b
* STRICT dde61276e24beef1fdb79cc40d428ddffcffded08f3f4d617c4c671013cc20a4
* RANDOM 712947ec88b4b14b4b8be1fc1216b66addd4f3369383176adea4dc1042816a33
* GIANT c67dfb83e4846b49ada672cfa8233e0a53a2be8d10491fbdeb71acc51db45be3

Fold sizes are 265 x 5 for every grouped and random partition, the 183 benzene-scaffold compounds sit whole in fold 0, and there are 15 distinct held-out sets across PRIMARY plus the two sensitivity partitions.

## c. Representations

`build_v2_representations.py` (wall 15 s, script reports 14.0 s). Printed hashes (first 16 hex of SHA-256 of the array bytes):

* TIER_A (1325, 12) 45bdfdd7aef2aa2b
* MORGAN (1325, 2048) 1dd2e97e70c18d5b
* MORGAN_COUNTS (1325, 2048) f447b437000370d2
* ATOMPAIR (1325, 2048) 84e400a0ae38802f
* ATOMPAIR_COUNTS (1325, 2048) a66f1c71a11198f7
* MACCS (1325, 167) 13b95c01da6dde88
* MINMAX_MORGAN (1325, 1325) 60c5ff2f3ec632b2
* MINMAX_ATOMPAIR (1325, 1325) 5c42f709bd311cb3

The two tracked files are byte-identical to the committed copies: TIER_A.parquet (file SHA-256 c490ba9baa4ca701...) and MACCS.parquet (644c7888c3b4e220...); index, columns and values match with max absolute difference 0.0, and the array hashes computed from the committed files equal the printed ones.

The printed hashes are not recorded anywhere in the committed tree, so the six untracked blocks have no committed reference. As a secondary check only, all eight rebuilt files are byte-identical (file SHA-256) to the untracked copies in the development worktree `recursive-executor-framework-07dd81`. Those copies carry a 2026-09-12 20:59 modification time, so they are the development session's files, not an independent archive.

## d. OOF runs from an empty cache

`artifacts/wur_v2/runs` did not exist when `repro_oof_runs.py` started (the script asserts this), and `runner.run` was called with `use_cache=False`. Total wall 26 s (24.3 s internal; TA_RIDGE 0.74 s and 0.79 s, TA_MORGAN_JOINT 11.2 s and 11.0 s).

| partition | model | P1 reproduced | P1 committed |
|---|---|---|---|
| PRIMARY | TA_RIDGE | 0.13054598985817814 | 0.13054598985817814 |
| PRIMARY | TA_MORGAN_JOINT | 0.11599941847410669 | 0.11599941847410669 |
| STRICT | TA_RIDGE | 0.13268637788545154 | 0.13268637788545154 (EXP08B) |
| STRICT | TA_MORGAN_JOINT | 0.12281854776057843 | 0.12281854776057843 (EXP08B) |

P1 ratio joint/TA: PRIMARY 0.8885712889390591, STRICT 0.9256304205289858 (expected 0.9256).

Against the committed parquet files that were moved aside, for all four runs: identical key index (1,325), max absolute mu difference 0.0, max absolute log g difference 0.0, fold column identical, per-fold selected configuration identical, inner OOF tables identical (max absolute difference 0.0). The rebuilt `.parquet` and `.inner.parquet` files are byte-identical to the committed ones. The `.json` sidecars differ only in `seconds` and `created_utc`.

`runner.compare` on the rebuilt runs (with B0 and the 2,000-replicate cluster bootstrap) reproduces all 51 numeric fields of the committed `EXP08B_TA_MORGAN_JOINT.json` comparison block for PRIMARY and for STRICT with max absolute difference 0.0, including P1_ratio_ci [0.8650671578854009, 0.9105586625700234] on PRIMARY and [0.8959719905370668, 0.9550566519582481] on STRICT.

Extra check (not requested): re-running PRIMARY TA_MORGAN_JOINT through `engine.run_cv` with 1 and with 8 BLAS/OpenMP threads gives the same P1 and a max absolute mu difference of 0.0 against the 4-thread run, with the same selected configurations. On this host the result does not depend on thread count.

## e. Candidate

`build_v2_candidate.py` (wall 6 s). The script imports the ledger module but never calls it. All five output files are byte-identical to the committed copies, so the manifest sha256 values match:

* V2_TA_MORGAN_JOINT 9eaa78d6126f4dc826d58bc46915781dc990ad997c2adbfdd7e1ab392589ed93 (alpha 0.3, block_weight 0.1, n_training 1325)
* V2_REF_TA_RIDGE 2f575f38bcbacf60382507b12d403f0ee5701f543fe1378c47c0baa84a5962b5 (alpha 0.1)
* V2_REF_B1_MASS 10228c2832d07d0af2cf011ae831d32c69cab16c01465cc5435458436302a263
* V2_REF_B0_NULL b910cc0d8a16002612a010d5898cf436edd4dd0ac60612371e8fdfac7b7ff56a
* reload_parity_max_abs_logg 2.220446049250313e-15 (same as committed; below the script's 1e-9 assertion)

## f. Experiment 1 part A

`exp01_estimand_audit.py` (wall 12 s, script reports 10.07 s against 9.39 s committed). It wrote only into `artifacts/wur_v2/exp01`. A recursive comparison of `part_a_stage3_estimands.json` against the committed copy finds zero differences in every block: experiment, population, training_population, reproduction (21 numeric fields), estimands (126), comparisons (528 numeric, 32 non-numeric), diagnostics (13). The only textual diff is the top-level `seconds` field. `stage3_reproduced_predictions.npz` is byte-identical (git reports it unmodified); all eight arrays match with max absolute difference 0.0 and identical NaN patterns.

Reproduction block (rebuilt, identical to committed): V1B_RIDGE_TIERA P1 0.12514071092413145, S2A_FROZEN_PIPELINE 0.14746430045222683, B0_NULL_PROFILE 0.16759015537753202, B1_MASS_ONLY_ISOTONIC 0.141954738498782, V1A_STABLE_LAW 0.13063210493573843, V1C_RICH_RIDGE_24 0.12360237160082019, V1B_WUR_ONLY_TRAINED 0.12646058830120577. Each equals the historical Stage 3 record, with max per-compound RMSE differences between 1.4e-16 and 5.0e-16. One cosmetic point that was already present in the committed file: the S2A value recorded in `stage3_result.json` prints as 0.1474643004522268, one digit shorter than the reproduced value, a float round-off difference of about 3e-17. It is not a new discrepancy.

As noted above, the S2A arm reads its 30 PySR seeds from the tracked checkpoint store `artifacts/wur_stage3/ckpt_s2a_stage3`. No PySR search was run, and git reports that store unmodified.

## g. Tests

`python3 -m pytest tests/wur_v2 -q`: 30 passed in 2.95 s (wall 4 s), no failures, no skips. This ran against the rebuilt artifacts (data, folds, candidate) and a runs cache containing only the four reproduced runs. Afterwards the ledger, `artifacts/wur_stage2b` and `artifacts/wur_stage3` were still unmodified.

## Final worktree state

`git status` shows only the `seconds`/`created_utc` changes in the four run sidecar JSON files and in `exp01/part_a_stage3_estimands.json`, plus the untracked `docs/wur_v2_reviews/`. The untracked representation files and restored input data are gitignored.

## Summary table

| item | expected | reproduced | match | note |
|---|---|---|---|---|
| WUR release hashes | 20 files, 0 missing, 0 mismatches | 20 files, 0 missing, 0 mismatches | yes | zip 203,752,342 bytes |
| a. population keys_sha256 | 81eef787...8c0abd | 81eef787...8c0abd | yes | 1,325 compounds |
| a. compounds.csv | committed file | byte-identical | yes | sha 87d79ab7... |
| a. long_aligned.csv | committed file | byte-identical | yes | sha 2e86f741...; 6,604 cells |
| a. native_cells.csv | committed file | byte-identical | yes | sha 9aa09a1d... |
| a. population_manifest.json | committed file | byte-identical | yes | sha 55ee99a7... |
| a. other spectra/cell tables (5 files) | committed files | byte-identical | yes | wur_pos_*, wur_aligned_all, lcsb_pos_spectra |
| b. folds.json assignment hashes (6) | committed hashes | identical; whole file byte-identical | yes | sha 53a9a8c5... |
| c. TIER_A.parquet | committed file | byte-identical, hash 45bdfdd7aef2aa2b | yes | |
| c. MACCS.parquet | committed file | byte-identical, hash 13b95c01da6dde88 | yes | |
| c. untracked blocks and kernels (6) | no committed reference | hashes printed above | n/a | identical to development worktree's untracked copies |
| d. PRIMARY TA_RIDGE P1 | 0.13054598985817814 | 0.13054598985817814 | yes | OOF max abs diff 0.0 |
| d. PRIMARY TA_MORGAN_JOINT P1 | 0.11599941847410669 | 0.11599941847410669 | yes | OOF max abs diff 0.0 |
| d. STRICT ratio joint/TA | 0.9256 | 0.9256304205289858 | yes | equals EXP08B to all digits; OOF max abs diff 0.0 |
| d. OOF parquet and inner parquet (8 files) | committed files | byte-identical | yes | sidecar JSON differ only in timing fields |
| d. EXP08B comparison blocks incl. bootstrap CIs | committed values | 51 of 51 fields per partition, diff 0.0 | yes | PRIMARY and STRICT |
| e. V2_TA_MORGAN_JOINT sha256 | 9eaa78d6...589ed93 | 9eaa78d6...589ed93 | yes | alpha 0.3, block_weight 0.1 |
| e. comparator sha256 (3) and manifest | committed manifest | byte-identical | yes | reload parity 2.22e-15 |
| f. exp01 part A reproduction block | committed JSON | all fields diff 0.0 | yes | only `seconds` differs; S2A from cached PySR checkpoints |
| f. exp01 predictions npz | committed file | byte-identical | yes | |
| g. tests/wur_v2 | pass | 30 passed, 0 failed, 0 skipped | yes | 2.95 s |
| extra: thread-count sensitivity | not specified | 1, 4, 8 threads identical | yes | same host only |
