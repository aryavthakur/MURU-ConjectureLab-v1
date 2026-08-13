# MURU paper benchmark metrics and decision rule

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

## Three frozen gates

G1 requires, for a scalar-applicable case, Spearman correlation between true and
fold-local estimated log-g of at least 0.80, held-out trajectory MAE no greater
than 0.80 of the per-energy-mean baseline, and no M0 rejection. G1 passes only
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
