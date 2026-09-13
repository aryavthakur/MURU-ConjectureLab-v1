# MURU-WUR-v2 run state

**Updated:** 2026-09-12 (milestone M1: registry, data layer, partitions, protocol)
**Branch:** `claude/muru-wur-v2-generation-b2ffa1` (based on `fable/wur-stage2-muru-development` @ `17027e1`)
**HEAD:** see `git log -1`; this file is updated at each milestone commit.

## Current phase

Phase 0 preparation complete: exposure registry, v2 population (1,325 keys), frozen partitions, frozen development protocol `wur-v2-dev-1.0`. Next: Experiment 1.

## Completed

| Step | Artifact |
|---|---|
| Drift check, WUR bytes restored and hash-verified | registry section 1 |
| Exposure registry and manifest | `MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md`, `artifacts/wur_v2/exposure_manifest.json` |
| Spectrum tables with acquisition ids | `artifacts/wur_v2/data/wur_pos_spectra.parquet`, `lcsb_pos_spectra.parquet`, `wur_pos_cells.csv` |
| Population tables | `artifacts/wur_v2/data/compounds.csv`, `long_aligned.csv`, `native_cells.csv`, `population_manifest.json` |
| Partitions | `artifacts/wur_v2/folds.json` |
| One-look function guards | `stage3.sealed_tables`, `holdcheck.run`; tests `tests/wur_v2/` |
| Protocol | `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` |

## Current best candidate

None yet under v2. Historical: MURU-WUR-v1 `V1B_RIDGE_TIERA`.

## Populations

- Exposed (development): LCSB-DEV, WUR-DEV-ANALYSIS, WUR-DEV-HOLD, WUR-SEALED (1,325 keys, sha `81eef787...`).
- Excluded: LCSB-CONFIRMATION (110), WUR negative mode, LCSB negative mode.
- Protected, not outcome-accessed: MultiMS², MSnLib, MetaSci, BMDMS-NP, non-LCSB MassBank/MoNA cohorts.

## Next authorized step

Experiment 1 (estimand audit and v1 reproduction), then Experiments 2 to 5; MultiMS² outcome-blind census in parallel.

## Unresolved blockers

None. Environment note: the WUR release must exist at `data/external/wur` (restore from `20552933.zip`, hashes in `muru.io.wur_retrieval`); LCSB parquets under `artifacts/` are untracked and copied from the main checkout.
