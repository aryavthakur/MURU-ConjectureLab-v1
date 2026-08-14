"""Unit tests for MURU Prospective Result Ingestion Scaffold."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from paper.results.scripts.wilson import (
    wilson_score_interval,
    wilson_lower_95,
    wilson_upper_95,
    clopper_pearson_upper_bound,
)
from paper.results.scripts.verdict_engine import (
    evaluate_calibration_validity,
    evaluate_g1,
    evaluate_g2,
    evaluate_g3,
    evaluate_umbrella_claim,
    evaluate_all_gates,
    evaluate_claims,
)
from paper.results.schema.validators import (
    validate_calibration_result,
    validate_development_aggregate,
    validate_held_out_aggregate,
    validate_case_outcome,
    validate_paper_result_payload,
    SchemaValidationError,
    G1_HELD_OUT_DENOMINATOR,
    G2_HELD_OUT_DENOMINATOR,
    G3_HELD_OUT_DENOMINATOR,
)
from paper.results.scripts.render_prospective_figures import (
    render_all_prospective_figures,
    ResultArtifactMissingError,
)
from paper.results.scripts.populate_tables import populate_all_tables
from paper.results.scripts.update_claim_matrix import populate_claim_matrix, update_claim_matrix_file
from paper.results.scripts.update_evidence_ledger import generate_class_c_ledger_entries, update_evidence_ledger_file
from paper.results.scripts.export_paper_results_json import assemble_master_payload, export_master_payload_file


class TestWilsonMath(unittest.TestCase):

    def test_wilson_exact_calculation(self):
        # 164 successes out of 164
        res_full = wilson_score_interval(164, 164)
        self.assertAlmostEqual(res_full.point_estimate, 1.0)
        self.assertGreater(res_full.lower, 0.97)
        self.assertEqual(res_full.upper, 1.0)

        # 0 successes out of 164
        res_zero = wilson_score_interval(0, 164)
        self.assertAlmostEqual(res_zero.point_estimate, 0.0)
        self.assertEqual(res_zero.lower, 0.0)
        self.assertLess(res_zero.upper, 0.03)

        # 120 of 144
        res_mid = wilson_score_interval(120, 144)
        self.assertAlmostEqual(res_mid.point_estimate, 120 / 144)
        self.assertTrue(0.75 < res_mid.lower < res_mid.upper < 0.90)

    def test_clopper_pearson_reproduction(self):
        # n = 100 with zero errors yields upper 95% = 0.0362
        cp_100 = clopper_pearson_upper_bound(100)
        self.assertAlmostEqual(cp_100, 0.03621669, places=4)

        # n = 8 with zero errors yields upper 95% = 0.3694
        cp_8 = clopper_pearson_upper_bound(8)
        self.assertAlmostEqual(cp_8, 0.3694, places=4)


class TestVerdictEngine(unittest.TestCase):

    def test_calibration_verdicts(self):
        valid_res = evaluate_calibration_validity({"n_worlds_valid": 98, "n_worlds_executed": 100})
        self.assertEqual(valid_res["status"], "PASS")
        self.assertTrue(valid_res["is_valid"])

        invalid_res = evaluate_calibration_validity({"n_worlds_valid": 90, "n_worlds_executed": 100})
        self.assertEqual(invalid_res["status"], "FAIL")
        self.assertFalse(invalid_res["is_valid"])

        inconclusive_res = evaluate_calibration_validity({"n_worlds_valid": 50, "n_worlds_executed": 50})
        self.assertEqual(inconclusive_res["status"], "INCONCLUSIVE")

    def test_g1_gate_rules(self):
        # 150/164 passes lower >= 0.70
        g1_pass = evaluate_g1(150, 164)
        self.assertEqual(g1_pass.verdict, "PASS")
        self.assertTrue(g1_pass.gate_passed)
        self.assertIn("Gate G1 PASSED", g1_pass.wording)

        # 100/164 fails lower >= 0.70 (100/164 = 0.609)
        g1_fail = evaluate_g1(100, 164)
        self.assertEqual(g1_fail.verdict, "FAIL")
        self.assertFalse(g1_fail.gate_passed)
        self.assertIn("Gate G1 FAILED", g1_fail.wording)

    def test_g2_gate_rules(self):
        # 130/144 passes
        g2_pass = evaluate_g2(130, 144)
        self.assertEqual(g2_pass.verdict, "PASS")
        self.assertTrue(g2_pass.gate_passed)

        # 80/144 fails
        g2_fail = evaluate_g2(80, 144)
        self.assertEqual(g2_fail.verdict, "FAIL")
        self.assertFalse(g2_fail.gate_passed)

    def test_g3_gate_rules(self):
        # 1 violation out of 36 -> upper bound ~0.141 <= 0.15 (Pass)
        g3_pass = evaluate_g3(1, 36)
        self.assertEqual(g3_pass.verdict, "PASS")
        self.assertTrue(g3_pass.gate_passed)

        # 5 violations out of 36 -> upper bound ~0.285 > 0.15 (Fail)
        g3_fail = evaluate_g3(5, 36)
        self.assertEqual(g3_fail.verdict, "FAIL")
        self.assertFalse(g3_fail.gate_passed)

    def test_umbrella_claim_logic(self):
        g1_p = evaluate_g1(150, 164)
        g2_p = evaluate_g2(130, 144)
        g3_p = evaluate_g3(1, 36)
        umb_pass = evaluate_umbrella_claim(True, g1_p, g2_p, g3_p)
        self.assertEqual(umb_pass["verdict"], "PASS")
        self.assertTrue(umb_pass["positive_claim"])

        # Any single failure makes umbrella claim fail
        umb_fail_g1 = evaluate_umbrella_claim(True, evaluate_g1(50, 164), g2_p, g3_p)
        self.assertEqual(umb_fail_g1["verdict"], "FAIL")
        self.assertFalse(umb_fail_g1["positive_claim"])

        umb_fail_cal = evaluate_umbrella_claim(False, g1_p, g2_p, g3_p)
        self.assertEqual(umb_fail_cal["verdict"], "FAIL")
        self.assertFalse(umb_fail_cal["positive_claim"])


class TestSchemaValidators(unittest.TestCase):

    def _sample_calibration_data(self) -> dict:
        table = []
        for c in range(1, 21):
            table.append({
                "complexity": c,
                "null_median": -0.1 + 0.01 * c,
                "threshold": 0.1 + 0.02 * c,
                "bootstrap_interval_95": {"lower": 0.05 + 0.02 * c, "upper": 0.15 + 0.02 * c},
            })
        return {
            "schema_version": "muru-calibration-result-schema-1.0.0",
            "n_worlds_executed": 100,
            "n_worlds_valid": 97,
            "validity_floor": 95,
            "validity_verdict": "VALID",
            "total_seeds_attempted": 3000,
            "total_seeds_completed": 3000,
            "execution_failure_seeds": 3,
            "completed_no_candidate_seeds": 0,
            "wall_clock_runtime_seconds": 1200.0,
            "threshold_table": table,
            "per_construction_diagnostics": {
                "target_permuted_across_compounds": {
                    "n_worlds": 34, "p95_c4": 0.1, "p95_c10": 0.2, "p95_c20": 0.3, "mean_constant_model_r2": -0.05
                },
                "descriptors_permuted_across_compounds": {
                    "n_worlds": 33, "p95_c4": 0.1, "p95_c10": 0.2, "p95_c20": 0.3, "mean_constant_model_r2": -0.05
                },
                "gaussian_targets_with_observed_variance": {
                    "n_worlds": 33, "p95_c4": 0.1, "p95_c10": 0.2, "p95_c20": 0.3, "mean_constant_model_r2": -0.05
                },
            },
        }

    def _sample_case_record(self, cid: str) -> dict:
        return {
            "case_id": cid,
            "partition": "held_out",
            "family": "F01",
            "variant": "base",
            "replicate": 0,
            "g_spearman": 0.95,
            "trajectory_mae": 0.40,
            "per_energy_mean_mae": 1.0,
            "adequacy_status": "M0_NOT_REJECTED",
            "m0_accepted": True,
            "candidate_expression": "mass**0.5",
            "candidate_complexity": 3,
            "candidate_valid_r2": 0.85,
            "null_threshold": 0.25,
            "structural_acceptance_status": "STRUCTURAL_ACCEPTED",
            "accepted": True,
            "effective_support": ["mass"],
            "support_status": "MATCH",
            "discovered_family": "mass_power",
            "truth_family": "mass_power",
            "family_status": "MATCH",
            "g1_scalar_competent": True,
            "g2_family_recovered": True,
            "g3_event": "SAFE",
            "parameter_recovery": {
                "applicable": True,
                "p_mass_truth": 0.50,
                "p_mass_discovered": 0.50,
                "p_mass_error": 0.0,
                "p_mass_recovered": True,
                "c_desc_truth": None,
                "c_desc_discovered": None,
                "c_desc_error": None,
                "c_desc_recovered": None,
                "joint_recovered": True,
            },
            "predictive_equivalence": {
                "applicable": True,
                "valid_fraction": 1.0,
                "c_star": 1.0,
                "rel_rmse": 0.01,
                "pearson_r": 0.999,
                "passed": True,
            },
            "exact_algebra": {
                "applicable": True,
                "symbolically_equivalent": True,
                "functional_equivalence_class": "mass_power_canon",
            },
            "diagnostics": {
                "boundary_hit": False,
                "unsupported_non_mass": False,
                "richer_family": False,
                "adversarial_flagged": False,
                "null_flagged": False,
            },
        }

    def _sample_held_out_data(self) -> dict:
        cases = [self._sample_case_record(f"PB|held_out|F{(i%20)+1:02d}|r{i//20:03d}") for i in range(240)]
        return {
            "schema_version": "muru-held-out-aggregate-schema-1.0.0",
            "partition": "held_out",
            "total_cases": 240,
            "primary_gates": {
                "G1": {
                    "name": "G1", "endpoint": "scalar_competence", "numerator": 150, "denominator": 164,
                    "rate": 150 / 164, "wilson_95": {"lower": 0.86, "upper": 0.95}, "gate_threshold": 0.70, "passed": True
                },
                "G2": {
                    "name": "G2", "endpoint": "family_recovery", "numerator": 130, "denominator": 144,
                    "rate": 130 / 144, "wilson_95": {"lower": 0.84, "upper": 0.94}, "gate_threshold": 0.70, "passed": True
                },
                "G3": {
                    "name": "G3", "endpoint": "principal_structural_safety", "violations": 1, "denominator": 36,
                    "rate": 1 / 36, "wilson_95": {"lower": 0.005, "upper": 0.14}, "gate_threshold": 0.15, "passed": True,
                    "unevaluable_count": 0
                },
            },
            "umbrella_decision": {
                "positive_claim": True, "all_primary_passed": True, "calibration_valid": True, "failed_gates": []
            },
            "secondary_endpoints": {
                "joint_parameter_recovery": {"role": "SECONDARY", "numerator": 140, "denominator": 156, "rate": 140/156, "wilson_95": {"lower": 0.84, "upper": 0.93}},
                "mass_exponent_recovery": {"role": "SECONDARY_COMPONENT", "numerator": 145, "denominator": 156, "rate": 145/156, "wilson_95": {"lower": 0.88, "upper": 0.96}},
                "descriptor_coupling_recovery": {"role": "SECONDARY_COMPONENT", "numerator": 75, "denominator": 84, "rate": 75/84, "wilson_95": {"lower": 0.80, "upper": 0.94}},
                "predictive_equivalence": {"role": "SECONDARY", "numerator": 135, "denominator": 144, "rate": 135/144, "wilson_95": {"lower": 0.88, "upper": 0.96}, "n_reference_points": 2160, "n_frames": 12},
                "exact_algebra": {"role": "SECONDARY", "numerator": 15, "denominator": 60, "rate": 15/60, "wilson_95": {"lower": 0.16, "upper": 0.37}, "distinct_functional_classes": 8},
                "support_recovery": {"role": "SECONDARY", "numerator": 138, "denominator": 144, "rate": 138/144, "wilson_95": {"lower": 0.91, "upper": 0.98}},
            },
            "model_adequacy": {
                "m0_specificity": {"numerator": 155, "denominator": 164, "rate": 155/164, "wilson_95": {"lower": 0.89, "upper": 0.97}},
                "m1_sensitivity": {"numerator": 34, "denominator": 36, "rate": 34/36, "wilson_95": {"lower": 0.82, "upper": 0.98}},
                "m2_sensitivity": {"numerator": 22, "denominator": 24, "rate": 22/24, "wilson_95": {"lower": 0.73, "upper": 0.98}},
                "m3_sensitivity": {"numerator": 23, "denominator": 24, "rate": 23/24, "wilson_95": {"lower": 0.79, "upper": 0.99}},
                "f16_breakdown": {"m1_detected": 10, "m2_detected": 8, "m3_detected": 9, "at_least_one_detected": 12, "denominator": 12},
            },
            "diagnostics": {
                "boundary_hit": {"numerator": 1, "denominator": 12, "rate": 1/12, "wilson_95": {"lower": 0.01, "upper": 0.35}},
                "response_structure_diagnostic": {"numerator": 0, "denominator": 4, "rate": 0.0, "wilson_95": {"lower": 0.0, "upper": 0.49}},
                "scalar_target_yield": {"numerator": 164, "denominator": 164, "rate": 1.0, "wilson_95": {"lower": 0.97, "upper": 1.0}},
            },
            "g3_decomposition": {
                "f07_false_extra_structure": {"unsafe_events": 0, "denominator": 12, "rate": 0.0, "wilson_95": {"lower": 0.0, "upper": 0.24}},
                "f19_false_null_structure": {"f19a_unsafe": 0, "f19b_unsafe": 0, "f19c_unsafe": 0, "total_unsafe": 0, "denominator": 12, "rate": 0.0, "wilson_95": {"lower": 0.0, "upper": 0.24}},
                "f20_false_adversarial": {"f20a_unsafe": 0, "f20b_unsafe": 1, "f20c_unsafe": 0, "total_unsafe": 1, "denominator": 12, "rate": 1/12, "wilson_95": {"lower": 0.01, "upper": 0.35}},
            },
            "by_truth_family": {
                "mass_power": {"cases": 24, "support_match": 24, "family_match": 22, "g2_both": 22, "param_rec": 24, "pred_equiv": 23, "exact_algebra": 8},
            },
            "failure_census": {"REJECTED_A1_INADEQUATE": 5, "UNEVALUABLE": 0},
            "cases": cases,
        }

    def test_calibration_validator_success(self):
        data = self._sample_calibration_data()
        validated = validate_calibration_result(data)
        self.assertEqual(validated["n_worlds_valid"], 97)

    def test_calibration_validator_non_monotone(self):
        data = self._sample_calibration_data()
        data["threshold_table"][5]["threshold"] = 0.01  # drop
        with self.assertRaises(SchemaValidationError):
            validate_calibration_result(data)

    def test_held_out_validator_denominator_enforcement(self):
        bad_ho = {
            "schema_version": "muru-held-out-aggregate-schema-1.0.0",
            "partition": "held_out",
            "total_cases": 240,
            "primary_gates": {
                "G1": {"name": "G1", "endpoint": "scalar_competence", "numerator": 100, "denominator": 150},  # Wrong: should be 164
            }
        }
        with self.assertRaises(SchemaValidationError):
            validate_held_out_aggregate(bad_ho)

    def test_held_out_validator_success(self):
        ho_data = self._sample_held_out_data()
        validated = validate_held_out_aggregate(ho_data)
        self.assertEqual(validated["total_cases"], 240)


class TestTableAndLedgerPopulators(unittest.TestCase):

    def setUp(self):
        self.cal_data = TestSchemaValidators()._sample_calibration_data()
        self.ho_data = TestSchemaValidators()._sample_held_out_data()
        
        dev_cases = [TestSchemaValidators()._sample_case_record(f"PB|development|F{(i%20)+1:02d}|r{i//20:03d}") for i in range(80)]
        for c in dev_cases:
            c["partition"] = "development"
        self.dev_data = {
            "schema_version": "muru-development-aggregate-schema-1.0.0",
            "partition": "development",
            "total_cases": 80,
            "denominators": {
                "scalar_competence": 55, "family_recovery": 48, "principal_structural_safety": 12,
                "support_recovery": 48, "parameter_recovery": 52, "predictive_equivalence": 48,
                "exact_algebra": 20, "m0_specificity": 55, "m1_sensitivity": 12,
                "m2_sensitivity": 8, "m3_sensitivity": 8,
            },
            "numerators": {
                "scalar_competence": 50, "family_recovery": 45, "principal_structural_safety": 0,
                "support_recovery": 46, "parameter_recovery": 48, "predictive_equivalence": 45,
                "exact_algebra": 5, "m0_specificity": 52, "m1_sensitivity": 12,
                "m2_sensitivity": 8, "m3_sensitivity": 8,
            },
            "rates": {},
            "wilson_95": {},
            "engine_failures": 0,
            "runtime_seconds": 300.0,
            "peak_memory_mb": 512.0,
            "cases": dev_cases,
        }

        self.payload = assemble_master_payload(
            cal_data=self.cal_data,
            dev_data=self.dev_data,
            held_out_data=self.ho_data,
            code_commit="0cd8038",
        )

    def test_table_population_creates_all_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            populate_all_tables(self.payload, out_dir)
            
            tables_dir = out_dir / "paper" / "tables" / "results"
            self.assertTrue(tables_dir.exists())
            
            expected_tables = [
                "table_03b_calibration_execution",
                "table_03c_threshold_table",
                "table_03d_calibration_diagnostics",
                "table_04_development_results",
                "table_05_held_out_primary",
                "table_05a_secondary_and_diagnostic",
                "table_06_symbolic_by_family",
                "table_07_false_discovery_and_refusals",
                "table_08_challenge_outcomes",
                "table_09_historical_vs_prospective",
            ]
            for tname in expected_tables:
                self.assertTrue((tables_dir / f"{tname}.md").exists(), f"Missing {tname}.md")
                self.assertTrue((tables_dir / f"{tname}.tex").exists(), f"Missing {tname}.tex")
                self.assertTrue((tables_dir / f"{tname}.json").exists(), f"Missing {tname}.json")

    def test_class_c_ledger_entries(self):
        entries = generate_class_c_ledger_entries(self.payload)
        self.assertEqual(len(entries), 18)
        self.assertEqual(entries[0]["id"], "P001")
        self.assertEqual(entries[0]["evidence_class"], "C")
        self.assertEqual(entries[0]["status"], "populated_prospective")


class TestFailClosedGuarantees(unittest.TestCase):

    def test_figures_fail_closed_without_artifacts(self):
        with self.assertRaises(ResultArtifactMissingError):
            render_all_prospective_figures(None, Path("/tmp"))

        with self.assertRaises(ResultArtifactMissingError):
            render_all_prospective_figures({}, Path("/tmp"))

    def test_ingest_cli_fails_closed_when_missing_inputs(self):
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script = repo_root / "paper" / "results" / "scripts" / "ingest_results.py"
        res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertIn("RESULT_ARTIFACT_MISSING", res.stderr)


if __name__ == "__main__":
    unittest.main()
