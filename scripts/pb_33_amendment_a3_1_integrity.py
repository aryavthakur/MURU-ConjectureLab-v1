#!/usr/bin/env python3
"""Amendment A3.1 integrity verification.

Verifies:
  - A2.1 protected paths are byte-identical
  - A3.1 added files exist and hash correctly
  - Calibration seed invariants hold
  - No Development or Held-out contamination in A3.1 code
  - Frozen parameters match contract
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Ensure src/ is importable (matches pytest.ini pythonpath = src)
_src = str(ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
_scripts = str(Path(__file__).resolve().parent)
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)
SRC = ROOT / "src" / "muru" / "paper_benchmark"

# RC5: the union view, so this check recognizes any authorized ledger by
# path+hash -- RC4.2's R1-R4 repair, RC4.2.1's tooling change, and RC5's A3.5
# implementation alike. The classification rule is unchanged: a protected path
# may differ from A2.1 ONLY when BOTH its old and its new bytes match a ledger
# entry exactly. Before this, the check consulted the RC4.2-only dict, so a
# change authorized by either later ledger was reported as unauthorized drift.
from pb_rc4_2_authorized_delta import (  # noqa: E402
    ALL_AUTHORIZED_BY_PATH as AUTHORIZED_BY_PATH,
)

# A2.1 parent commit
A2_1_COMMIT = "80a78032ac601466b35e9dce3fa56f6ae215605f"

# Paths that must be byte-identical to A2.1
PROTECTED_PATHS = [
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

# A3.1 added files
ADDED_FILES = [
    "MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md",
    "src/muru/paper_benchmark/g2_contract.py",
    "src/muru/paper_benchmark/structural_acceptance.py",
    "src/muru/paper_benchmark/calibration_contract.py",
    "src/muru/paper_benchmark/g3_contract.py",
    "tests/test_a3_1_g2_contract.py",
    "tests/test_a3_1_structural_acceptance.py",
    "tests/test_a3_1_calibration_contract.py",
    "tests/test_a3_1_g3_contract.py",
    "scripts/pb_33_amendment_a3_1_integrity.py",
    "artifacts/paper_benchmark_amendment_a3_1.json",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show_hash(commit: str, path: str) -> str:
    """Get SHA-256 of a file at a specific commit."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        capture_output=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return "MISSING_AT_COMMIT"
    return hashlib.sha256(result.stdout).hexdigest()


def check_protected_paths() -> tuple[list[str], list[str]]:
    """Returns (errors, rc4_2_authorized_delta_paths).

    RC4.2.1: a protected path may differ from A2.1 ONLY if it is exactly the
    ledgered RC4.2 authorized-defect-repair delta (old and new bytes both
    pinned; scripts/pb_rc4_2_authorized_delta.py). Any other drift is still
    an error, exactly as before RC4.2 existed.
    """
    errors = []
    rc4_2_delta: list[str] = []
    for rel in PROTECTED_PATHS:
        current = ROOT / rel
        if not current.exists():
            errors.append(f"MISSING: {rel}")
            continue
        current_hash = sha256_file(current)
        parent_hash = git_show_hash(A2_1_COMMIT, rel)
        if parent_hash == "MISSING_AT_COMMIT":
            errors.append(f"NOT_IN_A2_1: {rel}")
        elif current_hash != parent_hash:
            entry = AUTHORIZED_BY_PATH.get(rel)
            if entry is not None and entry.old_sha256 == parent_hash and entry.new_sha256 == current_hash:
                rc4_2_delta.append(rel)
                continue
            errors.append(f"MODIFIED: {rel} (current={current_hash[:12]}, a2.1={parent_hash[:12]})")
    return errors, rc4_2_delta


def check_added_files() -> tuple[list[str], dict[str, str]]:
    errors = []
    hashes = {}
    for rel in ADDED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"MISSING_ADDED: {rel}")
        else:
            hashes[rel] = sha256_file(path)
    return errors, hashes


def check_no_development_contamination() -> list[str]:
    """Verify A3.1 code does not load Development outcomes."""
    errors = []
    contamination_patterns_lower = [
        "development",
        "dev_result",
        "dev_outcome",
        "load_development",
    ]
    contamination_patterns_exact = [
        "PB|development|",
    ]
    for rel in ADDED_FILES:
        if not rel.startswith("src/"):
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        content = path.read_text()
        content_lower = content.lower()
        for pattern in contamination_patterns_exact:
            if pattern in content:
                errors.append(f"CONTAMINATION: {rel} contains '{pattern}'")
        for pattern in contamination_patterns_lower:
            if pattern in content_lower:
                # Allow documentation references
                if pattern == "development" and "post-development" in content.lower():
                    continue
                if pattern == "development" and "predates development" in content.lower():
                    continue
                if pattern == "development" and "predates_development" in content.lower():
                    continue
                errors.append(f"CONTAMINATION: {rel} contains '{pattern}'")
    return errors


def check_no_held_out_contamination() -> list[str]:
    """Verify A3.1 code does not access Held-out data.

    Constant names like G3_HELD_OUT_DENOMINATOR and documentation
    references to 'Held-out' are not data access.  Only actual data
    loading patterns (partition='held_out', PB|held_out|, file I/O)
    constitute contamination.
    """
    errors = []
    # Patterns that indicate actual data access, not just naming
    access_patterns = [
        'PB|held_out|',
        "partition='held_out'",
        'partition="held_out"',
        "load_held_out",
        "read_held_out",
        "open_held_out",
        "generate_partition(\"held_out\")",
        "generate_partition('held_out')",
        "iter_case_ids(\"held_out\")",
        "iter_case_ids('held_out')",
    ]
    for rel in ADDED_FILES:
        if not rel.startswith("src/"):
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        content = path.read_text()
        for pattern in access_patterns:
            if pattern in content:
                errors.append(f"HELD_OUT_ACCESS: {rel} contains '{pattern}'")
    return errors


def check_calibration_seeds() -> list[str]:
    """Verify seed invariants programmatically."""
    errors = []
    try:
        from muru.paper_benchmark.calibration_contract import verify_seed_invariants
        results = verify_seed_invariants()
        for key, value in results.items():
            if not value:
                errors.append(f"SEED_INVARIANT_FAILED: {key}")
    except ImportError as e:
        errors.append(f"IMPORT_ERROR: {e}")
    return errors


def check_frozen_parameters() -> list[str]:
    """Verify frozen parameters match contract."""
    errors = []
    try:
        from muru.paper_benchmark.g2_contract import G2_HELD_OUT_DENOMINATOR, G2_WILSON_LOWER_GATE
        from muru.paper_benchmark.g3_contract import G3_HELD_OUT_DENOMINATOR, G3_WILSON_UPPER_GATE
        from muru.paper_benchmark.calibration_contract import (
            N_CALIBRATION_WORLDS, N_SEEDS_PER_WORLD,
            PB_SEED_BASE, PB_SEED_SPREAD,
            QUANTILE_LEVEL, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED,
        )
        from muru.paper_benchmark.structural_acceptance import (
            STABILITY_GATE, MAX_COMPLEXITY, MAX_INVALID_FRACTION,
            CEILING_FRACTION_GATE, CEILING_WAIVER_THRESHOLD,
        )

        checks = [
            ("G2_DENOMINATOR", G2_HELD_OUT_DENOMINATOR, 144),
            ("G2_GATE", G2_WILSON_LOWER_GATE, 0.70),
            ("G3_DENOMINATOR", G3_HELD_OUT_DENOMINATOR, 36),
            ("G3_GATE", G3_WILSON_UPPER_GATE, 0.15),
            ("N_WORLDS", N_CALIBRATION_WORLDS, 100),
            ("N_SEEDS", N_SEEDS_PER_WORLD, 30),
            ("SEED_BASE", PB_SEED_BASE, 2_110_000_000),
            ("SEED_SPREAD", PB_SEED_SPREAD, 370_000),
            ("QUANTILE", QUANTILE_LEVEL, 0.95),
            ("BOOTSTRAP_N", BOOTSTRAP_RESAMPLES, 2000),
            ("BOOTSTRAP_SEED", BOOTSTRAP_SEED, 20260812),
            ("STABILITY", STABILITY_GATE, 20),
            ("MAX_COMPLEXITY", MAX_COMPLEXITY, 20),
            ("MAX_INVALID", MAX_INVALID_FRACTION, 0.005),
            ("CEILING_GATE", CEILING_FRACTION_GATE, 0.80),
            ("CEILING_WAIVER", CEILING_WAIVER_THRESHOLD, 0.05),
        ]
        for name, actual, expected in checks:
            if actual != expected:
                errors.append(f"PARAM_MISMATCH: {name} = {actual}, expected {expected}")
    except ImportError as e:
        errors.append(f"IMPORT_ERROR: {e}")
    return errors


def main() -> int:
    print("Amendment A3.1 integrity verification")
    print("=" * 60)

    all_errors: list[str] = []

    print("\n1. Protected paths (must match A2.1)...")
    errors, rc4_2_delta = check_protected_paths()
    all_errors.extend(errors)
    unchanged_count = len(PROTECTED_PATHS) - len(errors) - len(rc4_2_delta)
    print(f"   {unchanged_count}/{len(PROTECTED_PATHS)} byte-identical")
    if rc4_2_delta:
        print(f"   RC4.2 AUTHORIZED DELTA: {', '.join(rc4_2_delta)}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n2. Added files...")
    errors, hashes = check_added_files()
    all_errors.extend(errors)
    print(f"   {len(ADDED_FILES) - len(errors)}/{len(ADDED_FILES)} present")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n3. Development contamination audit...")
    errors = check_no_development_contamination()
    all_errors.extend(errors)
    print(f"   {'CLEAN' if not errors else 'CONTAMINATED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n4. Held-out contamination audit...")
    errors = check_no_held_out_contamination()
    all_errors.extend(errors)
    print(f"   {'CLEAN' if not errors else 'CONTAMINATED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n5. Calibration seed invariants...")
    errors = check_calibration_seeds()
    all_errors.extend(errors)
    print(f"   {'ALL PASS' if not errors else 'FAILED'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n6. Frozen parameters...")
    errors = check_frozen_parameters()
    all_errors.extend(errors)
    print(f"   {'ALL MATCH' if not errors else 'MISMATCH'}")
    for e in errors:
        print(f"   ERROR: {e}")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s)")
        return 1
    else:
        print("A3.1 INTEGRITY VERIFIED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
