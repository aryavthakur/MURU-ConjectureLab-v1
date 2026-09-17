# V (v_blind): blindness and scope audit

Study: MURU collision-energy interface adjudication (outcome-blind). Task V, lens = BLINDNESS and SCOPE.
Written 2026-09-15. Worktree `.claude/worktrees/muru-ce-interface-adjudication` at 5b1c502 (HEAD unchanged, nothing committed).

Status tags: VERIFIED = read in code/data or recomputed here; INFERRED = reasoned from verified facts;
UNVERIFIABLE = the material needed is not in the worktree or is itself forbidden.

## 0. What this audit did and did not open

- Did NOT open, at any point: `MURU_COMPARATOR_BENCHMARK_RESULT.md`,
  `artifacts/comparator_benchmark/{result,predictions,prediction_verification}/`, any
  `artifacts/comparator_benchmark/technical/**` file other than the explicitly authorised
  `technical/t1/checkpoint_hyperparameters.jsonl` (and that only via grep of other agents' scripts, never read here),
  `/Users/aryav/muru-comparators/runs/` (not listed, not stat-ed, not grepped), any `*_RESULT.md`, any measured-mu file.
  `artifacts/comparator_benchmark/population/t4_*_raw.json` was also left unopened; only its directory listing was seen.
- Did open: every file under `artifacts/ce_interface_adjudication/` and `scripts/ce_interface_adjudication/` needed for
  the checks below, the two MassSpecGym fetch records, `artifacts/comparator_benchmark/population/common_population.csv`
  header line only (4 columns: key, scaffold_group, mh, model_smiles), and `git status`/`git log` of this worktree and of
  the ms-pred clone.
- No model of any kind was run by this audit.

## 1. Forbidden-path access by the study's own scripts and notes: NO BREACH FOUND

VERIFIED by enumerating every `artifacts/...` and `/Users/aryav/...` path literal in all 59 committed scripts under
`scripts/ce_interface_adjudication/` (excluding `__pycache__`) and by grepping every authored artifact for the forbidden
tokens `comparator_benchmark/(result|predictions|prediction_verification)`, `muru-comparators/runs`, `*_spectra.json`,
`*_preds.hdf5`, `*.mgf`, `RESULT.md`, `measured_mu`.

- Every hit is a self-declaration of non-access, not a read:
  `scripts/ce_interface_adjudication/screen_c11_expolib_verdict.py:279-283` (a "files NOT opened" list that is written
  into `screen/c11_expolib/c11_verdict.json:184-188`), and
  `artifacts/ce_interface_adjudication/notes/p5_exclusion_linkage.md:14-15`.
- The only paths under `artifacts/comparator_benchmark/` that any script actually reads are the two the task authorises:
  - `population/common_population.csv`, read four times and always with `usecols` restricted to identity columns:
    `p5_01_build_exclusion_sets.py:215` (`key`, `scaffold_group`), `scaffold_key.py:104-105`
    (`key`, `scaffold_group`, `model_smiles`), `screen_c11_expolib_criteria.py:274-276` (`model_smiles` only),
    `screen_c01_eawag_eq_tautomer.py:88` (`model_smiles` only). The file's only other column is `mh`, a precursor mass,
    and it is never read. `population/common_population_keys.txt` is read as a plain key list
    (`p5_01_build_exclusion_sets.py:216`).
  - `technical/t1/checkpoint_hyperparameters.jsonl` (`03_classify_ce_conventions.py:12,41`,
    `screen_c11_expolib_verdict.py:133`), explicitly pre-authorised by the task.
- Other MURU artifacts read are all identity, population or freeze material, none matching the forbidden
  `measured_mu`/`result`/`analysis` path rule: `artifacts/wur_v2/data/compounds.csv`,
  `artifacts/wur_v2/external/populations.json`, `artifacts/wur_v2/external_census/msnlib_census.json`,
  `artifacts/wur_v2_confirmation_v2/{exposure_registry/*, freeze/validation_population.csv, freeze/freeze_manifest.json,
  population/sampled_scaffold_groups.txt}`, `artifacts/comparator_feasibility/{massspecgym15_identity.parquet,
  massspecgym15_identity_fetch_record.json, overlap_support_per_compound.csv}`. The last is read with
  `usecols=["key","in_msnlib_v1_0","in_msnlib_16984129","msg_folds"]` (`p5_01_build_exclusion_sets.py:249-250`), i.e.
  membership flags, not support or performance values.
- The two authorised benchmark documents are cited for interface definitions only:
  `MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md:18,219` (MURU's fixed NCE20/NCE60 Orbitrap HCD deployment, in
  `screen/c10_bafg/c10_criteria_evidence.json:34`) and `MURU_COMPARATOR_FEASIBILITY_AUDIT.md:106-107,313`
  (the MSnLib NCE ladder and MURU's claim scope, in `02_descriptive_ce_distributions.py:36` and
  `screen/c11_expolib/c11_verdict.json:64`). None of these cites an outcome.

## 2. Disclosed incidental exposure (P5): confirmed, correctly disclosed, small residue

`notes/p5_exclusion_linkage.md:17-24` discloses that one `git grep` for the literal strings "13855/12249" did not exclude
`artifacts/comparator_benchmark/technical/`, so the tool preview printed roughly the first 250 characters of one line of
six `*_spectra.json` files under `technical/t2_t3/` and `technical/t2b_seeded/`.

- VERIFIED that nothing else in the study tree carries that content: a grep for `pred_Example`, `t2_t3`, `t2b_seeded`
  and `stored_collision_energy` across both authorised directories returns only that one disclosure paragraph.
- Residue, and I am not smoothing it over: the disclosure paragraph itself reproduces four fragments read from a
  forbidden file, including the literal pairing `"collision_key": "collision 10"` for the eV primary files versus
  `"collision 20"` for the raw-NCE sensitivity file. Assessment: this is interface-level information (which arm used
  which mapping), and the task brief already states that the closed benchmark had an eV arm and a raw-NCE arm, so it
  leaks no outcome. It is nevertheless forbidden-file content now living in an authored artifact. The alternative
  (redacting it) would weaken the disclosure, so my recommendation is to keep it and flag it, not to delete it.
- VERIFIED that the smoke-test spectra concerned are example records (`pred_Example_0_NCE20`), not benchmark-population
  predictions, consistent with P5's own characterisation.

## 3. Model inference: NONE FOUND in any committed script

VERIFIED by grepping all 59 scripts for `import torch`, `load_state_dict`, `load_from_checkpoint`, `.forward(`,
`predict_smis`, `predict_gen`, `Trainer(`, `.eval()` and `ms_pred` as an import. There are zero hits of any of these as
code. Every `ms_pred` and `iceberg`/`glacier` occurrence is either a source-citation string (for example
`screen_c02_cyanometdb_s2_criteria.py:11` "constants, read not imported",
`screen_c08_reframe_criteria.py:77` citing `chem_utils.py:277-283`) or a checkpoint name used as a dictionary key in
`03_classify_ce_conventions.py`.

Corroborating VERIFIED facts:
- No model-output file exists anywhere under `artifacts/ce_interface_adjudication`: zero files with extension
  `.mgf`, `.msp`, `.mzML`, `.mzXML`, `.hdf5`, `.h5`, `.raw`, `.wiff`. The full extension census is json 250, csv 81,
  txt 56, html 13, xml 9, parquet 9, md 8, gz 8, jsonl 5, xlsx 4, zip 2, py 2, pdf 2, mzmwizard 2, mzbatch 2, ipynb 2,
  tsv 1, log 1, ini 1, headers 1, Rmd 1, R 1.
- The ms-pred clone at `/Users/aryav/muru-comparators/repos/ms-pred` is at `ed8311f` with an empty `git status` and no
  `__pycache__` newer than 2026-09-14, which confirms P1's claim that the `__pycache__` its import created was removed.
- LIMITATION, stated rather than papered over: P1's and P2's scripts were never delivered into the worktree (section 5),
  so their "no model was run" claims cannot be audited from code here. The only positive evidence for them is their own
  self-report plus the absence of any model output in the tree. `/Users/aryav/muru-comparators/runs/` is forbidden to me,
  so I did not check it for new run directories, and I cannot rule inference in or out from that side. UNVERIFIABLE.

## 4. Download scope

### 4.1 MassSpecGym parquet range reads: independently reverified, ZERO spectral bytes

I recomputed the overlap myself from `massspecgym15_metadata_columns_fetch_record.json` rather than trusting its own
summary. VERIFIED:

- 1,395 byte ranges, declared lengths all internally consistent, summing to exactly 5,500,533 bytes, equal to the
  record's `bytes_transferred`.
- 0 ranges and 0 bytes intersect the 464 `forbidden_intervals_never_read` (the per-row-group `mzs` and `intensities`
  column chunks, 125,870,293 bytes in total). Not one byte of either spectral column was transferred.
- Composition: 1 probe byte, 1,259,236 footer bytes, 4,241,296 column-chunk bytes. All 1,392 column-chunk ranges name
  exactly one requested column, 232 ranges per column for each of `identifier`, `precursor_mz`, `parent_mass`,
  `formula`, `precursor_formula`, `smiles`. No coalescing across columns, so this fetch did not repeat the earlier
  pre_buffer defect.
- The output `massspecgym15_metadata_columns.parquet` hashes to the recorded
  `40d185c7d1fbb3c0023714b5c6d1cd02f179679213162cc03c086dd40504e1f2` and contains exactly those six columns.
- The six columns read are within the task's authorised list (precursor_mz, parent_mass, formula, precursor_formula,
  smiles, plus the join key identifier).

I also reverified the earlier `artifacts/comparator_feasibility/massspecgym15_identity_fetch_record.json`, because P4
raised it as an open question. VERIFIED: its `forbidden_intervals_never_read` set is byte-identical to the new one; its
316 ranges sum to its declared 4,314,135 bytes; and 0 of those ranges overlap any `mzs`/`intensities` chunk. P4's
disclosure is therefore accurate and its concern is bounded: that fetch over-transferred non-requested NON-spectral
columns through coalescing, and never touched a spectral chunk.

### 4.2 No spectra or peak arrays were downloaded anywhere

VERIFIED by content, not by file name:

- All seven stored GNPS LibraryServlet listings carry a `peaks_json` field, and in every one of the 52,485 records the
  value is the literal string `"null"` (CMMC-LIBRARY 23,913; GNPS-LIBRARY 16,158; REFRAME-POSITIVE-LIBRARY 9,620;
  TUEBINGEN 980; LDB_POSITIVE 700; LDB_NEGATIVE 580; ELIXDB 534). Zero records carry an actual peak array.
- The two large GNPS processed-library CSVs (REFRAME 46.2 MB, CMMC-REFRAME 49.5 MB) have 26 metadata columns and no
  peak column.
- Across all MassBank code-search stores (`c01`, `c02`, `c03`, `c07`, `c10`, `d3_downloads`) there are zero
  peak-triplet lines. The only `PK$` tokens present are `PK$SPLASH` (a hash) and `PK$NUM_PEAK` (a count), which
  matches the `dropped_pk_lines` discipline recorded in 19 register entries.
- The only files matching an m/z-like nested-array pattern are the two PharmMet CSV range-read outputs, and inspection
  of the header shows the matched column is `mz`, an MS1 feature m/z list paired with `rt`, `adduct` and `mode`
  columns. These are chromatographic feature coordinates with no intensities, not a spectrum. I record this as
  borderline-but-inside-scope rather than a breach.
- Register line 52 explicitly records that `BOKU_iBAM.mgf` and `other_MSMS_datasets.zip` were never requested; line 266
  is an R markdown script, not an msp file. Those are the only two register lines whose text mentions a spectra
  extension at all.
- Both stored zips contain only figures, supplementary tables, mzmine method XML and compound tables.

### 4.3 Volume and per-file cap

VERIFIED: 366,706,348 bytes (366.7 MB) recorded across 440 register lines; 0 transfers above the ~50 MB cap; the largest
is CMMC-REFRAME-POSITIVE-LIBRARY.csv at 49,520,118 bytes. Every file above 50 MB at source (the 133 MB MassSpecGym
parquet, the 104 MB PharmMet CSV, the 28 MB and 0.96 MB supplementary zips) was range-read, not fetched whole.

### 4.4 Register completeness: ONE REAL DEVIATION

VERIFIED by reconciling the register against every file in a downloads directory (278 files):

- 274 register rows with a `stored_as` resolve to a file on disk; of the 70 rows carrying a `stored_sha256`, 69 hash
  exactly. The one mismatch, line 123 `pharmmet_db_v1_0_precursor_rows.csv`, is fully explained by the correction note
  at line 127: the attempt-1 outputs were renamed with an `attempt1_` prefix, and
  `attempt1_pharmmet_db_v1_0_precursor_rows.csv` hashes to the recorded `9a0e1e86...`. Not a discrepancy.
- Rows whose `sha256` differs from the stored file are a semantics artifact, not an error: `sha256` is defined in the
  register as "sha256 over all transferred bytes in transfer order", while `stored_as` points at a derived or
  appended-to file (for example `codesearch_ac_lines.jsonl`, which accumulates across runs).
- 18 files in downloads directories have a basename that appears nowhere in the register. Seven are locally derived
  (zip central-directory listings, `commits_used.json`, `refs_used.json`, an extracted article text) and one is the
  register itself. The remaining 10 are genuine network transfers with no register line:
  - `d3_downloads/` (8 files, 823,469 bytes): `zenodo_2653017_record.json`, `WRTMSD_wDTXSIDs_24012019.csv`,
    `WRTMSD_InChIKeys.txt`, `massbank_eu_metadata.json`, `massbank_eu_filter_browse.json` and its `.headers`, and two
    GitHub code-search snippet files. No register line carries a "D3" task tag, and no committed script references
    `d3_downloads`, so these have neither script nor register provenance.
  - `screen/c02_cyanometdb/downloads/failed_attempts/pmc_pow_stub_for_si_00{1,2}.html` (2 files, 3,633 bytes), two
    failed supplementary fetches.
  All 10 are inside the content scope (compound, instrument and CE metadata; no spectra, no peaks) and none is
  load-bearing: no authored note, script or JSON references `d3_downloads`, `WRTMSD` or `pmc_pow_stub`. The deviation
  is the record-keeping requirement ("Record every downloaded file's name, source URL, size and sha256"), not the
  content scope.

## 5. Energy mapping choices: NONE ASSERTED, so none can rest on benchmark outcomes

VERIFIED by grepping every authored file (excluding downloaded third-party documents) for decision language:
`we (recommend|adopt|choose|select|fix)`, `the (correct|right) (mapping|interface)`, `mapping should be`,
`interface should be`, `deployment mapping (is|should)`, `therefore (use|apply) the (eV|raw NCE)`,
`ADJUDICATION VERDICT`, `FINAL MAPPING`. Zero matches. No adjudication verdict document exists in the worktree; the
study is still at the evidence stage (P3, P4, P5, Q, and eleven candidate screens).

VERIFIED that the two determinations that could have been contaminated are grounded in code and data instead:
- Q's classification rule (`notes/q_counts.md` Part 1) was frozen with a sha256 self-check before counting, and its
  categories rest on construction-order code provenance (category 1), a numeric m/z-proportionality test (category 2)
  and instrument semantics (QTOF), with an explicit "Nothing from the closed comparator benchmark was opened."
- The screen verdicts justify CE semantics from record text, vendor documentation and papers. Where they mention the
  benchmark at all it is a method fact: `screen_c08_reframe_criteria.py:77` says the ms-pred Orbitrap token is "the same
  token the frozen benchmark used", which is an interface statement, not a result.

## 6. Write scope

VERIFIED: `git status --porcelain` on this worktree lists exactly one untracked path,
`scripts/ce_interface_adjudication`, and no modified tracked file. `artifacts/*` is gitignored
(`.gitignore:34`), which is why the artifact tree does not appear. HEAD is still `5b1c502`; nothing was committed or
pushed.

VERIFIED by mtime: only three files outside the two authorised directories were written since the study began, all of
them Python bytecode caches created at 21:40 by P5 importing `muru.wur_v2.identity` to cross-check its own key function:
`src/muru/__pycache__/__init__.cpython-313.pyc`, `src/muru/wur_v2/__pycache__/__init__.cpython-313.pyc`,
`src/muru/wur_v2/__pycache__/identity.cpython-313.pyc`. They are gitignored (`.gitignore:104`) and harmless, but they
are writes outside the declared output scope, and P1 removed the analogous artifact from the ms-pred clone while P5 did
not remove these.

## 7. Undelivered P1 and P2 outputs (scope and auditability gap, still open)

VERIFIED absent from the worktree as of this audit:
`notes/p1_pipeline.md`, `p1/p1_evidence.json`, `scripts/.../p1_pipeline_evidence.py`, `notes/p2_model_internals.md`,
`p2_checkpoint_ce_parameters.json`, `p2_ce_embedding_geometry.json`, `p2_msg_label_ce_boundary_check.json`,
`scripts/.../p2_read_checkpoint_ce_parameters.py`, `scripts/.../p2_ce_embedding_geometry.py`,
`scripts/.../p2_msg_label_ce_boundary_check.py`. All ten are still only in the P1/P2 session scratchpads.

This matters for this lens in three ways. First, P1's C13-C15 and P2's C1-C2 are load-bearing for Q's counts and for the
"what the checkpoints encode" question, and their evidence is not reproducible from the worktree. Second, the blindness
and no-inference claims of the two phases that actually touched the frozen checkpoint files cannot be audited from code.
Third, register lines 11-17 and 37-48 point at "session scratchpad only", so those transfers, which by the phase
summaries were GitHub and API reads rather than data, are also unverifiable here.

## 8. Summary of deviations found

1. Register incompleteness: 10 genuine network transfers (8 in `d3_downloads/`, 2 failed PMC fetches in
   `screen/c02_cyanometdb/downloads/failed_attempts/`) have no `downloads_register.jsonl` line. In scope by content,
   non-load-bearing, but the task's recording rule was not met for them. The `d3_downloads/` set additionally has no
   producing script in `scripts/ce_interface_adjudication/`.
2. Three `.pyc` files written outside the two authorised output directories (`src/muru/**/__pycache__`), gitignored,
   not cleaned up.
3. P5's disclosure paragraph carries four verbatim fragments read from forbidden `*_spectra.json` files. Interface-level
   only, no outcome, correctly disclosed; flagged for the record rather than for removal.
4. Ten P1 and P2 deliverables are still undelivered, so those two phases' scope and blindness claims are unverifiable
   from the worktree.

No forbidden outcome file was opened by any committed script or authored note; no model inference was run by any
committed script; no spectral byte and no peak array was downloaded; and no energy mapping choice has been made at all,
let alone one justified by benchmark outcomes.

## 9. Dash check

VERIFIED: zero em dashes (U+2014), en dashes (U+2013), figure dashes (U+2012) or horizontal bars (U+2015) in any
authored file under `artifacts/ce_interface_adjudication/` or `scripts/ce_interface_adjudication/`. The nine files that
contain such characters are all unmodified downloaded third-party documents (a Hugging Face README, the MassBank record
format documentation in two copies, four Europe PMC full-text XMLs, and a PMC article HTML with its text extraction).
This note also contains none.
