# MURU v2: G2 Pareto Instrumentation and Ablation Study Design

**Status:** DESIGN ONLY. Nothing here has been executed. The official v1 result
stands at G2 4/144 and is not reinterpreted by any experiment in this document.

**Covers:** E2 (`G2_PARETO_INSTRUMENTATION`) and E4
(`G2_SINGLE_FACTOR_ABLATIONS`, six one-factor arms E4a to E4f).

**Addresses:** RC3 (within-seed retention discards the accurate candidate, 69
cases), RC4 (search never reaches the descriptor structure, 57 cases), RC5
(family classifier coverage, 37 cases), RC7 (cross-seed identity finer than the
endpoint, 2 cases).

**The observability bound this study exists to remove.**
`WITHIN_SEED_PARETO_NOT_OBSERVABLE`: `rc5_selection` section 7.1 retains exactly
one candidate per seed, `argmax(score)` of that seed's PySR Pareto front, and
only that row is persisted. Every v1 statement of the form "the correct
expression was never generated" means only "never reached cross-seed selection".
E2 is the instrument that turns that inference into an observation.

---

## 1. The question E2 must answer

The decomposition partitions 144 G2 cases into a first irreversible failure
point, but two of those classes rest on an inference the sealed evidence cannot
support:

| First failure point | Cases | What is actually known |
|---|---|---|
| `REPRESENTATION` | 12 | Certain. F18 needs `exp`; the grammar excludes it. |
| `GENERATION` / `GENERATION_FAMILY` | 57 | Only that no *retained* candidate was correct. The front is unobserved. |
| `SELECTION_WITHIN_SEED_RETENTION` | 69 | Inferred from paired within-case behaviour: correct-retaining seeds carry +0.121 median `valid_r2` at +3.4 median complexity. The discarded candidates were never seen. |
| `SELECTION_CROSS_SEED_IDENTITY` | 2 | Certain. |
| `NONE` | 4 | Certain. |

E2 replaces the inference in rows 2 and 3 with a direct measurement, and it does
so by changing nothing except what is written to disk.

---

## 2. E2: full per-seed Pareto front persistence

### 2.1 Hypotheses

| ID | Statement |
|---|---|
| **H_retain** (RC3) | In the majority of the cases the decomposition classed `SELECTION_WITHIN_SEED_RETENTION`, a G2-correct row is present on the seed's front and `argmax(score)` selects a lower-complexity mass-only row over it. |
| **H_generate** (RC4) | In the majority of the cases classed `GENERATION`, no row anywhere on the front carries both the correct support and the correct family, in the majority of seeds. |
| **H_partial** | A material share of the `GENERATION` cases in fact have correct rows on the front that never survived retention, meaning the decomposition's 57/69 split understates retention and overstates generation failure. |

H_partial is the outcome that would revise the decomposition's own attribution.
It is stated first-class so it cannot be discovered and then quietly absorbed.

### 2.2 Independent variable

**None. E2 is observational by design.**

The engine, the grammar, the search configuration, the seed derivation, the
retention rule and the cross-seed rule are all held at their frozen v1 values.
The only change is the persistence layer. Stating this plainly matters: E2 is not
an ablation and must not be read as one. It establishes the missing observable so
that E4's ablations have something to be ablations *of*.

### 2.3 Two populations, two roles, one of them decision-inadmissible

**E2a, fresh worlds, calibration role.** Fresh `V2C` worlds spanning the five
truth families at controlled coefficient regimes and noise levels. **v2 design
decisions may be based on E2a.**

**E2b, Held-out replay, explanatory role only.** The identical frozen search
re-run on the 144 Held-out G2 cases with front persistence enabled. This explains
the sealed v1 result, which is scientifically valuable and is the only way to
check the decomposition's attribution against direct observation.

**E2b outputs are `DECISION_INADMISSIBLE`.** No v2 threshold, retention rule,
grammar change, classifier change or benchmark change may be justified by E2b.
E2b may only corroborate or contradict a conclusion already reached on E2a.

This is enforced mechanically, not by convention:

- every E2b record carries `admissibility = "DECISION_INADMISSIBLE"` at the row
  level;
- every proposed v2 design change must cite the experiment IDs supporting it;
- a static citation checker rejects any change whose supporting set contains an
  E2b identifier and no E2a identifier.

Re-running a search on Held-out does not re-score the endpoint and does not
reinterpret the v1 result. The v1 result stands at 4/144 regardless of what the
fronts contain.

**If E2a and E2b disagree**, that is itself a finding and it blocks adoption of
any E4 conclusion until explained. Divergence would mean the fresh worlds do not
reproduce the Held-out regime, which invalidates E2a as a calibration surface.

### 2.4 The front record

Persisted for every (world, seed, front row), before retention is applied:

```
world_id, cell_id, replicate, split, seed_ordinal_k, seed,
front_rank, engine_complexity, grammar_complexity,
expression_string, parse_ok,
train_r2, valid_r2, test_r2, loss, score, invalid_fraction,
effective_support, template_key,
retained_by_argmax_score,
admissibility
```

Joined in a **separate scoring pass the search never sees**:

```
discovered_family, support_status_vs_truth, family_status_vs_truth,
g2_correct, truth_family, truth_support, coefficient_regime
```

The truth-derived columns are computed downstream of the search by a distinct
process. This preserves the truth-blind boundary that `rc3_acceptance` and
`g2_contract` maintain by design: acceptance never reads truth, only post-hoc
scoring does.

### 2.5 Controls

1. **Retention-identity regression.** The instrumented engine is run alongside
   the frozen persistence on a control world set, and the retained
   `argmax(score)` candidate must be **byte-identical** to the frozen path's, for
   every seed. Instrumentation that changes the search is not instrumentation.
   This is a hard gate before any E2 record is used.
2. **Frozen configuration.** `PYSR_CONFIG` unchanged, `GRAMMAR_VERSION`
   unchanged, `SEEDS_PER_CASE = 30` unchanged, `deterministic=True` and
   `parallelism="serial"` unchanged, so reruns reproduce.
3. **Replay fidelity for E2b.** E2b's seeds are the v1 seeds. Its retained
   candidates must reproduce the sealed `selection_count` and cross-seed
   representative for all 144 cases, replaying `group_and_select` exactly as the
   decomposition did. Any case that fails to reproduce is quarantined and
   reported, not silently dropped.

### 2.6 Metrics

Three conditional stages, measured per family and per coefficient regime:

| Metric | Definition |
|---|---|
| `P_front` | fraction of seeds whose front contains at least one G2-correct row |
| `P_retain_given_front` | among correct-containing seeds, fraction where `argmax(score)` retains a correct row |
| `P_win_given_retain` | among cases with at least one correct retained candidate, fraction where cross-seed selection returns a correct representative |
| `rank_of_correct` | front rank of the highest-scoring correct row |
| `score_gap` | `score` of the argmax row minus `score` of the best correct row |
| `complexity_gap` | complexity of the best correct row minus complexity of the argmax row |
| `r2_gap` | `valid_r2` of the best correct row minus `valid_r2` of the argmax row |
| `front_size` | rows per front |

The v1 diagnosis measured `r2_gap` and `complexity_gap` *across seeds* at +0.121
and +3.4. E2 measures them **within a front**, which is the comparison that
actually indicts the retention rule.

### 2.7 The three-way attribution

Every case is assigned exactly one label, forming a partition:

| Label | Condition |
|---|---|
| `SUCCESS` | cross-seed selection returns a G2-correct representative |
| `NEVER_ON_FRONT` | 0 of 30 seeds' fronts contain any correct row |
| `LOST_IN_RETENTION` | at least one front contains a correct row, but too few are retained for a correct class to win |
| `LOST_IN_CROSS_SEED` | correct rows are retained by at least one seed but the winning class is incorrect |

This is the (a) / (b) / (c) answer the mission requires, and it is a measurement
rather than an inference.

### 2.8 Case count and seeds

**E2a.** 5 truth families (`mass_affine_descriptor`, `mass_power`,
`mass_saturating_descriptor`, `mass_interaction`, `mass_exponential_descriptor`)
x 3 coefficient regimes x 3 noise levels x 12 replicates = **540 worlds** x 30
seeds = **16,200 searches**.

Twelve replicates per cell matches the v1 per-family case count of 12, so E2a's
per-family precision is comparable to the evidence it is meant to explain.

**E2b.** 144 Held-out G2 cases x 30 seeds = **4,320 searches**.

### 2.9 Decision criterion

Pre-declared, applied to the E2a attribution:

| Observation | Conclusion | Licences |
|---|---|---|
| `LOST_IN_RETENTION` is the largest non-success class | RC3 confirmed by direct observation | E4a (retention policy) |
| `NEVER_ON_FRONT` is the largest non-success class | RC4 confirmed | E3 must first establish whether those cells are identifiable at all; only then E4b/E4c/E4d |
| `LOST_IN_CROSS_SEED` is the largest | RC7 is larger than the 2 cases v1 showed | E4f (canonicalization / voting relation) |
| `P_retain_given_front` is near 1 wherever `P_front` is high | the retention rule is exonerated | RC3 is withdrawn; no retention change licensed |

**Falsification hook.** The decomposition predicts, on Held-out, roughly 69
retention-class and 57 generation-class cases. If E2b's direct measurement
contradicts that split materially, the decomposition's attribution is wrong and
**every E4 ablation is suspended** until the contradiction is resolved. This is
the strongest single check in the plan, because it tests the diagnosis that the
whole remediation rests on.

### 2.10 Cost

| Item | Basis | Estimate |
|---|---|---|
| E2a search | 16,200 runs x 2.30 s (RUNTIME_BUDGET_P3 measured, serial) | 10.4 CPU-hours |
| E2b search | 4,320 runs x 2.30 s | 2.8 CPU-hours |
| Post-hoc scoring | one `sympy.simplify` per distinct expression string; `classify_discovered_family` and `extract_effective_support` both call it | 3 to 5 CPU-hours |
| Storage | ~20,500 seeds x ~15 front rows ≈ 310,000 rows | under 200 MB |

**Total: 16 to 19 CPU-hours.**

The scoring pass, not the search, is the cost risk. `simplify` is unbounded in
the worst case. Mitigations, all declared in advance: memoise by expression
string (fronts repeat heavily across seeds), apply a per-expression wall-clock
cap with the timeout recorded as an explicit `SIMPLIFY_TIMEOUT` status rather
than silently becoming `None`, and run scoring as a separate restartable stage.
The `SIMPLIFY_TIMEOUT` status matters: v1's 34.2 percent `None` rate is currently
indistinguishable between "classifier does not cover this form" and "simplify
gave up", and E4f cannot be interpreted until those are separated.

### 2.11 What each outcome supports

- **H_retain confirmed.** RC3 becomes an observation. E4a's retention arms are a
  re-scoring of E2's own fronts, so the remediation is measured at zero
  additional search cost, and the accuracy-versus-parsimony trade is quantified
  within the front rather than across seeds.
- **H_generate confirmed.** The failure is upstream of every selection layer, and
  the next question is E3's: is the structure findable at all? No search-side
  change is licensed until E3 answers, because increasing budget or grammar
  richness against an unidentifiable target buys only false structure.
- **H_partial confirmed.** The decomposition's 57/69 split is revised. The
  revision is published as a correction to the attribution, and the root-cause
  ranking's ordering of RC3 and RC4 is recomputed before E4 proceeds.

---

## 3. E4: single-factor ablations

**Discipline.** One factor at a time. No arm changes two factors. Any joint or
interaction study is a separately authorised later stage that may combine only
factors already shown individually admissible, and it must re-measure false
structure jointly, because admissibility is not additive.

**Common controls for every arm.** Frozen v1 setting is always the control arm.
Identical worlds, identical seeds, identical downstream stages. Every arm reports
its G2 metric **and** its false-structure metric from E6 in the same table.
Reporting a G2 gain without its safety cost is not permitted.

**Common failure metric.** For every arm, `false_structure_rate` is the fraction
of mass-only-truth and null worlds on which the pipeline structurally accepts a
non-mass effective support. Its pre-declared ceiling is set in E6.

### 3.1 E4a: retention policy

*Post-hoc on E2's persisted fronts. Zero additional search.*

| Arm | Rule | Free parameters |
|---|---|---|
| R0 | `argmax(score)` | 0 (control, frozen v1) |
| R1 | `argmax(valid_r2)` | 0 |
| R2 | top-`k` by `score`, `k` in {1, 2, 3, 5} | 1 |
| R3 | whole front, seed votes for its best member by `valid_r2` | 0 |
| R4 | accuracy-thresholded parsimony: among rows with `valid_r2 >= max(valid_r2) - eps`, take the lowest complexity; `eps` in {0.001, 0.005, 0.02} | 1 |

R4 targets the observed signature directly. The v1 evidence is that correct
candidates carry +0.121 `valid_r2` at +3.4 complexity, which is a parsimony rule
buying complexity at the price of accuracy far above any sensible exchange rate.
R4 caps that exchange rate explicitly.

**Metrics:** G2 case success; `false_structure_rate`; and `selection_count`
distribution, because retaining more than one candidate per seed changes what the
20-of-30 stability gate means. RC3's own risk note is explicit that multi-retention
weakens the stability gate and inflates the effective multiple-comparison count;
the `selection_count` distribution is how that inflation is measured rather than
assumed away.

**Decision:** adopt the simplest rule whose G2 improvement over R0 has a Wilson
lower bound above 0 **and** whose `false_structure_rate` stays under the E6
ceiling. If several qualify, fewest free parameters wins, then lowest false
structure.

**Cost:** zero search, minutes of re-scoring.

### 3.2 E4b: search budget

| Arm | `niterations` | Other |
|---|---|---|
| B0 | 40 | frozen control |
| B1 | 120 | populations, population_size unchanged |
| B2 | 400 | populations, population_size unchanged |

**Population.** Restricted to the cells E2 labels `NEVER_ON_FRONT` **and** E3
labels identifiable. Running B2 on cells that are unidentifiable wastes the
budget on a target that no budget can reach; running it on cells already found
answers nothing. This is why E4b is scheduled after E2 and E3.

**Metric:** `P_front`, not case success. Budget is a generation-stage factor and
must be measured at the generation stage.

**Decision:** if `P_front` is flat across B0 to B2, generation failure is not a
budget problem and no budget increase is licensed. If `P_front` rises materially
at B1, adopt the smallest sufficient budget. A rise only at B2 is reported with
its 10x cost so the trade is explicit.

**Cost:** 60 worlds x 30 seeds x (2.3 + 6.9 + 23.0) s ≈ **16 CPU-hours**,
dominated by B2.

### 3.3 E4c: search objective and parsimony

Two sweeps, each one-factor:

| Sweep | Factor | Levels |
|---|---|---|
| C-i | `parsimony` | 0.0032 (control), 0.001, 0.01 |
| C-ii | `adaptive_parsimony_scaling` | 20.0 (control), 5.0, 40.0 |

**Metrics:** `P_front`; `P_retain_given_front`; front complexity distribution;
`false_structure_rate`.

**Decision:** a parsimony change is licensed only if it raises `P_front` (a
generation effect) rather than only `P_retain_given_front` (which E4a already
addresses more directly and at zero cost). Lowering parsimony to make the search
emit more complex expressions and then declaring victory on retention is
double-counting the same fix.

**Cost:** 60 worlds x 30 seeds x 2.3 s x 4 non-control arms ≈ **4.6 CPU-hours**.

### 3.4 E4d: grammar and operator availability

| Arm | Grammar |
|---|---|
| G0 | frozen: `sqrt, log, square, cube, inv` (control) |
| G1 | + unguarded `exp` |
| G2 | + domain-clipped `exp_p(x) = exp(clip(x, -B, B))`, `B` declared, with `NESTED_CONSTRAINTS["exp"] = {"exp": 0}` |
| G3 | + `exp` admissible only over a linear argument in one primitive |

**Metrics:** F18-analogue `P_front`; **and** for every other family, G2 success
and `false_structure_rate`, because a richer grammar is a global change scored on
a single family's benefit. Plus overflow instrumentation: rate of `finite_mask`
rejection, rate of `MAX_INVALID_FRACTION` (0.005) rejection, and a direct check
that an invalid candidate never outscores a valid one.

**Decision:** adding an operator is licensed only if F18-analogue `P_front` rises
materially **and** no other family's `false_structure_rate` rises above the E6
ceiling. G3 is presumptively rejected: constraining `exp` to exactly the planted
argument form encodes the answer in the grammar. It is measured so the size of
that encoding effect is on the record, not so it can be adopted.

**Ordering constraint:** E4d may not be interpreted before E3 reports whether the
exponential family is separable from its affine neighbour at the planted
coefficient magnitude. See `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` section 5
and E5 below.

**Cost:** 200 worlds x 30 seeds x 2.3 s x 3 non-control arms ≈ **11.5
CPU-hours**.

### 3.5 E4e: coefficient and effect-size regime

The coefficient ladder from E3, now measured through the real search rather than
an oracle: `c` in {0.25, 0.40, 0.55, 1.1, 2.2}, spanning and extending the frozen
`rng.uniform(0.25, 0.55)`.

**Metric:** G2 success as a function of `c`, per family. Define `c*_search` as the
smallest `c` at which G2 success reaches 0.80.

**The headline quantity of the whole G2 programme:**

```
engine_inefficiency = c*_search  -  c*_oracle
```

where `c*_oracle` comes from E3, which hands a model-selection criterion the five
correct parametric candidates in closed form. The gap is how much stronger the
planted signal must be for a symbolic search than for a selector that already
knows the answer set. It separates benchmark difficulty from engine capability,
which is the distinction v1 could not make and which RC4 names as unresolvable
from the seal.

**Decision:** a large gap licenses search-side work (E4b/c/d). A gap near zero
means the search is already near the statistical limit and further search
engineering is wasted; the constraint is then the benchmark's signal-to-noise,
which is a benchmark-design question governed by the difficulty guard in
`MURU_V2_A1_STUDY_DESIGN.md` section 3.11.

**Cost:** 5 families x 5 coefficients x 20 worlds x 30 seeds x 2.3 s ≈ **9.6
CPU-hours**.

### 3.6 E4f: family classifier and canonicalization

*Post-hoc on E2's persisted fronts. Zero additional search.*

Two independent sweeps.

**F-i, discovered-family classifier:**

| Arm | Classifier |
|---|---|
| K0 | frozen `classify_discovered_family` (control) |
| K1 | K0 plus a canonical structural normal form before pattern matching |
| K2 | behavioural identification: fit each of the five truth-family parametric forms to the **candidate's own predicted values** and label by best fit |

K2 is truth-blind in the sense that matters: it consumes only the candidate's
outputs on the design matrix, never the planted law. It is the arm most likely to
close the 34.2 percent unlabelled rate, and it is also the arm with the highest
false-labelling risk, which is why the metric below is ordered as it is.

**F-ii, cross-seed voting relation:**

| Arm | Grouping key |
|---|---|
| V0 | `identity_contract.template_key` (control) |
| V1 | `(effective_support, discovered_family)`, the pair the endpoint is scored on |
| V2 | algebraic equivalence under `discovery.equivalence` |

**Metrics, in priority order:**

1. **`false_labelling_rate`** (primary): fraction of adversarial negative
   controls that receive the truth family. Negative controls are constructed by
   structurally perturbing the truth expression: substitute `correlated_distractor`
   for `descriptor`, substitute `descriptor2` for `descriptor`, and replace the
   descriptor factor with a constant of matched magnitude. These are known
   not-truth-equivalent by construction.
2. `coverage`: 1 minus the `None` rate, with `SIMPLIFY_TIMEOUT` reported
   separately from genuine non-coverage.
3. `k_inflation`: change in median class count per case and in
   `selection_count`, since merging is the direction the identity contract was
   deliberately written to avoid.
4. G2 case success.

**Decision:** coverage is *not* the adoption criterion. RC5's risk note is
explicit that a more permissive classifier converts `UNEVALUABLE` into false
`SUCCESS`, which is the direction that flatters the result. A classifier arm is
adopted only if `false_labelling_rate` stays below its pre-declared ceiling; among
those, the highest coverage wins. A voting arm is adopted only if `k_inflation`
stays within its ceiling; v1's own counterfactual showed V1 recovers 2 cases and
loses 3, for a net loss, so V1 carries a specific prior against it.

**Cost:** zero search; 2 CPU-hours of scoring, dominated by K2's per-candidate
parametric fits.

---

## 4. Ablation summary

| Arm | Factor | Search cost | Licensed by |
|---|---|---|---|
| E4a | retention policy | 0 | E2 shows `LOST_IN_RETENTION` dominant |
| E4b | search budget | 16 CPU-h | E2 shows `NEVER_ON_FRONT` **and** E3 shows identifiable |
| E4c | objective / parsimony | 4.6 CPU-h | same as E4b |
| E4d | grammar / operators | 11.5 CPU-h | E3 resolves the exponential separability question first |
| E4e | coefficient regime | 9.6 CPU-h | always; produces `c*_search` |
| E4f | classifier / canonicalization | 0 | E2 provides the fronts |

**E4 total: about 42 CPU-hours of search**, plus E2's 16 to 19. Every arm is
restartable and checkpointed at the world level.

---

## 5. Pre-registered predictions

| ID | Prediction |
|---|---|
| PE2-1 | `P_front` for `mass_affine_descriptor` at the frozen coefficient range exceeds 0.5, and `P_retain_given_front` is below 0.5, confirming H_retain for that family. |
| PE2-2 | `P_front` for `mass_saturating_descriptor` (F09 analogue) is below 0.1 even with the whole front observed, so F09's 0/12 oracle was a generation or identifiability failure, not a retention failure. |
| PE2-3 | Within-front `r2_gap` and `complexity_gap` reproduce the sign and rough magnitude of the v1 cross-seed values (+0.121, +3.4). |
| PE2-4 | E2b reproduces the decomposition's retention-versus-generation split to within 10 cases of 69/57. |
| PE4a-1 | R4 with `eps = 0.005` raises G2 success over R0 without raising `false_structure_rate`, and R3 (whole front) raises both. |
| PE4d-1 | Adding `exp` does not materially raise F18-analogue `P_front`, because the planted exponential is numerically indistinguishable from an affine descriptor law at the planted coefficient. See the identifiability design, section 2.2. |
| PE4e-1 | `engine_inefficiency` is positive and largest for `mass_saturating_descriptor` and `mass_interaction`. |

PE4d-1 is the prediction that, if it holds, makes E5's grammar question moot. It
is stated here and tested in E3 before E4d is interpreted.

---

**Terminal state for this document:** design only. No search executed, no front
persisted, no ablation run.
