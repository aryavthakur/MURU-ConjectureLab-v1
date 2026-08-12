"""Phase-boundary enforcement.

Phase 3 builds and calibrates the discovery engine. It must not run symbolic
regression against the real `mu` response, and it must not open the sealed
confirmation outcomes. Those belong to Phase 4 and Phase 5 respectively, and
only if `PHASE3_DECISION.md` authorizes Phase 4.

This module is the single guarded door. It contains no Phase 4 implementation —
only the lock — so that `tests/test_p3_phase_boundary.py` can prove the door is
shut while Phase 3 is running.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

AUTHORIZING_VERDICTS = ("GO TO PHASE 4", "RESTRICT AND GO TO PHASE 4")


class PhaseBoundaryError(RuntimeError):
    """Raised when Phase 3 code attempts work reserved for a later phase."""


def phase3_verdict() -> str | None:
    """The first verdict line of `PHASE3_DECISION.md`, or None if absent."""
    p = ROOT / "PHASE3_DECISION.md"
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        s = line.lstrip("# ").strip()
        if s in ("GO TO PHASE 4", "RESTRICT AND GO TO PHASE 4",
                 "STOP BEFORE PHASE 4", "INCONCLUSIVE DUE TO BLOCKER"):
            return s
    return None


def phase4_authorized() -> bool:
    return phase3_verdict() in AUTHORIZING_VERDICTS


def assert_phase4_authorized(what: str = "real-data symbolic search") -> None:
    v = phase3_verdict()
    if v is None:
        raise PhaseBoundaryError(
            f"{what} is a Phase 4 activity and PHASE3_DECISION.md does not "
            "exist yet. Phase 3 must complete and authorize Phase 4 first.")
    if v not in AUTHORIZING_VERDICTS:
        raise PhaseBoundaryError(
            f"{what} is not authorized: PHASE3_DECISION.md states '{v}'.")


def real_data_symbolic_search(*args, **kwargs):
    """The Phase 4 entry point. Unimplemented, and locked.

    Phase 3 may not fit PySR, gplearn or any other symbolic engine to the
    observed real `mu` response, and may not test candidate equations against
    real development `mu` as a preview of Phase 4.
    """
    assert_phase4_authorized("real-data symbolic search")
    raise NotImplementedError(
        "Phase 4 is not implemented. Phase 3 authorizes it; it does not "
        "perform it.")


def assert_no_confirmation_outcomes(keys) -> None:
    """Guard against any confirmation compound's response being read."""
    seal = json.loads(
        (ROOT / "artifacts" / "confirmation_set_sealed.json").read_text())
    sealed = set(seal["connectivity_keys"])
    leaked = sealed & set(keys)
    if leaked:
        raise PhaseBoundaryError(
            f"{len(leaked)} sealed confirmation compounds reached a Phase 3 "
            "code path that reads outcomes; the seal must hold through Phase 3.")
