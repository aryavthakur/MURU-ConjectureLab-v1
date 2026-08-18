# MURU paper benchmark freeze record

## Content-freeze versions

| Designation | Commit | Status |
|---|---|---|
| ORIGINAL BENCHMARK CONTENT FREEZE V1 | `d94d2c9` | preserved permanently, never rewritten |
| EFFECTIVE BENCHMARK CONTENT FREEZE | the Amendment A1 commit, tagged `benchmark-content-freeze-a1` | the contract supplied to Engineering RC 2 |

Amendment A1 is a pre-execution amendment: it binds the previously unspecified
M0/M1/M2/M3 adequacy decision rule that G1 depends on. It was prepared before
any Development or Held-out scientific outcome was executed, scored, or
inspected. `d94d2c9` did not contain this rule and is not modified. Every
frozen scientific artifact unrelated to the adequacy rule remains byte-identical
to `d94d2c9`; `artifacts/paper_benchmark_amendment_a1.json` records the
per-path SHA-256 verification of that claim. See
[`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md`](MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md).

A1 does not lift any refusal. The implementation lock stays `PENDING_LOCK`, the
held-out guard still refuses execution, and Phase 4 remains unauthorised.

## Content and executable freezes

The content freeze consists of the case registry, fully synthetic generator,
partition assignment, truth schema, generated input artifacts, metrics,
endpoint denominators, null definitions, hashes, and development-only preflight
record. The executable freeze additionally requires a locked MURU implementation
commit, strict evaluator version, grammar, engine configuration, runtime budget,
complete engine preflight, verified hashes, and a clean tracked tree.

`PENDING_LOCK` forces the held-out guard to refuse execution. No command may
load or score held-out data before the complete executable freeze. A content
freeze preparation status of `WAITING_FOR_LOCKED_IMPLEMENTATION` is not a
held-out result, and it does not authorize Phase 4.

## Required artifacts

- `artifacts/paper_benchmark_partition_manifest.json`
- `artifacts/paper_benchmark_case_manifest.json`
- `artifacts/paper_benchmark_truth_manifest.json`
- `artifacts/paper_benchmark_hash_inventory.json`
- `artifacts/paper_benchmark_preflight.json`
- `artifacts/paper_benchmark_content_freeze.json`
- `artifacts/paper_benchmark_amendment_a1.json`
