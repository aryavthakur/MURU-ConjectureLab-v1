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


def test_alignment_box_bounds_are_exactly_the_preregistered_values():
    """The box is the constraint on the only fitted object in Stage 1.
    Widening it after seeing a fit that sits on a bound is the archetypal
    post-hoc move, so the exact values are pinned, not just their shape."""
    assert K.ALIGNMENT_A_BOUNDS == (-30.0, 30.0)
    assert K.ALIGNMENT_B_BOUNDS == (0.5, 2.0)


def test_alignment_optimizer_settings_are_pinned():
    assert K.ALIGNMENT_MAXITER == 1000
    assert K.ALIGNMENT_TOL == 1e-8
    assert K.ALIGNMENT_POLISH is True


def test_small_sample_floors_are_pinned():
    assert K.MIN_PAIRS_FOR_CORRELATION == 3
    assert K.MIN_POPULATION_B == 30


def test_every_gate_threshold_appears_in_the_preregistration_document():
    """The document, not this module, is the source of truth. This closes
    the loop: a constant edited without a matching erratum fails here."""
    from pathlib import Path
    doc = (Path(__file__).resolve().parents[1]
           / "MURU_WUR_REAL_DATA_PREREGISTRATION.md").read_text()
    section5 = doc[doc.index("## 5. Stage 1"):doc.index("## 6. Inherited")]
    assert f"**{K.MEDIAN_ABS_DELTA_MAX}**" in section5
    assert f"**{K.SPEARMAN_MIN:.2f}**" in section5
    assert f"**{K.MIN_PASSING_ENERGIES} of the 6**" in section5
    assert f"**{K.OFFSET_MAX}**" in section5
    assert f"**{K.MIN_POPULATION_B}**" in section5
    assert f"fewer than {K.MIN_PAIRS_FOR_CORRELATION} pairs" in section5
    assert f"[{K.ALIGNMENT_A_BOUNDS[0]:.0f}, {K.ALIGNMENT_A_BOUNDS[1]:.0f}]" in section5
    assert f"[{K.ALIGNMENT_B_BOUNDS[0]}, {K.ALIGNMENT_B_BOUNDS[1]}]" in section5
    assert f"maxiter = {K.ALIGNMENT_MAXITER}" in section5


def test_the_document_records_an_errata_section():
    from pathlib import Path
    doc = (Path(__file__).resolve().parents[1]
           / "MURU_WUR_REAL_DATA_PREREGISTRATION.md").read_text()
    assert "## 12. Errata" in doc
    assert "E-1" in doc
