#!/usr/bin/env python3
"""Regenerate Phase 4 figures from frozen result JSON and machine-readable tables."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

P4=Path(__file__).resolve().parents[1]
FROOT=P4/'figures'
TROOT=P4/'supplement/COMPLETE_SUPPLEMENTARY_TABLES'
BLUE='#285f8f'; ORANGE='#cc7620'; GRAY='#59636d'; GREEN='#4a8567'; LIGHT='#f6f8fa'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160,'savefig.dpi':450,'svg.fonttype':'none','pdf.fonttype':42})

def save(fig,n):
    out=FROOT/f'FIGURE_{n}';out.mkdir(parents=True,exist_ok=True)
    stem=f'figure_{n}'
    for ext in ('svg','pdf','png'): fig.savefig(out/f'{stem}.{ext}',bbox_inches='tight',facecolor='white')
    plt.close(fig)

def box(ax,x,y,w,h,title,body,color,fontsize=10):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.035,rounding_size=.08',fc='white',ec=color,lw=2)
    ax.add_patch(p);ax.text(x+w/2,y+h-.18,title,ha='center',va='top',weight='bold',color=color,fontsize=11)
    ax.text(x+.16,y+h-.52,body,ha='left',va='top',fontsize=fontsize,linespacing=1.28,color='#20252a')

def arrow(ax,a,b,color=GRAY,rad=0): ax.add_patch(FancyArrowPatch(a,b,connectionstyle=f'arc3,rad={rad}',arrowstyle='-|>',mutation_scale=14,color=color,lw=1.6))

def fig1():
    fig,ax=plt.subplots(figsize=(11.5,6.1));ax.set_xlim(0,11.5);ax.set_ylim(0,6.1);ax.axis('off')
    box(ax,.15,4.05,2.4,1.5,'Stage 3 context','404 trajectories\n275 scaffold groups\nHistorical context only',GRAY,11)
    box(ax,2.85,4.05,2.55,1.5,'WUR-v2 development','1,325 compounds\n13 model families\nScaffold-held-out',BLUE,11)
    box(ax,5.7,4.05,1.85,1.5,'Frozen model','Tier A + Morgan\nridge; frozen\nNo MSnLib refit',GREEN,10.5)
    box(ax,7.85,4.05,3.35,1.5,'MSnLib external evaluation','Measured: 1,794\nSupport excluded: 5\nScored: 1,789\nScaffold groups: 1,687',ORANGE,10.5)
    arrow(ax,(2.55,4.8),(2.85,4.8));arrow(ax,(5.4,4.8),(5.7,4.8));arrow(ax,(7.55,4.8),(7.85,4.8))
    box(ax,.4,1.25,3.3,1.75,'Exposure history','Sample 1 exposed pre-score\nNot scored; excluded\nReplacement draw: once,\noutcome-blind',ORANGE,10)
    box(ax,4.1,1.25,3.3,1.75,'Separate CE Design A','33 compounds\nK1 highest point score\nAdjusted intervals cross zero\nVerdict: unresolved',GRAY,10)
    box(ax,7.85,1.25,3.35,1.75,'External result','P1 ratio: 0.97067\nScaffold CI: [.95236, .98927]\n2.93% lower\n5% target missed',BLUE,10.5)
    arrow(ax,(9.53,4.02),(9.53,3.03),ORANGE)
    ax.text(.3,.45,'Recorded key/scaffold exclusion does not establish zero structural similarity. The four-frame census check is separate from external model evaluation.',fontsize=9,color=GRAY)
    save(fig,1)

def fig2():
    d2=pd.read_csv(TROOT/'figure_2_data.csv').set_index('metric')['value']; dev=float(d2['development_ratio']); ratio=float(d2['ratio']); lo=float(d2['ratio_ci_low']); hi=float(d2['ratio_ci_high']); n=int(d2['n_scored'])
    fig,ax=plt.subplots(figsize=(9.0,5.1));ax.axvline(1,color='#222',lw=1.3,ls='--')
    ax.scatter([dev,ratio],[1,0],s=100,c=[BLUE,ORANGE],zorder=3)
    ax.errorbar(ratio,0,xerr=[[ratio-lo],[hi-ratio]],fmt='none',ecolor=ORANGE,capsize=6,lw=2)
    ax.text(dev,1.16,f'{dev:.3f}',ha='center',weight='bold',fontsize=12,color=BLUE)
    ax.text(ratio,-.23,f"{ratio:.3f} [{lo:.3f}, {hi:.3f}]",ha='center',fontsize=10,color=ORANGE)
    ax.axvline(.95,color='#7a4a22',lw=1.2,ls=':',label='5% practical target (0.95)')
    ax.set_yticks([0,1],[f'MSnLib external\n(n={n:,} compounds)','Development\n(scaffold OOF)']);ax.set_xlim(.82,1.04);ax.set_ylim(-.55,1.48)
    ax.set_xlabel('Pooled trajectory RMSE ratio (candidate / Tier A reference)');ax.set_title('The external interval excludes 1 but not the 5% target',loc='left',weight='bold')
    ax.text(.825,-.49,'Development point estimate only; its reported simultaneous max-T interval was not reproduced.\nExternal interval: 10,000 whole-scaffold bootstrap replicates.',fontsize=9,color=GRAY)
    ax.legend(loc='upper right',frameon=False,fontsize=9)
    save(fig,2)

def fig3():
    raw=pd.read_csv(TROOT/'figure_3_compound_errors.csv')
    fig,axs=plt.subplots(1,2,figsize=(11.2,5.0),gridspec_kw={'width_ratios':[1.2,1]})
    vals=[raw.error_muru20,raw.error_reference20,raw.error_muru60,raw.error_reference60]
    bp=axs[0].boxplot(vals,patch_artist=True,showfliers=False,whis=(5,95),medianprops={'color':'#222','linewidth':1.4})
    for b,col in zip(bp['boxes'],[BLUE,ORANGE,BLUE,ORANGE]):b.set_facecolor(col);b.set_alpha(.78)
    axs[0].axhline(0,color='#222',lw=.8);axs[0].set_xticks([1,2,3,4],['MURU\nNCE 20','Reference\nNCE 20','MURU\nNCE 60','Reference\nNCE 60'])
    axs[0].set_ylabel('Signed prediction error in μ');axs[0].set_title('Compound-rung errors\n(box: IQR; whiskers: 5th–95th percentiles)',loc='left',weight='bold',fontsize=11)
    vals2=[raw.rmse_muru,raw.rmse_reference]
    bp2=axs[1].boxplot(vals2,patch_artist=True,showfliers=False,whis=(5,95),medianprops={'color':'#222','linewidth':1.4})
    for b,col in zip(bp2['boxes'],[BLUE,ORANGE]):b.set_facecolor(col);b.set_alpha(.78)
    axs[1].axhline(.20,color=GRAY,ls='--',lw=1.2,label='AF threshold = 0.20')
    axs[1].set_xticks([1,2],['MURU','Tier A\nreference']);axs[1].set_ylabel('Two-rung compound RMSE');axs[1].set_title('Compound error and threshold',loc='left',weight='bold',fontsize=11)
    axs[1].legend(frameon=False,fontsize=9,loc='lower left')
    summary=pd.read_csv(TROOT/'error_summary.csv').set_index('metric'); tail=pd.read_csv(TROOT/'figure_3_tail_data.csv').set_index('metric')
    afc=float(summary.loc['AF','candidate']); afr=float(summary.loc['AF','reference']); ci=[float(tail.loc['AF_diff','low']),float(tail.loc['AF_diff','high'])]; cvarc=float(summary.loc['CVaR95','candidate']); cvarr=float(summary.loc['CVaR95','reference'])
    note=(f"Tail summaries (descriptive)\nAF: {afc:.3f} vs {afr:.3f}\nAF difference 95% CI: [{ci[0]:+.3f}, {ci[1]:+.3f}]\nCVaR95: {cvarc:.3f} vs {cvarr:.3f}\nNo tail-risk improvement demonstrated.")
    fig.tight_layout(rect=(0,.18,1,1),w_pad=2.0)
    fig.text(.53,.035,note,ha='left',va='bottom',fontsize=9.4,color='#27313a',linespacing=1.25)
    save(fig,3)

def fig4():
    d=pd.read_csv(TROOT/'figure_4_data.csv');d['q']=d.quartile.str.extract(r'Q([1-4])').astype(int);d=d.sort_values('q')
    fig,ax=plt.subplots(figsize=(9.0,5.0));ax.axhline(1,color='#222',ls='--',lw=1.2)
    ax.bar(d.q,d.ratio,color=[ORANGE,BLUE,BLUE,BLUE],width=.62)
    ax.set_xticks(d.q,[f"Q{q}\nn={n}" for q,n in zip(d.q,d.n)]);ax.set_ylim(.92,1.04);ax.set_ylabel('P1 ratio (MURU / Tier A reference)')
    ax.set_title('The least-similar quartile has slightly higher candidate error',loc='left',weight='bold')
    for q,r in zip(d.q,d.ratio):ax.text(q,r+.003,f'{r:.4f}',ha='center',fontsize=10,weight='bold')
    ax.text(.02,-.16,'Q1 is the lowest maximum Morgan-count Tanimoto similarity. Quartile estimates are descriptive; no quartile-specific intervals were computed.',transform=ax.transAxes,fontsize=9,color=GRAY)
    fig.subplots_adjust(bottom=.23);save(fig,4)

def fig5():
    d=pd.read_csv(TROOT/'figure_5_design_a_data.csv'); comp=pd.read_csv(TROOT/'figure_5_comparator_data.csv')
    fig,axs=plt.subplots(1,2,figsize=(11.0,5.0),gridspec_kw={'width_ratios':[1,1.2]})
    y=np.arange(len(d));axs[0].axvline(0,color='#222',lw=1,ls='--')
    axs[0].errorbar(d.estimate,y,xerr=[d.estimate-d.low,d.high-d.estimate],fmt='o',color=ORANGE,capsize=5,lw=1.8)
    axs[0].set_yticks(y,d.contrast);axs[0].invert_yaxis();axs[0].set_xlim(-.035,.14);axs[0].set_xlabel('Difference in mean cosine similarity')
    axs[0].set_title('Design A: Bonferroni-adjusted 98.33% CIs',loc='left',weight='bold',fontsize=11)
    names=['FIORA-OS v0.1.0','ICEBERG 2.1','GLACIER'];comp=comp.set_index('model').loc[names].reset_index();x=np.arange(3);w=.34
    axs[1].axhline(1,color='#222',lw=1,ls='--');axs[1].bar(x-w/2,comp.ratio,w,color=BLUE,label='Model-specific primary input')
    for i,row in comp.iterrows():
        if np.isfinite(row.raw_nce_ratio):axs[1].bar(i+w/2,row.raw_nce_ratio,w,color=ORANGE,label='Raw-NCE diagnostic (two models)' if i==1 else None)
    axs[1].set_xticks(x,['FIORA-OS','ICEBERG 2.1','GLACIER'],rotation=8);axs[1].set_ylabel('MURU / comparator P1 ratio on derived μ')
    axs[1].set_ylim(.5,1.4);axs[1].set_title('Comparator ratios change with CE input',loc='left',weight='bold',fontsize=11);axs[1].legend(frameon=False,fontsize=9)
    fig.text(.08,.015,'Primary inputs: FIORA native NCE; ICEBERG and GLACIER ev_primary. Raw-NCE sensitivity is shown for ICEBERG/GLACIER only.\nDesign A: K1 led descriptively, but adjusted intervals cross zero; verdict remains INTERFACE_UNRESOLVED.',fontsize=8.8,color=GRAY)
    fig.tight_layout(rect=(0,.07,1,1));save(fig,5)

if __name__=='__main__':
    fig1();fig2();fig3();fig4();fig5()
    print('Regenerated five figures (SVG/PDF/PNG) from frozen outputs and source tables.')
