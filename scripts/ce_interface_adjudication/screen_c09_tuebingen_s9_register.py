"""Append the S9-C09-verify metadata downloads to downloads_register.jsonl and refresh the
C09 output manifest. Metadata only: no spectra file, no peak array was fetched."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

ADJ = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication"
           "/artifacts/ce_interface_adjudication")
OUT = ADJ / "screen" / "c09_tuebingen"
DL = OUT / "downloads"
REG = ADJ / "downloads_register.jsonl"
NOW = "2026-09-15T19:10:00+00:00"

ENTRIES = [
    ("massive_params_MSV000092049.xml",
     "MassIVE submission parameters XML for MSV000092049 (dataset.comments with the stepped-CE statement, "
     "dataset.instrument accession, default.license flag, file mapping paths only; no spectra, no peaks)",
     "https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.MSV000092049/ccms_parameters/params.xml"),
    ("gnps2_gnpslibrary_index_2026-09-15.html",
     "GNPS2 library download index web page, re-fetched 2026-09-15 to confirm which per-library files exist for "
     "TUEBINGEN-NATURAL-PRODUCT-COLLECTION (json/mgf/msp only, no processed CSV); page only, no spectra",
     "https://external.gnps2.org/gnpslibrary"),
    ("github_gnps_ml_processing_GNPS2_Processor.py",
     "GitHub source code: Wang-Bioinformatics-Lab/gnps_ml_processing_workflow GNPS_ML_Processing/bin/GNPS2_Processor.py "
     "(documents that GNPS recovers library collision energy from the original upload file via cvParam MS:1000045)",
     "https://api.github.com/repos/Wang-Bioinformatics-Lab/gnps_ml_processing_workflow/contents/GNPS_ML_Processing/bin/GNPS2_Processor.py"),
    ("github_GNPS_DatasetCache_tasks_compute.py",
     "GitHub source code: Wang-Bioinformatics-Lab/GNPS_DatasetCache tasks_compute.py (shows Top_CEs/Top_CE_Counts in the "
     "uniquemri table come from the PerScanSummarizer workflow output)",
     "https://api.github.com/repos/Wang-Bioinformatics-Lab/GNPS_DatasetCache/contents/tasks_compute.py"),
]

lines = []
for name, kind, url in ENTRIES:
    p = DL / name
    b = p.read_bytes()
    lines.append({
        "fetched_utc": NOW, "task": "S9-C09-verify", "name": f"{name} ({kind})",
        "source_url": url, "size_bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
        "stored_as": str(p.relative_to(ADJ.parents[1])), "content_class": "metadata_only",
    })
# not-stored probes
lines.append({
    "fetched_utc": NOW, "task": "S9-C09-verify",
    "name": "HEAD-only probes, bodies NOT fetched: processed_gnps_data/gnps_cleaned.csv (HTTP 200, content-length "
            "471257140 bytes, above the ~50 MB metadata cap, NOT fetched); processed_gnps_library/"
            "TUEBINGEN-NATURAL-PRODUCT-COLLECTION.csv (HTTP 404, no per-library processed CSV exists); "
            "gnpslibrary/TUEBINGEN-NATURAL-PRODUCT-COLLECTION.json (HTTP 200, 4436703 bytes, spectra-bearing, NOT "
            "fetched). Also: repos Wang-Bioinformatics-Lab/PerScanSummarizer and .../PerScanSummarizer_Workflow "
            "return HTTP 404 (not public).",
    "source_url": "https://external.gnps2.org/", "size_bytes": 0, "sha256": None,
    "stored_as": None, "content_class": "probe_only",
})
# rendered page reads
lines.append({
    "fetched_utc": NOW, "task": "S9-C09-verify",
    "name": "Rendered public web page reads (WebFetch, not stored as files): MassIVE dataset page for MSV000092049 "
            "(license shown as CC0 1.0 Universal, access level 'Partial Public', DOI 10.25345/C5J38KT5R) and "
            "ccms-ucsd.github.io/GNPSDocumentation/gnpslibraries/ (no explicit license stated)",
    "source_url": "https://massive.ucsd.edu/ProteoSAFe/QueryMSV?id=MSV000092049 ; "
                  "https://ccms-ucsd.github.io/GNPSDocumentation/gnpslibraries/",
    "size_bytes": 0, "sha256": None, "stored_as": None, "content_class": "web_page_read",
})

with REG.open("a") as fh:
    for r in lines:
        fh.write(json.dumps(r) + "\n")

man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
       for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "output_manifest_sha256.json"}
(OUT / "output_manifest_sha256.json").write_text(json.dumps(man, indent=1) + "\n")
print(json.dumps(man, indent=1))
print("register lines appended:", len(lines), "total register lines:", sum(1 for _ in REG.open()))
