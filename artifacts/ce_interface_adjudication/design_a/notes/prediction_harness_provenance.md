# Design A prediction harness: inherited execution conventions

Study: MURU CE interface adjudication, Design A (study id `muru-ce-interface-adjudication-design-a`).
Harness: `scripts/ce_interface_adjudication/design_a/30_run_predictions.py`.
Tests: `scripts/ce_interface_adjudication/design_a/tests/test_prediction_harness.py`.
Written results-blind. Nothing in this note was derived from any measured spectrum, any comparator result
artifact, or any `*_RESULT.md`.

The Design A harness reuses, unchanged, the execution conventions of the already frozen comparator benchmark
(`muru-v2-comparator-benchmark-1.0`). It reuses them so that a difference between this study's predictions and
that study's predictions can only come from the collision-energy field, which is the quantity under
adjudication. Every inherited convention is listed in section 2 with its source line. Everything deliberately
not inherited is listed in section 3 with the reason.

Source files read for this note (code and technical provenance only):

- `scripts/comparator_benchmark/run_predictions.py`
- `scripts/comparator_benchmark/modal_app.py`
- `scripts/comparator_benchmark/container/seeded_run.py`
- `scripts/comparator_benchmark/container/mspred_h5_to_json.py`
- `scripts/comparator_benchmark/container/ckpt_hparams.py`
- `scripts/comparator_benchmark/t1_provenance.py`
- `scripts/comparator_benchmark/freeze_manifest.py`
- `artifacts/comparator_benchmark/technical/t1/t1_provenance.json`
- upstream ms-pred at commit `ed8311f22958cb37f055b663b5f56c5c77a2ee33`, clone at
  `/Users/aryav/muru-comparators/repos/ms-pred` (source read only, nothing executed, no checkpoint loaded)

---

## 1. What the harness does

`emit-inputs` builds six ms-pred `--dataset-labels` TSVs, one per (model, mapping) with
model in {`iceberg_2_1_msg_simulation`, `glacier_msg`} and mapping in {K1, K2, K3}, each covering every
(compound, NCE) cell of the Design A population, and writes
`artifacts/ce_interface_adjudication/design_a/prediction_inputs/prediction_input_manifest.json` recording every
file's sha256, the exact command line execution would run, the checkpoint identities with their expected
sha256, and the resolved environment variables. It imports neither torch nor modal, loads no checkpoint and
contacts no model.

`execute` refuses unless all three preconditions hold, in this order:

1. `MURU_CE_ADJUDICATION_EXECUTE=1` in the environment;
2. `refs/muru-freeze/muru-ce-interface-adjudication-design-a` resolves in git;
3. every emitted input file still matches its manifest sha256 (and every expected file is in the manifest).

Each refusal is a hard `SystemExit` naming the missing precondition. Only after all three pass does it hash
the checkpoints on disk and import the container runner.

The three frozen mappings, applied to the collision energy only:

| Id | Definition | Harness function |
| --- | --- | --- |
| K1 | `CE_input = float(NCE)` | `k1` |
| K2 | `CE_input = float(NCE) * theoretical_mh / 500.0`, IEEE-754 binary64, no rounding | `k2` |
| K3 | `CE_input = float(math.floor(K2))`, floor toward negative infinity | `k3` |

The `precursor` column always carries the unmodified `theoretical_mh`. It is a precursor m/z input, not a
collision-energy input, so no mapping is applied to it. This is asserted by
`test_precursor_column_is_unmapped_theoretical_mh`.

---

## 2. Conventions inherited, with sources

### 2.1 Seeding wrapper

| Convention | Source | Inherited as |
| --- | --- | --- |
| Prediction scripts are invoked through `seeded_run.py`, not directly | `scripts/comparator_benchmark/run_predictions.py:40`, `:45` | identical, same wrapper file, uploaded to `$WORK/seeded_run.py` |
| Seed value `42`, passed as the wrapper's first positional argument | `run_predictions.py:40`, `:45` | identical (`42`), recorded in the manifest under `seeded_run.seed` |
| Wrapper applies `pl.seed_everything(seed, workers=True)` then `runpy.run_path(script, run_name="__main__")` | `scripts/comparator_benchmark/container/seeded_run.py:13-17` | identical, wrapper file byte-for-byte, its sha256 recorded in the manifest |
| Reason the wrapper exists: `predict_smis.py` declares `--seed` (default 42) but leaves `seed_everything` commented out while shuffling entries with Python `random` | `seeded_run.py:3-5`; upstream `src/ms_pred/iceberg/predict_smis.py:91` (commented-out call), `:205` (`random.shuffle`) | inherited unchanged. GLACIER has no equivalent shuffle (`predict_smis_joint.py:404` uses `shuffle=False`), so the wrapper is load-bearing for ICEBERG and harmless for GLACIER; it is applied to both for symmetry |

### 2.2 Container environment

| Convention | Source | Inherited as |
| --- | --- | --- |
| `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` | `scripts/comparator_benchmark/modal_app.py:88-89` (rationale at `:85-87`: torch 2.6 defaults `torch.load` to `weights_only=True`, which rejects the `pathlib.PosixPath` stored in the official Lightning checkpoints' hyperparameters) | identical, recorded in the manifest `environment` block and asserted by `test_manifest_records_hashes_commands_checkpoints_and_env` |
| `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1` | `modal_app.py:88-89` | identical |
| `WORK` set by the runner to a fresh temp dir; inputs written into it by name; outputs collected by relative glob | `modal_app.py:62-72` | identical. The manifest records each TSV's `uploaded_as: "in.tsv"` because every command reads `$WORK/in.tsv` |
| Working directory `/opt/ms-pred`; ms-pred at `ed8311f`, installed with `uv sync --extra cpu` under `UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z` | `modal_app.py:46-50`, `:88`, `:21` | identical, image reused unchanged |
| Checkpoints mounted at `/ckpt/iceberg21_msg_simulation` and `/ckpt/glacier_msg` | `modal_app.py:51-52` | identical, both container paths and host paths recorded in the manifest |
| Function resources `cpu=4, memory=16384, timeout=3600`, CPU only | `modal_app.py:83` | identical (execute mode calls `MA.mspred_run` unchanged) |
| Runner records `returncode`, truncated stdout/stderr, `platform`, `machine`, per-output sha256 | `modal_app.py:73-75` | identical, `platform`, `machine` and `output_sha256` copied into the execution provenance record |
| Package freeze read back with `mspred_env()` | `modal_app.py:98-102` | identical, captured into `execution_provenance.json` as `container_package_freeze` |
| Host checkpoint and repo root `$MURU_COMPARATORS_HOME` (default `~/muru-comparators`) | `modal_app.py:20`, `t1_provenance.py:17` | identical env-var resolution |

### 2.3 ICEBERG invocation

Inherited verbatim from `run_predictions.py:40-44`:

```
/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/iceberg/predict_smis.py --dataset-labels $WORK/in.tsv --sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 --gen-checkpoint /ckpt/iceberg21_msg_simulation/gen/best.ckpt --inten-checkpoint /ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt --save-dir $WORK/out --out-name preds.hdf5
```

Every flag is carried over unchanged: `--sparse-out`, `--sparse-k 100`, `--max-nodes 100`, `--threshold 0.0`,
`--num-cpu-workers 0`, both checkpoint flags, `--save-dir $WORK/out`, `--out-name preds.hdf5`.
`--num-cpu-workers 0` additionally forces the serial `prepare_entry` path
(upstream `predict_smis.py:195-196`), which removes the parallel-chunking source of nondeterminism.
`--sparse-out` is required by the script itself (upstream `predict_smis.py:253` asserts it).

### 2.4 GLACIER invocation

Inherited verbatim from `run_predictions.py:45-47`:

```
/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/glacier/predict_smis_joint.py --dataset-labels $WORK/in.tsv --sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint /ckpt/glacier_msg/best.ckpt --save-dir $WORK/out --out-name preds.hdf5
```

GLACIER takes a single `--checkpoint` and has no `--max-nodes` or `--threshold`, matching the comparator's own
GLACIER command exactly.

### 2.5 HDF5 dump appended to both commands

Inherited verbatim from `run_predictions.py:48`:

```
 && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json
```

`parse.py` is `scripts/comparator_benchmark/container/mspred_h5_to_json.py`, uploaded unchanged; its sha256 is
recorded in the manifest. It reads the `PredSpecDB` exactly as written and dumps the stored float32 masses and
intensities with no transform (`mspred_h5_to_json.py:1-2`, `:29-30`), in `sorted(db.get_all_names())` order
(`:13`). Collected outputs are `["spectra.json", "out/preds.hdf5"]` (`run_predictions.py:143`); both are
written to the study output directory and hashed.

ms-pred prefixes every emitted spectrum name with `pred_` (upstream `predict_smis.py:190`,
`predict_smis_joint.py:183`); the comparator strips it with `removeprefix("pred_")`
(`run_predictions.py:149`). The Design A analysis step must do the same.

### 2.6 Input TSV column set, tokens and formatting

Inherited from `run_predictions.py:135-140`.

| Element | Source | Inherited as |
| --- | --- | --- |
| Column order `spec, smiles, ionization, collision_energies, instrument` and, for ICEBERG only, a trailing `precursor` | `run_predictions.py:135-138` (`if with_prec: row["precursor"]`), matching `with_prec=True` for ICEBERG and `False` for GLACIER at `:130` | identical; `test_column_set_and_order_match_the_comparator` asserts both column sets |
| Reason the `precursor` column is ICEBERG-only | upstream `predict_smis.py:166` reads `entry["precursor"]`; `predict_smis_joint.py:153-184` never reads it | identical |
| `ionization = "[M+H]+"` | `run_predictions.py:135` | identical (the Design A population is [M+H]+ only) |
| `instrument = "Orbitrap"` | `run_predictions.py:136` | identical. `Orbitrap` is index 0 of `common.instrument2onehot_pos` and is commented upstream as "Orbitrap HCD" (`src/ms_pred/common/chem_utils.py:277-283`), which is the Design A population's acquisition mode. ICEBERG passes the token through `normalize_instrument` (`predict_smis.py:78-80`), GLACIER does not normalise at all (`predict_smis_joint.py:162`), so a token outside the table would silently differ between the two models. `Orbitrap` avoids that |
| `collision_energies` cell written as `str([repr(<float>)])`, that is a Python list literal holding one single-quoted decimal string, for example `['19.9998']` | `run_predictions.py:136` | identical, implemented as `format_collision_energies`. `test_collision_energies_field_matches_comparator_byte_for_byte` compares against the comparator expression re-evaluated in the test, for nine values including both boundary cases |
| The container parses it with `ast.literal_eval` then `common.collision_energy_to_float` | upstream `predict_smis.py:183-186`, `predict_smis_joint.py:177-181`, `src/ms_pred/common/chem_utils.py:780-784` (`float(colli_eng.split()[0])` for a str) | unchanged. `repr` of a binary64 is the shortest round-tripping decimal, so the container recovers the identical double. Asserted by `test_collision_energies_field_shape_and_container_roundtrip` |
| Spec id `f"{key}_NCE{n}"` | `run_predictions.py:111`, `:135` | identical shape, with the Design A key: `f"{compound_id}_NCE{nce}"` |
| TSV serialization `pd.DataFrame(rows).to_csv(sep="\t", index=False).encode()` | `run_predictions.py:140` | identical call, so quoting, line terminator and float formatting match byte for byte |

### 2.7 Freeze gate and manifest discipline

| Convention | Source | Inherited as |
| --- | --- | --- |
| Refuse to run unless the study's freeze ref exists in git | `run_predictions.py:30`, `:55-58` (`git rev-parse --verify refs/muru-freeze/<prereg-id>`) | identical mechanism, ref `refs/muru-freeze/muru-ce-interface-adjudication-design-a` |
| Refuse to run unless the population inputs match their recorded sha256 | `run_predictions.py:32-33`, `:59-60` | generalised: the Design A harness hashes the emitted inputs against a manifest it wrote itself, and additionally hashes the population CSV into that manifest |
| Every produced artifact hashed into a manifest | `run_predictions.py:164-170` | identical idea, split into `prediction_input_manifest.json` (emit-inputs) and `execution_provenance.json` (execute) |
| Provenance record structure: recorded date, execution platform, repo commits, per-file checkpoint sha256 and byte counts, environment freezes and their sha256 | `t1_provenance.py:33-92`, `artifacts/comparator_benchmark/technical/t1/t1_provenance.json:1-99` | `collect_provenance()` mirrors this shape and adds the MURU git HEAD, branch and porcelain status, the driver platform, the freeze ref sha, the input manifest sha256 and the per-run output hashes |

### 2.8 Checkpoint identities

Taken from `artifacts/comparator_benchmark/technical/t1/t1_provenance.json` and re-verified from disk by
`verify_checkpoints()` before execution (file hashing only, no torch, no checkpoint load).

| Model | Container path | sha256 | bytes | Source |
| --- | --- | --- | --- | --- |
| ICEBERG 2.1 msg_simulation | `/ckpt/iceberg21_msg_simulation/gen/best.ckpt` | `1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70` | 41561644 | `t1_provenance.json:55-58` |
| ICEBERG 2.1 msg_simulation | `/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt` | `e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58` | 40604948 | `t1_provenance.json:63-66` |
| GLACIER MassSpecGym | `/ckpt/glacier_msg/best.ckpt` | `5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11` | 181602423 | `t1_provenance.json:83-86` |

Host paths are `$MURU_COMPARATORS_HOME/checkpoints/...` with the same relative layout
(`modal_app.py:51-52`). Archive hashes `ea510bba...d397a63` (ICEBERG, `t1_provenance.json:53`) and
`7e0fa24a...8d1258b` (GLACIER, `:81`) are recorded upstream and are not re-verified here.

Two further facts carried over unchanged from `t1_provenance.json:72`: the published ICEBERG 2.1
msg_simulation archive contains only `gen/` and `inten_contr/`, so the contrastive-finetuned intensity model is
the only intensity checkpoint available and is the one used. ms-pred is MIT licensed, with no separate licence
stated for the checkpoints (`t1_provenance.json:46`).

### 2.9 ms-pred code identity

| Element | Value | Source |
| --- | --- | --- |
| Repository | `https://github.com/coleygroup/ms-pred` | `t1_provenance.json:45` |
| Commit | `ed8311f22958cb37f055b663b5f56c5c77a2ee33` | `t1_provenance.json:47`, confirmed by `git rev-parse HEAD` in the local clone |
| Commit date | `2026-09-04T01:12:22-04:00` | `t1_provenance.json:48` |
| Install | `uv sync --extra cpu`, `UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z` | `t1_provenance.json:49`, `modal_app.py:21`, `:48` |
| Reference package freeze | `artifacts/comparator_benchmark/technical/t1/mspred_env_freeze.txt`, sha256 `a7ff2fcea09a4541748b85aae63bf13fc579fe8e7ed796251abc0d47f9782b78` | `t1_provenance.json:97` |

No retraining, no finetuning, no patch. Unlike FIORA, which the comparator study had to patch one character
(`t1_provenance.json:10`), ms-pred is used entirely as published.

---

## 3. Conventions deliberately NOT inherited

| Not inherited | Source in the comparator harness | Why not |
| --- | --- | --- |
| FIORA-OS v0.1.0 entirely: the `FIORA_CMD` string, the `fiora_image`, the `in.csv` input builder, the MGF parser, the one-character `SimulationFramework.py` patch and its hashes | `run_predictions.py:38-39`, `:70-85`, `:111-128`; `modal_app.py:32-40`, `:78-80`; `t1_provenance.json:4-42` | FIORA does not participate in Design A. Its CE interface is not under adjudication here. The test suite asserts no FIORA token appears anywhere in the harness or the manifest |
| The `mu` endpoint: `spectrum_mu`, `mu_rows`, `competitor_mu.csv`, the `%.17g` float format, `status`/`NO_SPECTRUM`/`EMPTY_OR_NONPOSITIVE` codes, `status_counts` | `run_predictions.py:27`, `:88-100`, `:162-169` | Design A adjudicates a collision-energy input convention by spectrum agreement, not by the comparator's MURU-specific mu statistic. Importing `muru.wur_v2.external_multims2` would also couple this harness to MURU internals it has no need for. Design A's criterion is preregistered separately and is not implemented in this harness at all |
| The frozen intensity inverse `intens_float32 ** 2` and the float32 to float64 promotion | `run_predictions.py:155-159` | That transform belongs to the comparator's mu pipeline. Design A's analysis step will declare its own treatment of stored intensities in the preregistration. The harness stores the native `preds.hdf5` and the untransformed `spectra.json` so that either choice remains available downstream |
| The `precursor_peak_emitted` descriptive flags and the 5 ppm root-fragment match | `run_predictions.py:125`, `:158`, `:167-168` | Descriptive-only diagnostics of the comparator study's population. Not an endpoint here |
| The two-condition design `("ev_primary", "raw_nce_sensitivity")` and the `ce()` function that implements it | `run_predictions.py:66-67`, `:131` | Superseded by design. The comparator study ran one primary condition plus one raw-NCE sensitivity diagnostic. Design A runs three predeclared conventions K1, K2, K3 symmetrically, with no primary-versus-sensitivity asymmetry, and adds K3 which the comparator had no analogue for. Reusing `ce()` would silently reintroduce the comparator's asymmetric framing. `test_no_fiora_and_no_raw_nce_sensitivity_leak_into_the_harness` asserts neither `ev_primary` nor `raw_nce_sensitivity` appears in this harness |
| The comparator's energy rungs `RUNGS = (20, 60)` | `run_predictions.py:35` | The Design A population is MassBank Eawag EQ [M+H]+ HCD at NCE 30 and 60. `NCE_RUNGS = (30, 60)` |
| The comparator's population files, their two hard-coded sha256 constants, and the `"\n".join(pop.key)` key-list cross-check | `run_predictions.py:31-33`, `:59-62` | Different population. Design A hashes `design_a_compounds.csv` into its own manifest instead. The key-list cross-check has no Design A analogue yet (see open question O-4) |
| The comparator's model-name strings `"ICEBERG 2.1"`, `"GLACIER"` as artifact keys | `run_predictions.py:130`, `:145` | Replaced by the unambiguous checkpoint-identifying keys `iceberg_2_1_msg_simulation` and `glacier_msg`, since Design A is a statement about specific published checkpoints and not about the methods in general |
| `ckpt_hparams.py` and the `checkpoint_hyperparameters.jsonl` record | `scripts/comparator_benchmark/container/ckpt_hparams.py`; `t1_provenance.json:73-76` | It calls `torch.load`. The hyperparameters are already recorded verbatim in `t1_provenance.json:74-75` for both ICEBERG checkpoints, so Design A cites that record rather than re-loading a checkpoint |
| The single-invocation structure that ran both conditions inside one `MA.app.run()` block and assembled one `mu` table | `run_predictions.py:109-162` | Design A keeps six independent invocations, each with its own `$WORK`, its own input hash and its own output hashes, so that a per-cell artifact can be attributed to exactly one (model, mapping) pair |

---

## 4. Exact command lines execution would use

Six invocations, one per (model, mapping). The command text is identical across the three mappings of a model:
the mapping enters only through the uploaded `in.tsv`. Each invocation uploads `in.tsv` (the mapping's TSV),
`parse.py` (`container/mspred_h5_to_json.py`) and `seeded_run.py` (`container/seeded_run.py`) into a fresh
`$WORK`, runs with cwd `/opt/ms-pred` and environment
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`, and collects
`spectra.json` and `out/preds.hdf5`.

ICEBERG 2.1 msg_simulation, for each of `iceberg_2_1_msg_simulation__{K1,K2,K3}__in.tsv`:

```
/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/iceberg/predict_smis.py --dataset-labels $WORK/in.tsv --sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 --gen-checkpoint /ckpt/iceberg21_msg_simulation/gen/best.ckpt --inten-checkpoint /ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt --save-dir $WORK/out --out-name preds.hdf5 && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json
```

GLACIER MassSpecGym, for each of `glacier_msg__{K1,K2,K3}__in.tsv`:

```
/opt/ms-pred/.venv/bin/python $WORK/seeded_run.py 42 src/ms_pred/glacier/predict_smis_joint.py --dataset-labels $WORK/in.tsv --sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint /ckpt/glacier_msg/best.ckpt --save-dir $WORK/out --out-name preds.hdf5 && /opt/ms-pred/.venv/bin/python $WORK/parse.py $WORK/out/preds.hdf5 $WORK/spectra.json
```

Outputs are written as
`artifacts/ce_interface_adjudication/design_a/prediction_outputs/<model>__<mapping>_preds.hdf5` and
`..._spectra.json`, with `execution_provenance.json` beside them.

---

## 5. Open questions a preregistration author must settle before execution

| Id | Question | Why it matters |
| --- | --- | --- |
| O-1 | Fold separation. The preregistration outline, section 5 steps 5 and 7, requires calibration-fold predictions first, then evaluation-fold predictions under the selected convention only. The harness as written emits every (compound, NCE) cell in one pass unless `--fold` is given, and the current `design_a_compounds.csv` carries no `fold` column. Either the split must be drawn and written into the population as a `fold` column before `emit-inputs` runs, or the prereg must explicitly license emitting both folds at once and gate the reading of measured spectra instead | Emitting evaluation-fold inputs early is harmless on its own, but running them early would burn the single sealed look |
| O-2 | Whether the manifest's `n_cells_per_model_mapping` should be the compound-cell count (33 compounds times 2 rungs = 66) or the record count. `design_a_records.csv` has one row per record and a compound may hold more than one record per rung. The harness predicts once per (compound, NCE) cell and leaves record-level aggregation to the analysis step | Determines the denominator of every per-cell endpoint, and whether replicate records are averaged or treated as separate observations |
| O-3 | The `theoretical_mh` used by K2 and K3 is the recomputed theoretical [M+H]+, not the deposited `deposited_precursor_mz`. The population file carries both. The comparator harness used its own `mh` column (`run_predictions.py:136`). K2 and K3 are sensitive to this choice at the fourth decimal, and K3's floor can flip for a cell sitting within that distance of an integer | A single flipped K3 cell changes a per-cell endpoint. The prereg must name the column and state that the same column feeds both the CE mapping and the ICEBERG `precursor` field |
| O-4 | Whether Design A wants the comparator's key-list cross-check (`run_predictions.py:62`), that is a second frozen file listing the population keys in order, as a redundant guard against a silently reordered population CSV. The harness currently sorts by `compound_id` and hashes the CSV, which is weaker | Cheap, and it is the check that would catch a population rebuild that changed membership without changing the file name |
| O-5 | The `instrument` token is fixed to `Orbitrap` for both models. The population's `instrument` column records `Exploris 240 Orbitrap Thermo Scientific` and an `instrument_type`. `Orbitrap` is the only ms-pred token matching Orbitrap HCD, and GLACIER does not normalise unrecognised tokens, so this is forced rather than chosen; the prereg should state it as forced and note that the checkpoints therefore cannot distinguish this instrument from any other Orbitrap HCD | Removes an apparent free choice from the record |
| O-6 | Whether NCE below 15 or above 60 will ever be added. The outline defers this (section 10). The harness hard-codes `NCE_RUNGS = (30, 60)`; extending it is a code change that would need a new freeze | Named here so that any later extension is visible as a deviation |
| O-7 | Determinism of ICEBERG's `random.shuffle` (`predict_smis.py:205`) across the three mappings. By construction the pre-shuffle entry list has the same length and the same compound order under K1, K2 and K3, and the seeded wrapper fixes the seed, so the permutation and therefore the batching should be identical across mappings, leaving the CE value as the only difference. That is an argument, not a measurement: it has not been checked for this population, and the comparator's own seeded-determinism check (`scripts/comparator_benchmark/t2b_seeded_determinism.py`) was run on a different one | If batching differed across mappings, a CE-independent batching effect could masquerade as a convention effect. A t2b-style replicate check on one mapping, before the sealed analysis, would close this |
| O-8 | Whether the study intends to record the untransformed `spectra.json` only, or also to preregister the intensity treatment (the comparator's single squaring inverse, `run_predictions.py:159`). The harness stores both the native HDF5 and the untransformed dump and applies no transform | The intensity treatment must be frozen before the calibration criterion is computed, or it becomes a free parameter |
