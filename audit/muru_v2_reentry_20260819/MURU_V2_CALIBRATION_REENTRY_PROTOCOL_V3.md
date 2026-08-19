# MURU v2 — CALIBRATION / RE-ENTRY PROTOCOL, **VERSION 3**

> ## THIS IS A PROSPECTIVE POST-GATE-1 PROTOCOL-OWNER AMENDMENT
> ## CREATED UNDER THE MAXIMUM-AUTHORIZATION INSTRUCTION.
> ## IT IS **NOT** HISTORICALLY PREREGISTERED AND MUST NEVER BE DESCRIBED AS SUCH.
>
> Authority to exist: `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10. Provenance discipline:
> ratification §10 and P2 PM-17. Calling this document a "preregistration" without the above
> qualifier is a provenance misstatement of the exact kind the Gate 1 record already had to
> withdraw once. The filename says `PROTOCOL_V2` for that reason (repairs `S23`).

**Experiment identifier:** `E7 — CALIBRATION PARTITION RE-ENTRY SURFACE`

**Supersession.** This document **supersedes**
`MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md`
(sha256 `38d1e997355f712f98eb205439dd3869e21f3a95112e05e8980d886bab758117`, 1,183 lines),
which is **retained in the repository as superseded** and must not be executed. v1 failed two
independent hostile pre-freeze reviews:
`CRITIC_SCIENCE_REENTRY.md` = **FAIL** (defects D1–D13) and
`CRITIC_GOVERNANCE_REENTRY.md` = **FAIL** (defects S1–S25).
Every one of those 38 defects is dispositioned in `V2_REPAIR_LEDGER.md`, in the same
directory, as FIXED / NOT-A-DEFECT / ACCEPTED-LIMITATION.

**Status at this commit: PROTOCOL TEXT, VERSION 3. NOT YET FROZEN. D3 item 7 is UNMET.**
**No calibration world generated. No calibration search executed. No re-entry licensed.**

> **`G2` correction — v2's status line was FALSE at its own HEAD, and this one is written to
> be checkable.** v2 declared *"No module written. No search executed."* while (a) both §5.2
> modules existed on disk and (b) Stage 0 had been executed **three times**. State of the
> world at **this** commit, verifiable by `git log` and `ls`:
>
> | claim | status |
> |---|---|
> | §5.2 modules `calibration_surface.py`, `calibration_seed_band.py` | **WRITTEN and COMMITTED.** Control `C-0` executed: **380/380 identical, 0 mismatched, 5.3 s** |
> | any calibration (`PBC|`) world generated | **NONE** |
> | any calibration search executed | **NONE** |
> | Stage 0 (D-INST) | **EXECUTED THREE TIMES, ALL THREE INADMISSIBLE AND QUARANTINED.** See §0.7 |
> | re-entry licensed | **NONE** |
>
> Writing the population modules before the freeze is **correct and required**: §5.2 makes
> `C-0` a precondition of Route R-B, and `C-0` cannot be evaluated without them. Their
> existence is not execution. What was **not** correct was Stage 0's three runs, which §0.7
> now records in full rather than in a status line that denied them.
(v1 asserted a freeze that had not been performed; `S12`. This document does not.)

**Threshold discipline (binding on every number in this document).** Every threshold is
either **(i) REUSED VERBATIM** from frozen authority with a citation the author verified by
direct read, or **(ii) DERIVED** from first principles with the derivation shown inline.
**§34 is the complete and exhaustive list of free parameters** — v1's claim that it
introduced "exactly one new magnitude" was false (`S4`) and is not repeated.
**No wall-clock cap, memory cap, worker count, host-load condition, CPU model or compute
budget may decide a scientific label or a scientific terminal anywhere in this protocol, at
any level, including meta-level terminals** (§25, repairing `D6`).

---

## 0. WHAT CHANGED FROM v1, IN ONE PLACE

Two decisions were taken by the protocol owner and coordinator before this document was
written. They are implemented here and are **not relitigated**.

### 0.1 DECISION 1 — Gate V is removed as a gate

v1 §21.3 made every licence conditional on a post-seal veto
`TV(pi_hat, pi_0) <= delta` against the sealed Held-out attribution `pi_0`. Both critics
proved, and the coordinator confirmed by constrained minimisation over the simplex, that
**this leaves no reachable positive licensing terminal for any dataset**:

| Certified route | minimum attainable `TV` over ALL data at `n = 1296` | v1 Gate V at tolerance 0.0694 |
|---|---:|---|
| `A` (generation) | 0.2578 | VETOED always |
| `B` (retention) → the only full re-entry terminal | 0.0783 | VETOED always |
| `C+D` (cross-seed) | 0.0008 | STANDS — and v1 pre-labelled it non-executable |

with a minimum certifiable lead of `0.0427` at `n = 1296`. The coordinator additionally
tested `CRITIC_SCIENCE`'s proposed repair — replacing total variation with the per-class
maximum deviation `max_k |pi_k - pi_0k|`, arguably the statistic PE2-4 was actually frozen on
— and it **does not help**: route B's minimum is `0.0781` against the same `0.0694`.
> **`G5` — the robustness claim is WITHDRAWN in the dimension that matters.**
> `CRITIC_GOVERNANCE` found that *"the impasse is robust"* was tested across **statistics**
> but never across **thresholds**, and that §21.4's own bootstrap shows a calibrated tolerance
> would admit route B. It further found that the forward-run event log at `07:20:00Z` records
> the **milder** repair being rejected as results-aware *"having computed exactly which routes
> each tolerance admits"*, while the **maximal** repair was adopted on the same information.
> That asymmetry is real and I do not defend it.
>
> **Decision 1 therefore rests on its AUTHORITY ground alone, which review found sound**
> (*"The authority argument is real and P2 item 38 sanctions omission"*). The robustness
> claim is struck from the justification and is not relied on anywhere. The sentence below is
> retained, struck through, so the withdrawal is visible rather than silent:
>
> ~~The impasse is robust to the choice of statistic, so changing the distance is not the~~
repair.**

**The repair is grounded in authority, not in results.** `befca0d` §2.3 states, verbatim
(verified by `git show befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md`, lines 76–78):

> *"**E2b outputs are `DECISION_INADMISSIBLE`.** No v2 threshold, retention rule, grammar
> change, classifier change or benchmark change may be justified by E2b. E2b may only
> corroborate or contradict a conclusion already reached on E2a."*

"Corroborate or contradict a conclusion **already reached**" is an **annotation applied
after a conclusion is reached**. It is not a gate determining whether the conclusion stands.
The single place in frozen authority where E2b is granted blocking power is the §2.9
falsification hook, operationalised as `f4c1105` §4 **GATE 1** — and that hook has **already
fired**, was adjudicated `GATE_1 = FAIL`, `GATE_1_DEFINITIVE = YES`, and is sealed. A
**second** E2b veto, applied to the **routing statistic**, has no basis in frozen authority.

Worse, it is not even a veto. Its admissible set is the singleton `{C+D}` — which is E2b's
own argmax — so extensionally it **selects** the route, which §2.3's second sentence
forbids in terms ("no ... change may be justified by E2b"). v1's §4 property (iii) proved
channel monotonicity **per arm**, which is true and insufficient: when a veto zeroes every
arm except the one the comparator itself names, the composite map is a selector.

**SO: Gate V is removed as a gate.** It is replaced by a **mandatory reported
corroborate/contradict annotation** (§21.4) computed **after** the routing verdict is sealed
and hash-chained, which **can change no terminal state and licenses nothing**.

**The counter-argument, stated fairly and at full strength.** `befca0d` §2.3's *final*
paragraph reads, verbatim:

> *"**If E2a and E2b disagree**, that is itself a finding and it blocks adoption of any E4
> conclusion until explained. Divergence would mean the fresh worlds do not reproduce the
> Held-out regime, which invalidates E2a as a calibration surface."*

That sentence **does** attach a blocking consequence to disagreement, and a reader is
entitled to say that removing Gate V removes a blocking rule that frozen authority actually
contains. Three responses, none of which fully dissolves the objection:

1. The clause says *"blocks adoption ... **until explained**"*, not "vetoes". It is a
   disclosure-and-explanation obligation. **This protocol does NOT retain it as a
   precondition** (`N1` correction, superseding the claim originally made here): §21.5's
   `G6` repair makes the §21.4 annotation condition **nothing** — no terminal, licence, gate
   or ratification requirement depends on its value, for any route. What is retained is
   **disclosure**: the annotation is computed, published and quoted in full, including a
   `CONTRADICTS` reading, so an owner reads it before acting — but nothing in this protocol
   compels the owner to explain it before a licence proposal exists, because (§2.1) no
   licence under this protocol currently becomes operative without a separate ratification
   act regardless of the annotation's value. The loss of `befca0d` §2.3's obligation is
   accepted as a further disclosed limitation, alongside the loss of falsification power
   response 3 already records.
2. The clause's antecedent is *"E2a and E2b"*. Ratified **D5** invalidated E2a as a
   held-out-facing calibration surface; the surface this protocol builds is **not E2a**. The
   clause's literal referent no longer exists. Extending it to a new surface is a
   generalisation, not reuse — and the extension is what v1 mislabelled "REUSED VERBATIM".
3. Reading a qualitative *"disagree"* as a quantitative `TV <= 10/144` veto is precisely the
   threshold-transfer error `P2 BC-16` warns about (`S5`). The number 10/144 was frozen
   against **absolute deviations of two class counts on a two-way split**, not against a
   four-cell total-variation distance.

**What survives of the objection, and is accepted as a limitation:** this protocol has
**less falsification power** than v1 claimed to have. Decision rule **R2** ("strongest
falsification opportunity") is therefore **overridden here by R3** ("keeps Held-out evidence
out of positive licensing") and by the plain reading of §2.3's second sentence. That
override is recorded, not hidden. See `V2_REPAIR_LEDGER.md`, rows `S1`/`D1`/`D13`.

### 0.2 DECISION 2 — Route C+D → E4f family i is now PREREGISTERED (v2 said "EXECUTABLE"; withdrawn, see §2.1 and §21.2 row 3)

v1 §21.2 row 5 pre-labelled the `C+D` route `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`, because
E4f had no operational freeze and *"inventing those ceilings after the route is known is
prohibited."* **That was correct at the time.** It is no longer the state of the world.

`MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` now exists:

| Fact | Value, verified at this commit |
|---|---|
| Freeze commit | `8a2ffa504f1dafd7b07d85bc6cab2b74be1cbdaa` — `git cat-file -t` = commit; `git merge-base --is-ancestor 8a2ffa50 HEAD` = true |
| Results-blind ancestor at authorship | `119ba265e16d2fed04cc332b879803b407562a05` |
| Artifact sha256 | `0ce2755d9661d707a48961d11477fd6b793f8567c0e835e058a180d2763a7f61` (re-verified against the file at this commit) |
| Tuning ledger | **EMPTY** (`E4F_FREEZE.txt`) |
| Margin | **exactly 0** — control-relative non-inferiority, no invented absolute ceiling |

It was written **results-blind**: at `8a2ffa50` no calibration surface existed, no route
existed, and no `false_labelling_rate` or `k_inflation` value had ever been computed by
anyone, for any arm, on any population — each independently checkable from the freeze
record. **The routing table is updated accordingly (§21.2 row 3).**

**v1's anti-tampering intent is preserved and strengthened, not discarded.** The E4f freeze
**predates any route** and **may not be amended after one**. Any post-route change to E4f's
gates, margins, populations or terminals voids E4f under its own §13
`E4F_VOID_TUNING_LEDGER_NONEMPTY`. §36 of this document declares the one
population-by-reference restatement that this protocol's corrected `n` forces, records it as
**results-blind and pre-route**, and requires the protocol owner to countersign it **before**
any route exists — precisely so it can never be done afterwards.

### 0.3 Everything else that changed

Summarised for orientation only; each is authoritative in its own section.

| Repair | Where | Defects closed |
|---|---|---|
| Freeze-clean population route: a **new module**, zero protected bytes touched, equivalence **demonstrated 380/380** | §5 | `S2`, `S19` |
| `QND_PASS` deleted as an unsatisfiable empirical clause; replaced by an **in-text constructive non-determination proof with exhibited witnesses** | §4.1, §32.1 | `D2`, `S9` |
| Routing critical value corrected to `z_.975`; **materiality clause `lead >= delta` added**; `n` re-derived to **1,656** | §10, §21.1 | `D4`, `S6`, `D11`, `S15` |
| `g_max = 0.010`, precondition `P6`, and the blinded top-up **deleted as provably vacuous** | §0.4, §20, §22 | `D5`, `S4`, `S10` |
| Resource exhaustion produces an **operational non-terminal**, never a scientific label at any level | §25.4 | `D6` |
| Stage-0→Stage-1 resource-sizing channel closed by freezing sizing **before** Stage 0 | §13, §25.5 | `D7` |
| `development ∪ challenge` fallback **deleted**; replaced by a route-failure ladder that cannot emit a false benchmark-defect claim | §5.4, §22 | `D8` |
| Expression→label table **re-keyed** and two-architecture parity made mandatory on it | §25.3, §28 | `D9` |
| Every previously undeclared magnitude declared | §33, §34 | `D10` |
| `TV` defined | §21.4 | `S3` |
| `10/144` moved from REUSED to DERIVED with its derivation shown | §33 | `S5` |
| Exoneration branch given a derived predicate with zero new magnitudes | §21.2, §21.3 | `S7` |
| **§22 is the sole terminal-assigning authority**; terminals exhaustive, exclusive, reachable, honestly named | §22, §32 | `S8`, `S11` |
| E6 circularity dissolved: the ceiling is frozen text, the opportunities come from this surface's own NEG stratum | §21.5 | `D13(3)`, `S14` |
| One definition of `QUALIFIED` | §18, §20 | `S18` |
| Licence is **proposed, not issued**; owner ratification required | §21.5 | `S24` |

### 0.4 Structure — two stages, and Stage 1 is conditional

```
STAGE 0   INSTRUMENT VALIDATION ON THE SEALED E2a CORPUS
          zero new search · explanatory-only · licenses nothing · citable by nothing
          GATE: INDETERMINATE_WORLDS_E2A == 0
                  |                                    |
                 PASS                                 FAIL
                  v                                    v
STAGE 1   THE CALIBRATION SURFACE            T-INSTRUMENT-UNBOUNDED-ON-E2A
          Gate Q -> Gate R (sealed) -> §21.4 annotation      STOP
```

**The Stage 0 gate is `INDETERMINATE_WORLDS_E2A == 0` and nothing else.** v1 conjoined
`g_j <= 0.010`. Under v1 §25.1's own monotonicity lemma — which `CRITIC_SCIENCE` attacked at
the code level and could not break, and which this protocol retains unchanged (§25.1) —

```
reach_win  =>  reach_retain  =>  reach_front,   each a disjunction over row labels;
representative selection never reads g2_correct; retained_by_argmax_score is a score
comparison.  Hence every resolution moves a world WEAKLY LATER in A < B < C/D < E, and
no cancellation between worlds is possible.
```

Therefore `g_j = S_j(rho_top) - S_j(rho_bot) > 0` for some `j` **if and only if** some
world's class differs between the two extreme resolutions, i.e. **if and only if**
`INDETERMINATE_WORLDS > 0`. The equivalence is exact in both directions.
`g_j <= 0.010` was **entirely subsumed** by the second clause; the derived
`g_max = 0.010`, the undeclared factor `1.4` behind it, precondition `P6`, and the whole
blinded top-up to `n = 1,944` were **dead code** (`D5`, `S4`). They are deleted. The real
bar is `g = 0` exactly, and this document says so.

`INDETERMINATE_WORLDS == 0` is **REUSED**: P2 §6.2's least-discretionary choice, taken from
demonstrated achievement — the sealed Gate 1 adjudication achieved 158/51,411 = 0.31% rows
unresolved and **0** indeterminate cases across 144 (`FINAL_TERMINAL_REPORT.md` §3).

**A useful consequence, used throughout.** Because `INDETERMINATE_WORLDS == 0` is a hard
precondition of Stage 1 too (§20 `P6'`), `rho_bot` and `rho_top` **coincide on any surface
that reaches the routing step**. Every "under both resolutions" clause below is therefore
satisfied automatically whenever the run is admissible at all, and fails loudly otherwise.
This is stated because it makes the argmax-invariance requirement mechanical rather than
aspirational.

### 0.5 What Stage 0 is, and is NOT, for

**Stage 0 is instrument validation. It is not an explanation of the E2a/E2b divergence.**
That question is already answered analytically, at zero compute, in
`SYNTHESIS_DECISION_RECORD.md` §1.2–§1.3: the corrected determinacy bound is
`A ∈ [49,122]`, `B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`; the frozen Gate-2
predicate `B > A AND B > C+D` holds at **every** point of it; and correcting the instrument
moves E2a **further** from the sealed Held-out attribution (total variation 14.78 → 25.00
cases pooled, 10.67 → 17.00 noise-matched). **No statement of the form "the E2a/E2b
divergence is explained by the wall-clock timer" may be made or cited under this protocol.**

Stage 0 exists to (a) establish that the escalation instrument terminates with zero
indeterminate worlds on a real 539-world / 189,467-row corpus, and (b) validate the
evaluator, escalation harness, schema validator and bootstrap code against that corpus at
**zero scientific compute and zero leakage**, since D5 already bars E2a from licensing
anything.

**Stage 0's identity is fixed here, closing `CRITIC_GOVERNANCE` §7's open question.**
Stage 0 **is** the frozen D-INST protocol
(`MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md`, tag `muru-freeze/dinst-protocol`,
commit `7e99830`) **widened in exactly one respect and in no other**: D-INST escalates the
314 timed-out rows inside the 73 affected stage-A worlds; Stage 0 escalates **all 397
distinct `SIMPLIFY_TIMEOUT` expressions** in the corpus, so that the control-stratum result
is measured rather than assumed. D-INST's determinacy standard, its subprocess isolation,
its `UNRESOLVED`-is-never-a-classification rule and its terminal names are adopted
unchanged. D-INST's three terminals (`D-INST-DETERMINATE`, `D-INST-INDETERMINATE`,
`D-INST-PLURALITY-NOT-INVARIANT`) are **Stage 0's own disjoint terminal set, sealed
separately** (§22.2), and are **not** members of §32's Stage 1 terminal set (`S8`).

**Stage 0's gate is over-conservative and this is disclosed.** Stage 0 runs on E2a. E2a
contains **zero** F17 (`equivalent symbolic forms`) worlds — the registry condition whose
frozen purpose is *"canonicalize equivalent laws"* and which is the single most likely
source of canonicalization-expensive expressions. Stage 1's population contains **138** of
them. A Stage 0 PASS is therefore **weak** evidence that the instrument is bounded on Stage
1's population, and a Stage 0 FAIL says nothing at all about Stage 1's population
(`S11`). Two consequences, both binding:

1. The Stage 0 failure terminal is named **`T-INSTRUMENT-UNBOUNDED-ON-E2A`**, and its gloss
   is restricted accordingly (§32).
2. The **real** protection for Stage 1 is Stage 1's own precondition `P6'`
   (`INDETERMINATE_WORLDS == 0` on the calibration surface itself), not Stage 0.

---

### 0.7 STAGE 0's THREE INADMISSIBLE RUNS, AND THE SINGLE-SHOT RULE IT NEVER HAD

`CRITIC_SCIENCE` `DEF-C3` and `CRITIC_GOVERNANCE` `G2` both found Stage 0 executing **before
the freeze it gates**, on a corpus it was simultaneously being debugged against, re-run after
each observed failure, with **no single-shot rule and no tuning ledger**. Both findings are
upheld. Stage 0 was **halted** on receipt of the reviews, at 47/396 pairs, and nothing was
sealed. The full record:

| run | when | workers | bound | outcome | why inadmissible |
|---|---|---|---|---|---|
| 1 | 02:42–02:55 | 22 | 8 GiB `RLIMIT_AS` | 22 pairs completed | superseded bound; `479656b` tightened 8 GiB → 6 GiB **mid-run**, so the set straddles two instrument configurations |
| 2 | 13:31–13:37 | 6 | 6 GiB | **396/396 null** | wrong interpreter: bare `python3` = `/usr/bin/python3`, no `numpy`, no `muru`. Every payload died at import. All records `wall_seconds == 0.0` |
| 3 | 13:52–14:2x | 6 → 12 | 6 GiB | halted at 47/396 | halted pre-freeze on receipt of the hostile reviews |

**What the executor did that was wrong, stated plainly.** I inspected run 1's verdicts (19
INCORRECT, 1 CORRECT, 2 `MEMORY_SIMPLIFY`) and its wall-time distribution, and published that
comparison, **before** the instrument was final. Even used only as a reproducibility check and
entering no count, that is looking at outcomes from a gating instrument while still changing
it. It is the channel `D7` exists to close, and no amount of "it changed no count" repairs the
order in which it happened.

**Binding rules for Stage 0, which v2 had only for Stage 1:**

```
S0-1  SINGLE SHOT. Exactly one admissible Stage 0 run. Its tool hash, protocol hash,
      interpreter, worker count and memory bound are FROZEN AND PUBLISHED BEFORE IT STARTS.
S0-2  TUNING LEDGER. Stage 0 has one, it starts EMPTY, and every instrument change after
      the freeze is an entry. A non-empty ledger VOIDS the Stage 0 result exactly as P10
      voids Stage 1's.
S0-3  NO OUTCOME INSPECTION BEFORE FREEZE. No verdict, count, wall-time distribution or
      terminal from any Stage 0 execution may be read before S0-1's freeze is published.
      Runs 1-3 are quarantined under _quarantine/ and are EXPLANATORY_ONLY: they enter no
      count, no denominator, no bound and no terminal.
S0-4  A RESOURCE EVENT IS NOT A RESULT. Section 25.4 governs Stage 0 identically. A run
      that ends in RUN_INCOMPLETE_RESOURCE_EXHAUSTION may be resumed on a larger host
      WITHOUT a ledger entry, because nothing scientific was read -- and may NOT be
      resumed with a changed bound, which IS a ledger entry.
S0-5  ENVIRONMENT FAILURE IS NOT A RUN. Run 2 produced 396 records and a well-formed
      terminal while computing nothing. Preflight now refuses to start under an
      interpreter that cannot execute the payload, and the tool refuses to emit a pass
      terminal when every pair is UNRESOLVED. A run barred by preflight does not consume
      the single shot, because it produced no evidence of any kind.
```

**`S0-5`'s exemption is narrow and is stated so it cannot be stretched.** It covers a run that
produced **no evidence whatsoever** — every pair dead at import, every `wall_seconds == 0.0`.
It does **not** cover a run that produced some verdicts and then failed, which consumes the
single shot like any other.

### 0.8 `G11` — the S16 blindness qualification

Commit `b4ea2a0`'s subject says the S16 re-derivation was made *"independently of `pi_0`"*.
`CRITIC_GOVERNANCE` `G11` observes that the task brief **quoted `pi_0`** (A .09722 / B .38194
/ C+D .49306 / E .02778), so "blind" in the strict sense of never-exposed is false.

The **document** is scrupulous and was not the problem: `S16_BLIND_COMPOSITION_DERIVATION.md`
item 4 discloses the exposure itself, states it was supplied rather than retrieved, and spells
out concretely what a contaminated derivation would have looked like (reasoning backwards from
the common denominator 144). §1 derives 144 from `endpoint_applies_to_variant` over the
registry, before and independently of `pi_0`.

**The accurate characterisation, which replaces the commit subject's claim everywhere it is
cited:** *exposure disclosed; unused in the derivation; the rule reproduces from `registry.py`
and `generator.py` alone with zero free parameters.* Blindness of **procedure**, not of
**exposure**. §16's `G16` note applies equally: `pi_0` is printed in this protocol, in the
ratification and in the E4f document, so every "results-blind" claim in this programme is an
**artifact-order** claim — that no design choice was made after consulting an outcome — and
never a claim that no outcome was ever visible. That is the strongest form of blindness
available at this point in the programme, and it is the form claimed.

## 1. PURPOSE

To construct and execute the prospectively frozen, decision-admissible calibration and
re-entry qualification required by ratified decision **D3**, items 1–7 (protocol
construction) and item 8 (execution), so that `EXPERIMENTAL_REENTRY_RESOLUTION` can be
evaluated on evidence that is admissible for licensing.

The scientific question, in one sentence, unchanged from v1:

> On an independent draw from the benchmark's own G2 condition grid — the same generator,
> the same twelve prospectively declared experimental conditions, the same coefficient and
> noise design as the Held-out population, in a population disjoint from `held_out` and
> never used for any endpoint — **which single pipeline stage (generation, within-seed
> retention, cross-seed identity voting) first loses the G2 signal, and does its lead over
> the runner-up exceed the programme's own definition of a material attribution
> difference?**

This is the **original causal question** of `befca0d` §2.1 (`H_retain` / `H_generate` /
`H_partial`) and §2.9's licensing table, preserved verbatim, on a population that can
actually answer it. Decision rule **R1** governs and is not overridden anywhere in this
document.

## 2. AUTHORITY

| Source | What it supplies |
|---|---|
| `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §10 | authority for this document to exist; its status as a prospective post-Gate-1 amendment |
| ratification §5 (D3) | the eight `EXPERIMENTAL_REENTRY_RESOLUTION` items this protocol must satisfy |
| ratification §7 (D5) | E2a invalidated as a Held-out-facing calibration surface; `LOCKED_EXECUTE_E4A` has no forward-licensing force; the `B` plurality may not be cited to license E4a |
| ratification §8 (D6) | any new decision-relevant corpus must satisfy the frozen required schema **from inception**; no retroactive field fabrication; regenerate rather than impute |
| ratification §4 (D2-ext) | all E4 arms suspended; no automatic re-entry |
| ratification §6 (D4) | E5 deferred; its reconsideration trigger remains with the protocol owner (§32.4, closing `S25`) |
| `befca0d` (`MURU_V2_G2_PARETO_STUDY_DESIGN.md`) §2.3–§2.11, §3 | inadmissibility of E2b; the 28-field schema; truth-blind boundary; controls; conditional-stage metrics; the §2.9 licensing table; the safety-cost requirement |
| `MURU_V2_E2_PREDECLARATION.md` §4/§5/§6 | world enumeration, seed derivation, the A–E taxonomy and its strict decision order |
| `f4c1105` (`v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`) §4/§5/§6/§7/§8/§9 | materiality tolerance; the Gate-2 branch structure including the exoneration and tie branches; DEV/EVAL discipline; paired statistics; multiplicity; controls |
| `1d20731` / `94abf97` (E3) | completed identifiability verdicts, binding on the generation branch |
| `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` @ `8a2ffa50` | the operational freeze for the `C+D` route. **Its authority is the protocol owner's maximum-autonomy delegation, NOT ratification §10 — see the correction below** |
| `MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md` @ `7e99830` | Stage 0's determinacy standard, subprocess isolation and terminal names |
| `GATE_1_DEFINITIVE.md`, `FINAL_TERMINAL_REPORT.md`, `ATTRIBUTION_REVISION.md` | the sealed Held-out attribution (ratified D1) and the determinacy-bound precedent |
| `src/muru/paper_benchmark/registry.py`, `generator.py`, `rc5_seeds.py`, `seed_band_registry.py` | the condition grid, the generator, the seed derivation and the declared-band mechanism — **all read, none mutated** (§5) |
| `scripts/pb_33_amendment_a3_1_integrity.py`, `scripts/pb_34_rc3_integrity.py` | the byte freeze on `registry.py` and `generator.py` that §5 must not break |
| `SYNTHESIS_DECISION_RECORD.md` §0 | the ordered decision rule R1–R10 that fixed each contested choice |
| `CRITIC_SCIENCE_REENTRY.md`, `CRITIC_GOVERNANCE_REENTRY.md` | the 38 defects this version repairs |

**This protocol licenses nothing by itself.** It defines an instrument. Execution of that
instrument, its adjudicated verdict, **and a protocol-owner ratification of that verdict**
(§21.5) may license.

### 2.1 `G7` / `N6` — authority correction, twice, because the first correction did not survive its own check

`CRITIC_GOVERNANCE` `G7` found Decision 2's authority chain **self-granted**: v2 cited
ratification §10, which authorizes constructing *this* protocol, not an operational
preregistration for an E4 arm ratification §4 (D2-ext) **suspends**; and it cited
`P2_GOVERNANCE_LEAKAGE.md` open items 33/34, whose actual text is *"Declare E4f
non-executable (BC-21)"* — the opposite of what was quoted.

The v3 repair replaced that citation with *"the protocol owner's maximum delegated authority
… exercised under its three stated conditions"*. `CRITIC_GOVERNANCE` `N6` checked that claim
against the repository and it fails on its own terms:

1. **The delegation is in no record.** `grep -rniI "maximum.autonomy|maximum delegat"` over
   the whole repository returns hits **only** in documents this session produced. The one
   document that *is* a governance record — `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md`, whose
   §1 states *"every decision below is the owner's, not the analyst's"* — contains no
   delegation and no mention of E4f. There is no `muru-authority/*` tag for it.
2. **The three conditions are invented.** The forward-run event log's actual authority field
   reads *"Prompt section 2 … + section 2 condition A (before the governed result is
   observed)"* — **one** condition, about ordering. The hostile-review and hash-freeze
   conditions were supplied by §2.1 itself.
3. **The hostile-review condition, even as invented, is unmet.** `design_council/` holds
   `P1_SCIENTIFIC_DESIGN.md`, `P2_GOVERNANCE_LEAKAGE.md`, `P3_STATISTICAL.md`, all scoped to
   *this* protocol. **No E4f hostile review exists anywhere in the repository.**

An authority claim that fails the one check a reviewer can actually perform — does the
record exist? — is not a repair, whatever its content. `N6`'s own minimal repair is taken
directly, in its stated form (b):

```
The authority for the E4f operational preregistration is an OPERATOR INSTRUCTION recorded
only in FORWARD_RUN_EVENT_LOG.jsonl as "Prompt section 2". It is NOT a governance record of
this repository. No hostile review of E4f was performed. Until a protocol-owner record
exists -- signed, scoped, and tagged like the programme's other ten authority tags --

    ratification section 4 (D2-ext)'s suspension of ALL E4 arms governs WITHOUT EXCEPTION.
    Gate R row 3 REVERTS to ROUTE_DETERMINED_ARM_NOT_EXECUTABLE.
    Section 21.2 row 3, section 22 F12/F12a/F12b, and section 32's E4f rows are VOID.
    A certified C+D route assigns ROUTE_DETERMINED_ARM_NOT_EXECUTABLE and proposes nothing.
```

This is the same standard §5.3 already applies, correctly, to Route R-A: an unratified
amendment does not execute merely because an analyst can construct it. `MURU_V2_E4F_
OPERATIONAL_PREREGISTRATION.md` **remains prospectively frozen and unedited** — the moment a
real ratification record exists, it is ready to be re-armed without redoing any of its own
work. Nothing about E4f's own content is retracted; only its **executability today** is.

**This closes `N1` as a side effect, not by choice.** `N1` found Decision 1's own
justification (§0.1 response 1) still asserting that `befca0d` §2.3's disagreement-disclosure
obligation is *"retained in full"* by §21.5, while §21.5 itself (the `G6` repair) makes the
annotation condition nothing — a live contradiction an owner could read either way. With E4f
non-executable, only route `B` (E4a, itself requiring a separate owner re-arming act per
§21.2 row 1's honesty note) can reach an operative licence at all, so the annotation's role is
now uniformly **disclosure only**, exactly as `G6` requires. §0.1 response 1, §21.4's bullet
4, and §32.1's `"→ §21.5 explanation required"` are corrected below to say that once, not
argued twice in two directions.

## 3. WHAT THE OLD E2a FAILURE MEANS

Unchanged from v1 except where the critics required a correction. It means three separate
things and they must not be conflated.

1. **A composition failure (primary).** E2a is a balanced factorial — 5 truth families at
   20% each, 3 coefficient regimes, 3 noise levels. Held-out G2 is 75% `mass_affine`, 8.3%
   each saturating / interaction / exponential, and **zero `mass_power`**; and its noise is
   a *condition axis* at 1/12 weight, not a crossed factor at 1/3 weight. E2a's
   `mass_power` stratum is 107/107 `SUCCESS` and has no descriptor truth at all.
   *(Disclosure required by `S16`: the quantitative statement v1 made here — that
   direct-standardising E2a to the Held-out truth-family mix removes 68.1% / 77.0% of the
   divergence — was computed in a document that had `pi_0` in hand. It is retained as a
   fact and is **not** the argument for the population. The argument for the population is
   §5's provenance argument, which cites `registry.py` and no outcome, and which §30 attack 1
   requires an independent agent, **blind to this paragraph**, to re-derive before freeze.)*
2. **A condition-coverage failure (decisive for what must be built).** E2a instantiated
   **none** of the twelve prospectively declared Held-out G2 conditions. It has no
   missingness condition (F04), no boundary-scale condition (F05), no
   irrelevant-distractor condition (F11), no correlated-distractor condition (F12), and no
   **equivalent-symbolic-forms** condition (F17) — the condition whose frozen registry
   purpose is *"canonicalize equivalent laws"* and whose expected behaviour is *"score
   equivalent forms once"*, i.e. the one condition purpose-built to stress the cross-seed
   identity contract. **The live routing question is retention versus cross-seed identity.
   No admissible corpus contains an identity-stressor condition.** This is the reason — the
   only reason — a new surface is required, and it cites `registry.py` and no outcome.
3. **An instrument failure (real, quantified, and NOT the explanation).**
   `lazy_classify.py:186` returns `False` whenever `canonicalization_status != "OK"`, so a
   wall-clock `SIMPLIFY_TIMEOUT` is consumed as evidence of absence, monotonically toward
   `NEVER_ON_FRONT`.

   **Two corrections required by `S22` and made here.**
   (a) The **operative cap** is not `signal.alarm(5)`; it is the parent-side
   `conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` at `e2_classify.py:338`, which **also absorbs pipe
   and worker failures under the same `SIMPLIFY_TIMEOUT` name**. Some of the 397 cached
   `SIMPLIFY_TIMEOUT` records may therefore not be simplify timeouts at all.
   (b) The **stage-A figure is sound** (`DINST_HOSTILE_REVIEW.md` D8: 0 of 42,411 A-world
   rows are absent from the classify cache), but the accompanying **B / C / E contamination
   figures are inferred UPPER BOUNDS, not observations**, because 48,790/70,322 B rows,
   31,781/35,988 C rows and 36,525/40,746 E rows are absent from the cache entirely. They
   are labelled as upper bounds wherever they appear in this document and in any report of
   it.

   The determinacy consequence stands and is unaffected by (a) and (b): every retained row
   of every one of the 539 worlds is determinately labelled, retention is label-independent
   and already persisted, so `n_retained_correct` cannot move, the corrected bound is
   `A ∈ [49,122]`, `B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`, and the frozen
   Gate-2 predicate is **invariant** across all of it.

**What the failure does NOT mean.** It does not mean the sealed Held-out attribution
licenses anything. E2b remains `DECISION_INADMISSIBLE`. It does not mean agreement with
Held-out qualifies a surface — `befca0d` §2.3's first two paragraphs are **destructive-only**
and attach no positive force to agreement.

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
  is too weak to establish fidelity (P2 §2.6, accepted). **Under Decision 1 this claim is
  now consistent end to end**: v1 disclaimed behavioural resemblance in §4 and then required
  it in §21.3 as a necessary condition of every licence. That contradiction is gone.
- that an x86 search would have produced the Held-out fronts. Cross-architecture **search**
  equivalence is unestablished (`worlds_executed_on_this_host: 0`) and this protocol makes
  **no cross-architecture numeric claim anywhere**. (v1 excepted its §21.3 veto; there is no
  such veto now.)
- any claim about Held-out. **Every licence proposed under this protocol is scoped to the
  regime characterised by the surface's own published descriptor vector, never to
  "Held-out".**

### 4.1 Formal non-circularity properties this design exhibits

| # | Property | How it is checked |
|---|---|---|
| i | **Provenance separation** | Gate Q reads `registry.py`, `generator.py`, `rc5_seeds.py` and the v1-sealed truth-blind taxonomy. It reads **no E2b artifact**. Enforced by the same static data-flow checker §2.3 mandates for the citation checker. **Honest qualification required by `S16`:** the Gate Q *predicate* reads no E2b artifact; the population's *composition rule* was selected in a document that had access to `pi_0`. The provenance argument is independent but was not independently generated. §30 attack 1 must generate it independently before freeze |
| ii | **Zero magnitudes in qualification** | The qualification criterion (§18/§20) is a conjunction of **binary** construction and control checks. It contains no numeric threshold that could be moved. This is now true without exception: v1's `g_max = 0.010` — the one numeric knob inside `QUALIFIED` — is deleted (§0.4) |
| iii | **No channel from E2b to the terminal state at all** | Under Decision 1 the comparator enters only as the §21.4 annotation, which is computed **after** the routing verdict is hash-sealed, is applied **identically to all three routes**, and is mechanically incapable of changing any terminal. v1's weaker per-arm monotonicity property is superseded |
| iv | **Order enforcement, mechanical** | Gate R's verdict is hash-sealed and appended to a hash-chained event log in a commit that is a **strict ancestor** of the first commit containing any comparator artifact. `git merge-base --is-ancestor`. **This guarantees artifact order, not information order** (`S13`) — `pi_0` is printed in the public ratification record and in this document — and is claimed only as artifact order |
| v | **Non-determination, PROVEN CONSTRUCTIVELY rather than measured** | See below |

**Property (v), and why v1's version was deleted.** v1 required `QND_PASS`: *enumerate
stratified subpopulations of E2a's sealed corpus that would pass Gate Q's measurable clauses
and verify the routing verdict is not constant across them.* `CRITIC_SCIENCE` D2 and
`CRITIC_GOVERNANCE` S9 both proved the enumeration set is **empty**: Gate Q's Q1 requires the
registry's twelve G2 conditions at equal weight and 138 completed worlds per cell, and this
protocol's own §3 item 2 states that **E2a instantiates none of the twelve conditions**;
E2a's largest cell holds 12 worlds; E2a carries no `partition` field. Read literally,
`QND_PASS = FALSE` over an empty family and the protocol **forbids its own execution**; read
as "no counterexample found", it passes vacuously and tests nothing. Neither reading is
acceptable, and the clause was load-bearing in `QUALIFIED`.

**`QND_PASS` is therefore DELETED from `QUALIFIED`, and this document says so plainly.**
The property worth having is not "the verdict varies across E2a subpopulations" — E2a cannot
supply one. It is: **does Gate Q determine the route?** That is a question about the *map*,
not about a corpus, and it is decidable at zero compute:

> **`NON_DETERMINATION_PROVEN` (NDP).** Exhibit, for **each** admissible route, a concrete
> distribution over `(A, B, C+D, E)` that (a) satisfies **every** clause of Gate Q by
> construction and (b) routes to that route under §21. If such witnesses exist for more than
> one route, Gate Q does not determine the route, and qualification is not routing.

The witnesses are exhibited, with integer per-condition counts and verified arithmetic, in
**§32.1**. NDP is discharged **in this document**, and a frozen script re-verifies each
witness against each Gate Q clause and against the §21.1 certification predicate at freeze
time. If any witness fails re-verification, the protocol does not freeze.

This is strictly stronger than v1's clause in the only way that matters — it is
**decidable** — and strictly weaker in one way that is disclosed: it proves Gate Q does not
*determine* the route; it does not prove Gate Q fails to *bias* it. No available construction
proves the latter, and this protocol does not claim it.

## 5. POPULATION — AND THE BYTE FREEZE

### 5.1 The freeze `CRITIC_GOVERNANCE` S2 found, verified independently here

v1 §5 proposed to set, in `src/muru/paper_benchmark/registry.py`:

```
PARTITIONS            = ("development", "held_out", "challenge", "calibration")
PARTITION_CASE_COUNTS = {..., "calibration": 108}
```

and asserted that *"the frozen modules are byte-pinned by `pb_30`/`pb_33`/`pb_34`"*,
referring to `rc5_seeds` and `seed_band_registry`.

**Verified on this host, and S2 is correct. The citation was inverted.**

```
$ grep -n "PROTECTED_PATHS" scripts/pb_33_amendment_a3_1_integrity.py
43:PROTECTED_PATHS = [
44:    "src/muru/paper_benchmark/registry.py",
45:    "src/muru/paper_benchmark/generator.py",
    ... 9 more src paths, 5 artifacts/*.json manifests ...
      byte-identity enforced against A2.1 commit 80a78032ac601466b35e9dce3fa56f6ae215605f

$ grep -n "A2_1_PROTECTED_PATHS" scripts/pb_34_rc3_integrity.py
40:A2_1_PROTECTED_PATHS = [ "src/muru/paper_benchmark/registry.py", ... ]

$ grep -rn "rc5_seeds|seed_band_registry" scripts/pb_*.py
scripts/pb_50_build_global_science_plan.py:44,58     (code-provenance record)
scripts/pb_rc5_a3_5_authorized_delta.py:229,240      (authorized-delta ledger)
    -- NO hit in pb_30, pb_33 or pb_34.
```

`registry.py` and `generator.py` **are** byte-protected. `rc5_seeds.py` and
`seed_band_registry.py` **are not** in any `pb_30/33/34` protected list.

Both integrity scripts pass **today** (`pb_33` → `A3.1 INTEGRITY VERIFIED`; `pb_34` →
`RC3 INTEGRITY VERIFIED`), so any drift introduced by this protocol would be attributable to
this protocol.

**Frozen authority already states the correct route, verbatim, in the repository.**
`src/muru/paper_benchmark/rc5_seeds.py`, module docstring:

> *"**Why a new module.** A3.5 implementation obligation 9: A3.5's constants MUST live in a
> new module importing the frozen ones, because `rc3_provenance.py`, `registry.py` and
> `analysis.py` are byte-pinned by `pb_30`/`pb_33`/`pb_34` and the RC4.2 `AUTHORIZED_DELTA`
> ledger is a closed 8-entry tuple. Nothing here mutates a frozen module."*

v1's §5 sentence was a garbled paraphrase of exactly this docstring, with the subject and
object exchanged. The docstring is the precedent, it is frozen, and it prescribes the route
this protocol takes.

**Three further reasons the v1 edit was not merely unauthorised but wrong.**

- `PARTITION_CASE_COUNTS` is **the same dict object** passed as `partition_counts` to all
  twenty `FamilySpec` literals (`registry.py:121,157,169` and the `_family` helper at
  `:118`). Adding `"calibration": 108` would declare 108 replicates for **all twenty**
  families = 2,160 cases, not the 1,512 v1 searched, and `iter_case_ids("calibration")`
  would emit 648 case ids for the six families v1 lists as "not searched" — breaking
  precondition `P1`. `S19`'s substance is confirmed; its stated mechanism ("twenty more
  places") is **incorrect** and is corrected here: there is one shared mapping, not twenty.
- `rc5_seeds.A35_TOTAL_CASES` is computed **dynamically** as
  `sum(len(list(iter_case_ids(p))) for p in PARTITIONS)`. Adding a partition changes it from
  380 to 2,540, which changes `A35_SEARCH_SEED_MAX` and therefore the envelope of the
  declared band `a3_5_case_search_reserved`, which `seed_band_registry` checks for overlap.
- Three frozen test files assert `PARTITION_CASE_COUNTS == {"development": 4,
  "held_out": 12, "challenge": 3}` exactly.

### 5.2 ROUTE R-B (PRIMARY) — a new module, zero protected bytes touched, equivalence demonstrated

The calibration population is declared **entirely outside** `registry.py` and `generator.py`,
in **two new files** that are in no protected list and that import the frozen modules
read-only:

```
src/muru/paper_benchmark/calibration_surface.py     (NEW)
src/muru/paper_benchmark/calibration_seed_band.py   (NEW)
```

**Case-id namespace.** Calibration case ids carry the prefix `PBC`, not `PB`:

```
PBC|calibration|<family_code>|r<replicate:03d>
```

`registry.resolve_case_id` rejects any id whose first field is not `"PB"`, so the frozen
resolver **cannot** be fed a calibration id, and no existing `case_ordinal`, seed or manifest
can move. Because `generator.derive_seed` hashes the full case-id string, the `PBC` prefix
also guarantees the calibration draw is **statistically independent** of every `held_out`,
`development` and `challenge` draw at the same family and replicate index.

**Population declaration** (module constants in `calibration_surface.py`, not in the
registry):

```
CALIBRATION_REPLICATES = 138

# DEF-M7: DERIVED from a predicate over the frozen registry, not hand-transcribed.
# v2 declared these as literals under a citation that points at eighteen families.
CALIBRATION_G2_FAMILIES  = every family all of whose variants declare
                           symbolic_truth_kind == "defined"
                        -> ("F01","F02","F03","F04","F05","F08",
                            "F09","F10","F11","F12","F17","F18")   # 12, verified
CALIBRATION_NEG_FAMILIES = every family all of whose variants declare
                           "false_null_structure" OR symbolic_truth_kind == "mass_only"
                        -> ("F07","F19")                            #  2, verified
# the other six registry families (F06, F13-F16, F20) receive NO calibration case ids,
# because they declare no symbolic truth at all (symbolic_truth_kind == "none",
# scalar_truth_defined == False, no g_recovery endpoint).
#
# The module ASSERTS that the derived tuples equal the intended ones and refuses to
# import if the registry ever drifts, so the population cannot change silently.
```

| Stratum | Families | Replicates | Worlds | Role |
|---|---|---:|---:|---|
| **G2 (primary)** | F01,F02,F03,F04,F05,F08,F09,F10,F11,F12,F17,F18 | 138 | **1,656** | primary endpoint |
| **NEG (control)** | F07 (mass-only truth), F19 (null worlds, 3-variant cycle) | 138 | **276** | false-structure safety; supplies the E6 opportunities (§21.5) |
| not enumerated | F06, F13–F16, F20 | 0 | 0 | not G2-relevant |

**Total searched: 1,932 worlds × 30 seeds = 57,960 searches.**

**Generation.** `calibration_surface.generate_calibration_case(case_id)` resolves
`(family, variant, replicate)` from the frozen `registry.CASE_FAMILIES` and
`FamilySpec.variant_for_replicate` (imported, unmodified — F19's `("F19A","F19B","F19C")`
cycle is the registry's own), and then executes **the identical generative body as
`generator.generate_case`**, calling the frozen `_synthetic_compounds`, `_rng`, `_law`,
`_response_matrix`, `derive_seed`, `scientific_payload_hash` and `TruthRecord` with no
change of any kind. `generate_case` uses `resolve_case_id` **only** to obtain
`(family, variant)`; everything downstream is a pure function of the case-id string and that
pair. The new module changes the resolver and nothing else.

**Mandatory equivalence control `C-0`, and its result, obtained before freeze.**
Duplicating twenty lines of a frozen generator is a risk, so it is discharged
**exhaustively** rather than argued:

```
for every one of the 380 frozen case ids:
    generate_calibration_case_body(cid, *registry.resolve_case_id(cid)).content_hash
        ==  generator.generate_case(cid).content_hash
```

**Executed on this host during authorship (disclosed in full, §31.8): 380/380 identical,
0 mismatched, 5.3 s.** In addition:

```
registry.resolve_case_id("PBC|calibration|F17|r000")
    -> ValueError: invalid case id: PBC|calibration|F17|r000      [frozen resolver rejects]
generate_calibration_case("PBC|calibration|F17|r000")
    -> partition="calibration", mathematical_family="mass_affine_descriptor",
       1,080 trajectory rows, content_hash cbc38b51add1e7a5...
derive_seed("PBC|calibration|F17|r000","compounds") =  9218284394062082508
derive_seed("PB|held_out|F17|r000","compounds")     = 16635993092838667630   [independent]
FamilySpec("F19").variant_for_replicate(r) for r in 0..5
    -> ['F19A','F19B','F19C','F19A','F19B','F19C']                [cycle preserved]
```

`C-0` is re-run mechanically at preflight and at seal time and its result is recorded in the
manifest. **`C-0` fails ⟹ Route R-B is abandoned and Route R-A is attempted (§5.3). No
world is generated under a failing `C-0`.**

**Seed band — new module, frozen rule, derived value, zero frozen bytes touched.**

```
CALIBRATION_SEARCH_SEED_BASE = rc5_seeds.A35_SEARCH_SEED_MAX + 1   # computed, never a literal
CALIBRATION_SEEDS_PER_CASE   = rc5_seeds.A35_SEEDS_PER_CASE        # = 30, imported
search_seed(calibration_ordinal, k) = CALIBRATION_SEARCH_SEED_BASE
                                    + calibration_ordinal * 30 + k
    calibration_ordinal in [0, 1932)   # family-major over the 14 declared families,
                                       # then replicate, fixed by the new module
    k in [0, 30)
```

Evaluated at this commit: `A35_SEARCH_SEED_MAX = 2_100_011_399`, so the band is
`[2_100_011_400, 2_100_069_359]` (57,960 integers). The declared bands verified at this
commit are

```
phase3_discovery                       [       900000, 1678621529]
falsification_calibration_v1           [   1680000000, 1680999999]
falsification_calibration_v2           [   1690000000, 1690999999]
objval_plan2                           [   1700000000, 2099999929]
rc3_engineering_smoke                  [   1900000000, 1900999999]
a3_5_case_search_reserved              [   2100000000, 2100011399]
a3_1_a3_2_structural_null_calibration  [   2110000000, 2146999929]
SIGNED_32BIT_MAX = 2147483647 ;  unacknowledged_overlaps() = []
```

so the new band sits in the 9,988,600-integer gap between `a3_5_case_search_reserved` and
`a3_1_a3_2_structural_null_calibration` and is disjoint from all seven. **The base is set by
a registered rule and derived from it — never chosen** (P2 T-a/T-b/BC-3).
Disjointness is checked by the frozen registry's **own** checker,
`seed_band_registry.find_overlaps(DECLARED_BANDS + (CALIBRATION_BAND,))`, evaluated on a
tuple constructed at runtime in the new module.

> **`NO-BAND-COLLISION`, stated exactly, because v2 stated it wrongly and it was fatal.**
> v2's Gate Q clause required the result of `find_overlaps` to be **empty**. It is never
> empty. The frozen registry carries **one pre-existing, disclosed, acknowledged** collision:
>
> ```
> find_overlaps(DECLARED_BANDS)
>     -> [Overlap(band_a='objval_plan2', band_b='rc3_engineering_smoke',
>                 lo=1900000000, hi=1900999999)]
> unacknowledged_overlaps()
>     -> []
> ```
>
> So v2's Q1 failed **unconditionally, on every dataset**, `QUALIFIED` was unreachable, and
> §22 F2 fired `BENCHMARK_INTEGRITY_DEFECT` — publishing a **false claim that the benchmark
> needs auditing**, caused purely by naming the wrong function. That is precisely the harm
> `D8` describes, and v2's own §5.2 evidence block displayed the output of the *other*
> function. This was `CRITIC_SCIENCE` `DEF-C1` and it killed v2 exactly where v1 died: at the
> conjunction of the reachability proof.
>
> **The predicate is therefore about the calibration band and nothing else:**
>
> ```
> NO-BAND-COLLISION :=
>     [ o for o in find_overlaps(DECLARED_BANDS + (CALIBRATION_BAND,))
>           if 'v2_calibration_surface' in (o.band_a, o.band_b) ]  ==  []
>   AND  unacknowledged_overlaps()  ==  []      # the frozen registry's own health check,
>                                               # unchanged, still required to pass
>   AND  CALIBRATION_SEARCH_SEED_MAX <= SIGNED_32BIT_MAX
> ```
>
> This is **stricter**, not laxer, than what v2 meant: it additionally requires the frozen
> registry's own acknowledged-collision invariant to hold, and it makes the calibration
> band's own cleanliness a separate, checkable conjunct. Evaluated at this commit it returns
> `[]`, `[]`, `True` — verified, not asserted. **`DECLARED_BANDS` is not mutated**, because
`seed_band_registry.py` is pinned by the closed RC5 authorized-delta ledger and a further
edit would be unauthorised drift under exactly the rule that ledger enforces.

**What R-B does NOT do, stated so it cannot be read as a workaround.** It does not add a
partition to the benchmark. `iter_case_ids("calibration")` raises, as it should; the
benchmark's case population remains the frozen 380; `pb_33` and `pb_34` continue to verify.
The calibration surface is a **separately declared population that reuses the benchmark's
frozen generative machinery**, in the manner `rc5_seeds.py` itself declares mandatory. It is
**not** a benchmark partition and this document never calls it one outside the `partition`
string the generator writes into each `TruthRecord`.

### 5.3 ROUTE R-A (DECLARED ALTERNATIVE, requires the protocol owner) — an authorized-delta amendment

If `C-0` fails, R-B is abandoned and R-A is attempted **once**. R-A amends `registry.py`
through the repository's own established, twice-used mechanism: a closed, hash-pinned
authorized-delta ledger (`scripts/pb_rc4_2_authorized_delta.py`,
`scripts/pb_rc5_a3_5_authorized_delta.py`; consumed by `pb_33` via
`ALL_AUTHORIZED_BY_PATH`), binding the exact path, the exact pre-change SHA-256, the exact
post-change SHA-256 and a one-line statement of the allowed semantic scope.

R-A requires **all** of:

1. A **protocol-owner ratification record** authorizing the amendment of a byte-protected
   benchmark file. Neither ratification §10 nor any other cited document currently grants
   this; §10 authorizes *constructing a protocol*, not amending the benchmark.
2. A new ledger module `scripts/pb_e7_calibration_authorized_delta.py` with the exact
   old/new hashes of `registry.py`.
3. `partition_counts["calibration"]` declared **per family** — 138 on the fourteen searched
   families, **0** on the other six — which requires replacing the shared
   `PARTITION_CASE_COUNTS` object with per-family mappings and updating the three frozen
   test files that assert its literal value. Each such change is a further ledger entry.
4. `pb_31`, `pb_32`, `pb_33`, `pb_34`, `pb_35` all returning **0 errors after** the
   amendment, and `rc5_seeds.verify_search_seed_invariants()` passing, and all 380
   pre-existing `case_ordinal` values and all 11,400 pre-existing search seeds **byte-equal**
   before and after.

**Clause added to Gate Q `Q1` and to precondition `P9` (`S2`'s minimal fix, adopted):**
*"`pb_33` and `pb_34` return 0 errors after any population construction, and every protected
path is either byte-identical to its freeze baseline or matched exactly by a registered
authorized-delta entry."* Under R-B this clause is satisfied trivially, because no protected
path changes. Under R-A it is satisfiable only with the ledger and the owner's record. **The
clause is stated so that Q1 and P9 can no longer pass while a byte freeze is broken** —
v1's ordinal-stability preflight checked ordinal *values*, not file *bytes*, and would have
passed with the content freeze broken.

### 5.4 If both routes fail

There is **no `development ∪ challenge` fallback.** v1 pre-declared one; `CRITIC_SCIENCE` D8
showed it supplies 4 + 3 = 7 replicates per condition against Q1's required 138, so it
**fails Q1 and P1 with certainty**, and v1's failure rule F5 would then have emitted the
claim *"the benchmark needs auditing before anything else proceeds"* — a **false diagnosis
of a benchmark defect caused by a protocol drafting error**. It also carries a contamination
caveat that v1 conceded while proposing to use it inside a licensing instrument.

Instead, the ladder terminates honestly:

```
C-0 fails                                 -> attempt R-A
R-A refused by the owner, or R-A fails    -> terminal NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT
Q1 fails for a mechanical reason under a route that was otherwise available
   (ordinal drift, band collision, GENERATOR_VERSION mismatch, C-0 mismatch)
                                          -> terminal BENCHMARK_INTEGRITY_DEFECT
```

The two are **different findings** and are named differently. Only the second asserts
anything about the benchmark.

### 5.5 Binding population properties

- Same generator (`paper_benchmark/generator.py`), same `GENERATOR_VERSION`, same
  `ROOT_SEED = 20260813`.
- Different case-id namespace ⟹ different `derive_seed(case_id, ·)` ⟹ statistically
  independent compounds, laws, responses and missingness draws.
- **Nothing in this protocol ever touches, reads, or re-runs a `held_out` or `challenge`
  case.** Enforced by a static import check plus a corpus-path allowlist (P2 BC-23).
- **Ordinal-stability preflight (hard gate, Q1 clause).** Recompute all 380 pre-existing
  `case_ordinal` values **and all 11,400 pre-existing search seeds** before and after
  population construction and require **byte equality**. Under R-B this is guaranteed by
  construction (nothing is touched) and is still executed, because a guarantee that is not
  checked is a promise.

## 6. GENERATIVE FACTORS

**REUSED VERBATIM.** The generative factors are the benchmark's own, exactly as
`paper_benchmark/generator.py` implements them for the `held_out` partition. There is **no
new factorial and no sweep.**

| Factor | Setting | Basis |
|---|---|---|
| Condition | the registry's 12 declared G2 conditions, equal weight `w_k = 1/12` | `registry.py`, prospectively declared, results-blind, long before any E2 |
| Truth law | drawn by `generator._law` for that condition | frozen |
| Compound / descriptor draw | `derive_seed(case_id, ·)` | frozen |
| Missingness | the condition's own declaration (F04) | frozen |
| Distractors | the condition's own declaration (F11, F12) | frozen |
| Equivalent-form presentation | the condition's own declaration (F17) | frozen |

**Rationale (decision record §7, R5 + R6).** A crossed sweep is a different experiment
(E4e's question). E2a's three coefficient levels all sit inside the frozen
`rng.uniform(0.25, 0.55)` the benchmark already uses, so the sweep bought no regime coverage
while destroying composition match. Reproducing "the Held-out regime" means reproducing its
**distribution**, not a lattice inside it.

## 7. FAMILY COVERAGE

Truth-family composition follows the registry and therefore reproduces the Held-out mix
exactly, **by construction rather than by reweighting**:

```
affine       9/12   (F01,F02,F03,F04,F05,F08,F11,F12,F17)
saturating   1/12   (F09)
interaction  1/12   (F10)
exponential  1/12   (F18)
mass_power   0/12   -- absent from the target and therefore absent from the primary
```

- **`mass_power` is absent from BOTH strata, not "moved to the NEG stratum".** v1 §7 said it
  *"moves entirely to the NEG control stratum"*; `CRITIC_SCIENCE` D12 showed this is false —
  `mass_power` is an E2a construct, not a registry family, and the NEG stratum is `F07`
  (`"mass-only g truth"`, `registry.py:141`) and `F19` (null worlds). **Precondition `P7` is
  therefore satisfied by construction, not by exclusion**, and this protocol claims no
  `mass_power` coverage. It also means the surface says nothing about the family behind the
  four-times-OOM-killed poison world, and that is disclosed here rather than discovered
  later.
- **Cell-level shortfall is an admissibility failure, not something standardisation fixes.**
  Every one of the 12 G2 cells must carry exactly `R = 138` completed worlds (§20 `P1`).
- **E3's completed verdicts bind and are declared now, before the numbers exist** (P2 BC-22,
  P3 C5), verified by direct read at `git show 1d20731:E3_RESULTS.md:76-78`:
  `mass_affine_descriptor` bic_rate **0.553 MARGINAL**, `mass_exponential_descriptor`
  **0.527 MARGINAL**, both with `search_side_attribution_licensed: false`;
  `mass_saturating_descriptor` **0.820 IDENTIFIABLE**; `mass_interaction` **1.000
  IDENTIFIABLE**. Since 10 of the 12 conditions carry MARGINAL-family truth, **a substantial
  `NEVER_ON_FRONT` share is expected and is licensed in advance by E3**, and may not later be
  re-read as a novel pipeline generation failure.

## 8. COEFFICIENT REGIMES

**REUSED VERBATIM: the frozen benchmark draw. There is no coefficient ladder and no sweep.**
The coefficient is drawn per world by `generator._law` from `rng.uniform(0.25, 0.55)`,
exactly as every Held-out case carries it. E2a's fixing of the coefficient to
`{0.25, 0.40, 0.55}` was itself a departure from the target regime and is not reproduced.
The realised coefficient is persisted per world and reported per-regime tertile as a
**diagnostic only** (§19 D4), preserving `befca0d` §2.6's frozen *"per family and per
coefficient regime"* stratification without promoting it to a factor.

## 9. NOISE REGIMES

**REUSED VERBATIM: the benchmark's own noise design, which is a CONDITION AXIS, not a
crossed factor.**

```
F01 noiseless          1/12 weight
F02 moderate noise     1/12 weight
F03 stronger noise     1/12 weight
F04..F18 (9 conditions) the generator's default for that condition
```

**Recorded consequence, fixed before execution.** Decision record §1.4 establishes that
conditioning on noise level flips the standardised E2a argmax on a 0.23 pp margin. Under
this protocol **the primary is computed on the full G2 population and is never conditioned
on noise**; noise-conditioned readings are diagnostics (§19 D5) and may not change any
verdict. The conditioning set is fixed here so it cannot be chosen after the counts exist.

## 10. REPLICATE COUNT AND SAMPLE SIZE — RE-DERIVED

**138 replicates per condition ⟹ `n = 1,656` G2 worlds. DERIVED. Full derivation below.**

### 10.1 The margin

```
delta = 10 / 144 = 0.0694444...
```

**Source, and its honest classification.** PE2-4 (`befca0d`
`MURU_V2_G2_PARETO_STUDY_DESIGN.md` line 466, verified by direct read):
*"E2b reproduces the decomposition's retention-versus-generation split to **within 10 cases
of 69/57**."* `f4c1105` §4 GATE 1: *"contradicts ... by more than 10 cases (PE2-4's own
tolerance)"*. `GATE_1_DEFINITIVE.json`: `FROZEN_THRESHOLD = "more than 10 cases (strict >)"`,
applied to `RETENTION_DEVIATION` and `GENERATION_DEVIATION` — **absolute deviations of two
class counts on a two-way split with denominator 144**.

**`10/144` is a DERIVED quantity in this protocol, not a verbatim reuse** (`S5`, adopted).
v1 listed it under "reused verbatim", which exempted the two most consequential uses of the
number from the derivation discipline the header imposes on everything else. The derivation
is stated once, here, and the entry moves to §33's DERIVED table:

> **Derivation.** The frozen quantity is *"a difference of more than 10 cases between two
> class counts on a 144-case denominator is material."* Ported to a proportion per P2 BC-16
> (silently reusing the literal count 10 against a different `n` would itself be threshold
> tuning), it reads: *a difference of more than `10/144` between two classes' shares is
> material.* This protocol applies it to **one** quantity: the lead `pi_top - pi_second`
> between two cells of the same four-cell partition. **Direction of generalisation:** from a
> two-way split to a four-way partition. The generalisation is **conservative for the
> routing decision** — it demands a lead at least as large as the frozen bar between two
> classes that are, in a four-way partition, each smaller than the two-way classes the bar
> was set on, so the required *relative* separation is larger, not smaller.
> **v1 also applied it to a total-variation distance over all four cells (Gate V). That use
> is deleted with Gate V (Decision 1) and is not reintroduced.** The §21.4 annotation reports
> TV against `delta` **as a reference scale only**, gating nothing.

The alternative candidate margin `delta_dec = 0.5*(pi_C - pi_B) = 0.0556` remains
**rejected**, because it is computed from the sealed Held-out attribution and would import
comparator evidence into the sizing of a licensing instrument (**R3**).

### 10.2 The critical value — corrected

v1 used a one-sided `z_.95 = 1.6448536` on `pi_top - pi_second`. `CRITIC_SCIENCE` D4 showed
this is wrong: `pi_top` and `pi_second` are **selected by the data** (§21.1), so a one-sided
bound on a data-selected contrast between two of three cells is a two-sided comparison read
one-sided. Fixed-sequence gatekeeping controls the qualification→routing ordering; it does
nothing about selection *within* the routing step. The critic measured, and I reproduce
independently at 200,000 multinomial draws:

| True configuration | `P(certify)` under v1's rule, `n = 1296`, `z_.95` | nominal |
|---|---:|---:|
| exact 3-way tie `A = B = C+D` | 0.034 – 0.036 | 0.05 |
| **2-way tie `B = C+D = 0.43`, `pi_A = 0.12`** (v1 §34's own prediction) | **0.100** | 0.05 |

**The corrected critical value is `z_.975 = 1.9599640`.** v1 §27's claim that no adjustment
is needed "as a theorem rather than a convention" was false for the routing step and is
withdrawn (§27).

### 10.3 The certification rule, and the materiality repair

`CRITIC_GOVERNANCE` S6: v1 certified on `LCB > 0` alone, so the operative materiality bar was
**implicit in `n`** and drifted with it (0.99 `delta` at `n = 1296`, 0.81 `delta` at v1's
pre-declared top-up `n = 1944`). Raising `n` was therefore lowering the effective margin,
which §10's own standing preference forbids. The repair is adopted:

```
ROUTING_CERTIFIED  :=  argmax over { pi_A , pi_B , pi_C+D } IDENTICAL under rho_bot, rho_top
                       AND  ( pi_top - pi_second )  >=  delta            [MATERIALITY - frozen]
                       AND  LCB_97.5( pi_top - pi_second )  >  0         [PRECISION  - derived]
```

The materiality clause is now **explicit, frozen, and independent of `n`**. The top-up that
S6's fix was needed to make safe is deleted anyway (§0.4), but the repair is kept because it
is correct on its own terms.

### 10.4 The sample size

v1's sizing criterion is preserved **verbatim** — *80% power to certify a true lead of
`delta` against the precision clause* — with only the critical value corrected.

> **`DEF-M1` — what `n = 1656` is DERIVED from, stated correctly.** The criterion above is
> attainable only against the **precision** clause. The **composite** rule
> `ROUTING_CERTIFIED` also requires the *observed* lead to reach `delta`, and at a true lead
> of exactly `delta` the observed lead falls short **half the time**, so composite power at
> exactly `delta` is bounded near **0.499 at every `n`** — a fact §10.5 already reports and
> which no sample size can repair. Calling `n` "DERIVED from 80% power at a lead of `delta`"
> without that qualifier, as v2's §33 did, describes a target the protocol proves unreachable.
>
> **Restated:** `n = 1656` is DERIVED from *"80% power **against the precision clause** at a
> true lead of `delta`"*. Against the composite rule its operating characteristic is the §10.5
> table, whose relevant entries are pre-recorded here and not renegotiable after execution:
>
> ```
> true lead = 1.0 delta   ->  composite power ~ 0.499   (bounded by the observed-lead clause)
> true lead = 1.5 delta   ->  composite power ~ 0.87
> true lead = 2.0 delta   ->  composite power ~ 0.99
> ```
>
> This is a **disclosed limitation, not a defect**: the design is well powered against leads
> materially above `delta` and is deliberately near-coin-flip exactly **at** the materiality
> boundary, which is the conservative direction for a licensing instrument. `CRITIC_SCIENCE`
> reached the same verdict — *"acceptable as disclosed"* — and objected only to the label. The
> label is fixed. Using the
distribution-free bound `pi_1 + pi_2 <= 1` so that no comparator quantity enters the sizing:

```
Var(pi_1 - pi_2) = ( pi_1 + pi_2 - (pi_1 - pi_2)^2 ) / n   <=   ( 1 - delta^2 ) / n

( z_.975 + z_.80 ) * sqrt( (1 - delta^2) / n )  <=  delta

n >= (1 - delta^2) * (z_.975 + z_.80)^2 / delta^2
   = 0.99517747 * (1.9599640 + 0.8416212)^2 / 0.0694444^2
   = 0.99517747 * 7.84887973 / 0.00482253
   = 1619.6948
```

**`R >= 134.98`. The smallest admissible replicate count is `R = 138`, giving `n = 1,656`.**
`R` must be divisible by **6**: by 3 so that F19's `(F19A,F19B,F19C)` variant cycle is
balanced **within each DEV/EVAL half** (`R/2` divisible by 3), and by 2 so the §26 secondary
split is exact. `R = 135` satisfies neither; `R = 136` is divisible by 2 but not 3 (this is
why `CRITIC_SCIENCE` D4's suggested `n = 1632 = 12 x 136` is not admissible under v1's own
lattice rule, which this protocol retains); `R = 138 = 6 x 23` is the smallest admissible
value. Among admissible values the lexicographically simplest is taken, per the tie-break
rule.

**Compare v1: `n` rises from 1,296 to 1,656 (+27.8%). `delta` is unchanged.** The standing
preference — *"if the design proves underpowered, raise `n`; do not lower the margin"* — is
honoured in the only direction it permits.

### 10.5 Resolving power and the full operating characteristic, recorded before execution

v1 published a resolving-power table that does not reproduce from its own formula; every
entry was optimistic and the entries were not even mutually consistent with a single
alternative assumption (`D11`, `S15`). **Republished, recomputed from
`d = sqrt(K/(n+K))`, `K = (z + z_.80)^2`, under the protocol's own declared bound
`pi_1 + pi_2 <= 1`:**

| `n` | min lead detectable at 80% power, `z_.95` (v1's rule) | in `delta` | min lead detectable at 80% power, **`z_.975` (this rule)** | in `delta` |
|---:|---:|---:|---:|---:|
| 252 | 0.1547 | 2.23 | 0.1738 | 2.50 |
| 576 | 0.1031 | 1.48 | 0.1159 | 1.67 |
| 1,296 (v1) | 0.0689 | 0.99 | 0.0776 | 1.12 |
| **1,656 (this protocol)** | 0.0610 | 0.88 | **0.0687** | **0.989** |
| 1,944 | 0.0563 | 0.81 | 0.0634 | 0.91 |

`n = 1,656` is thus the smallest admissible size at which a lead of exactly `delta` is
detectable at 80% power **under the corrected critical value** — the same property `n = 1296`
had under the wrong one.

**The full operating characteristic of the composite rule, which v1 never published.**
Adding the materiality clause changes the operating characteristic, and the change is
disclosed rather than absorbed. Verified at 100,000–200,000 multinomial draws per point,
`n = 1,656`:

| Configuration | `P(ROUTING_CERTIFIED)` |
|---|---:|
| exact 3-way tie `A = B = C+D` | **0.0001** |
| 2-way tie `B = C+D = 0.43`, `pi_A = 0.12` | **0.0024** |
| true lead = 1.00 `delta` | 0.499 |
| true lead = 1.10 `delta` | 0.619 |
| true lead = 1.25 `delta` | 0.775 |
| true lead = 1.30 `delta` | 0.821 |
| true lead = 1.50 `delta` | 0.936 |
| true lead = 2.00 `delta` | 0.999 |

**Three facts, stated because a reviewer will find them anyway:**

1. **The type-I rate is now 0.0024 at the 2-way tie, against a nominal 0.05.** The rule is
   **over**-corrected: the materiality clause dominates the precision clause at this `n`, so
   D4's 10% inflation is not merely removed but replaced by a highly conservative test. This
   is accepted. It costs power on genuinely near-tied configurations, which is exactly where
   `ROUTING_INDETERMINATE` is the honest answer.
2. **Power at a true lead of exactly `delta` is 0.499, not 0.80.** This is not a defect of
   `n`; it is a mathematical property of **any** rule that refuses to certify a sub-material
   lead: at the boundary `L = delta`, `P(observed lead >= delta) = 0.5` for every `n`. v1's
   advertised "80% power at a lead of `delta`" was attainable **only because v1 certified
   sub-material leads** — which is precisely S6's finding. The design attains 80% power at a
   true lead of **1.30 `delta`**. `n` buys resolution above the margin, not power at it.
3. The minimum lead the precision clause alone can pass at `n = 1,656` is
   `z_.975 / sqrt(n + z_.975^2) = 0.0481 = 0.693 delta`, i.e. **below** materiality — which
   is why the materiality clause is the binding one and why it is not redundant.

### 10.6 Compute cost, stated honestly

**Search.** 57,960 searches at the measured **3.86 s/search on this host** (the figure that
reproduces v1's 45,360-search / 48.6 CPU-hour statement exactly) = **223,726 s =
62.1 CPU-hours**. The `A3` host-determinism control (10 cases × 30 seeds, run twice) adds
600 searches = **0.64 CPU-hours**. Total search cost **62.7 CPU-hours**.

**Scoring.** This is the honest part, and it is not a point estimate. At E2a's measured
density of ~351 front rows per world, 1,932 worlds yield roughly **679,000 front rows**. At
E2a's measured `SIMPLIFY_TIMEOUT` rate (397 distinct expressions per 189,467 rows ≈ 0.21%),
that is on the order of **1,400 distinct expressions requiring tier-2 escalation** — and the
escalation tail is measured to be severe: `DINST_HOSTILE_REVIEW.md:39` records one sampled
stage-A abandoned expression reaching **44.4 GB RSS after 95 s** on a 48.2 GB host and still
running when killed; `POISON_WORLD_DETERMINATION.json` records one world OOM-killed **four**
times at 33.4/47.7/47.7/47.5 GB; the Gate 1 evaluator lost two cases to the OOM killer above
25 GB anon-rss.

**Therefore: no compute ceiling is declared, and the sympy scoring pass is not costed as a
single number.** `SYNTHESIS_DECISION_RECORD.md` §10's "ceiling: 260 CPU-hours" is
**withdrawn** and does not bind this protocol (`D6`). A declared compute ceiling over an
uncapped escalation tier is either not a ceiling or not uncapped, and — worse — under v1 it
would have decided `T-INSTRUMENT-UNBOUNDED`, i.e. a published scientific finding about the G2
contract. §25.4 replaces it with an **operational, non-scientific** state that produces no
label and no terminal. The realistic statement is: **search cost is 62.7 CPU-hours and is
known; scoring cost is dominated by a tail with no established upper bound, and the protocol
is designed so that exhausting that tail's resources produces no scientific conclusion of any
kind.**

## 11. SEED COUNT

**30 seeds per world. REUSED VERBATIM and NON-NEGOTIABLE.**
`rc5_seeds.A35_SEEDS_PER_CASE = 30` (imported, not restated); `befca0d` §2.5 control 2
(*"SEEDS_PER_CASE = 30 unchanged"*); `MURU_V2_E2_PREDECLARATION.md` §6 quantifies every
predicate *"for all 30 seeds"*.

**Why it may not be reduced as an economy.** `S_1` is a max over seeds,
`S_1(S) = 1 - (1-q)^S`. Reducing to 15 seeds shifts the estimand by **21.5 pp = 3.09 delta**
— three times the entire margin — so the surface would fail for a reason having nothing to
do with the pipeline. `S_3` is defined through `group_and_select` over exactly 30 retained
candidates and has **no seed-count-invariant reading at all**. Any proposal to change the
seed count is a change of estimand requiring protocol-owner ratification, not an engineering
decision.

## 12. SEARCH CONFIGURATION

**REUSED VERBATIM. Any deviation is a factor change requiring its own arm.**

| Item | Value | Source |
|---|---|---|
| Engine | PySR 1.5.10 / SymbolicRegression.jl 1.11.3 / PythonCall.jl 0.9.26 | `CLOUD_X86_PARITY_QUALIFICATION.json`, dependency lock 50/50 pins, 0 deviations |
| `PYSR_CONFIG` | frozen, unchanged | `befca0d` §2.5.2 |
| `GRAMMAR_VERSION` | frozen; operators `sqrt, log, square, cube, inv`; `exp` excluded | `befca0d` §2.5.2; DEVIATIONS_P3 D1 |
| Determinism | `deterministic=True`, `parallelism="serial"` | `befca0d` §2.5.2 |
| Threading | single-threaded pinned across Julia / OMP / MKL / OpenBLAS | parity artifact |
| Execution path | `muru.v2_calibration.e2c_search` (paired with `e2c_classify`), a **separate truth-blind module** reusing `rc5_runner`'s own building blocks directly and never importing `rc5_runner` (§16 `P8a`). Equivalence to `rc5_runner`'s search semantics is **measured, not asserted**, by control `C-1b`: **9 compared, 0 mismatched** | P1 §4.1, adopted; §16 `P8a`/`P8b` |
| Within-seed retention | `argmax(score)` = R0 control, `rc5_selection.select_row_label` | `befca0d`; alternatives are E4a arms, not surface parameters |
| Cross-seed grouping | `rc5_selection.group_and_select` on `identity_contract.template_key`, largest-class-wins, lowest-ordinal tie-break | frozen; alternatives are E4f arms |
| Stability gate | `STABILITY_GATE / STABILITY_DENOMINATOR = 20/30` | `structural_acceptance.py` — **imported, not reimplemented** |

**Hard preflight gate, before world 1.** Persist one case; assert all 21 search-side §14
fields present and non-null on every row; assert `rc5_selection.select_row_label` runs on the
persisted frame; assert `admissibility = "DECISION_ADMISSIBLE"` is stamped at row level.
**Fail ⟹ stop, do not generate.** (E2a's rescue-v2 candidate schema dropped `score`, `loss`,
`train_r2`, `grammar_complexity`, `parse_ok`, `effective_support`, `template_key` and
`admissibility`; without `score`, `select_row_label` raises `SeedExecutionFailure` by design.
This gate exists so that failure mode cannot recur silently.)

## 13. PLATFORM / ARCHITECTURE REQUIREMENTS

```
ARCHITECTURE_REQUIREMENT = x86_64 ACCEPTABLE ; ARM64 NOT REQUIRED
```

**The one-sentence declaration P2 BC-12 requires, now unconditional:** *this protocol's
qualification and routing decisions are computed entirely within a single-host surface and
make **no cross-architecture numeric claim anywhere**.* (v1 excepted its §21.3 veto; under
Decision 1 there is no exception left to make.)

**Binding conditions:**

- **A1 — Single-host generation.** All 1,932 worlds generated on one x86_64 host, one
  environment, one hash-recorded dependency lock. **No merging of ARM and x86 worlds**,
  following the precedent `X86_E2A_SEAL.json` sets (`corpus_is_x86_only: true`,
  `historical_worlds_merged: false`).
- **A2 — No wall-clock cap may assign a label, anywhere.** `SIMPLIFY_TIMEOUT_SECONDS = 5` is
  **retired as a classification rule** under this protocol. See §25.
- **A3 — Host-determinism control before world 1.** Re-run the frozen search on a declared
  10-case × 30-seed control subset **twice on this host** and require byte-identical fronts;
  plus the §28 retention-identity regression. *Instrumentation that changes the search is not
  instrumentation.*
- **A4 — Worker count, RSS ceiling and host load are FROZEN BEFORE STAGE 0 RUNS, and are
  declared parameters.** This is the repair for `D7`. v1 required
  `WORKER_COUNT_CALIBRATION` to be sized with *"headroom sized for the sympy tail"* — and
  the sympy tail is exactly what Stage 0's mandatory cost-distribution publication measures,
  creating a live channel `Stage 0 cost → Stage 1 concurrency and RSS ceiling → Stage 1
  OOM/UNRESOLVED rate → Stage 1 terminal`. **Both quantities are instead profiled on the
  E2a *engineering DEV* set (§26(1), already permitted and already fully seen), frozen and
  hashed in the freeze manifest, and declared in §34 — before Stage 0 executes.** They may
  not be changed after Stage 0 reports. Any change is a tuning-ledger entry and voids the
  surface.

**Disclosed caveat.** Cross-architecture **search** equivalence is unestablished:
`worlds_executed_on_this_host: 0` in the parity artifact, which replayed sealed ARM candidate
rows through the x86 *classifier* and never compared x86 fronts to ARM fronts. Under
Decision 1 no decision in this protocol depends on a cross-architecture comparison, so the
non-attributability that v1 had to disclose about a tripped veto **no longer attaches to any
terminal**. It is retained here as a scope limit on what the surface's descriptor vector
describes.

**Mandatory hardening, derived from the measured E2a interruption**
(`INTERRUPTION_FORENSICS.json`:
`INFRASTRUCTURE_FAILURE__KERNEL_OOM_PLUS_SYSTEMD_SCOPE_TEARDOWN`): per-worker RSS ceiling
enforced in-process (a single python reached ~32 GiB on a 47 GiB host with no swap); shards
in **separate systemd scopes** or an explicit `OOMPolicy` (`DefaultOOMPolicy=stop` turned one
OOM kill into SIGTERM for 11 surviving shards); the staleness watchdog **smoke-tested in
preflight** (it previously died 0 s after launch with `line 46: File: unbound variable`, so
the run was unwatched end to end); world-level checkpointing with byte-exact resume, **tested
before the run rather than during it**. **None of these may produce a scientific label or a
scientific terminal — see §25.4.**

## 14. FULL FRONT SCHEMA

**REUSED VERBATIM from `befca0d` §2.4. All 28 fields, from inception. D6 is binding: there is
no imputation path and no retrofit path.** (`CRITIC_GOVERNANCE` check 5 verified v1's field
list against `befca0d` §2.4 field for field; it is reproduced unchanged.)

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

Extended, without removing or renaming any of the above, by the condition-identifying fields
the new population requires: `partition` (the literal string `"calibration"` the generator
writes into each `TruthRecord`), `case_id`, `family_code`, `variant`, `condition_kind`,
`coefficient_value`, `noise_sd`.

**BC-5 as a mechanical check.** A validator with the 28-field list **hard-coded and frozen
before execution** is run against the corpus at seal time. **Any absent field ⟹ VOID. Any
field written after the seal ⟹ VOID. No field may be back-filled, imputed, or recomputed
after the fact.**

## 15. ADMISSIBILITY FIELD

`admissibility` is **mandatory at the ROW level** and is stamped `"DECISION_ADMISSIBLE"` on
every persisted front row of the Stage 1 surface at write time. It is the mechanism by which
`DECISION_INADMISSIBLE` is enforced **mechanically rather than by convention**
(`befca0d` §2.3), and its absence is the stated reason the E2b front corpus cannot be reused
as the calibration surface (ratification §8).

**Rows produced by Stage 0 are stamped `"EXPLANATORY_ONLY"`.** The static citation checker
must **reject any proposed change whose supporting set contains a Stage 0 identifier or a
§21.4 annotation identifier.** This is the same checker that already rejects any change whose
supporting set contains an E2b identifier and no admissible identifier.

**`D13(1)` is resolved rather than finessed.** v1 required the checker to conceal a *necessary
condition* of every licence (a passing Gate V) from that licence's support set — an
incoherence. Under Decision 1 the §21.4 annotation is **not** a necessary condition of any
licence, so excluding it from support sets is simply correct. Where the annotation reads
`CONTRADICTS`, §21.5 requires it to be **quoted in full in the owner's ratification record** —
disclosed, never concealed, and never counted as support.

## 16. TRUTH-BLIND BOUNDARY

**REUSED VERBATIM from `befca0d` §2.4.** The search path is **truth-blind at search time**.
The seven truth-derived columns are computed in a **separate scoring pass the search never
sees, executed by a distinct process**, and joined afterwards.

**Enforced, not promised** — but **not** by the module-level import ban v2 wrote, which was
unsatisfiable:

> **`X-1` repair — v2's `P8` could not be passed by ANY implementation, including the
> production path the same protocol mandates.** §12 requires the search to run through
> `paper_benchmark/rc5_runner`; `rc5_runner.py:48` imports from `g2_contract`, and
> `rc5_selection.py:77` does too. §14 then requires the search-side field `effective_support`,
> whose function `extract_effective_support` is **defined in `g2_contract`**
> (`g2_contract.py:138`). So §12 mandates an entry point, §16 forbids what it imports, and §20
> makes the prohibition a hard precondition. `QUALIFIED` was unreachable by a **fourth**
> independent route.
>
> A module-level ban is also the wrong instrument in both directions. `g2_contract` mixes
> syntax-only helpers with truth-comparing ones:
>
> | symbol | argument | truth-dependent? |
> |---|---|---|
> | `extract_effective_support(expr_str)` | expression only | **no** |
> | `classify_discovered_family(expr_str)` | expression only | **no** |
> | `_safe_parse`, `GRAMMAR_PRIMITIVES`, `identity_contract.template_key` | expression only | **no** |
> | `classify_support(discovered, truth_support)` | takes truth | **yes** |
> | `classify_family_match(discovered_family, truth_family)` | takes truth | **yes** |
> | `evaluate_g2_event(support_status, family_status)` | truth-derived inputs | **yes** |
> | `truth_support_for_case(...)` | truth | **yes** |
>
> Banning the module is **too strong** (it forbids syntax helpers that cannot leak truth,
> because truth is not among their arguments) and **too weak** (importing nothing proves
> nothing about whether a `TruthRecord` field reaches the design matrix).

**The check, in the two parts that actually bind — corrected a second time
(`CRITIC_SCIENCE` `V3-C3`).** v3's `P8a` still read *"no MODULE reachable ... may BIND"*, which
is module-closure scoping wearing a new name. It is still unsatisfiable: `g2_contract` is the
**home module** of the permitted syntax helpers, and that same module **defines** (hence
binds) the four banned symbols and **imports** `TruthRecord` — so importing anything permitted
still drags the whole module into the reachable closure. Executed check found **7 violations**
across a 14-module transitive closure. The fix is to check the **call graph**, not the import
graph — whether a banned symbol is ever **invoked**, not whether its home module is ever
reachable:

```
P8a  CALL-GRAPH BAN. No function in the search entry point's transitive CALL GRAPH may
     INVOKE any of: classify_support, classify_family_match, evaluate_g2_event,
     truth_support_for_case, e2_classify.classify_expression,
     discovery.equivalence.algebraically_equivalent, or any oracle/truth-registry
     function. IMPORTING their home module for a permitted symbol is not itself a
     violation; CALLING one of these names, anywhere in the reachable call graph, is.
     EXPLICITLY PERMITTED CALL TARGETS: extract_effective_support,
     classify_discovered_family, _safe_parse, GRAMMAR_PRIMITIVES,
     identity_contract.template_key / template_key_string.

P8b  DATA-FLOW ASSERTION. No field of TruthRecord may be reachable from the object graph
     of CaseDesign. Asserted at runtime FOR EVERY WORLD, not once in preflight.
```

**`P8a` is executed, not asserted.** `scripts/v2_truth_blind_verifier.py` walks the AST of
every module in the entry point's import closure, collects every `Call` node's resolved
target, and fails if any resolves to a banned symbol. Run against
`muru.v2_calibration.e2c_search` + `muru.v2_calibration.e2c_classify` (the entry point named
below), it finds **zero** call-graph violations: `extract_effective_support` and
`classify_discovered_family` each call only `_safe_parse`, `sympy.simplify` and
`_resolved_support` internally — never `classify_support` or its siblings — so importing their
home module carries no call-graph exposure to the banned symbols.

**Why `P8b` is stricter where it counts.** The leak that matters is `g` being read from
`truth.g_by_compound` instead of estimated. It is currently clean and `P8b` is what keeps it
clean: `rc5_adapter.build_case_design(compounds, scalars)` takes
`scalars = rc5_estimate.estimate_case_scalars(compounds, trajectories)`, so `g` is **estimated
from the observed trajectories**. Neither an import ban nor a call-graph ban would ever detect
a regression there; `P8b`'s runtime data-flow assertion does, on every world.
`e2c_search.assert_design_truth_blind` implements it and runs per world, not once.

**Consequence for §12, now discharged rather than merely stated.** Because `rc5_runner` binds
the truth-dependent symbols at module scope, the search entry point is the **separate module
`muru.v2_calibration.e2c_search`** (paired with `e2c_classify` for canonicalisation), reusing
the truth-blind functions directly (`build_case_design`, `fit_case_scalars`,
`build_case_regressor`, `select_row_label`, `row_complexity`, `candidate_r2_on`) and never
importing `rc5_runner` or `e2_classify`. §12's *"the real v1 production path"* requirement is
discharged by **control `C-1b`**, which requires the instrumented engine's
`argmax(score)`-retained candidate to be byte-identical to the frozen `e2_search` module's (the
one that produced the sealed E2a corpus) on a declared control set. **Executed: 9 compared, 0
mismatched, PASSED** (`e2c_search.control_c1b`). `C-1b` tests identical search semantics by
measurement; an import path was only ever a proxy that did not imply it.

The check runs in preflight and at seal time and its result is recorded in the manifest.

**Gate Q's qualification clauses are truth-blind by construction** (§18): every one is a
function of the registry, the generator, the seed derivation, the new module's declared
population and the internal-validity controls. **None consults the oracle.** The four-way
partition is truth-dependent. That a truth-blind qualification cannot be the truth-dependent
attribution is the functional-independence argument at the qualification layer, and is the
argument §4.1 property (v) makes constructive.

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
`g2_contract.wilson_lower_95` / `wilson_upper_95`, `structural_acceptance.STABILITY_GATE`.

**`g2_contract.py` is byte-unchanged.** The classification **semantics** are byte-unchanged.
Only the control flow around unresolved rows changes (§25), and that change is **strictly
conservative**: it can refuse to decide, never decide differently.

**Classification mode is declared prospectively** (P2 §8 item 20): **lazy classification,
executed under the determinacy bound of §25.** This is sound because under the bound the
number of classify calls cannot change a label — a row is either resolved to its frozen label
or explicitly `UNRESOLVED`, and a world is classified only when the class is invariant over
every resolution. Under a wall-clock cap lazy classification is *not* sound, because the call
count differs by stage and therefore exposes stage A to systematically more timeouts. A2
removes the cap; §25 removes the dependence.

## 18. PRIMARY QUALIFICATION STATISTIC

**There is no numeric qualification statistic.** Qualification is **binary and structural**
(decision record §6, decided by R4): frozen authority contains **no** qualification concept
at all — `befca0d` §2.3 is destructive-only — so any numeric qualification bar would be a
newly invented magnitude applied to the surface it will judge.

**`QUALIFIED` has exactly one definition, and it is in §20.** v1 gave two mutually
inconsistent definitions in §18 and §20, differing by the nine preconditions `P1..P10`
(`S18`). This section therefore **defines the clauses** and **defers the predicate to §20**.

| Clause | Content | Type |
|---|---|---|
| **Q1 — design provenance** | same generator, same `GENERATOR_VERSION`, same `ROOT_SEED = 20260813`; the registry's twelve G2 conditions at equal weight `w_k = 1/12`; the calibration case-id namespace disjoint from every registry case id and rejected by `registry.resolve_case_id`; seed band declared by the §5.2 rule and **carrying no overlap of its own** under `seed_band_registry.find_overlaps(DECLARED_BANDS + (CALIBRATION_BAND,))` **restricted to overlaps naming `v2_calibration_surface`** (see §5.2's `NO-BAND-COLLISION` predicate); **all 380 pre-existing case ordinals and all 11,400 pre-existing search seeds byte-identical**; **`pb_33` and `pb_34` return 0 errors, every protected path byte-identical to its baseline or matched exactly by a registered authorized-delta entry**; every G2 cell carrying exactly 138 completed worlds; every world exactly 30 completed seeds | construction check, PASS/FAIL, **zero magnitudes, zero outcomes** |
| **C-0 — generator equivalence** | `generate_calibration_case_body` reproduces `generator.generate_case` byte-identically on **all 380** frozen case ids (§5.2). Result at authorship: **380/380** | binary |
| **C-1 — identity / replay** | the instrumented engine's `argmax(score)`-retained candidate **byte-identical** to the frozen production path's, for every seed on the §28 control world set | binary |
| **C-2 — negative control** | **exactly 12** adversarial constructions, one per G2 condition, **known not truth-equivalent by construction** (`correlated_distractor` substituted for `descriptor`; `descriptor2` substituted for `descriptor`; the descriptor factor replaced by a matched-magnitude constant — `befca0d` §3.6), must be **rejected** by the instrument. **Pass bar: 12/12** | binary |
| **C-3 — known-answer control** | **exactly 12** worlds whose stage is determinable analytically, one per condition, run through the full instrument, must recover the known stage. **Includes, mandatorily, at least 3 planted correct rows that are expensive to canonicalize**, verifying the instrument does not report `NEVER_ON_FRONT`. This is the control that would have caught the defect of §3 item 3. **Pass bar: 12/12 stages and 3/3 planted rows recovered** | binary |
| **C-4 — uncapped validation sample** | a pre-declared sample of **101 rows** (Gate 1's own precedent, 101/101) re-scored with **no cap**, requiring **100%** agreement with the bounded instrument | binary |
| **C-5 — determinism replay** | a pre-declared subset of **30 worlds × 30 seeds** re-executed (Gate 1's own precedent, 30/30), requiring byte-identity | binary |
> **`DEF-M3` — the classifier version that defines Stage 0's population is PINNED, not
> chosen at runtime.** v2 hashed the classify cache but selected the classifier `version`
> **by frequency** (`Counter(...).most_common(1)`) from a mutable file outside the repository.
> A different cache state could therefore silently redefine Stage 0's population. Pinned here,
> as a literal, verified at this commit:
>
> ```
> CLASSIFIER_VERSION = "90a3b5ea3a83b0e9587e3b1e4e54e188afb8e893fabc9293d9177bc767089e7a"
> CLASSIFY_CACHE_SHA256 = "66f30ea1d41d7063b3cb5a481281715011ba54ba897d5d17e058d8bb75273d50"
> ```
>
> The instrument **asserts** both and **aborts** on mismatch. It no longer infers either.

| **C-6 — canonicalisation-table parity** | the §25.3 expression → canonicalisation table re-computed on a second architecture on a pre-declared **500-expression** audit sample, requiring **0** mismatches. **Mandatory, not waivable** | binary |
| **C-6a — downstream-freeze integrity** | `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` still hashes to `0ce2755d…3a7f61`, **byte-for-byte and unamended**; `8a2ffa50` is still a strict ancestor of HEAD; `E4F_FREEZE.txt`'s tuning ledger is still empty. Checked **before** Gate R is read, so a downstream freeze drift can never present as a routing outcome. **The §36 restatement is written to a SEPARATE artifact and never to this file — see §36's precedence rule — so `C-6a` and §36 can both be satisfied** | binary |

**Every count in C-2 … C-6a is declared here and is in §33's inventory.** v1 left all of them
to the executor while claiming *"there is no knob in the qualification"* (`D10`).

**Why P1's Q2–Q4 are NOT gating clauses.** P1's truth-blind descriptor equivalence tests
(signal regime, consensus geometry, retained-candidate geometry) would introduce at least
three new magnitudes with no frozen source, and P1 itself discloses that **E2a would very
likely PASS Q3**. A clause that passes the surface it was built to exclude has no power as a
gate. They are retained in full as **mandatory reported diagnostics** (§19 D9) so that an
independent critic can test further descriptors against the same surface without regenerating
it.

## 19. SECONDARY DIAGNOSTICS

All are computed, sealed and published. **None may change any verdict. They exist to explain
a failure, not to rescue one.**

| # | Diagnostic |
|---|---|
| D1 | The frozen four-way partition `(pi_A, pi_B, pi_C+D, pi_E)` with 95% Wilson intervals |
| D2 | The `befca0d` §2.6 conditional metrics verbatim: `P_front`, `P_retain_given_front`, `P_win_given_retain`, `rank_of_correct`, `score_gap`, `complexity_gap`, `r2_gap`, `front_size` — per condition and per truth family |
| D3 | Per-condition stage table: `S_j` by each of the 12 conditions, 12 × 3 tests, **Holm–Bonferroni** across them (§27) |
| D4 | Per-coefficient-regime stage table (`befca0d` §2.6's own *"per family and per coefficient regime"*), coefficient tertiles, Holm across the regime family |
| D5 | Noise-conditioned readings of the primary — **explicitly a diagnostic**, because conditioning on noise flips the standardised argmax on the only corpus where it has been computed (decision record §1.4) |
| D6 | `selection_count` distribution and 20/30 stability-gate failure fraction |
| D7 | **P1's counterfactual recovery contrast**, DEV-half only: `rec_retention`, `rec_voting`, `rec_ceiling` over the frozen arm grids (retention R0–R4, voting V0–V2), with `selection_count` inflation **measured, not assumed away**. Non-licensing (decision record §5) |
| D8 | `false_structure_rate` on the NEG stratum for every arm, against E3's frozen `> 0.10` study-validity bar and E6's frozen `Wilson upper <= 0.15 on >= 100 evaluable safety opportunities`. **Reporting a G2 gain without its safety cost is not permitted** (`befca0d` §3) |
| D9 | P1's Q2–Q4 descriptor vector in full: `descriptor_sd`, `mass_range_ratio`, `identity_class_count`, consensus concentration, retained `valid_r2` and complexity |
| D10 | The determinacy report: `unresolved_rows / total_rows`, `INDETERMINATE_WORLDS` (which must be 0), escalation cost distribution, and the identity `g_1 = g_2 = g_3 = 0` restated as the check it is — **mandatory sealed fields** |
| D11 | **The §21.4 corroborate/contradict annotation**, with its interval. Mandatory, reported, non-licensing, non-citable |

## 20. ACCEPTANCE RULE — THE SINGLE DEFINITION

Evaluated mechanically from the sealed corpus. Every constant below is fixed at freeze time.

```
CONSTANTS
  delta   = 10/144 = 0.0694444...     [DERIVED from PE2-4; derivation at §10.1]
  z       = z_.975 = 1.9599640        [DERIVED: one-sided bound on a DATA-SELECTED
                                       contrast between two of three cells; §10.2]
  alpha   = 0.05 family-wise on the SECONDARIES  [REUSED: f4c1105 §8]
  w_k     = 1/12 for each of the 12 registry G2 conditions   [REUSED: registry.py]
  R       = 138 replicates per condition ; n = 1656 G2 worlds ; 276 NEG worlds
                                       [DERIVED: §10.4]
  seeds   = 30 per world               [REUSED: rc5_seeds.A35_SEEDS_PER_CASE, imported]
  B       = 10,000 bootstrap replicates, stratified by condition   [REUSED: f4c1105 §8]
  bootstrap RNG = derive_seed_v2("bootstrap", "<policy_id>") truncated to 64-bit
                                       [REUSED: f4c1105 §8]
  CI      = Wilson 95%, g2_contract.wilson_lower_95 / wilson_upper_95, IMPORTED
                                       [REUSED: f4c1105 §7 -- "reused, not reimplemented"]

ENDPOINT  (the frozen four-way partition, in its monotone cumulative parameterization)
  reach_front(w; rho)  = 1 { >=1 of the 30 seeds' Pareto fronts contains a G2-correct row }
  reach_retain(w; rho) = 1 { >=1 seed's argmax(score)-retained candidate is G2-correct }
  reach_win(w; rho)    = 1 { the cross-seed representative is G2-correct }     (= SUCCESS)

  S_j_hat(rho) = SUM_k w_k * ( 1/n_k * SUM_{w in condition k} reach_j(w; rho) )   j = 1,2,3
                 with n_k = 138 for every k, so the weighting is exact, not approximate

  pi_hat(rho)  = ( 1 - S1, S1 - S2, S2 - S3, S3 )   over ( A , B , C+D , E )
                 -- identical to the frozen A-E taxonomy by differencing; C+D is
                    MURU_V2_E2_PREDECLARATION §6's LOST_IN_CROSS_SEED

DETERMINACY  (monotone; two evaluations, not 2^U -- see §25)
  rho_bot = every UNRESOLVED row assigned INCORRECT
  rho_top = every UNRESOLVED row assigned CORRECT
  A world is INDETERMINATE iff its class differs between rho_bot and rho_top.
  Under §25.1's monotonicity lemma:  INDETERMINATE_WORLDS == 0  <=>  g_1 = g_2 = g_3 = 0.
  (v1's separate gate g_j <= 0.010 is deleted as provably subsumed -- see §0.4.)

ADMISSIBILITY PRECONDITIONS  (all must be YES; each is endpoint-blind)
  P1  COMPOSITION_EXACT     : every one of the 12 G2 conditions has exactly 138 completed
                              worlds; 0 missing, 0 duplicate. NEG stratum: 138 each for
                              F07 and F19, F19 variant cycle balanced in each half
  P2  SEEDS_EXACT           : every world has exactly 30 completed seeds
  P3  RETENTION_IDENTITY    : §28 byte-identical on the control world set
  P4  SCHEMA_COMPLETE       : all 28 §14 fields present incl. row-level `admissibility`;
                              0 imputed; 0 written after seal
  P5  HOST_INVARIANT_LABELS : no label is a function of wall-clock time, worker count,
                              host load or CPU model (§25); sealed canonicalisation table
  P6' DETERMINACY_OK        : INDETERMINATE_WORLDS == 0 on the CALIBRATION SURFACE
                              [violation => VOID_INSTRUMENT_INDETERMINATE. There is no
                               top-up and no re-read. v1's P6 and its top-up are deleted]
  P7  NO_MASS_POWER         : 0 mass_power worlds in the primary population
                              -- satisfied BY CONSTRUCTION (§7), not by exclusion
  P8  TRUTH_BLIND_BOUNDARY  : the §16 static import check passes
  P9  FREEZE_INTACT         : all 380 pre-existing ordinals and 11,400 pre-existing seeds
                              byte-identical; `pb_33` and `pb_34` return 0 errors; every
                              protected path byte-identical to baseline or matched exactly
                              by a registered authorized-delta entry
  P10 SINGLE_SHOT           : exactly one SURFACE generated (see §22 for the definition);
                              tuning ledger EMPTY

ACCEPTANCE  -- the ONLY definition of QUALIFIED in this document
  QUALIFIED := Q1 AND C-0 AND C-1 AND C-2 AND C-3 AND C-4 AND C-5 AND C-6 AND C-6a
               AND P1 AND P2 AND P3 AND P4 AND P5 AND P6' AND P7 AND P8 AND P9 AND P10

  IF NOT QUALIFIED -> the failing clause determines the terminal via §22, which is the
                      SOLE terminal-assigning authority. The failing clause(s) are
                      reported. **No margin, endpoint, weight, stratum, exclusion,
                      conditioning set, or population may be revised in response.**
```

**`QUALIFIED` now contains no numeric threshold at all.** v1's determinacy gate was the one
numeric knob inside it; deleting `g_max` (§0.4) removes it. The declared counts in
C-2 … C-6a are **sample sizes and pass bars, both fixed here**, not thresholds on a measured
quantity.

## 21. ROUTING RULE

Fixed-sequence gatekeeping. Routing is read **only if** `QUALIFIED`, never jointly, never the
other way round. This preserves the family-wise error rate without adjustment (§27).

### 21.1 The certification predicate

```
ROUTING_CERTIFIED  :=  argmax over { pi_A , pi_B , pi_C+D } is IDENTICAL under rho_bot
                       and rho_top
                       AND  ( pi_top - pi_second ) >= delta            under BOTH resolutions
                       AND  LCB_97.5( pi_top - pi_second ) > 0         under BOTH resolutions
                            with Var(pi_1 - pi_2) = (pi_1 + pi_2 - (pi_1 - pi_2)^2)/n
```

> **`DEF-H4` repair — v2 asserted the opposite of the truth here.** v2's text claimed the
> argmax-invariance clause *"fails loudly rather than a formality that cannot fail"*. It is a
> formality that cannot fail. `P6'` requires `INDETERMINATE_WORLDS == 0`, which makes
> `rho_bot` and `rho_top` **coincide on every admissible surface**; hence all three "under
> BOTH resolutions" qualifications are **provably vacuous** on anything that reaches this
> gate. Asserting a vacuous check is a live check is exactly the `g_max` / `D5` defect, and v2
> reintroduced it inside the certification predicate itself.
>
> **Repaired.** The qualifications are **retained as written but labelled what they are**:
>
> * On an admissible surface (`P6'` holding) they are **satisfied by construction** and add
>   nothing. This is stated, not claimed as strength.
> * They are retained because they are the **only** thing standing between this predicate and
>   a surface on which `P6'` was mis-evaluated. They are a **defence in depth against a bug in
>   `P6'`**, not an independent scientific check, and the protocol claims no more for them.
> * `ROUTING_CERTIFIED`'s scientific content is therefore carried **entirely** by the
>   materiality clause (`lead >= delta`) and the precision clause (`LCB > 0`), which are not
>   vacuous and which §10.3 and §10.5 show are not redundant with each other.

**Why a bare plurality is not sufficient** (decision record §3, R2 and R4): on the only corpus
where the standardised argmax has ever been computed it flips under two undeclared analyst
choices — conditioning on noise level (0.23 pp margin) and correcting the instrument (4.4 pp
margin). A bare argmax has the appearance of zero free parameters and in fact the maximum
hidden discretion.

**Why the materiality clause is separate from the precision clause:** §10.3, §10.5. It is not
redundant — the precision clause alone would certify leads down to `0.693 delta` at this `n`.

### 21.2 Gate R — the licensing table

Evaluated on the **full G2 population**, not the split (`f4c1105` §6: the gate is a diagnostic
fact about the surface's own attribution). Computed by an isolated process which writes a
hash-sealed verdict and appends it to the hash-chained event log **before any process is
permitted to compute the §21.4 annotation**.

**Exactly one row fires. The rows are mutually exclusive and jointly exhaustive by
construction, and §22 assigns the terminal.**

| # | Predicate, in this order | Route | Executable? |
|---|---|---|---|
| 0 | `NOT QUALIFIED` | — | §22 assigns the terminal from the failing clause |
| 1 | `ROUTING_CERTIFIED` and certified argmax = `B` (`LOST_IN_RETENTION`) | RC3 confirmed → **E4a** | **Yes, with one owner act** — see the note below |
| 2 | `ROUTING_CERTIFIED` and certified argmax = `A` (`NEVER_ON_FRONT`) | RC4 confirmed → routed **through E3's completed per-cell verdicts** | **Partially.** `mass_saturating_descriptor` (F09) and `mass_interaction` (F10) only. **BLOCKED** for `mass_affine_descriptor` and `mass_exponential_descriptor` (MARGINAL, `search_side_attribution_licensed: false`) — which is 10 of the 12 conditions |
| 3 | `ROUTING_CERTIFIED` and certified argmax = `C+D` (`LOST_IN_CROSS_SEED`) | RC7 → §22 `F16` | **No — `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`.** See the rider below (`§2.1`, `N6`): no protocol-owner record authorizes E4f's execution today, and none of ratification §4 (D2-ext)'s suspension is lifted by this protocol's own construction of E4f's text |
| 4 | `NOT ROUTING_CERTIFIED` and `RETENTION_EXONERATED` (§21.3) | RC3 withdrawn. No retention change licensed | n/a |
| 5 | `NOT ROUTING_CERTIFIED` and not `RETENTION_EXONERATED` | no route | n/a |

**Row 1's honesty note, required by `S17`.** `f4c1105` is operationally complete **but its own
§4 GATE 1 returned STOP on the sealed Gate 1 result** (`E2B_69_57_HOOK = "FAIL"`,
`GATE_1 = "FAIL"`, `GATE_1_DEFINITIVE = "YES"`), and nothing in the ratification re-arms it.
v1 called this row *"Yes — `f4c1105` is a complete operational freeze"* without stating this.
**Executing E4a therefore requires a protocol-owner act re-arming `f4c1105` against this
surface, in place of its frozen and already-fired GATE 1. That substitution is a change to
frozen authority and requires ratification; it is not reuse.** It is folded into the single
ratification step §21.5 already requires, so it adds no new procedure — only honesty about
what that step is doing.

**Row 3's authority rider — `§2.1` / `N6`, superseding v3's scope rider.** v3 attempted to
narrow route `C+D` to E4f family i (classifier) only, on an authority citation
(`CRITIC_GOVERNANCE` `G7`'s repair) that itself did not survive review (`N6`). With no
protocol-owner record for E4f's execution and no E4f hostile review performed, the narrowing
question is moot: **route `C+D` proposes nothing today**, regardless of family. `F16`
(`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`) fires unconditionally when Gate R selects row 3.

**The family i/ii analysis is preserved below, dormant, for the day a real ratification
record exists** — it is correct on its own terms and there is no reason to redo it then:

* **`DEF-H5`** — E4f's Gate `H1` is a **zero-defect census** (`b_V = 0`) in the direction the
  voting arm necessarily pushes. By E4f's own **Lemma K**, `gate_passed` is monotone in
  coarseness, so `H1` demands 100% correctness among every newly-stabilised world across 828
  EVAL worlds, in a regime running a few percent correct. Family ii (voting) is near-certainly
  dead on arrival.
* **`DEF-H6`** — E4f's `FP-6` substitutes `false_stabilisation_rate` for a gating
  `k_inflation`. That statistic is truth-facing and contains the negation of Gate `H2`'s own
  efficacy term, so family ii's safety evidence is partly discharged by its efficacy result —
  not independent of the efficacy claim.
* **If and when a ratification record authorizes E4f's execution**, the disposition these two
  findings support is: propose family i (classifier) only; execute and fully report family ii
  (voting), licensing nothing from it; treat `H1`'s expected failure as pre-recorded rather
  than surprising. `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` remains untouched and ready.

**Row 3's freeze-integrity rider, retained regardless of executability.** The E4f freeze
**predates any route** and **may not be amended after one**. Its hash (`0ce2755d…3a7f61`) and
its freeze commit (`8a2ffa50`, verified a strict ancestor of HEAD) are re-verified as a clause
of control `C-6a` (§18) before Gate R is read; if either has moved the run terminates at
`VOID_CONTROL_FAILURE` (§22 F6) — the drift is an integrity failure, not a routing outcome.
This check runs **independently of whether the route is executable**, so a future ratification
record cannot be dated to a stale freeze.

### 21.3 `RETENTION_EXONERATED` — the exoneration branch, with declared numbers

`f4c1105` §4 GATE 2's second branch, verbatim: *"ELSE IF `P_retain_given_front` is near 1
wherever `P_front` is high (the exoneration condition) — THEN this protocol DOES NOT
EXECUTE. RC3 is WITHDRAWN and reported as such; no retention policy is scored. STOP."*
Neither *"near 1"* nor *"high"* is a number, in the frozen text or in v1, and v1 **asserted**
the band was pre-declared when it was not, while placing the branch **first** in the table —
the single easiest cheat in v1 (`S7`).

**Declared now, DERIVED, with zero new magnitudes:**

```
RETENTION_EXONERATED  :=  pi_B < delta                                 under BOTH resolutions
                     AND  P_retain_given_front = S_2/S_1 >= 1 - delta   under BOTH resolutions
                     AND  S_1 > 0
```

**Derivation.** `pi_B = S_1 - S_2 = P(reach front) - P(reach retain)` is exactly the share of
worlds lost *at* the retention stage. "The retention rule is exonerated" is therefore
"retention loses less than a material share", and *material* is the programme's own frozen
`delta`. The absolute form is preferred over the frozen ratio form because the ratio form
requires a **second** undeclared threshold ("high `P_front`"), while the absolute form
requires none.

> **v2's dominance argument was mathematically false, and its own witness refuted it**
> (`CRITIC_GOVERNANCE` `G3`). v2 claimed `pi_B < delta` implies
> `P_retain_given_front = S_2/S_1 >= 1 - delta/S_1 >= 1 - delta` "whenever `S_1 <= 1`".
> The step `1 - delta/S_1 >= 1 - delta` requires `delta/S_1 <= delta`, i.e. `S_1 >= 1`. It
> therefore holds **only at `S_1 = 1`**, and is false for every surface that does not reach
> the front everywhere. v2's own §32.1 witness `W-EX` is a counterexample:
> `P_retain_given_front = 0.9036 < 1 - delta = 0.9306`.
>
> The consequence was not cosmetic. At `S_1 = 0.10` the absolute form admits
> `P_retain_given_front` as low as `1 - delta/S_1 = 0.306`, and the branch would then publish
> `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` — *"retention is exonerated"* — on a surface
> where retention discards two thirds of everything that reached the front. E3's MARGINAL
> verdicts make low `S_1` the **expected** regime, not a corner case.
>
> **Repair, adding no new magnitude:** the exoneration predicate is the **conjunction** of
> the absolute and ratio forms, both at the programme's own frozen `delta`:
>
> ```
> RETENTION_EXONERATED  :=  pi_B < delta                                under BOTH resolutions
>                      AND  P_retain_given_front = S_2/S_1 >= 1 - delta  under BOTH resolutions
>                      AND  S_1 > 0                        (else the ratio is undefined and
>                                                           the branch is not evaluated)
> ```
>
> The `S_1 > 0` guard is required so the branch cannot fire vacuously on a surface that never
> reaches the front — where "retention is not the loss stage" is true only because nothing
> ever reached retention. That degenerate path is routed to `SURFACE_DEGENERATE_NO_FRONT`
> (§22 F14), not to an exoneration.

**Two declared departures from the literal frozen ordering, disclosed rather than called
verbatim** (`S7`, `S17`):

1. **Position.** `f4c1105` evaluates exoneration immediately after the `B` branch and before
   the `A` and `C+D` branches. This protocol evaluates it **after all three certified
   routes**. Reason: `f4c1105`'s entire scope is *retention adoption*, so its "STOP" means
   "no retention policy is scored"; this protocol's scope is a **three-way route**, and
   letting a retention-scoped exoneration pre-empt a certified route to E4f or E4b/c/d would
   read a rule about one arm as a rule about all of them. Note that the reordering is
   **operationally vacuous on route B**: a certified `B` route requires
   `pi_B - pi_second >= delta` and `pi_second >= 0`, hence `pi_B >= delta`, so
   `RETENTION_EXONERATED` and route `B` are **mutually exclusive by arithmetic**. The
   reordering can only affect routes `A` and `C+D`.
2. **Predicate.** The frozen ratio-plus-threshold form is replaced by the absolute form
   above, for the reason given. This is a derivation, not reuse, and it is listed in §33's
   DERIVED table.

`RETENTION_EXONERATED` is additionally **reported as an annotation** whenever it holds,
including under rows 2 and 3, where it is informative and non-operative.

### 21.4 THE CORROBORATE / CONTRADICT ANNOTATION — mandatory, reported, licensing nothing

This replaces v1's Gate V. **It is computed only after Gate R's verdict is hashed and
appended to the hash-chained event log, by a different named party, and it can change no
terminal state.**

**Definition of the statistic, which v1 never gave** (`S3` — the factor of 2 was
outcome-determining under v1 and is fixed here regardless):

```
TV(p, q)     :=  0.5 * SUM_i | p_i - q_i |          (the half-sum convention)
D_max(p, q)  :=  MAX_i | p_i - q_i |                (the per-class convention PE2-4 was
                                                     actually frozen on; reported alongside)
```

**Comparator.** `pi_0 = (A, B, C+D, E) = (14, 55, 71, 4)/144 =
(0.09722, 0.38194, 0.49306, 0.02778)`, the ratified D1 attribution.

**The comparator is a 144-case draw and is treated as one** (`D3`, adopted). v1 treated it as
a constant with zero sampling error — the exact operation
`SYNTHESIS_DECISION_RECORD.md` §1.5 rules inadmissible and P3's own author labels
anti-conservative. Both `TV` and `D_max` are reported with a **95% interval from a parametric
bootstrap that resamples BOTH sides**:

```
surface    ~ Multinomial( n = 1656, pi_hat )
comparator ~ Multinomial( n =  144, pi_0   )
B = 10,000 replicates                        [REUSED: f4c1105 §8]
RNG = derive_seed_v2("bootstrap", "E7-CC")   [REUSED: f4c1105 §8]
```

**The annotation, which is a label and not a gate:**

```
CORROBORATES    if the UPPER end of the 95% interval on TV is <= delta
CONTRADICTS     if the LOWER end of the 95% interval on TV is  > delta
INDETERMINATE   otherwise
```

**Pre-recorded, before execution, so nobody reads more into it than it can carry.** Verified
at 200,000 draws on this host:

| Quantity | Value |
|---|---:|
| Mean `TV` arising from **comparator sampling noise alone**, surface exactly `pi_0` | **0.0477** = 69% of the entire `delta` |
| `P(TV > delta)` from comparator noise alone | **0.177** |
| `P(TV > delta)` with both sides sampled, surface regime **identical** to `pi_0`, `n = 1656` | **0.205** |
| Annotation for a surface drawn from **exactly** `pi_0` | **`INDETERMINATE`** |

**A perfectly matched surface does not read `CORROBORATES`.** The comparator's own variance
consumes most of the tolerance. That is the arithmetic reason this quantity cannot be a gate,
and it is stated here rather than discovered later. v1's own §34 central prediction gave
`TV = 0.0708 > delta` at the point estimate — v1's veto tripped on v1's own prediction
before any noise.

**Binding constraints on the annotation:**

- It is **mandatory**. It is computed and published on every execution that reaches a routing
  verdict, whatever the verdict.
- It **changes no terminal state**, appears in **no** §22 failure rule, and is **not** a
  member of any licence's support set. The static citation checker rejects any change citing
  it (P2 BC-10, PM-5).
- It is applied **identically to all three routes**, on the whole four-cell partition. It
  therefore cannot select a route — which is the specific property v1's Gate V lacked.
- The **disagreement-disclosure obligation of `befca0d` §2.3's final paragraph is NOT
  retained as a precondition** (`N1`/§0.1 response 1, corrected). What is retained is
  disclosure: the annotation is always computed and published, so an owner acts with it in
  view — but no licence's operativeness depends on its value.
- Its non-attributability is stated verbatim in any report: a large divergence is **not
  attributable** between "the surface does not reproduce the Held-out regime" and "an x86
  search differs from an ARM search", because cross-architecture search equivalence is
  unestablished (§13).

**T9 is NOT armed.** v1 §32 declared that any future amendment reintroducing *"a quantitative
Held-out-matching qualification"* re-arms `T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY`
automatically, and `CRITIC_SCIENCE` D13(2) correctly observed that v1's own Gate V **was**
such a requirement, merely positioned after the seal. Under Decision 1 there is **no**
quantitative Held-out-matching requirement anywhere in this protocol — not as a gate, not as
a veto, not as a necessary condition of any terminal. T9 does not arise. **The rule survives
unchanged: any future amendment that makes any Held-out comparison a necessary condition of
any terminal re-arms T9 automatically, and no weaker substitute comparison may be used to
dodge it.**

### 21.5 What a licence is, and is not

**A licence is PROPOSED by this protocol. It is ISSUED only by the protocol owner** (`S24`).
Ratification D2-ext states *"There is no automatic E4 re-entry"*, and every prior gate in this
programme was an owner act recorded by an analyst. v1's terminal fired on the protocol's own
adjudicated verdict and closed the loop without the owner. It no longer does:

> **Between the adjudicated verdict and any operative licence there is a mandatory
> protocol-owner ratification record naming the arm, the parameter setting, and the scope.
> Absent that record, the terminal is a proposal and nothing is licensed.**

That ratification record must contain, verbatim:

1. **The §21.4 annotation in full**, including its interval, **as disclosure only.**

   > **`G6` repair — this item is NOT a precondition, and v2's wording made it one.**
   > v2 required the annotation in the ratification record before a licence became operative,
   > making an **E2b-derived quantity a necessary condition of every licence**. That is the
   > prohibited channel *"use E2b to positively license an E4 arm"* running in reverse — E2b
   > could not grant a licence, but it could **withhold** one — and it contradicted §4.1
   > property (iii), *"No channel from E2b to the terminal state at all"*. §32.1 conceded the
   > obligation attached **asymmetrically**, because `pi_0`'s own argmax is `C+D`, so the two
   > non-`C+D` routes bore a burden route `C+D` did not.
   >
   > **Repaired:** the annotation is **published, quoted in full, and carried into the
   > record**, and it **conditions nothing**. No terminal, licence, gate or ratification
   > requirement depends on its value. A `CONTRADICTS` reading obliges the owner to nothing
   > and blocks nothing.
   >
   > `befca0d` §2.3's *"blocks adoption ... until explained"* is **not** discharged by this
   > item and is not claimed to be: that clause governs adoption of a **retention policy** on
   > **decision-admissible** evidence. This protocol adopts no policy and proposes rather than
   > issues. Conflating the two was v2's error.
2. For row 1 only: the owner's **re-arming of `f4c1105`** in place of its fired GATE 1 (§21.2
   note).
3. **Row 3 has no operative ratification item.** §21.2's `F16` disposition
   (`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`) means no licence is proposed on route `C+D` under
   this protocol, so there is nothing for an owner countersignature to activate. §36's
   population-by-reference restatement remains **written and available** for the day a
   separate ratification record authorizes E4f's execution; it is not itself a rider on any
   licence this protocol can currently issue.

**Three binding riders on every licence:**

1. **The E6 false-structure ceiling is a genuine precondition, named
   `E6_SAFETY_HEADROOM_PRESENT`.** `CRITIC_SCIENCE` `V3-C5` found four defects in how v3
   stated it: it is not actually in §20's `QUALIFIED` conjunction despite the claim that it
   is; `false_structure_events` was never defined; it was written as if parameterised by "the
   arm named by the certified route", though no route in §21.2 names an arm; and its
   denominator mixed DEV and EVAL. All four are fixed below, and the fix is **simpler than
   v3's statement**, not more complex: this protocol never selects or executes an arm — §12
   fixes retention to **`R0`, the frozen production `argmax(score)` control**, unconditionally
   and for every world, on every route. There is no arm to name because none is chosen from
   data.

   ```
   false_structure_events := count of NEG-stratum worlds, over ALL 230 evaluable
       opportunities (both DEV_ARM and EVAL_ARM halves), whose R0-retained cross-seed
       representative is flagged `false_null_structure` by that world's variant
       declaration (registry.py: F07's mass-only allowance, F19A's descriptor-link
       permutation, F19B's mass-preserving null -- each variant states in the
       registry what counts as false acceptance for IT). A section-14-persisted,
       seal-time count, evaluated by a function of this name that this protocol
       DECLARES and does not yet implement -- named here as a requirement on the
       Stage 1 scoring pass, not claimed as executed. Computed identically
       regardless of which route certifies, because R0 is fixed before any front is
       read (P10) and is never selected -- so using the full 230 is not double use
       of held-back evidence, unlike the D7 recovery contrast, which DOES select
       R*/V* from data and DOES require the DEV/EVAL split of section 26(3).

   E6_SAFETY_HEADROOM_PRESENT := wilson_upper_95(false_structure_events, 230) <= 0.15
                                 evaluated under BOTH resolutions
   ```

   **Not a member of `QUALIFIED`.** Folding it into §20 would make a safety-ceiling failure
   indistinguishable from a broken surface (`VOID_CONTROL_FAILURE`), destroying exactly the
   distinction the `*_NO_SAFETY_HEADROOM` terminals exist to preserve. It is instead a second,
   independent gate evaluated **inside §22's routing rules**, alongside `QUALIFIED` and Gate R
   — which is what the table in §22.1 already does; only the false "evaluated in §20" claim is
   withdrawn here.

   **The circularity v1 could not resolve is dissolved** (`D13(3)`, `S14`). v1 wrote that
   *"E6 is self-blocked pending exactly this hook"*, making every licence conditional and
   non-executable, and then froze around the open dependency. The resolution is that
   **E6-the-experiment is not needed; E6-the-ceiling is frozen text and is directly
   applicable here.** Verified by direct read at
   `git show befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3, lines 137–140: *"100 evaluable
   safety opportunities … unsafe acceptance Wilson upper <= 0.15 => change survives … > 0.15
   => VETO. Change rejected."* The opportunities come from this protocol's own NEG stratum:
   276 worlds (F07 mass-only truth, F19A/B/C null worlds), of which only the evaluable ones
   are the bar's denominator.

   > **`DEF-H7` repair — "evaluable safety opportunity" is defined, because v2 counted worlds
   > and the frozen registry disagrees.** `registry.py` declares `F19C`
   > (`scalar_truth_defined = False`, `m0_adequacy_truth = "not_applicable"`,
   > `expected_behavior = "trajectory destruction must be flagged non-evaluable"`)
   > **non-evaluable by design**. F19 cycles A/B/C over replicates, so over 138 replicates the
   > split is exactly **F19A 46 / F19B 46 / F19C 46** — verified against the registry, not
   > assumed — and **46 of the 276 NEG worlds are non-evaluable by construction**.
   >
   > ```
   > EVALUABLE SAFETY OPPORTUNITY := one NEG-stratum world whose variant declares
   >                                 scalar_truth_defined = True
   >                                 F07 138  +  F19A 46  +  F19B 46   =>   N = 230
   > ```
   >
   > `230 >= 100` clears the frozen bar by a factor of **2.30**, not the 2.76 v2 claimed, and
   > it is the full 230 (not a DEV/EVAL half) because `R0` is never selected. F19C worlds are
   > still generated, searched and reported under the `response_structure_diagnostic`
   > endpoint, but they are **not** in the safety denominator, because the frozen registry
   > says they cannot be.

   A surface whose R0 execution breaches `Wilson upper <= 0.15` on the **230 evaluable**
   opportunities licenses nothing on any route. No E6 execution is required and none is
   presumed.
2. **The licence is scoped to the regime characterised by the published descriptor vector
   (§19 D9), never to "Held-out".**
3. **If the four-way partition and the D7 recovery contrast disagree, that disagreement is
   itself a pre-declared reportable finding and REDUCES the proposal to conditional.** It is
   the direct generalisation of `H_partial`, stated first-class here for the same reason
   `befca0d` §2.1 stated `H_partial` first-class: so it cannot be discovered and then quietly
   absorbed.

## 22. FAILURE RULE — THE SOLE TERMINAL-ASSIGNING AUTHORITY

**§22 is the only section in this document that assigns a terminal state.** §18, §20 and §21
identify *which clause failed*; §22 names the terminal. v1 had three sections assigning three
different terminals to the same event, a `VOID` defined so as to subsume five named terminals,
one rule (F8) emitting two terminals, and one rule (F10) emitting none (`S8`). Every rule
below emits **exactly one** terminal, and the set is exhaustive.

### 22.1 Stage 1

| # | Condition | Terminal |
|---|---|---|
| # | Condition | Terminal |
|---|---|---|
| F0 | **Precedence rule, evaluated first. `#` IS the order — a literal list, not an inferred property of names.** Rules are checked `F1, F2, F3, … F17` in that exact printed sequence; the FIRST whose condition holds assigns the terminal; no later rule may re-assign it. **`CRITIC_SCIENCE` `V3-H1` / `CRITIC_GOVERNANCE` `N2` found "numerical order" undefined over `F10a`/`F12a`-style names and two terminals dead behind it as a result. Fixed by making `#` itself the ordering key and re-deriving every rule's position from a witness check, not from its label** (§31.1's verifier, run at freeze time, asserts every rule F1..F17 has >=1 witness (or is non-arithmetic and verified by construction) in this exact order -- executed by scripts/v2_reachability_verifier.py, PASSED (V3-H5)) | — |
| F1 | `C-0` fails **and** Route R-A is refused or also fails | `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` |
| F2 | `Q1` or `P9` fails for a mechanical reason (ordinal drift, **calibration-band collision under `NO-BAND-COLLISION`**, `GENERATOR_VERSION` mismatch, `pb_33`/`pb_34` non-zero, unauthorised protected-path drift). **`C-0` mismatch is NOT a member of this list** — it is F1's | `BENCHMARK_INTEGRITY_DEFECT` |
| F3 | `P7` fails: any `mass_power` world in the primary population | `SURFACE_POPULATION_CONTAMINATED` |
| F4 | `P1` or `P2` fails (composition or seed counts not exact) | `SURFACE_INCOMPLETE_COMPOSITION` |
| F5 | `P4` fails: schema incomplete at seal, or any field written after seal | `VOID_SCHEMA_INCOMPLETE` |
| F6 | Any of `C-1`, `C-2`, `C-3`, `C-4`, `C-5`, `C-6`, `C-6a`, `P3`, `P5`, `P8` fails | `VOID_CONTROL_FAILURE` |
| F7 | `P6'` fails: `INDETERMINATE_WORLDS > 0` on the calibration surface after uncapped escalation | `VOID_INSTRUMENT_INDETERMINATE` |
| F8 | `P10` fails: more than one SURFACE generated, or the tuning ledger is non-empty, or any protocol amendment is written after the first surface exists | `VOID_SINGLE_SHOT_BROKEN` |
| F9 | `QUALIFIED` and `S_1 = 0` (no world reached the front under either resolution). **Evaluated BEFORE any Gate R row is consulted**, because at `S_1 = 0`, `pi = (1,0,0,0)` satisfies Gate R row 2's certification arithmetic exactly (`CRITIC_SCIENCE` `V3-C1`: lead `= 1.0 ≥ delta`, `LCB = 1.0 > 0`), so a rule reading Gate R could never reach this state — placing `F9` here, not after F13, is the entire repair | `SURFACE_DEGENERATE_NO_FRONT` |
| F10 | `QUALIFIED` and Gate R row 5 | `ROUTING_INDETERMINATE` |
| F11 | `QUALIFIED` and Gate R row 4 | `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` |
| F12 | `QUALIFIED` and Gate R row 1 and `E6_SAFETY_HEADROOM_PRESENT` (§21.5) | `E4A_ENTRY_LICENCE_PROPOSED` |
| F13 | `QUALIFIED` and Gate R row 1 and **not** `E6_SAFETY_HEADROOM_PRESENT` | `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` |
| F14 | `QUALIFIED` and Gate R row 2 and `E6_SAFETY_HEADROOM_PRESENT` | `E4_GENERATION_LICENCE_PROPOSED_F09_F10` |

**Rules F15–F17 below govern route `C+D` and the D3/ratification rider, and are stated
separately from the F1–F14 table above because §2.1's `N6` correction changed what they
assign.**

| # | Condition | Terminal |
|---|---|---|
| F15 | `QUALIFIED` and Gate R row 2 and **not** `E6_SAFETY_HEADROOM_PRESENT` | `E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` |
| F16 | `QUALIFIED` and Gate R row 3 (certified argmax `C+D`). **§2.1 `N6`: E4f is not authorized to execute today** — no protocol-owner ratification record for the delegation exists, and no E4f hostile review has been performed. No `E6` headroom question, no population-reference question and no `E4F_*` terminal arises, because nothing is proposed on this route to condition — v3's `F12a` unreachability finding (`CRITIC_GOVERNANCE` `N2`) is closed by removing what it protected, not by reordering it | `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` |
| F17 | The protocol owner concludes that `befca0d` §2.3 combined with D6 admits no qualification that is both non-circular and non-vacuous | `T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS` |

**`D3_ITEMS_UNMET_NO_REENTRY` is DELETED as a terminal** (`CRITIC_SCIENCE` `V3-C2`, option (a),
taken because it is the honest reading: Gate R's five rows are exhaustive, so under `F0` some
rule in `F10..F16` always fires and a dedicated terminal for "D3 unmet" has no witness under
any ordering). It survives as a **mandatory rider**, attached to every proposing rule
(`F12`–`F16`): *any of D3's eight `EXPERIMENTAL_REENTRY_RESOLUTION` items unmet, or the §21.5
owner ratification refused or not produced, is reported against the named terminal and
prevents it from becoming an operative licence — the terminal is still published, and it is
still a proposal, never an adoption, exactly as §21.5 already states for every route.* This
changes nothing about what "licence" means; it only removes the fiction that a refusal is a
*different* terminal than the proposal it refuses.

**`VOID` is not a terminal in this protocol.** It was a residual category in v1 that swallowed
five named states. The four `VOID_*` terminals above are named for the specific failure they
report.

**There is no rehabilitation path from `VOID_SCHEMA_INCOMPLETE`, `VOID_CONTROL_FAILURE`,
`VOID_INSTRUMENT_INDETERMINATE` or `VOID_SINGLE_SHOT_BROKEN`.** A non-empty tuning ledger is
not a disclosure that rehabilitates the design; it is the measurement of how much fitting
occurred.

**`SURFACE` is defined, closing `S20`:** one **independently parameterised** surface. The
`C-0`→R-A ladder of §5.2–§5.3 is **one** surface attempted under at most two construction
routes with **identical** parameters, and both attempts are recorded in the ledger. v1 also
counted its blinded top-up against F9; the top-up is deleted (§0.4), so the ambiguity is gone.

### 22.2 Stage 0 — a disjoint terminal set, sealed separately

Stage 0 is the D-INST protocol (§0.5). Its terminals are D-INST's own and are **not** members
of §32's set:

| Terminal | Meaning | Effect on Stage 1 |
|---|---|---|
| `D-INST-DETERMINATE` | Every affected E2a world's stage is invariant | Stage 1 may proceed |
| `D-INST-INDETERMINATE` | ≥1 affected E2a world's stage is not invariant after **uncapped** tier-2 escalation | **`T-INSTRUMENT-UNBOUNDED-ON-E2A`. Stage 1 forbidden** |
| `D-INST-PLURALITY-NOT-INVARIANT` | E2a's routing predicate differs between LOWER and UPPER | Reported. Does **not** by itself forbid Stage 1; it is a fact about E2a, which D5 has already invalidated |
| *(operational, NOT a terminal)* `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` | Any **decisive** pair still unresolved after uncapped escalation | **No scientific terminal is emitted, no seal is written, Stage 1 neither proceeds nor is forbidden.** §25.4 |

**The instrument must emit a member of this set and nothing else, and v2's did not**
(`CRITIC_GOVERNANCE` `G4`, `CRITIC_SCIENCE` `DEF-C2`). v2's tool emitted
`D-INST-NO-WORLD-MOVED` / `D-INST-{n}-WORLDS-RECLASSIFIED`, neither of which appears above,
leaving the map onto the declared set to post-result analyst discretion **on the gate that
admits Stage 1**. Worse, it keyed the terminal on `moved_lo == 0` computed at the LOWER
resolution while computing `determinate` and discarding it, so a run in which **nothing
resolved** emitted the benign terminal — and that had already fired on a null run.

**Binding on the instrument, and now enforced in code by an assertion:**

1. The emitted terminal is a member of the table above, asserted at emission.
2. It is keyed on **determinacy**, never on `moved_lo`, which is retained as a diagnostic.
3. A run in which every pair is `UNRESOLVED` **cannot** emit a pass terminal, enforced by an
   explicit refusal.
4. §25.4 has **absolute precedence**: any residual decisive-unresolved pair produces the
   operational state and **no** terminal.

**A consequence stated rather than hidden.** With tier 2 genuinely uncapped,
`D-INST-INDETERMINATE` is **unreachable by construction**: a world stays indeterminate only by
holding an unresolved row, and after uncapped escalation an unresolved row can only be an
envelope event, which rule 4 has already claimed. Mathematical indeterminacy does not survive
removal of the cap. What v1 and v2 called *"the instrument is unbounded"* is really *"this
host is too small"*, which §25.4 already forbids from being a scientific finding. The terminal
is retained in the declared set, its unreachability is reported in the result object, and no
part of this protocol depends on it firing.

## 23. TIE RULE

**REUSED from `f4c1105` §4, adopted rather than restated, so that no boundary case is
silently redefined.**

- **"Strict plurality" means strictly greater than each of the other aggregates. Equality is
  NOT a plurality.** Under §21.1 the bar is stronger still: strictly greater **by at least
  `delta`**, with a positive lower confidence bound.
- A tie, a near-tie, or any configuration failing `ROUTING_CERTIFIED` falls to Gate R row 4 or
  row 5: every metric is reported, and the adoption rule is **suspended pending a *named*
  tie-breaking review**.
- **Inventing a tie-break after seeing counts that produced a tie is prohibited** (P2 PM-12).
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
| `INDETERMINATE` world (class not invariant after uncapped escalation) | **Its own state**, counted and sealed. `INDETERMINATE_WORLDS > 0` ⟹ `VOID_INSTRUMENT_INDETERMINATE` (§22 F6). Never silently folded |
| Parse failure (`parse_ok = false`) | `INCORRECT`. Deterministic, host-invariant, already the frozen semantics. **Not** `UNRESOLVED` |
| `invalid_fraction > MAX_INVALID_FRACTION = 0.005` | Excluded from the retained set by the frozen rule (`befca0d` §3.4), **plus** the direct check that an invalid candidate never outscores a valid one. REUSED |
| Search execution failure (world produces no front) | **Regenerate under the same frozen seed.** A missing world breaks `P1`. Count reported |
| Seed `EXECUTION_FAILURE` / `COMPLETED_NO_CANDIDATE` | Handled by the frozen `build_seed_selections` path unchanged; counted per world; a world with fewer than 30 completed seeds fails `P2` |
| World failing any control | **Quarantined and reported, never silently dropped.** REUSED from `befca0d` §2.5.3 |
| Resource exhaustion during escalation | **§25.4. Not a category of this table, because it produces no scientific state at all** |
| Denominator convention | Every rate has denominator `n = 1656` (G2 primary) or 276 (NEG stratum). `INDETERMINATE` worlds are reported **separately** and are **never folded into "not recovered"**. The sensitivity of every routing comparison to **both** extreme resolutions is reported alongside every point estimate, exactly as the Gate 1 adjudication reported its enumeration |

## 25. TIMEOUT / RESOURCE HANDLING

> **THE GOVERNING RULE OF THIS SECTION, NOW WITHOUT EXCEPTION: NO WALL-CLOCK CAP, MEMORY CAP,
> WORKER-COUNT CHOICE, HOST-LOAD CONDITION, CPU MODEL OR COMPUTE BUDGET MAY DECIDE A
> SCIENTIFIC LABEL OR A SCIENTIFIC TERMINAL ANYWHERE IN THIS PROTOCOL, AT ANY LEVEL,
> INCLUDING META-LEVEL TERMINALS.**

`SIMPLIFY_TIMEOUT_SECONDS = 5` is **retired as a classification rule.** It is the documented
root cause of `NEW_CLOUD_HOST_PARITY_FAILED` — *"the same unmodified classifier assigns a
different scientific label to the same expression purely as a function of host speed"*,
`not_floating_point: true`.

### 25.1 The determinacy bound (P2 §3.2's MANDATORY CORRECTION, all six conditions)

Executed through the machinery of `scripts/e2b_bounded_determinacy_evaluator.py`, already
hostile-audited in the sealed Gate 1 adjudication. **Retained unchanged from v1 —
`CRITIC_SCIENCE` attacked the monotonicity lemma at the code level as §30 requires and could
not construct a counterexample (its CREDITS item 1); `CRITIC_GOVERNANCE` check 14 recorded
this section as the strongest in the document.**

1. `g2_contract.py` and the classification **semantics** are **byte-unchanged**; only the
   control flow around unresolved rows changes.
2. The bound is proven to **over-approximate**: a class is emitted **only when it is
   invariant over every resolution of every unresolved row**. Under the monotonicity lemma
   this reduces to two evaluations rather than `2^U` — `correct_on_front` and
   `retained_correct` are disjunctions over row labels, hence monotone; the cross-seed
   representative is selected by `identity_contract.template_key` grouping and **never reads
   `g2_correct`**; `retained_by_argmax_score` is a score comparison, also label-independent.
   So a resolution can only move a world **weakly later** in the frozen order
   `A ≺ B ≺ C/D ≺ E`.
3. Rows that are **decisive** under that enumeration are **escalated to completion, not
   guessed**.
4. A residual undecidable world is emitted as explicit `INDETERMINATE`, never folded, with
   the pre-declared bar `INDETERMINATE_WORLDS == 0` above which the run terminates at
   `VOID_INSTRUMENT_INDETERMINATE`.
5. The implementation is validated against **uncapped ground truth** on the pre-declared
   101-row sample, with the sample and the pass bar (**100%**) frozen before execution.
6. The whole correction is **hash-frozen before any new world is generated** and applies
   **identically** to every surface any comparison touches — including Stage 0.

### 25.2 The two-tier budget

- **Tier 1 — CPU time, not wall clock.** `time.process_time` budget of **60 s per distinct
  expression**. **DECLARED, not derived** (`S4`, adopted): it is 12× the retired frozen 5 s,
  expressed in CPU time so it is not a function of load or co-tenancy, and **the multiplier
  12 has no frozen source**. It is a **cost** bound only; exceeding it produces `UNRESOLVED`,
  **never a label**. It is listed in §34 as a free parameter.
- **Tier 2 — uncapped escalation.** Any expression still unresolved **and decisive** — i.e.
  whose resolution changes some world's stage under the monotone bound — is escalated with
  **no time cap**. Precedent: Gate 1 escalated 6 decisive expressions at 5.5–21.8 s each.
- The cap exception derives from **`BaseException`**, deliberately, so that `g2_contract`'s
  seven `except Exception: return None` handlers cannot swallow it and silently turn a cap
  into `SUPPORT_UNRESOLVED → not-correct`.

### 25.3 The sealed table — correctly keyed

v1 asserted a *"sealed expression → label table"* making the label *"a pure function of the
expression string"*. `CRITIC_SCIENCE` D9 showed this is false: `g2_contract.classify_support`
and `classify_family_match` compare a candidate against **the world's truth**, so
`g2_correct = f(expression, truth)`, and trivial expressions recur across worlds with
incompatible truths. **Corrected and stated explicitly:**

```
CANONICALISATION TABLE   key: expression_string
                       value: ( canonicalization_status , effective_support ,
                                discovered_family )
        -- each a function of the expression ALONE. Computed once, escalated to
           completion, hashed, committed.

g2_correct(row, world)  is then computed per (row, world) from the table entry and the
        world's TruthRecord, by the imported, byte-unchanged g2_contract primitives.
```

Only the **canonicalisation table** is claimed to be architecture-portable, and only it is
sealed as a hash. This is the object `C-6` checks.

### 25.4 Resource exhaustion produces NO scientific state — the `D6` repair

v1 mandated a per-worker RSS ceiling while declaring tier 2 "uncapped", and routed the
resulting `UNRESOLVED` on a decisive expression into `INDETERMINATE_WORLDS > 0` and thence
into terminal `T-INSTRUMENT-UNBOUNDED`, described as *"a finding about the **contract**"*.
**A host RAM limit therefore produced a published scientific finding about the G2 contract**
— the wall-clock defect reproduced one level up, in the section that forbids it. The trigger
is measured, not hypothetical (§10.6).

**The repair, and it is structural rather than a renaming:**

```
RUN_INCOMPLETE_RESOURCE_EXHAUSTION
   -- an OPERATIONAL STATE. Explicitly NOT a member of the §32 terminal set. Explicitly
      NOT a finding about the G2 contract, the pipeline, the surface, or the instrument.
```

When any escalation exhausts the declared RSS ceiling, the host's memory, or any other
resource envelope:

1. Execution **suspends**. **No seal is written. No routing verdict is computed. No
   scientific label, terminal or meta-terminal of any kind is emitted.**
2. The protocol publishes: the offending expression strings, the RSS ceiling, the host's
   total memory and CPU model, the elapsed CPU time per offending expression, and the count
   of worlds whose class remains undetermined.
3. The run may be **resumed on a larger host** under the **identical frozen protocol hash**,
   with the tuning ledger still empty and the published expression set unchanged. **This is
   not a retry and does not violate `P10`**, because nothing scientific was read: the seal was
   never opened and no verdict existed to be re-rolled. The resumption is recorded in the
   event log with the before/after host envelopes.

   > **`DEF-H9` repair — in v2 this escape was inoperative, making the state absorbing.**
   > v2 froze `RSS_CEILING_GIB = 24` as an **in-process** ceiling. Moving to a larger host
   > therefore changed nothing: the in-process ceiling fired at 24 GiB on a 2 TB machine
   > exactly as on a 47 GiB one, and **raising** it was a tuning-ledger entry that fires `F7`
   > `VOID_SINGLE_SHOT_BROKEN`. So the only two exits from the memory tail were an unreachable
   > resume and a terminal void.
   >
   > **Repaired: the ceiling is a declared FUNCTION OF THE HOST, fixed before Stage 0, not a
   > constant.**
   >
   > ```
   > RSS_CEILING_GIB(host) := min( 0.50 * total_physical_GiB(host) , 24 * scale(host) )
   >   where scale(host) = max(1, floor(total_physical_GiB(host) / 47))
   >
   >   on this host (47 GiB):  scale = 1  ->  min(23.5, 24)  =  23.5 GiB
   > ```
   >
   > The **rule** is frozen; the **value** is derived from the host it runs on, exactly as
   > §5.2's seed-band base is a frozen rule evaluating to a derived value. Recording the host
   > envelope and the evaluated ceiling is mandatory and is **not** a tuning entry, because no
   > threshold, margin, gate, estimator, terminal or decision rule moves — only the size of
   > the machine. `WORKER_COUNT` is bound with it, closing the arithmetic hole that
   > `8 x 24 = 192 GiB` on a 47 GiB host was never satisfiable in the first place
   > (`EXECUTOR_FINDINGS` `X-2`):
   >
   > ```
   > WORKER_COUNT(host) := max(1, floor( 0.85 * total_physical_GiB(host)
   >                                     / RSS_CEILING_GIB(host) ))
   >   on this host:  floor(39.95 / 23.5) = 1
   > ```
   >
   > **A single ceiling for both phases is what produced `WORKER_COUNT = 1`, and that was
   > wrong.** Applied to this host the rule gives `floor(0.85 x 47 / 23.5) = 1`, which would
   > make 57,960 searches infeasible and turn a **resource envelope into a de-facto terminal**
   > — precisely what this section forbids. The 24 GiB figure was always motivated by the
   > sympy **canonicalisation** tail (one E2a pair measured 44.4 GB), never by PySR **search**.
   > The two phases have different memory profiles and must carry different declarations.
   >
   > **Profiled on the E2a engineering DEV set (§26(1), permitted and already fully seen),
   > published in `STAGE1_RESOURCE_PROFILE.json`, and frozen BEFORE Stage 0 executes**, which
   > is what §13 `A4` requires and what `DEF-M5` found v2 asserting without a record. Measured:
   > 12 searches, all completed, wall mean **5.1 s** / median 3.6 s / max 21.8 s, peak RSS for
   > the **entire** process **0.958 GiB**.
   >
   > ```
   >                    RSS_CEILING_GIB   WORKER_COUNT     envelope (<= 39.95 GiB)
   >   search phase           2.0              19             38.0   OK
   >   scoring tier 1         4.0               9             36.0   OK
   >   scoring tier 2        23.5               1             23.5   OK
   > ```
   >
   > Search: `2.0` is 2x the measured peak; `19 = min(floor(0.85 x 47 / 2.0), cpus - 5)`.
   > Tier 2 is **uncapped in time and serial in memory**, which is the correct shape for a
   > tail whose worst observed case is 44.4 GB. Projected Stage 1 search cost: **82.1 CPU-hours,
   > 4.3 wall-hours at 19 workers**. Scoring cost is deliberately **not** projected, because
   > its tail is exactly what Stage 0 measures and `A4` forbids Stage 0's cost from feeding
   > Stage 1's concurrency — the scoring concurrency above is declared from the DEV profile
   > alone.
   >
   > **All six numbers are frozen.** Changing any of them after Stage 0 reports is a
   > tuning-ledger entry and voids the surface under `P10`.
4. If no attainable host resolves the expressions, the protocol terminates in
   `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` **and publishes no scientific conclusion whatsoever**
   — not about the contract, not about the pipeline, not about decidability. The published
   artifact is the expression set and the host envelope, and nothing else.

**No compute ceiling is declared anywhere in this protocol** (§10.6).
`SYNTHESIS_DECISION_RECORD.md` §10's 260 CPU-hour figure is withdrawn as non-binding.

### 25.5 Resource handling that is explicitly not a classification, and is frozen early

**This section's numbers were superseded and are DELETED here rather than left stale a fourth
time** (`CRITIC_SCIENCE` `V3-H2`: this section still read `RSS_CEILING_GIB = 24` /
`WORKER_COUNT = 8` — the in-process constant `DEF-H9` condemned, an unsubstantiated "profiled"
claim `DEF-M5` condemned, and the `8 x 24 = 192 GiB` arithmetic on a 47 GiB host `X-2`
condemned — while §25.4 and `STAGE1_RESOURCE_PROFILE.json` declared the correct per-phase
values three sections earlier). Every clause that cites *"the §25.5 resource parameters"*
(§26(1), §31.1, §34 FP-3/FP-4) is repointed to **§25.4's per-phase table** and
`STAGE1_RESOURCE_PROFILE.json`, which is the single place these numbers are declared:

```
                       RSS_CEILING_GIB   WORKER_COUNT     envelope (<= 39.95 GiB)
  search phase              2.0              19              38.0   OK
  scoring tier 1            4.0               9              36.0   OK
  scoring tier 2           23.5               1              23.5   OK
```

Separate systemd scopes per shard, the smoke-tested watchdog, and world-level checkpointing
with byte-exact resume are **retained unchanged from this section's original text** and are
not numeric parameters, so they carry no staleness risk. **A world lost to an infrastructure
failure is regenerated under the same frozen seed and reported; it is never reclassified,
imputed, or dropped.**

**Process note, so a fifth staleness cannot recur unnoticed.** Three prior versions of this
protocol declared resource numbers in one place and updated them in another
(`DINST_FREEZE_SHA256.txt` → `_v2` → `_POSTREPAIR` for the Stage 0 tool alone). §31.1's
freeze-time verifier now **asserts numeric equality** between every section that cites a
resource parameter and the single source (`STAGE1_RESOURCE_PROFILE.json` for Stage 1,
the instrument's own emitted value for Stage 0) and refuses to freeze on any mismatch.

## 26. DEV / EVAL SEPARATION

Three distinct separations, for three distinct purposes. Each is deterministic, pre-declared,
stratified, and uses **no RNG**.

**(1) Engineering DEV — free, and it should be taken (P3 §7.3).**
`DEV_ENGINEERING = the sealed E2a corpus`. E2a is fully seen, hostile-audited, and ratified as
**invalidated for calibration (D5)**, which makes it worthless as evidence and ideal as an
engineering dev set. The bounded evaluator, escalation protocol, schema validator, bootstrap
harness, memory governor, **the §25.4/§25.5 resource parameters** and runtime profiling are
developed and debugged against it at **zero additional scientific compute and zero leakage**.
**The analysis code and the resource parameters are frozen and hashed against E2a before
Stage 0 runs and before the first Stage 1 world is generated.**

**(2) The primary is computed on the FULL G2 population, not on a split.**
REUSED from `f4c1105` §6: the gate is a diagnostic fact about the surface's own attribution.
No split is required for the alpha to be valid, because the qualification rule, the margin,
the routing rule, the conditioning set and the endpoints are **all frozen before any world
exists**, and qualification → routing is fixed-sequence gatekeeping.

**(3) Arm-selection DEV/EVAL, for the SECONDARY recovery contrast (D7) and for E4f.**
Deterministic by replicate index, fixed before any front is read:

```
DEV_ARM  = replicates r000 .. r068   (828 G2 worlds ; 138 NEG worlds)
EVAL_ARM = replicates r069 .. r137   (828 G2 worlds ; 138 NEG worlds)
```

`69 = 23 x 3`, so F19's three-variant cycle is exactly balanced in **each** half — which is
the reason `R` must be divisible by 6 (§10.4).

`R*` and `V*` are **selected on DEV_ARM** by the frozen `befca0d` §3.1/§3.6 decision rule
(*simplest rule whose G2 improvement over control has a Wilson lower bound above 0 and whose
`false_structure_rate` stays under the E6 ceiling; ties broken by fewest free parameters, then
lowest false structure*), and **measured on EVAL_ARM**. Without this split the contrast is
structurally biased toward retention, which has 4 arm-types spanning 9 parameter settings
against voting's 2 — a bias that would be invisible and would point at E4a.

**EVAL is scored exactly once. There is no second look.**

## 27. MULTIPLE-COMPARISON CONTROL

**Two-layer structure, REUSED from `f4c1105` §8, with v1's false theorem corrected.**

- **Qualification → routing: no adjustment, and this part IS a theorem.** Qualification is a
  **conjunction** of binary structural clauses, and qualification → routing is a
  **fixed-sequence (hierarchical gatekeeping)** procedure, which preserves the family-wise
  error rate without adjustment. Routing is read **only if** qualification passes.
- **Routing certification: NOT one comparison, and v1's claim that it was is withdrawn.**
  `pi_top` and `pi_second` are **selected by the data**, so the contrast is a two-sided
  comparison read one-sided. The correction is the critical value `z_.975` (§10.2), not a
  Holm adjustment, because there is one *decision* even though the contrast is selected. The
  realised type-I rate under the composite rule is **0.0024** at the 2-way tie and **0.0001**
  at the 3-way tie (§10.5), i.e. conservative, and this is reported rather than claimed as
  exactness.
- **Secondary diagnostics D3 and D4:** development-only pre-reduction of internal grids,
  **plus Holm–Bonferroni at `alpha = 0.05`** across the head-to-head comparisons within each
  family, with **unadjusted CIs reported alongside**. REUSED verbatim.
- **Secondary recovery contrast D7:** simultaneous paired intervals (exact McNemar on
  discordant pairs plus case-level bootstrap 95% CI, `B = 10,000`, resampling within EVAL_ARM
  only), **Holm-adjusted across the three comparisons**, family-wise `alpha = 0.05`. REUSED.
- **D1–D2, D5–D6, D8–D11 are descriptive** and carry no adjustment because they gate nothing.

## 28. REPLAY / IDENTITY CONTROL

**REUSED VERBATIM. `befca0d` §2.5.1; `f4c1105` §9.1. A hard gate before any record is used —
including before any record is *reported*.**

- **C-0 Generator equivalence.** 380/380 byte-identical `content_hash` against
  `generator.generate_case` (§5.2). Re-run at preflight and at seal.
- **C-1 Retention identity.** The instrumented engine's `argmax(score)`-retained candidate
  must be **byte-identical** to the frozen production path's, for **every seed** on the
  declared 30-world control set. *"Instrumentation that changes the search is not
  instrumentation."* Answerable against the production pipeline, not against the attribution.
- **R0 replay self-consistency** (`f4c1105` §9 control 1). The re-scoring pipeline scored
  under R0 must reproduce the surface's own sealed A/B/C/D/E counts and `selection_count`
  values **exactly**. Any discrepancy is a **defect in the implementation, not a finding**,
  and blocks all results.
- **C-5 Determinism replay.** 30 worlds × 30 seeds re-executed on this host, requiring
  byte-identity. Precedent: 30/30.
- **Host determinism, twice** (§13 A3): the 10-case × 30-seed control subset run twice with
  byte-identical fronts.
- **C-6 Two-architecture canonicalisation parity — MANDATORY, NOT WAIVABLE** (`D9`). v1 made
  its parity obligation *"discharged by construction and unverified by execution"* if a second
  architecture was unreachable — and §13 already records `worlds_executed_on_this_host: 0`,
  so the waiver was the **expected** path, against a **demonstrated** cross-host divergence.
  Under §25.3 the object requiring parity is the **canonicalisation table**, which needs **no
  search** to reproduce: it is a pure function of expression strings. A pre-declared
  **`DEF-M9` guard, added because `C-6` is mandatory, non-waivable, and has no rehabilitation
  path:** `C-6` is **smoke-tested on a 5-expression sample during §12's hard preflight, before
  world 1**. If no second architecture is reachable at preflight, the run **does not start**,
  and the outcome is a scheduling fact rather than `VOID_CONTROL_FAILURE` after 63 CPU-hours.
  A control whose satisfiability is unknown until seal time is a coin flip on the whole
  surface. The full
  500-expression audit sample is therefore re-computed on a second architecture — a laptop, a
  container on a different CPU family, or a cloud instance — at negligible cost. **0
  mismatches required. If no second architecture can be reached, `C-6` FAILS and the terminal
  is `VOID_CONTROL_FAILURE`.** An unverifiable parity claim is not a control.
- **Artifact reconciliation.** A manifest with SHA-256 for every produced artifact, verified
  after writing, with a recorded statement that **no sealed evidence was modified** — matching
  the discipline at `ARTIFACT_SHA256.txt` and `RATIFICATION_VERIFICATION.json`.

## 29. INDEPENDENT ADJUDICATOR

**D3 item 6 requires an independent adjudication procedure. A table saying "named before
execution" does not satisfy it** (`S13`). The four parties are **registered by name in the
freeze commit**, each with agent identity, model, invocation context, and an explicit
statement of what it may and may not read. Until that registration exists, D3 item 6 is
**PENDING** and no verdict issued is admissible.

| Role | Requirement |
|---|---|
| **ADJUDICATOR** | Registered by name in the freeze commit. Independent of the design author. Applies the frozen §20/§21 predicates mechanically to the sealed artifacts and produces a **signed verdict**. May not modify any predicate. May not compute the §21.4 annotation |
| **ANNOTATION ADJUDICATOR** | A **different** registered party. Computes §21.4 **once**, after Gate R's hash is chained. May not modify Gate R's verdict, and its output is not an input to any terminal |
| **CRITIC_A (scientific)** | Independent. Must return PASS |
| **CRITIC_B (governance / leakage)** | Independent. Must return PASS |

**Order enforcement is mechanical, and its strength is stated honestly.** Gate R is computed
by an isolated process which writes a hash-sealed verdict and appends it to a hash-chained
event log (the `AUTONOMOUS_RUN_EVENT_LOG.jsonl` pattern). `git merge-base --is-ancestor
<route-commit> <annotation-commit>` must hold. **This proves ARTIFACT order, not INFORMATION
order.** `pi_0` is printed verbatim in the ratification record and in §21.4 of this document,
which every party reads. The information barrier is zero; only the artifact barrier is real,
and that is the only claim made. Under Decision 1 the consequence of this weakness is small,
because the annotation controls no terminal — which is itself an argument for Decision 1.

**`UNRESOLVED_DEFECTS` must be 0 at verdict time**, as it was at Gate 1.

## 30. HOSTILE REVIEW REQUIREMENT

**Two hostile reviews, twice: against the design before freeze, and against the result before
the verdict is accepted.** The pre-freeze reviews of v1 (`CRITIC_SCIENCE_REENTRY.md`,
`CRITIC_GOVERNANCE_REENTRY.md`) both returned **FAIL** and produced this version. **They do
not discharge this section for v2**; v2 must be reviewed on its own terms.

**Mandatory attack surface for the v2 pre-freeze review, enumerated so it cannot be skipped:**

1. **Attack Q1's provenance argument, BLIND.** An independent agent, **blind to §3 item 1's
   quantitative composition statement and to `SYNTHESIS_DECISION_RECORD.md` §1.3**, must
   re-derive the population rule from `registry.py` and the v1-sealed taxonomy alone. If that
   agent reaches the same twelve-condition population, the charge *"you matched composition
   because you saw that matching composition moves E2a toward E2b"* is answered by
   **replication rather than by argument**. If it does not, the charge stands and the
   population must be re-argued before freeze. **This is `S16`'s outstanding item and it has
   not yet been performed.** **`DEF-M6`: STALE, and corrected here — the blind re-derivation WAS performed and is recorded in `S16_BLIND_COMPOSITION_DERIVATION.md` at commit `b4ea2a0`. Its rule selects exactly the twelve G2 families, with zero free parameters, recoverable from `registry.py` and `generator.py` alone. Note the blindness qualification in §0.8 (`G11`): the task brief quoted `pi_0`, the document discloses this at its own item 4, and `pi_0` is used nowhere in the derivation.**
2. **Attack the determinacy bound's monotonicity lemma** (§25.1 condition 2) at the code
   level, and attack §0.4's claimed equivalence
   `INDETERMINATE_WORLDS == 0 <=> g_1 = g_2 = g_3 = 0` by attempting to construct a
   cancellation.
3. **Attack the §32.1 non-determination witnesses** — verify each against every Gate Q clause
   and against §21.1, and attempt to show that Gate Q constrains the reachable
   `(pi_A, pi_B, pi_C+D)` region.
4. **Attack Decision 1 as an authority argument.** Attempt to show that `befca0d` §2.3's final
   paragraph requires a mechanical veto rather than the §21.5 disclosure obligation, or that
   the §21.4 annotation is extensionally a selector after all.
5. **Attack Route R-B as a circumvention.** Verify `C-0` independently; verify that `pb_33`
   and `pb_34` pass; attempt to show that a new module declaring an out-of-registry population
   defeats the purpose of the content freeze rather than honouring it.
6. **Attack the single-shot claim** — count surface manifests; audit the tuning ledger; check
   `git merge-base` ancestry; attack §25.4's resumption rule as a disguised retry.
7. **Attack every branch of §21.2 and §22 for a route to a non-executable arm that is not
   pre-labelled, and for a terminal that is unreachable, overlapping, or misnamed.**
8. **Attack the E4f coupling** — verify §36's restatement is results-blind and pre-route, and
   attempt to show it constitutes tuning under E4f's own §13.

**A review that returns PASS without engaging all eight is not a hostile review and does not
discharge this section.**

## 31. HASH / FREEZE PROCEDURE

**D3 item 7: results-blind freeze before any new outcome is inspected. NOT YET PERFORMED.**
v1 asserted *"Status at this commit: frozen protocol text"* while §31 was entirely unexecuted
(`S12`). This document asserts the opposite on its first page.

1. **Freeze commit.** This document, the routing table, the acceptance predicate, the failure
   rules, the tie rules, the schema validator's hard-coded field list, `scripts/v2_reachability_verifier.py` (section 32.1's witness verifier, EXECUTED:
   terminal-set equality PASSED, all 8 arithmetic rules F9-F16 REACHABLE),
   `scripts/v2_truth_blind_verifier.py` (section 16 P8a, EXECUTED: 0 call-graph violations
   over 16 modules), `scripts/v2_freeze_dinst.py` (generates D-INST's freeze record from the
   live tool, closing the four-times-stale pattern -- N4), the two new modules of §5.2, the
   §25.4/§25.5 resource parameters and **all analysis code** are committed and their SHA-256 hashes recorded in a manifest. The freeze commit
   must be a **strict ancestor** of the first data commit. Verified by
   `git merge-base --is-ancestor` and by re-verifying every recorded hash. An annotated tag
   `muru-freeze/e7-protocol-v2` is created.
2. **Tuning ledger.** A ledger recording every parameter changed after this freeze, with the
   reason and the evidence consulted, is registered at the freeze commit. It **must be empty
   at execution time**. A non-empty ledger fires §22 F7.
3. **Generator ancestry (P2 T-a/T-b/BC-3).** Every generator parameter is either bit-identical
   to a value already fixed in a commit that is a **strict ancestor of the first commit
   containing any E2b front**, or is set by a registered **rule** that provably never reads
   Held-out (here: *"the value the frozen registry already declares"*, and for the seed band
   *"`A35_SEARCH_SEED_MAX + 1`"*). **The rule is registered, and the value is derived from
   it** — never chosen.
4. **Surface count.** An auditable integer. **Exactly one.**
5. **Order seals.** Gate R's verdict is hashed and appended to the hash-chained event log
   before the §21.4 annotation exists. The annotation's artifact commit must be a strict
   descendant.
6. **Post-execution reconciliation.** SHA-256 manifest for every produced artifact, verified
   after writing; `git status` on `results/` empty for all pre-existing sealed evidence; an
   explicit recorded statement that **no sealed evidence was modified**; `pb_33` and `pb_34`
   re-run and recorded.
7. **Stage 0 is sealed separately** and is stamped `EXPLANATORY_ONLY` at the record level. The
   static citation checker must reject any change citing a Stage 0 identifier.
8. **Superseding stale freeze records, and disclosing this document's own executions.**
   - **The freeze record is now GENERATED, not hand-edited.** `DINST_FREEZE_SHA256.txt`,
     `DINST_FREEZE_SHA256_POSTREPAIR.txt` and `DINST_FREEZE_ADDENDUM.md`'s "binding amendment"
     each went stale the moment the tool changed after they were written — a **fourth**
     consecutive occurrence (`14a50d51` → `a3f97e38` → `9826cefe` → `1f8d4b4a`)
     (`CRITIC_GOVERNANCE` `G10`/`N4`). A record that must be remembered and hand-rewritten on
     every tool change will always be one edit behind the tool. `scripts/v2_freeze_dinst.py`
     computes the hash, the pinned constants and the binding statement **from the live
     file**, and writes `DINST_FREEZE_CURRENT.txt`. **This is the only file this protocol
     treats as authoritative for D-INST admissibility.** The three earlier files are retained
     as an audit trail of the staleness pattern itself and are explicitly **not** binding.
     `v2_freeze_dinst.py` is run after any change to `e2a_instrument_diagnostic.py` and before
     Stage 0 executes; it is idempotent and its own output states whether the tool has
     uncommitted changes, so a stale freeze cannot be committed silently. The D-INST
     **protocol text** must also be re-frozen or formally amended against its own failed
     review (`DINST_REVIEW = FAIL` named blocking defects D3–D6 against the protocol, not
     only the tool).
   - **`S21`: Stage 0's classify cache** (`~/e2_x86_cache/classify_cache.sqlite3`, ~89 MB,
     not in git, freely mutable) is in Stage 0's gating path. It is **hashed into the freeze
     manifest, read with an explicit `WHERE version = ?` filter, and re-verified at Stage 0
     seal time.** If it cannot be frozen, Stage 0's determinacy figures are reported as
     **conditional on an unhashed input** and the gate is re-derived from an uncached run.
   - **Executions performed during the authorship of this document, disclosed exhaustively**
     (none touches an outcome, none is scientific compute): the `C-0` equivalence check
     (380/380, §5.2); a single `PBC` case generation to confirm the namespace works; the
     declared-seed-band enumeration; `pb_33` and `pb_34`; the arithmetic of §10 and the
     Monte-Carlo operating characteristics of §10.5 and §21.4 (numpy/scipy, 100,000–200,000
     draws, on synthetic multinomials with no reference to any surface). Read-only `git show`
     of `befca0d`, `f4c1105`, `1d20731` and the `pb_*` scripts.

## 32. TERMINAL STATES

**The complete, mutually exclusive, exhaustive terminal set of Stage 1. Assigned solely by
§22, in the exact `F1..F17` order §22.1's `F0` now defines as a literal list, not an inferred
property of names.** Stage 0's disjoint set is §22.2. `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` is
**not** in this set, by design (§25.4).

**Rewritten in full against §22.1's `F1..F17`** (`CRITIC_GOVERNANCE` `N3`: v3's table named 15
terminals against 21 assigning rules, missing six that v3's own repairs created, and misdated
`T1` to the wrong rule). §31.1's freeze-time verifier (`V3-H5`) asserts mechanically that the
set of terminals named here equals the set named by §22 — the same discipline the Stage 0
instrument already applies to its own three terminals.

| Terminal | §22 rule | Meaning | Positive? | Licenses? |
|---|---|---|---|---|
| `T-INSTRUMENT-UNBOUNDED-ON-E2A` | Stage 0 | The frozen G2 contract is not decidable at finite cost **on the sealed E2a corpus**. A finding about the contract **and that corpus**. It establishes nothing about the calibration population, which contains 138 F17 worlds E2a does not contain | No | No |
| `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` | F1 | The freeze-clean construction route failed its equivalence control and the owner did not authorize a registered delta to `registry.py`. **Not** a claim that the benchmark is defective | No | No |
| `BENCHMARK_INTEGRITY_DEFECT` | F2 | Ordinal drift, calibration-band collision, generator-version mismatch, or unauthorised protected-path drift. **This is** the claim that the benchmark needs auditing before anything else proceeds | No | No |
| `SURFACE_POPULATION_CONTAMINATED` | F3 | `P7` fails: a `mass_power` world exists in the primary population, which the population declaration (§5.2, `G2` families derived by predicate) should make impossible | No | No |
| `SURFACE_INCOMPLETE_COMPOSITION` | F4 | Cells or seeds not exact | No | No |
| `VOID_SCHEMA_INCOMPLETE` | F5 | Schema incomplete at seal or written after it. No back-fill (D6) | No | No |
| `VOID_CONTROL_FAILURE` | F6 | A named control failed. Single shot, no retry, no amended protocol | No | No |
| `VOID_INSTRUMENT_INDETERMINATE` | F7 | `INDETERMINATE_WORLDS > 0` on the calibration surface after uncapped escalation | No | No |
| `VOID_SINGLE_SHOT_BROKEN` | F8 | More than one surface, or a non-empty tuning ledger, or a post-surface amendment | No | No |
| `SURFACE_DEGENERATE_NO_FRONT` | F9 | `S_1 = 0`: no world reached the front under either resolution, so every conditional retention statistic is undefined. **Evaluated before any Gate R row**, because at `S_1=0` Gate R row 2's arithmetic certifies trivially (`CRITIC_SCIENCE` `V3-C1`) — this terminal exists precisely to catch that case before routing consults it | No | No |
| `ROUTING_INDETERMINATE` | F10 | Certification fails and retention is not exonerated. **Not a null result:** the finding that G2 loss is jointly attributable across stages and **no single-factor repair is licensable in this regime**. E4's one-factor-at-a-time framing is then inadequate here, and the honest forward path is a jointly-varying design under separate authorisation, with `befca0d` §3's warning that admissibility is not additive | No | No |
| `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` | F11 | No stage certifiably dominates, **and** the retention stage is exonerated under the `G3`-repaired conjunction (`pi_B < delta` **and** `P_retain\|front >= 1-delta` **and** `S_1>0`). The retention rule is exonerated; no retention change is licensed. **Concludes, but licenses nothing** — see the `Concludes?`/`Licenses?` split below (`G17`) | **Concludes: Yes** | No |
| `E4A_ENTRY_LICENCE_PROPOSED` | F12 | Certified route `B`, `E6_SAFETY_HEADROOM_PRESENT` (§21.5, R0-based, no arm parameter). **A proposal**; operative only on the §21.5 owner ratification, which for this row must also re-arm `f4c1105` | **Yes** | Yes (proposal) |
| `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` | F13 | Certified route `B`, but the R0 execution's own NEG-stratum false-structure rate breaches the E6 ceiling. Certified and reported; nothing proposed | Certified, not licensing | No |
| `E4_GENERATION_LICENCE_PROPOSED_F09_F10` | F14 | Certified route `A`, `E6_SAFETY_HEADROOM_PRESENT`, restricted by E3's completed per-cell verdicts to `mass_saturating_descriptor` (F09) and `mass_interaction` (F10). The ten MARGINAL conditions are reported as **blocked**, not licensed | **Yes**, per cell | Yes (proposal) |
| `E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` | F15 | Certified route `A`, but the E6 ceiling is breached. Certified and reported; nothing proposed | Certified, not licensing | No |
| `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` | F16 | Certified route `C+D`. **REINSTATED, not deleted** (correcting §32.3's v3 disposition below): `§2.1`/`N6` found the authority v3 cited for E4f's execution does not survive review, so this route currently proposes nothing regardless of certification strength. `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` remains frozen and ready for the day a real ratification record exists | Certified, not licensing | No |
| `T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS` | F17 | The owner concludes that `befca0d` §2.3 combined with D6 admits no qualification that is both non-circular and non-vacuous. The programme publishes the divergence and stops. **A legitimate scientific result already present in the decision tree** | No | No |

**`D3_ITEMS_UNMET_NO_REENTRY` is not a terminal** (`CRITIC_SCIENCE` `V3-C2`, option (a) — see
§22.1). It is a mandatory rider on `F12`–`F16`: any of D3's eight items unmet, or the §21.5
ratification refused, prevents the named terminal from becoming an **operative** licence
without changing which terminal fires. The `Licenses?` column above already distinguishes
"proposal" from "adoption"; D3/ratification is what moves a proposal to an adoption, and its
absence keeps every row at "proposal" or "no", never at "operative".

### 32.1 CONSTRUCTIVE REACHABILITY — the defect that killed v1, proven not to recur

v1's two licensing terminals were **arithmetically unreachable for every possible dataset**,
and neither v1 nor its decision record noticed. **Every positive terminal below is therefore
proven reachable by exhibiting a concrete, attainable realisation**, in integer per-condition
world counts (which is the only form the surface can actually take: 12 conditions × 138
completed worlds each, `P1`), with the certification arithmetic recomputed and shown, and
**re-verified after every repair that could have moved it** (`CRITIC_SCIENCE` `V3-H5`'s
finding that no such re-verification existed is closed by the recomputation below and by the
freeze-time verifier of §31.1).

Each witness is a per-condition count vector `(A, B, C+D, E)` summing to 138, applied
identically to all 12 conditions — so `w_k`-weighting is exact, `P1` holds by construction,
`P7` holds (no `mass_power` exists in the population at all), and, given `P6'`
(`INDETERMINATE_WORLDS = 0`, hence `rho_bot = rho_top`), argmax invariance holds trivially.
All four therefore **satisfy every Gate Q clause by construction**.

`sigma = sqrt( (pi_top + pi_second - lead^2) / 1656 )`, `LCB = lead - 1.9599640 * sigma`,
`delta = 0.0694444`. All four values below were recomputed independently for this rewrite.

| Witness | per-condition `(A, B, C+D, E)` | shares `(pi_A, pi_B, pi_C+D, pi_E)` | argmax | lead | lead / `delta` | `LCB_97.5` | `pi_B` | Routes to |
|---|---|---|---|---:|---:|---:|---:|---|
| **W-B** | (14, 69, 50, 5) | (0.101449, 0.500000, 0.362319, 0.036232) | `B` | 0.137681 | 1.983 | **+0.093450** | 0.500 | Gate R row 1 → `E6` headroom → **`E4A_ENTRY_LICENCE_PROPOSED`** (F12) |
| **W-A** | (69, 30, 34, 5) | (0.500000, 0.217391, 0.246377, 0.036232) | `A` | 0.253623 | 3.652 | **+0.213847** | 0.217 | Gate R row 2 → `E6` headroom → **`E4_GENERATION_LICENCE_PROPOSED_F09_F10`** (F14) |
| **W-CD** | (14, 45, 74, 5) | (0.101449, 0.326087, 0.536232, 0.036232) | `C+D` | 0.210145 | 3.026 | **+0.166580** | 0.326 | Gate R row 3 → **`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`** (F16, `§2.1`/`N6`) |
| **W-EX** | (0, 0, 5, 133) | (0.000000, 0.000000, 0.036232, 0.963768) | `C+D` | 0.036232 | 0.522 | +0.027232 | **0.000** | not certified (lead < `delta`) **and** exonerated (`pi_B=0 < delta`, `S_1=1`, `P_retain\|front = S_2/S_1 = 1.0 >= 1-delta`) → Gate R row 4 → **`RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE`** (F11) |

**`W-EX` is a NEW witness, replacing v3's.** `CRITIC_SCIENCE` found v3's `W-EX =
(55,8,50,25)` stale against the `G3`-repaired conjunction: its `P_retain|front = 0.9036 <
1-delta = 0.9306`, so it no longer satisfies exoneration and instead falls to Gate R row 5
(`ROUTING_INDETERMINATE`). The replacement above satisfies **both** conjuncts of the repaired
predicate by construction (`S_1=1`, so the ratio is trivially `1.0`) and is independently
recomputed, not reused from the earlier document.

**All four are attainable**: every entry is a non-negative integer, every row sums to 138, and
nothing in Gate Q, in the generator, or in the endpoint definition excludes any of them. **Gate
Q therefore does not determine the route** — `NON_DETERMINATION_PROVEN` (§4.1 property v) is
discharged by W-B, W-A and W-CD alone, which certify to three different arguments while
satisfying identical qualification clauses, even though only two of the three currently reach
an operative proposal.

**Why this could not have been done under v1, and why it can be done now.** Under v1 every one
of W-B, W-A and W-CD would have been **vetoed by Gate V** — `TV(W-B, pi_0) = 0.1307`,
`TV(W-A, pi_0) = 0.4112`, `TV(W-CD, pi_0) = 0.0559`, against a tolerance of 0.0694 — so W-CD
alone would have survived, and v1 pre-labelled it non-executable anyway. The removal of Gate V
(Decision 1) is what makes W-B and W-A reachable. **Decision 2 no longer makes any terminal
executable** (`§2.1`/`N6`): W-CD reaches a certified route, but that route currently proposes
nothing. `NON_DETERMINATION_PROVEN` is a statement about Gate Q, not about executability, and
survives that correction intact.

**For the record, the §21.4 annotation on each witness** — computed here to show that it
carries information and changes no terminal:

| Witness | `TV` vs `pi_0` | in `delta` | `D_max` | 95% interval on `TV` | Annotation |
|---|---:|---:|---:|---|---|
| W-B | 0.1307 | 1.88 | 0.1307 | [0.0616, 0.2201] | `INDETERMINATE` |
| W-A | 0.4112 | 5.92 | 0.4028 | [0.3575, 0.4686] | `CONTRADICTS` — disclosed, conditions nothing (`N1`/`G6`) |
| W-CD | 0.0559 | 0.80 | 0.0559 | [0.0175, 0.1476] | `INDETERMINATE` |
| W-EX | 0.9360 | 13.48 | — | — | `CONTRADICTS` — disclosed; no licence exists on any route to condition |
| `pi_0` itself | 0.0000 | 0.00 | 0.0000 | [0.0127, 0.1105] | `INDETERMINATE` |

**Disclosed asymmetry.** The historical asymmetry recorded here in v2/v3 — that the
explanation obligation was more likely to attach to routes `B`/`A` than to `C+D` — no longer
applies to what the annotation *does*, because `G6`'s repair removed the obligation from every
route uniformly (`N1`, §0.1 response 1, corrected). The asymmetry that remains is purely
descriptive: `pi_0`'s own argmax is `C+D`, so a `C+D`-certifying surface will tend to read
closer to `pi_0` than a `B`- or `A`-certifying one, and that is disclosed as a property of the
comparator, not of the licensing rule.

### 32.2 Negative terminals are also checked for reachability

`ROUTING_INDETERMINATE` is reached by, e.g., per-condition `(40, 45, 48, 5)`
(lead `3/138 = 0.0217 < delta`, `pi_B = 0.326 > delta`). The `VOID_*` terminals are reached by
their named clause failing. `T-INSTRUMENT-UNBOUNDED-ON-E2A` is reached whenever any E2a world's
class differs between resolutions after uncapped escalation.
`NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` is reached if `C-0` regresses (it does not
today: 380/380) and the owner refuses R-A. `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` is reached by
`W-CD` above, today, unconditionally on route `C+D`. **§31.1's freeze-time verifier checks
every rule in `F1..F17` for at least one witness under the exact `F0` order and fails the
freeze if any rule has none** — this is now executed, not asserted (`V3-H5`).

### 32.3 Terminals of v1 that are deleted, with the reason

| v1 terminal | Disposition |
|---|---|
| `T-INSTRUMENT-UNBOUNDED` | Renamed `T-INSTRUMENT-UNBOUNDED-ON-E2A` and its gloss restricted (`S11`) |
| `CIRCULAR_BY_MEASUREMENT` | **Deleted.** Its trigger `QND` was unsatisfiable over an empty family (`D2`, `S9`). The property is now proven constructively (§32.1) rather than measured |
| `NO_ADMISSIBLE_SURFACE_EXISTS` | **Split** into `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` and `BENCHMARK_INTEGRITY_DEFECT`, because v1 conflated a governance refusal with a benchmark defect (`D8`) |
| `SURFACE_NOT_QUALIFIED` | **Split** into F2–F8's named terminals, because a single name for eight distinct failures is not a terminal state (`S8`) |
| `VOID` | **Deleted as a state.** It was a residual that subsumed five named terminals, violating exclusivity by definition (`S8`) |
| `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` | **REINSTATED as `F16`** (correcting v3, which deleted it on the strength of an authority claim `N6` found unsupported). It is no longer only the `A`-route's blocked-cell language; it is now the terminal for a certified `C+D` route under the current, unratified state of E4f's authority |
| `HALTED` | **Deleted with Gate V** (Decision 1) |
| `T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY` | Not armed (§21.4). The re-arming rule survives |

| `T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY` | Not armed (§21.4). The re-arming rule survives |

### 32.4 E5

`grep -n "E5"` returned zero hits in v1 (`S25`). Recorded here: **no terminal of this protocol
reconsiders E5.** Ratified D4 defers E5 and states it *"is reconsidered automatically if and
only if the newly qualified causal path makes it scientifically relevant and its dependencies
are prospectively satisfied."* That reconsideration trigger remains with the protocol owner and
is not delegated to any terminal above.

## 33. THRESHOLD INVENTORY — EVERY NUMBER IN THIS PROTOCOL

**Reused verbatim from frozen authority (each citation verified by direct read on this host):**

| Value | Meaning | Source, verified |
|---|---|---|
| `30` | seeds per case | `rc5_seeds.A35_SEEDS_PER_CASE`, imported; `befca0d` §2.5 control 2 |
| `12` | registry G2 conditions, `w_k = 1/12` | `registry.py:135-152` |
| `20/30` | stability gate | `structural_acceptance.py` — imported |
| `0.005` | `MAX_INVALID_FRACTION` | `befca0d` §3.4 |
| `95%` Wilson | CI method | `f4c1105` §7 — imported, not reimplemented |
| `alpha = 0.05` | family-wise, Holm–Bonferroni on the **secondaries** | `f4c1105` §8 |
| `B = 10,000` | bootstrap replicates; `derive_seed_v2("bootstrap", id)` | `f4c1105` §8 |
| `0.80 / 0.50 / 0.10` | E3 identifiability and study-validity bars | `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN` §5; verdicts verified at `1d20731:E3_RESULTS.md:76-78` |
| `Wilson upper <= 0.15` on `>= 100` opportunities | E6 safety ceiling | `befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3, lines 137–140, verbatim |
| `0` indeterminate worlds | determinacy bar | P2 §6.2; demonstrated achievable at Gate 1 (0/144) |
| `100%` | uncapped-validation agreement bar | Gate 1 precedent 101/101 |
| `101` | `C-4` sample size | Gate 1's own executed sample |
| `30 x 30` | `C-5` replay subset | Gate 1's own executed replay |
| `ROOT_SEED = 20260813`, `GENERATOR_VERSION` | generator identity | `registry.py:12`, `generator.py` |
| A–E taxonomy, decision order, C/D refinement | endpoint definition | `MURU_V2_E2_PREDECLARATION` §6 |
| Adoption tie-break: fewest free parameters, then lowest false structure | | `befca0d` §3.1 |
| Improvement bar: paired 95% lower bound `> 0` | | `f4c1105` §6.1; `befca0d` §3.1 |
| 28-field schema | corpus requirement | `befca0d` §2.4 |
| `PYSR_CONFIG`, `GRAMMAR_VERSION`, `deterministic=True`, `parallelism="serial"` | search configuration | `befca0d` §2.5.2 |

**Derived, with the derivation shown inline:**

| Value | Meaning | Derivation |
|---|---|---|
| `delta = 10/144 = 0.0694444` | materiality of a routing lead | **§10.1.** Ported from PE2-4's *"within 10 cases of 69/57"* on a 144-case denominator, from a two-way count deviation to a proportion-scale lead between two cells of a four-way partition. Direction of generalisation stated. **Moved here from v1's REUSED table (`S5`)** |
| `z_.975 = 1.9599640` | routing critical value | **§10.2.** One-sided bound on a **data-selected** contrast between two of three cells. `z_.95` gives a measured 10.0% type-I rate at a two-way tie |
| `n = 1656 = 12 x 138` | G2 replicate count | **§10.4.** Smallest lattice point ≥ 1619.69 with `R` divisible by 6, from `n >= (1-delta^2)(z_.975+z_.80)^2/delta^2` using the **distribution-free** bound `pi_1+pi_2 <= 1` |
| `276 = 2 x 138` | NEG control worlds | **§5.2.** Same replicate count on the two negative-control families; of which **230 are evaluable** (F19C is non-evaluable by registry declaration), i.e. 2.30× E6's frozen `>= 100 evaluable safety opportunities` — v2 said 2.76× by counting worlds |
| `DEV r000..r068 / EVAL r069..r137` | arm-selection split | **§26.** Exact halves; `69 = 23 x 3` so F19's variant cycle is balanced in each half |
| `RETENTION_EXONERATED := pi_B < delta` | exoneration predicate | **§21.3.** `pi_B = S_1 - S_2` is the retention-loss share; "exonerated" is "loses less than a material share"; the absolute form dominates the frozen ratio form and needs no second threshold |
| `CALIBRATION_SEARCH_SEED_BASE = 2_100_011_400` | new seed band base | **§5.2.** `rc5_seeds.A35_SEARCH_SEED_MAX + 1`, computed at import from the frozen module. Registered as a rule; the value is derived from it |
| `12` C-2 negatives / `12` C-3 known-answer worlds / `3` planted expensive rows / `500` C-6 audit expressions | control sample sizes | **§18.** One per G2 condition (12); the 3 planted rows are the minimum that makes the "expensive to canonicalise" clause non-vacuous across three canonicalisation mechanisms; 500 is the largest sample that runs in minutes on a commodity second host with zero search |

**Deleted from v1's inventory, with reason:**

| v1 value | Reason |
|---|---|
| `g_max = 0.010` | Provably vacuous: subsumed by `INDETERMINATE_WORLDS == 0` (`D5`). Its undeclared derivation constant `1.4` (`S4`) goes with it |
| `1944 = 12 x 162` | The blinded top-up it sized is unreachable (`D5`) and would have lowered the effective margin (`S6`) |
| `TV <= delta` as a veto tolerance | Gate V removed (Decision 1). `TV` survives only as the §21.4 reference scale |

## 34. FREE PARAMETERS — THE COMPLETE, HOSTILE-FACING LIST

v1's header claimed *"exactly one new magnitude is introduced anywhere in this protocol"* and
its §33 claimed *"Newly introduced magnitudes: ONE."* **Both were false** (`S4`). This section
replaces that claim. Every number below is a genuine free parameter: declared before
execution, but not derivable from frozen authority.

| # | Parameter | Value | Why it was unavoidable | Where it can affect a verdict |
|---|---|---|---|---|
| FP-1 | Power target in the §10.4 sizing | `0.80` | A sample size cannot be derived without one. It is the conventional default | **Nowhere.** It affects only `n`. `delta` and the certification rule are independent of it |
| FP-2 | Tier-1 CPU cost bound | `60 s` per distinct expression (12× the retired 5 s, in CPU time) | A cost bound is needed to decide *when to escalate*. No frozen source supplies a multiplier | **Nowhere.** Exceeding it produces `UNRESOLVED`, which is its own state and never a label. Tier 2 is uncapped in time |
| FP-3 | Per-worker RSS ceiling, **per phase** (search 2.0 / scoring tier-1 4.0 / scoring tier-2 23.5 GiB), profiled on the E2a DEV set and recorded in `STAGE1_RESOURCE_PROFILE.json` | see §25.4/§25.5 | A host with 48 GiB and no swap OOM-killed the previous run four times. Some ceiling must exist or the kernel picks one by SIGKILL | **Nowhere** — §25.4 routes exhaustion to an operational non-terminal that emits no scientific state. **`X-2` correction: v2 justified this as "the in-process ceiling fires before the kernel does", which was arithmetically false** — `WORKER_COUNT x RSS_CEILING = 8 x 24 = 192 GiB` on a 47 GiB host, so the kernel fired first and the stated guarantee never held. The per-phase ceilings now satisfy `WORKER_COUNT x RSS_CEILING <= 0.85 x total_physical_GiB` in every phase, which is what makes the guarantee true. **Frozen before Stage 0** (`D7`), profiled record in `STAGE1_RESOURCE_PROFILE.json` |
| FP-4 | Worker count, **per phase** (19 / 9 / 1), each satisfying `WORKER_COUNT x RSS_CEILING_GIB <= 0.85 x total_physical_GiB` | see §25.4/§25.5 | Concurrency must be a declared constant or it is a scientific variable (v1 §13 A4) | **Nowhere**, given FP-3's disposition. **Frozen before Stage 0** (`D7`) |
| FP-5 | `C-2` / `C-3` / `C-6` sample sizes and pass bars | 12 / 12 (+3 planted) / 500, all at 100% | Frozen authority names these controls but gives no sizes. v1 left them to the executor | **Yes, in principle** — a control's power depends on its size. Bars are 100%, so a larger sample can only make them harder; the risk is under-powering, not over-passing. Declared here so it is fixed rather than chosen |
| FP-6 | The §21.4 bootstrap RNG label | `"E7-CC"` | A label is required by `derive_seed_v2`'s frozen signature | **Nowhere.** The annotation gates nothing |

**Six free parameters. One of them (FP-5) can in principle affect a verdict, and only in the
conservative direction. `delta`, the certification rule, the routing table, the terminal set
and the qualification predicate contain none of them.**

## 35. PRE-RECORDED EXPECTED OUTCOME

Recorded here, before execution, so the record shows the design was not chosen for its answer.
`CRITIC_SCIENCE` correctly observed that v1's expectation was an **alibi**: v1 predicted "no
re-entry on any branch" at 55% probability when it was in fact a **theorem** of v1's own
arithmetic. This version states its arithmetic first (§32.1) and its expectation second.

**Stage 0.** Corrected E2a attribution near `A ≈ 60–90`, `B ≈ 230–255`, `C+D ≈ 100–104`,
`E ≈ 119–122`; `B` plurality intact; divergence from the comparator **larger** than the sealed
corpus's. **`INDETERMINATE_WORLDS_E2A = 0`, i.e. Stage 0 passes (~65%).** *(v1 predicted
"`g <= 0.005` and 0 indeterminate worlds", a state §0.4 shows to be impossible — non-zero `g`
with zero indeterminate worlds cannot occur. The corrected prediction is a single binary.)*
I judge `D-INST-INDETERMINATE` (~35%) the main risk, driven by the measured 44.4 GB / 95 s
expression; if it fires through resource exhaustion rather than genuine indeterminacy, §25.4
means **no scientific claim is published at all**, which is the intended behaviour.

**Stage 1 point prediction.** `pi_A < 0.15`; `pi_E < 0.10`; `pi_B` and `pi_C+D` both in
`[0.35, 0.52]` with **`|pi_B - pi_C+D| < delta`**.

**Predicted terminal:**

| Terminal | Probability | Reasoning |
|---|---:|---|
| `ROUTING_INDETERMINATE` | **~50%** | The point prediction sits inside the non-certification region, and the composite rule is deliberately conservative there (type-I 0.0024 at a two-way tie) |
| `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` (route `C+D`) | **~18%** | The live routing question is retention vs cross-seed identity, and the surface contains 138 F17 worlds — the identity stressor no admissible corpus has ever contained. **This is now a non-executable certification, not a licence** (`§2.1`/`N6`): if any route certifies, I think this is the likeliest, and it currently proposes nothing |
| `E4A_ENTRY_LICENCE_PROPOSED` (route `B`) | **~10%**, less `E6` attrition | Requires `pi_B` to lead by ≥ `delta` with `LCB > 0`; E3's MARGINAL verdicts on 10 of 12 conditions push mass toward `A`, not `B`. Some of this mass now lands on `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` if the `E6` check fails, which was previously folded into the same terminal |
| `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` | **~5%** | Requires `pi_B < delta` **and** the `G3`-repaired ratio `P_retain\|front >= 1-delta`, a strictly narrower gate than v3's single-inequality version. Possible if retention genuinely loses almost nothing among worlds that reach the front |
| `E4_GENERATION_LICENCE_PROPOSED_F09_F10` | **~4%**, less `E6` attrition | Requires `A` to lead by ≥ `delta`; plausible given E3, but then 10 of 12 conditions are blocked and the licence is thin. Some mass now lands on `E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` |
| One of the `VOID_*` terminals | **~8%** | `C-6` (two-architecture parity) and `P6'` are the likeliest failures |
| `T-INSTRUMENT-UNBOUNDED-ON-E2A` or `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` | **~5%** | The escalation tail |

**Annotation prediction.** Conditional on any certified route, I expect the §21.4 annotation to
read `INDETERMINATE` (~70%) rather than `CORROBORATES` or `CONTRADICTS` — because, as §21.4
records, **even a perfectly matched surface reads `INDETERMINATE`**, the comparator's own
variance consuming 69% of the reference scale.

**What has changed since v1's expectation, and it is the point of this version.**
v1 expected no re-entry on any branch **and that expectation was forced by its arithmetic** —
§32.1 shows its two licensing terminals had zero witnesses under any dataset. This version's
terminals are each **shown attainable** (§32.1), which is a claim about the design's
*capability to distinguish outcomes*, not a claim about how likely a positive outcome is.
Recomputed against the current disposition: `E4A_ENTRY_LICENCE_PROPOSED` (~10%, less `E6`
attrition) and `E4_GENERATION_LICENCE_PROPOSED_F09_F10` (~4%, less `E6` attrition) are the
**only** terminals that currently propose an operative licence — together **~14%** of the
predicted mass, down from v3's ~37%, because route `C+D`'s ~18% and the exoneration branch's
~5% both **conclude without licensing** (`§2.1`/`N6`, `G17`'s `Concludes?`/`Licenses?` split).
The remaining ~50%+8%+5% concludes nothing at all. §32.1 proves each terminal reachable; it
does not claim any one is likely, and the recomputation above states plainly how much smaller
the licensing mass is than v3 reported
is exhibited in §32.1 rather than asserted here.

**The disclosure that makes this checkable.** The design most likely to deliver re-entry was on
the table and was rejected: P3's fixed-target TOST at `n = 576`, whose own author labels its
framing anti-conservative. It was rejected under decision rules **R3** (keeps Held-out evidence
out of positive licensing) and **R8** (minimizes leakage and circularity) — **not** because it
was expected to fail, but because it was expected to pass. Two further choices in this version
run against my own interest: the materiality clause of §21.1 **cuts power at a lead of `delta`
from a nominal 0.80 to a real 0.499** and I adopted it anyway; and `n` rose 27.8% for a
correction (`z_.975`) that makes certification harder, not easier.

## 36. DOWNSTREAM CONSEQUENCE — THE E4f POPULATION RESTATEMENT

**Status: DORMANT.** `§2.1`/`N6` found no protocol-owner record authorizes E4f's execution
today, so a certified `C+D` route currently assigns `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`
(§22 `F16`) and proposes nothing — there is no operative licence for this section's
restatement to condition. The analysis below is **preserved rather than deleted**, because it
is correct on its own terms and there is no reason to redo it the day a real ratification
record exists: at that point `MURU_V2_E4F_POPULATION_RESTATEMENT.md` is written exactly as
described, `F16` is replaced by the licensing rules this section once fed, and nothing else
in this section changes.

**Disclosed in full because it is the one place where this protocol touches a frozen
document.**

> **`G8` / `DEF-H8` repair — v2 made `C-6a` and §36 mutually unsatisfiable, and left the
> choice between them to a clerk.**
>
> v2 required `C-6a` to re-verify E4f's sha256 **and** required §36 to restate E4f's
> population. Enacting §36 changes the artifact whose hash `C-6a` checks, so performing the
> mandated restatement **self-voids the terminal it enables** (`F12` → `VOID_CONTROL_FAILURE`).
> Whether the same edit counted as a "restatement" or a "tuning entry" then decided between
> `E4F_LICENCE_PROPOSED` and `VOID_CONTROL_FAILURE` — a **clerical choice available at
> execution time**, which is a relabel-after-results channel. Worse, §36 moved E4f's
> population **+27.8% from outside E4f**, where `C-6a`'s hash check is structurally incapable
> of detecting it.
>
> **Precedence rule, binding, and it resolves both halves:**
>
> ```
> 1. MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md is NEVER edited by this protocol.
>    Its bytes and its hash 0ce2755d...3a7f61 stand. C-6a checks exactly that.
>
> 2. The population restatement is written to a NEW, SEPARATELY HASHED artifact,
>       MURU_V2_E4F_POPULATION_RESTATEMENT.md
>    which cites E4f by hash, states the substituted display values, and is itself
>    frozen and hashed BEFORE Gate R is read.
>
> 3. E4f's population-by-reference clause (its own §7.1) is what makes this legitimate:
>    E4f DELEGATED its population to the calibration protocol, so supplying that
>    population is discharging E4f's own reference, not amending E4f. If a reader
>    concludes instead that E4f's printed numerals are independent parameters, then the
>    reference is broken and the correct terminal is E4F_POPULATION_REFERENCE_BROKEN --
>    NOT a licence, and NOT a control failure. (Numbered here as a dormant reference only;
>    section 22's live F16 is the terminal that fires today, per the DORMANT status above.)
>
> 4. The restatement is NOT a tuning-ledger entry, because it changes no threshold,
>    margin, gate, estimator, terminal or decision rule -- only a denominator that E4f
>    itself declined to fix. P10's ledger stays empty. This is stated here, before
>    execution, so it cannot be decided after.
> ```
>
> **The +27.8% is disclosed as what it is.** It is not a choice made for E4f's benefit: it
> follows mechanically from §10.4's sizing, which was fixed before any route was known, and it
> moves E4f's denominators **against** the arm (more negatives, more safety opportunities, a
> strictly harder zero-defect census). The direction is stated below.

`MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` §4.1 and §7.1 define E4f's population **by
reference** to the calibration protocol — §7.1 says so in terms: *"REUSED VERBATIM, not
invented here. From `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` §26(3), which already
declares the split for exactly this purpose."* The numerals E4f prints (108 replicates, 1,296
G2 worlds, 216 NEG, `DEV = r000..r053`, `EVAL = r054..r107`, 648 G2 worlds and 1,944 negatives
per half) are **display restatements of v1's then-current values**, not independent parameters
of E4f.

This protocol's corrected `n` changes those display values to:

```
replicates                138        (was 108)
G2 worlds               1,656        (was 1,296)
NEG worlds                276        (was   216)
DEV_ARM      r000 .. r068  ->  828 G2 worlds ; 2,484 negatives   (was r000..r053, 648 ; 1,944)
EVAL_ARM     r069 .. r137  ->  828 G2 worlds ; 2,484 negatives   (was r054..r107, 648 ; 1,944)
```

**No E4f threshold, margin, gate, estimator, terminal or decision rule changes.** Every E4f
gate is either a margin-exactly-0 census predicate (`b = 0` in Gates G1 and H1) or a paired
one-sided lower bound `> 0` at Holm-adjusted `alpha = 0.05` (Gates G2 and H2). All four are
**scale-free**. E4f §8.7's resolving-power statement — *"the minimum certifiable discordance is
`n_d >= 6`"* — is **unchanged**; only its denominator moves from 648 to 828.

**Direction of the change, so it cannot be read as flattering an arm.** More negatives makes
Gates G1 and H1 **strictly harder** to pass (more opportunities for `b >= 1`). More EVAL worlds
raises the **power** of Gates G2 and H2 without moving their bars. Neither direction lowers a
bar, and no arm is advantaged by the substitution.

**Governance, and why this is not tuning.** E4f's freeze record makes any post-freeze parameter
change a tuning-ledger entry that voids the run (`E4F_VOID_TUNING_LEDGER_NONEMPTY`). At this
commit, verifiably:

- no calibration surface exists;
- **no route exists** — this protocol is unexecuted text;
- no `false_labelling_rate` or `k_inflation` value has ever been computed by anyone, for any
  arm, on any population;
- the E4f artifact still hashes to `0ce2755d…3a7f61` and `8a2ffa50` is still a strict ancestor
  of HEAD.

The restatement is therefore **results-blind and pre-route**, which is exactly the condition
E4f's own §0 attestation was written to preserve. **It is nonetheless recorded as a formal act
requiring the protocol owner's countersignature before E4f may execute** (§21.5 item 3), and
must be entered in E4f's freeze record as a **population-by-reference restatement**, not as a
silent edit. If the owner judges it a tuning event rather than a restatement, the correct
remedy is to **re-freeze E4f results-blind now** — which is still possible, and will not be
possible once a route exists. **v1's anti-tampering intent is preserved: the E4f freeze
predates any route and may not be amended after one.**

---

**TERMINAL STATE OF THIS DOCUMENT: PROTOCOL TEXT, NOT YET FROZEN, NOT EXECUTED.**
**No world generated. No module written. No search executed. No partition amended. No
protected byte modified. No re-entry licensed.**
**D3 items 1–5 are met by this text; item 6 (named adjudicators) and item 7 (freeze) are
PENDING; item 8 (execution) is unstarted.**
