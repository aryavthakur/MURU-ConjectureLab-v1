# V: independent count reproduction (COUNT-REPRODUCTION lens)

Study: MURU collision-energy interface adjudication (outcome-blind). Task V. Written 2026-09-15.

Status tags: VERIFIED = read in code or recomputed from data here; INFERRED = deduced from verified facts;
UNRESOLVED = not decidable from allowed material.

## 0. Bottom line

Every convention count in Task Q reproduces exactly under an independent reimplementation of the predeclared
classification rule. 414 wide-table rows x 12 numeric columns = 4,968 cells, zero disagreements. 40 subreason groups
for the generator and 12 for the inten_contr exclusion, zero disagreements. 13 presented-value cells, zero
disagreements. No count differs.

One divergence was found, and it is not a count: the frozen rule text's clause for CE-missing rows
(`GNPS`: block C, or CE missing) does not reproduce P3's own label taxonomy on 3,696 rows. All 3,696 have missing CE,
so none is in `T_sim` and no count in any table changes. Details in section 5.

## 1. What was done and how independence was maintained

Script: `scripts/ce_interface_adjudication/verify_counts_independent.py`
(sha256 `e7e9bed1417ba14746a24086bae6e3198f90a0a68b0e97958f425c62550113ba`), written from scratch against Part 1 of
`artifacts/ce_interface_adjudication/notes/q_counts.md`.

- It does not import, exec, or copy `scripts/ce_interface_adjudication/03_classify_ce_conventions.py`, and that
  script's source was not read while writing or classifying. Its output tables
  (`counts/ce_convention_counts.csv`, `ce_convention_counts_long.csv`, `network_ce_value_quantiles.csv`) are read only
  at the end, to diff.
- Block boundaries, source labels, the ms-pred label/key functions, the numeric tests, the categories, the
  inten_contr exclusion and every aggregation were rewritten from the rule text. `format_collision_energy` and
  `collision_key` were retyped from `create_msg_simulation_dataset.py:67-80` and `:202-206` rather than extracted with
  `ast` as Q did, so the two implementations of that step are textually independent.
- Inputs (sha256 recorded in `counts/v_independent_counts.json`): MSG 1.5 identity parquet
  (`88e2fd1d...`), P4 metadata parquet (`40d185c7...`), P3 attribution parquet (`3eea7d36...`, labels compared
  only, never used as input to classification), P5 membership parquet (`94762079...`), ms-pred
  `data/spec_datasets/msg/labels.tsv` (`0b29f4b1...`).
- No model, no prediction, no download, no commit. No forbidden file was opened: nothing under
  `artifacts/comparator_benchmark/{result,predictions,prediction_verification}`, no `*_RESULT.md`, no
  `/Users/aryav/muru-comparators/runs/`, no measured-mu or analysis output.

Outputs: `artifacts/ce_interface_adjudication/counts/v_independent_counts.csv` (sha256 `e947256c...`, the same
414-row schema as Q's wide table) and `counts/v_independent_counts.json` (sha256 `d4bf5cec...`, 39 named checks, the
full diff record, and the diagnostics quoted below).

## 2. Reproduced counts

### 2.1 Upstream reconstruction (VERIFIED, all recomputed here)

| item | value | agrees with Q |
|---|---|---|
| MSG 1.5 rows after joining identity and metadata parquets | 231,104 | yes |
| `simulation_challenge` reproduced from nb6 cell 5 rule (no NaN, adduct [M+H]+) | 119,029, 0 disagreements | yes |
| block boundaries re-derived from rule 1.1 | `B_start` 202,862, `C_start` 239,029, 31,885 runs | yes |
| P3 row labels reproduced on every CE-present row | 121,746 rows, 0 disagreements | yes |
| `T_sim` equals committed `msg/labels.tsv` spec set | 119,029, symmetric difference 0 | yes |
| labels CE equals floor(MSG CE); instrument and precursor equal | 119,029 / 0 mismatches / 0 mismatches | yes |
| `format_collision_energy` drops rows on `T_sim` | 0 (so imputed energies = 0 rows) | yes |
| split sizes through `normalize_fold` | train 99,341 / val 9,734 / test 9,954 | yes |
| stage table (Q section 2.2) | 104,174 / 5,184 / 2,678 / 39 / 119,029, sum 231,104 | yes |

### 2.2 Headline categories, `T_sim`, all splits (VERIFIED, identical to Q section 2.3)

| category | rows |
|---|---|
| (1) raw NCE (`CAT1_RAW_NCE`) | 30,631 |
| (2) NCE x precursor_mz / 500 (`CAT2`) | 23,894 |
| (3) other conversion (`CAT3`) | 22 |
| (4) unknown / ambiguous (`CAT4`) | 26,776 |
| native eV, all QTOF (`NATIVE_EV_NOT_NCE`) | 37,706 |
| total | 119,029 |

Per checkpoint and split, per instrument, per source library (including the MSnLib sub-library partition
MCEBIO 15,537 / MCESCAF 11,471 / NIHNP 237 / OTAVAPEP 3,095 / multiple 262 / unmatched 29), the resolution columns
and the S1 sensitivity column: all 4,968 numeric cells agree. The key sets of the two tables are identical, so no row
exists in one table and not the other.

### 2.3 Subreasons and the checkpoint layer (VERIFIED)

- Subreason groups for `iceberg21_msg_simulation_gen` at split x category x subreason granularity: 40 groups,
  0 disagreements (for example probable-MSnLib 8,393; MassBank/MoNA integer multiple of 5 18,340; MassBank/MoNA
  integer other 20; CE 0 five rows; non-m/z-proportional 12; block B non-ladder 6; QTOF integer 36,345, half-integer
  546, other fractional 815).
- inten_contr exclusion: 12,191 rows (train 11,163, val 486, test 542), by category CAT2 11,759, CAT3 8,
  QTOF native eV 424. 12 groups compared, 0 disagreements. Kept train 88,178, inside the 88,129 to 88,192 window
  implied by 1,378 steps/epoch. Sensitivity S2 (round-half-even base keys) drops 0 rows, as Q reported.
- Presented value on retained inten_contr rows equals floor(CE) on all 106,838 rows (asserted here).
- Numeric-test detail: 23,928 non-integer Orbitrap rows, 23,894 pass T500 against 0.4060 expected by chance;
  implied NCE is a multiple of 5 in 23,888; QTOF 187 passes against 182.5707 expected by chance. Q's rounded
  0.41 and 182.6 reproduce. The exact-versus-`isclose` caveat reproduces at 15 rows.
- Presented-value spot check against `network_ce_value_quantiles.csv` (generator, as_trained, train,
  quantity `presented_value (eV if read as eV)`): 13 cells of n, n_distinct, min, q50, max, 0 disagreements.
  For example category (1) n 19,045 with 6 distinct values 15 to 75; category (2) n 21,982, min 2, median 26,
  max 358; all rows n 99,341, 165 distinct values, max 358.

## 3. Audit A: compound-level MSnLib membership was not used as row provenance

VERIFIED, four independent checks:

- A1. Recomputing `CAT1_RAW_NCE` from the block rule alone (Orbitrap, block B, CE present, integer, ladder), with
  P5's `in_msnlib_v1_compound` deleted from the expression, gives exactly the same 30,631 rows. Difference 0 rows.
- A2. 29 of those 30,631 rows belong to compounds that are not matched in P5's MSnLib v1.0 membership tables and are
  still counted as category (1). If membership were gating the category, those rows would have been dropped. This is
  the same 29 rows Q reports as sub-library `unmatched`.
- A3. 75,935 `T_sim` rows carry an MSnLib v1.0 compound, but only the 30,605 of them in block B can reach
  category (1), and 30,602 do (3 are QTOF). Not one of the 45,330 MSnLib-compound rows outside block B is assigned
  category (1).
- A4. The heuristic label `MSnLib_v1.0_probable`, which is the one place where compound membership enters the row
  labelling, carries 8,393 `T_sim` rows and every one of them is `CAT4_UNKNOWN_AMBIGUOUS` in the primary rule. It
  changes the primary counts only through the separately reported S1 sensitivity.
- A5. The sub-library names (MCEBIO and the rest), which do come from compound membership, only partition already
  attributed rows: summing the per-sub-library rows reproduces the `ALL` margin exactly for every checkpoint.

## 4. Audit B: ambiguous integer rows were not silently assigned

VERIFIED:

- B1. Of 57,395 integer-CE Orbitrap rows in `T_sim`, every one is either `CAT1_RAW_NCE` (30,631) or
  `CAT4_UNKNOWN_AMBIGUOUS` (26,764). None reaches CAT2 or CAT3.
- B2. 56,426 integer-CE Orbitrap rows pass the T500 arithmetic, which at a tolerance of 0.5 is uninformative for
  integers. None of them is assigned CAT2: they split 30,174 CAT1 and 26,252 CAT4. The rule's restriction of T500 to
  non-integer CE is therefore load-bearing and was honoured.
- B3. `CAT4` and the resolution basis `unresolved` are the same set of rows in both directions.
- B4. Every CAT4 row carries a named subreason. No residual or unnamed bucket exists.
- B5. All 18,365 MassBank/MoNA integer Orbitrap rows stay CAT4, including the 18,340 non-zero multiples of 5,
  15,791 of which sit on the same ladder as the implied NCE of the converted rows (the other 2,549 are at
  5/10/20/25/40/50/55/65/70/80/85). [Ladder clause corrected 2026-09-15 by the Task C completeness-critic
  pass; the check and its counts are unchanged.]
- C1. No `T_sim` row has a missing instrument, so the CAT4 fallback for missing instruments is 0 rows as Q expected.
- C2. 19,260 block A Orbitrap integer ladder rows (8,393 labelled probable, 10,867 labelled MassBank/MoNA) stay in
  CAT4 even though their CE values are on the MSnLib ladder. That is the rule's declared conservatism and it is
  applied without exception.

One assignment of ambiguous rows is made by the rule itself and should not be read as resolved: 36,345 integer-CE
QTOF rows are placed in `NATIVE_EV_NOT_NCE` by clause 1 on instrument semantics alone (INFERRED), not by any per-row
string or numeric evidence. Together with 546 half-integer and 815 other fractional QTOF rows that is 37,706 rows,
31.7% of `T_sim`, resting on one inferred premise. Q labels this INFERRED in the rule and repeats the caveat at
section 2.7 item 10; this reproduction does not add evidence for or against it.

## 5. The one divergence found (not a count)

Rule text 1.1 defines `GNPS` as "block C, or CE missing". Implementing exactly that and crosswalking to P3's label
vocabulary disagrees with P3's `source_label` on 3,696 of the 231,104 rows:

- 2,169 rows that P3 labels `MassBank_or_MoNA` have missing CE. P3 assigns `GNPS_or_MoNA_missing_ce` only to
  *trailing* CE-missing rows of a block A run (`scripts/ce_interface_adjudication/p3_msg_source_attribution.py:24,115`),
  so non-trailing CE-missing block A rows keep the MassBank/MoNA label.
- 1,527 CE-missing rows in block B, which P3 labels `GNPS`.

Decomposition check: P3's `MassBank_or_MoNA` 84,298 = my 82,129 CE-present rows plus those 2,169; P3's
`GNPS` 65,152 = 63,625 block C rows plus those 1,527; P3's `GNPS_or_MoNA_missing_ce` 42,037 plus both groups sums to
the 109,358 CE-missing rows.

Materiality: zero. Every disagreeing row has missing CE, and `T_sim` requires CE present, so 0 of the 3,696 rows is in
any training table (checked directly). All 121,746 CE-present rows, which is a superset of `T_sim`, agree with P3
exactly, including all 8,751 `MSnLib_v1_probable` rows. Q's script asserted it reproduced all 231,104 P3 labels, so Q
implemented P3's finer taxonomy rather than the literal prose of its own frozen rule. The finding is that the frozen
Part 1 text is under-specified for CE-missing rows, not that any count is wrong.

## 6. Disclosure of errors in this reproduction

Two bugs in my own first pass, both found by the internal checks and fixed before the numbers above were taken:

1. The "all splits" aggregate for the long-table comparison was built with a dict comprehension whose duplicate keys
   silently kept the last value instead of summing train, val and test. It produced 9 spurious disagreements
   (for example category (1) all splits 5,792 instead of 30,631). Fixed by accumulating into the Counter.
2. The presented-value spot check matched three different quantities (`presented_value`, `presented_value*mz/500`,
   `presented_value*500/mz`) to one of mine, producing 26 spurious disagreements. Fixed by pinning the quantity string.

Neither touched the wide-table comparison, which was zero-disagreement from the first run.

## 7. What this reproduction does not establish

- It shares Q's inputs. The MSG 1.5 values, P4's range-read metadata parquet, P5's membership tables and the
  committed ms-pred labels are taken as given; a defect common to both passes would not show up here.
- It shares Q's inferred premises: the construction-order block boundaries (empirical, from P3), the QTOF native-eV
  reading (instrument semantics), the int-truncated base spectrum keys behind the inten_contr filter and the
  floor presented value (P1 C13/C15), and GLACIER's split. Reproducing the arithmetic under those premises is not
  evidence for them. GLACIER's presented value remains UNRESOLVED (P1 C22) and the category counts do not depend on it.
- The source attribution is not fully independent of P3 in one respect: the `MSnLib_v1.0_probable` heuristic needs
  P5's compound membership, exactly as the rule specifies, and my run reproduces P3's probable rows exactly. The
  block derivation, by contrast, was recomputed from the rule and matched the declared `B_start` and `C_start`
  without being told them.
- The 205 to 236 unallocated train losses for the generator and GLACIER, and the at most 49 for inten_contr, are
  reproduced as bounds only, since they are not row-identifiable. Train counts remain upper bounds by those amounts.

## 8. Files

- `scripts/ce_interface_adjudication/verify_counts_independent.py`
- `artifacts/ce_interface_adjudication/counts/v_independent_counts.csv`
- `artifacts/ce_interface_adjudication/counts/v_independent_counts.json`
- `artifacts/ce_interface_adjudication/notes/v_counts.md` (this file)

File-writing note: as in phases P1 to P5 and Q, the session's Write tool refused writes into this worktree (the
session is bound to a different worktree), so the note and script were authored in the session scratchpad and copied
here with `cp`; the script was run from this worktree and wrote its outputs directly. Nothing was committed and
nothing was downloaded, so `downloads_register.jsonl` is unchanged.
