"""Guards for external outcome access (v2 final-candidate freeze, section "one look").

An `AccessGuard` must exist before any external peak array is decoded. On
creation it checks that the governing freeze document is committed, that the
tracked tree is clean, and (for kind VALIDATION) that no validation access
record exists yet; it then writes the first-access record (UTC time, HEAD,
dirty state, freeze-document sha256) before returning. It authorizes decodes
only for spectrum ids of its declared population and logs every decode.
A second VALIDATION guard refuses to construct.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class GuardError(RuntimeError):
    pass


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


class AccessGuard:
    KINDS = ("ANCHOR_CALIBRATION", "VALIDATION")

    def __init__(self, kind: str, record_path: Path, freeze_doc: Path, allowed_spectrum_keys: set,
                 require_clean: bool = True, root: Path = ROOT):
        if kind not in self.KINDS:
            raise GuardError(kind)
        self.kind, self.record_path, self.allowed = kind, Path(record_path), set(allowed_spectrum_keys)
        if self.record_path.exists():
            raise GuardError(f"{kind} access record exists ({self.record_path}); a second look is prohibited")
        rel = str(Path(freeze_doc).resolve().relative_to(root.resolve()))
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=root, capture_output=True)
        if tracked.returncode != 0:
            raise GuardError(f"freeze document {rel} is not committed")
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                                    capture_output=True, text=True).stdout.strip())
        if require_clean and dirty:
            raise GuardError("tracked tree is dirty; commit before external access")
        self.record = {"kind": kind, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip(),
                       "git_tree_dirty": dirty, "freeze_doc": rel,
                       "freeze_doc_sha256": hashlib.sha256(Path(freeze_doc).read_bytes()).hexdigest(),
                       "n_allowed_spectrum_keys": len(self.allowed), "decodes": []}
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        self.record_path.write_text(json.dumps(self.record, indent=1) + "\n")    # written before any decode
        self.authorized = True

    def record_decode(self, path, ids):
        bad = [i for i in ids if (Path(path).name, i) not in self.allowed]
        if bad:
            raise GuardError(f"{len(bad)} spectra outside the {self.kind} population requested, e.g. {bad[:3]}")
        self.record["decodes"].append({"file": Path(path).name, "n": len(ids)})
        self.record_path.write_text(json.dumps(self.record, indent=1) + "\n")
