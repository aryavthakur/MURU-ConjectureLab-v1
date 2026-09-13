"""Adversarial tests for the study-2 decode boundary (muru.wur_v2.decode_authority + external_mzml.decode_selected).

Every test attempts one concrete way premature or out-of-scope decoding could happen and asserts it is refused
AND that not a single binary array was decoded (a spy on external_mzml._decode_array counts calls). All data are
synthetic: tiny mzML bytes, ZIP members and throwaway git repositories with a bare origin under tmp_path.

Requirement map (MSnLib confirmation study 2 mandate, section 3), plus the pre-sampling review findings they close:
  R1 anchor preflight only decodes scans whose precursor matches the explicit anchor allowlist (F-03, F-04, F-14)
  R2 co-plated non-anchor scans cannot be selected by position
  R3 no validation decode without a committed final freeze (F-01, F-06, F-A, F-B, F-15)
  R4 every requested validation scan is in the frozen scan allowlist (F-10, F-H)
  R5 a historical access record blocks a second first look even if deleted (F-02, F-E, F-D)
  R6 hashes recomputed live (F-05, F-F, F-13)
  R7 freeze bytes bound to the freeze commit (F-12)
  R8 the access record is written, committed and pushed before any validation array is decoded
"""
import json
import shutil
import subprocess
import zipfile

import pytest

import decode_fixtures as FX
from muru.wur_v2 import decode_authority as DA
from muru.wur_v2 import external_mzml as X
from muru.wur_v2.decode_authority import AnchorPreflightAuthority, ConfirmationV2Authority, DecodeAuthorityError


@pytest.fixture(autouse=True)
def test_mode(monkeypatch):
    monkeypatch.setenv(DA.TEST_MODE_ENV, "1")


@pytest.fixture
def spy(monkeypatch):
    state = {"n": 0, "before": None}
    orig = X._decode_array

    def _spy(bda):
        if state["before"] is not None:
            state["before"]()
        state["n"] += 1
        return orig(bda)

    monkeypatch.setattr(X, "_decode_array", _spy)
    return state


# ======================================================================================= anchor preflight

def test_R2_positional_selection_in_pooled_well_is_refused_before_any_decode(tmp_path, spy):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    ids = [r["spectrum_id"] for r in X.scan_headers(env["pooled"]) if r.get("ms_level") == 2.0][:6]
    assert ids[:2] == ["s1", "s2"]
    with pytest.raises(DecodeAuthorityError, match="not in this authority's allowlist"):
        X.decode_selected(env["pooled"], ids, auth)
    assert spy["n"] == 0


def test_R1_anchor_re_decode_succeeds_and_is_logged(tmp_path, spy):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    out = X.decode_selected(env["pooled"], ["s3", "s4"], auth)
    assert set(out) == {"s3", "s4"} and spy["n"] == 4
    log = [json.loads(line) for line in env["log"].read_text().splitlines()]
    assert log[-1]["event"] == "authorize" and set(log[-1]["spectra"]) == {"s3", "s4"}


def test_R1_allowlist_scan_never_decoded_before_is_refused_at_construction(tmp_path):
    scans = FX.POOLED + [("s5", 2, 300.0, 20.0)]
    env = FX.anchor_env(tmp_path, pooled_scans=scans, extra_allow=[{
        "file": "pluskal_A1_id.mzML", "file_sha256": FX.sha(FX.mzml_bytes(scans)), "spectrum_id": "s5",
        "selected_ion_mz": "300.0", "anchor_key": "ANCHORKEY", "anchor_mh": "300.0"}])
    rows = [r for r in DA._rows(env["repo"], DA.DECODED_SPECTRA) if r["spectrum_id"] != "s5"]
    env["registry_sha"] = FX.write_registry(env["repo"], DA._rows(env["repo"], DA.EXPOSED_FILES), rows)
    FX.git(env["repo"], "commit", "-qam", "s5 was never decoded")
    with pytest.raises(DecodeAuthorityError, match="never decoded before"):
        FX.anchor_authority(env)


def test_R1_nan_anchor_mh_is_refused_at_construction(tmp_path):
    env = FX.anchor_env(tmp_path, anchor_mh="nan")
    with pytest.raises(DecodeAuthorityError, match="non-finite"):
        FX.anchor_authority(env)


def test_R1_non_anchor_key_is_refused_at_construction(tmp_path):
    env = FX.anchor_env(tmp_path, anchor_key="NOTANANCHOR")
    with pytest.raises(DecodeAuthorityError, match="non-anchor key"):
        FX.anchor_authority(env)


def test_R1_allowlisted_file_absent_from_exposed_files_is_refused(tmp_path):
    env = FX.anchor_env(tmp_path)
    rows = DA._rows(env["repo"], DA.EXPOSED_FILES)
    rows[0]["file_sha256"] = "0" * 64
    env["registry_sha"] = FX.write_registry(env["repo"], rows, DA._rows(env["repo"], DA.DECODED_SPECTRA))
    FX.git(env["repo"], "commit", "-qam", "registry no longer lists that content")
    with pytest.raises(DecodeAuthorityError, match="not an exposed file"):
        FX.anchor_authority(env)


def test_R1_registry_manifest_not_the_pinned_one_is_refused(tmp_path):
    env = FX.anchor_env(tmp_path)
    with pytest.raises(DecodeAuthorityError, match="not the one this code is bound to"):
        FX.anchor_authority(env, registry_manifest_sha256="f" * 64)


def test_R1_uncommitted_allowlist_widening_is_refused(tmp_path):
    env = FX.anchor_env(tmp_path)
    p = env["repo"] / DA.ANCHOR_ALLOWLIST
    p.write_text(p.read_text() + f"{env['other'].name},{FX.sha(env['other'])},t1,300.0,ANCHORKEY,300.0\n")
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        FX.anchor_authority(env)


def test_R1_file_not_on_allowlist_and_renamed_validation_file_are_refused(tmp_path, spy):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError, match="not in this authority's allowlist"):
        X.decode_selected(env["other"], ["t1"], auth)
    impostor = FX.write_mzml(tmp_path / "impostor" / env["pooled"].name, FX.POOLED, marker=3.0)
    with pytest.raises(DecodeAuthorityError, match="substituted file"):
        X.decode_selected(impostor, ["s3"], auth)
    assert spy["n"] == 0


def test_R1_spectrum_with_two_selected_ions_is_refused(tmp_path, spy):
    plain = [("s0", 1, None, None), ("s3", 2, 300.0, 20.0), ("s4", 2, 300.0, 60.0)]
    chimeric = [("s0", 1, None, None), ("s3", 2, [500.0, 300.0], 20.0), ("s4", 2, 300.0, 60.0)]
    env = FX.anchor_env(tmp_path, pooled_scans=plain)
    FX.write_mzml(env["pooled"], chimeric)
    rows = DA._rows(env["repo"], DA.EXPOSED_FILES)
    rows[0]["file_sha256"] = FX.sha(env["pooled"])
    env["registry_sha"] = FX.write_registry(env["repo"], rows, DA._rows(env["repo"], DA.DECODED_SPECTRA))
    allow = DA._rows(env["repo"], DA.ANCHOR_ALLOWLIST)
    for r in allow:
        r["file_sha256"] = FX.sha(env["pooled"])
    FX.write_csv(env["repo"] / DA.ANCHOR_ALLOWLIST, allow, list(allow[0]))
    FX.git(env["repo"], "commit", "-qam", "chimeric precursor list")
    auth = FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError, match="exactly one required"):
        X.decode_selected(env["pooled"], ["s3"], auth)
    assert spy["n"] == 0


def test_R1_msn_scan_on_the_allowlist_is_refused(tmp_path, spy):
    scans = [("s0", 1, None, None), ("s3", 3, 300.0, 40.0), ("s4", 2, 300.0, 60.0)]
    env = FX.anchor_env(tmp_path, pooled_scans=scans)
    auth = FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError, match="not an MS2 scan"):
        X.decode_selected(env["pooled"], ["s3"], auth)
    assert spy["n"] == 0


# ======================================================================================= decoder gate

class DuckGuard:
    authorized = True

    def authorize(self, *a):
        pass


def test_R3_duck_legacy_void_subclass_and_new_objects_are_refused(tmp_path, spy):
    from muru.wur_v2.confirmation_guard import ConfirmationAccessGuard
    from muru.wur_v2.external_guard import AccessGuard
    env = FX.anchor_env(tmp_path)
    real = FX.anchor_authority(env)

    class Sub(AnchorPreflightAuthority):
        __slots__ = ()

    guards = [DuckGuard(), object.__new__(AccessGuard), object.__new__(ConfirmationAccessGuard),
              object.__new__(AnchorPreflightAuthority), object.__new__(Sub)]
    for g in guards:
        with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
            X.decode_selected(env["pooled"], ["s3"], g)
    assert real.authorized is True and spy["n"] == 0


def test_R3_constructed_authority_cannot_be_mutated_or_given_new_scope(tmp_path, spy):
    """F-01/F-B: scope lives in module-private immutable state, not on the object."""
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError):
        auth.files = {}
    with pytest.raises(DecodeAuthorityError):
        auth.authorize = lambda *a: None
    with pytest.raises(TypeError):
        vars(auth)
    sc = DA._SCOPES[auth]
    with pytest.raises(TypeError):
        sc.files[env["other"].name] = (FX.sha(env["other"]), {"t1": 300.0})
    with pytest.raises(TypeError):
        sc.files[env["pooled"].name][1]["s1"] = 500.0
    with pytest.raises(DecodeAuthorityError, match="not in this authority's allowlist"):
        X.decode_selected(env["other"], ["t1"], auth)
    assert spy["n"] == 0


def test_R3_scope_digest_mismatch_is_refused(tmp_path, spy, monkeypatch):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    sc = DA._SCOPES[auth]
    monkeypatch.setitem(DA._SCOPES, auth, DA._Scope(sc.kind, sc.files, sc.log_path, sc.root, sc.code_root,
                                                     sc.ledger_paths, "0" * 64))
    with pytest.raises(DecodeAuthorityError, match="digest changed"):
        X.decode_selected(env["pooled"], ["s3"], auth)
    assert spy["n"] == 0


def test_R3_decode_primitive_refuses_outside_decode_selected():
    """F-A: importing _decode_array does not let anyone decode an array."""
    for spec in X._iter_spectra(FX.mzml_bytes(FX.POOLED)):
        bda = spec.find(f"{X.NS}binaryDataArrayList/{X.NS}binaryDataArray")
        with pytest.raises(X.OutcomeAccessError, match="only be decoded inside decode_selected"):
            X._decode_array(bda)
        break


def test_R3_overrides_require_test_mode(tmp_path, monkeypatch):
    """F-06: location overrides are unavailable to ordinary code."""
    env = FX.anchor_env(tmp_path)
    monkeypatch.delenv(DA.TEST_MODE_ENV)
    with pytest.raises(DecodeAuthorityError, match="only under pytest"):
        FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError, match="only in test mode"):
        AnchorPreflightAuthority(log_path=env["log"], _ov=DA._TestOverrides({"root": env["repo"], "code_root": None}))
    with pytest.raises(TypeError):
        AnchorPreflightAuthority(log_path=env["log"], root=env["repo"])
    with pytest.raises(TypeError):
        ConfirmationV2Authority(ledger_dir=tmp_path)


def test_R4_bytes_are_read_once_so_a_file_swapped_after_authorization_is_not_what_gets_decoded(tmp_path, monkeypatch):
    env = FX.anchor_env(tmp_path)
    auth = FX.anchor_authority(env)
    orig = DA.authorize_decode

    def authorize_then_swap(*a):
        orig(*a)
        FX.write_mzml(env["pooled"], FX.POOLED, marker=900.0)

    monkeypatch.setattr(DA, "authorize_decode", authorize_then_swap)
    out = X.decode_selected(env["pooled"], ["s3"], auth)
    assert out["s3"][0][0] < 100.0


def test_R3_code_provenance_refuses_shadowed_modified_untracked_and_fileless_scripts(tmp_path):
    repo = FX.init_repo(tmp_path / "code", with_origin=False)
    mod = repo / "src/muru/wur_v2/decode_authority.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("# committed\n")
    script = repo / "scripts/run.py"
    script.parent.mkdir()
    script.write_text("# committed\n")
    helper = repo / "scripts/helper.py"
    helper.write_text("# committed helper\n")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "code")
    ok = {"muru.wur_v2.decode_authority": str(mod)}
    DA.check_code_provenance(repo, modules=ok, main_file=str(script))
    shadow = tmp_path / "scratchpad/muru/wur_v2/decode_authority.py"
    shadow.parent.mkdir(parents=True)
    shadow.write_text("# committed\n")
    with pytest.raises(DecodeAuthorityError, match="outside"):
        DA.check_code_provenance(repo, modules={"muru.wur_v2.decode_authority": str(shadow)}, main_file=str(script))
    with pytest.raises(DecodeAuthorityError, match="outside"):
        DA.check_code_provenance(repo, modules=ok, main_file=str(tmp_path / "scratchpad/run_one_look.py"))
    with pytest.raises(DecodeAuthorityError, match="no file"):
        DA.check_code_provenance(repo, modules=ok, main_file="")
    DA.check_code_provenance(repo, modules={**ok, "helper": str(helper)}, main_file=str(script))
    helper.write_text("# edited helper, not committed\n")
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        DA.check_code_provenance(repo, modules={**ok, "helper": str(helper)}, main_file=str(script))
    helper.write_text("# committed helper\n")
    untracked = repo / "src/muru/wur_v2/header_eligibility.py"
    untracked.write_text("x = 1\n")
    with pytest.raises(DecodeAuthorityError, match="not present at commit"):
        DA.check_code_provenance(repo, modules={**ok, "muru.wur_v2.header_eligibility": str(untracked)},
                                 main_file=str(script))


def test_R3_legacy_pymzml_reader_refuses_renamed_external_files(tmp_path):
    from muru.io import mzml as legacy
    for name in ("20220613_100AGC_60000Res_pluskal_mce_1D1_A10_id.mzML", "20200303_ENTACT_RP_mix499_pos_CE15.mzML",
                 "anything.mzML"):
        p = FX.write_mzml(tmp_path / "neutral" / name, FX.VAL)
        with pytest.raises(legacy.ExternalSourceRefused):
            next(legacy.iter_ms2(p))


def test_R3_void_study1_guard_cannot_be_constructed(tmp_path):
    from muru.wur_v2.confirmation_guard import ConfirmationAccessGuard, ConfirmationGuardError
    with pytest.raises(ConfirmationGuardError, match="VOID"):
        ConfirmationAccessGuard(record_path=tmp_path / "r.json", freeze_doc_path=tmp_path / "f.md",
                                freeze_manifest_path=tmp_path / "m.json", expected_freeze_commit="0" * 40,
                                actual_candidate_hash="", actual_comparator_hash="", actual_population_key_hash="",
                                actual_scaffold_group_hash="", actual_spectrum_manifest_hash="",
                                allowed_spectrum_keys=set(), root=tmp_path)


def test_R3_constructed_subclass_is_refused_by_the_decoder(tmp_path, spy):
    env = FX.anchor_env(tmp_path)

    class Sub(AnchorPreflightAuthority):
        __slots__ = ()

    g = DA._for_tests(Sub, log_path=env["log"], root=env["repo"], code_root=None, registry_manifest_sha256=env["registry_sha"])
    assert DA.is_constructed(g)
    with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
        X.decode_selected(env["pooled"], ["s3"], g)
    assert spy["n"] == 0


def test_R3_authorize_decode_refuses_an_unconstructed_authority_directly():
    g = object.__new__(AnchorPreflightAuthority)
    with pytest.raises(DecodeAuthorityError, match="no registered scope"):
        DA.authorize_decode(g, "f.mzML", "0" * 64, [])


def test_R1_header_mz_differing_from_the_recorded_decoded_mz_is_refused(tmp_path, spy):
    scans = [("s0", 1, None, None), ("s3", 2, 300.004, 20.0), ("s4", 2, 300.0, 60.0)]
    env = FX.anchor_env(tmp_path, pooled_scans=scans)
    rows = DA._rows(env["repo"], DA.DECODED_SPECTRA)
    for r in rows:
        r["selected_ion_mz"] = "300.0"                    # registry and allowlist say 300.0; the file says 300.004
    env["registry_sha"] = FX.write_registry(env["repo"], DA._rows(env["repo"], DA.EXPOSED_FILES), rows)
    FX.git(env["repo"], "commit", "-qam", "recorded m/z differs from header")
    auth = FX.anchor_authority(env)
    with pytest.raises(DecodeAuthorityError, match="does not match the allowlisted"):
        X.decode_selected(env["pooled"], ["s3"], auth)
    assert spy["n"] == 0


def test_R1_empty_anchor_allowlist_is_refused(tmp_path):
    env = FX.anchor_env(tmp_path)
    FX.write_csv(env["repo"] / DA.ANCHOR_ALLOWLIST, [], ["file", "file_sha256", "spectrum_id", "selected_ion_mz",
                                                         "anchor_key", "anchor_mh"])
    FX.git(env["repo"], "commit", "-qam", "empty")
    with pytest.raises(DecodeAuthorityError, match="empty"):
        FX.anchor_authority(env)


def test_restricted_header_reader_never_returns_collision_energy_assisted_or_msn_rows():
    """F-MSn: population-2 headers must not expose the Assisted energy or MS3+ precursor (fragment) m/z."""
    scans = [("m1", 1, None, None), ("a20", 2, 300.1, 20.0), ("assist", 2, 300.1, 45.0), ("a60", 2, 300.1, 60.0),
             ("ms3", 3, 151.07, 20.0), ("ms3b", 3, 151.07, 60.0)]
    rows = X.scan_headers_rung_only(FX.mzml_bytes(scans))
    assert [r["spectrum_id"] for r in rows] == ["a20", "a60"]
    assert all(set(r) == set(X.RUNG_ONLY_COLUMNS) for r in rows)
    assert {r["rung"] for r in rows} == {20.0, 60.0}


# ======================================================================================= the one look

def test_R8_record_written_committed_pushed_and_intent_logged_before_first_array_decode(tmp_path, spy):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    freeze = FX.git(repo, "rev-parse", "HEAD")
    seen = {}

    def before_decode():
        if seen:
            return
        rec = repo / DA.ACCESS_RECORD
        assert rec.is_file() and json.loads(rec.read_text())["validation_access_head"] == freeze
        assert FX.git(repo, "rev-parse", "HEAD^") == freeze
        assert FX.git(repo, "ls-remote", "origin", DA.ACCESS_REF).split()[0] == FX.git(repo, "rev-parse", "HEAD")
        assert (env["ledger"] / f"{DA.STUDY_ID_V2}.json").is_file()
        intents = [json.loads(line) for line in (repo / DA.DECODE_INTENTS).read_text().splitlines()]
        assert intents and set(intents[-1]["spectra"]) == {"v1", "v2"}
        seen["ok"] = True

    spy["before"] = before_decode
    auth = FX.v2_authority(env)
    out = X.decode_selected(FX.member(env), ["v1", "v2"], auth)
    assert set(out) == {"v1", "v2"} and seen.get("ok") and spy["n"] == 4


def test_R3_no_freeze_commit_means_no_authority_and_nothing_written(tmp_path):
    env = FX.validation_env(tmp_path, commit_freeze=False)
    with pytest.raises(DecodeAuthorityError):
        FX.v2_authority(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()
    assert not (env["ledger"] / f"{DA.STUDY_ID_V2}.json").exists()


def test_R7_freeze_not_published_on_origin_is_refused(tmp_path):
    env = FX.validation_env(tmp_path, publish=False)
    with pytest.raises(DecodeAuthorityError, match="must be published"):
        FX.v2_authority(env)


def test_R7_head_one_commit_past_the_freeze_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    (env["repo"] / "NOTE.md").write_text("typo\n")
    FX.git(env["repo"], "add", "NOTE.md")
    FX.git(env["repo"], "commit", "-q", "-m", "note")
    with pytest.raises(DecodeAuthorityError, match="added exactly once, by HEAD"):
        FX.v2_authority(env)


def test_R7_freeze_deleted_and_readded_is_a_second_freeze(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.git(repo, "rm", "-q", DA.FREEZE_DOC)
    FX.git(repo, "commit", "-q", "-m", "remove")
    (repo / DA.FREEZE_DOC).write_text("FINAL FREEZE study 2\n")
    FX.git(repo, "add", DA.FREEZE_DOC)
    FX.git(repo, "commit", "-q", "-m", "re-freeze")
    FX.publish_freeze(env)
    with pytest.raises(DecodeAuthorityError, match="added exactly once"):
        FX.v2_authority(env)


def test_R7_competing_freeze_on_another_branch_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    freeze = FX.git(repo, "rev-parse", "HEAD")
    FX.git(repo, "checkout", "-q", "-b", "alt", "HEAD~1")
    (repo / DA.FREEZE_DOC).write_text("A DIFFERENT FREEZE\n")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "alternative")
    FX.git(repo, "checkout", "-q", "main")
    assert FX.git(repo, "rev-parse", "HEAD") == freeze
    with pytest.raises(DecodeAuthorityError, match="competing freezes"):
        FX.v2_authority(env)


def test_R7_manifest_committed_before_the_freeze_commit_is_refused(tmp_path):
    env = FX.validation_env(tmp_path, commit_freeze=False)
    repo = env["repo"]
    FX.git(repo, "add", DA.FREEZE_MANIFEST)
    FX.git(repo, "commit", "-q", "-m", "manifest first")
    FX.git(repo, "add", "-A")
    FX.git(repo, "commit", "-q", "-m", "FINAL FREEZE")
    FX.git(repo, "push", "-q", "origin", "main")
    FX.publish_freeze(env)
    with pytest.raises(DecodeAuthorityError, match="added exactly once"):
        FX.v2_authority(env)


def test_R7_skip_worktree_untracked_and_ignored_code_are_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    p = repo / DA.POPULATION_CSV
    FX.git(repo, "update-index", "--skip-worktree", DA.POPULATION_CSV)
    p.write_text(p.read_text() + "KEYB,GB,500.0\n")
    with pytest.raises(DecodeAuthorityError, match="hide working-tree changes"):
        FX.v2_authority(env)
    FX.git(repo, "update-index", "--no-skip-worktree", DA.POPULATION_CSV)
    FX.git(repo, "checkout", "--", DA.POPULATION_CSV)
    (repo / "scratch_decoder.py").write_text("x = 1\n")
    with pytest.raises(DecodeAuthorityError, match="not clean"):
        FX.v2_authority(env)
    (repo / "scratch_decoder.py").unlink()
    (repo / ".git/info/exclude").write_text("scripts/hidden_helper.py\n")
    (repo / "scripts").mkdir()
    (repo / "scripts/hidden_helper.py").write_text("x = 1\n")
    with pytest.raises(DecodeAuthorityError, match="ignored Python files"):
        FX.v2_authority(env)


@pytest.mark.parametrize("tweak,match", [
    (lambda m: m.update(candidate_hash="c" * 64), "candidate_hash"),
    (lambda m: m.update(study_id="muru-v2-msnlib-confirmation-1.0"), "study_id"),
    (lambda m: m.update(registry_manifest_sha256="r" * 64), "registry_manifest_sha256"),
    (lambda m: m["frozen_files"].pop(DA.PROTOCOL_V2), "lacks required entries"),
    (lambda m: m["frozen_files"].update({DA.SCAN_ALLOWLIST: "f" * 64}), "!= frozen"),
])
def test_R6_manifest_that_does_not_match_recomputed_values_is_refused(tmp_path, tweak, match):
    env = FX.validation_env(tmp_path, manifest_tweak=tweak)
    with pytest.raises(DecodeAuthorityError, match=match):
        FX.v2_authority(env)


def test_R6_population_intersecting_the_exposure_registry_is_refused(tmp_path):
    cases = ((dict(excluded_keys=["KEYA"]), "population keys are in the exposure registry"),
             (dict(excluded_groups=["GA"]), "scaffold groups intersect"),
             (dict(exposed_extra=[{"file": "x.mzML", "file_sha256": "0" * 64, "unique_sample_id": "pluskal_C3_id",
                                   "events": "E"}]), "exposed file or well"))
    for i, (kw, match) in enumerate(cases):
        env = FX.validation_env(tmp_path / f"case{i}", **kw)
        with pytest.raises(DecodeAuthorityError, match=match):
            FX.v2_authority(env)


def test_R6_live_header_re_read_catches_a_frozen_mz_that_the_file_does_not_have(tmp_path):
    env = FX.validation_env(tmp_path, allow_mz="412.25")
    with pytest.raises(DecodeAuthorityError, match="live re-read"):
        FX.v2_authority(env)


def test_R6_zip_member_with_different_bytes_is_refused_before_any_record(tmp_path):
    env = FX.validation_env(tmp_path)
    with zipfile.ZipFile(env["zips"] / "lib.zip", "w") as zf:
        zf.writestr(FX.MEMBER, FX.mzml_bytes(FX.VAL, marker=5.0))
    with pytest.raises(DecodeAuthorityError, match="frozen name and sha256"):
        FX.v2_authority(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_R5_second_construction_in_the_same_clone_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    FX.v2_authority(env)
    with pytest.raises(DecodeAuthorityError):
        FX.v2_authority(env)


def test_R5_record_deleted_branch_reset_and_ledgers_removed_is_still_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.v2_authority(env)
    shutil.rmtree(env["ledger"])
    shutil.rmtree(repo / ".git/muru-access-ledger")
    FX.git(repo, "update-ref", "-d", DA.ACCESS_REF)
    FX.git(repo, "reset", "-q", "--hard", "HEAD~1")
    assert not (repo / DA.ACCESS_RECORD).exists()
    with pytest.raises(DecodeAuthorityError, match="existed in git history|holds"):
        FX.v2_authority(env)


def test_R5_history_erased_locally_is_still_refused_by_the_pushed_ref(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.v2_authority(env)
    shutil.rmtree(env["ledger"])
    shutil.rmtree(repo / ".git/muru-access-ledger")
    FX.git(repo, "update-ref", "-d", DA.ACCESS_REF)
    FX.git(repo, "reset", "-q", "--hard", "HEAD~1")
    FX.git(repo, "reflog", "expire", "--expire=now", "--all")
    FX.git(repo, "gc", "-q", "--prune=now")
    assert FX.git(repo, "log", "--all", "--reflog", "--format=%H", "--", DA.ACCESS_DIR) == ""
    with pytest.raises(DecodeAuthorityError, match="holds"):
        FX.v2_authority(env)


def test_R5_layer_isolated_local_history_blocks_when_remote_ref_and_ledgers_are_gone(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    FX.v2_authority(env)
    shutil.rmtree(env["ledger"])
    shutil.rmtree(repo / ".git/muru-access-ledger")
    FX.git(repo, "push", "-q", "origin", f":{DA.ACCESS_REF}")
    FX.git(repo, "update-ref", "-d", DA.ACCESS_REF)
    FX.git(repo, "reset", "-q", "--hard", "HEAD~1")
    with pytest.raises(DecodeAuthorityError, match="existed in git history"):
        FX.v2_authority(env)


def test_R5_layer_isolated_record_is_not_authorized_if_origin_does_not_show_it(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    orig = DA._git_text

    def no_push(root, *args, **kw):
        if args and args[0] == "push":
            return ""
        return orig(root, *args, **kw)

    monkeypatch.setattr(DA, "_git_text", no_push)
    with pytest.raises(DecodeAuthorityError, match="does not show"):
        FX.v2_authority(env)
    assert not (env["ledger"] / f"{DA.STUDY_ID_V2}.json").exists()


def test_R7_layer_isolated_manifest_byte_binding(tmp_path, monkeypatch):
    env = FX.validation_env(tmp_path)
    monkeypatch.setattr(ConfirmationV2Authority, "_check_clean_tree", staticmethod(lambda ctx: None))
    p = env["repo"] / DA.FREEZE_MANIFEST
    p.write_text(p.read_text().replace('"study_id"', '"note": "harmless-looking edit", "study_id"'))
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        FX.v2_authority(env)


def test_R6_scan_allowlist_key_outside_the_population_is_refused(tmp_path):
    env = FX.validation_env(tmp_path, scan_key="KEYZ")
    with pytest.raises(DecodeAuthorityError, match="outside the population"):
        FX.v2_authority(env)


def test_R5_a_clone_made_before_the_look_is_refused_after_the_look(tmp_path):
    env = FX.validation_env(tmp_path)
    clone = tmp_path / "clone_b"
    origin = FX.git(env["repo"], "remote", "get-url", "origin")
    subprocess.run(["git", "clone", "-q", origin, str(clone)], check=True, capture_output=True)
    FX.git(clone, "config", "user.email", "t@t")
    FX.git(clone, "config", "user.name", "t")
    FX.v2_authority(env)
    env_b = dict(env, repo=clone, ledger=tmp_path / "ledger_b")
    with pytest.raises(DecodeAuthorityError, match="another clone|existed in git history"):
        FX.v2_authority(env_b)


def test_R5_shallow_clone_is_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    shallow = tmp_path / "shallow"
    origin = FX.git(env["repo"], "remote", "get-url", "origin")
    subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", "main", f"file://{origin}", str(shallow)], check=True, capture_output=True)
    FX.git(shallow, "config", "user.email", "t@t")
    FX.git(shallow, "config", "user.name", "t")
    with pytest.raises(DecodeAuthorityError, match="shallow"):
        FX.v2_authority(dict(env, repo=shallow))


def test_R5_gitignored_record_or_intents_on_disk_are_refused(tmp_path):
    env = FX.validation_env(tmp_path)
    repo = env["repo"]
    (repo / ".git/info/exclude").write_text(f"{DA.ACCESS_DIR}/\n")
    for rel in (DA.ACCESS_RECORD, DA.DECODE_INTENTS):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}\n")
        with pytest.raises(DecodeAuthorityError, match="already holds an access record"):
            FX.v2_authority(env)
        p.unlink()


def test_R5_common_dir_ledger_alone_blocks_a_second_look(tmp_path):
    env = FX.validation_env(tmp_path)
    common = env["repo"] / ".git/muru-access-ledger"
    common.mkdir(parents=True)
    (common / f"{DA.STUDY_ID_V2}.json").write_text("{}\n")
    with pytest.raises(DecodeAuthorityError, match="ledger entry"):
        FX.v2_authority(env)


def test_R5_unreachable_origin_fails_before_anything_is_written(tmp_path):
    env = FX.validation_env(tmp_path)
    FX.git(env["repo"], "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(DecodeAuthorityError, match="fetch"):
        FX.v2_authority(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_R4_scan_outside_allowlist_and_substituted_or_stranger_members_are_refused(tmp_path, spy):
    env = FX.validation_env(tmp_path)
    auth = FX.v2_authority(env)
    with pytest.raises(DecodeAuthorityError, match="not in this authority's allowlist"):
        X.decode_selected(FX.member(env), ["v1", "v3"], auth)
    other = tmp_path / "other.zip"
    with zipfile.ZipFile(other, "w") as zf:
        zf.writestr(FX.MEMBER, FX.mzml_bytes(FX.VAL, marker=9.0))
        zf.writestr("mzml/pluskal_Z9_id.mzML", FX.mzml_bytes(FX.VAL))
    with pytest.raises(DecodeAuthorityError, match="substituted file"):
        X.decode_selected(X.ZipMember(other, FX.MEMBER), ["v1"], auth)
    with pytest.raises(DecodeAuthorityError, match="not in this authority's allowlist"):
        X.decode_selected(X.ZipMember(other, "mzml/pluskal_Z9_id.mzML"), ["v1"], auth)
    assert spy["n"] == 0


def test_R8_decode_refused_if_record_or_ledger_disappears_after_construction(tmp_path, spy):
    env = FX.validation_env(tmp_path)
    auth = FX.v2_authority(env)
    (env["ledger"] / f"{DA.STUDY_ID_V2}.json").unlink()
    with pytest.raises(DecodeAuthorityError, match="ledger entry"):
        X.decode_selected(FX.member(env), ["v1"], auth)
    assert spy["n"] == 0


def test_canonical_hash_matches_candidate_module():
    from muru.wur_v2.candidate import sha256_of
    obj = {"b": [1, 2.5, {"z": None}], "a": "x"}
    assert DA.canonical_json_sha256(obj) == sha256_of(obj)
