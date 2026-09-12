"""Environment provenance and canonical content hashes for WUR artifacts.

Both Stage 0 manifests stamp a creation time, so whole-file byte-identity
across runs is impossible by construction. The reproducibility contract is
instead a canonical hash over the scientific payload: re-running the Stage 0
CLI must reproduce `connectivity_keys_sha256` exactly. Timestamps are
allowed to move; content hashes are not.
"""
import hashlib
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

import numpy
import pandas
import scipy
from rdkit import rdBase


def canonical_key_hash(keys: Iterable[str]) -> str:
    """SHA-256 over the UTF-8 bytes of the sorted keys joined by "\\n".

    Sorted, newline-joined, no trailing newline, no separators beyond the
    joins. This exact serialization is the contract; changing it invalidates
    every recorded hash.
    """
    payload = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git_commit_sha(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "unavailable"


def _pyarrow_version() -> str:
    try:
        import pyarrow
        return pyarrow.__version__
    except ImportError:
        return "absent"


def environment_provenance(root: Path) -> dict:
    """The interpreter, the libraries whose behaviour the results depend on,
    the commit that produced them, and the hash of the frozen release
    manifest they were computed against.

    rdkit sets the scaffold groups and the identity gate; pandas and numpy
    set the grouping and the medians; scipy supplies Spearman and PCHIP;
    pyarrow is the parquet engine that reads the LCSB corpus.
    """
    manifest = root / "artifacts" / "wur_retrieval_manifest.json"
    return {
        "python": sys.version.split()[0],
        "rdkit": rdBase.rdkitVersion,
        "pandas": pandas.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pyarrow": _pyarrow_version(),
        "git_commit_sha": _git_commit_sha(root),
        "wur_retrieval_manifest_sha256":
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }
