import json

from muru.paper_benchmark.generator import generate_case


def test_truth_record_serializes_required_machine_readable_fields():
    truth = generate_case("PB|development|F10|r000").truth
    payload = truth.to_dict()

    assert json.loads(json.dumps(payload)) == payload
    assert payload["case_id"] == "PB|development|F10|r000"
    assert payload["phi"]["family"] == "stretched_exponential"
    assert payload["active_variables"] == ["mass", "interaction_left", "interaction_right"]
    assert payload["noise"]["mechanism"] == "additive_gaussian"
    assert payload["missingness"]["mechanism"] == "none"


def test_f19_variant_truth_records_expected_null_behavior():
    truth = generate_case("PB|development|F19|r001").truth

    assert truth.variant == "F19B"
    assert truth.symbolic_truth_kind == "mass_only_allowance"
    assert "non-mass acceptance is false-null structure" in truth.expected_behavior
