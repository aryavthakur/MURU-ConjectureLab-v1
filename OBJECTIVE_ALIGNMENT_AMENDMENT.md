# OBJECTIVE_ALIGNMENT_AMENDMENT.md

**A formal amendment recording an objective-alignment discrepancy between the
MURU v1 master plan and the Phase 3 pre-registration, and authorizing a separate
prospective validation study of the original objective.**

This file amends nothing about Phase 3's result. It does not edit
`MURU_ConjectureLab_v1_Master_Plan.md`, `PHASE3_PREREGISTRATION.md` or
`PHASE3_DECISION.md`, and it does not create a phase. The five-phase
architecture stands. The official Phase 3 verdict stands:

# STOP BEFORE PHASE 4

---

## 1. The original master-plan objective

The master plan poses one question (§2):

> Given energy-resolved MS/MS trajectories for several hundred structurally
> diverse small molecules measured on a single Q Exactive under HCD, does a
> **compact, interpretable, molecule-conditional function** describe how the
> fragmentation state evolves with collision energy well enough to predict the
> trajectories of molecules held out by chemical scaffold?

Formally (§3.2, H-MAIN): there exist a molecule-conditional energy scale
`s_i = g(z_i)` and one shared univariate shape `Phi` with
`mu_i(E) = Phi(E / s_i) + eps_i(E)`, holding on scaffold-disjoint holdouts.
`H-PARAM` weakens it to a shared parametric family `Phi(E; theta_i)` with
`theta_i` predictable from `z_i`.

The plan's own success criterion for the synthetic positive control is §18.3:

| Case | MURU must |
|---|---|
| G1 | **recover g's exponent within ±0.15 and Phi's shape family, at L4 or above** |

and the Phase 3 acceptance checklist (§20, Phase 3) reads:

> - [ ] G1 recovered **at L4 or above** in ≥ 80% of replicates

`L4` is defined in §16.2 and §23 as:

> a symbolic expression at complexity ≤ 20 exceeding the null-calibrated 95th
> percentile, recovered by ≥ 20/30 seeds, reaching ≥ 80% of the Tier B ceiling

**Nothing in the master plan's G1 criterion requires recovering the planted
algebraic form.** It requires a scaling exponent, a shape family, and an L4-grade
compact expression. That is a claim about *which variables matter and how the
response scales*, not about which string the search returns.

## 2. The stricter criterion Phase 3 pre-registered

`PHASE3_PREREGISTRATION.md` §19 added a condition:

> **G1/G1B** — recover an equivalent or near-equivalent low-complexity
> expression: **functional equivalence to the planted law**, correct or
> substantively equivalent variable support, complexity ≤ 20, stability ≥ 20/30,
> and the mass exponent recovered within ±0.15 of the planted 0.5 (master plan
> 18.3).

The added clause is *functional equivalence to the planted law*, operationalized
in §10 as `r > 0.999` and relative RMSE `< 0.02` against the complete planted
expression after optimal positive rescaling. That is a **form-identification**
requirement. It is strictly stronger than §18.3 and it was not in the master
plan.

Phase 3 itself recorded the divergence, in the open, at the time:

> | Criterion | Source | Result at the moderate regime |
> |---|---|---|
> | exponent within ±0.15 **and** the recovered form is in the planted shape family | master plan §18.3, the weaker reading | **90%** |
> | the above **and** functional equivalence to the complete planted law | `PHASE3_PREREGISTRATION.md` §19, the reading frozen in advance | **0%** |
>
> — `PHASE3_DECISION.md`

## 3. The Phase 3 STOP

Phase 3 was evaluated against its own frozen §19 reading, obtained 0% functional
recovery at every noise regime, and returned `STOP BEFORE PHASE 4` by the frozen
decision rule in §22. The false-positive gate K6 did not fire (0/100, exact 95%
interval [0.0000, 0.0362]); the refusal worlds behaved correctly; the stop came
from the G1 recovery condition alone.

## 4. Why that STOP remains historically valid

It remains valid, is not reopened, and is not to be re-scored:

* the §19 reading was frozen **before** any governed run, precisely so that the
  choice between the two readings could not be made after seeing performance;
* Phase 3 applied the rule it had frozen, and reported both readings rather than
  quietly selecting the flattering one;
* changing the selection rule after seeing that recovery failed is the exact
  move Phase 3 exists to prevent, and Phase 3 explicitly declined to make it
  (`PHASE3_DECISION.md`, "None of these was applied").

Retro-scoring Phase 3 under a different criterion would destroy the only thing
that made its result meaningful. **This amendment does not do that.**

## 5. The conceptual-audit finding: partial objective drift

A conceptual audit found **partial objective drift**: the machinery was
validated against a Type 3 (form-identification) criterion while the project's
stated objective was a Type 2 (empirical family) claim. The audit modified
nothing in the repository. Its central finding has been re-derived here directly
from the files (§1 and §2 above quote the primary sources, not the audit).

The consequence is narrow and specific: **Phase 3's STOP is a valid answer to
the question Phase 3 asked, and is not an answer to the question the master plan
asked.** The second question has never been tested.

## 6. Type 2 against Type 3

| Class | Claim | Evidence bar |
|---|---|---|
| **Type 1** | a predictive trajectory equation over the declared domain | held-out predictive accuracy; no claim of a generating law |
| **Type 2** | a compact, interpretable **empirical relationship**: stable variable support, stable scaling behaviour, generalization to held-out chemistry, null-calibrated, falsification-surviving | this study's maximum target |
| **Type 3** | the algebraic form may correspond to fragmentation physics | requires form-level identifiability plus stronger corroboration — **not authorized here** |
| **Type 4** | an established physical law | independent experimental and mechanistic replication — far outside v1 |

A Type 2 result may **never** be converted into Type 3 language. In particular,
if the study succeeds, the permitted sentence is "the data support an empirical
molecule-conditional relationship involving these variables and this scaling
behaviour", and the forbidden sentences include "MURU discovered the equation"
and "MURU found the true law".

## 7. Why a new prospective validation is scientifically legitimate

Three things make it legitimate rather than a rescue attempt:

1. **The claim class is different and lower.** This study cannot authorize
   anything Phase 3 was asked to authorize. Phase 3's question was whether the
   machinery identifies a form. This one asks whether it identifies a family.
2. **The criterion is not invented from the failure.** It is taken from the
   master plan's §18.3, §16.2 and §14.4, which predate Phase 3 and which Phase 3
   itself cites. The exponent tolerance is the plan's ±0.15; the stability
   requirement is the plan's ≥ 20/30; the complexity budget is the plan's 20;
   the ceiling fraction is the plan's ≥ 80% of the Tier B ceiling; the
   false-positive gate is the plan's ≤ 5% over 100 replicates.
3. **It is prospective.** The rule is frozen and hashed before the evidence that
   scores it exists.

## 8. Why old Phase 3 evidence is development evidence only

The Phase 3 worlds, Pareto fronts, diagnoses and failures have been seen. A rule
designed by looking at them cannot also be *tested* on them: that is fitting the
selector to its own test set, and it is the failure mode the master plan's §14
data wall exists to prevent.

Old Phase 3 artifacts are therefore admissible for exactly one purpose — to
**choose** the Type 2 selection rule, its family-equivalence definition, its
engine-corroboration standard, and its runtime architecture — and for no other.
**No old Phase 3 number may appear in the pass/fail arithmetic of this study.**

## 9. Why fresh worlds are required

Because §8 leaves nothing else. Fresh worlds must use seed ranges never used in
Phase 3, freshly drawn nuisance values, fresh noise, fresh split assignments,
and generator parameters redrawn within pre-registered ranges rather than
Phase 3's exact constants. Varying the constants tests whether the rule
generalizes beyond the particular synthetic equations that motivated it, rather
than beyond one instance of them.

## 10. Why this is not a new numbered phase

`MASTER_PLAN_CLARIFICATIONS.md` C1 fixes the sequence Phase 1 → 2 → 3 → 4 → 5,
and the master plan §20 states "Five phases. No Phase 6." This study creates no
phase, renames none, and reorders none. It is a **validation study of a
differently scoped claim**, whose only possible product is a frozen protocol
that a *re-scoped* Phase 4 could later execute. It is not Phase 3b: it does not
re-run, re-score or supersede Phase 3, and Phase 3's artifacts are untouched.

## 11. What a successful study could authorize

At most, and exactly:

> a Phase 4 search for **a compact, interpretable, molecule-conditional
> empirical equation family** describing positive-mode collision-energy
> trajectories within the validated instrument, collision-energy, preprocessing
> and chemical domain — identifying relevant molecular descriptors, scaling
> exponents, interpretable trajectory parameters and stable empirical
> relationships.

Nothing more. The highest defensible **real-data** rung remains **L3**
throughout this study and cannot be advanced by synthetic worlds.

## 12. What remains forbidden

Regardless of outcome, this study and any Phase 4 it could authorize may not
claim:

* mechanism, or any physical interpretation of a fitted form;
* a universal law, or a "law of fragmentation";
* the exact algebraic generating equation, unless form-level identifiability is
  independently established, which this study is not designed to establish;
* negative-mode generality (Phase 2 K4B FAIL, +1.93%, interval spanning zero);
* cross-instrument transfer (never demonstrated);
* causal explanation of the retention-time association (Phase 2 NC7 fired);
* anomaly detection, CE-aware QC or data-mishap flagging — these were never part
  of the v1 repository objective and are recorded here as a possible **v2**
  application only, with no thresholds, no claims and no implementation in v1;
* any raising of the real-data claims ladder above **L3**.

Phase 1's endpoint decision is not reopened: `mu` remains the v1 primary
response. Phase 2's restrictions remain in force in full.

---

## Provenance

| Item | Value |
|---|---|
| Phase 3 completion commit | `211b500999a6ea0a098cfb87f1a9f4958060f81e` (verified) |
| Phase 3 pre-registration sha256 | `064ce1fb9939b10d3b22be1f74aa3da28f487ec3917449db0794cf6431af5a63` |
| Confirmation-set seal sha256 | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` (verified before this study) |
| Study branch | `objective-validation-type2`, based on `211b500` |
| Companion pre-registration | `TYPE2_VALIDATION_PREREGISTRATION.md` |

The discrepancy in §1–§2 is preserved, not erased. Neither the master plan nor
the Phase 3 pre-registration is edited to make them agree.
