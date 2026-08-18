# MURU V2 E4a Execution Gate Check (Step 8)

Mechanical check of all 8 required conditions. Reports `WAITING` and names
only the missing prerequisite(s) if any fail -- no number invented, no
condition waived.

| # | Condition | Status | Evidence |
|---|---|---|---|
| 1 | `LOCKED_EXECUTE_E4A` cryptographically/provenance recorded | **PASS** | `MURU_V2_E2_ROUTING_LOCK_FREEZE.md` + `.json` (Step 1); irreversibility proven both mathematically and empirically |
| 2 | Exact frozen E2b prerequisite satisfied | **FAIL** | `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md` (Step 2): E2b (Held-out replay) has never been executed anywhere in the repository (full-history search, zero mentions in the reconciliation's 73-finding ledger). Gate 1 is checked sequentially BEFORE Gate 2 in the frozen predicate and is not superseded by Gate 2's lock. Status: `WAITING`, not `NO` -- E2b could in principle still clear it, but it has not been run to check. |
| 3 | Balanced E2 estimation sample sealed, unless the authoritative protocol proves it's not a prerequisite | **PROVEN NOT A PREREQUISITE, BUT SUPERSEDED BY A LARGER ONE** | `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md` section 3, item 1: the "balanced n=270 sample" is a Rescue-v2-only construct, absent from `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` entirely -- proven from source, not inferred. What the frozen protocol actually requires (section 6: "Population. All 540 E2a cases") is the FULL population, which is the actual blocking condition below. |
| 3b | Full 540-case E2a population complete with persisted front data | **FAIL** (in progress) | See live figures below -- not yet 540/540, and the quarantined poison world has no scheduled resolution path |
| 4 | E4a results-blind amendment frozen | **PASS** | `MURU_V2_E4A_RESULTS_BLIND_AMENDMENT_V1.md` (Step 3) |
| 5 | E4a implementation passes all control tests | **PASS** | `src/muru/v2_calibration/e2_rescue_v2/e4a_scoring.py` (Step 4); `tests/test_e4a_scoring_controls.py`, 81/81 checks passing (Step 5), including a real replay-consistency control against an already-completed E2a world |
| 6 | No unresolved reachable equivalence defect can invalidate the primary endpoint | **PASS** | `MURU_V2_E4A_EQUIVALENCE_REACHABILITY_AUDIT.md` (Step 6): both inherited defects checked, neither reachable (one proven by static call-graph, the other by three independent empirical checks against the real corpus) |
| 7 | Dev/EVAL split frozen | **PASS** | `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 6 (replicate-stratified, sealed before any front is read); re-verified mechanically in Step 5 test 6 |
| 8 | E4a execution manifest frozen | **NOT YET PRODUCED** | Deferred -- would be the final artifact assembled once conditions 2 and 3b clear; not meaningful to freeze while the population and Gate 1 remain open, per the same "do not invent while the answer is still in motion" discipline this migration has followed throughout |

## Overall

```
E4A_EXECUTION_CURRENTLY_ALLOWED: NO
```

```
WAITING
```

**Missing prerequisites, precisely:**

1. **Gate 1 (E2b)** -- Held-out replay has not been executed. This is an
   entirely separate study, out of E2a/Rescue-v2's scope, and no amount of
   further E2a completion or routing-lock certainty can satisfy it. This
   is the harder blocker of the two: it requires a decision to launch a
   study this document does not authorize.
2. **Full 540-case E2a population** -- not yet complete (live figures
   below), and the quarantined poison world
   (`V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000`) has no
   scheduled resolution path, so a literal 540/540 cannot be reached on
   the current plan without a separate decision to re-attempt it in an
   uncontended window.

Both are genuine, disclosed, unresolved blockers -- not gaps this document
works around. E4a's scoring package (Steps 3-6) is fully prepared and
frozen, ready to execute the moment both clear; nothing further needs to
be built.

## Live figures at time of this check

(World-ID/count fields only, no scientific rate -- consistent with every
other operator-facing artifact in this migration.)

- Routing lock: `LOCKED_EXECUTE_E4A`, confirmed stable across every
  reading taken this session (most recent: `N_CLASSIFIED: 481/540`,
  `R_REMAINING: 59`).
- Population completion: 481/540 as of this check, 0 errors across all
  production shards, still short of the full 540 (condition 3b).
- Balanced-sample tier: tracked by the dedicated watcher
  (`/tmp/e2_rescue_v2_watch_sample_only.py`); sealed on completion per
  `/tmp/e2_rescue_v2_seal_sample_tier.py` (Step 7) -- included for its own
  sake, not because it gates E4a (see condition 3 above).
