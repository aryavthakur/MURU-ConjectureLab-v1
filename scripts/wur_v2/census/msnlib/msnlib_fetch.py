"""Outcome-blind, logged fetcher for the MSnLib identity/metadata census.

Every fetch goes through `fetch()`, which
  * refuses any URL whose path looks like a spectral/peak container
    (mzML, mzXML, raw, mgf, msp, spectral-library json/parquet file contents,
    zip/tar archives, Zenodo file-content endpoints),
  * refuses anything larger than MAX_BYTES,
  * saves the bytes under data/external/msnlib_metadata/ and appends a
    provenance row (url, file, size, sha256, UTC time) to fetch_log.jsonl.

Usage: python3 msnlib_fetch.py URL NAME
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/recursive-executor-framework-07dd81")
OUT = ROOT / "data" / "external" / "msnlib_metadata"
LOG = OUT / "fetch_log.jsonl"
MAX_BYTES = 99_000_000

DENY = [
    r"\.mz(ml|xml)(\.gz)?(\?|$)", r"\.raw(\?|$)", r"\.wiff", r"\.mgf", r"\.msp(\?|$)",
    r"\.parquet", r"\.sqlite", r"\.h5(\?|$)", r"\.hdf5", r"\.db(\?|$)", r"\.zip(\?|$)",
    r"\.tar", r"\.7z", r"_ms2\.json", r"_msn\.json", r"/files/.+/content", r"/api/records/\d+/files-archive",
    r"\.mzmine", r"\.mzbatch\.zip",
]


def denied(url: str) -> str | None:
    for pat in DENY:
        if re.search(pat, url, flags=re.IGNORECASE):
            return pat
    return None


def log_row(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(json.dumps(row))


def fetch(url: str, name: str, accept: str = "*/*") -> Path:
    pat = denied(url)
    if pat:
        raise SystemExit(f"REFUSED (outcome-integrity denylist '{pat}'): {url}")
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MURU-outcome-blind-census/1.0", "Accept": accept})
    with urllib.request.urlopen(req, timeout=180) as r:
        status = r.status
        clen = r.headers.get("Content-Length")
        if clen and int(clen) > MAX_BYTES:
            raise SystemExit(f"REFUSED (size {clen} > {MAX_BYTES}): {url}")
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"REFUSED (body exceeded {MAX_BYTES} bytes): {url}")
    path = OUT / name
    path.write_bytes(data)
    log_row({"url": url, "file": str(path.relative_to(ROOT)), "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest(), "http_status": status,
             "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    return path


if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
