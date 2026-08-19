# D-INST HOSTILE REVIEW — pre-execution falsification attempt

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md`
(sha256 `5b2d2ae5…b646`) and `scripts/e2a_instrument_diagnostic.py`
(sha256 `14a50d51…005a`), tag `muru-freeze/dinst-protocol`, commit `7e99830`.
Both on-disk hashes verify against `DINST_FREEZE_SHA256.txt`.

**Posture:** hostile. The author's stated hypothesis (§10) is that E2a's stage-A
attribution is inflated by a wall-clock artifact. I went looking for the mechanism
by which the protocol could deliver that answer, and for the ways it breaks.

## VERDICT

```
DINST_REVIEW = FAIL
```

Two blocking defects (the run cannot execute as written, and its own resource
failures are silently converted into scientific labels), two high-severity design
defects (the primary statement is unimplemented; one of the two headline claims is
arithmetically vacuous), and one high-severity honesty defect (a terminal state
whose own gloss inverts its meaning). Not fatal to the *idea* — the diagnostic is
worth running — but it must not be executed in its frozen form.

---

# 1. BLOCKING DEFECTS

## D1 — CRITICAL. The tool will kernel-OOM the host. Measured, not predicted.

`e2a_instrument_diagnostic.py:69-71` launches the child with **no memory bound**;
`:83` defaults to **12 concurrent workers**; `:22` sets `ESCALATION_SECONDS = 1800`,
removing the 5 s cap that was the only thing bounding memory as well as time.

I sampled one stage-A timed-out pair at random (seed 1) and ran the tool's *exact*
`-c` payload from `eval_one`:

```
PID 65494   RSS 44,375,516 kB (44.4 GB)   after 95 s
host: 48,160 MB total, 1,826 MB available
```

**One** of the 314 pairs consumed 92 % of a 47 GB machine in 95 seconds. Twelve
concurrently is an immediate global OOM. I killed it to protect the host.

This is not a novel discovery on this repo — it is a repeat:

- `results/e2/run_x86_e2a_v1/POISON_WORLD_DETERMINATION.json`: world
  `V2C|E2|mass_power|c_low|n_default|r000` OOM-killed **four** times at 33.4 /
  47.7 / 47.7 / 47.5 GB, and *"systemd then tore down the whole shared tmux scope,
  taking 11 healthy shards with it."*
- Gate 1 hit the same wall (`FROZEN_EVALUATOR_EXECUTION_MANIFEST.json:8`: *"two
  cases killed by the kernel OOM killer above 25 GB anon-rss"*) and answered it with
  a **memory governor** — `audit/e2b_definitive_cloud_adjudication_20260818/_memory_governor.log`
  shows `CULL pid=… rss_mb=32102 / 28468 / 38633`.

D-INST claims (§2) to reuse Gate 1's method verbatim and omits the one control Gate 1
needed to finish. `befca0d` §2.10, cited in the protocol's own authority table, says
*"simplify is unbounded in the worst case"* — unbounded in memory, not only in time.

**Does it change the conclusion?** It prevents one. The run dies, or worse, dies
partially and leaves a checkpoint set that looks complete.

**Minimal fix.** In the child code string, `import resource;
resource.setrlimit(resource.RLIMIT_AS, (N<<30, N<<30))`; set `--workers` ≤
`floor(host_GB / N)`; record `MEMORY_EXCEEDED` as a distinct resolution reason.
Note this fix *activates* D2 — apply both together.

## D2 — CRITICAL. An OOM or recursion blow-up is silently recorded as INCORRECT, not UNRESOLVED. This is the exact defect under test, re-committed.

Protocol §8: *"A subprocess kill, OOM, or budget exhaustion is recorded as
`UNRESOLVED` and is **never** converted into `INCORRECT`."* The tool violates this.

`g2_contract.py:162-165`:

```python
    try:
        simplified = simplify(parsed)
    except Exception:
        return None
```

`MemoryError` and `RecursionError` are `Exception` subclasses. So an in-process
resource failure inside the child yields `None` →
`classify_support(None, ts)` → `SUPPORT_UNRESOLVED` (`g2_contract.py:178-179`) →
`evaluate_g2_event` → `UNEVALUABLE` (`g2_contract.py:413-414`) → the child prints
`VERDICT{"correct": false}` → `e2a_instrument_diagnostic.py:77` records
**`INCORRECT`**. No kill, no timeout, no missing verdict line — a clean, confident,
wrong classification.

Gate 1 anticipated this precisely and fixed it.
`FROZEN_EVALUATOR_EXECUTION_MANIFEST.json:15`:

> `"cap_exception_base": "BaseException (deliberately, so g2_contract's six
> \`except Exception: return None\` handlers cannot swallow a cap and silently turn
> it into not-correct)"`

D-INST drops that protection while asserting it reuses Gate 1's standard.

The direction matters and cuts *against* the author, which is the only reason this
is not disqualifying on bias grounds: a swallowed failure produces INCORRECT, which
preserves stage A. But it is still a machine resource limit deciding a scientific
label — verbatim the sin §3 is written to expose — and it makes `LOWER` unsound as a
*bound* rather than merely conservative.

**Minimal fix.** In the child: compute `s = extract_effective_support(e)`; if `s is
None`, re-derive independently (`_safe_parse` then `simplify`) *outside* the swallow
and emit an explicit `VERDICT_UNRESOLVED` on `MemoryError`/`RecursionError`/
`BaseException`. Emit `INCORRECT` only when the `None` genuinely came from
`_resolved_support` (unknown symbol) or when support/family genuinely mismatch.

---

# 2. HIGH-SEVERITY DEFECTS

## D3 — HIGH. §6's primary statement is not implemented, and the freeze therefore covers the instrument but not the inference.

`main()` (`e2a_instrument_diagnostic.py:81-120`) ends at
`print("[D-INST] evaluation complete")`. There is:

- no stage recomputation under the witness order;
- no `LOWER` / `UPPER` construction;
- no `E2A_ATTRIBUTION_DETERMINATE`, no `E2A_PLURALITY_INVARIANT`;
- no terminal state from §9;
- **no output artifact at all** — `OUT` (`:19`) is used only to site `CKPT`.

Everything §6 calls "the only claim this diagnostic makes" is unwritten code.

Compounding it, `:117` (`if r["verdict"] == CORRECT or done % 25 == 0`) streams
CORRECT verdicts to the console preferentially. So the analysis will be authored
*after* the answer is visible, and it carries real discretion: what to do with the
2 stage-A worlds whose retained row was abandoned (see D7), how to split C vs D
without an equivalence call, how to treat UNRESOLVED-from-crash (see D10), how to
handle the missing 540th world (D13).

**Does it change the conclusion?** It determines whether "frozen before any
diagnostic result is computed" (protocol header) is a true statement. As frozen, it
is true of the measurement and false of the inference.

**Minimal fix.** Implement §6 in the frozen tool and re-freeze before executing.
`§10`'s pre-recorded expectation cannot substitute for discretion that was never
written down.

## D4 — HIGH. §9's terminal-state gloss can label the maximal overturn "attribution stands as sealed".

§9: `D-INST-DETERMINATE` — *"Every affected world's stage is invariant; E2a's
attribution stands as sealed."*

Invariance in §5/§6 is invariance across the **UNRESOLVED** set, not agreement with
the seal. Suppose all 314 pairs resolve and 71 come out CORRECT: every affected
world has zero unresolved pairs, so LOWER ≡ UPPER, so the run is `D-INST-DETERMINATE`
— and the protocol's own table reports that 71 of 122 stage-A worlds moving is
"E2a's attribution stands as sealed." The maximal overturn and the null result share
a terminal state and a gloss that fits only one of them.

**Minimal fix.** Two orthogonal axes, both reported:
`RESOLUTION ∈ {DETERMINATE, INDETERMINATE}` × `AGREEMENT ∈ {CONFIRMS_SEAL,
OVERTURNS_SEAL}`. Never gloss determinacy as agreement.

## D5 — HIGH. `E2A_PLURALITY_INVARIANT` is forced TRUE by arithmetic; it is provable at freeze time without a single sympy call. §10 misdescribes its failure as "plausible".

Sealed counts (recomputed by me from `results/e2/run_x86_e2a_v1/worlds_shard_*.jsonl`,
539 worlds): **A=122 B=196 C=102 D=0 E=119** — matching D5 of the ratification.

Enumerate every channel by which a timed-out row can move a world (witness order,
`MURU_V2_E2_PREDECLARATION.md` §6 / `lazy_classify.py:238-297`):

| Channel | Requires | Observed in corpus |
|---|---|---|
| B → C/D/E | a timed-out **retained** row in a B world | **0** |
| C → E | the world's **representative** is a timed-out row | **0 of 539** |
| E → anything | impossible (rep already correct) | — |
| A → B | any timed-out non-retained row correct | 71 worlds possible |
| A → C/D/E | a timed-out **retained** row in an A world | **2** |

Timed-out retained rows by sealed stage: `{C: 3, A: 2, E: 1, B: 0}`; and none of the
6 is its world's `representative_expression`. Therefore, at **both** extremes:

```
B >= 196   (B can never lose a member)
A <= 122   (A can never gain one)
C + D <= 102 + 2 = 104
=> (B > A) AND (B > C+D) holds identically under LOWER and UPPER.  QED.
```

Up to ~13 CPU-hours (314 pairs x 1800 s / 12) buys nothing for this claim. And D5 of
the ratification already forbids citing B's plurality to license E4a, so it is
governance-moot as well as vacuous.

**Minimal fix.** Delete `E2A_PLURALITY_INVARIANT`, or replace it with the four-line
proof above, computed and asserted at startup.

---

# 3. MEDIUM-SEVERITY DEFECTS

## D6 — MEDIUM-HIGH. §2's "reused verbatim, no new rule" is false. Three new rules, one of them a changed number.

Gate 1's actual standard, `FROZEN_EVALUATOR_EXECUTION_MANIFEST.json:9-23`:

> 5 s cap → *"A case receives a class ONLY IF the frozen four-way decision tree yields
> the same class under EVERY consistent resolution of its UNRESOLVED rows, enumerated
> over the at most three booleans the tree reads"* → *"Cases whose class was not
> invariant were resolved by evaluating their few decisive expressions individually,
> to completion, on dedicated subprocesses"* → `escalation_budget_seconds: 1500`,
> `INDETERMINATE_AFTER_BOUND: 4`, **`INDETERMINATE_AFTER_ESCALATION: 0`**.

D-INST departs on three points:

1. **1500 → 1800.** Undisclosed, unjustified, and in the direction that resolves more
   pairs.
2. **Enumeration domain changed.** Gate 1 enumerates over *the booleans the decision
   tree reads*; D-INST (§5) enumerates over *raw rows* (all-INCORRECT vs
   all-CORRECT). Equivalent for the two `any(...)` predicates, **not** equivalent for
   the representative branch — under UPPER, "all unresolved rows correct" does not
   determine `representative_g2_correct` when the representative is not itself an
   unresolved row.
3. **Terminal requirement dropped.** Gate 1 escalated until residual indeterminacy
   was **zero**. D-INST (§9) makes `D-INST-INDETERMINATE` an acceptable terminal
   state. That is a new stopping rule, not a reused one.

**On the 1800 s budget specifically (the reviewer's direct question).** Budget length
cannot flip a resolved INCORRECT into a CORRECT — a longer run only lets `simplify`
finish, it does not change the answer it finishes with. So 1800 s does **not** bias
the sign of resolved verdicts. But it monotonically increases how many pairs resolve,
and a resolved-CORRECT pair is the **only** way stage A is overturned in the `LOWER`
bound — which is the reportable point estimate. So yes: a longer budget makes an
A-overturning LOWER bound strictly more likely. It simultaneously narrows the
interval, which works *against* the author's §10 expectation of `INDETERMINATE`. Net
assessment: not a smoking gun, but a free parameter with an unstated pull toward the
author's thesis on the headline number, silently different from the number the
protocol claims to be reusing.

**Minimal fix.** Use 1500 s, matching the standard actually cited; or preregister a
budget-sensitivity report (verdict at 30 s / 300 s / 1500 s) so a reader can see
whether any CORRECT verdict is itself a budget artifact.

## D7 — MEDIUM. §4's scope argument is a non sequitur. The scope happens to be right, for a contingent reason the protocol never states or checks.

§4 argues: *"The witness order is `A if n_correct_on_front == 0`, so a timed-out row
can only change a world's stage by turning out to be correct. Only worlds sealed as
stage A can therefore change class on this evidence."*

The second sentence does not follow from the first. Under
`lazy_classify.py:238-269`:

- A timed-out **retained** row turning correct in a **B** world sets
  `n_retained_correct > 0`, moving B → E/D/C. The protocol never excludes this.
- A timed-out **representative** in a **C** world moves C → E.

I computed both: B has **0** timed-out retained rows and no world's representative is
in the timed-out set, so neither channel fires. The scope is numerically correct and
logically unjustified — on marginally different data the protocol would have
undercounted the correction it exists to measure. §4 states the stage-A retained
count (2) but never the B/C/E retained counts that actually carry the argument.

Separately, §4/§5 do not handle the **2 stage-A worlds with a timed-out retained
row**: if either resolves CORRECT, the world does not go to B — it goes to E, D or C,
and the C/D split requires `discovery.equivalence.algebraically_equivalent` on the
representative plus `rc5_selection.group_and_select`. Neither the §5 method nor the
tool computes either. Those two worlds are not reclassifiable by this diagnostic.

**Minimal fix.** State the two contingent facts in §4 and assert them at runtime; add
`group_and_select` + `algebraically_equivalent` for the 2 retained-row A worlds, or
declare them explicitly as "not-A, destination undetermined".

## D8 — MEDIUM. §3's contamination table over-counts B/C/E roughly 2x. "Timed-out row" is an inference from a global cache, not a per-row fact.

Every one of the 189,467 rows in `candidates_shard_*.jsonl` carries
`"classified": false`. The corpus **never records which rows E2a actually
classified.** `timed_out_expressions()` (`:26-29`) keys purely on
`expression_string` across the whole cache, so a row counts as abandoned if *any*
world's classification of that string timed out.

For stage A this is sound: `lazy_classify.py:274-297` full-scans every row of every
front, and I verified **0 of 42,411** A-world rows are absent from the cache. For the
controls it is not — these rows were never classified at all:

| Stage | front rows absent from the cache | of total |
|---|---:|---:|
| B | 48,790 | 70,322 |
| C | 31,781 | 35,988 |
| E | 36,525 | 40,746 |
| A | **0** | 42,411 |

The lazy classifier short-circuits (`lazy_classify.py:285`), so most B/C/E front rows
were never touched. §3's "B 20 / C 3 / E 1 worlds contaminated" is an upper bound
presented as an observation.

**Minimal fix.** Label the B/C/E control counts as inferred upper bounds, or restrict
the control set to rows demonstrably classified.

## D9 — MEDIUM. The frozen protocol's primary input is unhashed, mutable, outside the repo, and read without its version filter.

`:21` — `CACHE = ~/e2_x86_cache/classify_cache.sqlite3`, 89 MB, not in
`DINST_FREEZE_SHA256.txt`, not in git, freely mutable between freeze and execution.

`:28` — `select expression_string,result_json from classify_cache` with **no
`WHERE version = ?`**, although the table is keyed `(version, expression_string)`
(`classify_cache.py:159-164`). Today there is exactly one version
(`90a3b5ea…9e7a`, 52,450 rows, 397 `SIMPLIFY_TIMEOUT`), so today's numbers are right.
Any second version — e.g. from the replacement surface running on the same host —
silently contaminates the affected set with no error.

A hash-frozen protocol whose subject population is selected by an unhashed mutable
file is not, in the relevant sense, frozen.

**Minimal fix.** Pin and filter the version string; record the DB sha256, row count
and timeout count in the freeze manifest; abort on mismatch.

## D10 — MEDIUM. UNRESOLVED carries no reason. `returncode` and `stderr` are discarded, so total breakage is indistinguishable from genuine intractability — and maps to the maximal overturn.

`:74-78`:

```python
    for line in (p.stdout or "").splitlines():
        if line.startswith("VERDICT"): ...
    return UNRESOLVED, 0.0   # crash/OOM/kill -> UNRESOLVED, never a class
```

`p.returncode` and `p.stderr` are thrown away. An `ImportError`, a `build_world`
signature drift, a sandbox limit, or a `SIGKILL` all produce the identical record.
A systematically broken run yields 100 % UNRESOLVED — which under `UPPER` becomes
100 % CORRECT, i.e. the largest overturn the diagnostic can report — with no artifact
recording that nothing actually executed. §8 requires the UNRESOLVED count be
reported "prominently"; the record cannot say what it means.

**Minimal fix.** Record `returncode`, a `stderr` tail, and
`reason ∈ {TIMEOUT, SIGKILL, MEMORY, CRASH}`. Abort if the first N pairs all fail
without a verdict.

---

# 4. LOW-SEVERITY / IMPLEMENTATION

## D11 — LOW. A silent-wrong-truth hatch, and no identity assertion. (Item 3 itself: NO DEFECT — verified.)

`:60-61` — `ts = w.truth.support if hasattr(w,'truth') else None`. Were the guard ever
to fire, `classify_support(support, None)` returns MISMATCH
(`g2_contract.py:180-182`) and `classify_family_match(f, None)` returns
`FAMILY_UNRESOLVED` (`:435-436`): a silent, universal INCORRECT indistinguishable
from a real result. The tool also never asserts
`w.world_id == world_meta['world_id']`.

**On the reviewer's item 3 — the "single most dangerous silent failure mode" — I
find no defect, and tested it directly:**

- The original run used the identical call: `e2_run_shard_lazy.py:103`
  `world = e2_worlds.build_world(family, regime, noise, replicate)`, then `:129`
  `lc.lazy_evaluate_world(seed_raw_fronts, world.truth)`.
- Round-trip on a random sample of 6 worlds across families / regimes / noise:
  `world_id`, `coefficient` and `noise_sd` all match the persisted record exactly.
- Structurally immune to RNG or platform drift: `truth.support` and `truth.family`
  are pure family-keyed lookups (`e2_worlds.py:334-340` —
  `support=TRUTH_SUPPORT_BY_FAMILY[family]`, `family=family`). No seeded data path
  touches either field.
- **End-to-end control the protocol does not contain**: the diagnostic's exact
  composition recomputes **CORRECT on 5/5** sealed stage-E representatives and
  **INCORRECT on 3/3** sealed stage-C representatives.

**Minimal fix.** Replace `hasattr` with an assert; assert `w.world_id`; ship the E/C
round-trip as a startup self-test.

## D12 — LOW. Checkpoint keying and torn-file handling.

- `:101` keys on `(world_id, k, front_rank)` only — not on the expression string and
  not on `ESCALATION_SECONDS`. A resumed run at a different budget silently reuses
  old verdicts.
- `:103-104` catches `json.JSONDecodeError` but not `UnicodeDecodeError`, which a
  torn multi-byte write raises; it would propagate out of `fut.result()` (`:116`) and
  kill the run.
- `:110` `ck.write_text(...)` is non-atomic.

**Minimal fix.** Write `.tmp` + `os.replace`; include the budget in the key; widen the
except.

## D13 — LOW, disclosure. The 540th world is silently absent.

The corpus holds **539** worlds; `MURU_V2_E2_PREDECLARATION.md` §6 says 540. The
missing one is the poison world `V2C|E2|mass_power|c_low|n_default|r000`
(`POISON_WORLD_DETERMINATION.json`). §3's table sums to 539 without saying so, and
`load_corpus()` (`:32-46`) drops it without comment. One line of disclosure.

## D14 — INFORMATIONAL. §3's named mechanism is not quite the operative one.

§3 attributes the loss to `signal.alarm(5)` around `sympy.simplify`. In the code that
actually produced this corpus, the authoritative cap is the parent-side
`conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` at `e2_classify.py:338`, which covers the
**whole** `_classify_compute` — parse, simplify, `extract_effective_support`,
`classify_discovered_family`, `template_key`, `coefficient_vector` — and whose
timeout branch (`:348-361`) also absorbs pipe and worker failures under the same
`SIMPLIFY_TIMEOUT` name. So some of the 397 cached timeouts may not be simplify
timeouts at all. The *effect* §3 describes is exactly right (`None` →
`SUPPORT_UNRESOLVED` → not-SUCCESS); the named cause is imprecise.

---

# 5. RULINGS ON THE SPECIFIC QUESTIONS

## Item 2 — Is the uncapped path equivalent to what the classifier would have computed? **YES. No defect.**

`e2_classify.py:161-162` calls `extract_effective_support(expression_string)` and
`classify_discovered_family(expression_string)` — the same two functions, on the same
raw string, that the diagnostic calls at `:64-65`. The gate on
`canonicalization_status == "OK"` is *not* a data dependency: `extract_effective_support`
re-runs its own `_safe_parse` + `simplify` internally (`g2_contract.py:158-170`) and
consumes nothing from the classifier's earlier simplify. The diagnostic pays the cost
twice and gets the right answer. `lazy_classify._g2_correct` (`:173-179`) composes the
same three calls in the same order. `TEMPLATE_KEY_FAILED` cannot interfere — lines
161-162 execute before the template block. No caching bridges the two paths (the
sqlite cache is read-only here; `_CACHE` is process-local). **Confirmed by the E/C
round-trip in D11.**

## Item 6 — Is the interval one-sided by construction? **The premise is wrong; a real one-sidedness exists elsewhere, and is not disclosed.**

`LOWER` does **not** reproduce the original run. Per §5, LOWER assigns each *resolved*
pair its true verdict and forces only the *residual* UNRESOLVED set to INCORRECT. It
coincides with the original only in the degenerate case where all 314 stay
unresolved. So the interval is genuinely two-sided about the corrected point
estimate — correct behaviour, not a defect.

The real asymmetry is different and undisclosed: relative to the **sealed** value the
entire interval is one-sided, because the mechanism can only turn a `False` into a
`True`. Both endpoints can only move worlds *out of* A; neither can move one *into*
it. This monotonicity is what makes D5 vacuous, and a reader will otherwise read
"interval" as symmetric uncertainty about the seal. State it.

## Item 4 — Governance.

- **D5 (E2a invalidated as a calibration surface): partial conflict.** Running the
  diagnostic does not violate D5 — D5 expressly preserves E2a as "synthetic-domain
  diagnostic evidence", and §7's may/may-not list is faithful. But
  `E2A_PLURALITY_INVARIANT` (§6) reconstructs the E4a routing predicate
  `(B > A) AND (B > C+D)` and, being forced true (D5 above), manufactures a
  strengthened form of exactly the sentence D5 prohibits citing — *"the plurality of
  `B` may **not** be cited to license E4a."* A disclaimer attached to the artifact
  does not travel with the artifact. **Remove the predicate.**
- **D6 (no retroactive fabrication of missing provenance fields): NOT violated.**
  Recomputing `g2_correct` from the persisted `expression_string` plus a
  deterministically reconstructible truth, through the unmodified frozen contract, is
  **re-measurement from primary data**, not fabrication. `g2_correct` is a derived
  quantity, not a provenance field; D6 targets fields recording unrecoverable facts
  about how a row was produced (`admissibility` and the 15 other §2.4 fields named in
  §8 of the ratification). The output goes to a separate audit directory and is never
  written back into the corpus — keep it that way. **However**, there is a
  D6-adjacent honesty issue: *which rows were abandoned* **is** a provenance fact, it
  **is** absent from the corpus (`"classified": false` on all 189,467 rows), and
  D-INST infers it from a global expression-keyed cache. Sound for stage A, unsound
  for B/C/E (D8). Present it as inference, not as record.
- **Does it reopen the sealed Gate 1? NO.** Gate 1 compared E2b's direct classes
  against the v1 69/57 hook. D-INST touches only E2a's internal `first_loss_stage`.
  No sealed Gate 1 quantity and no D1 attribution quantity is an input or an output.
- **Does it create a path to license an E4 arm? No direct path**, given §7's explicit
  prohibitions. The residual risk is the plurality artifact above — remove it and the
  risk goes to zero.

## Item 5 — Results-blindness.

Foreknowledge that 73/122 stage-A worlds are contaminated and that the bias is
monotone does **not** by itself contaminate a protocol that introduces no new
threshold; §2's claim on that narrow point is the right instinct. But three live
degrees of freedom remain:

1. `ESCALATION_SECONDS = 1800` — a free parameter, undisclosed as a change from
   Gate 1's 1500, with a real (if modest) pull toward an A-overturning LOWER bound
   (D6).
2. The scope-to-stage-A decision — correct on the data, but resting on an argument
   that does not entail its conclusion and was never checked against the corpus (D7).
3. **Decisively: the analysis is unwritten** (D3). The map from 314 verdicts to §6's
   primary statement will be authored with the verdicts already on screen — including
   the genuinely discretionary calls (the 2 retained-row A worlds, the absent C/D
   split, the poison world, UNRESOLVED-from-crash). §10's pre-recorded expectation
   cannot cover discretion that has never been written down.

The freeze, as it stands, is a freeze of the instrument and not of the inference.

## Item 7 — Implementation, remaining items.

- **ThreadPoolExecutor + subprocess deadlock / fd exhaustion at 12 workers:** no
  deadlock; `subprocess.run` with `capture_output=True` reads both pipes via
  `communicate()`. FD usage is ~24 + sqlite — no exhaustion. **Memory, not fds, is
  the binding constraint** (D1).
- **`subprocess.run(timeout=)` handling:** correct — the child is killed and reaped;
  no grandchildren are spawned, so no orphan risk.
- **stdout verdict parsing:** `:74-77` scans all lines for a `VERDICT` prefix, so
  incidental child output is tolerated. Acceptable. A verdict line is only mis-read
  if the child itself prints a line beginning `VERDICT` — it cannot.
- **Worst-case wall clock:** 314 stage-A + 82 control = 396 pairs x 1800 s / 12
  workers ≈ **16.5 h**, undisclosed anywhere in the protocol. Under D1's fix, worker
  count must drop, so the true worst case is materially longer.
- **Crash treated as UNRESOLVED vs INCORRECT:** two distinct paths, and they disagree
  — an *external* kill gives UNRESOLVED (`:78`, correct per §8), an *internal*
  `MemoryError` gives INCORRECT (D2, violates §8).
- **Does the tool compute the stage recomputation and the LOWER/UPPER bounds at
  all?** **No.** Per-pair verdicts only (D3).

---

# 6. WHAT WOULD MAKE THIS PASS

1. Bound child memory (`RLIMIT_AS`) and reduce workers accordingly. **[D1]**
2. Make in-process resource failures emit UNRESOLVED, not INCORRECT — Gate 1's
   `BaseException` discipline. **[D2]**
3. Implement §6 — stage recomputation, LOWER/UPPER, terminal state, output artifact —
   and re-freeze *before* any verdict is visible. **[D3]**
4. Split §9's terminal states into resolution × agreement-with-seal. **[D4]**
5. Delete `E2A_PLURALITY_INVARIANT` or replace it with its arithmetic proof. **[D5]**
6. Use 1500 s, or preregister a budget-sensitivity report. **[D6]**
7. Fix §4's argument, assert its contingent premises at runtime, and handle the 2
   retained-row stage-A worlds explicitly. **[D7]**
8. Mark the B/C/E control counts as inferred upper bounds. **[D8]**
9. Version-filter and hash the sqlite input. **[D9]**
10. Record a reason code for every UNRESOLVED. **[D10]**

Items 1-5 are blocking. Items 6-10 are required for the record to be honest.

---

*Reviewer note: I did not execute the protocol. The single 95-second probe cited in
D1 was a feasibility and resource measurement on one randomly drawn pair; its
CORRECT/INCORRECT verdict was deliberately not recorded, examined, or reported, and
the process was killed before it returned one.*
