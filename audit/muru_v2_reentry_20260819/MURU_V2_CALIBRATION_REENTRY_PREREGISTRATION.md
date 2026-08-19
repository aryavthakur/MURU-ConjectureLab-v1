# MURU v2 — CALIBRATION / RE-ENTRY PROTOCOL

> ## THIS IS A PROSPECTIVE POST-GATE-1 PROTOCOL-OWNER AMENDMENT
> ## CREATED UNDER THE MAXIMUM-AUTHORIZATION INSTRUCTION.
> ## IT IS **NOT** HISTORICALLY PREREGISTERED AND MUST NEVER BE DESCRIBED AS SUCH.
>
> Authority to exist: `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10. Provenance discipline:
> ratification §10 and P2 PM-17. Calling this document "preregistration" without the above
> qualifier is a provenance misstatement of the exact kind the Gate 1 record already had to
> withdraw once.

**Experiment identifier:** `E7 — CALIBRATION PARTITION RE-ENTRY SURFACE`
**Synthesis authority:** `SYNTHESIS_DECISION_RECORD.md` (same directory), which records
which numbered decision rule fixed each choice below.
**Status at this commit:** frozen protocol text. **No world generated. No partition
amended. No search executed.**

**Threshold discipline (binding on every number in this document).** Every threshold is
either **(i) REUSED VERBATIM** from frozen authority with its citation, or **(ii) DERIVED**
from first principles with the derivation shown inline. Both are fixed before any new
result is observed. §33 is the complete inventory. **Exactly one new magnitude is
introduced anywhere in this protocol** (the power level 0.80 in §10), and it affects only
the sample size — never a verdict, never a label. **No wall-clock cap decides a label
anywhere in this protocol.**

---

## 0. STRUCTURE — TWO STAGES, AND STAGE 1 IS CONDITIONAL

```
STAGE 0   INSTRUMENT CALIBRATION AND CORRECTED E2a ATTRIBUTION
          zero new search · explanatory-only · licenses nothing · citable by nothing
          GATE: g_j <= 0.010 for j=1,2,3 AND 0 indeterminate worlds
                  |                                    |
                 PASS                                 FAIL
                  v                                    v
STAGE 1   THE CALIBRATION SURFACE            TERMINAL T-INSTRUMENT-UNBOUNDED
          Gate Q -> Gate R (sealed) -> Gate V           STOP
```

### 0.1 Stage 0 — mandatory, gating, zero new search

**What it does.** Re-score the sealed E2a front corpus (`results/e2/run_x86_e2a_v1`, 539
worlds, 189,467 rows, 16,170 (world, seed) pairs) under the bounded-determinacy instrument
of §25, escalating **all 397 distinct `SIMPLIFY_TIMEOUT` expressions to completion** under
an uncapped tier-2 budget.

**Why it is computable without violating D6.** The frozen R0 retention decision is already
persisted as the boolean `retained_by_argmax_score`, verified unique per (world, seed)
across all 16,170 pairs. **No field is back-filled, imputed, recomputed from an absent
column, or fabricated.** The absent `score` column is not needed, because Stage 0 evaluates
no arm. Stage 0 is explanatory-only and therefore does not engage D6's "new
decision-relevant corpus" clause.

**What it publishes.** (a) the corrected A/B/C+D/E counts at both extreme resolutions and
after escalation; (b) the achieved determinacy gap `g_j` for `j = 1,2,3`; (c) the escalation
cost distribution per expression; (d) the corrected standardised stage vector; (e) the
count of expressions still unresolved after uncapped escalation.

**What it may never do.** Stage 0 output is stamped `EXPLANATORY_ONLY` at the record level.
It may not appear in the citation set of any change, may not license any E4 arm, and may
not be used to select, size, weight, exclude or re-read anything in Stage 1 other than the
binary gate below. Stage 1's population, statistic, margins, routing rule and terminal
states are fixed in this document **before Stage 0 runs**.

**The gate, fixed now.**

```
STAGE_0_PASS  <=>  g_j <= 0.010 for j = 1,2,3   AND   INDETERMINATE_WORLDS == 0
```

- `g_j <= 0.010` — **DERIVED.** `g_j` is subtracted directly from the equivalence/certification
  margin (§20). The derivation is in §10: the number of worlds required scales as
  `1/(delta - g)^2`, so at `g = 0.010` the design's resolving power is degraded by
  `(delta/(delta-g))^2 - 1 = (0.069444/0.059444)^2 - 1 = 36.5%`, and at `g = 0.020` by 97.3%. 0.010 is the largest gap at which the §10 sample size remains within a factor 1.4
  of its `g = 0` value. It is not chosen to be passable; §0.2 records that the sealed E2a
  corpus **fails** it by a factor of 4–6.
- `INDETERMINATE_WORLDS == 0` — **REUSED.** P2 §6.2's least-discretionary choice, taken from
  demonstrated achievement: the sealed Gate 1 adjudication achieved 158/51,411 = 0.31% rows
  unresolved and **0** indeterminate cases across 144 (`FINAL_TERMINAL_REPORT.md` §3). The
  strictest available bar, and the one already shown achievable.

### 0.2 What Stage 0 is NOT for, recorded so it cannot be repurposed

Stage 0's headline question — *"is the E2a/E2b divergence an artifact of the 5-second
timer?"* — **is already answered, analytically, at zero compute**, in
`SYNTHESIS_DECISION_RECORD.md` §1.2–§1.3. The corrected determinacy bound is
`A ∈ [49,122]`, `B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`; the frozen Gate-2
predicate `B > A AND B > C+D` holds at every point of it; and the correction moves E2a
**further** from the sealed Held-out attribution (total variation 14.78 → 25.00 cases
pooled, 10.67 → 17.00 noise-matched). Measured on the sealed corpus, the standardised
determinacy gap is **0.044–0.056**, i.e. **4.4 to 5.6 times** the Stage 0 gate.

Stage 0 therefore exists to answer the *remaining* question — **can the instrument be made
determinate enough for Stage 1 to be able to fail honestly?** — and to validate the
evaluator, escalation harness, schema validator and bootstrap code against a real corpus at
zero scientific compute and zero leakage. Nothing in Stage 0 may be reported as resolving
the divergence.

---

## 1. PURPOSE

To construct and execute the prospectively frozen, decision-admissible calibration and
re-entry qualification required by ratified decision **D3**, items 1–7 (protocol
construction) and item 8 (execution), so that
`EXPERIMENTAL_REENTRY_RESOLUTION` can be evaluated on evidence that is admissible for
licensing.

The scientific question, in one sentence:

> On an independent draw from the benchmark's own G2 condition grid — the same generator,
> the same twelve prospectively declared experimental conditions, the same coefficient and
> noise design as the Held-out population, in a partition disjoint from `held_out` and
> never used for any endpoint — **which single pipeline stage (generation, within-seed
> retention, cross-seed identity voting) first loses the G2 signal, and does its lead over
> the runner-up exceed the programme's own definition of a material attribution
> difference?**

This is the **original causal question** of §2.1 (`H_retain` / `H_generate` / `H_partial`)
and §2.9's licensing table, preserved verbatim, on a population that can actually answer it.

## 2. AUTHORITY

| Source | What it supplies |
|---|---|
| `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10 | authority for this document to exist; its status as a prospective post-Gate-1 amendment |
| ratification §5 (D3) | the eight `EXPERIMENTAL_REENTRY_RESOLUTION` items this protocol must satisfy |
| ratification §7 (D5) | E2a invalidated as a Held-out-facing calibration surface; `LOCKED_EXECUTE_E4A` has no forward-licensing force; the `B` plurality may not be cited to license E4a |
| ratification §8 (D6) | any new decision-relevant corpus must satisfy the frozen required schema **from inception**; no retroactive field fabrication; regenerate rather than impute |
| ratification §4 (D2-ext) | all E4 arms suspended; no automatic re-entry |
| `befca0d` (`MURU_V2_G2_PARETO_STUDY_DESIGN.md`) §2.3–§2.11, §3 | inadmissibility of E2b; the 28-field schema; truth-blind boundary; controls; conditional-stage metrics; licensing table; safety-cost requirement |
| `MURU_V2_E2_PREDECLARATION.md` §4/§5/§6 | world enumeration, seed derivation, the A–E taxonomy and its strict decision order |
| `f4c1105` (`…RETENTION_REMEDIATION_PREREGISTRATION.md`) §4/§5/§6/§7/§8/§9 | materiality tolerance; Gate-2 predicates including the tie branch; DEV/EVAL discipline; paired statistics; multiplicity; controls |
| `1d20731` / `94abf97` (E3) | completed identifiability verdicts, binding on the generation branch |
| `GATE_1_DEFINITIVE.md`, `FINAL_TERMINAL_REPORT.md`, `ATTRIBUTION_REVISION.md` | the sealed Held-out attribution (ratified D1) and the determinacy-bound precedent |
| `src/muru/paper_benchmark/registry.py`, `generator.py`, `rc5_seeds.py`, `seed_band_registry.py` | the condition grid, the generator, the seed derivation and the declared-band mechanism |
| `SYNTHESIS_DECISION_RECORD.md` | which numbered decision rule fixed each contested choice |

**This protocol licenses nothing by itself.** It defines an instrument. Execution of that
instrument, and only its adjudicated verdict, may license.

## 3. WHAT THE OLD E2a FAILURE MEANS

Stated precisely, because the whole design turns on it.

**It does not mean E2a's data are wrong.** D5 is a ruling on **role**, not a repudiation.
E2a's measurements remain valid synthetic-domain diagnostic evidence.

**It means three separate things, and they must not be conflated:**

1. **A composition failure (primary).** E2a is a balanced factorial — 5 truth families at
   20% each, 3 coefficient regimes, 3 noise levels. Held-out G2 is 75% `mass_affine`, 8.3%
   each saturating / interaction / exponential, and **zero `mass_power`**; and its noise is
   a *condition axis* at 1/12 weight, not a crossed factor at 1/3 weight. E2a's
   `mass_power` stratum is 107/107 `SUCCESS` and has no descriptor truth at all; the
   four-way partition scores it as G2 success and it single-handedly lifts E2a's success
   rate. Direct-standardising E2a to the Held-out truth-family mix removes **68.1%** of the
   total-variation divergence pooled over noise and **77.0%** noise-matched.
2. **A condition-coverage failure (decisive for what must be built).** E2a instantiated
   **none** of the twelve prospectively declared Held-out G2 conditions. It has no
   missingness condition (F04), no boundary-scale condition (F05), no
   irrelevant-distractor condition (F11), no correlated-distractor condition (F12), and no
   **equivalent-symbolic-forms** condition (F17) — the condition whose frozen registry
   purpose is *"canonicalize equivalent laws"* and whose expected behaviour is *"score
   equivalent forms once"*, i.e. the one condition purpose-built to stress the cross-seed
   identity contract. **The live routing question is retention versus cross-seed identity.
   No admissible corpus contains an identity-stressor condition.** This is the reason —
   the only reason — a new surface is required, and it cites `registry.py` and no outcome.
3. **An instrument failure (real, quantified, and NOT the explanation).**
   `lazy_classify.py:186` returns `False` whenever `canonicalization_status != "OK"`, so a
   5-second wall-clock `SIMPLIFY_TIMEOUT` is consumed as evidence of absence, monotonically
   toward `NEVER_ON_FRONT`. 397 distinct expressions / 396 rows are affected, concentrated
   59.8% in stage A. **But every retained row of every one of the 539 worlds is
   determinately labelled**, and retention is label-independent and already persisted, so
   `n_retained_correct` cannot move: the corrected bound is `A ∈ [49,122]`,
   `B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`, and the frozen Gate-2 predicate is
   **invariant** across all of it. Correcting the defect moves E2a **away** from the
   Held-out attribution. **No statement of the form "the E2a/E2b divergence is explained by
   the wall-clock timer" may be made or cited under this protocol.**

**What the failure does NOT mean.** It does not mean the sealed Held-out attribution
licenses anything. E2b remains `DECISION_INADMISSIBLE`. It does not mean agreement with
Held-out qualifies a surface — `befca0d` §2.3 is a **destructive-only** rule and attaches no
positive force to agreement.

## 4. WHAT THE NEW SURFACE IS INTENDED TO QUALIFY

**It is intended to qualify exactly one thing:** that a stage-attribution measured on it is
**decision-admissible** — i.e. may license the smallest matching E4 repair — because the
surface is an **independent draw from the same experimental design as the target
population**, measured with a host-independent instrument, under controls that are
answerable against something other than the surface's own attribution.

**It is NOT intended to qualify, and this protocol makes no claim of, any of the following:**

- that the surface reproduces the Held-out *behaviour*. Qualification is a statement about
  **where the surface came from**, not about what it resembles. Any qualification criterion
  strong enough to establish behavioural regime fidelity is necessarily keyed to the
  attribution and is therefore circular; any criterion weak enough to avoid the attribution
  is too weak to establish fidelity (P2 §2.6, accepted).
- that an x86 search would have produced the Held-out fronts. Cross-architecture **search**
  equivalence is unestablished (`worlds_executed_on_this_host: 0`) and this protocol makes
  no cross-architecture numeric claim outside the halt-only veto of §21.3.
- any claim about Held-out. **Every licence issued under this protocol is scoped to the
  regime characterised by the surface's own published descriptor vector, never to
  "Held-out".**

**Formal non-circularity properties this design exhibits (not asserts):**

| # | Property | How it is checked |
|---|---|---|
| i | **Provenance separation** | Gate Q reads `registry.py`, `generator.py`, `rc5_seeds.py` and the v1-sealed truth-blind taxonomy. It reads **no E2b artifact**. Enforced by the same static data-flow checker §2.3 mandates for the citation checker. |
| ii | **Zero magnitudes in qualification** | The qualification criterion (§18/§20) is a conjunction of **binary** construction and control checks. It contains no numeric threshold that could be moved. |
| iii | **Channel monotonicity** | Gate V's output space is `{STANDS, HALTED}`. For every arm `a`: `P(route = a | E2b) ∈ { P(route = a | ∅), 0 }`. **E2b can subtract; it cannot select.** |
| iv | **Order enforcement, mechanical** | Gate R's verdict is hash-sealed and appended to a hash-chained event log in a commit that is a **strict ancestor** of the first commit containing any Held-out comparison artifact. `git merge-base --is-ancestor`. |
| v | **Measured non-determination (`QND`)** | Before Stage 1 executes: enumerate stratified subpopulations of E2a's sealed corpus that would pass Gate Q's measurable clauses, and verify the routing verdict is **not constant** across them. If it is constant, qualification *is* routing, the design is circular by measurement, and **execution is forbidden**. |

## 5. POPULATION

A new **`calibration`** partition of the benchmark's own registry, appended **last** so that
no existing `case_ordinal` moves.

```
PARTITIONS            = ("development", "held_out", "challenge", "calibration")
PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3, "calibration": 108}
```

| Stratum | Families | Replicates | Worlds | Role |
|---|---|---:|---:|---|
| **G2 (primary)** | F01,F02,F03,F04,F05,F08,F09,F10,F11,F12,F17,F18 | 108 | **1,296** | primary endpoint |
| **NEG (control)** | F07 (mass-only truth), F19 (null worlds, 3-variant cycle) | 108 | **216** | false-structure safety |
| not searched | F06, F13–F16, F20 | — | 0 | not G2-relevant |

**Total searched: 1,512 worlds × 30 seeds = 45,360 searches.**

**Binding population properties:**

- Same generator (`paper_benchmark/generator.py`), same `GENERATOR_VERSION`, same
  `ROOT_SEED = 20260813`.
- Different replicate indices ⟹ different `derive_seed(case_id, ·)` ⟹ statistically
  independent compounds, laws, responses and missingness draws.
- **Nothing in this protocol ever touches, reads, or re-runs a `held_out` or `challenge`
  case.** Enforced by a static import check plus a corpus-path allowlist (P2 BC-23).
- **Seed band.** `rc5_seeds.A35_TOTAL_CASES = 380` and its band
  `[2_100_000_000, 2_100_011_399]` are exhausted. A **new declared disjoint band** is
  registered in `seed_band_registry.DECLARED_BANDS` **in a new module importing the frozen
  ones** — the frozen modules are byte-pinned by `pb_30`/`pb_33`/`pb_34` and must not be
  mutated. Disjointness is checked by the existing `assert_governance_clean`.
- **Ordinal-stability preflight (hard gate, Q1 clause).** Recompute all 380 pre-existing
  `case_ordinal` values **and all 11,400 pre-existing search seeds** before and after the
  amendment and require **byte equality**. If this cannot be made to pass, the amendment is
  abandoned and §5.1's pre-declared fallback is used.

### 5.1 Pre-declared fallback, fixed before attempt 1

If the protocol owner refuses the registry amendment, or the ordinal-stability preflight
fails: use `development` (4 families × 12 G2 replicates = 48 G2 cases) ∪ `challenge`
(3 × 12 = 36) = **84 G2 cases**. This is recorded here, before any attempt runs, so that no
attempt's parameters can be chosen in response to another attempt's result. It costs
decisive power (84 vs 1,296 — see §10's resolving-power table) and `development` carries a
contamination caveat. **Under the fallback, the routing certification of §21 will not be
achievable and the protocol's expected terminal is `ROUTING_INDETERMINATE`; that
consequence is accepted in advance rather than used as grounds to widen a margin.**

## 6. GENERATIVE FACTORS

**REUSED VERBATIM.** The generative factors are the benchmark's own, exactly as
`paper_benchmark/generator.py` implements them for the `held_out` partition. There is **no
new factorial and no sweep**.

| Factor | Setting | Basis |
|---|---|---|
| Condition | the registry's 12 declared G2 conditions, equal weight `w_k = 1/12` | `registry.py`, prospectively declared, results-blind, long before any E2 |
| Truth law | drawn by `generator._law` for that condition | frozen |
| Compound / descriptor draw | `derive_seed(case_id, ·)` | frozen |
| Missingness | the condition's own declaration (F04) | frozen |
| Distractors | the condition's own declaration (F11, F12) | frozen |
| Equivalent-form presentation | the condition's own declaration (F17) | frozen |

**Rationale (§7 of the decision record, R5 + R6).** A crossed sweep is a different
experiment (E4e's question). E2a's three coefficient levels all sit inside the frozen
`rng.uniform(0.25, 0.55)` the benchmark already uses, so the sweep bought no regime coverage
while destroying composition match. Reproducing "the Held-out regime" means reproducing its
**distribution**, not a lattice inside it.

## 7. FAMILY COVERAGE

**Truth-family composition follows the registry and therefore reproduces the Held-out mix
exactly, by construction rather than by reweighting:**

```
affine       9/12   (F01,F02,F03,F04,F05,F08,F11,F12,F17)
saturating   1/12   (F09)
interaction  1/12   (F10)
exponential  1/12   (F18)
mass_power   0/12   -- absent from the target and therefore absent from the primary
```

- **`mass_power` is EXCLUDED from the primary population.** It has no descriptor truth; the
  four-way partition scores it as `SUCCESS`; and it is the single largest source of the
  sealed E2a divergence (107/107 `SUCCESS`, 19.9% of E2a's worlds). It moves entirely to
  the NEG control stratum of §5 and is **excluded from every `S_j`**.
- **Cell-level shortfall is an admissibility failure, not something standardization fixes.**
  Every one of the 12 cells must carry exactly 108 completed worlds (§20 precondition P1).
- **E3's completed verdicts bind and are declared now, before the numbers exist** (P2 BC-22,
  P3 C5): `mass_affine_descriptor` bic_rate 0.553 **MARGINAL**,
  `mass_exponential_descriptor` 0.527 **MARGINAL**, both with
  `search_side_attribution_licensed: false`; `mass_saturating_descriptor` 0.820 and
  `mass_interaction` 1.000 **IDENTIFIABLE**. Since 10 of the 12 conditions carry
  MARGINAL-family truth, **a substantial `NEVER_ON_FRONT` share is expected and is licensed
  in advance by E3**, and may not later be re-read as a novel pipeline generation failure.

## 8. COEFFICIENT REGIMES

**REUSED VERBATIM: the frozen benchmark draw. There is no coefficient ladder and no sweep.**

The coefficient is drawn per world by `generator._law` from `rng.uniform(0.25, 0.55)`,
exactly as every Held-out case carries it. E2a's fixing of the coefficient to the three
lattice points `{0.25, 0.40, 0.55}` was itself a departure from the target regime; it is not
reproduced. The realised coefficient is persisted per world and reported per-regime tertile
as a **diagnostic only** (§19 D4), preserving §2.6's frozen *"per family and per coefficient
regime"* stratification without promoting it to a factor.

## 9. NOISE REGIMES

**REUSED VERBATIM: the benchmark's own noise design, which is a CONDITION AXIS, not a
crossed factor.**

```
F01 noiseless          1/12 weight
F02 moderate noise     1/12 weight
F03 stronger noise     1/12 weight
F04..F18 (9 conditions) the generator's default for that condition
```

This is the single change that removes E2a's largest ceiling artefact: E2a weighted
`noiseless` at 1/3, and the noiseless arm is a success ceiling. Under the registry the same
three noise conditions carry 1/12 weight each.

**Recorded consequence, fixed before execution.** The decision record §1.4 establishes that
conditioning on noise level flips the standardised E2a argmax on a 0.23 pp margin. Under
this protocol **the primary is computed on the full G2 population and is never conditioned
on noise**; noise-conditioned readings are diagnostics (§19 D5) and may not change any
verdict. The conditioning set is fixed here so it cannot be chosen after the counts exist.

## 10. REPLICATE COUNT

**108 replicates per condition ⟹ 1,296 G2 worlds. DERIVED. Full derivation:**

The design must be able to certify a routing lead at least as large as **the programme's own
definition of a material attribution difference**. That magnitude is frozen:

```
delta = 10 / 144 = 0.0694444...        [PE2-4 tolerance, `befca0d` line 466;
                                        `f4c1105` §4; adjudicated in GATE_1_DEFINITIVE.md]
```

ported as a **proportion**, not the literal count 10, per P2 BC-16 (silently reusing "10"
against a different `n` is threshold tuning). The alternative candidate margin —
`delta_dec = 0.5*(pi_C - pi_B) = 0.0556` — is **rejected** because it is computed from the
sealed Held-out attribution and would import Held-out evidence into the sizing of a
licensing instrument.

For a multinomial contrast between two cells of the same partition,

```
Var(pi_1 - pi_2) = ( pi_1 + pi_2 - (pi_1 - pi_2)^2 ) / n
```

The distribution-free bound `pi_1 + pi_2 <= 1` is used rather than a Held-out-informed value,
so that no comparator quantity enters the sizing. Requiring the 95% lower confidence bound
on the lead to exceed 0 with power 0.80 when the true lead equals `delta`:

```
( z_.95 + z_.80 ) * sqrt( (1 - delta^2) / n )  <=  delta

n >= (1 - delta^2) * (z_.95 + z_.80)^2 / delta^2
   = 0.9951775 * (1.6448536 + 0.8416212)^2 / 0.0694444^2
   = 0.9951775 * 6.1825 / 0.00482253
   = 1275.8
```

**1,296 = 12 x 108 is the smallest lattice point >= 1276 with `R` divisible by 3** (so
F19's `(F19A,F19B,F19C)` variant cycle stays balanced overall and in each DEV/EVAL half)
**and by 2** (so the §26 secondary split is exact). Among admissible values the
lexicographically simplest is taken, per the tie-break rule.

**The power level 0.80 is the ONE new magnitude introduced by this protocol.** It is the
conventional default, it is declared before execution, and it affects **only `n`** — no
verdict, no threshold, no label depends on it.

**Resolving power at candidate sample sizes, recorded before execution:**

| n | minimum routing gap certifiable at 80% power | in units of delta |
|---:|---:|---:|
| 84 (§5.1 fallback) | 0.2429 | 3.50 |
| 252 | 0.1448 | 2.08 |
| 576 | 0.0964 | 1.39 |
| **1,296** | **0.0659** | **0.95** |

**Standing preference, recorded before any result (P1 §3.2, adopted):** if the design proves
underpowered, **raise `n`; do not lower the margin.** No amendment lowering `delta` may be
written after a surface exists.

**Determinacy-gap top-up, blinded and pre-declared (P3 §3.3, adopted).** `g` is a nuisance
parameter, not an endpoint. If the sealed determinacy gate reports `g_j > 0.010` for any
`j` on the Stage 1 surface, the surface is extended to `12 x 162 = 1,944` G2 worlds by
generating replicates `r108…r161` from the same frozen generator and the same declared seed
band, and the endpoint is computed **once**, on the full extended surface. The trigger
quantity, the extension size and the extension's world IDs are fixed here, before any world
exists. **The trigger is blind to `S_j`, to the four-way shares and to the routing argmax**,
so it does not inflate alpha. It is **not** a licence to re-read, re-weight, exclude, or
change any margin.

## 11. SEED COUNT

**30 seeds per world. REUSED VERBATIM and NON-NEGOTIABLE.**
`rc5_seeds.A35_SEEDS_PER_CASE = 30`; `befca0d` §2.5 control 2 (*"SEEDS_PER_CASE = 30
unchanged"*); `MURU_V2_E2_PREDECLARATION.md` §6 quantifies every predicate *"for all 30
seeds"*.

**Why it may not be reduced as an economy.** `S_1` is a max over seeds,
`S_1(S) = 1 - (1-q)^S`. Reducing to 15 seeds shifts the estimand by **21.5 pp = 3.09 delta**
— three times the entire margin — so the surface would fail for a reason having nothing to
do with the pipeline. `S_3` is defined through `group_and_select` over exactly 30 retained
candidates and has **no seed-count-invariant reading at all**. Any proposal to change the
seed count is a change of estimand requiring protocol-owner ratification, not an engineering
decision.

Seed derivation: `seed = SEARCH_SEED_BASE_CALIBRATION + case_ordinal * 30 + k`, the frozen
`rc5_seeds` rule applied to the new declared band. The rule is reused; only the band base is
new, and it is registered rather than chosen.

## 12. SEARCH CONFIGURATION

**REUSED VERBATIM. Any deviation is a factor change requiring its own arm.**

| Item | Value | Source |
|---|---|---|
| Engine | PySR 1.5.10 / SymbolicRegression.jl 1.11.3 / PythonCall.jl 0.9.26 | `CLOUD_X86_PARITY_QUALIFICATION.json`, dependency lock 50/50 pins, 0 deviations |
| `PYSR_CONFIG` | frozen, unchanged | `befca0d` §2.5.2 |
| `GRAMMAR_VERSION` | frozen; operators `sqrt, log, square, cube, inv`; `exp` excluded | `befca0d` §2.5.2; DEVIATIONS_P3 D1 |
| Determinism | `deterministic=True`, `parallelism="serial"` | `befca0d` §2.5.2 |
| Threading | single-threaded pinned across Julia / OMP / MKL / OpenBLAS | parity artifact |
| Execution path | `paper_benchmark/rc5_runner`, the **real v1 production path**, with front persistence added and nothing else changed | §4.1 of P1, adopted |
| Within-seed retention | `argmax(score)` = R0 control, `rc5_selection.select_row_label` | `befca0d`; alternatives are E4a arms, not surface parameters |
| Cross-seed grouping | `rc5_selection.group_and_select` on `identity_contract.template_key`, largest-class-wins, lowest-ordinal tie-break | frozen; alternatives are E4f arms |
| Stability gate | `STABILITY_GATE / STABILITY_DENOMINATOR = 20/30` | `structural_acceptance.py` — **imported, not reimplemented** |

**Hard preflight gate, before world 1.** Persist one case; assert all 21 search-side §14
fields present and non-null on every row; assert `rc5_selection.select_row_label` runs on
the persisted frame; assert `admissibility = "DECISION_ADMISSIBLE"` is stamped at row level.
**Fail ⟹ stop, do not generate.** (E2a's rescue-v2 candidate schema dropped `score`,
`loss`, `train_r2`, `grammar_complexity`, `parse_ok`, `effective_support`, `template_key`
and `admissibility`; without `score`, `select_row_label` raises `SeedExecutionFailure` by
design. This gate exists so that failure mode cannot recur silently.)

## 13. PLATFORM / ARCHITECTURE REQUIREMENTS

```
ARCHITECTURE_REQUIREMENT = x86_64 ACCEPTABLE ; ARM64 NOT REQUIRED
```

**The one-sentence declaration P2 BC-12 requires:** *this protocol's qualification and
routing decisions are computed entirely within a single-host surface and make no
cross-architecture numeric claim; the sole cross-architecture comparison is the post-seal
falsification veto of §21.3, whose output space is `{STANDS, HALTED}` and which therefore
cannot license anything.*

**Binding conditions:**

- **A1 — Single-host generation.** All 1,512 worlds generated on one x86_64 host, one
  environment, one hash-recorded dependency lock. **No merging of ARM and x86 worlds**,
  following the precedent `X86_E2A_SEAL.json` sets (`corpus_is_x86_only: true`,
  `historical_worlds_merged: false`).
- **A2 — No wall-clock cap may assign a label, anywhere.** `SIMPLIFY_TIMEOUT_SECONDS = 5`
  is **retired as a classification rule** under this protocol. See §25.
- **A3 — Host-determinism control before world 1.** Re-run the frozen search on a declared
  10-case x 30-seed control subset **twice on this host** and require byte-identical fronts;
  plus the §28 retention-identity regression. *Instrumentation that changes the search is
  not instrumentation.*
- **A4 — Worker count and host load are frozen and load-isolated.** Under a wall-clock cap
  these are scientific variables. A2 removes the dependence; A4 removes it a second time.
  `WORKER_COUNT_CALIBRATION` is re-run on this host and its result is recorded as a
  **declared parameter**, not an engineering note. Concurrency is capped with headroom sized
  for the sympy tail, not the median.

**Disclosed caveat, so nobody can later read more into this than it says.** Cross-architecture
**search** equivalence is unestablished: `worlds_executed_on_this_host: 0` in the parity
artifact, which replayed sealed ARM candidate rows through the x86 *classifier* and never
compared x86 fronts to ARM fronts. Consequently a **tripped veto at §21.3 is not attributable**
between "the surface does not reproduce the Held-out regime" and "an x86 search differs from
an ARM search". **The veto is retained anyway**, because a false HALT is conservative and
removing it would reduce the design's falsification power. The non-attributability must be
stated verbatim in any report of a trip.

**Mandatory hardening, derived from the measured E2a interruption**
(`INTERRUPTION_FORENSICS.json`: `INFRASTRUCTURE_FAILURE__KERNEL_OOM_PLUS_SYSTEMD_SCOPE_TEARDOWN`):
per-worker RSS ceiling enforced in-process (a single python reached ~32 GiB on a 47 GiB
host with no swap); shards in **separate systemd scopes** or an explicit `OOMPolicy`
(`DefaultOOMPolicy=stop` turned one OOM kill into SIGTERM for 11 surviving shards); the
staleness watchdog **smoke-tested in preflight** (it previously died 0 s after launch with
`line 46: File: unbound variable`, so the run was unwatched end to end); world-level
checkpointing with byte-exact resume, **tested before the run rather than during it**.

## 14. FULL FRONT SCHEMA

**REUSED VERBATIM from `befca0d` §2.4. All 28 fields, from inception. D6 is binding: there
is no imputation path and no retrofit path.**

Persisted for **every (world, seed, front row), before retention is applied** — 21 fields:

```
 1  world_id                  8  engine_complexity        15  loss
 2  cell_id                   9  grammar_complexity       16  score
 3  replicate                10  expression_string        17  invalid_fraction
 4  split                    11  parse_ok                 18  effective_support
 5  seed_ordinal_k           12  train_r2                 19  template_key
 6  seed                     13  valid_r2                 20  retained_by_argmax_score
 7  front_rank               14  test_r2                  21  admissibility
```

Extended, without removing or renaming any of the above, by the condition-identifying
fields the new partition requires: `partition`, `case_id`, `family_code`, `variant`,
`condition_kind`, `coefficient_value`, `noise_sd`.

**BC-5 as a mechanical check.** A validator with the 28-field list **hard-coded and frozen
before execution** is run against the corpus at seal time. **Any absent field ⟹ VOID. Any
field written after the seal ⟹ VOID. No field may be back-filled, imputed, or recomputed
after the fact.**

## 15. ADMISSIBILITY FIELD

`admissibility` is **mandatory at the ROW level** and is stamped
`"DECISION_ADMISSIBLE"` on every persisted front row of the Stage 1 surface at write time.

It is the mechanism by which `DECISION_INADMISSIBLE` is enforced **mechanically rather than
by convention** (`befca0d` §2.3), and its absence is the stated reason the E2b front corpus
cannot be reused as the calibration surface (ratification §8).

**Rows produced by Stage 0 are stamped `"EXPLANATORY_ONLY"`** and the static citation
checker must **reject any proposed change whose supporting set contains a Stage 0 identifier
or a Gate V identifier.** This is the same checker that already rejects any change whose
supporting set contains an E2b identifier and no admissible identifier.

## 16. TRUTH-BLIND BOUNDARY

**REUSED VERBATIM from `befca0d` §2.4.**

The search path is **truth-blind at search time**. The seven truth-derived columns are
computed in a **separate scoring pass the search never sees, executed by a distinct
process**, and joined afterwards.

**Enforced, not promised:** a static import check asserts that no module reachable from the
search entry point imports anything truth-derived (`g2_contract`, the oracle, the truth
registry, `discovery.equivalence`). The check runs in preflight and at seal time and its
result is recorded in the manifest.

**Gate Q's qualification clauses are truth-blind by construction** (§18): every one is a
function of the registry, the generator, the seed derivation, and the internal-validity
controls. **None consults the oracle.** The four-way partition is truth-dependent. That a
truth-blind qualification cannot be the truth-dependent attribution is the
functional-independence argument at the qualification layer.

## 17. POST-HOC SCORING PASS

Joined in the separate pass — 7 fields, plus the resolution state:

```
22  discovered_family        25  g2_correct               28  coefficient_regime
23  support_status_vs_truth  26  truth_family
24  family_status_vs_truth   27  truth_support
    resolution_state in { CORRECT , INCORRECT , UNRESOLVED }
```

**Definitions are REUSED VERBATIM and imported, never reimplemented:**
`g2_contract.classify_support`, `g2_contract.classify_family_match`,
`g2_contract.evaluate_g2_event`, `e2_classify.classify_expression`,
`discovery.equivalence.algebraically_equivalent`, `rc5_selection.group_and_select`,
`rc5_selection.select_row_label`, `identity_contract.template_key`,
`g2_contract.wilson_lower_95` / `wilson_upper_95`,
`structural_acceptance.STABILITY_GATE`.

**`g2_contract.py` is byte-unchanged.** The classification **semantics** are byte-unchanged.
Only the control flow around unresolved rows changes (§25), and that change is **strictly
conservative**: it can refuse to decide, never decide differently.

**Classification mode is declared prospectively** (P2 §8 item 20 — an unregistered and
consequential degree of freedom): **lazy classification, executed under the determinacy
bound of §25.** This is sound because under the bound the number of classify calls cannot
change a label — a row is either resolved to its frozen label or explicitly `UNRESOLVED`,
and a world is classified only when the class is invariant over every resolution. Under a
wall-clock cap lazy classification is *not* sound, because the call count differs by stage
(stage A full-scans, stage E scans 30) and therefore exposes stage A to systematically more
timeouts. A2 removes the cap; §25 removes the dependence.

## 18. PRIMARY QUALIFICATION STATISTIC

**There is no numeric qualification statistic.** Qualification is **binary and structural**.
This is a deliberate design decision (decision record §6, decided by R4): frozen authority
contains **no** qualification concept at all — `befca0d` §2.3 is destructive-only — so any
numeric qualification bar would be a newly invented magnitude applied to the surface it will
judge.

```
QUALIFIED  :=  Q1  AND  C-1  AND  C-2  AND  C-3  AND  C-4  AND  C-5
               AND  SCHEMA_COMPLETE  AND  INDETERMINATE_WORLDS == 0
               AND  QND_PASS
```

| Clause | Content | Type |
|---|---|---|
| **Q1 — design provenance** | same generator, same `GENERATOR_VERSION`, same `ROOT_SEED = 20260813`; the registry's twelve G2 conditions at equal weight `w_k = 1/12`; partition disjoint from `held_out` and `challenge`; seed band declared and disjoint under `assert_governance_clean`; **all 380 pre-existing case ordinals and all 11,400 pre-existing search seeds byte-identical after the amendment**; every cell carrying exactly 108 completed worlds; every world exactly 30 completed seeds | construction check, PASS/FAIL, **zero magnitudes, zero outcomes** |
| **C-1 — identity / replay** | the instrumented engine's `argmax(score)`-retained candidate **byte-identical** to the frozen production path's, for every seed on the control world set (§28) | binary |
| **C-2 — negative control** | adversarial constructions **known not truth-equivalent by construction** (`correlated_distractor` for `descriptor`; `descriptor2` for `descriptor`; the descriptor factor replaced by a matched-magnitude constant — `befca0d` §3.6) must be **rejected** by the instrument | binary |
| **C-3 — known-answer control** | worlds whose stage is determinable analytically, run through the full instrument, must recover the known stage. **Includes, mandatorily, a planted correct row that is expensive to canonicalize**, verifying the instrument does not report `NEVER_ON_FRONT`. This is the control that would have caught the defect of §3 item 3 | binary |
| **C-4 — uncapped validation sample** | a pre-declared sample re-scored with **no cap**, requiring **100%** agreement with the bounded instrument. Precedent: 101/101 in the sealed Gate 1 run | binary |
| **C-5 — determinism replay** | a pre-declared subset re-executed, requiring byte-identity. Precedent: 30/30 on this host | binary |
| **QND_PASS** | the routing verdict is **not constant** across E2a subpopulations that would pass Q1's measurable clauses (§4 property v) | binary |

**Why Q2–Q4 of P1's proposal are NOT gating clauses.** P1's truth-blind descriptor
equivalence tests (signal regime, consensus geometry, retained-candidate geometry) would
introduce at least three new magnitudes with no frozen source, and P1 itself discloses that
**E2a would very likely PASS Q3**. A clause that passes the surface it was built to exclude
has no power as a gate. They are retained in full as **mandatory reported diagnostics**
(§19 D9) so that an independent critic can test further descriptors against the same surface
without regenerating it.

## 19. SECONDARY DIAGNOSTICS

All are computed, sealed and published. **None may change any verdict. They exist to explain
a failure, not to rescue one.**

| # | Diagnostic |
|---|---|
| D1 | The frozen four-way partition `(pi_A, pi_B, pi_C+D, pi_E)` with 95% Wilson intervals, and `TV(pi_hat, pi_0)` against the sealed Held-out attribution, reported **descriptively and never as a gate** |
| D2 | The §2.6 conditional metrics verbatim, for continuity with frozen authority: `P_front`, `P_retain_given_front`, `P_win_given_retain`, `rank_of_correct`, `score_gap`, `complexity_gap`, `r2_gap`, `front_size` — per condition and per truth family |
| D3 | Per-condition stage table: `S_j` by each of the 12 conditions, 12 x 3 tests, **Holm–Bonferroni** across them (§27) |
| D4 | Per-coefficient-regime stage table (§2.6's own *"per family and per coefficient regime"*), coefficient tertiles, Holm across the regime family |
| D5 | Noise-conditioned readings of the primary — **explicitly a diagnostic**, because conditioning on noise flips the standardised argmax on the only corpus where it has been computed (decision record §1.4) |
| D6 | `selection_count` distribution and 20/30 stability-gate failure fraction |
| D7 | **P1's counterfactual recovery contrast**, DEV-half only: `rec_retention`, `rec_voting`, `rec_ceiling` over the frozen arm grids (retention R0–R4, voting V0–V2), with `selection_count` inflation **measured, not assumed away**. Non-licensing (decision record §5) |
| D8 | `false_structure_rate` on the NEG stratum for every arm, against E3's frozen `> 0.10` study-validity bar and E6's frozen `Wilson upper <= 0.15 on >= 100 evaluable safety opportunities`. **Reporting a G2 gain without its safety cost is not permitted** (`befca0d` §3) |
| D9 | P1's Q2–Q4 descriptor vector in full: `descriptor_sd`, `mass_range_ratio`, `identity_class_count`, consensus concentration, retained `valid_r2` and complexity |
| D10 | The determinacy report: `g_1, g_2, g_3`, `unresolved_rows / total_rows`, `INDETERMINATE_WORLDS`, escalation cost distribution — **mandatory sealed fields** |

## 20. ACCEPTANCE RULE

Evaluated mechanically from the sealed corpus. Every constant below is fixed at freeze time.

```
CONSTANTS
  delta   = 10/144 = 0.0694444...     [REUSED: PE2-4; befca0d:466; f4c1105 §4]
  alpha   = 0.05 family-wise           [REUSED: f4c1105 §8]
  w_k     = 1/12 for each of the 12 registry G2 conditions   [REUSED: registry.py]
  n       = 1296 G2 worlds, 30 seeds each                    [DERIVED: §10]
  B       = 10,000 bootstrap replicates, stratified by condition
                                       [REUSED: f4c1105 §8]
  bootstrap RNG = derive_seed_v2("bootstrap", "<policy_id>") truncated to 64-bit
                                       [REUSED: f4c1105 §8]
  g_max   = 0.010                      [DERIVED: §0.1]
  CI      = Wilson 95%, g2_contract.wilson_lower_95 / wilson_upper_95, IMPORTED
                                       [REUSED: f4c1105 §7 -- "reused, not reimplemented"]

ENDPOINT  (the frozen four-way partition, in its monotone cumulative parameterization)
  reach_front(w; rho)  = 1 { >=1 of the 30 seeds' Pareto fronts contains a G2-correct row }
  reach_retain(w; rho) = 1 { >=1 seed's argmax(score)-retained candidate is G2-correct }
  reach_win(w; rho)    = 1 { the cross-seed representative is G2-correct }     (= SUCCESS)

  S_j_hat(rho) = SUM_k w_k * ( 1/n_k * SUM_{w in condition k} reach_j(w; rho) )   j = 1,2,3

  pi_hat(rho)  = ( 1 - S1, S1 - S2, S2 - S3, S3 )   over ( A , B , C+D , E )
                 -- identical to the frozen A-E taxonomy by differencing; C+D is
                    MURU_V2_E2_PREDECLARATION §6's LOST_IN_CROSS_SEED

DETERMINACY  (monotone; two evaluations, not 2^U -- see §25)
  rho_bot = every UNRESOLVED row assigned INCORRECT
  rho_top = every UNRESOLVED row assigned CORRECT
  g_j     = S_j_hat(rho_top) - S_j_hat(rho_bot)

ADMISSIBILITY PRECONDITIONS  (all must be YES; each is endpoint-blind)
  P1  COMPOSITION_EXACT     : every one of the 12 conditions has exactly 108 completed
                              worlds; 0 missing, 0 duplicate
  P2  SEEDS_EXACT           : every world has exactly 30 completed seeds
  P3  RETENTION_IDENTITY    : §28 byte-identical on the control world set
  P4  SCHEMA_COMPLETE       : all 28 §14 fields present incl. row-level `admissibility`;
                              0 imputed; 0 written after seal
  P5  HOST_INVARIANT_LABELS : no label is a function of wall-clock time, worker count,
                              host load or CPU model (§25); sealed expression->label table
  P6  DETERMINACY_OK        : g_j <= 0.010 for j = 1,2,3
                              [violation => blinded top-up of §10; NOT a re-read]
  P7  NO_MASS_POWER         : 0 mass_power worlds in the primary population
  P8  TRUTH_BLIND_BOUNDARY  : the §16 static import check passes
  P9  ORDINAL_STABILITY     : all 380 pre-existing ordinals and 11,400 pre-existing seeds
                              byte-identical before and after the registry amendment
  P10 SINGLE_SHOT           : exactly one surface generated; tuning ledger EMPTY

ACCEPTANCE
  QUALIFIED := Q1 AND C-1 AND C-2 AND C-3 AND C-4 AND C-5 AND QND_PASS
               AND P1..P10
               AND INDETERMINATE_WORLDS == 0

  IF NOT QUALIFIED -> terminal SURFACE_NOT_QUALIFIED. No E4 arm licensed.
                      The failing clause(s) are reported. **No margin, endpoint, weight,
                      stratum, exclusion, conditioning set, or population may be revised
                      in response.**
```

**Note that `QUALIFIED` contains no numeric threshold except the determinacy gate.** That is
the design's central governance property: there is no knob in the qualification.

## 21. ROUTING RULE

Fixed-sequence gatekeeping. Routing is read **only if** `QUALIFIED`, never jointly, never
the other way round. This preserves the family-wise error rate without adjustment (§27).

### 21.1 The certification predicate

```
ROUTING_CERTIFIED  :=  argmax over { pi_A , pi_B , pi_C+D } is IDENTICAL under rho_bot
                       and rho_top
                       AND  LCB_95( pi_top - pi_second ) > 0  under BOTH resolutions,
                            with Var(pi_1 - pi_2) = (pi_1 + pi_2 - (pi_1 - pi_2)^2)/n
```

**Why a bare plurality is not sufficient** (decision record §3, decided by R2 and R4): on
the only corpus where the standardised argmax has ever been computed it flips under two
undeclared analyst choices — conditioning on noise level (0.23 pp margin) and correcting the
instrument (4.4 pp margin). A bare argmax has the appearance of zero free parameters and in
fact the maximum hidden discretion. `n = 1296` is sized (§10) so that a lead of `delta` is
certifiable at 80% power.

### 21.2 Gate R — the licensing table, applied verbatim

Evaluated on the **full G2 population**, not the split (`f4c1105` §6: the gate is a
diagnostic fact about the surface's own attribution). Computed by an isolated process which
writes a hash-sealed verdict and appends it to the hash-chained event log **before any
process is permitted to read Gate V**.

| # | Predicate (in this order) | Route | Executable today? |
|---|---|---|---|
| 0 | Any §20 precondition or control fails, or schema incomplete, or `INDETERMINATE_WORLDS > 0` | **VOID** — negative terminal, no retry | — |
| 1 | **Exoneration branch:** `P_retain_given_front` inside a pre-declared band of 1 wherever `P_front` is high | **RC3 WITHDRAWN.** No retention change licensed. STOP | n/a |
| 2 | `NOT ROUTING_CERTIFIED` | **`ROUTING_INDETERMINATE`.** No E4 arm licensed. Report and stop | n/a |
| 3 | certified argmax = `B` (`LOST_IN_RETENTION`) | RC3 confirmed → **licenses E4a** | **Yes** — `f4c1105` is a complete operational freeze |
| 4 | certified argmax = `A` (`NEVER_ON_FRONT`) | RC4 confirmed → route **through E3's completed per-cell verdicts** | **Partially.** `mass_saturating_descriptor` and `mass_interaction` only. **BLOCKED** for `mass_affine_descriptor` and `mass_exponential_descriptor` (MARGINAL, `search_side_attribution_licensed: false`) — which is 10 of the 12 conditions |
| 5 | certified argmax = `C+D` (`LOST_IN_CROSS_SEED`) | RC7 → **E4f** (voting / canonicalization) | **NO.** Terminal `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` |

**Row 5 is pre-labelled non-executable, before execution and before any count exists**
(P2 BC-21). E4f has **no** standalone preregistration, **no** numeric
`false_labelling_rate` ceiling anywhere in the corpus, **no** `k_inflation` ceiling, **no**
population declaration, **no** DEV/EVAL split, **no** statistical procedure and **no**
identity/replay control (`FORWARD_AUTHORITY_MAP.md` §6: *"not executable as frozen authority
stands"*). **Inventing those ceilings after the route is known is prohibited.** Row 5 is
pre-labelled precisely so that a designer who notices it cannot be tempted to reshape the
table to make row 5 unreachable or fold it into row 3.

### 21.3 Gate V — the falsification veto, AFTER the seal

Executed **once**, by a **different adjudicator**, after Gate R's verdict is hashed and
chained. It compares the surface's four-way partition against the sealed Held-out
attribution `SUCCESS 4 / LOST_IN_CROSS_SEED 71 / LOST_IN_RETENTION 55 / NEVER_ON_FRONT 14`
(ratified D1) at total-variation tolerance `delta = 10/144` (REUSED; ported as a proportion
per BC-16).

```
Output space:  { STANDS , HALTED }   -- nothing else.

  TV(pi_hat, pi_0) <= delta   ->  STANDS.   Gate R's verdict takes effect.
  TV(pi_hat, pi_0)  > delta   ->  HALTED.   The routing seal is stamped NON_LICENSING,
                                            all E4 arms remain suspended, and the
                                            divergence is escalated to the protocol owner.
```

**Binding constraints on Gate V:**
- A **passing** veto is **SILENT**. It is reported only as *"the falsification hook did not
  trip"*. It may **never** appear in the citation set of any change and may never be
  described as support. The static citation checker must reject any change citing it
  (P2 BC-10, PM-5).
- A **tripped** veto → **VOID**, never a re-route. It may not be used to select a different
  branch (P2 F4).
- Any report of a trip must state verbatim that a trip is **not attributable** between "the
  surface does not reproduce the Held-out regime" and "an x86 search differs from an ARM
  search", because cross-architecture search equivalence is unestablished (§13).

### 21.4 What a licence is, and is not

A licence names **one arm at one parameter setting**, not an arm family. Every licence
carries three binding riders:

1. **The E6 false-structure ceiling is a precondition, not a report.** An arm that recovers
   cases and breaches `Wilson upper <= 0.15 on >= 100 evaluable safety opportunities` is not
   licensed. **If E6 cannot supply a ceiling at decision time — and E6 is self-blocked
   pending exactly this hook — every licence is CONDITIONAL and NON-EXECUTABLE.** This
   circular dependency must be resolved by the protocol owner **before freeze**, not
   discovered at the end.
2. **The licence is scoped to the regime characterised by the published descriptor vector
   (D9), never to "Held-out".**
3. **If the four-way partition and the D7 recovery contrast disagree, that disagreement is
   itself a pre-declared reportable finding and REDUCES the licence to conditional.** It is
   the direct generalisation of `H_partial`, stated first-class here for the same reason
   `befca0d` §2.1 stated `H_partial` first-class: so it cannot be discovered and then
   quietly absorbed.

## 22. FAILURE RULE

| # | Condition | Terminal |
|---|---|---|
| F0 | Stage 0 gate fails (`g_j > 0.010` after uncapped escalation, or `INDETERMINATE_WORLDS > 0`) | **`T-INSTRUMENT-UNBOUNDED`** — the G2 contract as frozen is not decidable at finite cost on this class of population. A finding about the **contract**, not the pipeline. Stage 1 is forbidden |
| F1 | Any control (C-1…C-5) fails, or any precondition P1–P10 fails | **VOID.** Negative terminal. **No retry** |
| F2 | `INDETERMINATE_WORLDS > 0` after escalation | **VOID** |
| F3 | Schema incomplete at seal, or any field written after seal | **VOID.** No back-fill (D6) |
| F4 | `QND` fails — the routing verdict is constant across all Gate-Q-passing E2a subpopulations | **`CIRCULAR_BY_MEASUREMENT`.** Qualification *is* routing. **Do not execute** |
| F5 | Q1 fails on both pre-enumerated attempts (amendment and §5.1 fallback) | **`NO_ADMISSIBLE_SURFACE_EXISTS`.** Since Q1 is a construction check this implies a mechanical failure (ordinal drift, band collision, generator version mismatch) — **the benchmark needs auditing before anything else proceeds** |
| F6 | Not `ROUTING_CERTIFIED` | **`ROUTING_INDETERMINATE`.** Not a null result: the finding that G2 loss is **jointly attributable across stages and no single-factor repair is licensable in this regime**. The honest forward path is a jointly-varying design under separate authorisation, with `befca0d` §3's warning that admissibility is not additive |
| F7 | Route determined but arm not executable (rows 4-partial, 5) | **`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`.** A legitimate, **pre-labelled** terminal |
| F8 | Gate V trips | **`HALTED` / VOID.** The routing seal is stamped `NON_LICENSING`. Never a re-route |
| F9 | More than one surface generated, or the tuning ledger is non-empty, or any protocol amendment is written after the first surface exists | **VOID.** Retry converts the veto into a fitting objective |
| F10 | Any of D3's eight `EXPERIMENTAL_REENTRY_RESOLUTION` items unmet at verdict time | **No re-entry, regardless of the route** |

**There is no rehabilitation path from any VOID.** A non-empty tuning ledger is not a
disclosure that rehabilitates the design; it is the measurement of how much fitting occurred.

## 23. TIE RULE

**REUSED VERBATIM from `f4c1105` §4, adopted rather than restated, so that no boundary case
is silently redefined.**

- **"Strict plurality" means strictly greater than each of the other aggregates. Equality is
  NOT a plurality.**
- A tie, a near-tie, or any configuration failing `ROUTING_CERTIFIED` falls to
  **`ROUTING_INDETERMINATE`** (§21.2 row 2): every metric is reported, and the adoption rule
  is **suspended pending a *named* tie-breaking review**.
- **Inventing a tie-break after seeing counts that produced a tie is prohibited** (P2 PM-12).
  The frozen rule already covers this branch and must be adopted verbatim.
- **Adoption tie-break order, where an adoption set genuinely exists:** fewest free
  parameters, then lowest false structure. REUSED from `befca0d` §3.1.
- **Cross-seed grouping tie-break:** largest-class-wins, **lowest-ordinal** tie-break, inside
  `rc5_selection.group_and_select`. REUSED, imported, not reimplemented.

## 24. INVALID / UNEVALUABLE HANDLING

**All dispositions are declared here, before execution, including their arithmetic effect on
every denominator** (P2 BC-13).

| Category | Treatment |
|---|---|
| `UNRESOLVED` row | **Its own state. Never folded into any substantive class, never imputed, never dropped, never defaulted to not-correct.** Enters the endpoint through the two-sided determinacy bound of §25 |
| `INDETERMINATE` world (class not invariant after uncapped escalation) | **Its own state**, counted and sealed. `INDETERMINATE_WORLDS > 0` ⟹ **VOID** (§22 F2). Never silently folded |
| Parse failure (`parse_ok = false`) | `INCORRECT`. Deterministic, host-invariant, already the frozen semantics. **Not** `UNRESOLVED` |
| `invalid_fraction > MAX_INVALID_FRACTION = 0.005` | Excluded from the retained set by the frozen rule (`befca0d` §3.4), **plus** the direct check that an invalid candidate never outscores a valid one. REUSED |
| Search execution failure (world produces no front) | **Regenerate under the same frozen seed.** A missing world breaks the exact-composition precondition P1. Count reported |
| Seed `EXECUTION_FAILURE` / `COMPLETED_NO_CANDIDATE` | Handled by the frozen `build_seed_selections` path unchanged; counted per world; a world with fewer than 30 completed seeds fails precondition P2 |
| World failing any control | **Quarantined and reported, never silently dropped.** REUSED from `befca0d` §2.5.3 as the general failure discipline |
| Denominator convention | Every rate in this protocol has denominator `n = 1296` (G2 primary) or the NEG stratum size. `INDETERMINATE` worlds are reported **separately** and are **never folded into "not recovered"**. The sensitivity of every routing comparison to **both** extreme resolutions is reported alongside every point estimate, exactly as the Gate 1 adjudication reported its 2^4 enumeration |

## 25. TIMEOUT / RESOURCE HANDLING

> **THE GOVERNING RULE OF THIS SECTION: NO WALL-CLOCK CAP, MEMORY CAP, WORKER-COUNT CHOICE,
> HOST-LOAD CONDITION OR CPU MODEL MAY DECIDE A SCIENTIFIC LABEL ANYWHERE IN THIS PROTOCOL.**

`SIMPLIFY_TIMEOUT_SECONDS = 5` is **retired as a classification rule.** It is the documented
root cause of `NEW_CLOUD_HOST_PARITY_FAILED` — *"the same unmodified classifier assigns a
different scientific label to the same expression purely as a function of host speed"*,
`not_floating_point: true` — and, per §3 item 3, it decided 314 row labels inside 73 of E2a's
122 stage-A worlds in the direction that determines the stage.

### 25.1 The determinacy bound (P2 §3.2's MANDATORY CORRECTION, all six conditions)

Executed through the machinery of `scripts/e2b_bounded_determinacy_evaluator.py`, already
hostile-audited in the sealed Gate 1 adjudication.

1. `g2_contract.py` and the classification **semantics** are **byte-unchanged**; only the
   control flow around unresolved rows changes.
2. The bound is proven to **over-approximate**: a class is emitted **only when it is
   invariant over every resolution of every unresolved row**. Under the monotonicity lemma
   this reduces to two evaluations rather than `2^U` — `correct_on_front` and
   `retained_correct` are disjunctions over row labels, hence monotone; the cross-seed
   representative is selected by `identity_contract.template_key` grouping and
   **never reads `g2_correct`**; `retained_by_argmax_score` is a score comparison, also
   label-independent. So a resolution can only move a world **weakly later** in the frozen
   order `A ≺ B ≺ C/D ≺ E`.
3. Rows that are **decisive** under that enumeration are **escalated to completion, not
   guessed**.
4. A residual undecidable world is emitted as explicit `INDETERMINATE`, never folded, with
   the pre-declared bar `INDETERMINATE_WORLDS == 0` above which the run is **VOID**.
5. The implementation is validated against **uncapped ground truth** on a pre-declared
   sample, with the sample and the pass bar (**100%**) frozen before execution. Precedent:
   101/101.
6. The whole correction is **hash-frozen before any new world is generated** and applies
   **identically** to every surface any comparison touches — including Stage 0.

### 25.2 The two-tier budget

- **Tier 1 — CPU time, not wall clock.** `time.process_time` budget of **60 s per distinct
  expression**. **DERIVED:** 12x the retired frozen 5 s, expressed in CPU time so it is not a
  function of load or co-tenancy. It is a **cost** bound only; exceeding it produces
  `UNRESOLVED`, **never a label**.
- **Tier 2 — uncapped escalation.** Any expression still unresolved **and decisive** — i.e.
  whose resolution changes some world's stage under the monotone bound — is escalated with
  **no cap**. Precedent: Gate 1 escalated 6 decisive expressions at 5.5–21.8 s each.
- The cap exception derives from **`BaseException`**, deliberately, so that `g2_contract`'s
  seven `except Exception: return None` handlers cannot swallow it and silently turn a cap
  into `SUPPORT_UNRESOLVED → not-correct`.
- **Sealed expression → label table.** Labels are computed once, escalated to completion,
  **hashed and committed**. Classification at scoring time is then a lookup, so the label is
  a pure function of the expression string. Cross-architecture parity becomes a hash
  comparison rather than a re-run.

### 25.3 Resource handling that is explicitly NOT a classification

Per-worker RSS ceiling enforced in-process; separate systemd scopes per shard; smoke-tested
watchdog; world-level checkpointing with byte-exact resume; frozen and load-isolated worker
count (§13 A4). **A world lost to an infrastructure failure is regenerated under the same
frozen seed and reported; it is never reclassified, imputed, or dropped.**

## 26. DEV / EVAL SEPARATION

Three distinct separations, for three distinct purposes. Each is deterministic,
pre-declared, stratified, and uses **no RNG**.

**(1) Engineering DEV — free, and it should be taken (P3 §7.3).**
`DEV_ENGINEERING = the sealed E2a corpus`. E2a is fully seen, hostile-audited, and ratified
as **invalidated for calibration (D5)**, which makes it worthless as evidence and ideal as an
engineering dev set. The bounded evaluator, escalation protocol, schema validator, bootstrap
harness, memory governor and runtime profiling are developed and debugged against it at
**zero additional scientific compute and zero leakage** — nothing about E2a can contaminate a
decision it is already barred from licensing. **The analysis code is frozen and hashed
against E2a before the first Stage 1 world is generated.**

**(2) The primary is computed on the FULL G2 population, not on a split.**
REUSED from `f4c1105` §6: the gate is a diagnostic fact about the surface's own attribution.
No split is required for the alpha to be valid, because the qualification rule, the margin,
the routing rule, the conditioning set and the endpoints are **all frozen before any world
exists**, and qualification → routing is fixed-sequence gatekeeping.

**(3) Arm-selection DEV/EVAL, for the SECONDARY recovery contrast only (D7).**
Deterministic by replicate index, fixed before any front is read:

```
DEV_ARM  = replicates r000 .. r053   (648 G2 + 108 NEG)
EVAL_ARM = replicates r054 .. r107   (648 G2 + 108 NEG)
```

`R*` and `V*` are **selected on DEV_ARM** by the frozen `befca0d` §3.1/§3.6 decision rule
(*simplest rule whose G2 improvement over control has a Wilson lower bound above 0 and whose
`false_structure_rate` stays under the E6 ceiling; ties broken by fewest free parameters,
then lowest false structure*), and **measured on EVAL_ARM**. Without this split the contrast
is structurally biased toward retention, which has 4 arm-types spanning 9 parameter settings
against voting's 2 — a bias that would be invisible and would point at E4a.

**EVAL is scored exactly once. There is no second look.**

## 27. MULTIPLE-COMPARISON CONTROL

**REUSED, two-layer structure, exactly as `f4c1105` §8 fixes it.**

- **Primary: no adjustment, and this is a theorem rather than a convention.** Qualification
  is a **conjunction** of binary structural clauses, and qualification → routing is a
  **fixed-sequence (hierarchical gatekeeping)** procedure, which preserves the family-wise
  error rate without adjustment. Routing is read at full alpha and **only if** qualification
  passes. Adjusting here would make an already-conservative procedure more conservative and
  inflate the required `n` for nothing.
- **Routing certification: one comparison** (`pi_top` vs `pi_second`), evaluated at both
  extreme resolutions. One endpoint, one alpha, one decision.
- **Secondary diagnostics D3 and D4:** development-only pre-reduction of internal grids,
  **plus Holm–Bonferroni at `alpha = 0.05`** across the head-to-head comparisons within each
  family, with **unadjusted CIs reported alongside**. REUSED verbatim.
- **Secondary recovery contrast D7:** simultaneous paired intervals (exact McNemar on
  discordant pairs plus case-level bootstrap 95% CI, `B = 10,000`, resampling within
  EVAL_ARM only), **Holm-adjusted across the three comparisons**, family-wise
  `alpha = 0.05`. REUSED from `f4c1105` §8.
- **D1–D2, D5–D6, D8–D10 are descriptive** and carry no adjustment because they gate nothing.

## 28. REPLAY / IDENTITY CONTROL

**REUSED VERBATIM. `befca0d` §2.5.1; `f4c1105` §9.1. A hard gate before any record is used —
including before any record is *reported*.**

- **C-1 Retention identity.** The instrumented engine's `argmax(score)`-retained candidate
  must be **byte-identical** to the frozen production path's, for **every seed** on the
  declared control world set. *"Instrumentation that changes the search is not
  instrumentation."* Answerable against the production pipeline, not against the attribution.
- **R0 replay self-consistency** (`f4c1105` §9 control 1). The re-scoring pipeline scored
  under R0 must reproduce the surface's own sealed A/B/C/D/E counts and `selection_count`
  values **exactly**. Any discrepancy is a **defect in the implementation, not a finding**,
  and blocks all results.
- **C-5 Determinism replay.** A pre-declared subset re-executed on this host, requiring
  byte-identity. Precedent: 30/30.
- **Host determinism, twice** (§13 A3): the 10-case x 30-seed control subset run twice with
  byte-identical fronts.
- **Two-architecture label parity** as a proof obligation rather than a gamble: under §25.2's
  sealed expression → label table the label is a pure function of the expression string, so
  a pre-declared audit sample re-classified on a second architecture must return **0**
  mismatches by construction. If a second architecture is unreachable, this obligation is
  recorded as **discharged by construction and unverified by execution**, and stated as such.
- **Artifact reconciliation.** A manifest with SHA-256 for every produced artifact, verified
  after writing, with a recorded statement that **no sealed evidence was modified** —
  matching the discipline at `ARTIFACT_SHA256.txt` and `RATIFICATION_VERIFICATION.json`.

## 29. INDEPENDENT ADJUDICATOR

**Registered before execution (D3 item 6). REUSED structure: the one the sealed Gate 1
adjudication actually executed.**

| Role | Requirement |
|---|---|
| **ADJUDICATOR** | **Named before execution.** Independent of the design author. Applies the frozen §20/§21 predicates mechanically to the sealed artifacts and produces a **signed verdict**. May not modify any predicate. May not see Gate V before sealing Gate R |
| **GATE-V ADJUDICATOR** | A **different** named party. Executes §21.3 **once**, after Gate R's hash is chained. Output space `{STANDS, HALTED}`. No other output is accepted |
| **CRITIC_A (scientific)** | Independent. Must return PASS |
| **CRITIC_B (governance / leakage)** | Independent. Must return PASS |

**Order enforcement is mechanical, not procedural.** Gate R is computed by an isolated
process which writes a hash-sealed verdict and appends it to a hash-chained event log
(the `AUTONOMOUS_RUN_EVENT_LOG.jsonl` pattern). Out-of-order execution is **detectable from
the chain**. `git merge-base --is-ancestor <route-commit> <gate-v-commit>` must hold.
*"We looked first"* becomes a falsifiable claim rather than a promise.

**`UNRESOLVED_DEFECTS` must be 0 at verdict time**, as it was at Gate 1.

## 30. HOSTILE REVIEW REQUIREMENT

**Two hostile reviews, twice: against the design before freeze, and against the result before
the verdict is accepted.** Matching the CRITIC_A / CRITIC_B discipline the Gate 1
adjudication used, in which CRITIC_A broke through on the mapping, CRITIC_B refuted the
break-through, and CRITIC_A withdrew.

**Mandatory attack surface for the pre-freeze review, enumerated so it cannot be skipped:**

1. **Attack Q1's provenance argument.** An independent agent, **blind to the composition
   reweighting**, must re-derive the population rule from `registry.py` and the v1-sealed
   taxonomy alone. If that agent reaches the same twelve-condition partition, the charge
   *"you matched composition because you saw that matching composition moves E2a toward
   E2b"* is answered by **replication rather than by argument**. If it does not, the charge
   stands and the population must be re-argued before freeze.
2. **Attack the determinacy bound's monotonicity lemma** (§25.1 condition 2) at the code
   level, not the prose level.
3. **Attack the claim that E2a's Gate-2 predicate is invariant** (decision record §1.2) by
   attempting to construct a resolution under which a `B` world moves.
4. **Attack `QND`** — attempt to exhibit a Gate-Q-passing subpopulation family on which the
   routing verdict is constant.
5. **Attack the single-shot claim** — count surface manifests; audit the tuning ledger; check
   `git merge-base` ancestry for both BC-1 and BC-19.
6. **Attack every branch of §21.2 for a route to a non-executable arm that is not
   pre-labelled.**

**A review that returns PASS without engaging all six is not a hostile review and does not
discharge this section.**

## 31. HASH / FREEZE PROCEDURE

**D3 item 7: results-blind freeze before any new outcome is inspected.**

1. **Freeze commit.** This document, the routing table, the acceptance predicate, the failure
   rules, the tie rules, the schema validator's hard-coded field list, and **all analysis
   code** are committed and their SHA-256 hashes recorded in a manifest. The freeze commit
   must be a **strict ancestor** of the first data commit. Verified by
   `git merge-base --is-ancestor` and by re-verifying every recorded hash.
2. **Tuning ledger.** A ledger recording every parameter changed after this freeze, with the
   reason and the evidence consulted, is registered at the freeze commit. It **must be empty
   at execution time**. A non-empty ledger **voids the surface** (§22 F9).
3. **Generator ancestry (P2 T-a/T-b/BC-3).** Every generator parameter is either bit-identical
   to a value already fixed in a commit that is a **strict ancestor of the first commit
   containing any E2b front**, or is set by a registered **rule** that provably never reads
   Held-out (here: *"the value the frozen registry already declares for the `held_out`
   partition"*). **The rule is registered, and the value is derived from it** — never chosen.
4. **Surface count.** An auditable integer. **Exactly one.**
5. **Order seals.** Gate R's verdict is hashed and appended to the hash-chained event log
   before Gate V exists. Gate V's artifact commit must be a strict descendant.
6. **Post-execution reconciliation.** SHA-256 manifest for every produced artifact, verified
   after writing; `git status` on `results/` empty for all pre-existing sealed evidence;
   an explicit recorded statement that **no sealed evidence was modified**.
7. **Stage 0 is sealed separately** and is stamped `EXPLANATORY_ONLY` at the record level.
   The static citation checker must reject any change citing a Stage 0 identifier.

## 32. TERMINAL STATES

The complete, mutually exclusive, exhaustive terminal set. **All are declared before
execution. Several of them are honest scientific results and are not failures of this
protocol.**

| Terminal | Meaning | Re-entry? |
|---|---|---|
| `T-INSTRUMENT-UNBOUNDED` | Stage 0 gate fails. The G2 contract as frozen is not decidable at finite cost on this class of population. A finding about the **contract** | No. Stage 1 forbidden |
| `CIRCULAR_BY_MEASUREMENT` | `QND` fails. Qualification determines routing. The design is withdrawn | No |
| `NO_ADMISSIBLE_SURFACE_EXISTS` | Q1 fails on both pre-enumerated attempts. Implies a mechanical/benchmark defect requiring audit before anything else proceeds | No |
| `SURFACE_NOT_QUALIFIED` | A control, precondition or schema clause fails. Single shot, **no retry**, no amended protocol | No |
| `VOID` | Any §22 failure rule fires | No |
| `ROUTING_INDETERMINATE` | Certification fails. **Not a null result:** the finding that G2 loss is jointly attributable across stages and **no single-factor repair is licensable in this regime**. E4's one-factor-at-a-time framing is then inadequate for this regime, and the honest forward path is a jointly-varying design under separate authorisation | No |
| `RC3_WITHDRAWN` | The exoneration branch fires: the retention rule is exonerated and no retention change is licensed. **This branch exists so the protocol can conclude "the retention rule is fine" — an outcome the licensing table must be able to reach, or it is not a test** | No |
| `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` | A route is certified to E4f, or to E4b/c/d on a cell E3 has ruled MARGINAL. **Pre-labelled** | No, pending a separate operational preregistration |
| `HALTED` | Gate V trips after the route is sealed. Routing seal stamped `NON_LICENSING`; all E4 arms remain suspended; escalated to the protocol owner. **The most scientifically interesting failure available**: the Held-out *design* is reproduced but the Held-out *behaviour* is not | No |
| `E4A_LICENSED_AT_<arm>` | `ROUTING_CERTIFIED → B`, Gate V `STANDS`, E6 ceiling available and met, all eight D3 items satisfied | **Yes**, at one arm at one parameter setting, scoped to the published descriptor vector |
| `E4_GENERATION_LICENSED_<cells>` | `ROUTING_CERTIFIED → A`, restricted to `mass_saturating_descriptor` and `mass_interaction` only | **Partial**, per cell |
| `T1 — NO_ADMISSIBLE_QUALIFICATION_EXISTS` | The protocol owner concludes that `befca0d` §2.3's destructive-only rule combined with D6's inadmissibility admits no qualification that is both non-circular and non-vacuous. The programme publishes the divergence and stops. **A legitimate scientific result already present in the decision tree** (*"No v2 architecture is proposed at all"*) | No |

**Not in this list, and explicitly unreachable:** `T9 —
REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY`. T9 is forced **if and only if** Held-out-matching
qualification is retained as a requirement. This protocol abandons it (§4, §18), so T9 does
not arise. Any future amendment that re-introduces a quantitative Held-out-matching
qualification **re-arms T9 automatically**, and no weaker substitute comparison may be used
to dodge it.

---

## 33. THRESHOLD INVENTORY — EVERY NUMBER IN THIS PROTOCOL

**Reused verbatim from frozen authority (with citation):**

| Value | Meaning | Source |
|---|---|---|
| `10/144 = 0.069444` | materiality tolerance; §10 sizing; §21.3 veto tolerance | PE2-4; `befca0d`:466; `f4c1105` §4; `GATE_1_DEFINITIVE.md` |
| `30` | seeds per case | `rc5_seeds.A35_SEEDS_PER_CASE`; `befca0d` §2.5 control 2 |
| `12` | registry G2 conditions, `w_k = 1/12` | `registry.py` |
| `20/30` | stability gate | `structural_acceptance.py` — imported |
| `0.005` | `MAX_INVALID_FRACTION` | `befca0d` §3.4 |
| `95%` Wilson | CI method | `f4c1105` §7 — imported, not reimplemented |
| `alpha = 0.05` | family-wise, Holm–Bonferroni on secondaries | `f4c1105` §8 |
| `B = 10,000` | bootstrap replicates; `derive_seed_v2("bootstrap", id)` | `f4c1105` §8 |
| `0.80 / 0.50 / 0.10` | E3 identifiability and study-validity bars | `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN` §5; already applied, verdicts bind |
| `Wilson upper <= 0.15` on `>= 100` opportunities | E6 safety ceiling | decision tree §3, A.2 — the only numeric safety ceiling in the corpus |
| `0` indeterminate cases | determinacy bar | P2 §6.2; demonstrated achievable at Gate 1 |
| `100%` | uncapped-validation agreement bar | Gate 1 precedent 101/101 |
| A–E taxonomy, decision order, C/D refinement | endpoint definition | `MURU_V2_E2_PREDECLARATION` §6 |
| Gate-2 predicates, exoneration branch, tie branch | routing table | `f4c1105` §4 — adopted verbatim |
| Adoption tie-break: fewest free parameters, then lowest false structure | | `befca0d` §3.1 |
| Improvement bar: paired 95% lower bound `> 0` | | `f4c1105` §6.1; `befca0d` §3.1 |
| 28-field schema | corpus requirement | `befca0d` §2.4 |
| `PYSR_CONFIG`, `GRAMMAR_VERSION`, `deterministic=True`, `parallelism="serial"` | search configuration | `befca0d` §2.5.2 |

**Derived, with the derivation shown inline:**

| Value | Meaning | Derivation |
|---|---|---|
| `n = 1296 = 12 x 108` | G2 replicate count | §10: smallest lattice point ≥ 1275.8 with `R` divisible by 6, from `n >= (1-delta^2)(z_.95+z_.80)^2/delta^2` using the **distribution-free** bound `pi_1+pi_2 <= 1` |
| `216 = 2 x 108` | NEG control worlds | §5: same replicate count on the two negative-control families; ≥ 100 evaluable safety opportunities as E6's frozen ceiling requires |
| `g_max = 0.010` | determinacy gate | §0.1: largest gap keeping the required `n` within a factor 1.4 of its `g = 0` value; the sealed E2a corpus fails it by 4–6x |
| `60 s` CPU tier-1 budget | cost bound, never a label | §25.2: 12x the retired 5 s, expressed in CPU time so it is not a function of load |
| `1944 = 12 x 162` | blinded top-up size | §10: `1.5 x 1296`, fixed before any world exists, triggered blind to every endpoint |

**Newly introduced magnitudes: ONE.**

| Value | Meaning | Where it can affect a verdict |
|---|---|---|
| `power = 0.80` | conventional default in the §10 sample-size derivation | **Nowhere.** It affects only `n` |

---

## 34. PRE-RECORDED EXPECTED OUTCOME

Recorded here, before execution, so the record shows the design was not chosen for its
answer. The full reasoning and probability assignments are in `SYNTHESIS_DECISION_RECORD.md`
§11.

**Stage 0:** corrected E2a attribution near `A ≈ 60–90, B ≈ 230–255, C+D ≈ 100–104,
E ≈ 119–122`, `B` plurality intact, divergence from Held-out **larger** than the sealed
corpus's. `g <= 0.005` and `0` indeterminate worlds, i.e. Stage 0 **passes** its gate
(~70%).

**Stage 1:** `pi_A < 0.15`; `pi_E < 0.10`; `pi_B` and `pi_C+D` both in `[0.35, 0.52]` with
**`|pi_B - pi_C+D| < delta`**.

**Predicted terminal: `ROUTING_INDETERMINATE`** (~55%), then `ROUTING_CERTIFIED → B`
followed by a Gate V **HALT** (~30%), `ROUTING_CERTIFIED → C+D` terminating at
`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` (~10%), `VOID` (~5%).

**I therefore expect this protocol NOT to reach E4 re-entry on any branch, and I am
proposing it anyway.** An honest `ROUTING_INDETERMINATE` is a valid scientific and
governance result, and §22 F6 already states what it means. The alternative — a bare
plurality on a near-tie — is exactly the error that produced the v1 attribution disaster in
which 124 of 144 cases were relabelled.

**The disclosure that makes this claim checkable.** The design most likely to deliver
re-entry was on the table and was rejected: P3's fixed-target TOST at `n = 576`, whose own
author labels its framing anti-conservative. It was rejected under decision rules **R3**
(keeps Held-out evidence out of positive licensing) and **R8** (minimizes leakage and
circularity) — **not** because it was expected to fail, but because it was expected to pass.

---

**TERMINAL STATE OF THIS DOCUMENT: PROTOCOL TEXT, FROZEN, NOT EXECUTED.**
**No world generated. No partition amended. No search executed. No re-entry licensed.**
