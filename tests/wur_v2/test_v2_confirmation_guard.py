"""ConfirmationAccessGuard: mutation-detection tests for every process-level weakness the
mandate identified in the base AccessGuard (external_guard.py) before this study's first
validation-outcome access.

Covers: deleted historical record, edited freeze document (even if the edit is itself
committed, so the tree reads clean), different candidate hash, different population hash,
dirty tracked tree, and a second first-look attempt.
"""
import json
import subprocess

import pytest

from muru.wur_v2.confirmation_guard import ConfirmationAccessGuard, ConfirmationGuardError

TEST_STUDY = "test-only-historical-guard-mechanics"
HASHES = dict(actual_candidate_hash="cand-1", actual_comparator_hash="comp-1",
              actual_population_key_hash="pop-1", actual_scaffold_group_hash="scaf-1",
              actual_spectrum_manifest_hash="spec-1")


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "FREEZE.md").write_text("frozen prose\n")
    manifest = {"candidate_hash": "cand-1", "comparator_hash": "comp-1", "population_key_hash": "pop-1",
                "scaffold_group_hash": "scaf-1", "spectrum_manifest_hash": "spec-1"}
    (tmp_path / "FREEZE_MANIFEST.json").write_text(json.dumps(manifest))
    _git(tmp_path, "add", "FREEZE.md", "FREEZE_MANIFEST.json")
    _git(tmp_path, "commit", "-q", "-m", "freeze")
    head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    return tmp_path, head


def _make(root, head, record_name="access/validation.json", **overrides):
    # study 1.0 is VOID (2026-09-13 incident) and refuses construction; the historical mechanics are
    # exercised under a test-only study id
    kwargs = dict(record_path=root / record_name, freeze_doc_path=root / "FREEZE.md",
                  freeze_manifest_path=root / "FREEZE_MANIFEST.json", expected_freeze_commit=head,
                  allowed_spectrum_keys={("a.mzML", "scan=1")}, root=root, study_id=TEST_STUDY)
    kwargs.update(HASHES)
    kwargs.update(overrides)
    return ConfirmationAccessGuard(**kwargs)


def test_first_look_succeeds_and_writes_record_before_decode(tmp_path):
    root, head = _repo(tmp_path)
    g = _make(root, head)
    rec = json.loads((root / "access/validation.json").read_text())
    assert rec["study_id"] == TEST_STUDY
    assert rec["freeze_commit"] == head
    assert rec["decodes"] == []
    assert g.authorized is True


def test_second_first_look_attempt_refused(tmp_path):
    root, head = _repo(tmp_path)
    _make(root, head)
    with pytest.raises(ConfirmationGuardError, match="second look"):
        _make(root, head)


def test_deleted_historical_record_still_refuses_a_new_first_look(tmp_path):
    root, head = _repo(tmp_path)
    _make(root, head)
    # the record itself is never committed by the guard (only written to disk before decode);
    # simulate an operator having committed it at some point, then deleted it, to prove the
    # history check catches a record that existed in git history even if none exists now
    _git(root, "add", "access/validation.json")
    _git(root, "commit", "-q", "-m", "operator commits the access record")
    _git(root, "rm", "-q", "access/validation.json")
    _git(root, "commit", "-q", "-m", "delete record (attempted do-over)")
    assert not (root / "access/validation.json").exists()
    with pytest.raises(ConfirmationGuardError, match="existed in git history"):
        _make(root, head)


def test_edited_freeze_document_refused_even_though_tree_is_clean(tmp_path):
    root, head = _repo(tmp_path)
    # edit AND commit the edit -- tree is clean, doc is "tracked", but content no longer
    # matches the byte-identical version at the pinned freeze commit
    (root / "FREEZE.md").write_text("edited after freeze\n")
    _git(root, "commit", "-am", "quietly edit the freeze doc")
    with pytest.raises(ConfirmationGuardError, match="not byte-identical"):
        _make(root, head)


def test_edited_freeze_manifest_refused(tmp_path):
    root, head = _repo(tmp_path)
    (root / "FREEZE_MANIFEST.json").write_text(json.dumps({"candidate_hash": "cand-1-tampered"}))
    _git(root, "commit", "-am", "tamper with the manifest")
    with pytest.raises(ConfirmationGuardError, match="not byte-identical"):
        _make(root, head)


def test_different_candidate_hash_refused(tmp_path):
    root, head = _repo(tmp_path)
    with pytest.raises(ConfirmationGuardError, match="candidate_hash mismatch"):
        _make(root, head, actual_candidate_hash="cand-DIFFERENT")


def test_different_population_hash_refused(tmp_path):
    root, head = _repo(tmp_path)
    with pytest.raises(ConfirmationGuardError, match="population_key_hash mismatch"):
        _make(root, head, actual_population_key_hash="pop-DIFFERENT")


def test_dirty_tracked_tree_refused(tmp_path):
    root, head = _repo(tmp_path)
    (root / "FREEZE.md").write_text("frozen prose\nan uncommitted extra line")
    with pytest.raises(ConfirmationGuardError, match="not byte-identical|dirty"):
        _make(root, head)


def test_dirty_tree_on_an_unrelated_tracked_file_refused(tmp_path):
    root, head = _repo(tmp_path)
    (root / "FREEZE.md").write_text("frozen prose\n")  # freeze doc itself untouched
    (root / "other_tracked.txt").write_text("x")
    _git(root, "add", "other_tracked.txt")
    _git(root, "commit", "-am", "add another tracked file")
    (root / "other_tracked.txt").write_text("y")  # now dirty, unrelated to the freeze doc
    with pytest.raises(ConfirmationGuardError, match="dirty"):
        _make(root, head, expected_freeze_commit=_git(root, "rev-parse", "HEAD~0").stdout.strip())


def test_head_ahead_of_freeze_with_unallowlisted_change_refused(tmp_path):
    root, head = _repo(tmp_path)
    (root / "scientific_change.py").write_text("x = 1\n")
    _git(root, "add", "scientific_change.py")
    _git(root, "commit", "-q", "-m", "a commit after the freeze")
    with pytest.raises(ConfirmationGuardError, match="not the freeze commit"):
        _make(root, head)


def test_head_ahead_of_freeze_with_allowlisted_change_permitted(tmp_path):
    root, head = _repo(tmp_path)
    (root / "docs_only.md").write_text("typo fix\n")
    _git(root, "add", "docs_only.md")
    _git(root, "commit", "-q", "-m", "outcome-neutral doc fix after freeze")
    g = _make(root, head, code_allowlist={"docs_only.md"})
    assert g.authorized is True


def test_record_decode_refuses_spectra_outside_declared_population(tmp_path):
    root, head = _repo(tmp_path)
    g = _make(root, head)
    g.record_decode(root / "a.mzML", ["scan=1"])
    with pytest.raises(ConfirmationGuardError, match="outside"):
        g.record_decode(root / "a.mzML", ["scan=99"])
