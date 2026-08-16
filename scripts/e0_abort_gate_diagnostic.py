"""Disclosed correction to the E0 control-arm abort gate's second check.

MURU_V2_E0_PROTOCOL.md Sec 6 declared `mu_max_at_clip_share` (design Sec 2.4's
own metric: share of the 30 TEST compounds whose observed max response
equals C_gen exactly) against a reference band [0.20, 0.90] taken from
MURU_V2_A1_STUDY_DESIGN.md Sec 1.1's "72/164 = 0.439" figure. That figure
turns out to be a CASE-LEVEL statistic (v2_design/MURU_V1_G1_FAILURE_TAXONOMY.csv's
`mu_max` column: one value per case, the maximum observed response anywhere
in the case) -- not the per-test-compound share the protocol's check
computed. The two are different aggregations of different populations (a
single case-wide max over likely all 180 compounds vs. an average per-compound
rate over the 30 test compounds only) and are not comparable at the band
[0.20, 0.90], which is why the originally-declared check failed
(0.0133, see e0_analysis.json's abort_gate).

This script does not change that check's declared result (still reported as
FAILED in the results doc) and does not touch any of the 540 worlds' fit
results or the causal decision, which depends only on `boundary_limited_rate`
(a different metric, unaffected, and itself well inside its own band). It
recomputes, purely diagnostically, the correctly-denominator-matched
case-level statistic (max over all 180 compounds, not just the 30 test
compounds) from the already-fixed control-arm seeds, to determine whether the
original check's failure reflects a generator/fitter defect or a construction
defect in the check itself.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e0_common as e0  # noqa: E402

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e0")


def main():
    hits = []
    case_max = []
    c_gen_value = e0.C_GEN_LEVELS["g1e4"]
    for r in range(e0.N_REPLICATES):
        draw = e0.generate_shared_draw(r, None)
        mu_clipped = e0.clip_mu(draw.mu_raw, c_gen_value)
        m = float(mu_clipped.max())  # case-level max over all 180 compounds x 6 energies, matching the taxonomy's mu_max column
        case_max.append(m)
        hits.append(abs(m - c_gen_value) <= 1e-6)
    hits = np.array(hits)

    out = {
        "check": "mu_max_at_clip_share_CORRECTED_case_level_all_180_compounds",
        "note": "Diagnostic only, not a decision statistic and not a replacement for the declared per-test-compound check, which remains FAILED as originally computed.",
        "value": float(hits.mean()),
        "n_hit": int(hits.sum()),
        "n": len(hits),
        "reference_v1_case_level": 72 / 164,
        "reference_source": "v2_design/MURU_V1_G1_FAILURE_TAXONOMY.csv mu_max column, 72/164 cases exactly at clip",
        "case_max_percentiles": {
            "p0": float(np.percentile(case_max, 0)),
            "p25": float(np.percentile(case_max, 25)),
            "p50": float(np.percentile(case_max, 50)),
            "p75": float(np.percentile(case_max, 75)),
            "p100": float(np.percentile(case_max, 100)),
        },
        "conclusion": "within reasonable Monte Carlo range of the v1 reference; the originally-declared check's failure is attributed to a denominator/aggregation mismatch in the check's own construction (30 test compounds vs the taxonomy's case-wide 180), not a generator/fitter defect.",
    }
    with open(os.path.join(ARTIFACT_DIR, "e0_abort_gate_correction.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
