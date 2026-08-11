# REPEATABILITY.md

Generated 2026-08-11 23:11 UTC.

## What was measured, precisely

The curated MassBank layer holds one record per compound per energy, so it contains no repeated measurement. The estimate below comes from raw mzML.

Mixes 499, 503 and 505 share a compound set (verified from Elapavalore et al. 2023 Table 1 and text: mix 5 and mix 7 each include the replicate set of mix 1, mapping to 503 and 505 including 499). Measured overlap: **92 compounds in all three mixes**, of which **40 appear in MassBank positive mode** and can be located in the raw files by measured precursor m/z and retention time.

**These are not injection replicates of one vial.** Mix 499 carries 95 substances, mix 503 carries 185 and mix 505 carries 365. They are three separate preparations at three matrix complexities, run as separate injections. The variance across them contains preparation, injection, instrument **and matrix-complexity** variation.

Reported quantity: **inter-mixture repeatability**, an **upper bound** on technical repeatability. For kill criterion K3 -- which asks whether within-compound signal exceeds replicate SD by >= 3x -- an inflated noise estimate makes the gate harder to pass, so a pass under this estimate is conservative.

## Data actually used

- Mixes acquired: [499, 503]
- Compound x mix x energy cells with >= 1 matched MS2 scan: **438**
- Distinct compounds: **38**
- MS2 scans per compound-file: median 1, mean 1.46, max 3
- Matching: precursor within 10 ppm and retention time within +/-0.5 min of the curated record's values (the same RT window the study's own Shinyscreen prescreening used)

**Note:** mix 505 is absent from this run, so the structure is a duplicate rather than a triplicate.

## Inter-mixture repeatability by endpoint

Pooled within-(compound, energy) SD across mixes, raw-mzML branch.

| Endpoint | replicate SD | cells | d.f. | relative SD (SD / endpoint IQR) |
|---|---|---|---|---|
| mu | **0.0292** | 215 | 215 | 0.080 |
| survival_yield | **0.0293** | 215 | 215 | 0.156 |
| fragment_depth | **0.0385** | 215 | 215 | 0.142 |
| spectral_entropy | **0.1260** | 215 | 215 | 0.085 |

### mu, per collision energy

| NCE | replicate SD | cells | d.f. |
|---|---|---|---|
| 15 | 0.0242 | 36 | 36 |
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
| mu | 0.4505 | 0.0292 | **15.4x** | **yes** | 15.6x |
| survival_yield | 0.5767 | 0.0293 | **19.7x** | **yes** | 21.8x |
| fragment_depth | 0.2857 | 0.0385 | **7.4x** | **yes** | 6.2x |
| spectral_entropy | 1.5238 | 0.1260 | **12.1x** | **yes** | 13.3x |

### K3: **DOES NOT FIRE**

4 of 4 candidate endpoints clear the 3x bar (mu, survival_yield, fragment_depth, spectral_entropy). The criterion requires failure for *every* endpoint. Best performer: **survival_yield** at **19.7x**.

## Within-run scan variability (lower bound)

DDA acquired more than one MS2 scan across the LC peak for 158 of 438 compound-mix-energy cells (median 1 scans). Pooled within-cell scan SD for mu: **0.0403**.

This is a *lower* bound on measurement noise -- it captures detector and ion-statistics variation within a single chromatographic peak but no preparation or injection variation. The inter-mixture estimate above is the upper bound. True technical repeatability lies between them.

## Branch comparison: RMassBank curated vs raw mzML

Same compounds, same energies, same instrument files. The difference is RMassBank's sub-formula annotation filter.

Paired (compound, energy) cells: **234**

| Quantity | raw median | curated median | median difference (raw - curated) | mean abs difference | Spearman rho |
|---|---|---|---|---|---|
| mu | 0.5000 | 0.4803 | +0.0009 | 0.0190 | 0.978 |
| survival_yield | 0.0003 | 0.0000 | +0.0000 | 0.0193 | 0.907 |
| fragment_depth | 0.4756 | 0.4585 | +0.0012 | 0.0219 | 0.956 |
| spectral_entropy | 2.0595 | 1.6170 | +0.1591 | 0.3110 | 0.897 |
| peak_count | 62.5000 | 24.0000 | +33.0000 | 38.6368 | 0.858 |

**The formula filter is the dominant preprocessing effect, and it hits endpoints very unequally.** Median peak count is 62 raw against 24 curated -- roughly 3x more peaks before annotation filtering.

- **mu** shifts by 0.0190 on average (4.0% of its median). Its branch disagreement is **smaller than the replicate SD (0.0292)**, meaning the annotation filter moves mu less than the measurement itself varies between mixes.
- **spectral entropy** shifts by 0.3110 on average, which is 2.5x its replicate SD. Entropy is substantially an artifact of which peaks the annotator kept.

This is the F3 (source-branch invariance) evidence the master plan predicted would be most likely to kill entropy-based results, and it does.
