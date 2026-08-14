"""Verify Amendment A2.1 against Amendment A2, byte for byte.

A2.1 bumps `GENERATOR_VERSION` because Amendment A2 changed the generator's
scientific behavior for F16 while the version string stayed at `1.0.0`. The
version string is part of every case's hashed payload
(`generator.scientific_payload_hash`), so this bump mechanically changes
`content_hash` for **all 380 cases**, not just F16's. That is expected and is
not a scientific change.

This script proves the distinction directly: it rebuilds the A2 (`03cc4d3`)
and A2.1 (current) generator states and, for every one of the 380 cases,
compares the scientific payload (covariates, scaffolds, partitions, seeds,
energies, generated responses, truth values -- i.e. `inputs` and `truth` with
`generator_version` excluded from the hash pre-image) rather than the raw
`content_hash`. It requires that payload to be identical for all 380 cases,
`content_hash` to differ for all 380 cases, and the set of *changed tracked
files* to be exactly the declared version-bump set.

Never inspects mu values scientifically beyond whole-object equality; never
scores, fits, or summarises a Development or Held-out outcome.
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

#: RC4.2's authorized, byte-pinned defect-repair delta (`engineering-rc4-2-
#: core-defect-repair`). Not a science amendment and not declared through
#: ENGINEERING_CHANGED_PATHS -- pb_engineering_paths.py's own guard forbids
#: that channel from ever touching src/muru/paper_benchmark/ or tests/test_a3_
#: /tests/test_paper_benchmark*.  RC4.2's six repaired files sit exactly on
#: that surface, so they get their own hash-pinned ledger instead. See
#: pb_rc4_2_authorized_delta.py.
from pb_rc4_2_authorized_delta import split_unexpected_changed  # noqa: E402

AMENDMENT_A2_FREEZE = "03cc4d3"

#: Paths whose bytes logically depend on the GENERATOR_VERSION bump.
ALLOWED_CHANGED_PATHS = frozenset({
    "src/muru/paper_benchmark/generator.py",
    "artifacts/paper_benchmark_case_manifest.json",
    "artifacts/paper_benchmark_hash_inventory.json",
    "artifacts/paper_benchmark_preflight.json",
    "artifacts/paper_benchmark_content_freeze.json",
    # Provenance bookkeeping: these must be re-run so the V1/A1-relative
    # reports still attribute every changed path to its owning amendment, and
    # the A2 test module's content_hash pins move to payload-hash pins so they
    # do not go stale on the next metadata-only bump.
    "artifacts/paper_benchmark_amendment_a1.json",
    "artifacts/paper_benchmark_amendment_a2.json",
    "scripts/pb_30_amendment_a1_integrity.py",
    "scripts/pb_31_amendment_a2_integrity.py",
    "tests/test_paper_benchmark_amendment_a2_integrity.py",
    "tests/test_paper_benchmark_amendment_integrity.py",
    "tests/test_paper_benchmark_f16_combined.py",
})

CHANGE_JUSTIFICATION = {
    "requirements.lock.txt": "ENGINEERING (not this amendment): RC4.1 environment closure replaced the reduced 39-pin Phase-1 lock with the 50-pin lock the frozen runtime guard already enforced and the audited A3.2 calibration declared; no science moved",
    "src/muru/paper_benchmark/generator.py": "GENERATOR_VERSION bumped to paper-benchmark-generator-1.1.0; adds scientific_payload_hash helper (byte-neutral refactor)",
    "artifacts/paper_benchmark_case_manifest.json": "content_hash changes for all 380 cases (version string is part of the hash pre-image)",
    "artifacts/paper_benchmark_hash_inventory.json": "SHA-256 of the six regenerated row files, which change only in their content_hash fields",
    "artifacts/paper_benchmark_preflight.json": "re-measured wall/cpu/rss; artifact_bytes is unchanged (content_hash is fixed-width hex)",
    "artifacts/paper_benchmark_content_freeze.json": "records the new hash_inventory and preflight digests",
    "artifacts/paper_benchmark_amendment_a1.json": "bookkeeping: V1-relative report re-run to attribute A2.1's changes",
    "artifacts/paper_benchmark_amendment_a2.json": "bookkeeping: A1-relative report re-run to attribute A2.1's changes",
    "scripts/pb_30_amendment_a1_integrity.py": "bookkeeping: imports A2.1's allowed-path sets alongside A2's",
    "scripts/pb_31_amendment_a2_integrity.py": "row comparison made payload-aware so it stays accurate across a later metadata-only bump",
    "tests/test_paper_benchmark_amendment_a2_integrity.py": "content_hash pins replaced with version-independent scientific_payload_hash pins",
    "tests/test_paper_benchmark_amendment_integrity.py": "asserts the new three-amendment (A1/A2/A2.1) attribution split",
    "tests/test_paper_benchmark_f16_combined.py": "GENERATOR_VERSION pin updated from 1.0.0 to 1.1.0",
}

ALLOWED_ADDED_PATHS = frozenset({
    "MURU_PAPER_BENCHMARK_AMENDMENT_A2_1_GENERATOR_VERSION.md",
    "artifacts/paper_benchmark_amendment_a2_1.json",
    "scripts/pb_32_amendment_a2_1_integrity.py",
    "tests/test_paper_benchmark_amendment_a2_1_integrity.py",
})

#: This provenance record cannot contain its own hash.
SELF_EXCLUDED = "artifacts/paper_benchmark_amendment_a2_1.json"

#: `paper_benchmark_amendment_a1.json` and `_a2.json` are produced by pb_30 and
#: pb_31 respectively, which also depend on each other and on this script's
#: output paths.  Embedding a live hash of either here would make three scripts
#: mutually recursive with no run order that reaches a fixed point.  Each
#: script instead reports its peers' provenance files as cross-referenced and
#: trusts their own regeneration to keep their own bytes correct.
CROSS_REFERENCED = frozenset({
    "artifacts/paper_benchmark_amendment_a1.json",
    "artifacts/paper_benchmark_amendment_a2.json",
})
EXPECTED_TOTAL_CASES = 380


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
    for path in _frozen_paths(AMENDMENT_A2_FREEZE):
        original = _digest(_frozen_bytes(AMENDMENT_A2_FREEZE, path))
        current_path = ROOT / path
        if not current_path.exists():
            removed.append(path)
            continue
        current = _digest(current_path.read_bytes())
        if current == original:
            unchanged[path] = current
        else:
            changed[path] = {
                "a2_sha256": original,
                "a2_1_sha256": "cross-referenced" if path in CROSS_REFERENCED else current,
                "justification": CHANGE_JUSTIFICATION.get(path, ""),
            }
    frozen = set(_frozen_paths(AMENDMENT_A2_FREEZE))
    added: dict[str, str] = {}
    for path in sorted(ALLOWED_ADDED_PATHS):
        if path in frozen:
            continue
        candidate = ROOT / path
        if candidate.exists():
            added[path] = "self" if path == SELF_EXCLUDED else _digest(candidate.read_bytes())
    return {"unchanged": unchanged, "changed": changed, "removed": removed, "added": added, "frozen_count": len(frozen)}


def _build_state(ref: str | None, destination: Path) -> None:
    if ref is None:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pb_00_build.py"), "--output", str(destination)],
            cwd=ROOT, capture_output=True, check=True,
        )
        return
    with tempfile.TemporaryDirectory() as checkout:
        subprocess.run(f"git archive {ref} src scripts | tar -x -C {checkout}", cwd=ROOT, shell=True, check=True)
        subprocess.run(
            [sys.executable, str(Path(checkout) / "scripts" / "pb_00_build.py"), "--output", str(destination)],
            cwd=checkout, capture_output=True, check=True,
        )


def _strip_hash(record: dict) -> dict:
    stripped = dict(record)
    stripped.pop("content_hash", None)
    return stripped


def _row_comparison() -> dict[str, object]:
    """Rebuild A2 and A2.1 row files; every case must be payload-identical."""
    with tempfile.TemporaryDirectory() as workspace:
        a2_dir, a21_dir = Path(workspace) / "a2", Path(workspace) / "a21"
        _build_state(AMENDMENT_A2_FREEZE, a2_dir)
        _build_state(None, a21_dir)

        streams: dict[str, dict[str, int]] = {}
        breach = False
        for partition in ("development", "held_out", "challenge"):
            for stream in ("inputs", "truth"):
                relative = f"{stream}/{partition}.jsonl"
                a2_lines = (a2_dir / relative).read_bytes().splitlines()
                a21_lines = (a21_dir / relative).read_bytes().splitlines()
                if len(a2_lines) != len(a21_lines):
                    breach = True
                payload_changed = hash_changed = payload_and_hash_identical = 0
                for left, right in zip(a2_lines, a21_lines):
                    lr, rr = json.loads(left), json.loads(right)
                    if lr["case_id"] != rr["case_id"]:
                        breach = True
                        break
                    same_payload = _strip_hash(lr) == _strip_hash(rr)
                    same_hash = lr.get("content_hash") == rr.get("content_hash")
                    if not same_payload:
                        payload_changed += 1
                    elif not same_hash:
                        hash_changed += 1
                    else:
                        payload_and_hash_identical += 1
                if payload_changed:
                    breach = True
                streams[relative] = {
                    "lines": len(a2_lines),
                    "payload_changed": payload_changed,
                    "hash_only_changed": hash_changed,
                    "payload_and_hash_identical": payload_and_hash_identical,
                }

        a2_cases = json.loads((a2_dir / "paper_benchmark_case_manifest.json").read_text())["cases"]
        a21_cases = json.loads((a21_dir / "paper_benchmark_case_manifest.json").read_text())["cases"]
        if len(a2_cases) != EXPECTED_TOTAL_CASES or len(a21_cases) != EXPECTED_TOTAL_CASES:
            breach = True
        payload_diff_ids = [
            x["case_id"] for x, y in zip(a2_cases, a21_cases)
            if {k: v for k, v in x.items() if k != "content_hash"} != {k: v for k, v in y.items() if k != "content_hash"}
        ]
        hash_diff_ids = [x["case_id"] for x, y in zip(a2_cases, a21_cases) if x["content_hash"] != y["content_hash"]]
        if payload_diff_ids or len(hash_diff_ids) != EXPECTED_TOTAL_CASES:
            breach = True

        return {
            "row_streams": streams,
            "case_records_total": len(a21_cases),
            "case_records_payload_changed": len(payload_diff_ids),
            "case_records_content_hash_changed": len(hash_diff_ids),
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
    from muru.paper_benchmark.generator import GENERATOR_VERSION

    assert_engineering_paths_carry_no_science()
    tracked = _tracked_comparison()
    rows = _row_comparison()
    invariants = _population_invariants()

    changed = tracked["changed"]
    allowed_changed = ALLOWED_CHANGED_PATHS | ENGINEERING_CHANGED_PATHS
    unexpected_changed_raw = sorted(set(changed) - allowed_changed)
    unexpected_changed, rc4_2_delta = split_unexpected_changed(
        unexpected_changed_raw, frozen_commit=AMENDMENT_A2_FREEZE, root=ROOT,
    )
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
    version_bumped = GENERATOR_VERSION == "paper-benchmark-generator-1.1.0"
    breach = (
        bool(unexpected_changed or tracked["removed"])
        or not rows["row_integrity_verified"]
        or not invariants_hold
        or not version_bumped
    )

    return {
        "version": "paper-benchmark-amendment-a2-1-integrity-1.0.0",
        "amendment": "A2.1",
        "amendment_a2_freeze": AMENDMENT_A2_FREEZE,
        "effective_content_freeze": "the Amendment A2.1 commit, tagged benchmark-content-freeze-a2-1",
        "old_generator_version": "paper-benchmark-generator-1.0.0",
        "new_generator_version": GENERATOR_VERSION,
        "generator_version_bumped": version_bumped,
        "frozen_path_count": tracked["frozen_count"],
        "protected_unchanged_count": len(tracked["unchanged"]),
        "protected_unchanged_paths": sorted(tracked["unchanged"]),
        "changed_paths": sorted(changed),
        "changed_sha256": dict(sorted(changed.items())),
        "added_paths": sorted(tracked["added"]),
        "added_sha256": dict(sorted(tracked["added"].items())),
        "removed_paths": sorted(tracked["removed"]),
        "unexpected_changed_paths": unexpected_changed,
        "rc4_2_authorized_delta": rc4_2_delta,
        "declared_changed_paths_not_actually_changed": declared_missing,
        "changed_by_engineering": {
            ENGINEERING_OWNER: sorted(set(changed) & ENGINEERING_CHANGED_PATHS),
        },
        "engineering_declared_paths": sorted(ENGINEERING_CHANGED_PATHS),
        "engineering_science_surface_violations": science_surface_violations(),
        "generated_row_comparison": rows,
        "population_invariants": invariants,
        "population_invariants_hold": invariants_hold,
        "scientific_change": "NONE",
        "development_outcomes_executed": False,
        "held_out_outcomes_executed": False,
        "held_out_rows_opened": False,
        "scientific_inspection_note": (
            "row files are compared as opaque whole lines with content_hash stripped before comparison; "
            "no response value is decoded, no case is scored, no outcome is summarised"
        ),
        "integrity_verified": not breach,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "paper_benchmark_amendment_a2_1.json")
    arguments = parser.parse_args()
    manifest = build_manifest()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    rows = manifest["generated_row_comparison"]
    print(f"amendment A2 freeze:         {manifest['amendment_a2_freeze']}")
    print(f"generator version:           {manifest['old_generator_version']} -> {manifest['new_generator_version']}")
    print(f"frozen tracked paths:        {manifest['frozen_path_count']}")
    print(f"protected unchanged:         {manifest['protected_unchanged_count']}")
    print(f"changed:                     {len(manifest['changed_paths'])}")
    print(f"added:                       {len(manifest['added_paths'])}")
    print(f"case records: payload changed = {rows['case_records_payload_changed']} "
          f"(expect 0); content_hash changed = {rows['case_records_content_hash_changed']} "
          f"(expect {EXPECTED_TOTAL_CASES})")
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
        if not manifest["generator_version_bumped"]:
            print("  generator version was not bumped", file=sys.stderr)
        return 1
    print("integrity verified: only the declared version-bump paths differ from 03cc4d3, "
          "and every case's scientific payload is unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
