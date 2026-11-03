# Structural Features for Predicting Collision-Energy-Dependent Fragmentation Extent: Development and Independent Confirmation of MURU-WUR-v2

**Aryav Thakur**
Affiliation: not specified in the verified project records.
Internal research draft; not submitted to a journal.

## Abstract

**Background and objective.** Collision-induced dissociation changes the fragment-ion distribution with collision energy. This study asks whether molecular structure improves prediction of a compact fragmentation-extent endpoint beyond a physicochemical descriptor baseline, and whether the development gain transfers to an independently sampled library. **Methods.** MURU-WUR-v2 predicts a one-scale trajectory of the precursor-including, intensity-weighted fragment-mass fraction, μ, using 12 Tier A descriptors and radius-2 Morgan count features. A frozen shared energy-response profile maps the predicted molecular scale to μ. The model was selected in a multi-experiment, scaffold-grouped development program. After disclosing and excluding an exposed earlier sample, we evaluated it once on the replacement MSnLib population at fixed HCD NCE 20 and 60. The comparison used the frozen Tier A ridge reference and a whole-scaffold bootstrap. **Results.** Of 1,794 measured compounds, 5 were outside the joint model support; 1,789 compounds in 1,687 scaffold groups were scored. External pooled trajectory RMSE was 0.12961 for MURU and 0.13353 for the reference (ratio 0.97067; 95% scaffold-bootstrap interval 0.95236–0.98927), a 2.93% relative reduction. The prespecified 5% practical-improvement criterion was not met. Tail-error metrics were similar, and the least-similar structural quartile had a ratio of 1.0083. **Conclusion.** The findings support modest external confirmation of a structural scale predictor for this endpoint and domain, but not a practically meaningful improvement, tail-risk benefit, or transfer to the most novel quartile. Collision-energy-interface adjudication remains unresolved, and comparisons with full-spectrum predictors are conditional on their energy-input convention.

**Keywords:** tandem mass spectrometry; collision-induced dissociation; fragmentation extent; molecular descriptors; Morgan fingerprints; external validation; scaffold bootstrap

## 1. Introduction

Tandem mass spectrometry (MS/MS) isolates a precursor ion, activates it, and measures product ions by mass-to-charge ratio. In collision-induced dissociation (CID), energy is transferred through collisions with a neutral gas; the observed product-ion distribution depends on precursor structure and charge, collision conditions, and instrument settings. Higher-energy collision-induced dissociation (HCD) is commonly used on Orbitrap platforms. Fragmentation can involve competing bond cleavages, rearrangements, charge retention or migration, and sequential decomposition, so a measured spectrum is an aggregate outcome rather than a direct image of one reaction pathway [1].

Collision energy influences both precursor survival and the production and secondary breakdown of fragments. Thermo instruments distinguish normalized collision energy (NCE), a dimensionless setting normalized to precursor mass and charge, from absolute collision energy. NCE is only approximately equivalent to collision energy in eV for a reference ion; the delivered energy depends on precursor mass and charge [2]. Energy-dependent spectra therefore cannot safely be pooled or compared by treating a numeric energy label as a universal physical unit.

Predicting how much a molecule fragments as energy changes is scientifically useful as a compact description of the response trajectory. It may support controlled comparison of fragmentation behavior and help characterize an energy-dependent aspect of a prediction system. It is a narrower task than predicting a complete tandem mass spectrum. Full-spectrum approaches predict fragment identities or masses and relative intensities and may support candidate ranking or identification. MURU-WUR-v2 instead predicts a scalar summary of the mass distribution of all observed ions, including the precursor; it does not predict fragment formulas, pathways, peak intensities, or a complete spectrum.

Computational MS/MS methods span rule-based fragmentation, probabilistic fragmentation trees, formula and structure ranking, and machine-learning approaches. CFM-ID models competing fragmentation events and has developed through successive ESI-MS/MS prediction versions [3,4]. Neural systems such as MassFormer, ICEBERG and FIORA use molecular graphs and learned representations to predict spectra or fragmentation events [5–7]. FIORA models local bond neighborhoods and predicts fragment probabilities, while ICEBERG combines graph-based fragment generation and scoring [6,7]. These systems address a richer output than the endpoint studied here. Their performance therefore provides context for the field, but cannot be compared directly to MURU's scalar RMSE as if both solved the same task.

Molecular machine learning commonly represents a compound through physicochemical descriptors and structural fingerprints. Morgan or extended-connectivity fingerprints encode local atom environments at successive radii, and count variants retain multiplicity information [8]. Such features can be used as model inputs without implying a specific causal fragmentation mechanism. The MURU development program compared descriptor-only, fingerprint-only, and joint representations and selected a ridge model combining standardized Tier A descriptors with log-transformed Morgan counts. Its target was the compound scale parameter of a shared empirical energy-response profile.

The motivation for the present work is not a claim that scalar fragmentation-extent prediction replaces full-spectrum prediction. Rather, the scalar endpoint makes it possible to ask a bounded question about whether structure carries predictive information across collision-energy levels, how that information transfers to a separate library, and where its limits appear. Evaluation on held-out scaffolds reduces direct analogue leakage, while an independently sampled external chemical-library population tests transport beyond the development records. Scaffold separation alone does not guarantee structural novelty; nearest-training similarity must also be examined [9,10].

The research question was: **Does a frozen structural scale model predict the precursor-including fragmentation-extent trajectory better than a refitted Tier A descriptor ridge on a separately sampled MSnLib population, and does any advantage persist across energy rungs and structural novelty?** The development hypothesis was that joint descriptor and local structural features would reduce scaffold-held-out pooled trajectory error relative to Tier A alone. The external practical criterion was fixed in advance at a candidate/reference P1 ratio of 0.95 or lower, with the direction and tail rule specified by the confirmation protocol. The scope is limited to positive-mode HCD data, two measured MSnLib rungs, the MURU scalar endpoint, a fixed deployment energy map, and support-qualified compounds.

## 2. Materials and Methods

### 2.1 Study design and evidence hierarchy

This computational study contains (i) historical WUR Stage 3 context, (ii) a scaffold-held-out WUR-v2 development program, (iii) one frozen MSnLib external confirmation, and (iv) a distinct collision-energy-interface adjudication study. The stages answer related but non-interchangeable questions. The primary external confirmation was not used to select or refit the candidate. The external population was measured at fixed HCD NCE 20 and 60. A previous MSnLib sample was exposed by an accidental parser-preflight decode before scoring. That sample was not analyzed for the outcome and was permanently excluded; a replacement population was selected under a new frozen protocol. The replacement population was used once and is now exposed. No third sample, replacement draw, repair, or post-result tuning is authorized by the frozen study record [11–14].

### 2.2 Development and external populations

WUR-v2 development used 1,325 positive-mode compounds drawn from the MassBank/LCSB multi-collision-energy acquisition collection and WUR spectral records [15,16]. Primary evaluation used grouped out-of-fold predictions from five scaffold-disjoint folds. Bemis–Murcko scaffolds were computed on stereo-stripped parents; acyclic compounds were assigned compound-specific groups. Model development was a multi-experiment program (13 experiment families), not a single model test. The selected model, `V2_TA_MORGAN_JOINT`, was admitted under the documented simplicity rule among models within 1% of the best observed candidate. The development comparator was a Tier A ridge refitted within the same evaluation design [11].

The MSnLib confirmation frame comprised 1,794 compounds with measured μ at both fixed rungs. Five compounds were excluded because at least one model's implied normalized profile coordinate fell outside the fitted profile's knot support. The scored analysis contained 1,789 compounds in 1,687 Bemis–Murcko scaffold groups; the largest group contained seven compounds. The per-compound observations are repeated measures at two energy rungs, not independent samples. Uncertainty for the primary contrast was estimated by resampling the whole scaffold groups; the generic bootstrap inference framework is described by Efron and Tibshirani [17].

The replacement population was drawn once from an outcome-blind eligible universe after excluding all project-exposed compound keys and scaffolds recorded in the exposure registry. Fixed-rung scan headers were screened before any peak arrays were decoded. In the frozen final population, all 6,004 allowlisted scans were decoded, no spectrum was empty or nonpositive, and every included compound had both rungs. The exact count flow and exposure history are shown in Figure 1 and Supplementary Table S1 [12–14].

![Figure 1. Study design and population flow. Development and independent external evidence are separated; the exposed first sample is shown as excluded history, and CE Design A is a separate study.](../figures/figure_1_study_design.png)

### 2.3 Fragmentation-extent endpoint

For a centroid spectrum with peak masses `m_j` and nonnegative intensities `I_j`, and theoretical protonated precursor mass `m_prec`, the per-spectrum endpoint was:

**μ = [Σ_j (I_j × m_j)] / [m_prec × Σ_j I_j].**

All centroid peaks were included, including the precursor peak; there was no intensity cutoff. The theoretical [M+H]+ mass was used. For each compound and fixed energy rung, the median μ across matched scans from the allowed wells was used as the measured value. This ratio is a mass-weighted extent proxy on a roughly 0-to-1 scale, not a fraction of cleaved bonds, an ion count, a survival yield, or a mechanistic pathway assignment. The data-processing code permits values slightly above one due to observed mass and measurement details; no logit or Beta likelihood was assumed in the model development [11–14].

### 2.4 Structures, molecular standardization, and representations

Compound identity was based on the first InChIKey block of the parent structure. The parent was the largest organic fragment and was neutralized where a neutral form existed; permanent cations retained charge. Stereochemistry was removed from the features. Acyclic compounds were assigned compound-specific scaffold groups in the frozen split audit [18]. The representation protocol did not perform additional tautomer union beyond the standard InChI connectivity behavior. The chosen representative SMILES was sourced from the LCSB structure for LCSB-primary keys or selected lexicographically from deposited WUR SMILES otherwise [11].

Tier A comprised 12 fixed descriptors: precursor m/z, total atom count, rotatable-bond count, ring count, aromatic-ring count, RDBE, TPSA, heteroatom fraction, and N, O, S, and halogen counts. Descriptor values were scaled by frozen constants and then standardized using training-fold means and standard deviations. The Morgan representation used RDKit 2026.03.5, radius 2, 2,048 hashed count features, no chirality, and `log1p` transformation. The candidate used a fixed feature-block weight of 0.1 for Morgan counts; all model fitting and scaling occurred within the training boundary [11,19].

### 2.5 Shared energy-response model and candidate

The model predicts a compound-specific log scale `ℓ_i = log(g_i)` from molecular features. For the joint ridge candidate, the design vector was the concatenation of standardized Tier A features and 0.1 times the log-transformed Morgan count vector. In implementation, ridge regression estimates coefficients and an intercept by minimizing a curvature-weighted squared error over the training compounds:

**β̂ = argmin_β Σ_i w_i (ℓ_i − x_iᵀβ)² + α‖β‖².**

Here `x_i` is the training-standardized feature vector; `w_i` is the frozen curvature weight; `α` is the ridge penalty selected by nested grouped validation. The curvature weight is the normalized inverse estimated variance of `log(g_i)`: the variance estimate is residual variance divided by the sum of squared finite-difference sensitivities of the fitted profile to `log(g_i)`, with the frozen `10⁻⁹` lower bounds applied before inversion; weights are normalized to mean one. Candidate tuning considered `α ∈ {0.1, 0.3, 1, 3, 10, 30, 100, 300}` and Morgan block weight in `{0.1, 0.3, 1.0}`; the deployed final candidate has `α = 0.3` and block weight 0.1. The Tier A reference tuning grid was `{0.01, 0.1, 1, 10, 100}` and selected `α = 0.1`. Nested selection used grouped inner folds. The training population contains 1,325 compounds. These are not identical model classes differing only by the Morgan block: they differ in features, scaling and selected penalty. Therefore the paired external contrast estimates the performance difference between the frozen candidate and refitted descriptor reference; it does not isolate a causal contribution of fingerprints alone [11,20].

A frozen shared monotone response profile `Φ` maps normalized coordinate `u` to μ:

**μ̂_i(E) = Φ((E / 30) / ĝ_i), where ĝ_i = exp(ℓ̂_i).**

`Φ` is represented by 60 fixed knots on the log-u coordinate and fitted by decreasing isotonic regression using development data only. The frozen collapse alternates profile fitting and per-compound scale estimation three times; each scale is selected on the 241-point log-scale grid from −1.6 to 1.6 with parabolic refinement, followed by geometric-mean centering. The same profile and scale parameterization are used by candidate and reference; the structural model predicts `g_i`, not the curve shape. The historical development code and frozen candidate JSON define the complete profile values and coefficients. The external profile coordinate is supported only within the knot range; a compound was excluded from the primary analysis if either model was unsupported at either rung.

### 2.6 Energy coordinate and reference model

The WUR-to-LCSB development bridge used the frozen affine map `T(E) = a + bE`, where `a = −5.95552603907965` and `b = 0.8618030610784555`. For the MSnLib analysis, the predictor's energy coordinate was computed as `E = (NCE − a)/b`; this used zero parameters fit to the MSnLib validation outcomes. The reference was the frozen `V2_REF_TA_RIDGE` descriptor model applied through the same fixed profile. This is a computationally fixed map, not a physical calibration of energy deposition across instruments. Thermo documentation describes NCE as a dimensionless normalized setting whose approximate eV equivalence holds for a reference ion; the source-level and instrument-level history does not establish that the MURU affine map is a universal physical conversion [2,12,13,21].

### 2.7 Prediction metrics and primary inference

Let `e_iE = μ̂_i(E) − μ_i(E)` for compound `i` and observed energy rung `E`. The primary P1 metric is pooled root mean square error over all scored compound-rung cells:

**P1 = √[Σ_i Σ_E e_iE² / N_cells].**

The candidate/reference ratio is `P1_C/P1_R`; ratios below one favor the candidate. P1 is cell-weighted; each compound contributes two observed cells. We also report the mean per-compound RMSE (MRMSE), median, Q90, Q95, CVaR95 (mean of the largest 5% of compound RMSE values), AF (proportion with compound RMSE > 0.20), and AF_max (proportion with any rung absolute error > 0.30). The 0.20 and 0.30 thresholds are frozen engineering failure thresholds, not physical constants. A whole-scaffold bootstrap sampled 1,687 groups with replacement for 10,000 replicates (seed 20261011) and recomputed P1 and its ratio in each replicate. The reported percentile interval is a 95% interval for the paired P1 ratio. The predeclared 5% practical criterion corresponds to ratio ≤ 0.95; statistical evidence that the ratio is below 1 does not satisfy that practical criterion [12–14].

Per-rung RMSE and novelty-quartile results are descriptive secondary analyses. Novelty quartiles were frozen using each compound's maximum Morgan-count Tanimoto similarity to any of 1,325 development compounds; Q1 contains the lowest similarities and is therefore the most novel. No quartile-specific uncertainty interval was computed. Tail differences are described with the scaffold-bootstrap interval for AF; Q90, Q95 and CVaR95 are descriptive point summaries, and no tail advantage is inferred when these values are similar [12–14].

### 2.8 Comparator benchmark and CE-interface adjudication

The public comparator benchmark evaluated MURU, FIORA-OS v0.1.0, ICEBERG 2.1 and GLACIER checkpoints on a common population using fixed spectral metrics under the preregistered mapped-energy convention. It also computed a raw-NCE diagnostic for ICEBERG and GLACIER. These analyses compare full-spectrum outputs and remain sensitive to an unresolved CE input-unit mapping. They are kept separate from the primary scalar endpoint analysis; no state-of-the-art claim is made [22].

The separate CE Design A analysis compared three energy conventions on an independent population of 33 compounds. K1 raw NCE had the highest observed composite score (0.557070), but its Bonferroni-adjusted intervals against K2 and K3 included zero. Under the frozen rule, the result was `INTERFACE_UNRESOLVED`. It does not determine the physical energy unit of any dataset and does not rerank the comparator benchmark [21,23].

### 2.9 Reproducibility and software

Frozen release commit: `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`. External analysis script: `scripts/wur_v2_confirmation_v2/11_external_analysis.py`. A detached worktree at that release was used to rerun the frozen script against the committed result inputs. It reproduced the external point estimates, bootstrap limits, novelty ratios, and decision exactly. The source repository records Python 3.13.12, NumPy 2.5.2, SciPy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, RDKit 2026.03.5, and pymzML 2.6.1 for the Phase 2 reconstruction environment. Raw mzML files are not redistributed in this package; the scored aggregate μ table and allowable source evidence are included in the repository, subject to their source terms. The model's structure-derived Morgan representation is deterministic and can be rebuilt from committed structures; the prior reproducibility audit noted the rebuilt representation was not present in the historical tracked set, a packaging issue addressed by recording the command and version here [11,24].

### 2.10 Data rights and ethics

The work reanalyzes chemical structures and mass spectra; it includes no human or animal subjects. The MSnLib raw archives are third-party data and are not bundled in the reviewer archive. Source acquisition instructions, original source citations, and file hashes are supplied. No raw spectra should be redistributed unless the relevant source license permits it. Project-owned analysis code and derived tables are identified in the release manifest.

## 3. Results

### 3.1 Study populations and exclusions

The fixed MSnLib population included 1,794 measured compounds, with no incomplete two-rung cases. Five compounds were outside at least one model's supported profile coordinate and were excluded from the primary score, leaving 1,789 compounds across 1,687 scaffold groups. All 1,789 compounds were evaluated at both NCE 20 and NCE 60, for 3,578 compound-rung cells. A sensitivity analysis including the five support-excluded compounds gave P1 values of 0.12947 for MURU and 0.13336 for the reference and did not change the interpretation. The independent population does not represent a blind sample after analysis: it is now permanently exposed and cannot be reused for confirmation [12–14].

### 3.2 Model-development experiments

The development search comprised 13 experiment families. It considered descriptor baselines, Morgan-only models, additional structural representations, hybrid feature blocks, residual models, nonlinear alternatives, trust/abstention features and an attempted shape extension. The selected candidate was the joint Tier A plus Morgan-count ridge model, chosen under the prespecified simplicity rule among near-best candidates. On scaffold-held-out development predictions, its P1 was 0.1160 versus 0.1305 for the refitted Tier A reference (ratio 0.8886). The release records the original ten-arm simultaneous interval as [0.860, 0.918]; because the Phase 2 audit package and its calculation artifacts were not present in the available workspace, this interval was not independently reconstructed in the present phase and is not treated as an independently verified inferential result. The point estimates and selection history are retained as frozen development records [11,18,25].

### 3.3 Primary independent MSnLib confirmation

MURU achieved P1 = 0.1296115 and the Tier A reference achieved P1 = 0.1335276. The paired ratio was 0.970672, with a 95% whole-scaffold bootstrap interval of [0.952361, 0.989267]. This corresponds to a 2.93% relative reduction in pooled RMSE. The interval lies below one but entirely above the prespecified 0.95 practical threshold; the result therefore meets the frozen classification of **MODEST EXTERNAL CONFIRMATION**, not practically meaningful improvement. The detached-release reconstruction reproduced the frozen values [12–14].

![Figure 2. Candidate/reference pooled trajectory RMSE ratios in development and external confirmation. Only the external interval is shown because its bootstrap was independently reconstructed in this phase.](../figures/figure_2_performance.png)

### 3.4 Per-energy-rung performance

At NCE 20, candidate RMSE was 0.16438 and reference RMSE was 0.16736 (ratio 0.9822). At NCE 60, candidate RMSE was 0.08111 and reference RMSE was 0.08747 (ratio 0.9273). Both rungs favored the candidate, with a larger point difference at NCE 60. The reference residuals had positive means at both rungs (+0.0354 and +0.0207), while candidate mean residuals were −0.0077 and +0.0033. Thus some of the pooled difference accompanies a smaller systematic offset under the fixed map; this does not establish that the map is physically calibrated [12–14].

### 3.5 Structural novelty

All four frozen quartiles are shown in Figure 4 and Supplementary Table S5. The most novel quartile, Q1 (maximum training-set similarity <0.281; n = 449), had candidate P1 = 0.12768 and reference P1 = 0.12663, ratio = 1.0083. The candidate therefore had slightly higher error in this subset. Q2, Q3 and Q4 ratios were 0.9655, 0.9593 and 0.9528, respectively. These are descriptive stratum estimates without quartile-specific confidence intervals. The main external advantage did not appear in the least-similar quarter [12–14].

![Figure 4. P1 ratio across all four structural-novelty quartiles. Q1 is the least-similar, most novel quartile; values above one indicate higher candidate error.](../figures/figure_4_structural_novelty.png)

### 3.6 Error distributions and tail performance

MURU and reference MRMSE values were 0.11214 and 0.11752; median compound RMSE values were 0.09956 and 0.10752. The candidate/reference Q90 values were 0.20705 and 0.20659; Q95 values were 0.23151 and 0.23486; and CVaR95 values were 0.26568 and 0.26486. AF was 11.85% for MURU and 11.79% for the reference. The bootstrap AF difference was +0.00056, with 95% interval [−0.01453, +0.01554], below the protocol's +0.03 adverse-tail override. These results do not demonstrate tail-risk improvement. The point estimates show little to no difference in upper-tail behavior [12–14].

![Figure 3. Per-rung RMSE and compound error summaries. Upper-tail measures are descriptive; AF's scaffold-bootstrap difference interval includes zero.](../figures/figure_3_external_errors.png)

### 3.7 Comparator analyses and energy-interface adjudication

On the comparator benchmark's primary mapped-energy convention, MURU's P1 was 0.1265, compared with 0.2046 for FIORA-OS, 0.1621 for ICEBERG 2.1, and 0.1384 for GLACIER. The primary MURU/comparator ratios were 0.619, 0.781, and 0.914. On the raw-NCE diagnostic, ICEBERG and GLACIER ratios reversed to 1.076 and 1.238, favoring the respective comparator under that diagnostic. A recent GLACIER preprint treats fragment prediction as graph object detection, adding a distinct architecture to this rapidly developing field [26]. Since model input energy conventions could not be confirmed completely from upstream training metadata and artifacts, these comparisons are conditional on the tested mapping. They do not support a convention-independent ranking or a state-of-the-art claim [21–23,26].

In Design A, the three mappings ranked K1 > K2 > K3 in every descriptive cut. K1's pooled composite score was 0.557070. Its contrasts with K2 and K3 were +0.042318 and +0.050333, but the primary Bonferroni-adjusted intervals [−0.012660, +0.099083] and [−0.007439, +0.109993] crossed zero. The frozen decision was `INTERFACE_UNRESOLVED`. This independent 33-compound study supports a consistent descriptive ordering but does not identify a correct physical energy convention [23].

![Figure 5. CE Design A adjusted contrasts and comparator benchmark sensitivity. Ratios below one favor MURU under the tested convention; diagnostic reversals and the unresolved Design A result preclude a convention-independent ranking.](../figures/figure_5_energy_interface.png)

### 3.8 Reproducibility findings

The frozen MSnLib analysis script was executed in a fresh detached worktree at the release commit using committed inputs and model artifacts. It returned 1,789 scored compounds, 1,687 groups, the same candidate and reference P1 values, the same bootstrap ratio interval, the same per-rung values, all four novelty ratios, and the same frozen decision. The bootstrap used 10,000 resamples and seed 20261011. The reproducibility boundary is statistical reconstruction from the committed measured-μ table and frozen model JSON; raw mzML retrieval and parsing are not included in this rerun. The repository's Phase 1 whole-suite test record contains 11 pre-existing failures and 14 errors (identical at the comparison base), including a newly identified unpinned `lxml` dependency and tests requiring absent large synthetic benchmark artifacts; these are not used to validate the scientific result [24].

## 4. Discussion

The central result is a small but statistically directional external difference for the frozen scalar endpoint: the MURU candidate's pooled two-rung RMSE was 2.93% lower than that of the refitted Tier A reference. The 95% scaffold-bootstrap interval excludes one, but every value in the interval is above 0.95. The prespecified practical-improvement criterion therefore failed. Calling this a modest confirmation reflects the frozen decision rule and the limited size of the effect; it does not imply operational benefit.

The development estimate was appreciably larger than the external estimate (ratio 0.889 versus 0.971), and the development tail-failure reduction did not transfer. Several explanations remain compatible with these observations. Development model selection involved multiple candidate families, even though grouped nested validation and a simplicity rule were used. The external population differs in source, library construction and the measured energy rungs. Model representation and selection also differ between candidate and reference: the candidate includes a Morgan count block and has its own selected ridge penalty; the reference is a separate Tier A ridge. The paired evaluation identifies their overall predictive difference under the frozen pipeline, not the fingerprint block's causal effect. Source shift, residual confounding, the fit of the zero-parameter map, and selection optimism could each affect the magnitude. None is separately identified by this comparison.

The adverse Q1 finding is important. Q1 is defined by low maximum Morgan-count similarity to the development compounds, and the candidate/reference ratio of 1.008 indicates slightly worse point performance there. The other three quartiles favor the candidate, but no subgroup intervals were computed, so this pattern should be treated as descriptive. It does not establish a sharp applicability threshold. It does show why an average external gain cannot be generalized to the structural frontier represented by this library's least-similar compounds.

No improvement in tail risk was demonstrated. Candidate and reference Q90 and CVaR95 values are nearly equal, Q95 differs only slightly, and the AF contrast interval includes zero. In particular, the candidate's AF point estimate is marginally higher. The data support a typical-error reduction more readily than any reduction in severe failures, but the distinction is descriptive: the uncertainty interval for AF does not establish equality or harm.

Energy interpretation is a major limitation. The model's fixed affine conversion is computationally reproducible and was not fit on the validation outcomes, so the external scalar calculation is valid as a test of that deployed mapping. However, it is not demonstrated to be a universal physical calibration from NCE to electron-volts or deposited internal energy. Thermo documentation defines NCE as a normalized setting and only approximately equivalent to eV for a reference mass/charge. In addition, source records and code for public comparator checkpoints do not unambiguously identify the CE unit used throughout training. The raw-NCE diagnostic reverses two comparator rankings, while a separate frozen Design A study failed its prespecified inferential rule despite a consistent descriptive rank order. Therefore, public-model comparisons are conditional; they cannot establish general superiority or resolve the physical interface.

The full-spectrum comparator study also evaluates a different target. It compares spectral outputs with a spectral similarity metric, whereas MURU's P1 compares a scalar mass-weighted μ. The comparator result may be useful as a sensitivity analysis within its own benchmark, but it does not place the scalar MURU model on an equivalent scale to a full-spectrum predictor. Benchmark populations, excluded spectra, energy conventions and model versions must all be considered before interpreting those results.

The earlier sample exposure must remain part of the research history. A parser-preflight error decoded and surfaced one outcome from sample 1 before its planned look. That sample was not scored; it was permanently excluded and replaced under a new protocol. Sample 2 was drawn once, used for the frozen analysis and is now exposed. This provenance weakens any casual use of “blind” for the overall project and prevents another confirmatory use of this library population. It does not change the recorded sample-2 calculations, but it constrains how independent the full development history can be represented.

The development simultaneous max-T interval [0.860, 0.918] remains a historical claim in the release record. The calculation source was not found in the Phase 3 workspace because the specified Phase 2 audit directory and commit were absent. It is therefore not presented here as a newly reproduced interval. The external scaffold-bootstrap interval is independently reproducible from the committed frozen inputs. This distinction matters: development evidence informed model selection, while the external interval supports the primary independent comparison.

Future work should predefine a physically interpretable energy interface, use independently collected spectra with documented instrument-specific CE semantics, and retain enough chemically remote compounds to estimate performance at the structural frontier. A prospective study should freeze the model, endpoint, support rule, comparator, energy mapping and subgroup estimands before access to outcomes. If the intended scientific use is complete spectrum simulation or structure identification, those outputs need separate benchmarks with matched test compounds and clearly documented CE settings. The present result supports further independent study of a compact fragmentation-extent endpoint; it does not support using MURU as a universal MS/MS predictor.

## 5. Conclusion

On the frozen MSnLib population and fixed deployment energy map, MURU-WUR-v2 achieved a lower pooled fragmentation-extent RMSE than the Tier A reference, with a ratio of 0.9707 (95% scaffold-bootstrap interval 0.9524–0.9893). The gain was statistically directional but smaller than the prespecified 5% practical-improvement threshold. No tail-risk advantage was demonstrated, and performance did not improve in the least-similar structural quartile. The defensible conclusion is modest external confirmation for this two-rung, positive-mode scalar endpoint, with unresolved collision-energy interpretation and limited transfer to novel chemistry.

## Declarations

**Author contributions.** Aryav Thakur: project ownership, study design and computational research. Specific contribution allocation should be confirmed by the author before any external circulation.

**Acknowledgments.** No acknowledgments are recorded in the verified project files.

**Data availability.** Frozen source records, derived measured-μ tables, model artifacts and analysis code are included in the MURU-ConjectureLab-v1 repository at the release commit listed above. Third-party MSnLib raw archives are not redistributed here. Instructions and source identifiers are provided in the supporting information.

**Code availability.** Analysis source is present in the repository. Phase 3 figure and table generation scripts are included in this package. The release branch remains the source of frozen scientific results; this publication branch adds documentation and reproducibility outputs.

**Competing interests.** No competing-interest statement has been verified. The author should confirm this declaration before external circulation.

**Ethical considerations.** No human participants or animals were involved; no institutional review approval was applicable to the computational reanalysis described here.

**Research limitations.** This study addresses a precursor-including scalar endpoint on positive-mode HCD data at two external energy rungs. It does not validate full-spectrum prediction, identification accuracy, transfer across instruments, negative-mode performance, or universal calibration. The external population is exposed after the single frozen look. The energy interface is unresolved; the most novel quartile shows no candidate advantage; and the prior development max-T interval could not be independently reconstructed from available audit files.

**AI-assisted research and drafting record.** AI tools assisted with repository inspection, analysis-code authoring, generation of figures and tables, literature discovery, drafting and editing of this internal manuscript and supporting information. Frozen experimental outcomes were not altered. All factual, scientific and authorship statements require owner review before any external use. This is an internal AI-assisted draft and has not been submitted to a journal.

## References

1. A. R. Johnson, E. E. Carlson. Collision-induced dissociation mass spectrometry: A powerful tool for natural product structure elucidation. Analytical Chemistry. Vol. 87, pg. 10668–10678, 2015. https://doi.org/10.1021/acs.analchem.5b01543.
2. Thermo Fisher Scientific. Q Exactive HF Software Manual: HCD normalized and absolute collision energy. 2018. https://documents.thermofisher.com/TFS-Assets/CMD/manuals/man-1372090-q-exactive-hf-soft-man1372090-en.pdf.
3. F. Allen, R. Greiner, D. Wishart. Competitive fragmentation modeling of ESI-MS/MS spectra for putative metabolite identification. Metabolomics. Vol. 11, pg. 98–110, 2015. https://doi.org/10.1007/s11306-014-0676-4.
4. F. Wang, J. Liigand, S. Tian, D. Arndt, R. Greiner, D. S. Wishart. CFM-ID 4.0: More accurate ESI-MS/MS spectral prediction and compound identification. Analytical Chemistry. Vol. 93, pg. 11692–11700, 2021. https://doi.org/10.1021/acs.analchem.1c01465.
5. A. Young, H. Röst, B. Wang. Tandem mass spectrum prediction for small molecules using graph transformers. Nature Machine Intelligence. Vol. 6, pg. 404–416, 2024. https://doi.org/10.1038/s42256-024-00816-8.
6. Y. Nowatzky, F. F. Russo, J. Lisec, A. Kister, K. Reinert, T. Muth, P. Benner. FIORA: Local neighborhood-based prediction of compound mass spectra from single fragmentation events. Nature Communications. Vol. 16, Article 2298, 2025. https://doi.org/10.1038/s41467-025-57422-4.
7. R. Wang, M. Manjrekar, B. Mahjour, J. Avila-Pacheco, J. Provenzano, E. Reynolds, M. Lederbauer, E. Mashin, S. Goldman, M. Wang, J.-K. Weng, D. L. Plata, C. B. Clish, C. W. Coley. Neural spectral prediction for structure elucidation with tandem mass spectrometry. bioRxiv preprint, 2025. https://doi.org/10.1101/2025.05.28.656653. Not peer reviewed as of the source record consulted.
8. D. Rogers, M. Hahn. Extended-connectivity fingerprints. Journal of Chemical Information and Modeling. Vol. 50, pg. 742–754, 2010. https://doi.org/10.1021/ci100050t.
9. G. W. Bemis, M. A. Murcko. The properties of known drugs. 1. Molecular frameworks. Journal of Medicinal Chemistry. Vol. 39, pg. 2887–2893, 1996. https://doi.org/10.1021/jm9602928.
10. R. J. Bajusz, A. Rácz, K. Héberger. Why is Tanimoto index an appropriate choice for fingerprint-based similarity calculations? Journal of Cheminformatics. Vol. 7, Article 20, 2015. https://doi.org/10.1186/s13321-015-0069-3.
11. A. Thakur. MURU-WUR-v2 development protocol, final candidate freeze and final report. MURU-ConjectureLab-v1 repository, frozen release commit bfa153e828e08b3c7e674ef7fe9d6818d14a2b61, 2026. Files: `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md`; `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`; `MURU_WUR_V2_FINAL_REPORT.md`.
12. A. Thakur. MURU-WUR-v2 MSnLib Confirmation Study 2 protocol, freeze and result. MURU-ConjectureLab-v1 repository, 2026. Files: `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`; `MURU_V2_MSNLIB_CONFIRMATION_V2_RESULT.md`.
13. A. Thakur. MURU-WUR-v2 MSnLib Confirmation Study 2 analysis code and frozen outputs. MURU-ConjectureLab-v1 repository, 2026. Files: `scripts/wur_v2_confirmation_v2/11_external_analysis.py`; `artifacts/wur_v2_confirmation_v2/result/external_analysis.json`; `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`.
14. A. Thakur. MURU-WUR-v2 exposure and data registry. MURU-ConjectureLab-v1 repository, 2026. File: `MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md`.
15. A. Elapavalore, T. Kondić, R. R. Singh, B. A. Shoemaker, P. A. Thiessen, J. Zhang, E. E. Bolton, E. L. Schymanski. Adding open spectral data to MassBank and PubChem using open source tools to support non-targeted exposomics of mixtures. Environmental Science: Processes & Impacts. Vol. 25, pg. 1788–1801, 2023. https://doi.org/10.1039/D3EM00181D.
16. S. Neumann, R. Meier, M. Wenk, A. Elapavalore, T. Nishioka, T. Schulze, M. Stravs, H. Tsugawa, F. Matsuda, E. L. Schymanski. MassBank: an open and FAIR mass spectral data resource. Nucleic Acids Research. Vol. 54, pg. D601–D606, 2026. https://doi.org/10.1093/nar/gkaf1193.
17. B. Efron, R. J. Tibshirani. Bootstrap methods for standard errors, confidence intervals, and other measures of statistical accuracy. Statistical Science. Vol. 1, pg. 54–75, 1986. https://doi.org/10.1214/ss/1177013815.
18. A. Thakur. MURU-WUR-v2 development split and population audit. MURU-ConjectureLab-v1 repository, frozen release commit bfa153e828e08b3c7e674ef7fe9d6818d14a2b61, 2026.
19. RDKit. Morgan fingerprint implementation and documentation, version 2026.03.5. https://www.rdkit.org/docs/.
20. D. C. Montgomery, E. A. Peck, G. G. Vining. Introduction to linear regression analysis, 5th ed. Wiley, 2012.
21. Thermo Fisher Scientific. Orbitrap Exploris 240 Software Manual: normalized and absolute HCD collision energy. https://docs.thermofisher.com/.
22. A. Thakur. MURU public comparator benchmark preregistration, record chain and result. MURU-ConjectureLab-v1 repository, 2026.
23. A. Thakur. MURU collision-energy-interface adjudication Design A preregistration and result. MURU-ConjectureLab-v1 repository, 2026.
24. A. Thakur. MURU-WUR-v2 reproducibility manifest and full-repository regression verification. MURU-ConjectureLab-v1 repository, 2026.
25. A. Thakur. MURU-WUR-v2 review adjudication and statistical review records. MURU-ConjectureLab-v1 repository, 2026.
26. R.-X. Wang, R. Wang, C. W. Coley. GLACIER: Rethinking Mass Spectrum Prediction as an Object Detection Problem. arXiv:2606.29161, 2026. Preprint; not peer reviewed as of 2 November 2026.
