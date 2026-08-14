"""Verify Amendment A1 against the original content freeze, byte for byte.

Every tracked path at `d94d2c9` is compared with the amendment tree by SHA-256
of its bytes.  Only the declared adequacy paths may differ; anything else is an
integrity breach and this script exits non-zero.

The comparison is mechanical hashing.  It never parses, scores, or otherwise
inspects a Development or Held-out scientific record.  The held-out row files
are untracked regenerable bytes that are absent from the tree entirely; their
integrity is carried by the frozen `paper_benchmark_hash_inventory.json`, which
is itself one of the protected unchanged paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

ORIGINAL_CONTENT_FREEZE = "d94d2c9"

#: Amendment A2 repaired F16 and Amendment A2.1 bumped the generator version on
#: top of that, so paths that differ from `d94d2c9` are now the union of all
#: three declared sets.  Each amendment's sets are imported rather than
#: restated so the integrity scripts cannot drift apart, and every changed path
#: is attributed to the amendment that owns it.
from pb_31_amendment_a2_integrity import (  # noqa: E402
    ALLOWED_ADDED_PATHS as A2_ALLOWED_ADDED_PATHS,
    ALLOWED_CHANGED_PATHS as A2_ALLOWED_CHANGED_PATHS,
)
from pb_32_amendment_a2_1_integrity import (  # noqa: E402
    ALLOWED_ADDED_PATHS as A2_1_ALLOWED_ADDED_PATHS,
    ALLOWED_CHANGED_PATHS as A2_1_ALLOWED_CHANGED_PATHS,
)

ALLOWED_CHANGED_PATHS = frozenset({
    "MURU_PAPER_BENCHMARK_FREEZE.md",
    "MURU_PAPER_BENCHMARK_METRICS.md",
    "MURU_PAPER_BENCHMARK_PROTOCOL.md",
    "src/muru/paper_benchmark/analysis.py",
    "tests/test_paper_benchmark_docs.py",
})

ALLOWED_ADDED_PATHS = frozenset({
    "MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md",
    "artifacts/paper_benchmark_amendment_a1.json",
    "scripts/pb_30_amendment_a1_integrity.py",
    "src/muru/paper_benchmark/adequacy.py",
    "tests/test_paper_benchmark_adequacy.py",
    "tests/test_paper_benchmark_amendment_integrity.py",
})

#: Engineering-owned changes inside the frozen set, declared in one place so
#: pb_30/pb_31/pb_32 cannot disagree, and reported separately from
#: `changed_by_amendment` so an engineering exemption can never be read as a
#: science amendment.
from pb_engineering_paths import (  # noqa: E402
    ENGINEERING_CHANGED_PATHS,
    ENGINEERING_OWNER,
    science_surface_violations,
    SCIENCE_SURFACE_PREFIXES,
    assert_engineering_paths_carry_no_science,
)

#: RC4.2's authorized, byte-pinned defect-repair delta. Not an amendment and
#: not an engineering exemption (it touches the science surface); see
#: pb_rc4_2_authorized_delta.py.
from pb_rc4_2_authorized_delta import split_unexpected_changed  # noqa: E402

#: The provenance record cannot contain its own hash; it is verified by the
#: contract tests instead.
SELF_EXCLUDED = "artifacts/paper_benchmark_amendment_a1.json"


def _git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _frozen_paths() -> list[str]:
    listing = _git("ls-tree", "-r", "--name-only", ORIGINAL_CONTENT_FREEZE)
    return [line for line in listing.splitlines() if line]


def _frozen_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{ORIGINAL_CONTENT_FREEZE}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_manifest() -> dict[str, object]:
    assert_engineering_paths_carry_no_science()
    unchanged: dict[str, str] = {}
    changed: dict[str, dict[str, str]] = {}
    removed: list[str] = []
    for path in _frozen_paths():
        original = _digest(_frozen_bytes(path))
        current_path = ROOT / path
        if not current_path.exists():
            removed.append(path)
            continue
        current = _digest(current_path.read_bytes())
        if current == original:
            unchanged[path] = current
        else:
            changed[path] = {"original_sha256": original, "amended_sha256": current}

    frozen = set(_frozen_paths())
    added: dict[str, str] = {}
    for path in sorted(ALLOWED_ADDED_PATHS | A2_ALLOWED_ADDED_PATHS | A2_1_ALLOWED_ADDED_PATHS):
        if path in frozen:
            continue
        candidate = ROOT / path
        if not candidate.exists():
            continue
        added[path] = "self" if path == SELF_EXCLUDED else _digest(candidate.read_bytes())

    amendment_changed = (
        ALLOWED_CHANGED_PATHS | A2_ALLOWED_CHANGED_PATHS | A2_1_ALLOWED_CHANGED_PATHS
    )
    allowed_changed = amendment_changed | ENGINEERING_CHANGED_PATHS
    unexpected_changed_raw = sorted(set(changed) - allowed_changed)
    unexpected_changed, rc4_2_delta = split_unexpected_changed(
        unexpected_changed_raw, frozen_commit=ORIGINAL_CONTENT_FREEZE, root=ROOT,
    )
    declared_missing = sorted(allowed_changed - set(changed))
    breach = bool(unexpected_changed or removed)
    return {
        "changed_by_amendment": {
            "A1": sorted(set(changed) & ALLOWED_CHANGED_PATHS),
            "A2": sorted(set(changed) & A2_ALLOWED_CHANGED_PATHS),
            "A2.1": sorted(set(changed) & A2_1_ALLOWED_CHANGED_PATHS),
        },
        "changed_by_engineering": {
            ENGINEERING_OWNER: sorted(set(changed) & ENGINEERING_CHANGED_PATHS),
        },
        "changed_by_rc4_2_delta": rc4_2_delta,
        "engineering_declared_paths": sorted(ENGINEERING_CHANGED_PATHS),
        "engineering_science_surface_violations": science_surface_violations(),
        "added_by_amendment": {
            "A1": sorted(path for path in added if path in ALLOWED_ADDED_PATHS),
            "A2": sorted(path for path in added if path in A2_ALLOWED_ADDED_PATHS),
            "A2.1": sorted(path for path in added if path in A2_1_ALLOWED_ADDED_PATHS),
        },
        "version": "paper-benchmark-amendment-a1-integrity-1.0.0",
        "amendment": "A1",
        "original_content_freeze": ORIGINAL_CONTENT_FREEZE,
        "original_freeze_designation": "BENCHMARK CONTENT FREEZE V1",
        "effective_content_freeze": "the Amendment A2.1 commit, tagged benchmark-content-freeze-a2-1",
        "amendments_applied": ["A1", "A2", "A2.1"],
        "frozen_path_count": len(frozen),
        "protected_unchanged_count": len(unchanged),
        "protected_unchanged_paths": sorted(unchanged),
        "protected_unchanged_sha256": dict(sorted(unchanged.items())),
        "changed_paths": sorted(changed),
        "changed_sha256": dict(sorted(changed.items())),
        "added_paths": sorted(added),
        "added_sha256": dict(sorted(added.items())),
        "removed_paths": sorted(removed),
        "unexpected_changed_paths": unexpected_changed,
        "declared_changed_paths_not_actually_changed": declared_missing,
        "held_out_rows_opened": False,
        "held_out_integrity_note": (
            "inputs/*.jsonl and truth/*.jsonl are untracked regenerable bytes absent from the tree; "
            "their SHA-256 values live in the unchanged paper_benchmark_hash_inventory.json"
        ),
        "integrity_verified": not breach,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "paper_benchmark_amendment_a1.json")
    arguments = parser.parse_args()
    manifest = build_manifest()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"original content freeze: {manifest['original_content_freeze']}")
    print(f"frozen tracked paths:    {manifest['frozen_path_count']}")
    print(f"protected unchanged:     {manifest['protected_unchanged_count']}")
    print(f"changed:                 {len(manifest['changed_paths'])}")
    print(f"added:                   {len(manifest['added_paths'])}")
    print(f"removed:                 {len(manifest['removed_paths'])}")
    print(
        "  of which engineering:  "
        f"{len(manifest['changed_by_engineering'][ENGINEERING_OWNER])}"
    )
    if not manifest["integrity_verified"]:
        print("INTEGRITY BREACH", file=sys.stderr)
        for path in manifest["unexpected_changed_paths"]:
            print(f"  unexpected change: {path}", file=sys.stderr)
        for path in manifest["removed_paths"]:
            print(f"  removed: {path}", file=sys.stderr)
        return 1
    print("integrity verified: every protected benchmark path is byte-identical to d94d2c9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
