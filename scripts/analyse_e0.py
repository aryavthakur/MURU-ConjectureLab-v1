#!/usr/bin/env python
"""Run the preregistered E0 analysis, once.

Refuses to run unless `scripts/verify_e0_design_fidelity.py` has passed on the
corpus, and refuses to run twice without `--rerun`, which is recorded in the
output.  Every threshold it applies is fixed in `muru.v2_calibration.e0_cells`
and `MURU_V2_E0_PROTOCOL.md`, both committed before the corpus existed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from muru.v2_calibration.e0_analysis import analyse  # noqa: E402

OUT = REPO / "artifacts" / "e0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true", help="overwrite an existing analysis")
    args = parser.parse_args()

    fidelity_path = OUT / "e0_design_fidelity.json"
    if not fidelity_path.exists():
        print("REFUSED: run scripts/verify_e0_design_fidelity.py first", file=sys.stderr)
        return 2
    fidelity = json.loads(fidelity_path.read_text())
    if not fidelity["passed"]:
        print(f"REFUSED: design fidelity failed: {fidelity['failed']}", file=sys.stderr)
        return 2

    result_path = OUT / "e0_analysis.json"
    if result_path.exists() and not args.rerun:
        print("REFUSED: an analysis already exists; pass --rerun to overwrite", file=sys.stderr)
        return 3

    worlds = pd.read_csv(OUT / "e0_worlds.csv")
    fits = pd.read_parquet(OUT / "e0_fits.parquet")
    report = analyse(worlds, fits)
    report["design_fidelity_passed"] = True
    report["rerun"] = bool(args.rerun)

    result_path.write_text(json.dumps(report, indent=2, default=str))

    # Machine-readable per-cell table.
    rows = []
    for cell_id, m in report["cell_metrics"].items():
        rows.append({
            "cell_id": cell_id,
            "generator_clip_level": m["generator_clip_level"],
            "fitter_ceil_level": m["fitter_ceil_level"],
            "coupled": m["coupled"],
            "n_worlds": m["n_worlds"],
            "boundary_limited_rate": m["boundary_limited_rate"]["rate"],
            "boundary_limited_wilson_lower": m["boundary_limited_rate"]["wilson_lower_95"],
            "boundary_limited_wilson_upper": m["boundary_limited_rate"]["wilson_upper_95"],
            "m0_not_rejected_rate": m["m0_not_rejected_rate"]["rate"],
            "false_rejection_rate": m["false_rejection_rate"]["rate"],
            "contact_rate": m["contact_rate"]["rate"],
            "unresolved_rate": m["unresolved_rate"]["rate"],
            "pin_at_ceiling_share": m["pin_at_ceiling_share"]["rate"],
            "evaluable_M3_mean": m["evaluable_M3"]["mean"],
            "evaluable_M3_below_floor_24": m["evaluable_M3"]["below_floor_24"],
            "probe_gain_rel_median": m["probe_gain_rel"]["median"],
            "probe_gain_rel_max": m["probe_gain_rel"]["max"],
            "mu_max_at_clip_share": (m["mu_max_at_clip_share"] or {}).get("rate"),
            "mu_max_at_v1_constant_share": m["mu_max_at_v1_constant_share"]["rate"],
            "modal_dominant_bound": m["modal_dominant_bound"],
        })
    pd.DataFrame(rows).to_csv(OUT / "e0_cell_metrics.csv", index=False)
    pd.DataFrame(report["contrasts"].values()).to_csv(OUT / "e0_contrast_table.csv", index=False)

    print(json.dumps({
        "abort_gate_passed": report["abort_gate"]["passed"],
        "decision": report["decision"],
        "blocked_reason": report["blocked_reason"],
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
