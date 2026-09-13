# MURU-WUR-v2 run state

**Updated:** 2026-09-13 (milestone M5: first decision gate; candidate selected for adversarial review)
**Branch:** `claude/muru-wur-v2-generation-b2ffa1` (based on `fable/wur-stage2-muru-development` @ `17027e1`)
**HEAD:** see `git log -1`.

## Current phase

First decision gate passed (`MURU_WUR_V2_DECISION_GATE_1.md`). Leading candidate `V2_TA_MORGAN_JOINT` fit on all 1,325 compounds and serialized (`artifacts/wur_v2/candidate/`). Next: five adversarial reviews, adjudication, final-candidate decision; in parallel, MultiMS2 external-validation design (outcome-blind).

## Completed experiments (ledger `artifacts/wur_v2/ledger/ledger.jsonl`)

EXP01A/B estimand audit and baselines; EXP02 repeatability and identifiability; EXP03 derivative amplification; EXP04 survival/depth; EXP05/05B acquisition; EXP06 learning curves; EXP07 ION_ENV; EXP08A-E Morgan family and permutation controls (EXP08P corrected); EXP09A-D alternatives; EXP10 trust (failed); EXP11 shape oracle; EXP12 shape arm (not selected); EXP13 candidate stress. Protocol amendments A-1, A-2.

## Current best candidate

`V2_TA_MORGAN_JOINT`: frozen v1 collapse (shared isotonic profile, one scale per compound) + ridge of log g on training-standardized Tier A (12) and 0.1 x log1p Morgan r2 2048 counts, alpha 0.3 (nested selection on all 1,325). Development PRIMARY P1 0.1160 vs refitted Tier A 0.1305 (ratio 0.889 [0.865, 0.911]); STRICT 0.926; GIANT 0.896; AF 6.3 vs 10.3 percent. No trust output.

## Populations

- Exposed (development): LCSB-DEV, WUR-DEV-ANALYSIS, WUR-DEV-HOLD, WUR-SEALED (1,325 keys, sha `81eef787...`).
- Excluded: LCSB-CONFIRMATION (110), WUR negative mode, LCSB negative mode.
- Protected, not outcome-accessed: MultiMS2 (outcome-blind census done: `MURU_V2_MULTIMS2_OUTCOME_BLIND_CENSUS.md`; aggregate QC-pass membership seen), MSnLib, MetaSci, BMDMS-NP, non-LCSB MassBank/MoNA cohorts.

## Next authorized step

Adversarial reviews of the candidate and development record; then final-candidate freeze decision and MultiMS2 external protocol. External outcome access is NOT authorized until every condition of the v2 brief holds, including a committed freeze document and disjoint calibration anchors.

## Unresolved blockers

- MultiMS2 observable compatibility: library QC censors precursor-rich spectra; MS2 window and CE spread undocumented; QTOF CID in eV requires an m/z-aware energy adapter fitted on anchors.
- Environment: WUR release at `data/external/wur` (restore from `20552933.zip`); LCSB parquets under `artifacts/` untracked (copied from the main checkout); representations other than TIER_A/MACCS rebuilt by `scripts/wur_v2/build_v2_representations.py`.
