"""Raw mzML branch (W1.5, W1.6).

Purpose: two Phase 1 measurements that the curated layer cannot supply.

  1. REPEATABILITY. The curated MassBank layer holds one record per compound,
     so it contains no repeated measurement of the same compound at the same
     energy. Mixes 499, 503 and 505 share a compound set, so the same compound
     at the same NCE was measured three times. That is the only route to a
     noise floor (master plan section 9.4).

  2. FORMULA-FILTER EFFECT. RMassBank keeps only peaks assignable as
     sub-formulas of the precursor. Endpoints computed from raw centroided
     mzML carry no such filter, so the difference between branches measures
     how much of an endpoint is annotation rather than detection (risk R1).

WHAT THESE REPLICATES ARE, PRECISELY. Mixes 499 (95 substances), 503 (185) and
505 (365) are three DIFFERENT mixture preparations that share a compound set,
run as separate injections. They are not repeated injections of one vial. The
variance they yield therefore contains preparation, injection, instrument AND
matrix-complexity variation, and is an UPPER BOUND on technical repeatability.
For the K3 gate that direction is conservative: an endpoint whose signal
exceeds this inflated noise also exceeds pure technical noise. Called
"inter-mixture repeatability" throughout, never "technical replicate".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymzml

from ..spectra import Spectrum


@dataclass(frozen=True)
class MS2Scan:
    """One MS2 scan as recorded, before any merging."""

    scan_id: str
    rt_min: float
    precursor_mz: float
    mz: np.ndarray
    intensity: np.ndarray

    def to_spectrum(self, declared_precursor_mz: float | None = None) -> Spectrum:
        return Spectrum(
            mz=self.mz, intensity=self.intensity,
            precursor_mz=(declared_precursor_mz if declared_precursor_mz
                          is not None else self.precursor_mz),
            accession=self.scan_id,
        )


def iter_ms2(path: str | Path, min_peaks: int = 1):
    """Yield MS2 scans from a centroided mzML.

    Reads only what is needed: scan id, retention time, selected precursor m/z,
    and the centroided peak list. No feature detection, no deisotoping -- this
    is the deliberately un-processed branch.
    """
    run = pymzml.run.Reader(str(path), MS_precisions={1: 5e-6, 2: 5e-6})
    for spec in run:
        if spec.ms_level != 2:
            continue
        sel = spec.selected_precursors
        if not sel or "mz" not in sel[0]:
            continue
        peaks = spec.peaks("centroided")
        if peaks is None or len(peaks) < min_peaks:
            continue
        arr = np.asarray(peaks, dtype=float)
        keep = arr[:, 1] > 0
        if not keep.any():
            continue
        rt = spec.scan_time_in_minutes()
        yield MS2Scan(
            scan_id=str(spec.ID),
            rt_min=float(rt) if rt is not None else float("nan"),
            precursor_mz=float(sel[0]["mz"]),
            mz=arr[keep, 0], intensity=arr[keep, 1],
        )


def match_scans(scans: list[MS2Scan], target_mz: float, target_rt: float | None,
                mz_ppm: float = 10.0, rt_window_min: float = 0.5) -> list[MS2Scan]:
    """Scans whose precursor matches a target within m/z and RT tolerance.

    RT tolerance mirrors the +/-0.5 min used by the study's own Shinyscreen
    prescreening, so the raw branch selects on the same basis the curated branch
    did. When target_rt is None the RT filter is skipped and the caller must
    treat the result as potentially chimeric.
    """
    tol = target_mz * mz_ppm * 1e-6
    out = []
    for s in scans:
        if abs(s.precursor_mz - target_mz) > tol:
            continue
        if target_rt is not None and np.isfinite(s.rt_min):
            if abs(s.rt_min - target_rt) > rt_window_min:
                continue
        out.append(s)
    return out


def merge_scans(scans: list[MS2Scan], mz_ppm: float = 10.0) -> tuple[np.ndarray, np.ndarray]:
    """Sum intensities of scans onto a common m/z axis by greedy ppm binning.

    Mirrors what RMassBank's MERGING step does in spirit (combine the MS2 scans
    across an LC peak) without its formula filter, so the branch comparison
    isolates the filter rather than confounding it with merging.
    """
    if not scans:
        return np.array([]), np.array([])
    mz = np.concatenate([s.mz for s in scans])
    inten = np.concatenate([s.intensity for s in scans])
    order = np.argsort(mz)
    mz, inten = mz[order], inten[order]

    out_mz, out_in = [], []
    i = 0
    while i < mz.size:
        j = i + 1
        tol = mz[i] * mz_ppm * 1e-6
        while j < mz.size and (mz[j] - mz[i]) <= tol:
            j += 1
        w = inten[i:j]
        # intensity-weighted centroid of the bin
        out_mz.append(float((mz[i:j] * w).sum() / w.sum()) if w.sum() > 0
                      else float(mz[i:j].mean()))
        out_in.append(float(w.sum()))
        i = j
    return np.array(out_mz), np.array(out_in)


def merged_spectrum(scans: list[MS2Scan], declared_precursor_mz: float,
                    mz_ppm: float = 10.0) -> Spectrum:
    mz, inten = merge_scans(scans, mz_ppm)
    return Spectrum(mz=mz, intensity=inten, precursor_mz=declared_precursor_mz)
