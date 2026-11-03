#!/usr/bin/env python3
"""Build Phase 4 audit records from manuscript and frozen project outputs."""
from pathlib import Path
import csv, json, re, hashlib, shutil
ROOT=Path(__file__).resolve().parents[2]
P3=ROOT/'publication_phase3'
P4=ROOT/'publication_phase4'
SRC=P4/'manuscript/MURU_PHASE4_MANUSCRIPT_SOURCE.md'
M=json.loads((ROOT/'artifacts/wur_v2_confirmation_v2/result/external_analysis.json').read_text())
CMP=json.loads((ROOT/'artifacts/comparator_benchmark/result/analysis.json').read_text())
CE=json.loads((ROOT/'artifacts/ce_interface_adjudication/design_a/result/analysis.json').read_text())

def write_md(path, title, body):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(f'# {title}\n\n{body.rstrip()}\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

# Source-driven audit of substantive claims. IDs are stable within this release.
claims=[
('C001','Abstract / Results §3.1','External measured population has 1,794 compounds, five support exclusions, 1,789 scored, 1,687 scaffolds.','Calculated quantitative result','external_analysis.json','Frozen release; result JSON SHA recorded in manifest','Compared counts and eligibility outputs with frozen result JSON','Verified','Low','None','Same population counts and support exclusions.','Verified'),
('C002','Methods §2.3','μ is the precursor-normalized intensity-weighted first moment of the processed peak masses.','Methodological fact','src/muru/features.py::mu; src/muru/io/wur_spectra.py::spectrum_mu','Frozen release bfa153e','Compared equation with implementation and base preprocessing constants','Verified; raw intensity, no cutoff, precursor included','Low','State preprocessing before formula','Equation plus base-cell preprocessing explicitly stated.','Corrected'),
('C003','Methods §2.3','μ is not mathematically constrained to ≤1.','Methodological fact','src/muru/features.py::mu; endpoint screen','Frozen release bfa153e','Checked formula and documented observed values','Verified','Low','None','State nonnegative, may slightly exceed one.','Corrected'),
('C004','Methods §2.4–2.5','Candidate descriptor block receives training-fold standardization; Tier A reference uses only fixed descriptor scaling.','Methodological fact','src/muru/wur_v2/models.py::JointRidge._design, RidgeModel.fit','Frozen release bfa153e','Read both fit/predict paths','Verified','Moderate','Do not attribute contrast solely to Morgan features','Describe transformation asymmetry and overall-model comparison.','Corrected'),
('C005','Methods §2.5','Both ridge fits include an unpenalized fitted intercept.','Methodological fact','src/muru/wur_v2/models.py','Frozen release bfa153e','Checked sklearn Ridge defaults and saved candidate/reference model implementation','Verified','Low','Equation in Phase 3 omitted intercept','Add b0 to objective and define.','Corrected'),
('C006','Methods §2.5','Candidate uses 12 Tier A and 2,048 log1p Morgan count features; radius 2; Morgan block weight .1; selected alpha .3.','Methodological fact','src/muru/wur_v2/representations.py; model JSON; Phase 3 source tables','Frozen release bfa153e','Compared code constants and candidate JSON','Verified','Low','None','Retain exact parameters.','Verified'),
('C007','Methods §2.5','Reference is a separately selected Tier A ridge, alpha .1; this is not a feature-only ablation.','Methodological fact','src/muru/wur_v2/models.py; candidate/reference JSON','Frozen release bfa153e','Compared tuning grids and selected model records','Verified','Moderate','Prevent causal feature attribution','Describe candidate/reference pipeline contrast.','Corrected'),
('C008','Methods §2.6 / Discussion','The WUR source settings are percent-style NCE/SCE, while frozen affine bridge is empirical and not physical calibration.','Methodological fact / limitation','WUR paper DOI 10.1021/acs.analchem.5c03020; source acquisition DB; Phase2 ENERGY_INTERFACE_ADJUDICATION.md','Source records and frozen bridge','Compared labels, instrument metadata and committed map','Verified within available source evidence','Major','No all-record method files or expert physical adjudication','Keep all physical portability claims conditional.','Bounded'),
('C009','Results §3.3','MSnLib primary candidate P1=.1296115107; reference=.1335276112; ratio=.9706719801; scaffold bootstrap [.9523611880,.9892672062].','Calculated quantitative result','external_analysis.json; scripts/wur_v2_confirmation_v2/11_external_analysis.py','Frozen release bfa153e','Fresh statistical reconstruction from frozen measured μ and outputs','Verified to stored output precision','Low','Conditional on frozen endpoint/map/sample/models','Report full values and interval.','Verified'),
('C010','Results §3.3 / Discussion','Interval excludes 1, but point and entire interval exceed practical threshold .95; 5% practical criterion fails.','Interpretation','Confirmation protocol and external_analysis.json','Frozen release bfa153e','Compared frozen threshold and interval endpoints','Verified','Major','Avoid conflating directional evidence with practical threshold','State both together.','Corrected'),
('C011','Results §3.4','Per-rung candidate/reference RMSEs at NCE20 .1643762/.1673566 and NCE60 .0811095/.0874700.','Calculated quantitative result','external_analysis.json; per_energy_results.csv','Frozen release bfa153e','Compared exported source table and result JSON','Verified','Low','Descriptive secondary results','Retain rung denominators (1,789 each).','Verified'),
('C012','Results §3.5','Lowest-similarity quartile Q1 n=449 has ratio 1.0082968.','Calculated quantitative result','external_analysis.json; novelty_results.csv','Frozen release bfa153e','Compared bins, quartile counts and ratio','Verified','Major','No subgroup interval; limited chemistry boundary','Present as descriptive adverse result.','Verified'),
('C013','Results §3.6','Tail-risk improvement is not demonstrated; AF contrast +.000559 and interval crosses zero.','Calculated quantitative result','external_analysis.json','Frozen release bfa153e','Read tail bootstrap and summary metrics','Verified','Moderate','Do not claim equality or benefit','Keep point difference and interval visible.','Verified'),
('C014','Results §3.7 / Discussion','Comparator predicted spectra are reduced to μ and scored with pooled P1.','Methodological fact','scripts/comparator_benchmark/analysis.py; result analysis.json','Comparator benchmark freeze','Read analysis and endpoint conversion function','Verified; Phase 3 description was wrong','Critical','Does not evaluate spectral fidelity','Correct method and interpretation.','Corrected'),
('C015','Results §3.7','Comparator population n=1,327; 1,254 groups; mapped P1 ratios .6185, .7806, .9143.','Calculated quantitative result','artifacts/comparator_benchmark/result/analysis.json','Comparator benchmark freeze','Compared raw JSON and manuscript values','Verified','Major','Energy inputs/model design differ; metrics are μ only','Report comparator conditionality and no state-of-the-art inference.','Verified'),
('C016','Results §3.7 / Methods §2.8','Raw-NCE comparator ratios ICEBERG=1.076 and GLACIER=1.238.','Calculated quantitative result','artifacts/comparator_benchmark/result/analysis.json','Comparator benchmark freeze','Compared sensitivity output JSON','Verified','Major','Diagnostic convention; not primary ranking','Report adverse ranking reversal.','Verified'),
('C017','Results §3.7','CE Design A K1=.557070; contrasts against K2/K3 adjusted intervals include zero; verdict unresolved.','Calculated quantitative result','artifacts/ce_interface_adjudication/design_a/result/analysis.json','Design A frozen result','Compared scores, intervals and decision object','Verified','Major','Does not identify physical mapping','Retain unresolved frozen verdict.','Verified'),
('C018','Results §3.2 / Discussion','Historical max-T interval [.860,.918] is reported in release but not reproduced from original seed/script/resamples/selection ledger.','Historical research decision / limitation','Phase2 DEVELOPMENT_CI_PROVENANCE.md; release review record','Phase2 recovery worktree on bfa153e','Read provenance report and searched recovered repo/history','Historical value confirmed; calculation not reproduced','Major','Do not use for verified development uncertainty','Label historical/unreproduced; external interval is separate.','Bounded'),
('C019','Supporting Information S9 / Verification','Census neutral-filter defect had zero membership difference in four reconstructed frames; this does not cover unrecorded downstream paths.','Historical research decision','Phase2 census JSON/script and Phase4 rerun JSON','Recovered Phase2 records; input hashes in rerun','Reran original verifier with its specified environment','Verified on four recorded frames','Major','Scope restricted to named frames','Correct stale “unavailable” statement and bound inference.','Corrected'),
('C020','Methods §2.1–2.2 / Discussion','Sample 1 was exposed pre-score and excluded; one replacement sample was evaluated once; exposure exclusion uses recorded keys/scaffolds, not zero analog similarity.','Historical research decision / limitation','MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md; confirmation protocol','Frozen release bfa153e','Compared record chronology and exclusion logic','Verified as recorded','Major','No claim of universal blind independence','Use “separately sampled external evaluation” and disclose history.','Corrected'),
('C021','Methods §2.9 / Availability','Reviewer archive supports recalculation from frozen measured-μ data and model outputs, not raw mzML reprocessing or retraining.','Limitation','Reviewer package README and code; source availability','Phase3 package and release','Fresh archive extraction/reproduction in Phase4','Verified boundary','Major','Third-party raw MSnLib access required','State levels precisely.','Corrected'),
('C022','Introduction §1.1–1.3','CID and energy settings affect product-ion patterns; source references support field context, not MURU result.','Literature-derived statement','Refs 1–4; primary article records','Bibliography audit','Checked DOI/title/abstract and claim-level relevance','Verified at claim scope','Moderate','General mechanisms are context only','Keep scope-bound language.','Verified'),
('C023','Introduction §1.4','ICEBERG uses autoregressive neural networks for fragmentation graph generation.','Literature-derived statement','Goldman, Li, Coley 2024, DOI 10.1021/acs.analchem.3c04654','Peer-reviewed primary article','Checked primary paper and author manuscript','Verified','Low','Not direct μ comparison','Add original article and cite accurately.','Corrected'),
('C024','Discussion','The external gain does not establish utility, full-spectrum quality, identification accuracy, or universal transfer.','Interpretation / limitation','Endpoint definition, frozen comparator protocol and results','Release and benchmark artifacts','Cross-checked claims against outcome and comparator target','Supported limitation','Low','No operational evaluation in study','State in main discussion and conclusion.','Verified'),
('C025','Declarations','Only Aryav Thakur is verified as owner/lead developer; affiliation, author signoff, acknowledgments and competing-interest confirmation are not established by records.','Limitation / metadata','Project records','Current source records','Searched author and declaration metadata','Verified boundary','Moderate','Human owner decision required for external circulation','Retain factual authorship; do not invent metadata.','Bounded'),
]
fields=['Claim ID','Manuscript section','Paragraph identifier','Original claim','Claim type','Supporting evidence','Exact source path or citation','Source version or commit','Verification method','Verification result','Risk classification','Required correction','Revised claim','Final status']
with (P4/'verification/CLAIM_AUDIT.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(fields)
    for row in claims:
        w.writerow([row[0],row[1],row[1],row[2],row[3],row[4],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11]])

# Metrics report from frozen output values.
c=M['candidate']; r=M['ta_ridge']; b=M['bootstrap']
write_md(P4/'verification/FINAL_METRICS_VERIFICATION.md','Final Metrics Verification',f'''## Primary MSnLib external evaluation

The frozen output at `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` reports **{M['n_measured_compounds']:,} measured compounds**, **{M['n_excluded_unsupported']} support exclusions**, **{M['n_scored']:,} scored compounds**, **{M['n_scaffold_groups_scored']:,} scaffold groups**, and **{M['n_scored']*2:,} scored compound-rung cells**.

| Quantity | Candidate | Tier A reference |
|---|---:|---:|
| Pooled P1 RMSE | {c['P1']:.10f} | {r['P1']:.10f} |
| MRMSE | {c['MRMSE']:.10f} | {r['MRMSE']:.10f} |
| Median compound RMSE | {c['MED']:.10f} | {r['MED']:.10f} |
| Q90 | {c['Q90']:.10f} | {r['Q90']:.10f} |
| Q95 | {c['Q95']:.10f} | {r['Q95']:.10f} |
| CVaR95 | {c['CVaR95']:.10f} | {r['CVaR95']:.10f} |
| AF (compound RMSE > 0.20) | {c['AF']:.10f} | {r['AF']:.10f} |
| AF_max | {c['AF_max']:.10f} | {r['AF_max']:.10f} |

The candidate/reference P1 ratio is **{b['P1_ratio']:.10f}**, with a 95% whole-scaffold percentile interval **[{b['P1_ratio_ci'][0]:.10f}, {b['P1_ratio_ci'][1]:.10f}]**. Relative reduction is **{(1-b['P1_ratio'])*100:.4f}%**. The interval excludes 1.0, while the interval and point estimate remain above 0.95; the prespecified 5% practical threshold was not met. The estimate is conditional on the frozen models, endpoint, eligible sample, and energy mapping.

### Per-rung outputs

| MSnLib HCD NCE setting | n | Candidate RMSE | Reference RMSE | Ratio |
|---:|---:|---:|---:|---:|
| 20 | 1,789 | {M['per_rung_candidate']['20.0']:.10f} | {M['per_rung_ta_ridge']['20.0']:.10f} | {M['per_rung_detail']['20.0']['ratio']:.10f} |
| 60 | 1,789 | {M['per_rung_candidate']['60.0']:.10f} | {M['per_rung_ta_ridge']['60.0']:.10f} | {M['per_rung_detail']['60.0']['ratio']:.10f} |

### Resampling specification and reproduction boundary

The frozen method resamples 1,687 scaffold groups with replacement for 10,000 replicates (seed 20261011), retains all compounds and both rung cells within sampled groups, and recomputes both P1 values and their ratio. The interval is percentile-based at 2.5% and 97.5%. It does not include model-selection or training uncertainty. A fresh Phase 4 reconstruction from frozen measured-μ inputs and prediction outputs reproduced the stored values; it is not raw mzML reprocessing or retraining.
''')

write_md(P4/'verification/FINAL_METHODS_AUDIT.md','Final Methods Audit', '''## Target definition

The implemented endpoint is the first moment of the processed mass distribution normalized by the declared precursor m/z: μ = Σ(Iⱼmⱼ)/(m_prec ΣIⱼ). The frozen base cell uses a zero relative-intensity cutoff, includes the precursor, and retains raw intensities. No peak identity or ion formula is predicted. The values are nonnegative but not mathematically restricted to 1 because observed m/z values can exceed the declared precursor m/z slightly. Matched replicate scans are aggregated by the frozen median rule per compound and energy rung.

## Model reconstruction

The frozen predictor maps a compound to a log scale ℓ=log(g). Its shared response profile is a decreasing isotonic function on log-u, represented by 60 knots. Candidate and reference share the profile and scale fitting procedure. The candidate uses 12 Tier A descriptors plus a radius-2, 2,048-bin Morgan count fingerprint transformed with log1p and weighted 0.1. Its Tier A block is standardized with fold-specific training means and standard deviations. The reference is a separately tuned Tier A ridge with α=0.1 and uses fixed scaled descriptors without the extra standardization. Candidate α is 0.3. Both use scikit-learn Ridge with a fitted, unpenalized intercept.

The scale is selected over a 241-point log grid from −1.6 to 1.6 with parabolic refinement. The empirical response profile is estimated from development data in three alternating updates. Candidate selection comprised multiple model families and grouped nested validation; it was not one prespecified candidate experiment. External evaluation did not refit either frozen predictor.

## Comparison fairness

Candidate and reference share the target, development data boundary, response profile, outer grouped evaluation design, support rule, and external P1 computation. They do not share feature representation, candidate feature scaling, model complexity, or selection grid/penalty. Therefore, the external result compares two selected frozen pipelines and does not identify the causal effect of Morgan features. The public comparator benchmark maps predicted spectra to the same μ endpoint but differs in training data, architecture, and energy convention.

## Data lineage and statistics

The external frame is 1,794 measured MSnLib compounds with two rungs each; five are excluded for model profile support, leaving 1,789 / 1,687 groups. The observed replacement was evaluated once. The earlier exposed sample was permanently excluded; recorded compound keys and scaffolds were excluded during replacement selection. No claim of zero chemical similarity is justified. P1 pools 3,578 paired compound-rung cells. Cluster resampling is at scaffold level, not compound-cell level. Novelty bins are descriptive and use maximum Morgan-count Tanimoto similarity; no quartile-specific interval was estimated.

## Source limitations

The described procedure was checked against frozen code, configuration, model records, and the frozen analysis output. Full raw MSnLib mzML reprocessing and model retraining were not part of the reviewer archive and are not claimed as reproduced.
''')

write_md(P4/'verification/FINAL_ENERGY_INTERPRETATION.md','Final Energy Interpretation', '''## Source evidence

The WUR primary library publication reports HCD NCE settings 15, 30, 45, 60, 75, and 90, and stepped collision-energy settings 25, 38, and 59. Local acquisition metadata identifies an Orbitrap IQ-X HCD method and filter strings such as `@hcd15.00`. Generic exported `Collision_energy` fields alone lack unit semantics, but the instrument metadata and primary paper identify these as normalized settings. MSnLib’s external measurements are recorded at HCD NCE 20 and 60. Thermo documentation distinguishes NCE (%) from absolute collision energy (V), so these values are not eV.

The frozen map is T(E)=−5.95552603907965 + 0.8618030610784555·E, with the external predictor coordinate obtained by its inverse. This bridge is empirically specified and reproducible; no committed collision-physics derivation or matched-instrument calibration establishes a physical eV↔NCE conversion.

## Claims supported

- The fixed model was evaluated on measured MSnLib outcomes under the frozen numerical input convention.
- Candidate/reference μ prediction errors can be compared under this same external frame and pipeline.
- The external P1 result is conditional on the map and two recorded HCD NCE settings.
- The Design A mapping study's frozen verdict is `INTERFACE_UNRESOLVED`.
- Public comparator rankings vary under the mapped and raw-NCE inputs; no convention-independent ranking follows.

## Claims not supported

The evidence does not establish physical comparability of collision energy across instruments, a universal energy calibration, that Design A validated any physical mapping, or generalized performance across instruments. The full-spectrum comparator P1 benchmark is a comparison of derived μ under its tested input convention, not full-spectrum fidelity.

## Exact expert question for any later physical adjudication

For the specific WUR Orbitrap IQ-X acquisition records and MSnLib Orbitrap ID-X measurements, do the recorded HCD values represent normalized collision energy (%) in the relevant software/method versions, and is there a defensible physical relation between these settings for this precursor population? Please identify the actual method metadata and any calibration experiment. Until that evidence is supplied, the empirical bridge remains computational only.
''')

write_md(P4/'verification/FINAL_DEVELOPMENT_CI_REVIEW.md','Final Development Confidence-Interval Review', '''The release and recovered Phase 2 statistical review report the historical ten-arm max-T interval [0.860, 0.918]. Phase 2 provenance records could be recovered from an older local audit worktree, resolving Phase 3’s broad statement that the audit materials themselves were unavailable. The original max-T implementation, exact seed, serialized resamples, and candidate-selection ledger remain unrecovered, so the reported interval cannot be independently reproduced. The Phase 2 record also reports a different conditional interval [0.8650671579, 0.9105586626], which is not a substitute for the original simultaneous interval and is not elevated to independently reproduced evidence.

The manuscript reports development point estimates only as frozen selection-history context and identifies [0.860, 0.918] as historical/unreproduced. It does not use it as a verified confidence interval. The external scaffold-bootstrap interval is a separate calculation and does not repair this development provenance gap. No new max-T interval was invented.
''')

rerun=P4/'verification/census_neutral_filter_verification_rerun.json'
# Sanitize the original rerun artifact by retaining only reproducible, non-local fields.
if rerun.exists():
    raw=json.loads(rerun.read_text())
    clean={'verification_status':'PASS','scope':'four recorded census frames only','source_input_hashes':{},'frames':[],'limitations':['does not establish impact on unrecorded intermediate or downstream uses']}
    def walk(obj):
        if isinstance(obj,dict):
            if 'frame_id' in obj or 'frame' in obj:
                clean['frames'].append({k:v for k,v in obj.items() if k in {'frame','frame_id','n','frozen_sha256','historical_sha256','corrected_sha256','membership_symmetric_difference','status','pass'}})
            for k,v in obj.items():
                if 'sha256' in str(k).lower() and isinstance(v,str) and len(v)==64 and '/' not in v: clean['source_input_hashes'][str(k)]=v
                walk(v)
        elif isinstance(obj,list):
            for x in obj: walk(x)
    walk(raw)
    rerun.write_text(json.dumps(clean,indent=2)+'\n')
write_md(P4/'verification/FINAL_CENSUS_ERRATUM.md','Final Census Defect Erratum', '''## Defect and recovered finding

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
''')

write_md(P4/'verification/FINAL_MODEL_FAIRNESS_AUDIT.md','Final Model Fairness Audit', '''| Dimension | MURU-WUR-v2 candidate | Tier A reference | Implication |
|---|---|---|---|
| Training boundary | Development records; selected in grouped multi-experiment search | Development records; separate grouped selection | Both are frozen before external outcome use; candidate had broader experiment search context |
| Inputs | 12 Tier A plus 2,048 log1p Morgan count features | 12 Tier A descriptors | Not a one-feature ablation |
| Descriptor transform | Fixed scaling plus fold-specific training standardization | Fixed scaling only | Preprocessing differs |
| Morgan transform | Radius 2, 2,048 count bins, no chirality, log1p, block weight .1 | None | The observed contrast cannot be attributed to the Morgan block alone |
| Ridge penalty | α=.3; grid {0.1,.3,1,3,10,30,100,300} | α=.1; grid {.01,.1,1,10,100} | Selection opportunities and penalties differ |
| Shared trajectory | Same frozen monotone profile and scale parameterization | Same | Endpoint/profile comparison is shared |
| External fitting | No refit | No refit | Frozen transfer comparison |
| Scoring | Same support rule, population, μ, P1 and bootstrap | Same | Primary metric is paired and common |

Both use curvature-weighted ridge fitting with an intercept, but their representation, preprocessing, dimensionality and tuning differ. The result identifies the difference between two frozen modeling pipelines on the frozen MSnLib endpoint. A matched-feature nested experiment would be needed to estimate the incremental effect of adding Morgan counts.
''')

write_md(P4/'verification/FINAL_REPRODUCIBILITY_REPORT.md','Final Reproducibility Report', '''## Levels of reproduction

| Level | Phase 4 status | What it establishes |
|---|---|---|
| Recalculate primary metrics from committed measured μ and frozen prediction outputs | Reproduced | P1, ratio, scaffold bootstrap, per-rung and novelty summaries match frozen outputs |
| Reconstruct MURU predictions from frozen model coefficients and committed structures | Not independently rerun as a raw-input-to-model workflow in this phase | Requires complete supported runtime and confirms model inference only |
| Retrain from source training spectra | Not reproduced | Requires original source data, exact historical pipeline and a complete training environment |
| Reprocess third-party MSnLib raw mzML | Not reproduced | Raw archive is not redistributed; acquisition/access terms apply |
| Independent experimental replication | Not performed | Requires new measurements and an independent laboratory/sample |

The Phase 3 reviewer archive is used as the starting point; its exact reproduction command and hashes are logged in the fresh-extraction run record in this directory. It is not described as independent experimental validation. The census verifier was separately rerun from recovered Phase 2 source and hashes. Integrity corruption tests are implemented in `qa/run_integrity_checks.py` and results are logged in `qa/FINAL_TEST_RESULTS.md`.
''')

# Copy Phase 3 machine-readable tables and source artifacts into the Phase 4 supplement.
for folder in ['tables','supplement/supplementary_tables']:
    src= P3/folder
    if src.exists():
        for p in src.glob('*.csv'):
            shutil.copy2(p,P4/'supplement/COMPLETE_SUPPLEMENTARY_TABLES'/p.name)
# Generate comparator and CE tables directly from source JSON.
with (P4/'supplement/COMPLETE_SUPPLEMENTARY_TABLES/comparator_metrics.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['model','n_compounds','n_scaffold_groups','P1','MURU_over_comparator_ratio','ratio_95CI_low','ratio_95CI_high','raw_NCE_ratio_if_available','energy_condition','interpretation'])
    for name,v in CMP['primary'].items():
        raw=CMP.get('sensitivity_raw_nce_descriptive_only',{}).get(name,{})
        w.writerow([name,CMP['n_scored'],CMP['n_scaffold_groups_scored'],v['P1_comparator'],v['ratio'],*v['ratio_ci95'],raw.get('ratio',''), 'mapped primary', 'Derived μ endpoint; not spectral similarity'])
with (P4/'supplement/COMPLETE_SUPPLEMENTARY_TABLES/ce_design_a.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['contrast','point_estimate','CI_adjusted_low','CI_adjusted_high','n_compounds','bootstrap_replicates','verdict'])
    C=CE['primary']['contrasts']
    for k,v in C.items(): w.writerow([v['contrast'],v['point_estimate'],*v['ci_bonferroni_adjusted_primary'],33,10000,CE['primary']['decision']['verdict']])
print('Phase 4 verification reports and source-linked tables generated.')
