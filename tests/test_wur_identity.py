import pandas as pd
import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors, inchi

from muru.io.wur_identity import (
    LADDER_ENERGIES, normalize_collision_energy, snap_to_ladder,
    connectivity_key, verify_identity, infer_adduct,
    build_qualifying_trajectories, accepted_rows,
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


ACETAMINOPHEN = "CC(=O)Nc1ccc(O)cc1"
ACETAMINOPHEN_IK = "RZVAJINKPMORJF-UHFFFAOYSA-N"
ACETAMINOPHEN_MH = 152.070605  # [M+H]+


def _raw_row(**over):
    row = {
        "source_library": "WUR",
        "source_polarity_file": "POS",
        "compound_id": 1,
        "name": "Acetaminophen",
        "formula": "C8H9NO2",
        "smiles": ACETAMINOPHEN,
        "inchikey": ACETAMINOPHEN_IK,
        "spectrum_id": 1,
        "precursor_mass": ACETAMINOPHEN_MH,
        "collision_energy_raw": "15.0",
        "fragmentation_mode": "HCD",
        "polarity": "+",
        "precursor_ion_type": None,
    }
    row.update(over)
    return row


def _raw(rows):
    return pd.DataFrame(rows)


def test_accepted_rows_keeps_one_row_per_accepted_spectrum():
    raw = _raw([_raw_row(spectrum_id=i, collision_energy_raw=f"{e}")
                for i, e in enumerate([15, 30, 45, 60, 75, 90], start=1)])
    acc = accepted_rows(raw, "+")
    assert len(acc) == 6
    assert sorted(acc["energy"]) == [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
    assert set(acc["spectrum_id"]) == {1, 2, 3, 4, 5, 6}


def test_accepted_rows_carries_the_columns_stage1_needs():
    acc = accepted_rows(_raw([_raw_row()]), "+")
    assert set(acc.columns) >= {
        "source_library", "source_polarity_file", "spectrum_id",
        "connectivity_key", "smiles", "adduct", "energy", "precursor_mass",
    }
    assert acc.iloc[0]["connectivity_key"] == "RZVAJINKPMORJF"
    assert acc.iloc[0]["adduct"] == "[M+H]+"


def test_accepted_rows_rejects_uvpd_offladder_and_wrong_polarity():
    raw = _raw([
        _raw_row(spectrum_id=1, fragmentation_mode="UVPD"),
        _raw_row(spectrum_id=2, collision_energy_raw="40.67"),
        _raw_row(spectrum_id=3, collision_energy_raw="25,38,59"),
        _raw_row(spectrum_id=4, polarity="-"),
        _raw_row(spectrum_id=5),
    ])
    acc = accepted_rows(raw, "+")
    assert list(acc["spectrum_id"]) == [5]


def test_accepted_rows_rejects_unexplained_precursor_mass():
    acc = accepted_rows(_raw([_raw_row(precursor_mass=999.9999)]), "+")
    assert len(acc) == 0


def test_accepted_rows_rejects_smiles_contradicting_its_own_inchikey():
    acc = accepted_rows(_raw([_raw_row(smiles="CCO")]), "+")
    assert len(acc) == 0


def test_build_qualifying_trajectories_agrees_with_accepted_rows():
    raw = _raw([_raw_row(spectrum_id=i, collision_energy_raw=f"{e}")
                for i, e in enumerate([15, 30, 45, 60, 75, 90], start=1)])
    traj = build_qualifying_trajectories(raw, "+")
    acc = accepted_rows(raw, "+")
    assert len(traj) == 1
    assert traj.iloc[0]["connectivity_key"] == "RZVAJINKPMORJF"
    assert traj.iloc[0]["n_source_rows"] == len(acc)
