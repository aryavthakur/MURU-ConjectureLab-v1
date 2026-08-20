# MURU SAFE_EXP DIAGNOSTIC

**Scope**: the 10 G1C development worlds only. The fresh independent holdout was
not touched. Run only AFTER architectures A-D were compared and frozen, and kept
entirely out of that comparison.

**Verdict: SAFE_EXP is NOT adopted.**

## Why the experiment exists

Two G1C worlds, `OV|G1C|r001|moderate` and `OV|G1C|r002|moderate`, are genuine
search failures: zero family-correct candidates among 30 seeds and every band
member. G1C plants

```
g = s * sqrt(m) * exp(a * (x - x_bar))
```

and `exp` is deliberately outside the frozen grammar (`DEVIATIONS_P3` D1).
Searching the same space harder cannot represent a function the space does not
contain, so the only search-side intervention that could move these two worlds is
a grammar change.

## Design, fixed before any recovery number

* Operator: `sexp(x) = exp(clamp(x, -K, K))`, **K = 8.0**, chosen before scoring.
* Complexity cost **5** (a plain unary operator costs 1), so SAFE_EXP is charged
  five times the usual price and cannot be used casually. `MAX_COMPLEXITY = 20`
  unchanged. Nested constraint `sexp` inside `sexp` = 0.
* No other operator added. `niterations = 40`, `populations = 15`,
  `population_size = 33`, parsimony, adaptive scaling, determinism, serial
  parallelism: all the frozen `PYSR_CONFIG`, unchanged.
* **BASE_GRAMMAR** = the 30 existing frozen-grammar seeds per world.
* **PORTFOLIO_GRAMMAR** = 15 frozen-grammar seeds + 15 new SAFE_EXP seeds.
  Total search runs per world identical at 30 in both arms.
* Both arms pass through identical downstream code: frozen per-seed Pareto band
  at `BAND_TOL = 0.01`, structural signature on the frozen 2,000-point lattice,
  Type 2 family clustering, architecture A selection, then truth scoring.
* 150 new PySR runs, 202 s wall clock on 5 processes.

## Result

| | BASE_GRAMMAR | PORTFOLIO_GRAMMAR |
|---|---|---|
| search runs per world | 30 | 30 (15 + 15) |
| oracle support | 10/10 | 10/10 |
| oracle family | 8/10 | **8/10** |
| oracle exact | 6/10 | 7/10 |
| **selected family recovery** | **6/10** | **6/10** |
| selected support recovery | 10/10 | 10/10 |
| selected exact | 1/10 | 1/10 |
| median best rel_RMSE in pool | 0.0159 | 0.0105 |
| median seed-best validation R^2 | 0.9636 | 0.9643 |
| reports using SAFE_EXP | — | 2/10 |
| SAFE_EXP band members | 0 | 196 |
| compute | already spent | +150 PySR runs, 202 s on 5 procs |

Per world (family-correct = the frozen family definition, untouched):

| world | base oracle | base selected | base best rel_RMSE | portfolio oracle | portfolio selected | portfolio best rel_RMSE | SAFE_EXP members | of which family-correct | report uses SAFE_EXP |
|---|---|---|---|---|---|---|---|---|---|
| r000 | yes | **yes** | 0.0047 | yes | **yes** | 0.0002 | 61 | 57 | no |
| **r001** | **no** | no | **0.1653** | **no** | no | **0.1562** | **1** | 0 | no |
| **r002** | **no** | no | **0.1572** | **no** | no | **0.1549** | **1** | 0 | no |
| r003 | yes | **yes** | 0.0045 | yes | **yes** | 0.0035 | 13 | 9 | **yes** |
| r004 | yes | **yes** | 0.0154 | yes | **yes** | 0.0098 | 33 | 28 | no |
| r005 | yes | **yes** | 0.0970 | yes | **no** | 0.0113 | 27 | 13 | no |
| r006 | yes | **yes** | 0.0079 | yes | **yes** | 0.0062 | 26 | 25 | no |
| r007 | yes | no | 0.0752 | yes | no | 0.0752 | 0 | 0 | no |
| r008 | yes | **no** | 0.0164 | yes | **yes** | 0.0157 | 10 | 6 | no |
| r009 | yes | **yes** | 0.0041 | yes | **yes** | 0.0041 | 24 | 20 | **yes** |

## Reading

1. **The two worlds SAFE_EXP was designed for are not rescued.** `r001` and
   `r002` attract exactly **one** SAFE_EXP band member each. Their best
   achievable relative RMSE against truth moves 0.1653 -> 0.1562 and
   0.1572 -> 0.1549, both still far outside the frozen 0.10 family tolerance.
   The selected representative in `r001` is byte-identical across the two arms.
2. **Selected family recovery is a wash**: 6/10 in both arms. `r008` is rescued,
   `r005` is lost. Net zero, on 10 worlds — well inside sampling noise.
3. **The operator is used most where it is least needed.** 196 SAFE_EXP band
   members appear, 61 of them in `r000`, which the base grammar already recovers.
   Two of the ten reports promote a SAFE_EXP expression, both in worlds recovered
   without it. The deliberately high complexity cost did not suppress this.
4. The only real improvement is in *exact*-form recovery at the oracle level
   (6 -> 7) and in median best rel_RMSE (0.0159 -> 0.0105) — the grammar does fit
   G1C better, in worlds it does not need to.

The brief's condition — adopt only if the controlled comparison improves held-out
G1C recovery without clear overfitting — is **not met**. The grammar stays frozen.

## Honest scope limits

One `K`, one complexity cost, 15 SAFE_EXP seeds per world, 10 worlds, one engine.
This falsifies the specific proposition "adding a bounded exponential at a high
complexity price rescues the two G1C representability failures at constant search
budget." It does not prove that no grammar expansion could. Testing that is not
in scope, is not proposed here, and is covered by the sprint's hard stop.
