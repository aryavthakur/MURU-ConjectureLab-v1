# DEVIATIONS_OBJECTIVE_VALIDATION.md

Deviations from `TYPE2_VALIDATION_PREREGISTRATION.md`
(sha256 `9ce046294940464343cd74978931fa3fc9ed7bb79541484a9fba7b8c142ee9e7`,
frozen at commit `307e4e0` before any fresh world existed).

The pre-registration §14 draws one line: **an implementation bug may be fixed; a
methodological change may not be made.** Both entries below are implementation
corrections. Neither touches the selector, a tolerance, a threshold, a seed, an
operator, a complexity rule, an acceptance condition or the decision rule.
Neither changes any generated world: every world's frozen `output_sha256` was
re-verified after both fixes.

**Neither changes the verdict.** The verdict was computed before D2 and again
after it, and is `DO NOT AUTHORIZE PHASE 4` in both cases, on the same single
stop condition.

---

## D1 — Recovery scoring crashed on the null-calibration worlds (IMPLEMENTATION ONLY)

**What happened.** `ov_45_recovery.py` raised `KeyError: 'NULL'` on the first
`NCAL` world. `objval.recovery.planted_evaluator` looked every world's family up
in `REGISTRY2`, and the 100 calibration worlds carry the family label `NULL`,
which is not a planted law — a realistic world is built and then the
descriptor-response link is destroyed by one of the master plan's §13.6
constructions.

**Why it is a bug and not a methodological change.** There is nothing to recover
in a null-calibration world and nothing the pre-registration asks to be scored
there. The correct behaviour was already specified — recovery fields are
recorded *not applicable* where no descriptor law exists, exactly as they are for
`G4` and `GC` — and the code simply failed to reach it for one family label.

**Fix.** `planted_evaluator` returns `(None, ())` for any family absent from
`REGISTRY2`, which routes `NULL` down the same not-applicable path as `G4`
and `GC`.

**Scope of the rerun.** Recovery scoring only. It is a pure function of frozen
selection and adjudication output, both of which were already written to disk
and were not recomputed. No search, no selection, no acceptance, no threshold.

**Regression test.** `tests/test_ov_scoring.py::test_null_calibration_worlds_score_as_not_applicable`.

---

## D2 — The G1C planted law recomputed its own centering constant under perturbation (IMPLEMENTATION ONLY)

**What happened.** `G1C` plants `g = a0·√m·exp(a1·(X − X̄))`, where `X̄` is the
mean of the carrier — **a constant of the world**, fixed when the world is
generated. The evaluator computed `X̄` inside the lambda from whichever matrix it
was handed. Truth-side scoring measures elasticities by a central multiplicative
perturbation of one column; perturbing the carrier moved `X̄` with it, so

    a1·(X·(1+ε) − X̄·(1+ε)) = a1·(1+ε)·(X − X̄)

and the finite difference measured `a1·(X − X̄)`, whose median over a centered
variable is ≈ 0. The carrier therefore fell below the 0.02 effective-support
threshold and vanished from the **planted** signature, so all ten `G1C` worlds
were scored against a planted support of `['MASS']` alone.

**Evidence it is a defect and not a result.** With the constant frozen, the
measured planted carrier elasticity on world `OV|G1C|r000|moderate` is
**0.7291**, which equals the analytic value `a1 · median(X) = 0.494 × 1.4759 =
0.7291` to four decimals. With the constant recomputed it is `nan`. The law
being differentiated was not the law that was planted.

**Why it is a bug and not a methodological change.** The planted law is
unambiguous and unchanged; only its numerical differentiation was wrong. Nothing
about the candidate side, the selector, the acceptance rule or any threshold is
involved, and `G1C` carries no gate other than the false-identification count,
which is 0 both before and after.

**This correction makes `G1C` look better, and that is recorded here
deliberately.** Before: support recovery 0/10, Type 2 success 0/10. After:
support recovery 8/10, Type 2 success 5/10. It was applied because the diagnosis
is exact and verifiable against a closed-form value, not because the result was
disappointing — and it could not change the verdict, which was already
`DO NOT AUTHORIZE PHASE 4` on the corroboration gate.

**Fix.** `truth2.G1C.g_of` reads `params["carrier_center"]` when present and
falls back to the in-line mean when it is not. World construction passes nothing,
so the fallback reproduces the generated data exactly;
`objval.recovery.freeze_constants` injects the frozen value for scoring.

**Verification that no world changed.** All 10 `G1C` worlds, plus spot-checked
`G1B`, `G3` and `G4` worlds, reproduce the `output_sha256` recorded in
`artifacts/ov_worlds.json` after the fix.

**Scope of the rerun.** Recovery scoring only, as in D1.

**Regression tests.**
`tests/test_ov_scoring.py::test_a_centered_planted_law_keeps_its_carrier_in_support`
and `tests/test_ov_pipeline.py::test_g1c_worlds_reproduce_their_frozen_hash_after_the_centering_fix`.

---

## Not deviations

Recorded here because they were noticed and deliberately left alone.

* **The null thresholds came out materially higher than Phase 3's** (complexity
  6: **+0.6106** against Phase 3's +0.4125; complexity 20: **+0.6831** against
  +0.4889). This is a result of the frozen procedure applied to 100 fresh
  calibration worlds, not a change to it. Nothing was adjusted.
* **The comparison arm's configuration was not touched** after it failed its
  gate. `TYPE2_ENGINE_CORROBORATION.md` §5 committed in advance to leaving it at
  Phase 3's settings, precisely so the standard could not depend on a tuning
  choice made after seeing disagreement.
* **Shard 1 of the search ran ~15 min longer than the others** because the
  deterministic `index mod 4` split gave it every world of one null construction,
  and that construction is the slowest. No work was rebalanced, no process was
  restarted, and per-seed checkpointing means the split has no effect on results.
* **Actual runtime, 3.89 h, exceeded the 2.62 h projection** by a factor of 1.50
  on per-run wall time (1.309 s against 0.874 s). The cause is sustained thermal
  behaviour on a fanless machine, which `RUNTIME_BUDGET_OBJECTIVE_VALIDATION.md`
  flagged in advance as the reason the honest range was 2.4–3.3 h. Nothing was
  changed in response.
