"""S8 screen, candidate C08: GNPS REFRAME-POSITIVE-LIBRARY and sibling CMMC-REFRAME-POSITIVE-LIBRARY. FETCH ONLY.

Downloads the GNPS2 processed-library CSV files, which are per-spectrum METADATA tables (no peak arrays: the
header is checked before the body is kept, and the fetch aborts and discards the bytes if any column name looks
like a peak, m/z-array or intensity column). Each file is under the 50 MB policy cap (HEAD content-length
46,165,951 and 49,520,118 bytes on 2026-09-14). One register line per stored file is appended to
artifacts/ce_interface_adjudication/downloads_register.jsonl.

No spectra file (MGF/MSP/mzML/JSON-with-peaks) is fetched. No model is run.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c08_reframe"
DL = OUT / "downloads"
REGISTER = ADJ / "downloads_register.jsonl"
TASK = "S8-C08"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_c08_reframe_fetch.py"
MAX_BYTES = 50_000_000
BASE = "https://external.gnps2.org/processed_gnps_library/"
FILES = [
    ("REFRAME-POSITIVE-LIBRARY.csv", "GNPS2 processed library metadata CSV (per-spectrum metadata, no peaks)"),
    ("CMMC-REFRAME-POSITIVE-LIBRARY.csv", "GNPS2 processed library metadata CSV (per-spectrum metadata, no peaks)"),
]
PEAK_COL = re.compile(r"peak|mz_array|m/z array|intensit|^mzs$|^mz$|spectrum_json|peaks_json", re.I)


def append_register(rec: dict) -> None:
    line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(REGISTER, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def fetch_csv() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    for name, desc in FILES:
        url = BASE + name
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
        with urllib.request.urlopen(req, timeout=300) as r:
            head = r.read(4096)
            hdr = next(csv.reader(io.StringIO(head.decode("utf-8", "replace").split("\n", 1)[0])))
            bad = [c for c in hdr if PEAK_COL.search(c)]
            if bad:
                raise SystemExit(f"{name}: peak-like columns {bad}; aborted, nothing stored")
            body = head + r.read(MAX_BYTES + 1 - len(head))
            final_url = r.geturl()
            last_mod = r.headers.get("Last-Modified")
        if len(body) > MAX_BYTES:
            raise SystemExit(f"{name}: exceeds size cap; nothing stored")
        (DL / name).write_bytes(body)
        rec = {
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
            "task": TASK,
            "name": f"{name} ({desc}; header columns: {','.join(hdr)}; Last-Modified {last_mod})",
            "source_url": url,
            "final_url": final_url if final_url != url else None,
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "stored_as": str((DL / name).relative_to(ROOT)),
            "script": SCRIPT_REL,
        }
        append_register(rec)
        print(name, len(body), rec["sha256"][:16], len(hdr), "columns")


SERVLET = [
    ("gnps_libraryservlet_REFRAME-POSITIVE-LIBRARY.json",
     "https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library=REFRAME-POSITIVE-LIBRARY",
     "GNPS LibraryServlet library metadata listing (JSON: source_file, task, create_time, PI, Data_Collector, "
     "Instrument, Adduct, Smiles, INCHI per record); peaks_json verified null for every record; no peak arrays"),
]
# CMMC-REFRAME-POSITIVE-LIBRARY on the same servlet returned HTTP 500 on 2026-09-14 (HEAD), so it is not fetched.


def fetch_servlet() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    for name, url, desc in SERVLET:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
        with urllib.request.urlopen(req, timeout=600) as r:
            data = r.read(MAX_BYTES + 1)
            final_url = r.geturl()
        if len(data) > MAX_BYTES:
            raise SystemExit(f"{name}: exceeds size cap; nothing stored")
        # the servlet body is not valid UTF-8 (mixed latin-1 bytes); raw bytes are stored unchanged
        spectra = json.loads(data.decode("utf-8", "replace"), strict=False)["spectra"]
        nonnull = sum(1 for s in spectra if s.get("peaks_json") not in (None, "null", ""))
        if nonnull:
            raise SystemExit(f"{name}: {nonnull} non-null peaks_json; discarded, nothing stored")
        (DL / name).write_bytes(data)
        rec = {
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
            "task": TASK,
            "name": f"{name} ({desc}; {len(spectra)} records)",
            "source_url": url,
            "final_url": final_url if final_url != url else None,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "stored_as": str((DL / name).relative_to(ROOT)),
            "script": SCRIPT_REL + " --servlet",
        }
        append_register(rec)
        print(name, len(data), rec["sha256"][:16], len(spectra), "records")


def _get(url: str, timeout: int = 300) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(MAX_BYTES + 1)
        final = r.geturl()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{url}: exceeds size cap; nothing stored")
    return data, final


def _store(name: str, url: str, desc: str, data: bytes, final: str, mode: str) -> None:
    low = name.lower()
    assert not low.endswith((".mzxml", ".mzml", ".mgf", ".msp", ".raw", ".hdf5", ".h5")), name
    (DL / name).write_bytes(data)
    append_register({
        "fetched_utc": datetime.now(timezone.utc).isoformat(), "task": TASK, "name": f"{name} ({desc})",
        "source_url": url, "final_url": final if final != url else None, "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(), "stored_as": str((DL / name).relative_to(ROOT)),
        "script": SCRIPT_REL + " " + mode})
    print(name, len(data), hashlib.sha256(data).hexdigest()[:16])


def fetch_provenance() -> None:
    """Small provenance metadata: MassIVE dataset records, dataset file listing (names/sizes only), and the GNPS
    library-upload task status and parameters for every task id in the REFRAME LibraryServlet listing."""
    DL.mkdir(parents=True, exist_ok=True)
    msv = "MSV000093469"
    items = [
        (f"massive_proxi_{msv}.json", f"https://massive.ucsd.edu/ProteoSAFe/proxi/v0.1/datasets/{msv}",
         "MassIVE PROXI dataset metadata JSON (title, instrument, contacts, publications)"),
        (f"massive_massiveinformation_{msv}.json",
         f"https://massive.ucsd.edu/ProteoSAFe/MassiveServlet?function=massiveinformation&massiveid={msv}",
         "MassIVE dataset information JSON (DOI, file count, size, create task, keywords)"),
        (f"gnps2_datasetcache_filelist_{msv}.csv",
         f"https://datasetcache.gnps2.org/datasette/database/filename.csv?_sort=filepath&dataset__exact={msv}&_size=max",
         "GNPS2 dataset cache file listing (file paths, sizes, create times only; no file contents)"),
    ]
    for name, url, desc in items:
        data, final = _get(url)
        _store(name, url, desc, data, final, "--provenance")
    spectra = json.loads((DL / SERVLET[0][0]).read_bytes().decode("utf-8", "replace"), strict=False)["spectra"]
    tasks = sorted({s["task"] for s in spectra})
    print("distinct upload tasks:", len(tasks))
    for t in tasks:
        for kind, url in [("status", f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={t}"),
                          ("params", f"https://gnps.ucsd.edu/ProteoSAFe/ManageParameters?task={t}")]:
            data, final = _get(url)
            ext = "json" if kind == "status" else "xml"
            _store(f"gnps_task_{t}_{kind}.{ext}", url,
                   f"GNPS library-upload task {kind} ({'workflow, description, user, create time' if kind == 'status' else 'workflow parameters: annotation table path, reanalyzed MassIVE dataset, input mzML path mapping (paths only)'})",
                   data, final, "--provenance")


def fetch_listing() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    url = "https://external.gnps2.org/gnpslibrary"
    data, final = _get(url)
    _store("gnps2_external_gnpslibrary_listing.html", url,
           "GNPS2 external library listing page (library names, link paths, processing pipeline labels; no spectra)",
           data, final, "--listing")


if __name__ == "__main__":
    import sys
    if "--listing" in sys.argv:
        fetch_listing()
        raise SystemExit(0)
    if "--provenance" in sys.argv:
        fetch_provenance()
        raise SystemExit(0)
    if "--servlet" in sys.argv:
        fetch_servlet()
    else:
        fetch_csv()  # run once on 2026-09-14 (default mode)
