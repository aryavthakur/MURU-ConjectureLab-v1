import pandas as pd
import pytest

from muru.io import wur_spectra as WS


def _acc(keys):
    return pd.DataFrame({"connectivity_key": keys, "source_library": "x",
                         "source_polarity_file": "POS", "spectrum_id": range(len(keys)),
                         "energy": 15.0, "precursor_mass": 100.0})


def test_guard_raises_on_a_sealed_key_before_any_blob_is_read(tmp_path):
    with pytest.raises(WS.SealedReadError):
        WS.assert_no_sealed_key(_acc(["A", "SEALED1"]), sealed={"SEALED1"})
    # build_mu_table must refuse before touching data_dir: a nonexistent dir
    # would otherwise raise FileNotFoundError from the reader.
    import muru.io.wur_spectra as mod
    orig = mod.sealed_keys_on_disk
    mod.sealed_keys_on_disk = lambda: {"SEALED1"}
    try:
        with pytest.raises(WS.SealedReadError):
            WS.build_mu_table(_acc(["A", "SEALED1"]), tmp_path / "nope")
        # explicit override is the only way through
        with pytest.raises((FileNotFoundError, KeyError)):   # past the guard, into the reader
            WS.build_mu_table(_acc(["A", "SEALED1"]), tmp_path / "nope", allow_sealed=True)
    finally:
        mod.sealed_keys_on_disk = orig


def test_guard_is_silent_without_sealed_keys():
    WS.assert_no_sealed_key(_acc(["A", "B"]), sealed={"Z"})
    WS.assert_no_sealed_key(_acc(["A", "B"]), sealed=set())


def test_the_real_sealed_list_is_loaded_when_present():
    s = WS.sealed_keys_on_disk()
    assert len(s) == 404
