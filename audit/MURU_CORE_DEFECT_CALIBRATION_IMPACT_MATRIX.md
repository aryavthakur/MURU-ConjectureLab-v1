# MURU Core-Defect Repair -> Calibration Impact Matrix

**Document ID:** `MURU-AUDIT-CORE-DEFECT-CALIBRATION-IMPACT-01`
**Classification:** `CONDITIONAL_ANALYSIS_ONLY`
**Status:** `AUDIT_COMPLETE`
**Mode:** `READ_ONLY`. No repair was made. No recalibration was executed. Development
was not opened. Held-out was not opened.
**Repository state audited:** `07f43d3` on `audit/muru-rc5-execution-semantics-authority-audit`

**Governing state at audit time (per [[muru-a3-1-state]]):**

| Item | Ref |
|---|---|
| A1-A3.4 science freeze | frozen; A3.4 = `be23b80` / `benchmark-content-freeze-a3-4` |
| RC4 engineering freeze | `c800e7a` |
| A3.2 calibration | executed `VALID`, preserved (`44e5e36`) |
| `threshold_table.json` comparator | active (`compute_threshold_table`, `calibration_contract.py:280`) |
| RC5 case-execution path | does not exist (confirmed independently in `audit/MURU_RC5_EXECUTION_SEMANTICS_AUTHORITY_AUDIT.md`) |

This document does not assume R1-R4 are real defects. It asks a narrower
question: **if each were required, would the calibration that already ran
and is already preserved need to be redone?**

---

## 0. Method

For each repair, the calibration data-flow was traced forward from source:

```
build_world()                    rc3_calibration_worlds.py
  -> compounds, target                (frozen law + A3.2 permutation, A3.2 split)
  -> CalibrationWorld.design_matrix() (plain np.ndarray, CALIBRATION_COVARIATE_ORDER)
PySRBackend.search()             rc3_calibration_runner.py:827
  -> model.fit(design[train], target[train])
  -> equations["complexity"]          (PySR's own column, read only as int)
  -> model.predict(design[validation], index=row)
  -> _r2(target[validation], predictions)
  -> SearchOutcome.best_valid_r2_by_complexity
run_seed() / run_world()         rc3_calibration_runner.py
  -> SeedResult.status, .best_valid_r2_by_complexity
compute_world_null_statistic()   calibration_contract.py:190
  -> S(w, c) per world
compute_threshold_table()        calibration_contract.py:280
  -> threshold_table.json
```

and reverse-checked by import graph: every module R1-R4 live in was checked
for whether it is imported by, or imports, any module in the chain above.

```
calibration_contract.py      imports: hashlib, dataclasses, enum, typing, numpy   (no paper_benchmark siblings)
rc3_calibration_worlds.py    imports: .calibration_contract, .g2_contract.GRAMMAR_PRIMITIVES (constant only), .generator
rc3_calibration_runner.py    imports: .calibration_contract, .rc3_calibration_worlds, .rc3_provenance
```

`GRAMMAR_PRIMITIVES` is the *only* edge between the calibration chain and
any module R1-R4 touch. It is a five-string tuple (`"mass"`, `"descriptor"`,
`"descriptor2"`, `"distractor"`, `"correlated_distractor"`) declared under
g2_contract.py's "Protected grammar primitives" section (`g2_contract.py:44-53`),
consumed by `rc3_calibration_worlds.py` only as `CALIBRATION_COVARIATE_ORDER`
(`rc3_calibration_worlds.py:142`), i.e. as a column-order label for
`design_matrix()`. None of R1-R4, as stated, proposes to change this tuple's
membership, count, or order; each targets logic that sits *after* the tuple
is defined (parsing of already-produced expression strings, event
classification, a truth operand). This edge is therefore inert for all four
repairs and is flagged explicitly per-repair below rather than assumed away.

---

## 1. R1 - correct orientation/sign of `protocol.estimate_one`

**Location:** `src/muru/paper_benchmark/protocol.py:31-38`

```python
def estimate_one(frozen: FrozenScalarObjects, compound_rows: pd.DataFrame) -> ScalarEstimate:
    ...
    residual = float(np.nanmean(observed - baseline))
    log_g = float(np.clip(-residual, *frozen.support))
```

`estimate_one` and its companion `fit_training_scalar` (`protocol.py:24-28`)
are the frozen fold-local scalar adapter for the **G1 scalar-competence**
endpoint (`g_spearman`, `analysis.py:47`) — a case-level quantity computed
from real held-out compound rows against a per-fold training mean profile.
It has no defined relationship to the calibration null statistic at all.

**Reference check.** `git grep -n "estimate_one\|fit_training_scalar" -- src/ tests/` returns
exactly two production references, both inside `protocol.py` itself (its own
definitions), plus test-only call sites (`tests/test_paper_benchmark_protocol.py`,
`tests/test_paper_benchmark_adequacy.py:400,408`). **No file under
`rc3_calibration_worlds.py`, `rc3_calibration_runner.py`, or
`calibration_contract.py` imports `protocol.py`, and `protocol.py` imports
nothing from any of them.** `CalibrationWorld.target` is built exclusively by
`_base_target()` (`rc3_calibration_worlds.py:276-306`), which calls
`frozen_law_target()` -> `generator._law()` and a permutation RNG — never
`estimate_one`.

| Question | Answer | Basis |
|---|---|---|
| Alter A3.2 world generation? | **No** | `build_world` (`rc3_calibration_worlds.py:366`) never calls `protocol.py`. |
| Alter the PySR target? | **No** | `CalibrationWorld.target` comes from `_base_target`, not `estimate_one`. |
| Alter any candidate expression? | **No** | `PySRBackend.search` (`rc3_calibration_runner.py:827`) never touches `protocol.py`. |
| Alter `valid_r2`? | **No** | Calibration's per-seed validation R2 (`_r2`, `rc3_calibration_runner.py:750`) is computed from `design`/`target`, unrelated to `log_g`. The separate, still-unimplemented case-level `valid_r2` field (`rc3_record.py`, RC5 audit item #21) is untouched by R1 for an independent reason: nothing computes it yet, regardless of R1. |
| Alter complexity? | **No** | `equations["complexity"].iloc[row]` (`rc3_calibration_runner.py:846`) is PySR's own reported column. |
| Alter per-complexity S(w,c)? | **No** | `compute_world_null_statistic` (`calibration_contract.py:190`) is a pure function of `SeedResult`, which is a pure function of the untouched search above. |
| Alter `threshold_table.json`? | **No** | `compute_threshold_table` (`calibration_contract.py:280`) is a pure function of `world_statistics`, unaffected transitively. |
| Only downstream case scoring? | **Yes** | Once wired, a sign fix changes `log_g` per compound, hence `g_spearman`, hence `CaseOutcome.scalar_competent` (`analysis.py:47`) — G1 only. |
| Existing thresholds remain valid comparator? | **Yes** | Gate 2 (`structural_acceptance.py:198-210`), the only acceptance gate reading calibration output, reads `candidate.valid_r2` and `null_threshold`; neither depends on `estimate_one`. |

### Classification: `CALIBRATION_PROVABLY_UNAFFECTED`

**Proof.** Zero import edge, zero data-flow edge, in either direction,
between `protocol.py` and any of `calibration_contract.py`,
`rc3_calibration_worlds.py`, `rc3_calibration_runner.py`. The calibration
target is a permuted synthetic-law vector; `estimate_one` is never in that
computation's call graph. A sign correction changes only the G1 endpoint,
which is not evaluated on calibration worlds (calibration worlds have no
compounds subjected to A1/G1 case scoring at all — `run_calibration`
(`rc3_calibration_runner.py`) never imports `adequacy` or `analysis`).

---

## 2. R2 - bind/implement F07 G3 event semantics

**Location:** `src/muru/paper_benchmark/analysis.py:81-90` (legacy `classify_negative_control`,
`family.code == "F07"` at line 83), `src/muru/paper_benchmark/g3_contract.py`
(A3.1 frozen G3 reference contract, `score_g3` at line 220), and
`MURU_PAPER_BENCHMARK_METRICS.md:16-22,69-71` (G3 = F07(12) + F19(12) +
F20(12) = 36; `g3_contract.py`'s own docstring at lines 3-6 currently
describes only F19+F20, which is itself evidence of the alleged unbound-F07
defect — noted here as context, not adjudicated).

Whichever way F07's G3 classifier is bound or implemented, it is an event
classification over an **already-computed** `AcceptanceResult` plus
discovered family/support for a **real production case** in the F07 family
(`registry.py:141`, `"mass-only g truth"`). It has no calibration-world
counterpart: calibration worlds are anonymous null constructions with no
family code, no F07/F19/F20 identity, and no G3 opportunity at all.

**Reference check.** `g3_contract.py` imports only `.structural_acceptance`
and `.g2_contract` (`g3_contract.py:25-26`). `analysis.py` imports only
`.adequacy` and `.registry` (`analysis.py:8-9`). Neither is imported by, nor
imports, `calibration_contract.py`, `rc3_calibration_worlds.py`, or
`rc3_calibration_runner.py`. `structural_acceptance.py` imports only
`.adequacy` (`structural_acceptance.py:24`) — it has no path back into
calibration either.

| Question | Answer | Basis |
|---|---|---|
| Alter A3.2 world generation? | **No** | No import edge; calibration worlds carry no family/variant identity for G3 to act on. |
| Alter the PySR target? | **No** | Same. |
| Alter any candidate expression? | **No** | Same; calibration's `PySRBackend.search` never constructs `AcceptanceResult` or any G3 event. |
| Alter `valid_r2`? | **No** | G3 reads `AcceptanceResult`, which reads `valid_r2` (via Gate 2) but never writes back to it. |
| Alter complexity? | **No** | Same directionality argument. |
| Alter per-complexity S(w,c)? | **No** | `compute_world_null_statistic` has no dependency on `g3_contract.py`/`analysis.py`. |
| Alter `threshold_table.json`? | **No** | Transitively unaffected. |
| Only downstream case scoring? | **Yes** | F07/G3 binding changes only the `G3Event` classification and the aggregate `score_g3` (`g3_contract.py:220-243`) for F07/F19/F20 held-out cases. |
| Existing thresholds remain valid comparator? | **Yes** | G3 is computed *from* accepted/rejected verdicts that already used the threshold table; it cannot revise the table that produced them. |

### Classification: `CALIBRATION_PROVABLY_UNAFFECTED`

**Proof.** The dependency arrow runs one way only:
`threshold_table.json` -> Gate 2 -> `AcceptanceResult` -> G3 event. There is
no arrow from G3/F07 semantics back into calibration. Binding F07 cannot
retroactively change which cases were accepted (that used the threshold
table as-is); it can only change how already-accepted or already-rejected
F07 cases are scored for safety.

---

## 3. R3 - repair parser/support/canonicalization (cancelled variables; PySR feature-name mapping)

**Location:** `src/muru/paper_benchmark/g2_contract.py`: `_safe_parse`
(line 81), `extract_effective_support` (line 93), `classify_discovered_family`
(line 149), all built on `_PRIMITIVE_SYMBOLS` (line 53) and SymPy `simplify`.

This module is explicitly self-scoped: *"This module is the REFERENCE
CONTRACT implementation. It does not integrate into the production
execution path... This module NEVER reads planted truth during
acceptance."* (`g2_contract.py:14-20`).

**The feature-name half of R3, checked directly against the calibration backend.**
`PySRBackend._make_regressor` (`rc3_calibration_runner.py:803-825`) builds
`PySRRegressor(...)` with no `variable_names` argument, and
`PySRBackend.search` (`rc3_calibration_runner.py:827-865`) calls
`model.fit(design[train], target[train])` where `design =
world.design_matrix()` is a bare `np.ndarray` (`rc3_calibration_worlds.py:213-217`,
built by `np.column_stack`, which carries no column names). Confirmed by
`grep -n "variable_names\|feature_names" src/muru/paper_benchmark/*.py` ->
no match anywhere in the package. This means calibration's PySR equations
are internally named `x0..x4` and **calibration never reads the equation
text at all** — `search()` extracts only `equations["complexity"].iloc[row]`
(line 846, an integer PySR itself reports) and
`model.predict(design[validation], index=row)` (line 856, a numeric
prediction vector). The discovered symbolic expression string is computed by
PySR internally but is never assigned to a variable, never stored, and never
passed to `g2_contract._safe_parse` anywhere in the calibration call graph.
So the "x0-to-mass" feature-name mapping R3 would fix is a defect in a
**case-level adapter that does not exist yet** (RC5 audit item #1, #9, #10 —
`UNFROZEN_SCIENTIFIC_DECISION`), not in anything calibration currently does.

The cancelled-variable half of R3 (SymPy `simplify` correctly excluding
algebraically cancelled terms from `free_symbols`) is likewise confined to
`extract_effective_support`, invoked only by G2 scoring
(`rc3_scoring.py:27-33` imports `g2_contract` for exactly this) and by
Gate 6 of `structural_acceptance.py` (`effective support non-empty`,
line 233-238) through `rc3_acceptance.candidate_from_record`
(`rc3_acceptance.py:66-79`, which reads `record.effective_support` — a
**case-record field**, never a calibration-world field; `CalibrationWorld`
has no `effective_support` attribute at all, confirmed:
`rc3_calibration_worlds.py`'s `CalibrationWorld` dataclass, lines 205-212,
has exactly `world_id, construction, index, compounds, target, seeds`).

**Scope caveat considered and ruled out.** The one identifier R3's target
modules share with calibration is `GRAMMAR_PRIMITIVES`
(`g2_contract.py:44-53`), reused as `CALIBRATION_COVARIATE_ORDER`
(`rc3_calibration_worlds.py:142`). R3 as specified repairs *parsing/support
logic*, not the *primitive name inventory* — the inventory is declared
separately, above the parsing functions, under "Protected grammar
primitives," and is not itself alleged defective. If a hypothetical
implementation of R3 also silently changed the count or order of
`GRAMMAR_PRIMITIVES`, that would be a **different, unscoped change** outside
R3 as stated, and would require independent re-audit (it would alter
`design_matrix()`'s column count/order and therefore genuinely require
recalibration). Under R3's stated scope — parser, support extraction,
feature-name mapping — this edge is inert.

| Question | Answer | Basis |
|---|---|---|
| Alter A3.2 world generation? | **No** | `GRAMMAR_PRIMITIVES` content/order untouched by a parser/mapping repair; see caveat above. |
| Alter the PySR target? | **No** | `CalibrationWorld.target` never touches `g2_contract.py`. |
| Alter any candidate expression? | **No** | `PySRBackend.search` never parses or stores equation text; only `complexity` (int) and numeric predictions. |
| Alter `valid_r2`? | **No** | Calibration's validation R2 comes from `_r2(target[validation], predictions)` (`rc3_calibration_runner.py:750,859-863`), numeric only. |
| Alter complexity? | **No** | `equations["complexity"]` is PySR's own column, read as-is. |
| Alter per-complexity S(w,c)? | **No** | Pure function of the above. |
| Alter `threshold_table.json`? | **No** | Pure function of S(w,c) across 100 worlds. |
| Only downstream case scoring? | **Yes** | Affects `extract_effective_support`/`classify_discovered_family` for real cases only, feeding G2 (`rc3_scoring.py`) and Gate 6 of case-level acceptance. |
| Existing thresholds remain valid comparator? | **Yes** | Gate 2's comparator (`valid_r2 > null_threshold[complexity]`) is arithmetic on numbers computed before any parsing occurs; Gate 6 is a separate, later gate in the same predicate and does not feed back into Gate 2's inputs. |

### Classification: `CALIBRATION_PROVABLY_UNAFFECTED`

**Proof.** Calibration's search backend is provably blind to symbolic
expression text: it consumes exactly two outputs per Pareto row —
`equations["complexity"]` (int) and `model.predict(...)` (float array) — and
both are computed by PySR/SymbolicRegression.jl internals, not by any
function R3 would touch. The parser/support/family-classification code R3
repairs operates only on `expr_str` arguments that are supplied by a
case-level caller (`rc3_scoring.py`, `rc3_acceptance.py` via
`CaseExecutionRecord`), a caller which — per the independent RC5 audit —
does not yet exist for calibration and never has for calibration (calibration
was never designed to run G2 at all: `g2_contract.py:14-20` states this
directly).

---

## 4. R4 - supply the canonical truth-support operand for G2

**Location:** `truth_support: frozenset[str]` (`rc3_record.py:221`),
consumed by `g2_contract.classify_support(discovered_support, truth_support)`
(`g2_contract.py:132-141`).

`truth_support` is the planted-truth structural-support set for a **real
production case with a genuine planted law** (Development/Held-out, drawn
from `generator._law`/`objval/truth2.py` families). `rc3_acceptance.py`
states directly: *"`truth_family` and `truth_support` are read nowhere in
this module"* (`rc3_acceptance.py:16-17`) — truth-blindness of the
acceptance predicate is enforced by construction, not merely by convention;
`TRUTH_BLIND_FIELDS` (`rc3_acceptance.py:44-48`) explicitly excludes both.

Calibration worlds have **no planted truth to be canonical about**. Each of
the three null constructions (`target_permuted_across_compounds`,
`descriptors_permuted_across_compounds`,
`gaussian_targets_with_observed_variance`,
`rc3_calibration_worlds.py:388-405`) is, by A3.1/A3.2 design, a structural
null: the target's association to every covariate is deliberately destroyed
before any search runs. There is no "true support" for a null world to
compare against — the concept is undefined for this data, not merely
unsupplied.

| Question | Answer | Basis |
|---|---|---|
| Alter A3.2 world generation? | **No** | `build_world` has no truth-support parameter or dependency (`rc3_calibration_worlds.py:366-435`). |
| Alter the PySR target? | **No** | Same. |
| Alter any candidate expression? | **No** | `PySRBackend.search` never reads `truth_support`. |
| Alter `valid_r2`? | **No** | Numeric-only computation, as in R3. |
| Alter complexity? | **No** | PySR's own reported column. |
| Alter per-complexity S(w,c)? | **No** | Pure function of untouched search outputs. |
| Alter `threshold_table.json`? | **No** | Pure function of S(w,c). |
| Only downstream case scoring? | **Yes** | `truth_support` feeds only `classify_support` (`g2_contract.py:132`), which feeds only `evaluate_g2_event` (`g2_contract.py:255`), which feeds only `score_g2` (`rc3_scoring.py`). |
| Existing thresholds remain valid comparator? | **Yes** | The acceptance predicate that used the threshold table is proven truth-blind by `rc3_acceptance.py`'s own field projection; supplying `truth_support` cannot retroactively touch Gate 2. |

### Classification: `CALIBRATION_PROVABLY_UNAFFECTED`

**Proof.** `CalibrationWorld` (`rc3_calibration_worlds.py:205-212`) has no
truth-support-shaped field, and none of the three admitted null
constructions defines one implicitly (each is defined purely as a
transformation of `target`/`compounds`, `rc3_calibration_worlds.py:388-405`).
`truth_support` is structurally a case-record concept
(`rc3_record.py:221`) consumed by a module (`g2_contract.py`) that
self-declares it reads truth "only for post-hoc G2 scoring, which is
separated from the acceptance predicate by design" (`g2_contract.py:18-20`).
Calibration's threshold computation predates and does not depend on G2 at
all.

---

## 5. Summary table

| Repair | World gen | PySR target | Candidate expr | `valid_r2` | Complexity | S(w,c) | `threshold_table.json` | Downstream-only | Thresholds still valid | Classification |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 estimate_one sign | No | No | No | No | No | No | No | Yes | Yes | `CALIBRATION_PROVABLY_UNAFFECTED` |
| R2 F07/G3 semantics | No | No | No | No | No | No | No | Yes | Yes | `CALIBRATION_PROVABLY_UNAFFECTED` |
| R3 parser/support/feature-names | No | No | No | No | No | No | No | Yes | Yes | `CALIBRATION_PROVABLY_UNAFFECTED` |
| R4 G2 truth-support operand | No | No | No | No | No | No | No | Yes | Yes | `CALIBRATION_PROVABLY_UNAFFECTED` |

**All four hypothetical repairs, independently and jointly, are
`CALIBRATION_PROVABLY_UNAFFECTED`.** The preserved A3.2 `threshold_table.json`
remains a valid comparator against which any future case execution can be
scored, whether or not R1-R4 are ever repaired, and repairing all four
simultaneously would not require recalibration: the four repair sites share
no data or import edge with each other inside the calibration chain, so
their effects (all confined to downstream case/endpoint scoring — G1 for
R1, G3 for R2, G2 support/family for R3, G2 truth comparison for R4) do not
compose into any calibration-facing change either.

**What this does not say.** This matrix does not adjudicate whether R1-R4
are real defects, does not say the missing case-to-search adapter
(RC5 audit items #1, #9, #10, #13-19, #21, #23, #27, #39) is unrelated to
R1-R4 — several of R1-R4 are exactly the kind of gap that adapter's design
would need to close — and does not authorize any repair, Development
opening, or Held-out opening. It answers only the calibration-impact
question asked.

```
======================================================================
CORE-DEFECT CALIBRATION IMPACT MATRIX READY — NO RECALIBRATION EXECUTED
======================================================================
```
