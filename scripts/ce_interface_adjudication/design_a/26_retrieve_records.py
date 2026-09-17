#!/usr/bin/env python3
"""Design A step 26: retrieve exactly the 69 frozen MassBank Eawag EQ records.

Each record is fetched by the git blob sha recorded for it in the frozen population manifest,
so every retrieved file is byte-verifiable: the sha1 of "blob <len>\\0" + content must equal
the requested blob sha. Nothing else is fetched. No neighbouring record, no alternate release,
no related compound, no additional spectrum.

This script never prints, parses or summarizes record content. It records only accession,
source URL, release, filename, byte size, sha256, blob verification and success or failure.

Once the first record is written, the Design A population is EXPOSED permanently.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STUDY_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
ACCESS_REF = f"refs/muru-access/{STUDY_ID}"
EXECUTE_ENV_VAR = "MURU_CE_ADJUDICATION_EXECUTE"
ROOT = Path(__file__).resolve().parents[3]
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_a"
POP_CSV = STUDY_DIR / "population/design_a_records.csv"
POP_MANIFEST = STUDY_DIR / "population/design_a_manifest_sha256.json"
OUT_DIR = ROOT / "data/massbank/MassBank-data/Eawag"
REG_DIR = STUDY_DIR / "records"
REPO = "MassBank/MassBank-data"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob_sha1(b: bytes) -> str:
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(b))
    h.update(b)
    return h.hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def fetch_blob(sha: str) -> bytes:
    """Fetch one git blob's raw bytes through the authenticated GitHub CLI."""
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/git/blobs/{sha}", "-H", "Accept: application/vnd.github.raw"],
        capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip()[:200])
    return r.stdout


def main() -> int:
    import os
    if os.environ.get(EXECUTE_ENV_VAR) != "1":
        raise SystemExit(f"refusing: set {EXECUTE_ENV_VAR}=1 only for authorized execution")
    if not git("rev-parse", "--verify", FREEZE_REF):
        raise SystemExit(f"refusing: {FREEZE_REF} does not resolve")
    if not git("rev-parse", "--verify", ACCESS_REF):
        raise SystemExit(f"refusing: {ACCESS_REF} does not resolve; the access record must precede retrieval")
    if not git("ls-remote", "origin", ACCESS_REF):
        raise SystemExit(f"refusing: {ACCESS_REF} is not published on origin")

    manifest = json.loads(POP_MANIFEST.read_text())
    recorded = None
    for block in ("outputs_written", "inputs_read", "sha256"):
        d = manifest.get(block, {})
        for k, v in (d.items() if isinstance(d, dict) else []):
            if k.endswith("design_a_records.csv"):
                recorded = v if isinstance(v, str) else v.get("sha256")
    observed = sha256_bytes(POP_CSV.read_bytes())
    if recorded and recorded != observed:
        raise SystemExit(f"refusing: population records csv {observed} != recorded {recorded}")

    rows = list(csv.DictReader(POP_CSV.open()))
    if len(rows) != 69:
        raise SystemExit(f"refusing: expected 69 frozen records, manifest has {len(rows)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REG_DIR.mkdir(parents=True, exist_ok=True)
    register = []
    ok = fail = 0
    for i, row in enumerate(sorted(rows, key=lambda r: r["record_id"]), 1):
        acc, fname, blob, rel = row["record_id"], row["source_file"], row["blob_sha"], row["release"]
        url = f"https://api.github.com/repos/{REPO}/git/blobs/{blob}"
        entry = {"n": i, "accession": acc, "source_url": url, "repo": REPO, "release": rel,
                 "requested_blob_sha1": blob, "filename": fname}
        try:
            content = fetch_blob(blob)
            got = git_blob_sha1(content)
            entry.update({
                "bytes": len(content),
                "sha256": sha256_bytes(content),
                "git_blob_sha1_recomputed": got,
                "blob_sha_verified": got == blob,
                "status": "ok" if got == blob else "blob_sha_mismatch",
            })
            if got != blob:
                fail += 1
            else:
                (OUT_DIR / fname).write_bytes(content)
                ok += 1
        except Exception as exc:
            entry.update({"bytes": None, "sha256": None, "git_blob_sha1_recomputed": None,
                          "blob_sha_verified": False, "status": "fetch_failed",
                          "error": str(exc)[:200]})
            fail += 1
        register.append(entry)
        if i % 10 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)} retrieved, ok={ok} fail={fail}", flush=True)

    cols = ["n", "accession", "source_url", "repo", "release", "requested_blob_sha1",
            "filename", "bytes", "sha256", "git_blob_sha1_recomputed", "blob_sha_verified",
            "status", "error"]
    with (REG_DIR / "retrieval_register.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for e in register:
            w.writerow({c: e.get(c, "") for c in cols})
    summary = {
        "study_id": STUDY_ID,
        "utc_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "access_ref_commit": git("rev-parse", ACCESS_REF),
        "freeze_ref_commit": git("rev-parse", FREEZE_REF),
        "n_requested": len(rows), "n_retrieved_ok": ok, "n_failed": fail,
        "all_blob_shas_verified": all(e["blob_sha_verified"] for e in register),
        "records_dir": str(OUT_DIR.relative_to(ROOT)),
        "scope_statement": ("Exactly the 69 frozen accessions were requested, each by its recorded git blob "
                            "sha. No neighbouring record, alternate release, related compound or additional "
                            "spectrum was fetched."),
        "exposure_statement": ("The Design A population is now EXPOSED permanently. It may never be reused as "
                               "a blind or confirmatory population."),
    }
    (REG_DIR / "retrieval_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"retrieved {ok} of {len(rows)}; failures {fail}; "
          f"all blob shas verified: {summary['all_blob_shas_verified']}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
