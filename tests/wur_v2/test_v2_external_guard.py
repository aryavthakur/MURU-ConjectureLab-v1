"""External one-look guard: committed freeze, clean tree, first-access record before decode, no second look,
no decode outside the declared population."""
import json
import subprocess

import pytest

from muru.wur_v2.external_guard import AccessGuard, GuardError


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "FREEZE.md").write_text("frozen\n")
    subprocess.run(["git", "add", "FREEZE.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "freeze"], cwd=tmp_path, check=True)
    return tmp_path


def test_guard_writes_record_first_and_refuses_second_look(tmp_path):
    root = _repo(tmp_path)
    rec = root / "access" / "validation.json"
    g = AccessGuard("VALIDATION", rec, root / "FREEZE.md", {("a.mzML", "scan=1")}, root=root)
    assert rec.exists() and json.loads(rec.read_text())["git_tree_dirty"] is False
    g.record_decode(root / "a.mzML", ["scan=1"])
    with pytest.raises(GuardError, match="outside"):
        g.record_decode(root / "a.mzML", ["scan=2"])
    with pytest.raises(GuardError, match="second look"):
        AccessGuard("VALIDATION", rec, root / "FREEZE.md", set(), root=root)


def test_guard_requires_committed_freeze_and_clean_tree(tmp_path):
    root = _repo(tmp_path)
    (root / "UNTRACKED.md").write_text("x")
    with pytest.raises(GuardError, match="not committed"):
        AccessGuard("VALIDATION", root / "r.json", root / "UNTRACKED.md", set(), root=root)
    (root / "FREEZE.md").write_text("edited after freeze\n")
    with pytest.raises(GuardError, match="dirty"):
        AccessGuard("VALIDATION", root / "r2.json", root / "FREEZE.md", set(), root=root)
