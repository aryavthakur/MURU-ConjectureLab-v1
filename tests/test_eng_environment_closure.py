"""RC4.1 environment closure tests.

Engineering only.  Nothing here reads a benchmark case, a partition, or a
scientific outcome; the point is that the tracked environment specification
is executable and self-contained, and that closing it moved no science.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pb_37_environment_closure.py"

sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("pb_37_environment_closure", SCRIPT)
closure = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(closure)

from muru.paper_benchmark.rc3_provenance import (  # noqa: E402
    RC2_LOCK_RELPATH,
    RC2_LOCK_SHA256,
    REQUIRED_PACKAGES,
    read_lock_pins,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_tracked_bootstrap_is_the_same_bytes_as_the_enforced_pin_source():
    """README tells a replicator to install from requirements.lock.txt.

    The frozen runtime guard enforces configs/rc3_requirements_lock_c7c2332
    .txt.  If those two files can differ, a fresh clone installs one
    environment and is then checked against another.
    """
    tracked = _sha256(ROOT / "requirements.lock.txt")
    enforced = _sha256(ROOT / RC2_LOCK_RELPATH)
    assert tracked == enforced
    assert tracked == RC2_LOCK_SHA256


def test_every_package_the_frozen_guard_requires_is_pinned_in_the_tracked_lock():
    pins = closure.read_pins(ROOT / "requirements.lock.txt")
    missing = sorted(
        name for name in REQUIRED_PACKAGES if name.lower() not in pins
    )
    assert missing == []


def test_the_previously_missing_engines_are_now_pinned():
    """The exact gap the hostile lineage audit named."""
    pins = closure.read_pins(ROOT / "requirements.lock.txt")
    for distribution in ("sympy", "mpmath", "pysr", "gplearn", "juliacall", "juliapkg"):
        assert distribution in pins, distribution


def test_no_third_party_import_escapes_the_lock():
    """A hard import that nothing pins is an unpinned transitive escape."""
    pins = closure.read_pins(ROOT / "requirements.lock.txt")
    escaped = []
    for name in closure.third_party_imports():
        distribution = closure.IMPORT_TO_DISTRIBUTION.get(name, name)
        if distribution.lower() not in pins:
            escaped.append(name)
    assert sorted(escaped) == []


def test_the_lock_pins_every_distribution_exactly_once_with_an_equality():
    lines = [
        line.strip()
        for line in (ROOT / "requirements.lock.txt").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert all("==" in line for line in lines)
    names = [line.split("==", 1)[0].strip().lower() for line in lines]
    assert len(names) == len(set(names))
    assert len(names) == 50


def test_read_lock_pins_accepts_the_tracked_lock_unchanged():
    """The frozen guard's own parser must accept the repaired bootstrap."""
    pins = read_lock_pins(ROOT / "requirements.lock.txt")
    assert pins["pysr"] == "1.5.10"
    assert pins["sympy"] == "1.14.0"
    assert pins["gplearn"] == "0.4.3"


def test_the_julia_side_identity_is_bound_and_hashed():
    project = ROOT / closure.JULIA_PROJECT_RELPATH
    manifest = ROOT / closure.JULIA_MANIFEST_RELPATH
    assert project.exists() and manifest.exists()
    assert _sha256(project) == closure.JULIA_PROJECT_SHA256
    assert _sha256(manifest) == closure.JULIA_MANIFEST_SHA256
    text = manifest.read_text()
    assert 'julia_version = "1.12.6"' in text
    assert closure.FROZEN_SYMBOLICREGRESSION_JL_VERSION == "1.11.3"
    assert f'version = "{closure.FROZEN_SYMBOLICREGRESSION_JL_VERSION}"' in text


def test_the_closure_verifier_passes_in_this_environment(tmp_path):
    """Written to a temporary path: a test must not rewrite tracked evidence."""
    process = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(tmp_path / "manifest.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_the_tracked_environment_manifest_matches_this_tree():
    import json

    recorded = json.loads(
        (ROOT / "configs" / "rc4_1_environment_manifest.json").read_text()
    )
    assert recorded["static_closure_verified"] is True
    # Derived from git against the RC4 parent, not a self-declared flag.
    assert recorded["paper_benchmark_paths_changed_vs_rc4_parent"] == []
    assert recorded["pinned_distribution_count"] == 50
    assert recorded["tracked_lock_sha256"] == _sha256(ROOT / "requirements.lock.txt")
    assert recorded["pin_source_sha256"] == recorded["tracked_lock_sha256"]
    assert recorded["unpinned_imports"] == []
    assert recorded["julia"]["julia"] == "1.12.6"
    assert recorded["julia"]["SymbolicRegression.jl"] == "1.11.3"


def test_the_manifest_does_not_claim_the_julia_identity_was_verified():
    """The static closure flag must not be readable as a Julia guarantee.

    pb_37 writes the manifest before the optional --start-julia block runs, so
    a manifest that claimed to cover Julia would be claiming something it
    cannot know.  It points at the separate proof instead.
    """
    import json

    recorded = json.loads(
        (ROOT / "configs" / "rc4_1_environment_manifest.json").read_text()
    )
    assert "closure_verified" not in recorded
    assert "julia_live" not in recorded
    assert (
        recorded["julia_identity_proof_relpath"]
        == "configs/rc4_1_julia_identity_proof.json"
    )


def test_the_julia_identity_gate_has_no_prospective_caller_yet():
    """Pins reviewer finding B1 so it cannot be forgotten by RC5.

    assert_julia_identity() fails closed WHEN CALLED, but nothing on a
    prospective execution path calls it, because RC4 has no prospective case
    execution path at all.  When that path is built it MUST call this before
    the first search seed.  If a caller appears in src/, this test should be
    updated to assert the caller exists rather than deleted.
    """
    callers = []
    for base in ("src", "scripts"):
        for path in sorted((ROOT / base).rglob("*.py")):
            if path.name == "pb_37_environment_closure.py":
                continue
            if "assert_julia_identity" in path.read_text(encoding="utf-8"):
                callers.append(str(path.relative_to(ROOT)))
    assert callers == [], (
        "a caller appeared; update this test to assert the prospective "
        f"execution path calls the gate: {callers}"
    )


def test_the_julia_identity_proof_is_a_live_reading_not_a_declaration():
    """`--start-julia` booted a real Julia and read the loaded module versions.

    Kept in its own file so a later run without `--start-julia` cannot erase
    the proof by replacing it with a run that never booted Julia.
    """
    import json

    proof = json.loads(
        (ROOT / "configs" / "rc4_1_julia_identity_proof.json").read_text()
    )
    assert proof["julia_identity_verified"] is True
    assert proof["live"] == proof["frozen"]
    assert proof["live"]["julia"] == closure.FROZEN_JULIA_VERSION
    assert (
        proof["live"]["SymbolicRegression.jl"]
        == closure.FROZEN_SYMBOLICREGRESSION_JL_VERSION
    )


def test_gplearn_scope_is_declared_and_no_prospective_module_executes_it():
    assert "gplearn" in closure.DECLARED_SCOPES
    prospective = ROOT / "src" / "muru" / "paper_benchmark"
    offenders = []
    for path in sorted(prospective.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import gplearn", "from gplearn")):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def _engineering_paths_module():
    spec = importlib.util.spec_from_file_location(
        "pb_engineering_paths_under_test",
        ROOT / "scripts" / "pb_engineering_paths.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_closing_the_environment_changed_no_scientific_definition():
    """The engineering exemption may only cover engineering paths."""
    module = _engineering_paths_module()

    assert module.ENGINEERING_CHANGED_PATHS == frozenset({"requirements.lock.txt"})
    for path in module.ENGINEERING_CHANGED_PATHS:
        assert not path.startswith(module.SCIENCE_SURFACE_PREFIXES), path


@pytest.mark.parametrize(
    "science_path",
    [
        "src/muru/paper_benchmark/truth.py",
        "artifacts/paper_benchmark_truth_manifest.json",
        "MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md",
        "tests/test_a3_1_g2_contract.py",
        "truth/held_out.jsonl",
        "inputs/held_out.jsonl",
    ],
)
def test_the_engineering_guard_actually_fires_rather_than_being_decorative(science_path):
    module = _engineering_paths_module()
    module.ENGINEERING_CHANGED_PATHS = frozenset({science_path})
    with pytest.raises(module.EngineeringExemptionCoversScience):
        module.assert_engineering_paths_carry_no_science()


def test_all_three_amendment_scripts_share_one_engineering_declaration():
    """Three copies of a governance exemption would drift.  There is one."""
    for script in (
        "pb_30_amendment_a1_integrity.py",
        "pb_31_amendment_a2_integrity.py",
        "pb_32_amendment_a2_1_integrity.py",
    ):
        text = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert "from pb_engineering_paths import" in text, script
        assert "assert_engineering_paths_carry_no_science()" in text, script
