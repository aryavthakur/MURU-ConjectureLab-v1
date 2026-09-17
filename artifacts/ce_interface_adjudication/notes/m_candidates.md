# M: candidate external datasets, deduplicated, screened for construction eligibility, ranked

Study: MURU collision-energy interface adjudication (outcome-blind). Task M. Written 2026-09-14.
Worktree: `.claude/worktrees/muru-ce-interface-adjudication` at 5b1c502. Paths are relative to it unless absolute.
`$SP` = `/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-stability-study-6537d5/c50bb7b0-c2aa-4e0b-bd11-bc34c1ea3cbc/scratchpad`.

Inputs: the three discovery lists D1 (aggregators, 14 entries), D2 (repositories, 22 entries) and D3 (energy-resolved
libraries, 17 entries), as passed to task M.

Status labels: **VERIFIED** = read in code/data; **M-VERIFIED** = recomputed in this task from staged metadata
(script and summary in section 0); **D1/D2/D3 VERIFIED** = verified by that discovery agent and carried forward, not
re-read here; **INFERRED**; **UNRESOLVED**.

## 0. Access, blindness and file placement record

- Read in task M: `artifacts/ce_interface_adjudication/notes/p3_msg_curation.md` (grep hits and lines 54-80),
  `notes/p5_exclusion_linkage.md` (sections 0-2), `p3_msg15_row_source_attribution_summary.json`,
  `exclusion/{msg15_keys_all,muru_exposure_registry_keys,msnlib_9lib_keys,comparator_common_population_keys}.txt`,
  a directory listing of `exclusion/`, the `precursor_mz` column of `massspecgym15_metadata_columns.parquet`, the D1
  staged header-metadata table `$SP/ce_interface_adjudication/d1_metadata/d1_eawag_new_record_metadata.csv`
  (sha256 `56bdbdee...`, 7,490 rows, 13 columns, no peaks), the D1 staged key list
  `d1_clean_ik14_eawag_new_MH_ge3nce.json` (sha256 `cfe8c91d...`), the file-path keys of D3's
  `$SP/d3/artifacts/eawag_eq5_path_to_inchikey.json`, and ms-pred @ ed8311f `src/ms_pred/common/chem_utils.py:132`,
  `src/ms_pred/iceberg/predict_inten.py:233`, `src/ms_pred/glacier/joint_model.py:71`.
- Recount script: `scripts/ce_interface_adjudication/m_01_recheck_d1_massbank_counts.py`; output
  `artifacts/ce_interface_adjudication/m_d1_recheck_summary.json`. It reproduces every D1 MassBank count quoted below
  and confirms the 207-key D1 clean list is identical to an independent recomputation.
- Not opened: every forbidden path (benchmark RESULT document, `comparator_benchmark/{result,predictions,prediction_verification}`,
  model-output files under `technical/`, `/Users/aryav/muru-comparators/runs/`, MURU measured-mu/result/analysis files,
  PR bodies). A plain directory listing of `$SP` showed file NAMES of PR body drafts (`pr7_body_*.md`,
  `pr_body_comparator.md`); none was opened.
- No download, no web request, no model inference (ICEBERG, GLACIER, FIORA, MURU) in task M. Nothing appended to
  `downloads_register.jsonl`.
- **Placement:** the Write tool refused writes into the adjudication worktree from this session ("belongs to a
  different worktree"), exactly as reported by D1, D2 and D3. This note, the script and the summary JSON were therefore
  staged at the mirrored paths under `$SP/m/` (`$SP/m/artifacts/ce_interface_adjudication/notes/m_candidates.md`,
  `$SP/m/artifacts/ce_interface_adjudication/m_d1_recheck_summary.json`,
  `$SP/m/scripts/ce_interface_adjudication/m_01_recheck_d1_massbank_counts.py`) and must be copied by the orchestrator.
- **Open housekeeping (outside task M):** the D1 register (92 lines, `$SP/ce_interface_adjudication/downloads_register.jsonl`),
  D2 register (104 lines, `$SP/d2/artifacts/downloads_register_d2.jsonl`) and D3 pending register (28 lines,
  `$SP/d3/downloads_register_D3_pending.jsonl`) are still staged; `artifacts/ce_interface_adjudication/downloads_register.jsonl`
  holds 20 lines. D3's first eight files already sit in `artifacts/ce_interface_adjudication/d3_downloads/`.

## 1. Rules applied

Construction exclusions (drop regardless of suitability):

- **X1 MURU development data.** LCSB (MassBank contributor LCSB; LCSB populations in the exposure registry) and WUR
  (WUR Mass Spectral Library, Zenodo 20552933, and Wageningen Food Safety Research libraries: WFSR-LIBRARY, PASL,
  ECRFS_DB). That WFSR libraries are the same lab lineage as MURU's WUR data is INFERRED (WFSR is part of WUR; D2
  census: ECRFS_DB 97 of 99 keys already in the MURU exposed union); they are dropped either way.
- **X2 MSnLib lineage.** Listed only in section 6 as disfavoured fallback.
- **X3 QTOF-only eV sets.** Kept at most as SUPPORTING (they cannot adjudicate NCE semantics).
- **X4 Other MURU-exposed populations.** MultiMS2 and ENTACT are named exposure-registry populations (VERIFIED file
  names `exclusion/muru_exposure_registry_population_MultiMS2-ANCHOR_keys.txt` and
  `..._ENTACT-MIX-LISTS-499-503-505_keys.txt`).

Ranking criteria, in priority order:

- **R1** Orbitrap HCD with one explicit, non-stepped, non-ramped NCE per spectrum (the disputed quantity).
- **R2** Several NCE per compound (a ladder constrains the CE response, not just an offset).
- **R3** Precursor m/z on both sides of 500. The documented interface eV = NCE*mz/500 and raw NCE coincide at
  m/z 500 and separate by the factor mz/500 (MassSpecGym `convert_nce`, p3 note line 162, VERIFIED there).
- **R4** Independence from the checkpoints' training data: spectra outside the MassSpecGym sources (MassBank release
  2023.11, MoNA LC-MS export, the 46 named GNPS libraries, MSnLib v1.0; p3 note lines 67-73) and compounds absent from
  MassSpecGym 1.5; plus absence from MURU exposure.
- **R5** Identity, instrument and per-spectrum CE reachable under the current download policy.
- **R6** Identity quality (reference standards) and inside the checkpoints' domain. M-VERIFIED: MassSpecGym 1.5
  `precursor_mz` maximum is 999.396. VERIFIED constants: `MAX_ATOM_CT = 160` (chem_utils.py:132) and output binning
  `upper_limit` 1500 (iceberg/predict_inten.py:233, glacier/joint_model.py:71). Whether either is enforced on inputs at
  inference is UNRESOLVED (not traced).

Roles: **EVAL** = candidate independent adjudication/evaluation set. **ATTRIBUTION** = in training; used only to
attribute how MassSpecGym encoded CE strings per source, never for evaluation. **SUPPORTING** = QTOF eV control.

Suitability drops (not construction): commercial or access-restricted; CE not recorded and no policy-compliant route
to it; stepped or ramped CE only; identity from pooled or combinatorial runs with no recoverable CE; in-training with
no attribution value beyond C03.

## 2. Merge map

| ID | Merged entries (source list: entry) |
|---|---|
| C01 | D1: "Eawag post-snapshot HCD additions"; D2: "Eawag MassBank EQ additions after the MassSpecGym snapshot". NOT D3's EQ5 sample (see K3) |
| C02 | D1: "CyanoMetDB"; D2: "CyanoMetDB reference spectra"; D3: "MLU-ED series" (MLU-ED is the CyanoMetDB Q Exactive Plus block) and D3's MassBank API contributor count "EAWAG 2,546" (= EAWAG-EC 1,010 + EAWAG-ED 1,536, D2) |
| C03 | D1: "NaToxAq"; D1: "pre-2023.11 Eawag and Eawag_Additional_Specs"; D1: "UFZ, HBM4EU, AAFC" (Orbitrap parts); D3: "Eawag collection" (pre-2023.11 part, including the EQ5xxxxx sample); D3: "NaToxAq"; D3: "Other MassBank EU contributors" (UFZ, HBM4EU Orbitrap parts); D2 excluded-list NaToxAq line |
| C04 | D1: GNPS post-snapshot entry (ELIXDB-LICHEN-DATABASE sub-item); D2: "ELIXDB lichen natural products" |
| C05 | D2: "BOKU/Mendel University prenylated flavonoid MS/MS library" |
| C06 | D2: "PharmMet DB" |
| C07 | D1: "ACES_SU PW-FDA and other post-2023.11 contributions" (mFam sub-item); D2: "mFam Consortium MassBank contribution" |
| C08 | D2: "REFRAME drug repurposing library spectra" (REFRAME-POSITIVE-LIBRARY and its sibling CMMC-REFRAME-POSITIVE-LIBRARY, duplication between the two UNRESOLVED) |
| C09 | D1: GNPS post-snapshot entry (TUEBINGEN-NATURAL-PRODUCT-COLLECTION sub-item); D2: "Tuebingen Natural Product Collection" |
| C10 | D1: "BAFG (BfG) SCIEX TripleTOF CE ladder"; D3: "BAFG collection"; D2: "SECONDARY (TOF/QTOF)" (BfG 2025.05.1 sub-item) |
| C11 | D2: "SECONDARY (QTOF eV): ExpoLib 1.0" |

## 3. Shortlist (11 of a permitted 12)

| Rank | ID | Name | Role | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C01 | MassBank Eawag EQ HCD NCE ladders first released 2024.06 / 2024.11 / 2025.10 | EVAL (primary) | yes | yes (15-180) | mostly below 500 | 87-compound clean core | yes | standards, in domain |
| 2 | C02 | CyanoMetDB spectra (MassBank 2026.03: EAWAG-EC, EAWAG-ED, MLU-ED) | EVAL (high-m/z arm) | yes | yes (15-80) | mostly above 500 | 120 clean | yes | weak (49/150 Level 1); 38/120 above m/z 999.4 |
| 3 | C03 | MassBank 2023.11 in-training Orbitrap HCD contributors (NaToxAq, Eawag, Eawag_Additional_Specs, UFZ, HBM4EU, AAFC) | ATTRIBUTION | yes | yes | both | no (in MSG) | yes | standards |
| 4 | C04 | ELIXDB lichen library (GNPS; MetaboLights MTBLS8109) | EVAL (conditional) | unit ambiguous | 3 levels | UNRESOLVED | 72 novel [M+H]+ keys | partly | isolates |
| 5 | C05 | BOKU/Mendel prenylated flavonoid library (Zenodo 16762591) | EVAL (conditional) | unit ambiguous | 10 HCD levels | UNRESOLVED | partly | NO (CE only in MGF) | standards and isolates |
| 6 | C06 | PharmMet DB parent drugs (Metabolomics Workbench ST003991) | EVAL (conditional) | yes (single 35) | no | likely both | overlap unquantified | partly | parents only |
| 7 | C07 | mFam consortium, Orbitrap subset (MassBank 2025.10) | EVAL (conditional) | mixed | mixed | UNRESOLVED | overlap unreported | yes | mixed |
| 8 | C08 | REFRAME-POSITIVE-LIBRARY (GNPS) | EVAL (conditional on CE present) | UNVERIFIED | UNVERIFIED | likely both | 4,411 novel [M+H]+ keys | 46 MB CSV in policy | crude pooled |
| 9 | C09 | Tuebingen Natural Product Collection (GNPS) | EVAL (conditional on CE recovery) | UNVERIFIED | UNVERIFIED | UNRESOLVED | 173 novel [M+H]+ keys | no CE route yet | isolates |
| 10 | C10 | BAFG SCIEX TripleTOF CE ladders (MassBank) | SUPPORTING | QTOF | yes (10-150) | n/a | mostly in MSG | yes | standards |
| 11 | C11 | ExpoLib 1.0 (Zenodo 20715576) | SUPPORTING | QTOF | yes (20-70) | n/a | UNRESOLVED | names only | standards |

The twelfth slot is deliberately unused: no remaining Orbitrap entry has a policy-compliant route to per-spectrum CE,
and the remaining QTOF entries add nothing C10 and C11 do not already cover (see MUI NPS in section 4).

### C01 (rank 1, EVAL primary). MassBank Eawag EQ post-2023.11 HCD NCE ladders

- URL: https://github.com/MassBank/MassBank-data/tree/dev/Eawag (merged PRs #258, #263, #319; dev-only PR #398).
- Instrument, M-VERIFIED ([M+H]+ records): Exploris 240 2,201 (1,346 "Exploris 240 Orbitrap Thermo Scientific" + 855
  "Exploris 240 Thermo Scientific"), Q Exactive Plus 609, Q Exactive 96. HCD, LC-ESI-QFT (D1 VERIFIED). All
  polarities: Exploris 3,299, Q Exactive Plus 834, Q Exactive 183.
- CE semantics: `COLLISION_ENERGY N % (nominal)`, one energy per spectrum. M-VERIFIED: 100% of the 7,490 staged
  Eawag-family records contain `%`. MassSpecGym's parser converts `%` strings with /500 (p3 note lines 162 and 235),
  but these records are not in MassSpecGym, so that is only the documented convention. D2's "CE UNVERIFIED" is
  superseded by D1's header harvest.
- Energies, M-VERIFIED over all 375 [M+H]+ compounds: full ladder 15,30,45,60,75,90,120,150,180 for 201; truncated
  15-120 (41), 15-150 (30), 15-90 (25).
- Compounds, M-VERIFIED: 375 [M+H]+ compounds (first release 2024.06: 81; 2024.11: 214; 2025.10: 80); 364 with >=3 NCE;
  of those 248 in MassSpecGym 1.5 and 222 in the MURU exposure registry keys; **87 in neither** (23 / 31 / 33 by
  release), 0 of them in MSnLib 9-lib keys, 0 in the closed benchmark common population. Clean-core precursor m/z
  median 311.1, 10-90% 159.3-581.4, max 784.5; 73 of 87 below 500, so mz/500 is mostly 0.32 to 1.16.
- Polarity: [M+H]+ 2,939 and [M-H]- 1,425 records (M-VERIFIED).
- Release: 2024-06-05, 2024-11-26, 2025-10-24; dev 2026-07-30 (D1). All after MassBank 2023.11, the MassSpecGym source.
- Metadata access: git trees (file names encode compound id and spectrum index), GitHub code-search header fragments,
  MassBank3 API counts. Full record files contain `PK$PEAK` and were not fetched.
- Overlap risks: 68% (248/364) of multi-NCE compounds are already MassSpecGym 1.5 compounds, so only the 87-compound
  core is compound-independent. Overlap used the recorded InChIKey first block, not the MURU parent connectivity key,
  and no scaffold-group exclusion was applied (K12). Some transformation products are flagged TENTATIVE (D2).
  Environmental-suspect chemistry adjacent to LCSB. PR #398 (670 files, 64 compound ids) is unprofiled.
- Why rank 1: meets R1, R2, R4, R5 and R6 with one lab, one CE convention and three Thermo platforms on one ladder.
  Weakness is R3 (14 of 87 compounds above m/z 500), which C02 complements.
- Detailed screening must: recompute keys and scaffold groups with `scripts/ce_interface_adjudication/scaffold_key.py`
  from record SMILES; re-read CE strings at tag 2025.10 rather than dev HEAD; check chemical-class diversity; decide
  whether PR #398 is in scope.

### C02 (rank 2, EVAL high-m/z arm). CyanoMetDB spectra in MassBank 2026.03

- URLs: https://github.com/MassBank/MassBank-data/pull/366 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC13200231/ ;
  https://pubs.acs.org/doi/10.1021/acs.jnatprod.6c00107
- Instrument, M-VERIFIED records: Exploris 240 2,546 (EAWAG-EC/ED), Q Exactive Plus 580 (MLU-ED). Paper: Exploris 240
  for 336 compounds plus 54 reanalysed, Q Exactive Plus for 75 (D2 VERIFIED).
- CE semantics: `N % (nominal)` HCD, single energy (D1 VERIFIED); paper states separate NCE 15-80 % (D2 VERIFIED).
- Energies, M-VERIFIED over 136 [M+H]+ compounds: 15,20,25,30,40,50,60,70,80 for 99; 15-60 for 13; 15-70 with 35
  for 11.
- Compounds, M-VERIFIED: 136 [M+H]+ compounds, all with >=3 NCE; 14 in MassSpecGym 1.5, 4 in MURU keys, **120 clean**,
  0 in MSnLib 9-lib. Clean precursor m/z median 883.4, 10-90% 587.3-1096.4, max 1752.8; **38 of 120 above the
  MassSpecGym 1.5 maximum 999.396**; 6 below 500. mz/500 is mostly 1.17 to 2.19.
- Polarity: [M+H]+ 1,888, [M-H]- 1,211, [M+2H]2+ 27 records (M-VERIFIED).
- Identity: only 49 of 150 uploaded compounds are Level 1 reference materials; 101 are from semipurified or crude
  biomass and flagged TENTATIVE (D2 VERIFIED from the paper).
- Metadata access: Supplementary Table S4 (Excel, accessions and compound metadata) per D2; git trees and code search.
- Overlap risks: low compound overlap, but out of training domain (m/z, likely atom count; cyclic peptides), a single
  structural class, two labs.
- Role: the only verified independent Orbitrap NCE ladder on the high side of m/z 500, where the two interfaces
  separate in the opposite direction from C01. Defensible core = Level 1 compounds with precursor m/z <= 999.4
  (size UNRESOLVED; needs S4).

### C03 (rank 3, ATTRIBUTION). MassBank 2023.11 in-training Orbitrap HCD contributors

- URLs: https://github.com/MassBank/MassBank-data/tree/2023.11/Eawag , `/Eawag_Additional_Specs`, `/NaToxAq`, `/UFZ`,
  `/HBM4EU`, `/AAFC`.
- Purpose: the checkpoints were trained on MassSpecGym rows whose CE came from these strings. MassSpecGym converts
  only strings containing `%` and keeps other numbers raw (p3 note line 235, VERIFIED there). These contributors carry
  both arms on Orbitrap HCD: `%` strings (NaToxAq 100% of HCD; HBM4EU HCD 100%; Eawag EQ 63 of 101 sampled; UFZ 85%)
  and NCE strings without `%` (AAFC `N(NCE)` 100%; Eawag `90 (nominal)` 38 of 101 sampled; Eawag_Additional_Specs
  `30 (nominal)` 235 of 300 sampled; UFZ remainder) (D1 VERIFIED, sampled at dev HEAD). So MassSpecGym training
  plausibly mixes both interfaces for the same instrument class (INFERRED). Consistent aggregate: MassBank_or_MoNA
  Orbitrap rows are 24,104 other_fractional versus 19,261 integer CE (M-VERIFIED from
  `p3_msg15_row_source_attribution_summary.json`).
- Energies (D1 VERIFIED): NaToxAq 10-105 step 5 (20 levels, 60 compounds); Eawag EQ 15-180; Eawag_Additional_Specs
  15-90; UFZ 10-90; HBM4EU 15-60; AAFC 10-55.
- Compounds (D1 VERIFIED): NaToxAq 119 with >=3 HCD energies (118 in MSG); Eawag at 2023.11: EQ 4-digit 515, EQ
  6-digit 184, EA 361 compound ids; Eawag_Additional_Specs 79 of 82 multi-energy in MSG; UFZ 324 (323); HBM4EU 131
  (121); AAFC 140 (126).
- Metadata access: git trees at tag 2023.11; code-search fragments; MassSpecGym 1.5 rows (`massspecgym15_metadata_columns.parquet`,
  identity parquet) for matching.
- Overlap risks: in training by construction; never usable for evaluation.
- Detailed screening must: re-read CE strings at tag 2023.11 (curation PRs may have changed them since); match
  MassSpecGym rows by InChIKey, precursor m/z and CE value to classify each contributor's rows as converted
  (CE = NCE*mz/500) or raw; include the D3 EQ5xxxxx Exploris sample (K3).

### C04 (rank 4, EVAL conditional). ELIXDB lichen library

- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11814408/ (Sci Data 2025); GNPS ELIXDB-LICHEN-DATABASE; MetaboLights MTBLS8109.
- Instrument: Orbitrap Exploris 120 with polarity switching (D2).
- CE semantics: GNPS spectra merged from events labelled 10, 35 and 80 eV; individual-CE spectra said to be in
  MTBLS8109. Exploris instruments offer absolute and normalized modes, so the unit is AMBIGUOUS (K5).
- Compounds (D2 census): 534 spectra, 518 parent keys, [M-H]- 437, [M+H]+ 96; 72 novel [M+H]+ keys against
  MassSpecGym 1.5, MSnLib 9-lib and the MURU union.
- Release: GNPS create_time 2024-08-14; paper 2025-02-12. Not in the MassSpecGym GNPS list (INFERRED from D1/D2 lists;
  the related older LDB lichen library is).
- Metadata access: GNPS LibraryServlet metadata (done by D2, peaks null); MTBLS8109 ISA-Tab for per-file CE (not read).
- Risks: small positive yield; merged spectra in GNPS; unit ambiguity.
- Why here: if the ISA-Tab or method resolves the unit, it gives either an Orbitrap absolute-eV set (a direct test of
  the eV interface) or a 3-level NCE set, with metadata inside policy.

### C05 (rank 5, EVAL conditional). BOKU/Mendel prenylated flavonoid library

- URL: https://zenodo.org/records/16762591 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12471768/
- Instrument: Orbitrap IQ-X Tribrid (library acquisition) and Q Exactive HF (D2).
- CE semantics: HCD 10-100 step 10 plus stepped 20/45/70 and CID 10-100; the authors write "eV in absolute values" (D2
  VERIFIED wording). Whether the method editor used absolute or normalized mode is AMBIGUOUS (K5).
- Compounds: UNVERIFIED (64 prenylated flavonoids used for training plus other flavonoid standards).
- Polarity: positive and negative; [M+H]+ and [M-H]- dominant.
- Release: Zenodo 2025-08-07; paper 2025-09-17.
- Metadata access: **fails R5 under current policy.** The only file is `in-house_MSMS_library.mgf` (18.8 MB, a
  spectra file). Compound list only from the paper SI; per-spectrum CE cannot be verified without a policy extension.
- Risks: common flavonoids are in MassSpecGym 1.5; isolates are non-commercial.

### C06 (rank 6, EVAL conditional). PharmMet DB parent drugs

- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12923290/ ; Metabolomics Workbench ST003991 (doi 10.21228/M8W55K).
- Instrument: Orbitrap ID-X Tribrid, the MSnLib instrument class (D2).
- CE semantics: single HCD 35 % normalized (paper text, D2).
- Compounds: 1,114 parent drugs; 59,869 putative metabolites (not structure-confirmed, not usable).
- Release: 2025-10-13. Licence CC BY-NC-ND 4.0.
- Metadata access: Metabolomics Workbench REST study metadata and feature tables.
- Risks: parent drugs overlap MassSpecGym and MSnLib collections (not quantified); licence may constrain derived
  publication; whether MS/MS spectra are deposited in usable form is UNVERIFIED.
- Why here: one NCE over a drug m/z range still separates the interfaces (raw 35 everywhere versus 35*mz/500), on the
  instrument class whose training rows entered raw; but no ladder.

### C07 (rank 7, EVAL conditional). mFam consortium Orbitrap subset

- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC13328316/ ; MassBank contributor mFam (MSBNK-mFam-MC_*).
- Instrument (D2 API VERIFIED, all mFam records): LC-ESI-QTOF 3,254; LC-ESI-ITFT 2,634; ESI-TOF 1,094; LC-ESI-QFT 689;
  APCI-ITFT 116; ESI-QTOF 85. 47 datasets from 25 labs.
- CE semantics: heterogeneous free text (D1 VERIFIED samples: `6.0000000`, `0.6458333`, `15,30,45 (NCE)`,
  `-10, -35, -60V`); D1 reports mostly single stepped or ramped spectra.
- Compounds: 2,126 unique compounds, 7,872 spectra (paper, D2).
- Release: MassBank 2025.10 (2025-10-24).
- Metadata access: code-search header fragments; MassBank3 API counts; paper SI template.
- Risks: overlap with GNPS/MSnLib/MassSpecGym unreported and likely substantial; most sub-collections probably fail R1.
- Screening must count sub-collections that are Orbitrap, single NCE with `%` or `(NCE)`, and >=3 energies per
  compound; drop if none.

### C08 (rank 8, EVAL conditional on CE present). REFRAME-POSITIVE-LIBRARY

- URL: https://external.gnps2.org/gnpslibrary ; https://external.gnps2.org/processed_gnps_library/REFRAME-POSITIVE-LIBRARY.csv
- Instrument: GNPS `Orbitrap`; processed CSV msManufacturer Thermo, msMassAnalyzer orbitrap (D2).
- CE semantics: UNVERIFIED; `collision_energy` empty in the 2 processed-CSV rows read (D2). Stepped NCE is INFERRED
  lab practice only.
- Compounds (D2 census): 7,351 parent keys, 7,295 [M+H]+ keys; 2,642 in MassSpecGym 1.5; 4,411 novel [M+H]+ keys.
- Release: GNPS create_time 2024-11-22 to 2025-07-04.
- Metadata access: processed CSV, 46 MB, metadata only, inside policy, not yet downloaded.
- Risks: identity is `Crude` with names carrying "(known structural isomers: N; isobaric peaks in run: N)", i.e.
  pooled-plate annotations, not single-standard injections.
- Screening must download the 46 MB CSV (inside policy), count non-empty `collision_energy`, `msModel`,
  `msDissociationMethod`; drop if CE is absent or stepped.

### C09 (rank 9, EVAL conditional on CE recovery). Tuebingen Natural Product Collection

- URL: https://external.gnps2.org/gnpslibrary (TUEBINGEN-NATURAL-PRODUCT-COLLECTION).
- Instrument: GNPS `Orbitrap`; model UNVERIFIED.
- CE semantics: not in the GNPS summary schema (D1 VERIFIED key list); UNVERIFIED.
- Compounds: 980 spectra, 340 parent keys, 273 [M+H]+ keys (D2); 302 [M+H]+ spectra, 277 unique SMILES (D1);
  173 novel [M+H]+ keys (D2).
- Release: 2023-09-18 to 2025-01-24; not in the MassSpecGym 46-library list (D2, from the supplement), so absent from
  MassSpecGym despite predating the snapshot.
- Metadata access: GNPS metadata JSON (done); CE would need the GNPS2 processed CSV (size not reported) or MassIVE
  method files.
- Risks: isolated microbial natural products; CE may simply not exist in any open metadata.

### C10 (rank 10, SUPPORTING). BAFG SCIEX TripleTOF CE ladders

- URL: https://github.com/MassBank/MassBank-data/tree/dev/BAFG (PR #275).
- Instrument: TripleTOF 5600 / 6600 / X500R SCIEX, LC-ESI-QTOF, CID (D1 VERIFIED; D3 saw 5600).
- CE semantics: bare `COLLISION_ENERGY 10` with record title `10 V` (D1 VERIFIED, MSBNK-BAFG-CSL25011727798.txt); SCIEX
  CE in V equals eV for singly charged ions (INFERRED). MassSpecGym keeps numbers without `%` raw, so QTOF rows are
  native eV in training (p3 note line 235).
- Energies: 10-150 step 10 (D1 sample); D3 saw 20-140 for one compound.
- Compounds: not counted (accession does not encode compound); 20,658 records (API).
- Release: bulk <= 2023.11 (in MassSpecGym source); post-2023.11 increment 875 files (D1, D2) versus "+646 spectra" in
  PR #275 (K9).
- Role: eV-path control and in-training eV attribution; the post-2023.11 increment is a small independent QTOF arm.

### C11 (rank 11, SUPPORTING). ExpoLib 1.0

- URL: https://zenodo.org/records/20715576
- Instrument: SCIEX QTOF (model UNVERIFIED).
- CE semantics: single CE 20-70 eV step 5 plus CES 30+-10, 30+-20, 40+-10, 40+-20 (D2 VERIFIED in
  `Library Overview - ESI+.xlsx`, 53,212 B, registered in D2's staged register).
- Compounds: >170 xenobiotics; about 106 ESI+ rows; names only, no SMILES.
- Release: 2026-06-16.
- Risks: exposome chemistry probably overlaps LCSB/ENTACT MURU populations and MassSpecGym (not computed; needs
  name-to-structure resolution).
- Role: dense, independent, post-snapshot QTOF eV ladder.

## 4. Dropped entries (one line each)

From D1:

- MUI PSY-SUB NPS (MassBank dev PR #396): QTOF (TripleTof 5600+, eV, D1 VERIFIED), untagged dev contribution with ladder and identities unprofiled; C10/C11 already cover the QTOF control.
- ACES_SU PW-FDA (Prestwick FDA, MassBank 2025.10): one ramped spectrum per compound (`Ramp 20%-70% (nominal)` in 299/300 sampled, D1 VERIFIED), fails R1 and R2; FDA drugs overlap MassSpecGym.
- SMB_Measured / Shin-MassBank (2026.03): CE recorded as ranges or stepped lists (`20-40%`, `NCE 20.30.40`), fails R1; mixed Orbitrap and TripleTOF.
- NILU (MassBank 2024.11-2025.10): 610 records with mixed CE formats (`30% (nominal)`, `20`, `40 eV`) across Exploris 120 negative, QE Plus and Agilent QTOF; too small and inconsistent.
- HBM4EU QTOF records (TripleTOF 5600+, Agilent 6547): in-training QTOF eV, redundant with C10 (HBM4EU Orbitrap part kept in C03).
- MoNA VF-NPL QExactive (28,260 spectra): CE unverified, per-spectrum metadata only with peaks, predates the MoNA export used by MassSpecGym (in training).
- MoNA HCD_natural_product_library (LibGen): CE field unverified (count query returned 0), release date unknown, D2 reports single HCD 30.
- MoNA UVPD Library (Fiehn, IQ-X): single HCD 30 NCE plus UVPD, likely in the MassSpecGym MoNA export (D2).
- MoNA Alkaloids QE pos: CE field unverified, per-spectrum metadata needs peaks, release unknown.
- MoNA EMBL-MCF_2.0_HRMS_Library: stepped NCE 30/50/70 only; EMBL-MCF 1.0 in the MassSpecGym GNPS list (D2).
- MoNA PFP NP library: CE field unverified, metadata only with peaks, release unknown.
- MoNA Plant Metabolites NIST: CE unverified, metadata only with peaks, release unknown.
- MoNA POS_Metabolite_IDX: CE unverified, metadata only with peaks, release unknown.
- MoNA DNAAdduct library: CE unverified, mixed Orbitrap and QTOF MSn, metadata only with peaks.
- MoNA NCU fungicide and EnvCpd suspect libraries: Compound Discoverer annotations, not reference standards.
- GNPS-LIBRARY post-2024-05-13 submissions (1,729 entries): no CE field in GNPS metadata (D1 VERIFIED), generic `Orbitrap`, heterogeneous submitters.
- GNPS CMMC-FOOD-BIOMARKERS: no CE field; 154 unique [M+H]+ SMILES of common food metabolites.
- GNPS LEAFBOT: no CE field; 224 unique [M+H]+ SMILES.
- GNPS-ALKYLAMINES libraries: reaction-product candidates, not reference standards.
- GNPS WINE-DB-ORBITRAP (and paired WINE-DB-QTOF, D2): no CE field; only 38 novel Orbitrap [M+H]+ keys (29 QTOF).
- GNPS PYRROLIZIDINE-ALKALOID-SPECTRAL-LIBRARY (PASL): X1, WFSR (WUR).
- GNPS ECRFS_DB: X1, WFSR (WUR); 97 of 99 keys already in the MURU exposed union (D2).
- GNPS WFSR-LIBRARY (WFSR Food Safety library): X1, WUR.
- GNPS MCE-DRUG: X2, MSnLib lineage (2,842 of 2,867 keys in MSnLib 9-lib, D2); section 6 only.
- GNPS BERKELEY-LAB (JGI QE-HF): stepped CE encoded in compound names, in the MassSpecGym GNPS list (training).
- MultiMS2 (ZenoTOF 7600, MassIVE MSV000099369): X4 (MURU MultiMS2-ANCHOR population) and X3 (QTOF CID/EAD).
- Spectraverse v1.0.1: aggregation, not a new measurement; its eV and NCE fields are derived with the same /500 formula (D1 VERIFIED on 273,012 rows), so circular; retained only as an enumeration aid (section 5).
- D1 pre-rejected MassBank contributors (Athens_Univ, Antwerp_Univ, Fiocruz, Env_Anal_Chem_U_Tuebingen, IPB_Halle, KWR, MPI_for_Chemical_Ecology, NAIST, CASMI_2016, MetaboLights, MSSJ, ENTACT_AGILENT, RIKEN groups, Tolmar, Qingdao_University, CPU): not Orbitrap HCD NCE, eV/ion-trap CID, or trivially small (D1); LCSB: X1.

From D2:

- ACES_SU (MassBank 2025.10, 1,507 records): same as D1's ACES_SU line (ramped, D1 VERIFIED).
- 3-HYDROXY-ACYL-AMIDES-LIBRARY (GNPS): `Crude` combinatorial-synthesis candidates, positional isomers, one lipid-like class, CE unverified.
- Utrecht University Endogenous Metabolite Library (Zenodo 21394919): only 7 novel [M+H]+ keys and an unresolved CE contradiction (K7).
- EMBL-MCF 2.0 HILIC library: stepped only and high MassSpecGym overlap (same as the MoNA line).
- MUI NPS series: same as D1's MUI line; D2's Orbitrap inference is contradicted by D1's record read (K4).
- NIOM extractables and leachables library (Zenodo 21260530): access restricted, no file listing.
- ORNL drop-on-demand OPSI libraries (JASMS 2026): data availability unverified (paywalled), flow injection, likely high MassSpecGym overlap.
- mzCloud: licensed, no bulk export; not usable for an open evaluation.
- NIST 23 / NIST 26 HR-MS/MS: commercial licence only.
- Enveda-180 (timsTOF): X3, and no metadata table under 50 MB (349 MB parquet with spectra); pooled-injection identity.
- GNPS-ION-MOBILITY-LIBRARY: X3 (ToF), `Crude` pooled/propagated identity.
- DMIM-DRUG-METABOLITE-LIBRARY: X3 (qTof), `Crude` identity, CE unverified.
- WUR Mass Spectral Library (Zenodo 20552933): X1.
- MSNLIB-POSITIVE / MSNLIB-NEGATIVE (GNPS): X2; section 6 only.
- LibGen HCD_natural_product_library and UVPD Library: as the MoNA lines above.
- CASMI 2022 (MassIVE MSV000089239): instrument and CE unverified, only mzML (spectra) carries CE (outside policy), and D2/D3 disagree on single versus several energies (K8).
- HighResNPS: consensus fragment lists, not spectra; crowd-sourced mixed instruments; login required.
- FragHub and MassCube DB: aggregations, not new measurements.

From D3:

- Athens_Univ (Bruker maXis Impact): X3, QTOF eV, in MassSpecGym source.
- MSnLib raw and library files (Zenodo 11163381, 10966404, 10967081, 10966280; MassIVE MSV000094528): X2; section 6 only.
- Wiley Registry MSforID (WRTMSD, NORMAN-SLE S31 list): spectra commercial; compound list only; retained as literature evidence (section 5).
- NIST20/23/26: commercial licence (same as D2 line).
- mzCloud: licensed (same as D2 line).
- BMDMS-NP: in the MassSpecGym 46-library GNPS list (VERIFIED, p3 note line 72), CE values and units not recorded in GNPS metadata.
- Szabo et al. 2021 energy-resolved peptides (MassIVE MSV000086434): peptides, not small molecules, raw spectra only; retained as literature evidence (section 5).
- EPA ENTACT_AGILENT (MassBank): X4 (MURU ENTACT population) and X3 (Agilent QTOF, 3 levels).
- CASMI 2016: stepped NCE 20/35/50 merged into one spectrum, in MassBank 2023.11 (training).
- FREMS near-continuous ramp (Yevdokimov et al.): ion-trap CAD on LTQ Orbitrap XL, not beam-type HCD; a handful of ions.
- EMBL-MCF 1.0: stepped NCE 20/40/60; GNPS-EMBL-MCF in MassSpecGym's GNPS list (D2).
- Antwerp_Univ (Agilent 6560 QTOF), KWR (Orbitrap Classic ion-trap CID labelled eV), NILU, IPB_Halle, MSSJ, RIKEN_ReSpect: not Orbitrap HCD NCE ladders (D3 "Other MassBank EU contributors"; UFZ and HBM4EU Orbitrap parts are in C03, ACES_SU dropped above).

## 5. Auxiliary evidence retained (not candidate datasets)

- MassSpecGym construction notebooks 1 and 4 (already analysed in `notes/p3_msg_curation.md`).
- Spectraverse v1.0.1 metadata CSV (Zenodo 17870921): locator for non-MassSpecGym compounds only.
- Oberacher et al. 2019, Metabolites 9:3 (PMC6359582): Eawag Orbitrap NCE versus WRTMSD QqTOF eV on 233 shared
  compounds, optimal ranges 30-60 NCE versus 20-50 eV, no conversion formula (D3).
- Szabo et al. 2021, J Mass Spectrom (doi 10.1002/jms.4693): peptide NCE versus eV, ridge slope 0.92 (D3).
- ICEBERG 2.0 (PMC12154671) states eV = NCE*mz/500; GLACIER arXiv 2606.29161v1 states no unit (D3). ms-pred README @
  ed8311f lines 183-184 and 193-213 (msg_simulation versus msg_all CE imputation) and MassSpecGym issue #71 (D3).
- Thermo trailer readers: ProteoWizard `SpectrumList_Thermo.cpp` @ e96bc80 lines 150-178, 461, 493-503; alpharaw
  `thermo.py` @ a3dbb6d lines 323-329 (D3). These would matter only if raw files are ever authorized.
- GNPS `gnps_cleaned.csv` (471,257,140 B): metadata-only with a `collision_energy` column for every GNPS spectrum;
  above the 50 MB cap, needs a policy extension (D1, D3).

## 6. Disfavoured fallback (MSnLib lineage, not ranked)

- F1 MSnLib raw acquisition files (Zenodo 10966404 `.raw` positive, 10967081 negative, 10966280 `.mzML`; MassIVE
  MSV000094528). Thermo trailers carry an instrument-computed `HCD Energy eV:` that would map NCE to eV for the
  exact training chemistry. Needs spectra-file downloads (outside policy). Exposure: MassSpecGym training (MSnLib_v1
  30,866 rows plus 8,751 probable, p3 summary), FIORA-OS training, MURU MSnLib confirmation population.
  Contradiction K6.
- F2 GNPS MCE-DRUG (MSnLib lineage by key overlap).
- F3 GNPS MSNLIB-POSITIVE / MSNLIB-NEGATIVE.

## 7. Contradictions and unresolved points

- **K1 MassSpecGym snapshot date.** Notebook 1 cell 0 says 13/05/2024; the paper says May 27, 2024 (p3 note lines
  67-69; D1 versus D2). Immaterial for MassBank (2023.11 either way; 2024.06 was published 2024-06-05). Material for
  GNPS "post-snapshot" counts: D1 used 2024-05-13, D2 used 2024-05-27, so those counts are not comparable.
- **K2 D2 Eawag EQ added-record total.** D2 states 5,053 but its components 1,156 + 2,058 + 1,152 + 670 sum to 5,036
  (difference 17, UNRESOLVED). The three tagged components (4,366) agree within 2 with M-VERIFIED Eawag-EQ
  [M+H]+/[M-H]- records 2,939 + 1,425 = 4,364.
- **K3 D3's "newer" Exploris EQ5 sample is not post-snapshot.** 0 of D3's 188 files (e.g. `MSBNK-Eawag-EQ500051.txt`)
  are among the 7,490 post-2023.11 Eawag-family records (M-VERIFIED). D1 counts 184 six-digit EQ compound ids already
  at 2023.11. So D3's EQ5 sample and its "10/15 in MSG" figure belong to C03, and Exploris 240 NCE spectra are
  INFERRED to be in MassSpecGym training too. Confirm against the 2023.11 git tree.
- **K4 MUI NPS instrument.** D1 VERIFIED TripleTof 5600+ QTOF with `COLLISION_ENERGY 5 eV` in `MSBNK-MUI-NPS0001.txt`;
  D2 INFERRED Orbitrap from a La Sapienza paper. D1's direct record read prevails.
- **K5 Absolute eV claims on Orbitrap instruments.** ELIXDB (10/35/80 "eV", Exploris 120) and BOKU (10-100 "eV in
  absolute values", IQ-X): both instruments support absolute and normalized modes; unit AMBIGUOUS in both.
- **K6 MSnLib CE unit.** Nature Methods Methods text uses eV wording; MassSpecGym stores the integers unconverted and
  FIORA-OS and the feasibility audit treat them as NCE (D3). Relevant only to F1.
- **K7 Utrecht library.** Description says NCE 20, 30, 40; compound table says 30 for all 101 compounds (D2 VERIFIED).
- **K8 CASMI 2022 energies.** D2: single CE. D3: FIORA reports not all collision energies were found, suggesting
  several (INFERRED).
- **K9 BAFG post-2023.11 increment.** 875 files by file diff (D1, D2) versus "+646 spectra" in PR #275 (D1).
- **K10 NaToxAq CID values.** D1: CID 35% (789 records). D3 fragments: CID 40/50/90 % (nominal). Not load-bearing
  (CID not used).
- **K11 CyanoMetDB counts.** Paper: 2,905 spectra of 150 compounds (search snippet, D1). MassBank: 3,126 records
  (D2 release note; M-VERIFIED 3,126 rows). The 221-record gap is UNRESOLVED.
- **K12 Key definitions.** D1 and task M overlap use the recorded InChIKey first block; the MURU registry uses the
  parent connectivity key (p5 note section 1); D2's census used the parent key against MassSpecGym's recorded block.
  All overlap counts here are approximate until recomputed with `scaffold_key.py`, and no scaffold-group exclusion
  has been applied to any candidate.
- **K13 Exploris 240 spelling count.** D1 says three spellings; the 7,490 staged records show two
  (`Exploris 240 Orbitrap Thermo Scientific`, `Exploris 240 Thermo Scientific`). Not load-bearing.
- **K14 Domain limits.** D2 states ICEBERG/MSG limits of precursor m/z <= 1000 and MAX_ATOM_CT 160. Only the constant
  and MassSpecGym's 999.396 maximum are verified; enforcement at inference is UNRESOLVED.
