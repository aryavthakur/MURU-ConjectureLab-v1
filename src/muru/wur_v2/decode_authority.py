"""Decode authorities for MSnLib confirmation study 2 (`muru-v2-msnlib-confirmation-2.0`).

Why this module exists. Confirmation sample 1 was burned on 2026-09-13 when a
parser-preflight script passed a duck-typed guard (`authorized = True`, no
scope) to `external_mzml.decode_selected` and selected scans by file position
in pooled wells. Every scope rule lived in the caller. This module moves scope
into the decode path itself:

* `external_mzml.decode_selected` accepts ONLY an object whose exact type is
  `AnchorPreflightAuthority` or `ConfirmationV2Authority` (no duck types, no
  subclasses, no legacy `AccessGuard`, no void study-1 guard).
* The decoder reads each requested scan's selected-ion m/z and MS level from
  the file itself (arrays removed first) and hands (spectrum_id, m/z, level)
  to `authorize` BEFORE any binary array is decoded; it re-reads the m/z from
  the same spectrum element immediately before decoding it.
* `AnchorPreflightAuthority` authorizes only files whose CONTENT sha256 is on
  the committed anchor allowlist and in the committed exposure registry's
  exposed-file list, and only scans whose precursor is within 0.01 Da of an
  allowlisted anchor [M+H]+ plated in that file's well. A caller cannot widen
  scope by passing other ids: the check is on the file's own header values.
* `ConfirmationV2Authority` can only be constructed at the final freeze
  commit and writes, fsyncs and commits its access record (plus an
  out-of-repo ledger entry) before it becomes authorized. It loads the
  validation scan allowlist itself from the frozen, commit-bound CSV and
  recomputes every frozen hash itself.

Threat model. This protects against honest mistakes and careless reuse (the
2026-09-13 failure class) and makes deliberate circumvention require
conspicuous new code (a new decoder, a `root=`/`ledger_dir=` override in a
study script, or an edit to this module), which the static choke-point tests
and the review process are designed to catch. It cannot stop a deliberately
malicious operator who writes their own base64 decoder; nothing in-process
can.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import weakref
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEL_TOL = 0.01

STUDY_ID_V2 = "muru-v2-msnlib-confirmation-2.0"
V2_DIR = "artifacts/wur_v2_confirmation_v2"
ANCHOR_ALLOWLIST = f"{V2_DIR}/anchor_preflight/anchor_preflight_allowlist.csv"
EXPOSED_FILES = f"{V2_DIR}/exposure_registry/exposed_files.csv"
FREEZE_DOC = "MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md"
FREEZE_MANIFEST = f"{V2_DIR}/freeze/freeze_manifest.json"
SCAN_ALLOWLIST = f"{V2_DIR}/freeze/validation_scan_allowlist.csv"
POPULATION_CSV = f"{V2_DIR}/freeze/validation_population.csv"
ACCESS_DIR = f"{V2_DIR}/access"
ACCESS_RECORD = f"{ACCESS_DIR}/validation_access_record.json"
DECODE_INTENTS = f"{ACCESS_DIR}/validation_decode_intents.jsonl"
CANDIDATE_JSON = "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json"
COMPARATOR_JSON = "artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json"
DEFAULT_LEDGER_DIR = Path.home() / ".muru" / "access_ledger"

# Semantic hashes the freeze manifest must carry and the authority recomputes.
LIVE_HEADER_HASH_FIELDS = ("population_key_hash", "scaffold_group_hash", "spectrum_manifest_hash")


class DecodeAuthorityError(RuntimeError):
    pass


# Instances are added only as the last statement of a successful __init__. The decoder requires membership,
# so an object made with __new__ (skipping every construction check) is refused even though its type is exact.
_CONSTRUCTED: "weakref.WeakSet" = weakref.WeakSet()


def is_constructed(obj) -> bool:
    try:
        return obj in _CONSTRUCTED
    except TypeError:
        return False


# ---------------------------------------------------------------------------------------------
# small, separately testable helpers
# ---------------------------------------------------------------------------------------------

def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True)


def _git_text(root: Path, *args: str) -> str:
    r = _git(root, *args)
    if r.returncode != 0:
        raise DecodeAuthorityError(f"git {' '.join(args)} failed: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout.decode().strip()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lines(lines) -> str:
    """Program convention: sorted items joined by newline, no trailing newline."""
    return sha256_bytes("\n".join(sorted(lines)).encode())


def canonical_json_sha256(obj) -> str:
    """Identical to muru.wur_v2.candidate.sha256_of (asserted by test), without its heavy imports."""
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())


def _blob_at(root: Path, commit: str, rel: str) -> bytes:
    r = _git(root, "show", f"{commit}:{rel}")
    if r.returncode != 0:
        raise DecodeAuthorityError(f"{rel} is not present at commit {commit[:12]}")
    return r.stdout


def require_committed_identical(root: Path, rel: str, commit: str) -> bytes:
    """On-disk bytes of `rel` must equal the blob committed at `commit`. Returns the bytes."""
    p = root / rel
    if not p.is_file():
        raise DecodeAuthorityError(f"{rel} does not exist on disk")
    on_disk = p.read_bytes()
    blob = _blob_at(root, commit, rel)
    if on_disk != blob:
        raise DecodeAuthorityError(
            f"{rel} on disk (sha256 {sha256_bytes(on_disk)[:16]}) is not byte-identical to commit {commit[:12]} "
            f"(sha256 {sha256_bytes(blob)[:16]})")
    return on_disk


def _durable_append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (json.dumps(obj, sort_keys=True) + "\n").encode())
        os.fsync(fd)
    finally:
        os.close(fd)


def _durable_create(path: Path, text: str) -> None:
    """Create exclusively (fails if the file exists) and fsync file and directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, text.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def check_code_provenance(code_root: Path, modules=None, main_file=None) -> None:
    """The code doing the decoding must be the committed code of `code_root`.

    Every loaded muru module file must live under code_root/src (so nothing earlier on sys.path, such as
    another session's scratchpad, shadows the package) and be byte-identical to its HEAD blob; the running
    script (__main__) must also be a committed, unmodified file under code_root.
    """
    code_root = Path(code_root).resolve()
    head = _git_text(code_root, "rev-parse", "HEAD")
    if modules is None:
        modules = {n: getattr(m, "__file__", None) for n, m in list(sys.modules.items())
                   if n == "muru" or n.startswith("muru.")}
    if main_file is None:
        main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    src = code_root / "src"
    files = [(n, f) for n, f in sorted(modules.items()) if f]
    if not any(n == "muru.wur_v2.decode_authority" for n, _ in files):
        raise DecodeAuthorityError("muru.wur_v2.decode_authority is not among the modules being checked")
    if main_file is not None:
        files.append(("__main__", main_file))
    for name, f in files:
        fp = Path(f).resolve()
        base = code_root if name == "__main__" else src
        try:
            rel = fp.relative_to(code_root)
            fp.relative_to(base)
        except ValueError:
            raise DecodeAuthorityError(f"{name} is loaded from {fp}, outside {base}; refusing (shadowed or foreign code)")
        require_committed_identical(code_root, str(rel), head)


# ---------------------------------------------------------------------------------------------
# Anchor parser preflight
# ---------------------------------------------------------------------------------------------

class AnchorPreflightAuthority:
    """Authorizes decodes of already-exposed anchor spectra only.

    Allowlist CSV columns: file (basename), file_sha256, unique_sample_id, anchor_key, anchor_mh.
    Exposed-file CSV columns (exposure registry): file, file_sha256, unique_sample_id, events.
    Both must be tracked and byte-identical to HEAD.
    """
    KIND = "ANCHOR_PREFLIGHT"

    def __init__(self, *, log_path: Path, root: Path = ROOT, code_root: Path | None = ROOT,
                 allowlist_rel: str = ANCHOR_ALLOWLIST, exposed_files_rel: str = EXPOSED_FILES):
        self.authorized = False
        self.root = Path(root)
        if code_root is not None:
            check_code_provenance(code_root)
        head = _git_text(self.root, "rev-parse", "HEAD")
        allow_rows = _read_csv(self.root / allowlist_rel) if (self.root / allowlist_rel).is_file() else None
        if allow_rows is None:
            raise DecodeAuthorityError(f"anchor allowlist {allowlist_rel} does not exist")
        require_committed_identical(self.root, allowlist_rel, head)
        require_committed_identical(self.root, exposed_files_rel, head)
        exposed_sha = {r["file_sha256"] for r in _read_csv(self.root / exposed_files_rel)}

        self.files: dict[str, dict] = {}
        for r in allow_rows:
            ent = self.files.setdefault(r["file"], {"sha256": r["file_sha256"], "mh": [], "keys": []})
            if ent["sha256"] != r["file_sha256"]:
                raise DecodeAuthorityError(f"anchor allowlist lists two sha256 values for {r['file']}")
            ent["mh"].append(float(r["anchor_mh"]))
            ent["keys"].append(r["anchor_key"])
        if not self.files:
            raise DecodeAuthorityError("anchor allowlist is empty")
        not_exposed = sorted(f for f, e in self.files.items() if e["sha256"] not in exposed_sha)
        if not_exposed:
            raise DecodeAuthorityError(
                f"{len(not_exposed)} anchor-allowlisted file(s) are not in the exposure registry's exposed-file "
                f"list, e.g. {not_exposed[:3]}; anchor preflight may only touch already-exposed files")
        self.log_path = Path(log_path)
        self.head = head
        self._sha_cache: dict[tuple, str] = {}
        _durable_append(self.log_path, {"event": "construct", "kind": self.KIND, "git_head": head,
                                         "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                         "n_files": len(self.files)})
        self.authorized = True
        _CONSTRUCTED.add(self)

    def _file_sha(self, path: Path) -> str:
        st = path.stat()
        k = (str(path.resolve()), st.st_size, st.st_mtime_ns)
        if k not in self._sha_cache:
            self._sha_cache[k] = sha256_file(path)
        return self._sha_cache[k]

    def authorize(self, path, requests) -> None:
        """requests: iterable of (spectrum_id, selected_ion_mz, ms_level) read from the file by the decoder."""
        if not self.authorized:
            raise DecodeAuthorityError("anchor preflight authority is not authorized")
        path = Path(path)
        ent = self.files.get(path.name)
        if ent is None:
            raise DecodeAuthorityError(f"{path.name} is not on the anchor preflight allowlist")
        sha = self._file_sha(path)
        if sha != ent["sha256"]:
            raise DecodeAuthorityError(
                f"{path.name} content sha256 {sha[:16]} does not match the allowlisted anchor file "
                f"{ent['sha256'][:16]} (renamed or substituted file)")
        approved = []
        for sid, mz, level in requests:
            if level != 2.0 and level != 2:
                raise DecodeAuthorityError(f"{path.name}:{sid} is not an MS2 scan (ms_level={level!r})")
            if mz is None:
                raise DecodeAuthorityError(f"{path.name}:{sid} has no selected-ion m/z")
            d = [abs(float(mz) - m) for m in ent["mh"]]
            i = min(range(len(d)), key=d.__getitem__)
            if d[i] > SEL_TOL:
                raise DecodeAuthorityError(
                    f"{path.name}:{sid} precursor {float(mz):.5f} is not within {SEL_TOL} Da of any allowlisted "
                    f"anchor [M+H]+ in this well; decode refused")
            approved.append({"spectrum_id": sid, "selected_ion_mz": float(mz), "anchor_key": ent["keys"][i]})
        _durable_append(self.log_path, {"event": "authorize", "file": path.name, "file_sha256": sha,
                                         "spectra": approved})


# ---------------------------------------------------------------------------------------------
# The one-look validation authority
# ---------------------------------------------------------------------------------------------

class ConfirmationV2Authority:
    """The single first look at replacement population 2. Construction order (each a separate method so
    the mutation harness can remove one check at a time):

      1 _check_not_previously_accessed  ledger entry, on-disk record, any commit or reflog entry ever
                                        touching the access directory
      2 _resolve_freeze_commit          exactly one commit ever ADDED the freeze doc, and it is HEAD
      3 _check_clean_tree               no tracked modification and no untracked file anywhere
      4 _check_frozen_bytes             every file in the manifest's frozen_files is byte-identical on disk
                                        to the freeze commit and has the recorded sha256
      5 _check_recomputed_hashes        candidate/comparator canonical hashes, population/scaffold/scan
                                        hashes recomputed here from committed files; caller's live header
                                        recomputation must also match
      6 _write_and_commit_record        exclusive-create + fsync record and ledger, git commit the record,
                                        verify HEAD^ == freeze commit
    """
    KIND = "VALIDATION"

    def __init__(self, *, live_header_hashes: dict, root: Path = ROOT, ledger_dir: Path = DEFAULT_LEDGER_DIR,
                 code_root: Path | None = ROOT):
        self.authorized = False
        self.root = Path(root)
        self.study_id = STUDY_ID_V2
        self.ledger_path = Path(ledger_dir) / f"{self.study_id}.json"
        if code_root is not None:
            check_code_provenance(code_root)
        self._check_not_previously_accessed()
        self.freeze_commit = self._resolve_freeze_commit()
        self._check_clean_tree()
        self.manifest = self._check_frozen_bytes()
        self.allowed = self._check_recomputed_hashes(live_header_hashes)
        self._sha_cache: dict[tuple, str] = {}
        self.record = self._write_and_commit_record()
        self.authorized = True
        _CONSTRUCTED.add(self)

    # 1
    def _check_not_previously_accessed(self) -> None:
        if self.ledger_path.exists():
            raise DecodeAuthorityError(
                f"out-of-repo access ledger entry {self.ledger_path} exists: study {self.study_id} was already "
                f"accessed on this machine; a second first look is prohibited")
        if (self.root / ACCESS_RECORD).exists() or (self.root / DECODE_INTENTS).exists():
            raise DecodeAuthorityError(f"{ACCESS_DIR} already holds an access record; a second look is prohibited")
        hist = _git_text(self.root, "log", "--all", "--reflog", "--format=%H", "--", ACCESS_DIR)
        if hist:
            raise DecodeAuthorityError(
                f"a validation access record has existed in git history under {ACCESS_DIR} "
                f"({len(hist.splitlines())} commit(s)); a second first look is prohibited even though none is on disk")

    # 2
    def _resolve_freeze_commit(self) -> str:
        head = _git_text(self.root, "rev-parse", "HEAD")
        reachable = _git_text(self.root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", FREEZE_DOC).splitlines()
        if len(reachable) != 1:
            raise DecodeAuthorityError(
                f"{FREEZE_DOC} must have been added by exactly one commit in HEAD's history; found {len(reachable)} "
                f"(a deleted-and-re-added freeze is a second freeze)")
        if reachable[0] != head:
            raise DecodeAuthorityError(
                f"HEAD {head[:12]} is not the freeze commit {reachable[0][:12]} that added {FREEZE_DOC}; validation "
                f"access HEAD must equal the final freeze commit (no allowlist)")
        manifest_adds = _git_text(self.root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--",
                                  FREEZE_MANIFEST).splitlines()
        if manifest_adds != [head]:
            raise DecodeAuthorityError(
                f"{FREEZE_MANIFEST} must be added by the freeze commit itself and never re-added (found {manifest_adds})")
        # a freeze with DIFFERENT content added anywhere else (another branch, a rewritten or amended commit
        # still in the reflog) is a competing freeze: refuse rather than let the operator choose between them
        everywhere = set(_git_text(self.root, "log", "--all", "--reflog", "--diff-filter=A", "--format=%H", "--",
                                   FREEZE_DOC).splitlines())
        for c in sorted(everywhere - {head}):
            for rel in (FREEZE_DOC, FREEZE_MANIFEST):
                other = _git(self.root, "show", f"{c}:{rel}")
                if other.returncode != 0 or other.stdout != _blob_at(self.root, head, rel):
                    raise DecodeAuthorityError(
                        f"commit {c[:12]} elsewhere in history added a different {rel}; competing freezes are prohibited")
        return head

    # 3
    def _check_clean_tree(self) -> None:
        st = _git_text(self.root, "status", "--porcelain", "--untracked-files=all")
        if st:
            raise DecodeAuthorityError(f"working tree is not clean (tracked or untracked changes): {st.splitlines()[:5]}")
        # skip-worktree ("S") and assume-unchanged (lower-case tag) hide on-disk edits from git status
        hidden = [ln for ln in _git_text(self.root, "ls-files", "-v").splitlines() if ln[:1] == "S" or ln[:1].islower()]
        if hidden:
            raise DecodeAuthorityError(f"index flags hide working-tree changes (skip-worktree/assume-unchanged): {hidden[:5]}")

    # 4
    def _check_frozen_bytes(self) -> dict:
        raw = require_committed_identical(self.root, FREEZE_MANIFEST, self.freeze_commit)
        require_committed_identical(self.root, FREEZE_DOC, self.freeze_commit)
        manifest = json.loads(raw)
        if manifest.get("study_id") != self.study_id:
            raise DecodeAuthorityError(f"freeze manifest study_id {manifest.get('study_id')!r} != {self.study_id!r}")
        frozen = manifest.get("frozen_files") or {}
        for rel in (SCAN_ALLOWLIST, POPULATION_CSV, CANDIDATE_JSON, COMPARATOR_JSON, FREEZE_DOC):
            if rel not in frozen:
                raise DecodeAuthorityError(f"freeze manifest frozen_files lacks required entry {rel}")
        for rel, want in sorted(frozen.items()):
            b = require_committed_identical(self.root, rel, self.freeze_commit)
            if sha256_bytes(b) != want:
                raise DecodeAuthorityError(f"{rel} sha256 {sha256_bytes(b)[:16]} != frozen {str(want)[:16]}")
        return manifest

    # 5
    def _check_recomputed_hashes(self, live_header_hashes: dict) -> dict:
        m = self.manifest
        cand = canonical_json_sha256(json.loads((self.root / CANDIDATE_JSON).read_bytes()))
        comp = canonical_json_sha256(json.loads((self.root / COMPARATOR_JSON).read_bytes()))
        rows = _read_csv(self.root / SCAN_ALLOWLIST)
        pop = _read_csv(self.root / POPULATION_CSV)
        recomputed = {
            "candidate_hash": cand,
            "comparator_hash": comp,
            "population_key_hash": sha256_lines({r["key"] for r in pop}),
            "scaffold_group_hash": sha256_lines({r["scaffold_group"] for r in pop}),
            "spectrum_manifest_hash": sha256_lines({f"{r['file']}:{r['spectrum_id']}" for r in rows}),
        }
        for field, val in recomputed.items():
            if m.get(field) != val:
                raise DecodeAuthorityError(f"{field}: freeze manifest {m.get(field)!r} != recomputed {val!r}")
        for field in LIVE_HEADER_HASH_FIELDS:
            if (live_header_hashes or {}).get(field) != m.get(field):
                raise DecodeAuthorityError(
                    f"{field}: live header-only recomputation {(live_header_hashes or {}).get(field)!r} != frozen "
                    f"{m.get(field)!r}; the on-disk data or eligibility code has drifted since the freeze")
        pop_keys = {r["key"] for r in pop}
        allowed: dict[str, dict] = {}
        for r in rows:
            if r["key"] not in pop_keys:
                raise DecodeAuthorityError(f"scan allowlist row {r['file']}:{r['spectrum_id']} names key outside population")
            f = allowed.setdefault(r["file"], {"sha256": r["file_sha256"], "scans": {}})
            if f["sha256"] != r["file_sha256"]:
                raise DecodeAuthorityError(f"scan allowlist lists two sha256 values for {r['file']}")
            f["scans"][r["spectrum_id"]] = float(r["selected_ion_mz"])
        return allowed

    # 6
    def _write_and_commit_record(self) -> dict:
        record = {
            "study_id": self.study_id, "kind": self.KIND,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "validation_access_head": self.freeze_commit, "freeze_commit": self.freeze_commit,
            "freeze_manifest_sha256": sha256_bytes((self.root / FREEZE_MANIFEST).read_bytes()),
            **{k: self.manifest[k] for k in ("candidate_hash", "comparator_hash", "population_key_hash",
                                             "scaffold_group_hash", "spectrum_manifest_hash")},
            "n_allowed_files": len(self.allowed),
            "n_allowed_scans": sum(len(v["scans"]) for v in self.allowed.values()),
            "statement": "written, fsynced and committed before any validation binary array is decoded; "
                         "population 2 is permanently EXPOSED from this record onward",
        }
        text = json.dumps(record, indent=1, sort_keys=True) + "\n"
        _durable_create(self.root / ACCESS_RECORD, text)
        _durable_create(self.ledger_path, json.dumps({**record, "repo_root": str(self.root)}, indent=1) + "\n")
        _git_text(self.root, "add", "-f", "--", ACCESS_RECORD)
        _git_text(self.root, "commit", "-q", "-m",
                  f"{self.study_id}: VALIDATION ACCESS RECORD (written before any validation decode)",
                  "--", ACCESS_RECORD)
        parent = _git_text(self.root, "rev-parse", "HEAD^")
        changed = _git_text(self.root, "show", "--name-only", "--format=", "HEAD").splitlines()
        if parent != self.freeze_commit or changed != [ACCESS_RECORD]:
            raise DecodeAuthorityError(
                f"access-record commit did not land directly on the freeze commit with only the record "
                f"(parent {parent[:12]}, changed {changed})")
        record["access_record_commit"] = _git_text(self.root, "rev-parse", "HEAD")
        return record

    def _file_sha(self, path: Path) -> str:
        st = path.stat()
        k = (str(path.resolve()), st.st_size, st.st_mtime_ns)
        if k not in self._sha_cache:
            self._sha_cache[k] = sha256_file(path)
        return self._sha_cache[k]

    def authorize(self, path, requests) -> None:
        if not self.authorized:
            raise DecodeAuthorityError("validation authority is not authorized")
        if not (self.root / ACCESS_RECORD).is_file() or not self.ledger_path.is_file():
            raise DecodeAuthorityError("access record or ledger entry missing; refusing to decode")
        path = Path(path)
        ent = self.allowed.get(path.name)
        if ent is None:
            raise DecodeAuthorityError(f"{path.name} is not in the frozen validation scan allowlist")
        sha = self._file_sha(path)
        if sha != ent["sha256"]:
            raise DecodeAuthorityError(
                f"{path.name} content sha256 {sha[:16]} != frozen {ent['sha256'][:16]} (substituted file)")
        approved = []
        for sid, mz, level in requests:
            if sid not in ent["scans"]:
                raise DecodeAuthorityError(f"{path.name}:{sid} is not in the frozen validation scan allowlist")
            if (level != 2.0 and level != 2) or mz is None or abs(float(mz) - ent["scans"][sid]) > 1e-6:
                raise DecodeAuthorityError(
                    f"{path.name}:{sid} header (ms_level={level!r}, m/z={mz!r}) does not match the frozen scan "
                    f"(m/z {ent['scans'][sid]!r})")
            approved.append(sid)
        _durable_append(self.root / DECODE_INTENTS, {"file": path.name, "file_sha256": sha, "spectra": approved,
                                                      "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})


AUTHORITY_TYPES = (AnchorPreflightAuthority, ConfirmationV2Authority)
