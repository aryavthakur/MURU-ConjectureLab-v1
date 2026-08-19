# S16: Blind re-derivation of the calibration-surface composition rule

**Defect being closed:** S16. The population composition rule for the calibration
surface was originally selected inside a document that also carried the Held-out
G2 outcome distribution `pi_0`. The rule may be correct, but its provenance is
contaminated: it cannot be shown to have been chosen independently of the target
it is compared against. This document re-derives the rule from design sources
only.

**Method:** derive the composition from the frozen registry, the frozen
generator, and the frozen contracts alone. No outcome, no stage count, no
`first_loss_stage`, no attribution, no `pi_0` was consulted.

---

## 0. DECLARATION OF SOURCES OPENED

Every file opened during this derivation, in the order opened. A reviewer should
check that no outcome-bearing artifact appears in this list.

| # | Path | Extent read |
|---|---|---|
| 1 | `src/muru/paper_benchmark/registry.py` | whole file (225 lines) |
| 2 | `src/muru/paper_benchmark/generator.py` | whole file (290 lines) |
| 3 | `src/muru/paper_benchmark/calibration_contract.py` | whole file (349 lines) |
| 4 | `src/muru/paper_benchmark/g2_contract.py` | lines 1–140 only (definitions, taxonomy, grammar) |
| 5 | `src/muru/paper_benchmark/heldout_endpoint_populations.py` | lines 1–60 (module docstring + population dataclass) |
| 6 | `src/muru/v2_calibration/e2_worlds.py` | lines 1–80 and 192–270, plus a grep of symbol-definition lines |
| 7 | `MURU_PAPER_BENCHMARK_PROTOCOL.md` | whole file (43 lines) |
| 8 | `MURU_PAPER_BENCHMARK_CASE_FAMILIES.md` | whole file (18 lines) |
| 9 | `v2_design_reference/DESIGN_PROVENANCE.md` | whole file (23 lines) |
| 10 | `v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` | **§2.2 (L55–64), §2.4 (L96–121), §2.5 (L122–137), §2.8 (L171–182) ONLY**, plus the file's heading list |
| 11 | `v2_design_reference/MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md` | lines 1–120 |
| 12 | `git log --oneline` for items 1, 2, 3, 6, 10 | commit subject lines only |

**Files explicitly NOT opened** (the prohibited set, verified by absence from the
list above): everything under `audit/e2b_definitive_cloud_adjudication_20260818/`;
everything under `audit/muru_v2_reentry_20260819/` (this document is written into
that directory but nothing in it was read); `v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv`;
`v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.{md,json}`; `results/e2/**`;
`results/e2b_*/**`; `E3_RESULTS.json`; any E0/E1/E3 result artifact. Sections
2.1, 2.3, 2.6, 2.7, 2.9, 2.11 and the PE table of the Pareto study design were
not read.

**Screening procedure.** Before opening items 7–11 each file was scanned with a
count-only grep (`grep -c`, output = an integer, no content) for the markers
`first_loss_stage`, `pi_0`, `attribution`, `0.09722`, `0.38194`, `0.49306`,
`0.02778`, `stage_[a-e]`, `observed rate`, `G2 outcome`. Every file returned 0.
The same count-only screen was applied to items 5 and 6.

### 0.1 Incidental exposures, disclosed

Five things were seen that are adjacent to outcomes. None is an outcome, and
none entered the derivation. They are disclosed so the reviewer can judge for
themselves rather than take my word for it.

1. **Heading text of forbidden sections.** Listing the Pareto document's headings
   to locate the permitted line ranges necessarily rendered the titles of the
   forbidden ones, including `### 2.3 Two populations, two roles, one of them
   decision-inadmissible` and `### 2.11 What each outcome supports`. I read the
   headings, not the sections. §2.3's title is suggestive of the very conclusion
   this document reaches; I note explicitly that I reached that conclusion from
   the registry arithmetic in §1 and §6 below, and that a title asserting "one of them
   is decision-inadmissible" does not say *which* one or *why*. The derivation
   below stands on its own numbers.
2. **§2.5 of the Pareto design** refers to "the sealed `selection_count` and
   cross-seed representative for all 144 cases". 144 is a registry-derived
   denominator (re-derived independently in §1 below); `selection_count` is
   named but no value is given.
3. **§3 of the balanced-sample design** states E2's purpose as "locating which of
   A/B/C+D dominates". This names the stage categories but supplies no counts, no
   proportions and no ordering. It is a statement of estimand, not of estimate.
   §4 of the same document reports world-ID completion counts (127/159/191/228/259
   reusable worlds); these are execution-progress counts over world identifiers,
   which that document itself states are read "world-IDs only ... never outcomes".
4. **The task brief itself quoted `pi_0`** (A .09722 / B .38194 / C+D .49306 /
   E .02778). This was supplied to me, not retrieved by me. It is used nowhere in
   this document's reasoning. To be concrete about what that would have looked
   like: those four figures have a common denominator of 144, and a derivation
   that reasoned backwards from that fact would be contaminated. §1 derives 144
   from `endpoint_applies_to_variant` over the registry, before and independently
   of any consideration of `pi_0`, and every subsequent count in this document is
   produced by the script in §1 from the registry and generator alone.

5. **`git status --short` on the output directory**, run after writing this file to
   confirm it was created, listed three untracked checkpoint *filenames* under
   `audit/muru_v2_reentry_20260819/_ckpt_dinst/` (e.g.
   `V2C_E2_mass_exponential_descriptor_c_low_n_default_r006__14_13.json`). These
   are E2a world identifiers — family, regime, noise, replicate — i.e. the exact
   factorial coordinates already derived in §6 from `e2_worlds.py`. No file under
   that directory was opened and no content was read. World identifiers are the
   same class of information the balanced-sample design itself treats as
   non-outcome ("world-IDs only ... never outcomes").

**Blindness statement.** To the best of my knowledge and the record above, this
derivation is blind. No outcome-bearing file was opened at any point in this
session.

---

## 1. The Held-out G2 population, enumerated structurally

G2 is the `family_recovery` endpoint (`registry.ENDPOINTS["family_recovery"]`,
role `primary_symbolic`, "G2 family recovery").

The population is built exactly as `heldout_endpoint_populations.py` mandates —
from `endpoint_applies_to_variant`, never from `len(case_ids)`:

```
for family in CASE_FAMILIES:
    for replicate in range(family.partition_counts["held_out"]):   # = 12 for every family
        variant = family.variant_for_replicate(replicate)
        if endpoint_applies_to_variant("family_recovery", variant): include
```

`PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3}` is a
**single shared mapping** referenced by all twenty `FamilySpec`s. Every family
receives exactly 12 held-out replicates. This matters for §2 and is easy to
overlook: the Held-out condition mix is not an artifact of sampling, it is a
deliberately *equal* allocation declared once in the registry.

### 1.1 Composition by F-code

Twelve of twenty families carry `family_recovery` (it is a member of
`SYMBOLIC_ENDPOINTS`). Each contributes 12 replicates.

| F-code | Family name | Declared scientific question | `generative_kind` | n |
|---|---|---|---|---|
| F01 | noiseless scalar collapse | recover unambiguous collapse | `scalar_noiseless` | 12 |
| F02 | moderate-noise scalar collapse | recover under moderate noise | `scalar_moderate` | 12 |
| F03 | stronger realistic noise | characterize graceful degradation | `scalar_strong` | 12 |
| F04 | missing-one-energy | recover with declared missingness | `missing_one_energy` | 12 |
| F05 | boundary-scale | detect profile boundaries | `boundary_scale` | 12 |
| F08 | simple descriptor law | recover a monotone descriptor law | `simple_descriptor` | 12 |
| F09 | nonlinear descriptor law | recognize saturation | `nonlinear_descriptor` | 12 |
| F10 | interaction law | recognize interpretable interaction | `interaction` | 12 |
| F11 | irrelevant distractors | exclude independent nuisance variables | `irrelevant_distractors` | 12 |
| F12 | correlated distractors | separate support from correlation | `correlated_distractors` | 12 |
| F17 | equivalent symbolic forms | canonicalize equivalent laws | `equivalent_forms` | 12 |
| F18 | algebraically difficult, predictively simple | separate prediction from exact algebra | `difficult_algebra` | 12 |

**Total: 144.** Cross-checked against `registry.endpoint_case_count("family_recovery")`
= 144.

**Excluded, and why (structural, not empirical):**

- **F06** (`no_scalar`), **F13/F14/F15** (M1/M2/M3 violations), **F16**
  (combined violation): `endpoint_names = {m1_sensitivity, ...}` only. No symbolic
  truth (`symbolic_truth_kind = "none"`). Not in any symbolic denominator.
- **F07** (`mass_only`): carries `parameter_recovery`, `false_extra_structure`,
  `principal_structural_safety` — but **not** `family_recovery`. Its symbolic
  truth kind is `mass_only`, not `defined`.
- **F19** (target-specific nulls, variants F19A/B/C) and **F20** (adversarial
  worlds, F20A/B/C): endpoint sets are `false_null_structure` /
  `false_adversarial_structure` / `principal_structural_safety`. No variant of
  either carries `family_recovery`.

This exclusion structure is the same one `heldout_endpoint_populations.py`'s
docstring records as previously mis-handled ("F07 and F19 contributed 16 of the 23
reported G2 'successes' despite carrying no `family_recovery` endpoint at all").
It is re-derived here from the registry, not taken from that note.

### 1.2 Composition by truth family

Mapping each `generative_kind` through `generator._law` to its
`mathematical_family` (the same taxonomy frozen in `g2_contract.TRUTH_FAMILIES`):

| Truth family | n | share |
|---|---|---|
| `mass_affine_descriptor` | 108 | 75.00% |
| `mass_saturating_descriptor` | 12 | 8.33% |
| `mass_interaction` | 12 | 8.33% |
| `mass_exponential_descriptor` | 12 | 8.33% |
| `mass_power` | **0** | **0.00%** |

`mass_power` is a member of the frozen five-family taxonomy but is generated
**only** by `generative_kind ∈ {mass_only, mass_preserving_null}` — i.e. only by
F07 and F19B, neither of which carries `family_recovery`. **The Held-out G2
population contains zero `mass_power` cases.** This is a structural fact from the
registry, independent of any result.

### 1.3 Composition by generative nuisance factors

From `generator._response_matrix`:
`noise_sd = {"scalar_noiseless": 0.0, "scalar_moderate": 0.0295, "scalar_strong": 0.06}.get(kind, 0.02)`,
and missingness is applied only for `kind == "missing_one_energy"`
(`{"mechanism": "one_energy_per_compound", "rate": 1/6}`).

| noise_sd | n | | missingness | n |
|---|---|---|---|---|
| 0.0 | 12 | | none | 132 |
| 0.02 | 108 | | `one_energy_per_compound` | 12 |
| 0.0295 | 12 | | | |
| 0.06 | 12 | | | |

Joint (truth family × noise × missingness) — **eight** occupied cells:

| truth family | noise_sd | missingness | n |
|---|---|---|---|
| `mass_affine_descriptor` | 0.0 | none | 12 |
| `mass_affine_descriptor` | 0.02 | none | 60 |
| `mass_affine_descriptor` | 0.02 | one_energy_per_compound | 12 |
| `mass_affine_descriptor` | 0.0295 | none | 12 |
| `mass_affine_descriptor` | 0.06 | none | 12 |
| `mass_saturating_descriptor` | 0.02 | none | 12 |
| `mass_interaction` | 0.02 | none | 12 |
| `mass_exponential_descriptor` | 0.02 | none | 12 |

### 1.4 The decisive structural observation: the benchmark is OFAT, not factorial

Two facts follow directly from the table above and settle most of what comes
after.

**(i) The generative factors are confounded with F-code by construction.** Each
eligible F-code fixes exactly one combination of (law, noise, missingness). The
benchmark never crosses them. There is no held-out case with an interaction law
at noise 0.06, none with a saturating law and missing energies, none with an
exponential law at noise 0.0. The design is **one-factor-at-a-time off a common
baseline** (`mass_affine_descriptor`, noise 0.02, no missingness), which is the
60-case block in the table. Of the 15 possible (5 truth families × 3 of the noise
levels) combinations, only 6 are instantiated at all.

**(ii) Five F-codes are generatively identical.** F05, F08, F11, F12 and F17 all
route to the same `_law` branch (`mass_affine_descriptor`), take no special
branch in `_response_matrix`, take the default `noise_sd = 0.02`, and apply no
missingness. The `distractor` and `correlated_distractor` covariates are present
in **every** case's compound frame regardless of family, so F11 and F12 do not
differ in their data-generating process from F08 either. These five families
differ in their **declared scientific purpose** and in their **endpoint set**
(F05 adds `boundary_hit`; F01/F08/F09/F10/F17 add `exact_algebra`), not in their
generative distribution. This is important for §5.

---

## 2. The design-level principle that determines a calibration population

The question posed is: *what population should a calibration surface have, if its
purpose is to support inference about the same experimental regime as the Held-out
G2 partition?*

The phrase "support inference about" fixes the estimand. A surface that supports
inference about Held-out G2 is one whose per-unit results are aggregated into a
statement about the 144-case Held-out G2 population — a rate, a proportion, a
composition. Whether such a statement is valid is a **design-based sampling**
question, and design-based sampling theory gives a sharp answer with two
conditions:

> For a finite target population partitioned into strata *h* with known target
> weights *W_h*, an estimator built on a calibration population with weights *w_h*
> is unbiased for the target quantity iff (a) *w_h = W_h* for all *h*, or the
> per-stratum estimates are re-weighted to *W_h*; and (b) every stratum with
> *W_h > 0* has *w_h > 0*.

Condition (b) is not repairable by analysis. A stratum with target weight but no
calibration units is simply not estimable; no post-stratification, no raking, no
re-weighting recovers it. Condition (a) is repairable if and only if the strata
are identifiable and the weights are known.

Weighing the four candidate principles against this:

**(a) Match the target partition's declared condition mix exactly.**
Satisfies (a) and (b) trivially and by construction. Requires zero analyst
choices: the strata are the F-codes, the weights come from
`PARTITION_CASE_COUNTS`, and both are computable from the registry by a function
that already exists (`endpoint_applies_to_variant`). Fully checkable: a reviewer
re-runs the loop in §1 and compares.

**(b) Balanced factorial over generative factors.**
Fails (b) outright against this target, and fails it in the unrepairable
direction — see §6. Also requires the analyst to nominate a factor set and a level
grid, neither of which the registry declares. The discretion is not hypothetical:
the E2a grid invented a "coefficient regime" factor that does not exist in the
benchmark at all, chose 3 of the 4 declared noise levels, and dropped missingness
entirely. Three unforced analyst choices, each of which changes the answer.

**(c) Match on truth family only.**
Collapses 9 of the 12 eligible F-codes into a single stratum and discards noise,
missingness and the distractor/equivalence structure. Under this rule F01
(noiseless) and F03 (noise 0.06) are interchangeable units. It also leaves
undetermined whether `mass_power` is in the population — the taxonomy has five
families, the target has four, and "match on truth family" does not by itself say
whether to use the taxonomy's support or the target's. Maximal information loss
for no reduction in discretion.

**(d) Stratify by declared experimental purpose.**
The registry's unit of declared experimental purpose is exactly the F-code:
`FamilySpec.scientific_question` is one string per family, and the F-code is what
determines the endpoint set and the expected behavior. So (d) reduces to: one
stratum per eligible F-code. And since `PARTITION_CASE_COUNTS` allocates 12
replicates to *every* family identically, **equal allocation across purpose-strata
is numerically identical to the target's condition mix**.

**(a) and (d) coincide.** This is the derivation's central result and it is worth
stating plainly, because it is what makes the answer non-arbitrary. Mirroring the
Held-out mix is not "chasing an observed distribution" — the Held-out mix *is* the
design's own declared, deliberately uniform, purpose-stratified allocation. The
two principles that survive scrutiny turn out to be the same principle, arrived at
from opposite directions: one from estimator validity, one from respecting the
design's declared structure.

**Selection under the stated criteria:**

| Criterion | (a)/(d) | (b) | (c) |
|---|---|---|---|
| Supports inference about the *same* regime | yes, by construction | no — support violated both ways | partially; loses 3 factors |
| Minimizes analyst discretion | zero free parameters | 3+ free choices | 1 free choice, large loss |
| Checkable from the registry alone | yes, one function call | no — grid is not in the registry | yes, but underdetermined |

**Principle adopted: the calibration population must be purpose-stratified by
F-code over the endpoint-eligible families, with allocation proportional to the
registry's declared held-out allocation — which, the allocation being uniform,
means equal replicates per eligible F-code.**

### 2.1 An internal precedent, and the limit of this principle

`calibration_contract.py` (Amendment A3.1) already contains a calibration
population derived this way, and it is instructive that it does **not** match the
held-out mix. Its 100 structural-null worlds are allocated 34/33/33 across three
destruction constructions, and it **excludes** `within_compound_energy_permutation`
with an explicit reason: *"it preserves compound mean level, the scalar quantity
being estimated."*

That exclusion is justified against the **estimand**, not against convenience.
This is the same principle operating in a different regime: the A3.1 surface's job
is to furnish a null reference distribution, so its composition is dictated by what
must be destroyed relative to the estimand; a surface whose job is to support a
population-level inference about Held-out G2 has its composition dictated by what
must be *preserved* — the target's composition.

Consequently: **"calibration surface" is ambiguous in this repository, and the
rule derived here applies to the inferential sense only.** For an A3.1-style null
threshold surface, composition-matching is the wrong rule and A3.1's own
estimand-based derivation is the right one. S16 concerns the surface that carries
population-level statements about the Held-out G2 regime, so the rule below is the
one that binds it.

---

## 3. The concrete derived composition

**Strata.** The 12 F-codes for which
`endpoint_applies_to_variant("family_recovery", variant_for_replicate(r))` holds:
F01, F02, F03, F04, F05, F08, F09, F10, F11, F12, F17, F18.

**Allocation.** Equal, *r* replicates per stratum. Total *n* = 12·*r*.

**Per-stratum generative settings.** Each stratum reproduces its F-code's declared
condition exactly, as `generator.py` defines it:

| Stratum | law branch | noise_sd | missingness |
|---|---|---|---|
| F01 | `mass_affine_descriptor` | 0.0 | none |
| F02 | `mass_affine_descriptor` | **0.0295** | none |
| F03 | `mass_affine_descriptor` | 0.06 | none |
| F04 | `mass_affine_descriptor` | 0.02 | **one_energy_per_compound**, rate 1/6 |
| F05, F08, F11, F12, F17 | `mass_affine_descriptor` | 0.02 | none |
| F09 | `mass_saturating_descriptor` | 0.02 | none |
| F10 | `mass_interaction` | 0.02 | none |
| F18 | `mass_exponential_descriptor` | 0.02 | none |

**Nuisance parameters must be drawn, not gridded.** `generator._law` and
`_response_matrix` draw `scale ~ U(1.1, 1.8)`, `coefficient ~ U(0.25, 0.55)`,
`exponent ~ U(0.45, 0.75)`, `mu_inf ~ U(0.15, 0.30)`, `phi_p ~ U(1.20, 1.70)`
i.i.d. per case. The registry declares these as *draws*, not as factors. A
calibration population that reproduces the regime must draw them from the same
frozen priors. Fixing any of them to a grid replaces a uniform continuum with
point masses and is a departure from the declared design that requires its own
justification.

**Shared structure held at declared values:** 180 compounds, 30 scaffold groups,
scaffold-disjoint 20/5/5-group train/validation/test split, energy grid
(15,30,45,60,75,90), response clip [1e-4, 1−1e-4] — all per `generator.py` and
`MURU_PAPER_BENCHMARK_PROTOCOL.md`.

### 3.1 Deriving the replicate count *r*

**The divisibility constraint.** `FamilySpec.variant_for_replicate` is
`variants[variant_cycle[replicate % len(variant_cycle)]]`. For a family whose
cycle has period *k*, a set of replicates is variant-balanced iff the replicate
indices form a complete residue system mod *k*, which requires *k | r*.

The registry's own choice of 12 is evidently made with this in mind: F19 and F20
have *k* = 3, and 12 ≡ 0 (mod 3) gives exactly 4 cases per variant. 12 is
divisible by 1, 2, 3, 4, 6 and 12, so any variant cycle of those periods is
balanced at the declared allocation. The design applied a divisibility discipline
to its replicate count.

**For this endpoint the constraint does not bind.** All 12 `family_recovery`
families have `variant_cycle = ("BASE",)`, so *k* = 1 and every *r* ∈ {1,…,12} is
variant-balanced. Balance therefore does not pin *r*, and *r* must be fixed by a
second criterion.

**Least-discretionary resolution: *r* = 12, *n* = 144 — the full census of the
frame.** The reasoning is that every *r* < 12 requires the analyst to supply three
things the design does not: a precision threshold, a variance convention, and a
sampling seed. That is not hypothetical either — the balanced-sample design
document had to introduce "overall MOE < 5% at 95% confidence" as an explicitly
acknowledged convention ("stated here explicitly (not assumed) so it can be
disputed on its own terms") plus a worst-case *p* = 0.5 assumption plus a
SHA-256-derived selection seed, purely in order to land on *r* = 6. Each is a
defensible choice and each is a choice. At *r* = 12 the sampling fraction is 1,
the finite-population correction `(N_h − n_h)/(N_h − 1)` is exactly 0, sampling
variance is exactly 0, and no threshold, convention or seed is needed. The frame
has 144 units; it is small enough to enumerate. **When the target frame is finite,
fully enumerated and cheap, the census dominates every sample on both variance and
discretion.**

**Seeds per unit: 30.** `calibration_contract.N_SEEDS_PER_WORLD = 30`, surfaced as
`SEARCH_SETTINGS["seeds_per_world"]`; Pareto §2.5 control 2 holds
`SEEDS_PER_CASE = 30` unchanged. Total search budget: 144 × 30 = **4,320
searches**.

**Identity of the units: fresh worlds, not the held-out cases themselves.** The
registry fixes the *composition*; it does not say whether the calibration units
should be the held-out cases or new draws from the same conditions. Reusing the
held-out cases would make the calibration set and the evaluation set the same data,
which is circular. The least-discretionary resolution is fresh worlds generated
under the same conditions with a disjoint seed namespace — the discipline
`e2_worlds.py::assert_seed_namespace_disjoint` already implements. Composition
mirrors; case identity does not.

### 3.2 The derived rule, stated once

> **S16 composition rule (blind derivation).** A calibration surface intended to
> support population-level inference about Held-out G2 shall be stratified by the
> 12 F-codes admitted by `endpoint_applies_to_variant("family_recovery", ·)` over
> the held-out replicate range, with equal allocation of 12 replicates per
> stratum (n = 144, mirroring `PARTITION_CASE_COUNTS["held_out"]`), each stratum
> reproducing its F-code's declared law, noise level and missingness mechanism
> exactly, all nuisance parameters drawn i.i.d. from their frozen priors rather
> than gridded, at 30 search seeds per unit, on world identifiers drawn from a
> seed namespace disjoint from the benchmark's.

---

## 4. Does this MATCH or DIFFER from "match the Held-out condition mix exactly"?

**It MATCHES. Exactly, and as an identity rather than an approximation.**

The derived rule is *equal allocation across purpose-strata*. The Held-out
condition mix is *equal allocation across F-codes*, because
`PARTITION_CASE_COUNTS` is one shared mapping assigning 12 to every family. The
registry's unit of declared experimental purpose is the F-code. Therefore the two
descriptions denote the same population, unit for unit: 12 F-codes × 12
replicates = 144.

I want to be precise about what has and has not been shown, because this is the
claim S16 exists to test:

- I did **not** derive "mirror the target" as a heuristic and then discover it
  matched. I derived (i) that estimator validity requires *w_h = W_h* with common
  support, and (ii) that purpose-stratification with the registry's declared
  allocation yields that mix. These are independent routes to the same population.
- The rule is therefore **not** contingent on any property of the outcome
  distribution. It would be the same rule if `pi_0` were uniform, degenerate, or
  unknown — as it was to me while deriving it. This is precisely the property S16
  demanded and could not previously demonstrate.
- The contamination in the original provenance was real but, on this evidence,
  **non-load-bearing**: the rule the contaminated document recorded is
  recoverable from `registry.py` + `generator.py` alone, by a procedure with no
  free parameters. S16 is closable as *confirmed by independent re-derivation*
  rather than as *repaired*.

One honest caveat on scope: this matching claim is about the *composition rule*.
It says nothing about whether any other choice recorded in the same contaminated
document is similarly recoverable. S16 as briefed concerns the composition rule,
and that is the extent of what this document closes.

---

## 5. Where the design under-determines the choice

Four places. Each is recorded with its least-discretionary resolution.

**U1. F05/F08/F11/F12/F17 are generatively identical (§1.4(ii)).** A purist could
describe this block as one condition with 60 replicates rather than five
conditions with 12 each, and the registry does not adjudicate — the five F-codes
have distinct `scientific_question` and `endpoint_names` but an identical
data-generating distribution.
*Resolution:* keep the F-code stratification the registry declares. Stratifying by
F-code is a **refinement** of stratifying by generative condition; under
proportionate allocation a refinement of the strata never changes the estimator's
expectation, so it cannot introduce bias, and it preserves the ability to report
per-purpose rates that the coarser scheme destroys. Refine when in doubt: it costs
nothing and retains information.

**U2. The replicate count *r* is not pinned by any balance constraint** (§3.1),
since all eligible families have variant-cycle period 1.
*Resolution:* *r* = 12, the census. It is the unique value requiring no threshold,
no variance convention and no seed.

**U3. The registry does not say whether calibration units should be the held-out
cases or fresh worlds.**
*Resolution:* fresh worlds, disjoint seed namespace (§3.1). Reuse would be
circular; the project's own `assert_seed_namespace_disjoint` establishes the
convention.

**U4. "Calibration surface" is ambiguous between an inferential reference surface
and an A3.1-style structural-null threshold surface** (§2.1).
*Resolution:* the rule derived here binds the inferential sense — the one the S16
brief describes as "supporting inference about the same experimental regime". For
a null-threshold surface, A3.1's estimand-based derivation governs and
composition-matching would be actively wrong, since a null surface's job is to
destroy the estimand rather than to reproduce its distribution.

A fifth item is worth flagging as *not* under-determined, since it might look it:
whether `mass_power` belongs in the population. It does not, and this is
determined, not discretionary — `mass_power` arises only from F07 and F19B, and
`endpoint_applies_to_variant("family_recovery", ·)` is False for both. The
taxonomy in `g2_contract.TRUTH_FAMILIES` lists five families; the *endpoint's*
population contains four. Reading the taxonomy as the population is a category
error: the taxonomy is the classifier's output space, not the target's support.

---

## 6. Assessment: is a balanced factorial over (family × regime × noise) a defensible calibration population for Held-out-facing inference?

The E2a surface, per Pareto §2.8 and `src/muru/v2_calibration/e2_worlds.py`:
5 truth families × 3 coefficient regimes (`low`/`mid`/`high` = coefficient fixed
at 0.25/0.40/0.55) × 3 noise levels (0.0/0.02/0.06) × 12 replicates = 45 cells ×
12 = **540 worlds**, equally weighted.

Assessed purely as a design question, without reference to any outcome.

### 6.1 Ruling: NOT defensible as a calibration population for this target

Four independent design-level defects, in descending severity. Each is verifiable
from `registry.py`, `generator.py` and `e2_worlds.py` alone.

**D1 — Support violation, unrepairable direction (fatal).** Two Held-out G2
strata lie entirely outside E2a's support:

- **F02**, noise_sd = **0.0295** (12 cases, 8.33%). `NOISE_SD_BY_LEVEL` is
  `{0.0, 0.02, 0.06}`; `e2_worlds.py`'s own comment states these are "the three
  `noise_sd` values already literal in `generator._response_matrix`'s own dict
  **that are not `scalar_moderate`'s family-specific 0.0295**". The omission is
  documented and deliberate.
- **F04**, `missingness = one_energy_per_compound` (12 cases, 8.33%).
  `_response_matrix_v2`'s docstring: "no missingness mechanism is applied".

**24 of 144 held-out G2 cases (16.67%) are in strata with zero E2a units.** No
re-weighting scheme recovers them; the weight needed is finite and the sample
available is empty. Any E2a-based statement about the Held-out G2 population is
silently a statement about 120/144 of it.

**D2 — A 20% stratum with exactly zero target weight.** E2a allocates
`mass_power` 9 of its 45 cells — 108 of 540 worlds, 20% of the surface. The
Held-out G2 population contains **zero** `mass_power` cases (§1.2). Under equal
cell weighting, any pooled E2a proportion is an estimate for a population that is
20% composed of a condition the target does not contain. This is bias by
construction, present before a single search runs.

**D3 — Crossing factors the benchmark deliberately does not cross.** The benchmark
is OFAT off a common baseline (§1.4(i)). Of E2a's 15 family × noise combinations,
only **6 have nonzero target weight**; the other 9 are counterfactual worlds no
held-out case instantiates — saturating/interaction/exponential laws at noise 0.0
or 0.06, and `mass_power` at all three levels.

> **324 of 540 E2a worlds (60%) sit on strata of exactly zero target measure.**

**D4 — Promoting a nuisance draw to a factor, and gridding it at the extremes.**
"Coefficient regime" **does not exist in the benchmark design.** `generator._law`
draws `coefficient ~ U(0.25, 0.55)` i.i.d. per case; it is a nuisance parameter,
not a declared condition. E2a fixes it at {0.25, 0.40, 0.55} — the support's two
endpoints and its midpoint — and weights them 1/3 each. This replaces a uniform
continuum with three point masses, two of which are at the boundary, so the
implied distribution of `coefficient` is not merely discretized but
extremum-loaded relative to the target. Unlike D1–D3 this is repairable in
principle by re-weighting, but the weights would have to be invented, since the
target's coefficient distribution is continuous and the surface's is atomic.

### 6.2 What this does *not* establish, stated fairly

The brief correctly anticipates that if balanced-factorial were defensible on
design grounds, the premise of a mis-composed E2a surface would weaken. It does
not weaken — but the honest form of the finding is narrower than "E2a was badly
designed", and I do not think the record supports the broader claim.

**A balanced factorial is the *right* design for a different estimand.** For a
mechanistic or explanatory question — *does coefficient magnitude or noise drive
structural loss, and do they interact?* — equal allocation across a crossed grid is
exactly correct. It maximizes per-cell precision, keeps the factors orthogonal so
main effects are separable, and deliberately does **not** want the target's
unbalanced weights, since matching them would starve the sparse cells and confound
the very contrasts being estimated. Cell D3 counts as a defect only against a
Held-out-facing estimand; against a mechanistic estimand, deliberately populating
combinations the benchmark leaves empty is the entire point of the design.
Similarly, including `mass_power` is a defect for D2's purpose and a virtue for a
mechanistic one — it is the taxonomy's only non-descriptor family, and a factorial
that omitted it could not separate descriptor-driven effects from mass-driven ones.

The defect is therefore **a role mismatch, not a design error**: E2a is a
well-constructed mechanistic surface, and `e2_worlds.py` is careful work (it
transcribes the frozen generator line-for-line, preserves the RNG call order so
the streams consume identically, and proves it with an executable identity check
rather than by inspection). What it is not, and cannot be made into by
re-weighting, is a population from which Held-out G2 proportions can be estimated.

**Conclusion.** Balanced factorial over (family × regime × noise) is *defensible
as a mechanistic surface* and *indefensible as an inferential surface facing
Held-out G2*. The premise that the earlier surface was mis-composed **for
calibration purposes stands**, confirmed here without reference to any outcome.
The stronger claim that the surface was badly designed does not stand and should
not be made.

---

## 7. Provenance of the sources used

| Source | Commit | Subject |
|---|---|---|
| `registry.py` | `ea7b990` | Add frozen paper benchmark registry |
| `generator.py` | `80a7803` | Amendment A2.1: bump GENERATOR_VERSION (A2 F16 behavior change) |
| `calibration_contract.py` | `c8938e8` | Amendment A3.1: G2/G3 structural endpoints and calibration contract |
| `e2_worlds.py` | `c9d08db` | E2a: fresh-world builder, full-front search capture, ... |
| `MURU_V2_G2_PARETO_STUDY_DESIGN.md` | `ae002d2` | E0 preregistration: executable protocol and design reference, **before any world exists** |

The registry and generator — the two sources that carry the entire derivation —
were frozen before any v2 experiment existed. The Pareto design document is
prospectively pre-registered by its own commit subject. Nothing in the chain above
post-dates an outcome.

## 8. Reproduction

The composition tables in §1 are produced by iterating `CASE_FAMILIES`, calling
`variant_for_replicate(r)` for `r ∈ [0, 12)`, filtering on
`endpoint_applies_to_variant("family_recovery", variant)`, and mapping
`generative_kind` through the `_law` dispatch and the `noise_sd` dict transcribed
from `generator._response_matrix`. The total is cross-checked against
`registry.endpoint_case_count("family_recovery") == 144`. No file outside the
declaration in §0 is required to reproduce any number in this document.
