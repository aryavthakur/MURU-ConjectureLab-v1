"""Strict evaluator input contract for a future locked MURU engine."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class StrictCandidate:
    expression: str
    predictions: tuple[complex | float, ...]
    grammar_version: str = ""


def validate_candidate(candidate: StrictCandidate) -> None:
    """Require a versioned expression with only finite real predictions."""
    if not candidate.expression or not candidate.grammar_version:
        raise ValueError("candidate requires expression and grammar version")
    values = np.asarray(candidate.predictions)
    if np.iscomplexobj(values) or not np.isfinite(values).all():
        raise ValueError("candidate must evaluate to finite real values")
