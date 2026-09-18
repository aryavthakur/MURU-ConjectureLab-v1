# MURU CE interface adjudication, Design B: feasibility and design plan

Status: PLANNING ONLY. Not preregistered, not frozen, no spectra acquired, no model run on any candidate molecule. Written 2026-09-18 on top of the closed Design A (interpretation commit `1937aa9`).

Pilot information used: only the aggregate Design A results already reported in `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_RESULT.md`, plus Design A population metadata already summarised at freeze (precursor mass distribution, `diagnostics/k_separation_summary.json`). No compound-level outcome was reopened and no new analysis of the 33-compound population was run.

## 1. Primary hypothesis

For the frozen public ICEBERG 2.1 (`msg` simulation) and GLACIER (`msg`) checkpoints, on prospectively acquired Orbitrap HCD [M+H]+ spectra of compounds absent from their training table:

- H0: mean compound-level composite cosine advantage of K1 (`CE = NCE`) over K2 (`CE = NCE x precursor_mz / 500`) is zero in the mass-divergent strata.
- H1: it is non-zero. Two-sided, alpha 0.05.

Composite = mean over the NCE grid and the two models, exactly as in Design A. Endpoint: untransformed full-spectrum cosine. Jensen-Shannon is robustness only. K3 (`floor(K2)`) is scored and reported descriptively; it spends no alpha and drives no sample size.

Physical note that motivates the contrast: Thermo HCD already scales applied energy with m/z, so K2 is the conversion from instrument NCE to an absolute-energy-like value. The question is which of the two the checkpoints actually learned from their mixed training axis.

## 2. Mass strata ([M+H]+ theoretical m/z)

| Stratum | Window | r = abs(m/z / 500 - 1) | K2 relative to K1 | Role |
|---|---|---|---|---|
| L, low | 130 to 300 | 0.40 to 0.74 | lower (K2 = 0.26 to 0.60 x NCE) | divergent |
| N, null | 485 to 515 | at most 0.03 | equal within 3% | negative control |
| H, high | 700 to 900 | 0.40 to 0.80 | higher (K2 = 1.40 to 1.80 x NCE) | divergent |

L and H have matched divergence magnitude but opposite sign. That is the second identifying lever: an interface effect penalises K2 in both directions, whereas a model that simply prefers lower (or higher) energies would reward K2 in one divergent stratum and penalise it in the other. Design A had one compound in 450 to 550 and mean r 0.42; here mean r in the divergent strata is about 0.55 and the null stratum is one third of the design.

## 3. NCE grid: 15, 30, 45, 60, 75, 90 (six levels)

Rationale, not the 16-level 15 to 90 by 5 ladder:

- Leverage does not need a dense grid. The checkpoints encode CE as a 64-dimension sinusoid that saturates fast (encoding distance 4.12 at a 5-unit difference, 5.76 at 40). In the divergent strata K1 and K2 differ by 6 to 72 units at every grid level, so every level already carries near-maximal separation. Extra levels add no new contrast.
- Precision gain flattens by six. Treating the within-compound correlation of the K1 minus K2 contrast across NCE cells as 0.5 (assumption), the compound-level SD falls from 0.135 at Design A's 2 cells to 0.123 at 4, 0.119 at 6, 0.117 at 8 and 0.114 at 16. Going from 6 to 16 levels buys 4% in SD for 2.7x the scans.
- Six evenly spaced levels give two points in each of low (15, 30), mid (45, 60) and high (75, 90) energy, keep a linear NCE term estimable, and contain Design A's cells 30 and 60 for descriptive continuity.
- Five levels (e.g. 20, 35, 50, 65, 80) would also be defensible; six is chosen because it keeps 15 and 90, which matter most for H at low energy and L at high energy, at the cost of one extra scan per compound.

Disclosed support check for preregistration: K2 reaches 162 at NCE 90 and m/z 900. The fraction of (compound, NCE) cells whose K1 or K2 value falls outside the checkpoints' training CE support will be computed from Phase 0 metadata only and reported, with one prespecified sensitivity analysis excluding those cells.

## 4. Compound eligibility (all decidable from metadata, no model run)

1. Theoretical [M+H]+ inside one of the three windows.
2. 2D InChIKey first block absent from the MassSpecGym 1.5 table the three checkpoints trained and validated on (all splits), and absent from the Design A and PR #8 populations.
3. Passes the frozen ms-pred structure filters and input limits of both checkpoints (element set, heavy-atom and mass limits), checked on the structure only.
4. Neutral, single covalent unit, no permanent charge; [M+H]+ is the dominant MS1 species in the acquired standard (checked on MS1, not MS2).
5. Purity at least 95% by vendor certificate; MS1 precursor within 5 ppm of theory.
6. At most one compound per Murcko scaffold group, so the compound is the resampling unit.
7. Selected from the purchasable pool by stratified random draw within each window, before any acquisition, with the drawn list committed first.

## 5. Recommended N: 180 analysable compounds, 60 per stratum (procure 66 per stratum, 198)

Pilot variance: Design A's descriptive 95% interval for D12, [-0.003235, +0.088835], implies a compound-level SD of 0.135 at 2 NCE cells. Projected to 6 cells this is 0.119; the plan uses **sigma = 0.13** to allow for a new laboratory and instrument.

Design effect: Design A's D12 of +0.042 at mean r 0.42 projects to about +0.055 at the divergent strata's mean r of 0.55. The plan powers on **delta = 0.040**, which shrinks that projection by about 27% for the optimism of an unresolved pilot.

Paired, two-sided alpha 0.05, 90% power: n = ((1.960 + 1.282) x 0.13 / 0.040)^2 + 1.9 = **113 divergent compounds**. The plan uses 120 analysable (60 L + 60 H):

| True divergent-stratum effect | Power at n = 120 |
|---|---|
| 0.030 | 0.72 |
| 0.0385 (MDE at 90%) | 0.90 |
| 0.040 | 0.92 |
| 0.050 | 0.99 |

Null stratum, 60 compounds: sized for the identifying test (section 8), not the primary. Procurement at 66 per stratum covers about 10% attrition from failed ionisation, impurity or QC. Minimum acceptable if H sourcing falls short: H at least 50 with L + H at least 120; below that, stop before acquisition and do not preregister.

## 6. Replicate strategy

- Replication budget goes to compounds, not injections. Between-compound model error dominates the contrast; instrument repeatability of a pure standard is small by comparison.
- One primary acquisition per compound, all six NCE levels as separate single-energy (non-stepped) HCD targeted scans in the same injection.
- At least three MS2 scans per NCE level across the chromatographic peak, combined into one spectrum per (compound, NCE) cell by a rule frozen at preregistration. Scan-level replication is free.
- A reproducibility set: a random 15% of compounds (27), balanced across strata, re-acquired on a separate day. Used for a QC gate (obs-to-obs cosine) and reported, never pooled into the primary.

## 7. Primary statistical test

- Per compound i: d_i = mean over 6 NCE cells and 2 models of [cos(K1 prediction, observed) - cos(K2 prediction, observed)].
- Estimand: D_div = (mean d in L + mean d in H) / 2, equal stratum weights.
- Test: stratified compound-level percentile bootstrap, B = 10,000, fixed seed, two-sided 95% interval. K1 favoured if wholly above zero, K2 favoured if wholly below, otherwise unresolved. No alpha split: one primary contrast.
- Descriptive only: K3, JS, per-model, per-NCE, per-stratum.

## 8. Mass-by-mapping identifying test

Run only if the primary rejects, in fixed sequence, so family-wise alpha stays 0.05.

- I = D_div - D_null, where D_null is the same contrast in stratum N. Under the interface explanation the K1 minus K2 advantage collapses near m/z 500, so I has the sign of D_div. One-sided alpha 0.05 in that direction (the direction is fixed by the primary result, before this test is looked at).
- Sign-consistency gate, no alpha: the point estimates of the contrast in L and in H must both share the sign of D_div.

Verdicts: **K1 (or K2) SUPPORTED AND IDENTIFIED** requires primary rejection, I rejection and the sign gate. Primary rejection alone is **K1 (or K2) FAVOURED, NOT IDENTIFIED**. Otherwise **INTERFACE UNRESOLVED**.

Power of I at n = 60 null compounds, divergent effect 0.040 fully shrunk at m/z 500: 0.91 if the null-stratum contrast SD is 0.05, 0.82 at 0.08, 0.62 in the worst case where it is as dispersed as the divergent strata (0.13). The worst case is unlikely, because K1 and K2 inputs differ by at most 2.7 CE units there, but it is disclosed. Raising N to 80 moves the worst case only to 0.68, so 60 is kept.

## 9. Acquisition burden

| Item | Count |
|---|---|
| Compounds procured / analysable | 198 / 180 |
| Pooled mixes (about 10 compounds, strata balanced within each mix, no co-eluting precursors within 2 m/z) | 20 |
| Reproducibility re-injections | 3 mixes (27 compounds) |
| Blanks, system suitability, QC standards | about 10 |
| Total injections | about 33, at 20 min each, about 11 instrument hours |
| Primary (compound, NCE) spectra | 1,188 acquired, 1,080 analysable |
| Reproducibility spectra | 162 |
| MS2 scans acquired | about 4,000 |
| Later model predictions (after acquisition only) | 180 x 6 x 2 models x 3 mappings = 6,480 |

Injection order randomised with strata interleaved, so run position is not confounded with mass. One instrument, one resolution setting, one isolation width for the whole study.

## 10. Feasibility

Instrument burden is small: about two instrument days including the separate reproducibility day, on one Orbitrap with HCD. It is feasible.

The binding constraint is compound sourcing, not acquisition. The H stratum is the risk: 66 compounds at [M+H]+ 700 to 900 that ionise as [M+H]+, pass both checkpoints' input limits and are absent from MassSpecGym excludes many familiar large drugs and natural products. The N stratum needs 66 in a 30 Da window, which is plausible from a large commercial or in-house library. Next concrete step before any preregistration: a metadata-only sourcing screen of available compound libraries against items 1 to 6 of section 4, with the go rule that H reaches at least 50 and each other stratum at least 60. If it passes, freeze this design as the Design B preregistration; if not, report the shortfall rather than widen the windows after seeing availability by mass.
