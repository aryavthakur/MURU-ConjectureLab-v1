import hashlib

import pytest

from muru.io.wur_retrieval import build_manifest, EXPECTED_FILES


def test_build_manifest_detects_missing_files(tmp_path):
    manifest = build_manifest(tmp_path)
    assert set(manifest["missing"]) == set(EXPECTED_FILES)
    assert manifest["n_files"] == 0


def test_build_manifest_detects_hash_mismatch(tmp_path, monkeypatch):
    import muru.io.wur_retrieval as mod
    monkeypatch.setattr(mod, "EXPECTED_FILES", {"fake.db": "0" * 64})
    (tmp_path / "fake.db").write_bytes(b"wrong bytes")
    manifest = mod.build_manifest(tmp_path)
    assert manifest["hash_mismatches"] == ["fake.db"]


def test_build_manifest_passes_when_bytes_match(tmp_path, monkeypatch):
    import muru.io.wur_retrieval as mod
    content = b"exact frozen bytes for this one file"
    expected_hash = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(mod, "EXPECTED_FILES", {"fake.db": expected_hash})
    (tmp_path / "fake.db").write_bytes(content)
    manifest = mod.build_manifest(tmp_path)
    assert manifest["missing"] == []
    assert manifest["hash_mismatches"] == []
    assert manifest["files"][0]["sha256"] == expected_hash


def test_expected_files_covers_ten_msp_and_ten_db():
    dbs = [n for n in EXPECTED_FILES if n.endswith(".db")]
    msps = [n for n in EXPECTED_FILES if n.endswith(".msp")]
    assert len(dbs) == 10
    assert len(msps) == 10
