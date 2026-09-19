"""Design B step 30: deterministic candidate ordering over the frozen sourcing frame.

No human choice and no seed: each candidate's key is sha256(study_id | frame_sha256 | stratum | parent_key),
hex, sorted ascending within stratum. Metadata only. Writes procurement/ordered_queues.csv.
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
OUT = ROOT / "artifacts/ce_interface_adjudication/design_b/procurement/ordered_queues.csv"


def ordering_key(stratum: str, parent_key: str, frame_sha: str = C.FRAME_SHA256) -> str:
    return hashlib.sha256(f"{C.STUDY_ID}|{frame_sha}|{stratum}|{parent_key}".encode()).hexdigest()


def build(frame: pd.DataFrame, frame_sha: str = C.FRAME_SHA256) -> pd.DataFrame:
    if frame["parent_key"].duplicated().any():
        raise SystemExit("refusing: duplicate parent_key in the sourcing frame")
    q = frame.copy()
    q["ordering_key"] = [ordering_key(s, k, frame_sha) for s, k in zip(q["stratum"], q["parent_key"])]
    q = q.sort_values(["stratum", "ordering_key"], kind="mergesort")
    q["rank"] = q.groupby("stratum").cumcount() + 1
    return q[["stratum", "rank", "ordering_key"] + [c for c in frame.columns if c != "stratum"]]


def main() -> int:
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    path = ROOT / C.FRAME_REL
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != C.FRAME_SHA256:
        raise SystemExit(f"refusing: sourcing frame sha256 {got} != frozen {C.FRAME_SHA256}")
    q = build(pd.read_csv(path))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    q.to_csv(OUT, index=False)
    print(q.groupby("stratum").size().to_dict(), hashlib.sha256(OUT.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
