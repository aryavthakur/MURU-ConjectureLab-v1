"""Adversarial tests for the study-2 round-2 review findings (commit 1ecc992 review) and for the checks whose
removal survived the reviewers' extra mutants. Synthetic data only (see decode_fixtures)."""
import copy
import json
import os
import pickle
import subprocess
import sys
import zipfile

import pytest

import decode_fixtures as FX
from muru.wur_v2 import decode_authority as DA
from muru.wur_v2 import external_mzml as X
from muru.wur_v2.decode_authority import AnchorPreflightAuthority, DecodeAuthorityError


@pytest.fixture(autouse=True)
def test_mode(monkeypatch):
    monkeypatch.setenv(DA.TEST_MODE_ENV, "1")


@pytest.fixture
def spy(monkeypatch):
    state = {"n": 0}
    orig = X._decode_array

    def _spy(bda):
        state["n"] += 1
        return orig(bda)

    monkeypatch.setattr(X, "_decode_array", _spy)
    return state


# ------------------------------------------------------------------ N1: verify before publishing, publish once

def test_verify_freeze_candidate_catches_a_slip_before_anything_is_published(tmp_path):
    env = FX.validation_env(tmp_path, publish=False, allow_mz="412.25", pop_mh="412.25")
    with pytest.raises(DecodeAuthorityError, match="live re-read"):
        DA.verify_freeze_candidate(_ov=DA._TestOverrides(FX.v2_overrides(env)))
    with pytest.raises(DecodeAuthorityError):
        DA.publish_freeze(_ov=DA._TestOverrides(FX.v2_overrides(env)))
    assert FX.git(env["repo"], "ls-remote", "origin", DA.FREEZE_REF) == ""
    assert not (env["repo"] / ".git/muru-access-ledger" / f"{DA.STUDY_ID_V2}.freeze.json").exists()


def test_publish_freeze_then_the_look_succeeds_and_a_second_publication_is_refused(tmp_path, spy):
    env = FX.validation_env(tmp_path, publish=False)
    ov = DA._TestOverrides(FX.v2_overrides(env))
    head = DA.publish_freeze(_ov=ov)
    assert FX.git(env["repo"], "ls-remote", "origin", DA.FREEZE_REF).split()[0] == head
    with pytest.raises(DecodeAuthorityError, match="published once|File exists"):
        DA.publish_freeze(_ov=DA._TestOverrides(FX.v2_overrides(env)))
    auth = FX.v2_authority(env)
    assert set(X.decode_selected(FX.member(env), ["v1", "v2"], auth)) == {"v1", "v2"}


def test_failure_after_the_record_exists_is_logged_as_attempt_failed_and_stays_blocked(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    orig = DA._git_text

    def failing_push(root, *args, **kw):
        if args and args[0] == "push" and "--dry-run" not in args:
            raise DecodeAuthorityError("simulated push failure")
        return orig(root, *args, **kw)

    monkeypatch.setattr(DA, "_git_text", failing_push)
    with pytest.raises(DecodeAuthorityError, match="simulated push failure"):
        FX.v2_authority(env)
    log = env["repo"] / ".git/muru-access-ledger" / f"{DA.STUDY_ID_V2}.attempts.jsonl"
    assert json.loads(log.read_text().splitlines()[-1])["status"] == "ATTEMPT_FAILED_NO_DECODE"
    monkeypatch.setattr(DA, "_git_text", orig)
    with pytest.raises(DecodeAuthorityError):
        FX.v2_authority(env)


def test_push_permission_is_probed_before_anything_is_written(tmp_path):
    env = FX.validation_env(tmp_path)
    FX.git(env["repo"], "remote", "set-url", "--push", "origin", str(tmp_path / "nowhere.git"))
    with pytest.raises(DecodeAuthorityError):
        FX.v2_authority(env, canonical_remote=FX.git(env["repo"], "remote", "get-url", "origin"))
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


# ------------------------------------------------------------------ NF-2 canonical remote, N4 exact refs, NF-3 CAS

def test_a_fork_or_repointed_origin_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    with pytest.raises(DecodeAuthorityError, match="not the canonical remote"):
        FX.v2_authority(env, canonical_remote=str(tmp_path / "some_other_origin.git"))
    fork = tmp_path / "fork.git"
    subprocess.run(["git", "clone", "-q", "--bare", FX.git(env["repo"], "remote", "get-url", "origin"), str(fork)],
                   check=True, capture_output=True)
    canonical = FX.git(env["repo"], "remote", "get-url", "origin")
    FX.git(env["repo"], "remote", "set-url", "origin", str(fork))
    with pytest.raises(DecodeAuthorityError, match="not the canonical remote"):
        FX.v2_authority(env, canonical_remote=canonical)


def test_normalize_remote_accepts_ssh_and_https_spellings_of_the_canonical_remote():
    for url in ("git@github.com:aryavthakur/MURU-ConjectureLab-v1.git", "https://github.com/aryavthakur/MURU-ConjectureLab-v1",
                "ssh://git@github.com/aryavthakur/MURU-ConjectureLab-v1.git"):
        assert DA.normalize_remote(url) == DA.CANONICAL_REMOTE
    assert DA.normalize_remote("git@github.com:someone-else/MURU-ConjectureLab-v1.git") != DA.CANONICAL_REMOTE


def test_a_branch_named_like_the_freeze_ref_does_not_satisfy_publication(tmp_path):
    env = FX.validation_env(tmp_path, publish=False)
    head = FX.git(env["repo"], "rev-parse", "HEAD")
    FX.git(env["repo"], "push", "-q", "origin", f"{head}:refs/heads/{DA.FREEZE_REF}")
    reg = env["repo"] / ".git" / "muru-access-ledger" / f"{DA.STUDY_ID_V2}.freeze.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(json.dumps({"freeze_commit": head}))
    with pytest.raises(DecodeAuthorityError, match="must be published"):
        FX.v2_authority(env)


def test_access_ref_push_is_create_only(tmp_path):
    env = FX.validation_env(tmp_path)
    origin = FX.git(env["repo"], "remote", "get-url", "origin")
    head = FX.git(env["repo"], "rev-parse", "HEAD")
    subprocess.run(["git", "--git-dir", origin, "update-ref", DA.ACCESS_REF, head], check=True)
    with pytest.raises(DecodeAuthorityError, match="another clone"):
        FX.v2_authority(env)


# ------------------------------------------------------------------ N2 semantic allowlist checks

@pytest.mark.parametrize("kw,match", [
    (dict(allow_mz="412.2", pop_mh="412.5"), "not within 0.01 Da of the population compound"),
    (dict(pop_wells="pluskal_Z1_id"), "is not plated in well"),
    (dict(row_well="pluskal_Z1_id"), "is not the file's well"),
    (dict(rungs=("60", "60")), "not the frozen fixed rung"),
    (dict(scan_key="KEYZ"), "outside the population"),
])
def test_scan_allowlist_rows_must_be_the_population_compounds_own_fixed_rung_scans(tmp_path, kw, match):
    env = FX.validation_env(tmp_path, **kw)
    with pytest.raises(DecodeAuthorityError, match=match):
        FX.v2_authority(env)


def test_live_header_ms2_and_single_precursor_are_checked_at_construction(tmp_path):
    for i, scans in enumerate(([("v1", 3, 412.2, 20.0), ("v2", 2, 412.2, 60.0)],
                               [("v1", 2, [100.0, 412.2], 20.0), ("v2", 2, 412.2, 60.0)])):
        env = FX.validation_env(tmp_path / f"c{i}", scans=scans)
        with pytest.raises(DecodeAuthorityError, match="live re-read"):
            FX.v2_authority(env)


# ------------------------------------------------------------------ N3 ids and identity

class EqAll(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


def test_non_str_spectrum_ids_are_refused(tmp_path, spy):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    with pytest.raises(X.OutcomeAccessError, match="plain str"):
        X.decode_selected(env["pooled"], [EqAll("s3")], auth)
    assert spy["n"] == 0


def test_is_constructed_is_identity_based_and_authorities_cannot_be_copied(tmp_path):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)

    class Impostor(AnchorPreflightAuthority):
        __slots__ = ()

        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash(auth)

    fake = object.__new__(Impostor)
    assert DA._scope_of(fake) is None
    with pytest.raises(DecodeAuthorityError):
        copy.copy(auth)
    with pytest.raises(DecodeAuthorityError):
        pickle.dumps(auth)


# ------------------------------------------------------------------ N7 test-mode hardening

def test_test_overrides_refuse_real_root_zip_dir_and_ledger(tmp_path, monkeypatch):
    env = FX.anchor_env(tmp_path)
    with pytest.raises(DecodeAuthorityError, match="real repository root"):
        FX.anchor_authority(env, root=DA.ROOT)
    with pytest.raises(DecodeAuthorityError, match="real MSnLib ZIP"):
        DA._for_tests(DA.ConfirmationV2Authority, zip_dir=DA.DEFAULT_ZIP_DIR, root=env["repo"])
    with pytest.raises(DecodeAuthorityError, match="real access ledger"):
        DA._for_tests(DA.ConfirmationV2Authority, ledger_dirs=(DA.DEFAULT_LEDGER_DIR,), root=env["repo"])


def test_test_mode_needs_pytest_and_a_running_test(tmp_path, monkeypatch):
    env = FX.anchor_env(tmp_path)
    monkeypatch.delitem(sys.modules, "pytest")
    with pytest.raises(DecodeAuthorityError, match="only inside a running pytest test"):
        FX.anchor_authority(env)


def test_test_mode_needs_the_current_test_marker(tmp_path, monkeypatch):
    env = FX.anchor_env(tmp_path)
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
    with pytest.raises(DecodeAuthorityError, match="only inside a running pytest test"):
        FX.anchor_authority(env)


# ------------------------------------------------------------------ provenance inside the authorities

def test_both_authorities_check_code_provenance_at_construction(tmp_path):
    code = FX.init_repo(tmp_path / "code", with_origin=False)
    (code / "README").write_text("x\n")
    FX.git(code, "add", "-A")
    FX.git(code, "commit", "-q", "-m", "c")
    env = FX.anchor_env(tmp_path / "a")
    with pytest.raises(DecodeAuthorityError, match=r"outside \S+; refusing|running script has no file"):
        FX.anchor_authority(env, code_root=code)
    venv = FX.validation_env(tmp_path / "v")
    with pytest.raises(DecodeAuthorityError, match=r"outside \S+; refusing|running script has no file"):
        FX.v2_authority(venv, code_root=code)


def test_provenance_refuses_foreign_non_muru_modules_muru_outside_src_and_pyc(tmp_path):
    repo = FX.init_repo(tmp_path / "code", with_origin=False)
    mod = repo / "src/muru/wur_v2/decode_authority.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("# committed\n")
    script = repo / "scripts/run.py"
    script.parent.mkdir()
    script.write_text("# committed\n")
    stray = repo / "muru_misplaced.py"
    stray.write_text("# committed\n")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "c")
    ok = {"muru.wur_v2.decode_authority": str(mod)}
    foreign = tmp_path / "scratch" / "selection_helper.py"
    foreign.parent.mkdir()
    foreign.write_text("x = 1\n")
    with pytest.raises(DecodeAuthorityError, match=r"outside \S+; refusing"):
        DA.check_code_provenance(repo, modules={**ok, "selection_helper": str(foreign)}, main_file=str(script))
    with pytest.raises(DecodeAuthorityError, match=r"outside \S+; refusing"):
        DA.check_code_provenance(repo, modules={**ok, "muru.misplaced": str(stray)}, main_file=str(script))
    pyc = repo / "src/muru/wur_v2/compiled.pyc"
    pyc.write_bytes(b"\x00")
    with pytest.raises(DecodeAuthorityError, match="non-source"):
        DA.check_code_provenance(repo, modules={**ok, "muru.wur_v2.compiled": str(pyc)}, main_file=str(script))
    site_mod = os.path.join(sys.prefix, "lib", "python3", "site-packages", "whatever.py")
    DA.check_code_provenance(repo, modules={**ok, "whatever": site_mod}, main_file=str(script))


# ------------------------------------------------------------------ remaining extra-mutant checks

def test_decode_refused_if_access_record_disappears_after_construction(tmp_path, spy):
    env = FX.validation_env(tmp_path)
    auth = FX.v2_authority(env)
    (env["repo"] / DA.ACCESS_RECORD).unlink()
    with pytest.raises(DecodeAuthorityError, match="access record is missing"):
        X.decode_selected(FX.member(env), ["v1"], auth)
    assert spy["n"] == 0


def test_registry_output_that_no_longer_matches_its_manifest_is_refused(tmp_path):
    env = FX.anchor_env(tmp_path)
    p = env["repo"] / DA.DECODED_SPECTRA
    p.write_text(p.read_text() + "E,pluskal_A1_id.mzML,pluskal_A1_id,s9,300.0,,False\n")
    FX.git(env["repo"], "commit", "-qam", "edit without manifest")
    with pytest.raises(DecodeAuthorityError, match="does not match its manifest"):
        FX.anchor_authority(env)


def test_uncommitted_census_edit_is_refused_by_anchor_authority(tmp_path):
    env = FX.anchor_env(tmp_path)
    (env["repo"] / DA.CENSUS).write_text(json.dumps({"anchors": {"design": {"v2_dev_five_rung": {"keys": ["X"]}}}}))
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        FX.anchor_authority(env)


def test_anchor_row_mz_must_equal_recorded_and_be_the_anchor_mass(tmp_path):
    env = FX.anchor_env(tmp_path, anchor_mh="300.5")
    with pytest.raises(DecodeAuthorityError, match="not the anchor's"):
        FX.anchor_authority(env)
    env2 = FX.anchor_env(tmp_path / "b")
    allow = DA._rows(env2["repo"], DA.ANCHOR_ALLOWLIST)
    allow[0]["selected_ion_mz"] = "300.005"
    FX.write_csv(env2["repo"] / DA.ANCHOR_ALLOWLIST, allow, list(allow[0]))
    FX.git(env2["repo"], "commit", "-qam", "drift")
    with pytest.raises(DecodeAuthorityError, match="differs from the recorded decoded"):
        FX.anchor_authority(env2)


def test_git_calls_ignore_git_environment_variables(tmp_path, monkeypatch):
    repo = FX.init_repo(tmp_path / "a", with_origin=False)
    other = FX.init_repo(tmp_path / "b", with_origin=False)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    assert DA._git_text(repo, "rev-parse", "--show-toplevel") == str(repo.resolve())


def test_push_permission_probe_refuses_before_anything_is_written(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    orig = DA._git_text

    def no_dry_run(root, *args, **kw):
        if args and args[0] == "push" and "--dry-run" in args:
            raise DecodeAuthorityError("simulated: push permission denied")
        return orig(root, *args, **kw)

    monkeypatch.setattr(DA, "_git_text", no_dry_run)
    with pytest.raises(DecodeAuthorityError, match="push permission denied"):
        FX.v2_authority(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_freeze_made_as_a_merge_commit_that_adds_it_is_accepted_once(tmp_path):
    env = FX.validation_env(tmp_path, commit_freeze=False)
    repo = env["repo"]
    FX.git(repo, "stash", "push", "-u", "-q", "-m", "freeze-files-for-evil-merge")
    FX.git(repo, "checkout", "-q", "-b", "side")
    (repo / "SIDE.md").write_text("s\n")
    FX.git(repo, "add", "SIDE.md")
    FX.git(repo, "commit", "-q", "-m", "side")
    FX.git(repo, "checkout", "-q", "main")
    FX.git(repo, "merge", "-q", "--no-ff", "--no-commit", "side")
    FX.git(repo, "stash", "pop", "-q")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "freeze in a merge commit")
    FX.git(repo, "push", "-q", "origin", "main")
    FX.publish_freeze(env)
    assert FX.v2_authority(env).authorized


def test_git_environment_variables_cannot_redirect_the_history_checks(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    pristine = tmp_path / "pristine"
    origin = FX.git(env["repo"], "remote", "get-url", "origin")
    subprocess.run(["git", "clone", "-q", "--branch", "main", origin, str(pristine)], check=True, capture_output=True)
    FX.v2_authority(env)
    monkeypatch.setenv("GIT_DIR", str(pristine / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(pristine))
    with pytest.raises(DecodeAuthorityError):
        FX.v2_authority(env)


def test_repository_hooks_cannot_fail_or_alter_the_record_commit(tmp_path):
    env = FX.validation_env(tmp_path)
    for name in ("pre-commit", "commit-msg", "reference-transaction"):   # reference-transaction is not skipped by --no-verify
        hook = env["repo"] / ".git/hooks" / name
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
    auth = FX.v2_authority(env)
    assert auth.authorized


def test_study_root_must_be_the_git_toplevel(tmp_path):
    env = FX.validation_env(tmp_path)
    with pytest.raises(DecodeAuthorityError, match=r"git toplevel \S+ is not the study root"):
        FX.v2_authority(env, root=env["repo"] / "artifacts")


def test_missing_committer_identity_and_index_lock_are_refused_before_writing(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    (env["repo"] / ".git/index.lock").write_text("")
    with pytest.raises(DecodeAuthorityError, match="index.lock"):
        FX.v2_authority(env)
    (env["repo"] / ".git/index.lock").unlink()
    orig = DA._git_text

    def no_ident(root, *args, **kw):
        if args[:2] == ("var", "GIT_COMMITTER_IDENT"):
            raise DecodeAuthorityError("git var GIT_COMMITTER_IDENT failed: no identity")
        return orig(root, *args, **kw)

    monkeypatch.setattr(DA, "_git_text", no_ident)
    with pytest.raises(DecodeAuthorityError, match="GIT_COMMITTER_IDENT"):
        FX.v2_authority(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_unwritable_ledger_directory_is_refused_before_writing(tmp_path):
    env = FX.validation_env(tmp_path)
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        with pytest.raises(OSError):
            FX.v2_authority(env, ledger_dirs=(locked / "sub",))
    finally:
        locked.chmod(0o700)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_competing_freeze_on_a_deleted_branch_seen_through_the_reflog(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.git(repo, "checkout", "-q", "-b", "alt", "HEAD~1")
    (repo / DA.FREEZE_DOC).write_text("A DIFFERENT FREEZE\n")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "alternative")
    FX.git(repo, "checkout", "-q", "main")
    FX.git(repo, "branch", "-q", "-D", "alt")
    with pytest.raises(DecodeAuthorityError, match="competing freezes"):
        FX.v2_authority(env)


def test_competing_freeze_with_same_doc_but_different_manifest(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.git(repo, "checkout", "-q", "-b", "alt", "HEAD~1")
    FX.git(repo, "checkout", "main", "--", ".")
    m = json.loads((repo / DA.FREEZE_MANIFEST).read_text())
    m["note"] = "a different manifest"
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(m))
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "alt freeze, same doc")
    FX.git(repo, "checkout", "-q", "main")
    with pytest.raises(DecodeAuthorityError, match="competing freezes"):
        FX.v2_authority(env)


def test_allowlisted_file_whose_sha_is_exposed_is_refused_even_in_a_clean_well(tmp_path):
    member_sha = FX.sha(FX.mzml_bytes(FX.VAL))
    env = FX.validation_env(tmp_path, exposed_extra=[{"file": "other.mzML", "file_sha256": member_sha,
                                                      "unique_sample_id": "pluskal_Q1_id", "events": "E"}])
    with pytest.raises(DecodeAuthorityError, match="exposed file or well"):
        FX.v2_authority(env)


@pytest.mark.parametrize("field", ["population_key_hash", "scaffold_group_hash", "spectrum_manifest_hash", "comparator_hash"])
def test_every_recomputed_field_is_checked(tmp_path, field):
    env = FX.validation_env(tmp_path, manifest_tweak=lambda m: m.update({field: "0" * 64}))
    with pytest.raises(DecodeAuthorityError, match=field):
        FX.v2_authority(env)


def test_ignored_data_file_in_the_study_directory_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    (env["repo"] / ".git/info/exclude").write_text(f"{DA.V2_DIR}/freeze/matched_scans.parquet\n")
    (env["repo"] / DA.V2_DIR / "freeze/matched_scans.parquet").write_bytes(b"PAR1")
    with pytest.raises(DecodeAuthorityError, match="ignored files under"):
        FX.v2_authority(env)


def test_freeze_added_by_a_merge_is_counted_once(tmp_path):
    env = FX.validation_env(tmp_path, commit_freeze=False)
    repo = env["repo"]
    FX.git(repo, "checkout", "-q", "-b", "side")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "freeze on side")
    FX.git(repo, "checkout", "-q", "main")
    (repo / "MAIN_ONLY.md").write_text("m\n")
    FX.git(repo, "add", "MAIN_ONLY.md")
    FX.git(repo, "commit", "-q", "-m", "main work")
    FX.git(repo, "merge", "-q", "--no-ff", "-m", "merge freeze", "side")
    FX.git(repo, "push", "-q", "origin", "main")
    FX.publish_freeze(env)
    with pytest.raises(DecodeAuthorityError, match="added exactly once, by HEAD"):
        FX.v2_authority(env)


def test_legacy_reader_accepts_any_indexed_size_for_a_shared_basename(tmp_path, monkeypatch):
    from muru.io import mzml as legacy
    p = FX.write_mzml(tmp_path / "20200303_ENTACT_RP_mix499_pos_CE15.mzML", FX.VAL)
    monkeypatch.setattr(legacy, "_indexed_lcsb_sizes", lambda: {p.name: {p.stat().st_size, p.stat().st_size + 1000}})
    pytest.importorskip("pymzml")
    try:
        next(legacy.iter_ms2(p))
    except legacy.ExternalSourceRefused:
        pytest.fail("an indexed size in the set must be accepted")
    except Exception:
        pass
