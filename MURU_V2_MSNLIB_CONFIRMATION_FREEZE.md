# MURU-WUR-v2 MSnLib Confirmation: Final Freeze (before the one look)

> **⚠ VOID — DO NOT EXECUTE. This freeze's validation population is
> PERMANENTLY EXPOSED and must never be used for a confirmatory claim.**
> A parser-preflight scoping bug decoded real peak data for 964 spectra
> matching validation-population compounds, and the operator saw one real
> validation μ value (compound `MURAVORBGFDSMA`), before this freeze was ever
> committed and before any guard existed. Full incident record:
> `MURU_V2_MSNLIB_CONFIRMATION_POPULATION_EXPOSED.md`. This document is kept,
> not deleted, as a record of a methodology and infrastructure that is
> otherwise sound (transport, guard hardening, statistics, all independently
> reviewed) — but the specific 2,000-scaffold-group sample it describes is
> dead. Do not construct `ConfirmationAccessGuard` against this freeze. A new
> validation design, with a new sample, is required and is out of scope for
> this document.

**Study identifier:** `muru-v2-msnlib-confirmation-1.0`
**Protocol:** `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`, sha256
`5b5ba790cd209352db0c0dfeb2d526f04874aded854bb3d73eb273e07cd9a93d`.
**Machine-readable companion:** `artifacts/wur_v2_confirmation/freeze_manifest.json`
(every hash below is duplicated there for the one-look guard to verify
programmatically against the live population at construction time).
**Status:** VOID (see banner above). Everything below describes what was
committed and reviewed before the exposure incident was discovered; it is
historical, not actionable.

## 1. Frozen model, unchanged from PR #5 / PR #6

| Role | Model | Canonical-JSON sha256 |
|---|---|---|
| Candidate | `V2_TA_MORGAN_JOINT` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` |
| Primary comparator | `V2_REF_TA_RIDGE` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` |

Both independently recomputed from the on-disk candidate files at freeze time
via `muru.wur_v2.candidate.sha256_of` and confirmed to match exactly (no
retraining, no coefficient change). Training population: 1,325 keys, sha256
`81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd`.

## 2. Deployment map, endpoint, rung and matching rules (unchanged)

- **A0, zero MSnLib-fitted parameters:** `E_LCSB = (NCE - a_WUR) / b_WUR`,
  `a_WUR = -5.95552603907965`, `b_WUR = 0.8618030610784555` (frozen Stage 1
  bridge). A1/A2 are not used for the confirmation look.
- **Endpoint:** `mu = sum(I*m)/sum(I)/m_prec` over all centroid peaks of the
  matched MS2 scan (precursor included, no intensity cutoff); `m_prec` =
  theoretical [M+H]+; per (compound, rung) = median over matched scans across
  the compound's used wells.
- **Fixed rungs:** NCE 20 and 60 only. `muru.wur_v2.external_msnlib.fixed_rung_scans`:
  within a run of consecutive MS2 scans sharing one selected-ion m/z, the
  first scan with collision energy 20 is rung 20, the last scan (run length
  ≥ 2) with energy 60 is rung 60. The Assisted scan is never used.
- **Matching:** selected-ion m/z within 0.01 Da of the theoretical [M+H]+;
  matched scan window lower limit ≤ 40, upper limit ≥ [M+H]+ + 1.
- **Support/exclusion:** a compound is excluded from the primary endpoint if
  either model's `u = (E/30)/g_hat` falls outside the frozen profile's knot
  range at either rung (`muru.wur_v2.candidate.supported`); counted, not
  silently dropped.

## 3. Design 12b population, sampling, and the frozen sample (unchanged from Step 6)

- **Design 12b population** (outcome-free, structure/identity only):
  39,238 compounds, 29,562 scaffold groups. Reconstructed independently from
  the nine pinned MERLIN identity tables (`raw.githubusercontent.com`,
  commit `ed7f85f`, every file's sha256 verified against the census's own
  fetch log) and confirmed against the recorded population sha256
  `8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e` — exact
  match.
- **Eligible scaffold-group list**, `sorted(eligible_group_ids)` on the plain
  `scaffold_group_v2` identifier, ascending, hashed **before** sampling:
  sha256 `809f14c4d2528661be39e169aacf67b8618f736db6d1d17afd2a7914c67f07b9`
  (29,562 groups).
- **The one sample** (drawn once, no reroll): `numpy.random.default_rng(20261010)
  .choice(sorted_ids, size=2000, replace=False)` → **2,000 scaffold groups,
  2,690 compounds**.
- **Required wells:** 2,402 (one preferred acquisition per well; 262 wells
  are pooled and serve more than one sampled compound).

## 4. Transport (item 1 of the confirmation mandate)

All 2,402 required wells are physically accounted for:

| Source | Files | Notes |
|---|---|---|
| MassIVE MSV000094528 | 98 | Preserved from a bulk-fetch route later cancelled by explicit instruction (0 failures at cancellation; single-threaded, polite, `Retry-After`-aware retry after an initial 4-worker attempt re-triggered `mod_qos` rate limiting — that attempt's log is preserved, not deleted, at `artifacts/wur_v2/external_msnlib/massive_download_provenance.attempt1_too_aggressive.jsonl`) |
| Nine official Zenodo positive-mode mzML archives (DOI `10.5281/zenodo.15683784`) | 2,304 | All nine archives authenticated: byte size, MD5, and SHA256 independently recomputed and matched against both the user-supplied provenance and this repository's own prior (`msnlib_census.json`) central-directory record |

Spot-verified: MassIVE and Zenodo serve **byte-identical** content for the
same well (e.g. `pluskal_mce_1D1_A12_id`, sha256
`5ae3905047c23de2aac73aa389d273ba8631f0d41906eb26d27e69144f2ebe0d` on both
sources) — the two transports are interchangeable, not a hidden confound.
Full per-file source/path/size/sha256 row list:
`artifacts/wur_v2_confirmation/transport_provenance_manifest.json`
(sha256 `ee63202c08fdd503c46e3a70a49de7802034b52298817dfa55235649dd4ce2a6`).
41 wells across both transports needed a disclosed duplicate-acquisition
tie-break (prefer the production/`100AGC_60000Res_` variant, else the
plain filename over a resubmission-timestamped one, else the latest
timestamp) — every instance is flagged in that manifest, none silently
dropped.

Raw mzML is never committed to git (`data/external/` is gitignored); only
derived headers, hashes, and aggregated mu values ever enter version
control.

## 5. Header-only eligibility (item 3)

`scan_headers()` (removes `binaryDataArrayList` before reading any
`cvParam` — no `<binary>` array is ever touched at this stage) +
`fixed_rung_scans` + `match_compounds` + `eligible`, all reused verbatim
from `muru.wur_v2.external_msnlib` — no new eligibility logic was written
for this study.

| Stage | Compounds | Scaffold groups |
|---|---|---|
| Sampled | 2,690 | 2,000 |
| Required file present on disk | 2,690 | 2,000 |
| **Survive header-only eligibility (both rungs, window ok)** | **2,140** | **1,658** |

7,616 eligible (file, spectrum_id) scan pairs identified. **1,658 ≥ the
frozen 500-group floor — the study proceeds.**

- **Validation key hash** (sorted eligible compound keys):
  `2e3dec7e085e628c86b6c1031a33b57479f941b87ff5282e9ab595c3790d5590`
- **Scaffold-group hash** (sorted eligible group ids):
  `c6d2713a04801eb5db678aaf7ff79599c40d3313c85cf76b63791531cff157ff`
- **Spectrum-manifest hash** (sorted `file:spectrum_id` for every eligible,
  window-ok matched scan): `c7c7ccafb3352060ccf938f96018b7e9f5fde93b5b154b35441968ac807ad748`

No intensity, peak count, TIC, base peak, μ, precursor survival, or model
prediction was used anywhere in this filter — only scan id, MS level,
selected-ion m/z, collision energy, and scan-window bounds.

`artifacts/wur_v2_confirmation/eligible_population.parquet` (key, smiles, mh,
scaffold_group; one row per eligible compound — `scripts/wur_v2_confirmation/08b_build_eligible_population.py`)
is the auditable restriction of the frozen sampled population to exactly
these 2,140 keys, asserted at build time to contain no MURU-development key
and no key outside the eligible set. `11_run_one_look.py` recomputes header
eligibility live (re-running `08_header_eligibility.py`'s core function)
immediately before constructing the guard, rather than trusting a
potentially-stale cached JSON — this is what makes the guard's
population/scaffold/spectrum-manifest hash cross-check a real check against
the current on-disk files, not a comparison of one static file to another.

## 6. Structural-novelty bins (item 7 of the earlier mandate, frozen pre-look)

Fixed bands (`<0.30`, `0.30–0.50`, `0.50–0.70`, `≥0.70`) computed by maximum
Morgan-count Tanimoto similarity to the 1,325-compound development
population: the `≥0.70` band held only 6 compounds (< the 30-compound
floor), so the pre-registered quantile fallback applies automatically:

| Bin | Range | n |
|---|---|---|
| Q1 | [0.000, 0.289) | 672 |
| Q2 | [0.289, 0.326) | 668 |
| Q3 | [0.326, 0.371) | 677 |
| Q4 | [0.371, 1.000) | 673 |

Per-compound assignments: `artifacts/wur_v2_confirmation/novelty_bins_per_compound.csv`.
Never used to exclude a primary compound; interpreted strongly only if the
primary confirmation result is itself supported (§9).

## 7. Parser preflight on exposed anchors only (item 4)

Re-exercised the complete parser end-to-end on all 561 already-exposed
anchor wells (calibration data from the original anchor gate,
`MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` Part IV — re-decoding it creates no
new outcome exposure and needed no VALIDATION guard). **The 2,402
validation-population files, though present in the same local directory,
were explicitly excluded from this pass by filename allowlist — this
preflight never touched them.**

- MS-Numpress PIC (+ zlib) decoded on all 561 files; every decode repeated
  twice and compared bit-for-bit (0 non-deterministic decodes).
- `MS:1000519` ("32-bit integer") appears alongside the Numpress-PIC
  accession on intensity arrays — this is the nominal pre-compression type
  tag Numpress-PIC always carries; the decoder branches on the Numpress
  accession itself, never on this tag, so it does not affect decode
  behavior. No other unanticipated compression/encoding accession was
  found.
- Array lengths agreed with `defaultArrayLength` in all cases (0 failures).
- Sample precursor-inclusion / selected-ion-matching / endpoint sanity
  check on real decoded arrays produced finite, in-range μ values.
- Full results: `artifacts/wur_v2_confirmation/parser_preflight.json`.

## 8. Environment

`artifacts/wur_v2_confirmation/environment_manifest.json`, sha256
`da69aa0ef9a7f6073d109f5684e16c60a3c0c050cbd8dcee4a487724485086d3`: Python
3.13.12, numpy 2.5.2, scipy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, rdkit
2026.03.5, pymzml 2.6.1, lxml 6.0.2, pyarrow 25.0.1 — identical interpreter
used throughout this study. This is a confirmation-study-specific record; it
does not modify `requirements.lock.txt`, which remains under its own,
separate RC4-era environment-closure contract (with its already-disclosed
`lxml` gap, `MURU_V2_REGRESSION_VERIFICATION.md` §4).

## 9. Primary estimand, bootstrap, and decision rule (frozen, unchanged from the protocol)

- **P1** = pooled two-rung RMSE over all eligible compound-rung cells
  (`muru.wur_v2.metrics.p1`), for both candidate and comparator.
- **P1_ratio = P1_candidate / P1_TierA.** Also reported: P1 difference,
  MRMSE, median compound RMSE, Q90, Q95, CVaR95, AF (compound two-rung RMSE
  > 0.20), AF_max (any rung |error| > 0.30), per-rung breakdown.
- **Bootstrap:** whole validation scaffold groups, B = 10,000, seed =
  20261011, `muru.wur_v2.metrics.cluster_bootstrap` — P1 of both arms
  recomputed inside every replicate.
- **Decision rule**, applied literally, not reinterpreted after the look —
  evaluated in this order (a disjunctive override, not just the ratio/CI
  branches in isolation):
  1. Point ratio ≥ 1.00, **or** the secondary AF tail-risk check is
     materially adverse (whole-scaffold-group bootstrap upper-95%
     `AF_diff` CI exceeds the pre-specified +0.03 noninferiority
     tolerance) → **failed to transfer**, regardless of how favorable the
     point ratio looks.
  2. Otherwise, if the upper-95%-bootstrap `P1_ratio` CI `< 1.00`: point
     ratio ≤ 0.95 → **practically meaningful confirmation**; point ratio
     `> 0.95` → **modest confirmation**.
  3. Otherwise (ratio `< 1.00` but the 95% upper bound includes 1.00) →
     **directionally favorable but inconclusive**.

## 10. Prior anchor-gate disclosure (not revisited)

The MSnLib absolute-agreement anchor gate **failed at all three tested
adapters**: A0 NCE20 median |Δμ| 0.0501 (required ≤ 0.05, over by 0.0001),
A1 pooled RMSD 0.0811 (required ≤ 0.08), A2 NCE20 median 0.0506 — margins
the source document itself calls smaller than anchor sampling noise. This
confirmation study does not reinterpret, round, or re-litigate that result;
it tests a narrower, differently-scoped comparative claim under the same
fixed A0 map.

## 11. Prohibited after this freeze

No change to the candidate, comparator, A0 map, endpoint, sample or its
seed, bootstrap rule, success thresholds, or novelty-bin analysis. No
second population draw. No repair-and-revalidate. HEAD at first validation
access must equal the commit that carries this document and its manifest
(no outcome-neutral allowlist is declared here — none is needed, since the
freeze commit is the last commit before the guard runs).

## 12. Independent pre-access review

Four independent adversarial reviewers (leakage, statistics, implementation,
governance) audited this study before this freeze was committed. The
statistics reviewer found two real, pre-outcome implementation gaps, both
fixed before this document reached its final form (not after — no scientific
rule changed, only code correctness):

1. `scripts/wur_v2_confirmation/12_external_analysis.py`'s decision logic
   omitted the frozen tail-risk override (§9 above already states the
   corrected rule). Fixed by adding the `AF_diff`/`AF_diff_ci` check as a
   disjunctive precondition to `FAILED_TO_TRANSFER`, evaluated before the
   ratio/CI branches.
2. `artifacts/wur_v2_confirmation/eligible_population.parquet` was read by
   two scripts but had no builder anywhere in the tracked tree, so its
   no-leakage and consistent-scaffold-group properties could not be
   verified from code. Fixed by writing
   `scripts/wur_v2_confirmation/08b_build_eligible_population.py`, an
   auditable filter with build-time assertions (exact key-set match, no
   overlap with the 1,325-compound MURU development population).

Full reviewer output: `artifacts/wur_v2_confirmation/pre_access_review.json`
(written after this document is committed, alongside the outcome of all four
reviews).

Two further, self-caught corrections, disclosed for the same reason: (a)
this repository's `.gitignore` excludes `*.parquet` globally, which would
have silently dropped `eligible_population` and the eventual one-look
`measured_mu` outputs from the tracked/auditable record despite living
under the otherwise explicitly un-ignored `artifacts/wur_v2_confirmation/`
— all such outputs are written as CSV instead; (b) the guard's
`expected_freeze_commit` cannot be a field stored inside
`freeze_manifest.json` itself (a commit's hash is a function of its own
tree, so no commit can embed its own resultant SHA) — `11_run_one_look.py`
resolves it live via `git rev-parse HEAD` instead, which only holds
meaning because this script is run immediately after the freeze commit
with nothing else committed in between.

## 13. Tracked tree

Clean at commit time (verified by `git status --porcelain` immediately
before this commit). The one-look guard (`ConfirmationAccessGuard`,
`src/muru/wur_v2/confirmation_guard.py`) additionally requires this exact
document and its manifest to be byte-identical, at construction time, to
the versions committed here — not merely "some version is tracked."
