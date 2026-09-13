# MURU-WUR-v2: first decision gate (after Experiments 1-13)

**Protocol:** `wur-v2-dev-1.0` with amendments A-1, A-2. **Ledger:** `artifacts/wur_v2/ledger/ledger.jsonl`. All numbers are development evidence on 1,325 exposed compounds (PRIMARY pooled out-of-fold, 5 grouped folds, 765 stereo-free scaffold groups) unless stated. Intervals are scaffold-cluster bootstraps that recompute P1 in each replicate, conditional on the fitted fold models.

## 1. Measurement and statistics corrections (Phase 0)

| Question | Finding | Evidence |
|---|---|---|
| Does v1 reproduce? | Yes, exactly (per-compound RMSE within 5e-16 of the Stage 3 record) | EXP01A |
| Does the P1/bootstrap estimand fix change v1's reading? | No. V1B vs S2A P1 ratio 0.849 [0.807, 0.891]; vs mass-only 0.882 [0.826, 0.939]; B1 vs S2A 0.963 [0.902, 1.032]; V1C vs V1B 0.988 [0.962, 1.014]. Cluster intervals are wider than the historical compound ones. P1 0.1251 is not mean compound RMSE (0.1080) | EXP01A |
| Fair v2 baseline | TA_RIDGE refit under v2 nesting: P1 0.1305 (MRMSE 0.1148, AF 10.3 percent); B1 0.1464; B0 0.1754. v1's alpha-selection shortcut changes P1 by < 0.001 | EXP01B |
| Is "0.988 reliability" a repeatability? | No. Empirical per-measurement log g SD from independent preparations is 0.116 (26 compounds), 1.6x the curvature SD v1 used; log g ICC 0.97; cross-instrument ICC 0.94 | EXP02 |
| Does measurement noise dominate the remaining error? | No. Repeat noise is 6.5 percent (preparations) to 10.3 percent (instruments) of Tier A's out-of-fold log g error variance. A scale measured on an independent preparation predicts the other preparation's trajectory at P1 0.065, against 0.158 for Tier A on those compounds | EXP02 |
| Are scales identifiable? | Yes. 42 of 1,325 at the grid edge (heavy, median m/z 748); median likelihood-interval width 0.15 log units; weakly identified compounds carry no absolute failure | EXP02 |
| WUR technical repeats | None exist: 5,580 of 6,060 WUR cells are two archive copies of one acquisition; distinct acquisitions at one key are isomers | registry, EXP02 R3 |
| Why is E30 worse than E90? | Scale error through the nonlinear profile: the scale-only term explains 72 percent of the E30 - E90 MSE gradient (92 percent with the scale-shape cross term; shape alone 8 percent). The local linear derivative explains less at the tails (R^2 0.72 at E30, 0.35 at E90): errors are large enough to be nonlinear | EXP03 |
| Survival or depth? | Neither beyond total mu: adding survival and depth to total mu explains at most 2 percent more error variance at any rung. E30 errors are symmetric onset misplacement: early-fragmenting compounds are predicted too intact and survivors too fragmented | EXP04 |
| Acquisition and ion effects | Per-rung cross-instrument mu equivalent within +/-0.02 (partly by construction of the map), but log g WUR - LCSB rises +0.13 per 100 m/z [0.09, 0.17]; modelling source x mass moves pooled P1 by < 1 percent. Non-[M+H]+ ions (36) are worse under every model | EXP05, EXP05B |
| Absolute failure tolerance | RMSE_i > 0.20 (AF), max rung error > 0.30 (AF_max), derived in protocol section 6 and frozen before any v2 fit | protocol |

## 2. Representation results (Phases 1-4)

TA_RIDGE: P1 0.1305, MRMSE 0.1148, AF 0.103, AF_max 0.100, S4 0.094, Q95 0.231.

| Arm | PRIMARY P1 | ratio vs TA [95%] | S1 | S2 | STRICT | GIANT | RANDOM | MRMSE | AF | AF_max | S4 | Q95 | admitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP07 TA + ION_ENV | 0.1277 | 0.978 [0.960, 0.995] | 0.979 | 0.974 | 0.979 | 0.991 | 0.960 | 0.1112 | 0.096 | 0.088 | 0.088 | 0.228 | yes |
| EXP08A Morgan ridge | 0.1239 | 0.949 [0.918, 0.981] | 0.937 | 0.941 | 0.983 | 0.930 | 0.889 | 0.1068 | 0.090 | 0.094 | 0.075 | 0.233 | yes |
| **EXP08B TA + Morgan joint ridge** | **0.1160** | **0.889 [0.865, 0.911]** | 0.883 | 0.890 | **0.926** | **0.896** | 0.845 | 0.1005 | **0.063** | 0.065 | 0.070 | 0.212 | yes |
| EXP08C TA then Morgan residual | 0.1166 | 0.893 [0.870, 0.916] | 0.886 | 0.892 | 0.930 | 0.892 | 0.845 | 0.1009 | 0.062 | 0.067 | 0.073 | 0.213 | yes |
| EXP08D MinMax kernel ridge | 0.1189 | 0.911 [0.876, 0.944] | 0.887 | 0.891 | 0.947 | 0.922 | 0.823 | 0.1018 | 0.077 | 0.077 | 0.072 | 0.219 | yes |
| EXP09A atom-pair ridge | 0.1229 | 0.941 [0.903, 0.974] | 0.933 | 0.940 | 0.988 | 1.012 | 0.895 | 0.1053 | 0.078 | 0.085 | 0.084 | 0.222 | yes |
| EXP09B MACCS ridge | 0.1326 | 1.016 [0.981, 1.051] | 0.998 | 0.994 | 1.028 | 1.027 | 0.985 | 0.1155 | 0.099 | 0.094 | 0.099 | 0.237 | no |
| EXP09C kNN residual (Morgan) | 0.1215 | 0.931 [0.886, 0.969] | 0.909 | 0.904 | 0.970 | 1.001 | 0.852 | 0.1030 | 0.079 | 0.077 | 0.079 | 0.228 | yes |
| EXP09D TA + atom-pair joint (A-1) | 0.1157 | 0.886 [0.854, 0.915] | 0.886 | 0.889 | 0.926 | 0.939 | 0.854 | 0.0992 | 0.061 | 0.062 | 0.083 | 0.212 | yes |
| EXP08E TA + ION_ENV + Morgan joint (A-1) | 0.1151 | 0.882 [0.852, 0.910] | 0.869 | 0.876 | 0.905 | 0.904 | 0.832 | 0.0994 | 0.058 | 0.066 | 0.071 | 0.206 | yes |

Controls: Morgan rows permuted across compounds through the full pipeline give ratio 1.38 to 1.40 alone and 0.998 to 1.005 inside the joint model (EXP08P): the joint gain disappears with the structure-label link.

Learning curves (EXP06): Tier A flattens by half the training groups; Morgan alone keeps improving to 100 percent on PRIMARY and flattens by 75 percent on STRICT; Morgan's gain over Tier A is 11 percent on RANDOM, 5.1 on PRIMARY, 1.7 on STRICT.

## 3. Trust (Phase 5)

No pre-measurement signal identifies absolute failures of the joint model (prevalence 6.3 percent): best AF PR-AUC 0.084 against a random 0.063; retained AF at 80 percent coverage 5.8 to 6.3 percent for every signal and for the learned model; learned versus distance-only relative reduction -5 percent [-24, +10]; logistic Brier equal to a constant; calibration slope 0.20. STRICT is no better. Route B is closed (EXP10).

## 4. Shape (optional Phase 6)

Gate 13(a) fired on the strict reading of EXP03 (scale-only 72.5 percent of the gradient, below 75). EXP11: a tangent-orthogonal residual basis is stable across folds (PC1 about 70 percent of residual variance, a low-E versus high-E tilt); its coefficient reproduces across preparations (r 0.77) and instruments (r 0.85) and is predictable from structure at out-of-fold R^2 0.18; a held-energy oracle loses 12.7 percent. Under A-2 one fully nested arm (EXP12) gives a stable but small gain over the joint model: PRIMARY 0.1139, ratio 0.982 [0.976, 0.988], 1.8 to 2.1 percent on every grouped partition and 0.8 percent on STRICT. It misses the frozen 2 percent bar for adding a second profile parameter. **Decision: keep the one-scale shared profile.** The shape residual is real, reproducible and weakly predictable; its practical value is about 2 percent.

## 5. Stress test of the leading model (EXP13)

Every pre-stated sensitivity keeps the joint model ahead of TA_RIDGE: compound weighting 0.889; per fold 0.84 to 0.93; strict-cluster bootstrap unit 0.889 [0.863, 0.915]; top leverage decile 0.94; least-similar decile 0.94; compounds with maximum training similarity below 0.5 (881) 0.91; native WUR energies through the inverse map 0.90; train on LCSB, predict WUR 0.90; train on WUR, predict LCSB 0.90. Per rung the gain is largest at E30 (0.153 vs 0.172) and smallest at E90 (0.087 vs 0.093). On the 404 formerly sealed compounds (descriptive only) the joint out-of-fold P1 is 0.1121 against the frozen v1 model's 0.1251 and TA_RIDGE out-of-fold 0.1235. The Morgan block carries 27 percent of fitted log g variance.

## 6. Gate questions

1. **Is more of g predictably encoded in local structure?** Yes. Local connectivity adds information Tier A does not carry: 11 percent lower P1 on PRIMARY, 7.4 on STRICT, 10.4 on benzene held out, destroyed by permutation.
2. **Is Tier A sample- or representation-limited?** Representation-limited: flat from half the groups. The fingerprint models are partly coverage-limited: their gain grows with data and shrinks for structurally novel clusters.
3. **Does local chemistry improve held-out P1 meaningfully?** Yes, a major development gain (11.1 percent), with AF 10.3 to 6.3 percent. The structural metric matters little (Morgan and atom pairs give the same joint result); the architecture (Tier A trend plus local environments) matters. Hand-built ion-environment features help alone (2.2 percent) but add under 1 percent once Morgan is present on PRIMARY (2.2 on STRICT).
4. **Can bad predictions be identified before measurement?** No, not with novelty, leverage, disagreement, sensitivity or their combination.
5. **Is E30 error mostly scale sensitivity?** Yes (section 1).
6. **Is the shared-profile shape now the main limitation?** No. With the joint model, scale-only error still dominates (oracle-scale P1 0.052 against 0.116), and the best shape model gains about 2 percent.

## 7. Optional phases

| Phase | Gate as written | Decision |
|---|---|---|
| 6 Shape | 13(a) fired; oracle held-energy gate failed; A-2 arm run | closed: 1.8 percent, below the bar |
| 7 Quantum/ion-state pilot | "ION_ENV admitted or joint gain over Morgan >= 2 percent": the first clause holds | **not run.** The gate is necessary, not sufficient. The ion block's marginal value beyond Morgan is 0.8 percent on PRIMARY, so fingerprints already absorb most ion-environment signal; xTB is not installed; expected information value is low against the cost. Stop rule "quantum adds nothing beyond fingerprints" is the likely outcome and is not worth an experiment at this gain level |
| 8 Pretrained encoder | "fingerprint admitted with >= 5 percent and still rising at 100 percent" | **not run.** The joint model's gain is large, but the fingerprint learning curve rises only 1.2 percent from 75 to 100 percent on PRIMARY and is flat on STRICT; two different structural metrics give the same joint result, which points at data coverage rather than representation; no deep-learning stack is installed and a model download would need its own provenance audit. Poor expected value per unit complexity |
| 9 Direct trajectory model | requires the shape conditions and energy-structured residuals | **not run**: the shape phase closed |

## 8. Decision

Proceed to candidate selection. By protocol section 12 the simplest admitted candidate within 1 percent of the best admitted P1 (EXP08E, 0.1151, an A-1 arm) is **EXP08B, TA_MORGAN_JOINT (0.1160)**: EXP08E is 0.8 percent better, adds the ION_ENV block, and reduces AF by only 0.5 points; EXP09D (atom pairs) is equal in complexity, 0.3 percent better, worse on GIANT, and an A-1 arm; EXP08C (two stage) is equal in class and slightly worse. Outcome A applies: a simple structural model that improves P1 materially over the refitted v1 family and stays ahead on every hard split, with no trust mechanism.
