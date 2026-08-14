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


A1_CHANGED = [
    "MURU_PAPER_BENCHMARK_FREEZE.md",
    "MURU_PAPER_BENCHMARK_METRICS.md",
    "MURU_PAPER_BENCHMARK_PROTOCOL.md",
    "src/muru/paper_benchmark/analysis.py",
    "tests/test_paper_benchmark_docs.py",
]
A1_ADDED = [
    "MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md",
    "artifacts/paper_benchmark_amendment_a1.json",
    "scripts/pb_30_amendment_a1_integrity.py",
    "src/muru/paper_benchmark/adequacy.py",
    "tests/test_paper_benchmark_adequacy.py",
    "tests/test_paper_benchmark_amendment_integrity.py",
]
#: Amendment A2 repaired F16.  These are the V1-resident paths it changed: the
#: generator itself and the four artifacts whose bytes follow the 19 F16 cases.
#: No registry, truth schema, protocol, governance, partition manifest, or A1
#: decision path appears here.
#:
#: A2 also edits three paths that A1 introduced (`paper_benchmark_amendment_a1
#: .json`, `pb_30_amendment_a1_integrity.py`, and this test module) so that the
#: V1-relative report attributes each change to its owning amendment.  Those do
#: not appear below: relative to `d94d2c9` they are additions, not changes, and
#: this manifest reports them under `added_by_amendment["A1"]`.
A2_CHANGED = [
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_content_freeze.json",
    "artifacts/paper_benchmark_hash_inventory.json",
    "artifacts/paper_benchmark_preflight.json",
    "src/muru/paper_benchmark/generator.py",
]
A2_ADDED = [
    "MURU_PAPER_BENCHMARK_A2_F16_GOVERNANCE_REVIEW.md",
    "MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md",
    "artifacts/paper_benchmark_amendment_a2.json",
    "scripts/pb_31_amendment_a2_integrity.py",
    "tests/test_paper_benchmark_amendment_a2_integrity.py",
    "tests/test_paper_benchmark_f16_combined.py",
]
#: Amendment A2.1 bumped GENERATOR_VERSION for provenance reasons (no science
#: changed).  It touches the same five V1-resident paths A2 did -- generator.py
#: and the four artifacts whose bytes follow every case's content_hash -- so
#: relative to V1 those five paths are legitimately attributed to *both*
#: amendments (each made an independent, cumulative change to them), which is
#: why `A2_CHANGED` and `A2_1_CHANGED` are set-equal below.
A2_1_CHANGED = [
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_content_freeze.json",
    "artifacts/paper_benchmark_hash_inventory.json",
    "artifacts/paper_benchmark_preflight.json",
    "src/muru/paper_benchmark/generator.py",
]
A2_1_ADDED = [
    "MURU_PAPER_BENCHMARK_AMENDMENT_A2_1_GENERATOR_VERSION.md",
    "artifacts/paper_benchmark_amendment_a2_1.json",
    "scripts/pb_32_amendment_a2_1_integrity.py",
    "tests/test_paper_benchmark_amendment_a2_1_integrity.py",
]
#: Not an amendment.  The RC4.1 environment closure repaired one engineering
#: file inside the V1-frozen path set: `requirements.lock.txt` was a reduced
#: 39-pin Phase-1 lock omitting SymPy, mpmath, PySR, gplearn and the Julia
#: bridge, while README.md instructs a replicator to build the environment
#: from it.  It is now byte-identical to the 50-pin
#: `configs/rc3_requirements_lock_c7c2332.txt` the frozen runtime guard
#: already enforced and the audited A3.2 calibration declared.  No scientific
#: definition moved, which is what the last test in this module pins.
ENGINEERING_CHANGED = [
    "requirements.lock.txt",
]


def test_every_protected_benchmark_path_is_byte_identical_to_the_original_freeze(tmp_path):
    process, manifest = _run(tmp_path)

    assert process.returncode == 0, process.stdout + process.stderr
    assert manifest["original_content_freeze"] == ORIGINAL_FREEZE
    assert manifest["amendments_applied"] == ["A1", "A2", "A2.1"]
    # d94d2c9 froze 247 tracked paths.  A1 changed 5, leaving 242; A2 changed 5
    # more, leaving 237 still byte-identical to the original content freeze.
    # A2.1 changed no path A2 had not already changed, so 237 is unchanged.
    assert manifest["frozen_path_count"] == 247
    # 237 until the RC4.1 environment closure, which repaired exactly one
    # engineering-only path inside the frozen set (requirements.lock.txt),
    # leaving 236 byte-identical to the original content freeze.
    assert manifest["protected_unchanged_count"] == 236
    assert manifest["unexpected_changed_paths"] == []
    assert manifest["removed_paths"] == []


def test_the_changed_and_added_paths_are_exactly_the_declared_amendment_sets(tmp_path):
    _, manifest = _run(tmp_path)

    assert sorted(manifest["changed_paths"]) == sorted(
        set(A1_CHANGED) | set(A2_CHANGED) | set(A2_1_CHANGED) | set(ENGINEERING_CHANGED)
    )
    assert sorted(manifest["added_paths"]) == sorted(set(A1_ADDED) | set(A2_ADDED) | set(A2_1_ADDED))


def test_the_engineering_change_is_attributed_to_engineering_not_to_an_amendment(tmp_path):
    """An engineering exemption must never be readable as a science amendment."""
    _, manifest = _run(tmp_path)

    assert manifest["changed_by_engineering"]["RC4.1_environment_closure"] == sorted(
        ENGINEERING_CHANGED
    )
    for amendment in ("A1", "A2", "A2.1"):
        assert not set(manifest["changed_by_amendment"][amendment]) & set(
            ENGINEERING_CHANGED
        )


def test_no_engineering_exemption_can_cover_a_benchmark_science_path(tmp_path):
    _, manifest = _run(tmp_path)

    # The prefix list is imported, never restated: a fourth copy would be the
    # exact drift the single shared declaration exists to prevent.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pb_engineering_paths_for_integrity_test",
        Path(__file__).resolve().parents[1] / "scripts" / "pb_engineering_paths.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # A computed result, not a flag the script wrote about itself.
    assert manifest["engineering_science_surface_violations"] == []
    for path in manifest["engineering_declared_paths"]:
        assert not path.startswith(module.SCIENCE_SURFACE_PREFIXES), path


def test_each_change_is_attributed_to_the_amendment_that_owns_it(tmp_path):
    _, manifest = _run(tmp_path)

    assert manifest["changed_by_amendment"]["A1"] == sorted(A1_CHANGED)
    assert manifest["changed_by_amendment"]["A2"] == sorted(A2_CHANGED)
    assert manifest["changed_by_amendment"]["A2.1"] == sorted(A2_1_CHANGED)
    assert manifest["added_by_amendment"]["A1"] == sorted(A1_ADDED)
    assert manifest["added_by_amendment"]["A2"] == sorted(A2_ADDED)
    assert manifest["added_by_amendment"]["A2.1"] == sorted(A2_1_ADDED)


def test_no_registry_truth_schema_or_partition_artifact_is_touched_by_any_amendment(tmp_path):
    _, manifest = _run(tmp_path)

    protected = set(manifest["protected_unchanged_paths"])
    for path in (
        "src/muru/paper_benchmark/registry.py",
        "src/muru/paper_benchmark/truth.py",
        "src/muru/paper_benchmark/protocol.py",
        "src/muru/paper_benchmark/governance.py",
        "artifacts/paper_benchmark_truth_manifest.json",
        "artifacts/paper_benchmark_partition_manifest.json",
        "MURU_PAPER_BENCHMARK_CASE_FAMILIES.md",
    ):
        assert path in protected, path


def test_the_generator_change_is_owned_by_a2_and_a2_1_only(tmp_path):
    """The generator differs from V1 because A2 repaired F16 and A2.1 then
    corrected its version provenance; A1 never touched it."""
    _, manifest = _run(tmp_path)

    generator = "src/muru/paper_benchmark/generator.py"
    assert generator not in set(manifest["protected_unchanged_paths"])
    assert generator in manifest["changed_by_amendment"]["A2"]
    assert generator in manifest["changed_by_amendment"]["A2.1"]
    assert generator not in manifest["changed_by_amendment"]["A1"]


def test_held_out_row_bytes_are_never_opened_by_the_integrity_check(tmp_path):
    _, manifest = _run(tmp_path)

    assert manifest["held_out_rows_opened"] is False
    for path in manifest["protected_unchanged_paths"] + manifest["changed_paths"] + manifest["added_paths"]:
        assert not path.startswith("truth/")
        assert not path.startswith("inputs/")
