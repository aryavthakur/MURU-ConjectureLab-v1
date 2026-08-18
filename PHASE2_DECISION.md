# PHASE2_DECISION.md

# RESTRICT AND GO TO PHASE 3

Phase 2 of MURU ConjectureLab v1: representation, hierarchical baselines,
structural generalization, and the flexible predictive benchmark.

Pre-registration `PREREGISTRATION.md`, sha256
`4cfc623361a62e64f4c5a8720c3ccf3ffea6ed2b1ed86f53b7154e5acb6e6d17`,
committed `ddcdb8de1b69480178495bc0ec89e7fdce7a6dda` **before** any model
in this document was executed. The verdict below is computed from the
decision rule in that file, not chosen after the fact.

Per `MASTER_PLAN_CLARIFICATIONS.md` C1, Phase 2 authorizes **Phase 3
only** — never Phase 4.

---

## The scientific question

> Does molecular structure predict the collision-energy trajectory of mu
> for unseen chemistry beyond what can already be explained by collision
> energy and precursor mass?

---

## Adjudication

| Gate | Result |
|---|---|
| **K4A** — structure-aware model beats B1 on S2 | **PASS** |
| **K4B** — structure-aware model beats MASS FLEX by ≥ 5% | **PASS** |
| **K5** — structure explains nothing beyond mass | **does not fire** |
| **K8** — mixture identity confounds | **does not fire** |
| Negative controls | **NC7_retention_time FIRES (explained)** |

## Design and sample sizes

| Item | Value |
|---|---|
| Primary split | **S2**, Bemis-Murcko scaffold-disjoint |
| Development corpus | **439 compounds / 2610 rows** |
| Sealed confirmation set | **110 compounds (20.04%)**, NOT opened |
| Confirmation sha256 | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` |
| Tier A | 12 descriptors |
| Tier B | 718 features |
| Bootstrap | 2000 resamples, molecule/scaffold unit |

## Performance on the primary split (S2)

| Model | MAE (compound) | MAE (scaffold) | 95% CI (scaffold) | grouped R² |
|---|---|---|---|---|
| `B0_global_mean` | **0.20269** | 0.21122 | [0.20421, 0.21821] | -0.0027 |
| `B1_per_energy_mean` | **0.15468** | 0.15482 | [0.14651, 0.16310] | 0.3713 |
| `B2_MASS_SIMPLE` | **0.12959** | 0.13153 | [0.12416, 0.13954] | 0.5316 |
| `MASS_FLEX` | **0.12548** | 0.12823 | [0.12030, 0.13641] | 0.5578 |
| `TIER_A` | **0.11227** | 0.11448 | [0.10791, 0.12174] | 0.6489 |
| `TIER_A_no_mass` | **0.11781** | 0.11665 | [0.11004, 0.12348] | 0.6127 |
| `TIER_A_mass_only` | **0.11831** | 0.11986 | [0.11297, 0.12691] | 0.6119 |
| `FLEX_BENCHMARK` | **0.10036** | 0.10036 | [0.09385, 0.10727] | 0.6899 |
| `FLEX_BENCHMARK_no_mass` | **0.10322** | 0.10256 | [0.09545, 0.10978] | 0.6637 |

### Paired differences that decide the phase

| Comparison | ΔMAE | 95% CI (scaffold) | Relative |
|---|---|---|---|
| FLEX_BENCHMARK vs B1_per_energy_mean | -0.05432 | [-0.06349, -0.04515] | +35.12% |
| FLEX_BENCHMARK vs B2_MASS_SIMPLE | -0.02923 | [-0.03812, -0.02380] | +22.56% |
| FLEX_BENCHMARK vs MASS_FLEX | -0.02513 | [-0.03500, -0.02003] | +20.02% |
| MASS_FLEX vs B1_per_energy_mean | -0.02919 | [-0.03563, -0.01800] | +18.87% |
| TIER_A_no_mass vs B1_per_energy_mean | -0.03686 | [-0.04693, -0.02948] | +23.83% |
| FLEX_BENCHMARK_no_mass vs B1_per_energy_mean | -0.05146 | [-0.06175, -0.04296] | +33.27% |

Best structure-aware model on S2: **`FLEX_BENCHMARK`**.

## K4A

*mean MAE reduction vs B1 > 0 and upper bound of the 95% scaffold-level paired interval < 0*

ΔMAE vs B1 = **-0.05432** (+35.12%), 95% scaffold interval [-0.06349, -0.04515], compound interval [-0.06296, -0.04568].

**K4A: PASS.**

## K4B

*paired interval upper bound < 0 AND relative MAE reduction >= 5%*

ΔMAE vs MASS FLEX = **-0.02513** (+20.02%, minimum required 5.0%), 95% scaffold interval [-0.035, -0.02003].

**K4B: PASS.**

## K5

Adjudicated on five inputs jointly, as pre-registered.

**1. Descriptor-driven between-compound variance share.** Cross-validated
R² of Tier A predicting the compound random intercept, scaffold-grouped:
**0.4693** against the master plan's 0.20 threshold (meets = **True**). Without the mass block: **0.4235** (meets = **True**).

**2. Mass-block ablation.** Removing `precursor_mz`, `total_atom_count`
and `rdbe` together:

- Tier A without mass vs B1: ΔMAE -0.03686, CI [-0.04693, -0.02948]
- Flexible benchmark without mass-like features vs B1: ΔMAE -0.05146, CI [-0.06175, -0.04296]
- Structure advantage survives ablation: **True**

**3. Correlated-block ablation.** `TIER_A_mass_only` (the mass block
alone) reaches MAE 0.11831 against the full Tier A model's
0.11227.

**4. Denominator-coupling audit.** `MASS_COUPLING_AUDIT.md` shows that
purely fractional fragmentation manufactures rho = -0.0578 (numerically zero), while proportional
chemistry plus a single absolute 50 Da low-mass cutoff manufactures rho = **-0.4791** with **no chemistry at all** — the same sign
and a magnitude comparable to the observed -0.6759. On the real data the
high-energy association sits in the fragment term (rho(phi, mass) = -0.6735)
rather than survival yield (rho(SY, mass) = -0.5021), which is the signature
mechanical coupling predicts.

This is a **sensitivity and mechanistic-coupling diagnostic, not an
identification result.** It does not establish what fraction of the
observed association is artifactual, and this document makes no such
claim: the diagnostic is stipulated rather than fitted, and no
coupling-free counterfactual of this corpus exists. Against a purely
mechanical reading, the observed association *grows* with energy
(-0.0913 to -0.6759) while the diagnostic's is roughly flat, so
the coupling alone does not reproduce the observed energy dependence.
What it does establish is that mass dependence of mu is not, by itself,
evidence of chemistry.

**5. Variance decomposition.** Energy accounts for 38.0% of Var(mu), compound identity 50.7%, residual 8.8%.

**K5: does not fire.**

## K8 — mixture confounding

Mixture identity added to MASS FLEX changes MAE by **+0.00159** (CI [-0.00095, 0.00264]), against a structure gain of -0.01322.

**K8 fires: False.**

## Negative controls

| Control | Family | Observed | Null p95 | Fires |
|---|---|---|---|---|
| `NC1_energy_shuffle_within_compound` | destruction | +0.04257 | -0.015274 | **False** |
| `NC2_descriptor_shuffle` | destruction | +0.04257 | -0.000229 | **False** |
| `NC3_trajectory_shuffle` | destruction | +0.04257 | +0.000953 | **False** |
| `NC4_sham_descriptors` | nuisance | -0.00078 | +0.000507 | **False** |
| `NC6_mixture_identity` | nuisance | -0.00038 | +0.000444 | **False** |
| `NC7_retention_time` | nuisance | +0.01006 | +0.000210 | **True** |

CONTROL FIRES: NC7_retention_time -- BLOCKER until explained.

### NC7 fired, and this is its explanation

Retention time predicts trajectory shape above its permutation null
(observed +0.01006 against a null 95th percentile of +0.000210; 0 of 200 permutation replicates reached the observed value, giving a finite-sample corrected empirical p = 0.00498 = (b+1)/(B+1)). Phase 1 anticipated this: `CONFOUNDERS.md` finding 4 recorded |rho| up to 0.36 between RT and
mu and left the resolution to NC7.

The discriminating question is whether RT carries information
**independent of structure**, or is a **structure surrogate** — RT
tracks lipophilicity, which is itself a structural property.

| Model | Improvement over B1 |
|---|---|
| Retention time alone | +0.01006 |
| Tier A alone | +0.04257 |
| Tier A + retention time | +0.04354 |

RT alone recovers 23.6% of the structural effect, but adding
it to Tier A gains only **+0.00097** — 2.3% of the Tier A effect, against the 10% limit.

RT therefore carries predictive signal by itself but adds little
incremental predictive information beyond Tier A descriptors, which is
consistent with it acting **primarily as a structure-associated
surrogate in this dataset**. This is an observational association, not
an identification result: **independent confounding cannot be
completely excluded**, since a small incremental gain is also
compatible with a confounder largely collinear with the descriptors.

**Status: explained sufficiently not to block, but restricting.**
Co-elution and matrix effects cannot be separated from lipophilicity
with these data, so no mechanistic reading of the structural effect
may lean on RT-correlated descriptors.

## Preprocessing sensitivity

Matched raw subset: **39 compounds** (7.1% of the development corpus). rho(mu, mass) has the
same sign at every energy across branches: **True**, largest absolute difference 0.0784.

This is **subset preprocessing robustness, not full-corpus independent
raw replication**, and is not extrapolated beyond the 39 compounds
measured.

## Negative mode

349 compounds, S2 only. K4A pass = **True**, K4B pass = **False**.

Negative-mode repeatability remains **UNKNOWN**; no claim requiring it is
made.

## Model adequacy findings

The master plan's §9.2 formulation was **not** adequate and was replaced
on measured evidence before any model was fitted:

- mu reaches **1.0000008** with 7 rows above 1, so the logit link and a Beta likelihood
  are undefined (`DEVIATIONS.md` D7). Modelled on the natural scale.
- A two-parameter linear energy term leaves 70% of trajectories below
  R² 0.9 (`DEVIATIONS.md` D8). Energy is treated nonparametrically.
- PyMC was deliberately not used; the decomposition is a `statsmodels`
  mixed model with bootstrap intervals (`DEVIATIONS.md` D11).

## Highest defensible claims-ladder rung

# L3

Structure explains between-compound variation beyond mass on scaffold-disjoint holdouts.

Interpretation discipline, restated because it constrains what the above
means: feature importance is not mechanism, permutation importance is not
causation, a fingerprint improving prediction does not establish a
chemical law, and a flexible model beating a baseline is not discovery.
Phase 2 establishes whether reproducible structural predictive information
exists. It does not establish why.

## Verdict

# RESTRICT AND GO TO PHASE 3

Phase 3 is **authorized subject to the restrictions below**, which are
binding rather than advisory:

1. **The denominator-coupling finding is binding.** A mass association of the observed sign and comparable magnitude **can** be generated by mu's normalization plus an absolute low-mass cutoff, with no chemistry. This is a sensitivity result, not an identification result: it does not establish what fraction of the observed association is artifactual, and no such fraction is claimed. Phase 3's synthetic generator must nonetheless include the coupling mechanism, or it will manufacture recoverable 'laws' that are normalization artifacts.

2. **NC7 fired and is explained, but it restricts.** Retention time predicts trajectory shape above its permutation null, though it adds only +0.00097 (2.3% of the Tier A effect) on top of structure — consistent with RT acting primarily as a structure-associated surrogate in this dataset. Independent confounding cannot be completely excluded: co-elution and matrix effects cannot be separated from lipophilicity with these data, so no mechanistic reading may lean on RT-correlated descriptors.

3. **Raw-branch evidence covers 39 compounds only.** No full-corpus preprocessing-invariance claim is available.

4. **The structure-beyond-mass result does NOT replicate in negative mode.** Negative-mode K4A passes, but K4B gives only +1.93% against the 5% minimum, with a scaffold interval of [-0.01572, 0.00038] that spans zero. Any Phase 3 claim is restricted to positive-mode chemistry until this is resolved.

5. **Negative-mode repeatability remains UNKNOWN.** No noise-referenced negative-mode claim may be made.

6. Phase 2 authorizes **Phase 3 only**. Phase 4 requires Phase 3's own decision (`MASTER_PLAN_CLARIFICATIONS.md` C1).

## What Phase 2 did not do

No Phase 3 work. No symbolic regression. PySR not installed. No synthetic
discovery engine. The sealed confirmation set was not opened.

