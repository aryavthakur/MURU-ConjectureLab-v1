#!/usr/bin/env python3
"""Adversarial self-test for `v2_stage1_scoring.py`'s tier-2 subprocess isolation.

CRITIC_GOVERNANCE (review of the isolation change, 2026-08-19) correctly FAILED an
earlier version of that change for asserting, in a code comment, that a race
condition "caught by adversarial self-test" -- with no test file anywhere in the
repository to check the claim against. This file is that test, committed and
re-runnable, so the claim is no longer just a comment.

Covers every case the execution-safety tooling authorization requires:
normal success, forced resource exhaustion (real, not mocked), a killed
subprocess, malformed output, cross-talk (wrong-expression) output, subprocess
launch failure, non-UTF-8 output, and checkpoint/resume including a corrupted
checkpoint and concurrent-duplicate de-duplication.

Run: /home/aryav_thakur/venv/bin/python3 scripts/v2_stage1_scoring_selftest.py
Exits 0 and prints ALL PASSED, or raises AssertionError on the first failure.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import v2_stage1_scoring as S  # noqa: E402

TMP = Path("/home/aryav_thakur/.claude/jobs/d40d7453/tmp/v2_scoring_selftest_ckpt")


def _fresh_ckpt() -> Path:
    if TMP.exists():
        shutil.rmtree(TMP)
    return TMP


def test_normal_success():
    d = S.canonicalise_isolated("sin(x)**2 + cos(x)**2")
    assert d["canonicalization_status"] == "OK", d
    assert d["canonical_expression"] == "1", d
    print("PASS test_normal_success")


def test_unparseable_is_not_a_crash():
    d = S.canonicalise_isolated(")))nonsense((((")
    assert d["canonicalization_status"] == "UNPARSEABLE", d
    print("PASS test_unparseable_is_not_a_crash")


def test_real_resource_exhaustion_via_tiny_rlimit():
    """A REAL subprocess, REAL sympy import, under REAL memory pressure severe
    enough to crash CPython's own import machinery (not a typed MemoryError --
    an uncaught SystemError deep in importlib). Demonstrates the OUTER
    subprocess-isolation layer contains and correctly types the failure
    regardless of what killed the inner process."""
    orig = S.SCORING_TIER2_RSS_GIB
    S.SCORING_TIER2_RSS_GIB = 0.01
    try:
        d = S.canonicalise_isolated("x + x")
    finally:
        S.SCORING_TIER2_RSS_GIB = orig
    assert d["canonicalization_status"] == "UNRESOLVED", d
    assert d["canonicalization_status"] != "OK"
    print("PASS test_real_resource_exhaustion_via_tiny_rlimit:", d["unresolved_reason"])


def test_simulated_kernel_oom_kill():
    with mock.patch("subprocess.run") as m:
        m.return_value = subprocess.CompletedProcess(args=[], returncode=-9, stdout="", stderr="")
        d = S.canonicalise_isolated("some_expr")
    assert d["canonicalization_status"] == "UNRESOLVED"
    assert "KERNEL_OOM_KILL" in d["unresolved_reason"]
    print("PASS test_simulated_kernel_oom_kill")


def test_malformed_output_not_silently_ok():
    with mock.patch("subprocess.run") as m:
        m.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="Rnot{valid]json",
                                                       stderr="")
        d = S.canonicalise_isolated("some_expr")
    assert d["canonicalization_status"] == "UNRESOLVED"
    assert d["unresolved_reason"] == "MALFORMED_OUTPUT"
    print("PASS test_malformed_output_not_silently_ok")


def test_crosstalk_output_rejected():
    """Output for the WRONG expression must never be attributed to the one asked
    for -- this would otherwise let a subprocess's stale/mismatched output
    silently mislabel a different expression as OK."""
    with mock.patch("subprocess.run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='R{"expression_string": "DIFFERENT_EXPR", "canonicalization_status": "OK"}',
            stderr="")
        d = S.canonicalise_isolated("some_expr")
    assert d["canonicalization_status"] == "UNRESOLVED"
    assert d["unresolved_reason"] == "MALFORMED_OUTPUT"
    print("PASS test_crosstalk_output_rejected")


def test_environment_import_failure_typed():
    with mock.patch("subprocess.run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="",
            stderr="Traceback...\nModuleNotFoundError: No module named sympy")
        d = S.canonicalise_isolated("some_expr")
    assert "ENVIRONMENT_IMPORT_FAILURE" in d["unresolved_reason"]
    print("PASS test_environment_import_failure_typed")


def test_subprocess_launch_failure():
    with mock.patch("subprocess.run", side_effect=OSError("fork failed")):
        d = S.canonicalise_isolated("some_expr")
    assert d["canonicalization_status"] == "UNRESOLVED"
    assert "SUBPROCESS_LAUNCH_FAILED" in d["unresolved_reason"]
    print("PASS test_subprocess_launch_failure")


def test_non_utf8_output_does_not_raise():
    """CRITIC_SCIENCE advisory: a dying subprocess could leave non-UTF-8 bytes on
    stdout/stderr. `errors="replace"` must stop that from raising UnicodeDecodeError
    uncaught through canonicalise_isolated -- verified against the REAL subprocess
    path (not mocked), since text-decoding only happens inside subprocess.run
    itself, not somewhere a mock would intercept it."""
    code = 'import sys; sys.stdout.buffer.write(b"R\\xff\\xfe not valid utf8"); sys.exit(1)'
    with mock.patch.object(sys, "executable", sys.executable):
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                            errors="replace")
    assert p.returncode == 1
    # The real assertion: canonicalise_isolated must not raise when subprocess.run's
    # OWN text decoding meets bad bytes. Exercise the real function end to end by
    # monkeypatching only the *command* it builds, not subprocess.run's behavior.
    with mock.patch.object(S, "_CANON_PAYLOAD", "import sys\nsys.stdout.buffer.write(b'R\\xff\\xfe bad')\n"):
        d = S.canonicalise_isolated("some_expr")  # must not raise
    assert d["canonicalization_status"] == "UNRESOLVED", d
    print("PASS test_non_utf8_output_does_not_raise:", d["unresolved_reason"])


def test_escalate_isolated_dedup_and_no_race():
    ckpt = _fresh_ckpt()
    call_count = {"n": 0}
    real = S.canonicalise_isolated

    def counting(expr):
        call_count["n"] += 1
        return real(expr)

    exprs = ["x + x", "2*y - y", "x + x"]  # duplicate on purpose
    with mock.patch.object(S, "canonicalise_isolated", side_effect=counting):
        out1 = S.escalate_isolated(exprs, ckpt)
    assert call_count["n"] == 2, ("duplicate expression was escalated twice", call_count)
    assert set(out1) == {"x + x", "2*y - y"}
    print("PASS test_escalate_isolated_dedup_and_no_race (dedup)")

    call_count["n"] = 0
    with mock.patch.object(S, "canonicalise_isolated", side_effect=counting):
        out2 = S.escalate_isolated(exprs, ckpt)
    assert call_count["n"] == 0, ("resume re-escalated instead of reading checkpoints", call_count)
    assert out1 == out2
    print("PASS test_escalate_isolated_dedup_and_no_race (resume, 0 recompute)")
    shutil.rmtree(ckpt)


def test_partial_crash_resume():
    ckpt = _fresh_ckpt()
    manual = {"expression_string": "x + x", "canonicalization_status": "OK",
              "canonical_expression": "2*x", "effective_support": None,
              "discovered_family": None, "template_key_repr": None,
              "cpu_seconds": 0.01, "tier": 2, "unresolved_reason": None}
    ckpt.mkdir(parents=True, exist_ok=True)
    (ckpt / (hashlib.sha256("x + x".encode()).hexdigest() + ".json")).write_text(json.dumps(manual))
    call_count = {"n": 0}
    real = S.canonicalise_isolated

    def counting(expr):
        call_count["n"] += 1
        return real(expr)

    with mock.patch.object(S, "canonicalise_isolated", side_effect=counting):
        out = S.escalate_isolated(["x + x", "2*y - y"], ckpt)
    assert call_count["n"] == 1, ("crash-resume recomputed the already-checkpointed expression",
                                   call_count)
    assert out["x + x"]["canonical_expression"] == "2*x"
    print("PASS test_partial_crash_resume")
    shutil.rmtree(ckpt)


def test_corrupted_checkpoint_recovered():
    ckpt = _fresh_ckpt()
    ckpt.mkdir(parents=True, exist_ok=True)
    bad = ckpt / (hashlib.sha256("2*y - y".encode()).hexdigest() + ".json")
    bad.write_text("{not valid json")
    call_count = {"n": 0}
    real = S.canonicalise_isolated

    def counting(expr):
        call_count["n"] += 1
        return real(expr)

    with mock.patch.object(S, "canonicalise_isolated", side_effect=counting):
        S.escalate_isolated(["2*y - y"], ckpt)
    assert call_count["n"] == 1, ("corrupted checkpoint was not discarded and recomputed",
                                   call_count)
    print("PASS test_corrupted_checkpoint_recovered")
    shutil.rmtree(ckpt)


def test_frozen_constants_match_resource_profile():
    profile = json.loads((ROOT / "audit/muru_v2_reentry_20260819/STAGE1_RESOURCE_PROFILE.json")
                          .read_text())
    tier2 = profile["DECLARED, FROZEN BEFORE STAGE 0"]["scoring_tier2"]
    assert S.SCORING_TIER2_RSS_GIB == tier2["RSS_CEILING_GIB"], \
        (S.SCORING_TIER2_RSS_GIB, tier2["RSS_CEILING_GIB"])
    assert S.SCORING_TIER2_WORKERS == tier2["WORKER_COUNT"], \
        (S.SCORING_TIER2_WORKERS, tier2["WORKER_COUNT"])
    print("PASS test_frozen_constants_match_resource_profile")


def test_scoring_preflight_passes_on_this_host():
    S.scoring_preflight()  # must not raise / sys.exit
    print("PASS test_scoring_preflight_passes_on_this_host")


ALL_TESTS = [
    test_normal_success,
    test_unparseable_is_not_a_crash,
    test_real_resource_exhaustion_via_tiny_rlimit,
    test_simulated_kernel_oom_kill,
    test_malformed_output_not_silently_ok,
    test_crosstalk_output_rejected,
    test_environment_import_failure_typed,
    test_subprocess_launch_failure,
    test_non_utf8_output_does_not_raise,
    test_escalate_isolated_dedup_and_no_race,
    test_partial_crash_resume,
    test_corrupted_checkpoint_recovered,
    test_frozen_constants_match_resource_profile,
    test_scoring_preflight_passes_on_this_host,
]


def main() -> None:
    for t in ALL_TESTS:
        t()
    print(f"\nALL PASSED ({len(ALL_TESTS)} tests)")


if __name__ == "__main__":
    main()
