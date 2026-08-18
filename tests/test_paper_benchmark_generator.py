import inspect

from muru.paper_benchmark.generator import generate_case


def test_development_case_rebuilds_bit_identically():
    first = generate_case("PB|development|F01|r000")
    second = generate_case("PB|development|F01|r000")

    assert first.content_hash == second.content_hash
    assert len(first.inputs.compounds) == 180
    assert first.inputs.compounds.scaffold_id.nunique() == 30
    assert set(first.inputs.compounds.split) == {"train", "validation", "test"}
    assert first.inputs.compounds.groupby("split").size().to_dict() == {
        "train": 120,
        "validation": 30,
        "test": 30,
    }


def test_missing_one_energy_case_has_exactly_five_observations_per_compound():
    generated = generate_case("PB|development|F04|r000")
    observations = generated.inputs.trajectories.groupby("compound_id").size()

    assert observations.nunique() == 1
    assert observations.iloc[0] == 5


def test_f19c_truth_excludes_scalar_and_m0_interpretation():
    truth = generate_case("PB|development|F19|r002").truth

    assert truth.variant == "F19C"
    assert truth.scalar_truth_defined is False
    assert truth.m0_adequacy_truth == "not_applicable"
    assert truth.g_by_compound == {}
    assert "response_structure_diagnostic" in truth.applicable_endpoints


def test_generator_has_no_real_or_historical_synthetic_import_path():
    import muru.paper_benchmark.generator as generator

    source = inspect.getsource(generator)
    assert "muru.synth" not in source
    assert "load_dev_covariates" not in source
    assert "read_parquet" not in source
