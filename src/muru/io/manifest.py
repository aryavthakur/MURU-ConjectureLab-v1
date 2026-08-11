"""Provenance: hashing, manifests, release pinning.

Every byte MURU reads from outside the repository is recorded here with a
SHA-256, a size, and a retrieval timestamp. A manifest is the only evidence
that an analysis ran on the data it claims to have run on.

Design rule: manifests are append-only facts about files that already exist on
disk. This module never downloads, never mutates, and never repairs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

CHUNK = 1 << 20  # 1 MiB


def sha256_file(path: str | Path) -> str:
    """SHA-256 of a file's bytes, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class FileRecord:
    """One acquired file. `path` is relative to the manifest's root."""

    path: str
    sha256: str
    size_bytes: int
    retrieved_utc: str


@dataclass
class Manifest:
    """A set of acquired files plus the pin that identifies their source."""

    source: str
    pin: dict
    root: str
    files: list[FileRecord]
    created_utc: str

    @classmethod
    def build(cls, source: str, pin: dict, root: str | Path, paths: list[Path]) -> "Manifest":
        root = Path(root)
        now = datetime.now(timezone.utc).isoformat()
        records = [
            FileRecord(
                path=str(p.relative_to(root)),
                sha256=sha256_file(p),
                size_bytes=p.stat().st_size,
                retrieved_utc=datetime.fromtimestamp(
                    p.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            )
            for p in sorted(paths)
        ]
        return cls(
            source=source, pin=pin, root=str(root), files=records, created_utc=now
        )

    @property
    def total_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)

    def corpus_digest(self) -> str:
        """A single hash over (path, sha256) pairs.

        Two acquisitions of the same corpus produce the same digest. This is the
        number quoted in reports to identify 'which corpus'.
        """
        h = hashlib.sha256()
        for f in sorted(self.files, key=lambda x: x.path):
            h.update(f.path.encode())
            h.update(f.sha256.encode())
        return h.hexdigest()

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["n_files"] = len(self.files)
        payload["total_bytes"] = self.total_bytes
        payload["corpus_digest"] = self.corpus_digest()
        path.write_text(json.dumps(payload, indent=2, sort_keys=False))
        return path

    @classmethod
    def read(cls, path: str | Path) -> "Manifest":
        d = json.loads(Path(path).read_text())
        return cls(
            source=d["source"],
            pin=d["pin"],
            root=d["root"],
            files=[FileRecord(**f) for f in d["files"]],
            created_utc=d["created_utc"],
        )

    def verify(self, root: str | Path | None = None) -> list[dict]:
        """Re-hash every file and return mismatches.

        An empty list means every acquired byte is unchanged since acquisition.
        A non-empty list is a BLOCKER under the Phase 1 bug policy.
        """
        base = Path(root if root is not None else self.root)
        problems = []
        for f in self.files:
            p = base / f.path
            if not p.exists():
                problems.append({"path": f.path, "issue": "MISSING"})
                continue
            actual = sha256_file(p)
            if actual != f.sha256:
                problems.append(
                    {
                        "path": f.path,
                        "issue": "HASH_MISMATCH",
                        "expected": f.sha256,
                        "actual": actual,
                    }
                )
        return problems
