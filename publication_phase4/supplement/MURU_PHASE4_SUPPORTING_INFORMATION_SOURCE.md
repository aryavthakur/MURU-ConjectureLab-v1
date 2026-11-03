# Supporting Information

## S1. Study evidence hierarchy and artifact lineage

The study contains four evidence streams that should not be pooled: historical Stage 3 context; the WUR-v2 grouped model-development program; the single frozen external MSnLib evaluation; and a separate 33-compound collision-energy-interface Design A study. The primary MSnLib result comes from the frozen release `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`. The Phase 4 manuscript and derived figures do not alter the original experimental outcomes.

Source artifacts include `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`, `external_analysis.json`, the frozen candidate and reference model records in `artifacts/wur_v2`, the source analysis script `scripts/wur_v2_confirmation_v2/11_external_analysis.py`, the comparator result at `artifacts/comparator_benchmark/result/analysis.json`, and Design A result at `artifacts/ce_interface_adjudication/design_a/result/analysis.json`. The complete repository release manifest supplies hashes. Tables in `COMPLETE_SUPPLEMENTARY_TABLES/` identify the source JSON or CSV for each export.

## S2. Population flow, inclusion, and exposure history

| Stage | Compounds | Notes |
|---|---:|---|
| MSnLib measured population | 1,794 | Each has two recorded external HCD NCE settings |
| Outside candidate/reference profile support | 5 | Excluded if either model was unsupported at either rung |
| Primary scored population | 1,789 | Two compound-rung cells per compound; 3,578 cells |
| Scaffold groups | 1,687 | Bemis–Murcko grouping; largest group size 7 |
| Comparator common population | 1,327 | 1,254 scaffold groups; a distinct benchmark population |
| Comparator source candidates removed | 0 | No excluded predicted/measurement cases in the frozen primary comparator output |

A prior MSnLib sample was exposed during parser preflight before the planned outcome analysis. It was not scored and was permanently excluded. The replacement sample was selected once under a frozen outcome-blind protocol after excluding recorded exposed compound keys and scaffolds. That control does not establish that every close analogue was excluded or that no unrecorded exposure occurred. The replacement population was evaluated once and is now exposed. It cannot support a second confirmatory use.

WUR-v2 development used 1,325 positive-mode compounds and a five-fold scaffold-disjoint outer evaluation; 13 model-experiment families were documented. The chosen candidate was selected by a simplicity rule among near-best models. The MSnLib primary analysis is separate from development selection. Exact sample lineage and exclusions are defined in the frozen protocol and exposure registry.

## S3. Measured endpoint and data processing

For a processed spectrum with masses `mⱼ`, raw intensities `Iⱼ ≥ 0`, and declared protonated precursor mass `m_prec`, the endpoint is:

**μ = (Σⱼ Iⱼ mⱼ) / (m_prec Σⱼ Iⱼ).**

The implemented base preprocessing has zero relative-intensity cutoff, includes the precursor peak, and uses raw peak intensities. The per-spectrum function checks finite positive m/z, nonnegative intensities, positive total signal, and positive precursor mass. Duplicate compound-energy scans are reduced to one measured value by the frozen median aggregator. The WUR development path uses the MassBank declared `PRECURSOR_M/Z`; the MSnLib validation path passes structure-derived [M+H]+ to the endpoint. The same formula is applied, but the denominator source differs and equality is not assumed. The WUR numerator also includes observed peaks, so the endpoint can slightly exceed one. The endpoint is dimensionless and nonnegative, but can be slightly greater than one if observed peaks are marginally heavier than the declared precursor. It is not a count of cleaved bonds, precursor survival yield, fragment identity, mechanism, or complete-spectrum similarity.

The formula is implemented by `src/muru/features.py::mu` after `Spectrum.preprocess` in `src/muru/io/wur_spectra.py::spectrum_mu`; base settings are defined in `src/muru/wur_bridge_constants.py`. No inference is made from the scalar endpoint about fragment identity or pathway.

## S4. Molecular representation and model fitting

| Component | Frozen setting |
|---|---|
| Compound parent | Largest organic fragment; neutralized where a neutral form exists; permanent cations retain charge |
| Stereochemistry | Removed from model feature structure |
| Identity key | First InChIKey block |
| Tier A | 12 fixed physicochemical/molecular descriptors, divided by descriptor-specific constants |
| Candidate Tier A scaling | Further standardized using training-fold mean and SD |
| Reference Tier A scaling | No additional fold-specific standardization |
| Morgan fingerprint | RDKit 2026.03.5; radius 2; 2,048 hashed count bins; no chirality; `log1p` |
| Candidate feature block weight | Morgan block multiplied by 0.1 |
| Candidate ridge | α=0.3; search α∈{0.1,0.3,1,3,10,30,100,300}, Morgan weight∈{0.1,0.3,1.0} |
| Tier A reference ridge | α=0.1; search α∈{0.01,0.1,1,10,100} |
| Ridge intercept | Fitted and unpenalized (`fit_intercept=True`) |
| Profile | Shared decreasing isotonic response; 60 knots on log-u |
| Profile/scale fitting | Three alternating updates; log-scale grid of 241 points on [−1.6,1.6], followed by parabolic refinement |
| Model population | 1,325 compounds in development records |

Let `xᵢ` be the model-specific feature vector, `ℓᵢ=log(gᵢ)` the target log-scale, `wᵢ` the normalized curvature weight, and `α` the ridge penalty. The implemented weighted ridge objective is:

**(b̂₀,β̂)=argmin_(b₀,β) Σᵢ wᵢ(ℓᵢ−b₀−xᵢᵀβ)² + α‖β‖².**

The intercept `b₀` is not penalized. Candidate and reference use the same shared response profile and scale parameterization, but they are separately selected pipelines with different feature spaces, candidate descriptor scaling, dimensionality, and α grids. Their contrast cannot isolate a Morgan-fingerprint effect.

## S5. Response profile and external energy input

The response profile is written `Φ(u)`, with normalized coordinate `u=(E/30)/g`; the predicted endpoint is `μ̂ᵢ(E)=Φ((E/30)/ĝᵢ)`. The profile is a decreasing isotonic fit represented by 60 fixed knots. Development fitting uses the selected training data only.

WUR primary-library methods report HCD NCE settings 15, 30, 45, 60, 75, 90 and stepped SCE settings 25, 38, 59. These are percent-style normalized settings, not eV. The 10-ppm peak-matching tolerance is used for auxiliary precursor-matching quantities; because the base cell includes the precursor, this tolerance does not change the μ numerator or denominator. MSnLib external settings are HCD NCE 20 and 60. The frozen empirical bridge is `T(E)=a+bE`, with `a=−5.95552603907965`, `b=0.8618030610784555`; external model input is its inverse at recorded NCE. The bridge is computationally reproducible but is not a physical NCE-to-eV conversion or cross-instrument calibration.

Design A evaluated three comparator energy conventions on 33 compounds. It used cosine similarity as primary metric and paired molecule-level bootstrap because all 33 scaffold groups were unique. K1 had the highest score, 0.5570699532, but adjusted K1−K2 and K1−K3 intervals were [−0.0126596, 0.0990831] and [−0.0074389, 0.1099934]. The frozen conclusion is `INTERFACE_UNRESOLVED`. The full estimates and source record are exported in `COMPLETE_SUPPLEMENTARY_TABLES/ce_design_a.csv`.

## S6. Metrics and uncertainty

For compound `i`, rung `E`, and prediction error `eᵢE=μ̂ᵢ(E)−μᵢ(E)`, pooled P1 is:

**P1 = √(ΣᵢΣ_E eᵢE² / N_cells).**

Each of the 1,789 scored compounds contributes two cells. The candidate/reference ratio is `P1_candidate/P1_reference`; values below one favor the candidate. Compound-level summaries include the mean and median compound RMSE, Q90, Q95, CVaR95 (mean of the highest 5% of compound RMSE values), AF (fraction with compound RMSE >0.20), and AF_max (fraction with any rung absolute error >0.30). The AF and AF_max thresholds are frozen engineering thresholds, not physical constants.

The primary 95% interval is a paired scaffold bootstrap with 10,000 resamples and seed 20261011. Each replicate draws 1,687 scaffold groups with replacement and carries all compounds and both rung cells in each sampled group. P1 for both models and their ratio are recomputed per replicate. The interval uses empirical 2.5th and 97.5th percentiles. It quantifies sampling uncertainty across the observed scaffold groups conditional on the frozen models, eligible sample, endpoint, and energy map. It does not include training or model-selection uncertainty.

## S7. Full primary external results

Exact source values are available in `COMPLETE_SUPPLEMENTARY_TABLES/primary_results.csv`, `per_energy_results.csv`, `error_summary.csv`, `external_compound_errors.csv`, and `novelty_results.csv`.

| Result | Value |
|---|---:|
| Candidate P1 | 0.1296115107 |
| Tier A reference P1 | 0.1335276112 |
| Candidate/reference ratio | 0.9706719801 |
| 95% scaffold bootstrap interval | [0.9523611880, 0.9892672062] |
| Relative P1 reduction | 2.9328% |
| Prespecified practical target | ratio ≤0.95 |
| Target passed? | No |

| Rung | n | Candidate RMSE | Reference RMSE | Ratio | Candidate mean residual | Reference mean residual |
|---|---:|---:|---:|---:|---:|---:|
| HCD NCE 20 | 1,789 | 0.1643762 | 0.1673566 | 0.9821913 | −0.0077006 | +0.0353532 |
| HCD NCE 60 | 1,789 | 0.0811095 | 0.0874700 | 0.9272829 | +0.0033380 | +0.0206737 |

## S8. Novelty, error distribution, and tail outcomes

| Frozen novelty quartile | n | Candidate P1 | Reference P1 | Ratio |
|---|---:|---:|---:|---:|
| Q1, lowest maximum similarity | 449 | 0.12768 | 0.12663 | 1.0082968 |
| Q2 | 462 | 0.11787 | 0.12208 | 0.9655334 |
| Q3 | 456 | 0.12356 | 0.12880 | 0.9592956 |
| Q4, highest similarity | 422 | 0.12686 | 0.13316 | 0.9527711 |

Novelty bins use maximum Morgan-count Tanimoto similarity to any of 1,325 development compounds. Quartile estimates are descriptive and no quartile-specific uncertainty intervals were estimated. The most-novel quartile has slightly worse candidate point error.

| Compound-level measure | Candidate | Reference |
|---|---:|---:|
| MRMSE | 0.1121374 | 0.1175158 |
| Median RMSE | 0.0995566 | 0.1075164 |
| Q90 | 0.2070537 | 0.2065879 |
| Q95 | 0.2315082 | 0.2348610 |
| CVaR95 | 0.2656786 | 0.2648635 |
| AF | 0.1185020 | 0.1179430 |
| AF_max | 0.0620458 | 0.0609279 |

The scaffold-bootstrap AF difference was +0.0005590, 95% interval [−0.0145253,+0.0155383]. Tail-risk benefit was not demonstrated; these data also do not prove equality or harm.

## S9. Comparator benchmark under both tested energy conventions

The comparator study used 1,327 common compounds and 1,254 scaffold groups. Its primary input condition was native NCE for FIORA-OS and `ev_primary` for ICEBERG and GLACIER; only the latter two have a raw-NCE diagnostic. It converted predicted fragment peak lists from each full-spectrum system to the precursor-including μ endpoint with the frozen `spectrum_mu` function and calculated the same two-rung pooled P1. Thus the comparison uses a common derived scalar endpoint. It does not score spectrum similarity, peak identity, candidate identification, or complete-spectrum fidelity. The study is not feature-matched; systems differ in training data, architecture, preprocessing, tuning, and energy-input semantics.

| Model | Comparator P1 | MURU/comparator ratio (mapped primary) | Ratio CI (95%) | Raw-NCE ratio | Interpretation |
|---|---:|---:|---:|---:|---|
| FIORA-OS v0.1.0 | 0.2045525 | 0.6185250 | [0.5933494,0.6456244] | not calculated | Conditional μ comparison |
| ICEBERG 2.1 | 0.1620766 | 0.7806238 | [0.7479332,0.8145965] | 1.076 | Conditional; raw-NCE point ordering reverses |
| GLACIER | 0.1383865 | 0.9142574 | [0.8729690,0.9584434] | 1.238 | Conditional; raw-NCE point ordering reverses |

The mapped primary outputs showed lower MURU μ error for this benchmark. Under the raw-NCE diagnostic, ICEBERG and GLACIER point ratios exceed one. These are convention-dependent benchmark results and do not support a universal full-spectrum ranking. The output and exact CIs are source-derived in `comparator_metrics.csv`.

## S10. Development evidence and unresolved max-T provenance

The development point estimates were P1=0.1159994 for the selected candidate and 0.1305460 for the Tier A reference, ratio 0.8885713. The release reports a ten-arm simultaneous max-T interval [0.860,0.918]. The recovered Phase 2 report records a max-T analysis but not the original script, exact seed, serialized resamples, or selection ledger. Phase 2 also contains a distinct conditional interval [0.8650671579,0.9105586626], which is not interchangeable with the simultaneous interval. Neither value is presented as independently reproduced in Phase 4. The external bootstrap is a different inferential calculation and does not repair the development provenance gap.

## S11. Census neutral-scaffold defect erratum

The recovered Phase 2 code called `neutral_scaffold(group_key, smiles)` although its function signature is `neutral_scaffold(smiles, key)`. Reconstructing the historical and corrected sets yielded 2,090 and 766 neutral-scaffold labels, respectively. The Phase 2 verifier reran the population membership chain for four recorded frames; Phase 4 reran the same verifier read-only from the recovered source and input worktrees.

| Population frame | n | Frozen population SHA-256 | Historical/corrected membership symmetric difference |
|---|---:|---|---:|
| DESIGN, step 10b | 39,238 | `8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e` | 0 |
| DESIGN, step 12b | 47,742 | `84828abfe29e595379baceb993e97edc846268f255935a66b675c59407c1e283` | 0 |
| DETECTED_POSITIVE, step 10b | 32,154 | `feaade612cb35cde6c627b813b9dc69a9dae966ed1bc05b7fd6ba0af9741e451` | 0 |
| DETECTED_POSITIVE, step 12b | 39,236 | `b526ca0b9b93c7dc39f8b463d2b77f40541b44b0b301e7e3bdacebfc52737aca` | 0 |

The rerun verified all four historical reconstructions against frozen counts and hashes and found the watched inputs unchanged. This establishes no membership impact for these four frames only. It cannot establish that all unrecorded intermediate tables, manual decisions, or downstream calculations were unaffected. No frozen input was changed. The read-only verifier short-circuited a strict-similarity diagnostic that cannot affect membership at steps 10b and 12b. The machine-readable sanitized run record is `../verification/census_neutral_filter_verification_rerun.json`.

## S12. Software, rights, reproducibility, and limitations

The recovered Phase 2 reconstruction record lists Python 3.13.12, NumPy 2.5.2, SciPy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, RDKit 2026.03.5, and pymzML 2.6.1. Phase 4 figure regeneration uses Python 3.13 and Matplotlib 3.11.1 with NumPy/pandas in the local environment; exact runtime snapshots and hashes are recorded in the release manifest.

The reviewer archive supports statistical reconstruction from committed measured-μ values and frozen model output. It does not include third-party MSnLib raw mzML archives, and does not claim raw-data-to-model reproduction or training from scratch. A system Python environment without RDKit failed to run the census verifier; the preserved Phase 2 worktree environment ran it successfully. Third-party raw files must be acquired under their source terms. Rights-cleared project code and derived tables remain in the project repository.

No human or animal subjects were involved. The principal scientific limits are the scalar target, positive-mode HCD data, two external nominal energy settings, profile-support exclusions, the single exposed replacement sample, the physical energy-map ambiguity, the small external effect, the non-improvement in the least-similar quartile, no demonstrated tail advantage, and unreproduced development max-T uncertainty provenance.
