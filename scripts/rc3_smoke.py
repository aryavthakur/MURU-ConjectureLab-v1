#!/usr/bin/env python3
"""Engineering RC3 smoke: prove the calibration runner works. NOT SCIENCE.

Every number this script produces is engineering evidence that the machinery
executes, persists, resumes and reproduces.  None of it is evidence about
MURU, about any null distribution, or about any threshold.

Quarantine, enforced not merely declared:

* seeds come from ``rc3_provenance.smoke_seed`` and live in a band that
  ``assert_seed_band_separation`` proves cannot collide with any calibration
  seed
* at most 2 worlds and at most 2 seeds, with reduced ``niterations``
* output goes only under ``artifacts/rc3_engineering_smoke/``
* every output file carries ``ENGINEERING_SMOKE_NOT_SCIENTIFIC``
* the record store is marked quarantined, and ``run_calibration`` - the only
  threshold-computing entry point - refuses a quarantined store and an
  engineering backend

Usage::

    python scripts/rc3_smoke.py            # run once
    python scripts/rc3_smoke.py --twice    # run twice, prove byte-identity
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_src = str(ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS  # noqa: E402
from muru.paper_benchmark.rc3_calibration_runner import (  # noqa: E402
    ENGINEERING_SMOKE_MARKER,
    FROZEN_SETTINGS_DIGEST,
    PySRBackend,
    SeedRecordStore,
    run_world,
    search_settings_digest,
)
from muru.paper_benchmark.rc3_calibration_worlds import build_world  # noqa: E402
from muru.paper_benchmark.rc3_provenance import (  # noqa: E402
    assert_seed_band_separation,
    build_provenance_manifest,
    smoke_seed,
)

SMOKE_ROOT = ROOT / "artifacts" / "rc3_engineering_smoke"

# Quarantine budget.  Deliberately tiny.
SMOKE_WORLDS = (
    ("target_permuted_across_compounds", 0),
    ("gaussian_targets_with_observed_variance", 0),
)
SMOKE_SEEDS_PER_WORLD = 2
SMOKE_NITERATIONS = 2


def _marked(payload: dict) -> dict:
    return {"marker": ENGINEERING_SMOKE_MARKER, **payload}


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_marked(payload), indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _CountingBackend:
    """Wraps the real backend and counts how many searches actually ran.

    Used to make the resume claim evidence rather than assertion.
    """

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0
        self.engineering_smoke = inner.engineering_smoke

    @property
    def effective_settings(self):
        return self.inner.effective_settings

    def search(self, world, seed):
        self.calls += 1
        return self.inner.search(world, seed)


def run_once(run_dir: Path, scratch: Path) -> tuple[dict, dict]:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    records_dir = run_dir / "seed_records"
    inner = PySRBackend(
        niterations_override=SMOKE_NITERATIONS,
        engineering_smoke=True,
        # Julia scratch lives OUTSIDE the quarantine tree: a crashed run
        # would otherwise leave unmarked files there, which the integrity
        # check would (correctly) flag as unmarked smoke output.
        work_dir=scratch,
    )
    backend = _CountingBackend(inner)
    settings_digest = search_settings_digest(inner.effective_settings)
    store = SeedRecordStore(
        records_dir, quarantined=True, settings_digest=settings_digest
    )

    summary: dict[str, dict] = {}
    all_seeds: list[tuple] = []
    for world_index, (construction, index) in enumerate(SMOKE_WORLDS):
        world = build_world(construction, index)
        seeds = [smoke_seed(world_index, k) for k in range(SMOKE_SEEDS_PER_WORLD)]
        results = run_world(world, backend, store, seeds=seeds)
        all_seeds.append((world, seeds))
        summary[world.world_id] = {
            "construction": construction,
            "seeds": seeds,
            "statuses": [r.status.value for r in results],
            "n_complexities_with_values": [
                0 if r.best_valid_r2_by_complexity is None
                else len(r.best_valid_r2_by_complexity)
                for r in results
            ],
        }

    calls_first_pass = backend.calls

    # Resume evidence: re-run the identical seeds against the same store.
    # Every seed is already recorded, so the backend must not be called once.
    for world, seeds in all_seeds:
        run_world(world, backend, store, seeds=seeds)
    calls_after_resume = backend.calls
    resume_reexecuted = calls_after_resume - calls_first_pass

    resume = {
        "seeds_executed_first_pass": calls_first_pass,
        "seeds_reexecuted_on_resume": resume_reexecuted,
        "resume_proven": resume_reexecuted == 0,
    }

    _write(
        run_dir / "smoke_summary.json",
        {
            "not_scientific": True,
            "statement": (
                "Engineering evidence only. These numbers are not evidence "
                "about MURU, about any null distribution, or about any "
                "threshold. Reduced niterations and a 2x2 budget mean they "
                "are not comparable to anything."
            ),
            "worlds": summary,
            "niterations_used": SMOKE_NITERATIONS,
            "niterations_frozen": SEARCH_SETTINGS["niterations"],
            "search_settings_digest": settings_digest,
            "frozen_settings_digest": FROZEN_SETTINGS_DIGEST,
            "settings_differ_from_frozen": settings_digest != FROZEN_SETTINGS_DIGEST,
            "resume": resume,
            "seed_bands": assert_seed_band_separation(),
        },
    )
    return summary, resume


def _tree_digest(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return digests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--twice", action="store_true", help="prove determinism")
    args = parser.parse_args()

    bands = assert_seed_band_separation()
    print(f"seed bands: {bands}")
    print(f"{ENGINEERING_SMOKE_MARKER}: nothing below is a scientific result")

    manifest = build_provenance_manifest(strict=True, start_julia=True)
    _write(SMOKE_ROOT / "provenance.json", manifest.to_payload())

    scratch = Path(tempfile.mkdtemp(prefix="rc3_smoke_"))
    try:
        _, resume_a = run_once(SMOKE_ROOT / "run_a", scratch)
        digest_a = _tree_digest(SMOKE_ROOT / "run_a" / "seed_records")
        print(f"run_a seed-record files: {len(digest_a)}")
        print(f"resume: re-executed {resume_a['seeds_reexecuted_on_resume']} "
              f"of {resume_a['seeds_executed_first_pass']} completed seeds")
        if not resume_a["resume_proven"]:
            print("RESUME FAILURE")
            return 1

        result = {
            "not_scientific": True,
            "run_a": digest_a,
            "resume": resume_a,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }

        if args.twice:
            run_once(SMOKE_ROOT / "run_b", scratch)
            digest_b = _tree_digest(SMOKE_ROOT / "run_b" / "seed_records")
            identical = digest_a == digest_b
            result["run_b"] = digest_b
            result["byte_identical"] = identical
            print(f"run_b seed-record files: {len(digest_b)}")
            print(f"BYTE-IDENTICAL ACROSS RUNS: {identical}")
            if not identical:
                _write(SMOKE_ROOT / "determinism.json", result)
                print("DETERMINISM FAILURE")
                return 1

        _write(SMOKE_ROOT / "determinism.json", result)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print("SMOKE OK - engineering only, not scientific evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
