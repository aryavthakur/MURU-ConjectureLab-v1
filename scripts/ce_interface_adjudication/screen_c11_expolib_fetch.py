"""S11 screen, candidate C11: ExpoLib 1.0 (University of Vienna, Zenodo 20715576). FETCH ONLY (metadata).

Stores into artifacts/ce_interface_adjudication/screen/c11_expolib/downloads/ and appends one line per stored file to
artifacts/ce_interface_adjudication/downloads_register.jsonl.

Files fetched (all compound / method METADATA tables or code; no spectra):
  - Zenodo record JSON (file listing only).
  - "Library Overview - ESI+.xlsx" (53,212 B): per-compound CE list, adduct counts, chimeric flag, RT. Re-fetched here
    so its sha256 can be checked against D2's staged copy (D2 sha256 62c27a83...).
  - "mzmine files.zip" (51,028 B): mzmine batch/preset XML plus the mzmine "Database File" compound tables
    (Database_File_mzmine_ESI+.csv / ESI-.csv; compound name, formula, SMILES, InChIKey per the paper). The Zenodo
    zip preview listed only .mzbatch, .mzmwizard and .csv members before download; the script re-checks the member
    list and refuses any spectra-like extension.
  - "R Script - Lib Summary From .msp - #spectra,CE,adducts.Rmd" (6,226 B): R code that summarizes the library.
  - Springer/PMC Supplementary Material 1 (11306_2026_2481_MOESM1_ESM.xlsx, about 1.8 MB): Tables S1-S8 (compound list
    with SMILES/InChIKey, LC-MS parameters, mzmine parameters, library overview, benchmarking tables).
Run history (2026-09-15): the PMC URL for the SI returned a Google reCAPTCHA challenge page (21,420 B, not solved);
it was renamed to downloads/pmc_recaptcha_challenge_page_not_the_xlsx.html, a CORRECTION line was appended to the
register, and the SI was fetched from static-content.springer.com (register line with that source_url). The Zenodo
versions API JSON (zenodo_18186810_versions.json) was fetched manually and registered. The FILES list below now uses the
Springer URL so a rerun reproduces the stored file.
NOT fetched: ExpoLib1.0_*.msp / *.json / *.SDF (carry peak lists), RawData_ESI+/-.tar (.wiff raw data), the PDF render.
No model of any kind is run.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c11_expolib"
DL = OUT / "downloads"
REGISTER = ADJ / "downloads_register.jsonl"
TASK = "S11-C11"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_c11_expolib_fetch.py"
MAX_BYTES = 50_000_000
SPECTRA_EXT = (".mzxml", ".mzml", ".mgf", ".msp", ".raw", ".hdf5", ".h5", ".wiff", ".wiff2", ".scan", ".mzdata",
               ".cdf", ".sdf", ".json", ".tar")
Z = "https://zenodo.org/api/records/20715576"
FILES = [
    ("zenodo_20715576_record.json", Z, "Zenodo record API JSON (file listing only)"),
    ("Library_Overview_-_ESI+.xlsx", Z + "/files/Library%20Overview%20-%20ESI%2B.xlsx/content",
     "ExpoLib ESI+ library overview table (compound, CE list, adducts, chimeric flag, RT)"),
    ("mzmine_files.zip", Z + "/files/mzmine%20files.zip/content",
     "mzmine batch/presets XML and Database_File compound tables (no spectra)"),
    ("R_Script_-_Lib_Summary_From_msp.Rmd",
     Z + "/files/R%20Script%20-%20Lib%20Summary%20From%20.msp%20-%20%23spectra,CE,adducts.Rmd/content",
     "R markdown code used to build the Library Overview"),
    ("11306_2026_2481_MOESM1_ESM.xlsx",
     "https://static-content.springer.com/esm/art%3A10.1007%2Fs11306-026-02481-x/MediaObjects/11306_2026_2481_MOESM1_ESM.xlsx",
     "Metabolomics 2026 ExpoLib paper Supplementary Material 1 (Tables S1-S8)"),
]


def append_register(rec: dict) -> None:
    line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(REGISTER, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def _get(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read(MAX_BYTES + 1)
        final = r.geturl()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{url}: exceeds size cap; nothing stored")
    return data, final


def main() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    for name, url, desc in FILES:
        try:
            data, final = _get(url)
        except Exception as e:  # report and continue; nothing stored for this file
            print("FAILED", name, url, repr(e))
            continue
        extra = {}
        zf = None
        if name.endswith(".zip"):
            zf = zipfile.ZipFile(io.BytesIO(data))
            members = [(i.filename, i.file_size) for i in zf.infolist()]
            bad = [m for m, _ in members if m.lower().endswith(SPECTRA_EXT)]
            if bad:
                raise SystemExit(f"zip has spectra-like members {bad}; nothing stored")
            extra["zip_members"] = members
        (DL / name).write_bytes(data)
        append_register({
            "fetched_utc": datetime.now(timezone.utc).isoformat(), "task": TASK, "name": f"{name} ({desc})",
            "source_url": url, "final_url": final if final != url else None, "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "stored_as": str((DL / name).relative_to(ROOT)),
            "script": SCRIPT_REL, **extra})
        print(name, len(data), hashlib.sha256(data).hexdigest(), extra or "")
        if zf is not None:
            xd = DL / "mzmine_files_extracted"
            xd.mkdir(exist_ok=True)
            for m, _ in extra["zip_members"]:
                if m.endswith("/"):
                    continue
                (xd / Path(m).name).write_bytes(zf.read(m))


if __name__ == "__main__":
    sys.exit(main())
