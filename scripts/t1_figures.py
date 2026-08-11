"""Phase 1 figures. Four plots, each answering a question in the decision.

No decoration beyond what makes the numbers legible.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.screen import spearman_by_energy, trajectory_stats  # noqa: E402

FIG = ROOT / "artifacts" / "figures"
ENERGIES = [15, 30, 45, 60, 75, 90]


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(ROOT / "artifacts" / "trajectories.parquet")
    df["log_tic"] = np.log10(df.tic.replace(0, np.nan))
    base = df[df.is_base_cell]
    pos = base[base.ion_mode_raw.str.upper() == "POSITIVE"]
    cnt = pos.groupby("group_key").ce_numeric.nunique()
    bf = pos[pos.group_key.isin(set(cnt[cnt == 6].index))]

    # 1. Endpoint trajectories -------------------------------------------
    eps = ["mu", "survival_yield", "fragment_depth", "spectral_entropy"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    for ax, ep in zip(axes, eps):
        for _, g in list(bf.groupby("group_key"))[:250]:
            g = g.sort_values("ce_numeric")
            ax.plot(g.ce_numeric, g[ep], color="0.75", lw=0.4, alpha=0.5)
        q = bf.groupby("ce_numeric")[ep].quantile([.25, .5, .75]).unstack()
        ax.fill_between(q.index, q[.25], q[.75], color="tab:blue", alpha=0.25)
        ax.plot(q.index, q[.5], color="tab:blue", lw=2.5, marker="o")
        ax.set_title(ep); ax.set_xlabel("NCE"); ax.set_xticks(ENERGIES)
    axes[0].set_ylabel("endpoint value")
    fig.suptitle(f"Phase 1 endpoint trajectories, positive mode, "
                 f"{bf.group_key.nunique()} complete six-energy compounds "
                 f"(grey: 250 individual trajectories; blue: median and IQR)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "endpoint_trajectories.png", dpi=140)
    plt.close(fig)

    # 2. Monotonicity ------------------------------------------------------
    names = eps + ["normalized_entropy", "base_peak_fraction", "peak_count"]
    strict = [100 * trajectory_stats(bf, e).monotone_strict.mean() for e in names]
    fig, ax = plt.subplots(figsize=(8, 4))
    order = np.argsort(strict)[::-1]
    ax.barh([names[i] for i in order], [strict[i] for i in order],
            color=["tab:green" if strict[i] >= 70 else "tab:red" for i in order])
    ax.axvline(70, ls="--", color="k", lw=1)
    ax.text(70.8, -0.4, "70% acceptance bar", fontsize=8)
    ax.set_xlabel("% of trajectories strictly monotone in collision energy")
    ax.invert_yaxis()
    fig.tight_layout(); fig.savefig(FIG / "monotonicity.png", dpi=140)
    plt.close(fig)

    # 3. Confounders -------------------------------------------------------
    covs = ["log_tic", "precursor_mz", "peak_count", "retention_time_min"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.4), sharey=True)
    for ax, ep in zip(axes, eps):
        for c in covs:
            s = spearman_by_energy(bf, ep, c).set_index("energy")
            ax.plot(ENERGIES, [s.rho.get(e, np.nan) for e in ENERGIES],
                    marker="o", label=c)
        ax.axhline(0, color="k", lw=0.8); ax.set_ylim(-1, 1)
        ax.set_title(ep); ax.set_xlabel("NCE"); ax.set_xticks(ENERGIES)
    axes[0].set_ylabel("Spearman rho"); axes[-1].legend(fontsize=7)
    fig.suptitle("Confounder associations by collision energy", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "confounders.png", dpi=140)
    plt.close(fig)

    # 4. Branch comparison -------------------------------------------------
    rp = ROOT / "artifacts" / "raw_branch_merged.parquet"
    if rp.exists():
        raw = pd.read_parquet(rp)
        raw = raw[raw.n_scans > 0]
        m = raw.groupby(["inchikey_first_block", "ce_numeric"])[
            eps + ["peak_count"]].mean().reset_index()
        j = m.merge(pos[["inchikey_first_block", "ce_numeric"] + eps + ["peak_count"]],
                    on=["inchikey_first_block", "ce_numeric"],
                    suffixes=("_raw", "_cur"))
        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        for ax, ep in zip(axes, ["mu", "spectral_entropy", "peak_count"]):
            ax.scatter(j[f"{ep}_cur"], j[f"{ep}_raw"], s=12, alpha=0.5)
            lo = min(j[f"{ep}_cur"].min(), j[f"{ep}_raw"].min())
            hi = max(j[f"{ep}_cur"].max(), j[f"{ep}_raw"].max())
            ax.plot([lo, hi], [lo, hi], "k--", lw=1)
            ax.set_xlabel(f"{ep} — RMassBank curated")
            ax.set_ylabel(f"{ep} — raw mzML")
            ax.set_title(ep)
        fig.suptitle("Preprocessing branch comparison (identity line dashed): "
                     "mu is unaffected, entropy and peak count are not",
                     fontsize=10)
        fig.tight_layout(); fig.savefig(FIG / "branch_comparison.png", dpi=140)
        plt.close(fig)

    print(f"figures written to {FIG.relative_to(ROOT)}: "
          f"{sorted(p.name for p in FIG.glob('*.png'))}")


if __name__ == "__main__":
    main()
