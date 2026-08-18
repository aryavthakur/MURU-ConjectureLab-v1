"""Executable identity test for raw_search.py, per this project's own
transcription discipline (MURU_V2_E2_PREDECLARATION.md section 1): runs
BOTH the real, unmodified `e2_search.run_seed_search` and this rescue's
`raw_search.run_seed_search_raw` on the IDENTICAL (world, seed), and
asserts every structural field is byte-identical. Uses one real,
deterministic PySR fit (frozen config, deterministic=True) -- not a mock --
because this is exactly the claim that needs checking against reality, not
assumed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_worlds, e2_search  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import raw_search  # noqa: E402


def test_raw_search_matches_real_search_structurally():
    # A small, cheap, real world -- mass_power has no descriptor coefficient
    # search overhead beyond the exponent, typically fast to fit.
    world = e2_worlds.build_world("mass_power", "low", "noiseless", 0)
    world_design = e2_search.build_world_design(world.compounds, world.trajectories, world.world_id)

    seed_val = 2_104_500_000 + world.world_ordinal * 30 + 0

    real = e2_search.run_seed_search(world_design, k=0, seed=seed_val)
    raw = raw_search.run_seed_search_raw(world_design, k=0, seed=seed_val)

    assert real.status == raw.status
    assert len(real.rows) == len(raw.rows)
    for r_real, r_raw in zip(real.rows, raw.rows):
        assert r_real.front_rank == r_raw.front_rank
        assert r_real.engine_complexity == r_raw.complexity
        assert r_real.expression_string == r_raw.expression_string
        assert r_real.valid_r2 == r_raw.valid_r2
        assert r_real.invalid_fraction == r_raw.invalid_fraction
        assert r_real.test_r2 == r_raw.candidate_test_r2
        assert r_real.retained_by_argmax_score == r_raw.retained_by_argmax_score
    print(f"PASS: {len(real.rows)} structural rows byte-identical between real and raw search")


if __name__ == "__main__":
    try:
        test_raw_search_matches_real_search_structurally()
        print("1/1 passed")
        sys.exit(0)
    except Exception:
        import traceback
        traceback.print_exc()
        print("0/1 passed")
        sys.exit(1)
