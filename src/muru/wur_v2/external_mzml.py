"""Outcome-blind mzML access for an external validation source.

Two strictly separated operations:

* `scan_headers(path)` streams the file and returns acquisition metadata for
  every spectrum from an allowlist of controlled-vocabulary terms (MS level,
  scan time, selected-ion m/z and charge, collision energy, activation, scan
  window, isolation window). It never decodes a binary array, and it never
  returns intensity summaries (total ion current, base peak, lowest/highest
  observed m/z): those are outcomes and are not on the allowlist.

* `decode_selected(path, spectrum_ids, guard)` decodes peak arrays for an
  explicit list of spectra only, and only under a fully constructed decode
  authority from `muru.wur_v2.decode_authority` (since 2026-09-13: the legacy
  `AccessGuard`, the void study-1 `ConfirmationAccessGuard` and duck-typed
  guards are refused). Any other spectrum's arrays are skipped unread.
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
NUMPRESS_UNSUPPORTED = {"MS:1002312", "MS:1002314", "MS:1002746", "MS:1002748"}   # linear, slof (+ zlib variants)
NUMPRESS_PIC = {"MS:1002313", "MS:1002747"}                                       # positive integer (+ zlib)


def numpress_pic_decode(data: bytes) -> np.ndarray:
    """MS-Numpress positive-integer decoding (reference MSNumpress decodePic/decodeInt).

    Values are stored as half-byte (nybble) sequences: a head nybble n <= 8 gives
    n leading zero nybbles, n > 8 gives n-8 leading 0xf nybbles, followed by the
    remaining nybbles least significant first. An odd half-byte count is padded with
    a 0x0 nybble; a final lone low nybble is decoded only if it is 0x8 (a zero value).
    """
    nyb = np.empty(len(data) * 2, dtype=np.uint8)
    arr = np.frombuffer(data, dtype=np.uint8)
    nyb[0::2], nyb[1::2] = arr >> 4, arr & 0xF
    out, i, total = [], 0, len(nyb)
    while i < total:
        if i == total - 1 and nyb[i] != 0x8:
            break
        head = int(nyb[i]); i += 1
        if head <= 8:
            n, res = head, 0
        else:
            n = head - 8
            res = 0
            for j in range(n):
                res |= 0xF0000000 >> (4 * j)
        for j in range(n, 8):
            res |= int(nyb[i]) << ((j - n) * 4)
            i += 1
        out.append(res & 0xFFFFFFFF)
    return np.array(out, dtype=float)


def numpress_pic_encode(values) -> bytes:
    """Reference encoder (tests only)."""
    nybs = []
    for v in values:
        x = int(v + 0.5) & 0xFFFFFFFF
        mask = 0xF0000000
        if x & mask == 0:
            l = 8
            for k in range(8):
                if x & (mask >> (4 * k)):
                    l = k
                    break
            nybs.append(l)
            nybs += [(x >> (4 * (k - l))) & 0xF for k in range(l, 8)]
        else:
            nybs.append(0)
            nybs += [(x >> (4 * k)) & 0xF for k in range(8)]
    if len(nybs) % 2:
        nybs.append(0x0)
    return bytes((nybs[k] << 4) | nybs[k + 1] for k in range(0, len(nybs), 2))


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
    if accs & NUMPRESS_UNSUPPORTED:
        raise ValueError("numpress linear/slof arrays are not supported")
    raw = base64.b64decode(bda.find(NS + "binary").text or b"")
    if "MS:1000574" in accs or "MS:1002747" in accs:
        raw = zlib.decompress(raw)
    if accs & NUMPRESS_PIC:
        arr = numpress_pic_decode(raw)
    else:
        dtype = "<f8" if "MS:1000523" in accs else "<f4"
        arr = np.frombuffer(raw, dtype=dtype).astype(float)
    kind = "mz" if "MS:1000514" in accs else ("intensity" if "MS:1000515" in accs else "other")
    return kind, arr


def _spectrum_header_scope(spec) -> tuple[float | None, float | None]:
    """(ms_level, selected_ion_mz) read from a spectrum element's own cvParams, never from its arrays.
    Same last-value-wins semantics as scan_headers/_cv, so the two passes agree on an unchanged file."""
    level = mz = None
    for cv in spec.iter(NS + "cvParam"):
        if cv.getparent() is not None and cv.getparent().tag == NS + "binaryDataArray":
            continue
        acc, val = cv.get("accession"), cv.get("value")
        if acc == "MS:1000511" and val not in (None, ""):
            level = float(val)
        elif acc == "MS:1000744" and val not in (None, ""):
            mz = float(val)
    return level, mz


def _authority_types() -> tuple:
    from muru.wur_v2.decode_authority import AUTHORITY_TYPES
    return AUTHORITY_TYPES


def _constructed(guard) -> bool:
    from muru.wur_v2.decode_authority import is_constructed
    return is_constructed(guard)


def decode_selected(path: Path, spectrum_ids, guard) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Decode peak arrays for explicitly named spectra under a decode authority.

    Hardened 2026-09-13 after confirmation sample 1 was burned by a duck-typed guard with no scope
    (artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/). Order is fixed:
      1. the guard's EXACT type must be AnchorPreflightAuthority or ConfirmationV2Authority
         (muru.wur_v2.decode_authority); duck types, subclasses and legacy guards are refused;
      2. a header-only pass (arrays removed) reads each requested scan's ms level and selected-ion m/z
         from the file itself;
      3. guard.authorize(path, [(id, m/z, level)]) checks file content hash, scan allowlist and precursor
         scope and durably records the intent, or raises;
      4. the decode pass re-reads m/z and level from the same spectrum element and refuses on any change,
         then decodes only those spectra.
    """
    if (guard is None or type(guard) not in _authority_types() or not _constructed(guard)
            or getattr(guard, "authorized", False) is not True):
        raise OutcomeAccessError(
            "peak decode requires an authorized AnchorPreflightAuthority or ConfirmationV2Authority "
            f"(got {type(guard).__module__}.{type(guard).__qualname__})")
    path = Path(path)
    wanted = sorted(set(spectrum_ids))
    if not wanted:
        return {}
    header = {r["spectrum_id"]: r for r in scan_headers(path)}
    missing = [s for s in wanted if s not in header]
    if missing:
        raise OutcomeAccessError(f"{len(missing)} requested spectra are not in {path.name}, e.g. {missing[:3]}")
    requests = [(s, header[s].get("selected_ion_mz"), header[s].get("ms_level")) for s in wanted]
    guard.authorize(path, requests)
    scope = {s: (lvl, mz) for s, mz, lvl in requests}
    out = {}
    for _, spec in etree.iterparse(str(path), events=("end",), tag=NS + "spectrum", huge_tree=True):
        sid = spec.get("id")
        if sid in scope:
            if _spectrum_header_scope(spec) != scope[sid]:
                raise OutcomeAccessError(f"{path.name}:{sid} header changed between authorization and decode")
            arrays = dict(_decode_array(b) for b in spec.iter(NS + "binaryDataArray"))
            n_declared = int(spec.get("defaultArrayLength", -1))
            if not (len(arrays["mz"]) == len(arrays["intensity"]) and (n_declared < 0 or len(arrays["mz"]) == n_declared)):
                raise ValueError(f"{sid}: decoded array lengths disagree with each other or with defaultArrayLength")
            out[sid] = (arrays["mz"], arrays["intensity"])
        spec.clear()
        while spec.getprevious() is not None:
            del spec.getparent()[0]
        if len(out) == len(wanted):
            break
    return out
