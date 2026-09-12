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
    every recorded hash. A key containing a literal newline would collide
    with a differently-partitioned key set under this join (e.g. ["a\\nb"]
    vs ["a", "b"]), so such a key is rejected outright rather than silently
    admitted; today's connectivity keys are InChIKey first blocks and never
    contain one.
    """
    keys = list(keys)
    for key in keys:
        if "\n" in key:
            raise ValueError(f"canonical_key_hash: key contains a newline: {key!r}")
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


def _git_tree_dirty(root: Path) -> bool | str:
    """Whether the working tree has uncommitted changes at run time.

    `git_commit_sha` alone can silently misrepresent provenance: it always
    names a clean, committed SHA, even when the tree that actually produced
    the artifact differed from that commit. This flag makes that condition
    visible instead of hiding it. In particular, an artifact generated in
    the same commit that lands it will legitimately show
    `git_tree_dirty: true`, because the artifact is written before it is
    committed -- the recorded SHA is HEAD at run time, which is normally
    the parent of the commit that carries the artifact. A reader seeing
    `true` knows to check the diff rather than trust the SHA alone; that is
    the intended signal, not noise. Same failure handling as
    `_git_commit_sha`: a subprocess failure records "unavailable" rather
    than a misleading `False`.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return bool(out.stdout.strip())
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
        "git_tree_dirty": _git_tree_dirty(root),
        "wur_retrieval_manifest_sha256":
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }
