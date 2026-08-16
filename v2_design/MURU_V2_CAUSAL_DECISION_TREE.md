# MURU v2: Causal Decision Tree

**Status:** DESIGN ONLY. No experiment has been executed, so no branch of this
tree has been taken. No v2 scientific architecture is chosen here.

**Rule of construction:** every node is an experiment result and every edge is a
design change that result justifies. A design change that appears on no edge is
**not licensed**. There is no path from "we would like G2 to be higher" to a
change; every path starts at a measurement.

**Rule of exclusion:** every branch has a `NO CHANGE LICENSED` leaf. A leaf that
merely reports a finding and changes nothing is a legitimate and frequent
outcome.

---

## 0. Dependency order

Experiments are not independent. The order below is forced by what each one needs
to be interpretable.

```
E0  admissible-range provenance
 |
 +--> E1  joint evaluability and detector power        [needs E0's ceiling verdict]
 |
E3  descriptor identifiability                          [independent, run early]
 |
E2  Pareto front instrumentation                        [independent, run early]
 |
 +--> E4a retention policy         [needs E2]
 +--> E4f classifier / voting      [needs E2]
 +--> E4b search budget            [needs E2 AND E3]
 +--> E4c objective / parsimony    [needs E2 AND E3]
 +--> E4d grammar / operators      [needs E3]
 +--> E4e coefficient regime       [needs E3 for c*_oracle]
 |
E5  F18 resolution                                      [gated by E3, informed by E4d]
 |
E6  false-structure and safety counterweight            [runs against EVERY candidate change; holds veto]
 |
v2 architecture proposal                                [separately authorised; not in scope here]
```

E1 and E3 can run concurrently. E2 can start as soon as compute is free. E4's
arms serialise behind their prerequisites. E6 is not a stage at the end; it runs
against each candidate change as that change becomes a candidate.

---

## 1. Branch A: the A1 defect (RC1 and RC2, G1 and G3)

### A.0 E0, admissible-range provenance

```
E0: decouple generator response clip from fitter MU_CEIL, true-M0 worlds only
 |
 |-- boundary_limited_rate falls by MORE THAN 0.50
 |     => H_clip confirmed. The boundary event is manufactured by the
 |        coincidence MU_CEIL == generator clip.
 |     CHANGE: re-derive the M3 admissible ceiling from an identifiability
 |             argument rather than inheriting the generator's clip constant.
 |             This is a specification repair, not a threshold change, and it
 |             introduces no free parameter.
 |     THEN: E1 runs with the re-derived ceiling as control and the v1 ceiling
 |           as a reported arm.
 |
 |-- falls by 0.10 to 0.50
 |     => H_clip and H_alias both contribute.
 |     CHANGE: none yet. E1 runs with the ceiling as an explicit third factor.
 |
 |-- falls by LESS THAN 0.10
       => H_null. MU_CEIL exonerated.
       CHANGE: NO CHANGE LICENSED. E1 runs with MU_CEIL fixed at the v1 value
               and the floor question is the whole question.
```

### A.1 E1, joint evaluability and detector power

```
E1: criteria C0..C4 x rules P0..P3, on 51 cells, CALIBRATE split
 |
 |-- (a) An admissible pair exists AND C4 (verdict invariance) is selected
 |     => The v1 boundary defect was a decision-irrelevance defect: compounds
 |        were removed for boundary contact that could not have changed the
 |        contrast verdict.
 |     CHANGE 1: replace `obj < best_obj - 1e-12` with the verdict-invariance
 |               test. Zero new magnitude parameters.
 |     CHANGE 2: adopt the selected practical-win rule.
 |     GATE: confirm once on the sealed CONFIRM split; then E6 veto.
 |
 |-- (b) An admissible pair exists but the selected criterion is C1/C2/C3
 |     => A magnitude or interval floor is genuinely needed.
 |     CHANGE: adopt the floor at the selected value, prospectively calibrated
 |             on fresh worlds, with its measured false-rejection rate and
 |             alpha_star recorded as part of the contract.
 |     GATE: confirm on CONFIRM; then E6 veto.
 |
 |-- (c) No pair admissible at alpha = 1.0, but admissible at alpha >= 2.0
 |     => H2. The v1-planted deviation amplitudes lie below the detection floor
 |        of a 30-compound, 6-energy LOEO contrast. F13 to F16 were not tests
 |        of the detector.
 |     CHANGE: NO THRESHOLD CHANGE LICENSED.
 |             Report alpha_star_D as the endpoint's declared sensitivity limit.
 |             Two permitted follow-ons, each separately authorised:
 |               (i)  change the acquisition geometry (more energies per
 |                    compound, more test compounds), which is a prospective
 |                    benchmark design question; or
 |               (ii) re-declare the planted amplitudes, permitted ONLY under
 |                    the difficulty guard (section 5).
 |
 |-- (d) No pair admissible at any alpha
 |     => H3. Evaluability and power trade off with no admissible point.
 |     CHANGE: NO CONSTANT IN adequacy.py MAY BE EDITED ON THIS EVIDENCE.
 |             Escalate to redesigning the adequacy statistic itself. The LOEO
 |             practical-win contrast over 30 compounds is the object under
 |             suspicion, not its thresholds.
 |
 |-- (e) A pair is selected on CALIBRATE but fails on CONFIRM
       => Failure to replicate.
       CHANGE: NO CHANGE LICENSED. Report the non-replication. Do not re-select
               on CONFIRM; that would spend the only internal replication.
```

### A.2 The G1 and G3 consequence

G1 and G3 are one problem. Any change adopted on branch A.1 (a) or (b) is
projected onto both, and both projections are reported together:

```
Adopted A1 rule
 |
 |-- G1 projection: expected adequacy-conjunct pass rate on fresh worlds
 |-- G3 projection: expected UNEVALUABLE rate, and hence violation rate
 |
 +--> E6 measures unsafe structural acceptance under the new rule, on at least
      100 evaluable safety opportunities.
      |
      |-- unsafe acceptance Wilson upper <= 0.15  => change survives
      |-- unsafe acceptance Wilson upper >  0.15  => VETO. Change rejected
            regardless of its G1 benefit.
```

v1's safety result rested on 10 evaluable opportunities. A v2 rule that makes G3
pass while resting on similarly thin evidence has not improved the safety
argument, it has only moved the count. The 100-opportunity floor is what makes
the resolved G3 informative rather than merely passing.

---

## 2. Branch B: the G2 defect (RC3, RC4, RC5, RC7)

### B.0 E3, identifiability, decided before any search-side blame

```
E3: oracle selection among five known parametric families, per (family, c, noise, grid)
 |
 |-- false_structure_oracle > 0.10 on the mass_power control
 |     => STUDY INVALID. The oracle invents structure.
 |     CHANGE: none. Redesign E3 before any of its cells are used.
 |
 |-- cell IDENTIFIABLE (oracle selection >= 0.80)
 |     => the signal is present; failures in this cell are the search's.
 |     ENABLES: E4b, E4c, E4d for that cell.
 |
 |-- cell MARGINAL (0.50 to 0.80)
 |     => attribution ambiguous.
 |     CHANGE: NO SEARCH-SIDE CHANGE MAY CITE THIS CELL ALONE.
 |
 |-- cell WEAKLY IDENTIFIABLE (< 0.50)
       => failures here are not the search's.
       CHANGE: NO SEARCH-SIDE CHANGE LICENSED FOR THIS CELL.
               Permitted follow-ons, separately authorised:
                 (i)  re-declare the family-recovery endpoint population to
                      exclude the unreachable family, shrinking the claim; or
                 (ii) re-specify the planted coefficient, ONLY under the
                      difficulty guard (section 5); or
                 (iii) narrow the endpoint claim to "recoverable at coefficient
                      at or above c*", reporting c* as the primary result.
```

### B.1 E2, where the correct structure is actually lost

```
E2a (fresh worlds, decision-admissible) partitions each case into
    SUCCESS | NEVER_ON_FRONT | LOST_IN_RETENTION | LOST_IN_CROSS_SEED
 |
 |-- E2b (Held-out replay) contradicts the decomposition's 69/57 split materially
 |     => the diagnosis the whole remediation rests on is wrong.
 |     CHANGE: SUSPEND ALL E4 ABLATIONS until the contradiction is resolved.
 |             Republish the root-cause attribution first.
 |
 |-- LOST_IN_RETENTION dominates the non-success cases
 |     => RC3 confirmed by direct observation rather than inference.
 |     ENABLES: E4a.
 |
 |-- NEVER_ON_FRONT dominates
 |     => RC4 confirmed. Route through E3's verdict for those cells:
 |          IDENTIFIABLE          -> E4b, E4c, E4d licensed
 |          WEAKLY IDENTIFIABLE   -> NO SEARCH CHANGE LICENSED; benchmark branch
 |
 |-- LOST_IN_CROSS_SEED dominates
 |     => RC7 is larger than the 2 cases v1 showed.
 |     ENABLES: E4f voting-relation arms.
 |
 |-- P_retain_given_front is near 1 wherever P_front is high
       => the retention rule is exonerated.
       CHANGE: RC3 WITHDRAWN. No retention change licensed. E4a is not run.
```

### B.2 E4a, retention policy

```
E4a: R0 argmax(score) | R1 argmax(valid_r2) | R2 top-k | R3 whole front | R4 knee
 |
 |-- an arm raises G2 (Wilson lower of the improvement > 0)
 |     AND its false_structure_rate stays under the E6 ceiling
 |     AND its selection_count distribution does not collapse the stability gate
 |     => CHANGE: adopt the simplest such arm (fewest free parameters, then
 |               lowest false structure).
 |
 |-- an arm raises G2 but also raises false structure past the ceiling
 |     => CHANGE: REJECTED. This is the RC3 risk realised: an accuracy-weighted
 |               rule biasing toward overfit high-complexity expressions.
 |
 |-- an arm raises G2 but drives selection_count below the 20-of-30 gate for
 |   most cases
 |     => CHANGE: REJECTED, or adopted only together with a re-derived stability
 |               gate, which is itself a change requiring its own experiment.
 |               Multi-retention silently weakening the stability gate is the
 |               k-inflation the identity contract was written to avoid.
 |
 |-- no arm beats R0
       => CHANGE: NO CHANGE LICENSED. The frozen retention rule stands, and
                  RC3's attribution is revised downward.
```

### B.3 E4b and E4c, budget and objective

```
E4b/E4c, restricted to cells that are NEVER_ON_FRONT and IDENTIFIABLE
 |
 |-- P_front flat across budgets
 |     => generation failure is not a budget problem.
 |     CHANGE: NO BUDGET INCREASE LICENSED.
 |
 |-- P_front rises materially at niterations = 120
 |     => CHANGE: adopt the smallest sufficient budget. Report the cost.
 |
 |-- P_front rises only at niterations = 400
 |     => CHANGE: reported with its 10x cost. Adoption requires an explicit
 |               cost decision, not an automatic one.
 |
 |-- a parsimony change raises P_front (a generation effect)
 |     => CHANGE: licensed, subject to E6.
 |
 |-- a parsimony change raises only P_retain_given_front
       => CHANGE: NOT LICENSED via E4c. That is E4a's territory, addressed there
                  at zero search cost. Counting it twice would attribute one
                  fix to two factors.
```

### B.4 E4d and E5, the grammar and F18

```
E3's verdict on mass_exponential_descriptor
 |
 |-- WEAKLY IDENTIFIABLE at the frozen coefficient range   [predicted]
 |     => adding `exp` cannot help: an affine candidate fits as well at lower
 |        complexity, so a parsimony-driven search never emits the exponential
 |        form and _contains_exp_of never sees a literal exp node.
 |     CHANGE: DEVIATIONS_P3 D1's exclusion of `exp` STANDS. The grammar is
 |             exonerated. Resolve F18 by:
 |               O5 remove F18 from the family-recovery population (144 -> 132),
 |                  re-declaring the endpoint claim; or
 |               O6 re-specify F18's coefficient, ONLY under the difficulty
 |                  guard; or
 |               O7 replace F18's truth with an algebraically difficult but
 |                  grammar-expressible form preserving the family's question.
 |             The choice among O5/O6/O7 is a governance decision on what claim
 |             the endpoint should make, not an experimental one.
 |
 |-- IDENTIFIABLE
       => the grammar exclusion is the binding defect. Evaluate E4d arms.
       |
       |-- O3 (clipped exp) raises F18 P_front AND no other family's
       |   false_structure_rate rises past the E6 ceiling AND overflow
       |   instrumentation shows invalidity never improves a score
       |     => CHANGE: admit guarded `exp`, with overflow instrumentation
       |               permanently enabled and the clip-activation rate reported.
       |
       |-- O2 (unguarded) passes but O3 does not
       |     => CHANGE: NOT LICENSED. D1 excluded exp for overflow reasons and
       |               an unguarded reintroduction does not answer them.
       |
       |-- O4 (exp restricted to a linear argument) outperforms O3
       |     => CHANGE: STILL REJECTED. O4 encodes the planted form in the
       |               grammar. Its margin over O3 is reported as the size of
       |               the encoding effect, which is information about the
       |               benchmark, not a licence.
       |
       |-- no grammar option passes safety
             => CHANGE: the operator cannot be admitted safely. Resolve by
                        O5 or O7.
```

**G2 success rate ranks no option on this branch.** It is reported for all of
them and decides none of them. The ordered tests are coherence, then
identifiability, then safety.

### B.5 E4e, the coefficient regime and the engine-inefficiency measurement

```
engine_inefficiency = c*_search (E4e) - c*_oracle (E3)
 |
 |-- large and positive
 |     => the search is far from the statistical limit. Search engineering has
 |        headroom.
 |     ENABLES: continued work on E4b/E4c/E4d for identifiable cells.
 |
 |-- near zero
       => the search is already near the statistical limit for this data
          geometry. Further search engineering is wasted.
       CHANGE: NO FURTHER SEARCH-SIDE CHANGE LICENSED. The binding constraint
               is the benchmark's signal-to-noise, and that is a benchmark
               design question under the difficulty guard.
```

### B.6 E4f, classifier and voting relation

```
E4f-i, discovered-family classifier: K0 frozen | K1 normal form | K2 behavioural
 |
 |-- an arm raises coverage AND false_labelling_rate on adversarial negatives
 |   stays under its pre-declared ceiling
 |     => CHANGE: adopt the highest-coverage such arm.
 |
 |-- an arm raises coverage but also raises false labelling past the ceiling
       => CHANGE: REJECTED. This is RC5's risk realised, and it is the direction
                  that flatters the result: UNEVALUABLE converted to false
                  SUCCESS.

E4f-ii, voting relation: V0 template_key | V1 (support, family) | V2 algebraic
 |
 |-- an arm raises G2 AND k_inflation stays under its ceiling
 |     => CHANGE: adopt.
 |
 |-- V1 again shows the v1 pattern (recovers some, loses more)
       => CHANGE: NO CHANGE LICENSED. v1's counterfactual already measured V1
                  at 3/144 against the frozen rule's 4/144.
```

Note the standing prior: RC7 is worth 2 cases and its naive fix was net negative.
Nothing on this branch can rescue G2 on its own, and it must not be presented as
if it could.

---

## 3. Branch C: E6, the counterweight with veto

E6 is not a terminal stage. It runs against every candidate change from branches
A and B, as that change becomes a candidate.

```
Candidate change X (from E1, E4a, E4b, E4c, E4d, E4f, or E5)
 |
 +--> E6 measures, under X, on fresh worlds:
 |      - unsafe structural acceptance on mass-only truth (F07 analogue)
 |      - false structure on destroyed-link nulls (F19A analogue)
 |      - false structure on mass-preserving nulls (F19B analogue)
 |      - non-evaluability flagging on destroyed response (F19C analogue)
 |      - false structure on adversarial worlds (F20A latent driver,
 |        F20B measurement coupling, F20C out-of-grammar)
 |      on at least 100 evaluable safety opportunities
 |
 |-- unsafe acceptance rate Wilson upper <= the pre-declared ceiling
 |     => X survives and proceeds to the v2 architecture proposal.
 |
 |-- Wilson upper > the ceiling
       => VETO. X is rejected regardless of its G1 or G2 benefit.
```

**E6 has veto and no positive power.** It can reject a change; it can never
license one. That asymmetry is deliberate: a safety experiment that could
authorise changes would become a route to justifying looser rules by pointing at
an unfired alarm.

---

## 4. Terminal leaves: what v2 may look like, per outcome

The tree does not choose a v2 architecture. It bounds the space of architectures
that would be justified. Three illustrative terminal states, none of them
selected here:

| Combination of outcomes | Justified v2 shape |
|---|---|
| E0 H_clip, E1 (a), E3 mostly identifiable, E2 retention-dominant, E4a adopts R4, E6 clears | A1 gains a verdict-invariance boundary test and a re-derived ceiling; G2 gains a knee-based retention rule. No grammar change, no benchmark change, no new magnitude threshold anywhere. This is the cheapest justified v2 and the one the pre-registered predictions point toward. |
| E1 (c), E3 weakly identifiable for several families | v2 is primarily a **benchmark** revision, not an engine revision: amplitudes and coefficients re-declared from an external scientific rationale, endpoint claims narrowed to measured sensitivity floors, and the engine largely unchanged. |
| E1 (d), or E2b contradicting the decomposition | No v2 architecture is proposed at all. The adequacy statistic is redesigned from first principles, or the failure decomposition is republished first. |

---

## 5. The difficulty guard, applied at every benchmark-side edge

Three edges in this tree lead to changing the benchmark rather than the method:
A.1 (c)(ii), B.0 (ii), and B.4 O6. All three carry the same guard.

A planted magnitude may be changed only if **all** of the following hold:

1. an experiment (E1's `alpha_star`, E3's `c*`) measures the identifiability or
   detection floor above the current planted magnitude;
2. an external scientific rationale states what deviation or effect magnitude is
   chemically meaningful, **written before** the new magnitude is chosen;
3. the new magnitude is set from that rationale and not from the measured floor.

If (2) cannot be written, the correct action is to keep the magnitude and narrow
the endpoint claim to the measured floor, reporting the current magnitude as
below it.

The distinction this enforces: a benchmark that is easier because the planted
signal was raised to meet the method is a different and weaker benchmark. A
benchmark whose planted signal is set from a stated scientific criterion, and
whose method's sensitivity floor is separately measured and reported, is a
stronger one. Only the second is licensed anywhere in this tree.

---

## 6. Changes explicitly not licensed by any branch

Recorded so their absence is deliberate rather than accidental:

| Change | Why no branch licenses it |
|---|---|
| Choosing a boundary floor from the Held-out counterfactual table | Held-out is spent; the counterfactual is a diagnostic probe, not a proposal. Every floor in this tree is calibrated on fresh worlds and confirmed on a sealed split. |
| Lowering `MIN_EVALUABLE_COMPOUNDS` to make cases evaluable | E1 sweeps it only as a labelled secondary sweep, because moving it changes the denominator of every other metric. No edge adopts it alone. |
| Lowering `MIN_PRACTICAL_WINS` to make detectors fire | Only adoptable inside an admissible `(C, P)` pair that simultaneously holds false rejection at or below 0.05. A win-count reduction alone fails criterion 1. |
| Retaining the whole Pareto front to raise G2 | E4a R3 is measured, but adoption requires clearing E6 and not collapsing the stability gate. |
| Coarsening the voting relation to raise `selection_count` | RC7's own counterfactual is net negative, and `k_inflation` is a gating metric in E4f. |
| Loosening the family classifier to raise coverage | `false_labelling_rate` on adversarial negatives is the primary metric, not coverage. |
| Relaxing Gate 7 or Gate 8 | Late falsification is not the bottleneck: only 27 of 240 cases reach Gate 7, which passes 26 of 27, and Gate 8 passes 25 of 26 with its single failure a correct negative-control rejection. No experiment in this plan targets them, so no change to them is licensed. |
| Touching the Challenge partition | It is sealed and unopened and is v2's only confirmation surface. |

---

**Terminal state for this document:** design only. No branch taken, no change
adopted, no architecture chosen.
