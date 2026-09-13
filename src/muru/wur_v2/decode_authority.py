"""Decode authorities for MSnLib confirmation study 2 (`muru-v2-msnlib-confirmation-2.0`).

Why this module exists. Confirmation sample 1 was burned on 2026-09-13 when a parser-preflight script passed a
duck-typed guard (`authorized = True`, no scope) to `external_mzml.decode_selected` and selected scans by file
position in pooled wells. The study-2 pre-sampling review (leakage, implementation and registry reviewers) then
found that a first hardening still kept scope in mutable attributes, trusted local-only history, and let the
anchor preflight create new exposure. This version:

* keeps every authority's scope in module-private, immutable state registered only as the last step of a
  completed constructor. The authority objects carry no scope attributes and reject attribute assignment, and
  `external_mzml.decode_selected` calls the module function `authorize_decode`, never a method on the object;
* `AnchorPreflightAuthority` authorizes only exact (file content sha256, spectrum id) pairs that were ALREADY
  decoded in a past event, as recorded in the committed exposure registry, and only when the scan's precursor
  is within 0.01 Da of a census anchor [M+H]+. A preflight therefore creates no new exposure;
* `ConfirmationV2Authority` is constructible only at a freeze commit that is also published on origin as
  refs/muru-freeze/<study>. It verifies every frozen byte, recomputes every hash itself (including a header-only
  re-read of every allowlisted scan from the frozen ZIP members), enforces disjointness from the exposure
  registry, and writes, fsyncs, commits AND PUSHES its access record (refs/muru-access/<study>) plus ledger
  entries before any decode can be authorized. A second clone, shallow clone, other HOME or removed worktree
  sees the pushed ref and refuses;
* production constructors take no location overrides. Tests obtain overrides only through `_for_tests`, which
  requires pytest to be imported and MURU_DECODE_AUTHORITY_TEST_MODE=1.

Threat model. Honest mistakes and ordinary misuse of repo code are blocked in code and by the static choke-point
tests. A deliberately malicious operator can still write a new base64 decoder for bytes on disk or rewrite this
module; that is disclosed, not claimed to be prevented.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pwd
import subprocess
import sys
import time
import types
import weakref
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEL_TOL = 0.01
STUDY_ID_V2 = "muru-v2-msnlib-confirmation-2.0"
TEST_MODE_ENV = "MURU_DECODE_AUTHORITY_TEST_MODE"

V2_DIR = "artifacts/wur_v2_confirmation_v2"
REGISTRY_DIR = f"{V2_DIR}/exposure_registry"
REGISTRY_MANIFEST = f"{REGISTRY_DIR}/registry_manifest.json"
EXPOSED_FILES = f"{REGISTRY_DIR}/exposed_files.csv"
DECODED_SPECTRA = f"{REGISTRY_DIR}/decoded_spectra.csv"
EXCLUDED_KEYS = f"{REGISTRY_DIR}/excluded_compound_keys.txt"
EXCLUDED_GROUPS = f"{REGISTRY_DIR}/excluded_scaffold_groups.txt"
REGISTRY_FILES = (REGISTRY_MANIFEST, EXPOSED_FILES, DECODED_SPECTRA, EXCLUDED_KEYS, EXCLUDED_GROUPS)
ANCHOR_ALLOWLIST = f"{V2_DIR}/anchor_preflight/anchor_preflight_allowlist.csv"
CENSUS = "artifacts/wur_v2/external_census/msnlib_census.json"
PROTOCOL_V2 = "MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md"
FREEZE_DOC = "MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md"
FREEZE_MANIFEST = f"{V2_DIR}/freeze/freeze_manifest.json"
SCAN_ALLOWLIST = f"{V2_DIR}/freeze/validation_scan_allowlist.csv"
POPULATION_CSV = f"{V2_DIR}/freeze/validation_population.csv"
ACCESS_DIR = f"{V2_DIR}/access"
ACCESS_RECORD = f"{ACCESS_DIR}/validation_access_record.json"
DECODE_INTENTS = f"{ACCESS_DIR}/validation_decode_intents.jsonl"
CANDIDATE_JSON = "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json"
COMPARATOR_JSON = "artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json"
REQUIRED_FROZEN = (SCAN_ALLOWLIST, POPULATION_CSV, CANDIDATE_JSON, COMPARATOR_JSON, FREEZE_DOC, PROTOCOL_V2,
                   *REGISTRY_FILES)
ACCESS_REF = f"refs/muru-access/{STUDY_ID_V2}"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID_V2}"
REMOTE = "origin"
HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)          # not $HOME: an environment variable must not move the ledger
DEFAULT_LEDGER_DIR = HOME / ".muru" / "access_ledger"
DEFAULT_ZIP_DIR = HOME / "muru-msnlib" / "zenodo"

# sha256 of the committed registry manifest this code is bound to. Updated only together with a registry rebuild.
REGISTRY_MANIFEST_SHA256 = "89d55a29b4884c6d43df6cb3b41def010b45c8e630ae3d934816dfaf589dc1bb"


class DecodeAuthorityError(RuntimeError):
    pass


# ============================================================================================ helpers

def _git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1")
    return env


def _git(root: Path, *args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
                          cwd=root, capture_output=True, env=_git_env(), timeout=timeout)


def _git_text(root: Path, *args: str, timeout: int = 300) -> str:
    r = _git(root, *args, timeout=timeout)
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


def _finite(x) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _blob_at(root: Path, commit: str, rel: str) -> bytes:
    r = _git(root, "cat-file", "blob", f"{commit}:{rel}")
    if r.returncode != 0:
        raise DecodeAuthorityError(f"{rel} is not present at commit {commit[:12]}")
    return r.stdout


def require_committed_identical(root: Path, rel: str, commit: str) -> bytes:
    p = Path(root) / rel
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


def _rows(root: Path, rel: str) -> list[dict]:
    with open(Path(root) / rel, newline="") as f:
        return list(csv.DictReader(f))


def _lines(root: Path, rel: str) -> set:
    return {ln for ln in (Path(root) / rel).read_text().split("\n") if ln}


def check_code_provenance(code_root: Path, modules=None, main_file=None, *, require_main=True) -> list[str]:
    """The code doing the decoding must be the committed code of `code_root`.

    Every loaded module whose file lies inside code_root, and every muru module wherever it lives, must be a
    .py file under code_root/src (or, for the running script, under code_root) that is byte-identical to HEAD.
    The running script must have a real file (python -c, stdin and notebooks are refused). Returns the checked
    'relative path:sha256' lines for the access record."""
    code_root = Path(code_root).resolve()
    head = _git_text(code_root, "rev-parse", "HEAD")
    if modules is None:
        modules = {n: getattr(m, "__file__", None) for n, m in list(sys.modules.items())}
    if main_file is None:
        main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    if require_main and not main_file:
        raise DecodeAuthorityError("the running script has no file (python -c, stdin or a notebook); refusing")
    items = sorted((n, f) for n, f in modules.items() if f)
    if not any(n == "muru.wur_v2.decode_authority" for n, _ in items):
        raise DecodeAuthorityError("muru.wur_v2.decode_authority is not among the modules being checked")
    if main_file:
        items.append(("__main__", main_file))
    src = code_root / "src"
    checked = []
    for name, f in items:
        fp = Path(f).resolve()
        is_muru = name == "muru" or name.startswith("muru.")
        if not fp.is_relative_to(code_root) and not is_muru and name != "__main__":
            continue                                                  # stdlib and site-packages
        base = src if is_muru else code_root
        if not fp.is_relative_to(base):
            raise DecodeAuthorityError(f"{name} is loaded from {fp}, outside {base}; refusing (shadowed or foreign code)")
        if fp.suffix != ".py":
            raise DecodeAuthorityError(f"{name} is loaded from a non-source file {fp.name}; refusing")
        rel = str(fp.relative_to(code_root))
        b = require_committed_identical(code_root, rel, head)
        checked.append(f"{rel}:{sha256_bytes(b)}")
    return checked


# ============================================================================================ scope registry

@dataclass(frozen=True)
class _Scope:
    kind: str
    files: types.MappingProxyType          # basename -> (sha256, MappingProxyType(spectrum_id -> frozen m/z))
    log_path: Path
    root: Path
    code_root: Path | None
    ledger_paths: tuple
    digest: str


_SCOPES: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_RECORDS: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _freeze_files(entries: dict) -> types.MappingProxyType:
    return types.MappingProxyType({f: (sha, types.MappingProxyType(dict(scans))) for f, (sha, scans) in entries.items()})


def _scope_digest(kind: str, files) -> str:
    return canonical_json_sha256({"kind": kind, "files": {f: [sha, sorted(scans.items())] for f, (sha, scans) in files.items()}})


def is_constructed(obj) -> bool:
    try:
        return obj in _SCOPES
    except TypeError:
        return False


class _Sealed:
    __slots__ = ("__weakref__", "_sealed")

    def __setattr__(self, name, value):
        raise DecodeAuthorityError("decode authorities are immutable")

    def __delattr__(self, name):
        raise DecodeAuthorityError("decode authorities are immutable")

    @property
    def authorized(self) -> bool:
        return is_constructed(self)


class _TestOverrides:
    __slots__ = ("values",)

    def __init__(self, values: dict):
        self.values = dict(values)


def _test_mode() -> bool:
    return os.environ.get(TEST_MODE_ENV) == "1" and "pytest" in sys.modules


def _for_tests(cls, **overrides):
    """Construct an authority with location overrides. Tests only."""
    if not _test_mode():
        raise DecodeAuthorityError("_for_tests is available only under pytest with MURU_DECODE_AUTHORITY_TEST_MODE=1")
    if issubclass(cls, AnchorPreflightAuthority):
        log_path = overrides.pop("log_path")
        return cls(log_path=log_path, _ov=_TestOverrides(overrides))
    return cls(_ov=_TestOverrides(overrides))


def _overrides(_ov) -> dict:
    if _ov is None:
        return {}
    if type(_ov) is not _TestOverrides or not _test_mode():
        raise DecodeAuthorityError("location overrides are available only in test mode")
    return _ov.values


def _check_registry(root: Path, commit: str, pinned: str) -> None:
    for rel in REGISTRY_FILES:
        require_committed_identical(root, rel, commit)
    got = sha256_file(Path(root) / REGISTRY_MANIFEST)
    if got != pinned:
        raise DecodeAuthorityError(f"exposure registry manifest sha256 {got[:16]} is not the one this code is bound to "
                                   f"({str(pinned)[:16]})")
    m = json.loads((Path(root) / REGISTRY_MANIFEST).read_text())
    for name, want in m["output_file_sha256"].items():
        if sha256_file(Path(root) / REGISTRY_DIR / name) != want:
            raise DecodeAuthorityError(f"registry output {name} does not match its manifest")


# ============================================================================================ authorization

def authorize_decode(guard, name: str, sha: str, requests) -> None:
    """Called by external_mzml.decode_selected before any array is decoded.

    requests: (spectrum_id, ms_level, selected_ion_mz, n_precursors, n_selected_ions), read from the bytes that
    will be decoded."""
    if type(guard) not in AUTHORITY_TYPES:
        raise DecodeAuthorityError("not a decode authority")
    sc = _SCOPES.get(guard)
    if sc is None:
        raise DecodeAuthorityError("authority has no registered scope (construction did not complete)")
    if _scope_digest(sc.kind, sc.files) != sc.digest:
        raise DecodeAuthorityError("authority scope digest changed")
    if sc.code_root is not None:
        check_code_provenance(sc.code_root)                       # late imports are checked too
    for lp in sc.ledger_paths:
        if not lp.is_file():
            raise DecodeAuthorityError(f"ledger entry {lp} is missing; refusing to decode")
    if sc.kind == "VALIDATION" and not (sc.root / ACCESS_RECORD).is_file():
        raise DecodeAuthorityError("validation access record is missing; refusing to decode")
    ent = sc.files.get(name)
    if ent is None:
        raise DecodeAuthorityError(f"{name} is not in this authority's allowlist")
    if sha != ent[0]:
        raise DecodeAuthorityError(f"{name} content sha256 {sha[:16]} != allowlisted {ent[0][:16]} (substituted file)")
    approved = []
    for sid, level, mz, n_prec, n_sel in requests:
        if sid not in ent[1]:
            raise DecodeAuthorityError(f"{name}:{sid} is not in this authority's allowlist")
        if level != 2.0:
            raise DecodeAuthorityError(f"{name}:{sid} is not an MS2 scan (ms_level={level!r})")
        if n_prec != 1 or n_sel != 1:
            raise DecodeAuthorityError(f"{name}:{sid} has {n_prec} precursors / {n_sel} selected ions; exactly one required")
        if not _finite(mz) or not (abs(float(mz) - ent[1][sid]) <= 1e-6):
            raise DecodeAuthorityError(f"{name}:{sid} selected-ion m/z {mz!r} does not match the allowlisted {ent[1][sid]!r}")
        approved.append(sid)
    _durable_append(sc.log_path, {"event": "authorize", "kind": sc.kind, "file": name, "file_sha256": sha,
                                  "spectra": approved, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})


# ============================================================================================ anchor preflight

class AnchorPreflightAuthority(_Sealed):
    """Re-decodes of already-exposed anchor spectra only.

    Allowlist CSV columns: file, file_sha256, spectrum_id, selected_ion_mz, anchor_key, anchor_mh. Every row must
    be a (file, spectrum_id) already in the registry's decoded_spectra.csv, with the file's sha256 in
    exposed_files.csv, the precursor within 0.01 Da of anchor_mh, and anchor_key a census anchor."""
    __slots__ = ()
    KIND = "ANCHOR_PREFLIGHT"

    def __init__(self, *, log_path, _ov=None):
        ov = _overrides(_ov)
        root = Path(ov.get("root", ROOT)).resolve()
        code_root = ov.get("code_root", ROOT)
        if code_root is not None:
            check_code_provenance(code_root)
        head = _git_text(root, "rev-parse", "HEAD")
        _check_registry(root, head, ov.get("registry_manifest_sha256", REGISTRY_MANIFEST_SHA256))
        require_committed_identical(root, ANCHOR_ALLOWLIST, head)
        require_committed_identical(root, CENSUS, head)
        anchors = set(json.loads((root / CENSUS).read_text())["anchors"]["design"]["v2_dev_five_rung"]["keys"])
        exposed = {r["file"]: r["file_sha256"] for r in _rows(root, EXPOSED_FILES)}
        decoded = {(r["file"], r["spectrum_id"]): r["selected_ion_mz"] for r in _rows(root, DECODED_SPECTRA)}
        entries: dict[str, tuple] = {}
        for r in _rows(root, ANCHOR_ALLOWLIST):
            f, sid = r["file"], r["spectrum_id"]
            if exposed.get(f) != r["file_sha256"]:
                raise DecodeAuthorityError(f"anchor allowlist file {f} is not an exposed file with that sha256")
            if (f, sid) not in decoded:
                raise DecodeAuthorityError(f"anchor allowlist scan {f}:{sid} was never decoded before; a preflight may "
                                           f"only re-decode already-exposed spectra")
            mz, mh = r["selected_ion_mz"], r["anchor_mh"]
            if not (_finite(mz) and _finite(mh) and _finite(decoded[(f, sid)])):
                raise DecodeAuthorityError(f"anchor allowlist row {f}:{sid} has a non-finite m/z")
            if not (abs(float(mz) - float(decoded[(f, sid)])) <= 1e-6) or not (abs(float(mz) - float(mh)) <= SEL_TOL):
                raise DecodeAuthorityError(f"anchor allowlist row {f}:{sid} precursor is not the anchor's [M+H]+")
            if r["anchor_key"] not in anchors:
                raise DecodeAuthorityError(f"anchor allowlist row {f}:{sid} names a non-anchor key")
            sha, scans = entries.setdefault(f, (r["file_sha256"], {}))
            if sha != r["file_sha256"]:
                raise DecodeAuthorityError(f"anchor allowlist lists two sha256 values for {f}")
            scans[sid] = float(mz)
        if not entries:
            raise DecodeAuthorityError("anchor allowlist is empty")
        files = _freeze_files(entries)
        log_path = Path(log_path)
        _durable_append(log_path, {"event": "construct", "kind": self.KIND, "git_head": head,
                                   "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n_files": len(files)})
        _SCOPES[self] = _Scope(self.KIND, files, log_path, root, None if code_root is None else Path(code_root),
                               (), _scope_digest(self.KIND, files))


# ============================================================================================ the one look

class ConfirmationV2Authority(_Sealed):
    """The single first look at replacement population 2. Construction phases:

      _preflight_environment          repo identity, not shallow, committer identity, no index lock, ledger
                                      writable, origin fetched
      _check_not_previously_accessed  ledgers, on-disk record, any commit/reflog/remote-tracking history of the
                                      access directory, local and remote refs/muru-access/<study>
      _resolve_freeze_commit          the freeze doc and manifest were each added exactly once, by HEAD (merges
                                      included), no competing freeze anywhere, origin refs/muru-freeze/<study> == HEAD
      _check_clean_tree               no tracked change, untracked file, ignored .py under src/scripts, index flag
      _check_frozen_bytes             every frozen file byte-identical to the freeze commit with the recorded sha256
      _check_recomputed               candidate/comparator/population/scaffold/spectrum hashes, registry binding and
                                      disjointness, header-only re-read of every allowlisted scan from its ZIP member
      _write_commit_push_record       exclusive record, commit on the freeze commit, refs/muru-access/<study>, push,
                                      verify on origin, then ledger entries; only then is the scope registered
    """
    __slots__ = ()
    KIND = "VALIDATION"

    def __init__(self, *, _ov=None):
        ov = _overrides(_ov)
        root = Path(ov.get("root", ROOT)).resolve()
        code_root = ov.get("code_root", ROOT)
        ledger_dirs = tuple(Path(p) for p in ov.get("ledger_dirs", (DEFAULT_LEDGER_DIR,)))
        checked_code = check_code_provenance(code_root) if code_root is not None else []
        common = Path(_git_text(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        ctx = types.SimpleNamespace(
            root=root, zip_dir=Path(ov.get("zip_dir", DEFAULT_ZIP_DIR)),
            pinned=ov.get("registry_manifest_sha256", REGISTRY_MANIFEST_SHA256),
            ledger_paths=tuple(d / f"{STUDY_ID_V2}.json" for d in ledger_dirs)
            + (common / "muru-access-ledger" / f"{STUDY_ID_V2}.json",))
        self._preflight_environment(ctx)
        self._check_not_previously_accessed(ctx)
        ctx.freeze = self._resolve_freeze_commit(ctx)
        self._check_clean_tree(ctx)
        ctx.manifest = self._check_frozen_bytes(ctx)
        entries = self._check_recomputed(ctx)
        files = _freeze_files(entries)
        record = self._write_commit_push_record(ctx, files, checked_code)
        _RECORDS[self] = types.MappingProxyType(record)
        _SCOPES[self] = _Scope(self.KIND, files, root / DECODE_INTENTS, root,
                               None if code_root is None else Path(code_root), ctx.ledger_paths,
                               _scope_digest(self.KIND, files))

    @property
    def record(self) -> dict:
        return dict(_RECORDS.get(self, {}))

    @staticmethod
    def _preflight_environment(ctx) -> None:
        top = Path(_git_text(ctx.root, "rev-parse", "--show-toplevel")).resolve()
        if top != ctx.root:
            raise DecodeAuthorityError(f"git toplevel {top} is not the study root {ctx.root}")
        if _git_text(ctx.root, "rev-parse", "--is-shallow-repository") != "false":
            raise DecodeAuthorityError("shallow repositories cannot prove the absence of a prior look")
        _git_text(ctx.root, "var", "GIT_COMMITTER_IDENT")
        git_dir = Path(_git_text(ctx.root, "rev-parse", "--path-format=absolute", "--git-dir"))
        if (git_dir / "index.lock").exists():
            raise DecodeAuthorityError("git index.lock present")
        for lp in ctx.ledger_paths:
            lp.parent.mkdir(parents=True, exist_ok=True)
            probe = lp.parent / f".probe-{os.getpid()}"
            probe.write_text("x")
            probe.unlink()
        _git_text(ctx.root, "fetch", "--prune", REMOTE, timeout=600)

    @staticmethod
    def _check_not_previously_accessed(ctx) -> None:
        for lp in ctx.ledger_paths:
            if lp.exists():
                raise DecodeAuthorityError(f"access ledger entry {lp} exists: {STUDY_ID_V2} was already accessed")
        if (ctx.root / ACCESS_RECORD).exists() or (ctx.root / DECODE_INTENTS).exists():
            raise DecodeAuthorityError(f"{ACCESS_DIR} already holds an access record; a second look is prohibited")
        hist = _git_text(ctx.root, "log", "--all", "--reflog", "-m", "--format=%H", "--", ACCESS_DIR)
        if hist:
            raise DecodeAuthorityError(
                f"a validation access record has existed in git history under {ACCESS_DIR}; a second first look is prohibited")
        if _git(ctx.root, "rev-parse", "--verify", "--quiet", ACCESS_REF).returncode == 0:
            raise DecodeAuthorityError(f"local {ACCESS_REF} exists; a second first look is prohibited")
        if _git_text(ctx.root, "ls-remote", REMOTE, ACCESS_REF, timeout=300):
            raise DecodeAuthorityError(f"{REMOTE} holds {ACCESS_REF}; a look already happened in another clone")

    @staticmethod
    def _resolve_freeze_commit(ctx) -> str:
        root = ctx.root
        head = _git_text(root, "rev-parse", "HEAD")
        for rel in (FREEZE_DOC, FREEZE_MANIFEST):
            adds = _git_text(root, "log", "-m", "--diff-filter=A", "--format=%H", "HEAD", "--", rel).splitlines()
            if adds != [head]:
                raise DecodeAuthorityError(f"{rel} must be added exactly once, by HEAD (the freeze commit); found {adds}")
        everywhere = set(_git_text(root, "log", "--all", "--reflog", "-m", "--diff-filter=A", "--format=%H", "--",
                                   FREEZE_DOC).splitlines())
        for c in sorted(everywhere - {head}):
            for rel in (FREEZE_DOC, FREEZE_MANIFEST):
                other = _git(root, "cat-file", "blob", f"{c}:{rel}")
                if other.returncode != 0 or other.stdout != _blob_at(root, head, rel):
                    raise DecodeAuthorityError(f"commit {c[:12]} added a different {rel}; competing freezes are prohibited")
        remote = _git_text(root, "ls-remote", REMOTE, FREEZE_REF, timeout=300).split()
        if not remote or remote[0] != head:
            raise DecodeAuthorityError(f"{REMOTE} {FREEZE_REF} does not name HEAD {head[:12]}; the freeze must be "
                                       f"published before the look")
        return head

    @staticmethod
    def _check_clean_tree(ctx) -> None:
        st = _git_text(ctx.root, "status", "--porcelain", "--untracked-files=all")
        if st:
            raise DecodeAuthorityError(f"working tree is not clean (tracked or untracked changes): {st.splitlines()[:5]}")
        ign = _git_text(ctx.root, "status", "--porcelain", "--ignored=matching", "--untracked-files=all").splitlines()
        bad = [ln for ln in ign if ln.startswith("!!") and ln.endswith(".py")
               and (ln[3:].startswith("src/") or ln[3:].startswith("scripts/"))]
        if bad:
            raise DecodeAuthorityError(f"ignored Python files under src/ or scripts/: {bad[:5]}")
        hidden = [ln for ln in _git_text(ctx.root, "ls-files", "-v").splitlines() if ln[:1] == "S" or ln[:1].islower()]
        if hidden:
            raise DecodeAuthorityError(f"index flags hide working-tree changes (skip-worktree/assume-unchanged): {hidden[:5]}")

    @staticmethod
    def _check_frozen_bytes(ctx) -> dict:
        raw = require_committed_identical(ctx.root, FREEZE_MANIFEST, ctx.freeze)
        manifest = json.loads(raw)
        if manifest.get("study_id") != STUDY_ID_V2:
            raise DecodeAuthorityError(f"freeze manifest study_id {manifest.get('study_id')!r} != {STUDY_ID_V2!r}")
        frozen = manifest.get("frozen_files") or {}
        missing = [rel for rel in REQUIRED_FROZEN if rel not in frozen]
        if missing:
            raise DecodeAuthorityError(f"freeze manifest frozen_files lacks required entries {missing}")
        for rel, want in sorted(frozen.items()):
            b = require_committed_identical(ctx.root, rel, ctx.freeze)
            if sha256_bytes(b) != want:
                raise DecodeAuthorityError(f"{rel} sha256 {sha256_bytes(b)[:16]} != frozen {str(want)[:16]}")
        return manifest

    @staticmethod
    def _check_recomputed(ctx) -> dict:
        from muru.wur_v2 import external_mzml as X
        root, m = ctx.root, ctx.manifest
        _check_registry(root, ctx.freeze, ctx.pinned)
        rows = _rows(root, SCAN_ALLOWLIST)
        pop = _rows(root, POPULATION_CSV)
        recomputed = {
            "candidate_hash": canonical_json_sha256(json.loads((root / CANDIDATE_JSON).read_bytes())),
            "comparator_hash": canonical_json_sha256(json.loads((root / COMPARATOR_JSON).read_bytes())),
            "population_key_hash": sha256_lines({r["key"] for r in pop}),
            "scaffold_group_hash": sha256_lines({r["scaffold_group"] for r in pop}),
            "spectrum_manifest_hash": sha256_lines({f"{r['file']}:{r['spectrum_id']}" for r in rows}),
            "registry_manifest_sha256": sha256_file(root / REGISTRY_MANIFEST),
        }
        for field, val in recomputed.items():
            if m.get(field) != val:
                raise DecodeAuthorityError(f"{field}: freeze manifest {m.get(field)!r} != recomputed {val!r}")
        excluded_keys, excluded_groups = _lines(root, EXCLUDED_KEYS), _lines(root, EXCLUDED_GROUPS)
        exposed = _rows(root, EXPOSED_FILES)
        exposed_sha, exposed_wells = {r["file_sha256"] for r in exposed}, {r["unique_sample_id"] for r in exposed}
        pop_keys = {r["key"] for r in pop}
        if pop_keys & excluded_keys:
            raise DecodeAuthorityError(f"{len(pop_keys & excluded_keys)} population keys are in the exposure registry")
        if {r["scaffold_group"] for r in pop} & excluded_groups:
            raise DecodeAuthorityError("population scaffold groups intersect the exposure registry")
        entries: dict[str, tuple] = {}
        members: dict[str, tuple] = {}
        for r in rows:
            if r["key"] not in pop_keys:
                raise DecodeAuthorityError(f"scan allowlist row {r['file']}:{r['spectrum_id']} names a key outside the population")
            if r["file_sha256"] in exposed_sha or r["unique_sample_id"] in exposed_wells:
                raise DecodeAuthorityError(f"scan allowlist file {r['file']} is an exposed file or well")
            if not _finite(r["selected_ion_mz"]):
                raise DecodeAuthorityError(f"scan allowlist row {r['file']}:{r['spectrum_id']} has a non-finite m/z")
            sha, scans = entries.setdefault(r["file"], (r["file_sha256"], {}))
            if sha != r["file_sha256"]:
                raise DecodeAuthorityError(f"scan allowlist lists two sha256 values for {r['file']}")
            scans[r["spectrum_id"]] = float(r["selected_ion_mz"])
            members[r["file"]] = (r["source_zip"], r["member"])
        for f, (sha, scans) in sorted(entries.items()):             # live header-only re-read from the frozen bytes
            zname, member = members[f]
            name, data = X.read_source(X.ZipMember(ctx.zip_dir / zname, member))
            if name != f or sha256_bytes(data) != sha:
                raise DecodeAuthorityError(f"{zname}!{member} does not have the frozen name and sha256")
            seen = {}
            for spec in X._iter_spectra(data):
                sid = spec.get("id")
                if sid in scans:
                    bdal = spec.find(X.NS + "binaryDataArrayList")
                    if bdal is not None:
                        spec.remove(bdal)
                    seen[sid] = X._spectrum_scope(spec)
            for sid, mz in scans.items():
                s = seen.get(sid)
                if s is None or s[0] != 2.0 or s[2] != 1 or s[3] != 1 or not _finite(s[1]) or not (abs(s[1] - mz) <= 1e-6):
                    raise DecodeAuthorityError(f"{f}:{sid} header does not match the frozen scan (live re-read)")
        return entries

    @staticmethod
    def _write_commit_push_record(ctx, files, checked_code) -> dict:
        root = ctx.root
        record = {
            "study_id": STUDY_ID_V2, "kind": "VALIDATION",
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "validation_access_head": ctx.freeze, "freeze_commit": ctx.freeze,
            "freeze_manifest_sha256": sha256_file(root / FREEZE_MANIFEST),
            **{k: ctx.manifest[k] for k in ("candidate_hash", "comparator_hash", "population_key_hash",
                                            "scaffold_group_hash", "spectrum_manifest_hash", "registry_manifest_sha256")},
            "n_allowed_files": len(files), "n_allowed_scans": sum(len(s) for _, s in files.values()),
            "code_provenance": checked_code,
            "statement": "written, fsynced, committed and pushed before any validation binary array is decoded; "
                         "population 2 is permanently EXPOSED from this record onward",
        }
        _durable_create(root / ACCESS_RECORD, json.dumps(record, indent=1, sort_keys=True) + "\n")
        _git_text(root, "add", "-f", "--", ACCESS_RECORD)
        _git_text(root, "commit", "-q", "--no-verify", "-m",
                  f"{STUDY_ID_V2}: VALIDATION ACCESS RECORD (written before any validation decode)", "--", ACCESS_RECORD)
        rec_commit = _git_text(root, "rev-parse", "HEAD")
        parent = _git_text(root, "rev-parse", "HEAD^")
        changed = _git_text(root, "show", "--name-only", "--format=", "HEAD").splitlines()
        if parent != ctx.freeze or changed != [ACCESS_RECORD]:
            raise DecodeAuthorityError("access-record commit is not a single-file child of the freeze commit")
        _git_text(root, "update-ref", ACCESS_REF, rec_commit)
        _git_text(root, "push", "--atomic", REMOTE, f"{rec_commit}:{ACCESS_REF}", timeout=600)
        remote = _git_text(root, "ls-remote", REMOTE, ACCESS_REF, timeout=300).split()
        if not remote or remote[0] != rec_commit:
            raise DecodeAuthorityError(f"{REMOTE} does not show {ACCESS_REF} at the record commit after push")
        record["access_record_commit"] = rec_commit
        for lp in ctx.ledger_paths:
            _durable_create(lp, json.dumps({**record, "repo_root": str(root)}, indent=1) + "\n")
        return record


AUTHORITY_TYPES = (AnchorPreflightAuthority, ConfirmationV2Authority)
