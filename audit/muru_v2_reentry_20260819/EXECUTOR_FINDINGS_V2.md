# Executor findings against protocol v2, raised during Stage 1 construction

These are found by BUILDING the thing the protocol specifies, which is a different
attack surface from reading it. They are offered to the same repair round as the
CRITIC_SCIENCE / CRITIC_GOVERNANCE findings.

## X-1 (CRITICAL) — P8 / TRUTH_BLIND_BOUNDARY is unsatisfiable as written, so QUALIFIED is unreachable

**Where.** Section 16: *"a static import check asserts that no module reachable from the
search entry point imports anything truth-derived (`g2_contract`, the oracle, the truth
registry, `discovery.equivalence`)"*. Section 12: *"Execution path:
`paper_benchmark/rc5_runner`, the **real v1 production path**"*. Section 20: `P8` is a
conjunct of `QUALIFIED`.

**The contradiction, verified in the code.**

    src/muru/paper_benchmark/rc5_runner.py:48     from .g2_contract import (...)
    src/muru/paper_benchmark/rc5_selection.py:77  from .g2_contract import GRAMMAR_PRIMITIVES, _safe_parse

Section 12 mandates the entry point; section 16 forbids what that entry point imports;
section 20 makes the prohibition a hard precondition. **No implementation can satisfy all
three**, including the production path itself. This is v1's fatal defect class -- an
unreachable positive terminal -- re-entering through a different door.

Worse, section 14 lists `effective_support` (field 18) and `template_key` (field 19) as
**search-side** fields persisted *before* retention, and `extract_effective_support` is
**defined in `g2_contract`** (`g2_contract.py:138`). The protocol therefore requires the
search path to compute a field from a module the same protocol forbids it to import.

**Why the module-level test is the wrong test.** `g2_contract` mixes two kinds of function:

| symbol | signature | truth-dependent? |
|---|---|---|
| `extract_effective_support(expr_str)` | expression only | **no** -- pure syntax |
| `classify_discovered_family(expr_str)` | expression only | **no** -- pure syntax |
| `classify_support(discovered, truth_support)` | takes truth | **yes** |
| `classify_family_match(discovered_family, truth_family)` | takes truth | **yes** |
| `evaluate_g2_event(support_status, family_status)` | truth-derived inputs | **yes** |
| `truth_support_for_case(...)` | truth | **yes** |

An import-level ban is simultaneously too strong (it bans syntax helpers the search
legitimately needs, and which cannot leak truth because truth is not among their arguments)
and too weak (importing nothing proves nothing about whether a `TruthRecord` field reaches
the design matrix).

**The leak that actually matters is data flow, and it is currently clean.** The design is
built by `rc5_adapter.build_case_design(compounds, scalars)` where
`scalars = rc5_estimate.estimate_case_scalars(compounds, trajectories)`. `g` is **estimated
from the observed trajectories**, never read from `truth.g_by_compound`. So the search is
truth-blind in the sense that matters; only the stated *test* is wrong.

**Minimal repair (does not weaken the scientific content).** Replace the module-import test
with a two-part test that is both satisfiable and strictly stronger where it counts:

1. **Symbol-level ban.** The search entry point's reachable import graph may not bind any of
   `classify_support`, `classify_family_match`, `evaluate_g2_event`, `truth_support_for_case`,
   `classify_expression`, `algebraically_equivalent`, or any name from the oracle / truth
   registry. The syntax-only helpers `extract_effective_support`,
   `classify_discovered_family`, `_safe_parse`, `GRAMMAR_PRIMITIVES`, `template_key` are
   explicitly permitted and enumerated.
2. **Data-flow assertion.** No field of `TruthRecord` may appear in the object graph reachable
   from `CaseDesign`. Asserted at runtime for every world, not once in preflight.

Because `rc5_runner` *does* bind the truth-dependent symbols at module scope, the search entry
point must be a **separate module** that reuses the truth-blind functions directly
(`build_case_design`, `estimate_case_scalars`, `build_case_regressor`, `select_row_label`)
and never imports `rc5_runner`. Section 12's equivalence requirement is then discharged where
it was always actually discharged -- by **control C-1**, which requires the instrumented
engine's `argmax(score)`-retained candidate to be **byte-identical** to the production path's
on the section 28 control set. C-1 tests the thing section 12 cares about (identical search
semantics) by measurement rather than by an import-path proxy that does not imply it.

**Status: this repair changes no threshold, definition, population, denominator or decision
rule. It changes a mis-specified test into a satisfiable and stricter one.**

## X-2 (MED) — FP-3 x FP-4 exceed the host, so the RSS ceiling cannot bind as claimed

Section 34 freezes `RSS_CEILING_GIB = 24` (FP-3) and `WORKER_COUNT = 8` (FP-4), and argues
FP-3 is chosen "below the 25 GiB at which Gate 1 lost cases, so the in-process ceiling fires
before the kernel does". At `WORKER_COUNT = 8` the admissible envelope is `8 x 24 = 192 GiB`
on a **47 GiB** host with no swap. Two concurrent workers near the ceiling exhaust the host,
so **the kernel still fires first** and the stated guarantee does not hold. FP-3's "Where it
can affect a verdict: Nowhere" depends on that guarantee.

The consequence is bounded -- section 25.4 routes exhaustion to an operational non-terminal
that emits no scientific state, and the Stage 0 incident confirms an environment kill lands
on `UNRESOLVED` rather than a label -- so this is a **liveness** defect, not a validity one.
But the justification in section 34 is wrong as stated. Repair: either bind
`WORKER_COUNT * RSS_CEILING_GIB <= usable host RAM` as a preflight assertion, or restate
FP-3's rationale as per-worker runaway containment rather than pre-emption of the kernel.

## X-3 (CRITICAL) — Stage 1's classifier is unspecified, and the obvious choice re-commits the Gate 1 defect

**Where.** Section 13 `A2`: *"No wall-clock cap may assign a label, anywhere.
`SIMPLIFY_TIMEOUT_SECONDS = 5` is **retired as a classification rule** under this protocol."*
Section 14 lists `effective_support` (field 18) and `template_key` (field 19) as **search-side**
fields persisted **before retention**. Section 17 governs the *scoring* pass. **No section says
which classifier computes the search-side fields 18 and 19.**

The only existing module that persists a full front with those fields is
`src/muru/v2_calibration/e2_search.py`, and at line 192 it calls
`e2_classify.classify_expression`, which enforces `SIMPLIFY_TIMEOUT_SECONDS = 5`
(`e2_classify.py:92`). **Executing Stage 1 with the existing front-capture module therefore
violates `A2` on the first world**, and re-commits the precise defect Gate 1 was convened to
adjudicate.

**The defect, in the two lines that cause it** (`e2_classify.py:161-162`):

```python
effective_support   = extract_effective_support(expression_string)  if canonicalization_status == "OK" else None
discovered_family   = classify_discovered_family(expression_string) if canonicalization_status == "OK" else None
```

Note what this actually does. Both functions take **`expression_string` and nothing else**;
neither consumes `simplified`. They are pure syntactic functions of the candidate. Yet both
are **gated on whether `sympy.simplify` returned within 5 seconds** — an unrelated
computation. A wall-clock event on `simplify` nulls two fields **that never depended on
`simplify` in the first place**, and `None` effective support propagates to
`SUPPORT_UNRESOLVED` -> `g2_correct = False`. The label is not merely time-dependent; the
time-dependence is **gratuitous**.

This also explains the measured asymmetry cleanly: the cap fires more often on expressions
that are expensive to canonicalise, and the loss is monotone toward the earlier stage, which
is why E2a's contamination ran 73/122 = 59.8% in stage A against 1/119 = 0.8% in stage E.

**Minimal repair.** Stage 1 must use a calibration classifier that implements section 25
rather than the retired cap:

1. Compute `effective_support` and `classify_discovered_family` **unconditionally**, since
   they are pure functions of `expression_string`. This alone removes most of the coupling
   and is strictly a bug fix — it cannot change any value that was previously computed, only
   supply values that were previously nulled.
2. Replace the 5 s SIGALRM with section 25's two-tier budget (`FP-2` = 60 s CPU tier 1,
   tier 2 uncapped) and record exhaustion as an explicit `UNRESOLVED` **resolution state**,
   never as a status that nulls a field.
3. `e2_classify.py` **must not be edited** — it is the sealed E2a instrument and changing it
   would retroactively alter sealed E2a semantics. The calibration classifier is a new module.

**Consequence if unrepaired:** `P5 HOST_INVARIANT_LABELS` fails by construction, so
`QUALIFIED` is unreachable — the same terminal-reachability failure as `X-1`, reached by a
third route.
