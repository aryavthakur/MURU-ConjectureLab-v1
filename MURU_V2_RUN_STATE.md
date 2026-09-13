# MURU-WUR-v2 run state

**Updated:** 2026-09-13 (terminal state of this program)
**Branch:** `claude/muru-wur-v2-generation-b2ffa1` (based on `fable/wur-stage2-muru-development` @ `17027e1`); local, not pushed.
**HEAD:** see `git log -1`.

## Current phase

COMPLETE for development; external validation NOT executed on any source. Final report: `MURU_WUR_V2_FINAL_REPORT.md`.

## Completed

Registry; protocol wur-v2-dev-1.0 with A-1 to A-3; Experiments 1 to 13 (ledger, 23 entries); first decision gate; five adversarial reviews and adjudication; candidate `V2_TA_MORGAN_JOINT` serialized; freeze Parts I to IV; MultiMS2 census, populations, anchor gate FAILED; MSnLib census, anchors-first gate FAILED by small margins.

## Current best candidate

`V2_TA_MORGAN_JOINT` (frozen): development PRIMARY P1 0.1160 vs refitted Tier A 0.1305 (ratio 0.889, simultaneous [0.860, 0.918]), STRICT 0.926, AF 6.3 vs 10.3 percent; no trust output; one-scale shared profile.

## Populations

- Development-exposed: 1,325 v2 keys (includes former WUR HOLD and SEALED).
- Calibration-exposed: MultiMS2 anchors (106), MSnLib anchors (328 decoded).
- Excluded: LCSB confirmation set, WUR and LCSB negative mode.
- Protected, not outcome-accessed: MultiMS2 VALIDATION (1,297, `c411bb04...`) and SECONDARY (228); MSnLib validation frame (39,238 keys); MetaSci, BMDMS-NP, other MassBank/MoNA cohorts.

## Next authorized step

None within this program. Options needing a new user decision: (1) a separately pre-registered MSnLib two-rung study with the zero-parameter frozen WUR map fixed in advance and bridge uncertainty propagated instead of an absolute gate, spending the untouched MSnLib validation sample once; (2) a prospective dense-NCE acquisition with calibration anchors; (3) more diverse development chemistry on the development coordinate.

## Unresolved blockers / environment

- `ext03_validation.py` (MultiMS2) refuses to run because the anchor gate did not qualify the source.
- Data restoration: WUR release from `~/Downloads/20552933.zip` to `data/external/wur`; LCSB parquets copied from the main checkout; representations rebuilt by `scripts/wur_v2/build_v2_representations.py`; MultiMS2 mzML (6.9 GB) and MSnLib anchor mzML (4.2 GB) under `data/external/` (gitignored).
