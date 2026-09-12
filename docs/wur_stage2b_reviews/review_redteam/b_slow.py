import sys, json, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from muru.discovery import protocol
from muru.discovery.estimate import fit_collapse, _phi_eval, ENERGY_SCALE
from muru.wur_stage2 import folds as FO
from muru.wur_stage2.arms_v1 import _X24, FEATURES_24
from sklearn.linear_model import Ridge
from sklearn.isotonic import IsotonicRegression
A='artifacts/wur_stage2a/A_POOLED_ALIGNED'; O='artifacts/wur_stage2b'
long=pd.read_csv(f'{A}/long_mu.csv'); cov=pd.read_csv(f'{A}/covariates.csv'); fr=pd.read_csv(f'{A}/compounds.csv').set_index('group_key')
a2=pd.read_csv(f'{O}/descriptors_a2.csv').set_index('group_key')
print('n_amine == n_N ? ', np.allclose(a2.loc[cov.group_key,'n_amine'].to_numpy(), cov['n_N'].to_numpy()), ' corr', np.corrcoef(a2.loc[cov.group_key,'n_amine'], cov['n_N'])[0,1])
F=json.load(open(f'{O}/folds.json')); E=np.array([30.,45.,60.,75.,90.]); Es=E/ENERGY_SCALE
def X12(c): return np.column_stack([c[k].to_numpy(float)/protocol.SCALE[k] for k in protocol.FEATURES])
def r2(y,p,w=None):
    w=np.ones_like(y) if w is None else w
    return 1-np.sum(w*(y-p)**2)/np.sum(w*(y-np.average(y,weights=w))**2)
def tune(X,y,w,inner,alphas):
    best=None
    for a in alphas:
        sse=0
        for k in range(FO.INNER_K):
            tr,va=inner!=k,inner==k
            m=Ridge(alpha=a).fit(X[tr],y[tr],sample_weight=w[tr]); sse+=np.sum(w[va]*(y[va]-m.predict(X[va]))**2)
        if best is None or sse<best[0]: best=(sse,a)
    return best[1]
rows=[]
t0=time.time()
for rep in F['repeats']:
    asg=pd.Series(rep['assignment'])
    for k in range(5):
        held=sorted(asg.index[asg==k]); train=sorted(asg.index[asg!=k])
        Ltr=long[long.group_key.isin(train)]
        fit=fit_collapse(Ltr, with_hmain=False)
        ctr=cov.set_index('group_key').loc[fit.compounds].reset_index(); lg=np.log(fit.g_hat); w=fit.weights
        # oracle held-out log g (for R2 scoring), using training Phi: collapse on held-out too via training profile
        Wte=long[long.group_key.isin(held)].pivot_table(index='group_key',columns='ce_numeric',values='mu').reindex(index=held,columns=E)
        Yte=Wte.to_numpy(float); cte=cov.set_index('group_key').loc[held].reset_index()
        from muru.discovery.estimate import _best_log_g, LOG_G_GRID
        lg_or=_best_log_g(E,Yte,fit.phi_u,fit.phi_v)
        src_te=fr.loc[held,'source'].to_numpy(); src_tr=ctr['source'].to_numpy() if 'source' in ctr else fr.loc[ctr.group_key,'source'].to_numpy()
        inner=FO.inner_folds(ctr,k).to_numpy()
        def P1(pred,mask=None):
            d=pred-Yte
            if mask is not None: d=d[mask]
            return float(np.sqrt(np.nanmean(d**2)))
        def mu_of(lgp): return _phi_eval(fit.phi_u,fit.phi_v,Es[None,:]/np.exp(lgp)[:,None])
        out=dict(rep=rep['repeat'],fold=k,n=len(held),nWUR=int((src_te=='WUR').sum()))
        # ridge12 / ridge24 pooled
        X12tr,X12te=X12(ctr),X12(cte); X24tr,X24te=_X24(ctr),_X24(cte)
        a12=tune(X12tr,lg,w,inner,(0.01,0.1,1,10,100)); a24=tune(X24tr,lg,w,inner,(0.1,1,3,10,30,100))
        p12=Ridge(alpha=a12).fit(X12tr,lg,sample_weight=w).predict(X12te); p24=Ridge(alpha=a24).fit(X24tr,lg,sample_weight=w).predict(X24te)
        out.update(r2_12=r2(lg_or,p12), r2_24=r2(lg_or,p24), P1_12=P1(mu_of(p12)), P1_24=P1(mu_of(p24)), P1_24_WUR=P1(mu_of(p24),src_te=='WUR'), P1_12_WUR=P1(mu_of(p12),src_te=='WUR'))
        # mass-only: log N OLS, log mz OLS, isotonic on mz
        for nm,col in [('logN','total_atom_count'),('logmz','precursor_mz')]:
            z=np.log(ctr[col].to_numpy(float)); zt=np.log(cte[col].to_numpy(float))
            Aa=np.column_stack([np.ones(len(z)),z]); b,*_=np.linalg.lstsq(Aa*np.sqrt(w)[:,None],lg*np.sqrt(w),rcond=None)
            out[f'r2_{nm}']=r2(lg_or,b[0]+b[1]*zt); out[f'slope_{nm}']=b[1]
        iso=IsotonicRegression(increasing='auto',out_of_bounds='clip').fit(ctr['precursor_mz'].to_numpy(float),lg,sample_weight=w)
        out['r2_isoMz']=r2(lg_or,iso.predict(cte['precursor_mz'].to_numpy(float)))
        # source indicator added to 24
        s_tr=(src_tr=='WUR').astype(float)[:,None]; s_te=(src_te=='WUR').astype(float)[:,None]
        p24s=Ridge(alpha=a24).fit(np.hstack([X24tr,s_tr]),lg,sample_weight=w); out['src_coef']=float(p24s.coef_[-1]); out['P1_24src']=P1(mu_of(p24s.predict(np.hstack([X24te,s_te]))))
        # WUR-only training: collapse on WUR training compounds only, ridge24, score WUR held-out
        trW=[g for g in train if fr.loc[g,'source']=='WUR']
        fitW=fit_collapse(long[long.group_key.isin(trW)], with_hmain=False)
        cW=cov.set_index('group_key').loc[fitW.compounds].reset_index(); lgW=np.log(fitW.g_hat); wW=fitW.weights
        innerW=FO.inner_folds(cW,k).to_numpy()
        XW=_X24(cW); aW=tune(XW,lgW,wW,innerW,(0.1,1,3,10,30,100))
        pW=Ridge(alpha=aW).fit(XW,lgW,sample_weight=wW).predict(X24te)
        muW=_phi_eval(fitW.phi_u,fitW.phi_v,Es[None,:]/np.exp(pW)[:,None])
        out['P1_WURonlytrain_WUR']=P1(muW,src_te=='WUR'); out['nWURtrain']=len(trW); out['alphaW']=aW
        # pooled-trained but only WUR profile? skip. Also LCSB-only training scored on WUR held-out (transfer)
        trL=[g for g in train if fr.loc[g,'source']=='LCSB']
        fitL=fit_collapse(long[long.group_key.isin(trL)], with_hmain=False)
        cL=cov.set_index('group_key').loc[fitL.compounds].reset_index(); lgL=np.log(fitL.g_hat); wL=fitL.weights
        pL=Ridge(alpha=a24).fit(_X24(cL),lgL,sample_weight=wL).predict(X24te)
        muL=_phi_eval(fitL.phi_u,fitL.phi_v,Es[None,:]/np.exp(pL)[:,None]); out['P1_LCSBonlytrain_WUR']=P1(muL,src_te=='WUR')
        # benzene-scaffold-only prediction stats: within held-out fold, R2 on benzene subset
        rows.append(out); print(json.dumps({kk:(round(v,4) if isinstance(v,float) else v) for kk,v in out.items()}), round(time.time()-t0), flush=True)
R=pd.DataFrame(rows); R.to_csv('/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_redteam/b_slow.csv',index=False)
print(R.drop(columns=['rep','fold']).mean().round(4).to_string())
print('paired WURonly - pooled on WUR held-out:', (R.P1_WURonlytrain_WUR-R.P1_24_WUR).describe().round(4).to_dict())
