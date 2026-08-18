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

#: RC4.2 (tag `engineering-rc4-2-core-defect-repair`) repaired four confirmed
#: implementation defects (R1-R4). Not an amendment (no new scientific choice
#: was made) and not an engineering exemption (it touches the science
#: surface pb_engineering_paths.py forbids that channel from reaching); see
#: audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md and scripts/pb_rc4_2_authorized_delta.py.
#: Of RC4.2.1's eight-file ledger, only these two were tracked at d94d2c9
#: (V1); the other six (g2_contract.py, g3_contract.py, their tests, and the
#: two new test files) postdate V1 and are out of this script's scope
#: entirely, exactly like every other post-V1 addition it does not track.
RC4_2_DEFECT_REPAIR_CHANGED = [
    "src/muru/paper_benchmark/protocol.py",
    "tests/test_paper_benchmark_protocol.py",
]

#: RC5's ledgered A3.5-implementation delta, declared here for the same reason
#: RC4.2's is: it touches the science surface, so it is neither an amendment nor
#: an engineering exemption, and it is recognized only by exact old+new bytes
#: (scripts/pb_rc5_a3_5_authorized_delta.py). Of RC5's delta, only preflight.py
#: was tracked at d94d2c9 (V1); structural_acceptance.py postdates V1 (A3.1),
#: the rc3_* files postdate it (RC3), and every rc5_* module is a post-V1
#: addition -- all out of this script's scope exactly like every other post-V1
#: path it does not track.
RC5_A3_5_IMPLEMENTATION_CHANGED = [
    "src/muru/paper_benchmark/preflight.py",
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
    # leaving 236 byte-identical to the original content freeze; RC4.2 then
    # repaired two more of the 247 (protocol.py, its test), leaving 234; RC5's
    # A3.5 implementation then generalized one more (preflight.py), leaving 233.
    assert manifest["protected_unchanged_count"] == 233
    assert manifest["unexpected_changed_paths"] == []
    assert manifest["removed_paths"] == []
    # Both ledgers are reported through the same channel; each path is
    # attributed to the ledger that authorizes it, so an A3.5 implementation
    # can never be read as a defect repair.
    ledgered = {entry["path"]: entry["ledger"] for entry in manifest["changed_by_rc4_2_delta"]}
    assert sorted(ledgered) == sorted(
        RC4_2_DEFECT_REPAIR_CHANGED + RC5_A3_5_IMPLEMENTATION_CHANGED
    )
    for path in RC4_2_DEFECT_REPAIR_CHANGED:
        assert ledgered[path] == "RC4.2_R1_R4_defect_repair"
    for path in RC5_A3_5_IMPLEMENTATION_CHANGED:
        assert ledgered[path] == "RC5_A3_5_implementation"


def test_the_changed_and_added_paths_are_exactly_the_declared_amendment_sets(tmp_path):
    _, manifest = _run(tmp_path)

    assert sorted(manifest["changed_paths"]) == sorted(
        set(A1_CHANGED)
        | set(A2_CHANGED)
        | set(A2_1_CHANGED)
        | set(ENGINEERING_CHANGED)
        | set(RC4_2_DEFECT_REPAIR_CHANGED)
        | set(RC5_A3_5_IMPLEMENTATION_CHANGED)
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
    """None of these six is a case any repair here has ever touched.

    `protocol.py` is intentionally not in this list: RC4.2 (an engineering
    defect repair, not an amendment) changed it via the ledgered delta
    checked separately below. Every other path here has never moved from any
    amendment or any engineering repair, protocol.py included -- it just has
    two owners of "never moved from d94d2c9" now instead of one: "protected
    since V1" for six of these seven, "protected since V1 except the one
    ledgered RC4.2 repair" for protocol.py.
    """
    _, manifest = _run(tmp_path)

    protected = set(manifest["protected_unchanged_paths"])
    for path in (
        "src/muru/paper_benchmark/registry.py",
        "src/muru/paper_benchmark/truth.py",
        "src/muru/paper_benchmark/governance.py",
        "artifacts/paper_benchmark_truth_manifest.json",
        "artifacts/paper_benchmark_partition_manifest.json",
        "MURU_PAPER_BENCHMARK_CASE_FAMILIES.md",
    ):
        assert path in protected, path

    # protocol.py did move -- but only through the one ledgered RC4.2 repair,
    # never silently and never through any amendment's allowed-change set.
    assert "src/muru/paper_benchmark/protocol.py" not in protected
    assert "src/muru/paper_benchmark/protocol.py" not in set(manifest["changed_by_amendment"]["A1"])
    assert "src/muru/paper_benchmark/protocol.py" not in set(manifest["changed_by_amendment"]["A2"])
    assert "src/muru/paper_benchmark/protocol.py" not in set(manifest["changed_by_amendment"]["A2.1"])
    assert "src/muru/paper_benchmark/protocol.py" in {
        entry["path"] for entry in manifest["changed_by_rc4_2_delta"]
    }


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
