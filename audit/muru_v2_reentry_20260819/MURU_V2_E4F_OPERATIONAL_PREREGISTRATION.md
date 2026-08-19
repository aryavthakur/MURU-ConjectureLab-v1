# MURU v2 — E4f OPERATIONAL PREREGISTRATION
## `G2_SINGLE_FACTOR_ABLATIONS / E4f — FAMILY CLASSIFIER AND VOTING RELATION`

> ## THIS IS A PROSPECTIVE POST-GATE-1 PROTOCOL-OWNER AMENDMENT
> ## CREATED UNDER THE MAXIMUM-AUTHORIZATION INSTRUCTION.
> ## IT IS **NOT** HISTORICALLY PREREGISTERED AND MUST NEVER BE DESCRIBED AS SUCH.
>
> Authority to exist: `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10, and
> `design_council/P2_GOVERNANCE_LEAKAGE.md` open items 33 and 34, which direct that the
> two absent E4f ceilings be supplied either by declaring E4f non-executable (BC-21) **or**
> by *"commission[ing] a separate operational preregistration for it."* This document is
> that commission. Calling it "preregistration" without the qualifier above is a
> provenance misstatement of the exact kind the Gate 1 record already had to withdraw once.

---

## 0. RESULTS-BLIND ATTESTATION — THE REASON THIS DOCUMENT EXISTS NOW

**Frozen at commit `119ba265e16d2fed04cc332b879803b407562a05`** (branch
`claude/muru-v2-autonomous-reentry`, 2026-08-19), which is the repository HEAD at the moment
of authorship and is a **strict ancestor** of any commit that will ever contain an E4f
result.

At that commit, and therefore at the moment every threshold below was fixed:

| Fact | State at the freeze commit |
|---|---|
| A qualified calibration surface (E7 Stage 1) | **Does not exist.** No world generated, no partition amended, no search executed |
| Any E4f front corpus | **Does not exist** |
| Any routing result | **Does not exist.** `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` is frozen protocol text, unexecuted |
| Whether E4f will be licensed at all | **Unknown, and currently improbable.** Its own routing protocol carries two standing hostile-review FAIL verdicts (`CRITIC_GOVERNANCE_REENTRY.md`, `CRITIC_SCIENCE_REENTRY.md`, both at HEAD `119ba26`), one of which argues the licensing terminals are arithmetically unreachable |
| Any `false_labelling_rate` or `k_inflation` value, for any arm, on any population | **Does not exist and has never been computed by anyone** |

**Attestation.** No threshold, margin, estimator, gate, population, split or terminal in
this document was consulted from, derived from, tuned to, or checked against any E4f
outcome, any calibration-surface outcome, or any routing outcome — because none exists.
The prior governance finding that *"inventing this ceiling after the route is known is the
highest-leverage cheat available"* (`P2_GOVERNANCE_LEAKAGE.md` line 685;
`SYNTHESIS_DECISION_RECORD.md` line 701) is the entire reason for writing now rather than
later. Writing it now makes that cheat mechanically impossible: the freeze commit precedes
every possible datum.

**Everything executed during authorship, disclosed exhaustively.** Three read-only
operations were run against frozen source, none of which touches an outcome:

1. `git show muru-authority/befca0d-study-design:MURU_V2_G2_PARETO_STUDY_DESIGN.md` and
   `sed`/`grep` reads of `v2_design_reference/*.md`, `src/muru/paper_benchmark/*.py`,
   `src/muru/discovery/equivalence.py`, `scripts/e2b_bounded_determinacy_evaluator.py`.
2. `registry.CASE_FAMILIES` enumerated to map the 12 G2 conditions onto their
   `generative_kind` and thence onto truth families (§4.1). This is registry metadata,
   frozen since v1, and contains no result.
3. **A parse check** of the twelve constructed negative-control strings in §5.3, confirming
   `g2_contract._safe_parse` accepts them and `extract_effective_support` returns the
   support the construction intends. **No family label was computed, for any arm, on any
   input.** The check establishes that the negative population is *constructible*; it
   cannot and does not establish what any arm will do to it.

**Threshold discipline (binding on every number below).** Every number is either
**(i) REUSED VERBATIM** from frozen authority with a verified citation, or **(ii) DERIVED**
with the derivation shown inline. §14 is the complete inventory. §15 is the exhaustive,
hostile-facing list of every free parameter this document was forced to introduce.
**No wall-clock cap decides a label anywhere in this protocol** (§10).

---

## 1. STATUS, DEPENDENCY, AND WHAT THIS DOCUMENT DOES NOT DO

**Status: protocol text, frozen, not executed. E4f remains NON-EXECUTABLE at this commit.**

This document does **not** license E4f, does not un-suspend it, and does not weaken
ratification §4 (D2-ext: *all E4 arms suspended; no automatic re-entry*). E4f's frozen
prerequisite is **E2 — a calibration surface** (`befca0d` §4 table, row E4f: *"Licensed by
… E2 provides the fronts"*; `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` line 316,
*"Prerequisite: E2"*). No such admissible surface exists.

What this document removes is exactly one blocker, the one P2 flagged as un-improvisable:

> P2 open item 33: *"`false_labelling_rate` ceiling — **OPEN — genuinely absent**"*
> P2 open item 34: *"`k_inflation` ceiling — **OPEN — genuinely absent**"*

and, alongside them, the four further absences the forward-authority map records
(`audit/e2b_definitive_cloud_adjudication_20260818/FORWARD_AUTHORITY_MAP.md` lines 779–780):
*"no population, no DEV/EVAL split, no statistical procedure, no replay [control]."*

If E4f is never routed to, this document is simply never executed, and that is a normal
outcome (§13, terminal `E4F_NOT_ENTERED_NO_ROUTE`).

---

## 2. AUTHORITY

| Source | What it supplies, verified by direct read |
|---|---|
| `muru-authority/befca0d-study-design:MURU_V2_G2_PARETO_STUDY_DESIGN.md` §3.6 | The two factors, the six arms, the controls K0/V0, the four metrics **in priority order**, the adversarial-negative *construction*, the adoption rule ("coverage is not the adoption criterion"), the standing prior against V1, and the cost ("zero search; 2 CPU-hours of scoring") |
| same, §2.4 / §2.5 / §2.10 | 28-field front schema; retention-identity and replay-fidelity controls; `SIMPLIFY_TIMEOUT` must be an explicit status, never a silent `None`; *"simplify is unbounded in the worst case"* |
| same, §3 preamble | *"One factor at a time. No arm changes two factors."*; every arm reports its E6 false-structure metric in the same table; *"Reporting a G2 gain without its safety cost is not permitted."* |
| `v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` lines 316, 341, 572, 574 | Metric order **`false_labelling_rate` first, then coverage, then `k_inflation`**; cost **0 (post hoc)**; prerequisite **E2**; the two named failure modes and their guards |
| `v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` §B.1, §B.6, §3, §4, §6 | The licensing edge into E4f (`LOST_IN_CROSS_SEED` dominant); the E4f branch structure; E6's veto and its **`Wilson upper ≤ 0.15` on ≥ 100 opportunities**; the terminal-leaf discipline; the two explicitly-unlicensed changes |
| `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` §5, §10, §14, §17, §25, §26, §27, §28, §31, §32 | The population, the 28-field schema, the post-hoc scoring pass, the determinacy bound and its no-wall-clock rule, the DEV/EVAL split, the multiplicity convention, the replay controls, the freeze procedure, the terminal-state discipline |
| `f4c1105` (`…RETENTION_REMEDIATION_PREREGISTRATION.md`) §6.1, §7, §8, §9.1 | Improvement bar *paired 95% lower bound > 0*; Wilson method; Holm–Bonferroni at `α = 0.05`; `B = 10,000` bootstrap; replay self-consistency control |
| `src/muru/paper_benchmark/g2_contract.py` | `classify_discovered_family`, `extract_effective_support`, `classify_support`, `classify_family_match`, `evaluate_g2_event`, `truth_support_for_case`, `wilson_lower_95` / `wilson_upper_95` — the operational meaning of "label" and "correct" |
| `src/muru/paper_benchmark/rc5_selection.py` | `select_row_label` (`argmax(score)`), `group_and_select`, `EquivalenceClass`, `selection_count`, `stability_gate_passed` — the operational meaning of `k` |
| `src/muru/paper_benchmark/identity_contract.py` | `template_key` (V0), the canonicalisation pipeline reused by K1, `_MAX_OPS_BEFORE_FALLBACK = 400` |
| `src/muru/discovery/equivalence.py` | `algebraically_equivalent` (V2) and its deterministic `SIMPLIFY_TIMEOUT_TERMS = 400` op-count bound |
| `scripts/e2b_bounded_determinacy_evaluator.py` | The bounded-determinacy pattern: a cost cap yields `UNRESOLVED`, **never a class**; a class is emitted only when invariant over every resolution |

**This protocol licenses nothing by itself.** It defines an instrument and the predicate
that instrument's output is read through.

---

## 3. THE FROZEN DESIGN, RESTATED VERBATIM AND NOT EXTENDED

**Two independent sweeps. One factor at a time. The 3 × 3 grid is not the design.**

**E4f-i — discovered-family classifier** (`befca0d` §3.6, F-i):

| Arm | Classifier | Free parameters in the arm itself |
|---|---|---|
| **K0** | frozen `g2_contract.classify_discovered_family` (**control**) | 0 |
| **K1** | K0 plus a canonical structural normal form before pattern matching | 0 (see §6.1) |
| **K2** | behavioural identification: fit each of the five truth-family parametric forms to the **candidate's own predicted values** and label by best fit | 0 (see §6.2) |

**E4f-ii — cross-seed voting relation** (`befca0d` §3.6, F-ii):

| Arm | Grouping key |
|---|---|
| **V0** | `identity_contract.template_key` (**control**) |
| **V1** | `(effective_support, discovered_family)` |
| **V2** | algebraic equivalence under `discovery.equivalence` |

**Metric order, frozen and binding** (`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` line 316;
`befca0d` §3.6): **`false_labelling_rate` → coverage → `k_inflation` → G2 case success.**
§8 encodes this as **sequential gates**, not as a score.

**Cost, frozen: 0 new search.** E4f re-scores fronts that already exist
(`REMEDIATION_EXPERIMENT_PLAN` line 348: *"E4a and E4f cost nothing beyond re-scoring"*).
**No clause of this protocol may be satisfied by running a search.** Any implementation
that invokes the discovery engine on any world for any E4f purpose is a protocol violation
and voids the run (§13 `E4F_VOID_COST_CONTRACT_BREACH`).

**One-factor discipline, and what it does to the multiplicity family.** Because *"no arm
changes two factors"*, E4f-i is evaluated at **V = V0 held fixed** and E4f-ii at
**K = K0 held fixed**. There are therefore **four** treatment-vs-control comparisons, in
**two disjoint families of two**, not nine. The remaining four off-diagonal cells
(K1V1, K1V2, K2V1, K2V2) **are computed and reported as a descriptive interaction map and
are inadmissible for adoption** — `befca0d` §3: *"Any joint or interaction study is a
separately authorised later stage that may combine only factors already shown individually
admissible."* The interaction map is stamped `DESCRIPTIVE_ONLY` at the record level and
the static citation checker must reject any proposed change citing an off-diagonal
identifier.

---

## 4. POPULATION

### 4.1 The scored population `P_G2` — zero new search

`P_G2` = **the persisted per-seed Pareto fronts of a qualified calibration surface**, in the
sense of `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` §5:

| Stratum | Conditions | Replicates | Worlds | Seeds | Front rows |
|---|---|---:|---:|---:|---|
| **G2** | F01–F05, F08–F12, F17, F18 | 108 | **1,296** | 30 | all, pre-retention |
| NEG (E6-facing, carried but not an E4f endpoint) | F07, F19A/B/C | 108 | 216 | 30 | all |

Truth families actually present in the G2 stratum, enumerated from `registry.CASE_FAMILIES`
and `generator._law` (read, not assumed):

| Truth family | Conditions | Worlds |
|---|---|---:|
| `mass_affine_descriptor` | F01,F02,F03,F04,F05,F08,F11,F12,F17 | 972 |
| `mass_saturating_descriptor` | F09 | 108 |
| `mass_interaction` | F10 | 108 |
| `mass_exponential_descriptor` | F18 | 108 |
| `mass_power` | *(none — F07 is in the NEG stratum)* | 0 |

**This matters and is recorded before execution:** the G2 stratum contains **no
`mass_power` world**, so E4f measures classifier behaviour on four of the five truth
families. `mass_power` appears only as a *possible discovered label*, never as a truth
label to be recovered. Any claim about `mass_power` recovery is out of E4f's scope by
construction.

### 4.2 Admissibility preconditions on the surface — hard, checked before any scoring

P1–P7 are **preconditions, not findings.** Failure of any one is `E4F_VOID_SURFACE_
PRECONDITION_FAILURE` (§13). They exist so that no weaker corpus can be substituted later.

| # | Precondition |
|---|---|
| **P1** | Every row carries `admissibility = "DECISION_ADMISSIBLE"` at the **row** level (`befca0d` §2.3; calibration prereg §15) |
| **P2** | The full **28-field schema** is present **from inception**, verified by the frozen hard-coded field-list validator. No back-fill, no imputation, no post-seal write (`befca0d` §2.4; ratification §8 / D6) |
| **P3** | The surface passed its own qualification and its routing gate certified a route **to E4f** (decision tree §B.6 entry: `LOST_IN_CROSS_SEED` dominant), with the routing seal hash-chained before this protocol executes |
| **P4** | The surface's own retention-identity control passed: the instrumented engine's `argmax(score)` row is byte-identical to the frozen production path's, for every seed (`befca0d` §2.5.1) |
| **P5** | Every world's **design matrix is regenerable byte-identically** from `generate_case(case_id)` with a matching `content_hash`. Required only by K2, which consumes covariates; verified for **all** worlds so K2 cannot be scored on a subset chosen after the fact |
| **P6** | Every world's `TruthRecord` carries `symbolic_truth_kind == "defined"`, a `mathematical_family` in `TRUTH_FAMILIES`, and populated `coefficients` / `exponents` — the inputs §5 needs to construct negatives |
| **P7** | The **replay control of §9 passes.** K0+V0 reproduces the surface's own sealed attribution exactly |

**Explicitly excluded populations, by name, so no substitution is possible:**

- **E2a** (`results/e2/run_x86_e2a_v1`) — ratified **invalidated as a calibration surface**
  (ratification §7 / D5). May be used only as an engineering DEV set (§7.1), never as
  `P_G2`.
- **E2b** (the Held-out full-front replay) — `admissibility = "DECISION_INADMISSIBLE"`
  at the row level (`befca0d` §2.3). Its use as `P_G2` is rejected by the static citation
  checker, not by convention.
- Any corpus lacking the 28-field schema from inception (D6).

### 4.3 What "case" means

For E4f-ii and for every G2 endpoint, the unit is the **world** (one `case_id` × one
replicate), which carries 30 seeds and yields exactly one `CrossSeedSelection`. For E4f-i's
primary metric the unit is the **negative control** (§5). For coverage the unit is the
**distinct front row**, with the per-world rate as the paired unit (§7.3).

---

## 5. THE ADVERSARIAL NEGATIVE POPULATION `P_NEG`

### 5.1 Status: the construction is frozen, the population is not

`befca0d` §3.6 declares the *construction* verbatim:

> *"Negative controls are constructed by structurally perturbing the truth expression:
> substitute `correlated_distractor` for `descriptor`, substitute `descriptor2` for
> `descriptor`, and replace the descriptor factor with a constant of matched magnitude.
> These are known not-truth-equivalent by construction."*

It declares **no population, no count, no applicability rule, and no operational meaning for
"matched magnitude."** Those are supplied here, prospectively, and are flagged as free
parameters FP-1 and FP-2 in §15.

### 5.2 Enumeration — deterministic, exhaustive, no RNG

For **every** world `w ∈ P_G2`, take its own frozen symbolic truth template
`TruthRecord.descriptor_relationship` (equivalently `g_definition`) and substitute **that
world's own** `coefficients` and `exponents`. Apply each of the three declared perturbations:

| Tag | Perturbation | Definition |
|---|---|---|
| **N1** | `descriptor → correlated_distractor` | textual substitution on the primitive symbol `descriptor` only; `descriptor2` is never touched |
| **N2** | `descriptor → descriptor2` | same, collapsing the pair onto one symbol |
| **N3** | descriptor factor → constant of matched magnitude | the maximal sub-expression that (a) is a multiplicative factor of the law and (b) contains `descriptor`, replaced by the arithmetic mean of that sub-expression evaluated on **that world's own compound table** |

`|P_NEG| = 1,296 × 3 = 3,888`, of which `DEV_ARM` holds 1,944 and `EVAL_ARM` holds 1,944
(§7.1). All three perturbations apply to all four truth families present in `P_G2`
(verified: each family's law contains a `descriptor`-bearing multiplicative factor).

**Why N3's constant is the mean and not something else (derivation, FP-2).** "Matched
magnitude" is undefined in frozen text. The mean of the replaced factor over the world's own
covariates is the **unique** constant that leaves the law's expectation on that world
unchanged, so it is the only reading of "matched" that requires no new number and no new
distributional assumption. Median and the raw coefficient value were both considered and
rejected: the median matches no conserved quantity, and the coefficient is not the factor's
magnitude. The chosen constant is recomputed deterministically per world from sealed inputs;
it is not a protocol constant.

### 5.3 Not-truth-equivalence, verified rather than asserted

Verified at authorship by executing `g2_contract.extract_effective_support` on the twelve
(4 families × {truth, N1, N2}) constructed strings:

| Truth family | truth support | N1 support | N2 support |
|---|---|---|---|
| `mass_affine_descriptor` | `{mass, descriptor}` | `{mass, correlated_distractor}` | `{mass, descriptor2}` |
| `mass_saturating_descriptor` | `{mass, descriptor}` | `{mass, correlated_distractor}` | `{mass, descriptor2}` |
| `mass_interaction` | `{mass, descriptor, descriptor2}` | `{mass, correlated_distractor, descriptor2}` | `{mass, descriptor2}` |
| `mass_exponential_descriptor` | `{mass, descriptor}` | `{mass, correlated_distractor}` | `{mass, descriptor2}` |

Every N1 and N2 changes the effective support, so none is truth-equivalent. N3 removes
`descriptor` from the support entirely, and the planted coefficient is drawn from
`rng.uniform(0.25, 0.55)` (`generator._law` line 155) and is therefore never zero, so N3's
law is never equal to its truth law. **Not-truth-equivalence is a theorem of the
construction, not an empirical claim.** No family label was computed during this check.

### 5.4 Mandatory positive control on the negative constructor

The **unperturbed** truth expression of every world is also scored, under every arm, as a
positive control. **K0 must return the world's truth family on the unperturbed truth
expression for every world.** Any failure is an instrument defect in the negative
constructor or in the substitution of `coefficients`/`exponents` — *not* a finding about any
arm — and is `E4F_VOID_NEGATIVE_CONSTRUCTOR_DEFECT` (§13). This is FP-7: the frozen text
does not require it; it is added because a negative-control set whose positive control fails
measures nothing.

---

## 6. OPERATIONAL DEFINITIONS OF THE ARMS

### 6.1 K1 — canonical structural normal form (zero new numbers)

K1 = `classify_discovered_family` applied to a canonicalised expression, where the
canonicalisation is **the frozen `identity_contract` pipeline reused verbatim**:
`_positivize` → `_rationalize_floats` → `together` → `cancel` → `as_content_primitive`,
including its own deterministic `sp.count_ops(expr) > _MAX_OPS_BEFORE_FALLBACK = 400`
fallback. The **classification semantics are byte-unchanged**: the same `_contains_product`,
`_contains_exp_of`, `_contains_saturating`, `_is_linear_in`, `_fallback_classify` predicates
run, on a different normal form. No new operator, no new pattern, no new number.

**Rationale for reusing that pipeline rather than writing one:** it is the only
canonicalisation in the repository that is already frozen, already proven total and
deterministic, already carries a deterministic (not wall-clock) cost fallback, and is
already the control relation V0. Writing a second one would introduce free parameters for no
gain. Recorded as FP-3 because "a canonical structural normal form" in frozen text does not
name this pipeline.

### 6.2 K2 — behavioural identification (zero new numbers)

For a candidate expression `e` and world `w`:

1. Evaluate `e` on `w`'s regenerated design matrix (P5) over the five `GRAMMAR_PRIMITIVES`
   columns in `CALIBRATION_COVARIATE_ORDER`. Non-finite or non-evaluable ⟹ `UNRESOLVED`,
   never a label.
2. Fit each of the **five** truth-family parametric forms of `generator._law` — verbatim,
   with their own free coefficients — to `ŷ = e(X)` by ordinary least squares, using a
   deterministic solver with **fixed initialisation, fixed tolerances, and no RNG**. Any
   form that fails to converge yields `+∞` residual sum of squares for that form only.
3. Label by **minimum RSS**. **Ties, and only exact-float ties, are broken toward the
   fewest-free-parameter form, then toward `TRUTH_FAMILIES` declaration order.**
4. If **all five** forms fail to converge, or the evaluation in step 1 fails ⟹ `UNRESOLVED`.

**No tolerance, no "near-tie" band, no improvement threshold is introduced, deliberately.**
The five forms are nested (`mass_affine_descriptor` is a limiting case of both
`mass_saturating_descriptor` and `mass_exponential_descriptor`), so minimum-RSS labelling is
**structurally biased toward the richer form**. That bias is not a defect to be patched
here; it is precisely the mechanism `befca0d` §3.6 predicts when it calls K2 *"the arm with
the highest false-labelling risk."* Introducing a tolerance to suppress it would be
inventing a free number **in the direction that flatters the arm**, which is the exact
prohibited move. The bias is left in, measured by `false_labelling_rate`, and pre-recorded
as my expected failure mechanism (§16).

### 6.3 V1 — `(effective_support, discovered_family)`

Grouping key = the ordered pair `(extract_effective_support(e), classify_discovered_family(e))`,
with `None` on either component forming its **own** key rather than merging into any other
(fail-closed, matching `rc5_selection.parse_production_candidate`'s *"routes the candidate to
its conservative singleton class"*). Everything downstream of the key —
`group_and_select`'s largest-class-wins, lowest-seed-ordinal tie-break, representative rule,
and `selection_count` — is **unchanged**.

### 6.4 V2 — algebraic equivalence, and the transitivity problem

`discovery.equivalence.algebraically_equivalent(a, b)` returns `bool | None`; it is a
**partial, pairwise** predicate and is **not guaranteed transitive**, so it does not by
itself induce a partition. The grouping procedure is therefore specified explicitly (FP-4):

> Build an undirected graph on the ≤ 30 retained candidates of a world, in seed-ordinal
> order. Add an edge `(a, b)` **iff** `algebraically_equivalent(a, b) is True`. `None`
> (undecided, including the deterministic `count_ops(a)+count_ops(b) > SIMPLIFY_TIMEOUT_TERMS
> = 400` bound) adds **no edge** — fail-closed, the conservative direction. Classes are the
> **connected components**, which are deterministic and order-independent.

**Disclosed consequence, recorded before execution:** connected-component closure can merge
two candidates that were never directly certified equivalent. That is a coarsening the
pairwise oracle did not authorise, and it is exactly the kind of merge `k_inflation` exists
to catch. The count of such transitive-only merges is a **mandatory reported diagnostic**.

### 6.5 Containment check — mandatory, reported, not assumed

For every world and every arm `V ∈ {V1, V2}`, report the number of V0-classes that V
**splits** (i.e. whose members land in ≥ 2 V-classes). The design intends V1 and V2 to be
**coarsenings** of V0, and Lemma K (§8.3) depends on it. A non-zero split count does not
void the run; it is a first-class instrument finding about the frozen identity contract and
is reported as such.

---

## 7. DESIGN: SPLIT, UNITS, PAIRING

### 7.1 DEV / EVAL — REUSED VERBATIM, not invented here

From `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` §26(3), which already declares the
split **for exactly this purpose** (*"`R*` and `V*` are selected on DEV_ARM … and measured
on EVAL_ARM"*), deterministic by replicate index, no RNG:

```
DEV_ARM  = replicates r000 .. r053   ( 648 G2 worlds ; 1,944 negatives )
EVAL_ARM = replicates r054 .. r107   ( 648 G2 worlds ; 1,944 negatives )
```

A negative inherits its parent world's replicate index, so `P_NEG` splits identically and no
world contributes to both halves.

- **Engineering DEV** = the sealed, invalidated E2a corpus (calibration prereg §26(1)).
  All E4f analysis code — the negative constructor, the three classifiers, the three voting
  relations, the bounded-determinacy driver, the bootstrap harness — is developed, debugged
  and **hash-frozen against E2a** before a single row of `P_G2` is read. Zero leakage: E2a
  is barred from licensing anything.
- **Arm-internal choices** (none are declared open in this protocol; if an implementation
  discovers one, it is resolved on `DEV_ARM` and recorded in the tuning ledger).
- **Every gate in §8 is evaluated on `EVAL_ARM`, exactly once. There is no second look.**

### 7.2 Pairing — the structural fact this design exploits

**Every arm re-scores the same fronts.** K0, K1, K2 label the *same* front rows and the
*same* negatives; V0, V1, V2 group the *same* 30 retained candidates of the *same* worlds.
The comparison is therefore **paired at the row / negative / world level**, and every
statistic below is paired. An unpaired two-sample test on these data would discard the
pairing and is prohibited.

### 7.3 Unit of analysis per metric

| Metric | Unit | Paired across |
|---|---|---|
| `false_labelling_rate` | one adversarial negative | arms K, same negative |
| `coverage` | one distinct front row; aggregated to a per-world rate for the paired interval | arms K, same row |
| `k_inflation` (reported) and `false_stabilisation_rate` (gating) | one world | arms V, same world |
| G2 case success | one world | arms, same world |

---

## 8. THE ACCEPTANCE PREDICATE

### 8.0 The design constraint, stated so a reviewer can attack it directly

Frozen authority requires that `false_labelling_rate` stay *"below its pre-declared
ceiling"* and `k_inflation` *"within its ceiling"*, and **declares no number for either**.
Supplying a number now would be an absolute threshold chosen by taste, and it is the single
move the governance record names as the highest-leverage cheat available.

**This protocol supplies no absolute number. It replaces both ceilings with a
control-relative non-inferiority predicate**, which is available *because the frozen design
already mandates K0 and V0 as control arms*. The ceiling is the control's own value,
measured on the same data, in the same run, by the same code. There is nothing left to
choose.

### 8.1 Estimator and interval — the general form

For arms `A` (treatment) and `C` (control) and a binary harm indicator `H(·)` on a paired
population of size `N`:

```
b = #{ i : H_A(i) = 1  and  H_C(i) = 0 }      "arm-worse discordants"
c = #{ i : H_A(i) = 0  and  H_C(i) = 1 }      "arm-better discordants"
delta_hat = (b - c) / N                        paired risk difference
```

**Interval method: exact conditional McNemar.** Conditional on `n_d = b + c`, under
`H0: p_b = p_c` we have `b ~ Binomial(n_d, 1/2)`. The one-sided exact 95 % upper confidence
bound on `π = p_b / (p_b + p_c)` is the Clopper–Pearson upper limit for `b` successes in
`n_d` trials, and the upper bound on the paired risk difference is

```
UCB_95( delta )  =  ( 2 * CP_upper_95(b ; n_d) - 1 ) * ( n_d / N )
```

with the convention `UCB_95(delta) := 0` **only** in the degenerate case `n_d = 0`, whose
justification is given in §8.2(c). Exact, not asymptotic: `n_d` will be small and normal
approximations are not admissible here. `wilson_lower_95` / `wilson_upper_95` from
`g2_contract` are imported unchanged for the **unpaired descriptive** rates that accompany
every table, never for the paired comparison.

Bootstrap companion, REUSED from `f4c1105` §8: case-level paired bootstrap, `B = 10,000`,
seeded by `derive_seed_v2("bootstrap", <arm_id>)`, resampling **within EVAL_ARM only**,
reported alongside the exact interval. Where the two disagree, **the exact interval
governs**.

### 8.2 The margin is exactly 0, and here is what that means and why it is attainable

The non-inferiority margin is **exactly 0** — strict non-increase — for both harm metrics.
No margin was chosen, derived, or negotiated. The operational form of a margin-0 predicate
requires care, and the care is the point:

**(a) Why "`UCB_95(delta) ≤ 0`" alone is unattainable in principle, and therefore is not the
predicate.** For any interval procedure with correct one-sided coverage `1 - α`, if the true
difference `δ = 0` then `P(UCB_95 ≥ 0) ≥ 1 - α`, so `P(UCB_95 < 0) ≤ α = 0.05`. A criterion
that an arm *exactly as safe as the control* passes with probability ≤ 0.05 is not a
non-inferiority test; it is a superiority test wearing one's name, and it would reject the
one arm the frozen adoption rule most wants to be able to adopt — *"among those [that hold
false labelling], the highest coverage wins"* — whenever that arm ties the control on
safety. **This is the "unattainable in principle" demonstration the margin-0 default asks
for, and it rules out the confidence-bound-only form, not the margin.**

**(b) The predicate that keeps margin 0 and is attainable: paired census dominance.**
`P_NEG` is **exhaustively enumerated, deterministically constructed, and scored by
deterministic functions.** On the population in hand there is no sampling error at all: the
paired outcome of every negative is a fact, not an estimate. Margin-0 non-increase on that
population is therefore expressible **exactly**:

```
b = 0
```

i.e. `H_A(i) ≤ H_C(i)` for **every** `i`. This is strict non-increase, per item, at margin
exactly 0, with no free number and no interval needed to state it. An arm identical to the
control passes. An arm strictly better passes. An arm that introduces even one new false
label on one enumerated, deterministically-constructed negative fails.

**(c) Where the one-sided interval then does real work.** `b = 0` is a statement about the
1,944 EVAL negatives in hand; the worlds behind them were drawn by the generator's RNG, so
the negatives are a sample from a super-population. The exact interval quantifies the
extrapolation, and is **reported with every arm** in exactly one of three forms:

| Observed | Interval statement | Reading |
|---|---|---|
| `b = 0, c = 0` | The two arms are the **same function** on `P_NEG`. `δ_N = 0` **exactly, as an identity, not an inference.** The residual extrapolation risk is the exact one-sided bound `p_b ≤ 1 - 0.05^(1/N)` (rule of three; `= 0.00154` at `N = 1,944`), reported, never used to reject | non-inferior on the population; extrapolation bounded and disclosed |
| `b = 0, c ≥ 1` | `CP_upper_95(0 ; n_d)` gives `UCB_95(δ) < 0` for `n_d ≥ 1`. **Strict non-increase certified by the one-sided interval** | non-inferior, and certified superior on harm |
| `b ≥ 1` | **FAIL.** No interval can rescue it: the arm demonstrably produced a false label the control did not, on an enumerated negative constructed to be not-truth-equivalent | rejected |

**(d) Asymmetric by design, and the asymmetry is the frozen intent.** A single deterministic
counterexample rejects an arm. That is the correct direction for the metric whose named
failure mode is *"Loosen the family classifier until things match"* and whose named risk is
*"`UNEVALUABLE` converted to false `SUCCESS` — the direction that flatters the result."* The
cost is disclosed as FP-5.

### 8.3 `k_inflation` cannot be gated control-relatively, and here is the proof

**Lemma K (monotonicity of `k` under coarsening).** Let `R` and `R'` be equivalence
relations on a world's retained candidates with `R' ⊒ R` (every `R`-class is contained in an
`R'`-class). Then `max_class_size(R') ≥ max_class_size(R)`, because the `R'`-class
containing the `R`-maximal class is a union of `R`-classes including it. Since
`selection_count = winning.size` (`rc5_selection.group_and_select`, line 348), it follows
that

```
Δk(world) = k_V - k_V0  ≥  0     pointwise and deterministically, for every coarsening V.
```

**Corollary.** Any margin-0 control-relative gate on `Δk` — "k_inflation not higher than the
control's" — is satisfiable **only** when `Δk ≡ 0`, i.e. only by an arm that induces exactly
the frozen partition and therefore does nothing. And any non-zero ceiling on `Δk` is a free
absolute number, which is the move this protocol exists to avoid. **Gating on raw `Δk` is
therefore refused, with proof, rather than fudged.** The same corollary applies to every
statistic that is zero-by-construction for the control (e.g. "V0-classes merged by V", or
"cases whose stability gate flips": both are `≥ 0` by Lemma K), so the gating statistic must
be one that is **well-defined and generally non-zero for V0 itself**.

**`k_inflation` is nonetheless computed and reported exactly as frozen text defines it** —
*"change in median class count per case and in `selection_count`"* — as a mandatory
descriptive quantity, per world and per family:

```
k_inflation_selection(world) = k_V - k_V0
k_inflation_classes          = median_w |classes_V0(w)| - median_w |classes_V(w)|
```

Neither gates. Both appear in every table. **This is a disclosed deviation from a literal
reading of frozen text, and it is FP-6.**

### 8.4 The derived gating statistic for E4f-ii: `false_stabilisation_rate`

**Derivation from the code, not from taste.** `selection_count` enters **exactly one**
predicate anywhere in the frozen pipeline: `CrossSeedSelection.stability_gate_passed`, i.e.
`selection_fraction ≥ STABILITY_GATE / STABILITY_DENOMINATOR = 20/30`
(`rc5_selection.py` lines 274–283, importing `structural_acceptance`). Everything else about
`k` is inert. The harm the identity contract was written to prevent, as the decision tree
states it, is *"multi-retention silently weakening the stability gate"* (§B.2) — that is, a
**stable-looking verdict that is not one discovery.** The truth-facing, post-hoc
operationalisation of "not one discovery" that the surface already computes is: the elected
cross-seed representative is not G2-correct. Hence, for **any** voting relation `V`
including `V0`:

```
FS_V(world) = 1  iff  stability_gate_passed(V, world)  AND  NOT g2_correct( representative(V, world) )
false_stabilisation_rate(V) = mean_w FS_V(world)
```

This is defined identically for the control, is generally non-zero for the control, and is
**not monotone in coarseness**: merging can create a spurious stable-but-wrong verdict
(raising it) or let a correct class win (lowering it). Margin-0 control-relative
non-inferiority is therefore attainable in principle, and Lemma K's corollary does not
apply. `g2_correct(representative)` is computed by the byte-unchanged
`classify_support` / `classify_family_match` / `evaluate_g2_event` chain at **K = K0**
(one-factor discipline, §3).

### 8.5 THE ACCEPTANCE PREDICATE, IN FULL

Let `α = 0.05` family-wise, Holm–Bonferroni within each family (REUSED, `f4c1105` §8).
All quantities on `EVAL_ARM`, scored once, at the **worst-case resolution** of every
`UNRESOLVED` outcome (§10.3).

---

**FAMILY i — discovered-family classifier. Comparisons: {K1 vs K0, K2 vs K0}, at V = V0.**
**PRIMARY COMPARISON: K2 vs K0 on `false_labelling_rate`.**

> **Gate G1 — FALSE-LABELLING NON-INCREASE (margin exactly 0).**
> `H_K(n) = 1` iff arm `K` assigns negative `n` the truth family of `n`'s parent world.
> `b_K = #{ n ∈ P_NEG^EVAL : H_K(n) = 1 and H_K0(n) = 0 }` at worst-case resolution.
> **PASS iff `b_K = 0`.** The exact one-sided interval of §8.2(c) is reported for every arm.
> **FAIL ⟹ the arm is DEAD. Its coverage, its `k_inflation` and its G2 effect are reported
> but can license nothing.** (Frozen: *"an arm raises coverage but also raises false
> labelling past the ceiling ⟹ REJECTED"*, decision tree §B.6.)
>
> **Gate G2 — COVERAGE STRICT INCREASE.** Only for arms passing G1.
> `coverage(K) = 1 - (rate of `None` labels)`, with `SIMPLIFY_TIMEOUT` / `UNRESOLVED`
> reported **separately** from genuine non-coverage (`befca0d` §3.6 metric 2, §2.10).
> **PASS iff the paired 95 % lower bound on `coverage(K) - coverage(K0)` exceeds 0**,
> Holm-adjusted across the two comparisons in this family. Bar REUSED verbatim
> (`f4c1105` §6.1; `befca0d` §3.1: *"a Wilson lower bound above 0"*).
> **FAIL ⟹ `NO CHANGE LICENSED` for that arm.** An arm that is safe but buys nothing is not
> adopted.
>
> **Gate G3 — SELECTION AMONG SURVIVORS.** *"Among those, the highest coverage wins"*
> (`befca0d` §3.6). Ties broken by **fewest free parameters, then lowest false structure**
> (`befca0d` §3.1, REUSED verbatim).
>
> **Gate G4 — SAFETY COUPLING (§11).** No arm is adopted on efficacy alone.

**FAMILY ii — voting relation. Comparisons: {V1 vs V0, V2 vs V0}, at K = K0.**

> **Gate H0 — ORDER PRESERVATION.** `false_labelling_rate` and `coverage` are **invariant**
> across V by construction (a voting relation changes no label). This is asserted and
> **verified**: any non-zero difference is an implementation defect, not a finding, and
> voids the run. The frozen metric order is thereby respected, vacuously and checkably,
> before `k_inflation` is read.
>
> **Gate H1 — FALSE-STABILISATION NON-INCREASE (margin exactly 0).**
> `b_V = #{ w ∈ EVAL_ARM : FS_V(w) = 1 and FS_V0(w) = 0 }` at worst-case resolution.
> **PASS iff `b_V = 0`**, with the exact one-sided interval of §8.2(c) reported.
> **FAIL ⟹ the arm is DEAD.** Frozen `k_inflation` is reported either way (§8.3).
>
> **Gate H2 — G2 STRICT IMPROVEMENT.** Only for arms passing H1.
> **PASS iff the exact paired one-sided 95 % lower bound on
> `P(G2 success | V) - P(G2 success | V0)` exceeds 0**, Holm-adjusted across the two
> comparisons. Bar REUSED (`befca0d` §3.1; decision tree §B.6: *"an arm raises G2 AND
> k_inflation stays under its ceiling ⟹ adopt"*).
> **FAIL ⟹ `NO CHANGE LICENSED`.** The frozen standing prior against V1 — *"v1's own
> counterfactual showed V1 recovers 2 cases and loses 3, for a net loss"* — is recorded here
> as a prior, and is **not** allowed to substitute for the measurement.
>
> **Gate H3 — SAFETY COUPLING (§11).**

**Nothing is adopted from the off-diagonal interaction map, under any outcome.**

### 8.6 Multiplicity — family, control, correction, primary

| Question | Answer, and why |
|---|---|
| **Family** | **Two disjoint families of two comparisons**, forced by the frozen one-factor rule (§3). The 3 × 3 = 9-cell grid is **not** the family, because five of its cells are inadmissible for adoption by frozen authority |
| **Control** | K0 in family i; V0 in family ii. Both are frozen v1 settings (`befca0d` §3: *"Frozen v1 setting is always the control arm"*) |
| **Correction** | **Holm–Bonferroni at family-wise `α = 0.05`, within each family.** REUSED from `f4c1105` §8. **Dunnett was considered and rejected**: Dunnett's many-to-one procedure derives its critical values from a common-variance normal model with a known correlation structure among the treatment-vs-control contrasts. Here the endpoints are **exact discrete paired binary** statistics on small discordance counts, where that model does not hold and its critical values are not valid. Holm is valid under **arbitrary** dependence and is exact-p-value compatible, which is what these data are. With only two comparisons per family the power cost of Holm over Dunnett is negligible |
| **Gate G1 / H1** | **No adjustment, and this is a theorem rather than a convention.** `b = 0` is a deterministic census predicate on the population in hand, not a hypothesis test; it has no type-I error to inflate. The accompanying intervals are reported, not gating |
| **Sequential gates** | Gates are applied in the frozen metric order and are **fixed-sequence gatekeeping**: G2 is read **only** for arms passing G1, H2 **only** for arms passing H1. Fixed-sequence testing preserves the family-wise error rate without further adjustment |
| **PRIMARY comparison** | **K2 vs K0 on `false_labelling_rate`.** Designated from frozen text, not preference: `befca0d` §3.6 singles K2 out as *"the arm most likely to close the 34.2 percent unlabelled rate, and also the arm with the highest false-labelling risk, **which is why the metric below is ordered as it is**."* The primary comparison is the one the frozen metric ordering was written for |
| Everything else | Secondary, Holm-adjusted, with unadjusted intervals reported alongside (REUSED, `f4c1105` §8) |

### 8.7 Resolving power, recorded before execution

With the exact one-sided paired binomial and all discordance in one direction, the minimum
certifiable discordance is `n_d` with `0.5^{n_d} ≤ 0.05 ⟹ n_d ≥ 5`; under Holm across two
comparisons the smaller p must clear `0.025`, giving `n_d ≥ 6`. **Gates G2 and H2 therefore
cannot certify any effect supported by fewer than 6 one-directional discordant worlds out of
648.** RC7 is worth ≈ 2/144 ≈ 1.4 % of cases by v1's own measurement, i.e. ≈ 9 worlds at
`n = 648`, **against a counterfactual that lost 3 for every 2 it recovered.** This is
recorded here, before execution, as the arithmetic reason §16 expects Gate H2 to fail. It is
**not** grounds to lower a bar: the standing rule is *"if the design proves underpowered,
raise `n`; do not lower the margin"* (calibration prereg §10), and E4f cannot raise `n`
without new search, which its frozen zero-cost contract forbids. **If that means E4f-ii is
underpowered for its own effect size, that is a finding about E4f-ii, and it is
pre-recorded.**

---

## 9. IDENTITY / REPLAY CONTROL — A HARD PRECONDITION, NOT A DIAGNOSTIC

**The K0 + V0 arm is a free, exact, powerful control, and it is gated on.** It re-computes
what the surface already sealed, so it must reproduce it **exactly**.

REUSED VERBATIM from `befca0d` §2.5.1 / §2.5.3, `f4c1105` §9.1, calibration prereg §28.

| ID | Control | Bar |
|---|---|---|
| **C-1** | K0's `discovered_family`, `support_status_vs_truth`, `family_status_vs_truth`, `g2_correct` for **every persisted front row** | **Byte-identical** to the surface's sealed post-hoc scoring columns |
| **C-2** | V0's `group_and_select` output for **every world**: `selection_count`, winning class `key`, `representative.expression_string`, `distinct_expression_strings`, `distinct_coefficient_vectors`, `voting_seeds` | **Byte-identical** to the sealed values |
| **C-3** | The K0+V0 four-way attribution and the G2 case-success count | **Exactly** the surface's sealed counts |
| **C-4** | Retention identity: the `argmax(score)` row used by E4f is the surface's own `retained_by_argmax_score` row | **Every seed, every world.** *"Instrumentation that changes the search is not instrumentation"* |
| **C-5** | Determinism replay: a pre-declared 30-world subset re-scored twice on this host | Byte-identical, 30/30 |
| **C-6** | Sealed **expression → label** table (§10.2): labels are a pure function of the expression string, hashed and committed, so cross-architecture parity is a hash comparison rather than a re-run | 0 mismatches, by construction |

**Any discrepancy in C-1…C-4 is a defect in the E4f implementation, not a finding, and
blocks every result.** Terminal `E4F_VOID_REPLAY_FAILURE`. It may **never** be reported as
"E4f revises the surface's attribution."

**Artifact reconciliation.** SHA-256 manifest for every produced artifact, verified after
writing; `git status` clean on all pre-existing sealed evidence; an explicit recorded
statement that **no sealed evidence was modified**.

---

## 10. INVALID / UNRESOLVED HANDLING, AND THE NO-WALL-CLOCK RULE

### 10.1 The governing rule

> **NO WALL-CLOCK CAP, MEMORY CAP, WORKER COUNT, HOST LOAD, CPU MODEL OR CONCURRENCY LEVEL
> MAY DECIDE A SCIENTIFIC LABEL ANYWHERE IN THIS PROTOCOL.**

`SIMPLIFY_TIMEOUT_SECONDS = 5` is **retired as a classification rule** and is not used
anywhere in E4f. Its documented root-cause finding stands: *"the same unmodified classifier
assigns a different scientific label to the same expression purely as a function of host
speed"* (`NEW_CLOUD_HOST_PARITY_FAILED`, calibration prereg §25). E4f is a re-scoring
protocol whose entire output is labels, so it is the experiment most exposed to that defect
and the one where it must not recur.

### 10.2 The determinacy bound — all six conditions, REUSED

Executed through the machinery of `scripts/e2b_bounded_determinacy_evaluator.py`
(hostile-audited in the sealed Gate 1 adjudication), with the calibration prereg §25.1
conditions applied unchanged:

1. `g2_contract.py` and the classification **semantics** are **byte-unchanged**; only the
   control flow around unresolved outcomes differs.
2. A label or class is emitted **only when it is invariant over every resolution of every
   unresolved input**; monotonicity reduces the enumeration to the extremes.
3. Inputs that are **decisive** under that enumeration are **escalated to completion, not
   guessed**.
4. A residual undecidable unit is emitted as explicit `INDETERMINATE`, never folded, with
   the pre-declared bar **`INDETERMINATE == 0`** above which the run is VOID.
5. The implementation is validated against **uncapped ground truth** on a pre-declared
   sample with a frozen **100 %** pass bar. Precedent: 101/101 at Gate 1.
6. The correction is **hash-frozen before any E4f record is produced** and applies
   identically to every arm and both sweeps.

**Two-tier cost budget, REUSED from calibration prereg §25.2:**

- **Tier 1 — CPU time, never wall clock.** `time.process_time` budget of **60 s per distinct
  expression** (DERIVED there as 12 × the retired 5 s, expressed in CPU time so it is not a
  function of load or co-tenancy). It is a **cost** bound only; exceeding it yields
  `UNRESOLVED`, **never a label**.
- **Tier 2 — uncapped escalation** of any expression still unresolved **and decisive**.
- The cap exception derives from **`BaseException`**, deliberately, so `g2_contract`'s seven
  `except Exception: return None` handlers cannot swallow it and silently convert a cost
  bound into `SUPPORT_UNRESOLVED → not-correct`.
- **Sealed expression → label table.** Labels are computed once, escalated to completion,
  hashed and committed. Scoring is then a lookup, so the label is a pure function of the
  expression string.
- **Deterministic, host-invariant bounds are used in preference wherever the frozen code
  already has one**: `identity_contract._MAX_OPS_BEFORE_FALLBACK = 400` (K1, V0) and
  `equivalence.SIMPLIFY_TIMEOUT_TERMS = 400` (V2) are `count_ops` bounds, not timers, and are
  reused unchanged. K2's fits carry **iteration-count** limits, not time limits.

**Implementation substrate, named so it is not reinvented.** The sealed expression → label
table is `src/muru/v2_calibration/e2_rescue_v2/classify_cache.py`, whose keying discipline
is already justified by the fact that `e2_classify.classify_expression` is a **pure function
of `expression_string` alone**; the minimal-work driver is `lazy_classify.py`, which is
sound **only under a determinacy bound** and not under a wall-clock cap (calibration prereg
§17). **No E4f implementation exists at the freeze commit** — `grep -rl 'E4[Ff]'` over
`src/` and `scripts/` returns only `routing_lock.py` and two unrelated delta scripts — which
is a further, mechanical confirmation that this document precedes every E4f result.

### 10.3 How `UNRESOLVED` propagates into every rate — bounds, not point estimates

Every rate in §8 is computed as an **interval over all consistent resolutions**, and **the
acceptance predicate must hold for every consistent resolution.** Operationally this is the
worst-case assignment for the treatment arm:

| Quantity | `UNRESOLVED` on the **treatment** arm | `UNRESOLVED` on the **control** arm |
|---|---|---|
| `H(n)` for Gate G1 (false labelling) | counted as **1** (a false label) | counted as **0** (not a false label) |
| `H(w)` for Gate H1 (false stabilisation) | counted as **1** | counted as **0** |
| coverage numerator (Gate G2) | counted as **not covered** | counted as **covered** |
| G2 success (Gate H2) | counted as **failure** | counted as **success** |

so that every gate is evaluated against the treatment arm's **most favourable-to-rejection**
resolution and the control's **most favourable-to-the-control** resolution. Both extremes
are additionally reported for every table, exactly as the Gate 1 adjudication reported its
`2^4` enumeration, so the sensitivity of every verdict to unresolved inputs is visible.

### 10.4 Complete disposition table (declared before execution, with denominator effects)

| Category | Treatment |
|---|---|
| `UNRESOLVED` (cost bound reached, before escalation) | **Its own state.** Never folded, never imputed, never dropped, never defaulted. Enters via §10.3 bounds |
| `INDETERMINATE` (still not invariant after uncapped escalation) | **Its own state**, counted and sealed. `INDETERMINATE > 0 ⟹ VOID` |
| `parse_ok = false` | **`INCORRECT` / not-a-label.** Deterministic, host-invariant, already the frozen semantics. **Not** `UNRESOLVED` |
| `classify_discovered_family` returns `None` | **Non-coverage.** A genuine, deterministic, frozen outcome. Reported separately from `UNRESOLVED` (`befca0d` §2.10 requires exactly this separation, because v1's 34.2 % `None` rate is *"currently indistinguishable between 'the classifier does not cover this form' and 'simplify gave up'"*) |
| `FAMILY_AMBIGUOUS` | Its own state. **Not** a false label (it asserts nothing), **not** coverage. Counted and reported |
| `invalid_fraction > MAX_INVALID_FRACTION = 0.005` | Excluded by the frozen rule (`befca0d` §3.4). REUSED |
| A world missing from the surface | **Fails precondition P2/P7.** Never imputed. E4f cannot regenerate it (zero-search contract), so a gap is a VOID condition, not a smaller denominator |
| Denominators | Fixed before execution: `N_NEG_EVAL = 1,944`, `N_G2_EVAL = 648`. `INDETERMINATE` units are reported **separately** and never folded into any rate |

---

## 11. SAFETY COUPLING — NO ARM IS ADOPTED ON EFFICACY ALONE

**Passing every gate in §8 makes an arm `EFFICACY_ADMISSIBLE`. It does not adopt it.**

`befca0d` §3 is binding: *"Every arm reports its G2 metric **and** its false-structure metric
from E6 in the same table. Reporting a G2 gain without its safety cost is not permitted."*
The decision tree §3 makes E6 a **veto** that runs against every candidate change as it
becomes a candidate, on **≥ 100 evaluable safety opportunities**, with the only numeric
safety ceiling in the corpus: **unsafe structural acceptance `Wilson upper ≤ 0.15` ⟹
survives; `> 0.15` ⟹ VETO regardless of G2 benefit** (decision tree §A.2 lines 139–140,
verified by direct read).

Therefore:

- Every E4f table reports `false_structure_rate` on the surface's **NEG stratum** (216
  worlds: F07 mass-only truth, F19A/B/C nulls), per arm, alongside every G2 quantity. A
  table omitting it is non-compliant.
- **No E4f terminal adopts anything.** The most an arm can reach is
  `E4F_*_ADMISSIBLE_PENDING_E6_<arm>` (§13).
- **E6 is not pre-judged here.** This protocol does not assert that any arm will or will not
  clear 0.15, does not assert that E6 is currently executable, and does not import E6's
  ceiling into any E4f gate. It records only that E6 clearance is **necessary** and that E4f
  clearance is **not sufficient**.
- The E6 circular dependency is disclosed: `SYNTHESIS_DECISION_RECORD.md` records that *"if
  E6 cannot supply a ceiling at decision time, every licence is conditional and
  non-executable."* If E6 has not run when E4f completes, the terminal is
  `E4F_*_ADMISSIBLE_PENDING_E6_<arm>` and it **stays** there. That is not a failure of E4f.

---

## 12. FREEZE PROCEDURE

1. **Freeze commit.** This document, the acceptance predicate, the gate order, the negative
   constructor, the schema validator's hard-coded field list, the terminal table and **all
   analysis code** are committed, and their SHA-256 hashes recorded in a manifest. The
   freeze commit must be a **strict ancestor** of the first E4f data commit, verified by
   `git merge-base --is-ancestor` and by re-verifying every recorded hash. The
   results-blind ancestor at authorship is `119ba265e16d2fed04cc332b879803b407562a05`.
2. **Tuning ledger.** A ledger of every parameter changed after this freeze, with reason and
   evidence consulted, is registered at the freeze commit. It **must be empty at execution
   time.** A non-empty ledger **voids the run** (§13).
3. **Analysis code hash-frozen against the E2a engineering DEV set** (§7.1) before the first
   `P_G2` row is read.
4. **Surface count: exactly one.** E4f is executed against exactly one qualified surface.
   `EVAL_ARM` is scored exactly once.
5. **Order seals.** Gate G1/H1 verdicts are hashed and appended to the hash-chained event log
   before Gates G2/H2 are computed, so the sequential-gate order is auditable rather than
   asserted.
6. **Post-execution reconciliation** per §9.

---

## 13. TERMINAL STATES

**Exhaustive and mutually exclusive by construction.** The outcome is either **one** global
terminal from set **T-G** (which pre-empts both sweeps), or an **ordered pair**
`(t_i, t_ii)` with `t_i` drawn from **T-I** and `t_ii` from **T-II**, each of which is
exhaustive and mutually exclusive within itself. Names are written so that **the name states
the outcome**, never its opposite and never a euphemism.

**T-G — global, pre-emptive (exactly one may fire; if any fires, no sweep terminal is
emitted):**

| Terminal | Meaning |
|---|---|
| `E4F_NOT_ENTERED_NO_ROUTE` | No qualified surface certified a route to E4f. This protocol is not executed. **The default state at the freeze commit, and the expected one** |
| `E4F_VOID_SURFACE_PRECONDITION_FAILURE` | One of P1–P7 (§4.2) fails |
| `E4F_VOID_REPLAY_FAILURE` | K0+V0 does not reproduce the sealed attribution byte-exactly (§9 C-1…C-4). An implementation defect, **never** a finding about the surface |
| `E4F_VOID_NEGATIVE_CONSTRUCTOR_DEFECT` | The §5.4 positive control fails: K0 does not return the truth family on an unperturbed truth expression |
| `E4F_VOID_INSTRUMENT_INDETERMINATE` | `INDETERMINATE > 0` after uncapped escalation. The G2 contract is not decidable at finite cost on this population — a finding about the **contract** |
| `E4F_VOID_COST_CONTRACT_BREACH` | The implementation invoked the discovery engine. E4f's frozen cost is 0 new search |
| `E4F_VOID_TUNING_LEDGER_NONEMPTY` | A parameter changed after the freeze commit |
| `E4F_VOID_ORDER_INVARIANCE_BROKEN` | Gate H0 fails: a voting relation changed a label. Implementation defect |

**T-I — E4f-i, discovered-family classifier (exactly one):**

| Terminal | Meaning |
|---|---|
| `E4F_I_ALL_ARMS_REJECTED_FOR_FALSE_LABELLING` | Both K1 and K2 fail Gate G1. The classifier arms introduce false family labels on adversarial negatives the control does not. **RC5's risk realised.** No classifier change licensed |
| `E4F_I_SAFE_ARMS_RAISE_NO_COVERAGE` | ≥ 1 arm passes G1; none passes G2. The safe arms buy nothing measurable. No classifier change licensed |
| `E4F_I_CLASSIFIER_EFFICACY_ADMISSIBLE_PENDING_E6_<arm>` | One arm passes G1, G2 and wins G3. **Efficacy-admissible only. Not adopted.** Adoption requires E6 clearance at `Wilson upper ≤ 0.15` on ≥ 100 opportunities (§11) |

**T-II — E4f-ii, voting relation (exactly one):**

| Terminal | Meaning |
|---|---|
| `E4F_II_ALL_ARMS_REJECTED_FOR_FALSE_STABILISATION` | Both V1 and V2 fail Gate H1. Coarsening bought stable-looking verdicts on wrong discoveries. **Exactly the harm the identity contract was written to prevent.** No voting change licensed |
| `E4F_II_SAFE_ARMS_RAISE_NO_G2` | ≥ 1 arm passes H1; none passes H2. Includes the case where V1 reproduces v1's own counterfactual (recovers some, loses more). No voting change licensed |
| `E4F_II_VOTING_EFFICACY_ADMISSIBLE_PENDING_E6_<arm>` | One arm passes H1 and H2. **Efficacy-admissible only. Not adopted.** |

**Note on naming, recorded deliberately.** A prior protocol in this programme was found by
hostile review to carry *"a terminal state whose own gloss inverts its meaning"*
(`DINST_HOSTILE_REVIEW.md`). Every terminal above is named for what **is true when it
fires**: `..._REJECTED_FOR_FALSE_LABELLING` fires when arms were rejected for false
labelling; `..._EFFICACY_ADMISSIBLE_PENDING_E6` fires when efficacy is admissible and E6 is
pending. **No terminal's name asserts a licence, because no E4f terminal grants one.**

---

## 14. THRESHOLD INVENTORY — EVERY NUMBER IN THIS PROTOCOL

**Reused verbatim from frozen authority (citation verified by direct read):**

| Value | Meaning | Source |
|---|---|---|
| `K0`, `V0` as controls | the frozen v1 setting is always the control arm | `befca0d` §3, §3.6 |
| metric order FL → coverage → `k_inflation` → G2 | gate order | `REMEDIATION_EXPERIMENT_PLAN`:316; `befca0d` §3.6 |
| `0` new search | E4f cost contract | `REMEDIATION_EXPERIMENT_PLAN`:348; `befca0d` §3.6 |
| N1/N2/N3 perturbation forms | negative-control construction | `befca0d` §3.6 metric 1 |
| `30` | seeds per world | `rc5_seeds.A35_SEEDS_PER_CASE`; `befca0d` §2.5 control 2 |
| `20/30` | stability gate; the sole consumer of `selection_count` | `structural_acceptance.STABILITY_GATE` — imported, not restated |
| `0.005` | `MAX_INVALID_FRACTION` | `befca0d` §3.4 |
| `400` | `_MAX_OPS_BEFORE_FALLBACK` (K1, V0) and `SIMPLIFY_TIMEOUT_TERMS` (V2) — deterministic `count_ops` bounds, **not timers** | `identity_contract.py`:639; `equivalence.py`:35 |
| paired 95 % lower bound `> 0` | improvement bar, Gates G2 and H2 | `befca0d` §3.1; `f4c1105` §6.1 |
| `α = 0.05`, Holm–Bonferroni | family-wise multiplicity | `f4c1105` §8 |
| `B = 10,000`, `derive_seed_v2("bootstrap", ·)` | bootstrap companion | `f4c1105` §8 |
| 95 % Wilson | descriptive unpaired intervals only | `g2_contract.wilson_*` — imported |
| fewest free parameters, then lowest false structure | adoption tie-break, Gate G3 | `befca0d` §3.1 |
| `Wilson upper ≤ 0.15` on `≥ 100` opportunities | **E6** safety ceiling, referenced not applied | decision tree §A.2, §3 |
| 28-field schema; row-level `admissibility` | surface preconditions P1–P2 | `befca0d` §2.3, §2.4 |
| `1,296` G2 / `216` NEG / `108` replicates | population | calibration prereg §5, §10 |
| `r000–r053` / `r054–r107` | DEV/EVAL split | calibration prereg §26(3) |
| `60 s` CPU-time tier-1 budget; two-tier escalation; `BaseException` cap; sealed label table | cost bounds, never labels | calibration prereg §25.2 |
| `INDETERMINATE == 0`; `100 %` uncapped-validation bar | determinacy bars | calibration prereg §25.1 |

**Derived, with the derivation shown inline:**

| Value | Meaning | Derivation |
|---|---|---|
| **margin `= 0`** | non-inferiority margin for both harm metrics | §8.2. Not chosen: it is the strict-non-increase limit. The confidence-bound-only form of margin 0 is shown *unattainable in principle* (§8.2(a)) and replaced by the paired census-dominance form `b = 0`, which is exactly margin 0 and is attainable |
| `b = 0` | Gate G1 and Gate H1 predicate | §8.2(b). `P_NEG` and `P_G2` are exhaustively enumerated and deterministically scored, so per-item paired dominance is an exact statement about the population in hand |
| `1 - 0.05^(1/N)` | reported extrapolation bound when `b = c = 0` | §8.2(c). Exact one-sided Clopper–Pearson upper limit for 0 successes; `= 0.00154` at `N = 1,944`. **Reported, never gating** |
| `false_stabilisation_rate` | the gating operationalisation of the frozen `k_inflation` ceiling | §8.3 Lemma K proves raw `Δk ≥ 0` deterministically for any coarsening, so no control-relative margin-0 gate on `Δk` exists; §8.4 derives the replacement from the fact that `selection_count` enters exactly one predicate in the frozen code |
| `n_d ≥ 6` | minimum certifiable one-directional discordance under Holm | §8.7. `0.5^{n_d} ≤ 0.025` |
| `|P_NEG| = 3,888` | negative population size | §5.2. `1,296 × 3`, exhaustive over worlds × declared perturbations; no sampling, no RNG |
| N3's constant `= mean of the replaced factor on the world's own compounds` | "matched magnitude" | §5.2. The unique constant preserving the law's expectation on that world's covariates; requires no new number |

**Newly introduced magnitudes: ZERO.**
No absolute ceiling, no margin, no tolerance, no power level, and no sample size is
introduced by this protocol. Every threshold is either reused, or is the value `0`, or is
computed from the data by a rule fixed here. The free parameters this protocol does
introduce are **structural, not numeric**, and are enumerated in §15.

---

## 15. FREE PARAMETERS — THE HOSTILE-REVIEW SURFACE

**This is the section a hostile reviewer will attack first, and it is written for that
purpose.** Every choice below was forced, is disclosed, and is stated with the alternative
that was rejected. None is numeric.

| # | Free parameter | Why it could not be avoided | Alternatives considered and rejected | Direction of risk |
|---|---|---|---|---|
| **FP-1** | **The adversarial-negative population.** `befca0d` declares three perturbation *forms* and no population, count, or applicability rule | `false_labelling_rate` is the primary metric; it is a rate; a rate needs a denominator, and none exists in frozen text | (a) a hand-picked adversarial set — rejected: selectable after the fact; (b) negatives only for families where they seem hard — rejected: selection on expected difficulty; (c) sampling a subset — rejected: introduces an RNG and a size | Exhaustive enumeration over all worlds × all three declared forms is the **only** choice with no selection step. Residual risk: the negative set tests three specific perturbations and generalises no further, and I say so rather than implying broader coverage |
| **FP-2** | **"constant of matched magnitude" for N3** | Frozen text uses the phrase and never defines it | median (matches no conserved quantity); the planted coefficient (not the factor's magnitude); a fixed constant (a new number) | The mean is the unique reading that preserves the law's expectation on the world's own covariates and introduces no protocol constant. Recomputed per world from sealed inputs |
| **FP-3** | **K1's "canonical structural normal form" is `identity_contract`'s pipeline** | Frozen text names a property, not a procedure; a procedure is required to execute | Writing a new normal form — rejected: every step would be a new free parameter; `sympy.simplify` alone — rejected: not canonical and unbounded | Reusing an already-frozen, already-total, already-deterministic pipeline with a deterministic op-count fallback minimises new surface. Risk: K1 is then partly a test of that pipeline, which I state rather than hide |
| **FP-4** | **V2's connected-component closure, with `None` = no edge** | `algebraically_equivalent` is a **partial and not-provably-transitive** predicate; it does not induce a partition, and grouping requires one | (a) `None` = edge — rejected: fails closed in the *coarsening* direction, which is the direction under suspicion; (b) clique-only grouping — rejected: order-dependent, not deterministic; (c) declaring V2 unimplementable — rejected: it is a frozen arm | Closure can merge candidates never directly certified equivalent. Disclosed, counted, and reported as a mandatory diagnostic (§6.4) |
| **FP-5** | **Per-item census dominance (`b = 0`) as the operational form of margin 0** | The confidence-bound form of margin 0 is provably unattainable for a truly-equal arm (§8.2(a)); some operational form is required | (a) a positive margin — rejected: any value is a free absolute number, the prohibited move; (b) harm-exclusion only ("not certified worse") — rejected: accepts on absence of evidence; (c) equivalence testing (TOST) — rejected: requires an equivalence bound, i.e. a free number | One deterministic counterexample rejects an arm. That is severe, and it is the correct severity for the metric whose named failure mode is *"loosen the classifier until things match"*. A reviewer who thinks it too severe is asking for a positive margin, and must then supply its derivation |
| **FP-6** | **Gating on `false_stabilisation_rate` instead of on frozen `k_inflation`** | Lemma K (§8.3) proves the frozen quantity is monotone in coarseness, so **no** control-relative margin-0 gate on it can exist, and any positive ceiling is a free number | (a) an absolute `k_inflation` ceiling — rejected as the prohibited move; (b) `Δk ≤ 0` — rejected: provably rejects every non-trivial arm; (c) declaring E4f-ii ungateable — rejected: a frozen arm with no criterion is worse than a derived one | **This is the largest deviation in the document.** Frozen `k_inflation` is still computed and reported in both its declared components; only the *gate* differs, and the gate is derived from the fact that `selection_count` enters exactly one predicate in the frozen code. If the protocol owner rejects this substitution, the honest fallback is terminal `E4F_NOT_ENTERED_NO_ROUTE`, not an invented ceiling |
| **FP-7** | **The §5.4 positive control on the negative constructor** | Not required by frozen text; added because a negative set whose positive control fails measures nothing | omitting it — rejected: a silent construction bug would masquerade as an arm result | Adds a VOID condition, i.e. it can only stop the protocol, never license anything |
| **FP-8** | **Designating K2 vs K0 on `false_labelling_rate` as the single primary comparison** | Multiplicity control needs a primary; frozen text implies but does not designate one | K1 as primary — rejected: `befca0d` §3.6 singles out K2 explicitly as the highest-risk arm and says the metric order exists *for it*; no primary — rejected: leaves all four comparisons co-equal and weakens the family | The designation makes the arm most likely to fail the primary gate the one the design is pointed at, which is the conservative direction |
| **FP-9** | **K2's tie rule (exact-float ties → fewest parameters → declaration order) and the deliberate absence of a fit tolerance** | "label by best fit" is undefined for nested models, where the richer form always fits at least as well | An RSS-improvement tolerance — rejected: a new free number, and one that would suppress K2's bias **in the direction that flatters K2**; an information criterion — rejected: imports a penalty constant | K2 is left structurally biased toward richer families. That bias is the hypothesis under test, not a defect to be patched, and §16 pre-records it as my expected failure mechanism |
| **FP-10** | **Treating the off-diagonal 2 × 2 interaction cells as `DESCRIPTIVE_ONLY`** | The frozen one-factor rule forbids adopting them; but reporting them is informative | Not computing them — rejected: hides a known interaction; treating them as adoptable — rejected: violates `befca0d` §3 | Purely a reporting choice, enforced by the citation checker |

**What I could NOT avoid introducing and would flag first if I were the reviewer:** FP-6.
It is a substitution of a derived statistic for a frozen one. Its justification is a proof
(Lemma K) plus a code-reading (`selection_count` has exactly one consumer), and both are
checkable in minutes. If either fails, the correct action is to stop E4f-ii, not to widen
anything.

---

## 16. PRE-RECORDED EXPECTED OUTCOME

Recorded before execution so the record shows the design was not chosen for its answer. No
part of it was consulted in fixing any gate, and every gate above is stated in a form that
would fire against my expectation without amendment.

**Most likely outcome overall: `E4F_NOT_ENTERED_NO_ROUTE` (~75 %).** E4f requires a
qualified calibration surface whose routing certifies `LOST_IN_CROSS_SEED` as dominant.
Both standing hostile reviews at HEAD `119ba26` argue the calibration protocol's licensing
terminals are unreachable, and the decision tree's own note is that *"RC7 is worth 2 cases
and its naive fix was net negative. Nothing on this branch can rescue G2 on its own."* I
expect this document to be a completed obligation that is never executed, and I am writing
it anyway, because the obligation is to remove the cheat, not to reach a licence.

**Conditional on execution:**

| Sweep | Prediction | Mechanism |
|---|---|---|
| **E4f-i, Gate G1 (PRIMARY)** | **K2 FAILS (`b_K2 ≥ 1`), ~70 %.** K1 passes (`b_K1 = 0`), ~80 % | K2 labels by minimum RSS over nested forms fitted to the candidate's own predictions. On N1 negatives (`descriptor → correlated_distractor`) the substituted variable is correlated with `descriptor` **by construction** (family F12 exists precisely to plant that correlation), so the `mass_affine_descriptor` form will fit the perturbed candidate's outputs closely and K2 will return the truth family on an expression whose support does not contain `descriptor`. K0 returns `None` on those same strings — with `has_descriptor = False` and `has_descriptor2 = False`, `classify_discovered_family` matches neither the interaction branch nor the mass+descriptor branch and falls through to the terminal `return None` at `g2_contract.py:260`, never reaching a family test — so the discordance is one-directional |
| **E4f-i, Gate G2** | **K1 fails to raise coverage with LCB > 0, ~60 %** | The frozen record attributes the 34.2 % `None` rate to a mixture of genuine non-coverage and `SIMPLIFY_TIMEOUT` that has *never been separated*. Canonicalisation before pattern matching addresses neither the `not has_mass` early return nor the timeout share |
| **Predicted `t_i`** | `E4F_I_SAFE_ARMS_RAISE_NO_COVERAGE` (~45 %), then `E4F_I_ALL_ARMS_REJECTED_FOR_FALSE_LABELLING` (~20 %), then `E4F_I_CLASSIFIER_EFFICACY_ADMISSIBLE_PENDING_E6_K1` (~25 %), VOID (~10 %) | |
| **E4f-ii, Gate H1** | **V2 passes (`b_V2 = 0`), ~65 %; V1 passes, ~55 %** | Merging genuinely equivalent forms should not create new stable-but-wrong verdicts. V1's `(support, family)` key merges all `None`-family candidates sharing a support, which is where I expect its discordance if it has any |
| **E4f-ii, Gate H2** | **Both fail, ~75 %** | §8.7's arithmetic: the certifiable minimum is 6 one-directional discordant worlds out of 648; RC7's own measured size is ≈ 1.4 % of cases **against a counterfactual that lost 3 for every 2 recovered**. I expect the discordance to be roughly balanced or net negative |
| **Predicted `t_ii`** | `E4F_II_SAFE_ARMS_RAISE_NO_G2` (~60 %), then `E4F_II_ALL_ARMS_REJECTED_FOR_FALSE_STABILISATION` (~20 %), then `E4F_II_VOTING_EFFICACY_ADMISSIBLE_PENDING_E6_V2` (~10 %), VOID (~10 %) | |

**Frozen `k_inflation`, reported not gated: I expect `Δk > 0` for both V1 and V2 on most
worlds**, which is Lemma K restated as a prediction and is therefore *not* evidence for
anything. If `Δk ≤ 0` is ever observed for a world, the containment check of §6.5 has failed
and that world's V-partition splits a V0-class — an instrument finding, reported as such.

**Summary: I expect E4f to license nothing on either sweep, and I am preregistering it
anyway.** The value of this document is not the licence it might produce; it is that the
two ceilings the governance record flagged as un-improvisable are now fixed at a commit that
precedes every possible result, in a form that contains no absolute number for anyone to
tune.

**The disclosure that makes this checkable.** The design most likely to deliver an
adoption was available and was rejected: an **absolute** ceiling on `false_labelling_rate`
(the obvious candidate being E6's `0.15`, the only numeric safety ceiling in the corpus,
ported across metrics). It would have been trivially defensible in review, and K2 would
plausibly have cleared it. It was rejected because porting a ceiling across metrics is an
invented number wearing a citation, and because a control-relative predicate makes the
result independent of anyone's taste — **not** because it was expected to fail, but because
it was expected to pass.

---

**TERMINAL STATE OF THIS DOCUMENT: PROTOCOL TEXT, FROZEN, NOT EXECUTED.**
**No surface scored. No negative constructed. No arm evaluated. No re-entry licensed.**
**E4f remains NON-EXECUTABLE. What changes at this commit is only that its two absent
ceilings are no longer absent, and were fixed results-blind.**
