"""Exposure guards for v2.

v2 decodes WUR-DEV-HOLD and WUR-SEALED peaks, which the v1 guards refuse.
That is legitimate only because both one-look records exist: HOLD was
scored once (`artifacts/wur_stage2b/hold_check.json`) and SEALED was scored
once (`artifacts/wur_stage3/first_sealed_access.json`). `assert_wur_exposed`
checks both records before any v2 code passes `allow_sealed=True`, so the
override cannot run on a checkout where the historical looks never happened.

The LCSB confirmation set (110 keys) was never used for fitting or scoring
and stays excluded; `lcsb_confirmation_keys` returns it so v2 loaders can
assert its absence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"

STAGE3_FIRST_ACCESS = ART / "wur_stage3" / "first_sealed_access.json"
STAGE3_RESULT_DOC = ROOT / "MURU_WUR_STAGE3_RESULT.md"
HOLD_CHECK = ART / "wur_stage2b" / "hold_check.json"
STAGE3_ONE_LOOK_HEAD = "69ca1a6"


class ExposureError(RuntimeError):
    """A v2 read was attempted on a population whose exposure is unrecorded."""


def assert_wur_exposed() -> dict:
    """Both historical one-look records must exist before v2 decodes HOLD or SEALED."""
    if not HOLD_CHECK.exists():
        raise ExposureError("hold_check.json is absent: WUR-DEV-HOLD is not recorded as exposed")
    if not STAGE3_FIRST_ACCESS.exists():
        raise ExposureError("first_sealed_access.json is absent: WUR-SEALED is not recorded as exposed")
    first = json.loads(STAGE3_FIRST_ACCESS.read_text())
    if not str(first.get("git_head", "")).startswith(STAGE3_ONE_LOOK_HEAD):
        raise ExposureError(f"the recorded sealed access is not the Stage 3 one look: {first}")
    hold = json.loads(HOLD_CHECK.read_text())
    if hold.get("hold_status") != "EXPOSED":
        raise ExposureError("hold_check.json does not mark HOLD as EXPOSED")
    return {"stage3_first_access": first, "hold_status": hold["hold_status"]}


def lcsb_confirmation_keys() -> set[str]:
    d = json.loads((ART / "confirmation_set_sealed.json").read_text())
    keys = d.get("inchikey_first_blocks") or d.get("connectivity_keys") or d.get("keys")
    if not keys:
        raise ExposureError("confirmation_set_sealed.json has no key list")
    return set(keys)
