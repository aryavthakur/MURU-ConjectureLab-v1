# MURU RC5 — post-A3.5-freeze reconciliation

**Document ID:** `MURU-AUDIT-RC5-POST-A3-5-FREEZE-RECONCILIATION-01`
**Classification:** `PRE_BUILD_AUTHORITY_RECONCILIATION`
**Status:** `RECONCILED — RC5 IMPLEMENTATION AUTHORIZED`

**Purpose.** `audit/MURU_RC5_FINAL_PREBUILD_MAP.md` (`7452f32`, blob
`dcda291727c147d3e45ff851a0cc50f1865d5c82`) was authored *before* A3.5 froze. Its
implementation map (D1–D14) is still accurate as engineering forensics, but its
**authority classifications are stale**: it labels every item
`A3.5_BOUND_NOT_TAGGED` or `A3.5_RECOMMENDATION_NOT_YET_BOUND`, and it says of D1–D4
"**Do not build.**" A3.5 has since frozen. This document reclassifies every D-item against
the *final frozen amendment text*, and records where the frozen text differs from the map.

**No new scientific rule is created by this document.** Where the frozen A3.5 text and the
prebuild map differ, the frozen text wins and the difference is recorded in §3.

---

## 0. Verified authorities

Every object below was verified in this repository with `git rev-parse` / `git cat-file`,
not accepted from a summary.

| Object | Type | SHA | Verified |
|---|---|---|---|
| `benchmark-content-freeze-a3-5` | annotated tag object | `533777b73748e3c45dd1ecbda07098ba9837c587` | `git cat-file -t` → `tag` |
| its target commit | commit | `560bf28568e2762c60edc994aac7f2b6de14081f` | `git rev-parse <tag>^{commit}` |
| `engineering-rc4-2-1-integrity-closure` | annotated tag object | `5bd6d899b26d0eeda0e3db638625ae22128c8a99` | `git cat-file -t` → `tag` |
| its target commit — **the RC5 engineering parent** | commit | `69e33c778efb14362439941d25ebbfcfb1068284` | `git rev-parse <tag>^{commit}` |
| A3.5 Session-4 Gate-8 meta-adjudication | commit | `748eea9b7ebe8c056714237213b644e521ef84f9` | strict ancestor of `560bf28` |
| A3.5 Session-3 evidence preservation | commit | `6b56bc4cb9de7b4538a1b87c09c91b83bc708ccf` | strict ancestor of `560bf28` |

Per A3.5 §1's binding canonical form, the engineering parent is cited as commit
`69e33c778efb14362439941d25ebbfcfb1068284`, never as "commit `5bd6d89`".

**Lineage.** `69e33c7` and `560bf28` are **sibling lineages**, neither an ancestor of the
other; their merge base is `a605120242594d23a5fc36d2e622d7d3084356fb` (the RC5 Gate-1 stop).
Verified by `git merge-base --is-ancestor` in both directions. RC5 branches from `69e33c7`
alone; the science branch is **not** merged (see §4).

**Contents present at the A3.5 tag target**, verified by `git ls-tree`:
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_5.md` (final amendment, 1658 lines),
`audit/MURU_A3_5_FINAL_HOSTILE_REVIEW.md`, `audit/MURU_A3_5_FINAL_DECISION_LEDGER.md`,
`audit/MURU_A3_5_GATE8_META_ADJUDICATION.md`, `audit/MURU_A3_5_IDENTITY_FINAL_CONTRACT.md`,
`audit/MURU_A3_5_SEED_BAND_INVENTORY.md`, `artifacts/paper_benchmark_amendment_a3_5.json`,
`audit/templates/MURU_A3_5_PRE_FREEZE_REVIEW_MATRIX*.md`, plus
`src/muru/paper_benchmark/identity_contract.py` and
`src/muru/paper_benchmark/seed_band_registry.py`. The Session-5 delta (`748eea9 → 560bf28`)
is 11 files, +2207/−230, and is confined to the amendment, the ledger, the hostile review,
and the review-matrix templates.

**Sealed state at reconciliation** (attested without opening any outcome): current-contract
Development symbolic execution NOT RUN; Held-out SEALED_NOT_OPENED; Challenge NOT
CONSTRUCTED OR EXECUTED; Confirmation (`artifacts/confirmation_set_sealed.json`) SEALED.
No outcome file was read, deserialized, previewed, grepped, or inferred from in producing
this document.

---

## 1. What the A3.5 freeze changed relative to the prebuild map

The prebuild map's own §0 states its blocking condition precisely: "A3.5 is still not
frozen — no tag exists (`benchmark-content-freeze-a3-5` was never applied), and the
corrective Gate-8 architecture is a recommendation, not yet folded into
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_5.md`'s own §6/§7 text."

Both halves of that condition are now discharged:

1. The tag exists and is verified above.
2. The corrective Gate-8 architecture **is** folded into the amendment's own bound prose,
   at the new §6.9 (§6.9.1 outcome-invariance discipline, §6.9.2 F5 supersession, §6.9.3
   amended Gate 7, §6.9.4 amended Gate 8 + F9 demotion, §6.9.5 independent verification),
   and is restated as numbered RC5 implementation obligations at §11 items 13, 14, 17, 18, 19.

The prebuild map's class `A3.5_RECOMMENDATION_NOT_YET_BOUND` (D1–D4) therefore no longer
exists. Its class `A3.5_BOUND_NOT_TAGGED` (D5–D14) no longer exists.

---

## 2. D1–D14 reconciliation

Classification vocabulary, as required:
`AUTHORIZED_UNCHANGED` · `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` ·
`ALREADY_IMPLEMENTED_REUSE` · `MECHANICAL_ENGINEERING` · `SUPERSEDED_DO_NOT_BUILD`

Every row's **prospective authority** is a citation into the *final frozen* amendment at
`560bf28`, not into a pre-freeze design document.

| # | Item | Classification | Prospective authority in the final frozen A3.5 |
|---|---|---|---|
| D1 | Gate 7 ceiling boolean + waiver floor | `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` | §6.9.3 (the amended `Gate7_PASS` rule, written out in full); §11 obligation 17 ("Gate 7 implements the amended waiver rule exactly as specified in §6.9.3 — … not the unconditional-waiver form `rc3_ceiling.py` currently implements"); §6.9.2 (why the floor lands in the waiver branch only); §9 row 19b (`VALID_WITH_SCOPE_LIMIT`) |
| D2 | `candidate_test_r2` provenance, computed once | `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` | §6.3(i) (binds `candidate_test_r2` identical to F5's R² and **computed once**); §6.9.3 ("this amendment does not add a second computation of it"); §11 obligation 13; §6.0 (the two-parameter affine-refit convention it is computed under) |
| D3 | Gate 8 hard-rung set + fail-closed check | `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` | §6.9.4 (`REQUIRED_HARD_GATES = {F1,F4,F7,F10}` and `check_gate8`'s `result != PASS` predicate, both written out in full, plus the exhaustive applicability table); §11 obligations 14 and 18 |
| D4 | Execution record: rung order, F9 secondary fields, schema bump | `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` | §6.9.4 (names the two secondary fields **`f9_stress_test_result`** and **`f9_stress_test_metric`** exactly, and states neither is read by `REQUIRED_HARD_GATES` or `check_gate8`); §11 obligation 19; §6.0/§6.9.4 (`NOT_APPLICABLE` never emitted; `EXECUTION_FAILURE` resolves to `FAIL` before the mapping) |
| D5 | Positive-scale-invariant identity contract | `ALREADY_IMPLEMENTED_REUSE` | §14.1 (identity contract row: `IDENTITY_CONTRACT_PASS`, **closed**, naming `audit/MURU_A3_5_IDENTITY_FINAL_CONTRACT.md`, "does not reopen at Session 5"); that document's own §1–§5 is the frozen specification; `src/muru/paper_benchmark/identity_contract.py` blob `151867cbee4cf60189afc5c393d0c8f3ca77c6a0` exists at the A3.5 tag target. See §3.1 for the §7.3 supersession. |
| D6 | `search_seed(case_ordinal, k)` + band invariants | `AUTHORIZED_UNCHANGED` | §8.1 (constants `A35_SEARCH_SEED_BASE = 2_100_000_000`, `A35_SEEDS_PER_CASE = 30`, the injective ordinal formula, the band `[2,100,000,000 , 2,100,011,399]`, the by-construction disjointness table, the mandatory `verify_search_seed_invariants()`); §11 obligations 9 and 10. Sub-parts: `seed_band_registry.py` is `ALREADY_IMPLEMENTED_REUSE`; the `search_seed`/`case_ordinal` arithmetic is `MECHANICAL_ENGINEERING` against a settled band. |
| D7 | Falsification executor | `AUTHORIZED_WITH_FINAL_A3_5_CORRECTION` | §6.0 (affine refit, truth-blindness incl. **no branching on partition**, no validity floors, outcome-state mapping), §6.1 F1, §6.2 F4, §6.4 F7, §6.5 F9, §6.6 F10, §6.7 null-threshold scope, §6.8 numeric ledger — **all unedited by Session 5** — as corrected by §6.9.2 (F5 is no longer a rung; its quantity is D2) and §6.9.4 (F9 computed and reported, never gating). See §3.2. |
| D8 | G1 LOEO trajectory bridge | `AUTHORIZED_UNCHANGED` | §5.1 (the frozen G1 spec, byte-identical at `d94d2c9` and `69e33c7`), §5.2 (the full binding table: A1's M0 form, A1.2's own fit protocol, A1.3's within-compound LOEO, the 30 test compounds, `trajectory_mae` = case-level flat-mean aggregate of `MAE_0,i`, `per_energy_mean_mae` = training-only per-energy-mean baseline, the gate, denominator 164, Wilson ≥ 0.70, the struck in-sample reading); §11 obligation 12 |
| D9 | Two-layer execution manifest | `AUTHORIZED_UNCHANGED` | §8.4 (the two-layer table, the "why per-partition is forced" argument, the binding derivation clause for scientific fields, append-only post-execution provenance, the canonical-JSON digest convention, the required field list); §11 obligation 15; §1's manifest rule (`git rev-parse <tag>^{}`) |
| D10 | G3 scoring authority guard | `AUTHORIZED_UNCHANGED` | §8.3 (`analysis.classify_negative_control` **MUST NOT** be used to score G3; `g3_contract.classify_g3_event` / `rc3_scoring.score_g3` are the sole authority); §11 obligation 11; §9 row 24 |
| D11 | Per-seed retention (`model_selection="score"`) | `AUTHORIZED_UNCHANGED` | §7.1 (the binding, the corrected derivation, the "not set on the regressor" rule), §7.6 (the exhaustive degenerate-state table), §7.2's `get_loc` landmine; §11 obligations 5 and 6; §9 row 13 (`NOT_PROVEN`, unbounded by calibration in either direction) |
| D12 | Gate-2 input provenance | `AUTHORIZED_UNCHANGED` | §7.2 (`complexity` from PySR's own `equations_["complexity"]`; `valid_r2` from the unweighted `rc3_calibration_runner._r2`; `engine.run_pysr`'s `Candidate` explicitly excluded); §11 obligation 4; §9 rows 9 and 10 (`VALID_NO_RECALIBRATION` — **and required for validity**) |
| D13 | Cross-seed grouping, `selection_count`, representative | `AUTHORIZED_UNCHANGED` | §7.4 (parameter-sharing merge bound on identifiability; two mandatory non-gating diagnostics), §7.5 (largest class wins; ties → class containing the lowest seed ordinal; `selection_count` ∈ 0..30 with frozen denominator 30; representative = lowest seed ordinal in the winning class; **no value recomputed, averaged, pooled or refit**), §7.6; §11 obligation 8; §9 rows 14–16. Grouping key comes from D5. |
| D14 | `Phi`, per-compound `g`, search target, `invalid_fraction` | `AUTHORIZED_UNCHANGED` | §4.1 (isotonic/60-knot/linear/flat-clamp `Phi`, training-fold only, then frozen; **no re-centring after freeze**; `E_REF = 45.0`, **not** `estimate.py`'s `ENERGY_SCALE = 30.0`; grid stated explicitly, not inherited), §4.2 (genuine A1 M0 per-compound fit vs frozen `Phi`; `protocol.estimate_one` excluded), §4.3 (raw untransformed `g`; one row per compound; five `GRAMMAR_PRIMITIVES` in frozen order; **no weights**; **no row filtering**), §4.4 (validation rows, `grammar.finite_mask`, **denominator 30**, gate ≤ 0.005); §11 obligations 1, 2, 3; §9 rows 1–8, 11, 12 |

**Every formerly provisional behavior now has prospective authority.** The prebuild map's
§1 table listed eleven "provisional assumptions (WAITING_FOR_A3_5_FREEZE)". Each is now
bound in the final frozen amendment:

| Map assumption | Now bound at |
|---|---|
| 1. Corrected profile/`g` estimator (Bundle 1) | §4.1–§4.2 |
| 2. Positive-scale-invariant identity contract | §14.1 + `MURU_A3_5_IDENTITY_FINAL_CONTRACT.md` (`FROZEN`) |
| 3. Per-seed PySR score selector | §7.1 |
| 4. One-seed-one-vote | §7.5 |
| 5. Largest class wins, tie → lowest seed ordinal | §7.5 |
| 6. 20/30 stability | §3 (frozen `STABILITY_GATE`/`STABILITY_DENOMINATOR`), §7.5 |
| 7. Earliest-seed representative | §7.5 |
| 8. `invalid_fraction` denominator 30 | §4.4 |
| 9. G1 A1.3/A1.4 LOEO semantics | §5.2 |
| 10. Seed/failure/manifest contract | §8.1–§8.4 |
| 11. Gate-8 corrective architecture | §6.9 (all five subsections) + §11 obligations 13–14, 17–19 |

---

## 3. Where the frozen A3.5 text differs from the prebuild map

**Rule applied: the frozen A3.5 text wins.** Five differences were found. None creates a
new scientific rule; each is the frozen text being more specific than, or naming something
differently from, the pre-freeze map.

### 3.1 §7.3's `TEMPLATE_KEY` recipe is superseded — resolved, with residual stale prose

The frozen amendment's §7.3 still carries the six-step `TEMPLATE_KEY` recipe
(`expand → powsimp(force=True) → together → cancel → expand`, guards A/B, singleton
fallback). The frozen sibling document `audit/MURU_A3_5_IDENTITY_FINAL_CONTRACT.md`
(Status: `FROZEN`, same commit) states in its own §1 that it "is the clean, freeze-ready
SPECIFICATION replacing amendment §7.3", and that §7.3's global-scale-strip step "was
proven unsound for rational-function-shaped candidates and is discarded, not patched."
The amendment's own §14.1 lists the identity contract as `IDENTITY_CONTRACT_PASS`,
**closed**, naming that document.

**Resolution.** This is a *disclosed supersession with stale prose in the superseded
section*, not a contradiction between two live bindings: the amendment names the
replacement document as the closed contract in its own attestation table, and the
replacement document names exactly which amendment section it replaces. The prebuild map
independently recorded the same reading (§3 item 6: "The amendment's own prose has not yet
been updated to point at the replacement — a text-only, non-scientific correction").

**Binding for RC5:** `identity_contract.py`'s `template_key` / `positive_scale_equivalent`
is the cross-seed identity contract. §7.3's recipe is `SUPERSEDED_DO_NOT_BUILD`. RC5 does
not re-implement it, does not "fix" it, and does not resurrect the seven-step
`TEMPLATE_KEY` construction. This is recorded here rather than silently applied.

### 3.2 F5's per-case procedure survives only as `candidate_test_r2`

The prebuild map's D7 says "build the **six** per-case procedures (F1/F4/F5/F7/F9/F10)".
The frozen §6.9.2 removes `F5_SCAFFOLD_HOLDOUT` from the rung set entirely: "It is never
again independently evaluated as a Gate-8 rung. Its floor role is discharged inside Gate 7."
RC5 therefore computes **five** rung procedures (F1, F4, F7, F9, F10) plus the single
`candidate_test_r2` quantity §6.3 defines, which is D2, not a rung.

### 3.3 The Gate-8 checker is renamed and its predicate changes

The map's D3 keeps the name `check_falsification_harness` and narrows
`REQUIRED_FALSIFICATION_RUNGS`. The frozen §6.9.4 specifies a function named **`check_gate8`**
over a set named **`REQUIRED_HARD_GATES`**, with predicate `result != PASS` (not
`result == FAIL`), explicitly so a stray `NOT_APPLICABLE` fails closed. §11 obligation 18
names the replacement. RC5 implements the frozen names and the frozen predicate.

### 3.4 The F9 secondary field names are fixed by the frozen text

The map's D4 proposes "e.g. `f9_secondary_result`". The frozen §6.9.4 names the fields
exactly: **`f9_stress_test_result`** (∈ `{PASS, FAIL}`) and **`f9_stress_test_metric`**
(the raw `min_k(R2_k)` over the six leave-one-energy-out folds). §11 obligation 19 repeats
both names. RC5 uses the frozen names.

### 3.5 A1.2's fit protocol is frozen as a specification, not as executable code

The map's D8 speaks of "consuming `adequacy.py`'s frozen M0 LOEO machinery". Direct
inspection of `69e33c7:src/muru/paper_benchmark/adequacy.py` shows that module states its
own scope boundary explicitly: "it deliberately contains **no fitter, no optimiser, and no
numerical model evaluation**"; it owns the *decision contract* and consumes
`CompoundContrastRecord` values reported by an engine. No executable A1.2 fitter exists
anywhere at `69e33c7` (verified: `COARSE_LOG_G_POINTS`, `REFINEMENT_ROUNDS`,
`REFINEMENT_POINTS`, `REFINEMENT_SHRINK`, `LOG_G_BOUNDS` have no non-test consumer).

**Consequence, resolved conservatively as a mechanical engineering consequence, not a
scientific choice:** RC5 must *implement* A1.2's protocol, because A3.5 §5.2 binds every
one of its parameters explicitly — `log_g ∈ [-2.0, +2.0]`, 81-point endpoint-inclusive
coarse grid, 3 refinement rounds of 21 points, shrink 10, lexicographic tie-break,
objective `unweighted_sum_of_squared_mu_residuals` — and explicitly forbids substituting
`estimate._best_log_g`'s 241-point `[-1.6, 1.6]` grid with parabolic refinement. Every
number comes from `adequacy.py`; RC5 invents none. "Do not create a new trajectory
estimator" is honoured by implementing the frozen protocol exactly and reading every
constant from the frozen module, never by inventing an estimator or importing the Phase-3
one.

---

## 4. Science-lineage artifacts required by RC5, and how they are brought across

The identity contract and the seed-band registry live on the science lineage, not at
`69e33c7`. A3.5 §8.1 additionally requires that A3.5's constants live in a **new** module
because `rc3_provenance.py`, `registry.py` and `analysis.py` are byte-pinned by
`pb_30`/`pb_33`/`pb_34` and the RC4.2 `AUTHORIZED_DELTA` ledger is closed.

**Method (per mission §3): file-level import with recorded provenance, never a branch
merge.** The blobs below are byte-identical at `6b56bc4`, `748eea9` and `560bf28`; the
A3.5 **tag target** `560bf28` is used as the source of record because it is the frozen
science freeze itself.

| File | Source commit | Blob SHA | Bytes |
|---|---|---|---|
| `src/muru/paper_benchmark/identity_contract.py` | `560bf28` | `151867cbee4cf60189afc5c393d0c8f3ca77c6a0` | 46602 |
| `src/muru/paper_benchmark/seed_band_registry.py` | `560bf28` | `b6b127ef11fc7f2c46379acd089755057f5ee7cb` | 15123 |
| `tests/test_identity_contract.py` | `560bf28` | `96b20878fa2583ab318b53393d93b430fbef94f6` | 52747 |
| `tests/test_seed_band_separation.py` | `560bf28` | `ddd702c081de5d0fe679737f5a78965736906fff` | 6937 |

Byte identity is verified after import by recomputing `git hash-object` on the working-tree
file and comparing to the frozen blob SHA above.

**Deliberately NOT imported:** `src/muru/paper_benchmark/falsification_v2_fixtures.py`
(blob `1a617036cfad1793775bf3a82ac0e9982db23dd6`) and
`audit/muru_a3_5_falsification_v2_sealed_raw_results.json`. Both are qualification-harness
material for the **consumed** v1/v2 sealed populations. §14.1 marks those populations
`CONSUMED, permanently`; the prebuild map §5.4 marks v2's single-parameter scale-only refit
`DEAD/SUPERSEDED_PATH` for production; and `MURU_A3_5_FALSIFICATION_V1_STATUS.md` carries a
standing prohibition on reuse as fixture material. RC5 imports neither, and no RC5 test
consumes either.

`identity_contract.py` is preserved **exactly**. The frozen A3.5 contract requires no
engineering adaptation at its call boundary: its public surface
(`parse_candidate`, `template_key`, `template_key_string`, `positive_scale_equivalent`,
`cluster_by_template_key`) already accepts freshly-parsed candidate strings, which is
precisely the production construction §5 of the identity-contract document proves the
contract holds unconditionally for. RC5's caller passes `parse_candidate(<as-emitted
equations_["equation"] string>)` and never scalar-multiplies an already-parsed object.

---

## 5. Frozen-file edits RC5 must make, and their prospective authority

Two `FROZEN_EXPLICIT` A3.1 files require coordinated edits. Both are explicitly authorized
by the final frozen amendment's own §11 obligations, which is what changed since the
prebuild map wrote "Do not build."

| File | Edit | Authorized by |
|---|---|---|
| `src/muru/paper_benchmark/structural_acceptance.py` | Gate 7's waiver gains the `candidate_test_r2 > null_threshold[min(complexity,20)]` conjunct; `StructuralCandidate` gains `candidate_test_r2`; `REQUIRED_HARD_GATES = {F1,F4,F7,F10}`; `check_gate8` with `result != PASS` | §11 obligations 14, 17, 18; §6.9.3, §6.9.4 |
| `src/muru/paper_benchmark/rc3_record.py` | `FALSIFICATION_RUNG_ORDER` / drift guard reconciled with the four-member hard set; `f9_stress_test_result` and `f9_stress_test_metric` added; `RECORD_SCHEMA_VERSION` bumped | §11 obligation 19; §6.9.4; the drift guard is a mechanical coupling first surfaced by the prebuild map's D4 |

**Not authorized and not done:** no historical digest is edited, no test is skipped,
xfailed or weakened, no protected-path enforcement is loosened, no calibration artifact or
threshold table is touched, no historical freeze tag is moved, and `CEILING_FRACTION_GATE`,
`CEILING_WAIVER_THRESHOLD`, `STABILITY_GATE`, `STABILITY_DENOMINATOR`, `MAX_COMPLEXITY`,
`MAX_INVALID_FRACTION` keep their frozen values.

---

## 6. `SUPERSEDED_DO_NOT_BUILD` inventory

Carried forward from the prebuild map §5.4 and extended by the final freeze. RC5 builds
none of these:

1. §7.3's seven/eight-step `TEMPLATE_KEY` placeholder-canonicalization recipe (§3.1 above).
2. `63bbcce`'s bucket+stride A3.5 seed band `[1,905,281,400 , 2,104,764,629]` — overlaps
   `objval/plan2` by 194.7M integers (A3.5 §8.1, §13 row 3).
3. `50e42c7`/`9c8d42b`'s five hand-named F9 energy subsets (A3.5 §6.5, §13 row 8).
4. `falsification_v1` in any role, including as fixture material.
5. `falsification_v2`'s single-parameter scale-only refit `y ≈ b·E(x)` as a production
   convention — §6.0's two-parameter affine refit `y ≈ a + b·E(x)` governs.
6. `aec93db`'s per-coefficient-WLS justification for parameter-sharing merge (§7.4; the
   merge rule survives on identifiability, the justification does not).
7. `dd0d054`'s inverse-variance weighting channel (§4.3, §13 row 5).
8. `analysis.classify_negative_control` as a G3 scoring path (§8.3).
9. `F5_SCAFFOLD_HOLDOUT` as an independent Gate-8 rung (§6.9.2, §12).
10. `F9_ENERGY_SUBSET` as a hard gate (§6.9.4, §12).
11. `discovery/estimate.py`'s `ENERGY_SCALE = 30.0`, `LOG_G_GRID`, `N_ALTERNATIONS` as
    inherited constants for benchmark estimation (§4.1, §13 row 17).
12. `protocol.estimate_one` as the per-compound `g` estimator (§4.2).
13. `engine.run_pysr`'s `Candidate` (`grammar.complexity`, weighted invalid-masked R²) as
    any gate input (§7.2).
14. Exact Algebra computation — `DEFER_AS_UNEXECUTABLE_DESCRIPTIVE_ENDPOINT` (§10.1).

---

## 7. Verdict

Every D1–D14 item is classified. Every formerly provisional A3.5 behavior has prospective
authority in the final frozen amendment at `560bf28`. Five differences between the frozen
text and the pre-freeze map were found and resolved in the frozen text's favour, each
recorded in §3. No new scientific rule was created. No sealed outcome was accessed.

```
======================================================================
RC5 POST-A3.5-FREEZE RECONCILIATION COMPLETE — IMPLEMENTATION AUTHORIZED
======================================================================
```
