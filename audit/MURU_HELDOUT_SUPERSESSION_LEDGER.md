# MURU Held-out — Supersession Ledger

Status of every post-run analysis object, with its disposition and hash. Nothing is deleted.

## 1. Superseded objects

**Classification: `SUPERSEDED - POST-RUN ANALYSIS CONTRACT DRIFT`**

Every one of these was untracked in git at the time of the defect — never committed, never part of
any frozen engineering line. They are preserved verbatim in this worktree under
`superseded/post_run_analysis_contract_drift/`, where they are now committed and therefore
permanently recoverable.

| Original path (execution worktree `exec/muru-heldout-a3-6`) | SHA-256 of the preserved copy |
|---|---|
| `src/muru/paper_benchmark/held_out_analyzer.py` | `3c85a262ea9f8722a5c677395ac7ea269c5cff45b8490038460935f595bb9bf7` |
| `src/muru/paper_benchmark/independent_recomputation.py` | `2ba5941426572fdffb5117dc910c086f10cb3943ea90bf438bc951f976d19fe1` |
| `src/muru/paper_benchmark/hostile_reviewer.py` | `50250fd808c1831602dc360580b55f5553a048e37f58ce9da876b85c1dc581a9` |
| `src/muru/paper_benchmark/pipeline.py` | `48823fd984551d59c76ab4b3bf27960b551b359604f0207aad09414d6c84fb3d` |
| `scripts/run_post_held_out_pipeline.py` | `cf61c39909ac2528c67c4700d9c49eff11d129bc2fb30520191c1ca98f3a2f2c` |
| `results/held_out/held_out_formal_analysis.json` | `38c3c5b5fcf71d7d84a85ac261b900cd0ca2c79c4490de5db83cc898a7f72486` |
| `results/held_out/held_out_hostile_audit_report.md` | `3794edc4f3b342725bfee9adcf8a0763d2bcfc4c55654014caa30234e74b0ed8` |

### Why the originals were not edited in place

The two output files live inside the evidence directory. They are **outside the seal** — the seal
covers exactly 482 files (240 records + 240 seed records + 1 provenance log + 1 execution manifest),
and both outputs were written at 09:02:00, after the seal was taken at 09:00:11. Superseding them
therefore touches no sealed evidence.

Even so, **nothing was written into or removed from the evidence root**. Marking the originals in
place would have added or altered files inside a directory whose integrity is the foundation of
every claim in this study, for no evidential gain. The supersession is recorded here, in a
committed ledger, with content hashes that pin exactly which bytes are superseded. A future reader
can verify the correspondence without trusting this document.

## 2. What was wrong with each

| Object | Defect |
|---|---|
| `held_out_analyzer.py` | Scored every endpoint over `len(expected_case_ids)` = 240; used `candidate_test_r2 ≥ 0.80` as G1; used `SUCCESS **OR** support==MATCH` as G2; invented a G3 rule with inverted direction; read Gate 7 as full structural acceptance; computed `gate8 = gate7 AND g1`; read F9 from a field fixed to `NOT_PROVEN_FOR_HARD_GATE`; accepted `BOUNDARY_LIMITED` and a non-existent `M1_NOT_REJECTED` as adequate, making `is_adequate` true for all 240 cases; emitted an existence-only `decision_passed`. |
| `independent_recomputation.py` | Imported `HeldOutAnalysisReport` from the analyzer it was meant to check, shared its constants and helpers, and cloned every rule line for line. Its "0 discrepancies" is exactly what two copies of one wrong rule must produce. |
| `hostile_reviewer.py` | Claimed seven lenses, contained six, all sequential calls in one module. Its denominator lens **asserted every endpoint total equalled 240** — certifying the central defect and guaranteeing rejection of a correct analysis. Its Gate 7 / Gate 8 lens branched on `gate7_pass`, `gate8_pass`, `g1_wilson_lower`, none of which exist in the record schema, so its sole condition never fired. |
| `pipeline.py`, `run_post_held_out_pipeline.py` | Orchestration for the above. |
| `held_out_formal_analysis.json` | The emitted numbers: G1 119, G2 23, G3 2, Gate 7 25, Gate 8 24, F9 0, all over a 240 denominator, with `decision_passed: true`. |
| `held_out_hostile_audit_report.md` | The rendered six-checkpoint review that passed. |

Timing, from the forensic diff: all machinery was authored 00:36–00:46 outcome-blind; execution ran
00:39–08:50; the seal was written 09:00:11; **four analysis files were then edited at 09:01:32–09:01:59
with outcomes fully accessible**, and the reported analysis was emitted at 09:02:00 — one second
after the last edit. `held_out_analyzer.py` and `independent_recomputation.py` share an identical
modification timestamp, indicating one coordinated edit rather than two independent authorships.
Absent committed history, the supportable classification is **scientific semantic change of unknown
provenance, applied after outcomes were visible**.

## 3. Retained as valid

| Object | Status | Reason |
|---|---|---|
| `results/held_out/records/` (240) | **VALID, SEALED** | 482/482 files re-hash correctly; re-running the frozen acceptance predicate over all 240 reproduces the stored verdicts with 0 disagreements |
| `results/held_out/seed_records/` (240 / 7,200 seeds) | **VALID, SEALED** | no duplicates; every seed matches `rc5_seeds.case_search_seeds` |
| `results/held_out/provenance/case_provenance.jsonl` | **VALID, SEALED** | single run commit `8d87143d…`, no re-run entries |
| `results/held_out/execution_manifest.json` | **VALID, SEALED** | digest `bcd197dc…` recomputes |
| `results/held_out/execution_seal_receipt.json` | **VALID** | `sealed=true`, 240 cases, 7,200 seeds, run commit matches |
| `src/muru/paper_benchmark/post_execution_sealer.py` | **VALID, CARRIED FORWARD** | authored 00:43, never edited after outcomes; the one post-run module with clean provenance. Copy SHA-256 `37eab2f7799cac24c368d5d93e4d472520908819e91ff1d42b0cb272714009dc` |
| The five forensic rescue artifacts | **AUTHORITATIVE** | committed at `b16d274`; all five hashes verified before use |

## 4. Replacing objects

| New object | Replaces | Discharges |
|---|---|---|
| `src/muru/paper_benchmark/rc5_record_payload.py` | — | requirement 10 (no branching on absent fields) |
| `src/muru/paper_benchmark/heldout_endpoint_populations.py` | — | requirement 1 (registry-built populations) |
| `src/muru/paper_benchmark/heldout_contract_analysis.py` | `held_out_analyzer.py` | requirements 2–8 |
| `src/muru/paper_benchmark/heldout_g1_recovery.py` | — | requirement 9 (zero-search G1) |
| `src/muru/paper_benchmark/heldout_independent_scoring.py` | `independent_recomputation.py` | requirement 11 |
| `src/muru/paper_benchmark/heldout_hostile_lenses.py` | `hostile_reviewer.py` | requirement 12 |
| `scripts/run_heldout_restored_analysis.py` | `run_post_held_out_pipeline.py` | orchestration |
| `scripts/run_heldout_hostile_lenses.py` | — | orchestration |
| `tests/test_heldout_analysis_restoration.py` | `tests/test_held_out_analyzer.py` | regression |
| `tests/test_heldout_superseded_rules_differ.py` | — | differential proof the repair is not a relabelling |
| `tests/test_heldout_hostile_lenses_have_teeth.py` | — | mutation proof the lenses can fail |

## 5. Pre-existing defect disclosed, deliberately not repaired here

`tests/test_rc5_authorized_delta.py::test_every_pinned_post_change_hash_matches_the_working_tree`
**fails at this commit, and failed before this session began.**

| Artifact | SHA-256 of `src/muru/paper_benchmark/rc5_authorization.py` |
|---|---|
| A3.5 authorized-delta ledger pin (`scripts/pb_rc5_a3_5_authorized_delta.py`) | `fd1dfe745feaf4344a08678eb6266e3bfb87add119b9927f78550ed70ebcfc72` |
| File content at A3.5 engineering commit `7cdd5a6` | `fd1dfe74…` — matches the pin |
| File content at A3.6 run commit `8d87143` | `e8fc53c50fb8873cc4989db03e49ec5beb33872967f7cc1c4f5a14be8272ed2c` |
| File content in this repair worktree | `e8fc53c5…` — identical to the run commit, unmodified |

**Cause**: A3.6 legitimately changed `AUTHORISED_PARTITIONS` from `{"development"}` to
`{"development", "held_out"}` — the authorization-only delta the rescue verified independently — but
did so on a file pinned by the *A3.5* ledger without recording that in an A3.6 ledger or superseding
the A3.5 pin.

**Classification**: governance bookkeeping, not science. The change itself is authorized, verified,
and semantically confined to partition permission.

**Not repaired here, deliberately.** The A3.5 ledger is a frozen record of the A3.5 delta. Editing
it to accommodate a later amendment would falsify what it attests. The correct instrument is an A3.6
ledger or erratum, which is a governance act outside this restoration's remit. Recorded so it cannot
be mistaken for damage introduced by the repair.

A second pre-existing condition: `tests/test_ov_pipeline.py` errors on a missing
`artifacts/p2_compounds.parquet`, a large data artifact absent from this worktree. Environmental,
unrelated to the restoration.

---

**SUPERSESSION LEDGER COMPLETE — NOTHING DELETED, NOTHING SEALED WAS TOUCHED**
