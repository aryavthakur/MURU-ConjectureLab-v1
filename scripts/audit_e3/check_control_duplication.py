"""INDEPENDENT check: does the mass_power control's law ignoring `c` make the
5 c-labeled worlds within a (noise, grid, replicate) triple literally
identical draws, and if so, what is the effective independent sample size
behind the n=2000 STUDY_INVALID gate statistic?

Written from scratch, reads only raw e3_worlds.jsonl.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

WORLDS_PATH = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/results/e3_identifiability/e3_worlds.jsonl")


def main():
    groups = defaultdict(list)  # (noise, grid, replicate) -> list of (c, seeds, law_params, bic_selected, false_structure_bic)
    control_rows = []
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["family"] != "mass_power":
                continue
            control_rows.append(r)
            key = (r["noise_sd"], r["grid_points"], r["replicate"])
            groups[key].append(r)

    print(f"Total mass_power rows: {len(control_rows)}")
    print(f"Distinct (noise,grid,replicate) groups: {len(groups)}")
    assert len(control_rows) == 2000

    # For each group, check whether all 5 c-labeled rows share identical seeds
    identical_seed_groups = 0
    identical_outcome_groups = 0
    non_identical_examples = []
    for key, rows in groups.items():
        seeds_set = {tuple(sorted(r["seeds"].items())) for r in rows}
        outcomes = {r["false_structure_bic"] for r in rows}
        if len(seeds_set) == 1:
            identical_seed_groups += 1
        else:
            non_identical_examples.append((key, seeds_set))
        if len(outcomes) == 1:
            identical_outcome_groups += 1

    print(f"\nGroups where all 5 c-labels share IDENTICAL seeds: {identical_seed_groups} / {len(groups)}")
    print(f"Groups where all 5 c-labels share IDENTICAL false_structure_bic outcome: {identical_outcome_groups} / {len(groups)}")
    if non_identical_examples:
        print("Non-identical seed examples (first 3):", non_identical_examples[:3])

    # Effective independent sample size for the pooled n=2000 gate statistic
    n_unique_geometries = len(groups)  # should be 4 noise x 2 grid x 50 replicate = 400
    print(f"\nExpected unique geometries (4 noise x 2 grid x 50 rep): {4*2*50}")
    print(f"Observed unique geometries: {n_unique_geometries}")

    # Compute the false-structure rate two ways: (a) naive pooled n=2000 as reported,
    # (b) deduplicated to one observation per unique geometry (n=400 effective).
    k_bic_2000 = sum(1 for r in control_rows if r["false_structure_bic"])
    n_2000 = len(control_rows)
    rate_2000 = k_bic_2000 / n_2000

    dedup_outcomes = []
    for key, rows in groups.items():
        # majority/any -- since we've shown they're identical, take the first
        dedup_outcomes.append(rows[0]["false_structure_bic"])
    k_bic_400 = sum(1 for v in dedup_outcomes if v)
    n_400 = len(dedup_outcomes)
    rate_400 = k_bic_400 / n_400

    print(f"\nPooled-as-reported: k={k_bic_2000}, n={n_2000}, rate={rate_2000:.4f}")
    print(f"Deduplicated-to-unique-geometry: k={k_bic_400}, n={n_400}, rate={rate_400:.4f}")

    def wilson(k, n, z=1.959963984540054):
        if n == 0:
            return (float("nan"), float("nan"))
        p = k / n
        denom = 1 + z * z / n
        centre = p + z * z / (2 * n)
        adj = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
        return ((centre - adj) / denom, (centre + adj) / denom)

    lo2000, hi2000 = wilson(k_bic_2000, n_2000)
    lo400, hi400 = wilson(k_bic_400, n_400)
    print(f"\nWilson 95% CI at n=2000 (as reported, TREATS DUPLICATES AS INDEPENDENT): [{lo2000:.4f}, {hi2000:.4f}]")
    print(f"Wilson 95% CI at n=400 (deduplicated, effective independent draws): [{lo400:.4f}, {hi400:.4f}]")
    print(f"\nSTUDY_INVALID threshold: 0.10")
    print(f"n=2000 Wilson upper {'EXCEEDS' if hi2000 > 0.10 else 'stays under'} 0.10")
    print(f"n=400 (dedup) Wilson upper {'EXCEEDS' if hi400 > 0.10 else 'stays under'} 0.10")

    result = {
        "total_control_rows": len(control_rows),
        "distinct_geometries": n_unique_geometries,
        "identical_seed_groups": identical_seed_groups,
        "identical_outcome_groups": identical_outcome_groups,
        "groups_total": len(groups),
        "pooled_2000": {"k": k_bic_2000, "n": n_2000, "rate": rate_2000, "wilson_lo": lo2000, "wilson_hi": hi2000},
        "dedup_400": {"k": k_bic_400, "n": n_400, "rate": rate_400, "wilson_lo": lo400, "wilson_hi": hi400},
    }
    out = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3/control_duplication.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
