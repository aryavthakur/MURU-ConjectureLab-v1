# MURU collision-energy interface adjudication, Design A: PREREGISTRATION

Study id: `muru-ce-interface-adjudication-design-a`
Status: FROZEN, results-blind. Prediction generation and analysis are NOT authorized by this document alone.
Branch: `claude/muru-ce-interface-adjudication`. Freeze ref: `refs/muru-freeze/muru-ce-interface-adjudication-design-a`.

Supersedes, for Design A only, `MURU_CE_INTERFACE_ADJUDICATION_PREREGISTRATION_OUTLINE_DRAFT.md`. That outline proposed a calibration and evaluation split; the design fixed here is a single paired within-compound adjudication, because no parameter is fitted and no selection needs a held-out fold. The outline is retained unchanged as history.

Companion evidence, all outcome-blind and already committed: `MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md` (provenance, convention counts, model-internal CE handling), `MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md` (candidate conventions, dataset screens).

---

## 1. Question, scope and what this study cannot do

**Question.** Which discrete collision-energy input convention do the public ICEBERG 2.1 `msg_simulation` and GLACIER MassSpecGym checkpoints actually encode, judged by native full-spectrum prediction quality on independent spectra that were never part of their training data.

**Why it is open.** Phase 0 established that the checkpoints trained on one unit-free numeric energy column carrying both unconverted instrument NCE (at least 30,631 rows) and `NCE x precursor_mz / 500` conversions (23,894 rows), for one instrument class, with no per-row unit marker, and that ms-pred applies no conversion anywhere in the training path.

**Scope limits, binding.**

| Limit | Statement |
|---|---|
| Not a comparator evaluation | This study licenses no statement about relative model accuracy, and none about MURU. MURU does not participate. |
| Not a state-of-the-art claim | Nothing here supports a performance claim for any model. |
| Not universal | A population of this size from a single independent laboratory cannot establish a universally correct convention. Any SUPPORTED verdict is bounded to these checkpoints, this instrument class, [M+H]+, and the NCE cells used. |
| Not a MURU rung reproduction | The study uses NCE 30 and 60 because those are the independently available cells. These are not a substitute for MURU's frozen NCE 20 and 60 external interface, and results must never be described as a replacement external MURU benchmark. |
| No back-projection | Whatever this study finds, the closed comparator benchmark (PR #8) stays CLOSED and EXPOSED. Its numbers will not be recomputed, reranked or reinterpreted under any adjudicated convention, and none of its diagnostic rows becomes a confirmatory result. Any future MURU against modern-comparator claim requires a genuinely new independent population or a prospective acquisition. |
| Unresolved is a real outcome | `INTERFACE UNRESOLVED` is a fully reportable verdict. The decision rule never forces a selection among K1, K2 and K3. |

---

## 2. Authorization gates as resolved by the principal investigator

| Gate | Resolution | Consequence encoded in this document |
|---|---|---|
| G1 external peak files | ACCEPT CONDITIONALLY | Retrieval of the Eawag EQ spectrum files is authorized only after this preregistration, the exact population manifest, the analysis code, the model and checkpoint hashes and the decision rules are committed, pushed and freeze-tagged. Until that ref exists, metadata only: no download, inspection, parsing, summarizing or counting of peaks from candidate outcome records. |
| G2 sample size | ACCEPT FOR INTERFACE ADJUDICATION ONLY | The population size is accepted for a bounded adjudication, not for a universal convention claim or a new comparator claim. `INTERFACE UNRESOLVED` must remain available, and the study must not force a selection. |
| G3 energy cells | ACCEPT NCE 30 and 60 | The independently available NCE 30 and 60 cells are used instead of attempting to reproduce MURU's NCE 20 and 60 pair. |

---

## 3. The three frozen candidate mappings

For an acquisition setting `(NCE, precursor_mz)`, the float written into each checkpoint's `collision_energy` input is exactly one of:

| Id | Definition | Exact numerical semantics |
|---|---|---|
| K1 | raw NCE | `float(NCE)`, IEEE-754 binary64. For NCE 30 and 60 the value is exactly representable, so K1 is exact. |
| K2 | documented conversion | `float(NCE) * precursor_mz / 500.0`, evaluated in IEEE-754 binary64 in that association order (multiply first, then divide by 500.0), no rounding, no clamping. |
| K3 | integer-rounded conversion | `math.floor(K2)` returned as a float. Floor is toward negative infinity; all values here are positive, so it truncates. K3 is computed from the K2 double, never re-derived from a rounded intermediate. |

`precursor_mz` is the frozen theoretical [M+H]+ of the compound's representative structure, not the deposited value. No other candidate is admitted. Explicitly excluded, for the avoidance of doubt: fitted scale factors, additive offsets, interpolation rules, per-instrument tuning, per-model post-hoc conversions, round-half-even variants, imputed-energy conventions, and any convention introduced after this freeze.

---

## 4. Models

| Role | Model | Provenance |
|---|---|---|
| Primary | ICEBERG 2.1 `msg_simulation` (generator plus contrastive intensity model) | ms-pred HEAD ed8311f, checkpoints and sha256 as recorded in the comparator study's technical provenance and re-verified at execution |
| Primary | GLACIER MassSpecGym | same |
| Not used | FIORA-OS | FIORA does not share the MassSpecGym mixed-axis problem, so it cannot inform this adjudication and does not participate in the primary decision |
| Not used | MURU | The endpoint is deliberately independent of MURU's mu endpoint |

No retraining, no finetuning, no checkpoint modification. Both models see identical compounds, identical energy cells and identical mapping inputs.

---

## 5. Population, constructed outcome-blind and frozen

Built by `scripts/ce_interface_adjudication/design_a/10_build_population.py` from three metadata tables only. No record file, spectrum file or network fetch was involved, and no peak information of any kind entered any inclusion decision.

### 5.1 Final population

| Quantity | Value |
|---|---|
| Records | 69 |
| Compounds (MURU `parent_connectivity_key`) | 33 |
| Scaffold groups (`scaffold_group_v2`) | 33, every one a singleton |
| Records at NCE 30 | 34, covering all 33 compounds |
| Records at NCE 60 | 35, covering all 33 compounds |
| Records per compound | 2 for 31 compounds, 3 for 1, 4 for 1 |
| Instruments | Exploris 240 Orbitrap Thermo Scientific 44, Exploris 240 Thermo Scientific 21, Q Exactive Plus 4 |
| Resolutions | 17,500 on 44 records, 15,000 on 25 |
| Releases | 2025.10 on 32, 2024.11 on 25, 2024.06 on 12 |
| Theoretical [M+H]+ | 100.04 to 784.53, median 333.07 |

This reproduces the independently frozen C01 screen figure (tagged releases, conservative tier: 33 compounds in 33 groups) exactly, which is a check on the cascade rather than a new measurement.

Secondary figure, recorded and NOT used: admitting the unreleased dev pull request would give 91 records, 44 compounds, 44 groups. The preregistered population is tagged releases only, so that every record can be cited at a published MassBank release.

### 5.2 Inclusion rules, in binding order

Every one of the 5,051 input records carries its first failed rule in `population/design_a_exclusion_ledger.csv`.

| Rule | Condition | Records surviving | Compounds |
|---|---|---|---|
| R0 | Input, all Eawag EQ records | 5,051 | 507 |
| R1 | POSITIVE mode and precursor type exactly [M+H]+ | 3,295 | 415 |
| R2 | MS2, HCD, Orbitrap instrument type (LC-ESI-QFT or LC-ESI-ITFT; only LC-ESI-QFT occurs). QTOF excluded by design | 3,295 | 415 |
| R3 | Single-value `N % (nominal)` collision-energy form, NCE parses to a finite float. No ramps, lists or ranges | 3,295 | 415 |
| R4 | NCE exactly 30 or exactly 60 | 815 | 412 |
| R5 | First appears in a tagged release (2024.06, 2024.11, 2025.10) | 736 | 374 |
| R6 | Structural integrity: SMILES parses, both recorded InChIKey routes agree, parent formal charge 0, absolute theoretical [M+H]+ error below 0.01 Da | 734 | 374 |
| R7 | Model support: elements inside ms-pred `VALID_ELEMENTS`, heavy atoms at most `MAX_ATOM_CT` (160), theoretical [M+H]+ at most 995.556 (the ICEBERG training-label maximum) | 734 | 374 |
| R8 | Identity exclusions at compound level, each sub-rule logged: MassSpecGym 1.5 by recorded or parent key route, ms-pred `msg/labels.tsv`, the MURU exposure registry, any MURU exposed population, any MURU development population, PR #7, the comparator benchmark, plus the scaffold-group guards and the canonical-tautomer recheck | 70 | 34 |
| R9 | Cell completeness: at least one eligible record at NCE 30 AND at least one at NCE 60 | **69** | **33** |

R8 removals, marginal given this order: MassSpecGym recorded route 256 compounds, MURU exposure registry 29, the registry scaffold-group guard 54, the tautomer recheck 1 (clethodim, the known enol-tautomer leak that sits at Tanimoto 0.54 to its MassSpecGym counterpart and no similarity threshold would have caught). The final set is the union and is order-invariant; the per-sub-rule column is marginal and the counts file records both flagged and newly-removed for each. The formula-constrained skeleton key is computed and reported but is NOT binding; it removes nothing the tautomer route does not.

### 5.3 Frozen identity and value rules

| Item | Rule |
|---|---|
| Compound identifier | MURU `parent_connectivity_key`. The deposited InChIKey first block is carried for traceability only and never groups. |
| Representative structure | The lexicographically smallest RDKit canonical SMILES among the compound's surviving records. Defensive only: no compound in the population spans more than one canonical structure. |
| Model-input precursor | Theoretical [M+H]+ = `ExactMolWt(parent) + 1.00727646688`, the proton constant already used by the frozen C01 screen. The deposited PRECURSOR_M/Z is never used as a model input. Deposited minus theoretical, as a check only: median +9.4e-6 Da, range -4.5e-5 to +4.8e-5 Da. |
| Scaffold groups | Recomputed with `scaffold_key.py` under rdkit 2026.03.5. All 33 agree with the cached column. |
| Replicate records | All eligible records are retained. None is dropped for redundancy, quality, peak count or any other post-hoc reason. The reduction rule in section 8 defines how they combine. |

No peak count, spectrum quality, observed precursor intensity or prediction performance entered any rule above, and none may enter later. A record that proves technically unreadable after access is handled by the mechanical failure rule in section 8.5, not by judgement.

### 5.4 Two population facts that the preregistration records now

1. One compound (deoxyguanosine, `YKBGVTZYEHREMT`) carries a deposited precursor m/z 82.0127 Da away from its theoretical [M+H]+. Metadata alone cannot say whether the deposited precursor or the deposited structure is wrong, and the record may not be opened to find out. R6 excludes it either way. It is the only compound R6 removes.
2. One compound (`KHLRYLUKBJEYFH`) passes every identity rule but has no NCE 60 record, so R9 drops it. Admitting single-cell compounds would give 34, not 33. The design requires both cells so that every compound contributes the same energy structure.

---

## 6. Numerical separation of the three mappings, before any outcome

Computed from precursor masses and NCE metadata alone (`20_separation_diagnostics.py`). This is an identifiability diagnostic. It excludes nothing, and no compound is dropped because of it.

| Quantity, 66 cells pooled | median | q05 | q95 | range |
|---|---|---|---|---|
| \|K1 - K2\| | 16.74 | 4.21 | 43.82 | 1.36 to 48.00 |
| \|K2 - K3\| | 0.46 | 0.05 | 0.97 | below 1 by construction |
| \|K1 - K3\| | 16.50 | 4.00 | 44.00 | 1.00 to 48.00 |
| encoding distance d(K1, K2) | 4.94 | 4.05 | 5.76 | against 8.0 for a random phase pair |
| encoding distance d(K2, K3) | 0.70 | - | - | maximum 1.45 |
| encoding distance d(K1, K3) | 4.94 | 4.04 | 5.78 | - |

Separation is linear in NCE, so the 60 cell carries twice the leverage of the 30 cell (median \|K1 - K2\| 23.69 against 11.85). The encoding used is the checkpoints' own 64-dimension fixed sinusoid, re-implemented from the Phase 0 definition and self-checked against its published distances (d(20,12) = 4.3786, d(20,60) = 5.7624).

Null region: **1 compound of 33** has a theoretical [M+H]+ between 450 and 550 (522.60). Seven are within 400 to 600. No cell has \|K1 - K2\| below 1, one has it below 2, five below 5.

### 6.1 A priori identifiability statement, binding

This population separates K1 from K2 and K1 from K3 well, and separates K2 from K3 barely at all. K2 and K3 differ only by the fractional part of K2, bounded in [0, 1) by construction, giving a median encoding distance of 0.70 against 4.94 for the other two contrasts.

The consequence for the frozen decision rule in section 8.4 is stated now, before any outcome: a SUPPORTED verdict requires the winner to beat BOTH other mappings with a Bonferroni-adjusted interval wholly above zero. Because K2 and K3 are near-identical inputs here, neither can plausibly clear that bar against the other. The realistic outcomes of this study are therefore K1 SUPPORTED, or INTERFACE UNRESOLVED. The rule is not being altered to accommodate this; it is being disclosed so that an unresolved verdict is read correctly.

A further limitation, recorded in advance: with one compound in the 450 to 550 band, this population contains no usable negative control for the K1-against-K2 discrimination. The null-stratum check that Design B is meant to provide cannot be performed here, and no claim resting on it may be made from Design A.

A null or unresolved result may therefore mean that this external population lacks sufficient energy-axis leverage, and not that the checkpoints encode no distinguishable convention.

## 7. Prediction generation, frozen

Harness: `scripts/ce_interface_adjudication/design_a/30_run_predictions.py`, 40 unit tests in `design_a/tests/test_prediction_harness.py`, provenance of every inherited convention in `artifacts/ce_interface_adjudication/design_a/notes/prediction_harness_provenance.md`. Nothing has been executed against a model.

### 7.1 Design of the prediction grid

Six prediction sets: two models times three mappings. Each set covers every (compound, NCE cell) pair, so 33 compounds times 2 cells = 66 predictions per set, 396 predictions in total. Replicate records of the same compound at the same NCE share one prediction, because the model input is identical for them; replicates enter at the scoring stage (section 8.1), not here.

Spec id: `<compound_id>_NCE<nce>`. Row order is deterministic and byte-identical across runs.

### 7.2 Model inputs

| Field | Value | Note |
|---|---|---|
| `smiles` | the frozen representative structure | section 5.3 |
| `ionization` | `[M+H]+` | the population is [M+H]+ only |
| `instrument` | `Orbitrap` | FORCED, not chosen: it is the only ms-pred token for Orbitrap HCD, and GLACIER does not normalise an unrecognised token |
| `precursor` | frozen theoretical [M+H]+ | ICEBERG only; GLACIER's entry point never reads it |
| `collision_energies` | `str([repr(float(CE))])` | CE is K1, K2 or K3 of that cell, computed from the SAME theoretical [M+H]+ that fills the `precursor` field. The formatting is byte-identical to the comparator harness convention and is asserted by test |

Worked example from the emitted inputs, at NCE 30 with theoretical [M+H]+ 400.96067388088: K1 renders `['30.0']`, K2 renders `['24.0576404328528']`, K3 renders `['24.0']`. This is the whole of the manipulation: the three sets differ in one field and in nothing else.

### 7.3 Execution conventions, inherited from the frozen comparator harness

Seeded wrapper `seeded_run.py` with seed 42, applying `pl.seed_everything(seed, workers=True)` before the entry point. This is load-bearing: upstream `predict_smis.py` leaves its own seeding commented out and shuffles with Python `random`. Environment `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`. ICEBERG: `--sparse-out --sparse-k 100 --max-nodes 100 --threshold 0.0 --num-cpu-workers 0` with both checkpoints. GLACIER: `--sparse-out --sparse-k 100 --num-cpu-workers 0`. Native HDF5 output is dumped to JSON by the unchanged container parser. The native sparse top-100 output is preserved and no peak is ever synthesized, inserted or restored, exactly as in the comparator study.

Checkpoints, verified by file hash at freeze and to be re-verified at execution:

| Checkpoint | sha256 | Bytes |
|---|---|---|
| `iceberg21_msg_simulation/gen/best.ckpt` | `1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70` | 41,561,644 |
| `iceberg21_msg_simulation/inten_contr/best.ckpt` | `e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58` | 40,604,948 |
| `glacier_msg/best.ckpt` | `5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11` | 181,602,423 |

Code: ms-pred `ed8311f22958cb37f055b663b5f56c5c77a2ee33`, `uv sync --extra cpu`, `UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z`. No retraining, no finetuning, no checkpoint modification.

### 7.4 Deliberately not inherited from the comparator harness

FIORA in its entirety; the mu endpoint and everything that computes it; the comparator's two-condition eV-primary and raw-NCE-sensitivity structure, which Design A replaces with three symmetric mappings; the NCE 20 and 60 rungs, replaced by 30 and 60; the comparator's population constants; and `ckpt_hparams.py`, because it calls `torch.load` while the hyperparameters are already recorded verbatim in the technical provenance. Tests assert that none of these tokens appears in the harness or its manifest.

### 7.5 Execution preconditions, enforced in code

The execute mode raises a hard exit unless all three hold: `MURU_CE_ADJUDICATION_EXECUTE=1` is set, `refs/muru-freeze/muru-ce-interface-adjudication-design-a` resolves in git, and every input file matches its manifest sha256. Both refusal paths are covered by tests and were verified live.

### 7.6 Disclosed residual risk

ICEBERG's entry point shuffles its work list with Python `random`. Under the seeded wrapper the permutation should be identical across K1, K2 and K3 by construction, but that is an argument rather than a measurement on this population, and the comparator study's byte-determinism check was run on a different population. At execution, before any spectrum is scored, one mapping will be generated twice and the outputs compared byte for byte; a mismatch is a technical failure that halts the study under section 10.2 rather than something to be analysed away.

## 8. Endpoints, scoring and the frozen spectrum-matching procedure

The adjudication endpoint is deliberately independent of MURU's mu endpoint. MURU's mu, P1, per-rung mu error and every transformation derived from the closed comparator benchmark are excluded from this study by construction: none is computed, read or used anywhere in the pipeline.

### 8.1 Endpoints

| Role | Endpoint |
|---|---|
| Primary | Untransformed full-spectrum cosine similarity between each predicted spectrum and its observed external spectrum |
| Secondary, robustness only | Jensen-Shannon spectrum similarity, identical pipeline, cannot change the primary decision |

Both are native to the public evaluation semantics rather than invented here. MassSpecGym's own headline simulation metrics are untransformed cosine and Jensen-Shannon similarity, and ms-pred ships the same two functions; its `entropy_sim` and MassSpecGym's `js_sim` are algebraically the same function, differing only in the intensity space fed to them.

### 8.2 The frozen spectrum-matching procedure

Implemented in `scripts/ce_interface_adjudication/design_a/spectrum_similarity.py`, 68 unit tests, config sha256 `655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848`, pinned by a regression test so any later change to any convention fails. Full semantics with file:line evidence in `artifacts/ce_interface_adjudication/design_a/notes/similarity_semantics.md`.

| Convention | Frozen value |
|---|---|
| Binning | ms-pred's grid: 15,000 bins over 0 to 1500 Da, index `floor(mz * (num_bins - 1) / 1500) + 1`, bin width 0.10000666711114074 Da (not 0.1) |
| Tolerance | None, in either toolchain. Matching is fixed-grid bin coincidence. Two peaks closer than one bin width still miss if a boundary separates them |
| Pooling | `add`, with peaks lexsorted before reduction so the result is a function of the peak set and not of input order |
| Intensity inverse transform | `square`, applied to the PREDICTION side exactly once, and to nothing else. The observed side is supplied in linear units and is not transformed |
| Normalization | max, per spectrum, before binning. Order: drop non-finite, drop non-positive, mass cutoff, inverse transform, max normalize, bin, pool, precursor treatment |
| Precursor peak | KEPT, matching both upstream defaults. No peak is ever synthesized, inserted or restored |
| Mass cutoff | keep m/z at most (theoretical [M+H]+ plus 1.0 Da); parent mass comes from the frozen theoretical value, never from the deposited precursor |
| Sparse-output convention | The native ms-pred top-100 sparse output is preserved. An absent peak is scored as an exact zero, and the preregistration records what that means: a model zero, a peak outside the top 100, or a fragment never enumerated under the 100-node DAG cap |
| Degenerate cases | Empty spectrum 0.0, zero norm 0.0, disjoint support exactly 0.0, identical prepared spectra exactly 1.0, output clipped to [0, 1], non-finite peaks dropped, length mismatch raises |
| Jensen-Shannon | Natural log divided by ln 2, so the range is [0, 1]; sum (L1) normalization of the binned vector; a one-sided bin contributes exactly `p ln 2` |
| dtype | float64 throughout |

Ten deviations from upstream convention are documented in the semantics note, each with its reason. The four that matter scientifically: the endpoint is untransformed rather than sqrt-space (which is what the principal investigator preregistered, and is MassSpecGym's own headline convention); the inverse is asymmetric because only the prediction arrives in sqrt space; within-bin pooling is `add` rather than `max`, conserving within-bin ion current; and ms-pred's grid is used for both models, because comparability across the two comparators outranks fidelity to either upstream harness.

Disclosed and not adjusted for: GLACIER's own training hyperparameters record 150,000 bins over 1500 Da, a grid ten times finer than the evaluation grid used here, while ICEBERG's intensity model recorded binned targets with a cosine loss and a 20 ppm training tolerance. The evaluation grid is a property of the measurement, applied identically to both models and all three mappings, so it cannot favour a mapping; it is stated because it is a real difference from GLACIER's native resolution.

Two upstream questions resolved without running anything: no observed peak can exceed the 1500 Da limit, because the largest theoretical [M+H]+ in the population is 784.53; and the choice between the absolute and relative intensity column of a MassBank record cannot change either endpoint, because both are scale invariant.

### 8.2b The scoring step

`scripts/ce_interface_adjudication/design_a/40_score_spectra.py`, 50 unit tests on synthetic MassBank-format fixtures. It joins each population record to the prediction for its (compound, NCE) cell, for every model and mapping, and writes `artifacts/ce_interface_adjudication/design_a/scores/record_scores.csv` with the columns the analysis consumes, plus a sidecar manifest.

| Item | Frozen value |
|---|---|
| Row grid | (population record) x (2 models) x (3 mappings); `record_id` is `<accession>__<model>__<mapping>`, since the analysis refuses on duplicate ids |
| Observed intensity | Column 1 of the `PK$PEAK` triplet, the absolute intensity. Frozen even though both endpoints are scale invariant. MassBank's relative column is conventionally a rounded copy scaled to 999, which is the second reason the unrounded column is the one used |
| Prediction intensities | Left on ms-pred's sqrt scale, so the frozen layer's single square applies to the prediction side exactly once |
| Parent mass | The population's theoretical [M+H]+. A missing or unparseable deposited `PRECURSOR_M/Z` is deliberately NOT a drop, because dropping on it would be a filter this preregistration has not fixed |
| Numeric output | `repr(float)` round-tripping binary64, nothing rounded. Byte-identical across runs |

Six drop reasons, fixed strings, and no others: `unreadable_record`, `missing_pk_peak_block`, `malformed_peak_line`, `zero_peaks_after_parsing`, `missing_prediction`, `empty_prediction`. A missing records directory, a missing prediction dump or a duplicated spec id inside a dump is a hard refusal rather than a drop: the step either ran or it did not.

### 8.3 Reduction to one compound-level score per mapping, in this exact order

Let `x(r)` be the record-level similarity of record `r`.

1. **Replicate step.** For each (compound, model, mapping, NCE cell), the arithmetic unweighted mean of `x(r)` over that cell's surviving replicate records. This is the frozen replicate rule. All eligible replicates are used; none is dropped for redundancy or quality.
2. **NCE step.** `U(c, m, k) = ( V(c, m, k, 30) + V(c, m, k, 60) ) / 2`, equal weight for the two cells regardless of how many replicate records each contains.
3. **Model step.** `S_k(c) = ( U(c, ICEBERG, k) + U(c, GLACIER, k) ) / 2`.

This yields `S_K1(c)`, `S_K2(c)`, `S_K3(c)` for every analysed compound. The composite score `S_k` is the mean of `S_k(c)` over analysed compounds. The model step is the point of the design: the convention is a property of the shared checkpoint interface question, so the study must not select whichever convention flatters one model.

### 8.4 Resampling and contrasts

| Item | Frozen value |
|---|---|
| Comparison | Paired within compound. Every compound contributes all three mapping scores or none |
| Resampling unit | **Molecule (compound)**, decided from identities only and before any outcome exists: 0 of 33 compounds share a scaffold group, all 33 groups being singletons, which is below the frozen 0.10 threshold for nontrivial scaffold clustering. Had clustering been nontrivial, the whole-scaffold-group bootstrap would have applied; both code paths exist and are tested, and the rule with its counts is recorded in the result JSON |
| Replicates | B = 10,000, seed 20260916, weights drawn once per run as a multinomial over units and REUSED for all three contrasts and for the descriptive per-model contrasts. The weight matrix sha256 is recorded in the result. `D12 + D23 = D13` holds exactly and is asserted as the mechanical proof that the weights are shared |
| Contrasts | `D12 = S_K1 - S_K2`, `D13 = S_K1 - S_K3`, `D23 = S_K2 - S_K3` |
| Point estimate | The observed mean paired difference over analysed compounds, not the bootstrap mean |
| Intervals | Ordinary percentile 95 percent, reported descriptively; Bonferroni-adjusted percentile at 1 - 0.05/3 = 98.3333 percent, which is the primary interval for all three contrasts |

### 8.5 Frozen adjudication rule

A mapping is declared **SUPPORTED** only if both hold:

1. it has the highest observed primary composite cosine score, uniquely; and
2. the Bonferroni-adjusted interval for its paired advantage over EACH of the other two mappings lies wholly above zero, meaning a lower bound strictly greater than 0.0.

Otherwise the verdict is **INTERFACE UNRESOLVED**. An exact tie for the highest score fails criterion 1. The decision function has no branch that can return a mapping without both criteria, and is covered by tests that plant each failure mode. No rule may be constructed after seeing results.

Reported alongside, descriptively and never decisively: ICEBERG-only and GLACIER-only paired contrasts; a model-agreement check that compares the two models' orderings of K1, K2 and K3 and raises a prominent disagreement flag when they differ, surfaced in the result JSON, the printed summary and the verdict file even when the composite rule declares a mapping SUPPORTED; per-NCE-cell breakdowns; and the identical contrasts under Jensen-Shannon.

### 8.6 Mechanical failure rule, predeclared

1. A record is dropped if it carries a drop reason from the scoring step or if its similarity is missing or non-finite. Every drop is recorded with its reason.
2. The expected grid is 33 compounds by 2 models by 3 mappings by 2 NCE cells. Any expected cell with no surviving record is recorded as absent.
3. A compound that loses an entire cell for any model or mapping is dropped entirely from the primary analysis and counted. Because the drop is by compound, it removes that compound from all three mappings at once, so the comparison stays paired. This invariant is asserted by test.
4. Drops are mechanical. There is no quality filtering, no minimum peak count, no intensity threshold and no subjective exclusion at any point after the freeze.
5. The analysis refuses to run only if no compound survives at all.

## 9. Blinding, access record and the freeze chain

The study follows the same one-look discipline as the comparator benchmark.

| Step | Ref | Content |
|---|---|---|
| Freeze | `refs/muru-freeze/muru-ce-interface-adjudication-design-a` | This document, the population manifest, all analysis code, the tests, the frozen configurations and their hashes |
| Access record | `refs/muru-access/muru-ce-interface-adjudication-design-a` | Written and pushed before any spectrum file is retrieved, recording the freeze commit, the manifest hashes, the environment and the statement that no peak list had been read |
| Predictions | `refs/muru-predictions/muru-ce-interface-adjudication-design-a` | The six prediction sets (two models by three mappings), committed before the analysis runs |
| Result | `refs/muru-result/muru-ce-interface-adjudication-design-a` | The single analysis output |

Execution gates already built into the code: `30_run_predictions.py` refuses to execute without `MURU_CE_ADJUDICATION_EXECUTE=1`, the freeze ref, and a manifest hash match; `50_analysis.py` refuses without `MURU_CE_ADJUDICATION_ONE_LOOK=1`, the freeze ref, matching hashes and a mechanically complete score table.

---

## 10. Deviations policy

1. Any deviation from this document must be committed and pushed BEFORE the step it affects, as a numbered amendment, with its reason, and must state what it would have been.
2. A technical failure (a crash, an unreadable file, a non-converging run) may be retried with byte-identical inputs and code. A retry with any change is a deviation.
3. No rule, threshold, endpoint, reduction, mapping or decision criterion may be added, removed or altered after any outcome data has been read. The analysis runs once.
4. If the mechanical failure rule drops compounds, the count and the reasons are reported; the rule itself is not revisited.
5. Post hoc analyses are permitted only as explicitly labelled exploration, may never be presented as confirmatory, and may not change the verdict.

---

## 11. Design B remains the prospective confirmation

Design B is retained as the stronger follow-up and is NOT executed now: NCE 15 through 90 in steps of 5, broad precursor-mass coverage, deliberate low, mid and high m/z strata, a 450 to 550 near-null stratum where K1 and K2 converge, and enough compounds per mass stratum to separate a mapping effect from molecule-specific model error. Design A may inform the mapping hypothesis that Design B tests, but Design B requires its own preregistration before any acquisition.

---

## 12. What is deliberately not yet verified, and fails loudly if wrong

No candidate record has been opened, so the record format is frozen from the public MassBank specification rather than from an Eawag EQ record. Each item below is a declared expectation whose violation causes a loud, mechanical failure rather than a silent mis-score.

| Id | Expectation frozen now | Behaviour if it is wrong |
|---|---|---|
| X1 | The `PK$PEAK` column header is the canonical `m/z int. rel.int.` (whitespace collapsed, token spellings matter) | Every affected record drops as `malformed_peak_line`. The study can never score a column whose meaning is not the frozen one |
| X2 | The relative intensity column is a rounded copy of the absolute column | Inert: the absolute column is the frozen one |
| X3 | The peak block runs from the `PK$PEAK` line to the first blank line, `//`, tag line or end of file, with no blank line inside the block and no peak line continued across two physical lines | A truncated block becomes a `PK$NUM_PEAK` disagreement and drops as `malformed_peak_line` |
| X4 | Records are provisioned one file per accession, named by the population's `source_file` column, under a records directory given at execution. The `blob_sha` column is not checked by the scoring step | A missing directory is a hard refusal |
| X5 | Exactly one prediction dump entry exists per spec id | A duplicate is a hard refusal, not a silent selection |
| X6 | ICEBERG's internal shuffle produces an identical permutation across the three mappings under the seeded wrapper | Checked by byte comparison at execution before scoring; a mismatch halts the study as a technical failure |

If any of X1, X3 or X4 fires widely, the correct response is an amendment committed before re-running the scoring step, stating what the real format is, not a quiet parser fix.

---

## 13. Status and authorization

| Item | State |
|---|---|
| Population | Built, frozen, hashed. 33 compounds, 69 records, 33 singleton scaffold groups |
| Separation diagnostics | Computed and frozen. K1 against K2 has leverage; K2 against K3 has almost none |
| Similarity layer | Implemented, frozen, config hash pinned by test |
| Prediction harness | Implemented. Refuses to execute without authorization, the freeze ref and matching hashes |
| Scoring step | Implemented. Same refusals |
| Analysis and decision rule | Implemented. Refuses without the one-look variable, the freeze ref, matching hashes and a mechanically complete score table |
| Tests | 198 unit tests, all passing, entirely on synthetic data |
| Spectra accessed | NONE. No candidate peak list has been downloaded, opened, parsed, summarized or counted |
| Predictions generated | NONE |
| Analysis run | NEVER |

**Execution is NOT authorized by this document.** Retrieval of the Eawag EQ record files is the next step and requires explicit authorization from the principal investigator, per gate G1, now that this preregistration, the population manifest, the analysis code, the checkpoint hashes and the decision rules are committed, pushed and freeze-tagged.

Order of execution when authorized: provision records, write and push the access record, generate the six prediction sets and commit them, run the scoring step, run the analysis exactly once, commit the result. Each step is gated in code on the step before it.
