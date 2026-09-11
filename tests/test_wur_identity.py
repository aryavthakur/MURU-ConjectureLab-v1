import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors, inchi

from muru.io.wur_identity import (
    LADDER_ENERGIES, normalize_collision_energy, snap_to_ladder,
    connectivity_key, verify_identity, infer_adduct,
)


def test_normalize_collision_energy_parses_plain_float():
    assert normalize_collision_energy("15.0") == 15.0


def test_normalize_collision_energy_parses_long_decimal():
    assert normalize_collision_energy("15.0000000000000000000000") == 15.0


def test_normalize_collision_energy_rejects_stepped_energy():
    assert normalize_collision_energy("25,38,59") is None


def test_normalize_collision_energy_rejects_garbage():
    assert normalize_collision_energy("not a number") is None


def test_normalize_collision_energy_rejects_none():
    assert normalize_collision_energy(None) is None


@pytest.mark.parametrize("rung", LADDER_ENERGIES)
def test_snap_to_ladder_matches_exact_rung(rung):
    assert snap_to_ladder(rung) == rung


def test_snap_to_ladder_rejects_off_ladder_value():
    assert snap_to_ladder(40.7) is None


def test_connectivity_key_takes_first_block():
    assert connectivity_key("LFQSCWFLJHTTHZ-UHFFFAOYSA-N") == "LFQSCWFLJHTTHZ"


def test_verify_identity_accepts_matching_smiles_and_inchikey():
    smiles = "CCO"
    real_inchikey = inchi.MolToInchiKey(Chem.MolFromSmiles(smiles))
    assert verify_identity(smiles, real_inchikey) is True


def test_verify_identity_rejects_mismatched_inchikey():
    assert verify_identity("CCO", "AAAAAAAAAAAAAA-UHFFFAOYSA-N") is False


def test_verify_identity_rejects_unparseable_smiles():
    assert verify_identity("not a smiles", "AAAAAAAAAAAAAA-UHFFFAOYSA-N") is False


def test_infer_adduct_resolves_mh_plus():
    smiles = "CCO"
    exact_mass = Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles))
    precursor_mass = exact_mass + 1.007276
    assert infer_adduct(smiles, precursor_mass, "+") == "[M+H]+"


def test_infer_adduct_resolves_m_minus_h_negative():
    smiles = "CCO"
    exact_mass = Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles))
    precursor_mass = exact_mass - 1.007276
    assert infer_adduct(smiles, precursor_mass, "-") == "[M-H]-"


def test_infer_adduct_returns_none_when_nothing_matches():
    assert infer_adduct("CCO", 9999.0, "+") is None
