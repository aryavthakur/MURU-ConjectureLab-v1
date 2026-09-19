#!/usr/bin/env python3
"""High-mass replication, step 05: complete the C02 header harvest (metadata only, no peaks).

The frozen C02 screen (screen_c02_cyanometdb_fetch.py) ran query QC ("FRAGMENTATION_MODE RESOLUTION", which also
returns the adjacent COLLISION_ENERGY line) on only every 4th code-search partition. This step runs the SAME QC
query, with the same peak-content abort, on every partition so that HCD and the 'N % (nominal)' CE field can be
checked for every record. GitHub code search returns text-match fragments of header lines (+-1 line) only; any
fragment containing 'PK$' or a peak-like line aborts the run. No record file is downloaded.

Reuses gh(), QUERIES and PEAKLIKE from the frozen screen fetch script by import.
Output: artifacts/ce_interface_adjudication/high_mass/metadata/qc_fragments_all_partitions.jsonl (resumable).
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("c02fetch", HERE.parent / "screen_c02_cyanometdb_fetch.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

OUT = REPO_ROOT / "artifacts/ce_interface_adjudication/high_mass/metadata/qc_fragments_all_partitions.jsonl"
RECORDS = REPO_ROOT / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb/records.csv"


def partitions(names, cap=100):
    def part(prefix, sub):
        sub = [n for n in sub if n.startswith(prefix)]
        if len(sub) <= cap:
            return [(prefix, len(sub))] if sub else []
        r = []
        for d in "0123456789":
            r += part(prefix + d, sub)
        return r
    out = []
    for base in F.SERIES:
        out += part(base, names)
    return out


def main():
    names = sorted(pd.read_csv(RECORDS)["accession"])
    assert len(names) == 3126
    parts = partitions(names)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        done = {json.loads(line)["prefix"] for line in OUT.open()}
    q = F.QUERIES["QC"]
    with OUT.open("a") as fh:
        for prefix, expected in parts:
            if prefix in done:
                continue
            raw = F.gh(["-X", "GET", "search/code", "-f", f"q={q} repo:{F.REPO} filename:{prefix}",
                        "-f", "per_page=100"], accept="application/vnd.github.text-match+json").encode()
            d = json.loads(raw)
            items = []
            for it in d.get("items", []):
                frags = [tm["fragment"] for tm in it.get("text_matches", [])]
                for f in frags:
                    if "PK$" in f or F.PEAKLIKE.search(f):
                        raise SystemExit(f"ABORT: peak-like content in fragment of {it['path']}")
                items.append({"path": it["path"], "blob_sha": it["sha"], "fragments": frags})
            fh.write(json.dumps({"query_id": "QC", "query": q, "prefix": prefix, "expected_files_in_tag_tree": expected,
                                 "total_count": d.get("total_count"), "incomplete_results": d.get("incomplete_results"),
                                 "fetched_utc": F.now(), "response_bytes": len(raw), "response_sha256": F.sha(raw),
                                 "items": items}) + "\n")
            fh.flush()
            print(prefix, expected, d.get("total_count"), len(items), flush=True)
            time.sleep(8)
    print("partitions", len(parts))


if __name__ == "__main__":
    sys.exit(main())
