# MURU-WUR-v2 scientific red-team review of the first decision gate

**Commit under review:** 52967a0 (branch claude/muru-wur-v2-generation-b2ffa1). **Reviewer role:** scientific red team. The task was to try to show that the claimed v2 improvement (TA_MORGAN_JOINT, PRIMARY P1 0.1160 vs refitted TA_RIDGE 0.1305, ratio 0.889) is chemically empty, an artifact, or overstated.

**Bottom line.** The gain is real at the level the decision gate measures it. It reproduces, it disappears under permutation, it is not a source or adduct artifact, and it survives a refit of Tier A with nonlinear size terms. Three things are overstated.

1. **What the gain is made of.** About half of it (53 percent on PRIMARY, 67 percent on STRICT) and most of the absolute-failure reduction come from atom-type composition plus smooth size terms. That is hybridization, branching, aromatic substitution and chlorine counts, with no bonded-neighbour connectivity. Radius-1 environments reproduce all of the gain, so radius 2 adds nothing.
2. **How far it transfers.** The connectivity-specific part is 5.5 percent on PRIMARY and 2.6 percent on STRICT. It falls toward zero for structurally novel compounds.
3. **What it implies for an external test.** Nothing in development tests a fixed-eV QTOF regime. Reweighting development gains to the MultiMS2 structure distribution predicts about 7 to 8 percent, and that is an upper bound on the retained gain because it ignores the regime change.

A separate finding: the MultiMS2 scaffold-new population is not natural-product-like. Its structures are drug-like screening compounds.

Everything here is development evidence on the same 1,325 exposed compounds. Red-team arms were chosen after seeing results and are diagnostics, not candidates.

## 1. What I ran

No tracked file was modified. No write went to `artifacts/wur_v2`. All scripts and outputs are in `docs/wur_v2_reviews/redteam_scratch/`.

| Script | Content | Compute |
|---|---|---|
| `rt_a_cached.py` -> `rt_a_cached.json` | Cached OOF predictions only. Concentration of the P1 gain by scaffold group and strict cluster, max MinMax similarity of each held-out compound to its own training fold, what the log g correction (joint minus TA) correlates with, grouped-CV predictability of source/adduct/formerly-sealed from Morgan vs Tier A, SMARTS chemical classes, NP-likeness strata, arm-selection optimism, per-rung ratios | seconds |
| `rt_b_size_ladder.py` -> `rt_b_size_ladder.json`, `pred_*.parquet` | **The one nested diagnostic.** A ladder of ridge arms through the frozen engine (`engine.run_cv`, inner collapse refits, trajectory-loss selection, direct engine call so nothing is cached), PRIMARY and STRICT. All arms share the same collapse fits | about 30 s total |
| `rt_c_transfer.py`, `rt_f_reweight2d.py` | Concentration null (TA vs B1), class exclusions, noise floor against the joint model, and an outcome-blind structural comparison with the MultiMS2 scaffold-new population, followed by a reweighting of development gains to that population's similarity and mass distribution | seconds |
| `rt_d_halogen.py`, `rt_e_r0_content.py` | Gain by halogen type and mass per heavy atom; descriptive content of the radius-0 atom-type block | seconds |

**MultiMS2 inputs.** For MultiMS2 I read only the `SMILES` and `INCHIAUX` columns of the peak-free identity TSVs in `data/external/multims2_metadata/`. I restricted them to the 1,165 step-10 scaffold-new keys listed in `artifacts/wur_v2/external_census/multims2_census.json`. All matched a parseable SMILES. No peak, intensity, record count or QC field was used. This is the same class of information the outcome-blind census already computed (the census reports a Tanimoto median of 0.35).

**Engine sanity.** The TA_RIDGE rerun reproduces the cached PRIMARY P1 of 0.1305 and STRICT P1 of 0.1327 exactly, with the same selected alphas.

## 2. Question 1: is the Morgan gain just size, mass or energy-transfer modelling?

### 2.1 The ladder

All ratios are against the cached TA_RIDGE on the same cells. "Captured" is the share of the joint model's P1 reduction that the arm reproduces.

| Arm (nested, inner-CV selected) | PRIMARY P1 | ratio vs TA [95% cluster CI] | captured | AF | STRICT P1 | STRICT ratio | captured | STRICT AF |
|---|---|---|---|---|---|---|---|---|
| TA_RIDGE (cached) | 0.1305 | 1 | 0 | 0.103 | 0.1327 | 1 | 0 | 0.109 |
| TA standardized, joint's wider alpha grid | 0.1304 | 0.999 [0.997, 1.001] | 0.01 | 0.102 | 0.1324 | 0.998 | 0.03 | 0.109 |
| TA + smooth size (log m/z, m/z^2, log atoms, heavy atoms and square, nH, nC, m/z per heavy atom) | 0.1273 | 0.975 [0.963, 0.987] | 0.22 | 0.091 | 0.1298 | 0.978 | 0.29 | 0.101 |
| TA full quadratic expansion (90 terms) | 0.1263 | 0.967 [0.952, 0.982] | 0.29 | 0.091 | 0.1306 | 0.984 | 0.21 | 0.112 |
| TA + Morgan radius 0 (48 atom-type counts) joint | 0.1245 | 0.953 [0.937, 0.971] | 0.42 | 0.085 | 0.1276 | 0.962 | 0.52 | 0.097 |
| TA + smooth size + Morgan radius 0 joint | 0.1228 | 0.941 [0.922, 0.960] | 0.53 | 0.071 | 0.1261 | 0.950 | 0.67 | 0.088 |
| TA + Morgan radius 1 joint | 0.1152 | 0.882 [0.857, 0.908] | 1.06 | 0.060 | 0.1217 | 0.917 | 1.12 | 0.070 |
| **TA_MORGAN_JOINT (radius 2, candidate, cached)** | **0.1160** | **0.889** | 1 | **0.063** | **0.1228** | **0.926** | 1 | **0.076** |

The candidate against the size + radius-0 arm is 0.945 [0.925, 0.964] on PRIMARY and 0.974 on STRICT (point estimate). The candidate against the radius-1 arm is 1.007 [0.993, 1.020].

### 2.2 Reading

1. **Smooth nonlinear size terms are a small part.** They give 2.5 percent on PRIMARY and 2.2 percent on STRICT, about a fifth to a quarter of the gain. A full quadratic Tier A gives 3.3 and 1.6 percent. The pure "size/energy transfer that a linear Tier A misses" hypothesis explains at most about a quarter of the gain, so it is refuted as the main explanation. Consistent with this, the joint model's out-of-fold log g correction (sd 0.20 log units) has in-sample R^2 0.04 against a set of smooth size functions, and 0.06 after adding Tier A, Fsp3 and stereocentre count (`rt_a_cached.json`, `delta_logg_joint_minus_TA`). The hyperparameter-asymmetry explanation (joint model has 24 configurations and standardized Tier A, TA_RIDGE has 5 alphas) is also refuted: 0.999.
2. **Atom-type composition is about half.** Tier A plus smooth size plus radius-0 Morgan counts captures 53 percent on PRIMARY and 67 percent on STRICT. It also captures 80 percent of the AF reduction on PRIMARY ((0.103 - 0.071)/(0.103 - 0.063)) and 64 percent on STRICT. Radius-0 bits encode element, heavy-atom degree, hydrogen count, ring membership and charge, with no information about bonded neighbours. The largest radius-0 weights in a descriptive full-population fit (`rt_e_r0_content.py`) are:
   - lowering g: ring sp3 CH (-0.11), quaternary ring and chain carbons (-0.09, -0.07), ring ether oxygen (-0.07), aryl or alkyl Cl (-0.05)
   - raising g: substituted aromatic or ring carbon (+0.09), methyl (+0.05)

   These atom types correspond to known fragmentation chemistry: branching and tertiary or quaternary centres, labile ring ethers, and aromatic stabilization. Tier A (ring_count, aromatic_ring_count, rdbe, element totals) carries them only partly. **So the gain is not chemically empty, but half of it is atom typing rather than local connectivity.** The decision gate's own Morgan content table (EXP13 `morgan_content`) agrees: 6 of its 12 largest g-lowering bits are single-atom "C", "O" environments.
3. **Radius 2 adds nothing over radius 1.** The radius-1 joint arm reproduces 106 to 112 percent of the gain. The connectivity-specific increment (candidate vs size + radius 0) is 5.5 percent on PRIMARY but only 2.6 percent on STRICT, whereas the composition part is roughly stable across splits (5.9 and 5.0 percent). The part of the model most exposed to chemical novelty is the connectivity part.

**Consequence for wording.** Gate answer 1 ("Local connectivity adds information Tier A does not carry: 11 percent") and answer 3 ("the architecture (Tier A trend plus local environments) matters") should say that roughly half the development gain is atom-type composition (hybridization, branching, aromatic substitution, halogen identity). The part that needs bonded-neighbour context is about 5 percent on PRIMARY and 3 percent on STRICT, and radius-1 environments are sufficient.

The permutation control (EXP08P) shows only that the structure-label link matters. It cannot distinguish composition from connectivity. The Phase 8 rationale ("two different structural metrics give the same joint result, which points at data coverage") has a more economical explanation: both metrics carry the same atom-type composition.

## 3. Question 2: is the gain concentrated in near-duplicate series?

### 3.1 Similarity strata

This is the maximum MinMax Morgan similarity of each held-out compound to its own outer training fold (`rt_a_cached.json`).

| max sim to training | PRIMARY n | PRIMARY ratio | STRICT n | STRICT ratio |
|---|---|---|---|---|
| < 0.30 | 200 | 0.946 | 301 | **0.988** |
| 0.30-0.35 | 205 | 0.949 | 284 | 0.956 |
| 0.35-0.40 | 187 | 0.880 | 258 | 0.909 |
| 0.40-0.50 | 289 | 0.884 | 334 | 0.902 |
| 0.50-0.60 | 210 | 0.831 | 148 | 0.858 |
| 0.60-0.70 | 164 | 0.847 | 0 | n/a |
| >= 0.70 | 70 | 0.78-0.91 | 0 | n/a |

The gain rises steeply with similarity to training chemistry. On STRICT, the 301 compounds with no training neighbour above 0.30 gain 1.2 percent. EXP13 reported only "least-similar decile 0.94" and "max similarity below 0.5, 0.91". Those numbers are correct but hide this gradient.

### 3.2 Chemical classes

- **1,2,4-triazoles.** These compounds, mainly conazole fungicides, are 49 compounds (3.7 percent). Their ratio is 0.637, and they carry **21.6 percent of the PRIMARY net squared-error gain**. Five of the ten top-gain scaffold groups are triazolylmethyl-aryl conazole scaffolds, which account for 13 percent of the gain from 12 compounds.
- **Aromatic halogen compounds.** These 283 compounds carry 37 percent of the gain.
- **Excluding triazoles and all halogenated compounds.** The remaining 940 compounds give a ratio of 0.908 on PRIMARY but **0.957 on STRICT**. CHNO-only compounds (695) give 0.916 on PRIMARY and **0.966 on STRICT**. On STRICT, the composition arm captures most of the chlorinated-compound gain (Cl compounds: joint 0.858, size + radius 0 0.883), while the non-halogen majority gains 4.4 percent (`rt_d_halogen.json`).

### 3.3 Is concentration itself evidence of an artifact?

Not by itself. Twelve strict clusters give half of the PRIMARY net gain, and removing the top 50 gain-contributing strict clusters leaves 0.970 on PRIMARY and 1.006 on STRICT. But TA_RIDGE's gain over mass-only B1 has almost the same ratio (0.892) and almost the same concentration profile: 15 clusters for half the gain, and 0.971 without the top 50 on PRIMARY (`rt_c_transfer.json`, `concentration_null_*`). Heavy-tailed per-compound error differences produce this shape for any real improvement.

Under STRICT the joint gain is somewhat more concentrated than B1-to-TA (1.006 vs 0.985 without the top 50). The removal is also selected on the outcome, so it is a stress reading, not an estimate.

### 3.4 What this does not show

- The benzene hold-out is about as hard as STRICT, not harder. The median max similarity of benzene-scaffold compounds to the rest is 0.365, the same as STRICT held-out compounds.
- NP-likeness is not where the gain fails. The top NP-likeness decile retains 0.912 and NP score above 1 retains 0.915.
- Mass extremes are not where it fails either. The mid-mass tercile gains most (0.836), the high tercile least (0.936).

**Verdict on question 2.** The gain is not a single-series artifact. It is substantially a coverage effect, and a large share of it sits in pesticide-class chemistry (conazoles, chlorinated aromatics) that the WUR food-safety library over-represents. For structurally novel CHNO compounds under STRICT, the expected development gain is about 3 to 4 percent, not 11.

## 4. Question 3: source, instrument, adduct or campaign encoding

This hypothesis is refuted.

- **Source.** Grouped 5-fold logistic AUC for WUR vs LCSB is 0.653 from Morgan and 0.696 from Tier A, and the joint block adds nothing (0.657). Morgan is a worse source detector than Tier A.
- **Correction offset.** The joint-minus-TA log g correction has a source offset of 0.023 log units after Tier A.
- **Gain by source.** Gains are equal by source (WUR 0.892, LCSB 0.884). Train-on-one-source/score-the-other transfer gives 0.90 in both directions (EXP13).
- **Adducts.** Non-[M+H]+ adducts (36) get no gain (0.994), and their AF is worse (13.9 vs 11.1 percent). There is no adduct shortcut. The domain is also too small to support any claim.
- **Campaign.** WUR sub-library cannot be tested as a confounder: 939 of 1,010 WUR positive keys are `WFSR_food_safety;WUR`. The WUR "campaign" is effectively one library. Its chemistry (pesticides, veterinary drugs, toxins) is exactly what section 3 flags.
- **Formerly sealed compounds.** Formerly-sealed membership is not predictable from Morgan (AUC 0.48).

## 5. Question 4: optimism of the "11 percent" point estimate

1. **Arm selection is a small effect.** Eleven arms were run on PRIMARY, including A-1 and A-2. The joint-family arms are near-duplicates (0.882 to 0.893). A Tibshirani-Tibshirani-style estimate over 2,000 scaffold-group bootstrap replicates is 0.0014 ratio units (0.14 points). This is the in-replicate P1 ratio of the overall best arm minus the replicate-best arm. The protocol's selection rule also picked the third-best admitted arm, not the minimum. Refit variance across partitions is small (0.883, 0.890 on S1/S2).
2. **Comparator choice is the material effect.** TA_RIDGE is a 12-descriptor linear baseline. Against the best non-connectivity comparator found in one cheap diagnostic, the candidate's gain is 8.2 percent against quadratic Tier A and 5.5 percent against size + radius 0 on PRIMARY. On STRICT it is 5.9 and 2.6 percent. These comparators were constructed post hoc by the red team, so they are themselves slightly optimistic. The direction is clear, though.
3. **The headline partition is not the most transfer-relevant one.** RANDOM gives 15.5 percent, PRIMARY 11.1 and STRICT 7.4. The single-block Morgan ridge falls from 11 to 5.1 to 1.7 percent over the same splits. For any prediction about new chemistry, STRICT is the more relevant development number.
4. **Unquantifiable reuse.** All 1,325 compounds are exposed, including the 404 formerly sealed ones. The fingerprint-joint architecture was motivated by the Phase 2 Tier B result on the LCSB subset. The bootstrap is conditional on fitted fold models. Protocol section 7 already says this. None of it is a large effect on the number, but together they mean the 0.889 interval [0.865, 0.911] should not be quoted as a sampling interval for a new population.

**Plausible range.** For "same population, same regime" the 11 percent is accurate to within about 1 point. For "new chemistry, same regime", the defensible development estimate is 7 percent on STRICT, and reweighting to MultiMS2-like novelty gives about 7 to 8 percent (section 7). About half of that gain comes from composition, which is not what the claim describes.

## 6. Question 5: are the stated scientific conclusions supported?

| Gate conclusion | Verdict | Evidence |
|---|---|---|
| "Tier A is representation-limited: flat from half the groups" (Q2) | Supported in outcome, weak in argument | A flat learning curve of a linear model cannot separate representation limits from model-class limits. My quadratic and smooth-size Tier A arms show the model-class share is small (2.5 to 3.3 percent on PRIMARY, 1.6 to 2.2 on STRICT), so the conclusion survives on evidence the gate did not run |
| "Local connectivity / local chemistry adds information" (Q1, Q3) | Overstated | Section 2: half is atom-type composition; radius 1 is sufficient; the connectivity-specific part is 5.5 percent on PRIMARY and 2.6 on STRICT |
| "Measurement noise does not dominate the remaining error" (section 1, EXP02) | Holds, but the headroom is understated | The gate quotes 6.5 to 10.3 percent, a share of TA_RIDGE's log g error variance. In trajectory MSE against the candidate, the independent-preparation floor (repeat-scale P1 0.065, n = 26 LCSB compounds) is **32 percent** of the joint model's MSE on those compounds (joint 0.115). The cross-instrument floor (0.068, n = 124) is **30 percent** (joint 0.123), and that floor is optimistic because the frozen map was fitted on those compounds. WUR repeatability, which covers 67 percent of the population, is unmeasurable. The reducible room below the candidate is therefore roughly 0.116 down to about 0.065 to 0.07, not down to the oracle-scale 0.052 |
| "E30 error is mostly scale sensitivity" (Q5, EXP03) | Partly supported; the mechanism is not | 72.5 percent is the scale term's share of the E30 - E90 MSE gradient under TA_RIDGE. The 92 percent figure includes the scale x shape cross term, which is not scale. The same 72.5 percent was used to fire the shape gate (below 75). The decomposition credits to "scale" whatever an oracle per-compound scale can absorb, including shape mismatch aliased onto g, so scale dominance is partly by construction. Within EXP03 the derivative-amplification mechanism is contradicted: at E30 the scale-error RMSE is highest in the **lowest**-sensitivity tercile (0.162) and lowest in the highest (0.130). The analysis was run on TA_RIDGE, not the candidate. The candidate's relative per-rung gain is largest at E45 (0.864), not E30 (0.885) |
| "Shape is not the main limitation" (Q6, EXP11/12) | Supported with a caveat | Oracle-scale P1 0.052 vs predicted-shape gain 1.8 percent. The caveat: the oracle scale absorbs aliasable shape, and only one tangent-orthogonal PC was tested |
| "Trust fails" (Q4) | Supported | Not attacked further |
| "Structural metric matters little, architecture matters" | Supported; the explanation is incomplete | Section 2: Morgan, atom pairs and radius 1 all converge because much of what they share is composition |

## 7. Question 6: would the claim survive in the MultiMS2 regime?

### 7.1 Chemistry

The prompt and census (section 7 item 7) describe the MultiMS2 scaffold-new population as natural-product-like. The structures do not support that (`rt_c_transfer.json`, `multims2_structure_only`).

| Property | MultiMS2 scaffold-new (1,165) | v2 development (1,325) |
|---|---|---|
| NP-likeness score, median and 90th percentile | -0.95 / 0.14 | -0.46 / 2.12 |
| Median Fsp3 | 0.25 | 0.42 |
| [M+H]+ m/z, median and 5-95 percentile | 376 (237-520) | 304 (152-562) |
| Halogenated / P or S / CHNO only | 31 / 29 / 48 percent | 28 / 26 / 52 percent |
| 1,2,4-triazole | 1.4 percent | 3.7 percent |
| Max Morgan MinMax similarity to development, median; share below 0.35 | 0.35; 48 percent | n/a |

A random sample of 25 structures is dominated by combinatorial amides, purinones, aryl piperazines and heteroaromatic screening compounds, with a few flavones and chalcones. The upstream README calls NEXUS "diverse natural product and drug-like compounds". **These are synthetic screening compounds with low similarity to the pesticide/drug-residue development chemistry.** They are heavier and flatter (more aromatic, less sp3).

Reweighting the development OOF gains by (max similarity bin x m/z bin) to the MultiMS2 distribution gives expected ratios of **0.922 (from PRIMARY) and 0.928 (from STRICT)** (`rt_f_reweight2d.json`). The composition arm gives 0.951. This is optimistic on two counts:

- MultiMS2 similarity is measured against all 1,325 development compounds rather than an 80 percent fold.
- It assumes nothing but covariate shift.

So under the development regime, chemistry shift alone is expected to cut the gain to about 7 to 8 percent.

### 7.2 Energy and instrument regime

No development evidence bears on this.

1. **Different energy coordinate.** The model is defined on the Orbitrap HCD NCE coordinate, E/30. MultiMS2 is SCIEX ZenoTOF CID at fixed 20/40/60 V lab frame, and NCE carries a precursor-m/z normalization that fixed-voltage CID does not. In the candidate, precursor_mz is the largest standardized Tier A coefficient (-0.56). Any NCE-to-volt map is therefore mass-dependent and changes the mass law the Tier A block encodes.
2. **Mass-dependent drift is already the size of the Morgan correction.** The only development transfer test (LCSB to WUR, EXP13 0.90) is Orbitrap to Orbitrap on the same NCE scale, through a frozen map fitted on 124 shared compounds. Even there, log g drifts +0.13 per 100 m/z between the two Orbitraps (EXP05), which is the same order as the Morgan correction's SD (0.20 log units).
3. **The correction may be partly mass-per-DOF.** Section 2 shows part of the correction is composition. The chlorine and quaternary-carbon terms plausibly mix fragmentation chemistry with a mass-per-degree-of-freedom correction to the NCE normalization (for Cl compounds, Tier A's single n_halogen term cannot separate a 35 Da atom from a 19 Da one). That second component need not have the same sign under lab-frame CID with a different centre-of-mass energy dependence. This is a mechanism hypothesis, not a measurement.
4. **Three rungs, censored at the low end.** With three rungs, the P1 weighting shifts. The candidate's gain is concentrated at E30 to E60 (ratios 0.885, 0.864, 0.889 vs 0.937 at E90). The census documents that MultiMS2 QC preferentially removes precursor-rich spectra at 20 V and can drop whole compound-adduct pairs. The low-energy rung, where the gain is largest, is therefore selected on the outcome, which should attenuate both absolute P1 and the relative gain.

**Verdict on question 6.** "The joint model ranks above TA_RIDGE" is more likely to survive than the magnitude, because both models share the same profile and map errors. The magnitude should be pre-registered as uncertain, with a chemistry-only expectation of about 0.92 to 0.95 and possibly no gain after the regime change. A MultiMS2 result read against an 11 percent expectation would be misleading whichever way it went. Treating a null MultiMS2 result as a refutation of the development finding would be equally wrong, since the regimes differ on at least four axes simultaneously.

## 8. Checks that passed (claims I tried and failed to break)

- The engine reproduces TA_RIDGE exactly, and the joint model's wider hyperparameter grid does not explain the gain (0.999).
- The gain is not a smooth nonlinear size effect (at most about 25 percent of it) and is not a quadratic Tier A effect (about 30 percent on PRIMARY, 21 percent on STRICT).
- Morgan does not encode source, adduct or formerly-sealed status better than Tier A. Gains are equal across sources.
- Arm-selection optimism is about 0.1 to 0.2 points.
- The gain is not specific to low-NP-likeness compounds, one fold (0.84 to 0.93), or the benzene group (0.887 without it).
- Concentration in a few clusters is typical of any real improvement of this size in this dataset (TA vs B1 control).

## 9. Findings

| Id | Severity | Finding | Evidence | Recommended action |
|---|---|---|---|---|
| RT-1 | Critical (for external-validation design) | No development evidence addresses transfer to fixed-eV QTOF CID. Chemistry-only reweighting already predicts 0.92 to 0.93 rather than 0.889. The mass-dominated Tier A block and composition corrections that may partly encode NCE mass normalization are exposed to the energy-coordinate change. Low-energy QC censoring in MultiMS2 hits the rungs where the gain is largest | `rt_f_reweight2d.json`; EXP13 `morgan_content` (precursor_mz -0.56); EXP05 slope 0.13 per 100 m/z; EXP13 per-rung ratios; census section 6 | Before any MultiMS2 look, pre-register: the estimand as the joint vs TA ratio under one frozen, mass-aware energy map applied identically to both models; an expected effect of about 0 to 8 percent with power computed for it; and an explicit statement that a null result does not refute the development finding (and a positive one does not confirm the 11 percent) |
| RT-2 | Important | About half the gain is atom-type composition (hybridization, branching, aromatic substitution, halogen identity), not local connectivity. It accounts for 53 percent of P1 gain on PRIMARY and 67 on STRICT, and 80 and 64 percent of the AF reduction. Radius 1 reproduces the full gain; radius 2 adds nothing (1.007 [0.993, 1.020]) | `rt_b_size_ladder.json`; `rt_e_r0_content.py` | Reword gate answers 1 and 3 and any manuscript text: "atom-type composition plus first-shell environments". Report the ladder. Consider whether a radius-1 or composition-plus-radius-1 model is the simpler equivalent candidate before the freeze (protocol section 12's "simplest within 1 percent" rule would apply) |
| RT-3 | Important | The connectivity-specific gain shrinks with novelty. It is 5.5 percent on PRIMARY and 2.6 on STRICT beyond composition. STRICT compounds with max training similarity below 0.30 gain 1.2 percent. CHNO-only compounds gain 3.4 percent on STRICT. Conazole fungicides (3.7 percent of compounds) carry 22 percent of the PRIMARY gain | `rt_a_cached.json` (similarity, classes); `rt_c_transfer.json` (class exclusions) | Report similarity-stratified and class-excluded ratios with the headline. Quote STRICT (7.4 percent), not PRIMARY, as the new-chemistry development estimate. Scope the claim to chemistry covered by the training library |
| RT-4 | Important | The MultiMS2 scaffold-new population is drug-like synthetic screening chemistry, not natural-product-like: NP score median -0.95 vs development -0.46, Fsp3 0.25 vs 0.42, [M+H]+ median 376 vs 304, median max similarity 0.35 | `rt_c_transfer.json` `multims2_structure_only`; sampled structures; upstream README | Correct the census wording (section 7 item 7) and any external-protocol scope statement. Scope the claim to "low-similarity drug-like screening compounds" |
| RT-5 | Important | "Noise not dominant" understates how little headroom is left. Repeat floors are 30 to 32 percent of the candidate's trajectory MSE (n = 26 and n = 124, the latter optimistic by construction), not 6.5 to 10 percent. WUR repeatability is unmeasurable | `rt_c_transfer.json` `noise_floor_cross_instrument_124`; recomputation on EXP02 R1 compounds (joint P1 0.115 vs floor 0.065) | State the floor against the candidate in trajectory MSE. Treat roughly 0.065 to 0.07, not 0.052, as the practical floor when judging whether further escalation is worth it |
| RT-6 | Minor | "E30 error is scale sensitivity": scale share is partly definitional (the oracle scale absorbs aliased shape), the 92 percent includes the cross term, the derivative-amplification mechanism is contradicted by EXP03's own terciles (E30 scale RMSE 0.162 low-sensitivity vs 0.130 high), and the analysis used TA_RIDGE | `artifacts/wur_v2/exp03/exp03_results.json` | Soften to "scale misplacement dominates E30 error under an oracle-scale decomposition". Drop the amplification mechanism or test it on the candidate |
| RT-7 | Minor | The "Tier A is representation-limited" argument rests on a linear-model learning curve that cannot separate representation from model class. The conclusion survives on the red-team quadratic and size arms (at most 3.3 percent) | `rt_b_size_ladder.json` | Cite a nonlinear Tier A control when making the claim |
| RT-8 | Minor | The "11 percent" is relative to the weakest reasonable baseline. Against quadratic Tier A the gain is 8.2 percent (PRIMARY) and 5.9 (STRICT); against composition it is 5.5 and 2.6. Arm-selection optimism itself is negligible (0.14 points) | `rt_b_size_ladder.json`; `rt_a_cached.json` `search_optimism` | Report the gain against at least one nonlinear non-fingerprint comparator alongside TA_RIDGE |
| RT-9 | Minor | The permutation control only shows a structure-label link. It is cited as evidence for "local connectivity", which it cannot show | EXP08P; section 2 | Reword; the composition ladder is the relevant control |
| RT-10 | Minor (check passed) | No source, adduct or campaign encoding: Morgan source AUC 0.65 < Tier A 0.70, source offset 0.023, equal gains by source. WUR sub-library is untestable (93 percent one library). Non-[M+H]+ ions gain nothing and have worse AF (n = 36) | `rt_a_cached.json` `source_predictability_grouped_cv` | Keep the [M+H]+ scope for any external claim |
| RT-11 | Minor | Gain concentration in few clusters (12 strict clusters give 50 percent) is not by itself diagnostic: TA vs B1 is equally concentrated. It is slightly stronger under STRICT (1.006 vs 0.985 without the top 50) | `rt_c_transfer.json` `concentration_null_*` | If concentration is discussed, always pair it with the TA vs B1 null |
