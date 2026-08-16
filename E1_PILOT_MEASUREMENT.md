# E1 pilot measurement and full-run authorization

Per `MURU_V2_E1_PROTOCOL.md` Sec 8: "A 5-cell pilot ... is run first to
measure true per-fit-unit cost; the design's own 12-CPU-hour estimate ...
is replaced by that measurement before the full 11,475-fit-unit run is
authorised."

## Pilot

5 fit units (one `MU_CEIL` level each, diverse `D`/`alpha`/`noise`
combinations per the protocol's declared picks): `M0_a000_n002_c1e4`
(control-analogue), `M3_a025_n000_c1e4` (small alpha), `M1M2M3_a200_n006_copen`
(large alpha, high noise, open ceiling), `M2_a100_n000_c1e3` (mid alpha,
middle ceiling), `M1_a050_n006_c1e4` (different D, high noise). Run via
`scripts/e1_run.py --pilot`. 0 errors, 0 PySR imports, output:
`artifacts/e1_pilot/`.

Sanity check on the 5 pilot worlds' primal (`C0`/`P0`, i.e. frozen v1 rule)
case status: `M3_a025_n000_c1e4` (a *planted M3 deviation*, `alpha=0.25`) →
`M0_REJECTED_M3` -- the frozen detector fires even at a *small* alpha, which
is itself informative for `alpha_star_M3` once the full grid runs.
`M0_a000_n002_c1e4` and `M2_a100_n000_c1e3` (a true null and a mid-alpha M2
world) → `M0_NOT_REJECTED` -- no false rejection on the null, consistent
with E0's own 0/540 finding. `M1_a050_n006_c1e4` and the large-alpha,
high-noise combined-family world → `BOUNDARY_LIMITED` under the frozen `C0`
rule -- exactly RC1's pathology this study exists to characterize.

## Cost measurement

Direct per-unit serial timing (outside multiprocessing, to isolate real
compute from one-time worker-import overhead, which is separately amortized
below): 5 fresh single-unit calls to `e1_run.run_fit_unit` across different
cells measured **2.8s-9.5s per fit unit** (mean ≈ 6.4s), with `cProfile`
attributing ≈ 72% of that to the **frozen** `rc5_adequacy.fit_model`'s own
1,080 grid searches per unit (unmodified code, not something this
implementation can speed up) and the remaining ≈ 28% to `fit_case_phi`
(computed once per fit unit, not per `MU_CEIL` level) plus this
implementation's probe/profile/C4-relaxed-refit overhead, which fires only
on the ≈ 3-20%-of-folds that show boundary contact (8.4% of (fold, model)
probes touched a bound across the pilot's mixed sample).

**Worker-import overhead is a one-time-per-worker cost, not per-unit**: a
multiprocessing pool worker imports `numpy`/`pandas`/the `muru` package
once (≈ 20s cold) and then serves many fit units from the same warm
interpreter, so it amortizes to a negligible fraction of the 11,475-unit
total and is excluded from the per-unit estimate above.

**Projection.** At 6.4s/unit serial and this machine's 8 CPUs: 11,475 x
6.4s / 8 ≈ **9,180s ≈ 2.55 CPU-wall-hours**. In total-CPU terms: 11,475 x
6.4s ≈ 20.4 CPU-hours, above the design's original 12-CPU-hour estimate for
the smaller (pre-`MU_CEIL`-crossing) 3,825-unit grid -- consistent with,
not contradicting, that estimate once divided by this protocol's own 3x
crossing factor (20.4 / 3 ≈ 6.8 CPU-hours, inside the design's original
6-10 CPU-hour fitting-cost range for the base grid).

## Decision

The measured cost is **within the fallback threshold this protocol
declared** (Sec 8: reduce `N_REPLICATES` only if the full run is not
practical for this session to complete and verify end to end). A ≈2.5-hour
wall-clock background run is practical in this environment (long-running
background execution with periodic progress checks is supported), so **no
reduction is invoked**: the full run proceeds at the frozen `N_REPLICATES =
75` (11,475 fit units), exactly as designed, not the reduced fallback.

**Full run authorized at full preregistered scale.**
