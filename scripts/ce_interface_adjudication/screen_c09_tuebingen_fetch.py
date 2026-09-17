"""S9 screen, candidate C09: GNPS TUEBINGEN-NATURAL-PRODUCT-COLLECTION. FETCH ONLY (metadata).

Modes (each run appends one register line per stored file to
artifacts/ce_interface_adjudication/downloads_register.jsonl):
  --servlet     GNPS LibraryServlet JSON listing for the library. Stored only if peaks_json is null for every record
                (abort and discard otherwise). No peak arrays.
  --provenance  GNPS library-upload task status JSON and task params XML (paths only) for every task id in the
                listing, plus MassIVE dataset metadata JSON and the GNPS2 dataset-cache file LISTING (names, sizes,
                times only) for any MassIVE accession named in those params.
  --get NAME URL DESC   one small metadata file (refuses spectra-like extensions and anything over 50 MB).

Why no processed CSV: https://external.gnps2.org/processed_gnps_library/TUEBINGEN-NATURAL-PRODUCT-COLLECTION.csv
returned HTTP 404 on 2026-09-14 and the GNPS2 library page lists processed CSVs for 25 other files only.
No spectra file (MGF/MSP/mzML/mzXML/RAW/JSON-with-peaks) is fetched. No model is run.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c09_tuebingen"
DL = OUT / "downloads"
REGISTER = ADJ / "downloads_register.jsonl"
TASK = "S9-C09"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_c09_tuebingen_fetch.py"
MAX_BYTES = 50_000_000
LIB = "TUEBINGEN-NATURAL-PRODUCT-COLLECTION"
SERVLET_NAME = f"gnps_libraryservlet_{LIB}.json"
SPECTRA_EXT = (".mzxml", ".mzml", ".mgf", ".msp", ".raw", ".hdf5", ".h5", ".d", ".wiff", ".mzdata", ".cdf")


def append_register(rec: dict) -> None:
    line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(REGISTER, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def _get(url: str, timeout: int = 600) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(MAX_BYTES + 1)
        final = r.geturl()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{url}: exceeds size cap; nothing stored")
    return data, final


def _store(name: str, url: str, desc: str, data: bytes, final: str, mode: str) -> None:
    assert not name.lower().endswith(SPECTRA_EXT), name
    DL.mkdir(parents=True, exist_ok=True)
    (DL / name).write_bytes(data)
    append_register({
        "fetched_utc": datetime.now(timezone.utc).isoformat(), "task": TASK, "name": f"{name} ({desc})",
        "source_url": url, "final_url": final if final != url else None, "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(), "stored_as": str((DL / name).relative_to(ROOT)),
        "script": SCRIPT_REL + " " + mode})
    print(name, len(data), hashlib.sha256(data).hexdigest()[:16])


def fetch_servlet() -> None:
    url = f"https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library={LIB}"
    data, final = _get(url)
    spectra = json.loads(data.decode("utf-8", "replace"), strict=False)["spectra"]
    nonnull = sum(1 for s in spectra if s.get("peaks_json") not in (None, "null", ""))
    if nonnull:
        raise SystemExit(f"{nonnull} non-null peaks_json; discarded, nothing stored")
    _store(SERVLET_NAME, url,
           "GNPS LibraryServlet library metadata listing (JSON, one record per library spectrum: identity, "
           "source_file, task, create_time, PI, Data_Collector, Instrument, Ion_Source, Adduct, Precursor_MZ, "
           f"Smiles, INCHI); peaks_json verified null for every record; no peak arrays; {len(spectra)} records",
           data, final, "--servlet")


def fetch_provenance() -> None:
    spectra = json.loads((DL / SERVLET_NAME).read_bytes().decode("utf-8", "replace"), strict=False)["spectra"]
    tasks = sorted({s["task"] for s in spectra if s.get("task")})
    print("distinct upload tasks:", len(tasks))
    msvs: set[str] = set()
    for t in tasks:
        for kind, url in [("status", f"https://gnps.ucsd.edu/ProteoSAFe/status_json.jsp?task={t}"),
                          ("params", f"https://gnps.ucsd.edu/ProteoSAFe/ManageParameters?task={t}")]:
            data, final = _get(url)
            ext = "json" if kind == "status" else "xml"
            _store(f"gnps_task_{t}_{kind}.{ext}", url,
                   f"GNPS library-upload task {kind} ("
                   + ("workflow, description, user, create time" if kind == "status" else
                      "workflow parameters: annotation table path, input file path mapping (paths only)") + ")",
                   data, final, "--provenance")
            msvs |= set(re.findall(r"MSV\d{9}", data.decode("utf-8", "replace")))
    for s in spectra:
        msvs |= set(re.findall(r"MSV\d{9}", json.dumps(s)))
    print("MassIVE accessions referenced:", sorted(msvs))
    for msv in sorted(msvs):
        for name, url, desc in [
            (f"massive_proxi_{msv}.json", f"https://massive.ucsd.edu/ProteoSAFe/proxi/v0.1/datasets/{msv}",
             "MassIVE PROXI dataset metadata JSON (title, instrument, contacts, publications)"),
            (f"massive_massiveinformation_{msv}.json",
             f"https://massive.ucsd.edu/ProteoSAFe/MassiveServlet?function=massiveinformation&massiveid={msv}",
             "MassIVE dataset information JSON (DOI, file count, size, create task, keywords)"),
            (f"gnps2_datasetcache_filelist_{msv}.csv",
             f"https://datasetcache.gnps2.org/datasette/database/filename.csv?_sort=filepath&dataset__exact={msv}&_size=max",
             "GNPS2 dataset cache file listing (file paths, sizes, create times only; no file contents)"),
        ]:
            try:
                data, final = _get(url)
            except Exception as e:  # noqa: BLE001
                print("FAILED", url, e)
                continue
            _store(name, url, desc, data, final, "--provenance")


if __name__ == "__main__":
    if "--servlet" in sys.argv:
        fetch_servlet()
    elif "--provenance" in sys.argv:
        fetch_provenance()
    elif "--get" in sys.argv:
        i = sys.argv.index("--get")
        name, url, desc = sys.argv[i + 1:i + 4]
        data, final = _get(url)
        _store(name, url, desc, data, final, "--get")
    else:
        raise SystemExit(__doc__)
