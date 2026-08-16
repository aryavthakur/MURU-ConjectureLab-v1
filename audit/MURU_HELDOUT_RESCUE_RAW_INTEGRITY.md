# MURU Held-out Rescue — Raw Execution Integrity Report

**Phase B artifact. Produced before any post-run analysis artifact was opened.**

Evidence root (read-only): `/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-heldout-a3-6/results/held_out`
Execution worktree branch: `exec/muru-heldout-a3-6`
Execution worktree HEAD: `8d87143d4280602323aa33ee0b5481aaef0fb4a8` (tag `engineering-rc5-1-heldout-authorization`)

No file under the evidence root was modified, moved, or deleted by this audit.

## 1. Checklist results

| # | Check | Result |
|---|---|---|
| 1 | Exactly 240 expected case records | **PASS** (240) |
| 2 | All expected Held-out case IDs present, no others | **PASS** (set equality vs `registry.iter_case_ids("held_out")`; 0 missing, 0 extra) |
| 3 | Exactly 7,200 seed slots | **PASS** (7,200; every case exactly 30) |
| 4 | No duplicate seed records | **PASS** (0 duplicate `(case_id, seed)` pairs) |
| 5 | No unexpected case IDs | **PASS** (0; no seed-file case mixing) |
| 6 | No Challenge records | **PASS** (0) |
| 7 | No Confirmation records | **PASS** (0) |
| 8 | Schema validity | **PASS** (240/240 `muru-rc5-case-record-2.0.0`; uniform 35-key schema) |
| 9 | Execution-manifest identity | **PASS** — digest `bcd197dce732f2b2ad156d04ac4285ab23371a8dce40cb1f98281615a01afd08`, matches the launch-recorded value **and** recomputes correctly under the declared canonical convention |
| 10 | Run commit identity | **PASS** — `run_commit = 8d87143d…`, `tree_clean = true`; all 240 provenance entries carry the same commit |
| 11 | Global-plan identity | **PASS** — single `global_plan_digest f2a81a91…` across all 7,200 seed records; artifact recomputes to the same digest; single `search_settings_digest`, single `null_threshold_digest` |
| 12 | Seed derivation | **PASS** — all 240 cases' manifest seeds and seed-record seeds match `rc5_seeds.case_search_seeds` exactly (0 mismatches); frozen invariants report 11,400 seeds / 11,400 distinct across 380 cases, band `[2100000000, 2100011399]`, disjoint from all other bands |
| 13 | Source identity | **PASS** — `a3_5_science_freeze = 560bf285…`, `engineering_parent_commit = 69e33c77…`, grammar/calibration/threshold digests all single-valued |
| 14 | No post-execution mutation of raw records | **PASS with disclosed operational anomaly** — see §2 |
| 15 | Seal receipt validity | **PASS** — `CURRENT-CONTRACT HELD-OUT RAW EXECUTION SEALED`, `sealed=true`, `case_count=240`, `seed_count=7200`, `run_commit` matches |
| 16 | Canonical raw hashes | **PASS** — all **482/482** sealed files re-hash to their recorded SHA-256; 0 mismatched, 0 missing, 0 raw files outside the seal |
| 17 | Execution-failure count | **PASS** — **0** cases `execution_failure_poisoned`; seed statuses 7,136 `COMPLETED_WITH_CANDIDATES` + 64 `COMPLETED_NO_CANDIDATE`; **zero `EXECUTION_FAILURE`** |

## 2. Disclosed operational anomaly — case `PB|held_out|F14|r008`

Filesystem mtimes show one raw case record written at 08:50:27 local, roughly 5.6 hours after
every other case finished (03:11:21). This was examined specifically as a candidate mutation.

**Finding: genuine long-running case, not a mutation.** Evidence:

- Provenance carries **exactly one** entry for the case (`started_utc 06:06:51Z`,
  `finished_utc 12:50:27Z`, `wall_seconds 24216.4`). There are **no duplicate provenance entries
  for any case** and **no re-run entries anywhere** in the partition.
- The entry's `commit` is `8d87143d…`, identical to all 239 others.
- All 30 of its seeds are present, all `COMPLETED_WITH_CANDIDATES`, `execution_failure_poisoned=false`.
- Its digests (`null_threshold_digest`, schema version) are identical to every other record.
- Its seed-record file was last written 02:10:32, consistent with search completing early and
  case-level scoring stalling; the record write is the normal end-of-case write.

**Magnitude**: median case wall time 117.1 s; this case 24,216.4 s (≈207× median). The second
longest is `PB|held_out|F20|r002` at 1,351.4 s.

**Scientific reach**: family F14 (`high-energy vertical violation`, adequacy target M2) carries
**no primary endpoint** — it contributes 0 to G1, 0 to G2, 0 to G3. Its record is
`UNEVALUABLE` at `a1_adequacy` (`BOUNDARY_LIMITED`), so it also never reached Gate 7 or Gate 8.
The anomaly therefore cannot affect any primary endpoint or gate count.

**Sealing order is correct**: the seal receipt was written at 09:00:11, *after* the last raw
write at 08:50:27. **No raw file has an mtime later than the seal.** The two post-run analysis
files (09:02:00) were written after sealing and are **not covered by the seal**.

## 3. Seal scope finding (material to Phase D)

The seal covers exactly 482 files: 240 records + 240 seed records + 1 provenance log +
1 execution manifest.

**`held_out_formal_analysis.json` and `held_out_hostile_audit_report.md` are NOT in the seal.**
They live in the same directory but are outside the sealed set and were written after it. The
integrity of the raw evidence therefore says nothing about the correctness of those two files,
and they can be superseded without touching sealed evidence.

## 4. Observed record-schema limitation (material to Phase C)

The sealed case record schema (`muru-rc5-case-record-2.0.0`, 35 keys, uniform across all 240)
contains:

- `g2_event` — G2 is directly scorable from sealed evidence.
- `acceptance_status`, `acceptance_gate_reached`, `falsification_results`, plus every
  `StructuralCandidate` input (`valid_r2`, `complexity`, `selection_fraction`,
  `invalid_fraction`, `effective_support`, `ceiling_fraction`, `ceiling_r2`,
  `candidate_test_r2`) and `a1_case_adequacy_status` — Gate 7 and Gate 8 are reconstructable.
- `f9_stress_test_result`, `f9_stress_test_metric`, `f9_acceptance_calibration_status` — the F9
  secondary is reportable.
- `effective_support` + case variant — **G3 is fully derivable**, since `classify_g3_event`
  requires only `(variant, AcceptanceResult, effective_support)`.

It **does not** contain any G1 observable: there is no `g_spearman`, no `trajectory_mae`, no
`per_energy_mean_mae`, and no G1 verdict field. Only G1's third conjunct is recoverable, via
`m0_accepted ⟺ a1_case_adequacy_status == M0_NOT_REJECTED`.

**Consequence**: G1 cannot be scored end-to-end from the sealed records alone. This is a
**record-schema/persistence gap, not a search-execution defect** — A3.5 §8.2 records that "G1's
four inputs are in fact search-independent", so G1 is recomputable from frozen case content and
the frozen training-only `Phi` **without rerunning any of the 7,200 searches**.

## 5. Distinction: execution versus analysis

**RAW EXECUTION VALID**

The 7,200 searches, their 240 case records, the manifest, the provenance log, and the seal are
internally consistent, cryptographically intact, derived from the correct frozen commit and
global plan, and free of Challenge/Confirmation contamination and of execution failures. The one
operational anomaly (§2) is disclosed and is scientifically inert.

Any defect located in a downstream analyzer does **not** invalidate this evidence, and no search
requires rerunning.

---

**Classification: `VALID WITH DISCLOSED OPERATIONAL DEVIATION`** (search execution)
**Classification: `VALID`** (raw sealed evidence)
