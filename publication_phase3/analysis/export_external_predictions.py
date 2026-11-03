#!/usr/bin/env python3
"""Export compound-level residuals from the frozen external model artifacts."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from muru.wur_v2 import candidate as CA
from muru.wur_v2 import decode_authority as DA

V2=ROOT/"artifacts/wur_v2_confirmation_v2"
OUT=ROOT/"publication_phase3/tables/external_compound_errors.csv"
def main():
    mu=pd.read_csv(V2/"result/measured_mu.csv")
    pop=pd.read_csv(ROOT/DA.POPULATION_CSV)
    W=mu.pivot(index="key",columns="energy",values="mu").reindex(columns=[20.0,60.0])
    p=pop.set_index("key").loc[W.index]
    a,b=-5.95552603907965,.8618030610784555
    E=(np.array([20.,60.])-a)/b
    cand=json.loads((ROOT/DA.CANDIDATE_JSON).read_text())
    ref=json.loads((ROOT/DA.COMPARATOR_JSON).read_text())
    pc=CA.predict_mu(cand,p.smiles,p.mh,E); pr=CA.predict_mu(ref,p.smiles,p.mh,E)
    supported=CA.supported(cand,p.smiles,p.mh,E).all(1)&CA.supported(ref,p.smiles,p.mh,E).all(1)
    complete=np.isfinite(W.to_numpy()).all(1); keep=supported&complete
    y=W.to_numpy()[keep]; keys=W.index.to_numpy()[keep]
    x=pd.DataFrame({"key":keys,"scaffold_group":p.scaffold_group.to_numpy()[keep],"mu20":y[:,0],"mu60":y[:,1],
                    "prediction_muru20":pc[keep,0],"prediction_muru60":pc[keep,1],
                    "prediction_reference20":pr[keep,0],"prediction_reference60":pr[keep,1]})
    x["error_muru20"]=x.prediction_muru20-x.mu20; x["error_muru60"]=x.prediction_muru60-x.mu60
    x["error_reference20"]=x.prediction_reference20-x.mu20; x["error_reference60"]=x.prediction_reference60-x.mu60
    x["rmse_muru"]=np.sqrt((x.error_muru20**2+x.error_muru60**2)/2)
    x["rmse_reference"]=np.sqrt((x.error_reference20**2+x.error_reference60**2)/2)
    x.to_csv(OUT,index=False,float_format="%.12g")
    print(f"wrote {len(x)} compounds to {OUT}")
if __name__=="__main__": main()
