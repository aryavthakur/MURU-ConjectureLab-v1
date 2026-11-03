"""Peak-list operations and the preprocessing grid (master plan section 7.3).

A Spectrum here is a finite measure on m/z: pairs (mz_k, I_k), k = 1..n, with
n from 1 to 331 in this corpus. Preprocessing is a finite, enumerable grid --
not a feature architecture, not a plugin system. Four axes, declared in
configs/preprocessing.yaml, evaluated exhaustively:

    relative intensity cutoff : 0, 0.1%, 1% of base peak
    precursor peak            : included / excluded
    intensity transform       : raw / sqrt
    source branch             : massbank_curated / raw_mzml

Precursor identification is the one genuinely delicate operation. The observed
precursor peak m/z and the declared MS$FOCUSED_ION: PRECURSOR_M/Z differ at the
ppm level (recalibration), so matching is by tolerance, and the tolerance is an
explicit parameter rather than a hidden constant.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

DEFAULT_PRECURSOR_PPM = 10.0


@dataclass(frozen=True)
class Spectrum:
    """An immutable peak list with its precursor context.

    `mz` and `intensity` are parallel arrays sorted by m/z. `precursor_mz` is
    the DECLARED value from the record, kept separate from whichever observed
    peak matches it.
    """

    mz: np.ndarray
    intensity: np.ndarray
    precursor_mz: float | None
    accession: str | None = None

    def __post_init__(self) -> None:
        if self.mz.shape != self.intensity.shape:
            raise ValueError("mz and intensity must have the same shape")
        if np.any(self.intensity < 0):
            raise ValueError("negative intensities are not a valid spectrum")

    @property
    def n_peaks(self) -> int:
        return int(self.mz.size)

    @property
    def tic(self) -> float:
        """Total ion current: sum of intensities in the peak list."""
        return float(self.intensity.sum())

    @property
    def base_peak_intensity(self) -> float:
        return float(self.intensity.max()) if self.n_peaks else 0.0

    def precursor_index(self, ppm: float = DEFAULT_PRECURSOR_PPM) -> int | None:
        """Index of the peak matching the declared precursor m/z, else None.

        Returns the CLOSEST peak within tolerance. None when the precursor is
        absent from the peak list -- which is a real, common physical outcome
        at high energy, not an error.
        """
        if self.precursor_mz is None or self.n_peaks == 0:
            return None
        tol = self.precursor_mz * ppm * 1e-6
        d = np.abs(self.mz - self.precursor_mz)
        i = int(np.argmin(d))
        return i if d[i] <= tol else None

    # -- preprocessing grid axes -----------------------------------------
    def with_relative_cutoff(self, cutoff: float) -> "Spectrum":
        """Drop peaks below `cutoff` * base-peak intensity. cutoff in [0, 1)."""
        if cutoff <= 0 or self.n_peaks == 0:
            return self
        keep = self.intensity >= cutoff * self.base_peak_intensity
        return replace(self, mz=self.mz[keep], intensity=self.intensity[keep])

    def without_precursor(self, ppm: float = DEFAULT_PRECURSOR_PPM) -> "Spectrum":
        """Remove the precursor peak if present."""
        i = self.precursor_index(ppm)
        if i is None:
            return self
        keep = np.ones(self.n_peaks, dtype=bool)
        keep[i] = False
        return replace(self, mz=self.mz[keep], intensity=self.intensity[keep])

    def with_intensity_transform(self, transform: str) -> "Spectrum":
        """Apply an intensity weighting. 'raw' or 'sqrt'.

        sqrt is the classical dot-product weighting. It changes mu's weighting
        and so must be tested rather than assumed harmless.
        """
        if transform == "raw":
            return self
        if transform == "sqrt":
            return replace(self, intensity=np.sqrt(self.intensity))
        raise ValueError(f"unknown intensity transform {transform!r}")

    def preprocess(
        self,
        relative_cutoff: float = 0.0,
        include_precursor: bool = True,
        intensity_transform: str = "raw",
        ppm: float = DEFAULT_PRECURSOR_PPM,
    ) -> "Spectrum":
        """Apply one cell of the preprocessing grid.

        Order matters and is fixed: cutoff on RAW intensities first (so the
        cutoff means what it says), then precursor removal, then transform.
        """
        s = self.with_relative_cutoff(relative_cutoff)
        if not include_precursor:
            s = s.without_precursor(ppm)
        return s.with_intensity_transform(intensity_transform)


def spectrum_from_record(record, ppm: float = DEFAULT_PRECURSOR_PPM) -> Spectrum:
    """Build a Spectrum from a parsed MassBankRecord.

    Uses PK$PEAK absolute intensities, not the 0-999 relative column, because
    the relative column is already normalized and would destroy TIC.
    """
    mz = np.array([p.mz for p in record.peaks], dtype=float)
    inten = np.array([p.intensity for p in record.peaks], dtype=float)
    order = np.argsort(mz)
    prec_raw = record.sub("MS$FOCUSED_ION", "PRECURSOR_M/Z")
    try:
        prec = float(prec_raw) if prec_raw is not None else None
    except ValueError:
        prec = None
    return Spectrum(
        mz=mz[order], intensity=inten[order],
        precursor_mz=prec, accession=record.accession,
    )
