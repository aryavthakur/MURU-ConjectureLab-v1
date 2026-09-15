# MURU-WUR-v2 vs FIORA-OS v0.1.0, ICEBERG 2.1 and GLACIER on the frozen mu endpoint: result

**Identifier:** `muru-v2-comparator-benchmark-1.0`, governed by `MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md`.
**Status:** EXECUTED. One look, exit 0. This document was written after the numerical outputs were committed.

## Record chain

All refs are published on `origin`:

| Step | Ref | Commit |
|---|---|---|
| Protocol freeze | `refs/muru-freeze/muru-v2-comparator-benchmark-1.0` | `c0e724e342ee37139a50999be2030bd8144b1346` |
| Predictions | `refs/muru-predictions/muru-v2-comparator-benchmark-1.0` | `2c291a2be28617083dab19b7dadcc617b1ace75b` |
| Pre-access record (published before measured data was opened; adds only `artifacts/comparator_benchmark/access/access_record.json`) | `refs/muru-access/muru-v2-comparator-benchmark-1.0` | `9ed02751cc1ff4e868afbe6ab0764555e53b333d` |
| Execution commit (clean tree) | | `2c291a2` |
| Result (adds only `artifacts/comparator_benchmark/result/*`) | `refs/muru-result/muru-v2-comparator-benchmark-1.0` | `156fb8777306f88cb00bce8e85d241464e662630` |

**Environment:** `/opt/miniconda3/bin/python3`, Python 3.13.12, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, RDKit
2026.03.5, macOS 26.1 arm64. `sys.flags.optimize == 0` and `PYTHONOPTIMIZE` was unset.

**Command:** `env -u PYTHONOPTIMIZE MURU_COMPARATOR_ONE_LOOK=1 /opt/miniconda3/bin/python3 scripts/comparator_benchmark/analysis.py`

**Execution record:** executed once, from 2026-09-15T01:09:56.978Z to 01:10:03Z UTC (`result/analysis_start_utc.txt`, `result/analysis_exit.txt`). There were no
post-access code, input or setting changes and no rerun.

## Population

- **1,327 compounds in 1,254 scaffold groups.** Key-list sha256 `dbdba9ca7edd4c6532b1e88b556f6fadcb582dd14d5c50a78f05c5bf04a52514`.
- 0 prediction-failure exclusions and 0 incomplete measurements, so all 1,327 compounds were scored.
- Every model was scored on the identical 2,654 (compound, rung) cells.

## Primary result (decisional)

Ratio = P1_MURU / P1_comparator; values below 1 favour MURU. Intervals come from a whole-scaffold-group bootstrap
(B = 10,000, seed 20260915), with the same replicate weights for all comparators.

| Model | P1 | Ratio MURU/comparator | 95% CI | Bonferroni 98.33% CI | Frozen decision | Ratio <= 0.95 |
|---|---|---|---|---|---|---|
| MURU-WUR-v2 `V2_TA_MORGAN_JOINT` | 0.1265 | | | | | |
| FIORA-OS v0.1.0 | 0.2046 | 0.619 | [0.593, 0.646] | [0.588, 0.652] | **MURU superior** | yes |
| ICEBERG 2.1 msg_simulation | 0.1621 | 0.781 | [0.748, 0.815] | [0.741, 0.823] | **MURU superior** | yes |
| GLACIER MassSpecGym | 0.1384 | 0.914 | [0.873, 0.958] | [0.864, 0.968] | **MURU superior** | yes (point estimate) |

**Supporting 95% intervals (MURU minus comparator):**

| Comparator | P1 difference | MRMSE difference | AF difference |
|---|---|---|---|
| FIORA-OS v0.1.0 | -0.078 [-0.085, -0.071] | [-0.075, -0.062] | [-0.286, -0.224] |
| ICEBERG 2.1 | -0.036 [-0.042, -0.029] | [-0.036, -0.024] | [-0.157, -0.098] |
| GLACIER | -0.012 [-0.018, -0.006] | [-0.0117, -0.0005] | [-0.067, -0.016] |

**Per-model summaries:**

| Model | MRMSE | Median compound RMSE | Q95 | AF (compound RMSE > 0.20) |
|---|---|---|---|---|
| MURU | 0.109 | 0.098 | 0.227 | 10.6% |
| FIORA-OS v0.1.0 | 0.178 | 0.164 | 0.363 | 36.2% |
| ICEBERG 2.1 | 0.140 | 0.125 | 0.290 | 23.4% |
| GLACIER | 0.116 | 0.097 | 0.268 | 14.8% |

## Secondary results (descriptive, never decisional)

**Per rung.** RMSE, ratio MURU/comparator, and mean signed residual (prediction minus measured):

| | MURU | FIORA-OS v0.1.0 | ICEBERG 2.1 | GLACIER |
|---|---|---|---|---|
| NCE 20 RMSE | 0.1616 | 0.1552 (ratio **1.041**) | 0.1848 (ratio 0.874) | 0.1558 (ratio **1.037**) |
| NCE 60 RMSE | 0.0769 | 0.2441 (ratio 0.315) | 0.1356 (ratio 0.567) | 0.1184 (ratio 0.649) |
| NCE 20 signed bias | -0.001 | +0.058 | +0.116 | +0.081 |
| NCE 60 signed bias | +0.008 | +0.198 | +0.084 | +0.066 |

**Structural novelty.** Frozen PR #7 quartiles of max similarity to MURU development compounds; P1 ratio
MURU/comparator; Q1 is the most novel.

| Bin | n | FIORA-OS v0.1.0 | ICEBERG 2.1 | GLACIER |
|---|---|---|---|---|
| Q1 [0.000, 0.281) | 351 | 0.525 | 0.694 | 0.767 |
| Q2 [0.281, 0.319) | 319 | 0.608 | 0.760 | 0.940 |
| Q3 [0.319, 0.364) | 333 | 0.670 | 0.814 | 0.970 |
| Q4 [0.364, 1.000) | 324 | 0.713 | 0.881 | 1.040 |

**Raw-NCE sensitivity.** Diagnostic only; it cannot affect ranking, inclusion or conclusions. The collision-energy
input is the numeric NCE (20 or 60), the convention of much of the MassSpecGym MSnLib training material.

| Comparator | P1 | Ratio MURU/comparator | 95% CI |
|---|---|---|---|
| ICEBERG 2.1 | 0.1176 | 1.076 | [1.029, 1.127] |
| GLACIER | 0.1022 | 1.238 | [1.181, 1.299] |

## Native precursor-peak disclosure

Share of predicted spectra that contain a native intact-precursor [M+H]+ peak:

| Model, condition | Share |
|---|---|
| FIORA-OS v0.1.0 primary | 100% |
| ICEBERG 2.1 primary | 88.4% |
| GLACIER primary | 84.6% |
| ICEBERG 2.1 raw-NCE sensitivity | 77.2% |
| GLACIER raw-NCE sensitivity | 61.6% |

- Missing precursor peaks come from the models' frozen native sparse output: both ms-pred predictors keep only their
  top 100 peaks (`--sparse-out --sparse-k 100`, enforced by upstream).
- No peak was restored, inserted or estimated. The native peak lists were passed unchanged, after the single frozen
  intensity inverse, to `external_multims2.spectrum_mu`.
- These rates were not used to change model inclusion.
- A dropped precursor carries at most the 100th-largest intensity. On the T3 examples, restoring it would have moved
  mu by at most 5.7e-4.

## Interpretation (at the strength the frozen rules support)

**1. Statistically demonstrated superiority, under the preregistered primary energy mapping.**
- All three Bonferroni 98.33% intervals lie wholly below 1.
- MURU-WUR-v2's pooled two-rung mu error is statistically lower than that of FIORA-OS v0.1.0, ICEBERG 2.1
  (msg_simulation) and GLACIER (MassSpecGym), on the common 1,327-compound population.
- For this benchmark the frozen decision is MURU superior against every comparator. No result is "no demonstrated
  difference" or "comparator superior".

**2. Practically at least 5% superiority.**
- **FIORA-OS v0.1.0 and ICEBERG 2.1:** the point ratio and the whole adjusted interval are below 0.95 (38% and 22%
  lower P1).
- **GLACIER:** the point ratio 0.914 meets the 0.95 descriptor. The adjusted interval [0.864, 0.968] still includes
  advantages smaller than 5%. So a 5% or larger advantage over GLACIER is the point estimate, not an
  interval-supported bound. The GLACIER MRMSE difference interval nearly reaches 0 ([-0.0117, -0.0005]).

**3. Where the advantage sits (descriptive).**
- The pooled advantage is carried by NCE 60. There MURU's RMSE is 0.077, against 0.118 to 0.244 for the comparators.
- At NCE 20, MURU is not better than FIORA-OS v0.1.0 or GLACIER (point ratios 1.04). It is better only than ICEBERG
  2.1 (0.87).
- All three comparators predict mu too high on average (they under-fragment), most strongly at NCE 60.
- Against GLACIER the advantage fades with chemical proximity to MURU's development set: 0.77 in the most novel
  quartile, 1.04 in the least novel.

**4. The energy-convention diagnostic points the other way, and it must be reported with the primary result.**
- With the numeric NCE as the collision-energy input, both ms-pred models have lower P1 than MURU (ICEBERG 2.1 ratio
  1.08 [1.03, 1.13]; GLACIER 1.24 [1.18, 1.30]).
- By the frozen rules this cannot change the primary decision, the ranking or the preferred mapping, and it is not a
  confirmatory result.
- It does show that the primary superiority over ICEBERG 2.1 and GLACIER is conditional on the documented
  model-interface energy mapping (eV = NCE × m/z / 500). With the input convention that dominates their MSnLib-derived
  training data, those checkpoints' spectra carry mu information that beats MURU on this population.
- The honest reading: much of the primary gap to the modern ms-pred models plausibly reflects an energy-input
  convention mismatch in the public checkpoints, not only a difference in predictive structure. This benchmark was
  not designed to establish that and does not.

**5. No state-of-the-art claim.**
- MURU beats all three comparators under the frozen primary rules. But the claim is limited to the specific public
  checkpoints: FIORA-OS v0.1.0 (not the current or NIST-trained FIORA), and the MassSpecGym-trained ICEBERG 2.1 and
  GLACIER.
- It is limited to their documented eV mapping, to [M+H]+ at fixed Orbitrap HCD NCE 20/60 on this MSnLib population,
  and to the mu endpoint, not full spectra.
- The preregistered diagnostic reverses the direction for both modern ms-pred models under an alternative, plausible
  input convention. So "state of the art" is not justified.
- The supported statement is: under the preregistered primary protocol, MURU-WUR-v2 predicted collision-energy-
  dependent fragmentation extent (mu) more accurately than all three public comparators. The margin over GLACIER is
  modest, and the conclusion for ICEBERG 2.1 and GLACIER depends on the energy-input convention.

## Result artifact hashes (SHA-256)

- `artifacts/comparator_benchmark/result/analysis.json` `e21037e154c3432d7403c19733be887fcb51d3c8bedaea449147511c48be922b`
- `artifacts/comparator_benchmark/result/analysis_stdout_stderr.log` `9c4a7a5767c3d3ccc7b9b5bdcbdbfbb84c55ed83ae5112199b53168d4ec74bdb`
- `artifacts/comparator_benchmark/result/analysis_start_utc.txt` `e1a80a0daaf4d51d020e446b54f43137f38b0d0f44e1bd74d59488ed76053347`
- `artifacts/comparator_benchmark/result/analysis_exit.txt` `b94f7b4da6fd2f3974af4567896f13bf2b12c9c71c258341be95e8c2da3b7beb`
- Prediction manifest `b39f643496bbf71591c7367428e69b86ea705e15c36a94d7860c747547e489c4`; `competitor_mu.csv` `c51041d4757d873a4db4837042680ad109037ab4dd7c9848a968a39ed801baad`;
  `analysis.py` `c6851db9cbca70eff2d10c47e35ed792fe8d07a2e2c6d8c2a6723b36f7ea1276`.
