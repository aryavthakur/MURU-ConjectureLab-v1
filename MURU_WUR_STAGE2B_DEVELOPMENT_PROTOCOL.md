# MURU WUR Stage 2B: real-data-informed development protocol

**Identifier:** `wur-stage2b-1.0`
**Status:** FROZEN before any candidate MURU variant is compared
**Parent:** `MURU_WUR_STAGE2A_EXECUTION_PROTOCOL.md`, `MURU_WUR_STAGE2A_BASELINE_RESULT.md` (commit `a5611aa`)
**Generation label:** everything produced under this document is **MURU-WUR-v1** (candidate family). A candidate that changes the profile model or the target is labelled **MURU-WUR-v2**. The Stage 2A method is **MURU pre-WUR**.

## 1. Epistemic status of the data from here on

WUR-DEV-ANALYSIS (476 compounds, 241 scaffold groups) is now development
information, as is LCSB-DEV (439). Nothing found on them is external
evidence. WUR-DEV-HOLD (130 compounds, 94 groups) stays undecoded until the
single internal check of section 8. WUR-SEALED (404) is untouched; the seal
guard in `wur_spectra.build_mu_table` refuses it and the population loader
refuses HOLD. The Stage 1 map is not refitted. E = 15 never enters a pooled
fit; native E = 15 may be used only inside single-corpus diagnostics and is
reported separately.

## 2. Development population

DEV2B is the Stage 2A pooled-aligned world: 791 compounds in 431 scaffold
groups, keys sha256
`f38f2d806df6659059e7aea6639481cb5d72c37ab2291485c50afb58239c1ee3`
(`artifacts/wur_stage2a/A_POOLED_ALIGNED/result.json`, `population.keys_sha256`),
asserted by the fold builder. Rungs 30, 45, 60, 75, 90 on the LCSB
nominal coordinate; WUR read at the frozen `T(E)`; population-B keys carry
the LCSB copy. The native views (B, C of Stage 2A) are diagnostic only.

## 3. Folds, frozen

Repeated scaffold-group K-fold, K = 5, R = 3, on DEV2B, with
`muru.splits.grouped_folds` (largest-group-first size balancing) at seeds
20260913, 20260914, 20260915. Connectivity-key and scaffold-group
disjointness are asserted per repeat. Fold membership and its sha256 are
persisted to `artifacts/wur_stage2b/folds.json` before any candidate runs,
and every candidate result records that hash. Any tuning inside a training
fold uses an inner scaffold-group 4-fold at seed `20260916 + outer fold
index`; the outer held-out fold is never read during tuning. Folds do not
change after the first candidate result exists.

## 4. What a candidate is

A candidate is a complete pipeline: given the training fold's trajectories
and descriptors, it must return, for a held-out compound, a predicted mu at
each pooled rung **from that compound's descriptors alone**. It may also
return a confidence in [0, 1] or an abstain flag. Anything that reads a
held-out compound's own spectra to predict that compound is not a candidate
for the primary metric (it is a diagnostic).

Every candidate gets an immutable ledger entry
(`artifacts/wur_stage2b/ledger/<candidate_id>.json`) with: id, parent,
hypothesis, rationale, code commit, features, preprocessing, model family,
free parameters, tuning space, training data hash, folds hash, seeds,
per-fold metrics, uncertainty, failures, complexity, outcome, and the
reason accepted or rejected. Entries are never overwritten.

## 5. Metrics

| Id | Metric | Definition |
|---|---|---|
| **P1** | held-out trajectory RMSE | root mean square of (predicted mu - observed mu) over every (held-out compound, pooled rung) cell of a fold; 15 fold values, mean and SD reported |
| S1 | per-energy and per-source RMSE | P1 split by rung and by WUR / LCSB |
| S2 | descriptor practical-win fraction | fraction of held-out compounds whose RMSE is <= 0.90 x the null profile B0's RMSE for that compound |
| S3 | within-compound adequacy | under the candidate's profile model, the leave-one-energy-out M0-analogue MAE per compound, and the frozen M1/M2/M3 contrast where the model admits it |
| S4 | catastrophic rate | fraction of held-out compounds with RMSE > 2 x B0's RMSE for that compound |
| S5 | stability | SD of P1 over the 15 folds; per-repeat spread |
| S6 | complexity | number of free parameters and of distinct input features |
| S7 | preprocessing robustness | change in P1 (repeat 1 only) under `relative_cutoff = 0.01` and under `include_precursor = false` |
| S8 | uncertainty use | if a confidence is emitted: Spearman between confidence and held-out per-compound RMSE; P1 among non-abstained; abstention rate |

Uncertainty on P1 differences: paired over folds (15 differences, mean, SE,
sign count) and a compound-level bootstrap (1,000 resamples, seed 20260911)
of the paired per-compound RMSE difference within each repeat.

## 6. Reference arms, run on the same folds

| Arm | Definition |
|---|---|
| B0 | per-energy mean mu of the training fold (no descriptors) |
| B1 | mass-only: training-fold collapse (`fit_collapse`, frozen settings) then isotonic regression of log g on precursor m/z; held-out g from the isotonic fit |
| LIN | ridge regression of log g on the 12 scaled Tier A descriptors (alpha chosen on the inner folds), same training-fold collapse |
| **S2A** | the frozen pre-WUR pipeline per fold: training-fold collapse, 30-seed PySR search on training/validation parts of the training fold (inner 75/25 scaffold split by `protocol.group_split`), frozen B2/R1 selector and gate; the representative expression predicts held-out g; gate decision recorded, prediction scored regardless |

For every arm, a held-out compound's predicted mu is `Phi_train(E / (30 g_pred))`
unless the candidate defines its own profile model.

## 7. Selection rule, frozen

A candidate C **beats S2A** iff all of:

1. P1(C) < P1(S2A) in at least 12 of the 15 folds;
2. mean relative improvement over S2A, averaged over folds, >= 5 percent;
3. P1(C) < P1(B0) in at least 13 of 15 folds and P1(C) < P1(B1) in at least
   12 of 15 folds (it must add value beyond a null profile and beyond mass);
4. S4(C) <= S4(S2A) on the pooled 15 folds;
5. inherited non-regression: the median within-compound leave-one-energy-out
   MAE of C's profile model on held-out compounds is <= 0.035, the frozen
   M0's pooled-analysis value (0.032) plus one repeatability-scale tolerance;
6. no result depends on native E = 15 or on HOLD.

Among candidates that beat S2A, order by mean P1; a candidate whose paired
fold-difference to the best is within one standard error of that difference
is tied with it, and the tie is broken by S6 (fewer features, then fewer
free parameters). The final candidate is the simplest member of the top tie
group. No candidate is selected on any number not listed here.

## 8. Readiness gate and the single internal check

The final candidate may be frozen for Stage 3 only if all hold:

- no unresolved Critical scientific or implementation finding from the
  reviews of section 10; no leakage finding;
- the full test suite passes except the eight pre-existing ledger failures
  documented in the Stage 2A protocol preflight;
- the candidate's 15-fold results reproduce from the committed code and the
  committed folds (hash equality of the ledger metrics);
- section 7 is satisfied;
- S5(C) <= 1.5 x S5(S2A);
- S6: at most 24 input features (twice the frozen twelve) and an
  interpretable form, or a black box only if condition 2 of section 7 holds
  at >= 15 percent instead of 5;
- no threshold in this document moved after any candidate result existed.

**Internal check, one look.** Train C, S2A, B0, B1 on all of DEV2B; decode
HOLD once (130 compounds, aligned coordinate, WUR read at `T(E)`); score
P1 on HOLD. The check passes iff P1(C) < P1(S2A), P1(C) < P1(B1), the
relative improvement over S2A is >= 2.5 percent, and the compound-level
bootstrap 90 percent interval of the paired per-compound RMSE difference
C - S2A lies below 0. HOLD is then marked EXPOSED whatever the outcome. A
failed check stops the program before Stage 3; development may continue
only under an amended protocol with HOLD treated as development data, and
the only remaining untouched population is WUR-SEALED.

## 9. Stage 3 endpoints, pre-stated

The freeze document fixes the exact list; it will not go beyond these:
P1 on WUR-SEALED (aligned coordinate) for C, S2A, B0 and B1 trained on
DEV2B plus HOLD; the paired bootstrap of C - S2A and C - B1; S1 per rung;
S2 and S4; the native-coordinate P1 as a secondary; E = 15 native,
separate; S8 if C emits confidence. Success is defined as the internal
check's conditions holding on the sealed population.

## 10. Process

Order of work: (i) failure analysis of Stage 2A on DEV2B, with the
extended spectral summaries of `wur_stage2.spectral_features` computed on
both corpora, (ii) fold freeze, (iii) reference arms, (iv) candidates in
order of hypothesis strength, each ledgered, (v) adversarial reviews
(scientific red team, leakage, statistics, implementation,
reproducibility), (vi) selection, (vii) internal check, (viii) freeze.
Hypotheses are stated before the experiment that tests them. A failed
hypothesis is recorded and not retried with a different fold set.

## 11. Prohibited

Refitting or reinterpreting the Stage 1 map; decoding HOLD before section 8
or WUR-SEALED before the freeze; changing folds, P1, or any threshold above
after a candidate result exists; using native E = 15 in a pooled fit;
deleting or editing a ledger entry; comparing candidates on the Stage 2A
single split instead of the frozen folds.

## 12. Amendments

### A-1, 2026-09-12, issued after the reference arms and before any candidate

Section 7 condition 5 pinned the inherited non-regression threshold at
0.035 from the Stage 2A ladder's M0 median MAE (0.032). That number was
computed with `fit_case_phi` at `E_REF = 45` on a train-only Phi. The Stage
2B harness scores every collapse arm's within-compound LOEO MAE (S3) with
the frozen M0 fitter against the arm's own `ENERGY_SCALE = 30` collapse
profile, and the frozen S2A arm itself scores 0.0465 there, identical for
B1 and LIN because they share the profile. A threshold pinned on one
estimator and applied to another would fail every candidate for a reason
unrelated to regression. Condition 5 is therefore restated on like-for-like
numbers: **the median S3 of C over the 15 folds must be <= the median S3 of
the S2A arm under this harness (0.0465) + 0.003**, the tolerance being one
tenth of the repeatability SD. No candidate result existed when this was
written; the four reference-arm ledger entries did, and their S3 values are
all equal by construction, so no candidate ordering was informed by it.

### A-2, 2026-09-12, clerical, issued after the candidate runs

A-1 quoted the S2A arm's S3 as 0.0465; that was the fold-0 value. The
rule as written and as implemented in `candidates.evaluate_rule` uses the
median over the 15 folds of the S2A ledger, which is 0.0397. The quoted
number is corrected; the rule, its reference quantity and its tolerance are
unchanged, and every candidate's condition 5 outcome is the same under both
readings (all candidates' S3 medians are <= 0.0397).
