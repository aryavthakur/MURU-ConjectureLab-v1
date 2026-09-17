# P2 - Model-internal CE handling and deployment interface (ms-pred)

Study: MURU collision-energy interface adjudication (outcome-blind).
Scope of this note: how the CE float is consumed inside the three frozen checkpoint model classes, what the
prediction path does to it, what the ms-pred authors document, and the closed-form numerical consequences.
No ICEBERG, GLACIER, FIORA or MURU prediction or inference was run. No forbidden path was opened.

Code base: `/Users/aryav/muru-comparators/repos/ms-pred`, HEAD `ed8311f` (paths below are relative to it).
Checkpoints (sha256 re-computed by `p2_read_checkpoint_ce_parameters.py`, all match t1_provenance.json):
- ICEBERG 2.1 msg_simulation gen: `1eda5f3d...7a70`
- ICEBERG 2.1 msg_simulation inten_contr: `e074c039...4f58`
- GLACIER msg: `5a47cecc...db11`

Label key: VERIFIED = read directly in code, checkpoint tensors or data. INFERRED = reasoning from verified facts.
UNRESOLVED = cannot be settled from what P2 may read.

Location note: the session guard refused writes into the `muru-ce-interface-adjudication` worktree from this session,
so this note, its scripts and JSON outputs were written to the session scratchpad under
`.../scratchpad/ce_interface_adjudication/{artifacts,scripts}/ce_interface_adjudication/` with the intended
relative layout. They need to be copied into the worktree by a session allowed to write there.

---

## 1. The CE embedding (identical in all three model classes)

### 1.1 Formula, constants, dimension - VERIFIED

- Constants: `COLLISION_PE_DIM = 64`, `COLLISION_PE_SCALAR = 10000`
  (`src/ms_pred/common/chem_utils.py:118-119`; introduced in commit `13a031e`, 2025-05-23, unchanged since per
  `git log -S`).
- Denominators: `pe_power = 2 * arange(32) / 64`, `d_i = 10000 ** pe_power`, stored as a frozen `nn.Parameter`
  (`requires_grad = False`):
  - FragGNN (ICEBERG gen): `src/ms_pred/iceberg/gen_model.py:141-147`
  - IntenGNN (ICEBERG inten / inten_contr): `src/ms_pred/iceberg/inten_model.py:132-138`
  - GLACIER JointModel: `src/ms_pred/glacier/joint_model.py:138-144`
- Embedding: `e(c) = cat( sin(c / d_i), cos(c / d_i) )`, i = 0..31, 32 sines then 32 cosines
  (`gen_model.py:284-288`, `inten_model.py:498-502`, `glacier/joint_model.py:271-275`).
  So d_0 = 1 (period 2*pi = 6.28), d_8 = 10, d_16 = 100, d_24 = 1000, d_31 = 7498.9 (period 47,117).
- NaN handling: any NaN CE is replaced by the frozen all-zero vector `collision_embed_merged`
  (`gen_model.py:158-160, 289-291`; `inten_model.py:149-151, 503-505`; `glacier/joint_model.py:146-147, 277-279`).
- Checkpoint confirmation (`p2_checkpoint_ce_parameters.json`): in all three frozen checkpoints
  `collision_embedder_denominators` has shape [32] and equals `10000 ** (2i/64)` (rtol 1e-5), and
  `collision_embed_merged` is all zero. The frozen `hparams.yaml` / checkpoint `hyper_parameters` have
  `embed_collision: true`, `embed_instrument: true`, `embed_adduct: true`, `embed_elem_group: true` for gen,
  inten_contr and GLACIER.
- The ICEBERG preprint states the same design: "64-dimensional positional encoding (32 sine, 32 cosine terms,
  base 10,000)" and says it encodes CE "(in eV)" (bioRxiv 10.1101/2025.05.28.656653, v2 full text, section
  "Incorporating collision energy").

### 1.2 What is NOT done to the CE float - VERIFIED

Searched in `gen_model.py`, `inten_model.py`, `glacier/joint_model.py`, `iceberg/joint_model.py`,
`iceberg/dag_data.py`, `glacier/dataset.py`, `common/chem_utils.py`, `common/misc_utils.py`:
- no standardization, no mean/std scaling, no min/max normalization, no log transform, no clipping or clamp,
  no max value, no bucketing or one-hot binning of the value inside the model;
- no learned scaling (denominators are frozen);
- the only transformation is `c / d_i` followed by sin/cos; the tensor is float32 (`torch.FloatTensor`,
  e.g. `gen_model.py:526`, `iceberg/dag_data.py:650-651`, `glacier/dataset.py:589`).

The one quantization that exists is in the data layer, not the model: CE keys are rounded to integer strings.
- `common.get_collision_energy` formats with `f"{float(ce):.0f}"` (`chem_utils.py:740-755`).
- `CompositeMassSpec._standardize_ce` formats with `f'{float(ce):.0f}'` (`misc_utils.py:780-784`).
- Training trees get CE from file-name keys via `get_collision_energy` (e.g. `data_scripts/dag/add_dag_intens.py:113`,
  `iceberg/dag_data.py:892`, `glacier/dataset.py:836`), so training CE values are integers.
- Prediction entry points do NOT round: `predict_smis.py:187`, `predict_gen.py:193,200`,
  `glacier/predict_smis_joint.py:180` use `collision_energy_to_float` (`chem_utils.py:780-784`), which only
  parses the first token. `iceberg_elucidation.iceberg_prediction` does round (`iceberg_elucidation.py:305`).

### 1.3 Where the embedding is injected - VERIFIED

- ICEBERG FragGNN (gen): concatenated per atom to the ROOT molecule node features
  (`gen_model.py:273-318`, order: atom feats, adduct, CE, instrument) and again to every FRAGMENT graph's node
  features (`gen_model.py:332-359`, same order), then through `MoleculeGNN.input_project` (`nn_utils.py:95, 139`).
  `root_module` is the same module object as `gnn` (`gen_model.py:182-183`); both state-dict copies are identical.
  `inject_early: false`, so no other path.
- ICEBERG IntenGNN (inten_contr): same two injection points, root (`inten_model.py:489-531`) and fragments
  (`inten_model.py:542-571`). CE reaches the fragment MLP, the 3 transformer set layers and the output map only
  through these GNN embeddings (`inten_model.py:584-640`).
- GLACIER JointModel: concatenated per atom to the Graphormer input `x` (`glacier/joint_model.py:259-292`,
  order: atom feats, adduct, CE, instrument), consumed only by `atom_encoder = nn.Linear(num_atom_features, hidden)`
  (`graphormer/graphormer_layers.py:36, 51`; `num_atom_features = node_feats + adduct + collision + instrument`,
  `glacier/joint_model.py:157`). The attention-bias module reads `x` only for its shape
  (`graphormer_layers.py:99-110`). The breakpoint decoder and intensity decoder see CE only through the Graphormer
  root token and node embeddings (`glacier/joint_model.py:309-325, 371-389`).
  Discrepancy to note: the GLACIER paper (arXiv 2606.29161v1, section 3.1) says instrument parameters are projected
  "into node embeddings and edge-level attention biases via linear layers"; in the code CE enters node features only.
  This does not change CE semantics.
- Frozen input-projection widths confirm the concatenation layout exactly
  (`p2_checkpoint_ce_parameters.json`): gen `input_project.weight` [512, 136] = 46 atom + 22 adduct + 64 CE + 4
  instrument; inten_contr [256, 122] = 32 + 22 + 64 + 4; GLACIER `atom_encoder.weight` [256, 178] = 88 + 22 + 64 + 4.

---

## 2. Precursor m/z, mass and adduct covariates

### 2.1 No CE conversion anywhere in the model or dataset code - VERIFIED

- `precursor_mzs` is an argument of `FragGNN.forward` (`gen_model.py:237`) and `IntenGNN.forward`
  (`inten_model.py:441`) but is never read in either forward body (`gen_model.py:263-403`,
  `inten_model.py:474-716`). grep shows it appears only in signatures, docstrings and plumbing
  (`gen_model.py:431, 476, 510, 529, 579`; `inten_model.py:363, 381, 404, 728`).
- In IntenGNN and GLACIER, precursor m/z is used only in the training LOSS as a ppm mass tolerance
  (`inten_model.py:275, 311, 762-788`; `glacier/joint_model.py:647-657, 731-733`).
- GLACIER `predict_mol` has no precursor argument at all (`glacier/joint_model.py:833`) and `forward` has none
  (`glacier/joint_model.py:439-441`).
- The ICEBERG joint prediction path passes `precursor_mz` through (`iceberg/joint_model.py:69, 116, 153, 174`) to
  those unused arguments. Fragment m/z values are built from formula masses and `ion2mass[adduct]`
  (`iceberg/joint_model.py:142-148`; `glacier/joint_model.py:891-894, 404-408`) and are used only to place outputs
  in m/z bins, not as an input covariate.
- `nce_to_ev` (`misc_utils.py:2542-2565`, `ev = nce * precursor_mz / 500`) is never called from any model,
  dataset or `predict_*.py` file. Its only callers are `iceberg_elucidation.py:302` (`nce=True`),
  `iceberg_elucidation.py:439` and `MassSpec/CompositeMassSpec.nce_to_ev` for experimental spectra,
  `iceberg_extract_fragments.py:60` (plot labels), `run_scripts/iceberg/msg_all/04_impute_missing_collision_energies.py:163`,
  `run_scripts/iceberg_atlas/01_generate_task_tsv.py:35`, and `webui/app.py` (e.g. 244, 2414, 2714, 3110).

Consequence (VERIFIED): whatever number is placed in `collision_energies` is embedded verbatim (after float parsing).
The model code has no way to know whether it is NCE or eV.

### 2.2 Could the network rescale NCE-like inputs internally? - INFERRED capacity, UNRESOLVED behaviour

- There is no explicit scalar mass covariate, but the exact elemental composition is visible:
  root and fragment formula vectors are encoded with `abs-sines` Fourier features of element counts
  (`form_embedder.py:137-169, 271-272`; used at `gen_model.py:87-95, 384-392`, `inten_model.py:78-86, 591-598`,
  `glacier/joint_model.py:174-180, 315-317, 372-374`), and atoms are one-hot element features. With a fixed adduct
  ([M+H]+ only in training, section 2.3), precursor m/z is a deterministic function of inputs the network sees, so a
  mass-dependent reinterpretation of the CE embedding is representable in principle.
- The only instrument-specific signal is the instrument one-hot, so instrument-conditional CE semantics
  (for example NCE-like numbers on Orbitrap rows and eV-like on QTOF rows) are also representable.
- Whether the frozen weights actually implement either is not decidable by static reading; deciding it would need
  model evaluation, which is out of scope.

### 2.3 Adduct and instrument vocabularies - VERIFIED

- Adduct one-hot: 14 positions (`chem_utils.py:187-217`, ICEBERG 2.1 layout, negative modes at 9-13) plus a
  multi-hot mode block (`chem_utils.py:220-256`). The frozen `adduct_embedder` is [14, 22] in all three
  checkpoints, i.e. 8 mode columns (index 8 "+NH3" is never triggered by the string parser, so it is absent).
  Row [M+H]+ = one-hot col 0 + mode cols 14 (positive) and 17 (add proton).
- Instrument one-hot: `{"Orbitrap": 0, "QTOF": 1, "IT-FT": 2, "Unknown": 3}` (`chem_utils.py:277-283`; comments say
  Orbitrap = "Orbitrap HCD", IT-FT = "Orbitrap CID"). Frozen `instrument_embedder` is the 4x4 identity in all three
  checkpoints.
- Training labels (`data/spec_datasets/msg/labels.tsv`, 119,029 rows, committed in `648b061`): ionization
  [M+H]+ only; instrument Orbitrap 81,323 and QTOF 37,706 only; labels `instrument` equals MassSpecGym
  `instrument_type` for every row (`p2_msg_label_ce_boundary_check.json`).
- Frozen weights agree (`p2_checkpoint_ce_parameters.json`, column norms of the first input projection):
  - inten_contr: every adduct column except 0, 14, 17 and instrument columns IT-FT and Unknown have max |w| about
    4.9e-38 (numerically zero). Orbitrap and QTOF columns have norms 1.31 and 1.44.
    INFERRED mechanism: Adam with L2 weight decay 1e-7 and zero data gradient drives never-active columns to zero.
  - gen (weight decay 0): IT-FT / Unknown columns 1.108 / 1.146, the same level as never-active adduct columns
    (about 1.08-1.17); Orbitrap / QTOF 1.53 / 1.99.
  - GLACIER (weight decay 0): IT-FT / Unknown 0.333 / 0.332, the same as never-active adduct columns (0.29-0.34);
    Orbitrap / QTOF 1.44 / 2.00.
  So only the Orbitrap and QTOF tokens carry trained signal. Passing IT-FT or Unknown is out of distribution
  (for inten_contr it is exactly equivalent to giving no instrument column at all).
- Instrument defaults in code differ by path (VERIFIED): ICEBERG `DAGDataset` sets missing instrument to
  "Orbitrap" (`iceberg/dag_data.py:486-487`; the "Unknown" default at 495-496 is dead code after that);
  `predict_smis.normalize_instrument` maps NaN or unknown strings to "Orbitrap" (`predict_smis.py:78-81, 167-168`);
  GLACIER `IntenPredDataset` defaults a missing column to "Unknown" and silently drops rows whose instrument or adduct
  is not in the vocabulary (`glacier/dataset.py:907-908, 928-931`); `glacier/predict_smis_joint.prepare_entry`
  defaults a missing column to "Orbitrap" (`predict_smis_joint.py:162`).

---

## 3. Deployment interface and author guidance

### 3.1 Prediction entry points - VERIFIED

- `src/ms_pred/iceberg/predict_smis.py`: reads `labels["collision_energies"]` (a Python-literal list), parses each
  with `collision_energy_to_float`, skips NaN, and passes the float unchanged plus `precursor` and `instrument`
  (`predict_smis.py:163-191, 230-241`). No `--nce` flag exists (`predict_smis.py:33-75`).
- `src/ms_pred/iceberg/predict_gen.py:146-202`: same, no conversion.
- `src/ms_pred/iceberg/predict_inten.py:181-195`: uses `batch["collision_engs"]` from the dataset, no conversion.
- `src/ms_pred/glacier/predict_smis_joint.py:153-184`: same parsing, no precursor, no conversion.
- `src/ms_pred/glacier/predict_inten_joint.py:147-169`: uses `batch["collision_engs"]`, no conversion.
- `src/ms_pred/iceberg/iceberg_elucidation.py`:
  - `iceberg_prediction(..., nce=False, ...)`, docstring: if True "treated as normalized collision energy;
    otherwise, they are treated as absolute eV" (`iceberg_elucidation.py:176, 201`);
  - computes `precursor_mass = mass_from_smi(cand) + ion2mass[adduct]` and, if `nce`, applies `nce_to_ev`, then
    rounds to integer strings (`iceberg_elucidation.py:294-306`) before writing the labels TSV for `predict_smis.py`
    (`iceberg_elucidation.py:327-345`);
  - `load_real_spec(..., nce=...)` converts experimental spectrum CE keys the same way (`iceberg_elucidation.py:371, 439`).

### 3.2 What the authors instruct for Orbitrap NCE data - VERIFIED, with the scope caveat below

- Demo notebook: `local_config['nce'] = True  # nce is used instead of eV values in the MS/MS file for collision
  energy` (`notebooks/iceberg_2025_biorxiv/iceberg_demo_pubchem_elucidation.ipynb`, cell 6), and plots keys as
  `f'{ce} eV'` (cell 7). Same `nce=True` pattern in `iceberg_fig_visual_msms.ipynb` (cells 7-29),
  `iceberg_pooled_cn_coupling.ipynb` (cell 13) and `sirius_eval_msnlib.ipynb` (cells 30, 39, 45), where MSnLib
  `COLLISION_ENERGY` is converted with `common.nce_to_ev(int(float(meta['COLLISION_ENERGY'])), float(pmz))`
  (cell 34).
- Atlas generation: NCE grid 5..100 converted to eV with `nce_to_ev` (`run_scripts/iceberg_atlas/01_generate_task_tsv.py:16, 35`).
- Web UI: "Assume the labels are NCE" then `nce_to_ev(parentmass)` (`webui/app.py:2412-2414`).
- Preprint: "Collision energy values recorded as normalized collision energy (NCE) are converted to eV using:" an
  equation rendered as an image (bioRxiv v2, "Dataset processing"); the code formula is `nce * precursor_mz / 500`
  (`misc_utils.py:2557`; tested in `tests/test_misc_utils.py:48-59`). The preprint also says non-HCD spectra were
  excluded and QTOF spectra not included for that work.
- SCOPE CAVEAT (VERIFIED): every one of these instructions is attached to NIST-trained ICEBERG checkpoints.
  `configs/iceberg/iceberg_elucidation.yaml:6-7, 32-33` point to `iceberg_nist20` / `iceberg_nist23` checkpoints;
  the atlas uses `dag_nist20` / `dag_inten_nist20` (`run_scripts/iceberg_atlas/02_run_prediction_slurm.sh:57-58`).
  The README contains no CE unit statement for the MassSpecGym-trained ICEBERG 2.1 or GLACIER weights
  (`README.md:91-94, 125-224, 277-282, 364-372`). There is no author instruction specific to the frozen MSG
  checkpoints.

### 3.3 Author-side evidence about the MSG-trained models' CE axis - VERIFIED text, contradictory implications

- `msg_simulation` pipeline: labels are built from MassSpecGym 1.5 `collision_energy` with no conversion
  (`data_scripts/create_msg_simulation_dataset.py:67-80, 98-131`); the README says the result has 119,029 spectra
  (`README.md:183-184`), equal to the committed `msg/labels.tsv` row count. The docstring and code keep the raw
  value; `spec_files_w_eV` is listed as a linkable resource name (`create_msg_simulation_dataset.py:446`) but its
  content is not in the repo (UNRESOLVED what it holds).
- `msg_all` imputation, which runs a MassSpecGym-known-CE ICEBERG model: builds candidate CEs as
  `nce_to_ev(NCE grid 5..150, precursor_mz)` and feeds those eV values to `predict_smis.py`
  (`04_impute_missing_collision_energies.py:5-6, 53, 160-166, 193-209`), then writes the best eV back into labels
  alongside the known raw MassSpecGym values (`05_build_msg_all_iceberg_dataset.py:105-106, 131-149`).
  So the ms-pred authors treated the MSG-trained model's CE axis as eV in that script.
- MassSpecGym paper (arXiv 2410.23326): the simulation challenge defines C as "measured in electronvolts or eV"
  (section 3.2), while section 3.3 says 53% of entries "contain normalized collision energies".
- Data check (`p2_msg_label_ce_boundary_check.json`): committed labels CE equals floor(MassSpecGym 1.5 CE) for all
  119,029 rows (not rounding; 12,191 rows differ from round()). 25,274 MassSpecGym CE values are non-integer
  (Orbitrap 23,913; QTOF 1,361) and 94.6% of them equal `NCE * precursor_mz / 500` for NCE on a 5-step ladder,
  while the integer values include ladders such as 20/30/45/60. Label CE range 0 to 358, 1st/50th/99th percentile
  6/30/150. This is a pointer for P1: the training CE axis looks mixed (some already eV-converted, some raw),
  and P2 does not attribute sources.
- Contradiction flagged, not resolved: GLACIER's config trains on `dataset-name: msg`, `labels.tsv`
  (`configs/glacier/joint_train_msg.yaml:20-23`), i.e. the 119,029-row file, while the GLACIER paper (section 4.1.1)
  describes "231,104 tandem mass spectra" for the MassSpecGym split. The frozen GLACIER checkpoint alone cannot
  show which label file and which CE values were used (UNRESOLVED; the MAGMa tree files carrying the training CE
  keys are not local).

---

## 4. Numerical consequence of the embedding actually used

All numbers from `p2_ce_embedding_geometry.json` (pure formula; no weights, no inference).

### 4.1 Structure

- ||e(a) - e(b)||^2 = 2 * sum_i (1 - cos((a - b)/d_i)): the embedding geometry depends only on the difference
  a - b. There is no absolute-magnitude term except through which phases are reached.
- No saturation or clipping: every input maps to a distinct point, and there is no exact aliasing (the 32 periods
  2*pi*d_i are incommensurate). Over integer differences 1..400 the smallest distance is at difference 1 (1.47).
- Partial aliasing: the fastest components wrap inside the training range. Period of i = 0 is 6.28, of i = 8 is 62.8.
  The distance curve rises fast then plateaus with ripples: difference 0.5 -> 0.75, 1 -> 1.47, 2 -> 2.72,
  3 -> 3.58, 5 -> 4.12, 8 -> 4.38, 10 -> 4.68, 24 -> 4.96, 40 -> 5.76, 100 -> 5.32, 300 -> 6.73.
  Local minima (near-aliases) at differences about 5.95 (4.11), 11.95 (4.62), 18.15 (4.84), 24.8 (4.87).
  Reference scales: random phases give 8.0, the maximum is 11.31.
- Magnitude-bearing (monotone) components: sin(c/d_i) is monotone on [0, 358.4] for 13 of 32 frequencies
  (i >= 19, d >= 237) and on [0, 150] for 16 (i >= 16, d >= 100). Their amplitudes are small at typical CE:
  sin(20/100) = 0.199, sin(60/100) = 0.565, sin(12/100) = 0.12; at i = 24 (d = 1000) 0.02 / 0.06 / 0.012.
- Local Lipschitz constant ||de/dc|| = 1.51 per CE unit; an integer-rounding half step moves the embedding by 0.75.

### 4.2 The specific comparisons asked for

| Pair | Difference | Distance | Share of squared distance in i0-15 (d <= 75) | Distance from i16-31 only |
|---|---|---|---|---|
| 20 vs 60 | 40 | 5.76 | 98.9% | 0.60 |
| 20 vs 30 | 10 | 4.68 | 99.9% | 0.15 |
| NCE 20 raw vs eV at m/z 300 (20 vs 12) | 8 | 4.38 | 99.9% | 0.12 |
| NCE 60 raw vs eV at m/z 300 (60 vs 36) | 24 | 4.96 | 99.5% | 0.36 |
| NCE 40 raw vs eV at m/z 800 (40 vs 64) | 24 | 4.96 | 99.5% | 0.36 |
| NCE 90 raw vs eV at m/z 150 (90 vs 27) | 63 | 5.92 | 97.5% | 0.94 |
| any NCE raw vs eV at m/z 500 | 0 | 0.00 | - | - |
| 0 vs 358.4 (label range) | 358.4 | 6.48 | 64.1% | 3.88 |

Raw-NCE versus documented-eV input gap is `NCE * (1 - mz/500)`: zero at m/z 500, growing linearly with NCE and with
distance from m/z 500 (full grid in the JSON; for example m/z 200 NCE 60 -> 24 eV, distance 5.63; m/z 1000 NCE 60 ->
120 eV, distance 5.68; m/z 400 NCE 10 -> 8 eV, distance 2.72).

### 4.3 Reading - INFERRED

- The two candidate interfaces are not near-duplicates in embedding space: except within a few units of m/z 500,
  raw NCE and the eV conversion land 4-6 distance units apart, i.e. about half to three quarters of the
  random-phase distance. The embedding itself cannot make "NCE 20" and "12 eV" equivalent; any equivalence would
  have to be learned from mixed training labels.
- For CE differences under about 40, almost all embedding contrast lives in periodic components that wrap within the
  training range. A monotone "higher CE" signal must be read from the i >= 16 components, whose contrast between 20
  and 60 is only 0.60. The embedding therefore gives strong local identity (which value) but weak, compressive
  ordinal structure; a network trained on a label axis that mixes NCE-ladder integers with eV conversions can place
  a given number anywhere on the fragmentation-extent scale, with nothing in the encoding forcing monotonicity.
- First-layer column norms (not a forward pass) show all 64 CE columns carry non-trivial weight in all three
  checkpoints (gen 0.86-1.47; inten_contr 0.48-1.18; GLACIER 0.33-1.71). In GLACIER the cos columns for i >= 18
  sit at 0.33-0.36, the same as never-active instrument columns (0.33), consistent with those features being nearly
  constant 1 (bias-like) over the CE range, while sin columns for i >= 19 are at about 0.98-1.08.
- Large values do not saturate or clip; values beyond the training maximum (358) or negative values produce valid,
  unseen phase combinations (extrapolation, not aliasing to a boundary).

---

## 5. Answers in brief

1. Embedding: fixed Transformer sinusoidal positional encoding, 64 dims (32 sin + 32 cos), base 10000,
   d_i = 10000^(2i/64), no scaling, normalization, clipping, log or bucketing inside the model; NaN -> zeros.
   `embed_collision` is true in all three frozen checkpoints. Injected as per-atom node features into the root and
   fragment GNNs (ICEBERG gen and inten) or the Graphormer atom encoder (GLACIER). VERIFIED.
2. Precursor m/z never enters any CE conversion in any model or predict path; it is unused in forward and used only
   as a ppm tolerance in losses. Composition is visible, so internal mass-dependent rescaling is representable but
   not observable statically. Instrument vocabulary has 4 tokens; only Orbitrap and QTOF are trained in these
   checkpoints; adduct training is [M+H]+ only. VERIFIED (capacity INFERRED).
3. Deployment: `predict_smis.py`, `predict_gen.py`, `predict_smis_joint.py` pass the labels value verbatim;
   `iceberg_elucidation` offers `nce=True` to convert with `NCE * precursor / 500` and rounds to integers. All author
   instructions to convert Orbitrap NCE to eV are tied to NIST checkpoints; nothing documents the unit for the MSG
   checkpoints. The authors' own msg_all imputation script feeds eV to an MSG-trained model, while the msg_simulation
   label builder passes MassSpecGym values raw. VERIFIED; implication for the frozen checkpoints UNRESOLVED.
4. Numerics: no clipping or exact aliasing; strong local distinguishability (20 vs 12: 4.38; 20 vs 60: 5.76) but
   weak ordinal structure; raw and eV inputs coincide only near m/z 500. VERIFIED arithmetic, INFERRED reading.

## 6. Files

- Scripts: `scripts/ce_interface_adjudication/p2_read_checkpoint_ce_parameters.py` (static tensor read, torch-free
  unpickler), `p2_ce_embedding_geometry.py` (closed form), `p2_msg_label_ce_boundary_check.py` (labels vs MSG 1.5).
- Outputs: `artifacts/ce_interface_adjudication/p2_checkpoint_ce_parameters.json`,
  `p2_ce_embedding_geometry.json`, `p2_msg_label_ce_boundary_check.json`.
- Nothing was downloaded (no entry added to `downloads_register.jsonl`). Web pages read: arXiv 2606.29161 (abs and
  html v1), bioRxiv 10.1101/2025.05.28.656653 v2 full text (v1 full text returned HTTP 429), arXiv 2410.23326 (html).
  WebFetch returns model-extracted text; the short quotes above were requested verbatim, but they were not
  cross-checked against the PDFs.
