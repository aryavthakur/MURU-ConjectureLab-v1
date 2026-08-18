"""Checkpoint and resume behaviour.

Phase 2 lost time to poor execution planning (BACKLOG I4). These tests pin the
four properties Phase 3 relies on: completed units are detected, they are not
recomputed, a partial run resumes at the next incomplete unit, aggregation does
not depend on completion order, and an interrupted write cannot corrupt a
completed artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery.checkpoint import Store  # noqa: E402

BLOCK, WORLD = "G1_pysr", "G1B|r000|moderate"


def test_completed_units_are_detected(tmp_path):
    s = Store(tmp_path)
    assert not s.done(BLOCK, WORLD, 1)
    s.write(BLOCK, WORLD, 1, {"seed": 1})
    assert s.done(BLOCK, WORLD, 1)


def test_pending_skips_what_is_already_present(tmp_path):
    s = Store(tmp_path)
    for u in (1, 2, 5):
        s.write(BLOCK, WORLD, u, {"seed": u})
    assert s.pending(BLOCK, WORLD, [1, 2, 3, 4, 5]) == [3, 4]


def test_a_completed_unit_is_never_recomputed(tmp_path):
    """Simulate the runner loop and count how often work is actually done."""
    s = Store(tmp_path)
    units = list(range(6))
    computed = []

    def run():
        for u in s.pending(BLOCK, WORLD, units):
            computed.append(u)
            s.write(BLOCK, WORLD, u, {"seed": u, "value": u * 2})

    run()
    assert computed == units
    computed.clear()
    run()
    assert computed == [], "a second pass recomputed completed units"


def test_a_partial_run_resumes_at_the_next_incomplete_unit(tmp_path):
    s = Store(tmp_path)
    units = list(range(10))
    for u in units[:4]:
        s.write(BLOCK, WORLD, u, {"seed": u})
    assert s.pending(BLOCK, WORLD, units) == [4, 5, 6, 7, 8, 9]


def test_aggregation_is_invariant_to_completion_order(tmp_path):
    a, b = Store(tmp_path / "a"), Store(tmp_path / "b")
    units = [3, 1, 4, 1, 5, 9, 2, 6]
    for u in units:
        a.write(BLOCK, WORLD, u, {"seed": u, "v": u})
    for u in reversed(units):
        b.write(BLOCK, WORLD, u, {"seed": u, "v": u})
    assert a.read_world(BLOCK, WORLD) == b.read_world(BLOCK, WORLD)
    assert list(a.read_world(BLOCK, WORLD)) == list(b.read_world(BLOCK, WORLD))


def test_an_interrupted_write_does_not_corrupt_a_completed_artifact(tmp_path):
    s = Store(tmp_path)
    s.write(BLOCK, WORLD, 1, {"seed": 1, "good": True})
    # a crashed writer leaves a .tmp behind; the completed .json must survive
    (s.path(BLOCK, WORLD, 1).with_suffix(".json.tmp")).write_text('{"trunc')
    assert s.done(BLOCK, WORLD, 1)
    assert s.read(BLOCK, WORLD, 1)["good"] is True


def test_a_truncated_result_file_counts_as_incomplete_not_as_a_result(tmp_path):
    s = Store(tmp_path)
    p = s.path(BLOCK, WORLD, 7)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"seed": 7, "candi')
    assert not s.done(BLOCK, WORLD, 7), (
        "a half-written file must be recomputed, never believed")
    assert s.pending(BLOCK, WORLD, [7]) == [7]


def test_read_world_skips_unreadable_files_without_failing(tmp_path):
    s = Store(tmp_path)
    s.write(BLOCK, WORLD, 1, {"seed": 1})
    (s.path(BLOCK, WORLD, 2)).write_text("not json")
    got = s.read_world(BLOCK, WORLD)
    assert set(got) == {"1"}


def test_world_ids_with_pipes_are_stored_safely(tmp_path):
    s = Store(tmp_path)
    p = s.write(BLOCK, "NULL|construction|r001", 1, {"seed": 1})
    assert "|" not in p.parent.name
    assert json.loads(p.read_text())["seed"] == 1
