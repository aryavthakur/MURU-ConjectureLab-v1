# Task V: CODE-TRACE lens

Independent re-trace of the load-bearing provenance claims (P1, P2, P3, Q) in ms-pred
source and in the MassSpecGym dataset-construction notebooks. Method: read the code,
try to refute each claim, and default to refuted when the cited evidence does not
actually show what the claim says.

Scope of this pass: (a) which dataset each frozen checkpoint trained on, (b) every
point where a collision energy (CE) is parsed, converted, rounded or imputed, (c) how
the three models embed the CE float. Numeric claims were recomputed from local data.
No model was run. No forbidden file was opened.

Repositories and revisions used:

- ms-pred clone `/Users/aryav/muru-comparators/repos/ms-pred`, HEAD `ed8311f22958cb37f055b663b5f56c5c77a2ee33` (2026-09-04), clean tree.
- Frozen checkpoints `/Users/aryav/muru-comparators/checkpoints/{iceberg21_msg_simulation/{gen,inten_contr},glacier_msg}/best.ckpt`.
- Frozen hyperparameters `artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl`.
- MassSpecGym construction notebooks 1 to 7 at commit `f259fe3`, fetched this session with `gh api` and recorded in `downloads_register.jsonl` (7 lines, phase `v_code`).
- Local data: `/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv` and `artifacts/ce_interface_adjudication/massspecgym15_identity_metadata_joined.parquet`.

Headline: nothing in the provenance set was refuted. Two claims are upgraded from
INFERRED to VERIFIED, one inference gains a second and independent derivation, one
stated justification is replaced by a stronger one, and one attempted narrowing of the
GLACIER question FAILED for a dated reason that makes the open question sharper rather
than smaller. Eight new issues are recorded at the end.

---

## 1. Which dataset each checkpoint trained on

### 1.1 Checkpoint self-identification (re-derived, not taken from P1)

I scanned `archive/data.pkl` inside each checkpoint zip for printable ASCII runs. The
file was never unpickled and no tensor was loaded into torch.

| checkpoint | strings found |
|---|---|
| gen | `results/iceberg_msg_simulation/split_rnd1/ckpt/gen/best.ckpt`, `.../last.ckpt`, `iceberg_msg_simulation`, `split_rnd1`, `ckpt` |
| inten_contr | `results/iceberg_msg_simulation/split_rnd1/ckpt/inten_contr/best.ckpt`, `.../last.ckpt` |
| glacier | `results/joint_train_msg/split_rnd1/version_5/best.ckpt`, `results/joint_train_msg/split_rnd1/version_5` |

VERIFIED, reproducing P1 C5 exactly.

The directory shapes are diagnostic. `train_gen.py:264` builds
`TensorBoardLogger(Path(save_dir)/"ckpt", name="", version=kwargs["version"])` with
`--version` defaulting to `gen` (`train_gen.py:62`), which is why the ICEBERG paths
carry `ckpt/gen` and `ckpt/inten_contr`. Both `glacier/train_joint.py:278` and
`glacier/train_contr_joint.py:337` instead use `TensorBoardLogger(save_dir, name="")`,
producing `save_dir/version_N`. So the GLACIER path form is consistent with EITHER the
base joint training OR the contrastive finetune. See section 5.

### 1.2 ICEBERG 2.1: `msg_simulation`

`configs/iceberg/msg_simulation/dag_train_msg_simulation.yaml` (experiment
`iceberg_msg_simulation`, `dataset-name: [msg_simulation]`, `magma-folder:
[magma_outputs]`, `learning-rate: [0.000996]`) and
`dag_inten_contr_finetune_msg_simulation.yaml` (same experiment,
`magma-dag-folder: results/iceberg_msg_simulation/split_rnd1/preds_train_100_inten.hdf5`,
`train-checkpoint: results/iceberg_msg_simulation/split_rnd1/ckpt/inten/best.ckpt`).

The gen checkpoint's stored `learning_rate` is 0.000996, matching the gen config
exactly. The inten_contr checkpoint's stored `learning_rate` is 0.000736, which is the
BASE intensity config's value (`dag_inten_train_msg_simulation.yaml`,
`learning-rate: [0.000736]`) and NOT the contrastive config's 0.0005. That is what
`IntenGNN.load_from_checkpoint(train_checkpoint)` at `train_contr_inten.py:331` does:
it restores the base model's saved hparams. P1 C6 VERIFIED.

No external or NIST warm start: `train_gen.py:304-322` only resumes its own
`last.ckpt`; the only `load_from_checkpoint` in the ICEBERG training path is the
msg_simulation base intensity model. VERIFIED.

### 1.3 GLACIER: dataset `msg`

`configs/glacier/joint_train_msg.yaml` at HEAD: `dataset-name: [msg]`,
`dataset-labels: [labels.tsv]`, `magma-folder: [magma_outputs]`, `batch-size: [32]`,
`learning-rate: [0.0004]`, `max-breakpoints: [200]`, `min-epochs: [20]`,
`max-epochs: [200]`. The checkpoint's stored hparams include `lr: 0.0004` and
`max_breakpoints: 200`. `glacier/train_joint.py:146-148` reads
`data/spec_datasets/msg/magma_outputs/magma_tree_with_inten.hdf5` through
`common.HDF5Dataset` (the legacy JSON container), not `magma_tree.hdf5`.
`run_scripts/glacier/add_inten.sh:16-26` builds that file for `dataset="msg"` from
`magma_outputs/magma_tree_new.hdf5` (predicted side) plus
`subformulae/no_subform.hdf5` (true side) with `--magma-output`. P1 C7 VERIFIED at
HEAD.

Config history for the GLACIER MSG training config (traced through two renames with
`git log --follow --name-status`):

| commit | date | path | experiment_name | dataset-labels | batch | devices |
|---|---|---|---|---|---|---|
| 04ba1a9 | 2026-02-22 | configs/iceberg_transformer/joint_train_msg.yaml | joint_train_**nist20** | `labels_withev.tsv` | 32 | [1] |
| c792201 | 2026-03-24 | same | **joint_train_msg** | `20250725_labels_spec_sim.tsv` | 16 | [0,1] |
| 13ce056 | 2026-05-06 | same | joint_train_msg | `20250725_labels_spec_sim.tsv` | 16 | [0,1] |
| 470d118 | 2026-05-28 | configs/GLACIER/joint_train_msg.yaml | joint_train_msg | `labels.tsv` | 32 | [2] |
| 35a5aa3 | 2026-07-06 | configs/glacier/joint_train_msg.yaml | **glacier_msg** | `labels.tsv` | 32 | [0] |

This gives an independent and stronger version of P1 C8. The checkpoint's internal
path contains `results/joint_train_msg/`, and `joint_train_msg` is the experiment name
ONLY between c792201 (2026-03-24) and 35a5aa3 (2026-07-06). At 04ba1a9, the era of
`labels_withev.tsv`, the experiment name was still the copy-paste artifact
`joint_train_nist20`. The `labels_withev.tsv` era is therefore excluded by the
checkpoint string alone, without needing the lr/max_breakpoints argument. The labels
file is `20250725_labels_spec_sim.tsv` or `labels.tsv`. P1 C8 NOT REFUTED and
strengthened.

### 1.4 `msg_all` is not any frozen checkpoint's dataset

`configs/iceberg/msg_all/*.yaml` use `dataset-name: [msg_known_ce]` and
`[msg_all_iceberg]` with experiment names `iceberg_msg_known_ce` and
`iceberg_msg_all_iceberg`. Neither matches any checkpoint string in section 1.1.
P1 C19's exclusion VERIFIED.

---

## 2. Where CE is parsed, converted, rounded or imputed

### 2.1 No NCE-to-eV conversion anywhere in the MSG training path

Repo-wide grep for `nce_to_ev|ev_to_nce` (excluding `.git`) returns exactly these
sites: `tests/test_misc_utils.py:8,11,50,51,56-59`;
`run_scripts/iceberg/msg_all/04_impute_missing_collision_energies.py:161-166,194,207-210,367-372`;
`run_scripts/iceberg_atlas/01_generate_task_tsv.py:35`; `webui/app.py:227,244,2414,2714,2752,3110`;
`notebooks/iceberg_2025_biorxiv/sirius_eval_msnlib.ipynb:2315`;
`notebooks/iceberg_2025_biorxiv/iceberg_fig_visual_msms.ipynb:536,540,551`;
`src/ms_pred/iceberg/iceberg_elucidation.py:302,439`;
`src/ms_pred/iceberg/iceberg_extract_fragments.py:60`;
`src/ms_pred/graff_ms/graff_ms_data.py:238,338`;
plus the definitions and the two wrapper methods `misc_utils.py:580-585` and
`misc_utils.py:824-830`.

None of them is in `create_msg_simulation_dataset.py`, `run_magma.py`,
`01_assign_subformulae.py`, `add_dag_intens.py`, `predict_gen.py`, `dag_data.py`,
`glacier/dataset.py`, or any `train_*.py`. P1 C1 VERIFIED. Two omissions in P1's own
enumeration (the two notebooks, and the wrapper methods whose only callers are
`webui/app.py:2414` and `iceberg_elucidation.py:439`) do not affect the conclusion.

The conversion constant is `misc_utils.py:2557`, `ev = nce * precursor_mz / 500`.

### 2.2 The MassSpecGym side: the only CE transformation

I downloaded all seven dataset-construction notebooks at `f259fe3` and grepped every
cell. The ONLY cells that touch `collision_energy` are notebook 4 cells 9, 10 and 23,
plus notebook 5 cells 11 and 21, which use a `simple_ce` helper for stratification and
plotting only and never write the column back.

Notebook 4 cell 9, verbatim structure:

```
ce_str = ce_str.split(";")[-1]
if "%" in ce_str: normalized = True else: normalized = False
if "-" in ce_str or "Ramp" in ce_str or "RAMP" in ce_str or "->" in ce_str:
    ramped = True ; ce = 0.5*min + 0.5*max      # ramped_regex, "V" stripped
else:
    ramped = False ; ce = float(normal_regex.search(ce_str).group(0))
except: ce = np.nan
...
def convert_nce(row):
    if row["normalized"]: ace = (nce * row["precursor_mz"] * 1.) / 500.
    else: ace = row["ce"]
```

Cell 10 applies it and prints the NaN count before and after: `116828` and `116828`.
Cell 23 strips the annotation suffix with `float(x.split(' ')[0])`.

P3 C1 and P3 C2 VERIFIED. Three corrections to P3's description:

1. The ramped test also matches the literal `RAMP`, not only `Ramp`.
2. `normalized` and `ramped` are INDEPENDENT flags. A string carrying both a `%` and a
   hyphen is averaged first and then multiplied by `precursor_mz/500`. P3's account
   reads as if `%` and ramp were alternatives.
3. `normal_regex = \d+(\.\d+)?` does not match a sign or an exponent, so a negative or
   scientific-notation CE string silently loses that information, exactly as ms-pred's
   own parser does (section 2.4).

Notebook 6 cell 3 does the instrument merge: input `ITFT 110724, QTOF 53823,
Orbitrap 38585, QFT 22749`, output `Orbitrap 172058, QTOF 53823`. P3 C14 VERIFIED.
Notebook 6 cell 5 defines `simulation_challenge = (~df.isna().any(axis=1)) & (adduct ==
'[M+H]+')` with output `True 119029 / False 112075`. Q1 VERIFIED.

Merge order, notebook 1 cell 12: `MassBank_NIST.msp`, `MoNA-export-LC-MS_Spectra.msp`,
`ms2_spectra_corinna.mgf` (MSnLib), then the 46 GNPS MGFs. Notebook 3 cell 2 groups
spectra by InChIKey in first-appearance order and cell 13 assigns
`MassSpecGymID{i+1:07d}` sequentially. P3 C18's mechanism VERIFIED.

### 2.3 The value that reaches each model, traced end to end

**ICEBERG generator.** `train_gen.py:160-161` reads
`data/spec_datasets/msg_simulation/magma_outputs/magma_tree.hdf5`.
`create_msg_simulation_dataset.py:445-450` symlinks `magma_outputs` (and
`spec_files.hdf5`, `spec_files`, `spec_files_w_eV`) from the `msg` dataset directory,
so this IS the `msg` MAGMa tree file. `DAGDataset.__init__` at `dag_data.py:505` does
`.drop("collision_energies", axis=1)`: the labels CE column is discarded. The join to
labels is by `common.rm_collision_str` (`misc_utils.py:2585-2593`, split on
`'_collision'` and keep the prefix), which is CE-format agnostic, so no row is lost on
a CE mismatch. The CE the model sees is `tree["collision_energy"]`
(`dag_data.py:309-310`), collated at `dag_data.py:650-651` as
`torch.FloatTensor([float(j["collision_energy"]) ...])`. P1 C3 VERIFIED and
strengthened by the symlink line, which P1 did not cite.

`run_magma.py:172-173` reads the spectrum through `common.parse_spectra`, whose per
block header string becomes `MassSpec(spectra_header, ...)` (`misc_utils.py:1938`).
`MassSpec.__init__` (`misc_utils.py:57-61`) calls
`chem_utils.get_collision_energy` when the string contains `collision`, then does
`float(f'{float(ce):.0f}')`. `run_magma.py:211,427-429` then keys the tree by that
rounded value and stores it as the tree's `collision_energy`.

**ICEBERG intensity and contrastive intensity.** `train_inten.py:144-150` and
`train_contr_inten.py:150-156` read the predicted DAG folder given by
`--magma-dag-folder`, which the configs set to
`results/iceberg_msg_simulation/split_rnd1/preds_train_100_inten.hdf5`, the output of
`add_dag_intens.py`. That file's CE came from `predict_gen.py`:
`collision_energies = ast.literal_eval(entry["collision_energies"])` at line 146 and
`common.collision_energy_to_float(colli_eng)` at lines 199 and 203, from
`msg_simulation/labels.tsv`. P1 C4 VERIFIED, with one correction: the UNROUNDED label
float is what `model.predict_mol(..., collision_eng=colli_eng_val, ...)` receives at
`predict_gen.py:246-252`; the rounding happens afterwards, when the result is wrapped
in `common.MassSpec(collision_energy=_colli_eng_val, ...)` at `predict_gen.py:262-264`.
So the value the generator saw while producing the training trees and the value the
intensity model is later trained on can differ by up to 1.

`run_scripts/iceberg/msg_simulation/02_run_dag_gen_predict_msg_simulation.sh:7-11`
passes `--true-dag-path data/spec_datasets/msg_simulation/subformulae/no_subform.hdf5`.
`add_dag_intens.py:121-149` iterates the TRUE tree names, takes
`colli_eng = common.get_collision_energy(true_dag_n)`, and calls
`pred_dag_db.read(pred_dag_name, collision_energy)`, which resolves an exact key
(`misc_utils.py:1360-1379`, `_get_full_name` then `read_attr`). So the intensity
training set is keyed by the msg_simulation subformula CE key, not by the labels CE.

**GLACIER.** `glacier/dataset.py:26` imports `DAGDataset` from `iceberg.dag_data`, so
the `drop("collision_energies")` at `dag_data.py:505` applies here too. Its own
`TreeProcessor` sets
`"collision_energy": float(tree["collision_energy"]) if "collision_energy" in tree else 0.0`
(`glacier/dataset.py:150`) and collates at `glacier/dataset.py:589`. P1 C3 VERIFIED
for GLACIER.

### 2.4 Parser semantics, probed verbatim

I re-implemented `chem_utils.get_collision_energy` (`chem_utils.py:740-755`) and
`collision_energy_to_float` (`chem_utils.py:780-784`) verbatim from source and ran
them. Results:

```
'collision 30 eV'            -> '30'
'collision 27.5'             -> '28'      (round half to even)
'collision 28.5'             -> '28'
'collision 32.5'             -> '32'
'collision 30 % NCE'         -> '30'      (unit and % silently dropped)
'collision 30 eV [imputed]'  -> '30'      ([imputed] silently dropped)
'collision -20'              -> '20'      (sign lost)
'collision 1e2'              -> '1'       (exponent lost)
'collision 20,30'            -> '20'      (only the first value of a list)
'collision nan'              -> 'nan'
'ms2peaks'                   -> '2'       (see new issue N1)
collision_energy_to_float('20,30') -> ValueError
collision_energy_to_float('30%')   -> ValueError
```

P1 C17 VERIFIED, every sub-claim reproduced. The last line is new (N1).

### 2.5 The CE key format is a bare integer, by construction

Two code paths write the subformula keys, and both force a bare number:

- `data_scripts/forms/01_assign_subformulae.py:135-139`,
  `format_collision_energy(ce) = f"{float(ce):.0f}"` (or the literal `"nan"`), used in
  the `--collision-source labels` branch (line 424-433).
- The default `raw` branch (line 435-438) takes the keys of the object returned by
  `common.parse_spectra`, i.e. `CompositeMassSpec._standardize_ce`
  (`misc_utils.py:780-784`): `get_collision_energy` first, then `f'{float(ce):.0f}'`.

Either way the key is written as `f'{spec_name}_collision {colli_eng}'` + `.json`
(line 439, line 469). A unit, a `%`, or an `[imputed]` marker present in a spectrum
header CANNOT survive into a key. This UPGRADES P1 C16 from INFERRED to VERIFIED, and
replaces its stated justification. P1 argued from the consequence ("otherwise
parse_subformula_key would skip every key and intensity training would have had no
data"); the key-writing code settles it directly.

### 2.6 Imputation

`create_msg_simulation_dataset.py:67-80` `format_collision_energy` returns
`f"['{label}']"` where `label` is `str(int(val))` or `f"{val:g}"`. Its
`if "[imputed]" in label: return None` guard is unreachable, because `label` is derived
from a float. P1 C23 VERIFIED. The row-level guard that can fire is at lines 130-131,
which drops rows whose `collision_energies` string contains `[imputed]`; the source
column is MassSpecGym's numeric `collision_energy`, so nothing matches. Combined with
0 NaN CE among the simulation rows, Q2's "0 imputed rows" VERIFIED.

The only imputation code in the repository is
`run_scripts/iceberg/msg_all/04_impute_missing_collision_energies.py`, which builds a
candidate grid with `NCE_GRID = range(5, 151, 5)` (line 53) while its own module
docstring (line 6) says "a 5..100 NCE grid, step 5", converts each with
`int(common.nce_to_ev(int(nce), precursor_mz))` (line 163), and
`05_build_msg_all_iceberg_dataset.py:105-106` writes the result back as
`str([f"{float(ev):.0f}"])`. P1 C19 VERIFIED including the docstring contradiction.

---

## 3. How the models embed the CE float

### 3.1 The embedding is identical in all three models

`chem_utils.py:118-119`: `COLLISION_PE_DIM = 64`, `COLLISION_PE_SCALAR = 10000`.
Constructor, identical in `iceberg/gen_model.py:140-160`,
`iceberg/inten_model.py:131-151` and `glacier/joint_model.py:137-147`:

```
pe_power = 2 * torch.arange(pe_dim // 2) / pe_dim
self.collision_embedder_denominators = nn.Parameter(torch.pow(pe_scalar, pe_power))
self.collision_embedder_denominators.requires_grad = False
self.collision_embed_merged = nn.Parameter(torch.zeros(pe_dim))
```

Forward, identical in `gen_model.py:283-295`, `inten_model.py:497-510` and
`glacier/joint_model.py:270-284`:

```
embed_collision = torch.cat((torch.sin(ce.unsqueeze(1)/denoms.unsqueeze(0)),
                             torch.cos(ce.unsqueeze(1)/denoms.unsqueeze(0))), dim=1)
embed_collision = torch.where(torch.isnan(embed_collision),
                              self.collision_embed_merged.unsqueeze(0), embed_collision)
```

There is no scaling, standardisation, clipping, log, bucketing or learned projection of
the scalar before the sin/cos. P1 C2 and P2 C1/C2 VERIFIED.

The commented-out block at `gen_model.py:149-156` and `inten_model.py:142-149` carries
the only unit statement anywhere in the model code: "Compute the merged collision
embedding as the mean of all energies 0 - 100 eV". It is dead code.

### 3.2 Checkpoint tensors, verified without torch

torch is not installed in the available interpreter, so I verified the frozen
denominators directly from the zip containers: read every `archive/data/*` member,
select the 128-byte members (32 float32), and compare against
`10000 ** (2*arange(32)/64)` at `rtol=1e-5`.

| checkpoint | matching 32-float blob | all-zero 64-float blobs |
|---|---|---|
| gen | `archive/data/2` | 1 |
| inten_contr | `archive/data/2` | 1 |
| glacier | `archive/data/1` | 1 |

Exactly one denominator tensor and exactly one all-zero 64-vector in each. P2 C1
VERIFIED independently. `git log -S` shows `COLLISION_PE_DIM`/`COLLISION_PE_SCALAR`
were last touched at `13a031e` (2025-05-23), long before any of these checkpoints, so
the formula could not have differed at training time.

`embed_collision`, `embed_instrument` and `embed_adduct` are all `true` in all three
checkpoints (t1 `checkpoint_hyperparameters.jsonl`). P2 C3 VERIFIED.

### 3.3 Injection point and widths

`gen_model.py:263-300` builds `concat_list = [ndata, adducts, collision, instruments]`
and `gen_model.py:177` sets
`gnn_node_feats = node_feats + adduct_shift + collision_shift + instrument_shift`.
`inten_model.py:489-511` does the same by repeated `torch.cat` on `root_repr.ndata["h"]`.
`glacier/joint_model.py:259-295` concatenates onto the Graphormer node features.

Arithmetic check against the checkpoints' own `node_feats`: gen 46 + 22 + 64 + 4 = 136;
inten_contr 32 + 22 + 64 + 4 = 122; glacier 88 + 22 + 64 + 4 = 178. These match P2 C4's
reported input widths. I could not read the actual `input_project` weight shapes
without torch, so the widths themselves are taken from P2; the additive decomposition is
VERIFIED from code plus the checkpoint `node_feats` values.

`gen_model.py:192` carries the author's own note that the fragment-side root GNN uses
`orig_node_feats + adduct_shift` with the comment `# TODO: why not ev or instrument?`.

### 3.4 Precursor m/z never participates in a CE conversion

`gen_model.py:236` accepts `precursor_mzs` and the forward body (lines 263 to 403)
never references it. `inten_model.py` uses it only at lines 762-788 as a `parent_mass`
argument to the loss. `glacier/joint_model.py` uses it only at lines 647-657, 731-733,
also in losses; `glacier/predict_smis_joint.py:322` hard-codes `"precursor": 0.0`.
P2 C5 VERIFIED.

### 3.5 Missing CE is handled differently by ICEBERG and GLACIER

ICEBERG: a NaN CE produces NaN sin/cos, which `torch.where` replaces with the all-zero
vector.

GLACIER: `glacier/dataset.py:150` substitutes `0.0` when the tree has no
`collision_energy` key, and 0.0 is NOT NaN, so it gets the genuine sin/cos embedding of
zero, which is `[0]*32 + [1]*32`, not the zero vector. P1 C18 VERIFIED. This is a real
asymmetry: the two families encode "unknown energy" as two different points.

### 3.6 Deployment-side conversion exists but is opt-in and eV-facing

`predict_smis.py:183-190` and `glacier/predict_smis_joint.py:177-180` pass the labels
CE through `collision_energy_to_float` with no conversion and no NCE flag
(`predict_smis.py:188` additionally skips NaN). The only conversion entry point is
`iceberg_elucidation.py`, whose docstring at line 201 reads "if True, the collision
energies are treated as normalized collision energy; otherwise, they are treated as
absolute eV", with the conversion at line 302 and `f'{float(_):.0f}'` rounding at line
305. `webui/app.py:225-244` converts user NCE to eV the same way. P2 C10, P2 C11 and
P1 C20 VERIFIED.

---

## 4. Numeric re-derivation

Recomputed from `msg/labels.tsv` (119,029 rows) joined to
`massspecgym15_identity_metadata_joined.parquet` on `spec == identifier`:

- merged rows 119,029, zero on either side of the set difference.
- simulation_challenge fold sizes: train 99,341, val 9,734, test 9,954.
- labels CE == `floor(MSG 1.5 CE)` on 119,029 of 119,029 rows.
- labels CE == round-half-even(MSG CE) on 106,838 rows only.
- rows where `f"{CE:.0f}" != f"{floor(CE):.0f}"`: train **11,163**, val **486**, test **542**.
- kept after that filter: train **88,178**, val 9,248, test 9,412.
- full MassSpecGym fold sizes: train 194,119, val 19,429, test 17,556.

Step arithmetic from the frozen checkpoints:

| checkpoint | epoch | global_step | steps/epoch | implied N |
|---|---|---|---|---|
| gen | 16 | 52,666 | 52,666/17 = 3,098 | 99,105 to 99,136 (bs 32, `devices=1` hardcoded at `train_gen.py:294`) |
| glacier | 23 | 74,352 | 74,352/24 = 3,098 | 99,105 to 99,136 |
| inten_contr | 5 | 8,268 | 8,268/6 = 1,378 | 88,129 to 88,192 (bs 32, DDP, `devices=torch.cuda.device_count()` at `train_contr_inten.py:319`, config `visible_devices: [0,1]`) |

99,341 train rows would need 3,105 steps, so 205 to 236 train rows are missing for gen
and GLACIER. 88,178 falls inside the inten_contr window; 99,341 with no drop would give
1,553 steps, which the checkpoint excludes. P1 C13, C14, Q8 and Q9 VERIFIED.

A robustness point P1 and Q did not make: GLACIER's implied N window is the SAME under
both of its historical configs, because `train_joint.py:294-295` uses
`DDPStrategy` with `devices=torch.cuda.device_count()`. Batch 16 on two visible devices
(c792201, 13ce056) and batch 32 on one visible device (470d118 onward) both give 32
items per optimizer step. The window does not depend on which config era produced the
checkpoint.

---

## 5. What remains genuinely open, and one attempted narrowing that failed

### 5.1 The `int(MSG CE)` inference (P1 C15, Q8) survives and gains a second route

The drop that explains inten_contr's step count is produced by
`filter_subformulae` (`create_msg_simulation_dataset.py:236-276`), which keeps a base
`no_subform.hdf5` entry only if `(spec, collision_key(base key CE))` is in
`iter_label_collision_pairs(labels)`, where both sides go through
`collision_key(v) = f"{float(v):.0f}"` (line 202-206). A row is dropped exactly when
round-half-even(base key CE) differs from round-half-even(label CE).

P1 derived the 11,163 figure by assuming the base msg keys are `int(MSG CE)` and
attributing that to the non-public `spec_files.hdf5` headers. I found a second and
independent route that P1 did not consider: `01_assign_subformulae.py` has a
`--collision-source {raw,labels}` option (lines 59-66). Under `labels`, the base key is
`format_collision_energy(labels CE)`, and the committed `msg/labels.tsv` CE is
`floor(MSG CE)` on 100 percent of rows (section 4), so base key = floor(MSG CE) BY
CONSTRUCTION, with no assumption at all about the header values. Under the default
`raw`, the same conclusion requires the headers to hold `int(MSG CE)`.

Either way the conclusion is the same, and the competing hypothesis (base keys =
round(MSG CE)) is excluded by the step count. The inference is therefore better
supported than P1 stated. It is still an inference: the step window is 64 wide, so
11,163 is not the unique drop count that fits, and the committed run scripts do not
pass `--collision-source` at all (HEAD `run_magma.sh` omits it, so the default `raw`
applies to anything actually run from the committed scripts).

### 5.2 GLACIER's numeric CE (P1 C22, Q16) stays UNRESOLVED, and I can say why more sharply

I tried to close it with a stem-matching argument and the argument failed on dates.

`add_dag_intens.py:94-117` matches predicted to true trees by `Path(n).stem`. If
GLACIER's `magma_tree_with_inten.hdf5` were built against a `no_subform.hdf5` whose
keys use the `f"{ce:.0f}"` format, then GLACIER's keys would be integer-formatted, and
since the legacy JSON writer stores `"collision_energy": float(colli_eng.split()[1])`
parsed from that SAME string (commit `3d08224`, `run_magma.py` lines shown by
`git show`), GLACIER's stored CE would necessarily be an integer. That would eliminate
Q's `H_raw` sensitivity (GLACIER seeing the unrounded MSG float).

The argument does not hold, for a dated reason. At `3d08224` (2025-09-02) BOTH writers
keyed on the RAW header string verbatim: `parse_spectra` returned
`(spectra_header, peak_data)` tuples with no rounding, `process_spec_file` built
`fused_tuples = {ce: x for ce, x in tuples}` on those raw headers, the subformula key
was `f'{spec_name}_{colli_eng}'`, and the MAGMa tree name was
`f"{spec_name_clean}_{colli_eng}.json"`. Under that era the two key sets match each
other trivially while both being raw, and `float(colli_eng.split()[1])` yields the
unrounded header number. The rounding-based writers appear later (`2efc62c`,
2026-03-20, for `run_magma`; the `format_collision_energy` path in
`01_assign_subformulae` arrives with `7b59014`, 2026-07-06). The GLACIER checkpoint is
dated 2026-06-12 and the msg_simulation work is 2026-07, so GLACIER plausibly trained
on artifacts produced before the rounding writers existed.

Conclusion: Q's `H_raw` for GLACIER is a LIVE hypothesis, not a remote one, and the
question cannot be closed without `data/spec_datasets/msg/spec_files*.hdf5` or
`magma_outputs/magma_tree_new.hdf5`.

One further constraint that does NOT help: the fact that GLACIER's implied N equals
gen's is uninformative about key format, because `DAGDataset` joins on
`rm_collision_str`, which strips everything after `_collision` regardless of format.

### 5.3 Which GLACIER stage produced version_5 (P1 open question) stays open

Both `train_joint.py:278` and `train_contr_joint.py:337` write to `save_dir/version_N`,
so the path form does not discriminate. The checkpoint's `lr: 0.0004` does not
discriminate either, because `train_contr_joint.py:365` calls
`JointModel.load_from_checkpoint(train_checkpoint)`, which restores the base model's
hparams exactly as the ICEBERG contrastive stage does. The contrastive config's
`batch-size: [16]` with `visible_devices: [0,1]` also gives 32 items per step, so the
step arithmetic does not discriminate. The only weak signal is that 24 completed epochs
sits just above the base config's `min-epochs: [20]`, which both configs share.

### 5.4 Evidence that an eV-labelled msg variant existed in the authors' tree

Three separate textual traces, all VERIFIED at the cited lines:

- `create_msg_simulation_dataset.py:446` symlinks a resource literally named
  `spec_files_w_eV` alongside `spec_files.hdf5`.
- `run_magma.sh` at `3d08224` ran MAGMa on `spec_files.hdf5` but pointed the subformula
  step at `--spectra-dir data/spec_datasets/$dataset/spec_files_w_imputed_eV`, with an
  inline comment "for msg: may need to override the --spectra-dir flag to point to a
  different spec_files folder as needed".
- HEAD `src/ms_pred/retrieval/retrieval_benchmark_torchmetrics.py:234` reads
  `labels_withev_validinst.tsv` for `dataset == 'msg'`, and the GLACIER config used
  `labels_withev.tsv` at `04ba1a9`.

None of these is in the frozen checkpoints' declared path, but together they show the
authors maintained an eV-converted msg variant, which is why P1 C22 cannot be closed
from the public tree.

### 5.5 Committed scripts are not an execution record

`3d08224`'s `run_magma.sh` passes `--spectra-dir` and `--output-dir` to
`01_assign_subformulae.py`, whose argparse at that commit accepts neither (it has
`--output-dir-name`, and no spectra-dir option at all). argparse would have exited with
"unrecognized arguments". P1 C23 VERIFIED.

Likewise `create_msg_simulation_dataset.py` cannot have produced the committed
`msg/labels.tsv`: its `format_collision_energy` writes `f"{val:g}"` for non-integers,
it adds a `collision_imputed` column, and it writes no `Unnamed: 0` column, whereas the
committed file has `Unnamed: 0`, no `collision_imputed`, and integer-only CE strings.
P1 C12 VERIFIED. `git log --follow` shows `data/spec_datasets/msg/labels.tsv` was added
once, at `648b061` (2025-10-26), and never modified; `git ls-files data/spec_datasets`
lists no msg split file. P1 C9 VERIFIED.

---

## 6. New issues found in this pass

N1. `chem_utils.get_collision_energy` has a silent fallback that fires on any string
containing a digit. Probed verbatim: `get_collision_energy('ms2peaks')` returns `'2'`,
and `get_collision_energy('x_collision 45.0.json')` returns `'45'` because the trailing
`.*` swallows the extension. A spectrum block header with no `collision` token but any
digit therefore receives a fabricated collision energy rather than `nan`. This function
is on the MAGMa path (`run_magma.py` via `MassSpec.__init__`), on the
`add_dag_intens.py:113` path, and on the `dag_data.py:892` decoy path.

N2. `create_msg_simulation_dataset.format_collision_energy` uses `f"{val:g}"`, which
keeps only six significant figures. Probed: `358.40016` becomes `'358.4'`. A
script-generated `msg_simulation/labels.tsv` therefore does NOT round-trip the
MassSpecGym float exactly. It does not change any rounded key, but it means the
"raw MassSpecGym value passed through" description is true only to six significant
digits.

N3. `01_assign_subformulae.py` has an undocumented-in-the-run-scripts
`--collision-source {raw,labels}` switch (lines 59-66) that changes the base subformula
key from round(header CE) to round(labels CE). `run_magma.sh` at HEAD never passes it,
so the default `raw` applies to the committed pipeline. This switch is the single
highest-leverage unknown for reconstructing the ICEBERG base keys, and no prior phase
mentions it.

N4. MassSpecGym notebook 1 cell 12 loads every library with
`load_spectra(..., metadata_harmonization=False)`. P3 C14's account of the instrument
key mapping cited matchms `known_key_conversions` and `PickyDict` without noting that
matchms value harmonisation was switched off at load time. The conclusion (the explicit
conversions dict in notebook 2 and the prefix stripping in notebook 4 do the work) is
unaffected, but the matchms citation should be qualified.

N5. Notebook 6 computes `simulation_challenge` with `~df.isna().any(axis=1)` on a
15-column frame and only then drops to the 14 released columns (cell 9 prints
`(231104, 15)` then `(231104, 14)`). The rule therefore depends on a column that is not
in the release. Q verified empirically that the rule reproduces on the 14 released
columns, which implies the dropped column had no nulls, but the rule as stated is not
self-contained from the public file.

N6. The generator and the intensity model are trained on DIFFERENT CE values for the
same spectrum whenever the two disagree. The generator's tree CE comes from the MAGMa
tree (round of the header), while the predicted trees it produced were generated at the
UNROUNDED labels CE (`predict_gen.py:246-252`) and only then rounded for storage
(`predict_gen.py:262-264`). No prior phase flagged that `predict_mol` sees the
unrounded value.

N7. `train_contr_inten.py:319` and `glacier/train_joint.py:295` use
`devices=torch.cuda.device_count()`, so the effective items-per-step depends on the
launch environment rather than on the config. Every step-count inference in this study
is conditional on the `visible_devices` entry in the config having been honoured. The
gen model is the exception: `train_gen.py:294` hardcodes `devices=1`.

N8. `iceberg/joint_model.py` exists alongside `glacier/joint_model.py`. P1 C2 cites
"joint_model.py:138-147,270-284" without a package prefix; the lines it describes are
in `glacier/joint_model.py` (P2 C1 cites it correctly). Worth fixing in any merged
record so the citation resolves.

---

## 7. Files and reproduction

Notebooks fetched this session (recorded in `downloads_register.jsonl`, phase
`v_code`, all at MassSpecGym commit `f259fe3`):

| file | bytes | sha256 |
|---|---|---|
| 1_Load_data_from_repositories.ipynb | 19,356 | 7b205c0cb5eab6b82d976bca8b598786acfdaddb03a4d35280e1442777023547 |
| 2_clean_library.ipynb | 38,678 | 465efc34e923a2c488b68a0b0963d385ab16a80d523248af92cd2ecc8bbdbddf |
| 3_remove_duplicates_and_profiled_spectra.ipynb | 13,622 | 636ccf6ec3880bbb2b04c0dce0558d11d38aadddc6ffd5eec883e669893173b7 |
| 4_standardization_and_cleaning.ipynb | 181,122 | 5d8ea5993feb450f21fd1dc82b77a05ebc8590b3338a1e2b162e7cb0fc6b832c |
| 5_split.ipynb | 286,603 | cc7e1d9d2f982bde4281003c69550a217c8f7e8bff0ca9d25e1ebdfacbcd7342 |
| 6_final_postprocessing.ipynb | 19,057 | 293975fbc6486a26bb49fe662333bb80a3457ff965261a029d174e653986d878 |
| 7_format_conversions.ipynb | 5,714 | 937d618766d04034b107c892bdf42309fdac3d37ae32cb3f092c8dcab308f46c |

All ms-pred citations are against HEAD `ed8311f` unless a commit hash is given
explicitly. Historical commits referenced: `3d08224` (2025-09-02), `648b061`
(2025-10-26), `13a031e` (2025-05-23), `2efc62c` (2026-03-20), `04ba1a9` (2026-02-22),
`c792201` (2026-03-24), `13ce056` (2026-05-06), `470d118` (2026-05-28), `78c4a00`
(2026-06-11), `d1b1802` (2026-06-17), `35a5aa3` (2026-07-06), `7b59014` (2026-07-06),
`11fd2ed` (2026-07-08).
