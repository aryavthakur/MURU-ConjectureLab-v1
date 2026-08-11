# PROPOSED_DEVIATION_FROM_MASTER_PLAN.md

Deviations proposed during Phase 1. Each states the original criterion, why the
data make it inappropriate, the replacement, and the consequences. Per the
session brief, none of these is adopted silently, and the recommendation on
whether to accept them is deferred to `PHASE1_DECISION.md`.

Severity is the master plan's bug policy: BLOCKER / IMPORTANT / MINOR.

---

## D1 — The mu decomposition identity (IMPORTANT)

**Original criterion.** Master plan section 7.1: `mu_i(E) = SY_i(E) * 1 +
(1 - SY_i(E)) * phi_i(E)`, with the session brief adding: "For mu verify
algebraically and numerically the decomposition ... within floating-point
tolerance where the definitions apply. A failure of this identity is a BLOCKER."

**Why the data make it inappropriate.** The identity is not an algebraic
consequence of the three definitions. Writing `p` for the precursor peak index:

```
mu = (sum_k I_k mz_k) / (sum_k I_k) / mz_declared
   = SY * (mz_observed_precursor / mz_declared_precursor) + (1 - SY) * phi
```

The plan's form additionally requires `mz_observed == mz_declared`. In this
corpus it does not: RMassBank recalibrates fragment and precursor masses
(`MS$DATA_PROCESSING: RECALIBRATE loess on assigned fragments and MS1`), so the
peak-list precursor and `MS$FOCUSED_ION: PRECURSOR_M/Z` differ at the ppm level.
Measured across all 66,514 evaluable rows:

| Form | max residual | rows above 1e-12 |
|---|---|---|
| Exact (with the mass-ratio factor) | 4.441e-16 | 0 |
| Plan form | 5.934e-06 | 10,588 |

Max `|1 - mz_observed/mz_declared|` = 9.087e-06, about 9 ppm, which fully
accounts for the gap.

**Replacement criterion.** The BLOCKER condition is evaluated against the exact
identity, which must hold to floating point. The plan's form is retained as a
reported diagnostic with its residual measured rather than assumed. `mu` is
computed directly from its definition (first moment of the normalized mass
distribution) and is never reconstructed from the decomposition, so no numerical
error propagates either way.

**Consequences.** None scientifically. A 6e-6 discrepancy is nine orders of
magnitude below mu's within-compound range of ~0.44. The change is one of
statement, not of behaviour: it prevents a future maintainer from "fixing" the
apparent failure by snapping peak masses onto the declared precursor m/z, which
would corrupt real measured data to satisfy a mis-stated identity.
`tests/test_corpus_assertions.py` pins both magnitudes so that either drift is
caught.

**Recommendation: ACCEPT.**

---

## D2 — E_com mass-invariance figure (MINOR)

**Original criterion.** Master plan section 6.2: "Over the sample's mass range
(151-526 m/z) I computed E_com spanning 0.71-0.80 eV at NCE 15 and 4.25-4.79 eV
at NCE 90, a spread under 13%." Section 6.2 uses this to argue NCE is a
defensible cross-molecule energy axis.

**Why the data make it inappropriate.** The 13% figure was computed on a
373-record sample spanning 151-526 m/z. The full corpus spans a wider precursor
mass range, and E_com spread scales with it. The specific number does not
survive; see `CE_AUDIT.md` for the measured per-energy spreads.

**Replacement criterion.** State the measured spread at full corpus mass range
rather than the sampled figure. The qualitative claim it supports -- that the
CoM transform substantially cancels the mass dependence of E_lab, so NCE is a
usable cross-molecule axis for singly charged ions on one instrument -- is
unaffected.

**Consequences.** None for Phase 1, which uses NCE as the energy axis and treats
E_com as descriptive. Phase 2 must not quote "under 13%".

**Recommendation: ACCEPT.**

---

## D3 — "Zero technical replicates in the curated layer" (MINOR)

**Original criterion.** Master plan section 9.4: "**VERIFIED:** the curated
MassBank layer contains no technical replicates. Zero InChIKeys map to more than
one internal ID in my sample of 53 unique compounds."

**Why the data make it inappropriate.** At full corpus, 6 of 967 compound-by-mode
keys map to two internal IDs (listed in `DATA_CENSUS.md`). The claim was verified
on a sample and does not hold corpus-wide.

**Replacement criterion.** State the measured count. The operational conclusion
is unchanged: 6 duplicated compounds cannot support a variance-component
estimate, so the raw mzML branch remains the only viable route to repeatability.

**Consequences.** None. The plan's downstream reasoning survives its own
factual error.

**Recommendation: ACCEPT.**

---

## D4 — Environment: `venv` + pinned requirements instead of `uv` (MINOR)

**Original criterion.** Master plan section 25 and T1.1: "`uv` project, Python
3.12", with `uv.lock`.

**Why.** `uv` is not installed on this machine, and installing it is a global
tool change outside the Phase 1 mandate. The available interpreter is Python
3.13.12; RDKit 2026.03.5 and PyArrow 25 both ship 3.13 wheels.

**Replacement.** A `.venv` created with the system interpreter and a fully
pinned `requirements.lock.txt` (32 packages, exact versions) committed to the
repository. This satisfies every reproducibility property Phase 1 needs: exact
versions recorded, environment reconstructible, no floating dependencies.

**Consequences.** A future Phase 2 that wants `uv` can adopt it without
rework. Python 3.13 rather than 3.12 is recorded in the report.

**Recommendation: ACCEPT.**

---

## D5 — Raw branch restricted to positive mode, and one file does not exist (IMPORTANT)

**Original criterion.** Master plan W1.5: "Download only the mzML files for
mixes 499, 503 and 505 from MSV000091754. Extract MS2 for the ~95 compounds
present in all three."

**Why the data make it inappropriate.** Two distinct issues.

1. *Positive mode only.* The session brief requires the minimum subset
   sufficient for the analysis. Positive mode is the primary experiment
   (section 10.3) and K3 needs one endpoint to clear one gate. Both modes would
   roughly double the download for a negative-mode repeatability number Phase 1
   does not gate on.

2. *A missing file.* `20200303_ENTACT_RP_mix505_pos_CE90.mzML` **does not exist
   in MSV000091754**. All 35 other mix-by-mode-by-energy combinations for mixes
   499/503/505 are present; this one is absent from the repository index. It is
   not a download failure.

**Replacement criterion.** Acquire the 17 available positive-mode files. At NCE
90 the replicate structure is a duplicate (mixes 499 and 503) rather than a
triplicate; the variance estimate at that energy carries correspondingly fewer
degrees of freedom and is reported separately.

**Consequences.** Repeatability at NCE 90 rests on two mixes rather than three.
Since NCE 90 is the energy at which survival yield is entirely dead (85.3% of
records at exactly zero) and mu is flattest, this is the least costly place to
lose a replicate. Negative-mode repeatability is **UNKNOWN** and is declared as
such.

**Recommendation: ACCEPT**, with negative-mode repeatability recorded as an open
item for Phase 2 rather than an assumed equivalence.

---

## D6 — "Replicate" terminology (IMPORTANT)

**Original criterion.** Master plan section 9.4 calls mixes 499/503/505
"raw-data replicates" and says "Roughly 95 compounds were therefore injected
three times", yielding "a proper repeatability estimate".

**Why the data make it inappropriate.** Verified from Elapavalore et al. 2023
(Table 1 and text): mix 499 contains 95 substances, mix 503 contains 185, mix
505 contains 365. Mixes 503 and 505 each *include the compound set of mix 499*,
but they are **three different mixture preparations at three different matrix
complexities**, run as separate injections. They are not repeated injections of
one vial.

The variance they yield therefore contains preparation, injection, instrument
**and matrix-complexity** variation. Calling it "technical repeatability" would
overstate what was measured. Measured overlap is **92** compounds in all three
(not ~95), of which **40** appear in MassBank positive mode.

**Replacement criterion.** The quantity is named **inter-mixture repeatability**
throughout and is explicitly described as an **upper bound** on technical
repeatability.

**Consequences.** For the K3 gate the direction is conservative and therefore
safe: K3 asks whether within-compound signal exceeds replicate SD by >= 3x, so
an inflated noise estimate makes K3 *harder* to pass. A K3 pass under this
estimate is a stronger result than a K3 pass under true technical noise. If K3
fails narrowly, the inflation becomes material and the estimate must be
decomposed before concluding.

**Recommendation: ACCEPT**, with the upper-bound framing carried into every
downstream use, including Phase 3's synthetic noise model.
