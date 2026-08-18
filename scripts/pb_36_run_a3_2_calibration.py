#!/usr/bin/env python3
"""Execute and freeze the A3.2 structural-null calibration.

ONE authorized scientific action: run the prospectively specified A3.2 null
calibration exactly once against the frozen RC3.1 implementation.

Phases
------
1. Build and hash the execution manifest BEFORE the first seed.  The manifest
   is deterministic: no timestamps, no paths outside the repository, no
   wall-clock. Timestamps live in a separate provenance sidecar.
2. Execute the calibration through the canonical frozen runner, at the FULL
   frozen search settings, writing per-seed records incrementally.
3. Aggregate through the frozen contract functions, unchanged.
4. Decide validity by the frozen rules only.
5. Write the evidence, valid or not.

Resume
------
Re-invoking the script resumes.  Records are adopted only when world id,
seed, world-construction digest and search-settings digest all match; every
other record is refused.  Resume never re-executes a completed seed and never
re-executes a recorded execution failure.

Evidence location
-----------------
``calibration/a3_2/`` rather than ``artifacts/``.  ``artifacts/*`` is ignored
wholesale by ``.gitignore``, and the negation that would be needed there
changes ``.gitignore``, which the frozen amendment-integrity test treats as a
changed path.  ``calibration/`` is untracked by any ignore rule, so the
evidence is committable without touching a frozen contract.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_src = str(ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from muru.paper_benchmark.calibration_contract import (  # noqa: E402
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
    MAX_COMPLEXITY,
    MIN_VALID_WORLDS,
    N_CALIBRATION_WORLDS,
    N_SEEDS_PER_WORLD,
    QUANTILE_LEVEL,
    SEARCH_SETTINGS,
    CalibrationValidity,
    SeedStatus,
    all_world_ids,
    derive_calibration_seeds,
)
from muru.paper_benchmark.rc3_calibration_runner import (  # noqa: E402
    FROZEN_SETTINGS_DIGEST,
    PySRBackend,
    SeedRecordStore,
    run_calibration,
)
from muru.paper_benchmark.rc3_calibration_worlds import (  # noqa: E402
    BASE_TARGET_ALGORITHM,
    CALIBRATION_SCAFFOLD_COUNTS,
    EXPECTED_SPLIT_COUNTS,
    SPLIT_ALGORITHM,
    build_world,
)
from muru.paper_benchmark.rc3_provenance import (  # noqa: E402
    RC2_LOCK_COMMIT,
    RC2_LOCK_SHA256,
    a3_2_world_construction,
    assert_seed_band_separation,
    build_provenance_manifest,
    verify_dependencies,
)

OUT = ROOT / "calibration" / "a3_2"
RECORDS = OUT / "seed_records"

CALIBRATION_IDENTITY = "muru-a3.2-structural-null-calibration-1.0.0"
A3_2_SCIENCE_COMMIT = "1194fcbc9d9edcb14583eedfdcb0e395028dd93a"
A3_2_SCIENCE_TAG = "benchmark-content-freeze-a3-2"
RC3_1_COMMIT = "07c64c862cb32a306f5081582dacf73e09211c0a"
RC3_1_TAG = "engineering-rc3-1-a3-2"


def canonical(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# -----------------------------------------------------------------------
# Phase 1: execution manifest
# -----------------------------------------------------------------------

def build_execution_manifest() -> dict:
    """Everything that fixes what this run IS, before it produces anything."""
    verify_dependencies()
    provenance = build_provenance_manifest(strict=True).to_payload()

    world_ids = all_world_ids()
    seeds = {wid: derive_calibration_seeds(wid) for wid in world_ids}

    a3_2 = json.loads(
        (ROOT / "artifacts" / "paper_benchmark_amendment_a3_2.json").read_text()
    )

    return {
        "calibration_identity": CALIBRATION_IDENTITY,
        "a3_2_science_commit": A3_2_SCIENCE_COMMIT,
        "a3_2_science_tag": A3_2_SCIENCE_TAG,
        "rc3_1_engineering_commit": RC3_1_COMMIT,
        "rc3_1_engineering_tag": RC3_1_TAG,
        "dependency_lock_commit": RC2_LOCK_COMMIT,
        "dependency_lock_sha256": RC2_LOCK_SHA256,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_packages": provenance["python_packages"],
        "julia": provenance["julia"],
        "world_construction": a3_2_world_construction(),
        "base_target_algorithm": BASE_TARGET_ALGORITHM,
        "split_algorithm": SPLIT_ALGORITHM,
        "search_settings": {k: SEARCH_SETTINGS[k] for k in sorted(SEARCH_SETTINGS)},
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
        "seed_policy": {
            "derivation": "calibration_contract.derive_calibration_seeds",
            "namespace_form": "PB|NCAL|<construction>|r<index:03d>",
            "seeds_per_world": N_SEEDS_PER_WORLD,
            "bands": assert_seed_band_separation(),
        },
        "world_ids": world_ids,
        "seed_ids": {wid: seeds[wid] for wid in world_ids},
        "expected_world_count": N_CALIBRATION_WORLDS,
        "expected_seed_execution_count": N_CALIBRATION_WORLDS * N_SEEDS_PER_WORLD,
        "null_family_allocation": dict(CONSTRUCTION_ALLOCATION),
        "excluded_constructions": sorted(EXCLUDED_CONSTRUCTIONS),
        "scaffold_counts": dict(CALIBRATION_SCAFFOLD_COUNTS),
        "compound_counts": dict(EXPECTED_SPLIT_COUNTS),
        "threshold_aggregation_identity": (
            "S(w,c)=max over seeds of prefix-max validation R2; "
            "Q95 across worlds per complexity; np.maximum.accumulate over c"
        ),
        "quantile_definition": {
            "level": QUANTILE_LEVEL, "method": "linear",
            "implementation": "numpy.quantile",
        },
        "bootstrap_definition": {
            "resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED,
            "level": "world", "use": "uncertainty reporting only",
        },
        "failure_semantics": {
            "statuses": [s.value for s in SeedStatus],
            "status_from_execution_outcome_not_finiteness": True,
            "any_execution_failure_forces_world_row_to": 1.0,
            "completed_no_candidate_contributes": "-inf",
            "no_selective_retry": True,
            "operator_abort_propagates_unrecorded": True,
        },
        "resume_semantics": {
            "adopt_requires_match_on": [
                "world_id", "seed", "world_construction_digest",
                "search_settings_digest",
            ],
            "rejects": [
                "foreign world", "stale/pre-A3.2 world construction",
                "engineering smoke marker", "duplicate seed",
                "malformed record", "settings mismatch",
            ],
        },
        "validity_rule": {
            "min_clean_worlds": MIN_VALID_WORLDS,
            "of": N_CALIBRATION_WORLDS,
            "invalid_threshold_table_refused": True,
        },
        "max_complexity": MAX_COMPLEXITY,
        "output_locations": {
            "seed_records": "calibration/a3_2/seed_records/",
            "execution_manifest": "calibration/a3_2/execution_manifest.json",
            "result": "calibration/a3_2/calibration_result.json",
            "threshold_table": "calibration/a3_2/threshold_table.json",
        },
        "protected_path_digest": a3_2["protected_path_digest"],
        "protected_sha256": a3_2["protected_sha256"],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "execution_manifest.json"

    manifest = build_execution_manifest()
    text = canonical(manifest) + "\n"
    digest = sha256_text(canonical(manifest))

    if manifest_path.exists():
        existing = manifest_path.read_text()
        if existing != text:
            print("EXECUTION MANIFEST CHANGED SINCE THE RUN BEGAN - REFUSING")
            print(f"  recorded digest: {sha256_text(canonical(json.loads(existing)))}")
            print(f"  current  digest: {digest}")
            return 2
        print(f"execution manifest unchanged (sha256 {digest})")
    else:
        manifest_path.write_text(text)
        print(f"execution manifest frozen: sha256 {digest}")

    backend = PySRBackend()  # FULL frozen settings; no override anywhere
    if backend.niterations != SEARCH_SETTINGS["niterations"]:
        print("BACKEND IS NOT AT FROZEN SETTINGS - REFUSING")
        return 2
    store = SeedRecordStore(RECORDS)

    # Pre-count what already exists, so resume adoption can be reported.
    adopted = 0
    for wid in all_world_ids():
        world = build_world(*_spec_for(wid))
        try:
            adopted += len(store.load(wid, world_digest=world.construction_digest()))
        except RuntimeError as exc:
            print(f"RESUME REFUSED for {wid}: {exc}")
            return 2

    print(f"resume: {adopted} valid seed records already present")
    print(f"executing at niterations={backend.niterations}, "
          f"{N_CALIBRATION_WORLDS} worlds x {N_SEEDS_PER_WORLD} seeds")

    started = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    done = [0]

    def on_seed(world_id, result):
        done[0] += 1
        if done[0] % 10 == 0:
            rate = (time.time() - t0) / done[0]
            print(f"  {done[0]} seeds executed this session "
                  f"({rate:.1f}s/seed)", flush=True)

    result = run_calibration(backend, store, on_seed=on_seed)
    elapsed = time.time() - t0
    finished = datetime.now(timezone.utc).isoformat()

    _write_results(manifest, digest, result, store, started, finished, elapsed, adopted)
    print(f"\nVALIDITY: {result.validity.value}")
    print(f"clean worlds: {result.clean_worlds}/{N_CALIBRATION_WORLDS}, "
          f"failed: {result.failed_worlds}")
    return 0


def _spec_for(world_id: str) -> tuple[str, int]:
    _, _, construction, replicate = world_id.split("|")
    return construction, int(replicate[1:])


def _json_float(value: float):
    import math
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def _write_results(manifest, manifest_digest, result, store, started,
                   finished, elapsed, adopted_at_start) -> None:
    from collections import Counter

    per_world = {}
    statuses = Counter()
    failure_types = Counter()
    for wid in all_world_ids():
        world = build_world(*_spec_for(wid))
        records = store.load(wid, world_digest=world.construction_digest())
        world_statuses = Counter(r.status.value for r in records.values())
        statuses.update(world_statuses)
        for r in records.values():
            if r.status == SeedStatus.EXECUTION_FAILURE:
                failure_types[r.error_message.split(":", 1)[0].strip()] += 1
        per_world[wid] = {
            "construction": world.construction,
            "world_construction_digest": world.construction_digest(),
            "seed_count": len(records),
            "statuses": dict(sorted(world_statuses.items())),
            "has_execution_failure": bool(
                world_statuses.get(SeedStatus.EXECUTION_FAILURE.value, 0)
            ),
            "statistic": {
                str(c): _json_float(v)
                for c, v in sorted(result.world_statistics.get(wid, {}).items())
            },
        }

    payload = {
        "calibration_identity": CALIBRATION_IDENTITY,
        "execution_manifest_sha256": manifest_digest,
        "a3_2_science_commit": A3_2_SCIENCE_COMMIT,
        "rc3_1_engineering_commit": RC3_1_COMMIT,
        "validity": result.validity.value,
        "clean_worlds": result.clean_worlds,
        "failed_worlds": result.failed_worlds,
        "world_count": len(per_world),
        "seed_status_totals": dict(sorted(statuses.items())),
        "execution_failure_types": dict(sorted(failure_types.items())),
        "resume_records_adopted_at_start": adopted_at_start,
        "null_family_allocation": dict(CONSTRUCTION_ALLOCATION),
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
        "world_construction": a3_2_world_construction(),
        "per_world": per_world,
        "threshold_table": (
            None if result.thresholds is None
            else {str(c): _json_float(v) for c, v in sorted(result.thresholds.items())}
        ),
        "bootstrap": (
            None if result.bootstrap is None
            else {str(c): [_json_float(lo), _json_float(hi)]
                  for c, (lo, hi) in sorted(result.bootstrap.items())}
        ),
    }
    (OUT / "calibration_result.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n"
    )
    if result.thresholds is not None:
        (OUT / "threshold_table.json").write_text(
            json.dumps({
                "calibration_identity": CALIBRATION_IDENTITY,
                "execution_manifest_sha256": manifest_digest,
                "validity": result.validity.value,
                "thresholds": {str(c): _json_float(v)
                               for c, v in sorted(result.thresholds.items())},
            }, indent=1, sort_keys=True) + "\n"
        )

    # Timestamps live only here.
    (OUT / "provenance_sidecar.json").write_text(
        json.dumps({
            "execution_manifest_sha256": manifest_digest,
            "started_utc": started,
            "finished_utc": finished,
            "wall_seconds": round(elapsed, 3),
            "host_platform": platform.platform(),
        }, indent=1, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    sys.exit(main())
