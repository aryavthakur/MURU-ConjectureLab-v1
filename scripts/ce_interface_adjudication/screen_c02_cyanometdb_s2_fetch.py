#!/usr/bin/env python3
"""S2 screen C02 (CyanoMetDB in MassBank 2026.03): supplementary metadata-only fetch.

Adds to the earlier S2-C02 fetch (screen_c02_cyanometdb_fetch.py):
  1. Git tree listings (file names + blob sha only, no file contents) of the MassBank-data
     Eawag/ directory at the earlier tags 2023.11 (the release MassSpecGym 1.0 ingested) and
     2025.10 (the last release before PR #366 was merged).  Used to date the first appearance
     of the MSBNK-EAWAG-EC / MSBNK-EAWAG-ED / MSBNK-MLU-ED record files.
  2. GitHub code-search text-match FRAGMENTS for the header keys LICENSE, COPYRIGHT and for
     the token TENTATIVE inside the three CyanoMetDB accession series.  Fragments are header
     lines only; every fragment is checked for 'PK$' and for peak-like lines and the run
     aborts on any hit.

No spectra, no peak arrays, no MGF/MSP/mzML.  Every stored file is appended to
artifacts/ce_interface_adjudication/downloads_register.jsonl.

Usage: screen_c02_cyanometdb_s2_fetch.py
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = "MassBank/MassBank-data"
W = Path(__file__).resolve().parents[2]
OUT = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb/downloads_s2"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
NAME_RE = re.compile(r"MSBNK-(EAWAG-E[CD]|MLU-ED)\d+\.txt")
PEAKLIKE = re.compile(r"^\s*\d+\.\d+\s+\d+(\.\d+)?\s+\d+\s*$", re.M)


def gh(args, accept=None):
    cmd = ["gh", "api"] + args
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    last = ""
    for _ in range(8):
        p = subprocess.run(cmd, capture_output=True, text=True, cwd="/private/tmp")
        if p.returncode == 0:
            return p.stdout
        last = (p.stdout + p.stderr)[:300]
        time.sleep(30 if ("rate limit" in last.lower() or "403" in last) else 8)
    raise RuntimeError("gave up: " + " ".join(cmd) + " :: " + last)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def register(entry):
    with REG.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}

    # ---- 1. Eawag tree listings at earlier tags ----
    for tagname in ["2023.11", "2025.10"]:
        ref_obj = json.loads(gh([f"repos/{REPO}/git/ref/tags/{tagname}"]))["object"]
        if ref_obj["type"] == "tag":  # annotated tag: dereference to the commit
            commit = json.loads(gh([f"repos/{REPO}/git/tags/{ref_obj['sha']}"]))["object"]["sha"]
        else:
            commit = ref_obj["sha"]
        obj = json.loads(gh([f"repos/{REPO}/git/commits/{commit}"]))
        root = json.loads(gh([f"repos/{REPO}/git/trees/{obj['tree']['sha']}"]))
        dirs = {t["path"]: t["sha"] for t in root["tree"]}
        fn_root = OUT / f"massbank_data_root_tree_tag_{tagname}.json"
        fn_root.write_text(json.dumps(root))
        register({"task": "S2-C02", "fetched_utc": now(), "content_class": "metadata_only",
                  "name": fn_root.name,
                  "kind": "GitHub git tree listing of the repository root (directory names + sha only)",
                  "source_url": f"https://api.github.com/repos/{REPO}/git/trees/{obj['tree']['sha']}",
                  "ref": f"tags/{tagname}", "commit": commit,
                  "size_bytes": fn_root.stat().st_size, "sha256": sha(fn_root.read_bytes()),
                  "stored_as": str(fn_root.relative_to(W)),
                  "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_fetch.py"})
        counts = {}
        for d in ("Eawag", "MLU"):
            if d not in dirs:
                counts[d] = None
                continue
            raw = gh([f"repos/{REPO}/git/trees/{dirs[d]}"]).encode()
            t = json.loads(raw)
            assert not t["truncated"]
            fn = OUT / f"massbank_data_{d}_tree_tag_{tagname}.json"
            fn.write_bytes(raw)
            names = [x["path"] for x in t["tree"]]
            counts[d] = {"n_files": len(names),
                         "n_cyanometdb_named": sum(1 for p in names if NAME_RE.fullmatch(p))}
            register({"task": "S2-C02", "fetched_utc": now(), "content_class": "metadata_only",
                      "name": fn.name,
                      "kind": "GitHub git tree listing (file names and blob sha only; no file contents)",
                      "source_url": f"https://api.github.com/repos/{REPO}/git/trees/{dirs[d]}",
                      "ref": f"tags/{tagname}", "commit": commit, "dir": d,
                      "size_bytes": len(raw), "sha256": sha(raw),
                      "stored_as": str(fn.relative_to(W)),
                      "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_fetch.py"})
        log[tagname] = {"commit": commit, "root_dirs": sorted(dirs), "counts": counts}

    # ---- 2. code-search fragments for LICENSE / COPYRIGHT / TENTATIVE ----
    frag_path = OUT / "codesearch_license_tentative.jsonl"
    queries = [("LIC", "LICENSE COPYRIGHT"), ("TENT", "TENTATIVE")]
    prefixes = ["MSBNK-EAWAG-EC", "MSBNK-EAWAG-ED", "MSBNK-MLU-ED"]
    n_calls, total_bytes, hasher = 0, 0, hashlib.sha256()
    cs = []
    with frag_path.open("w") as fh:
        for qid, q in queries:
            for prefix in prefixes:
                raw = gh(["-X", "GET", "search/code",
                          "-f", f"q={q} repo:{REPO} filename:{prefix}",
                          "-f", "per_page=100"],
                         accept="application/vnd.github.text-match+json").encode()
                n_calls += 1
                total_bytes += len(raw)
                hasher.update(raw)
                d = json.loads(raw)
                items = []
                for it in d.get("items", []):
                    frags = [tm["fragment"] for tm in it.get("text_matches", [])]
                    for f in frags:
                        if "PK$" in f or PEAKLIKE.search(f):
                            raise SystemExit(f"ABORT: peak-like content in fragment of {it['path']}")
                    items.append({"path": it["path"], "blob_sha": it["sha"], "fragments": frags})
                rec = {"query_id": qid, "query": q, "prefix": prefix,
                       "total_count": d.get("total_count"),
                       "incomplete_results": d.get("incomplete_results"),
                       "n_items_returned": len(items), "fetched_utc": now(),
                       "response_bytes": len(raw), "response_sha256": sha(raw), "items": items}
                fh.write(json.dumps(rec) + "\n")
                cs.append({k: rec[k] for k in ("query_id", "prefix", "total_count",
                                               "incomplete_results", "n_items_returned")})
                print(qid, prefix, d.get("total_count"), len(items), flush=True)
                time.sleep(8)
    register({"task": "S2-C02", "fetched_utc": now(), "content_class": "metadata_only",
              "name": frag_path.name,
              "kind": ("GitHub code-search API text-match fragments (header lines only, terms "
                       "LICENSE/COPYRIGHT and TENTATIVE); no PK$ peak block (checked per fragment)"),
              "source_url": (f"https://api.github.com/search/code?q=<terms>+repo:{REPO}+filename:<prefix>"
                             " (indexes the default branch dev)"),
              "n_api_calls": n_calls, "size_bytes_raw_responses": total_bytes,
              "sha256_raw_responses_in_order": hasher.hexdigest(),
              "size_bytes": frag_path.stat().st_size, "sha256": sha(frag_path.read_bytes()),
              "stored_as": str(frag_path.relative_to(W)),
              "script": "scripts/ce_interface_adjudication/screen_c02_cyanometdb_s2_fetch.py"})
    log["codesearch"] = cs
    (OUT / "s2_fetch_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps(log, indent=1)[:4000])


if __name__ == "__main__":
    sys.exit(main())
