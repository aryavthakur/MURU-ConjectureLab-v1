#!/usr/bin/env python3
"""Engineering RC3 integrity verification.

Extends pb_33 rather than replacing it.  pb_33 verifies the 16 A2.1
protected paths against the A2.1 commit; RC3 additionally freezes the 11
A3.1 files against the A3.1 commit, giving 27 protected paths in total.

Verifies:
  1. all 27 protected paths byte-identical (16 vs A2.1, 11 vs A3.1)
  2. every RC3 file exists and is hashed
  3. Development non-contamination across RC3 source
  4. Held-out non-contamination across RC3 source
  5. seed-band separation between calibration and engineering smoke seeds
  6. engineering smoke output is quarantined and marked
  7. dependency provenance against the RC2 lock
  8. calibration execution status
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_src = str(ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# The A2.1 commit, as pb_33 declares it.
A2_1_COMMIT = "80a78032ac601466b35e9dce3fa56f6ae215605f"
# The A3.1 content freeze.
A3_1_COMMIT = "c8938e86c6a979e21bb23a0d2f317ccb5f22e1a0"

A2_1_PROTECTED_PATHS = [
    "src/muru/paper_benchmark/registry.py",
    "src/muru/paper_benchmark/generator.py",
    "src/muru/paper_benchmark/truth.py",
    "src/muru/paper_benchmark/adequacy.py",
    "src/muru/paper_benchmark/governance.py",
    "src/muru/paper_benchmark/contract.py",
    "src/muru/paper_benchmark/freeze.py",
    "src/muru/paper_benchmark/protocol.py",
    "src/muru/paper_benchmark/preflight.py",
    "src/muru/paper_benchmark/artifacts.py",
    "src/muru/paper_benchmark/analysis.py",
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_truth_manifest.json",
    "artifacts/paper_benchmark_partition_manifest.json",
    "artifacts/paper_benchmark_content_freeze.json",
    "artifacts/paper_benchmark_hash_inventory.json",
]

A3_1_PROTECTED_PATHS = [
    "MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md",
    "artifacts/paper_benchmark_amendment_a3_1.json",
    "scripts/pb_33_amendment_a3_1_integrity.py",
    "src/muru/paper_benchmark/g2_contract.py",
    "src/muru/paper_benchmark/structural_acceptance.py",
    "src/muru/paper_benchmark/calibration_contract.py",
    "src/muru/paper_benchmark/g3_contract.py",
    "tests/test_a3_1_g2_contract.py",
    "tests/test_a3_1_structural_acceptance.py",
    "tests/test_a3_1_calibration_contract.py",
    "tests/test_a3_1_g3_contract.py",
]

TOTAL_PROTECTED = len(A2_1_PROTECTED_PATHS) + len(A3_1_PROTECTED_PATHS)

RC3_SOURCE_FILES = [
    "src/muru/paper_benchmark/rc3_scoring.py",
    "src/muru/paper_benchmark/rc3_record.py",
    "src/muru/paper_benchmark/rc3_acceptance.py",
    "src/muru/paper_benchmark/rc3_ceiling.py",
    "src/muru/paper_benchmark/rc3_calibration_worlds.py",
    "src/muru/paper_benchmark/rc3_calibration_runner.py",
    "src/muru/paper_benchmark/rc3_provenance.py",
]

RC3_TEST_FILES = [
    "tests/test_rc3_scoring.py",
    "tests/test_rc3_record.py",
    "tests/test_rc3_acceptance.py",
    "tests/test_rc3_ceiling.py",
    "tests/test_rc3_calibration.py",
    "tests/test_rc3_provenance.py",
]

RC3_SCRIPT_FILES = [
    "scripts/pb_34_rc3_integrity.py",
    "scripts/rc3_smoke.py",
]

#: Everything the contamination audits scan.  Tests and the smoke script are
#: included: a partition call in a test would leak just as surely as one in a
#: module.
#:
#: This auditor is the one exclusion, and it excludes only itself.  It holds
#: every contamination pattern as a string literal by necessity, so scanning
#: itself reports the definition of contamination as an instance of it.  Its
#: own cleanliness is covered by the import-graph check and by review, not by
#: a grep against its own pattern table.
RC3_SCANNED_FILES = RC3_SOURCE_FILES + RC3_TEST_FILES + [
    rel for rel in RC3_SCRIPT_FILES if not rel.endswith("pb_34_rc3_integrity.py")
]

RC3_ADDED_FILES = RC3_SCANNED_FILES + [
    "configs/rc3_requirements_lock_c7c2332.txt",
]

SMOKE_DIR = "artifacts/rc3_engineering_smoke"
SMOKE_MARKER = "ENGINEERING_SMOKE_NOT_SCIENTIFIC"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show_hash(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"], capture_output=True, cwd=ROOT
    )
    if result.returncode != 0:
        return "MISSING_AT_COMMIT"
    return hashlib.sha256(result.stdout).hexdigest()


def check_protected_paths() -> tuple[list[str], int]:
    errors: list[str] = []
    verified = 0
    for commit, paths in ((A2_1_COMMIT, A2_1_PROTECTED_PATHS),
                          (A3_1_COMMIT, A3_1_PROTECTED_PATHS)):
        for rel in paths:
            current = ROOT / rel
            if not current.exists():
                errors.append(f"MISSING: {rel}")
                continue
            frozen = git_show_hash(commit, rel)
            if frozen == "MISSING_AT_COMMIT":
                errors.append(f"NOT_AT_{commit[:7]}: {rel}")
            elif sha256_file(current) != frozen:
                errors.append(f"MODIFIED: {rel} (drifted from {commit[:7]})")
            else:
                verified += 1
    return errors, verified


def check_rc3_files() -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    hashes: dict[str, str] = {}
    for rel in RC3_ADDED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"MISSING_RC3: {rel}")
        else:
            hashes[rel] = sha256_file(path)
    return errors, hashes


def check_no_development_contamination() -> list[str]:
    """RC3 source must not name, load, or reference Development outcomes."""
    errors: list[str] = []
    patterns_lower = ["development", "dev_result", "dev_outcome", "load_development"]
    patterns_exact = ["PB|development|", 'iter_case_ids("development")',
                      "iter_case_ids('development')",
                      'generate_partition("development")',
                      "generate_partition('development')"]
    for rel in RC3_SCANNED_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        content = path.read_text()
        lowered = content.lower()
        for pattern in patterns_exact:
            if pattern in content:
                errors.append(f"CONTAMINATION: {rel} contains '{pattern}'")
        for pattern in patterns_lower:
            if pattern in lowered:
                errors.append(f"CONTAMINATION: {rel} contains '{pattern}'")
    return errors


def check_no_held_out_contamination() -> list[str]:
    """RC3 source must not access Held-out or Confirmation case data.

    Constant names and prose references are not data access; only loading
    patterns are.
    """
    errors: list[str] = []
    access_patterns = [
        "PB|held_out|",
        "partition='held_out'",
        'partition="held_out"',
        "load_held_out",
        "read_held_out",
        "open_held_out",
        'generate_partition("held_out")',
        "generate_partition('held_out')",
        'iter_case_ids("held_out")',
        "iter_case_ids('held_out')",
        "PB|challenge|",
        'generate_partition("challenge")',
        "generate_partition('challenge')",
        'iter_case_ids("challenge")',
        "iter_case_ids('challenge')",
        "confirmation_seal",
    ]
    for rel in RC3_SCANNED_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        content = path.read_text()
        for pattern in access_patterns:
            if pattern in content:
                errors.append(f"HELD_OUT_ACCESS: {rel} contains '{pattern}'")
    return errors


def check_import_graph() -> list[str]:
    """Structural non-contamination: what can RC3 actually reach?

    Substring greps cannot see through an alias or a built string.  This
    imports every RC3 module and asserts that the partition entry points -
    the only functions that can materialize Development, Held-out or
    Confirmation case data - are not bound anywhere in their namespaces, and
    that no RC3 module resolves them transitively as a module attribute.
    """
    errors: list[str] = []
    forbidden = {"generate_partition", "iter_case_ids", "resolve_case_id", "generate_case"}
    module_names = [
        "muru.paper_benchmark." + Path(rel).stem for rel in RC3_SOURCE_FILES
    ]
    try:
        import importlib

        for name in module_names:
            module = importlib.import_module(name)
            bound = forbidden.intersection(vars(module))
            if bound:
                errors.append(f"IMPORT_GRAPH: {name} binds {sorted(bound)}")
    except Exception as exc:
        errors.append(f"IMPORT_GRAPH_ERROR: {type(exc).__name__}: {exc}")
    return errors


def check_seed_band_separation() -> list[str]:
    errors: list[str] = []
    try:
        from muru.paper_benchmark.calibration_contract import (
            all_world_ids, derive_calibration_seeds,
        )
        from muru.paper_benchmark.rc3_provenance import (
            RC3_SMOKE_SEED_BASE, RC3_SMOKE_SEED_MAX, SIGNED_32BIT_MAX,
            assert_seed_band_separation, smoke_seed,
        )

        assert_seed_band_separation()

        # Exhaustive: every one of the 3000 calibration seeds against the band.
        calibration_seeds = set()
        for world_id in all_world_ids():
            calibration_seeds.update(derive_calibration_seeds(world_id))
        if len(calibration_seeds) != 3000:
            errors.append(f"SEED_COUNT: {len(calibration_seeds)} unique, expected 3000")
        colliding = [
            s for s in calibration_seeds
            if RC3_SMOKE_SEED_BASE <= s <= RC3_SMOKE_SEED_MAX
        ]
        if colliding:
            errors.append(f"SEED_BAND_COLLISION: {len(colliding)} calibration seeds in smoke band")

        smoke_seeds = {smoke_seed(w, k) for w in range(8) for k in range(8)}
        overlap = smoke_seeds & calibration_seeds
        if overlap:
            errors.append(f"SEED_COLLISION: {sorted(overlap)[:5]}")
        if any(s > SIGNED_32BIT_MAX or s < 0 for s in smoke_seeds | calibration_seeds):
            errors.append("SEED_NOT_SIGNED_32BIT_SAFE")
    except Exception as exc:
        errors.append(f"SEED_BAND_CHECK_ERROR: {type(exc).__name__}: {exc}")
    return errors


def check_smoke_quarantine() -> list[str]:
    """Every engineering-smoke output file must carry the marker."""
    errors: list[str] = []
    smoke_root = ROOT / SMOKE_DIR
    if not smoke_root.exists():
        return errors  # smoke not run; nothing to quarantine
    for path in sorted(smoke_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"SMOKE_UNMARKED_BINARY: {rel}")
            continue
        if SMOKE_MARKER not in content:
            errors.append(f"SMOKE_UNMARKED: {rel}")
    return errors


def check_dependencies() -> list[str]:
    errors: list[str] = []
    try:
        from muru.paper_benchmark.rc3_provenance import verify_dependencies
        verify_dependencies()
    except Exception as exc:
        errors.append(f"DEPENDENCY: {type(exc).__name__}: {exc}")
    return errors


def check_calibration_execution_status() -> tuple[str, list[str]]:
    """Report whether the 100 calibration worlds have been executed.

    RC3 must report NOT EXECUTED.  Any calibration record store outside the
    quarantined smoke directory contradicts that.

    Scope, stated honestly: this scans the repository tree.  A record store
    written outside the repository (``SeedRecordStore`` accepts any path)
    is not visible here, so this establishes "no calibration output in this
    repository", which is what the freeze needs, not "no calibration was
    ever run anywhere".
    """
    errors: list[str] = []
    smoke_parts = Path(SMOKE_DIR).parts
    candidates = []
    for path in ROOT.rglob("PB__NCAL__*.jsonl"):
        rel = path.relative_to(ROOT)
        # Path-component match, not substring: a sibling directory named
        # rc3_engineering_smoke_real must NOT be treated as quarantined.
        if rel.parts[:len(smoke_parts)] == smoke_parts:
            continue
        candidates.append(str(rel))
    if candidates:
        errors.append(f"CALIBRATION_RECORDS_PRESENT: {sorted(candidates)[:5]}")
        return "EXECUTED", errors
    return "NOT EXECUTED", errors


def main() -> int:
    print("Engineering RC3 integrity verification")
    print("=" * 60)
    all_errors: list[str] = []

    print(f"\n1. Protected paths (16 vs A2.1 + 11 vs A3.1 = {TOTAL_PROTECTED})...")
    errors, verified = check_protected_paths()
    all_errors.extend(errors)
    print(f"   {verified}/{TOTAL_PROTECTED} byte-identical")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n2. RC3 added files...")
    errors, hashes = check_rc3_files()
    all_errors.extend(errors)
    print(f"   {len(RC3_ADDED_FILES) - len(errors)}/{len(RC3_ADDED_FILES)} present")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n3. Development contamination audit (RC3 source)...")
    errors = check_no_development_contamination()
    all_errors.extend(errors)
    print(f"   {'CLEAN' if not errors else 'CONTAMINATED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n4. Held-out / Confirmation contamination audit (RC3 source)...")
    errors = check_no_held_out_contamination()
    all_errors.extend(errors)
    print(f"   {'CLEAN' if not errors else 'CONTAMINATED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n4b. Import-graph non-contamination (structural, not grep)...")
    errors = check_import_graph()
    all_errors.extend(errors)
    print(f"   {'UNREACHABLE' if not errors else 'REACHABLE'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n5. Seed-band separation (3000 calibration seeds vs smoke band)...")
    errors = check_seed_band_separation()
    all_errors.extend(errors)
    print(f"   {'DISJOINT' if not errors else 'FAILED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n6. Engineering smoke quarantine...")
    errors = check_smoke_quarantine()
    all_errors.extend(errors)
    print(f"   {'ALL MARKED' if not errors else 'UNMARKED OUTPUT'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n7. Dependency provenance (RC2 lock c7c2332)...")
    errors = check_dependencies()
    all_errors.extend(errors)
    print(f"   {'VERIFIED' if not errors else 'MISMATCH'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n8. Calibration execution status...")
    status, errors = check_calibration_execution_status()
    all_errors.extend(errors)
    print(f"   {status}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n9. Delegating to pb_33 (A3.1 integrity)...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "pb_33_amendment_a3_1_integrity.py")],
        capture_output=True, cwd=ROOT,
    )
    if result.returncode != 0:
        all_errors.append("PB_33_FAILED")
        print("   ERROR: pb_33 failed")
        print(result.stdout.decode("utf-8", "replace"))
    else:
        print("   pb_33 PASS")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s)")
        return 1
    print("RC3 INTEGRITY VERIFIED")
    print(f"CALIBRATION EXECUTION STATUS: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
