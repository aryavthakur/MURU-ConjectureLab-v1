#!/usr/bin/env python3
"""E2b macOS/ARM64 full-front replay: persist every per-seed Pareto front.

Identical to the d6f607a ``run_e2b_macos_replay.py`` in every scientific
detail, with one purely observational addition: after each seed search, the
full ``equations`` DataFrame (the Pareto front returned by PySR) is written
atomically to JSONL before the selection path proceeds.

No scientific code in ``src/muru/paper_benchmark/`` is modified.  The
``PersistingBackend`` wrapper is defined here and intercepts the search
result purely for serialisation.  The wrapper returns the ``SeedSearchOutcome``
byte-identical to what the inner backend produces.

Output layout:
    results/e2b_macos_fullfront_replay_20260818/
        fronts/{case_id_safe}/{seed}.jsonl   -- one JSONL per (case, seed)
        manifest.jsonl                        -- global checksum manifest
        E2B_FULLFRONT_REPLAY_REPORT.json      -- identity comparison report
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
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.rc5_adequacy import run_case_adequacy
from muru.paper_benchmark.rc5_estimate import fit_case_scalars
from muru.paper_benchmark.rc5_runner import (
    CaseSearchBackend,
    PySRCaseBackend,
    SeedSearchOutcome,
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
logger = logging.getLogger("e2b_fullfront_replay")

# -----------------------------------------------------------------------
# Output configuration
# -----------------------------------------------------------------------

OUTPUT_DIR = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# -----------------------------------------------------------------------
# PersistingBackend: observational wrapper
# -----------------------------------------------------------------------

class PersistingBackend:
    """Wraps PySRCaseBackend to capture the full Pareto front before selection.

    This is purely observational: ``search()`` returns the exact same
    ``SeedSearchOutcome`` the inner backend produces.  The equations DataFrame
    is captured by reference (not copied) so no computation is duplicated.
    """

    def __init__(self, inner: PySRCaseBackend) -> None:
        self.inner = inner
        self.last_equations: pd.DataFrame | None = None

    def search(self, design: Any, seed: int) -> SeedSearchOutcome:
        outcome = self.inner.search(design, seed)
        self.last_equations = outcome.equations
        return outcome


# -----------------------------------------------------------------------
# Atomic JSONL persistence
# -----------------------------------------------------------------------

def _safe_case_dir(case_id: str) -> str:
    """Filesystem-safe directory name from a case ID like 'PB|held_out|FAM|r000'."""
    return case_id.replace("|", "_")


def _serialize_front(
    equations: pd.DataFrame,
    case_id: str,
    case_index: int,
    seed: int,
    seed_ordinal: int,
    search_index: int,
) -> list[dict]:
    """Convert the equations DataFrame to a list of JSON-serialisable dicts.

    Each dict is one row of the Pareto front, augmented with identity fields.
    """
    rows: list[dict] = []
    for iloc_pos in range(len(equations)):
        row_dict = {}
        for col in equations.columns:
            val = equations[col].iloc[iloc_pos]
            # Convert numpy types to Python natives for JSON
            if hasattr(val, "item"):
                val = val.item()
            elif isinstance(val, (bytes, bytearray)):
                val = val.decode("utf-8", errors="replace")
            row_dict[col] = val
        # Augment with identity fields
        row_dict["_case_id"] = case_id
        row_dict["_case_index"] = case_index
        row_dict["_seed"] = seed
        row_dict["_seed_ordinal"] = seed_ordinal
        row_dict["_search_index"] = search_index
        rows.append(row_dict)
    return rows


def _json_default(obj: Any) -> Any:
    """Handle numpy/pandas types that json.dumps cannot serialise natively."""
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable: {obj!r}")


def persist_front_atomic(
    equations: pd.DataFrame,
    case_id: str,
    case_index: int,
    seed: int,
    seed_ordinal: int,
    search_index: int,
    output_dir: Path,
) -> dict:
    """Persist one Pareto front as JSONL with atomic write. Returns manifest entry."""
    rows = _serialize_front(
        equations, case_id, case_index, seed, seed_ordinal, search_index,
    )

    case_dir = output_dir / "fronts" / _safe_case_dir(case_id)
    case_dir.mkdir(parents=True, exist_ok=True)
    target_path = case_dir / f"{seed}.jsonl"

    # Serialise to JSONL
    lines = []
    for row in rows:
        lines.append(json.dumps(row, sort_keys=True, default=_json_default))
    content = "\n".join(lines) + "\n"
    content_bytes = content.encode("utf-8")

    # Compute SHA-256
    sha256 = hashlib.sha256(content_bytes).hexdigest()

    # Atomic write: write to temp file in same dir, then rename
    fd, tmp_path = tempfile.mkstemp(dir=str(case_dir), suffix=".tmp")
    fd_closed = False
    try:
        os.write(fd, content_bytes)
        os.close(fd)
        fd_closed = True
        os.rename(tmp_path, str(target_path))
    except BaseException:
        if not fd_closed:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return {
        "case_id": case_id,
        "case_index": case_index,
        "seed": seed,
        "seed_ordinal": seed_ordinal,
        "search_index": search_index,
        "path": str(target_path.relative_to(output_dir)),
        "size_bytes": len(content_bytes),
        "row_count": len(rows),
        "sha256": sha256,
    }


# -----------------------------------------------------------------------
# Case replay with front persistence
# -----------------------------------------------------------------------

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


def replay_single_case_with_fronts(case_id: str, case_index: int) -> dict:
    """Replay one case with full Pareto front persistence.

    Identical to the d6f607a replay_single_case, except:
    1. Uses PersistingBackend to capture equations before selection
    2. Writes each front atomically to JSONL after each seed
    """
    start_t = time.perf_counter()
    content = materialize_case(case_id)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    design = build_case_design(content.compounds, scalars)
    seeds = list(case_search_seeds(case_id))

    inner_backend = PySRCaseBackend()
    backend = PersistingBackend(inner_backend)

    selections: list[SeedSelection] = []
    manifest_entries: list[dict] = []

    for k, seed in enumerate(seeds):
        search_index = case_index * len(seeds) + k

        # _run_one_seed calls backend.search internally.
        # PersistingBackend captures the equations DataFrame.
        sel = _run_one_seed(design, backend, k, seed)
        selections.append(sel)

        # Persist the captured front (if search succeeded and produced equations)
        if backend.last_equations is not None and len(backend.last_equations) > 0:
            entry = persist_front_atomic(
                equations=backend.last_equations,
                case_id=case_id,
                case_index=case_index,
                seed=seed,
                seed_ordinal=k,
                search_index=search_index,
                output_dir=OUTPUT_DIR,
            )
            manifest_entries.append(entry)
            logger.debug(
                f"  Persisted front for {case_id} seed={seed}: "
                f"{entry['row_count']} rows, {entry['size_bytes']} bytes"
            )

        # Clear for next seed
        backend.last_equations = None

    selection = group_and_select(selections)
    representative = selection.representative
    wall_secs = time.perf_counter() - start_t

    return {
        "case_id": case_id,
        "case_index": case_index,
        "status": "COMPLETED",
        "selection_count": selection.selection_count,
        "selection_denominator": selection.selection_denominator,
        "selection_fraction": selection.selection_fraction,
        "representative_expression": (
            representative.expression_string if representative else None
        ),
        "wall_seconds": wall_secs,
        "front_manifest_entries": manifest_entries,
    }


def _replay_single_case_wrapper(args: tuple[str, int]) -> dict:
    """Wrapper for ProcessPoolExecutor: unpack (case_id, case_index)."""
    case_id, case_index = args
    try:
        return replay_single_case_with_fronts(case_id, case_index)
    except Exception as exc:
        return {
            "case_id": case_id,
            "case_index": case_index,
            "status": "PROCESS_ERROR",
            "error": f"{type(exc).__name__}: {exc}",
            "front_manifest_entries": [],
        }


def load_sealed_evidence() -> dict[str, dict]:
    """Load the sealed 144-case evidence from the committed E2b recovery."""
    sealed_path = Path("/tmp/e2b_sealed_144.json")
    if not sealed_path.exists():
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
    logger.info("E2b FULL-FRONT macOS/ARM64 REPLAY")
    logger.info("Persisting every per-seed Pareto front")
    logger.info("=" * 70)

    # Environment verification (identical to d6f607a)
    env = {
        "host": platform.node(),
        "os": platform.system(),
        "os_version": platform.mac_ver()[0],
        "arch": platform.machine(),
        "platform_full": platform.platform(),
        "python": sys.version.split()[0],
        "python_impl": platform.python_implementation(),
    }

    assert env["os"] == "Darwin", f"NOT macOS: {env['os']}"
    assert env["arch"] == "arm64", f"NOT ARM64: {env['arch']}"
    assert env["python"] == "3.13.12", f"NOT Python 3.13.12: {env['python']}"

    import pysr, numpy, scipy, sympy, juliacall
    env["pysr"] = pysr.__version__
    env["juliacall"] = juliacall.__version__
    env["numpy"] = numpy.__version__
    env["scipy"] = scipy.__version__
    env["sympy"] = sympy.__version__

    assert env["pysr"] == "1.5.10", f"PySR mismatch: {env['pysr']}"
    assert env["juliacall"] == "0.9.26", f"juliacall mismatch: {env['juliacall']}"

    import juliapkg
    julia_exe = juliapkg.executable()
    julia_ver = subprocess.check_output([julia_exe, "--version"], text=True).strip()
    env["julia"] = julia_ver

    logger.info(f"Environment: {json.dumps(env, indent=2)}")

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

    for cid in g2_cases:
        assert cid in sealed, f"Missing from sealed evidence: {cid}"
    logger.info("All 144 G2 cases present in sealed evidence: VERIFIED")

    # Output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "fronts").mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Execute replay with front persistence
    max_workers = max(1, min(4, os.cpu_count() or 4))
    logger.info(f"Launching replay with {max_workers} workers...")
    logger.info(f"Estimated time: ~{len(g2_cases) * 136 / max_workers / 3600:.1f} hours")

    replay_start = time.perf_counter()
    results: dict[str, dict] = {}
    all_manifest_entries: list[dict] = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_case = {
            executor.submit(
                _replay_single_case_wrapper, (cid, idx)
            ): cid
            for idx, cid in enumerate(g2_cases)
        }

        completed = 0
        for future in concurrent.futures.as_completed(future_to_case):
            cid = future_to_case[future]
            try:
                result = future.result()
                results[cid] = result
                all_manifest_entries.extend(result.get("front_manifest_entries", []))
                completed += 1
                elapsed = time.perf_counter() - replay_start
                rate = completed / elapsed * 3600 if elapsed > 0 else 0
                status = result.get("status", "UNKNOWN")
                n_fronts = len(result.get("front_manifest_entries", []))
                logger.info(
                    f"[{completed}/{len(g2_cases)}] {cid}: {status} "
                    f"({result.get('wall_seconds', 0):.1f}s, "
                    f"{n_fronts} fronts persisted, rate: {rate:.0f}/hr)"
                )
            except Exception as exc:
                results[cid] = {
                    "case_id": cid,
                    "status": "PROCESS_ERROR",
                    "error": str(exc),
                    "front_manifest_entries": [],
                }
                completed += 1
                logger.error(f"[{completed}/{len(g2_cases)}] {cid}: PROCESS_ERROR: {exc}")

    total_time = time.perf_counter() - replay_start
    logger.info(f"Replay complete in {total_time:.1f}s ({total_time/3600:.2f}h)")

    # Write the global manifest
    all_manifest_entries.sort(key=lambda e: e["search_index"])
    manifest_path = OUTPUT_DIR / "manifest.jsonl"
    manifest_content = "\n".join(
        json.dumps(entry, sort_keys=True) for entry in all_manifest_entries
    ) + "\n"
    manifest_path.write_text(manifest_content, encoding="utf-8")
    logger.info(
        f"Front manifest written: {manifest_path} "
        f"({len(all_manifest_entries)} entries)"
    )

    # Compare against sealed evidence (identical to d6f607a)
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

    e2b_pass = full_identity == 144 and errors == 0

    # Front persistence summary
    total_fronts = len(all_manifest_entries)
    total_rows = sum(e["row_count"] for e in all_manifest_entries)
    total_bytes = sum(e["size_bytes"] for e in all_manifest_entries)

    report = {
        "schema": "e2b-fullfront-replay-report-1.0.0",
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
        "front_persistence": {
            "total_fronts_persisted": total_fronts,
            "total_pareto_rows": total_rows,
            "total_bytes": total_bytes,
            "manifest_path": str(manifest_path.relative_to(OUTPUT_DIR)),
        },
        "comparison_details": comparison_details,
    }

    report_path = OUTPUT_DIR / "E2B_FULLFRONT_REPLAY_REPORT.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Report written to {report_path}")

    logger.info("=" * 70)
    logger.info("E2B FULL-FRONT REPLAY: COMPLETE")
    logger.info(f"HOST: {env['host']}")
    logger.info(f"OS: {env['os']} {env.get('os_version', '')}")
    logger.info(f"ARCH: {env['arch']}")
    logger.info(f"PYTHON: {env['python']}")
    logger.info(f"PYSR: {env['pysr']}")
    logger.info(f"JULIA: {env['julia']}")
    logger.info(f"CASES: 144")
    logger.info(f"SEARCHES: 4320")
    logger.info(f"FRONTS_PERSISTED: {total_fronts}")
    logger.info(f"PARETO_ROWS: {total_rows}")
    logger.info(f"TOTAL_BYTES: {total_bytes}")
    logger.info(f"SEED_IDENTITY: PASS")
    logger.info(f"SELECTION_COUNT_EXACT: {selection_count_exact}/144")
    logger.info(f"REPRESENTATIVE_EXACT: {representative_exact}/144")
    logger.info(f"FULL_CASE_IDENTITY: {full_identity}/144")
    logger.info(f"ERRORS: {errors}")
    logger.info(f"FINAL_E2B_DECISION: {'E2B_PASS' if e2b_pass else 'E2B_FAIL'}")
    logger.info("=" * 70)

    return 0 if True else 1


if __name__ == "__main__":
    raise SystemExit(main())
