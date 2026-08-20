# MURU FINAL ACCURACY SPRINT

**Mode**: controlled, preregistered, exploratory DEVELOPMENT — one pass, then stop.
**Design frozen before any scored comparison**: `MURU_FINAL_ACCURACY_SPRINT_FREEZE.md`
(committed before the first architecture number existed).
**New PySR runs**: 150, and only inside the bounded conditional SAFE_EXP diagnostic.
**Fresh independent holdout**: NOT touched, NOT generated, NOT inspected, plan unchanged.

## DECISION

> **RETAIN CURRENT_FINAL.** No architecture change ships. No gate change ships.
> No tolerance, CAS or grammar operator was moved.

The best alternative architecture lost 1.79 percentage points of family recovery
against a ship bar of +3.00. The two remaining scientific hypotheses that did
show signal (worst-stratum robustness, residual structure) are reported as
measurements only; per the brief's hard stop, no fifth architecture was created
from them.

---

## 1. Headline, pooled outer-fold held-out

| Metric | OLD (frozen baseline) | NEW (this sprint) |
|---|---|---|
| support recovery, ungated | 98.2% (55/56) | **98.2% (55/56)** |
| support recovery, end-to-end | 96.4% (54/56) | **96.4% (54/56)** |
| family recovery | 83.9% (47/56) | **83.9% (47/56)** |
| G1A family | 100% (6/6) | **100% (6/6)** |
| G1B family | 87.5% (35/40) | **87.5% (35/40)** |
| G1C family | 60.0% (6/10) | **60.0% (6/10)** |
| null FPR | 3.0% | **3.0%** |
| balanced accuracy | 96.7% | **96.7%** |
| ROC AUC | 0.9991 | **0.9991** |

Identical by construction: the winning architecture *is* the incumbent. 95% Wilson
intervals: family 83.9% [72.2%, 91.3%], support 98.2% [90.6%, 99.7%],
null FPR 3.0% [1.5%, 6.1%], sensitivity 96.4% [87.9%, 99.0%].

---

## 2. Phase 0 — baseline reproduced exactly

Re-running `scripts/accopt_run.py` on the copied candidate cache is **bit-identical**
to the frozen baseline artifact on `oracle`, `baseline_30`, `held_out` and
`failure_taxonomy`. All five outer folds independently re-chose B2 + R1, with the
same fitted gate thresholds (`t1` 0.595 in four folds, 0.725 in one; `t2` 0.2 in
four, 0.433 in one).

Independently, the sprint's own implementation of architecture A selects the
**same representative on 323 of 323 worlds** as `accopt_selectors.select_world`
under B2 + R1. Every downstream comparison therefore starts from a verified
reproduction, not a re-implementation.

Cache completeness: 323 worlds, 26,600 Pareto-band members, 9,690 seed-runs,
0 missing. No fresh-holdout world is present in the experiment: every world is
one of the 323 objective-validation worlds already in `artifacts/ov_ckpt`.

---

## 3. Candidate-side features actually built

323 worlds x 26,600 members, 44 s, **0 computational failures (0.00%)**.

* **Deterministic constant refit**: succeeded on **26,192 of 26,600 (98.5%)**.
  The 1.5% that fail closed are structures with no free constant, or where the
  refit would have exceeded the frozen 0.5% invalid-point ceiling. Structure was
  never changed; constants were fitted on TRAIN only; the world `test` split was
  used by nothing.
* **Cross-stratum**: `precursor_mz` tertiles plus one tertile split per
  effective-support descriptor, minimum 15 validation molecules per stratum,
  unavailable strata marked rather than fabricated.
* **Residual structure**: `|Spearman(e, ·)|` against all 12 frozen protocol
  descriptors, plus one predeclared mass x descriptor interaction diagnostic.

---

## 4. Architecture comparison, nested world-level CV

Outer 5-fold by world (the exact existing folds), inner 5-fold inside every
outer-training set for `(alpha, beta, gamma)`, the ranker's `C`, and the gate form.
No test-fold world ever touched a coefficient, a threshold or a variant choice.

| Architecture | support ungated | support e2e | **family** | exact | G1A | G1B | G1C | family gain |
|---|---|---|---|---|---|---|---|---|
| **A CURRENT_FINAL** | 55/56 | 54/56 | **47/56 (83.9%)** | 22 | 6/6 | 35/40 | 6/10 | — |
| B CONSTANT_REFIT | 55/56 | 54/56 | 46/56 (82.1%) | 19 | 6/6 | 35/40 | 5/10 | **-1.79 pp** |
| C ROBUST_GENERALIZATION | 55/56 | 54/56 | 45/56 (80.4%) | 19 | 6/6 | 35/40 | 4/10 | **-3.57 pp** |
| D SMALL_FAMILY_RANKER | 27/56 | 26/56 | 1/56 (1.8%) | 1 | 1/6 | 0/40 | 0/10 | **-82.14 pp** |

Constraints (ungated support >= 95%, e2e support >= 95%, null FPR <= 5%,
ROC AUC >= 0.98, computational failure <= 2%) are met by A, B and C; D fails the
support constraints outright. **No architecture reaches the +3 pp ship bar.**

C additionally causes a **catastrophic subgroup regression** that the primary
metric hides: G4M family recovery collapses from 17/30 to 4/30. On its own this
would have disqualified C.

G1B by noise regime, architecture A: low 10/10, moderate 19/20, **adverse 6/10**.
The whole positive-side deficit now lives in the adverse regime and in G1C.

---

## 5. Where each hypothesis landed

Within-world ranking information carried by each candidate-side feature —
mean ROC AUC for separating family-correct from family-incorrect band members,
inside a world, over the 53 positive worlds that contain both classes. 0.5 = no
information.

| Feature | mean within-world AUC (all positives) | G1B |
|---|---|---|
| `strat_min_r2` (worst-stratum R^2) | **0.709** | **0.712** |
| `complexity` (lower is better) | 0.700 | 0.725 |
| `strat_worst_norm_rmse` | **0.699** | **0.698** |
| `refit_valid_r2` | 0.686 | 0.679 |
| `valid_r2` (the incumbent signal) | 0.682 | 0.672 |
| `resid_max_abs_spearman` | 0.611 | 0.639 |
| `resid_interaction_spearman` | 0.606 | 0.611 |
| `strat_sd_r2` | 0.604 | 0.601 |
| `resid_med_abs_spearman` | 0.592 | 0.635 |
| `strat_median_r2` | **0.462** | **0.436** |
| `refit_valid_r2 - valid_r2` | 0.509 | 0.527 |

Three things follow, and they explain every outer-fold number above.

1. **Constant refitting carries essentially no new information.** The refit
   changes validation R^2 by a median of `3.6e-10`; only 5.9% of candidates move
   by more than 0.001; improvements and regressions are a coin flip (50.4% /
   49.6%). The *change itself* has AUC 0.509 — indistinguishable from noise.
   PySR already estimates its constants near-optimally on the training split, so
   the premise that structure discovery leaves constants badly estimated is
   **false in this system**.
2. **Cross-stratum robustness is real, but SCORE_C was pointed at the wrong
   summary.** The worst-stratum statistics (`strat_min_r2` 0.709,
   `strat_worst_norm_rmse` 0.699) beat raw validation R^2 (0.682). The **median**
   stratum R^2 — the term the preregistered `SCORE_C` uses — is at **0.462, below
   chance**. C was therefore built on the one cross-stratum summary that carries
   negative information, which is why it lost 2 worlds. This is a genuine,
   quantified miss in the preregistered design, and per the hard stop it is
   **recorded, not repaired**.
3. **Residual structure adds a little, but not enough to matter.** 0.61 AUC,
   above chance and below complexity. Its contribution inside `SCORE_C` (weight
   gamma) never became decisive: the inner CV chose `gamma = 0.25`, the smallest
   grid value, in every outer fold.

Concrete illustration on a real failure: in `OV|G1B|r005|adverse` the promoted
representative has `strat_median_r2 = 0.634` but `strat_min_r2 = 0.059`. The
median term sees a healthy candidate; the worst-stratum term sees the shortcut.

### Why D collapsed

D is not broken code; it is a correctly-fitted small model that learned the wrong
thing. Its dominant coefficient is `min_complexity` at **-0.86** — it learned
"prefer the simplest family". Diagnostics (`artifacts/sprint/d_diagnostic.json`,
**diagnostic only, nothing adopted**):

* 1,275 training rows, 7.9% positive; positives are present in 50 of 56 positive
  worlds, so the label is not degenerate.
* A positive world offers a median of 11.5 candidate families (range 1-37), so
  chance is roughly 1 in 12.
* Retraining on positive worlds only (excluding G3/G4M, whose simple mass power
  laws supply 38 of 94 scorable training worlds) moves it from 1/56 to **3/56**
  — still far below chance-corrected expectation and far below B2's 47/56.

The failure is structural, not a training-set artifact: 13 aggregate
family-level features, all of them world-relative quantities pooled across worlds
with wildly different achievable R^2, cannot recover a within-world ranking. The
hand-designed B2 vote wins because it is explicitly *within-world*.

---

## 6. Null gate — the two predefined forms, head to head

Both fitted on training folds only, maximising sensitivity subject to training
null FPR <= 5%, evaluated once per outer test fold.

| Gate | sensitivity | null FPR | specificity | balanced accuracy | ROC AUC | PR AUC |
|---|---|---|---|---|---|---|
| **CURRENT_GATE** (frozen) | **96.43%** (54/56) | 3.04% (7/230) | 96.96% | 96.69% | 0.99907 | 0.99685 |
| MONOTONIC_LINEAR_GATE | **96.43%** (54/56) | 2.61% (6/230) | 97.39% | 96.91% | 0.99907 | 0.99685 |

**The monotonic gate recovered no additional positives.** Sensitivity is
identical to the world — the same 54 of 56, the same two false negatives. It is
better on the secondary axis by exactly one null world (7 -> 6 false positives)
and one confounded world.

The frozen rule is "FPR <= 5%, then maximise sensitivity, ties to CURRENT_GATE"
(freeze doc 5, 9.5). Sensitivity is an exact tie, so **CURRENT_GATE is retained**.
A 1-world FPR difference is not evidence worth a production change, and honouring
the preregistered tie-break is the point of preregistering it.

Refusal-block behaviour under the frozen gate is unchanged from the baseline:
no-law worlds (NCAL+G4+GC, n=209) 8 reported / 3.8%; **mass-only worlds
(G3+G4M, n=38) 9 reported and 0 claiming any non-mass structure** — the K5 threat
is realised zero times; G5 0/8; G2 5/8 remains the weakest cell.

---

## 7. Error decomposition under the frozen architecture

Diagnostic only. Nothing was changed on the basis of it.

| Class | n |
|---|---|
| Correct | **47** |
| FAMILY_TOLERANCE_BOUNDARY | 4 |
| NULL_GATE_FALSE_NEGATIVE | 2 |
| SEARCH_FAILURE | 2 |
| FAMILY_AGGREGATION_FAILURE | 1 |
| REPRESENTATIVE_SELECTION_FAILURE | 0 |
| CONSTANT_ESTIMATION_FAILURE | **0** |
| CROSS_STRATUM_GENERALIZATION_FAILURE | 0 |

| World | class | rel_RMSE vs truth | best in pool | best after refit | family-correct members in pool |
|---|---|---|---|---|---|
| `OV\|G1B\|r004\|adverse` | tolerance boundary | 0.0997 | 0.0092 | 0.0152 | 18 |
| `OV\|G1B\|r005\|adverse` | tolerance boundary | 0.0751 | 0.0108 | 0.0088 | 30 |
| `OV\|G1B\|r007\|adverse` | tolerance boundary | 0.1024 | 0.0240 | 0.0240 | 4 |
| `OV\|G1C\|r008\|moderate` | tolerance boundary | 0.0978 | 0.0164 | 0.0234 | 17 |
| `OV\|G1B\|r009\|adverse` | gate false negative | 0.0967 | 0.0129 | 0.0129 | 3 |
| `OV\|G1B\|r015\|moderate` | gate false negative (correct refusal of a wrong report) | 0.1525 | 0.0008 | 0.0008 | 35 |
| `OV\|G1C\|r007\|moderate` | family aggregation | 0.1960 | 0.0752 | 0.0737 | 2 |
| `OV\|G1C\|r001\|moderate` | search (representability) | 0.1858 | **0.1653** | 0.1653 | **0** |
| `OV\|G1C\|r002\|moderate` | search (representability) | 0.1878 | **0.1572** | 0.1549 | **0** |

**CONSTANT_ESTIMATION_FAILURE is empty**: not one failure is explained by a
badly-estimated constant, and deterministic refitting rescues none of the four
tolerance-boundary worlds. The boundary cases were left visible, exactly as the
brief requires: `EXPONENT_TOL` and the family relative-RMSE tolerance were not
moved.

---

## 8. Exact headroom, recomputed over all 26,600 candidates

| Population | n | RAW_CANDIDATE_ORACLE | CONSTANT_REFIT_ORACLE | CURRENT_GRAMMAR_ORACLE |
|---|---|---|---|---|
| all positives — support | 56 | 56 | 56 | 56 |
| all positives — **family** | 56 | **54** | **53** | **54** |
| all positives — exact | 56 | 45 | 44 | 45 |
| G1A family | 6 | 6 | 6 | 6 |
| G1B family | 40 | 40 | 40 | 40 |
| G1C family | 10 | 8 | 7 | 8 |
| G3 family | 8 | 8 | 8 | 8 |
| G4M family | 30 | 22 | 23 | 23 |

`CURRENT_GRAMMAR_ORACLE` is the union of the two (the best any member of the
current grammar's output reaches, with or without optimal constants).

**Deterministic constant refitting does NOT raise the family ceiling — it lowers
it.** Across positive worlds, refitting makes 28 previously family-incorrect
members pass the frozen family definition and pushes **117** previously
family-correct members out of it, a net loss of 89 members and one world
(`OV|G1C|r005|moderate`). The mechanism is straightforward: constants are refitted
on 263 training molecules, while family adjudication is decided on a 2,000-point
dense lattice, so a train-optimal constant is not a lattice-optimal one. Only in
G4M does refitting rescue a world (`OV|G4M|r020|moderate`, 22 -> 23).

So: **some apparent family errors are not coefficient-estimation errors.** Zero
of them are.

Achieved 47 against a reachable 54: **seven of the nine errors remain selection
errors**, and only two are genuine search failures.

---

## 9. Is search still a meaningful bottleneck?

**No — 2 of 56 worlds (3.6%), and both for representability, not budget.**

Every G1B world still has a family-correct candidate in the pool. The two G1C
search failures have **zero** family-correct members among 30 seeds and every band
member, with a best achievable relative RMSE of 0.165 and 0.157 against a frozen
0.10 tolerance. Constant refitting moves those to 0.165 and 0.155 — nowhere near.
Section 10 shows that adding `exp` to the grammar does not move them either.

---

## 10. Conditional SAFE_EXP experiment — ran, and did not pay

Run only after A-D were frozen. G1C development worlds only. `K = 8.0` and a
SAFE_EXP complexity cost of 5 were fixed before any recovery number was seen.
30 search runs per world in both arms, `niterations`, population count and
population size identical to the frozen `PYSR_CONFIG`.

| | BASE_GRAMMAR (30 frozen seeds) | PORTFOLIO (15 frozen + 15 SAFE_EXP) |
|---|---|---|
| oracle family | 8/10 | **8/10** |
| **selected family** | **6/10** | **6/10** |
| oracle exact | 6/10 | 7/10 |
| selected support | 10/10 | 10/10 |
| median best rel_RMSE | 0.0159 | 0.0105 |
| worlds whose report uses SAFE_EXP | — | 2/10 |
| SAFE_EXP band members | 0 | 196 |

**Selected family recovery is unchanged at 6/10.** One world is rescued
(`r008`) and one is lost (`r005`) — a wash, not a gain. The operator is used
heavily where it is not needed (61, 33, 27, 26, 24 members in already-recovered
worlds) and is family-correct there, which is exactly the gratuitous-use pattern
the high complexity cost was supposed to suppress.

Decisively, **the two worlds it was designed for are not rescued**: `r001` and
`r002` attracted only **one** SAFE_EXP band member each, and their best
achievable relative RMSE improves from 0.1653 to 0.1562 and 0.1572 to 0.1549 —
both still far outside the 0.10 tolerance. The selected representative in `r001`
is byte-identical between the two arms.

**Verdict: SAFE_EXP is NOT adopted.** The controlled comparison does not improve
held-out G1C recovery. Scope: one K, one complexity cost, 15 seeds per world —
a bounded diagnostic, not an exhaustive test of grammar expansion. Full detail in
`MURU_SAFE_EXP_DIAGNOSTIC.md`.

---

## 11. Development replay with the frozen architecture

Descriptive only (gate fitted in-sample on the same 323 worlds):
support ungated 55/56, support end-to-end 55/56, family 47/56, G1B 35/40,
G1C 6/10, null FPR 4.35%, balanced accuracy 97.83%, ROC AUC 0.9991,
`t1 = 0.595`, `t2 = 0.2`. The held-out cross-validated numbers in section 1 are
the honest ones; the in-sample replay is quoted only because the brief asks for it.

---

## 12. Regression tests and leakage

No production architecture was adopted, so the brief's conditional
regression-test obligation is not triggered and no production file was modified.
`src/muru/**` is untouched by this sprint; everything new lives in
`scripts/sprint_*.py` and `artifacts/sprint/`. The existing suite was run and is
reported in section 14.

Leakage checks: (a) architecture A reproduces the frozen selector on 323/323
worlds; (b) selectors read only candidate-side statistics — truth fields exist in
the cache and are consumed exclusively to score a selection after it is made, and
by D's *training* label, which is a declared development-only use; (c) constants
were refitted on the world TRAIN split and scored on VALID; the world TEST split
is read by nothing in this study; (d) no fold was regenerated after seeing an
outcome, and folds are the exact frozen assignment; (e) no fresh-holdout world
exists in any artifact this sprint reads or writes.

---

## 13. The thirteen questions

1. **Did deterministic constant refitting improve family accuracy?** No.
   47 -> 46 held-out; the oracle ceiling *falls* 54 -> 53; the refit delta carries
   AUC 0.509. PySR's constants were already near-optimal.
2. **Did cross-stratum robustness distinguish correct laws from high-R^2
   shortcuts?** Partly, yes — but only in its worst-stratum form
   (`strat_min_r2` AUC 0.709 vs raw R^2 0.682). The preregistered `SCORE_C` used
   the *median* stratum, which is below chance at 0.462. Recorded, not repaired.
3. **Did residual structure add useful ranking information?** A little: AUC 0.611,
   above chance, below complexity, never decisive (inner CV always chose the
   smallest gamma).
4. **Did the small family ranker beat the hand-designed B2 score?** No — 1/56 vs
   47/56. A cross-world model on aggregate family features cannot reproduce a
   within-world ranking.
5. **Final held-out family recovery**: **83.9% (47/56)**, 95% CI [72.2%, 91.3%].
6. **Final support recovery**: **98.2% (55/56)** ungated, **96.4% (54/56)** end-to-end.
7. **Final null FPR**: **3.0% (7/230)**, 95% CI [1.5%, 6.1%].
8. **Did the monotonic gate recover additional positives at <=5% FPR?** No —
   sensitivity identical at 96.43%. It is better by one null world; the frozen
   tie-break retains CURRENT_GATE.
9. **Remaining error decomposition**: 4 tolerance boundary, 2 gate false
   negatives, 2 search (representability), 1 family aggregation, 0 representative
   selection, 0 constant estimation, 0 cross-stratum.
10. **New oracle ceiling after refitting**: 53/56 family — *lower* than the raw
    54/56.
11. **Is search still a meaningful bottleneck?** No: 2/56, both representability.
12. **Did SAFE_EXP materially improve G1C?** No — 6/10 both arms, and the two
    target worlds are untouched.
13. **Frozen architecture**: B2 validation-quality-weighted family vote + R1
    highest-validation-R^2 representative + the existing calibrated two-quantity
    gate + the corrected production parser + the frozen p3 grammar + SymPy.
    Recorded in `artifacts/sprint/architecture_freeze.json`.

---

## 14. Test suite

`python -m pytest tests -q` over the full suite: **8 failures**, and the
**identical 8 failures reproduce on a pristine checkout of the pre-sprint commit
`716cf97`** in a separate worktree. They are environment-closure and
paper-benchmark freeze-hash tests, all tripping on `INTEGRITY BREACH: unexpected
change: .gitignore`, a file this sprint did not touch (`git diff 716cf97 HEAD --
.gitignore` is empty).

**This sprint introduces zero test regressions**, which is expected: `src/muru/**`
was not modified.

```
tests/test_eng_environment_closure.py            3 pre-existing failures
tests/test_paper_benchmark_amendment_integrity.py        2 pre-existing failures
tests/test_paper_benchmark_amendment_a2_1_integrity.py   2 pre-existing failures
tests/test_rc5_authorized_delta.py               1 pre-existing failure
```

---

## 15. Artifacts

```
MURU_FINAL_ACCURACY_SPRINT_FREEZE.md      design frozen before any comparison
MURU_FINAL_ACCURACY_SPRINT.md / .json     this report
MURU_SAFE_EXP_DIAGNOSTIC.md / .json       conditional grammar experiment
artifacts/sprint/architecture_freeze.json     the frozen architecture + hashes
artifacts/sprint/candidate_feature_cache.json 26,600 members x feature groups 1-3
artifacts/sprint/nested_cv_results.json       every outer fold, every inner grid
artifacts/sprint/outer_fold_predictions.json  every held-out selection, all 4 architectures
artifacts/sprint/error_decomposition.json     the 9 remaining failures
artifacts/sprint/headroom_summary.json        three oracle ceilings
artifacts/sprint/headroom_members.json        per-member raw and refit truth scores
artifacts/sprint/feature_signal.json          within-world AUC of every feature
artifacts/sprint/d_diagnostic.json            why D collapsed (diagnostic only)
artifacts/sprint/gate_comparison.json         both gate forms, per fold
artifacts/sprint/development_replay.json      in-sample replay
artifacts/sprint/safeexp_runs.json / safeexp_score.json
```

```
scripts/sprint_features.py        feature groups 1-3
scripts/sprint_arch.py            architectures A-D, both gates, folds
scripts/sprint_run.py             nested CV
scripts/sprint_gate.py            gate head-to-head + error decomposition
scripts/sprint_headroom.py        three oracle ceilings
scripts/sprint_signal.py          per-feature within-world information
scripts/sprint_d_diagnostic.py    D post-mortem (adopts nothing)
scripts/sprint_replay.py          development replay
scripts/sprint_safeexp.py         SAFE_EXP search
scripts/sprint_safeexp_score.py   SAFE_EXP scoring
scripts/sprint_write.py           freeze + JSON assembly
```

---

## 16. HARD STOP

The predefined experiment ran to completion, all four architectures and both
gates were scored under nested world-level cross-validation, and the incumbent
won. **CURRENT_FINAL is frozen.** No further score, ranker, tolerance, CAS or
grammar operator is proposed. The next experiment is the genuinely fresh
holdout, which this task did not touch.
