from muru.paper_benchmark.registry import (
    CASE_FAMILIES,
    ENERGY_GRID,
    ROOT_SEED,
    endpoint_case_count,
    endpoint_applies_to_variant,
    resolve_case_id,
)


def test_registry_reconstructs_the_frozen_partition_shape():
    assert sum(f.partition_counts["development"] for f in CASE_FAMILIES) == 80
    assert sum(f.partition_counts["held_out"] for f in CASE_FAMILIES) == 240
    assert sum(f.partition_counts["challenge"] for f in CASE_FAMILIES) == 60
    assert len(CASE_FAMILIES) == 20
    assert ROOT_SEED == 20260813
    assert ENERGY_GRID == (15, 30, 45, 60, 75, 90)


def test_f19_variants_have_distinct_frozen_applicability():
    f19 = next(family for family in CASE_FAMILIES if family.code == "F19")
    assert f19.variants["F19A"].scalar_truth_defined is True
    assert f19.variants["F19B"].symbolic_truth_kind == "mass_only_allowance"
    assert f19.variants["F19C"].scalar_truth_defined is False
    assert f19.variants["F19C"].m0_adequacy_truth == "not_applicable"
    assert endpoint_applies_to_variant("m0_specificity", f19.variants["F19A"])
    assert not endpoint_applies_to_variant("m0_specificity", f19.variants["F19C"])
    assert endpoint_applies_to_variant("false_null_structure", f19.variants["F19C"])


def test_primary_endpoint_denominators_derive_from_applicability():
    assert endpoint_case_count("scalar_competence") == 164
    assert endpoint_case_count("family_recovery") == 144
    assert endpoint_case_count("principal_structural_safety") == 36


def test_development_f19_case_resolves_without_listing_held_out_cases():
    family, variant, replicate = resolve_case_id("PB|development|F19|r002")
    assert family.code == "F19"
    assert variant.code == "F19C"
    assert replicate == 2
