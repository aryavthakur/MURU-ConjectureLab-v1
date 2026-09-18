# MURU CE interface adjudication, Design B: feasibility and design plan

Status: PLANNING ONLY. Not preregistered, not frozen, no spectra acquired, no model run on any candidate molecule. Written 2026-09-18 on top of the closed Design A (interpretation commit `1937aa9`). Revision 2 (correction pass on `4a4c999`): single acquisition format, corrected NCE-grid rationale, metadata-only training-support audit, pilot-agnostic power table, two-sided identifying test.

Pilot information used: only the aggregate Design A results already reported in `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_RESULT.md`, treated as a noisy pilot for variance only, plus Design A population metadata already summarised at freeze. No compound-level outcome was reopened and no new analysis of the 33-compound population was run.

## 1. Primary hypothesis

For the frozen public ICEBERG 2.1 (`msg` simulation) and GLACIER (`msg`) checkpoints, on prospectively acquired Orbitrap HCD [M+H]+ spectra of compounds absent from their training table:

- H0: the mean compound-level composite cosine advantage of K1 (`CE = NCE`) over K2 (`CE = NCE x precursor_mz / 500`) in the mass-divergent strata is zero.
- H1: it is non-zero. Two-sided, alpha 0.05.

Composite = mean over the NCE grid and the two models, as in Design A. Endpoint: untransformed full-spectrum cosine. Jensen-Shannon is robustness only. K3 (`floor(K2)`) is scored and reported descriptively; it spends no alpha and drives no sample size.

Thermo HCD already scales applied energy with m/z, so K2 is the conversion from instrument NCE to an absolute-energy-like value. The question is which of the two the checkpoints learned from their mixed training axis.

## 2. Mass strata ([M+H]+ theoretical m/z)

| Stratum | Window | r = abs(m/z / 500 - 1) | K2 relative to K1 | Role |
|---|---|---|---|---|
| L, low | 130 to 300 | 0.40 to 0.74 | lower (K2 = 0.26 to 0.60 x NCE) | divergent |
| N, null | 485 to 515 | at most 0.03 | within 3%, at most 2.25 CE units | negative control |
| H, high | 700 to 900 | 0.40 to 0.80 | higher (K2 = 1.40 to 1.80 x NCE) | divergent |

L and H have matched divergence magnitude but opposite sign. An interface effect penalises K2 in both; a model that merely prefers lower (or higher) energies would reward K2 in one and penalise it in the other.

## 3. NCE grid: 15, 30, 45, 60, 75 (five levels)

The CE encoding is a fixed 64-dimension sinusoid with no saturation, clipping or exact aliasing (Phase 0, section 6). Its distance depends only on the CE difference and has near-alias dips at differences of about 5.95, 11.95 and 18.15, and its ordinal structure is weak. So the grid cannot be justified by the encoding; it is justified by these four criteria:

1. **Energy coverage.** 15 and 30 low, 45 mid, 60 and 75 high. Evenly spaced, so a linear NCE term is estimable. Contains Design A's 30 and 60 for descriptive continuity.
2. **Burden.** Five targeted MS2 scans per cycle per compound (section 6). Every added level costs duty cycle and spectra.
3. **K1/K2 separation.** In L and H, abs(K1 - K2) runs from 6.0 to 60.0 CE units at every grid level; in N it is at most 2.25. 6.1% of divergent (m/z, NCE) cells fall within 0.5 units of a near-alias difference; disclosed, not designed around.
4. **Training support** (audit below). Dropping NCE 90 removes the only cells beyond the training q99 and the only cell with zero local training support.

Precision gain from more levels is small: with an assumed within-compound correlation of 0.5 across cells, the projected compound-level SD is 0.121 at five levels and 0.119 at six, both under the planning sigma of 0.13.

### Training-support audit (metadata only)

Script `scripts/ce_interface_adjudication/design_b/01_grid_support_audit.py`, output `artifacts/ce_interface_adjudication/design_b/grid_support_audit.json`. Reads only the reconstructed MassSpecGym 1.5 CE metadata (the 119,029 rows all three checkpoints trained and validated on, all [M+H]+). No model run, no spectrum read. Training numeric CE: min 0, q05 7.6, q95 90, q99 150, max 358.4. Design cells = every 0.5 Da m/z step in each window times each NCE level, strata weighted equally. Local support = training rows in the same mass window with CE within 5 units of the cell's range (training rows per window: L 46,985, N 2,611, H 2,385).

| Grid | Mapping | Planned CE range | Cells above q95 (90) | Cells above q99 (150) | Outside training min/max |
|---|---|---|---|---|---|
| 15 to 90 by 15 | K1 | 15 to 90 | 0% | 0% | 0% |
| 15 to 90 by 15 | K2 | 3.9 to 162 | 18.0% | 1.9% | 0% |
| **15 to 75 by 15** | K1 | 15 to 75 | 0% | 0% | 0% |
| **15 to 75 by 15** | K2 | 3.9 to 135 | 11.7% | 0% | 0% |

Sparse extreme cells:

- **K2, H, NCE 90 (dropped):** CE 126 to 162, one third above q99, and **0** training rows in the 700 to 900 window within 5 units of 162. This is avoidable tail extrapolation and the reason for the 75 cap.
- **K2, H, NCE 60 and 75 (kept):** CE 84 to 108 and 105 to 135, 75% and 100% above q95, 127 and 135 local training rows. Unavoidable: K2 exceeds 90 at m/z 700 for any NCE above 64, so removing these would remove high-energy coverage from H. It is part of what K2 asserts, not a design choice, and is reported.
- **K1 and K2, N and H, NCE 75:** thin local support for both mappings (N 44 rows, H 83 rows for K1), because training CE above 70 is rare at these masses. Shared by both mappings, so it cannot favour one.
- Prespecified sensitivity: the primary contrast recomputed excluding cells above the training q95 under either mapping. Descriptive only.

## 4. Compound eligibility (all decidable from metadata, no model run)

1. Theoretical [M+H]+ inside one of the three windows.
2. 2D InChIKey first block absent from the MassSpecGym 1.5 table the three checkpoints trained and validated on (all splits), and absent from the Design A and PR #8 populations.
3. Passes the frozen ms-pred structure filters and input limits of both checkpoints (element set, heavy-atom and mass limits), checked on the structure only.
4. Neutral, single covalent unit, no permanent charge; [M+H]+ is the dominant MS1 species in the acquired standard (checked on MS1, not MS2).
5. Purity at least 95% by vendor certificate; MS1 precursor within 5 ppm of theory.
6. At most one compound per Murcko scaffold group, so the compound is the resampling unit.
7. Selected from the purchasable pool by stratified random draw within each window, before any acquisition, with the drawn list committed first.

## 5. Sample size: 120 divergent (60 L + 60 H) and 60 null analysable; procure 198

Pilot variance: Design A's descriptive 95% interval for D12 implies a compound-level SD of 0.135 at 2 NCE cells. The plan uses **sigma = 0.13**. Design A's point estimate is not used to set the effect: it is a noisy pilot from an unresolved study, and no linear projection with mass divergence is assumed.

Required divergent compounds, paired, two-sided alpha 0.05, 90% power, sigma 0.13 (normal approximation plus the t correction):

| True effect | Required divergent N |
|---|---|
| 0.025 | 286 |
| 0.030 | 199 |
| 0.035 | 147 |
| 0.040 | 113 |

**Resolution target, chosen consciously: 0.040 composite cosine.** With 120 divergent compounds the design has 90% power for a true effect of **0.0385** or larger, 84% at 0.035 and 71% at 0.030. Smaller true effects are more likely to end unresolved than resolved. Resolving 0.030 would need about 200 divergent compounds (roughly 1.7x the sourcing and instrument time).

Null stratum: 60, sized for the identifying test (section 8). Procurement at 66 per stratum covers about 10% attrition. Minimum acceptable if H sourcing falls short: H at least 50 with L + H at least 120; below that, stop before acquisition and do not preregister.

## 6. Acquisition format and replicate strategy: individual injections

**One compound per injection.** Pooled mixtures are rejected. Retention times of the new compounds are unknown before acquisition, so a pooled targeted method cannot guarantee in advance that every compound gets at least 3 clean MS2 scans at every NCE level: co-elution divides the cycle among up to ten precursors, and in-source fragments or isotopes of one mix member can fall into another's isolation window. Neither risk can be excluded from the instrument method alone.

Method, fixed for the whole study: short reversed-phase LC, about 10 min injection to injection; one MS1 scan plus five single-energy (non-stepped) HCD targeted MS2 scans of the one precursor per cycle, one per NCE level; one resolution setting and one isolation width (1.0 m/z). With a single precursor the cycle is about 0.3 to 0.4 s, which gives well over 3 scans per NCE level across a typical peak. Scan-level replication still costs duty cycle; it is affordable here only because each injection targets one precursor.

- Spectrum per (compound, NCE) cell: combined from the scans within the peak by a rule frozen at preregistration, requiring at least 3 scans.
- **Fallback rule, fixed before acquisition:** if any NCE level of a compound yields fewer than 3 qualifying scans, or the MS1 isolation window fails a precursor-purity threshold frozen at preregistration, re-inject that compound once with a longer gradient. If it still fails, the compound is excluded and counted as attrition. All exclusions are decided before any prediction is generated.
- Replication goes to compounds, not injections. A random 15% (27, balanced across strata) is re-injected on a separate day for a reproducibility QC gate (observed-to-observed cosine), reported and never pooled into the primary.
- Injection order randomised with strata interleaved, so run position is not confounded with mass.

## 7. Primary statistical test

- Per compound i: d_i = mean over 5 NCE cells and 2 models of [cos(K1 prediction, observed) - cos(K2 prediction, observed)].
- Estimand: D_div = (mean d in L + mean d in H) / 2, equal stratum weights.
- Test: stratified compound-level percentile bootstrap, B = 10,000, fixed seed, two-sided 95% interval. K1 favoured if wholly above zero, K2 favoured if wholly below, otherwise unresolved. One primary contrast, no alpha split.
- Descriptive only: K3, JS, per-model, per-NCE, per-stratum, and the support sensitivity of section 3.

## 8. Mass-by-mapping identifying test

Run only if the primary rejects. Fixed sequence, so family-wise alpha stays 0.05.

- Contrast: I = D_div - D_null, where D_null is the same contrast in stratum N. Two-sided 95% stratified bootstrap interval, preregistered in this form.
- I is significant if its interval excludes zero. It supports identification only if its sign agrees with the sign of D_div (the advantage shrinks near m/z 500).
- Sign-consistency gate, no alpha: the L and H point estimates must both share the sign of D_div.

| Verdict | Requires |
|---|---|
| **K1 (or K2) SUPPORTED AND IDENTIFIED** | Primary rejects; I significant with the same sign as D_div; L and H point estimates share that sign |
| **K1 (or K2) FAVOURED, NOT IDENTIFIED** | Primary rejects; any identification condition fails |
| **INTERFACE UNRESOLVED** | Primary does not reject |

Power of the identifying test at 60 null compounds, assuming a divergent effect of 0.040 that vanishes at m/z 500: 0.84 if the null-stratum contrast SD is 0.05, 0.72 at 0.08, 0.49 in the worst case where it is as dispersed as the divergent strata (0.13). Near 500 the K1 and K2 inputs differ by at most 2.25 CE units, so a smaller null-stratum SD is plausible but not guaranteed. The worst case is disclosed: identification can fail even when the primary succeeds.

## 9. Acquisition burden

| Item | Count |
|---|---|
| Compounds procured / analysable | 198 / 180 |
| Primary injections (one per compound) | 198 |
| Blanks (1 per 10) and QC standards (1 per 20) | about 30 |
| Primary run subtotal | about 228 injections, about 38 instrument hours |
| Reproducibility day: 27 re-injections plus blanks and QC | about 35 injections, about 6 hours |
| Fallback re-injections (allowance 5%) | about 10, under 2 hours |
| **Total** | **about 270 injections, about 46 instrument hours, about 3 instrument days** |
| Primary (compound, NCE) spectra | 990 acquired, 900 analysable |
| Reproducibility spectra | 135 |
| Later model predictions (after acquisition only) | 180 x 5 x 2 models x 3 mappings = 5,400 |

## 10. Feasibility

Feasible on one Orbitrap with HCD: about three instrument days of mostly unattended autosampler queue, including the separate reproducibility day.

The binding constraint is compound sourcing. The H stratum is the risk: 66 compounds at [M+H]+ 700 to 900 that ionise as [M+H]+, pass both checkpoints' input limits and are absent from MassSpecGym. The N stratum needs 66 in a 30 Da window. Next step before any preregistration: a metadata-only sourcing screen of available compound libraries against items 1 to 6 of section 4. Go rule: H at least 50 and each other stratum at least 60. If it passes, freeze this design as the Design B preregistration; if not, report the shortfall rather than widen the windows after seeing availability by mass.
