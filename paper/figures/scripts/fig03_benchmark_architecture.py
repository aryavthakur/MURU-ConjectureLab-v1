"""Figure 3: Synthetic Benchmark Architecture and Truth-Family Taxonomy.

Publication-quality benchmark architecture diagram:
- Panel 3A: 20 Case families map, grouped by scientific test category & partition allocations (80 Dev, 240 Held-out, 60 Challenge = 380 total)
- Panel 3B: Within-case geometry (180 compounds, 30 scaffolds, 20/5/5 scaffold-disjoint train/val/test split, 6 energy grid)
- Panel 3C: 5 Truth-Family Taxonomy mathematical curves & functional relationships
- Panel 3D: Adequacy deviation models (M0 vs M1, M2, M3 standalone and F16 combined) & Covariate correlation structure

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
    
    fig = plt.figure(figsize=(16.0, 11.5), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1.1], hspace=0.26, wspace=0.22,
                           left=0.06, right=0.96, top=0.94, bottom=0.05)
    
    # -------------------------------------------------------------------------
    # Panel 3A: 20 Case Families Map & Partition Hierarchy
    # -------------------------------------------------------------------------
    ax3a = fig.add_subplot(gs[0, 0])
    ax3a.set_title("A   Case Family Taxonomy (20 Families × 3 Partitions = 380 Cases)", loc="left", pad=10)
    ax3a.set_xlim(0, 10)
    ax3a.set_ylim(0, 10)
    ax3a.axis("off")
    
    card3a = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax3a.add_patch(card3a)
    
    # Summary banner on top
    ax3a.text(5.0, 9.3, "Total Benchmark: 380 Cases  |  80 Development (4/fam)  |  240 Held-Out (12/fam)  |  60 Challenge (3/fam)",
              ha="center", va="center", fontsize=8.0, fontweight="bold", color="#0f172a",
              bbox=dict(boxstyle="round,pad=0.25", facecolor="#e2e8f0", edgecolor="#94a3b8", lw=0.8))
    
    # Grid of 20 families
    # Categories:
    # 1. Scalar Collapse & Noise: F01-F05 (Blue)
    # 2. Descriptor & Symbolic: F07-F12, F17, F18 (Green)
    # 3. Adequacy Violations: F06, F13-F16 (Orange/Red)
    # 4. Null & Adversarial: F19, F20 (Purple)
    
    fam_data = [
        ("F01", "Noiseless M0", "Blue", 0, 0),
        ("F02", "Mod Noise M0", "Blue", 0, 1),
        ("F03", "Strong Noise", "Blue", 0, 2),
        ("F04", "Missing Energy", "Blue", 0, 3),
        ("F05", "Boundary Scale", "Blue", 0, 4),
        
        ("F06", "Null Scalar (M1)", "Orange", 1, 0),
        ("F07", "Mass-Only g", "Green", 1, 1),
        ("F08", "Linear Desc", "Green", 1, 2),
        ("F09", "Saturating Desc", "Green", 1, 3),
        ("F10", "Interaction Law", "Green", 1, 4),
        
        ("F11", "Irrelevant Dist", "Green", 2, 0),
        ("F12", "Correlated Dist", "Green", 2, 1),
        ("F13", "M1 Violation", "Orange", 2, 2),
        ("F14", "M2 High Floor", "Orange", 2, 3),
        ("F15", "M3 Low Ceiling", "Orange", 2, 4),
        
        ("F16", "M1+M2+M3 Comb", "Orange", 3, 0),
        ("F17", "Equivalent Form", "Green", 3, 1),
        ("F18", "Exponential Law", "Green", 3, 2),
        ("F19", "Null Targets (A-C)", "Purple", 3, 3),
        ("F20", "Adversarial (A-C)", "Purple", 3, 4),
    ]
    
    color_map = {
        "Blue": ("#dbeafe", "#2563eb", "#1e40af"),
        "Green": ("#dcfce7", "#16a34a", "#166534"),
        "Orange": ("#ffedd5", "#ea580c", "#9a3412"),
        "Purple": ("#f3e8ff", "#9333ea", "#6b21a8"),
    }
    
    for fid, name, cat, row, col in fam_data:
        x = 0.45 + col * 1.85
        y = 7.1 - row * 1.8
        w = 1.75
        h = 1.55
        bg, edge, tc = color_map[cat]
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                     facecolor=bg, edgecolor=edge, lw=1.1)
        ax3a.add_patch(box)
        ax3a.text(x + w/2.0, y + h - 0.35, fid, ha="center", va="center",
                  fontweight="bold", color=tc, fontsize=8.0)
        ax3a.text(x + w/2.0, y + 0.75, name, ha="center", va="center",
                  color="#1e293b", fontsize=6.6, wrap=True)
        ax3a.text(x + w/2.0, y + 0.28, "4 Dev | 12 Held | 3 Ch", ha="center", va="center",
                  color="#64748b", fontsize=5.8)

    # -------------------------------------------------------------------------
    # Panel 3B: Within-Case Partition Geometry & Data Structure
    # -------------------------------------------------------------------------
    ax3b = fig.add_subplot(gs[0, 1])
    ax3b.set_title("B   Within-Case Geometry (180 Compounds in 30 Scaffold Groups)", loc="left", pad=10)
    ax3b.set_xlim(0, 10)
    ax3b.set_ylim(0, 10)
    ax3b.axis("off")
    
    card3b = patches.FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.2",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax3b.add_patch(card3b)
    
    # 30 Scaffolds representation
    ax3b.text(5.0, 9.2, "Disjoint Scaffold Group Partitioning (6 Compounds / Scaffold)",
              ha="center", va="center", fontweight="bold", color="#1e293b", fontsize=8.5)
    
    # Training Box (20 scaffolds = 120 compounds)
    box_train = patches.FancyBboxPatch((0.4, 4.8), 5.7, 3.8, boxstyle="round,pad=0.15",
                                       facecolor="#eff6ff", edgecolor="#3b82f6", lw=1.3)
    ax3b.add_patch(box_train)
    ax3b.text(3.25, 8.1, "Training Partition (20 Scaffolds / 120 Cmpds)",
              ha="center", va="center", fontweight="bold", color="#1d4ed8", fontsize=8.0)
    ax3b.text(3.25, 7.3, "Scaffolds S001 – S020", ha="center", va="center",
              color="#2563eb", fontsize=7.2)
    ax3b.text(3.25, 6.0, "• Shared profile $\Phi(u)$ fit\n• Symbolic search $\hat{g} = f(\mathbf{x})$\n• Centering & variance fitting\n• 6 collision energies per cmpd",
              ha="center", va="center", color="#0f172a", fontsize=7.5, linespacing=1.3)
    
    # Validation Box (5 scaffolds = 30 compounds)
    box_val = patches.FancyBboxPatch((6.4, 6.8), 3.2, 1.8, boxstyle="round,pad=0.15",
                                     facecolor="#fef3c7", edgecolor="#d97706", lw=1.3)
    ax3b.add_patch(box_val)
    ax3b.text(8.0, 8.2, "Validation Set (5 Scaffolds)", ha="center", va="center",
              fontweight="bold", color="#92400e", fontsize=7.8)
    ax3b.text(8.0, 7.4, "S021 – S025 (30 Cmpds)\nNull fit & Pareto selection",
              ha="center", va="center", color="#0f172a", fontsize=6.8, linespacing=1.2)
    
    # Test Box (5 scaffolds = 30 compounds)
    box_test = patches.FancyBboxPatch((6.4, 4.8), 3.2, 1.8, boxstyle="round,pad=0.15",
                                      facecolor="#ecfdf5", edgecolor="#059669", lw=1.3)
    ax3b.add_patch(box_test)
    ax3b.text(8.0, 6.2, "Test Set (5 Scaffolds)", ha="center", va="center",
              fontweight="bold", color="#065f46", fontsize=7.8)
    ax3b.text(8.0, 5.4, "S026 – S030 (30 Cmpds)\nAdequacy & GBDT ceiling",
              ha="center", va="center", color="#0f172a", fontsize=6.8, linespacing=1.2)
    
    # Feature Vector Box on Bottom
    box_feats = patches.FancyBboxPatch((0.4, 0.5), 9.2, 3.8, boxstyle="round,pad=0.2",
                                       facecolor="#ffffff", edgecolor="#94a3b8", lw=1.2)
    ax3b.add_patch(box_feats)
    ax3b.text(5.0, 3.8, "Five Primitive Benchmark Covariates & Energy Grid",
              ha="center", va="center", fontweight="bold", color="#334155", fontsize=8.2)
    
    cov_text = (
        r"$\mathbf{1.\ mass}$: Precursor mass $m \in [100, 800]$ Da (log-uniform scaffold distribution)" + "\n" +
        r"$\mathbf{2.\ descriptor}$: Active continuous molecular descriptor $d \in [-2.5, +2.5]$" + "\n" +
        r"$\mathbf{3.\ descriptor2}$: Secondary descriptor $d_2 \in [-2.5, +2.5]$ (for interaction family F10)" + "\n" +
        r"$\mathbf{4.\ distractor}$: Independent orthogonal Gaussian noise $z \sim \mathcal{N}(0, 1)$" + "\n" +
        r"$\mathbf{5.\ correlated\_distractor}$: Collinear nuisance variable $z_{\mathrm{corr}} = 0.85 d + 0.15 \epsilon$" + "\n" +
        r"$\mathbf{Energy\ Grid}$: Collision energy $E \in \{15, 30, 45, 60, 75, 90\}$ NCE (6 points)"
    )
    ax3b.text(0.7, 2.1, cov_text, ha="left", va="center", fontsize=7.2, color="#0f172a", linespacing=1.35)

    # -------------------------------------------------------------------------
    # Panel 3C: Five Truth Families Mathematical Relationships
    # -------------------------------------------------------------------------
    ax3c = fig.add_subplot(gs[1, 0])
    ax3c.set_title("C   Five Truth-Family Taxonomy Functional Forms", loc="left", pad=10)
    
    desc_vals = np.linspace(-2.0, 2.0, 100)
    mass_fixed = 250.0
    c0 = 1.0
    c1 = 0.40
    
    # 1. mass_affine_descriptor: g = c0 * sqrt(m/250) * (1 + c1 * d)
    g_affine = c0 * np.sqrt(mass_fixed / 250.0) * (1.0 + c1 * desc_vals)
    # 2. mass_saturating_descriptor: g = c0 * sqrt(m/250) * (1 + c1 * d / (1 + |d|))
    g_sat = c0 * np.sqrt(mass_fixed / 250.0) * (1.0 + c1 * desc_vals / (1.0 + np.abs(desc_vals)))
    # 3. mass_exponential_descriptor: g = c0 * sqrt(m/250) * exp(c1 * d / 3)
    g_exp = c0 * np.sqrt(mass_fixed / 250.0) * np.exp(c1 * desc_vals / 3.0)
    # 4. mass_power (varying mass at d=0):
    m_vals = np.linspace(100, 800, 100)
    g_pow = (m_vals / 250.0) ** 0.50
    
    ax3c.plot(desc_vals, g_affine, label=r"1. Affine: $g = c_0 \sqrt{m/250}(1 + c_1 d)$", color="#1f77b4", lw=2.0)
    ax3c.plot(desc_vals, g_sat, label=r"3. Saturating: $g = c_0 \sqrt{m/250}\left(1 + c_1 \frac{d}{1+|d|}\right)$", color="#ff7f0e", lw=2.0)
    ax3c.plot(desc_vals, g_exp, label=r"5. Exponential: $g = c_0 \sqrt{m/250} \exp(c_1 d / 3)$", color="#2ca02c", lw=2.0)
    
    ax3c.set_xlabel("Descriptor Value $d$", fontsize=8.5)
    ax3c.set_ylabel(r"Scale Factor $g$", fontsize=8.5)
    ax3c.set_xlim(-2.0, 2.0)
    ax3c.set_ylim(0.2, 2.0)
    ax3c.grid(True, linestyle="--", alpha=0.4)
    ax3c.legend(loc="upper left", fontsize=7.5, framealpha=0.9)
    
    # Inset for mass_power and mass_interaction
    ins3c = ax3c.inset_axes([0.62, 0.12, 0.35, 0.40])
    ins3c.plot(m_vals, g_pow, color="#9467bd", lw=1.8, label=r"2. Power: $(m/250)^p$")
    ins3c.set_title("Mass Power Scaling", fontsize=7.2, fontweight="bold")
    ins3c.set_xlabel("$m$ (Da)", fontsize=6.8)
    ins3c.set_ylabel("$g$", fontsize=6.8)
    ins3c.grid(True, linestyle="--", alpha=0.3)
    ins3c.legend(fontsize=6.5)

    # -------------------------------------------------------------------------
    # Panel 3D: Adequacy Deviation Models M1, M2, M3 & F16
    # -------------------------------------------------------------------------
    ax3d = fig.add_subplot(gs[1, 1])
    ax3d.set_title("D   Adequacy Violation Models (M0 vs M1, M2, M3 Standalone & F16 Combined)", loc="left", pad=10)
    
    e_grid = np.linspace(15, 90, 100)
    # M0 Base
    s_base = 1.0 / (1.0 + np.exp((e_grid / 45.0 - 1.0) * 5.0))
    mu_m0 = 0.05 + 0.90 * s_base
    
    # M1 Horizontal shape violation (amplitude 0.45): slope modification
    s_m1 = 1.0 / (1.0 + np.exp((e_grid / 45.0 - 1.0) * 1.5))
    mu_m1 = 0.05 + 0.90 * s_m1
    
    # M2 High-energy floor (amplitude 0.18): elevates upper baseline
    mu_m2 = np.maximum(mu_m0, 0.22)
    
    # M3 Low-energy ceiling (amplitude 0.22): clips lower baseline
    mu_m3 = np.minimum(mu_m0, 0.75)
    
    ax3d.plot(e_grid, mu_m0, label="M0: True Scalar Collapse", color="#0f172a", lw=2.2)
    ax3d.plot(e_grid, mu_m1, label="M1: Horizontal Shape Violation (Amp 0.45)", color="#dc2626", lw=1.8, linestyle="--")
    ax3d.plot(e_grid, mu_m2, label="M2: High-Energy Floor (Amp 0.18)", color="#ea580c", lw=1.8, linestyle="-.")
    ax3d.plot(e_grid, mu_m3, label="M3: Low-Energy Ceiling (Amp 0.22)", color="#9333ea", lw=1.8, linestyle=":")
    
    ax3d.set_xlabel("Collision Energy $E$ (NCE)", fontsize=8.5)
    ax3d.set_ylabel(r"Fragmentation Response $\mu(E)$", fontsize=8.5)
    ax3d.set_xticks([15, 30, 45, 60, 75, 90])
    ax3d.set_ylim(0, 1.05)
    ax3d.grid(True, linestyle="--", alpha=0.4)
    ax3d.legend(loc="upper right", fontsize=7.3, framealpha=0.9)
    
    # Annotation for F16
    ax3d.text(35, 0.12, "F16 Combined Violation:\n• M1 Amp = 0.15 (1/3)\n• M2 Amp = 0.05 (5/18)\n• M3 Amp = 11/180 (A2 Repair)",
              fontsize=7.2, color="#7f1d1d",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="#fee2e2", edgecolor="#ef4444", lw=0.8))
    
    fig.suptitle("FIGURE 3: Synthetic Benchmark Case Families, Partition Geometry, and Truth Taxonomy",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    out_svg = out_dir / "fig03_benchmark_architecture.svg"
    out_pdf = out_dir / "fig03_benchmark_architecture.pdf"
    out_png = out_dir / "fig03_benchmark_architecture.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 3:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
