# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF `E7 — CALIBRATION PARTITION RE-ENTRY SURFACE`

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` (frozen, not executed)
**Supporting:** `SYNTHESIS_DECISION_RECORD.md`, `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md`, `design_council/P{1,2,3}*.md`
**Role:** hostile scientific adversary. Falsify the design before it runs.
**Discharges:** §30 mandatory attack surface items 1–6 (item 4 is discharged with a proof, see D2).

---

# VERDICT

```
CRITIC_SCIENCE = FAIL
```

The protocol is not defective because it is careless. It is defective because **its
positive outcome space is empty for every possible dataset**, and that emptiness is
derivable at zero compute from three numbers already frozen inside the document. A
45,360-search, ~260 CPU-hour experiment whose every branch terminates without a licence
regardless of the data is not a conservative test; it is an unfalsifiable one. The
pre-recorded expectation in §34 ("I expect this protocol NOT to reach E4 re-entry on any
branch, and I am proposing it anyway") is presented as scientific humility. It is in fact a
theorem of the design that the author did not derive, did not disclose, and recorded as a
30% probability rather than a certainty.

Two further defects (D2, D3) are independently blocking. Neither the author's predicted
`ROUTING_INDETERMINATE` nor any other terminal is reached honestly under the text as
written.

---

# DEFECTS, RANKED

## D1 — CRITICAL, DISPOSITIVE. Gate R's licensing routes and Gate V's veto are arithmetically incompatible. `E4A_LICENSED` is unreachable for every possible dataset.

### What is wrong

`§32:1094` makes `E4A_LICENSED_AT_<arm>` — the only full re-entry terminal — require
**both** `ROUTING_CERTIFIED → B` **and** Gate V `STANDS`. `§21.3:770-771` defines Gate V as
`TV(pi_hat, pi_0) <= delta` against the sealed Held-out attribution
`pi_0 = (A,B,C+D,E) = (14,55,71,4)/144 = (0.0972, 0.3819, 0.4931, 0.0278)`, with
`delta = 10/144 = 0.069444`.

`pi_0` puts `C+D` **ahead of** `B` by `71-55 = 16/144 = 0.11111`. Route B requires the
surface to put `B` **ahead of** `C+D`, and `§21.1:721-724` requires that lead to be
certified: `LCB_95(pi_top - pi_second) > 0`.

For any surface with `pi_B - pi_C+D = m > 0`:

```
TV(pi_hat, pi_0) >= 0.5 * | (pi_B - pi_B0) - (pi_CD - pi_CD0) |
                 =  0.5 * | (pi_B - pi_CD) + 0.11111 |
                 =  0.5 * ( m + 0.11111 )
```

Gate V therefore admits route B **only if** `m <= 2*delta - 0.11111 = 0.02778`.

But `§10:376-382` sized `n = 1296` precisely so that the **smallest certifiable** lead is
`delta = 0.0694` (recomputed from the protocol's own formula: `0.06890`, see D11). The
minimum lead the certification predicate can pass at `n = 1296` with
`pi_B + pi_C+D ~ 0.875` is `m_min = z_.95 * sqrt(s/(n + z_.95^2)) = 0.0427`.

```
0.0427  >  0.02778     =>   TV_min = 0.5*(0.0427 + 0.11111) = 0.0769  >  0.069444
```

**The design is powered to certify exactly the leads Gate V will veto, and is unpowered
for the only leads Gate V would accept. The two admissible regions are disjoint.**

### Verified numerically

Constrained minimisation of `TV(pi, pi_0)` over the full simplex subject to each route's
certification predicate (`z_.95`, `n = 1296`, 400 SLSQP restarts):

| Certified route | min attainable `TV` over ALL data | Gate V |
|---|---:|---|
| `A` → row 4, partial generation licence | **0.25158** | HALTS always — **UNREACHABLE** |
| `B` → row 3 → **E4a re-entry** | **0.07690** | HALTS always — **UNREACHABLE** |
| `C+D` → row 5 | **0.00000** | STANDS — reachable |

Monte-Carlo confirmation (200,000 multinomial draws, `n = 1296`):

- surface regime **identical** to Held-out: `P(certify → B) = 0.0000`
- surface with `B` leading by exactly `delta`: `P(certify → B) = 0.7547`,
  `P(Gate V STANDS) = 0.0102`, **`P(both) = 0.0000`**

### The complete reachable terminal set of this protocol

```
T-INSTRUMENT-UNBOUNDED | CIRCULAR_BY_MEASUREMENT | NO_ADMISSIBLE_SURFACE_EXISTS |
SURFACE_NOT_QUALIFIED  | VOID | ROUTING_INDETERMINATE | RC3_WITHDRAWN |
ROUTE_DETERMINED_ARM_NOT_EXECUTABLE | HALTED | T1
```

Every one of them is a non-licensing terminal. The **only** route that survives Gate V
(`C+D`) is the one `§21.2:748` **pre-labels non-executable**. `E4A_LICENSED_AT_<arm>`
(`§32:1094`) and `E4_GENERATION_LICENSED_<cells>` (`§32:1095`) are dead rows.

### Does it change the protocol's conclusions?

It changes what the protocol **is**. `§1:104-108` states the purpose as making
`EXPERIMENTAL_REENTRY_RESOLUTION` *evaluable on evidence admissible for licensing*. No
possible execution of this instrument can produce such evidence. D3 item 8 can never be
satisfied by this design. `§34:1168` is therefore not a risky prediction but a restatement
of the design's arithmetic, and `§34:1174-1178`'s "disclosure that makes this claim
checkable" checks the wrong thing: it establishes that a re-entry-delivering design was
rejected, not that the retained design can deliver anything at all.

### Minimal fix (choose one; the first is correct)

1. **Apply `delta` to the statistic it was frozen on.** `PE2-4`'s "more than 10 cases" is a
   **per-class** deviation (`GATE_1_DEFINITIVE`: `DIRECT_RETENTION 55 vs 69 -> dev 14`;
   `DIRECT_GENERATION 14 vs 57 -> dev 43`). `§21.3` re-uses the number against
   **total variation over a 4-cell partition**, a statistic that aggregates four deviations
   and is therefore roughly twice as strict. Restating Gate V as
   `max_k |pi_k - pi_0k| <= delta` restores the frozen semantics and makes route B
   reachable in the limit. This is exactly the threshold-transfer error `P2 BC-16` warns
   about, committed by the section that cites BC-16.
2. If TV is retained, `n` must satisfy `m_min <= 2*delta - 0.11111`, i.e.
   **`n >= 3,066`** (and `n >= 3,894` once D4 is fixed) — 2.4x to 3x the declared surface.
   State this, or state that route B is unreachable.
3. Failing both: pre-label rows 3 and 4 non-executable alongside row 5, as `§21.2:750-757`
   already does for row 5, and stop describing the protocol as a re-entry qualification.

---

## D2 — CRITICAL. `QND_PASS`, the design's flagship non-circularity property, is provably unsatisfiable. Under a literal reading the protocol forbids its own execution. (Discharges §30 attack item 4.)

### What is wrong

`§4:217` / `§18:620` define `QND_PASS` as: *enumerate stratified subpopulations of E2a's
sealed corpus that would pass Gate Q's measurable clauses, and verify the routing verdict is
not constant across them.* `§18:700` makes it a conjunct of `QUALIFIED`; `§22:814` makes
failure terminal `CIRCULAR_BY_MEASUREMENT`, **"Do not execute"**.

Gate Q's Q1 (`§18:614`) requires, among other clauses:

- *the registry's twelve G2 conditions at equal weight `w_k = 1/12`*
- *every cell carrying exactly 108 completed worlds*
- *partition disjoint from `held_out` and `challenge`*

Verified directly against `results/e2/run_x86_e2a_v1/WORLD_ORDER_539_MAIN.json`:

```
E2a = 539 worlds, 45 cells (5 families x 3 coefficient regimes x 3 noise levels),
      12 replicates per cell (one cell has 11)
families: mass_affine_descriptor, mass_exponential_descriptor, mass_interaction,
          mass_power, mass_saturating_descriptor
```

E2a's axes are `(family, regime, noise)`. They are **not** registry F-codes. The protocol
states this itself at `§3:160-169`: *"E2a instantiated **none** of the twelve prospectively
declared Held-out G2 conditions."* Additionally E2a's largest cell holds 12 worlds against
Q1's required 108, and the entire corpus (539) is smaller than one qualifying cell set
(12 x 108 = 1,296). E2a carries no `partition` field at all.

**The set of E2a subpopulations passing Q1's measurable clauses is empty, provably and by
the protocol's own §3.** There is nothing to enumerate.

### Consequence

- Implemented literally — "verify the verdict is **not constant**", which requires two
  distinct verdicts to be exhibited — `QND_PASS = FALSE` over an empty family.
  `§22:814` then fires `CIRCULAR_BY_MEASUREMENT` **before Stage 1 executes**. The protocol
  forbids its own execution.
- Implemented as "no counterexample of constancy was found", it passes **vacuously** and
  tests nothing. The design's only *measured* (as opposed to argued) non-circularity
  property is then decorative.

The protocol does not say which reading governs. Both are fatal in different ways.

### Minimal fix

Delete the E2a-keyed formulation. The property worth testing is real but must be tested on
**simulated** surfaces drawn from the registry generator: pre-declare a family of synthetic
condition-mix perturbations that satisfy Q1 by construction, and require the routing verdict
to vary across them. That is enumerable, it is truth-blind, and it actually measures whether
qualification determines routing. Alternatively remove `QND_PASS` from `QUALIFIED` and stop
claiming property (v).

---

## D3 — CRITICAL. Gate V treats a 144-case draw as a constant with zero sampling error. Comparator noise alone consumes 69% of the tolerance and produces a 21% false HALT against a perfectly matched surface.

### What is wrong

`§21.3:763-773` compares `pi_hat` (n = 1,296) against `pi_0` (n = **144**) at
`TV <= delta`, with no interval on `pi_0`.

`SYNTHESIS_DECISION_RECORD.md §1.5` establishes — and I reproduce — that the sealed 144-case
comparator's own sampling variance makes a two-sample equivalence test on `S_2`
**infeasible at any n**, and that P3's escape is to treat `S^0` as a constant, a framing
*"P3 itself labels anti-conservative"*. `§2` of the same record rules that escape
inadmissible for qualification. Gate V then performs exactly that inadmissible operation,
one section later, as a necessary condition for every licence.

### Quantified (200,000 draws)

Surface drawn from the **identical** regime as Held-out; comparator is one 144-case
realisation of that regime:

```
mean TV from comparator sampling noise alone (surface n -> infinity) = 0.0478
                                        = 69% of the entire 0.069444 tolerance
P(TV > delta | surface regime IDENTICAL to Held-out)                  = 0.2099
```

**A surface that reproduces the Held-out regime exactly HALTs 21.0% of the time.** The
false-HALT rate is not incidental: it is the dominant term.

Compounding this, `§34:1161`'s own predicted Stage-1 point
(`pi_A ~ 0.12, pi_B ~ pi_C+D ~ 0.43, pi_E ~ 0.02`) gives `TV = 0.0708 > 0.069444` — the
protocol's own central prediction trips its own veto **at the point estimate**, before any
noise.

### Does it change the conclusions?

Yes. `§21.3:794` argues *"a false HALT is conservative"*. A false HALT is a **VOID**
(`§22:818`) with no rehabilitation path (`§22:822`), escalated to the protocol owner as a
substantive divergence finding, and `§13:489-496` concedes a trip is **not attributable**
between "the surface does not reproduce Held-out" and "x86 search differs from ARM search".
A 21% probability of manufacturing an uninterpretable, non-rehabilitable, escalation-forcing
terminal out of comparator sampling noise is not conservatism. It is a defect that
terminates the programme on a coin-weighted flip.

### Minimal fix

Either (a) put a 95% simultaneous interval on `pi_0` and trip only when the TV lower bound
exceeds `delta` — which, per `§1.5`, will show the veto has almost no power and should then
be reported as such; or (b) drop the veto and state plainly that no Held-out comparison is
performed, which is what `§4:195-207` already claims. Retaining a point-estimate veto on a
144-case comparator is the worst of the three options.

---

## D4 — MAJOR. The routing certification's stated alpha is wrong by a factor of two under the protocol's own predicted configuration. `§27`'s "theorem" is false.

### What is wrong

`§27:965` asserts *"Routing certification: **one comparison** (`pi_top` vs `pi_second`)...
One endpoint, one alpha, one decision"*, and `§27:959-964` calls the absence of adjustment
*"a theorem rather than a convention"*.

It is not one comparison. `pi_top` and `pi_second` are **selected by the data**
(`§21.1:721`). Applying a one-sided `z_.95` bound to a data-selected contrast between two
cells is a two-sided comparison read one-sided. Fixed-sequence gatekeeping controls the
qualification→routing ordering; it does nothing about selection *within* the routing step.

### Quantified (200,000 draws, n = 1,296)

| True configuration | `P(ROUTING_CERTIFIED)` | nominal |
|---|---:|---:|
| exact 3-way tie A=B=C+D | 0.0344 – 0.0362 | 0.05 |
| **2-way tie B = C+D at 0.43, `pi_A = 0.12`** (= `§34:1161`'s prediction) | **0.1005** | 0.05 |

Under a 3-way tie the rule is conservative — credit where due. But `§34:1161` predicts
`pi_A < 0.15` and `pi_B ~ pi_C+D`, i.e. **the two-way-tie configuration**, where the
type-I error is **10.0%, exactly double nominal**. Conditional on a false certification,
roughly half point at `B`, i.e. at E4a.

### Does it change the conclusions?

It changes the honesty of the only branch the protocol expects to be live. Under D1 the
false certification cannot become a licence (Gate V halts it), so the practical effect
today is to convert `ROUTING_INDETERMINATE` into `HALTED` at twice the advertised rate. If
D1 is fixed, this becomes a direct alpha inflation on the licensing path.

### Minimal fix

Use `z_.975` on the selected contrast (verified: restores `P = 0.0508` at the 2-way tie,
`P = 0.7707` at a true lead of `delta`). Then `§10`'s derivation must be re-run:

```
n >= (1 - delta^2)(z_.975 + z_.80)^2 / delta^2 = 1,619.7   ->   n = 1,632 = 12 x 136
```

`§10:402-404`'s standing preference ("raise `n`; do not lower the margin") already commits
the design to this.

---

## D5 — MAJOR. The Stage 0 gate `g_j <= 0.010` is vacuous. Its derivation, precondition P6, and the entire blinded top-up mechanism are dead code, and `§34`'s predicted Stage 0 state is impossible.

### Proof

`§25.1:877-883` establishes the monotonicity lemma: `reach_win => reach_retain =>
reach_front`, each a disjunction over row labels, with representative selection and
`retained_by_argmax_score` both label-independent. Therefore a resolution can only move a
world **weakly later** in `A < B < C/D < E`. (The lemma is correct — see CREDITS.)

Under that lemma:

```
g_j > 0 for some j  <=>  some world's reach_j differs between rho_bot and rho_top
                    <=>  that world's class differs between rho_bot and rho_top
                    <=>  INDETERMINATE_WORLDS > 0
```

Monotonicity forbids cancellation, so the equivalence is exact in both directions:

```
INDETERMINATE_WORLDS == 0   <=>   g_1 = g_2 = g_3 = 0
```

### Consequences

1. **`§0.1:69`'s gate collapses to its second clause.** `g_j <= 0.010` is entirely
   subsumed. The 36.5%/97.3% resolving-power derivation at `§0.1:72-77`, the entry
   `g_max = 0.010` in the `§33:1138` derived-threshold inventory, and precondition
   `P6 DETERMINACY_OK` (`§20:691`) are all inoperative. One of the protocol's **two**
   claimed derived thresholds is a no-op.
2. **The blinded top-up is unreachable.** `§10:406-414` triggers extension to `n = 1,944`
   on `g_j > 0.010`. That state implies `INDETERMINATE_WORLDS > 0`, which `§22:812` (F2)
   and `§24:850` make an immediate **VOID**, and `§20:702` excludes from `QUALIFIED`.
   `§20:692`'s "[violation => blinded top-up of §10; NOT a re-read]" **directly contradicts
   §22 F2**. The design therefore has no power-rescue mechanism at all; the one it advertises
   can never fire.
3. **`§34:1158` predicts an impossible state:** *"`g <= 0.005` and `0` indeterminate
   worlds"*. Non-zero `g` with zero indeterminate worlds cannot occur. The author's
   pre-recorded expectation is not evaluable as written.
4. `§0.2:91-92`'s "the sealed E2a corpus fails it by a factor of 4–6" implies a graded
   scale that does not exist. The real Stage 0 bar is **`g = 0` exactly** across 539 worlds /
   189,467 rows / 397 escalated expressions — materially harsher than the document
   represents, and the gate on which Stage 1 is conditional.

### Minimal fix

Delete `g_max = 0.010`, `P6`, and the top-up; state the gate as `INDETERMINATE_WORLDS == 0`
and record that this means `g = 0`. If a genuine power top-up is wanted, trigger it on an
endpoint-blind quantity that is not identically zero — e.g. the realised `pi_B + pi_C+D`
entering the variance — and pre-declare it.

---

## D6 — MAJOR. A memory cap decides a scientific finding. `§25`'s governing rule is violated by `§25.3`, with a measured trigger already on file.

### What is wrong

`§25:860-861` (bolded, the governing rule): *"NO WALL-CLOCK CAP, **MEMORY CAP**,
WORKER-COUNT CHOICE, HOST-LOAD CONDITION OR CPU MODEL MAY DECIDE A SCIENTIFIC LABEL
ANYWHERE IN THIS PROTOCOL."*

`§25.3:913` then mandates: *"Per-worker RSS ceiling enforced in-process"*, and `§13:498-505`
requires it again. `§25.2:900-902` declares Tier 2 **"uncapped"**. These cannot all hold:
an RSS ceiling is a cap on the uncapped tier.

The escape offered is that a ceiling produces `UNRESOLVED`, never a label. But
`UNRESOLVED` on a **decisive** expression produces `INDETERMINATE_WORLDS > 0`, which
`§0.1:69` / `§22:810` (F0) converts into terminal `T-INSTRUMENT-UNBOUNDED`, described
verbatim as *"the G2 contract as frozen is **not decidable at finite cost on this class of
population**. A finding about the **contract**, not the pipeline."*

**A host RAM limit therefore produces a published scientific finding about the G2 contract.**
This is precisely the defect the protocol was written to eliminate (`§3:170-180`, a
wall-clock cap deciding a label), reproduced one level up, in the section that forbids it.

### The trigger is measured, not hypothetical

- `DINST_HOSTILE_REVIEW.md:39`: one randomly sampled stage-A abandoned expression reached
  **44.4 GB RSS after 95 s** on a 48.2 GB host and was still running when killed.
- `results/e2/run_x86_e2a_v1/POISON_WORLD_DETERMINATION.json`: world
  `V2C|E2|mass_power|c_low|n_default|r000` OOM-killed **four** times at 33.4/47.7/47.7/47.5 GB.
- `FROZEN_EVALUATOR_EXECUTION_MANIFEST.json`: Gate 1 lost two cases to the OOM killer above
  25 GB anon-rss.
- Stage 0 must escalate **all 397** distinct `SIMPLIFY_TIMEOUT` expressions to completion
  (`§0.1:44-46`). Scaling E2a's timeout rate (397 / 189,467 rows) to the Stage 1 surface
  (~531,000 rows at E2a's 11.7 rows per (world,seed) pair over 45,360 pairs) gives
  **~1,100** additional escalation candidates.

The probability that none of ~1,500 escalations behaves like the measured one is not
established anywhere, and the protocol's answer is a ceiling that converts the event into a
programme-terminating scientific claim.

Compounding: `SYNTHESIS_DECISION_RECORD.md §10` declares a **"ceiling: 260 CPU-hours"**
while `§25.2:900` declares Tier 2 **uncapped**. A declared compute ceiling over an uncapped
tier is either not a ceiling or not uncapped.

### Minimal fix

Pre-declare, before execution, what an expression that cannot be resolved within any
attainable resource envelope **means scientifically**, and separate it from
`T-INSTRUMENT-UNBOUNDED`. A distinct terminal — `T-RESOURCE-BOUNDED-ON-THIS-HOST`, reported
with the RSS ceiling, host memory and the offending expression strings, and explicitly
**not** a finding about the contract — is honest. Additionally, pre-declare the RSS ceiling
as a **declared parameter** in `§33`'s inventory (it is currently absent), and reconcile the
260 CPU-hour ceiling with Tier 2.

---

## D7 — MAJOR. Stage 0 leaks into Stage 1 through the resource-sizing channel, which controls Stage 1's VOID/not-VOID terminal.

`§0.1:60-64`: Stage 0 output *"may not be used to select, size, weight, exclude or re-read
anything in Stage 1 other than the binary gate below."*

`§0.1:57` makes *"the escalation cost distribution per expression"* a mandatory Stage 0
publication. `§13:483-487` (A4) then requires `WORKER_COUNT_CALIBRATION` to be *"re-run on
this host and its result recorded as a **declared parameter**"* with *"concurrency capped
with headroom sized for **the sympy tail**, not the median"* — and the sympy tail is exactly
what Stage 0's cost distribution measures. `§25.3:913` requires the RSS ceiling to be sized
similarly.

So: Stage 0 cost distribution → Stage 1 concurrency and RSS ceiling → Stage 1 OOM/UNRESOLVED
rate → Stage 1 `INDETERMINATE_WORLDS` → Stage 1 `VOID` vs proceed (`§22:812`). That is a
live channel from a Stage-0 output to a Stage-1 terminal state, contradicting `§0.1:60-64`.

It cannot change a **label** (D5's collapse means labels are invariant or the run voids), so
this is not fatal on its own. But the firewall is asserted as absolute and is not.

**Minimal fix.** Either size concurrency and the RSS ceiling from the *E2a engineering DEV
set* (`§26:923-930`, which is already permitted and already seen) and freeze them **before**
Stage 0 runs, or amend `§0.1` to declare the resource-sizing channel explicitly and bound
what it can affect.

**On the rest of the firewall:** the gate itself is binary and mechanical, Stage 1's
population/statistic/margins/routing/terminals are genuinely fixed in the frozen text before
Stage 0 runs, and the `EXPLANATORY_ONLY` stamp plus the static citation checker
(`§15:542-545`, `§31:1074-1075`) are real mechanisms. No other channel found.

---

## D8 — MODERATE. The pre-declared fallback population fails Gate Q by construction, guaranteeing a false diagnosis of a benchmark defect.

`§5.1:255-264` pre-declares the fallback as `development` ∪ `challenge`. Verified against
`src/muru/paper_benchmark/registry.py:15`:
`PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3}` — these are
**replicates per condition**. The fallback therefore supplies `4 + 3 = 7` replicates per
condition, 84 G2 worlds total.

Q1 (`§18:614`) requires *"every cell carrying exactly 108 completed worlds"*; `§20:683-684`
(P1 `COMPOSITION_EXACT`) repeats it as a hard-coded 108; `§7:305` repeats it a third time.
**The fallback fails Q1 and P1 with certainty, at 7 worlds per cell against 108.**

`§22:815` (F5) then fires: *"Q1 fails on both pre-enumerated attempts ⟹
`NO_ADMISSIBLE_SURFACE_EXISTS`. Since Q1 is a construction check this implies a mechanical
failure (ordinal drift, band collision, generator version mismatch) — **the benchmark needs
auditing before anything else proceeds**."*

So if attempt 1 fails for any reason, the protocol mechanically emits a false claim that the
benchmark is broken. Separately, `development` is the arm-development partition and `§5.1`
concedes it *"carries a contamination caveat"* while proceeding to use it inside a licensing
instrument.

**Minimal fix.** Parameterise P1/Q1 as "every cell carries exactly `R` completed worlds,
where `R` is the attempt's declared replicate count", declare `R = 7` for the fallback, and
label the fallback branch's terminal as `INSUFFICIENT_POWER_BY_CONSTRUCTION` rather than
routing it to F5. Or delete the fallback: `§5.1:262-264` already concedes it cannot certify
anything.

---

## D9 — MODERATE. The "sealed expression → label table" is not well-defined, and the one control against the demonstrated host-dependence failure is permitted never to run.

`§25.2:906-909`: *"Labels are computed once, escalated to completion, hashed and committed.
Classification at scoring time is then a lookup, **so the label is a pure function of the
expression string**."*

It is not. `§17:571-583` imports `g2_contract.classify_support` and
`classify_family_match`, which compare a candidate's effective support and discovered family
**against the world's truth**. `g2_correct = f(expression, truth)`, not `f(expression)`.
Trivial and low-complexity expressions (`x1`, constants, mass-only forms) recur across worlds
with different truths. A table keyed on the expression string alone would assign one label
across incompatible truths.

The charitable reading is that the table stores the *canonicalization* result
(`effective_support`, `discovered_family`), which **is** a function of the expression. The
protocol does not say so, and the distinction is load-bearing because `§28:993-997` rests
its two-architecture parity obligation on it:

> *"a pre-declared audit sample re-classified on a second architecture must return **0**
> mismatches **by construction**. If a second architecture is unreachable, this obligation
> is recorded as **discharged by construction and unverified by execution**."*

The documented root cause of the previous failure is `NEW_CLOUD_HOST_PARITY_FAILED` —
*"the same unmodified classifier assigns a different scientific label to the same expression
purely as a function of host speed"* (`§25:863-867`). The protocol's answer to a
**demonstrated** cross-host divergence is a control that may be discharged by assertion.
`§13:490` records `worlds_executed_on_this_host: 0`, i.e. a second architecture is already
known to be out of reach. So the waiver is not a contingency; it is the expected path.

**Minimal fix.** State explicitly that the table is keyed
`expression_string -> (effective_support, discovered_family, canonicalization_status)` and
that `g2_correct` is computed per (row, world) from the table; and make the two-architecture
parity check **mandatory on the canonicalization table only** (which is architecture-portable
and cheap — it needs no search), removing the waiver.

---

## D10 — MODERATE. Undeclared magnitudes inside a protocol whose central claim is that it has none.

`§33:1107-1147` claims to be *"THE COMPLETE INVENTORY — EVERY NUMBER IN THIS PROTOCOL"*
and `§18:600` / `§20:710` claim *"no numeric threshold that could be moved"* and
*"there is no knob in the qualification"*. Both are false:

| Location | Undeclared quantity | Why it matters |
|---|---|---|
| `§18:616` C-2 | number of adversarial constructions; pass bar | binary clause with an executor-chosen `n` |
| `§18:617` C-3 | number of analytically determinable worlds; pass bar | this is the control that would catch the §3 defect |
| `§18:618` C-4 | size of the "pre-declared sample" | only the 100% bar is frozen |
| `§18:619` C-5 | size of the "pre-declared subset" | only byte-identity is frozen |
| `§21.2:744` row 1 | *"a pre-declared band of 1"* (band **width** undeclared) and *"wherever `P_front` is **high**"* (undeclared) | this is the **first** row of the routing table, evaluated before row 2 |
| `§25.3:913` / `§13:500` | the per-worker RSS ceiling | see D6: it decides a terminal |

`§21.2` row 1 is the worst: an exoneration branch with two undefined predicates that fires
**ahead of** the certification test and terminates the protocol at `RC3_WITHDRAWN`. A
routing table whose first row is undefined is not mechanically evaluable, contradicting
`§20:650` (*"Evaluated mechanically from the sealed corpus. Every constant below is fixed at
freeze time"*).

**Minimal fix.** Declare all six in `§33` before freeze. Precedent exists for four of them
(Gate 1's 101/101 and 30/30 fix C-4 and C-5 counts). Row 1's band and the `P_front`
threshold must be numbers or the row must be deleted.

---

## D11 — MINOR (but it flatters the design). The `§10` resolving-power table is not reproducible from `§10`'s own formula and overstates the design's headroom.

Recomputing from `§10:376-382`'s equation `g = (z_.95 + z_.80)/sqrt(n + (z_.95+z_.80)^2)`:

| `n` | protocol `§10:395-400` | recomputed | in `delta` |
|---:|---:|---:|---:|
| 84 | 0.2429 | **0.2618** | 3.77 |
| 252 | 0.1448 | **0.1547** | 2.23 |
| 576 | 0.0964 | **0.1031** | 1.48 |
| **1296** | **0.0659 (0.95 delta)** | **0.0689 (0.992 delta)** | **0.99** |

Every row is understated, and the 1296 row is understated by a different factor (4.4%) than
the others (~6.5%), so the table is not even internally consistent with a single alternative
formula. The claimed `0.0659` resolving power requires **`n ~ 1,417`**, 9% more worlds than
the design has.

The honest statement is: *`n = 1296` certifies a lead of exactly `delta` at 80.6% power and
nothing materially smaller; the headroom over the derived minimum `n = 1275.8` is 1.6%, not
5%.* `SYNTHESIS_DECISION_RECORD.md §10`'s "powered exactly at the boundary of my own
predicted outcome" is right in substance and wrong in the numbers it publishes.

Verified separately: the `n >= 1275.8` derivation itself is **correct**, is driven by the
frozen `delta` (not reverse-engineered to be affordable — 48.6 CPU-hours of search is not a
binding budget), and uses the distribution-free bound `pi_1 + pi_2 <= 1`, which is genuinely
conservative (at the realistic `pi_B + pi_C+D ~ 0.86` the achieved power at a true lead of
`delta` is 85.4%, above nominal). **`n` is honestly derived; the table reporting it is not.**

**Minimal fix.** Republish the table.

---

## D12 — MINOR. `mass_power` is claimed to move to the NEG stratum; it is absent from the surface entirely.

`§7:300-303`: *"`mass_power` is EXCLUDED from the primary population... **It moves entirely
to the NEG control stratum of §5**."* `§5:232` defines NEG as `F07` (mass-only truth) and
`F19` (null worlds). `registry.py:141` confirms `F07 = "mass-only g truth"`. `mass_power` is
an E2a construct, not a registry family, and appears nowhere in the new surface.

This matters because `mass_power` is the family behind the four-times-OOM-killed poison world
(D6) and, per `§3:152-159`, the single largest source of the E2a divergence. Claiming it is
retained as a control when it is simply deleted overstates the surface's coverage.

**Minimal fix.** State that `mass_power` is absent from both strata, and that
`P7 NO_MASS_POWER` (`§20:693`) is satisfied by construction rather than by exclusion.

---

## D13 — MINOR / GOVERNANCE. Gate V is a necessary condition for every licence that the citation checker is required to conceal, and its retention should re-arm T9 by the protocol's own rule.

1. `§21.3:777-780` requires that a passing Gate V *"may **never** appear in the citation set
   of any change"*, enforced by the static citation checker. `§32:1094` makes Gate V
   `STANDS` a **necessary condition** of `E4A_LICENSED`. The protocol therefore mandates that
   a necessary condition of a licence be excluded from that licence's support set. The
   monotonicity argument (`§4:215`, `P(route = a | E2b) ∈ {P(route = a | ∅), 0}`) is
   formally correct for *which arm* is selected; it does not make the condition absent from
   the licence.
2. `§32:1098-1103`: *"Any future amendment that re-introduces a quantitative Held-out-matching
   qualification **re-arms T9 automatically**."* `§21.3` **is** a quantitative Held-out-matching
   requirement — it is simply positioned after the seal rather than before it. Both are
   necessary conditions for the licence; the qualification/veto distinction is nominal. By
   `§32`'s own rule, T9 is armed.
3. `§21.4:793-797` states the E6 circular dependency *"must be resolved by the protocol owner
   **before freeze**, not discovered at the end"*, yet `§0` line 15 and line 1182 declare the
   document **frozen** with the dependency unresolved and no E6 ceiling on file. `§32:1094`
   requires *"E6 ceiling available and met"*. `D3` item 8 is therefore unsatisfiable
   independently of D1.

**Minimal fix.** (1) Permit Gate V in the support set as a *necessary condition, non-supporting*
entry — concealment is worse than disclosure. (2) State that T9 is armed or excise Gate V.
(3) Obtain the E6 ceiling before freeze, as `§21.4` itself demands.

---

# ON THE CENTRAL QUESTION (attack item 1) — NO PROXY SUBSTITUTION FOUND

I looked hard for endpoint drift and did not find it.

`§20:666-675` defines the endpoint as `reach_front / reach_retain / reach_win`, each a
predicate on `g2_correct` computed by the **imported, byte-unchanged** `g2_contract`
(`§17:585`), differenced into the frozen A/B/C+D/E taxonomy of
`MURU_V2_E2_PREDECLARATION §6`. `SYNTHESIS_DECISION_RECORD §4` correctly establishes the
three parameterisations are bijective. The original G2 endpoint — support **and** family
recovery — is preserved intact. P1's counterfactual recovery contrast, which *would* have
been a proxy substitution, is correctly demoted to secondary (`§19` D7,
`SYNTHESIS_DECISION_RECORD §5`) and explicitly non-licensing.

The one substantive endpoint change is the pooling of `C` and `D`, and it is declared
(`§20:674-675`) and traceable to the predeclaration.

# ON QUALIFICATION BY PROVENANCE (attack item 2) — STRONGER THAN THE CHARGE ASSUMES, BUT CIRCULARITY RETURNS AT GATE V

The charge that provenance is insufficient because "a surface can be drawn from the same
generator and still not reproduce the regime — different conditions, different coefficient
and noise cells" **does not land here**, and I record that against my own interest:

- The 12 conditions are not a free choice. `registry.py:135-152` fixes them; `held_out`'s
  own G2 population is those same 12 conditions at
  `PARTITION_CASE_COUNTS["held_out"] = 12` replicates each = 144 worlds, which is exactly the
  sealed denominator. The calibration surface is the same 12 conditions at 108 replicates.
  **The condition grid is matched by identity, not by resemblance.**
- The truth-family mix follows (`§7:293-297`): affine 9/12, saturating 1/12, interaction 1/12,
  exponential 1/12, `mass_power` 0/12 — the Held-out mix exactly, by construction.
- Coefficients and noise are the generator's own draws (`§8:316-324`, `§9:327-339`), not a
  lattice. E2a's three-point coefficient ladder and 1/3 noiseless weighting — the two largest
  composition artefacts — are not reproduced.
- Gate Q reads `registry.py`, `generator.py`, `rc5_seeds.py` and cites **no outcome**
  (`§4:213`). I verified the registry facts independently; they hold.

What remains unmatched is (i) host/architecture, conceded and unestablished
(`§13:489-496`), and (ii) the replicate block itself — an irreducible sampling difference
that is the point of an independent draw.

**But the circularity does return, through Gate V.** `§4:195-201` declares the design makes
no claim that *"the surface reproduces the Held-out behaviour"*; `§32:1094` then makes
Held-out behavioural agreement within `TV <= delta` a **necessary condition of every
licence**. The resemblance requirement was moved from Gate Q to Gate V, not removed. Because
the comparator is E2b-derived `DECISION_INADMISSIBLE` evidence treated as a constant (D3),
and because a trip is conceded non-attributable (`§21.3:783-785`), the design's positive
branch is gated on a comparison it has itself declared uninterpretable — and, per D1,
gated on one that can never pass.

---

# CREDITS — WHAT SURVIVED THE ATTACK

Recorded so this review is not read as uniform hostility.

1. **The monotonicity lemma (`§25.1:877-883`) is correct.** I attacked it at the code level
   as `§30:1037-1038` requires. `reach_win => reach_retain => reach_front` because the
   cross-seed representative is drawn from retained candidates and retained candidates are
   front rows; representative selection uses `identity_contract.template_key` and never reads
   `g2_correct`; `retained_by_argmax_score` is a score comparison. All three reach predicates
   are disjunctions over row labels, hence monotone, and the class order `A < B < C/D < E`
   moves weakly later under any resolution. Two evaluations genuinely suffice; `2^U` is not
   needed. No counterexample constructible.
2. **The instrument replacement is the right correction.** Retiring `SIMPLIFY_TIMEOUT` as a
   classification rule (`§25:863`), CPU-time rather than wall-clock for the cost bound
   (`§25.2:896-899`), deriving the cap exception from `BaseException` so `g2_contract`'s
   seven `except Exception: return None` handlers cannot swallow it (`§25.2:903-905`), and
   `UNRESOLVED` as its own state that is never folded (`§24:849`) — these are all correct and
   all target the actual mechanism.
3. **C-3 is a real control, not a decorative one.** *"Includes, mandatorily, a planted correct
   row that is expensive to canonicalize, verifying the instrument does not report
   `NEVER_ON_FRONT`"* (`§18:617`) is precisely the known-answer test that would have caught
   the §3 defect. C-1 (retention identity against the production path) and R0 replay
   self-consistency (`§28:986-988`) are answerable against the pipeline rather than the
   attribution, which is the correct property for a control. Their **sizes** are undeclared
   (D10), but their **construction** is sound. The NEG stratum at 216 worlds genuinely clears
   E6's `>= 100 evaluable safety opportunities`.
4. **The sample size is honestly derived** (D11's arithmetic complaint notwithstanding):
   driven by the frozen `delta`, using a distribution-free variance bound, explicitly
   rejecting the Held-out-informed `delta_dec = 0.0556` and `pi_1 + pi_2 = 0.875`. Compute is
   not the binding constraint (48.6 CPU-hours of search at the measured 3.86 s/search
   reproduces exactly), so `n` was not reverse-engineered to be affordable.
5. **The routing certification is conservative under a 3-way tie** (3.4–3.6% against a
   nominal 5%). It fails only under the 2-way tie (D4).
6. **Row 5 pre-labelling (`§21.2:748-757`) is genuine and costly to the author.** Declaring
   the `C+D` route non-executable *before* execution, when `§34` assigns it 10%, is exactly
   the discipline the section claims. It is also — see D1 — the only route that survives
   Gate V, which makes the pre-labelling far more consequential than the author realised.
7. **`§26`'s use of the invalidated E2a corpus as the engineering DEV set** is a genuinely
   good idea: zero leakage because E2a is already barred from licensing, at zero scientific
   compute.

None of this rescues the design. A careful instrument with an empty positive outcome space
is still an instrument that cannot answer its question.

---

# THE HONEST-FAILURE TEST (attack item 8)

**What would falsify the design's own premise?** The premise (`§1:110-121`, `§4:189-193`) is
that a provenance-matched independent draw can produce a *decision-admissible* stage
attribution. It is falsified if, for every possible realisation of that draw, no licence can
issue.

**That is the case, and it is provable at zero compute (D1).** The design admits the outcome
in the weak sense that `ROUTING_INDETERMINATE`, `HALTED` and
`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` are all declared terminals. It does **not** admit it in
the sense that matters: nowhere does the protocol state that its licensing rows are
unreachable, and `§32:1094-1095` presents two licensing terminals as live.

`§34`'s pre-recorded expectation is therefore an **alibi**, though I judge it an unwitting
one. The author predicted the right answer (`no E4 re-entry on any branch`) from the wrong
premise (an empirical near-tie at ~55%) and thereby earned credit for humility that the
design's arithmetic had already made unavoidable. The correct pre-recorded statement is:
*"`P(E4A_LICENSED) = 0` and `P(E4_GENERATION_LICENSED) = 0` for every dataset, because Gate R
row 3 and Gate V are jointly infeasible at `n = 1296`."* Had that been computed before freeze
— and it is ten lines of arithmetic on numbers already in the document — the design would
have been rejected or resized at the council stage.

**Symmetrically, the design cannot fail honestly either.** Under D3 it VOIDs 21% of the time
against a perfect surface; under D2 it may be forbidden from executing at all; under D6 its
Stage 0 terminal is decided by host RAM and published as a finding about the G2 contract.

---

# REQUIRED BEFORE FREEZE

Blocking (the protocol must not execute until each is resolved):

1. **D1** — reconcile Gate V's tolerance with Gate R's certification margin, or declare rows
   3 and 4 non-executable. Recommended: apply `delta` to `max_k |pi_k - pi_0k|`, the
   per-class statistic it was frozen on.
2. **D2** — replace or delete `QND_PASS`. It is currently either an execution prohibition or
   a no-op.
3. **D3** — put an interval on the 144-case comparator, or delete Gate V.
4. **D6** — pre-declare a resource-bounded terminal distinct from `T-INSTRUMENT-UNBOUNDED`,
   and reconcile "uncapped" Tier 2 with the RSS ceiling and the 260 CPU-hour budget.
5. **D13(3)** — obtain the E6 false-structure ceiling, as `§21.4` itself requires.

Non-blocking but required for the document to mean what it says: D4 (alpha and the
consequent `n`), D5 (delete the vacuous gate and the unreachable top-up; fix `§34`), D7
(freeze resource sizing before Stage 0), D8 (parameterise the replicate count), D9 (define
the table's key; make the parity check mandatory on it), D10 (declare the six missing
magnitudes in `§33`), D11 (republish the table), D12 (correct the `mass_power` claim).

---

**CRITIC_SCIENCE = FAIL**

*Methods: all statistical claims recomputed from first principles with
`/home/aryav_thakur/venv/bin/python` (scipy/numpy); Monte Carlo at 200,000 multinomial draws;
route reachability by constrained SLSQP minimisation of `TV` over the simplex with 400
random restarts. Corpus structure verified directly against
`results/e2/run_x86_e2a_v1/WORLD_ORDER_539_MAIN.json` and
`src/muru/paper_benchmark/registry.py`. No sealed evidence was read for licensing purposes
and none was modified.*
