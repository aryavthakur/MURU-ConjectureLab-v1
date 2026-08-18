# MURU v2 E2 Rescue-v2 — Local Artifact Recovery (Response to Cloud x86_64 Reconciliation Failure)

**Date (UTC)**: 2026-08-18
**Host**: Local macOS ARM64
**Branch**: `claude/e2-rescue-v2-computational`
**Trigger**: `results/e2/rescue_v2_migration/CLOUD_X86_HOST_RECONCILIATION_FAILURE.{md,json}` (commit `929c7a7`),
which found only 235/530 completed E2a worlds reconcilable on the new x86_64 cloud host, and required
recovery step 4: "Re-verify the 31 manifest files against their recorded sha256 ... Move
`/tmp/e2_rescue_v2_production_out/` and `/tmp/e2_rescue_v2_smoke_output/` into the repository under a
provenance-labelled directory."

No world was recomputed. This is a byte-preserving artifact recovery only.

## 1. Authoritative manifest recovered

The 31-file manifest with expected sha256/size was recovered from
`results/e2/rescue_v2_migration/LOCAL_E2_RESCUE_V2_CHECKPOINT_530.json`'s `result_file_manifest` field.
Cross-checked byte-for-byte identical (same 31 paths, same sha256, same size) against
`CLOUD_X86_HOST_RECONCILIATION_FAILURE.json`'s `manifest_reconciliation` `expected_*` fields. No
disagreement between the two recorded copies of the manifest.

## 2. Pre-copy verification (source artifacts, before touching anything)

All 31 manifest files were located and sha256-verified at their literal recorded source paths, before
any copy or move:

- 8 files: `/tmp/e2_rescue_v2_production_out/{candidates,worlds}_shard_00{0,1,2,3}.jsonl` — new
  Rescue-v2 lazy-worker production output (shards 0-3, PIDs 77974-77977), never previously committed.
- 21 files: `.claude/worktrees/exp-v2-e2-pareto-observability/results/e2/{run,run_shard1_healthy,
  run_shard3_healthy,run_shard4_healthy,run_shard5_healthy}/*` — the old-E2 checkpoint's five
  `chmod 444` preserved directories (409/540, imported by reference by Rescue-v2 per
  `MURU_V2_E2_RESCUE_V2_MIGRATION_PROVENANCE.json`).
- 2 files: `/tmp/e2_rescue_v2_smoke_output/{candidates,worlds}_shard_000.jsonl` — the 2 smoke-verified
  worlds from Rescue-v2's launch smoke test.

**Result: 31/31 MATCH.** Every source artifact reproduced its recorded sha256 and size exactly.

## 3. Diagnosis of the differing committed files (required before any overwrite)

This worktree's own committed copies of the 21 preserved-directory files (`results/e2/run/*`,
`results/e2/run_shard{1,3,4,5}_healthy/*`) were checked against the same manifest and found to
**mismatch** — same sizes/hashes as the cloud host reported as `HASH_MISMATCH`/`MISSING_ON_HOST`
(e.g. `results/e2/run/candidates_shard_000.jsonl`: committed at 26,197,568 bytes vs. authoritative
59,211,935 bytes).

Root-caused before any file was touched: `git cat-file -s` on `HEAD:results/e2/run/candidates_shard_000.jsonl`
returns 26,197,568 bytes and the working tree was clean (no local uncommitted edit) — the truncated
content was itself committed, in `dc66e27` ("E2: commit accumulated production output"). This matches
`CLOUD_X86_HOST_RECONCILIATION_FAILURE.json`'s root-cause finding verbatim: a full-history blob scan
shows the larger manifest versions of these files were never committed on any branch. The true,
complete content survives only as uncommitted (never-`git add`ed) working-tree state in the
`exp-v2-e2-pareto-observability` worktree, protected by `chmod 444` immutability per the migration
provenance record — which is exactly why it still verified byte-identical to the manifest above. This
is a safe, diagnosed overwrite: replacing bytes that never matched the authoritative record with bytes
that do, not a scientific-content change.

3 files (`run/errors_shard_000.jsonl`, `run_shard1_healthy/errors_shard_000.jsonl`,
`run_shard3_healthy/errors_shard_000.jsonl`) were simply absent from this worktree's committed tree
(never committed at all) and were added, not overwritten.

## 4. Destination determined from existing structure, not invented

- The 21 preserved-directory files recover to their **existing, already-git-tracked repo paths**:
  `results/e2/run/`, `results/e2/run_shard1_healthy/`, `results/e2/run_shard3_healthy/`,
  `results/e2/run_shard4_healthy/`, `results/e2/run_shard5_healthy/` — these directory names are the
  repo's own pre-existing convention (first committed in `dc66e27`) and are the exact relative paths
  recorded in the manifest itself once the `exp-v2-e2-pareto-observability` worktree prefix is
  stripped.
- The 10 `/tmp`-only files (never previously in the repo) recover to two new directories named after
  their own source directories, keeping the repo's existing `run_<label>` naming convention (siblings:
  `run_shard1_healthy`, `run_poison_world`, `run_stuck_worlds`,
  `run_PRERESCUE_INVALIDATED_2026-08-16`): `results/e2/run_rescue_v2_production_out/` and
  `results/e2/run_rescue_v2_smoke_output/`. This directly satisfies the reconciliation report's own
  required-recovery step 2 ("`/tmp` must not hold authoritative record").

## 5. Post-copy verification

All 31 files re-hashed at their new repository destinations: **31/31 MATCH** (sha256 and size, both
against the checkpoint's manifest and against the pre-copy source hashes — byte identity preserved).

## 6. Reconstructed 530-world set (from the repository copies, post-recovery)

Recomputed independently from the 14 `worlds_shard_*.jsonl` and 14 `candidates_shard_*.jsonl` files now
in the repository (not merely re-read from the checkpoint JSON):

| Quantity | Value |
|---|---:|
| Unique completed world IDs | 530 |
| Duplicate world IDs | 0 |
| Torn world JSONL records | 0 |
| Candidate rows | 186,314 |
| Torn candidate JSONL records | 0 |
| Reconstructed world-ID set equals checkpoint's declared `completed_world_ids` | exact match (530/530) |
| Checkpoint world-ID hash — sha256(sorted(world_ids), "\n"-joined), `checkpoint_live_e2.py` convention | `139535c0e59bdbf274ac07fac47373345c50927d791aff3efce91ad79a45b8ad` |
| Remaining 9 ordinary worlds present in the recovered completed set | 0 (confirmed absent) |
| Quarantined poison world present in the recovered completed set | 0 (confirmed absent) |
| 530 + 9 + 1 | 540 (= `total_population_count`) |

No world beyond the checkpoint's own 530 was executed, retried, or classified as part of this recovery.
The 9 remaining ordinary worlds and 1 poison world remain exactly as unresolved as the checkpoint left
them.

## 7. Scope discipline

Only the 31 manifest-listed scientific-record files (`{candidates,worlds,errors}_shard_*.jsonl`) were
copied or overwritten. Sibling operational files present in the same source directories
(`log_shard_*.txt`, `staleness_watchdog.log`, `supervisor_shard_*.log`) were left untouched in
`results/e2/run/` and the `_healthy` directories — they are not part of the authoritative manifest and
carry no scientific content; the corresponding log/manifest files under the two new
`run_rescue_v2_*` directories were copied alongside their source `.jsonl` files for operational
provenance only, not as part of the hash-verified manifest.
