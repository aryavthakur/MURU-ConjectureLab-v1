"""The frozen decision rule for the objective-alignment validation study.

`TYPE2_VALIDATION_DECISION.md` begins with exactly one of

    AUTHORIZE RE-SCOPED PHASE 4
    DO NOT AUTHORIZE PHASE 4
    INCONCLUSIVE DUE TO BLOCKER

computed by `decide()` from machine-readable artifacts, never chosen afterwards.
`GO TO PHASE 3` is not a possible output: Phase 3 is over and is not reopened.

Every threshold below is fixed by `TYPE2_VALIDATION_PREREGISTRATION.md` before
the fresh worlds exist.
"""
from __future__ import annotations

import numpy as np

DECISION_VERSION = "ov-decision-1.0.0"

# --- frozen thresholds -------------------------------------------------------
MIN_G1B_SUCCESS = 0.80            # master plan §20 Phase 3 acceptance, on the
                                  # moderate regime
MIN_G1A_SUCCESS = 1.00            # a transparent law must be recovered every time
MAX_FALSE_POSITIVE_RATE = 0.05    # master plan §18.3 / K6
MIN_G1B_MEDIAN_SELECTION = 20.0 / 30.0
MIN_NULL_CLEARANCE_ABOVE_CI = 0.80   # fraction of accepted G1B worlds whose R^2
                                     # exceeds the UPPER bootstrap bound of the
                                     # threshold, not merely its point estimate

MAX_G2_ACCEPTED = 1               # of 8
MAX_G3_NONMASS = 0                # of 8
MAX_G4M_NONMASS = 0               # of 30
MAX_GC_NONMASS = 1                # of 9
MAX_G5_NONMASS = 2                # of 8
MAX_GRT_NONMASS = 1               # of 4
MAX_G1C_FALSE_IDENTIFICATION = 1  # of 10


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial interval. `p = 0` is never claimed for a finite count."""
    from scipy.stats import beta
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def type2_success(row: dict) -> bool:
    """Did this world deliver the Type 2 claim it was built to test?

    Acceptance plus block-level support recovery plus exponent recovery within
    the master plan's ±0.15 plus shape-family recovery. Exact algebraic-form
    recovery is NOT part of it — that is the whole point of the claim class, and
    it is measured and reported separately.
    """
    rec = row.get("recovery", {})
    if not row.get("accepted"):
        return False
    sup = rec.get("support_recovery", {})
    exp = rec.get("exponent_recovery", {})
    shp = rec.get("shape", {})
    if not (sup.get("applicable") and exp.get("applicable")):
        return False
    ok = bool(sup.get("recovered") and exp.get("recovered"))
    if shp.get("applicable"):
        ok = ok and bool(shp.get("shape_family_recovered"))
    return ok


def _rows(rows: list[dict], block: str, regime: str | None = None) -> list[dict]:
    out = [r for r in rows if r["block"] == block]
    if regime:
        out = [r for r in out if r["noise_regime"] == regime]
    return out


def decide(rows: list[dict], calibration: dict, corroboration: dict,
           seal: dict, coverage: dict) -> dict:
    """Compute the verdict. `rows` are the joined recovery + adjudication rows."""
    stops: list[str] = []
    blockers: list[str] = []
    m: dict = {}

    # --- coverage: is every gate evaluable at all? --------------------------
    for k, v in coverage.items():
        if not v["complete"]:
            blockers.append(f"{k}: {v['have']}/{v['expected']} worlds present")

    # --- positive controls ---------------------------------------------------
    # The analytic sanity anchor is gated on the regimes where recovery is
    # supposed to be easy. Its adverse-regime worlds are reported as a
    # diagnostic: a transparent law that fails at SD 0.06 says something about
    # the noise ceiling, not about whether the pipeline works.
    g1a = _rows(rows, "G1A")
    g1a_gate = [r for r in g1a if r["noise_regime"] in ("low", "moderate")]
    m["G1A"] = {"n": len(g1a), "success": sum(map(type2_success, g1a)),
                "n_gated": len(g1a_gate),
                "success_gated": sum(map(type2_success, g1a_gate)),
                "adverse_success": sum(map(type2_success,
                                           [r for r in g1a
                                            if r["noise_regime"] == "adverse"]))}
    if not g1a_gate:
        blockers.append("no G1A low/moderate worlds")
    elif m["G1A"]["success_gated"] / len(g1a_gate) < MIN_G1A_SUCCESS:
        stops.append(f"G1A analytic sanity: {m['G1A']['success_gated']}/"
                     f"{len(g1a_gate)} at low+moderate noise, below the "
                     f"required {MIN_G1A_SUCCESS:.0%}")

    for regime in ("low", "moderate", "adverse"):
        rs = _rows(rows, "G1B", regime)
        m[f"G1B_{regime}"] = {
            "n": len(rs), "success": sum(map(type2_success, rs)),
            "rate": (sum(map(type2_success, rs)) / len(rs)) if rs else float("nan"),
            "median_selection_fraction": (float(np.median(
                [r["selection_fraction"] for r in rs])) if rs else float("nan")),
        }
    gate = m["G1B_moderate"]
    if not gate["n"]:
        blockers.append("no G1B moderate worlds")
    elif gate["rate"] < MIN_G1B_SUCCESS:
        stops.append(f"G1B moderate Type 2 recovery {gate['rate']:.2f} "
                     f"< {MIN_G1B_SUCCESS}")
    if gate["n"] and gate["median_selection_fraction"] < MIN_G1B_MEDIAN_SELECTION:
        stops.append(f"median G1B selection fraction "
                     f"{gate['median_selection_fraction']:.2f} below 20/30")

    # --- G1C: the near-degeneracy challenge ---------------------------------
    g1c = _rows(rows, "G1C")
    false_id = [r for r in g1c
                if r.get("accepted")
                and r["recovery"].get("exact_form", {}).get("algebraic_form_identified")
                and not r["recovery"].get("exact_form", {}).get("system_reported_the_law")]
    m["G1C"] = {"n": len(g1c), "type2_success": sum(map(type2_success, g1c)),
                "false_identification_claims": len(false_id),
                "worlds": [r["world_id"] for r in false_id]}
    if len(false_id) > MAX_G1C_FALSE_IDENTIFICATION:
        stops.append(f"G1C: {len(false_id)} worlds claimed the algebraic form "
                     f"was identified when it was not "
                     f"(> {MAX_G1C_FALSE_IDENTIFICATION})")

    # --- false-positive gate -------------------------------------------------
    g4 = _rows(rows, "G4")
    fp = [r for r in g4 if r.get("accepted")]
    n, k = len(g4), len(fp)
    lo, hi = clopper_pearson(k, n) if n else (float("nan"), float("nan"))
    m["G4"] = {"n": n, "accepted": k,
               "rate": (k / n) if n else float("nan"),
               "clopper_pearson_95": [lo, hi],
               "accepted_worlds": [r["world_id"] for r in fp]}
    if not n:
        blockers.append("no G4 null worlds")
    elif k / n > MAX_FALSE_POSITIVE_RATE:
        stops.append(f"fresh G4 false-positive rate {k}/{n} = {k/n:.3f} "
                     f"> {MAX_FALSE_POSITIVE_RATE}")

    # --- refusal worlds ------------------------------------------------------
    def nonmass(block: str) -> list[dict]:
        return [r for r in _rows(rows, block)
                if r.get("accepted") and r.get("claims_non_mass_structure")]

    checks = [("G2", None, MAX_G2_ACCEPTED, "accepted compact conjecture"),
              ("G3", "nonmass", MAX_G3_NONMASS, "non-mass structural claim"),
              ("G4M", "nonmass", MAX_G4M_NONMASS, "non-mass structural claim"),
              ("GC", "nonmass", MAX_GC_NONMASS, "non-mass structural claim"),
              ("G5", "nonmass", MAX_G5_NONMASS, "non-mass structural claim"),
              ("GRT", "nonmass", MAX_GRT_NONMASS, "non-mass structural claim")]
    for block, kind, limit, label in checks:
        rs = _rows(rows, block)
        bad = (nonmass(block) if kind == "nonmass"
               else [r for r in rs if r.get("accepted")])
        m[block] = {"n": len(rs), "violations": len(bad), "limit": limit,
                    "worlds": [r["world_id"] for r in bad]}
        if len(bad) > limit:
            stops.append(f"{block}: {len(bad)} of {len(rs)} worlds produced an "
                         f"{label}, above the pre-registered limit of {limit}")

    # --- null calibration stability -----------------------------------------
    hi_ci = calibration.get("threshold_ci_hi") or []
    acc_g1b = [r for r in _rows(rows, "G1B", "moderate") if r.get("accepted")]
    clear = 0
    for r in acc_g1b:
        c = int(r.get("complexity") or 0)
        bound = hi_ci[min(c, len(hi_ci) - 1)] if hi_ci else np.inf
        if r.get("valid_r2", -np.inf) > bound:
            clear += 1
    frac = (clear / len(acc_g1b)) if acc_g1b else float("nan")
    m["null_calibration"] = {
        "n_calibration_worlds": calibration.get("n_calibration_worlds"),
        "accepted_g1b_moderate": len(acc_g1b),
        "clearing_upper_ci": clear, "fraction": frac,
        "requirement": MIN_NULL_CLEARANCE_ABOVE_CI}
    if acc_g1b and frac < MIN_NULL_CLEARANCE_ABOVE_CI:
        stops.append(f"null thresholds too uncertain to adjudicate: only "
                     f"{clear}/{len(acc_g1b)} accepted G1B moderate candidates "
                     f"clear the threshold's upper bootstrap bound")

    # --- independent-engine corroboration ------------------------------------
    m["corroboration"] = corroboration.get("gate", {})
    if not corroboration.get("gate", {}).get("satisfied"):
        stops.append("independent-engine corroboration did not meet the frozen "
                     "claim-relevant standard")

    # --- seal ----------------------------------------------------------------
    m["seal"] = seal
    if not seal.get("intact"):
        blockers.append("the sealed confirmation set hash changed during the study")
    if seal.get("real_data_symbolic_search_ran"):
        blockers.append("a real-data symbolic search was executed")

    if blockers:
        verdict = "INCONCLUSIVE DUE TO BLOCKER"
    elif stops:
        verdict = "DO NOT AUTHORIZE PHASE 4"
    else:
        verdict = "AUTHORIZE RE-SCOPED PHASE 4"

    return {"decision_version": DECISION_VERSION, "verdict": verdict,
            "stop_conditions_fired": stops, "blockers": blockers, "metrics": m}
