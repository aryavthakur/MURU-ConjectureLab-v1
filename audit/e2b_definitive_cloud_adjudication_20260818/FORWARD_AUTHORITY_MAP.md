# FORWARD AUTHORITY MAP
## What frozen prospective authority does and does not specify for the path after Gate 1 fails

**Author:** AGENT_5 (GOVERNANCE_FORWARD_PATH)
**Date:** 2026-08-18
**Repo:** `/home/aryav_thakur/MURU-ConjectureLab-v1`, branch `claude/e2b-definitive-cloud-adjudication`
**Method:** read-only trace of git-committed authority. Every claim below carries a file path,
a commit (where the file is not at HEAD), and a verbatim quotation. No scientific compute was
run. No file was modified except this one.

**Reading key used throughout:**

- **(a) FROZEN** — the authority text says this literally.
- **(b) READING** — a defensible inference from frozen text, marked as inference.
- **(c) UNSPECIFIED** — frozen authority genuinely does not say; naming it here is the point.

---

## 0. Executive answer (detail and evidence follow)

| Question | Answer | Class |
|---|---|---|
| What repair family is now primary? | **E4f** (`classifier / canonicalization` + cross-seed voting relation) is the *nominated* family for `LOST_IN_CROSS_SEED` dominance — but it is **not currently authorized**, for three independent frozen reasons. | (a) nomination FROZEN; (b) non-authorization is FROZEN on all three grounds |
| What previous repair is suspended? | **E4a** (retention policy) explicitly, and **every E4 ablation** — E4a, E4b, E4c, E4d, E4e, E4f — collectively. | (a) FROZEN |
| Which experiments remain authorized? | **E0, E1, E3, E6** are untouched by the hook. **E5** is not literally named by the hook but is gated by E3 and informed by E4d. **All of E4 is suspended.** | (a) FROZEN for E0/E1/E3/E6/E4; (c) E5's status under the hook is UNSPECIFIED |
| Do M2 or M3 map to the new primary failure mode? | **No.** M1/M2/M3 are A1 adequacy-ladder detector contrasts on the G1 branch (energy-response deviation models). They have no defined relation to `NEVER_ON_FRONT` / `LOST_IN_RETENTION` / `LOST_IN_CROSS_SEED`, which are G2 symbolic-recovery stages. | (a) FROZEN |
| Is a new experiment required? | **Yes, at minimum one.** The mandated post-failure action ("republish the root-cause attribution first") has **no frozen protocol anywhere**. E4f additionally has no operational freeze. | (c) UNSPECIFIED — this is the finding |
| Is protocol-owner action required? | **Yes.** A genuine, non-manufactured `PROTOCOL_OWNER_DECISION_REQUIRED` boundary exists. | (b) READING from (a)+(c) |

---

## 1. The Gate 1 falsification hook, recovered in full

### 1.0 Provenance correction (material)

`MURU_V2_E4A_BLOCKER_RESOLUTION_AUDIT.md` (committed at `62b4b55`) records, at its
lines 23 and 29:

> "…is not present in, and not recoverable from, anything reachable from…"
> | Named authority commit | `git cat-file -t f4c1105` | "Not a valid object name" |

and `MURU_V2_E4A_PROTOCOL_OWNER_DECISION_PACKAGE.md` (uncommitted working material) repeats:

> "**Preregistration**: `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` … is not
> recoverable anywhere on this host or in git history."

**That is false on this host and branch.** `f4c1105` resolves, and
`git show f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`
returns the complete 565-line preregistration. The file was **deleted from the working
tree after `f4c1105`** (`git diff --stat f4c1105 HEAD -- v2_design_reference/` shows
`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md | 565 ---`), along with its
`PROTOCOL.json`, `ANALYSIS_SCHEMA.json`, `E2_INPUT_CONTRACT.json`,
`MANIFEST_TEMPLATE.json`, and `HOSTILE_REVIEW_CHECKLIST.md`. It is fully recoverable.

**Consequence:** every downstream conclusion that rested on "the preregistration is
unrecoverable" (the "materially" threshold being second-hand, R5/R6 arm status being
unknown, k/eps ambiguity) is **resolved by direct recovery**, not by ruling. This is
recorded because it changes what is actually in dispute.

### 1.1 Section 4, verbatim and complete

Source: `git show f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`,
section 4.

> ## 4. Execution trigger (results-blind, mechanical)
>
> This protocol does not execute unconditionally. `MURU_V2_CAUSAL_DECISION_TREE.md`
> section B.1 already froze E4a's licensing gate; this section restates it as an
> executable predicate over E2a's sealed attribution counts, evaluated **once**,
> immediately after E2a seals and before any policy in section 6 is scored.
>
> ```
> Let A, B, C, D, E = case counts of the five stages over all 540 E2a cases.
> Let NONSUCCESS = A + B + C + D.
>
> GATE 1 (falsification hook, checked first, from B.1's first branch):
>     IF E2b's direct measurement contradicts the v1 decomposition's
>     69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
>     tolerance) --
>         THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended
>         per MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9's falsification
>         hook. The non-execution, and the E2a/E2b divergence that caused it,
>         is reported in place of any policy comparison. STOP.
>
> GATE 2 (retention-dominance, B.1's second and fifth branches):
>     IF B is the strict plurality of {A, B, C+D}  -- i.e. B > A AND B > C+D --
>         THEN this protocol EXECUTES. RC3 is confirmed by direct observation;
>         E4a is enabled.
>     ELSE IF P_retain_given_front is near 1 wherever P_front is high (the
>     exoneration condition) --
>         THEN this protocol DOES NOT EXECUTE. RC3 is WITHDRAWN and reported as
>         such; no retention policy is scored. STOP.
>     ELSE IF A is the strict plurality --
>         THEN this protocol DOES NOT EXECUTE. RC4 is confirmed; the next
>         licensed step is E3-gated (E4b/c/d), not this document. STOP.
>     ELSE IF C+D is the strict plurality --
>         THEN this protocol DOES NOT EXECUTE as adoption-relevant; RC7 is
>         larger than v1's 2 cases and E4f (classifier/voting) is the licensed
>         arm. Section 8's C/D metrics are still reported, unchanged, as the
>         diagnostic record E4f will need, but no retention *adoption* decision
>         is made here. STOP for adoption purposes.
>     ELSE (no strict plurality; a tie or a near-uniform split) --
>         THEN this protocol EXECUTES in DIAGNOSTIC-ONLY mode: every policy in
>         section 6 is scored and reported, but section 10's adoption rule is
>         suspended pending a named tie-breaking review, because the frozen
>         decision tree does not cover a non-plurality outcome and inventing a
>         tie-break now, after seeing the counts that produced the tie, would
>         not be results-blind.
> ```
>
> **This is the exact, complete, mechanical trigger.** Nothing about section 6's
> policy definitions, section 7's population split, or section 10's adoption
> rule may be altered by which branch fires -- the *policies* are frozen now,
> before Gate 1 or Gate 2 is evaluated for real; only whether comparison
> proceeds, and whether its result may license adoption, depends on the gate.

### 1.2 Exactly WHICH protocol "does not execute"

The exact sentence is:

> "THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended per
> MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9's falsification hook."

**"this protocol"** is bound unambiguously by the document's own opening
(`f4c1105`, same file, lines 1-20):

> "**This document operationalizes E4a** (`G2_SINGLE_FACTOR_ABLATIONS`, arm a,
> "retention policy")…"

and by section 15:

> ```
> RETENTION REMEDIATION PROTOCOL FROZEN RESULTS-BLIND
> ```

So **(a) FROZEN:** "this protocol" = the **Retention Remediation Protocol = E4a**.
It is *not* the whole remediation plan and *not* the v2 programme.

But the same sentence carries a **second, wider** consequence that is not scoped
to E4a: *"All E4 ablations are suspended."* That is a direct restatement of two
upstream authorities:

`v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.9 (at HEAD, lines 193-199):

> **Falsification hook.** The decomposition predicts, on Held-out, roughly 69
> retention-class and 57 generation-class cases. If E2b's direct measurement
> contradicts that split materially, the decomposition's attribution is wrong and
> **every E4 ablation is suspended** until the contradiction is resolved. This is
> the strongest single check in the plan, because it tests the diagnosis that the
> whole remediation rests on.

`v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` section B.1 (at HEAD, lines 186-191):

> ```
>  |-- E2b (Held-out replay) contradicts the decomposition's 69/57 split materially
>  |     => the diagnosis the whole remediation rests on is wrong.
>  |     CHANGE: SUSPEND ALL E4 ABLATIONS until the contradiction is resolved.
>  |             Republish the root-cause attribution first.
> ```

`v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` E2 register (at HEAD, line 228-229):

> "**Falsification hook:** if E2b's direct measurement materially contradicts the
> decomposition's 69/57 retention-versus-generation split, all E4 ablations are
> suspended until the contradiction is resolved."

**(a) FROZEN, summarised:** the literal referent of "does not execute" is **E4a**.
The literal scope of *suspension* is **all six E4 arms: E4a, E4b, E4c, E4d, E4e, E4f.**
The literal scope of the mandated *remedy* is **"Republish the root-cause attribution first."**

### 1.3 The one place the tree describes the resulting terminal state

`v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` section 4 ("Terminal leaves"), line 400:

> | E1 (d), or E2b contradicting the decomposition | No v2 architecture is proposed at all. The adequacy statistic is redesigned from first principles, or the failure decomposition is republished first. |

**(a) FROZEN.** This is the *only* forward-looking terminal statement in the entire
frozen corpus that is conditioned on "E2b contradicting the decomposition." It says
what may **not** happen ("No v2 architecture is proposed at all") and names one
prerequisite ("the failure decomposition is republished first"). It specifies **no
experiment, no protocol, and no procedure** for that republication.

---

## 2. Section 2 of the preregistration — the A-E first-loss taxonomy, verbatim

Source: `git show f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`,
section 2.

> ## 2. The A-E first-loss taxonomy (inherited, not redefined)
>
> `MURU_V2_E2_PREDECLARATION.md` section 6 already froze this taxonomy
> mechanically, against real pipeline functions, before any E2a world was built.
> It is authority here and is reproduced, not altered:
>
> | Stage | Meaning | Design-doc class | Frozen condition (verbatim from the predeclaration) |
> |---|---|---|---|
> | **A** | truth absent from the candidate pool | `NEVER_ON_FRONT` | `correct_on_front(seed)` false for all 30 seeds |
> | **B** | truth available, lost within-seed | `LOST_IN_RETENTION` | `correct_on_front(seed)` true for >=1 seed, `retained_correct(seed)` false for all 30 |
> | **C** | survives within-seed, lost cross-seed | `LOST_IN_CROSS_SEED` (aggregation half) | representative not `g2_correct` **and** not `algebraically_equivalent` to truth -- a genuinely incorrect class won the vote |
> | **D** | survives aggregation, lost to equivalence/classification | `LOST_IN_CROSS_SEED` (classifier half) | representative not `g2_correct` **but** *is* `algebraically_equivalent` to truth -- the truth-blind classifier failed to recognize a structurally correct winner |
> | **E** | final recovery | `SUCCESS` | representative is itself `g2_correct` |
>
> `correct_on_front` and `retained_correct` are evaluated per seed against that
> world's own `g2_contract.evaluate_g2_event`. The C/D split is the one
> refinement the predeclaration adds beyond the design doc's own four-way
> partition, using `discovery.equivalence.algebraically_equivalent` (up to a
> positive multiplicative constant, the same tolerance the frozen recovery
> hierarchy already uses) as a classifier-independent ground-truth check. Every
> case receives exactly one label, in strict A-B-(E-or-D-or-C) decision order;
> the partition is exhaustive and non-overlapping by construction.
>
> **What this protocol changes about the taxonomy: nothing.** It recomputes A
> through E once per candidate retention policy, holding the front fixed. Stage
> A is **policy-invariant** -- the front is a property of the frozen search, not
> of retention -- so `|A|` and the eligible pool `|B|+|C|+|D|+|E|` are identical
> across every policy compared below. Only the B/{C,D,E} split, and the
> C/D/E split within it, can move.

The upstream authority it inherits from, `v2_design_reference/MURU_V2_E2_PREDECLARATION.md`
section 6 (at HEAD), states the same mapping and adds the operative definitions:

> | Design doc class | A-E refinement |
> |---|---|
> | `NEVER_ON_FRONT` | **A** |
> | `LOST_IN_RETENTION` | **B** |
> | `LOST_IN_CROSS_SEED` | **C** (aggregation) or **D** (classifier/equivalence) |
> | `SUCCESS` | **E** |

and

> - **C -- lost in cross-seed aggregation**: the representative is not
>   algebraically equivalent to the truth either -- a genuinely incorrect class
>   won the cross-seed vote over the seed(s) that did retain a correct candidate.

### 2.1 An ambiguity the hook itself carries — (c) UNSPECIFIED

The hook compares a **four-way front-based partition** against a **five-class v1
first-failure-point decomposition**. The frozen corpus never states the mapping.

v1's decomposition (`v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.md`, lines 210-217):

> | First irreversible failure point | Cases | Root-cause class |
> |---|---|---|
> | `REPRESENTATION` (grammar cannot express the family) | 12 | GRAMMAR_REPRESENTABILITY |
> | `GENERATION` (no seed matched support or family) | 45 | SEARCH_GENERATION_FAILURE |
> | `GENERATION_FAMILY` (support reached, family never) | 12 | SEARCH_GENERATION_FAILURE |
> | `SELECTION_WITHIN_SEED_RETENTION` | 69 | SELECTION_FAILURE |
> | `SELECTION_CROSS_SEED_IDENTITY` | 2 | CANONICALIZATION_EQUIVALENCE_FAILURE |
> | `NONE` (success) | 4 | NONE_SUCCESS |

So "69" = `SELECTION_WITHIN_SEED_RETENTION`, and "57" = `GENERATION` (45) +
`GENERATION_FAMILY` (12), **excluding** `GRAMMAR_REPRESENTABILITY` (12).

**(c) UNSPECIFIED:** no frozen document states whether the 12
`GRAMMAR_REPRESENTABILITY` cases should be counted into the direct measurement's
"generation" bucket. A grammar-inexpressible truth is, by construction, `NEVER_ON_FRONT`.
If those 12 are counted in, the direct generation figure moves from 14 toward the
14-vs-69 comparison territory; **it does not change the verdict** (14+12 = 26 vs 57 is
still a 31-case deviation, and retention 55 vs 69 is a 14-case deviation regardless),
but the ambiguity is real and should be recorded rather than silently resolved.

**(b) READING:** under every plausible mapping, both deviations exceed the frozen
10-case tolerance. The Gate 1 = FAIL verdict is robust to the mapping ambiguity.

The tolerance itself is pinned, not vague. `v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md`
section 5, line 466:

> | PE2-4 | E2b reproduces the decomposition's retention-versus-generation split to within 10 cases of 69/57. |

The preregistration's "more than 10 cases (PE2-4's own tolerance)" therefore binds the
word "materially" to an exact number, recovered from primary authority — **not** second-hand.

---

## 3. What E4a is, exactly

**(a) FROZEN.** E4a = `G2_SINGLE_FACTOR_ABLATIONS`, arm a, "retention policy."

`v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.1 (at HEAD):

> ### 3.1 E4a: retention policy
>
> *Post-hoc on E2's persisted fronts. Zero additional search.*
>
> | Arm | Rule | Free parameters |
> |---|---|---|
> | R0 | `argmax(score)` | 0 (control, frozen v1) |
> | R1 | `argmax(valid_r2)` | 0 |
> | R2 | top-`k` by `score`, `k` in {1, 2, 3, 5} | 1 |
> | R3 | whole front, seed votes for its best member by `valid_r2` | 0 |
> | R4 | accuracy-thresholded parsimony: among rows with `valid_r2 >= max(valid_r2) - eps`, take the lowest complexity; `eps` in {0.001, 0.005, 0.02} | 1 |

The preregistration at `f4c1105` section 5 registers two further arms, **R5** (Pareto-
nondominated retention, 0 free params) and **R6** (top-3 by score restricted to rows whose
`template_key` recurs in the top-3 of >= 2 of the other 29 seeds, 0 free params, constants
frozen directly per section 5.2 rather than DEV-tuned). R3 is registered as an
**oracle/control excluded from adoption** (section 5.1).

**What E4a was designed to test** (`f4c1105` section 1):

> "given the front E2a already captured (frozen, unchanged, not re-searched), **how
> much correct symbolic signal exists after generation, and which retention
> architecture recovers the most of it without paying for that recovery in
> parsimony, specificity, or cross-seed stability.**"

**Authorizing conditions.** Two gates in strict order (section 4, quoted in full above):
Gate 1 (E2b falsification hook) then Gate 2 (retention-dominance on E2a's 540 cases).
Prerequisite in the dependency order (`MURU_V2_CAUSAL_DECISION_TREE.md` section 0):

> ```
>  +--> E4a retention policy         [needs E2]
> ```

**Gate 2's actual state: LOCKED_EXECUTE_E4A.** Commit `d23d18e` ("x86 E2a sealed"):

> ```
> ROUTING, recomputed from the x86 corpus alone (no historical world merged):
>   A=122  B=196  C=102  D=0  E=119   r_remaining=1
>   branch 1: B > A + r      196 > 123   true
>   branch 1: B > C + D + r  196 > 103   true
>   => LOCKED_EXECUTE_E4A
> ```

and `MURU_V2_E2_ROUTING_LOCK_FREEZE.md` section 4 (committed at `fff660f`):

> "this locks **Gate 2 only**. It says nothing about Gate 1 (the E2b falsification
> hook), which is a separate, sequentially-prior, out-of-scope precondition this
> module cannot resolve from E2a data at any completeness."

**This is load-bearing for everything below.** On the *decision-admissible* surface (E2a,
540 fresh `V2C` worlds), `LOST_IN_RETENTION` **is** the strict plurality — 196, with
margins of 73 and 93. Cross-seed (C+D = 102) is **not** dominant on E2a. The cross-seed
dominance being adjudicated arises **only** on E2b.

---

## 4. What M2 and M3 are — and what they are not

**Task-4 hypothesis tested: "M2/M3 are repair families." That hypothesis is FALSE.**

**(a) FROZEN.** M0/M1/M2/M3 are the **adequacy-ladder alternative models** on the
**A1 / G1 branch** of the benchmark — energy-response deviation models fitted per
compound, nothing to do with G2 symbolic recovery.

`MURU_PAPER_BENCHMARK_METRICS.md` (at HEAD, lines 25-45):

> ## Adequacy endpoint scoring (Amendment A1)
>
> The adequacy ladder compares M0 with M1 (horizontal shape), M2 (high-energy
> vertical/asymptotic), and M3 (low-energy vertical) on the case's 30 test
> compounds. …
>
> | Endpoint | Held-out denominator | Case-level success |
> |---|---:|---|
> | M0 specificity | 164 | adequacy status is `M0_NOT_REJECTED` |
> | M1 sensitivity | 36 | the M1 detector fires |
> | M2 sensitivity | 24 | the M2 detector fires |
> | M3 sensitivity | 24 | the M3 detector fires |
>
> A detector fires only when at least 24 of the 30 test compounds are evaluable
> for that contrast and at least 20 of them are practical wins, where a practical
> win requires the alternative's within-compound leave-one-energy-out MAE to be no
> more than 0.90 of M0's.

Their exact generative forms (`MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md`, lines 99-105, 139):

> | M2 | `a_i + (A_LO - a_i) * S(E / g_i)` | `a_i = A_HI` |
> | M2 | `a_i = clip(mu_inf + A * (descriptor2 - 0.5), 0.03, 0.55)` | `descriptor2` | `0.05` | frozen V1, unchanged |

Their role in the v1 diagnosis (`v2_design_reference/MURU_V1_ROOT_CAUSE_RANKING.md`, lines 41-45):

> "Every one of the 154 is blocked by M3: 127 by M3 alone, 27 by M2 and M3. M1
> never blocks."
> "7,399 of the 8,816 recorded bound contacts (84 percent) are the M3 low-energy
> plateau pinned at its `MU_CEIL` upper bound."

The v2 theory work on them is likewise A1-branch:

- `b98e4d0` — "M2 detectability lower bound: six-energy design is below the frozen
  architecture's requirement, not below the information … The 20-of-30 rule requires
  per-compound efficacy D_REQ = 0.5766."
- `679a7a0` — "M3/Phi bias theory: derive the influence relation, prove the a_lo
  aliasing, construct the orthogonal score … for the frozen M3 target estimator."
- `46e94cb` — "M1 efficient-score theory: derive the replacement adequacy statistic …
  treating M0 as a composite null."

(The corresponding documents — e.g. `MURU_V2_M2_INFORMATION_SCALING_THEORY.md`, named in
`git show c8301a2:MURU_V2_PRE_E6_GOVERNANCE_AMENDMENT.md` AMENDMENT 7 — were also
deleted from the working tree but remain in history.)

**Mapping verdict (a) FROZEN:**

| Failure mode | Branch | Addressed by |
|---|---|---|
| `NEVER_ON_FRONT` (generation) | Branch B, G2 | E3 first, then E4b / E4c / E4d |
| `LOST_IN_RETENTION` (retention) | Branch B, G2 | E4a |
| `LOST_IN_CROSS_SEED` (voting + classifier) | Branch B, G2 | **E4f** |
| M1 / M2 / M3 detector non-firing | **Branch A, G1/G3** | E0, then E1 |

**M2 and M3 map to NONE of the three G2 failure modes.** They are a different
endpoint (G1 adequacy), a different partition of the causal tree (Branch A vs Branch B),
and a different root-cause family (RC1/RC2 vs RC3/RC4/RC7). Any proposal to treat M2 or
M3 as the "new primary repair family" after Gate 1 fails would be a category error against
frozen authority. The `MURU_V2_CAUSAL_DECISION_TREE.md` section 0 dependency order keeps
the branches disjoint:

> ```
> E0  admissible-range provenance
>  |
>  +--> E1  joint evaluability and detector power        [needs E0's ceiling verdict]
>  |
> E3  descriptor identifiability                          [independent, run early]
>  |
> E2  Pareto front instrumentation                        [independent, run early]
> ```

---

## 5. CRITICAL — is there a frozen post-Gate-1-failure contingency?

### 5.1 What the frozen corpus DOES say — (a) FROZEN

Three sentences, and only three, address the state after Gate 1 fails:

1. `MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 2.9 —
   > "**every E4 ablation is suspended** until the contradiction is resolved."
2. `MURU_V2_CAUSAL_DECISION_TREE.md` § B.1 —
   > "CHANGE: SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. Republish the root-cause attribution first."
3. `MURU_V2_CAUSAL_DECISION_TREE.md` § 4, terminal-leaf table —
   > "No v2 architecture is proposed at all. The adequacy statistic is redesigned from first principles, or the failure decomposition is republished first."

A fourth is the preregistration's own restatement (§ 4 Gate 1), which adds a *reporting*
obligation:

> "The non-execution, and the E2a/E2b divergence that caused it, is reported in place
> of any policy comparison. STOP."

The verbs are exhaustively: **suspend, resolve, republish, report, STOP.** There is
**no** "if Gate 1 fails then run X" clause anywhere.

### 5.2 What the frozen corpus does NOT say — (c) UNSPECIFIED

An exhaustive grep of `v2_design_reference/` for suspension / republication / falsification
language returns exactly the lines quoted above and nothing more. Specifically **unspecified**:

1. **No definition of "resolved."** What state discharges "until the contradiction is
   resolved" is nowhere defined. There is no criterion, no adjudicator, no artifact.
2. **No republication protocol.** "Republish the root-cause attribution first" names an
   obligation with **no** preregistered method, population, statistic, freeze discipline,
   or acceptance rule. There is no `MURU_V2_ATTRIBUTION_REPUBLICATION_*` document in any
   commit reachable from any branch.
3. **No decision tree for the post-failure branch.** The tree explicitly disclaims
   coverage of outcomes it did not enumerate — the preregistration itself uses that
   principle for the *tie* case in Gate 2:
   > "because the frozen decision tree does not cover a non-plurality outcome and
   > inventing a tie-break now, after seeing the counts that produced the tie, would
   > not be results-blind."
   The same reasoning applies with full force here: **inventing a post-Gate-1-failure
   route now, after seeing the counts, would not be results-blind.**
4. **No re-licensing route.** Nothing states whether, after a republished attribution,
   E4 arms re-enter via the original Gate 2 predicate, via a new gate, or not at all.

### 5.3 Is any cross-seed experiment prospectively authorized? — E4f, with three blockers

**E4f exists and is the named cross-seed arm. (a) FROZEN.**

`v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 3.6:

> ### 3.6 E4f: family classifier and canonicalization
>
> *Post-hoc on E2's persisted fronts. Zero additional search.*
>
> Two independent sweeps.
>
> **F-i, discovered-family classifier:**
>
> | Arm | Classifier |
> |---|---|
> | K0 | frozen `classify_discovered_family` (control) |
> | K1 | K0 plus a canonical structural normal form before pattern matching |
> | K2 | behavioural identification: fit each of the five truth-family parametric forms to the **candidate's own predicted values** and label by best fit |
>
> **F-ii, cross-seed voting relation:**
>
> | Arm | Grouping key |
> |---|---|
> | V0 | `identity_contract.template_key` (control) |
> | V1 | `(effective_support, discovered_family)`, the pair the endpoint is scored on |
> | V2 | algebraic equivalence under `discovery.equivalence` |
>
> **Metrics, in priority order:**
>
> 1. **`false_labelling_rate`** (primary): fraction of adversarial negative
>    controls that receive the truth family. …
> 2. `coverage`: 1 minus the `None` rate, with `SIMPLIFY_TIMEOUT` reported separately …
> 3. `k_inflation`: change in median class count per case and in `selection_count` …
> 4. G2 case success.
>
> **Decision:** coverage is *not* the adoption criterion. … A classifier arm is
> adopted only if `false_labelling_rate` stays below its pre-declared ceiling; among
> those, the highest coverage wins. A voting arm is adopted only if `k_inflation`
> stays within its ceiling; v1's own counterfactual showed V1 recovers 2 cases and
> loses 3, for a net loss, so V1 carries a specific prior against it.
>
> **Cost:** zero search; 2 CPU-hours of scoring, dominated by K2's per-candidate
> parametric fits.

The licensing route is stated in three places, all conditioned on **E2a**:

`MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 2.9 ("Pre-declared, applied to the E2a attribution"):

> | `LOST_IN_CROSS_SEED` is the largest | RC7 is larger than the 2 cases v1 showed | E4f (canonicalization / voting relation) |

`MURU_V2_CAUSAL_DECISION_TREE.md` § B.1:

> ```
>  |-- LOST_IN_CROSS_SEED dominates
>  |     => RC7 is larger than the 2 cases v1 showed.
>  |     ENABLES: E4f voting-relation arms.
> ```

`f4c1105` § 4, Gate 2 branch 4:

> "ELSE IF C+D is the strict plurality -- THEN this protocol DOES NOT EXECUTE as
> adoption-relevant; RC7 is larger than v1's 2 cases and E4f (classifier/voting) is
> the licensed arm."

**Blocker 1 — Gate 1 suspends E4f too. (a) FROZEN.** E4f *is* an E4 ablation. "All E4
ablations are suspended" / "SUSPEND ALL E4 ABLATIONS" names no exception. The very same
sentence that suspends E4a suspends E4f. The frozen text does not carve E4f out.

**Blocker 2 — E2b cannot license E4f. (a) FROZEN, and this is the sharpest point.**

`MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 2.3:

> **E2b outputs are `DECISION_INADMISSIBLE`.** No v2 threshold, retention rule,
> grammar change, classifier change or benchmark change may be justified by E2b.
> E2b may only corroborate or contradict a conclusion already reached on E2a.
>
> This is enforced mechanically, not by convention:
>
> - every E2b record carries `admissibility = "DECISION_INADMISSIBLE"` at the row level;
> - every proposed v2 design change must cite the experiment IDs supporting it;
> - a static citation checker rejects any change whose supporting set contains an
>   E2b identifier and no E2a identifier.

and `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` § 2.3:

> "A static citation checker rejects any change whose supporting set contains an E2b
> identifier and no decision-admissible identifier. Held-out evidence can corroborate
> a v2 conclusion; it cannot produce one."

The E2b measurement showing `LOST_IN_CROSS_SEED = 71` is therefore **structurally
incapable of licensing E4f**. The governance architecture explicitly grants E2b a
**veto/blocking** power (§ 2.9's hook, § 2.3's "blocks adoption of any E4 conclusion
until explained") but **no licensing power**. The falsification hook is precisely the
one blocking power E2b holds — and it is exercised.

**Blocker 3 — E2a, the only licensing surface, does not show cross-seed dominance.
(a) FROZEN.** Per `d23d18e`: `A=122, B=196, C=102, D=0, E=119`. `C+D = 102 < B = 196`.
Gate 2 on the decision-admissible surface locked to `LOCKED_EXECUTE_E4A`, not to the
cross-seed branch. There is no decision-admissible evidence for cross-seed dominance
anywhere in the frozen record.

**(b) READING:** the three blockers are independent. Removing any one leaves the other
two intact. E4f is *nominated by name* for the cross-seed failure mode, and is *not
authorized* to execute or to license adoption on the present evidence.

### 5.4 Any other prospectively authorized cross-seed experiment?

Exhaustive check of the register (`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` § 3 and
`MURU_V2_CAUSAL_DECISION_TREE.md` § 0):

| ID | Name | Failure mode addressed | Cross-seed? |
|---|---|---|---|
| E0 | `A1_ADMISSIBLE_RANGE_PROVENANCE` | A1 ceiling / clip provenance (G1) | No |
| E1 | `A1_JOINT_EVALUABILITY_POWER` | M1/M2/M3 detector power (G1) | No |
| E2a | `G2_PARETO_INSTRUMENTATION` (fresh) | measurement, no IV | Diagnostic only |
| E2b | same, Held-out replay | `DECISION_INADMISSIBLE` | Diagnostic only |
| E3 | `DESCRIPTOR_IDENTIFIABILITY` | is the target findable at all | No |
| E4a | retention policy | `LOST_IN_RETENTION` | No |
| E4b | search budget | `NEVER_ON_FRONT` | No |
| E4c | objective / parsimony | `NEVER_ON_FRONT` | No |
| E4d | grammar / operators | `NEVER_ON_FRONT` / representability | No |
| E4e | coefficient regime | `engine_inefficiency` | No |
| **E4f** | **classifier / canonicalization + voting** | **`LOST_IN_CROSS_SEED`** | **Yes — the only one** |
| E5 | `F18_EXPONENTIAL_RESOLUTION` | F18 exponential, governance options O1-O7 | No |
| E6 | `FALSE_STRUCTURE_SAFETY_COUNTERWEIGHT` | safety veto against every candidate change | No |

**R1-R6 are not experiments.** They are E4a's within-seed retention *arms* (`f4c1105`
§ 5). **M1/M2/M3 are not experiments.** They are A1 adequacy-ladder alternative models
(§ 4 above). **RC1-RC7 are root causes**, not experiments.

**(a) FROZEN:** **E4f is the unique prospectively registered cross-seed / representative-
selection / voting experiment in the entire frozen corpus.**

---

## 6. Does E4f have complete frozen execution parameters? — mostly NO

**Specified (a) FROZEN:**

- Arms: K0/K1/K2 (classifier sweep), V0/V1/V2 (voting sweep) — `G2_PARETO_STUDY_DESIGN.md` § 3.6.
- Metric priority order: `false_labelling_rate` > `coverage` > `k_inflation` > G2 success.
- Adversarial negative-control *construction*: "substitute `correlated_distractor` for
  `descriptor`, substitute `descriptor2` for `descriptor`, and replace the descriptor
  factor with a constant of matched magnitude."
- Prerequisite: E2 only (`CAUSAL_DECISION_TREE.md` § 0: `+--> E4f classifier / voting [needs E2]`).
- Cost: "zero search; 2 CPU-hours of scoring."
- Decision branches: `CAUSAL_DECISION_TREE.md` § B.6.
- A standing prior against V1: "v1's own counterfactual showed V1 recovers 2 cases and
  loses 3, for a net loss."

**UNSPECIFIED (c) — E4f has NO operational freeze:**

1. **No standalone preregistration.** E4a received one (`f4c1105`: 565 lines plus
   `PROTOCOL.json`, `ANALYSIS_SCHEMA.json`, `E2_INPUT_CONTRACT.json`,
   `MANIFEST_TEMPLATE.json`, `HOSTILE_REVIEW_CHECKLIST.md`). **E4f received none.**
   `git log --all --diff-filter=A` finds no E4f protocol, schema, contract, manifest, or
   checklist in any commit on any branch. E4f appears in exactly four design `.md`
   files and one `.json` register — all at summary level.
2. **No numeric ceiling for the primary metric.** Both § 3.6 and the register say
   `false_labelling_rate` must stay "below its **pre-declared ceiling**" — and that
   ceiling is **never declared anywhere**. Grep across `v2_design_reference/` returns
   only the phrase, never a number. The only numeric ceiling in the corpus is E6's
   `false_structure_rate` at 0.15, which is a *different* metric on a *different*
   population.
3. **No `k_inflation` ceiling.** Same defect: "stays within its ceiling," ceiling never given.
4. **No population declaration.** E4a's preregistration fixes 540 cases with an exact
   `world_ordinal` formula and a stratified 90/450 DEV/EVAL split. E4f has no stated
   population, no split, no development surface for any tuned constant.
5. **No statistical procedure.** No paired test, no bootstrap, no seed derivation, no
   multiplicity control. E4a's § 8 has all four; E4f has none.
6. **No control/replay gate.** E4a has a mandatory R0-reproduces-E2a's-sealed-counts
   replay control (§ 9 item 1). E4f has no analogous V0/K0 identity control specified.

**(b) READING:** E4f is registered at *design* level and is **not executable as frozen
authority stands.** Running it would require writing an operational preregistration — i.e.
authoring new prospective authority — exactly the step `f4c1105` itself performed for E4a
and described as "the missing operational layer."

### 6.1 Architecture neutrality — E4f IS Linux x86_64-runnable

**(a) FROZEN.** Both E4a and E4f are declared zero-search post-hoc re-scorings:

`G2_PARETO_STUDY_DESIGN.md` § 3.6: *"Post-hoc on E2's persisted fronts. Zero additional search."*
`f4c1105` § 9 control 2 makes this structural for E4a:

> "A static check asserts that no function in this protocol's implementation
> imports `rc5_estimate`, `rc5_adapter`, PySR, or Julia -- the search-side
> modules -- so 'zero additional search' is enforced structurally."

**No PySR, no Julia, no macOS/ARM64 dependency.** The macOS/ARM64 constraint applies only
to *reproducing the frozen symbolic search* (E2a/E2b re-runs), not to re-scoring persisted
fronts. Verified on this host:

- **E2b front corpus is complete and local.** `results/e2b_macos_fullfront_replay_20260818/fronts/`
  — 144 case directories, 4,320 front files, 31 MB.
  `audit/e2b_definitive_cloud_adjudication_20260818/FRONT_CORPUS_INTEGRITY.json` reports
  `FRONTS_MISSING: 0`, `SHA256_MISMATCHES: 0`, `FRONTS_TORN: 0`,
  `TOTAL_PARETO_ROWS_FROM_MANIFEST: 51411`, `FRONT_CORPUS_ACCEPTABLE: true`.
  Rows carry `complexity`, `equation`, `loss`, **`score`**, `sympy_format`.

- **E2a corpus is local but SCHEMA-DEFICIENT.** `results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl`
  rows carry:
  `['cell_id','classified','engine_complexity','expression_string','family','front_rank','invalid_fraction','noise_level','regime','replicate','retained_by_argmax_score','seed','seed_ordinal_k','test_r2','valid_r2','world_id']`
  — **no `score` and no `loss` column.** Any arm keyed on `score` (E4a's R0/R2/R6) cannot
  be computed from this corpus as persisted. `retained_by_argmax_score` is a *precomputed
  boolean*, sufficient to reconstruct V0's per-seed vote but **not** sufficient to re-rank.

**(b) READING:** the architecture-neutral surface with full scoring columns is **E2b's**
— the `DECISION_INADMISSIBLE` one. The decision-admissible surface (E2a) is on this host
but lacks the `score` column. That asymmetry is itself a governance hazard: the only
corpus rich enough to run a cross-seed re-scoring today is the one that cannot license
anything.

---

## 7. Task-6 answers, with citations

### 7.1 WHAT REPAIR FAMILY IS NOW PRIMARY (if cross-seed becomes dominant)?

**Nominated: E4f — `classifier / canonicalization` (F-i: K0/K1/K2) and `cross-seed
voting relation` (F-ii: V0/V1/V2). Root cause: RC7,
`CANONICALIZATION_EQUIVALENCE_FAILURE`. Currently NOT AUTHORIZED.**

- Evidence, nomination: `v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` § B.1 (HEAD) —
  *"LOST_IN_CROSS_SEED dominates => RC7 is larger than the 2 cases v1 showed. ENABLES: E4f voting-relation arms."*
- Evidence, non-authorization (1): `MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 2.9 (HEAD) —
  *"every E4 ablation is suspended."* E4f is an E4 ablation.
- Evidence, non-authorization (2): `MURU_V2_G2_PARETO_STUDY_DESIGN.md` § 2.3 (HEAD) —
  *"No v2 threshold, retention rule, grammar change, classifier change or benchmark
  change may be justified by E2b."* The 71-case cross-seed count is an E2b measurement.
- Evidence, non-authorization (3): commit `d23d18e` — E2a's decision-admissible attribution
  is `A=122 B=196 C=102 D=0 E=119`; cross-seed is **not** the plurality on the only surface
  that can license.

**Class: (a) FROZEN for the nomination; (a) FROZEN for all three non-authorization grounds.**

### 7.2 WHAT PREVIOUS REPAIR IS SUSPENDED?

**E4a explicitly; all six E4 arms collectively.**

- `git show f4c1105:…PREREGISTRATION.md` § 4 —
  *"THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended … STOP."*
- `MURU_V2_CAUSAL_DECISION_TREE.md` § B.1 —
  *"CHANGE: SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. Republish the root-cause attribution first."*
- Arms in scope, from `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` § 3 E4 register: E4a
  (retention), E4b (budget), E4c (objective/parsimony), E4d (grammar/operators), E4e
  (coefficient regime), E4f (classifier/voting).

Note that E4a's Gate 2 had already **locked to EXECUTE** (`d23d18e`,
`MURU_V2_E2_ROUTING_LOCK_FREEZE.md` § 1). Gate 1 is sequentially prior and overrides it.

**Class: (a) FROZEN.**

### 7.3 WHICH EXISTING EXPERIMENTS REMAIN AUTHORIZED?

**Unaffected by the hook (a) FROZEN:** **E0**, **E1**, **E3**, **E6**. The hook's scope
is textually "E4 ablations" / "every E4 ablation"; none of these is an E4 arm.

- E3 is independent: `CAUSAL_DECISION_TREE.md` § 0 — *"E3 descriptor identifiability [independent, run early]"*.
- E1 depends on E0, not on E2: *"E1 joint evaluability and detector power [needs E0's ceiling verdict]"*.
- E6 is not a stage: `REMEDIATION_EXPERIMENT_PLAN.md` § 3 E6 — *"Not a terminal stage. E6
  runs against every candidate change from E1, E4 and E5, as that change becomes a candidate."*
  With E4 suspended, E6 has no E4 candidate to run against, but E6 itself is not suspended.

**Suspended (a) FROZEN:** E4a, E4b, E4c, E4d, E4e, E4f.

**(c) UNSPECIFIED — E5.** `CAUSAL_DECISION_TREE.md` § 0 places E5 *"[gated by E3, informed
by E4d]"* and § B.4 treats E4d and E5 jointly. E5 is registered as its own experiment,
not as an E4 arm, so the hook's literal wording does not suspend it — but its
informing input (E4d) is suspended. Frozen authority does not resolve whether E5 may
proceed on E3 alone. **This is a genuine gap, not a reading.**

**A hard ceiling applies regardless (a) FROZEN.** `CAUSAL_DECISION_TREE.md` § 4:

> | E1 (d), or E2b contradicting the decomposition | **No v2 architecture is proposed at all.** … |

So whatever runs, **no v2 architecture proposal is licensed** while the contradiction stands.

### 7.4 DO M2 OR M3 MAP TO THE NEW PRIMARY FAILURE MODE?

**No. Neither maps to any G2 failure mode at all.**

M1/M2/M3 are A1 adequacy-ladder alternative models on the **G1** branch — M1 horizontal
shape, M2 high-energy vertical/asymptotic, M3 low-energy vertical — scored by
leave-one-energy-out MAE across 30 test compounds with a 24-of-30 evaluability and
20-of-30 practical-win rule (`MURU_PAPER_BENCHMARK_METRICS.md`, "Adequacy endpoint scoring
(Amendment A1)", commit `2ac86c5`).

The G2 failure modes (`NEVER_ON_FRONT`, `LOST_IN_RETENTION`, `LOST_IN_CROSS_SEED`) are
symbolic-recovery pipeline stages defined against `g2_contract.evaluate_g2_event`,
`rc5_selection.select_row_label`, and `rc5_selection.group_and_select`
(`MURU_V2_E2_PREDECLARATION.md` § 6). The two branches are kept disjoint by the
causal tree's § 0 dependency order (Branch A: E0 -> E1; Branch B: E3, E2 -> E4).

**Correct mapping for the cross-seed mode is E4f, not M2 or M3.**

**Class: (a) FROZEN.**

### 7.5 IS A NEW EXPERIMENT REQUIRED (not in frozen authority)?

**Yes — at least one, and arguably two.**

**(i) The republication of the root-cause attribution. (c) UNSPECIFIED — REQUIRED.**
Frozen authority *mandates* it —
`CAUSAL_DECISION_TREE.md` § B.1: *"Republish the root-cause attribution first."*
`CAUSAL_DECISION_TREE.md` § 4: *"the failure decomposition is republished first."*
`REMEDIATION_EXPERIMENT_PLAN.md` E2 register: *"H_partial confirmed … forces the
root-cause ranking to be recomputed before E4 proceeds."*
— and **specifies nothing about how**. No protocol, no population, no statistic, no
acceptance rule, no freeze discipline, no adjudicator, no document template exists in any
commit. **This is a mandated action with no frozen procedure. Authoring it is authoring new
prospective authority.**

**(ii) An operational preregistration for E4f. (c) UNSPECIFIED — REQUIRED before E4f
could ever run.** Per § 6 above: no ceiling for `false_labelling_rate`, no ceiling for
`k_inflation`, no population, no DEV/EVAL split, no statistical procedure, no replay
control. Even if the suspension were lifted and a decision-admissible licensing route
existed, E4f is **not executable** as frozen.

**(iii) Not required but blocked either way:** a decision-admissible cross-seed measurement.
E2a's sealed corpus already gives `C+D = 102` and does not support cross-seed dominance;
E2b's 71 cases cannot license. So there is **no frozen route** by which cross-seed becomes
the licensed primary — the licensing predicate (`C+D` strict plurality on E2a) is
measured and **false**.

### 7.6 IS PROTOCOL_OWNER ACTION REQUIRED?

**Yes. A genuine `PROTOCOL_OWNER_DECISION_REQUIRED` boundary exists.**

The boundary is not manufactured, and it is not "the agent is unsure." It is structural:

1. **Frozen authority mandates an action it does not define.** "Republish the root-cause
   attribution first" is an obligation with no protocol. An agent that invents one is
   authoring prospective authority after seeing the results that make it necessary — the
   exact violation the preregistration's own Gate 2 tie-branch names:
   > "inventing a tie-break now, after seeing the counts that produced the tie, would not
   > be results-blind."
2. **The evidence pointing at the new failure mode is structurally unable to license it.**
   E2b is `DECISION_INADMISSIBLE` by mechanical enforcement (§ 2.3, static citation
   checker). Only the protocol owner can decide what an inadmissible-but-decisive
   measurement means for the programme. No agent may relax that.
3. **The decision-admissible surface disagrees with the inadmissible one.** E2a says
   retention dominates (B=196); E2b says cross-seed dominates (71/144). Frozen authority
   anticipates this exactly and calls it disqualifying, not routable:
   `G2_PARETO_STUDY_DESIGN.md` § 2.3 —
   > "**If E2a and E2b disagree**, that is itself a finding and it blocks adoption of any
   > E4 conclusion until explained. Divergence would mean the fresh worlds do not
   > reproduce the Held-out regime, **which invalidates E2a as a calibration surface.**"
   That last clause is the deepest consequence in the record: the divergence puts the
   *calibration surface itself* in question, not merely E4a's execution.
4. **The only unblocked forward action is reporting.** `f4c1105` § 4 —
   > "The non-execution, and the E2a/E2b divergence that caused it, is reported in place
   > of any policy comparison. STOP."

**Legitimate protocol-owner decisions on the table (each requires explicit sign-off; none
is an agent call):**

| # | Decision | Notes |
|---|---|---|
| D1 | Ratify `GATE_1 = FAIL` on the recovered `f4c1105` § 4 text and record the suspension of all six E4 arms | The prereg is recovered (§ 1.0), so "materially = >10 cases" is now **primary**, not second-hand |
| D2 | Rule how the v1 `GRAMMAR_REPRESENTABILITY` (12) cases map into the direct "generation" bucket | § 2.1; does not change the verdict, but should be on the record |
| D3 | Define what "resolved" means and commission a republication protocol for the root-cause attribution | The mandated action with no frozen procedure |
| D4 | Rule on E5's status (E4d-informed but not an E4 arm) | § 7.3, genuine gap |
| D5 | Rule whether E2a remains a valid calibration surface given § 2.3's divergence clause | Deeper than E4a; touches the whole Branch-B programme |
| D6 | If E4f is ever to run: commission its operational preregistration (ceilings, population, split, statistics, replay control), results-blind, before any front is re-scored | § 6 |
| D7 | Note the E2a corpus lacks `score`/`loss`; any score-keyed re-scoring needs corpus regeneration or a schema amendment | § 6.1 |

**Class: (b) READING, built entirely on (a) FROZEN premises and (c) UNSPECIFIED gaps.**

---

## 8. Summary of classification

**(a) What frozen authority explicitly says:**
Gate 1's text and its >10-case tolerance; that "this protocol" = E4a; that ALL E4
ablations are suspended; that the root-cause attribution must be republished first; that
no v2 architecture may be proposed; that E4f is the named cross-seed arm; that E4f is
licensed only by an E2a cross-seed plurality; that E2b is `DECISION_INADMISSIBLE` and can
block but never license; that E2a/E2b divergence "invalidates E2a as a calibration
surface"; that M1/M2/M3 are G1-branch adequacy models; that E2a sealed at
`A=122 B=196 C=102 D=0 E=119` with `LOCKED_EXECUTE_E4A` on Gate 2 only.

**(b) Reasonable readings, flagged as inference:**
That E4f's three blockers are independent; that the Gate 1 = FAIL verdict is robust to the
`GRAMMAR_REPRESENTABILITY` mapping ambiguity; that E4f is not executable as frozen; that a
genuine protocol-owner boundary exists; that the architecture-neutral, scoring-complete
corpus is the inadmissible one.

**(c) Genuinely unspecified — stated precisely:**
1. What "resolved" means for "until the contradiction is resolved."
2. How the root-cause attribution is to be republished — no protocol, population,
   statistic, acceptance rule, freeze discipline, or adjudicator anywhere.
3. Whether/how E4 arms re-enter after a republished attribution.
4. E5's status under a hook whose text names only E4.
5. E4f's `false_labelling_rate` ceiling, `k_inflation` ceiling, population, DEV/EVAL
   split, statistical procedure, and replay control.
6. Whether the 12 `GRAMMAR_REPRESENTABILITY` cases count toward the direct "generation" figure.

**There is NO preregistered contingency, decision tree, or "if Gate 1 fails then X" clause
beyond "suspend, republish, report, STOP." The forward path is genuinely unspecified by
frozen prospective authority.**

---

## 9. Primary sources consulted

| Path | Commit | Role |
|---|---|---|
| `v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` | `f4c1105` (deleted from HEAD, fully recoverable) | Gate 1/Gate 2 executable predicate; A-E taxonomy restatement; R0-R6 |
| `v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` | HEAD | § 2.3 admissibility, § 2.7 attribution, § 2.9 falsification hook, § 3.1 E4a, § 3.6 E4f, § 5 PE2-4 |
| `v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md` | HEAD | § 0 dependency order, § B.1 licensing gate, § B.2 E4a, § B.6 E4f, § 4 terminal leaves, § 6 not-licensed |
| `v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` | HEAD | § 2 governance frame, § 3 E0-E6 register, § 6 open items |
| `v2_design_reference/MURU_V2_E2_PREDECLARATION.md` | HEAD | § 6 A-E taxonomy against real pipeline functions |
| `v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.md` / `.json` | HEAD | the 69/57 split and its five-class origin |
| `v2_design_reference/MURU_V2_E2_ROUTING_LOCK_THEORY.md` | HEAD | Gate-1-needs-E2b; exoneration-branch undefined |
| `MURU_V2_E2_ROUTING_LOCK_FREEZE.md` | `fff660f` | `LOCKED_EXECUTE_E4A`, Gate 2 only |
| `MURU_PAPER_BENCHMARK_METRICS.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md` | HEAD | M0/M1/M2/M3 adequacy-ladder definitions |
| commit `d23d18e` | — | E2a seal: `A=122 B=196 C=102 D=0 E=119` |
| commit `6b18dd8` | — | E2b full-front replay: `GATE_1 = FAIL` |
| commits `b98e4d0`, `679a7a0`, `46e94cb` | — | M2/M3/M1 v2 theory, all A1-branch |
| `results/e2b_macos_fullfront_replay_20260818/fronts/` | `6b18dd8`/`7dfe0d2` | 4,320 fronts with `score`+`loss` |
| `results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl` | `d23d18e` | E2a corpus, **no `score`/`loss` column** |

**Treated as SUPERSEDED working material, not cited as authority:**
`MURU_V2_E4A_PROTOCOL_OWNER_DECISION_PACKAGE.md` (uncommitted),
`MURU_V2_E4A_BLOCKER_RESOLUTION_AUDIT.md` (`62b4b55`) — both of whose
"preregistration unrecoverable" premise is **falsified** by § 1.0 above.

---

**Terminal state of this document:** governance research only. No experiment designed,
authorized, or executed. No frozen document amended. No scientific compute run.
