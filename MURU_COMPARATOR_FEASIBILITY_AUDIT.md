# MURU-WUR-v2 vs full-spectrum predictors: comparator feasibility audit

**Date:** 2026-09-14. **Status:** reconnaissance only, outcome-blind. No competitor prediction was generated, no model
was downloaded or run, MURU-v2 is unchanged, and no measured MSnLib mu value, peak or intensity was read.
**Base:** PR #7 head `f9e4ea1` (branch `claude/msnlib-confirmation-restart-88cf89`), which is left untouched. This
work sits on its own branch stacked on that commit.

**Question for the later benchmark:** when modern full-spectrum predictors are reduced to MURU's exact frozen mu
endpoint, how accurately do they predict collision-energy-dependent fragmentation extent relative to MURU-WUR-v2?

## 0. Decision table

| | FIORA (default, FIORA-OS v1.0.0) | FIORA-OS v0.1.0 | ICEBERG 2.1 (MassSpecGym) | GLACIER (MassSpecGym) |
|---|---|---|---|---|
| Usable checkpoint | Yes, in repo, CLI default | Yes, shipped in the same repo at HEAD | Yes, public Dropbox (hash on download) | Yes, public Dropbox (contents and hash unverified) |
| Training provenance known | Library yes (Zenodo 16984129, all 9 MSnLib libraries); split membership **no** (unpublished, not reconstructible) | Yes (MSnLib v1.0, Zenodo 11163381, 4 libraries) | Yes (MassSpecGym 1.5, official MCES folds, published) | Yes (same MassSpecGym split) |
| PR #7 training overlap (of 1,794) | **1,794 (100%)** | 456 (25.4%), library-level | 454 in MassSpecGym (238 train, 120 val, 96 test) | same 454 |
| Strict-independent n (MURU-supported) | **0** | 1,337 compounds / 1,264 groups | 1,339 / 1,266 | 1,339 / 1,266 |
| NCE 20/60 representable | Yes (raw NCE, HCD) | Yes (raw NCE, HCD) | Yes (documented NCE to eV) | Yes (same) |
| Exact mu computable | Yes (linear probabilities, precursor emitted) | Yes on HEAD CLI (squares back); **no** on v0.1.2 CLI (bug) | Yes, after the upstream-defined square of the sqrt training scale; precursor root emitted | Conditional: sqrt scale as ICEBERG; root/precursor emission unverified |
| Include in primary | **No** | **Yes**, as the FIORA representative | **Yes** | **Yes**, conditional on pre-freeze check T3 |
| Reason | Every PR #7 compound is in its training universe and the 10% held-out test membership cannot be identified | Only clean public FIORA checkpoint; exact training library; passes the endpoint | Clean after structure exclusion; endpoint defined | Current Coley-group model, omitting it would date the comparison; must emit the intact-precursor peak |

**All-model common intersection** (FIORA-OS v0.1.0, ICEBERG 2.1, GLACIER, MURU): **1,327 compounds in 1,254
scaffold groups**. It differs from every pairwise clean population by at most 12 compounds, so the primary benchmark
should use this single common population (section 7).

## 1. Candidate comparator set and provenance

Full pins are in `artifacts/comparator_feasibility/comparator_provenance.json`. Code was read at the pinned commits.

### 1.1 FIORA (BAMeScience/fiora)

- **Code:** tag v1.1.0 = main HEAD `e19ef82c9a6cb9dbac92bce23e914008f1aeb44e` (2026-04-28). Earlier tags v1.0.1
  `94ec85e`, v1.0.0 `21dc75b`, v0.1.2 `53ac247`, v0.1.1 `8d26d13`, v0.1.0 `218014d`. Not on PyPI. MIT.
- **Checkpoints in `fiora/resources/models/`:**
  - `fiora_OS_v1.0.0.pt` (git blob `bfee085`, 53,845,076 B). CLI default (`predict.py`, `--model default`). Params:
    "FIORA OS v1.0.0", `training_library` "MSnLib v7", `training_label` compiled_probsALL (linear), RGCN depth 10,
    covariates collision_energy, molecular_weight, precursor_mode, instrument, element_composition.
  - `fiora_OS_v0.1.0.pt` (git blob `e53b447`, 39,533,372 B). Params: "trained on the MSnLib v1.0",
    `training_label` compiled_probsSQRT, depth 6. This is the open-source model of the Nature Communications 2025
    paper and was the CLI default through v0.1.2.
  - The main FIORA model (NIST'17 + MS-DIAL and others) is not released (commercial licensing). Not runnable.
- **Is the public default FIORA-OS?** Yes. It is FIORA-OS v1.0.0, a later retrain, not the paper's FIORA-OS.
- **Training data:**
  - v1.0.0: `resources/data/msnlib/download_msnlib.py` downloads `*_ms2.mgf` from Zenodo record 16984129
    (2025-08-28). Zenodo lists that record as version 6; FIORA calls it "v7". Its 72 library files are
    byte-identical (md5) to record 21105617, which adds only the compound-metadata parquet used here. All nine
    libraries are present, including MCEDIV and TargetMol HTS NP.
  - v0.1.0: MSnLib v1.0, Zenodo 11163381 (2024-05-09), libraries MCEBIO, NIHNP, MCESCAF, OTAVAPEP only.
- **Split:** by structure (`group_id`). Compounds found in a non-public reference file `datasplits_Jan24.csv` and the
  CASMI 2016/2016T/2022 lists keep their preset split. The rest go to `sklearn.train_test_split(random_state=42)`
  for 80/10/10 train/validation/test. The key order depends on upstream filters computed from spectra (coverage
  >= 0.5, precursor fraction <= 0.9, at least 2 matched peaks). The resulting `datasplits_msnlib_v7_Sep25.csv` is
  not published.
  - **Consequence:** FIORA-OS test membership cannot be reconstructed outcome-blind. It needs a non-public file plus
    the MSnLib spectra of the PR #7 compounds themselves, and even then it could not be verified against the shipped
    weights. So validation versus test membership is unknowable, and every compound in the training universe counts
    as trained-on.
- **Adducts:** [M+H]+, [M-H]-, [M]+, [M]-. **Instrument covariate:** one category, HCD, with an OTHERS slot.
- **Collision energy semantics (resolved, and different from the brief's premise):**
  - `fiora/MOL/collision_energy.py` defines `NCE_to_eV = nce * precursor_mz / 500 * charge_factor`, applied by
    `align_CE` to NIST/MoNA-style strings and to Orbitrap-type instrument names.
  - The FIORA-OS MSnLib loaders do not use it. `lib_loader/msnlib_loader.ipynb` at `218014d` sets
    `CE = Collision energy`; at `e19ef82` it sets `CE = mean(CE steps)`, and `preprocess_msnlib.py` does the same.
    All set `instrument = "HCD"`. `predict.py` passes `CE` through unchanged.
  - So the FIORA-OS checkpoints were trained with **raw MSnLib NCE numbers** as their CE input, and the documented
    native mapping for PR #7 is `CE = 20` and `CE = 60`, `Instrument_type = HCD`. The NCE to eV conversion belongs
    to FIORA's NIST-trained pipeline, whose weights are not public.
  - Covariates are normalized as CE/100 and MW/1000 and clamped.
- **Output intensity semantics:**
  - `SimulationFramework.simulate_spectrum` always emits the intact precursor at theoretical [M+H]+ with its
    predicted probability (`sim_probs[-1]`).
  - Fragments cover both sides of every single-bond break across 5 hydrogen modes; peaks with probability
    > `--min_prob` (default 0.001) are kept and identical fragments are summed.
  - Linear-label models get no renormalization. For compiled_probsSQRT models, `simulate_and_score` squares and
    max-scales the intensities.
  - **Defect found:** at v0.1.2 the square is written `sim_peaks["intensity"][i] == ...`, a no-op, so that CLI emits
    sqrt-scale intensities for v0.1.0. HEAD writes `=`. FIORA-OS v0.1.0 must therefore run on HEAD code.

### 1.2 ICEBERG 2.1 (coleygroup/ms-pred)

- **Code:** no tag or release for 2.1. Pin main HEAD `ed8311f22958cb37f055b663b5f56c5c77a2ee33` (2026-09-04). The
  README commit announcing ICEBERG 2.1 and GLACIER is `f7482f1` (2026-07-07). MIT.
- **Public checkpoints:**
  - MassSpecGym `msg_simulation` and `msg_all` (Dropbox folders in the README). File names and hashes are
    unverifiable without download.
  - NIST'20/23/26 weights are sent only on proof of a NIST licence, so they are not public.
- **Training data:** MassSpecGym 1.5 (`data_scripts/create_msg_simulation_dataset.py`,
  `DEFAULT_SOURCE_TABLE = .../MassSpecGym1.5.tsv`, LFS sha256 `50cfdd1d...`).
  - `msg_simulation` keeps `simulation_challenge == True` rows with a known CE. Split = MassSpecGym's `fold`
    column; `train_gen.py` fits on train and uses val for checkpoint monitoring.
  - `msg_all` additionally imputes missing CEs by matching predicted to experimental spectra, over all folds
    including test.
- **MassSpecGym is not independent of MSnLib.** Its dataset construction notebook 1 loads the Zenodo 11163381
  MSnLib v1.0 MSn MGFs, which are about a third of its molecules.
- **Adducts:** 14-slot embedding, but MassSpecGym has only [M+H]+ and [M+Na]+. **Instruments:** Orbitrap / QTOF /
  IT-FT / Unknown. **Limits:** `MAX_ATOM_CT = 160`; `VALID_ELEMENTS` (C N P O S Si I H Cl F Br B Se Fe Co As Na K);
  MassSpecGym precursor m/z <= 1000.
- **Collision energy semantics:**
  - The model input is absolute eV, embedded sinusoidally.
  - The documented conversion is `ms_pred.common.misc_utils.nce_to_ev`: `eV = NCE * precursor_mz / 500`. The
    ICEBERG paper states it, and `iceberg_elucidation.iceberg_prediction(nce=True)` applies it.
  - MassSpecGym's own construction (notebook 4, `convert_nce`) uses the same formula.
  - **Disclosed conflict:** that conversion only fires when the source CE string contains "%". Among MassSpecGym 1.5
    Orbitrap rows whose molecule is in an MSnLib v1.0 library, 84% of CE values are the integer MSnLib NCE ladder
    (60: 13,855; 20: 12,249; 30: 6,889; 45: 4,870; 15: 4,133; 75: 812). So the checkpoints saw MSnLib NCE numbers
    entered unconverted as "eV", alongside genuinely converted eV from other sources. Read from identity/metadata
    columns only.
- **Output semantics:**
  - Verified in `gen_model.predict_mol` and `joint_model.predict_mol`: the root fragment (intact molecule, initial
    probability 1, always retained) is part of the fragment set and gets a predicted intensity at every hydrogen
    shift, including the unshifted [M+H]+.
  - `predict_smis.py` keeps the top `sparse_k = 100` (fragment, shift) peaks with `threshold 0.0` and
    `max_nodes 100`; each CE is predicted separately.
  - Intensities are on the training scale. `process_spec_file` keeps peaks <= parent mass + 1 (precursor kept),
    max-normalizes, then applies `np.sqrt`, so the native output is sqrt(relative intensity).

### 1.3 GLACIER (coleygroup/ms-pred)

- **Paper:** "GLACIER: Rethinking Mass Spectrum Prediction as an Object Detection Problem", R.-X. Wang, R. Wang,
  C. W. Coley, arXiv 2606.29161 v1 (2026-06-28), not yet peer reviewed.
- **Code:** `src/ms_pred/glacier/` at `ed8311f` (the HEAD commit itself is "clarify glacier model weight link").
- **Checkpoint:** one public MassSpecGym-trained checkpoint (Dropbox). No NIST weights offered. Whether it is
  contrastive-finetuned is unverified.
- **Training data:** `configs/glacier/joint_train_msg.yaml` uses dataset `msg` with the MassSpecGym split and the
  same MAGMA-processed (sqrt) intensity targets. The committed `data/spec_datasets/msg/labels.tsv` carries raw
  MassSpecGym CE values. Overlap with PR #7 is identical to ICEBERG's.
- **CE:** raw float input with sinusoidal embedding; no conversion on the GLACIER path. The same documented ms-pred
  conversion applies, with the same training-encoding conflict.
- **Output:** per-fragment detections across 13 hydrogen-shift states, sparse top-k 100. The dataset placeholder
  `"precursor": 0.0` is a covariate slot, not a peak. **Whether the unbroken molecule is emitted with an intensity
  is not verified from code**; pre-freeze check T3 settles it.

## 2. Overlap audit method

`scripts/comparator_feasibility/01_overlap_and_support.py`. Identity is the parent InChIKey first block
(`identity.parent_connectivity_key`, stereo-agnostic), the same key PR #7 used.

- **MSnLib libraries:**
  - Every well listed for a PR #7 compound was mapped to its library through the Zenodo 21105617 compound-metadata
    parquet (md5 `fe0fd40f...` checked; only library, unique_sample_id and split_inchikey read; all wells mapped).
  - Every library holding the same key was added.
  - A compound counts as in a library release if either route hits.
  - The library-level rule does not condition on detection or spectral quality. Any compound of a training library
    is excluded, whether or not it reached that model's final training rows.
- **MassSpecGym 1.5:** `scripts/comparator_feasibility/02_fetch_massspecgym_identity.py`, run with explicit user
  authorization.
  - HTTP range reads of Hugging Face's parquet conversion of `data/MassSpecGym1.5.tsv` (convert revision `0bced33`,
    231,104 rows).
  - Only identifier, inchikey, fold, simulation_challenge, adduct, instrument_type and collision_energy were read.
  - The reader computed the byte intervals of every `mzs` and `intensities` column chunk from the footer, refused
    any overlapping range, and asserted afterwards that none was read. Total transferred: 4,314,135 of 133,354,917
    bytes (log in `massspecgym15_identity_fetch_record.json`). No MassSpecGym spectrum was downloaded.

**Results (1,794 frozen compounds):**

| Source | PR #7 compounds present |
|---|---|
| MSnLib Zenodo 16984129, 9 libraries (FIORA-OS v1.0.0) | 1,794 |
| MSnLib v1.0 Zenodo 11163381, 4 libraries (FIORA-OS v0.1.0) | 456 |
| MassSpecGym 1.5, any fold | 454 (train 238, val 120, test 96) |
| Cross-tab | 443 in both; 13 MSnLib v1.0 only (filtered out of MassSpecGym); 11 MassSpecGym only (GNPS/MoNA/MassBank) |

**Strictness rule (recommended):**
- A compound enters a competitor's clean population only if it is **absent** from that checkpoint's training release
  at the identity level.
- MassSpecGym test-fold compounds (96) are also excluded. The released weights cannot be checked for train-only
  fitting, and `msg_all`'s CE imputation touched test-fold spectra.
- The fold-aware alternative (exclude train and val only) would give 1,433 / 1,354 for ICEBERG and GLACIER. It is
  reported, not recommended.

## 3. MURU's canonical spectrum-to-mu transform and what a predicted spectrum must supply

`muru.wur_v2.external_multims2.spectrum_mu` (`src/muru/wur_v2/external_multims2.py:189-193`):

```python
def spectrum_mu(mz, intensity, m_prec):
    if mz.size == 0 or intensity.sum() <= 0:
        return float("nan")
    return float((intensity * mz).sum() / intensity.sum() / m_prec)
```

- **Required input:** one centroid peak list on a linear intensity scale with the intact precursor included; no
  intensity cutoff, window, sorting or merging. `m_prec` is the frozen theoretical [M+H]+ (`mh` column,
  `ExactMolWt(parent) + 1.007276`).
- **Measured side:** the per-(compound, rung) value is the median over matched scans (`10_one_look.py`). A predictor
  gives one spectrum per (compound, rung), so its mu is the single value.
- **Scale:** mu is invariant to a global intensity scale, so max- or sum-normalization is immaterial. A nonlinear
  intensity transform is not.

**Per competitor, on native output:**
- **FIORA-OS v1.0.0:** linear probabilities, precursor emitted. Exact mu defined as-is.
- **FIORA-OS v0.1.0:** HEAD CLI squares back to linear (FIORA's own code, keyed to the checkpoint's own
  `training_label`), precursor emitted. Exact mu defined as-is. On v0.1.2 code it is not (sqrt output, bug).
- **ICEBERG 2.1:** native intensities are sqrt(relative intensity) and the root [M+H]+ peak is emitted. Exact mu
  needs one transform, `I = inten ** 2`. It is fully determined by upstream code (`process_spec_file`: max-normalize,
  then `np.sqrt`), and it is the same principle FIORA applies to its own sqrt checkpoint. It is not a normalization,
  a peak insertion or a filter, and it has no free parameter. **Ratification item R1:** the preregistration must
  state this inverse explicitly. If the square is not accepted as native semantics, ICEBERG and GLACIER become
  unsupported for the primary, and passing sqrt intensities to `spectrum_mu` must not be done because that is a
  different endpoint.
- **GLACIER:** same as ICEBERG, if T3 shows the unbroken molecule is emitted. If no intact-precursor peak exists,
  exact mu is undefined and GLACIER is unsupported. No precursor peak may be inserted.

**Disclosed asymmetry (not fixed):**
- Measured spectra carry no peaks below the scan-window first mass (<= 40 m/z), and MURU was fit to such spectra.
  Competitors can emit fragments below 40 m/z.
- The frozen endpoint has no window, so none is applied. The expected effect is small (mass-weighted, low m/z) and
  it disfavours competitors. It is reported as a limitation.

## 4. Collision-energy mapping (frozen before predictions)

| Model | Native CE input | Frozen PR #7 mapping | NCE 20 | NCE 60 |
|---|---|---|---|---|
| MURU-WUR-v2 | LCSB eV scale via A0 | `E = (NCE + 5.95552603907965) / 0.8618030610784555` | 30.12 | 76.53 |
| FIORA-OS v0.1.0 | raw MSnLib NCE, `Instrument_type = HCD` | `CE = NCE` | 20 | 60 |
| ICEBERG 2.1 | absolute eV, instrument Orbitrap, adduct [M+H]+ | `eV = NCE * mh / 500` (`nce_to_ev`) | 5.72-41.42 | 17.17-124.26 |
| GLACIER | same as ICEBERG | same | same | same |

`mh` is the frozen theoretical [M+H]+ of each compound. No map was chosen, fit or compared on any data.

- **ICEBERG/GLACIER training-encoding conflict:** section 1.2 documents that MSnLib-derived training rows carry raw
  NCE numbers.
  - **Primary:** freeze the documented conversion, as the brief requires.
  - **Recommendation R2:** preregister one descriptive, non-decisional sensitivity row with `CE = NCE` as the model
    input, labelled as a training-encoding check. It never enters the ranking or decision rule. Declining it is also
    defensible. It must be decided before predictions, not after.

## 5. Support

- **MURU support** is the frozen protocol rule (profile knot range at both rungs, both frozen models). Structure-only:
  5 of 1,794 unsupported, leaving 1,789 in 1,687 groups, matching the committed PR #7 count.
- **FIORA:** parent exact mass <= 1,000 (covariate clamp and training filter). 1 compound unsupported (QXPYMYKHTLVJKY,
  parent 1,034.5 Da; MURU-supported).
- **ms-pred:** parse OK, single component, elements in `VALID_ELEMENTS`, <= 160 atoms with H, [M+H]+ <= 1,000.
  1 compound unsupported (the same QXPYMYKHTLVJKY, [M+H]+ 1,035.5). Element content of the population: C H N O S F Cl Br I P only.
- **At prediction time:** a compound for which a competitor produces no spectrum, or an empty or non-positive one,
  is counted and excluded from that competitor's pairwise population and from the intersection. It is never
  imputed. If failures exceed 2% of a population, report that prominently.

## 6. Sample sizes and outcome-blind novelty

Novelty = frozen PR #7 quartile bins of maximum Morgan-count Tanimoto (r2, 2048) to the 1,325 MURU development
compounds.

| Population | Compounds | Scaffold groups | Q1 (most novel) | Q2 | Q3 | Q4 | median max-sim |
|---|---|---|---|---|---|---|---|
| PR #7 frozen | 1,794 | 1,691 | 450 | 464 | 457 | 423 | 0.318 |
| PR #7 scored (MURU-supported) | 1,789 | 1,687 | 449 | 462 | 456 | 422 | 0.318 |
| FIORA-OS v1.0.0 clean | 0 | 0 | 0 | 0 | 0 | 0 | n/a |
| FIORA-OS v0.1.0 clean | 1,337 | 1,264 | 353 | 321 | 335 | 328 | 0.319 |
| ICEBERG 2.1 strict clean | 1,339 | 1,266 | 355 | 322 | 334 | 328 | 0.318 |
| GLACIER strict clean | 1,339 | 1,266 | 355 | 322 | 334 | 328 | 0.318 |
| ICEBERG/GLACIER fold-aware (not recommended) | 1,433 | 1,354 | 375 | 358 | 357 | 343 | 0.317 |
| **All-model intersection** | **1,327** | **1,254** | 351 | 319 | 333 | 324 | 0.318 |

- Largest scaffold group in the intersection: 6 compounds.
- Library mix of the intersection: MCEDIV 697, ENAMDISC 569, ENAMMOL 51, TargetMol 9, MCEDRUG 2. The clean
  population is almost entirely the MCE diversity and Enamine libraries that postdate MSnLib v1.0.
- Novelty relative to MURU is essentially unchanged by the exclusions. Novelty relative to each competitor's own
  training set was not computed; that would need MassSpecGym SMILES, which were outside the authorized columns.

## 7. Recommended frozen benchmark protocol (for the preregistration)

1. **Population:**
   - **Primary:** the all-model intersection, 1,327 compounds / 1,254 scaffold groups. The key list comes from
     `overlap_support_per_compound.csv` at this commit, minus any compound where a model fails at prediction time
     (counted).
   - Freeze the key-list hash before any prediction.
   - **Secondary:** each competitor on its own pairwise clean population (1,337 / 1,339 / 1,339), never ranked
     against each other.
2. **Models and pins:**
   - MURU-WUR-v2 `V2_TA_MORGAN_JOINT` (sha256 `11aa801c...`) with the A0 map; predictions via
     `candidate.predict_mu`, unchanged.
   - FIORA-OS v0.1.0 on FIORA `e19ef82` CLI defaults (`--min_prob 0.001`).
   - ICEBERG 2.1 `msg_simulation` on ms-pred `ed8311f` (`sparse_k 100`, `max_nodes 100`, `threshold 0.0`,
     instrument Orbitrap, adduct [M+H]+). Choose the spectrum-loss intensity checkpoint over a contrastive-finetuned
     one when both are present, because the endpoint is intensity-derived; record which files were used.
     `msg_simulation` is preferred over `msg_all` a priori, because its CE labels are annotated rather than imputed
     by spectral matching and CE is the construct under test.
   - GLACIER MassSpecGym checkpoint on `ed8311f` with its script defaults (`sparse_k 100`).
   - Structure input: canonical SMILES of `identity.parent_mol(smiles)` for every model.
   - Record sha256 of every downloaded checkpoint file in the preregistration before inference.
3. **Energy:** section 4, exactly. Rungs fixed at NCE 20 and NCE 60. The optional descriptive sensitivity row is
   per R2.
4. **Endpoint:**
   - `spectrum_mu(mz, I, mh)` on each predicted spectrum.
   - Linear intensity per section 3: FIORA as emitted by the HEAD CLI; ICEBERG/GLACIER `I = inten ** 2` per R1.
   - No peak insertion, filtering, window or renormalization.
   - Measured mu: the committed PR #7 per-(compound, rung) medians, used as-is.
5. **Metric:** PR #7's P1 (pooled two-rung RMSE, `muru.wur_v2.metrics.p1`) for every model on the same cells.
   - Primary contrast per competitor: `P1_ratio = P1_MURU / P1_competitor`.
   - Also reported per model, as in PR #7: P1 difference, MRMSE, median compound RMSE, Q90, Q95, CVaR95, AF (> 0.20),
     AF_max (> 0.30), per-rung RMSE and mean signed residual.
6. **Uncertainty:** whole-scaffold-group bootstrap over the 1,254 groups, B = 10,000, one seed fixed in the
   preregistration.
   - The same replicate weights are used for all models, and every statistic is recomputed per replicate.
   - Report 95% intervals and Bonferroni-simultaneous 98.33% intervals across the three primary contrasts.
7. **Decision labels per competitor, applied literally, simultaneous interval:**
   - upper < 1.00: **MURU more accurate**;
   - lower > 1.00: **competitor more accurate**;
   - otherwise **not distinguishable**.
   - The point ratio against 0.95 and 1.05 is reported as practical magnitude.
   - No model-level ranking is claimed beyond these pairwise labels on the common population.
8. **Secondary, descriptive:** NCE 20 and NCE 60 separately; the frozen PR #7 novelty quartiles within the
   intersection; pairwise clean populations; the R2 row if adopted. No other metrics.
9. **One look:**
   - Generate all competitor predictions blind to measured mu and commit the prediction tables with their hashes.
   - Then run the single frozen analysis.
   - **Do not compute MURU's P1 on any candidate subset before that freeze.** MURU's PR #7 errors are already
     exposed in aggregate, so the population and rules must be fixed first.
10. **Claim scope:** fragmentation extent as mu at fixed Orbitrap ID-X HCD NCE 20/60 on MSnLib screening
    compounds absent from every compared checkpoint's training release, for the specific public checkpoints
    named. Not full-spectrum similarity, not NIST-trained FIORA or ICEBERG, not other instruments.

### Pre-freeze technical checks (no PR #7 data, no benchmark predictions)

- **T1:** download the pinned checkpoints (needs explicit authorization) and record sha256.
- **T2:** run each model once on FIORA's upstream `examples/example_input.csv` [M+H]+ rows, whose keys must not be
  in PR #7. Confirm the model loads unmodified (FIORA-OS v0.1.0 on HEAD code), output is finite, repeated runs are
  bit-identical on the chosen device, and FIORA emits a squared linear scale for v0.1.0.
- **T3:** on the same molecules, confirm that ICEBERG and GLACIER output contains a root/unbroken-molecule peak at
  [M+H]+. If GLACIER has none, it is unsupported for the primary.
- **T4:** parse-only check that every intersection SMILES is accepted by each model's featurizer. Failures are
  counted at this point, before any prediction.

## 8. GLACIER and the 2026 state of the art

- GLACIER is the Coley group's newest spectrum simulator (preprint June 2026). ms-pred's README calls it "our
  state-of-the-art single-stage MS/MS simulator". The authors report it above ICEBERG 2.0 on MassSpecGym retrieval
  and NIST'20 cosine.
- A 2026 comparison that ran ICEBERG and FIORA but omitted a public, runnable GLACIER would be dated on arrival.
- The public checkpoint exists, its training split is the published MassSpecGym split, and its overlap with PR #7 is
  measured. It should be included.
- The only open question is whether it emits an intact-precursor intensity (T3). If it does not, it is excluded as
  unsupported with that reason stated, and the endpoint is not altered.
- The claims behind its SOTA status are the authors' own and not yet peer reviewed. The benchmark does not depend
  on them.

## 9. Why default FIORA cannot enter

- The PR #7 population was drawn from the nine MSnLib libraries, and FIORA-OS v1.0.0 was trained on exactly those
  libraries.
- Its roughly 10% test fold would contain about 180 PR #7 compounds, but which ones depends on an unpublished preset
  file and on filters computed from the PR #7 compounds' own spectra.
- Reconstructing it would expose benchmark outcomes and still could not be verified against the weights.
- Strict independence therefore gives n = 0. FIORA-OS v0.1.0 is the only public FIORA checkpoint whose training
  release excludes most of PR #7. That choice is made on provenance, before any prediction.
- It must be described as FIORA-OS v0.1.0, not "FIORA".

## 10. Residual risks

- Identity is by InChIKey first block. Tautomers and distinct registrations of the same parent that differ in the
  connectivity layer are not merged. PR #7 parents are neutral and design-standardized, so the risk is low.
- MSnLib v1.0 library membership is inferred from the 2025 cleaned plate metadata plus plate well membership, not
  from the 2024 v1.0 MGF headers. Structures deleted during later curation could escape. Checking those headers
  would mean downloading spectra-bearing MGFs.
- MassSpecGym spectra retaining the precursor peak is inferred from ms-pred's `process_spec_file` (peaks <= parent
  + 1 kept) and MassSpecGym's evaluation-only precursor removal, not from reading spectra.
- The ICEBERG/GLACIER CE training-encoding conflict (section 4) is intrinsic to the public checkpoints.
- Checkpoint file identities for ICEBERG and GLACIER are unverifiable until download (T1).

## 11. Files

- `scripts/comparator_feasibility/01_overlap_and_support.py`: overlap, support, populations and novelty.
- `scripts/comparator_feasibility/02_fetch_massspecgym_identity.py`: identity-only MassSpecGym range reader.
- `artifacts/comparator_feasibility/overlap_support_per_compound.csv` (sha256 `bf31cb02...`): per compound: MURU
  support, plated and key-level MSnLib libraries, MassSpecGym folds, model support facts, ICEBERG eV per rung, novelty.
- `artifacts/comparator_feasibility/overlap_support_summary.json` (sha256 `9ad592f6...`).
- `artifacts/comparator_feasibility/massspecgym15_identity.parquet` (MIT-licensed MassSpecGym identity columns,
  sha256 `88e2fd1d...`) and `massspecgym15_identity_fetch_record.json`.
- `artifacts/comparator_feasibility/comparator_provenance.json`: all pins and semantics.

Reproduce: `python3 scripts/comparator_feasibility/01_overlap_and_support.py --msnlib-parquet <Zenodo 21105617
20250828_9libraries_only_detected_cleaned.parquet>`.
