#!/usr/bin/env python3
"""Adversarial self-test for v2_stage1_calibration_run.py's stall-recovery supervisor.

Motivation, found live not hypothesised: a control run (--limit 1) segfaulted
inside the PySR/Julia/PythonCall bridge, and a synthetic reproduction proved the
consequence -- plain `multiprocessing.Pool.imap_unordered` does not raise or time
out when a worker dies unexpectedly mid-task; it blocks FOREVER waiting for that
one missing result, even while every other task keeps completing normally. For an
unattended 57,960-search run that is a real risk: one crash anywhere silently
hangs the entire run with no exception and no signal to notice except it never
finishing.

Whether the specific crashes observed were a genuine PySR/Julia/PythonCall issue
or resource contention from testing them alongside Stage 0's own memory-hungry
tier-2 phase is NOT established here -- deliberately not claimed either way. This
self-test validates the RECOVERY MECHANISM (run_pool_with_stall_recovery) against
a synthetic crash, independent of root cause, using lightweight fake workers so
it never competes with Stage 0 for real resources.

Worker functions are module-level, not closures: `multiprocessing.Pool` pickles
the task callable by reference even under the `fork` context (its internal task
queue always serializes through `_ForkingPickler`), and a function nested inside
another function cannot be pickled by name. Caught by this self-test itself on
its first run.

Run: /home/aryav_thakur/venv/bin/python3 scripts/v2_stage1_calibration_run_selftest.py
"""
from __future__ import annotations
import json
import os
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import v2_stage1_calibration_run as R  # noqa: E402

TMP = Path(tempfile.gettempdir()) / "v2_stage1_stall_recovery_selftest"


def _fresh(name: str) -> Path:
    d = TMP / name
    if d.exists():
        shutil.rmtree(d)
    R._set_out(str(d))
    return d


# ---------------------------------------------------------------- module-level workers
def _worker_normal(case_id):
    ck = R.CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        return case_id, "CACHED"
    time.sleep(0.05)
    ck.write_text(json.dumps({"case_id": case_id}))
    return case_id, "OK"


_RECOVERABLE_ATTEMPTS_DIR: Path = TMP / "recoverable" / "_attempts"


def _worker_recoverable_crash(case_id):
    ck = R.CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        return case_id, "CACHED"
    marker = _RECOVERABLE_ATTEMPTS_DIR / (case_id.replace("|", "_") + ".attempt")
    if case_id == "PBC|fake|002" and not marker.exists():
        marker.write_text("1")
        os.kill(os.getpid(), signal.SIGSEGV)  # simulate the observed crash, once
    time.sleep(0.05)
    ck.write_text(json.dumps({"case_id": case_id}))
    return case_id, "OK"


def _worker_persistent_crash(case_id):
    ck = R.CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        return case_id, "CACHED"
    if case_id == "PBC|fake|002":
        os.kill(os.getpid(), signal.SIGSEGV)  # crashes on EVERY attempt
    time.sleep(0.05)
    ck.write_text(json.dumps({"case_id": case_id}))
    return case_id, "OK"


def _worker_definitive_failure(case_id):
    """DEF-1 (CRITIC_SCIENCE + CRITIC_GOVERNANCE, both independently reproduced):
    `_worker()` in production has TWO non-crash failure returns
    (`RSS_CEILING_EXCEEDED`, `f"ERROR {type}: {e}"`) and NEITHER writes a
    checkpoint. The first version of this fix treated "no checkpoint" as
    "resubmit" unconditionally, so a case_id returning one of these definitive
    statuses was resubmitted forever -- reproduced live by both reviewers as
    thousands of resubmissions with no termination. This worker reproduces
    that exact shape: a clean, immediate, no-exception failure return, never
    a crash, never a checkpoint."""
    ck = R.CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        return case_id, "CACHED"
    if case_id == "PBC|fake|002":
        return case_id, "RSS_CEILING_EXCEEDED"     # the exact production status
    time.sleep(0.05)
    ck.write_text(json.dumps({"case_id": case_id}))
    return case_id, "OK"


# ---------------------------------------------------------------------- tests
def test_normal_path_zero_false_positive_stalls():
    _fresh("normal")
    R.STALL_TIMEOUT_S, R.POLL_INTERVAL_S = 1200, 1
    R._worker = _worker_normal

    ids = [f"PBC|fake|{i:03d}" for i in range(20)]
    summary = R.run_pool_with_stall_recovery(ids, workers=5)
    assert summary["pool_restarts"] == 0, summary
    assert summary["OK"] == 20, summary
    assert summary["n_failed"] == 0, summary
    print("PASS test_normal_path_zero_false_positive_stalls")


def test_recoverable_crash_no_lost_or_duplicated_work():
    global _RECOVERABLE_ATTEMPTS_DIR
    d = _fresh("recoverable")
    R.STALL_TIMEOUT_S, R.POLL_INTERVAL_S = 3, 1
    _RECOVERABLE_ATTEMPTS_DIR = d / "_attempts"
    _RECOVERABLE_ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
    R._worker = _worker_recoverable_crash

    ids = [f"PBC|fake|{i:03d}" for i in range(10)]
    t0 = time.time()
    summary = R.run_pool_with_stall_recovery(ids, workers=3)
    elapsed = time.time() - t0

    assert summary["pool_restarts"] == 1, summary  # exactly one stall, one recovery
    assert summary["OK"] == 10, summary
    assert elapsed < 15, ("did not recover promptly", elapsed)  # not a hang

    ckpts = sorted((R.OUT / "_ckpt_worlds").glob("*.json"))
    assert len(ckpts) == 10, ("wrong checkpoint count", len(ckpts))
    case_ids_seen = set()
    for p in ckpts:
        cid = json.loads(p.read_text())["case_id"]
        assert cid not in case_ids_seen, ("duplicate checkpoint", cid)
        case_ids_seen.add(cid)
    print(f"PASS test_recoverable_crash_no_lost_or_duplicated_work (recovered in {elapsed:.1f}s)")


def test_persistent_crash_gives_up_cleanly_never_hangs():
    _fresh("persistent")
    R.STALL_TIMEOUT_S, R.POLL_INTERVAL_S = 2, 1
    R.MAX_POOL_RESTARTS = 3
    R._worker = _worker_persistent_crash

    ids = [f"PBC|fake|{i:03d}" for i in range(10)]
    t0 = time.time()
    elapsed = None
    try:
        R.run_pool_with_stall_recovery(ids, workers=3)
        raise AssertionError("expected sys.exit() from MAX_POOL_RESTARTS, got a normal return")
    except SystemExit as ex:
        elapsed = time.time() - t0
        assert elapsed < 30, ("did not give up promptly -- looks like a hang", elapsed)
    ckpts = sorted((R.OUT / "_ckpt_worlds").glob("*.json"))
    assert len(ckpts) == 9, ("healthy worlds were lost when giving up on the bad one",
                              len(ckpts))
    # CRITIC_GOVERNANCE DEF-2: the give-up path must still write a full,
    # untruncated report -- main()'s own RUN_SUMMARY.json write is skipped by
    # the sys.exit() unwind, so this driver must write its own.
    report_path = R.OUT / "RUN_SUMMARY_INCOMPLETE.json"
    assert report_path.exists(), "give-up path wrote no report at all (DEF-2 regression)"
    report = json.loads(report_path.read_text())
    assert report["GAVE_UP"] is True, report
    assert "PBC|fake|002" in report["worlds_never_completed"], report
    assert len(report["worlds_never_completed"]) < 20, report  # this test's own sanity
    print(f"PASS test_persistent_crash_gives_up_cleanly_never_hangs (gave up in {elapsed:.1f}s, "
          f"9/9 healthy worlds preserved, full report on disk)")
    R.MAX_POOL_RESTARTS = 30  # restore default for any subsequent test


def test_definitive_failure_status_terminates_and_is_reported_once():
    """The bug both hostile critics found and reproduced: a case_id that
    returns a clean, non-crash, non-exceptional failure status (exactly what
    production `_worker()` returns for RSS_CEILING_EXCEEDED or a caught
    Exception) must be recorded EXACTLY ONCE and must not prevent the run
    from terminating -- matching the pre-fix single-pass code's behavior for
    this case, not the buggy infinite-resubmission behavior the first version
    of this fix introduced."""
    _fresh("definitive_failure")
    R.STALL_TIMEOUT_S, R.POLL_INTERVAL_S = 1200, 1   # must NOT need a stall to terminate
    R._worker = _worker_definitive_failure

    ids = [f"PBC|fake|{i:03d}" for i in range(10)]
    t0 = time.time()
    summary = R.run_pool_with_stall_recovery(ids, workers=3)
    elapsed = time.time() - t0

    assert elapsed < 10, ("did not terminate promptly -- looks like the DEF-1 infinite "
                          "resubmission loop", elapsed)
    assert summary["pool_restarts"] == 0, \
        ("a clean failure return should never trigger stall-based restart logic", summary)
    assert summary["OK"] == 9, summary
    assert summary["n_failed"] == 1, summary
    assert len(summary["failures"]) == 1, \
        ("recorded more than once -- the exact DEF-1 symptom", summary["failures"])
    assert summary["failures"][0] == {"case_id": "PBC|fake|002", "status": "RSS_CEILING_EXCEEDED"}, \
        summary["failures"]
    ckpts = sorted((R.OUT / "_ckpt_worlds").glob("*.json"))
    assert len(ckpts) == 9, ("the failed case_id must never get a checkpoint", len(ckpts))
    print(f"PASS test_definitive_failure_status_terminates_and_is_reported_once "
          f"(terminated in {elapsed:.2f}s, recorded exactly once)")


ALL_TESTS = [
    test_normal_path_zero_false_positive_stalls,
    test_recoverable_crash_no_lost_or_duplicated_work,
    test_persistent_crash_gives_up_cleanly_never_hangs,
    test_definitive_failure_status_terminates_and_is_reported_once,
]


def main() -> None:
    for t in ALL_TESTS:
        t()
    print(f"\nALL PASSED ({len(ALL_TESTS)} tests)")


if __name__ == "__main__":
    main()
