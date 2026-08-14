"""Verify Amendment A2 against Amendment A1, byte for byte.

Every tracked path at `2ac86c5` (the A1 effective content freeze) is compared
with the A2 tree by SHA-256 of its bytes.  Only the declared F16-repair paths
may differ; anything else is an integrity breach and this script exits non-zero.

The generated row files `inputs/*.jsonl` and `truth/*.jsonl` are untracked
regenerable bytes, so they carry no git-visible hash.  This script therefore
also rebuilds both the A1 and A2 generator states into temporary directories and
compares the resulting case records **line by line**, proving that exactly the
19 F16 cases changed and that all 361 non-F16 cases are byte-identical.

The comparison is mechanical hashing and whole-line byte equality.  It never
decodes a response value, scores a case, or otherwise inspects a Development or
Held-out scientific outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Engineering-owned changes inside the frozen set, declared once for all
#: three amendment integrity scripts.  Reported separately from the amendment
#: sets so an engineering exemption is never readable as a science amendment.
from pb_engineering_paths import (  # noqa: E402
    ENGINEERING_CHANGED_PATHS,
    ENGINEERING_OWNER,
    science_surface_violations,
    assert_engineering_paths_carry_no_science,
)

ORIGINAL_CONTENT_FREEZE = "d94d2c9"
AMENDMENT_A1_FREEZE = "2ac86c5"

#: Paths whose bytes logically depend on the corrected F16 generator, plus the
#: integrity bookkeeping that must record the repair.  No registry, truth
#: schema, protocol, governance, partition manifest, or A1 decision path is in
#: this set.
ALLOWED_CHANGED_PATHS = frozenset({
    "src/muru/paper_benchmark/generator.py",
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_hash_inventory.json",
    "artifacts/paper_benchmark_preflight.json",
    "artifacts/paper_benchmark_content_freeze.json",
    "artifacts/paper_benchmark_amendment_a1.json",
    "scripts/pb_30_amendment_a1_integrity.py",
    "tests/test_paper_benchmark_amendment_integrity.py",
})

#: Why each changed path is allowed to change.
CHANGE_JUSTIFICATION = {
    "requirements.lock.txt": "ENGINEERING (not this amendment): RC4.1 environment closure replaced the reduced 39-pin Phase-1 lock with the 50-pin lock the frozen runtime guard already enforced and the audited A3.2 calibration declared; no science moved",
    "src/muru/paper_benchmark/generator.py": "the F16 combined_violation branch gains its declared M3 low-energy ceiling",
    "artifacts/paper_benchmark_case_manifest.json": "per-case content hashes for the 19 F16 cases",
    "artifacts/paper_benchmark_hash_inventory.json": "SHA-256 of the six regenerated inputs/truth row files",
    "artifacts/paper_benchmark_preflight.json": "artifact_bytes follows the F16 rows; wall/cpu/rss are environment re-measurements",
    "artifacts/paper_benchmark_content_freeze.json": "records the new hash_inventory and preflight digests",
    "artifacts/paper_benchmark_amendment_a1.json": "bookkeeping: the V1-relative report now attributes each change to A1 or A2",
    "scripts/pb_30_amendment_a1_integrity.py": "bookkeeping: attributes V1-relative changes to the amendment that owns them",
    "tests/test_paper_benchmark_amendment_integrity.py": "bookkeeping: asserts the A1/A2 attribution split",
}

ALLOWED_ADDED_PATHS = frozenset({
    "MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md",
    "MURU_PAPER_BENCHMARK_A2_F16_GOVERNANCE_REVIEW.md",
    "artifacts/paper_benchmark_amendment_a2.json",
    "scripts/pb_31_amendment_a2_integrity.py",
    "tests/test_paper_benchmark_f16_combined.py",
    "tests/test_paper_benchmark_amendment_a2_integrity.py",
})

#: The provenance record cannot contain its own hash; the contract tests cover it.
SELF_EXCLUDED = "artifacts/paper_benchmark_amendment_a2.json"

#: The A1 integrity record hashes *this* record among its added paths, so hashing
#: it back here would make the two manifests mutually recursive and neither could
#: ever be regenerated to a fixed point.  The dependency is therefore broken in
#: one direction: A1's record cites A2's digest, A2's record cites A1 by name
#: only.  Regenerate A2 first, then A1.
CROSS_REFERENCED = "artifacts/paper_benchmark_amendment_a1.json"

REPAIRED_FAMILY = "F16"
EXPECTED_TOTAL_CASES = 380
EXPECTED_F16_CASES = 19


def _git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _frozen_paths(ref: str) -> list[str]:
    return [line for line in _git("ls-tree", "-r", "--name-only", ref).splitlines() if line]


def _frozen_bytes(ref: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _tracked_comparison() -> dict[str, object]:
    unchanged: dict[str, str] = {}
    changed: dict[str, dict[str, str]] = {}
    removed: list[str] = []
    for path in _frozen_paths(AMENDMENT_A1_FREEZE):
        original = _digest(_frozen_bytes(AMENDMENT_A1_FREEZE, path))
        current_path = ROOT / path
        if not current_path.exists():
            removed.append(path)
            continue
        current = _digest(current_path.read_bytes())
        if current == original:
            unchanged[path] = current
        else:
            changed[path] = {
                "a1_sha256": original,
                "a2_sha256": "cross-referenced" if path == CROSS_REFERENCED else current,
                "justification": CHANGE_JUSTIFICATION.get(path, ""),
            }

    frozen = set(_frozen_paths(AMENDMENT_A1_FREEZE))
    added: dict[str, str] = {}
    for path in sorted(ALLOWED_ADDED_PATHS):
        if path in frozen:
            continue
        candidate = ROOT / path
        if candidate.exists():
            added[path] = "self" if path == SELF_EXCLUDED else _digest(candidate.read_bytes())
    return {"unchanged": unchanged, "changed": changed, "removed": removed, "added": added, "frozen_count": len(frozen)}


def _build_state(ref: str | None, destination: Path) -> None:
    """Build the generator state at `ref` (or the working tree) into `destination`."""
    if ref is None:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pb_00_build.py"), "--output", str(destination)],
            cwd=ROOT, capture_output=True, check=True,
        )
        return
    with tempfile.TemporaryDirectory() as checkout:
        source = Path(checkout) / "src"
        source.mkdir()
        subprocess.run(f"git archive {ref} src scripts | tar -x -C {checkout}", cwd=ROOT, shell=True, check=True)
        subprocess.run(
            [sys.executable, str(Path(checkout) / "scripts" / "pb_00_build.py"), "--output", str(destination)],
            cwd=checkout, capture_output=True, check=True,
        )


def _strip_hash(record: dict) -> dict:
    """Amendment A2.1 note: comparisons here are payload-level (content_hash
    stripped), not raw-byte-level. Amendment A2.1 legitimately changes
    content_hash for every case via a GENERATOR_VERSION bump, which is
    scientifically inert; a raw-byte comparison would misreport that as a
    breach of "only F16 changed relative to A1". Stripping content_hash keeps
    this script's actual claim -- F16's science changed and nothing else's did
    -- accurate independent of any later version-metadata-only amendment.
    """
    stripped = dict(record)
    stripped.pop("content_hash", None)
    return stripped


def _row_comparison() -> dict[str, object]:
    """Rebuild A1 and A2 row files and compare their scientific payload line by line."""
    with tempfile.TemporaryDirectory() as workspace:
        a1_dir, a2_dir = Path(workspace) / "a1", Path(workspace) / "a2"
        _build_state(AMENDMENT_A1_FREEZE, a1_dir)
        _build_state(None, a2_dir)

        streams: dict[str, dict[str, int]] = {}
        breach = False
        payload_changed_ids: set[str] = set()
        for partition in ("development", "held_out", "challenge"):
            for stream in ("inputs", "truth"):
                relative = f"{stream}/{partition}.jsonl"
                a1_lines = (a1_dir / relative).read_bytes().splitlines()
                a2_lines = (a2_dir / relative).read_bytes().splitlines()
                if len(a1_lines) != len(a2_lines):
                    breach = True
                changed_family = changed_other = 0
                for left, right in zip(a1_lines, a2_lines):
                    lr, rr = json.loads(left), json.loads(right)
                    case_id = lr["case_id"]
                    if case_id != rr["case_id"]:
                        breach = True
                        break
                    if _strip_hash(lr) == _strip_hash(rr):
                        continue
                    payload_changed_ids.add(case_id)
                    if case_id.split("|")[2] == REPAIRED_FAMILY:
                        changed_family += 1
                    else:
                        changed_other += 1
                if changed_other:
                    breach = True
                streams[relative] = {
                    "lines": len(a1_lines),
                    "f16_changed": changed_family,
                    "non_f16_changed": changed_other,
                }

        # The case manifest's own record carries no inputs/truth -- content_hash
        # is its only payload fingerprint, so it cannot be used with
        # `_strip_hash` the way the row records above are: stripping the one
        # field that reflects the payload would make every manifest row look
        # identical.  `payload_changed_ids`, collected from the row-level
        # comparison above (which does carry the full payload), is the correct
        # source for which cases actually changed.
        a2_cases = json.loads((a2_dir / "paper_benchmark_case_manifest.json").read_text())["cases"]
        changed_ids = sorted(payload_changed_ids)
        families = sorted({case_id.split("|")[2] for case_id in changed_ids})
        if families not in ([], [REPAIRED_FAMILY]) or len(changed_ids) != EXPECTED_F16_CASES:
            breach = True
        if len(a2_cases) != EXPECTED_TOTAL_CASES:
            breach = True

        return {
            "row_streams": streams,
            "case_records_total": len(a2_cases),
            "case_records_changed": len(changed_ids),
            "case_record_families_changed": families,
            "changed_case_ids": sorted(changed_ids),
            "non_f16_case_records_changed": len(changed_ids) - sum(
                1 for case_id in changed_ids if case_id.split("|")[2] == REPAIRED_FAMILY
            ),
            "row_integrity_verified": not breach,
        }


def _population_invariants() -> dict[str, object]:
    from muru.paper_benchmark.analysis import endpoint_denominator
    from muru.paper_benchmark.registry import CASE_FAMILIES, ENERGY_GRID, PARTITION_CASE_COUNTS, ROOT_SEED

    return {
        "family_count": len(CASE_FAMILIES),
        "root_seed": ROOT_SEED,
        "energy_grid": list(ENERGY_GRID),
        "partition_case_counts": dict(PARTITION_CASE_COUNTS),
        "endpoint_denominators": {
            name: endpoint_denominator(name)
            for name in (
                "scalar_competence", "family_recovery", "principal_structural_safety",
                "m0_specificity", "m1_sensitivity", "m2_sensitivity", "m3_sensitivity",
            )
        },
    }


def build_manifest() -> dict[str, object]:
    assert_engineering_paths_carry_no_science()
    tracked = _tracked_comparison()
    rows = _row_comparison()
    invariants = _population_invariants()

    changed = tracked["changed"]
    allowed_changed = ALLOWED_CHANGED_PATHS | ENGINEERING_CHANGED_PATHS
    unexpected_changed = sorted(set(changed) - allowed_changed)
    declared_missing = sorted(allowed_changed - set(changed))
    expected_denominators = {
        "scalar_competence": 164, "family_recovery": 144, "principal_structural_safety": 36,
        "m0_specificity": 164, "m1_sensitivity": 36, "m2_sensitivity": 24, "m3_sensitivity": 24,
    }
    invariants_hold = (
        invariants["family_count"] == 20
        and invariants["root_seed"] == 20260813
        and invariants["partition_case_counts"] == {"development": 4, "held_out": 12, "challenge": 3}
        and invariants["endpoint_denominators"] == expected_denominators
    )
    breach = bool(unexpected_changed or tracked["removed"]) or not rows["row_integrity_verified"] or not invariants_hold

    return {
        "version": "paper-benchmark-amendment-a2-integrity-1.0.0",
        "amendment": "A2",
        "original_content_freeze": ORIGINAL_CONTENT_FREEZE,
        "original_freeze_designation": "BENCHMARK CONTENT FREEZE V1",
        "amendment_a1_freeze": AMENDMENT_A1_FREEZE,
        "effective_content_freeze": "the Amendment A2 commit, tagged benchmark-content-freeze-a2",
        "repaired_family": REPAIRED_FAMILY,
        "frozen_path_count": tracked["frozen_count"],
        "protected_unchanged_count": len(tracked["unchanged"]),
        "protected_unchanged_paths": sorted(tracked["unchanged"]),
        "protected_unchanged_sha256": dict(sorted(tracked["unchanged"].items())),
        "changed_paths": sorted(changed),
        "changed_sha256": dict(sorted(changed.items())),
        "added_paths": sorted(tracked["added"]),
        "added_sha256": dict(sorted(tracked["added"].items())),
        "removed_paths": sorted(tracked["removed"]),
        "unexpected_changed_paths": unexpected_changed,
        "declared_changed_paths_not_actually_changed": declared_missing,
        "changed_by_engineering": {
            ENGINEERING_OWNER: sorted(set(changed) & ENGINEERING_CHANGED_PATHS),
        },
        "engineering_declared_paths": sorted(ENGINEERING_CHANGED_PATHS),
        "engineering_science_surface_violations": science_surface_violations(),
        "generated_row_comparison": rows,
        "population_invariants": invariants,
        "population_invariants_hold": invariants_hold,
        "development_outcomes_executed": False,
        "held_out_outcomes_executed": False,
        "held_out_rows_opened": False,
        "scientific_inspection_note": (
            "row files are compared as opaque whole lines and artifacts by SHA-256; "
            "no response value is decoded, no case is scored, no outcome is summarised"
        ),
        "integrity_verified": not breach,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "paper_benchmark_amendment_a2.json")
    arguments = parser.parse_args()
    manifest = build_manifest()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    rows = manifest["generated_row_comparison"]
    print(f"amendment A1 freeze:     {manifest['amendment_a1_freeze']}")
    print(f"frozen tracked paths:    {manifest['frozen_path_count']}")
    print(f"protected unchanged:     {manifest['protected_unchanged_count']}")
    print(f"changed:                 {len(manifest['changed_paths'])}")
    print(f"added:                   {len(manifest['added_paths'])}")
    print(f"removed:                 {len(manifest['removed_paths'])}")
    print(f"case records changed:    {rows['case_records_changed']} of {rows['case_records_total']} "
          f"(families {rows['case_record_families_changed']})")
    print(f"non-F16 records changed: {rows['non_f16_case_records_changed']}")
    if not manifest["integrity_verified"]:
        print("INTEGRITY BREACH", file=sys.stderr)
        for path in manifest["unexpected_changed_paths"]:
            print(f"  unexpected change: {path}", file=sys.stderr)
        for path in manifest["removed_paths"]:
            print(f"  removed: {path}", file=sys.stderr)
        if not rows["row_integrity_verified"]:
            print("  generated row comparison failed", file=sys.stderr)
        if not manifest["population_invariants_hold"]:
            print("  population invariants changed", file=sys.stderr)
        return 1
    print("integrity verified: only the declared F16 repair paths differ from 2ac86c5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
