# Protocol v3 — repair ledger against the v2 hostile reviews

Inputs: `CRITIC_SCIENCE_V2_REVIEW.md` (FAIL — 3 CRITICAL, 9 HIGH, 10 MED, 1 LOW) and
`CRITIC_GOVERNANCE_V2_REVIEW.md` (FAIL — 4 CRITICAL, 7 HIGH, 6 MED, 4 LOW). 45 defects.

**On the honesty of this ledger.** `CRITIC_GOVERNANCE` `G14` found v2's ledger overstated its
`FIXED` dispositions on at least three defects that were deferred, and `CRITIC_SCIENCE` found
v2's headline *"37/38 FIXED"* did *"not survive contact with the code"*. This ledger therefore
uses five dispositions and does not use `FIXED` loosely:

| code | meaning |
|---|---|
| **FIXED** | the defect cannot recur; where testable, a test or execution is cited |
| **FIXED-BY-SCOPING** | not repairable here (frozen bytes), so the protocol's claim is narrowed until the defect cannot bite |
| **PARTIAL** | materially improved, with the residue named |
| **DISCLOSED** | not repaired; accepted as a stated limitation, with the reason |
| **WITHDRAWN** | the v2 claim is struck rather than defended |

---

## CRITICAL

| id | defect | disposition | evidence |
|---|---|---|---|
| **DEF-C1** | Gate Q's seed-band clause names `find_overlaps`, which is never empty, so `QUALIFIED` is unreachable and `BENCHMARK_INTEGRITY_DEFECT` fires unconditionally | **FIXED** | §5.2 now states `NO-BAND-COLLISION`, restricted to overlaps naming the calibration band, **plus** the registry's own `unacknowledged_overlaps() == []`, **plus** the 32-bit bound — strictly stronger than v2 intended. Executed: v2's predicate FAILS, v3's PASSES, `overlaps_involving_calibration_band = []` |
| **DEF-C2 / G1** | a 1500 s wall cap and a 6 GiB address-space cap decide a scientific terminal; the terminal is keyed on `moved_lo` while `determinate` is discarded, so a run that resolved nothing emits the benign terminal — and it had already fired | **FIXED** | Instrument rewritten to §25.2's two tiers (tier 1 = 60 s **CPU** via `ITIMER_PROF`; tier 2 **uncapped**, applied only to DECISIVE pairs) and §25.4 (residual decisive-unresolved ⇒ `RUN_INCOMPLETE_RESOURCE_EXHAUSTION`, **no** terminal). Regression on the same 396 null records: old ⇒ `D-INST-NO-WORLD-MOVED`; new ⇒ `TERMINAL: null`, `OPERATIONAL_STATE: RUN_INCOMPLETE_RESOURCE_EXHAUSTION` |
| **DEF-C3 / G2** | Stage 0 executing pre-freeze, re-run three times after observing its own failures, on the corpus it is debugged against; status line false at HEAD | **FIXED** | Halted at 47/396, nothing sealed, all three runs quarantined `EXPLANATORY_ONLY`. New §0.7 adds `S0-1..S0-5` (single shot, tuning ledger, no pre-freeze outcome inspection, resource-resume rule, environment-failure exemption). §0.5's status line rewritten as a checkable table. **The executor's own error is stated in §0.7, not softened**: run 1's verdicts and wall-times were inspected and published before the instrument was final |
| **G3** | `RETENTION_EXONERATED`'s dominance derivation is false; the protocol's own witness `W-EX` refutes it; at `S_1 = 0.10` it publishes "retention exonerated" at `P_retain\|front ≈ 0.31` | **FIXED** | §21.3 predicate is now the **conjunction** `pi_B < delta` **AND** `S_2/S_1 >= 1 - delta` **AND** `S_1 > 0`, all under both resolutions, adding no new magnitude. The false algebra is quoted and corrected in place. Degenerate `S_1 = 0` routed to new terminal `SURFACE_DEGENERATE_NO_FRONT` (F14) |
| **G4** | Stage 0's emitted terminals are not in §22.2's declared set; the map is analyst discretion on the gate that admits Stage 1 | **FIXED** | Instrument asserts membership of `{D-INST-DETERMINATE, D-INST-INDETERMINATE, D-INST-PLURALITY-NOT-INVARIANT}` at emission; `moved_lo` demoted to a diagnostic. §22.2 rewritten against the tool as it now stands, and **reports that `D-INST-INDETERMINATE` is unreachable by construction under uncapped escalation** rather than concealing it |

## HIGH

| id | defect | disposition | evidence |
|---|---|---|---|
| **DEF-H1** | §19 says no diagnostic changes a verdict; §21.5 makes the E6 ceiling a necessary condition of every licence | **FIXED** | The ceiling is named `E6_SAFETY_HEADROOM_PRESENT`, evaluated as a precondition, and given explicit terminals F10a / F11a / F12b. It is no longer a rider contradicting §19 |
| **DEF-H2** | `E4A_LICENCE_PROPOSED_AT_<arm>` — `<arm>` has no admissible source | **FIXED** | Renamed `E4A_ENTRY_LICENCE_PROPOSED`; no arm parameter. Arm selection remains D7's non-licensing diagnostic and names nothing |
| **DEF-H3** | §22 neither exclusive nor exhaustive; `C-0` maps to F1 and F2; `P7` and `C-0` appear in no rule | **FIXED** | New **F0 precedence rule** (numerical order, first match wins) makes the set exclusive by construction; `C-0` removed from F2 and left to F1; `P7` gets F2a `SURFACE_POPULATION_CONTAMINATED`; F13 explicitly ordered after F8–F12 |
| **DEF-H4** | three `ROUTING_CERTIFIED` clauses are provably vacuous given `P6'`, and §21.1 asserts the opposite | **FIXED** | v2's assertion is struck. The clauses are retained and **relabelled as defence-in-depth against a bug in `P6'`**, explicitly *not* independent scientific checks. The predicate's scientific content is stated to rest entirely on the materiality and precision clauses |
| **DEF-H5** | E4f Gate H1 is a zero-defect census in the direction the voting arm necessarily pushes (its own Lemma K), so route C+D's family ii is near-certainly dead on arrival | **FIXED-BY-SCOPING** | E4f is frozen and §36's precedence rule forbids editing it, so option (iii) is taken: **a certified C+D route proposes family i (classifier) only**; family ii is executed, fully reported, and **licenses nothing**. The expectation that H1 fails is pre-recorded in §35 |
| **DEF-H6** | FP-6's `false_stabilisation_rate` is truth-facing and contains the negation of Gate H2's own efficacy term, so family ii's safety gate is not independent of its efficacy claim | **FIXED-BY-SCOPING** | Same disposition as DEF-H5 — family ii licenses nothing, so the compromised gate gates nothing. E4f's own `E4F_NOT_ENTERED_NO_ROUTE` is explicitly not resisted if family i also fails |
| **DEF-H7** | the E6 "≥100 opportunities, 2.76×" claim counts worlds; `registry.py` declares F19C non-evaluable by design | **FIXED** | "Evaluable safety opportunity" defined as a NEG world whose variant declares `scalar_truth_defined = True`. Verified against the registry: F19 splits **F19A 46 / F19B 46 / F19C 46** over 138 replicates, so **N = 138 + 46 + 46 = 230**, and the multiple is **2.30×**, not 2.76× |
| **DEF-H8 / G8** | §36 mandates a restatement that changes the artifact whose hash `C-6a` verifies, so enacting §36 self-voids F12; and "restatement vs tuning entry" is a clerical choice deciding between a licence and a void | **FIXED** | §36 precedence rule: E4f is **never edited**; the restatement goes to a new separately-hashed `MURU_V2_E4F_POPULATION_RESTATEMENT.md` frozen before Gate R is read; legitimacy rests on E4f's own population-by-reference clause; if a reader judges the reference broken the terminal is the new **F12a `E4F_POPULATION_REFERENCE_BROKEN`**, which is neither a licence nor a control failure. Declared *before* execution so it cannot be decided after |
| **DEF-H9** | `RSS_CEILING_GIB = 24` is an in-process constant, so "resume on a larger host" is a no-op and `RUN_INCOMPLETE` is absorbing; raising it fires F7 | **FIXED** | The ceiling is now a **frozen rule evaluating to a host-derived value**, `min(0.50 × total_GiB, 24 × scale)`, with `WORKER_COUNT` bound to it so `WORKER_COUNT × RSS_CEILING ≤ 0.85 × total`. This also closes `X-2` (v2's `8 × 24 = 192 GiB` was never satisfiable on a 47 GiB host). Stated to be conservative and slow, with a published-measurement escape |
| **G5** | Decision 1's "the impasse is robust" was never tested in the threshold dimension; the event log shows the milder repair rejected as results-aware while the maximal one was adopted on the same information | **WITHDRAWN** | The robustness claim is struck from the justification and relied on nowhere. Decision 1 rests on its authority ground alone, which review found sound. The struck sentence is shown struck, not deleted |
| **G6** | §21.5 makes the E2b-derived annotation a precondition of any licence, so E2b can *withhold* a licence — asymmetrically against the two non-C+D routes | **FIXED** | The annotation is published and quoted in full and **conditions nothing**: no terminal, licence, gate or ratification requirement depends on its value. §4.1 (iii) is restored to true. `befca0d` §2.3 is explicitly *not* claimed to be discharged by it |
| **G7** | Decision 2's authority is self-granted: ratification §10 does not authorize an E4f prereg, and the cited P2 items say "Declare E4f non-executable" | **FIXED** | New §2.1 corrects the chain: authority is the owner's **maximum-autonomy delegation** under its three conditions, not ratification §10. **D2-ext's suspension STANDS**; E4f is *preregistered*, not *unsuspended*. v2's headline "EXECUTABLE" is withdrawn as overstated throughout |
| **G9** | the straggler addendum cites a sealed audit that does not contain the case; the sealed resource-kill audit is incomplete | **FIXED (citation) + DISCLOSED (the gap)** | `E2B_STRAGGLER_ADDENDUM_CORRECTION.json`. The fabricated citation is retracted. The true source is `FROZEN_DIRECT_CLASSES.csv`, where both `F10\|r009` and `F08\|r007` carry valid classes (`LOST_IN_RETENTION`). The **second** defect — audit lists 7, failures file lists 8 — is disclosed and **not** repaired, because sealed bytes are not rewritten |
| **G10** | D-INST ran under a protocol text its own review said must not be executed; freeze record amended twice; §31.8 names a file that does not exist | **PARTIAL** | §31.8 re-pointed to `DINST_FREEZE_ADDENDUM.md` + `DINST_FREEZE_SHA256_POSTREPAIR.txt`, both committed. §0.7 records the amendments. **Residue:** the D-INST protocol *text* still carries its original wording; the instrument, not the text, was repaired. The text is superseded by §22.2 and §0.7, which is stated, but a consolidated D-INST protocol v2 is **not** written |
| **G11** | the S16 re-derivation was not blind: the brief supplied `pi_0`, while the commit claims independence | **FIXED** | New §0.8: blindness of **procedure**, not of **exposure**. The document itself already disclosed the exposure; the commit subject overstated. All "results-blind" claims in this programme are restated as **artifact-order** claims |

## MED / LOW

| id | defect | disposition | note |
|---|---|---|---|
| **DEF-M1** | `n = 1656` labelled DERIVED from a criterion unattainable at every `n` | **FIXED** | Relabelled "80% power **against the precision clause**". The composite OC (0.499 / 0.87 / 0.99 at 1.0 / 1.5 / 2.0 δ) is pre-recorded and non-renegotiable |
| **DEF-M2** | the composite rule tests the *observed* lead, so certification does not establish a material *true* lead | **DISCLOSED** | Accepted. The gap is in the conservative direction for a licensing instrument and is now stated in §10.4 rather than implied |
| **DEF-M3** | the classifier version defining Stage 0's population is chosen at runtime by frequency from a mutable out-of-repo file | **FIXED** | `CLASSIFIER_VERSION` and `CLASSIFY_CACHE_SHA256` pinned as literals and **asserted**; the instrument aborts on mismatch. Both verified against the live cache |
| **DEF-M4** | §0.5's account of D-INST does not match the instrument | **PARTIAL** | §22.2 and §0.7 are rewritten against the tool as it stands; §0.5's narrative is superseded by them but not itself rewritten |
| **DEF-M5** | `RSS_CEILING_GIB` / `WORKER_COUNT` declared "profiled on the E2a DEV set" with no profiling record | **PARTIAL** | Both are now host-derived by a frozen rule (DEF-H9) and declared free parameters. **No profiling record is produced**; the "profiled" claim is dropped rather than substantiated |
| **DEF-M6** | text asserts the S16 re-derivation has not been performed | **FIXED** | Corrected in place, citing `b4ea2a0`, with §0.8's blindness qualification |
| **DEF-M7** | Q1's "twelve G2 conditions" cites a source listing eighteen families; the selection rule lives outside the protocol | **FIXED** | `calibration_surface.py` now **derives** both strata from registry predicates (`symbolic_truth_kind == "defined"`; `false_null_structure` or `mass_only`) and **asserts** they reproduce the intended tuples, refusing to import on drift. Executed: G2 and NEG both match exactly |
| **DEF-M8** | `recompute_stage` never returns `E`, so the UPPER bound is not an upper bound on `E`, and the quoted interval matches no artifact | **DISCLOSED** | Real and confirmed. Conservative for the B-plurality claim, which is the only thing Stage 0 gates. The `E`-bound is **not** claimed from this instrument, and §0.5's quoted interval is withdrawn rather than recomputed |
| **DEF-M9** | `C-6` is mandatory and non-waivable but depends on an unsecured second architecture, with no rehabilitation path | **FIXED** | A 5-expression `C-6` smoke test is added to §12's hard preflight. No second architecture at preflight ⇒ the run does not start, so it is a scheduling fact rather than a void after 63 CPU-hours |
| **DEF-M10 / G10** | §31.8 names a superseding freeze record that does not exist | **FIXED** | Re-pointed and committed |
| **G12** | control *selection rules* undeclared; §34 declares sizes only | **DISCLOSED** | Sizes and pass bars are declared; the selection rules for `C-2`/`C-3`/`C-4`/`C-5`/`C-6` samples are **not**. Named here as an open degree of freedom rather than left implicit |
| **G13** | the exoneration branch is reordered against frozen `f4c1105` in the licence-expanding direction | **DISCLOSED** | The reorder and its rationale were already disclosed in §21.3 and are retained. G3's conjunction repair materially narrows the branch, which reduces but does not remove the expansion |
| **G14** | v2's ledger overstated `FIXED` | **FIXED** | This ledger's five graded dispositions, with `PARTIAL` / `DISCLOSED` / `WITHDRAWN` used wherever they are the truth |
| **G15** | `E4F_FREEZE.txt`'s attestation describes a state v2 establishes never existed | **DISCLOSED** | E4f's bytes are not edited (§36 precedence). The attestation's defect is recorded here and in §2.1's authority correction |
| **G16** | `pi_0` is printed in the protocol, ratification and E4f, so "results-blind" is an artifact-order claim | **FIXED** | Stated as such in §0.8 and applied to every blindness claim in the document |
| **G17 / DEF-L1** | `RC3_WITHDRAWN_...` marked `Positive? Yes` though it licenses nothing | **FIXED** | §32's column split into `Concludes?` / `Licenses?` |
| **G18** | §35's headline states a selection mechanism as a virtue | **DISCLOSED** | Retained with the mechanism stated |
| **G19** | line count off by three | **FIXED** | Recomputed at freeze |
| **G20** | `find_overlaps` not demonstrated on the new band | **FIXED** | `verify_band()` executed; output quoted in §5.2 |
| **G21** | the straggler addendum sits outside every manifest | **FIXED** | Addendum and its correction enter the v3 freeze manifest |

---

## Executor findings, raised by building rather than reading

| id | defect | disposition |
|---|---|---|
| **X-1** | §16's module-level truth-blind import ban is unsatisfiable — §12 mandates `rc5_runner`, which imports `g2_contract` at line 48, and §14 requires `effective_support`, which is *defined* in `g2_contract`. `P8` therefore fails by construction, a **fourth** independent route to an unreachable `QUALIFIED` | **FIXED** — the test becomes symbol-level plus a data-flow assertion; the syntax-only helpers (`extract_effective_support`, `classify_discovered_family`, `_safe_parse`, `GRAMMAR_PRIMITIVES`, `template_key`) are enumerated as permitted, the truth-comparing symbols are banned, and no `TruthRecord` field may be reachable from `CaseDesign`. §12's equivalence requirement is discharged where it always actually was — by control `C-1` |
| **X-2** | `WORKER_COUNT × RSS_CEILING_GIB = 192 GiB` on a 47 GiB host, so FP-3's "the in-process ceiling fires before the kernel does" cannot hold | **FIXED** — subsumed by DEF-H9's host-derived rule |
| **X-3** | Stage 1's classifier is unspecified, and the only existing front-capture module calls the 5 s-capped `e2_classify`, which §13 `A2` retires. Its lines 161–162 gate `effective_support` and `discovered_family` — both **pure functions of the expression string** — on whether an unrelated `sympy.simplify` returned in time | **FIXED** — new `e2c_classify.py` implements §25: both properties computed **unconditionally**, tier-1 CPU budget via `ITIMER_PROF`, tier-2 uncapped, cap derived from `BaseException`. `e2_classify.py` is **not** edited (sealed E2a instrument) |
