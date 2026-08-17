# MURU v2 Final Remaining Program

**Status:** SEALED synthesis, results-blind to E2. Determined only after `MURU_V2_MASTER_MATHEMATICAL_RECONCILIATION.md` and `MURU_V2_REPAIR_SPACE_CLOSURE.md`. **Nothing below is executed by this document.**

The repair space closure leaves 4 unconditionally licensed repair classes (M2 descriptor pooling, M2 pooled case statistic, M3 relative-plateau estimator, and a straightforward symbolic-equivalence code patch handled directly in the governance amendment rather than as an experiment) and 2 classes gated on E2a's seal. Combined into coherent experimental items — the two M2 classes are one experiment viewed from two angles — this yields the 5 numbered program items below: 2 genuine new experiments (M2, M3), the already-designed E4a sequence, one integration/scoping step, and E6 itself. This is the minimum remaining program.

---

## 1. M2 architectural repair experiment (descriptor-conditional pooling + pooled case statistic + oracle reference)

**QUESTION:** Does replacing the frozen LOEO-holdout + 0.90-margin + 20-of-30-vote decision architecture with a descriptor-conditional-pooled parameter estimate and a pooled case-level statistic, at the *existing* 6-energy budget, restore M2 detector power toward the architecture-independent ceiling (0.416 full-info) or the pooled ceiling (0.73–0.82)?

**WHY NOT ALREADY ANSWERED:** M2GV1 tested geometry under the frozen architecture (closed, `L-M2-04`). RC1 tested coordinates under the frozen architecture (closed, `L-M2-08`). The detectability lower bound and the (unsealed) information-scaling theory both derive, but do not execute, the pooled-statistic prediction (`L-M2-05`, `L-M2-07`). No sealed study has ever run the frozen *decision architecture itself* as the manipulated variable.

**ARMS:** (i) production control (frozen LOEO+margin+vote); (ii) descriptor-conditional pooled parameter estimate, frozen decision rule; (iii) pooled case-level statistic (no LOEO, no margin, no per-compound vote), production parameter estimate; (iv) both (ii)+(iii) combined; (v) oracle reference arm (true `a_i`, pooled statistic) — a non-adoptable ceiling check, not a candidate.

**PRIMARY ENDPOINT:** Case-level power at the frozen reference cell (alpha=1.0, noise=0.02), Wilson-bounded, against the same admissibility gates E1 used (FRR≤0.05, power≥0.80 Wilson-lower≥0.70).

**ORACLE/NEGATIVE CONTROL:** Arm (v) bounds the ceiling; arm (i) reproduces M2GV1's already-known 0.0000 as an internal consistency check.

**MECHANICAL DECISION:** If arm (iv) clears the E1 admissibility bar on Confirmation data → licensed for adoption as a decision-architecture amendment (requires the same governance authorization tier as any change to `adequacy.py`'s decision rule — this is not a threshold tweak). If arm (iv) does not clear it but exceeds arm (i) by a pre-registered material margin → `PARTIAL`, name the residual gap. If arm (iv) does not exceed arm (i) → `NO_M2_ARCHITECTURE_REPAIR_LICENSED`, and the M2 detector is retired to a documented-impossible-under-current-architecture status analogous to M1's.

**WHAT WOULD CLOSE THE BRANCH:** Either adoption (with a formal decision-tree amendment) or a clean negative — either way, this is the last M2 experiment the evidence licenses; a negative result here closes M2 repair entirely (every other axis is already `CLOSED_NEGATIVE` or `CONTRA_INDICATED`, per the repair-space closure).

---

## 2. M3 targeted estimator/detector experiment (relative-plateau construction, contingent on a prior governance decision)

**QUESTION:** Does the Neyman-orthogonal relative-plateau construction (`tau=(b-a_hi)/D`) both (a) remove the proven finite-support floor at the parameter level and (b) improve the *actual* M3 detector's power, at matched false-rejection rate?

**WHY NOT ALREADY ANSWERED:** The Phi-bias theory derives the construction and its predicted ~1.22× variance cost but never executes it (`L-M3-02` §12). No sealed study has tested whether a parameter-level bias fix propagates to detector power, because the frozen M3 decision does not read the biased parameter at all (`L-M3-02` §1.4) — this is a genuinely open, structurally distinct question from every closed M3 repair axis.

**PRECONDITION, not part of the experiment itself:** a governance decision on route A (add a new target-contrast decision statistic reading `tau_i` — an escalation to the adequacy statistic requiring its own preregistration and safety pass) vs. route B (measure parameter recovery only, make no power claim). This document does not make that decision; it is named as the design's own stated prerequisite.

**ARMS:** `A0` (production control); `A1`/`A2` (non-adoptable diagnostic isolators: exact-Phi frozen `b_hat`, and exact-Phi+true-g, to verify the floor's predicted magnitude in isolation); `A4` (construction with case-level free `a`,`c`, `m=0`); `A5` (construction with `m∈{2,3}` cross-fitted interior-shape directions); `A6` (non-adoptable coupling-sensitivity control, forces `corr(log_g,descriptor)`).

**PRIMARY ENDPOINT:** (1) `bias_share_pathology2 = |bias_A2|/|bias_A0|` with a bootstrap interval; (2) measured bias gains under `A4`/`A5` for the four named directions (should be ~zero if the construction is correctly implemented); (3) **M3 detector power under `A4`/`A5` vs. `A0` at matched FRR** — the endpoint that actually answers the mission question, not just the parameter residual.

**ORACLE/NEGATIVE CONTROL:** `A1`/`A2` (isolate the floor); `A6` (non-adoptable, tests the coupling-sensitivity prediction P6 without touching anything adoptable).

**MECHANICAL DECISION:** the theory's own pre-specified adoption rule (`L-M3-02` §12): `A4`/`A5` become candidates only if ALL of — `bias_share_pathology2≥0.5`; measured level/endpoint gains ≈0 within tolerance; power's Wilson-lower exceeds `A0`'s Wilson-upper in ≥3 of 4 alphas; variance penalty ≤1.5× (margin exists at the theory's own 1.22× estimate); FRR on null worlds ≤0.05. Missing any one → `NO_M3_ARCHITECTURE_REPAIR_LICENSED`.

**WHAT WOULD CLOSE THE BRANCH:** A clean pass licenses a decision-tree-level amendment (same tier as item 1). A clean fail — especially if `A4`/`A5` fix the parameter bias but detector power does not move — would be the first sealed proof that M3's problem is *decision-statistic* choice, not *estimator* choice at all, closing the M3 repair question definitively either way.

---

## 3. E4a — only if E2's frozen gate licenses it

**QUESTION:** Already fully specified (`design/v2-retention-remediation`, `L-RET-01..05`); not restated here.

**WHY NOT ALREADY ANSWERED:** E2 is still running (mission constraint); the frozen protocol requires E2a to seal first (`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` §4).

**PRECONDITION** (before execution, not part of E4a's science): the two documentation-only corrections in `MURU_V2_PRE_E6_GOVERNANCE_AMENDMENT.md` (90-vs-36; optionally the R1=R3=R5 explicit self-consistency control) should be applied — both are derivable from already-frozen definitions and require zero E2a data, so making them now does not touch results-blindness. The missing scoring implementation (R0–R6, vote-reduction, McNemar/paired-bootstrap) must be built — a precondition, not a design change.

**ARMS/ENDPOINT/DECISION:** as already frozen in the preregistration. **This document does not modify E4a's scientific arms** — see Part VII of the reconciliation and the governance amendment for the exact, narrow, results-blind corrections licensed.

**WHAT WOULD CLOSE THE BRANCH:** E4a's own frozen adoption rule, once run.

---

## 4. Final integration

**QUESTION:** After items 1–3 resolve (whichever combination of adoption/negative results occurs), does the assembled system (whatever repair lanes were actually licensed) form a coherent `C_impl` candidate for E6 to test at all?

**WHY NOT ALREADY ANSWERED:** As of this reconciliation, **there may be no concrete repair candidate** — nearly every M1/M2/M3 study returned a negative (`L-M1-03/04/06`, `L-M2-04/08`, `L-M3-04/05`). If items 1 and 2 both return negative, E6 has nothing to validate except the status quo, which changes what E6-R's positive claim can even be about.

**ARMS:** N/A — this is an assembly/scoping step, not an experiment.

**PRIMARY ENDPOINT:** A named, versioned `C_impl` (or an explicit "no repair candidate exists" governance finding).

**MECHANICAL DECISION:** If a `C_impl` exists → proceed to E6. If not → E6-R's scope must be explicitly redefined as validating the *current, unrepaired* system (a materially different, and materially less favorable, claim than what E6 was designed to support) — a governance decision, not a scientific one.

**WHAT WOULD CLOSE THE BRANCH:** Either a named `C_impl` or an explicit governance acknowledgment that none exists.

---

## 5. E6

**QUESTION:** Already specified (`MURU_V2_E6_FINAL_VALIDATION_PREREGISTRATION.md`), pending the corrections in `MURU_V2_PRE_E6_GOVERNANCE_AMENDMENT.md`.

**WHY NOT ALREADY ANSWERED:** Not frozen (verified, `L-E6-01`); `n_rec≥320`'s adjudicability against the reconciled denominator is unchecked (`L-E6-04`); item 4 above is a precondition.

**Not restated further here** — see the governance amendment for the exact, minimal changes required before freeze, and the mathematical reconciliation Part XI for the full analysis.

---

## Explicitly not proposed as new experiments (already answered, would be redundant)

- Any further M1 statistic tournament, profile architecture, or reparameterization study — all three axes are closed (repair-space closure).
- Any further M2 grid-geometry or coordinate study — both closed.
- A 4th M3 profile-estimator study — contra-indicated, not merely unneeded.
- Further F09 search-parameter sweeps — case-level front-reach is already saturated at 12/12.
- A fresh recoverability-ceiling re-derivation — the four numbers are sealed and internally consistent; what remains is ratification (governance), not re-measurement.
- Re-running E0 or E1 — both independently cross-checked/hostile-reviewed already.

## Dependency graph

```
                    ┌─────────────────────────────┐
                    │  E2 (running; frozen gate)   │
                    └──────────────┬───────────────┘
                                   │ seals
                                   v
     ┌──────────────────┐   ┌─────────────┐
     │ M2 architecture   │   │  E4a        │
     │ repair experiment │   │ (retention) │
     │ (item 1)          │   └──────┬──────┘
     └─────────┬─────────┘          │
               │                    │
     ┌─────────v─────────┐          │
     │ M3 targeted        │         │
     │ estimator/detector │         │
     │ experiment (item 2)│         │
     └─────────┬─────────┘          │
               │                    │
               └────────┬───────────┘
                         v
              ┌───────────────────────┐
              │ Final integration       │
              │ (item 4: name C_impl,   │
              │  or acknowledge none)   │
              └───────────┬─────────────┘
                           v
              ┌───────────────────────┐
              │ Pre-E6 governance       │
              │ amendment applied       │
              │ (commit + n_rec check + │
              │  DA5/Dim-E ratification)│
              └───────────┬─────────────┘
                           v
                    ┌─────────────┐
                    │     E6      │
                    └─────────────┘
```

Items 1 and 2 have no dependency on E2 or on each other and could, in principle, run in parallel — neither is authorized for execution by this document.
