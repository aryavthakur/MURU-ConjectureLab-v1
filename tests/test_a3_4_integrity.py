"""A3.4 science-freeze and sealed-boundary integrity checks."""

from __future__ import annotations

import builtins
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pb_35_a3_4_integrity.py"
RECORDED_PROTECTED_AGGREGATE = (
    "d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8"
)
TERMINAL_NEWLINE_PROTECTED_AGGREGATE = (
    "55ebd0b92ba07ad828983f4e7add5163f49377255dfcf47bdd9f1af98174f16a"
)
FROZEN_METADATA_ADVISORIES = [
    "ADVISORY_A3_4_PARENT_A3_3_LITERAL_NONOBJECT",
]


def _load_integrity_module():
    spec = importlib.util.spec_from_file_location("pb_35_a3_4_integrity", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _commit_fixture(repo: Path, relative_path: str, content: bytes) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "integrity@example.invalid")
    _git(repo, "config", "user.name", "Integrity fixture")
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _git(repo, "add", relative_path)
    _git(repo, "commit", "-qm", "freeze fixture")


def test_a34_integrity_script_accepts_clean_checkout():
    """The real engineering checkout must satisfy every frozen boundary."""
    result = subprocess.run(
        (sys.executable, str(SCRIPT)),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "A3.4 INTEGRITY VERIFIED" in result.stdout
    assert (
        "RECORDED_PROTECTED_AGGREGATE_NO_TERMINAL_NEWLINE: "
        f"{RECORDED_PROTECTED_AGGREGATE}"
    ) in result.stdout
    assert (
        "DERIVED_PROTECTED_AGGREGATE_TERMINAL_NEWLINE: "
        f"{TERMINAL_NEWLINE_PROTECTED_AGGREGATE}"
    ) in result.stdout
    for advisory in FROZEN_METADATA_ADVISORIES:
        assert f"ADVISORY: {advisory}" in result.stdout
    assert "ADVISORY_A3_4_PROTECTED_AGGREGATE_NONSTANDARD" not in result.stdout


def test_byte_identity_reports_a_changed_protected_file(tmp_path: Path):
    """Replacing a protected byte changes the result even with a valid Git tree."""
    integrity = _load_integrity_module()
    _commit_fixture(tmp_path, "science/protected.txt", b"frozen bytes\n")
    (tmp_path / "science/protected.txt").write_bytes(b"drifted bytes\n")

    errors = integrity.check_byte_identity(
        tmp_path,
        "HEAD",
        ("science/protected.txt",),
        label="fixture",
    )

    assert errors == ["MODIFIED_FIXTURE: science/protected.txt"]


def test_frozen_a34_artifact_links_all_published_digests():
    """The frozen record uses the no-terminal-newline aggregate convention."""
    integrity = _load_integrity_module()

    assert integrity.check_a34_artifact_linkage(ROOT) == []
    assert integrity.frozen_recorded_protected_aggregate(ROOT) == RECORDED_PROTECTED_AGGREGATE
    assert (
        integrity.frozen_terminal_newline_protected_aggregate(ROOT)
        == TERMINAL_NEWLINE_PROTECTED_AGGREGATE
    )
    assert RECORDED_PROTECTED_AGGREGATE != TERMINAL_NEWLINE_PROTECTED_AGGREGATE
    assert integrity.known_frozen_metadata_advisories(ROOT) == FROZEN_METADATA_ADVISORIES


def test_static_scan_permits_only_the_covariate_reference_adapter(
    tmp_path: Path,
    monkeypatch,
):
    """AST inspection must not execute the permitted frozen generator import."""
    integrity = _load_integrity_module()
    endpoint_dir = tmp_path / "src/muru/paper_benchmark"
    endpoint_dir.mkdir(parents=True)
    (endpoint_dir / "a34_contract.py").write_text(
        "from .generator import _synthetic_compounds\n"
        "def reference_rows(frame_id):\n"
        "    return _synthetic_compounds(frame_id)\n",
        encoding="utf-8",
    )
    (endpoint_dir / "a34_safe.py").write_text(
        "from .truth import TruthRecord\n"
        "def score(truth):\n"
        "    return isinstance(truth, TruthRecord)\n",
        encoding="utf-8",
    )

    original_import = builtins.__import__

    def forbid_execution_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.endswith("generator") or name.endswith("truth"):
            raise AssertionError(f"static scan imported {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", forbid_execution_import)

    assert integrity.scan_a34_endpoint_sources(tmp_path) == []


def test_static_scan_rejects_forbidden_endpoint_import_or_reference(tmp_path: Path):
    """An alias cannot hide partition materialization or calibration access."""
    integrity = _load_integrity_module()
    endpoint_dir = tmp_path / "src/muru/paper_benchmark"
    endpoint_dir.mkdir(parents=True)
    (endpoint_dir / "a34_contract.py").write_text(
        "from .generator import _synthetic_compounds\n",
        encoding="utf-8",
    )
    (endpoint_dir / "a34_boundary_breach.py").write_text(
        "from .generator import generate_partition as covariates\n"
        "import muru.paper_benchmark.rc3_calibration_runner as runner\n"
        "def breach():\n"
        "    return covariates('held_out'), runner.run_calibration()\n",
        encoding="utf-8",
    )

    errors = integrity.scan_a34_endpoint_sources(tmp_path)

    assert any("generate_partition" in error for error in errors)
    assert any("rc3_calibration_runner" in error for error in errors)


def test_static_scan_rejects_frozen_outcome_api(tmp_path: Path):
    """A score-only endpoint cannot import outcome-bearing analysis objects."""
    integrity = _load_integrity_module()
    endpoint_dir = tmp_path / "src/muru/paper_benchmark"
    endpoint_dir.mkdir(parents=True)
    (endpoint_dir / "a34_contract.py").write_text(
        "from .generator import _synthetic_compounds\n",
        encoding="utf-8",
    )
    (endpoint_dir / "a34_outcome_breach.py").write_text(
        "from .analysis import CaseOutcome\n",
        encoding="utf-8",
    )

    errors = integrity.scan_a34_endpoint_sources(tmp_path)

    assert any("analysis" in error for error in errors)


def test_static_scan_follows_local_bridge_to_forbidden_outcome_api(
    tmp_path: Path,
    monkeypatch,
):
    """A local helper cannot hide an outcome import from an A3.4 endpoint."""
    integrity = _load_integrity_module()
    endpoint_dir = tmp_path / "src/muru/paper_benchmark"
    endpoint_dir.mkdir(parents=True)
    (endpoint_dir / "a34_contract.py").write_text(
        "from .generator import _synthetic_compounds\n",
        encoding="utf-8",
    )
    (endpoint_dir / "a34_bridge_bypass.py").write_text(
        "from .outcome_bridge import make_outcome\n",
        encoding="utf-8",
    )
    (endpoint_dir / "outcome_bridge.py").write_text(
        "from .analysis import CaseOutcome\n"
        "def make_outcome():\n"
        "    return CaseOutcome\n",
        encoding="utf-8",
    )

    original_import = builtins.__import__

    def forbid_bridge_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.endswith("outcome_bridge") or name.endswith("analysis"):
            raise AssertionError(f"static scan imported {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", forbid_bridge_import)

    errors = integrity.scan_a34_endpoint_sources(tmp_path)

    assert any("outcome_bridge.py" in error and "analysis" in error for error in errors)


def test_static_scan_rejects_unbounded_local_package_import(tmp_path: Path):
    """An endpoint cannot bypass the local closure through package-root access."""
    integrity = _load_integrity_module()
    endpoint_dir = tmp_path / "src/muru/paper_benchmark"
    endpoint_dir.mkdir(parents=True)
    (endpoint_dir / "a34_contract.py").write_text(
        "from .generator import _synthetic_compounds\n",
        encoding="utf-8",
    )
    (endpoint_dir / "a34_package_bypass.py").write_text(
        "import muru.paper_benchmark as benchmark\n"
        "OUTCOME = benchmark.analysis.CaseOutcome\n",
        encoding="utf-8",
    )

    errors = integrity.scan_a34_endpoint_sources(tmp_path)

    assert any("muru.paper_benchmark" in error for error in errors)
