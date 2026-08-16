"""Assemble the machine-readable audit JSON twin from the raw audit result
files under results/audit_e3/. Pure aggregation of THIS audit's own outputs
-- does not read anything from the object under audit beyond what those
files already captured.
"""
import json
from pathlib import Path

BASE = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent")
RESULTS = BASE / "results" / "audit_e3"


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def main():
    completeness = load("independent_completeness.json")
    duplication = load("control_duplication.json")
    recompute = load("independent_recompute.json")
    robustness = load("robustness_scan.json")
    refit_75 = load("independent_refit_sample.json")
    refit_240 = load("independent_refit_sample_broad.json")

    out = {
        "audit": "MURU_V2_E3_INDEPENDENT_HOSTILE_AUDIT",
        "status": "COMPLETE",
        "object_under_audit": {
            "branch": "exp/v2-e3-identifiability",
            "commit": "1d20731",
            "worktree": ".claude/worktrees/muru-v2-e3-identifiability-b23a7b",
        },
        "auditor": {
            "branch": "audit/v2-e3-independent",
            "worktree": ".claude/worktrees/audit-v2-e3-independent",
        },
        "verdict": {
            "execution_real_and_complete": True,
            "headline_arithmetic_correct": True,
            "f09_remediation_license_survives": True,
            "conclusions_requiring_weakening": [
                "STUDY_INVALID gate Wilson-upper-bound framing understates true uncertainty "
                "(0.128 correctly, not 0.109 as reported) due to mass_power's control population "
                "having only 400 independent draws, not the nominal 2000. Formal point-estimate-based "
                "pass (0.095 < 0.10) is unaffected and stands."
            ],
            "conclusions_requiring_retraction": [],
        },
        "q1_10000_worlds_200_cells": completeness,
        "q8_q9_study_validity_and_sensitivity": duplication,
        "q10_q11_q12_q13_recomputation": recompute,
        "robustness_appendix": {
            "convergence_and_bic_margins": robustness,
            "independent_refit_75_worlds_noise0.02_grid6": refit_75,
            "independent_refit_240_worlds_full_grid": refit_240,
        },
        "discrepancy_ledger": [
            {"id": "D1", "item": "Study validity Wilson upper bound (BIC)", "independent": 0.1277, "reported": 0.109,
             "status": "DISCREPANCY", "classification": "MATERIAL_NONBLOCKING",
             "explanation": "mass_power's law ignores c; 400/400 (noise,grid,replicate) groups are byte-identical "
                             "across their 5 c-labels (verified). True independent n=400, not 2000. Point estimate "
                             "(0.095) unaffected; only the CI precision claim is wrong."},
            {"id": "D2", "item": "All other headline rates/tables", "status": "EXACT_MATCH", "classification": "NONE"},
            {"id": "D3", "item": "Manifest/execution completeness", "status": "EXACT_MATCH", "classification": "NONE"},
            {"id": "D4", "item": "PySR absence (static+dynamic, broadened)", "status": "CONFIRMED", "classification": "NONE"},
            {"id": "D5", "item": "Frozen estimator byte-identity vs sealed commit 8d87143", "status": "CONFIRMED", "classification": "NONE"},
            {"id": "D6", "item": "registry.resolve_case_id static check (design doc section 2.2)", "status": "NOT_IMPLEMENTED",
             "classification": "MINOR", "explanation": "Practically inert (ID formats structurally incompatible), but the specific check the design document describes was not built in E3's own code."},
            {"id": "D7", "item": "Confusion matrix at frozen operating point", "status": "EXACT_MATCH", "classification": "NONE"},
            {"id": "D8", "item": "BIC formula convention", "status": "CONFIRMED_CORRECT", "classification": "NONE"},
            {"id": "D9", "item": "Fit convergence (50,000 fits)", "status": "100_PERCENT_CONVERGED", "classification": "NONE"},
            {"id": "D10", "item": "Artifact hashes (e3_hashes.json, 15 files)", "status": "EXACT_MATCH_SHA256", "classification": "NONE"},
            {"id": "D11", "item": "v1-observed F02/F03/F09/F18 reference counts", "status": "TRACED_EXACT", "classification": "NONE"},
            {"id": "D12", "item": "Design commit precedes execution commit (git ancestry)", "status": "CONFIRMED", "classification": "NONE"},
        ],
        "findings": [
            {
                "id": "F-1",
                "classification": "MATERIAL_NONBLOCKING",
                "summary": "STUDY_INVALID gate's Wilson-interval framing computed on an inflated, non-independent "
                            "sample size (n=2000 nominal vs n=400 true independent draws for the mass_power control).",
                "detail": "mass_power's truth law does not consume c, so the 5 c-labeled worlds within each of the "
                          "400 (noise,grid,replicate) triples are byte-identical (verified 400/400). Correct Wilson "
                          "95% upper bound on k=38/n=400 is 0.1277, not the reported 0.109 (k=190/n=2000). Does not "
                          "flip the formal VALID verdict (defined on the point estimate 0.095, unaffected), but "
                          "materially undermines the report's own 'narrow pass, not comfortable' confidence claim -- "
                          "properly accounted, the pass is even less comfortable. Same inflation affects every other "
                          "pooled mass_power statistic in the report (concretely verified for the frozen-operating-"
                          "point confusion matrix's mass_power row: reported 15/150 leak to mass_interaction is "
                          "5 independent geometries out of 50, tripled).",
            },
            {
                "id": "F-2",
                "classification": "MINOR",
                "summary": "Design doc's registry.resolve_case_id collision check (section 2.2) not implemented in E3's own code.",
                "detail": "Only the seed-prefix-disjointness half of the design's stated static check exists in "
                          "v2c_generator.py; no test calls registry.resolve_case_id on a V2C-namespaced id. "
                          "Practically inert given the structurally incompatible ID formats, but a documented "
                          "governance mechanism was not built as described.",
            },
            {
                "id": "F-3",
                "classification": "MINOR",
                "summary": "Section 12's 'DATA-LIMITED' framing for affine/exponential reads more assertive than the "
                            "frozen decision tree's own 'MARGINAL licenses nothing on its own' language.",
                "detail": "Substantively earned by the additional noise-free-arm (H_id_noise) evidence the report "
                          "cites, but should be read as 'not attributable to search from this cell alone,' not as a "
                          "flat dispositive diagnosis. No numbers are wrong; interpretation/phrasing note only.",
            },
            {
                "id": "F-4",
                "classification": "NONE",
                "summary": "Every other checked item reproduced exactly under independent, from-scratch recomputation.",
            },
        ],
    }

    out_path = BASE / "MURU_V2_E3_INDEPENDENT_HOSTILE_AUDIT.json"
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
