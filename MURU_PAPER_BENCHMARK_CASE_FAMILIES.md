# MURU paper benchmark case families

The registry freezes 20 families, F01–F20. They cover scalar truth under
noiseless, moderate-noise, stronger-noise, missing-energy, and boundary-scale
conditions; no-scalar, mass-only, simple, nonlinear, interaction, distractor,
and equivalent-form conditions; M1/M2/M3 and combined violations; difficult
algebra; target-specific nulls; and adversaries.

## F19 variant applicability

| Variant | Scalar truth | M0 truth | Symbolic truth | Applicable endpoints | Expected behavior |
|---|---|---|---|---|---|
| F19A descriptor-link permutation | yes | M0 | no | scalar endpoints, M0 specificity, false-null structure | Preserve trajectories while descriptor acceptance is false-null structure. |
| F19B mass-preserving target null | yes | M0 | mass-only allowance | scalar endpoints, M0 specificity, false-null structure | Preserve mass-only truth while unsupported non-mass structure is false-null structure. |
| F19C response-cell resampling | no | not applicable | no | response-structure diagnostic, false-null structure | Flag non-evaluable destroyed trajectories. It is outside scalar, M0, and symbolic recovery denominators. |

The historical within-compound energy permutation is excluded as a scalar-target
null. Every F19 mechanism has an information-destruction test.
