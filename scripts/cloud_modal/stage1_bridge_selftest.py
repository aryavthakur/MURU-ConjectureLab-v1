#!/usr/bin/env python3
"""Adversarial self-test for the Stage 1 -> Modal artifact bridge.

Uses ONLY synthetic dummy files -- never real Stage 1 data. Run under the
isolated Modal-CLI venv:
    ~/.venvs/modal-cli/bin/python3 stage1_bridge_selftest.py

Exercises all 11 properties required before the bridge can be trusted (the
original 9 from the operator's spec, plus J and K added after a hostile
review found the concurrency lock and containment guard untested):
  A. local sha256 computed
  B. file uploaded
  C/D. Modal sidecar independently sees and re-hashes it, matching
  E. duplicate uploader invocation creates no duplicate work
  F. an altered same-path source is refused, not overwritten
  G. many files upload together without loss
  H. the sidecar derived/verify function cannot write to the raw mount
  I. resume after an interrupted run loses no completed transfers
  J. two GENUINELY concurrent instances against the same ledger: one runs,
     one is refused (not raced)
  K. a ledger path inside the watch dir is refused at startup
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

MODAL_PY = os.path.expanduser("~/.venvs/modal-cli/bin/python3")
MODAL_BIN = os.path.expanduser("~/.venvs/modal-cli/bin/modal")
CLOUD_MODAL_DIR = Path(__file__).resolve().parent
UPLOADER = CLOUD_MODAL_DIR / "stage1_bridge_uploader.py"

import re as _re


def _extract_json_object(text: str) -> dict:
    """Robustly extract a JSON object from `modal run`'s rich-formatted CLI
    output. Naive `out[start:rindex('}')]` slicing broke on this exact
    output (caught live, see commit history): the CLI interleaves spinner
    control sequences and line-wraps long strings, so the LAST '}' in the
    raw text is not reliably the matching close brace. Fix: strip ANSI
    escapes and carriage returns, find the first '{', then hand the rest to
    the REAL JSON decoder via `raw_decode`, which knows how to find its own
    matching close brace (including inside nested objects and strings) --
    not a smarter guess, the actual parser."""
    clean = _re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text).replace("\r", "")
    start = clean.index("{")
    obj, _ = json.JSONDecoder().raw_decode(clean, start)
    return obj

TMPROOT = Path("/home/aryav_thakur/.claude/jobs/d40d7453/tmp/bridge_selftest")
N_FILES = 25


def _fresh():
    if TMPROOT.exists():
        shutil.rmtree(TMPROOT)
    TMPROOT.mkdir(parents=True)
    watch_dir = TMPROOT / "watch"
    watch_dir.mkdir()
    ledger_path = TMPROOT / "ledger.json"
    return watch_dir, ledger_path


def _write_complete(watch_dir: Path, name: str, content: bytes) -> Path:
    """Mirror the real scientific writer's atomic tmp.replace(ck) pattern."""
    final = watch_dir / name
    tmp = final.with_suffix(final.suffix + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(final)
    return final


def _run_uploader(watch_dir: Path, run_id: str, ledger_path: Path) -> dict:
    p = subprocess.run(
        [MODAL_PY, str(UPLOADER), "--watch-dir", str(watch_dir), "--run-id", run_id,
         "--ledger-path", str(ledger_path), "--once"],
        capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"uploader failed rc={p.returncode}\n{p.stdout}\n{p.stderr}")
    return _extract_json_object(p.stdout)


def _modal_verify(remote_path: str, expected_sha256: str) -> dict:
    p = subprocess.run(
        [MODAL_BIN, "run", "-q", "modal_app.py::verify_bridge_file",
         "--remote-path", remote_path, "--expected-sha256", expected_sha256],
        cwd=str(CLOUD_MODAL_DIR), capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"verify failed rc={p.returncode}\n{p.stdout}\n{p.stderr}")
    return _extract_json_object(p.stdout)


def main() -> None:
    run_id = f"selftest-{uuid.uuid4().hex[:12]}"
    watch_dir, ledger_path = _fresh()
    print(f"[TEST] run_id={run_id}")

    # ---- A, B, G: write N_FILES dummy files, upload them together ----
    files = {}
    for i in range(N_FILES):
        content = f"dummy stage1 bridge selftest content #{i} {uuid.uuid4().hex}".encode()
        p = _write_complete(watch_dir, f"world_{i:03d}.json", content)
        files[str(p)] = {"sha256": hashlib.sha256(content).hexdigest(), "content": content}
    print(f"[TEST] wrote {N_FILES} dummy files (A)")

    result1 = _run_uploader(watch_dir, run_id, ledger_path)
    uploaded = [r for r in result1["pass_results"] if r["status"] == "UPLOADED"]
    assert len(uploaded) == N_FILES, (
        f"G FAILED: expected {N_FILES} uploaded together, got {len(uploaded)}: {result1}")
    print(f"[TEST] PASS B/G: {len(uploaded)}/{N_FILES} uploaded together, none lost")

    # ---- C, D: independently re-hash a sample of files from the sidecar ----
    sample = uploaded[:5] + uploaded[-1:]
    for r in sample:
        v = _modal_verify(r["remote_path"], r["sha256"])
        assert v["exists"], (r, v)
        assert v["match"] is True, ("D FAILED: sidecar re-hash mismatch", r, v)
    print(f"[TEST] PASS C/D: sidecar independently re-hashed {len(sample)} files, all matched")

    ledger = json.loads(ledger_path.read_text())
    for r in uploaded:
        ledger[r["path"]]["verified"] = True
        ledger[r["path"]]["remote_sha256"] = r["sha256"]
    ledger_path.write_text(json.dumps(ledger, indent=2))

    # ---- E: duplicate uploader invocation must not re-upload / re-do work ----
    result2 = _run_uploader(watch_dir, run_id, ledger_path)
    re_uploaded = [r for r in result2["pass_results"] if r["status"] == "UPLOADED"]
    already = [r for r in result2["pass_results"] if r["status"] == "ALREADY_UPLOADED"]
    assert len(re_uploaded) == 0, (
        f"E FAILED: duplicate invocation re-uploaded {len(re_uploaded)} files", re_uploaded)
    assert len(already) == N_FILES, (len(already), N_FILES)
    print(f"[TEST] PASS E: duplicate invocation re-uploaded 0 files, "
         f"{len(already)} correctly short-circuited")

    # ---- F: altered same-path source must be REFUSED, never silently re-uploaded ----
    target = watch_dir / "world_000.json"
    _write_complete(watch_dir, "world_000.json", b"ALTERED CONTENT -- must be refused")
    result3 = _run_uploader(watch_dir, run_id, ledger_path)
    refused = [r for r in result3["pass_results"] if r["path"] == str(target)]
    assert refused and refused[0]["status"] == "REFUSED_SOURCE_CHANGED", \
        ("F FAILED", refused)
    # Confirm the REMOTE object is untouched -- re-verify against the ORIGINAL hash.
    orig_hash = files[str(target)]["sha256"]
    v = _modal_verify(f"/stage1/{run_id}/world_000.json", orig_hash)
    assert v["match"] is True, ("F FAILED: remote object was overwritten", v)
    print("[TEST] PASS F: altered source refused locally; remote object provably untouched")

    # ---- H: the sidecar function must not be able to write into the raw mount ----
    # Real, active probe: a dedicated test-only function DELIBERATELY attempts a
    # write into /raw and reports whether the OS/filesystem blocked it -- not a
    # structural claim, an actual attempted write.
    p = subprocess.run([MODAL_BIN, "run", "-q", "modal_app.py::probe_raw_write_blocked"],
                       cwd=str(CLOUD_MODAL_DIR), capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, (p.stdout, p.stderr)
    v_write = _extract_json_object(p.stdout)
    assert v_write["write_blocked"] is True, ("H FAILED: write to /raw succeeded!", v_write)
    print(f"[TEST] PASS H: active write attempt into /raw was blocked at the OS level "
         f"({v_write['error_type']}), not merely avoided by convention")

    # ---- I: resume after an "interrupted" run loses no completed transfers ----
    watch_dir2, ledger_path2 = TMPROOT / "watch2", TMPROOT / "ledger2.json"
    watch_dir2.mkdir()
    run_id2 = f"selftest-resume-{uuid.uuid4().hex[:12]}"
    batch_a = []
    for i in range(10):
        content = f"resume-test batch A file {i} {uuid.uuid4().hex}".encode()
        p = _write_complete(watch_dir2, f"a_{i:03d}.json", content)
        batch_a.append((str(p), hashlib.sha256(content).hexdigest()))
    r_a = _run_uploader(watch_dir2, run_id2, ledger_path2)  # "killed after batch A"
    assert all(r["status"] == "UPLOADED" for r in r_a["pass_results"])
    for i in range(10, 15):
        content = f"resume-test batch B file {i} {uuid.uuid4().hex}".encode()
        _write_complete(watch_dir2, f"a_{i:03d}.json", content)
    # "restart": fresh process, same ledger path, same watch dir
    r_b = _run_uploader(watch_dir2, run_id2, ledger_path2)
    statuses = {r["path"]: r["status"] for r in r_b["pass_results"]}
    for local_path, _ in batch_a:
        assert statuses[local_path] == "ALREADY_UPLOADED", \
            (f"I FAILED: batch-A file re-uploaded after restart", local_path, statuses[local_path])
    new_uploads = [r for r in r_b["pass_results"] if r["status"] == "UPLOADED"]
    assert len(new_uploads) == 5, (len(new_uploads), r_b)
    print(f"[TEST] PASS I: restart correctly resumed -- 10 pre-restart files untouched "
         f"(ALREADY_UPLOADED), 5 new files uploaded, 0 lost")

    # ---- J: genuine concurrent overlap (not just sequential duplicate invocation) ----
    # Hostile-review finding (2026-08-19): property E above only exercises a
    # SECOND invocation that starts after the first fully exits -- it never
    # tests two instances genuinely overlapping in time, which is exactly the
    # scenario the flock lock (added in response to the same review) exists
    # to guard against. This launches two long-running --watch processes
    # against the SAME ledger truly concurrently via Popen and confirms
    # exactly one acquires the lock; the other must refuse to start, not race.
    watch_dir3, ledger_path3 = TMPROOT / "watch3", TMPROOT / "ledger3.json"
    watch_dir3.mkdir()
    run_id3 = f"selftest-lock-{uuid.uuid4().hex[:12]}"
    proc_a = subprocess.Popen(
        [MODAL_PY, str(UPLOADER), "--watch-dir", str(watch_dir3), "--run-id", run_id3,
         "--ledger-path", str(ledger_path3), "--poll-interval", "2"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)  # let proc_a acquire the lock and enter its watch loop
    proc_b = subprocess.run(
        [MODAL_PY, str(UPLOADER), "--watch-dir", str(watch_dir3), "--run-id", run_id3,
         "--ledger-path", str(ledger_path3), "--once"],
        capture_output=True, text=True, timeout=30)
    proc_a.terminate()
    try:
        proc_a.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc_a.kill()
        proc_a.wait(timeout=10)
    assert proc_b.returncode != 0, \
        ("J FAILED: second concurrent instance was NOT refused -- lock did not hold",
         proc_b.stdout, proc_b.stderr)
    assert "already holds the lock" in proc_b.stderr, \
        ("J FAILED: refused for the wrong reason", proc_b.stderr)
    print("[TEST] PASS J: genuinely concurrent second instance against the same ledger "
         "was refused by the flock lock, not raced")

    # ---- K: containment guard (ledger path must not be inside the watch dir) ----
    bad_watch = TMPROOT / "watch4"
    bad_watch.mkdir()
    bad_ledger = bad_watch / "ledger.json"  # *.json -- would match the default pattern
    p = subprocess.run(
        [MODAL_PY, str(UPLOADER), "--watch-dir", str(bad_watch), "--run-id", "selftest-k",
         "--ledger-path", str(bad_ledger), "--once"],
        capture_output=True, text=True, timeout=30)
    assert p.returncode != 0, ("K FAILED: did not refuse a ledger path inside watch-dir", p.stdout)
    assert "inside" in p.stderr, ("K FAILED: refused for the wrong reason", p.stderr)
    print("[TEST] PASS K: ledger-path-inside-watch-dir misconfiguration correctly refused")

    print(f"\nALL 11 PROPERTIES PASSED (A-K), N_FILES={N_FILES}, run_id={run_id}")


if __name__ == "__main__":
    main()
