"""Master script to generate all MURU Pre-Results tables.

Produces publication-quality tables in Markdown (.md), LaTeX (.tex), and JSON (.json):
1. Table 1: Benchmark case families & partition hierarchy (table_01_case_families)
2. Table 2: Frozen endpoints & success definitions (table_02_endpoints)
3. Table 3: Primary gates summary & umbrella claim (table_03_primary_gates)
4. Table 4: Secondary & diagnostic endpoints (table_04_secondary_endpoints)
5. Table 5: Null calibration design & threshold shells (table_05_calibration_design)
6. Table 6: A3.4 12 Predictive-Equivalence reference frames (table_06_reference_frames)
7. Table 7: Governance & amendment audit ledger (table_07_governance_amendments)
8. Table 8: Reproducibility & software dependency stack (table_08_reproducibility_dependencies)
9. Table 9: Scientific claim boundaries & forbidden overclaims (table_09_claim_boundaries)

Binding rule: No prospective result numerator populated ([PROSPECTIVE RESULT TO INSERT]).
"""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
TABLES_DIR = SCRIPTS_DIR.parents[1] / "tables" / "pre_results"

def save_table(name: str, md_content: str, tex_content: str, json_data: dict | list) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    
    md_file = TABLES_DIR / f"{name}.md"
    tex_file = TABLES_DIR / f"{name}.tex"
    json_file = TABLES_DIR / f"{name}.json"
    
    md_file.write_text(md_content.strip() + "\n", encoding="utf-8")
    tex_file.write_text(tex_content.strip() + "\n", encoding="utf-8")
    json_file.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")
    
    print(f"Generated {name}:\n  [MD] {md_file.name}\n  [TEX] {tex_file.name}\n  [JSON] {json_file.name}")

def build_table_01() -> None:
    """Table 1: Benchmark Case Families."""
    families = [
        {"family": "F01", "name": "noiseless scalar collapse", "question": "recover unambiguous collapse", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, exact algebra"},
        {"family": "F02", "name": "moderate-noise scalar collapse", "question": "recover under moderate noise", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F03", "name": "stronger realistic noise", "question": "characterize graceful degradation", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F04", "name": "missing-one-energy", "question": "recover with declared missingness", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F05", "name": "boundary-scale", "question": "detect profile boundaries", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, boundary hit"},
        {"family": "F06", "name": "no molecule-specific scalar truth", "question": "reject an unsupported scalar", "scalar_truth": "no", "m0_truth": "M1", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "M1 sensitivity"},
        {"family": "F07", "name": "mass-only g truth", "question": "avoid invented non-mass structure", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "mass only", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, parameter recovery, false extra structure, structural safety"},
        {"family": "F08", "name": "simple descriptor law", "question": "recover a monotone descriptor law", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, exact algebra"},
        {"family": "F09", "name": "nonlinear descriptor law", "question": "recognize saturation", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, exact algebra"},
        {"family": "F10", "name": "interaction law", "question": "recognize interpretable interaction", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, exact algebra"},
        {"family": "F11", "name": "irrelevant distractors", "question": "exclude independent nuisance variables", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F12", "name": "correlated distractors", "question": "separate support from correlation", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F13", "name": "horizontal-shape violation", "question": "detect M1", "scalar_truth": "no", "m0_truth": "M1", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "M1 sensitivity"},
        {"family": "F14", "name": "high-energy vertical violation", "question": "detect M2", "scalar_truth": "no", "m0_truth": "M2", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "M2 sensitivity"},
        {"family": "F15", "name": "low-energy vertical violation", "question": "detect M3", "scalar_truth": "no", "m0_truth": "M3", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "M3 sensitivity"},
        {"family": "F16", "name": "combined mild non-scalar violation", "question": "flag combined violations", "scalar_truth": "no", "m0_truth": "M1+M2+M3", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "M1, M2, M3 sensitivity, scored independently"},
        {"family": "F17", "name": "equivalent symbolic forms", "question": "canonicalize equivalent laws", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic, exact algebra"},
        {"family": "F18", "name": "algebraically difficult, predictively simple", "question": "separate prediction from exact algebra", "scalar_truth": "yes", "m0_truth": "M0", "symbolic_truth": "defined", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "scalar, symbolic"},
        {"family": "F19", "name": "target-specific null worlds", "question": "prevent specified null structure from being accepted", "scalar_truth": "by variant", "m0_truth": "by variant", "symbolic_truth": "none / mass-only allowance", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "false null structure, structural safety; scalar for F19A/B"},
        {"family": "F20", "name": "adversarial worlds", "question": "reject or flag specified traps", "scalar_truth": "no", "m0_truth": "not applicable", "symbolic_truth": "none", "dev": 4, "held_out": 12, "challenge": 3, "endpoint_groups": "false adversarial structure, structural safety"},
    ]
    
    md = "# Table 1. Benchmark Partitions and Case Families\n\n"
    md += "**Status: Fully populated from frozen sources.** Total: 380 cases (80 Dev, 240 Held-out, 60 Challenge).\n\n"
    md += "| Family | Name | Scientific Question | Scalar Truth | M0 Truth | Symbolic Truth | Dev | Held-out | Challenge | Applicable Endpoints |\n"
    md += "|---|---|---|---|---|---|---:|---:|---:|---|\n"
    for r in families:
        md += f"| {r['family']} | {r['name']} | {r['question']} | {r['scalar_truth']} | {r['m0_truth']} | {r['symbolic_truth']} | {r['dev']} | {r['held_out']} | {r['challenge']} | {r['endpoint_groups']} |\n"
    md += "| **Total** | | | | | | **80** | **240** | **60** | |\n\n"
    
    md += "### Table 1a. F19 and F20 Variant Semantics\n\n"
    md += "| Variant | Mechanism | Scalar Truth | M0 Truth | Symbolic Truth | Correct Behaviour |\n"
    md += "|---|---|---|---|---|---|\n"
    md += "| F19A | descriptor-link permutation | yes | M0 | none | Mass-only permitted; unsupported non-mass unsafe. Carries scalar endpoints. |\n"
    md += "| F19B | mass-preserving target null | yes | M0 | mass-only | Mass-only permitted; accepted non-mass unsafe. Carries scalar endpoints. |\n"
    md += "| F19C | response-cell resampling | no | n/a | none | Flag non-evaluable; accepted structure unsafe; UNEVALUABLE is violation. Excluded from scalar/symbolic. |\n"
    md += "| F20A | latent driver | no | n/a | none | Reject latent-driver trap. |\n"
    md += "| F20B | measurement coupling | no | n/a | none | Reject measurement-coupling trap. |\n"
    md += "| F20C | out-of-grammar trap | no | n/a | none | Reject out-of-grammar trap (generating law outside grammar). |\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Benchmark Partitions and Case Families (380 Total Cases).}
\label{tab:case_families}
\begin{tabular}{llllcccc}
\toprule
Family & Name & Scientific Question & Truth & Dev & Held-out & Challenge & Endpoints \\
\midrule
"""
    for r in families:
        tex += f"{r['family']} & {r['name']} & {r['question']} & {r['m0_truth']} & {r['dev']} & {r['held_out']} & {r['challenge']} & {r['endpoint_groups']} \\\\\n"
    tex += r"""\midrule
\textbf{Total} & & & & \textbf{80} & \textbf{240} & \textbf{60} & \\
\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_01_case_families", md, tex, families)

def build_table_02() -> None:
    """Table 2: Frozen Endpoints and Success Criteria."""
    endpoints = [
        {"endpoint": "scalar competence (G1)", "role": "PRIMARY", "denominator": 164, "definition": "Spearman >= 0.80 AND MAE <= 0.80 x baseline AND M0_NOT_REJECTED", "gate": "Wilson lower >= 0.70", "failure_handling": "fails G1"},
        {"endpoint": "family recovery (G2)", "role": "PRIMARY", "denominator": 144, "definition": "support_status == MATCH AND family_status == MATCH", "gate": "Wilson lower >= 0.70", "failure_handling": "fails G2"},
        {"endpoint": "principal structural safety (G3)", "role": "PRIMARY", "denominator": 36, "definition": "Unsafe structural acceptance across F07, F19, F20", "gate": "Wilson upper <= 0.15", "failure_handling": "fails G3 (UNEVALUABLE is violation)"},
        {"endpoint": "support recovery", "role": "SECONDARY", "denominator": 144, "definition": "support_status == MATCH under algebraic normalisation", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "parameter recovery (joint)", "role": "SECONDARY", "denominator": 156, "definition": "p_mass within +/-0.15 AND c_desc within +/-0.10 at x0 = (250, 0, 0, 0, 0)", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "mass exponent recovery", "role": "SECONDARY", "denominator": 156, "definition": "p_mass within +/-0.15 of planted exponent at x0", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "descriptor coupling recovery", "role": "SECONDARY", "denominator": 84, "definition": "c_desc within +/-0.10 of planted coefficient at x0", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "predictive equivalence", "role": "SECONDARY", "denominator": 144, "definition": "valid >= 0.995, c* > 0, REL_RMSE <= 0.05, Pearson r >= 0.990 over 12 ref frames (2,160 rows)", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "exact algebra recovery", "role": "SECONDARY", "denominator": 60, "definition": "Symbolic equivalence to planted law up to positive scale", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "M0 specificity", "role": "SECONDARY", "denominator": 164, "definition": "M0_NOT_REJECTED in M0-truth worlds", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "M1 sensitivity", "role": "SECONDARY", "denominator": 36, "definition": "M1 detector fires for M1 truth (F06, F13, F16)", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "M2 sensitivity", "role": "SECONDARY", "denominator": 24, "definition": "M2 detector fires for M2 truth (F14, F16)", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "M3 sensitivity", "role": "SECONDARY", "denominator": 24, "definition": "M3 detector fires for M3 truth (F15, F16)", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "trajectory prediction", "role": "DIAGNOSTIC", "denominator": 164, "definition": "MAE <= 0.80 of baseline on held-out test compounds", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "profile stability", "role": "DIAGNOSTIC", "denominator": 164, "definition": "Profile variation across bootstrap resamples", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "scalar target yield", "role": "DIAGNOSTIC", "denominator": 164, "definition": "Fraction of test compounds with successful scalar fit", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "boundary hit", "role": "DIAGNOSTIC", "denominator": 12, "definition": "Flags boundary condition hits in F05", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
        {"endpoint": "response structure diagnostic", "role": "DIAGNOSTIC", "denominator": 4, "definition": "Flags destroyed response cells in F19C", "gate": "Descriptive / ungated", "failure_handling": "non-success"},
    ]
    
    md = "# Table 2. Frozen Endpoints and Success Criteria\n\n"
    md += "**Status: Fully populated from frozen sources.**\n\n"
    md += "| Endpoint | Role | Denominator (Held-Out) | Mathematical Definition | Gate Threshold | Failure Handling |\n"
    md += "|---|---|---:|---|---|---|\n"
    for r in endpoints:
        md += f"| {r['endpoint']} | {r['role']} | {r['denominator']} | {r['definition']} | {r['gate']} | {r['failure_handling']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Frozen Benchmark Endpoints and Success Criteria.}
\label{tab:endpoints}
\begin{tabular}{llclll}
\toprule
Endpoint & Role & Denom & Definition & Gate & Failure Handling \\
\midrule
"""
    for r in endpoints:
        tex += f"{r['endpoint']} & {r['role']} & {r['denominator']} & {r['definition']} & {r['gate']} & {r['failure_handling']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_02_endpoints", md, tex, endpoints)

def build_table_03() -> None:
    """Table 3: Primary Gates Summary."""
    gates = [
        {"gate": "G1 Scalar Competence", "definition": "Spearman r_s >= 0.80 AND MAE <= 0.80 x baseline AND M0_NOT_REJECTED", "denominator": 164, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]", "criterion": "Wilson lower 95% >= 0.70", "verdict": "[PROSPECTIVE RESULT TO INSERT]"},
        {"gate": "G2 Family Recovery", "definition": "support_status == MATCH AND family_status == MATCH", "denominator": 144, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]", "criterion": "Wilson lower 95% >= 0.70", "verdict": "[PROSPECTIVE RESULT TO INSERT]"},
        {"gate": "G3 Structural Safety", "definition": "Unsafe structural acceptances in F07, F19, F20", "denominator": 36, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]", "criterion": "Wilson upper 95% <= 0.15", "verdict": "[PROSPECTIVE RESULT TO INSERT]"},
        {"gate": "Umbrella Claim", "definition": "Preconditions valid AND G1 PASS AND G2 PASS AND G3 PASS", "denominator": "Full", "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]", "criterion": "All three gates pass simultaneously", "verdict": "[PROSPECTIVE RESULT TO INSERT]"},
    ]
    
    md = "# Table 3. Primary Gates Summary (Held-Out Partition)\n\n"
    md += "**Status: Entirely pending execution. Held-out partition remains sealed.**\n\n"
    md += "| Gate | Definition | Denominator | Numerator | Rate | 95% Wilson CI | Gate Criterion | Verdict |\n"
    md += "|---|---|---:|---|---|---|---|---|\n"
    for r in gates:
        md += f"| {r['gate']} | {r['definition']} | {r['denominator']} | {r['numerator']} | {r['rate']} | {r['ci']} | {r['criterion']} | {r['verdict']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Primary Benchmark Gates on Held-Out Partition (Sealed).}
\label{tab:primary_gates}
\begin{tabular}{llcccccc}
\toprule
Gate & Definition & Denom & Num & Rate & 95\% Wilson & Criterion & Verdict \\
\midrule
"""
    for r in gates:
        tex += f"{r['gate']} & {r['definition']} & {r['denominator']} & {r['numerator']} & {r['rate']} & {r['ci']} & {r['criterion']} & {r['verdict']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_03_primary_gates", md, tex, gates)

def build_table_04() -> None:
    """Table 4: Secondary Endpoints."""
    sec = [
        {"endpoint": "Parameter Recovery (Joint)", "denominator": 156, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Mass Exponent Recovery (p_mass +/-0.15)", "denominator": 156, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Descriptor Coupling Recovery (c_desc +/-0.10)", "denominator": 84, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Predictive Equivalence (REL_RMSE <= 0.05, r >= 0.990)", "denominator": 144, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Exact Algebra Recovery (Symbolic Equivalence)", "denominator": 60, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Support Recovery (support_status == MATCH)", "denominator": 144, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "M0 Specificity (M0_NOT_REJECTED in M0 truth)", "denominator": 164, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "M1 Sensitivity (Horizontal violation detected)", "denominator": 36, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "M2 Sensitivity (High-energy floor detected)", "denominator": 24, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "M3 Sensitivity (Low-energy ceiling detected)", "denominator": 24, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Trajectory Prediction (MAE <= 0.80 baseline)", "denominator": 164, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Profile Stability (Bootstrap IQR)", "denominator": 164, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Scalar Target Yield (Fit convergence)", "denominator": 164, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Boundary Hit (F05 boundary detection)", "denominator": 12, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
        {"endpoint": "Response Structure Diagnostic (F19C cell resampling)", "denominator": 4, "numerator": "[PROSPECTIVE RESULT TO INSERT]", "rate": "[PROSPECTIVE RESULT TO INSERT]", "ci": "[PROSPECTIVE RESULT TO INSERT]"},
    ]
    
    md = "# Table 4. Secondary and Diagnostic Endpoints (Held-Out Partition)\n\n"
    md += "**Status: Entirely pending execution. Descriptive / Ungated.**\n\n"
    md += "| Endpoint | Denominator | Numerator | Rate | 95% Wilson CI |\n"
    md += "|---|---:|---|---|---|\n"
    for r in sec:
        md += f"| {r['endpoint']} | {r['denominator']} | {r['numerator']} | {r['rate']} | {r['ci']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Secondary and Diagnostic Endpoints on Held-Out Partition.}
\label{tab:secondary_endpoints}
\begin{tabular}{lcccc}
\toprule
Endpoint & Denom & Num & Rate & 95\% Wilson \\
\midrule
"""
    for r in sec:
        tex += f"{r['endpoint']} & {r['denominator']} & {r['numerator']} & {r['rate']} & {r['ci']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_04_secondary_endpoints", md, tex, sec)

def build_table_05() -> None:
    """Table 5: Null Calibration Design & Shell."""
    design = {
        "worlds": 100,
        "constructions": {
            "target_permuted_across_compounds": 34,
            "descriptors_permuted_across_compounds": 33,
            "gaussian_targets_with_observed_variance": 33
        },
        "excluded_construction": "within_compound_energy_permutation (unconstructible in RC3.1)",
        "compounds_per_world": 180,
        "scaffolds_per_world": 30,
        "calibration_split": "18 / 6 / 6 scaffolds = 108 / 36 / 36 compounds",
        "seeds_per_world": 30,
        "total_searches": 3000,
        "seed_base": 2110000000,
        "seed_spread": 370000,
        "base_target_seed_namespace": "PB|NCAL|<world_id>|BASE_TARGET",
        "split_seed_namespace": "PB|NCAL|<world_id>|SPLIT",
        "statistic": "max over 30 seeds of best validation R2 at complexity <= c; prefix-monotone",
        "quantile": "0.95 (linear method), cumulative maximum",
        "bootstrap": "2,000 world-level resamples at seed 20260812 (reporting only)",
        "validity_floor": "at least 95 of 100 worlds with zero execution-failure seeds",
        "execution_outcome": "[PROSPECTIVE RESULT TO INSERT]",
        "threshold_table": "[PROSPECTIVE RESULT TO INSERT]"
    }
    
    md = "# Table 5. Structural-Null Calibration Design & Execution Shell\n\n"
    md += "### Table 5a. Design Specifications (Frozen)\n\n"
    md += "| Parameter | Frozen Specification |\n"
    md += "|---|---|\n"
    md += f"| Total Worlds | {design['worlds']} |\n"
    md += f"| Construction Allocation | target_permuted: 34; descriptors_permuted: 33; gaussian_targets: 33 |\n"
    md += f"| Excluded Construction | {design['excluded_construction']} |\n"
    md += f"| Compounds / World | {design['compounds_per_world']} in {design['scaffolds_per_world']} scaffolds |\n"
    md += f"| Calibration Split | {design['calibration_split']} |\n"
    md += f"| Seeds / World | {design['seeds_per_world']} ({design['total_searches']} planned searches) |\n"
    md += f"| Base-Target Namespace | `{design['base_target_seed_namespace']}` |\n"
    md += f"| Split Namespace | `{design['split_seed_namespace']}` |\n"
    md += f"| Aggregation Statistic | {design['statistic']} |\n"
    md += f"| Threshold Quantile | {design['quantile']} |\n"
    md += f"| Bootstrap Resamples | {design['bootstrap']} |\n"
    md += f"| Validity Criterion | {design['validity_floor']} |\n\n"
    
    md += "### Table 5b. Threshold Table Shell (Pending Outcome)\n\n"
    md += "| Complexity c | Null Median | Threshold T(c) | 95% Bootstrap Band |\n"
    md += "|---:|---|---|---|\n"
    for c in range(1, 21):
        md += f"| {c} | [PROSPECTIVE RESULT TO INSERT] | [PROSPECTIVE RESULT TO INSERT] | [PROSPECTIVE RESULT TO INSERT] |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Structural-Null Calibration Protocol Specifications.}
\label{tab:calibration_design}
\begin{tabular}{ll}
\toprule
Parameter & Frozen Value \\
\midrule
Total Calibration Worlds & 100 (34 target\_permuted, 33 desc\_permuted, 33 gaussian) \\
Calibration Split & 18 / 6 / 6 scaffolds (108 / 36 / 36 compounds) \\
Search Multiplicity & 30 seeds per world (3,000 total searches) \\
Threshold Statistic & Empirical $Q_{95}$ of world-max validation $R^2$, cummax \\
Bootstrap Uncertainty & 2,000 resamples at seed 20260812 (reporting only) \\
Validity Floor & $\ge 95/100$ worlds with zero execution failures \\
\midrule
Observed Threshold Table & [PROSPECTIVE RESULT TO INSERT] \\
\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_05_calibration_design", md, tex, design)

def build_table_06() -> None:
    """Table 6: A3.4 Reference Frame Manifest."""
    frames = [
        {"frame_id": "PB|PRED_EQUIV|FRAME|000", "seed": "10159460000043340500", "compounds": 180, "scaffolds": 30, "sha256": "4bd545ba3fa8e2538096d9cc9245ba79021d9089cd739c8a4d048e41e8332e7e"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|001", "seed": "6369442522185596642", "compounds": 180, "scaffolds": 30, "sha256": "a45c217b297166f0689ce61b1602db33c41719813895de6441b314e326656ec7"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|002", "seed": "10285077022068351075", "compounds": 180, "scaffolds": 30, "sha256": "8f18bc0a6d4e7a299b8aada901877cc15bab7d5b953b5b2bbe66fa3ca055f747"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|003", "seed": "12287309645523585205", "compounds": 180, "scaffolds": 30, "sha256": "4b48e62e8d347e48a5d04791c50092a2dca861bd3395f921c7ed25e57ab7d92e"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|004", "seed": "10093203124591748778", "compounds": 180, "scaffolds": 30, "sha256": "de717d3baec939534ee20072cb9335e78c8c9fba32674b0b07bb389ea1e74bb3"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|005", "seed": "11744644982560049663", "compounds": 180, "scaffolds": 30, "sha256": "0919b84e1200316e3a2d396a20791f43f19a452bf14e4e858d8acf21d7655e7e"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|006", "seed": "16102535362459587545", "compounds": 180, "scaffolds": 30, "sha256": "ae5cd95f57b935e5faeeae0d8273c48ef028c8353282a6a64575420d68d6dda6"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|007", "seed": "11399441919836473429", "compounds": 180, "scaffolds": 30, "sha256": "282fd2d1279c4040f35c1ba779291df1879df7fd39a71813c15ee6e8b9920030"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|008", "seed": "6117612182649873844", "compounds": 180, "scaffolds": 30, "sha256": "c1f4cdf75dbb108e7407d6f5e6e9b80addc55050a90f206d2e25066b6035654b"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|009", "seed": "1323825430146244524", "compounds": 180, "scaffolds": 30, "sha256": "ea93b8a18af342f3f1995ef1cafa47992e2d3e1245fb98fe5c776c4d70e63689"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|010", "seed": "16921266869593996090", "compounds": 180, "scaffolds": 30, "sha256": "7b93c136145a8e0bc2d83116d8c65881aa8a83bc087c3745ad0bbd2dd05bbdb7"},
        {"frame_id": "PB|PRED_EQUIV|FRAME|011", "seed": "10286422724919074315", "compounds": 180, "scaffolds": 30, "sha256": "9224ac40d4a73d1a1437d0a0aed3b32c398039e16d54ca808e11da09b3bced26"},
    ]
    
    aggregate_hash = "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"
    
    md = "# Table 6. A3.4 Predictive-Equivalence Reference Frame Manifest\n\n"
    md += f"**Aggregate Canonical SHA-256 Digest:** `{aggregate_hash}`\n\n"
    md += "| Frame ID | Derived Seed | Compounds | Scaffolds | Frame Content SHA-256 |\n"
    md += "|---|---|---:|---:|---|\n"
    for r in frames:
        md += f"| `{r['frame_id']}` | `{r['seed']}` | {r['compounds']} | {r['scaffolds']} | `{r['sha256']}` |\n"
    md += f"| **Total** | | **2,160** | **360** | **Aggregate: `{aggregate_hash[:16]}...`** |\n\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Amendment A3.4 Predictive-Equivalence Reference Frame Manifest (2,160 Total Evaluation Rows).}
\label{tab:reference_frames}
\begin{tabular}{llccc}
\toprule
Frame ID & Seed (uint64) & Rows & Scaffolds & SHA-256 Digest (first 16 hex) \\
\midrule
"""
    for r in frames:
        tex += f"\\texttt{{{r['frame_id']}}} & \\texttt{{{r['seed']}}} & {r['compounds']} & {r['scaffolds']} & \\texttt{{{r['sha256'][:16]}...}} \\\\\n"
    tex += r"""\midrule
\textbf{Aggregate (2,160 Rows)} & & \textbf{2,160} & \textbf{360} & \textbf{\texttt{4fef2379ae33a10d...}} \\
\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_06_reference_frames", md, tex, {"aggregate_hash": aggregate_hash, "frames": frames})

def build_table_07() -> None:
    """Table 7: Governance Amendments."""
    amends = [
        {"amendment": "Content Freeze V1", "creation_commit": "d94d2c9", "binding_commit": "d94d2c9", "tag": "benchmark-content-freeze-v1", "date": "2026-08-13", "description": "Base prospective paper benchmark design, 380 cases manifest, 20 families"},
        {"amendment": "Amendment A1", "creation_commit": "2ac86c5", "binding_commit": "2ac86c5", "tag": "benchmark-content-freeze-a1", "date": "2026-08-13", "description": "Binds M0/M1/M2/M3 adequacy decision rules, thresholds, and failure semantics"},
        {"amendment": "Amendment A2", "creation_commit": "03cc4d3", "binding_commit": "03cc4d3", "tag": "benchmark-content-freeze-a2", "date": "2026-08-14", "description": "Repairs F16 generator to honour declared M1+M2+M3 truth; restores M3 amplitude"},
        {"amendment": "Amendment A2.1", "creation_commit": "80a7803", "binding_commit": "80a7803", "tag": "benchmark-content-freeze-a2-1", "date": "2026-08-14", "description": "Bumps GENERATOR_VERSION to 1.1.0 to enforce A2 generator repair"},
        {"amendment": "Amendment A3.1", "creation_commit": "c8938e8", "binding_commit": "c8938e8", "tag": "benchmark-content-freeze-a3-1", "date": "2026-08-14", "description": "Binds G2/G3 structural endpoints, taxonomy, and null calibration contract"},
        {"amendment": "Amendment A3.2", "creation_commit": "1194fcb", "binding_commit": "1194fcb", "tag": "benchmark-content-freeze-a3-2", "date": "2026-08-14", "description": "Corrects null calibration base target (global permutation) and 18/6/6 scaffold split"},
        {"amendment": "Amendment A3.3", "creation_commit": "e91aae6", "binding_commit": "71f5369", "tag": "benchmark-content-freeze-a3-3", "date": "2026-08-14", "description": "Proposes initial secondary endpoint contracts for Parameter Recovery and Predictive Equivalence"},
        {"amendment": "Amendment A3.4", "creation_commit": "d0ea5d4", "binding_commit": "be23b80", "tag": "benchmark-content-freeze-a3-4", "date": "2026-08-14", "description": "Repairs predictive-equivalence domain to 12 generator frames (2,160 rows); clarifies parameter invariance"},
        {"amendment": "A3.4 Provenance Erratum", "creation_commit": "220c9cb", "binding_commit": "220c9cb", "tag": "a3-4-temporal-provenance-erratum", "date": "2026-08-14", "description": "Adjudicates calibration chronology metadata; confirms outcome-blind design"},
    ]
    
    md = "# Table 7. Prospective Governance & Amendment Ledger\n\n"
    md += "**Status: Complete and verified across repository commit graph.**\n\n"
    md += "| Stage / Amendment | Creation Commit | Binding Commit | Annotated Tag | Date | Scope of Scientific Specification |\n"
    md += "|---|---|---|---|---|---|\n"
    for r in amends:
        md += f"| {r['amendment']} | `{r['creation_commit']}` | `{r['binding_commit']}` | `{r['tag']}` | {r['date']} | {r['description']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Prospective Governance and Amendment Ledger.}
\label{tab:governance_amendments}
\begin{tabular}{lllcl}
\toprule
Amendment & Binding Commit & Tag & Date & Scope \\
\midrule
"""
    for r in amends:
        tex += f"{r['amendment']} & \\texttt{{{r['binding_commit']}}} & \\texttt{{{r['tag']}}} & {r['date']} & {r['description']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_07_governance_amendments", md, tex, amends)

def build_table_08() -> None:
    """Table 8: Reproducibility Dependencies."""
    deps = [
        {"package": "python", "version": "3.13.12", "purpose": "Runtime interpreter (plan recorded 3.12 target; full stack verified on 3.13)"},
        {"package": "scikit-learn", "version": "1.9.0", "purpose": "HistGradientBoostingRegressor GBDT ceiling estimator"},
        {"package": "pysr", "version": "1.5.10", "purpose": "Symbolic regression search engine under Julia backend"},
        {"package": "sympy", "version": "1.14.0", "purpose": "Symbolic expression parsing, differentiation, and normalisation"},
        {"package": "numpy", "version": "1.26.4", "purpose": "Numerical array operations and linear-method quantile estimation"},
        {"package": "scipy", "version": "1.17.1", "purpose": "Statistical distributions, correlations, and optimization routines"},
        {"package": "pandas", "version": "2.2.2", "purpose": "Structured dataset, manifest, and partition frame handling"},
        {"package": "matplotlib", "version": "3.11.1", "purpose": "Vector figure generation (SVG / PDF) and 300-DPI PNG previews"},
    ]
    
    md = "# Table 8. Reproducibility & Software Dependency Stack\n\n"
    md += "| Package / Component | Exact Bound Version | Purpose in Benchmark Pipeline |\n"
    md += "|---|---|---|\n"
    for r in deps:
        md += f"| `{r['package']}` | `{r['version']}` | {r['purpose']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Reproducibility and Software Dependency Stack.}
\label{tab:reproducibility}
\begin{tabular}{lll}
\toprule
Package & Version & Purpose \\
\midrule
"""
    for r in deps:
        tex += f"\\texttt{{{r['package']}}} & \\texttt{{{r['version']}}} & {r['purpose']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_08_reproducibility_dependencies", md, tex, deps)

def build_table_09() -> None:
    """Table 9: Claim Boundaries."""
    claims = [
        {"claim": "C1: Molecule-specific horizontal scale", "evidence": "G1 success on 164 cases", "status": "PENDING (transductive historical only)", "allowed": "Scale estimable on scaffold-disjoint synthetic compounds", "forbidden": "That g is a real physical/chemical property or transfers across instruments"},
        {"claim": "C2: Reject scalar adequacy violations", "evidence": "M0 specificity (164) & M1/M2/M3 sensitivity (36/24/24)", "status": "PENDING (decision rule bound by A1)", "allowed": "Adequacy ladder rejected M0 in violation families at stated rates", "forbidden": "That collapse model is adequate for real spectra; that non-rejection proves M0"},
        {"claim": "C3: Recover relevant variable support", "evidence": "support_status == MATCH on 144 cases", "status": "PENDING (narrow Type 2 historical)", "allowed": "Effective support matched planted support in n of 144 cases", "forbidden": "That recovered variables are causal fragmentation drivers; that proxies are interchangeable"},
        {"claim": "C4: Recover mathematical family structure", "evidence": "G2 success (support & family MATCH) on 144 cases", "status": "PENDING (narrow Type 2 historical)", "allowed": "Recovered support and family in n of 144 cases, satisfying G2 gate", "forbidden": "That family is the equation; calling expression a 'law' or 'universal mechanism'"},
        {"claim": "C5: Recover exact generating algebra", "evidence": "Symbolic equivalence on 60 cases", "status": "PENDING (historically UNSUPPORTED: 0%)", "allowed": "Symbolic equivalence observed in n of 60 cases (ungated secondary)", "forbidden": "Presenting expression as true law; inferring algebra from family recovery"},
        {"claim": "C6: Avoid false discoveries under nulls", "evidence": "G3 unsafe rate <= 0.15 on 36 opportunities", "status": "PENDING (0/100 historical on pure nulls)", "allowed": "n unsafe acceptances on 36 frozen opportunities, satisfying gate", "forbidden": "Quoting zero error as p=0; claiming safety against untested confounders"},
        {"claim": "C7: Detect structure beyond mass", "evidence": "G2 positive rate & F07/F20 negative rates", "status": "PENDING (historically weak in positive)", "allowed": "Both positive and negative rates reported together", "forbidden": "Claiming non-mass structure exists in real data; quoting positive without negative"},
        {"claim": "C8: Generalize to held-out compounds", "evidence": "Trajectory MAE <= 0.80 & Pred Equiv on 144 cases", "status": "PENDING (first fold-local design)", "allowed": "On scaffold-disjoint test compounds, metrics satisfied at stated rates", "forbidden": "Generalization to real compounds or instruments; calling historical results fold-local"},
        {"claim": "C9: Identify a real collision energy law", "evidence": "Authorized Phase 4 on sealed Confirmation set", "status": "UNSUPPORTED (STOP BEFORE PHASE 4)", "allowed": "None. Claim unavailable from this benchmark", "forbidden": "Every form: 'universal law', 'physical equation of fragmentation'"},
        {"claim": "C10: Establish fragmentation mechanism", "evidence": "Interventional causal evidence (unproducible)", "status": "UNSUPPORTED (Design cannot produce it)", "allowed": "None. Claim unavailable from this benchmark", "forbidden": "Every causal verb: 'explains', 'is driven by', 'RRKM-consistent'"},
    ]
    
    md = "# Table 9. Scientific Claim Boundaries & Forbidden Overclaims\n\n"
    md += "| Claim | Required Evidence | Prospective Status | Allowed Wording if Supported | Binding Forbidden Overclaim |\n"
    md += "|---|---|---|---|---|\n"
    for r in claims:
        md += f"| {r['claim']} | {r['evidence']} | {r['status']} | {r['allowed']} | {r['forbidden']} |\n"
    md += "\n"
    
    tex = r"""\begin{table*}[t]
\centering
\small
\caption{Scientific Claim Boundaries and Forbidden Overclaims.}
\label{tab:claim_boundaries}
\begin{tabular}{llll}
\toprule
Claim & Status & Allowed Wording & Forbidden Overclaim \\
\midrule
"""
    for r in claims:
        tex += f"{r['claim']} & {r['status']} & {r['allowed']} & {r['forbidden']} \\\\\n"
    tex += r"""\bottomrule
\end{tabular}
\end{table*}
"""
    save_table("table_09_claim_boundaries", md, tex, claims)

def main() -> None:
    print("=" * 70)
    print("MURU CONJECTURELAB v1: PRE-RESULTS TABLE PRODUCTION")
    print("=" * 70)
    print(f"Output directory: {TABLES_DIR}")
    print("Binding rule: No result numerator populated.")
    print("-" * 70)
    
    build_table_01()
    build_table_02()
    build_table_03()
    build_table_04()
    build_table_05()
    build_table_06()
    build_table_07()
    build_table_08()
    build_table_09()
    
    print("=" * 70)
    print("ALL 9 TABLES SUCCESSFULLY GENERATED IN MD, TEX, AND JSON FORMATS")
    print("=" * 70)

if __name__ == "__main__":
    main()
