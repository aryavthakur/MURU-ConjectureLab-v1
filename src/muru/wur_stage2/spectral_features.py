"""Extended per-spectrum summaries for Stage 2B, defined before any use.

The frozen endpoint is `features.mu`. Stage 2A showed a single shared shape
with one scale per compound is inadequate on real spectra, so Stage 2B asks
whether mu discards information that a compact summary would keep. The set
below was fixed from the literature review (survival yield / CE50, spectral
entropy, precursor survival, fragment-mass distribution) before any Stage 2B
model was fitted. All are computed at the base preprocessing cell through
the same `Spectrum` path the corpus uses, on both corpora with the same code.

Nothing here reads a sealed or held-out spectrum: the WUR table builder
passes the holdout as `forbidden` and the seal guard runs before any blob.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from muru import features as F
from muru.io.massbank import parse_file
from muru.io.wur_raw import LIBRARY_DB_FILES
from muru.io.wur_spectra import (
    BlobDefect, assert_no_sealed_key, read_spectrum_peaks_censused,
)
from muru.spectra import Spectrum, spectrum_from_record
from muru.wur_bridge_constants import BASE_CELL, PRECURSOR_MATCH_PPM

ROOT = Path(__file__).resolve().parents[3]
LCSB_DIR = ROOT / "data" / "massbank" / "MassBank-data" / "LCSB"

FEATURE_NAMES = (
    "mu", "survival_yield", "fragment_depth", "spectral_entropy",
    "normalized_entropy", "peak_count", "base_peak_fraction",
    "x_wsd", "x_wq25", "x_wq50", "x_wq75",
    "frac_x_lt_025", "frac_x_025_050", "frac_x_050_075", "frac_x_ge_075",
    "n_peaks_1pct", "log_tic",
)


def _weighted_quantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    order = np.argsort(x)
    x, w = x[order], w[order]
    c = np.cumsum(w) / w.sum()
    return float(np.interp(q, c, x))


def spectrum_features(s: Spectrum) -> dict[str, float]:
    """The a-priori feature set for one base-cell spectrum."""
    s = s.preprocess(ppm=PRECURSOR_MATCH_PPM, **BASE_CELL)
    out = {"mu": F.mu(s), "survival_yield": F.survival_yield(s),
           "fragment_depth": F.fragment_depth(s),
           "spectral_entropy": F.spectral_entropy(s),
           "normalized_entropy": F.normalized_entropy(s),
           "peak_count": float(F.peak_count(s)),
           "base_peak_fraction": F.base_peak_fraction(s)}
    if s.n_peaks == 0 or s.intensity.sum() <= 0 or not s.precursor_mz:
        for k in FEATURE_NAMES:
            out.setdefault(k, float("nan"))
        return out
    x = s.mz / s.precursor_mz
    w = s.intensity / s.intensity.sum()
    m = float((w * x).sum())
    out["x_wsd"] = float(np.sqrt(max(0.0, (w * (x - m) ** 2).sum())))
    out["x_wq25"] = _weighted_quantile(x, w, 0.25)
    out["x_wq50"] = _weighted_quantile(x, w, 0.50)
    out["x_wq75"] = _weighted_quantile(x, w, 0.75)
    out["frac_x_lt_025"] = float(w[x < 0.25].sum())
    out["frac_x_025_050"] = float(w[(x >= 0.25) & (x < 0.5)].sum())
    out["frac_x_050_075"] = float(w[(x >= 0.5) & (x < 0.75)].sum())
    out["frac_x_ge_075"] = float(w[x >= 0.75].sum())
    out["n_peaks_1pct"] = float((s.intensity >= 0.01 * s.intensity.max()).sum())
    out["log_tic"] = float(np.log10(s.intensity.sum()))
    return out


# ------------------------------------------------------------------ WUR --
def wur_feature_table(accepted: pd.DataFrame, data_dir: Path,
                      forbidden: set[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Per-(key, energy) median of every feature over the accepted spectra."""
    assert_no_sealed_key(accepted, forbidden=forbidden)
    census, rows = [], []
    for (library, pf), grp in accepted.groupby(["source_library", "source_polarity_file"],
                                               sort=True, dropna=False):
        db_path = data_dir / f"{LIBRARY_DB_FILES[(library, pf)]}.db"
        peaks, defects = read_spectrum_peaks_censused(db_path, grp["spectrum_id"])
        for d in defects:
            census.append({"spectrum_id": d["spectrum_id"], "reason": d["reason"]})
        for r in grp.itertuples(index=False):
            sid = int(r.spectrum_id)
            if sid not in peaks:
                continue
            mz, inten = peaks[sid]
            try:
                if mz.size == 0 or inten.sum() <= 0:
                    raise BlobDefect("empty or zero spectrum")
                order = np.argsort(mz)
                s = Spectrum(mz=mz[order], intensity=inten[order],
                             precursor_mz=float(r.precursor_mass))
                f = spectrum_features(s)
            except (BlobDefect, ValueError) as exc:
                census.append({"spectrum_id": sid, "reason": str(exc)})
                continue
            rows.append({"connectivity_key": r.connectivity_key,
                         "ce_numeric": float(r.energy), "spectrum_id": sid, **f})
    per = pd.DataFrame(rows)
    agg = per.groupby(["connectivity_key", "ce_numeric"])[list(FEATURE_NAMES)].median()
    agg["n_spectra"] = per.groupby(["connectivity_key", "ce_numeric"]).size()
    agg["source"] = "WUR"
    return agg.reset_index(), census


# ----------------------------------------------------------------- LCSB --
def lcsb_feature_table(keys: set[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Per-(key, energy) mean over the base-cell accessions the corpus used.

    The LCSB corpus aggregates duplicate accessions by the mean, so the same
    aggregator is used here for consistency with `p2_dev_corpus.mu`.
    """
    traj = pd.read_parquet(ROOT / "artifacts" / "trajectories.parquet")
    base = traj[traj["is_base_cell"] & (traj["ion_mode_raw"].str.upper() == "POSITIVE")
                & traj["inchikey_first_block"].isin(keys)]
    census, rows = [], []
    for r in base[["accession", "inchikey_first_block", "ce_numeric"]].drop_duplicates().itertuples(index=False):
        path = LCSB_DIR / f"{r.accession}.txt"
        if not path.exists():
            census.append({"accession": r.accession, "reason": "record file missing"})
            continue
        try:
            s = spectrum_from_record(parse_file(path))
            f = spectrum_features(s)
        except Exception as exc:
            census.append({"accession": r.accession, "reason": repr(exc)})
            continue
        rows.append({"connectivity_key": r.inchikey_first_block,
                     "ce_numeric": float(r.ce_numeric), "accession": r.accession, **f})
    per = pd.DataFrame(rows)
    agg = per.groupby(["connectivity_key", "ce_numeric"])[list(FEATURE_NAMES)].mean()
    agg["n_spectra"] = per.groupby(["connectivity_key", "ce_numeric"]).size()
    agg["source"] = "LCSB"
    return agg.reset_index(), census
