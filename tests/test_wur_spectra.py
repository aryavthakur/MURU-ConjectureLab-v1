import sqlite3

import numpy as np
import pandas as pd
import pytest

from muru.io.wur_spectra import (BlobDefect, build_mu_table, decode_blob,
                                 read_spectrum_peaks, spectrum_mu)


def test_decode_blob_reads_little_endian_float64():
    values = np.array([52.9174027, 121.07587178, 330.19774367])
    assert np.allclose(decode_blob(values.astype("<f8").tobytes()), values)


def test_decode_blob_rejects_a_length_that_is_not_a_multiple_of_eight():
    with pytest.raises(BlobDefect, match="length"):
        decode_blob(b"\x00" * 12)


def test_decode_blob_rejects_an_empty_blob():
    with pytest.raises(BlobDefect, match="empty"):
        decode_blob(b"")


def test_decode_blob_rejects_none():
    with pytest.raises(BlobDefect, match="missing"):
        decode_blob(None)


def _tiny_db(tmp_path, rows):
    """rows: (spectrum_id, mz_array, intensity_array)"""
    path = tmp_path / "tiny.db"
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE SpectrumTable "
                "(SpectrumId INTEGER, blobMass BLOB, blobIntensity BLOB)")
    for sid, mz, inten in rows:
        con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                    (sid, np.asarray(mz, dtype="<f8").tobytes(),
                     np.asarray(inten, dtype="<f8").tobytes()))
    con.commit()
    con.close()
    return path


def test_read_spectrum_peaks_returns_parallel_arrays_by_spectrum_id(tmp_path):
    path = _tiny_db(tmp_path, [
        (1, [100.0, 200.0], [10.0, 20.0]),
        (2, [150.0], [5.0]),
    ])
    peaks = read_spectrum_peaks(path, [1, 2])
    assert np.allclose(peaks[1][0], [100.0, 200.0])
    assert np.allclose(peaks[1][1], [10.0, 20.0])
    assert np.allclose(peaks[2][0], [150.0])


def test_read_spectrum_peaks_only_returns_requested_ids(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0]), (2, [150.0], [5.0])])
    assert set(read_spectrum_peaks(path, [2])) == {2}


def test_read_spectrum_peaks_raises_when_an_id_is_absent(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0])])
    with pytest.raises(BlobDefect, match="absent"):
        read_spectrum_peaks(path, [1, 99])


def test_read_spectrum_peaks_raises_on_mismatched_blob_lengths(tmp_path):
    path = tmp_path / "bad.db"
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE SpectrumTable "
                "(SpectrumId INTEGER, blobMass BLOB, blobIntensity BLOB)")
    con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                (1, np.array([100.0, 200.0], dtype="<f8").tobytes(),
                 np.array([10.0], dtype="<f8").tobytes()))
    con.commit()
    con.close()
    with pytest.raises(BlobDefect, match="mismatch"):
        read_spectrum_peaks(path, [1])


def test_decode_blob_is_little_endian_not_native_agnostic():
    """Big-endian bytes must NOT decode to the same values. On a
    little-endian host a native-endian decoder would pass the
    little-endian test above, so this is what actually pins the dtype."""
    values = np.array([52.9174027, 121.07587178, 330.19774367])
    decoded = decode_blob(values.astype(">f8").tobytes())
    assert not np.allclose(decoded, values)


def test_decode_blob_returns_a_writable_array():
    """The next stage sorts and scales these arrays in place."""
    arr = decode_blob(np.array([1.0, 2.0]).astype("<f8").tobytes())
    arr[0] = 9.0  # must not raise
    assert arr[0] == 9.0


def test_read_spectrum_peaks_returns_empty_for_an_empty_id_list(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0])])
    assert read_spectrum_peaks(path, []) == {}


def test_read_spectrum_peaks_raises_on_a_duplicate_spectrum_id(tmp_path):
    """SpectrumTable has no uniqueness constraint on SpectrumId, so a
    duplicate would otherwise silently win."""
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0]), (1, [200.0], [20.0])])
    with pytest.raises(BlobDefect, match="more than once"):
        read_spectrum_peaks(path, [1])


def test_read_spectrum_peaks_raises_blobdefect_on_a_non_integer_id(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0])])
    with pytest.raises(BlobDefect):
        read_spectrum_peaks(path, ["not-an-id"])


def test_spectrum_mu_is_the_intensity_weighted_normalized_mass():
    # Two peaks of equal intensity at 100 and 200, precursor 200.
    # mu = ((100 + 200) / 2) / 200 = 0.75
    assert spectrum_mu(np.array([100.0, 200.0]),
                       np.array([1.0, 1.0]), 200.0) == pytest.approx(0.75)


def test_spectrum_mu_is_one_for_a_precursor_only_spectrum():
    assert spectrum_mu(np.array([200.0]), np.array([7.0]), 200.0) == pytest.approx(1.0)


def test_spectrum_mu_sorts_unsorted_input_without_changing_the_value():
    unsorted_mu = spectrum_mu(np.array([200.0, 100.0]), np.array([1.0, 3.0]), 200.0)
    sorted_mu = spectrum_mu(np.array([100.0, 200.0]), np.array([3.0, 1.0]), 200.0)
    assert unsorted_mu == pytest.approx(sorted_mu)


def test_spectrum_mu_rejects_a_nonfinite_mass():
    with pytest.raises(BlobDefect, match="nonfinite"):
        spectrum_mu(np.array([100.0, np.nan]), np.array([1.0, 1.0]), 200.0)


def test_spectrum_mu_rejects_a_negative_intensity():
    with pytest.raises(BlobDefect, match="negative"):
        spectrum_mu(np.array([100.0, 200.0]), np.array([1.0, -1.0]), 200.0)


def test_spectrum_mu_rejects_an_unusable_precursor():
    with pytest.raises(BlobDefect, match="precursor"):
        spectrum_mu(np.array([100.0]), np.array([1.0]), 0.0)


def test_spectrum_mu_rejects_zero_total_intensity():
    with pytest.raises(BlobDefect, match="intensity"):
        spectrum_mu(np.array([100.0, 200.0]), np.array([0.0, 0.0]), 200.0)


def _accepted(rows):
    return pd.DataFrame(rows)


def _acc_row(sid, key, energy, library="WUR", precursor=200.0):
    return {"source_library": library, "source_polarity_file": "POS",
            "spectrum_id": sid, "compound_id": 1, "connectivity_key": key,
            "smiles": "CCO", "adduct": "[M+H]+", "energy": energy,
            "precursor_mass": precursor, "polarity": "+"}


def test_build_mu_table_has_one_row_per_key_and_energy(tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [100.0, 200.0], [1.0, 1.0]),
                             (2, [100.0, 200.0], [3.0, 1.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 30.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert census == []
    assert len(table) == 2
    assert set(table["ce_numeric"]) == {15.0, 30.0}
    assert table.set_index("ce_numeric").loc[15.0, "mu"] == pytest.approx(0.75)


def test_build_mu_table_takes_the_median_over_duplicate_spectra(tmp_path, monkeypatch):
    # Three deposits at the same (key, energy): mu = 1.0, 0.75, 0.625.
    # Median is 0.75, mean would be 0.7917.
    db = _tiny_db(tmp_path, [
        (1, [200.0], [1.0]),
        (2, [100.0, 200.0], [1.0, 1.0]),
        (3, [100.0, 200.0], [3.0, 1.0]),
    ])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 15.0),
                     _acc_row(3, "AAA", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert len(table) == 1
    assert table.iloc[0]["mu"] == pytest.approx(0.75)
    assert table.iloc[0]["n_spectra"] == 3


def test_build_mu_table_preserves_contributing_spectrum_ids_and_libraries(
        tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [200.0], [1.0]), (2, [100.0, 200.0], [1.0, 1.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 15.0)])
    table, _ = build_mu_table(acc, tmp_path)
    assert table.iloc[0]["spectrum_ids"] == (("WUR", "POS", 1), ("WUR", "POS", 2))
    assert table.iloc[0]["source_libraries"] == ("WUR",)


def test_build_mu_table_censuses_a_defective_spectrum_rather_than_dropping_it(
        tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [100.0, 200.0], [1.0, 1.0]),
                             (2, [100.0, 200.0], [0.0, 0.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "BBB", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert len(census) == 1
    assert census[0]["connectivity_key"] == "BBB"
    assert census[0]["spectrum_id"] == 2
    assert "intensity" in census[0]["reason"]
    assert set(table["connectivity_key"]) == {"AAA"}


def test_spectrum_mu_rejects_a_non_positive_mz():
    with pytest.raises(BlobDefect, match="non-positive m/z"):
        spectrum_mu(np.array([0.0, 200.0]), np.array([1.0, 1.0]), 200.0)


def test_spectrum_mu_rejects_a_negative_mz():
    with pytest.raises(BlobDefect, match="non-positive m/z"):
        spectrum_mu(np.array([-100.0, 200.0]), np.array([1.0, 1.0]), 200.0)


def test_spectrum_mu_actually_consults_the_preprocessing_cell(monkeypatch):
    """At the base cell `Spectrum.preprocess` is an identity, so a
    hand-rolled formula would pass every other test here. Perturbing the
    cell makes the routing observable: dropping the precursor must change
    the answer."""
    mz = np.array([100.0, 200.0])
    intensity = np.array([1.0, 1.0])
    base = spectrum_mu(mz, intensity, 200.0)
    monkeypatch.setattr(
        "muru.io.wur_spectra.BASE_CELL",
        {"relative_cutoff": 0.0, "include_precursor": False,
         "intensity_transform": "raw"})
    without_precursor = spectrum_mu(mz, intensity, 200.0)
    assert base == pytest.approx(0.75)
    assert without_precursor == pytest.approx(0.5)


def test_spectrum_mu_passes_a_real_sorted_spectrum_to_features_mu(monkeypatch):
    """The preregistration claims both corpora reach `features.mu` through
    the same object. Pin that the object is a Spectrum, that its peaks are
    sorted, and that it carries the declared precursor."""
    from muru.spectra import Spectrum

    seen = {}

    def _spy(spectrum):
        seen["obj"] = spectrum
        return 0.5

    monkeypatch.setattr("muru.io.wur_spectra.feature_mu", _spy)
    spectrum_mu(np.array([200.0, 100.0]), np.array([1.0, 3.0]), 200.0)
    obj = seen["obj"]
    assert isinstance(obj, Spectrum)
    assert list(obj.mz) == [100.0, 200.0]
    assert obj.precursor_mz == 200.0


def test_build_mu_table_median_of_an_even_number_of_duplicates(tmp_path, monkeypatch):
    """Two deposits: mu = 1.0 and 0.5. numpy.median averages them to 0.75,
    a value no single spectrum has. The frozen text names numpy.median, so
    this is the intended convention, pinned here because an even count is
    where the convention is actually a choice."""
    db = _tiny_db(tmp_path, [(1, [200.0], [1.0]), (2, [100.0, 200.0], [1.0, 0.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert census == []
    assert table.iloc[0]["n_spectra"] == 2
    assert table.iloc[0]["mu"] == pytest.approx(0.75)


def test_build_mu_table_censuses_a_mis_sized_blob_instead_of_aborting(
        tmp_path, monkeypatch):
    """A corrupt blob is a property of one spectrum. It must be reported per
    spectrum, not abort the read and hide the state of every other."""
    path = tmp_path / "mixed.db"
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE SpectrumTable "
                "(SpectrumId INTEGER, blobMass BLOB, blobIntensity BLOB)")
    con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                (1, np.array([100.0, 200.0], dtype="<f8").tobytes(),
                 np.array([1.0, 1.0], dtype="<f8").tobytes()))
    con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                (2, np.array([100.0, 200.0], dtype="<f8").tobytes(),
                 np.array([1.0], dtype="<f8").tobytes()))
    con.commit()
    con.close()
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): path.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "BBB", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert len(census) == 1
    assert census[0]["spectrum_id"] == 2
    assert census[0]["connectivity_key"] == "BBB"
    assert "mismatch" in census[0]["reason"]
    assert set(table["connectivity_key"]) == {"AAA"}
