# Simulated Reviewer C: Computational Reproducibility and Research Integrity

**Review type:** Adversarial, simulated review; not a human peer review or external expert opinion.  
**Materials examined:** Phase 4 canonical source as available on 2 November 2026; Phase 3 reviewer archive and README; frozen analysis script, inputs, output JSON, model records, manifest; reproduced extraction; source hashes; Phase 4 reproducibility and availability passages.

## Overall assessment

The frozen-output statistical reconstruction is substantially more reproducible than the manuscript’s earlier narrative implied. I extracted the Phase 3 reviewer archive into a new temporary directory and ran its verifier under the exact Python 3.13.12 environment specified in its README. The package passed its checksum and required-file checks and reproduced all primary counts, P1 values, ratio, interval, and frozen decision to the verifier’s specified tolerance. Deliberate input corruption and file removal were both detected.

This is a useful and specific reproducibility result. It does not reproduce the original raw mzML processing, model training, development search, or independent experimental measurement. Those boundaries are stated in the package README and mostly reflected in the revised Methods. The paper is not yet reproducibility-final because one Discussion paragraph still contains a stale Phase 3 provenance claim, and the Phase 4 source’s figure links still point to Phase 3 output paths rather than the regenerated Phase 4 figure directories.

## Reproduction attempt

### Archive integrity and extraction

Commands executed:

```bash
unzip -t publication_phase3/release/MURU_PHASE3_REVIEWER_PACKAGE.zip
mkdir -p /tmp/muru_phase4_reviewc/extracted
unzip -q publication_phase3/release/MURU_PHASE3_REVIEWER_PACKAGE.zip -d /tmp/muru_phase4_reviewc/extracted
cd /tmp/muru_phase4_reviewc/extracted/reviewer_package
python3.13 verify_reproduction.py
```

`unzip -t` reported no archive errors. The extracted archive contained the verifier, frozen analysis script and its source tree, measured-μ table, validation population, model records, expected output, README, and checksum list. The archive SHA-256 at review time was `4a68ff73a98933ff9e827831812006d8a2ce3ae1d55674523013a5ba8a1e857a`.

The verifier passed and returned:

```text
n_measured_compounds: 1794
n_excluded_unsupported: 5
n_scored: 1789
n_scaffold_groups_scored: 1687
candidate_P1: 0.12961151072591617
reference_P1: 0.13352761116871245
ratio: 0.9706719800607511
ci: [0.9523611879747089, 0.9892672061846276]
decision: MODEST EXTERNAL CONFIRMATION
```

The installed Python 3.11 environment did not satisfy the archive dependencies (`scikit-learn` and RDKit were absent; other versions also differed). Running the documented Python 3.13.12 environment succeeded with NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, scikit-learn 1.9.0, and RDKit 2026.03.5. No package files were altered during the successful run.

### Integrity-failure controls

I made disposable copies of the fresh extraction and ran two fault injections:

- Appending text to `README.md` caused exit code 1 and `CHECKSUM MISMATCH: README.md`.
- Removing `expected_primary.json` caused exit code 1 and `MISSING: expected_primary.json`.

These checks show that the verifier catches an altered manifest-covered file and a missing expected-result file. The verifier’s manifest does not checksum itself; the enclosing ZIP hash must be kept in the release manifest.

## Major concerns

### 1. Stale Phase 2 availability statement remains in the Discussion

**Location:** Phase 4 manuscript source, Discussion paragraph currently beginning “The development simultaneous max-T interval [0.860, 0.918] remains a historical claim…” (approximately §4, paragraph 7).

**Concern:** This paragraph says the Phase 2 audit directory and commit were absent and that the calculation source was not found for that reason. The Phase 2 reports, evidence JSON, census verifier, and reviewer package have since been recovered in an older worktree. The original recorded commit object remains unavailable, and the max-T computation itself remains unreproduced, but these are narrower facts. The paragraph conflicts with the Phase 4 Methods, the revised census erratum, and the recovered provenance report.

**Evidence:** Recovered `publication_phase2/DEVELOPMENT_CI_PROVENANCE.md` and `ENERGY_INTERFACE_ADJUDICATION.md`; the census verifier and JSON; the Phase 4 `FINAL_CENSUS_ERRATUM.md` and `FINAL_DEVELOPMENT_CI_REVIEW.md`.

**Required correction:** State that the Phase 2 audit reports and census artifacts were recovered, while the cited Phase 2 audit commit object was not recovered; the max-T source implementation, seed, serialized resamples, and selection ledger remain missing. Keep the interval historical and unreproduced. This correction is material because it avoids confusing an absent original calculation with absent audit records.

### 2. Phase 4 manuscript figure paths are not yet self-contained

**Location:** Figure references in the Phase 4 canonical source, e.g. Figure 1 path `../figures/figure_1_study_design.png` and corresponding paths for Figures 2–5.

**Concern:** The regenerated assets are stored under `publication_phase4/figures/FIGURE_1/figure_1.png` through `FIGURE_5/figure_5.png`. The current Markdown points to the Phase 3 `publication_phase3/figures/` filenames, not the required Phase 4 figure outputs. A renderer that resolves relative paths from the Phase 4 manuscript directory will not find the Phase 3 figures at that path, and a reviewer extracting the Phase 4 package independently may receive missing images.

**Evidence:** Current Phase 4 source paths and generated folder layout. The Phase 3 reviewer archive itself does not contain Phase 4 figures or their scripts.

**Required correction:** Update source image paths to the Phase 4 locations or make the renderer’s explicit mapping deterministic and package-contained. Run the renderer from a clean extraction and fail on missing image references rather than silently omitting them.

### 3. Environment is specified by version list but not yet locked

**Location:** Methods §2.9 and reviewer package README.

**Concern:** The README gives exact package versions and the verifier rejects mismatches, which is helpful, but there is no `requirements.txt`, lock file, or fully recorded platform/build manifest in the extracted reviewer archive. A scientist must resolve and install those versions independently; RDKit and numerical package availability may vary by platform. The verifier demonstrates the intended versions in this environment, not necessarily a portable install recipe.

**Evidence:** Fresh extracted archive file list and README; verifier’s hard-coded version dictionary.

**Required correction:** Include a pinned environment specification (for example, conda environment YAML or platform-specific lock) or document a tested installation recipe and platform. Record OS/architecture and Python build. The phase4 package should include its own figure/table generation dependencies and inputs rather than relying on paths outside the archive.

## Minor concerns

### 4. Archive reproduces a statistical analysis, not the full scientific workflow

**Location:** README, Methods §2.9, Results §3.8, Data/Code Availability.

The package accurately disclaims raw mzML parsing and training. For clarity, retain a four-level terminology distinction: (i) metric reconstruction from frozen measured-μ values and predictions (achieved); (ii) prediction regeneration from frozen coefficients and structures (not attempted by this clean-extraction check); (iii) training reconstruction (not achieved); and (iv) raw mzML reprocessing and external experimental replication (not achieved). The README currently clearly describes (i) versus raw reprocessing/training, but does not separately describe inference regeneration.

### 5. Phase 4 verification outputs need final-source hashes and commands

**Location:** Phase 4 `FINAL_REPRODUCIBILITY_REPORT.md`.

The report correctly distinguishes reproducibility levels, but at review time it refers prospectively to “the fresh-extraction run record in this directory” and `qa/run_integrity_checks.py`; those run records/scripts were not present yet. Before release, replace these forward references with exact command, output log, input hashes, and exit status. Do not claim verification based on an intended command.

### 6. Inference-time candidate reconstruction should be exercised or described as untested

The packaged verifier reruns `11_external_analysis.py` using frozen model JSON and measured-μ/prediction inputs; it does not demonstrate that reconstructing predictions from structures, feature code, and frozen coefficients reproduces the archived predictions. This is not necessary for the stated statistical reconstruction, but the manuscript should avoid saying the model itself was reconstructed from the reviewer archive unless that separate step is tested.

## Assessment of data integrity and rights

The reviewer package excludes the third-party raw MSnLib mzML archive and gives an acquisition route/checksum instruction, which is appropriate. It includes project code, derived measured-μ data, model records, structures, and analysis outputs. The current archive docs correctly distinguish the source data from project-derived artifacts. The final Phase 4 package should retain the rights statement and must not claim raw-data-to-model reproducibility. The frozen package checksum and internal SHA-256 manifest serve different purposes and should both be reported.

## Unresolved issues that cannot be fixed by documentation alone

- The original max-T development interval cannot be reproduced without the original calculation implementation, seed, selected input snapshot, serialized resamples, and selection ledger.
- Raw MSnLib mzML processing cannot be reproduced from this archive alone; third-party acquisition/access terms and the raw source archive are needed.
- No training-level reconstruction or independent experiment was carried out in this review.
- The release’s historical model-search decision cannot be independently re-audited from the aggregate result archive alone; the selected candidate’s external statistical comparison is reproducible.

## Recommendation

**Major revision before calling Phase 4 reproducibility-complete.** The primary external statistical result is reproducible from a fresh extraction with the stated exact environment, and integrity checks behave correctly. Correct the stale Phase 2 Discussion statement, ensure the Phase 4 figures resolve within the package, and include final run logs and a lockable environment specification. The strongest supportable claim is: *independent recalculation of the frozen external metrics from the committed measured-μ table and frozen prediction/model artifacts reproduced the primary statistics.* This is not a claim of raw-data-to-model reproduction, retraining, or independent experimental replication.
