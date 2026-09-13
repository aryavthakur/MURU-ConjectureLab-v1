"""Append-only v2 experiment ledger (protocol section 14)."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "artifacts" / "wur_v2" / "ledger" / "ledger.jsonl"
REQUIRED = ("experiment_id", "generation", "hypothesis", "parent_model", "population_sha256", "partition",
            "representation", "endpoint", "hyperparameters_and_space", "tuning_process", "results",
            "uncertainty", "tail_metrics", "interpretation", "decision", "reason", "informed_later_decisions")


def git_state() -> dict:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    return {"code_sha": sha, "tree_dirty": dirty}


def _default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def existing_ids() -> set[str]:
    if not LEDGER.exists():
        return set()
    return {json.loads(line)["experiment_id"] for line in LEDGER.read_text().splitlines() if line.strip()}


def append(record: dict) -> dict:
    missing = [k for k in REQUIRED if k not in record]
    if missing:
        raise ValueError(f"ledger record lacks {missing}")
    if record["experiment_id"] in existing_ids():
        raise FileExistsError(f"ledger already has {record['experiment_id']}; entries are immutable")
    rec = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **git_state(), **record}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as fh:
        fh.write(json.dumps(rec, sort_keys=True, default=_default) + "\n")
    return rec
