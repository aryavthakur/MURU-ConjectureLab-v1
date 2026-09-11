from muru.io.wur_raw import LIBRARY_DB_FILES, RAW_COLUMNS, read_mzvault_db
from fixtures.wur_db import make_fixture_db


def test_read_mzvault_db_returns_one_row_per_spectrum(tmp_path):
    db_path = tmp_path / "fixture.db"
    make_fixture_db(db_path, [
        {"smiles": "CCO", "name": "ethanol"},
        {"smiles": "c1ccccc1", "name": "benzene", "energies": ["15.0", "30.0"]},
    ])
    df = read_mzvault_db(db_path, "WUR", "POS")
    assert list(df.columns) == RAW_COLUMNS
    assert len(df) == 6 + 2
    assert set(df["source_library"]) == {"WUR"}
    assert set(df["source_polarity_file"]) == {"POS"}


def test_library_db_files_covers_five_libraries_and_two_polarities():
    libraries = {lib for lib, _ in LIBRARY_DB_FILES}
    polarities = {pf for _, pf in LIBRARY_DB_FILES}
    assert libraries == {"ETE", "FCH", "WFSR_Polar", "WFSR_food_safety", "WUR"}
    assert polarities == {"POS", "NEG"}
    assert len(LIBRARY_DB_FILES) == 10
