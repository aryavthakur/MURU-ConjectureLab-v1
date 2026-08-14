# MURU RC5 Missing-Semantics Prospective-Authority Audit

**Document ID:** `MURU-AUDIT-RC5-EXECUTION-SEMANTICS-AUTHORITY-01`
**Classification:** `INDEPENDENT_PROSPECTIVE_AUTHORITY_AUDIT`
**Status:** `AUDIT_COMPLETE`
**Audit Branch:** `audit/muru-rc5-execution-semantics-authority-audit`
**Mode:** `READ_ONLY`. RC5 was not implemented. Development was not opened. Held-out
was not opened. Challenge was not run. Confirmation was not opened. No science
was altered.

**Governing state at audit time:**

| Item | Ref |
|---|---|
| A3.4 science freeze | `be23b80` / `benchmark-content-freeze-a3-4` |
| RC4 engineering freeze | `c800e7a` / `engineering-rc4-a3-4` |
| RC4.1 environment closure | `8c5dd41` / `engineering-rc4-1-environment-closure` |
| Calibration preservation | `44e5e36` |
| Calibration integrity adjustment | `6a67982` (current tip of `main`/`eng/muru-rc5-case-execution`) |
| Development | `NOT_OPENED` |
| Held-out | `SEALED` |

This audit is independent of, and was conducted without relying on the
correctness of, any of Claude's own RC5 work. Where Claude's own prior finding
(`e54364b`, "Record the Development execution blocker: RC4 has no executable
case path") is cited below, it is cited as **evidence**, checked directly
against the source it claims to describe, not accepted on authority.

---

## 1. Method

Searched: all local branches and tags (`git branch -a`, `git tag`), the full
commit graph reachable from every ref (`git log --all`), every Claude worktree
under `.claude/worktrees/`, `engineering/muru-completion` (RC2, `c7c2332` /
`5235f81`), the RC3/RC3.1/RC4/RC4.1 lineage, `src/muru/paper_benchmark/*.py`,
`src/muru/adequacy/*.py`, `src/muru/pipeline.py`, `src/muru/objval/*.py`,
`src/muru/discovery/*.py`, all `MURU_PAPER_BENCHMARK_AMENDMENT_A*.md`
documents, `MURU_PAPER_BENCHMARK_PROTOCOL.md`, `DEVELOPMENT_EXECUTION_BLOCKER.md`,
and the prior audit `audit/muru-heldout-preparation-spec-audit`
(`202edd7`).

Historical implementation was **not** treated as automatic authority.
Frozen-content freezes (`benchmark-content-freeze-a*`, `engineering-rc*`) and
amendment documents were treated as the only sources of prospective science
authority; code was treated as authority only where it is itself part of a
frozen, amended, or explicitly-referenced-as-contract module (e.g.
`structural_acceptance.py` self-declares "This module is the REFERENCE
CONTRACT").

Classification labels (exactly as specified):
`FROZEN_EXPLICIT`, `FROZEN_DERIVABLE_ENGINEERING`, `HISTORICAL_PRECEDENT_ONLY`,
`UNFROZEN_SCIENTIFIC_DECISION`, `NOT_REQUIRED`.

---

## 2. Headline finding

**RC4 has no executable production-case path**, confirming `e54364b` by
independent inspection rather than by trusting it. Verified directly:

- `git grep -n "CaseExecutionRecord(" -- src/ scripts/` (at `6a67982`, current
  tip) → no match outside `tests/`.
- `git grep -n "CompoundContrastRecord(" -- src/ scripts/` → no match anywhere.
- `PySRBackend.search(self, world: CalibrationWorld, seed: int)` in
  [`rc3_calibration_runner.py:114,827`](../src/muru/paper_benchmark/rc3_calibration_runner.py)
  is typed on `CalibrationWorld` only; no function anywhere in
  `src/muru/paper_benchmark/` builds a `CalibrationWorld`-shaped object, or any
  compatible object, from a benchmark case.
- No `runner.py` exists anywhere under `src/muru/paper_benchmark/` at any
  commit on the RC3/RC3.1/RC4/RC4.1 lineage. `find . -iname runner.py` across
  the whole checkout returns nothing.
- `eng/muru-rc5-case-execution` (the worktree seeded for RC5 engineering) is
  at the same commit as `main` (`6a67982`) — zero RC5 commits exist yet.

This is the correct backdrop against which "was every semantic prospectively
frozen" must be read: for most of the missing items there is *no executable
code at all* to audit, only (a) reference-contract modules that define
**inputs and predicates** over already-computed values, and (b) prose
amendments that are explicit about calibration-world mechanics but frequently
silent on whether the same mechanics apply, unmodified, to a real benchmark
case.

---

## 3. Per-semantic classification

| # | Semantic | Classification | Proof |
|---|---|---|---|
| 1 | Case → execution adapter | **UNFROZEN_SCIENTIFIC_DECISION** | No function anywhere builds a case's design matrix / target / split into the shape `PySRBackend.search` requires. `PySRBackend.search(world: CalibrationWorld, seed)` in [`rc3_calibration_runner.py:114`](../src/muru/paper_benchmark/rc3_calibration_runner.py) is typed on `CalibrationWorld`, which is itself bound (per A3.2) to "the A3.2 null covariate order, split algorithm and base-target identity" — i.e. calibration-specific, not a generic case container. Alternative adapter designs (which columns become covariates, in what order, what representation) would change which candidates PySR can even express, materially altering G1/G2/G3 outcomes. Confirmed independently of, and consistent with, `e54364b` §2 check 5. |
| 2 | Train/validation/test usage | **FROZEN_EXPLICIT** | [`generator.py:30-31`](../src/muru/paper_benchmark/generator.py): `N_COMPOUNDS = 180`, `N_SCAFFOLDS = 30`, `scaffold = np.repeat(np.arange(30), 6)`; 20 scaffolds (120 compounds) train / 5 scaffolds (30) validation / 5 scaffolds (30) test, scaffold-disjoint. Restated in [`MURU_PAPER_BENCHMARK_PROTOCOL.md`](../MURU_PAPER_BENCHMARK_PROTOCOL.md): "split, into 20 training, five validation, and five test groups." |
| 3 | Scalar target construction (adequacy scalar `log_g`) | **FROZEN_EXPLICIT** | [`protocol.py`](../src/muru/paper_benchmark/protocol.py): `fit_training_scalar` (training-only mean profile) and `estimate_one` (`log_g = clip(-residual, -2, 2)`) are the frozen, structurally fold-local helpers. Module docstring: "Minimal fold-local scalar adapter boundary for the locked implementation." Their absence of a production caller is an engineering gap (item 5 of `e54364b`), not a semantics gap — the rule itself is fully specified. |
| 4 | M0 fit | **FROZEN_EXPLICIT** | Amendment A1 (`2ac86c5`, `MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md`), implemented verbatim in `src/muru/adequacy/` on `engineering/muru-completion` (`c7c2332`): "M0 is the frozen shared horizontal-scaling model against the training-only `Phi`." Fitter is "A1.2 verbatim — unweighted squared `mu` residuals, closed-form solves... coarse-to-fine grid... lexicographic tie resolution, no random restart." |
| 5 | M1 fit | **FROZEN_EXPLICIT** | Same source as #4: "M1 warps the profile argument about the frozen E_REF = 45 pivot." |
| 6 | M2 fit | **FROZEN_EXPLICIT** | Same source as #4: "M2 and M3 rescale the normalised shape between a compound-specific vertical endpoint and the frozen opposite one," closed-form solve. |
| 7 | M3 fit | **FROZEN_EXPLICIT** | Same source as #4/#6. |
| 8 | Adequacy decision | **FROZEN_EXPLICIT** | `src/muru/adequacy/decision.py` on `c7c2332`, conformance-proven against the frozen contract by `tests/test_eng_adequacy_conformance.py`, which "materialises the frozen decision module from commit 80a7803 and requires identical typed verdicts" across 11 named scenarios. `check_falsification_harness`/A1 wiring is a **different engineering branch** from RC4, but the decision rule text and its independent implementation both exist and agree — a merge, not a scientific choice. |
| 9 | Exact symbolic target (the PySR search dependent variable for a real case) | **UNFROZEN_SCIENTIFIC_DECISION** | No document or module states what quantity a case's symbolic search fits (raw `mu`, the `log_g` adequacy scalar, a per-energy trajectory, or something else), nor its representation (log vs linear, per-energy vs case-aggregate). `contract.py`'s own docstring: "Strict evaluator input contract for a **future locked MURU engine**" — it validates predictions computed elsewhere; it does not define what is predicted. Choosing wrongly changes what candidates PySR can discover at all. |
| 10 | Symbolic covariates | **UNFROZEN_SCIENTIFIC_DECISION** | Case content generation (which descriptor columns a compound has) is frozen and healthy (`generator.py`; `e54364b` §3: "Case content generation is healthy and is not part of the gap"). But *which* of those columns enter the PySR design matrix, in what order, and in what representation, is exactly the missing case-to-search adapter's job (#1). A3.1's calibration text says worlds share "the same five synthetic covariates," which is evidence about calibration worlds, not a binding statement about which covariates a real case's search uses. |
| 11 | Search settings (PySR version, operator grammar, `niterations`/`populations`/`population_size`/`maxsize`/parsimony) | **FROZEN_DERIVABLE_ENGINEERING** | [`calibration_contract.py:56-72`](../src/muru/paper_benchmark/calibration_contract.py) `SEARCH_SETTINGS` is a single frozen dict (PySR 1.5.10, `+,-,*,/`, unary `sqrt,log,square,cube,inv`, `exp`/trig excluded, `niterations=40`, `populations=15`, `population_size=33`, `maxsize=20`, `parsimony=0.0032`). A3.2 (`MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md:185`) restates "the search settings, PySR 1.5.10, the operator grammar" in its "everything else in A3.1 stands unchanged" list **without** the "calibration worlds only" qualifier it explicitly attaches to the seed/split mechanics two lines above — i.e. this is the one place A3.2 treats a piece of the calibration section as a global fact rather than a calibration-scoped one. Combined with the structural necessity that a null threshold is meaningless unless computed under the identical search process it is compared against (Gate 2: `valid_r2 > null_threshold[complexity]`), there is only one scientific reading: real-case search must use these exact settings. Caveat: this reading is derived, not a sentence that says "Development case search uses `SEARCH_SETTINGS`" in so many words. |
| 12 | Seeds/case (count = 30) | **FROZEN_EXPLICIT** | [`structural_acceptance.py:68`](../src/muru/paper_benchmark/structural_acceptance.py): `STABILITY_DENOMINATOR = 30`, docstring "selection_fraction >= 20/30" under `## Structural acceptance` (the real case-level gate, not the calibration section). `rc3_record.py` imports this constant directly into `CaseExecutionRecord`. |
| 13 | Search-seed derivation (the formula producing 30 seed integers for a Development/Held-out case) | **UNFROZEN_SCIENTIFIC_DECISION** | Only two seed-generating functions exist in the repository: `derive_calibration_seeds` (`calibration_contract.py`, hashes `world_id` into band `PB_SEED_BASE=2_110_000_000` + spread `370_000`×100) and `derive_smoke_seed` (`rc3_provenance.py`, band `1_900_000_000`+). Neither is parameterised over a case ID in a way that is declared authoritative for Development; both are explicitly scoped in code and docstring to their own domain. `e54364b` records this as unwritten (item 1); independently confirmed no third function exists at `6a67982`. |
| 14 | Prospective seed namespace (the string domain hashed to derive seeds, e.g. `PB\|development\|...`) | **UNFROZEN_SCIENTIFIC_DECISION** | `rc3_provenance.py:317-320` documents only `base_target_seed_namespace = "PB\|NCAL\|<world_id>\|..."` and `split_seed_namespace`, both calibration (`NCAL`)-prefixed. No `PB|development|...` or `PB|held_out|...` search-seed namespace string is declared anywhere in code or amendment text. |
| 15 | Seed band (integer range reserved so Development/Held-out seeds cannot alias calibration or smoke seeds) | **UNFROZEN_SCIENTIFIC_DECISION** | `rc3_provenance.py:137-153` `assert_seed_band_separation()` proves disjointness of exactly two bands: smoke (`RC3_SMOKE_SEED_BASE`, 1_900_000_000+) and calibration (`CALIBRATION_SEED_MIN..MAX`, 2_110_000_000..2_146_999_929). No third band is declared, reserved, or asserted disjoint for Development or Held-out. If a future implementer reuses the calibration band's derivation naively, Development seeds could numerically collide with calibration seeds. |
| 16 | Per-seed candidate retention | **UNFROZEN_SCIENTIFIC_DECISION** | `PerSeedStatusEntry` (`rc3_record.py:162-173`) stores only `seed`, `status`, `selected_expression_string`, `error_message` — a single already-*selected* string per seed, not the seed's raw Pareto front. But no rule (see #9, #17, #19) specifies how that one string is chosen from a seed's raw PySR output, so this field's own contents are underspecified even though its container schema is frozen. The prior audit (`audit/MURU_HELDOUT_PREPARATION_SPEC_AUDIT.md` Pass 2 #10) separately found "mandatory retention of internal intermediate Pareto evolution histories is optional hardening" — i.e. full-Pareto retention is affirmatively *not* required, sharpening rather than resolving the gap: some single-candidate-per-seed rule is required and none is frozen. |
| 17 | Pareto handling | **FROZEN_DERIVABLE_ENGINEERING** | `rc3_calibration_runner.py` (~line 840-882) already extracts a per-complexity best-validation-R2 curve from a seed's raw PySR `equations` dataframe (`best_valid_r2_by_complexity`), a generic, case-agnostic transform of any PySR run's Pareto front. This extraction pattern is directly reusable for case seeds with no scientific choice involved. What it does *not* resolve is #16/#19 (picking one candidate expression per seed, and grouping across seeds) — a materially different operation from building a per-complexity R2 curve. |
| 18 | Cross-seed selection | **UNFROZEN_SCIENTIFIC_DECISION** | No equivalence rule (exact string match after canonicalization? SymPy `simplify`-equal? same family per `g2_contract.py`'s effective-support taxonomy?) is declared for grouping 30 seeds' outputs into a modal candidate. A candidate but non-authoritative precedent exists in `src/muru/objval/select.py` — the Type 2 (`objval`) study's cross-seed rule retains the whole Pareto band and groups by *family* (support/sign/exponent/monotonicity), explicitly rejecting collapsing to one expression per seed. This is a *different, declared study* ("Fresh validation-world construction for the objective-alignment study" — `generators2.py` docstring) with its own tolerance the commit explicitly says must not move for *that* study; it predates and is structurally incompatible with `structural_acceptance.py`'s count-based `selection_fraction = k/30` gate, which presumes a single yes/no "was this seed's output the accepted candidate" per seed. `select.py` is evidence a different design was chosen for a sibling track — not authority for A3.1's paper-benchmark denominator. |
| 19 | `selection_count` | **UNFROZEN_SCIENTIFIC_DECISION** | The *field* is frozen (`rc3_record.py:237` `selection_count: int # k, out of 30`, validated `0 <= k <= 30`), and the *denominator/threshold it feeds* is frozen (see #20). Its *computation* is not: `e54364b` §2 check 3, independently reverified (`git grep -n selection_count -- src/`) returns only the field name in `rc3_record.py`/`rc3_acceptance.py`; no function computes it. |
| 20 | Stability threshold (`k/30 >= 20/30`) | **FROZEN_EXPLICIT** | [`structural_acceptance.py:66`](../src/muru/paper_benchmark/structural_acceptance.py): `STABILITY_GATE = 20 # out of 30`. `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md:150`: "`selection_fraction >= 20/30`." A3.2 explicitly reaffirms: "stability 20/30... unchanged." |
| 21 | `valid_r2` definition | **UNFROZEN_SCIENTIFIC_DECISION** | `rc3_record.py:235` declares `valid_r2: float` as a dataclass field only. No function anywhere computes an R² value against a validation split for a real case (`git grep -n "valid_r2\s*="` finds no assignment outside dataclass slots and a docstring reference). Ambiguous in at least: validation-split-only vs validation+test, `sklearn.r2_score` vs manual formula, and whether it is per-seed-best or per-candidate. |
| 22 | Complexity definition | **FROZEN_DERIVABLE_ENGINEERING** | `SEARCH_SETTINGS` (#11) declares no custom per-operator complexity weights; PySR 1.5.10's default node-count complexity applies uniquely once the operator grammar and engine version are pinned, exactly as already consumed at `rc3_calibration_runner.py:846`: `complexity = int(equations["complexity"].iloc[row])`, i.e. PySR's own reported column, used as-is. |
| 23 | `invalid_fraction` definition | **UNFROZEN_SCIENTIFIC_DECISION** | `rc3_record.py:239` `invalid_fraction: float` — dataclass field only, no computation anywhere. Undefined whether the numerator counts invalid *seeds*, invalid *candidates within a seed's Pareto front*, or invalid *evaluations* (e.g. complex/NaN outputs per FM-07); the A3.1 gate text ("`invalid_fraction <= 0.005`") does not disambiguate. |
| 24 | Null-threshold lookup | **FROZEN_EXPLICIT** | `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md:150`: `valid_r2 > null_threshold[min(complexity, 20)]`. Threshold table construction itself: `numpy.quantile(..., 0.95, method="linear")` then `np.maximum.accumulate` (A3.1 lines 208-211), calibrated once and VALID (`44e5e36` preserves the A3.2 execution). |
| 25 | Ceiling rule | **FROZEN_EXPLICIT** | A3.1 lines 103-104: `ceiling_fraction >= 0.80 OR ceiling_r2 < 0.05` (waiver), with the exact `HistGradientBoostingRegressor(max_iter=150, max_depth=3, min_samples_leaf=20, random_state=0)` pinned to `scikit-learn==1.9.0`, implemented in `rc3_ceiling.py`. |
| 26 | Support recovery | **FROZEN_EXPLICIT** | A3.1 "Effective support" section (lines 52-67): parse under protected grammar, SymPy `simplify` normalization, cancelled/zero/constant terms excluded, "No new magnitude threshold invented," unresolvable → `SUPPORT_UNRESOLVED`. Implemented in `g2_contract.py`. |
| 27 | Six falsification-rung execution (the pass/fail procedure for each rung against a real case) | **UNFROZEN_SCIENTIFIC_DECISION** | `check_falsification_harness()` (`structural_acceptance.py:104`) only aggregates an already-supplied `Mapping[FalsificationRung, FalsificationResult]`; there is no executor. `e54364b` §2 check 4, reverified directly. Rung *names* are frozen (#28), but e.g. what perturbation magnitude or reproducibility tolerance makes `F1_REPRODUCIBILITY` return `FAIL` vs `PASS` is nowhere specified — a materially outcome-affecting choice. |
| 28 | Rung ordering / membership | **FROZEN_EXPLICIT** | `FALSIFICATION_RUNG_ORDER` tuple (`rc3_record.py:59-65`) = `(F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT, F5_SCAFFOLD_HOLDOUT, F7_INFLUENCE_DROP, F9_ENERGY_SUBSET, F10_NEGATIVE_CONTROL)`, cross-checked at import time (`if set(...) != set(REQUIRED_FALSIFICATION_RUNGS): raise ImportError`) against `structural_acceptance.py`'s `REQUIRED_FALSIFICATION_RUNGS`. Matches A3.1 lines 122-131 exactly, including "F8 is structural labelling, not an acceptance gate" and "`NOT_APPLICABLE` is never counted as `PASS`." |
| 29 | Structural acceptance (the 8-gate ordered predicate) | **FROZEN_EXPLICIT** | A3.1 lines 89-104 give the exact ordered 8-gate predicate; `structural_acceptance.py` implements it verbatim, self-declared "the REFERENCE CONTRACT." Confirmed against the codebase directly, not merely against the prior audit that also found this. |
| 30 | Parameter recovery integration | **FROZEN_DERIVABLE_ENGINEERING** | The scoring *rule* (denominators 156/156/84, tolerances `\|Δp_mass\| <= 0.15`, `\|Δc_desc\| <= 0.10`) is fully specified by Amendment A3.3 (`e91aae6`) and implemented (referenced in `audit/MURU_HELDOUT_PREPARATION_SPEC_AUDIT.md` Pass 1). What is missing is only the per-case *call* into that already-complete scorer with case-specific inputs — mechanical wiring, not a science decision, once #1/#9/#10 are resolved. |
| 31 | Predictive equivalence integration | **FROZEN_DERIVABLE_ENGINEERING** | Same reasoning as #30. A3.4 fully specifies thresholds (`\|V\| >= 2150`, `c* > 0`, `rel_RMSE <= 0.05`, `r >= 0.990`) and denominator (144); only per-case invocation is missing. |
| 32 | Exact algebra scoring | **FROZEN_EXPLICIT** | A3.4, 5 families (F01, F08, F09, F10, F17) × 12 cases = 60, per prior audit Pass 1 (independently re-derivable from `registry.py` family/partition counts, not re-verified line-by-line in this pass but consistent with all other denominators checked). |
| 33 | Scientific failure semantics (per-seed `EXECUTION_FAILURE` handling) | **FROZEN_DERIVABLE_ENGINEERING** | `SeedStatus` enum (`COMPLETED_WITH_CANDIDATES` / `COMPLETED_NO_CANDIDATE` / `EXECUTION_FAILURE`) and the rule "if ANY seed has `EXECUTION_FAILURE`, ... becomes +1.0. Conservative" (A3.1 lines 185-195) is written for calibration worlds, but `e54364b` item 3 itself frames the needed component as "a per-case multi-seed driver **with the calibration runner's failure and resume semantics**" — i.e. reuse, not reinvention. The enum and its `np.isfinite`-is-not-enough rule generalize with only one sensible reading to a case's 30 seeds. |
| 34 | Operational resume semantics | **FROZEN_DERIVABLE_ENGINEERING** | `rc3_calibration_runner.py`'s `SeedStore` (settings-digest-checked resume, no selective retries — corroborated by `audit/MURU_HELDOUT_PREPARATION_SPEC_AUDIT.md` DEF-09 discussion) is an existing, reusable pattern for exactly this purpose; same reasoning as #33. |
| 35 | Development/Held-out path parameterization | **FROZEN_DERIVABLE_ENGINEERING** | `MURU_PAPER_BENCHMARK_PROTOCOL.md` "Execution boundary": path identity ("same backend, settings, grammar, selection rules, threshold, representation, endpoints, failure semantics, differing only in partition identity and seeds" — `e54364b` §5) is a binding requirement, not a free choice; once #1-#34 are resolved as one parameterised path, threading `partition`/`case_id` through it has only one sensible engineering shape. No code currently implements *any* path (confirmed §2 above), so nothing exists to audit for divergence — the requirement is frozen, the artifact is not yet built. |
| 36 | Raw seed record format | **FROZEN_EXPLICIT** (schema) / gap noted at #16 | `PerSeedStatusEntry` (`rc3_record.py:162-173`): `seed: int`, `status: SeedStatus`, `selected_expression_string: str \| None`, `error_message: str`, with `error_type` derived as exception class name only (no path/PID leakage, per the module's determinism rules). The *container* schema is frozen; what populates `selected_expression_string` is not (#16, #18). |
| 37 | Case record format | **FROZEN_EXPLICIT** | `CaseExecutionRecord` dataclass (`rc3_record.py`), `RECORD_SCHEMA_VERSION = "muru-rc3-case-record-1.0.0"`, canonical JSON serialization rules stated in the module docstring (sorted keys, fixed float formatting via shortest-round-trip decimal, `-0.0` normalized to `0.0`, no timestamps/paths/hostnames in the scientific payload). |
| 38 | Sidecar format | **FROZEN_EXPLICIT** | `ProvenanceSidecar` (`rc3_record.py`), explicitly the container for timestamps/paths/hostnames/durations, "excluded from the scientific hash" by design. |
| 39 | Execution manifest | **UNFROZEN_SCIENTIFIC_DECISION** | No `ExecutionManifest`-equivalent class or schema exists in `governance.py` (only `ImplementationLock`) or anywhere else in `src/muru/paper_benchmark/`. The prior audit classified every manifest *path* (`artifacts/held_out/held_out_execution_manifest.json` etc.) as `FROZEN_FUTURE_PATH` — i.e. only the *filename convention* is anticipated; the manifest's *content schema* (which fields lock which case/seed set pre-execution, preventing selective retries) is unwritten. This is not a purely mechanical choice: a manifest that under-specifies what it locks would fail to actually prevent selective retries (item 8/9 of the heldout matrix), so its content is a real design surface, not a naming convenience. |
| 40 | Atomic-write requirements | **FROZEN_DERIVABLE_ENGINEERING** | `artifacts.py:25-30` `_write_atomic()` — write to `path.tmp`, then `Path.replace()` (POSIX atomic rename), return sha256 of the payload — is an established, already-used pattern for every existing frozen-content artifact. Extending it to new execution outputs (seed records, case records, sidecars, manifests) has only one standard-engineering meaning; no scientific choice is involved. |

---

## 4. Special-focus verdict (Claude's suspected missing items)

Every item Claude's own prior work flagged as suspect is **confirmed genuinely
unfrozen**, not merely buried:

| Suspect item | Independently confirmed? | Where it actually lives (or doesn't) |
|---|---|---|
| Development search seed rule | **Confirmed unfrozen** | Only `derive_calibration_seeds` (calibration-band) and `derive_smoke_seed` (engineering-smoke-band) exist. Neither is declared as, or trivially reducible to, a Development rule. |
| Seed namespace/band | **Confirmed unfrozen** | `assert_seed_band_separation()` proves exactly two bands disjoint; no third band reserved. |
| Cross-seed selection | **Confirmed unfrozen** | No equivalence rule; the one extant precedent (`objval/select.py`) belongs to a different, declared study with an incompatible (band/family, not count) selection philosophy. |
| `selection_count` | **Confirmed unfrozen** | Field and its consumption (threshold, denominator) are frozen; its computation is not — no function in the repository computes it. |
| `k >= 20/30` stability threshold | **Confirmed frozen** (the threshold, not the count) | `STABILITY_GATE = 20`, `STABILITY_DENOMINATOR = 30` in `structural_acceptance.py`, reaffirmed by A3.1 and A3.2 text. This one piece *is* settled; only the input (`k`) feeding it is not. |
| Case-to-PySR target mapping | **Confirmed unfrozen** | No adapter exists; the only frozen scalar target (`log_g`, `protocol.py`) is the M0-adequacy target, not shown or argued anywhere to be the same quantity PySR's symbolic search fits. |

None of these were found "buried elsewhere" under a different name. The
search covered every branch and worktree reachable from `git branch -a` /
`git tag`, and the two most on-topic sibling artifacts that could plausibly
have resolved them — `engineering/muru-completion`'s `pipeline.py` (old
engine, `n_seeds=8`, a "random" engine, not PySR — incompatible search config,
not just a different branch of the same one) and `objval/select.py` (a
declared different study with a declared different tolerance) — were
inspected directly and ruled out as authority, with reasons given per-row
above.

---

## 5. Conclusion

Of the 40 audited semantics: **19** are `FROZEN_EXPLICIT`, **9** are
`FROZEN_DERIVABLE_ENGINEERING`, **0** are `HISTORICAL_PRECEDENT_ONLY` as a
sole classification (two rows cite historical precedent that was explicitly
ruled non-authoritative and folded into an `UNFROZEN_SCIENTIFIC_DECISION`
verdict instead), and **12** are `UNFROZEN_SCIENTIFIC_DECISION`. No row was
`NOT_REQUIRED` — every audited semantic is on the critical path to a
production benchmark-case execution.

Twelve genuine scientific-decision surfaces remain open, all clustered around
the same root cause: **no case-to-search adapter and no case-level seed/
selection layer have ever been written or specified**, for either partition.
These are not implementation defects to be patched during engineering; per
`e54364b`'s own framing (independently upheld here), specifying them now,
prospectively and blind to every partition, is exactly what an RC5 amendment
must do before any RC5 engineering release can claim conformance.

```
======================================================================
RC5 HAS UNFROZEN SCIENTIFIC EXECUTION SEMANTICS
======================================================================
```
