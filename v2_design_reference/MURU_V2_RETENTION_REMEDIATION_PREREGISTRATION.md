# MURU v2: Retention Remediation Preregistration

**Status:** DESIGN ONLY, written and committed **before any E2 outcome is
inspected**. No E2a front has been read by the author of this document. No
retention policy's performance is known. The official v1 result stands at
G2 4/144 and is not reinterpreted by anything here.

**This document operationalizes E4a** (`G2_SINGLE_FACTOR_ABLATIONS`, arm a,
"retention policy"), which `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1 and
`MURU_V2_CAUSAL_DECISION_TREE.md` section B.2 already froze at summary level:
five named arms (R0-R4), their free-parameter grids, and the adoption rule.
**Nothing in that prior freeze is replaced here.** This document is the missing
operational layer: exact pseudocode for every arm, two new arms the prior
design left unregistered (`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 3
E4a row lists R0-R4 only), the machine-readable protocol, the input contract
against E2a's sealed schema, the analysis schema, the provenance manifest
template, and the hostile-review checklist E4a itself never received a
dedicated one for.

Machine-readable twin: `MURU_V2_RETENTION_REMEDIATION_PROTOCOL.json`.
Companion artifacts: `MURU_V2_RETENTION_REMEDIATION_ANALYSIS_SCHEMA.json`,
`MURU_V2_RETENTION_REMEDIATION_E2_INPUT_CONTRACT.json`,
`MURU_V2_RETENTION_REMEDIATION_MANIFEST_TEMPLATE.json`,
`MURU_V2_RETENTION_REMEDIATION_HOSTILE_REVIEW_CHECKLIST.md`.

**Authority chain, most specific first.** Where this document and a prior
frozen document appear to disagree, the prior document wins and this document
has a defect: `MURU_V2_E2_PREDECLARATION.md` section 6 (A-E taxonomy, exact
pipeline functions) > `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1 (R0-R4
definitions, decision rule) > `MURU_V2_CAUSAL_DECISION_TREE.md` section B.2
(licensing gate) > `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 2
(governance frame) > this document.

---

## 0. Scope boundary

This protocol consumes **only E2a** (fresh `V2C` worlds, `DECISION_ADMISSIBLE`,
540 worlds x 30 seeds, already-persisted per-seed Pareto fronts). It never
reads E2b (Held-out replay, `DECISION_INADMISSIBLE`), never reads Held-out or
Challenge case data directly, and proposes no grammar, budget, objective, or
classifier change -- those are E4b/c/d/f's territory, licensed separately and
only if E2's own attribution points there (`MURU_V2_CAUSAL_DECISION_TREE.md`
section B.1). It runs **zero new symbolic search**: every candidate policy
below is a re-scoring of rows E2a's frozen search already emitted and
persisted, exactly the discipline `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section
3.1 states for E4a ("post-hoc on E2's persisted fronts. Zero additional
search").

---

## 1. The question this protocol answers

E2 replaces an inference with a measurement: whether a G2-correct row exists
on a seed's front at all. What E2 does **not** measure is what a *different*
within-seed retention rule, or a different cross-seed vote reduction, would
have done with that same front. That is this protocol's entire subject: given
the front E2a already captured (frozen, unchanged, not re-searched), **how
much correct symbolic signal exists after generation, and which retention
architecture recovers the most of it without paying for that recovery in
parsimony, specificity, or cross-seed stability.**

---

## 2. The A-E first-loss taxonomy (inherited, not redefined)

`MURU_V2_E2_PREDECLARATION.md` section 6 already froze this taxonomy
mechanically, against real pipeline functions, before any E2a world was built.
It is authority here and is reproduced, not altered:

| Stage | Meaning | Design-doc class | Frozen condition (verbatim from the predeclaration) |
|---|---|---|---|
| **A** | truth absent from the candidate pool | `NEVER_ON_FRONT` | `correct_on_front(seed)` false for all 30 seeds |
| **B** | truth available, lost within-seed | `LOST_IN_RETENTION` | `correct_on_front(seed)` true for >=1 seed, `retained_correct(seed)` false for all 30 |
| **C** | survives within-seed, lost cross-seed | `LOST_IN_CROSS_SEED` (aggregation half) | representative not `g2_correct` **and** not `algebraically_equivalent` to truth -- a genuinely incorrect class won the vote |
| **D** | survives aggregation, lost to equivalence/classification | `LOST_IN_CROSS_SEED` (classifier half) | representative not `g2_correct` **but** *is* `algebraically_equivalent` to truth -- the truth-blind classifier failed to recognize a structurally correct winner |
| **E** | final recovery | `SUCCESS` | representative is itself `g2_correct` |

`correct_on_front` and `retained_correct` are evaluated per seed against that
world's own `g2_contract.evaluate_g2_event`. The C/D split is the one
refinement the predeclaration adds beyond the design doc's own four-way
partition, using `discovery.equivalence.algebraically_equivalent` (up to a
positive multiplicative constant, the same tolerance the frozen recovery
hierarchy already uses) as a classifier-independent ground-truth check. Every
case receives exactly one label, in strict A-B-(E-or-D-or-C) decision order;
the partition is exhaustive and non-overlapping by construction.

**What this protocol changes about the taxonomy: nothing.** It recomputes A
through E once per candidate retention policy, holding the front fixed. Stage
A is **policy-invariant** -- the front is a property of the frozen search, not
of retention -- so `|A|` and the eligible pool `|B|+|C|+|D|+|E|` are identical
across every policy compared below. Only the B/{C,D,E} split, and the
C/D/E split within it, can move.

---

## 3. Primary endpoint

```
conditional retention recall (policy P) =

    #{ cases : truth survives retention under P }
    -----------------------------------------------
    #{ cases : truth existed in the eligible candidate pool }
```

Formally, for the fixed, policy-invariant front:

- **eligible pool** = `{case : correct_on_front(case) = true}` = every case
  **not** in stage A. Cardinality is the same for every policy `P`.
- **truth survives retention under P** = at least one of the case's 30 seeds
  retains a G2-correct row **under P's own within-seed retention rule**,
  applied to that seed's already-persisted front (no re-search). This is
  exactly "not stage B under P".
- `conditional_retention_recall(P) = |eligible pool minus stage-B-under-P| / |eligible pool|`

R0 (the frozen v1 rule) reproduces E2a's own sealed B/A/{C,D,E} split by
construction; every other policy is scored against the identical eligible
pool, so **the comparison is paired at the case level**, not an independent
proportion comparison. Section 9 makes the paired statistic explicit.

This is a **within-seed** recall statistic in the sense E2's own section 2.6
distinguishes from v1's cross-seed measurement: it asks whether *retention*,
not generation, is where the signal is lost, using the front-level comparison
`MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.6 says "actually indicts the
retention rule."

---

## 4. Execution trigger (results-blind, mechanical)

This protocol does not execute unconditionally. `MURU_V2_CAUSAL_DECISION_TREE.md`
section B.1 already froze E4a's licensing gate; this section restates it as an
executable predicate over E2a's sealed attribution counts, evaluated **once**,
immediately after E2a seals and before any policy in section 6 is scored.

```
Let A, B, C, D, E = case counts of the five stages over all 540 E2a cases.
Let NONSUCCESS = A + B + C + D.

GATE 1 (falsification hook, checked first, from B.1's first branch):
    IF E2b's direct measurement contradicts the v1 decomposition's
    69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
    tolerance) --
        THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended
        per MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9's falsification
        hook. The non-execution, and the E2a/E2b divergence that caused it,
        is reported in place of any policy comparison. STOP.

GATE 2 (retention-dominance, B.1's second and fifth branches):
    IF B is the strict plurality of {A, B, C+D}  -- i.e. B > A AND B > C+D --
        THEN this protocol EXECUTES. RC3 is confirmed by direct observation;
        E4a is enabled.
    ELSE IF P_retain_given_front is near 1 wherever P_front is high (the
        exoneration condition) --
        THEN this protocol DOES NOT EXECUTE. RC3 is WITHDRAWN and reported as
        such; no retention policy is scored. STOP.
    ELSE IF A is the strict plurality --
        THEN this protocol DOES NOT EXECUTE. RC4 is confirmed; the next
        licensed step is E3-gated (E4b/c/d), not this document. STOP.
    ELSE IF C+D is the strict plurality --
        THEN this protocol DOES NOT EXECUTE as adoption-relevant; RC7 is
        larger than v1's 2 cases and E4f (classifier/voting) is the licensed
        arm. Section 8's C/D metrics are still reported, unchanged, as the
        diagnostic record E4f will need, but no retention *adoption* decision
        is made here. STOP for adoption purposes.
    ELSE (no strict plurality; a tie or a near-uniform split) --
        THEN this protocol EXECUTES in DIAGNOSTIC-ONLY mode: every policy in
        section 6 is scored and reported, but section 10's adoption rule is
        suspended pending a named tie-breaking review, because the frozen
        decision tree does not cover a non-plurality outcome and inventing a
        tie-break now, after seeing the counts that produced the tie, would
        not be results-blind.
```

**This is the exact, complete, mechanical trigger.** Nothing about section 6's
policy definitions, section 7's population split, or section 10's adoption
rule may be altered by which branch fires -- the *policies* are frozen now,
before Gate 1 or Gate 2 is evaluated for real; only whether comparison
proceeds, and whether its result may license adoption, depends on the gate.

---

## 5. Candidate retention policies

**Discipline, inherited from `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3:**
one factor -- the within-seed retention rule -- at a time. The cross-seed
grouping mechanism (`identity_contract.template_key` grouping, largest-class-
wins, lowest-ordinal tie-break -- `rc5_selection.group_and_select`) is held
fixed for every policy. A policy that retains more than one row per seed
still casts exactly **one** cross-seed vote per seed, by a single frozen
reduction rule stated once here rather than reinvented per policy:

> **Vote-reduction rule (frozen, applies to every multi-row policy below).**
> A seed's cross-seed vote is cast by the `argmax(valid_r2)` row among that
> seed's own retained set. `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1
> already states this for R3 ("whole front, seed votes for its best member by
> `valid_r2`"); this document generalizes the identical rule to every
> multi-row arm rather than inventing a distinct rule per arm, which would be
> an unregistered extra degree of freedom.

Retention itself (what counts toward "truth survives retention", candidate-set
size, and complexity burden) and the cross-seed vote (what counts toward
stages C/D/E and `selection_count`) are therefore two **separate**, both
frozen, functions of the same front.

| Arm | Rule (within-seed retention) | Free params | Role |
|---|---|---|---|
| **R0** | `argmax(score)` | 0 | **Control.** Frozen v1 production rule. Reproduces E2a's own sealed labels exactly (section 11's replay check). |
| **R1** | `argmax(valid_r2)` | 0 | Single-row, accuracy-only alternative. |
| **R2** | top-`k` rows by `score`; `k` in `{1, 2, 3, 5}` | 1 (`k`) | Breadth without full retention. `k=1` degenerates to R0. |
| **R3** | whole front (every row) | 0 | **Oracle/control, not adoptable.** Measures the retention ceiling. See section 5.1. |
| **R4** | among rows with `valid_r2 >= max(valid_r2) - eps`, keep the lowest-complexity row; `eps` in `{0.001, 0.005, 0.02}` | 1 (`eps`) | Caps the accuracy-for-parsimony exchange rate the v1 evidence (+0.121 `valid_r2` at +3.4 complexity, 70/75 paired cases) showed retention paying. |
| **R5** | Pareto-nondominated subset of the front in `(valid_r2, -complexity)`: a row survives iff no other row on the same front has both `valid_r2` >= its own and `complexity` <= its own, with at least one strict | 0 | Genuine multi-objective retention, distinct from R3 (which keeps dominated rows too) and R4 (which keeps a single row). |
| **R6** | top-3 rows by `score`, further restricted to rows whose `template_key` recurs in the top-3 of at least 2 of the world's other 29 seeds | 0 (frozen directly, not DEV-selected -- section 5.2) | Cross-seed-stability-aware retention: a row must show corroborating structure elsewhere in the *same case* before it is retained, not only score well in isolation. |

### 5.1 Why R3 cannot win

The mission is explicit that a policy must not win "simply by retaining
everything unless the design explicitly treats full-Pareto retention as an
oracle/control." R3 is registered under exactly that label. It is scored on
every metric in section 8 like every other arm, but it is excluded from
section 10's adoption set by construction, for two independent, pre-declared
reasons, not one:

1. **It is definitionally certain to win or tie on conditional retention
   recall.** If a correct row is on the front at all (not stage A), R3
   retains it by definition; R3's recall equals `1 - |A| / eligible pool`'s
   complement... concretely, R3's within-seed recall is a tautology, not a
   finding. Reporting it as though it competed with R0-R2/R4-R6 would let
   the "retain everything" temptation the master remediation plan's lens 4
   already names win by construction.
2. **Its candidate-set size and complexity burden are reported but never
   traded off.** R3's `candidate_set_size` is the full `front_size` (E2a's
   own design doc puts front sizes at "~15 rows" per seed on average --
   section 2.10), the largest of any arm by construction, which is precisely
   the axis section 10's adoption rule requires every *adoptable* arm to be
   evaluated against.

R3's reported numbers are the **ceiling** every other arm is measured against,
not a competitor for adoption. `engine_inefficiency`-style headline framing
(`MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.5) is the model: report the gap,
do not rank the oracle.

### 5.2 R6's constant is frozen directly, not Development-tuned

R6 has two integer knobs: the per-seed shortlist size (3) and the minimum
cross-seed recurrence count (2 of the other 29). Per the mission's instruction
("preregister how that constant is selected using Development only **or omit
it**"), this protocol omits the Development-tuning step for these two knobs
and freezes them directly, for stated reasons, before any data is seen:

- **Shortlist size 3** matches R2's own already-frozen grid value `k=3`
  exactly, so R6 is legible as "R2 with a stability filter added" rather than
  introducing an unrelated magnitude.
- **Minimum recurrence 2** is the smallest threshold that is not "any single
  other seed" (recurrence >= 1, which is nearly guaranteed by chance whenever
  a front has >=2 correct rows anywhere) and not a majority (which would make
  R6 nearly indistinguishable from requiring `selection_count` to already
  clear the stability gate before retention is even attempted, collapsing the
  two pipeline stages this protocol exists to keep separate). "At least two
  independent seeds agree" is the minimal corroboration threshold above pure
  chance.

Freezing these directly (rather than selecting from a grid on
`V2C_RET_DEV`) means R6 carries **zero** free parameters into section 10's
tie-break, exactly like R0, R1, R3, and R5.

---

## 6. Population and the Development/Evaluation split

**Population.** All 540 E2a cases (5 truth families x 3 coefficient regimes x
3 noise levels x 12 replicates), enumerated by the deterministic
`world_ordinal` formula `MURU_V2_E2_PREDECLARATION.md` section 4 already
fixed:

```
world_ordinal = ((family_idx*3 + regime_idx)*3 + noise_idx)*12 + replicate
family_idx in [0,5), regime_idx in [0,3), noise_idx in [0,3), replicate in [0,12)
```

**Split, fixed here, before any front is read, purely as a function of
`replicate`:**

```
V2C_RET_DEV  = { case : replicate in {0, 1} }    -- 2 of 12 per cell, 90 cases
V2C_RET_EVAL = { case : replicate in {2..11} }   -- 10 of 12 per cell, 450 cases
```

The split is **stratified by construction**: every one of the 45
`(family, regime, noise)` cells contributes exactly 2 cases to
`V2C_RET_DEV` and exactly 10 to `V2C_RET_EVAL`, so no family, regime, or
noise level is over- or under-represented in either half. This mirrors the
discipline `MURU_V2_A1_STUDY_DESIGN.md`'s E1 already uses (an 80/20
`CALIBRATE`/`CONFIRM` split, sealed at generation time, opened once after
selection) rather than inventing a new one.

**Role.**

- `V2C_RET_DEV` (90 cases) is the **only** surface on which R2's `k` and
  R4's `eps` are selected (section 6.1). It is never used for the headline
  policy comparison.
- `V2C_RET_EVAL` (450 cases) is the surface for every metric in section 8,
  every adoption decision in section 10, and every predicted number in
  section 13. It is opened for scoring exactly once, after `k` and `eps` are
  fixed on `V2C_RET_DEV` alone.
- Section 4's gate-evaluation counts (A/B/C/D/E dominance) are computed on
  the **full 540-case population**, not the split, because that gate is a
  diagnostic fact about E2a's own attribution, not a policy-tuning decision.

### 6.1 Development-only constant selection (R2, R4)

For each grid (`k` in `{1,2,3,5}` for R2; `eps` in `{0.001,0.005,0.02}` for
R4), evaluated on `V2C_RET_DEV` only:

1. Compute `conditional_retention_recall` for R0 and for every grid value,
   restricted to `V2C_RET_DEV`'s 90 cases.
2. For each grid value, compute the **paired** improvement over R0 (section 9's
   paired bootstrap) on `V2C_RET_DEV`.
3. Select the **smallest** grid value whose paired improvement's 95 percent
   bootstrap lower bound exceeds 0.
4. If no grid value clears that bar, the entire policy family (R2 or R4) is
   **not eligible for adoption** in section 10, regardless of its
   `V2C_RET_EVAL` performance. It is still scored and reported on
   `V2C_RET_EVAL` for transparency (an arm that looks good only on the
   evaluation split and not on development is itself a finding, not a result
   to hide), but it cannot be the arm section 10 adopts.
5. The selected `k`/`eps` (or the family's disqualification) is recorded in
   the manifest (`MURU_V2_RETENTION_REMEDIATION_MANIFEST_TEMPLATE.json`)
   before `V2C_RET_EVAL` is scored, and is never revisited after.

This is the one place this protocol looks at any data before the headline
comparison, and it is scoped, mechanical, and disclosed exactly the way E1's
`CALIBRATE`/`CONFIRM` split and E3's oracle-ceiling framing already are.

---

## 7. Required metrics

Computed per policy (R0-R6), on `V2C_RET_EVAL` unless stated otherwise. Every
proportion carries a 95 percent Wilson interval via `g2_contract.wilson_lower_95`
/ `wilson_upper_95` (reused, not reimplemented). Every policy-vs-R0 comparison
additionally carries the paired statistic from section 9.

| # | Metric | Definition | Task requirement satisfied |
|---|---|---|---|
| 1 | `conditional_retention_recall` | Section 3's formula | primary endpoint |
| 2 | `false_structure_rate_proxy` | Among the 108 `mass_power`-truth cases (36 in `V2C_RET_EVAL`; see note below), fraction whose cross-seed representative under `P` is **not** `mass_power` -- a spurious descriptor/interaction/exponential structure survived retention and the vote on a truth that has none | specificity |
| 3 | `candidate_set_size` | Rows retained per seed under `P`, mean and median, over all seeds (not just eligible-pool cases) | candidate-set size |
| 4 | `complexity_burden` | (a) mean/median `engine_complexity` of the retained set per seed; (b) mean/median `engine_complexity` of the cross-seed representative | complexity burden |
| 5 | `cross_seed_stability` | Distribution of `selection_count` (0..30) for the winning class under `P`; fraction of eligible-pool cases whose `selection_count` still clears `STABILITY_GATE / STABILITY_DENOMINATOR = 20/30` (`structural_acceptance.py`, reused not reproduced) | cross-seed stability |
| 6 | `family_performance` | `conditional_retention_recall` and `E`-stage rate, broken out per truth family (5 rows) | family-level performance |
| 7 | `worst_family_performance` | `min` over the 5 families of `conditional_retention_recall(P)` | worst-family performance |
| 8 | `final_downstream_recovery` | Fraction of eligible-pool cases reaching stage **E** under `P` (i.e. G2-analogue success after `P`'s own retention **and** the frozen vote-reduction rule) -- **admissible** because it stays entirely inside E2a's `DECISION_ADMISSIBLE` population; never computed against Held-out | final downstream recovery where permitted |
| 9 | `compute_memory_cost` | Wall-clock and peak memory of the re-scoring pass itself (section 12); zero additional search cost by construction | compute/memory cost |

**Note on metric 2.** E2a's own world population (section 6) contains no
dedicated null/adversarial worlds of the kind E6 uses (mass-only-truth
negative controls, destroyed-link nulls, adversarial substitutions). This
protocol's `false_structure_rate_proxy` reuses E2a's `mass_power` family --
the only truth-negative-support family already inside the sealed population,
at zero additional cost -- as a **necessary but not sufficient** specificity
signal. **A policy clearing this proxy is not thereby cleared for adoption
without a formal E6 run against it**; section 10 states this as a hard
prerequisite, not a formality. This scoping is disclosed here rather than
silently substituting the proxy for E6, per the master plan's own lens 7
discipline (arms must not claim a safety clearance they were not measured
against).

---

## 8. Statistical procedure

- **Paired comparison, primary.** For any policy `P` against control R0 on
  `V2C_RET_EVAL`'s 450 cases: build the 2x2 discordant-pair table (`P` wins
  where R0 does not; R0 wins where `P` does not; both; neither) on
  `conditional_retention_recall`'s underlying binary per-case indicator.
  Report the exact McNemar test on the discordant cells and a
  **case-level bootstrap** 95 percent CI on the net difference
  (`P` recall minus R0 recall), `B = 10,000` resamples, resampling cases
  with replacement within `V2C_RET_EVAL` (never across the DEV/EVAL split).
- **Bootstrap seed, frozen.** `derive_seed_v2("bootstrap", "<policy_id>")`
  (the same `SHA-256` construction `e2_worlds.py::derive_seed_v2` already
  uses, under the `V2C` namespace prefix so it cannot collide with any search
  seed) truncated to a `numpy.random.Generator`-compatible 64-bit unsigned
  integer. Deterministic and independently reproducible; no new seed band is
  registered because no PySR `random_state` is consumed (zero search).
- **Single-proportion intervals** (e.g. `false_structure_rate_proxy`,
  per-family `conditional_retention_recall` reported in isolation) use
  `g2_contract.wilson_lower_95` / `wilson_upper_95` directly, imported not
  reimplemented.
- **Multiple comparisons.** Seven policies (R1, R2 x 4 grid values pre-reduced
  to 1 by section 6.1, R3, R4 x 3 grid values pre-reduced to 1, R5, R6) are
  compared against one control on one primary endpoint. Section 6.1's
  Development-only pre-reduction is the family-wise error control for R2 and
  R4's internal grids (the grid search happens on `V2C_RET_DEV`, never on the
  surface the p-value is computed against). The six remaining head-to-head
  comparisons against R0 (R1, R2*, R3, R4*, R5, R6) are reported with
  unadjusted paired CIs **and** with a Holm-Bonferroni-adjusted significance
  flag at `alpha = 0.05` across the 6, so a reader can see both the raw and
  the multiplicity-corrected picture.

---

## 9. Controls

1. **Replay self-consistency (not a new control -- a reuse of E2's own gate).**
   R0 scored by this protocol's own re-scoring pipeline must reproduce
   E2a's own sealed A/B/C/D/E counts and `selection_count` values exactly,
   because R0's retention rule is byte-identical to the one E2a's own
   `e2_aggregate.evaluate_world` already applied. Any discrepancy is a defect
   in this protocol's implementation, not a finding, and blocks every other
   policy's results from being reported until resolved.
2. **Frozen front.** No policy re-runs or perturbs the search. Every policy
   operates on the identical, already-persisted `FrontRow` sequence per seed.
   A static check asserts that no function in this protocol's implementation
   imports `rc5_estimate`, `rc5_adapter`, PySR, or Julia -- the search-side
   modules -- so "zero additional search" is enforced structurally, the same
   discipline `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.5 uses for E2's
   own retention-identity regression.
3. **Vote-reduction rule held fixed across arms** (section 5's boxed rule),
   so a recall improvement cannot be confounded with a simultaneously
   different cross-seed voting change -- exactly the attribution-exclusivity
   discipline `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 5 lens 7
   requires between arms that could otherwise claim the same effect twice.
4. **`mass_power` specificity arm is scored identically to the four
   descriptor-bearing families** -- no separate, more permissive rule for it
   -- so `false_structure_rate_proxy` cannot be inflated by construction.

---

## 10. Selection and adoption criteria (frozen, extended from E4a)

Inherits `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1's decision rule and
`MURU_V2_CAUSAL_DECISION_TREE.md` section B.2's branches verbatim, extended to
cover R5 and R6:

**An arm `P` in {R1, R2*, R4*, R5, R6} (R0 excluded as control, R3 excluded
per section 5.1) is adoption-eligible iff, on `V2C_RET_EVAL`, all of:**

1. Its `conditional_retention_recall` improvement over R0 has a paired
   bootstrap 95 percent lower bound **above 0** (section 9).
2. Its `false_structure_rate_proxy` does **not** exceed R0's own
   `false_structure_rate_proxy` by more than the E6 ceiling's own margin
   (0.15 Wilson-upper, mirroring G3's gate --
   `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 3 E6). Clearing this proxy
   is necessary, **not sufficient**: adoption additionally requires a formal
   E6 run against the specific adopted arm before any v2 architecture change
   is finalized (section 7's note; this is a hard prerequisite this document
   cannot waive).
3. Its `cross_seed_stability` fraction-clearing-the-20-of-30-gate does not
   fall below R0's own, for the eligible-pool cases -- an arm that raises
   recall by fragmenting votes across near-duplicate classes and thereby
   collapsing `selection_count` is rejected, or adopted only together with a
   re-derived stability gate, which is itself a separately authorized
   experiment (`MURU_V2_CAUSAL_DECISION_TREE.md` section B.2, third branch).
4. For R2 and R4 specifically: its grid value was selected by section 6.1's
   Development-only rule and was not disqualified there.

**Among adoption-eligible arms, the tie-break is lexicographic and
pre-declared:**

```
1. fewest free parameters        (R0=0, R1=0, R5=0, R6=0  <  R2=1, R4=1)
2. lowest false_structure_rate_proxy
3. lowest median candidate_set_size   (parsimony / storage burden)
4. lowest ladder index: R0 < R1 < R5 < R6 < R2 < R4
   (R3 excluded entirely -- section 5.1)
```

**If no arm is adoption-eligible:** `NO CHANGE LICENSED`. The frozen R0
retention rule stands, and RC3's attribution is revised downward exactly as
`MURU_V2_CAUSAL_DECISION_TREE.md` section B.2's fourth branch already states.
This is a fully valid, fully reportable outcome, not a failure of the
protocol.

---

## 11. What this protocol does not decide

1. **No grammar, budget, objective, or classifier change.** Those are E4b,
   E4c, E4d, E4f's territory and are licensed only by E2's own attribution
   (section 4's gate), never by this document.
2. **No E6 run.** `false_structure_rate_proxy` (metric 2) is a necessary
   screen computed at zero extra cost from E2a's own sealed population; it is
   not a substitute for E6's dedicated null/adversarial population and does
   not by itself clear any arm for adoption (section 10, item 2).
3. **No re-derivation of the stability gate.** `20/30` stays fixed
   (`structural_acceptance.STABILITY_GATE` / `STABILITY_DENOMINATOR`,
   imported, not restated as a new constant) for every arm's own scoring; an
   arm that needs a different gate to look adoptable is flagged, not silently
   accommodated.
4. **No Held-out or Challenge access.** Every case, seed, and front row this
   protocol touches originates in E2a's `V2C` namespace. A static import-graph
   check (mirroring `pb_35_a3_4_integrity.py`'s discipline) asserts this
   protocol's implementation never imports `registry.resolve_case_id` or any
   Held-out/Challenge-partition loader.
5. **No v2 architecture decision.** Section 10's adoption verdict is an input
   to that decision, one arm among several this remediation plan's E4 register
   produces, not the decision itself.

---

## 12. Cost

Every policy is a re-scoring of already-persisted rows: no PySR run, no Julia
call, no new world. The work is: (a) apply each policy's within-seed rule to
each seed's already-parsed front (vectorizable, O(front rows) per seed); (b)
apply the frozen vote-reduction rule and re-run `group_and_select`-equivalent
grouping per policy (O(30) per case); (c) the paired bootstrap (`B=10,000`
resamples x 6 head-to-head comparisons x 450 cases, entirely in memory, no
re-parsing). No `sympy.simplify` call is repeated -- E2a's own classification
cache (`e2_classify.py`, memoized by expression string) is reused verbatim,
never recomputed, since classification is truth-blind and policy-independent.

**Estimate: under 1 CPU-hour, under 50 MB of new output**, dominated by I/O
over the 540 x 30 x ~15-row front table, not computation. Matches
`MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1's own E4a cost line ("zero
search, minutes of re-scoring") generalized from 5 arms to 7.

---

## 13. Pre-registered predictions

Stated now, before any front is read, so a miss is a finding rather than a
quiet revision (the discipline `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md`
section 5 lens 8 requires).

| ID | Prediction |
|---|---|
| PRR-1 | R3's `conditional_retention_recall` on `V2C_RET_EVAL` is at or within Wilson noise of 1.0 for every family except `mass_saturating_descriptor`, confirming section 5.1's claim that R3's recall is close to tautological rather than a finding. |
| PRR-2 | At least one of R2*, R4*, R5 clears section 10's adoption bar, conditional on Gate 2 (section 4) selecting the retention-dominant branch -- because `MURU_V2_G2_PARETO_STUDY_DESIGN.md`'s own PE4a-1 already predicts R4 with `eps=0.005` raises G2 success over R0 without raising false structure. |
| PRR-3 | R6's `conditional_retention_recall` improvement over R0 is smaller than R2*'s and R4's, because R6's cross-seed corroboration requirement is the most conservative filter registered (closest to R0 in effective selectivity), but its `false_structure_rate_proxy` is the lowest of any non-control arm, because corroboration across independent seeds is specifically a false-positive suppressor. |
| PRR-4 | `mass_saturating_descriptor` (the F09 analogue) is the `worst_family_performance` family for every policy including R3, because `MURU_V2_G2_PARETO_STUDY_DESIGN.md`'s own PE2-2 already predicts `P_front` for this family is below 0.1 even with the whole front observed -- i.e. this protocol predicts the family's ceiling is set by stage A, which no retention policy can move, not by stage B. |
| PRR-5 | Stage D (classifier/equivalence loss) is small relative to stage C (genuine cross-seed vote loss) across every policy, because RC7's v1 evidence (`SELECTION_CROSS_SEED_IDENTITY`, 2 of 144 cases) was already small before this finer split existed. |

---

## 14. Hostile-review summary

Full checklist: `MURU_V2_RETENTION_REMEDIATION_HOSTILE_REVIEW_CHECKLIST.md`.
Condensed here in the master plan's own lens format.

| Lens | Attack | Residual risk after this design |
|---|---|---|
| Retain-everything | R3 wins by construction | Excluded from adoption by section 5.1, reported as ceiling only |
| Free-parameter leakage | R2/R4's `k`/`eps` chosen after seeing the comparison that matters | Selected on `V2C_RET_DEV` only (section 6.1), never revisited on `V2C_RET_EVAL` |
| Specificity substitution | `false_structure_rate_proxy` quietly stands in for E6 | Explicitly declared necessary-not-sufficient; adoption requires a separate E6 run (section 10 item 2) |
| Attribution exclusivity | A recall gain is actually a vote-reduction-rule effect | Vote-reduction rule frozen identically across every arm (section 5) |
| Multiple comparisons | 6 head-to-head tests inflate false-positive adoption | Holm-Bonferroni flag reported alongside raw CIs (section 9) |
| Gate gaming | Section 4's trigger reinterpreted after counts are seen | Trigger stated as an executable predicate with no free interpretation left (section 4) |
| Held-out leakage | This protocol quietly reads Held-out for a stronger denominator | Static import-graph check forbids it (section 11 item 4) |

---

## 15. Terminal state

```
RETENTION REMEDIATION PROTOCOL FROZEN RESULTS-BLIND
```

No E2a front read. No policy scored. No adoption decision made. Execution is
gated exactly by section 4 and does not begin until E2a seals and an
independent party confirms this document was committed before the seal.
