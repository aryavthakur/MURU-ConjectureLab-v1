"""Figure 6: Four-Tier Evidence Hierarchy and Scientific Claim Boundaries.

Publication-quality diagram of the MURU evidence hierarchy:
- Panel 6A: Four-tier evidence categorization (Class A Historical, Class B Frozen Methods, Class C Prospective Results, Future External Real Data)
- Panel 6B: Historical vs Prospective claim comparisons & divergences (Support vs Family vs Exact Algebra)
- Panel 6C: Forbidden inference boundaries and governance constraints

No result numbers. Strictly reproducible design schematic.
"""

from __future__ import annotations

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Styling configuration
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "mathtext.fontset": "dejavusans",
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "figure.dpi": 300,
})

def generate_figure(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(16.0, 11.2), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 0.95], hspace=0.28, wspace=0.22,
                           left=0.06, right=0.96, top=0.94, bottom=0.05)
    
    # -------------------------------------------------------------------------
    # Panel 6A: Four-Tier Evidence Classification
    # -------------------------------------------------------------------------
    ax6a = fig.add_subplot(gs[0, 0])
    ax6a.set_title("A   Four-Tier Evidence Classification Framework", loc="left", pad=10)
    ax6a.set_xlim(0, 10)
    ax6a.set_ylim(0, 10)
    ax6a.axis("off")
    
    card6a = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax6a.add_patch(card6a)
    
    tiers = [
        ("CLASS A: Historical Development Evidence",
         "• Phase 1, Phase 2, Phase 3 (STOP BEFORE PHASE 4), Type 2 (DO NOT AUTHORIZE P4)\n• Background, method motivation, and diagnostic context only\n• NEVER entered into prospective primary denominators or rates",
         "#f1f5f9", "#64748b", "#334155", 7.2),
        
        ("CLASS B: Frozen Prospective Methods & Contracts",
         "• V1 Freeze (d94d2c9), Amendments A1–A3.4, Temporal Erratum (220c9cb)\n• 380 cases manifest, truth payloads, PySR grammar, 8-stage acceptance predicate\n• Primary gates G1/G2/G3 & secondary evaluation contracts (A3.4)",
         "#eff6ff", "#3b82f6", "#1d4ed8", 4.9),
        
        ("CLASS C: Prospective Benchmark Results",
         "• 100 Calibration worlds (Threshold freeze), 80 Development cases (Sanity rerun)\n• 240 Held-Out cases (Primary gates G1–G3), 60 Challenge stress cases\n• STRICTLY SEALED until execution under frozen RC4 production code",
         "#fef3c7", "#d97706", "#92400e", 2.6),
        
        ("TIER 4: Future External Real-Data Validation",
         "• Sealed Confirmation set (110 compounds, 82 scaffolds; SHA-256 d6b6b135...)\n• Requires future prospective physical acquisitions & multi-instrument calibration\n• OUT OF SCOPE for current manuscript (Synthetic benchmark only)",
         "#fee2e2", "#ef4444", "#b91c1c", 0.3),
    ]
    
    for title, desc, bg, edge, tc, y in tiers:
        box = patches.FancyBboxPatch((0.4, y), 9.2, 2.05, boxstyle="round,pad=0.12",
                                     facecolor=bg, edgecolor=edge, lw=1.2)
        ax6a.add_patch(box)
        ax6a.text(0.7, y + 1.6, title, ha="left", va="center",
                  fontweight="bold", color=tc, fontsize=7.8)
        ax6a.text(0.7, y + 0.75, desc, ha="left", va="center",
                  color="#1e293b", fontsize=6.8, linespacing=1.25)

    # -------------------------------------------------------------------------
    # Panel 6B: Ladder of Claims & Identifiability Divergence
    # -------------------------------------------------------------------------
    ax6b = fig.add_subplot(gs[0, 1])
    ax6b.set_title("B   Ladder of Scientific Claims (Why Endpoint Levels Diverge)", loc="left", pad=10)
    ax6b.set_xlim(0, 10)
    ax6b.set_ylim(0, 10)
    ax6b.axis("off")
    
    card6b = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax6b.add_patch(card6b)
    
    levels = [
        ("Level 1: Effective Variable Support", "Matches active primitive variables (Denominator: 144)", "#e0f2fe", "#0284c7"),
        ("Level 2: Mathematical Family Structure", "Matches truth taxonomy skeleton (G2 Primary Gate, Denom: 144)", "#dcfce7", "#16a34a"),
        ("Level 3: Dimensionless Parameter Elasticity", "Normalized mass exponent & descriptor coupling at x0 (Denom: 156)", "#fef3c7", "#d97706"),
        ("Level 4: Out-of-Sample Predictive Equivalence", "REL_RMSE <= 0.05 & r >= 0.990 over 12 ref frames (Denom: 144)", "#f3e8ff", "#9333ea"),
        ("Level 5: Exact Symbolic / Algebraic Identity", "Exact algebraic identity up to scale (Ungated Secondary, Denom: 60)", "#fee2e2", "#dc2626"),
    ]
    
    for i, (title, desc, bg, edge) in enumerate(levels):
        y = 7.7 - i * 1.75
        box = patches.FancyBboxPatch((0.5, y), 9.0, 1.45, boxstyle="round,pad=0.1",
                                     facecolor=bg, edgecolor=edge, lw=1.1)
        ax6b.add_patch(box)
        ax6b.text(0.8, y + 1.0, title, ha="left", va="center",
                  fontweight="bold", color="#0f172a", fontsize=7.6)
        ax6b.text(0.8, y + 0.45, desc, ha="left", va="center",
                  color="#334155", fontsize=6.8)
        
        if i < len(levels) - 1:
            ax6b.annotate("", xy=(5.0, y - 0.25), xytext=(5.0, y),
                          arrowprops=dict(arrowstyle="->", color="#94a3b8", lw=1.5))

    # -------------------------------------------------------------------------
    # Panel 6C: Historical Class A Evidence (Background Context)
    # -------------------------------------------------------------------------
    ax6c = fig.add_subplot(gs[1, 0])
    ax6c.set_title("C   Verified Historical Observations (CLASS A Development Findings)", loc="left", pad=10)
    ax6c.set_xlim(0, 10)
    ax6c.set_ylim(0, 10)
    ax6c.axis("off")
    
    card6c = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax6c.add_patch(card6c)
    
    hist_text = (
        r"$\mathbf{1.\ Support\ Recovery}$: Type 2 G1B moderate observed 20/20 block support recovery." + "\n" +
        r"$\mathbf{2.\ Family\ Recovery}$: Type 2 dense-lattice family recovery was 16/20 measured (composite passed 17/20)." + "\n" +
        r"$\mathbf{3.\ Exact\ Algebra}$: Phase 3 & Type 2 observed 0% symbolic equivalence across all positive blocks." + "\n" +
        r"$\mathbf{4.\ Exponent\ Recovery}$: Type 2 mass exponent median 0.500 [0.448, 0.540], 20/20 within $\pm 0.15$." + "\n" +
        r"$\mathbf{5.\ Pure\ Null\ Rejection}$: 0/100 accepted in Phase 3 and Type 2 (Clopper-Pearson upper 0.0362)." + "\n" +
        r"$\mathbf{6.\ Historical\ Verdicts}$: Phase 3 STOP BEFORE PHASE 4; Type 2 DO NOT AUTHORIZE PHASE 4."
    )
    ax6c.text(0.6, 5.0, hist_text, ha="left", va="center", fontsize=7.2, color="#1e293b", linespacing=1.4)
    
    # Tag
    ax6c.text(9.2, 9.1, "CLASS A HISTORICAL", ha="right", va="center",
              fontweight="bold", color="#475569", fontsize=7.2,
              bbox=dict(boxstyle="square,pad=0.2", facecolor="#e2e8f0", edgecolor="#94a3b8", lw=0.6))

    # -------------------------------------------------------------------------
    # Panel 6D: Binding Claim Boundaries & Forbidden Inferences
    # -------------------------------------------------------------------------
    ax6d = fig.add_subplot(gs[1, 1])
    ax6d.set_title("D   Strict Governance Boundaries & Forbidden Overclaims", loc="left", pad=10)
    ax6d.set_xlim(0, 10)
    ax6d.set_ylim(0, 10)
    ax6d.axis("off")
    
    card6d = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax6d.add_patch(card6d)
    
    bound_text = (
        r"$\mathbf{1.\ No\ Physical\ Law\ Claim}$: Discovered expressions are synthetic empirical fits," + "\n" +
        r"   never 'physical laws', 'universal equations', or 'mechanisms of fragmentation'." + "\n\n" +
        r"$\mathbf{2.\ No\ Real-Data\ Transferability}$: Synthetic benchmark success does not license" + "\n" +
        r"   real-world spectral claims; Phase 4 remains strictly unauthorized." + "\n\n" +
        r"$\mathbf{3.\ No\ Conflation\ of\ Levels}$: Family recovery (G2) never implies exact algebra," + "\n" +
        r"   and exact algebra non-recovery does not fail G2 (reported separately)." + "\n\n" +
        r"$\mathbf{4.\ No\ Cross-Class\ Pooling}$: Historical Class A rates are never merged into" + "\n" +
        r"   prospective Class C denominators or confidence intervals."
    )
    ax6d.text(0.6, 5.0, bound_text, ha="left", va="center", fontsize=7.2, color="#7f1d1d", linespacing=1.3)

    fig.suptitle("FIGURE 6: Evidence Hierarchy, Scientific Claim Boundaries, and Identifiability Limits",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    out_svg = out_dir / "fig06_evidence_hierarchy.svg"
    out_pdf = out_dir / "fig06_evidence_hierarchy.pdf"
    out_png = out_dir / "fig06_evidence_hierarchy.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 6:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
