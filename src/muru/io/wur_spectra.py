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
from collections import Counter
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


def _coerce_ids(spectrum_ids) -> list[int]:
    """Sorted, deduplicated int ids, or a `BlobDefect` for a non-integer id."""
    try:
        return sorted({int(s) for s in spectrum_ids})
    except (TypeError, ValueError) as exc:
        raise BlobDefect(f"non-integer spectrum id in {spectrum_ids!r}: {exc}")


def _fetch_blob_rows(db_path: Path, wanted: list[int]) -> list[tuple]:
    """Raw (SpectrumId, blobMass, blobIntensity) rows for `wanted` ids.

    The query is chunked at 500 ids per statement so the id count never
    depends on a particular SQLite build's placeholder ceiling. Duplicate
    and absent SpectrumIds are a lineage disagreement between the
    accepted-row table and the file, not a property of one spectrum, so
    both still raise here.
    """
    con = sqlite3.connect(str(db_path))
    try:
        rows = []
        chunk_size = 500
        for start in range(0, len(wanted), chunk_size):
            chunk = wanted[start:start + chunk_size]
            placeholders = ",".join("?" * len(chunk))
            rows.extend(con.execute(
                f"SELECT SpectrumId, blobMass, blobIntensity FROM SpectrumTable "
                f"WHERE SpectrumId IN ({placeholders})",
                chunk,
            ).fetchall())
    finally:
        con.close()

    seen_ids = [int(sid) for sid, _, _ in rows]
    counts = Counter(seen_ids)
    duplicates = sorted(sid for sid, count in counts.items() if count > 1)
    if duplicates:
        raise BlobDefect(
            f"{db_path.name}: SpectrumId(s) appear more than once in "
            f"SpectrumTable: {duplicates}")

    missing = set(wanted) - set(seen_ids)
    if missing:
        raise BlobDefect(
            f"{db_path.name}: SpectrumId absent from SpectrumTable: "
            f"{sorted(missing)}")
    return rows


def read_spectrum_peaks(db_path: Path,
                        spectrum_ids) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Peak arrays for the requested SpectrumIds in one mzVault file.

    SpectrumId is unique per file, not across the release, so the caller
    must group its accepted rows by source file before calling this.
    """
    wanted = _coerce_ids(spectrum_ids)
    if not wanted:
        return {}
    rows = _fetch_blob_rows(db_path, wanted)

    out = {}
    for sid, blob_mz, blob_inten in rows:
        mz = decode_blob(blob_mz)
        inten = decode_blob(blob_inten)
        if mz.size != inten.size:
            raise BlobDefect(
                f"spectrum {sid} in {db_path.name}: blob length mismatch, "
                f"{mz.size} masses against {inten.size} intensities")
        out[int(sid)] = (mz, inten)
    return out


def read_spectrum_peaks_censused(
        db_path: Path, spectrum_ids) -> tuple[dict[int, tuple[np.ndarray, np.ndarray]],
                                              list[dict]]:
    """Like `read_spectrum_peaks`, but a defect in ONE spectrum's blob is
    returned as a census entry rather than aborting the whole read.

    The distinction is deliberate. An unreadable or mis-sized blob is a
    property of that spectrum, and the preregistration requires it to be
    reported per spectrum, so one corrupt deposit must not hide the state of
    every other. A missing, duplicated or non-integer SpectrumId is instead a
    property of the LINEAGE -- the accepted-row table and the file disagree
    about what exists -- which no per-spectrum census can express, so those
    still raise.

    Returns (peaks, defects). Each defect is
    {"spectrum_id": int, "reason": str}.
    """
    wanted = _coerce_ids(spectrum_ids)
    if not wanted:
        return {}, []
    rows = _fetch_blob_rows(db_path, wanted)

    peaks, defects = {}, []
    for sid, blob_mz, blob_inten in rows:
        try:
            mz = decode_blob(blob_mz)
            inten = decode_blob(blob_inten)
            if mz.size != inten.size:
                raise BlobDefect(
                    f"blob length mismatch, {mz.size} masses against "
                    f"{inten.size} intensities")
        except BlobDefect as exc:
            defects.append({"spectrum_id": int(sid), "reason": str(exc)})
            continue
        peaks[int(sid)] = (mz, inten)
    return peaks, defects


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
    if np.any(mz <= 0):
        raise BlobDefect("non-positive m/z in the peak list")
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
            ["source_library", "source_polarity_file"], sort=True, dropna=False):
        stem = LIBRARY_DB_FILES[(library, polarity_file)]
        db_path = data_dir / f"{stem}.db"
        peaks, blob_defects = read_spectrum_peaks_censused(
            db_path, grp["spectrum_id"])
        by_spectrum = {int(r.spectrum_id): r for r in grp.itertuples(index=False)}
        for defect in blob_defects:
            row = by_spectrum[defect["spectrum_id"]]
            census.append({
                "connectivity_key": row.connectivity_key,
                "ce_numeric": float(row.energy),
                "source_library": library,
                "source_polarity_file": polarity_file,
                "spectrum_id": defect["spectrum_id"],
                "reason": defect["reason"],
            })

        for row in grp.itertuples(index=False):
            sid = int(row.spectrum_id)
            if sid not in peaks:
                continue          # already censused above
            mz, intensity = peaks[sid]
            try:
                value = spectrum_mu(mz, intensity, row.precursor_mass)
            except BlobDefect as exc:
                census.append({
                    "connectivity_key": row.connectivity_key,
                    "ce_numeric": float(row.energy),
                    "source_library": library,
                    "source_polarity_file": polarity_file,
                    "spectrum_id": int(row.spectrum_id),
                    "reason": str(exc),
                })
                continue
            per_spectrum.append({
                "connectivity_key": row.connectivity_key,
                "ce_numeric": float(row.energy),
                "source_library": library,
                "source_polarity_file": polarity_file,
                "spectrum_id": int(row.spectrum_id),
                "mu": value,
            })

    if not per_spectrum:
        return pd.DataFrame(columns=MU_TABLE_COLUMNS), census

    df = pd.DataFrame(per_spectrum)
    rows = []
    for (key, energy), grp in df.groupby(["connectivity_key", "ce_numeric"],
                                          sort=True, dropna=False):
        grp = grp.sort_values(["source_library", "source_polarity_file", "spectrum_id"])
        rows.append({
            "connectivity_key": key,
            "ce_numeric": float(energy),
            "mu": float(np.median(grp["mu"].to_numpy())),
            "n_spectra": int(len(grp)),
            "spectrum_ids": tuple(
                (str(lib), str(pf), int(sid))
                for lib, pf, sid in zip(grp["source_library"],
                                        grp["source_polarity_file"],
                                        grp["spectrum_id"])),
            "source_libraries": tuple(sorted(set(grp["source_library"]))),
        })
    return pd.DataFrame(rows, columns=MU_TABLE_COLUMNS), census
