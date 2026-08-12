# PHASE3_DECISION.md

# STOP BEFORE PHASE 4

Phase 3 of MURU ConjectureLab v1: discovery-engine construction, synthetic
ground truth, falsification and null calibration.

Pre-registration `PHASE3_PREREGISTRATION.md`, sha256
`064ce1fb9939b10d3b22be1f74aa3da28f487ec3917449db0794cf6431af5a63`,
committed `9ca09e9b950d4c473af6ff8740f8b3d1625d1a2b` **before** any governed symbolic run in this
document was executed. The verdict above is **computed** from the decision rule
in that file (§22), not chosen after the fact.

Phase 3 validates the **discovery machinery**. It does not discover the MURU
conjecture. No synthetic result here licenses any statement about the real
MS/MS system.

---

## Phase 2 gate verification

Verified independently from machine-readable artifacts, not from
`PHASE2_DECISION.md` prose.

| Check | Evidence | Result |
|---|---|---|
| Verdict | `p2_decision.json` | `RESTRICT AND GO TO PHASE 3` |
| Highest real-data rung | `p2_decision.json` | **L3** |
| K4A on the pre-registered S2 split | ΔMAE −0.05432, CI [−0.06349, −0.04515] | PASS |
| K4B vs MASS FLEX, positive mode | −0.02513, +20.02% ≥ 5% | PASS |
| K5 | `K5_fires: false` | does not fire |
| K8 | +0.00159, CI spans zero | does not fire |
| Structure beat MASS FLEX materially | interval excludes zero | yes |
| No-mass ablations retained information | −0.03686 and −0.05146 vs B1 | yes |
| Negative mode | K4A PASS, **K4B FAIL** (+1.93%) | binding restriction |
| NC7 retention time | fired; incremental +0.00097 (2.3%) | qualified, not causal |
| Raw preprocessing branch | 39 compounds (7.1%) | matched subset only |
| Mass-coupling audit | regime D, ρ = −0.4791 stipulated | sensitivity, not identification |
| Sealed confirmation set | sha256 recomputed = expected | intact |
| p-values | `(b+1)/(B+1)` | finite-sample |
| Final Phase 2 state | `0b5e13b`, clean tree, 168 tests pass | reproducible |

## Confirmation seal

| Item | Value |
|---|---|
| Compounds | 110 (20.04%), 82 scaffold groups |
| SHA-256 before and after Phase 3 | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` |
| Opened during Phase 3 | **No** |
| What Phase 3 read | connectivity identifiers only, to exclude them |

Phase 3 built every real-covariate world on the **439 development compounds**.
`tests/test_p3_seal.py` asserts the hash, that no Phase 3 artifact contains a
sealed identifier, and that the synthetic response is not the observed one.

## Environment

| Component | Version |
|---|---|
| PySR (primary) | **1.5.10** |
| SymbolicRegression.jl | 1.11.3 |
| Julia | 1.12.6 |
| gplearn (comparison arm) | 0.4.3 |
| SymPy | 1.14.0 |
| Generator / truth version | `p3-gen-1.0.0` / `p3-truth-1.0.0` |

PySR smoke test on `1.5*x0 + 0.5*x1**2`:
recovered **True** as
`((x0 + square(x1)) / 2.0000467) + x0`. Identical Pareto front at a repeated
seed: **True**.

Successful installation is not scientific validation, and none is claimed from
it.

---

## Results by block

| Block | Worlds | Accepted | Claiming structure beyond mass | Median seed stability |
|---|---|---|---|---|
| G1B — clean collapse with non-mass structure | 30 | 23 | 23 | 1.00 |
| G2 — predictable, no compact collapse | 8 | 0 | 0 | 0.27 |
| G3 — mass only | 8 | 7 | 0 | 1.00 |
| G4 — pure null (K6) | 100 | 0 | 0 | 0.50 |
| G4M — mass-conditional null | 30 | 4 | 0 | 0.88 |
| G5 — confounded | 8 | 1 | 1 | 0.20 |
| GC — measurement coupling | 9 | 0 | 0 | 0.50 |
| GRT — retention-time surrogate | 4 | 0 | 0 | 0.58 |
| GA — analytic sanity | 3 | 3 | 3 | 0.97 |
| NCAL — null calibration | 40 | 0 | 0 | 0.48 |

## G1 recovery

Both rates are reported, as required: **symbolic-equivalent** recovery and
**functionally equivalent** recovery. A simpler algebraically equivalent form
counts; a high-complexity interpolant does not.

| Noise regime | Worlds | Accepted | Functional recovery | Symbolic recovery | Mass exponent within ±0.15 | Median exponent | Median complexity | Median stability |
|---|---|---|---|---|---|---|---|---|
| `low` | 10 | 10 | **0%** | 0% | 100% | 0.500 | 6 | 1.00 |
| `moderate` | 10 | 9 | **0%** | 0% | 100% | 0.500 | 6 | 1.00 |
| `adverse` | 10 | 4 | **0%** | 0% | 90% | 0.500 | 6 | 0.77 |

Planted mass exponent **0.5**. The master plan §18.3 criterion is recovery
within ±0.15.

### Two different criteria give two different answers, and both are reported

| Criterion | Source | Result at the moderate regime |
|---|---|---|
| exponent within ±0.15 **and** the recovered form is in the planted shape family | master plan §18.3, the weaker reading | **90%** |
| the above **and** functional equivalence to the complete planted law | `PHASE3_PREREGISTRATION.md` §19, the reading frozen in advance | **0%** |

The pre-registered reading is the binding one. It was chosen before any
performance was observed, precisely so that this choice could not be made
afterwards, and it is the one the decision rule uses.

### Why they diverge — the search finds the law and the ranking rule discards it

`scripts/t3_45_recovery_diagnosis.py` separates two questions that a single
recovery rate conflates. **Does any candidate anywhere on the 30 seeds' Pareto
fronts match the planted law, and does the frozen ranking rule select it?**

| World | Search **finds** the law | System **reports** it | Median complexity gap |
|---|---|---|---|
| `G1/low` | 100% | 0% | +2 |
| `G1/moderate` | 100% | 10% | +2 |
| `G1/adverse` | 30% | 0% | +2 |
| `G3/moderate` | 100% | 62% | +0 |
| `GA/moderate` | 100% | 100% | +0 |

The mechanism is specific. In `G1B` the planted law needs complexity **13**;
a complexity-**6** expression, `sqrt(precursor_mz · (heteroatom_fraction + c))`,
approximates it to within about 2.5% relative RMSE over the descriptor domain
and reaches a held-out R² within **0.004** of it. The frozen elbow rule takes
the smallest complexity whose validation R² is within 0.01 of the best on the
front, so it takes the approximation — every time, in every seed, at every noise
level.

This is not a search failure. It is a **candidate-selection failure**: the
system finds the truth and then reports something simpler that is
statistically indistinguishable from it on held-out data.

`GA` is the control that pins this down. Its law is representable at low
complexity, and there the same pipeline reports it in **100%** of worlds. `G3`,
a single power law, is reported in **62%**. The failure is confined to laws
whose true form sits above a near-equivalent approximation on the Pareto front —
and that is exactly the situation a real conjecture search would face.

## H-MAIN adequacy

The collapse model is compared against the same model with a per-compound shape
exponent freed, out of sample by leave-one-energy-out; H-MAIN is rejected when
the lower bound of a compound-clustered bootstrap interval on the ratio exceeds
1.0. No arbitrary inflation constant is used.

Worlds rejecting H-MAIN, by block:
**G1** 0/30, **G2** 8/8, **G3** 0/8, **G4** 0/100, **G5** 0/8.

G2 is the world built to have no single compact collapse, and it is the block
where H-MAIN rejection concentrates.

## G2 behaviour

0 of 8 G2 worlds produced an accepted
compact conjecture. **Refusing to produce an equation in G2 is the correct
outcome and is not penalized.** G2 exists to stop the project equating
"predictable" with "compressible into a universal law".

## G3 — the K5 threat

0 of 8 mass-only worlds produced
an accepted candidate claiming non-mass structural dependence. A candidate using
mass and energy may legitimately recover the planted relationship there; a
candidate claiming *additional* non-mass dependence must fail unless that
dependence is redundant with the planted mass law.

## G4 — false-positive rate and K6

```
false-positive rate = 0 / 100 = 0.0000
```

| Quantity | Value |
|---|---|
| Numerator | **0** |
| Denominator | **100** |
| Rate | **0.0000** |
| Clopper-Pearson exact 95% interval | **[0.0000, 0.0362]** |
| Criterion | ≤ 5% |
| **K6** | **K6 does not fire** |

`p = 0` language is not used for a finite simulation count: with
100 replicates the interval, not the point estimate, is
the claim.

**Supplementary — G4M mass-conditional null.** 30 worlds where
mass dependence is real and no non-mass structure exists:
4 accepted any candidate,
**0** claimed structure beyond
mass. K6 is adjudicated on G4 as the master plan specifies; G4M is reported
alongside, not instead.

## G5 — confounded worlds

1 of 8 confounded worlds produced
an accepted candidate claiming non-mass structure. The true driver is latent and
never supplied; observed descriptors are proxies. The question is not whether
the search proposes attractive expressions there — it is whether the complete
adjudication system rejects them.

## Measurement-coupling stress result

0 of 9 coupling worlds produced an
accepted candidate claiming non-mass structural dependence.

The generator holds fractional fragmentation fixed as a law, varies precursor
mass, applies an absolute low-mass cutoff at 30/50/80 Da, and computes `mu`
exactly as the real pipeline does. It reproduces both the sign and the
energy-growth of the real association **with no chemistry anywhere in the
construction**.

**Restriction, restated because it binds.** This is a robustness test of the
discovery system. It does **not** identify the mechanism of the real
association, and it does **not** establish what fraction of the observed real
association is artifactual. No such fraction is claimed.

## Retention-time surrogate stress result

0 of 4 GRT worlds produced an accepted
candidate. A latent property drives both descriptors and retention time; RT
predicts observationally but is not the planted cause.

This is a bounded synthetic stress test. It does **not** establish that the real
NC7 finding has been causally resolved. Phase 2's wording stands: RT carries
predictive signal by itself but adds little incremental information beyond
Tier A descriptors, consistent with a structure-associated surrogate in this
dataset; independent confounding cannot be completely excluded.

## Null thresholds

40 calibration worlds, cycling the four master-plan 13.6
constructions, disjoint from the 100 G4 worlds. Statistic: max over seeds of best validation R^2 at complexity <= c; the max over seeds is what prices in search multiplicity.

| Complexity | 4 | 7 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| Threshold | +0.3888 | +0.4166 | +0.4534 | +0.4597 | +0.4889 |

Frozen for Phase 4. Full table in `NULL_CALIBRATION.md`.

## Repair attempts

None. K6 did not fire, so no repair was permitted or needed.

## Runtime and checkpointing

| Item | Value |
|---|---|
| Worlds × seeds | 240 × 30 = **7200 PySR runs** |
| gplearn comparison arm | 680 runs |
| Workers | 4 (measured 2.97×; 6 workers rejected at +11% for +50% memory) |
| Thread caps | OMP/OpenBLAS/MKL/VECLIB/NUMEXPR = 1 |
| Projection | 1.69 h |
| Checkpoint unit | one `(block, world, seed)` run |
| Worst case lost to a crash | 12.4 s |

Checkpointing was exercised for real: the run was interrupted and resumed, and
resume recomputed nothing (`tests/test_p3_checkpoint.py` pins the four
properties).

## Comparison engine — gplearn

Master plan 13.3: "If two engines with different search dynamics converge on
equivalent expressions, that is evidence. If they do not, the expression is a
search artifact."

| Block | Worlds | Engines agree | Support match | PySR matches planted | gplearn matches planted |
|---|---|---|---|---|---|
| `G1` | 30 | 3% | 3% | 3% | 0% |
| `G3` | 8 | 0% | 0% | 62% | 0% |
| `G4` | 30 | 60% | 63% | — | — |

**The comparison arm did not corroborate PySR.** On the structured worlds the
two engines converge on functionally equivalent expressions almost never, and
gplearn never recovers the planted law — including in `G3`, a single power law
that PySR recovers 62% of the time. On the `G4` nulls the engines agree 60% of
the time, which is agreement about noise and is not evidence of anything.

This is reported as measured. It does not change the verdict, which is already
`STOP BEFORE PHASE 4` on the pre-registered rule, and no engine-agreement gate
was pre-registered. It is recorded because it points the same way: **PySR's
selected expressions are not independently corroborated**, and under the master
plan's own reading that is a reason to treat them as search artifacts rather
than as recovered laws.

gplearn was run at its pre-registered configuration on the pre-registered subset
(`DEVIATIONS_P3.md` D5). It is a comparison arm, not a tournament entrant, and
**nothing here would license switching the project to it** — that would require
an explicit deviation and an independent recalibration.

## GA — analytic sanity case

3 of 3 fully synthetic worlds recovered the
transparent planted law `1.5·v₀ + 0.5·v₁²`, found by the search and selected by
the ranking rule. This world uses no real chemistry, so it isolates the
machinery from any property of the real descriptor matrix.

Its first construction planted the law in the raw frame while the search saw the
dimensionless frame, making it unrecoverable by construction; that was found by
the sanity case doing its job and is recorded in `DEVIATIONS_P3.md` D9.

## Stop conditions, evaluated explicitly

| Condition | Fired |
|---|---|
| K6 fires after the permitted repairs | no |
| G1 recovery below 80% at the moderate noise regime | **FIRED** |
| more than 1 of 8 G2 worlds yields an accepted compact conjecture | no |
| any G3 world yields an accepted non-mass structural conjecture | no |
| more than 1 of 9 GC worlds claims non-mass structure | no |
| more than 2 of 8 G5 worlds claims non-mass structure | no |
| median G1 seed-selection frequency below 20/30 | no |
| null threshold table not reproducible | no |

## What must change before Phase 4 can be reconsidered

Phase 3 stopped on **candidate selection**, not on false positives, not on
search capability, and not on the falsification harness — all of which passed.
The specific, reproducible defect and its evidence:

**The elbow rule resolves near-degenerate Pareto fronts in favour of the wrong
expression.** With a tolerance of 0.01 absolute R², a complexity-6
approximation that sits 0.004 R² below the complexity-13 planted form is
preferred to it, in 30 of 30 seeds, at every noise level tested.

A future attempt would need to change the candidate-selection rule and then
**recalibrate the null thresholds under the changed rule**, because the
threshold is conditioned on the complexity the rule selects. Candidate
directions, recorded so the reasoning is not lost, and **deliberately not
applied here**:

1. tighten the elbow tolerance, or make it relative to the front's own R² spread
   rather than absolute;
2. carry the whole Pareto front forward and adjudicate every knee against the
   null, rather than committing to one candidate per seed;
3. report the recovered **variable support and scaling exponents** as the
   claim, and treat the functional form as unidentified — which is what this
   evidence actually supports.

**None of these was applied.** Changing the selection rule after seeing that the
planted recovery failed is exactly the move Phase 3 exists to prevent, and the
pre-registration's repair allowance is scoped to K6 alone, which did not fire.

## Restrictions that would have applied, recorded for a future attempt

These were computed by the decision rule and are preserved because they remain
true of the evidence, not because Phase 4 is authorized. **It is not.**

1. **Noise ceiling.** Functional recovery at the adverse regime (SD 0.06) is 0% against 0% at the moderate regime. Phase 4 must report the residual scale of its own fit and treat a candidate found at comparable or worse noise as unconfirmed.
2. **Complexity ceiling.** Every accepted G1 recovery sits at complexity ≤ 6, well inside the budget of 20. Recovery was demonstrated only in that range, so a Phase 4 candidate above complexity 6 is outside the validated envelope and must be reported as such.
3. **The null threshold is a point estimate with wide uncertainty.** At complexity 20 the frozen threshold is +0.4889 with a bootstrap interval of [+0.2603, +0.6859], because a 95th percentile from 40 null worlds rests on its top two or three. Phase 4 must report any candidate's margin over the threshold, and a candidate whose R² falls inside that interval is **not** to be reported as clearing the null — it is inconclusive and requires an enlarged calibration before any claim.
4. **Positive mode only.** Phase 2's structure-beyond-mass result does not replicate in negative mode (K4B FAIL, +1.93%, scaffold interval [-0.01572, 0.00038] spanning zero). Any Phase 4 authorization is for the positive-mode discovery question.
5. **No mechanistic reading may lean on RT-correlated descriptors.** NC7 fired in Phase 2 and is explained but restricting; the Phase 3 GRT stress test does not resolve it causally.
6. **No full-corpus preprocessing-invariance claim.** The raw branch covers 39 compounds (7.1%).

## Unresolved issues

See `BACKLOG.md`. Phase 2's open items I1, I2, I3, I5 and I6 remain open and are
untouched by Phase 3, which is synthetic throughout.

## Highest defensible real-data claims-ladder rung

# L3

**Unchanged by Phase 3.** Structure explains between-compound variation beyond
mass on scaffold-disjoint holdouts. L4 requires an actual real-data symbolic
candidate, which belongs to Phase 4.

A synthetic planted-law recovery is **not** a MURU scientific conjecture and is
not called one. What Phase 3 establishes is separate and narrower: whether the
conjecture-discovery engine passes its synthetic validation.

## Phase 4 authorization

**STOP BEFORE PHASE 4**

Phase 4 is NOT authorized.

The frozen adjudication protocol is `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md` with
machine-readable companion `artifacts/phase4_frozen_protocol.json`. It was
**not executed on the real response during Phase 3**.

## What Phase 3 did not do

No real-data symbolic discovery. No symbolic engine was fitted to the observed
`mu`. No candidate equation was tested against real development `mu`. The sealed
confirmation set was not opened. No Phase 4 implementation exists in this
commit.
