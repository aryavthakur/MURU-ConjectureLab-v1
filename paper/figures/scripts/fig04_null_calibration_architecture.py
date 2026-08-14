"""Figure 4: Null-Calibration Architecture and Monotonic Threshold Protocol.

Publication-quality calibration architecture diagram:
- Panel 4A: Why complexity-indexed empirical thresholding is required (diagrammatic unscaled concept)
- Panel 4B: 100 Structural-null worlds & 34/33/33 allocation under A3.2 18/6/6 scaffold split
- Panel 4C: A3.2 Global base-target permutation mechanism vs rejected provisional design
- Panel 4D: Threshold table protocol & prospective shell [PROSPECTIVE RESULT PANEL — DO NOT RENDER]

No observed calibration threshold values rendered. Strictly reproducible design schematic.
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
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.15], hspace=0.28, wspace=0.22,
                           left=0.06, right=0.96, top=0.94, bottom=0.05)
    
    # -------------------------------------------------------------------------
    # Panel 4A: Rationale for Complexity-Indexed Null Calibration
    # -------------------------------------------------------------------------
    ax4a = fig.add_subplot(gs[0, 0])
    ax4a.set_title("A   Rationale for Complexity-Indexed Empirical Thresholding", loc="left", pad=10)
    ax4a.set_xlim(0, 10)
    ax4a.set_ylim(0, 10)
    ax4a.axis("off")
    
    card4a = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax4a.add_patch(card4a)
    
    # Diagrammatic unscaled inset
    ins4a = ax4a.inset_axes([0.08, 0.15, 0.84, 0.65])
    c_dummy = np.linspace(1, 20, 20)
    # Conceptual unscaled curve showing rising search capacity
    ins4a.plot(c_dummy, 0.10 + 0.35 * (1 - np.exp(-c_dummy / 6.0)), color="#0284c7", lw=2.2, label="Null Search Capacity (Multiplicity)")
    ins4a.axhline(0.20, color="#dc2626", linestyle="--", lw=1.5, label="Constant Arbitrary Threshold (Uncalibrated)")
    ins4a.plot(c_dummy, 0.12 + 0.38 * (1 - np.exp(-c_dummy / 6.0)), color="#059669", lw=2.0, linestyle="-.", label="Empirical $Q_{95}$ Monotonic Gate $T(c)$")
    
    ins4a.set_title("Conceptual Search Multiplicity vs Complexity", fontsize=8.0, fontweight="bold")
    ins4a.set_xlabel("Candidate Expression Complexity $c \in \{1 \dots 20\}$", fontsize=7.8)
    ins4a.set_ylabel("Validation $R^2$ (Unscaled Conceptual Axis)", fontsize=7.8)
    ins4a.set_xticks([1, 5, 10, 15, 20])
    ins4a.set_yticks([])
    ins4a.grid(True, linestyle="--", alpha=0.3)
    ins4a.legend(loc="upper left", fontsize=7.0, framealpha=0.9)
    
    ax4a.text(5.0, 9.1, "Search algorithms always return candidate expressions; threshold must match search capacity at complexity c.",
              ha="center", va="center", fontsize=7.6, color="#0f172a")

    # -------------------------------------------------------------------------
    # Panel 4B: 100 Structural-Null Worlds Allocation & Geometry
    # -------------------------------------------------------------------------
    ax4b = fig.add_subplot(gs[0, 1])
    ax4b.set_title("B   100 Structural-Null Worlds Protocol (Amendments A3.1 & A3.2)", loc="left", pad=10)
    ax4b.set_xlim(0, 10)
    ax4b.set_ylim(0, 10)
    ax4b.axis("off")
    
    card4b = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax4b.add_patch(card4b)
    
    # 3 Construction Cards
    consts = [
        ("target_permuted_across_compounds", "34 Worlds (Index 0..33)",
         "Global compound index permutation of target values", "#eff6ff", "#3b82f6", "#1d4ed8"),
        ("descriptors_permuted_across_compounds", "33 Worlds (Index 34..66)",
         "Global permutation of 5 covariate rows", "#ecfdf5", "#059669", "#065f46"),
        ("gaussian_targets_with_observed_variance", "33 Worlds (Index 67..99)",
         "Gaussian synthetic target matching observed scale", "#fef3c7", "#d97706", "#92400e"),
    ]
    
    for i, (name, count, desc, bg, edge, tc) in enumerate(consts):
        y = 6.4 - i * 2.1
        box = patches.FancyBboxPatch((0.5, y), 9.0, 1.8, boxstyle="round,pad=0.15",
                                     facecolor=bg, edgecolor=edge, lw=1.2)
        ax4b.add_patch(box)
        ax4b.text(0.8, y + 1.25, name, ha="left", va="center",
                  fontweight="bold", color=tc, fontsize=7.8)
        ax4b.text(9.2, y + 1.25, count, ha="right", va="center",
                  fontweight="bold", color=tc, fontsize=7.6)
        ax4b.text(0.8, y + 0.55, desc, ha="left", va="center",
                  color="#1e293b", fontsize=7.0)
        
    # Bottom specs
    box_spec = patches.FancyBboxPatch((0.5, 0.5), 9.0, 1.4, boxstyle="round,pad=0.1",
                                      facecolor="#ffffff", edgecolor="#94a3b8", lw=1.0)
    ax4b.add_patch(box_spec)
    ax4b.text(5.0, 1.2, "Calibration Split: 18 / 6 / 6 Scaffolds = 108 / 36 / 36 Compounds  |  30 Seeds / World (3,000 Total)",
              ha="center", va="center", fontweight="bold", color="#334155", fontsize=7.5)

    # -------------------------------------------------------------------------
    # Panel 4C: A3.2 Base Target Permutation Mechanism
    # -------------------------------------------------------------------------
    ax4c = fig.add_subplot(gs[1, 0])
    ax4c.set_title("C   Amendment A3.2 Base-Target Repair (Destroying Scaffold Leakage)", loc="left", pad=10)
    ax4c.set_xlim(0, 10)
    ax4c.set_ylim(0, 10)
    ax4c.axis("off")
    
    card4c = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax4c.add_patch(card4c)
    
    # Rejected Provisional Design Box
    box_rej = patches.FancyBboxPatch((0.5, 5.2), 9.0, 4.0, boxstyle="round,pad=0.15",
                                     facecolor="#fee2e2", edgecolor="#ef4444", lw=1.3)
    ax4c.add_patch(box_rej)
    ax4c.text(0.8, 8.6, "Rejected Provisional Design (Scaffold Confounding)",
              ha="left", va="center", fontweight="bold", color="#b91c1c", fontsize=8.0)
    ax4c.text(0.8, 7.0, "• Evaluated frozen law on unpermuted scaffolds → target inherited scaffold latent\n• Permuting only covariates left target scaffold structure intact\n• Produced train/val mean shifts across scaffold-disjoint splits\n• Biased constant-model validation $R^2$ down to -0.246 (min -1.28)",
              ha="left", va="center", color="#7f1d1d", fontsize=7.2, linespacing=1.3)
    
    # Corrected A3.2 Design Box
    box_cor = patches.FancyBboxPatch((0.5, 0.6), 9.0, 4.2, boxstyle="round,pad=0.15",
                                     facecolor="#ecfdf5", edgecolor="#059669", lw=1.3)
    ax4c.add_patch(box_cor)
    ax4c.text(0.8, 4.2, "Corrected A3.2 Design: Global Compound Index Permutation",
              ha="left", va="center", fontweight="bold", color="#065f46", fontsize=8.0)
    ax4c.text(0.8, 2.4, "• Evaluates frozen law once, then globally permutes across all 180 compounds\n• Dedicated seed namespace: PB|NCAL|<world_id>|BASE_TARGET\n• Preserves exact marginal distribution bitwise while destroying scaffold assignment\n• Applied before split assignment (18/6/6 scaffolds) and before null transformation\n• Restores clean constant-model validation $R^2 \\approx -0.033$",
              ha="left", va="center", color="#064e3b", fontsize=7.2, linespacing=1.3)

    # -------------------------------------------------------------------------
    # Panel 4D: Threshold Construction Protocol & Prospective Result Shell
    # -------------------------------------------------------------------------
    ax4d = fig.add_subplot(gs[1, 1])
    ax4d.set_title("D   Threshold Construction Protocol & Calibration Shell", loc="left", pad=10)
    ax4d.set_xlim(0, 10)
    ax4d.set_ylim(0, 10)
    ax4d.axis("off")
    
    card4d = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax4d.add_patch(card4d)
    
    # Mathematical Formula Box
    box_math = patches.FancyBboxPatch((0.5, 6.2), 9.0, 3.2, boxstyle="round,pad=0.15",
                                      facecolor="#ffffff", edgecolor="#3b82f6", lw=1.2)
    ax4d.add_patch(box_math)
    ax4d.text(5.0, 8.8, "Mathematical Threshold Accumulation Protocol",
              ha="center", va="center", fontweight="bold", color="#1d4ed8", fontsize=8.0)
    
    proto_text = (
        r"$\mathbf{1.\ World\ Statistic}$: $S(w, c) = \max_{s \in 1..30} R^2_{\mathrm{val}}(w, s, \leq c)$" + "\n" +
        r"$\mathbf{2.\ Empirical\ Quantile}$: $Q_{0.95}(c) = \mathrm{numpy.quantile}(\{S(w, c)\}_{w=1}^{100}, 0.95, \mathrm{method='linear'})$" + "\n" +
        r"$\mathbf{3.\ Monotonic\ Gate}$: $T(c) = \max_{1 \leq k \leq c} Q_{0.95}(k) = \mathrm{cummax}(Q_{0.95})$" + "\n" +
        r"$\mathbf{4.\ Bootstrap\ Band}$: 2,000 world-level resamples at seed 20260812 (reporting only)"
    )
    ax4d.text(0.7, 7.3, proto_text, ha="left", va="center", fontsize=7.0, color="#0f172a", linespacing=1.35)
    
    # Shell Placeholder Box
    box_shell = patches.FancyBboxPatch((0.5, 0.6), 9.0, 5.2, boxstyle="round,pad=0.2",
                                       facecolor="#f1f5f9", edgecolor="#64748b", lw=1.4, linestyle=":")
    ax4d.add_patch(box_shell)
    ax4d.text(5.0, 3.8, "[PROSPECTIVE RESULT PANEL — DO NOT RENDER]",
              ha="center", va="center", fontweight="bold", color="#b91c1c", fontsize=9.0)
    ax4d.text(5.0, 2.4, "Observed threshold table $T(c)$ and 2,000-resample bootstrap band\nremain strictly unrendered to prevent outcome visualization prior to formal unsealing.\nThreshold table is frozen upon calibration run completion.",
              ha="center", va="center", color="#475569", fontsize=7.2, linespacing=1.3)

    fig.suptitle("FIGURE 4: Null-Calibration Protocol, Construction Hierarchy, and Monotonic Threshold Design",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    out_svg = out_dir / "fig04_null_calibration_architecture.svg"
    out_pdf = out_dir / "fig04_null_calibration_architecture.pdf"
    out_png = out_dir / "fig04_null_calibration_architecture.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 4:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
