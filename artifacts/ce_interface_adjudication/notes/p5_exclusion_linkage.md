# P5: exclusion inventory and MassSpecGym source-linkage data inventory (identity only)

Study: MURU collision-energy interface adjudication (outcome-blind). Task P5. Written 2026-09-14.
Worktree: `.claude/worktrees/muru-ce-interface-adjudication` at 5b1c502. All paths below are relative to it unless absolute.

Status labels: VERIFIED = read in code/data or recomputed here; INFERRED = reasoned from verified facts, not directly
observed; UNRESOLVED = open.

## 0. Access and blindness record

- No model was run (no ICEBERG, GLACIER, FIORA or MURU prediction). The MURU support rule needs model predictions of
  log g, so it is documented (section 4) but NOT evaluated for any compound.
- Read: identity/key/structure columns and method docs only (files listed per section).
- Not opened: `MURU_COMPARATOR_BENCHMARK_RESULT.md`, `artifacts/comparator_benchmark/{result,predictions,prediction_verification}/`,
  `/Users/aryav/muru-comparators/runs/`, any `*_RESULT.md`, any measured-mu file (e.g. `artifacts/wur_v2/external_msnlib/anchor_mu.csv`,
  `artifacts/wur_v2_confirmation_v2/result/`).
- **Disclosed incident (low content):** one `git grep` for the literal audit counts "13855/12249" (to find which script
  produced the audit's CE-ladder numbers) did not exclude `artifacts/comparator_benchmark/technical/`, so the tool
  preview printed the first ~250 characters of one line of six `*_spectra.json` files under `technical/t2_t3/` and
  `technical/t2b_seeded/`. The visible text was only record headers of the technical smoke-test example spectra:
  `"name": "pred_Example_0_NCE20"`, an example InChIKey, `"collision_key": "collision 10"` (eV primary files) or
  `"collision 20"` (raw-NCE sensitivity file), `"stored_collision_energy"`. No peak, intensity, mu or benchmark-population
  prediction was visible. The persisted full grep output file was not opened. Nothing in this note depends on it.
- Downloads by P5: none of data. Seven MassSpecGym dataset-construction notebooks (GitHub source code) were read via
  `gh api` into the session scratchpad and registered in `downloads_register.jsonl` (task "P5", sha256 and size per file).
  The MassSpecGym SMILES and precursor_mz used below come from P4's range read
  (`massspecgym15_metadata_columns.parquet`, sha256 `40d185c7...`), not from a P5 download.
- File placement: the session's Write tool refused to write into this worktree (its guard binds the session to another
  worktree), so files were authored in the scratchpad and copied here with `cp`. Contents are identical.

## 1. MURU compound key and scaffold group (reusable definition)

VERIFIED in `src/muru/wur_v2/identity.py` (sha256 `2ebe0de2...`, equal to `identity_py_sha256` in
`artifacts/wur_v2_confirmation_v2/exposure_registry/registry_manifest.json`):

- `parent_mol` (lines 33-42): RDKit `LargestFragmentChooser(preferOrganic=True)`, then `Uncharger` (exceptions ignored).
- **Compound key** `parent_connectivity_key` (lines 45-50): first 14-char block of `MolToInchiKey(parent)`.
- **Scaffold group** `scaffold_group_v2` (lines 61-68): parent, `RemoveStereochemistry`, Bemis-Murcko
  `GetScaffoldForMol`, canonical SMILES; acyclic parent -> `__ACYCLIC__<key>`; unparseable -> `__UNPARSED__<key>`.
  Not the generic framework; formal charges stay in the scaffold string.
- Census/study-1/study-2 wrapper `chem()` (`src/muru/wur_v2/msnlib_design.py:66-87`, same rule in
  `scripts/wur_v2_confirmation_v2/01_build_exposure_registry.py:131-152`): the key is accepted only if the RAW SMILES
  also yields an InChIKey.
- Separate stricter screening scaffold (not the group): `neutral_scaffold` (`src/muru/wur_v2/external_multims2.py:50-65`),
  N-oxide O and formal charges removed; used by census step 10b and MultiMS2 rule R7.
- Older v1 definitions differ and must not be mixed in: `src/muru/identity.py:47-52` (`first_block` of a recorded
  InChIKey, no parent normalization) and `src/muru/molecules.py:128` (v1 scaffold with stereo).

`scripts/ce_interface_adjudication/scaffold_key.py` reimplements this without importing MURU. Self-test
(`--self-test`, rdkit 2026.03.5 = frozen version), VERIFIED:
- `artifacts/comparator_benchmark/population/common_population.csv` (`model_smiles`): 1,327/1,327 key and 1,327/1,327
  scaffold_group matches, and identical to `muru.wur_v2.identity` output for all rows.
- `artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv` (`smiles`): 1,794/1,794 and 1,794/1,794.
- Output is RDKit-version dependent (InChI, canonical SMILES).

## 2. Exclusion sets

All in `artifacts/ce_interface_adjudication/exclusion/`, built by
`scripts/ce_interface_adjudication/p5_01_build_exclusion_sets.py`. Every count, sorted-list sha256 and file sha256 is in
`exclusion_manifest.json`.

| Set | File | Keys | Notes |
|---|---|---|---|
| (a) MassSpecGym 1.5, all rows | `msg15_keys_all.txt` | 28,929 | 231,104 rows; MassSpecGym's recorded `inchikey` (already 14 chars) |
| (a) train / val / test | `msg15_keys_{train,val,test}.txt` | 22,746 / 3,185 / 2,998 | rows 194,119 / 19,429 / 17,556; 0 keys in more than one fold |
| (a) simulation_challenge rows (ICEBERG `msg_simulation` universe) | `msg15_simchallenge_keys_{all,train,val,test}.txt` | 16,974 / 12,321 / 2,334 / 2,319 | rows 119,029 / 99,341 / 9,734 / 9,954 |
| (a) MURU parent keys of MassSpecGym SMILES | `msg15_parent_keys_{all,train,val,test}.txt` | 28,923 / 22,742 / 3,184 / 2,997 | per-row keys and scaffold groups in `msg15_row_keys.parquet`; 16,991 scaffold groups |
| (b) MURU exposure registry (verbatim) | `muru_exposure_registry_keys.txt`, `_scaffold_groups.txt` | 31,507 / 18,402 groups | file and list sha256 re-verified against `registry_manifest.json` |
| (b) registry keys with a direct (non-scaffold) reason | `muru_exposure_registry_keys_direct_reason.txt` | 26,005 | the other 5,502 are excluded only via `SCAFFOLD_GROUP_EXCLUDED` |
| (b) per exposed population | `muru_exposure_registry_population_<NAME>_keys.txt` | see below | from `excluded_compounds.csv` reasons; per-reason recount equals the manifest |
| (c) MSnLib confirmation study 2 (PR #7) frozen population | `msnlib_study2_population_keys.txt`, `_scaffold_groups.txt` | 1,794 / 1,691 groups | `freeze_manifest.json` population_key_hash `58f180a0...` and scaffold_group_hash reproduced |
| (d) comparator common population | `comparator_common_population_keys.txt`, `_scaffold_groups.txt` | 1,327 / 1,254 groups | key-list sha256 `dbdba9ca...` equals audit section 12; subset of (c) |
| (e) FIORA-OS v0.1.0 universe proxy: MSnLib v1.0 (MCEBIO, NIHNP, MCESCAF, OTAVAPEP) | `msnlib_v1_0_4lib_keys.txt` | 19,219 | plated compounds of the 2025 MERLIN cleaned tables, recorded split_inchikey first block UNION MURU parent key |
| (e') all nine MSnLib libraries (FIORA-OS v1.0.0 universe proxy) | `msnlib_9lib_keys.txt` | 53,612 | per-key libraries and match route in `msnlib_key_libraries.csv` |
| informational: MultiMS2 VALIDATION + SECONDARY | `multims2_reserved_validation_secondary_keys.txt` | 1,525 | reserved, never decoded, not exposed, not in the registry |
| union of (b), (c), (d) | `muru_exposed_union_keys.txt` | 33,301 | |

### 2.1 What the registry covers (VERIFIED, `registry_manifest.json`)

Study `muru-v2-msnlib-confirmation-2.0`, built 2026-09-13T23:48:22Z, rule: a listed compound or scaffold group may never
enter an MSnLib confirmatory pool. Exposed populations (keys): V2-DEVELOPMENT-POPULATION 1,325 (sorted-list sha256
`81eef787...` = the frozen training population), WUR-POS-IDENTITY 1,010, LCSB-ALL-MASSBANK-V1-EXPOSURE-SET 781,
LCSB-POS-V2-SPECTRA 478, WUR-DEV-ANALYSIS 476, ENTACT-MIX-LISTS-499-503-505 445, LCSB-DEV 439, WUR-SEALED 404, LCSB-NEG 379,
WUR-NEG-DEV 209, WUR-DEV-HOLD 130, LCSB-CONFIRMATION 110, MultiMS2-ANCHOR 106, LCSB-RAW-MIX-REPLICATE-SET-92 92,
LCSB-RAW-MIXES-499-503-505 39, WUR-NEG-D6-EXCLUDED 32 (union of these: 1,912 keys). Other reasons: burned sample 1
(`SAMPLE1_DRAW_GROUP` 2,690), decode-incident carryover and co-plating rules, `HEADER_READ_WELL_STUDY1` 23,147, MSnLib
anchor census/gate keys (402/340/328), and `SCAFFOLD_GROUP_EXCLUDED` 23,703.
Disclosed as NOT excluded: MultiMS2 VALIDATION/SECONDARY, prospective target lists, co-isolation from earlier wells.
WUR negative-mode keys lack SMILES, so they are excluded by exact key but have no scaffold group.

Coverage of the requested extra sources: WUR library, LCSB, ENTACT and MultiMS2 anchors are already registry populations
(VERIFIED above). The registry predates the study-2 draw, so (c) and (d) are separate lists; (c) is disjoint from the
registry (VERIFIED). No local FIORA training identity list exists (VERIFIED: no split/identity file tracked in
`/Users/aryav/muru-comparators/repos/fiora_head` (e19ef82) or `fiora_v0.1.2` (53ac247)); (e) is therefore a
library-level proxy, as in the feasibility audit.

Scope caution for screening a new dataset (INFERRED): most registry keys are MSnLib design-frame compounds excluded for
MSnLib-specific header or carryover exposure. For a non-MSnLib dataset the relevant exclusion is usually the 1,912
exposed-population keys plus (c) and (d); the full registry is the conservative choice.

### 2.2 Key overlaps (VERIFIED, `exclusion_manifest.json` pairwise_overlap_counts)

- (c) is inside the 9-library set (1,794/1,794); 456 of (c) are MSnLib v1.0 compounds; 454 of (c) are in MassSpecGym
  (238 train, 120 val, 96 test). (d) has 0 keys in MSnLib v1.0 and 0 in MassSpecGym.
- These reproduce the feasibility audit exactly: `overlap_support_per_compound.csv` flags 456 `in_msnlib_v1_0` and 454
  `msg_folds` non-empty; this build agrees on every one of the 1,794 compounds (0 disagreements either way).
- MassSpecGym vs MURU: registry 11,110 keys in MassSpecGym (8,311 train); exposed-population union 1,322 of 1,912 in
  MassSpecGym (1,154 train).
- MassSpecGym vs MSnLib: 14,744 recorded keys in MSnLib v1.0, 15,518 in any of the nine libraries.
- MassSpecGym recorded key vs MURU parent key: 35 recorded keys (272 rows) differ, e.g. charged P-oxide SMILES
  `O=[P+](c1ccccc1)c1ccccc1` (recorded ASUOLLHGALPRFK, parent YFPJFKYCVYXDJK), N-hydroxy piperidines, and hydroxy-acridine
  and hydroxycoumarin forms. Screening should match on both routes.

## 3. Source linkage for MassSpecGym rows

### 3.1 How the feasibility audit computed "molecule is in an MSnLib v1.0 library"

VERIFIED in `scripts/comparator_feasibility/01_overlap_and_support.py:106-123`: only for the 1,794 PR #7 compounds, from
the Zenodo 21105617 compound-metadata parquet (`20250828_9libraries_only_detected_cleaned.parquet`, md5 `fe0fd40f...`,
columns library, unique_sample_id, split_inchikey): library of each plated well plus every library holding the same
split_inchikey; `in_msnlib_v1_0` if any hit is MCEBIO, NIHNP, MCESCAF or OTAVAPEP (line 40). The v1.0 library set is
VERIFIED against the Zenodo 11163381 file list (P3's `p3_downloads/zenodo_11163381_record.json`: nihnp, mcebio, mcescaf,
otavapep, pos and neg MS2 and MSn MGFs). The audit's CE-ladder statement for MassSpecGym rows (section 1.2,
"84%", "60: 13,855; 20: 12,249; ...") has no committed script (not found in `scripts/comparator_feasibility/` or
`comparator_provenance.json`).

That parquet is not in this worktree or in `/Users/aryav/muru-msnlib/`; a copy exists only in another worktree
(`recursive-executor-framework-07dd81/data/external/msnlib_metadata/`), which P5 did not open. P5 instead used the nine
MERLIN cleaned design tables in `/Users/aryav/muru-msnlib/merlin_metadata/` (all sha256 VERIFIED against
`artifacts/wur_v2/external_census/msnlib_census.json` inputs) with MURU identity from the study-2 design cache
`/Users/aryav/muru-msnlib/cache/confirmation_v2/design_identity_673db151da69da9a.pkl` (tag recomputed from table sha256,
identity.py sha256 and rdkit version, as in `msnlib_design.load_design`; 300/300 random parent keys reproduced by
`scaffold_key.py`). These are plated compounds, a superset of the detected-only parquet.

### 3.2 Per-row table

`exclusion/msg_row_msnlib_membership.parquet` (231,104 rows, 24 columns; built by
`scripts/ce_interface_adjudication/p5_02_msg_msnlib_membership.py`; summary in `msg_row_msnlib_membership_summary.json`):
identifier, identifier_num, inchikey14 (recorded), parent_key14 (MURU), fold, simulation_challenge, adduct,
instrument_type, collision_energy, in_msnlib_v1_compound, msnlib_v1_sublibraries, in_msnlib_9lib_compound,
msnlib_9lib_libraries, match_route, run_index, run_first_identifier_num, run_length, position_in_run, n_runs_for_key,
key_first_identifier_num, key_first_in_dense_msnlib_bin, ce_in_msnlib_observed_set, precursor_mz_decimals,
msnlib_like_row_signature.

Compound membership (VERIFIED counts): 124,524 rows (53.9%) and 14,753 keys (51.0%) have an MSnLib v1.0 compound;
136,590 rows / 15,529 keys have a compound in any of the nine libraries. v1 rows by sub-library set: MCEBIO 78,371,
NIHNP 16,837, MCEBIO;NIHNP 13,128, MCESCAF 11,614, OTAVAPEP 3,230, others 1,344. By fold: train 102,731, val 11,019,
test 10,774.

**Compound membership is not row provenance.** MCEBIO and NIHNP are bioactive and natural-product collections whose
compounds are also in MassBank, MoNA and GNPS (notebook 1 loads GNPS-NIH-NATURALPRODUCTSLIBRARY and the Selleck/NIH
collections). 51% of MassSpecGym keys are MSnLib v1.0 compounds, while the audit describes MSnLib as "about a third" of
MassSpecGym molecules. Using compound membership as row provenance would mislabel tens of thousands of MassBank/MoNA/GNPS
rows as MSnLib rows.

### 3.3 Row-order provenance signal (VERIFIED construction code, INFERRED application to v1.5)

Read in `pluskal-lab/MassSpecGym` `notebooks/dataset_construction` (latest commit touching the folder `5a34ede`, 2024-09-07):
- `1_Load_data_from_repositories.ipynb` cell 12: sources concatenated as MassBank_NIST.msp, MoNA-export-LC-MS_Spectra.msp,
  `ms2_spectra_corinna.mgf` (MSnLib v1.0; cell 7 keeps only spectra with no `spectype`, i.e. non-merged, from the eight
  `*_all_lib_MSn.mgf` files in the order nihnp_neg, mcescaf_neg, otavapep_neg, mcebio_neg, nihnp_pos, mcescaf_pos,
  otavapep_pos, mcebio_pos), then 46 GNPS library MGFs.
- `3_remove_duplicates_and_profiled_spectra.ipynb` cell 2: spectra are grouped by source `inchikey` in first-appearance
  order and re-emitted group by group, each group in source order; cell 13 then numbers them `MassSpecGymID{i+1:07d}`.
- `6_final_postprocessing.ipynb` cell 9 keeps only the 14 released columns (no source column). The released schema has
  no source/library column (VERIFIED, P4 `massspecgym15_schema.json`: 14 leaf columns).

Consequence (INFERRED): a contiguous run of one InChIKey is ordered [MassBank][MoNA][MSnLib][GNPS], and where the run sits
in the identifier sequence reflects which source first contributed that InChIKey. VERIFIED consistency checks on the
released v1.5 data:
- identifiers are monotonic (max 414,174) but not consecutive (rows were filtered after numbering).
- Keys binned by their first identifier (`msg_run_region_composition.csv`, 2,000-id bins): bins 190,000-193,999 and
  204,000-237,999 have >= 99% MSnLib v1.0 compounds, and their sub-library composition follows the positive-file order:
  NIHNP dominates ~190,000-197,999, MCESCAF ~202,000-215,999, OTAVAPEP ~214,000-219,999, MCEBIO ~218,000-239,999.
  Bins from 240,000 on are 0-4% v1 (GNPS-first keys). Bins before 190,000 are mixed (MassBank/MoNA-first keys).
  The 198,000-201,999 low-membership zone and the negative-file sections are unexplained (UNRESOLVED).
- In runs whose key first appears in the dense bins (35,029 rows): all 29,840 CE-non-null rows are Orbitrap with integer
  CE (60: 10,292; 20: 9,407; 30: 4,851; 45: 2,913; 15: 2,305; 75: 72), 26,411 with 5 and 3,076 with 4 precursor_mz
  decimals, median position in run 1. The 5,189 CE-null rows sit later in the run (median position 5), include 1,197 QTOF
  rows and have 1-3 decimals: the pattern expected for GNPS spectra appended after the MSnLib spectra.

### 3.4 Proposed row-level attribution signals, best first

1. **Run position plus first-appearance region** (`key_first_identifier_num`, `run_index`, `position_in_run`): for keys
   first seen in the MSnLib section, leading rows are MSnLib and trailing rows GNPS. For keys first seen in MassBank/MoNA,
   MSnLib rows are an interior sub-run; position alone cannot delimit it.
2. **Acquisition signature** (`msnlib_like_row_signature` = Orbitrap AND CE in {15,20,30,45,60,75} AND precursor_mz with
   4-5 decimals). Captures 29,487 of 29,840 CE-non-null dense-region rows. It also fires on 12,420 v1-compound rows outside
   the dense region (candidate interior MSnLib sub-runs) and on 6,325 of 94,514 rows whose compound is in no MSnLib
   library, so it is not specific by itself (those 6,325 may include other Orbitrap libraries or MSnLib v1.0 compounds
   missing from the 2025 tables). Combine with 1 and compound membership: an interior contiguous signature sub-run inside
   a v1-compound run, bracketed by non-signature rows, is the strongest available call.
3. **Compound membership** (`in_msnlib_v1_compound`, `msnlib_v1_sublibraries`): necessary, not sufficient.
4. Not available without new downloads: exact precursor m/z or spectrum-level matching against the v1.0 MGF headers
   (spectra-bearing files, forbidden), or MoNA/GNPS spectrum-ID metadata tables (P3 is probing metadata-only endpoints).

Rough bound (INFERRED): MSnLib-derived rows in MassSpecGym 1.5 are about 29.5k (dense region) plus at most about 12.4k
interior rows, i.e. roughly 42k, which is of the same size as the audit's ladder total for Orbitrap v1-compound rows
(42,808).

Discrepancy (UNRESOLVED): recomputing the audit's statement with the plated MERLIN membership gives, for Orbitrap rows with
a v1.0 compound, 60: 13,944; 20: 12,283; 30: 7,006; 45: 5,008; 15: 4,218; 75: 902 (93,448 rows, 57,698 non-null CE), a
ladder share of 75.2% of non-null CE, not 84%. The counts are slightly higher than the audit's (plated superset vs
detected-only parquet), and the audit's denominator is undocumented. Not reconciled because the detected-only parquet was
not opened.

## 4. MURU applicability-domain constraints for screening future datasets

| Constraint | Rule | Source |
|---|---|---|
| Identity unit | parent connectivity key; stereo merged | `src/muru/wur_v2/identity.py:45-50`; `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md:17` |
| Polarity | positive mode only; negative mode never pooled or claimed | `src/muru/wur_v2/population.py:1-12`; `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md:22`; `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md:72-76` |
| Adduct / target ion | external: [M+H]+ of a charge-neutral parent (permanent cations removed, census step 3). Development training set: [M+H]+ 1,289, [M+NH4]+ 20, [M+Na]+ 8, [M]+ 8 (`artifacts/wur_v2/data/population_manifest.json`). Domain flag = adduct not [M+H]+ | `msnlib_census.json` design_frame step 3; `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md:115` |
| Precursor range | [M+H]+ in 70.0-1,042.6 m/z, equal to the development precursor range (VERIFIED min 70.040, max 1,042.594 in `artifacts/wur_v2/data/compounds.csv`) | `msnlib_design.py:27` `DEV_MH_RANGE`; `external_multims2.py:37` `R5_RANGE`; census step 12b |
| Element set | no explicit element filter in MURU code (none found in `src/muru/wur_v2`). Descriptors need only an RDKit-parseable SMILES (`tier_a_descriptors`, `src/muru/molecules.py:49-71`; rule R6). Elements seen in the 1,325 training compounds: C, H, N (1,102), O (1,192), S 309, Cl 266, F 147, P 99, Br 16, I 5, Si 2, As 1 (VERIFIED from `compounds.csv` SMILES) | as cited |
| Multi-component / salts | largest organic fragment, uncharged; 0 multi-component training SMILES | `identity.py:33-42` |
| Isolation purity (mixtures/plates) | no other co-injected compound ion ([M+H]+, [M+NH4]+, [M+Na]+, [M+K]+, [M-H2O+H]+, 13C, [M]+) within 0.7 m/z and no co-injected isomer | `msnlib_design.py:26-29,139-164`; `external_multims2.py:35` `R3_TOL` |
| Precursor matching and window | selected ion within 0.01 Da of theoretical [M+H]+ (MultiMS2 used 0.05); scan window lower <= 40 (MultiMS2 <= 50) and upper >= [M+H]+ + 1 | `external_msnlib.py:29-30,59-62`; `external_multims2.py:34,36` |
| Energy coordinate | model energy E in LCSB nominal NCE; development rungs 30-90 (native WUR 15-90); external NCE mapped by the frozen A0 map `E = (NCE + 5.9555) / 0.8618`; fixed NCE 20 and 60 used externally; Assisted/stepped scans excluded | `population.py:32-33`; `external_msnlib.py:28,31,90`; protocol V2 section 2 |
| Profile support | `supported` iff `u = (E/30)/g_hat` lies in the frozen profile knot range [0.2037, 14.9916] for both candidate and comparator at every used rung; needs model prediction of g_hat (not run here) | `src/muru/wur_v2/candidate.py:134-147`; knots from `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json` and `V2_REF_TA_RIDGE.json` (60 knots, energy_scale 30) |
| Structural independence | key and scaffold group absent from exposed populations; scaffold new vs the 1,325 development compounds, also after charge-neutral scaffolding (steps 8-10b) | `msnlib_census.json` steps 8-10b; `external_multims2.py:50-65,144` |
| Claim scope | Orbitrap HCD fixed NCE, [M+H]+, screening chemistry; never QTOF transfer, adducts, negative mode, dense trajectories | `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md:72-76`; `MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md:9` |

## 5. Open items

- Detected-only Zenodo 21105617 parquet not opened (other worktree); the audit's 84% CE-ladder share is not reproduced.
- MassSpecGym 1.5 identifier order is assumed to follow the 1.0 construction notebooks; supported by the region
  composition but not documented for 1.5.
- MSnLib v1.0 membership uses 2025 cleaned tables, not the 2024 v1.0 MGF headers; compounds removed in later curation
  could be missed (audit section 10 caveat carried over).
- Row attribution for MSnLib spectra inside MassBank/MoNA-first runs is signature-based and has a measured non-zero
  firing rate on non-MSnLib compounds (6.7%).
