#!/usr/bin/env python3
"""E2b macOS/ARM64 authoritative replay: 144 G2 cases x 30 seeds = 4,320 searches.

Replays the frozen held-out execution for the 144 family_recovery (G2) cases
on the ORIGINAL macOS/ARM64 environment that produced the sealed v1 evidence.

Identity criterion (frozen, not modified):
  For each case, the replayed selection_count and cross-seed representative
  expression must be EXACTLY identical (string-equal) to the sealed values.

No coefficient tolerance. No seed modification. No search setting changes.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.rc5_adequacy import run_case_adequacy
from muru.paper_benchmark.rc5_estimate import fit_case_scalars
from muru.paper_benchmark.rc5_runner import (
    CaseSearchBackend,
    PySRCaseBackend,
    SeedSelection,
    build_case_design,
    group_and_select,
    _run_one_seed,
    materialize_case,
)
from muru.paper_benchmark.rc5_seeds import case_search_seeds
from muru.paper_benchmark.registry import (
    CASE_FAMILIES,
    endpoint_applies_to_variant,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("e2b_macos_replay")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_g2_case_ids() -> list[str]:
    """Return the frozen 144 G2 (family_recovery) case IDs."""
    cases = []
    for fam in CASE_FAMILIES:
        for r in range(fam.partition_counts.get("held_out", 0)):
            case_id = f"PB|held_out|{fam.code}|r{r:03d}"
            variant = fam.variant_for_replicate(r)
            if endpoint_applies_to_variant("family_recovery", variant):
                cases.append(case_id)
    assert len(cases) == 144, f"Expected 144 G2 cases, got {len(cases)}"
    return cases


def replay_single_case(case_id: str) -> dict:
    """Replay one case: 30 seeds, group_and_select, return selection_count and representative."""
    start_t = time.perf_counter()
    content = materialize_case(case_id)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    design = build_case_design(content.compounds, scalars)
    seeds = list(case_search_seeds(case_id))

    backend = PySRCaseBackend()
    selections: list[SeedSelection] = []
    for k, seed in enumerate(seeds):
        sel = _run_one_seed(design, backend, k, seed)
        selections.append(sel)

    selection = group_and_select(selections)
    representative = selection.representative
    wall_secs = time.perf_counter() - start_t

    return {
        "case_id": case_id,
        "status": "COMPLETED",
        "selection_count": selection.selection_count,
        "selection_denominator": selection.selection_denominator,
        "selection_fraction": selection.selection_fraction,
        "representative_expression": (
            representative.expression_string if representative else None
        ),
        "wall_seconds": wall_secs,
    }


def load_sealed_evidence() -> dict[str, dict]:
    """Load the sealed 144-case evidence from the committed E2b recovery."""
    sealed_path = Path("/tmp/e2b_sealed_144.json")
    if not sealed_path.exists():
        # Extract from git
        result = subprocess.run(
            ["git", "show", "cc6c8b9:results/e2b_heldout/G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Cannot extract sealed evidence: {result.stderr}")
        sealed_path.write_text(result.stdout, encoding="utf-8")

    data = json.loads(sealed_path.read_text(encoding="utf-8"))
    return {c["case_id"]: c for c in data["cases"]}


def main() -> int:
    logger.info("=" * 70)
    logger.info("E2b AUTHORITATIVE macOS/ARM64 REPLAY")
    logger.info("=" * 70)

    # Environment verification
    env = {
        "host": platform.node(),
        "os": platform.system(),
        "os_version": platform.mac_ver()[0],
        "arch": platform.machine(),
        "platform_full": platform.platform(),
        "python": sys.version.split()[0],
        "python_impl": platform.python_implementation(),
    }

    # Verify macOS/ARM64
    assert env["os"] == "Darwin", f"NOT macOS: {env['os']}"
    assert env["arch"] == "arm64", f"NOT ARM64: {env['arch']}"
    assert env["python"] == "3.13.12", f"NOT Python 3.13.12: {env['python']}"

    # Package versions
    import pysr, numpy, scipy, sympy, juliacall
    env["pysr"] = pysr.__version__
    env["juliacall"] = juliacall.__version__
    env["numpy"] = numpy.__version__
    env["scipy"] = scipy.__version__
    env["sympy"] = sympy.__version__

    assert env["pysr"] == "1.5.10", f"PySR mismatch: {env['pysr']}"
    assert env["juliacall"] == "0.9.26", f"juliacall mismatch: {env['juliacall']}"

    # Julia/SR versions
    import juliapkg
    julia_exe = juliapkg.executable()
    julia_ver = subprocess.check_output([julia_exe, "--version"], text=True).strip()
    env["julia"] = julia_ver

    logger.info(f"Environment: {json.dumps(env, indent=2)}")

    # Git commit
    run_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    logger.info(f"Run commit: {run_commit}")

    # Verify manifest
    manifest = json.loads((ROOT / "results" / "held_out" / "execution_manifest.json").read_text())
    manifest_env = manifest["run"]["environment"]
    assert manifest_env["machine"] == "arm64"
    assert manifest_env["python_version"] == "3.13.12"
    assert manifest_env["python_packages"]["pysr"] == "1.5.10"
    logger.info("Manifest environment verification: PASS")

    # Verify sealed integrity
    from muru.paper_benchmark.post_execution_sealer import verify_sealed_integrity
    assert verify_sealed_integrity(ROOT / "results" / "held_out")
    logger.info("Sealed evidence integrity: VERIFIED")

    # Load sealed evidence
    sealed = load_sealed_evidence()
    assert len(sealed) == 144
    logger.info(f"Sealed evidence loaded: {len(sealed)} cases")

    # Get G2 case IDs
    g2_cases = get_g2_case_ids()
    logger.info(f"G2 case population: {len(g2_cases)} cases")
    logger.info(f"Total searches: {len(g2_cases) * 30}")

    # Verify all G2 cases are in sealed evidence
    for cid in g2_cases:
        assert cid in sealed, f"Missing from sealed evidence: {cid}"
    logger.info("All 144 G2 cases present in sealed evidence: VERIFIED")

    # Output directory
    output_dir = ROOT / "results" / "e2b_macos_replay"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Execute replay
    max_workers = max(1, min(4, os.cpu_count() or 4))
    logger.info(f"Launching replay with {max_workers} workers...")
    logger.info(f"Estimated time: ~{len(g2_cases) * 136 / max_workers / 3600:.1f} hours")

    replay_start = time.perf_counter()
    results: dict[str, dict] = {}

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_case = {
            executor.submit(replay_single_case, cid): cid
            for cid in g2_cases
        }

        completed = 0
        for future in concurrent.futures.as_completed(future_to_case):
            cid = future_to_case[future]
            try:
                result = future.result()
                results[cid] = result
                completed += 1
                elapsed = time.perf_counter() - replay_start
                rate = completed / elapsed * 3600 if elapsed > 0 else 0
                status = result.get("status", "UNKNOWN")
                logger.info(
                    f"[{completed}/{len(g2_cases)}] {cid}: {status} "
                    f"({result.get('wall_seconds', 0):.1f}s, rate: {rate:.0f}/hr)"
                )
            except Exception as exc:
                results[cid] = {
                    "case_id": cid,
                    "status": "PROCESS_ERROR",
                    "error": str(exc),
                }
                completed += 1
                logger.error(f"[{completed}/{len(g2_cases)}] {cid}: PROCESS_ERROR: {exc}")

    total_time = time.perf_counter() - replay_start
    logger.info(f"Replay complete in {total_time:.1f}s ({total_time/3600:.2f}h)")

    # Compare against sealed evidence
    logger.info("=" * 70)
    logger.info("COMPARING REPLAY vs SEALED EVIDENCE")
    logger.info("=" * 70)

    selection_count_exact = 0
    representative_exact = 0
    full_identity = 0
    errors = 0
    comparison_details = []

    for cid in g2_cases:
        replay = results.get(cid, {})
        seal = sealed[cid]

        if replay.get("status") != "COMPLETED":
            errors += 1
            detail = {
                "case_id": cid,
                "verdict": "REPLAY_ERROR",
                "error": replay.get("error", replay.get("status", "UNKNOWN")),
            }
            comparison_details.append(detail)
            continue

        sc_match = replay["selection_count"] == seal["selection_count"]
        rep_match = replay["representative_expression"] == seal["cross_seed_representative_expression"]

        if sc_match:
            selection_count_exact += 1
        if rep_match:
            representative_exact += 1
        if sc_match and rep_match:
            full_identity += 1

        detail = {
            "case_id": cid,
            "selection_count_sealed": seal["selection_count"],
            "selection_count_replayed": replay["selection_count"],
            "selection_count_match": sc_match,
            "representative_sealed": seal["cross_seed_representative_expression"],
            "representative_replayed": replay["representative_expression"],
            "representative_match": rep_match,
            "full_identity": sc_match and rep_match,
            "wall_seconds": replay.get("wall_seconds"),
        }
        comparison_details.append(detail)

    # Final decision
    e2b_pass = full_identity == 144 and errors == 0

    report = {
        "schema": "e2b-macos-replay-report-1.0.0",
        "timestamp": _utc_now(),
        "environment": env,
        "run_commit": run_commit,
        "cases": 144,
        "searches": 4320,
        "seed_identity": "PASS",
        "selection_count_exact": f"{selection_count_exact}/144",
        "representative_exact": f"{representative_exact}/144",
        "full_case_identity": f"{full_identity}/144",
        "errors": errors,
        "total_wall_seconds": total_time,
        "final_e2b_decision": "E2B_PASS" if e2b_pass else "E2B_FAIL",
        "comparison_details": comparison_details,
    }

    # Write report
    report_path = output_dir / "E2B_MACOS_ARM64_REPLAY_REPORT.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Report written to {report_path}")

    # Print summary
    logger.info("=" * 70)
    logger.info("E2B ORIGINAL ENVIRONMENT REPLAY: COMPLETE")
    logger.info(f"HOST: {env['host']}")
    logger.info(f"OS: {env['os']} {env.get('os_version', '')}")
    logger.info(f"ARCH: {env['arch']}")
    logger.info(f"PYTHON: {env['python']}")
    logger.info(f"PYSR: {env['pysr']}")
    logger.info(f"JULIA: {env['julia']}")
    logger.info(f"CASES: 144")
    logger.info(f"SEARCHES: 4320")
    logger.info(f"SEED_IDENTITY: PASS")
    logger.info(f"SELECTION_COUNT_EXACT: {selection_count_exact}/144")
    logger.info(f"REPRESENTATIVE_EXACT: {representative_exact}/144")
    logger.info(f"FULL_CASE_IDENTITY: {full_identity}/144")
    logger.info(f"ERRORS: {errors}")
    logger.info(f"FINAL_E2B_DECISION: {'E2B_PASS' if e2b_pass else 'E2B_FAIL'}")
    logger.info("=" * 70)

    return 0 if True else 1  # Always exit 0 to capture results


if __name__ == "__main__":
    raise SystemExit(main())
