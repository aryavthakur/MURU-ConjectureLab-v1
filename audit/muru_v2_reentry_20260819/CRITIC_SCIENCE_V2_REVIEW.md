# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF PROTOCOL v2

# VERDICT: FAIL

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V2.md`
(2,232 lines, unfrozen text at HEAD `906c9d4`).
**Reviewer stance:** hostile. Default FAIL on uncertainty. Reward is for falsification.
**Method:** full read of the target; direct execution of the code it cites
(`seed_band_registry`, `rc5_seeds`, `registry`, `pb_33`, `pb_34`,
`scripts/e2a_instrument_diagnostic.py`); independent recomputation of every number in
§10.4, §10.5, §21.4 and §32.1; `git log` provenance; 14 ledger claims spot-checked.

**Counts:** 3 CRITICAL · 9 HIGH · 10 MED · 1 LOW.

**Headline.** v2's central claim is that the defect that killed v1 — *no reachable positive
terminal* — cannot recur, because §32.1 exhibits constructive witnesses. **The witnesses are
arithmetically correct and I could not break their arithmetic.** But the reachability proof
is not a proof, because it verifies the witnesses against §21 (the routing predicate) and
asserts rather than checks them against Gate Q. Executed against Gate Q's actual code, **all
four witnesses fail `QUALIFIED` deterministically, for a reason independent of any data**
(`DEF-C1`). Under the protocol as written the only reachable Stage-1 terminal is
`BENCHMARK_INTEGRITY_DEFECT` — a *false accusation against the benchmark caused by a protocol
drafting error*, which is precisely the harm defect `D8` was raised about and which the ledger
records as FIXED.

Separately, the protocol's most emphatic rule — *"no wall-clock cap, memory cap … may decide a
scientific label or a scientific terminal anywhere in this protocol, at any level, including
meta-level terminals"* (header; §25) — is violated by the instrument the protocol designates
as Stage 0, in the repository, at HEAD, **and that instrument is running right now, before the
freeze it gates** (`DEF-C2`, `DEF-C3`).

**What I could not break, and credit where it is due.** §10.4/§10.5's arithmetic reproduces
exactly from the stated formulae (v1's `D11`/`S15` defect is genuinely repaired). §21.4's `TV`
and `D_max` values reproduce to the digit for all five distributions. §32.1's `LCB` column
reproduces to 6 decimal places for all four witnesses. `pb_33` and `pb_34` both return 0
errors on this host as claimed. `registry.resolve_case_id("PBC|…")` does raise `ValueError` as
claimed. `PARTITION_CASE_COUNTS` is the 3-key dict `S19` describes. `rc5_seeds.A35_SEARCH_SEED_MAX
= 2100011399`, so the derived band base is correct. The `D9` re-keying of the canonicalisation
table to `(status, effective_support, discovered_family)` is correct: all three are functions
of the expression alone in `g2_contract`. The `S16` blind re-derivation is methodologically
serious and its rule (`endpoint_applies_to_variant("family_recovery", ·)`, equivalently
`symbolic == "defined"`) selects **exactly** the twelve declared families with no discretion —
I verified this independently against `registry.py:135–152`. The document is unusually honest
about its own weaknesses. None of that is enough.

---

# PART 1 — DEFECTS

## DEF-C1 — CRITICAL. Gate Q's seed-band clause fails unconditionally. Every §32.1 witness fails `QUALIFIED`. The constructive reachability proof does not hold.

**Location:** `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V2.md:1157` (§18, clause `Q1`) and
`:601–607` (§5.2); consumed by `:1252–1256` (§20 `P9`) and `:1531` (§22 `F2`).

**Q1 states, verbatim (line 1157):**

> *"seed band declared by the §5.2 rule and **disjoint under `seed_band_registry.find_overlaps`**"*

**§5.2 (line 606) states the check operationally:**

> *"Disjointness is checked by the frozen registry's **own** checker,
> `seed_band_registry.find_overlaps(DECLARED_BANDS + (CALIBRATION_BAND,))`"*

**Executed on this host:**

```
$ python3 -c "from muru.paper_benchmark import seed_band_registry as sbr; print(sbr.find_overlaps(sbr.DECLARED_BANDS))"
[Overlap(band_a='objval_plan2', band_b='rc3_engineering_smoke', lo=1900000000, hi=1900999999)]
```

`find_overlaps` is **never empty**, with or without the calibration band, because
`objval_plan2 = [1700000000, 2099999929]` strictly contains
`rc3_engineering_smoke = [1900000000, 1900999999]`. This is a **pre-existing, acknowledged**
collision: `seed_band_registry.py:306` defines `ACKNOWLEDGED_COLLISIONS`, and
`:311 unacknowledged_overlaps()` is the governance-clean predicate — the one the protocol
*displays* in its own §5.2 evidence block (`:614`, `unacknowledged_overlaps() = []`) but
**not** the one it *mandates* in Q1 and §5.2's check line.

**Failure scenario, fully concrete.** The surface is generated. Everything works. The
adjudicator applies §20's `QUALIFIED` predicate mechanically, as §29 requires ("applies the
frozen §20/§21 predicates mechanically … may not modify any predicate"). Q1's seed-band clause
evaluates `find_overlaps(...) != []` → Q1 FAILS → `QUALIFIED = FALSE` → §22 `F2` fires →
terminal **`BENCHMARK_INTEGRITY_DEFECT`**, whose §32 gloss is *"**This is** the claim that the
benchmark needs auditing before anything else proceeds."* The benchmark is not defective. The
protocol misread its own checker. 62.7 CPU-hours of search and an unbounded scoring tail are
spent to publish a false accusation, and §22's "no rehabilitation path" plus §20's "no
margin, endpoint, weight, stratum, exclusion, conditioning set, or population may be revised
in response" forbid fixing it afterwards.

**Consequence for the reachability proof.** §32.1 line 1976 claims the four witnesses
*"satisfy every Gate Q clause by construction"*. They do not. **Every one of W-B, W-A, W-CD
and W-EX fails Q1 for a reason that has nothing to do with its `(A,B,C+D,E)` vector.** The
proof verifies the witnesses against §21.1 and §21.2 (which it does correctly) and takes Gate
Q on trust. That is exactly the failure mode of v1: a licensing path checked against one gate
and not against the conjunction. `NON_DETERMINATION_PROVEN` is likewise undischarged, because
its premise clause (a) — *"satisfies **every** clause of Gate Q by construction"* — is false
for all witnesses.

**Minimal repair.** Change Q1 and §5.2 to name `seed_band_registry.unacknowledged_overlaps`
(or `assert_governance_clean`), and add to §31's freeze procedure a mechanical step that
**executes** every Gate Q clause against the four §32.1 witnesses and refuses to freeze if any
clause fails for a witness-independent reason. §32.1 already promises "a frozen script
re-verifies each witness against each Gate Q clause … at freeze time" (line 424); that script
does not exist, and had it been run once, this defect would have surfaced.

---

## DEF-C2 — CRITICAL. A 1500 s wall-clock cap and a 6 GiB address-space cap decide the Stage 0 scientific terminal. §25's governing rule is violated by the instrument the protocol designates as Stage 0.

**Location:** protocol `:8–12` (header), `:1601–1605` (§25 governing rule), `:238–247`
(§0.5, Stage 0 *is* D-INST), `:1555–1564` (§22.2), `:1946` (§32,
`T-INSTRUMENT-UNBOUNDED-ON-E2A`); instrument `scripts/e2a_instrument_diagnostic.py:40–41,
118–124, 150–186, 258–266`.

**The protocol's rule (line 1601), stated in block capitals and repeated in the header:**

> *"NO WALL-CLOCK CAP, MEMORY CAP, WORKER-COUNT CHOICE, HOST-LOAD CONDITION, CPU MODEL OR
> COMPUTE BUDGET MAY DECIDE A SCIENTIFIC LABEL OR A SCIENTIFIC TERMINAL ANYWHERE IN THIS
> PROTOCOL, AT ANY LEVEL, INCLUDING META-LEVEL TERMINALS."*

**The instrument, at HEAD** (`sha256 9826cefe…`, the hash the D-INST freeze addendum declares
binding):

```
scripts/e2a_instrument_diagnostic.py:40   ESCALATION_SECONDS  = 1500          # WALL CLOCK
scripts/e2a_instrument_diagnostic.py:41   ADDRESS_SPACE_BYTES = 6 * 1024**3   # MEMORY CAP
:124   p = subprocess.run(..., timeout=ESCALATION_SECONDS, ...)
:126       except subprocess.TimeoutExpired:
:127           return UNRESOLVED, "WALL_BUDGET_EXHAUSTED", float(ESCALATION_SECONDS)
:106       except MemoryError:  print(... "UNRESOLVED","why":"MEMORY_SIMPLIFY" ...)
```

Those `UNRESOLVED` verdicts flow directly into `recompute_stage(..., assume_unresolved_correct)`
(`:150`), which produces the LOWER/UPPER pair, which produces
`ALL_AFFECTED_WORLDS_DETERMINATE` (`:238`), which is the protocol's Stage 0 gate
`INDETERMINATE_WORLDS_E2A == 0` (§0.4 line 173). Its FAIL branch is §22.2's
`D-INST-INDETERMINATE` → **`T-INSTRUMENT-UNBOUNDED-ON-E2A`**, which §32 line 1946 defines as:

> *"The frozen G2 contract is **not decidable at finite cost** on the sealed E2a corpus. **A
> finding about the contract** and that corpus."*

So: a 1500-second wall clock and a 6 GiB `RLIMIT_AS` publish a finding about the decidability
of the G2 contract, and forbid Stage 1. This is `D6` verbatim — the defect the ledger records
as *"FIXED — and fixed more strictly than the critic proposed"* — reproduced one level up, in
the stage the repair explicitly claimed to cover (§25.1 condition 6: *"applies **identically**
to every surface any comparison touches — including Stage 0"*).

**The failure is not hypothetical; it is measured.** `DINST_HOSTILE_REVIEW.md:36–39` records a
sampled stage-A expression from this exact escalation set at **44,375,516 kB = 44.4 GB RSS
after 95 s**, still running when killed. The bound is 6 GiB. That expression cannot resolve.
`POISON_WORLD_DETERMINATION.json` records a second at 33.4–47.7 GB. §10.6 of the protocol
itself cites both. The protocol's own §35 assigns `T-INSTRUMENT-UNBOUNDED-ON-E2A` or
`RUN_INCOMPLETE_RESOURCE_EXHAUSTION` a combined ~5% — against measured evidence that says the
memory bound will be hit.

**§25.4 does not save it.** §25.4's `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` escape (a) is
**not implemented anywhere in the instrument** — there is no such branch in
`e2a_instrument_diagnostic.py`; (b) is **not referenced in §22.2**, which maps
`D-INST-INDETERMINATE` to the scientific terminal with no resource carve-out; and (c) has no
stated precedence over §22.2. Three sections, three answers, no tie-break.

**Worse: the instrument emits terminals that are not in the protocol's terminal set.**
`:264–266`:

```python
"TERMINAL": ("D-INST-NO-WORLD-MOVED" if moved_lo == 0 else
             f"D-INST-{moved_lo}-WORLDS-RECLASSIFIED"),
```

Neither name appears in §22.2's declared Stage 0 set
`{D-INST-DETERMINATE, D-INST-INDETERMINATE, D-INST-PLURALITY-NOT-INVARIANT}`. And the
instrument's terminal is a function of `moved_lo` (worlds that moved at the LOWER resolution),
**not** of determinacy: the discarded null run at `DINST_RESULT.json` emitted the
reassuring-sounding `TERMINAL: "D-INST-NO-WORLD-MOVED"` while carrying
`"ALL_AFFECTED_WORLDS_DETERMINATE": false` and 396/396 `UNRESOLVED`. A total environment
failure produced a complete, well-formed, benign-looking terminal state. That is the
"unresolved case silently becomes a classification" path, at the terminal level, demonstrated
on real output.

**Minimal repair.** (1) Implement `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` inside the instrument
and make it dominate: if any `UNRESOLVED` record carries reason ∈
{`WALL_BUDGET_EXHAUSTED`, `MEMORY_*`, `KERNEL_OOM_KILL`, `SUBPROCESS_DIED_*`} **and** that
record is decisive, no terminal may be emitted. (2) Rewrite §22.2 to enumerate the
instrument's actual terminal strings and to route every resource-caused indeterminacy to the
operational state. (3) Either raise the Stage 0 caps to Tier-2-uncapped as §25.2 requires, or
delete the claim that Stage 0 inherits §25 — it does not.

---

## DEF-C3 — CRITICAL. Stage 0 is executing now, before the freeze it gates; its instrument has been modified three times after observing its own output; and E2a is simultaneously the engineering DEV set and the Stage 0 gating corpus.

**Location:** protocol `:26–27` (status assertion), `:1729–1737` (§26(1)), `:1015–1024`
(§13 A4), `:1888–1900` (§31 items 1–2), `:1714–1724` (§25.5).

**The protocol asserts, on its first page (line 26):**

> *"Status at this commit: PROTOCOL TEXT. NOT YET FROZEN. D3 item 7 is UNMET. No world
> generated. No module written. **No search executed.** No re-entry licensed."*

**The state of the repository contradicts the operative half of that claim.** Stage 0 is
running:

```
audit/muru_v2_reentry_20260819/_ckpt_dinst/                 13 live records at the start of this review
audit/muru_v2_reentry_20260819/_ckpt_dinst_ARCHIVED_8GB_BOUND/    22 records
audit/muru_v2_reentry_20260819/_ckpt_dinst_ARCHIVED_ENVFAIL/     396 records
git log:  3eb2bd7 13:25  "Stage 0 partial checkpoints (22/396)"
          592d199       "D-INST v3: preflight + typed subprocess deaths; null run discarded"
```

**The count rose from 13 to 45 live records during the ~40 minutes this review took, and a new
commit to the gating instrument's lineage landed in the same window.** Stage 0 is not merely
"already started"; it is running now, against an unfrozen protocol, with the instrument still
being changed.

Stage 0 is not decorative: §0.4 makes it a **hard gate** on Stage 1, and its FAIL branch is a
published scientific terminal (`DEF-C2`). §31 item 1 requires the freeze commit to be a
**strict ancestor of the first data commit**. Stage 0 data commits already exist; the freeze
commit does not, and the tag `muru-freeze/e7-protocol-v2` is absent from `git tag`. The
protocol can still be amended with Stage 0's partial results in hand. That is the ordering
§31 exists to prevent.

**The gating instrument has been repaired three times, twice after its own output was seen.**
From `DINST_FREEZE_ADDENDUM.md` and `git log --all`:

| commit | time | change | seen before the change? |
|---|---|---|---|
| `7e99830` | 01:04 | freeze v1, `14a50d51…` | — |
| `4e36f93` | 01:25 | repairs D1,D2,D3,D4,D6,D9,D10 after `DINST_REVIEW = FAIL` | review of the tool, not results |
| `479656b` | 02:45 | `ADDRESS_SPACE_BYTES` **8 GiB → 6 GiB** | **22 checkpoints already existed** |
| `592d199` | during this review | v3 (`9826cefe…`): D11 typed failure reasons, D12 preflight | **after a 396-record run was observed and discarded** |

Each is argued to be "engineering, not scientific". The 8→6 GiB change is not: it is the value
that decides, per `DEF-C2`, whether the scientific terminal fires, and it was tightened while
records produced under the looser bound were on disk. The addendum's own defence —
*"a stricter address-space limit can convert a verdict that would have been CORRECT or
INCORRECT into UNRESOLVED … so the tightening is conservative"* — concedes that the change
moves verdicts, and "conservative" is not "results-blind".

**And the corpus is doubly used.** §26(1) declares `DEV_ENGINEERING = the sealed E2a corpus`,
against which *"the bounded evaluator, escalation protocol, schema validator, bootstrap
harness, memory governor, the §25.5 resource parameters and runtime profiling are developed
and debugged"*. §0.4's gate is `INDETERMINATE_WORLDS_E2A == 0` — **on that same corpus**. The
instrument is tuned on the corpus it is then gated on, with unlimited iterations permitted
("developed and debugged"), and the tuning history above shows the iterations happening. There
is no stopping rule and no ledger for them. **Stage 0's gate is tunable and is being tuned.**

**Minimal repair.** Stop Stage 0. Archive everything produced so far as `EXPLANATORY_ONLY,
PRE-FREEZE, INADMISSIBLE`. Freeze the protocol text, the instrument hash, `ADDRESS_SPACE_BYTES`,
`ESCALATION_SECONDS`, `RSS_CEILING_GIB`, `WORKER_COUNT`, and the classify-cache hash **in one
commit**, tag it, and re-execute Stage 0 from zero under that tag. Separate the engineering DEV
corpus from the Stage 0 gating corpus, or drop the Stage 0 gate entirely (§0.5 already concedes
it is *"weak evidence"* for Stage 1 in the PASS direction and *"says nothing at all"* in the
FAIL direction — a gate with that operating characteristic is not worth the leakage it costs).

---

## DEF-H1 — HIGH. §19 says no diagnostic may change a verdict; §21.5 makes a diagnostic a necessary condition of every licence.

**Location:** `:1180` (§19 header) and `:1194` (D8) versus `:1487–1497` (§21.5 rider 1) and
`:1547` (§32, F10 gloss).

§19 line 1180: *"**None may change any verdict.** They exist to explain a failure, not to
rescue one."* D8 is a §19 diagnostic: `false_structure_rate` on the NEG stratum against
*"E6's frozen `Wilson upper <= 0.15`"*.

§21.5 rider 1 line 1497: *"An arm that recovers cases and breaches `Wilson upper <= 0.15` on
that stratum **is not licensed**."* §32's gloss for F10 line 1547 makes it constitutive:
*"Certified route `B`, **E6 ceiling met on the NEG stratum**, all eight D3 items satisfied."*

So the E6 ceiling is (i) a §19 diagnostic that may change no verdict, (ii) a §21.5 necessary
condition of every licence, and (iii) part of §32's definition of when F10 fires — while
(iv) §22 `F10`'s actual firing condition is only *"`QUALIFIED` and Gate R row 1"*, with no E6
clause at all. Four sections, three different answers, and §22 is declared *"the **sole**
terminal-assigning authority"*.

This is structurally identical to `D13(1)` — v1's concealed necessary condition — which the
ledger records as FIXED on the grounds that *"under Decision 1 the §21.4 annotation is **not**
a necessary condition of any licence"*. True of the annotation; false of the E6 ceiling, which
was **newly promoted** to a necessary condition by §21.5 in the same edit.

**Failure scenario.** Route `B` certifies. `false_structure_rate` on the NEG stratum yields
Wilson upper `0.17`. §22 F10 fires (`E4A_LICENCE_PROPOSED_AT_<arm>` — a positive terminal, on
the record). §21.5 says nothing is licensed. §19 says the number that blocked it may not change
a verdict. There is no terminal for "certified but E6-blocked", and no rule says which text
wins.

**Minimal repair.** Move the E6 ceiling out of §19 into §20's `QUALIFIED` conjunction or into
§21.2 as an explicit Gate R row, give it its own §22 rule and its own terminal
(`E6_SAFETY_CEILING_BREACHED_NO_LICENCE`), and remove it from §19's non-licensing list.

---

## DEF-H2 — HIGH. `E4A_LICENCE_PROPOSED_AT_<arm>` is parameterised by an arm whose only source is a diagnostic declared non-licensing.

**Location:** `:1542` (§22 F10), `:1546–1548` (§32), `:1471–1476` (§21.5), `:1190` (§19 D7),
`:1755–1762` (§26(3)).

§22 F10's terminal is `E4A_LICENCE_PROPOSED_AT_<arm>`, and §21.5 requires the owner's
ratification record to name *"the arm, the parameter setting, and the scope"*. The protocol
therefore must produce an arm.

The only arm-selection machinery in the document is §26(3): *"`R*` and `V*` are **selected on
DEV_ARM** by the frozen `befca0d` §3.1/§3.6 decision rule … and **measured on EVAL_ARM**."*
That machinery is §19 diagnostic **D7**, which line 1190 labels *"**Non-licensing** (decision
record §5)"*, under a §19 header that says no diagnostic may change any verdict.

So `<arm>` is either (a) undefined — the terminal has a free variable with no admissible
binding — or (b) bound by D7, in which case a non-licensing diagnostic determines the content
of the protocol's primary licensing terminal. Both readings are defects; (b) is the one the
document's structure implies.

This also interacts with `DEF-H1`: §21.5 rider 1's E6 ceiling is evaluated *"for every arm"*
(D8), so the E6 gate and the arm it gates both come from the non-licensing stratum.

**Minimal repair.** Either (i) rename F10 to `E4A_ENTRY_LICENCE_PROPOSED` with no `<arm>`
parameter and state explicitly that E7 licenses *entering* E4a, not adopting any arm, and
strike "the arm, the parameter setting" from §21.5 item content for row 1; or (ii) promote
§26(3)'s selection rule out of §19 into §21 with its own multiplicity control, and accept the
alpha cost.

---

## DEF-H3 — HIGH. §22 is neither exclusive nor exhaustive. `S8` is not fixed.

**Location:** §22.1 `:1524–1546`, §22.2 `:1558–1563`, §5.4 `:665–673`, §20 `:1240–1263`.

Four independent violations of the property §22 claims for itself (*"Every rule below emits
**exactly one** terminal, and the set is exhaustive"*, line 1521; and §32.2 line 2029, *"no
event maps to two terminals"*):

1. **A `C-0` failure maps to two terminals.** §22 `F1`: *"`C-0` fails and Route R-A is refused
   or also fails"* → `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT`. §5.4's ladder line 671
   lists *"**C-0 mismatch**"* among the mechanical reasons routing to
   `BENCHMARK_INTEGRITY_DEFECT`, and §22 `F2` covers *"`Q1` … fails for a mechanical reason"*
   with `C-0` inside `Q1`'s own clause list (§18 line 1158). One event, two named terminals,
   and they say opposite things about whether the benchmark is defective — the exact
   conflation `D8` was raised about.
2. **F10/F11/F12 overlap F13.** `F13` fires when *"the §21.5 owner ratification is refused or
   not produced"*. §21.5 places that ratification **after** the adjudicated verdict. So on any
   certified route where the owner declines, both the positive terminal (F10/F11/F12, which
   fires on the verdict) and `D3_ITEMS_UNMET_NO_REENTRY` are satisfied. No temporal
   disambiguation rule exists; `F13`'s first clause is time-qualified ("at verdict time") and
   its second is not.
3. **`P7` has no terminal.** §20 lists `P7 NO_MASS_POWER` as a precondition that must be YES.
   §22 covers `Q1`/`P9` (F2), `P1`/`P2` (F3), `P4` (F4), `C-1…C-6a`+`P3`/`P5`/`P8` (F5),
   `P6'` (F6), `P10` (F7). **`P7` and `C-0` appear in no §22 rule's clause list.** If `P7`
   fails, `QUALIFIED` is false and no terminal is assigned. Exhaustiveness fails.
4. **§22.2's Stage 0 set does not match the instrument** (see `DEF-C2`): the executable emits
   `D-INST-NO-WORLD-MOVED` / `D-INST-{n}-WORLDS-RECLASSIFIED`, neither of which §22.2 knows.

**Minimal repair.** Add `C-0` to `F5`'s clause list and delete "C-0 mismatch" from §5.4's
`BENCHMARK_INTEGRITY_DEFECT` ladder; add an explicit precedence line "F13 is evaluated only
after the §21.5 window closes, and supersedes F10–F12"; add a rule for `P7`; rewrite §22.2
against the instrument's actual output strings.

---

## DEF-H4 — HIGH. Three of `ROUTING_CERTIFIED`'s clauses are provably vacuous, and §21.1 explicitly asserts the opposite. The `g_max` defect (`D5`) is reintroduced.

**Location:** `:1284–1291` (§21.1) versus `:206–212` (§0.4) and `:1250–1252` (§20 `P6'`).

§21.1's predicate:

```
ROUTING_CERTIFIED := argmax over {pi_A, pi_B, pi_C+D} is IDENTICAL under rho_bot and rho_top
                     AND (pi_top - pi_second) >= delta       under BOTH resolutions
                     AND LCB_97.5(pi_top - pi_second) > 0    under BOTH resolutions
```

`P6'` makes `INDETERMINATE_WORLDS == 0` a hard precondition of `QUALIFIED`, and §20's own
definition says *"A world is INDETERMINATE iff its class differs between `rho_bot` and
`rho_top`"*. Zero indeterminate worlds therefore implies `pi_hat(rho_bot) ≡ pi_hat(rho_top)`
**exactly**, elementwise. §0.4 line 210 says so in terms:

> *"`rho_bot` and `rho_top` **coincide** on any surface that reaches the routing step. Every
> "under both resolutions" clause below is therefore **satisfied automatically** whenever the
> run is admissible at all."*

§21.1 line 1293 then says the opposite about the same clause:

> *"the argmax-invariance clause is **a genuine check that fails loudly rather than a
> formality that cannot fail**."*

It cannot fail. It is unreachable-false, given a clause upstream of it in the same conjunction.
This is `g_max = 0.010` again: a clause inside a decision predicate that is provably subsumed
by another clause, retained and described as operative. The ledger records `D5`/`S4` as FIXED
*"by deletion, with the equivalence stated as the identity it is"* — the identity is stated in
§0.4 and then contradicted in §21.1, and the three subsumed clauses are not deleted.

Severity is HIGH rather than MED because §21.1 is the certification predicate: a reader,
an adjudicator, or a future amendment will take the protocol's word that argmax invariance is
a live check, and the protocol's word is false.

**Minimal repair.** Delete the three vacuous qualifications from §21.1 and replace the
sentence at line 1293 with §0.4's correct statement; or drop `P6'` from `QUALIFIED` and let
the routing predicate carry the determinacy check, in which case the clauses become live and
`VOID_INSTRUMENT_INDETERMINATE` becomes `ROUTING_INDETERMINATE`. Not both.

---

## DEF-H5 — HIGH. Decision 2's pillar is weaker than claimed: E4f's family-ii Gate H1 is a zero-defect census in the direction the arm necessarily pushes, so route `C+D`'s downstream arm family is near-certainly dead on arrival.

**Location:** protocol `:1318` (§21.2 row 3, *"Executable? **YES — this is Decision 2**"*);
`MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md:506–526` (Lemma K), `:540–566` (§8.4), `:608–612`
(Gate H1).

E4f's own **Lemma K** proves that for any coarsening `V` of the control relation `V0`,
`max_class_size(V) >= max_class_size(V0)` **pointwise and deterministically**. Since
`stability_gate_passed` is `selection_fraction >= 20/30` and `selection_count =
winning.size`, Lemma K entails **`gate_passed_V(w) >= gate_passed_V0(w)` pointwise**: a
coarsening can only make the stability gate pass more often, never less.

Gate H1 is:

```
b_V = #{ w in EVAL_ARM : FS_V(w) = 1 and FS_V0(w) = 0 }      PASS iff b_V = 0
FS_V(w) = 1 iff stability_gate_passed(V,w) AND NOT g2_correct(representative(V,w))
```

This is a **one-directional census**: worlds where `V` improves on `V0` (`FS_V=0`, `FS_V0=1`)
do not offset. By Lemma K, every world that newly passes the gate under `V` is a candidate for
`FS_V = 1`, and `b_V = 0` therefore requires that **every single newly-stabilised world in the
828-world EVAL half have a G2-correct representative**, plus that no already-stable world
acquire a wrong representative. E4f's §8.4 defence — *"not monotone in coarseness: merging can
create a spurious stable-but-wrong verdict (raising it) **or let a correct class win**
(lowering it)"* — is a statement about the *rate*, and Gate H1 does not gate the rate.

The base rates make the requirement fanciful: the sealed comparator has `SUCCESS = 4/144
= 2.8%`; §32.1's own witnesses put `pi_E` at `5/138 = 3.6%`; §7 records that 10 of the 12
conditions carry E3-MARGINAL truth families with `search_side_attribution_licensed: false`.
Requiring 100% correctness among newly stabilised worlds, in a regime where correctness runs
at a few percent, is a bar that no non-trivial voting arm passes.

Route `C+D` is §35's most probable positive terminal (~18%, the largest positive) and Decision 2
is one of the two pillars of the reachability repair. "Executable" is being asked to carry
"capable of a positive outcome", and it does not. This is not a proof of unreachability — I
cannot exhibit the surface — but it is the same *shape* of defect as v1's, moved one level
downstream and not analysed anywhere in either document.

**Minimal repair.** Either (i) restate Gate H1 as a paired non-inferiority test on the
`false_stabilisation_rate` difference with an exact one-sided bound (accepting that the margin
is then not 0), or (ii) restrict the census to worlds that were already gate-passing under
`V0`, so that Lemma K's forced direction is excluded, or (iii) state in §21.2 row 3 that the
E4f voting family is expected to fail H1 and that Decision 2's executability claim rests on
family i, not family ii.

---

## DEF-H6 — HIGH. FP-6 substitutes a truth-dependent statistic that shares its correcting term with the efficacy endpoint for a truth-blind aggressiveness metric. The safety gate is not independent of the efficacy claim.

**Location:** `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md:528–566`, `:906`, `:932`, `:938`;
imported into this protocol by `:1318` (§21.2 row 3) and `:1500` (§21.5 rider 1).

**What is right about FP-6.** Lemma K is correct, and its corollary — that no margin-0
control-relative gate on `Δk` exists — is correct. Refusing to invent an absolute ceiling is
the right instinct. E4f discloses the substitution as its largest deviation and names the
honest fallback (`E4F_NOT_ENTERED_NO_ROUTE`). That is good practice and I credit it.

**What is wrong, and is not disclosed.** Frozen `k_inflation` is **truth-blind**: it measures
how aggressively an arm merges, and says nothing about whether the merged answer is right. The
substitute is

```
FS_V(w) = stability_gate_passed(V,w) AND NOT g2_correct(representative(V,w))
```

which is **truth-facing** and contains, as a factor, the negation of the very quantity
Gate H2 measures (`P(G2 success | V)`). The safety statistic and the efficacy statistic are
built from the same term. The consequence is that the "safety" evidence is not independent
evidence: on the sub-population where the arm succeeds, `FS_V` is driven to 0 by that success,
and the safety gate is discharged by the efficacy result rather than by an independent check
of the harm `k_inflation` was written to detect (*"multi-retention silently weakening the
stability gate"* — a statement about merging, not about correctness).

E4f's §8.4 justifies the substitution by reading the harm as *"a stable-looking verdict that
is not one discovery"* and then operationalising "not one discovery" as "the representative is
not G2-correct". Those are different predicates. A wrong-but-single discovery and a
right-but-merged discovery are exactly the two cases the substitution swaps.

Combined with `DEF-H5` (the substituted gate is also near-unpassable) the net effect is a
safety control that is simultaneously too strict to pass and, where it does pass, uninformative
about the hazard it replaced.

**Verdict on the disclosed open item.** Not an acceptable disclosed limitation as written.
It is repairable: report `false_stabilisation_rate` as a secondary, and gate family ii on a
**truth-blind** merging statistic that is non-zero for the control — e.g. the *rate of
gate-state flips induced by `V`*, `P(gate_passed_V ∧ ¬gate_passed_V0)`, with a declared
non-inferiority margin, or the median class-count change with a paired interval. Failing that,
E4f's own `E4F_NOT_ENTERED_NO_ROUTE` fallback should be taken and §21.2 row 3 relabelled.

---

## DEF-H7 — HIGH. The E6 ≥100-opportunity claim counts worlds, not evaluable opportunities, and the registry declares one third of the NEG stratum non-evaluable by design.

**Location:** `:1494–1497` (§21.5 rider 1), `:2087` (§33 DERIVED table),
`src/muru/paper_benchmark/registry.py:159–163`.

§21.5 rider 1: *"The opportunities come from this protocol's own NEG stratum: **276 worlds**
(F07 mass-only truth, F19A/B/C null worlds), which clears the frozen `>= 100` bar **by a
factor of 2.76** without executing E6 at all."*

The frozen bar (`befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3, quoted at line 1493) is
*"**100 evaluable** safety opportunities"*. Worlds are not opportunities:

- `registry.py:161` declares F19C's expected behaviour verbatim as *"trajectory destruction
  must be flagged **non-evaluable**"*. F19 cycles `(F19A, F19B, F19C)` over 138 replicates, so
  **46 of the 276 NEG worlds are non-evaluable by the registry's own declaration**. The factor
  is at most 2.30, not 2.76 — and the protocol cites the same registry line elsewhere, so this
  is a read it had already performed.
- Beyond F19C, a *safety opportunity* requires the arm to accept a structure that can be judged
  false. Worlds where no candidate survives the 20/30 stability gate, or where the seed set
  yields `COMPLETED_NO_CANDIDATE`, supply no opportunity. On null worlds this is not a small
  residual. The protocol nowhere estimates it.

If evaluable opportunities land below 100, the frozen E6 ceiling cannot be evaluated, and
§21.5 rider 1 — a necessary condition of **every** licence (`DEF-H1`) — has no defined value.
No terminal covers that state.

**Minimal repair.** Define "evaluable safety opportunity" operationally in §21.5, exclude F19C
from the count, publish the projected count in §35, and add a §22 rule for
"fewer than 100 evaluable opportunities" with its own terminal. If the projection is thin,
raise the NEG replicate count — it is cheap relative to the G2 stratum.

---

## DEF-H8 — HIGH. §36 and control `C-6a` are in direct conflict; enacting §36 can void the very terminal it enables.

**Location:** `:1166` (§18, `C-6a`), `:1325–1331` (§21.2 row 3 rider), `:1481–1484`
(§21.5 item 3), `:2172–2232` (§36).

`C-6a` requires, *"checked **before** Gate R is read"*, that
`MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` **still hashes to `0ce2755d…3a7f61`** and that
`E4F_FREEZE.txt`'s tuning ledger is **still empty**. Failure ⇒ `VOID_CONTROL_FAILURE`, no
route emitted (§21.2 rider, line 1329).

§36 requires that the population restatement *"**must be entered in E4f's freeze record** as a
population-by-reference restatement, not as a silent edit"* (line 2227), countersigned by the
owner **before** E4f may execute (§21.5 item 3).

If the restatement is written into `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md`, its sha256
moves off `0ce2755d…` and `C-6a` fails ⇒ `VOID_CONTROL_FAILURE`. If it is written into
`E4F_FREEZE.txt`, the "tuning ledger still empty" clause becomes contestable — the file's only
mutable region *is* the ledger. If it is written into a third document, §36's own words are not
satisfied. The protocol nowhere says which, and the ordering (countersignature before route vs.
`C-6a` before Gate R) is unspecified.

I confirmed the artifact currently hashes to
`0ce2755d9661d707a48961d11477fd6b793f8567c0e835e058a180d2763a7f61`, so `C-6a` passes **today**;
the conflict arises the moment §36 is enacted, which §21.5 item 3 requires for row 3.

**Minimal repair.** State in §36 that the restatement is recorded in a **new, separately hashed
countersignature file** (`E4F_POPULATION_RESTATEMENT.md`), that neither the E4f artifact nor
`E4F_FREEZE.txt` is edited, and amend `C-6a` to also verify that new file's hash and its
pre-route ancestry.

---

## DEF-H9 — HIGH. §25.4's "resume on a larger host" escape is inoperative for memory exhaustion, so `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` is an absorbing state.

**Location:** `:1698–1706` (§25.4 items 3–4), `:1714–1719` (§25.5), `:2110` (§34 FP-3).

§25.4 item 3: *"The run may be **resumed on a larger host** under the **identical frozen
protocol hash**, with the tuning ledger still empty and the published expression set
unchanged."*

But `RSS_CEILING_GIB = 24` is (a) **per-worker**, (b) **enforced in-process** (§25.5), and
(c) a **frozen declared parameter** (FP-3, frozen before Stage 0 per §13 A4). A larger host
does not raise an in-process per-worker ceiling. An expression that exceeds 24 GiB exceeds it
on a 48 GiB host and on a 1 TiB host identically. The only way to resolve it is to raise
`RSS_CEILING_GIB` — which §31 item 2 makes a tuning-ledger entry, which fires §22 `F7`
`VOID_SINGLE_SHOT_BROKEN`.

So §25.4's ladder is: item 3 (resume) is a no-op for the memory case; item 4 (terminate with
no scientific conclusion) is the only exit. Given `DEF-C2`'s measured 44.4 GB expression and
the four-times-OOM-killed poison world — both cited by the protocol's own §10.6 — the memory
case is the expected case, not the tail. §35 assigns the whole escalation tail ~5%.

**Minimal repair.** Make `RSS_CEILING_GIB` a **function of the host** (e.g. `min(24, 0.4 ×
host_total)` — a registered rule, per §31 item 3's own discipline) rather than a frozen scalar,
so that "resume on a larger host" is operative; and state explicitly that a host-envelope
change under a registered rule is not a tuning-ledger entry. Then publish a realistic
probability for `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` in §35.

---

## DEF-M1 — MED. `n = 1656` is presented as DERIVED from a criterion the protocol itself proves unattainable at every `n`.

**Location:** `:849–866` (§10.4), `:900–906` (§10.5 fact 2), `:2079` (§33 DERIVED table).

§10.4 line 849: *"v1's sizing criterion is preserved **verbatim** — *80% power to certify a
true lead of `delta` against the precision clause* — with only the critical value corrected."*
§10.5 fact 2 line 902: *"Power at a true lead of exactly `delta` is **0.499**, not 0.80. This
is … a mathematical property of **any** rule that refuses to certify a sub-material lead."*

Both are true, and together they mean the sizing criterion is unsatisfiable at every `n` under
the composite rule the protocol adopts. `n = 1656` is therefore not derived from an operative
property of the design; it is derived from the *precision clause in isolation*, a clause §10.5
fact 3 shows is not the binding one. §33 lists `n` under DERIVED with the derivation shown —
the derivation is arithmetically correct and targets a property the design does not have.

The practical consequence is modest (`n` affects only resolution, and FP-1's disposition
"Nowhere" is defensible), which is why this is MED and not HIGH. The honesty cost is not
modest: `n` is effectively a free parameter presented as derived, in a document whose header
imposes derive-or-cite on every number.

**Minimal repair.** Restate the sizing criterion as what it is — *"80% power under the
precision clause alone, at a lead of `delta`"* — and add `n` to §34's free-parameter list with
its "affects only resolution" disposition, or re-derive `n` from a criterion stated on the
composite rule (e.g. 80% power at 1.30 `delta`, which `n = 1656` does attain).

---

## DEF-M2 — MED. The certification predicate does not establish that the certified lead is material; it establishes `lead > 0` plus an observed-effect-size filter.

**Location:** `:833–843` (§10.3), `:1284–1291` (§21.1), `:1298` (§21.1 rationale),
`:906–910` (§10.5 fact 3).

`ROUTING_CERTIFIED` applies `>= delta` to the **plug-in observed** lead and `> 0` to the
**lower confidence bound**. It never tests `H0: L < delta`. The construct the terminal names —
*"does its lead over the runner-up exceed the programme's own definition of a material
attribution difference?"* (§1, line 274) — is a statement about the **true** lead. At a true
lead of `0.9 delta` the rule certifies with substantial probability (§10.5's own OC curve is
0.499 at `1.00 delta` and rises steeply; the sub-material region is not tabulated). So a
certified route licenses an E4 arm on a claim of materiality that the statistic does not
support.

The protocol is aware of the adjacent issue (fact 3: the precision clause alone would certify
down to `0.693 delta`) and adds the materiality clause to fix it, but the fix is an observed-
value filter, not an inferential one.

**Minimal repair.** Either replace the two clauses with `LCB_97.5(pi_top - pi_second) >=
delta` — a genuine test of materiality, at a real power cost that should then be tabulated —
or restate §1's scientific question and §32's F10/F11/F12 glosses to claim only what is
established: *a positive lead at 97.5% confidence whose point estimate is at least `delta`*.

---

## DEF-M3 — MED. `S21` is only half fixed: the classify cache is hashed, but the classifier **version** that defines Stage 0's population is chosen at runtime by frequency, from a mutable out-of-repo file.

**Location:** `:1926–1932` (§31.8), `scripts/e2a_instrument_diagnostic.py:57–64`.

```python
vers = collections.Counter(v for (v,) in con.execute("select version from classify_cache"))
top  = vers.most_common(1)[0][0]
out  = {e for e, rj in con.execute("... where version=?", (top,)) if ... == "SIMPLIFY_TIMEOUT"}
```

§31.8 promises the cache is *"hashed into the freeze manifest, read with an explicit `WHERE
version = ?` filter, and re-verified at Stage 0 seal time"*. The filter exists; the **value**
is `argmax` over the counts in a ~89 MB sqlite file at `~/e2_x86_cache/`, outside git, freely
mutable, with no freeze manifest yet in existence. Writing enough rows under a new classifier
version silently changes which expressions Stage 0 escalates, i.e. its entire population.

**Minimal repair.** Pin the version string as a literal in the freeze manifest and have the
tool `assert` it, rather than selecting it.

---

## DEF-M4 — MED. §0.5's account of what D-INST does, and of Stage 0's "one respect" widening, does not match the instrument at HEAD.

**Location:** `:238–245` (§0.5).

§0.5: *"D-INST escalates the 314 timed-out rows inside the 73 affected stage-A worlds; Stage 0
escalates **all 397 distinct `SIMPLIFY_TIMEOUT` expressions** in the corpus."*

The instrument at HEAD builds its work list as *every* `(world, seed, front_rank)` row in the
whole corpus whose `expression_string` is in the timeout set (`:196–199`), with no stage
filter. `DINST_RESULT.json` records `pairs_total: 396`, and the live checkpoints carry
`"sealed_stage": "A"` **and** `"sealed_stage": "B"`. The widening §0.5 declares is already the
instrument's behaviour, the unit is `(world,seed,rank)` pairs and not distinct expressions, and
the count is 396, not 397 or 314. A protocol that identifies Stage 0 with a named frozen tool
must describe that tool correctly, because §22.2 inherits its terminals.

**Minimal repair.** Rewrite §0.5 against the tool as it stands and restate the unit.

---

## DEF-M5 — MED. `RSS_CEILING_GIB = 24` and `WORKER_COUNT = 8` are declared as "profiled on the E2a engineering DEV set" though no profiling record exists, and they disagree with the bound Stage 0 actually enforces.

**Location:** `:1714–1722` (§25.5), `:1019–1024` (§13 A4), `:2110–2113` (§34 FP-3/FP-4).

§25.5 says both numbers are *"profiled on the E2a engineering DEV set … and frozen in the
freeze manifest BEFORE Stage 0 executes"*. There is no profiling artifact in the directory, no
freeze manifest, and Stage 0 has already started (`DEF-C3`). The stated justification for 24 is
*"below the 25 GiB anon-rss at which the Gate 1 evaluator lost cases"* — i.e. derived from an
observed outcome, not from profiling. Meanwhile Stage 0 enforces 6 GiB of address space and 3–6
workers, so the two stages of one protocol run under bounds differing by 4×, with only the
Stage 1 pair declared in §34.

**Minimal repair.** Either perform and publish the profiling, or relabel both as declared free
parameters with the honest rationale, and add Stage 0's `ADDRESS_SPACE_BYTES` and worker count
to §34.

---

## DEF-M6 — MED. The protocol text is stale on its own outstanding item: it asserts twice that the `S16` blind re-derivation has not been performed. It was, at `b4ea2a0`.

**Location:** `:392` (§4.1 property i), `:1860` (§30 attack 1).

Both say *"§30 attack 1 must generate it independently before freeze"* / *"This is `S16`'s
outstanding item and **it has not yet been performed**."* `git log` shows `b4ea2a0`
(2026-08-19 02:51, six minutes after the protocol commit) — *"S16 closed: blind re-derivation
CONFIRMS the composition rule"* — and `S16_BLIND_COMPOSITION_DERIVATION.md` exists, with a
declared source list, a count-only screening procedure, disclosed incidental exposures, and a
rule (`endpoint_applies_to_variant("family_recovery", ·)`) that I verified selects exactly the
twelve declared families. **This is the one place where reality is better than the protocol
says**, and freezing the current text would freeze a false statement about the programme's own
compliance.

**Minimal repair.** Update both sites to cite `S16_BLIND_COMPOSITION_DERIVATION.md` @ `b4ea2a0`
and record `AL-3` as discharged rather than accepted.

---

## DEF-M7 — MED. Q1's citation for "the registry's twelve G2 conditions" points at eighteen families; the non-discretionary selection rule is stated only outside the protocol.

**Location:** `:1157` (§18 Q1), `:2058` (§33 REUSED table, *"`12` | registry G2 conditions … |
`registry.py:135-152`"*).

`registry.py:135–152` spans F01–F18, i.e. eighteen `_family(...)` literals including F06, F07
and F13–F16, which the protocol excludes. The citation does not pick out the twelve; the list
in §5.2 is an enumeration. The actual rule — `symbolic == "defined"`, equivalently
`endpoint_applies_to_variant("family_recovery", variant)`, which yields exactly 12 families and
the registry's own `endpoint_case_count("family_recovery") == 144` — appears only in
`S16_BLIND_COMPOSITION_DERIVATION.md` §8. A "REUSED VERBATIM, zero magnitudes, zero outcomes"
clause should carry the predicate, not a hand-transcribed list under a citation that does not
support it.

**Minimal repair.** State the predicate in Q1 and have `calibration_surface.py` compute
`CALIBRATION_G2_FAMILIES` from it rather than declaring a literal tuple.

---

## DEF-M8 — MED. The instrument's UPPER bound cannot produce stage `E`, so it is not an upper bound on `E`; §0.5's quoted interval does not match the tool's output.

**Location:** `:301` and `:352` (§0.5 / §3, *"`E ∈ [119,124]`"*, *"`C+D ∈ [99,104]`"*);
`scripts/e2a_instrument_diagnostic.py:150–162`.

```python
if sealed == "A":
    if not any_correct: return "A"
    return "C" if retained_correct else "B"
if sealed == "B":
    return "C" if retained_correct else "B"
return sealed
```

`recompute_stage` never returns `"E"`. A world whose retained row becomes correct is assigned
`C` unconditionally, though under the frozen taxonomy it lands in `E` (`SUCCESS`) whenever the
elected cross-seed representative is the correct one. So the UPPER counts under-report `E` by
construction, and `DINST_RESULT.json` accordingly shows `E = 119` in **both** bounds, against
the protocol's stated `E ∈ [119,124]` and `C+D ∈ [99,104]` (the tool gives `C = 102` at LOWER,
outside the quoted lower end of 99). The protocol quotes an interval no cited artifact produces.

This is conservative for the B-plurality claim, which is why it is MED. It is not conservative
for §35's Stage 0 prediction or for any statement about `E`.

**Minimal repair.** Either extend `recompute_stage` to evaluate the cross-seed representative
under both resolutions, or state in §0.5 that the `E` bound is not computed by the instrument
and cite whatever does compute it.

---

## DEF-M9 — MED. `C-6` is a mandatory, non-waivable control whose satisfiability depends on an unsecured resource, in a protocol with no retry and no rehabilitation.

**Location:** `:1164` (§18 C-6), `:1809–1817` (§28), `:1035–1039` (§13 disclosed caveat),
`:2166` (§35, *"`C-6` … the likeliest failure"*).

§28: *"**If no second architecture can be reached, `C-6` FAILS and the terminal is
`VOID_CONTROL_FAILURE`.**"* §22: *"There is **no rehabilitation path** from …
`VOID_CONTROL_FAILURE`."* §13 records `worlds_executed_on_this_host: 0` and no second
architecture is demonstrated to be available to this programme. §35 names `C-6` as one of the
two likeliest voids.

I agree with the *principle* (`D9`'s repair is right: an unverifiable parity claim is not a
control, and re-keying parity to the canonicalisation table makes it cheap). The defect is
procedural: a single-shot protocol makes a terminal-voiding control contingent on procuring
hardware, and does not require that procurement to be demonstrated **before** 62.7 CPU-hours
are spent.

**Minimal repair.** Add to §12's hard preflight gate: *"execute `C-6` on a 5-expression smoke
sample on the second architecture before world 1; failure ⇒ stop, do not generate."*

---

## DEF-M10 — MED. §31.8 names a superseding freeze record that does not exist, and the record that does exist is uncommitted.

**Location:** `:1918–1924` (§31.8).

§31.8 says `DINST_FREEZE_SHA256.txt` *"is **superseded by `DINST_FREEZE_SHA256_v2.txt`**"*. The
file in the directory is `DINST_FREEZE_SHA256_POSTREPAIR.txt` (contents verified: it records
`9826cefe…` for the tool and `5b2d2ae5…` for the D-INST protocol, both of which match the
files at HEAD). `DINST_FREEZE_ADDENDUM.md`, which carries the binding admissibility statement for every
Stage 0 record, was committed only at `592d199` — during this review — and is already dirty
again in the working tree. §31.8 also states that *"The
D-INST **protocol text** must also be re-frozen or formally amended against its own failed
review"*; that has not happened.

**Minimal repair.** Rename or re-point, commit the addendum, and discharge the D-INST protocol
re-freeze before Stage 0 output is used for anything.

---

## DEF-L1 — LOW. `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` is marked "Positive?" = Yes though it licenses nothing.

**Location:** `:1545` (§32 table).

The column's other "Yes" entries are licence proposals. This one is a scientific conclusion
("the retention rule is fine") that licenses no arm. The gloss says so, and I accept the
argument that the licensing table must be able to reach it — but the shared column conflates
"positive scientific conclusion" with "positive licensing outcome", and §35's *"~37% to some
positive terminal"* silently includes it. Excluding it, the licensing-positive mass is ~32%.

**Minimal repair.** Split the column into `Concludes?` and `Licenses?`.

---

# PART 2 — REACHABILITY AUDIT

Two verdicts per terminal: **as written** (Gate Q evaluated with the code it names) and
**after `DEF-C1`'s one-word repair** (`find_overlaps` → `unacknowledged_overlaps`). All
witness arithmetic below was recomputed independently and agrees with §32.1 to 6 decimals.

| # | Terminal | Witness / refutation | As written | After DEF-C1 repair |
|---|---|---|---|---|
| T0 | `T-INSTRUMENT-UNBOUNDED-ON-E2A` | Any decisive E2a expression unresolved after escalation. **Reached today by a 6 GiB / 1500 s cap on a measured 44.4 GB expression** — `DEF-C2`. Reachable, but only through a resource cap, which the protocol forbids from deciding a terminal | **REACHABLE, ILLEGITIMATELY** | unchanged |
| T1 | `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` | `C-0 < 380/380` and owner refuses R-A. `C-0` is 380/380 today, so requires a generator regression. Also collides with T2 (`DEF-H3`) | REACHABLE (ambiguous) | unchanged |
| T2 | `BENCHMARK_INTEGRITY_DEFECT` | **Fires unconditionally**: `find_overlaps(DECLARED_BANDS + (CALIBRATION_BAND,)) = [Overlap('objval_plan2','rc3_engineering_smoke', …)] ≠ []` for every dataset ⇒ Q1 FAILS ⇒ §22 F2 | **THE ONLY REACHABLE STAGE-1 TERMINAL** | reachable only on genuine drift |
| T3 | `SURFACE_INCOMPLETE_COMPOSITION` | Any cell ≠ 138 completed worlds, or any world ≠ 30 seeds | unreachable (T2 pre-empts) | REACHABLE |
| T4 | `VOID_SCHEMA_INCOMPLETE` | Any of the 28 §14 fields absent at seal | unreachable (T2 pre-empts) | REACHABLE |
| T5 | `VOID_CONTROL_FAILURE` | `C-6` with no second architecture (§35's own likeliest void); or `C-6a` after any E4f drift — including the drift §36 itself mandates (`DEF-H8`) | unreachable (T2 pre-empts) | REACHABLE |
| T6 | `VOID_INSTRUMENT_INDETERMINATE` | `INDETERMINATE_WORLDS > 0` after uncapped escalation. But `RSS_CEILING_GIB = 24` is a cap, so this terminal and `RUN_INCOMPLETE` are separated only by §25.4's precedence, which is unstated | unreachable (T2 pre-empts) | REACHABLE, boundary undefined |
| T7 | `VOID_SINGLE_SHOT_BROKEN` | >1 surface, or non-empty tuning ledger. **Note:** the only fix for a 24 GiB-exceeding expression is a ledger entry (`DEF-H9`), so this is the forced exit from the memory tail | unreachable (T2 pre-empts) | REACHABLE |
| T8 | `ROUTING_INDETERMINATE` | §32.2's `(40,45,48,5)`: lead `3/138 = 0.021739 < delta`; `pi_B = 0.32609 > delta`. **Verified.** Row 5 → F8 | unreachable (T2 pre-empts) | **REACHABLE** |
| T9 | `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` | **W-EX** `(55,8,50,25)`: `pi = (0.398551, 0.057971, 0.362319, 0.181159)`; argmax `A`, second `C+D`, lead `0.036232 < delta`; `LCB = −0.005744 < 0`; `pi_B = 0.057971 < delta = 0.069444`. **Verified.** Not certified **and** exonerated → row 4 → F9. Non-degenerate: no cell is empty, `pi_E = 0.181` | unreachable (T2 pre-empts) | **REACHABLE** |
| T10 | `E4A_LICENCE_PROPOSED_AT_<arm>` | **W-B** `(14,69,50,5)`: `pi = (0.101449, 0.5, 0.362319, 0.036232)`; lead `0.137681 = 1.983 delta`; `sigma = 0.0225668`; `LCB = +0.0934505 > 0`. **Verified.** Routing arithmetic sound. **But:** `<arm>` has no admissible source (`DEF-H2`); the E6 ceiling is a hidden necessary condition with a contested opportunity count (`DEF-H1`, `DEF-H7`); and the operative licence additionally requires the owner to re-arm `f4c1105`, whose GATE 1 is sealed FAIL — an amendment of frozen authority, disclosed at line 1321 | unreachable (T2 pre-empts) | **TERMINAL REACHABLE; LICENCE CONDITIONAL ON THREE UNRESOLVED ITEMS** |
| T11 | `E4_GENERATION_LICENCE_PROPOSED_F09_F10` | **W-A** `(69,30,34,5)`: `pi = (0.5, 0.217391, 0.246377, 0.036232)`; argmax `A`, second `C+D`; lead `0.253623 = 3.652 delta`; `sigma = 0.0202940`; `LCB = +0.2138472`. **Verified.** Licence restricted by E3 to F09, F10 — 2 of 12 conditions, disclosed. Note the §21.4 annotation reads `CONTRADICTS` here (`TV = 0.4112`, interval `[0.3575, 0.4686]`, recomputed and confirmed), so §21.5 additionally requires a written owner explanation | unreachable (T2 pre-empts) | **REACHABLE, THIN BY DESIGN** |
| T12 | `E4F_LICENCE_PROPOSED` | **W-CD** `(14,45,74,5)`: `pi = (0.101449, 0.326087, 0.536232, 0.036232)`; lead `0.210145 = 3.026 delta`; `sigma = 0.0222273`; `LCB = +0.1665798`. **Verified.** **But** the downstream arm family it licenses is near-certainly dead at E4f Gate H1 by E4f's own Lemma K (`DEF-H5`), the gating statistic is not independent of the efficacy endpoint (`DEF-H6`), and enacting §36 as written can void `C-6a` (`DEF-H8`) | unreachable (T2 pre-empts) | **TERMINAL REACHABLE; DOWNSTREAM SUBSTANTIALLY VACUOUS** |
| T13 | `D3_ITEMS_UNMET_NO_REENTRY` | Owner declines ratification. **Overlaps T10/T11/T12 with no precedence rule** (`DEF-H3`) | unreachable (T2 pre-empts) | REACHABLE, non-exclusive |
| T14 | `T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS` | Owner judgement. No data path | REACHABLE (owner act) | unchanged |
| — | `P7 NO_MASS_POWER` fails | **No terminal exists** (`DEF-H3` item 3) | **UNASSIGNED** | UNASSIGNED |
| — | `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` | By design not a §32 terminal. Absorbing for the memory case (`DEF-H9`); not implemented in the Stage 0 instrument | REACHABLE, no exit | unchanged |
| S0a | `D-INST-DETERMINATE` | Requires all 396 pairs to resolve under 6 GiB / 1500 s. The corpus contains an expression measured at 44.4 GB | **DOUBTFUL** | unchanged |
| S0b | `D-INST-INDETERMINATE` | Any decisive pair unresolved — including for a purely resource reason | REACHABLE, illegitimately | unchanged |
| S0c | `D-INST-PLURALITY-NOT-INVARIANT` | **REFUTED as reachable.** `DINST_RESULT.json`'s own `PLURALITY_note` and the sealed analytic result (`B_min = 196 > max(122, 104, 121)`) make the predicate cap-invariant. `plur(lower)` and `plur(upper)` are both forced `True`. The terminal cannot fire | **UNREACHABLE** | unchanged |
| S0d | `D-INST-NO-WORLD-MOVED` / `D-INST-{n}-WORLDS-RECLASSIFIED` | **Emitted by the instrument; absent from §22.2** | **UNDECLARED** | unchanged |

**Summary.** §32.1's witnesses are internally sound and mutually consistent — they are four
distinct integer vectors, each summing to 138 per condition, each satisfying `P1` and `P7` by
construction, each with a distinct argmax, and their certification arithmetic reproduces
exactly. What §32.1 does not establish, and what it claims at line 1976, is that they satisfy
**every** Gate Q clause. Against the code Gate Q names, none of them does. **The constructive
reachability proof fails at the conjunction, which is the same place v1's failed.**

---

# PART 3 — LEDGER SPOT-CHECK (14 claims verified against the v2 text and the code)

| Defect | Ledger disposition | Verified? | What I found |
|---|---|---|---|
| **D5** — `g_max` vacuous | FIXED "by deletion, with the equivalence stated as the identity it is" | **OVERSTATED** | `g_max` is genuinely deleted and the identity is correct in §0.4. But §21.1 retains **three** provably vacuous clauses (two "under BOTH resolutions", one argmax-invariance) and line 1293 asserts the invariance clause *"fails loudly rather than a formality that cannot fail"* — the exact property `D5` condemned. `DEF-H4` |
| **D6** — a resource cap decides a scientific finding | FIXED "**more strictly** than the critic proposed" | **NOT FIXED** | §25.4 is well drafted for Stage 1 and unimplemented anywhere. Stage 0 — which the protocol *is* (§0.5) — runs under `ESCALATION_SECONDS = 1500` and `ADDRESS_SPACE_BYTES = 6 GiB`, whose `UNRESOLVED` outputs decide `T-INSTRUMENT-UNBOUNDED-ON-E2A`, a §32 terminal glossed as "a finding about the contract". `DEF-C2` |
| **D7** — Stage 0 → Stage 1 resource-sizing leakage | FIXED "by the first of the critic's two options" (freeze sizing before Stage 0) | **NOT FIXED IN FACT** | The repair is conditional on a freeze that has not occurred, while Stage 0 is already executing (13 live checkpoints) and the instrument has been retuned twice after observing its own output. `DEF-C3`, `DEF-M5` |
| **D8** — fallback guarantees a false benchmark-defect claim | FIXED "by deleting the fallback" | **REGRESSED** | The fallback is deleted. But `DEF-C1` makes `BENCHMARK_INTEGRITY_DEFECT` fire unconditionally from a drafting error — a *false diagnosis of a benchmark defect caused by a protocol drafting error*, which is D8's stated harm, now guaranteed rather than merely possible |
| **D9** — expression→label table ill-defined; parity may never run | FIXED, both halves | **HOLDS** | §25.3's re-keying to `(canonicalization_status, effective_support, discovered_family)` is correct: all three are functions of the expression alone in `g2_contract` (confirmed against the payload in `e2a_instrument_diagnostic.py:83–98`). `C-6` is mandatory and non-waivable as claimed. Residual procedural risk noted at `DEF-M9` |
| **D11 / S15** — resolving-power table irreproducible | FIXED, "republished, recomputed, for both critical values" | **HOLDS — verified numerically** | `d = sqrt(K/(n+K))`, `K = (z + z_.80)^2`. z_.975: K = 7.848880 → n=252: 0.17380; n=576: 0.11594; n=1296: 0.077588; n=1656: 0.068683; n=1944: 0.063413. z_.95: K = 6.182554 → 0.15470 / 0.10312 / 0.068904 / 0.060988 / 0.056326. **Every published entry reproduces.** Genuine repair |
| **D13(3) / S14** — E6 circularity | FIXED, "the dependency is closed inside the protocol" | **PARTLY; NEW DEFECT INTRODUCED** | Using the frozen ceiling as text rather than executing E6 is a legitimate move. But the ≥100 bar is asserted from 276 *worlds* while `registry.py:161` declares F19C *"non-evaluable"* by design (46 worlds), and "evaluable opportunity" is never defined (`DEF-H7`); and the ceiling was promoted to a necessary condition of every licence while remaining a §19 non-licensing diagnostic (`DEF-H1`) |
| **S5** — `10/144` mislabelled REUSED | FIXED, "moved to DERIVED with the derivation shown" | **HOLDS** | §10.1 gives the derivation; §33's DERIVED table carries the entry; the REUSED table no longer does. The "conservative direction of generalisation" argument (two-way → four-way) is correct |
| **S8** — terminals not exclusive/exhaustive | FIXED, "every element of the critic's minimal fix is adopted" | **NOT FIXED** | Four residual violations: `C-0` failure → F1 **and** F2; F10/F11/F12 overlap F13; `P7` and `C-0` appear in no §22 rule; §22.2's Stage 0 set does not match the instrument's emitted strings. `DEF-H3` |
| **S12** — no freeze occurred; the one freeze record is stale | FIXED, "all four sub-items" | **PARTLY** | The protocol now correctly declares itself unfrozen — a real improvement. But §31.8 names `DINST_FREEZE_SHA256_v2.txt`, which does not exist (the file is `…_POSTREPAIR.txt`); `DINST_FREEZE_ADDENDUM.md` is untracked; the D-INST protocol re-freeze §31.8 requires has not happened; and Stage 0 is running pre-freeze. `DEF-M10`, `DEF-C3` |
| **S16** — population chosen with `pi_0` in view | ACCEPTED-LIMITATION `AL-3`, discharge deferred to §30 attack 1 | **BETTER THAN CLAIMED, BUT THE TEXT IS STALE** | `S16_BLIND_COMPOSITION_DERIVATION.md` @ `b4ea2a0` performs the blind re-derivation with a declared source list and a count-only screening procedure, and its rule (`endpoint_applies_to_variant("family_recovery", ·)`) selects **exactly** the twelve declared families — I confirmed independently that `registry.py` has exactly 12 families with `symbolic="defined"` and that they are F01–F05, F08–F12, F17, F18. The protocol still says at two places that this "has not yet been performed". `DEF-M6` |
| **S19** — `PARTITION_CASE_COUNTS` misread | FIXED (substance confirmed, mechanism corrected) | **HOLDS — verified by execution** | `registry.PARTITION_CASE_COUNTS == {'development': 4, 'held_out': 12, 'challenge': 3}`; `registry.PARTITIONS` is a 3-tuple; `rc5_seeds.A35_TOTAL_CASES == 380`. Route R-B touches none of it, and `registry.resolve_case_id("PBC|calibration|F17|r000")` raises `ValueError` as claimed. `pb_33` → `A3.1 INTEGRITY VERIFIED`, `pb_34` → `RC3 INTEGRITY VERIFIED`, both rc=0 on this host |
| **S21** — classify cache unhashed, mutable, in the gating path | FIXED, "both clauses the critic asked for" | **HALF FIXED** | Hashing and the `WHERE version = ?` filter are implemented. The version **value** is selected at runtime by `Counter.most_common(1)`, from a mutable out-of-repo sqlite file, and no freeze manifest exists. `DEF-M3` |
| **S22** — §3/§25 reproduce unsound D-INST figures | FIXED, both corrections | **HOLDS** | I confirmed `conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` at `e2_classify.py:338`, inside a `try` that also catches `BrokenPipeError, EOFError, OSError` — so the parent-side poll is the operative cap and does absorb pipe/worker failures under the same name, exactly as §3 item 3(a) now states. The B/C/E figures are labelled upper bounds throughout |

**Score: of 14 spot-checked claims — 6 hold, 4 are overstated or half-true, 3 are not fixed,
1 is understated in the protocol's favour.** The ledger's headline "37/38 FIXED" does not
survive contact with the code.

---

# PART 4 — WHAT WOULD CHANGE MY VERDICT

I would return PASS on a v3 that does all of the following. Nothing here requires a new
experiment, a new magnitude, or a relitigation of Decision 1 or Decision 2.

1. **Fix `DEF-C1` and prove the fix.** Point Q1 and §5.2 at `unacknowledged_overlaps` (or
   `assert_governance_clean`), then **write and run** the witness verifier §32.1 already
   promises: a script that evaluates every Gate Q clause, every `P*` precondition and the
   §21.1 predicate against all four witnesses and refuses to freeze on any failure. Commit its
   output. A reachability proof that has never been executed is a reachability assertion.
2. **Fix `DEF-C2`.** Implement `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` inside
   `e2a_instrument_diagnostic.py`; make any resource-caused `UNRESOLVED` on a decisive pair
   suppress terminal emission entirely; rewrite §22.2 against the instrument's actual terminal
   strings; and either uncap Stage 0's Tier 2 or delete the claim that §25 governs Stage 0.
3. **Fix `DEF-C3`.** Halt Stage 0, mark everything produced so far inadmissible, freeze the
   protocol text **and** every Stage 0/Stage 1 resource parameter **and** the classify-cache
   version and hash in one tagged commit, and re-run Stage 0 from zero under that tag. Separate
   the engineering DEV corpus from the Stage 0 gating corpus — or drop the Stage 0 gate, which
   §0.5 already concedes is weak in both directions.
4. **Resolve `DEF-H1` and `DEF-H2`.** Move the E6 ceiling into `QUALIFIED` or Gate R with its
   own §22 rule and terminal; and either strip `<arm>` from F10 or promote §26(3)'s selection
   rule out of the non-licensing stratum with its own multiplicity control. A protocol may not
   have necessary conditions living in a section headed "None may change any verdict."
5. **Repair `DEF-H3` and `DEF-H4`.** Make §22 actually exclusive and exhaustive (`C-0`, `P7`,
   F13 precedence, Stage 0 names), and delete the vacuous clauses from §21.1 along with the
   sentence claiming they can fail.
6. **Address `DEF-H5`/`DEF-H6` before Decision 2 is relied on.** Either re-specify E4f Gate H1
   so it is not a forced-direction zero-defect census, or replace `false_stabilisation_rate`
   with a truth-blind merging statistic, or relabel §21.2 row 3 to say that route `C+D`
   licenses entry to E4f family **i** and that family **ii** is expected to fail its own gate.
   Any of the three is honest; the current text is not.
7. **Define "evaluable safety opportunity" (`DEF-H7`)**, exclude F19C, publish the projected
   count, and add a terminal for falling below 100.
8. **Resolve the §36 / `C-6a` conflict (`DEF-H8`)** by naming a third, separately hashed
   countersignature artifact.
9. **Make `RUN_INCOMPLETE` non-absorbing (`DEF-H9`)** by expressing `RSS_CEILING_GIB` as a
   registered host-relative rule, and republish §35's probabilities against the measured
   44.4 GB evidence rather than against ~5%.
10. **Housekeeping that costs nothing:** restate the sizing criterion (`DEF-M1`); restate what
    certification establishes (`DEF-M2`); pin the cache version (`DEF-M3`); describe D-INST
    correctly (`DEF-M4`); justify or reclassify 24 GiB / 8 workers (`DEF-M5`); update the two
    stale `S16` sentences (`DEF-M6`); put the family-selection predicate in Q1 (`DEF-M7`); fix
    the `E` bound (`DEF-M8`); smoke-test `C-6` in preflight (`DEF-M9`); fix and commit the
    freeze records (`DEF-M10`); split §32's `Positive?` column (`DEF-L1`).

**What would *not* change my verdict.** Argument that `DEF-C1` is "obviously a typo". It may
well be — but it is the load-bearing clause of the gate that the reachability proof asserts
without checking, in the exact defect class that killed v1, in a document that survived a
self-declared eight-point hostile attack surface (§30) including *"attack the §32.1 witnesses —
verify each against **every** Gate Q clause"*. The defect's existence is evidence that §30
attack 3 was not performed. The repair is one word; the discipline it demonstrates is the
thing under review.

---

**REVIEWER'S NOTE ON SCOPE.** I took Gate 1 = FAIL, E2b's decision-inadmissibility, and the
cap-invariance of E2a's B-plurality as fixed and did not relitigate them. I did not review
`V2_REPAIR_LEDGER.md`, `CRITIC_SCIENCE_REENTRY.md`, `SYNTHESIS_DECISION_RECORD.md`,
`S16_BLIND_COMPOSITION_DERIVATION.md` or `GATE_1_DEFINITIVE.md` as targets; they were read as
context and, where the target makes a claim about them, that claim was checked. This review
performed no scientific compute: it executed only read-only imports, two integrity scripts
(`pb_33`, `pb_34`), and closed-form arithmetic on the protocol's own published numbers. No
file outside `audit/muru_v2_reentry_20260819/CRITIC_SCIENCE_V2_REVIEW.md` was created or
modified, and nothing was committed.
