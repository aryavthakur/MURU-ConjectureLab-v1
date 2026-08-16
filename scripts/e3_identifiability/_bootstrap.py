"""Puts the frozen scientific source tree on sys.path, read-only.

Same pattern as scripts/diagnostics/muru_v1_diag_common.py's
`install_frozen_src`: the frozen tree lives in a sibling worktree
(`heldout-analysis-restoration`), whose diff against the sealed run commit
`8d87143` is additions only. Importing from it gives byte-identical
`generator`/`rc5_estimate`/`discovery.estimate`/`discovery.grammar` modules
to the ones the sealed v1 run executed, without merging git history and
without copying or modifying a single frozen file. Every module imported
through this path is read, never written.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
FROZEN_SRC = REPO_ROOT / ".claude" / "worktrees" / "heldout-analysis-restoration" / "src"
FROZEN_SRC_RUN_COMMIT = "8d87143d4280602323aa33ee0b5481aaef0fb4a8"

_THIS_DIR = Path(__file__).resolve().parent


def install() -> None:
    for path in (str(FROZEN_SRC), str(_THIS_DIR)):
        if path not in sys.path:
            sys.path.insert(0, path)


install()
