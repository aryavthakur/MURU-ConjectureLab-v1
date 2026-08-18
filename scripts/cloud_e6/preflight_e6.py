#!/usr/bin/env python
"""Preflight verification for E6 Cloud Execution.

Results-blind.  Verifies the complete software stack, Julia identity,
pinned locks, classifier version, and file system permissions without
running any un-licensed experiment.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from muru.discovery.engine import cap_threads  # noqa: E402
cap_threads()

from muru.paper_benchmark.rc3_provenance import verify_dependencies  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import classify_cache as cc  # noqa: E402


def check_all() -> bool:
    print("=== MURU E6 Cloud Preflight Check ===")
    errors = []

    # 1. Dependency check
    try:
        deps = verify_dependencies()
        print(f"[OK] Python dependencies verified: {len(deps)} core engines match lock")
    except Exception as exc:
        errors.append(f"DEPENDENCY ERROR: {exc}")

    # 2. Julia stack check
    import pb_37_environment_closure as pb37
    try:
        julia_stack = pb37.assert_julia_identity()
        print(f"[OK] Julia stack verified: {julia_stack}")
    except Exception as exc:
        errors.append(f"JULIA STACK ERROR: {exc}")

    # 3. Classifier hash check
    expected_hash = "90a3b5ea3a83b0e9587e3b1e4e54e188afb8e893fabc9293d9177bc767089e7a"
    actual_hash = cc.compute_classifier_version(ROOT)
    if actual_hash == expected_hash:
        print(f"[OK] Classifier version hash verified: {actual_hash}")
    else:
        errors.append(f"CLASSIFIER HASH MISMATCH: expected {expected_hash}, got {actual_hash}")

    # 4. Output directory permissions check
    out_dir = ROOT / "results" / "e6"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        test_file = out_dir / ".permission_check"
        test_file.write_text("ok")
        test_file.unlink()
        print(f"[OK] Output directory writable: {out_dir}")
    except Exception as exc:
        errors.append(f"DIRECTORY PERMISSION ERROR: {exc}")

    if errors:
        print("\n[PREFLIGHT FAILED]")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n[PREFLIGHT PASSED] Cloud host is scientifically and operationally ready.")
    return True


if __name__ == "__main__":
    success = check_all()
    sys.exit(0 if success else 1)
