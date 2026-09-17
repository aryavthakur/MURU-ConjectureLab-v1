# MURU collision-energy interface adjudication, Phases 1 to 3: candidate conventions, feasibility, design recommendation

Status: DESIGN DOCUMENT, outcome-blind. Nothing is frozen and no execution is authorized.
Companion: `MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md` (all provenance evidence and counts).
Branch: claude/muru-ce-interface-adjudication at 5b1c502. Date: 2026-09-15.

Standing constraint on everything below: the closed 1,327-compound comparator benchmark was not used to choose, tune, validate or justify any item in this document, and its outcome files were never opened. No effect size, threshold or coefficient anywhere in this document derives from it.

Evidence convention, the same one Phase 0 uses: VERIFIED means read in code or data and reproduced; INFERRED means derived by argument from verified facts; UNRESOLVED means not decidable from available material. Every count in section 2 is VERIFIED against the screen artifacts under `artifacts/ce_interface_adjudication/screen/` and re-derived by the verification lens recorded in `notes/v_screen.md`, except where a cell says otherwise. Every provenance count quoted in section 1 is VERIFIED against `artifacts/ce_interface_adjudication/counts/`. The verdicts themselves (SUITABLE, PARTIAL, UNSUITABLE) and the recommendation in section 3 are INFERRED: they are judgements over verified counts, not measurements.

---

## 1. Phase 1: candidate-convention decision table

### 1.1 What the deployment mapping is

A deployment mapping is a function from the acquisition setting of a new spectrum (Orbitrap HCD, normalized collision energy `NCE`, precursor `mz`) to the single float placed in the checkpoints' `collision_energy` input. It is a discrete choice among named formulas. It is NOT a fitted parameter: section 1.4 excludes that explicitly.

### 1.2 Conventions KEPT as predeclared discrete candidates

| Id | Convention | Upstream evidence FOR it being a genuine training or deployment convention | Upstream evidence AGAINST | Kept? |
| --- | --- | --- | --- | --- |
| K1 | `CE_input = NCE` (raw normalized collision energy, integer) | At least 30,631 and at most 49,891 training rows carry a raw NCE number that no code ever converted (Phase 0 section 5.5 bracket). For the MSnLib block this is established by code provenance, not inference: the MassSpecGym parser converts only strings containing `%`, MSnLib MGF headers carry a bare float, and `nce_to_ev` has zero call sites in any MSG training path. The `inten_contr` CE-key filter removes only MassBank or MoNA rows, raising the raw-NCE share further. The validation split that selected every best checkpoint is 70.5% raw-NCE Orbitrap rows | Nothing in the code labels the stored field as NCE; the field is unit-free. Upstream inference tooling (`iceberg_elucidation` with `nce=True`, the webui) treats the model input as eV and converts user NCE by `/500`, though every such instruction is attached to NIST-trained checkpoints, not to these | YES |
| K2 | `CE_input = NCE x precursor_mz / 500` (documented eV), unrounded | 23,894 training rows provably carry exactly this quantity: they satisfy `CE = n x mz / 500` for integer `n` within own-decimal tolerance against 0.41 rows expected by chance, with `n` a multiple of 5 in 23,888. This is the strongest identification in the whole provenance review. The constant 500 is the ms-pred constant at `misc_utils.py:2557`. The ICEBERG preprint states CE in eV | Those 23,894 rows are 20.1% of the training table, not a majority, and they coexist on one numeric axis with raw-NCE rows from the same instrument class. Neither model applies the conversion itself: precursor m/z never enters any CE conversion in any model or predict path. The MassSpecGym paper's own "53% normalized collision energies" figure equals the share of rows with any CE at all, so it does not support an NCE reading either | YES |
| K3 | `CE_input = floor(NCE x precursor_mz / 500)` (integer-rounded conversion) | This is what ICEBERG actually received for every converted row. The committed `msg/labels.tsv` CE equals `floor(MSG CE)` on all 119,029 rows; the `msg_simulation` path rounds with `f'{x:.0f}'`; the presented value equals `floor(CE)` on all 106,838 rows `inten_contr` retained. So an integerised conversion is not a hypothetical, it is the realised training convention for category (2) | The integerisation is an artifact of ms-pred's key handling, not a physical quantity, and it is not what GLACIER necessarily saw (Phase 0 U1 leaves H_raw live). K2 and K3 differ by less than 1, and a difference of 1 has embedding distance 1.47 against a random-phase expectation of 8.0, so the two are near but not identical | YES |

Relationship among the three, needed for the selection rule: at MURU's frozen external rungs (NCE 20 and 60, both integers) K1 and any integerisation of K1 coincide exactly, so no separate "rounded raw NCE" candidate is required. K2 and K3 differ only by the floor, which is exactly the unresolved GLACIER question U1; keeping both turns an unresolved provenance item into a testable discrete alternative rather than an assumption. K1 and K2 coincide exactly at precursor m/z 500 and diverge as `|1 - mz/500|` grows, which is the identifying structure any design must exploit (section 3.3).

### 1.3 Conventions CONSIDERED and EXCLUDED

| Id | Convention | Why excluded |
| --- | --- | --- |
| X1 | Imputed-energy convention: `int(nce_to_ev(NCE, precursor))` over an NCE grid of 5 to 150 | Upstream provenance shows it was NOT used in training for any frozen checkpoint. It lives in `run_scripts/iceberg/msg_all/04_impute_missing_collision_energies.py`, whose configs use datasets `msg_known_ce` and `msg_all_iceberg`; those experiment names match neither the checkpoint pickle strings nor the step counts. Imputed rows are 0 for all three checkpoints (verified by executing the ms-pred filter functions over T_sim). Its own docstring contradicts its code on the grid range (5 to 100 against 5 to 150), which is a further reason not to treat it as a documented convention |
| X2 | Source-conditional convention (raw NCE if the spectrum came from MSnLib, converted eV if from MassBank) | This IS the true generative structure of the training axis, and Phase 0 section 5.3 quantifies it. But it is not deployable: a deployment cannot know which library a newly acquired spectrum "would have come from". Excluded as a mapping, retained as the explanation for why any single mapping is a compromise |
| X3 | Instrument-conditional convention (Orbitrap branch and QTOF branch) | Supported upstream: QTOF rows entered as native eV or volts and Orbitrap rows did not. But MURU's claim scope is a single instrument class (Orbitrap HCD, [M+H]+, fixed NCE), so for this deployment the rule collapses to its Orbitrap branch and adds no discriminable alternative. Excluded as a candidate, PROMOTED to a hard design constraint: no QTOF data may enter an Orbitrap interface adjudication, and no candidate dataset may mix the two instrument classes in one estimand |
| X4 | Continuous fitted scale factor, for example `CE_input = a x NCE x mz / 500 + b` with `a`, `b` estimated | Excluded by the study's own mandate and independently by principle: a fitted coefficient would absorb the very ambiguity under adjudication and would not be checkable against upstream provenance. No coefficient anywhere in this design is optimized on any data |
| X5 | Round-half-even integerisation of raw NCE | Collapses to K1 at integer rungs, so it is not discriminable. Noted only because ms-pred's rounding is half-to-even (27.5 to 28, 28.5 to 28, 32.5 to 32), which matters for any non-integer acquisition setting but not for NCE 20 and 60 |

### 1.4 Explicit exclusions restated

No continuous fitted scale factor. No coefficient optimized on any data, exposed or not. No mapping selected by any quantity computed on the closed 1,327-compound benchmark. The Phase 1 candidate set is exactly `{K1, K2, K3}` and is closed unless new upstream provenance appears.

---

## 2. Phase 2: overlap and feasibility assessment

### 2.1 Screening criteria

Eleven criteria were applied to each candidate: (1) absent from MURU development, (2) absent from the PR #7 confirmation population, (3) absent from the comparator benchmark population, (4) absent from ICEBERG and GLACIER training at compound level (MassSpecGym 1.5, all folds, InChIKey14), (5) known CE semantics, (6) [M+H]+ positive mode available, (7) compatible fragmentation and instrument metadata, (8) multiple energies per compound, (9) structural diversity and scaffold count after all exclusions, (10) license and access, (11) hidden MassSpecGym inclusion under a different identifier.

Exclusion sets used: MassSpecGym 1.5 keys (28,929 recorded plus 28,923 MURU parent keys, union 28,952), MassSpecGym simulation-challenge keys (16,974), MURU exposure registry (31,507 keys, 18,402 scaffold groups), the 16 exposed populations (1,912 keys), the PR #7 frozen population (1,794 keys, 1,691 groups), the comparator common population (1,327 keys, 1,254 groups). Keys and scaffold groups are MURU `parent_connectivity_key` and `scaffold_group_v2`, recomputed from source SMILES with `scripts/ce_interface_adjudication/scaffold_key.py` (self-test passes 1,327 of 1,327 and 1,794 of 1,794).

### 2.2 Screened candidates

Counts below are the CORRECTED values where the verification lens refuted the screen; corrections are itemised in section 2.4.

| Id | Candidate | Verdict | Blocking criteria | Compounds after all exclusions | Scaffold groups after exclusions | Energies per compound | CE semantics |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | MassBank Eawag EQ records first released after MassBank 2023.11 (releases 2024.06, 2024.11, 2025.10, plus unreleased dev PR #398) | SUITABLE_DESIGN_A | None. Criterion 11 PARTIAL (residual MoNA or GNPS mirror route not excludable from metadata) | 111 compound-level; 58 primary tier; 44 conservative tier; 41 strict tier. Tagged releases only: 86 / 46 / 33 / 31 | 76 / 57 / 44 / 41 (Butina clusters 41 / 29 / 26, corrected) | 403 of 415 have >= 3 distinct NCE; 15 distinct NCE values exist across the 5,051 records (15, 20, 25, 30, 40, 45, 50, 60, 70, 75, 80, 90, 120, 150, 180), but the modal ladder is the nine-value 15,30,45,60,75,90,120,150,180 and the six off-ladder values are carried by at most 2 primary-tier compounds each (NCE 80 by 1); median 6 rungs inside 15 to 90 | Single `N % (nominal)` instrument NCE on 5,051 of 5,051 records, 0 ramps or lists. NOT in MassSpecGym, so the `/500` conversion has never been applied to them |
| C02 | CyanoMetDB in MassBank 2026.03 (EAWAG-EC, EAWAG-ED, MLU-ED) | PARTIAL_OR_SUPPORTING_ONLY | 9 (diversity); 4 and 7 PARTIAL | 107 rows / 104 keys after key exclusion; 84 rows / 81 keys after scaffold exclusion; 53 that additionally carry both NCE 20 and NCE 60 AND sit inside the models' precursor range; 37 of those 53 in the EC scan-mode arm | 45 / 33 / 21; only 20 Butina clusters at Tanimoto 0.4 over the 81 | Median 9 (15,20,25,30,40,50,60,70,80) | Single `N % (nominal)` NCE, HCD, triply documented |
| C03 | MassBank 2023.11 in-training Orbitrap HCD contributors (NaToxAq, Eawag EQ and EA, Eawag_Additional_Specs, UFZ, HBM4EU, AAFC) | PARTIAL_OR_SUPPORTING_ONLY (attribution only) | 1, 4, 9, 11 | 15 after key exclusion; 5 after scaffold exclusion, 4 of those above m/z 1,000 | 11 / 4 | Median 7 distinct CE | Both parser arms on ONE instrument class: 16,960 converted-only and 9,819 raw-only linked MassSpecGym rows |
| C04 | ELIXDB lichen library (GNPS, MetaboLights MTBLS8109) | UNSUITABLE | 5, 8, 9, 11 | 72 [M+H]+ keys | 24 | 1, and it is a MERGED stepped scan (10, 35, 80 combined into one spectrum) | Undocumented and moot: one constant string, no unit, no per-spectrum value; the individual activations are not deposited anywhere |
| C05 | BOKU, Mendel and Masaryk prenylated flavonoid library (Zenodo 16762591) | PARTIAL_OR_SUPPORTING_ONLY | 4, 9; 1, 5, 6, 7 PARTIAL | 17 strict; 64 lenient | 12 strict; 25 lenient (51.6% of compounds in 3 groups) | 10 fixed HCD plus 1 stepped plus 11 CID | Claimed absolute eV; credible for IQ-X HCD, but the CID sub-ladder contains 35 and is probably mislabelled NCE. Per-spectrum values are only inside an 18.8 MB MGF, outside download policy |
| C06 | PharmMet DB parent drugs (Metabolomics Workbench ST003991) | PARTIAL_OR_SUPPORTING_ONLY | 8 (single energy); 1 and 4 hold only for a residual; 5, 6, 7, 9, 10, 11 PARTIAL | 55, all singletons (UNTRACED denominator: 55 is tier M5 of `c06_screen_summary.json`, whose universe is 1,007 rows / 987 keys, while 689 is the deposited-and-identified key count of the `v_screen` and addendum universe of 698 rows; the two are not the same base) | 55; and 16 under the conservative full-registry exclusion, which is UNTRACED: the artifacts hold tier T5 = 15 keys / 15 groups on the 987-key universe and `v_partials.json` holds 22 on a cascade without the raw-file criterion, neither of which is 16. Immaterial to any verdict or recommendation, since criterion 8 already fails on a single energy | 1 | Single `HCD 35%`, documented only in the paper methods. Normalized is INFERRED from the percent unit |
| C07 | mFam consortium MassBank contribution, Orbitrap subset | UNSUITABLE | 1, 4, 5, 7, 9 | 6 | 6, of which 4 are acyclic pseudo-groups, so 2 real ring scaffolds | 178 of 695 have >= 3, all from one lab (MC20) | UNKNOWN for the only usable sub-collection: a bare unitless integer, no `FRAGMENTATION_MODE` anywhere in mFam, and the lab's instrument type is systematically mislabelled (Q Exactive Focus declared as LC-ESI-ITFT) |
| C08 | GNPS REFRAME-POSITIVE-LIBRARY (and CMMC sibling) | UNSUITABLE | 5, 8 | 4,350 [M+H]+ keys (ample) | 3,322 (ample) | 1, dataset-wide: one `Top_CEs` value (37) on 771,634 of 771,634 positive MS2 scans | UNKNOWN and undocumented. `collision_energy` blank in 9,618 of 9,618 library rows; the GNPS batch-upload schema has no CE field; the deposit has no associated manuscript |
| C09 | GNPS TUEBINGEN-NATURAL-PRODUCT-COLLECTION | UNSUITABLE | 5, 8, 7 (stepped acquisition) | 174 conservative; 116 after quality filters | 143 / 96 | 1, a stepped composite (submitter comment "stepped CE (25, 35, 45)", no unit); all 34 source files report one `Top_CE` of 35.0 | Undocumented at record level and moot: a stepped composite has no single deposited energy |
| C10 | MassBank BAFG SCIEX TripleTOF ladders | PARTIAL_OR_SUPPORTING_ONLY (QTOF control) | 1, 4, 7, 9, 11 | 16 (corrected from 17) | 16 (corrected), 14 strict | 1,038 of 1,070 have >= 2; 795 carry the full 15-point 10 to 150 V ladder | Bare unitless integer with an `N V` title, so volts; equals lab-frame eV for singly charged ions. MassSpecGym keeps these raw, and its QTOF CE maximum is exactly 150.0 |
| C11 | ExpoLib 1.0 (University of Vienna, Zenodo 20715576) | PARTIAL_OR_SUPPORTING_ONLY (QTOF control) | 1, 4, 9; 7 PARTIAL | 18 | 11; 4 under scaffold-level exclusion | Up to 15 [M+H]+ spectra (11 single volts 20 to 70 plus 4 spreads) | ABSOLUTE volts, triply documented (paper SI, mzmine batch file names, deposited R script) |

### 2.3 Dropped before screening, grouped by reason

| Reason | Candidates |
| --- | --- |
| MURU-exposed data (X1) | GNPS PYRROLIZIDINE-ALKALOID-SPECTRAL-LIBRARY, GNPS ECRFS_DB, GNPS WFSR-LIBRARY (all WFSR, part of WUR), WUR Mass Spectral Library (Zenodo 20552933), LCSB MassBank contributor, MultiMS2 (also QTOF), EPA ENTACT_AGILENT (also Agilent QTOF, 3 levels) |
| MSnLib lineage (X2), disfavoured fallback only | GNPS MCE-DRUG (2,842 of 2,867 keys in MSnLib), GNPS MSNLIB-POSITIVE and MSNLIB-NEGATIVE, MSnLib raw and library files (Zenodo 11163381, 10966404, 10967081, 10966280; MassIVE MSV000094528) |
| No usable CE ladder: single, stepped, ramped or merged | ACES_SU PW-FDA (one ramped spectrum per compound), SMB_Measured and Shin-MassBank (ranges and stepped lists), EMBL-MCF 1.0 and 2.0 (stepped only), GNPS BERKELEY-LAB (stepped CE in compound names), CASMI 2016 (stepped 20/35/50 merged), FREMS near-continuous ramp (ion-trap CAD, not beam-type HCD) |
| CE field absent or unverifiable in permitted metadata | GNPS-LIBRARY post-snapshot submissions, GNPS CMMC-FOOD-BIOMARKERS, GNPS LEAFBOT, GNPS WINE-DB-ORBITRAP and WINE-DB-QTOF, GNPS-ALKYLAMINES libraries, BMDMS-NP, several MoNA collections (VF-NPL QExactive, HCD_natural_product_library, UVPD Library, Alkaloids QE pos, PFP NP, Plant Metabolites NIST, POS_Metabolite_IDX, DNAAdduct), CASMI 2022, ORNL drop-on-demand OPSI |
| Wrong instrument class for an Orbitrap adjudication (X3) | Athens_Univ (Bruker maXis Impact), Enveda-180 (timsTOF), GNPS-ION-MOBILITY-LIBRARY, DMIM-DRUG-METABOLITE-LIBRARY, MUI PSY-SUB NPS (TripleTof), HBM4EU QTOF records, other MassBank QTOF contributors |
| Licensed, paywalled or not reference standards | mzCloud, NIST20/23/26, Wiley Registry MSforID (compound list only), HighResNPS (consensus fragment lists), NIOM extractables (access restricted), MoNA NCU fungicide and EnvCpd suspect libraries (Compound Discoverer annotations, not standards), 3-HYDROXY-ACYL-AMIDES-LIBRARY (crude combinatorial candidates) |
| Circular by construction | Spectraverse v1.0.1, FragHub, MassCube DB (aggregations whose CE fields are derived by the `/500` formula under test); retained only as enumeration aids |
| Too small or too inconsistent | NILU, Utrecht Endogenous Metabolite Library (7 novel keys plus a CE contradiction), Szabo et al. 2021 energy-resolved peptides (peptides, raw only), 16 pre-rejected MassBank contributors |

### 2.4 Corrections applied from the verification lens

| Item | Screen stated | Corrected value | Cause |
| --- | --- | --- | --- |
| C01 criterion 9, Butina cluster counts | 42 (primary), 30 (conservative) | 41 (primary), 29 (conservative), 26 (strict) | The screen reported post-tautomer-exclusion compound and group counts (58, 44) alongside pre-exclusion cluster counts (for 59 and 45 compounds) |
| C06 criterion 1, development-population overlap | 90 of 689 | 94 of 689 | 90 was the count over the 651 keys identified by the DB SMILES route only; the 4 keys identified by the PubChem name route were omitted, so the numerator and denominator came from different sets. Criterion stays NOT_MET |
| C10, post-exclusion cascade | 954 charge-neutral, 17 final compounds and 17 groups, 15 strict | 953 charge-neutral, 16 final compounds and 16 groups, 14 strict; intermediate steps 42 and 40 | Cetylpyridinium's deposited SMILES places the positive charge on a ring carbon rather than the quaternary nitrogen; RDKit's Uncharger neutralises that carbocation and returns a neutral parent that does not exist. It is a permanent cation and cannot supply an [M+H]+ measurement. Criterion 6's "every sampled [M]+ sits on a permanent-cation parent" needs the same correction. Verdict unchanged |

Two further verification findings that change how the screens should be read, without changing a verdict:

| Finding | Consequence |
| --- | --- |
| `artifacts/ce_interface_adjudication/exclusion/muru_exposed_union_keys.txt` (33,301 keys) is NOT the union of the 16 exposed populations (1,912 keys). It is the exposure registry (31,507) united with the PR #7 population (1,794), verified by set arithmetic | Any figure quoted as an "exposed union" count must be checked against which file produced it. C04 and C10 used the population files and are unaffected; C09's figure of 54 came from the mislabelled file and is really 53 registry hits plus 1 PR #7 hit. The file should be renamed before reuse |
| C01 has a feasibility problem no criterion measures: peak sparsity at low NCE. Over the 475 primary-tier [M+H]+ records, `PK$NUM_PEAK` has median 8 but 29 records carry at most 1 peak and 92 at most 3. By rung, NCE 15 has median 2 peaks with 21 of 59 records at 1 peak or fewer. These are RMassBank-annotated records, so only recalibrated formula-assignable peaks survive and the low rungs are sparse by construction | For an endpoint defined on fragmentation extent, roughly a third of NCE-15 measurements carry a single annotated peak. Any design using C01 must either drop the 15 rung or preregister a minimum-peak filter. Criterion 8 still holds per compound: the median clean compound has 5 rungs carrying at least 3 peaks inside 15 to 90, and only 1 of 58 primary-tier compounds has fewer than 3 such rungs |

### 2.4b Corrections applied by the Task C completeness-critic pass

A later completeness pass re-derived the C01 screen numbers this document quotes that the screen artifacts do not
record as a named field (`scripts/ce_interface_adjudication/c_taskc_recheck_c01.py`, output under key
`C01_screen_recheck` in `artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json`). No verdict changed.

| Id | What was wrong or missing | Correction |
| --- | --- | --- |
| C-6 | The document stated no evidence convention and tagged almost nothing VERIFIED or INFERRED, although Phase 0 defines and uses that convention throughout | Convention added at the head of the document, with an explicit statement that the verdicts and the recommendation are INFERRED judgements over verified counts |
| C-7 | 1.4 said "no coefficient optimized on any exposed data", weaker than X1 to X5 and than the outline, which both say "any data" | Now "any data, exposed or not" |
| C-8, C-14 | The C01 row and the outline's energy-cell section named the nine-value modal ladder as though it were the set of rungs C01 carries. C01 carries 15 distinct NCE values; the modal ladder covers 4,902 of the 5,051 records and the six off-ladder values are carried by at most 2 primary-tier compounds each (NCE 80 by 1). The screen's own verification note had repeated a truncated 12-value list, corrected there too | Full set stated in both documents, with the modal-ladder restriction named as a design choice rather than a fact about the library |
| C-9, C-10, C-16 | C02's 53-compound figure also requires NCE 20 and NCE 60, and the 37-compound EC arm is set P9 = P3 and NCE 20 and 60 and precursor range and first mass 40, not "NCE 20 to 80 complete" | Both definitions restated as verified; the 20 to 80 ladder is named as the library's modal ladder |
| C-11 | 3.4's category (4) row carried the all-source q95 of 90 in a row labelled by the MassBank ladder, and called NCE 120 and above "extrapolation on any reading" although 120, 150 and 180 are present in the training table | q95 corrected to 120 for the MassBank or MoNA arm with the all-source figure named alongside; "extrapolation" replaced by the measured sparsity, 1,205 of 18,365 rows (6.6%) |
| C-12 | "one clean compound has records from two instruments" did not say at which tier | 1 of the 112 compound-level-clean compounds, 0 in the primary, conservative and strict tiers; platform and resolution record counts added |
| C-13 | 2.5's "Tagged releases only: 33, 46, 31" gave three bare numbers in an order the reader had to infer, with no group counts | Tier order named and group counts added (conservative 33 in 33, primary 46 in 45, strict 31 in 31) |
| C-15 | The outline stated no evidence convention and did not say that its counts are carried over rather than newly measured | Convention added at its head |
| C-17 | C06's compound counts could not be traced: "55 (of 689)" takes numerator and denominator from two different screen universes (1,007 rows / 987 keys against 698 rows / 689 keys), and no artifact holds a 16-member C06 set. This is the same class of defect the verification lens already found in C06 criterion 1 ("90 of 689", correctly 94) | NOT FIXED, flagged in place. The numbers are left as the screen wrote them and marked UNTRACED rather than replaced by a guess. C06 is PARTIAL_OR_SUPPORTING_ONLY on criterion 8 (a single energy), which no compound count can change |

Numbers this pass re-derived and CONFIRMED: the Butina cluster counts 41 (primary), 29 (conservative) and
26 (strict), which the screen artifacts record only for the pre-tautomer primary tier; the tier cascade
112 / 59 / 45 / 42 before the tautomer step and 111 / 58 / 44 / 41 after, with tagged-only 86 / 46 / 33 / 31 and
tagged conservative groups 33; the primary-tier [M+H]+ range 100.04 to 784.53 with 18 at or above 500 and the
conservative-tier 16; NCE 60 on 58 of 58 and NCE 20 on 2 of 58 primary-tier compounds; median 6 rungs inside
15 to 90; and the full peak-sparsity census (475 records, median 8, 29 at 1 peak or fewer, 92 at 3 or fewer,
NCE 15 median 2 with 21 of 59 records at 1 peak or fewer).

### 2.5 Does any public population support a clean adjudication?

Stated plainly, without force-fitting:

| Question | Answer |
| --- | --- |
| Is there a public population that can adjudicate among K1, K2 and K3 for the Orbitrap HCD deployment? | YES, but only one, and only at limited power: C01. It is the sole candidate meeting criteria 1 to 8 with usable structure, and it has the decisive property that its records are absent from MassSpecGym, so the `/500` conversion has never been applied to them and remains a free variable rather than a property of the source |
| How large is that population? | 44 compounds in 44 scaffold groups (conservative tier), 58 in 57 (primary tier), 41 in 41 (strict tier). Tagged releases only, same tier order: conservative 33 in 33, primary 46 in 45, strict 31 in 31. A scaffold split therefore leaves roughly 10 to 20 compounds per side |
| Is there a population that can serve as the independent MURU-against-comparator evaluation at MURU's own interface? | NO. C01 carries NCE 20 for only 2 of 58 primary-tier compounds, so MURU's frozen external pair (NCE 20 and 60) is not reproducible on it; it is a different lab and a different set of Orbitrap platforms than MURU's Orbitrap ID-X deployment; and at 44 to 58 compounds it cannot carry both a calibration split and a powered evaluation |
| Is there high-mass coverage? | Only 16 of the 44 conservative-tier C01 compounds sit at or above m/z 500 (maximum 784.5). C02 is the only verified independent Orbitrap NCE ladder with precursor/500 above 1 (1.16 to 2.19 at the 10th to 90th percentile), but its defensible core is 37 compounds in 21 scaffold groups from one chemical class (cyanobacterial cyclic peptides), and 27 of its 81 clean compounds exceed the checkpoints' own training precursor ceiling |
| Is there an eV-side control? | YES, as supporting evidence only: C10 (BAFG, 10 to 150 V, 795 compounds with the full ladder) and C11 (ExpoLib, 11 single volts, triply documented). Both are QTOF, so by design constraint X3 they may support attribution but may not enter an Orbitrap estimand |
| Is there a population with a dense NCE ladder AND unexposed compounds AND MURU's rungs AND high mass? | NO. No public population found in this screen satisfies all four |

---

## 3. Phase 3: recommendation

### 3.1 The two designs

Design A: external calibration and evaluation on a scaffold split of an existing public population; calibration selects among the predeclared discrete conventions `{K1, K2, K3}` only; freeze; evaluate once; the same compounds and energy cells for MURU and every comparator.

Design B: prospective dense-NCE acquisition on previously unseen compounds, acquisition protocol frozen before any prediction is generated; aimed at interface identification, full fragmentation-extent curves, and whether MURU captures trajectory shape beyond NCE 20 and 60.

### 3.2 Recommendation

RECOMMENDED: Design A as the primary next step, scoped strictly as an INTERFACE ADJUDICATION and explicitly NOT as the independent comparator evaluation, executed on C01 (conservative tier) with C02's EC arm as a preregistered high-mass stratum; with Design B recommended as the subsequent and larger study, and promoted to primary if either trigger in 3.5 fires.

Reasons tied to the evidence:

| Reason | Evidence |
| --- | --- |
| Design A answers the study's stated question and Design B answers a strictly larger one | The central question is which deployment mapping to fix BEFORE an independent evaluation. That is a choice among three discrete formulas, which is what a calibration split can decide. Trajectory shape beyond NCE 20 and 60 is a different and later question |
| C01 has a property no other candidate has, and it is the property the adjudication needs | Its 5,051 records carry `N % (nominal)` NCE and are absent from MassSpecGym (verified by direct tree membership at tag 2023.11 and at 2025.10, not by release date alone). So the `/500` conversion is a free, testable variable there. Every in-training candidate (C03) is circular by construction, and every candidate whose own CE unit is unknown (C07, C08, C09) would use an undetermined quantity to adjudicate a quantity |
| The conventions are strongly separated on C01's mass range | K1 and K2 coincide only at precursor m/z 500. C01's primary-tier [M+H]+ range is 100.04 to 784.53 with 18 compounds at or above 500, so both sides of the null point are populated. The embedding geometry makes the separation real rather than nominal: at m/z 300, NCE 20 maps to 12 eV and the input distance is 4.38 against a random-phase expectation of 8.0 |
| Design A is executable now at low cost and no new acquisition | The records are public, CC BY-SA, and the only remaining fetch is the record files themselves, which is permitted but was deliberately not done in this outcome-blind phase |
| But Design A cannot be the comparator evaluation, and must not be presented as one | C01 lacks NCE 20 for 56 of 58 primary-tier compounds; it is a different lab and three different Orbitrap platforms mixed with two resolution settings; 25 of 58 primary-tier compounds come from an unreleased dev PR whose records could still change; and at 44 to 58 compounds a scaffold split leaves 10 to 20 compounds per side |
| Design B is the stronger science and the only route to the trajectory-shape claim | Only a prospective acquisition can put unexposed compounds, MURU's own rungs, a dense ladder and a deliberate precursor-mass stratification in one dataset. Section 2.5 establishes that no public population does |
| Design B is also the only route to closing U1 and U4 empirically | GLACIER's presented value (floor against raw) and the unit of the 18,340 unresolved MassBank rows cannot be settled from public material. A designed acquisition that places compounds at both sides of m/z 500 with a fine NCE grid can discriminate the hypotheses behaviourally without needing the non-public training files |

### 3.3 Design A scope, if adopted

| Element | Specification |
| --- | --- |
| Population | C01 conservative tier, tagged releases only: 33 compounds in 33 scaffold groups. The 44-compound conservative tier including dev PR #398 may be used only if the design accepts an unreleased source; state which at freeze |
| High-mass stratum | C02 EC arm (first-mass-40 scan mode, both NCE 20 and NCE 60 present, precursor m/z at or below 995.556 to stay inside the checkpoints' training precursor support), 37 compounds in 21 scaffold groups. VERIFIED definition: screen set P9 = P3 and NCE 20 and 60 and precursor range and first mass 40. The full 20 to 80 ladder is the library's modal ladder, not a verified property of all 37. Declared as a separate stratum, never pooled into a single estimand with C01 |
| Split | Scaffold-disjoint calibration and evaluation split on `scaffold_group_v2`, with the tautomer key and formula-constrained skeleton key applied as exclusion guards (section 3.6) |
| Calibration | Selects one of `{K1, K2, K3}` by a preregistered criterion evaluated on the calibration fold only. No continuous parameter is fitted |
| Evaluation | Run once, after freeze, on the held-out scaffolds; identical compounds and identical energy cells for MURU and every comparator |
| Energy cells | Restricted to the rungs C01 actually carries with adequate peak support. NCE 15 is excluded or gated by a minimum-peak filter declared at freeze (section 2.4) |
| Explicit non-claim | The result licenses a deployment mapping. It does not license any statement about relative model accuracy |

### 3.4 Design B acquisition parameters that the provenance review DOES establish

The provenance review establishes the training CE support in each candidate unit, so an acquisition range can be grounded rather than guessed:

| Axis | Training support established by Phase 0 | Implication for acquisition |
| --- | --- | --- |
| Raw NCE (category 1) | Exactly 6 values: 15, 20, 30, 45, 60, 75; median 30 | An NCE ladder must cover 15 to 75 at minimum to stay inside the raw-NCE support |
| Unresolved integer arm (category 4), MassBank or MoNA | Modal ladder 15, 30, 35, 45, 60, 75, 90, 120, 150, 180; presented values 0 to 180, q05 15, median 45, q95 120 (gen train, MassBank or MoNA only; the all-source category (4) arm has q95 90) | NCE 15 to 90 sits inside the arm's central 90%. NCE 120, 150 and 180 are present in training but sparse, 1,205 of the 18,365 MassBank or MoNA integer Orbitrap rows (6.6%), so they are thin support rather than extrapolation |
| Converted eV (category 2) | Presented values 2 to 358, q05 7, median 26, q95 74, from source NCE median 50, q05 15, q95 120 | An acquisition at NCE 15 to 90 over a 150 to 1,000 m/z range produces eV equivalents of roughly 4.5 to 180, which covers the converted support's central 90% and overshoots its tail, as intended |
| Precursor m/z | MassSpecGym maximum 999.396; ICEBERG label maximum 995.556; MURU development range 70.0 to 1042.6; GLACIER `upper_limit` 1500 | Stratify precursor m/z, because it is the identifying variable: K1 and K2 coincide exactly at m/z 500 |

Recommended, and grounded in the table above: an NCE ladder of 15 to 90 in steps of 5 (16 rungs), which necessarily includes MURU's frozen rungs 20 and 60, on compounds stratified into a low-mass arm (precursor below 350), a null arm (450 to 550, where K1 and K2 are indistinguishable and which therefore serves as a negative control for the discrimination itself), and a high-mass arm (750 to 995). Whether to acquire below NCE 15 is NOT established by the provenance: the raw-NCE support starts at 15, so 5 and 10 would be extrapolation on the K1 reading while being inside support on the K2 reading. That asymmetry is itself informative, so the decision is deferred and must be made explicitly at preregistration rather than defaulted.

Also not established and deferred: replicate count per cell, injection order and randomisation, isolation window, and whether to include a stepped-energy arm as a negative control.

### 3.5 Triggers that promote Design B to primary

1. Design A's calibration fold cannot separate `{K1, K2, K3}` at its available size, judged by a criterion preregistered before the split is drawn.
2. The trajectory-shape question (whether MURU captures fragmentation-extent curve shape beyond two rungs) is wanted as a claim, since no public population can support it.
3. The user decides that a mapping fixed on 33 to 44 compounds from a single non-MURU lab is too thin a basis for a subsequent comparator evaluation. This is a judgement call, and the evidence in 2.5 supports either answer.

### 3.6 Method constraints carried into both designs

| Constraint | Reason |
| --- | --- |
| Exclusion must use a canonical-tautomer key, not a similarity cutoff | The one real hidden-inclusion leak found across all 11 candidates (clethodim in C01) sits at Morgan2 Tanimoto 0.5424 to its MassSpecGym counterpart, below any threshold a reviewer would set. It was caught only by the tautomer key. MassBank re-deposits compounds under changed structural representations |
| A formula-constrained skeleton-key hit is a manual-review trigger, not an automatic exclusion | The unconstrained skeleton key produces false positives (it paired aflatoxicol with aflatoxin B2, a different substance sharing formula and heavy-atom skeleton) |
| Cross-check the MURU parent charge against the record's own recorded InChIKey protonation layer | The Cetylpyridinium defect (section 2.4) shows a malformed source SMILES can silently admit a permanent cation into an [M+H]+ population |
| No QTOF data in an Orbitrap estimand | Design constraint X3 |
| Instrument platform and resolution must be balanced or blocked | C01's [M+H]+ records span three Orbitrap platforms under four instrument strings (Exploris 240 under two spellings 2,576 records, Q Exactive Plus 623, Q Exactive 96) and two resolution settings (17,500 on 1,704 records, 15,000 on 1,591). One compound-level-clean compound has records from two instruments; none in the primary, conservative or strict tiers, so the confound is between compounds, not within them |
| Any power or sample-size reasoning must draw its effect size from a non-exposed source | Section 3.7 |

### 3.7 Power and sample size: what may and may not supply an effect size

No effect size from the closed comparator benchmark may be used, and none is used anywhere in this document. At present NO effect size from a non-exposed source is in hand, so neither design can yet state a powered sample size. The candidate non-exposed sources, in order of preference:

| Source | Status | Comment |
| --- | --- | --- |
| A preregistered pilot block inside Design B itself, analysed only for variance components and never for the endpoint | Not yet run | The cleanest option, and the only one that measures the actual acquisition's variance |
| The C01 public ladder used purely as a variance-estimation set, held strictly separate from any evaluation compounds | Available now | Requires fetching the record files (permitted, not yet done). Its own peak sparsity at low NCE would bias a naive variance estimate, so it must be restricted to rungs passing the minimum-peak filter |
| Dispersion figures reported in the comparator papers themselves (ICEBERG preprint, GLACIER paper, MassSpecGym) | Available now | Published, not exposed. Weakest option because their metrics and populations differ from this design's |
| MURU internal variance components from studies outside the closed benchmark | Unknown to this study | Whether any exist outside the exposed perimeter is a question for the user, not decidable here |

Until one of these supplies an estimate, the design must instead declare a smallest scientifically relevant difference a priori and size to that. Recorded as an open item in the preregistration outline.

---

## 4. Summary of what this document decides and does not decide

| Decided here | Not decided here |
| --- | --- |
| The Phase 1 candidate set is exactly `{K1 raw NCE, K2 NCE x mz / 500, K3 floor(NCE x mz / 500)}`, with X1 to X5 excluded and each exclusion justified from upstream provenance | Which of K1, K2 or K3 is correct. Nothing in this study selects a mapping |
| That C01 is the only public population supporting a clean interface adjudication, at limited power, and that no public population supports an independent comparator evaluation at MURU's own interface | Whether the user accepts a mapping fixed on 33 to 44 compounds from one non-MURU lab |
| That Design A is recommended as the next step, scoped as interface adjudication only, with Design B as the subsequent larger study and three named promotion triggers | Whether Design B is funded and run |
| A grounded NCE ladder (15 to 90 in steps of 5) and a precursor-mass stratification (low, null at 450 to 550, high) for Design B, each tied to measured training support | Acquisition below NCE 15, replicate counts, isolation window, and sample size, all of which lack a grounded basis and are deferred explicitly |
