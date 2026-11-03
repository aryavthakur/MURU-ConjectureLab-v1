"""Outcome-blind mzML access for an external validation source.

Two strictly separated operations:

* `scan_headers(path)` streams the file and returns acquisition metadata for
  every spectrum from an allowlist of controlled-vocabulary terms (MS level,
  scan time, selected-ion m/z and charge, collision energy, activation, scan
  window, isolation window). It never decodes a binary array, and it never
  returns intensity summaries (total ion current, base peak, lowest/highest
  observed m/z): those are outcomes and are not on the allowlist.

* `scan_headers_rung_only(source)` is the ONLY header reader for population-2
  (replacement validation) files. It returns fixed-rung MS2 rows only and never
  materialises a collision energy value, an Assisted scan, or an MS3+ precursor
  (which is an MS2 fragment m/z): headers are otherwise not outcome-blind
  (review finding F-MSn, 2026-09-13).

* `decode_selected(source, spectrum_ids, guard)` decodes peak arrays for an
  explicit list of spectra only, and only under a fully constructed decode
  authority from `muru.wur_v2.decode_authority` (since 2026-09-13: the legacy
  `AccessGuard`, the void study-1 `ConfirmationAccessGuard` and duck-typed
  guards are refused). Any other spectrum's arrays are skipped unread. A source
  is a file path or a `ZipMember`; its bytes are read ONCE, hashed, and both the
  authorization pass and the decode pass parse those same bytes.
"""
from __future__ import annotations

import base64
import contextvars
import hashlib
import io
import zipfile
from pathlib import Path
from typing import NamedTuple
import zlib

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


class ZipMember(NamedTuple):
    zip_path: Path
    member: str


def read_source(source) -> tuple[str, bytes]:
    """(basename, bytes) of a file path or a ZipMember. Reading bytes decodes nothing."""
    if isinstance(source, ZipMember):
        with zipfile.ZipFile(source.zip_path) as zf:
            return source.member.rsplit("/", 1)[-1], zf.read(source.member)
    p = Path(source)
    return p.name, p.read_bytes()


def _iter_spectra(data: bytes):
    for _, spec in etree.iterparse(io.BytesIO(data), events=("end",), tag=NS + "spectrum", huge_tree=True):
        yield spec
        spec.clear()
        while spec.getprevious() is not None:
            del spec.getparent()[0]


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


class HeaderAccessRefused(OutcomeAccessError):
    """Full headers were requested for a file that is not already exposed."""


def _full_header_allowlist() -> frozenset:
    """sha256 of files whose full headers may be read: the exposure registry's decoded files and the study-1
    sample transport files (all of whose compounds are excluded from population 2)."""
    import csv
    import json

    from muru.wur_v2 import decode_authority as DA
    shas = set()
    try:
        with open(DA.ROOT / DA.EXPOSED_FILES, newline="") as f:
            shas |= {r["file_sha256"] for r in csv.DictReader(f)}
        shas |= {r["sha256"] for r in json.loads((DA.ROOT / DA.STUDY1_TRANSPORT).read_text())["rows"] if r.get("sha256")}
    except (OSError, ValueError, KeyError):
        return frozenset()                                   # no readable allowlist: refuse everything
    return frozenset(shas)


def scan_headers(source) -> list[dict]:
    """Full allowlisted headers, including every collision energy and MS3+ precursor m/z. Those are outcome
    proxies (the Assisted energy is outcome-adaptive; an MS3 precursor is an MS2 fragment m/z), so since the
    study-2 review this refuses any file that is not already exposed. Population-2 files use
    scan_headers_rung_only."""
    data = source if isinstance(source, (bytes, bytearray)) else read_source(source)[1]
    from muru.wur_v2 import decode_authority as DA
    if not DA._test_mode() and hashlib.sha256(data).hexdigest() not in _full_header_allowlist():
        raise HeaderAccessRefused("full scan headers are only for already-exposed files; use scan_headers_rung_only")
    rows = []
    for spec in _iter_spectra(data):
        bdal = spec.find(NS + "binaryDataArrayList")
        if bdal is not None:
            spec.remove(bdal)                                   # arrays dropped before any parameter is read
        row = {"spectrum_id": spec.get("id"), "index": int(spec.get("index", -1))}
        row.update(_cv(spec))
        for k in list(row):
            if k in DENY.values():
                row.pop(k)
        rows.append(row)
    return rows


RUNG_ONLY_COLUMNS = ("spectrum_id", "index", "selected_ion_mz", "rung", "scan_window_lower_limit",
                     "scan_window_upper_limit")


def scan_headers_rung_only(source) -> list[dict]:
    """Fixed-rung MS2 rows only: spectrum_id, index, selected_ion_mz, rung (20.0 or 60.0), scan window.

    The rung rule (external_msnlib.fixed_rung_scans) needs every MS2 scan's collision energy; those values and
    the Assisted scans exist only inside this function and are never returned. MS3+ spectra are dropped before
    any of their parameters are kept."""
    import pandas as pd

    from muru.wur_v2.external_msnlib import fixed_rung_scans
    data = read_source(source)[1] if not isinstance(source, (bytes, bytearray)) else source
    rows = []
    for spec in _iter_spectra(data):
        bdal = spec.find(NS + "binaryDataArrayList")
        if bdal is not None:
            spec.remove(bdal)
        cv = _cv(spec)
        if cv.get("ms_level") != 2.0:
            continue
        rows.append({"spectrum_id": spec.get("id"), "index": int(spec.get("index", -1)), "ms_level": cv.get("ms_level"),
                     "selected_ion_mz": cv.get("selected_ion_mz"), "collision_energy": cv.get("collision_energy"),
                     "scan_window_lower_limit": cv.get("scan_window_lower_limit"),
                     "scan_window_upper_limit": cv.get("scan_window_upper_limit")})
    if not rows:
        return []
    r = fixed_rung_scans(pd.DataFrame(rows))
    r = r[r.rung.notna()]
    return [{c: getattr(t, c) for c in RUNG_ONLY_COLUMNS} for t in r.itertuples(index=False)]


# Set only inside decode_selected, after authorization; _decode_array refuses without it (review F-A).
_PERMIT: contextvars.ContextVar = contextvars.ContextVar("muru_decode_permit", default=None)


def _decode_array(bda) -> tuple[str, np.ndarray]:
    if _PERMIT.get() is None:
        raise OutcomeAccessError("binary arrays may only be decoded inside decode_selected after authorization")
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


def _spectrum_scope(spec) -> tuple:
    """(ms_level, selected_ion_mz, n_precursors, n_selected_ions) from a spectrum element's own parameters,
    never from its arrays. Last-value-wins like _cv."""
    level = mz = None
    n_sel = 0
    for cv in spec.iter(NS + "cvParam"):
        parent = cv.getparent()
        if parent is not None and parent.tag == NS + "binaryDataArray":
            continue
        acc, val = cv.get("accession"), cv.get("value")
        if acc == "MS:1000511" and val not in (None, ""):
            level = float(val)
        elif acc == "MS:1000744":
            n_sel += 1
            if val not in (None, ""):
                mz = float(val)
    n_prec = len(spec.findall(f"{NS}precursorList/{NS}precursor"))
    return level, mz, n_prec, n_sel


def _authority_module():
    from muru.wur_v2 import decode_authority
    return decode_authority


def decode_selected(source, spectrum_ids, guard) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Decode peak arrays for explicitly named spectra under a decode authority.

    Hardened 2026-09-13 after confirmation sample 1 was burned by a duck-typed guard with no scope
    (artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/), and again after the study-2
    pre-sampling review. Order is fixed:
      1. the guard's EXACT type must be AnchorPreflightAuthority or ConfirmationV2Authority AND it must hold a
         scope registered by a completed constructor (duck types, subclasses, __new__ objects, legacy guards
         are refused); its scope is immutable module-private state, never an attribute of the object;
      2. the source's bytes are read once and hashed;
      3. a header pass over those bytes (arrays removed) reads each requested scan's (ms level, selected-ion
         m/z, precursor count, selected-ion count);
      4. decode_authority.authorize_decode checks content hash, scan allowlist and precursor scope and durably
         logs the intent, or raises;
      5. the decode pass over the SAME bytes re-reads the scope of each requested spectrum and refuses on any
         difference, then decodes only those spectra with the decode permit set.
    """
    DA = _authority_module()
    if guard is None or type(guard) not in DA.AUTHORITY_TYPES or not DA.is_constructed(guard):
        raise OutcomeAccessError(
            "peak decode requires an authorized AnchorPreflightAuthority or ConfirmationV2Authority "
            f"(got {type(guard).__module__}.{type(guard).__qualname__})")
    spectrum_ids = list(spectrum_ids)
    if any(type(s) is not str for s in spectrum_ids):
        raise OutcomeAccessError("spectrum ids must be plain str")
    wanted = sorted(set(spectrum_ids))
    if not wanted:
        return {}
    name, data = read_source(source)
    sha = hashlib.sha256(data).hexdigest()
    scope = {}
    for spec in _iter_spectra(data):
        sid = spec.get("id")
        if sid in wanted:
            bdal = spec.find(NS + "binaryDataArrayList")
            if bdal is not None:
                spec.remove(bdal)
            scope[sid] = _spectrum_scope(spec)
    missing = [s for s in wanted if s not in scope]
    if missing:
        raise OutcomeAccessError(f"{len(missing)} requested spectra are not in {name}, e.g. {missing[:3]}")
    DA.authorize_decode(guard, name, sha, [(s, *scope[s]) for s in wanted])
    out = {}
    token = _PERMIT.set(object())
    try:
        for spec in _iter_spectra(data):
            sid = spec.get("id")
            if sid not in scope:
                continue
            if _spectrum_scope(spec) != scope[sid]:
                raise OutcomeAccessError(f"{name}:{sid} header differs between authorization and decode")
            arrays = dict(_decode_array(b) for b in spec.iter(NS + "binaryDataArray"))
            n_declared = int(spec.get("defaultArrayLength", -1))
            if not (len(arrays["mz"]) == len(arrays["intensity"]) and (n_declared < 0 or len(arrays["mz"]) == n_declared)):
                raise ValueError(f"{sid}: decoded array lengths disagree with each other or with defaultArrayLength")
            out[sid] = (arrays["mz"], arrays["intensity"])
            if len(out) == len(wanted):
                break
    finally:
        _PERMIT.reset(token)
    return out
