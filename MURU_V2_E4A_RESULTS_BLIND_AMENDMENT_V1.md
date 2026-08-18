# MURU V2 E4a Results-Blind Amendment v1.0.0

Applies exactly the master-reconciliation-approved corrections, as a
versioned amendment. `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`
(commit `f4c1105`) is **not edited in place** anywhere -- it remains the
authority text, with these three items applied on top of it by the E4a
implementation. Written and frozen before any E4a policy is scored
(results-blind to E4a; no E2a front read as part of authoring this).

**Does not**: change R0-R6, change any threshold, change the primary
endpoint, add a set-aware resolver, or change the frozen routing gate
(`MURU_V2_E2_ROUTING_LOCK_FREEZE.md` is untouched by this document).

---

## Correction 1: metric 2's EVAL denominator is 90, not 36

**Frozen text (verbatim, section 7, metric 2):** "Among the 108
`mass_power`-truth cases (36 in `V2C_RET_EVAL`; see note below)."

**Re-derivation from the frozen design's own numbers (not a new
assumption):**

```
mass_power occupies 1 of 5 families -> 3 regimes x 3 noise levels = 9 cells
V2C_RET_EVAL = replicate in {2..11} = 10 of 12 replicates per cell (section 6)

mass_power cases in V2C_RET_EVAL = 9 cells x 10 EVAL replicates/cell = 90
```

`108` (the total `mass_power` count, DEV+EVAL) is internally consistent
with this: `9 cells x 12 replicates = 108`, matching the frozen text's own
`108` figure exactly. The DEV-side count is `9 cells x 2 DEV
replicates = 18`, and `90 + 18 = 108` reconciles exactly. **`36` has no
derivation that reconciles with the frozen design's own `108` and
DEV/EVAL split** (`108 - 36 = 72 != 18`); it is a defect in the frozen
document's own prose, not a competing valid reading. `90` is correct and
is what the implementation uses.

Non-blocking regardless of which number is used for `false_structure_rate_
proxy`'s Wilson bound at zero events (`0` events at `n=36` gives Wilson
upper `0.096`; at `n=90` gives `0.041`; both clear the `0.15` E6-margin
ceiling section 10 item 2 references), so this correction changes no
adoption-gate outcome by itself -- it is corrected because it is wrong, not
because leaving it wrong would flip a decision.

## Correction 2: R3's conditional retention recall is tautologically 1.0

**Frozen text (section 5.1, item 1)** already states R3 "is definitionally
certain to win or tie" and calls its recall "a tautology, not a finding,"
but stops short of stating the exact value. This amendment makes it exact:

```
conditional_retention_recall(R3) = 1.0, EXACTLY, for every family,
for every stratum, with no Wilson interval, under the eligible-pool
definition (section 3).
```

**Derivation.** R3's within-seed retention rule is "whole front (every
row)" (section 5, R3's Rule column). The eligible pool is, by section 3's
own definition, exactly `{case : correct_on_front(case) = true}` -- i.e.,
every case where at least one of its 30 seeds' fronts already contains a
G2-correct row. Since R3 retains *every* row on every front, that same
G2-correct row is retained under R3 by construction, for every case in the
eligible pool, with no exception and no dependency on noise, family, or
stratum. "Truth survives retention under R3" is therefore true for the
entire eligible pool by definition, giving
`conditional_retention_recall(R3) = |eligible pool| / |eligible pool| = 1.0`
as an identity, not an empirical measurement -- there is no sampling
variation to attach a Wilson interval to.

**Consequence for PRR-1.** The frozen prediction (section 13, PRR-1)
hedges: "R3's `conditional_retention_recall` on `V2C_RET_EVAL` is at or
within Wilson noise of 1.0 for every family **except**
`mass_saturating_descriptor`." Given the identity above, this hedge cannot
be correct as stated against the *conditional* endpoint section 3 actually
defines -- R3 is exactly 1.0 for `mass_saturating_descriptor` too, with the
same certainty as every other family, because the identity does not depend
on which family's `P_front` is low. This amendment does not alter PRR-1's
text (a pre-registered prediction is not edited after the fact); it records
that PRR-1, if scored, should be read as evaluated against a
mis-specified (unconditional-flavored) expectation, and the implementation
reports R3's recall as the exact constant `1.0` rather than computing a
sample proportion or interval for it.

## Optional, zero-cost consistency check: R1 = R3 = R5 downstream identity

**Not a new arm. A control assertion**, derived once and checked
mechanically wherever it applies (Step 5 test 4), never used to justify or
adjust any arm's score.

**Claim.** For any seed whose front contains a row with a **unique**
maximum `valid_r2` (no valid_r2 tie on that front), R1, R3, and R5 cast
*identical* cross-seed votes for that seed, and therefore -- summed over
every seed of a case -- produce identical stage C/D/E labels,
`selection_count`, `false_structure_rate_proxy` contribution, and
`final_downstream_recovery` contribution for that case.

**Proof.** The frozen vote-reduction rule (section 5's boxed paragraph) is
"a seed's cross-seed vote is cast by the `argmax(valid_r2)` row among that
seed's own retained set," identically for every multi-row arm. Let `m` be
the front row with the (by assumption, unique) maximum `valid_r2` on this
seed's front.

- **R1** retains only `m` (its within-seed rule, section 5, is
  `argmax(valid_r2)` itself) -- its retained set is `{m}`, so its vote is
  `m` trivially.
- **R3** retains the whole front, so `m in R3`'s retained set. `m` has
  the maximum `valid_r2` over the *entire* front, hence also over R3's
  retained set (the whole front) -- R3's vote is `argmax(valid_r2)` over a
  superset that still has `m` as its unique maximizer, so R3's vote is `m`.
- **R5** retains the Pareto-nondominated subset in `(valid_r2, -complexity)`.
  `m` cannot be dominated: domination requires a rival with `valid_r2 >=
  m`'s (with at least one strict inequality across the two axes), but no
  rival has `valid_r2 >= m`'s by the uniqueness assumption, so `m` is
  always Pareto-nondominated and `m in R5`'s retained set. By the same
  argument as R3, `m` remains the unique `valid_r2`-maximizer within R5's
  retained set, so R5's vote is `m`.

All three retained sets contain `m` as their unique `argmax(valid_r2)`
member, so all three arms cast the identical vote `m` for this seed. This
holds seed-by-seed; if it holds for every one of a case's 30 seeds (i.e.,
no valid_r2 tie occurs on any of that case's 30 fronts), the case's entire
downstream pipeline -- grouping, stage label, `selection_count` -- is
byte-identical across R1/R3/R5 for that case, since grouping is a
deterministic function of the 30 per-seed votes alone (section 5's boxed
rule + `rc5_selection.group_and_select`, held fixed across every arm per
Control 3).

**Tie-break, when a valid_r2 tie does occur (needed for Step 5 test 5).**
No row-level tie-break for `argmax(valid_r2)` (or any of R1/R3/R4/R5/R6's
own selection criteria) is stated anywhere in the frozen preregistration.
The one tie-break precedent that exists anywhere in the frozen materials
is R0's own production rule: `rc5_selection.select_row_label` computes
`argmax(score)` via `equations["score"].idxmax()`, and pandas' `idxmax()`
is documented to return the **first** occurrence of the maximum in the
Series' existing order -- which, for a PySR-emitted front, is ascending
`front_rank` (lowest complexity first). This amendment adopts the
identical convention (lowest `front_rank` wins any tie) for every
within-seed/vote-reduction selection this protocol performs, as the least-
invented choice available: reusing R0's own frozen tie-break exactly,
rather than registering a new one. This affects the R1=R3=R5 identity only
by narrowing its scope to "no valid_r2 tie" cases, per the identity's own
stated precondition -- it does not resolve what happens *within* a tie
(R1/R3/R5 remain byte-identical even under a tie by this same tie-break
rule, since all three would independently break the tie the same way over
the same candidate set; the "no tie" qualifier is conservative, not
strictly required, but is kept because it is what section 5's request
literally specifies).

---

## Amendment provenance

| Field | Value |
|---|---|
| Amendment version | v1.0.0 |
| Source authority | `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` (`f4c1105`), sections 3, 5, 5.1, 6, 7, 13 |
| Prior derivation reused (not re-derived independently) | `muru-v2-retention-decision-theory` memory (O1, O3, O4), branch `claude/muru-v2-retention-theory-b0a3e4` commit `3c5bbab` -- theory-only, itself never executed E4a |
| Master-reconciliation approval | `muru-v2-master-reconciliation` memory: "The 90-vs-36 EVAL denominator discrepancy is resolved: 90 is correct" |
| Historical document edited in place | None |
| New arms added | None |
| Thresholds changed | None |
| Primary endpoint changed | None |
| Routing gate changed | None |
