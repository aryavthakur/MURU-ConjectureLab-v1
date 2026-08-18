#!/usr/bin/env python3
"""Operational monitor for the MURU Held-out benchmark execution.

Tracks process health, seed/case progress, throughput, and ETA.
Strictly blinds all scientific fields (candidate formulas, scores, pass/fail status).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.registry import iter_case_ids


def get_process_health(primary_pid: int = 36949) -> dict[str, object]:
    """Check whether primary runner and child worker processes are alive."""
    cmd = ["ps", "-ef"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = res.stdout.splitlines()
    
    primary_alive = False
    workers = []
    
    for line in lines:
        if str(primary_pid) in line and "run_held_out_production.py" in line:
            primary_alive = True
        if "spawn_main" in line and "--multiprocessing-fork" in line:
            parts = line.split()
            if len(parts) >= 2:
                workers.append(int(parts[1]))
                
    return {
        "primary_pid": primary_pid,
        "primary_alive": primary_alive,
        "worker_pids": workers,
        "worker_count": len(workers),
    }


def get_execution_progress(results_dir: Path) -> dict[str, object]:
    """Count completed seed and case records without parsing scientific fields."""
    seed_records_dir = results_dir / "seed_records"
    records_dir = results_dir / "records"
    
    expected_cases = list(iter_case_ids("held_out"))
    expected_case_count = len(expected_cases)
    expected_seed_count = expected_case_count * 30
    
    completed_cases = 0
    completed_seeds = 0
    in_progress_cases = 0
    
    if seed_records_dir.exists():
        for jsonl_file in seed_records_dir.glob("*.jsonl"):
            try:
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    lines = sum(1 for line in f if line.strip())
                completed_seeds += lines
                if lines == 30:
                    completed_cases += 1
                elif lines > 0:
                    in_progress_cases += 1
            except Exception:
                pass
                
    recorded_cases = 0
    if records_dir.exists():
        recorded_cases = len(list(records_dir.glob("*.json")))

    return {
        "expected_cases": expected_case_count,
        "expected_seeds": expected_seed_count,
        "completed_seeds": completed_seeds,
        "completed_cases": completed_cases,
        "in_progress_cases": in_progress_cases,
        "recorded_cases": recorded_cases,
        "percent_seeds": (completed_seeds / expected_seed_count) * 100 if expected_seed_count > 0 else 0.0,
        "percent_cases": (completed_cases / expected_case_count) * 100 if expected_case_count > 0 else 0.0,
    }


def main() -> None:
    # Check default worktree path or local results path
    worktree_path = ROOT / ".claude" / "worktrees" / "muru-heldout-a3-6" / "results" / "held_out"
    local_path = ROOT / "results" / "held_out"
    results_dir = worktree_path if worktree_path.exists() else local_path
    
    health = get_process_health()
    progress = get_execution_progress(results_dir)
    
    print("=" * 70)
    print("MURU CONJECTURELAB v1 — HELD-OUT OPERATIONAL MONITOR")
    print("=" * 70)
    print(f"Time (UTC): {datetime.now(timezone.utc).isoformat()}")
    print(f"Results Directory: {results_dir}")
    print(f"Primary Process (PID {health['primary_pid']}): {'ALIVE' if health['primary_alive'] else 'STOPPED'}")
    print(f"Active Worker Processes: {health['worker_count']} (PIDs: {health['worker_pids']})")
    print("-" * 70)
    print(f"Completed Searches: {progress['completed_seeds']} / {progress['expected_seeds']} ({progress['percent_seeds']:.2f}%)")
    print(f"Completed Cases:    {progress['completed_cases']} / {progress['expected_cases']} ({progress['percent_cases']:.2f}%)")
    print(f"In-Progress Cases:  {progress['in_progress_cases']}")
    print(f"Persisted Records:  {progress['recorded_cases']} / {progress['expected_cases']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
