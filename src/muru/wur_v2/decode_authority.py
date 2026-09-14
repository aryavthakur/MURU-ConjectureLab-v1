"""Decode authorities for MSnLib confirmation study 2 (`muru-v2-msnlib-confirmation-2.0`).

Why this module exists. Confirmation sample 1 was burned on 2026-09-13 when a parser-preflight script passed a
duck-typed guard (`authorized = True`, no scope) to `external_mzml.decode_selected` and selected scans by file
position in pooled wells. Two rounds of independent pre-sampling review (leakage, implementation, registry)
shaped this version:

* every authority's scope is module-private, immutable state, registered (by identity, not equality) only as the
  last step of a completed constructor. Authority objects carry no scope attributes and reject attribute
  assignment; `external_mzml.decode_selected` calls the module function `authorize_decode`, never a method;
* `AnchorPreflightAuthority` authorizes only exact (file content sha256, spectrum id) pairs that were ALREADY
  decoded in a past event (committed exposure registry) whose precursor is a census anchor [M+H]+ within 0.01 Da.
  A preflight creates no new exposure;
* the freeze is checked read-only by `verify_freeze_candidate` and only then published by `publish_freeze`, which
  registers the freeze sha in a local ledger and pushes refs/muru-freeze/<study> create-only to the pinned
  canonical remote. A slip in the frozen artifacts is therefore caught before it can burn population 2;
* `ConfirmationV2Authority` is constructible only in the clone that published the freeze, at that freeze commit,
  with the canonical remote. It re-runs every freeze check, re-reads every allowlisted scan header-only from the
  frozen ZIP members (m/z, rung, compound [M+H]+, well membership), enforces disjointness from the registry, and
  writes, fsyncs, commits and pushes create-only its access record (refs/muru-access/<study>) plus ledger
  entries before any decode can be authorized. A failure after the record exists is logged as
  ATTEMPT_FAILED_NO_DECODE and the study stays blocked (fail closed; recovery only by a documented amendment);
* production constructors take no location overrides; tests use `_for_tests` (pytest running a test, test-mode
  environment variable, and never the real repository root or real ZIP directory).

Threat model. Honest mistakes and ordinary misuse of repo code are blocked in code and by the static choke-point
tests. Deliberate circumvention remains possible and is disclosed, not claimed to be prevented: writing a new
decoder (stdlib base64/zlib, or an installed third-party reader) for bytes on disk, mutating this module in
memory (for example through sys.modules), setting the decode permit by hand, or faking test mode.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pwd
import re
import site
import socket
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
CANONICAL_REMOTE = "github.com/aryavthakur/MURU-ConjectureLab-v1"

V2_DIR = "artifacts/wur_v2_confirmation_v2"
REGISTRY_DIR = f"{V2_DIR}/exposure_registry"
REGISTRY_MANIFEST = f"{REGISTRY_DIR}/registry_manifest.json"
EXPOSED_FILES = f"{REGISTRY_DIR}/exposed_files.csv"
DECODED_SPECTRA = f"{REGISTRY_DIR}/decoded_spectra.csv"
EXCLUDED_KEYS = f"{REGISTRY_DIR}/excluded_compound_keys.txt"
EXCLUDED_GROUPS = f"{REGISTRY_DIR}/excluded_scaffold_groups.txt"
REGISTRY_FILES = (REGISTRY_MANIFEST, EXPOSED_FILES, DECODED_SPECTRA, EXCLUDED_KEYS, EXCLUDED_GROUPS)
STUDY1_TRANSPORT = "artifacts/wur_v2_confirmation/transport_provenance_manifest.json"
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
RECOMPUTED_FIELDS = ("candidate_hash", "comparator_hash", "population_key_hash", "scaffold_group_hash",
                     "spectrum_manifest_hash", "registry_manifest_sha256")
ACCESS_REF = f"refs/muru-access/{STUDY_ID_V2}"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID_V2}"
PROBE_REF = f"refs/muru-probe/{STUDY_ID_V2}"
REMOTE = "origin"
HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)          # not $HOME: an environment variable must not move the ledger
DEFAULT_LEDGER_DIR = HOME / ".muru" / "access_ledger"
DEFAULT_ZIP_DIR = HOME / "muru-msnlib" / "zenodo"
USID_RE = re.compile(r"(pluskal_.*?_id)(?=_|\.)")

# sha256 of the committed registry manifest this code is bound to. Updated only together with a registry rebuild.
REGISTRY_MANIFEST_SHA256 = "ef64541d71be977f65e880c616a8cb895b6c9f3657ff8d8019797ca7d69a9675"


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


def _remote_ref(root: Path, ref: str) -> str | None:
    """sha of exactly `ref` on the remote (ls-remote tail-matches patterns, so parse and compare the full name)."""
    for line in _git_text(root, "ls-remote", REMOTE, ref, timeout=300).splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1] == ref:
            return parts[0]
    return None


def normalize_remote(url: str) -> str:
    u = url.strip()
    if u.startswith(("/", ".", "file://")) or re.match(r"^[A-Za-z]:\\", u):
        return str(Path(u.replace("file://", "", 1)).resolve())
    u = re.sub(r"^(ssh|https?|git)://", "", u)
    u = re.sub(r"^[^@/]+@", "", u)
    u = u.replace(":", "/", 1) if ":" in u.split("/", 1)[0] else u
    return re.sub(r"\.git$", "", u.rstrip("/"))


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


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _rows(root: Path, rel: str) -> list[dict]:
    with open(Path(root) / rel, newline="") as f:
        return list(csv.DictReader(f))


def _lines(root: Path, rel: str) -> set:
    return {ln for ln in (Path(root) / rel).read_text().split("\n") if ln}


def _install_prefixes() -> list[Path]:
    paths = {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}
    try:
        paths |= set(site.getsitepackages()) | {site.getusersitepackages()}
    except AttributeError:
        pass
    return sorted({Path(p).resolve() for p in paths if p})


def check_code_provenance(code_root: Path, modules=None, main_file=None, *, require_main=True) -> list[str]:
    """The code doing the decoding must be the committed code of `code_root`.

    Modules of the Python installation (sys.prefix, base prefix, site-packages) are skipped. Every other loaded
    module must be inside code_root; muru modules must be under code_root/src; each must be a .py file
    byte-identical to HEAD. The running script must have a real file inside code_root (python -c, stdin and
    notebooks are refused). A module loaded from anywhere else (a PYTHONPATH scratch helper, sitecustomize) is
    refused. Returns the checked 'relative path:sha256' lines for the access record."""
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
    prefixes = [p for p in _install_prefixes() if not code_root.is_relative_to(p)]
    src = code_root / "src"
    checked = []
    for name, f in items:
        fp = Path(f).resolve()
        is_muru = name == "muru" or name.startswith("muru.")
        if not is_muru and name != "__main__" and any(fp.is_relative_to(p) for p in prefixes):
            continue
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


def _scope_of(obj):
    """Identity lookup: an object with a permissive __eq__/__hash__ cannot borrow another object's scope."""
    for ref in _SCOPES.keyrefs():
        k = ref()
        if k is obj:
            return _SCOPES[k]
    return None


def is_constructed(obj) -> bool:
    return type(obj) in AUTHORITY_TYPES and _scope_of(obj) is not None


class _Sealed:
    __slots__ = ("__weakref__",)

    def __setattr__(self, name, value):
        raise DecodeAuthorityError("decode authorities are immutable")

    def __delattr__(self, name):
        raise DecodeAuthorityError("decode authorities are immutable")

    def __reduce_ex__(self, protocol):
        raise DecodeAuthorityError("decode authorities cannot be copied or pickled")

    @property
    def authorized(self) -> bool:
        return is_constructed(self)


class _TestOverrides:
    __slots__ = ("values",)

    def __init__(self, values: dict):
        self.values = dict(values)


def _test_mode() -> bool:
    return (os.environ.get(TEST_MODE_ENV) == "1" and "pytest" in sys.modules
            and bool(os.environ.get("PYTEST_CURRENT_TEST")))


def _check_test_overrides(values: dict) -> None:
    root = values.get("root")
    if root is not None and Path(root).resolve() == ROOT:
        raise DecodeAuthorityError("test overrides may not target the real repository root")
    zip_dir = values.get("zip_dir")
    if zip_dir is not None and Path(zip_dir).resolve().is_relative_to(DEFAULT_ZIP_DIR.resolve()):
        raise DecodeAuthorityError("test overrides may not read the real MSnLib ZIP directory")
    for d in values.get("ledger_dirs", ()):
        if Path(d).resolve().is_relative_to(DEFAULT_LEDGER_DIR.resolve()):
            raise DecodeAuthorityError("test overrides may not use the real access ledger")


def _for_tests(cls, **overrides):
    """Construct an authority with location overrides. Tests only."""
    if not _test_mode():
        raise DecodeAuthorityError("_for_tests is available only inside a running pytest test in test mode")
    _check_test_overrides(overrides)
    if issubclass(cls, AnchorPreflightAuthority):
        log_path = overrides.pop("log_path")
        return cls(log_path=log_path, _ov=_TestOverrides(overrides))
    return cls(_ov=_TestOverrides(overrides))


def _overrides(_ov) -> dict:
    if _ov is None:
        return {}
    if type(_ov) is not _TestOverrides or not _test_mode():
        raise DecodeAuthorityError("location overrides are available only in test mode")
    _check_test_overrides(_ov.values)
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
    sc = _scope_of(guard)
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
        if type(sid) is not str or sid not in ent[1]:
            raise DecodeAuthorityError(f"{name}:{sid!r} is not in this authority's allowlist")
        if level != 2.0:
            raise DecodeAuthorityError(f"{name}:{sid} is not an MS2 scan (ms_level={level!r})")
        if n_prec != 1 or n_sel != 1:
            raise DecodeAuthorityError(f"{name}:{sid} has {n_prec} precursors / {n_sel} selected ions; exactly one required")
        if not _finite(mz) or not (abs(float(mz) - ent[1][sid]) <= 1e-6):
            raise DecodeAuthorityError(f"{name}:{sid} selected-ion m/z {mz!r} does not match the allowlisted {ent[1][sid]!r}")
        approved.append(sid)
    _durable_append(sc.log_path, {"event": "authorize", "kind": sc.kind, "file": name, "file_sha256": sha,
                                  "spectra": approved, "utc": _utc()})


# ============================================================================================ anchor preflight

class AnchorPreflightAuthority(_Sealed):
    """Re-decodes of already-exposed anchor spectra only.

    Allowlist CSV columns: file, file_sha256, spectrum_id, selected_ion_mz, anchor_key, anchor_mh. Every row must
    be a (file, spectrum_id) already in the registry's decoded_spectra.csv at the same m/z, with the file's sha256
    in exposed_files.csv, the precursor within 0.01 Da of anchor_mh, and anchor_key a census anchor."""
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
            if not (abs(float(mz) - float(decoded[(f, sid)])) <= 1e-6):
                raise DecodeAuthorityError(f"anchor allowlist row {f}:{sid} m/z differs from the recorded decoded m/z")
            if not (abs(float(mz) - float(mh)) <= SEL_TOL):
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
        _durable_append(log_path, {"event": "construct", "kind": self.KIND, "git_head": head, "utc": _utc(),
                                   "n_files": len(files)})
        _SCOPES[self] = _Scope(self.KIND, files, log_path, root, None if code_root is None else Path(code_root),
                               (), _scope_digest(self.KIND, files))


# ============================================================================================ freeze checks

def _context(ov: dict) -> types.SimpleNamespace:
    root = Path(ov.get("root", ROOT)).resolve()
    ledger_dirs = tuple(Path(p) for p in ov.get("ledger_dirs", (DEFAULT_LEDGER_DIR,)))
    common = Path(_git_text(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return types.SimpleNamespace(
        root=root, zip_dir=Path(ov.get("zip_dir", DEFAULT_ZIP_DIR)),
        pinned=ov.get("registry_manifest_sha256", REGISTRY_MANIFEST_SHA256),
        canonical_remote=ov.get("canonical_remote", CANONICAL_REMOTE),
        ledger_paths=tuple(d / f"{STUDY_ID_V2}.json" for d in ledger_dirs)
        + (common / "muru-access-ledger" / f"{STUDY_ID_V2}.json",),
        freeze_registration=common / "muru-access-ledger" / f"{STUDY_ID_V2}.freeze.json",
        attempts_log=common / "muru-access-ledger" / f"{STUDY_ID_V2}.attempts.jsonl")


def _check_repo_and_remote(ctx, *, need_push: bool) -> None:
    top = Path(_git_text(ctx.root, "rev-parse", "--show-toplevel")).resolve()
    if top != ctx.root:
        raise DecodeAuthorityError(f"git toplevel {top} is not the study root {ctx.root}")
    if _git_text(ctx.root, "rev-parse", "--is-shallow-repository") != "false":
        raise DecodeAuthorityError("shallow repositories cannot prove the absence of a prior look")
    url = normalize_remote(_git_text(ctx.root, "remote", "get-url", REMOTE))
    push_url = normalize_remote(_git_text(ctx.root, "remote", "get-url", "--push", REMOTE))
    want = normalize_remote(ctx.canonical_remote)
    if url != want or push_url != want:
        raise DecodeAuthorityError(f"remote {REMOTE} ({url}, push {push_url}) is not the canonical remote {want}")
    _git_text(ctx.root, "fetch", "--prune", REMOTE, timeout=600)
    if need_push:
        _git_text(ctx.root, "push", "--dry-run", "--porcelain", REMOTE, f"HEAD:{PROBE_REF}", timeout=600)


def _added_once_by_head(root: Path, head: str) -> None:
    for rel in (FREEZE_DOC, FREEZE_MANIFEST):
        adds = list(dict.fromkeys(_git_text(root, "log", "-m", "--diff-filter=A", "--format=%H", "HEAD", "--",
                                            rel).splitlines()))
        if adds != [head]:
            raise DecodeAuthorityError(f"{rel} must be added exactly once, by HEAD (the freeze commit); found {adds}")
    everywhere = set(_git_text(root, "log", "--all", "--reflog", "-m", "--diff-filter=A", "--format=%H", "--",
                               FREEZE_DOC).splitlines())
    for c in sorted(everywhere - {head}):
        for rel in (FREEZE_DOC, FREEZE_MANIFEST):
            other = _git(root, "cat-file", "blob", f"{c}:{rel}")
            if other.returncode != 0 or other.stdout != _blob_at(root, head, rel):
                raise DecodeAuthorityError(f"commit {c[:12]} added a different {rel}; competing freezes are prohibited")


def _check_clean_tree(ctx) -> None:
    st = _git_text(ctx.root, "status", "--porcelain", "--untracked-files=all")
    if st:
        raise DecodeAuthorityError(f"working tree is not clean (tracked or untracked changes): {st.splitlines()[:5]}")
    ign = _git_text(ctx.root, "status", "--porcelain", "--ignored=matching", "--untracked-files=all").splitlines()
    guarded = ("src/", "scripts/", f"{V2_DIR}/")
    bad = [ln for ln in ign if ln.startswith("!!") and ln[3:].startswith(guarded)
           and "__pycache__/" not in ln and not ln.endswith(".pyc")]
    if bad:
        raise DecodeAuthorityError(f"ignored files under src/, scripts/ or the study directory: {bad[:5]}")
    hidden = [ln for ln in _git_text(ctx.root, "ls-files", "-v").splitlines() if ln[:1] == "S" or ln[:1].islower()]
    if hidden:
        raise DecodeAuthorityError(f"index flags hide working-tree changes (skip-worktree/assume-unchanged): {hidden[:5]}")


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
    for field in RECOMPUTED_FIELDS:
        if m.get(field) != recomputed[field]:
            raise DecodeAuthorityError(f"{field}: freeze manifest {m.get(field)!r} != recomputed {recomputed[field]!r}")
    excluded_keys, excluded_groups = _lines(root, EXCLUDED_KEYS), _lines(root, EXCLUDED_GROUPS)
    exposed = _rows(root, EXPOSED_FILES)
    exposed_sha, exposed_wells = {r["file_sha256"] for r in exposed}, {r["unique_sample_id"] for r in exposed}
    by_key = {r["key"]: r for r in pop}
    if set(by_key) & excluded_keys:
        raise DecodeAuthorityError(f"{len(set(by_key) & excluded_keys)} population keys are in the exposure registry")
    if {r["scaffold_group"] for r in pop} & excluded_groups:
        raise DecodeAuthorityError("population scaffold groups intersect the exposure registry")
    entries: dict[str, tuple] = {}
    members: dict[str, tuple] = {}
    rungs: dict[tuple, str] = {}
    for r in rows:
        f, sid = r["file"], r["spectrum_id"]
        p = by_key.get(r["key"])
        if p is None:
            raise DecodeAuthorityError(f"scan allowlist row {f}:{sid} names a key outside the population")
        if r["file_sha256"] in exposed_sha or r["unique_sample_id"] in exposed_wells:
            raise DecodeAuthorityError(f"scan allowlist file {f} is an exposed file or well")
        well = USID_RE.search(f)
        if well is None or well.group(1) != r["unique_sample_id"]:
            raise DecodeAuthorityError(f"scan allowlist row {f}:{sid} well {r['unique_sample_id']!r} is not the file's well")
        if r["unique_sample_id"] not in set(p["wells"].split(";")):
            raise DecodeAuthorityError(f"population key {r['key']} is not plated in well {r['unique_sample_id']}")
        if not (_finite(r["selected_ion_mz"]) and _finite(p["mh"])):
            raise DecodeAuthorityError(f"scan allowlist row {f}:{sid} has a non-finite m/z")
        if not (abs(float(r["selected_ion_mz"]) - float(p["mh"])) <= SEL_TOL):
            raise DecodeAuthorityError(f"scan allowlist row {f}:{sid} precursor is not within {SEL_TOL} Da of the "
                                       f"population compound's [M+H]+")
        sha, scans = entries.setdefault(f, (r["file_sha256"], {}))
        if sha != r["file_sha256"]:
            raise DecodeAuthorityError(f"scan allowlist lists two sha256 values for {f}")
        scans[sid] = float(r["selected_ion_mz"])
        members[f] = (r["source_zip"], r["member"])
        rungs[(f, sid)] = r["rung"]
    for f, (sha, scans) in sorted(entries.items()):             # live header-only re-read of the frozen bytes
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
        live_rung = {r["spectrum_id"]: r["rung"] for r in X.scan_headers_rung_only(data)}
        for sid, mz in scans.items():
            s = seen.get(sid)
            if s is None or s[0] != 2.0 or s[2] != 1 or s[3] != 1 or not _finite(s[1]) or not (abs(s[1] - mz) <= 1e-6):
                raise DecodeAuthorityError(f"{f}:{sid} header does not match the frozen scan (live re-read)")
            if sid not in live_rung or not _finite(rungs[(f, sid)]) or float(rungs[(f, sid)]) != live_rung[sid]:
                raise DecodeAuthorityError(f"{f}:{sid} is not the frozen fixed rung (live re-read)")
    return entries


def verify_freeze_candidate(*, _ov=None) -> dict:
    """Read-only: every freeze check the look will run, on HEAD, without publishing or writing anything.
    Run it (through the committed freeze script) before publish_freeze; nothing here can burn population 2."""
    ov = _overrides(_ov)
    ctx = _context(ov)
    ctx.freeze = _git_text(ctx.root, "rev-parse", "HEAD")
    _added_once_by_head(ctx.root, ctx.freeze)
    _check_clean_tree(ctx)
    ctx.manifest = _check_frozen_bytes(ctx)
    entries = _check_recomputed(ctx)
    return {"freeze_commit": ctx.freeze, "n_files": len(entries), "n_scans": sum(len(s) for _, s in entries.values())}


def publish_freeze(*, _ov=None) -> str:
    """Verify, register the freeze sha locally (exclusive create), and push refs/muru-freeze/<study> create-only
    to the canonical remote. A second, different freeze can never be published by this function."""
    ov = _overrides(_ov)
    summary = verify_freeze_candidate(_ov=_ov)
    ctx = _context(ov)
    _check_repo_and_remote(ctx, need_push=True)
    head = summary["freeze_commit"]
    if _remote_ref(ctx.root, FREEZE_REF) is not None:
        raise DecodeAuthorityError(f"{REMOTE} already holds {FREEZE_REF}; a freeze is published once")
    _durable_create(ctx.freeze_registration, json.dumps({"study_id": STUDY_ID_V2, "freeze_commit": head,
                                                         "utc": _utc(), **summary}, indent=1) + "\n")
    _git_text(ctx.root, "push", "--atomic", f"--force-with-lease={FREEZE_REF}:", REMOTE, f"{head}:{FREEZE_REF}", timeout=600)
    if _remote_ref(ctx.root, FREEZE_REF) != head:
        raise DecodeAuthorityError(f"{REMOTE} does not show {FREEZE_REF} at the freeze commit after push")
    return head


# ============================================================================================ the one look

class ConfirmationV2Authority(_Sealed):
    """The single first look at replacement population 2. Construction phases:

      provenance, repo identity, not shallow, canonical remote (fetch and push permission), committer identity,
        no index lock, writable ledgers                                           (nothing written if any fails)
      _check_not_previously_accessed   ledgers, on-disk record, any commit/reflog/remote-tracking history of the
                                       access directory, local and remote refs/muru-access/<study>
      freeze                           doc and manifest added once by HEAD (merges included), no competing freeze,
                                       the local freeze registration names HEAD, origin refs/muru-freeze == HEAD
      clean tree, frozen bytes, recomputed values and live header re-read (as verify_freeze_candidate)
      _write_commit_push_record        exclusive record with a nonce, commit on the freeze commit, create-only push
                                       of refs/muru-access/<study>, exact remote verification, ledger entries;
                                       only then is the scope registered. Any failure here is logged as
                                       ATTEMPT_FAILED_NO_DECODE and the study stays blocked.
    """
    __slots__ = ()
    KIND = "VALIDATION"

    def __init__(self, *, _ov=None):
        ov = _overrides(_ov)
        code_root = ov.get("code_root", ROOT)
        checked_code = check_code_provenance(code_root) if code_root is not None else []
        ctx = _context(ov)
        _check_repo_and_remote(ctx, need_push=True)
        _git_text(ctx.root, "var", "GIT_COMMITTER_IDENT")
        git_dir = Path(_git_text(ctx.root, "rev-parse", "--path-format=absolute", "--git-dir"))
        if (git_dir / "index.lock").exists():
            raise DecodeAuthorityError("git index.lock present")
        for lp in ctx.ledger_paths:
            lp.parent.mkdir(parents=True, exist_ok=True)
            probe = lp.parent / f".probe-{os.getpid()}"
            probe.write_text("x")
            probe.unlink()
        self._check_not_previously_accessed(ctx)
        ctx.freeze = _git_text(ctx.root, "rev-parse", "HEAD")
        _added_once_by_head(ctx.root, ctx.freeze)
        reg = json.loads(ctx.freeze_registration.read_text()) if ctx.freeze_registration.is_file() else {}
        if reg.get("freeze_commit") != ctx.freeze:
            raise DecodeAuthorityError("no local freeze registration names HEAD; publish the freeze from this clone "
                                       "with publish_freeze before the look")
        if _remote_ref(ctx.root, FREEZE_REF) != ctx.freeze:
            raise DecodeAuthorityError(f"{REMOTE} {FREEZE_REF} does not name HEAD {ctx.freeze[:12]}; the freeze must be "
                                       f"published before the look")
        _check_clean_tree(ctx)
        ctx.manifest = _check_frozen_bytes(ctx)
        entries = _check_recomputed(ctx)
        files = _freeze_files(entries)
        try:
            record = self._write_commit_push_record(ctx, files, checked_code)
        except BaseException as exc:
            _durable_append(ctx.attempts_log, {"status": "ATTEMPT_FAILED_NO_DECODE", "utc": _utc(),
                                               "freeze_commit": ctx.freeze, "error": f"{type(exc).__name__}: {exc}"})
            raise
        _RECORDS[self] = types.MappingProxyType(record)
        _SCOPES[self] = _Scope(self.KIND, files, ctx.root / DECODE_INTENTS, ctx.root,
                               None if code_root is None else Path(code_root), ctx.ledger_paths,
                               _scope_digest(self.KIND, files))

    @property
    def record(self) -> dict:
        for ref in _RECORDS.keyrefs():
            if ref() is self:
                return dict(_RECORDS[self])
        return {}

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
        if _remote_ref(ctx.root, ACCESS_REF) is not None:
            raise DecodeAuthorityError(f"{REMOTE} holds {ACCESS_REF}; a look already happened in another clone")

    @staticmethod
    def _write_commit_push_record(ctx, files, checked_code) -> dict:
        root = ctx.root
        record = {
            "study_id": STUDY_ID_V2, "kind": "VALIDATION", "utc": _utc(),
            "nonce": os.urandom(16).hex(), "host": socket.gethostname(),
            "validation_access_head": ctx.freeze, "freeze_commit": ctx.freeze,
            "canonical_remote": ctx.canonical_remote,
            "freeze_manifest_sha256": sha256_file(root / FREEZE_MANIFEST),
            **{k: ctx.manifest[k] for k in RECOMPUTED_FIELDS},
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
        _git_text(root, "push", "--atomic", f"--force-with-lease={ACCESS_REF}:", REMOTE, f"{rec_commit}:{ACCESS_REF}",
                  timeout=600)
        if _remote_ref(root, ACCESS_REF) != rec_commit:
            raise DecodeAuthorityError(f"{REMOTE} does not show {ACCESS_REF} at the record commit after push")
        record["access_record_commit"] = rec_commit
        for lp in ctx.ledger_paths:
            _durable_create(lp, json.dumps({**record, "repo_root": str(root)}, indent=1) + "\n")
        return record


AUTHORITY_TYPES = (AnchorPreflightAuthority, ConfirmationV2Authority)
