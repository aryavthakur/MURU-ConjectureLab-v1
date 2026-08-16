"""Shared read-only plumbing for the MURU v1 failure decomposition.

DIAGNOSIS ONLY.  Nothing in this package mutates the sealed evidence, edits a
frozen scientific module, or re-runs a production search.  Every scientific
predicate used here is *imported* from the frozen source tree that produced the
sealed run; this package supplies only observation, aggregation, and I/O.

Two roots are read and never written:

``EVIDENCE_ROOT``
    ``.../muru-heldout-a3-6/results/held_out`` -- the sealed Held-out evidence
    named by ``execution_manifest.json``'s own ``run.output_root``.

``FROZEN_SRC``
    ``.../heldout-analysis-restoration/src`` -- the restoration worktree, whose
    diff against the run commit ``8d87143`` is *additions only* (7 new files,
    3016 insertions, 0 deletions and 0 modifications to any pre-existing
    module).  Every scientific module imported below is therefore byte-identical
    to the one the sealed run executed.

Outputs land exclusively under this diagnostic worktree's ``artifacts/``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
WORKTREES = REPO_ROOT / ".claude" / "worktrees"

EVIDENCE_ROOT = WORKTREES / "muru-heldout-a3-6" / "results" / "held_out"
RESTORED_ROOT = WORKTREES / "heldout-analysis-restoration" / "results" / "restored"
FROZEN_SRC = WORKTREES / "heldout-analysis-restoration" / "src"
DEV_ARTIFACTS = WORKTREES / "muru-development-a3-5" / "artifacts"

DIAG_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = DIAG_ROOT / "artifacts" / "diagnostics"

RUN_COMMIT = "8d87143d4280602323aa33ee0b5481aaef0fb4a8"

#: The three primary endpoints and the manifest key that declares eligibility.
ENDPOINT_KEYS = {
    "G1": "scalar_competence",
    "G2": "family_recovery",
    "G3": "principal_structural_safety",
}


def install_frozen_src() -> None:
    """Put the frozen scientific tree first on the import path."""
    path = str(FROZEN_SRC)
    if path not in sys.path:
        sys.path.insert(0, path)


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=1, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Sealed evidence
# ---------------------------------------------------------------------------


def case_id_to_stem(case_id: str) -> str:
    return case_id.replace("|", "_")


def load_sealed_records() -> dict[str, dict[str, Any]]:
    """All 240 sealed per-case records, keyed by case_id."""
    records: dict[str, dict[str, Any]] = {}
    for path in sorted((EVIDENCE_ROOT / "records").glob("*.json")):
        payload = read_json(path)
        records[payload["case_id"]] = payload
    return records


def load_seed_records() -> dict[str, list[dict[str, Any]]]:
    """All 7,200 sealed per-seed retention rows, keyed by case_id.

    Each row is one seed's single retained candidate -- the ``argmax(score)``
    row of that seed's PySR Pareto front (``rc5_selection`` section 7.1).  The
    front itself is not persisted; see ``PARETO_FRONT_NOT_PERSISTED`` in the
    decomposition report for what that bounds.
    """
    seeds: dict[str, list[dict[str, Any]]] = {}
    for path in sorted((EVIDENCE_ROOT / "seed_records").glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if rows:
            seeds[rows[0]["case_id"]] = rows
    return seeds


def load_truth() -> dict[str, dict[str, Any]]:
    """Held-out planted truth, keyed by case_id."""
    truth: dict[str, dict[str, Any]] = {}
    path = DEV_ARTIFACTS / "truth" / "held_out.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        truth[payload["case_id"]] = payload["truth"]
    return truth


def load_case_manifest() -> dict[str, dict[str, Any]]:
    """Frozen per-case manifest rows for the Held-out partition."""
    payload = read_json(REPO_ROOT / "artifacts" / "paper_benchmark_case_manifest.json")
    return {
        row["case_id"]: row
        for row in payload["cases"]
        if row["partition"] == "held_out"
    }


def eligible_case_ids(endpoint: str, manifest: dict[str, dict[str, Any]]) -> list[str]:
    """Case IDs carrying one primary endpoint, in frozen manifest order."""
    key = ENDPOINT_KEYS[endpoint]
    return [cid for cid, row in manifest.items() if key in row["applicable_endpoints"]]


def load_restored_analysis() -> dict[str, Any]:
    return read_json(RESTORED_ROOT / "heldout_restored_analysis.json")


def load_g1_recovery() -> dict[str, dict[str, Any]]:
    payload = read_json(RESTORED_ROOT / "heldout_g1_recovery.json")
    return {row["case_id"]: row for row in payload["per_case"]}


def iter_progress(items: list[Any], label: str, every: int = 20) -> Iterator[Any]:
    total = len(items)
    for index, item in enumerate(items, start=1):
        if index == 1 or index % every == 0 or index == total:
            print(f"  {label}: {index}/{total}", flush=True)
        yield item
