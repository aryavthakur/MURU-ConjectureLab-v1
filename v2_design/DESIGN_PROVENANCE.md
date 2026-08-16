# E0 design-reference provenance

This directory carries the frozen v2 design documents into the E0 execution
worktree **unmodified**. Nothing in `v2_design/` was authored in this worktree;
every file is a byte-identical copy of the corresponding blob at design commit
`befca0d` (`claude/muru-v2-remediation-design-93dafc`, "V2 remediation
experiments prospectively designed: design artifacts only").

This worktree (`exp/v2-e0-admissible-range`) is forked from `3056c9a`
(`MURU V1 CURRENT-CONTRACT SYNTHETIC BENCHMARK COMPLETE`, the frozen v1-closed
source tip), not from `befca0d`'s own lineage, because `befca0d` and `3056c9a`
diverge at their common ancestor `5049a1a` ("Phase 1 close") and neither is an
ancestor of the other: `befca0d`'s branch never received the
`src/muru/paper_benchmark` / `src/muru/discovery` production source that E0
needs to run (`generator.py`, `adequacy.py`, `rc5_adequacy.py`, `protocol.py`,
`registry.py`), and `3056c9a`'s branch never received the v2 design prose. This
import reconciles the two by copying only the design documents' file
*contents* across, verified byte-for-byte against the source blob by sha256
(manifest below) — no merge, no rebase, and zero files under `src/`, `tests/`,
or any pre-existing v1 path touched.

## Imported files (source: `befca0d`)

| file | sha256 |
|---|---|
| `MURU_V1_FAILURE_DECOMPOSITION.json` | `ff28eca3bff77c796afd4b2167470a47ed2380fec78f2c8230963c6d3e595582` |
| `MURU_V1_FAILURE_DECOMPOSITION.md` | `adb578166a855a97cca2feb10c7bdbfb89c3c58b6f3c3e4472edcf772eb64806` |
| `MURU_V1_G1_FAILURE_TAXONOMY.csv` | `0a7924f13e49bbe4cfa7fcafef6bc24ed6fac8d05304379c5c85fc2447dd0940` |
| `MURU_V1_G2_FAILURE_TAXONOMY.csv` | `e01ee0083ba26a28faf4b3cb145845247b0e3505481bf38f3826d7926a2c2ea6` |
| `MURU_V1_G3_FAILURE_TAXONOMY.csv` | `a5c7b52e0b431047c1132a50f3e36bcf568270a4a87284616340310f2f90c814` |
| `MURU_V1_ROOT_CAUSE_RANKING.json` | `151638c71c36cefa2c1f8869e65eba6d24de6d2cdfa5457809e526fe63f38a42` |
| `MURU_V1_ROOT_CAUSE_RANKING.md` | `6d37b70c8dc004d2624c7dd3f8ae60bcbfe20cfb6816a867ec0b01acbc6141f7` |
| `MURU_V2_A1_STUDY_DESIGN.md` | `8de7b59e32ae3a753c8713f7b07183e33b44b0ffd0d30a52c79da9fe0d46ec59` |
| `MURU_V2_CAUSAL_DECISION_TREE.md` | `1b458726b8fb9ed09dee6f5e22e3ff65739754a58d0f83fd7b00d399b5a1bf0b` |
| `MURU_V2_G2_PARETO_STUDY_DESIGN.md` | `daad48023ee7522f6c42459a7b0645dc711cbf4389f4d85149b21203f0d2e488` |
| `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` | `01eb2c8977fce9fb3cadf241fd5b5b8d0d3add7e86faf85e9d6a5d6852aa110f` |
| `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json` | `d8984827b6c213ec56896664233cfad0b44fb813e3a415e7e73a65c26bde3e7d` |
| `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` | `775e3d43f44d91efa8aa724c0bd2b7f8aa598d047cfceda208fde02490c3af27` |

Verified: `git show befca0d:<path> | sha256` equals the sha256 of the file
written into this worktree, for all 13 files, at import time.

## Scope

This worktree executes **only** E0 (`A1_ADMISSIBLE_RANGE_PROVENANCE`). E1-E6
are out of scope here; `MURU_V2_G2_PARETO_STUDY_DESIGN.md` and
`MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` (E2-E5) are imported only because
they are part of the same frozen design commit and E0's own citation
discipline (design §2.2) references the full experiment register; they are
not read for any E0 decision.
