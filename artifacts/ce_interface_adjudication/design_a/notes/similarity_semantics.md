# Design A similarity semantics: what ms-pred and MassSpecGym actually compute

Study: MURU CE interface adjudication, Design A.
Phase: frozen spectrum-similarity layer, written before any adjudication-population
spectrum exists in this workspace.

Scope gate honoured in producing this document. No observed spectrum of the candidate
adjudication population was downloaded, opened, parsed or summarized. Only source code
and published configuration were read. Nothing under
`artifacts/comparator_benchmark/{result,predictions,prediction_verification}/`,
nothing under `/Users/aryav/muru-comparators/runs/`, and no `*_RESULT.md` was opened.

Every statement below is marked **VERIFIED** (read directly in the cited source) or
**INFERRED** (a conclusion drawn from verified code, with the inference stated).

Sources, with the exact revisions read:

- `ms-pred` at `/Users/aryav/muru-comparators/repos/ms-pred`, HEAD
  `ed8311f22958cb37f055b663b5f56c5c77a2ee33`. Cited as `ms-pred:<path>:<line>`.
- `MassSpecGym` at `github.com/pluskal-lab/MassSpecGym`, ref `main`, read through the
  GitHub contents API on 2026-09-16. Cited as `msg:<path>:<line>`.

Implementation that this document freezes:
`scripts/ce_interface_adjudication/design_a/spectrum_similarity.py`,
`FROZEN_CONFIG` sha256 `655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848`.

---

## 1. How ms-pred bins spectra for cosine evaluation

### 1.1 Bin count and upper mass limit

**VERIFIED.** The grid is 15000 bins spanning 0 to 1500 Da.

- `ms-pred:analysis/spec_pred_eval.py:20-21` -- `DEFAULT_NUM_BINS = 15000`,
  `DEFAULT_UPPER_LIMIT = 1500`.
- `ms-pred:src/ms_pred/iceberg/predict_smis.py:66-67` -- `--upper-limit` default 1500,
  `--num-bins` default 15000.
- `ms-pred:src/ms_pred/retrieval/retrieval_benchmark.py:191-192` -- same defaults.
- `ms-pred:src/ms_pred/common/misc_utils.py:210` -- `ensure_binned_spectrum` defaults
  `mass_upper_limit=1500, num_bins=15000`.

### 1.2 Bin index rule

**VERIFIED.** The scale is `(num_bins - 1) / upper_limit`, and the index is
`floor(mz * scale) + 1`, kept when `0 <= index < num_bins`.

- `ms-pred:src/ms_pred/common/misc_utils.py:2337` -- `scale = (num_bins - 1) / upper_limit`.
- `ms-pred:src/ms_pred/common/misc_utils.py:2346-2349` -- `bin_idx = np.floor(mz * scale).astype(np.int32) + 1`,
  then `valid = (bin_idx >= 0) & (bin_idx < num_bins)`.
- Identical rule in the sparse path,
  `ms-pred:src/ms_pred/common/misc_utils.py:180-184`.

**VERIFIED (derived).** With 15000 bins and a 1500 Da limit this makes the bin width
`1500 / 14999 = 0.10000666711114074` Da, not 0.1 Da. The `+ 1` offset means bin 0 is
never populated by a non-negative m/z.

### 1.3 Pooling function

**VERIFIED, and ms-pred is internally inconsistent about this.**

- Dense `bin_spectra` has signature default `pool_fn = "max"`
  (`ms-pred:src/ms_pred/common/misc_utils.py:2323`), implemented as
  `np.maximum.at` (`:2353-2355`), with `"add"` implemented as `np.bincount` weights (`:2351-2352`).
- Sparse `_bin_spec_sparse` has signature default `pool_fn = "add"`
  (`ms-pred:src/ms_pred/common/misc_utils.py:171`, implementation `:189-199`).
- `ensure_binned_spectrum`, which every `MassSpec.cos_sim` call goes through, defaults
  to `'add'` (`ms-pred:src/ms_pred/common/misc_utils.py:210`, reached lazily from the
  `binned_spec_sparse` property at `:438-440`).
- `analysis/spec_pred_eval.py:85` calls `common.bin_spectra([spec_ar], num_bins, upper_limit)`
  with no `pool_fn`, so that script's observed side is pooled by **max**.
- `retrieval_benchmark.py:193` exposes `--pool-fn` with default `"add"`.

**INFERRED.** The benchmark-facing path (`MassSpec.cos_sim`, `retrieval_benchmark`) is
add-pooled; only the standalone `spec_pred_eval.py` script is max-pooled. The
inference is that add is the intended convention for the object model and max is a
leftover default on the dense helper.

### 1.4 Tolerance: value, unit, and how it is applied

**VERIFIED.** There is **no tolerance parameter at all** in ms-pred's binned
evaluation. Two peaks match if and only if they land in the same bin of the fixed grid.
There is no symmetric plus-or-minus window, and nothing in the binned path is expressed
in ppm.

- `ms-pred:src/ms_pred/common/misc_utils.py:2346-2361` -- binning is a `floor` onto a
  fixed grid, followed by a pooled reduction. No neighbour search, no window.
- `ms-pred:analysis/spec_pred_eval.py:24-34` -- `cos_sim_fn` is a plain dot product over
  aligned dense vectors.
- `ms-pred:src/ms_pred/common/misc_utils.py:643-651` -- `_cos_sim_sparse` matches by
  exact integer bin index through a dictionary lookup.

**VERIFIED.** A ppm tolerance exists in ms-pred, but only in the **unbinned training
loss**, never in evaluation: `ms-pred:src/ms_pred/iceberg/inten_model.py:220`
(`self.mass_tol = self.ppm_tol * 1e-6`) used at `:275` and `:311` as
`tol = parent_mass * self.mass_tol`, inside `cos_loss` / `entropy_loss` when
`binned_targs` is false.

**VERIFIED (consequence).** Because the tolerance is grid coincidence and not a window,
the effective match width is exactly one bin (0.10000666711114074 Da here), and two
peaks separated by far less than one bin width still fail to match when a bin boundary
falls between them. This is a property of ms-pred's own evaluation, reproduced
deliberately, and it is tested at the boundary in
`tests/test_spectrum_similarity.py::test_peaks_inside_the_tolerance_match_and_outside_do_not`.

---

## 2. sqrt scale or linear, and where the sqrt is applied

### 2.1 The observed side

**VERIFIED.** ms-pred stores observed intensities already max-normalized and already
square-rooted. The full chain:

1. `ms-pred:src/ms_pred/common/misc_utils.py:2203` (or `:2216` in the unmerged branch)
   filters `mz <= parent_mass + 1`.
2. `:2207` (or `:2220`) divides by the maximum intensity.
3. `:2209-2210` (or `:2222-2223`) applies `np.sqrt` to the intensity column, with the
   comment `# Sqrt intensities here`.
4. `ms-pred:data_scripts/forms/01_assign_subformulae.py:353-361` routes each raw
   spectrum through `MassSpec.process_spec_file`, which is
   `ms-pred:src/ms_pred/common/misc_utils.py:587-603` and calls the function above.
5. `ms-pred:data_scripts/forms/01_assign_subformulae.py:329-337` then writes `ms2_inten`
   and `rel_inten` **without re-normalizing**; the renormalization and sqrt lines are
   commented out at `:331-332` with the note
   `# Use rel inten, but assume it's already been processed`.

So the `output_tbl["ms2_inten"]` and `output_tbl["rel_inten"]` columns that every
evaluator reads are on the sqrt-of-max-normalized-relative scale.

**VERIFIED.** `analysis/spec_pred_eval.py:82-85` reads `output_tbl["ms2_inten"]` and bins
it without further transform. The `norm_spectrum` call that would max-normalize and
sqrt again is explicitly commented out at `:88-89`, as is the equivalent at
`ms-pred:src/ms_pred/common/misc_utils.py:2257`. `norm_spectrum` itself is at
`:2293-2316` and does max-normalize first (`:2306-2311`) and sqrt second (`:2313-2314`).

### 2.2 The prediction side

**VERIFIED.** The intensity heads of both checkpoints end in a sigmoid and are trained
against the sqrt-scale targets above.

- ICEBERG: `ms-pred:src/ms_pred/iceberg/inten_model.py:226`, `:229`, `:234` --
  `self.output_activations = [nn.Sigmoid()]`; applied at `:694-699`.
- GLACIER: `ms-pred:src/ms_pred/glacier/joint_model.py:223` --
  `self.inten_activation = nn.Sigmoid()`.
- Targets: `ms-pred:src/ms_pred/iceberg/dag_data.py:222` and `:252` read
  `tree["raw_spec"]` / `tree.info["raw_spec"]`; GLACIER does the same at
  `ms-pred:src/ms_pred/glacier/dataset.py:105` and `:118`.
- `raw_spec` is built as `list(zip(true_tbl["mono_mass"], true_tbl["rel_inten"]))` at
  `ms-pred:data_scripts/dag/add_dag_intens.py:73`, that is, from the already sqrt'd
  column of section 2.1.

**INFERRED.** Therefore a released ICEBERG or GLACIER prediction intensity is on the
sqrt-of-relative-intensity scale, and squaring it once recovers linear relative
intensity. The inference is from the training pipeline, not from the checkpoint files
themselves; see UNRESOLVED U1.

### 2.3 Where the cosine is computed

**VERIFIED.** ms-pred's binned cosine is computed on those sqrt-scale values on both
sides, with no transform inside the metric. The metric only L2-normalizes.

- `ms-pred:analysis/spec_pred_eval.py:24-34` -- `cos_sim = dot / (norm_pred * norm_true)`
  with each norm floored at `1e-6` (`:31-32`).
- `ms-pred:src/ms_pred/common/misc_utils.py:643-651` -- sparse variant, norms floored by
  adding `1e-22` (`:649-650`), returns `0.0` when either side has no peaks (`:644-645`).

**VERIFIED.** ms-pred itself provides an opt-out that computes the endpoint on **linear**
intensities, by squaring the stored sqrt values:

- `ms-pred:src/ms_pred/retrieval/retrieval_benchmark.py:87-91` --
  `_transform_sparse_intensities(vals, sqrt_inten)` returns `vals` unchanged when
  `sqrt_inten` is true and `np.square(vals)` when it is false.
- `:211-217` -- the `--no-sqrt-inten` flag, help text
  "Square stored sqrt-intensity values before scoring, recovering original intensities.",
  default `sqrt_inten=True`.
- Applied symmetrically to both sides at `:102` / `:114` (cosine) and `:134` / `:149`
  (entropy).

---

## 3. Normalization, and its order relative to binning and the sqrt

**VERIFIED.** Per-spectrum normalization is by **maximum**, applied to the raw linear
intensities, **before** the sqrt and **before** binning:
`ms-pred:src/ms_pred/common/misc_utils.py:2207` then `:2210` (merged branch), `:2220`
then `:2223` (unmerged branch). The order in full is

    mass filter -> max normalize -> sqrt -> (persist) -> bin -> pool -> cosine

**VERIFIED.** Nothing renormalizes after binning. `spec_pred_eval.py:202-205` carries a
`# Don't norm spec` comment with the prediction-side max renormalization commented out,
and `:88-89` and `misc_utils.py:2257` carry the same for the observed side. The only
normalization the metric performs is the L2 division inside the cosine itself
(`spec_pred_eval.py:31-33`).

**VERIFIED (consequence).** Because both endpoints are invariant to a positive global
rescale, and because max normalization commutes with both the power transform and
add-pooling, the max-normalization step cannot change either endpoint value beyond
float rounding. It is frozen anyway so that the intermediate binned vectors are
reproducible.

---

## 4. Precursor peak and mass cutoff

### 4.1 Mass cutoff relative to the parent mass

**VERIFIED.** `ms-pred:src/ms_pred/common/misc_utils.py:2161` -- `process_spec_file(...,
exclude_parent=False)`.

- With `exclude_parent=False` (the default everywhere in the data pipeline):
  `:2203` keeps `mz <= parent_mass + 1`, and `:2216` does the same in the unmerged
  branch. So the precursor peak survives preprocessing.
- With `exclude_parent=True`: `:2201` keeps `mz <= parent_mass - 1`.
- `:2204` / `:2217` then drop any peak with intensity `<= 0`.
- `:2164-2167` -- a missing parent mass falls back to `1000000`, that is, no effective
  cutoff.

### 4.2 Precursor treatment in the evaluators

**VERIFIED.** The precursor peak is **kept** by default in every ms-pred evaluator:

- `ms-pred:analysis/spec_pred_eval.py:216` -- the headline `cos_sim` is computed on the
  unmodified vectors. A separate secondary metric `cos_sim_zero_pep` (`:239-242`) zeroes
  a **single bin** in both vectors, the bin `max_possible_bin` (`:231`), which is the
  largest bin index over all subformula masses of the true formula (`:224-226`). This is
  a formula-derived bin, not a measured precursor m/z.
- `ms-pred:src/ms_pred/retrieval/retrieval_benchmark.py:185-190` --
  `--ignore-parent-peak` default `False`.
- When enabled, `:753-755` sets
  `parent_mass_idx = (parent_mass - 1) * num_bins / upper_limit`, with
  `parent_mass = common.mass_from_smi(true_smi) + common.ion2mass[true_ion]` (`:752`),
  and `:49-52` / `:68-71` drop every bin with `index >= parent_mass_idx`.
- `ms-pred:src/ms_pred/common/misc_utils.py:619-627` -- the `MassSpec.cos_sim`
  `ignore_mass` path computes `max_ind = int(ignore_mass * (self._num_bins / self._mass_upper_limit))`
  and keeps `inds < max_ind`.

**VERIFIED defect, worth recording.** Both index rules use `num_bins / upper_limit`
(`= 10.0`) while the binning scale is `(num_bins - 1) / upper_limit` (`= 9.999333...`).
The two disagree by about one bin per 100 Da: roughly 2 bins at 300 Da and 6.7 bins at
1000 Da. The Design A default keeps the precursor, so this does not bind, but the
optional removal path in the frozen module reproduces ms-pred's rule exactly, defect and
all, rather than silently correcting it.

---

## 5. The sparse output convention of `predict_smis`

**VERIFIED, ICEBERG** (`ms-pred:src/ms_pred/iceberg/predict_smis.py`):

- `:38` `--sparse-out` (store_true, default False), `:40` `--sparse-k` default `100`,
  `:39` `--binned-out` (store_true, default False), `:64` `--threshold` default `0.0`,
  `:65` `--max-nodes` default `100`, `:66-67` `--upper-limit` 1500 / `--num-bins` 15000.
- `:253` asserts `sparse_out` is set on the write path.
- `:257-259` -- `best_inds = np.argsort(output_spec[:, 1], -1)[::-1][:sparse_k]`, then
  the spectrum is truncated to those rows. Selection is by **predicted intensity rank
  only**; there is no minimum-intensity filter at write time.
- `:262-273` -- the surviving `(mass, intensity)` rows are stored as a `MassSpec` with
  `masses` and `intens`; `num_bins` and `upper_limit` are stored as `None` unless
  `--binned-out` was passed.

**VERIFIED, GLACIER** (`ms-pred:src/ms_pred/glacier/predict_smis_joint.py`):

- `:78-79` same `--sparse-out` / `--sparse-k` 100; `:359` asserts
  `sparse_out must be True`.
- `:479` calls `model.predict_inten_frag_batch_sparse(batch, sparse_k)`, implemented at
  `ms-pred:src/ms_pred/glacier/joint_model.py:983-1044`: padded rows are masked to
  `-inf` (`:1025-1028`), `k = min(sparse_k, R)` (`:1030`), `torch.topk` by intensity
  (`:1031`), and `counts = clamp(num_rows, max=k)` (`:1039`) records how many rows are
  real.

**What this means for a peak absent from a prediction.** A released prediction is a
**truncated list of the k most intense predicted peaks**, not a thresholded full
spectrum. An m/z that does not appear is not a measurement of zero; it is either a
genuine model zero, or a real prediction that fell outside the top 100, or an m/z whose
fragment was never enumerated because the DAG was capped at `--max-nodes 100`. For the
similarity endpoint the three are indistinguishable and all are treated as exact zeros.
`--threshold 0.0` means no probability pruning of the fragment DAG, so the cap that
binds is `--max-nodes`, not the threshold. **VERIFIED** from the flags above;
**INFERRED** only as to which cap binds in practice.

The Design A prediction harness already fixes these flags:
`scripts/ce_interface_adjudication/design_a/30_run_predictions.py:70` runs ICEBERG with
`--sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0` and `:75` runs GLACIER with
`--sparse-out --sparse-k 100`. **VERIFIED** (code read, no outputs read).

Note for completeness: `spec_pred_eval.py:61-69` and `:208-214` apply a separate
`--min-inten 1e-5` and `--max-peaks 20` truncation, but only on the **binned prediction**
path that that script consumes. It is not part of the sparse write convention and is not
part of the Design A endpoint.

---

## 6. MassSpecGym's own simulation-challenge metrics

### 6.1 Which metrics

**VERIFIED.** Four similarity metrics plus retrieval hit rate.

- `msg:config/simulation/template.yml` `sim_metrics:` block -- `cos_sim`, `js_sim`,
  `cos_sim_sqrt`, `cos_sim_obj`; `at_ks: [1, 5, 20]`.
- `msg:massspecgym/models/simulation/base.py:163-197` -- construction of all four.
  `:387` asserts `cos_sim` is always present.

### 6.2 The headline `cos_sim` is UNTRANSFORMED

**VERIFIED.** `msg:massspecgym/models/simulation/base.py:165-179`:

```
# untransformed
def no_transform_fn(logprobs, batch_idxs):
    probs = self.ints_untransform_func(torch.exp(logprobs), batch_idxs)
    logprobs = safelog(self.ints_normalize_func(probs, batch_idxs))
    return logprobs
self.cos_sim_fn = get_cos_sim_fn(deepcopy(no_transform_fn), ...)
self.js_sim_fn  = get_js_sim_fn(deepcopy(no_transform_fn), ...)
```

The training-space intensity transform is inverted before scoring
(`ints_untransform_func`, `msg:massspecgym/simulation_utils/spec_utils.py:48-80`; the
`sqrt` case is literally `x**2` at `:61`), then L1-normalized
(`batched_l1_normalize`, `spec_utils.py:238-244`). `cos_sim_sqrt`
(`base.py:181-190`) is the secondary sqrt-space variant and `cos_sim_obj`
(`base.py:192-197`) scores in the training objective's own space.

So MassSpecGym's headline simulation metric is cosine on untransformed linear relative
intensities, which is exactly the space this study preregisters.

### 6.3 `js_sim`

**VERIFIED.** `msg:massspecgym/simulation_utils/spec_utils.py:247-294` (`js_sim_helper`)
and `:296-336` (`sparse_jensen_shannon_similarity`):

- both sides L1 normalized (`:258-265`);
- union support, `m = 0.5 * (p + q)` (`:267-273`);
- `kl1`, `kl2` by `p * (log p - log m)` summed per spectrum (`:274-289`);
- `jsd = 0.5 * (kl1 + kl2)` (`:291`), `jss = 1 - jsd / LN_2` (`:293`), with
  `LN_2 = float(np.log(2.))` at `:28`.

So the log is natural and the divisor is `ln 2`, giving range `[0, 1]`.

**VERIFIED (algebra).** ms-pred's `entropy_sim`
(`ms-pred:analysis/spec_pred_eval.py:37-51`) writes
`1 - (2 H(m) - H(p) - H(q)) / ln 4`. Since `JSD = H(m) - (H(p) + H(q)) / 2`, we have
`2 H(m) - H(p) - H(q) = 2 JSD`, so `entropy_sim = 1 - 2 JSD / ln 4 = 1 - JSD / ln 2`.
**ms-pred's `entropy_sim` and MassSpecGym's `js_sim` are the same function.** They
differ only in the intensity space each is fed: ms-pred feeds it sqrt-scale values,
MassSpecGym feeds it untransformed ones. This is why the study's secondary endpoint can
be simultaneously native to both toolchains.

### 6.4 MassSpecGym binning and tolerance

**VERIFIED.** `msg:massspecgym/simulation_utils/spec_utils.py:83-167` (`batched_bin_func`):

- `:113` -- `bins = torch.arange(mz_bin_res, mz_max + mz_bin_res, step=mz_bin_res)`;
- `:115` -- `bin_idxs = torch.searchsorted(bins, mzs, side="right")`;
- `:111` -- asserts `max(mzs) < mz_max`.

Fixed width, no tolerance window, no ppm, exactly as in ms-pred but on a different grid.

Grid values: module constants are `MZ_MAX = 1500.0` and `MZ_BIN_RES = 0.01`
(`spec_utils.py:25-26`), but the shipped configs use `mz_max: 1005.` and
`mz_bin_res: 0.1` (`msg:config/simulation/template.yml`), with an input m/z window of
`mz_from: 10.` to `mz_to: 1000.` in the same file. **VERIFIED**; the module constants
are unused defaults.

Pooling for the similarity path is `agg="lse"`, that is, logsumexp in log space
(`spec_utils.py:188`, `:196`, implementation `:137-142`), which is **summation** in
probability space. `"sum"` and `"amax"` are the alternatives (`:129`, `:146`).

### 6.5 MassSpecGym precursor treatment

**VERIFIED.** `batched_bin_func` has a `remove_prec_peaks` option
(`spec_utils.py:91-92`, `:118-125`) that zeroes the intensity of any peak landing in the
precursor's own bin. Neither `sparse_cosine_distance` (`:182-199`) nor
`sparse_jensen_shannon_similarity` (`:308-325`) ever passes it. MassSpecGym's reported
`cos_sim` and `js_sim` therefore **keep the precursor peak**, and there is no
parent-mass cutoff of the kind ms-pred applies.

### 6.6 Hit rate

**VERIFIED.** `msg:massspecgym/models/simulation/base.py:412-457`. Candidates are scored
with the same untransformed `cos_sim` (`:239-246`), then
`torchmetrics.functional.retrieval.hit_rate.retrieval_hit_rate` is evaluated at each
`at_k` in `[1, 5, 20]` (`:441-445`). Ties are broken by adding
`1e-5 * torch.randn_like(scores)` at `:437`, so MassSpecGym's hit rate is **not
deterministic across runs**. This is a retrieval metric and is not part of Design A.

### 6.7 Where MassSpecGym and ms-pred differ

| Convention | ms-pred | MassSpecGym |
| --- | --- | --- |
| bin width | `1500/14999 = 0.10000667` Da | `0.1` Da exactly (config) |
| upper limit | 1500 Da | 1005 Da (config), 10 to 1000 Da input window |
| bin index rule | `floor(mz * (n-1)/limit) + 1` | `searchsorted(bins, mz, side="right")` |
| tolerance | none, grid coincidence | none, grid coincidence |
| pooling | `add` (object model) / `max` (spec_pred_eval) | `sum`, via logsumexp in log space |
| headline intensity space | sqrt, with `--no-sqrt-inten` to opt out | untransformed |
| per-spectrum normalization | max, before the sqrt and before binning | L1, after untransforming |
| JS-type metric | `entropy_sim`, algebraically identical, sqrt space | `js_sim`, untransformed |
| precursor | kept by default; optional cutoff at `parent - 1` | kept, no cutoff |

---

## 7. The frozen Design A configuration, and every deviation

The frozen configuration is the `FROZEN_CONFIG` dict in
`scripts/ce_interface_adjudication/design_a/spectrum_similarity.py`, sha256
`655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848`.

| Convention | Frozen value | Follows |
| --- | --- | --- |
| bin count | 15000 | ms-pred |
| mass upper limit | 1500.0 Da | ms-pred |
| bin index rule | `floor(mz * (num_bins - 1) / limit) + 1`, keep `0 <= i < num_bins` | ms-pred |
| bin width, that is the tolerance | 0.10000666711114074 Da | ms-pred, derived |
| tolerance unit | Da | ms-pred |
| tolerance application | fixed-grid bin coincidence, no window, no ppm | ms-pred and MassSpecGym |
| pooling | `add` | ms-pred object model, MassSpecGym |
| prediction inverse transform | `square`, applied exactly once | study deviation D1/D2 |
| observation inverse transform | `identity` | study deviation D2 |
| normalization | `max`, per spectrum | ms-pred |
| normalization order | drop non-finite, drop non-positive, mass cutoff, inverse transform, max normalize, bin, pool, precursor treatment | ms-pred order, with the study's explicit ingest guards prepended |
| precursor treatment | `keep` | ms-pred default, MassSpecGym |
| mass cutoff | `mz <= parent_mass + 1.0` when a parent mass is given, otherwise none | ms-pred |
| precursor removal (optional) | drop bins with index `>= int((parent_mass - 1.0) * num_bins / limit)` | ms-pred, defect preserved |
| low m/z cutoff | none | ms-pred (MassSpecGym would filter below 10 Da) |
| non-finite values | drop the peak | study, D8 |
| non-positive intensity | drop the peak | ms-pred (`:2204`) plus explicit negatives |
| empty spectrum, either side | 0.0 | study, D7 |
| zero-norm vector | 0.0 | study, D7 |
| disjoint supports | exactly 0.0 | study, D7 |
| bit-identical prepared spectra | exactly 1.0 | study, D7 |
| output clip | `[0.0, 1.0]` | study, D7 |
| length mismatch | raise `ValueError` | study |
| JS log base | natural log, divided by `ln 2`, range `[0, 1]` | MassSpecGym, and ms-pred `entropy_sim` |
| JS probability normalization | sum (L1) | MassSpecGym |
| JS zero handling | a bin on one side only contributes `p * ln 2`; `0 * ln(0/m) := 0` | MassSpecGym |
| dtype | `float64` | study deviation D4 |

### Deviations from ms-pred's or MassSpecGym's own convention, with reasons

**D1. Untransformed rather than sqrt-space cosine.**
ms-pred's headline binned cosine compares both sides in sqrt space
(`spec_pred_eval.py:216`, feeding values produced by `misc_utils.py:2210`). Design A
preregisters an **untransformed** endpoint, so the prediction is squared back to linear
first. This is not an invention: ms-pred ships `--no-sqrt-inten` to do exactly this
(`retrieval_benchmark.py:87-91`, `:211-217`), and MassSpecGym's own headline
simulation metric is the untransformed one (`msg base.py:165-174`). Reason: the study
needs an endpoint that is independent of MURU's mu endpoint and that is not distorted by
a variance-stabilizing transform when comparing across collision energies, where the
intensity dynamic range itself is the thing under test.

**D2. The inverse transform is asymmetric: prediction only.**
ms-pred applies the sqrt symmetrically because both sides are routed through
`common.process_spec_file`. Design A supplies the observed side in linear relative
intensity directly from the source record, never through `process_spec_file`, so
applying a square to it would be a transform, not an inverse. `pred_inverse_transform`
is `square` and `obs_inverse_transform` is `identity`, both named and frozen, and both
are tested. Reason: the transform is inverted exactly once in total, which is what
"untransformed" means.

**D3. `add` pooling rather than `max`.**
`analysis/spec_pred_eval.py:85` pools the observed side by `max` (via the dense
`bin_spectra` default at `misc_utils.py:2323`). Design A freezes `add`, matching
`ensure_binned_spectrum` (`misc_utils.py:210`), `retrieval_benchmark.py:193` and
MassSpecGym's summation. Reason: `add` conserves total ion current within a bin, `max`
does not, and `add` is what the two benchmark-facing paths and MassSpecGym all use.

**D4. `float64` rather than `float32`.**
ms-pred stores and compares binned intensities as `float32`
(`misc_utils.py:113`, `:137`, `:622`, `:627`). Design A computes in `float64`. Reason:
the endpoint is frozen and must be bit-reproducible, and the `float32` epsilon is within
an order of magnitude of the effect sizes the adjudication is expected to resolve.

**D5. ms-pred's grid, not MassSpecGym's.**
The GLACIER checkpoint is the MassSpecGym-trained one, but it is an ms-pred checkpoint
run through ms-pred's `predict_smis_joint`, and it emits ms-pred sparse peak lists.
Design A therefore uses ms-pred's grid (15000 bins to 1500 Da) for both models, so the
two comparators are scored identically. Reason: comparability across the two
checkpoints outranks fidelity to either upstream evaluation harness, and both harnesses
agree on the only semantically load-bearing point, which is that matching is grid
coincidence.

**D6. Canonical within-bin summation order.**
ms-pred pools with `np.bincount` / `np.add.at` (`misc_utils.py:2352`, `:191`), whose
floating-point result depends on the order the caller supplied the peaks in. Design A
lexicographically sorts by `(bin index, intensity, mz)` before reducing, so the result
is a function of the peak set and not of the peak order. Reason: no analysis-time
judgement, and bit-identical results under any reordering of the prediction file. This
is tested.

**D7. Exact degenerate values and clipping instead of epsilons.**
ms-pred floors norms at `1e-6` (`spec_pred_eval.py:31-32`) or adds `1e-22`
(`misc_utils.py:649-650`), which quietly turns an empty spectrum into a very small
non-zero denominator. Design A instead defines the degenerate cases explicitly: an empty
side, a zero-norm side, or a spectrum emptied by filtering returns `0.0`; disjoint
supports return exactly `0.0`; bit-identical prepared spectra return exactly `1.0`; every
other value is clipped into `[0, 1]`. Reason: these must be mechanical and decided
before any real data exists, and no endpoint may ever return `NaN`.

**D8. Non-finite peaks are dropped.**
Neither toolchain guards against `NaN` or `inf` in an input peak list. Design A drops any
peak with a non-finite m/z or a non-finite intensity, and if that empties a spectrum the
degenerate rule above applies. Reason: mechanical, and it removes the only route by which
a `NaN` could reach the endpoint.

**D9. MassSpecGym L1-normalizes before cosine; Design A max-normalizes before binning.**
Both endpoints are scale invariant, so this cannot change either value beyond rounding.
Design A follows ms-pred's max normalization because the prediction side arrives on
ms-pred's max-normalized scale and the intermediate binned vectors should be directly
comparable to ms-pred's.

**D10. No low m/z cutoff.**
MassSpecGym filters the input window to 10 to 1000 Da
(`config/simulation/template.yml`). Design A applies no low m/z cutoff, matching
ms-pred, and uses only the 1500 Da upper limit plus the parent-mass cutoff.

---

## 8. Degenerate cases, decided now

All of these are frozen in `FROZEN_CONFIG` and covered by the test suite. None of them
requires a judgement at analysis time, and none of them can return `NaN`.

| Case | Value |
| --- | --- |
| prediction has zero peaks | `0.0` |
| prediction has zero peaks after filtering (all non-positive, all non-finite, all above the mass cutoff, all above the upper limit) | `0.0` |
| observation has zero peaks, before or after filtering | `0.0` |
| both sides empty | `0.0` |
| zero-norm vector on either side | `0.0` |
| supports disjoint after binning | exactly `0.0` |
| prepared vectors bit-identical | exactly `1.0` |
| any individual non-finite m/z or intensity | that peak is dropped, the rest of the spectrum is scored |
| negative intensities | dropped before the inverse transform, so a square can never turn a negative into a positive peak |
| computed value outside `[0, 1]` by rounding | clipped into `[0, 1]` |
| a non-finite computed value | `0.0` |
| `mz` and intensity arrays of different length | `ValueError`, this is a caller bug and not a data degeneracy |
| `parent_mass` is `None` | no mass cutoff; precursor removal, if requested, raises |

---

## 9. UNRESOLVED

**U1. The checkpoints' own intensity conventions.**
Section 2.2 concludes that ICEBERG and GLACIER predictions are on the
sqrt-of-relative-intensity scale by tracing the training pipeline, which is VERIFIED. The
checkpoints themselves were not opened. A later phase must read the Lightning
`hyper_parameters` of both checkpoints and confirm `loss_fn` (`cosine`, `entropy`, or
`weighted_entropy`), `binned_targs`, `ppm_tol`, `include_unshifted_mz` and
`embed_instrument`. If either checkpoint was trained with `binned_targs=True`, the
target is the binned vector rather than the peak list and the normalization that reaches
the sigmoid differs. This does not change the endpoint definition, which is frozen, but
it changes the interpretation of the `square` inverse.

**U2. Whether the sparse prediction output is max-normalized at write time.**
Nothing in `iceberg/predict_smis.py` or `glacier/predict_smis_joint.py` renormalizes the
sigmoid outputs before writing, and the sigmoid is applied per bin without a
per-spectrum constraint (`inten_model.py:694-699`). So the base peak of a released
prediction need not be 1.0, and Design A's `max` normalization step is load-bearing
rather than inert relabelling. INFERRED from the absence of a renormalization, not
positively verified. A later phase can confirm on the study's own synthetic-input
predictions without touching any observed spectrum.

**U3. The parent-mass convention for the precursor-removal index.**
`retrieval_benchmark.py:752` builds `parent_mass` as neutral mass plus adduct mass and
does not subtract the electron mass, whereas ICEBERG's fragment m/z values do carry an
`ELECTRON_MASS` term (`iceberg/joint_model.py:142-148`). The two differ by about
0.00055 Da, which is well inside one bin, so it is almost certainly immaterial. It does
not bind at all under the frozen default, which keeps the precursor, but it would bind if
precursor removal were ever switched on, and it should be resolved before that happens.

**U4. The intensity units of the observed side as the study will read them.**
The endpoint is invariant to the absolute scale of the observed side, so nothing here
affects the result. What the frozen module does assume is that a single, consistent
intensity column is passed, that its values are linear (not already square-rooted, not
log-scaled) and that a peak list for one record is passed in one call. A later phase must
confirm which column of the source record satisfies this, and must do so from the record
schema rather than from the values.

**U5. Whether any adjudication record's observed peak list can exceed 1500 Da.**
Peaks above the upper limit are silently dropped by the bin validity rule, in both
toolchains and in the frozen module. For `[M+H]+` records this is expected to be vacuous,
but it has not been checked against the population, and checking it requires only the
precursor m/z column, not any spectrum.
