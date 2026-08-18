# MURU V2 E4a Equivalence-Defect Reachability Audit (Step 6)

Results-blind structural audit of whether either of the two inherited
`discovery/equivalence.py` defects (`L-RET-08`, from the master
reconciliation, citing the symbolic-equivalence and math-correctness
audits) is reachable in the ACTUAL E4a evaluation corpus. Existence checks
only, run against real persisted candidate rows and real truth laws --
never any A/B/C/D/E stage label, never a per-world scientific outcome.

## Conclusion

```
DEFECT_2_REACHABLE: NO  (provable, static -- not merely low-probability)
DEFECT_1_REACHABLE: NO  (empirically checked three independent ways; see below)
```

Neither defect threatens E4a's primary endpoint. **No stop condition per
Step 6's instruction is triggered.**

## Defect 2: sign-unconstrained numeric scale (math-correctness audit)

**Precise location, verified from current source, not assumed from the
audit's own summary.** Reading `discovery/equivalence.py` directly: the
sign-unconstrained least-squares scale lives in `numeric_relation()`
(`c = float(np.dot(a, b) / denom)`, no sign constraint), which feeds
`equivalence()`'s `exact_equivalent` field
(`exact = bool(alg is True or num["rel_rmse"] < EXACT_REL_RMSE)`). **This
is a different function from `algebraically_equivalent()`**, which is
purely symbolic (`sympy.simplify`/`cancel`/`powsimp`, never calls
`numeric_relation` or `equivalence()`). The master reconciliation's own
shorthand ("two defects in `algebraically_equivalent`") is imprecise on
this point -- corrected here from source, not merely repeated.

**Check performed:** static AST scan of `e4a_scoring.py` and
`lazy_classify.py` (the only two modules that ever compute a C/D split
or a `truth_equivalent` value in this rescue) for any import of or call to
`numeric_relation` or `equivalence`. Zero hits. Both modules call
`algebraically_equivalent` exclusively (`_truth_equivalent`, itself the
same call `e2_scoring.score_row` makes, decomposed at its own seam -- see
`lazy_classify.py`'s own docstring).

**This is not a probability statement. It is a call-graph fact**: E4a's
stage C/D split and PRR-5 cannot reach `numeric_relation`/`equivalence()`
because nothing in the code path that computes them ever calls those
functions, under any input.

## Defect 1: nan-ratio false positive (symbolic-equivalence audit, finding E-1)

**Precise location, verified from source.** `algebraically_equivalent`'s
line `return bool(ratio.is_positive is not False and ratio != 0)` --
`nan.is_positive` is sympy's `None` ("unknown"), and `None is not False`
is `True`, so a formally-`nan` ratio is misreported as a proof of
equivalence. The audit's own diagnosis: reachable only via a degenerate,
everywhere-invalid input that production's `finite_mask`/
`MAX_INVALID_FRACTION` gate normally excludes before this function is ever
called. Checked here against the REAL corpus, not assumed by analogy:

**(a) Exhaustive structural scan.** Every persisted candidate row's own
`invalid_fraction` field (already computed, zero new work), across all 7
result directories (old run's 5 healthy dirs + Rescue-v2's smoke +
production output), **166,908 rows scanned**:

```
n_everywhere_invalid_precondition_met: 1
max_invalid_fraction_observed: 1.0
```

**Contrary to a naive "the audit already said this doesn't happen"
assumption, ONE real row does meet the necessary precondition** --
disclosed and investigated, not dismissed:

- `world_id`: `V2C|E2|mass_affine_descriptor|c_mid|n_default|r002`, seed
  `2104501518`, `front_rank` 12, `invalid_fraction=1.0`,
  `valid_r2=NaN`, `retained_by_argmax_score: false`.

**(b) Direct check of that specific row against its own world's real
truth law** (timeout-protected, 8s cap): the resulting symbolic ratio is
a non-trivial rational expression still containing `mass`/`descriptor`
(`ratio.is_number` is `False`), so `algebraically_equivalent` takes the
`diff = simplify(cancel(a-b))` branch, **never reaching the vulnerable
`ratio.is_positive`/`nan` line at all** for this specific pair. This one
witness does not trigger the defect.

**(c) Corroborating random spot-check**, 60 (real candidate x real truth
law) pairs, `SIGALRM`-protected at 5s/pair (after an unprotected first
attempt genuinely hung and had to be killed -- see "adjacent finding"
below):

```
n_attempted: 60, n_parse_failed: 0, n_nan_ratio_hit: 0, n_timed_out: 0
```

**(d) The row can never reach `algebraically_equivalent` as a
representative in the first place**, independent of (a)-(c): its
`retained_by_argmax_score` is already `false` in production (pandas'
`idxmax()` skips NaN by default), and after this session's own fix (see
below), every E4a retention/vote-reduction rule excludes NaN-`valid_r2`
rows from consideration too -- so this row cannot become any policy's
cross-seed representative, the only place `algebraically_equivalent` is
ever called on a candidate.

**Conclusion: Defect 1 is not reachable in this corpus** -- the one row
meeting its structural precondition does not trigger it against real data,
a 60-pair random sample found zero hits, and the row cannot enter the
representative-selection path that would call the vulnerable function.

## Adjacent finding, self-discovered while running this audit (disclosed, and fixed)

The FIRST attempt at the spot-check (no per-pair timeout) hung for 7+
minutes on real data and had to be killed (`SIGTERM`) -- **live,
empirical confirmation of hostile-review finding F1**
("`algebraically_equivalent` has no wall-clock cap anywhere"), not merely
a theoretical risk. The rewritten, timeout-protected version (5s/pair)
completed cleanly with zero timeouts on its 60-pair sample, but F1 remains
a real, unresolved, already-disclosed production risk -- unchanged by
this audit, not newly discovered as a defect, only newly observed in
practice.

Separately, while investigating the one `invalid_fraction=1.0` row above,
found and fixed a genuine defect in **this session's own new code**
(`e4a_scoring.py`, not `equivalence.py`): `retain_r0`/`retain_r1`/
`retain_r4`/`retain_r5`/`retain_r6`/`cast_vote` ranked rows using plain
Python `min()`/`max()` over tuples containing `valid_r2`/`score`, which
does **not** skip NaN the way pandas' `idxmax()` (production's own
mechanism) does -- verified empirically:
`min([(-nan,12),(-0.5,0),(-0.9,1)])` incorrectly returns the NaN tuple
when it is first in iteration order. Fixed by filtering non-finite
`valid_r2`/`score` rows out of every ranking step before comparison (a
robustness fix, not a scientific choice -- no retention rule's intent
changes; a row with undefined accuracy simply can never be an "argmax" of
anything). 7 new regression tests added and passing
(`tests/test_e4a_scoring_controls.py`); all 74 prior checks still pass
unchanged (81/81 total).

## Scope discipline

No A/B/C/D/E label, first_loss_stage, or scientific rate was computed,
read, or exposed anywhere in this audit. The single row investigated in
detail was inspected purely for its non-scientific structural fields
(`invalid_fraction`, `valid_r2`, `retained_by_argmax_score`) and its
symbolic-ratio behavior against its own truth law -- an implementation-
correctness question, the same category of inspection this migration has
performed throughout (e.g. the poison world's own diagnosis, smoke-test
verification).
