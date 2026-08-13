import pytest

from muru.paper_benchmark.governance import (
    HeldOutAccessRefused,
    ImplementationLock,
    assert_held_out_execution_allowed,
)


def test_pending_implementation_lock_refuses_held_out_execution():
    with pytest.raises(HeldOutAccessRefused, match="PENDING_LOCK"):
        assert_held_out_execution_allowed(ImplementationLock.pending(), {"ok": "hash"}, {"complete": True}, True)


def test_clean_complete_lock_allows_only_the_governance_boundary():
    lock = ImplementationLock.locked("abc123", "strict-v1", "grammar-v1", "engine-v1")
    assert_held_out_execution_allowed(lock, {"ok": "hash"}, {"complete": True}, True) is None


def test_dirty_tree_refuses_held_out_execution():
    lock = ImplementationLock.locked("abc123", "strict-v1", "grammar-v1", "engine-v1")
    with pytest.raises(HeldOutAccessRefused, match="tree is not clean"):
        assert_held_out_execution_allowed(lock, {"ok": "hash"}, {"complete": True}, False)
