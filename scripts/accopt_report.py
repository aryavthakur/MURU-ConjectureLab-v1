"""Stage 5: architecture comparison (pooled held-out) + final report."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT/"scripts"))
import accopt_selectors as S
import accopt_run as R
OUT = WT/"artifacts"/"accopt"

worlds = S.load(); W = {w["world_id"]: w for w in worlds}
fold = S.assign_folds(worlds); allids = set(W)
res = json.loads((OUT/"run_result.json").read_text())
held = json.loads((OUT/"held_out_selections.json").read_text())
fdiag = json.loads((OUT/"failure_diagnosis.json").read_text())

runs = {}
runs[("BASELINE_30","-","-")] = R.run_arch(worlds,"BASELINE_30","B1","R2")
runs[("SUPPORT_CONSENSUS","-","-")] = R.run_arch(worlds,"SUPPORT_CONSENSUS","B1","R2")
for fv in R.FAM_VOTES:
    runs[("SUPPORT_PLUS_FAMILY_CONSENSUS",fv,"-")] = R.run_arch(worlds,"SUPPORT_PLUS_FAMILY_CONSENSUS",fv,"R2")
    for rr in R.REP_RULES:
        runs[("CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE",fv,rr)] = R.run_arch(worlds,"CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE",fv,rr)

BLK = [("all",S.POSITIVE_BLOCKS),("G1A",{"G1A"}),("G1B",{"G1B"}),("G1C",{"G1C"})]

def nested_heldout(arch, vote_space, rep_space):
    """Pooled held-out: variant chosen on the training fold, scored on the test fold."""
    sel_by_world, choices = {}, {}
    for f in range(S.N_FOLDS):
        tr = {w for w in allids if fold[w]!=f}; te = {w for w in allids if fold[w]==f}
        best=None
        for fv in vote_space:
            for rr in rep_space:
                sel = runs[(arch,fv,rr)]
                fk,fn = R.rates(worlds,sel,tr,"t_family",S.POSITIVE_BLOCKS)
                sk,sn = R.rates(worlds,sel,tr,"t_support",S.POSITIVE_BLOCKS)
                k=(-(fk/max(fn,1)),-(sk/max(sn,1)),fv,rr)
                if best is None or k<best[0]: best=(k,fv,rr)
        _,fv,rr = best; choices[f]=(fv,rr)
        for wid in te: sel_by_world[wid]=runs[(arch,fv,rr)][wid]
    return sel_by_world, choices

def score(selmap, gated_gate=None):
    row={}
    for lbl, blocks in BLK:
        n=k=0; nf=kf=0; ne=ke=0
        for wid,r in selmap.items():
            w=W[wid]
            if not w["scorable"] or w["block"] not in blocks: continue
            rep_ok = True if gated_gate is None else held[wid]["report"]
            if r["t_support"] is not None: n+=1; k+= bool(r["t_support"]) and rep_ok
            if r["t_family"] is not None: nf+=1; kf+= bool(r["t_family"]) and rep_ok
            if r["t_exact"] is not None: ne+=1; ke+= bool(r["t_exact"]) and rep_ok
        row[lbl]={"support":[k,n],"family":[kf,nf],"exact":[ke,ne]}
    return row

arch_rows = {}
arch_rows["BASELINE_30"] = score(runs[("BASELINE_30","-","-")])
arch_rows["SUPPORT_CONSENSUS"] = score(runs[("SUPPORT_CONSENSUS","-","-")])
s3,c3 = nested_heldout("SUPPORT_PLUS_FAMILY_CONSENSUS", R.FAM_VOTES, ["-"])
arch_rows["SUPPORT_PLUS_FAMILY_CONSENSUS"] = score(s3)
s4,c4 = nested_heldout("CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE", R.FAM_VOTES, R.REP_RULES)
arch_rows["CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE"] = score(s4)
arch_rows["CONSENSUS_PLUS_REPRESENTATIVE_PLUS_REFUSAL_GATE"] = score(s4, gated_gate=True)

# ---- R2 distributions ------------------------------------------------------
def r2dist(cats):
    v=[]
    for w in worlds:
        if S.category(w["block"]) not in cats: continue
        br=[s["best_valid_r2"] for s in w["seeds"] if s["best_valid_r2"]==s["best_valid_r2"]]
        if br: v.append(float(np.median(br)))
    a=np.array(v)
    return {"n":len(a),"mean":float(a.mean()),"median":float(np.median(a)),
            "p05":float(np.percentile(a,5)),"p95":float(np.percentile(a,95)),
            "min":float(a.min()),"max":float(a.max())}

dists={c:r2dist({c}) for c in ("positive","null","refusal")}
for name,blocks in [("no_law",S.NO_LAW_BLOCKS),("mass_only",S.MASS_ONLY_BLOCKS),
                    ("confounded",S.CONFOUNDED_BLOCKS)]:
    v=[]
    for w in worlds:
        if w["block"] not in blocks: continue
        br=[s["best_valid_r2"] for s in w["seeds"] if s["best_valid_r2"]==s["best_valid_r2"]]
        if br: v.append(float(np.median(br)))
    a=np.array(v); dists[name]={"n":len(a),"mean":float(a.mean()),"median":float(np.median(a)),
                                "p95":float(np.percentile(a,95)),"max":float(a.max())}

out = {"architectures":arch_rows,"fold_choices_arch3":{str(k):v for k,v in c3.items()},
       "fold_choices_arch4":{str(k):v for k,v in c4.items()},
       "r2_distributions":dists}
(OUT/"architecture_comparison.json").write_text(json.dumps(out,indent=1,default=str))
print(json.dumps(out,indent=1,default=str))
