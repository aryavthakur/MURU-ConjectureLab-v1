# CE interface adjudication: C02 high-mass replication, PREREGISTRATION

Study id `muru-ce-interface-high-mass-replication`. Freeze ref `refs/muru-freeze/muru-ce-interface-high-mass-replication`.
Written 2026-09-19. Computational only, on public online spectra. No C02 peak list has been read.

## 1. Question

Does Design A's descriptive K1 > K2 ordering (composite cosine K1 0.5571 vs K2 0.5148, formally INTERFACE
UNRESOLVED) replicate in an independent high-mass Orbitrap HCD NCE population, where for precursor m/z above
500 the conversion K2 = NCE x [M+H]+ / 500 lies numerically ABOVE K1 = NCE?

In Design A most compounds sat below m/z 500, so K2 fed the checkpoints a lower number than K1. Here 29 of 32
compounds sit above 500, so K2 feeds a higher number. A K1 advantage here cannot be explained by a generic
checkpoint preference for numerically lower CE inputs.

This study is NOT a replacement for the cancelled prospective Design B, NOT a universal interface proof, NOT a
MURU-vs-comparator benchmark, and NOT permission to recompute PR #8. Design A stays INTERFACE UNRESOLVED.

## 2. Population (fixed from metadata only)

Source: MassBank 2026.03 (git tag), CyanoMetDB contributors MSBNK-EAWAG-EC, MSBNK-EAWAG-ED, MSBNK-MLU-ED
(3,126 record files). Identity from the CyanoMetDB Table S4 (SMILES, identification level, material).
Header metadata came from the frozen C02 screen plus a completed header-only code-search harvest
(`high_mass/metadata/qc_fragments_all_partitions.jsonl`, 91 partitions, 3,126/3,126 files, no peak content).
Builder: `scripts/ce_interface_adjudication/high_mass/10_build_population.py`. Each record gets exactly one
first failed rule in `population/high_mass_exclusion_ledger.csv`.

| Rule | Criterion | Records left |
|---|---|---|
| H0 | C02 record files at tag 2026.03 | 3,126 |
| H1 | [M+H]+ (positive mode), field and title agree | 1,888 |
| H2 | MS2, Orbitrap instrument type (LC-ESI-QFT/ITFT) | 1,888 |
| H3 | FRAGMENTATION_MODE HCD explicit in the header | 1,888 |
| H4 | single explicit `N % (nominal)` CE equal to the title CE | 1,888 |
| H5 | header evidence is the pinned 2026.03 blob (file unchanged on dev) | 1,773 |
| H6 | record maps to exactly one Table S4 structure (no isomer groups) | 1,506 |
| H7 | precursor within 0.01 Da of theoretical [M+H]+, InChIKey block agrees | 1,506 |
| H8 | ms-pred elements, heavy atoms <= 160, theoretical [M+H]+ <= 995.556 (both checkpoints' training-label maximum, Design A R7) | 1,117 |
| H9 | not in MassSpecGym 1.5 (recorded and parent key), ms-pred MSG labels, MURU registry / exposed union / v2 development population, PR #7, PR #8 or Design A, by key and by tautomer key; scaffold group not in the MURU registry, v2 development population, PR #7, PR #8 or Design A. Skeleton route reported, not applied (as Design A) | 767 |
| H10 | identity tier in the primary tiers (all levels, section 3) | 767 |
| H11 | NCE grid below: record NCE in grid, compound complete on every grid level | 588 |
| H12 | one compound per scaffold group: best tier (1 < 2a < 2b/3), then smallest parent key | 364 |

Final: 32 compounds in 32 scaffold groups, 364 records. Theoretical [M+H]+ 299.23 to 991.51, median 774.86;
29 above m/z 500; 1 in 450 to 550. Records: EAWAG-EC 135 and EAWAG-ED 154 (Exploris 240), MLU-ED 75
(Q Exactive Plus). Compound arms: EC+ED 19, MLU-ED 10, ED only 2, EC+ED+MLU 1.

## 3. Identity tier (user decision, 2026-09-19)

Table S4 levels: Level 1 (confirmed against a standard) 12, Level 2a 6, Level 2b 14, Level 3 0 in the final
population. Level 1 alone leaves 12 groups, which cannot resolve an effect of Design A's size. The primary
population is therefore all single-structure levels with Level 1 preferred inside each scaffold group.
Rationale: each compound's single structure feeds both K1 and K2, so a wrong structure dilutes the paired
contrast but cannot create a direction. Level 1 and Level 1+2a subsets are descriptive only.

## 4. Energy grid (fixed from metadata only)

Available [M+H]+ ladder after H9: modal 15, 20, 25, 30, 40, 50, 60, 70, 80 (42 of 53 compounds complete),
plus 35 on 16 ED records. Rule (`choose_grid`): the largest grid, over subsets of the modal ladder with at
least 2 levels, whose scaffold-group count is at least 0.95 x the maximum over all grids (33). The rule selects
**NCE 15, 20, 25, 30, 40, 50, 60** (7 levels, 32 groups). With 8 levels only 31 groups remain (94%), and the
full ladder keeps 28. No cell was chosen from peaks, prediction performance or spectrum quality.

## 5. Mappings, models, endpoint

- K1 `CE = NCE`; K2 `CE = NCE x theoretical [M+H]+ / 500` (binary64, no rounding); K3 `floor(K2)`, descriptive only.
- ICEBERG 2.1 (msg_simulation) and GLACIER (msg), same public checkpoints, command lines and seed as Design A,
  via `design_a/30_run_predictions.py` pinned by sha256.
- Primary endpoint: untransformed full-spectrum cosine from the frozen Design A similarity layer
  (FROZEN_CONFIG sha256 `655436...b252848`) through `design_a/40_score_spectra.py` pinned by sha256.
  JS similarity is robustness only.

## 6. Analysis (one look)

`high_mass/60_analysis.py`, which reuses `design_a/50_analysis.py` (pinned) for the mechanical drop rule and the
reduction:

1. per (compound, model, mapping, NCE): mean over replicate records;
2. per (compound, model, mapping): mean over the 7 NCE cells, equal weight;
3. per (compound, mapping): mean of ICEBERG 2.1 and GLACIER.

Estimand: mean over compounds of S_K1 - S_K2. Unit: compound, which here equals scaffold group (one compound
per group). Bootstrap: multinomial compound resampling, B = 10,000, seed 20260920, 95% percentile interval.
Drop rule (Design A): a record with no readable spectrum or prediction is dropped; a compound that loses an
entire (model, mapping, NCE) cell is dropped for all mappings.

Verdict, exactly one:

- `HIGH_MASS_SUPPORTS_K1` if the 95% interval lies wholly above zero;
- `HIGH_MASS_SUPPORTS_K2` if it lies wholly below zero;
- `HIGH_MASS_UNRESOLVED` otherwise.

Descriptive only, never decisional: K3 contrasts, per-model, per-NCE, JS, contributor arm, mass band,
identity tier subsets.

## 7. Power, stated before any data

From Design A's composite, the per-compound SD of S_K1 - S_K2 was about 0.13 over 2 NCE cells. At N = 32 the
95% half-width is then about 0.046, against Design A's point estimate of +0.042. Averaging over 7 cells should
lower the SD, and the larger K1/K2 separation at high mass (median K2/K1 = 1.55) may enlarge the effect, but
UNRESOLVED is a realistic outcome and is fully reportable. Known confound: the population is one chemical
class (cyanobacterial peptides and related metabolites), mostly Level 2 and crude-extract measurements.

## 8. Execution sequence

1. this preregistration, code and population committed; 2. freeze ref published; 3. pre-access record
committed and `refs/muru-access/<study>` published; 4. retrieve exactly the 364 frozen record files by pinned
2026.03 blob sha (`26_retrieve_records.py`); 5. predictions (`30_run_predictions.py execute`), committed;
6. scoring (`40_score_spectra.py`) and input manifest (`45_write_input_manifest.py`), committed;
7. `60_analysis.py` run exactly once with `MURU_CE_HIGH_MASS_ONE_LOOK=1`; 8. result committed untouched.
Every execution step refuses without `MURU_CE_HIGH_MASS_EXECUTE=1` and the freeze ref.
After retrieval the C02 population is EXPOSED permanently.
