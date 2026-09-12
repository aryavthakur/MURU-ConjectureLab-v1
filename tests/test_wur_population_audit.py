import pandas as pd

from muru.io.wur_population_audit import audit_population

LADDER = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _rows(key, energies, adduct="[M+H]+", library="WUR"):
    return [{"connectivity_key": key, "energy": e, "adduct": adduct,
             "source_library": library, "spectrum_id": i}
            for i, e in enumerate(energies)]


def test_a_clean_single_adduct_single_library_ladder_is_clean():
    acc = pd.DataFrame(_rows("AAAAAAAAAAAAAA", LADDER))
    result = audit_population(acc)
    assert result["n_qualifying_keys"] == 1
    assert result["n_keys_multi_adduct"] == 0
    assert result["n_keys_complete_only_across_adducts"] == 0
    assert result["n_keys_complete_only_across_libraries"] == 0
    assert result["is_clean"] is True


def test_incomplete_ladders_are_not_qualifying_keys():
    acc = pd.DataFrame(_rows("AAAAAAAAAAAAAA", LADDER[:5]))
    assert audit_population(acc)["n_qualifying_keys"] == 0


def test_a_key_with_two_adducts_is_counted_and_named():
    acc = pd.DataFrame(
        _rows("BBBBBBBBBBBBBB", LADDER)
        + _rows("BBBBBBBBBBBBBB", [45.0], adduct="[M+Na]+")
    )
    result = audit_population(acc)
    assert result["n_keys_multi_adduct"] == 1
    assert result["keys_multi_adduct"] == ["BBBBBBBBBBBBBB"]
    assert result["is_clean"] is False


def test_a_ladder_complete_only_by_mixing_adducts_is_counted():
    acc = pd.DataFrame(
        _rows("CCCCCCCCCCCCCC", LADDER[:3])
        + _rows("CCCCCCCCCCCCCC", LADDER[3:], adduct="[M+NH4]+")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_adducts"] == 1
    assert result["keys_complete_only_across_adducts"] == ["CCCCCCCCCCCCCC"]
    assert result["is_clean"] is False


def test_a_ladder_complete_only_by_unioning_libraries_is_counted():
    acc = pd.DataFrame(
        _rows("DDDDDDDDDDDDDD", LADDER[:3], library="WUR")
        + _rows("DDDDDDDDDDDDDD", LADDER[3:], library="FCH")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_libraries"] == 1
    assert result["keys_complete_only_across_libraries"] == ["DDDDDDDDDDDDDD"]
    assert result["is_clean"] is False


def test_one_library_covering_the_ladder_alone_is_clean_even_with_a_second():
    acc = pd.DataFrame(
        _rows("EEEEEEEEEEEEEE", LADDER, library="WUR")
        + _rows("EEEEEEEEEEEEEE", [45.0], library="FCH")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_libraries"] == 0
    assert result["is_clean"] is True
