# S6-C06 screen: PharmMet DB parent drugs (Metabolomics Workbench ST003991, Jeon et al. 2025, PMC12923290)

Study: MURU collision-energy interface adjudication (outcome-blind). Task S6, candidate C06. Written 2026-09-15.
Metadata only. No spectra file was requested. No ICEBERG, GLACIER, FIORA or MURU prediction was run.

Status labels: VERIFIED = read in the stored file or recomputed here; INFERRED = reasoned from verified facts;
UNKNOWN = not decidable without spectra or further access.

Scripts: `scripts/ce_interface_adjudication/screen_c06_pharmmet.py` (first pass: DB precursor block, overlaps, tiers),
`scripts/ce_interface_adjudication/screen_c06_pharmmet_b.py` (second pass: paper supplementary table, the deposited
drugs with no DB row, union counts).
Outputs: `artifacts/ce_interface_adjudication/screen/c06_pharmmet/` (`c06_compounds_screen.csv`,
`c06_screen_summary.json`, `c06_addendum.json`, `c06_addendum_missing_precursors.csv`, `c06_deposited_union.csv`,
`downloads/`). Every transfer is a line of `artifacts/ce_interface_adjudication/downloads_register.jsonl` with task
`S6-C06` (13 lines from the first pass including one correction note, 2 from the second).

## 1. What the resource is (VERIFIED)

- Paper methods, `downloads/europepmc_PMC12923290_fullTextXML.xml`: "a Thermo Scientific Vanquish UHPLC coupled to a
  Thermo Scientific Orbitrap ID-X Tribrid mass spectrometer. MS1 spectra were acquired at 60,000 resolution with an m/z
  scan range of 100 to 1000, and MS2 spectra were acquired at 15,000 resolution with HCD 35%." Dual column, dual ESI:
  HILIC with positive ESI, C18 with negative ESI, 5 minute run per platform. 1114 therapeutic drugs incubated with
  pooled human liver S9 plus cofactors, sampled at 0 hr and 24 hr, duplicate incubations, one technical replicate each.
- Deposit, `downloads/mw_ST003991_summary.json`: study ST003991, 6,118 samples, submission 2025-06-19,
  release 2025-10-01, `"license":"CC BY 4.0"`. Analyses (`downloads/mw_ST003991_analysis.json`): AN006575 HILIC POSITIVE
  (Thermo IDX, Orbitrap, ESI), AN006576 HILIC NEGATIVE, AN006577 reversed phase POSITIVE, AN006578 reversed phase
  NEGATIVE.
- `downloads/mw_AN006575_mwtab.txt`: `ST:TOTAL_SUBJECTS 1132` (line 33), `MS:INSTRUMENT_NAME Thermo IDX` (6202),
  `MS:ION_MODE POSITIVE` (6205), `MS:MS_COMMENTS ddMSMS and MS1 data collection, mzmine2` (6206). The
  `MS_METABOLITE_DATA` block is a one-row placeholder ("Test"), so the mwTab carries no feature table.
- Archive listing, `downloads/mw_ST003991_archive_contents.html` (recomputed here): 12,236 file lines = 6,118 `.mzML`
  (24 GiB zip, 120.6 GB uncompressed) + 6,118 `.raw` (127 GiB zip, 196.2 GB uncompressed), **699 distinct PM ids**.
  By mode (raw): hilicpos 2,815, c18neg 2,815, c18pos 244, hilicneg 244. Seven PM ids carry suffixed repeat incubations
  (PM0000107, 204, 505, 816, 839, 899, 1001). So only 699 of the paper's 1114 drugs have deposited runs, each normally
  as 0 hr and 24 hr x 2 incubations x {HILIC ESI+, C18 ESI-}.
- Compound table: GitHub `ClinicalBiomarkersLaborabory/PharmMet`, commit `88eeb0a0`, `PharmMet_DB_v1.0.csv`,
  104,774,483 bytes. Only the leading precursor block was transferred (3 range reads, 786,432 bytes; rule
  `metaboliteID == precursorID`; 206 post-boundary rows checked, 0 stray precursor rows), giving **1,007 parent rows**
  with name, drug group and class, formula, SMILES, PubChem Parent ID and the MS1 feature list (adduct, m/z, RT, mode).
  Precursor ids run PM0000001 to PM0001123 with 116 ids absent from the block; metabolite ids start at PM0001124.
- Paper Supplemental Table 1 (`downloads/europepmc_PMC12923290_SupplementaryFiles.zip`, member `mmc1.xlsx`, 12,294 B)
  is a 12-row summary of drug classes, NOT a drug list. There is therefore no published per-drug list of the 1114; the
  only identity sources are the DB CSV and the mwTab sample-source names.

## 2. Identity coverage (VERIFIED)

- 1,007 DB parent rows parse to 987 unique MURU parent keys (rdkit 2026.03.5, `scaffold_key.py`), 0 unparsed SMILES,
  20 duplicate-key rows, 632 scaffold groups.
- mwTab subjects: 704 subject ids, 699 base PM ids, of which 659 have a DB parent row and **40 do not**. Those 40 were
  identified through PubChem by their mwTab sample-source name (`downloads/pubchem_missing_precursor_name_check.json`,
  40 requests): 39 resolved, 1 unresolved ("Gallamine triethyl"). The other 76 missing precursor ids have no deposited
  files, so the deposited set is fully enumerated: **699 deposited drugs, 698 identified (689 unique keys,
  477 scaffold groups)**.
- Identity checks: 25 random `Parent ID` values resolve as PubChem CIDs and 25/25 agree with the DB SMILES key
  (`downloads/pubchem_cid_sample_check.json`). Name route for all 204 DB-SMILES-novel parents
  (`downloads/pubchem_name_route_check.json`): 197 resolved, 9 where the name resolves to a different connectivity key
  than the DB SMILES, and 5 of those 9 names are in MassSpecGym 1.5. One defect read directly: PM0000264 "Cinnarazine"
  carries the enamine isomer `C1CN(CCN1C=CCC2=CC=CC=C2)C(c)c` (key SSKFWBSXNIWCBH), not cinnarizine
  (DERZBLKQOCDDDZ, which is in `exclusion/msg15_keys_all.txt`). DB SMILES novelty is therefore not automatically
  novelty; all headline counts below use the identity-robust filter (drop rows whose name route lands in
  MassSpecGym, whose name key contradicts the DB SMILES key, or whose DB name differs from the mwTab subject name).

## 3. Overlap with the exclusion inventory (deposited set, 689 keys; VERIFIED)

| Set | Keys of the deposited set present |
|---|---|
| MassSpecGym 1.5, all folds, recorded InChIKey14 | 545 |
| MassSpecGym 1.5, all folds, MURU parent key | 544 |
| MassSpecGym 1.5 train (DB-sourced 651 keys only) | 461 |
| MassSpecGym 1.5 simulation_challenge rows (ICEBERG msg_simulation universe) | 460 |
| MURU exposure registry (full, 31,507 keys) | 564 |
| MURU exposed populations (1,912 keys) | 135 |
| MURU V2 development population | 90 |
| MSnLib confirmation study 2 (PR #7) population | 1 |
| Comparator benchmark common population | 1 |
| MSnLib nine libraries | 587 |

Sequential exclusion of the deposited, identified set (each row adds one filter; keys / scaffold groups /
ring scaffold groups):

| Step | Keys | Groups | Ring groups |
|---|---|---|---|
| D0 deposited and identified | 689 | 477 | 436 |
| D1 minus MassSpecGym 1.5 all folds (both key routes) | 144 | 111 | 95 |
| D2 also minus MURU exposed populations + PR #7 + comparator, keys and scaffold groups | 80 | 78 | 62 |
| D3 also neutral parent with [M+H]+ inside the MS1 scan range 100-1000 (inside MURU 70.0-1042.6) | 60 | 60 | 49 |
| D4 also identity-robust (section 2) | **55** | **55** | 45 |
| D2f-D3f variant using the full MURU exposure registry instead of the exposed populations | 22 / 16 | 22 / 16 | 14 / 10 |

Of the 55 D4 compounds, 50 come from the DB (feature list available) and 26 of those 50 have a PharmMet MS1 `M+H`
feature in hilicpos; the remaining 5 come from the PubChem name route and have no DB feature list. The D4 [M+H]+ range
is 100.05 to 812.48, i.e. 7.0 to 56.9 eV under the documented eV = NCE x precursor_mz / 500 mapping against a constant
35 under raw NCE. Every D4 scaffold group is a singleton.

The 40 deposited drugs that have no DB row add at most 5 compounds to D3 (Mechlorethamine, Phensuximide, Pipobroman,
Prulifloxacin, Trichlormethine; one of their scaffold groups already appears in the DB block); 12 of the 39 resolved are
absent from MassSpecGym, 8 survive the MURU/PR7/comparator filters, 5 survive the range and availability filters.

## 4. Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Absent from MURU development | NOT_MET dataset-wide, MET for the residual | 90 of 689 deposited keys are in the V2 development population, 135 in the exposed populations, 564 in the full registry; D2 onwards removes them by key and by scaffold group |
| 2 | Absent from the PR #7 confirmation population | MET after one exclusion | exactly 1 deposited key in `msnlib_study2_population_keys.txt` |
| 3 | Absent from the comparator benchmark population | MET after one exclusion | exactly 1 deposited key in `comparator_common_population_keys.txt` |
| 4 | Absent from ICEBERG/GLACIER training (MassSpecGym 1.5, all folds, InChIKey14) | PARTIAL | 545 of 689 deposited keys are in MassSpecGym 1.5 (79%); only 144 are not, 55 after the other exclusions and the identity-robust filter; the 5 name-route defects show the residual is fragile |
| 5 | Known CE semantics | PARTIAL | paper: "MS2 spectra were acquired at 15,000 resolution with HCD 35%"; mwTab: "ddMSMS"; the word "normalized" appears nowhere, the percent unit implies Thermo normalized collision energy (INFERRED); fixed vs stepped/assisted and the per-scan value are UNKNOWN without the raw/mzML headers |
| 6 | [M+H]+ positive mode available | PARTIAL | HILIC ESI+ (AN006575) for all 699 deposited drugs, 2,815 raw files; the DB feature table lists an `M+H` hilicpos feature for 477 of 634 in-range deposited parents; whether a ddMS2 was triggered on the parent [M+H]+ in any given run is UNKNOWN without spectra |
| 7 | Compatible fragmentation/instrument metadata | PARTIAL | Orbitrap HCD beam-type on an ID-X Tribrid maps to the ms-pred token `"Orbitrap"` (`src/ms_pred/common/chem_utils.py:277-282`: Orbitrap 0 = Orbitrap HCD, QTOF 1, IT-FT 2 = Orbitrap CID, Unknown 3) and matches MURU's claim scope (Orbitrap HCD, fixed NCE, [M+H]+). Not compatible or unverifiable: NCE 35 is neither frozen external rung (MURU uses fixed NCE 20 and 60 through the A0 map, P5 section 4); the C18 channel is negative ESI only and MURU is positive only; samples are S9 incubation matrices with cofactors rather than injected standards, so MURU's isolation-purity rule (no co-injected ion within 0.7 m/z, `msnlib_design.py:26-29`) cannot be evaluated from metadata and DDA co-isolation is likely; 24 hr runs contain metabolites of the same parent, so only 0 hr runs are clean |
| 8 | Multiple energies per compound | NOT_MET | one energy, HCD 35%, no ladder; no stepped-energy statement |
| 9 | Structural diversity and scaffold count after exclusions | 55 keys in 55 singleton scaffold groups (45 ring scaffolds), 16 under the conservative full-registry exclusion | section 3 table |
| 10 | License and access | PARTIAL | MW deposit "CC BY 4.0" with open zip download (`mw_ST003991_summary.json`); paper CC BY-NC-ND 4.0 (Europe PMC XML); the GitHub compound table has NO license (`gh api repos/ClinicalBiomarkersLaborabory/PharmMet` -> `"license":null`, `/license` -> 404), so reuse terms for the identity table itself are unspecified; using it requires a 24 GiB (mzML) or 127 GiB (raw) download |
| 11 | Hidden MassSpecGym inclusion under a different identifier | PARTIAL, low for spectra and material for identity | the deposit is raw and mzML LC-MS runs on Metabolomics Workbench, not a library submission to MassBank, MoNA, GNPS or MSnLib, which are MassSpecGym's only sources (P5 section 3.3 from the construction notebooks); timing does not exclude it, since `MassSpecGym1.5.tsv` was uploaded 2026-05-07 (HF commit a2c04a24) after the 2025-10-01 MW release; the measured risk is identity-level, not source-level: 5 of 204 checked novel parents are in MassSpecGym under their name and one DB SMILES is a wrong isomer |

## 5. Verdict

PARTIAL_OR_SUPPORTING_ONLY. Not suitable as the Design A evaluation set: criteria 1 and 4 hold only for a residual of
55 compounds, criteria 5, 6, 7 are partial, criterion 8 fails outright, and 55 singleton scaffolds at one energy cannot
carry a scaffold-split calibration plus a held-out evaluation. It retains a specific supporting value: a single fixed
HCD 35% over [M+H]+ 100 to 1000 on the ID-X Tribrid (the MSnLib instrument class) separates raw NCE 35 from
35 x m/z / 500 by 7 to 57 eV, and the 545 deposited drugs that ARE in MassSpecGym make it usable as an in-training
consistency probe rather than an independent evaluation. Any use is gated on two facts that need the spectra
(criterion 5 and 6): whether the per-scan HCD value is normalized and constant, and whether the parent [M+H]+ is
actually selected for ddMS2 in the 0 hr HILIC ESI+ runs.

## 6. Open items and cautions

- UNKNOWN without spectra: per-scan collision energy semantics, stepped/assisted flag, isolation width, DDA trigger on
  the parent, co-isolation purity, whether MS2 exists for the D4 compounds at all.
- The DB CSV was read only up to the end of its leading precursor block. 116 precursor ids never appear there; 40 of
  them are covered by the mwTab route, the other 76 have no deposited runs and remain unidentified. Reading the whole
  104.8 MB file (above this study's ~50 MB cap) would settle the count against the paper's 1114.
- `positive_mode_deposited_no_exclusions` in `c06_screen_summary.json` (634 rows, 627 keys, 438 groups) is the
  deposited, in-range set BEFORE any exclusion; do not confuse it with D3/D4.
- The first-pass summary also reports T- and M-tier counts computed on all 1,007 DB rows; the section 3 table is the
  corrected, deposited-set version and supersedes them for reporting.
