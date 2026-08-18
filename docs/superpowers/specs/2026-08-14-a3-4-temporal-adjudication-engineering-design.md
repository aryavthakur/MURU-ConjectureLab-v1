# A3.4 Temporal Adjudication and RC4 Engineering Design

## Authority and scope

This design implements the user-supplied A3.4 takeover brief. The frozen
scientific authority is A3.4 (`be23b80d63fbd30227f0ab8f200dddc2121f3bfe`)
merged onto RC3.1 (`07c64c862cb32a306f5081582dacf73e09211c0a`; the brief's
version omits `158` and is not a Git object). No protected scientific file is
changed. Development, Held-out, and Confirmation data remain unopened while
engineering is built.

## Temporal provenance

The frozen RC3.1 execution rule treats a non-quarantined `PB__NCAL__` seed
record as executed science. The first durable record began at 10:08:31 EDT on
2026-08-14, before A3.4's creation at 11:56:17 EDT and freeze at 11:56:23 EDT.
No evidence shows outputs were inspected to define A3.4. The required
classification is therefore `TEMPORAL_PROVENANCE_ERRATUM_REQUIRED_OUTCOME_BLIND`.

An additive, immutable erratum will record this chronology without modifying
the A3.4 scientific amendment, its artifact, calibration procedure, or any
result. It will be tagged before implementation begins.

## Engineering architecture

RC4 adds isolated post-hoc secondary scorers. They only consume a final,
already-selected candidate expression, a constructed or later-authorized
`TruthRecord`, and frozen A3.4 constants. They contain no candidate search,
selection, partition materialization, threshold calculation, or calibration
logic.

- `a34_contract.py` exposes version-bound constants, fixed denominators,
  reference-frame generation, canonical serialization, and fail-closed digest
  validation. Frames are regenerated only through the frozen generator's
  covariate primitive under IDs `PB|PRED_EQUIV|FRAME|000` through `011`.
- `a34_parameter_recovery.py` parses a candidate under the frozen primitive
  grammar, differentiates symbolically at the fixed neutral anchor, and emits
  per-case / fixed-denominator Wilson summaries.
- `a34_predictive_equivalence.py` evaluates the supplied candidate and truth
  on the validated 2,160-row reference design, allowing only positive
  multiplicative alignment over the frozen valid set.
- `a34_record.py` binds results to the source final-candidate digest, frozen
  contract digest, and reference digest with deterministic serialization.
- `pb_35_a3_4_integrity.py` verifies byte identity of A3.3/A3.4 science paths
  against `be23b80` and fails when new endpoint modules import candidate
  selection, calibration, or partition-materialization APIs.

## Failure behavior

Every unparseable expression, non-finite derivative/evaluation, nonpositive
anchor, reference digest mismatch, invalid-domain shortfall, nonpositive or
non-finite scale, zero variance, or threshold miss is a deterministic failure.
No scorer repairs, refits, aligns an intercept, reselects a candidate, or
reduces a denominator.

## Testing and verification

All endpoint tests use constructed truth records and expressions; they do not
generate a benchmark partition or inspect calibration/held-out outcomes. Tests
cover all specified A3.4 boundaries, all twelve per-frame digests and the
aggregate digest, no-pole F09 reference frames, algebraic/scale invariance,
and source-level sealed-boundary checks. The full suite is also run with the
project virtualenv; its existing failure caused by absent untracked
`artifacts/p2_compounds.parquet` is documented separately from RC4 tests.
