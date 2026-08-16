# MURU v2 Experiment E0: executable protocol

**Status: PREREGISTERED, before any world exists.** Nothing below is fit to or
adjusted against any generated or fitted output. This document commits to
every number needed to run E0 and to the exact decision rule before the first
random draw. It binds the three things `MURU_V2_A1_STUDY_DESIGN.md` §2 and
`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` §E0 specify in prose but leave
unexecutable, deriving each from the frozen registry and generator source
alone: (1) the world configuration, (2) the control-arm abort gate, (3) which
of the nine cells the "decoupling" contrast reads.

Authority: `v2_design/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` §E0 (lines
91-133), `v2_design/MURU_V2_A1_STUDY_DESIGN.md` §2 (lines 74-166),
`v2_design/MURU_V2_CAUSAL_DECISION_TREE.md` §A.0 (lines 53-76). All three are
byte-identical imports from commit `befca0d`
(`v2_design/DESIGN_PROVENANCE.md`). Frozen production source read (never
modified): `src/muru/paper_benchmark/generator.py`,
`src/muru/paper_benchmark/adequacy.py`, `src/muru/paper_benchmark/rc5_adequacy.py`,
`src/muru/paper_benchmark/rc5_estimate.py`, `src/muru/paper_benchmark/registry.py`,
`src/muru/discovery/estimate.py` at worktree HEAD `3056c9a`.

---

## 1. World configuration (binds design §2.2's "world configuration")

**Reading, from the registry alone.** `registry.CASE_FAMILIES` has 13
single-variant families whose `m0_adequacy_truth == "M0"`
(F01,F02,F03,F04,F05,F07,F08,F09,F10,F11,F12,F17,F18), each with a distinct
`generative_kind` and each carrying exactly 19 cases (4 development + 12
held-out + 3 challenge) — a 13-way tie by raw case count, so "modal" cannot
mean case-count-per-kind. `generator._law` maps 9 of those 13 kinds
(`scalar_noiseless, scalar_moderate, scalar_strong, missing_one_energy,
boundary_scale, simple_descriptor, irrelevant_distractors,
correlated_distractors, equivalent_forms`) to the **same**
`mathematical_family = "mass_affine_descriptor"` (identical `g` formula:
`scale * sqrt(mass/250) * (1 + coefficient * descriptor)`); the other 4 kinds
each get their own distinct family. `mass_affine_descriptor` is therefore the
modal mathematical family among true-M0 cases (9 x 19 = 171 cases), by a wide
margin over the next-largest (`mass_power`, 2 kinds). This is the "modal v1
true-M0 generative cell."

**Narrowing within it.** Of those 9 kinds, `generator._response_matrix`'s
noise table gives `scalar_noiseless/moderate/strong` a non-default noise SD
(0, 0.0295, 0.06); the other 6 default to 0.02. `missing_one_energy`
additionally introduces missingness. The remaining 5
(`boundary_scale, simple_descriptor, irrelevant_distractors,
correlated_distractors, equivalent_forms`) are functionally identical for E0's
purposes: same `g` formula, same draw ranges, noise SD 0.02, no missingness —
they differ from each other only in registry/downstream metadata (e.g. which
extra covariate columns exist) that plays no role in the `g`/`mu`/adequacy
computation. E0's own world generator therefore implements exactly this one
functional configuration; no further choice among the 5 has any numerical
consequence, so none is made.

**Bound configuration:**

| Parameter | Value | Source |
|---|---|---|
| Compounds | 180 (30 scaffolds x 6) | `generator.N_COMPOUNDS`, `N_SCAFFOLDS` |
| Split | 20/5/5 scaffold groups -> 120 train / 30 validation / 30 test | `generator._synthetic_compounds` |
| Energies | (15, 30, 45, 60, 75, 90) | `registry.ENERGY_GRID` |
| `mass` | `exp(5.55 + 0.25*latent + N(0, 0.18))` | `generator._synthetic_compounds` |
| `descriptor` | `(latent + N(0,0.45) - min) / max` | `generator._synthetic_compounds` |
| `g` | `scale * sqrt(mass/250) * (1 + coefficient*descriptor)`, `scale~U(1.1,1.8)`, `coefficient~U(0.25,0.55)` | `generator._law`, `mass_affine_descriptor` branch |
| `mu_inf` | `U(0.15, 0.30)` | `generator._response_matrix` |
| `phi_p` | `U(1.20, 1.70)` | `generator._response_matrix` |
| `u` | `(E / 45.0) / g` | `generator._response_matrix` (`E_REF=45.0`, `adequacy.E_REF`) |
| `mu` (pre-clip, pre-noise) | `mu_inf + (1 - mu_inf) * exp(-u**phi_p)` | shared M0 branch |
| noise | additive Gaussian, sd 0.02 | default branch of `generator._response_matrix`'s noise table |
| response clip | **the E0 generator factor `C_gen`, varied — see §2** | `generator.py:221`, varied instead of fixed |
| Truth | M0 exactly (no planted M1/M2/M3 deviation anywhere) | design §2.3 control |

## 2. Independent variable and cell identifiers

3 x 3 crossed factors, both applied only as the **ceiling**; the floor stays
fixed at `MU_FLOOR = 1e-4` (`adequacy.MU_FLOOR`) in every cell, matching the
design's naming of only the ceiling as varied in each factor:

| Factor | Level id | Value |
|---|---|---|
| generator response clip `C_gen` | `g1e4` | ceiling `1 - 1e-4` = `0.9999` (v1) |
| | `g1e3` | ceiling `1 - 1e-3` = `0.999` |
| | `gnone` | no clip applied at all |
| fitter admissible ceiling `MU_CEIL` | `c1e4` | `1 - 1e-4` = `0.9999` (v1) |
| | `c1e3` | `1 - 1e-3` = `0.999` |
| | `copen` | `1.0 + 1e-2` = `1.01` |

Cell id = `<C_gen level>_<MU_CEIL level>`, e.g. `g1e4_c1e4`. World id =
`V2C|E0|<cell_id>|r<replicate:03d>`.

**Control arm:** `g1e4_c1e4` (both equal to the v1 constant).

**Decoupling contrast (binds design §2.2/§2.6's undeclared cell choice).**
"When the clip and ceiling are decoupled" is read as: both factors pushed to
their most-relaxed level simultaneously, i.e. the corner cell diagonally
opposite the control arm in the 3x3 grid, `gnone_copen` (generator applies no
clip at all; fitter's ceiling is not binding). This is the only cell in which
the `C_gen == MU_CEIL` coincidence is broken in the strongest possible sense
for both factors at once, matching "the clip AND ceiling are decoupled"
(plural, joint) rather than a single-factor relaxation. `E0's decision
criterion (§4 below) is evaluated on `boundary_limited_rate[g1e4_c1e4] -
boundary_limited_rate[gnone_copen]`.

The full 3x3 factorial (not just the two corner cells) is still generated and
analyzed, because the required analysis separately asks for each factor's
main effect and their interaction (§5), which the decoupling contrast alone
cannot distinguish (a large drop at the corner is consistent with either
factor mattering alone or both mattering jointly).

## 3. Controls

- **True M0 only.** No planted M1/M2/M3 deviation in any of the 540 worlds;
  the generator's `adequacy` output is always `"M0"` by construction (the
  `mass_affine_descriptor` branch never departs from the shared M0 response).
- **Shared randomness.** For each replicate `r` (0..59), the covariate draw
  (`mass`, `descriptor`, scaffold/split), the law draw (`scale`,
  `coefficient`), the response draw (`mu_inf`, `phi_p`), the noise draw, and
  therefore the pre-clip continuous `mu` array, are generated **exactly
  once**, keyed only by `r` (not by cell). Each of the 9 cells then applies
  its own `C_gen` clip to that one shared pre-clip array to obtain its
  trajectories, and its own `MU_CEIL` when fitting. This makes the comparison
  paired at the compound and fold level, as design §2.3 requires, and is the
  only way to satisfy "cells differ only in the two manipulated constants"
  given clipping is the last step of generation.
- **Seed namespace.** `derive_seed(*parts) = sha256("muru-v2-calibration|" +
  "|".join(parts))[:8 bytes], big-endian`, disjoint from
  `generator.derive_seed`'s `"paper-benchmark-v1|"` prefix (remediation plan
  §2.2). Parts are `("E0", f"r{r:03d}", stage)` for `stage` in
  `{"compounds","law","response"}` — replicate-only, no cell id, to realize
  shared randomness above.
- **No search.** `pysr` is never imported; verified mechanically after the
  run by asserting `"pysr" not in sys.modules`.

## 4. Decision criterion (frozen; no post-result threshold added)

Reproduced verbatim from `v2_design/MURU_V2_A1_STUDY_DESIGN.md` §2.6, the
sole authority for the causal conclusion:

| `boundary_limited_rate` drop, control minus `gnone_copen` (absolute, in rate units) | Committed conclusion | Mapped terminal category |
|---|---|---|
| `> 0.50` | H_clip carries the mechanism | `GENERATOR_CLIP_DOMINANT` if the two-factor decomposition (§5) attributes the drop mainly to the `C_gen` main effect; `FITTER_RANGE_DOMINANT` if attributed mainly to the `MU_CEIL` main effect instead |
| `0.10` to `0.50` | H_clip and H_alias both contribute | `COUPLING_INTERACTION_DOMINANT` |
| `< 0.10` | H_null; `MU_CEIL` exonerated | `NEITHER_SUFFICIENT` |

The three row boundaries (`0.10`, `0.50`) and their attached conclusions are
the frozen decision criterion and are not altered here. The right-hand column
maps that frozen 3-way outcome onto the four category names named in this
run's scope instructions using the mechanistic decomposition required
separately by §5 (main effects + interaction) — this mapping is declared now,
before any world is generated, precisely so it cannot be chosen after seeing
which row the run lands in. If the drop exceeds 0.50 and the decomposition
does not cleanly favor one main effect (e.g. both main effects are
comparable, or the interaction term is the largest component), the terminal
category is reported as `GENERATOR_CLIP_DOMINANT` only when `C_gen`'s main
effect strictly exceeds both `MU_CEIL`'s main effect and the interaction
term; otherwise `COUPLING_INTERACTION_DOMINANT` is used even though the drop
exceeds 0.50, and this is disclosed explicitly as a case the frozen three-row
table alone under-determines.

## 5. Required analysis

Per cell (9 cells x 60 worlds), at the compound-fold level and aggregated to
the case, exactly the metrics design §2.4 names: `contact_rate`,
`unresolved_rate`, `probe_gain_rel` distribution, `evaluable_M3` (0..30),
`boundary_limited_rate`, `pin_at_ceiling_share`, `mu_max_at_clip_share`. Also,
per the run scope: `false_m0_rejection_rate` (share of the 540 cases whose
`CaseAdequacyStatus` is any `M0_REJECTED_*`, which is a type-1 error rate by
construction since every world is true M0), and the `C_gen x MU_CEIL`
interaction effect on `boundary_limited_rate` via a saturated 3x3 cell-mean
decomposition (grand mean + row effects + column effects + residual
interaction, since the design is a balanced complete factorial with equal
n=60/cell — no model needs to be fit). Effect sizes reported as absolute rate
differences with Wilson 95% confidence intervals (n=60 per cell, n=180 per
factor level, n=540 grand total); uncertainty on `probe_gain_rel` reported as
median with bootstrap (2000 resamples) 95% CI.

## 6. Control-arm abort gate (validity check, not a decision statistic)

Per the hard scope, no v1 Held-out case is used in E0's decision statistics.
This gate instead compares the control arm's own aggregate rates against
**already-published, already-frozen aggregate figures** quoted in
`v2_design/MURU_V2_A1_STUDY_DESIGN.md` §1.1 (sourced from
`MURU_V1_G1_FAILURE_TAXONOMY.csv`, spent evidence, cited only as prior
corroboration per remediation plan §2.3 — "Held-out evidence can corroborate
a v2 conclusion; it cannot produce one" — never as a v2 decision input, and no
individual Held-out case record is read or rescored). Three checks, all
computed over the 60 `g1e4_c1e4` control-arm worlds:

| Check | Pre-declared band | Reference (spent, corroboration only) |
|---|---|---|
| `contact_rate` (M3, compound-fold level) | `> 0` | boundary contact is the mechanism under test; zero would mean the reimplementation never engages it |
| `mu_max_at_clip_share` | `[0.20, 0.90]` | 72/164 = 0.439 of v1 G1 cases have `mu_max` exactly at the clip |
| `boundary_limited_rate` (case level) | `[0.30, 0.90]` | 97/164 = 0.591 v1 Held-out `BOUNDARY_LIMITED` rate |

Bands are deliberately wide (v1's population mixes multiple noise levels,
missingness, and case-level idiosyncrasy that E0's homogeneous control arm
does not reproduce exactly; only order-of-magnitude, same-direction agreement
is required). If any check fails, E0 aborts before the other 8 cells run and
the discrepancy is investigated as an implementation defect, not resolved by
moving the band.

## 7. Per-world and per-fit persisted fields

Per compound-fold-detector fit (`FitResult`): `world_id`, `cell_id`,
`replicate`, `compound_id`, `detector` (M0/M1/M2/M3), `held_energy`,
`objective`, `params`, `boundary_contact`, `unresolved_boundary`,
`probe_param`, `probe_side`, `probe_obj`, `probe_gain_rel`, `state`.

Per world: `world_id`, `cell_id`, `C_gen_level`, `MU_CEIL_level`, `replicate`,
per-detector `ContrastResult` (`evaluable`, `practical_wins`,
`status_counts`, `evaluable_sufficient`, `fired`), `CaseAdequacyStatus`,
`false_m0_rejection` (bool), `boundary_counts` by detector,
`mu_max_at_clip_share`, `evaluable_M3`, detector evaluability (per detector
`evaluable_sufficient`), content hash of the world's compounds/trajectories
frame.

## 8. Cost

No symbolic search. A 5-world pilot (one replicate across all 9 cells) is run
first to measure true per-world cost; the 0.5-1.5 CPU-hour estimate (design
§2.7) is then replaced by the pilot's measurement before committing to the
full 540-world run.

## 9. What is out of scope here

E1-E6 are not executed. Held-out and Challenge partitions are not read.
`v2_design/MURU_V2_G2_PARETO_STUDY_DESIGN.md` and
`v2_design/MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` are carried only because
they are part of the same imported design commit; nothing in them is read for
any E0 decision.
