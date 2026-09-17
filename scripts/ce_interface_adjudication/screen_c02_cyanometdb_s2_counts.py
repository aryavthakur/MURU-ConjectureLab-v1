#!/usr/bin/env python3
"""S2 screen C02: count-only GitHub code-search probes (no text-match fragments at all).

Why count-only: the fragment-returning probe for the token TENTATIVE tripped this screen's own
peak-content guard (a returned fragment contained peak-like lines), so that probe was abandoned
and re-run WITHOUT the text-match Accept header.  Without that header the API returns only file
paths and counts, never file content.

Probes (all restricted to repo MassBank/MassBank-data, default branch dev, which is what code
search indexes):
  TENTATIVE / CONFIDENCE / "CyanoMetDB_ID" / "Level" counts per CyanoMetDB accession series,
  plus the root directory listing of branch dev (directory names only).

Usage: screen_c02_cyanometdb_s2_counts.py
"""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = "MassBank/MassBank-data"
W = Path(__file__).resolve().parents[2]
OUT = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb/downloads_s2"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
PREFIXES = ["MSBNK-EAWAG-EC", "MSBNK-EAWAG-ED", "MSBNK-MLU-ED"]
TERMS = {"TENTATIVE": "TENTATIVE", "CONFIDENCE": "CONFIDENCE",
         "CYANOMETDB_ID": "CyanoMetDB_ID", "LICENSE": "LICENSE"}


def gh(args):
    last = ""
    for _ in range(8):
        p = subprocess.run(["gh", "api"] + args, capture_output=True, text=True, cwd="/private/tmp")
        if p.returncode == 0:
            return p.stdout
        last = (p.stdout + p.stderr)[:300]
        time.sleep(30 if ("rate limit" in last.lower() or "403" in last) else 8)
    raise RuntimeError("gave up: " + " ".join(args) + " :: " + last)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"counts": [], "dev_root_dirs": None}
    raw_all, n_calls = b"", 0
    for label, term in TERMS.items():
        for prefix in PREFIXES:
            raw = gh(["-X", "GET", "search/code", "-f", f"q={term} repo:{REPO} filename:{prefix}",
                      "-f", "per_page=1"]).encode()
            n_calls += 1
            raw_all += raw
            d = json.loads(raw)
            paths = [it["path"] for it in d.get("items", [])]
            res["counts"].append({"term": term, "label": label, "prefix": prefix,
                                  "total_count": d.get("total_count"),
                                  "incomplete_results": d.get("incomplete_results"),
                                  "first_item_path": paths[0] if paths else None})
            print(label, prefix, d.get("total_count"), flush=True)
            time.sleep(8)
    root = json.loads(gh([f"repos/{REPO}/contents?ref=dev"]))
    res["dev_root_dirs"] = sorted(e["name"] for e in root if e["type"] == "dir")
    fn = OUT / "codesearch_counts_only.json"
    fn.write_text(json.dumps(res, indent=1))
    with REG.open("a") as fh:
        fh.write(json.dumps({
            "task": "S2-C02", "fetched_utc": now(), "content_class": "metadata_only",
            "name": fn.name,
            "kind": ("GitHub code-search COUNT-ONLY responses (no text-match header, so no file "
                     "content is returned; total_count plus one matched path per query) and the "
                     "branch-dev root directory listing"),
            "source_url": (f"https://api.github.com/search/code?q=<term>+repo:{REPO}+filename:<prefix>"
                           f" and https://api.github.com/repos/{REPO}/contents?ref=dev"),
            "n_api_calls": n_calls + 1,
            "size_bytes_raw_responses": len(raw_all),
            "sha256_raw_responses_in_order": hashlib.sha256(raw_all).hexdigest(),
            "size_bytes": fn.stat().st_size,
            "sha256": hashlib.sha256(fn.read_bytes()).hexdigest(),
            "stored_as": str(fn.relative_to(W)),
            "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_counts.py",
        }, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
