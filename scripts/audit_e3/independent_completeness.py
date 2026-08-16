"""INDEPENDENT hostile-audit check: manifest/execution completeness.

Written from scratch for the audit. Does NOT import manifest.py, run_e3.py,
aggregate_e3.py, or hostile_audit_e3.py from the E3 branch. Re-derives the
expected 200-cell / 10,000-world Cartesian product from the FROZEN DESIGN
DOCUMENT's stated factor levels (transcribed by hand from
MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md section 3.2/3.6), and checks the
raw e3_worlds.jsonl and e3_manifest.json against it independently.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

E3_DIR = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b")
WORLDS_PATH = E3_DIR / "results" / "e3_identifiability" / "e3_worlds.jsonl"
MANIFEST_PATH = E3_DIR / "results" / "e3_identifiability" / "e3_manifest.json"

# Transcribed independently from the frozen design doc (section 3.2, 3.6),
# NOT copy-pasted from manifest.py's constants.
FAMILIES = (
    "mass_power",
    "mass_affine_descriptor",
    "mass_saturating_descriptor",
    "mass_interaction",
    "mass_exponential_descriptor",
)
COEFFICIENTS = (0.25, 0.40, 0.55, 1.1, 2.2)
NOISE_LEVELS = (0.0, 0.02, 0.0295, 0.06)
GRID_POINTS = (6, 12)
N_REPLICATES = 50


def g(x: float) -> str:
    """Python %g formatting, matching the world_id scheme observed in the data."""
    return f"{x:g}"


def expected_world_id(family, c, noise, grid, rep) -> str:
    return f"V2C|E3|{family}|c{g(c)}|noise{g(noise)}|grid{grid}|r{rep:03d}"


def main():
    expected_ids = set()
    expected_cells = set()
    for family, c, noise, grid, rep in itertools.product(FAMILIES, COEFFICIENTS, NOISE_LEVELS, GRID_POINTS, range(N_REPLICATES)):
        expected_ids.add(expected_world_id(family, c, noise, grid, rep))
        expected_cells.add((family, g(c), g(noise), grid))

    expected_total = len(FAMILIES) * len(COEFFICIENTS) * len(NOISE_LEVELS) * len(GRID_POINTS) * N_REPLICATES
    print(f"Independently-derived expected total: {expected_total}")
    print(f"Independently-derived expected unique world_ids: {len(expected_ids)}")
    print(f"Independently-derived expected cell count: {len(expected_cells)}")
    assert expected_total == 10_000
    assert len(expected_ids) == 10_000
    assert len(expected_cells) == 200

    # --- raw JSONL, read line by line, no pandas, no aggregate_e3 ---
    executed_ids = []
    statuses = []
    families_seen = set()
    cs_seen = set()
    noise_seen = set()
    grid_seen = set()
    cell_replicate_map = {}
    world_lines = 0
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            world_lines += 1
            r = json.loads(line)
            executed_ids.append(r["world_id"])
            statuses.append(r["status"])
            families_seen.add(r["family"])
            cs_seen.add(r["c"])
            noise_seen.add(r["noise_sd"])
            grid_seen.add(r["grid_points"])
            key = (r["family"], g(r["c"]), g(r["noise_sd"]), r["grid_points"])
            cell_replicate_map.setdefault(key, set()).add(r["replicate"])

    executed_id_set = set(executed_ids)
    n_ok = sum(1 for s in statuses if s == "OK")
    n_fail = len(statuses) - n_ok

    print(f"\nRaw JSONL line count: {world_lines}")
    print(f"Executed unique world_id count: {len(executed_id_set)}")
    print(f"Duplicate world_id rows: {len(executed_ids) - len(executed_id_set)}")
    print(f"status == OK: {n_ok}  /  non-OK: {n_fail}")
    print(f"families observed: {sorted(families_seen)}")
    print(f"c levels observed: {sorted(cs_seen)}")
    print(f"noise levels observed: {sorted(noise_seen)}")
    print(f"grid levels observed: {sorted(grid_seen)}")

    missing = expected_ids - executed_id_set
    extra = executed_id_set - expected_ids
    print(f"\nMissing (expected but not executed): {len(missing)}")
    if missing:
        print("  sample:", sorted(missing)[:10])
    print(f"Extra (executed but not expected): {len(extra)}")
    if extra:
        print("  sample:", sorted(extra)[:10])

    bad_cells = {k: sorted(v) for k, v in cell_replicate_map.items() if v != set(range(N_REPLICATES))}
    print(f"\nCells with wrong replicate set (independent check): {len(bad_cells)}")
    if bad_cells:
        for k, v in list(bad_cells.items())[:5]:
            print("  ", k, "->", v)

    observed_cells = set(cell_replicate_map.keys())
    missing_cells = expected_cells - observed_cells
    extra_cells = observed_cells - expected_cells
    print(f"Missing cells (independent): {len(missing_cells)}")
    print(f"Extra cells (independent): {len(extra_cells)}")

    # --- cross-check against the persisted manifest file too (structural, not trusting its own self-check) ---
    manifest_obj = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_rows = manifest_obj["rows"]
    manifest_ids = {r["world_id"] for r in manifest_rows}
    print(f"\ne3_manifest.json row count: {len(manifest_rows)}")
    print(f"e3_manifest.json unique world_ids: {len(manifest_ids)}")
    print(f"manifest_ids == independently-derived expected_ids: {manifest_ids == expected_ids}")
    print(f"manifest_ids == executed_id_set: {manifest_ids == executed_id_set}")

    overall_pass = (
        expected_ids == executed_id_set
        and len(executed_ids) == len(executed_id_set)
        and n_ok == 10_000
        and not bad_cells
        and not missing_cells
        and not extra_cells
        and manifest_ids == expected_ids
    )
    print(f"\n=== INDEPENDENT COMPLETENESS CHECK: {'PASS' if overall_pass else 'FAIL'} ===")

    result = {
        "expected_total": expected_total,
        "raw_jsonl_line_count": world_lines,
        "executed_unique_world_count": len(executed_id_set),
        "duplicate_rows": len(executed_ids) - len(executed_id_set),
        "n_ok": n_ok,
        "n_non_ok": n_fail,
        "missing_worlds": len(missing),
        "extra_worlds": len(extra),
        "bad_cells": len(bad_cells),
        "missing_cells": len(missing_cells),
        "extra_cells": len(extra_cells),
        "manifest_matches_expected": manifest_ids == expected_ids,
        "manifest_matches_executed": manifest_ids == executed_id_set,
        "overall_pass": overall_pass,
    }
    out = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3/independent_completeness.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
