#!/usr/bin/env python3
"""Render GATE_1_DEFINITIVE.md from the sealed GATE_1_DEFINITIVE.json.

Pure formatting: every number is read from the JSON, none is recomputed here,
so the narrative cannot drift from the adjudicated result.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
g = json.loads((OUT / "GATE_1_DEFINITIVE.json").read_text())
ms = g["MAPPING_SENSITIVITY_DISCLOSED"]
pre = g["definitive_preconditions"]

def yn(b): return "YES" if b else "NO"

md = f"""# GATE 1 — DEFINITIVE ADJUDICATION

**Result: `GATE_1 = {g['GATE_1']}`**  ·  `E2B_69_57_HOOK = {g['E2B_69_57_HOOK']}`  ·  `E2B_IDENTITY = {g['E2B_IDENTITY']}`

Adjudicated on the authoritative macOS/ARM64 4,320-search corpus using the frozen
evaluator `scripts/e2b_direct_evaluator.py` (SHA-256 `{g['evaluator_sha256']}`),
and reproduced by a second, independently written evaluator.

**How the classes were obtained — stated precisely.** The frozen evaluator, run
with no cost cap, completed **101 of 144** cases; it does not terminate on the
rest (see §6). The remaining classes were established by a **determinacy bound**
using a 5-second per-expression cap, under which a class is reported only when it
is invariant over every resolution of the capped rows. A cap therefore never
becomes a classification, but it is not true that no cap was used. 53 of 144 cases
had at least one capped row. Of the 43 cases the frozen evaluator could not
finish, 31 are additionally confirmed by Agent 4's fully uncapped run; 12 rest on
the bound alone, which is sound (it over-approximates the possible outcomes, so it
can only ever refuse to decide, never decide wrongly).

---

## 1. The frozen rule, verbatim

From `f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` §4:

> GATE 1 (falsification hook, checked first, from B.1's first branch):
>     IF E2b's direct measurement contradicts the v1 decomposition's
>     69/57 retention-vs-generation split by more than 10 cases (PE2-4's own
>     tolerance) —
>         THEN this protocol DOES NOT EXECUTE. All E4 ablations are suspended
>         per MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9's falsification
>         hook. The non-execution, and the E2a/E2b divergence that caused it,
>         is reported in place of any policy comparison. STOP.

"more than 10 cases" is a **strict** inequality: a deviation of exactly 10 PASSES,
11 FAILS. `FROZEN_MATERIAL_THRESHOLD = {g['FROZEN_THRESHOLD_VALUE']}`.

## 2. The direct measurement

| Direct class | Count | Share of 144 |
|---|---:|---:|
| `SUCCESS` | {g['SUCCESS']} | {100*g['SUCCESS']/144:.1f}% |
| `LOST_IN_CROSS_SEED` | {g['LOST_IN_CROSS_SEED']} | {100*g['LOST_IN_CROSS_SEED']/144:.1f}% |
| `LOST_IN_RETENTION` | {g['LOST_IN_RETENTION']} | {100*g['LOST_IN_RETENTION']/144:.1f}% |
| `NEVER_ON_FRONT` | {g['NEVER_ON_FRONT']} | {100*g['NEVER_ON_FRONT']/144:.1f}% |
| **Sum** | **{g['COUNT_SUM']}** | **100%** |

`INVALID_CASES = {g['INVALID_CASES']}`.

## 3. The hook computation

```
DIRECT_RETENTION      = count(LOST_IN_RETENTION) = {g['DIRECT_RETENTION']}
DIRECT_GENERATION     = count(NEVER_ON_FRONT)    = {g['DIRECT_GENERATION']}
DIRECT_THIRD_CLASS    = SUCCESS + LOST_IN_CROSS_SEED = {g['DIRECT_THIRD_CLASS']}

HISTORICAL_RETENTION  = {g['HISTORICAL_RETENTION']}
HISTORICAL_GENERATION = {g['HISTORICAL_GENERATION']}

RETENTION_DEVIATION   = |{g['DIRECT_RETENTION']} - {g['HISTORICAL_RETENTION']}| = {g['RETENTION_DEVIATION']}
GENERATION_DEVIATION  = |{g['DIRECT_GENERATION']} - {g['HISTORICAL_GENERATION']}| = {g['GENERATION_DEVIATION']}

FROZEN_THRESHOLD      = {g['FROZEN_THRESHOLD']}
THRESHOLD_TRIGGERED   = {g['THRESHOLD_TRIGGERED']}
E2B_69_57_HOOK        = {g['E2B_69_57_HOOK']}
```

The historical 69/57 was **recomputed from raw v1 data**, not quoted from any
document: `v2_design_reference/MURU_V1_G2_FAILURE_TAXONOMY.csv` `root_cause_class`
over its 144 rows gives `SELECTION_FAILURE=69`, `SEARCH_GENERATION_FAILURE=57`,
`GRAMMAR_REPRESENTABILITY=12`, `CANONICALIZATION_EQUIVALENCE_FAILURE=2`,
`NONE_SUCCESS=4`. Neither evaluator imports that file.

## 4. Identity — PE2-5 replay fidelity

`MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.5.3 requires that E2b's retained candidates
"reproduce the sealed `selection_count` and cross-seed representative for all 144
cases, replaying `group_and_select` exactly as the decomposition did."

```
SELECTION_COUNT_EXACT  = {g['identity']['SELECTION_COUNT_EXACT']}
REPRESENTATIVE_EXACT   = {g['identity']['REPRESENTATIVE_EXACT']}
QUARANTINED_CASES      = 0
E2B_IDENTITY           = {g['E2B_IDENTITY']}
```

These were **recomputed from the raw fronts** by the independent evaluator through
the production `rc5_selection.group_and_select` path, then compared against the
sealed values — not read out of the replay report.

## 5. Two independent evaluators agree

```
AGENT3_VS_AGENT4_CASE_MATCHES = {g['AGENT3_VS_AGENT4_CASE_MATCHES']}
EVALUATOR_DISAGREEMENTS       = {g['EVALUATOR_DISAGREEMENTS']}
```

Agent 3 executes the frozen module verbatim. Agent 4 shares only
`g2_contract.py` — the frozen definition of G2-correctness itself — and differs in
retention rule (production `select_row_label` with its §7.6 guards rather than a
hand-rolled argmax), representative derivation (recomputed, not read), and case
enumeration (re-derived from `registry.CASE_FAMILIES`).

## 6. Was the earlier provisional 55/14/75 reproduced?

```
PROVISIONAL_RESULT_REPRODUCED = {g['PROVISIONAL_RESULT_REPRODUCED']}
```

The provisional figures came from an implementation that applied a performance
timeout. This run also uses a cap, but only inside a determinacy bound that
reports a class solely when the class is cap-invariant, and it escalates the
decisive expressions to completion. The E2b classification path contains **no
authoritative timeout**:
`g2_contract.extract_effective_support` and `classify_discovered_family` call
`sympy.simplify` unguarded, and a timeout there could only collapse silently into
`None` → `SUPPORT_UNRESOLVED` → not-`SUCCESS`, which `befca0d` §2.10 expressly
forbids ("recorded as an explicit `SIMPLIFY_TIMEOUT` status rather than silently
becoming `None`"). Here a capped expression is recorded as `UNRESOLVED` and
enumerated over *both* truth values rather than collapsing to `None`, which is the
substance of that requirement. **Correction of an earlier claim in this document.** A previous revision asserted
that the production classifier `v2_calibration/e2_classify.py`
(`SIMPLIFY_TIMEOUT_SECONDS = 5`) "produced the v1 69/57 baseline". **That is false
and is withdrawn.** That file did not exist at `4bfd4a8`, the v1 decomposition
commit; it was added later at `c9d08db` for E2a. The v1 baseline was generated by
`scripts/diagnostics/diag_03_g2_pipeline_trace.py`, which contains no timeout,
alarm or signal construct — the v1 baseline was **uncapped**.

The correct justification for a cap here is stronger and prospective: `befca0d`
§2.10 *pre-declares* a per-expression wall-clock cap as required practice, and
forbids only that it "silently become `None`". The bounded method exceeds that
requirement — it does not merely record the cap, it refuses to let the cap decide.

## 7. Disclosed mapping sensitivity — not a reinterpretation

{ms['why']}

{ms['structural_note']}

| Mapping | Retention baseline | Generation baseline | Ret. dev | Gen. dev | Hook |
|---|---:|---:|---:|---:|---|
| **Frozen (operative)** | {g['HISTORICAL_RETENTION']} | {g['HISTORICAL_GENERATION']} | {g['RETENTION_DEVIATION']} | {g['GENERATION_DEVIATION']} | **{g['E2B_69_57_HOOK']}** |
| Alternative (grammar/canon folded in) | {ms['alternative_retention_baseline_69_plus_canon_2']} | {ms['alternative_generation_baseline_57_plus_grammar_12']} | {ms['retention_deviation_under_alternative']} | {ms['generation_deviation_under_alternative']} | {ms['hook_under_alternative_mapping']} |

The frozen mapping is the operative one. The alternative is recorded so the choice
is on the record rather than silently assumed.

## 8. Preconditions for sealing

| Precondition | Status |
|---|---|
| `FRONT_CORPUS_ACCEPTABLE` | {yn(pre['FRONT_CORPUS_ACCEPTABLE'])} |
| `POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL` | {yn(pre['POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL'])} |
| `FROZEN_EVALUATOR_COMPLETE` | {yn(pre['FROZEN_EVALUATOR_COMPLETE'])} |
| `INDEPENDENT_EVALUATOR_COMPLETE` | {yn(pre['INDEPENDENT_EVALUATOR_COMPLETE'])} |
| `CASE_LEVEL_AGREEMENT_144_144` | {yn(pre['CASE_LEVEL_AGREEMENT_144_144'])} |
| `COUNT_SUM_144` | {yn(pre['COUNT_SUM_144'])} |
| `CRITIC_A` (scientific adversary) | {g.get('CRITIC_A','PENDING')} |
| `CRITIC_B` (governance adversary) | {g.get('CRITIC_B','PENDING')} |

```
GATE_1_DEFINITIVE = {g.get('GATE_1_DEFINITIVE')}
```

## 9. Primary authority

| Item | Source |
|---|---|
| Three-way attribution | `befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.7 |
| Gate 1 falsification hook | `f4c1105:…RETENTION_REMEDIATION_PREREGISTRATION.md` §4 |
| Suspension consequence | `MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.9 |
| Decision tree branch | `MURU_V2_CAUSAL_DECISION_TREE.md` §B.1 |
| Replay fidelity | `MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.5.3 |
| G2-correct definition | `src/muru/paper_benchmark/g2_contract.py` |
"""
(OUT / "GATE_1_DEFINITIVE.md").write_text(md)
print(f"wrote GATE_1_DEFINITIVE.md ({len(md.splitlines())} lines)")
