# Final Census Defect Erratum

## Defect and recovered finding

The recovered Phase 2 script identifies an argument-order defect in the neutral-scaffold helper: historical call sites passed `(group_key, smiles)` to a helper expecting `(smiles, key)`. The historical neutral-scaffold set had 2,090 entries; the corrected set had 766. Phase 2 reconstructed the historical and corrected membership calculations for four recorded population frames. In all four, the historical membership output matched the frozen population hash and the symmetric membership difference after correction was zero:

| Frame | n | Frozen population hash | Finding |
|---|---:|---|---|
| DESIGN step 10b | 39,238 | `8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e` | Zero membership difference |
| DESIGN step 12b | 47,742 | `84828abfe29e595379baceb993e97edc846268f255935a66b675c59407c1e283` | Zero membership difference |
| DETECTED_POSITIVE step 10b | 32,154 | `feaade612cb35cde6c627b813b9dc69a9dae966ed1bc05b7fd6ba0af9741e451` | Zero membership difference |
| DETECTED_POSITIVE step 12b | 39,236 | `b526ca0b9b93c7dc39f8b463d2b77f40541b44b0b301e7e3bdacebfc52737aca` | Zero membership difference |

Phase 4 reran the recovered verifier with the specified RDKit environment and the recovered input worktree. The rerun passed all four frames and confirmed watched inputs were unchanged. An initial attempt with system Python failed because RDKit was not installed in that environment; the recorded worktree virtual environment succeeded. This environment failure did not modify source data.

## Scope and limitation

The zero-impact result is established for these four reconstructed frames and their recorded membership outputs. It does not prove that every unrecorded intermediate table, manual analysis, or downstream use was unaffected. No frozen historical input was rewritten. Phase 3’s assertion that the defect and frames were unavailable has been replaced with this bounded erratum.
