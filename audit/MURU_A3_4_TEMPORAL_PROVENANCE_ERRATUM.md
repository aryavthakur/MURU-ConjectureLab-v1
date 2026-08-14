# MURU A3.4 Temporal Provenance Erratum

**Classification:** `TEMPORAL_PROVENANCE_ERRATUM_REQUIRED_OUTCOME_BLIND`

**Scope:** additive governance record only

**Scientific change:** none
**Outcome inspection:** none

## Purpose

This erratum records a temporal-provenance clarification for frozen Amendment
A3.4. It does not replace, amend, regenerate, or otherwise edit the A3.4
scientific artifact. The frozen source is
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md` at commit
`be23b80d63fbd30227f0ab8f200dddc2121f3bfe`, whose SHA-256 is
`c699230ab8995461b73a6db2b3fecab661f744e937f40ebe2db34fa8c8c11ada`.

## Frozen first-durable-seed definition

The first durable seed is the first seed record persisted in version control
before any outcome inspection; its identity is frozen at that commit and may
not be reselected from later outputs.

No calibration, held-out, development, or confirmation outcome was opened,
read, compared, or used to create this record. The clarification changes no
scientific claim, metric, selection, benchmark result, or frozen A3.4 byte.

## Exact 2026-08-14 EDT chronology

| Event | Timestamp | Immutable reference |
| --- | --- | --- |
| A3.4 frozen | 2026-08-14T11:56:23-04:00 | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` |
| A3.4 lineage merged with `--no-ff` | 2026-08-14T12:27:08-04:00 | `5055f69097aa0c6ce2ded6a3e57f0edfaea69faf` |

All timestamps are EDT (UTC-04:00). The subsequent erratum commit and
annotated tag are deliberately governed by Git metadata: the tag
`a3-4-temporal-provenance-erratum` is created only after this record is
committed and its regression test is green.

## Additivity guarantee

This file and its paired JSON ledger are new audit artifacts. They bind the
existing A3.4 source identity and temporal rule without altering any frozen
science path. The accompanying regression test recomputes the A3.4 SHA-256
from the working tree to make any later byte change visible.
