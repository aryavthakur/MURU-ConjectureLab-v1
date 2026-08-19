# P3 — STATISTICAL / IDENTIFIABILITY

**Role.** Agent P3 on the MURU v2 design council. This document specifies the
qualification statistic, uncertainty treatment, equivalence margin, sample design,
multiplicity control, identifiability controls, UNRESOLVED handling, and dev/eval
posture for the **replacement calibration surface** required by
`MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §5 (EXPERIMENTAL_REENTRY_RESOLUTION items
1–8).

**Status.** Prospective post-Gate-1 design input. **Not** historically preregistered.
Written before any world of the replacement surface exists.

**Disclosure of what I looked at.** I computed diagnostics on the *already-sealed and
already-invalidated* E2a corpus (`results/e2/run_x86_e2a_v1`, D5 = INVALIDATED AS A
CALIBRATION SURFACE) and on the sealed E2b/Held-out attribution (D1, ratified). Every
such number is reported below in full, including the ones that argue against my own
recommendation. No quantity in the acceptance rule is derived from any of them except
the sealed Held-out comparator itself, which is the fixed calibration target by
construction. The margin is a frozen quantity reused verbatim.

---

## 0. Executive answer

| Element | Recommendation |
|---|---|
| **Primary endpoint** | The **cumulative stage-survival vector** `S = (S₁, S₂, S₃)`, standardized to the Held-out cell mix |
| **Comparator** | Fixed sealed Held-out target `S⁰ = (130/144, 75/144, 4/144) = (0.9028, 0.5208, 0.0278)` |
| **Test** | Three-component **intersection–union** equivalence test (TOST), α = 0.025 one-sided per side ⇒ 95 % two-sided interval containment |
| **Interval method** | Stratified nonparametric **BCa bootstrap over worlds** (20 000 reps), **Wilson** score interval as the closed-form cross-check on unstandardized components |
| **Margin** | **δ = 10/144 = 0.069444** (6.944 pp) — the frozen PE2-4 / Gate-1 materiality tolerance, reused verbatim as a proportion |
| **UNRESOLVED** | Monotone determinacy bound; acceptance must hold at **both** extreme resolutions |
| **n** | **576 worlds = 12 Held-out cells × 48 replicates × 30 seeds = 17 280 searches** (≈ 42 CPU-hours) |
| **Seeds/world** | **30, mandatory.** Reducing to 15 shifts `S₁` by 21.5 pp = 3.09 δ. Not negotiable. |
| **Multiplicity** | None needed on the primary (IUT preserves α). Holm–Bonferroni on the 12 secondary per-family tests. |
| **Dev/Eval** | **DEV = the existing E2a corpus** (already seen, already invalidated — perfect engineering dev set, zero extra compute). **EVAL = the new 576-world surface, scored exactly once.** |
| **Biggest threat** | The **stage ORDERING is not identified on any existing surface.** Standardization closes 68-77 % of the E2a/Held-out magnitude but leaves the argmax unresolved (95 % CI on the B-C gap spans +-15 pp). Runner-up: the wall-clock `SIMPLIFY_TIMEOUT` is host-speed-dependent and directionally biased. |

---

## 1. THE QUALIFICATION STATISTIC

### 1.1 Evaluation of the four candidate framings

**(a) Equivalence on the full 4-category distribution (multinomial / TV / L1).**
*Verdict: SECONDARY, not primary.* A total-variation gate
`TV(π̂, π⁰) = ½Σ_k |π̂_k − π⁰_k| ≤ δ` is exactly commensurable with the frozen
tolerance (TV × n is literally "cases misattributed"), which is its virtue. Its
defects: (i) TV is a non-smooth functional of four correlated cell proportions, so
its null distribution is awkward and it requires a bootstrap regardless; (ii) it is
**omnibus** — a failure tells you the surface is wrong but not *where*, which is
precisely the information the programme needs, because each stage routes to a
different E4 arm; (iii) it is not monotone under UNRESOLVED resolution, so it does
not admit the closed-form determinacy bound that §6 needs. Keep it, report it, do
not gate on it.

**(b) Agreement on the DOMINANT class only (argmax).**
*Verdict: REJECT as a qualification statistic.* It is not identifiable at any feasible
n. Measured: on the E2a Held-out-comparable stratum standardized to the Held-out cell
mix, the two competing non-success classes come out at
`π_B = 0.4560` and `π_C = 0.4583` — a separation of **0.23 pp**. Certifying an argmax
at that separation needs n in the tens of thousands. Argmax agreement is also
*degenerate as evidence*: it is a 1-bit statistic against a 3-way alternative, so it
passes on surfaces that are grossly wrong in every stage magnitude. It survives only
as the **routing** predicate downstream of qualification (§8), where it is applied to
the new surface alone and must carry its own certified margin.

**(c) Per-class two-proportion equivalence with multiplicity control.**
*Verdict: REJECT as primary, on estimand grounds.* The four marginal class shares
`(π_A, π_B, π_C, π_E)` are the *terminal* partition. They confound the stages: a
surface can miss on `π_B` purely because it missed on `π_A` upstream (fewer cases
reach retention at all). Testing them jointly with Holm is statistically correct and
scientifically uninformative. It also loses monotonicity (§6).

**(d) Conditional / stage-wise survival formulation.**
*Verdict: ADOPT — and it is not an analyst invention.* `MURU_V2_G2_PARETO_STUDY_DESIGN.md`
**§2.6 already freezes exactly these three metrics**, by name, prospectively at
`befca0d`:

> `P_front` · `P_retain_given_front` · `P_win_given_retain` — *"Three conditional
> stages, measured per family and per coefficient regime."*

So the stage-wise framing, **and the per-family / per-regime stratification** that §5
of this document requires for identifiability control, are both frozen authority, not
new choices. This is the single most important governance fact in this document.

### 1.2 The refinement I recommend: cumulative, not conditional

I adopt (d) but reparameterize from **conditional** to **cumulative** survival. Define,
over a world (case) `w` with its 30 seeds:

```
reach_front(w)   = 1{ at least one of the 30 seeds' Pareto fronts contains a G2-correct row }
reach_retain(w)  = 1{ at least one seed's argmax(score)-retained candidate is G2-correct }
reach_win(w)     = 1{ the cross-seed representative is G2-correct }                (= SUCCESS)
```

and the three **cumulative stage-survival proportions**

```
S₁ = (1/n) Σ_w reach_front(w)
S₂ = (1/n) Σ_w reach_retain(w)
S₃ = (1/n) Σ_w reach_win(w)
```

These are a bijective reparameterization of both §2.6 and §2.7:

```
§2.6 conditionals :  P_front(case-level) = S₁ ,  P_retain|front = S₂/S₁ ,  P_win|retain = S₃/S₂
§2.7 partition    :  π_A = 1 − S₁ ,  π_B = S₁ − S₂ ,  π_C = S₂ − S₃ ,  π_E = S₃
```

(with `π_C = LOST_IN_CROSS_SEED = C ∪ D` of `MURU_V2_E2_PREDECLARATION.md` §6).
The reparameterization loses **no** information — the frozen four-way partition is
recovered exactly by differencing — and buys four properties the conditionals do not
have:

1. **Common denominator.** Each `S_j` is a count out of `n`. The frozen tolerance
   "more than 10 cases of 144" is a bound on a count out of 144. `S_j` is therefore
   *exactly* commensurable with it. The conditionals are not: `P_retain|front` has
   denominator 130, so ±6.944 pp on it means ±9.0 cases, not ±10.
2. **Monotonicity under UNRESOLVED resolution** (§6). Each `S_j` is a monotone
   non-decreasing function of the row-label lattice, so its determinacy interval has a
   closed form with **two** evaluations instead of `2^U`.
3. **Stage localization.** A failure names the stage, and each stage names the E4 arm:
   `S₁ → E4b/E4c/E4d (generation)`, `S₂ → E4a (retention)`, `S₃ → E4f (cross-seed)`.
4. **Variance behaviour.** Conditional estimators have random denominators; the
   cumulative ones are plain binomial proportions of a fixed `n`, so Wilson applies
   directly and the bootstrap is well-behaved at the boundary (`S₃ ≈ 0.028`, where Wald
   is unusable).

### 1.3 Standardization (this is the identifiability control — see §5)

**Two different standardization variables appear in this document and they must not be
confused. P1 is right that the 12 Held-out G2 "families" `F01…F18` are experimental
CONDITIONS, not truth laws, and that E2a instantiated none of them.**

| Use | Standardization variable | Identified from E2a? |
|---|---|---|
| **Prospective design** (§1.3, §3.2, §8) | the **12 Held-out conditions** `F01…F18`, `w_k = 1/12` | **Not applicable** — the replacement surface is *generated at* those 12 conditions, so the weights are exact by construction, not estimated |
| **Retrospective E2a diagnostic** (§5.3) | **`truth_family`, 4 levels** (affine 108/144, saturating 12/144, interaction 12/144, exponential 12/144) | **Yes** — E2a spans all four truth families. It does **not** span the 12 conditions, so no condition-level reweighting of E2a is attempted anywhere in this document |

Nothing in §5.3 standardizes E2a on the 12 F-codes. Doing so would not be identified,
and I do not do it.

For the **prospective design**, let `k` index the **12 Held-out conditions** `F01…F18`
(9 affine, 1 saturating, 1 interaction, 1 exponential — verified from
`v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv`). The standard weights are
`w_k = 1/12`. The primary estimator is the **direct-standardized** proportion

```
Ŝ_j = Σ_k w_k · Ŝ_j,k        with     Ŝ_j,k = (1/n_k) Σ_{w ∈ cell k} reach_j(w)
```

If the replacement surface is built with **proportional allocation** (`n_k = n/12`,
i.e. the Held-out cell mix reproduced exactly), then `Ŝ_j` is self-weighting, the
design effect is exactly 1.000, and standardization is a formality that nonetheless
must be *stated* so that any cell shortfall is corrected rather than ignored.

Measured design effects (computed, `w = (9,1,1,1)/12` over families):

| Allocation | DEFF |
|---|---:|
| proportional (= Held-out mix) | **1.000** |
| equal per family (27 % each) | 2.333 |

Equal-per-family allocation costs a **2.33× variance inflation** on the primary and is
rejected. Per-family precision for the secondary diagnostics is bought back by `n`,
not by reallocation.

### 1.4 Estimator and interval method — and why

| Quantity | Estimator | Interval | Why this one |
|---|---|---|---|
| `S_j` (primary, standardized) | direct-standardized proportion | **stratified nonparametric BCa bootstrap over worlds, resampling within cell, B = 20 000** | The standardized estimator is a weighted sum of binomials; no exact interval exists. BCa corrects both bias and skew, which matters at `S₃ ≈ 0.03`. Resampling the *world* is the correct unit — the 30 seeds are nested inside it and are not exchangeable across worlds. |
| `S_j` (unstandardized cross-check) | `x_j / n` | **Wilson score, 95 %** | Frozen precedent: `E3_RESULTS.json` uses Wilson bounds (`bic_wilson_lower`, `wilson_upper`) for every one of its verdicts. Wilson has near-nominal coverage at `p → 0` and `p → 1`, where both `S₁` and `S₃` live, and unlike Clopper–Pearson it is not systematically over-wide — at these n, CP would cost roughly 12–15 % of the sample for nothing. |
| Difference vs Held-out, **sensitivity only** | `Ŝ_j − S⁰_j` | **Newcombe hybrid-score (MOVER-R)** | Best small-sample coverage among two-proportion difference methods; the only defensible choice if the protocol owner rejects the fixed-target framing. See §3.3 — this analysis is prespecified to be **inconclusive**, and that is declared in advance so it cannot be spun either way. |
| `TV(π̂, π⁰)` (secondary) | `½Σ_k|π̂_k − π⁰_k|` | percentile bootstrap, same 20 000 replicates | Non-smooth functional; BCa's acceleration is not well defined, percentile is the honest choice. |
| Routing margin (§8) | `π̂_top − π̂_second` | multinomial paired-difference, `Var = (π_1 + π_2 − (π_1−π_2)²)/n`, normal LCB | Standard multinomial contrast; the correlation between two cells of the same partition must not be ignored (treating them as independent understates the variance by ~40 % here). |

**Why the comparator is fixed rather than sampled.** `S⁰` is the sealed, hostile-audited,
protocol-owner-**ratified** (D1) attribution of the *entire enumerated* Held-out G2 case
set — §2.8 defines that population as exactly "144 Held-out G2 cases", not a sample
from it. The calibration question §2.3 poses is whether the fresh worlds "reproduce
the Held-out regime", i.e. match *this* corpus, which is the corpus every E4 conclusion
must transfer to. So `S⁰` enters as a constant.

**This choice is anti-conservative and I flag it as such.** It narrows the intervals by
removing the comparator's variance. Two things offset it, both prespecified here:
(i) α is tightened from the conventional TOST α = 0.05 (90 % interval) to
**α = 0.025 (95 % interval containment)**, which also aligns with E3's own 95 % Wilson
precedent; (ii) the two-sample Newcombe analysis is reported alongside as a mandatory
sensitivity, with its expected inconclusiveness declared in advance.

---

## 2. THE EQUIVALENCE MARGIN

### 2.1 Recommendation

```
δ = 10 / 144 = 0.0694444…   (6.944 percentage points)
```

reused **verbatim** from the frozen `PE2-4` tolerance, as quoted in
`f4c1105:…RETENTION_REMEDIATION_PREREGISTRATION.md` §4 and adjudicated in
`GATE_1_DEFINITIVE.md` §1/§3:

> "contradicts the v1 decomposition's 69/57 retention-vs-generation split **by more
> than 10 cases (PE2-4's own tolerance)**"

and pinned independently at `MURU_V2_G2_PARETO_STUDY_DESIGN.md:466`:

> `PE2-4` — "E2b reproduces the decomposition's retention-versus-generation split
> **to within 10 cases of 69/57**."

### 2.2 Commensurability audit of every candidate threshold

The coordinator is right to demand this. What each candidate *actually bounds*:

| Candidate | What it bounds | Unit of analysis | Sidedness | Transfers to `S_j`? |
|---|---|---|---|---|
| **`> 10 of 144`** (PE2-4 / Gate 1) | absolute deviation in the **count of one pipeline-stage attribution class** on the Held-out G2 corpus | one case → one stage class | two-sided in effect (Gate 1 evaluated `\|55−69\|` and `\|14−57\|`) | **YES.** Same estimand class (stage attribution), same unit (a case), same corpus. Read as a proportion (10/144) so it is n-free. |
| **E3's `0.10` false-structure bar** | the **specificity of the BIC model-selection oracle** on the `mass_power` negative control — the rate at which a 5-way *closed-form* model comparison prefers a descriptor model when the truth is mass-only | one world → one model choice; **no symbolic search involved at all** | one-sided upper bound | **NO.** Different estimand (oracle specificity vs pipeline stage), different unit, wrong sidedness. It transfers **only** as (i) methodological precedent for Wilson-bound-vs-threshold decisions, and (ii) a reusable bar if the new design carries a `mass_power` false-structure control arm — which I recommend it does, in a **separate** arm outside the primary population (§5.4). |
| **§2.9 plurality rules** | nothing numeric — an `argmax` predicate with **no margin at all** | — | — | **NO.** Supplies no margin. And measurably non-identifiable: 0.23 pp separation on the standardized E2a stratum. |
| **Decision-relevant margin `δ_dec`** | half the Held-out top-two non-success gap, `½(π_C − π_B) = ½(0.4931 − 0.3819) = 0.0556` — the largest per-class error that provably cannot flip the §2.9 routing argmax | one case → one stage class | two-sided | **Commensurable but STRICTER, and unaffordable.** At `δ_dec` the binding sample size is **n ≥ 943** (α = 0.025, 80 % power, g = 0.01). Recommended as a **prespecified descriptive report**, not a gate. |
| **Power-based margin** | nothing scientific — it is the margin that makes the experiment you can afford come out significant | — | — | **REJECT categorically.** This is results-tuning with the results replaced by a budget. It inverts the logic of an equivalence margin. |

### 2.3 Why reusing δ = 10/144 is not results-tuned

Five independent arguments, each sufficient:

1. **It is frozen and predates everything.** `PE2-4` is fixed at `befca0d` (study
   design, line 466) and re-pinned at `f4c1105` (preregistration §4). Neither the E2a
   nor the E2b attribution existed when it was written.
2. **It is the programme's own definition of "material attribution difference."**
   That is precisely the quantity an equivalence margin must encode. The programme has
   already declared, results-blind, how many misattributed cases matter: ten in 144.
3. **The direction of reuse is conservative.** Gate 1 used δ as a *falsification*
   bound: exceeding it condemns. I use it as a *qualification* bound: staying inside it
   licenses. Reusing the same number means the new surface must reproduce Held-out at
   least as tightly as the v1 decomposition was required to. The bar is not loosened by
   the change of role.
4. **The proportional reading is forced, not chosen.** Transferring the literal count
   `10` to a corpus of `n ≠ 144` would make the test arbitrarily easier or harder as a
   pure function of `n`. The n-free reading `10/144` is the only one that is not itself
   a design lever.
5. **It is stricter than the alternative I could have picked.** Had I wanted a margin
   the surface would pass, I would have widened toward the omnibus TV gate or dropped
   to argmax agreement. Both are more permissive. I recommend the narrower option and
   disclose the still-narrower `δ_dec = 5.56 pp` that I cannot afford.

### 2.4 Disclosed pre-computation (full transparency)

Applying the recommended machinery to the **invalidated** E2a corpus, standardized on
`truth_family` to the Held-out family mix. **Two conditionings are reported because
they disagree** (see §5.3):

| Endpoint | E2a std., all noise/regime (n=432) | E2a std., within `noise_sd=0.02` (n=144) | Held-out `S⁰` | Δ (pp), pooled / noise-matched |
|---|---:|---:|---:|---:|
| `S₁` | 0.9059 | 0.9144 | 0.9028 | +0.31 / +1.16 |
| `S₂` | 0.4398 | 0.4583 | 0.5208 | −8.10 / −6.25 |
| `S₃` | 0.0463 | 0.0000 | 0.0278 | +1.85 / −2.78 |
| `TV(π̂,π⁰)` (secondary) | 0.1026 = **14.78 cases** | 0.0741 = **10.67 cases** | — | both **fail** the 10-case gate |

Under the pooled conditioning `S₂` also fails the primary margin (−8.10 pp > 6.944 pp).
Under the noise-matched conditioning all three stages pass on point estimates and the
secondary TV gate fails marginally. **I am not promoting or demoting any endpoint on
the strength of these numbers.** The primary was selected on the results-independent
grounds in §1.2 (frozen §2.6 lineage, monotonicity, exact commensurability). Any later
attempt to elevate or demote an endpoint after the new surface is scored is a protocol
violation.

---

## 3. SAMPLE SIZE

### 3.1 The calculation

For each `S_j`, the TOST requirement at true difference 0, one-sided α, power 1−β,
with a determinacy gap `g` (§6) consuming the margin:

```
( z_{1−α} + z_{1−β} ) · SE_j  +  g  ≤  δ
⇒ SE_j ≤ (δ − g) / (z_{1−α} + z_{1−β})
⇒ n_j ≥ S⁰_j (1 − S⁰_j) · ( z_{1−α} + z_{1−β} )² / (δ − g)²        [DEFF = 1 under proportional allocation]
```

With `S⁰ = (0.9028, 0.5208, 0.0278)`, `δ = 0.069444`, `β = 0.20`:

**α = 0.025 (95 % interval containment) — RECOMMENDED**

| `g` | `z` | `SE_max` | n(S₁) | **n(S₂)** | n(S₃) | **binding n** |
|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 2.802 | 0.02479 | 143 | **407** | 44 | 407 |
| 0.005 | 2.802 | 0.02300 | 166 | **472** | 52 | 472 |
| **0.010** | 2.802 | 0.02122 | 195 | **555** | 60 | **555** |
| 0.020 | 2.802 | 0.01765 | 282 | **802** | 87 | 802 |
| 0.030 | 2.802 | 0.01408 | 443 | **1259** | 137 | 1259 |

**α = 0.050 (90 % interval containment) — reported for reference only**

| `g` | binding n |
|---:|---:|
| 0.000 | 320 |
| 0.010 | 437 |
| 0.020 | 632 |

`S₂` binds throughout, because `S⁰₂ = 0.5208` sits at the variance maximum. `S₁` and
`S₃` are cheap. **The determinacy gap is worth hundreds of worlds** — moving `g` from
0.02 to 0.01 saves 247 worlds; from 0.02 to 0 saves 395. Escalating unresolved
expressions to completion (§6) costs single-digit CPU-hours. **Buy determinacy with
CPU, not with worlds.**

### 3.2 Recommended design

```
n = 576 worlds  =  12 Held-out cells × 48 replicates
    × 30 seeds  =  17 280 searches
```

- 576 ≥ 555 (the `g = 0.01`, α = 0.025, 80 %-power requirement) with ~4 % headroom for
  the bootstrap/Wilson interval being slightly wider than the normal approximation.
- The `12 cells × R replicates` construction reproduces the Held-out family mix
  **exactly by construction** (9/12 affine, 1/12 each saturating / interaction /
  exponential) — no post-hoc reweighting required, DEFF = 1.000, and it extends
  §2.8's own stated rationale ("Twelve replicates per cell matches the v1 per-family
  case count") from R = 12 to R = 48 without changing the design's logic.
- **Cost.** Measured E2a mean wall time on this host: **262.5 s/world** (median 257.4,
  p90 288.3, max 788.4), giving **41.7 CPU-hours** for 576 worlds, plus escalation.
  On 24 cores / 12 shards that is ≈ 3.5 h wall. E2a was 539 worlds ≈ 39.3 CPU-hours,
  so this is a **6 % increase in compute** over a run already executed once — the
  OOM problems in E2a were a scoring-stage pathology (§6), not a search-cost problem,
  and are addressed directly.

### 3.3 Blinded sample-size re-estimation (internal pilot)

`g` is a **nuisance parameter** (the unresolved-row rate), not an endpoint. Prespecify:

> After scoring, if the sealed determinacy gate reports `g_j > 0.010` for any `j`,
> the surface is extended to **n = 810 worlds** (12 cells × 67.5 → 12 × 68 = 816) by
> generating replicates 49…68 from the same frozen generator and seed band, and the
> endpoint is computed **once**, on the full extended surface.

This is standard blinded nuisance-parameter re-estimation. It does **not** inflate α,
because the trigger depends only on the unresolved-row rate and is **blind to
`Ŝ_j`, `π̂`, and the routing argmax**. The trigger quantity, the extension size, and
the extension's world IDs are all fixed here, before any world exists.

### 3.4 Minimum defensible n

| n | Construction | Valid **only if** |
|---:|---|---|
| **576** | 12 × 48 | `g ≤ 0.010` — **recommended** |
| **480** | 12 × 40 | `g ≤ 0.005` (n_req 472). Defensible; no headroom. |
| **408** | 12 × 34 | `g = 0` exactly — every expression resolved to completion, `INDETERMINATE_WORLDS = 0`. This is the **absolute floor** and it is achievable only by buying full determinacy. |
| < 408 | — | **Not defensible at δ = 10/144.** Do not run it. State the failure rather than run an underpowered qualification, because an underpowered equivalence test *fails by default* and would be misread as "the surface does not reproduce Held-out". |

Say this plainly to the protocol owner: **an equivalence test that cannot reject
non-equivalence is not neutral — it is a rigged failure.** Under-running this is worse
than not running it.

### 3.5 Seeds per world — 30 is mandatory, and here is the number

The frozen partition is defined over 30 seeds (`§2.5` control 2: `SEEDS_PER_CASE = 30
unchanged`; `MURU_V2_E2_PREDECLARATION.md` §6 quantifies every predicate "for all 30
seeds"). `S₁` is a **max over seeds**, so it is a function of the seed count:
`S₁(S) = 1 − (1−q)^S` for a per-seed front-correct rate `q`.

Held-out's `S₁ = 0.9028` over 30 seeds implies `q = 0.0748`. Then:

| seeds | implied `S₁` | shift vs 30 | in units of δ |
|---:|---:|---:|---:|
| 10 | 0.5402 | −36.26 pp | 5.22 δ |
| 15 | 0.6882 | **−21.46 pp** | **3.09 δ** |
| 20 | 0.7886 | −11.42 pp | 1.64 δ |
| 24 | 0.8450 | −5.77 pp | 0.83 δ |
| **30** | **0.9028** | — | — |
| 40 | 0.9553 | +5.25 pp | 0.76 δ |

**Reducing seeds below 30 is a scientific change, not an economy.** At 15 seeds the
estimand moves by three times the entire equivalence margin — the surface would fail
qualification for a reason that has nothing to do with the pipeline. `S₃` is worse: it
is defined through `group_and_select` over exactly 30 retained candidates, so it has no
seed-count-invariant reading at all. **Hold S = 30. Flag any proposal to reduce it as
a change of estimand requiring protocol-owner ratification.**

---

## 4. MULTIPLICITY

### 4.1 Primary — no adjustment needed, and this is a theorem not a convention

The primary is a **conjunction**:

```
QUALIFIED  ⟸  equivalence holds for S₁  AND  for S₂  AND  for S₃
```

Each component is an equivalence (TOST) test whose null is *non-equivalence*. A
conjunction of tests, each at level α, rejecting only when **all** reject, is an
**intersection–union test** and has size ≤ α without adjustment (Berger 1982).
Adjusting here would be a *mistake* — it would make an already-conservative procedure
more conservative and inflate the required n by ~40 % for nothing.

Same argument covers the two-stage structure: qualification → routing is a
**fixed-sequence (hierarchical gatekeeping)** procedure, which preserves FWER without
adjustment. Routing is read at full α, and only if qualification passes.

### 4.2 Single primary endpoint

```
PRIMARY ENDPOINT  =  STAGE_EQUIVALENCE, the 3-component IUT on the
                     standardized cumulative stage-survival vector S = (S₁,S₂,S₃)
                     against the fixed sealed Held-out target S⁰,
                     at margin δ = 10/144, α = 0.025 one-sided per side.
```

One endpoint. One α. One decision.

### 4.3 Prespecified secondary diagnostics (reported, never gating)

| # | Diagnostic | Multiplicity control |
|---|---|---|
| D1 | `TV(π̂, π⁰)` vs δ, percentile bootstrap | single test, none |
| D2 | The four marginal shares `π̂_A, π̂_B, π̂_C, π̂_E` with 95 % Wilson intervals | descriptive |
| D3 | **Per-family stage table**: `S_j` by family, 4 families × 3 stages = 12 equivalence tests | **Holm–Bonferroni** across the 12 |
| D4 | Per-coefficient-regime stage table (§2.6's own "per family and per coefficient regime") | Holm across the regime family |
| D5 | The §2.6 conditionals `P_front`, `P_retain|front`, `P_win|retain` reported verbatim, for continuity with frozen authority | descriptive |
| D6 | `rank_of_correct`, `score_gap`, `complexity_gap`, `r2_gap`, `front_size` distributions (§2.6) | descriptive |
| D7 | `δ_dec = 5.56 pp` re-read of the primary | descriptive |
| D8 | Two-sample Newcombe sensitivity (§3.3 below) | descriptive, **declared inconclusive in advance** |

**None of D1–D8 may change the qualification verdict.** They exist to explain a
failure, not to rescue one.

### 4.4 The two-sample sensitivity is provably inconclusive — declared now

If the protocol owner rejects the fixed-target framing and insists the Held-out corpus
be treated as a sample of size 144, then the comparator contributes irreducible
variance `S⁰_j(1−S⁰_j)/144`. Against the total budget `(δ/z)²` at α = 0.05, 80 % power:

| endpoint | `Var_HO` | budget | verdict |
|---|---:|---:|---|
| `S₁` | 6.095 × 10⁻⁴ | 7.800 × 10⁻⁴ | feasible, needs n ≥ 515 |
| **`S₂`** | **1.733 × 10⁻³** | 7.800 × 10⁻⁴ | **INFEASIBLE AT ANY n** |
| `S₃` | 1.875 × 10⁻⁴ | 7.800 × 10⁻⁴ | feasible, needs n ≥ 46 |

The comparator's own variance on `S₂` exceeds the *entire* margin budget by 2.2×.
**No replacement surface of any size can pass a two-sample equivalence test at
δ = 10/144 against a 144-case comparator.** This is a property of the sealed corpus,
not of the new design. It is stated here, before execution, so that a later
inconclusive two-sample result cannot be presented as evidence that the surface
failed. If the owner insists on two-sample as primary, the only honest options are
(i) widen δ — results-tuning, refuse — or (ii) declare the qualification
**unachievable** and route the programme elsewhere.

---

## 5. IDENTIFIABILITY — how far composition explains the E2a/E2b divergence (and where it stops)

### 5.1 The confound, stated

`E3_RESULTS.json`, at the frozen operating point:

| family | `bic_rate` | Wilson lower | class | `search_side_attribution_licensed` |
|---|---:|---:|---|:--:|
| `mass_interaction` | 1.000 | 0.975 | IDENTIFIABLE | true |
| `mass_saturating_descriptor` | 0.820 | 0.751 | IDENTIFIABLE | true |
| `mass_affine_descriptor` | **0.553** | 0.473 | **MARGINAL** | **false** |
| `mass_exponential_descriptor` | **0.527** | 0.447 | **MARGINAL** | **false** |

A pipeline stage cannot lose a signal the data never identified. If the population's
family mix differs, the attribution differs **for identifiability reasons alone.**

### 5.2 The compositions differ enormously — measured

| | Held-out (n = 144) | E2a (n = 539) |
|---|---:|---:|
| `mass_affine_descriptor` | **108 (75.0 %)** | 108 (20.0 %) |
| `mass_saturating_descriptor` | 12 (8.3 %) | 108 (20.0 %) |
| `mass_interaction` | 12 (8.3 %) | 108 (20.0 %) |
| `mass_exponential_descriptor` | 12 (8.3 %) | 108 (20.0 %) |
| `mass_power` (negative control, no descriptor) | **0 (0 %)** | **107 (19.9 %)** |
| E3-**MARGINAL** mass (affine + exponential) | **83.3 %** | 40.0 % |
| `noise_sd = 0.02` (the real benchmark level) | **100 %** | **33.2 %** |

Only **144 of E2a's 539 worlds (26.7 %)** are in the Held-out-comparable stratum at all
(descriptor family **and** `noise_sd = 0.02`). Two-thirds of E2a sits at noise levels
(0.0, 0.06) that no Held-out case has, and a fifth of it is a negative-control family
that has no G2 descriptor truth at all.

### 5.3 Composition explains most of the MAGNITUDE but does NOT resolve the ORDERING

**CORRECTION — issued in response to the coordinator's recomputation, which I have
reproduced exactly and which is right.** An earlier revision of this section claimed
standardization "removes 91 % of the total-variation divergence" and "flips the routing
argmax B → C, into agreement with Held-out". **Both claims are withdrawn.** The 91 %
was an arithmetic error — I attached the reduction computed on the *conditional*
`P_win|retain` (48.5 pp → 5.3 pp = 89 %) to the *total-variation* figure, whose true
reduction is 77.0 %. The argmax claim was conditioning-dependent and, on inspection,
not identified at all. The corrected analysis follows.

Per-family stage survival on E2a (36 worlds per family at `noise_sd = 0.02`; 108 pooled):

| family | pooled (A,B,C,E)/108 | at `noise_sd=0.02` (A,B,C,E)/36 |
|---|---|---|
| `mass_affine_descriptor` | (0, 51, 51, 6) | (0, 16, 20, 0) |
| `mass_saturating_descriptor` | (12, 93, 3, 0) | (1, 35, 0, 0) |
| `mass_interaction` | (2, 52, 48, 6) | (0, 18, 18, 0) |
| `mass_exponential_descriptor` | (108, 0, 0, 0) | (36, 0, 0, 0) |
| `mass_power` (n=107, all noise) | (0, 0, 0, 107) | — |

**The three surfaces, with both conditionings reported:**

| Surface | `π_A` | `π_B` | `π_C` | `π_E` | `TV` vs Held-out | TV reduction | argmax non-success | `π_B − π_C` (95 % CI) |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| **Held-out (target)** | 0.0972 | 0.3819 | 0.4931 | 0.0278 | — | — | **`C`** | −11.11 pp |
| **E2a raw, n=539** | 0.2263 | 0.3636 | 0.1892 | 0.2208 | 0.3221 (46.4 cases) | — | **`B`** | +17.44 pp |
| **E2a std. on `truth_family`, all noise/regime (n=432)** | 0.0941 | 0.4660 | 0.3935 | 0.0463 | 0.1026 (**14.8 cases**) | **68.1 %** | **`B`** | +7.25 pp (−1.46, +15.97) |
| **E2a std. on `truth_family` within `noise_sd=0.02` (n=144)** | 0.0856 | 0.4560 | 0.4583 | 0.0000 | 0.0741 (**10.7 cases**) | **77.0 %** | **`C`** | −0.23 pp (−15.85, +15.39) |

Standardization variable: `truth_family`, 4 levels, weights `(108, 12, 12, 12)/144`.
Support: the descriptor-family worlds of E2a — all 432 of them in the pooled row,
the 144 at `noise_sd = 0.02` in the noise-matched row. **`mass_power` is outside the
support in both** (Held-out weight = 0). No standardization on the 12 F-conditions is
performed anywhere; E2a does not span them (§1.3).

**Answering the coordinator's three questions:**

1. **On what did I standardize?** `truth_family` (4 levels), *within* the
   `noise_sd = 0.02` stratum. The coordinator standardized on `truth_family` *pooled*
   over all three noise levels and all three coefficient regimes. That single
   difference accounts for the entire discrepancy — 68.1 % vs 77.0 %, and `B` vs `C`.
   Both figures are correct computations of different estimands. I reproduce the
   coordinator's `(A 0.0941, B 0.4660, C 0.3935, E 0.0463)` to four decimals.
2. **Did the flip depend on the timeout correction?** **No.** It depended only on the
   extra conditioning on noise. No determinacy adjustment was applied to either figure.
   The summary sentence conflated nothing about timeouts — it simply reported a
   conditioning-specific result as though it were robust. That was the error.
3. **Exact standardized proportions:** both rows are in the table above.

**Who is right about the ordering: the coordinator, and more strongly than claimed.**
Even in *my* noise-matched conditioning where the argmax nominally sits on `C`, the
`B − C` gap is **−0.23 pp on n = 144, with a 95 % CI of (−15.85, +15.39) pp** — a gap
of one-third of one case. That is not a flip; it is a coin toss printed to four
decimals. And the coordinator's pooled conditioning gives `B` ahead by 7.25 pp with a
CI that also covers zero (−1.46, +15.97). **Neither conditioning identifies the
ordering.** The correct statement is:

> Composition explains **68–77 % of the magnitude** of the E2a/Held-out divergence.
> It leaves a residual of **10.7–14.8 cases of 144**, above the 10-case tolerance in
> both conditionings. **The stage ORDERING is not identified on E2a under any
> conditioning**, so composition cannot be said to explain it, and neither can
> anything else on present evidence.

**Forward-design consequence — this strengthens the case for the new surface, it does
not weaken it.** Had standardization cleanly flipped the ordering, the divergence would
have been a bookkeeping artifact and a cheap re-analysis of E2a might have sufficed.
It does not. What remains is: (i) a residual TV of 10.7–14.8 cases that *exceeds* the
frozen tolerance under both conditionings, so E2a does not qualify even after its
best-case reweighting; and (ii) an ordering that is statistically undetermined on
E2a at any conditioning — which is precisely the quantity §2.9 routes on. **A new,
composition-matched, adequately powered surface is the only instrument that can settle
it.** That is the §3.2 n = 576 design, whose routing certification (§7.2) has a 95 %
LCB of +0.0353 at a Held-out-like truth — versus E2a's CI that spans ±15 pp.

What survives from the original finding, undamaged: the compositions differ enormously
(§5.2); `mass_power` at 20 % of E2a with 107/107 success is a genuine artifact and must
be excluded (C3); direct standardization removes most of the divergence magnitude; and
`mass_exponential_descriptor` at 108/108 `NEVER_ON_FRONT` is a degenerate cell that
E3 already explains (MARGINAL, `search_side_attribution_licensed = false`).

### 5.4 Required design controls

**C1 — Composition matching is mandatory, by construction.** The replacement surface
is `12 Held-out cells × R replicates`, reproducing the Held-out family mix exactly.
Not reweighted after the fact; **generated** that way. Cell-level shortfall > 0 is an
admissibility failure, not something the standardization fixes.

**C2 — Noise and coefficient at the Held-out operating point.** `noise_sd = 0.02`
(the generator's real default for all four descriptor families), `coefficient ~
U(0.25, 0.55)` drawn per world exactly as `generator._law` does, **not** fixed to
{0.25, 0.40, 0.55}. E2a's fixing of the coefficient to three lattice points is itself a
departure from the Held-out regime — Held-out cases carry the random draw. Reproducing
"the Held-out regime" means reproducing its *distribution*, not a lattice inside it.

**C3 — `mass_power` is excluded from the primary population.** Held-out has zero
`mass_power` G2 cases. Including it in the primary is the single largest source of the
sealed divergence. It moves to a **separate, clearly-labelled false-structure control
arm** of 60 worlds, scored against **E3's 0.10 bar** (the one place that threshold
legitimately applies), reported as diagnostic D9, and **excluded from every `S_j`.**

**C4 — Stratification is frozen authority, not a new choice.** §2.6: "measured **per
family and per coefficient regime**". Report per-cell `S_j` (diagnostic D3/D4) so an
identifiability-driven mismatch is visible rather than absorbed into a pooled number.

**C5 — Pre-declare the identifiability prior.** E3 is complete: affine and exponential
are MARGINAL with `search_side_attribution_licensed = false`. Since Held-out is 83.3 %
MARGINAL-family mass, a large `π_A` on the replacement surface is **expected and
licensed by E3**, and must not later be re-read as a pipeline generation failure.
Write this into the protocol now, before the numbers exist.

**C6 — Conditioning, not matching, is wrong here.** Do not adjust for family with a
regression. The estimand is a standardized marginal over a *known* target
distribution; direct standardization with the design already at the target weights is
exact, model-free, and DEFF = 1. A model-based adjustment would import a functional
form assumption for nothing.

### 5.5 The rival explanation: measurement error (coordinator's finding)

The composition argument is **not** the whole story, and I weigh the rival explicitly.

`results/e2/cloud_x86_parity/CLOUD_X86_PARITY_QUALIFICATION.json` records
`NEW_CLOUD_HOST_PARITY_FAILED`: `SIMPLIFY_TIMEOUT_SECONDS = 5` is a **wall-clock**
budget, so the same unmodified classifier assigns a different scientific label to the
same expression as a pure function of host speed (witness: 4.80 s on x86, budget
5.00 s, ARM abandoned it). The affected field is `first_loss_stage` — the
routing-relevant one.

**The bias has a direction, and I can state it as a theorem.** A `SIMPLIFY_TIMEOUT`
collapses to `SUPPORT_UNRESOLVED` / `FAMILY_UNRESOLVED` ⇒ `g2_correct = false`. Since
`reach_front`, `reach_retain`, `reach_win` are all monotone-increasing indicators in
the row labels, **every timeout biases every `S_j` downward**, i.e. pushes mass toward
*earlier*-stage loss. The parity witness confirms it empirically: the world moved
`A → B` when the timeout resolved. This is **systematic bias, not noise** — it does not
average out, and it grows with corpus size.

**Exposure measured on the x86 E2a corpus** (I joined
`candidates_shard_*.jsonl` against the classify cache at
`/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3`):

```
SIMPLIFY_TIMEOUT distinct expressions : 397 of 52 450   (0.757 %)
timeout-carrying candidate rows       : 396 of 189 467  (0.209 %)
worlds with >= 1 timeout row          :  97 of 539      (18.0 %)
```

and the contamination is **concentrated exactly where the bias predicts**:

| observed stage | worlds | of which timeout-affected | share |
|---|---:|---:|---:|
| `A` NEVER_ON_FRONT | 122 | **73** | **59.8 %** |
| `B` LOST_IN_RETENTION | 196 | 20 | 10.2 % |
| `C` LOST_IN_CROSS_SEED | 102 | 3 | 2.9 % |
| `E` SUCCESS | 119 | 1 | 0.8 % |

Six in ten of E2a's `NEVER_ON_FRONT` worlds rest on at least one row the classifier
gave up on. (The ARM corpus is worse: 834 timeout rows across 237 of 530 worlds =
44.7 %, and the artifact states its 1/530 observed mismatch is a **lower bound**
because the lazy replay never classifies most affected rows.)

**Applying the Gate-1 determinacy standard to E2a — RETRACTED, with the derivation.**

An earlier revision of this document asserted that E2a's `B`-plurality is **not**
invariant over the resolutions of its own unresolved rows, and therefore that
`LOCKED_EXECUTE_E4A` "was never determinate". **That claim is WITHDRAWN. The refined
bound certifies the opposite.** The coordinator was right to refuse it on assertion.
Full derivation so it can be reproduced:

**Step 1 — exposure, split by whether the timeout sits on a RETAINED row.**
Join `results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl` against
`/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3`
(`canonicalization_status == 'SIMPLIFY_TIMEOUT'`, 397 distinct expressions), then group
by `first_loss_stage`:

| observed stage | worlds | with ≥1 timeout row | **with a timeout on a `retained_by_argmax_score` row** |
|---|---:|---:|---:|
| `A` NEVER_ON_FRONT | 122 | 73 | **2** |
| `B` LOST_IN_RETENTION | 196 | 20 | **0** |
| `C` LOST_IN_CROSS_SEED | 102 | 3 | 3 |
| `E` SUCCESS | 119 | 1 | 1 |

**Step 2 — the coarse bound I published, and why it was too weak.** Ignoring the
retention structure and allowing any unresolved row to push a world arbitrarily far
right gives `A∈[49,122]`, `B∈[176,269]`, `C∈[99,195]`, `E∈[119,215]`, hence
`B_min = 176 < C_max = 195` ⇒ not certified. **This is an over-approximation of the
reachable set**, and I reported it as though it were the reachable set. That was the
error.

**Step 3 — the refined bound, using structure already in the corpus.** By the §6.1
monotonicity lemma, movement past a stage requires the *specific* predicate of that
stage to flip:

- `A → B` requires **any** front row to become `CORRECT`.
- `A/B → C or E` requires a **retained (argmax-score)** row to become `CORRECT`.
- `C → E` requires the **representative** to become `CORRECT`.

So the 71 `A`-worlds whose timeouts are all on **non-retained** rows can reach `B` and
no further; and the 20 `B`-worlds — **none** of which has a timeout on a retained row —
cannot move **at all** (they already have a correct front row, and every one of their
retained rows is definitively classified `INCORRECT`).

```
A ∈ [122 − 73,        122]            = [ 49, 122]
B ∈ [196 −  0,  196 + (73 − 2)]       = [196, 267]
C ∈ [102 −  3,  102 + (2 + 0)]        = [ 99, 104]
E ∈ [119,       119 + (2 + 0 + 3)]    = [119, 124]

B_min = 196  >  max( C_max = 104,  E_max = 124,  A_max = 122 )
⇒ B-STRICT-PLURALITY IS CERTIFIED CAP-INVARIANT.
```

**Step 4 — the premises of the refined bound, verified, not assumed.** The bound is
sound only if every retained row and every `A`-world front row was actually classified
(an unclassified row is as unresolved as a timed-out one). Measured coverage against
the cache:

```
retained rows classified, all stages : 16 170 / 16 170  = 1.0000   (= 539 worlds x 30 seeds)
A-world front rows classified        : 42 411 / 42 411  = 1.0000
worlds with >= 1 UNCLASSIFIED retained row :        0
```

Both premises hold exactly. (`B`/`C`/`E`-world *non-retained* front rows are 10–31 %
covered, as the lazy witness protocol intends — and by Step 3 they cannot move those
worlds.)

**Conclusion, corrected.** On the sealed x86 corpus that actually produced
`X86_E2A_SEAL.json`, **E2a's Gate-2 `B`-strict-plurality survives the Gate-1
determinacy standard.** `LOCKED_EXECUTE_E4A` was determinate on its own corpus. It
remains stripped of forward-licensing force — but by ratified **D5** (composition /
role), **not** by any indeterminacy of measurement, and this document must not be cited
for the latter.

**What survives.** The instrument defect is real and unaffected by this retraction:
`SIMPLIFY_TIMEOUT_SECONDS = 5` is a wall-clock budget; the label is a function of host
speed; the bias is one-directional (timeout ⇒ `g2_correct = false` ⇒ earlier-stage
loss); and it is concentrated where the bias predicts — **59.8 % of `NEVER_ON_FRONT`
worlds (73/122) rest on at least one abandoned row**. It happens not to have been
decision-changing here because those 73 worlds' timeouts land on non-retained rows, so
they can only move `A → B` and cannot reach the plurality contest. **That is luck, not
design.** The ARM corpus's exposure is 3× worse (834 rows, 237 of 530 worlds = 44.7 %),
the parity artifact states its 1/530 observed mismatch is a **lower bound**, and no
equivalent retained-row analysis has been done there. The §5.6 remedies stand
unchanged: a defect that is decision-neutral by accident on one corpus must still be
engineered away before it is relied on for a new one.

### 5.6 How the new design must neutralize it

**N1 — The classifier label must be a pure function of the expression string.**
Not of the host, not of the clock. Build a **sealed expression → label table**,
computed once with escalation to completion, hashed, and committed. Classification at
scoring time is then a lookup, and cross-architecture parity becomes a hash comparison
rather than a re-run.

**N2 — Two-tier budget, CPU time not wall clock.** Tier 1: `time.process_time` budget
of 60 s per distinct expression (12× the frozen 5 s, and CPU-time so it is not a
function of load or co-tenancy). Tier 2: any expression still unresolved **and
decisive** — i.e. whose resolution changes some world's stage under the monotone
bound — is escalated with **no cap**. Gate 1 precedent: 6 decisive expressions,
5.5–21.8 s each. The cost is single-digit CPU-hours; the alternative costs hundreds of
worlds (§3.1).

**N3 — A cap may never become a classification.** Frozen `befca0d` §2.10 already
forbids a timeout "silently becoming `None`". The determinacy bound (§6) exceeds that
requirement: it refuses to let the cap decide at all.

**N4 — Two-architecture parity as an admissibility precondition.** Re-classify a
prespecified 2 000-expression audit sample on a second architecture; require **0**
label mismatches. Under N1 this is guaranteed by construction, so the check is a proof
obligation, not a gamble.

**N5 — Report `g` in the seal.** `INDETERMINATE_WORLDS`, `unresolved_rows / total_rows`,
and `g₁, g₂, g₃` are mandatory sealed fields. `g` drives the §3.3 top-up rule.

---

## 6. UNRESOLVED / INVALID HANDLING

### 6.1 The monotonicity lemma (this is what makes the bound cheap)

Let each front row `r` carry a label `λ(r) ∈ {CORRECT, INCORRECT, UNRESOLVED}` from the
frozen `g2_contract` under the N2 budget. A **resolution** `ρ` assigns each UNRESOLVED
row to `{CORRECT, INCORRECT}`; write `ρ_⊥` for all-INCORRECT and `ρ_⊤` for
all-CORRECT. Order the stages `A ≺ B ≺ C ≺ E`.

> **Lemma.** `σ(w, ρ)`, the frozen §2.7 / §6-predeclaration stage of world `w` under
> resolution `ρ`, is monotone non-decreasing in `ρ`.

*Proof.* `correct_on_front(seed)` and `retained_correct(seed)` are disjunctions /
indicators over row labels, hence monotone. Crucially, the **cross-seed winner and its
representative are label-independent**: `rc5_selection.group_and_select` groups the 30
retained candidates by `identity_contract.template_key` and takes the largest class
with a lowest-ordinal tie-break — none of which reads `g2_correct`. And
`retained_by_argmax_score` is a score comparison, also label-independent. So the only
thing `ρ` can change is *whether the (fixed) representative is judged correct*, plus
the two monotone predicates upstream. Every branch of the decision tree therefore moves
weakly later. ∎

**Corollary.** Each `S_j` is monotone non-decreasing in `ρ`, so

```
S_j^min = S_j(ρ_⊥)      S_j^max = S_j(ρ_⊤)      g_j = S_j^max − S_j^min
```

are computed in **two passes**, not `2^U`. This is the property that makes the
cumulative parameterization (§1.2) the right one — the conditionals `S₂/S₁`, `S₃/S₂`
and the marginal shares `π_B = S₁−S₂`, `π_C = S₂−S₃` are **not** monotone (they have a
random denominator / are differences of monotone terms), and would require the full
lattice enumeration.

### 6.2 How UNRESOLVED enters the statistic — recommendation

**Interval-valued / worst-case-bounded. Not excluded, not imputed, not point-estimated.**

Excluding unresolved worlds is the worst option available: §5.5 shows the
contamination is 60 % concentrated in a single stage, so complete-case analysis is
**informatively missing** and biases `S₁` upward by construction. Imputation requires a
model of `simplify`'s termination behaviour, which nobody has. The bound is the only
treatment that cannot be wrong.

### 6.3 The acceptance predicate under the bound

For `j = 1, 2, 3` let `[L_j(ρ), U_j(ρ)]` be the 95 % standardized BCa bootstrap
interval computed with resolution `ρ`. By §6.1 the interval is monotone-shifted in `ρ`,
so "the equivalence claim holds for **every** consistent resolution" reduces to two
evaluations:

```
STAGE_EQUIVALENCE_j  ⟺  L_j(ρ_⊥) ≥ S⁰_j − δ   AND   U_j(ρ_⊤) ≤ S⁰_j + δ
```

This mirrors Gate 1's logic exactly: *a class is reported only when it is invariant
over every resolution of its unresolved rows*, and a cap can only ever refuse to
decide, never decide wrongly.

**Achievable? Yes.** Achievability rests entirely on the monotonicity lemma, which
holds for the cumulative parameterization and for the frozen selection code as written.

**What it costs in power.** Exactly `g_j`, subtracted from the margin — the acceptance
condition is equivalent to requiring `2·z·SE_j + g_j ≤ 2δ`. The cost in worlds is the
§3.1 table: `g = 0.01` costs 148 worlds relative to `g = 0`; `g = 0.02` costs 395;
`g = 0.03` costs 852. **That is the entire economic argument for N2's escalation
protocol.** Gate 1 achieved 158/51 411 = 0.31 % unresolved rows and **0 indeterminate
cases** across 144; the same discipline here should yield `g < 0.005`.

### 6.4 Corpus-level determinacy gate (prespecified, endpoint-blind)

```
DETERMINACY_OK  ⟺  g_j ≤ 0.010  for j = 1,2,3
```

Violation triggers the §3.3 blinded top-up, **not** a change of margin, **not** an
exclusion, **not** a re-read of the endpoint.

### 6.5 Other invalid categories

| Category | Treatment |
|---|---|
| Search execution failure (world produces no front) | **Regenerate under the same frozen seed.** A missing world breaks the exact-composition precondition C1. Report count. |
| Parse failure on a front row (`parse_ok = false`) | `INCORRECT` — deterministic, host-invariant, already the frozen semantics. Not UNRESOLVED. |
| Retention-identity control mismatch (§2.5 control 1) | **Hard stop.** Not a statistical issue; the instrumentation changed the search and no record may be used. |
| Escalation still unresolved after tier 2 | World is `INDETERMINATE`; it enters the bound as an UNRESOLVED world and inflates `g`. Counted and sealed, never dropped. |

---

## 7. DEV / EVAL

### 7.1 Is a split needed for validity? No. Is one needed anyway? Yes — a different one.

The classical selective-inference concern requires a **choice made from the data**.
Here the qualification rule, the margin, the routing rule, and the endpoints are all
frozen before any world exists, so no split is required for the α to be valid.
Qualification → routing is a fixed-sequence gatekeeping procedure and preserves FWER.

### 7.2 But there *is* a real leakage channel, and I name it for P2

If the surface must match Held-out's `S` vector, then its marginal vector is forced
near Held-out's, whose argmax non-success class is `LOST_IN_CROSS_SEED` (71/144).
Conditioning on qualification therefore **truncates the sampling distribution of the
routing statistic toward the Held-out configuration.** The routing answer would then be
partly inherited from E2b — which is `DECISION_INADMISSIBLE` under `befca0d` §2.3/§2.4
and under ratified D5/§5 of the ratification record. This is a genuine
governance-statistics defect and P2 will find it. I state it first.

**It is not fatal, and here is the honest accounting.** Held-out enters the routing
path only through a **binary gate** — at most 1 bit. It does not enter the routing
estimate, which is computed from the new surface alone. The remedy is not to hide the
conditioning but to make the routing certification robust to it:

**R1 — Fixed-sequence gatekeeping.** Routing is read only if `QUALIFIED`. Never the
other way round; never jointly.

**R2 — Certified routing margin, not bare argmax.** §5.3 shows argmax alone is
non-identifiable (0.23 pp separation on the standardized E2a stratum). Require:

```
ROUTING_CERTIFIED  ⟺  the argmax over {π̂_A, π̂_B, π̂_C} is the SAME under ρ_⊥ and ρ_⊤
                      AND  LCB₉₅( π̂_top − π̂_second ) > 0  under BOTH resolutions,
                      with Var(π̂₁−π̂₂) = (π̂₁ + π̂₂ − (π̂₁−π̂₂)²)/n
```

Certification power at a Held-out-like truth (`π_C = 0.4931`, `π_B = 0.3819`, margin
0.1111):

| n | SE | 95 % LCB | verdict |
|---:|---:|---:|---|
| 288 | 0.0547 | +0.0038 | certified (barely) |
| 384 | 0.0474 | +0.0182 | certified |
| **576** | **0.0387** | **+0.0353** | **certified with margin** |

Routing is **not** the binding constraint; qualification is. At n = 576 routing
certification has comfortable headroom.

**R3 — Report the leakage bound.** Publish `π̂` unconditionally *and* the worst-case
routing conclusion over the entire qualification acceptance region — i.e. does the
argmax hold at every point of `{S : |S − S⁰| ≤ δ}` consistent with the observed data?
If not, `ROUTING_INDETERMINATE` is the correct terminal state and must be reported as
such rather than resolved by preference.

**R4 — If the protocol owner wants the leakage channel closed outright**, the price is
a 2:1 prespecified split by replicate index (Q = replicates 1–32, R = replicates
33–48), sealed before scoring. Then `n_Q = 384` (below the 555 requirement — under-
powered qualification) and `n_R = 192` (routing LCB fails, §7.2 table). **A split at
n = 576 breaks both halves.** Closing the channel by splitting costs
`n = 555 + 430 ≈ 1 000 worlds ≈ 73 CPU-hours`. That is the real, quantified price of
the clean design, and it is the protocol owner's call, not mine. My recommendation is
R1–R3 at n = 576.

### 7.3 The split that *is* free and that you should take

```
DEV  = the existing E2a corpus (results/e2/run_x86_e2a_v1)
EVAL = the new 576-world surface, scored exactly once
```

E2a is already fully seen, hostile-audited, and **ratified as invalidated for
calibration (D5)**. That makes it worthless as evidence and *ideal* as an engineering
dev set: schema conformance, the determinacy-bound implementation, the escalation
protocol, the bootstrap harness, runtime and memory profiling, the OOM mitigations, and
the two-architecture parity check can all be developed and debugged against it at
**zero additional scientific compute and zero leakage** — nothing about E2a can
contaminate a decision it is already barred from licensing.

**Discipline:** the analysis code is frozen and hashed against E2a **before** the first
EVAL world is generated. EVAL is scored **once**. No second look.

---

## 8. THE COMPLETE ACCEPTANCE RULE, AS A DECIDABLE PREDICATE

Everything below is fixed now and computable mechanically from the sealed EVAL corpus.

```
CONSTANTS (all frozen before any EVAL world exists)
  S⁰      = (130/144, 75/144, 4/144) = (0.902778, 0.520833, 0.027778)
              [sealed Held-out attribution, ratified D1: A=14 B=55 C=71 E=4]
  δ       = 10/144 = 0.0694444…            [PE2-4 / Gate-1 materiality tolerance]
  α       = 0.025 one-sided per side  ⇒  95 % two-sided interval containment
  w_k     = 1/12 for each of the 12 Held-out cells {F01..F05,F08,F09,F10,F11,F12,F17,F18}
  n       = 576 worlds (12 cells × 48 replicates), 30 seeds per world
  B       = 20 000 bootstrap replicates, stratified by cell, BCa
  g_max   = 0.010

ADMISSIBILITY PRECONDITIONS  (all must be YES; each is endpoint-blind)
  P1  COMPOSITION_EXACT      : every cell has exactly 48 completed worlds; 0 missing, 0 duplicate
  P2  SEEDS_EXACT            : every world has exactly 30 completed seeds
  P3  RETENTION_IDENTITY     : §2.5 control 1 byte-identical on the control world set
  P4  SCHEMA_COMPLETE        : all §2.4 fields present incl. `admissibility`; 0 imputed
  P5  HOST_INVARIANT_LABELS  : sealed expression→label table; 2 000-expression
                               two-architecture audit returns 0 mismatches
  P6  DETERMINACY_OK         : g_j = S_j(ρ_⊤) − S_j(ρ_⊥) ≤ 0.010 for j = 1,2,3
                               [violation ⇒ blinded top-up to n = 816, §3.3; not a re-read]
  P7  NO_MASS_POWER          : 0 `mass_power` worlds in the primary population

PRIMARY ENDPOINT
  Ŝ_j(ρ) = Σ_k w_k · ( 1/n_k · Σ_{w ∈ cell k} reach_j(w; ρ) )        j = 1,2,3
  [L_j(ρ), U_j(ρ)] = 95 % stratified BCa bootstrap interval of Ŝ_j(ρ)

ACCEPTANCE PREDICATE
  STAGE_EQUIVALENCE_j  :=  ( L_j(ρ_⊥) ≥ S⁰_j − δ )  ∧  ( U_j(ρ_⊤) ≤ S⁰_j + δ )

  QUALIFIED  :=  P1 ∧ P2 ∧ P3 ∧ P4 ∧ P5 ∧ P6 ∧ P7
                 ∧ STAGE_EQUIVALENCE_1
                 ∧ STAGE_EQUIVALENCE_2
                 ∧ STAGE_EQUIVALENCE_3

  IF ¬QUALIFIED  →  terminal state SURFACE_NOT_QUALIFIED.
                    The surface is NOT decision-admissible. No E4 arm is licensed.
                    The failing stage(s) are reported. No margin, endpoint, weight,
                    stratum, or exclusion may be revised in response.

ROUTING  (fixed-sequence; evaluated only if QUALIFIED)
  π̂(ρ) = ( 1−Ŝ₁(ρ), Ŝ₁(ρ)−Ŝ₂(ρ), Ŝ₂(ρ)−Ŝ₃(ρ), Ŝ₃(ρ) )   over (A, B, C, E)

  ROUTING_CERTIFIED := argmax over {A,B,C} identical under ρ_⊥ and ρ_⊤
                       ∧ LCB₉₅(π̂_top − π̂_second) > 0 under both,
                         Var = (π̂_top + π̂_second − (π̂_top − π̂_second)²)/n

  IF ROUTING_CERTIFIED, apply frozen §2.9 verbatim:
      argmax = B (LOST_IN_RETENTION)   → RC3 confirmed → licenses E4a
      argmax = A (NEVER_ON_FRONT)      → RC4 confirmed → E3 already answered:
                                          affine & exponential MARGINAL,
                                          search_side_attribution_licensed = false
                                          ⇒ E4b/E4c/E4d NOT licensed on those families
      argmax = C (LOST_IN_CROSS_SEED)  → RC7 → licenses E4f
  ELSE  →  ROUTING_INDETERMINATE.  No E4 arm licensed. Report and stop.
```

**Nothing in this predicate reads the EVAL numbers before it is fixed.** It should be
written to file, hashed, and committed before the first EVAL world is generated, per
ratification §5 item 7.

---

## 9. THE SINGLE BIGGEST STATISTICAL THREAT

**REVISED after the §5.3 / §5.5 corrections.** My original nomination (the timeout
instrument) survives as the runner-up; it is displaced by a threat the corrections
exposed.

### 9.1 Primary threat — the stage ORDERING is not identified on any existing surface

§2.9 routes on `argmax` over `{π_A, π_B, π_C}`. That argmax is **statistically
undetermined on every surface the programme currently holds**:

| Surface | `π_B − π_C` | 95 % CI | identified? |
|---|---:|---|:--:|
| E2a raw (n=539) | +17.44 pp | — | composition-confounded (§5.2) |
| E2a std. on family, pooled (n=432) | +7.25 pp | (−1.46, +15.97) | **no — CI covers 0** |
| E2a std. on family, noise-matched (n=144) | −0.23 pp | (−15.85, +15.39) | **no — CI covers 0** |
| Held-out / E2b (n=144) | −11.11 pp | — | `DECISION_INADMISSIBLE` by §2.3/§2.4 and D5 |

The one surface with a clear ordering is the one barred from licensing anything. The
surfaces that may license are the ones that cannot resolve it. And the two admissible
conditionings of E2a **point in opposite directions** while each fails to exclude zero.

This threat dominates because it is the *decision* quantity, not a nuisance: an
unidentified argmax means `ROUTING_INDETERMINATE`, which means no E4 arm is licensed
regardless of how well the surface qualifies. It also cannot be fixed by analysis —
only by n. Quantified: certifying a Held-out-like margin (0.1111) at 95 % needs
n ≥ 288; the recommended n = 576 gives an LCB of **+0.0353**, versus E2a's ±15 pp.
**This is the load-bearing argument for spending the 42 CPU-hours**, and it is
*strengthened*, not weakened, by the finding that composition explains only 68–77 % of
the divergence.

Secondary consequence, already built into the design: because the ordering is fragile,
§7.2 R2's certified-margin requirement is not optional belt-and-braces. Bare `argmax`
would have "resolved" the noise-matched E2a stratum at a 0.23 pp separation.

### 9.2 Runner-up — a directionally biased, host-dependent measurement instrument

`SIMPLIFY_TIMEOUT_SECONDS = 5` is a wall-clock budget, so the same classifier assigns a
different scientific label to the same expression as a function of CPU speed and load.
Every timeout collapses to `g2_correct = false`, and because `reach_front /
reach_retain / reach_win` are monotone in the row labels, **every timeout biases every
stage-survival estimate downward** — it manufactures `NEVER_ON_FRONT`. Measured:
**59.8 % of E2a's `NEVER_ON_FRONT` worlds (73/122) carry at least one abandoned row**;
the ARM corpus is 3× worse (237 of 530 worlds) and its observed mismatch rate is stated
to be a lower bound.

**It was not decision-changing on the x86 E2a corpus** — the refined bound in §5.5
certifies `B`-plurality — **because those 73 worlds' timeouts happen to sit on
non-retained rows.** That is an accident of where `simplify` gave up, not a property of
the design. It is systematic (does not shrink with n), confounded with the science (it
mimics generation failure), non-reproducible across hosts (so replication does not
control it), and it eats the equivalence margin at ≈150 worlds per percentage point of
determinacy gap (§3.1). **Engineer it away (§5.6 N1–N5), do not bound it away.**

### 9.3 Third — the two-sample infeasibility (§4.4)

The sealed 144-case comparator's own variance on `S₂` exceeds the entire margin budget
by 2.2×, so **no surface of any size** passes a two-sample equivalence test at
δ = 10/144. The fixed-target framing is load-bearing and anti-conservative, and is
declared here in advance rather than discovered afterwards.

## 10. Numbers appendix — provenance of every figure

| Figure | Source |
|---|---|
| Held-out `4 / 71 / 55 / 14`; `S⁰ = (0.9028, 0.5208, 0.0278)` | `GATE_1_DEFINITIVE.md` §2; `ATTRIBUTION_REVISION.md` §1; ratified D1 |
| `δ = 10/144` | `f4c1105:…RETENTION_REMEDIATION_PREREGISTRATION.md` §4; `MURU_V2_G2_PARETO_STUDY_DESIGN.md:466` (PE2-4) |
| §2.6 three conditional stages; per-family/per-regime stratification | `befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.6 |
| Four-way partition; `C ∪ D = LOST_IN_CROSS_SEED` | ibid. §2.7; `MURU_V2_E2_PREDECLARATION.md` §6 |
| `SEEDS_PER_CASE = 30` frozen | ibid. §2.5 control 2 |
| E2a `A=122 B=196 C=102 D=0 E=119`, n = 539 | `results/e2/run_x86_e2a_v1/worlds_shard_*.jsonl`, recomputed here |
| Held-out cell map (9 affine / F09 sat / F10 int / F18 exp) | `v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv`, recomputed here |
| Per-family `S_j` at `noise_sd = 0.02`; standardized `S = (0.9144, 0.4583, 0.0000)` | recomputed here from the E2a world records |
| `TV` raw 0.3221 (46.4 cases); std. pooled 0.1026 (14.8); std. noise-matched 0.0741 (10.7) | recomputed here; pooled figure independently reproduced from the coordinator's recomputation to 4 dp |
| Retained-row timeout split (A 73→2, B 20→0, C 3→3, E 1→1) and refined bound | joined here; premises verified at 16 170/16 170 retained rows and 42 411/42 411 A-world front rows classified |
| E3 family classifications, `search_side_attribution_licensed` | `muru-authority/1d20731-e3-identifiability:E3_RESULTS.json`, `frozen_operating_point_disposition` |
| E3's `0.10` false-structure bar | ibid. `study_validity.bic_criterion` |
| `397` timeout expressions; `97/539` worlds; per-stage 73/20/3/1 | joined here: `candidates_shard_*.jsonl` × `/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3` |
| `834` rows / `237` of `530` worlds; wall-clock root cause | `results/e2/cloud_x86_parity/CLOUD_X86_PARITY_QUALIFICATION.json` |
| Gate-1 determinacy method; `158/51 411 = 0.31 %`; 101/101 validation | `GATE_1_DEFINITIVE.md` intro & §6; `FINAL_TERMINAL_REPORT.md` §3 |
| Wall time 262.5 s/world mean, 39.3 CPU-h for 539 | recomputed here from `wall_seconds` |
| All power / DEFF / seed-sensitivity / routing-LCB tables | computed here with `scipy 1.18.0` under `/home/aryav_thakur/venv/bin/python` |

---

## 11. Revision record

| # | Change | Trigger |
|---|---|---|
| R1 | "91 % of TV divergence removed" → **77.0 %** (noise-matched) / **68.1 %** (pooled). Arithmetic error: a reduction computed on the conditional `P_win\|retain` was attached to the TV figure. | coordinator recomputation |
| R2 | "Standardization flips the routing argmax B→C, agreeing with Held-out" → **WITHDRAWN.** The flip is conditioning-specific and, at −0.23 pp with a ±15.6 pp CI, not identified. Pooled conditioning leaves `B` ahead by 7.25 pp, also not identified. | coordinator recomputation |
| R3 | "E2a's `B`-plurality is not cap-invariant; `LOCKED_EXECUTE_E4A` was never determinate" → **WITHDRAWN.** The refined bound using `retained_by_argmax_score` **certifies** invariance (`B∈[196,267]` vs `C∈[99,104]`). The published coarse bound was an over-approximation of the reachable set. | own re-derivation on the coordinator's challenge |
| R4 | Standardization variable made explicit: `truth_family` (4 levels) for the E2a diagnostic; the 12 `F` **conditions** only for the prospective design, where they are exact by construction. E2a does not span the 12 conditions and is never reweighted on them. | P1 via coordinator |
| R5 | §9 primary threat changed from the timeout instrument to **non-identification of the stage ordering**. | consequence of R2 |

**Unchanged by this revision:** the primary endpoint, the acceptance predicate, the
margin δ = 10/144, the sample size n = 576, the multiplicity treatment, the UNRESOLVED
bound, and the dev/eval posture. The corrections strengthen the case for the
replacement surface: E2a fails the frozen 10-case tolerance under **both** admissible
conditionings (10.7 and 14.8 cases), and the routing ordering it would have to supply
is undetermined at any conditioning.

---

*P3 — STATISTICAL / IDENTIFIABILITY. Submitted to the MURU v2 design council.*
