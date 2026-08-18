"""Unit-level checkpointing.

Phase 2 lost substantial time to poor execution planning (BACKLOG I4). Phase 3
checkpoints at the finest unit that exists — one (block, world, seed) symbolic
run — so a crash costs at most the units currently in flight.

Guarantees, each covered by a test in `tests/test_p3_checkpoint.py`:

* a completed unit is detected and never recomputed,
* a partial run resumes from the next incomplete unit,
* aggregation is invariant to the order units completed in,
* an interrupted write cannot corrupt a completed artifact (tmp + atomic
  rename), so a half-written file is never mistaken for a result.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

CHECKPOINT_VERSION = "p3-ckpt-1.0.0"


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, block: str, world: str, unit: str | int) -> Path:
        safe = str(world).replace("/", "_").replace("|", "~")
        return self.root / block / safe / f"{unit}.json"

    def done(self, block: str, world: str, unit: str | int) -> bool:
        p = self.path(block, world, unit)
        if not p.exists():
            return False
        try:
            json.loads(p.read_text())
            return True
        except (json.JSONDecodeError, OSError):
            # A truncated file is not a result. Treat it as incomplete so the
            # unit is recomputed rather than silently believed.
            return False

    def write(self, block: str, world: str, unit: str | int, payload: dict) -> Path:
        p = self.path(block, world, unit)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, default=str))
        os.replace(tmp, p)          # atomic on POSIX
        return p

    def read(self, block: str, world: str, unit: str | int) -> dict:
        return json.loads(self.path(block, world, unit).read_text())

    def read_world(self, block: str, world: str) -> dict[str, dict]:
        """All completed units for a world, keyed by unit id.

        Sorted glob, so aggregation does not depend on completion order.
        """
        safe = str(world).replace("/", "_").replace("|", "~")
        d = self.root / block / safe
        if not d.exists():
            return {}
        out = {}
        for p in sorted(d.glob("*.json")):
            try:
                out[p.stem] = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                continue
        return out

    def pending(self, block: str, world: str, units: Iterable) -> list:
        return [u for u in units if not self.done(block, world, u)]

    def count(self, block: str | None = None) -> int:
        base = self.root / block if block else self.root
        return sum(1 for _ in base.rglob("*.json")) if base.exists() else 0
