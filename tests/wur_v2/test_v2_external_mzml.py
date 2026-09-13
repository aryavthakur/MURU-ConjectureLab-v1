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
    """Since the 2026-09-13 incident a duck-typed guard like `Guard` (the pattern that burned confirmation
    sample 1) is refused; decoding needs an exact-type decode authority. Decode mechanics are unchanged."""
    import csv
    import hashlib
    import subprocess

    from muru.wur_v2 import decode_authority as DA

    p = _mzml(tmp_path)
    with pytest.raises(X.OutcomeAccessError):
        X.decode_selected(p, ["scan=2"], None)
    with pytest.raises(X.OutcomeAccessError):
        X.decode_selected(p, ["scan=2"], Guard())

    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=repo, check=True)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    for rel, row in ((DA.ANCHOR_ALLOWLIST, {"file": p.name, "file_sha256": digest, "unique_sample_id": "u",
                                            "anchor_key": "K", "anchor_mh": "301.1410"}),
                     (DA.EXPOSED_FILES, {"file": p.name, "file_sha256": digest, "unique_sample_id": "u", "events": "E"})):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        with open(repo / rel, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            w.writeheader()
            w.writerow(row)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "allowlist"], cwd=repo, check=True)
    g = DA.AnchorPreflightAuthority(log_path=tmp_path / "log.jsonl", root=repo, code_root=None)
    out = X.decode_selected(p, ["scan=2"], g)
    assert set(out) == {"scan=2"}
    mz, inten = out["scan=2"]
    assert np.allclose(mz, [50.0, 99.1, 301.14]) and np.allclose(inten, [10.0, 50.0, 40.0])
    with pytest.raises(DA.DecodeAuthorityError):
        X.decode_selected(p, ["scan=3"], g)                  # precursor 455.29 is not the allowlisted anchor


def test_numpress_pic_roundtrip_and_reference_vectors():
    vals = [0, 1, 7, 15, 16, 255, 4096, 123456, 2 ** 31 - 1, 3.4, 99.6]
    enc = X.numpress_pic_encode(vals)
    dec = X.numpress_pic_decode(enc)
    assert list(dec) == [0, 1, 7, 15, 16, 255, 4096, 123456, 2 ** 31 - 1, 3, 100]
    # hand-checked vectors: 1 -> head 7 then nybble 1 -> 0x71; 0 -> head 8 then a 0x0 pad -> 0x80;
    # two zeros -> 0x88 with the final lone 0x8 decoded as a value, not dropped as padding
    assert X.numpress_pic_encode([1]) == bytes([0x71])
    assert X.numpress_pic_encode([0]) == bytes([0x80])
    assert list(X.numpress_pic_decode(bytes([0x80]))) == [0.0]
    assert list(X.numpress_pic_decode(bytes([0x88]))) == [0.0, 0.0]
    for vals2 in ([0, 0], [1, 0], [0, 1, 0], [2 ** 32 - 5, 0]):
        assert list(X.numpress_pic_decode(X.numpress_pic_encode(vals2))) == vals2


def test_numpress_pic_matches_pymzml_encoder():
    pytest.importorskip("pymzml")
    from pymzml.ms_numpress import MSNumpress
    vals = [3, 250, 9000, 70000, 12, 0, 5]
    m = MSNumpress(list(map(float, vals)))
    enc = m.encode_pic()
    assert list(X.numpress_pic_decode(bytes(enc))) == vals
