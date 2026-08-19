# CRITIC_GOVERNANCE — hostile governance review of the v2 calibration / re-entry protocol

**Agent:** CRITIC_GOVERNANCE (hostile adversary). **Date:** 2026-08-19.
**Branch:** `claude/muru-v2-autonomous-reentry`. **HEAD at review:** `4e36f93`.
**Target:** `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md` (1,183 lines), with
`SYNTHESIS_DECISION_RECORD.md`, `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md`,
`MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md`, `DINST_HOSTILE_REVIEW.md`,
`FINAL_TERMINAL_REPORT.md`, `GATE_1_DEFINITIVE.json`.

**Nature of this document:** a pre-execution falsification attempt against a protocol that
has not run. Every number below was recomputed on this host with
`/home/aryav_thakur/venv/bin/python`, or read directly out of the cited commit with
`git show`. Nothing is taken on the protocol's report.

---

# VERDICT

```
CRITIC_GOVERNANCE = FAIL
```

**25 defects. 2 fatal, 6 blocking, 6 high, 8 medium, 3 low.**

The protocol is honest, unusually well-disciplined, and self-discloses more than most
reviews would extract. It nevertheless fails, for two independent reasons that are both
provable at freeze time with zero compute:

1. **Its two licensing terminals are arithmetically unreachable**, and the mechanism that
   makes them unreachable is the sealed E2b attribution. The "falsification veto" is
   extensionally a **selector over routes** whose admissible set is the singleton `{C+D}`
   — E2b's own argmax — and `C+D` is pre-labelled non-executable. The protocol therefore
   cannot satisfy D3 item 8 on **any** branch. It is not a re-entry protocol; it is a
   falsification protocol wearing one's terminal table.
2. **Its population plan requires mutating byte-protected benchmark content
   (`src/muru/paper_benchmark/registry.py` and five frozen artifacts)** without any
   authority to do so, and it misattributes the byte-protection to the wrong modules.

Defects S1, S2, S3, S4, S5, S6, S7, S8 change the protocol's terminal state or its routing
behaviour and must be repaired before freeze. The remainder change what the protocol may
claim.

**On the specific prohibitions I was asked to test:** I find **no** instance of the sealed
Gate 1 result being altered; **no** instance of E2b being used to *positively* license an
E4 arm in the strict per-arm sense (§4 property iii holds as stated); **no** restoration of
the old E2a Gate 2 routing; **no** post-result threshold selection (nothing has run);
**no** post-result design called preregistered in the body text. The D5 handling is clean
in both directions. But the *joint* effect of Gate R and Gate V (S1) makes E2b the sole
determinant of the licensing branch's outcome, which defeats the purpose the per-arm
property was built to serve.

---

# HOW TO READ THE SEVERITY LABELS

- **(a) FROZEN AUTHORITY STATES** — verbatim from a sealed commit, a ratified decision, or
  a byte-protected source file. I quote it and give the command that produces it.
- **(b) REASONABLE READING** — a defensible interpretation of (a) that the protocol either
  adopts or contradicts. Contestable; I say so.
- **(c) GENUINELY UNSPECIFIED** — frozen authority is silent and the protocol does not fill
  the gap. These are the ones a hostile executor exploits.

---

# 1. FATAL DEFECTS

## S1 — FATAL. Both licensing terminals are unreachable. Gate V's admissible set is the singleton `{C+D}` — E2b's own argmax — so the veto is extensionally a selector, and the only route it admits is pre-labelled non-executable.

**(a) FROZEN AUTHORITY STATES.** The ratified D1 attribution (`GATE_1_DEFINITIVE.json`,
`/SUCCESS = 4`, `/LOST_IN_CROSS_SEED = 71`, `/LOST_IN_RETENTION = 55`,
`/NEVER_ON_FRONT = 14`, `/denominator = 144`) is

```
pi_0 = ( A 0.09722 , B 0.38194 , C+D 0.49306 , E 0.02778 )
```

**(a) THE PROTOCOL STATES.** §21.3: `TV(pi_hat, pi_0) <= delta -> STANDS`, `delta = 10/144
= 0.069444`. §21.1: `ROUTING_CERTIFIED` requires `LCB_95(pi_top - pi_second) > 0` under
both extreme resolutions, with `Var = (pi_1 + pi_2 - (pi_1-pi_2)^2)/n`. §32: terminal
`E4A_LICENSED_AT_<arm>` requires `ROUTING_CERTIFIED -> B` **and** Gate V `STANDS`.

**The defect, computed.** In `pi_0`, `C+D` already leads `B` by `0.11111` (16 cases).
Gate V constrains `sum_i |pi_hat_i - pi_0_i|` to at most `2*delta = 0.13889` (standard TV,
the half-sum convention) or `delta = 0.069444` (the sum convention — see S3). The maximum
achievable `pi_B - pi_(C+D)` under a `STANDS` verdict is therefore

```
half-sum convention :  0.13889 - 0.11111 = +0.02778     (2 cases in 144)
sum convention      :  0.06944 - 0.11111 = -0.04167     (negative: impossible outright)
```

The minimum lead this design can certify (recomputed from the protocol's own formula, §10):

```
n = 1296  ->  0.06890        n = 1944 (blinded top-up)  ->  0.05630
```

`0.02778 < 0.05630 < 0.06890`. **Under either TV convention, no surface can simultaneously
certify a `B` route and survive Gate V.** Certifying a lead of `0.02778` would require
`n = 8,006` G2 worlds — 6.2x the design, 4.1x the top-up.

Route `A` is worse: `pi_A0 = 0.09722`, so certifying `A` as argmax requires
`pi_A >~ 0.42`, i.e. `sum|delta| >~ 0.64`, versus a budget of `0.13889`. Impossible by an
order of magnitude. Route `C+D` passes both gates comfortably — and §21.2 row 5 /
§32 pre-label it **`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`**.

**Consequences.**

- `E4A_LICENSED_AT_<arm>` and `E4_GENERATION_LICENSED_<cells>` are **unreachable**. §32's
  claim that the terminal set is "complete, mutually exclusive, exhaustive" and its
  `Re-entry? Yes / Partial` column are **false**.
- D3 item 8 ("successful execution of that qualification protocol") cannot be satisfied on
  any branch. `EXPERIMENTAL_REENTRY_RESOLUTION` is unachievable by this instrument.
- **The veto/selector distinction collapses.** §4 property (iii) proves
  `P(route=a | E2b) in { P(route=a | empty), 0 }` — true, per-arm. But when the veto zeroes
  every arm except the one E2b itself names, the composite map is
  `{A, B, C+D} -> {C+D} -> non-executable`. E2b is not subtracting at the margin; it is
  determining the terminal state. That is exactly what D1's "does not by itself license any
  E4 arm" and D3's "may not positively license re-entry or select an E4 arm" exist to
  prevent, and the per-arm proof does not reach it.
- §34's probability table (`ROUTING_CERTIFIED -> B` ~30% "followed by a Gate V HALT") is
  correct in outcome but presents as a *probabilistic expectation* what is a *deterministic
  arithmetic identity*. `SYNTHESIS_DECISION_RECORD.md` §11 states the same thing
  ("Conditional on `ROUTING_CERTIFIED -> B`, I expect Gate V to HALT") without noticing it
  is not an expectation.

**Changes terminal state:** YES — deletes two terminals from the reachable set.

**Minimal fix (choose one, and record it before freeze):**
1. **Delete both licensing terminals** and re-label the protocol truthfully as a
   falsification instrument whose best case is `ROUTING_INDETERMINATE` or `HALTED`. This is
   the honest option and costs nothing scientifically; or
2. **Apply Gate V to a quantity that is not the routing statistic** — e.g. veto on `S_1`
   (the generation margin) alone, leaving the `B`-vs-`C+D` contrast unvetoed — with explicit
   protocol-owner authority, since this narrows a ratified falsification hook; or
3. **Raise `n` to >= 8,006** and keep everything else. Consistent with §10's "raise `n`; do
   not lower the margin", but ~6x the compute.

In every case, **state the arithmetic of this section in the protocol at freeze time**, so
the unreachability is a declared design property and not a discovery.

---

## S2 — FATAL (authority). The population plan mutates byte-protected benchmark content, and §5 misattributes the byte-protection to modules that are not protected by the cited scripts.

**(a) FROZEN AUTHORITY STATES.** `scripts/pb_33_amendment_a3_1_integrity.py:43-60` and
`scripts/pb_34_rc3_integrity.py:40-57` define:

```python
PROTECTED_PATHS = [
    "src/muru/paper_benchmark/registry.py",
    "src/muru/paper_benchmark/generator.py",
    ...
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_partition_manifest.json",
    "artifacts/paper_benchmark_content_freeze.json",
    "artifacts/paper_benchmark_hash_inventory.json",
]
```

and enforce **byte identity** against commit `80a7803` (A2.1). Any drift is
`MODIFIED: <path>` unless it is pre-registered in `AUTHORIZED_BY_PATH`.

**(a) THE PROTOCOL STATES.** §5: `PARTITIONS = ("development", "held_out", "challenge",
"calibration")`, `PARTITION_CASE_COUNTS = {..., "calibration": 108}` — both are
module-level constants **in `registry.py`**, lines 14-15. §5 then says: *"the frozen modules
are byte-pinned by `pb_30`/`pb_33`/`pb_34` and must not be mutated"* — referring to
`rc5_seeds` and `seed_band_registry`.

**The defect.** The citation is inverted.
`grep -rn "rc5_seeds\|seed_band_registry" scripts/pb_*.py` returns hits **only** in
`pb_50_build_global_science_plan.py` and `pb_rc5_a3_5_authorized_delta.py` — **not** in
`pb_30`, `pb_33` or `pb_34`. Conversely `registry.py` and `generator.py` **are** in
`pb_33`'s and `pb_34`'s protected lists. The protocol carefully routes around a freeze that
does not exist on the modules it names, and walks straight through the one that does, on
the file it must edit. Executing §5 breaks `pb_33`, `pb_34`, and the
`benchmark-content-freeze-a2-1` / `-a3-1` tags, along with four protected artifact
manifests that any partition amendment regenerates.

No cited document grants authority to amend byte-protected benchmark content. The
ratification does not; §10 authorizes *constructing a protocol*, not amending the
benchmark. §5's mitigation — the ordinal-stability preflight — checks `case_ordinal` and
seed **values**, not file **bytes**, so it would pass while the content freeze is broken.

**Changes terminal state:** YES — `Q1` and `P9` both pass while the benchmark freeze is
broken, so the protocol executes on an unauthorized benchmark mutation.

**Minimal fix.** Add to Q1 and to P9 the clause: *"`pb_33` and `pb_34` return 0 errors
after the amendment"*, which is unsatisfiable without a registered
`AUTHORIZED_BY_PATH` delta. Then either obtain an explicit protocol-owner authorized-delta
for `registry.py` (the mechanism already exists — `pb_rc5_a3_5_authorized_delta.py` is the
template), or take §5.1's fallback as the primary. Correct §5's false statement about which
modules `pb_30/33/34` pin.

---

# 2. BLOCKING DEFECTS

## S3 — BLOCKING. `TV` is never defined. The factor-of-2 ambiguity in the protocol's only veto constant is outcome-determining.

**(c) GENUINELY UNSPECIFIED.** `TV(pi_hat, pi_0)` appears at §19 D1, §21.3 (twice) and
§33. It is never defined. Total variation between discrete distributions is conventionally
`0.5 * sum|p-q|`; the protocol's own §0.2 reports TV "in cases" (`14.78 -> 25.00`) which
is `144 * TV` under **some** convention, and `SYNTHESIS_DECISION_RECORD.md` §1.3's table
gives `TV = 0.3221` alongside `cases/144 = 46.39`, i.e. `46.39/144 = 0.3221` — the
half-sum convention. But the protocol never says so.

Per S1's arithmetic, the two conventions differ on whether a `B` route can *in principle*
reach `STANDS` (window of 2 cases) or is excluded outright (negative). A constant whose
normalization decides the reachability of the protocol's only re-entry terminal cannot be
left to convention.

**Changes terminal state:** YES.
**Minimal fix.** One line in §20 CONSTANTS: `TV(p,q) := 0.5 * sum_i |p_i - q_i|`, with the
worked value of `2*delta` as the `sum|.|` budget, and a cross-reference from §21.3.

## S4 — BLOCKING. "Exactly one new magnitude" is false. `g_max = 0.010` is a second new magnitude, it *does* decide a verdict, and its derivation rests on a third undeclared magnitude (`factor 1.4`).

**(a) THE PROTOCOL STATES.** Header: *"**Exactly one new magnitude is introduced anywhere
in this protocol** (the power level 0.80 in §10), and it affects only the sample size —
never a verdict, never a label."* §33: *"Newly introduced magnitudes: ONE."*

**The defect, in three parts.**

1. `g_max = 0.010` appears in the **Stage 0 gate** (§0.1), in **precondition P6** (§20), in
   **failure rule F0** (§22) and in **Gate R row 0** (§21.2). F0's terminal is
   `T-INSTRUMENT-UNBOUNDED`, which **forbids Stage 1 entirely**. That is the most
   consequential verdict in the document. `g_max` is listed under §33's *"Derived, with the
   derivation shown inline"* table — but "derived" is not "not new". The header's claim is
   false as written, and it is the sentence a future reader will rely on.
2. Its derivation introduces an **undeclared magnitude, `1.4`**: *"0.010 is the largest gap
   at which the §10 sample size remains within a factor 1.4 of its `g = 0` value."*
   Recomputed: `(delta/(delta-g))^2` = 1.1612 at g=0.005, **1.3647 at g=0.010**, 1.6269 at
   g=0.015, 1.9726 at g=0.020. Nothing in frozen authority supplies `1.4`. And the criterion
   does not even select `0.010` — the largest `g` with inflation `<= 1.4` is `0.010753`. The
   round number came first and the criterion was fitted to it.
3. Two further new multipliers ride in the §33 "derived" table without provenance: the
   tier-1 budget is *"12x the retired 5 s"* (why 12?) and the blinded top-up is
   *"1.5 x 1296"* (why 1.5?). Both are declared before execution, which is the important
   half; neither is derived from anything.

**Changes terminal state:** YES for `g_max` (it gates `T-INSTRUMENT-UNBOUNDED`).
**Minimal fix.** Replace the header claim with: *"Three new magnitudes are introduced:
`power = 0.80` (affects only `n`), `g_max = 0.010` (gates Stage 1 and precondition P6), and
the design-inflation tolerance `1.4` from which `g_max` is derived. Two further multipliers
(`12x`, `1.5x`) are declared, not derived."* Then say plainly that `g_max` was chosen as a
round number and `1.4` reports its consequence — which is defensible, prospectively fixed,
and far better than the current framing.

## S5 — BLOCKING. `delta = 10/144` is labelled REUSED VERBATIM but is a re-purposing of PE2-4 across two different estimands.

**(a) FROZEN AUTHORITY STATES.** `git show befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md`
line 466, PE2-4: *"E2b reproduces the decomposition's retention-versus-generation split to
**within 10 cases of 69/57**."* `f4c1105` §4 GATE 1: *"contradicts ... by more than 10 cases
(PE2-4's own tolerance)"*. `GATE_1_DEFINITIVE.json`:
`/FROZEN_THRESHOLD = "more than 10 cases (strict >)"`, `/FROZEN_THRESHOLD_VALUE = 10`,
applied to `RETENTION_DEVIATION` and `GENERATION_DEVIATION` — **absolute deviations of two
class counts on a two-way split**.

**(b) REASONABLE READING.** Porting a count to a proportion against a different `n` is
correct discipline (the protocol cites P2 BC-16 for exactly this, and it is right to).

**The defect.** The protocol then uses `10/144` for two things frozen authority never
sanctioned:
- **§21.3:** a **total-variation distance over a four-cell partition**. TV over 4 cells at
  tolerance `10/144` is not the same bar as "within 10 cases on a 2-way split" — it
  constrains four coordinates jointly and, per S1, is what makes the licensing branch
  unreachable.
- **§10:** the **lead margin between two cells of the same partition**, used to size `n`.

Neither re-purposing is wrong on its face. Both are **derivations**, and §33 lists them
under *"Reused verbatim from frozen authority (with citation)"*. That mislabel is the
defect: it exempts the two most consequential uses of the number from the derivation
discipline the header imposes on everything else.

**Changes terminal state:** NO directly; it conceals S1.
**Minimal fix.** Move `10/144` to the DERIVED table with the two-line derivation for each
use, and state which frozen quantity is being generalized and in what direction the
generalization is conservative.

## S6 — BLOCKING. The certification rule is `LCB > 0`, not `lead >= delta`. The blinded top-up therefore licenses a lead below the programme's own materiality tolerance, contradicting §10's own standing preference.

**(a) THE PROTOCOL STATES.** §21.1: `LCB_95(pi_top - pi_second) > 0`. §10: *"Standing
preference, recorded before any result: if the design proves underpowered, **raise `n`; do
not lower the margin.** No amendment lowering `delta` may be written after a surface
exists."* §10 also pre-declares the blinded top-up to `n = 1944`.

**The defect.** Because the rule is `LCB > 0` and not `LCB > delta` (or `point lead >=
delta`), the operative materiality bar is **implicit in `n`**. At `n = 1296` the minimum
certifiable lead is `0.06890` ~= `0.99 delta` — coincidentally material. At the pre-declared
top-up `n = 1944` it is `0.05630` = `0.81 delta` — **below** the programme's frozen
definition of a material attribution difference. The top-up is triggered by a nuisance
parameter (`g_j > 0.010`) that is blind to the endpoint, so alpha is intact; but the
*materiality* of a certified route is not. Raising `n` **is** lowering the effective
margin, which is precisely what §10 forbids.

**Changes terminal state:** YES — it makes `ROUTING_CERTIFIED` reachable on a
non-material lead.
**Minimal fix.** §21.1 becomes
`ROUTING_CERTIFIED := argmax invariant AND LCB_95(pi_top - pi_second) > 0 AND
(pi_top - pi_second) >= delta` under both resolutions. This costs nothing at `n = 1296`
(the design is sized for exactly this) and makes the top-up safe.

## S7 — BLOCKING. Gate R row 1 (exoneration) contains no declared threshold and is evaluated FIRST, reordering a frozen rule the protocol claims to adopt verbatim.

**(a) FROZEN AUTHORITY STATES.** `f4c1105` §4 GATE 2 orders the branches:
`IF B is the strict plurality -> EXECUTE` ... `ELSE IF P_retain_given_front is near 1
wherever P_front is high -> RC3 WITHDRAWN` ... `ELSE IF A is strict plurality` ...
`ELSE IF C+D is strict plurality` ... `ELSE (tie)`.

**(a) THE PROTOCOL STATES.** §21.2 orders them: row 0 VOID, **row 1 exoneration**, row 2
`NOT ROUTING_CERTIFIED`, row 3 `B`, row 4 `A`, row 5 `C+D`. §23 and §33 both describe this
table as *"REUSED VERBATIM from `f4c1105` §4, adopted rather than restated"*.

**Two defects.**
1. **The order is inverted, and the claim of verbatim adoption is false.** Under frozen
   authority a `B` plurality licenses E4a **regardless** of exoneration; under §21.2
   exoneration fires **first** and terminates at `RC3_WITHDRAWN` even when `B` is the
   certified argmax. That is a substantive routing change presented as reuse. (I note the
   protocol also, correctly and deliberately, reorders `f4c1105`'s GATE 1 falsification hook
   from first to last — see S17. Both reorderings may be improvements; neither is "verbatim".)
2. **(c) GENUINELY UNSPECIFIED — the row has no numbers.** *"`P_retain_given_front` inside a
   pre-declared band of 1 wherever `P_front` is high"*. The band is not declared anywhere in
   the document; "high" is not defined. Frozen authority is equally vague ("near 1",
   "high"), so this is inherited, not invented — but the protocol **asserts** the band is
   pre-declared when it is not, and it sits at the top of the routing table where a hostile
   executor picks it after seeing `P_retain_given_front`. This is the single easiest cheat
   in the document.

**Changes terminal state:** YES — row 1 can pre-empt row 3 and produce `RC3_WITHDRAWN`.
**Minimal fix.** Declare both numbers now (e.g. `P_retain_given_front >= 0.95` on the
subset with `P_front >= 0.50`, with the derivation of both, or by explicit reuse if a frozen
source exists), **and** move exoneration to its frozen position after the `B` branch, or
state plainly that the order was changed and why.

## S8 — BLOCKING. The terminal states are neither mutually exclusive nor exhaustive, and one failure rule emits two terminals at once.

**(a) THE PROTOCOL STATES.** §32: *"The complete, mutually exclusive, exhaustive terminal
set."*

**Counterexamples, all from the protocol's own text.**

| Event | §20 says | §21.2 says | §22 says |
|---|---|---|---|
| Control `C-3` fails | `SURFACE_NOT_QUALIFIED` | row 0 -> `VOID` | F1 -> `VOID` |
| `INDETERMINATE_WORLDS > 0` | `SURFACE_NOT_QUALIFIED` (via QUALIFIED) | row 0 -> `VOID` | F2 -> `VOID` |
| Precondition `P4` fails | `SURFACE_NOT_QUALIFIED` | row 0 -> `VOID` | F3 -> `VOID` |

Three sections assign three different terminals to the same event. Further:

- **`VOID` is defined as "Any §22 failure rule fires"**, which by construction subsumes F0
  (`T-INSTRUMENT-UNBOUNDED`), F4 (`CIRCULAR_BY_MEASUREMENT`), F5
  (`NO_ADMISSIBLE_SURFACE_EXISTS`), F6 (`ROUTING_INDETERMINATE`) and F7
  (`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`). Mutual exclusivity is violated by definition.
- **F8 emits `HALTED / VOID`** — two named terminals for one condition.
- **F10 has no terminal at all.** *"Any of D3's eight items unmet at verdict time -> No
  re-entry, regardless of the route."* "No re-entry" is not in §32. Exhaustiveness fails.
- **Stage 0's own terminals are absent.** If Stage 0 is the frozen D-INST protocol (tag
  `muru-freeze/dinst-protocol`, commit `7e99830`), its three terminals
  (`D-INST-DETERMINATE`, `D-INST-INDETERMINATE`, `D-INST-PLURALITY-NOT-INVARIANT`) appear
  nowhere in §32. See S10 for the deeper version of this.
- **Two terminals are unreachable** (S1).

**Changes terminal state:** YES, by definition.
**Minimal fix.** Make §22 the sole terminal-assigning authority; delete the terminal names
from §20 and §21.2 row 0 and replace them with references to the F-rule that fires; redefine
`VOID` as the *residual* ("any §22 rule not assigned a named terminal above"); give F8 one
terminal (`HALTED`, with `NON_LICENSING` as a stamp, not a state); give F10 a name
(`D3_ITEMS_UNMET`); and either fold Stage 0's terminals in or state that Stage 0 has its own
disjoint terminal set sealed separately.

---

# 3. HIGH-SEVERITY DEFECTS

## S9 — HIGH. The Stage 0 firewall is breached by `QND_PASS`, and `QND` is evaluated over a population that is plausibly empty, in which case F4 fires vacuously and forbids execution.

**(a) THE PROTOCOL STATES.** §0.1: Stage 0 *"may not be used to select, size, weight,
exclude or re-read anything in Stage 1 other than the binary gate below."* §18/§20:
`QUALIFIED` includes `QND_PASS`. §4 property (v): *"Before Stage 1 executes: enumerate
stratified subpopulations of **E2a's sealed corpus** that would pass Gate Q's measurable
clauses, and verify the routing verdict is **not constant** across them."* §22 F4: constant
=> `CIRCULAR_BY_MEASUREMENT`, **do not execute**.

**Two defects.**

1. **Firewall breach.** `QND_PASS` is a Stage-1 acceptance clause whose value is a function
   of the four-way partition computed on E2a — which is Stage 0's output (§0.1(a),(d)). If
   `QND` uses the corrected partition, Stage 0's *result* (not its binary gate) determines
   whether Stage 1 may execute at all. If it uses the sealed uncorrected partition, it is
   computed with the instrument the protocol's own §3 item 3 calls defective. The protocol
   does not say which. Either way the firewall claim in §0.1 is overstated.
2. **(c) GENUINELY UNSPECIFIED and plausibly vacuous.** "Gate Q's measurable clauses" is
   never enumerated. Read as `Q1` in full, **no E2a subpopulation can pass**: §3 item 2
   establishes that E2a *"instantiated none of the twelve prospectively declared Held-out
   G2 conditions"*, and Q1 requires *"the registry's twelve G2 conditions at equal weight
   `w_k = 1/12`"* and *"every cell carrying exactly 108 completed worlds"*. The enumeration
   is over the empty set. "The routing verdict is constant across them" is **vacuously
   true** over an empty family, so **F4 fires and execution is forbidden** — on the
   protocol's own most likely reading. The synthesis record (§9) assumes the opposite
   (*"§1.4 already shows the verdict varies ... which is evidence the check will pass"*)
   without noticing that §1.4's variation comes from *conditioning on noise*, not from
   Gate-Q-passing subpopulations.

**Changes terminal state:** YES — plausibly forces `CIRCULAR_BY_MEASUREMENT` before Stage 1
runs.
**Minimal fix.** Enumerate exactly which Q1 clauses are "measurable" on E2a (they are:
generator identity, `GENERATOR_VERSION`, `ROOT_SEED`, band disjointness, 30 seeds per
world — **not** the twelve-condition clause), declare the stratification variable
explicitly, declare the minimum family size, and state which resolution (`rho_bot` /
`rho_top` / sealed) the routing verdict is computed under. Then state whether an empty
family is `QND_PASS` or `QND_FAIL` — this must not be left to the executor.

## S10 — HIGH. The Stage 0 gate statistic `g_j` is undefined on the corpus Stage 0 runs on, and the only published measurement of it is standardised to the Held-out mix.

**(a) THE PROTOCOL STATES.** §20 defines `g_j = S_j_hat(rho_top) - S_j_hat(rho_bot)` where
`S_j_hat(rho) = SUM_k w_k * (1/n_k * SUM_{w in condition k} reach_j(w; rho))`, `w_k = 1/12`
over **the twelve registry G2 conditions**. §0.1 applies `g_j <= 0.010 for j = 1,2,3` to
the sealed E2a corpus.

**The defect.** E2a contains **none** of the twelve registry conditions (§3 item 2). The
`w_k`-weighted statistic is therefore undefined on E2a, and the gate has no computable
value as written. §0.2 nevertheless reports *"the standardised determinacy gap is
0.044-0.056"*. `SYNTHESIS_DECISION_RECORD.md` §1.3 shows where the standardisation comes
from: *"Standardising E2a to the **Held-out truth-family mix** (affine 108/144, saturating /
interaction / exponential 12/144 each, `mass_power` 0)"*. So the gate that authorises Stage
1 is, in the only form in which it has ever been computed, **a function of the Held-out
composition**. That is E2b entering the gate that permits the licensing instrument to run.
It is upstream of any verdict and it can only stop execution, so it is not positive
licensing — but it is not the zero-E2b firewall §0.1 advertises either.

**Changes terminal state:** YES — the gate's definition determines whether
`T-INSTRUMENT-UNBOUNDED` fires.
**Minimal fix.** Define the Stage 0 statistic separately and explicitly: an **unweighted**
determinacy gap over E2a's own 539 worlds (`g_j^{E2a} = S_j(rho_top) - S_j(rho_bot)`, equal
weight per world), stated as a distinct quantity from Stage 1's `w_k`-weighted `g_j`. State
that no Held-out-derived weighting enters the Stage 0 gate. Recompute and re-record the
0.044-0.056 figure under that definition before freeze.

## S11 — HIGH. `T-INSTRUMENT-UNBOUNDED`'s name and gloss misrepresent what a Stage 0 failure establishes — and a Stage 0 PASS establishes nothing about Stage 1's population.

This is the same defect class `DINST_HOSTILE_REVIEW.md` D4 found in Stage 0's own protocol
(*"§9's terminal-state gloss can label the maximal overturn 'attribution stands as
sealed'"*), recurring one level up.

**(a) THE PROTOCOL STATES.** §22 F0 / §32: *"`T-INSTRUMENT-UNBOUNDED` — the G2 contract as
frozen is not decidable at finite cost **on this class of population**."*

**The defect, both directions.**
- **Over-generalization on FAIL.** Stage 0 runs on E2a. Stage 1's population is, by the
  protocol's own §3 item 2, a *different class* — E2a shares no condition with it. A
  determinacy failure on E2a licenses no statement about the calibration partition.
- **Under-generalization on PASS.** E2a lacks **F17**, the condition the frozen registry
  declares as *"equivalent symbolic forms" / "canonicalize equivalent laws"*
  (`SYNTHESIS_DECISION_RECORD.md` §1.6, verified against `registry.py`) — i.e. precisely the
  condition purpose-built to generate canonicalization-expensive expressions. Stage 0 passing
  on a corpus with **zero** F17 worlds gives the weakest possible evidence that the
  instrument is bounded on a corpus with **108** of them. The gate is calibrated on the easy
  case and generalized to the hard one.

**Changes terminal state:** the name does not change which state fires, but it changes what
the state is reported to mean — which is the whole content of a terminal state.
**Minimal fix.** Rename to `T-INSTRUMENT-UNBOUNDED-ON-E2A` and rewrite the gloss: *"the
frozen G2 contract is not decidable at finite cost on the sealed E2a corpus. This is a
finding about the contract and the E2a corpus. It does not establish decidability or
undecidability on the calibration partition, which contains 108 F17 worlds that E2a does not
contain."* Then add an explicit, pre-declared F17 escalation-cost pilot to Stage 0's
publications, or state that no such assurance exists.

## S12 — HIGH. No freeze has occurred. §31 is entirely unexecuted, and the one freeze record in this directory is already stale.

**(a) D3 item 7 requires** a *"results-blind freeze before new outcomes are inspected"*;
ratification §5 lists it **PENDING**. §31 requires a manifest of SHA-256 hashes, a freeze
commit that is a strict ancestor of the first data commit, a tuning ledger registered at the
freeze commit, and an auditable surface count.

**Verified state on disk.**
```
ls audit/muru_v2_reentry_20260819/ | grep -i "sha|freeze|manifest"
  -> DINST_FREEZE_SHA256.txt          (Stage 0 only)
git tag | grep reentry                -> (nothing)
```
There is **no** hash manifest, **no** freeze tag, and **no** tuning ledger for this
protocol. Yet line 16 states *"**Status at this commit:** frozen protocol text"*. The
document asserts a freeze that has not been performed.

**Worse — the existing instance of the §31 pattern has already failed.**
```
sha256sum scripts/e2a_instrument_diagnostic.py
  b1476f8840c8c3709409c4d0906c95ba89e1f03475ee202abaa19bba03a060b0
cat audit/muru_v2_reentry_20260819/DINST_FREEZE_SHA256.txt
  14a50d51da41a15d96f4b33ce682e6a0e0034c72aa28ec99043f41868eea005a  scripts/e2a_instrument_diagnostic.py
```
The frozen tool was replaced (the review-mandated repair) and the freeze record was **not
updated and not superseded**. `DINST_FREEZE_SHA256.txt` now asserts a hash that does not
match the file it names — a freeze record that fails its own verification. §31's step 1
(*"re-verifying every recorded hash"*) would fail today, on the only artifact in this
directory it could be run against. Note also that the D-INST **protocol** hash still matches
the freeze, i.e. the protocol text was **not** amended despite `DINST_REVIEW = FAIL` naming
blocking defects against the protocol (D3, D4, D5, D6), not only the tool.

**Changes terminal state:** NO, but it means D3 item 7 is unmet and the document may not be
called frozen.
**Minimal fix.** (i) Change line 16 to *"Status: protocol text, NOT YET FROZEN. D3 item 7
is unmet."* (ii) Supersede `DINST_FREEZE_SHA256.txt` with `DINST_FREEZE_SHA256_v2.txt`
recording the repaired tool's hash and the review that mandated the change; never silently
overwrite a freeze record. (iii) Perform §31 for this protocol, with an annotated tag, before
any Stage 0 compute. (iv) Re-freeze or formally amend the D-INST **protocol** text against
its own failed review.

## S13 — HIGH. The independent adjudicator is a placeholder. D3 item 6 is not satisfied by a table that says "named before execution".

**(a) D3 item 6 requires** an *"independent adjudication procedure"*.

**(a) THE PROTOCOL STATES.** §29: *"**ADJUDICATOR** — **Named before execution.**
Independent of the design author."* No name. No definition of "independent". No statement of
what makes CRITIC_A and CRITIC_B independent, of each other or of the author. §30 requires a
pre-freeze hostile review engaging six enumerated attacks; none has been run against this
document (this review is the first, and I am not the adjudicator).

**(b) REASONABLE READING.** The Gate 1 adjudication did execute a real four-role structure
(`GATE_1_DEFINITIVE.json`: `CRITIC_A = PASS`, `CRITIC_B = PASS`,
`EVALUATOR_DISAGREEMENTS = 0`, `AGENT3_VS_AGENT4_CASE_MATCHES = 144/144`), so the *structure*
is proven executable. The protocol reuses the structure honestly.

**The defect.** Reusing a structure is not registering an adjudicator. §29's own strongest
requirement — that the Gate-V adjudicator be *"a **different** named party"* who *"may not
see Gate V before sealing Gate R"* — is unenforceable against a party that does not exist,
and the mechanical enforcement offered (`git merge-base --is-ancestor`, hash-chained log)
proves **commit order**, not **information order**. The Gate V target `pi_0` is printed
verbatim in §21.3 of the document every party reads before Gate R runs. The information
barrier is zero; only the artifact barrier is real.

**Changes terminal state:** NO, but D3 item 6 remains PENDING and no verdict issued without
it is admissible.
**Minimal fix.** Register the four parties by name (agent identity, model, invocation
context, and what each may and may not read) in the freeze commit, and state explicitly that
the ordering guarantee is **artifact-order only**, since `pi_0` is public in the protocol
text. That is a weaker but honest claim, and it is the claim the mechanism actually supports.

## S14 — HIGH. The E6 circular dependency makes every licence non-executable, and the protocol defers resolving it to a step ("before freeze") that has not happened.

**(a) FROZEN AUTHORITY STATES.** `git show befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3
confirms the ceiling verbatim: *"unsafe acceptance Wilson upper <= 0.15 => change survives"*
on *"100 evaluable safety opportunities"*. Citation verified.

**(a) THE PROTOCOL STATES.** §21.4 rider 1: *"**If E6 cannot supply a ceiling at decision
time — and E6 is self-blocked pending exactly this hook — every licence is CONDITIONAL and
NON-EXECUTABLE.** This circular dependency must be resolved by the protocol owner **before
freeze**, not discovered at the end."* §32's `E4A_LICENSED_AT_<arm>` requires *"E6 ceiling
available and met"*.

**The defect.** The protocol correctly identifies a blocking circularity and then freezes
around it, converting an unresolved precondition of its own freeze into a rider. As it
stands, `E4A_LICENSED_AT_<arm>` is unreachable for a **second, independent** reason beyond
S1. A protocol may not declare itself frozen while a named precondition of its freeze is
open.

**Changes terminal state:** YES (independently of S1).
**Minimal fix.** Escalate before freeze and record the owner's answer in the document. If
the owner cannot supply the ceiling, delete the licensing terminals (which S1 requires
anyway) and re-label the protocol as falsification-only.

---

# 4. MEDIUM-SEVERITY DEFECTS

## S15 — MEDIUM. §10's resolving-power table does not reproduce from the protocol's own formula and its own declared bound. Every entry is optimistic.

Recomputed with `z_.95 = 1.6448536`, `z_.80 = 0.8416212`, `K = (z_.95+z_.80)^2 =
6.1825569`, and the protocol's **declared** distribution-free bound `pi_1 + pi_2 <= 1`,
solving `d^2 (n + K) = K`:

| n | protocol says | correct | protocol's "units of delta" | correct |
|---:|---:|---:|---:|---:|
| 84 | 0.2429 | **0.2618** | 3.50 | **3.77** |
| 252 | 0.1448 | **0.1547** | 2.08 | **2.23** |
| 576 | 0.0964 | **0.1031** | 1.39 | **1.48** |
| 1296 | 0.0659 | **0.0689** | 0.95 | **0.99** |

The implied `pi_1 + pi_2` behind the reported figures is 0.861 / 0.876 / 0.875 / 0.915 —
not 1, and not constant, so it is not a single alternative assumption either. The headline
sizing itself is **correct** (`n >= 1275.83`, verified exactly), so `n = 1296` does not
change; but the table understates the required `n` throughout, and the `n = 1296` row is the
one that carries the claim *"sized so that a lead of `delta` is certifiable"* — at `0.99
delta` rather than the advertised `0.95 delta`, which is the margin S6 relies on.

**Changes terminal state:** NO. **Minimal fix.** Replace the table with the recomputed
values and show the solve.

## S16 — MEDIUM. Design-layer E2b conditioning in the population choice, disclosed but not discharged.

**(a) THE PROTOCOL STATES.** §3 item 1: *"Direct-standardising E2a to the Held-out
truth-family mix removes **68.1%** of the total-variation divergence pooled over noise and
**77.0%** noise-matched."* §7 then sets the new population's family composition to reproduce
the Held-out mix exactly.

**(a) THE SYNTHESIS RECORD STATES** (§1.3) a table whose columns are `TV vs Held-out`,
`cases/144` and `argmax`, over four candidate design configurations (raw / +composition std
/ +noise-matched / +instrument corrected). Candidate designs were evaluated by how far they
move the surface toward the sealed Held-out attribution.

**(b) REASONABLE READING — and it is a good one.** The population rule cites `registry.py`
and no outcome. The registry's twelve `held_out` G2 conditions were declared prospectively
and results-blind, long before any E2. Matching them is defensible on provenance grounds
alone, and §4 property (i) is correct that Gate Q reads no E2b artifact.

**The defect.** Property (i) and (iii) are proofs about the *predicate* and about *per-arm
channel monotonicity*. Neither covers *design-layer conditioning*: the endpoint's population
was selected in a document that had `pi_0` in hand and reported the selection's effect on
distance-to-`pi_0`. The protocol knows this — §30 attack 1 states the charge in the
adversary's own words (*"you matched composition because you saw that matching composition
moves E2a toward E2b"*) and proposes to answer it by blind replication. **That review has
not been performed.** Until it is, the charge stands unanswered, and §4's property table
overstates what it has established.

**Changes terminal state:** NO. **Minimal fix.** Either run §30 attack 1 (an agent blind to
§1.3 and §3 item 1 re-derives the population from `registry.py` alone) **before** freeze and
record the result, or downgrade §4 property (i) from *"reads no E2b artifact"* to *"the Gate
Q predicate reads no E2b artifact; the population's composition rule was selected in a
document that had access to `pi_0`, and the provenance argument is independent but was not
independently generated."*

## S17 — MEDIUM. §21.2 row 3 cites `f4c1105` as "a complete operational freeze" for E4a, but `f4c1105`'s own execution trigger has already fired STOP.

**(a) FROZEN AUTHORITY STATES.** `f4c1105` §4: *"GATE 1 (falsification hook, **checked
first**) ... IF E2b's direct measurement contradicts ... by more than 10 cases -- THEN this
protocol **DOES NOT EXECUTE**. All E4 ablations are suspended ... **STOP.**"*
`GATE_1_DEFINITIVE.json`: `/E2B_69_57_HOOK = "FAIL"`, `/GATE_1 = "FAIL"`,
`/GATE_1_DEFINITIVE = "YES"`, `/THRESHOLD_TRIGGERED = "YES"`. **Gate 1 has fired STOP.**

**(a) THE PROTOCOL STATES.** §21.2 row 3, "Executable today?": *"**Yes** — `f4c1105` is a
complete operational freeze"*.

**The defect.** `f4c1105` is operationally complete but **terminated**. Its own first gate
returned STOP on the sealed evidence, and nothing in the ratification re-arms it. The
protocol replaces `f4c1105`'s GATE 1 (E2b vs 69/57, count-based, checked first) with its own
Gate V (TV vs `pi_0`, checked last) and treats the substitution as verbatim reuse — the same
mislabel as S7, in the opposite direction. Moving the hook after the seal is defensible and
probably better governance (a veto applied before sealing is a selector); calling the result
"verbatim" is not.

**Changes terminal state:** NO directly. **Minimal fix.** Add to §21.2 row 3: *"`f4c1105`
is operationally complete but its own §4 GATE 1 returned STOP on the sealed Gate 1 result.
Executing it requires the protocol owner to re-arm it against this surface's Gate V in place
of its frozen Gate 1. That substitution is a change to frozen authority and requires
ratification; it is not reuse."*

## S18 — MEDIUM. `QUALIFIED` has two different definitions in the same frozen document.

§18: `QUALIFIED := Q1 AND C-1..C-5 AND SCHEMA_COMPLETE AND INDETERMINATE_WORLDS == 0 AND
QND_PASS`.
§20: `QUALIFIED := Q1 AND C-1..C-5 AND QND_PASS AND P1..P10 AND INDETERMINATE_WORLDS == 0`.

§18 omits `P1..P10` entirely (nine preconditions including `SINGLE_SHOT`,
`ORDINAL_STABILITY`, `HOST_INVARIANT_LABELS`). A frozen acceptance predicate must have
exactly one definition.
**Minimal fix.** Delete §18's version; make §18 reference §20.

## S19 — MEDIUM. `PARTITION_CASE_COUNTS` is misread. `"calibration": 108` declares 108 replicates for all twenty families, not 1,512 worlds.

**(a) FROZEN AUTHORITY STATES.** `src/muru/paper_benchmark/registry.py:14-15,206-225`:
`PARTITION_CASE_COUNTS` values are **replicates per family per partition** —
`family.partition_counts[partition]` bounds the replicate index (`:214`) and
`iter_case_ids` yields `range(family.partition_counts[partition])` for **every** family
(`:224-225`). Check: 20 families x (4 + 12 + 3) = 380 = `A35_TOTAL_CASES`. Confirmed.

**The defect.** `{"calibration": 108}` therefore declares 108 replicates for **all twenty**
families = **2,160 cases**, not the 1,512 the protocol searches. §5's "not searched: F06,
F13-F16, F20 -- 0 worlds" contradicts the registry's own enumeration, which will emit 648
`calibration` case_ids for those six families. Consequences: the new seed band must be sized
for 2,160 x 30 = 64,800 seeds (§11's rule keys on `case_ordinal` over the full enumeration),
not 45,360; and precondition P1 (`COMPOSITION_EXACT`) is silent about 648 declared-but-absent
cases. Separately, each of the twenty `FamilySpec` literals carries its own
`partition_counts` mapping, so the amendment touches twenty more places in `registry.py` —
compounding S2.

**Changes terminal state:** the preflight (§12) would catch it, terminating at
`NO_ADMISSIBLE_SURFACE_EXISTS` — a terminal whose gloss (*"implies a mechanical/benchmark
defect requiring audit before anything else proceeds"*) would then misattribute a protocol
drafting error to the benchmark.
**Minimal fix.** Declare `partition_counts["calibration"] = 108` on exactly the fourteen
searched families and `0` on the other six, and restate §5's totals against
`iter_case_ids`.

## S20 — MEDIUM. F9 (`> 1 surface => VOID`) contradicts §5.1's two pre-enumerated attempts and §10's blinded top-up.

§22 F9: *"**More than one surface generated**, or the tuning ledger is non-empty ... =>
VOID."* But §5.1 pre-enumerates a second attempt (the `development` u `challenge` fallback)
and §22 F5 explicitly contemplates *"Q1 fails on **both** pre-enumerated attempts"*; and §10
pre-declares extending the surface to `12 x 162 = 1,944` worlds. Neither is a *tuning*
event — both are blind and pre-declared, which is the property that matters — but "surface"
is never defined, so F9 as written voids the protocol's own pre-declared branches.
**Minimal fix.** Define `SURFACE_COUNT` as the number of **independently parameterized**
surfaces, state that the §10 extension is the same surface, and state that §5.1's fallback
is reachable only after the amendment attempt terminates at `Q1 = FAIL` — with both
counted in the ledger.

## S21 — MEDIUM. Stage 0's primary input is unhashed, mutable and outside the repository, and §31's manifest does not cover it — yet it gates Stage 1.

`DINST_HOSTILE_REVIEW.md` D9 (unrepaired at the protocol level): *"`CACHE =
~/e2_x86_cache/classify_cache.sqlite3`, 89 MB, not in `DINST_FREEZE_SHA256.txt`, not in git,
freely mutable between freeze and execution"*, and read *"with **no `WHERE version = ?`**"*
although the table is keyed `(version, expression_string)`. `SYNTHESIS_DECISION_RECORD.md`
§1.1 confirms this cache is the join source for the 397/396 figures the protocol reproduces
in §3 item 3.

Since Stage 0's gate decides whether Stage 1 runs at all, a mutable out-of-repo artifact is
in the gating path and outside §31's freeze manifest.
**Minimal fix.** Hash the cache into the freeze manifest, add the `version` filter, and
re-verify the hash at Stage 0 seal time. If the cache cannot be frozen, state that Stage 0's
determinacy figures are conditional on an unhashed input.

## S22 — MEDIUM. §3 item 3 and §25 reproduce two D-INST figures the hostile review showed are unsound, without the correction.

`DINST_HOSTILE_REVIEW.md` **D8**: the per-stage contamination table *"over-counts B/C/E
roughly 2x"* because *"a row counts as abandoned if **any** world's classification of that
string timed out"*, and 48,790/70,322 B rows, 31,781/35,988 C rows and 36,525/40,746 E rows
are **absent from the cache entirely** — *"§3's 'B 20 / C 3 / E 1 worlds contaminated' is an
**upper bound presented as an observation**."* **D14**: the named mechanism
(`signal.alarm(5)`) is not the operative cap; the authoritative one is
`conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` at `e2_classify.py:338`, which *"also absorbs pipe and
worker failures under the same `SIMPLIFY_TIMEOUT` name"*, so *"some of the 397 cached
timeouts may not be simplify timeouts at all."*

The re-entry protocol §3 item 3 reproduces *"397 distinct expressions / 396 rows ...
concentrated 59.8% in stage A"* and §25 reproduces *"it decided 314 row labels inside 73 of
E2a's 122 stage-A worlds"* with no upper-bound qualifier and with the superseded mechanism
named. The stage-A figure is sound (D8: *"0 of 42,411 A-world rows are absent from the
cache"*); the B/C/E comparisons carried alongside it are not.
**Minimal fix.** Two clauses: label the B/C/E figures as inferred upper bounds; name the
operative cap as the parent-side `conn.poll`, noting some `SIMPLIFY_TIMEOUT` records are
pipe/worker failures.

---

# 5. LOW-SEVERITY

## S23 — LOW. The filename says PREREGISTRATION. The ratification forbids it.

**(a) FROZEN AUTHORITY STATES.** Ratification §10: *"Documents created under that authority
are **prospective post-Gate-1 protocol-owner amendments**. They are **not** historically
preregistered and **must never be described as such**."*

**The body text is exemplary** — the first three lines are the disclaimer, and I found **no**
sentence in either document implying historical freeze. `SYNTHESIS_DECISION_RECORD.md`
carries the same disclaimer. Every remaining occurrence of "preregistration" refers to
`f4c1105`'s actual preregistration or to E4f's *absence* of one. This is the cleanest part
of the submission.

**The defect is the identifier.** The file is
`MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md`. A filename is how a document is described
in every citation, commit message, manifest and cross-reference — and it is the one string
that travels without the disclaimer attached. Gate 1's record already had to withdraw a
provenance misstatement of this exact kind, as the header itself notes.
**Minimal fix.** `git mv` to `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_AMENDMENT.md` before the
freeze commit (afterwards it costs a hash re-issue), and update the two cross-references in
`SYNTHESIS_DECISION_RECORD.md`.

## S24 — LOW. The protocol self-satisfies D3 item 8 and issues its own licence with no owner ratification step.

D2-ext: *"There is no automatic E4 re-entry."* D3 item 8: *"**Successful execution of that
qualification protocol**."* §32's `E4A_LICENSED_AT_<arm>` fires on the protocol's own
adjudicated verdict, and §22 F10 conditions it on all eight D3 items — of which item 8 is
the protocol's own success. The loop closes without the protocol owner. Every prior gate in
this programme (D1-D6, the ratification itself) was an owner act recorded by an analyst.
Moot while S1 stands, but it should not depend on S1.
**Minimal fix.** Insert between the adjudicated verdict and any licensing terminal: *"a
licence is proposed, not issued. It becomes operative only on a protocol-owner ratification
record naming the arm and the parameter setting."*

## S25 — LOW. D4 (E5 DEFERRED) is never carried forward.

`grep -n "E5" ` returns **zero** hits in the protocol. D4 states E5 *"is reconsidered
automatically if and only if the newly qualified causal path makes it scientifically
relevant and its dependencies are prospectively satisfied."* Silence honours the deferral
but drops the conditional reconsideration trigger, so nothing in the protocol would ever
fire it. Informational.
**Minimal fix.** One line in §32: *"No terminal of this protocol reconsiders E5. D4's
reconsideration trigger remains with the protocol owner."*

---

# 6. CHECKS THAT PASSED — recorded so the FAIL is not read as a blanket rejection

I attacked these and could not break them.

| # | Check | Result |
|---|---|---|
| 1 | **Labelling of the body text** | **PASS.** Both documents open with the required disclaimer; no sentence implies historical freeze; every "preregistration" refers to `f4c1105` or to E4f's absence of one. Only the filename fails (S23) |
| 2 | **Sealed Gate 1 unaltered** | **PASS.** No protocol text reopens, recomputes or re-maps Gate 1. §3 explicitly forbids the timer explanation. `GATE_1_DEFINITIVE.json` is cited only for `pi_0` and for precedents |
| 3 | **D5 consistency, forward direction** | **PASS.** The verified cap-invariance finding (`SYNTHESIS_DECISION_RECORD.md` §1.2, `DINST_HOSTILE_REVIEW.md` D5) is used **only** defensively — to refute the timer explanation and to establish that the correction moves E2a *away* from Held-out. `LOCKED_EXECUTE_E4A` is never restored. §26 uses E2a as an engineering DEV set **because** D5 invalidated it, which is the correct inference |
| 4 | **D5 consistency, reverse direction** | **PASS.** The protocol does **not** misstate D5 as resting on measurement indeterminacy. §3 states the opposite explicitly (item 3: the instrument failure is *"real, quantified, and NOT the explanation"*). Minor note, not a defect: §3's ranking of *composition* as D5's primary ground is the protocol's own reconstruction — ratification §7 gives only "a limitation on **role**", and `befca0d` §2.3's textual ground is divergence. The reconstruction is reasonable and does not weaken D5 |
| 5 | **Schema / D6** | **PASS.** §14's 21 search-side fields and §17's 7 post-hoc fields match `git show befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.4 **exactly**, field for field, including row-level `admissibility`. §15 stamps it at write time. §20 P4 and §22 F3 enforce it with a hard-coded frozen validator, no back-fill, VOID on any post-seal write. No existing corpus is reused as the decision surface; §26's use of E2a is engineering-only and non-scoring. `resolution_state` is an addition, not an omission. **D6 is honoured** |
| 6 | **Per-arm channel monotonicity** | **PASS as stated.** §4 property (iii) is true per-arm. It is the *composite* map that fails (S1) |
| 7 | **Order enforcement is real, as far as it goes** | **PASS with caveat.** `git merge-base --is-ancestor` plus a hash-chained event log is a genuine, falsifiable artifact-order guarantee, and the `AUTONOMOUS_RUN_EVENT_LOG.jsonl` pattern exists and works. It proves artifact order, not information order (S13) |
| 8 | **E6 ceiling citation** | **VERIFIED.** `befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3 contains *"unsafe acceptance Wilson upper <= 0.15"* on *"100 evaluable safety opportunities"*, verbatim |
| 9 | **E3 verdict citations** | **VERIFIED.** `git show 1d20731:E3_RESULTS.md:76-78`: `mass_saturating_descriptor` **0.820 IDENTIFIABLE**; `mass_affine_descriptor` **0.553 MARGINAL**; `mass_exponential_descriptor` **0.527 MARGINAL**; `mass_interaction` **1.000 IDENTIFIABLE**. All four verified. §7's and §21.2 row 4's use of these is correct, including the "10 of 12 conditions" consequence |
| 10 | **`befca0d`:466 citation** | **VERIFIED.** Line 466 is PE2-4. The *location* is right; the *re-purposing* is S5 |
| 11 | **`befca0d` §2.3 is destructive-only** | **VERIFIED.** *"If E2a and E2b disagree, that is itself a finding and it blocks adoption ... which invalidates E2a as a calibration surface."* No positive force attaches to agreement. §3 and §18 characterize this correctly, and Ruling 1's rejection of Held-out-matching qualification follows from it |
| 12 | **`n = 1275.83` sizing** | **VERIFIED EXACTLY.** `0.9951775 * 6.1825569 / 0.00482253 = 1275.83`. `1296 = 12 x 108` is the smallest lattice point above it with `R` divisible by 6. The *table* beneath it is wrong (S15); the sizing is right |
| 13 | **Registry facts** | **VERIFIED** against `registry.py`: `ROOT_SEED = 20260813`; `PARTITIONS = ("development","held_out","challenge")`; twelve G2 conditions; F17 present with the quoted purpose |
| 14 | **Timeout cannot become a classification** | **PASS.** §24 and §25 are the strongest sections in the document. `UNRESOLVED` is its own state, never folded; `INDETERMINATE` is its own state and VOIDs the run; the cap exception derives from `BaseException` so `g2_contract`'s seven `except Exception` handlers cannot swallow it; the monotonicity argument (disjunctions over row labels; `retained_by_argmax_score` label-independent; representative selection never reads `g2_correct`) is correct and reduces `2^U` to two evaluations. **No wall-clock cap decides a label anywhere.** This prohibition is fully honoured |
| 15 | **Threshold-after-result / post-result design** | **PASS, vacuously but genuinely.** Nothing has executed. Every constant is on the page before any world exists, §33 inventories them, and §34 pre-records the expected outcome including a disclosure that the design most likely to deliver re-entry was rejected *because* it was expected to pass. The provenance *labels* are wrong in places (S4, S5); the *timing* discipline is intact |

---

# 7. WHAT I COULD NOT DETERMINE

- Whether Stage 0 is the frozen D-INST protocol (`muru-freeze/dinst-protocol`, `7e99830`)
  or the different, narrower procedure described in §0.1 of the re-entry protocol. They
  differ in scope (73 affected worlds and 314 rows vs all 397 expressions), in budget
  (`DIAGNOSTIC_ESCALATION_SECONDS = 1800` vs uncapped tier-2), in output (stage invariance
  vs `g_j` for j=1,2,3) and in terminal set. **(c) GENUINELY UNSPECIFIED.** The re-entry
  protocol never names D-INST. If §0.1 supersedes D-INST it must say so and D-INST's freeze
  must be withdrawn; if D-INST is Stage 0 then §0.1's gate is not computable from D-INST's
  outputs. This should be resolved before anything else, because S9, S10, S11 and S21 all
  depend on which is true.
- The compute cost. At `befca0d` §2.10's measured 2.30 s/serial run, 45,360 searches is
  ~29 CPU-hours before scoring, escalation, the NEG stratum, the A3 host-determinism double
  run, and a possible 1.5x top-up. The protocol states no budget anywhere. Not a governance
  defect, but a `TIMEOUT`/abandonment risk on a protocol whose §22 F9 forbids a second
  attempt.

---

# 8. MINIMAL PATH TO A PASS

In order. Items 1-3 are the ones that decide whether this protocol is worth executing.

1. **Resolve S1.** Compute the Gate V reachability arithmetic, put it in the document, and
   choose: delete the licensing terminals, or move Gate V off the routing statistic under
   owner authority, or raise `n` to >= 8,006. Nothing else matters until this is settled.
2. **Resolve S2.** Either obtain an authorized-delta for `registry.py` under the pb_33/pb_34
   mechanism, or make §5.1's fallback the primary. Correct §5's false statement about which
   modules `pb_30/33/34` pin.
3. **Resolve S14** (E6 ceiling) with the protocol owner, before freeze, as §21.4 itself
   demands.
4. **Define `TV`** (S3). **Fix the certification rule to `LCB > 0 AND lead >= delta`** (S6).
   **Declare row 1's band** and restore or disclose its frozen position (S7).
5. **Rewrite the threshold-provenance claims** honestly (S4, S5) and **fix the
   resolving-power table** (S15).
6. **Make §22 the sole terminal authority** and repair exclusivity, exhaustiveness and the
   two misleading terminal names (S8, S11).
7. **Specify `QND`** — measurable clauses, stratification, empty-family disposition — and
   state which corpus resolution it uses (S9). **Define the Stage 0 statistic without
   Held-out weighting** (S10). **Say which document is Stage 0** (§7 above).
8. **Perform §31** and supersede the stale `DINST_FREEZE_SHA256.txt` (S12). **Register the
   adjudicators by name** (S13). **Run §30 attack 1 blind** (S16).
9. **Rename the file** (S23).

Items 4-9 are all repairable inside the document without changing the science. Items 1-3 are
not; they require the protocol owner.

---

**TERMINAL STATE OF THIS REVIEW: `CRITIC_GOVERNANCE = FAIL`.**
**No result was inspected. No compute was run against any surface. This review licenses
nothing and alters no sealed evidence.**
