import pytest

from muru.paper_benchmark.contract import StrictCandidate, validate_candidate


def test_complex_and_nonfinite_candidates_are_rejected():
    with pytest.raises(ValueError, match="finite real"):
        validate_candidate(StrictCandidate("sqrt(-1)", (1 + 0j,), grammar_version="strict-v1"))
    with pytest.raises(ValueError, match="finite real"):
        validate_candidate(StrictCandidate("log(0)", (float("inf"),), grammar_version="strict-v1"))


def test_finite_real_candidate_with_versioned_contract_is_accepted():
    candidate = StrictCandidate("mass", (1.0, 2.0), grammar_version="strict-v1")
    validate_candidate(candidate)
