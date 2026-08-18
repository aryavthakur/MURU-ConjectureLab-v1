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

## Frozen execution definition and provenance roles

The frozen execution definition is the first non-quarantined PB__NCAL__ durable seed record, durably written at 2026-08-14T10:08:31-04:00 (10:08:31 EDT). Preflight, manifest/directory setup, runner-sidecar start, and the inferred backend.search start interval are provenance stages, not durable seed records; the record identity may not be reselected from later outputs.

The distinctions are intentional:

| Provenance stage | What it establishes | What it does not establish |
| --- | --- | --- |
| Preflight | Pre-execution provenance exists. | A directory/manifest setup, runner start, or seed record. |
| Calibration directory and manifest setup | The directory/manifest setup event occurred. | A runner-phase start or durable seed record. |
| Runner sidecar `started_utc` | The runner phase had started. | The exact first `backend.search` start or a durable record. |
| First `backend.search` start | An inferred open interval, not an exact timestamp. | A substitute for the first durable record. |
| First non-quarantined `PB__NCAL__` durable record | The frozen execution identity. | Permission to reselect a later output. |

No calibration, held-out, development, or confirmation outcome was opened,
read, compared, or used to create this record. The clarification changes no
scientific claim, metric, selection, benchmark result, or frozen A3.4 byte.

## Exact EDT chronology

| Event | Timestamp | Immutable reference |
| --- | --- | --- |
| Preflight created | 2026-08-13T23:59:01-04:00 | Read-only preflight provenance timestamp. |
| Calibration directory and manifest setup | 2026-08-14T10:08:17-04:00 | Read-only directory/manifest provenance timestamp. |
| Runner sidecar `started_utc` | 2026-08-14T10:08:17.932248-04:00 | Source field name retained; recorded `-04:00` offset is EDT. |
| First `backend.search` start | Strictly after 2026-08-14T10:08:17.932248-04:00 and strictly before 2026-08-14T10:08:31-04:00 | Inferred open interval, not an exact timestamp; bounded only by the runner-sidecar start and first non-quarantined durable-record timestamps. |
| First non-quarantined `PB__NCAL__` durable seed record | 2026-08-14T10:08:31-04:00 | Frozen execution record. |
| A3.4 creation commit | 2026-08-14T11:56:17-04:00 | `d0ea5d4b0309e4e95dcab4035b9be66e166765b1` |
| A3.4 freeze commit | 2026-08-14T11:56:23-04:00 | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` |
| Annotated A3.4 freeze tag | 2026-08-14T11:56:26-04:00 | `benchmark-content-freeze-a3-4` tag object `326727d5f17943b22f014262dcf42f5cf043ba42` |
| Runner finished | 2026-08-14T11:58:40.935600-04:00 | Read-only runner provenance timestamp. |
| Terminal summary files | 2026-08-14T11:58:41-04:00 | Read-only terminal-summary provenance timestamp. |
| A3.4 lineage merged with `--no-ff` | 2026-08-14T12:27:08-04:00 | `5055f69097aa0c6ce2ded6a3e57f0edfaea69faf` |

All timestamps use EDT (UTC-04:00). This chronology uses only read-only
temporal provenance metadata; it contains no calibration or sealed-outcome
payload. The subsequent erratum commit and annotated tag deliberately are not
self-timestamped in this record. Their immutable Git identity is governed by
the annotated `a3-4-temporal-provenance-erratum` ref, which must resolve to the
commit containing this corrected record; Git is authoritative for those later
commit/tag timestamps.

## Additivity guarantee

This file and its paired JSON ledger are new audit artifacts. They bind the
existing A3.4 source identity and temporal rule without altering any frozen
science path. The accompanying regression test recomputes the A3.4 SHA-256
from the working tree to make any later byte change visible.
