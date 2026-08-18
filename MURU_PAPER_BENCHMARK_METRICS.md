# MURU paper benchmark metrics and decision rule

Amended by [`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md`](MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md),
which binds the M0/M1/M2/M3 adequacy decision rule that this document's G1 gate
depends on. A1 changes no denominator and no gate threshold.

## Endpoint denominators

The held-out population has 240 cases. Endpoint denominators are reconstructed
from frozen case/variant applicability:

| Endpoint | Held-out denominator |
|---|---:|
| G1 scalar competence | 164 |
| G2 family recovery | 144 |
| G3 principal structural safety | 36 |
| F07 false extra-structure component | 12 |
| F19 false-null-structure component | 12 |
| F20 false-adversarial-structure component | 12 |

F19C is not applicable to scalar, M0-specificity, or symbolic recovery. It is
applicable to false-null-structure because an unflagged, response-destroyed
world would be an invalid structural acceptance.

## Adequacy endpoint scoring (Amendment A1)

The adequacy ladder compares M0 with M1 (horizontal shape), M2 (high-energy
vertical/asymptotic), and M3 (low-energy vertical) on the case's 30 test
compounds. Amendment A1 gives these already-frozen denominators a fully
deterministic scoring rule; the denominators themselves are unchanged, except
where the already-frozen F19 applicability amendment requires it.

| Endpoint | Held-out denominator | Case-level success |
|---|---:|---|
| M0 specificity | 164 | adequacy status is `M0_NOT_REJECTED` |
| M1 sensitivity | 36 | the M1 detector fires |
| M2 sensitivity | 24 | the M2 detector fires |
| M3 sensitivity | 24 | the M3 detector fires |

A detector fires only when at least 24 of the 30 test compounds are evaluable
for that contrast and at least 20 of them are practical wins, where a practical
win requires the alternative's within-compound leave-one-energy-out MAE to be no
more than 0.90 of M0's. M0 is rejected when any alternative fires, and may be
recorded as not rejected only when all three contrasts are evaluable and none
fires. Detector identity is preserved: a wrong alternative firing may reject M0
but never satisfies another detector's sensitivity endpoint, and for F16 each
detector endpoint is scored independently. Insufficient data, boundary
limitation, numerical failure, model fit failure, and timeout produce
indeterminate adequacy states and are never M0 acceptance. A1 states the full
rule, its rationale, and its failure semantics.

## Three frozen gates

G1 requires, for a scalar-applicable case, Spearman correlation between true and
fold-local estimated log-g of at least 0.80, held-out trajectory MAE no greater
than 0.80 of the per-energy-mean baseline, and no M0 rejection under the
Amendment A1 rule — the adequacy component is satisfied only by an
`M0_NOT_REJECTED` status, never by an indeterminate or failure state. G1 passes only
when its lower 95% Wilson bound >= 0.70 across 164 cases. The rank threshold
requires strong scale recovery; the MAE condition requires useful out-of-sample
trajectory prediction; the adequacy condition prevents scalar interpretation
when M0 is contradicted.

G2 passes only when the family-level recovery lower 95% Wilson bound >= 0.70
across 144 applicable cases. A family success requires the frozen correct active
block support and mathematical family. Parameter recovery, predictive
equivalence, and exact algebra are separate secondary measures.

G3 combines 36 equally weighted opportunities: F07 false extra-structure
acceptance, F19 false-null-structure acceptance, and F20 false-adversarial-
structure acceptance. G3 passes only when its upper 95% Wilson bound <= 0.15.
The report keeps the three component numerators, denominators, rates, and
intervals beside the aggregate.

The paper makes the positive umbrella claim only when preconditions hold and
G1, G2, and G3 all pass. An adequacy failure that invalidates g therefore fails
G1. Any failed gate blocks the positive claim while retaining descriptive
endpoint reports.
