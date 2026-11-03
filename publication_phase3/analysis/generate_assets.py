#!/usr/bin/env python3
"""Export publication tables and five figures from frozen MURU records.

Run from the repository root with: python3.13 publication_phase3/analysis/generate_assets.py
No model fitting or raw-data decoding occurs in this script.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "publication_phase3"
FIG = OUT / "figures"
TAB = OUT / "tables"
RES = ROOT / "artifacts/wur_v2_confirmation_v2/result/external_analysis.json"
FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
R = json.loads(RES.read_text())
plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10, "axes.spines.top":False,
                     "axes.spines.right":False, "figure.dpi":160, "savefig.dpi":400,
                     "svg.fonttype":"none", "pdf.fonttype":42})
BLUE="#285f8f"; ORANGE="#d1842c"; GRAY="#68737d"; GREEN="#4a8567"

def savefig(fig, name):
    for ext in ("svg", "pdf", "png"): fig.savefig(FIG/f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)

def export_tables():
    c, t, b = R["candidate"], R["ta_ridge"], R["bootstrap"]
    rows = [
      ["Population compounds",R["n_population_compounds"],"count"],
      ["Measured compounds",R["n_measured_compounds"],"count"],
      ["Unsupported exclusions",R["n_excluded_unsupported"],"count"],
      ["Scored compounds",R["n_scored"],"count"],
      ["Scaffold groups",R["n_scaffold_groups_scored"],"count"],
      ["Candidate P1",c["P1"],"pooled two-rung RMSE"], ["Reference P1",t["P1"],"pooled two-rung RMSE"],
      ["P1 ratio",b["P1_ratio"],"candidate/reference"], ["P1 ratio 95% CI lower",b["P1_ratio_ci"][0],"scaffold bootstrap"],
      ["P1 ratio 95% CI upper",b["P1_ratio_ci"][1],"scaffold bootstrap"],
      ["Relative P1 reduction",1-b["P1_ratio"],"1 - ratio"],
      ["AF candidate",c["AF"],"fraction RMSE > 0.20"], ["AF reference",t["AF"],"fraction RMSE > 0.20"],
      ["CVaR95 candidate",c["CVaR95"],"mean worst 5% compound RMSE"], ["CVaR95 reference",t["CVaR95"],"mean worst 5% compound RMSE"],
    ]
    pd.DataFrame(rows,columns=["metric","value","definition"]).to_csv(TAB/"primary_results.csv",index=False)
    p=[]
    for e in ("20.0","60.0"):
      p.append({"NCE":int(float(e)),"candidate_RMSE":R["per_rung_candidate"][e],"reference_RMSE":R["per_rung_ta_ridge"][e],**R["per_rung_detail"][e]})
    pd.DataFrame(p).to_csv(TAB/"per_energy_results.csv",index=False)
    n=[]
    for q,v in R["novelty_bins"].items(): n.append({"quartile":q,**v})
    pd.DataFrame(n).to_csv(TAB/"novelty_results.csv",index=False)
    pd.DataFrame([
      {"metric":m,"candidate":c[m],"reference":t[m]} for m in ["P1","MRMSE","MED","Q90","Q95","CVaR95","AF","AF_max"]
    ]).to_csv(TAB/"error_summary.csv",index=False)

def figure1():
    fig,ax=plt.subplots(figsize=(11,5.1)); ax.set_xlim(0,11); ax.set_ylim(0,5.1); ax.axis("off")
    def box(x,y,w,h,title,body,color):
      p=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.03,rounding_size=0.08",fc="white",ec=color,lw=1.8)
      ax.add_patch(p); ax.text(x+w/2,y+h-.28,title,ha="center",va="top",weight="bold",color=color,fontsize=8.5)
      ax.text(x+.14,y+h-(.92 if "\n" in title else .62),body,ha="left",va="top",fontsize=6.8,linespacing=1.18)
    box(.2,3.15,2.25,1.35,"Historical Stage 3","WUR-era external\ncontext\n404 trajectories /\n275 scaffolds\nNot v2 confirmation",GRAY)
    box(3.05,3.15,2.35,1.35,"WUR-v2 development","1,325 compounds\nScaffold-held-out\nmodel search\n13 experiment families",BLUE)
    box(6.05,3.15,2.15,1.35,"Frozen model","Tier A + Morgan\nridge\nFrozen 2026-09-13\nNo external refit",GREEN)
    box(8.8,3.15,2.0,1.35,"MSnLib\nconfirmation","1,794 measured\n5 support\nexclusions\n1,789 scored\n1,687 groups",ORANGE)
    for x1,x2 in [(2.45,3.05),(5.4,6.05),(8.2,8.8)]: ax.add_patch(FancyArrowPatch((x1,3.82),(x2,3.82),arrowstyle="-|>",mutation_scale=12,color="#59636d"))
    box(2.05,.55,2.65,1.55,"Earlier sample exposure","Sample 1 parser-preflight\nincident\nNot scored; permanently\nexcluded\nReplacement sample 2 used",ORANGE)
    box(5.25,.55,2.5,1.55,"External result","Whole-scaffold\nbootstrap\n10,000 replicates\nseed 20261011\nMODEST EXTERNAL\nCONFIRMATION",BLUE)
    box(8.3,.55,2.5,1.55,"Separate CE study","Design A: 33 compounds\nRaw NCE highest\nobserved score\nDecision: INTERFACE\nUNRESOLVED",GRAY)
    ax.add_patch(FancyArrowPatch((9.8,3.12),(6.5,2.13),connectionstyle="arc3,rad=.12",arrowstyle="-|>",mutation_scale=12,color=ORANGE,lw=1.3))
    ax.add_patch(FancyArrowPatch((7.75,1.32),(8.3,1.32),arrowstyle="-|>",mutation_scale=12,color=GRAY,lw=1.3))
    ax.text(.25,.18,"Development and external evidence are distinct; Design A is a separate comparator-interface study.",fontsize=8.5,color=GRAY)
    savefig(fig,"figure_1_study_design")

def figure2():
    fig,ax=plt.subplots(figsize=(8.2,4.8))
    labels=["MSnLib\n(external)","Development\n(scaffold OOF)" ]
    ratios=[0.8885713,R["bootstrap"]["P1_ratio"]]
    ax.axvline(1,color="#222",lw=1.2,ls="--")
    ax.scatter(ratios,[1,0],s=100,c=[BLUE,ORANGE],zorder=3)
    ax.text(ratios[0],1.14,"0.889",ha="center",weight="bold",color=BLUE)
    b=R["bootstrap"]["P1_ratio_ci"]
    ax.errorbar(ratios[1],0,xerr=[[ratios[1]-b[0]],[b[1]-ratios[1]]],fmt="none",ecolor=ORANGE,capsize=5,lw=2)
    ax.text(ratios[1],-.28,"0.971 [0.952, 0.989]",ha="center",fontsize=9,color=ORANGE)
    ax.set_yticks([0,1],labels); ax.set_xlim(.82,1.04); ax.set_ylim(-.55,1.45); ax.set_xlabel("Pooled trajectory RMSE ratio (candidate / Tier A reference)")
    ax.set_title("Development gain attenuated in the independent MSnLib study",loc="left",weight="bold")
    ax.text(.83,-.47,"Development interval not independently reproduced in the available audit record; point estimate shown only.\nMSnLib interval: 10,000 whole-scaffold bootstrap replicates.",fontsize=8,color=GRAY)
    savefig(fig,"figure_2_performance")

def figure3():
    raw=pd.read_csv(TAB/"external_compound_errors.csv")
    fig,axs=plt.subplots(1,2,figsize=(10,4.5),gridspec_kw={"width_ratios":[1.2,1]})
    vals=[raw.error_muru20,raw.error_reference20,raw.error_muru60,raw.error_reference60]
    bp=axs[0].boxplot(vals,patch_artist=True,showfliers=False,whis=(5,95),medianprops={"color":"#222","linewidth":1.3})
    for box,col in zip(bp["boxes"],[BLUE,ORANGE,BLUE,ORANGE]): box.set_facecolor(col); box.set_alpha(.75)
    axs[0].axhline(0,color="#222",lw=.8); axs[0].set_xticks([1,2,3,4],["MURU\nNCE 20","Reference\nNCE 20","MURU\nNCE 60","Reference\nNCE 60"])
    axs[0].set_ylabel("Signed prediction error in μ"); axs[0].set_title("Compound-rung errors (5th–95th whiskers)",loc="left",weight="bold")
    vals2=[raw.rmse_muru,raw.rmse_reference]
    bp2=axs[1].boxplot(vals2,patch_artist=True,showfliers=False,whis=(5,95),medianprops={"color":"#222","linewidth":1.3})
    for box,col in zip(bp2["boxes"],[BLUE,ORANGE]): box.set_facecolor(col); box.set_alpha(.75)
    axs[1].axhline(.20,color=GRAY,ls="--",lw=1,label="AF threshold 0.20")
    axs[1].set_xticks([1,2],["MURU","Tier A\nreference"]); axs[1].set_ylabel("Two-rung compound RMSE"); axs[1].set_title("Compound error and threshold",loc="left",weight="bold")
    axs[1].legend(frameon=False,fontsize=7.5)
    axs[1].text(.02,.97,f"AF: {R['candidate']['AF']:.3f} vs {R['ta_ridge']['AF']:.3f}\nCVaR95: {R['candidate']['CVaR95']:.3f} vs {R['ta_ridge']['CVaR95']:.3f}\nAF difference 95% CI includes zero.",transform=axs[1].transAxes,va="top",fontsize=7.3,color=GRAY)
    fig.tight_layout(); savefig(fig,"figure_3_external_errors")

def figure4():
    d=pd.read_csv(TAB/"novelty_results.csv")
    # Stable ascending order by quartile labels
    d["q"] = d.quartile.str.extract(r"Q([1-4])").astype(int); d=d.sort_values("q")
    fig,ax=plt.subplots(figsize=(8.2,4.8)); colors=[ORANGE,BLUE,BLUE,BLUE]
    ax.axhline(1,color="#222",ls="--",lw=1)
    ax.bar(d.q,d.ratio,color=colors,width=.63)
    ax.set_xticks(d.q,[f"Q{q}\nn={n}" for q,n in zip(d.q,d.n)])
    ax.set_ylim(.92,1.035); ax.set_ylabel("P1 ratio (MURU / Tier A reference)")
    ax.set_title("MURU advantage is absent in the least-similar quartile",loc="left",weight="bold")
    for q,r in zip(d.q,d.ratio): ax.text(q,r+.003,f"{r:.3f}",ha="center",fontsize=9,weight="bold")
    fig.text(.13,.015,"Q1 is most novel (lowest max Morgan-count Tanimoto similarity); no quartile-specific intervals were computed.",fontsize=8,color=GRAY)
    fig.subplots_adjust(bottom=.20)
    savefig(fig,"figure_4_structural_novelty")

def figure5():
    fig,axs=plt.subplots(1,2,figsize=(10,4.8),gridspec_kw={"width_ratios":[1,1.15]})
    contrasts=["K1 − K2","K1 − K3"]
    points=[.042318,.050333]; lo=[-.012660,-.007439]; hi=[.099083,.109993]
    yy=np.arange(2)
    axs[0].axvline(0,color="#222",lw=1,ls="--")
    axs[0].errorbar(points,yy,xerr=[np.array(points)-lo,np.array(hi)-points],fmt="o",color=ORANGE,capsize=4,lw=1.8)
    axs[0].set_yticks(yy,contrasts); axs[0].invert_yaxis(); axs[0].set_xlim(-.04,.14); axs[0].set_xlabel("Difference in composite similarity")
    axs[0].set_title("Design A: adjusted 98.33% intervals",loc="left",weight="bold")
    model=["FIORA-OS","ICEBERG 2.1","GLACIER"]
    primary=[.619,.781,.914]; raw=[np.nan,1.076,1.238]
    x=np.arange(3); w=.34
    axs[1].axhline(1,color="#222",lw=1,ls="--")
    axs[1].bar(x-w/2,primary,w,color=BLUE,label="Mapped primary")
    axs[1].bar(x[1:]+w/2,raw[1:],w,color=ORANGE,label="Raw-NCE diagnostic")
    axs[1].set_xticks(x,model,rotation=12); axs[1].set_ylabel("MURU / comparator pooled RMSE")
    axs[1].set_ylim(.5,1.38); axs[1].set_title("Comparator ranking changes with CE input",loc="left",weight="bold"); axs[1].legend(frameon=False,fontsize=8)
    fig.text(.11,.015,"<1 favors MURU; >1 favors comparator. Design A: K1 score 0.557; both adjusted intervals cross zero.",fontsize=7.5,color=GRAY)
    fig.tight_layout(rect=(0,.07,1,1)); savefig(fig,"figure_5_energy_interface")

def main():
    export_tables()
    figure1(); figure2(); figure3(); figure4(); figure5()
    print(f"Generated tables and figures under {OUT}")

if __name__ == "__main__": main()
