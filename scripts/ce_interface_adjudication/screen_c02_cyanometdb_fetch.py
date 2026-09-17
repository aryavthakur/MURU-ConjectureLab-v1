#!/usr/bin/env python3
"""S2 screen C02 (CyanoMetDB spectra in MassBank 2026.03): metadata-only fetch.

What this fetches (no spectra, no peak arrays):
  1. GitHub git tree listings (file names + blob sha only) of MassBank/MassBank-data
     directory Eawag/ at tag 2026.03 and at branch dev.
  2. GitHub code-search text-match FRAGMENTS for the 3,126 CyanoMetDB record files
     (MSBNK-EAWAG-EC*, MSBNK-EAWAG-ED*, MSBNK-MLU-ED*). A text-match fragment is the
     matched header line plus at most one neighbouring line. Queried terms are header
     keys only (RECORD_TITLE, INCHIKEY, INSTRUMENT_TYPE, PRECURSOR_TYPE,
     FRAGMENTATION_MODE, RESOLUTION), all of which sit far above the PK$ peak block.
     Every fragment is checked for 'PK$' and for peak-like lines; any hit aborts.

Supplementary Table S4 (np6c00107_si_002.xlsx) and the SI PDF were fetched separately
(Europe PMC supplementaryFiles API zip, figures discarded) and are registered by hand.

Usage: screen_c02_cyanometdb_fetch.py OUTDIR
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
SERIES = ["MSBNK-EAWAG-EC", "MSBNK-EAWAG-ED", "MSBNK-MLU-ED"]
QUERIES = {
    "QA": "RECORD_TITLE INCHIKEY",
    "QB": "INSTRUMENT_TYPE PRECURSOR_TYPE",
    "QC": "FRAGMENTATION_MODE RESOLUTION",
}
NAME_RE = re.compile(r"MSBNK-(EAWAG-E[CD]|MLU-ED)\d+\.txt")
PEAKLIKE = re.compile(r"^\s*\d+\.\d+\s+\d+(\.\d+)?\s+\d+\s*$", re.M)


def gh(args, accept=None):
    cmd = ["gh", "api"] + args
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    last = ""
    for attempt in range(10):
        p = subprocess.run(cmd, capture_output=True, text=True, cwd="/private/tmp")
        if p.returncode == 0:
            return p.stdout
        last = (p.stdout + p.stderr)[:400]
        if "rate limit" in last.lower() or "secondary" in last.lower() or "403" in last:
            time.sleep(45)
        else:
            time.sleep(10)
    raise RuntimeError("gave up: " + " ".join(cmd) + " :: " + last)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    reg = []

    # 1. tree listings
    trees = {}
    for label, ref in [("tag_2026.03", "tags/2026.03"), ("branch_dev", "heads/dev")]:
        commit = json.loads(gh([f"repos/{REPO}/git/ref/{ref}"]))["object"]["sha"]
        root_tree = json.loads(gh([f"repos/{REPO}/git/commits/{commit}"]))["tree"]["sha"]
        root = json.loads(gh([f"repos/{REPO}/git/trees/{root_tree}"]))
        eaw = [t for t in root["tree"] if t["path"] == "Eawag"][0]["sha"]
        raw = gh([f"repos/{REPO}/git/trees/{eaw}"]).encode()
        d = json.loads(raw)
        assert not d["truncated"]
        fn = out / f"massbank_data_Eawag_tree_{label}.json"
        fn.write_bytes(raw)
        trees[label] = {t["path"]: t["sha"] for t in d["tree"]}
        reg.append({
            "fetched_utc": now(), "task": "S2-C02", "name": fn.name,
            "kind": "GitHub git tree listing (file names and blob sha only; no file contents)",
            "source_url": f"https://api.github.com/repos/{REPO}/git/trees/{eaw}",
            "ref": ref, "commit": commit,
            "size_bytes": len(raw), "sha256": sha(raw), "stored_as": str(fn),
        })

    names = sorted(p[:-4] for p in trees["tag_2026.03"] if NAME_RE.fullmatch(p))
    assert len(names) == 3126, len(names)

    def part(prefix, sub, cap=100):
        sub = [n for n in sub if n.startswith(prefix)]
        if len(sub) <= cap:
            return [(prefix, len(sub))] if sub else []
        r = []
        for dgt in "0123456789":
            r += part(prefix + dgt, sub, cap)
        return r

    parts = []
    for base in SERIES:
        parts += part(base, names)

    # 2. code-search fragments (resumable)
    frag_path = out / "massbank_codesearch_fragments.jsonl"
    done = set()
    if frag_path.exists():
        for line in frag_path.open():
            j = json.loads(line)
            done.add((j["query_id"], j["prefix"]))
    total_bytes, n_calls, hasher = 0, 0, hashlib.sha256()
    # QA and QB for every partition; QC (fragmentation mode, CE string, resolution, scan range) only for a
    # sample of partitions (every 4th partition per series plus the first of each series), to stay within the
    # code-search secondary rate limit. The title (QA) already carries CE, R and the first-mass flag per record.
    qc_sample = set()
    for base in SERIES:
        ps = [p for p, _ in parts if p.startswith(base)]
        qc_sample.update(ps[::4])
    # order: QA everywhere, then QB on the QC sample, then QC sample, then remaining QB
    plan = [(prefix, expected, "QA") for prefix, expected in parts]
    plan += [(prefix, expected, "QB") for prefix, expected in parts if prefix in qc_sample]
    plan += [(prefix, expected, "QC") for prefix, expected in parts if prefix in qc_sample]
    plan += [(prefix, expected, "QB") for prefix, expected in parts if prefix not in qc_sample]
    with frag_path.open("a") as fh:
        for prefix, expected, qid in plan:
            q = QUERIES[qid]
            if True:
                if (qid, prefix) in done:
                    continue
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
                       "expected_files_in_tag_tree": expected,
                       "total_count": d.get("total_count"),
                       "incomplete_results": d.get("incomplete_results"),
                       "fetched_utc": now(), "response_bytes": len(raw),
                       "response_sha256": sha(raw), "items": items}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print(qid, prefix, expected, d.get("total_count"), len(items), flush=True)
                time.sleep(8)
    reg.append({
        "fetched_utc": now(), "task": "S2-C02", "name": frag_path.name,
        "kind": ("GitHub code-search API text-match fragments (header lines only: RECORD_TITLE, INCHIKEY, "
                 "INSTRUMENT_TYPE, PRECURSOR_TYPE, FRAGMENTATION_MODE, RESOLUTION, each +-1 line); "
                 "no PK$ peak block (checked per fragment)"),
        "source_url": f"https://api.github.com/search/code?q=<terms>+repo:{REPO}+filename:<prefix> (indexes default branch dev)",
        "n_api_calls_this_run": n_calls,
        "size_bytes_raw_responses_this_run": total_bytes,
        "sha256_raw_responses_this_run_in_order": hasher.hexdigest() if n_calls else None,
        "stored_as": str(frag_path),
        "stored_sha256": sha(frag_path.read_bytes()),
        "stored_size_bytes": frag_path.stat().st_size,
    })
    (out / "fetch_register_entries.json").write_text(json.dumps(reg, indent=1))
    print("partitions", len(parts), "calls", n_calls)


if __name__ == "__main__":
    main()
