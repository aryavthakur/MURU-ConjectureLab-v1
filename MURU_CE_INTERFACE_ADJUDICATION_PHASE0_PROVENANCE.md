# MURU collision-energy interface adjudication, Phase 0: provenance record

Status: PROVENANCE RECORD, outcome-blind. No convention has been selected. No execution is authorized by this document.
Branch: claude/muru-ce-interface-adjudication at 5b1c502. Nothing committed by this study.
Date: 2026-09-15.

Central question of the study: what collision-energy (CE) quantity do the public ICEBERG 2.1 and GLACIER MassSpecGym checkpoints actually encode, as a function of training source dataset and instrument, and which deployment mapping should be fixed before an independent evaluation. This document answers only the first half (what they encode). The choice of deployment mapping is deferred to Phase 1 to 3.

Evidence convention used throughout: VERIFIED means read in code or data and reproduced; INFERRED means derived by argument from verified facts; UNRESOLVED means not decidable from available material. Every load-bearing claim carries a file:line or URL.

---

## 1. Scope

| Item | Value |
| --- | --- |
| Checkpoints in scope | ICEBERG 2.1 generator (`iceberg21_msg_simulation/gen/best.ckpt`), ICEBERG 2.1 contrastive intensity model (`.../inten_contr/best.ckpt`), GLACIER MassSpecGym (`glacier_msg/best.ckpt`) |
| Upstream code | ms-pred clone at `/Users/aryav/muru-comparators/repos/ms-pred`, HEAD ed8311f, plus full git history |
| Training label table | MassSpecGym (MSG) 1.5 `simulation_challenge` subset, 119,029 rows; identical to the committed `ms-pred/data/spec_datasets/msg/labels.tsv` spec set |
| Phases executed | P1 pipeline trace, P2 model internals, P3 MSG curation, P4 metadata fetch, P5 exclusion linkage, Q quantitative counts, M candidate enumeration, S1 to S11 candidate screens, V verification (4 lenses: code trace, count reproduction, screen re-check, blindness and scope) |
| Out of scope | Any model prediction or inference; any selection of a deployment mapping; anything about the closed comparator benchmark's outcomes |

---

## 2. Blindness statement

### 2.1 What was forbidden and never opened

| Forbidden path | Opened? |
| --- | --- |
| `MURU_COMPARATOR_BENCHMARK_RESULT.md` | No |
| `artifacts/comparator_benchmark/result/` (anything) | No |
| `artifacts/comparator_benchmark/predictions/` (anything) | No |
| `artifacts/comparator_benchmark/prediction_verification/` (anything) | No |
| Any `*_spectra.json`, `*_preds.hdf5`, `*.mgf` model-output file under `artifacts/comparator_benchmark/technical/` | See disclosure D1 below |
| `/Users/aryav/muru-comparators/runs/` (anything) | No (see limitation L1) |
| Any MURU measured-mu, result or analysis output; any `*_RESULT.md` | No |
| GitHub PR bodies or comments for the comparator benchmark | No |

Verification lens v_blind enumerated every path literal in all committed scripts and grepped every authored artifact for these patterns. Every hit was a self-declaration of non-access. Evidence: `artifacts/ce_interface_adjudication/notes/v_blind.md`.

### 2.2 No model was run

No ICEBERG, GLACIER, FIORA or MURU prediction or inference of any kind was executed. VERIFIED three ways: (a) zero hits for `import torch`, `load_state_dict`, `load_from_checkpoint`, `.forward(`, `predict_smis`, `predict_gen`, `Trainer(`, `.eval()` across all committed scripts; (b) zero spectra or model-output files of any extension exist anywhere under `artifacts/ce_interface_adjudication` (full extension census in v_blind); (c) the checkpoint CE denominator tensors were re-derived by scanning the `.ckpt` zip members for 128-byte float blocks, without torch and without unpickling.

### 2.3 The exposed 1,327-compound benchmark was not used to choose, tune, validate or justify anything

No mapping choice exists in this study to contaminate: v_blind grepped every authored file for decision language (`we (recommend|adopt|choose|select|fix)`, `the (correct|right) (mapping|interface)`, `mapping should be`, `ADJUDICATION VERDICT`, `FINAL MAPPING`) and found zero matches. What was read from the benchmark tree, and only this:

| Artifact read | Columns or content used | Why permitted |
| --- | --- | --- |
| `artifacts/comparator_benchmark/population/common_population.csv` | `key`, `scaffold_group`, `model_smiles` only (never the `mh` column) | Identity-only key list, explicitly allowed for exclusion and overlap |
| `.../population/common_population_keys.txt` | The key list | Identity-only, explicitly allowed |
| `artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl` | Frozen hyperparameters (epoch, global_step, embed flags, lr) | Named in the task brief as already-extracted input |
| `MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md` | Interface definitions only (fixed Orbitrap ID-X HCD NCE 20 and 60, lines 18 and 219) | Explicitly allowed for interface definitions |
| `MURU_COMPARATOR_FEASIBILITY_AUDIT.md` | Interface definitions only (lines 106 to 107, 313) | Explicitly allowed; document is outcome-free |

The classification rule that produced every count in section 5 was written and frozen with a sha256 self-check (`c5ab93af9bbddff93a957676a77e93275130295c59707726427c33bfdd9a671b`, 2026-09-15T03:18:59Z) before a single count was computed, and the script re-checked that hash at run time.

### 2.4 Disclosures

| Id | Disclosure |
| --- | --- |
| D1 | During P5 an accidental `git grep` matched forbidden `technical/*_spectra.json` smoke-test files and previewed record header text only (example compound names, `collision_key`, `stored_collision_energy`). No peaks, no intensities, no benchmark-population predictions, no measured quantity was visible. The disclosure paragraph at `notes/p5_exclusion_linkage.md:17-24` itself reproduces four verbatim header fragments, including the pairing `"collision_key": "collision 10"` (eV files) against `"collision 20"` (raw-NCE files). That is interface-level information the task brief already states and carries no outcome; it is retained for transparency rather than redacted. |
| D2 | During the C03 screen, one exploratory GitHub commit-diff call returned whole newly added MassBank record files, which carried peak lines in memory. Only a per-line field-tag histogram was computed and printed; no peak value was stored, printed or used, and none of those records is in the screened 2023.11 accession set. |
| D3 | The C05 screen range-read a single supplementary xlsx zip member; that member also contains a plant-extract feature sheet with chromatographic peak areas. It was never parsed and the workbook was not persisted. |

### 2.5 Limitations of the blindness audit

| Id | Limitation |
| --- | --- |
| L1 | `/Users/aryav/muru-comparators/runs/` is forbidden, so it was not listed, stat-ed or grepped. The "no inference was run" claim rests on the absence of inference code and the absence of any model-output file in the study tree, not on inspection of where such output would land. A positive check requires an agent outside this study's blindness perimeter. |
| L2 | The P2 weight-column sub-claims (that the IT-FT, Unknown and non-[M+H]+ adduct input columns of `inten_contr` sit at about 4.9e-38) were not independently re-verified, because torch is unavailable in the audit interpreter and those numbers require mapping named parameters to storages. They stand on P2's own evidence. The instrument vocabulary and the training-label instrument composition were independently VERIFIED. |

---

## 3. Download register summary

Register: `artifacts/ce_interface_adjudication/downloads_register.jsonl`, 457 lines, 367.5 MB recorded in total, largest single transfer 49,520,118 bytes (under the ~50 MB per-file cap).

| Task tag | Lines | Task tag | Lines |
| --- | --- | --- | --- |
| P3 | 7 | S6-C06 | 15 |
| P5 | 7 | S7-C07 | 51 |
| S1-C01 | 12 | S8-C08 (+verify) | 15 (+3) |
| S2-C02 | 11 | S9-C09 (+verify) | 16 (+6) |
| S3-C03 (+verify) | 97 (+73) | S10-C10 (+verify) | 44 (+23) |
| S4-C04 | 30 | S11-C11 | 8 |
| S5-C05 | 13 | V-SYN-backfill | 10 |
| (untagged, P4 and early lines) | 16 | | |

Policy compliance:

| Check | Result |
| --- | --- |
| Hugging Face parquet range reads: bytes touching the `mzs` or `intensities` column chunks | 0 of 5,500,533 bytes, across all 1,395 ranges, against 464 forbidden intervals totalling 125,870,293 bytes. Independently recomputed by v_blind from the fetch record, not from its own summary |
| Columns fetched | `identifier`, `precursor_mz`, `parent_mass`, `formula`, `precursor_formula`, `smiles` only. 1,392 of 1,395 ranges name exactly one column (232 per column), so no coalescing across columns |
| Earlier `comparator_feasibility` identity fetch | 316 ranges, 4,314,135 bytes, 0 overlap with any spectra chunk; its ranges did coalesce across non-spectral columns, which P4 disclosed |
| Spectra files (MGF, MSP, mzML, mzXML, HDF5, raw, wiff) downloaded | 0. Extension census of the whole artifacts tree confirms none exists |
| Peak content in stored metadata | 0. All 52,485 GNPS LibraryServlet records have `peaks_json` = literal "null"; the two 46 to 50 MB GNPS processed CSVs have no peak column; MassBank code-search stores contain only `PK$SPLASH` (a hash) and `PK$NUM_PEAK` (a count), never peak triplets |
| Failed or discarded fetches | Disclosed in-register (two MassSpecGym fetch attempts, one PMC reCAPTCHA page, two PMC proof-of-work stubs) |

Register correction made by this synthesis: v_blind found 10 genuine network transfers with no register line (8 files under `artifacts/ce_interface_adjudication/d3_downloads/`, 2 PMC proof-of-work stubs under the C02 failed-attempts directory). All 10 have now been appended under task tag `V-SYN-backfill` with name, source URL, size and sha256. Two of the eight (`massbank_eu_metadata.json`, `massbank_eu_filter_browse.json`) carry a source URL marked INFERRED from the response body schema rather than logged at fetch time; two are DERIVED aggregates of several GitHub code-search calls whose per-call URLs were not logged. All ten are metadata only and none is referenced by any authored note, script or JSON, so nothing downstream depends on them.

---

## 4. Exact checkpoint-training CE provenance table

### 4.1 Checkpoint identity and training dataset

| Checkpoint | Result path recovered from the .ckpt pickle strings | ms-pred dataset | Warm start | Row table | Epoch / global_step | Steps per epoch |
| --- | --- | --- | --- | --- | --- | --- |
| ICEBERG 2.1 gen | `results/iceberg_msg_simulation/split_rnd1/ckpt/gen/best.ckpt` | `msg_simulation` | None (resumes own last.ckpt only) | T_sim, 119,029 rows | 16 / 52,666 | 3,098 |
| ICEBERG 2.1 inten_contr | `results/iceberg_msg_simulation/split_rnd1/ckpt/inten_contr/best.ckpt` | `msg_simulation` | `.../ckpt/inten/best.ckpt` (own base intensity model) | T_sim minus the CE-key filter | 5 / 8,268 | 1,378 (2-GPU DDP) |
| GLACIER msg | `results/joint_train_msg/split_rnd1/version_5/best.ckpt` | `msg` | Possible own joint base | T_sim (split INFERRED) | 23 / 74,352 | 3,098 |

VERIFIED: printable-ASCII scan of `archive/data.pkl` in each `.ckpt` zip, never unpickled. No NIST or other external pretrained weights were loaded (`train_gen.py:304-322`, `train_contr_inten.py:329-337`, `train_joint.py:318`, `train_contr_joint.py:364-380`). The experiment name `joint_train_msg` exists in the repository only between commits c792201 (2026-03-24) and 35a5aa3 (2026-07-06), which by itself excludes the earlier `labels_withev.tsv` configuration era for GLACIER (v_code correction, stronger than P1's original lr and max_breakpoints argument).

T_sim reconciliation from the full MSG 1.5 release, by first failing criterion of the MassSpecGym notebook 6 cell 5 rule (no NaN in any column and adduct `[M+H]+`):

| Stage | Rows |
| --- | --- |
| MSG 1.5 total | 231,104 |
| Excluded: CE missing | 104,174 |
| Excluded: CE missing and instrument missing | 5,184 |
| Excluded: adduct not [M+H]+ | 2,678 |
| Excluded: instrument missing | 39 |
| `simulation_challenge` = T_sim | 119,029 |
| Splits | train 99,341 / val 9,734 / test 9,954 |

T_sim equals the committed `msg/labels.tsv` spec set exactly (symmetric difference 0), with instrument equal on all rows, precursor exactly equal on all rows, and labels CE equal to `floor(MSG CE)` on all 119,029 rows.

### 4.2A Provenance table, part 1: source, counts, field, quantity

Row key is (checkpoint x training source library x instrument). Source attribution is by MassSpecGym construction order (identifier blocks), not by compound membership; see section 5.1.

| Row | Checkpoint | Source library | Instrument | Spectra (rows) | Rows actually used | Precursor adduct | Supplied CE field, source string format | Source quantity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | gen | MSnLib v1.0 (construction order) | Orbitrap | 30,637 | 30,637 | [M+H]+ | MGF header `Collision energy`, bare float, no unit | Instrument NCE setting, percent (fixed 20 and 60 plus one assisted energy from 15/30/45/60/75) |
| G2 | gen | MSnLib v1.0 | QTOF | 3 | 3 | [M+H]+ | as above | Anomalous, 3 rows, instrument disagrees with block (see U6) |
| G3 | gen | MSnLib v1.0 probable (heuristic) | Orbitrap | 8,393 | 8,393 | [M+H]+ | as above, INFERRED | Probably NCE percent, not resolvable per row |
| G4 | gen | MassBank or MoNA | Orbitrap | 42,293 | 42,293 | [M+H]+ | MassBank `AC$MASS_SPECTROMETRY: COLLISION_ENERGY`, free text: `N % (nominal)`, `N (nominal)`, `N(NCE)`, `N eV`, ramps, lists | Mixed. Percent strings are NCE; unit-free and `(nominal)` strings are unlabelled; a minority are lab-frame eV |
| G5 | gen | MassBank or MoNA | QTOF | 37,703 | 37,703 | [M+H]+ | as above, predominantly unit-free integers and `N V` titles | Lab-frame eV or volts (INFERRED from instrument semantics; NCE is a Thermo setting) |
| G6 | gen | GNPS | any | 0 | 0 | n/a | GNPS MGFs carry no CE field | n/a. All GNPS rows have NaN CE and are excluded from `simulation_challenge` by construction |
| I1 | inten_contr | MSnLib v1.0 | Orbitrap | 30,637 | 30,637 | [M+H]+ | as G1 | as G1 |
| I2 | inten_contr | MSnLib v1.0 | QTOF | 3 | 3 | [M+H]+ | as G2 | as G2 |
| I3 | inten_contr | MSnLib v1.0 probable | Orbitrap | 8,393 | 8,393 | [M+H]+ | as G3 | as G3 |
| I4 | inten_contr | MassBank or MoNA | Orbitrap | 42,293 | 30,526 (11,767 dropped) | [M+H]+ | as G4 | as G4 |
| I5 | inten_contr | MassBank or MoNA | QTOF | 37,703 | 37,279 (424 dropped) | [M+H]+ | as G5 | as G5 |
| I6 | inten_contr | GNPS | any | 0 | 0 | n/a | n/a | n/a |
| L1 to L6 | glacier | same six sources | same | same as G1 to G6 | same as G1 to G6 (0 excluded), split INFERRED | [M+H]+ | same as G1 to G6 | same as G1 to G6 |

inten_contr retained total: 30,637 + 3 + 8,393 + 30,526 + 37,279 = 106,838. Exclusions total 12,191 (train 11,163 / val 486 / test 542), all of them MassBank or MoNA rows. Mechanism in 4.2B.

### 4.2B Provenance table, part 2: transformations, fidelity, presented values

| Row | Loader-side transformations | Preprocessing-side transformations | Stored value matches field name? | Values presented to the network | Precursor m/z used in any energy conversion? | Internal CE transformation |
| --- | --- | --- | --- | --- | --- | --- |
| G1, G3 | `labels.tsv` CE column is DROPPED (`dag_data.py:505`); CE is read from the MAGMa tree (`dag_data.py:309-310`), which `create_msg_simulation_dataset.py:445-450` symlinks from the non-public `msg` directory | MassSpecGym parser (nb4 cell 9) left the value RAW because the source string contains no `%`; ms-pred then integerises it | No. The field is named `collision_energy` and carries no unit. It holds an unconverted NCE percent value | 6 distinct integers: 15, 20, 30, 45, 60, 75; median 30 (gen train n = 19,045) | No | 64-dim fixed sinusoid, no normalisation (section 6) |
| G2, G5 | as G1 | Parser left RAW (no `%`) | No. Holds a volts or eV number on the same numeric axis as G1's NCE | Integers 0 to 150, 43 distinct, q05 6, median 30, q95 100 (gen train n = 34,603) | No | as above |
| G4 | as G1 | Two arms of the SAME parser on ONE instrument class: strings containing `%` were converted as eV = NCE x precursor_mz / 500; every other string kept its first number raw. Ramps averaged; lists truncated to the first value; sign and exponent dropped | No. Converted rows hold a pseudo-eV; unit-free rows hold an unlabelled number. Both share one column | Converted arm (n = 21,982 gen train): 2 to 358, q05 7, median 26, q95 74, from source NCE median 50 (q05 15, q95 120, max 185). Unresolved arm, MassBank or MoNA only (n = 16,464 gen train): integers 0 to 180, 30 distinct, q05 15, median 45, q95 120. The all-source category (4) gen-train arm, which additionally holds 7,219 probable-MSnLib and 6 block B rows, is n = 23,689 with q95 90; that is the figure `network_ce_value_quantiles.csv` reports at `category = CAT4`, and it is NOT this row's arm | Yes, but only inside MassSpecGym curation, never in ms-pred. `nce_to_ev` and `ev_to_nce` have zero call sites in any MSG training path | as above |
| G6 | n/a | n/a | n/a | n/a | n/a | n/a |
| I1 to I5 | CE comes from `msg_simulation/labels.tsv` instead (`predict_gen.py:146,199-203`), parsed by `collision_energy_to_float` and rounded by `MassSpec` with `f'{x:.0f}'` (`misc_utils.py:57-61`) | Additionally, `add_dag_intens` keeps only spectra whose filtered subformula key CE matches the rounded label CE. On MSG 1.5 this silently drops 12,191 rows, all from the MassBank or MoNA sources | as the corresponding G row | Same as gen for the retained rows; the presented value equals `floor(CE)` on all 106,838 retained rows | No | as above |
| L1 to L5 | Same drop of the labels CE column; CE is read from the legacy JSON `magma_tree_with_inten.hdf5` (`glacier/dataset.py:150`), built by `run_scripts/glacier/add_inten.sh` from `magma_tree_new.hdf5` | Under the 3d08224-era writer, the tree stored `float(header.split()[1])` with NO rounding | as the corresponding G row | UNRESOLVED: `floor(CE)` (H_floor, primary) or the unrounded float (H_raw, live sensitivity). Under H_raw the converted arm presents 2.052 to 358.400, median 26.891, 8,831 distinct values | No | as above |

Two structural facts that the table above depends on:

1. No MSG training path converts CE. `nce_to_ev` and `ev_to_nce` are never called in `create_msg_simulation_dataset.py`, `run_magma.py`, `01_assign_subformulae.py`, `add_dag_intens.py`, `predict_gen.py`, `dag_data.py`, `glacier/dataset.py`, or any `train_*.py`. Their only call sites are the `msg_all` imputation script, `iceberg_atlas`, `iceberg_elucidation`, `iceberg_extract_fragments`, `graff_ms_data`, the webui, two notebooks and the tests. VERIFIED by repo-wide grep at HEAD ed8311f; the conversion constant is `misc_utils.py:2557` (`ev = nce * precursor_mz / 500`).
2. Imputed energies are 0 rows for all three checkpoints. `create_msg_simulation_dataset.py`'s `[imputed]` guard (lines 74 to 78) is unreachable because its label is derived from a float, and the row-level `[imputed]` filter matches nothing because the source column is MassSpecGym's numeric `collision_energy`. VERIFIED by executing the ms-pred functions verbatim over T_sim: 0 rows dropped. The `msg_all` imputation path, which does convert an NCE grid to eV with `int(nce_to_ev(nce, precursor))`, is provably not the dataset of any frozen checkpoint (its configs use `msg_known_ce` and `msg_all_iceberg`, which match neither the checkpoint pickle strings nor the step counts).

---

## 5. Quantitative convention counts

### 5.1 The predeclared rule

Frozen results-blind before any count was computed (`notes/q_counts.md` Part 1, sha256 `c5ab93af...`, 2026-09-15T03:18:59Z; re-checked at run time).

Unit: one MSG 1.5 `simulation_challenge` spectrum. Source attribution by construction order: MassSpecGym numbers spectra molecule by molecule in source first-appearance order (MassBank, MoNA, MSnLib v1.0, GNPS), giving identifier blocks. Block B (MSnLib-first) is [202,862, 239,029); block C (GNPS-first) starts at 239,029; block A (MassBank or MoNA first) is below 202,862. Numeric test T500: with `n = round(CE * 500 / mz) >= 1`, pass iff `|CE - n * mz / 500| <= max(0.5 * 10^-d, 1e-9 * CE)` where `d` is the decimal count of the shortest repr, capped at 12. Categories, first match wins:

| Order | Condition | Category | Resolution basis |
| --- | --- | --- | --- |
| 1 | QTOF | native eV, not NCE | Instrument semantics (INFERRED) |
| 2 | Orbitrap, non-integer, T500 pass | (2) NCE x mz / 500 | Numeric test |
| 3 | Orbitrap, MSnLib v1.0 by construction order, integer on the ladder {15,20,30,45,60,75} | (1) raw NCE | Code provenance |
| 4 | Orbitrap, non-integer, T500 fail, T500_frac pass | (3) other conversion | Numeric test |
| 5 | every other Orbitrap row | (4) unknown or ambiguous, with a named subreason | Unresolved |

Integerisation is recorded as a rounding attribute, never as a category. Sensitivities: S1 counts the heuristic probable-MSnLib rows as category (1); S2 uses a round-keyed base for `inten_contr`; S3 is GLACIER H_raw.

### 5.2 Headline counts, T_sim, all splits

| Category | Rows | Share | Resolution basis |
| --- | --- | --- | --- |
| (1) raw NCE | 30,631 | 25.7% | Code provenance |
| (2) NCE x precursor_mz / 500 | 23,894 | 20.1% | Numeric test |
| (3) other conversion (NCE 61.67 converted) | 22 | 0.02% | Numeric test |
| (4) unknown or ambiguous | 26,776 | 22.5% | Unresolved |
| native eV, not NCE (all QTOF) | 37,706 | 31.7% | Instrument semantics |
| GNPS rows | 0 | 0% | n/a |
| Total | 119,029 | 100% | |

Resolution basis totals: code provenance 30,631; numeric test 23,916; instrument semantics 37,706; unresolved 26,776.

### 5.3 Breakdown by source library and instrument, T_sim all splits

| Source library | Instrument | (1) raw NCE | (2) NCE x mz/500 | (3) other | (4) unknown | native eV | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MSnLib v1.0 (construction order) | Orbitrap | 30,631 | 0 | 0 | 6 | 0 | 30,637 |
| MSnLib v1.0 | QTOF | 0 | 0 | 0 | 0 | 3 | 3 |
| MSnLib v1.0 probable (heuristic) | Orbitrap | 0 | 0 | 0 | 8,393 | 0 | 8,393 |
| MassBank or MoNA | Orbitrap | 0 | 23,894 | 22 | 18,377 | 0 | 42,293 |
| MassBank or MoNA | QTOF | 0 | 0 | 0 | 0 | 37,703 | 37,703 |
| GNPS | any | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | | 30,631 | 23,894 | 22 | 26,776 | 37,706 | 119,029 |

Category (1) by MSnLib sub-library: MCEBIO 15,537, MCESCAF 11,471, OTAVAPEP 3,095, NIHNP 237, multiple sub-libraries 262, unmatched 29.

Category (4) by named subreason: MassBank or MoNA integer, nonzero multiple of 5, 18,340 (the frozen subreason is `CE % 5 == 0`, not ladder membership: 15,791 of the 18,340 sit on the {15,30,35,45,60,75,90,120,150,180} ladder that matches the implied NCE of category (2), and the other 2,549 are at 5, 10, 20, 25, 40, 50, 55, 65, 70, 80 and 85); probable-MSnLib integer ladder 8,393; MassBank or MoNA integer other 20; MassBank or MoNA non-integer not m/z-proportional 12; block B non-ladder or anomalous 6; MassBank or MoNA integer CE 0 5.

Native eV by subreason: QTOF integer 36,345; QTOF half-integer 546; QTOF other fractional 815.

### 5.3b The same breakdown for `inten_contr`, the one checkpoint whose table is not T_sim

5.3 is the breakdown for `gen` and for GLACIER, whose row tables are exactly T_sim. `inten_contr` drops 12,191
rows, so its by-source-and-instrument breakdown differs and is stated separately rather than left to be inferred
from 4.2A. Source of both tables: `artifacts/ce_interface_adjudication/counts/ce_convention_counts.csv`, which
carries all three checkpoints at this granularity.

| Source library | Instrument | (1) raw NCE | (2) NCE x mz/500 | (3) other | (4) unknown | native eV | Excluded | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSnLib v1.0 (construction order) | Orbitrap | 30,631 | 0 | 0 | 6 | 0 | 0 | 30,637 |
| MSnLib v1.0 | QTOF | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| MSnLib v1.0 probable (heuristic) | Orbitrap | 0 | 0 | 0 | 8,393 | 0 | 0 | 8,393 |
| MassBank or MoNA | Orbitrap | 0 | 12,135 | 14 | 18,377 | 0 | 11,767 | 42,293 |
| MassBank or MoNA | QTOF | 0 | 0 | 0 | 0 | 37,279 | 424 | 37,703 |
| GNPS | any | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | | 30,631 | 12,135 | 14 | 26,776 | 37,282 | 12,191 | 119,029 |

Reconciliation against 5.3: every exclusion is a MassBank or MoNA row, 11,767 Orbitrap (11,759 category (2) plus
8 category (3)) and 424 QTOF. Category (1) and category (4) are untouched, so the CE-key filter raises the raw-NCE
share of this checkpoint's Orbitrap rows from 30,631 of 81,323 (37.7%) to 30,631 of 69,556 (44.0%).

### 5.4 Per-checkpoint counts by split

| Checkpoint | Split (role) | (1) | (2) | (3) | (4) | native eV | Excluded | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gen | train (gradients) | 19,045 | 21,982 | 22 | 23,689 | 34,603 | 0 | 99,341 |
| gen | val (early stop, best-ckpt) | 5,792 | 884 | 0 | 1,535 | 1,523 | 0 | 9,734 |
| gen | test (not used for fitting) | 5,794 | 1,028 | 0 | 1,552 | 1,580 | 0 | 9,954 |
| gen | all | 30,631 | 23,894 | 22 | 26,776 | 37,706 | 0 | 119,029 |
| inten_contr | train | 19,045 | 11,213 | 14 | 23,689 | 34,217 | 11,163 | 99,341 |
| inten_contr | val | 5,792 | 420 | 0 | 1,535 | 1,501 | 486 | 9,734 |
| inten_contr | test | 5,794 | 502 | 0 | 1,552 | 1,564 | 542 | 9,954 |
| inten_contr | all | 30,631 | 12,135 | 14 | 26,776 | 37,282 | 12,191 | 119,029 |
| glacier | train | 19,045 | 21,982 | 22 | 23,689 | 34,603 | 0 | 99,341 |
| glacier | val | 5,792 | 884 | 0 | 1,535 | 1,523 | 0 | 9,734 |
| glacier | test | 5,794 | 1,028 | 0 | 1,552 | 1,580 | 0 | 9,954 |
| glacier | all | 30,631 | 23,894 | 22 | 26,776 | 37,706 | 0 | 119,029 |

Step arithmetic (bounds on unallocated rows): gen and GLACIER run exactly 3,098 steps per epoch, implying 99,105 to 99,136 training items against 99,341 row-identifiable rows, so 205 to 236 train rows were lost without a row-identifiable cause and the gen and GLACIER per-category train counts are upper bounds. `inten_contr` runs exactly 1,378 steps per epoch under 2-GPU DDP, implying 88,129 to 88,192 items; the CE-key filter leaves 88,178, inside that window, with at most 49 further losses. A round-keyed base would drop 0 rows and give 1,553 steps, which the checkpoint excludes.

Two observations that matter for deployment:

- The early-stopping split is not representative of the gradient split. Validation Orbitrap rows (8,211) are 70.5% raw MSnLib NCE, 10.8% converted, 18.7% unknown; training Orbitrap rows (64,738) are 29.4% / 34.0% / 36.6%. Best-checkpoint selection was therefore driven by a subpopulation that is predominantly raw NCE.
- The `inten_contr` exclusion is entirely CE-driven and entirely removes MassBank or MoNA rows, raising the raw-NCE share of that checkpoint's Orbitrap training data.

### 5.5 Reconciliation and the identification strength of each basis

| Basis | Rows | Strength |
| --- | --- | --- |
| Numeric test (categories 2 and 3) | 23,916 | Strongest. 23,894 of 23,928 non-integer Orbitrap rows satisfy CE = n x mz / 500 for integer n within own-decimal tolerance, against 0.41 rows expected by chance; n is a multiple of 5 in 23,888. QTOF non-integer rows pass at chance level (187 observed, 182.6 expected), so no QTOF row shows a conversion signal |
| Code provenance (category 1) | 30,631 | Strong but block-boundary dependent. Rests on MassSpecGym's merge and grouping order plus the fact that GNPS MGFs carry no CE field. 6 Orbitrap rows and 3 QTOF rows inside block B contradict pure MSnLib content and were deliberately left out of category (1) |
| Instrument semantics (native eV) | 37,706 | Weakest of the three. No per-row string or numeric evidence; rests on NCE being a Thermo setting. MassSpecGym's instrument mapping has known curation errors, and stepped-list first-value collapses cannot be detected, so category (3) = 22 is a lower bound on conversions |
| Unresolved (category 4) | 26,776 | Not resolvable per row with available material |

Bracket on the raw-NCE share, stated because the point estimate is not the right summary: 49,891 T_sim rows are Orbitrap integer rows on the MSnLib ladder {15, 20, 30, 45, 60, 75} (a different and narrower set than the ten-value MassBank ladder named in 5.3; 8,393 of them are probable-MSnLib and 10,867 are MassBank or MoNA), of which only the 30,631 in block B are classified raw NCE. So the true number of raw-NCE rows is at least 30,631 and at most 49,891, with the S1 sensitivity (39,024) inside that bracket. Post hoc and not used for classification: 7,456 of the 8,393 probable-MSnLib rows lie in a trailing sub-run containing a CE 20 row, and 7,069 contain both 20 and 60, MSnLib's fixed pair, which suggests the primary rule understates category (1) by several thousand rows while S1 overstates it by up to about 1,000.

Consequence worth stating plainly: roughly half the training table (37,706 native eV plus 26,776 unresolved, 64,482 rows, 54.2%) carries a CE unit that is asserted or unknown rather than demonstrated. The 23,916 numerically identified rows are the only part of the axis whose unit is proved. Any Phase 1 to 3 argument must weight these bases differently rather than treating the table as uniformly evidenced.

### 5.6 Independent count reproduction

An independent implementation of the frozen rule (`scripts/ce_interface_adjudication/verify_counts_independent.py`), written without reading the classifier, reproduced the tables exactly:

| Comparison | Result |
| --- | --- |
| Wide table (414 rows x 12 numeric columns) | 4,968 cells compared, 0 disagreements, 0 rows present in only one table |
| Long table, generator, split x category x subreason | 40 groups, 0 disagreements |
| `inten_contr` excluded-row subreasons | 12 groups, 0 disagreements, 12,191 total |
| Presented-value quantiles, generator train | 13 cells, 0 disagreements |
| Named checks overall | 39 run, 38 pass |

Resolution of the one failing check: it is not a count disagreement. The frozen rule's Part 1 prose clause "GNPS: block C, or CE missing" does not reproduce P3's own source taxonomy on 3,696 rows (2,169 non-trailing CE-missing block A rows that P3 labels MassBank or MoNA, and 1,527 CE-missing block B rows that P3 labels GNPS). Every one of those 3,696 rows has missing CE and is therefore outside T_sim and outside every training table, so materiality is zero and no count changes. Both scripts were read; the classifier is not wrong, it implemented P3's finer taxonomy rather than the literal prose of its own rule. The defect is in the frozen rule text, which is under-specified for CE-missing rows. No classifier fix and no re-run was warranted. Recorded here so that a later phase re-deriving source labels from the frozen text alone knows it will not match P3.

Two audit hypotheses were tested and REFUTED, which is a positive result for the counts:

| Hypothesis | Verdict | Evidence |
| --- | --- | --- |
| Compound-level MSnLib membership was used as row provenance | REFUTED | Deleting membership from the category-1 expression gives the identical 30,631 rows; 29 category-1 rows belong to compounds unmatched in the membership tables and are still counted; 45,330 rows carrying an MSnLib compound outside block B never reach category 1. Membership enters only to name sub-libraries of already-attributed rows and to gate the explicitly heuristic probable label, which the primary rule leaves in category 4 |
| Ambiguous integer rows were silently assigned to a resolved category | REFUTED | All 57,395 integer-CE Orbitrap rows are category 1 or 4, never 2 or 3. 56,426 integer rows pass the T500 arithmetic (uninformative at a 0.5 tolerance) and not one is assigned category 2. All 18,365 MassBank or MoNA integer Orbitrap rows stay category 4. The one declared assignment of ambiguous integers is the rule's own clause 1 (QTOF to native eV), which is labelled INFERRED |

A separate reconciliation of earlier phase counts: 15 T_sim Orbitrap rows are non-integer in float64 but `np.isclose` to an integer. That single fact explains P3's 23,913 against 23,928 and P2's 25,274 against P1 and P4's 25,289.

---

## 6. Model-internal CE handling and its numerical consequences

All three checkpoints are identical in CE handling.

| Property | Value | Evidence |
| --- | --- | --- |
| Encoding | 64 dimensions, 32 sin and 32 cos of `c / d_i`, `d_i = 10000^(2i/64)`, `i = 0..31` | `chem_utils.py:118-119`; `gen_model.py:140-160,283-295`; `inten_model.py:131-151,497-510`; `glacier/joint_model.py:137-147,270-284` |
| Denominators | Frozen, `requires_grad=False`, verified numerically against `10000**(2i/64)` at rtol 1e-5 by reading the checkpoint tensors directly | v_code re-derivation without torch: exactly one matching 128-byte member per checkpoint |
| Normalisation, scaling, clipping, log, bucketing, learned scale | None. The only operation is `c / d_i` then sin/cos in float32 | Forward code contains nothing else |
| Missing CE | ICEBERG: NaN maps to an all-zero 64-vector. GLACIER: a tree without the key defaults to 0.0, which receives the genuine embedding of zero (`[0]*32 + [1]*32`), not the unknown vector | `gen_model.py:289-290`; `inten_model.py:503-504`; `glacier/dataset.py:150`; `glacier/joint_model.py:277-278` |
| Injection point | Concatenated to every atom's input features (order: atom, adduct, CE, instrument). ICEBERG: root and fragment GNNs. GLACIER: Graphormer atom encoder only, never the attention bias | Input widths gen [512,136] = 46+22+64+4; inten_contr [256,122] = 32+22+64+4; GLACIER atom_encoder [256,178] = 88+22+64+4 |
| Precursor m/z in any CE conversion | Never. Accepted but unused in the ICEBERG forwards, used only as a ppm tolerance in the intensity losses, absent from GLACIER's forward | `gen_model.py:237` against body 263-403; `inten_model.py:762-788`; `glacier/joint_model.py:439-441` |
| Instrument vocabulary | `{Orbitrap: 0 (Orbitrap HCD), QTOF: 1, IT-FT: 2 (Orbitrap CID), Unknown: 3}`; `embed_instrument` true in all three | `chem_utils.py:277-283`; `checkpoint_hyperparameters.jsonl`. Training labels contain only Orbitrap (81,323) and QTOF (37,706), so the IT-FT and Unknown tokens carry no trained signal |

Numerical consequences:

| Consequence | Magnitude |
| --- | --- |
| No saturation, clipping or exact aliasing | Pairwise distance depends only on the difference: 0.5 gives 0.75, 1 gives 1.47, 5 gives 4.12, 40 gives 5.76, 300 gives 6.73, against a random-phase expectation of 8.0 and a maximum of 11.31. Near-alias dips at differences of about 5.95, 11.95 and 18.15 |
| Raw NCE and its eV conversion are far apart in embedding space | They differ by `NCE x (1 - mz/500)`, so they coincide only at precursor m/z 500. Example: NCE 20 at m/z 300 converts to 12 eV, and d(20, 12) = 4.38; d(20, 60) = 5.76 |
| Ordinal structure is weak | For differences up to 40, at least 98.9% of the squared distance comes from fast components that wrap within the training range. The slow monotone components contribute only 0.12 (20 against 12) and 0.60 (20 against 60). Nothing in the encoding enforces a monotone response to higher CE |
| Therefore | Any equivalence the models express between a raw-NCE input and an eV input must have been LEARNED from the mixed label axis, not supplied by the encoding. This is what makes the counts in section 5 the load-bearing evidence for the interface question, and it is why a single numeric CE input cannot be assumed to carry a unit the model would recognise |

A related upstream inconsistency, VERIFIED and worth carrying forward: every author instruction to convert Orbitrap NCE to eV (`nce=True`, NCE x precursor / 500) is attached to NIST-trained checkpoints, not to the MassSpecGym-trained ones. Neither the README nor any notebook documents the CE unit for ICEBERG 2.1 or GLACIER MSG weights. The authors' own scripts disagree with each other: the `msg_simulation` label builder passes MassSpecGym values raw, while the `msg_all` imputation script feeds eV to a model trained on MassSpecGym known-CE data. The published papers disagree too: the ICEBERG preprint encodes CE in eV, the MassSpecGym paper defines C in eV while its dataset section says 53% of entries contain normalized collision energies (that 53% equals the share of rows with any CE at all, so it does not mean NCE), and the GLACIER paper states only that CE is positional-encoded, with no unit.

---

## 7. What remains unresolved, and why

| Id | Unresolved item | Why it cannot be closed now | Impact |
| --- | --- | --- | --- |
| U1 | GLACIER's presented numeric CE (floor, raw float, or an eV-converted spectrum-file variant) | The MAGMa tree files carrying the training CE keys are not public. The code era that plausibly produced GLACIER's artifacts (3d08224) stored the RAW header float with no rounding, so H_raw is a live hypothesis, not a remote one. Textual evidence that eV-named variants existed in the authors' tree: `create_msg_simulation_dataset.py:446` symlinks a resource named `spec_files_w_eV`; `retrieval_benchmark_torchmetrics.py:234` reads `labels_withev_validinst.tsv` for dataset `msg`; the 3d08224 `run_magma.sh` pointed the subformula step at `spec_files_w_imputed_eV` | Category counts by source do NOT depend on it. Category (2) rounding does. Under an eV-converted variant, GLACIER's category (1) semantics would also change |
| U2 | What the non-public `data/spec_datasets/msg/spec_files.hdf5` headers actually hold | Not public | Would confirm the inferred `int(CE)` keying for ICEBERG directly rather than by step arithmetic |
| U3 | Which GLACIER stage and which labels file produced `joint_train_msg/split_rnd1/version_5` | Config history narrows it to `20250725_labels_spec_sim.tsv` or `labels.tsv`, not further | Does not change the CE path; needed for exact provenance |
| U4 | The unit of the 18,340 MassBank or MoNA integer Orbitrap rows whose CE is a nonzero multiple of 5 (15,791 of them on the {15,30,35,45,60,75,90,120,150,180} ladder) | Requires the raw MSP metadata strings at release 2023.11, which live inside record files that carry peak lists and are outside the download policy. Post-tag drift was bounded (only five commits since the tag delete any line, and in 1,200 sampled record patches every changed line is `CH$LINK`), but that is a bound, not a direct read | The single largest unresolved block, 15.4% of T_sim. Their ladder matches the implied NCE of the converted rows, so they are probably NCE, but not per row |
| U5 | The 8,393 probable-MSnLib rows | The MassSpecGym block boundary is empirical and the within-molecule order heuristic is approximate | Bracket in 5.5 |
| U6 | The 6 Orbitrap rows with CE 55/40/10 and the 3 QTOF rows inside block B | Contradict pure MSnLib content in that block | 9 rows, no material effect; kept out of category (1) |
| U7 | Whether MassSpecGym v1 (2024-08-20) carried the same CE values as 1.5 for the simulation rows | v1 metadata columns are outside the download scope | The committed `labels.tsv` predates the 1.5 upload, so it was presumably built from v1 with truncation |
| U8 | Whether the 205 to 236 training rows missing from gen and GLACIER (and up to 49 from inten_contr) were MAGMa, prediction or SMILES failures | Only bounded by step arithmetic | Makes the gen and GLACIER per-category train counts upper bounds |
| U9 | Where MassBank-first ends and MoNA-first begins below identifier 202,862 | No source column exists in MassSpecGym; no crisp signal in block composition | Prevents splitting the 42,293 MassBank or MoNA Orbitrap rows by depositor |
| U10 | Whether the frozen weights implement an instrument-conditional or mass-conditional reinterpretation of CE | Deciding it requires evaluating the models, even a partial forward pass, which this study forbids. Representability is established (elemental composition and the instrument token are inputs), realisation is not | Bears directly on whether a single deployment mapping can be correct for both instrument classes |

### 7.1 Latent code defects found during verification that a later phase should carry

| Id | Defect | Where |
| --- | --- | --- |
| N1 | `get_collision_energy` has a fallback that fires on any string containing a digit, so a header with no `collision` token receives a FABRICATED energy instead of `nan`. Probed: `get_collision_energy('ms2peaks')` returns `'2'`; `get_collision_energy('x_collision 45.0.json')` returns `'45'` | `chem_utils.py:740-755`, on the MAGMa path, `add_dag_intens.py:113`, and the contrastive decoy path `dag_data.py:892` |
| N3 | An undocumented `--collision-source {raw,labels}` switch changes the base subformula key from the spectrum header CE to the labels CE. HEAD run scripts never pass it, so the committed pipeline uses `raw`. Under `labels` with the committed floor-integer labels, the ICEBERG base-key conclusion follows with NO assumption about the non-public headers | `data_scripts/forms/01_assign_subformulae.py:59-66` |
| N6 | The generator is invoked at the UNROUNDED labels CE and only the result is wrapped in `MassSpec` and rounded. Where the two differ, the predicted fragment DAG was generated at one energy and supervised as if it were another | `predict_gen.py:246-252` against `262-264` |
| N7 | `train_contr_inten.py:319` and `glacier/train_joint.py:295` set `devices=torch.cuda.device_count()`, so items per optimizer step depend on the launch environment, not the config. Every step-arithmetic conclusion assumes the config's `visible_devices` was honoured. `train_gen.py:294` hardcodes `devices=1` and is exempt | as listed |
| N2 | The `msg_simulation` label writer formats non-integer CE with `f'{val:g}'`, six significant figures, so 358.40016 becomes `'358.4'`. A script-generated labels file does not round-trip the MassSpecGym float exactly | `create_msg_simulation_dataset.py:67-80` |
| N5 | `simulation_challenge` is computed on a 15-column frame and only later reduced to the 14 released columns, so the rule as written is not self-contained from the public file. It reproduces empirically on the released columns, which implies the dropped column had no nulls | MassSpecGym notebook 6 cells 5 and 9 |
| N8 | The committed scripts are not a faithful execution record: at 3d08224 `run_magma.sh` passes `--spectra-dir` to a subformula script whose argparse did not accept it, the README says `msg_simulation` links subformulae where the code filters them, and the `[imputed]` guard is unreachable | `3d08224 data_scripts/dag/run_magma.sh`; `README.md:167-169`; `create_msg_simulation_dataset.py:74-78` |

---

## 8. Corrections applied from verification

Every item below was refuted or corrected by a verification lens; the corrected version is what this document states.

| Item | Original phase claim | Correction applied here |
| --- | --- | --- |
| P1 C16 (subformula key suffixes) | INFERRED, argued from the consequence that otherwise intensity training would have had no data | Upgraded to VERIFIED with a direct justification: both key writers force a bare number, so a unit, percent sign or `[imputed]` marker cannot survive into a subformula key at HEAD |
| P1 C4 (intensity CE path) | Implied the generator and the intensity model see the same value | Order corrected: the generator is invoked at the UNROUNDED CE and rounding happens only at the `MassSpec` wrap, so the two can differ by up to 1 (defect N6) |
| P1 C8 (GLACIER labels file era) | Argued from lr 0.0004 and max_breakpoints 200 | Replaced by a stronger argument: the experiment name `joint_train_msg` exists only between c792201 and 35a5aa3, which excludes the `labels_withev.tsv` era on the checkpoint string alone |
| P1 C14 (GLACIER step window) | Depended on which config era produced the checkpoint | Strengthened: batch 16 on two devices and batch 32 on one both give 32 items per optimizer step, so the window does not depend on the config era |
| P1 C15 (base keys are int(MSG CE)) | Rested on the non-public spectrum headers | Better supported: the `--collision-source labels` route reaches the same conclusion with no assumption about the headers. Still INFERRED, because the step window is 64 items wide so 11,163 is not the unique drop count that fits |
| P1 C22 (GLACIER CE source) | UNRESOLVED | Stays UNRESOLVED and is sharpened: H_raw is a LIVE hypothesis because the plausible code era stored the raw header float (U1) |
| P1 C3 (labels CE column dropped) | As stated | Strengthened: `create_msg_simulation_dataset.py:445-450` symlinks the MAGMa outputs from the `msg` directory, and the labels-to-tree join uses `rm_collision_str`, which is CE-format agnostic, so gen and GLACIER lose no row to a CE mismatch |
| P3 C1 (MassSpecGym parser) | Described the `%` and ramp branches as alternatives | Three corrections: the ramp test also matches the literal `RAMP`; `normalized` and `ramped` are independent flags, so a string carrying both is averaged first and then multiplied by mz/500; the number regex matches no sign and no exponent, so negative or scientific-notation CE silently loses that information |
| P3 C14 (instrument mapping) | Cited matchms `known_key_conversions` and PickyDict | Qualified: notebook 1 cell 12 loads with `metadata_harmonization=False`, so matchms value harmonisation was OFF and the notebook 2 conversions dict plus notebook 4 prefix stripping do the work |
| P1 C1 (no conversion call sites) | Enumerated call sites | Claim stands; the enumeration omitted two notebooks and two `MassSpec` wrapper methods, none in a training path |
| Q section 2.1 (rule reproduces all 231,104 P3 labels) | As stated | Corrected: reproduction holds on all 121,746 CE-present rows; the frozen prose disagrees with P3 on 3,696 CE-missing rows, all outside T_sim (section 5.6) |
| Register completeness | "Every downloaded file recorded" | 10 transfers were unregistered; back-filled in this synthesis under tag `V-SYN-backfill` |
| Write scope | "Outputs only under the two authorized directories" | Three stray `.pyc` files under `src/muru/` were created by a P5 import; removed in this synthesis. No file outside the two directories is now modified |
| P1 and P2 delivery | Outputs stranded in a session scratchpad | Delivered into the worktree in this synthesis (section 9) |

Screen-level corrections are applied in the Phase 1 to 3 design document, section 2.

### 8.1 Corrections applied by the Task C completeness-critic pass

Re-check script: `scripts/ce_interface_adjudication/c_taskc_recheck_numbers.py`; output
`artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json`. It recomputes, from the same metadata
parquets the frozen classifier used, exactly those document-level numbers that are NOT a named field of the
counts artifacts, so they can be confirmed or refuted without trusting the prose. Patch script:
`scripts/ce_interface_adjudication/c_taskc_apply_fixes.py`, each edit an exact-string swap asserted to match
once. No count in `counts/` changed and no classifier was re-run; these are description errors, not count errors.

| Id | What was wrong | Correction |
| --- | --- | --- |
| C-1 | 4.2B row G4 is keyed to (gen, MassBank or MoNA, Orbitrap) but its "Unresolved arm" cell quoted n = 23,689 with q95 90, which is the ALL-source category (4) gen-train row of `network_ce_value_quantiles.csv` | The MassBank or MoNA Orbitrap unresolved arm is n = 16,464 (16,452 integer rows plus the 12 CE 80.205 rows), 30 distinct presented values, 0 to 180, q05 15, median 45, q95 120. Both figures are now stated, each labelled |
| C-2 | 5.3 and U4 described the 18,340 rows as being "on the {15,30,35,45,60,75,90,120,150,180} ladder". The frozen subreason is `mbmona_integer_mult5`, defined at `03_classify_ce_conventions.py:268` as integer and `CE % 5 == 0` and CE non-zero, with no ladder test | 15,791 of the 18,340 are on that ladder; 2,549 are at 5, 10, 20, 25, 40, 50, 55, 65, 70, 80 and 85. Both places corrected. The count 18,340 is unchanged and correct |
| C-3 | 5.5's "49,891 T_sim rows are Orbitrap integer ladder rows" uses `ladder` for the MSnLib set {15,20,30,45,60,75}, two paragraphs after 5.3 named a different ten-value ladder | The set is now named explicitly, with its 8,393 probable-MSnLib and 10,867 MassBank or MoNA parts. 49,891 is unchanged and correct |
| C-5 | The document gave a by-source-and-instrument table only for T_sim (that is, for `gen` and GLACIER) and a per-checkpoint table only by split, so `inten_contr`'s by-source-and-instrument breakdown had to be assembled by the reader from 4.2A | Added as 5.3b, taken from `ce_convention_counts.csv`, which already carried all three checkpoints at that granularity |

Numbers that the pass re-derived and CONFIRMED, listed because a critic's silence is not evidence: the whole of
5.2, 5.3 and 5.4 against `ce_convention_counts.json` (every cell); 49,891 and the 30,631 to 49,891 bracket; the
Orbitrap 81,323 / QTOF 37,706 split; the 5.4 validation-against-training composition (70.5 / 10.8 / 18.7 against
29.4 / 34.0 / 36.6, both reproduced to the stated decimal); the 4.2B presented-value quantiles for G1, G2, G4's
converted arm and GLACIER's H_raw arm (8,831 distinct, 2.052 to 358.400, median 26.891); section 3's register
totals (457 lines, 367,533,450 bytes, largest 49,520,118, every task-tag count) and its Hugging Face range
accounting; section 6's embedding distances, near-alias minima and band shares; and the ms-pred file:line
citations spot-checked at HEAD ed8311f (`misc_utils.py:2557`, `chem_utils.py:118-119`, `:277-283`, `:740-755`,
`misc_utils.py:57-61`, `dag_data.py:505`, `:309-310`, `:892`, `create_msg_simulation_dataset.py:67-80`,
`:445-450`, `glacier/dataset.py:150`, `01_assign_subformulae.py:59-66`, `predict_gen.py:146,199-203,246-252`).

Corrections C-6 to C-16 land in the Phase 1 to 3 design document and the preregistration outline and are recorded in the design document's section 2.4b. The C01 numbers behind them were re-derived by `scripts/ce_interface_adjudication/c_taskc_recheck_c01.py` into the same JSON under key `C01_screen_recheck`.

---

## 9. Files delivered by this synthesis

| Path | Content |
| --- | --- |
| `artifacts/ce_interface_adjudication/notes/p1_pipeline.md` | P1 pipeline trace (was undelivered) |
| `artifacts/ce_interface_adjudication/p1/p1_evidence.json` | P1 evidence (was undelivered) |
| `scripts/ce_interface_adjudication/p1_pipeline_evidence.py` | P1 script (was undelivered) |
| `artifacts/ce_interface_adjudication/notes/p2_model_internals.md` | P2 model internals (was undelivered) |
| `artifacts/ce_interface_adjudication/p2_checkpoint_ce_parameters.json`, `p2_ce_embedding_geometry.json`, `p2_msg_label_ce_boundary_check.json` | P2 outputs (were undelivered) |
| `scripts/ce_interface_adjudication/p2_read_checkpoint_ce_parameters.py`, `p2_ce_embedding_geometry.py`, `p2_msg_label_ce_boundary_check.py` | P2 scripts (were undelivered) |
| `artifacts/ce_interface_adjudication/notes/m_candidates.md`, `m_d1_recheck_summary.json`, `scripts/ce_interface_adjudication/m_01_recheck_d1_massbank_counts.py` | M candidate enumeration (was undelivered) |
| `artifacts/ce_interface_adjudication/downloads_register.jsonl` | 10 back-filled lines, now 457 lines |

P1 and P2 are now auditable from the worktree. Their no-inference and no-forbidden-file claims were previously unverifiable for exactly this reason, and remain self-reported for the period before delivery; limitation L1 still applies.
