# P1 — SCIENTIFIC DESIGN PROPOSAL

**Agent:** P1 (scientific design), MURU v2 re-entry design council
**Status:** DESIGN PROPOSAL. Not a protocol. Not frozen. Produced results-blind.
**Date:** 2026-08-19
**Authority to exist:** `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10 — construct, results-blind,
the prospectively frozen decision-admissible calibration/re-entry protocol required by D3 items 1–7.
**Nature:** a **prospective post-Gate-1 protocol-owner amendment**. It is *not* historically
preregistered and must never be described as such.

**Proposed experiment identifier: `E7 — CALIBRATION PARTITION RE-ENTRY SURFACE`.**

---

## 0. The one-paragraph recommendation

Stop trying to *mimic* the Held-out regime with a hand-tuned synthetic factorial. **Draw the
calibration surface from the benchmark's own generator, on its own condition grid, in a new
`calibration` partition disjoint from `held_out`.** Qualification then holds *by construction and
by design-time provenance* — the surface is an independent draw from the same experimental design —
and needs **zero bits of E2b**. Route on an **interventional counterfactual-recovery contrast**
computed post-hoc on persisted fronts, not on the four-way first-loss plurality, because the
plurality is a statistic E2b already contains and is, on my own projection, a near-tie that n=144
cannot resolve. Confine E2b to a **halt-only veto applied after the routing verdict is hash-sealed**.
Score everything with the **bounded-determinacy evaluator**, never a wall-clock cap. x86 is
acceptable. 252 worlds × 30 seeds, ~30–40 CPU-hours.

I expect this protocol's most likely honest outcome to be `ROUTING_INDETERMINATE`. I am proposing
it anyway, and §10 says why the council should accept that before freezing it.

---

## 1. The scientific question, in one sentence

> On an independent draw from the benchmark's own G2 condition grid — the same generator, the same
> twelve experimental conditions, the same coefficient and noise design as the Held-out population,
> but a disjoint set of cases never used for any endpoint — **which single pipeline stage
> (generation, within-seed retention, cross-seed identity voting) accounts for the largest share of
> G2 loss that a single-factor repair actually recovers, and does that recovery exceed the surface's
> own sampling noise?**

Two clauses matter and are deliberate.

**"the largest share of G2 loss that a single-factor repair actually recovers."** The original
question (§2.1 `H_retain` / `H_generate` / `H_partial`; §2.9's licensing table) asks which stage
*first loses* the signal, in order to license the *smallest matching repair*. First-loss attribution
is a **proxy** for recoverability, and v1's catastrophe was precisely that the proxy was
mis-assigned by one pipeline stage. First-loss and recoverability are not the same functional: a
case can be `LOST_IN_CROSS_SEED` and be recovered by no voting arm in the declared space, and a case
can be `LOST_IN_RETENTION` and be recovered by a voting change. I therefore **measure both**, report
the four-way partition as the descriptive endpoint (preserving comparability with E2a, E2b and v1
exactly), and **route on the recovery contrast**, which is the quantity that "smallest matching
repair" actually names.

**"exceed the surface's own sampling noise."** §2.9's rule is a bare plurality — "`LOST_IN_RETENTION`
is the largest non-success class". A bare plurality over a population whose composition is a free
design choice is not a scientific criterion; it is a knob. §7 of this document shows it is a knob
that, on the sealed evidence, swings the verdict. Every routing comparison here therefore carries a
pre-declared interval and an explicit `INDETERMINATE` outcome.

---

## 2. What "qualified" must mean, and the circularity problem

### 2.1 The trap, stated precisely

The council's hard constraint: E2b is `DECISION_INADMISSIBLE` (ratification §5). It may falsify; it
may not license. But §2.3 of `befca0d` demands the calibration surface "reproduce the Held-out
regime". If reproduction is *defined* as agreement with E2b, and routing is a function of the
surface, then routing is a function of E2b through surface selection. P2 will drive a truck through
that.

**Why option (a) alone is insufficient.** "Use E2b only as a one-way falsifier, then route from the
surface" fails whenever the qualification statistic and the routing statistic are dependent. Take
the degenerate case: qualify on "`LOST_IN_CROSS_SEED` is the plurality (as E2b found)", route on
"the plurality class". PASS ⟹ route to cross-seed, with probability one. One-way-ness bought
nothing. Directionality is not a defence; **functional independence** is. Any acceptable design must
make that independence a *property it can exhibit*, not an assertion.

**Why option (d) alone is insufficient.** A DEV/EVAL split protects against overfitting the
*analysis* to the *sample*. The leakage here is upstream of the sample: it is in the surface's
**generator parameters**, which both halves share. Splitting a tuned surface gives two tuned halves.
(I adopt the split anyway — §4.5 — for the different and real problem of arm-selection bias.)

### 2.2 My answer: provenance, not similarity

**Qualification is a statement about where the surface came from, not about what it resembles.**

A calibration surface is qualified iff it is an **independent draw from the same experimental design
as the target population**. That is the definition of a valid calibration set everywhere else in
statistics, and it is achievable here *literally*, not approximately, because the Held-out G2
population is itself synthetic and its generator is in the repository.

The frozen registry (`src/muru/paper_benchmark/registry.py`) already declares:

```
PARTITIONS            = ("development", "held_out", "challenge")
PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3}
```

Held-out G2 is **12 benchmark families × 12 replicates = 144 cases**, and — this is the finding that
reorganised my whole design — those twelve families are not twelve replicates of a truth law. They
are **twelve distinct experimental conditions**, declared prospectively in the registry, results-blind,
long before any E2:

| Family | Condition (registry `name`) | truth_family |
|---|---|---|
| F01 | noiseless scalar collapse | affine |
| F02 | moderate-noise scalar collapse | affine |
| F03 | stronger realistic noise | affine |
| F04 | missing-one-energy | affine |
| F05 | boundary-scale | affine |
| F08 | simple descriptor law | affine |
| F09 | nonlinear descriptor law | saturating |
| F10 | interaction law | interaction |
| F11 | irrelevant distractors | affine |
| F12 | correlated distractors | affine |
| F17 | **equivalent symbolic forms** | affine |
| F18 | algebraically difficult, predictively simple | exponential |

**E2a instantiated none of the condition axes that stress the layers under investigation.** E2a was
`5 truth families × 3 coefficient regimes × 3 noise levels × 12 replicates`. It has no missingness
condition, no boundary condition, no irrelevant-distractor condition, no correlated-distractor
condition, and — decisively — **no equivalent-symbolic-forms condition**, a family whose declared
scientific question is literally *"canonicalize equivalent laws"* and whose expected behaviour is
*"score equivalent forms once"*. F17 is a condition purpose-built to stress the cross-seed identity
contract. A calibration surface that omits it cannot calibrate cross-seed voting.

**This argument cites the registry and nothing else.** It contains no outcome, no E2b number, no E2a
number. It is sufficient on its own to explain why E2a is not a Held-out-facing calibration surface,
and it is therefore an *independent* corroboration of ratification D5 that does not lean on the
E2a/E2b divergence at all.

### 2.3 The proposal: a new `calibration` partition

Prospectively amend the registry with a fourth partition, appended last so that no existing
`case_ordinal` moves:

```
PARTITIONS            = ("development", "held_out", "challenge", "calibration")
PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3, "calibration": 18}
```

- Same generator (`paper_benchmark/generator.py`), same `GENERATOR_VERSION`, same `ROOT_SEED`.
- Different replicate indices ⟹ different `derive_seed(case_id, ·)` ⟹ statistically independent
  compounds, laws, responses, missingness draws.
- Same twelve G2 conditions at equal weight, exactly as Held-out.
- **Nothing in this protocol ever touches, reads, or re-runs a `held_out` case.**

Engineering obligations this creates, all tractable and all following the existing A3.5 precedent:

1. `rc5_seeds.A35_TOTAL_CASES = 380` and its band `[2_100_000_000, 2_100_011_399]` are exhausted.
   A **new declared seed band** is required in `seed_band_registry.DECLARED_BANDS`, in a **new
   module importing the frozen ones** (A3.5 implementation obligation 9 — frozen modules are
   byte-pinned by `pb_30`/`pb_33`/`pb_34` and must not be mutated). Band disjointness is checked by
   the existing `assert_governance_clean`. Appending the partition last is what keeps ordinals
   0–379 — and therefore every Held-out search seed — bit-identical. **This must be verified, not
   assumed, in preflight: recompute all 380 existing ordinals and seeds before and after the
   amendment and require byte equality.**
2. `resolve_case_id` / `iter_case_ids` need no change beyond the two constants.
3. 18 is divisible by 3, so F19's and F20's three-variant cycles stay balanced, in the whole
   partition and in each DEV/EVAL half.

**Pre-declared fallback (attempt 2, parameters fixed before attempt 1 runs).** If the protocol owner
refuses a registry amendment, use `development` (4 × 12 = 48 G2 cases) ∪ `challenge` (3 × 12 = 36)
= **84 G2 cases**, which exist today with valid ordinals and seeds. This is the honest fallback and
it costs power: 84 vs 216, and `development` carries a contamination caveat (it is the partition the
programme was permitted to look at during v1). It is written down here so that no attempt's
parameters can ever be chosen in response to another attempt's result.

### 2.4 The three-gate ordered architecture

```
GATE Q  QUALIFY   inputs: registry + generator provenance + v1-sealed truth-blind descriptors
                  E2b contribution: ZERO BITS
                            |
                            v
GATE R  ROUTE     inputs: the new surface only
                  output hash-sealed and appended to a hash-chained event log
                  BEFORE any process is permitted to read Gate V
                            |
                            v
GATE V  VETO      inputs: Gate R's sealed output + E2b
                  output space: { STANDS , HALTED }   -- nothing else
```

The circularity answer has five components. I claim all five, and I claim the design fails without
any one of them.

**(i) Provenance separation — the load-bearing one.** Gate Q reads the registry, the generator, and
`v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv` (sealed at `4bfd4a8`, before E2b existed).
It reads no E2b artifact. Not as a rule of conduct — *as a data-flow fact that a static checker can
verify*, in exactly the manner §2.3 already mandates for the citation checker.

**(ii) Functional non-identity.** The routing statistic is a counterfactual recovery contrast (§6).
E2b contains the four-way first-loss partition. **Complete knowledge of all 144 E2b labels does not
determine any recovery contrast**, because recovery is defined by re-scoring a persisted front under
an alternative retention or voting rule — a computation over front rows that the partition does not
encode. The sealed record already supplies the constructive fact of the same shape: `ATTRIBUTION_REVISION.md`
§7.3 exhibits 13 `LOST_IN_CROSS_SEED` cases at `seeds_with_retained_correct = 1` whose
front contents can be varied without moving `selection_count` or the representative. Class labels
and front-level counterfactuals are genuinely different functionals of the same corpus.

**(iii) Channel monotonicity.** Gate V's output space is `{STANDS, HALTED}`. A monotone halt-only
channel cannot move probability mass *between* arms; it can only zero the entire vector. Formally,
for every arm `a`: `P(route = a | E2b) ∈ { P(route = a | ∅) , 0 }`. **E2b can subtract; it cannot
select.** Even granting an adversary the maximal assumption — that I secretly tuned the surface
toward E2b — the most that tuning can buy is avoiding a halt. It cannot choose E4a over E4f, because
the arm was chosen by a statistic E2b does not contain, and it was chosen and sealed first.

**(iv) Order enforcement, mechanical.** Gate R is computed by an isolated process that writes a
hash-sealed verdict and appends it to a hash-chained event log (the `AUTONOMOUS_RUN_EVENT_LOG.jsonl`
pattern already used in the Gate 1 adjudication). Gate V is computed by a **different adjudicator**,
after the seal. Out-of-order execution is detectable from the chain. "We looked first" becomes a
falsifiable claim rather than a promise.

**(v) Measured non-determination (`QND`) — the check that turns rhetoric into a measurement.**
Before executing E7, run this on **E2a's sealed corpus**, which ratification D5 explicitly preserves
as valid synthetic-domain diagnostic evidence:

> Enumerate subpopulations of E2a's 539 worlds (stratified resamples over family × regime × noise ×
> replicate). Restrict to those that would PASS Gate Q's measurable clauses. Ask: **is the routing
> verdict constant across the passing subpopulations?**
>
> - If the verdict **varies** among passing subpopulations, Gate Q demonstrably does not determine
>   routing. Proceed.
> - If the verdict is **constant**, Gate Q *is* routing. The design is circular by measurement.
>   **Do not execute.** (Failure mode F2, §7.)

I would rather discover circularity with a cheap analysis on sealed data than argue about it.

### 2.5 What I explicitly reject, and why

- **Option (a) alone** — one-way falsifier before routing. Rejected: directionality does not imply
  independence (§2.1). Retained only as Gate V, *after* the seal, where monotonicity does the work.
- **Option (b) alone** — qualify on a structural property such as "does the surface exhibit a
  measurable cross-seed vs within-seed loss structure at all". Rejected as the *primary* gate: it is
  too weak to have caught E2a. I measured E2a's consensus geometry (§5.3) and it sits close to
  Held-out's; a structural-existence test would have passed E2a. Retained as a secondary
  corroborating clause (Q3), and I disclose its low power rather than dress it up.
- **Option (d) alone** — DEV/EVAL split. Rejected as the answer to circularity (§2.1). Adopted for
  arm-selection bias (§4.5).
- **Option (c), generalised, is what I actually recommend**: qualify on a property derivable from
  the pipeline's and benchmark's own *definitions* — here, the registry's condition grid — rather
  than from any outcome. §2.2 is that answer, taken to its strongest form: not "derive an invariant
  and match it", but "draw from the same design".

---

## 3. Population

### 3.1 The design

**`calibration` partition, 18 replicates per family.**

| Stratum | Families | Replicates | Worlds | Role |
|---|---|---:|---:|---|
| **G2** | F01,F02,F03,F04,F05,F08,F09,F10,F11,F12,F17,F18 | 18 | **216** | primary |
| **NEG** | F07 (mass-only truth), F19 (target-specific null worlds, 3-variant cycle) | 18 | **36** | false-structure control |
| — | F06, F13–F16, F20 | — | 0 | not G2-relevant; **not searched** |

**Total searched: 252 worlds × 30 seeds = 7,560 searches.**

- Truth-family composition follows the registry and therefore reproduces Held-out **exactly**:
  affine 9/12, saturating 1/12, interaction 1/12, exponential 1/12, **`mass_power` 0/12**.
- Coefficient regime: the frozen benchmark draw. **No coefficient sweep.** A sweep is E4e's
  question, not a calibration question, and E2a's three levels (0.25 / 0.40 / 0.55) all sit inside
  the frozen `rng.uniform(0.25, 0.55)` the benchmark already uses, so the sweep bought no regime
  coverage.
- Noise regime: the benchmark's own noise design, which is a *condition axis* (F01 noiseless / F02
  moderate / F03 strong) at 1/12 weight each, not a crossed factor at 1/3 weight each. **This alone
  removes E2a's largest ceiling artefact.**
- Seeds: **30 per case**, frozen `A35_SEEDS_PER_CASE = 30`, frozen ordinal derivation. Non-negotiable
  — changing it would break comparability with v1, E2a and E2b simultaneously, and would silently
  redefine what the 20-of-30 stability gate means.

### 3.2 Why 216 G2 worlds and not more or fewer

1. **Precision parity with the evidence it must explain.** §2.8's own justification for E2a's twelve
   replicates was "matches the v1 per-family case count of 12, so E2a's per-family precision is
   comparable to the evidence it is meant to explain." I keep that principle and add margin: 18 ≥ 12
   per condition, and 216 ≥ 144 overall.
2. **The DEV/EVAL split costs half.** Arm selection on DEV, measurement on EVAL (§4.5). 18 → 9/9
   gives 108 G2 cases per half — still within 25% of Held-out's whole n, and per-condition 9 ≥ ... a
   real replicate count rather than a token one.
3. **Divisibility.** 18 % 3 = 0 keeps F19's three-variant cycle balanced overall *and* in each half.
4. **The routing contrast is paired.** `rec_retention` and `rec_voting` are measured on the *same*
   worlds with the *same* fronts; precision is governed by the discordant-pair count (McNemar), not
   by marginal rates. This is far more efficient than the unpaired between-population comparison
   §2.9's plurality rule implies, and it is why 216 buys more than E2a's 540 did.
5. **Budget.** 252 worlds is ~30–40 CPU-hours (§9) — comparable to E2a's measured 39.3 CPU-hours, on
   a population that can actually answer the question, and it makes all of E4a and E4f free (§9.3).

**If P3 shows 216 is underpowered for the contrast, raise n — do not lower the margin.** I would
rather run 432 worlds (~70 CPU-h) than accept a weaker decision rule. That preference is recorded
here, before any result, so it cannot be reversed after one.

### 3.3 What I deliberately excluded, and the honest disclosure

I exclude `mass_power` and the crossed coefficient/noise factorial. Both exclusions follow from
§3.1's design-provenance rule (the registry has no `mass_power` G2 condition, and no crossed
factorial), so neither is an outcome-driven choice. **But I must disclose that I also observed, in
E2a's sealed corpus, that `mass_power` is 107/107 `SUCCESS` and the `noiseless` arm is a success
ceiling** — i.e. the exclusions are *also* the ones that remove uninformative cells. I did look.
The defence is that the exclusions are entailed by the registry independently of that observation,
and that §7 and §10 put the observation on the record rather than burying it.

---

## 4. The measurement

### 4.1 Execution path — the production path, not a calibration surrogate

Run through **`paper_benchmark/rc5_runner`**, the real v1 production path, with front persistence
added and nothing else changed. `rc5_runner._run_one_seed` already calls
`rc5_selection.select_row_label(outcome.equations)` on PySR's live `equations_` frame. Persisting
that frame therefore yields **every §2.4 field natively**, including `score` and `loss`.

This is not a stylistic preference. **E2a's rescue-v2 candidate schema dropped `score`, `loss`,
`train_r2`, `grammar_complexity`, `parse_ok`, `effective_support`, `template_key` and
`admissibility`** — verified directly on `results/e2/run_x86_e2a_v1/candidates_shard_000.jsonl`.
Without `score`, `select_row_label` raises `SeedExecutionFailure` by design, and **E4a arms R2
(top-k by score) and R4 (accuracy-thresholded parsimony) are unscoreable on the E2a corpus.** R4 is
the arm §3.1 identifies as targeting the observed signature directly and PE4a-1 names explicitly.
An E4a routing decision taken on a corpus that cannot score R2 or R4 is not an E4a decision.

**Hard preflight gate, before world 1:** persist one case, assert all 18 §2.4 fields present and
non-null on every row, assert `select_row_label` runs, assert `admissibility = "DECISION_ADMISSIBLE"`
is stamped at row level. Fail ⟹ stop, do not generate.

### 4.2 The persisted record (§2.4, in full, from inception)

Per (case, seed, front row), before retention is applied:

```
case_id, partition, family_code, variant, replicate, condition_kind,
seed_ordinal_k, seed, front_rank,
engine_complexity, grammar_complexity, expression_string, parse_ok,
train_r2, valid_r2, test_r2, loss, score, invalid_fraction,
effective_support, template_key,
retained_by_argmax_score,
admissibility = "DECISION_ADMISSIBLE"
```

Joined in a **separate scoring pass the search never sees** (§2.4's truth-blind boundary):

```
discovered_family, support_status_vs_truth, family_status_vs_truth,
g2_correct, truth_equivalent, truth_family, truth_support, coefficient_value,
resolution_state ∈ {CORRECT, INCORRECT, UNRESOLVED}
```

Ratification D6 is binding: **any new decision-relevant corpus must satisfy the frozen required
schema from inception.** There is no imputation path and no retrofit path.

### 4.3 Scoring — bounded determinacy, and the retirement of the wall-clock cap

Scoring reuses the frozen definitions (`g2_contract.classify_support` / `classify_family_match` /
`evaluate_g2_event`, `e2_classify.classify_expression`, `discovery.equivalence.algebraically_equivalent`,
`rc5_selection.group_and_select`), executed through the **bounded-determinacy machinery of
`scripts/e2b_bounded_determinacy_evaluator.py`**:

- every front row resolves to `CORRECT` / `INCORRECT` / **`UNRESOLVED`** — `UNRESOLVED` is a cost
  state, never a class;
- the cap exception derives from `BaseException`, deliberately, so `g2_contract`'s seven
  `except Exception: return None` handlers cannot swallow it and silently turn a cap into
  `SUPPORT_UNRESOLVED → not-correct`;
- a case receives a class **only when that class is invariant over every consistent resolution of
  its `UNRESOLVED` rows**, enumerated over the ≤3 booleans the frozen decision tree reads (the tree
  is monotone in "more rows correct", so the two extremes bound every intermediate assignment);
- non-invariant cases escalate to per-expression evaluation to completion under a declared
  escalation budget (Gate 1 used 1,500 s total and escalated 6 expressions at 5.5–21.8 s);
- anything still indeterminate after escalation is reported as `INDETERMINATE` and enters every
  analysis as an explicit third state. **It is never imputed, never dropped, never defaulted to
  not-correct.**

**`SIMPLIFY_TIMEOUT_SECONDS = 5` is retired as a classification rule for this protocol.** §8 gives
the full argument; the short version is that it is the documented root cause of
`NEW_CLOUD_HOST_PARITY_FAILED` and it makes a scientific label a function of host speed.

**Exhaustive, not lazy.** E2a used `lazy_classify`, which short-circuits on the first correct row.
That is a legitimate optimisation for computing `first_loss_stage` alone, but it leaves most rows
unclassified — which is exactly why the parity audit's 1/530 mismatch is an explicit **lower bound**
(834 `SIMPLIFY_TIMEOUT` rows across 237 of 530 worlds = 44.7% exposure, never reached by the lazy
replay). E7 classifies **every row**, memoised by expression string. Cost is analysed in §9; the
compensation is that every counterfactual re-scoring in §4.4 then costs **zero additional
classification**.

### 4.4 What is computed per case

**(A) The descriptive endpoint — the frozen four-way partition (§2.7), unchanged.**

| Label | Condition |
|---|---|
| `SUCCESS` | cross-seed selection returns a G2-correct representative |
| `NEVER_ON_FRONT` | 0 of 30 seeds' fronts contain any correct row |
| `LOST_IN_RETENTION` | ≥1 front contains a correct row, but too few are retained for a correct class to win |
| `LOST_IN_CROSS_SEED` | correct rows are retained by ≥1 seed but the winning class is incorrect |

This preserves the original causal question verbatim, and is directly comparable to E2b's
4/71/55/14 and to E2a's `first_loss_stage` counts under the identity
`A ≡ NEVER_ON_FRONT`, `B ≡ LOST_IN_RETENTION`, `C ∪ D ≡ LOST_IN_CROSS_SEED`, `E ≡ SUCCESS`
(read directly off `e2_aggregate.evaluate_world`'s decision sequence).

**(B) The §2.6 conditional metrics, unchanged**, per condition and per truth family:
`P_front`, `P_retain_given_front`, `P_win_given_retain`, `rank_of_correct`, `score_gap`,
`complexity_gap`, `r2_gap`, `front_size`. These are the mechanism-level quantities and they, not the
marginal counts, are what actually transfers between populations.

**(C) The routing endpoint — the counterfactual recovery vector.** With the front held **fixed**
(zero additional search, per §3.1 and §3.6):

| Quantity | Definition |
|---|---|
| `rec_retention(w)` | 1 if `w` is not `SUCCESS` under (R0, V0) but **is** under (R\*, V0) |
| `rec_voting(w)` | 1 if `w` is not `SUCCESS` under (R0, V0) but **is** under (R0, V\*) |
| `rec_ceiling(w)` | 1 if **no** (R, V) pair in the declared grid makes `w` a `SUCCESS` |

Arm grids, taken verbatim from the frozen design so nothing is invented:

- **Retention (§3.1):** R0 `argmax(score)` (control) · R1 `argmax(valid_r2)` · R2 top-k by `score`,
  k ∈ {1,2,3,5} · R3 whole front, seed votes for its best member by `valid_r2` · R4
  accuracy-thresholded parsimony, ε ∈ {0.001, 0.005, 0.02}.
- **Voting (§3.6 F-ii):** V0 `identity_contract.template_key` (control) · V1
  `(effective_support, discovered_family)` · V2 algebraic equivalence under `discovery.equivalence`.

Note that R2 and R3 change `selection_count`, and therefore change what the 20-of-30 stability gate
means. `selection_count` distribution is reported for every arm, as §3.1 requires — the inflation is
**measured, not assumed away**.

**(D) The safety endpoint — `false_structure_rate`, from inception.** On the NEG stratum (F07
mass-only truths, F19 null worlds), for **every** arm: the fraction on which the pipeline
structurally accepts a non-mass effective support. §3's common control is explicit: *"Reporting a G2
gain without its safety cost is not permitted."* **E2a carried no negative-control stratum at all**,
which means no E2a-licensed arm could ever have been safety-scored. E7 fixes this at the population
level, not as an afterthought.

### 4.5 DEV / EVAL split

Deterministic, pre-declared, stratified, no RNG:

- **DEV** = replicates `r000`–`r008` (108 G2 + 18 NEG). Used to **select** R\* and V\*, one arm each,
  by the frozen §3.1 / §3.6 decision rules: *simplest rule whose G2 improvement over control has a
  Wilson lower bound above 0 and whose `false_structure_rate` stays under the E6 ceiling; ties broken
  by fewest free parameters, then lowest false structure.*
- **EVAL** = replicates `r009`–`r017` (108 G2 + 18 NEG). Used **only** to measure the recovery
  contrast for the already-selected R\* and V\*, and to compute Gate R.

This removes the selection bias that would otherwise inflate whichever arm family has more arms
(retention has 4 arm-types spanning 9 parameter settings; voting has 2). Without the split, the
routing contrast is structurally biased toward retention by construction — a bias that would have
been invisible and would have pointed at E4a.

---

## 5. Gate Q — the qualification statistic

### 5.1 Structure

Gate Q is a **conjunction** of pre-declared clauses. Q1 is the load-bearing one; Q2–Q4 are
corroborating checks that can only ever *reject*.

All comparisons are **equivalence tests** (TOST-style interval tests), never null-hypothesis
significance tests. The claim being made is *similarity*; a non-significant difference test is not
evidence of similarity, and treating it as such is the single most common way a "qualification"
becomes a rubber stamp.

| Clause | What it checks | Source of the comparator | Type |
|---|---|---|---|
| **Q1** | **Design provenance**: same generator, same `GENERATOR_VERSION`, same `ROOT_SEED`, same twelve G2 conditions at equal weight, partition disjoint from `held_out`, all 380 pre-existing ordinals and search seeds byte-identical after the amendment | `registry.py`, `generator.py`, `rc5_seeds.py` — **design-time only, zero outcomes** | construction check, PASS/FAIL |
| **Q2** | **Signal regime**: surface median `descriptor_sd` and `mass_range_ratio` inside the Held-out IQR, and surface IQR overlapping Held-out IQR by ≥50% | `MURU_V1_G2_FAILURE_TAXONOMY.csv` (v1-sealed, **truth-blind**) | interval |
| **Q3** | **Consensus geometry**: distributions of `identity_class_count`, consensus concentration `largest_identity_class_size / seeds_completed`, and the 20-of-30 stability-gate failure fraction | same, **truth-blind** | KS-equivalence + TOST |
| **Q4** | **Retained-candidate geometry**: median retained `valid_r2` and `complexity` inside the Held-out IQR | same, **truth-blind** | interval |

Held-out reference values, read out of the v1 taxonomy (n = 144), recorded here so the comparator is
fixed before any surface exists:

```
descriptor_sd                median 0.2085   IQR [0.1980, 0.2227]
mass_range_ratio             median 5.076    IQR [4.430, 5.951]
identity_class_count         median 11       IQR [7, 19]
largest_identity_class_size  median 17       IQR [9, 22]
consensus concentration      median 0.567    deciles [0.033 … 0.933]
stability-gate failure rate  0.597   (largest class < 20 of 30)
retained valid_r2            median 0.8457   IQR [0.7403, 0.8980]
retained complexity          median 4        IQR [3, 4]
```

**Q2–Q4 are all truth-blind.** Every one is a function of the *retained candidates and the identity
contract only*; none consults the oracle. The four-way partition is truth-dependent. A truth-blind
statistic is not the attribution — that is the functional-independence argument at the qualification
layer, and it is why Q2–Q4 can be checked without an oracle at all.

### 5.2 Setting the equivalence margins without looking at an answer

**Recommended construction, handed to P3 to refine:** set each margin **from the Held-out corpus's
own internal sampling variability**, not from any observed surface value.

Concretely, for the KS-equivalence margin δ on consensus concentration: partition the 144 Held-out
cases into their 12 family_id blocks, form block-jackknife resamples (leave-one-block-out, and
balanced 6-vs-6 block splits), compute the two-sample KS statistic of each resample against its
complement, and take **δ = the 90th percentile of that self-comparison null**.

The resulting criterion reads: **"the surface must be no further from Held-out than Held-out is from
itself."** It is self-calibrating, it is computable before any surface exists, and — the property
that matters — **it contains no free parameter I could move to change an answer.** P3 should
pressure-test whether block jackknife is the right resampling unit (I think it is: the block is the
condition, and condition is the axis along which the surface is constructed) and whether 90 is the
right percentile.

### 5.3 Disclosure: Q3 has low power against E2a's actual defect

I measured E2a's consensus geometry directly, on a stratified 60-world sample (12 per truth family)
of `results/e2/run_x86_e2a_v1`, recomputing `template_key` over the 30 retained rows per world
through the production `identity_contract` and `parse_production_candidate`:

```
                            E2a (n=60 sample)      Held-out (n=144)
identity_class_count            median  9.5            median 11
consensus concentration         median  0.633          median 0.567
stability-gate failure rate            0.55                   0.597
```

**E2a would very likely PASS Q3.** I am recommending Q3 anyway, and disclosing this, because:

- Q3 is not the clause that catches E2a. **Q1 is.** E2a fails Q1 outright — different generator,
  different condition grid, a truth family absent from the target, no missingness / boundary /
  distractor / equivalent-forms conditions.
- Q3 catches a *different* failure that Q1 cannot see: a surface built from the right generator on
  the right grid that nevertheless lands in a different consensus regime (e.g. because of an
  environment or engine change). Both clauses are needed; neither subsumes the other.
- Disclosing that a clause is weak is how the council learns what the gate does and does not buy.
  A qualification test whose power profile is undocumented is a rubber stamp with extra steps.

---

## 6. Routing

### 6.1 The rule, pre-declared in full

Computed on **EVAL only**, for the DEV-selected R\* and V\*:

```
ΔR  = rec_retention rate on EVAL          (recovered by R*, voting held at V0)
ΔV  = rec_voting rate on EVAL             (recovered by V*, retention held at R0)
C   = rec_ceiling rate on EVAL            (recovered by nothing in the arm grid)

LB(·) = pre-declared simultaneous lower confidence bound.
        P1 recommendation: exact paired (McNemar / Wilson-on-discordant) intervals,
        Holm-adjusted across the three comparisons, family-wise alpha = 0.05.
        P3 owns the final method; the requirement P1 fixes is that it be
        simultaneous, paired, and declared before execution.

E6_OK(arm) = arm's false_structure_rate on the NEG stratum is below the E6 ceiling.

if   LB(ΔR - ΔV) > 0  and  E6_OK(R*)                 -> LICENSE E4a ONLY, at arm R*, at its
                                                        DEV-selected parameter value
elif LB(ΔV - ΔR) > 0  and  E6_OK(V*)                 -> LICENSE E4f ONLY, at arm V*
elif LB(C - max(ΔR, ΔV)) > 0                          -> LICENSE E3-GATED SEARCH WORK
                                                        (E4b, then E4c, then E4d), and ONLY for
                                                        the conditions E3 has certified identifiable
else                                                  -> ROUTING_INDETERMINATE
```

**The exoneration branch is preserved verbatim from §2.9 row 4** and is checked *before* the ladder:
if `P_retain_given_front` is inside a pre-declared band of 1 wherever `P_front` is high, **RC3 is
withdrawn and no retention change is licensed regardless of ΔR.** This branch exists so that the
protocol can conclude "the retention rule is fine" — an outcome the licensing table must be able to
reach, or it is not a test.

### 6.2 What a licence is, and is not

A licence names **one arm at one parameter setting** — e.g. "E4a, arm R4, ε = 0.005" — not "E4a".
That is precisely the *smallest matching repair* the programme asked for, and it is stronger than
what §2.9 offered, which licensed a whole arm family.

Every licence carries three binding riders:

1. **The E6 false-structure ceiling is a precondition, not a report.** An arm that recovers cases
   and breaches the ceiling is not licensed. If the E6 ceiling is unavailable at decision time —
   and it may be, since E6 is self-blocked pending exactly this hook — the licence is **conditional
   and non-executable** until E6 supplies it. I flag this as a real dependency in §10.
2. **The licence is scoped to the regime characterised by Gate Q's descriptor vector**, which is
   reported in full alongside the verdict. It is *not* scoped to "Held-out". Nothing in E7 licenses
   a claim about Held-out.
3. **The four-way partition is reported alongside the recovery contrast.** If the two disagree —
   e.g. `LOST_IN_CROSS_SEED` is the plurality but ΔR > ΔV — **that disagreement is itself a
   pre-declared reportable finding** and it *reduces* the licence to conditional. It is the direct
   generalisation of `H_partial`, stated first-class here for the same reason §2.1 stated
   `H_partial` first-class: so it cannot be discovered and then quietly absorbed.

### 6.3 Then, and only then, Gate V

After Gate R is computed, hashed and chained, a separate adjudicator compares the surface's four-way
partition against E2b's `SUCCESS 4 / LOST_IN_CROSS_SEED 71 / LOST_IN_RETENTION 55 / NEVER_ON_FRONT 14`
under a pre-declared divergence tolerance.

- **Not divergent** → `STANDS`. Gate R's licence takes effect.
- **Divergent** → `HALTED`. The routing seal is stamped `NON_LICENSING`, all E4 arms remain
  suspended, and the divergence is escalated to the protocol owner.

This preserves §2.3's falsifying force in full — *"divergence would mean the fresh worlds do not
reproduce the Held-out regime"* — while confining E2b to a channel that is provably incapable of
selecting an arm.

---

## 7. The failure mode: when I would say no valid synthetic calibration surface exists

All five conditions are results-blind and are declared here, before execution.

**F1 — Gate Q fails on both pre-enumerated attempts.** The benchmark's own generator, on its own
condition grid, cannot produce a partition that passes Q1–Q4. Since Q1 is a construction check this
would mean a mechanical failure (ordinal drift, seed-band collision, generator version mismatch), and
Q2–Q4 failing on a same-generator draw would mean **the generator is not stationary across
replicate indices** — a benchmark defect of the first order, and one that would independently
undermine the Held-out result itself. **Verdict: no synthetic calibration surface exists, and the
benchmark needs auditing before anything else proceeds.**

**F2 — `QND` fails.** Gate Q is measured, on E2a's sealed corpus, to *determine* the routing verdict
across all passing subpopulations. Then qualification is routing, the design is circular by
measurement, and I withdraw it. **Do not execute.** No amount of argument substitutes for this
check coming back negative.

**F3 — `ROUTING_INDETERMINATE` at the precision floor.** The contrast's interval straddles zero
*and* the interval width is at the surface's sampling limit — i.e. n cannot separate the stages.
This is not a null result; it is the finding that **the pipeline's G2 loss is jointly attributable
across stages and no single-factor repair is licensable in this regime.** If that is what the data
say, then E4's entire one-factor-at-a-time framing (§3, "Discipline. One factor at a time.") is
inadequate for this regime, and the honest forward path is a jointly-varying design under separate
authorisation — with the §3 warning that "admissibility is not additive" and that any joint study
must re-measure false structure jointly.

**F4 — The scoring layer cannot evaluate the frozen semantics.** `INDETERMINATE`-after-escalation
exceeds a pre-declared ceiling (**recommendation: 5% of worlds**). Then the endpoint itself is not
measurable at finite cost on this population — the honest generalisation of Defect B and of the two
`mass_exponential_descriptor|c_mid|n_strong` worlds that still timed out on x86 at a *patient 600 s*
retry. **Verdict: the G2 contract as frozen is not computable on this population, and that is a
finding about the contract, not about the pipeline.**

**F5 — Gate V vetoes.** The surface is drawn from the same generator, on the same grid, passes every
qualification clause, routes — and then diverges from E2b beyond tolerance. This is the most
scientifically interesting failure available: it would mean the Held-out *design* is reproduced but
the Held-out *behaviour* is not, i.e. the loss mechanism depends on something outside the declared
design. **Verdict: design-matched synthetic calibration is not achievable for this pipeline**, and
the only remaining routes are (i) accept that the causal question cannot be answered under the
decision-inadmissibility constraint and say so, or (ii) petition the protocol owner to re-open E2b's
admissibility on the record — a governance act I have no standing to recommend and explicitly do
not.

F1 and F5 are the two that would genuinely end the programme's synthetic-calibration path. I want
them written down at the same time as the design, not discovered afterwards.

---

## 8. Architecture: x86 is acceptable; ARM64 is not required

### 8.1 What `CLOUD_X86_PARITY_QUALIFICATION.json` did establish

- **Environment reconstruction: EXACT.** Python 3.13.5, SymPy 1.14.0, Julia 1.12.6, PySR 1.5.10,
  SymbolicRegression.jl 1.11.3, PythonCall.jl 0.9.26; dependency lock 50/50 pins, **0 deviations**;
  Julia `Manifest.toml` sha256 identical *and unchanged after `instantiate`*; classifier version hash
  identical to the ARM host's; threading pinned to 1 across Julia/OMP/MKL/OpenBLAS.
- **Two independent corroborations of faithfulness:** the persistent classify cache seeded to
  **143,232 rows / 119,448 distinct expressions — exactly** the ARM counts; and
  `tests/test_raw_search_identity.py` PASSES on x86 (a real PySR fit, every structural field
  byte-identical between `e2_search.run_seed_search` and `raw_search.run_seed_search_raw`).
- **x86 internal determinism: 30/30.**
- **Full-corpus classifier replay:** all 530 completed ARM worlds, `N_MATCH 527`, `N_MISMATCH 1`,
  `ERROR_COUNT 2`. Conclusive coverage 528/530.
- **The single mismatch is diagnosed to the bottom and it is not architecture.** Verbatim:
  *"SIMPLIFY_TIMEOUT_SECONDS = 5 is a WALL-CLOCK budget. The faster x86_64 host completes a sympy
  canonicalization that the slower ARM64/macOS host abandoned, so the same unmodified classifier
  assigns a different scientific label to the same expression purely as a function of host speed."*
  `not_floating_point: true`; *"Same classifier, same input, different outcome — speed, not
  algorithm."* The witness (`mass_saturating_descriptor|c_low|n_default|r007`, seed 2104507054,
  front rank 11) canonicalises in **4.80 s** against a 5.00 s budget — a 200 ms margin — expanding
  to degree 12 with ~90-digit integer coefficients, dominated by `_PyLong_GCD`/`x_divrem`.

### 8.2 What it did **not** establish — the load-bearing gap

**`worlds_executed_on_this_host: 0`.** The audit **replayed sealed ARM candidate rows through the
x86 classifier**. It never re-ran PySR search on x86 and compared the resulting *fronts* against ARM
fronts. **Cross-architecture SEARCH equivalence is therefore not established by this artifact.** The
raw-search identity test shows only that two *x86* code paths agree with each other *on x86*; it is
an internal-consistency test, not a cross-architecture one.

Exposure is also larger than the headline: **834 rows carry `SIMPLIFY_TIMEOUT` across 237 of 530
worlds = 44.7%**, and the artifact states outright that the 1/530 figure *"measures what this audit
reached, not the divergence rate under full reclassification"*, because the lazy replay
short-circuits.

### 8.3 The answer: my endpoint does not require cross-architecture search equivalence

**E7 never compares an x86 front to an ARM front.** Every quantity is either

- a **within-surface** quantity (the four-way partition, the §2.6 conditional metrics, the recovery
  contrast, `false_structure_rate`) computed entirely from worlds generated on one host; or
- a comparison against a **v1 design descriptor** (Q1's registry/generator provenance; Q2–Q4's
  truth-blind consensus and signal geometry) — none of which is an ARM-produced floating-point
  output.

The **only** cross-architecture comparison anywhere in the protocol is **Gate V**, and Gate V
compares *aggregate class proportions* over 216 units against 144 units. Its sampling noise is
orders of magnitude larger than any plausible ULP-level cross-architecture drift, and its only power
is to **halt**. An architecture artefact cannot cause Gate V to license anything, because Gate V
cannot license anything.

Meanwhile the classification layer's host-dependence — the actual cause of
`NEW_CLOUD_HOST_PARITY_FAILED` — is removed **by construction**: under the determinacy bound, a row
is either resolved to its true frozen label or explicitly `UNRESOLVED`, and a case is classified only
when the class is invariant over every resolution of its unresolved rows. A faster or slower host
changes the **escalation cost**, never the **class**. The pathology cannot recur, on any
architecture, at any clock speed, under any thermal or load condition. The two worlds that still
timed out at a *patient 600 s* retry on x86 — where ARM's four all matched — are direct evidence
that some expressions are pathological on **any** host, and are precisely what the determinacy bound
exists for.

**Verdict: `ARCHITECTURE_REQUIREMENT = x86_64 ACCEPTABLE; ARM64 NOT REQUIRED`**, under three
binding conditions:

- **A1 — Single-host generation.** All 252 worlds generated on one x86 host, one environment, one
  hash-recorded dependency lock. **No merging of ARM and x86 worlds**, following the precedent
  `X86_E2A_SEAL.json` already sets (`corpus_is_x86_only: true`, `historical_worlds_merged: false`).
- **A2 — No wall-clock cap may assign a label.** Determinacy bound mandatory; `SIMPLIFY_TIMEOUT`
  retired as a classification.
- **A3 — Host determinism control before world 1.** Re-run the frozen search on a declared 10-case ×
  30-seed control subset **twice on this host** and require byte-identical fronts; plus §2.5
  control 1's retention-identity regression — the instrumented retained `argmax(score)` candidate
  must be **byte-identical** to the frozen path's, for every seed. *Instrumentation that changes the
  search is not instrumentation.*

**The honest caveat, stated so nobody can later read more into this than it says:** E7 is
*internally valid on x86* and *externally comparable to the Held-out design*. It does **not**
establish that an x86 search would have produced the Held-out fronts, and E7 makes no claim of that
form.

**Optional side-experiment I recommend but which cannot gate this protocol.** Re-run a stratified
12-case Held-out subset × 30 seeds on x86 and compare fronts against the macOS/ARM64 corpus. 360
searches, ≈0.9 CPU-hours. It would close the only genuinely open question the parity artifact leaves.
It is E2b-facing, so it files as **EXPLANATORY-ONLY** evidence and must be run *outside* E7's gate
chain and *after* Gate R is sealed.

---

## 9. Compute budget

### 9.1 Measured baseline (not estimated)

From `results/e2/run_x86_e2a_v1`, this host, 539 worlds × 30 seeds:

```
median wall per world     257.4 s      mean 262.5 s      p90 288.5 s      max 788.4 s
total                     39.3 CPU-hours
candidate rows            189,467      distinct expressions classified 52,450  (3.6x dedup)
lazy classify calls       65,090       (median 37/world)
witness paths             PHASE1_RETAINED_ONLY 221 · PHASE2_FRONT_SCAN_B 196 · PHASE2_FULL_SCAN_A 122
```

`befca0d` §2.10's 2.30 s/search figure gives the search component as ≈69 s/world; the remaining
≈193 s/world is classification.

### 9.2 E7 projection

| Item | Basis | Estimate |
|---|---|---|
| Search + persistence | 252 worlds × 30 seeds × 2.30 s | **4.8 CPU-h** |
| Exhaustive bounded scoring | ~97 distinct expressions/world after memoisation (52,450 / 539) vs lazy's 37; scaled from measured cost | **26–34 CPU-h** |
| Escalation | Gate 1 escalated 6 expressions at 5.5–21.8 s; declare a 1,500 s total budget | **< 0.5 CPU-h** |
| Counterfactual re-scoring, all R and V arms | zero search **and** zero extra classification (every row already labelled) | **~0 CPU-h** |
| Negative-control stratum | included in the 252 | — |
| Storage | ~7,560 seeds × ~15 rows ≈ 113,000 rows, full §2.4 schema | **< 300 MB** |

**Total: 30–40 CPU-hours. Declared ceiling: 48 CPU-hours. Wall clock ≈ 3–4 h on 10 workers.**

Exhaustive scoring is the cost, and it is worth paying: it is what makes **all of E4a and all of
E4f free** and what makes the corpus reusable without the lazy path's "reached-only" caveat. Under
the original plan those arms were separate experiments; here they are the routing measurement itself.

### 9.3 Mandatory hardening, derived from the measured E2a interruption

`INTERRUPTION_FORENSICS.json` classifies the E2a interruption as
`INFRASTRUCTURE_FAILURE__KERNEL_OOM_PLUS_SYSTEMD_SCOPE_TEARDOWN`:

1. **Per-worker RSS ceiling enforced in-process.** A single python reached
   `anon-rss: 33,477,720 kB` (≈32 GiB) on a 47 GiB host with **no swap**, triggering the global OOM
   killer. Reuse the `_memory_governor` pattern from the Gate 1 run.
2. **systemd scope isolation.** `DefaultOOMPolicy=stop` on the tmux scope turned one OOM kill into
   SIGTERM for **all 11 surviving shards and their supervisors**. Run shards in separate scopes, or
   set the policy explicitly. This single change converts a total-run loss into a one-world loss.
3. **Smoke-test the watchdog in preflight.** `scripts/e2_staleness_watchdog.sh` died 0 s after launch
   with `line 46: File: unbound variable` — the run was unwatched end to end. A watchdog that has
   never been observed to fire is not a watchdog.
4. **Cap concurrency at 10, not 12**, from a fresh `WORKER_COUNT_CALIBRATION` on this host, with
   headroom sized for the sympy tail rather than the median.
5. **World-level checkpointing with byte-exact resume** (already present; keep it, and test the
   resume path before the run rather than during it).

---

## 10. The three biggest threats to validity in my own design

### T1 — Design-matching is not behaviour-matching, and I cannot fully close this

Gate Q qualifies the surface on provenance (same generator, same condition grid, disjoint draw) plus
truth-blind descriptors. Nothing proves those are **sufficient**. The Held-out cases could differ
from a fresh `calibration` draw through some property of the generator that is not stationary across
replicate indices, or through an interaction between the condition grid and the search that only
manifests at particular draws. If the sufficient statistic for the loss mechanism is something I did
not measure, the surface can pass every gate and still be a different regime.

Gate V exists to catch exactly this, and **Gate V has modest power at 216 vs 144.** I will not
pretend otherwise. Mitigations: report the full Gate Q descriptor vector so a later analyst can test
additional descriptors against the *same* surface without regenerating it; scope every licence to
"the regime characterised by descriptor vector D" rather than to "Held-out" (§6.2 rider 2); and keep
the four-way partition as a first-class reported endpoint so the comparison stays available forever.

This is the residual risk of the entire approach and it does not go away. It is smaller than E2a's
version of the same risk by a large margin — E2a matched the target on *nothing* — but it is not
zero, and any synthesis document that claims it is zero is wrong.

### T2 — My design's most likely outcome is that it licenses nothing, and the council must accept that in advance

I did the following calculation on sealed evidence, and I am reporting it in full rather than acting
on it quietly. Reweighting E2a's sealed per-family `first_loss_stage` rates to the Held-out truth-family
composition (affine 0.75, saturating / interaction / exponential 0.0833 each, `mass_power` 0):

```
                       A/NOF     B/LIR    C+D/LICS   E/SUCCESS
E2a, raw               0.2263    0.3636    0.1892     0.2208
E2a, composition-      0.0941    0.4660    0.3935     0.0463
  reweighted
E2b, observed          0.0972    0.3819    0.4931     0.0278

total-variation distance to E2b:   raw 0.322   ->   reweighted 0.102
```

**Composition alone removes about two-thirds of the E2a/E2b divergence**, and `NEVER_ON_FRONT` moves
from 0.226 to 0.094 against E2b's 0.097 — an essentially exact match. What survives is a **near-tie**
between retention (0.466) and cross-seed (0.394), flipped in sign relative to E2b's (0.382, 0.493)
but with a gap of 0.07 in each — a difference n = 144 or 216 cannot resolve.

I therefore expect `LB(ΔR − ΔV)` to straddle zero and the honest verdict to be
**`ROUTING_INDETERMINATE`**. I am proposing this design anyway, because:

- an honest `INDETERMINATE` is a valid scientific and governance result, and F3 (§7) already says
  what it *means* — that the loss is jointly attributable and one-factor repair is not licensable;
- the alternative — a bare plurality on a near-tie — is **exactly the error that produced the v1
  attribution disaster**, where 124 of 144 cases were relabelled;
- if a determinate answer is required, the fix is **more n, not a weaker rule**: 432 worlds at
  ≈70 CPU-h. That preference is on the record before any result, so it cannot be reversed after one.

**The council should decide, before freezing, whether "probably licenses nothing" is acceptable.**
If the answer is no, the honest response is to raise n or to widen the arm grid — not to loosen the
margin.

### T3 — I read the sealed evidence before designing, and an adversary can fairly say one choice is downstream of it

I computed T2's reweighting, and E2a's per-family stage rates, and E2a's consensus geometry, before
writing this. That calculation is what convinced me the **population**, not the pipeline, explains
most of the E2a/E2b divergence — and it is what pushed me to make composition-and-condition matching
the centre of the design. It used E2a (admissible as synthetic diagnostic evidence under D5) and the
v1 taxonomy (admissible); it used E2b only for the final comparison line above, which I have
**disclosed rather than acted on**.

A fair adversary says: *"you chose to match composition because you saw that matching composition
moves E2a toward E2b."* My defences, in decreasing strength:

1. **The composition-and-condition match is entailed by the registry alone** (§2.2). A calibration
   surface containing 20% of a truth family that is absent from the target — and omitting the
   condition family whose declared purpose is *"canonicalize equivalent laws"* — is indefensible on
   its face, with or without E2b. The argument in §2.2 cites no outcome at all.
2. **No threshold anywhere is set from an observed value.** Q3's margin is self-calibrated from the
   Held-out corpus's own block jackknife (§5.2); Gate R's margin is the data's own sampling noise
   (§6.1). Neither has a free parameter I could move to change an answer.
3. **The projection is preregistered, not concealed** (T2), so it is a prediction the surface can
   falsify rather than a fishing expedition.
4. **I accept, and would welcome, a synthesis in which an independent agent — blind to T2's
   reweighting — re-derives the population rule from the registry and the v1 taxonomy alone.** If
   that agent reaches the same 12-condition calibration partition, the charge is answered by
   replication rather than by argument. **P2 should attack this specifically.**

### Further threats, recorded briefly rather than omitted

- **The `score` dependency.** If the production persistence path cannot emit `score`/`loss` for every
  front row, E4a arms R2 and R4 are unscoreable and the retention arm grid collapses to R1/R3 —
  which materially weakens ΔR and would bias routing toward voting. §4.1 makes this a hard preflight
  gate. It must not be waived.
- **The E6 dependency.** Every routing decision's safety half comes from E6's `false_structure_rate`
  ceiling, and **E6 is self-blocked pending exactly this hook.** If E6 cannot supply a ceiling at
  decision time, every licence is conditional and non-executable (§6.2 rider 1). The council should
  resolve the E6 circular dependency explicitly rather than let it surface at the end.
- **Registry amendment risk.** Appending a partition must not move any of the 380 existing
  `case_ordinal` values, or every Held-out search seed changes. §2.3 makes byte-equality of all 380
  pre- and post-amendment seeds a Q1 clause. If that check cannot be made to pass, fall back to the
  pre-declared `development ∪ challenge` population (84 cases) and accept the power loss and the
  contamination caveat.
- **`INDETERMINATE` worlds are a third state everywhere.** Every rate in this document has an
  explicit denominator convention that must be frozen with the protocol: `INDETERMINATE` worlds are
  reported separately and are never silently folded into "not recovered". P3 should fix the
  convention; P1's requirement is only that it be declared, and that the sensitivity of every routing
  comparison to both extreme resolutions be reported alongside the point estimate — exactly as the
  Gate 1 adjudication reported its 2⁴ enumeration.

---

## 11. Summary of what I am recommending

| Element | Recommendation |
|---|---|
| **Experiment** | `E7 — CALIBRATION PARTITION RE-ENTRY SURFACE` |
| **Surface** | New `calibration` partition of the benchmark's own registry, 18 replicates/family, appended last, new declared seed band |
| **Population** | 216 G2 worlds (12 conditions × 18) + 36 negative-control worlds (F07, F19) = **252 worlds × 30 seeds = 7,560 searches** |
| **Qualification** | Gate Q: design-provenance (Q1, load-bearing) + three truth-blind v1-sealed descriptor clauses (Q2–Q4), all equivalence tests, margins self-calibrated by block jackknife |
| **Circularity answer** | Provenance separation + functional non-identity + halt-only monotone channel + mechanical order enforcement + measured non-determination (`QND` on E2a) |
| **Routing statistic** | Paired counterfactual recovery contrast (ΔR, ΔV, C) on EVAL, simultaneous intervals, explicit `INDETERMINATE` |
| **Descriptive endpoint** | The frozen four-way partition, preserved verbatim and reported alongside |
| **E2b's role** | Gate V only: post-seal, one-way, output space `{STANDS, HALTED}` |
| **Scoring** | Bounded determinacy, exhaustive over rows; wall-clock cap retired as a classification rule |
| **Architecture** | x86_64 acceptable; ARM64 not required; conditions A1–A3 binding |
| **Budget** | 30–40 CPU-hours, 48 CPU-hour declared ceiling, ~3–4 h wall on 10 workers |
| **Most likely outcome** | `ROUTING_INDETERMINATE` — and the council should accept that before freezing |

**Terminal state for this document: proposal only. No world generated, no partition amended, no
search executed, no threshold frozen.**
