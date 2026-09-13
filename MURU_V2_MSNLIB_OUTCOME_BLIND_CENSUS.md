# MURU v2: MSnLib outcome-blind identity, metadata and acquisition census

Date: 2026-09-12. Status: census only. No MSnLib peak, intensity or peak-derived value was read, and no spectral library, raw or mzML file was downloaded or opened. MSnLib stays in exposure class "potential-future-external-not-outcome-accessed", with the disclosures in section 9.

Machine-readable output: `artifacts/wur_v2/external_census/msnlib_census.json` (attrition for every step in two frames, anchor counts, volumes, population hashes, the qualification block, and a provenance row for every fetched URL with file, size and sha256). Scripts (session scratchpad, copied to `data/external/msnlib_metadata/_scripts/`): `msnlib_fetch.py` (logged fetcher with a denylist), `parquet_footer.py` (schema-only range read), `zip_cd.py` (ZIP central directory range read), `zip_preview.py`, and `msnlib_census.py` (deterministic, about 3.5 min). Downloaded metadata (345 MB, gitignored) is in `data/external/msnlib_metadata/`.

## 1. Sources and versions

| Resource | Identifier | Version used |
|---|---|---|
| Paper | Brungs, Schmid, Heuckeroth et al. 2025, Nat Methods 22, 2028 to 2031, DOI 10.1038/s41592-025-02813-0 (PMC12510872, PMID 40954295) | PMC BioC full text (methods, data and code availability) and Supplementary Information MOESM1 (Supplementary Notes 3 and 4, Supplementary Tables 1 and 2) |
| Spectral libraries | Zenodo concept 10.5281/zenodo.11163380 | Current record 21105617 (DOI 10.5281/zenodo.21105617), published 2026-07-01, version index 7 of 8 (the eighth version; Zenodo carries no version string). 73 files, 17.62 GB: 72 MGF/JSON libraries and `20250828_9libraries_only_detected_cleaned.parquet`. API listing only for the libraries |
| Raw positive | Zenodo concept 10966404, latest 13785391 | 7 zips, 77.94 GB, 7 original libraries only |
| Raw negative | Zenodo concept 10967081, latest 13891125 | 7 zips, 43.41 GB |
| mzML both polarities | Zenodo concept 10966280, latest 15683784 (2025-06-17) | 18 zips, 21.63 GB, all 9 libraries. Only the ZIP central directories (member names and sizes) of the 9 positive zips were range-read |
| MassIVE | MSV000094528 | PROXI record, QueryDatasets row, GNPS2 datasetcache listing (18,280 rows). MassIVE reports 18,281 files, 254.2 GB, Orbitrap ID-X. One raw and one mzML per injection for the 7 original libraries (2022 to 2024 collections; the 2024 ones sit under `updates/`) |
| Metadata repository | github.com/merlin-ms/mass-spectral-library-network | commit ed7f85f (2026-02-20): 9 plate tables plus 9 cleaned tables in `libraries/MSnLib/compounds/`, `library_info.json`, mzmine positive batch |
| Code repository | github.com/corinnabrungs/msn_tree_library | commit eec6911 (2026-06-30): metadata cleanup and sequence scripts |

The library now covers 9 compound collections: MCEBIO, MCESCAF, NIHNP, OTAVAPEP, ENAMDISC, ENAMMOL and MCEDRUG from the paper, plus MCEDIV (20,000-compound MedChemExpress diversity subset) and TargetMol HTS natural products added in later Zenodo versions.

## 2. License

- Zenodo libraries, raw and mzML records: CC BY 4.0 in every version checked (attribution required).
- MassIVE MSV000094528: CC0 1.0 per the paper's data availability statement (not visible in the PROXI record).
- MERLIN metadata and batch files, and the cleanup code: MIT.

## 3. Instrument, activation, energies, ions

- **Instrument:** Thermo Orbitrap ID-X Tribrid with a Vanquish dual-pump flow injection front end (3 min run, about 1.5 min plateau, isocratic 50:50 water/acetonitrile with 0.1 percent formic acid). No chromatography. Wells hold 8 to 10 compounds (NIHNP up to 7). Each well was injected once in positive and once in negative mode.
- **MS1:** Orbitrap 30k, 115 to 2,000 m/z, top-3 DDA with a positive trigger threshold of 6e5. Dynamic exclusion is 3 occurrences within 200 s, then 70 s. The authors set the occurrence count to a multiple of 3 so each trigger runs all three energy experiments.
- **MS2 energy scheme (Supplementary Table 2), all HCD, all "Normalized (%)":**
  - Exp.1: Fixed, NCE 20.
  - Exp.2: Assisted, NCE 15, 30, 45, 60, 75.
  - Exp.3: Fixed, NCE 60.
  - Each experiment is its own Orbitrap scan (up to 9 MS2 scans per precursor). Nothing is merged at acquisition. The main text writes "eV", but the settings table says Normalized for every experiment.
- **Assisted is outcome-adaptive.** On Thermo Tribrids, Assisted Collision Energy is not the same as stepped energy. Hidden ion-trap scans build a breakdown curve of the precursor. The single analytical scan then uses the first listed energy at which unreacted precursor falls below a user threshold (Thermo poster PO65258, ASMS 2018, which lists HCD Fixed, Stepped and Assisted as separate modes). The chosen energy therefore depends on precursor survival, which is the quantity mu is built on. The Assisted scan is excluded as a rung. MS3 precursors are picked from it, so the MSn tree is also outcome-conditioned; this does not matter for MURU.
- **Fixed rungs usable by MURU:** exactly two, NCE 20 and NCE 60. No middle rung exists.
- **MS2 scan properties:**
  - quadrupole isolation 1.2 m/z
  - Orbitrap 15k, AGC 1.2e4, max IT 50 ms
  - first mass 40 m/z; last mass automatic and not stated
  - profile data
  - precursor selection range 115 to 2,000 m/z
- **Pilot variants:** MCEBIO has pilot runs of 20220601 (Methods 1 and 2, 24 wells) and a 20220613 production run (Method 3, all 1,051 wells). Per Supplementary Note 3, MS1 and MS2 settings did not change between methods.
- **Energy coordinate:** the frozen Stage 1 map reads WUR IQ-X nominal NCE as T(E) = -5.9555 + 0.8618 E of the LCSB coordinate. If ID-X NCE equals IQ-X NCE (both Tribrids, but this is untested), then:
  - NCE 20 maps to LCSB 30.12, only 0.12 above the lowest development rung (30);
  - NCE 60 maps to LCSB 76.53;
  - the Assisted steps 15 and 75 would map to 24.3 and 93.9, outside the development range.
- **Polarity and adducts:** both polarities were acquired for every well.
  - Positive adducts searched by mzmine: [M]+ (intrinsic charge), [M+H]+, [M+Na]+, [M+NH4]+, [M-H2O]+, [M-H2O+H]+, [M-2H2O+H]+.
  - Negative adducts searched: [M]-, [M-H]-, [M+Cl]-, [M+FA]-.
  - The v8 detection parquet has 52,068 compound-well rows: 24,572 positive only, 22,286 both, 5,210 negative only.
  - Per-adduct and per-energy spectrum counts exist only inside the peak-bearing library files, so they were not counted.

## 4. Processing and release facts (mzmine batch, Supplementary Note 4)

- **Denoising:** mass detection removes signals below 2.5 times the lowest signal in each scan ("denormalize fragment scans" on). Two background ranges (149.67 to 149.74 and 173.51 to 173.54 m/z) are removed at MS2 and above.
- **Annotation:** by exact mass (0.0015 m/z or 8 ppm), restricted to the compounds in the well through `unique_sample_id`.
- **Export:**
  - SINGLE_BEST_SCAN is the highest-TIC scan per precursor and energy.
  - SAME_ENERGY merges repeated scans at one energy (maximum height).
  - ALL_ENERGIES merges the three MS2 experiments, including the Assisted scan.
  - ALL_MSN_TO_PSEUDO_MS2 merges the whole tree.
- **Quality filters:**
  - at least 2 signals;
  - explained-intensity and explained-signal filters off;
  - "export explained signals only" off;
  - no precursor removal;
  - chimeric spectra flagged, not removed (purity 0.75).
- **Consequence:** released library spectra keep the precursor, but they are denoised and censored against spectra with fewer than 2 signals (a precursor-only spectrum is dropped). Best-scan choice is by TIC, and the merged types include the adaptive scan. A MURU endpoint has to be re-extracted from unmerged raw or mzML scans.

## 5. Attrition

Two frames were censused:

- **DESIGN:** all plated compounds from the nine cleaned MERLIN tables, joined to public positive-mode injection files by unique sample id. This frame is outcome-free.
- **DETECTED:** the same rows restricted to compound-well pairs that the authors' workflow annotated in positive mode (v8 parquet, polarity "positive" or "both"). This frame is conditioned on MS1 ion formation, DDA triggering and annotation.

Compound means distinct parent connectivity key (`parent_connectivity_key`). Groups means `scaffold_group_v2`.

### 5a. DESIGN frame

| Step | Compounds | Groups | Notes |
|---|---|---|---|
| 1 All plated compounds | 53,609 | 35,801 | 60,324 rows; 58 rows with missing or unparseable structure |
| 2 Positive injection public | 53,609 | 35,801 | All 6,752 plated wells have a positive file |
| 3 [M+H]+ eligible | 53,200 | 35,527 | 245 permanent-cation parents removed; 164 with [M+H]+ outside 115 to 2,000 |
| 4 Two fixed unmerged NCE rungs (20, 60) by design | 53,200 | 35,527 | Design level only; realized triggering needs scan headers |
| 5 Identifiable parent | 53,199 | 35,526 | 1 SMILES/InChIKey disagreement |
| 6 Unmerged data public | 53,199 | 35,526 | 33,544 with vendor raw; 19,655 mzML only (MCEDIV, TargetMol) |
| 7 Precursor-preserving endpoint possible | 53,199 | 35,526 | Status flag, see section 6 |
| 8 No exact overlap with exposed MURU data | 52,628 | 35,354 | 571 removed |
| 9 No normalized-parent or tautomer overlap | 52,622 | 35,354 | 3 parent-normalization and 3 tautomer matches |
| 10 Scaffold new versus v2 development | 47,744 | 35,094 | Identity-new but scaffold-seen: 4,878 compounds, 260 groups |
| 10b Charge-neutral scaffold new | 47,742 | 35,092 | 2 removed |
| 11 Independent scaffold groups | 47,742 | 35,092 | 30,068 groups of size 1, largest 235, 744 acyclic |

Step 8 overlap by population:

| Population | Overlapping keys |
|---|---|
| V2-DEVELOPMENT | 429 |
| WUR-DEV-ANALYSIS | 164 |
| LCSB-DEV | 159 |
| LCSB-NEG | 153 |
| WUR-SEALED | 121 |
| MultiMS2-ANCHOR | 97 |
| WUR-NEG-DEV | 54 |
| LCSB-CONFIRMATION | 44 |
| WUR-DEV-HOLD | 39 |
| LCSB-RAW-MIXES | 15 |
| WUR-NEG-D6-EXCLUDED | 9 |

Structure-only eligibility refinements after step 11:

| Rule | Compounds | Groups |
|---|---|---|
| 12a At least one well with no theoretical same-well isolation conflict (other compounds' [M+H]+, [M+NH4]+, [M+Na]+, [M+K]+, [M-H2O+H]+, 13C [M+H]+ or [M]+ within 0.7 m/z, or a same-well isomer) | 39,553 | 29,795 |
| 12b [M+H]+ in the development range 70.0 to 1,042.6 | 39,238 | 29,562 |
| 12c Sensitivity: compound in exactly one positive well | 35,420 | 27,125 |

Notes on the 12b population:

- **By library:** MCEDIV 15,048, ENAMDISC 8,190, MCEBIO 6,398, MCESCAF 4,149, NIHNP 2,907, ENAMMOL 2,431, TargetMol 1,451, MCEDRUG 1,279, OTAVAPEP 852. A key can sit in several libraries.
- **[M+H]+:** median 338.6 m/z, range 115.0 to 1,042.4.
- **Strict similarity:** 474 compounds have a maximum Morgan-count Tanimoto of 0.55 or more to a v2 development compound. The median maximum is 0.33. Below 0.55 there remain 38,764 compounds in 29,242 groups.
- **Overlap with the MultiMS2 VALIDATION population:** 364 compounds. That population is not exposed; the count is descriptive.

### 5b. DETECTED frame (outcome-conditioned)

| Step | Compounds | Groups |
|---|---|---|
| 1 and 2 Positive-detected compounds with a public positive injection | 42,531 | 31,095 |
| 3 to 7 | 42,324 | 30,960 |
| 8 No exact overlap | 41,916 | 30,815 |
| 9 | 41,912 | 30,815 |
| 10 Scaffold new | 39,238 | 30,581 |
| 10b and 11 Charge-neutral scaffold new | 39,236 | 30,579 |
| 12a No isolation conflict | 32,370 | 25,834 |
| 12b Development [M+H]+ range | 32,154 | 25,671 |
| 12c Single well | 29,499 | 23,801 |

Of the 46,858 positive-detected parquet rows, 46,850 join to design rows.

### 5c. Population hashes

Each hash is sha256 over the sorted keys joined by "\n", with no trailing newline.

| Population | n | sha256 |
|---|---|---|
| DESIGN step 8 | 52,628 | 8dfcd8106c9c3acc8c39048e34c360911904510b49c9cb31535dcff7a153d204 |
| DESIGN steps 10b and 11 | 47,742 | 84828abfe29e595379baceb993e97edc846268f255935a66b675c59407c1e283 |
| DESIGN 12b | 39,238 | 8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e |
| DESIGN identity-new, scaffold-seen | 4,878 | 35b591646e8036a1253ae1a4bb85e5cddf74325e51c4ec3b562aa24c8eadaf79 |
| DETECTED 12b | 32,154 | feaade612cb35cde6c627b813b9dc69a9dae966ed1bc05b7fd6ba0af9741e451 |
| DESIGN anchors, v2 five-rung | 402 | 0e66c78a85f0fc99060e13f25c7ac95b953894507ad57b063e42b85b1b4d102e |

Input checks:

- All 9 exposure-manifest hashes recompute (1,757-key union including v2 development and the 106 MultiMS2 anchors).
- v2 `scaffold_group` values reproduce 1,325 of 1,325.

## 6. Precursor window and censoring (step 7)

- **In raw and mzML:** the MS2 first mass is 40 m/z, the same start as the development Orbitraps. The last mass is automatic from the precursor, so [M+H]+ sits inside the window. No merging or quality filter is applied to the scans. The actual scan-window upper limit per scan still has to be confirmed from headers.
- **In the released library:** the precursor is kept, but 2.5-times-lowest-signal denoising, the at-least-2-signals rule and the TIC-best selection make it an outcome-censored view. The ALL_ENERGIES merges also contain the Assisted scan. The library is not a usable source for mu.
- **Profile versus centroid:** raw MS2 is profile. The Zenodo and MassIVE mzML are about a quarter of the raw size, which suggests centroiding, but the conversion settings were not verified. `msconvert.bat` on MassIVE returned HTTP 429 twice, and the FTP mirror reset the connection.

## 7. Anchors

Definition: identity-exposed compounds at step 6 (public positive injection, [M+H]+ eligible, identifiable parent) that also have a conflict-free well and [M+H]+ in 70.0 to 1,042.6.

| Exposed set | Design | Groups | Detected | Groups |
|---|---|---|---|---|
| v2 development, five aligned rungs | 402 | 281 | 340 | 245 |
| v2 development, any | 411 | 285 | 346 | 248 |
| MultiMS2 ANCHOR (already calibration-exposed) | 96 | 78 | 89 | 74 |
| Any exposed MURU population | 545 | 364 | 391 | 284 |

- **Where the 402 design anchors come from:** mostly MCEBIO (363) and MCEDRUG (221), with overlap between the two.
- **Historical classes:** WUR-SEALED 117, WUR-DEV-ANALYSIS 106, LCSB-DEV 93, LCSB-DEV+WUR-DEV-ANALYSIS 50, WUR-DEV-HOLD 36.
- **Measured on both development Orbitraps:** 50.

This is about four times MultiMS2's 106 anchors.

## 8. Data volume and download feasibility

**All public positive files:**
- MassIVE raw: 4,635 files, 129.0 GB (median 22 MB, maximum 70 MB per file).
- MassIVE mzML: 4,635 files, 37.1 GB.
- Zenodo positive mzML zips: 6,870 members, 13.59 GB compressed (53.8 GB uncompressed).

**(a) Anchors plus validation.** The 402 anchors and the 12b design population together touch 6,745 of the 6,752 wells, so they need essentially all positive data:
- Raw route: 4,527 raw files (125.2 GB, one preferred file per well) plus 2,218 mzML-only wells for MCEDIV and TargetMol (3.66 GB of zip members), about 129 GB in total.
- All-mzML route: 6,745 Zenodo members, 13.24 GB compressed (52.6 GB uncompressed); the nine whole zips are 13.59 GB.

**Anchors alone:** 590 wells.
- Raw route: 16.2 GB raw plus 0.08 GB of mzML-only members.
- mzML route: 1.32 GB of Zenodo members.

**Feasibility notes:**
- Zenodo supports HTTP range reads. Central-directory reads succeeded, so single members can be extracted without downloading a whole zip.
- MassIVE HTTPS downloads were rate-limited during the census. FTP is the documented bulk path.
- The Zenodo zips (up to 3.15 GB) exceed this census's 100 MB per-file limit. That limit is for the census only, but it means a later execution step needs its own authorization.

## 9. Outcome-blindness statement

No spectral peak, intensity, fragment count, entropy, similarity or per-spectrum quality value was downloaded, opened, parsed or computed.

**Not downloaded:**
- all 72 Zenodo MGF/JSON libraries
- all raw and mzML zips (only their ZIP central directories were range-read)
- every MassIVE raw and mzML file, and `params.xml`
- the GNPS2 MSNLIB libraries

**Partial reads:**
- The v8 parquet footer (schema only) was range-read before the file was downloaded. Its 363 columns are compound metadata plus `polarity` and `detected`. Only 7 columns were loaded: library, unique_sample_id, inchikey, split_inchikey, smiles, polarity, detected.
- The MERLIN tables were read for identity and plate columns only. No read table carries a peak, intensity, entropy, peak-count or explained-intensity column. ENAMMOL has a vendor "QUALITY CONTROL" column about the compound stock; it was not read.
- 18 MERLIN TSV headers were range-read (column names only) and nothing was saved; the Supplementary Information PDFs were saved through the logger.

**Outcome-adjacent information that was seen:**
- The authors' positive and negative detection membership, per compound-well pair.
- The published aggregate statements in the paper: 30,008 unique compounds detected and 357,065 MS2 spectra; for MS5, the authors note NCE 20 "produced mainly the precursor ion".
- The DETECTED frame is conditioned on that membership. It must not be used to define any validation population, exclusion, stratum or anchor (analogue of leakage finding L-02).

**Fetch provenance:**
- 59 logged fetches (360 MB bytes read, including 57.6 MB for the parquet and 255 MB for the cleaned tables) are in `fetch_log.jsonl` and in the JSON.
- Six preliminary or failed requests are listed separately in `provenance_outside_logger`.

## 10. Qualification assessment

**Claim tested:** two-rung (or more) fixed-NCE transfer across an independent Orbitrap instrument, with at least 400 compounds in at least 250 groups.

**Verdict:** conditionally eligible for a two-rung claim only (NCE 20 and 60). It is not qualified until a header gate and an anchor gate have passed. A three-rung claim is impossible, because the third MS2 experiment is outcome-adaptive.

**What favours it over MultiMS2:**
- Orbitrap Tribrid HCD on a normalized scale, the same platform family as WUR IQ-X, instead of lab-frame QTOF CID.
- The same 40 m/z first mass as development.
- Per-injection unmerged data with raw files for 7 of the 9 libraries.
- A size margin of about 100 times the floor (39,238 compounds and 29,562 groups in the design frame; 32,154 and 25,671 detected). The floor survives even the 53 percent header-level loss MultiMS2 showed.
- 402 v2 five-rung anchors in 281 groups.

**Blockers, in order:**

1. **Realized [M+H]+ triggering at both fixed rungs is unverified.** This needs a frozen header-only pass over the positive mzML (13.2 GB of Zenodo members, or 36.1 GB MassIVE mzML) that reads precursor m/z, energy, activation, filter string and scan window.
2. **Energy coordinate.** ID-X NCE is not the development coordinate. Under the untested IQ-X equivalence, NCE 20 maps to 30.12, at the clamp boundary, and NCE 60 maps to 76.53. The adapter family and gate must be frozen and run on the anchors before any validation decode. The MultiMS2 failure shows the ordering check is the real test.
3. **Library spectra are unusable for mu** (denoising, the at-least-2-signals censoring, TIC-best selection, merges that include the Assisted scan). Re-extraction from unmerged scans needs a frozen rule.
4. **Centroiding and noise-threshold rule.** Raw is profile and the mzML conversion settings are unverified. Raw centroid density was a named contributor to the MultiMS2 mismatch.
5. **Pooled flow injection with no separation.** 17 percent of scaffold-new compounds have a theoretical same-well conflict. In-source fragments and chimeras need a frozen MS1 purity rule.
6. **Replicates.** 5,091 compounds sit in more than one positive well, MCEBIO has pilot re-runs, and a precursor can trigger repeatedly within an injection. An aggregation rule is required.
7. **Access.** MCEDIV and TargetMol (about 40 percent of 12b) are available only as mzML inside Zenodo zips. MassIVE HTTPS was rate-limited.
8. **Outcome conditioning.** Only the DESIGN frame, plus header rules, may define populations.
9. **Scope.** The scaffold-new population is mostly commercial screening and diversity chemistry, and any claim must be scoped to it.

**Next step:** a frozen external protocol for MSnLib, modeled on the MultiMS2 protocol but with two rungs.
- Download the anchor mzML members (1.3 GB) first.
- Apply the header gate.
- Run the anchor calibration and its ordering gate.
- Decode validation spectra only if both pass.
