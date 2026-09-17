#!/usr/bin/env python3
"""S2 screen C02: backfill the downloads register with the files fetched by the earlier S2-C02 run.

The earlier fetch run (screen_c02_cyanometdb_fetch.py plus a hand fetch of the two supplementary
files) wrote its register entries only to
screen/c02_cyanometdb/downloads/fetch_register_entries.json and never appended them to
artifacts/ce_interface_adjudication/downloads_register.jsonl.  This script appends one line per
stored file, with the sha256 and size RECOMPUTED now from the stored file, and marks each entry
backfilled so the provenance of the timestamps is not overstated.

Usage: screen_c02_cyanometdb_s2_register_backfill.py
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parents[2]
DL = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb/downloads"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"

PRIOR = json.load(open(DL / "fetch_register_entries.json"))
BY_NAME = {e["name"]: e for e in PRIOR}

SI = {
    "np6c00107_si_002.xlsx": ("Supplementary Table S4 (extended): CyanoMetDB compound identities, "
                              "confidence levels, purity, SMILES/InChIKey and MassBank accession lists. "
                              "Metadata table, no spectra."),
    "np6c00107_si_001.pdf": ("Supporting Information PDF (Tables S1-S4 short form, method description). "
                             "Text/tables, no peak lists."),
}
SI_URL = ("https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13200231/supplementaryFiles "
          "(zip; the two supplementary files were extracted, figure files discarded). "
          "Article: J Nat Prod 2026, 89(5):1499-1512, doi 10.1021/acs.jnatprod.6c00107, PMC13200231.")


def sha_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    now = datetime.now(timezone.utc).isoformat()
    lines = []
    for name, entry in BY_NAME.items():
        p = DL / name
        lines.append({
            "task": "S2-C02", "content_class": "metadata_only", "name": name,
            "kind": entry.get("kind"), "source_url": entry.get("source_url"),
            "ref": entry.get("ref"), "commit": entry.get("commit"),
            "fetched_utc": entry.get("fetched_utc"),
            "size_bytes": p.stat().st_size, "sha256": sha_file(p),
            "stored_as": str(p.relative_to(W)),
            "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_fetch.py",
            "registered_utc": now,
            "backfilled": ("registered after the fact by "
                           "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_register_backfill.py; "
                           "fetched_utc, source_url and kind are copied from the fetch run's own "
                           "fetch_register_entries.json, size and sha256 are recomputed from the stored file"),
            "n_api_calls_total_all_runs": entry.get("n_api_calls_total_all_runs"),
            "size_bytes_raw_responses_total_all_runs": entry.get("size_bytes_raw_responses_total_all_runs"),
        })
    for name, kind in SI.items():
        p = DL / name
        lines.append({
            "task": "S2-C02", "content_class": "metadata_only", "name": name, "kind": kind,
            "source_url": SI_URL, "fetched_utc": None,
            "size_bytes": p.stat().st_size, "sha256": sha_file(p),
            "stored_as": str(p.relative_to(W)),
            "script": "hand fetch by the earlier S2-C02 run (no script committed)",
            "registered_utc": now,
            "backfilled": ("registered after the fact by "
                           "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_register_backfill.py; "
                           "the fetch time was not recorded by that run, the source URL is the one named in "
                           "screen_c02_cyanometdb_fetch.py's docstring and was re-confirmed live "
                           "(HTTP 200, content-type application/zip) on 2026-09-15; size and sha256 are "
                           "recomputed from the stored file"),
        })
    with REG.open("a") as fh:
        for line in lines:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
    print(json.dumps([{k: l[k] for k in ("name", "size_bytes", "sha256")} for l in lines], indent=1))


if __name__ == "__main__":
    main()
