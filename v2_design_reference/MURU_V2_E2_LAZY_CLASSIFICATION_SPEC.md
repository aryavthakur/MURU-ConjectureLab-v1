# MURU v2 E2 Rescue V2: Lazy Exact Classification Spec

**Status:** design + implementation document. Code:
`src/muru/v2_calibration/e2_rescue_v2/lazy_classify.py`. Tests:
`tests/test_lazy_classify_control_flow.py` (5/5 passing, synthetic-only).
Scientific fidelity against real data is validated separately by
`MURU_V2_E2_REPLAY_PARITY.json` (Part V), not by this document.

## 1. Where the brute-force cost actually is (recovered from source, not assumed)

`scripts/e2_run_shard.py::_run_all_worlds` calls, per world:

```
for k in range(30):                                   # every seed
    sr = e2_search.run_seed_search(...)                # classify_expression() called
                                                         # INSIDE this, once per front row
    scored_rows = [e2_scoring.score_row(fr, truth) for fr in sr.rows]  # EVERY row scored again
```

Two separate expensive symbolic calls happen for **every row of every
seed's front**, before `e2_aggregate.evaluate_world` ever looks at the
aggregate:

1. `e2_classify.classify_expression` (inside `run_seed_search`) -- up to
   one `sympy.simplify` per row, now capped at 5s by a hard process
   boundary (the 2026-08-16 rescue fix).
2. `discovery.equivalence.algebraically_equivalent` (inside `score_row`,
   for every row where `parse_ok` and `canonicalization_status == "OK"`)
   -- up to two more `sympy.simplify`-equivalent calls per row, **with NO
   wall-clock cap anywhere in its call path** (only a cheap `count_ops`
   early-out, `SIMPLIFY_TIMEOUT_TERMS`). This was never brought under the
   classify-hang rescue's process-boundary fix, because it isn't inside
   `classify_expression`. See section 5 for why this matters beyond speed.

`e2_aggregate.evaluate_world` itself (the stage-decision function) does
**no** further symbolic work -- it only reads `g2_correct`/`truth_equivalent`
fields already computed by the two calls above, for every row, whether or
not they end up mattering to the final label.

## 2. The exact minimal witness order (proof)

Recovered directly from `v2_design_reference/MURU_V2_E2_PREDECLARATION.md`
section 6 and `e2_aggregate.evaluate_world`'s own code (not assumed to
match the mission prompt's illustrative 6-step sketch, which this world
does not need beyond steps 1-3):

```
if n_correct_on_front == 0:            stage = A
elif n_retained_correct == 0:          stage = B
elif representative_g2_correct:        stage = E
elif representative_truth_equivalent:  stage = D
else:                                  stage = C
```

**Lemma 1.** `retained_by_argmax_score(row) => row in front`.
*Proof:* `e2_search.run_seed_search` marks `retained_by_argmax_score=True`
on exactly one element of the SAME `rows` list it returns as the front (the
element at `argmax_position`). It is not drawn from a different
population. Hence `retained_correct(seed) => correct_on_front(seed)`
trivially: the retained row, if correct, IS a correct row on the front.

**Lemma 2.** `group_and_select`'s winning class and representative are a
pure function of the 30 (or fewer) `RetainedCandidate` objects -- one per
seed, each built only from that seed's OWN retained row
(`rc5_selection.py::group_and_select`, reproduced in `e2_aggregate.build_seed_selections`).
It never reads any other row of any front.

**Theorem (witness order correctness).** The following two-phase procedure
computes `first_loss_stage`, `representative_g2_correct`, and
`representative_truth_equivalent` identically to `evaluate_world`, for
every world:

```
PHASE 1 (<=30 classify calls): classify each seed's retained row only.
    If ANY is g2_correct:
        # Lemma 1 => n_correct_on_front > 0 => not A.
        # this seed's own retained row being correct also directly gives
        # n_retained_correct > 0 => not B.
        compute the representative via group_and_select (Lemma 2: needs
        only the already-classified retained rows -- zero extra cost)
        if representative.g2_correct:               stage = E   (0 extra calls)
        else: check algebraically_equivalent(representative, truth) once
              stage = D or C accordingly              (exactly 1 extra call)
        STOP.
    If NONE is g2_correct: n_retained_correct == 0 (=> not E/D/C yet if
        stage A also fails) -- fall through to PHASE 2.

PHASE 2 (only reached when Phase 1 found nothing): scan the remaining
    (non-retained) rows of each seed's front, in a fixed deterministic
    order, classifying each until either:
      (a) a g2_correct row is found: n_correct_on_front > 0 (not A) is now
          proved, and n_retained_correct == 0 was already proved in Phase
          1 (no retained row was ever correct) => stage = B. STOP
          immediately -- no further rows, of this seed or any other, need
          classification.
      (b) every row of every seed is exhausted with none correct: this
          proves the universal negative n_correct_on_front == 0 => stage
          = A. This is the only branch that pays the full exhaustive
          classification cost, and it is proved, not assumed, that it must
          -- ruling out a correct row existing "anywhere" over an
          unbounded-in-principle front has no shortcut.
```

*Proof sketch:* Phase 1's branch is exactly Lemma 1 + Lemma 2 composed;
Phase 2's branch (a) is a direct existential witness for
`n_correct_on_front > 0` combined with Phase 1's already-established
`n_retained_correct == 0`, which is exactly `evaluate_world`'s own B
condition; Phase 2's branch (b), reached only when no witness exists
anywhere, is definitionally A. No case is double-counted or skipped: the
two phases and their sub-branches are mutually exclusive and jointly
exhaustive, mirroring the predeclaration's own claim about the A-E
partition itself. QED.

This order is NOT the mission prompt's illustrative sketch imposed by
assumption -- it is derived from what `evaluate_world` actually reads.
Concretely, it differs from the sketch in one respect worth flagging:
there is no separate "generated candidates" tier below the front in E2's
real schema (the persisted front already *is* the exhaustive
`equations_` Pareto front `run_seed_search` returns; nothing pre-front is
ever classified in production), so the sketch's steps 5-6 are simply
inapplicable here, not silently skipped.

## 3. Why `algebraically_equivalent` is decomposed away from `score_row`

`score_row` always attempts `algebraically_equivalent` for every row it is
given (once parseable), regardless of whether that row is `g2_correct` or
ever becomes a representative. `evaluate_world` only ever reads ONE row's
`truth_equivalent` -- the representative's, and only when the
representative is not itself `g2_correct`. Piping every Phase-1/Phase-2
witness row through `score_row` verbatim would silently reintroduce most
of the very cost this module exists to remove (see section 1's point 2).

`lazy_classify.py` therefore imports the three sub-calls `score_row` itself
composes for `g2_correct` (`classify_support`, `classify_family_match`,
`evaluate_g2_event` -- unmodified, from `g2_contract`) and calls them
directly, and separately reproduces `score_row`'s own guard and call for
`truth_equivalent` (`parse_production_candidate`, the *reused* (not
copied) `e2_scoring._parse_truth`, and `algebraically_equivalent` --
unmodified), invoking it **at most once per world**. This is a
decomposition of production code at a seam production itself already uses
to compose `score_row` (`e2_scoring.py`'s own docstring notes an identical
precedent: `rc5_selection.py`'s cross-seed grouping independently
recomputes `template_key` from the raw string rather than reusing
`classify_expression`'s cached value) -- not a new formula.

**Consequence beyond speed:** `algebraically_equivalent` has no wall-clock
cap anywhere in its call path (`discovery/equivalence.py`, only a cheap
`count_ops` early-out). It was never brought under the 2026-08-16 rescue's
process-boundary timeout fix, because that fix targeted
`classify_expression` specifically. Reducing its call count from "every
parseable row of every front" (up to 30 x front_size per world under
exhaustive execution) to "at most one row, only when the representative is
not already `g2_correct`" is therefore also a **risk reduction**, not
purely a speed one -- it shrinks exposure to the one remaining uncapped
symbolic call in the whole E2 pipeline. This is noted for the hostile
review and for Part X's poison-world analysis, not treated as license to
change `algebraically_equivalent` itself, which this rescue does not touch.

## 4. Parity contract -- exactly what is, and is not, claimed identical

The lazy path reproduces, **field-for-field identically** to
`e2_aggregate.evaluate_world`, whenever both are run on the same world:

- `first_loss_stage`
- `representative_g2_correct`
- `representative_truth_equivalent` -- **except** when
  `first_loss_stage == "E"`. In that one case, `evaluate_world`'s
  `WorldOutcome.representative_truth_equivalent` still holds whatever
  `score_row` computed for the representative (since `score_row` always
  attempts it), while the lazy path deliberately never computes it (it
  is not needed once `g2_correct` is already known True) and reports
  `None`. This is a disclosed, intentional narrowing, not a defect: no
  downstream consumer (Gate 2, the A-E rate, E4a) ever reads
  `representative_truth_equivalent` when the representative is already
  `g2_correct`. `MURU_V2_E2_REPLAY_PARITY.json`'s comparison logic
  excludes this one field on E-stage worlds accordingly (see that
  document's methodology section) -- everything else, on every stage, is
  compared with no exclusions.
- `representative_expression` (when a representative exists)

The lazy path does **not** reproduce (by design, and this is a real,
disclosed reduction in what gets computed, not an approximation of
anything that IS reproduced): per-seed diagnostics
(`n_seeds_correct_on_front`, `n_seeds_retained_correct`, `score_gap`,
`complexity_gap`, `r2_gap`), and does not persist a classification record
for every front row (only for the rows actually classified). Where full
per-seed diagnostics are wanted (e.g. the balanced estimation sample, Part
VII), the real, unmodified `e2_aggregate.evaluate_world` remains available
and should be used as-is -- this module's only job is the fast path to the
three routing/stage-relevant fields above.

## 5. What "cheap deterministic filters" this module does and does NOT use

None. The witness order changes only WHICH rows get classified and in what
order, using EXACTLY the frozen classifier/scorer on any row it does
classify. No candidate is ever declared equivalent, correct, or
incorrect by anything other than `classify_expression` +
`classify_support`/`classify_family_match`/`evaluate_g2_event` +
`algebraically_equivalent`, called on the real expression string, exactly
as production would call them. This satisfies the mission's "no
approximate pre-filter may be allowed to declare equivalence" constraint
by construction, not by discipline alone.

## 6. Test strategy (two tiers, and why)

**Tier 1 -- control-flow correctness** (`tests/test_lazy_classify_control_flow.py`,
5/5 passing): `classify_expression` and `algebraically_equivalent` are
mocked; `classify_support`/`classify_family_match`/`evaluate_g2_event` run
FOR REAL (cheap, pure, no reason to fake). Verifies: stage E needs exactly
30 classify calls and 0 equivalence calls; stage B short-circuits on the
first witness found (31 calls for a 60-row synthetic world, not 60); stage
A pays the full 60-call cost (proving no shortcut exists there, as
claimed); stage D/C fire on exactly the "correct minority loses the
cross-seed vote to an incorrect majority" scenario section 6 describes,
using exactly one equivalence call; stage E never calls
`algebraically_equivalent` even when it would return a value, proving the
section-3 divergence from `score_row` is real and intentional.

**Tier 2 -- scientific fidelity** (`MURU_V2_E2_REPLAY_PARITY.json`, Part
V): the real, unmodified `classify_expression` and
`algebraically_equivalent`, run on real persisted candidate rows from
already-completed E2a worlds, comparing the lazy result to the exhaustive
result already on record for that world. This is the tier that actually
licenses adoption; Tier 1 only proves the algorithm's control flow does
what section 2's theorem says it should.
