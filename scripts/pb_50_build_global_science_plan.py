"""Build and verify the RC5 global pre-execution science plan (A3.5 section 8.4, layer 1).

This writes the **partition-agnostic** object that binds the scientific
execution before any partition runs.  It is deliberately incapable of executing
anything: it opens no case, reads no truth, and takes no partition argument.

Run:  python scripts/pb_50_build_global_science_plan.py

The plan is written once and never amended.  Re-running against an existing
plan re-verifies it and reports whether it is byte-reproducible, rather than
overwriting it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.rc5_manifest import (  # noqa: E402
    build_global_science_plan,
    canonical_manifest_json,
    manifest_digest,
    resolve_tag_commit,
)

DEFAULT_OUTPUT = ROOT / "artifacts" / "muru_rc5_global_science_plan.json"

ENGINEERING_PARENT_TAG = "engineering-rc4-2-1-integrity-closure"
A3_5_TAG = "benchmark-content-freeze-a3-5"

THRESHOLD_TABLE = ROOT / "calibration" / "a3_2" / "threshold_table.json"

#: The RC5 implementation surface whose bytes define this plan's code identity.
#: Recorded per module rather than as one tree hash, so a reviewer can see
#: exactly which component moved.
CODE_PROVENANCE_PATHS = (
    "src/muru/paper_benchmark/identity_contract.py",
    "src/muru/paper_benchmark/seed_band_registry.py",
    "src/muru/paper_benchmark/structural_acceptance.py",
    "src/muru/paper_benchmark/rc3_acceptance.py",
    "src/muru/paper_benchmark/rc3_ceiling.py",
    "src/muru/paper_benchmark/rc3_record.py",
    "src/muru/paper_benchmark/rc5_adapter.py",
    "src/muru/paper_benchmark/rc5_adequacy.py",
    "src/muru/paper_benchmark/rc5_authorization.py",
    "src/muru/paper_benchmark/rc5_case_scoring.py",
    "src/muru/paper_benchmark/rc5_estimate.py",
    "src/muru/paper_benchmark/rc5_falsify.py",
    "src/muru/paper_benchmark/rc5_g1_bridge.py",
    "src/muru/paper_benchmark/rc5_manifest.py",
    "src/muru/paper_benchmark/rc5_runner.py",
    "src/muru/paper_benchmark/rc5_seeds.py",
    "src/muru/paper_benchmark/rc5_selection.py",
    "src/muru/paper_benchmark/rc5_store.py",
)


def _tag_object(tag: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", tag], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _null_threshold() -> dict[int, float]:
    payload = json.loads(THRESHOLD_TABLE.read_text(encoding="utf-8"))
    if payload.get("validity") != "VALID":
        raise RuntimeError(
            f"threshold table validity is {payload.get('validity')!r}, not VALID; "
            f"refusing to bind a plan to an invalid calibration"
        )
    return {int(c): float(v) for c, v in payload["thresholds"].items()}


def _calibration_manifest_digest() -> str:
    """The A3.2 calibration's own canonically-computed manifest digest.

    Read from the threshold table rather than recomputed, so the plan cites the
    value the calibration itself declared.  A3.5 section 8.4's digest-convention
    warning is live here: this is the CANONICAL digest, which differs from the
    raw-byte digest of the same file.
    """
    payload = json.loads(THRESHOLD_TABLE.read_text(encoding="utf-8"))
    return str(payload["execution_manifest_sha256"])


def build() -> dict:
    return build_global_science_plan(
        engineering_parent_commit=resolve_tag_commit(ENGINEERING_PARENT_TAG, ROOT),
        a3_5_tag=A3_5_TAG,
        a3_5_tag_object=_tag_object(A3_5_TAG),
        a3_5_commit=resolve_tag_commit(A3_5_TAG, ROOT),
        null_threshold=_null_threshold(),
        calibration_manifest_digest=_calibration_manifest_digest(),
        code_provenance={
            path: _sha256(ROOT / path) for path in CODE_PROVENANCE_PATHS
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    path = arguments.output

    plan = build()
    body = canonical_manifest_json(plan).encode("utf-8")

    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        reproducible = existing == json.loads(canonical_manifest_json(plan))
        print(f"plan already exists: {path}")
        print(f"  recorded digest:   {existing.get('digest')}")
        print(f"  recomputed digest: {plan['digest']}")
        print(f"  byte-reproducible: {reproducible}")
        print(f"  verified digest:   {manifest_digest(existing)}")
        if not reproducible:
            print(
                "PLAN NOT REPRODUCIBLE: the written plan and a fresh build differ. "
                "A written pre-execution plan is never amended; investigate the "
                "drift rather than overwriting.",
                file=sys.stderr,
            )
            return 1
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)

    # Verify what was actually written, not what we intended to write.
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert manifest_digest(reloaded) == plan["digest"]
    assert reloaded == json.loads(canonical_manifest_json(plan))

    print(f"global pre-execution science plan written: {path}")
    print(f"  schema_version:            {plan['schema_version']}")
    print(f"  partition_agnostic:        {plan['partition_agnostic']}")
    print(f"  engineering parent:        {plan['engineering_parent_commit']}")
    print(f"  A3.5 tag:                  {plan['a3_5_science_freeze']['tag']}")
    print(f"  A3.5 tag object:           {plan['a3_5_science_freeze']['tag_object']}")
    print(f"  A3.5 commit:               {plan['a3_5_science_freeze']['commit']}")
    print(f"  record schema:             {plan['record_schema_version']}")
    print(f"  threshold table digest:    {plan['threshold_table_digest']}")
    print(f"  calibration manifest:      {plan['calibration_manifest_digest']}")
    print(f"  grammar identity digest:   {plan['grammar_identity_digest']}")
    print(f"  search settings digest:    {plan['search_settings_digest']}")
    print(f"  cases:                     {sum(p['case_count'] for p in plan['case_inventory'].values())}")
    print(f"  derived search seeds:      {sum(len(s) for s in plan['case_search_seeds'].values())}")
    print(f"  PLAN DIGEST (canonical):   {plan['digest']}")
    print(f"  raw-byte digest (NOT the convention): {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
