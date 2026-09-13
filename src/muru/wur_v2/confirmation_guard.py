"""Confirmation-specific one-look VALIDATION guard (study `muru-v2-msnlib-confirmation-1.0`).

The base `AccessGuard` (`external_guard.py`) has two process-level weaknesses,
identified before this study's first validation-outcome access (no such
access has ever occurred; see `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`):

  1. it refuses a second run only when the access-record file currently
     exists on disk, not when a record for this path ever existed in git
     history and was later deleted;
  2. it verifies the freeze document is committed and the tree is clean, but
     never binds the on-disk freeze bytes to one specific freeze commit, and
     never independently re-verifies that the candidate/comparator/
     population/scaffold-group/spectrum-manifest hashes actually in force at
     construction time still match what the freeze recorded.

`ConfirmationAccessGuard` closes both gaps for this study only. It does not
alter `AccessGuard`'s behavior for ANCHOR_CALIBRATION or any earlier study;
this is an additive, infrastructure/reproducibility hardening layer, not a
scientific change.

Construction, in order:
  (a) historical existence check (`git log --all --follow`) on the record
      path -- refuses if a record for this path has EVER existed in any
      commit on any branch, even if none exists on disk right now;
  (b) current on-disk existence check (defense in depth / crash-resume);
  (c) the freeze manifest (a structured JSON sidecar to the prose freeze
      document) must be tracked at `expected_freeze_commit`, and its
      on-disk bytes right now must be byte-for-byte identical (by sha256)
      to the blob committed at that exact commit;
  (d) the prose freeze document must also be tracked at that commit;
  (e) HEAD must equal the freeze commit, or every path that differs must be
      on an explicit, caller-supplied outcome-neutral allowlist. NOTE
      (governance-review finding, disclosed not silently fixed): this check
      is name-based only -- it does not inspect diff content, so a caller
      could in principle allowlist a path whose change is scientifically
      material. There is no code-level defense against that; the intended,
      and only currently exercised, usage is an EMPTY allowlist with the
      freeze commit made the last commit before this guard ever runs
      ("freeze commit == validation-access HEAD"), so no diff exists to
      allowlist in the first place. Populating this argument for real is an
      honor-system escape hatch, not a verified-safe path;

  (f) the caller's freshly-computed candidate/comparator/population-key/
      scaffold-group/spectrum-manifest hashes must equal the values
      RECORDED IN the freeze manifest (not merely echoed back) -- a
      mismatch means the live data has drifted from what was frozen;
  (g) the tracked tree must be clean.

Only after all of (a)-(g) pass does it write the access record -- including
the study identifier and every verified field -- BEFORE returning
`authorized=True`. If the process crashes after this point, the population
is permanently EXPOSED: resuming means re-running with the same study id,
code SHA, candidate, comparator, population, rules, freeze and access
record, never deleting the record and constructing a fresh guard.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY_ID = "muru-v2-msnlib-confirmation-1.0"


class ConfirmationGuardError(RuntimeError):
    pass


def _git(*args, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def _git_out(*args, root: Path) -> str:
    return _git(*args, root=root).stdout.strip()


def _rel(p: Path, root: Path) -> str:
    return str(Path(p).resolve().relative_to(Path(root).resolve()))


class ConfirmationAccessGuard:
    KIND = "VALIDATION"

    def __init__(self, *, record_path: Path, freeze_doc_path: Path, freeze_manifest_path: Path,
                 expected_freeze_commit: str, actual_candidate_hash: str, actual_comparator_hash: str,
                 actual_population_key_hash: str, actual_scaffold_group_hash: str,
                 actual_spectrum_manifest_hash: str, allowed_spectrum_keys: set,
                 code_allowlist: set[str] | None = None, root: Path = ROOT, study_id: str = STUDY_ID):
        self.root = Path(root)
        self.record_path = Path(record_path)
        self.freeze_doc_path = Path(freeze_doc_path)
        self.freeze_manifest_path = Path(freeze_manifest_path)
        self.allowed = set(allowed_spectrum_keys)
        self.study_id = study_id

        rel_record = _rel(self.record_path, self.root)
        rel_freeze_doc = _rel(self.freeze_doc_path, self.root)
        rel_freeze_manifest = _rel(self.freeze_manifest_path, self.root)

        # (a) historical existence, any branch, any point in time -- not just "does it exist now"
        hist = _git_out("log", "--all", "--follow", "--format=%H", "--", rel_record, root=self.root)
        if hist:
            commits = hist.splitlines()
            raise ConfirmationGuardError(
                f"a {self.KIND} access record has existed in git history at {rel_record} "
                f"({len(commits)} commit(s), most recent {commits[0][:12]}); study {study_id} refuses "
                f"a new first-look record even though no file currently exists on disk")

        # (b) current on-disk existence
        if self.record_path.exists():
            raise ConfirmationGuardError(
                f"{self.KIND} access record already exists at {rel_record}; a second look is prohibited "
                f"(resume the existing study instead of constructing a new guard)")

        # (c) freeze manifest: exact commit binding, byte-identical on-disk content
        self._bind_to_freeze_commit(rel_freeze_manifest, expected_freeze_commit)
        # (d) prose freeze doc: must also be tracked at the freeze commit (informational binding)
        self._bind_to_freeze_commit(rel_freeze_doc, expected_freeze_commit)

        # (e) code-state check: HEAD == freeze commit, or every diff path is outcome-neutral-allowlisted
        current_head = _git_out("rev-parse", "HEAD", root=self.root)
        code_allowlist = set(code_allowlist or [])
        if current_head != expected_freeze_commit:
            diff = _git_out("diff", "--name-only", expected_freeze_commit, current_head, root=self.root)
            changed = set(diff.splitlines()) if diff else set()
            not_allowlisted = changed - code_allowlist
            if not_allowlisted:
                raise ConfirmationGuardError(
                    f"HEAD ({current_head[:12]}) is not the freeze commit ({expected_freeze_commit[:12]}) "
                    f"and {len(not_allowlisted)} changed path(s) are not on the outcome-neutral allowlist: "
                    f"{sorted(not_allowlisted)[:10]}")

        # (f) hash cross-checks against the FROZEN manifest content (not caller-trusted echo)
        frozen = json.loads(self.freeze_manifest_path.read_text())
        checks = [
            ("candidate_hash", actual_candidate_hash),
            ("comparator_hash", actual_comparator_hash),
            ("population_key_hash", actual_population_key_hash),
            ("scaffold_group_hash", actual_scaffold_group_hash),
            ("spectrum_manifest_hash", actual_spectrum_manifest_hash),
        ]
        for field, actual in checks:
            frozen_val = frozen.get(field)
            if frozen_val != actual:
                raise ConfirmationGuardError(
                    f"{field} mismatch: freeze manifest records {frozen_val!r}, actual live value is "
                    f"{actual!r}; the data in force no longer matches what was frozen")

        # (g) clean tracked tree
        dirty = bool(_git_out("status", "--porcelain", "--untracked-files=no", root=self.root))
        if dirty:
            raise ConfirmationGuardError("tracked tree is dirty; commit before validation access")

        self.record = {
            "study_id": study_id, "kind": self.KIND,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_head": current_head, "freeze_commit": expected_freeze_commit,
            "freeze_doc": rel_freeze_doc, "freeze_manifest": rel_freeze_manifest,
            "candidate_hash": actual_candidate_hash, "comparator_hash": actual_comparator_hash,
            "population_key_hash": actual_population_key_hash, "scaffold_group_hash": actual_scaffold_group_hash,
            "spectrum_manifest_hash": actual_spectrum_manifest_hash,
            "n_allowed_spectrum_keys": len(self.allowed), "git_tree_dirty": dirty, "decodes": [],
        }
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        self.record_path.write_text(json.dumps(self.record, indent=1) + "\n")  # written before any decode
        self.authorized = True

    def _bind_to_freeze_commit(self, rel_path: str, expected_freeze_commit: str) -> None:
        show = _git("show", f"{expected_freeze_commit}:{rel_path}", root=self.root)
        if show.returncode != 0:
            raise ConfirmationGuardError(
                f"{rel_path} is not present at freeze commit {expected_freeze_commit}: {show.stderr.strip()}")
        blob_at_commit = show.stdout.encode()
        abs_path = self.root / rel_path
        if not abs_path.exists():
            raise ConfirmationGuardError(f"{rel_path} does not exist on disk")
        on_disk = abs_path.read_bytes()
        # Compare content (not raw bytes of the git-show stdout, which normalizes line endings the
        # same way `git show` always does for text blobs) so an edit -- committed or not -- is caught.
        if on_disk != blob_at_commit:
            raise ConfirmationGuardError(
                f"{rel_path} on disk (sha256 {hashlib.sha256(on_disk).hexdigest()}) is not byte-identical "
                f"to the version committed at freeze commit {expected_freeze_commit} "
                f"(sha256 {hashlib.sha256(blob_at_commit).hexdigest()})")
        tracked = _git("ls-files", "--error-unmatch", rel_path, root=self.root)
        if tracked.returncode != 0:
            raise ConfirmationGuardError(f"{rel_path} is not committed on the current branch")

    def record_decode(self, path, ids):
        bad = [i for i in ids if (Path(path).name, i) not in self.allowed]
        if bad:
            raise ConfirmationGuardError(
                f"{len(bad)} spectra outside the declared {self.KIND} population requested, e.g. {bad[:3]}")
        self.record["decodes"].append({"file": Path(path).name, "n": len(ids)})
        self.record_path.write_text(json.dumps(self.record, indent=1) + "\n")
