import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from muru.discovery import grammar, protocol
A='artifacts/wur_stage2a/A_POOLED_ALIGNED'; O='artifacts/wur_stage2b'
cov=pd.read_csv(f'{A}/covariates.csv').set_index('group_key')
F=json.load(open(f'{O}/folds.json'))
S=json.load(open(f'{O}/ledger/S2A_FROZEN_PIPELINE.json'))
print('== S2A representative: held-out compounds falling back to g=1 (pred<=0 or invalid)')
tot=0; n=0
for f in S['folds']:
    asg=pd.Series(F['repeats'][f['repeat']]['assignment']); held=sorted(asg.index[asg==f['fold']])
    X=np.column_stack([cov.loc[held,c].to_numpy(float)/protocol.SCALE[c] for c in protocol.FEATURES])
    expr=grammar.parse(f['diagnostics']['expr'], list(protocol.FEATURES))
    pred,ok=grammar.evaluate(expr,list(protocol.FEATURES),X)
    bad=~(ok & np.isfinite(pred) & (pred>0))
    lg=np.log(np.where(bad,1.0,pred))
    print(f"r{f['repeat']}f{f['fold']} n={len(held)} fallback={bad.sum():3d} ({bad.mean()*100:4.1f}%)  pred log g range [{lg.min():+.2f},{lg.max():+.2f}] P1={f['P1']:.4f}")
    tot+=bad.sum(); n+=len(held)
print('total fallback', tot, 'of', n, f'{tot/n*100:.1f}%')

print('\n== winner\'s curse: repeat-0 fold means of exploratory arms vs registered candidates')
t9=pd.read_csv('docs/wur_stage2b_failure_analysis/t9_direct_tilt_folds.csv'); t10=pd.read_csv('docs/wur_stage2b_failure_analysis/t10_asymptote_folds.csv'); t4=pd.read_csv('docs/wur_stage2b_failure_analysis/t4_cv_r2.csv')
rows=[]
for nm,df in [('t9',t9),('t10',t10)]:
    d=df[(df.rep==0)&(~df.arm.str.startswith('_'))].groupby('arm').P1.mean()
    for a,v in d.items(): rows.append((nm+':'+a, v))
    d15=df[~df.arm.str.startswith('_')].groupby('arm').P1.mean()
for a,v in t4[~t4.model.str.startswith('_')].groupby('model').mu_rmse.mean().items(): rows.append(('t4:'+a, v))
for cid in ['LIN_RIDGE_TIERA','V1A_STABLE_LAW','V1C_RICH_RIDGE_24','V1D_RICH_HGB_24','V2A_TWOPARAM_RIDGE','S2A_FROZEN_PIPELINE','B1_MASS_ONLY_ISOTONIC']:
    L=json.load(open(f'{O}/ledger/{cid}.json')); rows.append(('ledger:'+cid, np.mean([f['P1'] for f in L['folds'] if f['repeat']==0])))
for a,v in sorted(rows,key=lambda t:t[1]): print(f'{v:.4f}  {a}')
print('\n15-fold means t9/t10:'); print(t9[~t9.arm.str.startswith('_')].groupby('arm').P1.mean().round(4).to_dict()); print(t10[~t10.arm.str.startswith('_')].groupby('arm').P1.mean().round(4).to_dict())

print('\n== Tier A2 collinearity with Tier A (in-sample R2 of each A2 column on the 12 Tier A columns, OLS)')
a2=pd.read_csv(f'{O}/descriptors_a2.csv').set_index('group_key').loc[cov.index]
XA=np.column_stack([cov[c].to_numpy(float)/protocol.SCALE[c] for c in protocol.FEATURES]); XA1=np.column_stack([np.ones(len(XA)),XA])
from muru.wur_stage2.descriptors2 import TIER_A2
for c in TIER_A2:
    y=a2[c].to_numpy(float); b,*_=np.linalg.lstsq(XA1,y,rcond=None); r2=1-((y-XA1@b)**2).sum()/((y-y.mean())**2).sum()
    print(f'{c:22s} R2_on_TierA={r2:.3f}  sd={y.std():.3f} frac_zero={(y==0).mean():.2f}')
