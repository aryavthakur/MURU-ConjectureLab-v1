"""Figure 5: Secondary Endpoint Design (Parameter Recovery & Predictive Equivalence).

Publication-quality diagram of Amendment A3.4 secondary evaluation contracts:
- Panel 5A: Parameter Recovery contract at neutral reference anchor x_0 = (250, 0, 0, 0, 0)
- Panel 5B: Predictive Equivalence reference distribution (12 generator frames, 2,160 rows) & alignment metrics
- Panel 5C: Prospective Held-out secondary outcomes shell [PROSPECTIVE RESULT PANEL — DO NOT RENDER]

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
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1.0], hspace=0.28, wspace=0.22,
                           left=0.06, right=0.96, top=0.94, bottom=0.05)
    
    # -------------------------------------------------------------------------
    # Panel 5A: Parameter Recovery Scientific Contract
    # -------------------------------------------------------------------------
    ax5a = fig.add_subplot(gs[0, 0])
    ax5a.set_title(r"A   Parameter Recovery Contract at Anchor $\mathbf{x}_0 = (250, 0, 0, 0, 0)$", loc="left", pad=10)
    ax5a.set_xlim(0, 10)
    ax5a.set_ylim(0, 10)
    ax5a.axis("off")
    
    card5a = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax5a.add_patch(card5a)
    
    # Mass Exponent Box
    box_p = patches.FancyBboxPatch((0.5, 5.2), 9.0, 4.0, boxstyle="round,pad=0.15",
                                   facecolor="#eff6ff", edgecolor="#3b82f6", lw=1.2)
    ax5a.add_patch(box_p)
    ax5a.text(0.8, 8.6, r"1. Mass Scaling Exponent $p_{\mathrm{mass}}$ (156 Held-Out Cases)",
              ha="left", va="center", fontweight="bold", color="#1d4ed8", fontsize=8.0)
    p_text = (
        r"$\bullet\ \mathbf{Operator}$: $p_{\mathrm{mass}}(\hat{g}) = \left. \frac{\partial \ln \hat{g}}{\partial \ln m} \right|_{\mathbf{x}_0} = \left. \frac{m}{\hat{g}} \frac{\partial \hat{g}}{\partial m} \right|_{\mathbf{x}_0}$" + "\n" +
        r"$\bullet\ \mathbf{Planted\ Truth}$: $p_{\mathrm{truth}} = 0.50$ (F01..F05, F08..F12, F17, F18) or $[0.45, 0.75]$ (F07)" + "\n" +
        r"$\bullet\ \mathbf{Tolerance}$: $|p_{\mathrm{mass}}(\hat{g}) - p_{\mathrm{truth}}| \leq 0.15$ ($\pm 30\%$ physical resolution)" + "\n" +
        r"$\bullet\ \mathbf{Properties}$: Scale-invariant to $A > 0$; algebraically invariant to $\sqrt{m/250}$ vs $\sqrt{m}$"
    )
    ax5a.text(0.8, 6.8, p_text, ha="left", va="center", fontsize=7.2, color="#0f172a", linespacing=1.35)
    
    # Descriptor Coupling Box
    box_c = patches.FancyBboxPatch((0.5, 0.6), 9.0, 4.2, boxstyle="round,pad=0.15",
                                   facecolor="#ecfdf5", edgecolor="#059669", lw=1.2)
    ax5a.add_patch(box_c)
    ax5a.text(0.8, 4.2, r"2. Normalized Descriptor Coupling $c_{\mathrm{desc}}$ (84 Descriptor Cases)",
              ha="left", va="center", fontweight="bold", color="#065f46", fontsize=8.0)
    c_text = (
        r"$\bullet\ \mathbf{Affine / Sat}$: $c_{\mathrm{desc}} = \left. \frac{1}{\hat{g}} \frac{\partial \hat{g}}{\partial d} \right|_{\mathbf{x}_0}$ (F08, F09, F11, F12, F17)" + "\n" +
        r"$\bullet\ \mathbf{Interaction}$: $c_{\mathrm{desc}} = \left. \frac{1}{\hat{g}} \frac{\partial^2 \hat{g}}{\partial d \partial d_2} \right|_{\mathbf{x}_0}$ (F10)  |  $\mathbf{Exp}$: $c_{\mathrm{desc}} = \left. \frac{3}{\hat{g}} \frac{\partial \hat{g}}{\partial d} \right|_{\mathbf{x}_0}$ (F18)" + "\n" +
        r"$\bullet\ \mathbf{Planted\ Truth}$: $c_{\mathrm{truth}} \in [0.25, 0.55]$  |  $\mathbf{Tolerance}$: $|c_{\mathrm{desc}}(\hat{g}) - c_{\mathrm{truth}}| \leq 0.10$" + "\n" +
        r"$\bullet\ \mathbf{Reporting}$: Joint /156, Mass Exponent /156, Descriptor Coupling /84"
    )
    ax5a.text(0.8, 2.4, c_text, ha="left", va="center", fontsize=7.2, color="#064e3b", linespacing=1.35)

    # -------------------------------------------------------------------------
    # Panel 5B: Predictive Equivalence Contract (12 Reference Frames)
    # -------------------------------------------------------------------------
    ax5b = fig.add_subplot(gs[0, 1])
    ax5b.set_title("B   Predictive Equivalence Design (12 Reference Covariate Frames)", loc="left", pad=10)
    ax5b.set_xlim(0, 10)
    ax5b.set_ylim(0, 10)
    ax5b.axis("off")
    
    card5b = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax5b.add_patch(card5b)
    
    # 12 Frames Box
    box_fr = patches.FancyBboxPatch((0.5, 5.4), 9.0, 3.8, boxstyle="round,pad=0.15",
                                    facecolor="#fef3c7", edgecolor="#d97706", lw=1.2)
    ax5b.add_patch(box_fr)
    ax5b.text(0.8, 8.6, "12 Generator-Derived Reference Frames (2,160 Rows)",
              ha="left", va="center", fontweight="bold", color="#92400e", fontsize=8.0)
    fr_text = (
        r"• $\mathbf{Authentic\ Geometry}$: 12 frames $\times$ 180 rows = 2,160 evaluation points" + "\n" +
        r"• $\mathbf{Scaffolds}$: 30 scaffold groups/frame (6 compounds/scaffold)" + "\n" +
        r"• $\mathbf{Preserved\ Covariance}$: Retains authentic $r \approx 0.98$ collinearity & finite-frame bounds" + "\n" +
        r"• $\mathbf{Canonical\ Digest}$: SHA-256 $\mathbf{4fef2379ae33a10d089bd66794fdd21418b2b3...}$"
    )
    ax5b.text(0.8, 6.9, fr_text, ha="left", va="center", fontsize=7.2, color="#78350f", linespacing=1.35)
    
    # Metrics Box
    box_met = patches.FancyBboxPatch((0.5, 0.6), 9.0, 4.4, boxstyle="round,pad=0.15",
                                     facecolor="#f3e8ff", edgecolor="#9333ea", lw=1.2)
    ax5b.add_patch(box_met)
    ax5b.text(0.8, 4.4, "Scale-Invariant Out-of-Sample Metrics & Gates",
              ha="left", va="center", fontweight="bold", color="#6b21a8", fontsize=8.0)
    met_text = (
        r"1. $\mathbf{Valid\ Fraction}$: $\text{valid\_fraction} \geq 0.995$ ($|\mathcal{V}| \geq 2150$ positive finite points)" + "\n" +
        r"2. $\mathbf{Scale\ Alignment}$: $c^* = \frac{\sum_{\mathcal{V}} y_{\mathrm{true}, i} \cdot \hat{y}_i}{\sum_{\mathcal{V}} \hat{y}_i^2} > 0$ (Strictly positive multiplier)" + "\n" +
        r"3. $\mathbf{Relative\ RMSE}$: $\mathrm{REL\_RMSE} = \frac{\sqrt{\frac{1}{|\mathcal{V}|} \sum (c^* \hat{y}_i - y_{\mathrm{true}, i})^2}}{\sqrt{\frac{1}{|\mathcal{V}|} \sum y_{\mathrm{true}, i}^2}} \leq 0.05$ (at most 5% error)" + "\n" +
        r"4. $\mathbf{Pearson\ Correlation}$: $r \geq 0.990$ (Zero-variance rule: $r = 0.0 \rightarrow \mathrm{FAIL}$)" + "\n" +
        r"5. $\mathbf{Denominator}$: 144 Held-Out Cases (F01..F05, F08..F12, F17, F18)"
    )
    ax5b.text(0.8, 2.5, met_text, ha="left", va="center", fontsize=7.1, color="#3b0764", linespacing=1.3)

    # -------------------------------------------------------------------------
    # Panel 5C: Conceptual Metric Comparison Diagram
    # -------------------------------------------------------------------------
    ax5c = fig.add_subplot(gs[1, 0])
    ax5c.set_title("C   Predictive Fit vs Exact Algebra Distinction", loc="left", pad=10)
    
    # Diagrammatic illustration of Padé / Taylor approximation
    x_test = np.linspace(0.1, 2.0, 100)
    y_true = np.exp(0.40 * x_test / 3.0)  # Planted exponential
    y_taylor = 1.0 + 0.1333 * x_test + 0.00889 * (x_test**2)  # Polynomial approximant
    y_bad = 1.0 + 0.30 * x_test  # Distorted slope
    
    ax5c.plot(x_test, y_true, label="Planted Exponential Truth (F18)", color="#0f172a", lw=2.2)
    ax5c.plot(x_test, y_taylor, label="Polynomial Approximant (REL_RMSE < 0.01, r > 0.999)", color="#059669", lw=1.8, linestyle="--")
    ax5c.plot(x_test, y_bad, label="Under-parameterized Linear (REL_RMSE > 0.08)", color="#dc2626", lw=1.8, linestyle=":")
    
    ax5c.set_xlabel("Covariate Coordinate $d$", fontsize=8.0)
    ax5c.set_ylabel("Predicted Response Scale $\hat{g}$", fontsize=8.0)
    ax5c.grid(True, linestyle="--", alpha=0.3)
    ax5c.legend(loc="upper left", fontsize=7.2, framealpha=0.9)
    
    # Text annotation
    ax5c.text(0.95, 0.12, "Predictive Equivalence rewards accurate functional approximation\nwithout requiring exact algebraic identity (Ungated Secondary).",
              transform=ax5c.transAxes, ha="right", va="bottom", fontsize=7.0, color="#475569",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="#f8fafc", edgecolor="#cbd5e1", lw=0.6))

    # -------------------------------------------------------------------------
    # Panel 5D: Prospective Results Shell
    # -------------------------------------------------------------------------
    ax5d = fig.add_subplot(gs[1, 1])
    ax5d.set_title("D   Observed Secondary Endpoint Outcomes", loc="left", pad=10)
    ax5d.set_xlim(0, 10)
    ax5d.set_ylim(0, 10)
    ax5d.axis("off")
    
    card5d = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax5d.add_patch(card5d)
    
    box_res = patches.FancyBboxPatch((0.5, 0.5), 9.0, 8.8, boxstyle="round,pad=0.2",
                                     facecolor="#f1f5f9", edgecolor="#64748b", lw=1.4, linestyle=":")
    ax5d.add_patch(box_res)
    ax5d.text(5.0, 6.2, "[PROSPECTIVE RESULT PANEL — DO NOT RENDER]",
              ha="center", va="center", fontweight="bold", color="#b91c1c", fontsize=9.0)
    
    res_info = (
        "• Parameter Recovery Rate (Denominator: 156)\n"
        "• Mass Exponent Recovery Decomposition (Denominator: 156)\n"
        "• Descriptor Coupling Recovery Decomposition (Denominator: 84)\n"
        "• Predictive Equivalence Pass Rate (Denominator: 144)\n"
        "• Exact Algebra Recovery Rate (Denominator: 60)\n\n"
        "All prospective outcomes remain sealed until one-shot execution."
    )
    ax5d.text(5.0, 3.4, res_info, ha="center", va="center", color="#475569", fontsize=7.4, linespacing=1.3)

    fig.suptitle("FIGURE 5: Secondary Endpoint Design (Parameter Recovery & Predictive Equivalence)",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    out_svg = out_dir / "fig05_secondary_endpoints_design.svg"
    out_pdf = out_dir / "fig05_secondary_endpoints_design.pdf"
    out_png = out_dir / "fig05_secondary_endpoints_design.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 5:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
