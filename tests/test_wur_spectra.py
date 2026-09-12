import sqlite3

import numpy as np
import pytest

from muru.io.wur_spectra import BlobDefect, decode_blob, read_spectrum_peaks


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
