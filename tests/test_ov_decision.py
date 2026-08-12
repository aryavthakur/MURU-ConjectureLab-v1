"""Null-calibration arithmetic, false-positive counting and the verdict rule.

The decision must be computable from artifacts and must not be expressible in
prose only. Every stop condition is exercised in isolation, so a rule that
silently stopped firing would fail here rather than in the report.
"""
from __future__ import annotations

import math

import pytest

from muru.objval.decision import (MAX_FALSE_POSITIVE_RATE, MIN_G1B_SUCCESS,
                                  clopper_pearson, decide, type2_success)


# --- finite-simulation interval ---------------------------------------------
def test_zero_of_n_never_licenses_a_claim_of_zero():
    lo, hi = clopper_pearson(0, 100)
    assert lo == 0.0
    assert hi == pytest.approx(0.03621, abs=1e-4)
    assert hi > 0, "a point estimate of 0/N is not evidence that the rate is 0"


def test_interval_narrows_with_more_replicates():
    assert clopper_pearson(0, 300)[1] < clopper_pearson(0, 100)[1]


def test_interval_brackets_the_point_estimate():
    lo, hi = clopper_pearson(3, 100)
    assert lo < 0.03 < hi


def test_full_count_gives_an_upper_bound_of_one():
    assert clopper_pearson(10, 10) == (pytest.approx(0.6915, abs=1e-3), 1.0)


# --- Type 2 success ----------------------------------------------------------
def _row(block, regime="moderate", accepted=True, support=True, exponent=True,
         shape=True, nonmass=True, forms=3, exact=False, world="w", r2=0.9, cx=6):
    return {
        "world_id": world, "block": block, "noise_regime": regime,
        "accepted": accepted, "claims_non_mass_structure": nonmass,
        "selection_fraction": 1.0, "complexity": cx, "valid_r2": r2,
        "recovery": {
            "support_recovery": {"applicable": True, "recovered": support},
            "exponent_recovery": {"applicable": True, "recovered": exponent},
            "shape": {"applicable": True, "shape_family_recovered": shape},
            "exact_form": {"applicable": True, "system_reported_the_law": exact,
                           "algebraic_form_identified": forms == 1,
                           "search_found_the_law": True},
        }}


def test_type2_success_requires_acceptance_support_exponent_and_shape():
    assert type2_success(_row("G1B"))
    assert not type2_success(_row("G1B", accepted=False))
    assert not type2_success(_row("G1B", support=False))
    assert not type2_success(_row("G1B", exponent=False))
    assert not type2_success(_row("G1B", shape=False))


def test_type2_success_does_not_require_exact_form_recovery():
    assert type2_success(_row("G1B", exact=False, forms=5))


# --- the verdict -------------------------------------------------------------
CAL = {"n_calibration_worlds": 100,
       "threshold_ci_hi": [0.5] * 21}
CORR = {"gate": {"satisfied": True, "block_support_agreement": 0.7,
                 "mass_exponent_agreement": 0.7}}
SEAL = {"intact": True, "real_data_symbolic_search_ran": False}


def _coverage(complete=True):
    return {b: {"complete": complete, "have": 1, "expected": 1}
            for b in ("G1B", "G4")}


def _clean_rows():
    rows = []
    rows += [_row("G1A", r, world=f"a{r}") for r in ("low", "moderate")]
    rows += [_row("G1B", "moderate", world=f"b{i}", r2=0.9) for i in range(20)]
    rows += [_row("G1B", "low", world=f"bl{i}") for i in range(10)]
    rows += [_row("G1C", world=f"c{i}", forms=4) for i in range(10)]
    rows += [_row("G4", accepted=False, nonmass=False, world=f"n{i}")
             for i in range(100)]
    for b, n in (("G4M", 30), ("G2", 8), ("G3", 8), ("G5", 8), ("GC", 9),
                 ("GRT", 4)):
        rows += [_row(b, accepted=False, nonmass=False, world=f"{b}{i}")
                 for i in range(n)]
    return rows


def test_a_clean_run_authorizes():
    d = decide(_clean_rows(), CAL, CORR, SEAL, _coverage())
    assert d["verdict"] == "AUTHORIZE RE-SCOPED PHASE 4"
    assert not d["stop_conditions_fired"]


def test_positive_control_below_eighty_percent_stops():
    rows = _clean_rows()
    g1b = [r for r in rows if r["block"] == "G1B" and r["noise_regime"] == "moderate"]
    for r in g1b[:6]:                       # 14/20 = 0.70
        r["recovery"]["support_recovery"]["recovered"] = False
    d = decide(rows, CAL, CORR, SEAL, _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert any("G1B moderate" in s for s in d["stop_conditions_fired"])
    assert d["metrics"]["G1B_moderate"]["rate"] == pytest.approx(0.70)
    assert MIN_G1B_SUCCESS == 0.80


def test_false_positive_rate_above_five_percent_stops():
    rows = _clean_rows()
    for r in [r for r in rows if r["block"] == "G4"][:6]:
        r["accepted"] = True
    d = decide(rows, CAL, CORR, SEAL, _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert d["metrics"]["G4"]["rate"] == pytest.approx(0.06)
    assert d["metrics"]["G4"]["rate"] > MAX_FALSE_POSITIVE_RATE
    lo, hi = d["metrics"]["G4"]["clopper_pearson_95"]
    assert lo < 0.06 < hi


def test_five_of_a_hundred_false_positives_does_not_stop():
    rows = _clean_rows()
    for r in [r for r in rows if r["block"] == "G4"][:5]:
        r["accepted"] = True
    d = decide(rows, CAL, CORR, SEAL, _coverage())
    assert d["metrics"]["G4"]["rate"] == pytest.approx(0.05)
    assert not any("false-positive" in s for s in d["stop_conditions_fired"])


@pytest.mark.parametrize("block,n_bad", [("G3", 1), ("G4M", 1), ("GC", 2),
                                          ("G5", 3), ("GRT", 2), ("G2", 2)])
def test_each_refusal_world_limit_fires(block, n_bad):
    rows = _clean_rows()
    for r in [r for r in rows if r["block"] == block][:n_bad]:
        r["accepted"] = True
        r["claims_non_mass_structure"] = True
    d = decide(rows, CAL, CORR, SEAL, _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert any(s.startswith(block + ":") for s in d["stop_conditions_fired"])


def test_g1c_false_identification_claim_stops():
    rows = _clean_rows()
    for r in [r for r in rows if r["block"] == "G1C"][:2]:
        r["recovery"]["exact_form"]["algebraic_form_identified"] = True
        r["recovery"]["exact_form"]["system_reported_the_law"] = False
    d = decide(rows, CAL, CORR, SEAL, _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert any("G1C" in s for s in d["stop_conditions_fired"])


def test_an_unstable_null_threshold_stops():
    rows = _clean_rows()
    cal = {"n_calibration_worlds": 100, "threshold_ci_hi": [0.95] * 21}
    d = decide(rows, cal, CORR, SEAL, _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert any("too uncertain" in s for s in d["stop_conditions_fired"])


def test_failed_engine_corroboration_stops():
    d = decide(_clean_rows(), CAL, {"gate": {"satisfied": False}}, SEAL,
               _coverage())
    assert d["verdict"] == "DO NOT AUTHORIZE PHASE 4"
    assert any("corroboration" in s for s in d["stop_conditions_fired"])


def test_a_broken_seal_is_a_blocker_not_a_stop():
    d = decide(_clean_rows(), CAL, CORR,
               {"intact": False, "real_data_symbolic_search_ran": False},
               _coverage())
    assert d["verdict"] == "INCONCLUSIVE DUE TO BLOCKER"


def test_a_real_data_symbolic_search_is_a_blocker():
    d = decide(_clean_rows(), CAL, CORR,
               {"intact": True, "real_data_symbolic_search_ran": True},
               _coverage())
    assert d["verdict"] == "INCONCLUSIVE DUE TO BLOCKER"


def test_incomplete_coverage_is_a_blocker():
    d = decide(_clean_rows(), CAL, CORR, SEAL,
               {"G4": {"complete": False, "have": 61, "expected": 100}})
    assert d["verdict"] == "INCONCLUSIVE DUE TO BLOCKER"


def test_go_to_phase_3_is_not_a_possible_verdict():
    for args in ((_clean_rows(), CAL, CORR, SEAL, _coverage()),):
        assert decide(*args)["verdict"] in (
            "AUTHORIZE RE-SCOPED PHASE 4", "DO NOT AUTHORIZE PHASE 4",
            "INCONCLUSIVE DUE TO BLOCKER")


def test_a_blocker_outranks_a_stop_condition():
    rows = _clean_rows()
    for r in [r for r in rows if r["block"] == "G4"][:20]:
        r["accepted"] = True
    d = decide(rows, CAL, CORR, SEAL,
               {"G4": {"complete": False, "have": 80, "expected": 100}})
    assert d["verdict"] == "INCONCLUSIVE DUE TO BLOCKER"
    assert d["stop_conditions_fired"], "the stop is still recorded, not hidden"


def test_metrics_are_finite_or_explicitly_nan():
    d = decide(_clean_rows(), CAL, CORR, SEAL, _coverage())
    r = d["metrics"]["G1B_moderate"]["rate"]
    assert isinstance(r, float) and (math.isnan(r) or 0.0 <= r <= 1.0)
