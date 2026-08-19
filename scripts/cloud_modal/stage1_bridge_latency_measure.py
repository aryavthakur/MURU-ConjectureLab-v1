#!/usr/bin/env python3
"""Measure Stage 1 bridge transfer latency on synthetic dummy data (part 8).

finalized local file -> uploaded -> independently remote-verified

Uses the same uploader/verify path as production, one file at a time (not
batched), to measure per-file end-to-end latency realistically.
"""
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage1_bridge_selftest import (  # noqa: E402
    MODAL_PY, MODAL_BIN, CLOUD_MODAL_DIR, UPLOADER, _extract_json_object, _write_complete,
)

TMPROOT = Path("/home/aryav_thakur/.claude/jobs/d40d7453/tmp/bridge_latency")
N = 8


def main():
    if TMPROOT.exists():
        shutil.rmtree(TMPROOT)
    watch_dir = TMPROOT / "watch"
    watch_dir.mkdir(parents=True)
    ledger_path = TMPROOT / "ledger.json"
    run_id = f"latency-{uuid.uuid4().hex[:10]}"

    latencies = []
    for i in range(N):
        content = f"latency probe {i} {uuid.uuid4().hex}".encode()
        t0 = time.time()
        p = _write_complete(watch_dir, f"probe_{i:03d}.json", content)
        sha = hashlib.sha256(content).hexdigest()

        up = subprocess.run(
            [MODAL_PY, str(UPLOADER), "--watch-dir", str(watch_dir), "--run-id", run_id,
             "--ledger-path", str(ledger_path), "--once"],
            capture_output=True, text=True, timeout=180)
        assert up.returncode == 0, up.stderr
        t_uploaded = time.time()

        v = subprocess.run(
            [MODAL_BIN, "run", "-q", "modal_app.py::verify_bridge_file",
             "--remote-path", f"/stage1/{run_id}/probe_{i:03d}.json", "--expected-sha256", sha],
            cwd=str(CLOUD_MODAL_DIR), capture_output=True, text=True, timeout=180)
        assert v.returncode == 0, v.stderr
        result = _extract_json_object(v.stdout)
        t_verified = time.time()
        assert result["match"] is True, result

        latencies.append({"upload_s": round(t_uploaded - t0, 2),
                          "verify_s": round(t_verified - t_uploaded, 2),
                          "total_s": round(t_verified - t0, 2)})
        print(f"[LATENCY] probe {i}: upload={latencies[-1]['upload_s']}s "
             f"verify={latencies[-1]['verify_s']}s total={latencies[-1]['total_s']}s", flush=True)

    totals = [x["total_s"] for x in latencies]
    uploads = [x["upload_s"] for x in latencies]
    print(json.dumps({
        "n": N,
        "upload_median_s": statistics.median(uploads),
        "upload_max_s": max(uploads),
        "end_to_end_median_s": statistics.median(totals),
        "end_to_end_max_s": max(totals),
        "note": ("end-to-end includes a fresh sidecar container cold-start for "
                "verify_bridge_file each time -- a production watcher only "
                "pays the UPLOAD cost per file; verification is a separate, "
                "batchable step, so upload_median_s is the number that matters "
                "for 'does the uploader load the scientific host'."),
    }, indent=2))


if __name__ == "__main__":
    main()
