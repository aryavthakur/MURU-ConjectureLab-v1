"""Outcome-blind mzML access for an external validation source.

Two strictly separated operations:

* `scan_headers(path)` streams the file and returns acquisition metadata for
  every spectrum from an allowlist of controlled-vocabulary terms (MS level,
  scan time, selected-ion m/z and charge, collision energy, activation, scan
  window, isolation window). It never decodes a binary array, and it never
  returns intensity summaries (total ion current, base peak, lowest/highest
  observed m/z): those are outcomes and are not on the allowlist.

* `decode_selected(path, spectrum_ids, guard)` decodes peak arrays for an
  explicit list of spectra only, and only when a guard object authorizes it
  (a calibration-anchor guard or the one-look validation guard). Any other
  spectrum's arrays are skipped unread.
"""
from __future__ import annotations

import base64
import zlib
from pathlib import Path

import numpy as np
from lxml import etree

NS = "{http://psi.hupo.org/ms/mzml}"
ALLOW = {
    "MS:1000511": "ms_level", "MS:1000016": "scan_start_time", "MS:1000744": "selected_ion_mz",
    "MS:1000041": "charge_state", "MS:1000045": "collision_energy", "MS:1000133": "cid",
    "MS:1000422": "beam_type_cid", "MS:1003294": "ead", "MS:1000501": "scan_window_lower_limit",
    "MS:1000500": "scan_window_upper_limit", "MS:1000827": "isolation_window_target_mz",
    "MS:1000828": "isolation_window_lower_offset", "MS:1000829": "isolation_window_upper_offset",
    "MS:1000130": "positive_scan", "MS:1000129": "negative_scan", "MS:1000512": "filter_string",
    "MS:1000579": "ms1_spectrum", "MS:1000580": "msn_spectrum", "MS:1000127": "centroid_spectrum",
}
DENY = {"MS:1000285": "total ion current", "MS:1000504": "base peak m/z", "MS:1000505": "base peak intensity",
        "MS:1000527": "highest observed m/z", "MS:1000528": "lowest observed m/z"}
DENY_NUMPRESS = {"MS:1002312", "MS:1002313", "MS:1002314", "MS:1002746", "MS:1002747", "MS:1002748"}


class OutcomeAccessError(RuntimeError):
    """A peak decode was attempted without an authorizing guard."""


def _cv(elem):
    out = {}
    for cv in elem.iter(NS + "cvParam"):
        # do not descend into binary data descriptions for header reads
        acc = cv.get("accession")
        if acc in ALLOW:
            name = ALLOW[acc]
            val = cv.get("value")
            out[name] = float(val) if val not in (None, "") and name not in ("filter_string",) else (val if val else True)
    return out


def scan_headers(path: Path) -> list[dict]:
    rows = []
    for _, spec in etree.iterparse(str(path), events=("end",), tag=NS + "spectrum", huge_tree=True):
        bdal = spec.find(NS + "binaryDataArrayList")
        if bdal is not None:
            spec.remove(bdal)                                   # arrays dropped before any parameter is read
        row = {"spectrum_id": spec.get("id"), "index": int(spec.get("index", -1))}
        row.update(_cv(spec))
        for k in list(row):
            if k in DENY.values():
                row.pop(k)
        rows.append(row)
        spec.clear()
        while spec.getprevious() is not None:
            del spec.getparent()[0]
    return rows


def _decode_array(bda) -> tuple[str, np.ndarray]:
    accs = {cv.get("accession") for cv in bda.iter(NS + "cvParam")}
    if accs & DENY_NUMPRESS:
        raise ValueError("numpress-compressed arrays are not supported")
    raw = base64.b64decode(bda.find(NS + "binary").text or b"")
    if "MS:1000574" in accs:
        raw = zlib.decompress(raw)
    dtype = "<f8" if "MS:1000523" in accs else "<f4"
    arr = np.frombuffer(raw, dtype=dtype).astype(float)
    kind = "mz" if "MS:1000514" in accs else ("intensity" if "MS:1000515" in accs else "other")
    return kind, arr


def decode_selected(path: Path, spectrum_ids, guard) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    if guard is None or not getattr(guard, "authorized", False):
        raise OutcomeAccessError("peak decode requires an authorizing guard")
    wanted = set(spectrum_ids)
    guard.record_decode(path, sorted(wanted))
    out = {}
    for _, spec in etree.iterparse(str(path), events=("end",), tag=NS + "spectrum", huge_tree=True):
        sid = spec.get("id")
        if sid in wanted:
            arrays = dict(_decode_array(b) for b in spec.iter(NS + "binaryDataArray"))
            out[sid] = (arrays["mz"], arrays["intensity"])
        spec.clear()
        while spec.getprevious() is not None:
            del spec.getparent()[0]
        if len(out) == len(wanted):
            break
    return out
