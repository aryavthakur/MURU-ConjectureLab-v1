# MURU v2 Experiment E1: executable protocol

**Status: PREREGISTERED, before any world exists.** Nothing below is fit to or
adjusted against any generated or fitted output. This document commits to
every number needed to run E1 and to the exact admissibility/selection rule
before the first random draw. It binds `v2_design/MURU_V2_A1_STUDY_DESIGN.md`
§3, `v2_design/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` §E1 (lines 135-188),
and `v2_design/MURU_V2_CAUSAL_DECISION_TREE.md` §A.1 (lines 78-123), and
resolves the one thing those three leave conditional on E0's outcome plus
three further engineering details the design's prose specifies conceptually
but not executably.

Authority chain: `v2_design/*` byte-identical import from commit `befca0d`
(`v2_design/DESIGN_PROVENANCE.md`). E0 authority: `MURU_V2_E0_PROTOCOL.md`
(commit `54368f3`), `MURU_V2_E0_ADMISSIBLE_RANGE_RESULTS.md` (commit
`bdbcea6`), `E0_INDEPENDENT_CROSS_CHECK.md` (commit `29bef8b`), all on this
worktree's parent branch `exp/v2-e0-admissible-range`, itself HEAD of this
worktree at creation. Frozen production source read (never modified), same
files and identical hashes as E0's own manifest (re-verified in this
worktree before this document was written):

| File | SHA-256 |
|---|---|
| `src/muru/paper_benchmark/generator.py` | `f5c167366d598695f732882842eef1c20b3cc2c31a39642d16ab6e01d335f604` |
| `src/muru/paper_benchmark/adequacy.py` | `1a96ef6e450aebba6a1ffac5e1fdc6c4bb9e52f29401745a1fafd73b69a0a6e2` |
| `src/muru/paper_benchmark/rc5_adequacy.py` | `6ab7f9c860ddd74c6741590915d440e59e23bb0cfc5c696fecd1dd7a8a3f3382` |
| `src/muru/paper_benchmark/rc5_estimate.py` | `e198e3fad40100e396f244c1055fe65b977b20e05ac98d3dbd0901d507c0d0f4` |
| `src/muru/paper_benchmark/registry.py` | `3f5164fdffc0bb54e5a380ac9ff2f0cad03c47a25095fd6b9a71be3f4b83d1d9` |
| `src/muru/discovery/estimate.py` | `9a12263d369cbe5c3acc6ac6ca0f5ebf4c1bee776c33985b7039db2d4cb42876` |

Identical to E0's own recorded hashes for the same six files: the frozen
fitting stack has not moved between E0 and E1.

---

## 0. What E0 licenses and requires here

E0's decoupling drop was **0.2667**, landing in `MURU_V2_A1_STUDY_DESIGN.md`
§2.6's middle row (`0.10`-`0.50`) and `MURU_V2_CAUSAL_DECISION_TREE.md` §A.0's
middle branch. Per that branch, verbatim: **"CHANGE: none yet. E1 runs with
the ceiling as an explicit third factor."** This binds three things for E1,
mechanically, not by choice:

1. `MU_CEIL` may **not** be fixed at the v1 value when E1 is designed (E0
   §11.1).
2. `C_gen` (the generator response clip) is **not** required to enter E1 as a
   factor: its main-effect range was `0.0056` (0.0% of variance) in E0 (E0
   §11.2). E1 therefore fixes `C_gen` at the v1 production value throughout
   -- i.e. E1 applies exactly the clip `generator.py` already applies
   unconditionally (`np.clip(mu, 1e-4, 1 - 1e-4)`), the same clip every
   Held-out and Development case was generated under. This is not a new
   choice; it is declining to add a factor E0 showed to be negligible, which
   §11.2 explicitly permits ("E1 is not obligated to vary it").
3. No floor/interval magnitude is licensed by E0 alone (E0 §11.4): that is
   exactly RC1's open question, and it is E1's C1-C4 criteria that answer it.

## 1. Resolving "explicit third factor": the one undeclared design choice

`MURU_V2_A1_STUDY_DESIGN.md` §3.2 fixes three design factors (`D`, `alpha`,
`noise`) and does not name `MU_CEIL` among them, because at the time that
document was written E0 had not yet run and the branch requiring `MU_CEIL` to
enter as a factor at all was not yet known to be the one taken. §2.6's
decision table is explicit that the *manner* of inclusion is left to be
"explicit" and "not a fixed constant" -- it does not specify levels or
crossing. This section resolves that the same way `MURU_V2_E0_PROTOCOL.md`
§2 resolved E0's own undeclared "decoupling contrast" cell: by the most
literal, fully-crossed reading, stated before any world is generated.

**Resolution.** `MU_CEIL` enters as a fourth crossed factor at the same three
levels E0 itself tested it at, for direct comparability with E0's own
finding and because those three levels already bracket the effect E0
measured (99.9% of E0's cross-cell variance):

| Level id | Value | Note |
|---|---|---|
| `c1e4` | `1 - 1e-4` = `0.9999` | v1 value; E1's control level |
| `c1e3` | `1 - 1e-3` = `0.999` | E0's middle level |
| `copen` | `1.0 + 1e-2` = `1.01` | E0's fully-open level |

It is **fully crossed** with the entire 51-cell `(D, alpha, noise)` grid,
mirroring E0's own precedent of crossing the full 3x3 rather than
spot-checking corners -- the only reading under which each factor's main
effect and interaction with the others can actually be measured, which
`MURU_V2_A1_STUDY_DESIGN.md` §3.6's metric list requires this study to be
able to do (`monotone_D` is checked "within every deviation type", and this
protocol additionally checks it within every `MU_CEIL` level; see §6).

**Why this is affordable.** `MU_CEIL` is a **fitter-side** manipulation only
(`rc5_adequacy.MU_CEIL` reassigned per fit, exactly as in E0); it never
touches world generation. Crossing it 3-way over the 51 `(D, alpha, noise)`
cells therefore triples the number of **fits**, not the number of **draws**:
each of the 51 x 75 = 3,825 generated worlds (one random draw per `(D,
alpha, noise, replicate)`, §3 below) is fit three times, once per `MU_CEIL`
level, instead of once. E0's own measured cost (407.8s wall clock for
583,200 fit records, single process, §8 below) shows the grid-vectorised
fitter is cheap enough that this is not a materially different undertaking;
§8's pilot re-measures this directly before the full run is authorised.

**Cell count.** 51 x 3 = **153 cells**. Cell id =
`<D>_<alpha>_<noise>_<mu_ceil_level>`, e.g. `m3_a100_n02_c1e4`. World id =
`V2C|E1|<cell_id>|r<replicate:03d>`.

**How the primary admissibility gate treats the new factor.** §3.8's
admissibility criteria (reproduced in §6 below) do not mention `MU_CEIL`,
exactly as `MURU_V2_A1_STUDY_DESIGN.md` §3.8 does not. The literal reading
applied here is the same the design applies to every other unmentioned
stratification (e.g. it does not split `FRR` by noise level either): **the
five admissibility criteria are computed pooled over all `MU_CEIL` levels**,
on `CALIBRATE`. `MU_CEIL`-stratified breakdowns of every headline metric
(`FRR`, `power_D`, `indeterminate_rate`, `alpha_star_D`) are additionally
**mandatory reporting** (per this run's scope instructions, which ask for
`MU_CEIL` as an explicit analysis axis) and criterion 5 (monotonicity in
`alpha`) is checked **both pooled and within each `MU_CEIL` level**; a
within-level monotonicity violation that the pooled check does not catch is
disclosed, not silently absorbed, but does not by itself block admissibility
under the frozen pooled criterion. This mirrors the disclosure discipline
`MURU_V2_E0_ADMISSIBLE_RANGE_RESULTS.md` §3 used for its own abort-gate
denominator mismatch: report the literal frozen criterion's output, and
disclose anything a more granular view shows without overriding it.

---

## 2. World configuration

Reuses `MURU_V2_E0_PROTOCOL.md` §1's bound configuration (180 compounds, 30
scaffolds, 20/5/5 split, energy grid `(15,30,45,60,75,90)`,
`mass_affine_descriptor` law, `mu_inf ~ U(0.15,0.30)`, `phi_p ~
U(1.20,1.70)`) with two additions the M2 and combined-family deviations need,
both transcribed read-only from `generator._synthetic_compounds`:

| Field | Formula | Source |
|---|---|---|
| `descriptor2` | `(0.65*latent + N(0,0.65,180) - min) / (max - min)` | `generator.py` line 109-110 |

(`distractor`, `correlated_distractor` are not read by any of E1's
generative kinds and are not generated.)

**Deviation injection**, transcribed from `generator.combined_response` and
`generator._response_matrix`'s `m1_horizontal` / `m2_high_energy` /
`m3_low_energy` / `combined_violation` branches (imported and called
unmodified; only the per-compound `shape`/`floor`/`ceiling` arrays below are
new code, and they are new only in that they carry an `alpha` multiplier the
production module does not have):

| `D` | `shape(alpha)` | `floor(alpha)` | `ceiling(alpha)` |
|---|---|---|---|
| `M0` | `1` | `mu_inf` | `1` |
| `M1` | `1 + alpha * 0.45 * tanh(descriptor)` | `mu_inf` | `1` |
| `M2` | `1` | `clip(mu_inf + alpha * 0.18 * (descriptor - 0.5), 0.03, 0.55)` | `1` |
| `M3` | `1` | `mu_inf` | `clip(1 - alpha * 0.22 * descriptor, 0.6, 0.99)` |
| `M1+M2+M3` | `1 + alpha * 0.15 * tanh(descriptor)` | `clip(mu_inf + alpha * 0.05 * (descriptor2 - 0.5), 0.03, 0.55)` | `clip(1 - alpha * (11/180) * descriptor, 0.6, 0.99)` |

`0.45`, `0.18`, `0.22`, `0.15`, `0.05`, `11/180` are
`generator.M1_HORIZONTAL_AMPLITUDE`, `M2_HIGH_ENERGY_AMPLITUDE`,
`M3_LOW_ENERGY_AMPLITUDE`, `COMBINED_M1_AMPLITUDE`, `COMBINED_M2_AMPLITUDE`,
`COMBINED_M3_AMPLITUDE` respectively, read by reference from the imported
module, not retyped as new literals, in the implementation. `mu =
generator.combined_response(u, phi_p, shape, floor, ceiling)` for every `D`
including `M0` (at `M0`'s neutral settings this reduces exactly to the M0
law, per `combined_response`'s own docstring). At `alpha = 0` every `D`
produces the identical neutral array regardless of which `D` label is
attached, so the five `alpha=0` cells per noise level are generated once and
shared, exactly as `MURU_V2_A1_STUDY_DESIGN.md` §3.2 requires ("the null arm
is one population of worlds, not five").

**Noise and clip.** Additive Gaussian noise at the cell's `noise` level
(`{0.0, 0.02, 0.06}`), added identically to the deterministic array above
before clipping. Final clip: fixed `[1e-4, 1 - 1e-4]` for every cell (§0.2).

## 3. Shared randomness and seed derivation

Extends `MURU_V2_E0_PROTOCOL.md` §3's paired-seed discipline. For a fixed
`(noise_level, replicate)` there is **one** shared draw -- compounds
(including `descriptor2`), `scale`, `coefficient`, `mu_inf`, `phi_p`, and the
noise array at that noise level -- used by **every** `(D, alpha)` at that
`(noise_level, replicate)`, and by all three `MU_CEIL` levels (`MU_CEIL`
never touches generation). This is what makes every non-null cell paired
with its `alpha=0` null counterpart at the fold and compound level, per
`MURU_V2_A1_STUDY_DESIGN.md` §3.4.3 and the register's "Controls" line for
E1.

```
seed_compounds = derive_seed("E1", noise_level, f"r{r:03d}", "compounds")
seed_law        = derive_seed("E1", noise_level, f"r{r:03d}", "law")
seed_response   = derive_seed("E1", noise_level, f"r{r:03d}", "response")
```

`derive_seed` is the same V2C-namespaced function E0 used:
`sha256("muru-v2-calibration|" + "|".join(parts))[:8 bytes]`, big-endian --
disjoint from `generator.derive_seed`'s `"paper-benchmark-v1|"` prefix. No
`D`, `alpha`, or `mu_ceil_level` token enters any seed derivation, which is
what realizes the pairing (identical draw regardless of which deviation or
ceiling is later applied to it).

**Split assignment.** Design §3.7 requires an *exact* 60/15 per-cell count
("80 percent, 60 per cell ... 20 percent, 15 per cell"), not merely an
expected 80/20 rate, so this is a seeded random **permutation** of the 75
replicate indices for each noise level, not a per-replicate Bernoulli draw:
`seed_perm = derive_seed("E1", noise_level, "split_assignment")`; the first
`round(0.20 * 75) = 15` indices of `np.random.default_rng(seed_perm)
.permutation(75)` are `CONFIRM`, the remaining 60 are `CALIBRATE`. One
permutation per noise level (3 total), shared across every `D`, `alpha`, and
`mu_ceil_level` built from that noise level's draws -- consistent with
`MURU_V2_CAUSAL_DECISION_TREE.md` §2.4 ("E1's world set is split 80/20 ...
both sealed together"). This guarantees exactly 60 `CALIBRATE` + 15
`CONFIRM` replicates in every one of the 51 `(D, alpha, noise)` cells (and
hence 180/45 pooled over each cell's 3 `MU_CEIL` levels), matching §4's
stated split exactly rather than approximately.

## 4. Case count

51 `(D, alpha, noise)` cells x 75 replicates = **3,825 generated worlds**
(distinct random draws), each fit **3 times** (once per `MU_CEIL` level) =
**11,475 (cell, replicate) fit units** = **153 cells x 75 replicates**.

Per fit unit: 3 detectors x 30 test compounds x 6 folds x 2 models (M0 + the
detector) = 1,080 grid fits, plus C4's relaxed refit (fired only for folds
that show boundary contact, not all 1,080) and C3's profile sweep (same
condition). Total base grid fits: 11,475 x 1,080 = **12,393,000**, before the
boundary-contingent C3/C4 overhead.

**Split.** 60 `CALIBRATE` + 15 `CONFIRM` replicates per `(noise_level,
replicate)` draw-group -- i.e. per 51-cell row, applied identically across
all 3 `MU_CEIL` levels of that row, giving 60 x 3 = 180 `CALIBRATE` and 15 x
3 = 45 `CONFIRM` fit units per `(D, alpha, noise)` cell.

Seventy-five replicates per `(D, alpha, noise)` cell (pooled across the 3
`MU_CEIL` levels for any statistic that pools `MU_CEIL`, or 75-per-level
where a `MU_CEIL`-stratified statistic is reported) reproduces
`MURU_V2_A1_STUDY_DESIGN.md` §3.7's own stated standard error (0.046 at p =
0.8) for every pooled statistic, and gives 75 per stratum for the mandatory
`MU_CEIL`-stratified reporting in §1.

## 5. Fit-record instrument

Per `(world_fit_id, detector, compound_id, fold_index)`, extending
`MURU_V2_A1_STUDY_DESIGN.md` §3.5's list to the concrete fields this
implementation persists:

```
world_id, cell_id, D, alpha, noise_level, mu_ceil_level, replicate, split,
detector, compound_id, fold_index, n_observed_energies,
m0_objective, m0_params, m0_boundary_contact,
m0_probes: [{param, side, bound, probe_obj, probe_gain_rel}, ...],
mk_objective, mk_params, mk_boundary_contact, mk_unresolved_c0,
mk_probes: [{param, side, bound, probe_obj, probe_gain_rel}, ...],
mk_relaxed_objective, mk_relaxed_params,                 # C4, per compound (not per fold; see §7.4)
mk_profile_one_se_outward_width, mk_profile_admissible_range,   # C3
sigma_hat_sq,                                             # C2
held_energy, held_response, m0_abs_error, mk_abs_error
```

C4's relaxed refit and verdict comparison are inherently compound-level (one
refit per fold, one verdict per compound across all its folds), so
`mk_relaxed_objective`/`mk_relaxed_params` are persisted per fold (the refit
is per fold, same as the primary fit) and the verdict comparison itself is
computed downstream from the per-fold relaxed errors, exactly mirroring how
the primary verdict is computed from the primary per-fold errors. This
keeps C4 a pure function of persisted per-fold fields, like every other
criterion.

Record volume: 11,475 fit units x 3 detectors x 30 compounds x 6 folds =
**6,196,500** fold records (base). This exceeds
`MURU_V2_A1_STUDY_DESIGN.md` §3.5's estimate (2.02M) by the crossing factor
(153/51 = 3x), as expected from §1's resolution; at the same per-record
footprint this is of order 1.2 GB parquet, still "minutes" to re-score
because every rule remains a pure function of the persisted record.

## 6. Admissibility criterion (frozen; reproduced verbatim from design §3.8)

On `CALIBRATE`, pooled over `MU_CEIL` levels (§1):

1. `FRR <= 0.05`, Wilson upper `<= 0.10`, pooled over the null cells (`alpha
   = 0`, all noise levels, all `MU_CEIL` levels).
2. `indeterminate_rate <= 0.10`, Wilson upper `<= 0.15`, same null population.
3. `power_D >= 0.80`, Wilson lower `>= 0.70`, for each of M1, M2, M3 at
   `alpha = 1.0`, `noise = 0.02`, pooled over `MU_CEIL`.
4. `misattribution <= 0.05` on every non-null cell at `alpha = 1.0`, pooled
   over `MU_CEIL`.
5. `power_D` monotone non-decreasing in `alpha` within every deviation type,
   pooled over `MU_CEIL` (primary check) **and** within each `MU_CEIL` level
   (disclosure-only, per §1).

**Selection**, pre-declared lexicographic order over ADMISSIBLE pairs:

1. fewest total free parameters (`C0`: 0, `C4`: 0, `C1`/`C2`/`C3`: 1 each,
   `P0`: 3, `P1`: 2, `P2`: 1, `P3`: 2 -- a `(C, P)` pair's parameter count is
   the sum);
2. lowest `indeterminate_rate` on the null cells;
3. highest `min(power_M1, power_M2, power_M3)` at `alpha = 1.0`;
4. lowest ladder index (most conservative parameter value; `C0`/`P0` are
   ladder index 0 by definition when tied with a swept criterion at its most
   conservative level).

**Confirmation.** The selected pair is evaluated once on `CONFIRM`. Adopted
only if criteria 1-4 hold again there.

**If no pair is admissible:** H2 or H3, reported as such, per design §3.10.

## 7. Criteria and rules, as pure post-hoc functions of the fit record

### 7.1 Boundary/identifiability criteria (recompute `unresolved_boundary` per fold)

- **C0** (frozen control, 0 param): `unresolved` iff any of that fold's
  touched-bound probes has `probe_obj < best_obj - 1e-12`. This is exactly
  `mk_unresolved_c0` as persisted (computed once, by the frozen
  `rc5_adequacy._boundary_flags`, never recomputed).
- **C1** (relative-SSE floor, 1 param `delta` in `{1e-3, 3e-3, 1e-2, 3e-2,
  1e-1}`): `unresolved` iff any touched probe's `probe_gain_rel > delta`.
- **C2** (noise-scaled floor, 1 param `delta` in `{0.25, 0.5, 1, 2, 4}`):
  `unresolved` iff any touched probe's `(best_obj - probe_obj) > delta *
  sigma_hat_sq * n_fold`, `n_fold = n_observed_energies - 1`.
  `sigma_hat_sq` is declared here (not in the design, which leaves "a
  fold-local residual scale" unspecified): the M0 fold fit's own residual
  variance, `sigma_hat_sq = m0_objective / max(n_fold - 1, 1)` (1 free
  parameter, `log_g`, in the M0 fold fit -- the standard unbiased-variance
  divisor). Computed from the **M0** fit specifically (not the detector's own
  fit) so `sigma_hat_sq` cannot shrink artificially when the detector's own
  fit is boundary-constrained, and so it is comparable across M1/M2/M3.
- **C3** (interval criterion, 1 param `rho` in `{0.05, 0.10, 0.25}`):
  `unresolved` iff `mk_profile_one_se_outward_width > rho *
  mk_profile_admissible_range` for the touched parameter. The one-SE profile
  width is declared here: for `M2`/`M3` (whose second free parameter is
  solved in closed form given `log_g`, making the fold objective an exact
  quadratic in that parameter -- `_grid_objective`'s `den`/`num`/`dev`
  algebra), the profile is the exact closed-form quadratic
  `SSE(theta) = SSE_min + den * (theta - theta_hat)^2` at the fold's fitted
  `log_g`; the outward one-SE half-width is `sqrt(sigma_hat_sq / den)`
  (`den > 0` whenever the fold is usable). For `M1` (two jointly grid-searched
  parameters, no closed form), the profile is a 41-point re-optimisation of
  `log_g` at each swept `log_shape` (nested grid, itself vectorised); this
  is a declared, disclosed approximation to a true profile only in that it
  reuses the coarse `log_g` grid rather than the full 3-round refinement, and
  only applies to `log_g`/`log_shape` boundary contacts, which E0 found are
  not where the boundary pathology concentrates (M3 dominates; see §11.4 of
  E0's results). `mk_profile_admissible_range` is the touched parameter's
  bound-to-bound width at that fold's `MU_CEIL` level (e.g. for
  `low_energy_plateau`: `mu_ceil_value - (a_hi + MIN_VERTICAL_AMPLITUDE)`).
- **C4** (verdict invariance, 0 magnitude parameters, 1 declared relaxation
  fraction): relaxation fraction is declared here as **0.10** -- the middle
  value of C3's own `rho` sweep, chosen for direct comparability between
  "C3 at rho=0.10" and "C4's fixed margin", not tuned to any outcome (no
  world has been generated when this document is written). For a fold whose
  primal fit touched a bound, the bound is relaxed outward by `0.10 *
  admissible_range` for that parameter (same range definition as C3) and the
  fold is refit with that relaxed bound (a full re-run of `fit_model`'s
  search, not a single-point probe). `unresolved` (i.e. `BOUNDARY_LIMITED`
  under C4) iff the compound's `PRACTICAL_WIN`/`NO_PRACTICAL_WIN` verdict
  under the relaxed refit (aggregated over all folds exactly as the primal
  verdict is) differs from the verdict under the primal fit. A compound with
  no boundary contact anywhere is never marked unresolved under any
  criterion, C4 included, matching C0's own behaviour.

Every criterion above operates identically regardless of which `MU_CEIL`
level produced the record: they are pure functions of `(best_obj, probe_obj,
sigma_hat_sq, n_fold, admissible_range, relaxed_objective)`, all already
scoped to that fold's own `mu_ceil_value`.

### 7.2 Practical-win rules (recompute case-level `fired` from per-compound `(mae_m0, mae_alt, evaluable)`)

- **P0** (frozen control): `adequacy.is_practical_win` (ratio 0.90), fired
  iff evaluable `>= 24` and wins `>= 20`.
- **P1** (ratio x win-count grid): ratio `r` in `{0.80, 0.90, 0.95, 0.98}` x
  win count `w` in `{15, 18, 20, 24}`, evaluable floor fixed at 24; win iff
  `mae_alt <= r * mae_m0` (and `mae_m0 > 0`); fired iff evaluable `>= 24` and
  wins `>= w`. 16 combinations.
- **P2** (paired sign test): significance `q` in `{0.05, 0.01, 0.001}`; win
  test identical to P0's (ratio 0.90, i.e. the sign test is over P0's own win
  indicator, replacing only the fixed win-count threshold with a test);
  fired iff evaluable `>= 24` and `adequacy.directional_null_tail(wins,
  evaluable) <= q`. 3 combinations.
- **P3** (conjunction): median relative reduction `m` in `{0.05, 0.10}` x win
  fraction `f` in `{0.5, 0.6, 0.67}`; win test identical to P0's; fired iff
  evaluable `>= 24` and `median((mae_m0 - mae_alt) / mae_m0 over evaluable
  compounds with mae_m0 > 0) >= m` and `(wins / evaluable) >= f`. 6
  combinations.

Total practical-win rule instances: 1 + 16 + 3 + 6 = **26**. Total criteria:
5 (C0 counts once; C1/C2/C3 each contribute 5/5/3 = 13 swept instances, C4
contributes 1) = **1 + 13 + 1 = 15**. Full `C x P` grid: 15 x 26 = **390**
`(criterion, rule)` pairs, each scored on every one of the 153 cells, on both
`CALIBRATE` and `CONFIRM` (`CONFIRM` computed but not consulted for
selection).

**Secondary sweep (labelled, not part of primary selection):** evaluability
floor swept over `{18, 21, 24, 27}` in place of the fixed 24, applied only to
the selected `(C, P)` pair post-selection, per design §3.2's closing
paragraph.

## 8. Cost and pilot

No symbolic search anywhere in E1 (`pysr` import asserted absent, identical
to E0 §3's check). A 5-cell pilot (one replicate from 5 diverse cells --
control-analogue, one at each extreme of `alpha`, one at `noise=0.06`, one at
`mu_ceil_level=copen` -- 5 fit units, not 5 worlds, since each covers one
`MU_CEIL` level only) is run first to measure true per-fit-unit cost; the
design's own 12-CPU-hour estimate (which predates the `MU_CEIL` crossing this
protocol adds) is replaced by that measurement before the full 11,475-fit-unit
run is authorised. If the measurement implies the full run would take longer
than is practical for this session to complete and verify end to end, the
authorized fallback -- applied only if invoked, and disclosed if it is -- is
to reduce `N_REPLICATES` uniformly (preserving the 60/15 CALIBRATE/CONFIRM
ratio and every cell's equal replicate count) to the largest value the
measured per-unit cost supports within budget, never to drop a cell, a
`MU_CEIL` level, or a criterion/rule from the grid. Any such reduction is
reported with its consequence for the design's own standard-error rationale
(§4).

## 9. What is out of scope here

E6 (`FALSE_STRUCTURE_SAFETY_COUNTERWEIGHT`) is not executed: `MURU_V2_A1_STUDY_DESIGN.md`
§4 and `MURU_V2_CAUSAL_DECISION_TREE.md` §A.2 both hold it as a veto
downstream of any change E1 licenses, not a part of E1 itself. Held-out and
Challenge partitions are not read (governance frame §2.1). No PySR import at
any point.

## 10. Implementation addendum: compound-level sufficient statistics

Written after §5-8 above but before any world was generated, once the
implementation (`scripts/e1_fit.py`) made the following storage compression
available; recorded here rather than silently applied, per this project's own
disclosure discipline (`MURU_V2_E0_ADMISSIBLE_RANGE_RESULTS.md` §3).

Every criterion in §7.1 tests "unresolved iff ANY touched-bound probe, across
both the M0 and Mk fold fits and across every one of a compound's (up to 6)
LOEO folds, satisfies condition X" -- and X is monotone in exactly one scalar
per probe (`probe_gain_rel` for C1; the ratio `gain_abs / (sigma_hat_sq *
n_fold)` for C2, pre-divided at aggregation time so C2's stored field is
compared directly against `delta`; `profile_extent / admissible_range` for
C3). An "any, over a set, of a monotone predicate" is exactly equivalent to
"the max of the underlying scalar over that set exceeds the threshold". This
means the fold-level record §5 describes can be losslessly reduced, at
generation time, to one row per `(world_id, detector, compound_id)` carrying
only: `mae_m0`, `mae_alt`, `m0_unresolved_c0_any`, `mk_unresolved_c0_any`
(boolean OR over folds/models), and the three max-over-(fold, model) ratios
above -- plus, for C4, the compound's relaxed-refit `mae_m0`/`mae_alt` pair
(itself already an aggregate over folds, since C4's verdict is compound-level
by construction, §7.1). No fold-level or probe-level detail is discarded that
any criterion in §7.1 can distinguish; `scripts/test_e1_aggregation.py` proves
the equivalence by comparing fold-level and compound-level scoring on a
synthetic record set with adversarially-chosen multi-fold, multi-probe
patterns. Record volume falls from §5's 6,196,500 fold rows to **1,032,750
compound rows** (11,475 fit units x 3 detectors x 30 compounds); this is a
representation change only and alters no criterion's decision.

---

**Terminal state for this document at commit time:** protocol only. No world
generated, no fit executed, no rule selected.
