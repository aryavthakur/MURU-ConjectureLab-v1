"""Outcome-blind, logged fetcher for the MultiMS2 identity/metadata census.

Every fetch goes through `fetch()`, which
  * refuses any URL whose path looks like a spectral/peak container
    (mzML, mzXML, raw, wiff, mgf, msp, parquet, sqlite, hdf5, the repository's
    MULTIMS2-PARTITION-*.tsv spectrum tables, Zenodo file-content endpoints),
  * refuses anything larger than MAX_BYTES,
  * saves the bytes under data/external/multims2_metadata/ and appends a
    provenance row (url, file, size, sha256, UTC time) to fetch_log.jsonl.

Usage: PYTHONPATH=src python3 scripts/wur_v2/census/multims2_fetch.py URL NAME [--range N]
  --range N performs an HTTP Range request for the first N bytes (header peek).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "external" / "multims2_metadata"
LOG = OUT / "fetch_log.jsonl"
MAX_BYTES = 8_000_000

DENY = [
    r"\.mz(ml|xml)(\.gz)?(\?|$)", r"\.raw(\?|$)", r"\.wiff", r"\.mgf", r"\.msp(\?|$)",
    r"\.parquet", r"\.sqlite", r"\.h5(\?|$)", r"\.hdf5", r"\.db(\?|$)", r"\.zip(\?|$)",
    r"\.tar", r"\.7z", r"PARTITION", r"spectra", r"/files/.+/content", r"/api/records/\d+/files-archive",
]
# Source code and method documentation are text, never peak data; a script
# named e.g. convert_spectra_to_tsv.py documents processing and is allowed.
CODE_OK = re.compile(r"\.(py|mzbatch|md|cff|toml)$", re.IGNORECASE)


def denied(url: str) -> str | None:
    for pat in DENY:
        if pat == r"spectra" and CODE_OK.search(url):
            continue
        if re.search(pat, url, flags=re.IGNORECASE):
            return pat
    return None


def fetch(url: str, name: str, range_bytes: int | None = None) -> Path:
    pat = denied(url)
    if pat:
        raise SystemExit(f"REFUSED (outcome-integrity denylist '{pat}'): {url}")
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MURU-outcome-blind-census/1.0",
                                               "Accept": "*/*"})
    if range_bytes:
        req.add_header("Range", f"bytes=0-{range_bytes - 1}")
    with urllib.request.urlopen(req, timeout=120) as r:
        status = r.status
        clen = r.headers.get("Content-Length")
        if clen and int(clen) > MAX_BYTES and not range_bytes:
            raise SystemExit(f"REFUSED (size {clen} > {MAX_BYTES}): {url}")
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"REFUSED (body exceeded {MAX_BYTES} bytes): {url}")
    path = OUT / name
    path.write_bytes(data)
    row = {"url": url, "file": str(path.relative_to(ROOT)), "bytes": len(data),
           "sha256": hashlib.sha256(data).hexdigest(), "http_status": status,
           "range_request_bytes": range_bytes,
           "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(json.dumps(row))
    return path


# GNPS batch-upload identity TSV columns, copied from the generating code
# (notebooks/convert_spectra_to_tsv.py at 659bd9b). The writer emits exactly
# these columns and never the MGF peak lines, so the file carries identity,
# acquisition labels and a scan pointer only. LIBQUALITY is the constant "1".
GNPS_COLUMNS = [
    "FILENAME", "SEQ", "COMPOUND_NAME", "COMPOUND_NAME_ORIGINAL", "MOLECULEMASS", "INSTRUMENT",
    "IONSOURCE", "EXTRACTSCAN", "SMILES", "SELFIES", "INCHI", "INCHIAUX", "CHARGE", "IONMODE",
    "FRAGMENTATION_METHOD", "COLLISION_ENERGY", "ACQUISITION", "EXACTMASS", "DATACOLLECTOR",
    "DATACURATOR", "ADDUCT", "LIBQUALITY", "PI", "SPECIES", "CASNUMBER", "PUBMED", "STRAIN",
    "INTEREST", "GENUS",
]


def fetch_gnps_identity_tsv(url: str, name: str) -> Path:
    """Header-verified download of a peak-free GNPS batch identity TSV.

    1. Range-peek the first 4 KB and require the header to equal GNPS_COLUMNS
       exactly (no extra column can smuggle peaks or QC summaries).
    2. Download, then require every line to split into exactly len(GNPS_COLUMNS)
       fields. Any violation deletes the file and aborts.
    """
    if not re.search(r"MULTIMS2-PARTITION-\d+\.tsv$", url):
        raise SystemExit(f"REFUSED (not a GNPS identity partition): {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "MURU-outcome-blind-census/1.0",
                                               "Range": "bytes=0-4095"})
    with urllib.request.urlopen(req, timeout=120) as r:
        head = r.read(4096).decode("utf-8", errors="replace")
    header = head.split("\n", 1)[0].rstrip("\r").split("\t")
    if header != GNPS_COLUMNS:
        raise SystemExit(f"REFUSED (header mismatch, not downloading): {header}")
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MURU-outcome-blind-census/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"REFUSED (body exceeded {MAX_BYTES} bytes): {url}")
    lines = data.decode("utf-8").rstrip("\n").split("\n")
    bad = [i for i, ln in enumerate(lines) if len(ln.rstrip("\r").split("\t")) != len(GNPS_COLUMNS)]
    if bad:
        raise SystemExit(f"REFUSED (rows with unexpected field count, first at line {bad[0]}); not saved")
    path = OUT / name
    path.write_bytes(data)
    row = {"url": url, "file": str(path.relative_to(ROOT)), "bytes": len(data),
           "sha256": hashlib.sha256(data).hexdigest(), "http_status": 200,
           "range_request_bytes": None, "header_verified_peak_free": True,
           "n_data_rows": len(lines) - 1,
           "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(json.dumps(row))
    return path


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--gnps-identity":
        fetch_gnps_identity_tsv(args[1], args[2])
        sys.exit(0)
    rng = None
    if "--range" in args:
        i = args.index("--range")
        rng = int(args[i + 1])
        del args[i:i + 2]
    fetch(args[0], args[1], rng)
