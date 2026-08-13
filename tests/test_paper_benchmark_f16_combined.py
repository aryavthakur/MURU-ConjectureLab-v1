"""Amendment A2 contract tests for the repaired F16 combined violation.

These are **contract** tests.  They assert that the generator's F16 response
mechanism contains the M1, M2 and M3 deviations its frozen truth declares, that
the combined form degenerates correctly, and that every frozen population
constant survives the repair.

They deliberately measure **no** detector performance.  Nothing here fits an
adequacy model, scores a Development or Held-out outcome, or asks whether a
violation is discoverable.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from muru.paper_benchmark.analysis import endpoint_denominator
from muru.paper_benchmark.generator import (
    COMBINED_M1_AMPLITUDE,
    COMBINED_M2_AMPLITUDE,
    COMBINED_M3_AMPLITUDE,
    COMBINED_M3_ATTENUATION_DENOMINATOR,
    COMBINED_M3_ATTENUATION_NUMERATOR,
    ENERGY_GRID,
    GENERATOR_VERSION,
    M1_HORIZONTAL_AMPLITUDE,
    M2_HIGH_ENERGY_AMPLITUDE,
    M3_CEILING_CLIP,
    M3_LOW_ENERGY_AMPLITUDE,
    combined_response,
    generate_case,
)
from muru.paper_benchmark.registry import CASE_FAMILIES, PARTITION_CASE_COUNTS, resolve_case_id

E_REF = 45.0
MU_INF, PHI_P = 0.22, 1.45
N = 40


@pytest.fixture(scope="module")
def coordinates() -> tuple[np.ndarray, np.ndarray]:
    """A deterministic normalised-energy grid and a descriptor vector.

    Dummy arrays only: these are not benchmark inputs and no case is read.
    """
    rng = np.random.default_rng(0)
    g = 1.4 * np.exp(rng.normal(0, 0.28, N))
    energy = np.asarray(ENERGY_GRID, dtype=float)
    u = (energy[None, :] / E_REF) / g[:, None]
    descriptor = np.linspace(0.0, 1.0, N)
    return u, descriptor


def _neutral(kind: str) -> np.ndarray:
    return {"shape": np.ones(N), "floor": np.full(N, MU_INF), "ceiling": np.ones(N)}[kind]


# --------------------------------------------------------------------------
# 1-4: the combined form degenerates to M0 and to each single-deviation branch
# --------------------------------------------------------------------------


def test_neutral_parameters_reduce_exactly_to_m0(coordinates):
    u, _ = coordinates
    m0 = MU_INF + (1 - MU_INF) * np.exp(-(u**PHI_P))

    combined = combined_response(u, PHI_P, _neutral("shape"), _neutral("floor"), _neutral("ceiling"))

    assert np.array_equal(combined, m0)


def test_shape_only_deviation_expresses_m1_behavior(coordinates):
    u, descriptor = coordinates
    shape = 1 + M1_HORIZONTAL_AMPLITUDE * np.tanh(descriptor)
    m1 = MU_INF + (1 - MU_INF) * np.exp(-(u**(PHI_P * shape[:, None])))

    combined = combined_response(u, PHI_P, shape, _neutral("floor"), _neutral("ceiling"))

    assert np.array_equal(combined, m1)
    # M1 is a horizontal warp: it moves the interior of the curve but leaves
    # both vertical endpoints at their M0 values.
    assert combined[:, 0].max() < 1.0
    assert np.allclose(combined.min(axis=1).min(), m1.min(axis=1).min())


def test_floor_only_deviation_expresses_m2_behavior(coordinates):
    u, descriptor = coordinates
    floor = np.clip(MU_INF + M2_HIGH_ENERGY_AMPLITUDE * (descriptor - 0.5), 0.03, 0.55)
    m2 = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**PHI_P))

    combined = combined_response(u, PHI_P, _neutral("shape"), floor, _neutral("ceiling"))

    assert np.array_equal(combined, m2)
    # M2 is a high-energy deviation: the asymptote becomes compound-specific.
    assert floor.min() < MU_INF < floor.max()


def test_ceiling_only_deviation_expresses_m3_behavior(coordinates):
    u, descriptor = coordinates
    ceiling = np.clip(1 - M3_LOW_ENERGY_AMPLITUDE * descriptor, *M3_CEILING_CLIP)
    m3 = MU_INF + (ceiling[:, None] - MU_INF) * np.exp(-(u**PHI_P))

    combined = combined_response(u, PHI_P, _neutral("shape"), _neutral("floor"), ceiling)

    assert np.array_equal(combined, m3)
    # M3 is a low-energy deviation: the plateau drops below the M0 value of 1.
    assert ceiling.max() <= M3_CEILING_CLIP[1]
    assert ceiling.min() < 1.0


def test_ceiling_pinned_at_one_is_the_pre_amendment_m3_neutral_form(coordinates):
    """The defect A2 repairs: the old F16 branch was this form at b = A_LO."""
    u, descriptor = coordinates
    shape = 1 + COMBINED_M1_AMPLITUDE * np.tanh(descriptor)
    floor = np.clip(MU_INF + COMBINED_M2_AMPLITUDE * (descriptor - 0.5), 0.03, 0.55)
    pre_amendment = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**(PHI_P * shape[:, None])))

    assert np.array_equal(combined_response(u, PHI_P, shape, floor, _neutral("ceiling")), pre_amendment)


# --------------------------------------------------------------------------
# 5: the frozen amplitudes and the A2 attenuation declaration
# --------------------------------------------------------------------------


def test_f16_amplitudes_are_all_non_neutral():
    assert COMBINED_M1_AMPLITUDE != 0.0
    assert COMBINED_M2_AMPLITUDE != 0.0
    assert COMBINED_M3_AMPLITUDE != 0.0


def test_m3_amplitude_is_the_f15_amplitude_attenuated_by_five_eighteenths():
    """A2 declaration: attenuate F15 by the smaller frozen F16 ratio, 5/18."""
    m1_ratio = Fraction(COMBINED_M1_AMPLITUDE).limit_denominator(10**6) / Fraction(M1_HORIZONTAL_AMPLITUDE).limit_denominator(10**6)
    m2_ratio = Fraction(COMBINED_M2_AMPLITUDE).limit_denominator(10**6) / Fraction(M2_HIGH_ENERGY_AMPLITUDE).limit_denominator(10**6)
    declared = Fraction(COMBINED_M3_ATTENUATION_NUMERATOR, COMBINED_M3_ATTENUATION_DENOMINATOR)

    assert m1_ratio == Fraction(1, 3)
    assert m2_ratio == Fraction(5, 18)
    assert declared == min(m1_ratio, m2_ratio)

    exact = Fraction(M3_LOW_ENERGY_AMPLITUDE).limit_denominator(10**6) * declared
    assert exact == Fraction(11, 180)
    # Bound as the binary64 nearest the exact rational, not the left-to-right
    # product, which rounds one ulp higher.
    assert COMBINED_M3_AMPLITUDE == 11 / 180
    assert COMBINED_M3_AMPLITUDE.hex() == "0x1.f49f49f49f49fp-5"
    assert COMBINED_M3_AMPLITUDE != M3_LOW_ENERGY_AMPLITUDE * (5 / 18)


def test_f16_m3_reuses_the_f15_mechanism_apart_from_amplitude(coordinates):
    """Same covariate, form, direction and clip window; amplitude only differs."""
    _, descriptor = coordinates
    f15 = np.clip(1 - M3_LOW_ENERGY_AMPLITUDE * descriptor, *M3_CEILING_CLIP)
    f16 = np.clip(1 - COMBINED_M3_AMPLITUDE * descriptor, *M3_CEILING_CLIP)

    assert M3_CEILING_CLIP == (0.6, 0.99)
    assert np.all(f16 <= 1.0) and np.all(f15 <= 1.0)          # same downward direction
    assert np.all(f16 >= f15)                                  # strictly milder deviation
    assert f16.min() > f15.min()


def test_generated_f16_case_carries_non_neutral_m1_m2_and_m3_parameters():
    """Recompute the three deviation parameters for a real generated F16 case."""
    generated = generate_case("PB|development|F16|r000")
    compounds = generated.inputs.compounds
    mu_inf = float(generated.truth.phi["mu_inf"])

    shape = 1 + COMBINED_M1_AMPLITUDE * np.tanh(compounds.descriptor.to_numpy())
    floor = np.clip(mu_inf + COMBINED_M2_AMPLITUDE * (compounds.descriptor2.to_numpy() - 0.5), 0.03, 0.55)
    ceiling = np.clip(1 - COMBINED_M3_AMPLITUDE * compounds.descriptor.to_numpy(), *M3_CEILING_CLIP)

    assert np.any(shape != 1.0), "M1 deviation absent"
    assert np.any(floor != mu_inf), "M2 deviation absent"
    assert np.any(ceiling != 1.0), "M3 deviation absent"
    # The M3 component must be present for a substantial majority of compounds,
    # not a numerical rounding artefact on a handful.
    assert (ceiling < 1.0).mean() > 0.9


# --------------------------------------------------------------------------
# 6-7: truth metadata and endpoint applicability
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case_id",
    ["PB|development|F16|r000", "PB|held_out|F16|r000", "PB|held_out|F16|r011", "PB|challenge|F16|r002"],
)
def test_f16_truth_marks_all_three_components_present(case_id):
    truth = generate_case(case_id).truth

    assert truth.family == "F16"
    assert truth.m0_adequacy_truth == "M1+M2+M3"
    assert set(truth.m0_adequacy_truth.split("+")) == {"M1", "M2", "M3"}
    assert truth.scalar_truth_defined is False
    assert truth.symbolic_truth_kind == "none"


@pytest.mark.parametrize(
    "case_id",
    ["PB|development|F16|r000", "PB|held_out|F16|r000", "PB|held_out|F16|r011", "PB|challenge|F16|r002"],
)
def test_f16_remains_applicable_to_all_three_sensitivity_endpoints(case_id):
    truth = generate_case(case_id).truth
    _, variant, _ = resolve_case_id(case_id)

    assert truth.applicable_endpoints == ["m1_sensitivity", "m2_sensitivity", "m3_sensitivity"]
    assert variant.endpoint_names == frozenset({"m1_sensitivity", "m2_sensitivity", "m3_sensitivity"})


# --------------------------------------------------------------------------
# 8-9: frozen denominators and case counts
# --------------------------------------------------------------------------


def test_sensitivity_denominators_remain_36_24_24():
    assert endpoint_denominator("m1_sensitivity") == 36
    assert endpoint_denominator("m2_sensitivity") == 24
    assert endpoint_denominator("m3_sensitivity") == 24
    assert endpoint_denominator("m0_specificity") == 164


def test_f16_case_counts_are_unchanged():
    f16 = next(family for family in CASE_FAMILIES if family.code == "F16")

    assert dict(f16.partition_counts) == PARTITION_CASE_COUNTS
    assert f16.partition_counts == {"development": 4, "held_out": 12, "challenge": 3}
    assert f16.held_out_cases_for("m1_sensitivity") == 12
    assert f16.held_out_cases_for("m2_sensitivity") == 12
    assert f16.held_out_cases_for("m3_sensitivity") == 12
    assert len(CASE_FAMILIES) == 20


def test_generator_version_constant_is_deliberately_unchanged():
    """Bumping it would rehash all 380 cases and break non-F16 immutability."""
    assert GENERATOR_VERSION == "paper-benchmark-generator-1.0.0"
