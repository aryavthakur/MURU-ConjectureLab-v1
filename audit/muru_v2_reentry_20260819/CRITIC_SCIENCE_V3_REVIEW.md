# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF PROTOCOL v3

# VERDICT: FAIL

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`
(2,748 lines, unfrozen text at HEAD `faad279`).
**Prior pass:** `CRITIC_SCIENCE_V2_REVIEW.md` — FAIL, 3 CRITICAL · 9 HIGH · 10 MED · 1 LOW (23 defects).
**Stance:** hostile. Default FAIL on uncertainty. Reward is for falsification, not approval.
**Method:** full read of the target; **execution** of `calibration_seed_band.verify_band`,
`calibration_surface.control_c0` and its drift assertions, `registry` variant enumeration,
`g2_contract.wilson_upper_95`, `e2c_classify.canonicalise` under injected resource faults, a
transitive-import closure check for `P8a`, a **full replay of the 396 quarantined null records
through the repaired instrument**, and an **exhaustive enumeration of all 457,380 attainable
per-condition `(A,B,C+D,E)` vectors × 4 side-conditions through §20/§21/§22** — the witness
verifier §31.1 promises and this repository still does not contain.

**Counts (new defects): 5 CRITICAL · 6 HIGH · 9 MED · 1 LOW.**
**Of my 23 v2 defects, 12 are genuinely repaired.**

---

## HEADLINE

v3 repairs `DEF-C1`. I confirmed it by execution: v2's `NO-BAND-COLLISION` predicate returns
`False` on every dataset, v3's returns `True`, and the calibration band is clean. v3 also
repairs the Stage 0 terminal defect: replaying the identical 396 null records through the
rewritten instrument yields `TERMINAL: null`, `OPERATIONAL_STATE:
RUN_INCOMPLETE_RESOURCE_EXHAUSTION`, where v2's tool emitted a pass terminal. Both of those are
real, executed, and to the executor's credit.

**And v3 died in exactly the same place v1 and v2 died: at the conjunction.**

v3 added six terminals (`F2a`, `F10a`, `F11a`, `F12a`, `F12b`, `F14`), one precedence rule
(`F0`), one new necessary condition on every licence (`E6_SAFETY_HEADROOM_PRESENT`), and one
new conjunct in `RETENTION_EXONERATED`. I evaluated the resulting rule set mechanically over
every surface it can ever see. **Four of the fifteen §22 rules cannot fire on any dataset:**

| rule | terminal | witnesses over all 457,380 surfaces |
|---|---|---:|
| `F13` | `D3_ITEMS_UNMET_NO_REENTRY` | **0** |
| `F14` | `SURFACE_DEGENERATE_NO_FRONT` | **0** |
| `F12a` | `E4F_POPULATION_REFERENCE_BROKEN` | **0** (table order) / headroom-absent only (numerical order) |
| `F2a` | `SURFACE_POPULATION_CONTAMINATED` | **0** (`mass_power` is not a registry `generative_kind`) |

The two consequences that matter are not cosmetic:

* **A surface on which no world ever reached the Pareto front proposes an E4 generation
  licence.** `S_1 = 0` forces `pi = (1,0,0,0)`, which certifies route `A` with `lead = 1` and
  `LCB = 1`, so `F11` `E4_GENERATION_LICENCE_PROPOSED_F09_F10` fires before `F14` ever runs.
  The `G3` repair explicitly routes that surface to `SURFACE_DEGENERATE_NO_FRONT`. It cannot
  get there.
* **A protocol owner who refuses ratification cannot terminate the protocol.** Gate R rows 1–5
  are exhaustive, `F8`–`F12b` cover all five, and `F0` says first match wins. `F13` is
  therefore unreachable *with all eight D3 items unmet and the ratification refused* — verified
  by enumeration under both readings of `F0`. The terminal that means "no re-entry, regardless
  of the route" has been starved by the terminals that mean "licence proposed".

Separately, `X-1` is not repaired but reproduced. `P8a` bans any module "reachable from the
search entry point" from binding `classify_support`, `classify_family_match`,
`evaluate_g2_event`, `truth_support_for_case` or "any name from the truth registry". §14 field
18 requires `effective_support`, whose *permitted* function `extract_effective_support` is
defined in `g2_contract` — and `g2_contract` binds **all four** banned symbols and imports
`TruthRecord`. Executed: 7 violations in a 14-module closure. `P8 ∈ QUALIFIED`, so `QUALIFIED`
is again unreachable by an independent route, which is what `X-1` said about the module ban.

And the §32.1 witness verifier — the one artifact I named first in "what would change my
verdict", the one whose absence *is* how `DEF-C1` survived v2's own §30 attack 3 — **still does
not exist.** §32.1 still asserts the witnesses "satisfy every Gate Q clause by construction."
Had that script been written, `F13`, `F14`, `F12a` and `F2a` would have surfaced in seconds.
I wrote it in forty lines and it found four unreachable terminals on the first run.

**Credit where it is due, and it is substantial.** `DEF-C1`, `DEF-C3`, `DEF-H4`, `DEF-H7`,
`DEF-M1`, `DEF-M3`, `DEF-M6`, `DEF-M7`, `DEF-M9` are genuinely repaired, most of them with
evidence I reproduced. The F19 split is **exactly 46/46/46** and `N = 230` and `2.30×` are
correct to the case. The derived strata reproduce the intended 12 + 2 families and the drift
assertion **actually fires** when I remove F18 from the registry. `C-0` is 380/380 in 5.0 s.
The classify-cache pin matches the live file byte for byte. §0.7's account of the executor's
own error — *"I inspected run 1's verdicts … and published that comparison, before the
instrument was final"* — is the most honest paragraph in this programme. `V3_REPAIR_LEDGER`'s
five graded dispositions are a real improvement over v2's "37/38 FIXED". None of that is
enough, because the licensing conjunction is still not checked mechanically, and it is still
wrong.

---

# PART 1 — REPAIR VERIFICATION (my 23 v2 defects)

| v2 defect | v3 claim | **Verdict** | Executed evidence |
|---|---|---|---|
| **DEF-C1** Gate Q's seed-band clause fails unconditionally | FIXED | **REPAIRED** | `find_overlaps(DECLARED_BANDS+(CALIBRATION_BAND,))` → `[Overlap('objval_plan2','rc3_engineering_smoke',…)]`, so **v2's predicate = False**. `verify_band()` → `overlaps_involving_calibration_band: []`, `preexisting_unacknowledged_overlaps: []`, `within_signed_32bit: True`, `NO_BAND_COLLISION: True`. Band `[2100011400, 2100069359]`, 57,960 seeds. **v3 passes, v2 fails, as claimed** |
| **DEF-C2** a 1500 s / 6 GiB cap decides the Stage 0 terminal | FIXED | **REPAIRED at Stage 0's terminal; §25's rule violated elsewhere (V3-C4, V3-H3)** | Replay of all 396 `_ckpt_dinst_ARCHIVED_ENVFAIL` records through `--analyze-only`: `verdicts {UNRESOLVED: 396}`, `ALL_AFFECTED_WORLDS_DETERMINATE: false`, `indeterminate_world_count: 73`, `decisive_unresolved_count: 314`, **`TERMINAL: null`, `OPERATIONAL_STATE: RUN_INCOMPLETE_RESOURCE_EXHAUSTION`**. v2's tool emitted `D-INST-NO-WORLD-MOVED` on this input. Genuine |
| **DEF-C3** Stage 0 executing pre-freeze, retuned after seeing its own output | FIXED | **REPAIRED** | Halted at 47/396; `_quarantine/` exists; §0.7 tabulates all three runs and states the executor's own error without softening; `S0-1..S0-5` added. `_ckpt_dinst` is empty at HEAD |
| **DEF-H1** §19 says no diagnostic changes a verdict; the E6 ceiling is a necessary condition of every licence | FIXED | **NOT REPAIRED — RELOCATED** → **V3-C5** | The ceiling now sits in `F10`/`F11`/`F12` as a hard conjunct. Its input `false_structure_events` appears **nowhere else in the document** (`grep`: one hit, line 1898). The only related quantity is §19 `D8` `false_structure_rate`, a declared **non-licensing** diagnostic on `D7`'s **DEV-half** arm grids. A §19 diagnostic still decides every licence |
| **DEF-H2** `E4A_LICENCE_PROPOSED_AT_<arm>` has no admissible arm source | FIXED | **OVERSTATED** → **V3-H4, V3-C5** | §22 renames it `E4A_ENTRY_LICENCE_PROPOSED`, but §32's terminal table **still reads `E4A_LICENCE_PROPOSED_AT_<arm>`** (line 2435) and §32.1/§35 read `E4A_LICENCE_PROPOSED`. Three names, three sections. Worse, the arm parameter **moved into §21.5**: `E6_SAFETY_HEADROOM_PRESENT` is evaluated *"for the arm named by the certified route"* — and no Gate R row names an arm |
| **DEF-H3** §22 neither exclusive nor exhaustive | FIXED via `F0` | **NEWLY BROKEN** → **V3-C1, V3-C2, V3-H1, V3-M1** | Exhaustive enumeration: `F13` 0 witnesses, `F14` 0 witnesses, `F12a` 0 witnesses under the table's own layout, `F2a` unreachable by construction. Exclusivity was bought by making four terminals unassignable |
| **DEF-H4** three `ROUTING_CERTIFIED` clauses provably vacuous, §21.1 asserts the opposite | FIXED | **REPAIRED** | v2's *"fails loudly"* sentence is struck and the clauses are relabelled defence-in-depth against a `P6'` bug, with the scientific content explicitly assigned to materiality + precision. Correct and honestly stated |
| **DEF-H5** E4f Gate H1 is a forced-direction zero-defect census | FIXED-BY-SCOPING | **ACCEPTABLE AS SCOPED** | Option (iii) taken: route `C+D` proposes **family i only**; family ii licenses nothing and its expected failure is pre-recorded. I checked E4f's own pre-recorded expectation: **`K1` passes Gate G1 at ~80%**, so family i is *not* symmetrically dead. The narrowing is substantive, not cosmetic. Residue disclosed below |
| **DEF-H6** FP-6's safety statistic is not independent of the efficacy endpoint | FIXED-BY-SCOPING | **ACCEPTABLE AS SCOPED** | Same disposition; the compromised gate now gates nothing |
| **DEF-H7** the ≥100-opportunity claim counts worlds; F19C is non-evaluable by design | FIXED | **REPAIRED** (residue → V3-M2) | Executed against the registry: `F19 → {F19A: 46, F19B: 46, F19C: 46}` over 138 replicates; `scalar_truth_defined` is `True/True/False`; `F07` 138 × `True`. **N = 138 + 46 + 46 = 230**, multiple **2.30×**. Every digit reproduces |
| **DEF-H8** §36 self-voids `C-6a` | FIXED via a third artifact + `F12a` | **NEWLY BROKEN** → **V3-H1** | The precedence rule is sound in text. Its terminal `F12a` cannot fire: `F12 ∪ F12b` exhausts `QUALIFIED ∧ row 3`, and `F12a` is listed **after `F13`** in a table whose governing rule says "numerical order". In the DEF-H8 scenario — route certified, headroom present, reference judged broken — the emitted terminal is `E4F_LICENCE_PROPOSED`, not `E4F_POPULATION_REFERENCE_BROKEN` |
| **DEF-H9** `RSS_CEILING_GIB` in-process ⟹ `RUN_INCOMPLETE` absorbing | FIXED via a host-derived rule | **NOT REPAIRED** → **V3-H2, V3-H3** | §25.5 **still reads** `RSS_CEILING_GIB = 24`, `WORKER_COUNT = 8`, *"profiled on the E2a engineering DEV set"* — i.e. `8 × 24 = 192 GiB` on a 47 GiB host, the `X-2` arithmetic verbatim — and §26(1), §31.1 and §34 FP-3/FP-4 **all name §25.5 as the source of the frozen values**. The Stage 0 instrument hard-codes `ADDRESS_SPACE_BYTES = 24 * 1024**3`, not the rule and not the 23.5 GiB the rule yields here |
| **DEF-M1** `n = 1656` DERIVED from an unattainable criterion | FIXED | **REPAIRED** | Relabelled against the precision clause; the composite OC (0.499 / 0.87 / 0.99) is pre-recorded in §10.5 and restated against the author's interest in §35 |
| **DEF-M2** certification tests the observed lead | DISCLOSED | **ACCEPTED, INCOMPLETE** → **V3-M8** | The disclosure is honest. It omits the stronger form: `pi_E` never enters the argmax, so `(0,10,0,128)` — 92.75% outright success — certifies route `B` and proposes an E4a licence |
| **DEF-M3** classifier version chosen at runtime by frequency | FIXED | **REPAIRED** | Live cache sha256 `66f30ea1…3d50` == pinned; `CLASSIFIER_VERSION 90a3b5ea…9e7a` present (52,450 rows, sole version); `sys.exit` on mismatch is in the code path |
| **DEF-M4** §0.5's account of D-INST does not match the instrument | PARTIAL | **NOT REPAIRED** → **V3-H6** | §0.5 still claims Stage 0 escalates *"all 397 distinct `SIMPLIFY_TIMEOUT` expressions"* versus D-INST's *"314 rows in the 73 affected stage-A worlds"*. Measured on the replay: the tool's `work` set is **396 pairs**, `indeterminate_world_count` **73**, `decisive_unresolved_count` **314**, and tier 2 escalates **only decisive pairs**. The claimed "one respect" widening is not in the tool |
| **DEF-M5** resource params "profiled" with no record | PARTIAL | **PARTIALLY REPAIRED; the ledger understates its own work** | `STAGE1_RESOURCE_PROFILE.json` **does exist** (12 searches, peak RSS 0.958 GiB, per-phase 2.0/19, 4.0/9, 23.5/1) — the ledger's *"No profiling record is produced"* is wrong in the protocol's disfavour. But §25.5 was never updated (V3-H2), and 12 searches is a thin basis for a frozen 57,960-search envelope |
| **DEF-M6** stale "S16 not yet performed" sentences | FIXED | **REPAIRED** | `grep` returns zero occurrences |
| **DEF-M7** Q1's twelve conditions cited from an eighteen-family source | FIXED | **REPAIRED** | Executed: derived `G2 = (F01..F05,F08..F12,F17,F18)` (12) and `NEG = (F07,F19)`, both matching `_EXPECTED_*`. Drift test: deleting F18 from `registry.CASE_FAMILIES` raises `AssertionError` at import. The assertion is live, not decorative |
| **DEF-M8** `recompute_stage` cannot return `E`, so UPPER is not an upper bound on `E` | DISCLOSED, interval "withdrawn" | **NOT REPAIRED — the interval is still printed and is still wrong** | §0.5 still quotes `A ∈ [49,122]`, `B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`. Measured extremes from the tool: LOWER `{A:122, B:196, C:102, E:119}`, UPPER `{A:49, B:267, C:104, E:119}`. `C+D` can never reach 99 and `E` can never exceed 119 |
| **DEF-M9** `C-6` mandatory but unsecured | FIXED | **REPAIRED** | §29 line 2307: `C-6` smoke-tested on a 5-expression sample in §12's hard preflight, before generation |
| **DEF-M10** §31.8 names a freeze record that does not exist | FIXED | **NOT REPAIRED** → **V3-M6** | Both records now exist and are tracked. But `DINST_FREEZE_SHA256_POSTREPAIR.txt` records `9826cefe…f4cb` for `scripts/e2a_instrument_diagnostic.py`, and the file at HEAD hashes to **`1f8d4b4a…78cc`**. §31.8 calls it *"recording the repaired tool's hash"*. Third consecutive stale D-INST freeze record |
| **DEF-L1** `Positive?` column conflates concluding with licensing | FIXED, "column split into `Concludes?` / `Licenses?`" | **NOT REPAIRED — the claim is false** | §32's header at line 2446 is `\| Terminal \| §22 rule \| Meaning \| Positive? \|`. `grep` for `Concludes?` and `Licenses?` returns zero hits |

**Score: 12 of 23 genuinely repaired** (`DEF-C1`, `C2`, `C3`, `H4`, `H5`, `H6`, `H7`, `M1`,
`M3`, `M6`, `M7`, `M9`), 1 acceptably disclosed with a residue (`M2`), **10 not repaired,
overstated, or newly broken**.

### Executor findings (`X-1`, `X-2`, `X-3`)

| id | claim | **Verdict** | Evidence |
|---|---|---|---|
| **X-1** | module ban → symbol ban + data-flow assertion | **NOT REPAIRED — REPRODUCED** → **V3-C3, V3-M7** | Transitive closure from `rc5_adapter`/`rc5_selection`/`rc5_estimate`: 14 muru modules, **7 `P8a` violations** — `g2_contract` binds `classify_support`, `classify_family_match`, `evaluate_g2_event`, `truth_support_for_case`, `TruthRecord`; `generator` and `truth` bind `TruthRecord`. The entry point *must* reach `g2_contract` for the permitted `extract_effective_support` |
| **X-2** | subsumed by DEF-H9's host rule | **NOT REPAIRED in the operative text** | `8 × 24 = 192 GiB` survives verbatim in §25.5 (V3-H2) |
| **X-3** | `e2c_classify.py` computes both properties unconditionally under a CPU budget | **NOT REPAIRED — the defect is reproduced in the repair module** → **V3-C4** | Two executed demonstrations below |

---

# PART 2 — REACHABILITY AUDIT (executed, not asserted)

Method: enumerate every attainable per-condition `(A,B,C+D,E)` with `A+B+C+D+E = 138`
(457,380 vectors — the only form §20 `P1` permits), cross `E6_SAFETY_HEADROOM_PRESENT ∈
{T,F}` and `reference_broken ∈ {T,F}`, evaluate §21.1 `ROUTING_CERTIFIED`, §21.3
`RETENTION_EXONERATED`, §21.2 Gate R, and §22 under `F0`. `pi = (1-S_1, S_1-S_2, S_2-S_3,
S_3)` inverts to `S_1 = (B+CD+E)/138`, `S_2 = (CD+E)/138`, `S_3 = E/138`. Both readings of
`F0` are run: **numerical** (`F12 < F12a < F12b < F13 < F14`) and **physical** (the table's
own layout, `F12, F12b, F13, F12a, F14`). `QUALIFIED = TRUE` throughout, since `F1`–`F7` are
reached only by a named clause failing.

| rule | terminal | witness (`A,B,C+D,E`; headroom; ref) | numerical | physical |
|---|---|---|---|---|
| F1 | `NO_ADMISSIBLE_SURFACE_WITHOUT_FREEZE_AMENDMENT` | `C-0 < 380/380` **and** owner refuses R-A. `C-0` is 380/380 in 5.0 s today, so this needs a generator regression | REACHABLE | REACHABLE |
| F2 | `BENCHMARK_INTEGRITY_DEFECT` | genuine ordinal/band/`pb_33` drift. **No longer unconditional** — `NO-BAND-COLLISION` verified `True` | REACHABLE | REACHABLE |
| **F2a** | `SURFACE_POPULATION_CONTAMINATED` | **REFUTED.** `P7` requires a `mass_power` world. Executed: the registry's `generative_kind` set contains no `power` variant at all, and §7 says `P7` holds *"by construction, not by exclusion"*. The rule can fire only on a code bug | **UNREACHABLE** | **UNREACHABLE** |
| F3 | `SURFACE_INCOMPLETE_COMPOSITION` | any cell ≠ 138 or world ≠ 30 seeds | REACHABLE | REACHABLE |
| F4 | `VOID_SCHEMA_INCOMPLETE` | any of the 28 §14 fields absent at seal | REACHABLE | REACHABLE |
| F5 | `VOID_CONTROL_FAILURE` | `C-6` with no second architecture; or `P8` — which **fails by construction today** (V3-C3), making this the guaranteed terminal until `P8a` is repaired | REACHABLE (and forced) | same |
| F6 | `VOID_INSTRUMENT_INDETERMINATE` | `INDETERMINATE_WORLDS > 0` after uncapped escalation. Note §25.4 has absolute precedence over it, and §22.2 concedes the Stage 0 analogue is unreachable for exactly that reason; the Stage 1 boundary is not analysed | REACHABLE, boundary undefined | same |
| F7 | `VOID_SINGLE_SHOT_BROKEN` | >1 surface or non-empty tuning ledger | REACHABLE | REACHABLE |
| F8 | `ROUTING_INDETERMINATE` | `(0,10,1,127)`; 307,924 witnesses. §32.2's `(40,45,48,5)` also verifies | REACHABLE | REACHABLE |
| F9 | `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` | `(0,0,0,138)`; 39,748 witnesses. §32.1's `W-EX (55,8,50,25)` verifies: `pi_B = 0.057971 < delta`, `S_2/S_1 = 0.9036` — **note this fails the new ratio conjunct `≥ 1 - delta = 0.930556`**, so `W-EX` no longer routes to `F9` under the `G3` repair and §32.1's own table is stale on it | REACHABLE | REACHABLE |
| F10 | `E4A_ENTRY_LICENCE_PROPOSED` | `(0,10,0,128)`; headroom `T`; 246,928 witnesses. `W-B (14,69,50,5)` verifies | REACHABLE | REACHABLE |
| F10a | `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` | same vector, headroom `F` | REACHABLE *iff* headroom is evaluable — **it is not** (V3-C5) | same |
| F11 | `E4_GENERATION_LICENCE_PROPOSED_F09_F10` | `(10,0,0,128)`; headroom `T`. `W-A (69,30,34,5)` verifies | REACHABLE | REACHABLE |
| F11a | `E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` | same vector, headroom `F` | REACHABLE *iff* headroom is evaluable | same |
| F12 | `E4F_LICENCE_PROPOSED` | `(0,0,10,128)`; headroom `T`. `W-CD (14,45,74,5)` verifies | REACHABLE | REACHABLE |
| **F12a** | `E4F_POPULATION_REFERENCE_BROKEN` | **REFUTED for its own use case.** `F12 ∪ F12b` exhausts `QUALIFIED ∧ row 3`. Under the table's layout `F12a` follows both ⟹ 0 witnesses. Under numerical order it fires only when headroom is **absent** — never in the DEF-H8 scenario | 123,464, headroom-**F** only | **UNREACHABLE** |
| F12b | `E4F_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` | `(0,0,10,128)`; headroom `F`; ref `F`. Under numerical order `F12a` pre-empts half its region | REACHABLE (halved) | REACHABLE |
| **F13** | `D3_ITEMS_UNMET_NO_REENTRY` | **REFUTED.** Re-run with **all eight D3 items unmet and ratification refused**: still **0 witnesses**, both orderings. Gate R rows 1–5 are exhaustive and `F8`–`F12b` cover them all | **UNREACHABLE** | **UNREACHABLE** |
| **F14** | `SURFACE_DEGENERATE_NO_FRONT` | **REFUTED.** `S_1 = 0 ⟺ (138,0,0,0) ⟺ pi = (1,0,0,0)`. Then `lead = 1 ≥ delta`, `Var = (1+0-1)/1656 = 0`, `LCB = 1 > 0`, argmax `A` ⟹ Gate R row 2 ⟹ **`F11` fires first**. 0 witnesses | **UNREACHABLE** | **UNREACHABLE** |
| F15 | `T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS` | owner judgement; no data path | REACHABLE (owner act) | same |
| S0a | `D-INST-DETERMINATE` | every decisive pair resolved under a hard-coded 24 GiB `RLIMIT_AS`. Two decisive sealed-`A` pairs already returned `MEMORY_SIMPLIFY` at 262.2 s and 446.2 s under 8 GiB; one E2a expression is measured at 44.4 GB. The ceiling is an in-process constant, so a larger host changes nothing (V3-H3) | **DOUBTFUL — and it is the only terminal that admits Stage 1** | — |
| S0b | `D-INST-INDETERMINATE` | **UNREACHABLE by construction**, conceded by §22.2 and asserted in the tool's own result object | UNREACHABLE (disclosed) | — |
| S0c | `D-INST-PLURALITY-NOT-INVARIANT` | still cap-invariant: my replay gives `PLURALITY_INVARIANT_lower = upper = true` from a run in which **nothing resolved** | UNREACHABLE | — |
| — | `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` | reached on the null replay. Absorbing for Stage 0 (V3-H3) | REACHABLE, no exit | — |

**Answers to the four questions put to me.**
1. *Does `E6_SAFETY_HEADROOM_PRESENT` make a licence terminal unreachable?* Not
   arithmetically — `wilson_upper_95(0,230) = 0.0164` and the ceiling breaks at `k ≥ 24` of
   230 — but **it makes all six of `F10/F10a/F11/F11a/F12/F12b` non-mechanically-decidable**,
   because the quantity has no definition, no measurement procedure, and no arm (V3-C5).
2. *Does `F0` starve a later rule?* **Yes — three of them:** `F13`, `F14`, and `F12a`.
3. *Is `F14` ordered so it can never fire?* **Yes.** Proven above and verified exhaustively.
4. *Does `G3`'s conjunction make `RETENTION_EXONERATED` unreachable or vacuous?* Neither — it
   is reachable with 39,748 witnesses and it is materially narrower, which is the right
   repair. **But it invalidates §32.1's own `W-EX` row**, which still claims `W-EX` routes to
   `F9` while `S_2/S_1 = 0.9036 < 0.930556`. The reachability table was not re-run after the
   predicate changed — the same omission, again.

---

# PART 3 — NEW DEFECTS

## V3-C1 — CRITICAL. `SURFACE_DEGENERATE_NO_FRONT` (F14) is unreachable, and the surface it was written for proposes an E4 generation licence instead.

**Location:** `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md:1919` (`F0`), `:1935` (`F11`),
`:1941` (`F14`), `:1716` (§21.3's routing of the degenerate path).

`S_1 = 0` means no world reached the front under either resolution. By §20's differencing,
`pi = (1 - S_1, S_1 - S_2, S_2 - S_3, S_3) = (1, 0, 0, 0)`. §21.1 then gives argmax `A`,
`lead = 1 - 0 = 1 ≥ delta`, `Var = (1 + 0 - 1^2)/1656 = 0`, `LCB = 1 > 0`, and argmax
invariance holds by `P6'`. `ROUTING_CERTIFIED` is **TRUE**. Gate R row 2 fires. `F11` is
numerically and physically before `F14`.

**Failure scenario.** The search produces 1,656 worlds in which not one of 49,680 seeds ever
places a G2-correct row on a Pareto front. Every control passes; the corpus is complete and
determinate; `QUALIFIED` holds. `false_structure_events = 0` on the NEG stratum trivially, so
`wilson_upper_95(0,230) = 0.0164 ≤ 0.15` and `E6_SAFETY_HEADROOM_PRESENT` is TRUE. The protocol
emits **`E4_GENERATION_LICENCE_PROPOSED_F09_F10`** — a positive terminal proposing E4
generation-side re-entry — from a surface that measured nothing at all. §21.3 wrote `F14`
precisely to stop this: *"The `S_1 > 0` guard is required so the branch cannot fire vacuously
on a surface that never reaches the front."* The guard works; the terminal it routes to cannot
be assigned.

**Minimal repair.** Move `F14` to fire immediately after `F7` and before `F8`, i.e. renumber it
`F7a`, and state that `S_1 = 0` is a surface-degeneracy condition evaluated before any routing
predicate. One line.

## V3-C2 — CRITICAL. `D3_ITEMS_UNMET_NO_REENTRY` (F13) is unreachable. A refused protocol-owner ratification cannot terminate the protocol.

**Location:** `:1919` (`F0`), `:1939` (`F13`), `:1611–1616` (Gate R rows 1–5), `:1826–1836`
(§21.5's mandatory ratification record).

Gate R's five rows are exhaustive by construction (the document says so at `:1607`). `F8`
takes row 5, `F9` row 4, `F10/F10a` row 1, `F11/F11a` row 2, `F12/F12b` row 3. Under `F0`'s
first-match-wins, **some rule in `F8..F12b` always fires**, so `F13` is dead. Verified by
enumerating all 457,380 vectors with `d3_ok = False`: **0 witnesses under both orderings.**

**Failure scenario.** The surface qualifies, route `C+D` certifies, and the protocol owner —
whose ratification §21.5 declares *"mandatory"* and without which *"nothing is licensed"* —
**refuses**. §22, "the sole terminal-assigning authority", assigns `E4F_LICENCE_PROPOSED`. The
published terminal of a run the owner has declined is a licence proposal. §32's gloss for
`D3_ITEMS_UNMET_NO_REENTRY` — *"No re-entry, regardless of the route"* — describes a state the
protocol cannot enter.

§22's own defence is that `F13`'s note says the D3 shortfall is *"reported against"* the named
route. That is a **rider**, not a terminal, and §22 lists it as a terminal in a set it declares
exhaustive and exclusive.

**Minimal repair.** Either (a) demote `F13` to a mandatory annotation on `F10..F12b` and delete
`D3_ITEMS_UNMET_NO_REENTRY` from §32 — the honest reading of the note; or (b) restore `F13`
ahead of `F8` so that an unmet D3 item pre-empts routing. (a) and (b) differ in substance; the
document must choose one and say which.

## V3-C3 — CRITICAL. `P8a` is unsatisfiable by construction. `X-1` is reproduced, not repaired, and `QUALIFIED` is again unreachable.

**Location:** `:1355–1364` (§16 `P8a`), `:1517` (§20 `P8 ∈ QUALIFIED`), `:1929` (`F5`);
`src/muru/paper_benchmark/g2_contract.py:29,173,189,357,402,427`.

`P8a`: *"No module reachable from the search entry point may bind any of `classify_support`,
`classify_family_match`, `evaluate_g2_event`, `truth_support_for_case`, … or any name from the
oracle or the truth registry."* §14 field 18 requires `effective_support`; §16 explicitly
**permits** `extract_effective_support`; that function is defined at `g2_contract.py:138`. Any
entry point that computes field 18 therefore reaches `g2_contract` — and `g2_contract` **binds
all four banned symbols** (it defines them) **and imports `TruthRecord`** at line 29.

**Executed** (transitive closure from `rc5_adapter`, `rc5_selection`, `rc5_estimate` — the four
functions §16 names as the entry point's building blocks):

```
REACHABLE MODULE CLOSURE (14) … P8a VIOLATIONS:
  muru.paper_benchmark.g2_contract   binds TruthRecord, classify_family_match,
                                     classify_support, evaluate_g2_event, truth_support_for_case
  muru.paper_benchmark.generator     binds TruthRecord
  muru.paper_benchmark.truth         binds TruthRecord
TOTAL: 7
```

Both readings of "bind" fail: `def` binds a name, and `from .truth import TruthRecord` binds an
imported one. `P8 ∈ QUALIFIED`, so `QUALIFIED = FALSE` deterministically, and §22 `F5` fires
`VOID_CONTROL_FAILURE` — this is `DEF-C1`'s failure mode with a different clause.

**Aggravating.** §12's execution-path row still reads *"`paper_benchmark/rc5_runner`, the real
v1 production path"* under the banner **"REUSED VERBATIM. Any deviation is a factor change
requiring its own arm."** §16 says the entry point is a separate module that *"never
import[s] `rc5_runner`"*. §12 was not updated, and **the separate module does not exist** — it
is in no manifest, no path, and no §31.1 freeze list, so `P8a` is not implementable today
even in principle.

**Minimal repair.** Scope `P8a` to the **call graph**, not the module closure: no function
reachable from the entry point's call graph may *invoke* a banned symbol, and no banned symbol
may appear as a call target in the entry point's own module. Then write the module, name it in
§12, and run the check.

## V3-C4 — CRITICAL. `e2c_classify.py` converts a resource-exhaustion event into a not-correct label, and its declared tier-1 CPU budget does not bound the dominant cost. `X-3` is reproduced inside the module written to repair it.

**Location:** `src/muru/v2_calibration/e2c_classify.py:118–126`;
`src/muru/paper_benchmark/g2_contract.py:163–166`.

`canonicalise()` computes `extract_effective_support` and `classify_discovered_family`
**before** entering `_cpu_budget`, each wrapped in a bare `except Exception`. But
`extract_effective_support` is **not** a cheap syntactic function — it calls `simplify(parsed)`
at `g2_contract.py:163`, inside `try: … except Exception: return None`. `MemoryError` and
`RecursionError` are `Exception` subclasses.

**Executed, two demonstrations:**

```
DEMO 1 -- MemoryError raised inside simplify (a simulated 44.4 GB canonicalisation):
  effective_support       : None       <-- NULLED by a RESOURCE event
  discovered_family       : None
  classify_support(None, truth) -> SupportStatus.SUPPORT_UNRESOLVED   -> g2_correct = False

DEMO 2 -- tier-1 budget = 1 s CPU, simplify burns 4 s CPU per call:
  elapsed wall            : 9.0 s   (budget was 1 s)
  cpu_seconds recorded    : 9.0
```

So (a) a memory envelope silently produces a not-correct label — the exact defect `D2` names,
that Gate 1 was convened over, and that §25's block-capital rule forbids *"anywhere in this
protocol, at any level"*; and (b) `FP-2`'s declared 60 s is not the operative bound — the two
unbudgeted calls run first and can each burn unbounded CPU.

**It also breaks two preconditions.** §25.3's canonicalisation table is keyed on
`(canonicalization_status, effective_support, discovered_family)`; two of those three are now
functions of the memory envelope, so the sealed table is not a function of the expression, and
§20 `P5 HOST_INVARIANT_LABELS` fails. §14 field 18 is persisted as `None` with no reason code,
indistinguishable from genuine unresolvability.

**Minimal repair.** Run `sympy.simplify(parsed)` **once**, outside `g2_contract`'s swallow and
inside `_cpu_budget`, with `MemoryError`/`RecursionError`/`_Cap` typed explicitly — exactly
what `e2a_instrument_diagnostic.py`'s `_PAYLOAD` already does correctly — then derive support
and family from the resolved form, and give `effective_support = None` its own
`support_status = UNRESOLVED_RESOURCE` reason code. Assert that no `CanonicalEntry` with a
resource reason ever reaches a label.

## V3-C5 — CRITICAL. `E6_SAFETY_HEADROOM_PRESENT` is a necessary condition of every licence terminal and has no mechanical evaluation. `DEF-H1` and `DEF-H2` are relocated, not repaired.

**Location:** `:1862` (§21.5 rider 1), `:1898` (the predicate), `:1933–1938` (`F10`–`F12b`),
`:1472` (§19 `D8`), `:1500–1519` (§20's precondition list), `:2239–2242` (§26(3)).

Four independent defects in one clause:

1. **§21.5 says it is *"evaluated in §20 with the other preconditions"*. It is not in §20.**
   §20's list is `P1..P10` and `QUALIFIED := Q1 ∧ C-0..C-6a ∧ P1..P10`. `grep`:
   `E6_SAFETY_HEADROOM_PRESENT` appears at `:1862`, `:1898` and in `F10/F10a/F11/F11a/F12/F12b`
   — never in §20. The `DEF-H1` repair's central claim is false against its own text.
2. **`false_structure_events` is defined nowhere.** One occurrence in 2,748 lines. The only
   related quantity is §19 `D8` `false_structure_rate`, and §19's header reads *"None may
   change any verdict."* `DEF-H1` is therefore not repaired; the diagnostic that could not
   change a verdict now decides six terminals.
3. **It is parameterised by an arm no route names.** *"for the arm named by the certified
   route"* — Gate R row 1 names **E4a** (five retention arms R0–R4), row 2 names **E3 cells**,
   row 3 names **E4f family i** (arms K1, K2). None is an arm. This is `DEF-H2`'s
   `<arm>` parameter, moved from a terminal *name* into a terminal *condition*, where it now
   decides between a licence and a no-headroom terminal rather than merely labelling one.
4. **Its denominator mixes DEV and EVAL.** §26(3) selects `R*`/`V*` on `DEV_ARM` and scores
   `EVAL_ARM` **once**. The 230 evaluable opportunities span both halves; the EVAL-only count
   is `69 + 23 + 23 = 115`, i.e. **1.15×** the frozen bar, not 2.30×.

**Failure scenario.** The surface qualifies and route `B` certifies. The adjudicator — who
under §29 *"applies the frozen §20/§21 predicates mechanically … may not modify any
predicate"* — must decide `F10` versus `F10a`. There is no predicate to apply: no numerator
definition, no arm, and a denominator that contradicts §26(3). The choice between
`E4A_ENTRY_LICENCE_PROPOSED` and `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` is analyst
discretion, exercised after the counts exist, on the licensing conjunction.

**Minimal repair.** Define `false_structure_events` as a §14-persisted, seal-time count on the
**`EVAL_ARM` NEG stratum** for the **control arm R0/V0** (which is what the calibration surface
actually runs — no E4 arm is executed by this protocol); republish the denominator as **115**
and the multiple as **1.15×**; and add `E6_SAFETY_HEADROOM_PRESENT` to §20's `P*` list as
`P11` with its own §22 rule, since that is what §21.5 already claims.

## V3-H1 — HIGH. `F12a` is unreachable, and `F0`'s "numerical order" is undefined over the lettered rules it governs.

**Location:** `:1919` (`F0`), `:1937–1940`.

The table's physical order is `F12, F12b, F13, F12a, F14`. `F0` mandates *"numerical order"*,
which for `F12a`/`F12b` is undefined and, on the natural reading (`12 < 12a < 12b`), disagrees
with the layout. Under the layout `F12a` has **0 witnesses**; under numerical order it has
123,464, **all with `E6_SAFETY_HEADROOM_PRESENT = False`**. The DEF-H8 scenario — route
certified, headroom present, a reader judges E4f's population-by-reference broken — yields
`E4F_LICENCE_PROPOSED` under both. §36 item 3 says the correct terminal there is
`E4F_POPULATION_REFERENCE_BROKEN`.

**Minimal repair.** Renumber every rule with a unique integer and state the order as a literal
list, not as an inferred property of the labels. Place `F12a` before `F12`.

## V3-H2 — HIGH. §25.5 is stale and contradicts §25.4, §34 and `STAGE1_RESOURCE_PROFILE.json`; the freeze manifest names the stale section.

**Location:** `:2205–2214` (§25.5) versus `:2140–2181` (§25.4's `DEF-H9` repair), `:2580–2583`
(§34 FP-3/FP-4, both of which say *"see §25.5"*), `:2222` (§26(1)), `:2394` (§31.1).

§25.5 still reads verbatim: *"Per-worker RSS ceiling `RSS_CEILING_GIB = 24`, enforced
in-process … frozen and load-isolated worker count `WORKER_COUNT = 8`. **Both numbers are
declared parameters (§34), profiled on the E2a engineering DEV set**"* — the in-process
constant `DEF-H9` condemned, the unsubstantiated "profiled" claim `DEF-M5` condemned, and the
`8 × 24 = 192 GiB` arithmetic on a 47 GiB host that `X-2` condemned, all three intact. §25.4
and `STAGE1_RESOURCE_PROFILE.json` declare 2.0/19, 4.0/9, 23.5/1 instead. §31.1 freezes *"the
§25.5 resource parameters"*; §26(1) hashes *"the §25.5 resource parameters"*; §34 points at
§25.5 for FP-3's and FP-4's values. **The manifest freezes the wrong numbers.**

**Minimal repair.** Delete §25.5's two constants and replace the paragraph with a pointer to
§25.4's table and `STAGE1_RESOURCE_PROFILE.json`.

## V3-H3 — HIGH. The Stage 0 instrument's memory ceiling is still an in-process constant, so `RUN_INCOMPLETE_RESOURCE_EXHAUSTION` remains absorbing and `D-INST-DETERMINATE` — the only terminal that admits Stage 1 — is gated on it.

**Location:** `scripts/e2a_instrument_diagnostic.py:76` (`ADDRESS_SPACE_BYTES = 24 * 1024**3`),
`:328–366` (terminal assignment); protocol `:2154–2160` (the host rule), `:2130–2136`
(§25.4 item 3's resume escape).

§25.4's repair makes the ceiling *"a declared FUNCTION OF THE HOST"*, evaluating to **23.5 GiB**
here. The instrument hard-codes **24 GiB** and reads no host property. So the resume escape is
still a no-op for Stage 0 — moving to a 2 TB host fires the same 24 GiB `RLIMIT_AS` — and
raising it is an `S0-2` ledger entry that voids the Stage 0 result. Both exits are still closed;
`DEF-H9` is repaired in the text and not in the code the text governs.

The terminal logic makes this decisive rather than academic. `resource_blocked =
decisive_unresolved`, and §25.4 has absolute precedence, so:

* any decisive pair unresolved ⟹ operational state, **no terminal, Stage 1 does not proceed**;
* `D-INST-DETERMINATE` requires **every** decisive pair resolved under 24 GiB.

**Measured evidence that this bites.** The archived 8 GiB run resolved 20 of 22 pairs and left
two `MEMORY_SIMPLIFY` after **262.2 s** and **446.2 s** of CPU, both on **sealed-stage-`A`**
worlds — and `recompute_stage` flips a sealed `A` on *any* correct row, retained or not, so
both are decisive. `DINST_HOSTILE_REVIEW.md:36–39` records one E2a expression at **44.4 GB RSS
after 95 s**; `POISON_WORLD_DETERMINATION.json` records 33.4–47.7 GB. A 24 GiB `RLIMIT_AS`
cannot resolve those. §35 nonetheless assigns Stage 0 a 65% pass.

**Minimal repair.** Compute `ADDRESS_SPACE_BYTES` in the instrument from
`os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')` by §25.4's frozen rule, record the
evaluated value in the result object, and state in §25.4 that the *rule* is frozen and the
*value* is not a ledger entry — which §25.4 already says and the code does not implement.

## V3-H4 — HIGH. §32 is not the terminal set. Six terminals are missing, two rule numbers collide, and the F10 terminal has three names.

**Location:** `:2417–2440` (§32's table), `:2496–2500` (§32.2), `:1925–1943` (§22.1).

§32 opens: *"The complete, mutually exclusive, exhaustive terminal set of Stage 1."* It omits
`SURFACE_POPULATION_CONTAMINATED` (F2a), `E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` (F10a),
`E4_GENERATION_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` (F11a), `E4F_POPULATION_REFERENCE_BROKEN`
(F12a), `E4F_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM` (F12b) and `SURFACE_DEGENERATE_NO_FRONT`
(F14) — **every terminal v3 added**. It assigns `T1_NO_ADMISSIBLE_QUALIFICATION_EXISTS` to
rule `F14`, which §22 gives to `SURFACE_DEGENERATE_NO_FRONT` (§22 numbers it `F15`). And it
names the F10 terminal **`E4A_LICENCE_PROPOSED_AT_<arm>`** — the exact string `DEF-H2`
condemned and the ledger records as renamed — while §22 says `E4A_ENTRY_LICENCE_PROPOSED` and
§32.1/§35 say `E4A_LICENCE_PROPOSED`.

§32.2 then asserts *"No terminal in §32 is unreachable, and no event maps to two terminals."*
Four of them are unreachable and the claim was never checked.

**Minimal repair.** Regenerate §32's table mechanically from §22 at freeze time and fail the
freeze on any mismatch of name, rule number or membership.

## V3-H5 — HIGH. The §32.1 witness verifier still does not exist, and §32.1 still asserts what it does not check.

**Location:** `:2394` (§31.1 lists *"the §32.1 witness verifier"* among artifacts to be
frozen), `:2470` (*"All four therefore satisfy every Gate Q clause by construction"*),
`:2338–2340` (§30 attack 3), `:2496` (§32.2).

`ls scripts/ | grep -i witness` returns nothing. The document again asserts the conjunction it
does not evaluate — the specific discipline failure that produced `DEF-C1`, that §30 attack 3
exists to catch, that my v2 review made item 1 of "what would change my verdict", and that
`V3_REPAIR_LEDGER` does not mention. It is also the direct cause of `V3-C1`, `V3-C2`, `V3-H1`
and `V3-M1`: a forty-line enumeration over 457,380 vectors found all four in one run.

§32.1's own table is now **stale on `W-EX`**: under the `G3` conjunction,
`S_2/S_1 = 50/(8+50+25) / … = 0.903614 < 1 - delta = 0.930556`, so `W-EX` fails
`RETENTION_EXONERATED` and routes to `F8` `ROUTING_INDETERMINATE`, not `F9`. The witness that
§32.1 exhibits for `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` no longer reaches it. (`F9` is
still reachable — `(0,0,0,138)` and 39,748 others — so the terminal survives; the *published
proof* does not.)

**Minimal repair.** Commit the script. Make it a freeze gate: enumerate every §22 rule over the
attainable simplex, refuse to freeze on any rule with zero witnesses, and re-verify every §32.1
row against the current §21.1/§21.3 predicates.

## V3-H6 — HIGH. §0.5's account of Stage 0 is still wrong against the instrument, and its determinacy interval is still wrong against the instrument's measured output.

**Location:** `:270–276` (the "one respect" widening), `:255–259` (the quoted interval);
`scripts/e2a_instrument_diagnostic.py:296–320` (`decisive_pairs`, tier-2 gating).

§0.5 claims Stage 0 is D-INST *"widened in exactly one respect"*: D-INST escalates *"the 314
timed-out rows inside the 73 affected stage-A worlds"*, Stage 0 escalates *"all 397 distinct
`SIMPLIFY_TIMEOUT` expressions"*. **Measured on the replay:** the tool's work set is **396
pairs**, `indeterminate_world_count` = **73**, `decisive_unresolved_count` = **314**, and tier
2 escalates *only* decisive pairs. The widening does not exist in the code. `DEF-M4`'s
disposition of PARTIAL is not supported.

The quoted interval is also still wrong, and now measurably so. §0.5 prints `A ∈ [49,122]`,
`B ∈ [196,267]`, `C+D ∈ [99,104]`, `E ∈ [119,124]`. The tool's extremes, under the
maximal-uncertainty input (all 396 `UNRESOLVED`), are `LOWER {A:122, B:196, C:102, E:119}` and
`UPPER {A:49, B:267, C:104, E:119}`. **`C+D` can never reach 99 and `E` can never leave 119** —
the latter is `DEF-M8` itself (`recompute_stage` never returns `E`). The ledger says the
interval is *"withdrawn rather than recomputed"*; it is neither.

**Minimal repair.** Delete the "one respect" sentence or implement the widening; replace the
interval with the two counters the tool emits, or delete it.

---

## MED

| id | defect | location | note |
|---|---|---|---|
| **V3-M1** | `F2a SURFACE_POPULATION_CONTAMINATED` is unreachable by construction and this is not disclosed | `:1925`, §7 `:905` | Executed: the registry declares 24 `generative_kind`s, **none containing `power`**; §7 says `P7` holds *"by construction, not by exclusion"*. `F2a` can fire only on a code bug. This is the `g_max`/`D5` defect class — a vacuous rule presented as a live check — reintroduced by the `DEF-H3` repair, in the same document that struck the identical assertion from §21.1. **Repair:** label `F2a` a bug-detector, as §21.1 now labels its own vacuous clauses |
| **V3-M2** | E6's 230-opportunity denominator spans `DEV_ARM` and `EVAL_ARM` | `:1893`, §26(3) `:2239` | `EVAL_ARM` alone holds `69` F07 + `23` F19A + `23` F19B = **115** evaluable opportunities, i.e. **1.15×** the frozen `≥ 100` bar, not 2.30×. §26(3) says *"EVAL is scored exactly once"* and arms are **selected** on DEV. Using DEV opportunities in a safety denominator scores the half the arm was fitted on. **Repair:** publish 115 and 1.15×, or state explicitly that the ceiling is evaluated on the pooled stratum and why that is admissible |
| **V3-M3** | §12 and §16 mandate incompatible search entry points, and neither module exists | `:1194` vs `:1372–1379` | §12: *"`paper_benchmark/rc5_runner`, the real v1 production path"* under *"REUSED VERBATIM. Any deviation is a factor change requiring its own arm."* §16: the entry point *"never import[s] `rc5_runner`"*. No such module is in the repository or in §31.1's manifest |
| **V3-M4** | §35 assigns 35% to a terminal §22.2 proves unreachable, and its probabilities sum to 100% over a terminal set missing six members | `:2608–2626` | *"I judge `D-INST-INDETERMINATE` (~35%) the main risk"* versus §22.2: *"unreachable by construction"*. The Stage 1 table (50+18+10+5+4+8+5 = 100) implicitly assigns 0% to `F2a`, `F10a`, `F11a`, `F12a`, `F12b`, `F14`. §35 itself criticises v1 for predicting *"a state §0.4 shows to be impossible"* |
| **V3-M5** | two incompatible frozen search costs | §10.6 `:1141–1145` vs `STAGE1_RESOURCE_PROFILE.json` | §10.6: 3.86 s/search ⟹ **62.7 CPU-hours**, quoted throughout. The frozen profile (cited by §25.4 and FP-3/FP-4): 5.1 s/search ⟹ **82.1 CPU-hours**. A 31% divergence between two numbers both declared frozen before Stage 0 |
| **V3-M6** | §31.8's superseding D-INST freeze record is already stale at HEAD | `:2419–2424` | `DINST_FREEZE_SHA256_POSTREPAIR.txt` records `9826cefe…f4cb`; `sha256sum scripts/e2a_instrument_diagnostic.py` = **`1f8d4b4a…78cc`**. §31.8 calls it *"recording the repaired tool's hash"*. Third consecutive stale record for the same file, and the failure mode `DEF-M10` was raised about |
| **V3-M7** | `P8b`'s data-flow assertion cannot detect the leak it is written for | `:1363`; `rc5_adapter.py:129–137,174` | *"No field of `TruthRecord` may be reachable from the object graph of `CaseDesign`."* `CaseDesign` is a frozen dataclass of `tuple[str,...]` and `np.ndarray`; `target = np.asarray(scalars.g, dtype=np.float64)` is a **value copy**. `g = truth.g_by_compound[c]` would copy floats and leave no `TruthRecord` field in the graph. Reference reachability is not taint. **Repair:** assert `scalars is estimate_case_scalars(...)`'s output and hash-compare `target` against the estimated vector, or drop the claim that `P8b` catches this |
| **V3-M8** | `pi_E` never enters the certification argmax, so a near-perfect surface proposes a re-entry licence | `:1563–1567` | Witness `(0,10,0,128)`: `pi = (0, 0.0725, 0, 0.9275)` — 92.75% outright success — certifies route `B` with `lead = 0.0725 ≥ delta` and `LCB = +0.060`. No clause requires the loss being attributed to be material in absolute terms. This is `DEF-M2` in a form the §10.4 disclosure does not cover. **Repair:** add `1 - pi_E ≥ some frozen share` to Gate R, or state that certification is explicitly conditional on loss existing |
| **V3-M9** | the operational branch still publishes routing quantities from a run that computed nothing | `e2a_instrument_diagnostic.py:346–370,441` | §25.4 item 1: *"No seal is written. No routing verdict is computed."* Executed on the 396-null replay, `DINST_RESULT.json` was written carrying `corrected_counts_UPPER_unresolved_as_correct {A:49, B:267, C:104, E:119}`, `PLURALITY_INVARIANT_lower: true`, `PLURALITY_INVARIANT_upper: true` and `worlds_whose_stage_MOVED_at_LOWER: 0` — Gate 2's routing predicate, published `true` from 396/396 environment failures. The `G1` defect survives in the diagnostics after being removed from the terminal |

## LOW

| id | defect | location | note |
|---|---|---|---|
| **V3-L1** | §32's `Positive?` column was never split; the ledger's `G17`/`DEF-L1` FIXED is false | `:2446` | Header is `\| Terminal \| §22 rule \| Meaning \| Positive? \|`. `grep` for `Concludes?` / `Licenses?`: zero hits. `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE` is still marked `**Yes**` though it licenses nothing — the original defect, unchanged |

---

# PART 4 — PRIORITY-4 ITEMS (DISCLOSED / PARTIAL) — accept or repair?

| id | disposition | **My judgement** |
|---|---|---|
| **DEF-M2** | DISCLOSED | **ACCEPTABLE as far as it goes.** The observed-vs-true-lead gap is conservative for a licensing instrument and §10.4 now states it. **But the disclosure is incomplete**: V3-M8 shows the predicate also never checks that loss exists. Add one sentence or one clause |
| **DEF-M4** | PARTIAL | **NOT ACCEPTABLE — repair required.** §0.5 makes two factual claims about the instrument that are false against the instrument (V3-H6), on the gate that admits Stage 1. Superseding a narrative by two other sections is fine; leaving a false description of the tool in the section that defines Stage 0's scope is not. Cost: delete two sentences |
| **DEF-M5** | PARTIAL | **NOT ACCEPTABLE as stated — but nearly repaired.** The profiling record now exists and the ledger understates it. What is unacceptable is that §25.5, which every freeze and manifest clause names, still carries the superseded values (V3-H2). Cost: delete one paragraph |
| **DEF-M8** | DISCLOSED | **NOT ACCEPTABLE.** "Disclosed" would mean the wrong interval is gone. It is still printed in §0.5 and is now measurably impossible in two of four cells (V3-H6). Withdraw it or recompute it; either is a one-line edit |
| **G12** (control selection rules undeclared) | DISCLOSED | **ACCEPTABLE, with one exception.** Naming the residual freedom is the right move for `C-2`/`C-3`/`C-5`. **`C-4` is different**: it is a 101-row *"pre-declared sample"* re-scored uncapped at a 100% bar, and *which* 101 rows decides whether the control has any power — a sample drawn from cheap expressions passes trivially. Require `C-4` to be the 101 most expensive rows by tier-1 CPU, which is mechanical and needs no new magnitude |
| **G13** (exoneration branch reordered against `f4c1105`) | DISCLOSED | **ACCEPTABLE.** The reorder is disclosed, its licence-expanding direction is stated, §21.3 proves it is operationally vacuous on route `B` by arithmetic (`pi_B ≥ delta` under certification), and the `G3` conjunction materially narrows the branch. This is the standard I want the rest of the document held to |

---

# PART 5 — WHAT WOULD CHANGE MY VERDICT

Nothing below requires a new experiment, a new magnitude, or relitigating Decision 1 or 2.

1. **Write and commit the §32.1 witness verifier, and make it a freeze gate.** Enumerate the
   attainable simplex through §20/§21/§22; refuse to freeze if any §22 rule has zero witnesses,
   if any §32.1 row no longer routes where the table says, or if §32's terminal names and rule
   numbers do not regenerate from §22. **Every one of `V3-C1`, `V3-C2`, `V3-H1`, `V3-H4`,
   `V3-H5` and `V3-M1` is found by running it once.** This is the third review in which the
   licensing conjunction has not been evaluated mechanically. It is the whole finding.
2. **Fix the four unreachable terminals.** Move `F14` before `F8`; decide whether `F13` is a
   terminal or a rider and make §22 and §32 agree; move `F12a` before `F12`; label `F2a` a
   bug-detector. Renumber every rule with a unique integer.
3. **Make `E6_SAFETY_HEADROOM_PRESENT` mechanical or delete it** (`V3-C5`): define
   `false_structure_events` on a §14-persisted field, name the arm, put it in §20's `P*` list
   as §21.5 already claims, and republish the denominator against §26(3) — 115, or a stated
   reason why 230 is admissible.
4. **Repair `P8a` at the call-graph level and write the entry-point module** (`V3-C3`), then
   run the check and commit its output. Update §12 so it does not mandate the module §16
   forbids.
5. **Repair `e2c_classify.py`** (`V3-C4`): one `simplify` call, inside the budget, outside the
   swallow, with typed resource exceptions and a reason code on `effective_support = None`.
   Add a test that injects `MemoryError` and asserts no label is produced.
6. **Make §25.5 consistent with §25.4**, and compute the Stage 0 ceiling from the host in the
   instrument (`V3-H2`, `V3-H3`). Then re-price §35's Stage 0 65% against the two measured
   `MEMORY_SIMPLIFY` pairs and the 44.4 GB record.
7. **Housekeeping that costs nothing:** one name for the F10 terminal; §32 regenerated from
   §22; the `Positive?` column split as the ledger already claims; the §0.5 interval and the
   "one respect" sentence deleted; §10.6 reconciled with the frozen profile; the D-INST freeze
   record re-hashed; §32.1's `W-EX` row recomputed under the `G3` conjunction.

**What would *not* change my verdict.** An argument that `F13`, `F14`, `F12a` and `F2a` are
"defence in depth" or "cannot arise in practice". `F14` was written *specifically* for a case
§21.3 argues is the expected regime (*"E3's MARGINAL verdicts make low `S_1` the **expected**
regime, not a corner case"*), and its unreachability converts that case into a licence. `F13`
was written for a protocol owner exercising the veto §21.5 calls mandatory. A terminal set
declared *"mutually exclusive and jointly exhaustive by construction"* in which four members
cannot be constructed is not exhaustive; it is four names.

**What earned real credit.** `DEF-C1` is repaired and I could not break the repair.
`NO-BAND-COLLISION` is strictly stronger than v2 intended and I verified all three conjuncts.
The instrument regression is genuine: the same 396 records that produced a benign terminal now
produce none. The `DEF-M7` derivation is not decoration — the assertion fires when I perturb
the registry. `N = 230` and `46/46/46` are exact. §0.7's admission of the executor's own
pre-freeze inspection is the single best paragraph in this programme, and the graded
dispositions in `V3_REPAIR_LEDGER` are how a ledger should read. The document is better than
v2 by a wide margin and it is still not freezable.

---

**REVIEWER'S NOTE ON SCOPE.** I took Gate 1 = FAIL, E2b's decision-inadmissibility, the
cap-invariance of E2a's B-plurality, and Decisions 1 and 2 as fixed and did not relitigate
them. This review performed **no scientific compute**: read-only imports, the `C-0` equivalence
control (5.0 s, no world generated), closed-form arithmetic, injected-fault unit tests on
`e2c_classify`, and one `--analyze-only` replay of already-quarantined `EXPLANATORY_ONLY`
records. The replay's transient artifacts (`_ckpt_dinst/*.json`, `DINST_RESULT.json`) were
removed and `git status` restored to its pre-review state. No file outside
`CRITIC_SCIENCE_V3_REVIEW.md` was created or modified, and nothing was committed.
