"""The external mzML reader returns allowlisted headers only, never intensity summaries,
and refuses to decode peaks without an authorizing guard."""
import base64
import zlib

import numpy as np
import pytest

from muru.wur_v2 import external_mzml as X


def _array(values, acc_kind, compress, bits64=True):
    raw = np.asarray(values, "<f8" if bits64 else "<f4").tobytes()
    if compress:
        raw = zlib.compress(raw)
    cvs = [f'<cvParam accession="{"MS:1000523" if bits64 else "MS:1000521"}" name="float"/>', f'<cvParam accession="{acc_kind}" name="arr"/>']
    if compress:
        cvs.append('<cvParam accession="MS:1000574" name="zlib compression"/>')
    return (f'<binaryDataArray encodedLength="0">{"".join(cvs)}<binary>{base64.b64encode(raw).decode()}</binary></binaryDataArray>')


def _mzml(tmp_path):
    specs = []
    for i, (lvl, prec, ce) in enumerate([(1, None, None), (2, 301.1410, 20.0), (2, 455.2900, 40.0)]):
        prec_xml = ""
        if prec:
            prec_xml = (f'<precursorList count="1"><precursor><isolationWindow><cvParam accession="MS:1000827" name="t" value="{prec}"/></isolationWindow>'
                        f'<selectedIonList count="1"><selectedIon><cvParam accession="MS:1000744" name="sel" value="{prec}"/>'
                        f'<cvParam accession="MS:1000041" name="z" value="1"/></selectedIon></selectedIonList>'
                        f'<activation><cvParam accession="MS:1000133" name="CID"/><cvParam accession="MS:1000045" name="ce" value="{ce}"/></activation></precursor></precursorList>')
        specs.append(
            f'<spectrum index="{i}" id="scan={i + 1}" defaultArrayLength="3">'
            f'<cvParam accession="MS:1000511" name="ms level" value="{lvl}"/>'
            f'<cvParam accession="MS:1000285" name="total ion current" value="12345"/>'
            f'<cvParam accession="MS:1000504" name="base peak m/z" value="99.1"/>'
            f'<cvParam accession="MS:1000527" name="highest observed m/z" value="301.14"/>'
            f'<scanList count="1"><scan><cvParam accession="MS:1000016" name="t" value="0.{i}"/>'
            f'<scanWindowList count="1"><scanWindow><cvParam accession="MS:1000501" name="lo" value="40"/><cvParam accession="MS:1000500" name="hi" value="1000"/></scanWindow></scanWindowList></scan></scanList>'
            f'{prec_xml}<binaryDataArrayList count="2">{_array([50.0, 99.1, 301.14], "MS:1000514", i % 2 == 0)}{_array([10.0, 50.0, 40.0], "MS:1000515", i % 2 == 0, bits64=False)}</binaryDataArrayList></spectrum>')
    text = ('<?xml version="1.0" encoding="utf-8"?><mzML xmlns="http://psi.hupo.org/ms/mzml"><run><spectrumList count="3">'
            + "".join(specs) + "</spectrumList></run></mzML>")
    p = tmp_path / "t.mzML"
    p.write_text(text)
    return p


class Guard:
    authorized = True

    def __init__(self):
        self.log = []

    def record_decode(self, path, ids):
        self.log.append((str(path), ids))


def test_headers_allowlisted_and_no_outcome_summaries(tmp_path):
    rows = X.scan_headers(_mzml(tmp_path))
    assert [r["ms_level"] for r in rows] == [1.0, 2.0, 2.0]
    assert rows[1]["selected_ion_mz"] == pytest.approx(301.1410) and rows[2]["collision_energy"] == 40.0
    assert rows[1]["scan_window_lower_limit"] == 40.0
    for r in rows:
        for banned in ("total ion current", "base peak m/z", "highest observed m/z", "total_ion_current"):
            assert banned not in r
        assert not any("intensity" in k or "base_peak" in k or "observed" in k for k in r)


def test_decode_requires_guard_and_returns_only_selected(tmp_path):
    p = _mzml(tmp_path)
    with pytest.raises(X.OutcomeAccessError):
        X.decode_selected(p, ["scan=2"], None)
    g = Guard()
    out = X.decode_selected(p, ["scan=2"], g)
    assert set(out) == {"scan=2"}
    mz, inten = out["scan=2"]
    assert np.allclose(mz, [50.0, 99.1, 301.14]) and np.allclose(inten, [10.0, 50.0, 40.0])
    assert g.log == [(str(p), ["scan=2"])]
