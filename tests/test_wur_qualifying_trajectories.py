import pandas as pd

from muru.io.wur_identity import build_qualifying_trajectories
from muru.io.wur_raw import read_mzvault_db
from fixtures.wur_db import make_fixture_db, true_inchikey


def _raw(tmp_path, compounds, library="WUR", polarity_file="POS", name="fixture.db"):
    db_path = tmp_path / name
    make_fixture_db(db_path, compounds)
    return read_mzvault_db(db_path, library, polarity_file)


def test_full_ladder_hcd_compound_qualifies(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "name": "ethanol"}])
    traj = build_qualifying_trajectories(raw, "+")
    assert len(traj) == 1
    assert traj.iloc[0]["adduct"] == "[M+H]+"
    assert traj.iloc[0]["connectivity_key"] == connectivity_key_of("CCO")


def connectivity_key_of(smiles: str) -> str:
    return true_inchikey(smiles).split("-")[0]


def test_incomplete_ladder_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "energies": ["15.0", "30.0", "45.0"]}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_stepped_energy_row_is_dropped_but_full_ladder_still_qualifies(tmp_path):
    raw = _raw(tmp_path, [{
        "smiles": "CCO",
        "energies": ["15.0", "30.0", "45.0", "60.0", "75.0", "90.0", "25,38,59"],
    }])
    assert len(build_qualifying_trajectories(raw, "+")) == 1


def test_identity_mismatch_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "inchikey": "AAAAAAAAAAAAAA-UHFFFAOYSA-N"}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_unresolved_adduct_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "precursor_mass": 9999.0}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_wrong_polarity_row_is_excluded_from_positive_population(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "polarity": "-"}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_same_compound_across_two_libraries_merges_into_one_trajectory(tmp_path):
    raw_a = _raw(tmp_path, [{"smiles": "CCO"}], library="WUR", name="a.db")
    raw_b = _raw(tmp_path, [{"smiles": "CCO"}], library="WFSR_food_safety", name="b.db")
    raw = pd.concat([raw_a, raw_b], ignore_index=True)
    traj = build_qualifying_trajectories(raw, "+")
    assert len(traj) == 1
    assert set(traj.iloc[0]["source_libraries"]) == {"WUR", "WFSR_food_safety"}
    assert traj.iloc[0]["n_source_rows"] == 12


def test_picks_lexicographically_first_smiles_across_duplicate_deposits(tmp_path):
    ik = true_inchikey("CCO")
    raw_a = _raw(tmp_path, [{"smiles": "OCC", "inchikey": ik}], library="WUR", name="a.db")
    raw_b = _raw(tmp_path, [{"smiles": "CCO", "inchikey": ik}], library="WFSR_food_safety", name="b.db")
    raw = pd.concat([raw_a, raw_b], ignore_index=True)
    traj = build_qualifying_trajectories(raw, "+")
    assert traj.iloc[0]["smiles"] == min("OCC", "CCO")
