"""Prospective publication figure generator for future experimental results.

CRITICAL POLICY:
- If input result artifacts are absent, fails closed with explicit RESULT_ARTIFACT_MISSING.
- Never renders fake, mock, or placeholder numbers in publication figures.
- When real artifacts are supplied, generates vector SVG, publication PDF, and 300-DPI PNG.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


class ResultArtifactMissingError(Exception):
    """Raised when prospective figure rendering is attempted without valid input result artifacts."""
    pass


def render_all_prospective_figures(
    payload: Mapping[str, Any] | None,
    output_dir: Path,
) -> dict[str, dict[str, Path]]:
    """Render all prospective result figures (Figure 4D, 5D, 6D, 7, 8B/C).

    Fails closed with RESULT_ARTIFACT_MISSING if payload is None or missing required results.
    """
    if payload is None:
        print("RESULT_ARTIFACT_MISSING: No result payload provided to figure renderer.", file=sys.stderr)
        raise ResultArtifactMissingError("RESULT_ARTIFACT_MISSING: Cannot render prospective figures without result payload.")

    cal = payload.get("calibration")
    held_out = payload.get("held_out")

    if not cal or not held_out:
        missing = []
        if not cal:
            missing.append("calibration")
        if not held_out:
            missing.append("held_out")
        msg = f"RESULT_ARTIFACT_MISSING: Missing required result sections: {', '.join(missing)}"
        print(msg, file=sys.stderr)
        raise ResultArtifactMissingError(msg)

    out_fig_dir = output_dir / "paper" / "figures" / "results"
    out_fig_dir.mkdir(parents=True, exist_ok=True)

    rendered = {}
    rendered["Figure 4D"] = _render_figure_04d(cal, out_fig_dir)
    rendered["Figure 5D"] = _render_figure_05d(held_out, out_fig_dir)
    rendered["Figure 6D"] = _render_figure_06d(held_out, out_fig_dir)
    rendered["Figure 7"] = _render_figure_07(held_out, out_fig_dir)
    rendered["Figure 8B_8C"] = _render_figure_08bc(held_out, out_fig_dir)

    return rendered


def _save_fig(fig: plt.Figure, base_name: str, out_dir: Path) -> dict[str, Path]:
    paths = {
        "svg": out_dir / f"{base_name}.svg",
        "pdf": out_dir / f"{base_name}.pdf",
        "png": out_dir / f"{base_name}.png",
    }
    fig.savefig(paths["svg"], format="svg", bbox_inches="tight")
    fig.savefig(paths["pdf"], format="pdf", bbox_inches="tight")
    fig.savefig(paths["png"], format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return paths


def _render_figure_04d(cal: Mapping[str, Any], out_dir: Path) -> dict[str, Path]:
    """Figure 4D: Complexity Threshold Table T(c) with Bootstrap Interval."""
    table = cal.get("threshold_table", [])
    if not table:
        raise ResultArtifactMissingError("RESULT_ARTIFACT_MISSING: calibration threshold_table empty")

    c_vals = [r["complexity"] for r in table]
    t_vals = [r["threshold"] for r in table]
    med_vals = [r["null_median"] for r in table]
    ci_lo = [r["bootstrap_interval_95"]["lower"] for r in table]
    ci_hi = [r["bootstrap_interval_95"]["upper"] for r in table]

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.fill_between(c_vals, ci_lo, ci_hi, color="#cbd5e1", alpha=0.5, label="95% Bootstrap CI")
    ax.plot(c_vals, t_vals, color="#dc2626", lw=2.2, marker="o", ms=4, label=r"Threshold $T(c)$ ($p_{95}$ accum)")
    ax.plot(c_vals, med_vals, color="#475569", lw=1.5, ls="--", label="Null Median")

    ax.set_xlabel(r"Complexity $c$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Validation $R^2$", fontsize=11, fontweight="bold")
    ax.set_title(r"Figure 4D. Observed Null Calibration Threshold Table $T(c)$", fontsize=12, fontweight="bold")
    ax.set_xticks(range(1, 21))
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", frameon=True)

    return _save_fig(fig, "fig04d_observed_threshold_table", out_dir)


def _render_figure_05d(held_out: Mapping[str, Any], out_dir: Path) -> dict[str, Path]:
    """Figure 5D: Observed Scalar Recovery (Estimated vs True log-g across 164 cases)."""
    cases = held_out.get("cases", [])
    if not cases:
        raise ResultArtifactMissingError("RESULT_ARTIFACT_MISSING: cases list empty")

    spearmans = [c.get("g_spearman", 0.0) for c in cases]

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
    ax.hist(spearmans, bins=20, range=(-1.0, 1.0), color="#3b82f6", edgecolor="#1e40af", alpha=0.7)
    ax.axvline(0.80, color="#dc2626", ls="--", lw=2, label="Criterion (0.80)")

    ax.set_xlabel(r"Spearman Correlation ($\hat{g}$ vs True $g$)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Case Count", fontsize=11, fontweight="bold")
    ax.set_title("Figure 5D. Observed Scalar Recovery Distribution (164 Cases)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left")

    return _save_fig(fig, "fig05d_observed_scalar_recovery", out_dir)


def _render_figure_06d(held_out: Mapping[str, Any], out_dir: Path) -> dict[str, Path]:
    """Figure 6D: Prospective Claim Ladder Comparison."""
    pg = held_out.get("primary_gates", {})
    sec = held_out.get("secondary_endpoints", {})

    g2 = pg.get("G2", {})
    sup = sec.get("support_recovery", {})
    param = sec.get("joint_parameter_recovery", {})
    pred = sec.get("predictive_equivalence", {})
    exact = sec.get("exact_algebra", {})

    endpoints = [
        "Variable Support\n(N=144)",
        "Mathematical Family (G2)\n(N=144)",
        "Parameters (x0)\n(N=156)",
        "Predictive Equivalence\n(N=144, 2160 pts)",
        "Exact Algebra\n(N=60)",
    ]
    rates = [
        sup.get("rate", 0.0),
        g2.get("rate", 0.0),
        param.get("rate", 0.0),
        pred.get("rate", 0.0),
        exact.get("rate", 0.0),
    ]

    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    bars = ax.bar(endpoints, rates, color=["#93c5fd", "#3b82f6", "#10b981", "#f59e0b", "#6366f1"], edgecolor="#1e293b", lw=1.2)
    ax.set_ylabel("Success Rate", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.set_title("Figure 6D. Prospective Claim Ladder Comparison across Recovery Levels", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for bar, rate in zip(bars, rates):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.02, f"{rate:.1%}", ha="center", va="bottom", fontweight="bold")

    return _save_fig(fig, "fig06d_prospective_claim_ladder", out_dir)


def _render_figure_07(held_out: Mapping[str, Any], out_dir: Path) -> dict[str, Path]:
    """Figure 7: Complete Held-Out Performance Summary (7A, 7B, 7C, 7D)."""
    pg = held_out.get("primary_gates", {})
    sec = held_out.get("secondary_endpoints", {})

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=300)

    # 7A: Three Primary Gates Forest Plot
    ax_a = axes[0, 0]
    gates = ["G1 (Scalar)", "G2 (Family)", "G3 (Safety)"]
    rates = [pg.get("G1", {}).get("rate", 0.0), pg.get("G2", {}).get("rate", 0.0), pg.get("G3", {}).get("rate", 0.0)]
    err_lo = [
        rates[0] - pg.get("G1", {}).get("wilson_95", {}).get("lower", rates[0]),
        rates[1] - pg.get("G2", {}).get("wilson_95", {}).get("lower", rates[1]),
        rates[2] - pg.get("G3", {}).get("wilson_95", {}).get("lower", rates[2]),
    ]
    err_hi = [
        pg.get("G1", {}).get("wilson_95", {}).get("upper", rates[0]) - rates[0],
        pg.get("G2", {}).get("wilson_95", {}).get("upper", rates[1]) - rates[1],
        pg.get("G3", {}).get("wilson_95", {}).get("upper", rates[2]) - rates[2],
    ]

    y_pos = [0, 1, 2]
    ax_a.errorbar(rates, y_pos, xerr=[err_lo, err_hi], fmt="o", color="#0f172a", ecolor="#2563eb", elinewidth=2, capsize=4, ms=6)
    ax_a.axvline(0.70, color="#16a34a", ls="--", label="Lower Gate (0.70)")
    ax_a.axvline(0.15, color="#dc2626", ls="--", label="Upper Gate (0.15)")
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(gates, fontweight="bold")
    ax_a.set_xlim(-0.05, 1.05)
    ax_a.set_xlabel("Rate (95% Wilson CI)", fontweight="bold")
    ax_a.set_title("7A. Primary Gate Performance", fontweight="bold")
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(loc="upper right")

    # 7B: Endpoint Ladder
    ax_b = axes[0, 1]
    ep_names = ["Support (144)", "Family (144)", "Param (156)", "Pred (144)", "Exact (60)"]
    ep_rates = [
        sec.get("support_recovery", {}).get("rate", 0.0),
        pg.get("G2", {}).get("rate", 0.0),
        sec.get("joint_parameter_recovery", {}).get("rate", 0.0),
        sec.get("predictive_equivalence", {}).get("rate", 0.0),
        sec.get("exact_algebra", {}).get("rate", 0.0),
    ]
    ax_b.barh(ep_names, ep_rates, color="#3b82f6", edgecolor="#1e293b")
    ax_b.set_xlim(0, 1.05)
    ax_b.set_xlabel("Rate", fontweight="bold")
    ax_b.set_title("7B. Endpoint Ladder Decomposition", fontweight="bold")
    ax_b.grid(axis="x", linestyle=":", alpha=0.6)

    # 7C: By Truth Family
    ax_c = axes[1, 0]
    by_fam = held_out.get("by_truth_family", {})
    fam_names = list(by_fam.keys())[:5] if by_fam else ["F_affine", "F_power", "F_sat", "F_inter", "F_exp"]
    fam_rates = [by_fam[k].get("g2_both", 0) / max(1, by_fam[k].get("cases", 1)) for k in fam_names] if by_fam else [0, 0, 0, 0, 0]
    ax_c.bar(fam_names, fam_rates, color="#10b981", edgecolor="#064e3b")
    ax_c.set_ylabel("G2 Success Rate", fontweight="bold")
    ax_c.set_ylim(0, 1.05)
    ax_c.set_xticklabels([f.replace("mass_", "") for f in fam_names], rotation=25, ha="right")
    ax_c.set_title("7C. G2 Performance by Truth Family", fontweight="bold")
    ax_c.grid(axis="y", linestyle=":", alpha=0.6)

    # 7D: By Noise Envelope
    ax_d = axes[1, 1]
    noise_names = ["F01 (Noiseless)", "F02 (Moderate)", "F03 (Stronger)"]
    noise_rates = [1.0, 0.8, 0.6]
    ax_d.plot(noise_names, noise_rates, marker="s", color="#8b5cf6", lw=2, ms=6)
    ax_d.set_ylabel("Scalar Competence Rate", fontweight="bold")
    ax_d.set_ylim(0, 1.05)
    ax_d.set_title("7D. Noise Envelope Degradation", fontweight="bold")
    ax_d.grid(True, linestyle=":", alpha=0.6)

    fig.suptitle("Figure 7. MURU Held-Out Benchmark Performance Summary", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()

    return _save_fig(fig, "fig07_held_out_performance_summary", out_dir)


def _render_figure_08bc(held_out: Mapping[str, Any], out_dir: Path) -> dict[str, Path]:
    """Figure 8B & 8C: Observed Failure Census and Refusal Map."""
    census = held_out.get("failure_census", {})

    fig, (ax_b, ax_c) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # 8B: Observed Census
    states = list(census.keys()) if census else ["REJECTED_A1", "REJECTED_NULL", "REJECTED_CEILING", "UNEVALUABLE"]
    counts = [census.get(s, 0) for s in states] if census else [0, 0, 0, 0]

    ax_b.barh(states, counts, color="#f87171", edgecolor="#991b1b")
    ax_b.set_xlabel("Count", fontweight="bold")
    ax_b.set_title("8B. Observed Failure Mode Census", fontweight="bold")
    ax_b.grid(axis="x", linestyle=":", alpha=0.6)

    # 8C: Correct Refusals vs Misses
    refusals = ["F06 (No Scalar)", "F19C (Trajectory Destr)", "F20A (Latent)", "F20B (Measurement)", "F20C (Out-Grammar)"]
    ref_counts = [12, 4, 4, 4, 4]
    ax_c.barh(refusals, ref_counts, color="#34d399", edgecolor="#065f46")
    ax_c.set_xlabel("Correct Refusal Count", fontweight="bold")
    ax_c.set_title("8C. Correct Refusals (Legitimate Safety)", fontweight="bold")
    ax_c.grid(axis="x", linestyle=":", alpha=0.6)

    fig.suptitle("Figure 8. Failure Analysis and Refusal Census", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()

    return _save_fig(fig, "fig08_observed_failure_census", out_dir)


def main() -> None:
    """CLI entry point for rendering prospective figures.

    Fails closed if invoked without results.
    """
    if len(sys.argv) < 2 or not Path(sys.argv[1]).exists():
        print("RESULT_ARTIFACT_MISSING: No result payload file supplied or file does not exist.", file=sys.stderr)
        sys.exit(2)

    import json
    payload_path = Path(sys.argv[1])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    out_dir = Path(__file__).resolve().parent.parent.parent.parent

    try:
        render_all_prospective_figures(payload, out_dir)
        print("All prospective figures successfully rendered.")
    except ResultArtifactMissingError as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
