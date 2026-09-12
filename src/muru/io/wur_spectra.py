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
