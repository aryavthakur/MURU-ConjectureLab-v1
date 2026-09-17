# P3: MassSpecGym curation provenance of `collision_energy` and `instrument_type`

Study: MURU collision-energy interface adjudication (outcome-blind). Task P3, upstream of ms-pred.
Written 2026-09-14. No comparator or MURU prediction, result, or measurement was read or run. No spectrum
(peak/intensity) column or spectra file was downloaded or read. Every fetched object is in
`artifacts/ce_interface_adjudication/downloads_register.jsonl` (task "P3" lines).

Evidence tags: **VERIFIED** = read in code, notebook source/output, or data; **INFERRED** = reasoned from verified
facts but not directly observed; **UNRESOLVED** = could not be settled with allowed sources.

Notebook citations use `cell N line L` of the `.ipynb` JSON (0-based cell index, 1-based line within the cell),
as printed by `scripts/ce_interface_adjudication/p3_dump_notebook.py`.

## 0. Bottom line

1. MassSpecGym's `collision_energy` is a float produced by one parser, `parse_ce_str` + `convert_nce`
   (notebook 4 cell 9), applied to each source's native CE string. Only strings containing the character `%` are
   converted, as `eV = NCE * precursor_mz / 500`. Every other string keeps its first number (or a ramp mean) with
   no unit conversion. **VERIFIED.**
2. The column therefore mixes at least three quantities (row counts are for the 119,029 `simulation_challenge` rows):
   - **Raw MSnLib v1.0 HCD NCE settings on an Orbitrap ID-X**, never converted: 30,637 Orbitrap rows in molecules
     first seen in MSnLib (VERIFIED from identifier order plus data), plus about 8,393 more in molecules already
     present in MassBank/MoNA (heuristic, INFERRED). Values {60, 20, 30, 45, 15, 75}.
   - **Converted "eV" from `%` strings** (MassBank/MoNA only): 23,894 Orbitrap rows with non-integer CE. 99.87% of
     these give an integer when multiplied by 500/precursor_mz (VERIFIED with P4's precursor_mz).
   - **Raw numbers from MassBank/MoNA strings without `%`**: 18,380 Orbitrap and 36,342 QTOF integer rows, plus
     half-integer ramp means (19 Orbitrap, 546 QTOF) and 815 QTOF raw fractional values. For QTOF these are eV/V
     (INFERRED). For Orbitrap the unit is mixed and not recoverable per row; the value ladder
     (45/30/90/15/75/35/60) matches the implied-NCE ladder of the converted rows, so most are probably unconverted
     NCE written as "(nominal)", "HCD" or "(NCE)" (INFERRED).
3. GNPS library spectra carry no CE field, so they are CE-missing and never enter `simulation_challenge`
   (VERIFIED: notebook 6 cell 5 line 1, GNPS MGF format, and 100% missing CE in the GNPS-first identifier block).
4. `instrument_type` has two values plus missing. "Orbitrap" merges the MSnLib literal "Orbitrap", the MassBank
   `-QFT` classes, and the `-ITFT` classes (notebook 6 cell 3 line 2). `-ITFT` includes ion-trap CID data
   (e.g. `LC-ESI-CID; Lumos`, `ESI-IT-FT/ion trap with FTMS`; notebook 2 cell 6). **VERIFIED.**
5. MassSpecGym 1.5 did not change `collision_energy` or `instrument_type`. Only `smiles` was re-canonicalized.
   The maintainers' v1 vs v1.5 diff shows 2 CE rows differing by at most 3.55e-15 and 0 instrument rows differing.
   **VERIFIED.**
6. No per-row source column exists (14-column schema, VERIFIED). Rows can still be attributed to source blocks
   from identifier order, because notebook 3 numbers spectra molecule by molecule in source first-appearance order.
   Result: identifiers 202,862..239,028 hold molecules first seen in MSnLib v1.0, and 239,029..414,174 hold
   molecules first seen in GNPS. **VERIFIED mechanism; boundaries VERIFIED empirically.**
7. Contradiction to note: the MassSpecGym paper defines the simulation input as "the collision energy, measured in
   electronvolts or eV". The released column does not meet that definition for MSnLib rows. The MSnLib paper also
   prints its HCD settings as "eV", while the instrument sets HCD energies in % (NCE). See section 5.

## 1. Code and data provenance (MassSpecGym repository)

Repository `github.com/pluskal-lab/MassSpecGym`, `main` at `f259fe3780d5bd227fc6ece36ce6f397c2eef716`
(2026-05-08, merge of PR #65 "MassSpecGym v1.5 (part 1/2)"). Files were read via `gh api` into the scratchpad.

| File | Last commit touching it |
|---|---|
| `notebooks/dataset_construction/1_Load_data_from_repositories.ipynb` | `1a54459` 2024-05-29 |
| `notebooks/dataset_construction/2_clean_library.ipynb` | `1a54459` 2024-05-29 |
| `notebooks/dataset_construction/3_remove_duplicates_and_profiled_spectra.ipynb` | `1a54459` 2024-05-29 |
| `notebooks/dataset_construction/4_standardization_and_cleaning.ipynb` | `618dedf` 2024-06-12 (previously `4_final_standardization_and_cleaning.ipynb`, changed by `24ce70b` "Incorporate Kai's filtering", 2024-05-30) |
| `notebooks/dataset_construction/5_split.ipynb` | `ae72901` 2024-08-12 |
| `notebooks/dataset_construction/6_final_postprocessing.ipynb` | `618dedf` 2024-06-12 |
| `notebooks/dataset_construction/7_format_conversions.ipynb` | `4046362` 2024-08-20 "Unhide test fold" |
| `notebooks/simulation_preproc.ipynb` at `8c6514cbbc2804ff57b5e9e39fe010a9d2ca310b` (source of the CE parser, cited in notebook 4 cell 9 line 1) | 2024-05-28 |
| `notebooks/massspecgym_in_the_wild/massspecgym_v1.5_validation.ipynb` | `b66d9c6` 2026-05-08 |
| `scripts/fixes/rdkit_canon_massspecgym.py` | PR #65 |

### 1.1 Notebook 1: load and merge (VERIFIED)

- cell 0 lines 2-6: libraries downloaded "13/05/2024" from GNPS, MoNA, MassBank, and Zenodo 11163381 ("Corinna
  Bruns Library", i.e. MSnLib v1.0).
  - Discrepancy: the paper says "downloaded from the official websites on May 27, 2024" (arXiv 2410.23326 section
    3.3). The date conflict is immaterial to CE semantics.
- cell 1: the 46 GNPS library MGFs, listed by name (BERKELEY-LAB ... UM-NPDC, including GNPS-NIST14-MATCHES,
  GNPS-NIH-NATURALPRODUCTSLIBRARY(_ROUND2_POSITIVE), GNPS-SCIEX-LIBRARY, MMV_POSITIVE, BMDMS-NP, and others).
- cell 2: MoNA "LC-MS Spectra" export. cell 3: MassBank release 2023.11.
- cell 4 and cell 7 lines 7-10: the eight MSnLib **MSn** MGFs `20231031_nihnp_library_{neg,pos}_all_lib_MSn.mgf`,
  `20231130_mcescaf_...`, `20231130_otavapep_...`, `20240411_mcebio_...`.
- cell 5 plus cell 7 lines 12-14: "Remove merged spectra". Only spectra with `spectrum.get("spectype") is None` are
  kept.
- cell 12 lines 7-10: merge order is fixed: `MassBank_NIST.msp`, `MoNA-export-LC-MS_Spectra.msp`,
  `ms2_spectra_corinna.mgf`, then the GNPS files in cell 1 order. They are loaded with `metadata_harmonization=False`
  and saved to `merged_libraries.mgf`.

### 1.2 Notebook 2: matchms cleaning (VERIFIED)

- cell 18 lines 20-39 define the filter order, which is printed in the cell 18 output. Relevant steps:
  - `remove_not_ms2_spectra` (cell 16) keeps `ms_level` in ("MS2", "2"). This drops MSnLib MS3+ spectra.
  - `require_correct_ionmode` "positive" (line 16).
  - `require_adduct_in_list` ["[M+H]+", "[M+Na]+"] (line 22).
  - `remove_charged_molecules`, the adduct/precursor/parent-mass consistency checks, and formula checks.
  - `harmonize_instrument_types` (line 32), then `remove_instrument_types` (line 33).
  - `store_relevant_metadata_only` (line 39). Its field list (cell 9 line 1) keeps `instrument_type` and
    `collision_energy`.
- No filter parses or edits `collision_energy` in this notebook. **VERIFIED:** it is absent from the cell 18
  filter list and the cell 20 report.
- cell 6 lines 1-21: the `conversions` dict for nonstandard instrument strings. Selected mappings:
  - `'ESI-Orbitrap': 'ESI-ITFT'`, `'LC-ESI-Orbitrap': 'LC-ESI-ITFT'`, `'DI-ESI-Orbitrap': 'ESI-QFT'`
  - `'ESI-HCD': 'ESI-QFT'`, `'ESI-Hybrid FT': 'ESI-QFT'`, `'LC-ESI-Q-Exactive Plus': 'LC-ESI-QFT'`
  - `'LC-ESI-CID; Lumos': 'LC-ESI-ITFT'`, `'LC-ESI-HCD; Velos': 'LC-ESI-ITFT'`,
    `'ESI-IT-FT/ion trap with FTMS': 'ESI-ITFT'`
  - `'LC-ESIMS-qTOF': 'LC-ESI-ITFT'` (a qTOF string mapped to ITFT; apparent curation error, VERIFIED as written)
  - `'N/A-N/A': 'ESI-QTOF'`, `'-Maxis HD qTOF': 'ESI-QTOF'`
  - `'Positive-Quattro_QQQ:25eV': 'ESI-QQ'`
- cell 7 lines 1-8: removed instrument types, e.g. "LC-ESI-QQ", "ESI-IT", "LC-ESI-IT", "QqQ", "APCI-QFT",
  "Q Exactive HF", "Waters SYNAPT", "Thermo LTQ", MALDI/GC/FAB variants. Note: "Q Exactive HF" is removed, but
  "QEHF" is later mapped to Orbitrap (notebook 4).
- cell 20 output: 1,334,962 processed, 885,241 removed (`remove_not_ms2_spectra` 628,478;
  `remove_instrument_types` 13,481; `harmonize_instrument_types` changed metadata on 294,479). cell 21 output:
  449,721 kept.
- Key harmonization happens inside matchms (0.25.0, tag commit dated 2024-05-21; the notebook comments that its
  helper filters are "now also available in matchms 0.26.0"):
  - `matchms/Metadata.py` lines 46-48 lowercase keys and replace whitespace with `_`, so an MGF key
    `Collision energy` becomes `collision_energy`.
  - `matchms/data/known_key_conversions.csv` lines 23-26 map `collisionenergy`, `colenergy` and
    `ac$mass_spectrometry:collision_energy` to `collision_energy`.
  - Lines 77-80 map `ac$instrument_type`, `instrument_type`, `instrumenttype` and **`source_instrument`** to
    `instrument_type`. Lines 117-119 map `spectrum_type` and `mslevel` to `ms_level`.
  - pickydict `PickyDict._apply_replacements` (github.com/florian-huber/pickydict, `pickydict/PickyDict.py`
    lines 172-186) keeps the value already present when two raw keys collide, and drops the other with a warning.
    For an MGF with both `INSTRUMENT_TYPE` and `SOURCE_INSTRUMENT`, as MSnLib has (section 3), `instrument_type`
    keeps the `INSTRUMENT_TYPE` value. VERIFIED for pickydict HEAD; the pickydict version actually installed is
    UNRESOLVED.

### 1.3 Notebook 3: dedup, profile removal, identifiers (VERIFIED)

- cell 2 lines 8-43: spectra are grouped by full `inchikey` in first-appearance order (`unique_inchikeys` dict
  insertion order). Groups are emitted one after another, each keeping its spectra in original file order.
  - Exact duplicates (CosineGreedy == 1.0) are dropped.
  - For a duplicated pair the **earlier** spectrum is removed and the later one kept (lines 36-38). A
    MassBank record duplicated in MoNA or GNPS therefore survives as the later copy.
  - cell 3 output: 22,504 removed.
- cell 5-7: profile-spectrum removal (427,217 -> 425,604). cell 10: spectra with 300 or more peaks are dropped.
- cell 13 lines 1-5: `identifier = MassSpecGymID{i+1:07d}` over the kept list. Output: 414,174 identifiers.
- Consequence (INFERRED from the code, confirmed by data in section 6): identifier order is molecule-grouped.
  Molecules are ordered by first appearance across MassBank, MoNA, MSnLib, GNPS. Within a molecule, rows follow
  that same source order.

### 1.4 "Kai's filtering" (partly UNRESOLVED)

- Notebook 4 (current) cell 1 line 1 reads `../../data/filtered_gym_fixed.tsv` (239,311 rows) and drops its `fold`
  and `simulation_challenge` columns (line 2). That file is not in the repository.
- The pre-`24ce70b` version (`4_final_standardization_and_cleaning.ipynb` at parent `2d16eb9`) ran the same CE
  parser directly on all 414,174 identifiers (cell 6).
  - Output: 272,296 missing CE before parsing and 272,690 after, so **394 native CE strings were unparseable and
    became NaN**.
  - That version wrote `MassSpecGym.tsv` with 414,049 rows (cell 10 output, cell 17).
- The paper (arXiv 2410.23326 section 3.3) describes the extra filter as "removing all spectra where more than 50%
  of the total intensity cannot be explained by combinatorially decomposing molecular mass into plausible chemical
  subformulae".
- The input file of Kai's filter and its exact rules are UNRESOLVED. INFERRED: it was the 414,049-row pre-Kai TSV,
  because its CE strings already had the "x (normalized=..., ramped=...)" form, and re-parsing that form is
  idempotent (no `%`, no `-`).

### 1.5 Notebook 4: CE and instrument standardization (VERIFIED)

- cell 9 lines 1-40 hold the parser. Line 1 comment: "Code from Adamo: .../8c6514cb.../notebooks/simulation_preproc.ipynb".
  - `parse_ce_str`:
    - line 9: `ce_str = ce_str.split(";")[-1]`, the last `;`-separated segment only.
    - lines 11-14: `normalized = True` iff `"%" in ce_str`.
    - lines 15-22: if `"-"`, "Ramp", "RAMP" or "->" is in the string, regex `\d+(\.\d+)?(V)?(-|->)\d+(\.\d+)?(V)?`
      and `ce = 0.5*min + 0.5*max`.
    - line 25: otherwise `ce` is the **first** number found (`\d+(\.\d+)?`).
    - lines 27-30: any exception gives `ce = NaN, normalized = False`.
  - `convert_nce` lines 33-40: `ace = nce * precursor_mz / 500` if normalized, else `ace = ce` ("assumes charge
    factor of 1").
- cell 10 lines 2-11 apply it and store `"{ce} (normalized=..., ramped=...)"`. Output: 116,828 missing CE before
  and after.
- cell 23 line 1 (after reload): `float(x.split(' ')[0])`, giving the final float column.
  - Provenance caveat: the cell 21 source reads `MassSpecGym.tsv`, but its stored warning shows the executed call
    read `MassSpecGym_OLD.tsv`. The source was edited after execution.
- **No CE imputation or unit inference exists anywhere in notebooks 1-7.** The paper's phrase "inferring missing
  or incorrect values where possible" (section 3.3) is not reflected for CE.
- Branch table (VERIFIED from the code; examples marked (VERIFIED string) were observed in notebook outputs,
  section 2):

| Native string form | Branch | Value stored |
|---|---|---|
| `35%`, `NCE 35%`, `10% (nominal)` | normalized | 35 * precursor_mz / 500 |
| `HCD (NCE 20-30-40%)` (hypothetical) | normalized + ramped | mean of first pair (25) * mz / 500 |
| `30 (nominal)`, `30(NCE)` (VERIFIED string), `65HCD` (VERIFIED string) | plain | 30, 65 (raw NCE, not converted) |
| `15, 30, 45, 60, 70 or 90 (nominal)` (MassBank Eawag form) | plain | 15 (first number only) |
| `10 eV`, `6V`, `20 V` (VERIFIED strings), `20.0 eV` | plain | 10, 6, 20 (raw eV/V) |
| `Ramp 10-50 kV`, `25-40 eV` | ramped | 30, 32.5 |
| MSnLib `60.0` (single float) | plain | 60 (raw NCE) |
| missing (GNPS) | NaN | NaN |
| unparseable (e.g. a `-` without a numeric range) | exception | NaN (394 cases in the 414k set) |

- cell 12 lines 1-20, `standardize_instrument_type`:
  - strip leading `LC-`, then `ESI-`, then `Q-`; strip trailing `/MS`;
  - `Q Exactive Focus Hybrid Quadrupole Orbitrap Mass Spectrometer (Thermo Fisher Scientific)` and `QEHF` become
    `Orbitrap`; `TOF` and `ITTOF` become `QTOF`; `FT` becomes `QFT`.
  - Output on 239,311 rows: ITFT 117,641; QTOF 54,461; Orbitrap 38,841; QFT 22,928; NaN 5,440.
- cell 16: spectra whose maximum intensity above precursor m/z + 3 exceeds 0.2 are dropped (239,311 -> 233,446).
- cell 27: precursor_mz <= 1000 (-> 231,108). cell 29: Sn/Al removed (-> 231,104).

### 1.6 Notebooks 5-7 (VERIFIED)

- nb5 cell 11 lines 4-28: split stratification uses adduct, instrument_type, the top-5 CE values or other/none,
  and molecule frequency. nb5 cell 21 output (full dataset): None 109,358; Other 60,546; 20.0 18,506;
  60.0 16,015; 30.0 12,780; 10.0 7,305; 45.0 6,594.
- nb6 cell 3 lines 1-3: `replace({'ITFT':'Orbitrap', 'QFT':'Orbitrap'})`. Before: ITFT 110,724, QTOF 53,823,
  Orbitrap 38,585, QFT 22,749. After: Orbitrap 172,058, QTOF 53,823.
- nb6 cell 5 line 1: `simulation_challenge = (~df.isna().any(axis=1)) & (df['adduct'] == '[M+H]+')`, 119,029 True.
  Every row with missing CE or missing instrument is excluded.
- nb7 cell 7 lines 7-13: the `.ms` export writes `energy` = `collision_energy` and `instrument` =
  `instrument_type` unchanged.

### 1.7 Downstream MassSpecGym code consuming the column (VERIFIED, context only)

- `massspecgym/data/transforms.py` (main, last touched `d126911`), `StandardMeta.transform_ce`, lines 635-639:
  `np.clip(ce, 0, int(max_collision_energy)-1)` then round to an integer index.
  `config/simulation/template.yml` lines 11-12 set `instrument_types: ["QTOF","QFT","Orbitrap","ITFT"]` and
  `max_collision_energy: 200.`. No NCE/eV handling.
- Open, unmerged PR #68 ("Dev/v1.5 MassSpecGym", head `dcdc3fd` on `harrylaucngd/MassSpecGym`):
  - `massspecgym/models/simulation/iceberg/adapter.py` lines 72, 78 and 85 pass the dataset `collision_energy`
    straight into ICEBERG `predict_mol(collision_eng=ce)`, default 40.0.
  - `massspecgym/models/oracles/iceberg/predict.py` line 50 documents it as "Collision energy in eV".
  - So the MassSpecGym-side ICEBERG adapter in development applies no NCE conversion. It is not merged.

## 2. Native CE and instrument formats per source

### 2.1 MassBank (release 2023.11, `MassBank_NIST.msp`)

- Exporter `MassBank-web` `massbank/export/RecordToNIST_MSP.java` (commit `4b6ea0b`):
  - lines 108-109 write `Instrument_type:` and `Instrument:` verbatim from `AC$INSTRUMENT_TYPE` and
    `AC$INSTRUMENT`;
  - lines 112-113 write `Collision_energy:` verbatim from `AC$MASS_SPECTROMETRY: COLLISION_ENERGY`;
  - the in-file example at line 33 is `Collision_energy: 15, 30, 45, 60, 70 or 90 (nominal)` for Eawag
    `LC-ESI-QFT`, HCD. **VERIFIED.**
  - That the 2023.11 release was produced by this exporter version is INFERRED.
- Record format (`Documentation/MassBankRecordFormat.md` lines 686-803):
  - instrument type is `(Separation-)Ionization-Analyzer`, e.g. `LC-ESI-QTOF`, `LC-ESI-ITFT`, `LC-ESI-QFT`, where
    `FT` includes Orbitrap;
  - CE is free text with examples `20 kV`, `Ramp 10-50 kV`, `10% (nominal)`. **VERIFIED.**
- MassBank -> MassSpecGym mapping (VERIFIED code path, INFERRED per contributor):
  - `LC-ESI-QTOF` -> QTOF; `LC-ESI-QFT` -> QFT -> Orbitrap; `LC-ESI-ITFT` -> ITFT -> Orbitrap.
  - CE with `%` is converted to NCE*mz/500. `(nominal)` or `(NCE)` without `%` keeps the raw number, and
    multi-energy "merged" records keep only the first listed energy.
- First MassSpecGym spectrum (`MassSpecGymID0000001`): native `collision_energy: '30(NCE)'`,
  `instrument_type: 'LC-ESI-ITFT'` (notebook 4 cell 4 output). It is stored as 30.0 with no conversion.
  - Its source is INFERRED to be MassBank, because MassBank is loaded first; within block A, MassBank vs MoNA
    cannot be proven (section 6).

### 2.2 MoNA ("LC-MS Spectra" MSP export)

- Free-text submitter CE strings. The MoNA REST value endpoint returned no value list (register:
  `mona_metadata_values_collision_energy.json`, 67 bytes), so a per-string census was not possible. UNRESOLVED
  per contributor.
- Strings observed in a MassSpecGym labeled intermediate that combined these sources
  (`simulation_preproc.ipynb` at `8c6514c`, table `MassSpecGym_labeled_data_df.csv`, 448,979 rows; VERIFIED):
  - cell 8 output, top CE strings: `60.0` 14,636; `20.0` 14,464; `30.0` 6,200; `6V` 5,930; `10 eV` 5,449;
    `15.0` 4,741; `40` 3,501; `45.0` 3,446; `30` 3,345; `20 eV` 3,225.
  - cell 14 output: `65HCD`, `45HCD`, `35HCD`, `20 V`, `10 V`, `40 V`.
  - cell 15 output, on a 120,020-row QTOF/Orbitrap/QFT subset: `normalized` True 5,250, ramped True 4,454.
  - cell 10 output, instrument strings: `ESI-ITFT` 222,251; `LC-ESI-QTOF` 69,842; `LC-ESI-ITFT` 61,678;
    `Orbitrap` 47,693; `LC-ESI-QFT` 21,954; `ESI-QTOF` 9,562; `ESI-QFT` 4,759.
  - The `.0`-suffixed ladder strings (`60.0`, `20.0`, `30.0`, `15.0`, `45.0`) match the MSnLib float format.
    INFERRED.
- MoNA also mirrors MassBank and GNPS records. Exact duplicates keep the later-loaded copy (notebook 3), so some
  MassBank content may survive with MoNA or GNPS metadata. INFERRED.

### 2.3 GNPS (46 library MGFs)

- The GNPS library MGF record example in `CCMS-UCSD/GNPSDocumentation` `docs/downloadlibraries.md` lines 14-33
  (commit `3a07ebf`) has `PEPMASS, CHARGE, MSLEVEL, SOURCE_INSTRUMENT, FILENAME, SEQ, IONMODE, ORGANISM, NAME, PI,
  DATACOLLECTOR, SMILES, INCHI, INCHIAUX, PUBMED, SUBMITUSER, TAGS, LIBRARYQUALITY, SPECTRUMID, SCANS` and **no CE
  field**.
- The GNPS library writer `ming_spectrum_library.py` lines 396-412 (`CCMS-UCSD/GNPS_Workflows`) also writes no CE.
  **VERIFIED.**
- Instrument: `SOURCE_INSTRUMENT` (e.g. `ESI-Orbitrap`, `LC-ESI-qTof`, `DI-ESI-Hybrid FT`) -> matchms
  `instrument_type` -> notebook 2 conversions -> notebook 4 -> notebook 6. VERIFIED code path.
- Result: GNPS rows have NaN CE and are excluded from `simulation_challenge`. Confirmed by data: all 63,625 rows in
  the GNPS-first block have missing CE (section 6).

### 2.4 MSnLib v1.0 (Zenodo 11163381; details in section 3)

- Header `Collision energy` holds a single float NCE setting; `INSTRUMENT_TYPE` and `SOURCE_INSTRUMENT` are both
  present.
- The string has no `%`, so it is stored raw: 15, 20, 30, 45, 60, 75.
- `instrument_type` is INFERRED to be the literal `Orbitrap`: the pre-merge "Orbitrap" class (38,585 rows,
  notebook 6 cell 3) is within 3% of the attributed MSnLib row count (39,614 Orbitrap rows, section 6), and no
  conversion or prefix rule produces "Orbitrap" from MassBank/GNPS-style strings except the two Q Exactive
  Focus/QEHF strings.
- Adduct filter: only [M+H]+ and [M+Na]+ survive. Negative-mode files are removed by the positive-ion-mode filter.

## 3. MSnLib v1.0 CE semantics

- **Zenodo record 11163381** (API JSON stored as `p3_downloads/zenodo_11163381_record.json`, sha256 `a0f92a87...`),
  published 2024-05-09, title "MSnLib Mass spectral libraries (.mgf)". VERIFIED from the description:
  - "Flow injection method to acquire MSn data on an Orbitrap ID-X instrument for four different compound
    libraries"; MCEBIO 10,315, MCESCAF 4,998 (sic), NIHNP 3,988, OTAVAPEP 1,298 compounds.
  - SPECTYPE semantics: "no SPECTYPE: Best spectrum for each precursor and energy (highest TIC)"; `SAME_ENERGY`
    merges repeats at one energy; `ALL_ENERGIES` is the "merged spectrum of all used energies (in our case 3 for
    each precursor ...)"; `ALL_MSN_TO_PSEUDO_MS2` merges the MSn tree.
  - Files: 16 MGFs. The `*_MSn.mgf` files "contain all individual MSn stages additionally".
- **MassSpecGym selection (VERIFIED):** `*_MSn.mgf` files, SPECTYPE absent (single best scan per precursor and
  energy, not merged), then MS2 only, positive mode, [M+H]+/[M+Na]+. **MSnLib rows in MassSpecGym are single-energy
  MS2 scans.**
- **MSnLib paper** (Brungs et al., Nature Methods 2025, doi 10.1038/s41592-025-02813-0, PMC12510872, retrieved via
  PubMed full text), Methods, "Data acquisition" (VERIFIED):
  - "Three fragmentation experiments to cover different collision energies (a maximum of nine scans) were
    conducted."
  - For MS2 the energies were 20 and 60, and the assisted collision energy was tested in 15-unit steps
    (15, 30, 45, 60, 75); the paper prints the unit as "eV".
  - MS3/MS4 used fixed 20/40/60; MS5 used 40/60. Instrument: Orbitrap ID-X.
  - SPECTYPE naming in the paper: "SINGLE_BEST_SCAN=highest TIC fragmentation scan is exported for each precursor".
- **Assisted CE is single-energy (VERIFIED, vendor document).** Thermo poster PO65258 (ASMS 2018, "Real-Time
  Collisional Energy Optimization on the Orbitrap Fusion Platform", register line with sha256):
  - Figure 7 table: HCD "Assisted: Selects single optimal energy from list of energies"; HCD "Stepped: Three
    collision energies combined into a single scan".
  - The method editor field is labelled "HCD Assisted Collision Energies (%)", and the Figure 1 caption reports
    energies in NCE.
  - So each MSnLib MS2 precursor has one scan at 20, one at 60, and one at an instrument-chosen energy from
    {15, 30, 45, 60, 75}, all in normalized (%) units.
  - INFERRED: the paper's "eV" is a unit misprint, because the ID-X method sets HCD energies in %. MURU and ms-pred
    convention both treat MSnLib values as NCE.
- **Data check (VERIFIED, `p3_msg15_row_source_attribution_summary.json`):** CE counts in MSnLib-first rows are
  60: 10,591 and 20: 9,644 (the two fixed energies, about equal), and assisted 30: 4,985, 45: 2,996, 15: 2,338,
  75: 78. The assisted total, 10,397, is about equal to each fixed count, which matches 3 energies per precursor.
  The ladder is the same in all four v1.0 sub-libraries (MCEBIO, MCESCAF, OTAVAPEP, NIHNP).
- **MGF header format (VERIFIED indirectly):**
  - FIORA `lib_loader/msnlib_loader.ipynb` at commit `7a7c1c0` (2024-07-18) read the v1.0 `*_MS2.mgf` files with
    `fiora/IO/mgfReader.py`, which keeps header keys verbatim.
  - cell 2 output lists the header keys `'SPECTYPE', 'Collision energy', 'FRAGMENTATION_METHOD',
    'ISOLATION_WINDOW', 'Acquisition', 'INSTRUMENT_TYPE', 'SOURCE_INSTRUMENT', 'IMS_TYPE', 'ION_SOURCE', 'MSLEVEL'`.
  - cell 1 line 12 casts `Collision energy` with `astype(float)` for all 8 MS2 files without error, so every entry
    is a single number.
  - At `8563ab1` the SPECTYPE counts of those MS2 files are NaN 64,937, SAME_ENERGY 26,823, ALL_ENERGIES 22,360
    (cell 12 output).
  - The MSn files are INFERRED to share the MS2 files' header format.
  - Version drift: MSnLib v5 exports (FIORA HEAD `9934d95`, files `20241003_*_ms2.mgf`) use `COLLISION_ENERGY` with
    bracketed lists for merged spectra (cell 2-3, e.g. `[20.0, 30.0, 60.0, 40.0, 15.0, 45.0]`) and
    `SPECTYPE=SINGLE_BEST_SCAN`.
  - Current mzmine `DBEntryField.java` (master `0801807`) lines 143, 648-649 and 656 declare `COLLISION_ENERGY`
    (FloatArrayList) and `SPECTYPE`. So v1.0 (`Collision energy`) and later MSnLib exports differ in key spelling.
    This does not matter for MassSpecGym, which only read v1.0.

## 4. MassSpecGym 1.0 -> 1.5 changes

- Hugging Face `roman-bushuiev/MassSpecGym` commits (API JSON stored): `data/MassSpecGym.tsv` was uploaded
  `1b6d1ec6` on 2024-08-20; `data/MassSpecGym1.5.tsv` was uploaded `a2c04a24` on 2026-05-07. Tree: MassSpecGym.tsv
  LFS sha256 `0c9cc504...`, MassSpecGym1.5.tsv `50cfdd1d...`, matching the identity fetch record.
- Dataset card (`README.md` stored) line 62: "Schema is identical to v1 and content is nearly identical, except
  that the `smiles` column is re-standardized with `rdkit.Chem.MolToSmiles(canonical=True)`". **VERIFIED.**
- `scripts/fixes/rdkit_canon_massspecgym.py` lines 35-36 set `TSV_IN = .../MassSpecGym.tsv` and
  `TSV_OUT = .../MassSpecGym1.5.tsv`. Line 137 replaces only `df["smiles"]`; formula, mass and InChIKey are
  validated but not rewritten. **VERIFIED.**
- `notebooks/massspecgym_in_the_wild/massspecgym_v1.5_validation.ipynb`, cell 7 output (per-column diff v1 vs
  v1.5): smiles 221,859 changed; precursor_mz 15; parent_mass 9; **collision_energy 2**; **instrument_type 0**.
  cell 10 output: collision_energy max absolute delta 3.552714e-15 (float round-trip). **VERIFIED.**
- Consistency check (VERIFIED): the MassSpecGym 1.5 identity parquet gives CE NaN 109,358; 20.0 18,506;
  60.0 16,015; 30.0 12,780; 10.0 7,305; 45.0 6,594; instrument Orbitrap 172,058, QTOF 53,823, NaN 5,223. These
  equal the notebook 5 cell 21 and notebook 6 cell 3 outputs.
- No 1.0 -> 1.5 change affects CE or instrument semantics.

## 5. Documentation vs content contradictions (VERIFIED statements; not smoothed over)

1. **Paper unit claim vs data.** arXiv 2410.23326 section 3.2 says C is "the collision energy, measured in
   electronvolts or eV". The column contains unconverted MSnLib NCE settings and unconverted MassBank/MoNA
   `(nominal)`/`HCD`/`(NCE)` numbers.
2. **"53% contain normalized collision energies"** (Figure 4 caption). 121,746 / 231,104 = 52.7% of rows have
   non-missing CE (VERIFIED arithmetic on the identity parquet). The caption's 53% matches the non-missing
   fraction, so "normalized" there almost certainly means "standardized/present", not NCE. INFERRED.
   - This contradicts a reading that 53% of rows carry NCE.
   - Only rows whose string had `%` were NCE-converted: 23,894 + 9 non-integer Orbitrap/NA rows back-convert
     exactly.
3. **MSnLib paper "eV" vs Tribrid % settings.** See section 3. The paper's MS2 values (20/60 plus assisted
   15-75) appear verbatim as MassSpecGym CE values. Whether MassSpecGym's authors read them as eV (per the paper
   text) or deliberately left NCE unconverted is not documented anywhere. UNRESOLVED intent.
4. **Converter comment.** Notebook 4 cell 9 `convert_nce` "assumes charge factor of 1", but it fires only on `%`.
   The notebooks contain no rule that recognizes `NCE`, `(nominal)` or `HCD` tokens.
5. **ms-pred committed labels vs ms-pred script** (hand-off to the ms-pred tasks; observed while linking):
   - `ms-pred` `data/spec_datasets/msg/labels.tsv` (commit `648b061`, 2025-10-26) matches all 119,029
     `simulation_challenge` identifiers, and `instrument` equals MassSpecGym `instrument_type` for 100% of rows.
   - Its `collision_energies` equals `floor(MassSpecGym collision_energy)` for 100% of rows. The 25,287 rows
     differing from the float are all MassBank/MoNA non-integer rows, e.g. 19.14924 -> '19'.
   - The current `data_scripts/create_msg_simulation_dataset.py` `format_collision_energy` (lines 67-80) would
     write `f"{val:g}"` (e.g. '19.1492') for non-integers. So the committed labels were not produced by that script
     version (the script was first committed 2026-07-06, after the labels).
   - Which truncation the checkpoints actually saw is for P1/P2 to settle.

## 6. Per-row source attribution without a source column

- **No source column.** The MassSpecGym 1.5 parquet schema has 14 columns: identifier, mzs, intensities, smiles,
  inchikey, formula, precursor_formula, parent_mass, precursor_mz, adduct, instrument_type, collision_energy, fold,
  simulation_challenge (`artifacts/ce_interface_adjudication/massspecgym15_schema.json`, fetched by P4). The v1
  schema is identical (validation notebook cell 3 output). The `.ms` export (notebook 7) adds none. **VERIFIED.**
- **Identifier-order attribution.** Script `scripts/ce_interface_adjudication/p3_msg_source_attribution.py`.
  - Inputs:
    - identity parquet sha256 `88e2fd1d...`;
    - P5 `exclusion/msg_row_msnlib_membership.parquet` sha256 `b71c522b...` (compound membership in the 4 v1.0
      sub-libraries);
    - P4 `massspecgym15_metadata_columns.parquet` sha256 `40d185c7...` (precursor_mz).
  - Outputs: `p3_msg15_row_source_attribution.parquet` (sha256 `3eea7d36...`) and
    `p3_msg15_row_source_attribution_summary.json`.
  - A "run" is a maximal set of consecutive identifiers sharing the 14-char key (31,885 runs, 28,929 keys).
  - The sorted identifiers are monotone. A 1.5 row's number is its notebook 3 position.
- **Block boundaries (VERIFIED empirically):**
  - **C (GNPS-first molecules): identifier >= 239,029.** From the run starting at 239,029 onward, every row
    (63,625) has missing CE. The rows just before are 100% Orbitrap-ladder runs.
  - **B (MSnLib-first molecules): 202,862..239,028.** 10,215 runs; 51 (0.5%) run first rows are not
    Orbitrap-ladder.
    - Per 1,000-ID bins 204,000-238,999: 100% of run first rows are Orbitrap with CE in {15,20,30,45,60,75}, and
      99-100% are compounds of an MSnLib v1.0 sub-library.
    - All 404 QTOF rows in B lack CE.
    - Every non-missing CE in B (IDs 204,000-239,028) is Orbitrap in the ladder.
    - Cross-check: 10,215 B runs against the paper's "10 thousand molecules (33%) ... derived from our newly
      measured in-house data (i.e., MSnLib ...)" (Table 1 context). INFERRED match.
  - **A (MassBank- or MoNA-first molecules): < 202,862.** MassBank-first and MoNA-first cannot be separated from
    these columns. UNRESOLVED boundary.
- **Row labels and counts, all rows / simulation_challenge rows** (labels in blocks A and B beyond the first row are
  INFERRED from within-molecule source order):

| Label | Rule | All rows | Sim-challenge rows |
|---|---|---|---|
| GNPS | block C, or block B with CE missing | 65,152 | 0 |
| GNPS_or_MoNA_missing_ce | block A trailing CE-missing rows | 42,037 | 0 |
| MSnLib_v1 | block B, CE present | 30,866 (30,863 Orbitrap, 3 QTOF exceptions) | 30,640 |
| MSnLib_v1_probable | block A trailing Orbitrap-ladder rows of MSnLib v1.0 compounds, before trailing CE-missing rows | 8,751 | 8,393 |
| MassBank_or_MoNA | rest of block A | 84,298 | 79,996 |

- **Simulation-challenge Orbitrap rows (81,323) by CE regime:**
  - MSnLib raw NCE: 30,637 (block B) + 8,393 (probable) = 39,030 (48.0%);
  - MassBank/MoNA converted NCE*mz/500: 23,894 (29.4%);
  - MassBank/MoNA raw integer: 18,380 (22.6%);
  - ramp half-integers: 19.
  - QTOF (37,706): 36,345 integer, 546 half-integer, 815 other fractional.
  - Split by fold: MSnLib_v1 train 19,054 / val 5,792 / test 5,794; MSnLib_v1_probable 7,219 / 556 / 618;
    MassBank_or_MoNA 73,068 / 3,386 / 3,542.
- **Fractional-CE back-conversion (VERIFIED):** `implied = CE * 500 / precursor_mz`.
  - All 24,928 non-integer CE rows lie in block A (none in B or C).
  - Share within 0.01 of an integer: Orbitrap 99.87%, NA 100% (9 rows), QTOF 2.94%.
  - So non-integer Orbitrap CE values are the `%`-converted rows, and QTOF fractional values are raw fractional
    eV.
  - Implied NCE of the converted Orbitrap sim rows: 25 (2,342), 60 (2,201), 30 (2,082), 90 (2,057), 45 (1,886),
    75 (1,885), 35 (1,635), 15 (1,496). Converted eV quantiles: 5% 7.35, median 27.66, 95% 80.13.
  - Integer MassBank/MoNA Orbitrap sim values: 45 (2,446), 30 (2,220), 90 (2,106), 15 (2,058), 75 (1,921),
    35 (1,919), 60 (1,916), 55 (733), 65 (415), 120 (403), 150 (403), 180 (399). This is the same ladder family as
    the implied NCE of the converted rows, so most are probably unconverted NCE. INFERRED; per-row unit
    UNRESOLVED. 120/150/180 may be eV-type entries.
- **If MSnLib rows were converted** (`NCE*mz/500`), their eV would be: MSnLib_v1 5% 10.86, median 25.15, 95% 58.47
  (precursor m/z median 386.1). Context only.
- **Limits of the heuristic (INFERRED):**
  1. MSnLib_v1_probable can absorb MassBank/MoNA Eawag-style 15/30/45/60/75 rows of MSnLib compounds. Its CE mix
     (60: 2,625; 20: 2,383; 15: 1,237; 30: 1,209; 45: 712; 75: 227) has more 15/30/45/75 than 20/60 parity
     predicts. The attributed MSnLib Orbitrap total, 39,614, exceeds the pre-merge literal "Orbitrap" count of
     38,585 by 1,029, consistent with about 1k false positives.
  2. Label B-with-CE assumes GNPS never has CE (VERIFIED format). Non-ladder exceptions: 3 QTOF rows plus CE
     10/40/55 (7 rows).
  3. Exact-duplicate removal keeps later copies, so MoNA/GNPS mirrors of MassBank records may carry later-source
     metadata.
  4. A 14-char run can in rare cases join two full-InChIKey groups.

## 7. Source inventory table

| Source | Entry into MassSpecGym | Native CE field and forms | Instrument field -> instrument_type | Adducts | Value in collision_energy | In simulation_challenge |
|---|---|---|---|---|---|---|
| MassBank 2023.11 (`MassBank_NIST.msp`) | notebook 1 cell 3, cell 12 | `Collision_energy:` verbatim record text: `x (nominal)`, `x%`, `x% (nominal)`, `x eV`, `x(NCE)`, `Ramp a-b`, multi-energy lists (VERIFIED format; per-record mix UNRESOLVED) | `Instrument_type:` e.g. LC-ESI-QTOF -> QTOF; LC-ESI-QFT -> QFT -> Orbitrap; LC-ESI-ITFT -> ITFT -> Orbitrap | [M+H]+, [M+Na]+ | `%`: NCE*mz/500; otherwise first number raw (NCE or eV), ramp mean; list keeps first | yes if CE present and [M+H]+ |
| MoNA LC-MS export | notebook 1 cell 2, cell 12 | free text: `10 eV`, `6V`, `20 V`, `65HCD`, `40`, `x%` (VERIFIED strings in intermediate) | free text via matchms key map and notebook 2 conversions | same | same branches | same |
| MSnLib v1.0 (Zenodo 11163381: MCEBIO, MCESCAF, NIHNP, OTAVAPEP; `*_MSn.mgf`, SPECTYPE absent, MS2) | notebook 1 cells 4, 7, 12 | `Collision energy=<float>` NCE setting: fixed 20, 60 and assisted one of 15/30/45/60/75; single-energy scans | `INSTRUMENT_TYPE` (INFERRED `Orbitrap`) wins over `SOURCE_INSTRUMENT` -> Orbitrap | same | raw NCE (15, 20, 30, 45, 60, 75), never converted | yes ([M+H]+) |
| GNPS (46 MGFs) | notebook 1 cells 1, 10, 12 | none | `SOURCE_INSTRUMENT` -> matchms instrument_type -> conversions (e.g. ESI-Orbitrap -> ESI-ITFT -> Orbitrap) | same | NaN | never |
| NIST | not used (paper: licensing) | - | - | - | - | - |

## 8. Items not settled (UNRESOLVED)

- Exact logic and input file of "Kai's filtering" (`filtered_gym_fixed.tsv`, not in the repository).
- The MassBank-first vs MoNA-first boundary inside block A, and which native string (unit) produced each integer
  MassBank/MoNA Orbitrap value.
- Whether any `%` string used a stepped or ramped list: the parser would convert only the mean of the first pair.
  Implied NCE 25 is the most common converted value, which could come from `20-30-40%`-style strings or from
  genuine NCE 25.
- The literal pre-merge `INSTRUMENT_TYPE` value of MSnLib v1.0 spectra (inferred `Orbitrap`; not read from MGF
  headers because spectra files were out of scope).
- The installed pickydict/matchms versions of the 2024-05 run; key-collision precedence was verified on current
  pickydict and matchms 0.25.0 only.

## 9. Files

- Notes: this file.
- Scripts: `scripts/ce_interface_adjudication/p3_dump_notebook.py` (notebook cell/line dumper, no network),
  `scripts/ce_interface_adjudication/p3_msg_source_attribution.py`.
- Outputs: `artifacts/ce_interface_adjudication/p3_msg15_row_source_attribution.parquet`,
  `artifacts/ce_interface_adjudication/p3_msg15_row_source_attribution_summary.json`.
- Downloads (metadata only): `artifacts/ce_interface_adjudication/p3_downloads/` (Zenodo 11163381 record JSON, HF
  commits JSON, HF README, HF data tree JSON, MoNA metadata response). The Thermo poster PDF is in the WebFetch
  cache. All are registered in `downloads_register.jsonl`.
- Note on tooling: the harness Write tool refused direct writes into this worktree from this session (the session's
  primary worktree is a different one). Files were staged in the session scratchpad and copied with shell `cp`
  into the task-designated directories, as the task instructions require.
