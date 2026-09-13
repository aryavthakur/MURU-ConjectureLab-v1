"""
Bulk, resumable, provenance-logged retrieval of the 1,514 required MassIVE
mzML files (from the frozen download manifest only -- no discovery by
content). Verifies each downloaded file is structurally an indexedmzML/mzML
document (rejects HTML/error payloads) without decoding any <binary> array.
Polite rate limiting + deterministic resume (skip files already verified).
"""
from __future__ import annotations
import concurrent.futures
import csv
import hashlib
import json
import random
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
DL = REPO / "data/external/msnlib_mzml"
DL.mkdir(parents=True, exist_ok=True)
MANIFEST_CSV = REPO / "MSnLib_required_mzML_downloads.csv"
PROV = REPO / "artifacts/wur_v2/external_msnlib/massive_download_provenance.jsonl"
PROV.parent.mkdir(parents=True, exist_ok=True)

BASE = "https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.MSV000094528/"
MAX_WORKERS = 1          # mod_qos on this host throttles hard on concurrency/rate; single-threaded is deliberate
MAX_RETRIES = 8
INTER_REQUEST_SLEEP_S = 2.5   # polite pacing between requests, independent of retries


def is_mzml(head_bytes: bytes) -> bool:
    s = head_bytes[:600].lstrip()
    return s.startswith(b"<?xml") and (b"mzML" in head_bytes[:2000] or b"indexedmzML" in head_bytes[:2000])


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_one(rel_path: str) -> dict:
    local_name = rel_path.rsplit("/", 1)[-1]
    local_path = DL / local_name
    rec = {"source": "MassIVE", "official_dataset": "MSV000094528", "relative_path": rel_path,
           "local_path": str(local_path.relative_to(REPO)), "attempts": 0, "status": None}
    # deterministic resume: a previously verified file is never re-fetched
    if local_path.exists() and local_path.stat().st_size > 0:
        try:
            with local_path.open("rb") as fh:
                head = fh.read(2000)
            if is_mzml(head):
                rec.update(status="already_present_verified", bytes=local_path.stat().st_size,
                           sha256=sha256_file(local_path))
                return rec
        except Exception:
            pass
    url = BASE + rel_path
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        rec["attempts"] = attempt
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MURU-v2-confirmation/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if not is_mzml(data):
                last_err = f"non-mzML payload (first bytes: {data[:120]!r})"
                time.sleep(min(15 * attempt, 120) + random.random())
                continue
            local_path.write_bytes(data)
            rec.update(status="downloaded", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            return rec
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                backoff = float(retry_after) if retry_after and retry_after.isdigit() else min(15 * attempt, 120)
                last_err = f"HTTPError 429 (backing off {backoff:.0f}s)"
                time.sleep(backoff)
            else:
                last_err = f"HTTPError {e.code}"
                time.sleep(min(15 * attempt, 120))
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(min(15 * attempt, 120))
    rec.update(status="FAILED", error=last_err)
    return rec


def main():
    with MANIFEST_CSV.open() as f:
        rows = list(csv.DictReader(f))
    rel_paths = sorted({r["filename"] for r in rows})
    print(f"{len(rel_paths)} distinct required MassIVE files", flush=True)

    results = []
    done = 0
    t0 = time.time()
    with PROV.open("a") as prov_f:
        for rp in rel_paths:
            rec = fetch_one(rp)
            prov_f.write(json.dumps(rec) + "\n")
            prov_f.flush()
            results.append(rec)
            done += 1
            if done % 25 == 0 or done == len(rel_paths):
                el = time.time() - t0
                nfail = sum(1 for r in results if r["status"] == "FAILED")
                print(f"{done}/{len(rel_paths)} done, {nfail} failed, {el:.0f}s elapsed", flush=True)
            if rec["status"] not in ("already_present_verified",):
                time.sleep(INTER_REQUEST_SLEEP_S)

    ok = [r for r in results if r["status"] in ("downloaded", "already_present_verified")]
    failed = [r for r in results if r["status"] == "FAILED"]
    print(f"FINAL: {len(ok)} ok, {len(failed)} failed")
    if failed:
        print("failed files:")
        for r in failed:
            print(" ", r["relative_path"], r.get("error"))


if __name__ == "__main__":
    main()
