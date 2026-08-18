# POST-RESULT FUTURE WORK — MURU v2

## 0. Status of this document

**This is post-result reasoning and carries no prospective authority.**

It was written *after* the Held-out outcome was known. Every proposal in it is therefore suspect in
exactly the way v1's governance exists to prevent: a change proposed after seeing a failure is
indistinguishable, from the outside, from a change chosen because it would have avoided the failure.

Consequently:

- **Nothing here may be applied to v1.** v1's contract is frozen, its result is frozen, and it is
  closed. No threshold, denominator, gate, family definition or role in v1 is revisited.
- **Nothing here is authorized.** Each item must be independently justified, prospectively frozen,
  and calibrated against a population never before drawn, *before* any v2 execution.
- **This document is deliberately kept separate** from the Methods, Results, Limitations and
  disposition, so no reader can mistake a proposal for a finding.
- The v1 Challenge and Confirmation partitions are **not** available to v2 as development or
  calibration material. Consuming a sealed partition to tune a successor destroys it.

## 1. What v1 actually established

Stripped of everything else, three findings should drive v2:

1. **The benchmark concluded upstream of the machinery it was built to test.** 154 of 240 cases
   stopped at A1 adequacy and 43 more at seed stability — 82% of the partition — while Gate 7 and
   Gate 8 rejected one case each. The falsification framework is largely untested by this evidence.
2. **Scalar competence is high conditional on adequacy, and adequacy is rare.** All 67 cases whose
   A1 adequacy was established passed both continuous conjuncts; zero failed on either alone. The
   scalar estimator is not the bottleneck. The adequacy verdict is.
3. **Symbolic family recovery failed comprehensively and on its own terms** — 4 of 144, including
   only 2 of 12 in the noiseless family — with 103 outright failures rather than unevaluable
   outcomes. This is the one endpoint whose failure is not explained by unevaluability.

A fourth, quieter finding: **G3 recorded zero unsafe acceptances.** Every G3 violation is an
unevaluability penalty. On the ten safety cases the pipeline could evaluate, it was safe ten times
out of ten.

## 2. The first question, which must be answered before anything else

**Is `BOUNDARY_LIMITED` at 64% of the partition a correctly-calibrated conservatism or an
over-tight bound?**

`BOUNDARY_LIMITED` means the M0 fit pressed against the frozen `log_g ∈ [-2, 2]` grid. Two readings
are consistent with the v1 evidence and it cannot distinguish them:

- **Correct conservatism.** The generator draws `g` values genuinely outside the range over which
  M0 is identifiable, and the ladder is right to decline. Then v1's result is the honest one and the
  benchmark is telling us the model family is too narrow for its own generator.
- **Over-tight bound.** The grid is narrower than the identifiable range, so adequacy is declined
  for cases that were in fact evaluable. Then v1's headline is dominated by an estimator
  configuration rather than by discovery competence.

**This must be settled by construction, not by widening the bound and observing that more cases
pass.** The latter is precisely the post-hoc move v1's governance forbids, and it would be
unfalsifiable: widening a bound always increases the pass rate.

Proposed v2 approach, to be prospectively frozen:

- Instrument the *generator* to record, per case, the true `log g` distribution and whether it lies
  inside the estimator's identifiable range. This is available without any search, from the planted
  truth.
- Report the joint distribution of `BOUNDARY_LIMITED` against true-`g`-in-range **as a prospective
  secondary endpoint of v2**, so the diagnostic is committed to before it is observed.
- Only if that diagnostic shows the bound excluding genuinely identifiable cases does a bound change
  become justifiable — and it would then require its own amendment, its own calibration against a
  fresh population, and a re-derivation of A1's contrasts, since M1/M2/M3 are defined relative to M0.

## 3. Candidate v2 work items

Each requires independent prospective justification. Listed with what would have to be true for it
to be legitimate.

### 3.1 Persist G1 observables (record schema successor)

`muru-rc5-case-record-2.0.0` persists no G1 observable, which is why v1's G1 point estimate had to
be recovered by recomputation rather than read from the seal. A successor schema adding
`g_spearman`, `trajectory_mae`, `per_energy_mean_mae` and `m0_accepted` is **purely additive,
introduces no rule, and changes no verdict.**

*Legitimacy*: unambiguous. This is a persistence fix, not a science change. It should be the first
v2 engineering item.

### 3.2 Add a per-case content digest to the execution manifest

v1 has no per-case content hash, so content identity for any post-hoc recomputation must be
established empirically. Recording `content_hash` per case in the manifest makes it a digest
comparison instead.

*Legitimacy*: unambiguous. Provenance only.

### 3.3 Separate "unevaluable" from "unsafe" in the safety endpoint's reporting

G3's frozen conservatism — UNEVALUABLE counts as a violation — is correct and should be retained:
a system that cannot evaluate a null world has not shown it would refuse one. But v1's 72%
violation rate and its 0 unsafe acceptances are very different facts, and a single number reports
them as one.

*Proposal*: retain the frozen gate exactly as is, and add a **prospectively frozen secondary
decomposition** reporting violations by cause (unevaluable / unsafe-accepted). No change to the
gate, the denominator or the direction.

*Legitimacy*: defensible, because it adds reporting without relaxing anything. It must be frozen
before v2 execution, not added after.

### 3.4 Investigate seed-stability attrition

43 cases were lost at `selection_fraction ≥ 20/30`, the largest post-adequacy attrition. v1 cannot
distinguish a genuinely unstable search from a stability gate tighter than the search's
reproducibility warrants.

*Proposal*: a **development-partition-only** study of the selection-fraction distribution as a
function of seed count and search budget, reported as a v2 design input. The stability gate itself
must not be moved on the basis of Held-out attrition.

*Legitimacy*: the study is legitimate; changing the gate because 43 cases failed it is not.

### 3.5 Exercise the falsification framework

Three of four hard rungs never rejected anything and the Gate 7 waiver branch was never entered.
Their correctness rests on construction and unit tests, not on discrimination against this evidence.

*Proposal*: a prospectively designed **adversarial development population** built to trigger each
rung and the waiver branch at least once, so v2's falsification framework arrives with demonstrated
discriminative power. This is development material and must never touch a sealed partition.

*Legitimacy*: strong. It tests the machinery rather than relaxing it.

### 3.6 Symbolic recovery: diagnose before changing anything

G2 failed at 4/144 with 103 resolvable-but-wrong outcomes. That is a *search and selection* failure,
not an unevaluability failure, and it is the one v1 result that points squarely at the discovery
pipeline.

*Proposal*: a development-partition diagnostic decomposing the 103 failures by whether support was
recovered but family was not, family but not support, or neither — and, for the noiseless family
specifically, whether the true expression was ever *visited* by the search and lost at selection, or
never visited at all. Those two have opposite remedies.

*Legitimacy*: diagnosis is legitimate. Changing the grammar, budget or selection rule in response
to Held-out failure counts is not, and would require a fresh amendment plus a fresh calibration.

### 3.7 Governance carried forward as standing requirements

v1's freeze discipline worked — the defect was detectable and fully correctable from bytes already
on disk, with no rerun. What failed was that a defective analysis reached a reported result, with
self-checks constructed so as to be incapable of failing. Carry forward as **binding**:

- An independent recomputation **must not import** the primary analyzer, and the non-import must be
  enforced structurally and tested.
- Every review check **must be demonstrated able to fail**, by mutation test, before the review is
  accepted. A check that cannot fail is not a check.
- Analysis machinery must be **committed before execution**, not merely authored before it. v1's
  machinery was authored outcome-blind but left untracked, which is exactly why post-outcome edits
  could not be distinguished from plumbing by commit history.
- Endpoint denominators must come from the registry, and the frozen scorers' length assertions must
  be reachable on every analysis path.

## 4. What v2 must not do

- Reuse v1's Challenge or Confirmation partitions as development or calibration material.
- Relax any v1 threshold, denominator, gate or role on the basis of v1's failure counts.
- Promote F9 to a hard gate without a prospectively frozen, F9-specific calibration against a
  never-before-drawn population. Its status is `NOT_PROVEN_FOR_HARD_GATE` in **both** directions.
- Cite v1's F9 26/26 PASS as evidence of robustness. The A3.5 §6.9.4 drafting guard survives v1's
  closure and binds any successor.
- Re-analyse v1's Held-out evidence under a v2 contract and report the result as a v1 finding. v1's
  result is frozen; a v2 re-analysis would be a new, clearly-labelled secondary study.
- Treat any v1 failure as evidence about real CID chemistry. v1 evaluated synthetic machinery.

## 5. The honest framing for v2

v1 asked whether this pipeline recovers planted structure and refuses absent structure. The answer
on this synthetic population is **no, comprehensively**, and the largest single reason is that the
adequacy prerequisite was not satisfiable for most of the population.

v2's first job is therefore not a better search. It is to determine whether the adequacy
prerequisite is measuring what it was meant to measure — and to do that with the same prospective
discipline v1 used, before touching anything downstream of it.
