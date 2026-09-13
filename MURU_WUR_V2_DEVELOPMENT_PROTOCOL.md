# MURU-WUR-v2 development protocol

**Identifier:** `wur-v2-dev-1.0`
**Status:** FROZEN before any v2 candidate comparison. Amendments are appended in section 16 and never rewrite earlier text.
**Parent state:** `fable/wur-stage2-muru-development` at `17027e1` (MURU-WUR-v1 final candidate `V1B_RIDGE_TIERA`, Stage 3 executed).
**Registry:** `MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md`. **Run state:** `MURU_V2_RUN_STATE.md`.
**Generation label:** everything produced under this document is MURU-WUR-v2 development evidence. Nothing in it is external validation.

**Result information visible when this was written:** all v1 development, HOLD and Stage 3 results (Stage 3 per-compound RMSE distributions included); the identity-only v2 population and partitions; descriptive endpoint scale of the v2 population (per-rung between-compound SD of mu, within-compound range). No v2 model had been fitted.

## 1. Question and principle

Build the simplest MURU that captures most of the practically available improvement over v1 and generalizes under chemically difficult splits. Stop when added complexity yields diminishing scientific returns. Heuristic reading of relative P1 gains over the refitted Tier A baseline: below 2 percent usually not worth new complexity; 2 to 5 percent useful if simple, stable or tail-reducing; 5 to 10 percent strong; above 10 percent major. These are development heuristics, not statistical thresholds, and no model is tuned toward them.

## 2. Identity, parents, stereochemistry, tautomers

- Identity unit: connectivity key = InChIKey first block of the parent structure (`muru.wur_v2.identity`). Stereoisomers and E/Z isomers share it. Parent = largest organic fragment, neutralized where a neutral form exists; permanent cations keep their charge. On the exposed data the parent step changes no key (0 mismatches).
- Representative structure of a key: LCSB SMILES for LCSB-primary keys; the lexicographically first deposited WUR SMILES otherwise (v1 D1). All v2 molecular representations are stereo-agnostic (Tier A, Morgan without chirality), so the choice of stereoisomer does not change features.
- Tautomers: the standard InChI first block already merges mobile-H tautomers it recognizes; no further tautomer union is applied. The strict grouping (section 4) absorbs residual near-identity.

## 3. Endpoint, energy coordinate, aggregation, missingness

- Endpoint: `features.mu` at the base cell (relative cutoff 0, precursor included, raw intensities, precursor match 10 ppm, declared precursor m/z). Unchanged from v1.
- Replicate aggregation (D-AGG): WUR archive copies (same peak-list hash, scan number and creation date) collapse to one acquisition; a (key, energy) value is the median over distinct acquisitions. LCSB: the corpus value (one record per key and energy). Isomer acquisitions under one key are aggregated, as v1 did, and flagged.
- Energy coordinate (primary): LCSB nominal NCE; pooled rungs 30, 45, 60, 75, 90; `ENERGY_SCALE = 30`. WUR is read at `T(E) = -5.95552603907965 + 0.8618030610784555 E` by PCHIP on its own six-rung ladder. The map is frozen and never refit. E = 15 never enters a pooled fit.
- Primary trajectory copy: LCSB for the 124 keys measured on both instruments, WUR otherwise. Both copies are kept for Experiment 5.
- Native secondary: WUR compounds are predicted at `E_LCSB = (E_WUR - a) / b` for each measured WUR rung and scored against the measured native mu, with no interpolation of outcomes. A predicted energy outside the training profile's support is flagged, not silently clipped, and the flagged fraction is reported.
- Missingness: a compound is scored on its observed aligned rungs (1,304 compounds have 5, 21 LCSB compounds have 4). No imputation.

## 4. Grouping and partitions (frozen in `artifacts/wur_v2/folds.json`)

- Primary grouping: Bemis-Murcko scaffold of the stereo-stripped parent; an acyclic parent is its own group (765 groups on 1,325 compounds). Groups are never split.
- **PRIMARY**: one 5-fold partition of whole groups, largest group first into the smallest fold, seed 20260920. Every compound is held out exactly once; primary metrics are computed on the pooled out-of-fold predictions of all 1,325 compounds.
- **PARTITION_S1, PARTITION_S2**: same rule at seeds 20260921, 20260922. They assess partition instability and are never pooled with PRIMARY as extra samples.
- **STRICT**: 5 folds of whole strict structural clusters (single-linkage components of Morgan-count Tanimoto >= 0.55 merged with scaffold groups; 558 clusters, largest 216), seed 20260923.
- **GIANT**: leave-benzene-group-out. The 183-compound `c1ccccc1` group is 13.8 percent of the population and sits whole in fold 0 of every grouped partition with 82 other compounds; it is never split to balance folds. GIANT trains on the other 1,142 compounds and scores the 183.
- **RANDOM**: compound-level 5-fold, seed 20260924. A leakage diagnostic only; never a primary or admission result.
- **Source strata**: pooled OOF results split by primary source (LCSB 439, WUR 886) and, as a transfer stress test, train-on-one-source/score-the-other, which confounds source with chemistry and is read only descriptively.
- Inner folds: 4 grouped folds on the same grouping column within a training set, seed 20260930 + outer fold index.

## 5. Nesting: everything learned inside the training boundary

For each outer training set:

1. The shared profile Phi and scale labels log g are fit by the frozen v1 collapse (`discovery.estimate.fit_collapse`: 3 alternations, 60 isotonic knots on log u, log g grid [-1.6, 1.6] x 241, unit geometric mean over the training compounds, curvature weights) on training compounds only.
2. Hyperparameters are chosen by inner grouped 4-fold CV in which **each inner training set refits its own collapse**, the candidate predicts inner-validation trajectories through the inner Phi, and the selection loss is pooled trajectory squared error. Outer-collapse labels are never used as ground truth for inner-validation compounds. (v1 selected alpha on outer-collapse log g labels; Experiment 1 measures whether that approximation matters.)
3. Standardization, fingerprint vocabulary handling, residual targets, kernels, neighbour sets, trust targets and trust calibration are built from the training set only. Residual targets for two-stage models are cross-fitted inside the training set.
4. The held-out compound is predicted from its structure (and acquisition-domain metadata where a model declares it) only.

A diagnostic that reads a held-out compound's own spectra (an oracle scale, an observed-shape fit) is labelled ORACLE and is never a candidate.

## 6. Metrics (exact estimands)

With `e_iE` the prediction error at an observed rung, `L_i = mean_E e_iE^2`, `RMSE_i = sqrt(L_i)`:

| Id | Estimand | Definition |
|---|---|---|
| **P1** (primary) | pooled trajectory RMSE | `sqrt(sum_{i,E} e_iE^2 / N_cells)` over pooled OOF cells of the partition |
| P1_ratio, P1_diff | candidate vs reference | `P1_c / P1_r`, `P1_c - P1_r` on the same cells |
| MRMSE | mean individual-compound RMSE | `mean_i RMSE_i`; its paired difference is a different estimand from P1_diff |
| MED, Q90, Q95, CVaR95 | distribution and tail | median, 90th and 95th percentiles of `RMSE_i`; mean of the worst 5 percent |
| **AF** | absolute development failure | fraction of compounds with `RMSE_i > 0.20` |
| AF_max | single-rung failure | fraction with `max_E |e_iE| > 0.30` |
| S4 | historical relative catastrophe | fraction with `RMSE_i > 2 * RMSE_i(B0)`, B0 refit in the same training set |
| S1 | per-rung RMSE | pooled by rung |
| P1_cw | compound-weighted P1 | `sqrt(mean_i L_i)`; sensitivity to the 21 four-rung compounds |

**Absolute failure tolerance, derivation (a development/engineering tolerance, not a physical constant).** The v2 population's per-rung between-compound SD of mu is 0.210, 0.197, 0.170, 0.150, 0.137 at E30 to E90, pooled 0.175: that is the RMSE of predicting each rung's population mean, the no-information level. The median within-compound excursion of mu across E30 to E90 is 0.26. The measured repeatability scale is 0.03 (inter-mixture, worst 0.056 at E30) and the cross-instrument RMSD after the map 0.056. A trajectory RMSE above 0.20 is therefore worse than a no-information prediction for that compound, about 77 percent of a typical trajectory's entire movement, and 4 to 7 times measurement variation: the prediction is not usable for choosing an energy or anticipating precursor survival. A single-rung error above 0.30 exceeds the largest per-rung population SD by more than 40 percent and the median whole-trajectory excursion. Historical rates for orientation (visible when set): Stage 3 V1B 9.4 percent above 0.20, B0 21.3 percent. The thresholds are frozen here and are not revisited after any v2 result.

## 7. Uncertainty

- **Primary comparison interval:** cluster bootstrap over PRIMARY scaffold groups of the pooled OOF predictions, B = 2,000, seed 20260925, percentile 95 percent intervals. Inside every replicate the resampled cells recompute P1 of candidate and reference, their difference and ratio; MRMSE difference and AF difference are recomputed from the same resample and reported as separate estimands. These intervals condition on the fitted fold models (they do not propagate refitting variance) and are labelled conditional descriptive uncertainty.
- STRICT, PARTITION_S1/S2, GIANT and source strata are reported as point estimates with the same bootstrap where a stratum has at least 50 groups.
- Fold-level standard errors, paired t-tests over folds, and nominal fold counts are not used.
- Search bias: every arm run on PRIMARY is ledgered; the selected candidate's development gain is described as optimistic by an unknown amount proportional to the number of arms compared.

## 8. Reference arms (refit under this protocol on every partition)

| Arm | Definition |
|---|---|
| B0 | per-rung training mean |
| B1 | collapse + isotonic regression of log g on precursor m/z |
| **TA_RIDGE** (the fair v1-family baseline) | collapse + ridge of log g on the 12 Tier A descriptors scaled by `protocol.SCALE`, curvature sample weights, alpha from {0.01, 0.1, 1, 10, 100} by nested trajectory-loss inner CV |
| TA_RIDGE_V1SEL | TA_RIDGE with v1's alpha selection (outer labels, weighted log g loss); Experiment 1 only |
| V1_FROZEN | the historical V1B fit (DEV2B + HOLD, alpha 1.0) used as a fixed model; reported on formerly sealed compounds only, for continuity |

## 9. Representation and model families, fixed in advance

- **TierA**: the 12 v1 descriptors.
- **ION_ENV** (Experiment 7): at most 12 incremental SMARTS-derived counts or graph distances describing basic-site types (aliphatic amine, aniline N, amide N, pyridine-type aromatic N, pyrrole-type N, amidine/guanidine), carbonyl classes (ester/lactone, acid, ketone/aldehyde, amide), sulfonyl/phosphoryl groups, permanent cation, the topological distance from the most basic site to the nearest labile bond, and the fraction of heavy atoms in the largest aromatic system. SMARTS are audited on exposed structures before any fit; a feature is dropped before fitting if it is constant in more than 97 percent of compounds, duplicates another feature exactly, or has in-sample R^2 > 0.90 on Tier A plus the rest of the block (structure-only checks). Any feature added after inspecting residuals is ledgered as such.
- **MORGAN**: RDKit Morgan radius 2, 2,048 hashed counts, no chirality, `log1p` transform, no frequency filter and no supervised bit selection.
- **ALT** (Experiment 9, the single controlled alternative metric): hashed atom-pair counts (2,048, `log1p`). MACCS (167 keys) is a cheap control reported alongside.
- **Models:** ridge (alpha grid {0.1, 0.3, 1, 3, 10, 30, 100, 300}); Tier A + fingerprint joint ridge with a Tier A block standardized on the training set and the fingerprint block weighted by w in {0.1, 0.3, 1} (alpha x w grid); two-stage Tier A ridge plus fingerprint ridge on cross-fitted Tier A residuals; kernel ridge with the MinMax (count Tanimoto) kernel (alpha grid {0.01, 0.03, 0.1, 0.3, 1}); k-nearest-neighbour residual correction (k = 10, similarity-weighted, training neighbours only, cross-fitted residuals). Every grid is inner-CV selected with trajectory loss.
- Negative control: MORGAN with fingerprint rows permuted across training compounds (5 permutations), full pipeline.

## 10. Experiment sequence and search budget

| Exp | Content | Budget |
|---|---|---|
| 1 | v1 reproduction from committed artifacts; estimand audit; corrected cluster bootstrap on Stage 3 predictions; old vs new intervals; TA_RIDGE vs TA_RIDGE_V1SEL | reproduction only |
| 2 | empirical repeatability and scale identifiability (LCSB inter-mixture repeat-A/B; cross-instrument pairs; WUR isomer groups; grid-boundary and flat-profile flags) | diagnostic |
| 3 | derivative amplification: finite-difference sensitivity of the training-fold profile times TA_RIDGE OOF scale error vs observed rung error | diagnostic |
| 4 | survival / fragment-depth decomposition of OOF errors, precursor-only spectra handled as undefined depth | diagnostic |
| 5 | acquisition and ion effects: paired cross-instrument residuals, source x mass, adduct strata, equivalence bounds | diagnostic |
| 6 | learning curves: B1, TA_RIDGE, MORGAN ridge at 25/50/75/100 percent of training groups (3 subsample seeds below 100), PRIMARY, STRICT, RANDOM | 3 arms |
| 7 | TierA + ION_ENV ridge | 1 arm |
| 8 | MORGAN ridge (A), TierA+MORGAN joint (B), TierA then MORGAN residual (C), MinMax kernel ridge (D), permutation control | 4 arms + control |
| 9 | ALT atom-pair ridge, MACCS ridge, kNN residual on the best structural metric | 3 arms |
| 10 | trust: individual signals, then at most one small penalized model | see section 11 |

Total candidate arms on PRIMARY before the first decision gate: at most 12 plus references and controls. Optional phases (shape, quantum pilot, pretrained encoder, direct trajectory model) require the gate conditions of section 13 and a ledger entry stating the admission reason before they run.

## 11. Trust evaluation

- Pre-measurement signals only, all computed from training data and the held-out structure: maximum MinMax similarity to the training set (Morgan counts); ridge leverage on the standardized Tier A design; Mahalanobis distance to the training Tier A distribution; disagreement |log g(TierA) - log g(best structural model)|; predicted profile sensitivity `sqrt(mean_E [u Phi'(u)]^2)` at the predicted scale (finite differences of the training Phi); domain flag (adduct not [M+H]+ or precursor m/z outside the training range).
- Trust targets (per-compound RMSE and AF) for training compounds are produced by inner cross-fitting within each outer training set; the trust model is trained on those and evaluated on outer held-out compounds. No held-out spectrum property enters a trust input.
- A learned trust model is at most a ridge on log(RMSE + 0.01) and an L2 logistic model for AF, on at most the six signals above.
- Evaluation: risk-coverage curves; P1, MRMSE and AF among retained compounds at 90, 80, 70 percent coverage; AF PR-AUC with prevalence; Brier score, calibration slope and intercept; the same under STRICT and source strata. Always against constant risk (random rejection), distance-only, leverage-only and disagreement-only. If a single signal matches the learned model within its interval, the single signal is used. Full-population accuracy and coverage are always reported next to any selective number.

## 12. Candidate admission and selection

A representation or model is **admitted** as a v2 candidate only if, against TA_RIDGE on the same cells:

1. PRIMARY P1_ratio <= 0.98 and the cluster-bootstrap 95 percent upper bound of P1_ratio < 1.00;
2. P1_ratio < 1.00 on PARTITION_S1, PARTITION_S2, STRICT, both primary-source strata and the non-benzene stratum, and P1_ratio <= 1.02 on GIANT;
3. MRMSE is also lower, and AF is not higher by more than 1.0 percentage point (point estimates);
4. the permutation control (where applicable) loses to the unpermuted arm and does not beat TA_RIDGE.

Improvement on RANDOM without improvement on PRIMARY and STRICT is never sufficient.

**Selection.** Among admitted candidates, order by PRIMARY P1. Complexity order: B1 < TA_RIDGE < TierA+ION_ENV < single-fingerprint ridge < joint or two-stage fingerprint models < kernel models < anything with a second profile parameter, a learned encoder or a direct trajectory head. The final point model is the simplest admitted candidate whose PRIMARY P1 is within 1.0 percent (relative) of the best admitted P1, unless the more complex model reduces AF by at least 2 percentage points. A trust mechanism is retained (Route B) only if at 80 or 90 percent coverage it lowers retained AF by at least 25 percent relative to the distance-only rule at the same coverage, with a bootstrap interval excluding no improvement, and its calibration is disclosed. If nothing is admitted, the v2 point model is TA_RIDGE refit on the v2 population (Outcome C) and any trust finding stands on its own.

## 13. First decision gate and optional phases

After Experiments 1 to 10 a synthesis document answers: is more of g encoded in local structure; is Tier A sample- or representation-limited; does local chemistry improve PRIMARY P1 meaningfully; can bad predictions be identified pre-measurement; is E30 error mostly scale sensitivity; is the shared profile shape now the main limitation.

- Shape phase (one residual basis, orthogonalized to the scale tangent, scale + asymptote, scale + width comparators) runs only if (a) Experiment 3 leaves more than 25 percent of the rung-error energy gradient unexplained by scale sensitivity or (b) an ORACLE one-parameter shape fit on OOF data improves pooled trajectory error by at least 5 percent after the best scale model. It stops if the oracle gain is below 3 percent or the coefficient's held-out predictability (R^2) is below 0.10.
- Quantum/ion-state pilot runs only if ION_ENV is admitted or shows a signal that fingerprints do not absorb (joint model gain over MORGAN >= 2 percent).
- Pretrained encoder runs only if a fingerprint model is admitted with a gain >= 5 percent and the learning curve for it is still rising at 100 percent.
- Direct trajectory model runs only if the shape conditions hold and the scale model's residuals after the best representation remain energy-structured.

## 14. Ledger

Append-only JSON lines in `artifacts/wur_v2/ledger/ledger.jsonl`, one record per substantive experiment or arm, never edited, with: `experiment_id`, `generation` (v2-G0 diagnostics, v2-G1 representations, v2-G2 trust, v2-G3 optional), `hypothesis`, `parent_model`, `code_sha`, `tree_dirty`, `population_sha256`, `partition` and its `assignment_sha256`, `representation`, `endpoint`, `hyperparameters_and_space`, `tuning_process`, `compute_seconds`, `results`, `uncertainty`, `tail_metrics`, `interpretation`, `decision` (accepted / rejected / diagnostic), `reason`, `informed_later_decisions`. Full outputs live in `artifacts/wur_v2/expNN/`.

## 15. Stop rules

Stop broad model escalation when any holds: independent-repeat variability dominates the remaining error; scales are frequently unidentifiable; local structural models fail PRIMARY and STRICT; MORGAN and one alternative fail admission; a shape oracle gains under 3 percent; a shape coefficient is unpredictable; the quantum pilot adds nothing beyond fingerprints; a pretrained encoder adds nothing beyond fingerprints; trust does not beat a novelty rule; remaining gains are about 1 percent and unstable; a gain depends on the benzene group or one source; complexity rises much faster than value. Stop before external validation if the candidate is not clearly worth a new dataset, the eligible external population is too small or overlapping, the observable or energy mapping is incompatible, external outcomes were exposed, or licensing is unresolved.

## 16. Amendments

### A-1, 2026-09-12, after Experiments 1-9 predeclared arms, before the arms below run

**What changed.** Two arms are added inside the section 10 budget (12 arms; 8 used): `TA_ATOMPAIR_JOINT` (the protocol's joint ridge with the atom-pair block in place of Morgan) and `TA_ION_MORGAN_JOINT` (the joint ridge with Tier A plus ION_ENV as the standardized base block and Morgan as the weighted block). Same grids, same nesting, same admission rule.

**Why.** The predeclared ALT arm compares atom pairs with Morgan only as single-block ridges; the leading arm is the Tier A + fingerprint joint ridge, so the like-for-like metric question is the atom-pair joint ridge. The optional quantum pilot gate (section 13) needs the gain of ION_ENV beyond Morgan, which no predeclared arm measures.

**Result information visible.** PRIMARY/STRICT/GIANT results of EXP07 (ION_ENV admitted, 2.2 percent), EXP08A-D (Morgan ridge 5.1, joint 11.1, two-stage 10.7, MinMax kernel 8.9 percent), EXP09A-C (atom-pair ridge 5.9 percent, MACCS not admitted, kNN residual 6.9 percent), the corrected permutation controls, and the Experiment 6 learning curves.

**Effect on earlier interpretation.** None on completed arms. The two added arms are exploratory with respect to the visible results and their outcome is read with that caveat: an added arm is selected over a predeclared one only if it is better by more than the section 12 one-percent practical margin.

### A-2, 2026-09-12, after Experiments 10 and 11, before the arm below runs

**What changed.** One shape arm, `JOINT_PLUS_SHAPE` (arm 11 of the 12-arm budget), is registered: the TA_MORGAN_JOINT scale model plus one structure-predicted, tangent-orthogonal shape coefficient, fully nested (basis from training residuals, coefficients cross-fitted inside the training set, coefficient ridge selected by the inner trajectory loss). It is **selected over TA_MORGAN_JOINT only if** (i) it passes section 12 against TA_RIDGE, (ii) its PRIMARY P1 is at least 2 percent below TA_MORGAN_JOINT with the cluster-bootstrap 95 percent upper bound of that ratio below 1.00, (iii) its ratio to TA_MORGAN_JOINT is below 1.00 on PARTITION_S1, PARTITION_S2, STRICT, GIANT and both source strata, and (iv) its AF is not higher than TA_MORGAN_JOINT's. Otherwise the one-scale architecture stays and the shape phase closes.

**Why.** Experiment 11's held-energy oracle, which the Experiment 11 ledger entry named as the oracle gate, fails (-12.7 percent): a tilt coefficient estimated from four rungs of a trajectory whose scale is itself mispredicted extrapolates badly to an end rung. That test answers whether shape can be measured from partial trajectories, not whether it can be predicted from structure. The prompt's own sequence for the latter is reproducibility, then predictability, then unseen-compound trajectory gain: the coefficient reproduces across independent preparations (r = 0.77, n = 26) and instruments (r = 0.85, n = 119) and is predictable from structure at out-of-fold R^2 = 0.18 (above the 0.10 bar). Only the unseen-compound test is missing, so one nested arm is run, with a bar raised above section 12 because a second profile parameter is the most complex class.

**Result information visible.** Everything in A-1 plus Experiments 10 and 11, including an exploratory, not fully nested predicted-shape estimate of P1 0.1132 against 0.1160 (the training coefficients for fold f came from models trained on fold f's labels).

**Effect on earlier interpretation.** The frozen section 13 stop reading ("oracle gain below 3 percent") is recorded as having fired on the held-energy oracle; A-2 overrides it for one arm only, disclosed here. No completed result changes.
