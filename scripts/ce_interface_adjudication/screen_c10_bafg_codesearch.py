"""S10 screen C10 (MassBank BAFG): GitHub code-search COUNTS and header-line FRAGMENTS, plus MassBank-data issue/PR
metadata for the BfG submissions. METADATA ONLY.

GitHub legacy code search indexes the default branch (dev, whose BAFG tree equals release 2025.05.1..2026.03).
Text-match fragments are a few header lines around the match. Any fragment line starting with "PK$" (SPLASH, peak
count; the fragments never reached peak rows in the probe) or any line that looks like a peak row (leading whitespace
then numbers) is DROPPED before storage; the number of dropped lines is recorded. total_count values are GitHub's
index counts and may be approximate.

Also stores MassBank-data issues/PRs #156, #245, #246, #248, #249, #275 (title, body, dates) and their comments
(GitHub issue API; public text, no data files).

Usage: python3 screen_c10_bafg_codesearch.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c10_bafg"
DL = OUT / "downloads"
REGISTER = ROOT / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c10_bafg_codesearch.py"
TASK = "S10-C10"
REPO = "MassBank/MassBank-data"
PEAKROW = re.compile(r"^\s+[0-9.]+\s+[0-9.eE+-]+")

# (label, query terms, pages of fragments to keep; 0 = count only)
QUERIES = [
    ("inst_TripleTOF_5600", '"TripleTOF 5600"', 0),
    ("inst_TripleTOF_6600", '"TripleTOF 6600"', 0),
    ("inst_X500R", "X500R", 0),
    ("inst_ZenoTOF", "ZenoTOF", 0),
    ("inst_QTRAP", "QTRAP", 0),
    ("inst_line", "AC$INSTRUMENT", 10),
    ("frag_CID", '"FRAGMENTATION_MODE CID"', 0),
    ("frag_HCD", "HCD", 0),
    ("frag_any", "FRAGMENTATION_MODE", 0),
    ("ce_any", "COLLISION_ENERGY", 0),
    ("ce_spread", "COLLISION_ENERGY_SPREAD", 0),
    ("prec_any", "PRECURSOR_TYPE", 10),
    ("prec_NH4", "PRECURSOR_TYPE NH4", 2),
    ("prec_Na", "PRECURSOR_TYPE Na", 2),
    ("prec_K", "PRECURSOR_TYPE K", 1),
    ("prec_H2O", "PRECURSOR_TYPE H2O", 2),
    ("ion_pos", '"ION_MODE POSITIVE"', 0),
    ("ion_neg", '"ION_MODE NEGATIVE"', 0),
    ("msdp_comment", "MS$DATA_PROCESSING", 2),
]
ISSUES = [156, 245, 246, 248, 249, 275]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def register(name, url, data: bytes, stored_as, kind, extra=None):
    rec = {"fetched_utc": now(), "task": TASK, "name": name, "kind": kind, "source_url": url,
           "size_bytes": len(data), "sha256": sha256(data), "stored_as": stored_as, "script": SCRIPT}
    if extra:
        rec.update(extra)
    with open(REGISTER, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def gh(path, accept=None, paginate=False):
    cmd = ["gh", "api"] + (["-H", f"Accept: {accept}"] if accept else []) + \
          (["--paginate", "--slurp"] if paginate else []) + [path]
    for i in range(6):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            return r.stdout
        err = r.stderr.decode()
        wait = 65 if "rate limit" in err.lower() else 10 * (i + 1)
        print("retry", path, err[:120], "sleep", wait, flush=True)
        time.sleep(wait)
    raise RuntimeError(f"gh api {path}: {err[:300]}")


def main():
    (DL / "github_codesearch").mkdir(parents=True, exist_ok=True)
    (DL / "github_issues").mkdir(parents=True, exist_ok=True)
    summary = {}
    for label, terms, pages in QUERIES:
        q = f"{terms} repo:{REPO} path:BAFG"
        slim = {"query": q, "fetched_utc": now(), "pages": [], "total_count": None, "incomplete_results": None}
        dropped = 0
        raw_all = b""
        for page in range(1, max(pages, 1) + 1):
            per = 100 if pages else 1
            path = f"search/code?q={urllib.parse.quote(q)}&per_page={per}&page={page}"
            raw = gh(path, accept="application/vnd.github.text-match+json" if pages else None)
            raw_all += raw
            d = json.loads(raw)
            slim["total_count"] = d.get("total_count")
            slim["incomplete_results"] = d.get("incomplete_results")
            hits = []
            for it in d.get("items", []):
                frs = []
                for tm in it.get("text_matches", []) if pages else []:
                    keep = []
                    for line in tm.get("fragment", "").split("\n"):
                        if line.startswith("PK$") or PEAKROW.match(line):
                            dropped += 1
                            continue
                        keep.append(line)
                    frs.append("\n".join(keep))
                hits.append({"path": it["path"], "sha": it["sha"], "fragments": frs})
            slim["pages"].append({"page": page, "n_items": len(hits), "hits": hits})
            time.sleep(7)
            if not pages or len(d.get("items", [])) < 100:
                break
        slim["dropped_pk_lines"] = dropped
        b = json.dumps(slim, indent=0).encode()
        rel = DL / f"github_codesearch/{label}.json"
        rel.write_bytes(b)
        register(f"GitHub code search {label}", "https://api.github.com/search/code?q=" + urllib.parse.quote(q),
                 raw_all, str(rel.relative_to(ROOT)),
                 "GitHub code search response (count, and for fragment queries header-line text-match FRAGMENTS; PK$ "
                 "lines dropped before storage, never peak rows); stored slimmed",
                 {"stored_sha256": sha256(b), "total_count": slim["total_count"], "dropped_pk_lines": dropped,
                  "n_hits_kept": sum(p["n_items"] for p in slim["pages"])})
        summary[label] = {"total_count": slim["total_count"], "incomplete": slim["incomplete_results"],
                          "hits_kept": sum(p["n_items"] for p in slim["pages"]), "dropped_pk_lines": dropped}
        print(label, summary[label], flush=True)
    for n in ISSUES:
        ib = gh(f"repos/{REPO}/issues/{n}")
        cb = gh(f"repos/{REPO}/issues/{n}/comments?per_page=100", paginate=True)
        i = json.loads(ib)
        comments = [c for page in json.loads(cb) for c in page]
        slim = {"number": n, "title": i["title"], "state": i["state"], "created_at": i["created_at"],
                "closed_at": i["closed_at"], "merged_at": (i.get("pull_request") or {}).get("merged_at"),
                "user": i["user"]["login"], "body": i["body"],
                "comments": [{"created_at": c["created_at"], "user": c["user"]["login"], "body": c["body"]}
                             for c in comments]}
        b = json.dumps(slim, indent=1).encode()
        rel = DL / f"github_issues/issue_{n}.json"
        rel.write_bytes(b)
        register(f"MassBank-data issue/PR #{n} with comments", f"https://api.github.com/repos/{REPO}/issues/{n}",
                 ib + cb, str(rel.relative_to(ROOT)),
                 "GitHub issue/PR metadata text (title, body, comments; no files, no diffs); stored slimmed",
                 {"stored_sha256": sha256(b), "n_comments": len(comments)})
    (OUT / "codesearch_summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
