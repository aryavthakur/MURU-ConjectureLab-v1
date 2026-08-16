# MURU ConjectureLab v1 — Final Scientific Disposition

## **MURU V1 CURRENT-CONTRACT SYNTHETIC BENCHMARK COMPLETE**

## 1. Claim boundary — read this first

**This study evaluated synthetic machinery. It makes no claim about real collision-induced
dissociation chemistry.**

Every one of the 240 evaluated cases was generated from a planted law by a frozen generator. No
measured spectrum, no real compound, and no observed fragmentation intensity entered any case, fit,
endpoint or gate. The benchmark asked whether a symbolic-discovery pipeline recovers structure known
to be present by construction and refuses structure known to be absent by construction.

A failure here is a failure of **this machinery on this synthetic population under this frozen
configuration**. It is not evidence that the underlying scientific conjecture is false, and a
success would not have been evidence that it is true. The real-data **Confirmation** partition
remains sealed and unopened; nothing here licenses any inference about it in either direction.

## 2. Primary endpoint dispositions

| Endpoint | Denominator | Result | Wilson 95% | Gate | Margin | Disposition |
|---|---|---|---|---|---|---|
| **G1** scalar competence | 164 | 67 competent (40.9%) | lower **0.336233** | ≥ 0.70 | −0.364 | **FAIL** |
| **G2** family recovery | 144 | 4 successes (2.8%) | lower **0.010854** | ≥ 0.70 | −0.689 | **FAIL** |
| **G3** structural safety | 36 | 26 violations (72.2%) | upper **0.841518** | ≤ 0.15 | +0.692 | **FAIL** |

**All three primary endpoints fail, independently.** The frozen decision rule — the conjunction of
the three Wilson gates, with no existence test and no composite score — returns **false**, and would
return false on any one of the three alone.

Under the frozen post-endpoint rule (`MURU_PAPER_BENCHMARK_METRICS.md`), *"any failed gate blocks
the positive claim while retaining descriptive endpoint reports."* Accordingly:

> **The positive umbrella claim is BLOCKED. This study does not claim that MURU recovers
> meaningful family-level mathematical structure while rejecting specified null and adversarial
> worlds.** Descriptive endpoint reporting is retained and is what this package delivers.

Supporting counts, none of which is an endpoint rate: Gate 7 reached by 27 cases and passed by 26;
Gate 8 reached by 26 and passed by 25; `STRUCTURAL_ACCEPTED` 25 of 240.

## 3. Dominant failure mechanisms

### 3.1 A1 adequacy — the dominant mechanism overall

154 of 240 cases (64%) terminated at the first gate. Within G1's population, 97 of 164 returned
`BOUNDARY_LIMITED` — the M0 fit pressing against the frozen `log_g ∈ [-2, 2]` grid — which the
frozen contract classifies as UNEVALUABLE.

The exact G1 recovery makes the consequence unambiguous:

| Stratum | Cases | both continuous conjuncts pass | competent |
|---|---|---|---|
| A1 established | 67 | **67** | **67** |
| A1 not established | 97 | 87 | **0** |

**Every case whose adequacy was established passed both continuous conjuncts — 67 of 67.** Zero
cases failed on `g_spearman` alone; zero on `trajectory_mae` alone; zero recorded a contract
failure. Across all 164, `g_spearman` has median 0.9806 against a 0.80 gate and the trajectory skill
ratio has median 0.3622 against a 0.80 gate.

**G1 does not fail because the scalar estimator is inaccurate. It fails because adequacy was
established for only 41% of its population.**

### 3.2 Symbolic search and selection — the one endpoint that fails on its own terms

G2 recorded 4 successes from 144, with **103 outright failures** and 37 unevaluable. Eight of the
twelve G2-carrying families recorded no success at all, and the noiseless family F01 — the easiest
in the benchmark — succeeded in only 2 of 12 replicates.

These are resolvable-but-wrong outcomes, not unevaluability. G2's failure points squarely at the
discovery pipeline: the search and selection machinery did not recover the planted family, even
where the signal is clean.

### 3.3 Unevaluability propagating into safety

All 26 G3 violations are UNEVALUABLE cases. **There are zero `UNSAFE` events**: the pipeline never
accepted a forbidden structure in a safety family, and both safety cases it did accept carried
mass-only support, which their variants permit. On the ten safety cases it could evaluate, it was
safe ten times out of ten.

G3's failure is legitimate — the contract was frozen prospectively to treat unevaluability as a
violation, because a system that cannot evaluate a null world has not shown it would refuse one.
But the failure mode is **inability to reach a verdict**, not **reaching a wrong verdict**, and any
summary reporting the 72% violation rate without that distinction is misleading.

### 3.4 Seed instability — the largest post-adequacy attrition

Of the 86 cases clearing A1, 43 were lost at `selection_fraction ≥ 20/30`. This evidence cannot
distinguish a genuinely unstable search from a stability gate tighter than the search's
reproducibility warrants, and that question must not be settled post hoc.

### 3.5 The falsification framework is largely untested by this partition

A1 adequacy and seed stability together account for 82% of the 240 cases. Gate 7 and Gate 8 rejected
**one case each**. Three of the four hard rungs never rejected anything, and the Gate 7 waiver
branch — into which F5's floor was folded by A3.5 — was never entered, making that amendment
outcome-invariant on this evidence as a matter of fact.

A benchmark that concludes at its first gate has measured its first gate. The falsification
framework's correctness here rests on construction and unit tests, not on demonstrated
discrimination.

## 4. Partition dispositions

| Partition | Cases | Disposition |
|---|---|---|
| Development | 80 | executed, used for development |
| **Held-out** | **240 (7,200 searches)** | **executed once, sealed, analysed, frozen. All three primary endpoints FAIL.** |
| Challenge | 60 | **UNOPENED BY FROZEN GOVERNANCE** — see `MURU_CHALLENGE_DISPOSITION.md` |
| Confirmation (real data) | — | **SEALED, NEVER OPENED** |

Challenge was adjudicated by an outcome-blind context which found it authorized by nothing frozen,
and found that verdict identical under both Held-out counterfactuals. `AUTHORISED_PARTITIONS`
remains `{"development", "held_out"}`.

## 5. Evidence integrity

| Attestation | Status |
|---|---|
| Sealed files re-hashing correctly | **482 / 482** |
| Records faithful to the frozen acceptance predicate | **240 / 240, 0 disagreements** |
| Execution failures across 7,200 searches | **0** |
| Execution-failure-poisoned cases per endpoint | **0 / 0 / 0** |
| Searches rerun during analysis or repair | **0** |
| Sealed files modified | **0** |
| Frozen source files modified | **0** (`git diff 8d87143 HEAD -- src/` empty) |
| Frozen thresholds / denominators verified against amendment values | **14 / 14, zero drift** |
| G1 recovery content-identity checks | **164 / 164, 0 mismatches** |
| Independent recomputation disagreements | **0 / 20 quantities** |
| Hostile lens failures | **0 / 66 checks** |
| Restoration tests | **52 passed** |

Because no endpoint is contaminated by execution failure, every UNEVALUABLE outcome reported is a
scientific result rather than an infrastructure artifact.

## 6. The analysis-contract failure, stated plainly

The originally reported Held-out analysis **inverted this study's verdict**, reporting
`decision_passed: true`. Its analyzer scored every endpoint over a 240 denominator, substituted
`candidate_test_r2` for G1, relaxed G2's conjunction to a disjunction, inverted G3's direction,
conflated Gate 7 with full structural acceptance, composed Gate 8 as the explicitly prohibited
"Gate 7 AND G1", and accepted `BOUNDARY_LIMITED` — plus a status that does not exist — as adequate,
making its adequacy test true for all 240 cases. Every deviation ran in the permissive direction.
Its two accompanying checks could not have caught it: the "independent" recomputation imported the
analyzer it audited, and the hostile review's denominator lens *asserted* the defective 240.

**What the governance got right.** Because the contract was frozen prospectively and the raw
evidence sealed before analysis, the defect was fully detectable and fully correctable from bytes
already on disk. The correct result was recovered without rerunning a single search, and the
forensic reconstruction was cryptographically sealed before the repair was written, fixing the
target in advance.

**What it got wrong.** A defective analysis reached a reported result, and its self-checks were
constructed so as to be incapable of failing. The remedies adopted — reconstruct rather than assert,
enforce independence structurally, and prove by mutation that every check can fail — are carried
forward as standing requirements.

**Residual honesty point.** The repair was performed by a context that knew the outcome. Requiring
the numbers to match a target sealed in advance, building an independent recomputation that shares
no object with the primary analyzer, and delegating the Challenge adjudication to a blind context
are mitigations, not proofs of impartiality.

## 7. What is established, and what is not

**Established, for this synthetic population under this frozen configuration:**

- Symbolic family recovery failed comprehensively (4/144), including on noiseless cases.
- Scalar competence is perfect conditional on adequacy (67/67) and the endpoint nevertheless fails,
  because adequacy holds for only 41% of the population.
- The safety endpoint fails on unevaluability, with zero observed unsafe acceptances.
- Attrition is dominated by A1 adequacy and seed stability, both upstream of every falsification
  gate.

**Not established, and not claimed:**

- Anything about real CID chemistry, real spectra, or any measured analyte.
- Anything about performance under a different grammar, budget, selection rule, adequacy ladder or
  calibration — all frozen, none varied, no sensitivity analysis performed.
- Anything about the Challenge partition, unopened, or the Confirmation partition, sealed.
- Any robustness claim from F9. Its 26/26 PASS is `NOT_PROVEN_FOR_HARD_GATE` and the A3.5 §6.9.4
  drafting guard **forbids citing it as evidence of validated robustness**. That guard survives this
  closure and binds any successor.

## 8. Evidence package

| Artifact | Contents |
|---|---|
| `paper/muru_v1_closure/METHODS.md` | manuscript Methods |
| `paper/muru_v1_closure/RESULTS.md` | manuscript Results |
| `paper/muru_v1_closure/LIMITATIONS.md` | manuscript Limitations |
| `paper/muru_v1_closure/GOVERNANCE_CHRONOLOGY.md` | freeze line and governance events |
| `paper/muru_v1_closure/REPRODUCIBILITY_INVENTORY.md` | digests, environment, verification recipes |
| `paper/muru_v1_closure/tables/` | T1–T9, generated from the artifacts |
| `paper/muru_v1_closure/figure_data/` | F1–F4 figure data |
| `paper/muru_v1_closure/POST_RESULT_FUTURE_WORK_MURU_V2.md` | v2 plan — **post-result, no prospective authority** |
| `audit/MURU_HELDOUT_RESTORED_ANALYSIS.md` | the restored analysis |
| `audit/MURU_HELDOUT_INDEPENDENT_RECOMPUTATION.md` | the independent cross-check |
| `audit/MURU_HELDOUT_RESTORATION_HOSTILE_REVIEW.md` | seven lenses, 66 checks |
| `audit/MURU_HELDOUT_SUPERSESSION_LEDGER.md` | what was superseded, with hashes |
| `audit/MURU_HELDOUT_RESTORATION_FINAL_DISPOSITION.md` | restoration disposition and hashes |
| `audit/MURU_CHALLENGE_BLIND_ADJUDICATION.md` | the blind adjudication |
| `audit/MURU_CHALLENGE_DISPOSITION.md` | Challenge disposition |
| `audit/MURU_HELDOUT_RESCUE_*.md` | the five forensic rescue artifacts |

---

**MURU V1 CURRENT-CONTRACT SYNTHETIC BENCHMARK COMPLETE**

**FINAL SCIENTIFIC DISPOSITION FROZEN**
