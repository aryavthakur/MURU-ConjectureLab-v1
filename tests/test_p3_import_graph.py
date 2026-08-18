"""The discovery code path must not be able to read the planted ground truth.

Master plan, Phase 3 Tests: "Ground-truth equations must be unreadable by the
discovery code (separate module, verified by import graph)."

This walks the real transitive import closure of every `muru.discovery` module
rather than grepping for import lines, so an indirect path through a third
module is caught too.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
DISCOVERY = SRC / "muru" / "discovery"
FORBIDDEN = {"muru.synth.truth", "muru.synth.generators", "muru.synth.plan"}


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
            out.update(f"{node.module}.{a.name}" for a in node.names)
    return out


def _closure(start: Path) -> set[str]:
    seen_files = {start}
    seen_mods: set[str] = set()
    stack = [start]
    while stack:
        mods = _module_imports(stack.pop())
        for m in mods:
            if not m.startswith("muru"):
                continue
            seen_mods.add(m)
            f = SRC / (m.replace(".", "/") + ".py")
            if f.exists() and f not in seen_files:
                seen_files.add(f)
                stack.append(f)
    return seen_mods


def discovery_modules() -> list[Path]:
    return sorted(p for p in DISCOVERY.glob("*.py") if p.name != "__init__.py")


@pytest.mark.parametrize("path", discovery_modules(), ids=lambda p: p.stem)
def test_discovery_module_cannot_reach_ground_truth(path: Path):
    reached = _closure(path)
    bad = {m for m in reached
           if any(m == f or m.startswith(f + ".") for f in FORBIDDEN)}
    assert not bad, (
        f"{path.name} can reach {sorted(bad)}; the search must never be able to "
        "read the planted law")


def test_the_check_would_actually_catch_a_violation(tmp_path):
    """A guard test is worthless if it cannot fail. Plant one and require a catch."""
    bad = DISCOVERY / "_violation_probe.py"
    bad.write_text("from muru.synth.truth import PHI\n")
    try:
        reached = _closure(bad)
        assert any(m.startswith("muru.synth.truth") for m in reached)
    finally:
        bad.unlink()


def test_truth_module_is_importable_by_the_generator():
    """The quarantine is one-directional: generators legitimately need truth."""
    sys.path.insert(0, str(SRC))
    reached = _closure(SRC / "muru" / "synth" / "generators.py")
    assert any(m.startswith("muru.synth.truth") for m in reached)
