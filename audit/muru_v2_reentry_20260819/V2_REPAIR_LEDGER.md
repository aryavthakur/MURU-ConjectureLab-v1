# V2 REPAIR LEDGER — every critic defect, mapped to its disposition

**Target document:** `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V2.md` (this directory).
**Superseded document:** `MURU_V2_CALIBRATION_REENTRY_PREREGISTRATION.md`, sha256
`38d1e997355f712f98eb205439dd3869e21f3a95112e05e8980d886bab758117`, retained as superseded.
**Sources of the defect list:** `CRITIC_SCIENCE_REENTRY.md` (D1–D13, verdict **FAIL**) and
`CRITIC_GOVERNANCE_REENTRY.md` (S1–S25, verdict **FAIL**).

**Nature of this document:** a governance record. It creates no scientific evidence and
alters none. Like the protocol it accompanies, it is a **prospective post-Gate-1
protocol-owner amendment created under the maximum-authorization instruction; NOT
historically preregistered.**

**Dispositions used:** `FIXED` (and how) · `NOT-A-DEFECT` (and why) ·
`ACCEPTED-LIMITATION` (why, and where disclosed).

**Summary of the 38 defects, counted exactly.**

```
FIXED                                     37   (D1-D13 all; S1-S15, S17-S25)
ACCEPTED-LIMITATION as the primary
   disposition                             1   (S16)
                                          ---
                                           38

Sub-claims inside an otherwise-FIXED defect that are themselves NOT-A-DEFECT:  2
   - D4's proposed n = 1632 (not admissible under the lattice rule; the alpha
     half of D4 IS a real defect and IS fixed)
   - S19's "twenty more places" mechanism (there is one shared mapping; the
     substance of S19 IS a real defect and IS fixed)

Residual limitations carried into v2 and disclosed in the protocol text:       3
   AL-1  reduced falsification power            (residual of D1 / S1 / D13(2))
   AL-2  Stage 0 generalises weakly to Stage 1  (residual of S11)
   AL-3  population chosen with pi_0 in view    (= S16, unrepairable in-document)
```

---

# PART 1 — `CRITIC_SCIENCE` D1–D13

## D1 — CRITICAL. Gate R's routes and Gate V's veto are arithmetically incompatible; both licensing terminals unreachable for every dataset.

**Disposition: FIXED.**

**How.** Gate V is **removed as a gate** (protocol §0.1, Decision 1) on **authority grounds,
not results grounds**. `befca0d` §2.3 verbatim: *"E2b may only corroborate or contradict a
conclusion already reached on E2a"* — an annotation applied after a conclusion, not a gate
determining whether it stands. The one place frozen authority grants E2b blocking power is
the §2.9 hook operationalised as `f4c1105` §4 GATE 1, which has already fired and is sealed.
A second E2b veto on the routing statistic has no basis in frozen authority, and because its
admissible set is the singleton `{C+D}` — E2b's own argmax — it operates as a **selector**,
which §2.3's second sentence forbids.

Gate V is replaced by a **mandatory reported corroborate/contradict annotation** (§21.4)
computed after the routing verdict is hash-sealed, applied identically to all three routes,
incapable of changing any terminal.

**The critic's own proposed fix was tested and rejected as insufficient.** Replacing TV with
`max_k |pi_k - pi_0k|` gives route B a minimum of `0.0781` against the same `0.0694` — the
impasse is robust to the statistic (§0.1). Changing the distance was not the repair.

**Reachability is now proven constructively** rather than assumed: §32.1 exhibits W-B, W-A,
W-CD and W-EX as integer per-condition count vectors with the certification arithmetic shown.

**The counter-argument is stated fairly in the protocol** (§0.1): `befca0d` §2.3's final
paragraph does attach a blocking consequence to disagreement. Its force is retained as the
§21.5 owner-ratification **explanation obligation**, which is dischargeable, route-symmetric,
and not an arithmetic threshold. See also `ACCEPTED-LIMITATION` at D13/S1 below.

## D2 — CRITICAL. `QND_PASS` is provably unsatisfiable; the protocol forbids its own execution.

**Disposition: FIXED — by deletion plus a decidable replacement, and the deletion is stated
plainly.**

**Verified independently.** Gate Q's Q1 requires the registry's twelve G2 conditions at equal
weight and `R` completed worlds per cell. The protocol's own §3 item 2 states E2a instantiated
**none** of the twelve. E2a's axes are `(family, regime, noise)` over 45 cells at 12 replicates
each; it carries no `partition` field. The enumeration family is **empty**.

**How fixed.** `QND_PASS` is **deleted from `QUALIFIED`** and terminal
`CIRCULAR_BY_MEASUREMENT` is deleted with it (§32.3). The property worth having is restated as
a question about the **map**, not a corpus, and made decidable:

> `NON_DETERMINATION_PROVEN` — exhibit, for each admissible route, a concrete distribution
> satisfying every Gate Q clause by construction that routes to that route.

Discharged **in the document** by W-B, W-A and W-CD (§32.1), which route to three different
arms under identical qualification clauses; re-verified mechanically at freeze time by a frozen
witness verifier (§31.1). §4.1 property (v) states honestly that this proves Gate Q does not
**determine** the route and does not prove it fails to **bias** it.

## D3 — CRITICAL. Gate V treats a 144-case draw as a constant; comparator noise consumes 69% of the tolerance and produces a 21% false HALT.

**Disposition: FIXED.** Largely moot under Decision 1 — the veto is gone — but the residual
reporting carries the comparator's uncertainty, as required.

**How.** §21.4 computes both `TV` and `D_max` with a **95% interval from a parametric bootstrap
that resamples BOTH sides** (`surface ~ Multinomial(1656, pi_hat)`,
`comparator ~ Multinomial(144, pi_0)`, `B = 10,000`, RNG `derive_seed_v2("bootstrap","E7-CC")`).
The annotation label is defined on the **interval**, never on the point estimate.

**Reproduced independently at 200,000 draws and recorded in the protocol before execution:**
comparator-noise-alone mean `TV = 0.0477` (69% of `delta`); `P(TV > delta)` from comparator
noise alone `= 0.177`; both-sides-sampled with the surface drawn from **exactly** `pi_0` at
`n = 1656`, `P(TV > delta) = 0.205`; and the annotation for a surface drawn from exactly `pi_0`
is **`INDETERMINATE`**, not `CORROBORATES`. That last fact is stated in the protocol as the
arithmetic reason the quantity cannot be a gate.

## D4 — MAJOR. Routing alpha is 0.10, not 0.05, under a post-selection argmax read one-sided; §27's "theorem" is false.

**Disposition: FIXED — critical value corrected and `n` re-derived.**

**How.** §10.2 adopts `z_.975 = 1.9599640` for the data-selected contrast, and §27 **withdraws**
v1's claim that no adjustment is needed "as a theorem". The critic's measurement was reproduced
independently: 0.100 at a two-way tie under v1's rule.

**`n` re-derived** (§10.4), with v1's sizing criterion preserved verbatim and only the critical
value changed:
`n >= (1-delta^2)(z_.975+z_.80)^2/delta^2 = 0.99517747 x 7.84887973 / 0.00482253 = 1619.6948`
⟹ `R >= 134.98` ⟹ **`R = 138`, `n = 1,656`**.

**Correction to the critic's own suggestion.** D4 proposed `n = 1632 = 12 x 136`. `R = 136` is
divisible by 2 but **not by 3**, so F19's `(F19A,F19B,F19C)` variant cycle would not be balanced
within each DEV/EVAL half. `R` must be divisible by **6**; `R = 138 = 6 x 23` is the smallest
admissible value. Recorded in §10.4.

**Realised type-I under the repaired composite rule (materiality + precision), measured:**
**0.0024** at a two-way tie, **0.0001** at a three-way tie — over-corrected, and reported as
such in §10.5 and §27 rather than claimed as exactness.

## D5 — MAJOR. `g_j <= 0.010` is vacuous; the top-up can never fire; §34's predicted Stage 0 state is impossible.

**Disposition: FIXED — deleted, with the equivalence stated as the identity it is.**

**How.** §0.4 states the exact equivalence, derived from §25.1's own monotonicity lemma (which
the critic verified and could not break): all three `reach_j` are disjunctions over row labels,
representative selection never reads `g2_correct`, `retained_by_argmax_score` is a score
comparison, so every resolution moves a world **weakly later** in `A ≺ B ≺ C/D ≺ E` and no
cancellation is possible. Therefore

```
INDETERMINATE_WORLDS == 0   <=>   g_1 = g_2 = g_3 = 0
```

**Deleted:** `g_max = 0.010`, the undeclared `1.4` behind it, precondition `P6`, and the entire
blinded top-up to `n = 1,944`. The Stage 0 gate is now `INDETERMINATE_WORLDS_E2A == 0` and
nothing else, and the protocol says explicitly that the real bar is `g = 0` exactly.

**§35's expectation is restated as a single binary** (`INDETERMINATE_WORLDS_E2A = 0`, ~65%),
replacing v1's impossible *"`g <= 0.005` and 0 indeterminate worlds"*.

**On the power-rescue mechanism the critic suggested reinstating on an endpoint-blind quantity:
declined, deliberately.** Any top-up mechanism reintroduces exactly the S6 pathology (raising
`n` lowers the effective margin). The materiality clause of §21.1 makes the margin independent
of `n`, and no top-up is declared. That is a strictly more conservative choice.

## D6 — MAJOR. An RSS ceiling decides a scientific finding; the wall-clock defect reproduced one level up.

**Disposition: FIXED — and fixed more strictly than the critic proposed.**

The critic's minimal fix was a **distinct terminal** `T-RESOURCE-BOUNDED-ON-THIS-HOST`. That is
insufficient under the binding constraint that *no resource limit may decide any scientific
label at any level, including meta-level terminals* — a named terminal is still a scientific
state decided by host RAM.

**How fixed.** §25.4 introduces `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` as an **operational state
that is explicitly NOT a member of the §32 terminal set** and explicitly not a finding about
the contract, the pipeline, the surface or the instrument. On exhaustion: execution
**suspends**; no seal is written; no routing verdict is computed; **no scientific label,
terminal or meta-terminal of any kind is emitted**. The offending expressions and the host
envelope are published. The run may be resumed on a larger host under the identical frozen
protocol hash with the ledger still empty — **not a retry under `P10`**, because nothing
scientific was read. If no attainable host resolves them, the protocol publishes the expression
set and the host envelope **and no scientific conclusion whatsoever**.

**The 260 CPU-hour ceiling is withdrawn** (§10.6, §25.4); no compute ceiling is declared
anywhere. **The RSS ceiling and worker count are declared parameters** (§34 FP-3, FP-4) with
`RSS_CEILING_GIB = 24` chosen below the 25 GiB at which Gate 1 lost cases, so the in-process
ceiling fires before the kernel OOM killer and the event is observable rather than a `SIGKILL`.

## D7 — MAJOR. Stage 0 leaks into Stage 1 through the resource-sizing channel.

**Disposition: FIXED — by the first of the critic's two options.**

**How.** §13 A4 and §25.5: `WORKER_COUNT` and `RSS_CEILING_GIB` are **profiled on the E2a
engineering DEV set** (§26(1), already permitted and already fully seen), **frozen and hashed in
the freeze manifest, and declared in §34 — before Stage 0 executes**. They may not be changed
after Stage 0 reports; any change is a tuning-ledger entry that fires §22 F7. The channel
`Stage 0 cost distribution → Stage 1 concurrency → Stage 1 terminal` is therefore severed at
its source rather than bounded.

## D8 — MODERATE. The fallback population fails Gate Q by construction, guaranteeing a false benchmark-defect diagnosis.

**Disposition: FIXED — by deleting the fallback, which is the critic's second option.**

**How.** §5.4 deletes the `development ∪ challenge` fallback outright. It supplies 7 replicates
per condition against 138, fails Q1 and P1 with certainty, and carries a contamination caveat
v1 conceded while proposing to use it inside a licensing instrument. The ladder is replaced by:

```
C-0 fails                            -> attempt Route R-A (owner-authorized delta)
R-A refused or fails                 -> NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT
Q1 fails for a MECHANICAL reason     -> BENCHMARK_INTEGRITY_DEFECT
```

The two terminals are **different findings and are named differently**. Only the second asserts
anything about the benchmark, closing the false-diagnosis path.

## D9 — MODERATE. The "sealed expression → label table" is not well-defined; the parity control may never run.

**Disposition: FIXED, both halves.**

**How (key).** §25.3 re-keys the table exactly as the critic's charitable reading requires:

```
CANONICALISATION TABLE  key: expression_string
                      value: (canonicalization_status, effective_support, discovered_family)
g2_correct(row, world) is computed per (row, world) from the table entry AND the world's
                       TruthRecord, by the imported byte-unchanged g2_contract primitives.
```

**How (parity).** `C-6` (§18, §28) makes two-architecture parity **mandatory and not waivable**
on the canonicalisation table — which needs **zero search** to reproduce — on a pre-declared
**500-expression** audit sample at **0 mismatches**. **If no second architecture can be reached,
`C-6` FAILS and the terminal is `VOID_CONTROL_FAILURE`.** v1's "discharged by construction and
unverified by execution" waiver is removed.

## D10 — MODERATE. Undeclared magnitudes inside a protocol whose central claim is that it has none.

**Disposition: FIXED — all six declared.**

| v1 undeclared quantity | v2 declaration |
|---|---|
| C-2 adversarial-construction count and pass bar | **12** (one per G2 condition), **12/12** — §18, §33, §34 FP-5 |
| C-3 known-answer world count and pass bar | **12** stages + **3** planted expensive rows, **12/12 and 3/3** — §18 |
| C-4 sample size | **101 rows** (Gate 1's own executed sample) — §18, §33 |
| C-5 subset size | **30 worlds × 30 seeds** (Gate 1's own executed replay) — §18, §33 |
| Row 1's exoneration band and "high `P_front`" | Replaced by the derived predicate `RETENTION_EXONERATED := pi_B < delta`, **zero new magnitudes** — §21.3 |
| Per-worker RSS ceiling | **`RSS_CEILING_GIB = 24`** — §25.5, §34 FP-3 |

Plus `WORKER_COUNT = 8` (§34 FP-4) and the C-6 sample of 500 (§18), which v1 did not have at
all. §34 is a dedicated free-parameter section replacing v1's false "exactly one new magnitude"
claim.

## D11 — MINOR. The §10 resolving-power table is not reproducible from its own formula and overstates headroom.

**Disposition: FIXED — republished, recomputed, for both critical values.**

**How.** §10.5 republishes the table from `d = sqrt(K/(n+K))`, `K = (z + z_.80)^2`, under the
protocol's own declared bound `pi_1 + pi_2 <= 1`, showing both the `z_.95` column (v1's rule,
for comparison) and the operative `z_.975` column. The critic's recomputation is reproduced
exactly: 0.2618 / 0.1547 / 0.1031 / 0.0689 at n = 84 / 252 / 576 / 1296.

At `n = 1,656` under `z_.975` the minimum lead detectable at 80% power is **0.0687 = 0.989
`delta`** — the same property `n = 1296` had under the wrong critical value, now honestly
computed. The critic's separate verification that the `n >= 1275.83` derivation itself was
**correct** is noted; only the table was wrong, and only the table is replaced.

## D12 — MINOR. `mass_power` is claimed to move to the NEG stratum; it is absent entirely.

**Disposition: FIXED.**

**How.** §7 states that `mass_power` is **absent from both strata**, that it is an E2a construct
rather than a registry family, that the NEG stratum is `F07` (`"mass-only g truth"`,
`registry.py:141`) and `F19` (null worlds), and that precondition **`P7` is satisfied by
construction, not by exclusion** (also restated at §20 `P7`). §7 additionally discloses the
consequence the critic drew: the surface says nothing about the family behind the
four-times-OOM-killed poison world.

## D13 — MINOR / GOVERNANCE. Gate V is a concealed necessary condition; T9 should be re-armed; the E6 dependency is unresolved.

**Disposition: (1) FIXED. (2) FIXED. (3) FIXED.**

**(1) The concealment paradox.** Dissolved by Decision 1: the §21.4 annotation is **not** a
necessary condition of any licence, so excluding it from support sets is simply correct rather
than a concealment (§15). Where it reads `CONTRADICTS` it must be **quoted in full in the
owner's ratification record** (§21.5) — disclosed, never concealed, never counted as support.

**(2) T9.** The critic was right that v1's Gate V was a quantitative Held-out-matching
requirement merely positioned after the seal, and that v1's own rule therefore armed T9. Under
Decision 1 there is **no** quantitative Held-out-matching requirement anywhere — not as a gate,
not as a veto, not as a necessary condition of any terminal — so T9 does not arise. §21.4
retains the arming rule verbatim and strengthens it: *any* future amendment making *any*
Held-out comparison a necessary condition of *any* terminal re-arms T9 automatically.

**(3) The E6 ceiling.** Resolved rather than deferred (§21.5 rider 1). The circularity was that
E6-the-**experiment** is self-blocked. But E6-the-**ceiling** is frozen text, verified verbatim
at `git show befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3 lines 137–140 (*"100 evaluable safety
opportunities … unsafe acceptance Wilson upper <= 0.15 => change survives … > 0.15 => VETO"*),
and the **opportunities come from this protocol's own NEG stratum** — 276 worlds, 2.76× the
frozen `>= 100` bar. No E6 execution is required and none is presumed. The dependency is closed
inside this protocol.

---

# PART 2 — `CRITIC_GOVERNANCE` S1–S25

## S1 — FATAL. Both licensing terminals unreachable; Gate V's admissible set is the singleton `{C+D}`, so the veto is extensionally a selector.

**Disposition: FIXED** (option 2 of the critic's three, executed under explicit protocol-owner
authority, which is what the critic said option 2 requires).

**How.** Decision 1, §0.1. Gate V is removed as a gate; the selector/veto collapse is the
**primary** stated ground, alongside the authority argument. The arithmetic S1 computed is put
**in the document** so the unreachability is a declared design property of v1 and not a
discovery (§0.1, §32.1's "Why this could not have been done under v1").

**Not chosen:** option 1 (delete the licensing terminals and relabel the protocol as
falsification-only) — that would make the instrument unable to satisfy D3 item 8 on any branch,
which is the disease rather than the cure. Option 3 (`n >= 8,006`) — a 6.2× compute increase to
preserve a veto that has no basis in frozen authority.

## S2 — FATAL (authority). The population plan mutates byte-protected benchmark content, and §5 misattributes the protection to the wrong modules.

**Disposition: FIXED. The finding was verified independently and is correct in both halves.**

**Verification performed on this host, reproduced in protocol §5.1:**

- `scripts/pb_33_amendment_a3_1_integrity.py:43` `PROTECTED_PATHS` — first two entries are
  `src/muru/paper_benchmark/registry.py` and `generator.py`, byte-identity enforced against A2.1
  commit `80a78032ac601466b35e9dce3fa56f6ae215605f`.
- `scripts/pb_34_rc3_integrity.py:40` `A2_1_PROTECTED_PATHS` — same.
- `grep -rn "rc5_seeds|seed_band_registry" scripts/pb_*.py` → hits **only** in
  `pb_50_build_global_science_plan.py` and `pb_rc5_a3_5_authorized_delta.py`; **no** hit in
  `pb_30`, `pb_33` or `pb_34`. **The v1 citation was inverted.**
- Both scripts pass today: `pb_33` → `A3.1 INTEGRITY VERIFIED`; `pb_34` → `RC3 INTEGRITY
  VERIFIED`.

**How fixed — Route R-B, and the freeze is honoured, not routed around.** Frozen authority
already prescribes the answer, verbatim, in `src/muru/paper_benchmark/rc5_seeds.py`'s own
docstring: *"**Why a new module.** A3.5 implementation obligation 9: A3.5's constants MUST live
in a new module importing the frozen ones, because `rc3_provenance.py`, `registry.py` and
`analysis.py` are byte-pinned by `pb_30`/`pb_33`/`pb_34` … Nothing here mutates a frozen
module."* v1's §5 sentence was a garbled paraphrase of that docstring with subject and object
exchanged.

Protocol §5.2 declares the calibration population in **two new files** in no protected list,
importing the frozen modules read-only, under a **`PBC` case-id namespace** that
`registry.resolve_case_id` rejects outright. Nothing in `registry.py`, `generator.py`,
`rc5_seeds.py` or `seed_band_registry.py` is modified; the benchmark's case population remains
the frozen 380; `iter_case_ids("calibration")` still raises.

**The duplication risk is discharged exhaustively rather than argued.** Control `C-0`:
`generate_calibration_case_body(cid, *registry.resolve_case_id(cid)).content_hash ==
generator.generate_case(cid).content_hash` for **all 380 frozen case ids**. **Executed during
authorship: 380/380 identical, 0 mismatched, 5.3 s.** Verified alongside: the frozen resolver
rejects `PBC|calibration|F17|r000`; that id generates with `partition="calibration"` and
`mathematical_family="mass_affine_descriptor"`; its `derive_seed` differs from the
corresponding `held_out` id; F19's variant cycle is preserved.

**Seed band** (§5.2): a new band `[2_100_011_400, 2_100_069_359]`, base **derived by a
registered rule** (`rc5_seeds.A35_SEARCH_SEED_MAX + 1`, computed at import, never a literal),
checked against the seven declared bands with the frozen registry's **own** `find_overlaps` on
a runtime-constructed tuple. `DECLARED_BANDS` is **not** mutated, because
`seed_band_registry.py` is pinned by the closed RC5 authorized-delta ledger.

**Route R-A retained as the declared alternative** (§5.3): if `C-0` ever fails, the amendment
proceeds only through the repository's own hash-pinned authorized-delta mechanism plus an
explicit protocol-owner ratification, with per-family `partition_counts` and three frozen test
files updated as further ledger entries.

**The critic's minimal fix is adopted verbatim in addition:** Q1 and `P9` now require *"`pb_33`
and `pb_34` return 0 errors, every protected path byte-identical to its baseline or matched
exactly by a registered authorized-delta entry"* — so Q1 and P9 can no longer pass while a byte
freeze is broken. v1's ordinal-stability preflight checked ordinal **values**, not file
**bytes**.

## S3 — BLOCKING. `TV` is never defined; the factor-of-2 ambiguity is outcome-determining.

**Disposition: FIXED.**

**How.** §21.4 defines `TV(p,q) := 0.5 * SUM_i |p_i - q_i|` (the half-sum convention, which is
the one `SYNTHESIS_DECISION_RECORD.md` §1.3's own table uses) and additionally defines and
reports `D_max(p,q) := MAX_i |p_i - q_i|`, the per-class convention PE2-4 was actually frozen
on. Under Decision 1 neither gates anything, so the ambiguity is no longer outcome-determining
— but it is fixed regardless, because an undefined statistic in a frozen document is a defect
whether or not it is currently load-bearing.

## S4 — BLOCKING. "Exactly one new magnitude" is false; `g_max` decides a verdict; its derivation rests on an undeclared 1.4.

**Disposition: FIXED — the false claim is withdrawn and the offending magnitudes are deleted.**

**How.** The header's "exactly one new magnitude" claim is **removed** and replaced by a pointer
to **§34, a dedicated free-parameter section listing six**. `g_max = 0.010` and the `1.4` behind
it are **deleted entirely** (D5's finding, §0.4) rather than re-justified, so the most
consequential of the critic's three parts disappears rather than being relabelled. The two
further multipliers the critic flagged are handled explicitly:

- the tier-1 `12×` multiplier is **declared, not derived**, and appears as **FP-2** in §34 with
  the statement that no frozen source supplies a multiplier;
- the `1.5×` top-up multiplier is deleted with the top-up.

The critic's recomputation `(delta/(delta-g))^2 = 1.3647` at `g = 0.010` (not 1.4) and the
observation that the criterion would actually select `0.010753` are recorded here as the reason
the derivation was not repaired but discarded: it was fitted to a round number, and the gate it
supported was vacuous.

## S5 — BLOCKING. `delta = 10/144` is labelled REUSED VERBATIM but is a re-purposing across two different estimands.

**Disposition: FIXED — moved to DERIVED with the derivation shown.**

**How.** §10.1 and §33 move `10/144` from the REUSED table to the **DERIVED** table with a
stated derivation: the frozen quantity is *"a difference of more than 10 cases between two class
counts on a 144-case denominator is material"*; ported to a proportion per P2 BC-16 it reads
*"a difference of more than 10/144 between two classes' shares is material"*; **the direction of
generalisation (two-way split → four-way partition) is stated, together with why it is
conservative for the routing decision.**

**One of the critic's two flagged uses is deleted rather than derived:** the total-variation
application (v1's Gate V) goes with Decision 1. `TV` survives only as the §21.4 reference scale,
gating nothing. So the number now has exactly **one** operative use — the routing lead — and
that use is derived in one place.

## S6 — BLOCKING. Certification is `LCB > 0`, so the top-up licenses a lead of 0.81 delta.

**Disposition: FIXED — the critic's minimal fix is adopted verbatim, and the top-up is deleted
independently.**

**How.** §21.1:

```
ROUTING_CERTIFIED := argmax invariant AND (pi_top - pi_second) >= delta
                                      AND LCB_97.5(pi_top - pi_second) > 0
```

The materiality bar is now **explicit, frozen, and independent of `n`**. The top-up S6's fix was
needed to make safe is deleted anyway (D5), but the repair is kept because it is correct on its
own terms: at `n = 1,656` the precision clause alone would certify leads down to
`z_.975/sqrt(n+z^2) = 0.0481 = 0.693 delta`, well below materiality, so the clause is binding
and not redundant.

**The cost is disclosed rather than absorbed** (§10.5, §35). Any rule that refuses to certify a
sub-material lead has `P(certify) = 0.5` at `L = delta` **for every `n`** — v1's advertised "80%
power at a lead of `delta`" was attainable only *because* it certified sub-material leads, which
is S6's finding restated. Measured operating characteristic at `n = 1,656`: 0.499 at `1.0 delta`,
0.821 at `1.30 delta`, 0.936 at `1.5 delta`, 0.999 at `2.0 delta`.

## S7 — BLOCKING. The exoneration row has no declared band and was moved first, inverting `f4c1105` §4 while claiming verbatim.

**Disposition: FIXED, both halves — one by declaring a derived predicate, one by disclosing the
reordering instead of calling it verbatim.**

**How (numbers).** §21.3 declares

```
RETENTION_EXONERATED := pi_B < delta   under both resolutions
```

**derived, with zero new magnitudes**: `pi_B = S_1 - S_2` is exactly the share of worlds lost at
the retention stage, so "the retention rule is exonerated" is "retention loses less than a
material share", and *material* is the programme's own frozen `delta`. The absolute form is
preferred over the frozen ratio form because the ratio form needs a **second** undeclared
threshold ("high `P_front`") while the absolute form needs none, and because it **dominates**:
`pi_B < delta` ⟹ `P_retain_given_front >= 1 - delta/S_1 >= 1 - delta`.

**How (order).** §21.3 declares **two departures from the literal frozen ordering and labels
them departures, not reuse.** Position: this protocol evaluates exoneration **after** all three
certified routes, because `f4c1105`'s scope is *retention adoption* and its "STOP" means "no
retention policy is scored", whereas this protocol routes three ways. It is further recorded
that the reordering is **operationally vacuous on route B** — a certified `B` requires
`pi_B >= delta`, so exoneration and route B are mutually exclusive by arithmetic — and can only
affect routes `A` and `C+D`. The exoneration terminal
`RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` remains **reachable and is proven so** by witness
W-EX (§32.1).

## S8 — BLOCKING. Terminals are neither mutually exclusive nor exhaustive; F8 emits two; F10 has none.

**Disposition: FIXED — every element of the critic's minimal fix is adopted.**

| Critic's requirement | v2 |
|---|---|
| Make §22 the sole terminal-assigning authority | Done — §22's title and first paragraph; §18/§20/§21 identify the failing clause only |
| Delete terminal names from §20 and Gate R row 0 | Done — Gate R row 0 reads *"§22 assigns the terminal from the failing clause"* |
| Redefine `VOID` as the residual | **Stronger:** `VOID` is **deleted as a state**. Four named `VOID_*` terminals replace it, each naming its own failure |
| Give F8 one terminal | Gate V is deleted, so v1's F8 no longer exists. Every §22 rule emits exactly one terminal |
| Give F10 a name | v1's F10 is now **F13 `D3_ITEMS_UNMET_NO_REENTRY`** |
| Fold in or separate Stage 0's terminals | §22.2 declares Stage 0's three D-INST terminals as a **disjoint set, sealed separately**, explicitly not members of §32 |
| Two terminals unreachable | Fixed by Decision 1 + Decision 2, and **proven** reachable constructively in §32.1 |

Additional exclusivity work not requested but required by the above: `SURFACE_NOT_QUALIFIED` is
split into F3–F7's five named terminals; `NO_ADMISSIBLE_SURFACE_EXISTS` is split into
`NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` and `BENCHMARK_INTEGRITY_DEFECT` (D8).
§32.2 checks the **negative** terminals for reachability as well.

## S9 — HIGH. The Stage 0 firewall is breached by `QND_PASS`, and `QND`'s population is plausibly empty.

**Disposition: FIXED — by the same deletion as D2, which removes both halves at once.**

**How.** `QND_PASS` is deleted from `QUALIFIED` (§4.1). With it goes the firewall breach: no
Stage 1 acceptance clause is any longer a function of any E2a partition, corrected or sealed.
The empty-family / vacuous-truth ambiguity the critic identified — which under the "not
constant" reading fires `CIRCULAR_BY_MEASUREMENT` **before Stage 1 executes** — cannot arise,
because the clause and its terminal are both gone (§32.3). The replacement,
`NON_DETERMINATION_PROVEN`, is evaluated on **exhibited witnesses over the routing map**, reads
no corpus at all, and therefore has no resolution to choose and no family to be empty.

## S10 — HIGH. The Stage 0 gate statistic is undefined on E2a, and its only published measurement is standardised to the Held-out mix.

**Disposition: FIXED — by deleting the statistic.**

**How.** `g_j` was the `w_k`-weighted statistic over the twelve registry conditions, and the
critic is right that it is undefined on a corpus containing none of them, and right that the
only published value (0.044–0.056) came from standardising E2a to the **Held-out truth-family
mix** — E2b entering the gate that permits the licensing instrument to run.

§0.4 deletes `g_j` from the Stage 0 gate entirely. The gate is now
`INDETERMINATE_WORLDS_E2A == 0` — a **count of worlds whose class is not invariant**, which is
well-defined per world on any corpus, requires no weighting of any kind, and therefore **carries
no Held-out-derived composition**. The 0.044–0.056 figure is not restated as a gate quantity
anywhere in v2.

## S11 — HIGH. `T-INSTRUMENT-UNBOUNDED`'s name and gloss misrepresent what a Stage 0 result establishes, in both directions.

**Disposition: FIXED — the critic's minimal fix is adopted, including the F17 disclosure.**

**How.** Renamed **`T-INSTRUMENT-UNBOUNDED-ON-E2A`** with the gloss restricted in §32: *"The
frozen G2 contract is not decidable at finite cost on the sealed E2a corpus. … It establishes
nothing about the calibration population, which contains 138 F17 worlds E2a does not contain."*

**The under-generalisation on PASS is disclosed in §0.5** in the critic's own terms: E2a has
**zero** F17 worlds, so a Stage 0 PASS is weak evidence that the instrument is bounded on a
population with 138 of them. Rather than add an F17 pilot to Stage 0 — which would require
generating Stage 1 worlds before the freeze — §0.5 states that **the real protection for Stage 1
is Stage 1's own precondition `P6'`** (`INDETERMINATE_WORLDS == 0` on the calibration surface),
and that Stage 0's gate is retained as a conservative instrument-validation step whose
generalising power is explicitly limited. See `ACCEPTED-LIMITATION` note at the end of this
ledger.

## S12 — HIGH. No freeze has occurred; §31 is unexecuted; the one freeze record in the directory is already stale.

**Disposition: FIXED (all four sub-items of the critic's minimal fix).**

| Critic's item | v2 |
|---|---|
| (i) Stop calling the document frozen | First page: **"Status at this commit: PROTOCOL TEXT. NOT YET FROZEN. D3 item 7 is UNMET."** Closing block repeats it |
| (ii) Supersede `DINST_FREEZE_SHA256.txt` rather than overwrite it | §31.8 requires `DINST_FREEZE_SHA256_v2.txt` recording the repaired tool's hash and the review that mandated the change, with the explicit rule *"a freeze record is never silently overwritten"* |
| (iii) Perform §31 before any Stage 0 compute | §31 is restated as a procedure to be executed, with an annotated tag `muru-freeze/e7-protocol-v2` and the freeze commit required to be a strict ancestor of the first data commit |
| (iv) Re-freeze or formally amend the D-INST **protocol** against its own failed review | Stated as a requirement in §31.8 |

## S13 — HIGH. The independent adjudicator is a placeholder; commit order is not information order.

**Disposition: FIXED — registration required, and the guarantee is downgraded to what it
actually supports.**

**How.** §29 states that D3 item 6 is **PENDING** and that *"a table saying 'named before
execution' does not satisfy it"*. The four parties must be **registered by name in the freeze
commit** with agent identity, model, invocation context, and what each may and may not read;
until then **no verdict issued is admissible**. §29 further states plainly: *"This proves
ARTIFACT order, not INFORMATION order. `pi_0` is printed verbatim in the ratification record
and in §21.4 of this document, which every party reads. The information barrier is zero; only
the artifact barrier is real, and that is the only claim made."* Under Decision 1 the
consequence of that weakness is small, because the annotation controls no terminal — which §29
notes is itself an argument for Decision 1.

## S14 — HIGH. The E6 circular dependency makes every licence non-executable, and v1 froze around it.

**Disposition: FIXED — the dependency is closed inside the protocol, not deferred.**

**How.** §21.5 rider 1. The distinction the critic's framing left implicit is made explicit:
E6-the-**experiment** is self-blocked; E6-the-**ceiling** is frozen text and is directly
applicable. Verified verbatim at `befca0d:MURU_V2_CAUSAL_DECISION_TREE.md` §3 lines 137–140.
The **evaluable safety opportunities come from this protocol's own NEG stratum** — 276 worlds
(F07, F19A/B/C), 2.76× the frozen `>= 100` bar — so an arm that breaches
`Wilson upper <= 0.15` on that stratum is not licensed, and **no E6 execution is required or
presumed**. The rider is a precondition on the licence, not a report.

## S15 — MEDIUM. The resolving-power table does not reproduce; every entry is optimistic.

**Disposition: FIXED.** Same repair as D11 — §10.5 republishes the table for both `z_.95` and
`z_.975`, showing the solve, reproducing the critic's recomputed values exactly. The critic's
verification that `n >= 1275.83` was itself **correct** is recorded; only the table was wrong.

## S16 — MEDIUM. Design-layer E2b conditioning in the population choice, disclosed but not discharged.

**Disposition: ACCEPTED-LIMITATION, with both of the critic's remedies applied — the disclosure
now, and the blind replication mandated before freeze.**

**Why it cannot be fully fixed in this document.** The charge is that the population's
composition rule was selected in a document that had `pi_0` in hand and reported the selection's
effect on distance-to-`pi_0`. That is a historical fact about how the rule was arrived at, and
no amount of re-argument inside this document can undo it. Only an independent, blind
re-derivation can.

**What is done.**
- §4.1 property (i) is **downgraded** exactly as the critic asked: *"the Gate Q predicate reads
  no E2b artifact; the population's composition rule was selected in a document that had access
  to `pi_0`. The provenance argument is independent but was not independently generated."*
- §3 item 1 now carries the disclosure inline and states that the 68.1% / 77.0% figures are
  **not** the argument for the population.
- §30 attack 1 is made **mandatory and blind** — an agent blind to §3 item 1 and to
  `SYNTHESIS_DECISION_RECORD.md` §1.3 must re-derive the population from `registry.py` alone —
  and §30 records that **it has not yet been performed**, so the charge stands until it is.

## S17 — MEDIUM. Row 3 cites `f4c1105` as "a complete operational freeze" though its own execution trigger has already fired STOP.

**Disposition: FIXED — the critic's minimal fix is adopted almost verbatim.**

**How.** §21.2, row 1's honesty note: *"`f4c1105` is operationally complete **but its own §4
GATE 1 returned STOP on the sealed Gate 1 result** … Executing E4a therefore requires a
protocol-owner act re-arming `f4c1105` against this surface, in place of its frozen and
already-fired GATE 1. That substitution is a change to frozen authority and requires
ratification; it is not reuse."* It is folded into the §21.5 owner-ratification step (item 2) so
it adds no new procedure — only honesty about what that step does. Verified by direct read:
`f4c1105` §4 GATE 1's text, and `GATE_1_DEFINITIVE.json`'s `E2B_69_57_HOOK = "FAIL"`.

## S18 — MEDIUM. `QUALIFIED` has two different definitions in the same frozen document.

**Disposition: FIXED, exactly as the critic prescribed.** §18 now **defines the clauses and
defers the predicate to §20**, and says so in bold. §20 carries the **single** definition,
including all ten preconditions. The section heading is *"ACCEPTANCE RULE — THE SINGLE
DEFINITION"*.

## S19 — MEDIUM. `PARTITION_CASE_COUNTS` is misread; `"calibration": 108` declares 108 replicates for all twenty families.

**Disposition: FIXED — the substance is confirmed and adopted; the stated mechanism is
corrected.**

**Substance confirmed and independently verified.** `iter_case_ids` reads
`family.partition_counts[partition]`, not the module constant directly, and it iterates **every**
family — so `{"calibration": 108}` would emit case ids for all twenty families (2,160 cases),
including the six v1 lists as "not searched", breaking `P1`. Also confirmed: `A35_TOTAL_CASES`
is computed dynamically over `PARTITIONS`, so adding one changes `A35_SEARCH_SEED_MAX` and the
declared band envelope.

**Mechanism corrected.** The critic states that *"each of the twenty `FamilySpec` literals
carries its own `partition_counts` mapping, so the amendment touches twenty more places"*. That
is **incorrect**: `registry.py`'s `_family` helper (`:118`) and the three explicit literals
(`:121, :157, :169`) all pass **the same shared `PARTITION_CASE_COUNTS` object**. There is one
mapping, not twenty. Recorded in protocol §5.1 so the record is right either way.

**How fixed.** Under Route R-B the issue does not arise at all: replicate counts are declared in
the new module as `CALIBRATION_REPLICATES = 138` over an explicitly enumerated 14 families
(§5.2), and the registry is untouched. Under Route R-A, §5.3 item 3 requires per-family
`partition_counts` — 138 on the fourteen searched families, **0** on the other six — plus
updates to the three frozen test files that assert the literal value, each as a further ledger
entry.

## S20 — MEDIUM. F9 (`> 1 surface => VOID`) contradicts the two pre-enumerated attempts and the blinded top-up.

**Disposition: FIXED.**

**How.** §22 defines `SURFACE` as one **independently parameterised** surface, and states that
the `C-0`→R-A ladder is **one** surface attempted under at most two construction routes with
**identical** parameters, both recorded in the ledger. The blinded top-up — the other half of
the contradiction — is deleted (D5), so the ambiguity is gone rather than merely defined away.
§25.4's resource resumption is separately declared **not** a retry, with the reason (no seal
opened, no verdict existed), and §30 attack 6 requires a hostile reviewer to attack that
declaration.

## S21 — MEDIUM. Stage 0's classify cache is unhashed, mutable, out of repo, and in the gating path.

**Disposition: FIXED, all three parts of the critic's minimal fix.**

**How.** §31.8: the cache is **hashed into the freeze manifest**, read with an explicit
`WHERE version = ?` filter (the missing filter the D-INST review found), and **re-verified at
Stage 0 seal time**. Explicit fallback declared: *"If it cannot be frozen, Stage 0's determinacy
figures are reported as conditional on an unhashed input and the gate is re-derived from an
uncached run."*

## S22 — MEDIUM. §3 item 3 and §25 reproduce two D-INST figures the hostile review showed are unsound.

**Disposition: FIXED — both clauses the critic asked for.**

**How.** §3 item 3(a): the operative cap is named as the parent-side
`conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` at `e2_classify.py:338`, with the note that it **also
absorbs pipe and worker failures under the same `SIMPLIFY_TIMEOUT` name**, so some of the 397
cached records may not be simplify timeouts at all. §3 item 3(b): the stage-A figure is retained
as **sound** (0 of 42,411 A-world rows absent from the cache) and the **B / C / E contamination
figures are labelled inferred UPPER BOUNDS**, with the absent-row counts (48,790/70,322;
31,781/35,988; 36,525/40,746) stated. The labelling requirement extends to any report of the
protocol.

## S23 — LOW. The filename says PREREGISTRATION; the ratification forbids it.

**Disposition: FIXED.** The v2 filename is
`MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V2.md`, and the header states why. The v1 file keeps its
name **as the superseded artifact**, since renaming a superseded document would break the
hash-and-citation trail the critic is protecting; the supersession notice on v2's first page
carries v1's sha256 so the linkage is explicit. The critic's separate finding that the **body
text** of both v1 and the synthesis record is exemplary on this point is noted and preserved.

## S24 — LOW. The protocol self-satisfies D3 item 8 and issues its own licence with no owner ratification step.

**Disposition: FIXED, with the critic's sentence adopted in substance.**

**How.** §21.5: *"A licence is PROPOSED by this protocol. It is ISSUED only by the protocol
owner. … Between the adjudicated verdict and any operative licence there is a mandatory
protocol-owner ratification record naming the arm, the parameter setting, and the scope. Absent
that record, the terminal is a proposal and nothing is licensed."* The three licensing terminals
are renamed `..._LICENCE_PROPOSED...` so the **name states what is true when it fires**, and
§22 F13 makes a refused or absent ratification terminate at `D3_ITEMS_UNMET_NO_REENTRY`.

## S25 — LOW. D4 (E5 DEFERRED) is never carried forward.

**Disposition: FIXED.** §32.4 states: *"No terminal of this protocol reconsiders E5. D4's
reconsideration trigger remains with the protocol owner and is not delegated to any terminal
above."*

---

# PART 3 — SUB-CLAIMS THAT ARE NOT DEFECTS, AND RESIDUAL LIMITATIONS

## NOT-A-DEFECT (2 sub-claims inside otherwise-FIXED defects)

**S19 (mechanism half).** The claim that the registry amendment *"touches twenty more places"*
because *"each of the twenty `FamilySpec` literals carries its own `partition_counts` mapping"*
is **incorrect as stated**: all twenty share one `PARTITION_CASE_COUNTS` object. The **defect
S19 identifies is real** and is fixed; only this sub-claim is not a defect in v1. Recorded in
protocol §5.1.

**D4 (proposed `n` half).** The critic's proposed `n = 1632 = 12 x 136` is **not admissible**
under v1's own lattice rule, which v2 retains: `R` must be divisible by 6 so that F19's
three-variant cycle is balanced within each DEV/EVAL half, and `136` is not divisible by 3. The
alpha half of D4 is a genuine defect and is fixed; the specific `n` is not the right answer.
`R = 138`, `n = 1,656`. Recorded in protocol §10.4.

## ACCEPTED-LIMITATION (3 residual limitations; AL-3 is also S16's primary disposition)

**AL-1 — Reduced falsification power (arising from D1 / S1 / D13(2)).**
Removing Gate V removes the design's only quantitative comparison against the sealed Held-out
attribution. Decision rule **R2** ("strongest falsification opportunity") is thereby overridden
by **R3** ("keeps Held-out evidence out of positive licensing") and by the plain reading of
`befca0d` §2.3's second sentence. The counter-argument — §2.3's final paragraph, *"If E2a and
E2b disagree, that … blocks adoption of any E4 conclusion until explained"* — is quoted at full
strength in protocol **§0.1** together with three responses and an explicit statement of what
survives the responses. The clause's force is retained as the §21.5 **explanation obligation**:
dischargeable, route-symmetric, an owner act on the record rather than an arithmetic threshold.
**Disclosed at:** protocol §0.1, §21.4, §21.5, §32.1's "disclosed asymmetry" paragraph.

**AL-2 — Stage 0 generalises weakly to Stage 1's population (arising from S11).**
Stage 0 runs on a corpus with **zero** F17 worlds and gates a stage whose population contains
**138**. A PASS is weak evidence of boundedness on the harder population; a FAIL says nothing
about it. The gate is retained anyway, because it is conservative and because the instrument
validation it performs is genuinely needed; the terminal is renamed and its gloss restricted so
it cannot be read as more than it is, and the real protection for Stage 1 is stated to be Stage
1's own `P6'`. No F17 pilot is added to Stage 0, because generating calibration worlds before
the freeze would breach the results-blind requirement it exists to protect.
**Disclosed at:** protocol §0.5, §32 (`T-INSTRUMENT-UNBOUNDED-ON-E2A` row).

**AL-3 — The population's composition rule was chosen with `pi_0` in view (arising from S16).**
Historical and not repairable by re-argument. §4.1 property (i) is downgraded to the honest
claim; §3 item 1 carries the disclosure inline; §30 attack 1 mandates a **blind independent
re-derivation before freeze** and records that it has not been performed. Until it is, the
charge stands unanswered and the protocol says so.
**Disclosed at:** protocol §3 item 1, §4.1 property (i), §30 attack 1.

---

# PART 4 — WHAT THE CRITICS FOUND SOUND, AND WHAT WAS PRESERVED UNCHANGED

Recorded because a repair ledger that lists only failures misrepresents the object being
repaired. All of the following were attacked and survived, and all are carried into v2
unchanged.

| Item | Critic finding | v2 |
|---|---|---|
| The determinacy bound's monotonicity lemma | `CRITIC_SCIENCE` CREDITS 1: correct, attacked at code level, no counterexample constructible | §25.1, unchanged — and now load-bearing for §0.4's `g = 0` identity |
| The instrument replacement (retiring `SIMPLIFY_TIMEOUT`, CPU-time cost bound, `BaseException`-derived cap exception, `UNRESOLVED` as its own state) | `CRITIC_SCIENCE` CREDITS 2; `CRITIC_GOVERNANCE` check 14: *"the strongest sections in the document … no wall-clock cap decides a label anywhere"* | §24, §25, unchanged and extended to resources (§25.4) |
| C-3's planted expensive-to-canonicalize row | `CRITIC_SCIENCE` CREDITS 3: *"precisely the known-answer test that would have caught the §3 defect"* | §18 C-3, retained, with its sizes now declared |
| The `n >= 1275.83` derivation and its distribution-free variance bound | Both critics verified exactly; not reverse-engineered to be affordable | §10.4, same method, corrected `z` |
| Row-5 pre-labelling as genuine and costly to the author | `CRITIC_SCIENCE` CREDITS 6 | Superseded by Decision 2 — but §21.2 row 3's anti-tampering rider preserves the intent: the E4f freeze predates any route and may not be amended after one |
| E2a as the engineering DEV set | `CRITIC_SCIENCE` CREDITS 7: *"a genuinely good idea: zero leakage … at zero scientific compute"* | §26(1), extended to carry the §25.5 resource parameters, which is what closes `D7` |
| No endpoint drift / proxy substitution | `CRITIC_SCIENCE`, "ON THE CENTRAL QUESTION": none found | §20's endpoint unchanged |
| Sealed Gate 1 unaltered; D5 handled correctly in both directions; the 28-field schema matching `befca0d` §2.4 field for field; per-arm channel monotonicity; real artifact-order enforcement; the E6 and E3 citations; `befca0d` §2.3 being destructive-only; the registry facts | `CRITIC_GOVERNANCE` checks 2–14, all PASS or VERIFIED | Carried unchanged; the E6 and E3 citations were independently re-verified for this version |

---

**TERMINAL STATE OF THIS LEDGER: COMPLETE. 38 of 38 critic defects dispositioned.**
**37 FIXED · 1 ACCEPTED-LIMITATION (S16) · 2 NOT-A-DEFECT sub-claims · 3 residual limitations
(AL-1, AL-2, AL-3), each disclosed at a named section of the protocol text.**
**This ledger licenses nothing and alters no sealed evidence.**
