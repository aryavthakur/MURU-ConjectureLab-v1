# TASK V (v_screen) - SCREEN lens adversarial re-check

Date 2026-09-15. Lens: SCREEN. Scope: re-check the overlap and feasibility verdicts for the
top-ranked candidate datasets, with priority on the single SUITABLE_DESIGN_A verdict (C01) and the
PARTIAL_OR_SUPPORTING_ONLY verdicts (C02, C03, C05, C06, C10, C11).

Method rule applied: default to refuted for any SUITABLE claim that cannot be reproduced from raw
inputs. Nothing in the screen phase's own derived columns was trusted where a re-derivation was
possible: every compound key and scaffold group used below was recomputed from the stored SMILES
with `scripts/ce_interface_adjudication/scaffold_key.py` (rdkit 2026.03.5, self-test PASS: 1327/1327
and 1794/1794 key and group matches against the frozen comparator and study-2 populations), and every
membership test was re-run from the raw key/scaffold-group list files in
`artifacts/ce_interface_adjudication/exclusion/`.

No model, prediction or inference of any kind was run. No forbidden result, prediction,
prediction_verification, measured-mu or `*_RESULT.md` file was opened. Network use was limited to the
public GitHub API (trees, tags, pull requests, record text) - see "Spectra discipline" below.

## 0. Exclusion-set integrity (prerequisite)

Re-read from disk, counted and cross-checked:

| list | n | check |
|---|---|---|
| msg15_keys_all | 28,929 | folds 22,746 / 3,185 / 2,998, pairwise disjoint, union = all |
| msg15_parent_keys_all | 28,923 | union with recorded route = 28,952 |
| msg15_simchallenge_keys_all | 16,974 | |
| msg15_scaffold_groups_all | 16,991 | |
| muru_exposure_registry_keys | 31,507 | disjoint from PR #7 population |
| muru_exposure_registry_scaffold_groups | 18,402 | |
| V2-DEVELOPMENT-POPULATION keys | 1,325 | identical set to `artifacts/wur_v2/data/compounds.csv` keys |
| msnlib_study2_population_keys (PR #7) | 1,794 | comparator population is a strict subset |
| comparator_common_population_keys | 1,327 | |

**NEW ISSUE (artifact mislabel).** `exclusion/muru_exposed_union_keys.txt` holds **33,301** keys and is
exactly `muru_exposure_registry_keys` (31,507) UNION `msnlib_study2_population_keys` (1,794). It is
**not** the 1,912-key union of the 16 exposed populations. The true exposed-population union is the
union of the 16 `muru_exposure_registry_population_*_keys.txt` files = **1,912** keys, a subset of the
registry. Verdicts that quote 1,912 explicitly (C04, C10) used the population files and are fine; a
verdict quoting an "exposed union" number taken from this file is quoting registry-plus-PR7. C09's
"54 in the exposed union" is such a number (= its 53 registry hits + its 1 PR #7 hit), not an
exposed-population count.

## 1. C01 Eawag EQ post-2023.11 - verdict SUITABLE_DESIGN_A: REPRODUCED, not refuted

### 1.1 Record universe and timing, re-fetched from GitHub

Independently resolved tag 2023.11 -> annotated tag object -> commit
`9dc52cb29b7ade23e81befc3ce9eb001477ce393` (tagger date 2023-11-28T13:26:24Z), fetched the `Eawag/`
tree at that commit and at tag 2025.10 (`fd8fb15e44035c53c9d937307c04ba62ebec606d`):

- Eawag directory: **13,210** files at 2023.11, **17,591** at 2025.10 (both trees untruncated).
- `MSBNK-Eawag-EQ*`: **7,134** at 2023.11, **11,515** at 2025.10; 11,515 - 7,134 = **4,381**, exactly
  the screen's tagged-release count, and 4,381 + 670 dev-only = 5,051.
- **0 of the screen's 5,051 records exist in the 2023.11 Eawag tree.** 4,381/4,381 tagged records are
  present at 2025.10 and every one of their stored `blob_2025_10` shas equals the sha in my freshly
  fetched tree (0 disagreements). 670/670 dev-only records are absent at 2025.10.

Because MassSpecGym ingested MassBank **release 2023.11** (P3 C3, notebook 1 cell 3), absence from
that release is decisive and does not depend on the download date at all. PR dates re-fetched:
#258 created 2024-05-16, merged 2024-06-04, 1,156 files (= the 1,156 records whose first tag is
2024.06); #263 merged 2024-06-20, 2,058 files (= the 2,058 at 2024.11); #319 merged 2025-09-22,
758 files; #398 merged 2026-07-30, 670 files (= the 670 dev-only records).

*Minor unresolved bookkeeping:* 1,167 EQ records first appear at tag 2025.10 but PR #319 changed only
758 files, so at least ~409 of them entered through a pull request the verdict does not name. This
does not bear on the verdict, because tree-absence at 2023.11 is verified directly for all 5,051.

### 1.2 Record-level criteria, re-derived

All from `c01_record_metadata.csv.gz`, re-applying the filters rather than reading the screen's flags:

- precursor types: **[M+H]+ 3,295**, [M-H]- 1,756, nothing else. (criterion 6 MET)
- of the 3,295: FRAGMENTATION_MODE HCD 3,295/3,295; AC$INSTRUMENT_TYPE LC-ESI-QFT 3,295/3,295;
  instruments Exploris 240 Orbitrap Thermo Scientific 1,704 / Exploris 240 Thermo Scientific 872 /
  Q Exactive Plus 623 / Q Exactive 96; RESOLUTION 17,500 (1,704) and 15,000 (1,591). (criterion 7)
- CE string form: **5,051 / 5,051 are `N % (nominal)`**; 0 ramp, stepped, list or eV strings; the
  distinct values are **{15,20,25,30,40,45,50,60,70,75,80,90,120,150,180} %**, 15 of them (criterion 5).
  [Corrected 2026-09-15 by the Task C completeness-critic pass: this line previously listed 12 values, which
  was the truncated `ce_raw_examples` field of `v_part1.json` (a first-12 slice), not the full set. It
  omitted 75, 80 and 90 and so contradicted this same section's "median 6 rungs in 15-90" and
  "NCE 60 present for 59/59". Record counts over all 5,051: 15 682, 20 29, 25 30, 30 678, 40 29, 45 625,
  50 24, 60 631, 70 20, 75 573, 80 17, 90 527, 120 465, 150 386, 180 335. No verdict or tier count changes.]
- LICENSE on [M+H]+ records: CC BY-SA 3,253, null 42 (the 42 nulls are a harvest gap, as disclosed);
  CONFIDENCE 'standard compound' 3,253, null 42. Every primary-tier compound is 'standard compound'.
- recomputed parent key equals the screen's `parent_key` on 5,051/5,051 records, scaffold group on
  5,051/5,051, and equals the record's own recorded InChIKey first block on 5,051/5,051.

CE semantics checked against the actual record text, not only the aggregate column. Two records read
from the dev branch (header lines only):

```
MSBNK-Eawag-EQ01147901  RECORD_TITLE: PFHxPA; LC-ESI-QFT; MS2; CE: 15%; R=17500; [M+H]+
                        AC$MASS_SPECTROMETRY: COLLISION_ENERGY 15 % (nominal)   FRAGMENTATION_MODE HCD
MSBNK-Eawag-EQ01060204  RECORD_TITLE: Diphenylphosphinic Acid; ...; CE: 60%; R=17500; [M+H]+
                        AC$MASS_SPECTROMETRY: COLLISION_ENERGY 60 % (nominal)   FRAGMENTATION_MODE HCD
```

and the two cited documents re-read locally: `MassBank-web Documentation/MassBankRecordFormat.md:802`
gives `AC$MASS_SPECTROMETRY: COLLISION_ENERGY 10% (nominal)` as the example, and
`RMassBank inst/RMB_options.ini:85-94` maps a scan commented `HCD 15% NCE` to `ce: 15 % (nominal)`
(and `CID 35% NCE` to `ce: 35 % (nominal)`). Criterion 5 VERIFIED.

### 1.3 Exclusion and tiers, re-derived

Candidates = 415 [M+H]+ compounds, **403** with >= 3 distinct NCE (both reproduce exactly).

| membership | mine | verdict |
|---|---|---|
| in MassSpecGym 1.5 (either key route, all folds) | **256** (train 220 / val 19 / test 17) | 256 |
| in MURU exposure registry | **233** | 233 |
| in V2 development population | **110** | 110 |
| in PR #7 population | **0** | 0 |
| in comparator common population | **0** | 0 |
| shares a development scaffold group | **243** | 243 |
| shares a registry scaffold group | **334** | 334 |

Tiers, recomputed end-to-end and then passed through my own independent tautomer/skeleton recheck
(canonical-tautomer InChIKey14 of the MURU parent via `rdMolStandardize.TautomerEnumerator`, plus a
formula-constrained heavy-atom skeleton key, both built fresh for all 31,602 MassSpecGym structures,
the 1,325 development, 1,794 PR #7 and 1,327 comparator structures):

| tier | key-clean | after my step-4 | verdict |
|---|---|---|---|
| compound level | 112 (76 groups, 906 records) | **111 / 76 / 897** | 111 / 76 / 897 |
| primary (scaffold new vs dev pop, PR7, comparator) | 59 (58 groups, 484 rec) | **58 / 57 / 475** | 58 / 57 / 475 |
| conservative (scaffold new vs full registry) | 45 (45, 370) | **44 / 44 / 361** | 44 / 44 / 361 |
| strict (scaffold also unseen in MassSpecGym) | 42 (42) | **41 / 41 / 339** | 41 / 41 / 339 |
| tagged releases only | 87 / 47 / 34 / 32 | **86 / 46 / 33 / 31** | 86 / 46 / 33 / 31 |

My step-4 flagged **exactly one** compound out of 112, the same one: clethodim `PHXHZCIAPNNPTQ`,
whose canonical tautomer key and skeleton key both hit MassSpecGym (matched structure
`CC/C(=N/OC/C=C/Cl)C1=C(O)CC(C2CCOCC2)CC1=O`, Morgan2 Tanimoto only 0.5424). Independent
confirmation of the hidden-route mechanism the verdict discloses.

Residual structure-proximity over the survivors: **max same-formula Morgan2 Tanimoto 0.6154** (the
verdict's "max 0.62"); 51 of 112 survivors have any same-formula MassSpecGym structure; 0 at >= 0.7;
3 at >= 0.5. So a 0.9 (or even 0.7) similarity screen would have missed clethodim - the canonical
tautomer key is the load-bearing guard, exactly as the verdict says.

Shared-UCHEM-id route, re-derived from the fetched 2023.11 tree (699 distinct UCHEM ids with
pre-2023.11 EQ records): **27** of 403 candidates reuse such an id; **26** are already excluded as
MassSpecGym compounds; the 27th is clethodim (UCHEM 3178). After the tautomer step, **0** clean
compound at any tier shares a pre-2023.11 UCHEM id. Criterion 11 VERIFIED.

Other criterion-7/9 details confirmed: exactly **1** clean compound has records from two instruments
(out of 4 in the full candidate set); 18 primary-tier and 16 conservative-tier compounds have
[M+H]+ >= 500 m/z; primary-tier [M+H]+ range 100.04 - 784.53, all inside the MURU development range;
NCE 60 present for 59/59 primary-tier compounds and NCE 20 for only 2; median 6 rungs in 15-90.

### 1.4 C01 sub-claims that do NOT reproduce

**(a) Butina cluster counts are stale (pre-tautomer).** Recomputing Morgan2 / Tanimoto distance 0.6
Butina clustering:

| set | n | clusters |
|---|---|---|
| primary INCLUDING clethodim | 59 | 42 |
| primary as reported (after tautomer) | 58 | **41** |
| conservative INCLUDING clethodim | 45 | 30 |
| conservative as reported | 44 | **29** |

The verdict's criterion 9 reports "58 compounds / 57 MURU scaffold groups / 42 Butina clusters" and
"44 groups over the 44 conservative-tier compounds (all singletons, 30 clusters)": the compound and
group counts are post-removal but the cluster counts are pre-removal. Correct values are 41 and 29.
Not verdict-changing (criterion 9's adequacy argument is unaffected by one cluster), but the numbers
as written are internally inconsistent.

**(b) NEW ISSUE, not measured by any screen criterion: peak sparsity at the low rungs.** I read
`PK$NUM_PEAK` (a record header count, not peak data) for all **475** primary-tier [M+H]+ records:

- distribution: min 1, q25 4, median 8, q75 19, max 85.
- **29 of 475 records have <= 1 peak**, 56 have <= 2, 92 have <= 3.
- by rung: NCE 15 -> median **2** peaks, 21 of 59 records (36%) at <= 1 peak, 34 of 59 (58%) at <= 2;
  NCE 30 -> median 5; NCE 45 -> median 8; NCE 60 -> median 8.
- conservative tier: 26 of 361 records at <= 1 peak.

These are RMassBank-annotated records, so only recalibrated, formula-assignable peaks survive; the
low-NCE rungs are sparse by construction. This does not overturn criterion 8 - per compound the median
is still 5 rungs carrying >= 3 peaks inside 15-90, and only 1 of 58 primary-tier compounds has fewer
than 3 such rungs - but for a study whose endpoint is fragmentation extent, roughly a third of the
NCE-15 measurements carry a single annotated peak, and no screen criterion states this. The C10 screen
did run a peak-count census, so the omission is specific to C01.

**Verdict outcome: SUITABLE_DESIGN_A is NOT refuted.** Every criterion reproduces; two sub-claims are
corrected (Butina counts) or supplemented (peak sparsity).

## 2. PARTIAL / other verdicts re-checked

### C02 CyanoMetDB - REPRODUCED
Full cascade reproduced from the compound table: 142 [M+H]+ >=3-NCE rows / 136 keys -> 122 / 119 after
dropping isomer-group members -> 107 / 104 (P2, minus MassSpecGym + registry + PR7 + comparator keys)
-> **84 rows / 81 keys / 45 scaffold groups** (P3), 28 singleton groups, largest group 7. Overlaps:
14 in MassSpecGym (7 in simulation-challenge), 4 in registry and 4 in the development population,
30 rows sharing a registry scaffold group, 0 PR #7, 0 comparator. All match.

Hidden-inclusion timing verified independently: the freshly fetched Eawag trees contain **0**
`MSBNK-EAWAG-EC` and **0** `MSBNK-EAWAG-ED` files at both tag 2023.11 and tag 2025.10, and there is no
top-level `MLU` directory at either tag; PR **#366** "upload of CyanoMetDB_01" (chufz) changed exactly
**3,126** files, created 2026-01-12, merged 2026-02-02 - matching the 3,126 records (EAWAG-ED 1,536 /
EAWAG-EC 1,010 / MLU-ED 580). Criterion 11 VERIFIED.

CE semantics verified from a real record header: `MSBNK-EAWAG-EC001501` carries
`COLLISION_ENERGY 15 % (nominal)`, `FRAGMENTATION_MODE HCD`, `LC-ESI-QFT`, `[M+H]+`, title
`... CE: 15%; R=15000; [M+H]+; First mass: 40` - including the EC-series "First mass: 40" token the
verdict relies on for MURU scan-window compatibility.

Criterion 4's supporting claim also verified: MC-LR (`ZYZCGGRZINLQBL`) has 40 MassSpecGym
simulation-challenge rows at precursor 995.556 with collision_energy 59.73336, 89.60004, ...,
358.40016, whose implied NCE (CE x 500 / mz) is exactly {30, 35, 45, 60, 75, 90, 120, 150, 180} - the
Eawag ladder, already converted by the rule under adjudication.

### C03 MassBank in-training HCD contributors - REPRODUCED
1,639 design compounds; 1,615 in MassSpecGym 1.5 (all folds), 1,609 in the simulation-challenge
universe, 911 in the registry, 539 in the development population, 2 in PR #7, 0 in comparator;
**15** survivors in **11** scaffold groups after key exclusion, **5** after scaffold exclusion. Every
figure matches.

### C05 BOKU/Mendel/Masaryk flavonoids - REPRODUCED
239 distinct keys; 175 in MassSpecGym (133 in simulation-challenge), 145 in registry, 8 in the
exposed-population union, 0 PR #7, 0 comparator; 67 scaffold groups of which 48 are registry groups;
strict ladder **17 compounds / 12 groups**, strict+MassSpecGym-scaffold **12**, lenient **64 / 25**.
All match.

### C06 PharmMet - REPRODUCED except one figure
Reproduced: 698 rows / **689** unique keys / 477 groups; **545** in MassSpecGym (482 train, 482
simulation-challenge); **564** in the full registry; **135** in the exposed-population union; **1** in
PR #7; **1** in comparator; after MassSpecGym **144 keys / 111 groups**; after adding exposed-population
keys **and** their scaffold groups (400 groups, derived from
`artifacts/wur_v2_confirmation_v2/exposure_registry/excluded_compounds.csv`) plus PR #7 and comparator:
**80 keys / 78 groups** - exactly the verdict's figure.

**Does not reproduce:** the verdict's criterion 1 says "Of the 689 design compounds, ... 90 are in the
V2-DEVELOPMENT-POPULATION". The correct count over 689 unique keys is **94**. 90 is the count over the
651 keys whose identity came from the `db_smiles` route only (the `pubchem_name` route adds 4). The
sentence's denominator and its number come from different sets. Not verdict-changing: criterion 1 is
NOT_MET either way.

### C10 BAFG SCIEX TripleTOF - REPRODUCED to the charge step, then off by one
Reproduced: 1,070 positive keys / 525 groups; **911** in MassSpecGym all folds, **901** in
simulation-challenge, **830** in train; **571** in registry; **366** in the exposed-population union;
0 PR #7; 0 comparator. CE semantics verified from a real record header:
`MSBNK-BAFG-CSL25011734176` carries `COLLISION_ENERGY 140` (bare integer, no unit),
`FRAGMENTATION_MODE CID`, `AC$INSTRUMENT: TripleTOF 6600 SCIEX`, `LC-ESI-QTOF`, title ending `140 V`.

**Does not reproduce:** the exclusion cascade. The screen's own compound table is internally
inconsistent for one row: `parent_charge == 0` for **954** compounds but `charge_neutral_parent == True`
for only **953**. The single disagreeing row is **Cetylpyridinium** (`UBGDIDXCMKJWND`,
`recorded_charged = True`). Cause, traced to source: the BAFG record's deposited SMILES is
`CCCCCCCCCCCCCCCCN1C=C[CH+]C=C1`, which places the positive charge on a ring **carbon** instead of the
quaternary nitrogen; RDKit's `Uncharger` neutralises that carbocation and returns a **neutral C21H39N
"parent" that does not exist**. The real substance is a permanent pyridinium cation (correct MURU
parent key from a well-formed SMILES: `NEUSVAOJNUQRTM`, formal charge +1), and its 16 BAFG records are
titled `Cetylpyridinium; LC-ESI-QTOF; MS2; <n> V` in POSITIVE mode.

Consequence: the verdict's cascade `1,070 -> 954 -> 43 -> 41 -> 18 -> 17 -> 15` carries this compound
through to the end. Using the boolean charge flag the cascade is `1,070 -> 953 -> 42 -> 40 -> 17 ->
**16** -> **14**`. The defensible answer is 16 keys / 16 groups (14 / 14 strict), not 17 / 15, because a
permanently charged parent cannot supply the [M+H]+ measurement the deployment needs. Not
verdict-changing (criterion 9 was already NOT_MET; 16 singletons is no better than 17), but the "after"
number and the criterion-6 claim that "every sampled [M]+ sits on a permanent-cation parent (formal
charge 1)" both need the correction.

### C11 ExpoLib - REPRODUCED
Base: the compound table has 106 rows but one (`Colibactin 540 DNA-Adduct`) has no SMILES and hence no
parent key, so the correct base is **105**, as the verdict says. (A naive re-run that lets a null key
pass every `isin` test yields a spurious 19th survivor; that is my artifact, not the screen's.)
Overlaps on the 105: **85** in MassSpecGym all folds, 79 in simulation-challenge, **70** in registry,
**54** in the union file (see section 0), 45 in the development population, **0** PR #7 (keys and
groups), **0** comparator (keys and groups), 94 sharing a registry scaffold group, 100 sharing a
MassSpecGym scaffold group. **18** key-level survivors in **11** scaffold groups; **4** after scaffold
exclusion (Aflatoxicol, Deoxynivalenol 3-glucuronide, SN-38-glucuronide, Tilimycin). Every figure and
the full 18-name list match.

## 3. Hidden inclusion routes - general finding

For C01 and C02 the "same spectra deposited to MoNA/GNPS/MassBank before the MassSpecGym snapshot"
route is closed by a stronger argument than dates: MassSpecGym ingested MassBank **release 2023.11**,
and I verified directly against the freshly fetched 2023.11 tree that **none** of the 5,051 C01
records and **none** of the 3,126 C02 records existed in it. MoNA harvests MassBank releases, so a
record that is in no MassBank release before 2024.06 cannot have reached MassSpecGym through MoNA on
2024-05-13 either.

That leaves representation as the only live route, and it is real: clethodim (C01) reached
MassSpecGym as its enol tautomer under a different InChIKey and at Morgan Tanimoto 0.54. Both the
canonical-tautomer key and the formula-constrained skeleton key catch it; no similarity threshold in
normal use would. Any downstream design should keep the tautomer key in the exclusion pipeline rather
than relying on fingerprint neighbours.

One further route is **not** closed by any screen and is not closable from metadata: a MassSpecGym row
whose curation dropped a compound that a differently filtered training snapshot would have retained.
This is only relevant to C09 (which already discloses it) since both frozen checkpoints train on the
released MassSpecGym simulation-challenge subset.

## 4. Spectra discipline and disclosures

- No MGF/MSP/mzML/HDF5 spectra file was downloaded. MassBank record text was read through the GitHub
  API and piped straight into a header-line filter; peak lines were never written to disk and the
  only peak-related value retained is the header count `PK$NUM_PEAK`.
- Reads were GitHub API only (git refs/tags/commits/trees, pull requests, record contents). Nothing
  was added to `downloads_register.jsonl` because nothing was saved as a downloaded file; the derived
  tables under `screen/v_screen/` are computed outputs, not fetched files.
- No forbidden path was opened: no `MURU_COMPARATOR_BENCHMARK_RESULT.md`, no
  `artifacts/comparator_benchmark/{result,predictions,prediction_verification}`, no `*_spectra.json`,
  `*_preds.hdf5` or `*.mgf` under `technical/`, no `/Users/aryav/muru-comparators/runs/`, no measured-mu
  or analysis output, no PR bodies or comments for the comparator benchmark. Only identity columns of
  `artifacts/comparator_benchmark/population/common_population.csv` were read.
- Writes: this session's primary worktree is `muru-v2-stability-study-6537d5`, so files were authored
  in the session scratchpad and copied into the adjudication worktree. Nothing was committed or pushed.

## 5. Files

- `scripts/ce_interface_adjudication/v_screen_verify.py` - exclusion-set integrity and full C01 re-derivation
- `scripts/ce_interface_adjudication/v_screen_hidden.py` - independent tautomer/skeleton/same-formula recheck
- `scripts/ce_interface_adjudication/v_screen_partials.py` - C02/C03/C05/C06/C10/C11 re-derivation
- `scripts/ce_interface_adjudication/v_c01_peakcount.py` - header-only PK$NUM_PEAK census
- `artifacts/ce_interface_adjudication/screen/v_screen/v_part1.json` - exclusion integrity + C01 counts
- `artifacts/ce_interface_adjudication/screen/v_screen/v_hidden.json` - hidden-route recheck result
- `artifacts/ce_interface_adjudication/screen/v_screen/v_partials.json` - PARTIAL-candidate counts
- `artifacts/ce_interface_adjudication/screen/v_screen/v_c01_peakcounts.json` + `.csv` - peak census
- `artifacts/ce_interface_adjudication/screen/v_screen/v_c01_cand.csv` - 403 re-derived C01 candidates
- `artifacts/ce_interface_adjudication/screen/v_screen/v_c01_survivors_hidden.csv` - 112 survivors with all keys
- `artifacts/ce_interface_adjudication/screen/v_screen/v_massbank_trees_meta.json` - fetched tree metadata
