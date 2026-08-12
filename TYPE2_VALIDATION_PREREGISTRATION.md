# TYPE2_VALIDATION_PREREGISTRATION.md

**Prospective objective-alignment validation of the Type 2 claim.**

This file is frozen and committed **before any fresh validation world is
generated**. Everything below — generators, parameter ranges, seeds, blinding,
the selection rule, family equivalence, the acceptance rule, null calibration,
the corroboration standard, the gates, the repair policy and the exact verdict
rule — is fixed in advance. After the freezing commit, any material
methodological change is recorded in `DEVIATIONS_OBJECTIVE_VALIDATION.md`.

Companion documents, all frozen with it: `OBJECTIVE_ALIGNMENT_AMENDMENT.md`,
`TYPE2_SELECTION_RULE.md`, `TYPE2_FAMILY_EQUIVALENCE.md`,
`TYPE2_ENGINE_CORROBORATION.md`, `RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md`.

---

## 0. What this study is, and what it is not

It is a **separate prospective validation study** of whether the MURU machinery
is trustworthy for the master plan's own molecule-conditional
equation-**family** objective.

It is **not** a Phase 3 re-score, not "Phase 3b", not a sixth phase, not Phase 4,
not a real-data search, not an anomaly-detection study, and not an attempt to
rescue MURU from a negative result. The five-phase architecture is intact. The
official Phase 3 verdict is unchanged:

> **STOP BEFORE PHASE 4**

The rationale is in `OBJECTIVE_ALIGNMENT_AMENDMENT.md` and is not repeated here.

## 1. Verified starting state

| Check | Evidence | Result |
|---|---|---|
| Phase 3 completion commit | `git rev-parse` | `211b500999a6ea0a098cfb87f1a9f4958060f81e` ✓ |
| Phase 3 verdict | `PHASE3_DECISION.md`, `artifacts/p3_decision.json` | `STOP BEFORE PHASE 4` |
| Phase 3 pre-registration sha256 | `PHASE3_PREREGISTRATION.md` | `064ce1fb9939b10d3b22be1f74aa3da28f487ec3917449db0794cf6431af5a63` |
| Highest real-data rung | `p2_decision.json`, `PHASE3_DECISION.md` | **L3**, unchanged by this study |
| Sealed confirmation set | sha256 recomputed before the study | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` ✓ intact |
| Study branch | `objective-validation-type2`, based on `211b500` | |

Phase 1's endpoint decision is not reopened: `mu` remains the primary response.
Phase 2's restrictions remain in force in full — positive mode primary,
negative-mode K4B did not replicate, raw-preprocessing robustness covers 39
compounds (7.1%), mass coupling remains a sensitivity issue, retention time
remains observationally associated, no cross-instrument transfer.

## 2. Scientific question

> Can MURU reliably identify a compact, interpretable, molecule-conditional
> empirical equation **family** — with correct structural support, correct
> scaling behaviour, good held-out predictive performance, a low false-positive
> rate, and survival of the existing falsification system — **even when the
> exact algebraic generating form is not identifiable**?

A negative answer is an acceptable and reportable outcome.

## 3. Claim taxonomy, frozen

| Class | Claim | Status here |
|---|---|---|
| Type 1 | a predictive trajectory equation | below the target |
| **Type 2** | a compact interpretable empirical relationship: stable support, stable scaling, generalization, null-calibrated, falsification-surviving | **the maximum target** |
| Type 3 | the algebraic form may correspond to fragmentation physics | **not authorized**; measured and reported as a diagnostic only |
| Type 4 | an established physical law | far outside v1 |

A Type 2 result is never converted into Type 3 language. The forbidden claim list
in `OBJECTIVE_ALIGNMENT_AMENDMENT.md` §12 is binding.

## 4. Architecture — unchanged from Phase 3

The search targets are the master plan's, and the existing T1/T2 abstraction is
retained because development found no methodological defect in it:

* **T1** — the alternating `(Phi, g)` collapse fit: an isotonic shared `Phi`
  against per-compound scales. Fitted for every world; its adequacy test decides
  H-MAIN.
* **T2** — the estimated per-compound scale `ĝ_i`, inverse-variance weighted,
  searched as a function of the 12 dimensionless Tier A descriptors. **Every
  gate, threshold and false-positive count is computed on it.**
* **T3** — not run, per `DEVIATIONS_P3.md` D2.

**The scalar scale `g_i` is retained.** Development found no evidence in the
Phase 3 artifacts that a multi-parameter `theta_i` is required for the H-MAIN
test: `G1`, `G3` and `G4` never rejected H-MAIN, and `G2` — the world built with
a varying shape — rejected it in 8 of 8. The scalar collapse is adequate for the
question, and expanding it would make the project more elaborate without making
the claim better supported. A larger parameterization is future work.

Grammar, complexity metric, protected numerics, dimensional discipline, split
construction and the falsification harness F1–F12 are **unchanged and frozen**
exactly as `PHASE3_PREREGISTRATION.md` §8–§9, §14 and §16 define them.

## 5. Fresh worlds

Generator version `ov-gen-1.0.0`, truth version `ov-truth-1.0.0`. Planted laws
live in `src/muru/objval/truth2.py`, which must not appear in the import closure
of the discovery side; `tests/test_ov_import_graph.py` enforces it.

**Every constant is drawn per replicate** from the ranges below rather than
reproduced from Phase 3, so the study tests generalization across the family
rather than across noise draws of one instance.

| Quantity | Phase 3 | Here |
|---|---|---|
| `Phi` asymptote `mu_inf` | fixed 0.2414 | drawn from [0.18, 0.30] |
| `Phi` exponent `p` | fixed 1.4874 | drawn from [1.20, 1.80] |
| overall scale of `g` | fixed 1.7017 | drawn from [1.40, 2.00] |
| non-mass carrier | always `heteroatom_fraction` | cycles `heteroatom_fraction`, `rotatable_bonds`, `n_O` |
| non-mass coefficient | fixed 0.35 | drawn from [0.25, 0.55] |
| G3 mass exponent | fixed 0.6 | drawn from [0.45, 0.75] |
| G4 / G4M offset SD | fixed 0.22 / 0.18 | drawn from [0.18, 0.28] / [0.14, 0.24] |

Noise regimes are unchanged — `low` 0.010, `moderate` **0.0295**, `adverse`
0.060 — because 0.0295 is the Phase 1 conservative inter-mixture variability
estimate, a measured quantity and not a tuning knob
(`MASTER_PLAN_CLARIFICATIONS.md` C4). Missing cells stay at the measured 0.97%.

### Positive controls

| Family | Planted law (dimensionless) | Purpose |
|---|---|---|
| **G1A** | `g = a0·v0 + a1·v1²`, i.i.d. covariates, no real chemistry | analytic sanity: prove the complete pipeline works and isolate it from any property of the real descriptor matrix |
| **G1B** | `g = a0·√m·(1 + a1·X)`, `X` the drawn non-mass carrier | **the actual MURU claim**: a shared trajectory family with molecule-specific scaling predicted by more than mass alone. Mass exponent exactly 0.5, the §18.3 target |
| **G1C** | `g = a0·√m·exp(a1·(X − X̄))` | **near-degenerate family challenge**: the generating form is *outside the frozen grammar* (`exp` is excluded, `DEVIATIONS_P3.md` D1), so several simpler forms are near-equivalent on the observed domain while the Type 2 signature is unchanged |

G1C's degeneracy is created by placing the truth outside the hypothesis space,
**not** by tuning constants to reproduce Phase 3's observed failure numerically.

### Refusal worlds

| Family | Construction | Correct behaviour |
|---|---|---|
| **G2** | scale and shape both descriptor-dependent, with a regime switch | refusal, or a restricted regime-specific conclusion; H-MAIN false |
| **G3** | mass only, drawn exponent | a mass law may be accepted and must be labelled one; any accepted non-mass structural claim is a failure |
| **G4** | pure null, offsets independent of every descriptor | no accepted conjecture; the false-positive basis |
| **G4M** | mass-conditional null | no accepted conjecture claiming structure beyond mass |
| **G5** | confounded; the true driver is latent and never supplied | the proxy expression must not survive as a structural claim |
| **GC** | measurement-coupling adversary: fixed fractional fragmentation plus an absolute low-mass cutoff at 30/50/80 Da | no accepted conjecture claiming non-mass structure |
| **GRT** | retention-time surrogate; a latent property drives both descriptors and RT | RT-associated expressions must not be promoted |

GC's cutoffs are stipulated at interpretable instrument settings and are never
tuned to reproduce an observed correlation. **GC does not identify the mechanism
of the real association and establishes no artifactual fraction.** GRT is a
bounded stress test and does not resolve the real NC7 finding causally.

### World counts

| Block | Worlds | Seeds | PySR runs |
|---|---|---|---|
| `NCAL` null calibration | 100 | 30 | 3,000 |
| `G4` | 100 | 30 | 3,000 |
| `G4M` | 30 | 30 | 900 |
| `G1A` | 6 (2 per regime) | 30 | 180 |
| `G1B` | 40 (low 10, **moderate 20**, adverse 10) | 30 | 1,200 |
| `G1C` | 10 (moderate) | 30 | 300 |
| `G2` | 8 | 30 | 240 |
| `G3` | 8 | 30 | 240 |
| `G5` | 8 | 30 | 240 |
| `GC` | 9 (3 per cutoff) | 30 | 270 |
| `GRT` | 4 | 30 | 120 |
| **Total** | **323** | **30** | **9,690** |

Plus the comparison arm: 88 worlds × 10 seeds = **880 gplearn runs**.

`G4` is 100 replicates because the master plan requires it. `NCAL` is 100 rather
than Phase 3's 40 because a 95th percentile from 40 worlds rests on its top two
or three (`BACKLOG.md` I8). `G1B` moderate carries 20 replicates because the
governing gate is stated on that regime and a rate of 0.80 estimated from 10
worlds resolves only to 0.1.

## 6. Seeds

**30 symbolic seeds per world** (master plan §13.4 minimum), in a band provably
disjoint from Phase 3's.

| | Phase 3 | This study |
|---|---|---|
| derivation | `900000 + sha256(world_id)[:3]·100 + k` | `1700000000 + (sha256(world_id)[:4] mod 4000000)·100 + k` |
| realized range | [11 258 400, 1 678 023 829] | [1 700 907 400, 2 099 175 629] |
| theoretical max | 1 678 621 529 | 2 100 000 029 (inside signed 32-bit) |

Generator seeds use the `ov-gen-1.0.0` namespace. `tests/test_ov_freshness.py`
asserts band separation, empty realized intersection with the Phase 3 manifest,
and that no Phase 3 world id can enter this study's plan. The seed manifest is
written and hashed **before** execution and seeds are never selected on outcomes.

## 7. Selection, equivalence and acceptance

The selection rule is `TYPE2_SELECTION_RULE.md` and family equivalence is
`TYPE2_FAMILY_EQUIVALENCE.md`; both are frozen with this file.

**A reported Type 2 family is ACCEPTED if and only if all of:**

1. the representative's validation R² **exceeds the null threshold at its own
   complexity**;
2. family selection frequency **≥ 20/30** seeds;
3. complexity **≤ 20**;
4. invalid fraction **≤ 0.5%**;
5. **non-empty effective support** — a family with no effective support makes no
   structural claim and is a refusal, not an acceptance;
6. the representative reaches **≥ 80% of the flexible all-descriptor ceiling's**
   held-out R² (master plan §16.2 L4 and §14.4), waived only when the ceiling
   itself is below R² 0.05 and the ratio is meaningless;
7. **H-MAIN is not rejected** — the Type 2 claim *is* `mu = Phi(E/g(z))`, so a
   collapse rejected out of sample against a freed per-compound shape
   contradicts the claim;
8. the **complete required falsification set** passes: F1, F2, F4, F5, F6, F7,
   F9, F10, with F3 and F11 recorded not-applicable and never counted as passes,
   F8 a labelling rung, F12 supporting only.

Conditions 6 and 7 are **new relative to Phase 3's acceptance rule**, are taken
from the master plan, and both make acceptance strictly harder — neither can
inflate a false-positive rate.

A family **claims structure beyond mass** only if its block-level effective
support contains a non-mass block, ablating the non-mass descriptors destroys the
result, and the mass block alone does not reproduce it. Unchanged from Phase 3.

## 8. Blind truth handling

1. Worlds are built by `ov_10_build_worlds.py`, which writes **two** manifests:
   `artifacts/ov_worlds.json` (identity, seeds, split counts, output hashes —
   **no planted law**) and `artifacts/ov_truth_manifest.json` (the quarantined
   planted laws and drawn parameters). Both are hashed.
2. The search receives `World2.search_inputs()` — the response frame and the
   covariate frame — and `World2.manifest()`, which carries no planted law.
3. Selection (`ov_30_select.py`) reads candidates only.
4. Adjudication (`ov_40_adjudicate.py`) reads world data and candidates only.
5. **`ov_45_recovery.py` is the first script that opens the truth manifest**, and
   it refuses to run unless every world in scope already has a frozen selection
   result and a frozen adjudication verdict on disk.

`tests/test_ov_blinding.py` asserts that no discovery-side module references the
truth manifest and that the truth module is outside the discovery import closure.

## 9. Null calibration

**Statistic, unchanged:** the maximum over the 30 seeds of the best validation R²
attainable at complexity ≤ c, for c = 1…20. It prices in search multiplicity, and
within a world it **upper-bounds whatever any selection rule can report** at
complexity c — so a threshold built from it is conservative under the Type 2 rule
as well as under Phase 3's. That is why the statistic did not need to change when
the selector did; what changed is the calibration size and the fact that it is
rebuilt from scratch on fresh worlds.

* **100 calibration worlds**, cycling the four master-plan §13.6 constructions.
* Threshold at each complexity = the **95th percentile** across calibration
  worlds, made non-decreasing in complexity.
* A **2,000-resample bootstrap interval on the quantile itself** is reported at
  every complexity, and the table is never read as more precise than it is.
* Calibration worlds are **disjoint from the 100 G4 worlds** that measure the
  false-positive rate.
* Per-construction 95th percentiles are reported separately so a single
  pathological construction is visible rather than buried.

## 10. False-positive gate

For each of the **100 fresh G4 replicates**: generate, run the frozen 30-seed
search, apply the frozen Type 2 selection rule, apply the frozen acceptance rule
including the complete falsification harness, and record whether a family would
incorrectly be accepted.

```
false-positive rate = (null worlds producing an accepted Type 2 family)
                    / (valid null replicates)
```

Numerator, denominator and a **Clopper–Pearson exact 95% interval** are reported.
`p = 0` language is never used for a finite simulation count. **The rate must be
≤ 5%.**

## 11. Positive-control gate

**Type 2 success**, per world, frozen:

* the reported family is ACCEPTED (§7), **and**
* **block-level support recovery**: the reported effective support blocks equal
  the planted ones, **and**
* **exponent recovery**: every planted block's scaling exponent is recovered
  within **±0.15** (master plan §18.3), **and**
* **shape-family recovery**: the fitted shared `Phi` reproduces the planted shape
  within 5% relative RMSE after the single positive rescaling of the energy axis
  that the collapse model leaves free, and is monotone decreasing.

Held-out generalization to unseen chemistry is already inside acceptance via F4,
F5, F6 and the ceiling fraction.

**Family recovery** — whether the reported representative and the planted law
satisfy the full `TYPE2_FAMILY_EQUIVALENCE.md` predicate, including dense
predictive agreement on the independent lattice — is **measured and reported for
every world but is not part of the gate**. The reason is stated in advance: the
master plan's §13.5 lattice is an independent Latin hypercube that deliberately
destroys the corpus's correlation structure, so a candidate written on
`total_atom_count` and a planted law written on `precursor_mz` can carry the same
support and the same exponent and still diverge on that lattice. Gating on it
would convert an unidentifiable proxy choice into a recovery failure. The gate is
support, exponent and shape; family recovery is reported beside them, and where
it fails while the gate passes, the report says so.

**The governing gate: Type 2 success in ≥ 80% of the 20 G1B moderate-regime
replicates**, with median selection frequency ≥ 20/30 across them.

**Exact algebraic-form recovery is measured and reported separately, for every
world, and is never folded into the gate.** Where it fails while Type 2 succeeds,
the report must say exactly that.

## 12. Independent-engine corroboration

`TYPE2_ENGINE_CORROBORATION.md`, frozen with this file. Gate: on the G1B
moderate worlds, block-level effective support agrees in ≥ 50% of worlds **and**
the mass-block exponent agrees within ±0.15 in ≥ 50%.

## 13. Runtime, hardware and checkpointing

`RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md`, computed from `muru.objval.plan2` so
it cannot drift from what is executed. 2024 MacBook Air, 8 cores (4 performance
+ 4 efficiency), 16 GB. Threads pinned to 1 for OMP, OpenBLAS, MKL, VECLIB and
NUMEXPR. Checkpoint unit is one `(block, world, seed)` run, written
tmp-then-atomic-rename. Parallelism is independent single-process shards, not a
worker pool, because `juliacall` does not survive multiprocessing teardown.

If the projected governed runtime exceeds **2 hours** the run does not start
without explicit approval, with the arithmetic, the benchmark and the
scope-reduction options presented first.

## 14. Method-development boundary

Development used **only** already-seen Phase 3 artifacts, and is recorded in
`TYPE2_SELECTION_RULE.md` §5–§6, `TYPE2_ENGINE_CORROBORATION.md` §2 and
`artifacts/ov_dev_*.json`. It did not use real `mu`, did not touch confirmation
outcomes, and did not generate any fresh validation world.

**After the freezing commit:** no selector change, no tolerance change, no seed
change, no threshold change, no operator change, no complexity-rule change. An
implementation bug may be fixed; a methodological change may not be made. The
distinction is recorded in `DEVIATIONS_OBJECTIVE_VALIDATION.md` with the
reasoning, and any governed experiment affected by a bug fix is rerun from
scratch.

## 15. Repair policy

At most **two** serious, scientifically justified repair attempts are permitted,
and **only** for a failure of the false-positive gate (§10) — the same class
Phase 3's policy covered. A repair may only tighten acceptance, and the entire
false-positive experiment is rerun under the revised frozen rule. Thresholds are
never tweaked repeatedly until a count falls below its limit.

**A failure of the positive-control gate is not repairable.** If the Type 2
system fails §11, the result stands and the verdict is
`DO NOT AUTHORIZE PHASE 4`. Loosening a criterion because the result is
disappointing is the move this study exists to avoid.

## 16. Sealed confirmation set

Completely sealed. No confirmation outcome is inspected, no candidate is run on
it, no symbolic search touches observed real `mu`, and the hash is verified
before and after the study. This study is entirely synthetic validation.
`tests/test_p3_seal.py` and `tests/test_ov_seal.py` fail if a sealed identifier
reaches any artifact.

## 17. Exact decision rule

`TYPE2_VALIDATION_DECISION.md` begins with exactly one of
`AUTHORIZE RE-SCOPED PHASE 4`, `DO NOT AUTHORIZE PHASE 4`, or
`INCONCLUSIVE DUE TO BLOCKER`, computed by `muru.objval.decision.decide` from
machine-readable artifacts. `GO TO PHASE 3` is not a possible output.

**`DO NOT AUTHORIZE PHASE 4`** if any of:

| # | Condition | Limit |
|---|---|---|
| 1 | G1A Type 2 success at low+moderate noise | < 4/4 |
| 2 | G1B **moderate** Type 2 success rate | < 0.80 |
| 3 | median G1B moderate selection frequency | < 20/30 |
| 4 | G1C worlds falsely claiming the algebraic form is identified | > 1 of 10 |
| 5 | fresh G4 false-positive rate | > 0.05 |
| 6 | G2 worlds yielding an accepted compact conjecture | > 1 of 8 |
| 7 | G3 worlds yielding an accepted non-mass structural claim | > 0 of 8 |
| 8 | G4M worlds yielding an accepted non-mass structural claim | > 0 of 30 |
| 9 | GC worlds yielding an accepted non-mass structural claim | > 1 of 9 |
| 10 | G5 worlds yielding an accepted non-mass structural claim | > 2 of 8 |
| 11 | GRT worlds yielding an accepted non-mass structural claim | > 1 of 4 |
| 12 | accepted G1B moderate candidates clearing the **upper bootstrap bound** of the null threshold | < 80% |
| 13 | independent-engine corroboration standard | not satisfied |

Condition 12 is how "null calibration is sufficiently stable" is made
operational: a candidate that clears only the point estimate and not the
threshold's own uncertainty has not been adjudicated.

**`INCONCLUSIVE DUE TO BLOCKER`** if a required gate cannot be evaluated —
missing worlds, an incomplete block, a changed confirmation-set hash, or evidence
that a real-data symbolic search was executed.

**`AUTHORIZE RE-SCOPED PHASE 4`** if none of the above fires. In that case, and
only then, `PHASE4_TYPE2_FROZEN_PROTOCOL.md` is written and the study stops.
Phase 4 is not started here.

## 18. Claims-ladder discipline

The highest defensible **real-data** rung is **L3** and this study does not raise
it, whatever its outcome. A synthetic recovery is not a MURU scientific
conjecture and is never called one. Any authorization is for the **positive-mode**
discovery question only.

## 19. Deliverables

`OBJECTIVE_ALIGNMENT_AMENDMENT.md`, `TYPE2_VALIDATION_PREREGISTRATION.md`,
`TYPE2_SELECTION_RULE.md`, `TYPE2_FAMILY_EQUIVALENCE.md`,
`TYPE2_ENGINE_CORROBORATION.md`, `RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md`,
`TYPE2_NULL_CALIBRATION.md`, `TYPE2_ENGINE_VALIDATION.md`,
`TYPE2_VALIDATION_DECISION.md`, `DEVIATIONS_OBJECTIVE_VALIDATION.md` if needed,
and machine-readable artifacts for the seed manifest, truth manifest, world
manifest, candidate families, support recovery, exponent recovery, exact-form
recovery, family-level recovery, null calibration, false-positive results,
refusal-world outcomes, corroboration, checkpoint state and runtime.

**No completed Phase 3 artifact is modified.**

## Environment

PySR 1.5.10 · SymbolicRegression.jl 1.11.3 · Julia 1.12.6 · gplearn 0.4.3 ·
SymPy 1.14.0 · NumPy 2.5.2 · pandas 3.0.5 · scikit-learn 1.9.0 · SciPy 1.18.0 ·
Python 3.13.12 · macOS (Darwin 25.1.0) arm64, 8 cores, 16 GB.
