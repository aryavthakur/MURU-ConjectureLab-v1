#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, subprocess, sys
ROOT=Path(__file__).resolve().parent
manifest=ROOT/'SHA256SUMS.txt'
for line in manifest.read_text().splitlines():
    digest, rel=line.split('  ',1); p=ROOT/rel
    if not p.is_file(): raise SystemExit(f'MISSING: {rel}')
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=digest: raise SystemExit(f'CHECKSUM MISMATCH: {rel}')
required=['src/muru/wur_v2/candidate.py','src/muru/wur_v2/metrics.py','scripts/wur_v2_confirmation_v2/11_external_analysis.py','artifacts/wur_v2_confirmation_v2/result/measured_mu.csv','artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv','artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json','artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json']
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f'REQUIRED FILE MISSING: {rel}')
import numpy, pandas, scipy, sklearn, rdkit
versions={'numpy':'2.5.2','pandas':'3.0.5','scipy':'1.18.0','scikit-learn':'1.9.0','rdkit':'2026.03.5'}
actual={'numpy':numpy.__version__,'pandas':pandas.__version__,'scipy':scipy.__version__,'scikit-learn':sklearn.__version__,'rdkit':rdkit.__version__}
if actual!=versions: raise SystemExit(f'ENVIRONMENT MISMATCH: expected {versions}, got {actual}')
subprocess.run([sys.executable,str(ROOT/'scripts/wur_v2_confirmation_v2/11_external_analysis.py')],cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')},check=True,stdout=subprocess.DEVNULL)
actual=json.loads((ROOT/'artifacts/wur_v2_confirmation_v2/result/external_analysis.json').read_text())
expected=json.loads((ROOT/'expected_primary.json').read_text())
observed={'n_measured_compounds':actual['n_measured_compounds'],'n_excluded_unsupported':actual['n_excluded_unsupported'],'n_scored':actual['n_scored'],'n_scaffold_groups_scored':actual['n_scaffold_groups_scored'],'candidate_P1':actual['candidate']['P1'],'reference_P1':actual['ta_ridge']['P1'],'ratio':actual['bootstrap']['P1_ratio'],'ci':actual['bootstrap']['P1_ratio_ci'],'decision':actual['decision']}
for key in ['n_measured_compounds','n_excluded_unsupported','n_scored','n_scaffold_groups_scored','decision']:
    if observed[key]!=expected[key]: raise SystemExit(f'RESULT MISMATCH {key}: {observed[key]} != {expected[key]}')
for key in ['candidate_P1','reference_P1','ratio']:
    if abs(observed[key]-expected[key])>1e-12: raise SystemExit(f'RESULT MISMATCH {key}: {observed[key]} != {expected[key]}')
if any(abs(a-b)>1e-12 for a,b in zip(observed['ci'],expected['ci'])): raise SystemExit('RESULT MISMATCH ci')
print('PASS: checksums, required files, environment, frozen external result')
print(json.dumps(observed,indent=2))
