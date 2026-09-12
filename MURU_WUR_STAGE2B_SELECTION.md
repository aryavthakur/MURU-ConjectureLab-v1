# MURU WUR Stage 2B: candidate ledger summary and selection

**Rule:** `MURU_WUR_STAGE2B_DEVELOPMENT_PROTOCOL.md` section 7 with A-1, A-2, implemented in `muru.wur_stage2.candidates.evaluate_rule` and `rank_candidates`. **Folds:** `artifacts/wur_stage2b/folds.json` (sha `fed82502...`). **Ledger:** `artifacts/wur_stage2b/ledger/`.

## Arms and candidates on the 15 frozen folds

| Id | Generation | Features | P1 mean | P1 SD | Wins vs S2A | Rel. vs S2A | S4 | Rule |
|---|---|---|---|---|---|---|---|---|
| B0_NULL_PROFILE | reference | 0 | 0.1814 | 0.0163 | | | | |
| B1_MASS_ONLY_ISOTONIC | reference | 1 | 0.1523 | 0.0059 | | | 0.19 | |
| S2A_FROZEN_PIPELINE | MURU pre-WUR | 12 (symbolic) | 0.1539 | 0.0179 | | | 0.104 | reference; gate refused in 15/15 folds |
| LIN_RIDGE_TIERA | reference | 12 | 0.1349 | 0.0067 | 15/15 | +11.6% | | passes every clause (computed from the ledger vectors) |
| V1A_STABLE_LAW | MURU-WUR-v1 | 3 | 0.1370 | 0.0067 | 14/15 | +10.2% | 0.084 | **beats S2A** |
| V1C_RICH_RIDGE_24 | MURU-WUR-v1 | 24 | 0.1337 | 0.0063 | 15/15 | +12.4% | 0.081 | **beats S2A** |
| V1D_RICH_HGB_24 | MURU-WUR-v1 (black box) | 24 | 0.1348 | 0.0062 | 12/15 | +11.5% | 0.087 | fails c2 (black-box bar 15%) |
| V2A_TWOPARAM_RIDGE | MURU-WUR-v2 | 12 | 0.1513 | 0.0069 | 8/15 | +0.5% | 0.129 | fails c1, c2, c3, c4 |

Hypothesis outcomes: H-L (stable law) supported; H-R (Tier A2 raises the ceiling materially) **not supported**, the twelve extra descriptors add 0.9 percent over the twelve-feature ridge; H-NL (nonlinear interactions) not supported at the black-box bar; H-P2 (descriptor-predicted second profile parameter) refuted, exactly as the failure analysis predicted.

## Ranking under the frozen tie rule

Ordered by mean P1: V1C 0.1337, V1D 0.1348, LIN 0.1349, V1A 0.1370. Paired fold difference V1C - LIN: -0.00121, SE 0.00047, 13 of 15 folds; V1C - V1A: larger. Under the frozen definition (tie = within one fold-paired standard error of the best) only V1D ties with V1C, and V1D is not eligible; the simplest member of the tie group is therefore **V1C_RICH_RIDGE_24**, the selected candidate.

**Caveats recorded for the reviewers, not used to alter the rule.**

1. The compound-level paired bootstrap of V1C - LIN includes zero in all three repeats (repeat 0: -0.0013 [-0.0031, +0.0006]; repeat 1: -0.0016 [-0.0035, +0.0004]; repeat 2: -0.0014 [-0.0035, +0.0007]). The fold-paired SE and the compound bootstrap disagree on whether V1C and LIN are distinguishable; the protocol's tie definition is the fold-paired SE, and it was frozen before any candidate ran. A reviewer who judges the 0.9 percent gain immaterial is reading the bootstrap; the selection record states both.
2. The confidence output of V1C (negated out-of-fold residual model) carries no signal: Spearman between confidence and held-out RMSE is -0.19 to +0.14 across folds (median -0.05), and the top-80-percent P1 (0.1333) equals the full P1 (0.1337). It is dropped from the frozen candidate as an inert output; no parameter or prediction changes.
3. LIN is a reference arm, not a registered candidate. It passes every section 7 clause on the ledger vectors and is reported in the ranking for transparency. Had the tie rule admitted it, it would have been selected over V1C on simplicity.
4. V1A's law form was chosen after seeing its exploratory CV R2 in the failure analysis; its coefficients are refit per fold, and the HOLD check is the guard against that optimism. It is the simplest candidate that beats S2A and is carried forward as the named alternative in the freeze document.

## What the selected candidate is

MURU-WUR-v1, candidate V1C_RICH_RIDGE_24: the frozen alternating collapse (shared isotonic profile Phi on log u, ENERGY_SCALE 30, per-compound scale g estimated on the training compounds), then ridge regression of log g on 24 scaled descriptors (Tier A twelve, Tier A2 twelve; alpha chosen on inner scaffold folds), and prediction mu(E) = Phi_train((E/30)/g_pred) at the pooled rungs. No symbolic search, no gate, no confidence output.

Against the pre-WUR method it changes three things: the descriptor-to-scale model (ridge instead of PySR plus selector), the report rule (always predicts; reports P1 against references instead of a validation-R2 gate), and the descriptor set (24 instead of 12). It keeps the endpoint mu, the collapse estimator, the energy coordinate, the Stage 1 map and E = 15 handling.

## Adjudicated selection (amendment A-3, after the five reviews)

**Final candidate: `V1B_RIDGE_TIERA`** (the LIN arm: frozen collapse, ridge of log g on the twelve Tier A descriptors, alpha by inner scaffold folds). V1C is rejected because its registered hypothesis failed and it is statistically tied with the simpler model; V1A is the named interpretable secondary; V1C is an exploratory non-inferiority comparator. See `MURU_WUR_STAGE2B_REVIEW_ADJUDICATION.md`.

Cluster-bootstrap (scaffold groups) 95 percent CIs on the P1 difference, from the statistical review: LIN - S2A [-0.027, -0.014]; V1C - LIN [-0.0036, +0.0011]; V1A - LIN [-0.0011, +0.0050]; V1C - B1 [-0.024, -0.013].
