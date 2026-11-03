# Final Energy Interpretation

## Source evidence

The WUR primary library publication reports HCD NCE settings 15, 30, 45, 60, 75, and 90, and stepped collision-energy settings 25, 38, and 59. Local acquisition metadata identifies an Orbitrap IQ-X HCD method and filter strings such as `@hcd15.00`. Generic exported `Collision_energy` fields alone lack unit semantics, but the instrument metadata and primary paper identify these as normalized settings. MSnLib’s external measurements are recorded at HCD NCE 20 and 60. Thermo documentation distinguishes NCE (%) from absolute collision energy (V), so these values are not eV.

The frozen map is T(E)=−5.95552603907965 + 0.8618030610784555·E, with the external predictor coordinate obtained by its inverse. This bridge is empirically specified and reproducible; no committed collision-physics derivation or matched-instrument calibration establishes a physical eV↔NCE conversion.

## Claims supported

- The fixed model was evaluated on measured MSnLib outcomes under the frozen numerical input convention.
- Candidate/reference μ prediction errors can be compared under this same external frame and pipeline.
- The external P1 result is conditional on the map and two recorded HCD NCE settings.
- The Design A mapping study's frozen verdict is `INTERFACE_UNRESOLVED`.
- Public comparator rankings vary under the mapped and raw-NCE inputs; no convention-independent ranking follows.

## Claims not supported

The evidence does not establish physical comparability of collision energy across instruments, a universal energy calibration, that Design A validated any physical mapping, or generalized performance across instruments. The full-spectrum comparator P1 benchmark is a comparison of derived μ under its tested input convention, not full-spectrum fidelity.

## Exact expert question for any later physical adjudication

For the specific WUR Orbitrap IQ-X acquisition records and MSnLib Orbitrap ID-X measurements, do the recorded HCD values represent normalized collision energy (%) in the relevant software/method versions, and is there a defensible physical relation between these settings for this precursor population? Please identify the actual method metadata and any calibration experiment. Until that evidence is supplied, the empirical bridge remains computational only.
