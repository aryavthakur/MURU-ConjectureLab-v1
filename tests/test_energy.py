"""BLOCKER-class tests for collision-energy handling.

A wrong energy assignment or a silent unit coercion corrupts every downstream
number, so these tests are about refusal as much as computation.
"""

from __future__ import annotations

import math

import pytest

from muru.energy import (
    N2_MASS, CollisionEnergy, charge_factor, e_com_direct, e_com_ev, e_lab_ev,
    infer_charge_from_precursor_type, ion_mass, parse_collision_energy,
)


# ---------------------------------------------------------------------------
# Parsing: the record carries a bare integer and MUST NOT gain a unit
# ---------------------------------------------------------------------------
def test_bare_integer_gets_no_unit_and_is_flagged_assumed():
    ce = parse_collision_energy("15")
    assert ce.numeric_value == 15.0
    assert ce.unit is None, "a unit must never be invented"
    assert ce.energy_type == "NCE_ASSUMED_FROM_PUBLICATION"
    assert ce.parse_status == "NO_UNIT_IN_RECORD"
    assert ce.warning is not None


def test_declared_unit_is_preserved_not_overwritten():
    """If a record ever DOES declare a unit, the assumption must not override it."""
    ce = parse_collision_energy("35 eV")
    assert ce.numeric_value == 35.0
    assert ce.unit == "eV"
    assert ce.energy_type == "DECLARED_IN_RECORD"


def test_absent_field_is_absent_not_zero():
    ce = parse_collision_energy(None)
    assert ce.numeric_value is None, "missing energy must never coerce to 0"
    assert ce.parse_status == "ABSENT"


def test_unparseable_value_is_flagged_not_dropped():
    ce = parse_collision_energy("ramp 10-40")
    assert ce.parse_status == "UNPARSEABLE"
    assert ce.numeric_value is None
    assert ce.raw_value == "ramp 10-40", "raw string must survive parsing"


def test_raw_value_always_retained():
    for raw in ["15", "35 eV", "ramp", "  90  "]:
        assert parse_collision_energy(raw).raw_value == raw


# ---------------------------------------------------------------------------
# Charge inference: must never silently default to 1
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("adduct", ["[M+H]+", "[M-H]-", "[M+Na]+", "[M+NH4]+"])
def test_known_singly_charged_adducts(adduct):
    z, prov = infer_charge_from_precursor_type(adduct)
    assert z == 1 and prov


def test_doubly_charged_adduct_detected():
    z, _ = infer_charge_from_precursor_type("[M+2H]2+")
    assert z == 2


def test_unknown_adduct_returns_none_not_one():
    """A silent default of 1 would corrupt E_lab for a multiply charged ion."""
    z, prov = infer_charge_from_precursor_type("something odd")
    assert z is None
    assert "unrecognised" in prov


def test_absent_adduct_returns_none():
    assert infer_charge_from_precursor_type(None)[0] is None


# ---------------------------------------------------------------------------
# Physics
# ---------------------------------------------------------------------------
def test_charge_factor_values():
    assert charge_factor(1) == 1.00
    assert charge_factor(2) == 0.90
    assert charge_factor(3) == 0.85
    assert charge_factor(4) == 0.80
    assert charge_factor(7) == 0.75  # 5+ bucket


def test_charge_factor_rejects_nonphysical():
    with pytest.raises(ValueError):
        charge_factor(0)


def test_e_lab_at_reference_mass_equals_nce():
    """At m/z = 500 and z = 1 the normalization factor is 1, so E_lab == NCE."""
    assert e_lab_ev(50.0, 500.0, 1) == pytest.approx(50.0)


def test_e_lab_hand_calculated():
    """E_lab = 15 * (250/500) * 1 = 7.5 eV."""
    assert e_lab_ev(15.0, 250.0, 1) == pytest.approx(7.5)


def test_e_lab_scales_linearly_in_nce_and_mass():
    assert e_lab_ev(30.0, 300.0) == pytest.approx(2 * e_lab_ev(15.0, 300.0))
    assert e_lab_ev(30.0, 600.0) == pytest.approx(2 * e_lab_ev(30.0, 300.0))


def test_e_com_hand_calculated():
    """E_lab=10, M_ion=272 -> E_com = 10*28/(28+272) = 280/300 = 0.9333..."""
    assert e_com_ev(10.0, 272.0) == pytest.approx(0.9333333333333333, abs=1e-12)


def test_e_com_direct_matches_composed_form():
    """The 0.056*NCE*M/(M+28) shorthand must equal the composed computation."""
    for nce in (15.0, 45.0, 90.0):
        for m in (151.0, 300.0, 526.0):
            composed = e_com_ev(e_lab_ev(nce, m, 1), ion_mass(m, 1))
            assert e_com_direct(nce, m, 1) == pytest.approx(composed, rel=1e-12)
            shorthand = 0.056 * nce * m / (m + N2_MASS)
            assert composed == pytest.approx(shorthand, rel=1e-12)


def test_e_com_is_bounded_by_e_lab():
    """Center-of-mass energy is always a fraction of laboratory-frame energy."""
    e_lab = e_lab_ev(90.0, 500.0)
    assert 0 < e_com_ev(e_lab, 500.0) < e_lab


def test_e_com_near_mass_invariance_claim():
    """Master plan section 6.2 claims E_com spread is under 13% across the
    corpus mass range at fixed NCE. Verified here at both grid ends."""
    for nce in (15.0, 90.0):
        lo = e_com_direct(nce, 151.0)
        hi = e_com_direct(nce, 526.0)
        assert (hi - lo) / hi < 0.13


def test_nonphysical_inputs_rejected():
    with pytest.raises(ValueError):
        e_lab_ev(15.0, 0.0, 1)
    with pytest.raises(ValueError):
        e_com_ev(10.0, -5.0)
