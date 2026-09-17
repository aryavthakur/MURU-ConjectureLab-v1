"""S3 screen C03: GitHub code-search text-match fragments for AC$ collision-energy / fragmentation-mode strings.

Metadata only. GitHub legacy code search (default branch index of MassBank/MassBank-data) returns short text-match
fragments around the matched term. Only lines beginning with "AC$" (instrument and mass-spectrometry acquisition
fields) or "MS$FOCUSED_ION: PRECURSOR_TYPE" are kept; every other fragment line is discarded before storage (a
fragment never reaches PK$ lines for these terms in practice; the script asserts that no kept line starts with PK$).
Each hit's blob sha is stored so the analysis can test identity with the tag 2023.11 tree.

Queries: for each contributor directory, terms COLLISION_ENERGY and FRAGMENTATION_MODE, pages 1..PAGES (100 per page).
Search API rate limit is 10 requests/minute (authenticated), so the script sleeps 7 s between requests.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c03_massbank_hcd/downloads/github_codesearch"
REGISTER = ROOT / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c03_massbank_hcd_codesearch.py"
CONTRIBUTORS = ["AAFC", "Eawag", "Eawag_Additional_Specs", "HBM4EU", "NaToxAq", "UFZ"]
PAGES = 3


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list dir:page to (re)fetch, e.g. UFZ:1,UFZ:2; appends to the output")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    kept = []
    only = [tuple(x.split(":")) for x in a.only.split(",") if x]
    plan = [(c, str(p)) for c in CONTRIBUTORS for p in range(1, PAGES + 1)] if not only else only
    for c, page in plan:
        page = int(page)
        if True:
            q = f"COLLISION_ENERGY FRAGMENTATION_MODE repo:MassBank/MassBank-data path:{c}"
            args = ["gh", "api", "-X", "GET", "search/code", "-H", "Accept: application/vnd.github.text-match+json",
                    "-f", f"q={q}", "-f", "per_page=100", "-f", f"page={page}"]
            r = subprocess.run(args, capture_output=True)
            if r.returncode != 0:
                print("error", c, page, r.stderr.decode()[:200])
                time.sleep(20)
                continue
            raw = r.stdout
            d = json.loads(raw)
            n_items = len(d.get("items", []))
            for it in d.get("items", []):
                lines = []
                for tm in it.get("text_matches", []):
                    for ln in tm.get("fragment", "").splitlines():
                        s = ln.strip()
                        assert not s.startswith("PK$")
                        if s.startswith("AC$") or s.startswith("MS$FOCUSED_ION: PRECURSOR_TYPE"):
                            lines.append(s)
                kept.append({"contributor_dir": c, "path": it["path"], "blob_sha": it["sha"], "query": q, "page": page,
                             "kept_lines": sorted(set(lines))})
            rec = {"fetched_utc": datetime.now(timezone.utc).isoformat(), "task": "S3-C03",
                   "name": f"GitHub code search text-match response dir={c} page={page} (fragments filtered to AC$ lines before storage)",
                   "kind": "GitHub code-search API metadata response (text-match fragments); raw response not stored",
                   "source_url": "https://api.github.com/search/code?q=" + q.replace(" ", "+") + f"&per_page=100&page={page}",
                   "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                   "stored_as": str((OUT / "codesearch_ac_lines.jsonl").relative_to(ROOT)),
                   "total_count": d.get("total_count"), "incomplete_results": d.get("incomplete_results"),
                   "n_items": n_items, "script": SCRIPT}
            with open(REGISTER, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(c, page, "total", d.get("total_count"), "items", n_items, "incomplete", d.get("incomplete_results"), flush=True)
            time.sleep(10)
    with open(OUT / "codesearch_ac_lines.jsonl", "a" if only else "w") as fh:
        for k in kept:
            fh.write(json.dumps(k) + "\n")
    print("kept", len(kept))


if __name__ == "__main__":
    main()
