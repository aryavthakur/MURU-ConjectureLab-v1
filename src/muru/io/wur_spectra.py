"""Peak-level reader for the WUR release, and the Stage 1 mu builder.

Stage 0 read header columns only. This module reads `blobMass` and
`blobIntensity` for spectra that Stage 0 already ACCEPTED, and never
selects spectra on its own: it is handed an accepted-row table from
`wur_identity.accepted_rows` so that a rejected UVPD, off-ladder,
wrong-polarity or wrong-adduct spectrum cannot re-enter here.

Both blobs are little-endian float64 arrays of equal length. Anything else
is a defect and is raised or censused, never silently dropped.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from muru.features import mu as feature_mu
from muru.io.wur_raw import LIBRARY_DB_FILES
from muru.spectra import Spectrum
from muru.wur_bridge_constants import BASE_CELL, PRECURSOR_MATCH_PPM


class BlobDefect(ValueError):
    """A peak blob that cannot be read as a valid peak list."""


def decode_blob(blob) -> np.ndarray:
    """A little-endian float64 array from an mzVault peak blob.

    The array is a copy, not a view over the original bytes, so it is
    writable. This is deliberate: the next stage sorts or scales these
    arrays in place.
    """
    if blob is None:
        return _fail("missing blob")
    if len(blob) == 0:
        return _fail("empty blob")
    if len(blob) % 8 != 0:
        return _fail(f"blob length {len(blob)} is not a multiple of 8")
    return np.frombuffer(bytes(blob), dtype="<f8").copy()


def _fail(message: str):
    raise BlobDefect(message)


def read_spectrum_peaks(db_path: Path,
                        spectrum_ids) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Peak arrays for the requested SpectrumIds in one mzVault file.

    SpectrumId is unique per file, not across the release, so the caller
    must group its accepted rows by source file before calling this.
    """
    try:
        wanted = sorted({int(s) for s in spectrum_ids})
    except (TypeError, ValueError) as exc:
        raise BlobDefect(f"non-integer spectrum id in {spectrum_ids!r}: {exc}")
    if not wanted:
        return {}
    con = sqlite3.connect(str(db_path))
    try:
        placeholders = ",".join("?" * len(wanted))
        rows = con.execute(
            f"SELECT SpectrumId, blobMass, blobIntensity FROM SpectrumTable "
            f"WHERE SpectrumId IN ({placeholders})",
            wanted,
        ).fetchall()
    finally:
        con.close()

    seen_ids = [int(sid) for sid, _, _ in rows]
    duplicates = sorted({sid for sid in seen_ids if seen_ids.count(sid) > 1})
    if duplicates:
        raise BlobDefect(
            f"{db_path.name}: SpectrumId(s) appear more than once in "
            f"SpectrumTable: {duplicates}")

    out = {}
    for sid, blob_mz, blob_inten in rows:
        mz = decode_blob(blob_mz)
        inten = decode_blob(blob_inten)
        if mz.size != inten.size:
            raise BlobDefect(
                f"spectrum {sid} in {db_path.name}: blob length mismatch, "
                f"{mz.size} masses against {inten.size} intensities")
        out[int(sid)] = (mz, inten)

    missing = set(wanted) - set(out)
    if missing:
        raise BlobDefect(
            f"{db_path.name}: SpectrumId absent from SpectrumTable: "
            f"{sorted(missing)}")
    return out


MU_TABLE_COLUMNS = ["connectivity_key", "ce_numeric", "mu", "n_spectra",
                    "spectrum_ids", "source_libraries"]


def spectrum_mu(mz: np.ndarray, intensity: np.ndarray,
                precursor_mz: float) -> float:
    """Base-cell `features.mu` for one peak list.

    Peaks are sorted by m/z, the declared PrecursorMass is used as the
    precursor (the WUR analogue of MassBank's MS$FOCUSED_ION), and the
    base preprocessing cell is applied through the same `Spectrum` path the
    LCSB corpus used. A nonfinite value, a negative intensity, an empty or
    all-zero peak list, or an unusable precursor raises rather than
    returning NaN, so a defect becomes a census entry upstream instead of a
    silent hole in the table.
    """
    if mz.size == 0 or intensity.size == 0:
        raise BlobDefect("empty peak list")
    if mz.size != intensity.size:
        raise BlobDefect(
            f"blob length mismatch: {mz.size} masses, {intensity.size} intensities")
    if not np.all(np.isfinite(mz)) or not np.all(np.isfinite(intensity)):
        raise BlobDefect("nonfinite value in the peak list")
    if np.any(intensity < 0):
        raise BlobDefect("negative intensity in the peak list")
    if intensity.sum() <= 0:
        raise BlobDefect("total intensity is not positive")
    if precursor_mz is None or not np.isfinite(precursor_mz) or precursor_mz <= 0:
        raise BlobDefect(f"unusable declared precursor m/z: {precursor_mz!r}")

    order = np.argsort(mz)
    spectrum = Spectrum(mz=mz[order], intensity=intensity[order],
                        precursor_mz=float(precursor_mz))
    value = feature_mu(spectrum.preprocess(ppm=PRECURSOR_MATCH_PPM, **BASE_CELL))
    if not np.isfinite(value):
        raise BlobDefect("mu is not finite")
    return float(value)


def build_mu_table(accepted: pd.DataFrame,
                   data_dir: Path) -> tuple[pd.DataFrame, list[dict]]:
    """One base-cell mu per (connectivity_key, ce_numeric), over exactly the
    spectra in `accepted`.

    Duplicate deposits at the same (key, energy) collapse by the
    preregistered aggregator, the median. The contributing spectrum ids and
    source libraries are preserved so the value is traceable to its inputs.

    Returns (table, census). A spectrum with a defect produces a census
    entry naming it and its reason; it never disappears quietly. A
    (key, energy) whose every spectrum is defective yields no row, and its
    absence is visible both in the census and in the per-energy n.
    """
    census: list[dict] = []
    per_spectrum = []

    for (library, polarity_file), grp in accepted.groupby(
            ["source_library", "source_polarity_file"], sort=True):
        stem = LIBRARY_DB_FILES[(library, polarity_file)]
        db_path = data_dir / f"{stem}.db"
        peaks = read_spectrum_peaks(db_path, grp["spectrum_id"])
        for row in grp.itertuples(index=False):
            mz, intensity = peaks[int(row.spectrum_id)]
            try:
                value = spectrum_mu(mz, intensity, row.precursor_mass)
            except BlobDefect as exc:
                census.append({
                    "connectivity_key": row.connectivity_key,
                    "ce_numeric": float(row.energy),
                    "source_library": library,
                    "spectrum_id": int(row.spectrum_id),
                    "reason": str(exc),
                })
                continue
            per_spectrum.append({
                "connectivity_key": row.connectivity_key,
                "ce_numeric": float(row.energy),
                "source_library": library,
                "spectrum_id": int(row.spectrum_id),
                "mu": value,
            })

    if not per_spectrum:
        return pd.DataFrame(columns=MU_TABLE_COLUMNS), census

    df = pd.DataFrame(per_spectrum)
    rows = []
    for (key, energy), grp in df.groupby(["connectivity_key", "ce_numeric"],
                                          sort=True):
        grp = grp.sort_values(["source_library", "spectrum_id"])
        rows.append({
            "connectivity_key": key,
            "ce_numeric": float(energy),
            "mu": float(np.median(grp["mu"].to_numpy())),
            "n_spectra": int(len(grp)),
            "spectrum_ids": tuple(zip(grp["source_library"],
                                      grp["spectrum_id"].astype(int))),
            "source_libraries": tuple(sorted(set(grp["source_library"]))),
        })
    return pd.DataFrame(rows, columns=MU_TABLE_COLUMNS), census
