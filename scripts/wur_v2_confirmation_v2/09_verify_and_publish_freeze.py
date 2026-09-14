"""MSnLib confirmation study 2, protocol V2 section 10: verify the freeze read-only, then publish it once.

`--verify-only` runs every look-time check without writing anything. Without it, publication follows only if the
verification passes: the freeze commit is registered locally and refs/muru-freeze/<study> is pushed create-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402


def main() -> int:
    summary = DA.verify_freeze_candidate()
    print(json.dumps({"verified": True, **summary}, indent=1))
    if "--verify-only" in sys.argv[1:]:
        return 0
    head = DA.publish_freeze()
    print(json.dumps({"published_freeze_commit": head, "ref": DA.FREEZE_REF}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
