# PREREGISTRATION.md — MURU ConjectureLab v1, Phase 2

**Status:** frozen. Committed before any Phase 2 outcome model was executed.

Everything below is fixed in advance. Any material methodological change after
this file's commit is recorded in `DEVIATIONS.md` with its reason, and appears
in `PHASE2_DECISION.md`. Thresholds and model definitions are not altered after
performance is observed.

Governing documents: `MURU_ConjectureLab_v1_Master_Plan.md`,
`MASTER_PLAN_CLARIFICATIONS.md` (C1–C5), `PHASE1_DECISION.md` (five binding
carry-forward restrictions).

---

## 1. Primary scientific question

> Does molecular structure predict the collision-energy trajectory of mu for
> unseen chemistry beyond what can already be explained by collision energy and
> precursor mass?

**A negative answer is an acceptable Phase 2 result.** Phase 2 establishes
whether reproducible structural predictive information exists. It does not
establish mechanism.

## 2. Primary endpoint

**mu**, the intensity-weighted normalized spectrum mass, selected on measured
evidence in Phase 1 (`ENDPOINT_SCREEN.md`). **Endpoint selection is not
reopened.**

Secondary: fragment depth. Robustness: spectral entropy. Diagnostic: survival
yield. A disappointing primary result is not replaced by a more attractive
secondary one.

Per Phase 1 carry-forward and instruction 12, survival yield is **not** treated
as a conventional continuous response above NCE 30, and no elaborate censored
survival model is required for Phase 2 completion.

## 3. Analysis population

Positive mode, base preprocessing cell, compounds with **≥ 5 of 6** collision
energies: **549 compounds / 3,262 compound-by-energy rows**.

The six compound-by-mode keys that map to two internal MassBank IDs
(`DATA_CENSUS.md`, deviation D3 / issue M1) are **averaged to one trajectory per
compound** so that a compound contributes one unit of analysis. Phase 1 left
them interleaved; that choice made Phase 1's monotone fractions slightly
conservative and is documented in `DEVIATIONS.md` D9.

After sealing the confirmation set: **development corpus = 439 compounds /
2,610 rows**.

## 4. Confirmation set

- **Unit of selection:** Bemis-Murcko scaffold group (not compound).
- **Rule:** scaffold groups walked in seeded random order (seed `20260811`),
  each taken unless it would push the set past 115% of the 20% target. The
  tolerance exists because group sizes are extremely uneven — the benzene group
  alone is 14.6% of the corpus — so an unbounded "add until ≥ target" loop
  overshoots to 28.6%. Every group remains eligible; large groups are not
  systematically excluded.
- **Result:** **110 compounds (20.04%)** across 82 scaffold groups.
- **Sealed artifact:** `artifacts/confirmation_set_sealed.json`
- **SHA-256:** `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07`

**Phase 2 does not open it.** No endpoint value from these compounds is loaded,
no performance is computed on them, they inform no descriptor choice, no
threshold, and no model comparison. Phase 2 operates on the development corpus
only.

### 4.1 Mandatory disclosure

The confirmation compounds are **not** unseen in the broadest scientific sense.
Phase 1 used the full positive-mode corpus — including these compounds — to
select mu, compare endpoints, characterize monotonicity, evaluate confounding,
and characterize the collision-energy response.

The defensible statement, which is the only one this project will make, is:

> The confirmation compounds were excluded from Phase 2 and later model fitting,
> hyperparameter tuning, symbolic search, candidate selection, and threshold
> adaptation. The primary endpoint was selected during the earlier corpus-wide
> Phase 1 audit.

## 5. Splits

Connectivity key: **InChIKey first block**. Every collision energy and every
internal ID sharing a connectivity moves together. Disjointness is enforced by
assertion (`src/muru/splits.py`), not by inspection. 5 grouped folds each,
seeded, with folds filled greedily largest-group-first into the currently
smallest fold so one large scaffold cannot dominate a fold.

| Split | Group key | Role |
|---|---|---|
| **S2** | Bemis-Murcko scaffold group | **PRIMARY** |
| S1 | connectivity block | secondary |
| S3 | Butina cluster, Tanimoto ≥ 0.6 | secondary / stress test |
| S0 | row-level (deliberately leaked) | diagnostic only, never reported as performance |

### 5.1 S2 accepted as primary — audit performed before any performance was seen

368 scaffold groups over 549 compounds; 322 singletons; largest group (benzene)
80 compounds = **14.6%**. Neither degenerate nor dominated. **S2 is meaningful
for this corpus** and is pre-registered as primary. Full audit in
`SPLIT_AUDIT.md`.

### 5.2 Ringless policy (MASTER_PLAN_CLARIFICATIONS C5)

32 of 549 compounds (5.8%) are acyclic and yield an empty Murcko scaffold. Each
becomes **its own scaffold group keyed by its connectivity block**. They are
**not** pooled into a single empty-scaffold group, which would assert a shared
core that does not exist. Consequence, declared in advance: S2 is marginally
easier for those 5.8%. S3 covers them properly by similarity.

### 5.3 Butina implementation

RDKit's `Butina.ClusterData` takes a **distance** cutoff. The pre-registered
Tanimoto **similarity** threshold of 0.6 is converted as `distance = 1 - 0.6 =
0.4`. Pinned by `tests/test_splits.py` using synthetic bit vectors with
hand-computed Tanimoto values, including a regression test that a pair at
similarity 0.4 is **not** merged under a 0.6 similarity threshold.

## 6. Tier A — frozen, 12 descriptors

precursor_mz, total_atom_count, rotatable_bonds, ring_count,
aromatic_ring_count, rdbe, tpsa, heteroatom_fraction, n_N, n_O, n_S, n_halogen.

Retention rule, applied before any outcome was observed: computable for every
compound, non-degenerate, mechanistically motivated, and not rank-redundant with
a descriptor already retained.

**Dropped candidates and reasons:**

| Dropped | Reason |
|---|---|
| exact_mass, mol_wt | Spearman **1.000** with precursor_mz — rank-identical and mathematically dependent |
| labute_asa | 0.985 with mass, 0.993 with heavy-atom count; the "molecular volume" slot carries nothing beyond mass here and would contaminate the K5 mass ablation |
| heavy_atom_count | 0.974 with mass, 0.903 with total_atom_count, which is the principled 3N−6 DOF proxy |

**Descriptors are not added later because cross-validation performance is
disappointing.**

Residual collinearity after the freeze: no pair reaches 0.90 (max **0.872**,
aromatic_ring_count~rdbe). VIF is nonetheless high for precursor_mz (**51.0**)
and total_atom_count (**34.5**). Consequence declared in advance: **individual
Tier A coefficients and per-descriptor importances are not interpreted
causally**; importance is reported over correlated blocks.

**Mass block for K5 ablation:** `precursor_mz`, `total_atom_count`, `rdbe` —
removed together, because dropping the named mass variable alone leaves its
proxies in place.

## 7. Tier B — frozen

Morgan fingerprints radius 2, 2048 bits (1,823 ever set) + a frozen 26-descriptor
RDKit block. **1,849 features total.** No learned embeddings, no graph neural
networks, no AutoML, no expansion after performance is observed. Tier B is a
finite pre-registered benchmark, not a feature search.

## 8. Baseline ladder

Every model answers a distinct scientific question. No leaderboard.

| Model | Specification | Question |
|---|---|---|
| **B0** | global mean of mu | floor |
| **B1** | per-energy mean (6-level factor), structure-blind | is there any energy signal |
| **B2 / MASS SIMPLE** | energy factor + **linear** precursor m/z | is the effect just mass, simply |
| **MASS FLEX** | see §9 | is the effect just mass, strongly |
| **Tier A** | ridge on Tier A × energy-spline interaction | interpretable structure model |
| **HIER** | mixed model, compound random intercept + slope | variance decomposition |
| **Tier B / FLEXIBLE PREDICTIVE BENCHMARK** | gradient boosting, §10 | recoverable nonlinear structural information |

### 8.1 MASS SIMPLE (B2)

`mu ~ C(NCE) + beta * precursor_mz`, ordinary least squares. The Phase 1
carry-forward competitor, unchanged.

## 9. MASS FLEX — frozen before structure-model performance was observed

`mu ~ tensor product of a natural cubic B-spline basis in NCE (5 knots) and in
precursor m/z (6 knots)`, i.e. a full smooth surface permitting nonlinear energy
response, nonlinear mass response, and an energy-by-mass interaction. Fitted by
ridge regression; the ridge penalty is selected **only** in the inner grouped CV
loop, over `alpha ∈ {1e-4, 1e-3, 1e-2, 1e-1, 1, 10}`.

MASS FLEX is not made deliberately weak, and its complexity is **not** increased
after results are seen.

## 10. Flexible predictive benchmark

One family: `sklearn.ensemble.HistGradientBoostingRegressor`. Frozen search
space, selected in the inner loop only:

- `max_depth ∈ {3, 6, None}`
- `learning_rate ∈ {0.05, 0.1}`
- `max_iter ∈ {200, 500}`
- `min_samples_leaf ∈ {10, 20}`
- `l2_regularization ∈ {0.0, 1.0}`

The space is **not enlarged** if performance disappoints. Per
`MASTER_PLAN_CLARIFICATIONS` C2 this is a **flexible predictive benchmark**, not
a ceiling; the rule "any baseline beating B7 signals a bug" is revoked. If a
simpler model wins, implementation, split and metric are verified and the result
is reported as measured.

## 11. Primary statistical model and the likelihood decision

**Response modelled on the natural scale, not logit.** Measured before freezing
(`artifacts/p2_prereg_diagnostics.json`):

- mu ∈ [0.0954, **1.0000008**]; **9 rows exceed 1** and 1 equals 1 exactly, via
  the ppm-level recalibration effect Phase 1 documented as deviation D1. A logit
  link and a Beta likelihood are both **undefined** there. Master plan §9.2 is
  inadequate as written → `DEVIATIONS.md` **D7**.
- `logit(mu)` linear in NCE: median R² 0.824, **69.8%** of trajectories below
  0.9. Linear in log NCE: median R² 0.926, 40.2% below 0.9. The plan's
  two-parameter `alpha_i + beta_i·h(E)` form does not describe these
  trajectories → `DEVIATIONS.md` **D8**. **Energy is treated nonparametrically**
  (6-level factor or spline), never as a 2-parameter linear term.
- Per-energy SD ratio max/min = 1.41 — heteroskedasticity mild.
- Marginal between-compound variance share = 0.470.

**HIER specification:** `statsmodels` MixedLM, compound random intercept +
random slope in centred energy, Tier A fixed effects. Its purpose is the
**variance decomposition**, not prediction.

**PyMC/numpyro deliberately not used** (instruction 14). mu has no censoring —
that was survival yield, which Phase 2 does not model as a continuous response;
n is ample; and every interval reported here comes from a compound-level
bootstrap rather than a posterior. Adding a probabilistic programming framework
would add implementation risk and sampling diagnostics without changing any
Phase 2 answer. Decision recorded in `VARIANCE_DECOMPOSITION.md`.

## 12. Evaluation protocol

Nested grouped cross-validation. **Outer** 5-fold grouped by the split's group
key; **inner** 4-fold grouped within each training fold for hyperparameter
selection only. No outer fold ever informs selection. Only outer-fold
performance is reported.

## 13. Metrics

Reported for every model under S1, S2, S3:

- **MAE** on natural-scale mu (primary)
- **RMSE** on natural-scale mu
- **R²** where meaningful, never alone and never as the decision variable
- **paired** held-out error differences at compound level
- compound-level bootstrap intervals

For the key comparison (structure model vs MASS FLEX) the **paired distribution
of compound-level held-out errors** is reported, not only a summary. A small R²
increase without a meaningful reduction in held-out error is **not** sufficient
evidence of useful structural information.

## 14. Bootstrap

**The molecule is the primary resampling unit.** 2,000 resamples. Spectra are
never resampled independently; all six energies of a molecule move together.

For S2 and S3 stress tests, resampling is additionally performed at the
**scaffold** and **cluster** level respectively, because the uncertainty claim
there concerns generalization to unseen scaffolds/clusters, not unseen
molecules. Both are reported; the scaffold/cluster-level interval is the one
quoted for a scaffold-disjoint or cluster-disjoint claim.

## 15. Negative controls and the null decision rule

NC1 energy permutation within molecule; NC2 descriptor permutation across
molecules; NC3 trajectory↔descriptor permutation; NC4 sham descriptor (uniform
random + an alphabetical-name index); NC6 mixture identity; NC7 retention time.

**Null decision rule, fixed in advance.** Each control is run with **200
permutation replicates**, and the observed statistic is compared against the
**95th percentile of its own matched permutation null**. The controls are *not*
six independent α = 0.05 tests: the family-level criterion is that **no control
exceeds its empirical 95th-percentile threshold after Benjamini-Hochberg
correction at q = 0.10 across the six**.

A negative control showing reproducible signal above its pre-registered null
threshold is a **BLOCKER** until explained, and yields
`INCONCLUSIVE DUE TO BLOCKER`.

## 16. Preprocessing robustness

1. Full Phase 2 analysis on the curated MassBank corpus.
2. Identify the matched independently processed raw subset (39 compounds, mixes
   499/503/505, positive mode).
3. Repeat applicable headline comparisons on that matched subset.
4. Compare direction, magnitude, residual behaviour, qualitative conclusion.
5. **Distinguish explicitly** between full-corpus evidence and subset
   preprocessing robustness.

Subset agreement is **not** extrapolated to the corpus, and no claim of
full-corpus independent raw replication is made.

## 17. Mixture confounding

Test whether mixture identity materially improves prediction **after** energy
and mass are included. If mixture identity carries predictive information
comparable to the molecular descriptors, K8 is evaluated explicitly and
leave-one-mixture-out sensitivity is run.

## 18. Negative-mode scope

The primary Phase 2 experiment is **positive mode**. Negative mode receives the
K4A/K4B comparison under S2 only, to establish whether the qualitative
conclusion replicates. **No claim requiring a negative-mode noise estimate is
made** — negative-mode repeatability is UNKNOWN (Phase 1 issue I2) and Phase 2
does not acquire it. Negative mode does not double Phase 2 scope.

## 19. Measurement-variability wording

The Phase 1 figure (mu SD **0.0295**) is the **conservative inter-mixture
variability estimate**, an **upper bound** on technical repeatability. It is
never called the instrument noise floor, pure technical replicate variance, or
an exact measurement-error variance.

## 20. Kill criteria and minimum effect sizes

### K4A
> Does the flexible structure-aware model beat the structure-blind energy
> baseline **B1** on the pre-registered primary split **S2**?

**Pass:** mean compound-level MAE reduction vs B1 > 0, with the **lower bound**
of the 95% compound-level bootstrap interval on the paired difference above
zero.
**Fail ⇒ Phase 3 is NOT authorized.**

### K4B
> Does the structure-aware model also beat **MASS FLEX** by a scientifically
> meaningful amount?

**Pass requires both:**
1. lower bound of the 95% paired compound-level bootstrap interval on the MAE
   difference (MASS FLEX − structure) **above zero**, and
2. relative MAE reduction vs MASS FLEX **≥ 5%** — the pre-registered minimum
   effect size, declared before any result was seen.

**Fail ⇒ no claim of meaningful structural information beyond mass.** Proceed
directly to K5 interpretation.

### K5
> Do molecular descriptors explain variation beyond precursor mass?

Adjudicated on five inputs jointly: the MASS FLEX comparison; the mass-block
ablation; the correlated-block ablation; the descriptor-driven between-compound
variance share (master plan threshold **≥ 0.20**); and the denominator-coupling
audit.

**Fires (structure explains nothing beyond mass) if:** variance share < 0.20,
**or** removing the mass block destroys the structure model's advantage over
B1.

### K8
Evaluated if mixture identity predicts trajectory shape at a level comparable to
the descriptor effect.

## 21. Denominator-coupling audit

Because precursor mass appears in mu's definition, `MASS_COUPLING_AUDIT.md`
determines analytically and with a minimal deterministic diagnostic whether the
observed mass association can arise mechanically from the normalization. Regimes:
(a) purely fractional fragmentation; (b) fragmentation with an absolute
fragment-mass floor; (c) a realistic blend. Each reports the rho(mu, mass) it
manufactures with fractional behaviour held constant, compared against the
observed −0.68.

**Mechanically induced mass dependence is not treated as molecular-structure
discovery.** This is a Phase 2 response-variable audit, not the Phase 3
synthetic discovery system.

## 22. Exact Phase 2 decision rule

`PHASE2_DECISION.md` begins with exactly one of `GO TO PHASE 3`,
`RESTRICT AND GO TO PHASE 3`, `STOP BEFORE PHASE 3`,
`INCONCLUSIVE DUE TO BLOCKER`.

| Condition | Verdict |
|---|---|
| Any negative control above its pre-registered null threshold, unexplained | **INCONCLUSIVE DUE TO BLOCKER** |
| K4A fails under S2 | **STOP BEFORE PHASE 3** |
| K4A passes, K4B fails, **and** K5 fires | **STOP BEFORE PHASE 3** |
| K4A passes, K4B fails, K5 does not fire | **RESTRICT AND GO TO PHASE 3**, with the restriction that no claim beyond mass is licensed |
| K4A and K4B pass, K5 does not fire, one or more secondary splits or the raw-branch check disagree | **RESTRICT AND GO TO PHASE 3** |
| K4A and K4B pass, K5 does not fire, S1/S2/S3 and raw-branch agree | **GO TO PHASE 3** |

Phase 3 is **not** authorized merely because the Phase 2 software works.
Per `MASTER_PLAN_CLARIFICATIONS` C1, Phase 2 authorizes **Phase 3 only** — never
Phase 4.

## 23. Claims-ladder discipline

Feature importance is not mechanism. Permutation importance is not causation. A
fingerprint improving prediction does not establish a chemical law. A descriptor
association does not establish physical explanation. A flexible model beating a
baseline does not constitute discovery. A statistically significant difference
need not be scientifically meaningful.

`PHASE2_DECISION.md` assigns the highest **defensible** rung from master plan
§23 and states why it is not higher.

---

## Environment

Python 3.13.12; numpy 2.5.2, pandas 3.0.5, scipy 1.18.0, pyarrow 25.0.1,
rdkit 2026.03.5, scikit-learn 1.9.0, statsmodels 0.14.6. Pinned in
`requirements.lock.txt`. Global seed **20260811**.
