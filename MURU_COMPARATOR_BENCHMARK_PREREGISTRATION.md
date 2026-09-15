# MURU-WUR-v2 vs full-spectrum predictors on the frozen mu endpoint: preregistration

**Identifier:** `muru-v2-comparator-benchmark-1.0`
**Status:** FROZEN before any benchmark inference. No comparator prediction exists for any PR #7 compound. MURU's
PR #7 per-compound errors have not been computed on this population.
**Frozen artifacts:** `artifacts/comparator_benchmark/freeze/freeze_manifest.json` records the SHA-256 of every file
this protocol depends on. The freeze commit is the one that adds this document and that manifest. Local ref:
`refs/muru-freeze/muru-v2-comparator-benchmark-1.0`.
**Upstream records:**
- Feasibility audit: `MURU_COMPARATOR_FEASIBILITY_AUDIT.md` (commit 21fae1a, updated at freeze).
- Technical phase T1 to T4: `artifacts/comparator_benchmark/technical/`, `artifacts/comparator_benchmark/population/`.
- PR #7 (`muru-v2-msnlib-confirmation-2.0`) is used only as the source of the frozen population identity, the frozen
  MURU model and the already-measured mu table. It is not modified.

## 1. Question

When public full-spectrum MS/MS predictors are reduced to MURU's exact frozen mu endpoint, how accurately do they
predict collision-energy-dependent fragmentation extent at fixed HCD NCE 20 and 60, relative to MURU-WUR-v2, on
MSnLib screening compounds absent from every compared checkpoint's training release?

## 2. Frozen models

| Role | Exact identity | Code | Weights (SHA-256) |
|---|---|---|---|
| MURU | `V2_TA_MORGAN_JOINT`, canonical-JSON sha256 `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` (git blob `f0e0a8d`), frozen in PR #7 | this repository, `muru.wur_v2.candidate.predict_mu` (blob `7660229`) | n/a |
| Comparator 1 | **FIORA-OS v0.1.0** | BAMeScience/fiora tag v0.1.2 `53ac2473665f76d6a47f14e49006cc8756431f30`, minimally patched (section 2.1) | `fiora_OS_v0.1.0.pt` `adf44d61e40083f23a593cd6a3914e8008c12637b556d0bf2abd6ac467ab55f5`; `_state.pt` `0615f268b10564a0bc262d43571a5f414a9c53083d65df3200bec89b9a258790`; `_params.json` `f4fd5a40bff01bfe8a244ac466bb56ee61bc789a01fc81e5102f8ec60ef3c85a` |
| Comparator 2 | **ICEBERG 2.1**, MassSpecGym `msg_simulation` release | coleygroup/ms-pred `ed8311f22958cb37f055b663b5f56c5c77a2ee33` (no tag) | `gen/best.ckpt` `1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70`; `inten_contr/best.ckpt` `e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58`; archive `ea510bba5bba7d34a49f15850f176e87aaec56795757db2f0b2366085d397a63` |
| Comparator 3 | **GLACIER**, MassSpecGym release (arXiv 2606.29161 v1) | coleygroup/ms-pred `ed8311f` | `best.ckpt` `5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11`; archive `7e0fa24a19163513fe7cbeea3bf51a48cdd33bf2dbe8ac7a0457cbbf28d1258b` |

**Naming rule:** each comparator is always named by the exact checkpoint above. FIORA-OS v0.1.0 is never described
as "FIORA" or as the current FIORA state of the art.

**Excluded:** the default FIORA-OS v1.0.0 (sha256 `273807127861...`), because its compound-level MSnLib split cannot be
reconstructed and all 1,794 PR #7 compounds lie in its training release. The NIST-trained FIORA, ICEBERG and GLACIER
weights are also excluded because they are not public.

**Checkpoint facts recorded in T1:**
- The ICEBERG 2.1 `msg_simulation` archive contains only a contrastive-finetuned intensity model (`inten_contr`,
  epoch 5, `contr_weight 1.0`).
- The GLACIER checkpoint is contrastive-finetuned as well (`contr_weight 1.0`, `contr_loss_fn entropy`, epoch 23).
- These are the only public MassSpecGym checkpoints for each model, so both are used as published.
- Source URLs, hyperparameters and licences (MIT code; no separate weight licence stated) are in
  `technical/t1/t1_provenance.json` and `technical/t1/checkpoint_hyperparameters.jsonl`.

### 2.1 FIORA-OS v0.1.0 inference implementation

- **The patch:** the v0.1.2 release is used with exactly one correction, in `fiora/MS/SimulationFramework.py` line
  124, `sim_peaks["intensity"][i] == ...` becomes `sim_peaks["intensity"][i] = ...` (`technical/t1/fiora_v0.1.2_minimal_patch.diff`).
  The release intended this assignment: it squares compiled_probsSQRT output back to linear intensity, but the
  release writes a no-op comparison.
- **Unpatched output:** T2 showed the unpatched release emits sqrt-scale intensities.
- **Patched output:** for every one of 20 example spectra, the patched output is exactly `I_unpatched ** 2 / max(I_unpatched) ** 2`
  (maximum absolute difference 0.0).
- **Equivalence to HEAD:** FIORA HEAD `e19ef82` running the same checkpoint produced identical peak sets and
  intensities (maximum absolute m/z and intensity difference 0.0). The equivalence holds, and per the user's
  safeguard the minimally patched release is the benchmark implementation.

### 2.2 Execution platform

Modal CPU containers, Linux x86_64 (gVisor), Python 3.11.12, images defined in `scripts/comparator_benchmark/modal_app.py`:

- **FIORA image:** torch 2.6.0+cpu; the packages FIORA imports, at FIORA `e19ef82` `constraints.txt` versions (rdkit
  2024.9.6, torch-geometric 2.6.1, numpy 2.1.3); system `libxrender1`, `libxext6` for `rdkit.Chem.Draw`.
- **ms-pred image:** upstream `uv sync --extra cpu` with `UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z` (resolved: torch
  2.6.0+cpu, dgl 2.5.0, rdkit 2025.3.6, pytorch-lightning 2.6.5, pygmtools git `5b7b3f8`).
- **Freezes:** full package lists in `technical/t1/*_env_freeze.txt`.
- **Checkpoint loading:** `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` is set in ms-pred runs. torch 2.6 otherwise refuses to
  unpickle the `pathlib.PosixPath` inside the official Lightning checkpoints' hyperparameters. No model code is
  changed.
- **Seeding:** ICEBERG's `predict_smis.py` declares `--seed 42` but leaves its `seed_everything` call commented out
  while shuffling entries with Python `random`. Unseeded, 2 of 20 example spectra changed top-100 membership between
  runs (mu change up to 3.5e-4). All ms-pred predictions therefore run through `container/seeded_run.py 42`, which
  applies `pytorch_lightning.seed_everything(42)` and executes the unmodified script. Seeded runs were
  HDF5-byte-identical for ICEBERG and GLACIER in both energy conditions.

## 3. Frozen common population

- **Definition:** PR #7 frozen population (1,794) ∩ MURU-supported (frozen PR #7 support rule) ∩ FIORA-supported ∩
  ms-pred-supported ∩ absent from MSnLib v1.0 (Zenodo 11163381) at the parent-InChIKey-first-block and library level
  ∩ absent from MassSpecGym 1.5 in every fold (train, val and test). MassSpecGym test-fold compounds are not restored.
- **T4 (structure, parser and featurization acceptance only, no forward pass):**
  - FIORA-OS v0.1.0 `build_metabolites`: 2,654/2,654 rows accepted.
  - ICEBERG 2.1 entry preparation and root featurization: 5,308/5,308 rows accepted (both energy conditions).
  - GLACIER `prepare_entry`, `GraphormerFeatDataset` and `collate_predict`: 5,308/5,308 rows accepted.
  - **Exclusions: none.**
- **Frozen population: 1,327 compounds in 1,254 scaffold groups (largest group 6).**
  - `population/common_population.csv` sha256 `5526441961102c41b128993b7e0af686e6bb63a10299e002cd230c2f0d0276fe`
    (columns key, scaffold_group, mh, model_smiles; sorted by key).
  - Key list (sorted parent InChIKey first blocks, newline-joined, no trailing newline) sha256
    **`dbdba9ca7edd4c6532b1e88b556f6fadcb582dd14d5c50a78f05c5bf04a52514`**.
- **Structure input** to every comparator: `model_smiles`, the canonical RDKit SMILES of
  `muru.wur_v2.identity.parent_mol(smiles)`. MURU uses the PR #7 population `smiles` and `mh` exactly as in PR #7.
- **Prediction-time exclusion rule:** a compound is removed from the primary analysis only if a surviving primary
  comparator returns no spectrum, or a spectrum giving non-finite mu, at either rung. Such removals are counted and
  listed. They are determined from the prediction tables before the measured mu table is read. A compound with
  incomplete PR #7 measurement is also removed and counted (PR #7 reported 0 incomplete).

## 4. Energy mappings (model inputs)

| Model | NCE 20 input | NCE 60 input | Other fixed inputs |
|---|---|---|---|
| MURU-WUR-v2 | `E = (20 + 5.95552603907965) / 0.8618030610784555` | `E = (60 + 5.95552603907965) / 0.8618030610784555` | A0 map, unchanged from PR #7 |
| FIORA-OS v0.1.0 | `CE = 20` | `CE = 60` | `Precursor_type [M+H]+`, `Instrument_type HCD` |
| ICEBERG 2.1 primary | `20 * mh / 500` eV | `60 * mh / 500` eV | `ionization [M+H]+`, `instrument Orbitrap`, `precursor = mh` |
| GLACIER primary | `20 * mh / 500` eV | `60 * mh / 500` eV | `ionization [M+H]+`, `instrument Orbitrap` |
| ICEBERG 2.1 / GLACIER sensitivity (diagnostic only) | `20` | `60` | as primary |

- `mh` is the frozen theoretical [M+H]+ of each compound. Each value is written as `str([repr(float)])` in
  `collision_energies`.
- **Sensitivity scope:** the raw-NCE condition is the single predeclared sensitivity run. It reflects the convention
  found in much of the MassSpecGym MSnLib-derived training material. It never affects ranking, model inclusion,
  primary conclusions, or selection of an energy mapping.

## 5. Native inference pipelines (exactly as run)

**Input order:** population order (sorted keys), NCE 20 then NCE 60 per key, one spectrum per row, one invocation per
model and condition.

- **FIORA-OS v0.1.0:**
  `cd /opt/fiora_v0.1.2_patched && PYTHONPATH=/opt/fiora_v0.1.2_patched python scripts/fiora-predict -i in.csv -o out.mgf --model /opt/fiora_v0.1.2_patched/models/fiora_OS_v0.1.0.pt --annotation`
  (defaults: `--min_prob 0.001`, CPU; `--annotation` only adds peak labels).
- **ICEBERG 2.1:**
  `python seeded_run.py 42 src/ms_pred/iceberg/predict_smis.py --dataset-labels in.tsv --sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0 --gen-checkpoint .../gen/best.ckpt --inten-checkpoint .../inten_contr/best.ckpt --save-dir out --out-name preds.hdf5`
  (default `--batch-size 64`).
- **GLACIER:**
  `python seeded_run.py 42 src/ms_pred/glacier/predict_smis_joint.py --dataset-labels in.tsv --sparse-out --sparse-k 100 --num-cpu-workers 0 --checkpoint .../best.ckpt --save-dir out --out-name preds.hdf5`
  (default `--batch-size 64`, size-sorted batching).
- **Peak list read:** FIORA peaks are read from the MGF as written. ICEBERG and GLACIER masses and intensities are
  read as stored float32 from `preds.hdf5` by `container/mspred_h5_to_json.py` (the ms-pred `PredSpecDB` reader).
- **Upstream truncations kept:** the only thresholds and truncations are those upstream makes unavoidable at its own
  defaults. FIORA emits only peaks with probability > 0.001. ICEBERG and GLACIER assert `--sparse-out` and keep their
  top 100 peaks; ICEBERG also uses its DAG `max_nodes 100` and `threshold 0.0`.
- **Nothing added:** there is no denoising, peak insertion, extra top-k, extra intensity threshold, m/z window,
  rescaling, renormalization or merging.

## 6. Intensity scale and spectrum-to-mu transformation

- **FIORA-OS v0.1.0:** intensities as emitted by the patched CLI. The CLI applies the square once, inside
  `simulate_and_score`, because the checkpoint's `training_label` is `compiled_probsSQRT`. No further transform.
- **ICEBERG 2.1 and GLACIER:** `I = inten ** 2`, applied exactly once in `run_predictions.py`, to the stored float32
  intensities (evaluated in float64).
  - This inverts ms-pred's training target `sqrt(I / I_max)` (`process_spec_file`).
  - T3 verified that the native inference path applies no inverse: no square or power operation in `predict_smis.py`,
    `joint_model.py` or `predict_smis_joint.py` besides the collision-energy positional encoding; native outputs lie
    in (0, 1) with maxima 0.98 and 0.9986.
  - The global scale is irrelevant to mu.
- **All models:** `mu = muru.wur_v2.external_multims2.spectrum_mu(mz, I, mh)`, unchanged (git blob `fad997a`), over
  the full final peak list with the precursor included wherever the native output contains it.
- **Precursor emission verified in T3 (non-benchmark examples):**
  - FIORA-OS v0.1.0 emits the intact precursor at [M+H]+ in 20/20 example spectra.
  - ICEBERG 2.1 emits the root (intact-molecule) fragment at [M+H]+ in 20/20 primary spectra.
  - GLACIER emits it in 18/20 primary spectra. In the other 2 the intact-molecule detection ranked below the
    native top-100 cut. Adding a peak at [M+H]+ with the smallest retained intensity would move mu by at most 5.7e-4.
  - GLACIER therefore natively produces the precursor contribution, and its native peak list passes unchanged into
    `spectrum_mu`. No precursor peak is ever synthesized, inserted, estimated or assigned for any model.
  - The fraction of benchmark spectra containing a native [M+H]+ precursor peak is reported descriptively per model
    and condition.

## 7. Primary analysis (the only decisional analysis)

`scripts/comparator_benchmark/analysis.py`, using `muru.wur_v2.metrics` (git blob `f6955c7`) unchanged.

1. **Cells:** identical compounds and (compound, rung) cells for all four models: the frozen population minus the
   section 3 prediction-time exclusions.
2. **Measured values:** the PR #7 committed per-(compound, rung) medians,
   `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` (git blob `375d36e`), read only inside the one-look
   analysis.
3. **P1** = `metrics.p1`, the pooled two-rung RMSE, for MURU and for each comparator on those cells.
4. **Ratio** per comparator: `P1_MURU / P1_comparator`. Values below 1 favour MURU.
5. **Bootstrap:** `metrics.cluster_bootstrap(pred_MURU, pred_comparator, Y, scaffold_group, n=10000, seed=20260915)`.
   Replicate weights depend only on the seed and the number of scaffold groups, so every comparator shares the
   identical replicate matrix. Whole scaffold groups are resampled, and P1 of both arms is recomputed in each
   replicate.
6. **Intervals:** an ordinary 95% percentile interval for estimation, and a Bonferroni-adjusted interval at level
   `1 - 0.05/k` for decisions, where `k` = number of surviving primary comparators (**k = 3, 98.33%**; with k = 1 the
   95% interval is used).
7. **Decision per comparator, on the adjusted interval, applied literally:**
   - wholly below 1: **MURU superior** to that comparator;
   - wholly above 1: **comparator superior** to MURU;
   - otherwise: **no demonstrated difference**.
8. **Practical-effect descriptor**, reported separately and never replacing the inferential result: point ratio
   <= 0.95 (practically meaningful MURU advantage), >= 1/0.95 (practically meaningful comparator advantage), or in
   between.
9. **Reported with each primary contrast:** P1 of both arms, P1 difference with its 95% interval, the MRMSE
   difference interval, the AF difference interval (`metrics.cluster_bootstrap`), and per-model `metrics.summary`.
   These are descriptive.
10. **Ranking scope:** the primary result is the common-intersection result above. No pairwise-population result, no
    sensitivity result and no subgroup may be substituted for it.

## 8. Secondary and descriptive analyses (never decisional)

- NCE 20 and NCE 60 RMSE and mean signed residual per model (`metrics.per_rung`).
- PR #7 frozen structural-novelty quartile bins (`novelty_bins_per_compound.csv`, git blob `8cfa47f`): P1 per model
  within each bin of the scored population.
- The raw-NCE sensitivity for ICEBERG 2.1 and GLACIER: P1, ratio and 95% interval, labelled diagnostic.
- Counts: prediction-time exclusions, precursor-peak-emission fractions, per-model peak counts.

## 9. Order of operations and one-look rule

1. Commit this document with `artifacts/comparator_benchmark/freeze/freeze_manifest.json`, then create
   `refs/muru-freeze/muru-v2-comparator-benchmark-1.0` at that commit. `run_predictions.py` refuses to run without
   the ref and the frozen population hashes.
2. Run `scripts/comparator_benchmark/run_predictions.py` once. It writes native outputs, per-(key, NCE) mu tables
   and `prediction_manifest.json` with hashes. It reads no measured data.
3. Commit the prediction artifacts.
4. Run `analysis.py` once with `MURU_COMPARATOR_ONE_LOOK=1`. It refuses unless the freeze ref exists and the
   committed prediction manifest matches. Only then does it read `measured_mu.csv` and compute MURU's errors on this
   population.
5. Commit the result unchanged.
- **Failure handling:** if a technical failure stops prediction generation, it may be rerun with the identical frozen
  commands and inputs. A failure after the analysis has read measured values is reported, never retried with changed
  rules.
- **Already known before the freeze:** aggregate PR #7 results over 1,789 compounds (MURU P1 0.1296). No subset-level
  outcome information was obtained while building this protocol. This technical phase read no measured spectrum, mu
  value, peak array, MURU residual or MURU per-compound error.

## 10. Claim scope

On 1,327 MSnLib screening compounds (Orbitrap ID-X, HCD NCE 20 and 60) absent from the training releases of
FIORA-OS v0.1.0 (MSnLib v1.0) and of the MassSpecGym 1.5-trained ICEBERG 2.1 (`msg_simulation`) and GLACIER
checkpoints, the benchmark compares mu predicted from each comparator's native spectrum with MURU-WUR-v2's direct mu
prediction.

It does not assess:
- full-spectrum similarity;
- NIST-trained or other checkpoints;
- adducts other than [M+H]+;
- other instruments or energies;
- the current default FIORA.

## 11. Disclosed limitations

- MURU was fitted to measured spectra with a first mass near 40 m/z. Comparators may emit peaks below that, and the
  frozen endpoint applies no window.
- The ICEBERG and GLACIER MassSpecGym checkpoints saw MSnLib NCE values unconverted as eV in training. The primary
  mapping stays the documented eV conversion.
- The ICEBERG and GLACIER outputs depend weakly on batch composition. On the examples, batch size 1 vs 64 changed
  ICEBERG mu by at most 2.5e-4. The frozen input order fixes the batches.
- Both ms-pred intensity checkpoints are contrastive-finetuned, which is the only public form.
- Identity overlap is by InChIKey first block and library membership (feasibility audit section 10).
