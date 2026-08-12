# PHASE3_PREREGISTRATION.md — MURU ConjectureLab v1, Phase 3

**Discovery engine construction, synthetic ground truth, falsification and null
calibration.**

This file is frozen and committed **before any governed symbolic experiment is
run**. Everything below — generators, grammar, complexity, equivalence, seeds,
thresholds, harness, acceptance rule, K6 adjudication, repair policy and the
exact Phase 3 verdict rule — is fixed in advance. After the freezing commit,
any material methodological change must be recorded in `DEVIATIONS_P3.md`.

Phase 3 validates the **discovery machinery**. It does not discover the MURU
conjecture, and no synthetic result here licenses any statement about the real
MS/MS system.

---

## 0. Authorization and phase boundary

Phase 2 verdict, verified independently from machine-readable artifacts rather
than from the prose of `PHASE2_DECISION.md`:

| Check | Evidence | Result |
|---|---|---|
| Verdict | `artifacts/p2_decision.json` | `RESTRICT AND GO TO PHASE 3` |
| Highest real-data rung | `artifacts/p2_decision.json` | **L3** |
| K4A, primary scaffold-disjoint split S2 | ΔMAE −0.05432, 95% CI [−0.06349, −0.04515] | PASS |
| K4B vs MASS FLEX, positive mode | ΔMAE −0.02513, +20.02% against a 5% minimum | PASS |
| K5 | `K5_fires: false` | does not fire |
| K8 | +0.00159, CI [−0.00095, 0.00264] | does not fire |
| Structure beats MASS FLEX materially | interval excludes zero | yes |
| No-mass ablations retain information | −0.03686 (Tier A) and −0.05146 (flexible) vs B1 | yes |
| Negative mode | K4A PASS, **K4B FAIL** (+1.93%, CI [−0.01572, 0.00038]) | binding restriction |
| NC7 retention time | fires (+0.01006); incremental +0.00097 = 2.3% of the Tier A effect | qualified, not causal |
| Raw preprocessing branch | 39 compounds, 7.1% | matched subset only |
| Mass-coupling audit | regime D, ρ = −0.4791 stipulated | sensitivity, not identification |
| Sealed confirmation set | sha256 recomputed = `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` | intact |
| p-values | `(b+1)/(B+1)` | finite-sample |
| Final Phase 2 state | `0b5e13b06b73a811a77c3922be95d6b4c717e832`, clean tree, 168 tests pass | reproducible |

Per `MASTER_PLAN_CLARIFICATIONS.md` C1 the sequence is strictly
Phase 1 → 2 → 3 → 4 → 5. **Phase 3 may authorize Phase 4 only.** Phase 3 does
not perform Phase 4, does not open the sealed confirmation outcomes, and does
not run symbolic regression against the real `mu` response.

## 1. Scientific question

> Can a symbolic conjecture-discovery system reliably recover compact
> mathematical relationships when such relationships truly exist, while
> refusing to manufacture them when the data are mass-dominated, confounded,
> mechanically coupled, structurally complex, or null?

A negative answer is an acceptable and reportable Phase 3 result.

## 2. The confirmation seal

The sealed set is 110 compounds, 20.04% of the eligible positive-mode corpus,
82 scaffold groups, sha256
`d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07`.

Phase 1 selected the endpoint using the full corpus, so the set is **not**
pristine with respect to all study design. It remains sealed with respect to
Phase 2 modelling and to all of Phase 3: symbolic search, threshold
calibration, candidate selection and falsification tuning.

Phase 3 code reads the confirmation **identifiers only, and only to exclude
them**. `muru.synth.generators.load_dev_covariates` drops them by connectivity
key and asserts their absence; no response column of any confirmation compound
is opened anywhere in Phase 3. The hash is verified before and after the phase,
and `tests/test_p3_seal.py` fails if any Phase 3 artifact contains a sealed key.

## 3. Data used

Real-covariate, synthetic-response worlds are built on the **439 development
compounds** and the frozen six-point energy grid {15, 30, 45, 60, 75, 90} NCE.
Only covariates are read: the 12 frozen Tier A descriptors, scaffold group,
similarity cluster, mixture label. **No observed `mu` value enters any
synthetic response.** One fully synthetic family (GA) uses no real chemistry at
all.

Aggregate Phase 1/Phase 2 statistics used as scale references only: the
marginal `mu`-by-energy means (0.8414 → 0.4133), the measured 99.03% cell
coverage, and the Phase 1 variability figures in §7.

## 4. Dimensional discipline

Every variable entering the search is **dimensionless** (master plan 13.4):
energy in NCE/30, precursor mass in Da/500, counts divided by their
development-corpus median, TPSA/54.5, heteroatom fraction/0.25. `n_S` and
`n_halogen` have median 0 and take unit scale.

| Frame | Variables |
|---|---|
| Raw | `precursor_mz` (Da), `tpsa` (Å²), counts, NCE |
| Scaled / dimensionless | all of the above divided by the constants in `generators.SCALE` |
| Derived | `g_i`, the per-compound energy scale, itself dimensionless and identified only **up to a positive multiplicative constant** |

Any law recovered here is a statement about **dimensionless** quantities. It
must never be reported as a physical law in raw units.

## 5. Search targets

The master plan's T1 is primary: find `(Φ, g)` with `mu_ij ≈ Φ(E_j / g(z_i))`
by alternating a shared monotone `Φ` against per-compound scales.

- **T1 (collapse fit).** Three alternations of isotonic-`Φ` against a
  vectorized grid search for `log g_i`. Fitted for **every** world; its
  adequacy test decides H-MAIN.
- **T2 (governed symbolic target).** The estimated scale `ĝ_i`,
  inverse-variance weighted by the asymptotic variance of `log ĝ_i`, searched
  as a function of the 12 dimensionless Tier A descriptors. **This is the
  target every gate, threshold and false-positive count is computed on**, and
  it is the target the master plan assigns to the gplearn comparison arm.
- **T3 (diagnostic).** Direct `mu = f(E, z)` is not run as a gate; the collapse
  fit's residual diagnostics carry the same information at a fraction of the
  cost, and T3 is the easiest place to overfit (master plan 13.2).

**H-MAIN adequacy rule (frozen).** Leave-one-energy-out error of the collapse
model is compared against the same model with a per-compound shape exponent
freed, so the extra parameter is charged out of sample. H-MAIN is **rejected**
when the lower bound of a 95% compound-clustered bootstrap interval on the
ratio `collapse / free-shape` exceeds 1.0. No arbitrary inflation constant is
used.

## 6. Synthetic generator families

Generator version `p3-gen-1.0.0`, truth version `p3-truth-1.0.0`. Planted laws
live in `src/muru/synth/truth.py`, which **must not appear in the import
closure of `muru.discovery`**; `tests/test_p3_import_graph.py` enforces this.

Shared shape, calibrated once to the marginal means and frozen:
`Φ(u) = 0.2414 + 0.7586/(1 + u^1.4874)`, `c₁ = 1.7017`.

| Family | Planted law (dimensionless) | Role |
|---|---|---|
| **G1** | `g = c₁·√m` | clean recoverable collapse; master plan 18.1 |
| **G1B** | `g = c₁·√m·(1 + 0.35·hetfrac)` | clean collapse **with** non-mass structure; the Phase 2 K4B analogue, and the G1 block actually run |
| **G2** | scale **and** shape depend on descriptors, with a regime switch on aromatic ring count | predictable but **no compact universal collapse**; H-MAIN is false |
| **G3** | `g = c₁·m^0.6` | mass-only world; other descriptors stay mass-correlated because covariates are real |
| **G4** | `g = c₁·exp(0.22·ε)`, ε ⊥ all descriptors | **pure null**; the K6 basis |
| **G4M** | `g = c₁·√m·exp(0.18·ε)` | mass-conditional null; supplementary, matched to the Phase 2 question |
| **G5** | `g = c₁·√m·(1 + 0.40·L)`, `L` latent and never supplied | confounded; true driver unobserved, proxies at ρ ≈ 0.6 |
| **GC** | no descriptor law; absolute low-mass cutoff at 30/50/80 Da | **measurement-coupling adversary** (§7) |
| **GRT** | `g = c₁·√m·(1 + 0.30·LIPO)`, RT a downstream marker of LIPO | retention-time surrogate stress test |
| **GA** | `g = 1.5·v₀ + 0.5·v₁²`, i.i.d. covariates | fully synthetic analytic sanity case |

### 6.1 GC — the Phase 2 measurement-coupling adversary

Phase 2 restriction 1 is binding: a mass association of the observed sign and
comparable magnitude **can** be generated by `mu`'s normalization plus an
absolute low-mass cutoff, with no chemistry.

GC holds fractional fragmentation fixed as a **law** — every compound draws
fragment positions and intensities from one common, mass-independent
distribution — lets precursor mass vary, applies a fixed absolute low-mass
cutoff, and computes `mu` exactly as the real pipeline does:
`mu = SY + (1 − SY)·φ`, `φ = ⟨m/z fragment⟩ / m/z precursor`.

Per-compound realizations vary but are **independent of every descriptor**, so
any descriptor structure found in GC is spurious by construction. Cutoffs are
stipulated at three interpretable instrument settings (30, 50, 80 Da) and are
**never tuned** to reproduce the observed ρ = −0.676.

**This generator does not identify the mechanism of the real association.** It
does not establish what fraction of the observed association is artifactual,
and no such fraction is claimed anywhere in Phase 3.

### 6.2 GRT — retention-time surrogate

A latent property drives both the descriptors and retention time; RT predicts
the response observationally but is **not** the planted cause. Bounded stress
test only. It does not resolve the real NC7 finding causally, and Phase 2's
wording discipline stands: RT carries predictive signal by itself but adds
little beyond Tier A descriptors, consistent with a structure-associated
surrogate; independent confounding cannot be completely excluded.

## 7. Noise regimes — frozen

| Regime | SD on `mu` | Rationale |
|---|---|---|
| `low` | 0.010 | below any measured variability; recovery should be easy |
| `moderate` | **0.0295** | the Phase 1 **conservative inter-mixture variability estimate** |
| `adverse` | 0.060 | roughly double the upper bound; a deliberately hard regime |

`0.0295` is an **upper bound on technical repeatability**, not an instrument
noise floor and not pure Gaussian technical error
(`MASTER_PLAN_CLARIFICATIONS.md` C4). It is used only as a scale reference for
an additive synthetic perturbation. The Phase 1 lower bound, within-run scan SD
0.0396, is recorded but not used as the regime because it is measured on a
different unit of replication.

Missing cells are applied at the **measured** 0.97% rate, never taking a
compound below five energies. The master plan's assumed 15% missingness does
not describe this corpus (`DEVIATIONS_P3.md` D3).

## 8. Symbolic grammar — frozen

| Item | Value |
|---|---|
| Binary operators | `+`, `−`, `×`, `÷` |
| Unary operators | `sqrt`, `log`, `square`, `cube`, `inv` |
| Excluded | `exp` (`DEVIATIONS_P3.md` D1), all trigonometric functions |
| Maximum complexity | **20** |
| Nested-operator limits | no `sqrt(sqrt)`, `log(log)`, `log(sqrt)`, `inv(inv)`, `square(square)`, `square(cube)` and mirrors |
| Constants | optimized by the engine's inner optimizer; final constants re-fitted by weighted least squares on the **training** partition only |

**Protected numerics.** `|denominator| < 1e−12` → invalid; `inv` of a
near-zero argument → invalid; `log` of a non-positive argument → invalid;
`sqrt` of a negative argument → invalid; `|value| ≥ 1e12`, NaN or any
non-finite value → invalid. Invalid points are **excluded from the fit
statistic and counted against the candidate**; a candidate with more than
**0.5%** invalid points on the evaluation domain is rejected outright.
Candidate invalidity can never be converted into a favourable score.

## 9. Complexity — frozen

Node count over the canonical expression tree: a variable costs 1, a constant
costs 1, each binary operation costs 1, each unary operation costs 1. An
integer or half-integer power counts as **one** unary operation over its base,
so `x**2` costs 2 exactly as `square(x)` does — this keeps PySR and gplearn on
one scale.

**One function, `muru.discovery.grammar.complexity`, is used for candidate
ranking, the Pareto front, null calibration and the Phase 4 thresholds.** It is
not altered after seeing which planted equations are recovered.

## 10. Candidate equivalence — frozen

String equality is not a recovery criterion. The hierarchy:

1. symbolic simplification where it is safe and terminates
   (`simplify`/`cancel`/`powsimp`),
2. algebraic equivalence on the valid domain, **up to a positive multiplicative
   constant** — the collapse model identifies `g` only up to scale,
3. dense noise-free evaluation on an **independently generated** 10,000-point
   Latin hypercube over the descriptor domain (2,000 points for within-world
   clustering), never on training points,
4. variable-support comparison,
5. complexity comparison.

Tolerances: `rel_rmse < 1e−6` after optimal positive rescaling ⇒
**symbolic-equivalent**; `r > 0.999` and `rel_rmse < 0.02` ⇒ **functionally
equivalent**. A candidate counts as recovery if it is numerically equivalent
within tolerance even when simplification cannot prove identity. **A
high-complexity interpolant with tiny training error is not recovery.**

## 11. Ranking and stability — frozen

- **Per seed**: the complexity **elbow** over that seed's Pareto front — the
  smallest complexity whose validation R² is within **0.01** of the best on the
  front (master plan 13.4: chosen by the elbow, not by best fit). Ties break on
  lower complexity, then expression string.
- **Across seeds**: per-seed picks are clustered by numerical fingerprint into
  expression **families**; the world's candidate is the lowest-complexity
  member of the largest family. Selection frequency is that family's share.
- **Stability requirement**: ≥ **20 of 30** seeds (master plan L4). Stability is
  never defined by identical expression strings.

## 12. Seeds — frozen

**30 symbolic seeds per world** (master plan 13.4 minimum). The seed list is a
deterministic function of the world id, fixed before any governed run and
recorded in `artifacts/p3_seed_manifest.json`. PySR runs with
`deterministic=True` and `parallelism="serial"`; generator seeds derive from
`sha256(generator_version | family | replicate | noise_regime)`.

## 13. Engines

**PySR 1.5.10** (SymbolicRegression.jl 1.11, Julia via juliacall) is the
primary engine and stays primary. Configuration: `niterations=40`,
`populations=15`, `population_size=33`, `maxsize=20`, `parsimony=0.0032`,
`adaptive_parsimony_scaling=20`.

**gplearn 0.4.3** is the comparison arm on T2 only, with a **pre-registered
limited scope frozen before any result was seen**: blocks G1 and G3 in full,
plus the first 30 G4 nulls, at 10 seeds each (68 worlds, 680 runs). Full
duplication of every PySR experiment would multiply compute without additional
scientific value; master plan 13.3 makes gplearn a comparison arm, not a second
full engine.

gplearn **cannot rescue a failing PySR calibration**. If PySR fails K6 and
gplearn passes, the project is not switched: that would require an explicit
documented deviation and independent recalibration. Engine disagreement is
reported honestly either way.

## 14. Grouped synthetic evaluation

Each world is split **scaffold-group-disjoint** into train 60% / validation 20%
/ test 20%, groups filled largest-first into the currently smallest partition —
the same rule Phase 2 used. Whole trajectories move together; no scaffold group
straddles a boundary. F6 re-splits by similarity cluster instead. A leaked
row-level diagnostic may be computed but is always labelled as a leakage
diagnostic and never reported as performance.

## 15. Null calibration — frozen

Statistic: **the maximum over the 30 seeds of the best validation R² attainable
at complexity ≤ c**, for c = 1…20. Taking the max over seeds is what prices in
search multiplicity — the protocol runs the search 30 times and keeps the best,
so the null must be allowed the same.

- **40 calibration worlds**, cycling the four master-plan 13.6 null
  constructions (targets permuted across compounds; targets permuted across
  energy within compound; descriptors permuted across compounds; Gaussian
  targets with the observed variance structure).
- Threshold at each complexity = the **95th percentile** across calibration
  worlds, made non-decreasing in complexity (a larger hypothesis space cannot
  make chance fitting harder).
- Calibration worlds are **disjoint from the 100 G4 worlds** that measure the
  false-positive rate, so the rate is not measured against a threshold fitted
  to it.
- The resulting table is frozen for Phase 4.

## 16. Falsification harness F1–F12

Implemented as an automated ladder with machine-readable pass/fail per rung.
Ambiguities are resolved here, before any candidate performance was observed.

| Rung | Test | Status |
|---|---|---|
| F1 | reproducibility of the recorded artifact; engine determinism pinned by test | **required** |
| F2 | invariance to a defensible change in the estimation pipeline (the synthetic analogue of the §7.3 preprocessing grid, which has no synthetic counterpart) | **required** |
| F3 | source-branch invariance | **not applicable** — no independently reprocessed branch exists for a synthetic response |
| F4 | compound holdout | **required** |
| F5 | scaffold holdout — **primary claim gate**; test-partition R² must exceed the null threshold | **required** |
| F6 | similarity-cluster holdout | **required** |
| F7 | influence robustness: drop the top 5% most influential compounds, and leave-one-mix-out | **required** |
| F8 | descriptor ablation, single descriptors and the mass block `{precursor_mz, total_atom_count, rdbe}` together, plus a mass-only flexible comparator | **labelling** — if removing mass destroys the result the law *is* a mass law and is reported as such; it gates only a claim of structure beyond mass |
| F9 | energy-subset stability on {15,30,45}, {45,60,75,90}, {15,45,75} | **required** |
| F10 | negative controls: the candidate must **fail** on permuted targets; ≤ 5% of 20 permutations may exceed threshold | **required** |
| F11 | mode replication | **not applicable** — generators are mode-agnostic; Phase 2's negative-mode K4B failure remains binding |
| F12 | extrapolation probe | **supporting only**, never a gate — six energy levels cannot support one |

A rung that is not applicable is recorded as such and is **never silently
counted as a pass**. A candidate must survive the complete required set.

## 17. Acceptance rule — frozen

A candidate is **ACCEPTED** if and only if all of:

1. validation R² **exceeds the null threshold at its own complexity**,
2. selection frequency ≥ 20/30 seeds,
3. complexity ≤ 20,
4. invalid fraction ≤ 0.5%,
5. the complete required falsification set passes.

A candidate additionally **claims structure beyond mass** only if its variable
support contains a non-mass descriptor, ablating the non-mass descriptors
destroys the result, and the mass block alone does not reproduce it.

## 18. G4 false-positive experiment and K6

For each of the **100 G4 replicates**: generate the null world, run the frozen
30-seed search, apply the frozen ranking rule, apply the complete falsification
harness, and record whether a candidate would incorrectly be accepted.

```
false-positive rate = (number of null worlds producing an accepted conjecture)
                    / (number of valid null replicates)
```

Exact numerator and denominator are reported with a **Clopper–Pearson exact**
binomial interval. `p = 0` language is never used for a finite simulation
count.

**K6 is a hard Phase 3 gate: the rate must be ≤ 5%.** More than 5 of 100 valid
replicates producing an accepted conjecture fails the nominal point criterion.
The interval is reported alongside so the population rate is not overstated in
either direction.

### Repair policy

If K6 fails, at most **two** serious, scientifically justified repair attempts
are permitted. A repair may tighten candidate acceptance, complexity penalties,
null thresholds, stability requirements or falsification criteria — but only
through an explicitly documented rule motivated by the observed failure
mechanism. Thresholds are **not** tweaked repeatedly until the count falls
below five. Each repair is recorded in `DEVIATIONS_P3.md` and the **entire**
null experiment is rerun under the revised frozen rule. After two serious
unsuccessful attempts, **K6 FIRES and Phase 4 is not authorized.**

## 19. Per-family success and failure criteria — frozen

| Family | Required behaviour |
|---|---|
| **G1/G1B** | recover an equivalent or near-equivalent low-complexity expression: functional equivalence to the planted law, correct or substantively equivalent variable support, complexity ≤ 20, stability ≥ 20/30, and the mass exponent recovered within **±0.15** of the planted 0.5 (master plan 18.3). Both **symbolic-equivalent** and **functionally equivalent** recovery rates are reported. Target: L4-or-above recovery in **≥ 80%** of replicates |
| **G2** | H-MAIN rejected. **No accepted compact conjecture is the correct outcome** and is not penalized. Consistently manufacturing a simple accepted law here is a scientific warning or blocker by severity |
| **G3** | a mass-based candidate may legitimately be accepted and must be **reported as a mass law** by F8. Any accepted candidate claiming non-mass structural dependence that is not mathematically redundant with the planted mass law is a **failure** — the Phase 2 K5 threat realized |
| **G4** | no accepted conjecture, in ≥ 95% of 100 replicates |
| **G4M** | no accepted conjecture **claiming structure beyond mass** |
| **G5** | the confounded proxy expression must not survive the complete harness as a mechanistic conjecture; unexplained between-compound variance flagged |
| **GC** | no accepted conjecture claiming **non-mass structural** dependence. A mass-associated candidate is expected — the honest, achievable discrimination is that the system must not manufacture chemistry from a normalization artifact, not that it can tell a real mass law from an induced one using the response alone |
| **GRT** | RT-associated expressions must not be promoted as mechanistic conjectures |
| **GA** | the analytically transparent law is recovered |

Judgement is of the **whole pipeline**, not of raw search: it is acceptable for
PySR to propose attractive expressions in confounded and coupled worlds. The
critical question is whether the adjudication system rejects them.

## 20. Comparison to flexible prediction

A symbolic candidate is **not** required to outperform a flexible predictor.
Interpretability and generalization are different objectives. Within synthetic
worlds, symbolic candidates are compared against a mass-only flexible
comparator (the MASS FLEX analogue) only to understand the cost of compression.

## 21. Runtime, hardware and checkpointing

2024 MacBook Air, 8 cores, 16 GB. Full arithmetic in `RUNTIME_BUDGET_P3.md`,
computed **from** `muru.synth.plan` so it cannot drift from what is executed.
Summary: 240 worlds × 30 seeds = **7,200 PySR runs**, plus 68 × 10 = **680
gplearn runs**. Benchmarked 2.3 s per run serial and 3.1 s at 4 workers
(2.97× speedup, 0.775 s per run of wall time), 1.16 GB per process. Six workers
returned only 11% more throughput for 50% more memory — rejected. Projection
**≈ 1.9 h wall**, peak memory ≈ 4.6 GB.

Threads pinned to 1 for OMP, OpenBLAS, MKL, VECLIB and NUMEXPR. Checkpoint unit
is one (block, world, seed) run, written tmp-then-atomic-rename. Worst case
lost to an interruption: the 4 units in flight, ≈ 13 s.

## 22. Exact Phase 3 decision rule

`PHASE3_DECISION.md` begins with exactly one of `GO TO PHASE 4`,
`RESTRICT AND GO TO PHASE 4`, `STOP BEFORE PHASE 4`, or
`INCONCLUSIVE DUE TO BLOCKER`, computed from this rule and not chosen
afterwards.

**`STOP BEFORE PHASE 4`** if any of:

- K6 fires after the permitted repair attempts;
- G1/G1B is not recovered at the required standard in ≥ 80% of replicates at
  the **moderate** noise regime;
- an accepted compact conjecture appears in **more than 1 of 8** G2 worlds;
- any G3 world yields an accepted candidate claiming non-mass structural
  dependence not redundant with the planted mass law;
- more than 1 of 9 GC worlds, or more than 2 of 8 G5 worlds, yields an accepted
  candidate claiming non-mass structural dependence;
- median seed-selection frequency across G1 worlds is below 20/30;
- the null threshold table is not reproducible from the recorded seeds.

**`GO TO PHASE 4`** if none of the stop conditions hold, K6 does not fire, and
no binding restriction is required.

**`RESTRICT AND GO TO PHASE 4`** if none of the stop conditions hold and K6 does
not fire, but the evidence supports a concrete, enforceable constraint on
Phase 4 — for example a complexity ceiling below 20, an operator restriction, a
noise-regime limit, or a mandatory additional Phase 4 falsification test.

**`INCONCLUSIVE DUE TO BLOCKER`** if a required gate cannot be evaluated.

## 23. Claims-ladder discipline

Phase 2's highest defensible real-data rung is **L3** and Phase 3 does not
raise it. L4 requires an actual real-data symbolic candidate, which belongs to
Phase 4. Even a perfect Phase 3 result leaves the real-data claim at **L3**
while separately stating that the conjecture-discovery engine passed its
synthetic validation.

A synthetic planted-law recovery is **not** a MURU scientific conjecture and is
never called one. Any Phase 4 authorization is for the **positive-mode**
discovery question only, since Phase 2's structure-beyond-mass result does not
replicate in negative mode.

## 24. Deliverables

`PHASE3_PREREGISTRATION.md`, `RUNTIME_BUDGET_P3.md`, `SYNTHETIC_GENERATORS.md`,
`SYMBOLIC_SEARCH_SPEC.md`, `FALSIFICATION_HARNESS.md`, `NULL_CALIBRATION.md`,
`ENGINE_VALIDATION.md`, `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md`,
`DEVIATIONS_P3.md`, `PHASE3_DECISION.md`, and machine-readable artifacts for
seeds, generator manifests, results, candidates, complexity, null calibration,
false-positive counts, falsification outcomes, checkpoints and the frozen
Phase 4 protocol.

## Environment

PySR 1.5.10 · SymbolicRegression.jl ~1.11 · gplearn 0.4.3 · SymPy 1.14.0 ·
NumPy 2.5.2 · pandas 3.0.5 · scikit-learn 1.9.0 · SciPy 1.18.0 ·
RDKit 2026.03.5 · Python 3.13.12 · macOS (Darwin 25.1.0), 8 cores, 16 GB.
