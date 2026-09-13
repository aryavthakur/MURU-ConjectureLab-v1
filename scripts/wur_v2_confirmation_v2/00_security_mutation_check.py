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
TESTS = ["tests/wur_v2/test_v2_decode_authority_security.py", "tests/wur_v2/test_v2_external_mzml.py"]
DA = "src/muru/wur_v2/decode_authority.py"
XM = "src/muru/wur_v2/external_mzml.py"

MUTANTS = [
    ("decoder_exact_type_gate", XM,
     "if (guard is None or type(guard) not in _authority_types() or not _constructed(guard)",
     "if (guard is None or not _constructed(guard)"),
    ("decoder_authorized_flag", XM, "            or getattr(guard, \"authorized\", False) is not True):", "            ):"),
    ("v2_index_flags_hiding_changes", DA, "        if hidden:", "        if False:"),
    ("decoder_constructed_registry", XM,
     "if (guard is None or type(guard) not in _authority_types() or not _constructed(guard)",
     "if (guard is None or type(guard) not in _authority_types()"),
    ("authority_code_provenance_outside_root", DA,
     "            raise DecodeAuthorityError(f\"{name} is loaded from {fp}, outside {base}; refusing (shadowed or foreign code)\")",
     "            continue"),
    ("authority_code_provenance_bytes", DA,
     "        require_committed_identical(code_root, str(rel), head)\n\n\n", "        pass\n\n\n"),
    ("v2_manifest_added_by_freeze_commit", DA, "        if manifest_adds != [head]:", "        if False:"),
    ("legacy_reader_refuses_external", "src/muru/io/mzml.py",
     "    if any(m in lowered for m in _EXTERNAL_MARKERS):", "    if False:"),
    ("void_study1_guard", "src/muru/wur_v2/confirmation_guard.py", "        if study_id == STUDY_ID:", "        if False:"),
    ("decoder_authorize_call", XM, "    guard.authorize(path, requests)\n", "    pass\n"),
    ("decoder_reread_header_scope", XM,
     "            if _spectrum_header_scope(spec) != scope[sid]:",
     "            if False:"),
    ("anchor_precursor_tolerance", DA, "            if d[i] > SEL_TOL:", "            if False:"),
    ("anchor_ms2_only", DA, "            if level != 2.0 and level != 2:\n                raise DecodeAuthorityError(f\"{path.name}:{sid} is not an MS2 scan",
     "            if False:\n                raise DecodeAuthorityError(f\"{path.name}:{sid} is not an MS2 scan"),
    ("anchor_file_on_allowlist", DA,
     "        if ent is None:\n            raise DecodeAuthorityError(f\"{path.name} is not on the anchor preflight allowlist\")",
     "        if ent is None:\n            ent = next(iter(self.files.values()))"),
    ("anchor_content_sha", DA, "        if sha != ent[\"sha256\"]:\n            raise DecodeAuthorityError(\n                f\"{path.name} content sha256 {sha[:16]} does not match",
     "        if False:\n            raise DecodeAuthorityError(\n                f\"{path.name} content sha256 {sha[:16]} does not match"),
    ("anchor_exposure_registry_membership", DA, "        if not_exposed:", "        if False:"),
    ("anchor_allowlist_committed", DA, "        require_committed_identical(self.root, allowlist_rel, head)\n", ""),
    ("v2_ledger_check", DA, "        if self.ledger_path.exists():", "        if False:"),
    ("v2_record_on_disk_check", DA,
     "        if (self.root / ACCESS_RECORD).exists() or (self.root / DECODE_INTENTS).exists():", "        if False:"),
    ("v2_history_check", DA, "        if hist:\n            raise DecodeAuthorityError(\n                f\"a validation access record has existed",
     "        if False:\n            raise DecodeAuthorityError(\n                f\"a validation access record has existed"),
    ("v2_single_freeze_add", DA, "        if len(reachable) != 1:", "        if False:"),
    ("v2_head_is_freeze", DA, "        if reachable[0] != head:", "        if False:"),
    ("v2_competing_freeze", DA, "                if other.returncode != 0 or other.stdout != _blob_at(self.root, head, rel):",
     "                if False:"),
    ("v2_clean_tree", DA, "        if st:\n            raise DecodeAuthorityError(f\"working tree is not clean",
     "        if False:\n            raise DecodeAuthorityError(f\"working tree is not clean"),
    ("v2_manifest_bytes_bound", DA, "        raw = require_committed_identical(self.root, FREEZE_MANIFEST, self.freeze_commit)",
     "        raw = (self.root / FREEZE_MANIFEST).read_bytes()"),
    ("v2_frozen_file_sha", DA, "            if sha256_bytes(b) != want:", "            if False:"),
    ("v2_recomputed_hashes", DA, "            if m.get(field) != val:", "            if False:"),
    ("v2_live_header_hashes", DA, "            if (live_header_hashes or {}).get(field) != m.get(field):", "            if False:"),
    ("v2_commit_record_before_authorized", DA,
     "        _git_text(self.root, \"add\", \"-f\", \"--\", ACCESS_RECORD)\n", ""),
    ("v2_ledger_written", DA,
     "        _durable_create(self.ledger_path, json.dumps({**record, \"repo_root\": str(self.root)}, indent=1) + \"\\n\")\n", ""),
    ("v2_scan_allowlist_membership", DA, "            if sid not in ent[\"scans\"]:", "            if False:"),
    ("v2_file_on_allowlist", DA,
     "        if ent is None:\n            raise DecodeAuthorityError(f\"{path.name} is not in the frozen validation scan allowlist\")",
     "        if ent is None:\n            ent = next(iter(self.allowed.values()))"),
    ("v2_content_sha", DA, "        if sha != ent[\"sha256\"]:\n            raise DecodeAuthorityError(\n                f\"{path.name} content sha256 {sha[:16]} != frozen",
     "        if False:\n            raise DecodeAuthorityError(\n                f\"{path.name} content sha256 {sha[:16]} != frozen"),
    ("v2_precursor_matches_frozen", DA,
     "            if (level != 2.0 and level != 2) or mz is None or abs(float(mz) - ent[\"scans\"][sid]) > 1e-6:",
     "            if False:"),
    ("v2_intent_logged_before_decode", DA,
     "        _durable_append(self.root / DECODE_INTENTS, {\"file\": path.name,",
     "        (lambda *a: None)(self.root / DECODE_INTENTS, {\"file\": path.name,"),
]


def run_suite(workdir: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *TESTS],
                       cwd=workdir, capture_output=True, text=True, timeout=900)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-3:])
    return r.returncode, tail


def stage(tmp: Path) -> None:
    shutil.copytree(ROOT / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for t in TESTS:
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
    return 0 if out["n_killed"] == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
