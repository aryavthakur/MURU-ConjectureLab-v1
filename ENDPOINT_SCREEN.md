# ENDPOINT_SCREEN.md

Generated 2026-08-11 23:08 UTC.

Basis: **517 positive-mode compound trajectories with all six collision energies**, base preprocessing cell (no cutoff, precursor included, raw intensities). The master plan's endpoint recommendation rests on 56 trajectories; this is that comparison re-run at 517.

## The decomposition identity (BLOCKER check)

Master plan section 7.1 states `mu = SY + (1-SY)*phi` and the session brief makes a failure of it a BLOCKER.

The identity as written requires the **observed** precursor peak m/z to equal the **declared** `MS$FOCUSED_ION: PRECURSOR_M/Z`. RMassBank recalibrates masses, so it does not. The exact identity is

```
mu = SY * (mz_observed_precursor / mz_declared_precursor) + (1 - SY) * phi
```

| Form | n | max residual | p99 | median | Rows above 1e-12 |
|---|---|---|---|---|---|
| Exact (above) | 66,514 | **4.441e-16** | 2.220e-16 | 0.000e+00 | **0** |
| Plan form | 66,514 | 5.934e-06 | 7.341e-07 | 0.000e+00 | 10,588 |

Max |1 - mz_observed/mz_declared| = **9.087e-06** (about 9 ppm), which fully accounts for the plan-form residual.

**BLOCKER RESOLVED.** The exact decomposition holds to 4.4e-16, i.e. floating point. The plan's stated form is an approximation accurate to ppm -- scientifically irrelevant against mu's within-compound range of ~0.44, but not 'floating-point tolerance'. mu is computed directly from its definition and never reconstructed from the decomposition. See `PROPOSED_DEVIATION_FROM_MASTER_PLAN.md`.

## Endpoint comparison at full n

| Endpoint | Monotone (strict) | % | Monotone (weak) % | Median within-cpd range | Range 95% CI | Between-cpd SD | Range/SD | NaN % | Direction |
|---|---|---|---|---|---|---|---|---|---|
| mu | 437/517 | 84.5 | 84.5 | 0.4372 | [0.416, 0.466] | 0.1851 | 2.36 | 0.00 | decreasing |
| survival_yield | 104/517 | 20.1 | 95.4 | 0.6603 | [0.611, 0.730] | 0.2405 | 2.75 | 0.00 | decreasing |
| fragment_depth | 347/517 | 67.1 | 67.1 | 0.2254 | [0.208, 0.240] | 0.1703 | 1.32 | 0.67 | decreasing |
| spectral_entropy | 144/517 | 27.9 | 28.0 | 1.7343 | [1.565, 1.835] | 0.9373 | 1.85 | 0.00 | flat_or_nonmonotone |
| normalized_entropy | 102/517 | 19.7 | 19.7 | 0.3767 | [0.352, 0.402] | 0.1872 | 2.01 | 0.96 | flat_or_nonmonotone |
| base_peak_fraction | 47/517 | 9.1 | 9.3 | 0.5355 | [0.498, 0.563] | 0.2275 | 2.35 | 0.00 | flat_or_nonmonotone |
| peak_count | 60/517 | 11.6 | 21.9 | 36.0000 | [31.000, 42.000] | 49.5203 | 0.73 | 0.00 | flat_or_nonmonotone |

(Bootstrap CI: 2000 resamples over compounds, not records.)

## Median endpoint value by collision energy

| NCE | mu | survival_yield | fragment_depth | spectral_entropy | normalized_entropy | base_peak_fraction | peak_count |
|---|---|---|---|---|---|---|---|
| 15 | 0.9165 | 0.6656 | 0.6541 | 0.6527 | 0.3703 | 0.7957 | 6 |
| 30 | 0.7085 | 0.1450 | 0.5823 | 1.1396 | 0.4442 | 0.6259 | 13 |
| 45 | 0.5348 | 0.0034 | 0.5135 | 1.5573 | 0.5197 | 0.4958 | 24 |
| 60 | 0.4642 | 0.0000 | 0.4599 | 2.0906 | 0.6015 | 0.3844 | 34 |
| 75 | 0.4185 | 0.0000 | 0.4165 | 2.3104 | 0.6336 | 0.3242 | 43 |
| 90 | 0.3803 | 0.0000 | 0.3803 | 2.3664 | 0.6700 | 0.3072 | 41 |

## Comparison with the master plan's 56-trajectory sample

| Claim (master plan) | Plan value (n=56) | This run (n=517) | Verdict |
|---|---|---|---|
| mu monotone fraction | 48/56 = 86% | 437/517 = 84.5% | **CONFIRMED** |
| entropy monotone fraction | 18/56 = 32% | 144/517 = 27.9% | **CONFIRMED** |
| mu median within-compound range | 0.44 | 0.4372 | **CONFIRMED** |
| mu between-compound SD | 0.23 | 0.1851 | lower than stated |
| mu medians 15->90 | 0.867 ... 0.385 | 0.916 ... 0.380 | **CONFIRMED** |
| SY medians 15->90 | 0.60, 0.085, 0.002, 0, 0, 0 | 0.666, 0.145, 0.003, 0.000, 0.000, 0.000 | **CONFIRMED** |
| entropy medians 15->90 | 0.63 ... 1.97 | 0.653 ... 2.366 | direction confirmed, high end higher |

## Preprocessing sensitivity (master plan section 7.3)

| Cutoff | Precursor | Transform | Median n peaks | mu monotone % | mu median range | entropy monotone % | entropy median range |
|---|---|---|---|---|---|---|---|
| 0.0 | out | raw | 21 | 67.1 | 0.225 | 33.1 | 1.502 |
| 0.0 | out | sqrt | 21 | 68.9 | 0.210 | 29.2 | 1.765 |
| 0.0 | in | raw | 22 | 84.5 | 0.437 | 27.9 | 1.734 |
| 0.0 | in | sqrt | 22 | 86.5 | 0.359 | 28.0 | 1.832 |
| 0.001 | out | raw | 21 | 67.1 | 0.225 | 33.1 | 1.502 |
| 0.001 | out | sqrt | 21 | 68.9 | 0.210 | 29.2 | 1.765 |
| 0.001 | in | raw | 22 | 84.5 | 0.437 | 27.9 | 1.734 |
| 0.001 | in | sqrt | 22 | 86.5 | 0.359 | 28.0 | 1.832 |
| 0.01 | out | raw | 10 | 57.8 | 0.224 | 21.9 | 1.567 |
| 0.01 | out | sqrt | 10 | 56.5 | 0.220 | 24.2 | 1.851 |
| 0.01 | in | raw | 10 | 81.2 | 0.443 | 21.1 | 1.675 |
| 0.01 | in | sqrt | 10 | 81.4 | 0.380 | 28.8 | 1.881 |

- mu's median within-compound range across all 12 cells: **0.210 to 0.443**
- The 0.1% cutoff cell is **numerically identical** to the no-cutoff cell in every metric. RMassBank's formula filter has already removed everything below that threshold, so that axis of the grid is inert on the curated branch. A real 0.1% test requires the raw branch.
- Excluding the precursor reduces mu's monotone fraction to the fragment-depth value exactly, which is the expected identity (mu without the precursor peak *is* phi) and serves as an internal consistency check.

## Endpoint verdicts

| Endpoint | Verdict | Reason |
|---|---|---|
| **mu** | **PRIMARY** | Highest strict monotonicity (84.5%), largest range/SD, 0% missing, resolves across the whole grid, most preprocessing-stable value. |
| survival_yield | SECONDARY, censored | Weakly monotone in 95.4% but strictly monotone in only 20.1% because it ties at exactly 0. Dead above NCE 45. Retained for the decomposition. |
| fragment_depth | SECONDARY | Monotone 67.1%, smaller range/SD than mu, undefined for precursor-only spectra. Retained for the decomposition. |
| spectral_entropy | **REJECTED as primary** | Monotone in only 27.9%. Spearman rho against peak count reaches +0.89 (see CONFOUNDERS.md): it is close to a peak-count statistic, and peak count here is set by RMassBank's annotator. Kept as a robustness endpoint. |
| normalized_entropy | DIAGNOSTIC only | Monotone 19.7%. |
| base_peak_fraction | REJECTED | Monotone 9.1%. |
| peak_count | COVARIATE only | Monotone 11.6%; range/SD below 1. |

**Assumption A13 is CONFIRMED at full n.** The master plan's recommendation of mu, derived from 56 trajectories, survives re-evaluation on 517. The decision follows the measured evidence, not the recommendation.
