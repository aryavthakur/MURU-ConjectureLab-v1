"""Pure-arithmetic tests for e2_rescue_v2.routing_lock. No E2 scientific data
involved anywhere -- every count here is synthetic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.v2_calibration.e2_rescue_v2.routing_lock import (
    LockState, evaluate_gate2, ExonerationRatification,
)


def test_unlocked_when_plenty_remaining():
    r = evaluate_gate2(a_n=10, b_n=12, c_n=5, d_n=5, r_remaining=400)
    assert r.state == LockState.FULL_RUN_REQUIRED


def test_locked_execute_when_b_cannot_be_caught():
    # B=100, A=10, C+D=10, r=50: A can reach at most 60, CD at most 60, both < 100
    r = evaluate_gate2(a_n=10, b_n=100, c_n=5, d_n=5, r_remaining=50)
    assert r.state == LockState.LOCKED_EXECUTE_E4A


def test_not_locked_execute_at_exact_boundary():
    # B_n == A_n + r exactly -> adversary can tie, not strictly beat, but
    # the gate requires B > A strictly, and our lock requires B_n > A_n+r
    # strictly (tight boundary case: adversary can force A_final == B_final,
    # which is NOT B-strict-plurality, so B's lock must NOT fire, but also
    # A cannot lock either -- this is a genuine unlocked case)
    r = evaluate_gate2(a_n=50, b_n=100, c_n=0, d_n=0, r_remaining=50)  # B_n=100, A_n+r=100
    assert r.state == LockState.FULL_RUN_REQUIRED


def test_locked_execute_boundary_plus_one():
    r = evaluate_gate2(a_n=50, b_n=101, c_n=0, d_n=0, r_remaining=50)  # B_n=101 > 100
    assert r.state == LockState.LOCKED_EXECUTE_E4A


def test_adversarial_worst_case_is_tight_all_to_rival():
    # A_n=0, B_n=1, r=1: adversary puts the 1 remaining into A -> A_final=1, B_final=1 -> tie, not a B lock
    r = evaluate_gate2(a_n=0, b_n=1, c_n=0, d_n=0, r_remaining=1)
    assert r.state == LockState.FULL_RUN_REQUIRED
    # A_n=0, B_n=2, r=1: worst case A_final=1 < B_final=2 -> B locks
    r2 = evaluate_gate2(a_n=0, b_n=2, c_n=0, d_n=0, r_remaining=1)
    assert r2.state == LockState.LOCKED_EXECUTE_E4A


def test_a_or_cd_dominant_never_locks_without_ratified_exoneration():
    # A totally overwhelms B and C+D, r=0 (everything classified) -- even
    # then, without a ratified exoneration threshold, branches 3/4/5 must
    # not be reported as locked.
    r = evaluate_gate2(a_n=500, b_n=10, c_n=15, d_n=15, r_remaining=0)
    assert r.state == LockState.FULL_RUN_REQUIRED
    assert "exoneration" in r.note.lower() or "branch 2" in r.note.lower() or "ratified" in r.note.lower()


def test_cd_dominant_never_locks_without_ratified_exoneration():
    r = evaluate_gate2(a_n=10, b_n=10, c_n=260, d_n=260, r_remaining=0)
    assert r.state == LockState.FULL_RUN_REQUIRED


def test_execute_still_locks_at_r_zero_full_completion():
    r = evaluate_gate2(a_n=100, b_n=300, c_n=70, d_n=70, r_remaining=0)
    assert r.state == LockState.LOCKED_EXECUTE_E4A


def test_negative_inputs_rejected():
    try:
        evaluate_gate2(a_n=-1, b_n=1, c_n=0, d_n=0, r_remaining=1)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_never_exposes_raw_counts_in_state_value():
    from muru.v2_calibration.e2_rescue_v2.routing_lock import evaluate_gate2_opaque
    s = evaluate_gate2_opaque(a_n=7, b_n=400, c_n=1, d_n=1, r_remaining=10)
    assert s in {e.value for e in LockState}
    # the opaque entry point returns nothing but the enum string
    assert isinstance(s, str) and s.isupper()


if __name__ == "__main__":
    import inspect
    mod = sys.modules[__name__]
    fns = [f for name, f in inspect.getmembers(mod, inspect.isfunction) if name.startswith("test_")]
    failed = 0
    for f in fns:
        try:
            f()
            print(f"PASS {f.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {f.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
