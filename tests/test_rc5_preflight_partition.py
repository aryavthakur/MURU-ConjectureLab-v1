"""RC5's partition-aware ``run_preflight``, and its unchanged default.

The generalisation is engineering only.  The first test here is the frozen
behaviour, asserted field by field: calling ``run_preflight(dir, lock)`` with
no partition must produce exactly what it produced before RC5 touched it.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.artifacts import build_partition
from muru.paper_benchmark.governance import ImplementationLock
from muru.paper_benchmark.preflight import (
    DEFAULT_PREFLIGHT_PARTITION,
    PARTITION_EXPECTED_CASES,
    run_preflight,
)


def test_the_default_call_is_unchanged(tmp_path):
    build_partition("development", tmp_path)
    report = run_preflight(tmp_path, ImplementationLock.pending())

    assert DEFAULT_PREFLIGHT_PARTITION == "development"
    assert report.partition == "development"
    assert report.case_count == 80
    assert report.engine_status == "not_run_pending_lock"
    assert report.complete is False
    assert report.held_out_accessed is False
    assert report.engine_failures == 0
    assert report.candidate_count == 0
    assert report.peak_rss_bytes > 0
    assert report.artifact_bytes > 0


def test_naming_development_explicitly_is_identical_to_the_default(tmp_path):
    build_partition("development", tmp_path)
    lock = ImplementationLock.pending()
    default = run_preflight(tmp_path, lock).to_dict()
    named = run_preflight(tmp_path, lock, "development").to_dict()
    # Timings are wall-clock and legitimately differ; everything else must not.
    volatile = {"wall_seconds", "cpu_seconds", "peak_rss_bytes"}
    assert {k: v for k, v in default.items() if k not in volatile} == {
        k: v for k, v in named.items() if k not in volatile
    }


def test_expected_counts_come_from_the_frozen_registry():
    assert PARTITION_EXPECTED_CASES == {
        "development": 80,
        "held_out": 240,
        "challenge": 60,
    }


def test_a_locked_implementation_reports_ready_and_complete(tmp_path):
    build_partition("development", tmp_path)
    lock = ImplementationLock.locked("abc123", "sev-1", "grammar-1", "pysr-1.5.10")
    report = run_preflight(tmp_path, lock)
    assert report.engine_status == "ready_for_locked_engine_preflight"
    assert report.complete is True


def test_an_unknown_partition_is_refused(tmp_path):
    build_partition("development", tmp_path)
    with pytest.raises(ValueError, match="unknown partition"):
        run_preflight(tmp_path, ImplementationLock.pending(), "confirmation")


def test_a_missing_partition_artifact_is_refused(tmp_path):
    build_partition("development", tmp_path)
    with pytest.raises(ValueError, match="challenge inputs are required"):
        run_preflight(tmp_path, ImplementationLock.pending(), "challenge")


def test_a_wrong_case_count_is_refused(tmp_path):
    build_partition("development", tmp_path)
    path = tmp_path / "inputs" / "development.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected 80 development cases, found 79"):
        run_preflight(tmp_path, ImplementationLock.pending())


def test_a_malformed_record_is_refused(tmp_path):
    build_partition("development", tmp_path)
    path = tmp_path / "inputs" / "development.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[0] = "{}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="development input record is malformed"):
        run_preflight(tmp_path, ImplementationLock.pending())


def test_preflight_never_opens_a_truth_artifact(tmp_path, monkeypatch):
    build_partition("development", tmp_path)
    opened: list[str] = []
    real_open = type(tmp_path).read_bytes

    def spy(self):
        opened.append(str(self))
        return real_open(self)

    monkeypatch.setattr(type(tmp_path), "read_bytes", spy)
    run_preflight(tmp_path, ImplementationLock.pending())
    assert opened
    assert not any("/truth/" in p for p in opened)
