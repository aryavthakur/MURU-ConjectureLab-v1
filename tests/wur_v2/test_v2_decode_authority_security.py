"""Adversarial tests for the study-2 decode boundary (muru.wur_v2.decode_authority + external_mzml.decode_selected).

Every test attempts one concrete way premature or out-of-scope decoding could happen and asserts it is refused
AND that not a single binary array was decoded (a spy on external_mzml._decode_array counts calls). All data are
synthetic: tiny mzML files and throwaway git repositories under tmp_path. No real MSnLib file is opened.

Requirement map (MSnLib confirmation study 2 mandate, section 3):
  R1 anchor preflight only decodes scans whose precursor matches the explicit anchor allowlist
  R2 co-plated non-anchor scans cannot be selected by position
  R3 no validation decode without a committed final freeze
  R4 every requested validation scan is in the frozen scan allowlist
  R5 a historical access record blocks a second first look even if the file was deleted
  R6 candidate/comparator/population/scaffold/spectrum hashes are recomputed live
  R7 freeze bytes are bound to the freeze commit
  R8 the access record is written (and committed) before any validation binary array is decoded
"""
import base64
import csv
import hashlib
import json
import shutil
import subprocess

import numpy as np
import pytest

from muru.wur_v2 import decode_authority as DA
from muru.wur_v2 import external_mzml as X
from muru.wur_v2.decode_authority import AnchorPreflightAuthority, ConfirmationV2Authority, DecodeAuthorityError


# ----------------------------------------------------------------------------------------- synthetic data

def _bda(values, kind_acc, bits64):
    raw = np.asarray(values, "<f8" if bits64 else "<f4").tobytes()
    return (f'<binaryDataArray encodedLength="0"><cvParam accession="{"MS:1000523" if bits64 else "MS:1000521"}" name="f"/>'
            f'<cvParam accession="{kind_acc}" name="a"/><binary>{base64.b64encode(raw).decode()}</binary></binaryDataArray>')


def write_mzml(path, scans):
    """scans: list of (spectrum_id, ms_level, selected_ion_mz or None, collision_energy or None)."""
    specs = []
    for i, (sid, level, mz, ce) in enumerate(scans):
        prec = ""
        if mz is not None:
            prec = (f'<precursorList count="1"><precursor><selectedIonList count="1"><selectedIon>'
                    f'<cvParam accession="MS:1000744" name="sel" value="{mz}"/></selectedIon></selectedIonList>'
                    f'<activation><cvParam accession="MS:1000045" name="ce" value="{ce}"/></activation></precursor></precursorList>')
        specs.append(
            f'<spectrum index="{i}" id="{sid}" defaultArrayLength="2"><cvParam accession="MS:1000511" name="ms level" value="{level}"/>'
            f'<scanList count="1"><scan><scanWindowList count="1"><scanWindow><cvParam accession="MS:1000501" name="lo" value="40"/>'
            f'<cvParam accession="MS:1000500" name="hi" value="1000"/></scanWindow></scanWindowList></scan></scanList>{prec}'
            f'<binaryDataArrayList count="2">{_bda([50.0 + i, 99.0 + i], "MS:1000514", True)}'
            f'{_bda([10.0, 20.0], "MS:1000515", False)}</binaryDataArrayList></spectrum>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<?xml version="1.0" encoding="utf-8"?><mzML xmlns="http://psi.hupo.org/ms/mzml"><run>'
                    f'<spectrumList count="{len(scans)}">' + "".join(specs) + "</spectrumList></run></mzML>")
    return path


# pooled well: a NON-anchor compound (m/z 500.0) is acquired FIRST, the anchor (m/z 300.0) later
POOLED = [("s0", 1, None, None),
          ("s1", 2, 500.0, 20.0), ("s2", 2, 500.0, 60.0),
          ("s3", 2, 300.0, 20.0), ("s4", 2, 300.0, 60.0)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    return root


def write_csv(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def spy(monkeypatch):
    """Counts binary array decodes; optional pre-decode assertion hook."""
    state = {"n": 0, "before": None}
    orig = X._decode_array

    def _spy(bda):
        if state["before"] is not None:
            state["before"]()
        state["n"] += 1
        return orig(bda)

    monkeypatch.setattr(X, "_decode_array", _spy)
    return state


# ----------------------------------------------------------------------------------------- anchor preflight

@pytest.fixture
def anchor_env(tmp_path):
    data = tmp_path / "data"
    pooled = write_mzml(data / "pluskal_A1_id.mzML", POOLED)
    other = write_mzml(data / "pluskal_B7_id.mzML", [("t1", 2, 300.0, 20.0), ("t2", 2, 300.0, 60.0)])
    repo = init_repo(tmp_path / "repo")
    write_csv(repo / DA.ANCHOR_ALLOWLIST,
              [{"file": pooled.name, "file_sha256": sha(pooled), "unique_sample_id": "pluskal_A1_id",
                "anchor_key": "ANCHORKEY", "anchor_mh": "300.0"}],
              ["file", "file_sha256", "unique_sample_id", "anchor_key", "anchor_mh"])
    write_csv(repo / DA.EXPOSED_FILES,
              [{"file": pooled.name, "file_sha256": sha(pooled), "unique_sample_id": "pluskal_A1_id", "events": "E"}],
              ["file", "file_sha256", "unique_sample_id", "events"])
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "registry + allowlist")
    return {"repo": repo, "pooled": pooled, "other": other, "log": tmp_path / "preflight_log.jsonl"}


def anchor_authority(env):
    return AnchorPreflightAuthority(log_path=env["log"], root=env["repo"], code_root=None)


def rung_ids_by_position(path, n=6):
    """Exactly the burned script's selection: first n rung-tagged scans by position."""
    return [r["spectrum_id"] for r in X.scan_headers(path) if r.get("ms_level") == 2.0][:n]


def test_R2_positional_selection_in_pooled_well_is_refused_before_any_decode(anchor_env, spy):
    auth = anchor_authority(anchor_env)
    ids = rung_ids_by_position(anchor_env["pooled"])
    assert ids[:2] == ["s1", "s2"]                                  # the non-anchor scans come first
    with pytest.raises(DecodeAuthorityError, match="not within 0.01 Da"):
        X.decode_selected(anchor_env["pooled"], ids, auth)
    assert spy["n"] == 0


def test_R1_caller_naming_only_a_coplated_scan_is_refused(anchor_env, spy):
    auth = anchor_authority(anchor_env)
    with pytest.raises(DecodeAuthorityError, match="not within 0.01 Da"):
        X.decode_selected(anchor_env["pooled"], ["s1"], auth)
    assert spy["n"] == 0


def test_R1_anchor_matched_scans_decode_and_are_logged_with_their_anchor(anchor_env, spy):
    auth = anchor_authority(anchor_env)
    out = X.decode_selected(anchor_env["pooled"], ["s3", "s4"], auth)
    assert set(out) == {"s3", "s4"} and spy["n"] == 4
    log = [json.loads(line) for line in anchor_env["log"].read_text().splitlines()]
    assert log[-1]["event"] == "authorize"
    assert {s["spectrum_id"] for s in log[-1]["spectra"]} == {"s3", "s4"}
    assert {s["anchor_key"] for s in log[-1]["spectra"]} == {"ANCHORKEY"}


def test_R1_near_isobar_just_outside_tolerance_is_refused(anchor_env, spy, tmp_path):
    p = write_mzml(tmp_path / "iso" / anchor_env["pooled"].name, [("a", 2, 300.011, 20.0)])
    auth = AnchorPreflightAuthority(log_path=anchor_env["log"], root=anchor_env["repo"], code_root=None)
    auth.files[p.name]["sha256"] = sha(p)          # isolate the precursor check from the content-hash check
    with pytest.raises(DecodeAuthorityError, match="not within 0.01 Da"):
        X.decode_selected(p, ["a"], auth)
    assert spy["n"] == 0


def test_R1_file_not_on_anchor_allowlist_is_refused(anchor_env, spy):
    auth = anchor_authority(anchor_env)
    with pytest.raises(DecodeAuthorityError, match="not on the anchor preflight allowlist"):
        X.decode_selected(anchor_env["other"], ["t1"], auth)        # precursor 300.0 matches the anchor mass
    assert spy["n"] == 0


def test_R1_validation_file_renamed_to_an_anchor_basename_is_refused(anchor_env, spy, tmp_path):
    impostor = tmp_path / "impostor" / anchor_env["pooled"].name
    impostor.parent.mkdir()
    shutil.copy(anchor_env["other"], impostor)                        # same name, different content
    auth = anchor_authority(anchor_env)
    with pytest.raises(DecodeAuthorityError, match="renamed or substituted"):
        X.decode_selected(impostor, ["t1"], auth)
    assert spy["n"] == 0


def test_R1_allowlisted_file_absent_from_exposure_registry_refused_at_construction(anchor_env):
    repo = anchor_env["repo"]
    rows = [{"file": "pluskal_A1_id.mzML", "file_sha256": "0" * 64, "unique_sample_id": "pluskal_A1_id", "events": "E"}]
    write_csv(repo / DA.EXPOSED_FILES, rows, ["file", "file_sha256", "unique_sample_id", "events"])
    git(repo, "commit", "-qam", "registry no longer lists the anchor file")
    with pytest.raises(DecodeAuthorityError, match="not in the exposure registry"):
        anchor_authority(anchor_env)


def test_R1_uncommitted_allowlist_widening_refused_at_construction(anchor_env):
    p = anchor_env["repo"] / DA.ANCHOR_ALLOWLIST
    p.write_text(p.read_text() + f"{anchor_env['other'].name},{sha(anchor_env['other'])},pluskal_B7_id,X,300.0\n")
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        anchor_authority(anchor_env)


def test_R1_ms1_scan_is_refused(anchor_env, spy):
    auth = anchor_authority(anchor_env)
    with pytest.raises(DecodeAuthorityError):
        X.decode_selected(anchor_env["pooled"], ["s0"], auth)
    assert spy["n"] == 0


def test_R1_msn_scan_carrying_the_anchor_precursor_is_refused(anchor_env, spy, tmp_path):
    p = write_mzml(tmp_path / "msn" / anchor_env["pooled"].name, [("ms3", 3, 300.0, 40.0)])
    auth = anchor_authority(anchor_env)
    auth.files[p.name]["sha256"] = sha(p)
    with pytest.raises(DecodeAuthorityError, match="not an MS2 scan"):
        X.decode_selected(p, ["ms3"], auth)
    assert spy["n"] == 0


# ----------------------------------------------------------------------------------------- decoder type gate

class DuckGuard:
    authorized = True

    def authorize(self, path, requests):
        pass

    def record_decode(self, path, ids):
        pass


class AnchorSubclass(AnchorPreflightAuthority):
    pass


def test_R3_duck_typed_guard_like_the_burned_TestGuard_is_refused(anchor_env, spy):
    with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
        X.decode_selected(anchor_env["pooled"], ["s1"], DuckGuard())
    assert spy["n"] == 0


def test_R3_legacy_and_void_guards_are_refused(anchor_env, spy, tmp_path):
    from muru.wur_v2.confirmation_guard import ConfirmationAccessGuard
    from muru.wur_v2.external_guard import AccessGuard
    for cls in (AccessGuard, ConfirmationAccessGuard):
        g = object.__new__(cls)
        g.authorized = True
        g.allowed = {(anchor_env["pooled"].name, "s1")}
        with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
            X.decode_selected(anchor_env["pooled"], ["s1"], g)
    assert spy["n"] == 0


def test_R3_subclass_of_an_authority_is_refused(anchor_env, spy):
    g = AnchorSubclass(log_path=anchor_env["log"], root=anchor_env["repo"], code_root=None)
    with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
        X.decode_selected(anchor_env["pooled"], ["s3"], g)
    assert spy["n"] == 0


def test_R3_authority_built_with_new_skipping_construction_checks_is_refused(anchor_env, spy):
    real = anchor_authority(anchor_env)
    fake = object.__new__(AnchorPreflightAuthority)
    fake.__dict__.update(real.__dict__)                        # every attribute a real one has, no __init__ run
    fake.files = {anchor_env["pooled"].name: {"sha256": sha(anchor_env["pooled"]), "mh": [500.0], "keys": ["X"]}}
    assert type(fake) is AnchorPreflightAuthority and fake.authorized is True
    with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
        X.decode_selected(anchor_env["pooled"], ["s1"], fake)
    assert spy["n"] == 0


def test_R3_code_provenance_refuses_shadowed_or_modified_modules(tmp_path):
    repo = init_repo(tmp_path / "code")
    mod = repo / "src/muru/wur_v2/decode_authority.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("# committed\n")
    script = repo / "scripts/run.py"
    script.parent.mkdir()
    script.write_text("# committed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "code")
    ok = {"muru.wur_v2.decode_authority": str(mod)}
    DA.check_code_provenance(repo, modules=ok, main_file=str(script))
    shadow = tmp_path / "scratchpad/muru/wur_v2/decode_authority.py"
    shadow.parent.mkdir(parents=True)
    shadow.write_text("# committed\n")
    with pytest.raises(DecodeAuthorityError, match="outside"):
        DA.check_code_provenance(repo, modules={"muru.wur_v2.decode_authority": str(shadow)}, main_file=str(script))
    with pytest.raises(DecodeAuthorityError, match="outside"):
        DA.check_code_provenance(repo, modules=ok, main_file=str(tmp_path / "scratchpad/run_one_look.py"))
    mod.write_text("# edited, not committed\n")
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        DA.check_code_provenance(repo, modules=ok, main_file=str(script))
    mod.write_text("# committed\n")
    untracked = repo / "src/muru/wur_v2/header_eligibility.py"
    untracked.write_text("x = 1\n")
    with pytest.raises(DecodeAuthorityError, match="not present at commit"):
        DA.check_code_provenance(repo, modules={**ok, "muru.wur_v2.header_eligibility": str(untracked)},
                                 main_file=str(script))


def test_R3_legacy_pymzml_reader_refuses_external_msnlib_files(tmp_path):
    from muru.io import mzml as legacy
    for name in ("20220613_100AGC_60000Res_pluskal_mce_1D1_A10_id.mzML", "anything.mzML"):
        sub = "msnlib_mzml" if name == "anything.mzML" else "x"
        p = write_mzml(tmp_path / sub / name, VAL)
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


def test_R3_authority_whose_construction_failed_midway_is_not_authorized(anchor_env, spy, monkeypatch):
    g = anchor_authority(anchor_env)
    g.authorized = False
    with pytest.raises(X.OutcomeAccessError):
        X.decode_selected(anchor_env["pooled"], ["s3"], g)
    assert spy["n"] == 0


def test_header_change_between_authorization_and_decode_is_refused(anchor_env, spy, monkeypatch):
    auth = anchor_authority(anchor_env)
    orig = auth.authorize

    def authorize_then_swap(path, requests):
        orig(path, requests)
        write_mzml(anchor_env["pooled"], [(sid, lvl, 500.0 if sid == "s3" else mz, ce) for sid, lvl, mz, ce in POOLED])

    monkeypatch.setattr(auth, "authorize", authorize_then_swap)
    with pytest.raises(X.OutcomeAccessError, match="changed between authorization and decode"):
        X.decode_selected(anchor_env["pooled"], ["s3"], auth)
    assert spy["n"] == 0


# ----------------------------------------------------------------------------------------- validation one look

VAL = [("v1", 2, 412.2, 20.0), ("v2", 2, 412.2, 60.0), ("v3", 2, 612.3, 20.0)]


def build_frozen_repo(tmp_path, *, commit_freeze=True):
    data = tmp_path / "data"
    vfile = write_mzml(data / "pluskal_C3_id.mzML", VAL)
    repo = init_repo(tmp_path / "repo")
    (repo / "README").write_text("r\n")
    git(repo, "add", "README")
    git(repo, "commit", "-q", "-m", "protocol")
    cand = {"name": "CAND", "coef": [1, 2]}
    comp = {"name": "COMP", "coef": [3]}
    for rel, obj in ((DA.CANDIDATE_JSON, cand), (DA.COMPARATOR_JSON, comp)):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(json.dumps(obj))
    pop = [{"key": "KEYA", "scaffold_group": "GA", "mh": "412.2"}]
    write_csv(repo / DA.POPULATION_CSV, pop, ["key", "scaffold_group", "mh"])
    scans = [{"file": vfile.name, "file_sha256": sha(vfile), "spectrum_id": "v1", "selected_ion_mz": "412.2", "key": "KEYA", "rung": "20"},
             {"file": vfile.name, "file_sha256": sha(vfile), "spectrum_id": "v2", "selected_ion_mz": "412.2", "key": "KEYA", "rung": "60"}]
    write_csv(repo / DA.SCAN_ALLOWLIST, scans, ["file", "file_sha256", "spectrum_id", "selected_ion_mz", "key", "rung"])
    (repo / DA.FREEZE_DOC).write_text("FINAL FREEZE study 2\n")
    hashes = {"candidate_hash": DA.canonical_json_sha256(cand), "comparator_hash": DA.canonical_json_sha256(comp),
              "population_key_hash": DA.sha256_lines(["KEYA"]), "scaffold_group_hash": DA.sha256_lines(["GA"]),
              "spectrum_manifest_hash": DA.sha256_lines([f"{vfile.name}:v1", f"{vfile.name}:v2"])}
    frozen = {rel: hashlib.sha256((repo / rel).read_bytes()).hexdigest()
              for rel in (DA.CANDIDATE_JSON, DA.COMPARATOR_JSON, DA.POPULATION_CSV, DA.SCAN_ALLOWLIST, DA.FREEZE_DOC)}
    manifest = {"study_id": DA.STUDY_ID_V2, **hashes, "frozen_files": frozen}
    (repo / DA.FREEZE_MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(manifest, indent=1))
    if commit_freeze:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "FINAL FREEZE")
    live = {k: hashes[k] for k in DA.LIVE_HEADER_HASH_FIELDS}
    return {"repo": repo, "vfile": vfile, "ledger": tmp_path / "ledger", "live": live, "manifest": manifest}


def v2(env, **kw):
    return ConfirmationV2Authority(live_header_hashes=kw.pop("live", env["live"]), root=env["repo"],
                                   ledger_dir=env["ledger"], code_root=None, **kw)


def test_R8_access_record_is_written_fsynced_committed_and_intent_logged_before_first_array_decode(tmp_path, spy):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    freeze = git(repo, "rev-parse", "HEAD")
    seen = {}

    def before_decode():
        if seen:
            return
        rec = repo / DA.ACCESS_RECORD
        assert rec.is_file()
        assert git(repo, "log", "--format=%H", "--", DA.ACCESS_RECORD) != ""
        assert git(repo, "rev-parse", "HEAD^") == freeze
        assert (env["ledger"] / f"{DA.STUDY_ID_V2}.json").is_file()
        intents = [json.loads(line) for line in (repo / DA.DECODE_INTENTS).read_text().splitlines()]
        assert intents and set(intents[-1]["spectra"]) == {"v1", "v2"}
        assert json.loads(rec.read_text())["validation_access_head"] == freeze
        seen["ok"] = True

    spy["before"] = before_decode
    auth = v2(env)
    out = X.decode_selected(env["vfile"], ["v1", "v2"], auth)
    assert set(out) == {"v1", "v2"} and seen.get("ok") and spy["n"] == 4


def test_R3_no_freeze_commit_means_no_authority(tmp_path, spy):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    with pytest.raises(DecodeAuthorityError):
        v2(env)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists() and not env["ledger"].exists()


def test_R7_head_one_commit_past_the_freeze_is_refused_even_for_docs(tmp_path):
    env = build_frozen_repo(tmp_path)
    (env["repo"] / "NOTE.md").write_text("typo fix\n")
    git(env["repo"], "add", "NOTE.md")
    git(env["repo"], "commit", "-q", "-m", "outcome-neutral note")
    with pytest.raises(DecodeAuthorityError, match="is not the freeze commit"):
        v2(env)


def test_R7_freeze_document_deleted_and_readded_is_a_second_freeze(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    git(repo, "rm", "-q", DA.FREEZE_DOC)
    git(repo, "commit", "-q", "-m", "remove freeze")
    (repo / DA.FREEZE_DOC).write_text("FINAL FREEZE study 2\n")
    git(repo, "add", DA.FREEZE_DOC)
    git(repo, "commit", "-q", "-m", "re-freeze")
    with pytest.raises(DecodeAuthorityError, match="exactly one commit"):
        v2(env)


def test_R7_competing_freeze_with_different_content_on_another_branch_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    freeze = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "alt", "HEAD~1")
    (repo / DA.FREEZE_DOC).write_text("A DIFFERENT FREEZE\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "alternative freeze")
    git(repo, "checkout", "-q", "--detach", freeze)
    with pytest.raises(DecodeAuthorityError, match="competing freezes"):
        v2(env)


def test_R7_uncommitted_edit_to_freeze_manifest_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    p = env["repo"] / DA.FREEZE_MANIFEST
    p.write_text(p.read_text().replace('"study_id"', '"note": "x", "study_id"'))
    with pytest.raises(DecodeAuthorityError):
        v2(env)


def test_R7_frozen_file_sha_in_manifest_must_match_committed_bytes(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    m = json.loads((repo / DA.FREEZE_MANIFEST).read_text())
    m["frozen_files"][DA.SCAN_ALLOWLIST] = "f" * 64
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(m))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "freeze with a wrong frozen sha")
    with pytest.raises(DecodeAuthorityError, match="!= frozen"):
        v2(env)


def test_R7_skip_worktree_flag_hiding_an_edited_frozen_file_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    git(repo, "update-index", "--skip-worktree", DA.POPULATION_CSV)
    p = repo / DA.POPULATION_CSV
    p.write_text(p.read_text() + "KEYB,GB,500.0\n")
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    with pytest.raises(DecodeAuthorityError, match="hide working-tree changes"):
        v2(env)


def test_R7_layer_isolated_manifest_bytes_binding(tmp_path, monkeypatch):
    """With the clean-tree layer disabled, the manifest byte binding alone must refuse an on-disk edit."""
    env = build_frozen_repo(tmp_path)
    monkeypatch.setattr(ConfirmationV2Authority, "_check_clean_tree", lambda self: None)
    p = env["repo"] / DA.FREEZE_MANIFEST
    p.write_text(p.read_text().replace('"study_id"', '"note": "harmless-looking edit", "study_id"'))
    with pytest.raises(DecodeAuthorityError, match="not byte-identical"):
        v2(env)


def test_R7_freeze_manifest_committed_before_the_freeze_commit_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    git(repo, "add", DA.FREEZE_MANIFEST)
    git(repo, "commit", "-q", "-m", "manifest first")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "FINAL FREEZE")
    with pytest.raises(DecodeAuthorityError, match="must be added by the freeze commit"):
        v2(env)


def test_untracked_file_in_tree_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    (env["repo"] / "scratch_decoder.py").write_text("print('x')\n")
    with pytest.raises(DecodeAuthorityError, match="not clean"):
        v2(env)


def test_R6_manifest_hash_that_does_not_match_recomputed_candidate_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    m = json.loads((repo / DA.FREEZE_MANIFEST).read_text())
    m["candidate_hash"] = "c" * 64
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(m))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "freeze whose candidate hash is caller-echoed, not real")
    with pytest.raises(DecodeAuthorityError, match="candidate_hash"):
        v2(env)


def test_R6_scan_row_smuggled_into_allowlist_before_freeze_is_caught_by_recomputed_spectrum_hash(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    p = repo / DA.SCAN_ALLOWLIST
    p.write_text(p.read_text() + f"{env['vfile'].name},{sha(env['vfile'])},v3,612.3,KEYA,20\n")
    m = json.loads((repo / DA.FREEZE_MANIFEST).read_text())
    m["frozen_files"][DA.SCAN_ALLOWLIST] = sha(p)          # the bytes are frozen, but the semantic hash was not updated
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(m))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "freeze")
    with pytest.raises(DecodeAuthorityError, match="spectrum_manifest_hash"):
        v2(env)


def test_R6_live_header_recomputation_mismatch_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    live = dict(env["live"], population_key_hash="drifted")
    with pytest.raises(DecodeAuthorityError, match="live header-only recomputation"):
        v2(env, live=live)
    assert not (env["repo"] / DA.ACCESS_RECORD).exists()


def test_R5_record_on_disk_refuses_second_look(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    v2(env)
    shutil.rmtree(env["ledger"])
    git(repo, "reset", "-q", "--soft", "HEAD~1")               # un-commit, record stays on disk
    git(repo, "restore", "--staged", DA.ACCESS_RECORD)
    with pytest.raises(DecodeAuthorityError):
        v2(env)


def test_R5_record_deleted_and_branch_reset_is_still_refused_via_history(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    v2(env)
    shutil.rmtree(env["ledger"])                               # out-of-repo ledger removed too
    git(repo, "reset", "-q", "--hard", "HEAD~1")               # branch and disk back to the freeze commit
    assert not (repo / DA.ACCESS_RECORD).exists()
    with pytest.raises(DecodeAuthorityError, match="existed in git history"):
        v2(env)


def test_R5_record_erased_from_history_is_still_refused_via_out_of_repo_ledger(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    v2(env)
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    git(repo, "reflog", "expire", "--expire=now", "--all")
    git(repo, "gc", "-q", "--prune=now")
    assert git(repo, "log", "--all", "--reflog", "--format=%H", "--", DA.ACCESS_DIR) == ""
    with pytest.raises(DecodeAuthorityError, match="ledger"):
        v2(env)


def test_R5_gitignored_record_left_on_disk_with_history_and_ledger_erased_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    (repo / ".gitignore").write_text(f"{DA.ACCESS_DIR}/\n")       # a record the clean-tree check cannot see
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "FINAL FREEZE")
    for rel in (DA.ACCESS_RECORD, DA.DECODE_INTENTS):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}\n")
        assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
        assert git(repo, "log", "--all", "--reflog", "--format=%H", "--", DA.ACCESS_DIR) == ""
        with pytest.raises(DecodeAuthorityError, match="already holds an access record"):
            v2(env)
        p.unlink()


def test_R7_freeze_manifest_that_was_never_committed_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path, commit_freeze=False)
    repo = env["repo"]
    (repo / ".gitignore").write_text(f"{DA.FREEZE_MANIFEST}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "freeze without its manifest")
    assert (repo / DA.FREEZE_MANIFEST).is_file()
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    with pytest.raises(DecodeAuthorityError, match="not present at commit|must be added by the freeze commit"):
        v2(env)


def test_R5_access_directory_touched_on_any_other_branch_is_refused(tmp_path):
    env = build_frozen_repo(tmp_path)
    repo = env["repo"]
    freeze = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "side")
    (repo / DA.ACCESS_DIR).mkdir(parents=True, exist_ok=True)
    (repo / DA.ACCESS_DIR / "old_record.json").write_text("{}\n")
    git(repo, "add", "-f", DA.ACCESS_DIR)
    git(repo, "commit", "-q", "-m", "an earlier look")
    git(repo, "rm", "-rq", DA.ACCESS_DIR)
    git(repo, "commit", "-q", "-m", "deleted")
    git(repo, "checkout", "-q", "--detach", freeze)
    with pytest.raises(DecodeAuthorityError, match="existed in git history"):
        v2(env)


def test_R4_scan_outside_frozen_allowlist_is_refused_even_in_an_allowlisted_file(tmp_path, spy):
    env = build_frozen_repo(tmp_path)
    auth = v2(env)
    with pytest.raises(DecodeAuthorityError, match="not in the frozen validation scan allowlist"):
        X.decode_selected(env["vfile"], ["v1", "v3"], auth)
    assert spy["n"] == 0


def test_R4_file_not_in_allowlist_is_refused(tmp_path, spy):
    env = build_frozen_repo(tmp_path)
    auth = v2(env)
    stranger = write_mzml(tmp_path / "data" / "pluskal_Z9_id.mzML", VAL)
    with pytest.raises(DecodeAuthorityError, match="not in the frozen validation scan allowlist"):
        X.decode_selected(stranger, ["v1"], auth)
    assert spy["n"] == 0


def test_R4_substituted_file_with_same_ids_is_refused_by_content_hash(tmp_path, spy):
    env = build_frozen_repo(tmp_path)
    auth = v2(env)
    write_mzml(env["vfile"], [("v1", 2, 412.2, 20.0), ("v2", 2, 412.2, 60.0), ("v3", 2, 612.3, 20.0), ("v4", 2, 1.0, 1.0)])
    with pytest.raises(DecodeAuthorityError, match="substituted file"):
        X.decode_selected(env["vfile"], ["v1"], auth)
    assert spy["n"] == 0


def test_R4_allowlisted_id_whose_precursor_differs_from_frozen_is_refused(tmp_path, spy):
    env = build_frozen_repo(tmp_path)
    auth = v2(env)
    auth.allowed[env["vfile"].name]["scans"]["v1"] = 999.0     # simulate a scan whose header disagrees with the freeze
    with pytest.raises(DecodeAuthorityError, match="does not match the frozen scan"):
        X.decode_selected(env["vfile"], ["v1"], auth)
    assert spy["n"] == 0


def test_R3_validation_authority_subclass_is_refused(tmp_path, spy):
    env = build_frozen_repo(tmp_path)

    class Sub(ConfirmationV2Authority):
        pass

    g = Sub(live_header_hashes=env["live"], root=env["repo"], ledger_dir=env["ledger"], code_root=None)
    with pytest.raises(X.OutcomeAccessError, match="requires an authorized"):
        X.decode_selected(env["vfile"], ["v1"], g)
    assert spy["n"] == 0


def test_canonical_hash_matches_candidate_module():
    from muru.wur_v2.candidate import sha256_of
    obj = {"b": [1, 2.5, {"z": None}], "a": "x"}
    assert DA.canonical_json_sha256(obj) == sha256_of(obj)
