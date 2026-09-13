"""Anchor preflight scopes exclude any anchor whose precursor isolation a co-plated compound could share
(red-team finding F09: SEL_TOL = 0.01 Da alone admits isomers and near-isobars)."""
from muru.wur_v2.anchor_scope import PROTON, admissible_anchor_scopes


def row(key, mh, formula, charge=0, m_plus=float("nan")):
    return {"key": key, "mh": mh, "parent_formula": formula, "parent_charge": charge, "m_plus": m_plus}


def test_clean_well_admits_the_anchor():
    well = [row("ANCHOR", 300.0, "C1"), row("OTHER", 450.0, "C2")]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert [a["key"] for a in admitted] == ["ANCHOR"] and not rejected


def test_isomer_at_zero_mass_difference_is_rejected():
    well = [row("ANCHOR", 300.0, "C10H12N2O"), row("ISOMER", 300.0, "C10H12N2O")]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "isomer" in rejected[0]["reason"]


def test_near_isobar_0005_da_away_is_rejected():
    well = [row("ANCHOR", 300.0, "C1"), row("NEAR", 300.005, "C2")]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "NEAR" in rejected[0]["reason"]


def test_sodium_adduct_of_a_lighter_coplated_compound_within_iso_tol_is_rejected():
    m_other = 300.0 - 22.989218 + 0.3            # its [M+Na]+ lands 0.3 Da from the anchor [M+H]+
    well = [row("ANCHOR", 300.0, "C1"), row("LIGHT", m_other + PROTON, "C2")]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "LIGHT" in rejected[0]["reason"]


def test_permanent_cation_within_iso_tol_is_rejected():
    well = [row("ANCHOR", 300.0, "C1"), row("QUAT", float("nan"), "C3", charge=1, m_plus=300.4)]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "QUAT" in rejected[0]["reason"]


def test_unknown_identity_in_well_blocks_all_anchors():
    well = [row("ANCHOR", 300.0, "C1"), {"key": None, "mh": float("nan"), "parent_formula": None, "parent_charge": None}]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "unknown identity" in rejected[0]["reason"]


def test_non_anchor_rows_are_never_admitted():
    well = [row("A", 300.0, "C1"), row("B", 500.0, "C2")]
    admitted, _ = admissible_anchor_scopes(well, set())
    assert admitted == []


def test_multiply_charged_and_in_source_forms_are_modelled():
    """REG-1: real carryover spectra were triggered on [M+2H]2+, [M+3H]3+ and [M+H-NH3]+ ions."""
    from muru.wur_v2.anchor_scope import ION_FORMS, ion_mzs
    m = 700.0
    mzs = dict(zip(ION_FORMS, ion_mzs(0, m + PROTON, float("nan"))))
    assert abs(mzs["[M+2H]2+"] - (m + 2 * PROTON) / 2) < 1e-9
    assert abs(mzs["[M+3H]3+"] - (m + 3 * PROTON) / 3) < 1e-9
    assert abs(mzs["[M+H-NH3]+"] - (m + PROTON - 17.026549)) < 1e-9
    assert ion_mzs(2, float("nan"), 500.0) == [250.0]            # a dication contributes M+/z


def test_doubly_charged_coplated_ion_blocks_an_anchor():
    heavy = 2 * (300.0 - 0.2) - 2 * PROTON                        # its [M+2H]2+ sits 0.2 Da from the anchor
    well = [row("ANCHOR", 300.0, "C1"), row("HEAVY", heavy + PROTON, "C9")]
    admitted, rejected = admissible_anchor_scopes(well, {"ANCHOR"})
    assert not admitted and "HEAVY" in rejected[0]["reason"]
