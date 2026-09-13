"""Anchor parser-preflight scopes for MSnLib confirmation study 2 (structure and identity only, no spectra).

A scope is one (well, anchor compound) pair whose fixed-rung scans the preflight may decode. MSnLib wells pool
8 to 10 compounds, so a scope is admitted only if no OTHER compound plated in the same well could share the
anchor's precursor isolation: no co-plated ion ([M+H]+, [M+NH4]+, [M+Na]+, [M+K]+, [M-H2O+H]+, [M+H]+ 13C, or
the permanent-cation M+) within ISO_TOL = 0.7 Da of the anchor's [M+H]+, and no co-plated compound with the
same parent formula (an isomer is indistinguishable by precursor m/z). These are the census's own 12a
conflict rules (scripts/wur_v2_confirmation/01_build_sample_and_massive_manifest.py), applied to anchor
scopes instead of validation wells. SEL_TOL alone (0.01 Da) would admit an isomer or near-isobar.
"""
from __future__ import annotations

import math

PROTON = 1.007276
ISO_TOL = 0.7
SHIFTS = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
          "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355}


def _ions(row: dict) -> list[float]:
    charge = row.get("parent_charge")
    if charge == 0 and row.get("mh") is not None and not math.isnan(row["mh"]):
        m = row["mh"] - PROTON
        return [m + s for s in SHIFTS.values()]
    if row.get("m_plus") is not None and not math.isnan(row["m_plus"]):
        return [row["m_plus"]]
    return []


def admissible_anchor_scopes(well_rows: list[dict], anchor_keys: set) -> tuple[list[dict], list[dict]]:
    """well_rows: every design-table row of ONE well (key, parent_charge, mh, m_plus, parent_formula).

    Returns (admitted, rejected). Each admitted scope: {key, mh}. Each rejected: {key, mh, reason}.
    Rows with no parseable key or no neutral [M+H]+ are never admitted as anchors, and a row with an unknown
    identity (key None) makes every anchor in the well inadmissible, since its ions cannot be ruled out.
    """
    admitted, rejected = [], []
    unknown = any(r.get("key") is None for r in well_rows)
    for a in well_rows:
        if a.get("key") not in anchor_keys:
            continue
        mh = a.get("mh")
        if a.get("parent_charge") != 0 or mh is None or math.isnan(mh):
            rejected.append({"key": a["key"], "mh": mh, "reason": "anchor has no neutral [M+H]+"})
            continue
        if unknown:
            rejected.append({"key": a["key"], "mh": mh, "reason": "well holds a compound of unknown identity"})
            continue
        reason = None
        for o in well_rows:
            if o.get("key") == a["key"]:
                continue
            if o.get("parent_formula") is not None and o.get("parent_formula") == a.get("parent_formula"):
                reason = f"co-plated isomer {o['key']} (same formula)"
                break
            close = [i for i in _ions(o) if abs(i - mh) <= ISO_TOL]
            if close:
                reason = f"co-plated {o['key']} ion {min(close, key=lambda i: abs(i - mh)):.4f} within {ISO_TOL} Da"
                break
        if reason:
            rejected.append({"key": a["key"], "mh": mh, "reason": reason})
        else:
            admitted.append({"key": a["key"], "mh": mh})
    return admitted, rejected
