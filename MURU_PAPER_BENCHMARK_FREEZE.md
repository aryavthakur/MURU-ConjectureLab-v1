# MURU paper benchmark freeze record

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
