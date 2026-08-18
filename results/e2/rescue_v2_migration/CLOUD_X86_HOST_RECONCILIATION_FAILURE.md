# MURU v2 — New Cloud Host (x86_64) Phase 1 Reconciliation Failure

**Date (UTC)**: 2026-08-18
**Host**: `instance-20260818-004057.us-east4-a` — Linux x86_64, 24 vCPU, 47 GiB RAM, Intel Xeon Platinum 8581C
**Branch**: `claude/e2-rescue-v2-computational`
**HEAD**: `d78e455` (identical to `origin/claude/e2-rescue-v2-computational`)

**VERDICT: `REPOSITORY_DOES_NOT_RECONCILE_TO_PUSHED_CHECKPOINT` — halted at Phase 1.**

---

## 1. What was checked

Phase 1 requires recovering the authoritative checkpoint state from the artifacts rather than
trusting the migration prompt, and halting if the repository does not reconcile.

Both checkpoint artifacts are present and internally consistent with the migration prompt:

- `LOCAL_E2_RESCUE_V2_CHECKPOINT_530.json` — 530 completed, 9 remaining ordinary, 1 quarantined
  poison world, `cloud_resume_safe: true`, `result_integrity: VERIFIED_0_TORN_RECORDS`.
- `MURU_V2_LOCAL_E2_CHECKPOINT_530_REPORT.md` — same population, same stalled-world diagnosis.

The checkpoint's own `result_file_manifest` (31 files, sha256 + size) was then verified against
this host. That is where reconciliation fails.

## 2. Manifest reconciliation result

| Status | Count |
|---|---|
| MATCH (sha256 exact) | 8 |
| HASH_MISMATCH (present but truncated/empty) | 10 |
| MISSING_ON_HOST | 13 |
| **Total manifest files** | **31** |

Representative failures:

| File | Expected bytes | Actual bytes |
|---|---:|---:|
| `results/e2/run/worlds_shard_000.jsonl` | 826,395 | 334,903 |
| `results/e2/run_shard1_healthy/worlds_shard_000.jsonl` | 463,404 | 0 |
| `results/e2/run_shard1_healthy/candidates_shard_000.jsonl` | 33,752,225 | 0 |
| `results/e2/run_shard3_healthy/worlds_shard_000.jsonl` | 179,533 | 0 |
| `results/e2/run_shard4_healthy/worlds_shard_000.jsonl` | 178,263 | 0 |
| `results/e2/run_shard5_healthy/worlds_shard_000.jsonl` | 428,281 | 68,417 |
| `/tmp/e2_rescue_v2_production_out/worlds_shard_00{0,1,2,3}.jsonl` | 89,337 total | absent |
| `/tmp/e2_rescue_v2_production_out/candidates_shard_00{0,1,2,3}.jsonl` | 22,116,362 total | absent |
| `/tmp/e2_rescue_v2_smoke_output/*` | 350,704 total | absent |

## 3. Scientific state actually recoverable on this host

| Quantity | Checkpoint | This host |
|---|---:|---:|
| Completed E2a worlds | 530 | **235** |
| Missing completed worlds | 0 | **295** |
| Candidate rows | 186,314 | **82,294** |
| Torn records among what is present | 0 | 0 |

Missing completed worlds by family: `mass_interaction` 88, `mass_exponential_descriptor` 83,
`mass_saturating_descriptor` 79, `mass_power` 35, `mass_affine_descriptor` 10.

The full list of 295 missing world IDs is enumerated in
`CLOUD_X86_HOST_RECONCILIATION_FAILURE.json`.

## 4. Root cause

The handoff commit `d78e455` recorded the checkpoint JSON and the diagnostic report, but **did not
commit the underlying E2a result data those artifacts describe.**

Ruled out as explanations, each verified directly:

- **Not a sync problem** — local `HEAD` equals `origin/claude/e2-rescue-v2-computational`.
- **Not a shallow clone** — no `.git/shallow`.
- **Not Git LFS** — LFS is not installed and no `.gitattributes` LFS filters exist.
- **Not an uncommitted stash or another branch** — `git stash list` empty; all-branch scan clean.
- **Not history truncation** — a full-history blob scan (`git rev-list --objects --all`) shows the
  larger manifest versions of these files **never existed in any commit on any branch**.
  `results/e2/run/worlds_shard_000.jsonl` has exactly one version in all of history, at 334,903
  bytes. The `run_shard{1,3,4}_healthy` world/candidate files have only ever been 0 bytes.

The 295 missing worlds exist only on the local macOS ARM64 host's filesystem — partly inside the
repository worktree, and partly in that machine's `/tmp`, which is not durable storage.

The checkpoint's `cloud_resume_safe: YES` assertion was evaluated against the local filesystem, not
against what had been pushed. It is correct about the local host and wrong about the remote.

## 5. Consequence

Resuming E2a here would silently rebuild an E2a population from 235 real worlds plus 295 worlds
recomputed on a **different architecture** than the one that produced the rest — an undeclared
mixed-architecture scientific record, produced without a parity qualification, contradicting the
frozen "do not recompute completed worlds" constraint.

No phase beyond Phase 1 was executed. Specifically **not** executed: environment reconstruction,
x86_64 parity qualification, E2a completion, E2b, poison-world retry, the E4a gate, E4a, and
reconciliation. No scientific definition, frozen artifact, or result file was modified.

## 6. Required recovery (needs the local macOS host)

1. On the local macOS ARM64 host, re-verify the 31 manifest files against their recorded sha256.
2. Move `/tmp/e2_rescue_v2_production_out/` and `/tmp/e2_rescue_v2_smoke_output/` into the
   repository under a provenance-labelled directory — `/tmp` must not hold authoritative record.
3. Commit and push the complete result data, then re-verify all 31 manifest hashes post-push from a
   clean clone.
4. Re-run this Phase 1 reconciliation on the cloud host. Only on a clean 530/530 reconciliation
   should Phase 2 (environment reconstruction) and Phase 3 (x86_64 parity qualification) begin.

Note for step 4: this host is **x86_64**, not the previously qualified ARM64. Even after data
recovery, Phase 3 requires the full results-blind parity qualification against frozen E2 reference
cases, treating this host as a new reproducibility boundary.
