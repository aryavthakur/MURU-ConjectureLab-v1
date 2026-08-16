# MURU v2 E0: Executable Protocol

**Status at the time of writing: NO WORLD GENERATED, NO FIT EXECUTED.** This
document is committed before `scripts/run_e0_admissible_range.py` is run for the
first time. Its purpose is to bind, in advance, the three things the committed E0
design specifies in prose but does not pin to executable values. Everything else
is inherited verbatim from the design and is not restated as if it were a choice
made here.

**Preregistered authority.** `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 3
(E0), `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json` `experiments[0]`,
`MURU_V2_A1_STUDY_DESIGN.md` section 2, and `MURU_V2_CAUSAL_DECISION_TREE.md`
section A.0. Copies are carried unmodified in `v2_design_reference/`, verified by
git blob hash against design commit `befca0d` (see section 7).

**Scope.** E0 only. No E1. No A1 architecture change. No boundary floor is
chosen. No v2 science is modified.

---

## 1. What the design fixes, and is therefore not open here

Inherited without alteration:

| Item | Design value |
|---|---|
| Factor 1: generator response clip `C_gen` | `1 - 1e-4` (v1), `1 - 1e-3`, none |
| Factor 2: fitter admissible ceiling `MU_CEIL` | `1 - 1e-4` (v1), `1 - 1e-3`, `1.0 + 1e-2` (open) |
| Crossing | full 3 x 3 = 9 cells |
| Worlds | 60 per cell, 540 total |
| Truth | true M0 only; no planted M1/M2/M3 anywhere |
| Geometry | 30 test compounds, 6 energies |
| Randomness | covariates, `mu_inf`, `phi_p`, `g` and noise shared across all nine cells |
| Search | none; PySR never imported |
| Namespace | `world_id = "V2C|E0|<cell_id>|r<replicate:03d>"`, seed payload `"muru-v2-calibration|" + "|".join(parts)` |
| Decision bands | drop `> 0.50` H_clip; `0.10` to `0.50` mixed; `< 0.10` H_null |
| Metrics | `contact_rate`, `unresolved_rate`, `probe_gain_rel`, `evaluable_M3`, `boundary_limited_rate`, `pin_at_ceiling_share`, `mu_max_at_clip_share` |
| Control arm | `(1-1e-4, 1-1e-4)` must reproduce v1 boundary behaviour or E0 aborts |
| Predictions | PE0-1, PE0-2 (design section 6) |

## 2. Open item 1: which world configuration

The design says "true M0 worlds only, 30 test compounds and 6 energies" but does
not name a generative kind. The v1 generator's true-M0 kinds differ in law family
and in noise sd, and both change boundary behaviour materially, so a choice is
forced and is made here on frozen v1 grounds alone.

**Declared: the modal v1 true-M0 configuration.** Law
`mass_affine_descriptor` (`scale * sqrt(mass/250) * (1 + coefficient *
descriptor)`, `scale ~ U(1.1,1.8)`, `coefficient ~ U(0.25,0.55)`), response noise
sd `0.02`, no missingness, 180 compounds split 120/30/30 over 30 scaffolds,
`ENERGY_GRID = (15, 30, 45, 60, 75, 90)`.

**Why this and not another.** Within the frozen 164-case G1 population, five
variants -- F05, F08, F11, F12, F17 -- are *generatively identical* under
`generator._law` and `generator._response_matrix`: same affine law branch, same
noise sd 0.02, no missingness branch, no deviation branch. They differ only in
which covariates the downstream symbolic search is offered, which E0 never runs.
Those five variants are 60 of the 164 G1 cases and are the single largest
generatively-homogeneous block in the population. Noise sd 0.02 is the v1
default, carried by 12 of the 13 G1 variants that are not `scalar_*`.

This choice is made from the frozen v1 registry and generator source, before any
E0 world exists. It is recorded here so that it cannot be revised after results.

## 3. Open item 2: the control-arm abort gate, made executable

The design requires the `(1-1e-4, 1-1e-4)` cell to "reproduce v1 boundary
behaviour on a v1-matched world within Monte Carlo error" and to abort otherwise,
without stating the comparison statistic or the tolerance.

**Declared reference population.** The 60 v1 Held-out G1 cases of variants F05,
F08, F11, F12, F17, from `MURU_V1_G1_FAILURE_TAXONOMY.csv`. This is the exact
generative configuration declared in section 2, at exactly E0's per-cell sample
size. Its frozen values, computed before any E0 world exists:

| Quantity | v1 matched reference (n = 60) |
|---|---|
| `BOUNDARY_LIMITED` cases | 37 |
| `boundary_limited_rate` | 0.6167 |
| 95% Wilson interval | [0.4902, 0.7291] |
| modal `dominant_bound_hit` | `M3:low_energy_plateau@upper`, 55 of 60 |
| detectors fired | 0 of 60 |

**Declared gate.** The control cell passes iff all three hold:

- **G-A.** The 95% Wilson interval of the control cell's `boundary_limited_rate`
  (n = 60) overlaps `[0.4902, 0.7291]`.
- **G-B.** Among control-cell worlds whose case status is `BOUNDARY_LIMITED`, the
  modal dominant bound is `M3:low_energy_plateau@upper`.
- **G-C.** No detector fires on any control-cell world, matching v1's 0 of 60.
  Every E0 world is true M0, so any firing is a false rejection.

If any of G-A, G-B, G-C fails, E0 reports `E0 BLOCKED - <reason>` and no causal
conclusion is drawn. The gate is evaluated on the control cell alone and is
computed before the decision statistic is read.

## 4. Open item 3: which contrast is "the decoupling"

The design's decision criterion is a drop in `boundary_limited_rate` "when the
clip and ceiling are decoupled" but the 3 x 3 admits several decoupled cells.

**Declared primary decision statistic.**

```
Delta_BL = boundary_limited_rate(C_gen = 1-1e-4, MU_CEIL = 1-1e-4)      # control
         - boundary_limited_rate(C_gen = none,   MU_CEIL = 1.0+1e-2)    # fully decoupled
```

expressed as an **absolute** change in the rate, in units of the rate itself, not
as a relative percentage of the control value. `H_clip` names a coincidence of
two constants; the cell in which that coincidence is fully broken on both sides
is `(none, open)`, so that is the cell the criterion is read on.

**Declared bands**, transcribed from the design with the endpoints closed on the
mixed band so the three cases are exhaustive and disjoint:

| Band | Conclusion |
|---|---|
| `Delta_BL > 0.50` | H_clip carries the mechanism |
| `0.10 <= Delta_BL <= 0.50` | H_clip and H_alias both contribute |
| `Delta_BL < 0.10` | H_null; `MU_CEIL` exonerated |

**Declared supporting quantities, reported but not decisional.** The mission
requires E0 to separate generator clipping from fitter admissibility. These are
computed from the same 3 x 3 and reported with Wilson intervals, and none of them
can move the band the decision falls in:

- `Delta_gen` = control minus `(none, 1-1e-4)`: the generator-clip main effect at
  the v1 ceiling.
- `Delta_fit` = control minus `(1-1e-4, open)`: the fitter-ceiling main effect at
  the v1 clip.
- `Interaction` = `Delta_BL - (Delta_gen + Delta_fit)`: the non-additive part.
- The full 9-cell table of every metric in section 1.

## 5. Metric definitions, pinned

| Metric | Denominator and rule |
|---|---|
| `contact_rate` | fits with `boundary_contact` / all fits in the cell. A "fit" is one (world, detector, compound, fold, model) record; 1,080 per world. Also broken out per model. |
| `unresolved_rate` | fits with `unresolved_boundary` / all fits in the cell. |
| `probe_gain_rel` | `(best_obj - probe_obj) / best_obj`, recorded for every probe that triggers the frozen `obj < best_obj - 1e-12` test. Distribution reported as median, IQR, max. |
| `evaluable_M3` | evaluable test compounds for the M3 contrast, 0..30, per world. |
| `boundary_limited_rate` | worlds whose case status is `BOUNDARY_LIMITED` / 60. This is the **decision metric**. |
| `pin_at_ceiling_share` | M3-model fits with `abs(low_energy_plateau - MU_CEIL) <= BOUNDARY_CONTACT_TOL` / all M3-model fits (180 per world). |
| `mu_max_at_clip_share` | test compounds whose observed max response equals `C_gen` exactly / 30. For `C_gen = none` no clip value exists; the metric is reported as `null` and the share at the v1 constant `1 - 1e-4` is reported alongside for comparability. |
| `false_rejection_rate` | worlds with any detector fired / 60. Every world is true M0, so this is false M0 rejection by construction. Reported; not decisional. |

Lower-clip activations are counted separately in every clipped cell. If the
`1e-4` floor never binds, the manipulation is purely on the ceiling and the
`C_gen = none` level differs from the others on the ceiling side only; that is
asserted rather than assumed.

## 6. Fidelity and isolation controls

Each is a hard gate; failure is `E0 BLOCKED`, not a warning.

1. **Generator identity.** The E0 world builder is the v1 generator arithmetic
   with two injected knobs (seed payload prefix, response ceiling). A test drives
   it with the v1 prefix and the v1 ceiling and requires the emitted compounds
   and trajectories to be **exactly equal** to `generator.generate_case` for real
   v1 case ids. Any drift fails closed.
2. **Fitter identity.** The frozen `rc5_adequacy` fitter executes unmodified;
   `MU_CEIL` is injected by an audited context manager that asserts the v1 value
   on entry and restores it on exit. A test requires the injected-at-v1-value
   path to reproduce `rc5_adequacy.run_case_adequacy` exactly on real v1 cases.
3. **Instrumentation identity.** The fit-level recorder must return
   `CompoundContrastRecord` values **identical** to the frozen
   `rc5_adequacy.evaluate_compound_contrast` on the same inputs, and its
   independently recomputed `(boundary_contact, unresolved_boundary)` must equal
   the frozen `_boundary_flags` output on every fit. Instrumentation may observe;
   it may not change what it measures.
4. **Namespace disjointness.** The v2 seed payload prefix
   `"muru-v2-calibration|"` differs from `generator.derive_seed`'s
   `"paper-benchmark-v1|"`; no `V2C|` world id resolves through
   `registry.resolve_case_id`; no E0 world's content hash collides with any
   benchmark case's.
5. **No Held-out or Development tuning.** No benchmark case contributes any value
   to an E0 world, an E0 fit, or the E0 decision. The frozen v1 taxonomy is read
   in exactly two places, both declared in advance: the section 3 abort-gate
   reference and the section 7 motivating-observation reproduction. Neither
   selects a parameter.
6. **No symbolic search.** An import guard installed on `sys.meta_path` raises if
   anything attempts to import `pysr` during an E0 run, and the run asserts
   `"pysr" not in sys.modules` at exit.
7. **Design drift.** Before analysis, the generated corpus is verified against
   this protocol and the committed design: 9 cells, 60 worlds each, 540 total,
   true M0 everywhere, 30 test compounds, 6 energies, factor levels exactly as
   declared, shared draws provably identical across cells. Mismatch aborts.

## 7. Motivating observation, reproduced not assumed

The design's motivating observation is recomputed here from
`MURU_V1_G1_FAILURE_TAXONOMY.csv` as a check that the frozen artifact carried
into `v2_design_reference/` is the one the design was written against:

| Design claim | Recomputed |
|---|---|
| 72 of 164 G1 cases at `mu_max` = 0.9999 | 72 of 164 |
| `M0_NOT_REJECTED` median `mu_max` 0.9802 (n = 67) | 0.9802, n = 67 |
| `BOUNDARY_LIMITED` median `mu_max` 0.9999 (n = 97) | 0.9999, n = 97 |

This motivates E0 and contributes nothing to its result.

## 8. Analysis discipline

The analysis in `scripts/run_e0_admissible_range.py` is run **once**. The
decision statistic, the bands, the abort gate and every metric definition above
are fixed by this document before the first world exists. No threshold is added
after results are viewed. If the outcome is uninformative, that is reported as
the outcome.

**Terminal states.** `E0 COMPLETE - ADMISSIBLE RANGE CAUSAL RESULT ESTABLISHED`
or `E0 BLOCKED - <exact reason>`.
