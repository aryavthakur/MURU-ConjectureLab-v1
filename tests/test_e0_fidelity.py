"""E0 fidelity gates.  Every test here is a fail-closed condition of the study.

Covers `MURU_V2_E0_PROTOCOL.md` section 6: generator identity, fitter identity,
instrumentation identity, namespace disjointness, and the no-symbolic-search
guarantee.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark import generator as G
from muru.paper_benchmark import rc5_adequacy as rc5
from muru.paper_benchmark.adequacy import MU_CEIL as V1_MU_CEIL
from muru.paper_benchmark.rc5_estimate import fit_case_phi
from muru.v2_calibration import e0_cells
from muru.v2_calibration.e0_instrument import (
    InstrumentationDrift,
    PySRImportBlocked,
    assert_pysr_absent,
    block_pysr_imports,
    mu_ceil_injected,
    run_case_adequacy_instrumented,
)
from muru.v2_calibration.e0_seeds import (
    BENCHMARK_SEED_PREFIX,
    V2_SEED_PREFIX,
    assert_namespace_disjoint,
    derive_v2_seed,
    e0_seed,
    e0_world_id,
)
from muru.v2_calibration.e0_worlds import build_case_inputs, draw_base, render

#: The five v1 G1 variants that share E0's declared generative configuration
#: (`MURU_V2_E0_PROTOCOL.md` section 2).
MATCHED_V1_VARIANTS = ("F05", "F08", "F11", "F12", "F17")


# ---------------------------------------------------------------------------
# Gate 1: generator identity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variant", MATCHED_V1_VARIANTS)
@pytest.mark.parametrize("replicate", [0, 5, 11])
def test_e0_builder_reproduces_frozen_generator_exactly(variant, replicate):
    """Driven with v1's seeds and v1's ceiling, the builder must *be* v1."""
    case_id = f"PB|held_out|{variant}|r{replicate:03d}"
    expected = G.generate_case(case_id)
    compounds, trajectories, _ = build_case_inputs(
        lambda stage: G.derive_seed(case_id, stage), response_ceiling=V1_MU_CEIL
    )
    pd.testing.assert_frame_equal(expected.inputs.compounds, compounds)
    pd.testing.assert_frame_equal(expected.inputs.trajectories, trajectories)


def test_generator_ceiling_is_the_only_injected_difference():
    """Changing the ceiling changes the response and nothing else."""
    case_id = "PB|held_out|F08|r000"
    seed_for = lambda stage: G.derive_seed(case_id, stage)  # noqa: E731
    c_v1, t_v1, d_v1 = build_case_inputs(seed_for, response_ceiling=V1_MU_CEIL)
    c_lo, t_lo, d_lo = build_case_inputs(seed_for, response_ceiling=1 - 1e-3)
    c_no, t_no, d_no = build_case_inputs(seed_for, response_ceiling=None)

    pd.testing.assert_frame_equal(c_v1, c_lo)
    pd.testing.assert_frame_equal(c_v1, c_no)
    for other in (d_lo, d_no):
        assert np.array_equal(d_v1["mu_preclip"], other["mu_preclip"])
        assert np.array_equal(d_v1["noise"], other["noise"])
        assert np.array_equal(d_v1["g"], other["g"])
        assert (d_v1["mu_inf"], d_v1["phi_p"]) == (other["mu_inf"], other["phi_p"])

    assert (t_v1["mu"].to_numpy() <= V1_MU_CEIL + 0.0).all()
    assert (t_lo["mu"].to_numpy() <= 1 - 1e-3 + 0.0).all()
    assert t_no["mu"].to_numpy().max() == pytest.approx(d_v1["mu_preclip"].max())


# ---------------------------------------------------------------------------
# Gate 2: shared draws across cells
# ---------------------------------------------------------------------------

def test_all_nine_cells_share_one_draw():
    """The seed stream cannot see the cell, so the nine cells are paired."""
    base = draw_base(3, e0_seed)
    rendered = [
        render(base, cell.cell_id, e0_world_id(cell.cell_id, 3), cell.generator_clip)
        for cell in e0_cells.CELLS
    ]
    assert len({w.base_fingerprint for w in rendered}) == 1
    for world in rendered:
        pd.testing.assert_frame_equal(base.compounds, world.compounds)

    # Nine separately identified worlds ...
    assert len({w.world_id for w in rendered}) == 9
    assert len({w.content_hash for w in rendered}) == 9
    # ... whose responses differ only where the generator clip differs.  Three
    # clip levels, so exactly three distinct response matrices.
    by_clip: dict[object, list] = {}
    for cell, world in zip(e0_cells.CELLS, rendered):
        by_clip.setdefault(cell.generator_clip, []).append(world)
    assert len(by_clip) == 3
    for group in by_clip.values():
        for world in group[1:]:
            assert np.array_equal(group[0].mu, world.mu)
            pd.testing.assert_frame_equal(group[0].trajectories, world.trajectories)


def test_seed_function_has_no_cell_argument():
    """Structural guarantee, not a promise: `e0_seed(replicate, stage)` only."""
    import inspect

    assert list(inspect.signature(e0_seed).parameters) == ["replicate", "stage"]


# ---------------------------------------------------------------------------
# Gate 3: namespace disjointness
# ---------------------------------------------------------------------------

def test_namespace_is_disjoint_from_the_benchmark():
    report = assert_namespace_disjoint()
    assert report["disjoint"] is True
    assert V2_SEED_PREFIX != BENCHMARK_SEED_PREFIX
    assert derive_v2_seed("E0", "r000", "compounds") != G.derive_seed("E0", "r000", "compounds")


def test_no_e0_world_content_hash_collides_with_a_benchmark_case():
    benchmark = {G.generate_case(f"PB|held_out|{v}|r{r:03d}").content_hash
                 for v in MATCHED_V1_VARIANTS for r in range(3)}
    base = draw_base(0, e0_seed)
    v2 = {render(base, c.cell_id, e0_world_id(c.cell_id, 0), c.generator_clip).content_hash
          for c in e0_cells.CELLS}
    assert benchmark.isdisjoint(v2)


# ---------------------------------------------------------------------------
# Gate 4: fitter identity and ceiling injection
# ---------------------------------------------------------------------------

def test_mu_ceil_injection_reaches_every_consumer_and_restores():
    assert rc5.MU_CEIL == V1_MU_CEIL
    with mu_ceil_injected(1.0 + 1e-2):
        assert rc5.MU_CEIL == 1.0 + 1e-2
        with pytest.raises(InstrumentationDrift):
            with mu_ceil_injected(1 - 1e-3):
                pass
    assert rc5.MU_CEIL == V1_MU_CEIL

    with pytest.raises(ValueError):
        with mu_ceil_injected(1 - 1e-3):
            raise ValueError("body raised")
    assert rc5.MU_CEIL == V1_MU_CEIL


def test_injected_ceiling_moves_the_m3_bound_and_the_usability_test():
    base = draw_base(0, e0_seed)
    world = render(base, "probe", e0_world_id("probe", 0), V1_MU_CEIL)
    shape = rc5.ProfileShape.from_phi(fit_case_phi(world.compounds, world.trajectories))
    sub = world.trajectories[world.trajectories.compound_id == world.compounds.compound_id.iloc[-1]]
    e, y = sub.energy.to_numpy()[:5], sub.mu.to_numpy()[:5]

    tight = rc5.fit_model("M3", shape, e, y)
    with mu_ceil_injected(1.0 + 1e-2):
        opened = rc5.fit_model("M3", shape, e, y)
    assert tight.params["low_energy_plateau"] <= V1_MU_CEIL
    assert opened.params["low_energy_plateau"] >= tight.params["low_energy_plateau"]


# ---------------------------------------------------------------------------
# Gate 5: instrumentation identity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cell", e0_cells.CELLS, ids=[c.cell_id for c in e0_cells.CELLS])
def test_instrumented_run_equals_frozen_run_on_fresh_worlds(cell):
    """The recorder observes; it does not change the verdict, in any cell."""
    base = draw_base(1, e0_seed)
    world = render(base, cell.cell_id, e0_world_id(cell.cell_id, 1), cell.generator_clip)
    phi = fit_case_phi(world.compounds, world.trajectories)

    with mu_ceil_injected(cell.fitter_mu_ceil):
        frozen = rc5.run_case_adequacy(world.world_id, world.compounds, world.trajectories, phi)
        instrumented, fits, contrasts = run_case_adequacy_instrumented(
            world.world_id, world.compounds, world.trajectories, phi
        )

    assert frozen.status is instrumented.status
    assert frozen.fired == instrumented.fired
    for detector in ("M1", "M2", "M3"):
        a, b = frozen.contrasts[detector], instrumented.contrasts[detector]
        assert (a.evaluable, a.practical_wins, a.fired) == (b.evaluable, b.practical_wins, b.fired)
        assert dict(a.status_counts) == dict(b.status_counts)
    assert len(fits) == 3 * 30 * 6 * 2
    assert len(contrasts) == 3 * 30


@pytest.mark.parametrize("case_id", ["PB|held_out|F08|r000", "PB|held_out|F17|r003"])
def test_instrumented_run_equals_frozen_run_on_v1_shaped_inputs(case_id):
    """Declared in protocol section 6.2: a code-identity regression only.

    Held-out inputs are used here to prove the instrumented code path is the
    frozen one on v1-shaped data.  No value computed here reaches an E0 world,
    an E0 parameter, or the E0 decision.
    """
    case = G.generate_case(case_id)
    phi = fit_case_phi(case.inputs.compounds, case.inputs.trajectories)
    frozen = rc5.run_case_adequacy(case_id, case.inputs.compounds, case.inputs.trajectories, phi)
    instrumented, _, _ = run_case_adequacy_instrumented(
        case_id, case.inputs.compounds, case.inputs.trajectories, phi
    )
    assert frozen.status is instrumented.status
    for detector in ("M1", "M2", "M3"):
        assert dict(frozen.contrasts[detector].status_counts) == dict(
            instrumented.contrasts[detector].status_counts
        )


# ---------------------------------------------------------------------------
# Gate 6: no symbolic search
# ---------------------------------------------------------------------------

def test_pysr_import_is_blocked_during_a_run():
    with block_pysr_imports():
        with pytest.raises(PySRImportBlocked):
            __import__("pysr")


def test_e0_modules_do_not_import_pysr():
    for name in list(sys.modules):
        if name.split(".")[0] == "pysr":
            del sys.modules[name]
    import importlib

    for module in ("e0_seeds", "e0_worlds", "e0_cells", "e0_instrument", "e0_analysis"):
        importlib.import_module(f"muru.v2_calibration.{module}")
    assert_pysr_absent()
