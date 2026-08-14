"""Mechanically populates MURU_CLAIM_MATRIX.md with evaluated verdicts and allowed wording."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from .verdict_engine import evaluate_claims


def populate_claim_matrix(
    claim_matrix_text: str,
    evaluated_claims: Mapping[str, Mapping[str, Any]],
) -> str:
    """Inject mechanically generated statuses and allowed wording into claim matrix text."""
    populated = claim_matrix_text

    # Replacement mappings for claims
    for claim_id, cinfo in evaluated_claims.items():
        # Match section for this claim
        # Example pattern: ## C4. Recovering mathematical family structure ... **Current status** | **PENDING.** ...
        status_pattern = rf"(\*\*Current status\*\*\s*\|\s*)\*\*PENDING\.\*\*(.*?)(?=\n\| \*\*Allowed wording)"
        
        # We replace the PENDING status block with the evaluated status and allowed wording
        status_str = f"**{cinfo.get('status', 'PENDING')}** (Verdict: {cinfo.get('verdict', 'N/A')})" if "verdict" in cinfo else f"**{cinfo.get('status', 'PENDING')}**"
        allowed_wording = cinfo.get("allowed_wording", "")

        # Target specific claim block
        # Replace "[PROSPECTIVE RESULT TO INSERT]" or placeholders in that claim's section if present
        pattern_claim = rf"(###?\s+{claim_id}\..*?)(?=\n###?\s+C|\Z)"
        match = re.search(pattern_claim, populated, re.DOTALL)
        if match:
            block = match.group(1)
            # Update status
            block_updated = re.sub(
                r"(\|\s*\*\*Current status\*\*\s*\|\s*)\*\*PENDING\.\*\*(.*?)(\n)",
                rf"\1{status_str}.\3",
                block
            )
            # Update allowed wording
            if allowed_wording:
                block_updated = re.sub(
                    r"(\|\s*\*\*Allowed wording if supported\*\*\s*\|\s*).*?(\n)",
                    rf"\1\"{allowed_wording}\"\2",
                    block_updated
                )
            populated = populated[:match.start()] + block_updated + populated[match.end():]

    return populated


def update_claim_matrix_file(
    matrix_path: Path,
    evaluated_claims: Mapping[str, Mapping[str, Any]],
    output_path: Path | None = None,
) -> Path:
    """Read claim matrix markdown, apply updates, and write populated output."""
    if not matrix_path.exists():
        raise FileNotFoundError(f"Claim matrix file not found: {matrix_path}")

    text = matrix_path.read_text(encoding="utf-8")
    updated_text = populate_claim_matrix(text, evaluated_claims)

    dest = output_path or matrix_path.parent / "results" / "MURU_CLAIM_MATRIX_POPULATED.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(updated_text, encoding="utf-8")
    return dest
