# MURU CE interface adjudication, Design B: preregistration

Study id: `muru-ce-interface-adjudication-design-b`. Freeze ref: `refs/muru-freeze/muru-ce-interface-adjudication-design-b`.

Governing documents: plan `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_PLAN.md` at `f7825e2` and sourcing screen `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_SOURCING_SCREEN.md` at `fa536bb`. Where this document is silent, the plan governs. New choices made here are only those needed to remove an ambiguity; each is marked **[fixed here]**.

State at freeze: no Design B MS/MS spectrum has been acquired or read, no compound has been ordered, and no prediction has been generated for any candidate. Design A stays closed; PR #8 is not touched.

## 1. Question and models

For the frozen public ICEBERG 2.1 (`msg_simulation`: `gen` sha256 `1eda5f3d...7a70`, `inten_contr` `e074c039...4f58`) and GLACIER (`msg`: `5a47cecc...db11`) checkpoints at ms-pred commit `ed8311f`, on prospectively acquired Orbitrap HCD [M+H]+ spectra: does raw NCE (K1, `CE = NCE`) outperform K2 (`CE = NCE x theoretical [M+H]+ / 500`) as the checkpoint collision-energy input? K3 (`floor(K2)`) is scored and reported descriptively only. No retraining, no fine-tuning, no other model. MURU does not participate.

## 2. Endpoint

Primary: untransformed full-spectrum cosine. Robustness only: Jensen-Shannon similarity. Both come from the frozen Design A similarity layer (`design_a/spectrum_similarity.py`, frozen config sha256 `65543686...2848`), called with its frozen defaults, `parent_mass` = theoretical [M+H]+. The prediction side is squared once from ms-pred's sqrt scale; the observed side is untransformed.

## 3. Population

- Strata by theoretical [M+H]+: L 130 to 300, N 485 to 515, H 700 to 900.
- Sourcing frame: `artifacts/ce_interface_adjudication/design_b/sourcing/eligible_universe.csv`, sha256 `5a99c75ffbc29ccec6178a2686f3608f4f4bc354ab4399acbfab67efe2b2b4bd` (frame, not population). Candidate ledger sha256 `e8c1bbe6...545d`. Exclusion-set hashes, RDKit 2026.03.5 and the sourcing scripts are pinned in the freeze manifest.
- One compound per scaffold group across the whole experiment.
- Procurement population: exactly 66 L + 66 N + 66 H, built mechanically by section 4. These 198 are the only compounds authorized for acquisition. No reserve compound is designated, and **no post-acquisition failure is replaced [fixed here]**: the 66 per stratum are the complete acquisition population and attrition is absorbed.
- Analysable target 60 per stratum; primary divergent sample 60 L + 60 H. **Every analysable compound enters the analysis, even beyond 60; none is trimmed [fixed here].** A stratum ending below 50 analysable compounds is labelled UNDERPOWERED in the result; the label never changes a verdict.

## 4. Deterministic procurement selection

Ordering (no human choice, no seed): `key = sha256("muru-ce-interface-adjudication-design-b|5a99c75f...b4bd|<stratum>|<parent_key>")`, hex, ascending within stratum. The complete ordered queues are committed in this freeze: `procurement/ordered_queues.csv` (L 19,046, N 3,454, H 4,246 candidates).

Walk (`35_procurement_walk.py`): strata in the fixed priority N, then H, then L. Within a stratum, candidates are taken strictly in rank order until 66 are accepted. A candidate may be passed over only for:

| Code | Reason |
|---|---|
| NO_SUPPLY | no current MCE, TargetMol or Selleck listing can supply it |
| PURITY_LT_95 | vendor cannot provide purity of at least 95% |
| IDENTITY_MISMATCH | supplied material does not match the frozen structure or identity |
| INSUFFICIENT_QUANTITY | less than 1 mg can be supplied (enough for the acquisition plus one re-injection) **[fixed here]** |
| SCAFFOLD_ALREADY_ACCEPTED | its scaffold group was already accepted, in this or a higher-priority stratum |

Verification evidence, logged append-only in `procurement/verification_log.csv` **[fixed here]**: a candidate PASSES only with a vendor's written confirmation of supply and purity at least 95%, followed on receipt by a certificate of analysis stating purity at least 95% and an identity consistent with the frozen structure and catalogue ID. List-price and quote-only products are equally eligible. A vendor that does not answer within 15 business days of a logged request and one reminder counts as NO_SUPPLY. Requests may be sent ahead of the frontier in queue order, but acceptance is decided only by the walk: a candidate with no logged decision stops the walk for its stratum and every lower-priority stratum.

**Cost is not an input.** Price, familiarity, solubility or chemical preference can never skip a candidate; the log format has no field that could. If the accepted population cannot be funded, the study halts; it never skips an expensive compound.

On completion the walk writes `procurement/procurement_manifest.csv` (structure, key, scaffold, vendor, catalogue ID, purity, pack, quantity, lot, rank), asserts exactly 66/66/66 and zero scaffold duplicates, re-applies every original exclusion rule including the tautomer route, and records the manifest sha256. The manifest is committed and published at `refs/muru-procurement/muru-ce-interface-adjudication-design-b` before any study injection.

## 5. Acquisition (parameters that affect the endpoint)

- One Orbitrap instrument, HCD, positive ESI, centroid MS2, one resolution setting for every MS2 scan in the study (the instrument's 15,000 at m/z 200 setting, or the nearest available) **[fixed here]**.
- One compound per injection; short reversed-phase LC, about 10 min injection to injection.
- Each cycle: one MS1 scan, then five targeted single-energy (non-stepped) HCD MS2 scans of the theoretical [M+H]+ at NCE 15, 30, 45, 60, 75; isolation width 1.0 m/z; MS2 first mass m/z 50 (or the instrument minimum if higher), last mass at least theoretical [M+H]+ + 10 **[fixed here]**.
- Injection order: ascending `sha256("muru-ce-interface-adjudication-design-b|injection|<parent_key>")` over the 198 **[fixed here]**. A blank every 10 injections and a QC standard every 20.
- Re-injection: once, with the gradient length doubled **[fixed here]**, only for a compound whose primary injection fails step 40.
- Reproducibility set: per stratum, the 9 accepted compounds with the smallest `sha256("...|repro|<parent_key>")` (27 in total), re-injected on a separate day. Descriptive QC only; never pooled into the primary.
- Before the first study injection, the vendor instrument method file(s) implementing exactly these settings are committed with their sha256. That commit may state instrument settings only and may not change anything in this document.

## 6. Observed-spectrum extraction (`40_extract_spectra.py`, frozen)

Per injection: MS1 XIC of the theoretical [M+H]+ at 5 ppm; peak window = the contiguous MS1 scans around the apex with XIC at least 50% of apex. A qualifying MS2 scan has the cell's NCE, isolation target within 0.01 m/z, a preceding MS1 scan inside the window, and precursor purity at least 0.80 in that MS1 scan (XIC over total intensity within 0.5 m/z). A cell passes with at least 3 qualifying scans; its spectrum is the unmodified concatenation of their centroid peaks. An injection passes when all 5 cells pass. Primary failure leads to one re-injection; if that passes, all 5 cells come from it; otherwise ACQUISITION_FAILURE. Cells are never mixed across injections. The observed spectra and acquisition outcomes are committed and published at `refs/muru-spectra/muru-ce-interface-adjudication-design-b`.

## 7. Predictions and scoring

**No prediction may be generated until acquisition is complete and the observed spectra are frozen** (step 45 refuses without the spectra ref). Predictions: the Design A harness (`30_run_predictions.py`, sha256 `461b18fb...0680`) unchanged, re-pointed to Design B paths and the Design B NCE grid, for the ANALYSABLE compounds only, both models, K1/K2/K3. Published at `refs/muru-predictions/...` before scoring. Scoring (`50_score_spectra.py`): the Design A scorer's `score_pair` and prediction reader (sha256 `ec0100b5...4bbf`), one row per (compound, NCE, model, mapping).

## 8. Analysis (`60_analysis.py`, one look)

- Per compound: `d_i` = mean over the 5 NCE cells and 2 models of [cosine(K1) - cosine(K2)]. A compound enters only if all 20 K1/K2 cells carry a value.
- Primary estimand: `D_div = (mean d over L + mean d over H) / 2`.
- Test: stratified compound-level percentile bootstrap, B = 10,000, seed 20260919, compounds resampled with replacement within stratum, one shared set of draws. Two-sided alpha 0.05: the primary rejects when the 95% interval of D_div excludes zero.
- Identifying test, fixed sequence, only if the primary rejects: `I = D_div - D_null` (D_null = mean d over N), two-sided 95% interval from the same draws.

| Verdict | Requires |
|---|---|
| K1 (or K2) SUPPORTED AND IDENTIFIED | primary rejects; I's interval excludes zero with I's sign equal to D_div's; mean d in L and in H both share D_div's sign |
| K1 (or K2) FAVOURED, NOT IDENTIFIED | primary rejects; any identification condition fails |
| INTERFACE UNRESOLVED | primary does not reject |

The lead mapping is K1 when D_div > 0 and K2 when D_div < 0.

Descriptive only, never able to change a verdict: K3 contrasts, JS, per model, per NCE, per stratum, the q95 support sensitivity (D_div recomputed on cells where both K1 and K2 are at most 90, the training-CE q95), and the reproducibility QC (median observed-to-observed cosine).

## 9. Power, stated plainly

With 60 L + 60 H and planning SD 0.13, the design has about 90% power for a true divergent-stratum effect of 0.0385 to 0.040 composite cosine (0.92 at 0.040, 0.84 at 0.035, 0.71 at 0.030). **It is not designed to reliably resolve substantially smaller effects**; those will more often end INTERFACE UNRESOLVED. The identifying test has 0.84, 0.72 or 0.49 power at a null-stratum SD of 0.05, 0.08 or 0.13, so identification can fail even when the primary succeeds.

## 10. Gates and record chain

| Step | Gate |
|---|---|
| Procurement walk | freeze ref |
| Acquisition | procurement ref plus the committed instrument method hash |
| Extraction (40) | freeze and procurement refs; every mzML sha256 in the acquisition sheet |
| Predictions (45) | spectra ref; `MURU_CE_DESIGN_B_EXECUTE=1`; pinned harness hash; checkpoint hashes |
| Scoring (50) | freeze, procurement, spectra and predictions refs; pinned scorer and similarity hashes |
| Analysis (60) | all four refs; `MURU_CE_DESIGN_B_ONE_LOOK=1`; refuses if a result already exists |

Code: `scripts/ce_interface_adjudication/design_b/` steps 30, 35, 40, 45, 50, 60, constants and 26 synthetic unit tests; hashes in `artifacts/ce_interface_adjudication/design_b/freeze/freeze_manifest.json`. Deviations after the freeze are recorded as dated amendments and cannot alter this document.
