# P4: MassSpecGym 1.5 metadata acquisition and descriptive CE distributions

Date 2026-09-14. Descriptive only; no convention verdict is made here. No spectra, no model outputs, no forbidden
file was opened. No ICEBERG, GLACIER, FIORA or MURU inference was run.

## 1. Fetch (script `scripts/ce_interface_adjudication/01_fetch_massspecgym_metadata_columns.py`)

- Re-read the prior fetch script `scripts/comparator_feasibility/02_fetch_massspecgym_identity.py` and its record
  `artifacts/comparator_feasibility/massspecgym15_identity_fetch_record.json`. New script reuses the same access pattern
  (HF parquet API `.../parquet/main/val/0.parquet`, one-byte probe, footer parse, pre-request refusal of any range that
  overlaps an `mzs`/`intensities` column chunk).
- VERIFIED same source object as the identity fetch: size 133,354,917 bytes, same CDN path / ETag
  `ee13e278...c528d86`, convert/parquet revision `0bced339751415306778d553dca97cfc2027ee86` (last modified
  2026-08-07T16:38:18Z), identical forbidden intervals (`same_file_as_identity_fetch` all true in
  `massspecgym15_schema.json`).
- VERIFIED full schema (footer, `massspecgym15_schema.json`): 231,104 rows, 232 row groups, 14 columns, created by
  parquet-cpp-arrow 22.0.0:
  `identifier` string, `mzs` string, `intensities` string, `smiles` string, `inchikey` string, `formula` string,
  `precursor_formula` string, `parent_mass` double, `precursor_mz` double, `adduct` string, `instrument_type` string,
  `collision_energy` double, `fold` string, `simulation_challenge` bool.
  There is NO source / library / database column in MassSpecGym 1.5. Source attribution cannot come from this file.
- Columns read: `identifier` (join key), `precursor_mz`, `parent_mass`, `formula`, `precursor_formula`, `smiles`.
  Bytes transferred 5,500,533 = footer tail 1,259,236 + byte-0 probe 1 + requested column chunks 4,241,296. The
  column-chunk bytes equal exactly the summed compressed sizes of the six columns (1,482,337 + 976,559 + 339,249 +
  416,060 + 526,337 + 500,754). 1,395 ranges, each classified; 1,392 are exactly one chunk of one requested column;
  0 overlap any forbidden interval. sha256 of transferred bytes (in order)
  `f6a3ea28a36ef3bd946c7852d31d5de3b64161c615a5b43281bc473c37f2699b`. Output
  `massspecgym15_metadata_columns.parquet` sha256 `40d185c7d1fbb3c0023714b5c6d1cd02f179679213162cc03c086dd40504e1f2`.
  Record: `massspecgym15_metadata_columns_fetch_record.json`.
- Disclosed fetch incidents (all in `downloads_register.jsonl`):
  1. Schema-only probe (footer only, 1,259,237 bytes) - succeeded.
  2. First full attempt with pyarrow default `pre_buffer=True`: the pre-request spectrum guard did not fire, but the
     post-hoc strict classifier failed because pyarrow coalesced adjacent chunks into single ranges that also covered
     unrequested NON-spectral columns (inchikey, adduct, instrument_type, collision_energy, fold,
     simulation_challenge; those are already held in the identity parquet). Output discarded; exact byte log not
     persisted. Note (VERIFIED from chunk offsets in this phase's record): the earlier identity fetch shows the same
     coalescing; its range 353680-369567 contains the row-group-0 chunks of formula (355152-356023),
     precursor_formula (356024-357571), parent_mass (357572-359515) and precursor_mz (359516-361459), so it too
     transferred bytes of non-requested non-spectral columns; never spectra.
  3. Second attempt (`pre_buffer=False`) aborted by a transient CDN TLS EOF. Output discarded; byte log not persisted.
  Fix: `pre_buffer=False`, per-range retry, and a failure path that registers the byte log of any failed run.
- Six register lines were written by this phase (2 probe, 2 manual failed-attempt notes, 2 final). Other phases append
  to the same register concurrently.

## 2. Join and cross-check (script 02, section "step 2"; `descriptive/p4_summary.json`)

- VERIFIED join exact: identity 231,104 rows, metadata 231,104 rows, inner join 231,104, 0 identifiers on either side
  only, identical row order. Nulls: collision_energy 109,358; instrument_type 5,223; no nulls in precursor_mz,
  parent_mass, formula, precursor_formula, smiles, inchikey. Joined table
  `massspecgym15_identity_metadata_joined.parquet` (sha256 `2e07c226...890b`).
- ms-pred `data/spec_datasets/msg/labels.tsv` (HEAD `ed8311f`, last touched by `648b061` "massspecgym weights +
  retrieval metrics update (#30)", sha256 `0b29f4b1...f244`): 119,029 rows, unique `spec`, dataset all MassSpecGym,
  ionization all `[M+H]+`, instrument Orbitrap 81,323 / QTOF 37,706, every `collision_energies` a one-element list.
- VERIFIED set equality: labels spec set == parquet `simulation_challenge == True` identifier set (119,029 both, 0 in
  either set difference; `descriptive/labels_vs_sim_subset_setdiff.csv` is empty). All 119,029 simulation rows have
  non-missing CE and `[M+H]+`. Fold of these rows: train 99,341, val 9,734, test 9,954.
- VERIFIED precursor: 119,029 / 119,029 exact float equality between labels `precursor` and parquet `precursor_mz`, and
  the labels string equals the shortest repr of the parquet double for all rows; max abs diff 0.0. 0 mismatches.
- VERIFIED instrument, adduct, inchikey (14-char), formula equal for all 119,029. SMILES strings differ in form for
  115,632 rows (labels Kekule, parquet aromatic) but RDKit canonical SMILES are equal for all 119,029 (0 parse failures).
- VERIFIED CE mismatch: 25,289 rows (Orbitrap 23,928, QTOF 1,361) differ between labels CE and parquet CE. These are
  exactly the 25,289 simulation rows whose parquet CE is non-integer. For ALL 119,029 rows, labels CE ==
  trunc(parquet CE) (floor, all values >= 0). Round-half would agree on only 13,098 of the 25,289. labels minus
  parquet on those rows ranges from -0.99975 to -0.000365, median -0.5. So labels.tsv stores integer-truncated CE;
  every labels CE string has 0 decimals. Rows listed in `descriptive/labels_vs_parquet_mismatches.csv`.
- INFERRED (provenance, not a verdict): labels.tsv at ed8311f was not written by
  `data_scripts/create_msg_simulation_dataset.py`'s `read_simulation_source` as committed, because that path formats CE
  with `f"{val:g}"` keeping decimals (lines 67-80) and writes a `collision_imputed` column (line 130), while labels.tsv
  has truncated integers, no `collision_imputed` column, and an `Unnamed: 0` column that is not the row number. That
  script also uses `f"{float(value):.0f}"` rounding for subformula keys (lines 202-206), a third convention. Which CE
  representation the checkpoints consumed (labels.tsv strings vs spectrum-file headers, cf. the `spec_files_w_eV`
  resource name at line 446) is not established here.
- No MSG split file exists locally under `data/spec_datasets/msg/` (only labels.tsv); fold was taken from the parquet.

## 3. Descriptive CE distributions (`descriptive/`)

Caveat on "stored value": the HF parquet holds float64 converted from the TSV text, so decimal counts are from the
shortest round-trip repr of the double, not the TSV text. Of 4,790 rows whose repr has >= 13 decimals, 4,419 lie within
1-3 ULP of a <= 12-decimal rounding (mostly 5-6 decimals, 1 ULP), which is consistent with either literal long text or
a non-correctly-rounded text parse; 371 are not within 4 ULP of any <= 12-decimal value
(`ce_long_repr_ulp_check.csv`).

Counts (`counts_instrument_simchallenge_cemissing.csv`, full cross-tab in
`counts_instrument_adduct_simchallenge_fold_cemissing.csv`):

| instrument_type | rows | CE missing | CE present, sim=True | CE present, sim=False |
|---|---|---|---|---|
| Orbitrap | 172,058 | 89,060 | 81,323 | 1,675 |
| QTOF | 53,823 | 15,114 | 37,706 | 1,003 |
| missing | 5,223 | 5,184 | 0 | 39 |

Integer vs non-integer (`ce_integer_decimal_counts_by_instrument.csv`, full value lists in
`ce_value_frequency_by_instrument.csv`):

- Orbitrap: 82,998 non-missing; 58,860 integer (32 distinct values), 24,138 non-integer (9,967 distinct). Repr
  decimals: 0: 58,860; 2: 3; 3: 76; 4: 489; 5: 4,468; 6: 13,532; 7-12: 822; 13-16: 4,748. Top integer values
  60: 15,272; 20: 12,571; 30: 8,572; 45: 6,513; 15: 5,638; 75: 2,226; 35: 2,167; 90: 2,106. 50,792 integer rows are in
  the audit reference set {15, 20, 30, 45, 60, 75}.
- QTOF: 38,709 non-missing; 37,348 integer (36 distinct), 1,361 non-integer (197 distinct), decimals 1: 847,
  2: 452, 5-7: 22, 14-15: 40. Top values 10: 7,055; 40: 6,275; 20: 5,935; 6: 4,339; 30: 4,207; 50: 3,071.
  All non-integer QTOF rows are simulation rows.
- instrument missing: 39 non-missing (30 integer, 9 non-integer).

Ratio r = CE * 500 / precursor_mz (`ratio_ce500_over_mz_near_integer_tests.csv`,
`ratio_nearest_integer_frequency_near_int_{d2,tight}.csv`, `ratio_distance_to_nearest_integer_histogram.csv`,
per-row `orbitrap_rows_ratio_tests.csv.gz`). Tolerance for a stored CE rounded to d decimals:
tol_d = 250 * 10^-d / mz + r * 5e-5 / mz + 1e-9; "tight" = |r - round(r)| <= 1e-6; "own" uses the row's own decimal
count (capped at 12). Chance = mean of min(1, 2 * tol). d=0 tolerance is uninformative (chance about 0.98 for
Orbitrap integer rows).

| subset | n | near d1 | near d2 (chance mean) | tight | own (chance mean) |
|---|---|---|---|---|---|
| Orbitrap integer CE | 58,860 | 9,420 | 989 (0.0155) | 5 (all CE = 0) | 57,800 (0.98) |
| Orbitrap non-integer CE | 24,138 | 24,110 | 24,106 (0.0195) | 24,104 | 24,104 (1.7e-5) |
| QTOF integer CE | 37,348 | 7,041 | 887 (0.0184) | 190 (all CE = 0) | 36,490 (0.97) |
| QTOF non-integer CE | 1,361 | 272 | 30 (0.0198) | 8 | 187 (0.134) |

- Orbitrap non-integer tight rows (24,104; 2,407 InChIKeys; 23,894 simulation rows): nearest integers are multiples of
  5 in 24,098 rows (5 to 185; the other 6 rows at 42); 10,255 rows fall on {15, 20, 30, 45, 60, 75}. Largest classes:
  25: 2,368; 60: 2,212; 30: 2,097; 90: 2,073; 45: 1,906; 75: 1,894; 35: 1,653; 15: 1,509. Within each class Pearson
  CE vs precursor_mz is 1.0 (by construction).
- The 34 Orbitrap non-integer rows not tight: 22 have CE/mz = 0.12334 exactly (r = 61.67), 12 have CE = 80.205
  constant across different precursor_mz (`ce_linear_fit_on_precursor_mz_by_decimals.csv`).
- QTOF non-integer rows show no excess over chance at d2 (30 vs 27.0 expected) or own tolerance (187 vs 182.6), but
  are strongly mass-associated: 2-decimal rows OLS CE = 0.0305 * mz + 16.93, resid sd 0.86, Pearson 0.980 (n 452);
  1-decimal rows CE = 0.0090 * mz + 26.81, resid sd 3.79 (n 847).
- Stored labels.tsv (truncated) CE: ratio tight-near-integer only for the CE = 0 rows (Orbitrap 5, QTOF 188).

CE vs precursor_mz correlation (`ce_precursor_mz_correlation_by_value_set.csv`, all folds, sim flag "all"):
Orbitrap all non-missing Pearson 0.088; integer CE -0.142 (n 58,860); non-integer CE +0.536 (n 24,138); integer in
{15,20,30,45,60,75} -0.064 (n 50,792). QTOF all -0.027; integer -0.031 (n 37,348); non-integer +0.440 (n 1,361).
Per stored CE value, precursor_mz min/median/max are in `ce_value_frequency_by_instrument.csv`.

labels.tsv stored CE quantiles (`mspred_msg_labels_ce_quantiles_by_instrument.csv`, full value list
`mspred_msg_labels_ce_value_frequency_by_instrument.csv`):

| instrument | n | distinct | q0 | q0.01 | q0.05 | q0.25 | q0.5 | q0.75 | q0.95 | q0.99 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Orbitrap | 81,323 | 192 | 0 | 6 | 12 | 20 | 32 | 60 | 90 | 150 | 358 |
| QTOF | 37,706 | 46 | 0 | 6 | 6 | 10 | 30 | 40 | 100 | 140 | 150 |

For comparison the untruncated parquet CE over the same rows: Orbitrap median 32.616, max 358.40016; QTOF median 30,
max 150.

## 4. Open items (not resolved in P4)

- Which CE field ICEBERG 2.1 / GLACIER training actually read (labels.tsv truncated integer vs spectrum-file headers
  vs another processed table) must be traced in code; P4 only shows labels.tsv truncates.
- MassSpecGym has no source column; source attribution for the integer vs converted Orbitrap populations has to come
  from external library metadata (other phase).
- The QTOF mass-linear non-integer values are unexplained descriptively.
