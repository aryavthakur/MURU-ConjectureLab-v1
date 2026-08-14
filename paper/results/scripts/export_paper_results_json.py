"""Assembles and exports the master machine-readable paper_results.json payload."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .verdict_engine import evaluate_all_gates, evaluate_claims
from .update_evidence_ledger import generate_class_c_ledger_entries


def assemble_master_payload(
    cal_data: Mapping[str, Any],
    dev_data: Mapping[str, Any],
    held_out_data: Mapping[str, Any],
    code_commit: str = "UNKNOWN",
    cal_sha256: str = "",
    dev_sha256: str = "",
    ho_sha256: str = "",
    preflight_sha256: str = "",
) -> dict[str, Any]:
    """Assemble the unified master result dictionary."""
    gate_verdicts = evaluate_all_gates(cal_data, held_out_data)
    claim_evals = evaluate_claims(gate_verdicts, held_out_data)

    payload: dict[str, Any] = {
        "schema_version": "muru-paper-results-1.0.0",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "governance": {
            "code_commit": code_commit,
            "calibration_artifact_sha256": cal_sha256,
            "development_artifact_sha256": dev_sha256,
            "held_out_artifact_sha256": ho_sha256,
            "preflight_sha256": preflight_sha256,
        },
        "calibration": dict(cal_data),
        "development": dict(dev_data),
        "held_out": dict(held_out_data),
        "gate_verdicts": gate_verdicts,
        "claim_evaluations": claim_evals,
    }

    # Add Class C evidence ledger updates
    payload["evidence_ledger_updates"] = generate_class_c_ledger_entries(payload)

    return payload


def export_master_payload_file(
    payload: Mapping[str, Any],
    output_path: Path,
) -> Path:
    """Write master result payload to json file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload_str = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    output_path.write_text(payload_str, encoding="utf-8")
    return output_path
