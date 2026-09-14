# MURU-WUR-v2 MSnLib Confirmation: Phase 0 Preflight

Status: repository integrity and ancestry checks, run before any Phase 1+ work.
This document records what was actually checked and what was actually found,
including one apparent discrepancy that was traced to a benign cause and one
environment-level blocker that stops the study before validation-outcome access.

## 0.1 Ancestry

- Starting HEAD required by the mandate: `dc1f04d0d7ba6ee59fc3baf7be7c4c350671efda`.
- Verified via `git rev-parse` and `git show -s`: commit exists, message
  `"wur v2 run state: terminal"`, authored 2026-09-12 23:33:30 -0400.
- Verified via `gh pr view 5`: PR #5 (`https://github.com/aryavthakur/MURU-ConjectureLab-v1/pull/5`,
  state OPEN, mergeable) has `headRefName=claude/muru-wur-v2-generation-b2ffa1`,
  `headRefOid=dc1f04d0d7ba6ee59fc3baf7be7c4c350671efda` — an **exact match**.
  `baseRefName=fable/wur-stage2-muru-development`,
  `baseRefOid=17027e13614cc850d88bcb72b3e8b8c2458eb00a` — matches the base SHA
  named in Phase 1 of the mandate.
- `dc1f04d0...` is **not** an ancestor of the local `main` tip (`7edc0f2...`):
  PR #5 has not been merged. Confirms "do not continue editing the PR #5
  branch" is moot (it hasn't moved) and there is no risk of accidentally
  building on top of an already-merged, possibly-diverged main.
- New branch `claude/muru-v2-msnlib-confirmation` created with
  `git checkout -b claude/muru-v2-msnlib-confirmation dc1f04d0d7ba6ee59fc3baf7be7c4c350671efda`
  from exactly that SHA. This worktree's harness had already auto-created a
  differently-based branch (`claude/muru-v2-msnlib-confirmation-44b714`, tip
  of local `main`, 7edc0f2) before this session started; that branch is left
  untouched and is **not** used for any of this study's work or commits.

## 0.2 Clean tree

- `git status --short` on `dc1f04d0...` immediately after checkout: empty.
  Confirmed clean before any file in this study was written.

## 0.3 Candidate and comparator hash verification

The mandate's stated "Expected sha256" for `V2_TA_MORGAN_JOINT.json`
(`11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b`) does
**not** equal a plain `sha256sum` of the on-disk file
(`f2ca0322ab75bbcc2ee91e66be07172966d0492060c7669107e1f9081edf58c3`). This
was investigated rather than assumed benign or silently corrected:

1. Confirmed the on-disk file at `dc1f04d` is exactly the git blob committed
   at that SHA (`git ls-tree dc1f04d0... -- artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json`
   → blob `f0e0a8d8...`, matching what a fresh checkout produces).
2. The file has exactly one substantive revision in its git history: created
   at `ed37f8c` (first decision gate) and amended at `96681cb` (Amendment
   A-3 disclosure pass). Diffing both blobs shows the amendment **only
   added** `canary_log_g`, `canary_smiles`, and `feature_spec` (RDKit
   version, Morgan spec, Tier A feature list/scale) — every scientific field
   (`coef_morgan`, `coef_tier_a`, `intercept`, `cfg`, `profile`,
   `tier_a_mean`, `tier_a_sd`, `n_training`) is byte-identical between the
   two versions. The candidate's predictions have not changed since the
   first decision gate.
3. Found the actual cause: `src/muru/wur_v2/candidate.py` defines
   `sha256_of(obj) = sha256(json.dumps(obj, sort_keys=True, separators=(",",":")))`
   — a **canonical-JSON** hash, not a raw-file hash. Recomputing with this
   exact function against the loaded (parsed) JSON reproduces the mandate's
   stated hash **exactly**: `11aa801c...9e9b`. The committed
   `artifacts/wur_v2/candidate/candidate_manifest.json` independently records
   the same value for the same reason.
4. Comparator `V2_REF_TA_RIDGE.json` checked the same way: canonical-JSON
   hash `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32`,
   matching `candidate_manifest.json`'s recorded value exactly. (Raw-file
   sha256 is `de9afa119b80ddc46ffebf98783ac18bfa97c79f0e9e7adf57c300cd9fc6146f`
   and is recorded here for completeness but is not the governing hash.)

**Conclusion: no integrity failure.** The candidate and comparator files at
PR #5 head are exactly what was frozen; the discrepancy was a
raw-bytes-vs-canonical-content hashing convention, not a content change.
All further hash verification in this program uses the repository's own
`canonical_json`/`sha256_of` convention, not `sha256sum`.

| File | Canonical-JSON sha256 | Matches mandate/manifest |
|---|---|---|
| `V2_TA_MORGAN_JOINT.json` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` | yes |
| `V2_REF_TA_RIDGE.json` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` | yes |
| `V2_REF_B1_MASS.json` | `3e8b889c9b096dec2e03b01ad900b49ad3046fb56c0795c54e39150c64c2ab56` (manifest value, not independently re-derived) | n/a |
| `V2_REF_B0_NULL.json` | `b910cc0d8a16002612a010d5898cf436edd4dd0ac60612371e8fdfac7b7ff56a` (manifest value) | n/a |

## 0.4 Training-population hash

- `V2_TA_MORGAN_JOINT.json`'s embedded field `training_keys_sha256` =
  `81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd` — matches
  the mandate's stated development training-population hash exactly.
- `artifacts/wur_v2/data/population_manifest.json`'s `keys_sha256` field is
  the same value, `n_compounds: 1325` (matches candidate `n_training`).
  Manifest also records `n_scaffold_groups: 765`, `n_strict_clusters: 558`,
  and the frozen bridge constants `a=-5.95552603907965`, `b=0.8618030610784555`
  used by the A0 energy map (§0.6 below).

## 0.5 Existing external-access records (disclosure, not re-litigation)

Every access record under `artifacts/wur_v2/external*` was enumerated. All
four are `"kind": "ANCHOR_CALIBRATION"`; none is `"kind": "VALIDATION"`:

| Record | git_head | n_allowed_spectrum_keys |
|---|---|---|
| `artifacts/wur_v2/external/anchor_calibration_access.json` | `6c6cc4f` | 1292 |
| `artifacts/wur_v2/external/anchor_diagnostics_access.json` | (MultiMS2 anchor diagnostics) | — |
| `artifacts/wur_v2/external_msnlib/anchor_calibration_access.json` | `a41ea4e` | 1935 (first attempt; stopped before any decode — MS-Numpress) |
| `artifacts/wur_v2/external_msnlib/anchor_calibration_access_attempt2.json` | (rerun after decoder fix) | 1935 |

The frozen final result of the anchor gate (`MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`,
Part IV) was independently re-read and cross-checked against the mandate's
stated numbers:

| Adapter | NCE20 median abs delta / Spearman | NCE60 | pooled RMSD | passes |
|---|---|---|---|---|
| A0 (frozen WUR map, no free parameter) | 0.0501 / 0.882 | 0.0320 / 0.902 | 0.0784 | no (NCE20 median exceeds 0.05 by 0.0001) |
| A1 (`E = k*NCE`) | 0.0500 / 0.881 | 0.0450 / 0.901 | 0.0811 | no (RMSD exceeds 0.08 by 0.0011) |
| A2 (`E = a + b*NCE`) | 0.0506 / 0.881 | 0.0303 / 0.902 | 0.0782 | no (NCE20 median exceeds 0.05) |

All values match the mandate's stated figures. 402 census anchors, 328 with
both fixed rungs under the frozen rules, 1,935 anchor scans decoded, only
anchor wells downloaded — all confirmed against
`MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` Part IV text. **The old gate was
applied literally and failed; this document does not revisit, round, or
reinterpret that result.**

## 0.6 No MSnLib validation-outcome access exists yet

- `git grep` at `dc1f04d0...` for `msnlib_validation`: zero hits. `git
  grep` for `validation_access` and `validation_result` (broader terms,
  not MSnLib-specific) returns 5 hits, **not zero as an earlier draft of
  this document incorrectly stated** — corrected here after an independent
  review caught it. All 5 are source code and prose for
  `scripts/wur_v2/ext03_validation.py`, the **pre-existing, never-executed
  MultiMS2** "one look" script (guarded by `AccessGuard("VALIDATION", ...)`,
  and itself gated on `cal.get("qualified")`, which is false because
  MultiMS2's own anchor calibration never qualified) — not MSnLib, and not
  an executed result. `git ls-tree` on `dc1f04d0...` confirms no actual
  `validation_access.json` or `validation_result.json` data file is
  tracked anywhere in the repository at that commit, for either MSnLib or
  MultiMS2. The substantive conclusion is unchanged; the literal "zero
  hits" phrasing was wrong and is not repeated.
- Filesystem search for `*.mzml*` anywhere in the repository (tracked or
  untracked): **zero hits**. Raw spectra were never committed, consistent
  with the mandate ("do not commit raw multi-gigabyte mzML").
  `artifacts/wur_v2/external_msnlib/` contains only derived summaries
  (`anchor_mu.csv`, `anchor_wells.csv`, calibration/access JSON) — the raw
  anchor mzML files themselves are **not** present in this checkout either
  (they were downloaded transiently in a prior session/environment and
  never committed, by design).
- Checked `~/Downloads` and did a shallow filesystem search for any
  `*msnlib*` path outside the repository on this machine: none found.
- `AccessGuard` (`src/muru/wur_v2/external_guard.py`) refuses to construct a
  second guard of a given `kind` if a record already exists at its path; no
  `VALIDATION`-kind record exists anywhere, so a fresh guard for this study
  is legal to construct once its prerequisites (frozen protocol committed,
  clean tree) are met. This class is reused as-is for the new study rather
  than reimplemented.
- **Conclusion: no MSnLib validation outcome has been exposed.** The
  population has not been sampled, downloaded, peak-decoded, scored, or
  used for any model-selection decision.

> **CORRECTION, added 2026-09-13 (study-2 preparation). The conclusion above
> was true when written (Phase 0, before sampling) and is no longer true.**
> Later on 2026-09-13 the confirmation sample was drawn and downloaded, and
> a parser-preflight script accidentally decoded validation-population MS2
> peak arrays (964 spectra matching 350 eligible validation compounds, by
> positional scan selection in pooled wells). One validation mu value
> (compound `MURAVORBGFDSMA`) was visibly printed to the operator. The whole
> 2,000-scaffold-group sample is permanently EXPOSED. No confirmatory one
> look was executed and no P1, ratio, bootstrap or AF was computed. Full
> record: `MURU_V2_MSNLIB_CONFIRMATION_POPULATION_EXPOSED.md`. The original
> text above is kept unchanged as history.

## 0.7 MultiMS² remains untouched

`artifacts/wur_v2/external_census/multims2_census.json` →
`outcome_blind_declaration.peaks_or_intensities_accessed: false`; explicit
`files_not_downloaded` list covers every MultiMS2 mzML/MGF archive (Zenodo
17250693, Zenodo 17417089, MassIVE MSV000099369, the GitHub MGF); only
header/identity/plate-metadata TSVs were fetched, with outcome columns
(`LIBQUALITY`, `SELFIES`) explicitly dropped unseen. No MultiMS2 decode or
validation-access record exists anywhere in `artifacts/wur_v2/`. Confirmed
untouched.

## 0.8 CRITICAL BLOCKER: no network egress to the MSnLib data host

This is the one prerequisite that does **not** pass, and it stops the study
before validation-outcome access, exactly as the mandate requires.

Tested from this sandboxed execution environment:

| Host | Result |
|---|---|
| `github.com` | HTTP 200, 0.49s |
| `zenodo.org` (bare HTTPS connect, no path/query, no dataset request) | `curl: (28) Operation timed out`, tested at 10s and 15s timeouts |
| `gnps-external.ucsd.edu` (bare HTTPS connect) | `curl: (28) Operation timed out`, 15s |
| DNS for `zenodo.org` | resolves fine (multiple A records via the sandbox's resolver; an independent re-check moments later saw a different record count — 6 vs. this run's 3 — consistent with anycast/load-balancer rotation, not a resolution failure) |
| ICMP to `8.8.8.8` | 0% loss, ~9ms |

DNS and ICMP both work, and `github.com` is fully reachable, so this is not
a general network outage — it is a host-level egress allowlist that does not
include the MSnLib data hosts (Zenodo / GNPS-external / presumably MassIVE).
No `http_proxy`/`https_proxy` override is set that could route around it.

Two connectivity probes were made (`https://zenodo.org`,
`https://gnps-external.ucsd.edu`, both bare domain roots, no path, no query
string, no dataset or scan identifier). Neither returned any content —
both timed out at the TCP/TLS layer before any HTTP response, successful or
otherwise. **This is not an MSnLib data-access event**: no scan ID, compound
identity, or outcome value was requested or could have been returned by a
timed-out connection attempt to a bare domain root. It is recorded here only
as the evidence for the blocker, not as a first look.

**Consequence.** Phase 4 of the mandate ("HEADER-ONLY PREFLIGHT", "PARSER
PREFLIGHT", and "FIRST VALIDATION EXECUTION") requires downloading
previously-untouched MSnLib validation records — at minimum scan headers,
and then centroid peak arrays for the frozen NCE20/NCE60 rungs. That is
categorically impossible from this sandbox: there is no cached local copy of
the census design frame's underlying raw files, no cached copy of the
anchor-well mzML files (only their already-committed derived summaries), and
no route to fetch anything new from Zenodo, GNPS, or MassIVE.

Per the mandate's own governing rule: *"If any prerequisite fails in a way
that threatens... the independence of the external test, STOP before
validation outcome access and report the blocker."* This blocker is
reported here, before any validation outcome access, and the run proceeds
only through the phases that do not require it (Phase 1 regression, Phase 2/3
reproducibility, and writing — but not executing — the Phase 4 confirmation
protocol). See `MURU_V2_MSNLIB_CONFIRMATION_RESULT.md` for the final
disposition (`VALIDATION NOT EXECUTED`).

## 0.9 Environment identity (for the reproducibility manifest, §Phase 3)

- Python: 3.13.12; OS: Darwin 25.1.0 arm64 (macOS, Apple Silicon).
- numpy 2.5.2, scipy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, rdkit
  2026.03.5, pymzml 2.6.1.
- Full versions recorded again, with the actual test-suite invocation, in
  `MURU_V2_REPRODUCIBILITY_MANIFEST.md`.
