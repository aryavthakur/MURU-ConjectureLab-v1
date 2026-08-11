# CONFOUNDERS.md

Generated 2026-08-11 23:20 UTC.

Spearman rank correlations between each endpoint and each acquisition covariate, **stratified by collision energy**. Pooling across energies would manufacture correlation from both variables moving with energy. Basis: 517 complete positive-mode trajectories, base cell.

Correlation is not causation; the purpose is to detect whether an apparently elegant energy relationship is dominated by abundance, mass, annotation behaviour or batch structure.

### mu

| Covariate | NCE 15 | NCE 30 | NCE 45 | NCE 60 | NCE 75 | NCE 90 | max abs |
|---|---|---|---|---|---|---|---|
| log10 total ion current | +0.515 | +0.258 | +0.114 | +0.043 | +0.030 | +0.025 | **0.515** |
| precursor m/z | -0.086 | -0.510 | -0.613 | -0.647 | -0.667 | -0.680 | **0.680** |
| peak count | -0.407 | -0.297 | -0.135 | -0.087 | -0.088 | -0.105 | **0.407** |
| retention time | -0.095 | -0.299 | -0.326 | -0.350 | -0.367 | -0.385 | **0.385** |

### survival_yield

| Covariate | NCE 15 | NCE 30 | NCE 45 | NCE 60 | NCE 75 | NCE 90 | max abs |
|---|---|---|---|---|---|---|---|
| log10 total ion current | +0.574 | +0.416 | +0.272 | +0.183 | +0.081 | +0.040 | **0.574** |
| precursor m/z | -0.104 | -0.526 | -0.637 | -0.647 | -0.596 | -0.511 | **0.647** |
| peak count | -0.411 | -0.266 | -0.131 | -0.106 | -0.094 | -0.116 | **0.411** |
| retention time | -0.093 | -0.306 | -0.364 | -0.355 | -0.320 | -0.288 | **0.364** |

### fragment_depth

| Covariate | NCE 15 | NCE 30 | NCE 45 | NCE 60 | NCE 75 | NCE 90 | max abs |
|---|---|---|---|---|---|---|---|
| log10 total ion current | +0.041 | +0.049 | +0.044 | +0.027 | +0.028 | +0.025 | **0.049** |
| precursor m/z | -0.111 | -0.340 | -0.525 | -0.615 | -0.658 | -0.678 | **0.678** |
| peak count | -0.000 | -0.123 | -0.091 | -0.075 | -0.082 | -0.102 | **0.123** |
| retention time | -0.131 | -0.237 | -0.301 | -0.341 | -0.363 | -0.383 | **0.383** |

### spectral_entropy

| Covariate | NCE 15 | NCE 30 | NCE 45 | NCE 60 | NCE 75 | NCE 90 | max abs |
|---|---|---|---|---|---|---|---|
| log10 total ion current | -0.334 | -0.140 | +0.012 | +0.096 | +0.148 | +0.201 | **0.334** |
| precursor m/z | -0.017 | +0.386 | +0.422 | +0.429 | +0.453 | +0.471 | **0.471** |
| peak count | +0.766 | +0.821 | +0.867 | +0.881 | +0.889 | +0.897 | **0.897** |
| retention time | +0.013 | +0.194 | +0.192 | +0.198 | +0.208 | +0.210 | **0.210** |

## Mixture identity (NC6 preview)

Kruskal-Wallis across mixtures at each energy. A significant result means trajectory shape carries batch structure.

| Endpoint | NCE 15 | NCE 30 | NCE 45 | NCE 60 | NCE 75 | NCE 90 |
|---|---|---|---|---|---|---|
| mu | p=0.779 | p=0.206 | p=0.170 | p=0.466 | p=0.480 | p=0.295 |
| spectral_entropy | p=0.641 | p=0.039** | p=0.075 | p=0.043** | p=0.034** | p=0.024** |

(`**` marks p < 0.05.)

## Findings

1. **Entropy is close to a peak-count statistic.** Spearman rho between spectral entropy and peak count runs +0.75 at NCE 15 to +0.89 at NCE 90. Since S <= ln(n) and n is set by RMassBank's formula-annotation success rather than by the detector, an entropy-based law would substantially be an annotation law. This is the strongest single argument against entropy as the primary endpoint, and it is stronger at full n than the master plan's sample suggested.

2. **mu carries a real and growing mass dependence.** rho(mu, precursor m/z) moves from -0.10 at NCE 15 to -0.68 at NCE 90. mu is already normalized by precursor m/z, so this is residual mass dependence, not the normalization showing through. This is exactly risk R4 ('the structure effect is precursor mass wearing a chemistry costume') and it fires **before** any modelling. Phase 2 must treat the mass-only baseline B2 as the real competitor, and kill criterion K5 is live.

3. **Abundance confounding is concentrated at low energy.** rho(mu, log TIC) is +0.53 at NCE 15 and decays to +0.02 by NCE 75. The master plan worried about abundance driving entropy at high energy; the measured pattern is the reverse for mu.

4. **Retention time is a moderate confounder for every endpoint** (|rho| up to 0.36 for mu). RT correlates with lipophilicity and therefore with structure, so this is partly a real chemical signal and partly co-elution. NC7 in Phase 2 must resolve which.

5. **Mixture identity does not confound mu, but does confound entropy.** mu shows no significant mixture effect at any energy (all p > 0.05). Entropy shows significant mixture effects at four of six energies. Another point for mu, and a specific warning that NC6 will fire for entropy-based analyses.
