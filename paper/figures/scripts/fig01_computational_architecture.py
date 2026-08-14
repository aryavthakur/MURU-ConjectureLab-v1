"""Figure 1: MURU Computational Architecture.

Publication-quality schematic of the MURU computational architecture:
- Panel 1A: Energy-dependent observations and collapse hypothesis
- Panel 1B: Two-stage fold-local target estimation
- Panel 1C: Symbolic search and 8-stage truth-blind acceptance predicate
- Panel 1D: Truth barrier and downstream scoring (Primary gates G1/G2/G3 & Secondary endpoints)

No result numbers. Strictly reproducible.
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
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 300,
})

def generate_figure(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(15.5, 10.5), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.28, wspace=0.22,
                           left=0.06, right=0.96, top=0.93, bottom=0.06)
    
    # -------------------------------------------------------------------------
    # Panel 1A: The Collapse Hypothesis
    # -------------------------------------------------------------------------
    ax1a = fig.add_subplot(gs[0, 0])
    ax1a.set_title("A   The Collapse Hypothesis (Energy Scaling Model $M_0$)", loc="left", pad=10)
    
    # Generate illustrative unconditioned curves
    energies = np.linspace(15, 90, 100)
    g_values = [0.75, 0.90, 1.05, 1.25, 1.45]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]
    
    # Left subplot inside 1A: Raw trajectories
    ax1a.set_xlim(0, 10)
    ax1a.set_ylim(0, 10)
    ax1a.axis("off")
    
    # Background card for 1A
    card1a = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax1a.add_patch(card1a)
    
    # Inset 1: Raw Trajectories mu(E)
    ins_raw = ax1a.inset_axes([0.06, 0.15, 0.40, 0.68])
    for g, c in zip(g_values, colors):
        # Logistic sigmoid profile S(E/g)
        s = 1.0 / (1.0 + np.exp((energies / (g * 45.0) - 1.0) * 5.0))
        mu = 0.05 + 0.90 * s
        ins_raw.plot(energies, mu, color=c, lw=2.0, alpha=0.85)
    ins_raw.set_title(r"Raw Trajectories $\mu_i(E)$", fontsize=8.5, fontweight="bold", color="#1e293b")
    ins_raw.set_xlabel("Collision Energy $E$ (NCE)", fontsize=8)
    ins_raw.set_ylabel(r"Fragmentation Response $\mu$", fontsize=8)
    ins_raw.set_xticks([15, 30, 45, 60, 75, 90])
    ins_raw.set_ylim(0, 1.05)
    ins_raw.grid(True, linestyle="--", alpha=0.4)
    
    # Inset 2: Collapsed Profile Phi(E/g)
    ins_col = ax1a.inset_axes([0.54, 0.15, 0.40, 0.68])
    u_grid = np.linspace(0.2, 2.5, 100)
    phi = 0.05 + 0.90 / (1.0 + np.exp((u_grid - 1.0) * 5.0))
    for g, c in zip(g_values, colors):
        # Sample points collapsed onto curve
        u_sample = np.array([15, 30, 45, 60, 75, 90]) / (g * 45.0)
        mu_sample = 0.05 + 0.90 / (1.0 + np.exp((u_sample - 1.0) * 5.0))
        ins_col.scatter(u_sample, mu_sample, color=c, s=18, alpha=0.75, zorder=3)
    ins_col.plot(u_grid, phi, color="#0f172a", lw=2.2, label=r"Shared Profile $\Phi(u)$", zorder=2)
    ins_col.set_title(r"Collapsed Profile $\Phi(E / g_i)$", fontsize=8.5, fontweight="bold", color="#1e293b")
    ins_col.set_xlabel(r"Rescaled Energy $u = E / g_i$", fontsize=8)
    ins_col.set_ylabel(r"$\mu$", fontsize=8)
    ins_col.set_ylim(0, 1.05)
    ins_col.grid(True, linestyle="--", alpha=0.4)
    ins_col.legend(loc="upper right", fontsize=7.5, framealpha=0.9)
    
    # Annotation on top of 1A
    ax1a.text(5.0, 9.1, r"Hypothesis: $\mu_i(E) = A_{\mathrm{HI}} + (A_{\mathrm{LO}} - A_{\mathrm{HI}}) \cdot \Phi(E / g_i) + \epsilon_i(E)$",
              ha="center", va="center", fontsize=9.2, fontweight="bold", color="#0f172a",
              bbox=dict(boxstyle="round,pad=0.3", facecolor="#e2e8f0", edgecolor="#94a3b8", lw=0.8))

    # -------------------------------------------------------------------------
    # Panel 1B: Two-Stage Fold-Local Target Estimation
    # -------------------------------------------------------------------------
    ax1b = fig.add_subplot(gs[0, 1])
    ax1b.set_title("B   Two-Stage Fold-Local Target Estimation (Execution Boundary)", loc="left", pad=10)
    ax1b.set_xlim(0, 10)
    ax1b.set_ylim(0, 10)
    ax1b.axis("off")
    
    card1b = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax1b.add_patch(card1b)
    
    # Box 1: Training Partition (Fit shared objects)
    box_tr = patches.FancyBboxPatch((0.5, 5.2), 4.2, 3.8, boxstyle="round,pad=0.2",
                                    facecolor="#e0f2fe", edgecolor="#0284c7", lw=1.4)
    ax1b.add_patch(box_tr)
    ax1b.text(2.6, 8.4, "Stage 1: Training Set Only", ha="center", va="center",
              fontweight="bold", color="#0369a1", fontsize=8.5)
    ax1b.text(2.6, 7.8, "(20 Scaffolds / 120 Compounds)", ha="center", va="center",
              color="#075985", fontsize=7.5)
    ax1b.text(2.6, 6.5, r"• Fit shared profile $\Phi(u)$" + "\n" + r"• Centering $\overline{g}_{\mathrm{train}} = 1.0$" + "\n" + r"• Residual variance $\sigma^2$" + "\n" + "• Energy observation weights",
              ha="center", va="center", color="#0f172a", fontsize=7.8, linespacing=1.3)
    
    # Arrow to Frozen Parameters
    ax1b.annotate("", xy=(5.2, 7.1), xytext=(4.7, 7.1),
                  arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    
    # Frozen Objects box
    box_frz = patches.FancyBboxPatch((5.3, 5.2), 4.2, 3.8, boxstyle="round,pad=0.2",
                                     facecolor="#f1f5f9", edgecolor="#64748b", lw=1.4)
    ax1b.add_patch(box_frz)
    ax1b.text(7.4, 8.4, "Frozen Shared Model", ha="center", va="center",
              fontweight="bold", color="#334155", fontsize=8.5)
    ax1b.text(7.4, 7.8, r"$\Theta_{\mathrm{shared}} = (\Phi, \sigma^2, \mathbf{w})$", ha="center", va="center",
              color="#475569", fontsize=8.0)
    ax1b.text(7.4, 6.5, "• Immutable parameters\n• No transductive updates\n• Strictly fixed for\n  all downstream estimation",
              ha="center", va="center", color="#0f172a", fontsize=7.8, linespacing=1.3)
    
    # Downward arrow to Stage 2
    ax1b.annotate("", xy=(5.0, 4.4), xytext=(5.0, 5.2),
                  arrowprops=dict(arrowstyle="->", color="#475569", lw=2.0))
    
    # Box 2: Independent Compound Target Estimation
    box_est = patches.FancyBboxPatch((0.5, 0.6), 9.0, 3.6, boxstyle="round,pad=0.2",
                                     facecolor="#ecfdf5", edgecolor="#059669", lw=1.4)
    ax1b.add_patch(box_est)
    ax1b.text(5.0, 3.6, "Stage 2: Independent Fold-Local Target Estimation", ha="center", va="center",
              fontweight="bold", color="#065f46", fontsize=8.8)
    ax1b.text(5.0, 2.9, "Validation Set (5 Scaffolds / 30 Cmpds)  &  Test Set (5 Scaffolds / 30 Cmpds)",
              ha="center", va="center", color="#047857", fontsize=7.8)
    ax1b.text(5.0, 1.6, r"$\hat{g}_i = \arg\min_g \sum_{j=1}^6 w_j \left[ \mu_{i}(E_j) - \Phi(E_j / g) \right]^2$" +
              "\n" + "Each compound estimated independently; zero cross-compound or test-to-train leakage.",
              ha="center", va="center", color="#0f172a", fontsize=8.0, linespacing=1.4)

    # -------------------------------------------------------------------------
    # Panel 1C: Symbolic Search & 8-Stage Acceptance Predicate
    # -------------------------------------------------------------------------
    ax1c = fig.add_subplot(gs[1, 0])
    ax1c.set_title("C   Symbolic Regression Search & Truth-Blind Acceptance", loc="left", pad=10)
    ax1c.set_xlim(0, 10)
    ax1c.set_ylim(0, 10)
    ax1c.axis("off")
    
    card1c = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax1c.add_patch(card1c)
    
    # Input Covariates & Search engine
    box_pysr = patches.FancyBboxPatch((0.4, 5.8), 9.2, 3.6, boxstyle="round,pad=0.2",
                                      facecolor="#fef3c7", edgecolor="#d97706", lw=1.3)
    ax1c.add_patch(box_pysr)
    ax1c.text(5.0, 8.8, "Symbolic Regression Engine (PySR 1.5.10 / Frozen Grammar)",
              ha="center", va="center", fontweight="bold", color="#92400e", fontsize=8.5)
    ax1c.text(5.0, 8.0, r"Search: $\hat{g} = f(\mathrm{mass}, \mathrm{desc}, \mathrm{desc2}, \mathrm{distractor}, \mathrm{corr\_distractor})$",
              ha="center", va="center", color="#78350f", fontsize=8.0)
    ax1c.text(5.0, 6.8, r"• Target: fold-local $\hat{g}$ on training partition (120 compounds)" + "\n" +
              r"• 30 seeds per world / Pareto frontier over complexity $c \in \{1 \dots 20\}$" + "\n" +
              r"• Operators: $\{+, -, \times, /, \mathrm{pow}, \mathrm{exp}, \mathrm{sqrt}, \mathrm{abs}\}$",
              ha="center", va="center", color="#0f172a", fontsize=7.8, linespacing=1.3)
    
    # Acceptance Predicate Pipeline (8 gates)
    ax1c.text(5.0, 5.2, "8-Stage Ordered Truth-Blind Structural Acceptance Predicate",
              ha="center", va="center", fontweight="bold", color="#1e293b", fontsize=8.5)
    
    gates = [
        r"1. Adequacy ($M_0$ not rejected)",
        r"2. Null-Calibrated Fit ($R^2_{\mathrm{val}} > T(c)$)",
        r"3. Seed Stability ($\geq 20/30$)",
        r"4. Complexity ($c \leq 20$)",
        r"5. Invalid Fraction ($\leq 0.005$)",
        r"6. Effective Support ($\neq \emptyset$)",
        r"7. GBDT Ceiling ($\geq 0.80$ / waiver)",
        r"8. Falsification Harness (F1..F10)"
    ]
    
    for i, g in enumerate(gates):
        col = 0 if i < 4 else 1
        row = i % 4
        x = 0.5 if col == 0 else 5.2
        y = 4.3 - row * 0.95
        w = 4.3
        h = 0.75
        box_g = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                       facecolor="#ffffff", edgecolor="#94a3b8", lw=0.9)
        ax1c.add_patch(box_g)
        ax1c.text(x + w/2.0, y + h/2.0, g, ha="center", va="center",
                  fontsize=7.2, color="#0f172a")

    # -------------------------------------------------------------------------
    # Panel 1D: Downstream Truth-Gated Scoring
    # -------------------------------------------------------------------------
    ax1d = fig.add_subplot(gs[1, 1])
    ax1d.set_title("D   Truth Barrier & Downstream Endpoint Scoring", loc="left", pad=10)
    ax1d.set_xlim(0, 10)
    ax1d.set_ylim(0, 10)
    ax1d.axis("off")
    
    card1d = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax1d.add_patch(card1d)
    
    # Truth Barrier Banner
    barr = patches.FancyBboxPatch((0.4, 8.3), 9.2, 1.1, boxstyle="round,pad=0.15",
                                  facecolor="#fee2e2", edgecolor="#ef4444", lw=1.4, linestyle="--")
    ax1d.add_patch(barr)
    ax1d.text(5.0, 8.85, "STRICT TRUTH BARRIER: Planted truth uninspected during search & acceptance",
              ha="center", va="center", fontweight="bold", color="#b91c1c", fontsize=7.8)
    
    # Primary Gates Box
    box_g123 = patches.FancyBboxPatch((0.4, 4.3), 9.2, 3.7, boxstyle="round,pad=0.2",
                                      facecolor="#eff6ff", edgecolor="#3b82f6", lw=1.3)
    ax1d.add_patch(box_g123)
    ax1d.text(5.0, 7.5, "Primary Benchmark Gates (Governing Claims)", ha="center", va="center",
              fontweight="bold", color="#1d4ed8", fontsize=8.5)
    
    g_items = [
        r"$\mathbf{G1}$ Scalar Competence: $r_s \geq 0.80 \ \mathrm{and}\ \mathrm{MAE} \leq 0.80 \times \mathrm{base} \ \mathrm{and}\ M_0\ \mathrm{valid}$ (Denom: 164)",
        r"$\mathbf{G2}$ Family Recovery: $\mathrm{support\_status} == \mathrm{MATCH} \ \mathrm{and}\ \mathrm{family\_status} == \mathrm{MATCH}$ (Denom: 144)",
        r"$\mathbf{G3}$ Principal Structural Safety: Unsafe structural acceptance rate $\leq 0.15$ (Denom: 36)"
    ]
    for idx, item in enumerate(g_items):
        ax1d.text(5.0, 6.7 - idx * 0.9, item, ha="center", va="center",
                  fontsize=7.3, color="#1e293b", bbox=dict(boxstyle="square,pad=0.2", facecolor="#ffffff", edgecolor="#bfdbfe", lw=0.6))
        
    # Secondary Endpoints Box
    box_sec = patches.FancyBboxPatch((0.4, 0.5), 9.2, 3.5, boxstyle="round,pad=0.2",
                                     facecolor="#f3e8ff", edgecolor="#a855f7", lw=1.3)
    ax1d.add_patch(box_sec)
    ax1d.text(5.0, 3.6, "Secondary Endpoints (Descriptive / Ungated)", ha="center", va="center",
              fontweight="bold", color="#7e22ce", fontsize=8.5)
    
    sec_items = [
        r"• $\mathbf{Parameter\ Recovery}$: $p_{\mathrm{mass}} \pm 0.15$ and $c_{\mathrm{desc}} \pm 0.10$ at anchor $\mathbf{x}_0 = (250, 0, 0, 0, 0)$ (Denom: 156)",
        r"• $\mathbf{Predictive\ Equivalence}$: $\mathrm{REL\_RMSE} \leq 0.05 \ \mathrm{and}\ r \geq 0.990$ over 12 ref frames (2,160 rows) (Denom: 144)",
        r"• $\mathbf{Exact\ Algebra\ Recovery}$: Symbolic equivalence to planted law (Denom: 60)"
    ]
    for idx, item in enumerate(sec_items):
        ax1d.text(0.7, 2.9 - idx * 0.85, item, ha="left", va="center",
                  fontsize=7.3, color="#0f172a")
        
    fig.suptitle("FIGURE 1: MURU Computational Architecture and Governance Boundary",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    # Save outputs
    out_svg = out_dir / "fig01_computational_architecture.svg"
    out_pdf = out_dir / "fig01_computational_architecture.pdf"
    out_png = out_dir / "fig01_computational_architecture.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 1:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
