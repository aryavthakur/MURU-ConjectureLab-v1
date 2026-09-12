# MURU WUR Stage 3: external validation on WUR-SEALED, RESULT

**One look, executed 2026-09-12T19:55:23Z at git HEAD `69ca1a6` (the freeze commit, clean tree), recorded in `artifacts/wur_stage3/first_sealed_access.json`. Audit `artifacts/wur_stage3/freeze_precedes_access_audit.json`: PASS.**
**Population evaluated:** all 404 sealed positive-mode trajectories (275 scaffold groups), keys sha256 `6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52`; 5,030 spectra, 2,424 cells, zero peak defects, zero descriptor failures, no exclusions.
**Candidate:** `V1B_RIDGE_TIERA` exactly as frozen; alpha 1.0 chosen on the 921-compound training population.
**WUR-SEALED is now EXPOSED.**

## 1. Pre-registered endpoints

| Id | Endpoint | Result |
|---|---|---|
| S3-1 | V1B vs S2A, aligned P1 | **0.1251 vs 0.1475**, 15.1 percent relative; paired difference 90 percent [-0.0263, -0.0177], 95 percent [-0.0270, -0.0167], cluster 95 percent [-0.0295, -0.0150]; V1B better on 64 percent of compounds |
| S3-2 | V1B vs B1 (mass-only) | **0.1251 vs 0.1420**, 11.8 percent; 90 percent [-0.0202, -0.0110]; cluster 95 percent [-0.0290, -0.0040] |
| S3-3 | V1B vs B0; B1 vs S2A | 0.1251 vs 0.1676 (25.3 percent, 90 percent [-0.0441, -0.0288]); B1 vs S2A 3.7 percent, 90 percent [-0.0126, -0.0002], 95 percent [-0.0139, +0.0005], cluster through zero: the pre-WUR pipeline is at best marginally better than mass alone |
| S3-4 | per-rung S1 (V1B / S2A / B0) | E30 0.164 / 0.190 / 0.202; E45 0.147 / 0.169 / 0.192; E60 0.118 / 0.141 / 0.163; E75 0.094 / 0.117 / 0.141; E90 0.083 / 0.102 / 0.128. S2 (descriptor practical win vs B0) V1B 0.604, S2A 0.530, B1 0.540; S4 (catastrophic) V1B 0.104, S2A 0.126, B1 0.121 |
| S3-5 | benzene stratum | no sealed compound carries the plain benzene scaffold (that group is development-side by D2); the "other" stratum is the whole population |
| S3-6 | S2A under its own gate | **abstains** (median seed-best validation R2 0.435 < 0.595; selection fraction 0.200). Its selected expression is `sqrt(1/heteroatom_fraction + ring_count) / total_atom_count`, the same three-input law Stage 2B named; forced prediction P1 0.1475 |
| S3-7 | secondaries | V1A (law) 0.1306: beats S2A by 11.4 percent (90 percent [-0.0205, -0.0126]) and is worse than V1B by 4.4 percent (90 percent [+0.0020, +0.0087]). V1C (24 features) 0.1236: 1.2 percent better than V1B, interval through zero ([-0.0032, +0.0008]), non-inferior, not superior. V1B trained on WUR rows only 0.1265: 1.1 percent worse than pooled, interval through zero |
| S3-8 | native-coordinate P1 | V1B 0.1446, S2A 0.1810, B1 0.1607, B0 0.1758 (models trained on the aligned coordinate, scored against native WUR rungs; ordering unchanged) |
| S3-9 | E = 15, native, separate | n 404, median 0.763, quartiles 0.583 to 0.929; never pooled |

**Success rule:** P1(V1B) < P1(S2A) yes; P1(V1B) < P1(B1) yes; relative improvement over S2A 15.1 percent >= 2.5 yes; 90 percent interval below zero yes. **The principal claim survives.**

## 2. Comparison with development

| Population | V1B | S2A | B1 | B0 | V1B rel. to S2A |
|---|---|---|---|---|---|
| DEV2B folds | 0.1349 | 0.1539 | 0.1523 | 0.1814 | 12 percent |
| HOLD (130) | 0.1298 | 0.1588 | 0.1438 | 0.1684 | 18 percent |
| SEALED (404) | 0.1251 | 0.1475 | 0.1420 | 0.1676 | 15 percent |

The sealed numbers sit inside the development range for every arm; nothing generalised worse than development predicted. V1C's 0.9 percent development edge over V1B reappears as 1.2 percent on sealed data, still inside its interval, so the adjudication's "not distinguishable" stands. V1A's optimism (2 to 3 percent, predicted by the statistical review) shows as the 4.4 percent deficit to V1B.

## 3. Failure modes on sealed data

- Error is concentrated at the low rungs (E30 0.164 versus E90 0.083 for V1B), as on development: the descriptor model's error in g dominates where the trajectory is steep.
- 10.4 percent of sealed compounds are catastrophic (RMSE more than twice the null profile's) under V1B, against 12.6 percent under S2A: the method still mispredicts one compound in ten badly and has no mechanism to say which.
- The pre-WUR pipeline, run as frozen, abstains on the entire sealed population.

## 4. Interpretation

What survives is exactly the weak claim the reviews allowed: on 404 independent real spectra of never-seen scaffolds, a ridge of the collapse scale on twelve descriptors predicts fragmentation trajectories 15 percent better than the pre-WUR MURU forced to predict, and 12 percent better than mass alone, while the pre-WUR method does not beat mass alone and would not have reported at all. The improvement comes from removing the symbolic search, selector and gate, not from a new law; the three-input law the frozen search itself keeps finding generalises too (11 percent over S2A) but is 4 percent behind the ridge. Half of the variance in the per-compound scale remains unexplained by any descriptor set tried, and the profile family still leaves a per-compound shape residual.

## 5. After the reveal

No repair on this population. Any improved generation (a richer molecular representation for g; a population-level mass-aware asymptote) needs a new independent external set for a definitive claim.
