"""S3 screen C03 (MassBank 2023.11 in-training Orbitrap HCD contributors): METADATA-ONLY fetch.

Outcome-blind CE interface adjudication study. No model is run. No spectrum, peak list, MSP/MGF/JSON/SQL release
asset, record .txt file, or /records/{accession}(/simple) API response (those carry peaks) is downloaded.

What is fetched (every object is written under OUT/downloads and registered in downloads_register.jsonl):
  1. GitHub git TREE listings (file names + blob sha, no file content) of MassBank/MassBank-data for the six
     contributor directories at tag 2023.11 (commit 9dc52cb) and at branch dev HEAD.
  2. GitHub commit LISTS (sha, date, message only; the list endpoint carries no diffs) touching those directories
     since the 2023.11 tag.
  3. MassBank3 API (https://massbank.eu/MassBank-api) metadata: /metadata, /filter/browse?contributor=X, and
     /records/search?contributor=X&instrument_type=I&ion_mode=M, which returns only accession + atomcount (verified in
     MassBank3 api/schemas/SearchResult.yaml and pkg/database/postgres.go GetAccessionsByFilterOptions:
     "SELECT accession, atomcount FROM browse_options").
  4. MassBank export-service JSON-LD structured metadata per accession
     (https://massbank.eu/MassBank-export/metadata/<accession>). Content verified in MassBank-lib
     src/main/java/massbank/Record.java createStructuredDataJsonArray(): record title, accession, license, date,
     citation, compound name/formula/InChI/SMILES/InChIKey/monoisotopic mass. No peaks. Each response is checked
     (keys must not mention peaks/intensities, and no numeric array may occur) and the run aborts otherwise.

Usage: python3 screen_c03_massbank_hcd_fetch.py [--workers 6] [--skip-github]
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
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c03_massbank_hcd"
DL = OUT / "downloads"
REGISTER = ROOT / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c03_massbank_hcd_fetch.py"
TASK = "S3-C03"

REPO = "MassBank/MassBank-data"
TAG_COMMIT = "9dc52cb29b7ade23e81befc3ce9eb001477ce393"  # tag 2023.11 (annotated tag object 5854dde) -> commit
CONTRIBUTORS = ["AAFC", "Eawag", "Eawag_Additional_Specs", "HBM4EU", "NaToxAq", "UFZ"]
API = "https://massbank.eu/MassBank-api"
EXPORT = "https://massbank.eu/MassBank-export"
SINCE = "2023-11-28T13:00:00Z"

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
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.decode()[:300]}")
    return r.stdout


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


def save(rel: str, data: bytes) -> str:
    p = DL / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return str(p.relative_to(ROOT))


def fetch_trees():
    tag_commit = json.loads(gh_api(f"repos/{REPO}/git/commits/{TAG_COMMIT}"))
    dev = json.loads(gh_api(f"repos/{REPO}/branches/dev"))
    dev_commit = dev["commit"]["sha"]
    info = {}
    for label, commit_sha, root_tree in (("2023.11", TAG_COMMIT, tag_commit["tree"]["sha"]),
                                         ("dev", dev_commit, dev["commit"]["commit"]["tree"]["sha"])):
        path = f"repos/{REPO}/git/trees/{root_tree}"
        data = gh_api(path)
        rel = save(f"github_trees/root_tree_{label}.json", data)
        register(f"root_tree_{label}.json", "https://api.github.com/" + path, data, rel,
                 "GitHub git tree listing (names and blob sha only, no file content)", {"commit": commit_sha})
        sub = {e["path"]: e["sha"] for e in json.loads(data)["tree"] if e["type"] == "tree"}
        for c in CONTRIBUTORS:
            p2 = f"repos/{REPO}/git/trees/{sub[c]}?recursive=1"
            d2 = gh_api(p2)
            assert not json.loads(d2)["truncated"], c
            rel2 = save(f"github_trees/tree_{label}_{c}.json", d2)
            register(f"tree_{label}_{c}.json", "https://api.github.com/" + p2, d2, rel2,
                     "GitHub git tree listing (names and blob sha only, no file content)", {"commit": commit_sha})
        info[label] = commit_sha
    b = json.dumps(info, indent=1).encode()
    save("github_trees/commits_used.json", b)
    return info


def fetch_commit_lists():
    for c in CONTRIBUTORS:
        p = f"repos/{REPO}/commits?path={c}&sha=dev&since={SINCE}&per_page=100"
        data = gh_api(p, paginate=True)
        pages = json.loads(data)
        slim = [{"sha": x["sha"], "date": x["commit"]["committer"]["date"], "message": x["commit"]["message"]}
                for page in pages for x in page]
        b = json.dumps(slim, indent=1).encode()
        rel = save(f"github_commits/commits_since_2023.11_{c}.json", b)
        register(f"commits_since_2023.11_{c}.json", "https://api.github.com/" + p, data, rel,
                 "GitHub commit list metadata (no diffs); stored slimmed to sha/date/message",
                 {"stored_sha256": sha256(b), "n_commits": len(slim)})


def fetch_api_partitions():
    data = http_get(f"{API}/metadata")
    rel = save("massbank_api/metadata.json", data)
    register("MassBank3 API /metadata", f"{API}/metadata", data, rel, "MassBank3 API metadata response (no spectra)")
    n = 0
    for c in CONTRIBUTORS:
        u = f"{API}/filter/browse?contributor={c}"
        d = http_get(u)
        rel = save(f"massbank_api/browse_{c}.json", d)
        register(f"MassBank3 API /filter/browse contributor={c}", u, d, rel,
                 "MassBank3 API browse-option counts (no spectra)")
        bo = json.loads(d)
        its = [x["value"] for x in bo["instrument_type"] if x.get("count")]
        modes = [x["value"] for x in bo["ion_mode"] if x.get("count")]
        for it in its:
            for m in modes:
                u2 = f"{API}/records/search?contributor={c}&instrument_type={it}&ion_mode={m}"
                d2 = http_get(u2)
                rel2 = save(f"massbank_api/search_{c}__{it}__{m}.json", d2)
                register(f"MassBank3 API /records/search contributor={c} instrument_type={it} ion_mode={m}", u2, d2,
                         rel2, "MassBank3 API search result (accession and atomcount only; no spectra)")
                n += len(json.loads(d2).get("data") or [])
    return n


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
    target = DL / "massbank_export_jsonld/export_metadata_jsonld.jsonl.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.parent / "export_metadata_jsonld.partial.jsonl"
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
    register("export_metadata_jsonld.jsonl.gz (aggregate of per-accession MassBank export-service JSON-LD responses)",
             f"{EXPORT}/metadata/<accession> for each of {len(rows)} accessions in the 2023.11 contributor trees",
             gz, str(target.relative_to(ROOT)),
             "MassBank export-service JSON-LD structured metadata (record title, compound identity; no peaks; content "
             "verified against MassBank-lib Record.createStructuredDataJsonArray and checked per response)",
             {"n_responses": len(rows), "status_counts": status, "sum_response_bytes": sum(r["bytes"] for r in rows),
              "uncompressed_sha256": sha256(raw), "per_response_sha256": "stored inside each JSONL row"})
    partial.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--skip-github", action="store_true")
    ap.add_argument("--skip-api", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.skip_github:
        print("trees", fetch_trees(), flush=True)
        fetch_commit_lists()
    if not args.skip_api:
        print("api partition accessions", fetch_api_partitions(), flush=True)
    acc = []
    for c in CONTRIBUTORS:
        t = json.loads((DL / f"github_trees/tree_2023.11_{c}.json").read_text())
        acc += [e["path"][:-4] for e in t["tree"] if e["type"] == "blob" and e["path"].endswith(".txt")]
    acc = sorted(set(acc))
    print("2023.11 accessions", len(acc), flush=True)
    fetch_jsonld(acc, args.workers)
    print("done", now(), flush=True)


if __name__ == "__main__":
    sys.exit(main())
