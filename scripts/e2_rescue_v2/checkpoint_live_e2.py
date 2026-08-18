#!/usr/bin/env python
"""Part XIII, migration step 1-2: read-only snapshot + hash manifest of the
live E2a run's current output. Mirrors the ORIGINAL rescue's own
pre-intervention snapshot discipline
(`E2_EXECUTION_DEVIATION.md` section 3: chmod 444 + SHA-256 manifest)
rather than inventing a new one.

Reads ONLY: file bytes (for hashing) and `world_id`/`wall_seconds` fields
(for the population-accounting summary, mirroring the rolling reporter's
own "completed + remaining + quarantined == 540" self-check, which is what
caught a real duplicate-recomputation bug during the original rescue --
E2_EXECUTION_DEVIATION.md section 16). Never reads `first_loss_stage` or
any other scientific field. Writes ONLY under `--out-dir` (never into the
live worktree).

Usage:
    checkpoint_live_e2.py --result-dir DIR [DIR ...] --out-dir SNAPSHOT_DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--out-dir", type=str, required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}
    world_ids = set()
    n_with_timing = 0
    total_wall_seconds = 0.0

    for d in args.dirs:
        d = Path(d)
        for path in sorted(d.glob("*")):
            if not path.is_file():
                continue
            rel = f"{d.name}/{path.name}"
            manifest[rel] = {"sha256": _sha256_file(path), "bytes": path.stat().st_size}
            if path.name.startswith("worlds_shard_") and path.suffix == ".jsonl":
                with path.open() as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        wid = rec.get("world_id")
                        if wid and wid not in world_ids:
                            world_ids.add(wid)
                            ws = rec.get("wall_seconds")
                            if ws is not None:
                                total_wall_seconds += ws
                                n_with_timing += 1

    summary = {
        "n_unique_world_ids": len(world_ids),
        "of_540": f"{len(world_ids)}/540",
        "n_with_timing_field": n_with_timing,
        "total_wall_seconds_timing_only": total_wall_seconds,
        "n_files_hashed": len(manifest),
        "note": "world_id membership and wall_seconds (timing) only -- no scientific outcome field read or recorded",
    }

    (out_dir / "checkpoint_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    (out_dir / "checkpoint_summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "checkpoint_world_ids.txt").write_text("\n".join(sorted(world_ids)) + "\n")

    print(f"n_unique_world_ids: {summary['n_unique_world_ids']}/540")
    print(f"n_files_hashed: {summary['n_files_hashed']}")
    print(f"written to {out_dir}")


if __name__ == "__main__":
    main()
