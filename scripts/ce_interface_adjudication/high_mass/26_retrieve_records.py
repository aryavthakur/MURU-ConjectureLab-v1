#!/usr/bin/env python3
"""High-mass replication, step 26: retrieve EXACTLY the frozen C02 record files, each by its pinned
MassBank 2026.03 git blob sha, verifying the recomputed blob sha. Reuses fetch_blob and git_blob_sha1
from the Design A retrieval module (pinned by sha256).

Refuses unless MURU_CE_HIGH_MASS_EXECUTE=1, the freeze ref resolves, the access ref resolves and is
published on origin, and the frozen record table matches its recorded sha256.
"""
import csv
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm_constants as C  # noqa: E402

ROOT = HERE.parents[2]
STUDY = ROOT / C.STUDY_DIR_REL
POP_CSV = STUDY / "population/high_mass_records.csv"
POP_MANIFEST = STUDY / "population/high_mass_manifest_sha256.json"
OUT_DIR = ROOT / C.RECORDS_DIR_REL
REG_DIR = STUDY / "records"
DESIGN_A_RETRIEVE = HERE.parent / "design_a/26_retrieve_records.py"


def load_a():
    got = hashlib.sha256(DESIGN_A_RETRIEVE.read_bytes()).hexdigest()
    if got != C.DESIGN_A_SHA256["26_retrieve_records.py"]:
        raise SystemExit("refusing: Design A retrieval module sha256 mismatch")
    spec = importlib.util.spec_from_file_location("a26", DESIGN_A_RETRIEVE)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def main() -> int:
    A = load_a()
    if os.environ.get(C.EXECUTE_ENV_VAR) != "1":
        raise SystemExit(f"refusing: set {C.EXECUTE_ENV_VAR}=1 only for authorized execution")
    for ref in (C.FREEZE_REF, C.ACCESS_REF):
        if not A.git("rev-parse", "--verify", ref):
            raise SystemExit(f"refusing: {ref} does not resolve")
    if not A.git("ls-remote", "origin", C.ACCESS_REF):
        raise SystemExit(f"refusing: {C.ACCESS_REF} is not published on origin")
    rel = str(POP_CSV.relative_to(ROOT))
    recorded = json.loads(POP_MANIFEST.read_text())["outputs_written"][rel]
    if hashlib.sha256(POP_CSV.read_bytes()).hexdigest() != recorded:
        raise SystemExit("refusing: frozen record table sha256 mismatch")
    rows = sorted(csv.DictReader(POP_CSV.open()), key=lambda r: r["record_id"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REG_DIR.mkdir(parents=True, exist_ok=True)
    reg, ok, fail = [], 0, 0
    for i, r in enumerate(rows, 1):
        e = {"n": i, "accession": r["record_id"], "filename": r["source_file"], "requested_blob_sha1": r["blob_sha"],
             "release": "2026.03", "source_url": f"https://api.github.com/repos/{A.REPO}/git/blobs/{r['blob_sha']}"}
        try:
            b = A.fetch_blob(r["blob_sha"])
            got = A.git_blob_sha1(b)
            e.update(bytes=len(b), sha256=A.sha256_bytes(b), git_blob_sha1_recomputed=got,
                     blob_sha_verified=got == r["blob_sha"], status="ok" if got == r["blob_sha"] else "blob_sha_mismatch")
            if got == r["blob_sha"]:
                (OUT_DIR / r["source_file"]).write_bytes(b)
                ok += 1
            else:
                fail += 1
        except Exception as exc:  # noqa: BLE001
            e.update(status="fetch_failed", blob_sha_verified=False, error=str(exc)[:200])
            fail += 1
        reg.append(e)
        if i % 25 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)} ok={ok} fail={fail}", flush=True)
    cols = ["n", "accession", "source_url", "release", "requested_blob_sha1", "filename", "bytes", "sha256",
            "git_blob_sha1_recomputed", "blob_sha_verified", "status", "error"]
    with (REG_DIR / "retrieval_register.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for e in reg:
            w.writerow({c: e.get(c, "") for c in cols})
    (REG_DIR / "retrieval_summary.json").write_text(json.dumps({
        "study_id": C.STUDY_ID, "utc": datetime.now(timezone.utc).isoformat(),
        "freeze_ref_commit": A.git("rev-parse", C.FREEZE_REF), "access_ref_commit": A.git("rev-parse", C.ACCESS_REF),
        "n_requested": len(rows), "n_ok": ok, "n_failed": fail,
        "all_blob_shas_verified": all(e.get("blob_sha_verified") for e in reg),
        "scope": "exactly the frozen accessions, each by its pinned 2026.03 blob sha; nothing else fetched",
        "exposure": "the C02 high-mass population is now EXPOSED permanently"}, indent=1) + "\n")
    print(f"retrieved {ok}/{len(rows)}, failed {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
