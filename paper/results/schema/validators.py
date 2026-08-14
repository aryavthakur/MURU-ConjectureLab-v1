"""Strict validator implementations for MURU prospective result artifacts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_DIR = Path(__file__).resolve().parent

# Frozen Denominator Constants
G1_HELD_OUT_DENOMINATOR = 164
G2_HELD_OUT_DENOMINATOR = 144
G3_HELD_OUT_DENOMINATOR = 36

PARAM_RECOVERY_JOINT_DENOMINATOR = 156
PARAM_RECOVERY_MASS_DENOMINATOR = 156
PARAM_RECOVERY_DESC_DENOMINATOR = 84

PRED_EQUIV_HELD_OUT_DENOMINATOR = 144
PRED_EQUIV_TOTAL_POINTS = 2160
PRED_EQUIV_N_FRAMES = 12

EXACT_ALGEBRA_HELD_OUT_DENOMINATOR = 60
SUPPORT_RECOVERY_HELD_OUT_DENOMINATOR = 144

M0_SPECIFICITY_HELD_OUT_DENOMINATOR = 164
M1_SENSITIVITY_HELD_OUT_DENOMINATOR = 36
M2_SENSITIVITY_HELD_OUT_DENOMINATOR = 24
M3_SENSITIVITY_HELD_OUT_DENOMINATOR = 24

BOUNDARY_HIT_HELD_OUT_DENOMINATOR = 12
RESPONSE_DIAGNOSTIC_HELD_OUT_DENOMINATOR = 4

CALIBRATION_WORLDS = 100
CALIBRATION_VALIDITY_FLOOR = 95
CALIBRATION_TOTAL_SEEDS = 3000

DEVELOPMENT_TOTAL_CASES = 80
HELD_OUT_TOTAL_CASES = 240
CHALLENGE_TOTAL_CASES = 60


class SchemaValidationError(Exception):
    """Raised when an incoming result artifact violates its frozen schema or denominators."""
    pass


def _load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_calibration_result(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a calibration outcome artifact against the frozen calibration schema."""
    if data.get("schema_version") != "muru-calibration-result-schema-1.0.0":
        raise SchemaValidationError("Invalid schema_version for calibration result")

    if data.get("n_worlds_executed") != CALIBRATION_WORLDS:
        raise SchemaValidationError(f"Expected {CALIBRATION_WORLDS} executed worlds, got {data.get('n_worlds_executed')}")

    n_valid = data.get("n_worlds_valid")
    if not isinstance(n_valid, int) or not (0 <= n_valid <= CALIBRATION_WORLDS):
        raise SchemaValidationError(f"Invalid n_worlds_valid: {n_valid}")

    verdict = data.get("validity_verdict")
    expected_verdict = "VALID" if n_valid >= CALIBRATION_VALIDITY_FLOOR else "INVALID"
    if verdict != expected_verdict:
        raise SchemaValidationError(f"Validity verdict '{verdict}' does not match n_valid={n_valid} vs floor {CALIBRATION_VALIDITY_FLOOR}")

    if data.get("total_seeds_attempted") != CALIBRATION_TOTAL_SEEDS:
        raise SchemaValidationError(f"Expected {CALIBRATION_TOTAL_SEEDS} attempted seeds")

    table = data.get("threshold_table")
    if not isinstance(table, list) or len(table) != 20:
        raise SchemaValidationError("Threshold table must contain exactly 20 complexity entries (c=1..20)")

    last_threshold = -1e9
    for i, row in enumerate(table, start=1):
        if row.get("complexity") != i:
            raise SchemaValidationError(f"Threshold table row {i} has unexpected complexity {row.get('complexity')}")
        thresh = row.get("threshold")
        if not isinstance(thresh, (int, float)):
            raise SchemaValidationError(f"Non-numeric threshold at complexity {i}")
        if thresh < last_threshold - 1e-9:
            raise SchemaValidationError(f"Threshold table must be prefix-monotone: T({i})={thresh} < T({i-1})={last_threshold}")
        last_threshold = thresh

        ci = row.get("bootstrap_interval_95")
        if not isinstance(ci, dict) or "lower" not in ci or "upper" not in ci:
            raise SchemaValidationError(f"Invalid bootstrap interval at complexity {i}")
        if ci["lower"] > ci["upper"]:
            raise SchemaValidationError(f"Inverted bootstrap interval at complexity {i}: {ci}")

    diag = data.get("per_construction_diagnostics")
    if not isinstance(diag, dict):
        raise SchemaValidationError("Missing per_construction_diagnostics")

    req_constructions = {
        "target_permuted_across_compounds": 34,
        "descriptors_permuted_across_compounds": 33,
        "gaussian_targets_with_observed_variance": 33,
    }
    for c_name, c_count in req_constructions.items():
        if c_name not in diag:
            raise SchemaValidationError(f"Missing diagnostic construction: {c_name}")
        if diag[c_name].get("n_worlds") != c_count:
            raise SchemaValidationError(f"Construction {c_name} must have {c_count} worlds, got {diag[c_name].get('n_worlds')}")

    return dict(data)


def validate_case_outcome(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an individual case outcome record."""
    required_keys = [
        "case_id", "partition", "family", "variant",
        "g_spearman", "trajectory_mae", "per_energy_mean_mae",
        "adequacy_status", "m0_accepted", "structural_acceptance_status",
        "accepted", "support_status", "family_status",
        "g1_scalar_competent", "g2_family_recovered"
    ]
    for k in required_keys:
        if k not in data:
            raise SchemaValidationError(f"Case outcome missing required key: {k}")

    case_id = data["case_id"]
    parts = str(case_id).split("|")
    if len(parts) != 4 or parts[0] != "PB":
        raise SchemaValidationError(f"Invalid case_id format: {case_id}")

    return dict(data)


def validate_development_aggregate(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a Development aggregate artifact."""
    if data.get("schema_version") != "muru-development-aggregate-schema-1.0.0":
        raise SchemaValidationError("Invalid schema_version for development aggregate")

    if data.get("partition") != "development":
        raise SchemaValidationError("Development aggregate partition must be 'development'")

    if data.get("total_cases") != DEVELOPMENT_TOTAL_CASES:
        raise SchemaValidationError(f"Expected {DEVELOPMENT_TOTAL_CASES} development cases, got {data.get('total_cases')}")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != DEVELOPMENT_TOTAL_CASES:
        raise SchemaValidationError(f"Development artifact must contain {DEVELOPMENT_TOTAL_CASES} case records")

    for c in cases:
        validate_case_outcome(c)

    return dict(data)


def validate_held_out_aggregate(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the 240-case Held-Out aggregate artifact against all frozen contracts."""
    if data.get("schema_version") != "muru-held-out-aggregate-schema-1.0.0":
        raise SchemaValidationError("Invalid schema_version for held-out aggregate")

    if data.get("partition") != "held_out":
        raise SchemaValidationError("Held-out aggregate partition must be 'held_out'")

    if data.get("total_cases") != HELD_OUT_TOTAL_CASES:
        raise SchemaValidationError(f"Expected {HELD_OUT_TOTAL_CASES} held-out cases, got {data.get('total_cases')}")

    # Validate Primary Gates
    pg = data.get("primary_gates")
    if not isinstance(pg, dict):
        raise SchemaValidationError("Missing primary_gates in held-out aggregate")

    # G1
    g1 = pg.get("G1")
    if not g1 or g1.get("denominator") != G1_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"G1 denominator must be {G1_HELD_OUT_DENOMINATOR}, got {g1.get('denominator') if g1 else None}")
    if g1.get("gate_threshold") != 0.70:
        raise SchemaValidationError("G1 gate threshold must be 0.70")
    if not (0 <= g1.get("numerator", -1) <= G1_HELD_OUT_DENOMINATOR):
        raise SchemaValidationError(f"G1 numerator out of bounds: {g1.get('numerator')}")

    # G2
    g2 = pg.get("G2")
    if not g2 or g2.get("denominator") != G2_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"G2 denominator must be {G2_HELD_OUT_DENOMINATOR}, got {g2.get('denominator') if g2 else None}")
    if g2.get("gate_threshold") != 0.70:
        raise SchemaValidationError("G2 gate threshold must be 0.70")
    if not (0 <= g2.get("numerator", -1) <= G2_HELD_OUT_DENOMINATOR):
        raise SchemaValidationError(f"G2 numerator out of bounds: {g2.get('numerator')}")

    # G3
    g3 = pg.get("G3")
    if not g3 or g3.get("denominator") != G3_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"G3 denominator must be {G3_HELD_OUT_DENOMINATOR}, got {g3.get('denominator') if g3 else None}")
    if g3.get("gate_threshold") != 0.15:
        raise SchemaValidationError("G3 gate threshold must be 0.15")
    if not (0 <= g3.get("violations", -1) <= G3_HELD_OUT_DENOMINATOR):
        raise SchemaValidationError(f"G3 violations out of bounds: {g3.get('violations')}")

    # Validate Secondary Endpoints (Ungated)
    sec = data.get("secondary_endpoints")
    if not isinstance(sec, dict):
        raise SchemaValidationError("Missing secondary_endpoints in held-out aggregate")

    if sec.get("joint_parameter_recovery", {}).get("denominator") != PARAM_RECOVERY_JOINT_DENOMINATOR:
        raise SchemaValidationError(f"Joint parameter recovery denominator must be {PARAM_RECOVERY_JOINT_DENOMINATOR}")
    if sec.get("joint_parameter_recovery", {}).get("role") != "SECONDARY":
        raise SchemaValidationError("Joint parameter recovery must be labeled SECONDARY")

    if sec.get("mass_exponent_recovery", {}).get("denominator") != PARAM_RECOVERY_MASS_DENOMINATOR:
        raise SchemaValidationError(f"Mass exponent recovery denominator must be {PARAM_RECOVERY_MASS_DENOMINATOR}")

    if sec.get("descriptor_coupling_recovery", {}).get("denominator") != PARAM_RECOVERY_DESC_DENOMINATOR:
        raise SchemaValidationError(f"Descriptor coupling recovery denominator must be {PARAM_RECOVERY_DESC_DENOMINATOR}")

    pred_eq = sec.get("predictive_equivalence", {})
    if pred_eq.get("denominator") != PRED_EQUIV_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"Predictive equivalence denominator must be {PRED_EQUIV_HELD_OUT_DENOMINATOR}")
    if pred_eq.get("n_reference_points") != PRED_EQUIV_TOTAL_POINTS:
        raise SchemaValidationError(f"Predictive equivalence reference points must be {PRED_EQUIV_TOTAL_POINTS}")
    if pred_eq.get("n_frames") != PRED_EQUIV_N_FRAMES:
        raise SchemaValidationError(f"Predictive equivalence frame count must be {PRED_EQUIV_N_FRAMES}")

    if sec.get("exact_algebra", {}).get("denominator") != EXACT_ALGEBRA_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"Exact algebra denominator must be {EXACT_ALGEBRA_HELD_OUT_DENOMINATOR}")
    if sec.get("exact_algebra", {}).get("role") != "SECONDARY":
        raise SchemaValidationError("Exact algebra must be labeled SECONDARY")

    # Validate Model Adequacy
    adeq = data.get("model_adequacy")
    if not isinstance(adeq, dict):
        raise SchemaValidationError("Missing model_adequacy in held-out aggregate")
    if adeq.get("m0_specificity", {}).get("denominator") != M0_SPECIFICITY_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"M0 specificity denominator must be {M0_SPECIFICITY_HELD_OUT_DENOMINATOR}")
    if adeq.get("m1_sensitivity", {}).get("denominator") != M1_SENSITIVITY_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"M1 sensitivity denominator must be {M1_SENSITIVITY_HELD_OUT_DENOMINATOR}")
    if adeq.get("m2_sensitivity", {}).get("denominator") != M2_SENSITIVITY_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"M2 sensitivity denominator must be {M2_SENSITIVITY_HELD_OUT_DENOMINATOR}")
    if adeq.get("m3_sensitivity", {}).get("denominator") != M3_SENSITIVITY_HELD_OUT_DENOMINATOR:
        raise SchemaValidationError(f"M3 sensitivity denominator must be {M3_SENSITIVITY_HELD_OUT_DENOMINATOR}")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != HELD_OUT_TOTAL_CASES:
        raise SchemaValidationError(f"Held-out aggregate must contain {HELD_OUT_TOTAL_CASES} case records")

    for c in cases:
        validate_case_outcome(c)

    return dict(data)


def validate_paper_result_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete master paper result payload."""
    if data.get("schema_version") != "muru-paper-results-1.0.0":
        raise SchemaValidationError("Invalid schema_version for master paper result payload")

    for section in ["governance", "calibration", "development", "held_out", "gate_verdicts", "claim_evaluations", "evidence_ledger_updates"]:
        if section not in data:
            raise SchemaValidationError(f"Master payload missing required section: {section}")

    validate_calibration_result(data["calibration"])
    validate_development_aggregate(data["development"])
    validate_held_out_aggregate(data["held_out"])

    return dict(data)
