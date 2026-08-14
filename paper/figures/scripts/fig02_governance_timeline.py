"""Figure 2: Prospective-Governance Timeline and Execution Seals.

Publication-quality governance timeline diagram:
- Panel 2A: Complete governance and amendment sequence from Historical (Class A) through Amendments A1-A3.4 to Executable Freeze and Evaluation
- Panel 2B: Partition seal states across project lifecycle (Held-out and Confirmation sealed)
- Panel 2C: Amendment lineage and temporal relationships to calibration and unsealing

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
    "figure.dpi": 300,
})

def generate_figure(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(16.0, 10.8), constrained_layout=False)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.3, 0.95, 0.85], hspace=0.32,
                           left=0.06, right=0.96, top=0.93, bottom=0.06)
    
    # -------------------------------------------------------------------------
    # Panel 2A: Complete Governance & Amendment Sequence
    # -------------------------------------------------------------------------
    ax2a = fig.add_subplot(gs[0, 0])
    ax2a.set_title("A   Chronological Governance Sequence (Historical Class A  →  Frozen Methods Class B  →  Prospective Results Class C)", loc="left", pad=10)
    ax2a.set_xlim(0, 100)
    ax2a.set_ylim(0, 10)
    ax2a.axis("off")
    
    card2a = patches.FancyBboxPatch((0.5, 0.2), 99.0, 9.6, boxstyle="round,pad=0.3",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax2a.add_patch(card2a)
    
    # Stage Blocks definitions
    stages = [
        # x, y, w, h, title, subtitle, commit/status, color_bg, color_edge, text_color
        (2.0, 1.2, 14.0, 7.5, "1. Historical\nDevelopment", "Phase 1 / 2 / 3\nType 2 Validation\nEngine Audit", "CLASS A\nObserved\nSTOP P4", "#f1f5f9", "#64748b", "#334155"),
        (18.0, 1.2, 11.5, 7.5, "2. Content\nFreeze V1", "380 Cases\n20 Families\n80/240/60 Split", "commit d94d2c9\nFROZEN\n2026-08-13", "#eff6ff", "#3b82f6", "#1d4ed8"),
        (31.5, 1.2, 27.5, 7.5, "3. Prospective Amendments (A1 – A3.4)", "A1 Adequacy (2ac86c5) • A2/A2.1 F16 Repair (03cc4d3)\nA3.1 G2/G3 Contract (c8938e8) • A3.2 Null Target (1194fcb)\nA3.3 Secondary (71f5369) • A3.4 Ref Frames (be23b80)\nA3.4 Temporal Erratum (220c9cb)", "CLASS B\nALL FROZEN\nOutcome-Blind", "#ecfdf5", "#059669", "#065f46"),
        (61.0, 1.2, 11.5, 7.5, "4. Null\nCalibration", "100 Worlds\n30 Seeds / World\n3,000 Searches", "CLASS C\nThreshold Freeze\nPending Scoring", "#fef3c7", "#d97706", "#92400e"),
        (74.5, 1.2, 11.5, 7.5, "5. Executable\nFreeze & Dev", "RC4 Production Path\n80 Dev Cases\nSanity Verification", "CLASS C\nCode Sealed\nPending Rerun", "#fef3c7", "#d97706", "#92400e"),
        (88.0, 1.2, 10.5, 7.5, "6. Held-out &\nChallenge", "240 Held-out (G1-G3)\n60 Challenge Stress\nOptional Ext. Valid.", "CLASS C\nSEALED\nUnopened", "#fee2e2", "#ef4444", "#b91c1c"),
    ]
    
    for x, y, w, h, title, subtitle, status, bg, edge, tc in stages:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                     facecolor=bg, edgecolor=edge, lw=1.4)
        ax2a.add_patch(box)
        ax2a.text(x + w/2.0, y + h - 1.2, title, ha="center", va="top",
                  fontweight="bold", color=tc, fontsize=8.2)
        ax2a.text(x + w/2.0, y + h/2.0 - 0.2, subtitle, ha="center", va="center",
                  color="#1e293b", fontsize=7.0, linespacing=1.2)
        ax2a.text(x + w/2.0, y + 1.1, status, ha="center", va="bottom",
                  fontweight="bold", color=tc, fontsize=6.8, linespacing=1.1)
        
    # Connecting Arrows
    arrow_xs = [16.2, 29.7, 59.2, 72.7, 86.2]
    for ax_x in arrow_xs:
        ax2a.annotate("", xy=(ax_x + 1.6, 5.0), xytext=(ax_x, 5.0),
                      arrowprops=dict(arrowstyle="->", color="#475569", lw=2.2))

    # -------------------------------------------------------------------------
    # Panel 2B: Partition Seal State Tracker
    # -------------------------------------------------------------------------
    ax2b = fig.add_subplot(gs[1, 0])
    ax2b.set_title("B   Partition Seal State & Execution Boundaries", loc="left", pad=10)
    ax2b.set_xlim(0, 100)
    ax2b.set_ylim(0, 10)
    ax2b.axis("off")
    
    card2b = patches.FancyBboxPatch((0.5, 0.2), 99.0, 9.6, boxstyle="round,pad=0.3",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax2b.add_patch(card2b)
    
    # 4 Partition cards
    parts = [
        (2.0, 1.0, 22.0, 8.0, "Calibration Worlds\n(100 Worlds × 30 Seeds)",
         "• 34 target_permuted\n• 33 descriptors_permuted\n• 33 gaussian_targets\n• 18/6/6 Scaffold split",
         "Status: IN PROGRESS / UNINSPECTED\nNo threshold values exposed", "#fef9c3", "#ca8a04", "#854d0e"),
        
        (26.5, 1.0, 22.0, 8.0, "Development Partition\n(80 Cases = 4 / Family)",
         "• 20 Truth Families\n• Scaffold 20/5/5 split\n• Sanity checks & smoke tests\n• Cannot alter contracts",
         "Status: SEALED / NOT OPENED\nPending rerun under A3.4", "#e0e7ff", "#4f46e5", "#3730a3"),
        
        (51.0, 1.0, 22.0, 8.0, "Held-Out Partition\n(240 Cases = 12 / Family)",
         "• Primary Gates: G1, G2, G3\n• Secondary: Param, Pred Equiv\n• Denominators: 164, 144, 36, 156\n• One-shot evaluation only",
         "Status: STRICTLY SEALED\nSHA-256 Hashed Manifest", "#fee2e2", "#dc2626", "#991b1b"),
        
        (75.5, 1.0, 22.5, 8.0, "Confirmation & External\n(110 Cmpds / Real Spectra)",
         "• Real MassBank / MASSIVE data\n• 82 Scaffold groups\n• Phase 4 Qualification\n• Real-data confirmation",
         "Status: STRICTLY SEALED\nSHA-256 d6b6b1358597...\nSTOP BEFORE PHASE 4", "#f1f5f9", "#475569", "#1e293b"),
    ]
    
    for x, y, w, h, title, bullets, status, bg, edge, tc in parts:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                     facecolor=bg, edgecolor=edge, lw=1.3)
        ax2b.add_patch(box)
        ax2b.text(x + w/2.0, y + h - 0.8, title, ha="center", va="top",
                  fontweight="bold", color=tc, fontsize=7.8)
        ax2b.text(x + 1.2, y + h/2.0 + 0.2, bullets, ha="left", va="center",
                  color="#1e293b", fontsize=7.0, linespacing=1.25)
        ax2b.text(x + w/2.0, y + 0.6, status, ha="center", va="bottom",
                  fontweight="bold", color=tc, fontsize=6.8, linespacing=1.1)

    # -------------------------------------------------------------------------
    # Panel 2C: Governance Amendment Lineage
    # -------------------------------------------------------------------------
    ax2c = fig.add_subplot(gs[2, 0])
    ax2c.set_title("C   Prospective Amendment Lineage & Temporal Governance Integrity", loc="left", pad=10)
    ax2c.set_xlim(0, 100)
    ax2c.set_ylim(0, 10)
    ax2c.axis("off")
    
    card2c = patches.FancyBboxPatch((0.5, 0.2), 99.0, 9.6, boxstyle="round,pad=0.3",
                                    facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2)
    ax2c.add_patch(card2c)
    
    amends = [
        ("V1 Freeze", "d94d2c9", "Base benchmark design & 380 cases", "2026-08-13"),
        ("A1 Adequacy", "2ac86c5", "Binds M0/M1/M2/M3 decision rules", "2026-08-13"),
        ("A2 / A2.1", "03cc4d3", "Repairs F16 generator & version bump", "2026-08-14"),
        ("A3.1 G2/G3", "c8938e8", "G2/G3 contract & calibration protocol", "2026-08-14"),
        ("A3.2 Null Base", "1194fcb", "Global base target permutation", "2026-08-14"),
        ("A3.3 Secondary", "71f5369", "Parameter recovery & pred equivalence", "2026-08-14"),
        ("A3.4 Ref Frames", "be23b80", "12 generator frames (2,160 rows)", "2026-08-14"),
        ("A3.4 Erratum", "220c9cb", "Temporal provenance & audit sync", "2026-08-14"),
    ]
    
    step_w = 11.5
    for i, (name, commit, desc, date) in enumerate(amends):
        x = 1.5 + i * 12.2
        y = 1.2
        w = 11.2
        h = 7.6
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                     facecolor="#ffffff", edgecolor="#0ea5e9", lw=1.1)
        ax2c.add_patch(box)
        ax2c.text(x + w/2.0, y + h - 0.7, name, ha="center", va="top",
                  fontweight="bold", color="#0369a1", fontsize=7.5)
        ax2c.text(x + w/2.0, y + h - 2.2, f"commit {commit[:7]}", ha="center", va="top",
                  fontfamily="monospace", color="#64748b", fontsize=6.8)
        ax2c.text(x + w/2.0, y + h/2.0 - 0.5, desc, ha="center", va="center",
                  color="#1e293b", fontsize=6.6, wrap=True)
        ax2c.text(x + w/2.0, y + 0.6, date, ha="center", va="bottom",
                  color="#94a3b8", fontsize=6.5)
        
        if i < len(amends) - 1:
            ax2c.annotate("", xy=(x + w + 0.9, y + h/2.0), xytext=(x + w + 0.1, y + h/2.0),
                          arrowprops=dict(arrowstyle="->", color="#0ea5e9", lw=1.5))

    fig.suptitle("FIGURE 2: Prospective-Governance Timeline, Partition Seals, and Amendment Lineage",
                 fontsize=11, fontweight="bold", color="#0f172a", y=0.98)
    
    out_svg = out_dir / "fig02_governance_timeline.svg"
    out_pdf = out_dir / "fig02_governance_timeline.pdf"
    out_png = out_dir / "fig02_governance_timeline.png"
    
    fig.savefig(out_svg, format="svg", bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    return {"svg": out_svg, "pdf": out_pdf, "png": out_png}

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[1] / "pre_results"
    paths = generate_figure(out_dir)
    print(f"Generated Figure 2:\n  {paths['svg']}\n  {paths['pdf']}\n  {paths['png']}")
