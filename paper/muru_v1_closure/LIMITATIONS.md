# MURU ConjectureLab v1 — Limitations

Ordered by how much they constrain what may be claimed.

## 1. The claim boundary is synthetic machinery, not chemistry

**This study says nothing about real collision-induced dissociation.**

Every case is generated from a planted law by a frozen generator. No measured spectrum, no real
compound, and no observed fragmentation intensity enters any case, fit, endpoint or gate. The
benchmark asks whether the pipeline recovers structure known to be present by construction and
refuses structure known to be absent by construction. It cannot answer whether any such structure
exists in real CID data, whether the model family is appropriate to real data, or how the pipeline
would behave on it.

The real-data **Confirmation** partition remains sealed and unopened. Nothing in these results
licenses any inference about it, in either direction. A failure here is a failure of this machinery
on this synthetic population — it is not evidence that the underlying scientific conjecture is
false, and a success would not have been evidence that it is true.

## 2. The generator is also the ground truth

The planted laws are drawn from the same grammar the search explores. This makes recovery *possible*
in principle, which is what a benchmark needs — but it also means the benchmark cannot detect a
mismatch between the grammar and reality, because no such mismatch exists by construction. The one
deliberate exception is F20C, an out-of-grammar trap, and it contributes 4 cases.

A benchmark in which the truth is always representable measures search and selection competence,
not modelling adequacy. Read the results accordingly.

## 3. The outcome was determined upstream of the machinery under test

154 of 240 cases terminated at A1 adequacy and a further 43 at seed stability — 82% of the partition
lost before any of the gates the falsification framework was built to enforce. Gate 7 and Gate 8
rejected one case each.

This constrains the study's informativeness in a specific way: **the falsification framework is
largely untested by this partition.** Three of the four hard rungs never rejected anything, and the
Gate 7 waiver branch was never entered. Their correctness is established by construction and by
unit tests, not by having discriminated on this evidence. A benchmark that concludes at its first
gate has measured its first gate.

## 4. `BOUNDARY_LIMITED` dominates, and its frequency was not anticipated

97 of G1's 164 cases and 154 of all 240 returned `BOUNDARY_LIMITED` from the A1 ladder — the
scalar fit pressing against the frozen `log_g ∈ [-2, 2]` bound. The frozen contract classifies this
as UNEVALUABLE, correctly and conservatively: a fit at its boundary has not demonstrated adequacy.

But the *rate* is the single largest driver of the study's outcome, and it is a property of the
interaction between the generator's parameter ranges and the estimator's frozen bounds — not a
property of the discovery pipeline the benchmark set out to evaluate. Whether that interaction is a
correctly-calibrated conservatism or an over-tight bound cannot be settled from this evidence, and
must not be settled post hoc. It is the first question for v2.

## 5. G3's failure is unevaluability, not observed unsafety

All 26 G3 violations are UNEVALUABLE cases; there are zero `UNSAFE` events. On the ten safety cases
the pipeline could evaluate, it was safe ten times out of ten.

The endpoint fails legitimately — the contract was frozen prospectively to treat unevaluability as
a violation, because a system that cannot evaluate a null world has not shown it would refuse one.
But "the system accepted forbidden structure" and "the system could not reach a verdict" are
different failures with different remedies, and only the second occurred. Any summary that reports
G3's 72% violation rate without this distinction is misleading.

## 6. G1 observables were recovered, not persisted

The sealed record schema `muru-rc5-case-record-2.0.0` persists no G1 observable. The exact G1 result
reported here was recomputed from frozen deterministic inputs with zero searches, and content
identity was verified by re-deriving A1 adequacy and matching all 164 sealed verdicts.

That check is strong — A1 is a sensitive function of the full trajectory matrix — but it is an
empirical identity test, not a stored per-case content digest. The execution manifest carries no
per-case content hash. A reader who does not accept the A1 agreement as sufficient evidence of
content identity cannot independently confirm the G1 point estimate from the sealed bytes alone,
though the **gate verdict** remains provable from them: `m0_accepted` is recoverable directly from
the sealed A1 status, and it alone bounds competence at ≤ 67, far below the gate.

A schema successor persisting the four G1 observables is specified but has not been exercised,
because no partition may be rerun.

## 7. One configuration, no sensitivity analysis

Grammar, search budget, 30 seeds per case, the selection rule, the stability gate at 20/30, the
complexity cap at 20, the null calibration table, the ceiling estimator, and every threshold were
frozen before execution and none was varied. This is what makes the result honest; it is also what
makes it narrow.

The study reports what this configuration did. It cannot attribute the failure to any particular
frozen choice, and no such attribution should be inferred. The seed-stability attrition (43 cases)
in particular is consistent with either a genuinely unstable search or a stability gate set tighter
than the search's reproducibility warrants; this evidence cannot distinguish them.

## 8. The analysis contract failed once and was repaired

The originally reported analysis inverted the verdict. It was reconstructed against the frozen
contract, cross-checked by a structurally independent recomputation and seven hostile lenses, and
reproduces the sealed pre-repair forensic result exactly — a result that was cryptographically
sealed before the repair was written.

Two residual honesty points. First, the defect reached a reported result at all, which is a process
failure independent of its correction; the governance chronology records how. Second, the repair was
performed by a context that knew the outcome. That is why the numbers were required to match a
target sealed in advance, why the independent recomputation shares no object with the primary
analyzer, and why the Challenge adjudication was delegated to an outcome-blind context. Those are
mitigations, not proofs of impartiality.

## 9. Statistical scope

Wilson 95% intervals on binomial proportions, one per endpoint, with fixed prospective denominators.
There is no multiplicity adjustment across the three endpoints — none is needed, since the decision
rule is a conjunction and all three failed. Cases within a family are replicates of a generator
configuration and are treated as independent; any within-family dependence would widen the true
intervals, which cannot rescue a failing gate but would matter had one passed.

The three margins (0.364, 0.689, 0.692) are large relative to any plausible correction, so the
verdicts are robust to these considerations. That robustness is asymmetric: it supports the failure
conclusion and would not have supported a pass conclusion at similar margins.

## 10. Pre-existing defects disclosed but not repaired

The A3.5 authorized-delta ledger pins `rc5_authorization.py` at its pre-A3.6 hash, so A3.6 changed a
pinned file without a corresponding ledger entry, and a repository test fails as a result. This is
governance bookkeeping, not science: the A3.6 change is authorization-only and was independently
verified. It was deliberately not repaired here, because editing a frozen A3.5 ledger to accommodate
a later amendment would falsify what that ledger attests.
