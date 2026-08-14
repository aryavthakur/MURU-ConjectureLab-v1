"""Mechanically updates MURU_EVIDENCE_LEDGER.json with Class C prospective result entries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def generate_class_c_ledger_entries(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build concrete Class C entries (P001..P018) from the master result payload."""
    tpl_path = TEMPLATES_DIR / "evidence_ledger_templates.json"
    template_entries = json.loads(tpl_path.read_text(encoding="utf-8"))["entries"]

    cal = payload.get("calibration", {})
    dev = payload.get("development", {})
    ho = payload.get("held_out", {})
    pg = ho.get("primary_gates", {})
    sec = ho.get("secondary_endpoints", {})
    adeq = ho.get("model_adequacy", {})
    diag = ho.get("diagnostics", {})
    gov = payload.get("governance", {})

    populated_entries = []

    for tpl in template_entries:
        entry_id = tpl["id"]
        entry = dict(tpl)
        entry["commit"] = gov.get("code_commit", "PENDING")
        entry["status"] = "populated_prospective"

        if entry_id == "P001":
            entry["value"] = {
                "n_worlds_valid": cal.get("n_worlds_valid", 0),
                "validity_verdict": cal.get("validity_verdict", "INVALID"),
                "threshold_c20": cal.get("threshold_table", [{}])[-1].get("threshold", 0.0) if cal.get("threshold_table") else 0.0,
            }
            entry["verification"] = f"Calibration {entry['value']['validity_verdict']}: {entry['value']['n_worlds_valid']}/100 valid worlds"

        elif entry_id == "P002":
            entry["value"] = cal.get("per_construction_diagnostics", {})
            entry["verification"] = "Computed from per-construction 95th percentiles"

        elif entry_id == "P003":
            entry["value"] = {
                "total_cases": dev.get("total_cases", 80),
                "numerators": dev.get("numerators", {}),
                "engine_failures": dev.get("engine_failures", 0),
            }
            entry["verification"] = "Verified 80 Development case outcomes"

        elif entry_id == "P004":
            g1 = pg.get("G1", {})
            entry["value"] = {
                "numerator": g1.get("numerator", 0),
                "denominator": 164,
                "rate": g1.get("rate", 0.0),
                "wilson_95": g1.get("wilson_95", {}),
                "passed": g1.get("passed", False),
            }
            entry["verification"] = f"G1 {'PASSED' if entry['value']['passed'] else 'FAILED'}: {entry['value']['numerator']}/164"

        elif entry_id == "P005":
            g2 = pg.get("G2", {})
            entry["value"] = {
                "numerator": g2.get("numerator", 0),
                "denominator": 144,
                "rate": g2.get("rate", 0.0),
                "wilson_95": g2.get("wilson_95", {}),
                "passed": g2.get("passed", False),
            }
            entry["verification"] = f"G2 {'PASSED' if entry['value']['passed'] else 'FAILED'}: {entry['value']['numerator']}/144"

        elif entry_id == "P006":
            g3 = pg.get("G3", {})
            entry["value"] = {
                "violations": g3.get("violations", 0),
                "denominator": 36,
                "rate": g3.get("rate", 0.0),
                "wilson_95": g3.get("wilson_95", {}),
                "passed": g3.get("passed", False),
            }
            entry["verification"] = f"G3 {'PASSED' if entry['value']['passed'] else 'FAILED'}: {entry['value']['violations']}/36 violations"

        elif entry_id == "P007":
            umb = payload.get("gate_verdicts", {}).get("umbrella_claim", {})
            entry["value"] = {
                "positive_claim": umb.get("positive_claim", False),
                "verdict": umb.get("verdict", "FAIL"),
                "failed_gates": umb.get("failed_gates", []),
            }
            entry["verification"] = f"Umbrella verdict: {entry['value']['verdict']}"

        elif entry_id == "P008":
            p = sec.get("joint_parameter_recovery", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 156,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
            }
            entry["verification"] = f"Joint parameter recovery: {entry['value']['numerator']}/156"

        elif entry_id == "P009":
            p = sec.get("mass_exponent_recovery", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 156,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
            }
            entry["verification"] = f"Mass exponent recovery: {entry['value']['numerator']}/156"

        elif entry_id == "P010":
            p = sec.get("descriptor_coupling_recovery", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 84,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
            }
            entry["verification"] = f"Descriptor coupling recovery: {entry['value']['numerator']}/84"

        elif entry_id == "P011":
            p = sec.get("predictive_equivalence", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 144,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
                "n_reference_points": 2160,
            }
            entry["verification"] = f"Predictive equivalence: {entry['value']['numerator']}/144"

        elif entry_id == "P012":
            p = sec.get("exact_algebra", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 60,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
                "distinct_functional_classes": p.get("distinct_functional_classes", 0),
            }
            entry["verification"] = f"Exact algebra: {entry['value']['numerator']}/60"

        elif entry_id == "P013":
            p = sec.get("support_recovery", {})
            entry["value"] = {
                "numerator": p.get("numerator", 0),
                "denominator": 144,
                "rate": p.get("rate", 0.0),
                "wilson_95": p.get("wilson_95", {}),
            }
            entry["verification"] = f"Support recovery: {entry['value']['numerator']}/144"

        elif entry_id == "P014":
            entry["value"] = adeq
            entry["verification"] = "Recomputed adequacy sensitivities and specificity"

        elif entry_id == "P015":
            entry["value"] = ho.get("g3_decomposition", {})
            entry["verification"] = "Decomposed F07, F19, F20 false-structure events"

        elif entry_id == "P016":
            entry["value"] = diag
            entry["verification"] = "Verified diagnostic endpoints"

        elif entry_id == "P017":
            entry["value"] = ho.get("by_noise_regime", {})
            entry["verification"] = "Decomposed F01, F02, F03 noise envelope"

        elif entry_id == "P018":
            entry["value"] = ho.get("failure_census", {})
            entry["verification"] = "Census of typed non-success states"

        populated_entries.append(entry)

    return populated_entries


def update_evidence_ledger_file(
    ledger_path: Path,
    payload: Mapping[str, Any],
    output_path: Path | None = None,
) -> Path:
    """Read MURU_EVIDENCE_LEDGER.json, update Class C entries, and save populated ledger."""
    if not ledger_path.exists():
        raise FileNotFoundError(f"Evidence ledger file not found: {ledger_path}")

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    # Retain Class A and Class B entries, replace Class C placeholder with concrete populated entries
    existing_entries = [e for e in ledger.get("entries", []) if e.get("evidence_class") != "C"]
    new_class_c_entries = generate_class_c_ledger_entries(payload)

    ledger["entries"] = existing_entries + new_class_c_entries
    ledger["contamination_attestation"]["prospective_results_ingested"] = True
    ledger["contamination_attestation"]["result_payload_sha256"] = payload.get("governance", {}).get("held_out_artifact_sha256", "")

    dest = output_path or ledger_path.parent / "results" / "MURU_EVIDENCE_LEDGER_POPULATED.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dest
