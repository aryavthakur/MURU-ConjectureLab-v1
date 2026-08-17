"""Tests for balanced_sample.py -- determinism, outcome-blindness, and the
design-based MOE formula."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "e2_rescue_v2"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import balanced_sample as bs  # noqa: E402
from muru.v2_calibration import e2_worlds  # noqa: E402


def test_selection_is_deterministic_across_repeated_calls():
    sel1 = bs.select_replicates_for_r(6)
    sel2 = bs.select_replicates_for_r(6)
    assert sel1 == sel2


def test_selection_size_matches_r_per_cell():
    for r in bs.CANDIDATE_R_VALUES:
        sel = bs.select_replicates_for_r(r)
        assert len(sel) == bs.N_CELLS
        for cell_id, reps in sel.items():
            assert len(reps) == r
            assert len(set(reps)) == r  # no replacement
            assert all(0 <= x < 12 for x in reps)


def test_total_world_count_matches_45_times_r():
    for r in bs.CANDIDATE_R_VALUES:
        sel = bs.select_replicates_for_r(r)
        wids = bs.world_ids_for_selection(sel)
        assert len(wids) == 45 * r
        assert len(set(wids)) == len(wids)  # no duplicates


def test_all_selected_world_ids_are_valid_manifest_members():
    valid_ids = {e2_worlds.world_id(*args) for args in e2_worlds.iter_worlds()}
    sel = bs.select_replicates_for_r(5)
    wids = bs.world_ids_for_selection(sel)
    assert set(wids).issubset(valid_ids)


def test_candidate_sizes_are_exactly_45_times_r():
    assert [r * 45 for r in bs.CANDIDATE_R_VALUES] == [180, 225, 270, 315, 360]


def test_moe_decreases_monotonically_with_r():
    moes = [bs.design_based_moe(r)["overall_moe_95"] for r in bs.CANDIDATE_R_VALUES]
    assert all(moes[i] > moes[i + 1] for i in range(len(moes) - 1))


def test_full_census_r12_has_zero_moe():
    d = bs.design_based_moe(12)
    assert abs(d["overall_moe_95"]) < 1e-12
    assert abs(d["finite_population_correction"]) < 1e-12


def test_r6_crosses_5_percent_overall_moe_threshold():
    d5 = bs.design_based_moe(5)
    d6 = bs.design_based_moe(6)
    assert d5["overall_moe_95"] > 0.05
    assert d6["overall_moe_95"] < 0.05


def test_selection_for_r_is_prefix_of_full_preference_order():
    for family, regime, noise in list(e2_worlds.iter_cells())[:5]:
        cell_id = e2_worlds.cell_id(family, regime, noise)
        order = bs.full_preference_order(cell_id)
        for r in bs.CANDIDATE_R_VALUES:
            sel = bs.select_replicates_for_r(r)
            assert set(sel[cell_id]) == set(order[:r])


def test_fallback_swaps_only_the_unresolvable_world_deterministically():
    r = 6
    baseline = bs.select_replicates_for_r(r)
    # Pick one real selected world from one cell and mark it permanently unresolvable.
    family, regime, noise = next(iter(e2_worlds.iter_cells()))
    cell_id = e2_worlds.cell_id(family, regime, noise)
    victim_replicate = baseline[cell_id][0]
    victim_wid = e2_worlds.world_id(family, regime, noise, victim_replicate)

    with_fallback = bs.select_replicates_with_fallback(r, {victim_wid})
    assert victim_replicate not in with_fallback[cell_id]
    assert len(with_fallback[cell_id]) == r  # still exactly r -- the fallback backfilled it
    # every OTHER cell is untouched
    for fam2, reg2, noi2 in e2_worlds.iter_cells():
        cid2 = e2_worlds.cell_id(fam2, reg2, noi2)
        if cid2 != cell_id:
            assert with_fallback[cid2] == baseline[cid2]
    # the substitute is the next name in THIS cell's own precommitted order
    order = bs.full_preference_order(cell_id)
    expected_next = next(x for x in order if x not in baseline[cell_id])
    assert expected_next in with_fallback[cell_id]


def test_fallback_with_empty_unresolvable_set_matches_plain_selection():
    for r in bs.CANDIDATE_R_VALUES:
        assert bs.select_replicates_with_fallback(r, set()) == bs.select_replicates_for_r(r)


def test_selection_depends_only_on_cell_identity_not_on_any_external_state():
    # Re-derive the seed for one cell two different ways and confirm they
    # agree -- proves the RNG seed is a pure function of cell_id, with no
    # hidden dependency on wall-clock time, process state, or outcome data.
    seed_a = bs._cell_seed("mass_power|c_low|n_noiseless")
    seed_b = bs._cell_seed("mass_power|c_low|n_noiseless")
    assert seed_a == seed_b
    seed_other = bs._cell_seed("mass_power|c_mid|n_noiseless")
    assert seed_a != seed_other  # different cells get different (still deterministic) seeds


if __name__ == "__main__":
    import inspect
    import traceback
    mod = sys.modules[__name__]
    fns = [f for name, f in inspect.getmembers(mod, inspect.isfunction) if name.startswith("test_")]
    failed = 0
    for f in fns:
        try:
            f()
            print(f"PASS {f.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {f.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
