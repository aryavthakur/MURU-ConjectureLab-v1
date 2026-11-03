# Phase 5 Verification — Census Neutral-Filter Erratum

## Corrected finding

The recovered Phase 2 verifier identifies a call-order defect. The helper signature is `neutral_scaffold(smiles, key)`, while the historical call expression supplied `(group_key, smiles)`. Reconstructing the historical and corrected neutral-scaffold sets changed the set size from **2,090** to **766**, but the recorded downstream population membership did not change in any of the four recorded census frames.

| Frozen frame | n | Population SHA-256 | Historical vs. corrected membership |
|---|---:|---|---|
| DESIGN step 10b (`r_b`) | 39,238 | `8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e` | symmetric difference 0 |
| DESIGN step 12b (`s10b`) | 47,742 | `84828abfe29e595379baceb993e97edc846268f255935a66b675c59407c1e283` | symmetric difference 0 |
| DETECTED_POSITIVE step 10b (`r_b`) | 32,154 | `feaade612cb35cde6c627b813b9dc69a9dae966ed1bc05b7fd6ba0af9741e451` | symmetric difference 0 |
| DETECTED_POSITIVE step 12b (`s10b`) | 39,236 | `b526ca0b9b93c7dc39f8b463d2b77f40541b44b0b301e7e3bdacebfc52737aca` | symmetric difference 0 |

For each frame, the reconstructed historical membership also matched the frozen count and population hash. The recovered verifier’s aggregate flags were `all_historical_reconstructions_match_frozen_counts_and_hashes=true`, `all_four_recorded_memberships_unchanged=true`, `watched_inputs_unchanged=true`, and `verification_status=PASS`.

## Reproduction source and hashes

| Source or input | SHA-256 | Role |
|---|---|---|
| Recovered Phase 2 verifier `publication_phase2/scripts/verify_census_neutral_filter.py` | `cf9a3464443e492cb93493501c834345e2ac3f6aed59dd6bd785cd485a204d4f` | Reconstructs the historical and corrected membership chains |
| Recovered Phase 2 evidence `publication_phase2/evidence/census_neutral_filter_verification.json` | `3b3e8b8cb40b669e7eaee1a051ce89b5a1079811ba5f8e89cb69adea0de621ed` | Prior recorded frame results and source checks |
| Frozen census record `artifacts/wur_v2/external_census/msnlib_census.json` | `e487b23ae8b3e6d12f741e8797da773dc629b6090e8f6cb425a677f5eaf7c3bf` | Frozen census source record |
| Frozen census implementation `scripts/wur_v2/census/msnlib/msnlib_census.py` | `1ee904b3c232380a1f308c3051e3819a0ce3be0b37887b9823d4acfc0798c303` | Historical run-chain implementation |
| Recovered `p2_compounds.parquet` | `59d54748a9888be0029490bae39a22462f8ccef1114386d1f00fa467c60f2119` | Compound input used for reconstructed frame chain |
| Recovered `trajectories.parquet` | `0b2ea8302485fdb91e96b3d7e6bbb673a014f05b314d61e1c434fb3ae88c5881` | Trajectory input used for reconstructed frame chain |
| DETECTED_POSITIVE metadata parquet | `afb798ea0f892ac39a549b0d7cc01c2677f891ae8433df24b5df7cf784fe6127` | Recorded metadata input; no peak/spectrum quality columns were read |
| Phase 4 raw verifier output captured outside repository | `fa16611a3f3251af1d965f3576482977dfca00bc26ceb65ddebc42fbf93f7540` | Full Phase 4 verifier JSON, contains local absolute paths |

The recovered verifier was run in the Phase 2 worktree’s Python environment because the system Python environment lacked RDKit. The first system-Python attempt failed at dependency import; the second, with the recovered `.venv`, completed with `PASS`. The verifier reports that its read was non-mutating and that watched input hashes were unchanged. It short-circuited a strict-similarity diagnostic because that branch cannot change step 10b/12b membership. This does not imply that every historical diagnostic was rerun.

## Phase 4 artifact defect

The Phase 4 public-safe file `publication_phase4/verification/census_neutral_filter_verification_rerun.json` is a lossy sanitized derivative, not the full verifier record. It reports PASS but omits frame identity (`DESIGN` versus `DETECTED_POSITIVE`), frozen population hashes, watched-input hashes, the neutral-scaffold set sizes, and the verifier’s full source metadata. Its `source_input_hashes.population_sha256` contains one population hash, not a complete input manifest. The corresponding Phase 4 prose lists counts/hashes manually, but the JSON cannot independently substantiate that table. The raw output was kept outside the repository because its watched-input keys contain personal absolute paths; publish a path-scrubbed complete summary if machine-readable evidence is required.

The Phase 2 report directory and files are recoverable locally from a worktree based on `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`; the recorded Phase 2 audit commit `459a78a8ef0ac7a3e92d15c25be38cc8d86403b6` is absent from that worktree’s Git object database. The evidence files there are untracked. Thus local evidence is recovered, but the historical audit commit itself is not verified.

## Scope of the erratum

The defect changed the neutral-scaffold helper’s return set but had **zero membership impact in these four reconstructed frames**, based on matching counts and hashes. This does not prove that every unrecorded intermediate table, manual analysis, notebook, or downstream use was unaffected. No frozen inputs were rewritten. Phase 3’s statement that the four frames and Phase 2 records could not be located is superseded by this recovered and rerun evidence.

## Phase 6 status

No contradictory census evidence was identified in the Phase 6 source review. The Phase 5 recovered verifier record remains the authority for its four tested frames. The scope is still limited to those recorded frames; Phase 6 did not infer the defect was harmless beyond the matched membership evidence.
