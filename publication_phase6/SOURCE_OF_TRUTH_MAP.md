# Phase 6 source-of-truth map

This map identifies the active authority for each scientific or editorial object. Frozen source artifacts remain unchanged; Phase 6 produces verification records and narrowly scoped energy-language corrections.

| Object | Authoritative source | Integrity/version | Phase 6 use |
|---|---|---|---|
| Frozen release | Git tag/branch `release/muru-v2-publication-2026-09-19` | `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61` | Historical protocol and model provenance; not modified. |
| Frozen external design and source ZIP hashes | `src/muru/wur_v2/msnlib_design.py` at Phase 5 head | Phase 5 `c945b1e90f017beebd7c58386bbbdb6b6a65e38e` | Nine source family identities and frozen hash expectations. |
| Selected scan membership | `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv` | Tracked frozen artifact at Phase 5 head | Records selected source ZIP, mzML member, spectrum, rung, and precursor m/z. |
| External measured endpoint | `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` | Hash recorded in Phase 5 statistical report | Frozen external measured μ values. |
| Model identities and weights | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json`; `V2_REF_TA_RIDGE.json` | Hashes in verification report | Frozen candidate/reference definitions; redistribution rights remain unresolved. |
| Primary metrics and bootstrap | Phase 4/5 frozen outputs and reviewer verifier | Reproduced in fresh extraction in Phase 6; see `verification/FINAL_REPRODUCIBILITY_RESULTS.md` | Statistical reconstruction only. |
| Nine-source archive metadata | Zenodo record v5, `metadata/zenodo_record_15683784.json` | DOI `10.5281/zenodo.15683784` | Public repository metadata; not native acquisition methods. |
| Converted scan metadata | `metadata/RAW_METADATA_EXTRACTION.py` plus generated `metadata/INSTRUMENT_PARAMETERS.csv` and `SOURCE_TO_EVALUATION_LINEAGE.csv` | Frozen member SHA/CRC and scan allowlist checks reported in extraction validation | Converted mzML annotations; not physical calibration. |
| Energy terminology | Primary MSnLib article, PSI-MS controlled vocabulary, Thermo ID-X documentation, evaluated mzML fields, public RAW archive central directories and 161 `.meth` summaries | `energy/FINAL_COLLISION_ENERGY_ADJUDICATION.md`; `metadata/METHOD_FILE_AUDIT.md`; `metadata/NESTED_NIH_ARCHIVE_AUDIT.csv` | Converted-file eV annotation established; native ID-X method and physical transfer remain unresolved. |
| Census defect | `verification/FINAL_CENSUS_ERRATUM.md` and recovered Phase 5 hashed-frame evidence | Scope limited to four recorded frames | A zero membership-change result for tested frames; not a universal downstream proof. |
| Development max-T interval | `verification/FINAL_MAXT_PROVENANCE.md` | Historical reported [0.860, 0.918], source calculation not recovered | Remains unreproduced; not presented as independently verified. |
| Current manuscript | `manuscript/MURU_PHASE6_MANUSCRIPT_SOURCE.md` | Phase 5 canonical source with evidence-driven Phase 6 energy clarifications | Current Phase 6 internal draft; Phase 5 remains historical. |
| Supporting Information | `manuscript/MURU_PHASE6_SUPPORTING_INFORMATION_SOURCE.md` | Rendered with Phase 6 manuscript pipeline | Current supplemental text. |
| Figures and data | `figures/generate_phase6_figures.py`, `supplement/tables/` | Five regenerated figures from Phase 5 frozen result tables | No primary numerical changes; Figure 3 energy annotation clarified. |
| Rights/distribution decision | `rights/EXACT_FILE_RIGHTS_MATRIX.csv` and associated rights reports | File-level Phase 6 assessment | External sharing not cleared where project ownership or derivatives require owner/rightsholder confirmation. |

The scientific numbers are fixed to the frozen comparison and are not re-estimated by Phase 6. The all-scan metadata validation passed. The RAW-positive `.meth` files are LC separation methods, and the nested NIH archive listing contains only mzML members; neither resolves native ID-X energy settings.
