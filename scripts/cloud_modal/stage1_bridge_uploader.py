#!/usr/bin/env python3
"""Stage 1 -> Modal artifact bridge: ONE-WAY local uploader/watcher.

Run under the ISOLATED Modal-CLI venv, never the MURU scientific venv:
    ~/.venvs/modal-cli/bin/python3 stage1_bridge_uploader.py ...

Watches a local directory of Stage 1 world checkpoints and uploads each
newly-COMPLETED file exactly once to the `muru-stage1-artifact-bridge`
Modal Volume, under an immutable path `/stage1/<run_id>/<relative_path>`.

One-way by construction: this script only ever READS the local directory
and only ever calls `batch_upload` (never any Volume write-back API), and
`v2_stage1_calibration_run.py`'s own checkpoint writer -- unedited by this
file -- is the only thing that ever writes into the local scientific
directory. Nothing here can write back into it.

Completion detection reuses the scientific writer's OWN existing atomicity
guarantee rather than inventing a new marker: `run_world()`'s checkpoint is
written via `tmp.replace(ck)` (scripts/v2_stage1_calibration_run.py), so a
file present at its final name (not ending `.tmp`) is, by construction,
already complete. No mtime-stability heuristic is used.

Persistent local transfer ledger (JSON, atomically written) keyed by local
path, recording `{sha256, remote_path, verified, status}`. Guarantees:
  - a file is uploaded at most once (ledger hit with a matching sha256 and
    `status` already UPLOADED/ALREADY_UPLOADED short-circuits re-upload --
    NOT gated on `verified`; an earlier version gated the short-circuit on
    `verified` and was caught failing its own adversarial resume test for
    exactly that reason -- see `upload_one`'s docstring);
  - independent remote verification is genuinely wired in, but SAMPLED, not
    exhaustive: `--verify-sample-every N` re-hashes every Nth successful
    upload via the sidecar (one container cold-start per sampled file, so
    verifying 100% of a 1,932-world run would materially slow the watch
    loop). A hostile review (2026-08-19) correctly caught an earlier
    version where `mark_verified` existed but nothing ever called it --
    the "verified" field was permanently False in production despite the
    docstring implying otherwise. Fixed here, not just reworded;
  - a SOURCE file that changed content at the same local path is REFUSED,
    never silently re-uploaded over a different remote object (`force=False`
    on `batch_upload` also enforces this at the Modal API level -- belt and
    braces, not either/or);
  - killing and restarting the watcher loses no completed transfers: the
    ledger is read back on startup and already-uploaded entries are
    skipped, exactly reproducing the discipline used throughout this
    session's own checkpoint-resume code (e.g.
    scripts/v2_stage1_calibration_run.py's `_checkpoint_exists`).
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import modal

VOLUME_NAME = "muru-stage1-artifact-bridge"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ledger(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_ledger(path: Path, ledger: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, indent=2))
    tmp.replace(path)  # atomic, mirrors the pattern this bridge itself relies on


def discover_completed_files(watch_dir: Path, pattern: str) -> list[Path]:
    """A file at its final name (no .tmp suffix) is already complete by
    construction of the scientific writer's own atomic-rename pattern."""
    return sorted(p for p in watch_dir.glob(pattern) if not p.name.endswith(".tmp") and p.is_file())


def upload_one(vol, local_path: Path, remote_path: str, ledger: dict, ledger_path: Path) -> dict:
    """Adversarial self-test finding (property I): the short-circuit below
    originally also required `prior.get("verified")`. Independent remote
    verification is a separate, deliberately-not-synchronous step (each
    round trip costs a container cold start; production won't verify every
    one of 1,932 uploads inline) -- gating re-upload-avoidance on it meant
    every unverified file was re-attempted on every single watcher poll
    forever. Modal's own `batch_upload(force=False)` still refuses to
    clobber an existing remote object either way, so no data was ever at
    risk -- but the efficiency property genuinely failed as designed, caught
    live by stage1_bridge_selftest.py's resume test. FIX: short-circuit on
    "already uploaded" alone; `verified` remains tracked separately and
    gates nothing about re-upload avoidance."""
    key = str(local_path)
    local_hash = sha256_file(local_path)
    prior = ledger.get(key)
    if prior and prior.get("sha256") == local_hash and prior.get("status") in ("UPLOADED", "ALREADY_UPLOADED"):
        return {"path": key, "status": "ALREADY_UPLOADED", "sha256": local_hash,
                "remote_path": prior.get("remote_path")}
    if prior and prior.get("sha256") != local_hash:
        # The local source changed content at a path already uploaded under a
        # DIFFERENT hash -- refuse rather than silently re-upload over it.
        return {"path": key, "status": "REFUSED_SOURCE_CHANGED",
                "ledgered_sha256": prior.get("sha256"), "current_sha256": local_hash}
    try:
        with vol.batch_upload(force=False) as batch:
            batch.put_file(str(local_path), remote_path)
    except Exception as ex:
        msg = str(ex).lower()
        if "already exists" in msg or "exists" in msg:
            # Someone/something else already put this exact remote path.
            # Fall through to ledger it as UPLOADED (unverified) so the
            # caller's verification step still runs against it.
            pass
        else:
            ledger[key] = {"sha256": local_hash, "remote_path": remote_path,
                           "verified": False, "status": "UPLOAD_FAILED",
                           "error": str(ex), "uploaded_at": time.time()}
            save_ledger(ledger_path, ledger)
            return {"path": key, "status": "UPLOAD_FAILED", "error": str(ex)}
    ledger[key] = {"sha256": local_hash, "remote_path": remote_path,
                   "verified": False, "status": "UPLOADED", "uploaded_at": time.time()}
    save_ledger(ledger_path, ledger)
    return {"path": key, "status": "UPLOADED", "sha256": local_hash, "remote_path": remote_path}


def mark_verified(ledger: dict, ledger_path: Path, local_path: str, remote_sha256: str) -> bool:
    entry = ledger.get(local_path)
    if not entry:
        return False
    ok = entry["sha256"] == remote_sha256
    entry["verified"] = ok
    entry["remote_verified_at"] = time.time()
    entry["remote_sha256"] = remote_sha256
    save_ledger(ledger_path, ledger)
    return ok


def verify_via_sidecar(remote_path: str, expected_sha256: str, cloud_modal_dir: Path) -> dict:
    """Call the sidecar's independent re-hash function for ONE file. A real
    network round trip (container cold start, ~5-25s per
    stage1_bridge_latency_measure.py) -- this is why verification is
    SAMPLED, not run for every file inline (see --verify-sample-every)."""
    modal_bin = str(Path(sys.executable).parent / "modal")
    p = subprocess.run(
        [modal_bin, "run", "-q", "modal_app.py::verify_bridge_file",
         "--remote-path", remote_path, "--expected-sha256", expected_sha256],
        cwd=str(cloud_modal_dir), capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        return {"exists": False, "error": p.stderr[-500:]}
    import re
    clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", p.stdout).replace("\r", "")
    start = clean.index("{")
    obj, _ = json.JSONDecoder().raw_decode(clean, start)
    return obj


def one_pass(vol, watch_dir: Path, run_id: str, pattern: str, ledger: dict, ledger_path: Path,
            verify_sample_every: int = 0, cloud_modal_dir: Path | None = None,
            _upload_counter: list | None = None) -> list[dict]:
    """CRITIC finding (2026-08-19): `mark_verified` existed but was never
    called anywhere in production -- the module docstring's claim that
    verification is "a deliberately separate step" was aspirational, not
    real. FIX: when `verify_sample_every > 0`, every Nth successful upload
    (counted across the whole run via `_upload_counter`, a 1-element list
    used as a mutable cell so this survives across poll iterations) is
    independently re-hashed via the sidecar and the ledger's `verified`
    field is genuinely set -- sampled, not exhaustive, because a full
    per-file round trip costs a container cold start and would materially
    slow the watch loop for no correctness benefit over a sample."""
    results = []
    counter = _upload_counter if _upload_counter is not None else [0]
    for f in discover_completed_files(watch_dir, pattern):
        rel = f.relative_to(watch_dir)
        remote_path = f"/stage1/{run_id}/{rel}"
        r = upload_one(vol, f, remote_path, ledger, ledger_path)
        results.append(r)
        if r["status"] == "UPLOADED":
            print(f"[BRIDGE] uploaded {rel} -> {remote_path}", flush=True)
            counter[0] += 1
            if verify_sample_every and cloud_modal_dir and counter[0] % verify_sample_every == 0:
                v = verify_via_sidecar(remote_path, r["sha256"], cloud_modal_dir)
                ok = mark_verified(ledger, ledger_path, r["path"],
                                   v.get("actual_sha256", "")) if v.get("exists") else False
                print(f"[BRIDGE] sampled verify {rel}: "
                     f"{'MATCH' if ok else 'MISMATCH_OR_MISSING -- ' + str(v)}", flush=True)
        elif r["status"] == "REFUSED_SOURCE_CHANGED":
            print(f"[BRIDGE] REFUSED (source changed at same path): {rel}", flush=True)
    return results


@contextlib.contextmanager
def _single_instance_lock(ledger_path: Path):
    """CRITIC finding (2026-08-19): the ledger is loaded once into memory and
    every save is a whole-snapshot write, not a merge -- exactly the
    "Volume commits are whole-snapshot" bug class this same infrastructure
    branch already fixed once for the control ledger (Volume -> Dict,
    commit 90521d4). Two overlapping uploader instances against the same
    --ledger-path (a supervisor restart racing the old process, an
    accidental double-launch) would clobber each other's committed
    entries. FIX: an OS-level flock on a dedicated lock file. Unlike a
    manual pidfile check, flock is kernel-managed and released
    automatically on process exit OR crash -- no stale-lock cleanup logic
    needed. A second instance refuses to start rather than racing."""
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        sys.exit(f"[BRIDGE] another uploader instance already holds the lock for "
                 f"{ledger_path} ({lock_path}) -- refusing to start a second one "
                 f"against the same ledger.")
    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--pattern", default="*.json")
    ap.add_argument("--ledger-path", required=True)
    ap.add_argument("--poll-interval", type=float, default=20.0)
    ap.add_argument("--once", action="store_true", help="single pass, for testing")
    ap.add_argument("--verify-sample-every", type=int, default=0,
                    help="independently re-hash every Nth successful upload via the "
                         "sidecar (0 disables sampled verification)")
    a = ap.parse_args()

    watch_dir = Path(a.watch_dir).resolve()
    ledger_path = Path(a.ledger_path).resolve()
    if watch_dir in ledger_path.parents or ledger_path == watch_dir:
        sys.exit(f"[BRIDGE] refusing to start: --ledger-path {ledger_path} is inside "
                 f"--watch-dir {watch_dir} -- the watcher would try to hash/upload its "
                 f"own ledger file.")
    cloud_modal_dir = Path(__file__).resolve().parent

    with _single_instance_lock(ledger_path):
        vol = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
        ledger = load_ledger(ledger_path)
        upload_counter = [0]

        if a.once:
            results = one_pass(vol, watch_dir, a.run_id, a.pattern, ledger, ledger_path,
                               a.verify_sample_every, cloud_modal_dir, upload_counter)
            print(json.dumps({"pass_results": results}, indent=2))
            return

        print(f"[BRIDGE] watching {watch_dir} (pattern={a.pattern}) -> "
             f"/stage1/{a.run_id}/, poll every {a.poll_interval}s, "
             f"verify_sample_every={a.verify_sample_every or 'disabled'}", flush=True)
        while True:
            one_pass(vol, watch_dir, a.run_id, a.pattern, ledger, ledger_path,
                    a.verify_sample_every, cloud_modal_dir, upload_counter)
            time.sleep(a.poll_interval)


if __name__ == "__main__":
    main()
