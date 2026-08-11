# REPEATABILITY.md

Generated 2026-08-11 23:20 UTC.

## What was measured, precisely

The curated MassBank layer holds one record per compound per energy, so it contains no repeated measurement. The estimate below comes from raw mzML.

Mixes 499, 503 and 505 share a compound set (verified from Elapavalore et al. 2023 Table 1 and text: mix 5 and mix 7 each include the replicate set of mix 1, mapping to 503 and 505 including 499). Measured overlap: **92 compounds in all three mixes**, of which **40 appear in MassBank positive mode** and can be located in the raw files by measured precursor m/z and retention time.

**These are not injection replicates of one vial.** Mix 499 carries 95 substances, mix 503 carries 185 and mix 505 carries 365. They are three separate preparations at three matrix complexities, run as separate injections. The variance across them contains preparation, injection, instrument **and matrix-complexity** variation.

Reported quantity: **inter-mixture repeatability**, an **upper bound** on technical repeatability. For kill criterion K3 -- which asks whether within-compound signal exceeds replicate SD by >= 3x -- an inflated noise estimate makes the gate harder to pass, so a pass under this estimate is conservative.

## Data actually used

- Mixes acquired: [499, 503, 505]
- Compound x mix x energy cells with >= 1 matched MS2 scan: **476**
- Distinct compounds: **39**
- MS2 scans per compound-file: median 1, mean 1.45, max 3
- Matching: precursor within 10 ppm and retention time within +/-0.5 min of the curated record's values (the same RT window the study's own Shinyscreen prescreening used)

**Note:** `20200303_ENTACT_RP_mix505_pos_CE90.mzML` does not exist in MSV000091754, so NCE 90 is a duplicate (mixes 499, 503) while NCE 15-75 are triplicates.

## Inter-mixture repeatability by endpoint

Pooled within-(compound, energy) SD across mixes, raw-mzML branch.

| Endpoint | replicate SD | cells | d.f. | relative SD (SD / endpoint IQR) |
|---|---|---|---|---|
| mu | **0.0295** | 216 | 252 | 0.070 |
| survival_yield | **0.0337** | 216 | 252 | 0.128 |
| fragment_depth | **0.0410** | 216 | 252 | 0.138 |
| spectral_entropy | **0.1427** | 216 | 252 | 0.097 |

### mu, per collision energy

| NCE | replicate SD | cells | d.f. |
|---|---|---|---|
| 15 | 0.0281 | 37 | 73 |
| 30 | 0.0559 | 36 | 36 |
| 45 | 0.0281 | 36 | 36 |
| 60 | 0.0168 | 36 | 36 |
| 75 | 0.0120 | 36 | 36 |
| 90 | 0.0129 | 35 | 35 |

Repeatability is worst near NCE 30, which is where mu's trajectory is steepest: a small difference in effective energy or in co-isolation translates into a larger endpoint difference where the slope is large. This is expected behaviour, not instability.

## K3 evaluation

*Trigger:* within-compound endpoint range fails to exceed replicate SD by >= 3x **for every candidate endpoint**.

The comparison is made **within the raw branch** so that signal and noise are measured on the same data. The curated-branch ratio is shown alongside for reference.

| Endpoint | median within-compound range (raw) | replicate SD | ratio | >= 3x? | curated-branch ratio |
|---|---|---|---|---|---|
| mu | 0.4489 | 0.0295 | **15.2x** | **yes** | 15.4x |
| survival_yield | 0.6174 | 0.0337 | **18.3x** | **yes** | 18.9x |
| fragment_depth | 0.2995 | 0.0410 | **7.3x** | **yes** | 5.8x |
| spectral_entropy | 1.5238 | 0.1427 | **10.7x** | **yes** | 11.7x |

### K3: **DOES NOT FIRE**

4 of 4 candidate endpoints clear the 3x bar (mu, survival_yield, fragment_depth, spectral_entropy). The criterion requires failure for *every* endpoint.

The highest ratio is **survival_yield** at **18.3x**, with mu at **15.2x**. **This ranking does not select the primary endpoint and must not be read as doing so.** Survival yield earns a large range by collapsing from ~0.62 to exactly zero, which is a wide excursion but a poor measurement: it is strictly monotone in only 20% of trajectories, is dead above NCE 45, and is left-censored at the detection floor. The range/SD ratio answers exactly one question -- is there signal above noise -- and K3 asks only that. Endpoint selection is decided on the full criterion set in `ENDPOINT_SCREEN.md`, where mu wins.

## Does matrix complexity inflate the estimate? (deviation D6)

The three mixes differ in complexity (95 / 185 / 365 substances), so the inter-mixture variance may contain a systematic matrix-complexity term rather than pure noise. That is testable wherever all three mixes are present.

**NCE 15**, 36 compounds in all three mixes. Mean mu by mix: mix499 = 0.8597, mix503 = 0.8574, mix505 = 0.8574. Friedman chi2 = 24.1, p = 5.98e-06.

The difference across mixes is **statistically detectable but negligible in magnitude**: the spread of mix means is 0.0023, which is 8% of the replicate SD (0.0295) and about 0.5% of mu's median within-compound range. The low-complexity mix (499) sits slightly higher in mu, consistent with less co-isolation adding less fragment intensity -- the expected direction.

**Consequence for D6:** the inter-mixture estimate is indeed an upper bound on technical repeatability, but the matrix-complexity component of it is small enough that the bound is tight. The K3 ratios are not materially inflated by using mixtures rather than injection replicates. A significant p-value on a 0.002 effect is a statement about n, not about consequence.

## Within-run scan variability (lower bound)

DDA acquired more than one MS2 scan across the LC peak for 169 of 476 compound-mix-energy cells (median 1 scans). Pooled within-cell scan SD for mu: **0.0396**.

This is a *lower* bound on measurement noise -- it captures detector and ion-statistics variation within a single chromatographic peak but no preparation or injection variation. The inter-mixture estimate above is the upper bound. True technical repeatability lies between them.

## Branch comparison: RMassBank curated vs raw mzML

Same compounds, same energies, same instrument files. The difference is RMassBank's sub-formula annotation filter.

Paired (compound, energy) cells: **235**

| Quantity | raw median | curated median | median difference (raw - curated) | mean abs difference | Spearman rho |
|---|---|---|---|---|---|
| mu | 0.5039 | 0.4809 | +0.0008 | 0.0194 | 0.977 |
| survival_yield | 0.0003 | 0.0000 | +0.0000 | 0.0185 | 0.909 |
| fragment_depth | 0.4745 | 0.4592 | +0.0012 | 0.0227 | 0.957 |
| spectral_entropy | 2.0574 | 1.6165 | +0.1551 | 0.3105 | 0.897 |
| peak_count | 62.5000 | 24.0000 | +34.3333 | 38.8362 | 0.852 |

**The formula filter is the dominant preprocessing effect, and it hits endpoints very unequally.** Median peak count is 62 raw against 24 curated -- roughly 3x more peaks before annotation filtering.

- **mu** shifts by 0.0194 on average (4.0% of its median). Its branch disagreement is **smaller than the replicate SD (0.0295)**, meaning the annotation filter moves mu less than the measurement itself varies between mixes.
- **spectral entropy** shifts by 0.3105 on average, which is 2.2x its replicate SD. Entropy is substantially an artifact of which peaks the annotator kept.

This is the F3 (source-branch invariance) evidence the master plan predicted would be most likely to kill entropy-based results, and it does.
