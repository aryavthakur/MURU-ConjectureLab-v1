from muru.paper_benchmark.analysis import endpoint_applies, endpoint_denominator


def test_endpoint_denominators_reconstruct_from_variant_applicability():
    assert endpoint_denominator("scalar_competence") == 164
    assert endpoint_denominator("family_recovery") == 144
    assert endpoint_denominator("principal_structural_safety") == 36


def test_f19c_is_excluded_from_m0_and_scalar_but_included_in_null_safety():
    f19c = "PB|held_out|F19|r008"
    assert not endpoint_applies("scalar_competence", f19c)
    assert not endpoint_applies("m0_specificity", f19c)
    assert endpoint_applies("false_null_structure", f19c)
    assert endpoint_applies("principal_structural_safety", f19c)
