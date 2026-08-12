# DEVIATIONS_P3.md

Deviations from `MURU_ConjectureLab_v1_Master_Plan.md` and from
`PHASE3_PREREGISTRATION.md` incurred during Phase 3.

D1–D5 were decided and written **before** the pre-registration freezing commit
and before any governed symbolic run, so none of them was chosen after seeing
performance. Anything added after that commit is dated and states what was
already known when it was made.

---

## D1 — `exp` is excluded from the operator grammar (IMPORTANT)

**What the plan says.** Section 13.4: "Operators: `+, -, *, /, ^` with integer
or half-integer exponents only; `log`, `exp`, `sqrt`."

**The deviation.** The frozen grammar is `+ − × ÷` with unary
`sqrt, log, square, cube, inv`. `exp` is not offered. Free-exponent `^` is also
not offered; integer and half-integer powers are reachable as compositions of
`square`, `cube`, `sqrt` and `inv`, which is the plan's own restriction stated
constructively.

**Why, decided before any run.** The governed search target is T2, a positive
**energy scale** `g`. The logistic shape of the trajectory lives in `Φ`, which
is fitted nonparametrically by the collapse step and is never searched over, so
`exp` buys no planted structure on this target. It does buy overflow: `exp` of a
moderately large subexpression saturates the protected-numerics ceiling and
produces candidates whose validity depends on the evaluation domain rather than
on their form.

**Risk acknowledged.** A narrower grammar could in principle make a world
easier to reject than a wider one would. This cuts against the direction that
would flatter Phase 3 — a narrower space makes *recovery* harder, not easier —
and the same grammar is applied identically to null worlds, planted worlds and
the frozen Phase 4 protocol, so no world is advantaged relative to another.

**Consequence.** The frozen Phase 4 protocol inherits this grammar. Phase 4 may
not widen it without recalibrating the null thresholds.

---

## D2 — T3 is not run as a separate gate (MINOR)

**What the plan says.** Section 20 W3.2 lists "the T1 alternating collapse
search, the T2 inverse-variance-weighted parameter search, and the T3
diagnostic search".

**The deviation.** T1 and T2 are implemented and run for every world. T3 —
direct `mu = f(E, z)` symbolic search — is not run as a gate.

**Why.** Section 13.2 itself calls T3 "diagnostic ... for comparison only,
because it lets the search absorb the energy shape and the structure dependence
into one expression and is therefore the easiest place to overfit". Running it
across 240 worlds × 30 seeds would roughly double Phase 3 compute to obtain a
statistic the plan already declares non-decisive. The collapse fit's residual
diagnostics carry the same information about whether energy shape and structure
are separable, at negligible cost.

**Consequence.** No gate depends on T3. Reported as not run.

---

## D3 — Missing-cell rate is the measured 0.97%, not the plan's 15% (MINOR)

**What the plan says.** Section 18.2: "Missing energy levels at the observed 15%
rate with the observed pattern."

**The deviation.** Synthetic worlds drop cells at **0.97%**.

**Why.** The 15% figure does not describe this corpus. Measured on the
development corpus: 517 of 549 compounds have all six energies and 32 have
five, i.e. **99.03% cell coverage**. Simulating 15% missingness would make the
synthetic worlds harder than the real data in a way the real data does not
justify, and the plan's instruction is to match the observed rate — which is
what this does.

**Consequence.** None beyond fidelity. The rate is recorded in every generator
manifest.

---

## D4 — The G1 block runs G1B, the variant carrying non-mass structure (IMPORTANT)

**What the plan says.** Section 18.1 G1: "`mu = Phi(E / g(z))` with
`g = c1 * m^0.5` and `Phi` a logistic in log-energy."

**The deviation.** The literal G1 law is implemented and available, but the 30
worlds of the G1 block plant
`g = c₁·√m·(1 + 0.35·heteroatom_fraction)` — the same collapse family and the
same mass exponent, plus genuine non-mass structural dependence.

**Why, decided before any run.** The literal G1 is a mass-only law, which makes
it the same *kind* of object as G3. Phase 2's established result is structure
**beyond** energy and mass (K4B), so the positive control for a Phase 4 that
will search for exactly that must itself contain non-mass structure; otherwise
"the engine recovers G1" would be satisfiable by a mass-only expression and
would prove nothing about the question Phase 4 asks.

The planted mass exponent stays **0.5**, so the master plan's §18.3 recovery
criterion — exponent recovered within ±0.15 — applies unchanged.

**Consequence.** G1 recovery is a stricter test than the plan's, not a weaker
one: a candidate must recover both the mass exponent and the non-mass term.

---

## D5 — gplearn comparison arm runs a pre-registered representative subset (MINOR)

**What the plan says.** Section 13.3: "run `gplearn` on T2 as a cheap
independent engine."

**The deviation.** gplearn runs on blocks G1 and G3 in full plus the first 30
G4 nulls, at 10 seeds each — 68 worlds, 680 runs — rather than duplicating all
240 worlds × 30 seeds.

**Why, frozen before any result was seen.** The plan assigns gplearn a
comparison role, not a second full calibration. The chosen subset covers the
three cases where engine disagreement would actually change a conclusion:
recovery of a planted law (G1), correct attribution to mass (G3), and
false-positive behaviour under the null (G4). Full duplication would add roughly
an hour of compute without addressing a question the subset leaves open.

**Consequence.** gplearn results are reported as a comparison and cannot rescue
a failing PySR calibration. Any engine disagreement is reported as measured.

---

## D6 — F2 and F3 have no synthetic counterpart and are re-scoped (MINOR)

**What the plan says.** Section 16.1 F2 requires survival of the §7.3
preprocessing grid; F3 requires survival on independently reprocessed mzML.

**The deviation.** F2 is implemented as invariance to a defensible change in the
**estimation** pipeline (the number of knots in the shared shape `Φ`). F3 is
recorded `not_applicable`.

**Why.** A synthetic response has no intensity cutoff, no annotation filter and
no raw branch, so neither rung is evaluable as written. The real raw branch
covers 39 compounds (7.1%) and licenses no corpus-level preprocessing-invariance
claim in any case.

**Consequence.** A rung recorded `not_applicable` is **never** counted as a
pass. F2's re-scoping is stated in `FALSIFICATION_HARNESS.md` and both are
carried into the Phase 4 protocol, where F2 and F3 become evaluable again on
real data and are required there.

---

## D7 — Expression parsing drops the positivity assumption (IMPLEMENTATION ONLY)

**Not a change of specification.** §9 of the pre-registration already states the
complexity metric's intent: an integer or half-integer power costs one unary
operation over its base "so `x**2` costs 2 exactly as PySR's `square(x)` does;
this keeps the two engines on the same scale." This entry records a bug fix that
makes the implementation match that frozen text.

**The defect.** Candidate strings were first parsed with symbols declared
`positive=True`. SymPy restructures expressions on sight under that assumption:
`sqrt(a*b)` is rewritten as `sqrt(a)*sqrt(b)`, raising the node count from 4 to
5. The metric was therefore counting a tree the engine never searched, and the
inflation applied unevenly — only to expressions containing a restructurable
form. A second defect in the same area: `sympy.lambdify` raises on degenerate
expressions such as the `ComplexInfinity` that `1/(a-a)` collapses to, and the
raise happened outside the guard, so a pathological candidate produced an
exception instead of being marked invalid.

**The fix.** Parsing and evaluation use plain symbols, preserving the engine's
tree. Positivity is asserted only inside
`equivalence.algebraically_equivalent`, where it is a proof aid for `powsimp`
rather than a change of representation. `lambdify` moved inside the protected
block, so a degenerate expression is now invalid — never an error, and never a
favourable score.

**When, and what had been seen.** Found by `tests/test_p3_grammar.py` while the
first governed run was in progress. **No result had been examined**: no
threshold, no candidate, no recovery rate and no false-positive count had been
computed or looked at — only unit tests on hand-constructed expressions. The
run in progress had written 528 checkpoint units under the old parser.

**Action taken.** The run was stopped and **all checkpoints were deleted**,
because mixing two complexity metrics across worlds would have corrupted the
null calibration: thresholds are conditioned on complexity, so worlds scored on
different scales are not comparable. The full 7,200-unit search was restarted
from zero under the corrected code. Approximately 13 minutes of compute was
discarded.

**Consequence.** None for the science. Every world in the reported results is
scored by one metric.
