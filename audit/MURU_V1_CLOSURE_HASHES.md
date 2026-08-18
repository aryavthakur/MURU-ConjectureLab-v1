# MURU ConjectureLab v1 — Closure Artifact Hashes

SHA-256 of every artifact produced by the restoration and closure. Restoration module, script and
test hashes are in `MURU_HELDOUT_RESTORATION_FINAL_DISPOSITION.md` §8; this file covers the closure
layer and the inherited evidence.

## 1. Closure artifacts

| File | SHA-256 |
|---|---|
| `audit/MURU_V1_FINAL_SCIENTIFIC_DISPOSITION.md` | `3d3a1fee10ff438269c3a7340be725921b44cb9f73b436342e69f735b84d12f5` |
| `audit/MURU_CHALLENGE_DISPOSITION.md` | `fe3627e431fd95cbcaa10c13f812bb2226af9e44b24420ea486a32488530327f` |
| `audit/MURU_CHALLENGE_BLIND_ADJUDICATION.md` | `14a3c037db09991f40f1b6f91d5ff390524cadda32b462a84e3ee2cdeba12eed` |
| `audit/MURU_HELDOUT_RESTORATION_HOSTILE_REVIEW.md` | `7ce319c22e12bc80af598832e9c653478fbcb0f2e9266b1fe8ad4da65b57029c` |
| `scripts/build_muru_v1_manuscript_tables.py` | `2d37869e6b08d8bd33707971aca434fa4130ac2266478c7fa98589704e3e78a6` |

## 2. Manuscript package

| File | SHA-256 |
|---|---|
| `paper/muru_v1_closure/METHODS.md` | `8d5b569c6547b78248b83075d54c0065c588cdc2e579d18df26ea90b722e5e17` |
| `paper/muru_v1_closure/RESULTS.md` | `c487c81ba15714b1bda12958005773943dba5c8f84c8b183f60b71a8e5b797fa` |
| `paper/muru_v1_closure/LIMITATIONS.md` | `85de1cf6c2bcabf8b0d9d7c31027d4f46b9d8f88a1a015758e696a443769befd` |
| `paper/muru_v1_closure/GOVERNANCE_CHRONOLOGY.md` | `a04736deb5c9bedf093aef25fdb21ad5c6055be0623cc450fb82008b2479aa50` |
| `paper/muru_v1_closure/REPRODUCIBILITY_INVENTORY.md` | `eab651ad4dcf57a5425075613ca9196b97bf54182900cbe8d8e11806336e85af` |
| `paper/muru_v1_closure/POST_RESULT_FUTURE_WORK_MURU_V2.md` | `e6dd352e09bf092af7c60a0cbbefc66601c9049228a88a8d14124d8c11313cfb` |

Tables T1–T9 and figure data F1–F4 are regenerated deterministically by
`scripts/build_muru_v1_manuscript_tables.py` from the committed analysis artifacts and are therefore
pinned transitively by those artifacts' hashes rather than listed individually.

## 3. Inherited evidence, hashes verified before use

The five forensic rescue artifacts, each verified against the hash recorded in the rescue's own
final decision before any of its content was relied upon:

| File | SHA-256 |
|---|---|
| `audit/MURU_HELDOUT_RESCUE_AUTHORITY_MATRIX.md` | `2e9b0534ff42fb45ce4e90c8e4854b50c914902c8a0572719be21834ca60a8bf` |
| `audit/muru_heldout_rescue_authority_matrix.json` | `b11af625f72dba3121ec26a2d59cfb8e7ebcf9c0af6aace4922d960bd1f16c5c` |
| `audit/MURU_HELDOUT_RESCUE_RAW_INTEGRITY.md` | `a8d97a5400b4119212a42db54ceda9cc60f4afe885959aa2a96d2f3a60d30e04` |
| `audit/MURU_HELDOUT_RESCUE_INDEPENDENT_RESULT.md` | `2c7b2529dc516a426c5283a33b8b3b4c3cfddbbc2dd9d7d63c65bdcac3799862` |
| `audit/muru_heldout_rescue_independent_result.json` | `b750d5c0af738a1226c293e8d13c3030d1d2c3cfbd7a5fd9dd6834b100416363` |

## 4. Sealed evidence identity

| Object | Digest |
|---|---|
| Run commit | `8d87143d4280602323aa33ee0b5481aaef0fb4a8` |
| Execution manifest | `bcd197dce732f2b2ad156d04ac4285ab23371a8dce40cb1f98281615a01afd08` |
| Seal receipt | `df128cd9356a31e0350fbf0dcc5a359c4e9116dcebbf30bb5381ab80b2c5e9c4` |
| Global science plan | `f2a81a91346b7607f4bff5bf673eaadf60e5d058d7b9625a9e49f4d7a9732334` |
| Grammar identity | `e7c1468473e1bee32696022bf714767a2e994ee88803964f503c4804eef9097e` |
| Calibration manifest | `9950b964346581d104bf3069c992eec2599c88235f6598b2aed1bb31ac58fe0f` |
| Null-threshold table | `b9b6148276160ea84f223ff9cba3db0fb93fd974efa3e790bcacab312fe59425` |

482 of 482 sealed files re-hash to their recorded values. No sealed file was modified.

## 5. Superseded objects

Content hashes of the preserved copies are in `MURU_HELDOUT_SUPERSESSION_LEDGER.md` §1. Nothing was
deleted.

## 6. Determinism check

Re-running both drivers after the artifacts were first written produced **byte-identical** output:
`git diff results/restored/` is empty following a full re-run. The analysis is deterministic and the
committed artifacts are reproducible from the sealed evidence.

## 7. Final test state

| Suite | Result |
|---|---|
| `tests/test_heldout_analysis_restoration.py` | 33 passed |
| `tests/test_heldout_superseded_rules_differ.py` | 6 passed |
| `tests/test_heldout_hostile_lenses_have_teeth.py` | 13 passed |
| **restoration total** | **52 passed** |
| `scripts/run_heldout_restored_analysis.py` | exit 0 |
| `scripts/run_heldout_hostile_lenses.py` | exit 0 |

Two pre-existing repository failures, disclosed and deliberately not repaired, are documented in
`MURU_HELDOUT_SUPERSESSION_LEDGER.md` §5.
