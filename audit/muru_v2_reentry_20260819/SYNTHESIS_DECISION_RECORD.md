# MURU v2 — SYNTHESIS DECISION RECORD

**Agent:** SYNTHESIS, MURU v2 design council.
**Date:** 2026-08-19. **Branch:** `claude/muru-v2-autonomous-reentry`.
**Nature:** a **prospective post-Gate-1 protocol-owner amendment** created under the
maximum-authorization instruction. **NOT historically preregistered** and must never be
described as such (ratification §10; P2 PM-17).
**Status:** decision record. It licenses no experiment. It fixes, before any new
scientific compute, which design choice was taken and *which numbered rule decided it*.

**Companion document:** `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` (the protocol).
This document is the *reasoning*; that document is the *instrument*. Where they differ,
the protocol governs.

---

## 0. THE ORDERED DECISION RULE (as issued by the protocol owner)

When frozen authority does not uniquely determine a choice, choose the option that, in order:

| # | Criterion |
|---|---|
| **R1** | best preserves the original causal question |
| **R2** | provides the strongest falsification opportunity |
| **R3** | keeps Held-out evidence out of positive licensing |
| **R4** | minimizes free parameters and analyst discretion |
| **R5** | changes the fewest scientific factors |
| **R6** | uses an already frozen metric or definition where applicable |
| **R7** | separates calibration from final evaluation |
| **R8** | minimizes leakage and circularity |
| **R9** | minimizes compute without reducing inferential validity |
| **R10** | is easiest for an independent critic to reproduce |

Ties break to the **lexicographically simplest implementation**, recorded before execution.

**Statement required by the owner, made explicitly:** every contested choice below was
decided by walking this list from R1 downward and stopping at the first rule that
discriminates. Where a lower-numbered rule pointed one way and a higher-numbered rule
pointed the other, **the lower-numbered rule won and the higher-numbered rule is recorded
as overridden**. No choice in this document was made because it was more likely to yield
re-entry. §11 records the outcome I expect, which is not re-entry, precisely so that this
claim is checkable.

---

## 1. WHAT I VERIFIED MYSELF BEFORE RULING

Every number in this section was recomputed by me on this host with
`/home/aryav_thakur/venv/bin/python` against sealed artifacts. Nothing here is taken on
report from P1, P2 or P3.

### 1.1 The instrument defect is real and its exposure is as reported

`lazy_classify.py:186` returns `False` whenever `canonicalization_status != "OK"`, so a
`SIMPLIFY_TIMEOUT` is consumed as evidence of absence. Joining
`results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl` against
`/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3` (frozen classifier version):

```
distinct SIMPLIFY_TIMEOUT expressions : 397 of 52,450 cached
timed-out candidate rows              : 396 of 189,467
worlds with >=1 timed-out front row   : A 73/122 (59.8%) · B 20/196 (10.2%)
                                        C  3/102 ( 2.9%) · E  1/119 ( 0.8%)
```

Confirmed. This matches P2 §1.7 and P3 §5.5 exactly.

### 1.2 **NEW — the correction bound published by P2 and P3 is WRONG, and the error reverses their conclusion**

P2 §1.7 and P3 §5.5 both compute the determinacy bound as

```
A in [49,122]   B in [176,269]   C in [99,195]   E in [119,215]
```

and both conclude from `B_min = 176 < C_max = 195` that **E2a's Gate-2 `B`-plurality is
not invariant** — P2: *"the plurality flips from B to C+D — which is exactly E2b's
finding"*; P3: *"`LOCKED_EXECUTE_E4A` was never determinate."*

**Both are incorrect, by the same mechanism.** They allow a timed-out front row that
resolves to `CORRECT` to carry an `A` world past `B` into `C` or `E`. It cannot, because
the frozen decision sequence in `e2_aggregate.evaluate_world` is

```
if n_correct_on_front == 0:      stage = "A"
elif n_retained_correct == 0:    stage = "B"
```

and `n_retained_correct` reads **only the `argmax(score)`-retained row of each seed**.
Retention is label-independent and is **persisted as a boolean**
(`retained_by_argmax_score`), so no resolution of any unresolved row can change *which*
row is retained. I verified the retained flag is present and unique:

```
189,467 rows · 16,170 (world, seed) pairs · retained rows per (world,seed): {1: 16170}
```

I then joined timeouts against the retained flag and against cache coverage:

| stage | worlds | worlds w/ front timeout | **timeout rows that are RETAINED rows** | retained rows uncached |
|---|---:|---:|---:|---:|
| A | 122 | 73 | **2** | 0 |
| B | 196 | 20 | **0** | 0 |
| C | 102 | 3 | 3 | 0 |
| E | 119 | 1 | 1 | 0 |

**Every retained row of every one of the 539 worlds is determinately labelled** (0 timeouts
and 0 cache misses on retained rows in all 196 `B` worlds). Therefore
`n_retained_correct = 0` is *determinate* for all 196 `B` worlds: **no `B` world can move
anywhere, and `B` can only gain.** Of the 73 affected `A` worlds, 71 have all retained rows
determinately incorrect, so they can move **only to `B`**. The correct bound is

```
A in [49, 122]    B in [196, 267]    C in [99, 104]    E in [119, 124]
```

and the frozen Gate-2 predicate `B > A AND B > C+D` holds at **every** point of it
(`B_min = 196 > A_max = 122` and `> C_max = 104`). I evaluated both extreme resolutions
directly:

```
rho_bot (sealed)                     A=122  B=196  C+D=102  E=119   Gate2 = TRUE
rho_top (all unresolved -> CORRECT)  A= 49  B=267  C+D= 99  E=124   Gate2 = TRUE
```

**E2a's `B`-plurality is invariant over every consistent resolution of its own unresolved
rows.** This is the exact standard the sealed Gate 1 adjudication applied to E2b.

**Governance consequence.** P2's recommended decision **D7** (*"the sealed E2a attribution
is INSTRUMENT-CONTAMINATED; `A = 122` is an upper bound"*) is correct in its first clause
and correct that `A = 122` is an upper bound. Its operative inference — that the
contamination *reverses the plurality onto E2b's answer* — is refuted. I recommend D7 be
issued in the corrected form given in §12.

### 1.3 **NEW — correcting the instrument moves E2a AWAY from E2b, not toward it**

Standardising E2a to the Held-out truth-family mix (affine 108/144, saturating /
interaction / exponential 12/144 each, `mass_power` 0) and evaluating at both resolutions:

| configuration | A | B | C | E | TV vs Held-out | cases/144 | argmax |
|---|---:|---:|---:|---:|---:|---:|:--:|
| raw, sealed instrument, all noise | 0.2263 | 0.3636 | 0.1892 | 0.2208 | 0.3221 | 46.39 | B |
| + composition std, all noise | 0.0941 | 0.4660 | 0.3935 | 0.0463 | 0.1026 | 14.78 | B |
| + composition std, noise-matched | 0.0856 | 0.4560 | 0.4583 | 0.0000 | 0.0741 | 10.67 | **C** |
| + instrument corrected (ρ⊤), all noise | 0.0378 | 0.5208 | 0.3789 | 0.0625 | 0.1736 | **25.00** | B |
| + instrument corrected (ρ⊤), noise-matched | 0.0417 | 0.5000 | 0.4560 | 0.0023 | 0.1181 | **17.00** | B |
| **HELD-OUT TARGET (E2b, sealed, ratified D1)** | 0.0972 | 0.3819 | 0.4931 | 0.0278 | 0 | 0 | C |

Composition alone removes **68.1%** of the divergence pooled over noise and **77.0%**
noise-matched. (P3 §5.3 reports this as *"removes 91%"*; the correct figure is
46.39 → 10.67 = **77.0%**. Arithmetic correction, recorded.)

Correcting the instrument then **increases** the divergence in both conditionings —
14.78 → 25.00 cases, and 10.67 → 17.00 cases — because the corrected mass lands in `B`,
the class where E2a already exceeds Held-out. The direction is certain without escalating
a single expression: by monotonicity the correction can only move mass later, and §1.2
proves that 71 of the 73 movable worlds can move only as far as `B`.

**Ruling on P2's terminal `T-INSTRUMENT` (*"divergence explained as instrument artifact"*):
REFUTED.** It is not merely unproven; the direction of the available correction is the
opposite of the one required. This is recorded here rather than left for discovery.

### 1.4 **NEW — the alleged P1/P3/coordinator disagreement about the argmax flip is resolved: it is a conditioning artifact, and that is the finding**

The coordinator computed standardised `B = 0.466` vs `C+D = 0.394` (no flip). P3 §5.3
computed `B = 0.4560` vs `C = 0.4583` (flip). I reproduced **both, exactly**. They are not
in conflict: the coordinator's is the **all-noise** conditioning (P3's own §2.4 pooled
column reports the identical `0.9059 / 0.4398 / 0.0463`), P3's §5.3 is the
**`noise_sd = 0.02`-only** conditioning.

So the four-way argmax on E2a is a function of **two undeclared analyst degrees of freedom**:

1. whether to condition on noise level — flips `B ↔ C` on a **0.23 pp** margin;
2. whether the wall-clock instrument is corrected — flips `C → B` on a **4.4 pp** margin.

The disagreement is therefore **RESOLVED**, and the resolution is worse for the plurality
than either possibility the coordinator flagged: the plurality is not merely contested,
it is **not a function of the data alone**.

### 1.5 P3's two-sample infeasibility claim: **VERIFIED, and stronger than P3 stated**

Treating the sealed 144-case Held-out corpus as a sample rather than a constant, at
`δ = 10/144`:

| endpoint | `Var_HO = S⁰(1−S⁰)/144` | budget `(δ/(z_{1−α}+z_{1−β}))²` | ratio | verdict |
|---|---:|---:|---:|---|
| `S₁` α=.05 | 6.0951e-4 | 7.8002e-4 | 0.781 | feasible, n ≥ 515 |
| **`S₂` α=.05** | **1.7331e-3** | 7.8002e-4 | **2.222** | **INFEASIBLE AT ANY n** |
| `S₃` α=.05 | 1.8754e-4 | 7.8002e-4 | 0.240 | feasible |
| `S₁` **α=.025** | 6.0951e-4 | **6.1442e-4** | **0.992** | requires **n ≈ 17,876** |
| **`S₂` α=.025** | **1.7331e-3** | 6.1442e-4 | **2.821** | **INFEASIBLE AT ANY n** |

P3's numbers reproduce exactly (n ≥ 515 for `S₁` at α = 0.05 ✓). Two strengthenings P3 did
not state: (i) at **P3's own recommended α = 0.025** the `S₁` component also collapses —
17,876 worlds, ~1,400 CPU-hours; (ii) the maximum attainable power as `n → ∞`, computed
exactly for the TOST at true difference 0, is **1.86%** at α = 0.05 and **0.00%** at
α = 0.025 on `S₂`.

**Ruling: P3's infeasibility claim HOLDS and is decisive.** The two-sample
Held-out-matching equivalence test is not underpowered — it is unachievable, at any budget,
as a property of the sealed comparator. P3's escape is to treat `S⁰` as a **constant**;
P3 itself labels that framing *"anti-conservative"*. §2 rules on whether that escape is
admissible.

### 1.6 Registry facts underpinning the population (verified against `registry.py`)

`ROOT_SEED = 20260813`; `PARTITIONS = ("development","held_out","challenge")`;
`PARTITION_CASE_COUNTS = {"development":4,"held_out":12,"challenge":3}`. The twelve G2
conditions are `F01,F02,F03,F04,F05,F08,F09,F10,F11,F12,F17,F18`. **F17 is declared in the
frozen registry as `"equivalent symbolic forms"` / purpose `"canonicalize equivalent laws"`
/ expected `"score equivalent forms once"`.** F07 is `"mass-only g truth"`; F19 carries the
3-variant null cycle `(F19A,F19B,F19C)`. `rc5_seeds.A35_SEARCH_SEED_BASE = 2_100_000_000`,
`A35_SEEDS_PER_CASE = 30`, occupied band `[2_100_000_000, 2_100_011_399]`.

P1's registry argument is confirmed in full and cites **no outcome of any experiment**.

---

## 2. RULING 1 — IS HELD-OUT-MATCHING QUALIFICATION ADMISSIBLE?

**Options.** (a) Qualify the surface by matching the sealed Held-out attribution — P3's
3-component IUT/TOST at δ = 10/144 against fixed `S⁰`. (b) Qualify by **provenance** —
P1's Gate Q1. (c) Qualify by **internal validity only** — P2 §2.5.

**Decided at R3.** Frozen `befca0d` §2.3 is a **destructive-only** rule: *"If E2a and E2b
disagree … which invalidates E2a as a calibration surface."* It attaches no positive force
to agreement. Option (a) converts a veto into a **selector over surfaces**, and a selector
is a licensing instrument. Conditional on qualification, the surface's stage vector is
pinned within δ of `S⁰`, and the routing statistic is a difference of that vector's
components. R3 is violated directly: Held-out evidence enters positive licensing.

**Corroborated at R8** (P2 §2.4's zero-residual-variance argument) and **at R4**: P3's own
analysis shows the two-sample framing is infeasible at any n (§1.5 verified), so the design
survives only by the discretionary act of declaring a 144-case sample to be a constant —
a choice made because it is the only one that makes the test feasible. That is precisely
the kind of analyst discretion R4 exists to eliminate.

> **DECISION 1 — Held-out-matching qualification is REJECTED in every form**, including
> "matching the dominant mechanism", "matching the ordering", "matching within a
> tolerance", and "matching the plurality". Decided by **R3**, corroborated by **R8** and
> **R4**. P2 (governance) and P3 (statistics) reach this independently; I verified P3's
> arithmetic myself and it holds with margin to spare.

**Consequence, recorded:** P3's `n = 576` was sized by the binding requirement
`n(S₂) = 555` of a test that no longer exists. That constraint is void. §7 re-derives `n`
from what remains.

**Consequence, recorded:** because no numeric Held-out-matching qualification survives,
P2's terminal **T9 (`REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY`) is NOT forced.** P2 §3.4
states the condition exactly: *"The only way T9 is avoided is by abandoning
Held-out-matching qualification entirely."* We abandon it. See §8.

---

## 3. RULING 2 — IS THE FOUR-WAY PLURALITY AN ADMISSIBLE ROUTING STATISTIC?

**Options.** (a) Bare argmax over `{A, B, C+D}` — P2 §7 rows 2–4, and frozen §2.9's own
licensing table. (b) Argmax with a certified margin — P3 R2. (c) Replace it with P1's
counterfactual recovery contrast.

**R1 favours (a) or (b).** The original causal question is *first loss*: `H_retain` /
`H_generate` / `H_partial` (§2.1), licensing the *smallest matching repair* (§2.9). The
four-way partition is that question's frozen statistic.

**R2 forbids (a).** A bare plurality with no margin cannot be falsified: every possible
count vector produces some argmax. §1.4 makes this concrete rather than theoretical — on
the only corpus where it has ever been computed, the argmax flips under two separate
undeclared analyst choices, at gaps of 0.23 pp and 4.4 pp.

**R4 forbids (a) decisively.** A bare argmax appears to have zero free parameters and in
fact has the maximum possible hidden discretion, because the conditioning set and the
instrument both move it. This is exactly the error that produced the v1 attribution
disaster in which 124 of 144 cases were relabelled.

> **DECISION 2 — The routing statistic is the frozen four-way partition, but a bare
> plurality is NOT the routing rule.** Routing requires a **certified margin**: the argmax
> must be identical under both extreme resolutions of the determinacy bound **and** its
> lead over the runner-up must have a 95% lower confidence bound above zero under both.
> Decided by **R2** and **R4**, within the estimand fixed by **R1**.

---

## 4. RULING 3 — WHICH PARAMETERIZATION OF THE FROZEN PARTITION?

**Options.** (a) The four marginal shares `(π_A, π_B, π_C, π_E)`. (b) P3's cumulative
stage-survival vector `S = (S₁, S₂, S₃)`. (c) The §2.6 conditionals
`P_front · P_retain|front · P_win|retain`.

**R1 is neutral:** all three are bijective reparameterizations of one another
(`π_A = 1−S₁`, `π_B = S₁−S₂`, `π_C = S₂−S₃`, `π_E = S₃`). No information is lost or gained.

**R6 decides.** `MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.6 freezes the three conditional
stages by name, prospectively at `befca0d`. The cumulative form is the **algebraically
identical** reading of that frozen triple with a fixed rather than random denominator.

**R9 then discriminates between (b) and (c) at no cost to validity.** Only the cumulative
form is **monotone** in the row-label lattice (P3 §6.1, proof verified: the cross-seed
representative is selected by `identity_contract.template_key` grouping and never reads
`g2_correct`; `retained_by_argmax_score` is a score comparison). Monotonicity turns the
determinacy bound from `2^U` evaluations into **two**. The conditionals and the marginal
shares are not monotone.

> **DECISION 3 — The primary is the frozen four-way partition, computed and bounded in
> P3's cumulative stage-survival parameterization `S = (S₁, S₂, S₃)`, with the four-way
> shares reported by differencing.** Decided by **R6**, with **R9** selecting the
> parameterization. P3's single most valuable technical contribution, adopted whole.

---

## 5. RULING 4 — PRIMARY OR SECONDARY FOR P1's RECOVERY CONTRAST?

P1 argues, correctly and importantly, that first-loss is a **proxy** for recoverability;
that the two are different functionals; and that "smallest matching repair" names
recoverability, not first loss.

**R1 decides against making it primary.** The rule is *"best preserves the original causal
question"*, and the original question is first-loss attribution. Substituting recovery
changes the estimand. **R5** agrees (it changes a scientific factor), and **R6** agrees
(first-loss is frozen at `E2_PREDECLARATION` §6; the recovery contrast is not frozen
anywhere).

**R2 argues for including it.** It is a genuine, independent falsification opportunity, and
P1's argument that E2b's four-way labels do not determine any recovery contrast is correct
and is the cleanest functional-independence claim in the council.

**R4 argues for keeping it out of the licensing path.** It requires a DEV/EVAL arm-selection
apparatus over a 9-parameter retention grid and a 3-arm voting grid — the largest single
source of analyst discretion proposed by anyone.

> **DECISION 4 — P1's counterfactual recovery contrast is adopted as a PRE-DECLARED
> SECONDARY DIAGNOSTIC, computed on the DEV half only, and it cannot license, block, or
> modify any routing verdict.** Decided by **R1/R5/R6** against primacy; retained by **R2**;
> confined by **R4**. If a later amendment wishes to promote it, that promotion must be
> written and frozen before its DEV values are read.

**Recorded as overridden:** R9 would have preferred to drop it entirely (it costs
classification of an 8-row retained superset per seed). R2 outranks R9. It stays.

---

## 6. RULING 5 — WHAT IS THE QUALIFICATION CRITERION?

**Options.** (a) P1's Gate Q = Q1 (design provenance) ∧ Q2–Q4 (truth-blind Held-out
descriptor equivalence tests). (b) P2's binary structural internal-validity criterion.
(c) P3's TOST — dead at §2.

**Q1 is adopted without argument.** It is a construction check over `registry.py`,
`generator.py` and `rc5_seeds.py`. It introduces **zero numeric magnitudes**, reads **zero
outcomes**, and is mechanically verifiable by a static checker. R3, R4, R8 and R10 all
favour it. It is the strongest single idea in the council.

**Q2–Q4 are REJECTED as gating clauses.** They are equivalence tests against descriptors
computed from the Held-out cases (`descriptor_sd`, `mass_range_ratio`,
`identity_class_count`, consensus concentration, retained `valid_r2`/complexity). They are
truth-blind and pre-E2b, so they do not violate R3 as strongly as option (a) — but:

- **R4 rejects them.** They introduce at least three new magnitudes (a block-jackknife
  percentile, an IQR-overlap fraction, a KS-equivalence margin), none frozen anywhere.
  P2's review metric — *"if a proposed design introduces more than one new number, it is
  almost certainly tuning"* — is the correct instrument here.
- **R2 rejects them as gates.** P1 discloses, honestly, that it measured E2a's consensus
  geometry and **E2a would very likely PASS Q3**. A clause that passes the surface it was
  designed to exclude has no falsification power as a gate.
- **R3 rejects them at the margin.** In a conjunction, a passing clause is a necessary
  component of the overall PASS, and the overall PASS is what permits routing. A
  Held-out-derived clause inside a conjunctive licence is Held-out evidence inside positive
  licensing, however weakly.

They survive, in full, as **mandatory reported diagnostics** — under **R2**, because
publishing the descriptor vector preserves an independent critic's ability to test
additional descriptors against the same surface later without regenerating it.

> **DECISION 5 — Qualification = Q1 (design provenance) ∧ the five internal-validity
> controls C-1…C-5 (P2 §10) ∧ schema completeness ∧ zero indeterminate cases.** Every
> clause is **binary and structural**; the criterion introduces **no numeric magnitude at
> all**. P1's Q2–Q4 descriptor vector is computed and published as a **non-gating**
> diagnostic. Decided by **R4**, corroborated by **R2** and **R3**.

This is the point where P1's and P2's positions converge exactly: once R4 strips the
margins out of Q2–Q4, P1's Gate Q *is* P2's "binary and structural" criterion, plus P1's
provenance clause which P2 never proposed and which is strictly better than anything in
P2's §6.2.

---

## 7. RULING 6 — IS THE NEW SURFACE NEEDED AT ALL, OR IS THE HONEST FIRST STEP P2's BC-0?

This is the ruling the owner asked to be argued under **R2, R5, R9, R10**. I argue it in
that order, because that is rule order.

### 7.1 What BC-0's headline question actually is, and why it is already answered

P2's BC-0: *"No new surface may be commissioned until the sealed E2a fronts are re-scored
under the determinacy-bound instrument and the corrected A/B/C+D counts are published."*
Its stated rationale is that the divergence *"has a live, cheap-to-test, mundane
explanation — an instrument asymmetry — that has never been controlled for"*, and that
commissioning a 540-world re-run before testing it *"is the single most expensive avoidable
error available to this programme."*

**§1.2 and §1.3 answer that question at zero compute, and the answer is no.** The worst-case
bound is `A ∈ [49,122]`, `B ∈ [196,267]`, `C ∈ [99,104]`, `E ∈ [119,124]`; the Gate-2
predicate is invariant across all of it; and the correction moves E2a *further* from E2b
(TV 14.78 → 25.00 cases pooled, 10.67 → 17.00 noise-matched). The instrument-artifact
hypothesis is refuted, not merely untested.

**R2 therefore demotes BC-0 sharply.** Its falsification power against the divergence
hypothesis is spent. I will not manufacture a diagnostic to look thorough when I have
already produced its answer.

### 7.2 But BC-0 has a second job that is not optional, and R2 makes it mandatory

The determinacy gap `g` — how much of the endpoint the instrument refuses to decide —
is a **nuisance parameter that eats the design's resolving power directly**. I measured it
on E2a, standardised: `g` ranges **0.044–0.056** across the four classes. That is
**0.63–0.81 δ**. P3's §3.1 table quantifies the price: moving `g` from 0.02 to 0.01 saves
247 worlds; from 0.03 to 0 saves 852.

If the new surface is generated and its `g` lands near E2a's, **the design cannot certify
any routing margin at any affordable n, and it will return INDETERMINATE for reasons that
have nothing to do with the pipeline.** That is P3's "rigged failure", and **R2 forbids
building a design whose outcome is determined by its instrument rather than by its
subject.** BC-0 — escalating the 397 timed-out expressions to completion and measuring the
achieved `g` and the escalation cost per expression — is the only way to know, before
spending the search budget, whether the instrument can be made determinate enough for the
experiment to be able to fail honestly.

BC-0 also discharges, at zero scientific compute and zero leakage (P3 §7.3), the
engineering validation of the bounded evaluator, the escalation harness, the bootstrap
code and the schema validator against a real corpus.

**R5:** BC-0 changes **zero** scientific factors. Same corpus, same `g2_contract`, same
A–E order; only the instrument's refusal-to-decide is added, which P2 §3.2 establishes is
strictly conservative — *"it can refuse to decide, never decide differently."*

**R9:** BC-0 requires **zero new search**. Its cost is escalating ≤ 397 distinct
expressions; the sealed Gate 1 precedent escalated 6 at 5.5–21.8 s each, and the E2b record
shows a pathological tail (2 expressions unresolved at a patient 600 s). Worst case with a
600 s per-expression patience bound is 66 CPU-hours and it is embarrassingly parallel;
realistic case is single-digit CPU-hours.

**R10:** BC-0 is a deterministic recomputation over a local sealed corpus. An independent
critic reproduces it with the corpus and the script. The surface is not reproducible
without ~150 CPU-hours and a registry amendment.

**Crucially, BC-0 is computable without violating D6 or P2's own PM-8.** PM-8 correctly
notes that `score` is absent from the E2a corpus and that arms keyed on `score` are not
computable from it. But BC-0 needs **no arm**: the frozen R0 retention decision is
**already persisted as the boolean `retained_by_argmax_score`**, verified unique per
(world, seed) across all 16,170 pairs (§1.2). No field is back-filled, imputed or
fabricated. And BC-0 is explanatory-only, so D6's "decision-relevant corpus" clause is not
engaged.

### 7.3 Is the surface needed at all?

**Not for the reason the programme thought.** The surface cannot adjudicate the E2a/E2b
divergence, because Decision 1 forbids the comparison from licensing anything and §1.5
shows it could not be certified even if it were permitted. And the divergence is now
largely explained without it: 68–77% composition (§1.3), plus a demonstrated instrument
asymmetry whose correction runs the other way.

**It is needed for exactly one reason, and that reason is sound and outcome-free.** No
corpus in existence instantiates the twelve Held-out G2 **conditions** in a form that may
license anything. E2a is `5 truth families × 3 coefficient regimes × 3 noise levels`. It
contains **no missingness condition (F04), no boundary condition (F05), no
irrelevant-distractor condition (F11), no correlated-distractor condition (F12), and — the
decisive omission — no equivalent-symbolic-forms condition (F17)**, whose frozen registry
purpose is literally *"canonicalize equivalent laws"* and whose expected behaviour is
*"score equivalent forms once"*. F17 is the condition purpose-built to stress the
cross-seed identity contract. **The live routing question is retention versus cross-seed
identity. Deciding it on a corpus containing no identity-stressor condition is not
answering the question.**

That argument cites `registry.py` and nothing else. It contains no outcome, no E2a number
and no E2b number. It satisfies **R3** and **R8** completely, and **R1** — it is the only
argument on the table that makes the surface serve the *original* causal question rather
than the divergence that interrupted it.

### 7.4 The ruling

> **DECISION 6 — The expensive surface is NOT commissioned now. It is CONDITIONAL, gated
> behind a mandatory zero-new-search Stage 0.**
>
> - **Stage 0 (mandatory, zero new search):** re-score the sealed E2a fronts under the
>   bounded-determinacy instrument with uncapped escalation of all 397 `SIMPLIFY_TIMEOUT`
>   expressions. Publish the corrected A/B/C+D/E counts, the achieved determinacy gap
>   `g_j`, the achieved escalation cost distribution, and the corrected standardised stage
>   vector. **Explanatory-only. Licenses nothing. Citable by nothing.**
> - **Stage 0 gate (fixed now, before Stage 0 runs):** Stage 1 may proceed **only if** the
>   escalation reduces the corpus-level determinacy gap to `g_j ≤ 0.010` for `j = 1,2,3`
>   *and* leaves `0` indeterminate worlds. If it does not, the honest terminal is
>   **`T-INSTRUMENT-UNBOUNDED`**: the G2 contract as frozen is not decidable at finite cost
>   on this class of population, which is a finding about the contract and forbids the
>   surface rather than merely delaying it.
> - **Stage 1 (conditional):** the calibration-partition surface specified in the companion
>   protocol.
>
> Decided by **R2** (BC-0's divergence question is spent, but its instrument question is a
> precondition for the surface having any falsification power at all), with **R5**, **R9**
> and **R10** all independently favouring running Stage 0 first, and **R1** establishing
> that the surface — if Stage 0 permits it — is genuinely required for the F17/F04/F11/F12
> condition coverage that no admissible corpus contains.

**Recorded honestly:** I did not reach "run the cheap thing first" by preference. R2 ranks
above R5, R9 and R10 and, taken alone against the *divergence* question, R2 favours the
surface. The reason Stage 0 gates Stage 1 is that R2 applied to the *instrument* question
makes Stage 0 a precondition of the surface being falsifiable. If Stage 0 returns
`g ≤ 0.010`, Stage 1 executes and the compute is spent. This is a gate, not an excuse.

---

## 8. RULING 7 — ARCHITECTURE

**x86_64 is ACCEPTABLE; ARM64 is NOT REQUIRED; T9 is NOT forced.**

All three council members agree conditionally, and Decision 1 removes the condition that
would have forced T9. Every quantity in the protocol is **within-surface**, computed on one
host under one hash-recorded dependency lock. The single exception is the post-seal
falsification veto (§9), which is quantitative and cross-architecture.

**R2 requires keeping the veto.** It is the strongest single falsification opportunity in
the design, and frozen §2.3 mandates it. **R3 and R8 permit it**, because its output space
is `{STANDS, HALTED}` — a monotone halt-only channel cannot move probability mass between
arms, only zero the vector (P1's argument (iii), which I endorse as correct and
load-bearing). **R4 is satisfied** because its tolerance is not a new number: it is δ =
10/144, ported as a proportion per P2's BC-16.

The unquantified cross-architecture search delta means a trip could be a regime difference
*or* an architecture artifact, and the design cannot tell them apart. **That is disclosed
rather than used as grounds to remove the veto**, because a false HALT is conservative and
removing the veto would reduce falsification opportunity, which R2 forbids.

Binding: **A1** single-host generation, no ARM/x86 merging; **A2** no wall-clock cap may
assign a label anywhere; **A3** host-determinism and retention-identity controls before
world 1. `SIMPLIFY_TIMEOUT_SECONDS = 5` is retired as a classification rule.

---

## 9. RULING 8 — THE ORDER OF OPERATIONS AND E2b's ROLE

P1's three-gate architecture and P2's BC-1/BC-2/BC-19 are the same mechanism. Adopted
without contest, decided by **R8**:

```
GATE Q  QUALIFY  registry + generator provenance + internal-validity controls
                 E2b contribution: ZERO BITS
GATE R  ROUTE    the new surface alone; verdict hash-sealed and chained BEFORE
                 any process may read Gate V
GATE V  VETO     sealed Gate R output + E2b;  output space { STANDS , HALTED }
```

Enforced mechanically by `git merge-base --is-ancestor` (P2 T-d/BC-1), by a hash-chained
event log, and by a **different adjudicator** for Gate V. Exactly **one** surface is
generated (BC-2); the tuning ledger must be empty (BC-4); a passing veto is **silent** and
may never appear in any citation set (BC-10, PM-5).

**Measured non-determination (`QND`), P1 §2.4(v), adopted as a hard precondition** under
**R2**: before Stage 1 executes, enumerate stratified subpopulations of E2a that would pass
Gate Q's measurable clauses and verify the routing verdict is **not constant** across them.
If it is constant, qualification *is* routing and the design is circular by measurement —
do not execute. §1.4 already shows the verdict varies under conditioning on this corpus,
which is evidence the check will pass, but it is run and sealed rather than assumed.

---

## 10. RULING 9 — SAMPLE SIZE, DERIVED RATHER THAN CHOSEN

P1 proposed 216 G2 + 36 control. P3 proposed 576. **Both were sized for constraints that
Decision 1 and Decision 2 dissolved** — P1's for a paired McNemar recovery contrast now
demoted to secondary; P3's for `n(S₂) = 555` under a two-sample-adjacent equivalence test
now rejected.

`n` must now be sized for exactly one thing: **the routing certification of Decision 2.**
The requirement, derived from frozen authority alone:

> The design must be able to certify a routing lead at least as large as the programme's
> own definition of a material attribution difference.

That magnitude is frozen: **δ = 10/144 = 0.069444** (PE2-4, `befca0d` line 466; `f4c1105`
§4; adjudicated in `GATE_1_DEFINITIVE.md`), ported as a proportion per BC-16. **R6** selects
it; **R3** rejects the alternative (P3's `δ_dec = ½(π_C − π_B) = 0.0556`) because it is
computed from the sealed Held-out attribution.

For a multinomial contrast, `Var(π̂₁ − π̂₂) = (π₁ + π₂ − (π₁−π₂)²)/n`. **R4** selects the
distribution-free bound `π₁ + π₂ ≤ 1` over the Held-out-informed value 0.875, because the
latter is a discretionary assumption imported from the comparator:

```
n  >=  (1 - delta^2) * ( z_.95 + z_.80 )^2 / delta^2
    =  0.995177 * 2.486473^2 / 0.069444^2
    =  1275.8
```

The single new magnitude introduced anywhere in this protocol is the power level **0.80**,
and it affects only `n` — never a verdict, never a threshold, never a label.

> **DECISION 7 — `n = 1296 G2 worlds = 12 conditions × 108 replicates`**, plus
> `216 negative-control worlds` (F07 × 108, F19 × 108), **× 30 seeds = 45,360 searches.**
> 1296 ≥ 1276; 108 is divisible by 3 so F19's variant cycle stays balanced and by 2 so the
> secondary DEV/EVAL split is exact; among admissible values the lexicographically simplest
> is taken, per the tie-break rule. Seeds per world = **30, frozen and non-negotiable**
> (`A35_SEEDS_PER_CASE`; P3 §3.5 shows 15 seeds shifts `S₁` by 3.09 δ — a change of
> estimand, not an economy).

**Resolving power of this n, recorded before execution:**

| n | minimum routing gap certifiable at 80% power |
|---:|---:|
| 252 (P1) | 0.1448 = 2.08 δ |
| 576 (P3) | 0.0964 = 1.39 δ |
| **1296** | **0.0659 = 0.95 δ** |

Note that this design is powered **exactly at the boundary of my own predicted outcome**
(§11): I predict a gap below δ, and 1296 is the smallest lattice point at which a gap of δ
is certifiable. My prediction is therefore falsifiable by this design, which is the point.

**Compute:** 45,360 searches at the measured 3.86 s/search = **48.6 CPU-hours** of search.
Scoring by lazy classification **under the determinacy bound** (permitted by P2 §8 item 20;
sound because the bound forbids the call count from changing a label), scaled from E2a's
measured 262.5 s/world: **~110 CPU-hours**, plus escalation. **Declared ceiling: 260
CPU-hours.** ~7–13 h wall at 20 workers. Search is not the bottleneck; scoring is, exactly
as the coordinator established.

---

## 11. THE OUTCOME I EXPECT, RECORDED BEFORE EXECUTION

The owner required this so the record shows the design was not chosen for its answer. I
record a **quantitative** prediction, not a hedge.

**Stage 0.** I expect the corrected E2a attribution to land near
`A ≈ 60–90, B ≈ 230–255, C+D ≈ 100–104, E ≈ 119–122`, with the `B` plurality intact and
the standardised divergence from Held-out **larger** than the sealed corpus's. I expect
`g` after escalation to be **≤ 0.005** and `0` indeterminate worlds, i.e. **Stage 0 passes
its gate**, but I put this at roughly 70% and the residual 30% on a pathological tail
forcing `T-INSTRUMENT-UNBOUNDED`.

**Stage 1.** I expect:

- `π_A < 0.15` — corrected E2a (0.038) and Held-out (0.097) agree here, and E3's completed
  MARGINAL verdicts on affine and exponential mean a moderate `π_A` is *licensed in
  advance* and must not be re-read as a generation failure (P3 C5, adopted).
- `π_E < 0.10`.
- `π_B` and `π_C` both in `[0.35, 0.52]`, with **`|π_B − π_C| < δ = 0.0694`**.

**My predicted terminal state is `ROUTING_INDETERMINATE`.** The two available predictions
point opposite ways and neither dominates: composition-matched, instrument-corrected E2a
says `B` (0.5208 vs 0.3789); the actual Held-out draw at these very conditions says `C`
(0.4931 vs 0.3819). A surface drawn at the twelve conditions but on a different host and a
different replicate block should land between them, with a gap this design is powered to
certify only if it exceeds δ. I put `ROUTING_INDETERMINATE` at ~55%, `ROUTING_CERTIFIED → B`
at ~30%, `ROUTING_CERTIFIED → C` at ~10%, `VOID` at ~5%.

**Conditional on `ROUTING_CERTIFIED → B`, I expect Gate V to HALT**, because a `B`-plurality
surface diverges from the sealed Held-out attribution by more than δ, and §2.3 fires exactly
as it did for E2a. Conditional on `ROUTING_CERTIFIED → C`, the licensed arm is **E4f, which
has no operational freeze** and terminates at `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`
(P2 §1.10, BC-21, F6 — verified).

**Therefore: my honest overall expectation is that this protocol does NOT reach E4
re-entry**, on any branch, and I am proposing it anyway.

**The disclosure that makes this checkable.** If I had wanted re-entry, the design that
delivers it was on the table and I rejected it: **P3's fixed-target TOST at n = 576.** With
`S⁰` treated as a constant and the surface generated at the Held-out cell mix, it is the
only proposal in the council with a plausible `QUALIFIED` verdict — and its own author flags
the framing as anti-conservative. I rejected it under **R3** and **R8**, not because I
doubted it would pass, but because I expected it would.

---

## 12. RECOMMENDATIONS TO THE PROTOCOL OWNER

**D7 (corrected form), recommended for issue.** P2 recommended a D7 asserting that the
instrument contamination may reverse E2a's plurality onto E2b's answer. §1.2 refutes that.
The correct D7 is:

> **D7 — the sealed E2a attribution is INSTRUMENT-CONTAMINATED but its Gate-2 plurality is
> DETERMINATE.** `A = 122` is an upper bound; the sealed corpus lacks the per-row
> `canonicalization_status` needed to audit the contamination row-wise. However, every
> retained row of every world is determinately labelled, so `n_retained_correct` cannot
> move; the corrected bound is `A ∈ [49,122]`, `B ∈ [196,267]`, `C+D ∈ [99,104]`,
> `E ∈ [119,124]`; and the frozen predicate `B > A AND B > C+D` holds at every point of it.
> **No statement of the form "the E2a/E2b divergence is explained by the wall-clock timer"
> may be made or cited** — the correction runs in the opposite direction. D5's ruling on
> *role* is unaffected: the determinate `B` plurality still may not license E4a.

**Two arithmetic corrections for the record.** P2 §1.7 and P3 §5.5 publish a determinacy
bound that is wrong on its lower limit for `B` and its upper limits for `C` and `E`; P3
§5.3 reports composition as removing 91% of the total-variation divergence where the
correct figure is 77.0%. Neither error is misconduct; both are on the record now.

**The E6 circular dependency must be resolved before Stage 1 freezes.** Every routing
licence's safety half depends on E6's `false_structure_rate` ceiling, and E6 is self-blocked
pending exactly this hook. If E6 cannot supply a ceiling at decision time, **every licence
is conditional and non-executable** and that must be pre-labelled, not discovered.

**E4f must be declared non-executable before Stage 1 freezes** (P2 BC-21). Its branch is
reachable and it has no operational freeze, no population, no split, no statistical
procedure, no identity control, and no numeric `false_labelling_rate` or `k_inflation`
ceiling. Inventing those ceilings after the route is known is, as P2 correctly identifies,
the highest-leverage cheat available to this programme.

---

## 13. DECISION SUMMARY

| # | Contested choice | Options | Decided by | Decision |
|---|---|---|---|---|
| 1 | Qualify by matching Held-out? | match / provenance / internal-validity | **R3** (+R8, R4) | **REJECTED in every form.** T9 not forced |
| 2 | Bare plurality as routing rule? | bare argmax / certified margin / recovery contrast | **R2, R4** (within **R1**) | Frozen partition retained; **bare plurality rejected**, certified margin required |
| 3 | Parameterization | marginal shares / cumulative `S` / conditionals | **R6** (+R9) | **Cumulative stage-survival `S`**, four-way recovered by differencing |
| 4 | Recovery contrast primary? | primary / secondary / omit | **R1, R5, R6** vs **R2** vs **R4** | **Secondary**, DEV-only, non-licensing |
| 5 | Qualification criterion | Q1+Q2–Q4 / binary structural / TOST | **R4** (+R2, R3) | **Q1 provenance ∧ C-1…C-5**, zero magnitudes; Q2–Q4 non-gating diagnostics |
| 6 | Surface now, or BC-0 first? | surface / BC-0 / both | **R2** (+R5, R9, R10) | **Stage 0 mandatory and gating; surface CONDITIONAL** |
| 7 | Architecture | x86 / ARM required | **R2, R3, R8** | **x86 acceptable; ARM not required; veto retained with disclosed caveat** |
| 8 | Order and E2b's role | veto-first / route-first | **R8** | **Q → R (sealed) → V**, halt-only, silent on pass, single-shot |
| 9 | Sample size | 252 / 576 / derived | **R6, R4, R2** | **1296 G2 + 216 NEG**, derived from frozen δ; one new magnitude (power 0.80) |
| 10 | Expected outcome | — | recorded | **`ROUTING_INDETERMINATE`**; no re-entry expected on any branch |

**Ties were broken by rule order, not by preference.** Where a member's proposal was
rejected, the rule number that rejected it is named above and argued in the corresponding
section. Where two members converged, I verified the convergence independently rather than
treating agreement as evidence — and in the one case where all three would have agreed with
each other (P2's and P3's determinacy bound on E2a), the agreement was **wrong**, which is
the strongest argument in this record for verification over consensus.

---

*SYNTHESIS. This document licenses no experiment, no threshold, no change and no re-entry.
It records which design was frozen and which numbered rule froze it.*
