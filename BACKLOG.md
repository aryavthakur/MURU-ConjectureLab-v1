# BACKLOG.md

Issues recorded under the master plan's bug policy (section 29.5). BLOCKERs are
fixed before a phase closes and therefore do not appear here. IMPORTANT items
are documented with reproduction and scientific impact. MINOR items are recorded
and carried.

Phase 1 items are I1–I3 and M1–M7. Phase 2 items are I4–I6 and M8–M10.

## BLOCKERs — all resolved, none open

| # | Issue | Resolution |
|---|---|---|
| B1 | `mu = SY + (1-SY)*phi` fails on 10,588 rows at up to 5.9e-6 | Not an implementation defect. The identity as stated in the master plan is false in general; the exact form carries a `mz_observed/mz_declared` factor and holds to 4.4e-16. mu is computed from its definition, never reconstructed. See deviation D1. Both magnitudes are pinned by tests. |

No other BLOCKER-class condition was observed: zero parse failures, zero hash
mismatches, zero energy misassignments, zero grouping collisions, zero silent
missing-value coercions across 5,582 records.

---

## IMPORTANT — open

### I1. Four mix-505 mzML files not acquired (MassIVE rate limiting)

**Reproduction.** `GET https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.MSV000091754/peak/20200303_ENTACT_RP_mzML/mix505/20200303_ENTACT_RP_mix505_pos_CE30.mzML`
returns HTTP 429 persistently. Two acquisition strategies were attempted: a
Python client with exponential backoff (30/60/90/120/150 s, five retries) and a
shell client with eight attempts at 300 s intervals. Mix 499 (6/6), mix 503
(6/6) and mix 505 CE 15 were acquired; mix 505 CE 30, 45, 60 and 75 were not.
13 of a possible 17 files, 1.18 GB.

**Scientific impact.** Repeatability rests on a triplicate at NCE 15 and a
duplicate (mixes 499, 503) at NCE 30-90. The pooled inter-mixture SD for mu is
0.0295. At NCE 15, where both structures are available, the duplicate estimate
was 0.0245 and the triplicate 0.0281 — a 15% increase, in the conservative
direction. Extrapolating that ratio, a full triplicate would raise the pooled SD
to roughly 0.034 and lower mu's K3 ratio from 15.2x to about 13x, which does not
approach the 3x trigger. **The K3 verdict is insensitive to this gap.**

**Two-attempt rule applied.** External host throttling, not a defect in this
code. Documented and carried rather than expanded into a new phase.

**Action for Phase 2.** Re-attempt acquisition at a different time of day, or
request the files via MassIVE's FTP/aspera path. Refresh `REPEATABILITY.md`
if obtained.

### I2. Negative-mode repeatability is UNKNOWN

**Cause.** Deliberate scope decision (deviation D5): positive mode is the
primary experiment and K3 needs one endpoint to clear one gate; acquiring both
modes would have roughly doubled a download that was already rate-limited.

**Scientific impact.** Any negative-mode claim that requires a noise floor —
including H-MAIN's "residual within measurement repeatability" clause applied to
the negative-mode replication — is not currently supportable. Positive-mode
noise must not be assumed to transfer: ESI polarity changes precursor ion,
charge localization and fragmentation chemistry.

**Action for Phase 2.** Acquire `20200303_ENTACT_RP_mix{499,503,505}_neg_CE*.mzML`
(all 18 exist) before making any negative-mode noise-referenced claim.

### I3. mu's residual mass association

**Observation.** Spearman rho(mu, precursor m/z) runs -0.10 at NCE 15 to -0.68
at NCE 90, after mu has already been normalized by precursor m/z.

**Scientific impact.** This is risk R4 and it fires before any model exists. A
fitted "structure law" on mu could be substantially a mass law. Kill criterion
K5 is live.

**Action for Phase 2.** Baseline B2 (per-energy mean + linear precursor m/z) is
the primary competitor, not a formality. F8 descriptor ablation must report what
happens when precursor mass is removed.

### I4. No runtime-budget check precedes expensive experiments (Phase 2)

**Observation.** `scripts/t2_05_baselines.py` was launched without any estimate
of its cost. It ran for **2 h 08 m** on an 8-core machine without completing and
was terminated, at times
consuming 600–670% CPU while the system carried a load average of 11.5 and had
2.34 GB of 3.07 GB swap in use and roughly 68 MB of free pages. A 3-second
process sample taken mid-run showed **23 stack frames in productive work**
(`Splitter.find_node_split`, `HistogramBuilder.compute_histograms_brute`)
against **249 frames in wait primitives** — that is, most of the 18 threads were
blocked or spinning in OpenMP barriers rather than computing. Measured
throughput was roughly **4x slower** than a single-fit calibration taken on the
same machine before launch predicted.

A second, separate defect compounded it: `nested_cv` returns test-fold slices
that still carry all ~719 Tier B feature columns, and the driver accumulates
about 30 such frames in a list before trimming columns at write time. Process
RSS grew from ~290 MB to ~462 MB during the run, with a larger transient
expected at the final `pd.concat`. On a memory-pressured machine this is
avoidable waste: the driver only ever needs the identifier, response and
prediction columns.

**Scientific impact.** **None.** No result, threshold, model definition or
pre-registered choice was altered because of runtime. Deviation D12 reduced the
Tier B fingerprint floor and the hyperparameter grid for cost reasons, but that
was decided and recorded **before** any performance was observed, and both
reductions weaken the structure-aware model, making K4A and K4B harder to pass.

**Action for Phase 3 and later — binding.** Before launching any expensive
experiment, produce and record a **runtime budget** covering at minimum:

1. total number of model fits implied by the grid, folds and splits, **stated as
   an explicit formula** rather than a bare number, so that loop nesting is
   visible and checkable. The first budget produced under this rule got this
   wrong by a factor of five by adding the inner and outer loops
   (`grid × inner + outer`) instead of nesting them
   (`outer × grid × inner + outer`); see `DEVIATIONS.md` D14,
2. estimated wall time, derived from a measured single-fit calibration on the
   target machine and multiplied by an explicit contention factor,
3. peak memory estimate, including any accumulation across loop iterations,
4. thread count per fit and expected parallel efficiency given available cores,
5. whether the job will oversubscribe the machine, and the thread cap that
   prevents it.

If the estimate exceeds the session budget, **reduce scope before launch and
record the reduction as a deviation** — never after seeing results. The estimate
belongs in the pre-registration when it affects a pre-registered quantity.

Two implementation fixes are also carried: cap worker threads explicitly rather
than letting OpenMP default to the core count under external load, and project
prediction frames down to their identifier and response columns before
accumulating them.

### I5. Structure-beyond-mass does not replicate in negative mode

**Observation.** Negative mode (349 compounds, S2 scaffold-disjoint) reproduces
K4A — Tier A beats the structure-blind B1 by 0.03204, scaffold interval
[-0.04052, -0.01964] — but **fails K4B**: Tier A beats MASS FLEX by only
0.00250, a **1.93%** relative reduction against the pre-registered 5% minimum,
with a scaffold interval of [-0.01572, +0.00038] that spans zero.

Positive mode by contrast gives 20.02% (flexible benchmark) and 10.53%
(Tier A), both with intervals excluding zero.

**Scientific impact.** The Phase 2 conclusion — that structure predicts beyond
a strong energy-plus-mass model — is currently a **positive-mode** result. It is
not established for negative mode. Three readings are consistent with the data
and Phase 2 cannot distinguish them: genuinely different negative-mode
fragmentation chemistry; lower statistical power (349 vs 439 compounds); or a
mass effect that dominates more strongly under deprotonation.

**Action for Phase 3+.** Any claim must carry the positive-mode restriction
until this is resolved. Resolving it needs at minimum the negative-mode
repeatability estimate that issue I2 already requires.

### I6. NC7 fired: retention time predicts trajectory shape

**Observation.** Retention time alone improves on B1 by **+0.01006**, above its
permutation null (95th percentile +0.00021). **0 of 200** permutation replicates
reached the observed value, giving a finite-sample corrected empirical
p = **0.00498** = (b+1)/(B+1) — the smallest value attainable with 200
resamples. Phase 1 anticipated this (`CONFOUNDERS.md` finding 4, |rho| up to
0.36).

**Explanation, and its limit.** Adding RT to Tier A gains only **+0.00097**,
2.3% of the Tier A effect. RT therefore carries predictive signal by itself but
adds little incremental predictive information beyond Tier A descriptors, which
is consistent with it acting **primarily as a structure-associated surrogate in
this dataset** — it tracks lipophilicity, itself a structural property. The
control does not block.

This is an observational association, not an identification result.
**Independent confounding cannot be completely excluded**: a confounder whose
effect is largely collinear with the descriptors would produce the same small
increment. Nor does the explanation separate real lipophilicity-driven chemistry
from co-elution and matrix effects; those mechanisms are confounded in this
dataset and no Phase 2 evidence distinguishes them.

**Scientific impact.** No mechanistic reading of the structural effect may lean
on RT-correlated descriptors.

**Action for Phase 3+.** Carry the restriction. Separating the mechanisms would
need either chromatography-resolved replicates or an orthogonal
lipophilicity measurement, neither of which this corpus provides.

---

## MINOR — recorded, no action

| # | Issue | Note |
|---|---|---|
| M1 | Master plan's "zero duplicate InChIKeys in the curated layer" is false at full corpus | 6 of 967 compound-by-mode keys map to two internal IDs. Too few for repeatability; conclusion unaffected. Deviation D3. |
| M2 | Master plan's "E_com spread under 13%" does not survive the full corpus mass range | The qualitative claim it supports is unaffected. Deviation D2. |
| M3 | `file(1)` reports Li_2021 PDF as 23 pages, `pypdf` counts 19 | Object-count vs page-tree difference. Document parses and yields text normally. No corruption. |
| M4 | The 0.1% relative-intensity cutoff cell is inert on the curated branch | RMassBank's formula filter already removed everything below it. The grid axis is only meaningful on the raw branch. Recorded so it is not mistaken for a null result. |
| M5 | Publication says "nominal collision energy (NCE)"; "normalized collision" appears zero times | The Thermo conversion assumes *normalized*. Immaterial to Phase 1, which uses NCE as the axis. Matters for cross-instrument work. See `CE_AUDIT.md`. |
| M6 | Environment uses `venv` + pinned requirements and Python 3.13, not `uv` + 3.12 | `uv` not installed; installing it is outside the Phase 1 mandate. Deviation D4. |
| M7 | Master plan cites the Thermo NCE formula to sources absent from the reference pack | Recorded as SUPPORTED, not VERIFIED. Every derived E_lab/E_com is labelled conditional. |

---

## Explicitly not done (Phase 2+ scope)

Splits of any kind, descriptors beyond identity checking, any model, any
symbolic search, negative-mode analysis beyond census, neutral losses,
ClassyFire classes, the falsification ladder beyond Phase-1-relevant checks.
None of these was built, and no dependency supporting them was installed.

| M8 | Phase 2 baseline ladder needed a full execution redesign after a 2h08m non-completing run | Thread oversubscription, no checkpoints, no visible progress, unbounded prediction-frame accumulation. Fixed; deviation D14 and issue I4. |
| M9 | The pre-registered negative-control rule conflated two control families and inverted the p-value | A perfectly passing control was reported as a BLOCKER while the one genuine firing control was concealed. Corrected before reporting; deviation D16, pinned by `tests/test_controls_adjudication.py`. |
| M10 | `PREREGISTRATION.md` §22's GO row omitted the negative-mode replication that §18 pre-registered | Folded into the RESTRICT condition, which can only make the verdict more conservative. Deviation D15. |
