"""Broader stratified extension of independent_refit_sample.py: covers every
family x every noise level x both grids x three coefficients x two
replicates (240 worlds total), to check that the independent-optimizer
agreement found on the noise=0.02/grid=6 slice holds across the whole design
space, not just the frozen operating point.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/scripts/audit_e3")
from independent_refit_sample import build_world, fit_case_scalars, split_dict, fit_independent, WORLDS_PATH

FAMILIES = ("mass_power", "mass_affine_descriptor", "mass_saturating_descriptor", "mass_interaction", "mass_exponential_descriptor")
MODEL_IDS = ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter")


def main():
    originals = {}
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            originals[r["world_id"]] = r

    sample_ids = []
    for fam in FAMILIES:
        for noise in (0.0, 0.02, 0.0295, 0.06):
            for grid in (6, 12):
                for c in (0.25, 0.55, 2.2):
                    for rep in (5, 41):
                        wid = f"V2C|E3|{fam}|c{c:g}|noise{noise:g}|grid{grid}|r{rep:03d}"
                        if wid in originals:
                            sample_ids.append(wid)
    print(f"broad sample size: {len(sample_ids)}")

    n_match, n_total, max_bic_diff, mismatches = 0, 0, 0.0, []
    for wid in sample_ids:
        orig = originals[wid]
        fam, c, noise, grid, rep = orig["family"], orig["c"], orig["noise_sd"], orig["grid_points"], orig["replicate"]
        world = build_world(fam, c, noise, grid, rep)
        scalars = fit_case_scalars(world.compounds, world.trajectories)
        cwg = world.compounds.assign(g=scalars.g)
        train, val, test = split_dict(cwg, "train"), split_dict(cwg, "validation"), split_dict(cwg, "test")
        my_bics = {}
        for mid in MODEL_IDS:
            fit = fit_independent(mid, train, val, test)
            my_bics[mid] = fit["bic"]
            ob = orig["models"][mid]["bic"]
            if ob is not None:
                max_bic_diff = max(max_bic_diff, abs(fit["bic"] - ob))
        my_sel = min(my_bics, key=my_bics.get)
        n_total += 1
        if my_sel == orig["bic_selected_model"]:
            n_match += 1
        else:
            mismatches.append({"world_id": wid, "orig": orig["bic_selected_model"], "mine": my_sel})

    result = {
        "sample_size": n_total,
        "agreement": n_match,
        "agreement_pct": 100 * n_match / n_total,
        "max_abs_bic_diff": max_bic_diff,
        "mismatches": mismatches,
    }
    print(json.dumps(result, indent=2))
    out = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3/independent_refit_sample_broad.json"
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
