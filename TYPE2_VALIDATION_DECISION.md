# TYPE2_VALIDATION_DECISION.md

# DO NOT AUTHORIZE PHASE 4

Prospective objective-alignment validation of the Type 2 claim: whether the MURU
machinery reliably identifies a compact, interpretable, molecule-conditional
empirical equation **family** — the objective the master plan actually posed —
even when the exact algebraic generating form is not identifiable.

Pre-registration `TYPE2_VALIDATION_PREREGISTRATION.md`, sha256
`9ce046294940464343cd74978931fa3fc9ed7bb79541484a9fba7b8c142ee9e7`, committed
`307e4e083256b04ee7c4452282f06c06812785b8` **before any fresh validation world
existed**. The verdict above is **computed** by `muru.objval.decision.decide`
from machine-readable artifacts (§17 of that file), not chosen afterwards.

**This study does not modify Phase 3.** Phase 3's verdict remains
`STOP BEFORE PHASE 4`, its pre-registration is unedited, and its artifacts are
untouched. This is not a phase, not "Phase 3b", and not Phase 4.

---

## Exactly one stop condition fired

```
independent-engine corroboration did not meet the frozen claim-relevant standard
```

Blockers: none. Every other gate in §17 passed.

| # | Condition | Limit | Observed | |
|---|---|---|---|---|
| 1 | G1A Type 2 success, low+moderate noise | 4/4 | **4/4** | pass |
| 2 | G1B **moderate** Type 2 success rate | ≥ 0.80 | **17/20 = 0.85** | pass |
| 3 | median G1B moderate selection frequency | ≥ 20/30 | **30/30** | pass |
| 4 | G1C worlds falsely claiming the form is identified | ≤ 1/10 | **0/10** | pass |
| 5 | fresh G4 false-positive rate | ≤ 0.05 | **0/100 = 0.0000** | pass |
| 6 | G2 accepted compact conjectures | ≤ 1/8 | **0/8** | pass |
| 7 | G3 accepted non-mass structural claims | 0/8 | **0/8** | pass |
| 8 | G4M accepted non-mass structural claims | 0/30 | **0/30** | pass |
| 9 | GC accepted non-mass structural claims | ≤ 1/9 | **0/9** | pass |
| 10 | G5 accepted non-mass structural claims | ≤ 2/8 | **0/8** | pass |
| 11 | GRT accepted non-mass structural claims | ≤ 1/4 | **0/4** | pass |
| 12 | accepted G1B moderate clearing the threshold's **upper** bootstrap bound | ≥ 80% | **19/19 = 100%** | pass |
| 13 | independent-engine corroboration | ≥ 50% support **and** ≥ 50% exponent | **15% and 25%** | **FAIL** |

## The binding result

`TYPE2_ENGINE_CORROBORATION.md` froze the standard on the G1B moderate worlds:
the comparison arm must reproduce PySR's reported family on **block-level
effective support in ≥ 50%** of worlds and on the **mass-block exponent within
±0.15 in ≥ 50%**.

| Block | n | Block support agrees | Mass exponent agrees | Sign agrees | Same Type 2 family | Same expression |
|---|---|---|---|---|---|---|
| `G1B` (all regimes) | 40 | 25% | 33% | 85% | 0% | 0% |
| `G1B` **moderate** — the gate | 20 | **15%** | **25%** | — | 0% | 0% |
| `G1C` | 10 | 20% | 20% | 80% | 0% | 0% |
| `G3` | 8 | **100%** | 38% | 100% | 0% | 0% |
| `G4` nulls | 30 | 80% | 0% | 0% | 0% | 0% |

The mechanism is visible in the expressions themselves. On the 20 G1B moderate
worlds PySR reported `{MASS, carrier}` in **20 of 20**, with a mass exponent of
0.500 against a planted 0.5. gplearn returned, in the same worlds, expressions
like `total_atom_count` (mass exponent 1.0), `sqrt(sqrt(tpsa))` (no mass at
all), `n_O/sqrt(n_O)`, and `precursor_mz + precursor_mz`. It reported a
mass-only family in 8 worlds, a non-mass-only family in 3, an empty family in 1,
and `{MASS, carrier}` in 4.

**This is not the proxy-substitution effect that development diagnosed.** On
Phase 3's worlds, block-level agreement was 18/30 (60%) and exponent agreement
22/30 (73%) — the disagreement there was `total_atom_count` standing in for
`precursor_mz` inside one structural block. On fresh worlds, with the non-mass
carrier rotating across three descriptors and every constant redrawn, the
comparison arm collapses to short mass-only or single-descriptor programs and
does not resolve the structure at all.

**The development estimate did not generalize.** That is precisely what fresh
worlds were required for, and it is the single most useful thing this study
learned.

## What passed, stated plainly

The Type 2 machinery itself did what it was built to do.

### Positive controls — Type 2 metrics

| Block | n | Accepted | **Type 2 success** | Support recovered | Exponent within ±0.15 | Shape family | Median selection | Median complexity | Median test R² | Median ceiling fraction |
|---|---|---|---|---|---|---|---|---|---|---|
| `G1A` low | 2 | 2 | **2** | 1.00 | 1.00 | 1.00 | 0.98 | 8 | 0.997 | 1.01 |
| `G1A` moderate | 2 | 2 | **2** | 1.00 | 1.00 | 1.00 | 1.00 | 8 | 0.980 | 1.02 |
| `G1A` adverse | 2 | 2 | **2** | 1.00 | 1.00 | 1.00 | 1.00 | 8 | 0.893 | 1.06 |
| `G1B` low | 10 | 10 | **10** | 1.00 | 1.00 | 1.00 | 1.00 | 8 | 0.993 | 1.08 |
| **`G1B` moderate** | **20** | **19** | **17 (85%)** | **1.00** | **0.90** | **1.00** | **1.00** | **6** | **0.958** | **1.12** |
| `G1B` adverse | 10 | 3 | **3 (30%)** | 0.90 | 0.80 | 1.00 | 0.97 | 6 | 0.817 | 1.11 |
| `G1C` | 10 | 7 | **5** | 0.80 | 0.50 | 1.00 | 0.97 | 8 | 0.915 | 1.11 |
| `G3` | 8 | 8 | **8** | 1.00 | 1.00 | 1.00 | 1.00 | 5 | 0.930 | 1.13 |

On the 20 G1B moderate worlds the reported mass-block exponent had median
**0.500**, range [0.448, 0.540], against a planted 0.5 — **20 of 20 within
±0.15**. Support was recovered in **20 of 20**. The three worlds that fell short
of full Type 2 success did so for two distinct and honest reasons: two recovered
the mass exponent but missed the *non-mass* carrier's exponent by more than 0.15
(`n_O` 0.415 against 0.566; `rotatable_bonds` 0.388 against 0.539), and one
failed seed stability at 0.37.

### Refusal worlds

| Block | n | Accepted | Accepted claiming structure beyond mass | H-MAIN rejected |
|---|---|---|---|---|
| `G2` predictable, not compressible | 8 | **0** | **0** | 8/8 |
| `G3` mass-only | 8 | 8 | **0** | 0/8 |
| `G4` pure null | 100 | **0** | **0** | 0/100 |
| `G4M` mass-conditional null | 30 | 1 | **0** | 0/30 |
| `G5` confounded | 8 | **0** | **0** | 0/8 |
| `GC` measurement coupling | 9 | **0** | **0** | 0/9 |
| `GRT` retention-time surrogate | 4 | **0** | **0** | 0/4 |
| `NCAL` calibration | 100 | **0** | **0** | 0/100 |

`G2` is the world built to have no compact universal collapse, and it is the
only block where H-MAIN rejection occurs — 8 of 8. Refusing to produce an
equation there is the correct outcome and is not penalized.

### False-positive rate

```
false-positive rate = 0 / 100 = 0.0000
```

| Quantity | Value |
|---|---|
| Numerator (null worlds producing an accepted Type 2 family) | **0** |
| Denominator | **100** |
| Rate | **0.0000** |
| Clopper–Pearson exact 95% interval | **[0.0000, 0.0362]** |
| Criterion | ≤ 5% |

A point estimate of 0/N does not license the claim that the population rate is
zero. The interval is the claim. `p = 0` language is not used.

## Type 3 diagnostic — reported separately, and it fails

Exact algebraic-form recovery is **not** part of the Type 2 gate. It is measured
for every world and reported here so that nothing is hidden.

| Block | n | Search **found** the law | System **reported** the law | Symbolically equivalent | Median distinct algebraic forms in the reported family | Worlds claiming the form is identified |
|---|---|---|---|---|---|---|
| `G1A` low/moderate | 4 | 1.00 | 1.00 | **0.00** | 4.0 | **0** |
| `G1B` low | 10 | 1.00 | 0.80 | **0.00** | 9.0 | **0** |
| `G1B` moderate | 20 | 0.90 | **0.40** | **0.00** | 8.5 | **0** |
| `G1B` adverse | 10 | 0.60 | 0.20 | **0.00** | 4.5 | 1 |
| `G1C` | 10 | 0.50 | **0.00** | **0.00** | 10.0 | **0** |
| `G3` | 8 | 1.00 | 0.62 | **0.00** | 7.5 | **0** |

**Type 2 succeeds and Type 3 fails, and that is the finding.** On the G1B
moderate worlds the search put a functionally equivalent form on the front in 18
of 20 worlds, the reported family contained one in 8 of 20, and **not once in
the entire study was an expression symbolically equivalent to the planted law**.
The reported family contained a median of 8.5 distinct functional-equivalence
classes, and in **0 of 20** worlds did the system claim the algebraic form was
identified.

`G1C` is the sharpest case. Its generating law lies outside the frozen grammar
by construction, so no candidate can represent it exactly. The system recovered
the support in 8 of 10 worlds, the shape family in 10 of 10 — and claimed the
algebraic form was identified in **0 of 10**. That is the behaviour the claim
class requires: *the empirical family and its scaling are identified within the
experimental domain; the exact algebraic form is not identified at the current
experimental resolution.*

## Null calibration

100 fresh worlds, cycling the four master-plan §13.6 constructions, 25 each.

| Complexity | Fresh threshold | 95% bootstrap interval | Interval width | Phase 3 (40 worlds) |
|---|---|---|---|---|
| 4 | +0.5584 | [+0.4926, +0.5871] | 0.095 | +0.3888 |
| 6 | +0.6106 | [+0.5619, +0.6643] | 0.102 | +0.4125 |
| 10 | +0.6512 | [+0.5908, +0.6697] | 0.079 | +0.4534 |
| 20 | +0.6831 | [+0.6392, +0.6993] | 0.060 | +0.4889 |

Raising the calibration from 40 to 100 worlds did what `BACKLOG.md` I8 asked:
the mean interval width across complexities is **0.109**, against Phase 3's
0.426 at complexity 20 alone. All 19 accepted G1B moderate candidates clear not
just the threshold but its **upper** bootstrap bound, with a minimum margin of
**+0.2280**.

**A restriction that must be carried forward.** The pooled threshold is
dominated by one construction:

| Construction | Worlds | p95 at c=10 | p95 at c=20 |
|---|---|---|---|
| `descriptors_permuted_across_compounds` | 25 | +0.0205 | +0.0835 |
| `gaussian_targets_with_observed_variance` | 25 | +0.0863 | +0.1509 |
| `target_permuted_across_compounds` | 25 | +0.0703 | +0.1057 |
| **`target_permuted_across_energy_within_compound`** | 25 | **+0.6768** | **+0.7228** |

Permuting the response across energies *within* a compound preserves that
compound's mean level, and the T2 target — the collapse scale `ĝ_i` — is largely
determined by that level. So this construction is a weaker null for this target
than the other three, and it sets the gate almost single-handedly. Phase 3
observed the same asymmetry (+0.5695 against +0.04 to +0.07) with 10 worlds per
construction. It was frozen as one of the master plan's four and was **not**
altered here. The consequence is that the operative threshold is conservative,
which is the safe direction, and any future work should decide explicitly
whether that construction is a valid null for a level-determined target.

## A restriction on the structural claim

The F8 labelling rung certified "structure beyond mass" in only **1 of 19**
accepted G1B moderate worlds, despite support being recovered in 20 of 20. The
contrast with `G1A` — 3 of 6, on a fully synthetic covariate frame where the
descriptors are independent — locates the cause: in the real development
descriptor matrix the mass block alone reproduces most of the fit, so ablating
the non-mass carrier rarely destroys the result by the F8 margin.

This is consistent with Phase 2's mass-coupling sensitivity (regime D,
ρ = −0.4791) and it means that even a Type 2 claim on this corpus would rest
largely on the mass block. It is reported here because it materially limits what
a re-scoped Phase 4 could have claimed, and it did not enter any gate.

## Noise ceiling

`G1B` Type 2 success is **100%** at SD 0.010, **85%** at SD 0.0295 (the Phase 1
conservative inter-mixture variability estimate), and **30%** at SD 0.060. Seven
of the ten adverse-regime failures are falsification failures with support and
exponent both still recovered. Any future work must report the residual scale of
its own fit and treat a candidate found at comparable or worse noise as
unconfirmed.

## Method-development boundary

Development used only already-seen Phase 3 checkpoints and is recorded in
`TYPE2_SELECTION_RULE.md` §5–§6, `TYPE2_ENGINE_CORROBORATION.md` §2 and
`artifacts/ov_dev_*.json`. It never used real `mu`, never touched confirmation
outcomes and generated no fresh world. **No development number appears in any
pass/fail arithmetic above.**

## Deviations

Two, both implementation corrections, both recorded with reasoning in
`DEVIATIONS_OBJECTIVE_VALIDATION.md`, neither touching the selector, a
tolerance, a threshold, a seed, an operator or the decision rule, and neither
changing any generated world — every world's frozen `output_sha256` was
re-verified afterwards. The verdict was computed before and after the second
correction and is identical.

## Repair attempts

**None, and none are permitted.** The pre-registration §15 scopes the repair
allowance to the false-positive gate alone, which did not fail. A failure of any
other gate is not repairable: *"Loosening a criterion because the result is
disappointing is the move this study exists to avoid."* The corroboration
standard is not re-opened, the comparison arm's configuration is not re-tuned,
and the result stands.

## Confirmation seal

| Item | Value |
|---|---|
| SHA-256 **before** the study | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` |
| SHA-256 **after** the study | `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07` |
| Opened at any point | **No** |
| Real-data symbolic search executed | **No** |
| What this study read of the real corpus | Tier A covariates of the 439 development compounds, and confirmation identifiers only, to exclude them |

## Runtime

| Item | Projected | Actual |
|---|---|---|
| PySR | 9,690 runs at 0.874 s | **9,690 runs at 1.309 s**, 211.4 min |
| gplearn | 880 runs | **880 runs**, 22.2 min |
| Total | 2.62 h | **3.89 h** |

The 1.50× per-run slowdown is sustained thermal behaviour on a fanless machine,
which `RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md` flagged in advance as the reason
the honest range was 2.4–3.3 h. Nothing was changed in response. Every one of
the 9,690 + 880 units completed; no unit was lost, and no completed unit was
recomputed.

## Highest defensible real-data claims-ladder rung

# L3

**Unchanged.** This study is entirely synthetic. A synthetic recovery is not a
MURU scientific conjecture and is not called one. L4 requires a real-data
symbolic candidate, which belongs to a Phase 4 that is not authorized.

## Phase 4 authorization

**DO NOT AUTHORIZE PHASE 4.**

Phase 4 is not authorized, in any scope. `PHASE4_TYPE2_FROZEN_PROTOCOL.md` is
**not** written, because §17 makes it conditional on an authorizing verdict.

## What this study establishes, and what it does not

**It establishes** that the Type 2 machinery — the retained Pareto band, the
family-level selection rule, the block-level support and scaling signature, the
reinstated ceiling and H-MAIN conditions, and the enlarged null calibration —
recovers a molecule-conditional empirical family at 85% under moderate noise,
manufactures nothing across 100 pure nulls, 100 calibration nulls, 30
mass-conditional nulls and 29 adversarial worlds, and correctly declines to
claim that the algebraic form is identified in every world where it is not.

**It does not establish** that those families are real rather than
search artifacts. The master plan's own test for that — an independent engine
converging on an equivalent expression — was applied at the claim-relevant level
rather than at the expression level, and still failed: the comparison arm
reproduced the structural claim in 3 of 20 worlds where the claim is true by
construction. Under master plan §13.3's own reading, that is a reason to treat
the selected expressions as search artifacts.

A second stop is a scientifically acceptable outcome, and this one is narrower
and more informative than Phase 3's: Phase 3 stopped because the selector
discarded the truth; this one stops with the selector working and the
corroboration absent.

## What a future attempt would need

Recorded so the reasoning is not lost, and **deliberately not applied here**:

1. **A comparison arm that can express the hypothesis space.** gplearn returns a
   single best program per seed rather than a Pareto front, and at
   `parsimony_coefficient=0.005` it collapses to one- and two-node expressions.
   A second engine that returns a front, or PySR under a genuinely different
   search dynamic, would test convergence rather than testing whether a weaker
   searcher can be made to agree.
2. **A corroboration standard chosen with a power analysis**, not a majority
   rule. 50% of 20 worlds is a coarse instrument.
3. **An explicit decision about the fourth null construction**, which sets the
   operative threshold almost alone and preserves the very quantity the T2
   target estimates.
4. **A resolution of the F8 structural-claim result**, which is the real
   scientific limit here: on this corpus the mass block reproduces most of the
   fit, so a Type 2 claim beyond mass is thinly supported even when the support
   is recovered.

Any of these is a new pre-registration, not an amendment to this one.
