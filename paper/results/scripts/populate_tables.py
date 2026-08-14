"""Generates populated Markdown, LaTeX, and JSON tables from validated result artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .wilson import wilson_score_interval


def _save_table(
    table_dir: Path,
    name: str,
    md_content: str,
    tex_content: str,
    json_data: Any,
) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)
    (table_dir / f"{name}.md").write_text(md_content, encoding="utf-8")
    (table_dir / f"{name}.tex").write_text(tex_content, encoding="utf-8")
    (table_dir / f"{name}.json").write_text(
        json.dumps(json_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def populate_all_tables(payload: Mapping[str, Any], output_dir: Path) -> dict[str, Path]:
    """Generate all result tables (Tables 3b through 9) in MD, TeX, and JSON."""
    results_tables_dir = output_dir / "paper" / "tables" / "results"
    results_tables_dir.mkdir(parents=True, exist_ok=True)

    cal = payload.get("calibration", {})
    dev = payload.get("development", {})
    ho = payload.get("held_out", {})
    verdicts = payload.get("gate_verdicts", {})

    generated_paths: dict[str, Path] = {}

    # -------------------------------------------------------------
    # Table 3b: Calibration Execution Outcome
    # -------------------------------------------------------------
    t3b_data = {
        "worlds_executed": cal.get("n_worlds_executed", 0),
        "worlds_with_zero_failure_seeds": cal.get("n_worlds_valid", 0),
        "validity_verdict": cal.get("validity_verdict", "PENDING"),
        "seed_runs_completed": f"{cal.get('total_seeds_completed', 0)} / 3000",
        "completed_no_candidate_seeds": cal.get("completed_no_candidate_seeds", 0),
        "execution_failure_seeds": cal.get("execution_failure_seeds", 0),
        "wall_clock_runtime_seconds": cal.get("wall_clock_runtime_seconds", 0.0),
    }

    t3b_md = f"""# Table 3b. Calibration Execution Outcome

| Quantity | Value |
|---|---|
| Worlds executed | {t3b_data['worlds_executed']} |
| Worlds with zero execution-failure seeds | {t3b_data['worlds_with_zero_failure_seeds']} |
| Validity verdict against 95/100 | **{t3b_data['validity_verdict']}** |
| Seed-runs completed of 3,000 | {t3b_data['seed_runs_completed']} |
| `COMPLETED_NO_CANDIDATE` seeds | {t3b_data['completed_no_candidate_seeds']} |
| `EXECUTION_FAILURE` seeds | {t3b_data['execution_failure_seeds']} |
| Wall-clock runtime | {t3b_data['wall_clock_runtime_seconds']:.1f} s |
"""

    t3b_tex = f"""\\begin{{table}}[h]
\\centering
\\small
\\caption{{Null Calibration Execution Outcome.}}
\\label{{tab:cal_execution}}
\\begin{{tabular}}{{ll}}
\\toprule
Quantity & Value \\\\
\\midrule
Worlds executed & {t3b_data['worlds_executed']} \\\\
Worlds with zero failure seeds & {t3b_data['worlds_with_zero_failure_seeds']} / 100 \\\\
Validity verdict ($\\ge 95$) & \\textbf{{{t3b_data['validity_verdict']}}} \\\\
Seed-runs completed & {t3b_data['seed_runs_completed']} \\\\
Completed no candidate seeds & {t3b_data['completed_no_candidate_seeds']} \\\\
Execution failure seeds & {t3b_data['execution_failure_seeds']} \\\\
Wall-clock runtime & {t3b_data['wall_clock_runtime_seconds']:.1f} s \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    _save_table(results_tables_dir, "table_03b_calibration_execution", t3b_md, t3b_tex, t3b_data)

    # -------------------------------------------------------------
    # Table 3c: Complexity Threshold Table T(c)
    # -------------------------------------------------------------
    t3c_rows = cal.get("threshold_table", [])
    t3c_md = "# Table 3c. Structural-Null Complexity Threshold Table T(c)\n\n"
    t3c_md += "| Complexity c | Null median | Threshold T(c) | 95% Bootstrap Interval |\n"
    t3c_md += "|---:|---|---|---|\n"
    for r in t3c_rows:
        ci = r.get("bootstrap_interval_95", {})
        t3c_md += f"| {r['complexity']} | {r['null_median']:.4f} | **{r['threshold']:.4f}** | [{ci.get('lower', 0):.4f}, {ci.get('upper', 0):.4f}] |\n"

    t3c_tex = r"""\begin{table}[h]
\centering
\small
\caption{Monotonic Structural-Null Threshold Table $T(c)$.}
\label{tab:threshold_table}
\begin{tabular}{rccc}
\toprule
$c$ & Median & $T(c)$ & 95\% Bootstrap CI \\
\midrule
"""
    for r in t3c_rows:
        ci = r.get("bootstrap_interval_95", {})
        t3c_tex += f"{r['complexity']} & {r['null_median']:.4f} & {r['threshold']:.4f} & [{ci.get('lower', 0):.4f}, {ci.get('upper', 0):.4f}] \\\\\n"
    t3c_tex += "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    _save_table(results_tables_dir, "table_03c_threshold_table", t3c_md, t3c_tex, t3c_rows)

    # -------------------------------------------------------------
    # Table 3d: Per-Construction Diagnostics
    # -------------------------------------------------------------
    t3d_diag = cal.get("per_construction_diagnostics", {})
    t3d_md = "# Table 3d. Null Calibration Per-Construction Diagnostics\n\n"
    t3d_md += "| Construction | Worlds | p95 at c=4 | p95 at c=10 | p95 at c=20 | Mean Constant-Model R2 |\n"
    t3d_md += "|---|---:|---|---|---|---|\n"
    for c_name, c_data in t3d_diag.items():
        t3d_md += f"| `{c_name}` | {c_data.get('n_worlds', 0)} | {c_data.get('p95_c4', 0):.4f} | {c_data.get('p95_c10', 0):.4f} | {c_data.get('p95_c20', 0):.4f} | {c_data.get('mean_constant_model_r2', 0):.4f} |\n"

    t3d_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Null Calibration Per-Construction Diagnostics.}
\label{tab:cal_diagnostics}
\begin{tabular}{lccccc}
\toprule
Construction & Worlds & $p_{95}$ ($c=4$) & $p_{95}$ ($c=10$) & $p_{95}$ ($c=20$) & Mean $R^2_0$ \\
\midrule
"""
    for c_name, c_data in t3d_diag.items():
        t3d_tex += f"\\texttt{{{c_name}}} & {c_data.get('n_worlds', 0)} & {c_data.get('p95_c4', 0):.4f} & {c_data.get('p95_c10', 0):.4f} & {c_data.get('p95_c20', 0):.4f} & {c_data.get('mean_constant_model_r2', 0):.4f} \\\\\n"
    t3d_tex += "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
    _save_table(results_tables_dir, "table_03d_calibration_diagnostics", t3d_md, t3d_tex, t3d_diag)

    # -------------------------------------------------------------
    # Table 4: Development Results
    # -------------------------------------------------------------
    dev_num = dev.get("numerators", {})
    dev_den = dev.get("denominators", {})
    t4_rows = []
    for ep, den in dev_den.items():
        num = dev_num.get(ep, 0)
        ci = wilson_score_interval(num, den)
        t4_rows.append({
            "endpoint": ep,
            "denominator": den,
            "numerator": num,
            "rate": ci.point_estimate,
            "lower_95": ci.lower,
            "upper_95": ci.upper,
        })

    t4_md = "# Table 4. Development Results (80 Cases)\n\n"
    t4_md += "| Endpoint | Denominator | Numerator | Rate | 95% Wilson Interval |\n"
    t4_md += "|---|---:|---:|---:|---|\n"
    for r in t4_rows:
        t4_md += f"| {r['endpoint'].replace('_', ' ')} | {r['denominator']} | {r['numerator']} | {r['rate']:.4f} | [{r['lower_95']:.4f}, {r['upper_95']:.4f}] |\n"
    t4_md += f"\nEngine Failures: {dev.get('engine_failures', 0)}\n"
    t4_md += f"Runtime: {dev.get('runtime_seconds', 0.0):.1f} s\n"

    t4_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Development Partition Sanity Check (80 Cases).}
\label{tab:dev_results}
\begin{tabular}{lcccc}
\toprule
Endpoint & Denominator & Numerator & Rate & 95\% Wilson CI \\
\midrule
"""
    for r in t4_rows:
        t4_tex += f"{r['endpoint'].replace('_', ' ')} & {r['denominator']} & {r['numerator']} & {r['rate']:.4f} & [{r['lower_95']:.4f}, {r['upper_95']:.4f}] \\\\\n"
    t4_tex += "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
    _save_table(results_tables_dir, "table_04_development_results", t4_md, t4_tex, {"endpoints": t4_rows, "engine_failures": dev.get("engine_failures", 0), "runtime": dev.get("runtime_seconds", 0.0)})

    # -------------------------------------------------------------
    # Table 5: Held-Out Primary Gates & Umbrella Decision
    # -------------------------------------------------------------
    pg = ho.get("primary_gates", {})
    t5_rows = []
    for g_key in ["G1", "G2", "G3"]:
        g_info = pg.get(g_key, {})
        num = g_info.get("numerator", g_info.get("violations", 0))
        den = g_info.get("denominator", 1)
        ci = g_info.get("wilson_95", {})
        t5_rows.append({
            "gate": g_key,
            "endpoint": g_info.get("endpoint", ""),
            "denominator": den,
            "successes_or_violations": num,
            "rate": g_info.get("rate", 0.0),
            "lower_95": ci.get("lower", 0.0),
            "upper_95": ci.get("upper", 0.0),
            "gate_criterion": ">= 0.70 (lower)" if g_key != "G3" else "<= 0.15 (upper)",
            "passed": g_info.get("passed", False),
        })

    umb = ho.get("umbrella_decision", {})
    t5_md = "# Table 5. Held-Out Primary Gate Results & Umbrella Scientific Claim\n\n"
    t5_md += "| Gate | Endpoint | Denominator | Numerator | Rate | 95% Wilson | Criterion | Gate Verdict |\n"
    t5_md += "|---|---|---:|---:|---:|---|---|---|\n"
    for r in t5_rows:
        verdict_str = "**PASS**" if r['passed'] else "**FAIL**"
        t5_md += f"| **{r['gate']}** | {r['endpoint'].replace('_', ' ')} | {r['denominator']} | {r['successes_or_violations']} | {r['rate']:.4f} | [{r['lower_95']:.4f}, {r['upper_95']:.4f}] | {r['gate_criterion']} | {verdict_str} |\n"
    t5_md += f"\n**Umbrella Scientific Claim Verdict: {'POSITIVE' if umb.get('positive_claim') else 'NEGATIVE'}**\n"

    t5_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Held-Out Primary Gates and Umbrella Claim Verdict.}
\label{tab:primary_gates_results}
\begin{tabular}{llcccccc}
\toprule
Gate & Endpoint & $N$ & $k$ & Rate & 95\% Wilson CI & Criterion & Verdict \\
\midrule
"""
    for r in t5_rows:
        v_str = "\\textbf{PASS}" if r['passed'] else "\\textbf{FAIL}"
        t5_tex += f"{r['gate']} & {r['endpoint'].replace('_', ' ')} & {r['denominator']} & {r['successes_or_violations']} & {r['rate']:.4f} & [{r['lower_95']:.4f}, {r['upper_95']:.4f}] & {r['gate_criterion']} & {v_str} \\\\\n"
    t5_tex += f"\\midrule\n\\multicolumn{{8}}{{l}}{{\\textbf{{Umbrella Benchmark Claim:}} {'POSITIVE' if umb.get('positive_claim') else 'NEGATIVE'}}} \\\\\n"
    t5_tex += "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
    _save_table(results_tables_dir, "table_05_held_out_primary", t5_md, t5_tex, {"gates": t5_rows, "umbrella_decision": umb})

    # -------------------------------------------------------------
    # Table 5a: Secondary and Diagnostic Endpoints
    # -------------------------------------------------------------
    sec = ho.get("secondary_endpoints", {})
    diag = ho.get("diagnostics", {})
    adeq = ho.get("model_adequacy", {})

    t5a_rows = []
    # Secondary endpoints
    for key, spec in [
        ("joint_parameter_recovery", "Joint Parameter Recovery"),
        ("mass_exponent_recovery", "Mass Exponent Recovery (tolerance 0.15)"),
        ("descriptor_coupling_recovery", "Descriptor Coupling Recovery (tolerance 0.10)"),
        ("predictive_equivalence", "Predictive Equivalence (2,160 reference points)"),
        ("exact_algebra", "Exact Algebra Recovery (ungated secondary)"),
        ("support_recovery", "Support Recovery"),
    ]:
        item = sec.get(key, {})
        if item:
            ci = item.get("wilson_95", {})
            t5a_rows.append({
                "group": "Secondary",
                "endpoint": spec,
                "role": item.get("role", "SECONDARY"),
                "denominator": item.get("denominator", 0),
                "numerator": item.get("numerator", 0),
                "rate": item.get("rate", 0.0),
                "lower_95": ci.get("lower", 0.0),
                "upper_95": ci.get("upper", 0.0),
            })

    # Model adequacy
    for key, spec in [
        ("m0_specificity", "M0 Specificity (non-rejection on M0 truth)"),
        ("m1_sensitivity", "M1 Sensitivity (horizontal violation detection)"),
        ("m2_sensitivity", "M2 Sensitivity (high-energy floor detection)"),
        ("m3_sensitivity", "M3 Sensitivity (low-energy ceiling detection)"),
    ]:
        item = adeq.get(key, {})
        if item:
            ci = item.get("wilson_95", {})
            t5a_rows.append({
                "group": "Adequacy",
                "endpoint": spec,
                "role": "ADEQUACY",
                "denominator": item.get("denominator", 0),
                "numerator": item.get("numerator", 0),
                "rate": item.get("rate", 0.0),
                "lower_95": ci.get("lower", 0.0),
                "upper_95": ci.get("upper", 0.0),
            })

    # Diagnostics
    for key, spec in [
        ("boundary_hit", "Boundary Hit Diagnostic (F05)"),
        ("response_structure_diagnostic", "Response Structure Diagnostic (F19C)"),
        ("scalar_target_yield", "Scalar Target Yield"),
    ]:
        item = diag.get(key, {})
        if item:
            ci = item.get("wilson_95", {})
            t5a_rows.append({
                "group": "Diagnostic",
                "endpoint": spec,
                "role": "DIAGNOSTIC",
                "denominator": item.get("denominator", 0),
                "numerator": item.get("numerator", 0),
                "rate": item.get("rate", 0.0),
                "lower_95": ci.get("lower", 0.0),
                "upper_95": ci.get("upper", 0.0),
            })

    t5a_md = "# Table 5a. Held-Out Secondary, Adequacy, and Diagnostic Endpoints\n\n"
    t5a_md += "| Group | Endpoint | Role | Denominator | Numerator | Rate | 95% Wilson Interval |\n"
    t5a_md += "|---|---|---|---:|---:|---:|---|\n"
    for r in t5a_rows:
        t5a_md += f"| {r['group']} | {r['endpoint']} | `{r['role']}` | {r['denominator']} | {r['numerator']} | {r['rate']:.4f} | [{r['lower_95']:.4f}, {r['upper_95']:.4f}] |\n"

    t5a_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Secondary, Adequacy, and Diagnostic Endpoints on Held-Out Partition.}
\label{tab:secondary_diagnostic_results}
\begin{tabular}{lllcccc}
\toprule
Group & Endpoint & Role & $N$ & $k$ & Rate & 95\% Wilson CI \\
\midrule
"""
    for r in t5a_rows:
        t5a_tex += f"{r['group']} & {r['endpoint']} & \\texttt{{{r['role']}}} & {r['denominator']} & {r['numerator']} & {r['rate']:.4f} & [{r['lower_95']:.4f}, {r['upper_95']:.4f}] \\\\\n"
    t5a_tex += "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
    _save_table(results_tables_dir, "table_05a_secondary_and_diagnostic", t5a_md, t5a_tex, t5a_rows)

    # -------------------------------------------------------------
    # Table 6: Symbolic Discovery by Truth Family
    # -------------------------------------------------------------
    by_fam = ho.get("by_truth_family", {})
    t6_md = "# Table 6. Symbolic Discovery Outcomes by Truth Family\n\n"
    t6_md += "| Truth Family | Cases | Support MATCH | Family MATCH | **G2 (both)** | Parameter Recovery | Predictive Equiv | **Exact Algebra** |\n"
    t6_md += "|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for fam_name, fdata in by_fam.items():
        t6_md += f"| `{fam_name}` | {fdata.get('cases', 0)} | {fdata.get('support_match', 0)} | {fdata.get('family_match', 0)} | **{fdata.get('g2_both', 0)}** | {fdata.get('param_rec', 0)} | {fdata.get('pred_equiv', 0)} | **{fdata.get('exact_algebra', 0)}** |\n"

    t6_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Symbolic Discovery Outcomes by Truth Family.}
\label{tab:symbolic_by_family}
\begin{tabular}{lccccccc}
\toprule
Truth Family & $N$ & Supp & Fam & \textbf{G2} & Param & Pred & \textbf{Exact} \\
\midrule
"""
    for fam_name, fdata in by_fam.items():
        t6_tex += f"\\texttt{{{fam_name}}} & {fdata.get('cases', 0)} & {fdata.get('support_match', 0)} & {fdata.get('family_match', 0)} & {fdata.get('g2_both', 0)} & {fdata.get('param_rec', 0)} & {fdata.get('pred_equiv', 0)} & {fdata.get('exact_algebra', 0)} \\\\\n"
    t6_tex += "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
    _save_table(results_tables_dir, "table_06_symbolic_by_family", t6_md, t6_tex, by_fam)

    # -------------------------------------------------------------
    # Table 7: False Discovery and Refusals
    # -------------------------------------------------------------
    g3d = ho.get("g3_decomposition", {})
    f07 = g3d.get("f07_false_extra_structure", {})
    f19 = g3d.get("f19_false_null_structure", {})
    f20 = g3d.get("f20_false_adversarial", {})
    f06_k = ho.get("cases_refused_f06", 12)

    t7_md = f"""# Table 7. False Discovery and Refusal Cases (36 G3 Opportunities)

| Component | Variant | Cases | Unsafe Events | Rate | 95% Wilson Interval |
|---|---|---:|---:|---:|---|
| F07 false extra structure | base | 12 | {f07.get('unsafe_events', 0)} | {f07.get('rate', 0.0):.4f} | [{f07.get('wilson_95', {}).get('lower', 0):.4f}, {f07.get('wilson_95', {}).get('upper', 0):.4f}] |
| F19 false null structure | F19A | 4 | {f19.get('f19a_unsafe', 0)} | - | - |
| F19 false null structure | F19B | 4 | {f19.get('f19b_unsafe', 0)} | - | - |
| F19 false null structure | F19C | 4 | {f19.get('f19c_unsafe', 0)} | - | - |
| **F19 Subtotal** | | 12 | {f19.get('total_unsafe', 0)} | {f19.get('rate', 0.0):.4f} | [{f19.get('wilson_95', {}).get('lower', 0):.4f}, {f19.get('wilson_95', {}).get('upper', 0):.4f}] |
| F20 false adversarial structure | F20A | 4 | {f20.get('f20a_unsafe', 0)} | - | - |
| F20 false adversarial structure | F20B | 4 | {f20.get('f20b_unsafe', 0)} | - | - |
| F20 false adversarial structure | F20C | 4 | {f20.get('f20c_unsafe', 0)} | - | - |
| **F20 Subtotal** | | 12 | {f20.get('total_unsafe', 0)} | {f20.get('rate', 0.0):.4f} | [{f20.get('wilson_95', {}).get('lower', 0):.4f}, {f20.get('wilson_95', {}).get('upper', 0):.4f}] |
| **G3 Aggregate** | | **36** | **{pg.get('G3', {}).get('violations', 0)}** | **{pg.get('G3', {}).get('rate', 0.0):.4f}** | **[{pg.get('G3', {}).get('wilson_95', {}).get('lower', 0):.4f}, {pg.get('G3', {}).get('wilson_95', {}).get('upper', 0):.4f}]** (Gate: upper <= 0.15) |
| F06 legitimate refusal | base | 12 | (Refused: {f06_k}/12) | - | - |
"""

    t7_tex = f"""\\begin{{table*}}[t]
\\centering
\\small
\\caption{{False Discovery and Structural Safety Decomposition (36 Opportunities).}}
\\label{{tab:false_discovery_refusal}}
\\begin{{tabular}}{{llcccc}}
\\toprule
Component & Variant & Cases & Unsafe & Rate & 95\\% Wilson CI \\\\
\\midrule
F07 false extra structure & base & 12 & {f07.get('unsafe_events', 0)} & {f07.get('rate', 0.0):.4f} & [{f07.get('wilson_95', {}).get('lower', 0):.4f}, {f07.get('wilson_95', {}).get('upper', 0):.4f}] \\\\
F19 Subtotal & all & 12 & {f19.get('total_unsafe', 0)} & {f19.get('rate', 0.0):.4f} & [{f19.get('wilson_95', {}).get('lower', 0):.4f}, {f19.get('wilson_95', {}).get('upper', 0):.4f}] \\\\
F20 Subtotal & all & 12 & {f20.get('total_unsafe', 0)} & {f20.get('rate', 0.0):.4f} & [{f20.get('wilson_95', {}).get('lower', 0):.4f}, {f20.get('wilson_95', {}).get('upper', 0):.4f}] \\\\
\\midrule
\\textbf{{G3 Aggregate}} & & \\textbf{{36}} & \\textbf{{{pg.get('G3', {}).get('violations', 0)}}} & \\textbf{{{pg.get('G3', {}).get('rate', 0.0):.4f}}} & \\textbf{{[{pg.get('G3', {}).get('wilson_95', {}).get('lower', 0):.4f}, {pg.get('G3', {}).get('wilson_95', {}).get('upper', 0):.4f}]}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table*}}
"""
    _save_table(results_tables_dir, "table_07_false_discovery_and_refusals", t7_md, t7_tex, g3d)

    # -------------------------------------------------------------
    # Table 8: Challenge and Stress Tests (Staged / Disabled)
    # -------------------------------------------------------------
    t8_md = """# Table 8. Challenge and Stress Test Outcomes (60 Cases)

**Status: STAGED / DISABLED. Descriptive stress test only; enters no primary denominator.**

| Aggregate Stress Measure | Denominator | Numerator | Rate | 95% Wilson Interval |
|---|---:|---:|---:|---|
| Challenge scalar competence | 41 | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` |
| Challenge family recovery | 36 | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` |
| Challenge structural safety | 9 | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` |
| Challenge exact algebra | 15 | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` | `[STAGED_DISABLED]` |
"""

    t8_tex = r"""\begin{table}[h]
\centering
\small
\caption{Challenge Partition Stress Outcomes (Descriptive Only).}
\label{tab:challenge_stress}
\begin{tabular}{lcccc}
\toprule
Measure & $N$ & $k$ & Rate & 95\% Wilson CI \\
\midrule
Scalar competence & 41 & -- & -- & -- \\
Family recovery & 36 & -- & -- & -- \\
Structural safety & 9 & -- & -- & -- \\
Exact algebra & 15 & -- & -- & -- \\
\bottomrule
\end{tabular}
\end{table}
"""
    _save_table(results_tables_dir, "table_08_challenge_outcomes", t8_md, t8_tex, {"status": "STAGED_DISABLED", "total_cases": 60})

    # -------------------------------------------------------------
    # Table 9: Historical vs Prospective Evidence
    # -------------------------------------------------------------
    g1_r = pg.get("G1", {})
    g2_r = pg.get("G2", {})
    g3_r = pg.get("G3", {})
    sec_p = sec.get("joint_parameter_recovery", {})
    sec_ea = sec.get("exact_algebra", {})
    sec_sup = sec.get("support_recovery", {})

    t9_md = f"""# Table 9. Historical Evidence (CLASS A) versus Prospective Evidence (CLASS C)

| Question | Historical Evidence (CLASS A) | Prospective Evidence (CLASS C) |
|---|---|---|
| Does the pipeline recover variable support? | Type 2 G1B moderate: 20/20 block supports recovered | Support recovery on 144 Held-out cases: **{sec_sup.get('numerator', 0)}/144** (Wilson 95% [{sec_sup.get('wilson_95', {}).get('lower', 0):.4f}, {sec_sup.get('wilson_95', {}).get('upper', 0):.4f}]) |
| Does it recover mathematical family? | Type 2 G1B moderate: dense-lattice family recovery 16/20 **measured, not gated**; composite gate 17/20 | G2 on 144 Held-out cases: **{g2_r.get('numerator', 0)}/144** (Wilson 95% [{g2_r.get('wilson_95', {}).get('lower', 0):.4f}, {g2_r.get('wilson_95', {}).get('upper', 0):.4f}]) |
| Does it recover exact algebra? | Phase 3 selected functional and symbolic recovery 0% at every G1B noise regime; Type 2 symbolic equivalence 0 | Exact algebra on 60 Held-out cases: **{sec_ea.get('numerator', 0)}/60** (Wilson 95% [{sec_ea.get('wilson_95', {}).get('lower', 0):.4f}, {sec_ea.get('wilson_95', {}).get('upper', 0):.4f}]) |
| Does it recover scaling exponents? | Type 2 G1B moderate: mass exponent median 0.500, range [0.448, 0.540], 20/20 within +/-0.15 | Parameter recovery on 156 Held-out cases: **{sec_p.get('numerator', 0)}/156** (Wilson 95% [{sec_p.get('wilson_95', {}).get('lower', 0):.4f}, {sec_p.get('wilson_95', {}).get('upper', 0):.4f}]) |
| Does it manufacture structure in pure nulls? | Phase 3 and Type 2 each: 0/100 accepted, Clopper-Pearson 95% [0.0000, 0.0362] | G3 on 36 Held-out opportunities: **{g3_r.get('violations', 0)}/36** (Wilson 95% [{g3_r.get('wilson_95', {}).get('lower', 0):.4f}, {g3_r.get('wilson_95', {}).get('upper', 0):.4f}]) |
| Does it refuse mass-only worlds? | Type 2 G3 block: 0/8 non-mass claims. Phase 3: 0/8 | F07 on 12 Held-out cases: **{f07.get('unsafe_events', 0)}/12** unsafe |
| Does it refuse latent-confounded worlds? | Type 2 G5: 0/8. Phase 3 G5: 1/8 | F20A on 4 Held-out cases: **{f20.get('f20a_unsafe', 0)}/4** unsafe |
| Does it refuse measurement-coupling worlds? | Type 2 GC: 0/9. Phase 3 GC: 0/9 | F20B on 4 Held-out cases: **{f20.get('f20b_unsafe', 0)}/4** unsafe |
| Does it refuse non-compressible worlds? | Type 2 G2: 0/8 accepted; H-MAIN rejected 8/8 | F06 on 12 Held-out cases: **{f06_k}/12** refused |
| Real-data claims ladder | L3, unchanged by synthetic study | Unchanged. No real-data claim available from this work |
| Phase 4 authorization | Phase 3: STOP BEFORE PHASE 4. Type 2: DO NOT AUTHORIZE PHASE 4 | Unchanged. This benchmark does not authorize Phase 4 |
"""

    t9_tex = r"""\begin{table*}[t]
\centering
\small
\caption{Historical Evidence (CLASS A) versus Prospective Evidence (CLASS C).}
\label{tab:historical_vs_prospective}
\begin{tabular}{lll}
\toprule
Question & Historical (CLASS A) & Prospective (CLASS C) \\
\midrule
Support recovery & Type 2: 20/20 & Held-out (144): """ + f"{sec_sup.get('numerator', 0)}/144" + r""" \\
Family recovery (G2) & Type 2: 16/20 (measured) & Held-out (144): """ + f"{g2_r.get('numerator', 0)}/144" + r""" \\
Exact algebra & Phase 3 / Type 2: 0\% & Held-out (60): """ + f"{sec_ea.get('numerator', 0)}/60" + r""" \\
Scaling exponents & Type 2: 18/20 within $\pm 0.15$ & Held-out (156): """ + f"{sec_p.get('numerator', 0)}/156" + r""" \\
Pure null structure & 0/100 ($p_{95} \le 0.0362$) & G3 (36): """ + f"{g3_r.get('violations', 0)}/36" + r""" \\
Real-data claims & Ladder L3 & Unchanged \\
Phase 4 authorization & DO NOT AUTHORIZE & Unchanged \\
\bottomrule
\end{tabular}
\end{table*}
"""
    _save_table(results_tables_dir, "table_09_historical_vs_prospective", t9_md, t9_tex, {"status": "POPULATED"})

    return generated_paths
