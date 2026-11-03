#!/usr/bin/env python3
"""Export Phase 4 CSV tables from frozen Phase 3 results and repository artifacts.

Run from any directory within a complete MURU-ConjectureLab checkout:
    python3.13 publication_phase4/scripts/build_source_tables.py
"""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'publication_phase4/supplement/COMPLETE_SUPPLEMENTARY_TABLES'
RES=json.loads((ROOT/'artifacts/wur_v2_confirmation_v2/result/external_analysis.json').read_text())
CMP=json.loads((ROOT/'artifacts/comparator_benchmark/result/analysis.json').read_text())
CE=json.loads((ROOT/'artifacts/ce_interface_adjudication/design_a/result/analysis.json').read_text())
DEV=json.loads((ROOT/'artifacts/wur_v2_confirmation/repro_check_p1.json').read_text())
OUT.mkdir(parents=True,exist_ok=True)
c,r,b=RES['candidate'],RES['ta_ridge'],RES['bootstrap']
primary=[
 ('Population compounds',RES['n_measured_compounds'],'count'),('Measured compounds',RES['n_measured_compounds'],'count'),('Unsupported exclusions',RES['n_excluded_unsupported'],'count'),('Scored compounds',RES['n_scored'],'count'),('Scaffold groups',RES['n_scaffold_groups_scored'],'count'),('Candidate P1',c['P1'],'pooled two-rung RMSE'),('Reference P1',r['P1'],'pooled two-rung RMSE'),('P1 ratio',b['P1_ratio'],'candidate/reference'),('P1 ratio 95% CI lower',b['P1_ratio_ci'][0],'scaffold bootstrap'),('P1 ratio 95% CI upper',b['P1_ratio_ci'][1],'scaffold bootstrap'),('Relative P1 reduction',1-b['P1_ratio'],'1 - ratio'),('AF candidate',c['AF'],'fraction RMSE > 0.20'),('AF reference',r['AF'],'fraction RMSE > 0.20'),('CVaR95 candidate',c['CVaR95'],'mean worst 5% compound RMSE'),('CVaR95 reference',r['CVaR95'],'mean worst 5% compound RMSE')]
pd.DataFrame(primary,columns=['metric','value','definition']).to_csv(OUT/'primary_results.csv',index=False)
pd.DataFrame([{'energy':k,'n':RES['n_scored'],'candidate_rmse':RES['per_rung_candidate'][k],'reference_rmse':RES['per_rung_ta_ridge'][k],'source':'external_analysis.json'} for k in ['20.0','60.0']]).to_csv(OUT/'per_energy_results.csv',index=False)
pd.DataFrame([{'metric':k,'candidate':c[k],'reference':r[k]} for k in ['P1','MRMSE','MED','Q90','Q95','CVaR95','AF','AF_max']]).to_csv(OUT/'error_summary.csv',index=False)
for name in ['external_compound_errors.csv','novelty_results.csv']:
    pd.read_csv(ROOT/'publication_phase3/tables'/name).to_csv(OUT/name,index=False)
pd.DataFrame([{'metric':'P1_candidate','value':c['P1'],'source':'external_analysis.json'},{'metric':'P1_reference','value':r['P1'],'source':'external_analysis.json'},{'metric':'ratio','value':b['P1_ratio'],'source':'external_analysis.json'},{'metric':'ratio_ci_low','value':b['P1_ratio_ci'][0],'source':'external_analysis.json'},{'metric':'ratio_ci_high','value':b['P1_ratio_ci'][1],'source':'external_analysis.json'},{'metric':'n_measured','value':RES['n_measured_compounds'],'source':'external_analysis.json'},{'metric':'n_excluded','value':RES['n_excluded_unsupported'],'source':'external_analysis.json'},{'metric':'n_scored','value':RES['n_scored'],'source':'external_analysis.json'},{'metric':'n_scaffolds','value':RES['n_scaffold_groups_scored'],'source':'external_analysis.json'},{'metric':'development_ratio','value':DEV['PRIMARY']['ratio'],'source':'artifacts/wur_v2_confirmation/repro_check_p1.json; point estimate only; max-T interval unreproduced'}]).to_csv(OUT/'figure_2_data.csv',index=False)
pd.read_csv(OUT/'per_energy_results.csv').rename(columns={'energy':'energy','candidate_rmse':'candidate_rmse','reference_rmse':'reference_rmse'}).to_csv(OUT/'figure_3_per_rung.csv',index=False)
pd.DataFrame([{'metric':'AF_diff','value':b['AF_diff'],'low':b['AF_diff_ci'][0],'high':b['AF_diff_ci'][1],'source':'external_analysis.json'}]).to_csv(OUT/'figure_3_tail_data.csv',index=False)
pd.read_csv(OUT/'novelty_results.csv').to_csv(OUT/'figure_4_data.csv',index=False)
comp=[]
for name,v in CMP['primary'].items():
    raw=CMP.get('sensitivity_raw_nce_descriptive_only',{}).get(name,{})
    comp.append({'model':name,'n_compounds':CMP['n_scored'],'n_scaffold_groups':CMP['n_scaffold_groups_scored'],'P1':v['P1_comparator'],'MURU_over_comparator_ratio':v['ratio'],'ratio_95CI_low':v['ratio_ci95'][0],'ratio_95CI_high':v['ratio_ci95'][1],'raw_NCE_ratio_if_available':raw.get('ratio'),'energy_condition':'model-specific primary','interpretation':'Derived μ endpoint; conditional on model-specific CE input'})
pd.DataFrame(comp).to_csv(OUT/'comparator_metrics.csv',index=False)
pd.DataFrame([{'contrast':x['contrast'],'point_estimate':x['point_estimate'],'CI_adjusted_low':x['ci_bonferroni_adjusted_primary'][0],'CI_adjusted_high':x['ci_bonferroni_adjusted_primary'][1],'n_compounds':33,'bootstrap_replicates':x['n_boot'],'verdict':'INTERFACE_UNRESOLVED'} for x in CE['primary']['contrasts'].values()]).to_csv(OUT/'ce_design_a.csv',index=False)
pd.DataFrame([{'model':name,'P1_MURU':v['P1_MURU'],'P1_comparator':v['P1_comparator'],'ratio':v['ratio'],'ratio_ci95_low':v['ratio_ci95'][0],'ratio_ci95_high':v['ratio_ci95'][1],'raw_nce_ratio':CMP.get('sensitivity_raw_nce_descriptive_only',{}).get(name,{}).get('ratio'),'source':'comparator_benchmark/result/analysis.json'} for name,v in CMP['primary'].items()]).to_csv(OUT/'figure_5_comparator_data.csv',index=False)
pd.DataFrame([{'contrast':x['contrast'],'estimate':x['point_estimate'],'low':x['ci_bonferroni_adjusted_primary'][0],'high':x['ci_bonferroni_adjusted_primary'][1],'source':'ce_interface_adjudication/design_a/result/analysis.json'} for x in CE['primary']['contrasts'].values()]).to_csv(OUT/'figure_5_design_a_data.csv',index=False)
print(f'Wrote frozen-output tables to {OUT}')
