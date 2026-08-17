# MURU v2 E2 Rescue V2: Balanced Estimation Sample Design (Part VII-IX)

**Status:** design document + implementation. Code:
`scripts/e2_rescue_v2/balanced_sample.py`. Tests:
`tests/test_balanced_sample.py` (9/9 passing). Manifest computed for real
against the live run's world-ID-only completion set (never outcomes) --
see section 4.

## 1. The manifest, recovered from source

`src/muru/v2_calibration/e2_worlds.py`: `FAMILIES` (5) x `REGIMES` (3,
`low`/`mid`/`high`) x `NOISE_LEVELS` (3, `noiseless`/`default`/`strong`) x
`N_REPLICATES` (12) = 540 worlds, **45 cells x 12 replicates**. This is the
exact factorial structure the mission's candidate sizes (180, 225, 270,
315, 360) are checked against below.

## 2. Design-based variance (derivation)

The sample takes an EQUAL number of replicates `r` from every one of the
45 cells (a fixed preregistered count, not chosen adaptively per cell).
Since every cell has the SAME population size (`N_h = 12`) and the SAME
sample size (`n_h = r`), the sampling fraction `f = r/12` is constant
across all 45 strata -- this is **proportionate stratified sampling**, so
the stratified estimator of an overall proportion collapses to the simple
mean of the 45 per-stratum sample proportions, each weighted equally
(`W_h = 1/45`).

For simple random sampling without replacement within stratum `h`:

```
Var(p_hat_h) = (N_h - n_h)/(N_h - 1) * p_h(1-p_h)/n_h        [finite-population-corrected]
```

Stratified variance (equal weights, `W_h = 1/45`):

```
Var(p_hat) = sum_h W_h^2 * Var(p_hat_h) = (1/45) * Var(p_hat_h)     [since all 45 terms are identical when p_h is assumed equal]
```

**Worst-case bound**, used throughout (since per-cell true proportions
`p_h` are exactly what this design must not look at before freezing):
set `p_h = 0.5` for every cell -- this maximizes `p_h(1-p_h)` and is the
standard conservative choice for a pre-data margin-of-error calculation.

```
overall_MOE_95 = 1.96 * sqrt( (1/45) * [(12-r)/11] * 0.25/r )
family_MOE_95  = 1.96 * sqrt( (1/9)  * [(12-r)/11] * 0.25/r )     [9 cells per family: 3 regimes x 3 noise]
```

Implemented verbatim in `balanced_sample.py::design_based_moe`;
`tests/test_balanced_sample.py` independently checks monotonicity, the
`r=12` (full census) zero-variance boundary, and the specific `r=5 -> r=6`
crossing used below.

## 3. Selecting the smallest sufficient sample

Evaluated at every candidate size the mission names, all of which are
**exact** (`45 x r`, confirmed by `test_candidate_sizes_are_exactly_45_times_r`)
-- 270 is not privileged by construction, only by where the threshold below
happens to land:

| r | n = 45r | overall MOE (95%) | family-level MOE (95%) |
|---|---|---|---|
| 4 | 180 | 6.23% | 13.93% |
| 5 | 225 | 5.21% | 11.65% |
| **6** | **270** | **4.40%** | 9.85% |
| 7 | 315 | 3.72% | 8.32% |
| 8 | 360 | 3.11% | 6.96% |

**Threshold used:** overall MOE < 5% at 95% confidence, worst-case
variance -- a standard survey-precision convention, stated here explicitly
(not assumed) so it can be disputed on its own terms. `r=5` (n=225) misses
it (5.21%); `r=6` (n=270) is the smallest candidate size that clears it
(4.40%). **`r=6`, n=270 is therefore the selected design** for the
**overall** (population-wide) first-loss proportion estimate -- this is
where 270 comes from, derived against a stated threshold, not asserted.

**Disclosed limitation, not smoothed over:** no candidate size in the
mission's offered range reaches 5% MOE at the **family** level -- even the
largest, `r=8`/n=360, sits at 6.96%. Family-level precision is capped by
each family only ever contributing 9 cells (vs. 45 pooled); reaching <5%
there needs roughly `r=10` (n=450), a regime where the finite-population
correction is already shrinking fast and the marginal value of the 41
additional replicates (`(12-10)/(12-8)` narrowing) over `r=8` is small
relative to the cost. **Recommendation:** adopt `r=6`/n=270 for E2's
stated primary purpose (locating which of A/B/C+D dominates, an
overall-population question); report family-level estimates from the same
n=270 sample with their wider (~9.85%) MOE explicitly attached, rather
than inflating the whole design to chase family-level precision the
mission's own candidate range does not comfortably reach.

## 4. Selection mechanism and reuse (computed for real, world-IDs only)

Per cell, `r` of its 12 replicate indices are drawn by a
`numpy.random.Generator` seeded from `sha256("MURU_V2_E2_BALANCED_SAMPLE_SEED_V1|" + cell_id)`
-- a pure function of the cell's own identity, fixed before this script
ever opens a single result file. `test_selection_depends_only_on_cell_identity_not_on_any_external_state`
and `test_selection_is_deterministic_across_repeated_calls` verify this
directly; nothing in `select_replicates_for_r` reads a clock, an
environment variable, or any file.

Run for real against the live run's world-ID set (membership only --
`_completed_world_ids` reads `world_id` and nothing else from every
`worlds_shard_*.jsonl` line, across all 5 live output directories,
read-only):

| r | n | already completed (reusable) | additional worlds required |
|---|---|---|---|
| 4 | 180 | 100 | 80 |
| 5 | 225 | 121 | 104 |
| **6** | **270** | **150** | **120** |
| 7 | 315 | 178 | 137 |
| 8 | 360 | 202 | 158 |

At the selected design (r=6, n=270): **150/270 (55.6%) of the frozen
sample is already complete** and directly reusable from the live run's
existing output, with **120 additional worlds** needed to finish it. This
count will keep changing as the live run progresses (it is a snapshot,
timestamped in `MURU_V2_E2_RESCUE_V2_PROVENANCE.json`), but the SAMPLE
ITSELF (which 270 world_ids) is frozen and does not change with it.

Selection is implemented as `select_replicates_for_r(r)` = the first `r`
entries of a single, per-cell, RNG-shuffled `full_preference_order` (all
12 replicates, one deterministic permutation per cell) -- so the r=180
sample is a strict subset of the r=225 sample, which is a strict subset of
r=270, and so on, rather than 5 independently-drawn samples. This nesting
is deliberate: it is what makes the section 7 fallback mechanism
well-defined (the "next" replicate for a given cell is unambiguous), and
it means growing the sample later (e.g. from 270 to 315, if the r=6
design's family-level precision proves insufficient once real data is
seen) never discards already-classified sample worlds.

## 5. Keeping the routing gate exact even though estimation is sampled (Part VIII)

The balanced sample answers a DIFFERENT question than the routing gate,
and must never substitute for it:

- **N_ESTIMATION = 270** (or whichever r is adopted): the frozen sample
  used to report a first-loss proportion with a known, honest MOE.
- **N_GATE**: whatever the exact routing-lock monitor (`routing_lock.py`)
  needs -- either it locks early over the full 540-world population
  (`LOCKED_EXECUTE_E4A`, section on Gate 2 branch 1), or it does not, and
  `FULL_RUN_REQUIRED` stands regardless of what the 270-world estimate
  suggests. A sample-based confidence interval is never treated as
  evidence for "B probably wins" in place of the frozen gate's exact
  plurality test -- this is enforced by construction (the two modules
  share no code path that could blend them) and is checked again in the
  hostile-review document.

Classifying a balanced-sample world is not wasted relative to the gate:
every classified world (sample or not) also advances `n_classified`/`r`
in the gate-lock monitor, since both draw from the same underlying 540
worlds. The two purposes are complementary reads of the same work, never
in tension.

## 6. Prioritized scheduling (Part IX)

Once the balanced sample is frozen (section 4's 270 world_ids, fixed),
remaining uncomputed worlds should be scheduled, in this order, using ONLY
information that cannot depend on any A-E outcome:

1. **Worlds in the frozen balanced sample not yet completed** (115 of them
   at the current snapshot) -- these are needed for BOTH the estimation
   endpoint and (as part of the underlying census) the gate.
2. **Worlds that maximize progress toward exact gate resolution** under an
   outcome-blind, deterministic rule. In practice this reduces to "classify
   remaining worlds in a fixed, arbitrary-but-deterministic order" (e.g.
   the existing `world_ordinal` order the manifest already defines) --
   because Gate 2's lock condition (`routing_lock.py` section 2) depends
   only on the COUNT of worlds still outstanding (`r`), not on which
   specific worlds they are. **No world's identity makes the lock fire
   sooner than any other's**, since the worst-case inequality is symmetric
   in which cases remain unclassified. This is disclosed rather than
   invented: Part IX asks whether outcome-blind prioritization can help
   gate resolution specifically, and the honest answer, derived from
   section 2's own proof, is that it cannot -- only the COUNT of remaining
   worlds matters to the lock, so priority (2) collapses to "any
   deterministic order," and priority (1) (the sample) is the only
   information-bearing preference available pre-outcome.
3. **Everything else** (worlds outside the frozen sample), in
   `world_ordinal` order, only after (1) and (2) are exhausted.

Allowed scheduling inputs used above: the frozen 540-world manifest, the
frozen 270-world sample membership, and `world_ordinal` (a pure identity
field, zero outcome content). Not used, per the mission's explicit
prohibition: any completion-order signal correlated with runtime class
(the interim characterization already showed completion order is
runtime-selected and NOT representative -- reusing that bias to prioritize
would reintroduce exactly the sampling problem this design exists to
avoid) and, of course, any A-E label.

## 7. The poison world falls inside the frozen sample -- the fallback mechanism (Part X)

Checked directly (world_id membership only, no outcome read): the known
poison world, `V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000`
(`E2_EXECUTION_DEVIATION.md` section 13; 80 isolated retry attempts, 100%
SIGKILL, 0 successes, retries currently stopped on the production host per
that document's section 14), is replicate 0 of the
`mass_affine_descriptor|c_low|n_noiseless` cell -- and replicate 0 is
selected by this cell's own precommitted `full_preference_order` at
**every** offered candidate size (r=4 through r=8; verified directly, not
assumed). It cannot simply be dropped from the sample without either
shrinking `n` for that one cell (biasing that cell's own estimate toward
whichever replicates happened to survive) or silently picking a
replacement after the fact (which would not be results-blind, since "which
replicate is easiest" is itself outcome-adjacent information).

**Resolution, decided now, before any outcome exists for it:**
`select_replicates_with_fallback(r, permanently_unresolvable)` swaps any
selected world found in `permanently_unresolvable` for the NEXT entry in
that cell's own `full_preference_order` -- mechanical, deterministic, and
identical regardless of which specific replicate turns out to be the
problem. For `mass_affine_descriptor|c_low|n_noiseless` at r=6, the
fallback substitute is precommitted to be replicate 7 (the next name in
`[5, 0, 3, 11, 2, 9, 7, 6, 4, 1, 10, 8]` after the first 6, excluding 0) --
this is disclosed here, in writing, before the poison world is declared
unresolvable, so the substitution cannot be read as chosen in hindsight.

This mechanism is invoked ONLY once a world is formally
`permanently_unresolvable`, a status this design does not itself declare
-- see Part X's own migration/operator guidance
(`MURU_V2_E2_RESCUE_V2_FEASIBILITY.md`) for the isolated-retry exhaustion
criteria that would justify calling the poison world exactly that. Until
then, it remains counted as an ordinary outstanding (`r`) world for both
the sample (still worth one more isolated retry attempt, ideally under the
lazy architecture -- see the feasibility document's Part X analysis of
whether that changes anything for THIS specific world) and the routing
gate (`routing_lock.py` never assumes a favorable or unfavorable resolution
for it, exactly as for any other outstanding world).
