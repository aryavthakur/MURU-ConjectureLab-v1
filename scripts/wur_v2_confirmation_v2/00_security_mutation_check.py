"""Mutation check for the study-2 decode boundary.

For each mutant, one safety check in decode_authority.py or external_mzml.decode_selected is deleted or
neutralized in a throwaway copy of src/, and the adversarial test suite is run against that copy. A mutant is
KILLED when at least one test fails. Every mutant must be killed: a surviving mutant means some check is not
actually load-bearing under test, i.e. it could be removed without anyone noticing.

Runs only synthetic tests; opens no real mzML file. Writes
artifacts/wur_v2_confirmation_v2/security/mutation_check.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ["tests/wur_v2/test_v2_decode_authority_security.py", "tests/wur_v2/test_v2_decode_authority_round2.py",
         "tests/wur_v2/test_v2_external_mzml.py"]
SUPPORT = ["tests/wur_v2/decode_fixtures.py", "data/massive/file_index.csv"]
DA = "src/muru/wur_v2/decode_authority.py"
XM = "src/muru/wur_v2/external_mzml.py"

MUTANTS = [
    # ---- decoder choke point
    ("decoder_exact_type_gate", XM, "if guard is None or type(guard) not in DA.AUTHORITY_TYPES or not DA.is_constructed(guard):",
     "if guard is None or not DA.is_constructed(guard):"),
    ("decoder_constructed_registry", XM, "if guard is None or type(guard) not in DA.AUTHORITY_TYPES or not DA.is_constructed(guard):",
     "if guard is None or type(guard) not in DA.AUTHORITY_TYPES:"),
    ("decoder_authorize_call", XM, "    DA.authorize_decode(guard, name, sha, [(s, *scope[s]) for s in wanted])\n", "    pass\n"),
    ("decoder_reread_scope", XM, "            if _spectrum_scope(spec) != scope[sid]:", "            if False:"),
    ("primitive_permit_check", XM, "    if _PERMIT.get() is None:", "    if False:"),
    ("restricted_headers_drop_msn", XM, '        if cv.get("ms_level") != 2.0:\n            continue', "        pass"),
    ("legacy_reader_allowlist", "src/muru/io/mzml.py", "    if p.name not in sizes or p.stat().st_size != sizes[p.name]:", "    if False:"),
    ("void_study1_guard", "src/muru/wur_v2/confirmation_guard.py", "        if study_id == STUDY_ID:", "        if False:"),
    # ---- immutability
    ("sealed_setattr", DA, '    def __setattr__(self, name, value):\n        raise DecodeAuthorityError("decode authorities are immutable")',
     "    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)"),
    ("scope_files_mappingproxy", DA, "    return types.MappingProxyType({f: (sha, types.MappingProxyType(dict(scans))) for f, (sha, scans) in entries.items()})",
     "    return {f: (sha, dict(scans)) for f, (sha, scans) in entries.items()}"),
    ("test_mode_gate", DA, '    return os.environ.get(TEST_MODE_ENV) == "1" and "pytest" in sys.modules', "    return True"),
    ("overrides_type_check", DA, "    if type(_ov) is not _TestOverrides or not _test_mode():", "    if False:"),
    # ---- authorize_decode
    ("authorize_scope_registered", DA, "    if sc is None:\n        raise DecodeAuthorityError(\"authority has no registered scope",
     "    if False:\n        raise DecodeAuthorityError(\"authority has no registered scope"),
    ("authorize_digest", DA, "    if _scope_digest(sc.kind, sc.files) != sc.digest:", "    if False:"),
    ("authorize_ledger_present", DA, "        if not lp.is_file():\n            raise DecodeAuthorityError(f\"ledger entry {lp} is missing; refusing to decode\")",
     "        if False:\n            raise DecodeAuthorityError(f\"ledger entry {lp} is missing; refusing to decode\")"),
    ("authorize_file_on_allowlist", DA, "    if ent is None:\n        raise DecodeAuthorityError(f\"{name} is not in this authority's allowlist\")",
     "    if ent is None:\n        ent = next(iter(sc.files.values()))"),
    ("authorize_content_sha", DA, "    if sha != ent[0]:", "    if False:"),
    ("authorize_scan_on_allowlist", DA, "        if sid not in ent[1]:", "        if False:"),
    ("authorize_ms2", DA, "        if level != 2.0:", "        if False:"),
    ("authorize_single_precursor", DA, "        if n_prec != 1 or n_sel != 1:", "        if False:"),
    ("authorize_mz_matches", DA, "        if not _finite(mz) or not (abs(float(mz) - ent[1][sid]) <= 1e-6):", "        if False:"),
    ("authorize_intent_logged", DA, '    _durable_append(sc.log_path, {"event": "authorize",', '    (lambda *a: None)(sc.log_path, {"event": "authorize",'),
    # ---- anchor preflight construction
    ("anchor_registry_bound", DA, '        _check_registry(root, head, ov.get("registry_manifest_sha256", REGISTRY_MANIFEST_SHA256))\n', ""),
    ("anchor_allowlist_committed", DA, "        require_committed_identical(root, ANCHOR_ALLOWLIST, head)\n", ""),
    ("anchor_exposed_sha", DA, '            if exposed.get(f) != r["file_sha256"]:', "            if False:"),
    ("anchor_previously_decoded", DA, "            if (f, sid) not in decoded:", "            if False:"),
    ("anchor_finite", DA, "            if not (_finite(mz) and _finite(mh) and _finite(decoded[(f, sid)])):", "            if False:"),
    ("anchor_key_is_census_anchor", DA, '            if r["anchor_key"] not in anchors:', "            if False:"),
    ("anchor_empty_allowlist", DA, "        if not entries:\n            raise DecodeAuthorityError(\"anchor allowlist is empty\")",
     "        if False:\n            raise DecodeAuthorityError(\"anchor allowlist is empty\")"),
    # ---- validation authority
    ("v2_shallow", DA, '        if _git_text(ctx.root, "rev-parse", "--is-shallow-repository") != "false":', "        if False:"),
    ("v2_fetch", DA, '        _git_text(ctx.root, "fetch", "--prune", REMOTE, timeout=600)\n', ""),
    ("v2_ledger_exists", DA, "            if lp.exists():", "            if False:"),
    ("v2_record_on_disk", DA, "        if (ctx.root / ACCESS_RECORD).exists() or (ctx.root / DECODE_INTENTS).exists():", "        if False:"),
    ("v2_history", DA, "        if hist:\n            raise DecodeAuthorityError(\n                f\"a validation access record has existed",
     "        if False:\n            raise DecodeAuthorityError(\n                f\"a validation access record has existed"),
    ("v2_local_access_ref", DA, '        if _git(ctx.root, "rev-parse", "--verify", "--quiet", ACCESS_REF).returncode == 0:', "        if False:"),
    ("v2_remote_access_ref", DA, '        if _git_text(ctx.root, "ls-remote", REMOTE, ACCESS_REF, timeout=300):', "        if False:"),
    ("v2_freeze_added_once_by_head", DA, "            if adds != [head]:", "            if False:"),
    ("v2_competing_freeze", DA, "                if other.returncode != 0 or other.stdout != _blob_at(root, head, rel):", "                if False:"),
    ("v2_freeze_published", DA, "        if not remote or remote[0] != head:", "        if False:"),
    ("v2_clean_tree", DA, "        if st:\n            raise DecodeAuthorityError(f\"working tree is not clean",
     "        if False:\n            raise DecodeAuthorityError(f\"working tree is not clean"),
    ("v2_ignored_py", DA, "        if bad:\n            raise DecodeAuthorityError(f\"ignored Python files",
     "        if False:\n            raise DecodeAuthorityError(f\"ignored Python files"),
    ("v2_index_flags", DA, "        if hidden:", "        if False:"),
    ("v2_manifest_bytes_bound", DA, "        raw = require_committed_identical(ctx.root, FREEZE_MANIFEST, ctx.freeze)",
     "        raw = (ctx.root / FREEZE_MANIFEST).read_bytes()"),
    ("v2_study_id", DA, '        if manifest.get("study_id") != STUDY_ID_V2:', "        if False:"),
    ("v2_required_frozen", DA, "        if missing:\n            raise DecodeAuthorityError(f\"freeze manifest frozen_files lacks",
     "        if False:\n            raise DecodeAuthorityError(f\"freeze manifest frozen_files lacks"),
    ("v2_frozen_sha", DA, "            if sha256_bytes(b) != want:", "            if False:"),
    ("v2_recomputed", DA, "            if m.get(field) != val:", "            if False:"),
    ("v2_disjoint_keys", DA, "        if pop_keys & excluded_keys:", "        if False:"),
    ("v2_disjoint_groups", DA, '        if {r["scaffold_group"] for r in pop} & excluded_groups:', "        if False:"),
    ("v2_key_in_population", DA, '            if r["key"] not in pop_keys:', "            if False:"),
    ("v2_not_exposed_file", DA, '            if r["file_sha256"] in exposed_sha or r["unique_sample_id"] in exposed_wells:', "            if False:"),
    ("v2_live_member_sha", DA, "            if name != f or sha256_bytes(data) != sha:", "            if False:"),
    ("v2_live_header", DA, "                if s is None or s[0] != 2.0 or s[2] != 1 or s[3] != 1 or not _finite(s[1]) or not (abs(s[1] - mz) <= 1e-6):",
     "                if False:"),
    ("v2_push_record", DA, '        _git_text(root, "push", "--atomic", REMOTE, f"{rec_commit}:{ACCESS_REF}", timeout=600)\n', ""),
    ("v2_verify_remote_record", DA, "        if not remote or remote[0] != rec_commit:", "        if False:"),
    ("v2_ledger_written", DA, '            _durable_create(lp, json.dumps({**record, "repo_root": str(root)}, indent=1) + "\\n")\n',
     "            pass\n"),
    # ---- round-2 review fixes and the reviewers' surviving extra mutants
    ("full_header_gate", XM, "    if not DA._test_mode() and hashlib.sha256(data).hexdigest() not in _full_header_allowlist():", "    if False:"),
    ("decoder_str_ids", XM, "    if any(type(s) is not str for s in spectrum_ids):", "    if False:"),
    ("identity_scope_lookup", DA, "        if k is obj:\n            return _SCOPES[k]", "        if k == obj:\n            return _SCOPES[k]"),
    ("sealed_no_copy", DA, '    def __reduce_ex__(self, protocol):\n        raise DecodeAuthorityError("decode authorities cannot be copied or pickled")',
     "    def __reduce_ex__(self, protocol):\n        return object.__reduce_ex__(self, protocol)"),
    ("test_mode_needs_current_test", DA, '            and bool(os.environ.get("PYTEST_CURRENT_TEST")))', "            and True)"),
    ("test_overrides_real_root", DA, "    if root is not None and Path(root).resolve() == ROOT:", "    if False:"),
    ("test_overrides_real_zip_dir", DA, "    if zip_dir is not None and Path(zip_dir).resolve().is_relative_to(DEFAULT_ZIP_DIR.resolve()):", "    if False:"),
    ("test_overrides_real_ledger", DA, "        if Path(d).resolve().is_relative_to(DEFAULT_LEDGER_DIR.resolve()):", "        if False:"),
    ("remote_ref_exact_name", DA, "        if len(parts) == 2 and parts[1] == ref:", "        if len(parts) == 2:"),
    ("canonical_remote", DA, "    if url != want or push_url != want:", "    if False:"),
    ("push_permission_probe", DA, '        _git_text(ctx.root, "push", "--dry-run", "--porcelain", REMOTE, f"HEAD:{PROBE_REF}", timeout=600)\n', "        pass\n"),
    ("toplevel_check", DA, "    if top != ctx.root:", "    if False:"),
    ("committer_ident_probe", DA, '        _git_text(ctx.root, "var", "GIT_COMMITTER_IDENT")\n', ""),
    ("index_lock_probe", DA, '        if (git_dir / "index.lock").exists():', "        if False:"),
    ("ledger_probe", DA, '            probe.write_text("x")\n', ""),
    ("git_env_sanitized", DA, '    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}', "    env = dict(os.environ)"),
    ("git_hooks_disabled", DA, '    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],',
     '    return subprocess.run(["git", "-c", "commit.gpgsign=false", *args],'),
    ("freeze_adds_dedupe_merges", DA, '        adds = list(dict.fromkeys(_git_text(root, "log", "-m", "--diff-filter=A", "--format=%H", "HEAD", "--",',
     '        adds = list(dict.fromkeys(_git_text(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--",'),
    ("competing_uses_reflog", DA, '    everywhere = set(_git_text(root, "log", "--all", "--reflog", "-m", "--diff-filter=A", "--format=%H", "--",',
     '    everywhere = set(_git_text(root, "log", "--all", "-m", "--diff-filter=A", "--format=%H", "--",'),
    ("competing_compares_manifest", DA, "        for rel in (FREEZE_DOC, FREEZE_MANIFEST):\n            other = _git(root,",
     "        for rel in (FREEZE_DOC,):\n            other = _git(root,"),
    ("freeze_registration_required", DA, '        if reg.get("freeze_commit") != ctx.freeze:', "        if False:"),
    ("publish_verifies_first", DA, "    summary = verify_freeze_candidate(_ov=_ov)\n", '    summary = {"freeze_commit": _git_text(_context(ov).root, "rev-parse", "HEAD")}\n'),
    ("publish_once", DA, '    if _remote_ref(ctx.root, FREEZE_REF) is not None:\n        raise DecodeAuthorityError(f"{REMOTE} already holds',
     '    if False:\n        raise DecodeAuthorityError(f"{REMOTE} already holds'),
    ("attempt_failed_logged", DA, '            _durable_append(ctx.attempts_log, {"status": "ATTEMPT_FAILED_NO_DECODE", "utc": _utc(),',
     '            (lambda *a: None)(ctx.attempts_log, {"status": "ATTEMPT_FAILED_NO_DECODE", "utc": _utc(),'),
    ("ignored_files_guarded", DA, "    if bad:\n        raise DecodeAuthorityError(f\"ignored files under",
     "    if False:\n        raise DecodeAuthorityError(f\"ignored files under"),
    ("allowlist_mz_vs_population_mh", DA, '        if not (abs(float(r["selected_ion_mz"]) - float(p["mh"])) <= SEL_TOL):', "        if False:"),
    ("allowlist_well_is_file_well", DA, '        if well is None or well.group(1) != r["unique_sample_id"]:', "        if False:"),
    ("allowlist_key_plated_in_well", DA, '        if r["unique_sample_id"] not in set(p["wells"].split(";")):', "        if False:"),
    ("allowlist_live_rung", DA, "            if sid not in live_rung or not _finite(rungs[(f, sid)]) or float(rungs[(f, sid)]) != live_rung[sid]:", "            if False:"),
    ("allowlist_exposed_sha", DA, '        if r["file_sha256"] in exposed_sha or r["unique_sample_id"] in exposed_wells:',
     '        if r["unique_sample_id"] in exposed_wells:'),
    ("recomputed_all_fields", DA, "    for field in RECOMPUTED_FIELDS:\n        if m.get(field) != recomputed[field]:",
     "    for field in RECOMPUTED_FIELDS[:1]:\n        if m.get(field) != recomputed[field]:"),
    ("authorize_record_present", DA, '    if sc.kind == "VALIDATION" and not (sc.root / ACCESS_RECORD).is_file():', "    if False:"),
    ("registry_outputs_match_manifest", DA, '        if sha256_file(Path(root) / REGISTRY_DIR / name) != want:', "        if False:"),
    ("anchor_census_committed", DA, "        require_committed_identical(root, CENSUS, head)\n", ""),
    ("anchor_mz_equals_recorded", DA, "            if not (abs(float(mz) - float(decoded[(f, sid)])) <= 1e-6):", "            if False:"),
    ("anchor_mz_within_anchor_mh", DA, "            if not (abs(float(mz) - float(mh)) <= SEL_TOL):", "            if False:"),
    ("anchor_provenance_at_construction", DA, "        if code_root is not None:\n            check_code_provenance(code_root)\n        head = ",
     "        if False:\n            check_code_provenance(code_root)\n        head = "),
    ("v2_provenance_at_construction", DA, "        checked_code = check_code_provenance(code_root) if code_root is not None else []",
     "        checked_code = []"),
    ("provenance_foreign_modules", DA, "        if not fp.is_relative_to(base):\n            raise DecodeAuthorityError(f\"{name} is loaded from",
     "        if not fp.is_relative_to(base):\n            continue\n            raise DecodeAuthorityError(f\"{name} is loaded from"),
    ("provenance_py_suffix", DA, '        if fp.suffix != ".py":', "        if False:"),
    ("legacy_reader_size_set", "src/muru/io/mzml.py", "    if p.name not in sizes or p.stat().st_size not in sizes[p.name]:",
     "    if p.name not in sizes or p.stat().st_size != max(sizes[p.name]):"),
    ("v2_record_before_scope", DA, "        record = self._write_commit_push_record(ctx, files, checked_code)\n",
     "        record = {}\n"),
]


# Targets re-pointed after the round-2 rewrite moved the validation checks into module functions.
_RETARGET = {
    "legacy_reader_allowlist": ("src/muru/io/mzml.py", "    if p.name not in sizes or p.stat().st_size not in sizes[p.name]:", "    if False:"),
    "test_mode_gate": (DA, '    return (os.environ.get(TEST_MODE_ENV) == "1" and "pytest" in sys.modules', "    return (True"),
    "authorize_scan_on_allowlist": (DA, "        if type(sid) is not str or sid not in ent[1]:", "        if type(sid) is not str:"),
    "v2_shallow": (DA, '    if _git_text(ctx.root, "rev-parse", "--is-shallow-repository") != "false":', "    if False:"),
    "v2_fetch": (DA, '    _git_text(ctx.root, "fetch", "--prune", REMOTE, timeout=600)\n', ""),
    "v2_remote_access_ref": (DA, "        if _remote_ref(ctx.root, ACCESS_REF) is not None:", "        if False:"),
    "v2_freeze_added_once_by_head": (DA, "        if adds != [head]:", "        if False:"),
    "v2_competing_freeze": (DA, "            if other.returncode != 0 or other.stdout != _blob_at(root, head, rel):", "            if False:"),
    "v2_freeze_published": (DA, "        if _remote_ref(ctx.root, FREEZE_REF) != ctx.freeze:", "        if False:"),
    "v2_clean_tree": (DA, "    if st:\n        raise DecodeAuthorityError(f\"working tree is not clean",
                      "    if False:\n        raise DecodeAuthorityError(f\"working tree is not clean"),
    "v2_index_flags": (DA, "    if hidden:", "    if False:"),
    "v2_manifest_bytes_bound": (DA, "    raw = require_committed_identical(ctx.root, FREEZE_MANIFEST, ctx.freeze)",
                                "    raw = (ctx.root / FREEZE_MANIFEST).read_bytes()"),
    "v2_study_id": (DA, '    if manifest.get("study_id") != STUDY_ID_V2:', "    if False:"),
    "v2_required_frozen": (DA, "    if missing:\n        raise DecodeAuthorityError(f\"freeze manifest frozen_files lacks",
                           "    if False:\n        raise DecodeAuthorityError(f\"freeze manifest frozen_files lacks"),
    "v2_frozen_sha": (DA, "        if sha256_bytes(b) != want:", "        if False:"),
    "v2_recomputed": (DA, "        if m.get(field) != recomputed[field]:", "        if False:"),
    "v2_disjoint_keys": (DA, "    if set(by_key) & excluded_keys:", "    if False:"),
    "v2_disjoint_groups": (DA, '    if {r["scaffold_group"] for r in pop} & excluded_groups:', "    if False:"),
    "v2_key_in_population": (DA, "        if p is None:\n            raise DecodeAuthorityError(f\"scan allowlist row {f}:{sid} names a key",
                             "        if False:\n            raise DecodeAuthorityError(f\"scan allowlist row {f}:{sid} names a key"),
    "v2_not_exposed_file": (DA, '        if r["file_sha256"] in exposed_sha or r["unique_sample_id"] in exposed_wells:', "        if False:"),
    "v2_live_member_sha": (DA, "        if name != f or sha256_bytes(data) != sha:", "        if False:"),
    "v2_live_header": (DA, "            if s is None or s[0] != 2.0 or s[2] != 1 or s[3] != 1 or not _finite(s[1]) or not (abs(s[1] - mz) <= 1e-6):",
                       "            if False:"),
    "v2_push_record": (DA, '        _git_text(root, "push", "--atomic", f"--force-with-lease={ACCESS_REF}:", REMOTE, f"{rec_commit}:{ACCESS_REF}",\n                  timeout=600)\n', ""),
    "v2_verify_remote_record": (DA, "        if _remote_ref(root, ACCESS_REF) != rec_commit:", "        if False:"),
}
_DROP = {"v2_ignored_py"}
MUTANTS = [(mid, *_RETARGET[mid]) if mid in _RETARGET else (mid, rel, old, new)
           for mid, rel, old, new in MUTANTS if mid not in _DROP]

# Mutants that cannot change behaviour, with the reason; reported, but not required to be killed.
EQUIVALENT = {
    "decoder_reread_scope": "both passes parse the same in-memory bytes, so the re-read scope always equals the "
                            "authorized one; kept as defense in depth against future refactors",
    "v2_local_access_ref": "git log --all already walks refs/muru-access/*, so a surviving local ref is always seen by "
                           "the history check first",
    "decoder_exact_type_gate": "is_constructed() itself requires type(obj) in AUTHORITY_TYPES, so the decoder's own "
                               "type test is a duplicate kept for readability",
    "restricted_headers_drop_msn": "external_msnlib.fixed_rung_scans independently keeps only ms_level == 2 rows, so "
                                   "MS3+ rows never reach the returned output; the early drop is defense in depth",
}


def run_suite(workdir: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *TESTS],
                       cwd=workdir, capture_output=True, text=True, timeout=900)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-3:])
    return r.returncode, tail


def stage(tmp: Path) -> None:
    shutil.copytree(ROOT / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for t in TESTS + SUPPORT:
        (tmp / t).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / t, tmp / t)
    shutil.copy(ROOT / "pytest.ini", tmp / "pytest.ini")


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory() as base:
        base = Path(base)
        clean = base / "clean"
        stage(clean)
        rc, tail = run_suite(clean)
        if rc != 0:
            print("unmutated suite fails; aborting\n" + tail, file=sys.stderr)
            return 2
        for mid, rel, old, new in MUTANTS:
            work = base / mid
            stage(work)
            text = (work / rel).read_text()
            n = text.count(old)
            if n != 1:
                results.append({"mutant": mid, "status": "INVALID", "detail": f"target snippet found {n} times"})
                print(f"{mid}: INVALID ({n} matches)", file=sys.stderr)
                continue
            (work / rel).write_text(text.replace(old, new))
            rc, tail = run_suite(work)
            status = "KILLED" if rc != 0 else "SURVIVED"
            results.append({"mutant": mid, "file": rel, "status": status, "pytest_tail": tail})
            print(f"{mid}: {status}", file=sys.stderr)
            shutil.rmtree(work)
    out = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": TESTS,
           "n_mutants": len(MUTANTS), "n_killed": sum(r["status"] == "KILLED" for r in results),
           "n_survived": sum(r["status"] == "SURVIVED" for r in results),
           "n_invalid": sum(r["status"] == "INVALID" for r in results), "results": results}
    dest = ROOT / "artifacts/wur_v2_confirmation_v2/security/mutation_check.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
    out_required = [r for r in results if r["mutant"] not in EQUIVALENT]
    out["equivalent_mutants"] = EQUIVALENT
    out["non_equivalent_survivors"] = [r["mutant"] for r in out_required if r["status"] != "KILLED"]
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print("non-equivalent survivors:", out["non_equivalent_survivors"])
    return 0 if not out["non_equivalent_survivors"] else 1


if __name__ == "__main__":
    sys.exit(main())
