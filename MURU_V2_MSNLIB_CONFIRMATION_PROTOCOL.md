# MURU-WUR-v2 MSnLib External Confirmation Protocol

**Identifier:** `muru-v2-msnlib-confirmation-1.0`
**Status:** pre-registered, **NOT executed**. See §11 for why, and what a future
session needs to do to execute it.

## 0. Provenance disclosure (read this first)

This document was written **after** the MSnLib anchor-calibration results
were seen (`MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` Part IV, reproduced in
`MURU_V2_CONFIRMATION_PREFLIGHT.md` §0.5). Those anchor results are
**calibration/pilot data, not an independent confirmatory result**: 402
census anchors, 328 with both fixed rungs, 1,935 anchor scans decoded. The
frozen absolute-agreement gate was applied literally and **failed** at all
three tested adapters (A0 NCE20 median |Δμ| 0.0501 vs required ≤0.05; A1
pooled RMSD 0.0811 vs required ≤0.08; A2 NCE20 median 0.0506 vs required
≤0.05) — by margins the source document itself calls "far smaller than
anchor sampling noise." **No MSnLib validation fragmentation outcome has
been seen.** Model development is closed: this protocol tests comparative
predictive transfer of the already-frozen candidate and comparator, not
absolute observable equivalence between MSnLib and the WUR/LCSB development
sources, and it does not re-litigate or reinterpret the failed gate.

## 1. What question this protocol asks

*"With the model and comparator now frozen, and using one fixed
zero-parameter deployment mapping chosen independently of MSnLib validation
outcomes, does the structural augmentation in MURU-v2 outperform the Tier A
comparator on previously untouched MSnLib compounds?"*

This is a narrower, different claim than the compatibility-gate question the
anchor study already answered. It is disclosed as such, not presented as a
do-over of that gate.

## 2. Frozen models (unchanged by this protocol)

| Role | Model | File | Canonical-JSON sha256 |
|---|---|---|---|
| Candidate | `V2_TA_MORGAN_JOINT` | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` |
| Primary comparator | `V2_REF_TA_RIDGE` | `artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` |

Both trained on the same 1,325 exposed development compounds
(`training_keys_sha256` = `81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd`).
Both hashes independently reproduced from a from-scratch fresh-worktree
rebuild — see `MURU_V2_REPRODUCIBILITY_MANIFEST.md`. **Neither model is
refit on MSnLib structures, anchors, or outcomes at any point in this
protocol.** Representations (Tier A descriptors, Morgan fingerprints) are
computed from validation-compound *structure* only, which is legitimate
model input, not retraining.

Secondary descriptive comparators (not a substitute for the primary
comparison): `V2_REF_B1_MASS`, `V2_REF_B0_NULL`, and historical frozen v1
(`V1B_RIDGE_TIERA_FROZEN`), all already in `artifacts/wur_v2/candidate/`.

## 3. Fixed deployment energy map: A0 only

```
E_LCSB = (NCE - a_WUR) / b_WUR
```

using the frozen Stage 1 WUR/LCSB bridge constants already recorded in
`artifacts/wur_v2/data/population_manifest.json`:
`a = -5.95552603907965`, `b = 0.8618030610784555`. **Zero MSnLib-fitted
parameters.** A1 (`E = k*NCE`) and A2 (`E = a + b*NCE`) are explicitly
**not** used, even though A2's absolute numbers were marginally closer to
passing the old gate — that is not the licensing rationale. The rationale
is that A0 was prespecified before any MSnLib outcome access and contains
no MSnLib-fitted parameter, which is what an independent comparative test
requires. No offset, slope, or calibration may be fit to validation data at
any point, before or after seeing the result.

Both candidate and comparator are scored under the identical A0 map, so a
global source mismatch (which the anchor study shows is real and roughly
0.078 RMSD — see §0 and `MURU_V2_CONFIRMATION_PREFLIGHT.md` §0.5) is shared
across both models rather than model-specific. This does not remove the
mismatch; absolute errors are reported alongside the comparative ratio, not
instead of it.

## 4. No new compatibility gate

The old absolute-agreement gate is not rerun and not reinterpreted as
having passed. Standing, disclosed measurement limitation: *on exposed
calibration anchors, MSnLib shows strong rank agreement with the
development coordinate (model-free Spearman 0.94 at NCE20/LCSB30, 0.96 at
NCE60/LCSB75) but narrowly misses the original absolute-agreement gate at
low energy.* This protocol asks only whether the candidate-vs-comparator
**advantage** survives under the fixed A0 deployment regime, not whether
MSnLib and WUR/LCSB are interchangeable in an absolute sense.

## 5. Endpoint (unchanged from the frozen MSnLib protocol)

Per spectrum: `mu = sum(I * m) / sum(I) / m_prec` — all centroid peaks in
the eligible MS2 scan, precursor included, no intensity cutoff, `m_prec` =
theoretical [M+H]+. Per (compound, rung): median over all eligible matched
scans/wells under the frozen rules. Two fixed rungs only: NCE 20 and NCE
60. The Assisted/adaptive scan is **never** used. No interpolation between
rungs.

## 6. Outcome-blind validation population

Reuses the frozen census design-frame rules (`MURU_V2_MSNLIB_OUTCOME_BLIND_CENSUS.md`,
`artifacts/wur_v2/external_census/msnlib_census.json`) unless a new
implementation inconsistency is discovered: identity-new filtering,
scaffold-new filtering, charge-neutral scaffold-new filtering, [M+H]+ mass
range (115-2,000 m/z), conflict-free well rules. Design frame at last
census: **39,238 compounds in 29,562 scaffold groups** (detected frame,
after additional structure-only rules: 32,154 / 25,671).

**Sampling rule (frozen, not re-derivable from outcomes):** sample 2,000
v2 scaffold groups without replacement from the sorted eligible group list
using `numpy.random.default_rng(seed=20261010)`. This exact seed, this exact
sampling call, against this exact sorted list. No re-seeding, no
similarity/confidence/molecular-class/anchor-behavior-based selection.

After sampling, apply only header/acquisition eligibility rules (never
outcome-derived ones): positive mode; correct production well/run; selected-
ion m/z within frozen tolerance; fixed NCE20/NCE60 rung definition; scan-
window requirements; ≥1 eligible scan at each rung; conflict-free well;
representation computability. Peak intensities, μ, precursor survival,
library detection status, QC-pass membership, fragment count, and any model
prediction/residual are **never** eligibility criteria.

**Stop condition:** if fewer than 500 independent scaffold groups survive
every purely eligibility/header filter, stop before outcome decoding and
report the validation population as inadequate. Otherwise proceed to
header-only preflight, then parser preflight, then the one-look decode.

## 7. Header-only preflight and parser preflight (before the one look)

Binary peak arrays are never decoded during population construction — only
scan id, selected-ion m/z, MS level, collision energy, scan window, and
other acquisition metadata needed by the frozen rules above. TIC, base peak
intensity, intensity arrays, peak counts, and any other outcome-derived
summary are out of scope until the one look.

Before touching any validation array, the MS-Numpress PIC decoder already
built and fixed for the anchor study (`MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`
Part III addendum) must be re-exercised end-to-end against the exposed
anchor files (round-trip test, cross-implementation check against pymzML,
decoded-length check against `defaultArrayLength`, 32/64-bit format check,
zlib+Numpress combination check, fixed-rung extraction, selected-ion
matching, precursor inclusion, deterministic aggregation) — using anchor
files only, never validation peaks, for this debugging. If the header-only
validation census discovers a compression/encoding type absent from the
anchors, a synthetic/reference-vector test for it is added before outcome
access.

## 8. Primary estimand and statistics (frozen before outcome access)

- **Primary metric P1:** pooled two-rung RMSE over all eligible compound-
  rung cells, both models, under A0.
- **P1_ratio = P1_candidate / P1_TierA.**
- Also reported: P1 difference, MRMSE, median compound RMSE, Q90, Q95,
  CVaR95, AF (compound two-rung RMSE > 0.20), AF_max (any rung absolute
  error > 0.30), each rung separately, coverage/exclusions.
- **Resampling unit: whole validation scaffold groups**, not compounds
  (several compounds share a group). Bootstrap B = 10,000, seed = 20261011.
  Every replicate recomputes P1_candidate, P1_TierA, P1 difference, P1
  ratio, MRMSE difference, AF difference from scratch — never a bootstrap
  of a mean individual RMSE relabeled as P1. Group count and size
  distribution (including the largest group) are reported.

## 9. Pre-registered interpretation rule (frozen before outcome access)

**Primary confirmation** requires both: (1) point `P1_candidate <
P1_TierA`; (2) the whole-scaffold-cluster bootstrap 95% upper bound of
`P1_candidate / P1_TierA` is `< 1.00`.

- Primary confirmation **and** `ratio ≤ 0.95` → *practically meaningful
  external improvement.*
- Primary confirmation **and** `0.95 < ratio < 1.00` → *statistically
  supported but modest external improvement.*
- `ratio < 1.00` point estimate but the 95% upper bound includes 1.00 →
  *directionally favorable but externally inconclusive* (not "validated").
- `ratio ≥ 1.00`, or the candidate materially worsens tail risk → *did not
  externally transfer.* No repair of the model on this population.

**Tail-risk secondary** (only interpreted strongly if the primary
point-prediction result is supported): `AF_candidate - AF_TierA` with
whole-scaffold bootstrap interval; prior noninferiority tolerance upper 95%
limit ≤ +0.03. Actual AF values always reported, no selective filtering
after seeing failures.

**Per-rung analysis:** NCE20 and NCE60 reported separately (candidate RMSE,
comparator RMSE, ratio, mean signed residual, median absolute residual). Both
rungs reaching independent significance is not required. If the pooled
result is driven entirely by one rung while the other meaningfully reverses,
that is discussed prominently, not hidden.

**Structural-novelty analysis** (secondary, descriptive, never used to
exclude compounds from the primary endpoint): partition validation
compounds into frozen similarity bands by maximum Morgan similarity to the
development training population, computed from structure only, before any
outcome is seen. Preferred fixed bands: `<0.30`, `0.30-0.50`, `0.50-0.70`,
`≥0.70`, adjusted to predeclared quantile bins only if these produce
inadequate counts — decided before outcomes, not after.

## 10. Claim scope

If positive: *"On an independent, scaffold-separated MSnLib
commercial-screening population measured on a Thermo Orbitrap ID-X at fixed
HCD NCE 20 and 60, the frozen MURU-WUR-v2 structural scale model
outperformed the frozen Tier A scale comparator under a fixed zero-parameter
deployment energy map."* Never: universal MS/MS prediction, all instruments,
all adducts, negative mode, dense energy trajectories, QTOF transfer,
natural products generally, or perfect cross-instrument calibration.

Source citation for the record: Brungs, Schmid, Heuckeroth et al., *Nat
Methods* 22, 2028-2031 (2025), doi:10.1038/s41592-025-02813-0; Zenodo
concept DOI 10.5281/zenodo.10966280 (mzML, all 9 libraries, cc-by-4.0);
MassIVE MSV000094528 (Orbitrap ID-X, 7 of 9 libraries).

## 11. Execution status: NOT EXECUTED — environment blocker

This protocol is committed as a complete, self-contained pre-registration.
**It has not been executed.** `MURU_V2_CONFIRMATION_PREFLIGHT.md` §0.8
records why: this execution sandbox has no network route to Zenodo,
GNPS-external, or (by strong inference) MassIVE, and no local cache of raw
MSnLib validation mzML exists in this checkout. Per the governing mandate's
own rule, this stops the study before validation-outcome access — which
here means before even the outcome-blind population is sampled, since
sampling requires either a fresh fetch of the design-frame identity tables
or reuse of an already-fetched local copy whose provenance this session did
not want to lean on without being able to verify it end to end (see note
below).

**What a future session needs to actually run this protocol:**

1. Network egress to Zenodo (`zenodo.org`) and/or MassIVE
   (`massive.ucsd.edu` / `gnps-external.ucsd.edu`), or a pre-fetched,
   hash-verified local copy of the MSnLib design-frame identity tables.
   (Note for whoever picks this up: at the time of this study, a sibling
   git worktree on the same development machine —
   `.claude/worktrees/recursive-executor-framework-07dd81/data/external/msnlib_metadata/`
   — held per-library compound TSVs whose filenames match
   `artifacts/wur_v2/external_census/msnlib_census.json`'s
   `inputs.design_tables[*].sha256` records. This session did not copy or
   use them: reusing files from another session's untracked scratch
   directory, without being able to independently re-fetch and re-verify
   them against their origin, was judged not sound enough to be load-bearing
   for a frozen population. A future session should re-fetch and re-hash
   against the recorded provenance, not silently trust a copy found on
   disk.)
2. Execute §6 (sampling with the frozen seed), producing the compound
   count, scaffold-group count, key hash, scaffold-group hash, and
   attrition table this document does not yet contain.
3. Execute §7 (header-only preflight, parser preflight against anchors).
4. Commit `MURU_V2_MSNLIB_CONFIRMATION_FREEZE.md` with every field listed
   in the mandate (protocol identifier, SHAs, hashes, population counts,
   manifest hash) filled in from steps 2-3 — **on a clean tree, before**
   any validation peak array is decoded.
5. Construct the one-look guard (`src/muru/wur_v2/external_guard.py`,
   `AccessGuard(kind="VALIDATION", ...)` — already implemented and reusable
   as-is, refuses a second construction) and execute the single look.
6. Everything in §8-§10 above governs that look unchanged. No threshold,
   population rule, or success criterion in this document may be edited
   after step 5 begins.
