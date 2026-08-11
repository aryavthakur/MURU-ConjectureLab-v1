# MASTER_PLAN_CLARIFICATIONS.md

Clarifications to `MURU_ConjectureLab_v1_Master_Plan.md` issued during Phase 2.

The master plan is a historical planning document and is **not rewritten** by
this file. Where the plan and this file conflict, this file governs Phase 2
implementation. Each entry states the plan's wording, the defect, and the
governing correction.

---

## C1 — Phase dependency: Phase 2 authorizes Phase 3, not Phase 4

**What the plan says.** Section 20, PHASE 2, Deliverable 7:

> `PHASE2_DECISION.md` stating the achieved ladder rung (L1, L2 or L3) and
> whether **Phase 4** is authorized.

and Section 20, PHASE 3, Inputs:

> Phase 2 exit artifact authorizing **Phase 4**.

**The defect.** This is a phase-dependency wording error. It implies Phase 2
can license the real symbolic discovery run in Phase 4 while skipping Phase 3,
which is the phase that builds and null-calibrates the discovery engine and
proves on synthetic ground truth that it can tell a real relationship from a
search artifact. Section 13.1 contradicts the wording directly by making
"Phase 3 synthetic recovery succeeded at the noise level measured in Phase 1"
a gating condition for symbolic regression, and kill criterion K6 can only fire
in Phase 3. The plan's own logic therefore requires Phase 3 between Phase 2 and
Phase 4; only the deliverable wording is wrong.

**The governing correction.** The project sequence is fixed and strictly
ordered:

```
Phase 1  ->  Phase 2  ->  Phase 3  ->  Phase 4  ->  Phase 5
```

- **Phase 2 may authorize Phase 3 only.**
- **Phase 3 may later authorize Phase 4.**
- No phase may authorize a phase more than one step ahead of itself.

Accordingly `PHASE2_DECISION.md` states whether **Phase 3** is authorized, and
says nothing about Phase 4. The four permitted Phase 2 verdicts are
`GO TO PHASE 3`, `RESTRICT AND GO TO PHASE 3`, `STOP BEFORE PHASE 3`, and
`INCONCLUSIVE DUE TO BLOCKER`.

**Consequence for Phase 2.** None beyond wording and the verdict vocabulary.
No Phase 2 analysis changes.

---

## C2 — B7 is a flexible predictive benchmark, not a ceiling

**What the plan says.** Section 11 calls B7 the "predictability ceiling";
section 12.1 says machine learning's one job is to "estimate the predictability
ceiling"; and section 20, PHASE 2, Scientific validation states:

> Any baseline beating B7 signals a bug.

**The defect.** A gradient-boosted tree ensemble under nested grouped
cross-validation is one model family with one pre-registered search space. It
is not an information-theoretic upper bound on recoverable information, and it
is not guaranteed to dominate simpler models. Trees are known to be weak at
smooth extrapolation along a continuous axis; a spline or tensor-product smooth
can legitimately beat them on a smooth low-dimensional surface such as
`mu ~ f(energy, mass)`. Treating any such outcome as a defect creates pressure
to tune the flexible model until it wins, which is exactly the researcher
degree of freedom section 14 exists to remove.

**The governing correction.** The B7 role is renamed **FLEXIBLE PREDICTIVE
BENCHMARK** throughout Phase 2. Its purpose is to estimate how much nonlinear
predictive information a pre-registered flexible family can recover from
molecular representation, not to bound what is recoverable in principle.

The rule "any baseline beating B7 signals a bug" is **revoked**. If a simpler
model outperforms the flexible benchmark, the response is to verify the
implementation, the split, and the metric, and then to report the result as
measured. The flexible benchmark is not re-tuned after seeing that it lost.

**Consequence for Phase 2.** Reporting language only; no analysis changes. The
Phase 2 acceptance criteria require that the flexible benchmark is not
described as a guaranteed upper bound.

---

## C3 — K4 is adjudicated as two separate questions

**What the plan says.** Section 22, K4:

> *Trigger:* B7 fails to beat B1 under S2 by more than the compound bootstrap
> interval.

**The defect.** A single K4 conflates two scientifically distinct questions.
Beating B1 (a structure-blind, energy-aware population mean) only establishes
that something beyond the population energy response is predictable. Because
Phase 1 measured `rho(mu, precursor m/z)` reaching -0.68 at NCE 90, and because
precursor mass appears in the definition of mu itself, "something beyond B1"
may be entirely precursor mass. The plan's own K5 and risk R4 anticipate this,
but K4 as written would pass on a pure mass effect.

**The governing correction.** K4 is split:

- **K4A** — does the flexible structure-aware model beat the structure-blind
  energy baseline (B1) on the pre-registered primary held-out chemistry split?
  If K4A fails, **Phase 3 is not authorized**.
- **K4B** — does the structure-aware model also beat **MASS FLEX** by a
  scientifically meaningful amount, with a paired compound-level uncertainty
  interval supporting the improvement?

If K4A passes and K4B fails, no claim of meaningful structural information
beyond mass may be made, and adjudication proceeds directly to K5 to determine
whether the current formulation should stop or be reframed.

**Consequence for Phase 2.** The baseline ladder gains **MASS FLEX**, a strong
nonlinear energy-plus-mass competitor, alongside the original **MASS SIMPLE**
(B2), which remains required as a Phase 1 carry-forward.

---

## C4 — The Phase 1 variability estimate is an upper bound, not a noise floor

**What the plan says.** Section 15 lists "Measurement repeatability" as
"replicate variance from the raw-data subset", and section 3.2's H-MAIN
requires "residual variance not exceeding the measurement repeatability of the
instrument".

**The defect.** Phase 1 deviation D6 established that mixes 499, 503 and 505 are
three different mixture preparations at three matrix complexities
(95 / 185 / 365 substances), not repeated injections of one vial. The variance
they yield contains preparation, injection, instrument and matrix-complexity
variation.

**The governing correction.** The quantity is named the **Phase 1 conservative
inter-mixture variability estimate**, or **upper bound on technical
repeatability**. It must not be called the instrument noise floor, pure
technical replicate variance, or an exact measurement-error variance. Negative
mode has no such estimate at all and remains **UNKNOWN**.

**Consequence for Phase 2.** Wording discipline in every Phase 2 artifact that
references measurement variability.

---

## C5 — Bemis-Murcko scaffolding requires an explicit ringless policy

**What the plan says.** Section 10.3 defines S2 as "group by scaffold" with no
statement of what happens to molecules that have no ring system.

**The defect.** `MurckoScaffold.GetScaffoldForMol` returns an empty molecule for
an acyclic input. The default behaviour of keying on the returned SMILES would
place every ringless molecule into a single group named by the empty string,
asserting that all acyclic compounds share a common core. That is chemically
false and would distort split difficulty in an undeclared direction.

**The governing correction.** Measured on the Phase 2 development corpus: 32 of
549 compounds (5.8%) are ringless and produce an empty scaffold. Each is
assigned **its own scaffold group, keyed by its connectivity block**, rather
than being pooled. The consequence — that S2 is marginally easier for those
5.8% because scaffold-disjointness is undefined for them — is declared in
`SPLIT_AUDIT.md`, and S3 (similarity-cluster-disjoint) is the stress test that
covers them properly.

**Consequence for Phase 2.** Recorded in the pre-registration before any
performance was observed.
