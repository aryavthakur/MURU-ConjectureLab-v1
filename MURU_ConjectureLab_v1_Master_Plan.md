# MURU ConjectureLab v1
## Scientific and Engineering Master Plan

**Status:** planning document. No implementation authorized by this document.
**Prepared:** 11 August 2026
**Basis:** three project references (read in full), the MassBank record format guide, and direct inspection of 373 live MassBank LCSB records fetched from `MassBank-data` during this analysis.

---

# 1. Executive verdict

**CONDITIONAL GO**, with one mandatory change to the research design before any modelling begins.

Three findings drive this.

**Finding A (positive).** The dataset is cleaner than the project files assume. Across 373 records I fetched and parsed, instrument metadata is perfectly homogeneous: one instrument string, one instrument type (LC-ESI-QFT), one fragmentation mode (HCD), one resolution setting (17500), one confidence class (`standard compound`), and exactly two precursor types ([M+H]+ and [M-H]-). 85% of compound-by-mode groups carry all six collision energies. The accession scheme is deterministic, so grouping spectra by molecule and energy requires no fuzzy matching. Almost every confounder you were worried about in `DATASET_SOURCE.md` is already controlled by construction.

**Finding B (negative, and it changes the design).** Spectral entropy is the wrong primary endpoint. In my sample only 18 of 56 complete six-energy trajectories show monotone entropy across the grid. Entropy correlates with total ion current (Spearman +0.27 to +0.33 at NCE 60–90) and with precursor m/z (+0.24 to +0.36 for NCE ≥ 30), so a fitted "entropy law" would be partly an abundance-and-mass law wearing a thermodynamic costume. Entropy is bounded above by ln(n), and n here is set by RMassBank's formula-annotation success rather than by physics.

**Finding C (negative, and it constrains the claims).** The NCE grid is mismatched to the phenomenon. Median precursor survival yield runs 0.60, 0.085, 0.002, 0.000, 0.000, 0.000 across NCE 15→90. The precursor depletion transition finishes before NCE 45 for most compounds. 45% of complete trajectories are left-censored: survival is already below 0.5 at the lowest available energy. Median count of informative survival points per compound is 2. Any per-compound sigmoid fit to survival yield is fitting two points and four zeros.

**The mandatory change.** Replace spectral entropy with the intensity-weighted normalized spectrum mass,

    mu_i(E) = ( sum_k I_ik(E) * mz_ik ) / ( sum_k I_ik(E) ) / mz_precursor,i

as the primary response, decomposed exactly into precursor survival and fragment depth. In the same sample, mu is monotone in 48 of 56 compounds (86% versus entropy's 32%), has a median within-compound range of 0.44 against a between-compound pooled SD of 0.23, and keeps resolving power across the whole grid where survival yield dies at NCE 45.

**What MURU v1 can honestly aim at.** Not "does fragmentation depend on collision energy" (Li et al. 2021 already published that for entropy across NIST20, and the physics has been settled since RRKM). The open, testable, falsifiable question is whether a molecule-conditional rescaling of the energy axis collapses the family of trajectories onto a shared curve, and whether that rescaling generalizes to chemistry the system has never seen.

**What I already tried, and what it says.** I ran a quick collapse test on the 56-compound sample. Raw NCE gives a binned common-curve R² of 0.420. Center-of-mass energy gives 0.454. The textbook energy-per-degree-of-freedom rescaling gives 0.237, worse than doing nothing. A power-law sweep found its optimum at an exponent of −0.5 (R² 0.501), which points in the opposite direction from RRKM and is more likely absorbing mu's own normalization by precursor mass than revealing physics. Treat that as a warning shot: this design will produce plausible-looking rescalings that are artifacts, and the falsification machinery has to be built before the search engine, not after.

**Conditions attached to the GO.** Phase 1 must clear three gates (§22 states the kill criteria in full). If any gate fails, MURU v1 stops and the Phase 1 audit becomes the deliverable, which is a legitimate outcome.

---

# 2. What MURU v1 actually is

MURU v1 is a falsification-first pipeline that asks one question about one dataset on one instrument.

**The question.** Given energy-resolved MS/MS trajectories for several hundred structurally diverse small molecules measured on a single Q Exactive under HCD, does a compact, interpretable, molecule-conditional function describe how the fragmentation state evolves with collision energy well enough to predict the trajectories of molecules held out by chemical scaffold?

**The system.** Six components, in dependency order:

1. A parser and census layer that turns MassBank LCSB records into an auditable trajectory table with full provenance and every raw metadata string retained.
2. A representation layer that computes a small, pre-registered set of fragmentation functionals with declared sensitivity to preprocessing.
3. A hierarchical statistical layer that separates within-compound energy response from between-compound variation, handles left-censoring at the detection floor, and reports intervals rather than points.
4. A predictive layer that establishes the ceiling of what any model can extract from molecular descriptors plus energy, under scaffold-disjoint splits.
5. A symbolic search layer that runs only after the predictive ceiling is known and only against pre-registered null calibration.
6. A falsification layer that attempts to destroy every candidate before it is allowed to be called anything.

**The output.** A report that states the highest claim level the evidence supports and refuses to state a higher one. A negative report is a completed project.

**What MURU v1 is not.** No LLM touches the numbers. No dashboard. No AutoML sweep. No second dataset until the first one has been exhausted. No claim of mechanism from a curve fit.

---

# 3. Epistemic audit of the current concept

## 3.1 The proposed question, graded

> "Can generalizable mathematical relationships be discovered that describe how molecular fragmentation changes as collision energy changes?"

As written, this is **not well posed**. Three defects.

**Defect 1: the answer is already known and trivially yes.** Fragmentation changes with collision energy. Li et al. (2021) report median NIST20 spectral entropy rising from 0.7–0.8 at <15 eV to 1.8–2.5 at >45 eV, with an initial steep rise, an approximately linear region between 10 and 37 eV, and shallower increase after. My own sample reproduces the shape (median entropy 0.63 → 1.97 across NCE 15→90). Rediscovering this with symbolic regression would be a pipeline test, not a discovery. **Status: VERIFIED that the qualitative relationship exists and is published.**

**Defect 2: "generalizable" is undefined.** Generalizing across energies within a molecule, across molecules within a scaffold, across scaffolds, across ion modes, across instruments, and across chemical space are five different claims with five different evidence bars. The current phrasing lets a weak result be reported as a strong one.

**Defect 3: "mathematical relationship" conflates a fitted curve with a law.** A three-parameter sigmoid fitted per compound is a description. A single functional form whose parameters are predicted from structure and which holds on unseen scaffolds is a candidate regularity. Only the second is worth the machinery.

## 3.2 The repaired question

> **H-MAIN.** There exists a rescaling of the collision energy axis, s_i = g(z_i), depending only on molecular descriptors z_i, and a shared univariate function Phi, such that for every molecule i in the accessible chemical domain, mu_i(E) = Phi(E / s_i) + eps_i(E), with residual variance not exceeding the measurement repeatability of the instrument, and with the collapse holding on molecules whose Bemis-Murcko scaffolds are absent from the fitting set.

This is falsifiable in one line: if a scaffold-disjoint held-out set shows residual structure exceeding replicate noise, H-MAIN is rejected for that domain.

Two subordinate hypotheses give the project graded outcomes rather than pass/fail:

> **H-PARAM.** A shared parametric family Phi(E; theta_i) fits all trajectories, and the parameters theta_i are predictable from z_i out of sample. (Weaker than collapse: allows the shape to vary, not just the scale.)

> **H-NULL-BEAT.** Any structure-aware model beats a structure-blind per-energy population mean on scaffold-disjoint molecules by a margin exceeding the compound-level bootstrap interval.

H-NULL-BEAT is the floor. If it fails, nothing above it can be claimed.

## 3.3 Epistemic status of the project's current assumptions

| Assumption in project files | Status | Evidence |
|---|---|---|
| Dataset has six NCE levels, 15/30/45/60/75/90, separate runs | **VERIFIED** | Elapavalore 2023 methods section; confirmed in 373 records |
| MassIVE MSV000091754 holds raw and mzML | **VERIFIED** (existence) / **UNKNOWN** (contents, structure) | Stated in paper's Data availability and in each record's `COMMENT: RAW_DATA`; I did not download it |
| 5582 curated spectra from 783 compounds | **VERIFIED** | Paper results section |
| Records are per collision energy, not merged across energies | **VERIFIED** | "up to six records per compound and mode"; confirmed by six distinct records for internal ID 1092 |
| Spectral entropy is a suitable endpoint | **FAILED as primary** | §7.2 below |
| Identity is reliable after 2021 isobar curation | **STRONGLY SUPPORTED** | Paper describes exclusion procedure; all 373 sampled records carry `CONFIDENCE standard compound` |
| Collision energy conventions may be mixed and need parsing care | **VERIFIED, and worse than stated** | `AC$MASS_SPECTROMETRY: COLLISION_ENERGY` carries a bare integer with no unit. Nothing in the record says "NCE" |
| Multiple adducts complicate grouping | **FAILED** (good news) | Only [M+H]+ and [M-H]- appear |
| Technical replicates are available | **FAILED** | Zero duplicate InChIKeys across internal IDs in the sample. The mix-499 replicate set was not deposited as duplicate records |

The last row is the most consequential and I return to it in §9.4.

---

# 4. Dataset audit

## 4.1 Acquisition chain (VERIFIED from Elapavalore et al. 2023)

Ten ENTACT synthetic mixtures containing 1268 ToxCast substances, 95 to 365 per mix. Reverse-phase LC on an Acquity UPLC BEH C18 (1.7 µm, 2.1 × 150 mm), 0.20 mL/min, water with 0.1% formic acid against methanol, gradient 90/10 to 0/100 over 15 minutes. Detection on a Q Exactive Orbitrap HF with ESI in both polarities. MS/MS in data-dependent mode using an inclusion list built from the mixture mass list. Six nominal collision energy settings acquired in separate runs per mixture and mode. Precursor isolation window 1 Da.

Processing: ProteoWizard MSConvert to centroided mzML, Shinyscreen v0.51 prescreening (intensity threshold 1e5, S/N 3, MS2 present, ±2.5 ppm, RT tolerance ±0.5 min), then RMassBank 2.99.2 via RMB-mix 0.2.7 for recalibration, denoising, sub-formula annotation and record export.

Yield: 750 compounds passed prescreening in positive mode, 587 in negative. After the 2021 isobar tightening, 590 positive compounds gave 3411 records and 379 negative compounds gave 2171 records, totalling 5582 records over 783 unique compounds. Mode overlap is therefore 590 + 379 − 783 = **186 compounds measured in both polarities**.

## 4.2 Record-level structure (VERIFIED by direct inspection, n = 373)

Accession scheme: `MSBNK-LCSB-LU<IIII><SS>` where `IIII` is the RMassBank internal compound ID and `SS` is a slot index. Slots 01–06 map to positive mode at NCE 15, 30, 45, 60, 75, 90. Slots 51–56 map to negative mode at the same energies. This is deterministic and removes any need for heuristic grouping.

Homogeneity across all 373 sampled records:

| Field | Values observed |
|---|---|
| `AC$INSTRUMENT` | `Q Exactive Orbitrap (Thermo Scientific)` (373/373) |
| `AC$INSTRUMENT_TYPE` | `LC-ESI-QFT` (373/373) |
| `AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE` | `HCD` (373/373) |
| `AC$MASS_SPECTROMETRY: RESOLUTION` | `17500` (373/373) |
| `COMMENT: CONFIDENCE` | `standard compound` (373/373) |
| `MS$FOCUSED_ION: PRECURSOR_TYPE` | `[M+H]+` (230), `[M-H]-` (143) |
| `COMMENT: DATASET` | `20200303_ENTACT_RP_MIX{499..508}` |

The record instrument string says "Q Exactive Orbitrap" while the paper says "Q Exactive Orbitrap HF". **UNKNOWN** which is correct; it does not affect within-dataset comparisons but does affect any future cross-instrument extension, since Révész et al. (2023, *Mass Spectrom Rev*) report that Orbitrap family members differ from one another even at matched NCE.

Coverage in the sample: 66 compound-by-mode groups, of which 56 (85%) have all six energies, 3 have five, 3 have four, 2 have three, 2 have two.

Peak counts per record: min 1, Q1 6, median 16, Q3 31, max 331. **8% of records carry fewer than four peaks**, where entropy and any distributional summary become unstable.

Mass range in the sample: exact mass 150.1 to 525.1 Da; precursor m/z 151.1 to 526.1.

## 4.3 The processing bias that matters most

Every m/z in `PK$PEAK` also appears in `PK$ANNOTATION` with an assigned sub-formula. **VERIFIED: these are not raw spectra. They are formula-filtered spectra.** RMassBank retains only peaks assignable as sub-formulas of the precursor, with a reanalysis pass permitting extra N2/O.

This cuts both ways and both directions matter.

*Protective.* The mixtures were measured with a 1 Da isolation window, so chimeric contamination from co-eluting neighbours is a real hazard. The sub-formula filter removes most of it, which is why the paper's spectra are usable at all.

*Distorting.* Peak count is now a function of the annotation algorithm's success rate, not of the detector. Any endpoint bounded by peak count, entropy above all, inherits that dependence. Whether annotation success itself varies with collision energy is **UNKNOWN** and is a Phase 1 measurement.

The mitigation is an independent preprocessing branch built from the raw mzML at MSV000091754 for a subset of compounds, with every conclusion required to survive both branches.

## 4.4 Collision energy semantics

The record field reads `AC$MASS_SPECTROMETRY: COLLISION_ENERGY 15` with no unit and no convention marker. The record title reads `CE: 15`. Nothing inside the record identifies this as normalized collision energy. Only the publication does.

**Parser rule (non-negotiable):** MURU stores `raw_value = "15"`, `unit = null`, `energy_type = "NCE_ASSUMED_FROM_PUBLICATION"`, `provenance = "Elapavalore 2023 methods"`, and refuses to merge this with any record whose `energy_type` differs. The field guide in the project already demands this; the data justify it.

## 4.5 Data sufficiency decision

**YES, WITH RESTRICTIONS.**

Sufficient for:
- Estimating population-level energy response of fragmentation functionals with compound-level random effects.
- Testing whether molecular descriptors predict compound-level trajectory parameters on scaffold-disjoint holdouts.
- Testing energy-axis collapse hypotheses on the mu / survival / fragment-depth family.
- Positive and negative mode as two independent replications of the same analysis.

Not sufficient for:
- Per-compound survival-yield midpoints as a continuous target (45% left-censored; see §4.6).
- Any claim of measurement repeatability from the curated layer alone (no technical replicates).
- Cross-instrument or cross-laboratory generality (one instrument, one lab, one acquisition date).
- Absolute-energy (eV) claims transferable to non-Thermo hardware.
- Anything about multiply charged precursors (none present).

## 4.6 The censoring problem, quantified

From the 56 complete trajectories:

| Survival-yield midpoint location | Count | Share |
|---|---|---|
| Below NCE 15 (left-censored) | 25 | 45% |
| In (15, 30] | 20 | 36% |
| In (30, 45] | 8 | 14% |
| In (45, 60] | 3 | 5% |
| Above NCE 90 (right-censored) | 0 | 0% |

Informative survival points per compound, counting only 0.02 < SY < 0.98: 24 compounds have 2, ten have 1, ten have 0, eight have 3, four have 4 or more. **Median 2.**

Read plainly: the experiment placed its six energies mostly above the interesting region. This is not fixable by cleverness. It has to be modelled as censoring, and it caps the resolution of any survival-based conjecture.

---

# 5. Scientific question refinement

The v1 question, restated so that it can fail:

> **Primary.** For [M+H]+ precursors of ENTACT compounds measured by HCD on one Q Exactive at NCE ∈ {15,30,45,60,75,90}, is there a function g of molecular descriptors and a shared shape Phi such that mu_i(E) ≈ Phi(E / g(z_i)) holds on scaffold-disjoint held-out molecules with residual RMSE below the preprocessing-branch disagreement?

> **Secondary.** If collapse fails, does a shared parametric family with structure-predicted parameters (H-PARAM) hold instead?

> **Floor.** Does any structure-aware model beat the per-energy population mean out of sample (H-NULL-BEAT)?

Negative mode runs as an independent replication, not a pooled sample. §10.3 explains why.

Deliberately deferred: mechanism, neutral-loss chemistry, instrument transfer, energy-optimal acquisition recommendations.

---

# 6. Mathematical formulation

## 6.1 The measured object

For molecule i, ion mode m, and setting E, the instrument produces a finite measure on m/z:

    S_i,m(E) = { (mz_k, I_k) : k = 1..n }

with n varying from 1 to 331. Comparing measures directly across molecules is ill-posed because the supports differ. Every candidate endpoint is a functional T[S] mapping the measure to R or R^d.

## 6.2 The energy axis, audited

For Thermo Orbitrap instruments the applied laboratory-frame energy follows

    E_lab(eV) = NCE(%) * (mz_precursor / 500) * f(z)

with f(1)=1, f(2)=0.9, f(3)=0.85, f(4)=0.8, f(5+)=0.75 (Révész et al. 2023 *Mass Spectrom Rev*; Thermo PSB 104; corroborated in J Proteome Res 2022). All precursors here are singly charged, so f = 1.

Single-collision center-of-mass energy against N2 (28 Da):

    E_com = E_lab * 28 / (28 + M_ion)
          = NCE * (M_ion / 500) * 28 / (28 + M_ion)
          = 0.056 * NCE * M_ion / (M_ion + 28)

**This is the single most useful piece of physics for the project.** For M_ion >> 28 the mass factor saturates, so at fixed NCE the center-of-mass energy is nearly mass-invariant. Over the sample's mass range (151–526 m/z) I computed E_com spanning 0.71–0.80 eV at NCE 15 and 4.25–4.79 eV at NCE 90, a spread under 13%.

Two consequences.

First, the worry in §9 of your brief, that NCE is not comparable across precursor masses, **resolves favourably**. Thermo's normalization plus the CoM transformation approximately cancel. NCE is a defensible cross-molecule energy variable for singly charged ions on one instrument.

Second, and less convenient: because E_com is a near-affine function of NCE, **E_com carries almost no information beyond NCE**. Feeding both to a model is redundancy, not physics. The interesting rescalings must involve molecular capacity, not mass alone.

Caveats requiring Phase 1 verification: HCD is a multi-collision regime, so the single-collision formula is an approximation; collision cross-section governs collision number and grows with size; Orbitrap models differ at matched NCE.

## 6.3 Candidate structural forms, evaluated

Write Y_i(E) for the chosen functional.

**(a) Y_i(E) = f(E).** One curve for all molecules. Rejected as a model, retained as the null baseline. Between-compound spread is comparable to within-compound range in my sample (0.23 vs 0.44 for mu).

**(b) Y_i(E) = f(E, z_i).** A single response surface over energy and descriptors. Flexible, and the right form for the machine-learning ceiling estimate. Weak as a scientific object: it does not separate what varies across molecules from what varies with energy.

**(c) Hierarchical: Y_ij = f(E_ij, z_i) + u_i + eps_ij.** Compound-level random effects with descriptor-driven means. **Recommended as the workhorse.** It gives partial pooling for compounds with few usable energies, an explicit variance decomposition, and honest intervals.

**(d) Collapse: Y_i(E) = Phi(E / g(z_i)).** A one-parameter rescaling. The strongest and most falsifiable form, and the one worth chasing. My preliminary sweep says the naive versions fail (§1, Finding C), which makes it a real test rather than a foregone conclusion.

**(e) Parametric curve family with structure-predicted parameters.** Fit Phi(E; theta_i), then regress theta_i on z_i. Standard and defensible. Requires care: theta_i uncertainty must propagate into stage two, otherwise the second-stage fit is overconfident. Use a joint hierarchical fit, not two independent stages.

**(f) Functional data analysis on the trajectory.** With six energy points and an irregular grid, FPCA is over-machinery. Deferred.

**(g) Derivative or threshold objects.** dY/dE on six points is a noise amplifier. Threshold energies are the censored survival midpoint already discussed. Both deferred.

**Decision: (c) as the estimation backbone, (d) as the hypothesis under test, (e) as the fallback, (b) for ceiling estimation only.**

## 6.4 Censoring

Survival yield hits exact zero in 43% of NCE 45 records and 92% of NCE 90 records. Those zeros are detection-limit events, not measurements of zero. The likelihood must treat them as left-censored below the instrument's effective floor, estimated from the intensity threshold used in prescreening (1e5) relative to the record's total ion current. Fitting untransformed zeros with Gaussian error would manufacture bias in exactly the direction that makes curves look sharper than they are.

---

# 7. Spectrum representation strategy

## 7.1 The pre-registered candidate set

Ten dimensions of evaluation were requested. The table condenses them; the discussion below handles the ones that decide the design.

| Functional | Definition | Physical meaning | Preprocessing sensitivity | Cross-molecule comparable | Monotone in my sample | Verdict |
|---|---|---|---|---|---|---|
| **mu** (normalized weighted mass) | sum(I·mz)/sum(I)/mz_prec | extent of mass loss | low (intensity-weighted) | yes, dimensionless | **48/56 (86%)** | **PRIMARY** |
| **SY** (survival yield) | I(precursor)/sum(I) | precursor depletion | moderate (precursor identification) | yes | 55/56 | **PRIMARY, censored** |
| **phi** (fragment depth) | weighted mean fragment mz / mz_prec | secondary fragmentation | low | yes | 42/56 (75%) | **PRIMARY** |
| Spectral entropy S | −sum(p ln p), p = I/sum(I) | information content | **high** (peak count, noise floor, annotation) | contested | 18/56 (32%) | SECONDARY / robustness |
| Normalized entropy S/ln(n) | as above | shape only | high | yes | not assessed | DIAGNOSTIC only |
| Peak count n | count | fragment richness | **very high** | no (mass-confounded) | 11/56 (20%) | COVARIATE only |
| Adjacent-energy similarity | entropy similarity of S(E_j), S(E_j+1) | trajectory speed | moderate | yes | n/a | EXPLORATORY |
| Neutral-loss distribution | mz_prec − mz_k spectrum | chemistry-specific | moderate | partly | n/a | DEFERRED to v2 |
| Latent spectral embedding | learned | none | n/a | n/a | n/a | REJECTED for v1 |

The exact decomposition tying the three primaries together:

    mu_i(E) = SY_i(E) * 1 + (1 − SY_i(E)) * phi_i(E)

mu is a convex combination of the precursor's contribution and the fragments' mean normalized mass. It answers your concern about crushing a rich spectrum into a crude scalar: mu is not an arbitrary summary, it is the first moment of the normalized mass distribution, and it factors exactly into two separately interpretable physical quantities. Survival dominates it at low energy, fragment depth at high energy, which is why it keeps dynamic range across the whole grid.

Observed medians across NCE 15 → 90 in my sample: mu 0.867, 0.663, 0.488, 0.443, 0.398, 0.385; phi 0.562, 0.513, 0.460, 0.419, 0.398, 0.385; SY 0.601, 0.085, 0.002, 0.000, 0.000, 0.000.

## 7.2 Why spectral entropy is demoted

Li et al. (2021) established entropy as an excellent *similarity* primitive and documented its collision-energy dependence. Neither fact makes it a good *response variable* for a scaling law here.

1. **Monotonicity.** 18 of 56 compounds. A "law" whose response fails to be monotone in two thirds of subjects is describing something other than the energy input.
2. **Abundance confounding.** Spearman(S, log TIC) is +0.273, +0.246, +0.331 at NCE 60, 75, 90. Brighter spectra reveal more low-intensity peaks, which raises entropy. Li et al. observed the same mechanism when they showed that removing peaks below 1% base-peak intensity collapsed GNPS's high-entropy tail.
3. **Mass confounding.** Spearman(S, mz_prec) is +0.28 to +0.36 for NCE ≥ 30, and Spearman(n_peaks, mz_prec) reaches +0.435. Bigger molecules give more peaks and thus more entropy at fixed energy.
4. **Annotation dependence.** S ≤ ln(n), and n here is set by RMassBank's formula assignment.
5. **Small-n instability.** Median peak count at NCE 15 is 5. Entropy from five peaks is a fragile statistic.

Entropy stays in the pipeline as a robustness endpoint: any conclusion that holds for mu should be checked against entropy, and disagreement is itself a reportable result.

## 7.3 Preprocessing sensitivity protocol

Every conclusion is computed under a grid of preprocessing choices and reported as a range, not a point:

- Relative intensity cutoff: {0, 0.1%, 1%} of base peak. (I measured that a 1% cutoff halves median peak count at NCE 90, from 25 to 15, while moving median entropy from 2.01 to 1.99. Entropy is more robust to this than to abundance. Worth stating.)
- Precursor peak: included / excluded.
- Intensity transform: raw / square root. (Square root is the classical dot-product weighting; it changes mu's weighting and therefore must be tested, not assumed.)
- Source branch: RMassBank formula-filtered records / independently reprocessed mzML for a subset.

A conclusion that survives one cell of this grid and dies in another is INCONCLUSIVE, not discovered.

---

# 8. Molecular representation strategy

## 8.1 Is structure necessary?

Yes. In my sample the between-compound pooled SD of mu is 0.232 against a median within-compound range of 0.440. Roughly a third of total variance sits between molecules at fixed energy. A structure-blind model gives that up by construction.

## 8.2 The descriptor tier system

Descriptors serve three incompatible purposes, and mixing them destroys interpretability. MURU keeps them separated by tier and each tier is used only where declared.

**Tier A: physics-facing, symbolic-regression eligible (target ≤ 12).**
These enter symbolic search. Each has a dimensional interpretation and a mechanistic rationale.

| Descriptor | Rationale |
|---|---|
| Precursor m/z | sets E_lab and E_com; unavoidable |
| Heavy-atom count | proxy for vibrational degrees of freedom (3N−6) |
| Total atom count including H | exact DOF proxy |
| Rotatable bond count | low-frequency mode density, energy sink capacity |
| Ring count and aromatic ring count | stabilizing substructures, raises dissociation thresholds |
| Degree of unsaturation (RDBE) | rigidity, bond-strength proxy |
| Heteroatom fraction (N, O, S, halogen counts) | charge localization and preferred cleavage sites |
| TPSA | proton affinity / charge localization proxy |
| Estimated molecular volume or CCS proxy | collision cross-section, controls collision number in HCD |

**Tier B: predictive, not symbolic (used only for ceiling estimation).**
Morgan fingerprints (radius 2, 2048 bits), full RDKit descriptor block, Mordred subset if justified. These answer "how much signal is there at all". They never appear in a conjecture.

**Tier C: rejected for v1.**
Learned embeddings, graph neural network features, quantum-chemical descriptors requiring DFT. The first two destroy interpretability; the third is a research project of its own.

## 8.3 Rules

- Tier A descriptors are frozen before any modelling and recorded with hashes.
- The gap between Tier B ceiling performance and Tier A performance is a reported quantity. A large gap means the interpretable model is missing real signal and the conjecture's domain is narrower than claimed.
- Descriptors are computed from `CH$SMILES` after RDKit sanitization, with failures logged and excluded rather than silently repaired.
- The MS-ready SMILES problem documented in Elapavalore et al. §Curation (stereochemistry stripped, salts removed, wrong names retrieved) means SMILES quality must be spot-checked against InChIKey in Phase 1.

---

# 9. Statistical design

## 9.1 Unit of analysis

The compound-by-mode trajectory is the unit. n_units ≈ 590 (positive) and ≈ 379 (negative). Records are nested observations, not independent samples. Every standard error, interval, and test statistic is computed at the compound level.

## 9.2 Core model

For compound i at energy E_j, working on the logit scale to respect mu ∈ (0,1]:

    logit(mu_ij) = alpha_i + beta_i * h(E_j) + eps_ij
    alpha_i = a0 + z_i' a + u_i,     u_i ~ N(0, sigma_a^2)
    beta_i  = b0 + z_i' b + v_i,     v_i ~ N(0, sigma_b^2)
    eps_ij ~ N(0, sigma_e^2)

with h a monotone energy transform (identity, log, or the fitted rescaling under test). Correlated random effects (u_i, v_i) via an LKJ prior. Fit in PyMC with NUTS; report R-hat, ESS, and posterior predictive checks.

For survival yield the same skeleton with a censored likelihood:

    SY_ij ~ Beta(mu_s, kappa)  truncated,  with P(SY < d_ij) integrated for censored observations

where d_ij is the detection floor implied by the prescreening intensity threshold relative to record TIC.

**Why Bayesian here rather than a frequentist mixed model.** Three reasons, each concrete: left-censoring plus nonlinear link is awkward in `statsmodels`; partial pooling matters because 15% of trajectories have fewer than six energies; and parameter uncertainty must propagate into the symbolic-regression target, which requires a posterior, not a point estimate. If Phase 2 shows censoring is negligible for mu (likely) then a `statsmodels` MixedLM is acceptable for mu alone and the Bayesian machinery is reserved for SY.

## 9.3 Variance decomposition as a first-class result

Report the intraclass correlation and the share of total variance attributable to: energy (fixed), compound identity (random), descriptor-explained between-compound variation, and residual. If descriptor-explained variation is a small fraction of between-compound variation, the honest conclusion is that structure explains little at this resolution, and MURU says so.

## 9.4 The replicate problem

**VERIFIED:** the curated MassBank layer contains no technical replicates. Zero InChIKeys map to more than one internal ID in my sample of 53 unique compounds.

This matters because without a repeatability estimate there is no yardstick for "residual smaller than measurement noise", and H-MAIN as written needs one.

Three routes, in order of preference:

1. **Raw-data replicates (preferred).** Elapavalore et al. state that mix 5 (503) included the replicate set of mix 1 (499) and mix 7 (505) included it again. Roughly 95 compounds were therefore injected three times. Those runs exist in MSV000091754 even though only one made it into MassBank. Extracting them for ~95 compounds × 6 energies × 2 modes gives a proper repeatability estimate. **This is the single highest-value Phase 1 task.**
2. **Within-run scan replicates.** DDA usually acquires multiple MS2 scans across an LC peak. RMassBank merged them (`DATA_PROCESSING MERGING`). The unmerged scans in the mzML give a lower bound on noise.
3. **Cross-mode consistency (weakest).** The 186 dual-mode compounds are not replicates, but systematic disagreement between modes bounds how much of the signal is chemistry versus ionization artifact.

If none of these yields a repeatability estimate, H-MAIN must be weakened to a comparative claim (collapse beats no collapse) rather than an absolute one (residual within noise). That weakening must be stated in the report, not absorbed silently.

## 9.5 Statistical power

Rough figures for planning, to be refined in Phase 1 with real variance components.

With 590 positive-mode compounds and a 60/20/20 scaffold-disjoint split, the confirmation set holds ~118 compounds. For a compound-level correlation between predicted and observed trajectory parameters, n = 118 gives a 95% CI half-width of about ±0.15 at rho = 0.5. Detecting rho = 0.5 against rho = 0 has power >0.99; detecting rho = 0.2 has power near 0.55. **MURU can credibly detect a moderate structure-trajectory relationship and cannot credibly detect a weak one.** State that limit in the report rather than discovering it afterwards.

For the collapse test, the relevant quantity is the reduction in held-out residual variance from adding g(z_i). A 5 percentage-point R² improvement of the kind my exploratory sweep produced (0.449 → 0.501) is inside the bootstrap noise band at n = 56 and will need the full corpus plus a locked confirmation set to be believable.

---

# 10. Leakage control and data splitting

## 10.1 The minimum

Compound-level grouping, enforced by InChIKey first block (connectivity layer):

    train ∩ val = ∅,  train ∩ test = ∅,  val ∩ test = ∅

Splitting spectra rather than compounds would put NCE 15 and NCE 30 of the same molecule on opposite sides of the wall. That is the trivial failure mode and the project files already warn about it.

## 10.2 Why compound-level is not enough

ENTACT mixtures were assembled from ToxCast, which contains dense congeneric series: chlorinated phenols, phthalate esters, triazines, homologous alkyl chains. Two compounds differing by one methylene have near-identical descriptors and near-identical fragmentation. Splitting them across the wall inflates apparent generalization.

## 10.3 The split hierarchy, with the claim each supports

| Split | Construction | Claim licensed |
|---|---|---|
| **S0: random spectrum** | none | none. Diagnostic only, reported as the leakage upper bound |
| **S1: compound (InChIKey)** | group by connectivity | "generalizes to unseen measurements of unseen molecules" |
| **S2: Bemis-Murcko scaffold** | group by scaffold | "generalizes to unseen core structures" |
| **S3: Butina cluster** | Tanimoto ≤ 0.6 on Morgan-2, cluster-disjoint | "generalizes to chemically dissimilar molecules" |
| **S4: mode transfer** | fit positive, test negative on the 186 dual-mode compounds | "the relationship is not an artifact of positive-mode chemistry" |

**Recommendation.** Report S1, S2, and S3 for every headline result. S2 is the primary claim vehicle: scaffold-disjoint is the standard bar in cheminformatics and is neither trivially easy nor artificially punitive. S3 is the stress test. S0 is reported only to show the size of the leakage gap.

**Do not** merge polarities into one training set. Positive and negative ESI produce different precursor ions, different charge localization, and different fragmentation chemistry. Li et al. (2021) measured systematically higher entropy and steeper collision-energy response in positive mode. Pooling would confound ionization with structure. Run positive as the primary experiment and negative as an independent replication with its own splits, its own baselines, and its own pre-registration.

## 10.4 Additional leakage vectors specific to this dataset

- **Mix identity.** All six energies of a compound come from the same mixture and the same day. Mix complexity affects co-isolation. Include `COMMENT: DATASET` as a covariate and test whether results survive holding out entire mixes.
- **Retention time.** Co-eluting compounds share matrix conditions. Check that RT does not act as a hidden grouping variable.
- **Internal ID adjacency.** Sequential internal IDs correlate with position in the input compound list, which may correlate with chemical class. Verify that random splits on ID do not accidentally group chemistry.

## 10.5 The confirmation set

20% of compounds, selected by scaffold before any analysis, hashed, and written to a file that the analysis code refuses to read until the pre-registration document is frozen. Opened once. If a result needs a second look at the confirmation set, that is a new experiment requiring a new pre-registration and disclosure in the report.

---

# 11. Baselines

MURU must beat these before any complicated method earns a paragraph in the report. Ordered by ascending sophistication; each evaluated under S1, S2, and S3.

| # | Baseline | What it tests |
|---|---|---|
| B0 | Global mean of mu | floor |
| B1 | Per-energy mean of mu (structure-blind, energy-aware) | is there any energy signal at all |
| B2 | B1 + linear precursor m/z term | is the "structure effect" just mass |
| B3 | Linear regression on Tier A descriptors × energy | is the relationship linear |
| B4 | Natural cubic spline in energy with compound random intercept | is a smooth energy shape enough |
| B5 | GAM: s(energy) + s(mass) + tensor interaction | is the nonlinearity separable |
| B6 | Hierarchical logit model (§9.2) | the reference scientific model |
| B7 | Gradient-boosted trees on Tier B descriptors + energy | predictability ceiling |

**The decisive comparison is B7 versus B6 versus B2.** If B7 barely beats B2, the dataset contains a mass effect and little else, and MURU should say so and stop. If B6 approaches B7, the interpretable model captures nearly everything and symbolic regression has a real target. If B7 crushes B6, there is nonlinear structure that Tier A descriptors cannot express, and any symbolic result will describe a fraction of the phenomenon.

Every baseline reports compound-level bootstrap intervals. A method that beats another by less than the interval width has not beaten it.

---

# 12. Machine learning strategy

## 12.1 The one job machine learning has here

Estimate the predictability ceiling. Nothing else.

With ~590 compounds and ~12 physics-facing descriptors, machine learning will not discover chemistry. It will tell you how much of the between-compound variance in trajectory shape is recoverable from structure at all. That number sets the bar symbolic regression must approach to be worth reporting.

## 12.2 Model selection

**Primary: gradient-boosted trees** (LightGBM or `sklearn.ensemble.HistGradientBoostingRegressor`). Justification: n ≈ 590 groups with mixed continuous and count descriptors, strong interactions expected, and tree ensembles are close to optimal in this regime. Hyperparameters tuned by nested grouped cross-validation with the outer loop scaffold-disjoint.

**Secondary: Gaussian process with a Tanimoto or Matérn kernel.** Justification: calibrated predictive variance, which matters for deciding whether a held-out miss is a model failure or an out-of-domain molecule. Feasible at this n.

**Rejected: neural networks of any kind.** With ~590 units, a deep model would be estimating more parameters than it has trajectories, and the variance would swamp any interpretation. If someone later argues for a GNN, the argument must include a power calculation.

**Rejected: AutoML.** It multiplies researcher degrees of freedom, which §14 exists to control.

## 12.3 Nested cross-validation

Outer loop: 5-fold scaffold-disjoint. Inner loop: 4-fold scaffold-disjoint within training folds for hyperparameter selection. Report outer-fold performance only. Any performance number produced by a procedure that saw the outer fold is not reported.

## 12.4 Feature importance, with a warning

Permutation importance on Tier A descriptors, computed on held-out folds, with compound-level permutation. Correlated descriptors (mass, atom count, volume all move together here) make individual importances unstable. Report grouped importances over correlated blocks and state the correlation structure. Do not present a ranked bar chart as if it were causal.

---

# 13. Symbolic regression strategy

## 13.1 Gating condition

Symbolic regression runs only if **all** of:

- B6 or B7 beats B1 on scaffold-disjoint splits by more than the compound bootstrap interval, and
- the null calibration (§13.6) shows the search engine finds no comparable expression under permuted targets, and
- Phase 3 synthetic recovery succeeded at the noise level measured in Phase 1.

If any fails, MURU reports "symbolic regression not warranted" and that is a completed Phase 4.

## 13.2 What it operates on

Not raw mu_ij. Three targets, in order:

**T1 (primary): the shared shape and rescaling.** Search jointly for g(z_i) and Phi such that mu_ij ≈ Phi(E_j / g(z_i)). Implement by alternating: fix Phi as a flexible monotone fit, search symbolically for g; fix g, search symbolically for Phi. Two to three alternations, with the whole loop treated as one search for multiplicity accounting.

**T2 (fallback): posterior-mean trajectory parameters.** From the hierarchical fit, take alpha_i and beta_i and search for symbolic expressions in Tier A descriptors. Weight each compound by the inverse posterior variance of its parameter so that poorly determined compounds do not drive the expression.

**T3 (diagnostic): direct mu_ij = f(E, z_i).** Runs for comparison only, because it lets the search absorb the energy shape and the structure dependence into one expression and is therefore the easiest place to overfit.

## 13.3 Engine

**Recommendation: PySR** (Cranmer 2023, `SymbolicRegression.jl` backend).

Reasons specific to this problem: multi-objective Pareto front over accuracy and complexity, which is exactly the trade-off MURU needs to report; custom loss functions, needed for the inverse-variance weighting in T2; constraint support for monotonicity and limit behaviour; nested-operator restrictions to block `exp(exp(x))`-style pathologies; and a benchmark record on recovering known empirical laws (EmpiricalBench).

**Not SINDy.** SINDy identifies governing equations of dynamical systems from time-series derivatives. There is no time here, six energy points cannot support derivative estimation, and the candidate library approach would restrict the answer to linear combinations of pre-chosen terms. Using it would be method theatre.

**Comparison arm:** run `gplearn` on T2 as a cheap independent engine. If two engines with different search dynamics converge on equivalent expressions, that is evidence. If they do not, the expression is a search artifact.

## 13.4 Search configuration

- Operators: `+, -, *, /, ^` with integer or half-integer exponents only; `log`, `exp`, `sqrt`. No trigonometric functions; nothing in this physics oscillates.
- Complexity budget: maximum complexity 20, with the Pareto front reported in full. The reported candidate is chosen by the complexity elbow, not by best fit.
- Dimensional discipline: all inputs pre-scaled to dimensionless quantities (E in NCE units divided by 30, masses divided by 500 Da, counts divided by their median). This makes fitted constants O(1) and interpretable, and it prevents the search from spending complexity on unit conversion.
- Constants: optimized by the engine's inner BFGS; final constants re-fitted by weighted least squares on the training set only.
- Runs: **30 independent seeds minimum.** Stochastic search variance is the dominant source of irreproducibility in symbolic regression and a single run tells you nothing about stability.

## 13.5 Ranking and equivalence

Rank candidates by held-out (validation-fold) error at matched complexity, then by **selection frequency across the 30 seeds**. An expression recovered by 24 of 30 seeds is a different object from one recovered once.

Detect equivalent formulas by canonicalizing with SymPy (`simplify`, `powsimp`, `cancel`) and additionally by numerical fingerprinting: evaluate each candidate on a fixed 10,000-point Latin hypercube over the descriptor domain and cluster by correlation above 0.999. Algebraic simplification alone misses reparameterizations.

## 13.6 Null calibration

Before any real search, run the identical pipeline on:
- targets permuted across compounds within energy,
- targets permuted across energy within compound,
- descriptors permuted across compounds,
- Gaussian noise targets with the observed variance structure.

Record the distribution of best held-out R² at each complexity level over 30 seeds each. **A real candidate must exceed the 95th percentile of the matched null at its own complexity.** Without this the Pareto front is uninterpretable, because genetic programming will always return something.

## 13.7 Expected overfitting severity

High. Six energy levels, a discrete grid, and ~590 groups is a small-data regime for a search over an unbounded expression space. Concretely: with 3411 positive-mode records the effective sample size for a between-compound relationship is 590, and PySR evaluates on the order of 10^6 expressions per run. The multiplicity is severe and §14 is not optional.

---

# 14. Multiple hypothesis safeguards

## 14.1 Pre-registration

Before Phase 2 modelling, MURU writes `PREREGISTRATION.md` containing: the primary endpoint, the split definitions with the confirmation-set compound list hashed, the Tier A descriptor list, the baseline set, the primary metric, the decision thresholds, the falsification ladder criteria, and the kill criteria. The file is committed, hashed, and the hash appears in the final report. Any deviation is logged in `DEVIATIONS.md` with a reason and appears in the report.

This is the cheapest and strongest safeguard available and it costs one afternoon.

## 14.2 The three-tier data wall

- **Discovery set (60% of compounds):** unlimited exploration, model selection, feature engineering, symbolic search.
- **Validation set (20%):** used for candidate ranking and the falsification ladder up to rung L3. Used repeatedly; treated as contaminated for final inference.
- **Confirmation set (20%):** opened once, after the candidate is frozen. Every number computed on it appears in the report whether flattering or not.

## 14.3 Formal multiplicity control

- **Permutation-calibrated significance** for the headline collapse test: 1000 compound-label permutations, empirical p-value.
- **Benjamini-Hochberg FDR at q = 0.10** across the family of endpoint × split × preprocessing-branch tests, with the family declared in the pre-registration.
- **Complexity-adjusted selection** for symbolic candidates via the null-calibrated threshold in §13.6, which is a per-complexity multiplicity correction.
- **Cluster bootstrap over compounds** (2000 resamples) for every reported interval. Resampling records rather than compounds would understate uncertainty by roughly sqrt(6).

## 14.4 Minimum effect sizes, declared in advance

- Collapse hypothesis: a candidate rescaling must reduce held-out residual variance by ≥ 15% relative to no rescaling, with the lower bound of the bootstrap interval above zero.
- Structure-explains-variation: descriptor-driven between-compound variance share ≥ 0.20.
- Symbolic value-add: the symbolic expression must reach ≥ 80% of the Tier B ceiling's held-out R² at complexity ≤ 20.

Effect sizes below these thresholds are reported as null results regardless of p-value.

---

# 15. Uncertainty strategy

| Quantity | Method | Why legitimate here |
|---|---|---|
| Population energy response | posterior credible interval from the hierarchical fit | correct nesting, handles unbalanced coverage |
| Compound-level trajectory parameters | posterior with partial pooling | 15% of trajectories are incomplete; shrinkage is the honest answer |
| Held-out predictive error | cluster bootstrap over compounds, 2000 resamples | preserves the dependence structure |
| Model comparison (B6 vs B7) | paired cluster bootstrap of the difference | avoids comparing two independently noisy point estimates |
| Symbolic expression stability | selection frequency across 30 seeds plus bootstrap-resampled searches | quantifies search variance, which no other method captures |
| Fitted symbolic constants | profile likelihood or posterior from a Bayesian refit of the frozen structure | the structure is not re-searched, so this interval is valid |
| Measurement repeatability | replicate variance from the raw-data subset (§9.4) | the only route to an absolute noise floor |

**What is not legitimate.** Analytic standard errors from a model fitted after model selection. Cross-validation standard errors treated as confidence intervals. Any interval on a symbolic expression's parameters that ignores the search that produced the structure. MURU reports the last as "conditional on the selected structure" every time.

---

# 16. Falsification framework

## 16.1 The ladder

A candidate ascends only by passing every rung. Failure at any rung sends it to REJECTED or INCONCLUSIVE, never sideways.

**F1. Reproducibility.** Identical result from a clean checkout, pinned environment, recorded seeds. Failure means the result does not exist.

**F2. Preprocessing invariance.** Survives the §7.3 grid. Sign and rough magnitude must persist across all cells. A conclusion that flips when the intensity cutoff changes from 0.1% to 1% is a preprocessing artifact.

**F3. Source-branch invariance.** Survives on independently reprocessed mzML for the subset. This is the test for RMassBank formula-filter artifacts and it is the one most likely to kill entropy-based results.

**F4. Compound holdout (S1).** Held-out molecules, compound-disjoint.

**F5. Scaffold holdout (S2).** Held-out Bemis-Murcko scaffolds. **This is the primary claim gate.**

**F6. Chemical-dissimilarity holdout (S3).** Butina clusters at Tanimoto 0.6.

**F7. Influence robustness.** Leave-one-cluster-out and leave-one-mix-out. Drop the 5% most influential compounds by Cook's-distance analogue and refit. A relationship carried by fifteen molecules is not a relationship.

**F8. Descriptor ablation.** Remove each Tier A descriptor and each correlated block. If removing precursor mass destroys the result, the "law" is a mass law. Report it as such.

**F9. Energy-subset stability.** Refit on {15,30,45}, on {45,60,75,90}, and on the odd-index subset. A form that only exists on the full six-point grid is describing the grid.

**F10. Negative controls.** The candidate must fail on permuted data (§17). Passing under permutation invalidates the pipeline, not the candidate.

**F11. Mode replication (S4).** Does the positive-mode result hold in negative mode? Failure does not reject the candidate; it narrows its declared domain and must be stated.

**F12. Extrapolation probe.** Predict at energies excluded from fitting. Weak here (only six levels), so it is reported as supporting evidence and never as a gate.

## 16.2 Status system with objective transitions

| Status | Entry criteria |
|---|---|
| **L0 PIPELINE VERIFIED** | F1 passed; synthetic recovery succeeded; nulls calibrated |
| **L1 ENERGY DEPENDENCE ESTABLISHED** | B1 beats B0 on held-out compounds beyond bootstrap interval; F2, F3 passed |
| **L2 CROSS-MOLECULE GENERALIZATION** | L1 plus F4 passed with effect above the §14.4 threshold |
| **L3 STRUCTURE-EXPLAINED VARIATION** | L2 plus F5 passed; descriptor-driven between-compound variance share ≥ 0.20; F8 shows the effect is not mass alone |
| **L4 SYMBOLIC CANDIDATE** | L3 plus a symbolic expression at complexity ≤ 20 exceeding the null-calibrated 95th percentile, recovered by ≥ 20/30 seeds, reaching ≥ 80% of the Tier B ceiling |
| **L5 VALIDATION SURVIVOR** | L4 plus F6, F7, F9, F10 passed on the validation set |
| **L6 CANDIDATE CONJECTURE** | L5 plus a single pre-registered evaluation on the confirmation set, meeting thresholds set before the set was opened |
| **REJECTED** | any gate failed with the effect estimate's interval excluding the threshold |
| **INCONCLUSIVE** | any gate failed with the interval spanning the threshold, or gate not evaluable |

Nothing is called a conjecture below L6. Nothing is called a discovery at all; L6 is a candidate conjecture requiring independent replication on data MURU never touched.

---

# 17. Negative controls

Mandatory. Run before the real analysis and again alongside it.

| Control | Construction | Pass condition |
|---|---|---|
| **NC1: energy shuffle within compound** | permute the six NCE labels within each trajectory | no energy effect detected; models collapse to B0 |
| **NC2: descriptor shuffle across compounds** | permute z_i rows, keep trajectories | no structure-explained variance beyond chance |
| **NC3: trajectory shuffle across compounds** | permute whole trajectories against descriptors | as NC2, tests the joint distribution |
| **NC4: sham descriptor** | inject a uniform random variable and an alphabetical-name index into Tier A | never selected by symbolic search or feature importance above chance |
| **NC5: synthetic null dataset** | simulate trajectories with realistic noise and zero descriptor dependence | pipeline returns "no relationship" |
| **NC6: mix-label control** | test whether mixture identity predicts trajectory shape | should be near zero; a positive result reveals batch confounding |
| **NC7: retention-time control** | test whether RT predicts trajectory shape | near zero expected; positive indicates matrix or co-elution confounding |

NC6 and NC7 are the two most likely to fire, because the mixtures differ in complexity and co-isolation probability. A positive NC6 does not stop the project; it forces mixture as a covariate and a leave-one-mix-out validation.

**Invalidation rule.** If MURU produces expressions above the null threshold on NC1 through NC3 more than 5% of the time, the pipeline is broken and no real result may be reported until it is fixed.

---

# 18. Synthetic validation strategy

Recommended, and required before any real symbolic search.

## 18.1 What to simulate

A generator producing 600 synthetic compounds with descriptor vectors drawn to match the real Tier A joint distribution (copula fitted to the real descriptors, so correlation structure is preserved rather than idealized).

Ground-truth families, each hidden from the discovery engine:

- **G1 (clean collapse):** mu = Phi(E / g(z)) with g = c1 * m^0.5 and Phi a logistic in log-energy. Tests recovery of the target hypothesis.
- **G2 (no collapse, parametric):** mu = Phi(E; theta(z)) with theta depending on two descriptors, no single-scale collapse. Tests whether MURU correctly rejects H-MAIN while accepting H-PARAM.
- **G3 (mass only):** mu depends on energy and precursor mass and on nothing else. Tests whether MURU correctly reports a mass law rather than inventing chemistry.
- **G4 (pure null):** mu depends on energy only, with compound-level random offsets. Tests false-positive rate.
- **G5 (confounded):** mu depends on energy and on a variable correlated with, but distinct from, the descriptors given to the model. Tests whether MURU overclaims when the true driver is unobserved.

## 18.2 Noise model

Calibrated to Phase 1 measurements, not invented:

- Multiplicative intensity noise with variance estimated from the replicate subset.
- Peak dropout below a detection floor matched to the observed 1e5 threshold.
- Left-censoring of survival at the observed rate.
- Missing energy levels at the observed 15% rate with the observed pattern.
- Formula-annotation dropout matched to the observed annotation rate as a function of fragment mass.

## 18.3 Success criteria

| Case | MURU must |
|---|---|
| G1 | recover g's exponent within ±0.15 and Phi's shape family, at L4 or above |
| G2 | reject H-MAIN, accept H-PARAM, recover theta's descriptor dependence |
| G3 | report "mass law", with F8 ablation identifying mass as the carrier |
| G4 | report no relationship above L1, in ≥ 95% of 100 replicate simulations |
| G5 | report L2 or L3 at most, and flag unexplained between-compound variance |

**G4 is the critical one.** A false-positive rate above 5% across 100 simulated null datasets means the validation system does not work and the real analysis must not proceed.

Synthetic success licenses nothing about real data. It licenses only the statement that the machinery is capable of the discrimination MURU claims to make.

---

# 19. Metrics

| Task | Metric | Why this one |
|---|---|---|
| Trajectory fit | RMSE and MAE on mu, natural scale | mu ∈ (0,1], errors are directly interpretable as fractional mass |
| Trajectory fit, secondary | grouped R² with compound-level bootstrap CI | comparability across baselines; the CI is the part that matters |
| Censored survival | censored log-likelihood; concordance index for ordering | R² on a variable that is 0.000 for 92% of high-energy records is meaningless |
| Cross-molecule ranking | Spearman rho between predicted and observed compound-level parameters | robust to the monotone transform ambiguity in the energy axis |
| Calibration | prediction-interval coverage at 50/80/95%; PIT histogram | a model that is accurate but overconfident fails the falsification ladder |
| Model comparison | paired difference with cluster bootstrap CI | avoids the two-noisy-point-estimates trap |
| Collapse quality | held-out residual variance ratio, with-rescaling over without | directly operationalizes H-MAIN |
| Symbolic candidates | Pareto front of held-out MAE against complexity; null-calibrated excess | complexity is half the objective |
| Symbolic stability | selection frequency over 30 seeds; expression-cluster entropy | the only measure of search reproducibility |
| Preprocessing robustness | range of the effect estimate across the §7.3 grid | reported as a range, always |

**R² is reported but never alone and never as the decision variable.** With grouped data and unbalanced coverage, R² depends on the between-compound variance in the particular split, which changes with the split.


---

# 20. Five-phase master implementation plan

Five phases. No Phase 6. Bugs, refactors, tests, documentation and stabilization live inside phases and never create one.

---

## PHASE 1 — Data reality and measurement audit

### Objective
Establish exactly what the corpus contains, what the collision energy variable means, how much of the observed signal survives preprocessing changes, and what the instrument's repeatability is. Produce a binding go/no-go decision.

### Scientific question
Does this dataset contain a measurable, preprocessing-stable, energy-dependent fragmentation signal that exceeds measurement noise?

### Inputs
The three references (read). The MassBank parser field guide. Network access to `MassBank-data` and MassIVE MSV000091754. Nothing else.

### Workstreams

**W1.1 Corpus acquisition and census.** Pull the LCSB contributor directory at a pinned MassBank release tag. Record release version, retrieval date, and a manifest with per-file SHA-256. Parse every record into a normalized table retaining raw strings for every field.

**W1.2 Grouping and identity.** Build compound-by-mode trajectory groups keyed on InChIKey first block. Verify the accession slot convention (01–06 positive, 51–56 negative) holds corpus-wide rather than only in my 373-record sample. Cross-check `CH$SMILES` against `CH$LINK: INCHIKEY` with RDKit; log every mismatch. Quantify the MS-ready SMILES stereochemistry problem documented by Elapavalore et al.

**W1.3 Collision energy audit.** Confirm every LCSB ENTACT record carries a unitless integer in {15,30,45,60,75,90}. Compute E_lab and E_com per record from the Thermo formula. Verify that no multiply charged precursor exists. Document the unit ambiguity and the `energy_type` provenance chain.

**W1.4 Coverage and censoring census.** Full-corpus versions of the numbers I estimated from 373 records: fraction of groups with all six energies, peak-count distribution by energy, survival-yield distribution by energy, censoring rates, fraction of records with fewer than four peaks.

**W1.5 Raw-data replicate extraction.** Download only the mzML files for mixes 499, 503 and 505 from MSV000091754. Extract MS2 for the ~95 compounds present in all three. Compute the primary functionals on all three replicates. **Deliver a repeatability variance estimate.** This is the highest-value task in the phase.

**W1.6 Independent preprocessing branch.** For the same subset, compute functionals from raw centroided mzML without the RMassBank formula filter. Quantify how much mu, SY, phi and entropy shift between branches. Measure whether formula-annotation success depends on collision energy.

**W1.7 Endpoint screening.** Compute all §7.1 candidate functionals corpus-wide under the §7.3 preprocessing grid. Produce the monotonicity, dynamic-range and confounding table I began here, at full n.

**W1.8 Confounder screening.** Spearman correlations of every endpoint against log TIC, precursor m/z, retention time, mixture identity, and peak count, at each energy.

### Mathematical methods
Shannon entropy S = −Σ p ln p with p = I/ΣI (Li et al. 2021 eq. 1). First moment of the normalized mass distribution for mu. Thermo NCE-to-eV conversion and the CoM transform (§6.2). Variance components by one-way random-effects ANOVA on the replicate subset. Spearman rank correlation for confounder screening. Bootstrap over compounds for all intervals.

### Deliverables
1. `trajectories.parquet` with full provenance columns.
2. `DATA_CENSUS.md` with every count, distribution and coverage figure.
3. `CE_AUDIT.md` documenting energy semantics and the E_com calculation.
4. `REPEATABILITY.md` with the replicate variance estimate, or an explicit statement that it could not be obtained and why.
5. `ENDPOINT_SCREEN.md` ranking candidate functionals on the ten criteria.
6. `CONFOUNDERS.md`.
7. `PHASE1_DECISION.md` with the go/no-go verdict.

### Tests
Parser round-trip on 50 hand-checked records. Slot-convention assertion corpus-wide. Entropy implementation checked against the four worked examples in Li et al. Fig. 1 (entropies 0, 1, 2, 3). Grouping invariance under record ordering. Hash verification of every downloaded file.

### Scientific validation
Recomputed corpus totals must reconcile with the published 3411 positive and 2171 negative records to within a documented difference attributable to release-version drift. A discrepancy larger than 5% requires explanation before the phase closes.

### Acceptance criteria
- [ ] ≥ 400 compound-by-mode groups with ≥ 5 of 6 energies, positive mode
- [ ] Collision energy semantics documented; zero records with ambiguous or out-of-set values silently retained
- [ ] Repeatability estimate delivered, or documented impossibility with the consequence for H-MAIN stated
- [ ] At least one endpoint monotone in ≥ 70% of trajectories with within-compound range exceeding replicate SD by ≥ 3×
- [ ] Preprocessing-branch disagreement quantified for every candidate endpoint
- [ ] `PHASE1_DECISION.md` states GO or STOP with numbered evidence

### Blockers
MassIVE unreachable or mzML unusable, which kills W1.5 and W1.6. Corpus yielding under 250 usable groups. Collision energy values outside the expected set in more than 5% of records.

### Deferred
Negative-mode deep analysis beyond the census. Neutral-loss extraction. ClassyFire class analysis. Any modelling.

### Exit artifact
`PHASE1_DECISION.md`, readable in ten minutes, containing the census table, the repeatability number, the endpoint ranking, and a one-line verdict with the evidence that supports it.

---

## PHASE 2 — Representation, hierarchical baselines and the predictability ceiling

### Objective
Fix the primary endpoint on Phase 1 evidence, build molecule-aware splits, establish the baseline ladder, decompose the variance, and measure how much of the between-compound variation any model can extract from structure.

### Scientific question
Does fragmentation behaviour vary with molecular structure in a way that predicts trajectories for molecules with unseen scaffolds, beyond a structure-blind per-energy mean?

### Inputs
Phase 1 exit artifact with a GO. `trajectories.parquet`. Frozen Tier A descriptor list.

### Workstreams

**W2.1 Pre-registration.** Write and hash `PREREGISTRATION.md` before any model runs. Generate and seal the confirmation set.

**W2.2 Splits.** Implement S0 through S4 (§10.3). Verify disjointness by assertion, not by inspection. Report scaffold and cluster count distributions so that split difficulty is visible.

**W2.3 Descriptors.** Compute Tier A and Tier B from sanitized SMILES. Log failures. Report the Tier A correlation matrix, because it determines how far §12.4 importances can be trusted.

**W2.4 Hierarchical model.** Fit the §9.2 model for mu, and the censored variant for SY. Report variance decomposition, convergence diagnostics, posterior predictive checks.

**W2.5 Baseline ladder.** B0 through B7 under S1, S2, S3 with nested grouped CV and cluster-bootstrap intervals.

**W2.6 Ceiling estimate.** Tier B gradient boosting. Report the Tier B minus Tier A gap.

**W2.7 Negative controls.** NC1 through NC4, NC6, NC7 against the full baseline ladder.

**W2.8 Preprocessing robustness sweep.** Repeat W2.4 and W2.5 headline numbers across the §7.3 grid; report ranges.

### Mathematical methods
Hierarchical generalized linear mixed model with correlated random slopes and LKJ prior; NUTS sampling. Beta likelihood with left-censoring for survival. Natural cubic splines and tensor-product GAMs. Gradient-boosted regression trees. Gaussian process with Tanimoto kernel. Bemis-Murcko scaffold decomposition. Butina clustering on Morgan-2 Tanimoto. Cluster bootstrap. Permutation importance with grouped features.

### Deliverables
1. `PREREGISTRATION.md` (hashed) and the sealed confirmation-set manifest.
2. Split definitions as versioned artifacts.
3. `VARIANCE_DECOMPOSITION.md`.
4. `BASELINES.md`: the full ladder with intervals under three splits.
5. `CEILING.md`: Tier B performance and the Tier A gap.
6. `NEGATIVE_CONTROLS_P2.md`.
7. `PHASE2_DECISION.md` stating the achieved ladder rung (L1, L2 or L3) and whether Phase 4 is authorized.

### Tests
Split-disjointness assertions across all pairs. Leakage canary: a deliberately leaked split must show measurably inflated performance, confirming the harness detects leakage. Descriptor determinism across runs. Model recovery on data simulated from the fitted model's own posterior.

### Scientific validation
Every negative control must return null. Any baseline beating B7 signals a bug. Posterior predictive intervals must cover at nominal rate on held-out compounds.

### Acceptance criteria
- [ ] Splits verified disjoint; leakage canary fires
- [ ] Hierarchical model converged (R-hat < 1.01, ESS > 400 for all reported parameters)
- [ ] Full baseline ladder reported with compound-level intervals under S1, S2, S3
- [ ] Variance decomposition delivered with intervals
- [ ] All negative controls null
- [ ] Ladder rung assigned with the evidence for it
- [ ] Preprocessing ranges reported for every headline number

### Blockers
B7 fails to beat B1 under S2 by more than the bootstrap interval, which triggers kill criterion K4. Negative controls firing, which means a pipeline defect. Sampler non-convergence after reparameterization attempts.

### Deferred
Symbolic regression. Cross-instrument work. Neutral-loss endpoints.

### Exit artifact
`PHASE2_DECISION.md` with the baseline table, the variance decomposition figure, the ceiling gap, and a stated ladder rung.

---

## PHASE 3 — Discovery engine construction and null calibration

### Objective
Build the symbolic search and the falsification harness, then prove on synthetic data with known ground truth that the system recovers real relationships and rejects false ones at the noise level Phase 1 measured.

### Scientific question
Can this discovery system distinguish a true mathematical relationship from a search artifact, at the noise and censoring levels of the real data?

### Inputs
Phase 2 exit artifact authorizing Phase 4. Measured noise model from Phase 1. Frozen endpoint and descriptor definitions.

### Workstreams

**W3.1 Synthetic generator.** Implement G1 through G5 (§18.1) with the §18.2 noise model calibrated to Phase 1.

**W3.2 Symbolic engine.** PySR configured per §13.4, with the T1 alternating collapse search, the T2 inverse-variance-weighted parameter search, and the T3 diagnostic search. `gplearn` comparison arm on T2.

**W3.3 Equivalence and stability tooling.** SymPy canonicalization plus numerical fingerprint clustering (§13.5). Seed-stability accounting over 30 runs.

**W3.4 Null calibration.** Run the full engine on all four null constructions (§13.6). Build the per-complexity null distribution of best held-out R².

**W3.5 Falsification harness.** Implement F1 through F12 as an automated ladder that a candidate is fed into, with machine-readable pass/fail per rung.

**W3.6 Synthetic recovery evaluation.** Run the complete pipeline end to end on G1–G5. Measure recovery rates and, for G4, the false-positive rate over 100 null replicates.

### Mathematical methods
Genetic-programming symbolic regression with Pareto multi-objective selection. Gaussian copula for descriptor simulation. Alternating minimization for the joint (Phi, g) collapse search. Isotonic or monotone spline fitting for Phi during alternation. SymPy canonical forms. Empirical null quantiles.

### Deliverables
1. `synthetic/` generator with recorded seeds and ground-truth equations stored separately from the discovery code path.
2. `NULL_CALIBRATION.md` with per-complexity thresholds.
3. `FALSIFICATION_HARNESS` implementing F1–F12.
4. `SYNTHETIC_VALIDATION.md` with recovery and false-positive rates.
5. `PHASE3_DECISION.md` authorizing or refusing the real search.

### Tests
Ground-truth equations must be unreadable by the discovery code (separate module, verified by import graph). Determinism under fixed seed. Harness must reject a deliberately planted artifact expression. Equivalence detector must merge known-equivalent reparameterizations and separate known-distinct ones.

### Scientific validation
G4 false-positive rate ≤ 5% over 100 replicates. G1 exponent recovered within ±0.15. G3 correctly reported as a mass law.

### Acceptance criteria
- [ ] G1 recovered at L4 or above in ≥ 80% of replicates
- [ ] G2 correctly rejects H-MAIN and accepts H-PARAM
- [ ] G3 identified as mass-only by F8 ablation
- [ ] G4 false-positive rate ≤ 5% over 100 replicates
- [ ] G5 capped at L3 with unexplained variance flagged
- [ ] Null calibration table complete for complexity 1 through 20
- [ ] Harness runs unattended and emits machine-readable rung results

### Blockers
G4 false-positive rate above 5% after two serious repair attempts. This is a BLOCKER by §27 because it invalidates scientific results.

### Deferred
Engine performance optimization. Alternative engines beyond the gplearn arm. LLM-assisted expression phrasing.

### Exit artifact
`SYNTHETIC_VALIDATION.md`, showing that the system found what was hidden and refused what was not there.

---

## PHASE 4 — Real symbolic discovery and falsification

### Objective
Run the calibrated engine on the real corpus, subject every candidate to the full ladder, and open the confirmation set exactly once.

### Scientific question
Does an interpretable expression describe energy-resolved fragmentation across molecules well enough to survive scaffold-disjoint validation and predetermined falsification?

### Inputs
Phase 3 authorization. Frozen pre-registration. Sealed confirmation set.

### Workstreams

**W4.1 Collapse search (T1).** Alternating search for Phi and g on the discovery set. 30 seeds. Pareto fronts retained in full.

**W4.2 Parameter search (T2).** Symbolic expressions for hierarchical posterior parameters, inverse-variance weighted.

**W4.3 Diagnostic search (T3).** Direct surface, for comparison only.

**W4.4 Candidate triage.** Rank by held-out error at matched complexity and by seed selection frequency. Drop everything below the null-calibrated threshold. Expect most candidates to die here; record how many.

**W4.5 Falsification ladder.** Feed survivors through F1–F12 on the validation set.

**W4.6 Confirmation.** Freeze at most three candidates. Open the confirmation set once. Report every number.

**W4.7 Negative-mode replication.** Repeat W4.1 through W4.5 independently on negative mode. Compare, do not pool.

**W4.8 Adjudication.** Assign a final status from §16.2 to every candidate, including the rejected ones.

### Mathematical methods
As Phase 3, applied to real data. Benjamini-Hochberg FDR at q = 0.10 across the declared family. Permutation-calibrated p-values with 1000 compound-label permutations. Cluster bootstrap for all intervals. Profile-likelihood intervals for constants conditional on frozen structure.

### Deliverables
1. `candidates/` with every expression, its Pareto position, seed frequency, and full ladder results, including failures.
2. `FALSIFICATION_RESULTS.md`.
3. `CONFIRMATION.md` recording the single confirmation-set evaluation.
4. `NEGATIVE_MODE_REPLICATION.md`.
5. `ADJUDICATION.md` assigning final statuses.

### Tests
Confirmation set access is guarded by code that fails loudly if the pre-registration hash does not match. Ladder results reproducible from stored artifacts. Rejected candidates persisted, not discarded.

### Scientific validation
Negative controls rerun alongside the real search, same session, same seeds family. Preprocessing grid applied to every surviving candidate.

### Acceptance criteria
- [ ] All three searches run with ≥ 30 seeds and full Pareto fronts stored
- [ ] Every candidate above the null threshold passed through the complete ladder
- [ ] Confirmation set opened exactly once, with the access log recorded
- [ ] Every candidate assigned a status, with rejected candidates documented
- [ ] Negative-mode replication reported independently
- [ ] Zero candidates above L1 without ladder evidence

### Blockers
Confirmation set opened prematurely, which is unrecoverable and forces the report to declare the confirmation invalid. Ladder failure at F1, meaning results are not reproducible.

### Deferred
Cross-instrument replication. Mechanistic interpretation beyond what F8 supports. Third-party dataset.

### Exit artifact
`ADJUDICATION.md`: one table, every candidate, final status, evidence.

---

## PHASE 5 — Reproducibility package and research report

### Objective
Produce a report whose claims match the evidence exactly, plus an artifact a stranger can rerun.

### Scientific question
What can be truthfully claimed, and at what level?

### Inputs
Phase 4 adjudication and all prior artifacts.

### Workstreams

**W5.1 Claims audit.** Map every sentence in the report making an empirical claim to a specific artifact and ladder rung. Any claim without a mapping is deleted or demoted.

**W5.2 Report.** Structured to §23's ladder: state the highest supported level and the evidence for stopping there.

**W5.3 Reproducibility package.** Pinned environment, seeds, data manifest with hashes, split definitions, pre-registration and deviations, one-command rerun for the headline figures.

**W5.4 Negative-result completeness.** Every rejected candidate, every failed gate, every preprocessing cell where a result reversed. Rejected material is content, not appendix filler.

**W5.5 Limitations.** Single instrument, single lab, single acquisition date, formula-filtered spectra, censored survival grid, no cross-instrument transfer, and the specific chemical domain of ENTACT.

**W5.6 Deferred-work register.** What v2 would need, ranked.

### Mathematical methods
None new. Figure regeneration from stored artifacts only.

### Deliverables
1. `REPORT.md` (and PDF).
2. `REPRODUCIBILITY.md` with the manifest and rerun instructions.
3. `LIMITATIONS.md`.
4. `BACKLOG.md`.
5. Tagged release with a DOI if archived.

### Tests
Clean-checkout rerun reproduces every headline number within seed tolerance. Every figure regenerates from stored artifacts. Every claim traces to an artifact.

### Scientific validation
An independent reader following `REPRODUCIBILITY.md` reproduces the headline table. The claims audit shows no claim exceeding its ladder rung.

### Acceptance criteria
- [ ] Every empirical claim mapped to an artifact and rung
- [ ] Highest claimed level equals the highest achieved level, with no gap and no overshoot
- [ ] Clean-checkout rerun succeeds
- [ ] Negative results reported at the same prominence as positive ones
- [ ] Limitations enumerate every restriction in §4.5
- [ ] Pre-registration hash and deviations published

### Blockers
Clean-checkout rerun failing. A claim that cannot be traced to an artifact.

### Deferred
Journal formatting, conference materials, v2 planning.

### Exit artifact
`REPORT.md`, with a first page stating the achieved level and the reason it is not higher.

---

# 21. Exact Definition of Done

MURU ConjectureLab v1 is complete when every item below is true. Completion does not require a positive scientific result.

**Data and provenance**
1. The corpus is ingested from a pinned MassBank release with a per-file hash manifest and recorded retrieval date.
2. Every collision energy value carries its raw string, parsed value, declared `energy_type`, and provenance for that declaration.
3. Compound-by-mode groups are constructed on a stable structural identifier, with identity mismatches logged rather than repaired.

**Representation**
4. The primary endpoint was chosen from measured evidence in Phase 1, not assumed in advance, and the selection record exists.
5. Every endpoint's sensitivity to the §7.3 preprocessing grid is quantified and reported.
6. At least one conclusion was checked against an independent preprocessing branch built from raw mzML.

**Statistics**
7. Splits are compound-disjoint, scaffold-disjoint and cluster-disjoint variants, verified by assertion, with a leakage canary demonstrating the harness detects leakage.
8. The baseline ladder B0–B7 is reported with compound-level bootstrap intervals under S1, S2 and S3.
9. Variance is decomposed into energy, compound, descriptor-explained and residual components with intervals.
10. Either a measurement repeatability estimate exists, or its absence is stated together with the specific claim it prevents.

**Discovery machinery**
11. Synthetic validation demonstrates recovery of hidden relationships and a false-positive rate ≤ 5% on null data over 100 replicates.
12. Null calibration thresholds exist per complexity level and every symbolic candidate was compared against them.
13. Symbolic search ran with ≥ 30 seeds and the full Pareto front is stored.

**Falsification**
14. Every candidate above the null threshold passed through F1–F12 with machine-readable results, and rejected candidates are retained in the artifact set.
15. The confirmation set was opened exactly once, after freezing, with the access logged.
16. All seven negative controls returned null.

**Reporting**
17. A pre-registration file exists with a published hash, and all deviations from it are documented.
18. Every empirical claim in the report maps to an artifact and a ladder rung.
19. The report's highest claim equals the highest achieved rung.
20. A clean checkout reproduces the headline numbers.

**Explicit non-requirements.** A positive result. A published equation. Any performance threshold. A second dataset. Cross-instrument validity.

A report reading "No candidate relationship survived scaffold-disjoint validation; the strongest observed effect was a mass-dominated energy response reaching level L2" satisfies this definition completely.

---

# 22. Kill criteria

Each states its trigger, its evidence, and where MURU goes instead. Sunk cost is not a defence.

**K1 — Insufficient usable compounds.**
*Trigger:* fewer than 250 positive-mode compound-by-mode groups with ≥ 5 of 6 energies after quality filtering.
*Detection:* Phase 1, W1.4.
*Alternative:* pivot the corpus to MassBank contributors with dense collision-energy series on comparable Orbitrap hardware (Eawag and BAFG are the obvious candidates), accepting cross-instrument heterogeneity as an explicit modelled factor. Requires its own audit and probably its own Phase 1.

**K2 — Collision energy semantics unresolvable.**
*Trigger:* more than 5% of records carry energy values that cannot be assigned a convention, or evidence emerges that the six settings were not applied as documented.
*Detection:* Phase 1, W1.3.
*Alternative:* restrict to the resolvable subset if ≥ 250 groups remain; otherwise stop and re-source.

**K3 — Signal below noise.**
*Trigger:* within-compound endpoint range fails to exceed replicate SD by ≥ 3× for every candidate endpoint.
*Detection:* Phase 1, W1.5 with W1.7.
*Alternative:* the question changes from "how does fragmentation vary with energy" to "what is the reproducibility of energy-resolved MS/MS", which is a publishable methods result and uses the same Phase 1 machinery.

**K4 — No out-of-sample predictability.**
*Trigger:* B7 fails to beat B1 under S2 by more than the compound bootstrap interval.
*Detection:* Phase 2, W2.5 and W2.6.
*Alternative:* report the negative result at L1 and stop. Do not run symbolic regression on a signal that does not generalize. The honest headline is that trajectory shape is not predictable from Tier A or Tier B descriptors at this sample size.

**K5 — Structure explains nothing beyond mass.**
*Trigger:* descriptor-driven between-compound variance share below 0.20, or F8 ablation shows removing precursor mass destroys the effect.
*Detection:* Phase 2, W2.4 and W2.7.
*Alternative:* reframe as "energy response is governed by precursor mass under NCE normalization", verify against the §6.2 physics, and report it. That is a smaller but real and defensible finding.

**K6 — Discovery system fails its own null test.**
*Trigger:* G4 false-positive rate above 5% after two serious repair attempts.
*Detection:* Phase 3, W3.6.
*Alternative:* stop. Report the methodological finding that the pipeline as designed cannot distinguish signal from search artifact at this noise level. No real-data claim may be made.

**K7 — Every symbolic candidate dies on held-out chemistry.**
*Trigger:* zero candidates reach L5.
*Detection:* Phase 4, W4.5.
*Alternative:* this is not a failure, it is the answer. Report at the highest achieved rung and complete Phase 5.

**K8 — Instrument artifact indistinguishable from energy effect.**
*Trigger:* NC6 (mixture identity) or NC7 (retention time) predicts trajectory shape at a level comparable to the descriptor effect, and leave-one-mix-out validation does not resolve it.
*Detection:* Phase 2, W2.7.
*Alternative:* restrict to compounds from low-complexity mixes (499–502, roughly 95 substances each), accepting the reduced n, and report the restriction.

---

# 23. Research claims ladder

| Level | Claim | Evidence required | Honest phrasing |
|---|---|---|---|
| **L0** | The pipeline runs and is reproducible | F1; clean-checkout rerun | "We built and validated a pipeline." No scientific claim. |
| **L1** | Fragmentation functionals change with collision energy in this dataset | B1 beats B0 out of sample; F2 and F3 passed | "Fragmentation extent increases with NCE, reproducing published qualitative behaviour." Not novel. |
| **L2** | The energy response generalizes to unseen molecules | F4 passed; effect above threshold | "The population energy response predicts trajectories of compounds not used in fitting." |
| **L3** | Molecular structure explains part of the between-compound variation | F5 passed; variance share ≥ 0.20; F8 shows the effect is not mass alone | "Structural descriptors explain X% (CI) of between-compound variation in trajectory shape on scaffold-disjoint holdouts." |
| **L4** | An interpretable expression captures that relationship | Null-calibrated symbolic candidate at complexity ≤ 20, ≥ 20/30 seeds, ≥ 80% of ceiling | "We identified a compact expression; it has not yet survived falsification." |
| **L5** | The expression survives falsification on validation chemistry | F6, F7, F9, F10 passed | "The expression survived scaffold-disjoint, cluster-disjoint, influence, energy-subset and permutation tests." |
| **L6** | Candidate scientific conjecture | L5 plus a single confirmation-set evaluation meeting pre-set thresholds | "We propose the following candidate conjecture, with domain of applicability limited to [singly charged ESI precursors, 150–530 Da, HCD on one Q Exactive, NCE 15–90, ENTACT chemical space], pending independent replication." |

**Enforcement.** The report's abstract states the level. §21 item 19 makes an overshoot a completion failure, not a stylistic quibble.

**What each level is worth.** L1 alone would duplicate Li et al. (2021) and is not publishable. L3 with a clean scaffold-disjoint estimate and honest intervals is a solid methods contribution. L5 with a compact expression and a documented domain would be a genuine result. L6 requires replication MURU v1 will not have, which is why the ceiling is "candidate conjecture" and not "discovery".

---

# 24. Risk register

Ranked by expected damage. Probability and severity on 1–5. Detectability: 1 = obvious, 5 = invisible without a specific test.

| # | Risk | Category | P | S | D | Mitigation | Can invalidate v1? |
|---|---|---|---|---|---|---|---|
| R1 | Formula-filtered spectra make peak-derived endpoints artifacts of RMassBank's annotation, not of physics | MS / preprocessing | 4 | 5 | 4 | Independent mzML branch (W1.6); F3 gate; endpoints weighted toward intensity-dominated functionals | **Yes** |
| R2 | Survival-yield censoring (45% left-censored) makes the low-energy regime unidentifiable | Statistical | 5 | 4 | 2 | Censored likelihood; shift primary weight to mu; declare the restriction in every claim | No, but caps claims |
| R3 | Symbolic regression returns a plausible expression that is a search artifact | Symbolic | 4 | 5 | 5 | Null calibration per complexity; 30 seeds; equivalence clustering; synthetic G4 test | **Yes** |
| R4 | The "structure effect" is precursor mass wearing a chemistry costume | Interpretation | 4 | 4 | 3 | F8 descriptor ablation; K5 kill criterion; explicit mass-only baseline B2 | No, forces reframing |
| R5 | No replicate estimate obtainable, so "residual within noise" is unfalsifiable | Statistical | 3 | 4 | 2 | W1.5 raw-data extraction; fallback to comparative claims with the weakening stated | No, weakens H-MAIN |
| R6 | Chemical leakage through congeneric ToxCast series inflates apparent generalization | Validation | 4 | 4 | 4 | S2 and S3 splits; report the S0-to-S3 gap explicitly | No, if splits enforced |
| R7 | Mixture complexity confounds trajectory shape via co-isolation | MS / dataset | 3 | 4 | 4 | NC6; mixture covariate; leave-one-mix-out; K8 | No, forces restriction |
| R8 | Preprocessing choice manufactures the relationship (the α = −0.5 finding in §1) | Statistical / MS | 4 | 5 | 4 | §7.3 grid on every conclusion; F2 gate; test collapse on mass-free endpoints too | **Yes** |
| R9 | Entropy results cited as physics when they are threshold effects | Interpretation | 4 | 3 | 3 | Entropy demoted to secondary; abundance and mass correlations reported alongside every entropy number | No |
| R10 | Sample size insufficient for the effect size present | Statistical | 3 | 4 | 3 | Power statement in §9.5 published in advance; minimum effect sizes pre-registered | No, caps claims |
| R11 | Researcher degrees of freedom across endpoints, splits and preprocessing cells | Statistical | 4 | 4 | 5 | Pre-registration with hash; declared test family; BH-FDR; sealed confirmation set | **Yes** |
| R12 | HCD multi-collision physics violates the single-collision CoM formula, invalidating E_com | MS theory | 3 | 3 | 4 | E_com used descriptively only; collapse hypotheses tested empirically, not assumed | No |
| R13 | MassIVE dataset unusable or file naming does not map to mix/mode/NCE | Dataset | 2 | 4 | 1 | Early Phase 1 probe; fall back to curated-layer-only with R1 unmitigated and stated | No, but raises R1 |
| R14 | MassBank release drift changes the corpus mid-project | Dataset / reproducibility | 3 | 2 | 2 | Pin the release tag; hash manifest; record retrieval date | No |
| R15 | Record instrument string ("Q Exactive Orbitrap") disagrees with the paper ("HF") | Dataset | 3 | 1 | 2 | Document; irrelevant within-dataset; blocks only cross-instrument extension | No |
| R16 | PySR/Julia toolchain instability in the build environment | Computational | 2 | 2 | 1 | Pin versions; gplearn arm as fallback; containerize | No |
| R17 | Bayesian sampler fails to converge on the censored survival model | Computational | 3 | 2 | 1 | Non-centred parameterization; fall back to mu-only mixed model | No |
| R18 | The result is real, correct, and already published | Scientific novelty | 3 | 3 | 3 | Literature check at Phase 4; §23 forces honest framing; L3 with clean methodology retains value | No |

**The three that can end the project:** R1, R3, R8, and R11. Each has a dedicated gate (F3, §13.6, F2, and the pre-registration respectively). None of them can be handled after the fact.


---

# 25. Recommended technical stack

Every dependency has a named job. Anything without one is not in the list.

## Core

| Package | Version | Job |
|---|---|---|
| Python | 3.12 | RDKit and PySR both support it; 3.13 is premature for the scientific stack |
| NumPy | ≥ 2.0 | arrays |
| SciPy | ≥ 1.14 | optimization for curve fits, `stats` for Spearman and bootstrap primitives |
| pandas | ≥ 2.2 | the corpus is ~6k rows; Polars would buy nothing and cost ecosystem compatibility with statsmodels and scikit-learn |
| PyArrow | ≥ 17 | Parquet with schema enforcement for `trajectories.parquet` |
| pydantic | ≥ 2.8 | schema validation of parsed records; catches parser regressions at ingest |

## Chemistry and mass spectrometry

| Package | Job |
|---|---|
| RDKit (≥ 2024.03) | SMILES sanitization, InChIKey generation, Tier A descriptors, Morgan fingerprints, Bemis-Murcko scaffolds, Butina clustering. Non-negotiable. |
| pyteomics or pymzml | mzML reading for the Phase 1 raw branch. `pymzml` is lighter; `pyteomics` has better centroid handling. Choose in Phase 1 after testing on actual MSV000091754 files. |
| matchms | **Optional.** Adduct parsing and spectrum cleaning helpers. The MassBank record format is simple enough to parse directly, and MURU must keep raw metadata anyway, which matchms discards. Recommend a custom parser and matchms only if its adduct utilities save real work. |
| pyOpenMS | **Not recommended.** Heavy dependency; nothing here needs its feature-detection machinery. |

## Statistics and modelling

| Package | Job |
|---|---|
| statsmodels | GAMs, splines, MixedLM for the uncensored mu model, ANOVA variance components |
| scikit-learn | gradient boosting, GP regression, grouped CV splitters, permutation importance |
| PyMC (≥ 5.16) + ArviZ | hierarchical censored models, posterior intervals, convergence diagnostics. Justified by §9.2. |
| numpyro | fallback backend if PyMC sampling is too slow; keep behind a flag, do not maintain two model definitions |
| lightgbm | optional; `HistGradientBoostingRegressor` is adequate at this n |

## Symbolic regression

| Package | Job |
|---|---|
| PySR (+ Julia) | primary engine, per §13.3 |
| gplearn | independent comparison arm |
| SymPy | canonicalization and equivalence detection |
| PySINDy | **Not recommended.** No dynamical system, no time derivative, and its candidate-library restriction is wrong for this problem. |
| PyTorch | **Not recommended.** ~590 groups. If a later argument for a GNN appears, it must include a power calculation. |

## Infrastructure

| Package | Job |
|---|---|
| uv | environment and lockfile. Faster and more reproducible than pip-tools here. |
| PyYAML + pydantic | experiment configuration with validation. Hydra is overkill for a fixed experiment set. |
| pytest + hypothesis | unit tests; property tests for the parser and the entropy implementation |
| matplotlib | figures. Seaborn optional. Plotly not needed; there is no dashboard. |
| joblib | caching of expensive fits and parallel CV |
| rich | readable console progress for long runs |

**Explicitly excluded:** MLflow and Weights & Biases (a JSON run log plus git is sufficient at this scale), DVC (the dataset is ~20 MB), Docker (useful for the final release, not for development), any web framework, any LLM library in the numerical path.

---

# 26. Proposed repository architecture

```
muru/
├── README.md
├── PREREGISTRATION.md              # hashed before Phase 2 modelling
├── DEVIATIONS.md
├── pyproject.toml
├── uv.lock
│
├── configs/
│   ├── dataset.yaml                # release tag, hashes, retrieval date
│   ├── preprocessing.yaml          # the §7.3 grid
│   ├── descriptors.yaml            # Tier A frozen list
│   ├── splits.yaml                 # S0–S4 definitions
│   ├── models.yaml                 # baselines B0–B7
│   └── symbolic.yaml               # PySR operators, complexity, seeds
│
├── src/muru/
│   ├── io/
│   │   ├── massbank.py             # record parser, raw strings preserved
│   │   ├── mzml.py                 # Phase 1 raw branch
│   │   └── manifest.py             # hashing, provenance, release pinning
│   ├── schema.py                   # pydantic models for record / trajectory
│   ├── spectra.py                  # peak-list operations, preprocessing grid
│   ├── energy.py                   # CE parsing, E_lab, E_com, provenance
│   ├── features.py                 # mu, SY, phi, entropy and the rest
│   ├── molecules.py                # RDKit descriptors, scaffolds, clustering
│   ├── splits.py                   # S0–S4 with disjointness assertions
│   ├── models/
│   │   ├── baselines.py            # B0–B5
│   │   ├── hierarchical.py         # PyMC models, censored likelihood
│   │   └── ceiling.py              # B6–B7
│   ├── symbolic/
│   │   ├── search.py               # T1/T2/T3 drivers
│   │   ├── equivalence.py          # SymPy + numerical fingerprint
│   │   └── nulls.py                # null calibration
│   ├── validation/
│   │   ├── ladder.py               # F1–F12
│   │   ├── controls.py             # NC1–NC7
│   │   └── uncertainty.py          # cluster bootstrap, coverage
│   ├── synthetic/
│   │   ├── generators.py           # G1–G5
│   │   └── truth.py                # ground-truth equations, import-isolated
│   └── report/
│       ├── claims.py               # claim-to-artifact mapping and the audit
│       └── figures.py
│
├── experiments/
│   ├── phase1_audit/
│   ├── phase2_baselines/
│   ├── phase3_synthetic/
│   ├── phase4_discovery/
│   └── phase5_report/
│
├── artifacts/                      # gitignored; regenerable, hashed
├── docs/                           # the phase decision documents
└── tests/
    ├── test_parser.py
    ├── test_energy.py
    ├── test_features.py            # includes Li et al. Fig. 1 entropy checks
    ├── test_splits.py              # includes the leakage canary
    └── test_ladder.py              # includes the planted-artifact rejection
```

Notes on what is deliberately absent. No `utils/` (a landfill by construction). No separate package per noun: `spectra.py` and `features.py` are modules, not subpackages, because they hold a few hundred lines each. No plugin architecture. No abstract base classes until a second implementation exists. `synthetic/truth.py` is import-isolated so the discovery code path cannot read the ground truth, and a test asserts the import graph.

---

# 27. Assumptions requiring verification

Ordered by consequence.

| # | Assumption | Current status | Verified in | If false |
|---|---|---|---|---|
| A1 | `COLLISION_ENERGY 15` means NCE 15 for all LCSB ENTACT records | WORKING ASSUMPTION from the publication | W1.3 | The energy axis is meaningless; K2 fires |
| A2 | RMassBank record peak lists contain only formula-assignable peaks | VERIFIED on 373 records; assumed corpus-wide | W1.6 | Changes the R1 mitigation, not the design |
| A3 | The accession slot convention (01–06 pos, 51–56 neg, energies 15–90) holds corpus-wide | VERIFIED on 373 records | W1.2 | Grouping needs a fallback on record title parsing |
| A4 | Only [M+H]+ and [M-H]- adducts appear | VERIFIED in sample (230/143) | W1.2 | Adduct becomes a grouping key and a covariate |
| A5 | All precursors are singly charged | STRONGLY SUPPORTED (small molecules, ESI, these adducts) | W1.3 | The NCE charge factor f(z) must be applied per record |
| A6 | The precursor peak is retained in records whenever detected | VERIFIED for the compounds inspected | W1.4 | Survival yield becomes uncomputable; mu loses its decomposition |
| A7 | Mixes 499, 503 and 505 share ~95 compounds with three independent injections | STRONGLY SUPPORTED from the paper's mix design | W1.5 | No repeatability estimate; R5 fires |
| A8 | MSV000091754 mzML files map cleanly to mix, mode and NCE by filename | UNKNOWN | W1.5 | The raw branch and repeatability both fail; R13 fires |
| A9 | `CH$SMILES` is chemically correct after the MS-ready and stereochemistry repair | WORKING ASSUMPTION; the paper documents past failures | W1.2 | Descriptors are wrong for an unknown subset; spot-check and exclude |
| A10 | RESOLUTION 17500 is constant across all records | VERIFIED in sample | W1.1 | Resolution becomes a covariate affecting peak counts |
| A11 | Center-of-mass energy against N2 is the right first-order physics for HCD | STRONGLY SUPPORTED for single collisions; approximate for HCD | W1.3 (descriptive only) | E_com is used descriptively, so nothing breaks |
| A12 | The corpus contains ≥ 400 positive-mode groups with ≥ 5 energies | STRONGLY SUPPORTED (85% completeness × 590 compounds ≈ 500) | W1.4 | K1 fires |
| A13 | mu's superiority over entropy holds at full n | HYPOTHESIS from a 56-compound sample | W1.7 | Endpoint choice is revisited on Phase 1 evidence, which is why Phase 1 chooses it |
| A14 | Mixture identity does not confound trajectory shape | UNKNOWN | W2.7 (NC6) | K8 fires; restrict to low-complexity mixes |

A13 deserves emphasis. My endpoint recommendation rests on 56 trajectories. Phase 1 must re-run that comparison at full n and is authorized to overturn it. The design commits to a selection *procedure*, not to mu specifically.

---

# 28. Decisions that must NOT be made yet

Making these now would either lock in a choice the data should make, or expand scope before the science is established.

1. **The final primary endpoint.** Phase 1 chooses it from measured evidence. mu is the recommendation, not the commitment.
2. **The functional form of Phi.** Logistic, Weibull, Gompertz, monotone spline: let the data and Phase 3 recovery tests decide. Assuming a sigmoid now would bias the collapse search toward finding one.
3. **The exact Tier A descriptor list.** Draft in §8.2; frozen at the start of Phase 2 after Phase 1 reveals the mass and size distribution and the descriptor correlation structure.
4. **Whether to use the raw mzML branch corpus-wide or on a subset only.** Depends on what W1.5 finds about file structure and cost.
5. **Whether negative mode gets a full independent analysis or a census-plus-replication treatment.** Depends on the negative-mode group count after Phase 1.
6. **The symbolic complexity ceiling.** Provisionally 20; set from the Phase 3 null calibration, where the complexity at which nulls start scoring well is the real ceiling.
7. **Whether PyMC or numpyro is the sampler.** Decide on Phase 2 timing measurements.
8. **Whether matchms enters the dependency list.** Decide after writing the parser and seeing whether its adduct utilities save work.
9. **Any second dataset.** Not before Phase 5 exists. Eawag and BAFG multi-energy Orbitrap collections are the natural v2 candidates and each needs its own audit.
10. **Any LLM component.** Only after L4 or above, and only to phrase a verified expression in prose. Never in the numerical path.
11. **Publication venue or framing.** After the report states the achieved level.
12. **Whether v1's negative result should be published.** After it exists. It probably should be.

---

# 29. Phase 1 exact specification

## 29.1 Preconditions
Empty repository. Network access to `raw.githubusercontent.com` and MassIVE. No modelling code exists.

## 29.2 Task list, in execution order

**T1.1 Environment.** `uv` project, Python 3.12, pin NumPy, SciPy, pandas, PyArrow, pydantic, RDKit, matplotlib, pytest. No modelling packages yet.

**T1.2 Release pinning.** Identify the current MassBank release tag. Record tag, date, and the exact URL pattern used. Write `configs/dataset.yaml`.

**T1.3 Corpus fetch.** Retrieve all LCSB records matching the ENTACT accession pattern. Store raw files. Emit `MANIFEST.json` with per-file SHA-256, byte size and retrieval timestamp.

**T1.4 Parser.** MassBank record format 2.6.0 parser producing, per record, both the parsed value and the raw string for every field, plus `parse_status` and any warning. Validate against the pydantic schema. Round-trip test on 50 hand-checked records.

**T1.5 Census.** Counts by mode, energy, adduct, instrument string, resolution, confidence, mixture. Reconcile against the published 3411 positive / 2171 negative / 5582 total. Report and explain any difference above 5%.

**T1.6 Identity and grouping.** InChIKey-based groups. RDKit round-trip of `CH$SMILES` compared against the recorded InChIKey. Log mismatches. Verify the slot convention. Report per-group energy coverage.

**T1.7 Energy audit.** Confirm the value set. Compute E_lab and E_com per record. Confirm charge state. Write `CE_AUDIT.md` including the provenance chain from the publication to the `energy_type` field.

**T1.8 Endpoint computation.** mu, SY, phi, entropy, normalized entropy, peak count, base-peak fraction, TIC, and adjacent-energy entropy similarity, under every cell of the §7.3 preprocessing grid.

**T1.9 Endpoint screening.** Per endpoint: monotone fraction, within-compound range, between-compound SD, correlation with log TIC, precursor m/z, RT and mixture, at each energy. This reproduces at full n the table I built from 373 records.

**T1.10 Censoring census.** Survival-yield midpoint bracketing distribution. Fraction left-censored. Informative-point counts. Detection-floor estimate from the prescreening threshold.

**T1.11 Raw branch.** Probe MSV000091754 structure. If the filename convention maps to mix, mode and energy, download mzML for mixes 499, 503, 505 only. Extract MS2 for compounds present in all three. Compute all endpoints without the formula filter.

**T1.12 Repeatability.** One-way random-effects variance decomposition on the triplicate subset, per endpoint, per energy. Deliver `REPEATABILITY.md` with the noise SD that Phase 3's synthetic generator will use.

**T1.13 Branch comparison.** Endpoint values from the curated branch against the raw branch on the shared subset. Bland-Altman style agreement plots. Test whether formula-annotation success depends on energy.

**T1.14 Decision.** Write `PHASE1_DECISION.md` against the §22 kill criteria K1, K2, K3.

## 29.3 Acceptance criteria
As listed in the Phase 1 block of §20. All six checkboxes plus `PHASE1_DECISION.md`.

## 29.4 Explicitly out of scope for Phase 1
Splits. Descriptors beyond what identity checking requires. Any model. Any symbolic search. Negative mode analysis beyond census. Neutral losses. ClassyFire classes.

## 29.5 Bug policy in force
BLOCKER: parser corrupting values, wrong energy assignment, wrong compound grouping, hash mismatches, missing provenance. Fix before proceeding.
IMPORTANT: parse failures on a small record subset, mzML edge cases, slow downloads. Fix if reasonable, otherwise document with a reproduction and defer.
MINOR: formatting, plot aesthetics, log verbosity. Backlog.
Two-attempt rule applies to everything except BLOCKERs.

## 29.6 Expected duration
Two to four working sessions, dominated by T1.11 and T1.12. If T1.11 exceeds one session because the MassIVE layout resists automation, downgrade to a smaller subset rather than expanding the phase.

---

# 30. Final recommendation

## **CONDITIONAL GO**

The MURU v1 concept is scientifically viable on this dataset, with three conditions.

**Condition 1: the primary endpoint changes.** Spectral entropy is demoted from primary endpoint to secondary robustness check. The evidence is in §7.2: monotone in 32% of trajectories, correlated with total ion current at +0.27 to +0.33 and with precursor mass at +0.24 to +0.36, bounded by a peak count that RMassBank's annotator determines. The recommended replacement is the intensity-weighted normalized spectrum mass mu, monotone in 86% of trajectories, with an exact decomposition into precursor survival and fragment depth. Phase 1 confirms or overturns this at full n.

**Condition 2: the question changes from existence to generalization.** "Fragmentation changes with collision energy" is published (Li et al. 2021, Extended Data Fig. 2). The open question is whether a molecule-conditional rescaling collapses the trajectory family, and whether it holds on scaffold-disjoint chemistry. §3.2 states it so that it can fail.

**Condition 3: Phase 1 clears K1, K2 and K3 before Phase 2 is authorized.** Corpus size, energy semantics, and signal-above-noise. The third is the one I cannot resolve from here, because the curated MassBank layer contains no technical replicates and the repeatability estimate has to come out of the raw mzML.

**Why not GO.** Three quantities that decide the project remain unmeasured: instrument repeatability, the size of the RMassBank formula-filter effect, and whether the endpoint ranking I derived from 56 trajectories survives at 590.

**Why not PIVOT.** Collision energy stays as the independent variable, and it survives the audit better than expected. §6.2 shows that Thermo's NCE normalization plus the center-of-mass transform leave E_com varying under 13% across the full mass range at fixed NCE, so NCE is a defensible cross-molecule energy axis for singly charged ions on one instrument. The dataset is unusually clean: one instrument, one resolution, two adducts, one confidence class, a deterministic accession scheme, and 85% six-energy coverage. Throwing that away would be an error. If you read "collision energy formulation" as including the endpoint, then Conditions 1 and 2 constitute a pivot inside a conditional go, and I would rather say that plainly than hide the change behind the label.

**Why not STOP.** The signal is there. Median mu falls from 0.867 to 0.385 across the grid with 86% monotonicity, against a between-compound SD of 0.232. That is a real, reproducible, physically interpretable energy response with room for structure to explain part of the spread.

**What I expect will actually happen.** Ranked by my honest estimate:

- L1 (energy dependence reproduced): near-certain.
- L2 (generalizes to unseen molecules): likely, because the population energy response is strong.
- L3 (structure explains between-compound variation beyond mass): perhaps even odds. Precursor mass will do a lot of work and F8 will have to separate it from chemistry.
- L4 (interpretable expression at the null-calibrated threshold): under even odds.
- L5 (survives full falsification): less likely than not.
- L6 (candidate conjecture): unlikely in v1.

A project that reaches L3 with clean scaffold-disjoint estimates, an honest censoring account, and a documented failure of the naive degrees-of-freedom collapse would be a good piece of work. Plan for that outcome and treat anything above it as upside.

---
---

# Appendix A — Answers to the 28 required questions

**1. Is the central MURU v1 question scientifically coherent?**
As written, no. It is trivially true in its weak reading and undefined in its strong one. §3.2 repairs it into H-MAIN, H-PARAM and H-NULL-BEAT, which are coherent and falsifiable.

**2. Is collision energy likely to contain a generalizable mathematical signal across compounds?**
Yes at the population level, with moderate confidence. VERIFIED: median mu falls 0.867 → 0.385 across NCE 15→90 with 86% monotonicity; median entropy rises 0.63 → 1.97, matching Li et al.'s NIST20 result. Whether that population signal supports a *compound-conditional* law generalizing to unseen scaffolds is the open question and my preliminary collapse test says the easy answers fail.

**3. What is the most defensible dependent variable or mathematical object?**
The energy-resolved trajectory of the pair (SY_i(E), phi_i(E)), summarized by mu_i(E) = SY + (1−SY)·phi. Not entropy. Not a single scalar per compound. §7.1.

**4. Is spectral entropy sufficient, useful but incomplete, or inappropriate?**
Useful but incomplete, and inappropriate as the primary endpoint. It remains an excellent similarity primitive (its intended purpose in Li et al.) and a legitimate secondary robustness check. §7.2 gives the five reasons.

**5. How much molecular structure information is likely necessary?**
Some, but less than instinct suggests, and the amount is the empirical question. Between-compound SD is 0.232 against a within-compound range of 0.440, so roughly a third of variance is between molecules. A Tier A set of about a dozen physics-facing descriptors is the right scale. Fingerprints belong in the ceiling estimate only.

**6. Does NCE create comparability problems across precursor masses or molecules?**
Less than feared, for this dataset. CE_lab = NCE × (m/z)/500 × f(z) with f(1) = 1, and E_com = E_lab × 28/(28+M) makes the mass dependence nearly cancel: at fixed NCE, E_com varies under 13% across 151–526 m/z. NCE is defensible here. Two caveats: this holds only for singly charged ions, and Révész et al. document that different Orbitrap models differ at matched NCE, so nothing transfers off this instrument.

**7. Is six collision energy levels enough for meaningful symbolic regression?**
Not for per-compound curve fitting, and marginally for population-level work. For survival yield the effective count is worse: median two informative points per compound with 45% left-censored. Six levels support a two- or three-parameter shared shape with compound-level scaling. They do not support free-form per-compound functional discovery. This is the sharpest structural limit on the project.

**8. How many compounds are likely required for credible generalization?**
For a scaffold-disjoint claim about a moderate effect, a few hundred training compounds and at least 100 in the confirmation set. Roughly 590 positive-mode compounds sits at the low end of adequate. §9.5: rho = 0.5 is detectable with power > 0.99, rho = 0.2 with power near 0.55.

**9. What sample size do we actually appear to have?**
VERIFIED from the publication: 590 positive-mode compounds giving 3411 records, 379 negative-mode giving 2171, 783 unique compounds, 186 measured in both polarities. From my sample, 85% of compound-by-mode groups carry all six energies, so expect roughly 500 complete positive-mode trajectories.

**10. What statistical power limitations are likely?**
Moderate effects detectable, weak ones not. Compound-level bootstrap intervals will be wide enough that small differences between models are uninterpretable. The 5-point R² improvement my exploratory collapse sweep produced is inside the noise band at n = 56 and needs the full corpus plus a sealed confirmation set to mean anything.

**11. Should we model individual spectra, trajectories, summary curve parameters, or something else?**
Trajectories, in a hierarchical model that estimates compound-level parameters jointly with the population, rather than fitting curves per compound and regressing the estimates afterwards. Two-stage fitting would discard the parameter uncertainty that 15% incomplete coverage and 45% censoring make large.

**12. Should MURU first solve prediction and only then attempt symbolic regression?**
Yes, and it is gated: §13.1 blocks symbolic search until the predictive ceiling is known. Without the ceiling there is no way to judge whether a compact expression captured the phenomenon or a fraction of it.

**13. What would constitute evidence that symbolic regression is adding scientific value?**
Four things together: the expression exceeds the null-calibrated 95th percentile at its own complexity; the same structure is recovered by at least 20 of 30 independent seeds; it reaches at least 80% of the Tier B ceiling at complexity ≤ 20; and it survives F6 through F10. Any one alone proves nothing.

**14. How do we prevent equations from being artifacts of a small discrete energy grid?**
F9 refits on energy subsets ({15,30,45}, {45,60,75,90}, odd indices) and requires the form to persist. Dimensionless energy scaling keeps constants O(1) so grid spacing cannot hide in them. Nested-operator restrictions block expressions that only interpolate six points. The synthetic G-cases are simulated on the same six-point grid so recovery rates account for it.

**15. What is the strongest possible held-out validation design?**
Scaffold-disjoint splitting (S2) as the primary gate, Butina cluster-disjoint (S3) as the stress test, a 20% confirmation set sealed before analysis and opened once, plus the mode-transfer test (S4) on the 186 dual-mode compounds. The S0-to-S3 performance gap is reported so readers can see the size of the leakage that naive splitting would have introduced.

**16. Do we need scaffold based generalization?**
Yes. ENTACT draws from ToxCast, which is full of congeneric series. Compound-level splitting alone would place near-identical analogues on both sides of the wall and inflate the result.

**17. Should positive and negative ionization modes be separate experiments?**
Yes. Different precursor ions, different charge localization, different fragmentation chemistry, and Li et al. measured systematically higher entropy and steeper energy response in positive mode. Run positive as primary and negative as independent replication with its own pre-registration.

**18. Should adducts be separate?**
The question is moot for this dataset: only [M+H]+ and [M-H]- appear, and they are collinear with ion mode. Keep adduct in the grouping key so that a future corpus with [M+Na]+ or [M+NH4]+ does not silently pool them.

**19. Should different precursor charge states be separate?**
Yes in principle, since the NCE charge factor f(z) differs. Moot here: all precursors are singly charged. Phase 1 verifies this rather than assuming it.

**20. What preprocessing transformations could accidentally manufacture a collision energy relationship?**
I found a live example. Normalizing the weighted mean mass by precursor m/z makes mu mass-dependent by construction, and a power-law energy rescaling sweep then finds an optimum at exponent −0.5 that improves apparent collapse without any physics behind it. Others: intensity thresholds that admit more peaks in brighter spectra, inflating entropy at high energy; the RMassBank formula filter, whose annotation success may itself depend on energy; square-root intensity weighting, which changes which peaks dominate mu; and precursor inclusion or exclusion, which swings mu's low-energy end.

**21. What negative controls are mandatory?**
All seven in §17. NC1 (energy shuffle), NC2 and NC3 (descriptor and trajectory shuffle), NC4 (sham descriptor), NC5 (synthetic null), NC6 (mixture identity), NC7 (retention time). NC6 and NC7 are the two most likely to fire, because mixture complexity drives co-isolation.

**22. What simple baselines must MURU beat?**
B1 (per-energy population mean) is the floor for any claim of energy dependence. B2 (per-energy mean plus a linear precursor mass term) is the floor for any claim about chemistry, since beating B1 but not B2 means the result is a mass law. B4 and B5 are the floors for claiming nonlinearity matters. All measured under S2 with compound-level bootstrap intervals.

**23. What would cause us to kill the current hypothesis?**
The eight criteria in §22, in short: fewer than 250 usable groups; unresolvable energy semantics; signal within replicate noise; B7 failing to beat B1 under scaffold splits; structure explaining nothing beyond mass; the discovery system failing its own null test; every candidate dying on held-out chemistry; or mixture and retention-time artifacts indistinguishable from the energy effect.

**24. What result would actually be scientifically interesting?**
A compact rescaling g(z) that collapses trajectories across scaffold-disjoint chemistry, with an exponent that either matches or contradicts RRKM degrees-of-freedom expectations. My preliminary sweep pointing to −0.5, the opposite sign from the textbook prediction, would be interesting if it survived validation and if the mu-normalization artifact were ruled out. A rigorous negative, showing that no simple rescaling collapses breakdown behaviour across diverse environmental chemicals on one instrument, would also be worth reporting, because practitioners currently assume NCE transfers across compounds.

**25. What result would merely be technically impressive but scientifically weak?**
A gradient-boosted model predicting mu with R² = 0.85 under random spectrum splits. Leakage does that. Also: a symbolic expression fitted on all data with excellent training error and no null calibration; a rediscovery of the entropy-versus-energy trend presented as a discovery; and any "law" that F8 shows is carried entirely by precursor mass but that gets described in the language of chemistry.

**26. What would make this project suitable for a serious research presentation or paper?**
Four things. A pre-registration with a published hash. A scaffold-disjoint confirmation set opened once. A null-calibrated symbolic search with per-complexity thresholds. Complete reporting of rejected candidates and failed gates. Those four turn even a negative result into a methods contribution, because almost nobody in this area does all four.

**27. What parts of the current vision are too ambitious for v1?**
Universal cross-instrument laws. Mechanistic explanation from curve fitting. Any LLM in the discovery path. Multiple datasets. Neutral-loss and fragment-level modelling. Full functional data analysis on six points. Latent spectral embeddings. Reaching L6 within v1.

**28. What parts are not ambitious enough?**
Three. First, the endpoint: `DATASET_SOURCE.md` and the reference pack lean toward entropy as the natural target, and the data say a richer, better-conditioned object exists. Second, the physics: the plan as briefed treats NCE as a bare number, when the Thermo conversion plus the center-of-mass transform give a principled, dimensionally motivated energy variable and a sharp collapse hypothesis to test. Third, the ambition of the negative result: the brief treats a negative outcome as an acceptable fallback, and a well-executed negative here, showing that breakdown behaviour does not collapse under any simple structural rescaling across several hundred diverse environmental compounds, would be a more useful contribution than a marginal positive.

---

*End of master plan.*
