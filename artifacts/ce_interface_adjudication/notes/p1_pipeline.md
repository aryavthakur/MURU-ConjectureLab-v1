# P1: ms-pred loader and preprocessing side of the CE interface

Study: MURU collision-energy interface adjudication (outcome-blind).
Scope: how the CE scalar that trained the frozen ICEBERG 2.1 `iceberg21_msg_simulation` (gen + inten_contr) and GLACIER `glacier_msg` checkpoints was produced, from MassSpecGym source to the float in `batch["collision_engs"]`.

Nothing in this note was learned from the closed comparator benchmark outcomes. No forbidden file was opened. No model was loaded or run; checkpoint pickles were only scanned for printable strings inside the zip (never unpickled).

Conventions: `MSPRED` = `/Users/aryav/muru-comparators/repos/ms-pred` at HEAD ed8311f. All `file:line` refer to that tree unless a commit is named. VERIFIED = read in code or computed from committed data. INFERRED = deduction from verified facts, not directly observed. UNRESOLVED = cannot be settled from available material.

Evidence script: `p1_pipeline_evidence.py` (reads only committed ms-pred data, the MSG 1.5 identity parquet, the t1 hparam extract, and checkpoint zip strings). Its JSON output is `p1/p1_evidence.json`. See "Delivery note" at the end about file locations.

---

## 0. Executive summary

1. No MSG training path in ms-pred converts CE. `nce_to_ev` / `ev_to_nce` are never called by the msg_simulation or GLACIER training pipelines (VERIFIED, call-site census in section 4). The model receives the MassSpecGym `collision_energy` number, reformatted and integer-rounded, fed raw into a sinusoidal embedding (no normalisation).
2. The CE float does NOT come from one place. For the ICEBERG generator and for GLACIER, the labels TSV CE column is explicitly dropped (`src/ms_pred/iceberg/dag_data.py:505`) and the CE comes from the MAGMa tree built from the `.ms` spectrum headers in `data/spec_datasets/msg/spec_files.hdf5` (not public). For the ICEBERG intensity model, the CE comes from `labels.tsv` via `predict_gen.py:146,199-203`.
3. The committed `data/spec_datasets/msg/labels.tsv` (added 2025-10-26, commit 648b061) has CE = floor(MSG CE) for 100% of 119,029 rows, while MassSpecGym1.5.tsv was uploaded to Hugging Face on 2026-05-07, after that commit. The frozen ICEBERG msg_simulation configs point at `data/spec_datasets/msg_simulation/labels.tsv`, which `create_msg_simulation_dataset.py` builds from MSG 1.5 with `f"{val:g}"` formatting, not at the committed file.
4. Checkpoint step arithmetic (VERIFIED numbers, INFERRED interpretation): gen and GLACIER both show exactly 3,098 optimizer steps per epoch (fits 99,105 to 99,136 training spectra at batch 32 on one GPU, i.e. the 99,341-row simulation-challenge train fold minus 205 to 236 drops). inten_contr shows exactly 1,378 steps per epoch (fits 88,129 to 88,192 spectra under the config's 2-GPU DDP, batch 32). If the base `msg` resources are keyed by int(CE) (the same truncation seen in the committed labels) and the msg_simulation labels come from MSG 1.5 via the script, exactly 11,163 train spectra have mismatched CE keys and are silently filtered out of intensity training, leaving 88,178, which lands inside the 1,378-step window. Without that drop the count would be 1,553 steps.
5. Therefore (INFERRED, strong): ICEBERG gen trained on CE = int(MSG CE) for about 99.1k spectra; ICEBERG inten trained on CE = round(MSG CE) only for the 88,178 spectra where round == int, so numerically also int(MSG CE). Neither checkpoint used `msg_all` or imputed energies. GLACIER's CE float = `float(header.split()[1])` from a legacy MAGMa JSON whose source spectrum headers are not public, so GLACIER's exact numeric CE source is UNRESOLVED beyond "the base msg spec files, not labels.tsv".
6. The numbers themselves are whatever MassSpecGym stores. Side observation for P2 (VERIFIED arithmetic): 23,926 of the 25,289 non-integer MSG 1.5 simulation CE values equal NCE x precursor_mz / 500 for an integer NCE (within 0.01), mostly Orbitrap. So the MSG `collision_energy` column is already a mixture that includes eV values computed with the same formula as `nce_to_ev`. ms-pred passes it through unchanged apart from rounding.

---

## 1. Which dataset each checkpoint trained on; warm starts

### 1.1 ICEBERG 2.1 msg_simulation gen

- Checkpoint pickle strings: `results/iceberg_msg_simulation/split_rnd1/ckpt/gen/best.ckpt` and `.../gen/last.ckpt` (VERIFIED, zip string scan of `/Users/aryav/muru-comparators/checkpoints/iceberg21_msg_simulation/gen/best.ckpt`, `archive/data.pkl`).
- That path is exactly what `configs/iceberg/msg_simulation/dag_train_msg_simulation.yaml` produces: `experiment_name: iceberg_msg_simulation` (line 1), `save-dir: [split_rnd1]` (45), and `train_gen.py` `--version` default `gen` (`src/ms_pred/iceberg/train_gen.py:62`) with logger dir `save_dir/ckpt/gen` (`train_gen.py:264`). VERIFIED.
- Config data: `dataset-name: [msg_simulation]` (18), `split-name: [split.tsv]` (19), `dataset-labels: [labels.tsv]` (20), `magma-folder: [magma_outputs]` (21). Hparams in the checkpoint (lr 0.000996, decay 0.7214, dropout 0.2, hidden 512, layers 6, pe_embed_k 14, embed_collision true) match lines 22-41 (VERIFIED against `artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl`).
- Data paths resolved by `train_gen.py:126-161`: labels `data/spec_datasets/msg_simulation/labels.tsv`, split `data/spec_datasets/msg_simulation/splits/split.tsv`, MAGMa `data/spec_datasets/msg_simulation/magma_outputs/magma_tree.hdf5`.
- `create_msg_simulation_dataset.py:446-451` symlinks `magma_outputs`, `spec_files.hdf5`, `spec_files`, `spec_files_w_eV` from `data/spec_datasets/msg` into `msg_simulation`. So the generator's MAGMa trees are the unfiltered base `msg` trees. VERIFIED.
- Warm start: none. `train_gen.py` only resumes its own `last.ckpt` (304-312) and loads `best` for testing (322). No pretrained/NIST weights. VERIFIED.

### 1.2 ICEBERG 2.1 msg_simulation inten_contr

- Pickle strings: `results/iceberg_msg_simulation/split_rnd1/ckpt/inten_contr/best.ckpt` (VERIFIED). Matches `configs/iceberg/msg_simulation/dag_inten_contr_finetune_msg_simulation.yaml` (experiment 1, save-dir 58) with `train_contr_inten.py:37` version default `inten_contr`.
- Config data: `dataset-name: [msg_simulation]` (21), `split.tsv` (22), `labels.tsv` (23), `magma-dag-folder: results/iceberg_msg_simulation/split_rnd1/preds_train_100_inten.hdf5` (59), `decoy-path` (60), `train-checkpoint: results/iceberg_msg_simulation/split_rnd1/ckpt/inten/best.ckpt` (61).
- Warm start: yes, from the msg_simulation non-contrastive intensity model (`train_contr_inten.py:329-337`), itself trained by `dag_inten_train_msg_simulation.yaml` (dataset msg_simulation, lines 19-21, 57). Not NIST. VERIFIED.
- Consistency check: the checkpoint hparams carry `learning_rate 0.000736` (the base inten config, `dag_inten_train_msg_simulation.yaml:23`) rather than the finetune config's 0.0005 (`...contr_finetune...yaml:25`). This is explained by `IntenGNN.load_from_checkpoint(train_checkpoint)` restoring the base hparams and only `sk_tau`, `contr_weight` being overwritten (`train_contr_inten.py:331-337`). VERIFIED code; consistent with the checkpoint.

### 1.3 GLACIER msg

- Pickle strings: `results/joint_train_msg/split_rnd1/version_5/best.ckpt` (VERIFIED). The experiment name `joint_train_msg` is the pre-2026-07-06 name; commit 35a5aa3 (2026-07-06) renamed it to `glacier_msg` in both `configs/glacier/joint_train_msg.yaml` and `joint_contr_finetune_msg.yaml`. Both train and contrastive finetune wrote under the same `results/joint_train_msg/split_rnd1/version_N`, so the stage cannot be read from the path.
- Config data at HEAD: `dataset-name: [msg]`, `split-name: [split.tsv]`, `dataset-labels: [labels.tsv]`, `magma-folder: [magma_outputs]` (`joint_train_msg.yaml:20-23`, `joint_contr_finetune_msg.yaml:20-23`). GLACIER trains on `msg`, NOT `msg_simulation`. VERIFIED.
- Labels file name history in the GLACIER msg configs (git log --follow -p, VERIFIED): `labels_withev.tsv` (04ba1a9, 2026-02-22, as `configs/iceberg_transformer/joint_train_msg.yaml`) -> `20250725_labels_spec_sim.tsv` (c792201, 2026-03-24) -> `labels.tsv` (470d118, 2026-05-28, rename to GLACIER). The checkpoint's `lr 0.0004` and `max_breakpoints 200` first appear in c792201. The Dropbox archive entry for `best.ckpt` is dated 2026-06-12 12:34:34 and the README link was added in 8e7923b (2026-06-14). So the checkpoint was trained with a config whose labels file was either `20250725_labels_spec_sim.tsv` or `labels.tsv` (INFERRED from dates; UNRESOLVED which).
- Checkpoint hparams `contr_threshold 0.5`, `contr_weight 1.0`, `contr_loss_fn entropy` are the `JointModel` defaults (`src/ms_pred/glacier/joint_model.py:55-57`), not the finetune config value 0.4 (`joint_contr_finetune_msg.yaml:66`). This fits either a base `train_joint.py` run (which never passes contr args) or a finetune that restored base hparams via `load_from_checkpoint` (`train_contr_joint.py:364-380`). Stage UNRESOLVED; irrelevant to CE because both stages use the same data path.
- MAGMa input: `data/spec_datasets/msg/magma_outputs/magma_tree_with_inten.hdf5` read as JSON (`train_joint.py:146-148`, `datatype="HDF5"` at 171/181/191; `train_contr_joint.py:176-178`, 208). Produced by `run_scripts/glacier/add_inten.sh:16-26` from `magma_tree_new.hdf5` with `--magma-output`. `magma_tree_new.hdf5` is the output name of the legacy JSON-writing `run_magma.py` at commit 3d08224 (2025-09-02, line 465). From 2026-03-20 (2efc62c) `run_magma.py` writes a PredSpecDB `magma_tree.hdf5` instead. VERIFIED.
- Warm start: base `train_joint.py` loads nothing except its own test checkpoint (318). The finetune loads a `joint_train_msg` base (`train_contr_joint.py:364-366`). No NIST weights in either path. VERIFIED.

### 1.4 Not msg_all, not imputed

- `msg_all` configs use datasets `msg_known_ce` and `msg_all_iceberg` and experiment names `iceberg_msg_known_ce` / `iceberg_msg_all_iceberg` (`configs/iceberg/msg_all/*.yaml`, line 1 and 13-21 of each). None matches the frozen pickle paths. VERIFIED.
- README labels the frozen archive as `msg_simulation` (`README.md:282`, commit c35bf82), matching the t1 source URL. VERIFIED.
- Step arithmetic (section 6) excludes the full MSG train fold (194,119 rows -> 6,067 steps at batch 32) for all three checkpoints. VERIFIED numbers.
- `msg_simulation/run_all.sh:6-9` states it "does not run collision-energy imputation". `create_msg_simulation_dataset.py:382-405` raises if any `[imputed]` literal or `collision_imputed` true is present. VERIFIED.

---

## 2. Provenance of the committed `data/spec_datasets/msg/labels.tsv`

- `git log --follow`: single commit 648b061, 2025-10-26 00:14:30 -0400, Mrunali Manjrekar, "massspecgym weights + retrieval metrics update (#30)". Never modified since. VERIFIED.
- No split files for msg are committed. `git ls-files` lists only `data/spec_datasets/msg/labels.tsv`; the only committed split files are under `nist20/splits` and `nist23/splits`. The task brief's "split files there" does not hold. VERIFIED.
- Content (VERIFIED, `p1_evidence.json`): 119,029 rows, 119,029 unique `spec`; columns `Unnamed: 0, dataset, spec, ionization, formula, smiles, inchikey, instrument, collision_energies, precursor`; all `[M+H]+`; Orbitrap 81,323 / QTOF 37,706; CE strings of the form `['30']`, 192 distinct, none containing `eV`, `imputed`, `nan`, `%`, `,` or `.`.
- Join with MSG 1.5 identity parquet on `spec == identifier`: all 119,029 match; spec set equals the MSG 1.5 `simulation_challenge == True` set exactly; inchikey, instrument and adduct agree 100%; `Unnamed: 0` equals the MSG 1.5 row position for 100% of rows. VERIFIED.
- CE: label CE == floor(MSG 1.5 CE) for 100% of rows; == MSG 1.5 CE for 78.76%; == round-half-even for 89.76%. MSG 1.5 simulation rows have 25,289 non-integer CE values (e.g. 32.5, 21.374848). VERIFIED.
- Timeline (VERIFIED from `git log` and Hugging Face API `datasets/roman-bushuiev/MassSpecGym/commits/main`):
  - 2024-08-20 `MassSpecGym.tsv` uploaded (v1).
  - 2025-09-02 3d08224 "MassSpecGym support"; configs use `labels_withev.tsv`, `labels_withev_validinst.tsv`, `spec_files_w_imputed_eV`.
  - 2025-10-26 648b061 adds committed `msg/labels.tsv` + `*_msg_spec.yaml` configs + first MSG weights (Dropbox d73o0o4...).
  - 2026-05-07 `MassSpecGym1.5.tsv` uploaded to Hugging Face.
  - 2026-06-14 8e7923b adds GLACIER MSG checkpoint link (ta99j0mp1...). Archive entry date 2026-06-12.
  - 2026-07-06 7b59014 adds `create_msg_simulation_dataset.py`, `msg_all` scripts.
  - 2026-07-08 14:38 11fd2ed adds `msg_simulation` configs/run scripts and the subformula filter.
  - 2026-07-08 23:02 c35bf82 "update link to MSG pretrained weights" adds the `msg_simulation` Dropbox link (mcj0ngdvuj2...). Archive entries dated 2026-07-09 02:47:16 (zip timestamps; timezone not recorded, plausibly UTC = 22:47 EDT, 15 minutes before the commit; INFERRED).
  - 2026-09-03 ed8311f "clarify glacier model weight link" (README only).
- The committed labels predate MSG 1.5, so they cannot have been generated from `MassSpecGym1.5.tsv`; they were presumably built from `MassSpecGym.tsv` v1 with int() truncation (INFERRED; v1 CE values were not fetched because v1 is outside the authorised download scope). The fact that MSG 1.5 floors to them exactly and shares row order suggests v1 and v1.5 carry the same CE values for these rows (INFERRED, UNRESOLVED without v1).
- `create_msg_simulation_dataset.py` cannot reproduce the committed file: it writes `f"{val:g}"` for non-integers (`:74-77`, e.g. `['32.5']`, `['21.3748']`), adds `collision_imputed` (`:130`), omits `Unnamed: 0`, and uses `index=False` (`:199`). VERIFIED by running the function on probes.
- README expectation "119,029 unique simulation-challenge spectra and zero imputed labels" (`README.md:183-185`) matches the MSG 1.5 simulation count (119,029, 0 NaN CE). VERIFIED.
- Can the committed labels be the ones used to train the frozen weights?
  - ICEBERG msg_simulation: not directly. The configs read `msg_simulation/labels.tsv`, and README's command uses `--force-output --overwrite` (`README.md:155-162`), which rewrites it from MSG 1.5 even though the spec set equals the committed one (the `same_spec_set` short-circuit at `create_msg_simulation_dataset.py:437` is bypassed by `--force-output`). The inten_contr step count (section 6) is consistent with script-generated labels and inconsistent with a floor-formatted copy (which would give 1,553 steps, not 1,378). INFERRED.
  - The base `msg` resources (spec_files.hdf5, magma_outputs, subformulae) that msg_simulation symlinks or filters are, on the same arithmetic, keyed by int(CE), i.e. produced by the same truncation as the committed labels. INFERRED.
  - GLACIER: reads `data/spec_datasets/msg/<labels>`. The committed labels are a plausible match (same 119,029 spec set; step count fits the simulation train fold), but GLACIER never uses the labels CE column (section 3.4). UNRESOLVED whether the file was byte-identical.

---

## 3. CE transformations, stage by stage

### 3.1 MSG 1.5 -> msg_simulation labels (`data_scripts/create_msg_simulation_dataset.py`)

- Source: `DEFAULT_SOURCE_TABLE` = HF `MassSpecGym1.5.tsv` (`:25-28`). Columns read include `collision_energy`, `precursor_mz`, `instrument_type`, `fold`, `simulation_challenge` (`:98-109`).
- Filter `simulation_challenge` truthy (`:112`, `truthy` at `:63-64`).
- `format_collision_energy` (`:67-80`): `float(value)`; None/NaN -> None; integer -> `str(int(val))`; else `f"{val:g}"` (6 significant digits); the `"[imputed]" in label` test (`:78`) is dead code because `label` comes from a float; returns `"['<label>']"`. No unit, no conversion.
- Rows with None dropped (`:115`); `[imputed]` regex filter (`:116`) also dead for numeric input. For MSG 1.5 simulation rows this drops 0 (0 NaN CE). VERIFIED.
- Output columns: `collision_energies`, `precursor` = MSG `precursor_mz`, `instrument` = MSG `instrument_type`, `collision_imputed` False (`:118-133`). Split `name`/`split` from `fold` (`:134-141`, `normalize_fold` `:83-89`: anything not train/val becomes test).
- Dedup on spec keep-first (`:423-424`).
- Resources: symlinks `magma_outputs`, `spec_files.hdf5`, `spec_files`, `spec_files_w_eV` from msg (`:446-451`). Contradiction: README says it links `subformulae` too (`README.md:167-169`), but since 11fd2ed the code instead FILTERS subformulae (`:453-458`).
- `filter_subformulae` (`:236-276`): builds `(spec, collision_key)` pairs from labels (`iter_label_collision_pairs` `:209-222`, `collision_key` = `f"{float(value):.0f}"` `:202-206`); keeps only source `no_subform.hdf5` keys matching regex `(.+)_collision\s+([0-9]+\.?[0-9]*|nan)\.json$` (`:225-233`) whose rounded CE is in the label pairs. Consequences (VERIFIED code): a key with any suffix such as ` eV` or ` eV [imputed]` before `.json` is `skipped_unparsed`; a key whose CE differs after rounding from the label is `skipped_not_in_labels`. This silently removes spectra from intensity training (3.3).
- Replication on MSG 1.5 (VERIFIED, evidence JSON): the label key equals round-half-even(MSG CE) for every row; it differs from floor(MSG CE) for 11,163 train, 486 val, 542 test rows.

### 3.2 Spectrum HDF5 -> MAGMa trees (generator and GLACIER CE source)

Current code (`src/ms_pred/magma/run_magma.py`, used for PredSpecDB `magma_tree.hdf5`):
- Reads `.ms` text from `spec_files.hdf5` (`:171-173`), `common.parse_spectra`.
- `parse_spectra` (`src/ms_pred/common/misc_utils.py:1899-1963`): each `>` header line after the first group becomes `MassSpec(spectra_header, ...)` (`:1929,1938`).
- `MassSpec.__init__` (`misc_utils.py:57-61`): if the string contains `collision`, `chem_utils.get_collision_energy` extracts it; then ALWAYS `self.collision_energy = float(f'{float(ce):.0f}')`. So every CE stored in a MassSpec is an integer-valued float, rounded with Python's format rounding (half-to-even on the binary value: 27.5 -> 28, 28.5 -> 28, 32.5 -> 32, 27.75 -> 28). VERIFIED by probe.
- `get_collision_energy` (`src/ms_pred/common/chem_utils.py:740-755`): regex `collision +([0-9]+\.?[0-9]*|nan).*`, then `f"{float(x):.0f}"`; fallback regex on bare numbers; else `'nan'`. Probed (VERIFIED): `collision 30 eV` -> 30, `collision 30 eV [imputed]` -> 30, `collision 30%` -> 30, `collision NCE 30` -> 30 (fallback), `collision 20,30,40` -> 20 (first of a stepped list, rest discarded), `collision nan` -> nan, `collision -5` -> 5 (sign lost), `collision 1.5e1` -> 2 (exponent lost), `collision` -> nan. Units and `[imputed]` tags are silently discarded.
- `CompositeMassSpec` merges spectra whose rounded CE key collides by summing peaks (`misc_utils.py:735-763`; key `_standardize_ce` `:780-784`).
- MAGMa runs unmerged only (`run_magma.py:494`, `merge_specs` False), writes `MassSpec(collision_energy=colli_eng, ...)` per rounded CE key (`:428-429`) into PredSpecDB (`:503-521`), stored under `name/collision {ce:.0f}` (`misc_utils.py:1466-1470`).

Legacy code that produced GLACIER's `magma_tree_new.hdf5` (commit 3d08224, `src/ms_pred/magma/run_magma.py`):
- Old `parse_spectra` returned raw `(header, array)` tuples (3d08224 `misc_utils.py:194-254`); `process_spec_file(meta, spectras, merge_specs=False)` keyed by the raw header string (`run_magma.py:179`).
- Tree file name `f"{spec_name_clean}_{colli_eng}.json"` (`:188`) and JSON field `"collision_energy": float(colli_eng.split()[1])` (`:400`): the second whitespace token of the raw header, NOT rounded. A header `collision 30 eV` gives 30.0; `collision 32.5` gives 32.5.

What the `msg/spec_files.hdf5` headers contain is not observable (not public; Dropbox listing not retrievable; issue #29 says the 2025 Dropbox had only retrieval candidates and weights). 2025-era names `spec_files_w_imputed_eV` (b776c64, 3d08224 `data_scripts/dag/run_magma.sh`), `spec_files_w_eV` (`create_msg_simulation_dataset.py:446`), `labels_withev.tsv`, and retrieval keys `"{spec}_collision {x} eV.json"` / `"... eV [imputed].json"` (`src/ms_pred/retrieval/retrieval_benchmark_msg.py:74-76`) show that eV-tagged, imputed MSG spectrum files existed in the authors' environment. Which variant fed which frozen checkpoint is UNRESOLVED from code alone; section 6 constrains the ICEBERG case.

### 3.3 Subformula assignment (intensity targets)

`data_scripts/forms/01_assign_subformulae.py`:
- `--collision-source` default `raw` (`:59-67`). With `raw`, keys are `f'{spec_name}_collision {colli_eng}'` where `colli_eng` iterates `CompositeMassSpec.items()`, i.e. the rounded header CE (`:434-442`, `process_spec_file` `:353-374`). Written as `<key>.json` (`:469-471`).
- With `labels` (used only by `msg_all` step 06, `run_scripts/iceberg/msg_all/06_assign_subformulae_msg_all_iceberg.sh:16-22`): `parse_label_collision_energies` (`:105-132`: `ast.literal_eval`, strips to first whitespace token, `nan`/`none`/`null`/empty -> NaN), `format_collision_energy` `.0f` (`:135-139`), `find_matching_raw_spec` (`:142-166`: single raw spectrum is used regardless of CE; otherwise match on rounded CE; else positional fallback).
- `data_scripts/all_assign_subform.sh` is hard-coded to `dataset=nist20` (`:1`); `data_scripts/dag/run_magma.sh:21-31` builds `no_subform.hdf5` with default `raw` source.
- Contradiction in history: 3d08224's `run_magma.sh` passed `--spectra-dir .../spec_files_w_imputed_eV` to `01_assign_subformulae.py`, which at that commit had no `--spectra-dir` argument (3d08224 `01_assign_subformulae.py:20-86`) and read `data_dir/"spec_files.hdf5"` (`:275`). The committed script could not have run as written; the committed scripts are not a faithful execution record.

### 3.4 Dataset classes: where the float is made

ICEBERG (`src/ms_pred/iceberg/dag_data.py`):
- `DAGDataset.__init__` (`:485-536`): instrument missing -> `Orbitrap` (`:486-487`); rows kept only if the spec has a MAGMa entry and its instrument is in `instrument2onehot_pos` (`:498`; map `chem_utils.py:277-283`: Orbitrap, QTOF, IT-FT, Unknown). **The labels CE column is dropped**: `self.df_sub.set_index("spec").drop("collision_energies", axis=1)` (`:505`). One dataset item per MAGMa map key `spec_collision <ce>` (`:508-512`), so every CE present in the tree file for a labelled spec is used, whatever labels.tsv says.
- `TreeProcessor._process_tree` (`:309-310`): `out_dict["collision_energy"] = tree["collision_energy"]` (for a `MassSpec`, `__contains__`/`__getitem__` are `hasattr`/`getattr`, `misc_utils.py:475-482`).
- Collate: `collision_engs = torch.FloatTensor([float(j["collision_energy"]) ...])` (GenDataset `:650-651`; IntenDataset `:774-775`). This is the float handed to the model.
- GenDataset `load_tree` (`:676-687`) reads PredSpecDB or legacy JSON; `train_gen.py:29-47` builds the map from `magma_tree.hdf5` (`name_to_entry[f"{name}_collision {ce}"]`).
- IntenDataset/IntenContrDataset `load_tree` read `preds_train_100_inten.hdf5` (PredSpecDB) (`:806-811`, `:929-934`); maps built in `train_inten.py:144-150`, `train_contr_inten.py:150-156`.
- IntenContrDataset decoys get `collision_energy = common.get_collision_energy(name)` (a rounded string, cast by collate) (`:892`, `:919`).
- Missing CE: string `nan` -> float NaN; the model replaces NaN embeddings with a zero vector (`gen_model.py:289-290`, `inten_model.py:503-504`).

ICEBERG intensity training data chain (msg_simulation):
1. `predict_gen.py` with `dataset-name msg_simulation`, `threshold 0`, `max-nodes 100` (`configs/iceberg/msg_simulation/dag_gen_predict_train_msg_simulation_decoy0.yaml:13-19`): CE list from `ast.literal_eval(entry["collision_energies"])` (`predict_gen.py:146`), `collision_energy_to_float` (`chem_utils.py:780-784`: first whitespace token -> float; `'20,30'` and `'30%'` raise ValueError) (`predict_gen.py:199-203`), stored as `MassSpec(collision_energy=...)` (`:262-274`) -> rounded `.0f`. Instrument NaN or unknown -> Orbitrap (`:64-67`, `:144-145`).
2. `add_dag_intens.py` (`run_scripts/iceberg/msg_simulation/02_run_dag_gen_predict_msg_simulation.sh:7-11`): iterates the FILTERED `msg_simulation/subformulae/no_subform.hdf5` names; CE from the name (`add_dag_intens.py:126-135`); reads the predicted DAG at that CE (`:63-65`, PredSpecDB `read` -> `h5_obj[name]`, a missing CE key raises KeyError, `misc_utils.py:1789-1792`); attaches raw spectrum; writes under `spec_id` with the predicted DAG's CE (`:152-156`).
3. So the inten model's CE float = round(label CE) = round-half-even(MSG 1.5 CE), and only for spectra whose filtered subformula key survived.

GLACIER (`src/ms_pred/glacier/dataset.py`):
- Uses the ICEBERG `DAGDataset` (`:26`), so the labels CE column is dropped the same way.
- `TreeProcessor.featurize_tree` (`:150`): `"collision_energy": float(tree["collision_energy"]) if "collision_energy" in tree else 0.0`. The JSON tree's CE (legacy: unrounded second header token) is used; **a tree lacking the key becomes 0.0, not NaN**, so it would get the sin/cos embedding of 0 eV rather than the zero "unknown" vector (`joint_model.py:277-278`). Code identical at c792201 (`:142`), 13ce056 (`:153`), 470d118 (`:149`). VERIFIED.
- Collate `collision_engs = torch.FloatTensor([float(item["collision_energy"]) ...])` (`:589`).
- IntenContrDataset decoys: `colli_eng = common.get_collision_energy(name)` (`:836`), passed as CE for decoy entries (`:857-861`).

Model side (for completeness, VERIFIED): the float is used raw in `sin(ce / d_k)`, `cos(ce / d_k)` with `d_k = 10000^(2k/64)` (`COLLISION_PE_DIM 64`, `COLLISION_PE_SCALAR 10000`, `chem_utils.py:118-119`; `gen_model.py:141-160, 283-295`; `inten_model.py:132-151, 497-510`; `joint_model.py:138-147, 270-284`). No mean/std normalisation (the `NIST_COLLISION_ENERGY_MEAN/STD` constants at `misc_utils.py:30-31` are used only by MassFormer, `massformer_data.py:68-69,190-191`). Code comments describe the domain as "0 - 100 eV" (`gen_model.py:149`, `inten_model.py:140`).

### 3.5 msg_all imputation (not used by frozen checkpoints)

- `04_impute_missing_collision_energies.py`: selects rows with missing CE (`:149-151,174-175`); NCE grid `range(5, 151, 5)` (`:54`), contradicting its own docstring "5..100 NCE grid" (`:6`); converts each NCE to eV with `int(common.nce_to_ev(int(nce), precursor_mz))` (`:160-166`), i.e. truncation of NCE x precursor / 500; predicts with the `msg_known_ce` ICEBERG at those eV values (`:207-210`, `:258-274`); stores `best_collision_energy` (eV int) and `best_nce` (`:368-372`).
- `05_build_msg_all_iceberg_dataset.py`: fills missing labels with `str([f"{float(ev):.0f}"])` (`:105-106,144-151`); known CEs untouched; symlinks `spec_files.hdf5`, `splits`, `magma_outputs` from `msg_all` (`:222-223`). So `msg_all_iceberg` generator trees keep raw-spectrum CE keys while intensity subformulae use label CEs (06 with `--collision-source labels`).
- This is the one place where upstream authors explicitly treat the model's CE input as eV for MSG, and treat known MSG CE labels as directly comparable to eV. It is not on the path of any frozen checkpoint (section 1.4).

---

## 4. `nce_to_ev` / `ev_to_nce` call-site census (VERIFIED by grep over the whole tree)

Definitions: `misc_utils.py:2542-2565` (`ev = nce * precursor_mz / 500`, type-preserving, int -> `int(round(ev))`), `:2568-2570`; methods `MassSpec.nce_to_ev` `:580-585`, `CompositeMassSpec.nce_to_ev` `:824-830`.

Call sites:
- `run_scripts/iceberg/msg_all/04_impute_missing_collision_energies.py:163` (msg_all imputation grid).
- `run_scripts/iceberg_atlas/01_generate_task_tsv.py:35` (atlas generation over NCE list).
- `src/ms_pred/iceberg/iceberg_elucidation.py:302, 439` (only when `nce=True`; docstring `:201` "otherwise, they are treated as absolute eV").
- `src/ms_pred/iceberg/iceberg_extract_fragments.py:60` (plotting/extraction utility).
- `src/ms_pred/graff_ms/graff_ms_data.py:238, 338` (`ev_to_nce`, GrAFF-MS baseline only).
- `webui/app.py:244, 2414, 2714, 2752, 3110` (user NCE -> eV; `:2412` "Assume the labels are NCE").
- `tests/test_misc_utils.py:49-59`; notebooks `sirius_eval_msnlib.ipynb`, `iceberg_fig_visual_msms.ipynb`.

None in: `create_msg_simulation_dataset.py`, `run_magma.py`, `01_assign_subformulae.py`, `add_dag_intens.py`, `train_gen.py`, `predict_gen.py`, `train_inten.py`, `train_contr_inten.py`, `dag_data.py`, `glacier/dataset.py`, `glacier/train_joint.py`, `glacier/train_contr_joint.py`, or the models. No MSG training path calls `nce_to_ev`. The authors' own inference tooling (webui, atlas, elucidation) treats the model CE as eV and converts user NCE with `/500`.

---

## 5. Does the stored value match the field name?

- Field `collision_energies` (labels) / `collision_energy` (MassSpec, JSON) / `collision_engs` (batch) has no unit in the data. For msg_simulation it holds the MassSpecGym `collision_energy` number, reformatted (`:g`) and rounded to an integer; nothing converts NCE to eV or back (sections 3-4). VERIFIED.
- The upstream convention elsewhere is eV (section 4). So the implied unit is eV, but the MSG values are passed through as-is. Whether they are eV depends entirely on MassSpecGym's own column semantics.
- Observation for P2 (VERIFIED arithmetic on committed `precursor` and MSG 1.5 CE): among 25,289 non-integer simulation CE values, 23,926 (94.6%) satisfy CE x 500 / precursor within 0.01 of an integer, with modes 25, 60, 30, 90, 45, 75, 35, 15 (Orbitrap 23,928 of the non-integer rows, QTOF 1,361); only 2.2% of integer-CE rows do. 704 non-integer values are quarter/half values (e.g. 32.5 x 463). So part of the MSG column already equals `nce_to_ev(NCE, precursor_mz)` for integer NCE; the integer rows' unit cannot be determined here.
- Truncation/rounding loses up to 1 unit (floor) or 0.5 (round) of that value; for the ICEBERG inten model the 11,163 train spectra with fractional part above 0.5 (or exactly .5 with odd integer part) are the ones dropped (section 6).

---

## 6. Checkpoint step arithmetic (VERIFIED numbers; interpretation INFERRED)

Inputs: `epoch`, `global_step` from t1 extract; PyTorch Lightning 1.6.5 counts optimizer steps; `accumulate_grad_batches` 1; batch sizes and GPU counts from configs.

| checkpoint | epoch (0-based) | global_step | steps/epoch | config batch, devices | implied training items |
|---|---|---|---|---|---|
| iceberg gen | 16 | 52,666 | 3,098.0 | 32, 1 GPU (`train_gen.py:295` devices=1) | 99,105 to 99,136 |
| iceberg inten_contr | 5 | 8,268 | 1,378.0 | 32, DDP over `torch.cuda.device_count()` (`train_contr_inten.py:318-319`), config `visible_devices [0,1]`, `gpus l40s:2` | 88,129 to 88,192 (2 GPUs) |
| glacier | 23 | 74,352 | 3,098.0 | 32 on 1 GPU (`joint_train_msg.yaml:5,16`) or 16 x 2 GPUs (finetune) | 99,105 to 99,136 either way |

Reference counts from MSG 1.5 (VERIFIED): simulation train fold 99,341 (3,105 steps); all-MSG train fold 194,119 (6,067); known-CE train fold 101,609 (3,176).

Interpretation:
- gen and GLACIER: consistent with the simulation train fold minus 205 to 236 spectra (plausibly MAGMa fragmentation failures or empty spectra, `run_magma.py:182-205`). Excludes msg_all. A known-CE msg_known_ce run would need 2,473 or more drops. INFERRED.
- inten_contr: 99,341 - 11,163 = 88,178 lies in the 64-wide window 88,129 to 88,192; with no CE-key drop the step count would be 1,553; single-GPU would give 2,756. This is the predicted count if (a) msg_simulation labels came from MSG 1.5 via `create_msg_simulation_dataset.py` (label keys = round-half-even) and (b) the base `msg/subformulae/no_subform.hdf5` keys (from `spec_files.hdf5` headers) equal int(MSG CE), so `filter_subformulae` discards exactly the rows where round != floor, and at most 49 other spectra were lost. INFERRED, strong (a random coincidence needs to hit a 64-item window).
- Corollary: the base msg spectrum headers were integer-truncated CE values with no ` eV` suffix in the subformula keys (a suffix would make every key `skipped_unparsed`, leaving no intensity data). INFERRED.
- Corollary: for the ICEBERG generator, CE float = int(MSG CE) for all ~99.1k train spectra (including the 11,163 whose true value rounds up). For the ICEBERG intensity model, CE float = round(MSG CE) = int(MSG CE) on the retained 88,178. For GLACIER, the same count argument shows no CE-key-induced loss (its `add_dag_intens --magma-output` matches pred and true trees by identical stems, `add_dag_intens.py:94-117`), but does not identify whether its legacy JSON headers were the same integer-truncated files or an eV-tagged variant. GLACIER numeric CE source: UNRESOLVED.

---

## 7. Contradictions and caveats (not smoothed over)

1. Brief says msg split files are committed; only `labels.tsv` is (section 2).
2. README says msg_simulation creation "links ... subformulae" (`README.md:167-169`); code filters them (`create_msg_simulation_dataset.py:446-458`).
3. `04_impute...py` docstring "5..100 NCE grid" (`:6`) vs `range(5, 151, 5)` (`:54`).
4. `format_collision_energy`'s `[imputed]` guard is unreachable (`create_msg_simulation_dataset.py:78`).
5. 3d08224 `run_magma.sh` passes an argument the subformula script did not accept (section 3.3).
6. Same spectrum, two CE code paths: generator CE from spectrum headers, intensity CE from labels; they agree only after rounding and the disagreement silently removes 11.2% of train spectra from intensity training (INFERRED magnitude).
7. GLACIER missing CE -> 0.0 (`glacier/dataset.py:150`) vs ICEBERG missing CE -> NaN -> zero embedding.
8. `get_collision_energy` discards sign, exponent, units, `%`, `[imputed]`, and all but the first stepped value (probe results, section 3.2).
9. Committed labels floor (int) CE; MassSpec objects round half-to-even; `create_msg_simulation_dataset` keys round; three different integerisations coexist.
10. Code at HEAD for all CE-relevant files is unchanged between 11fd2ed and ed8311f (`git diff --stat` empty for the files listed in section 3), but training may have run on uncommitted or earlier code; the msg_simulation checkpoints were published 15 minutes after the configs' sibling commit and 2 days after the scripts were added. UNRESOLVED whether training used exactly the committed scripts.
11. GLACIER stage (base vs contrastive finetune) and exact labels file UNRESOLVED; CE path identical for both.

---

## 8. Open items for other lanes

- P2 (source semantics): MSG 1.5 CE is mixed; 94.6% of non-integer simulation values are NCE x precursor / 500. Unit of the 93,740 integer rows by instrument and source is the real question; ms-pred adds no conversion on top.
- Deployment implication (for the adjudication, not decided here): to reproduce training conditions, the ICEBERG msg_simulation checkpoints expect the MassSpecGym-style number, integer-truncated/rounded, with no `/500` conversion applied by ms-pred. Whether a documented eV mapping (NCE x precursor_mz / 500) matches depends on how MassSpecGym encoded each source, which is outside P1.

## Delivery note

The session harness refused writes to the `muru-ce-interface-adjudication` worktree from this session ("belongs to a different worktree. Do not write to other worktrees' files from this session"), so this note, the script and the evidence JSON were written to the session scratchpad instead:
- `.../scratchpad/ce_interface_adjudication/artifacts/notes/p1_pipeline.md` (this file)
- `.../scratchpad/ce_interface_adjudication/scripts/p1_pipeline_evidence.py`
- `.../scratchpad/ce_interface_adjudication/artifacts/p1/p1_evidence.json`
They are intended to be copied to `artifacts/ce_interface_adjudication/notes/p1_pipeline.md`, `scripts/ce_interface_adjudication/p1_pipeline_evidence.py`, and `artifacts/ce_interface_adjudication/p1/p1_evidence.json`. No files were downloaded (nothing appended to `downloads_register.jsonl`); only the Hugging Face commits API JSON and GitHub issue API JSON were read in-memory.
