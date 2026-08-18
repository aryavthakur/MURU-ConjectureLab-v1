"""Tests for classify_cache.py. Uses REAL classify_expression on simple,
non-scientific expressions (e.g. "x0 + x1") -- these are not connected to
any real E2 world, family, or truth; they exercise the cache's own
correctness, not any scientific outcome.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.v2_calibration import e2_classify  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import classify_cache as cc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_classifier_version_is_deterministic():
    v1 = cc.compute_classifier_version(REPO_ROOT)
    v2 = cc.compute_classifier_version(REPO_ROOT)
    assert v1 == v2
    assert len(v1) == 64  # sha256 hex digest


def test_classifier_version_changes_when_a_versioned_file_changes(tmp_path):
    # Build a tiny fake repo layout with just one versioned file, hash it,
    # then mutate the file and confirm the version changes.
    fake_repo = tmp_path / "fake_repo"
    target = fake_repo / "src/muru/v2_calibration/e2_classify.py"
    target.parent.mkdir(parents=True)
    for rel in cc._VERSIONED_RELATIVE_PATHS:
        p = fake_repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("v1")
    before = cc.compute_classifier_version(fake_repo)
    target.write_text("v2 -- changed")
    after = cc.compute_classifier_version(fake_repo)
    assert before != after


def test_classify_cache_round_trip_with_real_classifier(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    version = "test-version-1"
    cache = cc.PersistentClassifyCache(db_path, version)
    try:
        expr = "x0 + x1"  # arbitrary, non-scientific test expression
        assert cache.get_classification(expr) is cc._MISSING
        real_result = e2_classify.classify_expression(expr)
        cache.put_classification(expr, real_result)
        round_tripped = cache.get_classification(expr)
        assert round_tripped == real_result
    finally:
        cache.close()


def test_classify_cache_survives_reopen(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    version = "test-version-1"
    expr = "x0 * x1"
    cache1 = cc.PersistentClassifyCache(db_path, version)
    real_result = e2_classify.classify_expression(expr)
    cache1.put_classification(expr, real_result)
    cache1.close()

    # Simulates a fresh shard process after a restart.
    cache2 = cc.PersistentClassifyCache(db_path, version)
    try:
        assert cache2.get_classification(expr) == real_result
    finally:
        cache2.close()


def test_classify_cache_version_mismatch_is_a_miss_not_a_wrong_answer(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    expr = "x2 ** 2"
    real_result = e2_classify.classify_expression(expr)

    cache_v1 = cc.PersistentClassifyCache(db_path, "version-1")
    cache_v1.put_classification(expr, real_result)
    cache_v1.close()

    cache_v2 = cc.PersistentClassifyCache(db_path, "version-2")
    try:
        assert cache_v2.get_classification(expr) is cc._MISSING  # never silently reused across versions
        stats = cache_v2.stats()
        assert stats["classify_rows_current_version"] == 0
        assert stats["classify_rows_stale_version"] == 1
    finally:
        cache_v2.close()


def test_cached_classify_expression_avoids_recomputation(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    cache = cc.PersistentClassifyCache(db_path, "v1")
    expr = "x3 + 1"
    call_count = {"n": 0}
    real_fn = e2_classify.classify_expression

    def counting_classify(e):
        call_count["n"] += 1
        return real_fn(e)

    try:
        with patch.object(e2_classify, "classify_expression", side_effect=counting_classify):
            r1 = cc.cached_classify_expression(cache, expr)
            r2 = cc.cached_classify_expression(cache, expr)
        assert call_count["n"] == 1  # second call was a cache hit, never reached the real classifier
        assert r1 == r2
    finally:
        cache.close()


def test_equivalence_cache_round_trip_and_ordered_key(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    cache = cc.PersistentClassifyCache(db_path, "v1")
    try:
        assert cache.get_equivalence("candA", "truthA") is cc._MISSING
        cache.put_equivalence("candA", "truthA", True)
        assert cache.get_equivalence("candA", "truthA") is True
        # order matters -- (truthA, candA) is a DIFFERENT key, not assumed symmetric
        assert cache.get_equivalence("truthA", "candA") is cc._MISSING
        # None is a legitimate, distinct, cacheable value (algebraically_equivalent's own "undetermined")
        cache.put_equivalence("candB", "truthB", None)
        assert cache.get_equivalence("candB", "truthB") is None  # a real cached None, not a miss
    finally:
        cache.close()


def test_concurrent_writers_same_key_do_not_conflict(tmp_path):
    db_path = tmp_path / "cache.sqlite3"
    cache_a = cc.PersistentClassifyCache(db_path, "v1")
    cache_b = cc.PersistentClassifyCache(db_path, "v1")
    try:
        expr = "x4 - 3"
        real_result = e2_classify.classify_expression(expr)
        cache_a.put_classification(expr, real_result)
        cache_b.put_classification(expr, real_result)  # INSERT OR IGNORE -- must not raise
        assert cache_a.get_classification(expr) == real_result
        assert cache_b.get_classification(expr) == real_result
    finally:
        cache_a.close()
        cache_b.close()


if __name__ == "__main__":
    import inspect
    import traceback
    mod = sys.modules[__name__]
    fns = [f for name, f in inspect.getmembers(mod, inspect.isfunction) if name.startswith("test_")]
    failed = 0
    for f in fns:
        with tempfile.TemporaryDirectory() as td:
            sig_params = inspect.signature(f).parameters
            try:
                if "tmp_path" in sig_params:
                    f(Path(td))
                else:
                    f()
                print(f"PASS {f.__name__}")
            except Exception:
                failed += 1
                print(f"FAIL {f.__name__}")
                traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
