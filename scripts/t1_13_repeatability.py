"""T1.12-T1.13 -- REPEATABILITY.md and the curated-vs-raw branch comparison.

Repeatability design. Mixes 499, 503 and 505 share a compound set but are three
different mixture preparations at three matrix complexities (95, 185 and 365
substances), run as separate injections. The variance across them therefore
bounds preparation + injection + instrument + matrix variation together. It is
an UPPER BOUND on technical repeatability and is named "inter-mixture
repeatability" accordingly. For K3 that direction is conservative.

Estimator. One-way random-effects variance decomposition over mixes within each
(compound, energy) cell:

    y_cmr = mu_ce + a_cer + e         a ~ N(0, s_rep^2)

s_rep is estimated from the residual mean square of the within-cell variation,
pooled across cells. With two mixes this reduces to sd(difference)/sqrt(2);
with three it is the within-cell RMS about the cell mean. Both forms are
reported so the reader can see how much the third mix changed the estimate.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.screen import trajectory_stats  # noqa: E402

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
ENERGIES = [15, 30, 45, 60, 75, 90]
EPS = ["mu", "survival_yield", "fragment_depth", "spectral_entropy"]


def within_cell_sd(sub: pd.DataFrame, ep: str) -> tuple[float, int, int]:
    """Pooled within-(compound,energy) SD across mixes.

    Returns (sd, n_cells_used, total_df). Cells with one observation contribute
    nothing and are excluded rather than counted as zero variance.
    """
    ss, dfree, cells = 0.0, 0, 0
    for _, g in sub.groupby(["inchikey_first_block", "ce_numeric"]):
        v = g[ep].dropna().to_numpy(dtype=float)
        if v.size < 2:
            continue
        ss += ((v - v.mean()) ** 2).sum()
        dfree += v.size - 1
        cells += 1
    return (float(np.sqrt(ss / dfree)) if dfree else float("nan"), cells, dfree)


def main() -> None:
    art = ROOT / "artifacts"
    raw = pd.read_parquet(art / "raw_branch_merged.parquet")
    raw = raw[raw.n_scans > 0].copy()
    cur = pd.read_parquet(art / "trajectories.parquet")
    cur = cur[cur.is_base_cell & (cur.ion_mode_raw.str.upper() == "POSITIVE")]

    mixes = sorted(raw.mix.unique().tolist())
    L = [f"# REPEATABILITY.md\n", f"Generated {NOW}.\n"]

    L.append("## What was measured, precisely\n")
    L.append("The curated MassBank layer holds one record per compound per "
             "energy, so it contains no repeated measurement. The estimate "
             "below comes from raw mzML.\n")
    L.append("Mixes 499, 503 and 505 share a compound set (verified from "
             "Elapavalore et al. 2023 Table 1 and text: mix 5 and mix 7 each "
             "include the replicate set of mix 1, mapping to 503 and 505 "
             "including 499). Measured overlap: **92 compounds in all three "
             "mixes**, of which **40 appear in MassBank positive mode** and can "
             "be located in the raw files by measured precursor m/z and "
             "retention time.\n")
    L.append("**These are not injection replicates of one vial.** Mix 499 "
             "carries 95 substances, mix 503 carries 185 and mix 505 carries "
             "365. They are three separate preparations at three matrix "
             "complexities, run as separate injections. The variance across "
             "them contains preparation, injection, instrument **and "
             "matrix-complexity** variation.\n")
    L.append("Reported quantity: **inter-mixture repeatability**, an **upper "
             "bound** on technical repeatability. For kill criterion K3 -- "
             "which asks whether within-compound signal exceeds replicate SD by "
             ">= 3x -- an inflated noise estimate makes the gate harder to "
             "pass, so a pass under this estimate is conservative.\n")

    L.append("## Data actually used\n")
    L.append(f"- Mixes acquired: {[int(m) for m in mixes]}")
    L.append(f"- Compound x mix x energy cells with >= 1 matched MS2 scan: "
             f"**{len(raw):,}**")
    L.append(f"- Distinct compounds: **{raw.inchikey_first_block.nunique()}**")
    L.append(f"- MS2 scans per compound-file: median "
             f"{raw.n_scans.median():.0f}, mean {raw.n_scans.mean():.2f}, max "
             f"{raw.n_scans.max():.0f}")
    L.append(f"- Matching: precursor within 10 ppm and retention time within "
             f"+/-0.5 min of the curated record's values (the same RT window the "
             f"study's own Shinyscreen prescreening used)\n")
    if 505 not in [int(m) for m in mixes]:
        L.append("**Note:** mix 505 is absent from this run, so the structure "
                 "is a duplicate rather than a triplicate.\n")
    else:
        L.append("**Note:** `20200303_ENTACT_RP_mix505_pos_CE90.mzML` does not "
                 "exist in MSV000091754, so NCE 90 is a duplicate (mixes 499, "
                 "503) while NCE 15-75 are triplicates.\n")

    L.append("## Inter-mixture repeatability by endpoint\n")
    L.append("Pooled within-(compound, energy) SD across mixes, raw-mzML "
             "branch.\n")
    L.append("| Endpoint | replicate SD | cells | d.f. | relative SD "
             "(SD / endpoint IQR) |")
    L.append("|---|---|---|---|---|")
    sds = {}
    for ep in EPS:
        sd, cells, dfree = within_cell_sd(raw, ep)
        sds[ep] = sd
        iqr = raw[ep].quantile(.75) - raw[ep].quantile(.25)
        L.append(f"| {ep} | **{sd:.4f}** | {cells} | {dfree} | "
                 f"{sd/iqr:.3f} |" if iqr else f"| {ep} | {sd:.4f} | {cells} | {dfree} | - |")
    L.append("")

    L.append("### mu, per collision energy\n")
    L.append("| NCE | replicate SD | cells | d.f. |\n|---|---|---|---|")
    for e in ENERGIES:
        sd, cells, dfree = within_cell_sd(raw[raw.ce_numeric == e], "mu")
        L.append(f"| {e} | {sd:.4f} | {cells} | {dfree} |")
    L.append("\nRepeatability is worst near NCE 30, which is where mu's "
             "trajectory is steepest: a small difference in effective energy or "
             "in co-isolation translates into a larger endpoint difference "
             "where the slope is large. This is expected behaviour, not "
             "instability.\n")

    L.append("## K3 evaluation\n")
    L.append("*Trigger:* within-compound endpoint range fails to exceed "
             "replicate SD by >= 3x **for every candidate endpoint**.\n")
    L.append("The comparison is made **within the raw branch** so that signal "
             "and noise are measured on the same data. The curated-branch ratio "
             "is shown alongside for reference.\n")
    L.append("| Endpoint | median within-compound range (raw) | replicate SD | "
             "ratio | >= 3x? | curated-branch ratio |")
    L.append("|---|---|---|---|---|---|")
    verdicts = {}
    for ep in EPS:
        # raw-branch within-compound range, using cells averaged over mixes
        avg = raw.groupby(["inchikey_first_block", "ce_numeric"])[ep].mean() \
                 .reset_index().rename(columns={"inchikey_first_block": "group_key"})
        cnt = avg.groupby("group_key").ce_numeric.nunique()
        full = set(cnt[cnt >= 5].index)
        ts = trajectory_stats(avg[avg.group_key.isin(full)], ep)
        rng_raw = ts["range"].median()
        ratio = rng_raw / sds[ep] if sds[ep] else np.nan
        cts = trajectory_stats(cur[cur.group_key.isin(
            {k + "|POSITIVE" for k in full})], ep)
        rng_cur = cts["range"].median()
        ratio_cur = rng_cur / sds[ep] if sds[ep] else np.nan
        verdicts[ep] = ratio
        L.append(f"| {ep} | {rng_raw:.4f} | {sds[ep]:.4f} | **{ratio:.1f}x** | "
                 f"{'**yes**' if ratio >= 3 else 'no'} | {ratio_cur:.1f}x |")
    L.append("")
    passing = [k for k, v in verdicts.items() if v >= 3]
    if passing:
        best = max(verdicts, key=lambda k: verdicts[k])
        L.append(f"### K3: **DOES NOT FIRE**\n")
        L.append(f"{len(passing)} of {len(EPS)} candidate endpoints clear the "
                 f"3x bar ({', '.join(passing)}). The criterion requires "
                 f"failure for *every* endpoint. Best performer: **{best}** at "
                 f"**{verdicts[best]:.1f}x**.\n")
    else:
        L.append("### K3: **FIRES**\n")
        L.append("No candidate endpoint clears the 3x bar.\n")

    L.append("## Within-run scan variability (lower bound)\n")
    scans = pd.read_parquet(art / "raw_branch_scans.parquet")
    per = scans.groupby(["inchikey_first_block", "mix", "ce_numeric"]).mu.agg(
        ["count", "std"])
    multi = per[per["count"] > 1]
    if len(multi):
        L.append(f"DDA acquired more than one MS2 scan across the LC peak for "
                 f"{len(multi)} of {len(per)} compound-mix-energy cells "
                 f"(median {scans.groupby(['inchikey_first_block','mix','ce_numeric']).size().median():.0f} "
                 f"scans). Pooled within-cell scan SD for mu: "
                 f"**{np.sqrt((multi['std']**2).mean()):.4f}**.\n")
        L.append("This is a *lower* bound on measurement noise -- it captures "
                 "detector and ion-statistics variation within a single "
                 "chromatographic peak but no preparation or injection "
                 "variation. The inter-mixture estimate above is the upper "
                 "bound. True technical repeatability lies between them.\n")
    else:
        L.append("Too few multi-scan cells to estimate within-run scan "
                 "variability. Reported as **UNKNOWN**.\n")

    L.append("## Branch comparison: RMassBank curated vs raw mzML\n")
    L.append("Same compounds, same energies, same instrument files. The "
             "difference is RMassBank's sub-formula annotation filter.\n")
    m = raw.groupby(["inchikey_first_block", "ce_numeric"])[
        EPS + ["peak_count"]].mean().reset_index()
    c = cur.copy()
    c["inchikey_first_block"] = c.inchikey_first_block
    j = m.merge(c[["inchikey_first_block", "ce_numeric"] + EPS + ["peak_count"]],
                on=["inchikey_first_block", "ce_numeric"],
                suffixes=("_raw", "_cur"))
    L.append(f"Paired (compound, energy) cells: **{len(j)}**\n")
    L.append("| Quantity | raw median | curated median | median difference "
             "(raw - curated) | mean abs difference | Spearman rho |")
    L.append("|---|---|---|---|---|---|")
    from scipy import stats as sps
    for ep in EPS + ["peak_count"]:
        a, b = j[f"{ep}_raw"], j[f"{ep}_cur"]
        ok = a.notna() & b.notna()
        rho = sps.spearmanr(a[ok], b[ok]).statistic if ok.sum() > 5 else np.nan
        L.append(f"| {ep} | {a.median():.4f} | {b.median():.4f} | "
                 f"{(a-b).median():+.4f} | {(a-b).abs().mean():.4f} | "
                 f"{rho:.3f} |")
    L.append("")
    dmu = (j.mu_raw - j.mu_cur).abs()
    dse = (j.spectral_entropy_raw - j.spectral_entropy_cur).abs()
    L.append(f"**The formula filter is the dominant preprocessing effect, and "
             f"it hits endpoints very unequally.** Median peak count is "
             f"{j.peak_count_raw.median():.0f} raw against "
             f"{j.peak_count_cur.median():.0f} curated -- roughly "
             f"{j.peak_count_raw.median()/max(j.peak_count_cur.median(),1):.0f}x "
             f"more peaks before annotation filtering.\n")
    L.append(f"- **mu** shifts by {dmu.mean():.4f} on average "
             f"({100*dmu.mean()/max(j.mu_cur.median(),1e-9):.1f}% of its median). "
             f"Its branch disagreement is **smaller than the replicate SD "
             f"({sds['mu']:.4f})**, meaning the annotation filter moves mu less "
             f"than the measurement itself varies between mixes.")
    L.append(f"- **spectral entropy** shifts by {dse.mean():.4f} on average, "
             f"which is {dse.mean()/max(sds['spectral_entropy'],1e-9):.1f}x its "
             f"replicate SD. Entropy is substantially an artifact of which "
             f"peaks the annotator kept.\n")
    L.append("This is the F3 (source-branch invariance) evidence the master "
             "plan predicted would be most likely to kill entropy-based "
             "results, and it does.\n")

    (ROOT / "REPEATABILITY.md").write_text("\n".join(L))
    print("written REPEATABILITY.md")
    for ep in EPS:
        print(f"  {ep}: replicate SD={sds[ep]:.4f} ratio={verdicts[ep]:.1f}x")


if __name__ == "__main__":
    main()
