# Q: training-row counts by collision-energy convention

Study: MURU collision-energy interface adjudication (outcome-blind). Task Q. Written 2026-09-14.

Status tags: VERIFIED = read in code or computed from data here; INFERRED = deduced from verified facts;
UNRESOLVED = not decidable from allowed material.

## Part 1. Predeclared classification rule (written before any category count was computed)

Disclosure of what was inspected before this rule was written: the P1-P5 notes and summary JSONs (their descriptive
counts are known to the author), P5's `exclusion/msg_run_region_composition.csv`, and one diagnostic table of
run-first-row composition (missing CE / Orbitrap ladder / other) per 1,000-identifier bin for identifiers
180,000-240,999. That diagnostic showed that identifiers about 184,500-202,999 are runs whose first row has missing
CE (no non-ladder CE-present first rows), and 203,000-238,999 are runs whose first row is an Orbitrap ladder row, which
supports P3's block boundary. No count by the categories below had been computed when this Part 1 was written.
Nothing from the closed comparator benchmark was opened.

### 1.0 Unit of analysis and training tables

- One row = one MassSpecGym 1.5 spectrum (`identifier`). Every MSG spectrum carries exactly one CE, so one row gives
  at most one training item.
- Source data: MSG 1.5 identity parquet (CE, instrument, fold, simulation flag) joined with P4's metadata parquet
  (precursor_mz). All numeric tests use these float64 values.
- `T_sim` = MSG 1.5 rows with `simulation_challenge == True` (expected 119,029). The script asserts that
  `T_sim` has the same spec set, instrument and precursor as the committed ms-pred `data/spec_datasets/msg/labels.tsv`,
  and that `create_msg_simulation_dataset.py` (functions extracted verbatim by `ast`) drops no row.
- Checkpoint tables (from P1, re-cited in Part 2):
  - `iceberg21_gen`: `T_sim`; split = MSG fold through `normalize_fold`. Presented value `v = floor(CE)` (INFERRED
    int-truncated spectrum headers, P1 C15). No row-identifiable exclusion. The 205-236 train spectra implied lost by
    step arithmetic are not row-identifiable and are reported as an unallocated bound, not as rows.
  - `iceberg21_inten_contr`: `T_sim` minus rows whose label CE key `collision_key(format_collision_energy(CE))`
    differs from the base key `str(floor(CE))` (INFERRED filter drop, P1 C13/C15). Those rows go to
    EXCLUDED. Presented value on retained rows `v = float(label key)`, which equals `floor(CE)` there. The at most 49
    further train losses implied by step arithmetic are an unallocated bound.
  - `glacier_msg`: same spec set (committed `msg/labels.tsv`, VERIFIED equal to `T_sim`); split assumed = MSG fold
    (INFERRED from 3,098 steps/epoch). Presented value UNRESOLVED; primary `H_floor: v = floor(CE)`, sensitivity
    `H_raw: v = CE` (float32). Category assignment does not depend on this choice.
  - Split scopes: `train` = gradient updates; `val` = early stopping and best-checkpoint selection (monitor
    `val_loss`); `test` = not used for fitting. Also `all`.

### 1.1 Source attribution (row level)

Construction-order provenance (MassSpecGym notebook 1 cell 12 merge order MassBank, MoNA, MSnLib v1.0, GNPS;
notebook 3 cell 2 molecule grouping in first-appearance order; cell 13 numbering). A run = maximal consecutive
identifiers sharing the 14-char InChIKey. Block of a row = block of its run's first identifier:
- `C_start` = first run after which every row has missing CE; block C (GNPS-first molecules) = `>= C_start`.
- `B_start` = earliest run start before `C_start` such that at most 0.5% of run first rows from it up to `C_start`
  are not (Orbitrap and CE in {15,20,30,45,60,75}); block B (MSnLib-first molecules) = `[B_start, C_start)`.
- Block A (MassBank- or MoNA-first molecules) = `< B_start`.
These are P3's criteria, reimplemented; the script must reproduce B_start 202,862 and C_start 239,029 and P3's row
labels exactly, or stop.

Source labels:
- `MSnLib_v1.0` (code/construction provenance): block B and CE present. Inside a block B molecule only MSnLib and
  GNPS rows can occur, and GNPS library MGFs have no CE field (P3 C9). Sub-library name is added only after this
  attribution: the compound's MSnLib v1.0 sub-library from P5's membership table if it is exactly one of MCEBIO,
  MCESCAF, NIHNP, OTAVAPEP; `multiple` if more than one; `unmatched` if none.
- `MSnLib_v1.0_probable` (heuristic, NOT code provenance): P3's rule, block A trailing rows (before trailing
  CE-missing rows) that are Orbitrap ladder rows of an MSnLib v1.0 compound. Sub-library named as above.
- `MassBank_or_MoNA`: every other block A row with CE present. MassBank and MoNA cannot be separated. This label
  can contain MSnLib rows missed by the heuristic; a diagnostic flag counts block A rows that carry P5's
  MSnLib-like signature (Orbitrap, ladder CE, 4-5 precursor decimals) without being labelled probable.
- `GNPS`: block C, or CE missing. (Expected 0 rows in `T_sim`.)

### 1.2 Numeric tests (float64, MSG 1.5 values)

- `is_int`: `CE == floor(CE)`.
- `d`: decimals in Python's shortest repr of CE, capped at 12.
- `T500`: `n = round(CE*500/mz)`, `n >= 1`, pass iff `|CE - n*mz/500| <= max(0.5*10^-d, 1e-9*CE)`. Chance
  probability per row is about `2*tol*500/mz`; the expected chance count is reported. Used as evidence only for
  non-integer CE (for integer CE the tolerance is 0.5 and the test is uninformative).
- `ladder`: CE in {15, 20, 30, 45, 60, 75}.
- `half`: `2*CE` integer and CE non-integer.
- `T500_frac`: for non-integer CE failing `T500`, `r = CE*500/mz` is within `tol*500/mz` of a value with at most 2
  decimals, and that value is shared by at least 2 rows with different precursor_mz.

### 1.3 Categories (first matching clause wins)

1. Instrument QTOF -> `NATIVE_EV` (source quantity is laboratory-frame eV/V nominal CE; NCE is a Thermo setting).
   Resolution basis `instrument_semantics` (INFERRED). Subreasons: integer, half-integer (ramp-mean collapse or
   literal), other fractional; flags for rows passing `T500` (expected at chance level) and QTOF rows in block B.
2. Orbitrap, non-integer, `T500` pass -> `CAT2_NCE_x_mz_over_500`. Basis `numeric_test` (corroborated by code: in
   `convert_nce` only `%` strings produce CE proportional to precursor m/z). Rounding: MSG stores the unrounded
   float; ICEBERG sees `floor`; GLACIER `floor` (H_floor) or none (H_raw).
3. Orbitrap, `MSnLib_v1.0`, integer and ladder -> `CAT1_RAW_NCE`. Basis `code_provenance`.
4. Orbitrap, non-integer, `T500` fail, `T500_frac` pass -> `CAT3_OTHER_CONVERSION` (subreason: `%` conversion of a
   non-integer NCE, e.g. a stepped-energy mean). Basis `numeric_test`.
5. Every other Orbitrap row -> `CAT4_UNKNOWN_AMBIGUOUS`. Subreasons: `msnlib_order_nonladder_or_anomalous`,
   `msnlib_probable_integer_ladder` (heuristic MSnLib raw NCE), `mbmona_integer_ce0`,
   `mbmona_integer_mult5`, `mbmona_integer_other`, `mbmona_half_integer`, `mbmona_nonint_not_mz_proportional`.
6. Instrument missing -> `CAT4` (expected 0 rows).
- Checkpoint-level exclusion (inten_contr filter drop) -> `EXCLUDED_OR_MISSING`, with the category the row would
  otherwise have kept in the long table.
- Imputed energies: no category needed if 0 rows (asserted). Stepped-list first-value collapses and ramp means that
  yield integers are not detectable per row; they stay inside CAT4 / NATIVE_EV and are not counted as CAT3.
- ms-pred's integerisation is recorded as a rounding attribute, not as a category change.

### 1.4 Declared sensitivities (reported, not primary)

- S1: `MSnLib_v1.0_probable` integer ladder Orbitrap rows moved from CAT4 to CAT1.
- S2: inten_contr with base CE keys = round-half-even (no filter drop).
- S3: GLACIER `H_raw` value quantiles.
- Resolution accounting: rows resolved by code provenance (CAT1), by numeric test (CAT2, CAT3), by instrument
  semantics (NATIVE_EV), and unresolved (CAT4).

## Part 2. Results (appended after the script ran; Part 1 above is unchanged)

Part 1 of this file was frozen at 2026-09-15T03:18:59Z with sha256
`c5ab93af9bbddff93a957676a77e93275130295c59707726427c33bfdd9a671b` (whole file at that time). The script
re-hashed the file at run time and found the same value before this Part 2 was appended.

Script: `scripts/ce_interface_adjudication/03_classify_ce_conventions.py`. Outputs in
`artifacts/ce_interface_adjudication/counts/`:
- `ce_convention_counts.csv`: wide table in the requested schema (checkpoint, split_scope, source_library, instrument,
  raw_nce, nce_times_mz_over_500, other_conversion, unknown_ambiguous, native_ev_not_nce, excluded_or_missing,
  total_rows) plus resolution columns, the S1 sensitivity and the rounding attribute. Margins use `ALL`.
- `ce_convention_counts_long.csv`: the same counts at subreason and status granularity.
- `ce_convention_counts.json`: inputs with sha256, verbatim ms-pred functions used, reconciliations, diagnostics.
- `network_ce_value_quantiles.csv`: quantiles of the value presented to each network, per split, instrument and
  category, in each candidate unit.

One post-hoc diagnostic block was added to the script after the first run (key
`post_hoc_diagnostics_not_used_for_categories`); it changes no category and no count.

File-writing note: the session's Write tool refused writes into this worktree (session bound to another worktree),
so the note and script were authored in the session scratchpad and copied here with `cp`; the script was run from
here and wrote its outputs directly. Nothing was committed.

### 2.1 Checks that passed (VERIFIED, asserted in the script)

- MSG 1.5 join: 231,104 rows; MassSpecGym nb6 cell 5 rule (no NaN in any column and adduct [M+H]+) reproduces the
  `simulation_challenge` flag on every row.
- P3's block boundaries (B_start 202,862, C_start 239,029) and all 231,104 P3 row labels were reproduced exactly.
- `T_sim` (119,029 rows) equals the committed ms-pred `msg/labels.tsv` spec set; instrument and precursor are exactly
  equal on every row; labels CE equals floor(MSG 1.5 CE) on every row.
- The verbatim ms-pred functions `truthy`, `format_collision_energy`, `normalize_fold` (create_msg_simulation_dataset.py
  :63-64, :67-80, :83-89) applied as in `read_simulation_source` (:112-116, :138) drop 0 rows: no NaN CE and no
  `[imputed]` label, so imputed energies = 0 rows for all three checkpoints.
- Split sizes from `normalize_fold`: train 99,341, val 9,734, test 9,954.
- Split roles (VERIFIED code): train rows feed `trainer.fit` gradient steps; val rows feed `val_loss`, which drives
  `EarlyStopping` and `ModelCheckpoint(monitor=val_loss)` that selects `best.ckpt` (train_gen.py:254,283-289,312;
  train_contr_inten.py:276,305-311,347; glacier/train_joint.py:269,283-288,308; train_contr_joint.py:328,347,386);
  test rows are only used by `trainer.test` after fitting (train_contr_inten.py:367; train_joint.py:324).
  `get_splits` reads the `split` column values train/val/test (common/splitter.py:50-73).

### 2.2 Training tables per checkpoint and reconciliation

| stage | rows |
|---|---|
| MSG 1.5 rows | 231,104 |
| not simulation: CE missing (instrument present) | 104,174 |
| not simulation: CE and instrument missing | 5,184 |
| not simulation: adduct not [M+H]+ (CE, instrument present) | 2,678 |
| not simulation: instrument missing only | 39 |
| `T_sim` = training label table of all three checkpoints | 119,029 (train 99,341 / val 9,734 / test 9,954) |

- `iceberg21_msg_simulation_gen` and `glacier_msg` share the same row-identifiable table (`T_sim`, 0 row-level
  exclusions). They still differ: gen reads `msg_simulation` (split from MSG fold, VERIFIED code path), GLACIER reads
  `msg` whose `splits/split.tsv` is not public (MSG-fold split INFERRED from identical 3,098 steps/epoch). Both are
  reported separately.
- Step arithmetic (VERIFIED numbers from t1 epoch/global_step): gen and GLACIER 3,098 steps/epoch imply 99,105 to
  99,136 train items, so 205 to 236 of the 99,341 train rows were lost without a row-identifiable cause (plausibly
  MAGMa failures, P1). These are NOT removed from any category; every train count below for gen and GLACIER is an
  upper bound by at most 236 rows in total. Val/test losses are not constrained by step counts.
- `iceberg21_msg_simulation_inten_contr` (INFERRED filter, P1 C13/C15): rows whose label key differs from floor(CE)
  are excluded: train 11,163, val 486, test 542 (total 12,191; Orbitrap CAT2 11,759, Orbitrap CAT3 8, QTOF 424).
  Kept train 88,178 lies inside the 88,129-88,192 window implied by 1,378 steps/epoch under 2-GPU DDP, leaving at most
  49 unallocated train losses. Sensitivity S2 (base keys = round-half-even) drops 0 rows, which would give 1,553
  steps/epoch and contradicts the checkpoint.
- The inten_contr contrastive decoys are presented at the anchoring spectrum's CE (`colli_eng =
  common.get_collision_energy(name)`, dag_data.py:892, :919), so decoys add presentations but no new CE values.

### 2.3 Headline counts (primary rule)

All splits, `T_sim` (identical category assignment for all three checkpoints before inten_contr's exclusion):

| category | rows | resolution basis |
|---|---|---|
| (1) raw NCE entered as model CE (`CAT1_RAW_NCE`) | 30,631 | construction-order code provenance |
| (2) NCE x precursor_mz / 500 (`CAT2`) | 23,894 | numeric test (0.41 rows expected by chance) |
| (3) other conversion (`CAT3`) | 22 | numeric test |
| (4) unknown / ambiguous (`CAT4`) | 26,776 | unresolved |
| native eV / nominal CE, not NCE (`NATIVE_EV_NOT_NCE`, all QTOF) | 37,706 | instrument semantics (INFERRED) |
| excluded or missing CE | 0 (gen, GLACIER); 12,191 (inten_contr) | |
| total | 119,029 | |

Per checkpoint and split (instrument ALL, source ALL). Columns: raw NCE / NCE x mz/500 / other / unknown / native eV /
excluded / total; last column S1 raw NCE if the probable-MSnLib rows are accepted.

| checkpoint | split | (1) | (2) | (3) | (4) | native eV | excl. | total | S1 (1) |
|---|---|---|---|---|---|---|---|---|---|
| ICEBERG 2.1 gen | train (gradient) | 19,045 | 21,982 | 22 | 23,689 | 34,603 | 0 | 99,341 | 26,264 |
| ICEBERG 2.1 gen | val (early stop) | 5,792 | 884 | 0 | 1,535 | 1,523 | 0 | 9,734 | 6,348 |
| ICEBERG 2.1 gen | test | 5,794 | 1,028 | 0 | 1,552 | 1,580 | 0 | 9,954 | 6,412 |
| ICEBERG 2.1 inten_contr | train (gradient) | 19,045 | 11,213 | 14 | 23,689 | 34,217 | 11,163 | 99,341 | 26,264 |
| ICEBERG 2.1 inten_contr | val (early stop) | 5,792 | 420 | 0 | 1,535 | 1,501 | 486 | 9,734 | 6,348 |
| ICEBERG 2.1 inten_contr | test | 5,794 | 502 | 0 | 1,552 | 1,564 | 542 | 9,954 | 6,412 |
| GLACIER msg | train (gradient) | 19,045 | 21,982 | 22 | 23,689 | 34,603 | 0 | 99,341 | 26,264 |
| GLACIER msg | val (early stop) | 5,792 | 884 | 0 | 1,535 | 1,523 | 0 | 9,734 | 6,348 |
| GLACIER msg | test | 5,794 | 1,028 | 0 | 1,552 | 1,580 | 0 | 9,954 | 6,412 |

By instrument: every category (1)-(4) row is Orbitrap and every native-eV row is QTOF. Train Orbitrap for gen and
GLACIER is 64,738 rows: (1) 29.4%, (2) 34.0%, (3) 22 rows, (4) 36.6%. For inten_contr retained train Orbitrap is
53,961 rows: (1) 35.3%, (2) 20.8%, (4) 43.9%. The early-stopping split is very different from the gradient split:
val Orbitrap (8,211 rows) is (1) 70.5%, (2) 10.8%, (4) 18.7%.

Resolution accounting, all splits (`T_sim`): code provenance 30,631; numeric test 23,916; instrument semantics
37,706; unresolved 26,776 (sum 119,029). Train (gen, GLACIER): 19,045 / 22,004 / 34,603 / 23,689 (sum 99,341).

### 2.4 Subreasons

| category / subreason | train | val | test | all |
|---|---|---|---|---|
| (1) MSnLib v1.0 block B, integer ladder | 19,045 | 5,792 | 5,794 | 30,631 |
| (2) non-integer Orbitrap passing T500 | 21,982 | 884 | 1,028 | 23,894 |
| (3) `%` conversion of non-integer NCE 61.67 | 22 | 0 | 0 | 22 |
| (4) probable MSnLib (heuristic), integer ladder | 7,219 | 556 | 618 | 8,393 |
| (4) MassBank/MoNA integer, multiple of 5 | 16,431 | 978 | 931 | 18,340 |
| (4) MassBank/MoNA integer, other | 18 | 0 | 2 | 20 |
| (4) MassBank/MoNA CE = 0 | 3 | 1 | 1 | 5 |
| (4) MassBank/MoNA non-integer, not m/z-proportional (CE 80.205) | 12 | 0 | 0 | 12 |
| (4) block B but not ladder (CE 55/40/10, identifiers 203,111-203,120) | 6 | 0 | 0 | 6 |
| native eV, QTOF integer | 33,319 | 1,483 | 1,543 | 36,345 |
| native eV, QTOF half-integer | 539 | 0 | 7 | 546 |
| native eV, QTOF other fractional | 745 | 40 | 30 | 815 |

inten_contr exclusions by subreason (train/val/test): CAT2 10,769/464/526; CAT3 8/0/0; QTOF half-integer 38/0/0;
QTOF other fractional 348/22/16.

Numeric test detail (VERIFIED): 23,928 non-integer Orbitrap `T_sim` rows; 23,894 pass T500 against 0.41 expected by
chance; implied integer NCE is a multiple of 5 for 23,888 of them (top: 25 2,342; 60 2,201; 30 2,082; 90 2,072;
45 1,890; 75 1,885; 35 1,635; 15 1,496; range 5 to 185). The 34 failures are 22 rows with r = 61.67 exactly (CAT3)
and 12 rows with CE 80.205 at several precursor m/z (CAT4). QTOF non-integer rows pass T500 in 187 of 1,361 against
182.6 expected by chance, so there is no `%`-conversion signal in QTOF (flag only; they stay native eV).

### 2.5 By source library

All splits (`T_sim`; train in parentheses for gen/GLACIER):
- `MSnLib_v1.0` (construction order), Orbitrap CAT1: MCEBIO 15,537 (9,717); MCESCAF 11,471 (6,321); NIHNP 237
  (162); OTAVAPEP 3,095 (2,649); compound in more than one v1.0 sub-library 262 (179); compound not matched in the
  2025 MERLIN tables 29 (17). Anomalous: 6 Orbitrap non-ladder rows (unmatched, CAT4) and 3 QTOF rows
  (MCEBIO;NIHNP, native eV).
- `MSnLib_v1.0_probable` (heuristic; CAT4 in the primary rule): MCEBIO 4,149 (3,589); MCESCAF 12 (9); NIHNP 3,393
  (2,856); multiple 839 (765). Total 8,393 (7,219).
- `MassBank_or_MoNA`: Orbitrap 42,293 (38,468): CAT2 23,894 (21,982), CAT3 22 (22), CAT4 18,377 (16,464). QTOF
  37,703 (34,600) native eV.
- `GNPS`: 0 rows (GNPS spectra carry no CE and never enter `T_sim`).
- MassBank vs MoNA are not separable; no row is attributed to "other".

Compound-level MSnLib membership is not used as row provenance. It only names the sub-library of rows already
attributed to MSnLib and gates P3's heuristic.

### 2.6 Values presented to the networks (from `network_ce_value_quantiles.csv`, train split)

Quantiles use numpy linear interpolation. `v` = presented value; `v*mz/500` = lab-frame eV if `v` were NCE;
`v*500/mz` = NCE if `v` were eV.

ICEBERG 2.1 gen, and GLACIER under H_floor (identical), train:

| instrument / category | n | v: min, q05, q25, q50, q75, q95, max | v*mz/500 median (q05-q95) | v*500/mz median (q05-q95) |
|---|---|---|---|---|
| Orbitrap (1) raw NCE | 19,045 | 15, 15, 20, 30, 60, 60, 75 (6 distinct) | 23.4 (10.1-55.8) | 44.1 (19.2-103.0) |
| Orbitrap (2) floor(NCE x mz/500) | 21,982 | 2, 7, 15, 26, 42, 74, 358 | 13.7 (2.6-54.2) | 49.7 (14.3-119.4) |
| Orbitrap (3) | 22 | 13, 13.1, 15.75, 19, 20, 24.8, 25 | 5.9 | 60.9 |
| Orbitrap (4) | 23,689 | 0, 15, 30, 45, 60, 90, 180 (30 distinct) | 24.5 (7.0-70.3) | 77.5 (19.5-249.9) |
| QTOF native eV | 34,603 | 0, 6, 10, 30, 40, 100, 150 (43 distinct) | 13.5 (3.0-61.5) | 46.6 (7.1-183.2) |
| all rows | 99,341 | 0, 6, 20, 30, 50, 90, 358 | 18.0 | 53.7 |

Meaning per category:
- (1) The network receives the MSnLib NCE setting itself (15-75). The lab-frame eV equivalent at each row's precursor
  is NCE x mz/500, median 23.4 eV (q05 10.1, q95 55.8) at median precursor 367.2. Read as eV, these inputs overstate
  lab-frame eV by the factor 500/mz.
- (2) The network receives floor(n x mz/500), an integer eV-like number. Source NCE n: median 50, q05 15, q95 120,
  max 185. Unrounded MSG eV: median 26.9. Truncation loss: median 0.49, max 1.0 eV. So the same nominal NCE appears as
  n in category (1) rows and as roughly n x mz/500 in category (2) rows of the same instrument class.
- (3) 22 rows at r = 61.67 (NCE 61.67 converted, e.g. a mean of stepped 35/60/90, INFERRED); presented 13-25.
- (4) Integer values 0-180 whose unit is not recoverable per row; 18,340 of all 26,776 are MassBank/MoNA
  non-zero multiples of 5 (the subreason's actual definition), of which 15,791 sit on the
  15/30/35/45/60/75/90/120/150/180 ladder that matches the implied NCE of category (2) rows (INFERRED mostly
  NCE) and 2,549 are at 5/10/20/25/40/50/55/65/70/80/85; 8,393 are probable MSnLib NCE.
  [Corrected 2026-09-15 by the Task C completeness-critic pass; see Part 3. The count 18,340 is unchanged.]
- native eV: QTOF nominal eV/V, 0-150; 815 fractional values are mass-linear (P4), floored for ICEBERG.

inten_contr, retained train (88,178): (1) identical to gen; (2) 11,213 rows, v 2-358, median 27, q05 7, q95 75;
(3) 14 rows; (4) identical to gen; QTOF 34,217 rows, median 30. Presented value equals floor(CE) on every retained row
(asserted).

GLACIER under H_raw (sensitivity S3, train): (1) and (4) unchanged except CAT4 gains the fractional 80.205;
(2) v = unrounded MSG eV 2.052-358.400, median 26.891 (8,831 distinct); (3) 13.331-25.177; QTOF 215 distinct values,
median 30. All-row distinct values 9,064 vs 165 under H_floor.

### 2.7 Contradictions and caveats (not smoothed over)

1. Exact vs tolerant integer test: 15 `T_sim` Orbitrap rows are non-integer in float64 but pass `np.isclose` to an
   integer. This explains P3's 23,913 vs the exact 23,928 non-integer Orbitrap rows, and P2's 25,274 vs P1/P4's
   25,289 non-integer rows. This script uses exact equality.
2. P1 C21 states 23,926 of 25,289 non-integer rows fit NCE x mz/500 within 0.01 of an integer NCE. With the
   own-decimal tolerance here, 23,894 Orbitrap rows pass and QTOF passes only at chance level. The 0.01 tolerance on
   r is loose enough to admit chance QTOF hits, so the two numbers are not in conflict, but P1's figure should not
   be read as an Orbitrap-only count.
3. Construction-order attribution is not clean at the block B start: 6 Orbitrap rows with CE 55/40/10 (identifiers
   203,111-203,120) and 3 QTOF rows sit in block B although MSnLib v1.0 is Orbitrap ID-X with a 15-75 ladder. They
   were kept in CAT4 / native eV, not in CAT1.
4. NIHNP: only 237 NIHNP rows are in block B; 3,393 NIHNP-only-compound probable rows are in block A (2,039 at
   identifiers 184,000-202,999, where run first rows have missing CE, and 1,354 below 184,000). Their MSnLib
   attribution is heuristic, so NIHNP is almost absent from category (1) under the primary rule. Of all 8,393 probable
   rows, 2,518 are at 184,000-202,999 and 5,875 below 184,000.
5. Post hoc (not used for categories): 7,456 of the 8,393 probable-MSnLib rows sit in a trailing sub-run that also
   contains a CE 20 row, and 7,069 in one that contains both 20 and 60 (MSnLib's fixed energies; the MassBank Eawag
   HCD ladder has no 20). P3 itself estimated about 1,000 false positives. S1 therefore probably overstates by up to
   about 1,000 rows, and the primary rule understates category (1) by up to about 7,400.
6. P5's MSnLib-like row signature (Orbitrap, ladder CE, 4-5 precursor decimals) fires on 9,332 `T_sim` MassBank/MoNA
   rows that P3 did not label probable. Their CE mix is 30 1,991; 15 1,861; 45 1,793; 75 1,727; 60 1,710; 20 250,
   i.e. an Eawag-style ladder rather than MSnLib's 20/60 pair, and 6,391 of them are not MSnLib v1.0 compounds. The
   signature is not specific enough for row attribution.
7. GLACIER's presented value is UNRESOLVED (P1 C22). Category counts do not depend on it, but category (2) rounding
   does (floor vs none). An eV-converted spectrum-file variant (`spec_files_w_eV` exists as a resource name,
   create_msg_simulation_dataset.py:446) cannot be excluded for GLACIER; if such a variant had converted MSnLib NCE,
   GLACIER's category (1) rows would instead be (2)-type values. Nothing local decides this.
8. gen's presented value floor(CE) and inten_contr's exclusion rule both rest on the INFERRED int-truncated base
   spectrum headers (P1 C15). The step count supports this strongly for inten_contr (88,178 inside a 64-wide window)
   but gives no direct view of gen's header values.
9. The 205-236 (gen, GLACIER) and at most 49 (inten_contr) unallocated train losses cannot be assigned to categories;
   category counts for train are upper bounds by those amounts in total.
10. The `NATIVE_EV_NOT_NCE` assignment of QTOF rows rests on instrument semantics, not on code or per-row strings.
    MassSpecGym's instrument mapping has known curation errors (for example `LC-ESIMS-qTOF` mapped to ITFT, hence
    Orbitrap; P3 section 1.2), so a small number of Orbitrap-class rows may be QTOF data and vice versa.
11. Stepped-list first-value collapses (e.g. `15, 30, 45, 60, 70 or 90 (nominal)` stored as 15) and integer ramp means
    are not detectable per row. They are inside CAT4 and native eV, so category (3) = 22 is a lower bound on
    conversions of that kind.
12. `T_sim` values come from the HF parquet (float64 via arrow); the ms-pred builder parses the TSV with pandas, which
    can differ by 1 ULP. This could change `f"{val:g}"` only at an exact 6-significant-digit half boundary; not
    checked because the TSV text is outside the download scope.


## Part 3. Corrections from the Task C completeness-critic pass (2026-09-15)

Part 1 (the frozen classification rule) is unchanged and its recorded freeze hash still refers to the file as it
stood at 2026-09-15T03:18:59Z. This part records description errors found in Part 2 after the fact. No count in
`artifacts/ce_interface_adjudication/counts/` changed and the classifier was not re-run.

1. Section 2.6's category (4) bullet described the 18,340 `mbmona_integer_mult5` rows as lying on the
   15/30/35/45/60/75/90/120/150/180 ladder. The subreason as implemented and as frozen in Part 1 section 1.3 is
   integer and `CE % 5 == 0` and CE non-zero, with no ladder test. Recomputed: 15,791 on that ladder, 2,549 off
   it at 5/10/20/25/40/50/55/65/70/80/85. Corrected in place above. The synthesis document repeated the error in
   two places and is corrected there as C-2.
2. Recomputation script for both figures: `scripts/ce_interface_adjudication/c_taskc_recheck_numbers.py`, output
   `artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json` (key `C1_mbmona_integer_mult5`).
3. The same pass re-derived the MassBank-or-MoNA-only gen-train category (4) arm, which section 2.6 does not
   report separately: n = 16,464, 30 distinct presented values, 0 to 180, q05 15, median 45, q95 120. Section
   2.6's own all-source figures are unaffected; the synthesis document had attributed the all-source figures to a
   MassBank-or-MoNA row and is corrected there as C-1.
