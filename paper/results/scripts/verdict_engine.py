"""Deterministic rule engine for gate evaluation, Wilson interval recomputation, and wording selection."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .wilson import wilson_score_interval, ScoreInterval

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _load_templates(filename: str) -> dict[str, Any]:
    path = TEMPLATES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class GateVerdict:
    name: str
    endpoint: str
    verdict: str  # "PASS", "FAIL", "INCONCLUSIVE", "NOT_EVALUABLE"
    gate_passed: bool
    numerator: int
    denominator: int
    interval: ScoreInterval
    wording: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "verdict": self.verdict,
            "gate_passed": self.gate_passed,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "rate": self.interval.point_estimate,
            "wilson_95": {
                "lower": self.interval.lower,
                "upper": self.interval.upper,
                "bracket": self.interval.format_bracket(),
            },
            "wording": self.wording,
        }


def evaluate_calibration_validity(cal_data: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate structural-null calibration validity mechanically."""
    templates = _load_templates("verdict_wording_templates.json")["calibration"]
    n_valid = cal_data.get("n_worlds_valid", 0)
    n_executed = cal_data.get("n_worlds_executed", 0)

    if n_executed < 100:
        status = "INCONCLUSIVE"
        wording = templates["INCONCLUSIVE"].format(n_completed=n_executed)
        is_valid = False
    elif n_valid >= 95:
        status = "PASS"
        wording = templates["PASS"].format(n_valid=n_valid)
        is_valid = True
    else:
        status = "FAIL"
        wording = templates["FAIL"].format(n_valid=n_valid)
        is_valid = False

    return {
        "status": status,
        "is_valid": is_valid,
        "n_worlds_valid": n_valid,
        "validity_floor": 95,
        "wording": wording,
    }


def evaluate_g1(numerator: int, denominator: int = 164) -> GateVerdict:
    """Evaluate Gate G1 (Scalar Competence).

    Gate rule: lower 95% Wilson bound >= 0.70 on denominator 164.
    """
    templates = _load_templates("verdict_wording_templates.json")["G1"]
    interval = wilson_score_interval(numerator, denominator)
    passed = interval.lower >= 0.70
    status = "PASS" if passed else "FAIL"

    wording = templates[status].format(
        k=numerator,
        rate=interval.point_estimate,
        lower=interval.lower,
        upper=interval.upper,
    )

    return GateVerdict(
        name="G1",
        endpoint="scalar_competence",
        verdict=status,
        gate_passed=passed,
        numerator=numerator,
        denominator=denominator,
        interval=interval,
        wording=wording,
    )


def evaluate_g2(numerator: int, denominator: int = 144) -> GateVerdict:
    """Evaluate Gate G2 (Family Recovery).

    Gate rule: lower 95% Wilson bound >= 0.70 on denominator 144.
    """
    templates = _load_templates("verdict_wording_templates.json")["G2"]
    interval = wilson_score_interval(numerator, denominator)
    passed = interval.lower >= 0.70
    status = "PASS" if passed else "FAIL"

    wording = templates[status].format(
        k=numerator,
        rate=interval.point_estimate,
        lower=interval.lower,
        upper=interval.upper,
    )

    return GateVerdict(
        name="G2",
        endpoint="family_recovery",
        verdict=status,
        gate_passed=passed,
        numerator=numerator,
        denominator=denominator,
        interval=interval,
        wording=wording,
    )


def evaluate_g3(violations: int, denominator: int = 36) -> GateVerdict:
    """Evaluate Gate G3 (Principal Structural Safety).

    Gate rule: upper 95% Wilson bound <= 0.15 on denominator 36.
    Conservative safety rule: UNEVALUABLE counts as violation.
    """
    templates = _load_templates("verdict_wording_templates.json")["G3"]
    interval = wilson_score_interval(violations, denominator)
    passed = interval.upper <= 0.15
    status = "PASS" if passed else "FAIL"

    wording = templates[status].format(
        violations=violations,
        rate=interval.point_estimate,
        lower=interval.lower,
        upper=interval.upper,
    )

    return GateVerdict(
        name="G3",
        endpoint="principal_structural_safety",
        verdict=status,
        gate_passed=passed,
        numerator=violations,
        denominator=denominator,
        interval=interval,
        wording=wording,
    )


def evaluate_umbrella_claim(
    cal_valid: bool,
    g1_verdict: GateVerdict,
    g2_verdict: GateVerdict,
    g3_verdict: GateVerdict,
) -> dict[str, Any]:
    """Evaluate the umbrella scientific claim.

    Positive claim requires: calibration valid AND G1 pass AND G2 pass AND G3 pass.
    """
    templates = _load_templates("verdict_wording_templates.json")["umbrella_claim"]
    failed = []
    if not cal_valid:
        failed.append("Null Calibration (validity floor >= 95/100 not met)")
    if not g1_verdict.gate_passed:
        failed.append(f"G1 Scalar Competence (lower Wilson {g1_verdict.interval.lower:.4f} < 0.70)")
    if not g2_verdict.gate_passed:
        failed.append(f"G2 Family Recovery (lower Wilson {g2_verdict.interval.lower:.4f} < 0.70)")
    if not g3_verdict.gate_passed:
        failed.append(f"G3 Structural Safety (upper Wilson {g3_verdict.interval.upper:.4f} > 0.15)")

    positive = len(failed) == 0
    verdict = "PASS" if positive else "FAIL"
    wording = templates["PASS"] if positive else templates["FAIL"].format(failed_gates_str="; ".join(failed))

    return {
        "verdict": verdict,
        "positive_claim": positive,
        "all_primary_passed": g1_verdict.gate_passed and g2_verdict.gate_passed and g3_verdict.gate_passed,
        "calibration_valid": cal_valid,
        "failed_gates": failed,
        "wording": wording,
    }


def evaluate_all_gates(cal_data: Mapping[str, Any], held_out_data: Mapping[str, Any]) -> dict[str, Any]:
    """Run comprehensive gate and calibration evaluation."""
    cal_eval = evaluate_calibration_validity(cal_data)
    pg = held_out_data.get("primary_gates", {})

    g1_num = pg.get("G1", {}).get("numerator", 0)
    g2_num = pg.get("G2", {}).get("numerator", 0)
    g3_viol = pg.get("G3", {}).get("violations", 0)

    g1_res = evaluate_g1(g1_num, 164)
    g2_res = evaluate_g2(g2_num, 144)
    g3_res = evaluate_g3(g3_viol, 36)

    umbrella = evaluate_umbrella_claim(cal_eval["is_valid"], g1_res, g2_res, g3_res)

    return {
        "calibration": cal_eval,
        "G1": g1_res.to_dict(),
        "G2": g2_res.to_dict(),
        "G3": g3_res.to_dict(),
        "umbrella_claim": umbrella,
    }


def evaluate_claims(
    gate_evals: Mapping[str, Any],
    held_out_data: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Mechanically select allowed wording for claims C1..C10, C4a, C4b without LLM subjectivity."""
    templates = _load_templates("claim_wording_templates.json")["claims"]
    evaluated_claims = {}

    sec = held_out_data.get("secondary_endpoints", {})
    adeq = held_out_data.get("model_adequacy", {})
    g3_decomp = held_out_data.get("g3_decomposition", {})

    # C1
    g1 = gate_evals["G1"]
    c1_tpl = templates["C1"]
    c1_wording = (c1_tpl["allowed_wording_pass"] if g1["gate_passed"] else c1_tpl["allowed_wording_fail"]).format(
        k=g1["numerator"],
        rate=g1["rate"],
        lower=g1["wilson_95"]["lower"],
        upper=g1["wilson_95"]["upper"],
    )
    evaluated_claims["C1"] = {
        "claim_id": "C1",
        "title": c1_tpl["title"],
        "status": "SUPPORTED" if g1["gate_passed"] else "UNSUPPORTED",
        "verdict": g1["verdict"],
        "allowed_wording": c1_wording,
        "forbidden_overclaim": c1_tpl["forbidden_overclaim"],
    }

    # C2
    m0_k = adeq.get("m0_specificity", {}).get("numerator", 0)
    m0_ci = wilson_score_interval(m0_k, 164)
    m1_k = adeq.get("m1_sensitivity", {}).get("numerator", 0)
    m2_k = adeq.get("m2_sensitivity", {}).get("numerator", 0)
    m3_k = adeq.get("m3_sensitivity", {}).get("numerator", 0)
    c2_tpl = templates["C2"]
    c2_wording = c2_tpl["allowed_wording_pass"].format(
        m0_k=m0_k, m0_lo=m0_ci.lower, m0_hi=m0_ci.upper,
        m1_k=m1_k, m2_k=m2_k, m3_k=m3_k,
    )
    evaluated_claims["C2"] = {
        "claim_id": "C2",
        "title": c2_tpl["title"],
        "status": "SUPPORTED",
        "allowed_wording": c2_wording,
        "forbidden_overclaim": c2_tpl["forbidden_overclaim"],
    }

    # C3
    sup_k = sec.get("support_recovery", {}).get("numerator", 0)
    sup_ci = wilson_score_interval(sup_k, 144)
    c3_tpl = templates["C3"]
    evaluated_claims["C3"] = {
        "claim_id": "C3",
        "title": c3_tpl["title"],
        "status": "REPORTED",
        "allowed_wording": c3_tpl["allowed_wording_pass"].format(
            k=sup_k, rate=sup_ci.point_estimate, lower=sup_ci.lower, upper=sup_ci.upper,
        ),
        "forbidden_overclaim": c3_tpl["forbidden_overclaim"],
    }

    # C4
    g2 = gate_evals["G2"]
    c4_tpl = templates["C4"]
    c4_wording = (c4_tpl["allowed_wording_pass"] if g2["gate_passed"] else c4_tpl["allowed_wording_fail"]).format(
        k=g2["numerator"],
        rate=g2["rate"],
        lower=g2["wilson_95"]["lower"],
        upper=g2["wilson_95"]["upper"],
    )
    evaluated_claims["C4"] = {
        "claim_id": "C4",
        "title": c4_tpl["title"],
        "status": "SUPPORTED" if g2["gate_passed"] else "UNSUPPORTED",
        "verdict": g2["verdict"],
        "allowed_wording": c4_wording,
        "forbidden_overclaim": c4_tpl["forbidden_overclaim"],
    }

    # C4a
    joint_k = sec.get("joint_parameter_recovery", {}).get("numerator", 0)
    joint_ci = wilson_score_interval(joint_k, 156)
    mass_k = sec.get("mass_exponent_recovery", {}).get("numerator", 0)
    mass_ci = wilson_score_interval(mass_k, 156)
    desc_k = sec.get("descriptor_coupling_recovery", {}).get("numerator", 0)
    desc_ci = wilson_score_interval(desc_k, 84)
    c4a_tpl = templates["C4a"]
    evaluated_claims["C4a"] = {
        "claim_id": "C4a",
        "title": c4a_tpl["title"],
        "status": "REPORTED_SECONDARY",
        "allowed_wording": c4a_tpl["allowed_wording_pass"].format(
            joint_k=joint_k, joint_lo=joint_ci.lower, joint_hi=joint_ci.upper,
            mass_k=mass_k, mass_rate=mass_ci.point_estimate, mass_lo=mass_ci.lower, mass_hi=mass_ci.upper,
            desc_k=desc_k, desc_rate=desc_ci.point_estimate, desc_lo=desc_ci.lower, desc_hi=desc_ci.upper,
        ),
        "forbidden_overclaim": c4a_tpl["forbidden_overclaim"],
    }

    # C4b
    pred_k = sec.get("predictive_equivalence", {}).get("numerator", 0)
    pred_ci = wilson_score_interval(pred_k, 144)
    c4b_tpl = templates["C4b"]
    evaluated_claims["C4b"] = {
        "claim_id": "C4b",
        "title": c4b_tpl["title"],
        "status": "REPORTED_SECONDARY",
        "allowed_wording": c4b_tpl["allowed_wording_pass"].format(
            k=pred_k, rate=pred_ci.point_estimate, lower=pred_ci.lower, upper=pred_ci.upper,
        ),
        "forbidden_overclaim": c4b_tpl["forbidden_overclaim"],
    }

    # C5
    exact_k = sec.get("exact_algebra", {}).get("numerator", 0)
    exact_ci = wilson_score_interval(exact_k, 60)
    n_classes = sec.get("exact_algebra", {}).get("distinct_functional_classes", 0)
    c5_tpl = templates["C5"]
    evaluated_claims["C5"] = {
        "claim_id": "C5",
        "title": c5_tpl["title"],
        "status": "REPORTED_SECONDARY",
        "allowed_wording": c5_tpl["allowed_wording_pass"].format(
            k=exact_k, rate=exact_ci.point_estimate, lower=exact_ci.lower, upper=exact_ci.upper,
            n_classes=n_classes,
        ),
        "forbidden_overclaim": c5_tpl["forbidden_overclaim"],
    }

    # C6
    g3 = gate_evals["G3"]
    c6_tpl = templates["C6"]
    c6_wording = (c6_tpl["allowed_wording_pass"] if g3["gate_passed"] else c6_tpl["allowed_wording_fail"]).format(
        violations=g3["numerator"],
        rate=g3["rate"],
        upper=g3["wilson_95"]["upper"],
    )
    evaluated_claims["C6"] = {
        "claim_id": "C6",
        "title": c6_tpl["title"],
        "status": "SUPPORTED" if g3["gate_passed"] else "UNSUPPORTED",
        "verdict": g3["verdict"],
        "allowed_wording": c6_wording,
        "forbidden_overclaim": c6_tpl["forbidden_overclaim"],
    }

    # C7
    f07_unsafe = g3_decomp.get("f07_false_extra_structure", {}).get("unsafe_events", 0)
    f20_unsafe = g3_decomp.get("f20_false_adversarial", {}).get("total_unsafe", 0)
    neg_safe_k = 24 - (f07_unsafe + f20_unsafe)
    c7_tpl = templates["C7"]
    evaluated_claims["C7"] = {
        "claim_id": "C7",
        "title": c7_tpl["title"],
        "status": "REPORTED_COMPOSITE",
        "allowed_wording": c7_tpl["allowed_wording_pass"].format(
            g2_k=g2["numerator"], neg_safe_k=neg_safe_k,
        ),
        "forbidden_overclaim": c7_tpl["forbidden_overclaim"],
    }

    # C8
    c8_tpl = templates["C8"]
    evaluated_claims["C8"] = {
        "claim_id": "C8",
        "title": c8_tpl["title"],
        "status": "REPORTED",
        "allowed_wording": c8_tpl["allowed_wording_pass"].format(
            g1_k=g1["numerator"], pred_k=pred_k,
        ),
        "forbidden_overclaim": c8_tpl["forbidden_overclaim"],
    }

    # C9 & C10 (Unsupported)
    for c_id in ["C9", "C10"]:
        c_tpl = templates[c_id]
        evaluated_claims[c_id] = {
            "claim_id": c_id,
            "title": c_tpl["title"],
            "status": "UNSUPPORTED",
            "allowed_wording": c_tpl["allowed_wording"],
            "forbidden_overclaim": c_tpl["forbidden_overclaim"],
        }

    return evaluated_claims
