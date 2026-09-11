import pandas as pd

from muru.io.wur_census import build_census, load_annotated_trajectories


def test_build_census_reports_counts_and_lcsb_overlap():
    traj = pd.DataFrame({
        "connectivity_key": ["K0", "K1", "K2"],
        "scaffold_group": ["g0", "g0", "g1"],
        "source_libraries": [("WUR",), ("WFSR_food_safety",), ("WUR", "FCH")],
        "adduct": ["[M+H]+", "[M+H]+", "[M+Na]+"],
        "in_lcsb_dev": [True, False, False],
        "in_lcsb_sealed": [False, False, True],
    })
    census = build_census({"POS": traj, "NEG": traj.iloc[:0]})
    pos = census["polarities"]["POS"]
    assert pos["n_trajectories"] == 3
    assert pos["n_scaffold_groups"] == 2
    assert pos["n_from_wfsr_food_safety"] == 1
    assert pos["n_in_lcsb_dev"] == 1
    assert pos["n_in_lcsb_sealed"] == 1
    assert census["polarities"]["NEG"]["n_trajectories"] == 0


def test_load_annotated_trajectories_flags_lcsb_membership(tmp_path, monkeypatch):
    import muru.io.wur_census as mod
    from fixtures.wur_db import make_fixture_db, true_inchikey

    # read_all_libraries expects all 10 db files to exist; write one tiny
    # database per (library, polarity_file), empty except where noted.
    for (library, pf), stem in mod.wur_raw.LIBRARY_DB_FILES.items():
        if pf == "POS" and library == "WUR":
            make_fixture_db(tmp_path / f"{stem}.db", [{"smiles": "CCO"}])
        elif pf == "POS" and library == "ETE":
            make_fixture_db(tmp_path / f"{stem}.db", [{"smiles": "c1ccccc1"}])
        else:
            make_fixture_db(tmp_path / f"{stem}.db", [])

    dev_key = true_inchikey("CCO").split("-")[0]
    sealed_key = true_inchikey("c1ccccc1").split("-")[0]
    monkeypatch.setattr(mod, "dev_corpus_keys", lambda: {dev_key})
    monkeypatch.setattr(mod, "sealed_keys", lambda: {sealed_key})

    annotated = load_annotated_trajectories(tmp_path)
    pos = annotated["POS"]
    assert bool(pos.loc[pos["connectivity_key"] == dev_key, "in_lcsb_dev"].iloc[0])
    assert bool(pos.loc[pos["connectivity_key"] == sealed_key, "in_lcsb_sealed"].iloc[0])
    assert "scaffold_group" in pos.columns
