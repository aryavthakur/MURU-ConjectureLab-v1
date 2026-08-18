============================================================
MURU E2B FULL FRONT REPLAY FINAL
============================================================

HOST: Sandeeps-MacBook-Air.local
OS: macOS 26.1 (Darwin 25.1.0)
ARCH: arm64

REPO: /Users/aryav/Documents/MURU-ConjectureLab-v1
BRANCH: audit/muru-rc5-execution-semantics-authority-audit

AUTHORITATIVE_REFERENCE_COMMIT: d6f607a

EXECUTION_FREEZE_COMMIT: dabcb4b

POST_RUN_COMMIT: (pending)

------------------------------------------------------------
PRE EXECUTION
------------------------------------------------------------

PERSISTENCE_PATCH_READY: PASS

PERSISTENCE_SIDE_EFFECT_TEST: PASS (6/6 tests)

SCIENCE_CONFIG_HASH_MATCH: YES (8056cb6f)

SCIENTIFIC_CHANGED_LINES: 0

UNRELATED_CHANGED_LINES: 0

CASE_COUNT: 144

EXPECTED_SEARCHES: 4320

CASE_ORDER_HASH_MATCH: YES (75d84d0b)

SEED_ORDER_HASH_MATCH: YES (e05e9cc0)

CASE_SEED_PAIR_HASH_MATCH: YES (bddb25e4)

STATIC_INPUT_HASH_MATCH: YES

ENVIRONMENT_ACCEPTABLE: YES (12/12 EXACT_MATCH)

DIRECT_EVALUATOR_FROZEN: YES

EVALUATOR_SHA256: ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743

PRE_RUN_TESTS_RUN: 46

PRE_RUN_TESTS_FAILED: 0

ESTIMATED_STORAGE_BYTES: 32000000

AVAILABLE_STORAGE_BYTES: 65498251264

DISK_HEADROOM_RATIO: 2046.8

PRE_EXECUTION_GATE: PASS

------------------------------------------------------------
EXECUTION
------------------------------------------------------------

SEARCHES_EXPECTED: 4320

SEARCHES_STARTED: 4320

SEARCHES_COMPLETED: 4320

SEARCHES_FAILED: 0

FRONTS_EXPECTED: 4320

FRONTS_WRITTEN: 4320

FRONTS_VALID: 4320

FRONTS_TORN: 0

FRONTS_DUPLICATE: 0

FRONTS_MISSING: 0

MANIFEST_ROWS: 4320

UNIQUE_MANIFEST_KEYS: 4320

TOTAL_PARETO_ROWS: 51411

TOTAL_FRONT_BYTES: 20642360

WALL_TIME: 4310.2s (1.20h)

------------------------------------------------------------
IDENTITY VALIDATION
------------------------------------------------------------

CASES_EXPECTED: 144

SELECTION_COUNT_EXACT_CASES: 144/144

REPRESENTATIVE_EXACT_CASES: 144/144

E2B_IDENTITY: PASS

------------------------------------------------------------
DIRECT E2B ATTRIBUTION
------------------------------------------------------------

CLASSIFICATION_DENOMINATOR: 144

SUCCESS: 4

LOST_IN_CROSS_SEED: 71

LOST_IN_RETENTION: 55

NEVER_ON_FRONT: 14

DIRECT_RETENTION: 55

DIRECT_GENERATION: 14

DIRECT_THIRD_CLASS: 75

INVALID_CASES: 0

COUNT_SUM_CHECK: PASS (55 + 14 + 75 + 0 = 144)

HISTORICAL_RETENTION: 69

HISTORICAL_GENERATION: 57

RETENTION_DEVIATION: 14

GENERATION_DEVIATION: 43

FROZEN_MATERIAL_CONTRADICTION_RULE:
  "IF E2b's direct measurement contradicts the v1 decomposition's
  69/57 retention-vs-generation split by more than 10 cases (PE2-4's
  own tolerance) -- THEN this protocol DOES NOT EXECUTE."
  Source: f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md
  section 4, verbatim.

THRESHOLD_TRIGGERED: YES (both deviations > 10)

E2B_69_57_HOOK: FAIL

------------------------------------------------------------
GATE 1
------------------------------------------------------------

E2B_IDENTITY: PASS

E2B_69_57_HOOK: FAIL

GATE_1: FAIL

------------------------------------------------------------
CURRENT E4A DEPENDENCY STATE
------------------------------------------------------------

E2A: COMPLETE (540 worlds accounted; routing locked)

E2B_IDENTITY: PASS (144/144 exact, d6f607a confirmed by fullfront replay)

E2B_69_57: FAIL (direct measurement materially contradicts 69/57)

GATE_1: FAIL

ROUTING: LOCKED_EXECUTE_E4A (but E4A now suspended by Gate 1 failure)

CONDITION_3B: BLOCKED (539/540, no exception)

SCORE_SCHEMA: BLOCKED

E4A: SUSPENDED (Gate 1 FAIL suspends all E4 ablations)

------------------------------------------------------------
TERMINAL CATEGORY
------------------------------------------------------------

E2B_69_57_FAIL

The E2b direct three-way attribution materially contradicts the v1
decomposition's 69/57 retention-vs-generation split.

The v1 predicted 69 retention-class and 57 generation-class cases.
The direct measurement found 55 LOST_IN_RETENTION and 14 NEVER_ON_FRONT,
with 71 cases in a previously invisible LOST_IN_CROSS_SEED category and
4 SUCCESS (unchanged).

The deviations (14 and 43) both exceed the frozen 10-case tolerance.

------------------------------------------------------------
SCIENTIFIC INTERPRETATION
------------------------------------------------------------

H_partial (befca0d section 2.1) is confirmed in dramatic fashion:

The v1 decomposition massively overstated generation failure. Of the 57
cases classified as "GENERATION" (no retained candidate correct, front
unobserved), only 14 truly had no correct row on any front. The remaining
43 cases DID have correct expressions on their Pareto fronts that were
either:
  (a) lost in argmax(score) retention (LOST_IN_RETENTION), or
  (b) retained by some seeds but lost in cross-seed voting
      (LOST_IN_CROSS_SEED)

The 71 LOST_IN_CROSS_SEED cases reveal that correct candidates survive
both search generation AND within-seed retention far more often than the
v1 decomposition suggested, but the cross-seed identity voting mechanism
(20-of-30 stability gate) is a larger failure source than previously
understood.

This does NOT change the v1 result (G2: 4/144 stands unchanged).

------------------------------------------------------------
SMALLEST JUSTIFIED NEXT ACTION
------------------------------------------------------------

Per MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9 falsification hook and
MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md section 4 Gate 1:

All E4 ablations are SUSPENDED until the E2a/E2b divergence in the
decomposition attribution is resolved.

The non-execution of E4a, and the direct measurement that caused it,
must be reported in place of any policy comparison.

The frozen next action: REPORT_GATE_1_FAILURE_AND_ATTRIBUTION_REVISION.

No retention-policy ablation (E4a) may proceed. No score remediation may
proceed. No poison-world amendment may proceed. These are all downstream
of Gate 1 and Gate 1 has failed.

The decomposition's root-cause ranking must be recomputed from the direct
E2b attribution before any E4 arm is re-authorized.

------------------------------------------------------------
DO NOT REPEAT
------------------------------------------------------------

1. E2a world enumeration and duplicate check (540 unique, 0 duplicates)
2. E2a routing lock verification (LOCKED_EXECUTE_E4A)
3. E2b identity replay (144/144 exact, d6f607a, confirmed again here)
4. E2b full-front replay (4,320 fronts, 51,411 rows, all valid)
5. E2b direct 69/57 measurement (55/14/75/0, materially contradicts 69/57)
6. Gate 1 evaluation (FAIL, both deviations > 10)
7. R2 k-grid recovery ({1,2,3,5} from f4c1105)
8. R4 eps-grid recovery ({0.001,0.005,0.02} from f4c1105)
9. E4a arm count recovery (7 arms, 13 parameters)
10. Poison-world OOM reproducibility (80+, both architectures)
11. ARM64/x86 interchangeability analysis (NOT interchangeable)

------------------------------------------------------------
FILES CREATED
------------------------------------------------------------

Replay artifacts:
  results/e2b_macos_fullfront_replay_20260818/
    E2B_FULLFRONT_REPLAY_REPORT.json
    manifest.jsonl (4,320 entries)
    fronts/ (4,320 JSONL files in 144 case subdirectories)
    MURU_E2B_FULLFRONT_REPLAY_FINAL.md (this file)

Gate artifacts:
  results/e2b_macos_fullfront_replay_20260818/gate/
    MURU_E2B_DIRECT_69_57_GATE.json
    MURU_E2B_DIRECT_69_57_CASES.csv

Manifests:
  results/e2b_macos_fullfront_replay_20260818/manifests/
    MURU_E2B_EXPECTED_SEARCH_MANIFEST.csv
    MURU_E2B_FULLFRONT_MANIFEST.sha256

Provenance:
  results/e2b_macos_fullfront_replay_20260818/provenance/
    MURU_E2B_FULLFRONT_REPLAY_PROVENANCE.json
    MURU_E2B_FULLFRONT_SCIENCE_CONFIG.json
    MURU_E2B_FULLFRONT_SCIENCE_CONFIG.sha256
    AGENT_2_SCIENTIFIC_EQUIVALENCE_REPORT.json

Scripts (committed at execution freeze):
  scripts/run_e2b_fullfront_replay.py
  scripts/e2b_direct_evaluator.py
  scripts/e2b_completeness_checker.py
  scripts/e2b_identity_comparator.py

Tests (committed at execution freeze):
  tests/test_persisting_backend_no_side_effect.py
  tests/test_e2b_direct_evaluator.py

SHA-256 Hashes:
  SCIENCE_CONFIG: 8056cb6feefc624dbb85e3312d81494f343cce3f858bd1ec7a2857c34681aeb2
  EVALUATOR: ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743
  FRONT_MANIFEST: 297e73b144b67534391b3b8bc8919e13ef979a386ef499aed61f2f2f0d9d97f6

------------------------------------------------------------
GIT
------------------------------------------------------------

EXECUTION_FREEZE_COMMIT: dabcb4ba3b8bb32c6a32dc54ae10e34d3d5c41c2

POST_RUN_COMMIT: (pending)

PUSH_STATUS: NOT PUSHED

WORKTREE_STATUS: main worktree

============================================================
END
============================================================
