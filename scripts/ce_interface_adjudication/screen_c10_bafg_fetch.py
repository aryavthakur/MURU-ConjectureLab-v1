"""S10 screen C10 (MassBank contributor BAFG, SCIEX TripleTOF QTOF CE ladders): METADATA-ONLY fetch.

Outcome-blind CE interface adjudication study. No model is run. No spectrum, peak list, MSP/MGF/JSON/SQL release
asset, record .txt file content, git blob, or MassBank3 /records/{accession}(/simple) response (those carry peaks) is
downloaded.

What is fetched (every object is written under OUT/downloads and registered in downloads_register.jsonl):
  1. GitHub git TREE listings (file names + blob sha + size, no file content) of MassBank/MassBank-data directory
     BAFG at every release tag from 2023.06 on and at branch dev HEAD (root tree listings are used only to find the
     BAFG subtree sha).
  2. GitHub commit LIST (sha, date, message only; the list endpoint carries no diffs) of all commits touching BAFG.
  3. MassBank3 API (https://massbank.eu/MassBank-api) /filter/browse?contributor=BAFG (+ per ion mode) and
     /records/search?contributor=BAFG&ion_mode=M, which returns accession + atomcount only (MassBank3
     api/schemas/SearchResult.yaml; same verification as S3-C03).
  4. MassBank export-service JSON-LD structured metadata per accession
     (https://massbank.eu/MassBank-export/metadata/<accession>): record title (which for BAFG carries the CE), license,
     datePublished, compound name/formula/InChI/SMILES/InChIKey/monoisotopic mass. No peaks. Each response is checked
     (no key mentioning peaks/intensities/mz, and no numeric array) and the run aborts otherwise.

Usage: python3 screen_c10_bafg_fetch.py [--workers 4] [--skip-github] [--skip-api] [--skip-jsonld]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c10_bafg"
DL = OUT / "downloads"
REGISTER = ROOT / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c10_bafg_fetch.py"
TASK = "S10-C10"
REPO = "MassBank/MassBank-data"
DIR = "BAFG"
TAGS = ["2023.06", "2023.09", "2023.11", "2024.06", "2024.11", "2025.05", "2025.05.1", "2025.10", "2026.03"]
API = "https://massbank.eu/MassBank-api"
EXPORT = "https://massbank.eu/MassBank-export"

_reg_lock = threading.Lock()


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def register(name, url, data: bytes, stored_as, kind, extra=None):
    rec = {"fetched_utc": now(), "task": TASK, "name": name, "kind": kind, "source_url": url,
           "size_bytes": len(data), "sha256": sha256(data), "stored_as": stored_as, "script": SCRIPT}
    if extra:
        rec.update(extra)
    with _reg_lock:
        with open(REGISTER, "a") as fh:
            fh.write(json.dumps(rec) + "\n")


def gh_api(path: str, paginate=False) -> bytes:
    cmd = ["gh", "api"] + (["--paginate", "--slurp"] if paginate else []) + [path]
    for i in range(4):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(10 * (i + 1))
    raise RuntimeError(f"gh api {path}: {r.stderr.decode()[:300]}")


def http_get(url: str, accept="application/json", tries=5) -> bytes:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": accept,
                                                       "User-Agent": "metadata-screen/1.0 (no spectra requested)"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                raise
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"GET {url} failed: {last}")


def save(rel: str, data: bytes, gz=False) -> str:
    p = DL / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if gz:
        with gzip.GzipFile(filename="", mode="wb", fileobj=open(p, "wb"), compresslevel=9, mtime=0) as g:
            g.write(data)
    else:
        p.write_bytes(data)
    return str(p.relative_to(ROOT))


def fetch_trees():
    refs = [(t, f"repos/{REPO}/commits/{t}") for t in TAGS] + [("dev", f"repos/{REPO}/commits/dev")]
    info = {}
    seen_sub = {}
    for label, cpath in refs:
        c = json.loads(gh_api(cpath))
        commit_sha, root_tree, cdate = c["sha"], c["commit"]["tree"]["sha"], c["commit"]["committer"]["date"]
        root = json.loads(gh_api(f"repos/{REPO}/git/trees/{root_tree}"))
        sub = {e["path"]: e["sha"] for e in root["tree"] if e["type"] == "tree"}
        bafg = sub.get(DIR)
        info[label] = {"commit": commit_sha, "commit_date": cdate, "root_tree": root_tree, "bafg_tree": bafg}
        if bafg is None or bafg in seen_sub:
            info[label]["same_listing_as"] = seen_sub.get(bafg)
            continue
        p2 = f"repos/{REPO}/git/trees/{bafg}"
        d2 = gh_api(p2)
        t2 = json.loads(d2)
        assert not t2["truncated"], label
        slim = json.dumps([{"path": e["path"], "sha": e["sha"], "size": e.get("size"), "type": e["type"]}
                           for e in t2["tree"]]).encode()
        rel = save(f"github_trees/tree_{label}_BAFG.json.gz", slim, gz=True)
        register(f"tree_{label}_BAFG.json.gz", "https://api.github.com/" + p2, d2, rel,
                 "GitHub git tree listing of MassBank-data/BAFG (names, blob sha, size; no file content); stored "
                 "slimmed and gzipped", {"commit": commit_sha, "n_entries": len(t2["tree"]),
                                         "stored_sha256": sha256((ROOT / rel).read_bytes())})
        seen_sub[bafg] = label
        info[label]["n_entries"] = len(t2["tree"])
    b = json.dumps(info, indent=1).encode()
    save("github_trees/refs_used.json", b)
    return info


def fetch_commit_list():
    p = f"repos/{REPO}/commits?path={DIR}&sha=dev&per_page=100"
    data = gh_api(p, paginate=True)
    pages = json.loads(data)
    slim = [{"sha": x["sha"], "date": x["commit"]["committer"]["date"],
             "author_date": x["commit"]["author"]["date"], "message": x["commit"]["message"]}
            for page in pages for x in page]
    b = json.dumps(slim, indent=1).encode()
    rel = save("github_commits/commits_touching_BAFG.json", b)
    register("commits_touching_BAFG.json", "https://api.github.com/" + p, data, rel,
             "GitHub commit list metadata (no diffs); stored slimmed to sha/date/message",
             {"stored_sha256": sha256(b), "n_commits": len(slim)})
    return len(slim)


def fetch_api():
    accs = []
    for q in ("contributor=BAFG", "contributor=BAFG&ion_mode=POSITIVE", "contributor=BAFG&ion_mode=NEGATIVE"):
        u = f"{API}/filter/browse?{q}"
        d = http_get(u)
        rel = save(f"massbank_api/browse_{q.replace('&', '__').replace('=', '-')}.json", d)
        register(f"MassBank3 API /filter/browse {q}", u, d, rel, "MassBank3 API browse-option counts (no spectra)")
    for m in ("POSITIVE", "NEGATIVE"):
        u = f"{API}/records/search?contributor=BAFG&ion_mode={m}"
        d = http_get(u)
        rel = save(f"massbank_api/search_BAFG__{m}.json", d)
        obj = json.loads(d)
        n = len(obj.get("data") or [])
        register(f"MassBank3 API /records/search contributor=BAFG ion_mode={m}", u, d, rel,
                 "MassBank3 API search result (accession and atomcount only; no spectra)", {"n_accessions": n})
        accs += [(x["accession"], m) for x in obj.get("data") or []]
    return accs


FORBIDDEN_KEY_TOKENS = ("peak", "intensit", "spectrum", "mz")


def check_no_peaks(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = k.lower()
            if any(t in kl for t in FORBIDDEN_KEY_TOKENS):
                raise RuntimeError(f"forbidden key {path}/{k}")
            check_no_peaks(v, path + "/" + k)
    elif isinstance(obj, list):
        if obj and all(isinstance(x, (int, float)) for x in obj):
            raise RuntimeError(f"numeric array at {path}")
        for x in obj:
            check_no_peaks(x, path + "[]")


def fetch_jsonld(accessions, workers):
    target = DL / "massbank_export_jsonld/bafg_export_metadata_jsonld.jsonl.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.parent / "bafg_export_metadata_jsonld.partial.jsonl"
    done = {}
    if partial.exists():
        for line in partial.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["status"] in (200, 404):
                    done[r["accession"]] = r
    todo = [a for a in accessions if a not in done]
    print(f"jsonld: {len(done)} cached, {len(todo)} to fetch", flush=True)
    lock = threading.Lock()

    def one(acc):
        url = f"{EXPORT}/metadata/{acc}"
        try:
            b = http_get(url, accept="application/ld+json")
            obj = json.loads(b)
            check_no_peaks(obj)
            return {"accession": acc, "url": url, "status": 200, "bytes": len(b), "sha256": sha256(b),
                    "fetched_utc": now(), "body": obj}
        except urllib.error.HTTPError as e:
            return {"accession": acc, "url": url, "status": e.code, "bytes": 0, "sha256": None, "fetched_utc": now(),
                    "body": None}

    n = 0
    with open(partial, "a") as fh, ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, a) for a in todo]
        for f in as_completed(futs):
            r = f.result()
            with lock:
                fh.write(json.dumps(r) + "\n")
                done[r["accession"]] = r
                n += 1
                if n % 500 == 0:
                    fh.flush()
                    print(f"  {n}/{len(todo)} {now()}", flush=True)
    rows = [done[a] for a in accessions]
    raw = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()
    with gzip.GzipFile(filename="", mode="wb", fileobj=open(target, "wb"), compresslevel=9, mtime=0) as g:
        g.write(raw)
    gz = target.read_bytes()
    status = {}
    for r in rows:
        status[str(r["status"])] = status.get(str(r["status"]), 0) + 1
    register("bafg_export_metadata_jsonld.jsonl.gz (aggregate of per-accession MassBank export-service JSON-LD)",
             f"{EXPORT}/metadata/<accession> for each of {len(rows)} BAFG accessions (API partitions UNION all tree "
             f"listings)", gz, str(target.relative_to(ROOT)),
             "MassBank export-service JSON-LD structured metadata (record title incl. CE, compound identity; no peaks; "
             "checked per response)",
             {"n_responses": len(rows), "status_counts": status, "sum_response_bytes": sum(r["bytes"] for r in rows),
              "uncompressed_sha256": sha256(raw), "per_response_sha256": "stored inside each JSONL row"})
    partial.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-github", action="store_true")
    ap.add_argument("--skip-api", action="store_true")
    ap.add_argument("--skip-jsonld", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.skip_github:
        print("trees", json.dumps(fetch_trees()), flush=True)
        print("commits", fetch_commit_list(), flush=True)
    accs = []
    if not args.skip_api:
        accs = fetch_api()
        print("api accessions", len(accs), flush=True)
    else:
        for m in ("POSITIVE", "NEGATIVE"):
            obj = json.loads((DL / f"massbank_api/search_BAFG__{m}.json").read_text())
            accs += [(x["accession"], m) for x in obj.get("data") or []]
    allacc = {a for a, _ in accs}
    for p in sorted((DL / "github_trees").glob("tree_*_BAFG.json.gz")):
        for e in json.loads(gzip.decompress(p.read_bytes())):
            if e["type"] == "blob" and e["path"].endswith(".txt"):
                allacc.add(e["path"][:-4])
    allacc = sorted(allacc)
    print("union accessions", len(allacc), flush=True)
    if not args.skip_jsonld:
        fetch_jsonld(allacc, args.workers)
    print("done", now(), flush=True)


if __name__ == "__main__":
    sys.exit(main())
