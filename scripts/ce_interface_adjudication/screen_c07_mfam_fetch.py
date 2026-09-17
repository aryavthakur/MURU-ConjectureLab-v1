"""S7 screen C07 (mFam consortium MassBank contribution): METADATA-ONLY fetch.

Outcome-blind CE interface adjudication study. No model is run. No spectrum, peak list, MSP/MGF/JSON/SQL release
asset, record .txt file, or /records/{accession}(/simple) API response (those carry peaks) is downloaded.

Stages (each object is written under OUT/downloads and registered in downloads_register.jsonl):
  github   GitHub git TREE listings (names + blob sha only) of MassBank/MassBank-data mFam/ at tag 2025.10
           (commit fd8fb15) and at dev HEAD; commit LIST (sha/date/message, no diffs) for path mFam.
  api      MassBank3 API /metadata, /filter/browse?contributor=mFam and
           /records/search?contributor=mFam&instrument_type=I&ion_mode=M (accession + atomcount only;
           verified by S3-C03 against MassBank3 api/schemas/SearchResult.yaml).
  jsonld   MassBank export-service JSON-LD per accession (record title, compound identity; no peaks), each response
           checked for peak-like keys and numeric arrays (abort otherwise). Same code path as S3-C03.
  tables   Paper SI template xlsx (PMC) and ECharria/mFam-contributions data/mFam_master_raw.csv (compound table).
  codesearch  GitHub code search (REST /search/code with text-match media type) restricted to repo
           MassBank/MassBank-data path:mFam, returning only the matched line FRAGMENTS (never whole files). Any
           fragment containing a PK$ line aborts. Only path, blob sha and fragments are stored.

Usage: python3 screen_c07_mfam_fetch.py STAGE [STAGE ...] [--workers 4] [--query 'label=::=q' ...]
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
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c07_mfam"
DL = OUT / "downloads"
REGISTER = ROOT / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c07_mfam_fetch.py"
TASK = "S7-C07"

REPO = "MassBank/MassBank-data"
TAG = "2025.10"
TAG_COMMIT = "fd8fb15e44035c53c9d937307c04ba62ebec606d"
CONTRIB = "mFam"
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


def gh_api(path: str, paginate=False, headers=()) -> bytes:
    cmd = ["gh", "api"] + (["--paginate", "--slurp"] if paginate else [])
    for h in headers:
        cmd += ["-H", h]
    cmd += [path]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.decode()[:300]} {r.stdout.decode()[:300]}")
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


# ----------------------------------------------------------------------------------------------------------- github
def stage_github():
    tag_commit = json.loads(gh_api(f"repos/{REPO}/git/commits/{TAG_COMMIT}"))
    dev = json.loads(gh_api(f"repos/{REPO}/branches/dev"))
    info = {}
    for label, commit_sha, root_tree in ((TAG, TAG_COMMIT, tag_commit["tree"]["sha"]),
                                         ("dev", dev["commit"]["sha"], dev["commit"]["commit"]["tree"]["sha"])):
        root = json.loads(gh_api(f"repos/{REPO}/git/trees/{root_tree}"))
        sub = {e["path"]: e["sha"] for e in root["tree"] if e["type"] == "tree"}
        p2 = f"repos/{REPO}/git/trees/{sub[CONTRIB]}?recursive=1"
        d2 = gh_api(p2)
        assert not json.loads(d2)["truncated"], label
        rel2 = save(f"github_trees/tree_{label}_{CONTRIB}.json", d2)
        register(f"tree_{label}_{CONTRIB}.json", "https://api.github.com/" + p2, d2, rel2,
                 "GitHub git tree listing (names and blob sha only, no file content)", {"commit": commit_sha})
        info[label] = commit_sha
    save("github_trees/commits_used.json", json.dumps(info, indent=1).encode())
    p = f"repos/{REPO}/commits?path={CONTRIB}&sha=dev&per_page=100"
    data = gh_api(p, paginate=True)
    slim = [{"sha": x["sha"], "date": x["commit"]["committer"]["date"], "author_date": x["commit"]["author"]["date"],
             "message": x["commit"]["message"]} for page in json.loads(data) for x in page]
    b = json.dumps(slim, indent=1).encode()
    rel = save(f"github_commits/commits_{CONTRIB}.json", b)
    register(f"commits_{CONTRIB}.json", "https://api.github.com/" + p, data, rel,
             "GitHub commit list metadata (no diffs); stored slimmed to sha/date/message",
             {"stored_sha256": sha256(b), "n_commits": len(slim)})
    print("github", info, "commits", len(slim), flush=True)


# -------------------------------------------------------------------------------------------------------------- api
def stage_api():
    data = http_get(f"{API}/metadata")
    rel = save("massbank_api/metadata.json", data)
    register("MassBank3 API /metadata", f"{API}/metadata", data, rel, "MassBank3 API metadata response (no spectra)")
    u = f"{API}/filter/browse?contributor={CONTRIB}"
    d = http_get(u)
    rel = save(f"massbank_api/browse_{CONTRIB}.json", d)
    register(f"MassBank3 API /filter/browse contributor={CONTRIB}", u, d, rel,
             "MassBank3 API browse-option counts (no spectra)")
    bo = json.loads(d)
    its = [x["value"] for x in bo["instrument_type"] if x.get("count")]
    modes = [x["value"] for x in bo["ion_mode"] if x.get("count")]
    n = 0
    for it in its:
        for m in modes:
            q = urllib.parse.urlencode({"contributor": CONTRIB, "instrument_type": it, "ion_mode": m})
            u2 = f"{API}/records/search?{q}"
            d2 = http_get(u2)
            k = len(json.loads(d2).get("data") or [])
            if k == 0:
                continue
            rel2 = save(f"massbank_api/search_{CONTRIB}__{it}__{m}.json", d2)
            register(f"MassBank3 API /records/search contributor={CONTRIB} instrument_type={it} ion_mode={m}",
                     u2, d2, rel2, "MassBank3 API search result (accession and atomcount only; no spectra)",
                     {"n_records": k})
            n += k
    print("api partition accessions", n, flush=True)


# ----------------------------------------------------------------------------------------------------------- jsonld
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


def tree_accessions(label=TAG):
    t = json.loads((DL / f"github_trees/tree_{label}_{CONTRIB}.json").read_text())
    return sorted({e["path"].split("/")[-1][:-4] for e in t["tree"] if e["type"] == "blob"
                   and e["path"].endswith(".txt")})


def stage_jsonld(workers, limit=None):
    accessions = sorted(set(tree_accessions(TAG)) | set(tree_accessions("dev")))
    if limit:
        accessions = accessions[:limit]
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
    if limit:
        print("limit mode: partial kept, nothing registered", flush=True)
        return
    rows = [done[a] for a in accessions]
    raw = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()
    with open(target, "wb") as fo, gzip.GzipFile(filename="", mode="wb", fileobj=fo, compresslevel=9, mtime=0) as g:
        g.write(raw)
    gz = target.read_bytes()
    status = {}
    for r in rows:
        status[str(r["status"])] = status.get(str(r["status"]), 0) + 1
    register("export_metadata_jsonld.jsonl.gz (aggregate of per-accession MassBank export-service JSON-LD responses)",
             f"{EXPORT}/metadata/<accession> for each of {len(rows)} accessions in the {TAG}+dev mFam trees",
             gz, str(target.relative_to(ROOT)),
             "MassBank export-service JSON-LD structured metadata (record title, compound identity; no peaks; "
             "checked per response)",
             {"n_responses": len(rows), "status_counts": status, "sum_response_bytes": sum(r["bytes"] for r in rows),
              "uncompressed_sha256": sha256(raw), "per_response_sha256": "stored inside each JSONL row"})
    partial.unlink()
    print("jsonld status", status, flush=True)


# ------------------------------------------------------------------------------------------------------- codesearch
def stage_codesearch(queries):
    """queries: list of (label, q). Stores only text-match fragments + path per hit."""
    for label, q in queries:
        hits = []
        total = None
        raw_all = b""
        for page in range(1, 11):
            path = "search/code?" + urllib.parse.urlencode({"q": q, "per_page": 100, "page": page})
            for attempt in range(8):
                try:
                    raw = gh_api(path, headers=("Accept: application/vnd.github.text-match+json",))
                    break
                except RuntimeError as e:
                    msg = str(e).lower()
                    if ("rate limit" in msg or "403" in msg or "secondary" in msg or "429" in msg or "timeout" in msg
                            or "tls" in msg or "connection" in msg or "502" in msg or "503" in msg):
                        time.sleep(65)
                        continue
                    raise
            else:
                raise RuntimeError("code search retries exhausted")
            raw_all += raw
            obj = json.loads(raw)
            total = obj.get("total_count")
            items = obj.get("items") or []
            for it in items:
                frags = [m.get("fragment", "") for m in it.get("text_matches") or []]
                for fr in frags:
                    if "PK$" in fr:
                        raise RuntimeError(f"fragment reaches peak block: {it['path']}")
                hits.append({"path": it["path"], "sha": it.get("sha"), "fragments": frags})
            time.sleep(7)
            if len(items) < 100 or len(hits) >= (total or 0):
                break
        b = json.dumps({"query": q, "total_count": total, "n_hits": len(hits),
                        "incomplete_results_or_cap": (total or 0) > len(hits), "hits": hits}, indent=1).encode()
        rel = save(f"github_codesearch/{label}.json", b)
        register(f"GitHub code search fragments {label}", "https://api.github.com/search/code?q=" +
                 urllib.parse.quote(q), raw_all, rel,
                 "GitHub code search text-match FRAGMENTS only (matched header lines; no file content, no peaks; "
                 "fragments checked for PK$ lines); stored slimmed to path/sha/fragments",
                 {"stored_sha256": sha256(b), "total_count": total, "n_hits": len(hits)})
        print("codesearch", label, total, len(hits), flush=True)


# ---------------------------------------------------------------------------------------------------------- tables
TABLES = [
    ("si_template/11306_2026_2480_MOESM1_ESM.xlsx",
     "https://static-content.springer.com/esm/art%3A10.1007%2Fs11306-026-02480-y/MediaObjects/11306_2026_2480_MOESM1_ESM.xlsx",
     "Paper Supplementary Material 1: metadata template spreadsheet with example entries (no spectra)"),
    ("mfam_contributions_repo/mFam_master_raw.csv",
     "https://raw.githubusercontent.com/ECharria/mFam-contributions/main/data/mFam_master_raw.csv",
     "ECharria/mFam-contributions data/mFam_master_raw.csv: accession + SMILES compound table used for paper Fig. 3 "
     "(no spectra)"),
]


def stage_tables(only=None):
    # Note: the PMC-hosted copy (pmc.ncbi.nlm.nih.gov/articles/instance/13328316/bin/...xlsx) returned a 1,817-byte
    # HTML "Preparing to download" bot-challenge page on 2026-09-15; it was registered, renamed to .html, and the
    # Springer static-content copy is used instead. No challenge was attempted.
    for rel, url, kind in TABLES:
        if only and only not in rel:
            continue
        head = http_get(url.replace("raw.githubusercontent.com", "raw.githubusercontent.com"), accept="*/*")
        if len(head) > 50 * 1024 * 1024:
            raise RuntimeError("too large")
        low = head[:200000].lower()
        if rel.endswith(".csv") and (b"peak" in low.split(b"\n")[0] or b"intens" in low.split(b"\n")[0]):
            raise RuntimeError("csv header mentions peaks")
        r = save(rel, head)
        extra = {}
        if "githubusercontent" in url:
            extra["repo_head"] = subprocess.run(["gh", "api", "repos/ECharria/mFam-contributions/commits/main", "--jq",
                                                 ".sha"], capture_output=True).stdout.decode().strip()
        register(rel.split("/")[-1], url, head, r, kind, extra)
        print("table", rel, len(head), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="+")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--query", action="append", default=[], help="label=::=query for codesearch")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for s in args.stages:
        if s == "github":
            stage_github()
        elif s == "api":
            stage_api()
        elif s == "jsonld":
            stage_jsonld(args.workers, args.limit)
        elif s == "tables":
            stage_tables()
        elif s == "si":
            stage_tables("si_template")
        elif s == "codesearch":
            stage_codesearch([tuple(x.split("=::=", 1)) for x in args.query])
        else:
            raise SystemExit(f"unknown stage {s}")


if __name__ == "__main__":
    sys.exit(main())
