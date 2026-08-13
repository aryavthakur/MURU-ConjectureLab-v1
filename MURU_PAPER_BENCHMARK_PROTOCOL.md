# MURU paper benchmark protocol

## Scope

This is a fully synthetic prospective computational validation benchmark. It
does not validate a real biological or instrumental system. Phase 3 remains
`STOP BEFORE PHASE 4`; Type 2 remains `DO NOT AUTHORIZE PHASE 4`; the
confirmation set stays sealed; and no real-data symbolic discovery is permitted.

The benchmark contains 380 cases: 80 Development, 240 Held-out, and 60
Challenge. Each case has 180 synthetic compounds in 30 scaffold groups, split
into 20 training, five validation, and five test groups on energies 15, 30, 45,
60, 75, and 90. Challenge cases do not enter primary denominators.

The primary claim is: under controlled, prospectively frozen synthetic
conditions, MURU can recover meaningful family-level mathematical structure
while rejecting specified null and adversarial worlds.

## Execution boundary

The scalar protocol fits all shared objects from training trajectories only. It
then estimates each validation or test compound independently against those
frozen objects. A held-out run is refused until the evaluated implementation
commit, strict evaluator, grammar, engine settings, runtime budget, hashes,
preflight, and clean-tree check are all locked and verified. Current status is
`PENDING_LOCK`; this document does not authorize held-out execution or Phase 4.

## Development-only preflight

The preflight may measure Development runtime, CPU time, peak memory, engine
failures, candidate counts, and artifact size. It cannot load or score a
held-out record. A locked-engine preflight must establish runtime feasibility
before final executable freeze. Development scientific performance cannot alter
the case architecture, generator, coefficients, endpoints, grammar, or
thresholds.
