# MURU-WUR-v2 — Publication Release Record

**Release status:** FINAL PROJECT STATE FOR PUBLICATION  
**Publication cutoff:** 2026-09-19  
**Candidate:** `V2_TA_MORGAN_JOINT`

This record freezes what the repository supports at project close. It intentionally includes completed studies and explicitly excludes unfinished or merely proposed work.

## Supported central claim

MURU-WUR-v2 predicts collision-energy-dependent fragmentation extent with a frozen one-scale trajectory model whose compound scale is predicted from Tier A molecular descriptors plus Morgan-count structural features.

On scaffold-held-out development data, the selected v2 candidate reduced pooled trajectory error relative to the refitted Tier A comparator (P1 0.1160 vs 0.1305; ratio 0.889, simultaneous interval 0.860–0.918).

A separately frozen MSnLib confirmation study then produced **MODEST EXTERNAL CONFIRMATION** on 1,789 scored compounds in 1,687 scaffold groups: P1 0.12961 vs 0.13353; ratio 0.9707 with 95% interval 0.9524–0.9893. The external gain was modest, did not improve tail failure, and disappeared in the most structurally novel quartile.

## Completed evidence included in the release

### 1. WUR Stage 3 external validation of v1-generation ridge
`MURU_WUR_STAGE3_RESULT.md`

404 sealed positive-mode trajectories, 275 scaffold groups. The frozen ridge candidate beat the pre-WUR comparator and mass-only baseline under the preregistered endpoints.

### 2. MURU-WUR-v2 development program
`MURU_WUR_V2_FINAL_REPORT.md`

Experiments 1–13 identified `V2_TA_MORGAN_JOINT` as the simplest admitted model within 1% of the best observed candidate. The main development gain came from adding local structural information to the scale predictor. Trust/abstention signals and the proposed shape extension did not survive their frozen bars.

### 3. MSnLib Confirmation Study 2
`MURU_V2_MSNLIB_CONFIRMATION_V2_RESULT.md`

Frozen decision: **MODEST EXTERNAL CONFIRMATION**. This is the principal independent external confirmation for v2.

### 4. Public comparator benchmark
Comparator-benchmark result document on the completed study stack.

Under the preregistered primary energy mapping, MURU had lower pooled two-rung fragmentation-extent error than the tested FIORA-OS v0.1.0, ICEBERG 2.1 and GLACIER public checkpoints. This result is **energy-interface dependent**: the preregistered raw-NCE diagnostic reverses the direction against ICEBERG 2.1 and GLACIER. Therefore this release does **not** claim state of the art or universal superiority.

### 5. Collision-energy interface Design A
`MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_RESULT.md`

Frozen verdict: **INTERFACE UNRESOLVED**.

Raw NCE (K1) had the highest observed composite score, but the adjusted intervals did not satisfy the preregistered support rule. No CE convention is claimed as correct.

## Explicitly excluded from the publication evidence

- Prospective Design B: **TERMINATED / NEVER EXECUTED**.
- Any procurement, wet-lab acquisition, or new physical experiment.
- Any proposed CyanoMetDB follow-up.
- Any unfinished repair experiment, E4a/E6 plan, or other future-work item not already completed.
- Any state-of-the-art claim.
- Any claim that the CE interface has been resolved.

## Final scientific scope

The release supports a constrained conclusion:

> MURU-WUR-v2 is a compact structural scale model for collision-energy-dependent fragmentation extent. It shows strong scaffold-held-out development improvement and modest independent confirmation on MSnLib under a fixed zero-parameter energy map. Its advantage over public full-spectrum comparators depends materially on collision-energy input convention, and the independent CE-interface adjudication remained unresolved.

That is the publication claim. No stronger claim is authorized by this repository state.
