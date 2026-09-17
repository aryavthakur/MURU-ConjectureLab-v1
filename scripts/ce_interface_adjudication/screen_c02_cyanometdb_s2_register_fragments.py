#!/usr/bin/env python3
"""S2 screen C02: register downloads_s2/codesearch_license_tentative.jsonl.

screen_c02_cyanometdb_s2_fetch.py stores this file incrementally and registers it only after the
whole probe plan finishes.  The plan aborted on purpose: the FIRST text-match response of the
TENTATIVE probe contained a fragment with peak-like lines, so the script's own peak guard raised
and that response was discarded in memory and never written.  The three LICENSE/COPYRIGHT probe
records (100 records each) had already been written to the file, so the file is registered here.

Usage: screen_c02_cyanometdb_s2_register_fragments.py
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parents[2]
P = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb/downloads_s2/codesearch_license_tentative.jsonl"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"


def main():
    recs = [json.loads(l) for l in P.open()]
    entry = {
        "task": "S2-C02", "content_class": "metadata_only", "name": P.name,
        "kind": ("GitHub code-search API text-match FRAGMENTS (record header lines only: "
                 "RECORD_TITLE, DATE, AUTHORS, LICENSE, COPYRIGHT, PUBLICATION, COMMENT); "
                 "each fragment checked for PK$ and peak-like lines before storage"),
        "source_url": ("https://api.github.com/search/code?q=LICENSE+COPYRIGHT+"
                       "repo:MassBank/MassBank-data+filename:<MSBNK-EAWAG-EC|MSBNK-EAWAG-ED|MSBNK-MLU-ED>"
                       " (indexes the default branch dev)"),
        "n_api_calls": len(recs),
        "n_records_with_fragments": sum(r["n_items_returned"] for r in recs),
        "size_bytes": P.stat().st_size,
        "sha256": hashlib.sha256(P.read_bytes()).hexdigest(),
        "stored_as": str(P.relative_to(W)),
        "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_fetch.py",
        "registered_utc": datetime.now(timezone.utc).isoformat(),
        "note": ("registered by screen_c02_cyanometdb_s2_register_fragments.py because the fetch "
                 "script aborted on its own peak guard during the following TENTATIVE probe; that "
                 "probe's response was discarded in memory and never stored"),
    }
    with REG.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    print(json.dumps(entry, indent=1))


if __name__ == "__main__":
    main()
