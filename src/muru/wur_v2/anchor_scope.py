"""Ion model and anchor parser-preflight scopes for MSnLib confirmation study 2 (structure and identity only).

A scope is one (well, anchor compound) pair whose fixed-rung scans the preflight may decode. MSnLib wells pool
8 to 10 compounds, so a scope is admitted only if no OTHER compound plated in the same well could share the
anchor's precursor isolation: no co-plated ion (ION_FORMS below) within ISO_TOL = 0.7 Da of the anchor's [M+H]+,
and no co-plated compound with the same parent formula (an isomer is indistinguishable by precursor m/z). These
extend the census's own 12a conflict rules (scripts/wur_v2_confirmation/01_build_sample_and_massive_manifest.py).

ION_FORMS (review finding REG-1, 2026-09-13): the census list of singly charged adducts missed real decoded
spectra that were same-plate carryover triggered on [M+2H]2+, [M+3H]3+ and [M+H-NH3]+ ions, so the model now
includes multiply charged, cluster, solvent and in-source forms. A permanent cation of charge z contributes m/z
M+/z.
"""
from __future__ import annotations

import math

PROTON = 1.007276
NA, K, NH4 = 22.989218, 38.963158, 18.033823
H2O, NH3, ACN, C13 = 18.010565, 17.026549, 41.026549, 1.003355
ISO_TOL = 0.7

# name -> (multiplier of neutral M, added mass, charge)
ION_FORMS = {
    "[M+H]+": (1, PROTON, 1), "[M+NH4]+": (1, NH4, 1), "[M+Na]+": (1, NA, 1), "[M+K]+": (1, K, 1),
    "[M-H2O+H]+": (1, PROTON - H2O, 1), "[M+H]+13C": (1, PROTON + C13, 1), "[M+H-NH3]+": (1, PROTON - NH3, 1),
    "[M+ACN+H]+": (1, ACN + PROTON, 1), "[2M+H]+": (2, PROTON, 1), "[2M+Na]+": (2, NA, 1),
    "[M+2H]2+": (1, 2 * PROTON, 2), "[M+H+Na]2+": (1, PROTON + NA, 2), "[M+H+NH4]2+": (1, PROTON + NH4, 2),
    "[M+3H]3+": (1, 3 * PROTON, 3),
}
# the census 12a singly charged set, kept for rules that are defined on it
SHIFTS = {k: ION_FORMS[k][1] for k in ("[M+H]+", "[M+NH4]+", "[M+Na]+", "[M+K]+", "[M-H2O+H]+", "[M+H]+13C")}


def _finite(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def ion_mzs(parent_charge, mh, m_plus, forms=None) -> list[float]:
    """Theoretical m/z values of one compound. Neutral parents use ION_FORMS (or `forms`); a permanent cation
    of charge z >= 1 contributes M+/z only."""
    if parent_charge == 0 and _finite(mh):
        m = mh - PROTON
        names = forms if forms is not None else ION_FORMS
        return [(mult * m + add) / z for mult, add, z in (ION_FORMS[n] for n in names)]
    if parent_charge is not None and _finite(parent_charge) and parent_charge > 0 and _finite(m_plus):
        return [m_plus / int(parent_charge)]
    return []


def _ions(row: dict) -> list[float]:
    return ion_mzs(row.get("parent_charge"), row.get("mh"), row.get("m_plus"))


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
        if a.get("parent_charge") != 0 or not _finite(mh):
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
