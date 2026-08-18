# E2b Held-out Recovery — Provenance Report

**Task**: recover the authoritative sealed evidence backing E2b's frozen identity criterion —
the per-case `selection_count` and cross-seed representative expression, for all 144 held-out
G2 (`family_recovery`) cases — from the local-only macOS host, with no recomputation, inference,
or reconstruction of any value. Artifact recovery only; no scientific search was executed.

## 1. Why this was missing from the repository

`selection_count`, `selection_denominator`, `selection_fraction`, and `discovered_expression_string`
(the cross-seed representative, i.e. the case-level winner selected across a case's 30 seeds) are
fields of the raw sealed per-case record
(schema `muru-rc5-case-record-2.0.0`), produced by the Held-out execution run.

That raw evidence directory — `results/held_out/` inside the execution worktree — was **never
committed to git, on any branch, in any worktree.** Confirmed directly:

```
$ cd .claude/worktrees/muru-heldout-a3-6 && git status --short results/held_out
?? results/held_out/
```

It is untracked (gitignored) and has existed only as local files on this macOS host since the run
finished. Prior sessions in this repository restored the **aggregate** G1/G2/G3 endpoint scoring
from these raw records (see `audit/MURU_HELDOUT_RESCUE_*`, `results/restored/*`), and those
derived, aggregate outputs *are* committed — but no prior commit persisted the **per-case**
`selection_count` / representative pairs themselves. `git log --all` and `git grep` over this
repository confirm no commit at any point contains a `records/PB_held_out_*.json` file or an
equivalent per-case `selection_count` field. This report closes that specific gap without altering
anything else the prior restorations established.

## 2. Source location

| | |
|---|---|
| Host | local macOS host (this machine) |
| Worktree | `/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-heldout-a3-6` |
| Branch | `exec/muru-heldout-a3-6` |
| Worktree HEAD | `8d87143d4280602323aa33ee0b5481aaef0fb4a8` (tag `engineering-rc5-1-heldout-authorization`) |
| Evidence root | `results/held_out/` (untracked, as shown above) |
| Seal receipt | `execution_seal_receipt.json`: `sealed=true`, `case_count=240`, `seed_count=7200`, `file_count=482`, `run_commit=8d87143d…` (matches worktree HEAD exactly) |

This is the same worktree and the same sealed evidence root already established as authoritative
in `v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.json` (`sealed_evidence_root`) and in
`audit/MURU_HELDOUT_RESCUE_RAW_INTEGRITY.md` / `audit/MURU_HELDOUT_SUPERSESSION_LEDGER.md`
(classification: raw sealed evidence **VALID**). Nothing about that prior classification is
revisited or repeated here beyond the fresh, independent hash check in §3 — this report only
recovers the specific per-case fields that were never copied into the repository.

## 3. Verification performed before copying (fresh, this session)

All checks below were re-run in this session against the live files on disk; none is carried
forward from a prior report.

**3.1 — Seal self-consistency.** `execution_seal_receipt.json.file_hashes` lists 482 entries
(240 `records/*.json` + 240 `seed_records/*.json` + 1 `provenance/case_provenance.jsonl` + 1
`execution_manifest.json`). Every one of those 482 files was re-hashed (SHA-256) directly off the
source worktree and compared byte-for-byte against the receipt's recorded value:

```
sealed file count per receipt: 482
missing_on_disk: 0
STRICT mismatches: 0
```

**3.2 — Source commit identity.** `git rev-parse HEAD` in the source worktree returns
`8d87143d4280602323aa33ee0b5481aaef0fb4a8`, identical to `run_commit` in the seal receipt.

**3.3 — G2 case population, derived from frozen registry code, not from the raw files.**
The 144-case `family_recovery` (G2) population was built by calling
`heldout_endpoint_populations.build_endpoint_population("family_recovery")` — the same
registry-derived, non-recomputing accessor already established as authoritative in the prior
restoration (`registry.endpoint_applies_to_variant` / `endpoint_case_count`; raises
`PopulationError` on any size mismatch). It returned exactly 144 case ids, matching
`endpoint_case_count("family_recovery") == 144` and the frozen scorer `rc3_scoring.score_g2`'s
own length assertion. This list, not any manual selection, is what was checked against the raw
records.

**3.4 — Per-case field presence, for exactly those 144 case ids.**

```
Expected G2 case count:                144
Case records found for all 144 ids:    144  (0 missing)
selection_count present:               144 / 144
cross-seed representative present:     144 / 144  (discovered_expression_string, non-null, non-empty)
```

No value was recomputed, inferred, or reconstructed — every value reported is copied verbatim
from the sealed record.

**3.5 — Copy-side integrity, after copying (§4).** Every one of the 482 sealed files, re-hashed
from the copies now inside this repository, matches the seal receipt's SHA-256 exactly (0
mismatches). A `diff -rq` between the source evidence root and the copied evidence root reports
**zero differences** except for the two files already known to be outside the seal and superseded
(`held_out_formal_analysis.json`, `held_out_hostile_audit_report.md` — see
`audit/MURU_HELDOUT_SUPERSESSION_LEDGER.md`; deliberately **not** copied here, since they are
already classified `INVALID` / superseded, not authoritative).

## 4. What was copied, and where

```
results/e2b_heldout/
├── E2B_HELDOUT_RECOVERY_PROVENANCE.md          (this file)
├── G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json   (curated extract, see §5)
└── sealed_evidence/
    └── held_out/
        ├── execution_manifest.json
        ├── execution_seal_receipt.json
        ├── provenance/
        │   └── case_provenance.jsonl
        ├── records/            (240 files — full raw sealed case records; the 144 G2 cases are a subset)
        └── seed_records/       (240 files — full raw sealed per-seed detail)
```

The full 482-file sealed set was copied (not only the 144 G2 subset), because the G2 identity
criterion is verifiable only against the complete manifest, provenance log, and seal receipt, and
because partial copying of a cryptographically sealed set would itself be a form of reconstruction.
`held_out_formal_analysis.json` and `held_out_hostile_audit_report.md` were deliberately excluded —
they sit outside the seal and are already documented as superseded/invalid.

Nothing outside this held-out evidence set was recovered. The repo-wide scan in §6 found other
paths that reference local-only material, but none of them met this task's bar of "clearly
authoritative scientific record" needed right now, so nothing else was copied.

## 5. Curated extract

`G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json` is a direct, lossless projection of the 144 raw
sealed records onto exactly the fields the frozen E2b identity criterion names, plus the hash that
ties each entry back to its source record inside `sealed_evidence/held_out/records/`. It is a
convenience index only — the sealed `records/*.json` files remain the sole authoritative source;
this file changes no value and adds no inference. Per case:

- `case_id`, `family_id`, `partition_label`
- `selection_count`, `selection_denominator`, `selection_fraction`
- `cross_seed_representative_expression` (= sealed `discovered_expression_string`)
- `discovered_family`, `g2_event`
- `source_record_relpath`, `source_record_sha256`, `sealed_receipt_sha256`, `hash_matches_seal`

All 144 entries carry `hash_matches_seal: true`.

## 6. Repo-wide, results-blind audit for other local-only authoritative artifacts

A `git grep` for `/Users/aryav` and `.claude/worktrees/<name>` across all tracked files in the
`muru-v2-stability-study-6537d5` worktree (broadest current checkout) surfaced these worktree
references, each checked against the live filesystem:

| Referenced worktree | Referencing file(s) | Exists on disk now | Disposition |
|---|---|---|---|
| `muru-heldout-a3-6` | multiple (this recovery's source) | Yes | **Recovered in this task** (§4) |
| `heldout-analysis-restoration` | requirement map, tests | Yes | Already reconciled by the prior restoration session; its outputs are the committed `audit/MURU_HELDOUT_*` / `results/restored/*` files. No further recovery needed. |
| `exp-v2-e2-pareto-observability` | `MURU_V2_E2_RESCUE_V2_FEASIBILITY.md`, `MURU_V2_E2_RESCUE_V2_MIGRATION_PROVENANCE.json` | Yes | **Live, actively-modified production E2 run** (`git status` shows in-flight modified shard files as of this session). Explicitly out of scope: this and prior sessions record that the live production run must be left untouched. Not recovered. |
| `muru-engineering-completion-9936eb` | `ENVIRONMENT_CLOSURE.md` | Yes | Referenced only for an environment-closure narrative; no per-case scientific evidence claim attached. Not recovered. |
| `challenge-adjudication-blind` | `audit/MURU_CHALLENGE_BLIND_ADJUDICATION.md` | No (worktree removed) | Historical reference only; nothing left to recover. |
| `muru-paper-benchmark-f16-amendment` | `MURU_PAPER_BENCHMARK_A2_F16_GOVERNANCE_REVIEW.md` | No (worktree removed) | Historical reference only; nothing left to recover. |
| `v2-retention-remediation` | `MURU_V2_E2_RESCUE_V2_PROVENANCE.json` | No (worktree removed) | Historical reference only; nothing left to recover. |

Other absolute-path hits, checked and judged benign / out of scope:

- `artifacts/MANIFEST_massbank.json` → `/Users/aryav/Documents/MURU-ConjectureLab-v1/data/massbank/MassBank-data/LCSB`. This directory exists locally (5,584 files) but is third-party downloaded reference data (MassBank spectral database), not a MURU-generated experimental result — re-acquirable from its public source, not a sealed scientific artifact. Not recovered.
- `docs/superpowers/plans/*.md`, `scripts/build_muru_v1_manuscript_tables.py`, `scripts/e2_rolling_report.py` → local `.venv`/pytest invocation examples and default-path fallbacks, not references to missing evidence.
- `results/e2/rescue_v2_migration/*`, `audit/MURU_HELDOUT_RESCUE_RAW_INTEGRITY.md`, `audit/muru_heldout_rescue_independent_result.json`, `results/restored/heldout_hostile_review.json`, `v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.json` → already-committed provenance narratives that *mention* the same `muru-heldout-a3-6` source this task recovers; no new missing artifact.

No other reference in the scanned tree points to a scientific artifact that is (a) local-only,
(b) not already accounted for above, and (c) clearly authoritative. This audit is results-blind:
it was run by pattern (`/Users/aryav`, `.claude/worktrees/<name>`) before any of §1–§5 was written,
and no file was excluded because of what its contents said.

## 7. Search execution statement

No scientific search was run, restarted, or re-derived at any point in this task. All 7,200 seed
searches behind these 240 records completed under the original Held-out execution
(`run_commit 8d87143d…`); this task only located, verified, and copied their already-sealed output.

---

**E2B_HELDOUT_RECOVERY: COMPLETE — 144/144 G2 cases, `selection_count` and cross-seed
representative both present and hash-verified for every case, 0 missing, 0 mismatches.**
