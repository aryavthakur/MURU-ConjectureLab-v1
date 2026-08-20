"""FRESH HOLDOUT — mechanical search-completeness check, before any selection."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
CKPT = ROOT / "artifacts" / "fh_ckpt"
OUT = ROOT / "artifacts" / "fresh_holdout"

import fh_lib as fh  # noqa: E402


def main() -> int:
    from muru.discovery.checkpoint import Store
    store = Store(CKPT)
    specs = fh.all_worlds()
    retained_p = OUT / "retained_worlds.json"
    if retained_p.exists():
        keep = set(json.loads(retained_p.read_text())["world_ids"])
        specs = [s for s in specs if s.world_id in keep]

    rows, missing, seen_ids = [], [], {}
    torn = []
    for s in specs:
        be = f"{s.block}_pysr"
        seeds = fh.fh_seed_list(s.world_id)
        done = []
        for sd in seeds:
            p = store.path(be, s.world_id, sd)
            if not p.exists():
                missing.append({"world_id": s.world_id, "seed": sd,
                                "reason": "absent"})
                continue
            try:
                d = json.loads(p.read_text())
            except Exception as e:
                torn.append({"world_id": s.world_id, "seed": sd, "error": str(e)})
                continue
            if int(d.get("seed", -1)) != int(sd):
                torn.append({"world_id": s.world_id, "seed": sd,
                             "error": f"seed field {d.get('seed')} != {sd}"})
                continue
            done.append(int(sd))
            key = (s.world_id, int(sd))
            seen_ids[key] = seen_ids.get(key, 0) + 1
        rows.append({"world_id": s.world_id, "block": s.block,
                     "n_seeds_planned": len(seeds), "n_seeds_done": len(done),
                     "seeds": done})

    all_seeds = [sd for r in rows for sd in r["seeds"]]
    failures = []
    fl = OUT / "search_failures.jsonl"
    if fl.exists():
        failures = [l for l in fl.read_text().splitlines() if l.strip()]

    out = {
        "n_worlds": len(rows),
        "n_seeds_per_world_intended": fh.N_SEEDS,
        "n_units_intended": len(rows) * fh.N_SEEDS,
        "n_units_present": sum(r["n_seeds_done"] for r in rows),
        "worlds_with_full_seed_set": sum(r["n_seeds_done"] == fh.N_SEEDS
                                         for r in rows),
        "duplicate_seed_identities": len(all_seeds) - len(set(all_seeds)),
        "duplicate_world_seed_pairs": sum(1 for v in seen_ids.values() if v > 1),
        "missing_units": missing,
        "torn_or_corrupt_units": torn,
        "n_recorded_search_exceptions": len(failures),
        "per_world": rows,
    }
    out["COMPLETE"] = (out["n_units_present"] == out["n_units_intended"]
                       and not torn and out["duplicate_seed_identities"] == 0)
    (OUT / "search_completeness.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("per_world", "missing_units",
                                   "torn_or_corrupt_units")}, indent=1))
    if missing:
        print(f"MISSING {len(missing)}:", missing[:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
