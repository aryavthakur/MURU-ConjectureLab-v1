"""Amendment A1 immutability verification.

Compares the amendment tree against the original content freeze `d94d2c9`
byte-for-byte.  Held-out row bytes are never opened: they are untracked
regenerable artifacts whose SHA-256 values live in the frozen hash inventory,
and only that inventory file is compared.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pb_30_amendment_a1_integrity.py"
ORIGINAL_FREEZE = "d94d2c9"


def _git_available() -> bool:
    if shutil.which("git") is None:
        return False
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{ORIGINAL_FREEZE}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
    )
    return probe.returncode == 0


pytestmark = pytest.mark.skipif(not _git_available(), reason="original content freeze d94d2c9 is not reachable")


def _run(tmp_path: Path) -> tuple[subprocess.CompletedProcess, dict]:
    output = tmp_path / "paper_benchmark_amendment_a1.json"
    process = subprocess.run(
        ["python3", str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(output.read_text()) if output.exists() else {}
    return process, payload


def test_every_protected_benchmark_path_is_byte_identical_to_the_original_freeze(tmp_path):
    process, manifest = _run(tmp_path)

    assert process.returncode == 0, process.stdout + process.stderr
    assert manifest["original_content_freeze"] == ORIGINAL_FREEZE
    assert manifest["protected_unchanged_count"] == 242
    assert manifest["unexpected_changed_paths"] == []
    assert manifest["removed_paths"] == []


def test_the_changed_and_added_paths_are_exactly_the_declared_adequacy_set(tmp_path):
    _, manifest = _run(tmp_path)

    assert sorted(manifest["changed_paths"]) == [
        "MURU_PAPER_BENCHMARK_FREEZE.md",
        "MURU_PAPER_BENCHMARK_METRICS.md",
        "MURU_PAPER_BENCHMARK_PROTOCOL.md",
        "src/muru/paper_benchmark/analysis.py",
        "tests/test_paper_benchmark_docs.py",
    ]
    assert sorted(manifest["added_paths"]) == [
        "MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md",
        "artifacts/paper_benchmark_amendment_a1.json",
        "scripts/pb_30_amendment_a1_integrity.py",
        "src/muru/paper_benchmark/adequacy.py",
        "tests/test_paper_benchmark_adequacy.py",
        "tests/test_paper_benchmark_amendment_integrity.py",
    ]


def test_no_generator_truth_registry_or_partition_artifact_is_touched(tmp_path):
    _, manifest = _run(tmp_path)

    protected = set(manifest["protected_unchanged_paths"])
    for path in (
        "src/muru/paper_benchmark/generator.py",
        "src/muru/paper_benchmark/registry.py",
        "src/muru/paper_benchmark/truth.py",
        "src/muru/paper_benchmark/protocol.py",
        "src/muru/paper_benchmark/governance.py",
        "artifacts/paper_benchmark_hash_inventory.json",
        "artifacts/paper_benchmark_truth_manifest.json",
        "artifacts/paper_benchmark_case_manifest.json",
        "artifacts/paper_benchmark_partition_manifest.json",
        "MURU_PAPER_BENCHMARK_CASE_FAMILIES.md",
    ):
        assert path in protected


def test_held_out_row_bytes_are_never_opened_by_the_integrity_check(tmp_path):
    _, manifest = _run(tmp_path)

    assert manifest["held_out_rows_opened"] is False
    for path in manifest["protected_unchanged_paths"] + manifest["changed_paths"] + manifest["added_paths"]:
        assert not path.startswith("truth/")
        assert not path.startswith("inputs/")
