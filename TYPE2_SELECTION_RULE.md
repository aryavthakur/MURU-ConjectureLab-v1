# TYPE2_SELECTION_RULE.md

**The frozen candidate-selection rule for the objective-alignment validation
study, and the development evidence that produced it.**

Frozen by `TYPE2_VALIDATION_PREREGISTRATION.md`. Every number in the development
section below comes from **already-seen Phase 3 worlds** and counts toward
nothing. The governed evidence is generated afterwards, on fresh worlds.

---

## 1. The defect this rule addresses

Phase 3 diagnosed it precisely and did not fix it, which was the right call at
the time:

> **The elbow rule resolves near-degenerate Pareto fronts in favour of the wrong
> expression.** With a tolerance of 0.01 absolute R², a complexity-6
> approximation that sits 0.004 R² below the complexity-13 planted form is
> preferred to it, in 30 of 30 seeds, at every noise level tested.
>
> — `PHASE3_DECISION.md`

The mechanism is not that the tolerance is wrong. It is that the rule **commits
to one expression per seed** and discards the rest of the band, so a question
about a *family* is answered by a single string.

## 2. What is NOT changed

* **The band tolerance stays 0.01.** Moving it would be the arbitrary
  substitution this study exists to avoid, and the Phase 3 evidence shows the
  planted form was already inside the 0.01 band — the tolerance never excluded
  it.
* **The stability requirement stays ≥ 20/30 seeds** (master plan L4).
* **The complexity budget stays ≤ 20**, the grammar stays frozen, the protected
  numerics stay frozen, the 0.5% invalid-fraction rule stays frozen.
* **The null statistic stays** the max over seeds of the best validation R² at
  complexity ≤ c. Only the calibration size changes.

## 3. The frozen rule

Per world, over its 30 independent symbolic seeds:

1. **Band.** For each seed, retain **every** candidate on that seed's Pareto
   front whose validation R² is within `BAND_TOL = 0.01` of that seed's best,
   with complexity ≤ 20 and invalid fraction ≤ 0.5%. Phase 3 took
   `min(complexity)` of exactly this set; this rule keeps all of it.
2. **Signature.** Compute each band member's Type 2 signature
   (`muru.objval.signature`): effective variable support, block-level support,
   scaling exponents, effect signs, monotonicity — every one of them invariant
   to multiplying the candidate by a positive constant, which is the only
   freedom the collapse model leaves in `g`.
3. **Families.** Pool the band across all 30 seeds and cluster into Type 2
   families by the frozen predicate in `TYPE2_FAMILY_EQUIVALENCE.md`.
4. **Selection frequency.** A family's frequency is the fraction of the 30 seeds
   contributing at least one member to it.
5. **Reported family.** The highest frequency wins; ties break on the lower
   representative complexity, then on the expression string.
6. **Representative.** The family's lowest-complexity member, ties broken by
   higher validation R², then by string. This is the expression that is
   adjudicated, falsified and reported.
7. **Identifiability.** Count the distinct **functional-equivalence** classes
   inside the reported family, using Phase 3's unchanged tolerances
   (`r > 0.999`, relative RMSE `< 0.02`). More than one class means the exact
   algebraic form is **not identified**, and that is reported as the finding
   rather than resolved by picking the simplest member.

Acceptance is separate and is defined in `muru.objval.adjudicate`; this file
defines only what is reported.

## 4. Why this is a Type 2 rule rather than a looser Type 3 rule

The claim being made is "these variables, this scaling, this direction, this
much predictive accuracy on unseen chemistry". Step 3 groups candidates by
exactly that, so the reported object is the claim. Step 7 measures what the
claim does *not* settle and forces it into the report. Phase 3's rule could not
express "the family is identified and the form is not"; this one can only report
that when it is true, and must report it when it is.

## 5. Development evidence

Source: the Phase 3 checkpoint store, 240 worlds × 30 seeds of complete Pareto
fronts, re-adjudicated offline under the candidate rule. **Development only.**
The threshold column uses Phase 3's frozen null table purely as a yardstick; the
governed study builds its own.

| Block | Worlds | Stable ≥ 20/30 | …and above threshold | …and claiming non-mass structure | Median Type 2 families | Median distinct algebraic forms in the reported family |
|---|---|---|---|---|---|---|
| G1 (G1B) | 30 | 29 | 29 | 29 | 9.5 | 6 |
| G2 | 8 | 0 | 0 | 0 | 19 | 2.5 |
| G3 | 8 | 8 | 8 | **0** | 23.5 | 5.5 |
| G4 | 100 | 41 | **0** | **0** | 17.5 | 1 |
| G4M | 30 | 23 | 13 | **0** | 13.5 | 2 |
| G5 | 8 | 1 | 1 | 1 | 22 | 1 |
| GA | 3 | 3 | 3 | 3 | 4 | 3 |
| GC | 9 | 5 | 2 | **0** | 23 | 4 |
| GRT | 4 | 1 | 1 | 1 | 14 | 1.5 |
| NCAL | 40 | 16 | 0 | 0 | 17 | 1 |

Three things this evidence established, each of which shaped the rule:

**The rule recovers the family where one exists.** In every G1B world the
reported family's effective support was `{precursor_mz, heteroatom_fraction}` —
the planted support — with a mass exponent of 0.500 against a planted 0.5.

**The rule does not manufacture structure where none exists.** Stability alone
is not enough — 41 of 100 pure-null worlds produced a stable family — but not
one of them cleared the null threshold. The threshold, not the stability count,
is what does the work, and that is by design: the null statistic upper-bounds
what any selector can report at a given complexity, so it stays conservative
under a rule it was not built for.

**The form is genuinely not identified.** The reported G1B family contained a
median of 6 distinct functional-equivalence classes. Under Phase 3's rule one of
them was picked and reported as "the" expression; under this rule the family is
reported and the multiplicity is stated.

## 6. The mass block, and why support is compared at block level

Development also produced a finding that changed the definition of "support".
The independent engine, gplearn, repeatedly selected `total_atom_count` where
PySR selected `precursor_mz` — two members of the same near-collinear size
block. At variable level that is 0/30 agreement; at block level it is a
substitution inside one structural slot.

`DESCRIPTORS.md` and `muru.discovery.protocol.MASS_BLOCK` already treat
`{precursor_mz, total_atom_count, rdbe}` as one block that must be ablated
together, because "dropping the named mass variable alone leaves its proxies in
place and understates how much of the effect mass carries". The same reasoning
applies to a structural *claim*: an expression that scales with
`total_atom_count^0.5` and one that scales with `precursor_mz^0.5` are making one
empirical claim about molecular size, and this corpus cannot say which proxy
carries it.

So the Type 2 claim is stated on **blocks**, and the scaling exponent is measured
by perturbing every member of a block together — which returns exactly the
planted exponent for a law written on any single proxy. Variable-level support is
computed, stored and reported in every artifact; it is simply not what the claim
is stated on, and where the two differ the difference is printed rather than
absorbed.

## 7. What could still go wrong, stated in advance

* A coarser equivalence relation raises stability fractions everywhere,
  including in nulls. The fresh G4 block measures the consequence directly, at
  the master plan's own 100 replicates, and the ≤ 5% gate is unchanged.
* Block-level support could mask a genuine mis-identification if a world's
  planted carrier were itself a mass proxy. No positive control plants one:
  G1B and G1C put the non-mass structure on `heteroatom_fraction`,
  `rotatable_bonds` or `n_O`, whose mass correlations are recorded in each
  world's manifest before the run.
* The rule was designed on Phase 3's worlds. That is why none of them can score
  it, why the fresh generators redraw every constant, and why G1C plants a truth
  the frozen grammar cannot represent at all.
