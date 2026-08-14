# Table 1. Benchmark Partitions and Case Families

**Status: Fully populated from frozen sources.** Total: 380 cases (80 Dev, 240 Held-out, 60 Challenge).

| Family | Name | Scientific Question | Scalar Truth | M0 Truth | Symbolic Truth | Dev | Held-out | Challenge | Applicable Endpoints |
|---|---|---|---|---|---|---:|---:|---:|---|
| F01 | noiseless scalar collapse | recover unambiguous collapse | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F02 | moderate-noise scalar collapse | recover under moderate noise | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F03 | stronger realistic noise | characterize graceful degradation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F04 | missing-one-energy | recover with declared missingness | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F05 | boundary-scale | detect profile boundaries | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, boundary hit |
| F06 | no molecule-specific scalar truth | reject an unsupported scalar | no | M1 | none | 4 | 12 | 3 | M1 sensitivity |
| F07 | mass-only g truth | avoid invented non-mass structure | yes | M0 | mass only | 4 | 12 | 3 | scalar, parameter recovery, false extra structure, structural safety |
| F08 | simple descriptor law | recover a monotone descriptor law | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F09 | nonlinear descriptor law | recognize saturation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F10 | interaction law | recognize interpretable interaction | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F11 | irrelevant distractors | exclude independent nuisance variables | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F12 | correlated distractors | separate support from correlation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F13 | horizontal-shape violation | detect M1 | no | M1 | none | 4 | 12 | 3 | M1 sensitivity |
| F14 | high-energy vertical violation | detect M2 | no | M2 | none | 4 | 12 | 3 | M2 sensitivity |
| F15 | low-energy vertical violation | detect M3 | no | M3 | none | 4 | 12 | 3 | M3 sensitivity |
| F16 | combined mild non-scalar violation | flag combined violations | no | M1+M2+M3 | none | 4 | 12 | 3 | M1, M2, M3 sensitivity, scored independently |
| F17 | equivalent symbolic forms | canonicalize equivalent laws | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F18 | algebraically difficult, predictively simple | separate prediction from exact algebra | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F19 | target-specific null worlds | prevent specified null structure from being accepted | by variant | by variant | none / mass-only allowance | 4 | 12 | 3 | false null structure, structural safety; scalar for F19A/B |
| F20 | adversarial worlds | reject or flag specified traps | no | not applicable | none | 4 | 12 | 3 | false adversarial structure, structural safety |
| **Total** | | | | | | **80** | **240** | **60** | |

### Table 1a. F19 and F20 Variant Semantics

| Variant | Mechanism | Scalar Truth | M0 Truth | Symbolic Truth | Correct Behaviour |
|---|---|---|---|---|---|
| F19A | descriptor-link permutation | yes | M0 | none | Mass-only permitted; unsupported non-mass unsafe. Carries scalar endpoints. |
| F19B | mass-preserving target null | yes | M0 | mass-only | Mass-only permitted; accepted non-mass unsafe. Carries scalar endpoints. |
| F19C | response-cell resampling | no | n/a | none | Flag non-evaluable; accepted structure unsafe; UNEVALUABLE is violation. Excluded from scalar/symbolic. |
| F20A | latent driver | no | n/a | none | Reject latent-driver trap. |
| F20B | measurement coupling | no | n/a | none | Reject measurement-coupling trap. |
| F20C | out-of-grammar trap | no | n/a | none | Reject out-of-grammar trap (generating law outside grammar). |
