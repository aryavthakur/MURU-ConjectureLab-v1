# MURU collision-energy interface adjudication: preregistration OUTLINE, DRAFT

> **Superseded for Design A (2026-09-16).** The binding Design A protocol is `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_PREREGISTRATION.md`, which is frozen. That protocol replaces this outline's calibration-and-evaluation split with a single paired within-compound adjudication, because no parameter is fitted. This outline is retained unchanged as history.

> **DRAFT OUTLINE ONLY. NOT FROZEN. EXECUTION NOT AUTHORIZED.**
> This is a skeleton for discussion, not a preregistration. No section is binding. Section 12 lists the decisions that must be made by the user before any part of this can be frozen, and several of them change the shape of the design rather than only its parameters.

Recommended design this outline covers: **Design A**, an interface adjudication on an external public population, scaffold-split, with calibration restricted to a choice among predeclared discrete conventions. Design B (prospective dense-NCE acquisition) is sketched only at section 11, because its acquisition parameters are partly ungrounded and it is recommended as the subsequent study.

Companion documents: `MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md` (provenance and counts), `MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md` (candidate conventions, feasibility, recommendation).

Evidence convention: every count quoted here is VERIFIED in the companion documents' artifacts and is carried over unchanged; nothing in this outline is a new measurement. Every rule, threshold, split ratio and criterion is a DRAFT PROPOSAL, not a verified fact, and section 12 lists the ones that are still open.

---

## 1. Objectives and estimands

### 1.1 Objective

Fix, before any independent comparator evaluation is run, the single discrete mapping from an Orbitrap HCD acquisition setting `(NCE, precursor_mz)` to the float supplied to each public comparator checkpoint's `collision_energy` input.

### 1.2 What this study is NOT

It is not a comparison of model accuracy. No statement about relative model performance is licensed by any endpoint here. That separation is structural: the population available for this study (section 2) lacks MURU's own frozen energy rungs and comes from different laboratories and Orbitrap platforms than MURU's deployment.

### 1.3 Estimands

| Id | Estimand | Population | Quantity |
| --- | --- | --- | --- |
| E1 (primary) | For each comparator checkpoint independently, which of the predeclared conventions `{K1, K2, K3}` yields the best agreement between predicted and measured spectra | Held-out evaluation scaffolds, all admissible energy cells, [M+H]+ only | The selected convention, plus the margin between it and the runner-up |
| E2 | Whether the selection is stable across the precursor-mass strata | Same, stratified low / null / high | Selected convention per stratum |
| E3 | Whether the selection agrees across checkpoints | Same | Agreement or disagreement, reported as such |
| E4 | Whether a convention can be distinguished at all in the null stratum (negative control) | Null stratum only (precursor m/z 450 to 550, where K1 and K2 coincide by construction) | Expected result: no discrimination. A discrimination here falsifies the design's own identifying assumption |

Note on E3: disagreement across checkpoints is a legitimate and informative outcome, not a failure. The provenance review shows the three checkpoints share one training axis but not one preprocessing chain (`inten_contr` drops 12,191 CE-mismatched rows; GLACIER's presented value is unresolved between floor and raw), so a per-checkpoint mapping is a possible correct answer. The preregistration must commit in advance to reporting a per-checkpoint mapping rather than forcing a single one.

---

## 2. Population and exclusion rules

### 2.1 Source population

| Stratum | Source | Compounds | Scaffold groups |
| --- | --- | --- | --- |
| Main | C01: MassBank Eawag EQ records first released after MassBank 2023.11, conservative tier, tagged releases only | 33 | 33 |
| Main, extended variant | Same including unreleased dev PR #398 | 44 | 44 |
| High mass | C02: CyanoMetDB EAWAG-EC arm (first-mass-40 scan mode, both NCE 20 and 60 present), restricted to precursor m/z at or below 995.556 | up to 37 | up to 21 |

The choice between the 33-compound tagged-only main stratum and the 44-compound extended variant is an open item (section 12, O1).

### 2.2 Exclusion rules, applied in this order

1. Compound key (MURU `parent_connectivity_key`) in MassSpecGym 1.5, any fold, by either the recorded InChIKey first block or the MURU parent key.
2. Compound key in the ms-pred `msg/labels.tsv` simulation universe.
3. Compound key in the MURU exposure registry (31,507 keys).
4. Compound key in the PR #7 confirmation population (1,794) or the comparator common population (1,327).
5. Scaffold group (`scaffold_group_v2`) in the MURU development population, PR #7 or comparator group lists.
6. Canonical-tautomer key matching any structure in the sets above.
7. Formula-constrained heavy-atom skeleton key matching any structure in the sets above: this flags for MANUAL REVIEW, it does not exclude automatically.
8. Parent formal charge must be 0, cross-checked against the record's own recorded InChIKey protonation layer; a disagreement excludes the compound pending manual review.
9. If FIORA-OS is included as a comparator, additionally exclude compounds in the MSnLib nine-library key set (this removes a substantial fraction of C01; see section 12, O5).

Rules 6, 7 and 8 exist because verification found concrete failures of a key-only screen: clethodim entered C01 as a distinct tautomer at Morgan2 Tanimoto 0.5424 to its MassSpecGym counterpart (below any similarity threshold a reviewer would set), and Cetylpyridinium passed a charge-neutrality filter in C10 only because its deposited SMILES misplaces the charge on a ring carbon. Rule 7 must not be automatic: the unconstrained skeleton key wrongly paired aflatoxicol with aflatoxin B2.

### 2.3 Spectrum-level admissibility

| Rule | Status |
| --- | --- |
| [M+H]+, positive mode, MS2, HCD, Orbitrap (`LC-ESI-QFT`) | Established for all C01 records |
| Precursor m/z inside MURU's development range 70.0 to 1042.6 | Established for C01 (100.04 to 784.53 primary tier) |
| Precursor m/z inside the checkpoints' training support (at or below 995.556) | Established for C01; binding for the C02 stratum |
| Single fixed NCE, no ramp, no stepped or assisted scan | Established for C01 (5,051 of 5,051 records are `N % (nominal)`) |
| MURU scan-window rule (first mass at or below 40, upper limit at or above [M+H]+ plus 1) | NOT ESTABLISHED for C01. The C01 screen did not evaluate it; the C02 screen found only its EC arm passes. This is a blocking open item (section 12, O2) |
| Isolation purity (no co-injected ion within 0.7 m/z) | NOT ESTABLISHED for C01 |
| Minimum annotated peak count per spectrum | To be declared. Verification found NCE 15 has median 2 peaks with 21 of 59 primary-tier records at 1 peak or fewer (section 12, O3) |

### 2.4 Energy cells

C01 carries 15 distinct NCE values (15, 20, 25, 30, 40, 45, 50, 60, 70, 75, 80, 90, 120, 150, 180). The nine-value modal ladder {15, 30, 45, 60, 75, 90, 120, 150, 180} covers 4,902 of the 5,051 records; the six off-ladder values are each carried by at most 2 primary-tier compounds (NCE 80 by 1) and so cannot support a cell of their own. Admissible rungs are therefore those modal-ladder rungs C01 actually carries with adequate peak support; restricting to the modal ladder is a design choice and must be declared as one. NCE 60 is present for all primary-tier compounds; the median clean compound has 6 rungs inside 15 to 90. Rungs 120, 150 and 180 lie outside the MassSpecGym CE distribution and outside MURU's development range and may be used, if at all, only as a declared extrapolation probe reported separately.

MURU's frozen external pair (NCE 20 and 60) is NOT reproducible on this population: only 2 of 58 primary-tier compounds carry NCE 20. Any MURU arm must therefore use 30 and 60, or the full 15 to 90 ladder, and this constitutes a declared deviation from MURU's frozen external interface (section 12, O4).

---

## 3. Predeclared discrete conventions

Exactly three, closed unless new upstream provenance appears:

| Id | Formula | Provenance basis |
| --- | --- | --- |
| K1 | `CE_input = NCE` | 30,631 to 49,891 training rows carry unconverted NCE; code provenance |
| K2 | `CE_input = NCE x precursor_mz / 500` | 23,894 training rows provably carry exactly this; numeric identification against 0.41 expected by chance |
| K3 | `CE_input = floor(NCE x precursor_mz / 500)` | The realised ICEBERG training value for every converted row; distinguishes GLACIER hypotheses H_floor and H_raw |

Excluded and not to be reintroduced without a documented provenance change: imputed-energy conventions, source-conditional conventions, instrument-conditional conventions (the deployment is single-instrument), round-half-even integerisation of raw NCE (collapses to K1 at integer rungs), and any continuous fitted scale factor or coefficient optimized on any data.

---

## 4. Calibration and selection rule

| Element | Draft specification |
| --- | --- |
| Split | Scaffold-disjoint on `scaffold_group_v2`. Groups, not compounds, are the randomisation unit. Split seed and group assignment frozen and published before any prediction is generated |
| Split ratio | To be declared. At 33 to 44 groups, a calibration and evaluation split leaves roughly 10 to 20 compounds per side; the ratio must be declared with that in view (section 12, O6) |
| Calibration | For each comparator checkpoint, generate predictions under each of K1, K2, K3 on the calibration fold only; select the convention optimising a single preregistered criterion |
| Criterion | To be declared before the split is drawn. It must be a single scalar per (checkpoint, convention), computed identically for all three conventions, with ties broken by a preregistered rule |
| What may be tuned | Nothing. The only free choice is the discrete convention index. No threshold, weight, scale factor or postprocessing parameter is fitted |
| Stopping | One calibration pass. No iteration, no looking at the evaluation fold, no revisiting the criterion |

---

## 5. Prediction generation order and freeze points

| Step | Action | Freeze |
| --- | --- | --- |
| 1 | Fetch C01 and C02 record files; build the spectrum table | Record-file sha256 manifest frozen and published |
| 2 | Apply exclusions (section 2.2) and spectrum admissibility (section 2.3) | Population key list and scaffold-group list frozen and published, with hashes |
| 3 | Draw the scaffold split | Split assignment frozen and published BEFORE any prediction exists |
| 4 | Declare the calibration criterion and all endpoints | This document's successor frozen, results-blind |
| 5 | Generate calibration-fold predictions for all checkpoints under K1, K2, K3 | Prediction artifact hashes recorded; measured spectra of the calibration fold may now be read |
| 6 | Run the selection rule; record the selected convention per checkpoint | Selection frozen and published BEFORE evaluation-fold predictions are generated |
| 7 | Generate evaluation-fold predictions under the selected convention only | Prediction artifact hashes recorded |
| 8 | Single sealed look at the evaluation fold | One look. No re-analysis |

Measured evaluation-fold spectra must not be read by any person or agent before step 8. Calibration-fold and evaluation-fold artifacts should live in separate directories with separate access records.

---

## 6. Endpoints

| Id | Endpoint | Type |
| --- | --- | --- |
| P1 | The convention selected per checkpoint on the calibration fold, and its margin over the runner-up | Primary |
| P2 | Confirmation on the held-out evaluation fold that the selected convention still ranks first for that checkpoint | Primary |
| S1 | Selected convention per precursor-mass stratum (low, null, high) | Secondary |
| S2 | Agreement or disagreement of the selection across checkpoints, reported as-is | Secondary |
| S3 | Negative control: no discrimination among conventions in the null stratum (450 to 550 m/z) | Secondary, falsifying |
| S4 | Sensitivity of P1 to the minimum-peak filter and to inclusion or exclusion of the NCE 15 rung | Secondary |
| S5 | Sensitivity of P1 to the tagged-only against extended C01 population | Secondary |

S3 is a design-validity check, not a scientific result: if conventions can be discriminated where they are mathematically identical, the pipeline has a defect and the primary endpoints are void.

---

## 7. Comparator handling

| Comparator | Role | Interface handling | Notes |
| --- | --- | --- | --- |
| ICEBERG 2.1 (gen plus inten_contr) | Under adjudication | Convention selected by the rule | Both stages take the same CE float; note that `inten_contr` was trained on a CE-filtered subset of the same rows |
| GLACIER MassSpecGym | Under adjudication | Convention selected by the rule | K2 against K3 is precisely this checkpoint's unresolved H_raw against H_floor question |
| MURU-WUR-v2 | Reference arm, interface NOT under adjudication | MURU's own frozen A0 energy map | MURU's interface is fixed by its own preregistration and is not a candidate here. Its inclusion is to keep compounds and energy cells identical across arms, not to compare accuracy |
| FIORA-OS v0.1.0 | Optional | Would require its own convention treatment | Its training set is MSnLib v1.0, which overlaps C01 substantially (150 of 403 candidate compounds are in the MSnLib nine-library set). Including it forces exclusion rule 9 and shrinks the population further. Recommend EXCLUDING it from this study (section 12, O5) |

All arms must receive identical compounds, identical energy cells and identical measured reference spectra. Any compound admissible for one arm but not another is dropped from all arms, and the drop is recorded.

---

## 8. Blinding and access-record chain

| Element | Draft specification |
| --- | --- |
| Outcome blindness of the closed benchmark | Maintained throughout. The forbidden list in the Phase 0 provenance document remains in force for every agent and person working on this study |
| Evaluation-fold blindness | Measured evaluation spectra unreadable until step 8. Enforced by directory separation and, preferably, by a separate access credential |
| Access record | One JSON record per access to a blinded artifact, written and published BEFORE the artifact is read, following the pattern already used in this repository (a pre-access record committed before any measured quantity is read) |
| Download register | Every fetched file recorded with name, source URL, size and sha256, continuing `artifacts/ce_interface_adjudication/downloads_register.jsonl`. Verification found 10 unregistered transfers in the present study; the register discipline needs a per-fetch automated hook rather than a manual step |
| Independent verification | At least one lens reproducing the selection from raw inputs without reading the primary script, as was done for the Phase 0 counts (39 checks, 38 pass, 0 count disagreements) |

---

## 9. Analysis plan skeleton

1. Descriptive: per stratum and per rung, number of compounds, spectra, annotated peaks; the realised `NCE x mz / 500` values and their separation from raw NCE.
2. Primary: per checkpoint, the calibration criterion under each of K1, K2, K3; selection; margin. Then the evaluation-fold confirmation.
3. Secondary: S1 to S5 as specified.
4. Uncertainty: paired, compound-clustered resampling at the scaffold-group level, since spectra within a compound and compounds within a scaffold group are not independent.
5. No effect size from the closed comparator benchmark enters any calculation. Sample-size justification must come from a non-exposed source (section 10).
6. Reporting: the per-checkpoint selection, the margin, and an explicit statement of what the result does NOT license (model accuracy comparison).

### 9.1 Power and sample size

No effect size from a non-exposed source is currently in hand, so this outline states no powered sample size. Candidate non-exposed sources, in order of preference: a preregistered pilot analysed only for variance components; the C01 public ladder used purely for variance estimation and held strictly apart from evaluation compounds; dispersion figures reported in the ICEBERG, GLACIER and MassSpecGym papers themselves. Failing all three, the design must declare a smallest scientifically relevant difference a priori and size to that. This is a blocking open item (section 12, O7).

At 33 to 44 scaffold groups the design is small by construction, and the honest framing is that it is powered to detect a large and consistent convention effect, not a subtle one. If the conventions differ only slightly in fit, the correct reported outcome is "not distinguishable at this size", which should be preregistered as an admissible result rather than treated as a failure.

---

## 10. Deviations policy

| Rule | Draft |
| --- | --- |
| Any change after freeze is a numbered deviation, recorded with timestamp, reason and the state of knowledge at the time |
| Deviations discovered before any measured evaluation quantity is read are results-blind and may be adopted with a recorded justification |
| Deviations proposed after the sealed look are recorded but NOT adopted; the frozen analysis stands and the proposed change is reported separately as a post hoc observation |
| A defect in a source record (malformed SMILES, mislabelled instrument, tautomer re-deposition) is handled by the preregistered manual-review path, not by an ad hoc exclusion |
| Failure of the S3 negative control voids the primary endpoints and requires a documented pipeline repair and a fresh freeze |

---

## 11. Design B skeleton, if promoted

Included only at outline depth, because section 3.4 of the design document establishes some acquisition parameters and explicitly defers others.

| Element | Status |
| --- | --- |
| Compounds | Previously unseen, screened against every exclusion set in section 2.2 plus the tautomer and skeleton guards |
| Precursor stratification | Low (below 350), null (450 to 550, negative control), high (750 to 995). Grounded: K1 and K2 coincide exactly at m/z 500, and 995.556 is the checkpoints' training precursor ceiling |
| NCE ladder | 15 to 90 in steps of 5 (16 rungs), which necessarily includes MURU's frozen 20 and 60. Grounded in the measured training support: raw-NCE support is {15, 20, 30, 45, 60, 75}, the unresolved integer ladder runs to 90, and the converted-eV support has q05 7 and q95 74 |
| Below NCE 15 | DEFERRED. Not established by the provenance: 5 and 10 are extrapolation under K1 but in-support under K2, and that asymmetry is itself informative, so the decision must be explicit |
| Replicates, injection order, isolation window, stepped-energy control arm | DEFERRED, not established by any evidence in this study |
| Freeze point | Acquisition protocol frozen and published before any prediction is generated |
| Additional objectives | Full fragmentation-extent curves; whether MURU captures trajectory shape beyond two rungs; behavioural discrimination of GLACIER's H_floor against H_raw |

---

## 12. Open items requiring user decisions

| Id | Item | Why it needs a decision | Blocking? |
| --- | --- | --- | --- |
| O1 | Tagged-releases-only C01 (33 compounds, 33 groups) or the extended variant including unreleased dev PR #398 (44, 44) | 25 of 58 primary-tier compounds come from an unreleased pull request whose records could still change before release. A design that must cite a released tag cannot use them | YES |
| O2 | C01 scan-window compatibility with MURU's external rule (first mass at or below 40, upper at or above [M+H]+ plus 1) was never evaluated | In C02 this rule eliminated two of three record series. If C01 fails it, the MURU arm cannot run on this population at all and the design changes shape | YES |
| O3 | Minimum annotated peak count, and whether to drop the NCE 15 rung | NCE 15 has median 2 peaks with 21 of 59 primary-tier records at 1 peak or fewer. An endpoint on fragmentation extent is poorly supported at that density | YES |
| O4 | Accepting NCE 30 and 60 (or the full ladder) in place of MURU's frozen NCE 20 and 60 | Only 2 of 58 primary-tier compounds carry NCE 20. This is a declared deviation from MURU's frozen external interface and needs explicit sign-off | YES |
| O5 | Whether FIORA-OS is a comparator in this study | Including it forces exclusion of MSnLib nine-library compounds (150 of 403 C01 candidates), shrinking an already thin population. Recommendation: exclude | YES |
| O6 | Calibration and evaluation split ratio at 33 to 44 scaffold groups | Determines whether either fold is usable | YES |
| O7 | Source of the effect size for sample-size justification, or a declared smallest scientifically relevant difference | No non-exposed effect size is currently in hand | YES |
| O8 | The calibration criterion itself | Must be a single scalar, declared before the split is drawn, computed identically for all three conventions | YES |
| O9 | Whether a per-checkpoint mapping is acceptable, or whether a single mapping must be forced across all comparators | The provenance shows the three checkpoints share a training axis but not a preprocessing chain, so disagreement is plausible. Forcing one mapping would be a scientific choice, not a technical one | YES |
| O10 | Whether to include the C02 high-mass stratum, given it is one chemical class (cyanobacterial cyclic peptides), identity-weak (only 49 of 150 uploaded compounds are Level 1), and 27 of 81 clean compounds sit above the checkpoints' precursor ceiling | Without it there is almost no coverage above m/z 500; with it the high-mass arm is confounded with chemical class | NO, but it changes the claim |
| O11 | Whether to fetch C01 and C02 record files, which contain peak lists | Permitted and necessary for execution, but deliberately not done during the outcome-blind provenance phase. Needs an explicit authorisation | YES, for execution |
| O12 | Whether to proceed to Design A at all, or go directly to Design B | A mapping fixed on 33 to 44 compounds from a single non-MURU lab may be too thin a basis for the subsequent comparator evaluation. The evidence supports either answer and this is a judgement call | YES |
| O13 | Rename or re-derive `artifacts/ce_interface_adjudication/exclusion/muru_exposed_union_keys.txt` | It is the exposure registry united with the PR #7 population (33,301 keys), not the 1,912-key union of the 16 exposed populations that its name implies. One screen's figure already came from the mislabelled file | NO, but fix before reuse |
| O14 | Whether the Bash copy route into this worktree is an acceptable substitute for the Write tool, which refuses writes here | Five phases hit this guard; two phases (P1 and P2) lost their outputs to it until this synthesis recovered them from the session scratchpad | NO, process only |

---

## 13. Status

Nothing above is frozen. No population is fixed, no criterion is declared, no split is drawn, no prediction has been generated, and no convention has been selected. Two corrections from the Task C completeness-critic pass are already folded in, C-14 (C01 carries 15 distinct NCE values, not the nine of the modal ladder) and C-16 (the high-mass stratum's 37 / 21 requires NCE 20 and 60 as well as the scan mode and the precursor ceiling); both are recorded in the design document's section 2.4b. Eleven of the fourteen open items in section 12 are blocking, and two of them (O2 and O12) can change the design's shape rather than only its parameters.
