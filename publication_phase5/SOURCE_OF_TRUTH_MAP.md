# Source of truth map

This map identifies the authoritative inputs for the Phase 5 release candidate. Historical releases remain immutable; Phase 5 files are copies or derived reports and do not replace the frozen experiment records.

| Question | Authority | Verification boundary |
|---|---|---|
| Frozen study base | `release/muru-v2-publication-2026-09-19` at `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61` | Frozen scientific release; never rewritten by publication work. |
| Development protocol and candidate freeze | `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md`; `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`; `artifacts/wur_v2/candidate/` | Includes post-results A-3 amendment; development max-T interval remains unreproduced. |
| External protocol, sample history, and population | `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`; `MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md`; `artifacts/wur_v2_confirmation_v2/freeze/` | Fixed numeric 20/60 rungs; replacement sample analyzed once and now exposed. |
| External measured values and frozen outputs | `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`; `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` | Source for MSnLib counts, primary metrics, subgroup metrics, bootstrap, and verdict. |
| Metric and bootstrap implementation | `src/muru/wur_v2/metrics.py`; `scripts/wur_v2_confirmation_v2/11_external_analysis.py` | Primary P1 pools compound-rung cells; whole-scaffold bootstrap resamples groups. |
| Collision-energy parsing and transformation | `src/muru/energy.py`; `src/muru/wur_bridge.py`; `src/muru/wur_v2/external_msnlib.py::adapter_energy`; external protocol §§2, 7 | WUR field is numeric/unitless in export; MSnLib protocol says NCE while primary paper says eV. Native method files for nine evaluated archives were not found. A0 anchor agreement gate failed. |
| Comparator benchmark | `MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md`; `artifacts/comparator_benchmark/result/analysis.json`; comparator code | Common derived μ endpoint; comparator rankings are conditional on model-specific energy inputs. |
| CE Design A | `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_PREREGISTRATION.md`; `artifacts/ce_interface_adjudication/design_a/result/analysis.json` | Separate 33-compound adjudication; frozen status `INTERFACE_UNRESOLVED`. |
| Census defect | Recovered Phase 2 verifier and inputs documented in `verification/FINAL_CENSUS_ERRATUM.md`; Phase 4 rerun JSON | Zero membership difference only across four reconstructed frames and hashes; not proof about every downstream operation. |
| Current manuscript source | `manuscript/MURU_PHASE5_MANUSCRIPT_SOURCE.md` | Canonical prose for the package. Phase 4 files remain historical. |
| Supporting Information source | `supplement/MURU_PHASE5_SUPPORTING_INFORMATION_SOURCE.md` | Canonical supplement prose; source tables copied into `supplement/tables/`. |
| Figure data | `supplement/tables/` and `figures/FIGURE_n/generate.py` | Figures regenerated from the bundled CSV tables; figures are not manually redrawn. |
| Bibliography and audit | `literature/FINAL_REFERENCES.bib`, `FINAL_REFERENCES.csv`, `FINAL_CITATION_AUDIT.csv` | 27 numbered references; most recent source inspection statuses carried forward from Phase 4; instrument-manual metadata remains partially verified. |
| Reproduction archive | Phase 4 reviewer archive nested frozen-output package, documented in `verification/FINAL_REPRODUCIBILITY_REPORT.md` | Reconstructs frozen-output statistics and figures; not raw-data-to-model reproduction. |
| Data rights | `release/FINAL_DATA_RIGHTS_REPORT.md` | Provisional. The exact redistributability of compound-level derived outcomes and WUR-derived model artifacts still needs owner/rights review. |

A title-level “independent validation” claim is not used. The frozen study category “MODEST EXTERNAL CONFIRMATION” is reported as the recorded classification, alongside the sampling history and current exposure boundary.
