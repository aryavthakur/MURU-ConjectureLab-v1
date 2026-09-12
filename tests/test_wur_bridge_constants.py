"""The preregistered constants are a contract. These tests exist so that
changing one shows up as a failing test, not a silent edit."""
from muru import wur_bridge_constants as K


def test_gate_thresholds_match_the_preregistration():
    assert K.MEDIAN_ABS_DELTA_MAX == 0.05
    assert K.SPEARMAN_MIN == 0.80
    assert K.MIN_PASSING_ENERGIES == 5
    assert K.OFFSET_MAX == 0.15


def test_ladder_is_the_six_point_nce_ladder():
    assert K.LADDER_ENERGIES == (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def test_base_cell_matches_configs_preprocessing_yaml():
    import yaml
    from pathlib import Path
    cfg = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "configs" / "preprocessing.yaml").read_text())
    assert K.BASE_CELL["relative_cutoff"] == cfg["base_cell"]["relative_cutoff"]
    assert K.BASE_CELL["include_precursor"] == cfg["base_cell"]["include_precursor"]
    assert K.BASE_CELL["intensity_transform"] == cfg["base_cell"]["intensity_transform"]
    assert K.PRECURSOR_MATCH_PPM == cfg["precursor_match_ppm"]


def test_alignment_bounds_are_a_positive_monotone_box():
    lo, hi = K.ALIGNMENT_B_BOUNDS
    assert lo > 0 and hi > lo
    a_lo, a_hi = K.ALIGNMENT_A_BOUNDS
    assert a_lo < 0 < a_hi


def test_duplicate_aggregator_is_the_preregistered_median():
    assert K.DUPLICATE_AGGREGATOR == "median"


def test_seed_matches_the_stage_zero_seed():
    from muru.io.wur_partition import SEED as STAGE0_SEED
    assert K.SEED == STAGE0_SEED == 20260911
