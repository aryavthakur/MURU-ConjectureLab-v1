"""Spectrum-level tables for v2, with acquisition metadata.

v1 aggregated WUR spectra by the median over every accepted row at a
(key, energy). The WUR release ships a combined library and four
sub-libraries, and the combined file repeats sub-library spectra with the
same SpectrumId and identical bytes, so most v1 "duplicates" are archive
copies, not repeated measurements. This module keeps one row per accepted
spectrum with a content hash of its peak list and the acquisition fields
the mzVault files carry (scan filter, retention time, scan number, creation
date, operator group, curation type), so archive copies, repeated
acquisitions and different campaigns can be told apart before aggregation.

Per spectrum it computes, at the frozen base cell, mu, survival yield,
fragment depth (NaN for precursor-only spectra, never zero), the observed
to declared precursor mass ratio, and the scan-range bounds parsed from the
scan filter.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from muru import features as F
from muru.io import wur_raw
from muru.io.wur_identity import accepted_rows
from muru.io.wur_spectra import BlobDefect, assert_no_sealed_key, decode_blob
from muru.spectra import Spectrum
from muru.wur_bridge_constants import BASE_CELL, PRECURSOR_MATCH_PPM
from muru.wur_v2.exposure import assert_wur_exposed

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"

META_SQL = """
SELECT SpectrumId AS spectrum_id, ScanFilter AS scan_filter, RetentionTime AS rt_min,
       ScanNumber AS scan_number, CreationDate AS creation_date,
       InstrumentOperator AS operator, CurationType AS curation_type,
       InstrumentName AS instrument, blobMass, blobIntensity
FROM SpectrumTable WHERE SpectrumId IN ({ph})
"""
_RANGE = re.compile(r"\[([0-9.]+)-([0-9.]+)\]")


def scan_range(scan_filter: str | None) -> tuple[float, float]:
    if not scan_filter:
        return float("nan"), float("nan")
    m = _RANGE.search(scan_filter)
    return (float(m.group(1)), float(m.group(2))) if m else (float("nan"), float("nan"))


def spectrum_quantities(mz: np.ndarray, intensity: np.ndarray, precursor_mz: float) -> dict:
    """Base-cell endpoint and its exact decomposition for one peak list."""
    if mz.size == 0 or mz.size != intensity.size or intensity.sum() <= 0:
        raise BlobDefect("unusable peak list")
    order = np.argsort(mz)
    s = Spectrum(mz=mz[order], intensity=intensity[order], precursor_mz=float(precursor_mz))
    s = s.preprocess(ppm=PRECURSOR_MATCH_PPM, **BASE_CELL)
    i = s.precursor_index(PRECURSOR_MATCH_PPM)
    return {"mu": F.mu(s), "survival_yield": F.survival_yield(s, PRECURSOR_MATCH_PPM),
            "fragment_depth": F.fragment_depth(s, PRECURSOR_MATCH_PPM),
            "precursor_mass_ratio": float(s.mz[i] / s.precursor_mz) if i is not None else float("nan"),
            "precursor_found": i is not None, "n_peaks": int(s.n_peaks),
            "min_peak_mz": float(s.mz.min()), "max_peak_mz": float(s.mz.max()),
            "log_tic": float(np.log10(s.intensity.sum()))}


def peak_hash(mz: np.ndarray, intensity: np.ndarray) -> str:
    return hashlib.sha256(mz.astype("<f8").tobytes() + b"|" + intensity.astype("<f8").tobytes()).hexdigest()[:24]


def wur_pos_spectra(data_dir: Path, keys: set[str]) -> pd.DataFrame:
    """One row per accepted positive-mode WUR spectrum of `keys`, all exposed."""
    assert_wur_exposed()
    acc = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    acc = acc[acc["connectivity_key"].isin(keys)].reset_index(drop=True)
    assert_no_sealed_key(acc, allow_sealed=True)          # exposure asserted above
    rows = []
    for (lib, pf), grp in acc.groupby(["source_library", "source_polarity_file"], sort=True):
        db = data_dir / f"{wur_raw.LIBRARY_DB_FILES[(lib, pf)]}.db"
        ids = sorted(int(x) for x in grp["spectrum_id"])
        con = sqlite3.connect(str(db))
        try:
            meta = {}
            for start in range(0, len(ids), 500):
                chunk = ids[start:start + 500]
                for r in con.execute(META_SQL.format(ph=",".join("?" * len(chunk))), chunk):
                    meta[int(r[0])] = r
        finally:
            con.close()
        for r in grp.itertuples(index=False):
            m = meta[int(r.spectrum_id)]
            base = {"source_library": lib, "spectrum_id": int(r.spectrum_id),
                    "connectivity_key": r.connectivity_key, "smiles": r.smiles, "adduct": r.adduct,
                    "ce_numeric": float(r.energy), "precursor_mass": float(r.precursor_mass),
                    "scan_filter": m[1], "rt_min": m[2], "scan_number": m[3], "creation_date": m[4],
                    "operator": m[5], "curation_type": m[6], "instrument": m[7]}
            lo, hi = scan_range(m[1])
            base.update(scan_lo=lo, scan_hi=hi)
            try:
                mz, inten = decode_blob(m[8]), decode_blob(m[9])
                base["peak_hash"] = peak_hash(mz, inten)
                base.update(spectrum_quantities(mz, inten, r.precursor_mass))
                base["defect"] = ""
            except BlobDefect as exc:
                base["defect"] = str(exc)
            rows.append(base)
    return pd.DataFrame(rows)


def acquisition_id(df: pd.DataFrame) -> pd.Series:
    """Identity of a physical acquisition: peak-list hash plus scan number and date.

    Two rows with the same id are archive copies of one measurement.
    """
    # object dtype and explicit fills: under pandas 3 a missing creation date
    # would otherwise propagate NaN through the concatenation and make distinct
    # acquisitions compare equal in drop_duplicates
    def part(c):
        return df[c].astype(object).where(df[c].notna(), "").astype(str)
    return part("peak_hash") + "|" + part("scan_number") + "|" + part("creation_date")


def aggregate_cells(spec: pd.DataFrame, value_cols=("mu", "survival_yield", "fragment_depth",
                                                    "precursor_mass_ratio")) -> pd.DataFrame:
    """One value per (key, energy): archive copies collapse first, then the
    median over distinct acquisitions (v2 policy D-AGG)."""
    s = spec[spec["defect"] == ""].copy()
    s["acq_id"] = acquisition_id(s)
    distinct = s.drop_duplicates(["connectivity_key", "ce_numeric", "acq_id"])
    agg = {c: "median" for c in value_cols}
    out = distinct.groupby(["connectivity_key", "ce_numeric"]).agg(
        **{c: (c, "median") for c in value_cols},
        n_archive_rows=("spectrum_id", "size"),
        n_acquisitions=("acq_id", "nunique"),
        n_creation_dates=("creation_date", "nunique"),
        precursor_mass=("precursor_mass", "median"),
        scan_lo=("scan_lo", "median"),
        adduct=("adduct", "first")).reset_index()
    archive = s.groupby(["connectivity_key", "ce_numeric"]).size().rename("n_accepted_rows")
    return out.drop(columns="n_archive_rows").merge(archive.reset_index(), on=["connectivity_key", "ce_numeric"])


def lcsb_dev_spectra(confirmation_keys: set[str]) -> pd.DataFrame:
    """LCSB positive-mode base-cell spectra for development keys only.

    Confirmation keys are removed by key before any value column is used.
    """
    t = pd.read_parquet(ART / "trajectories.parquet")
    t = t[t["is_base_cell"] & (t["ion_mode_raw"].str.upper() == "POSITIVE")]
    t = t[~t["inchikey_first_block"].isin(confirmation_keys)]
    cols = ["accession", "inchikey_first_block", "smiles_raw", "ce_numeric", "precursor_type_raw",
            "precursor_mz", "retention_time_min", "instrument_raw", "mu", "survival_yield",
            "fragment_depth", "precursor_mass_ratio", "peak_count", "tic"]
    return t[cols].rename(columns={"inchikey_first_block": "connectivity_key"}).reset_index(drop=True)
