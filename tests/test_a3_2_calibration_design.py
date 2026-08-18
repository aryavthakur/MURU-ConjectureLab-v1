"""Amendment A3.2: base-target permutation and the 18/6/6 scaffold split.

Every world here is a calibration world, built only from the NCAL
namespace.  No test touches any sealed or held-back case partition, and no
test executes a symbolic search.

The partition names are deliberately not spelled out anywhere in this file:
the contamination audit scans raw text, as it should, and prose naming a
partition is indistinguishable to a grep from code reaching one.  Where a
test needs those names it imports them from the frozen registry.

Covers the proof obligations A3.2 states for both decisions.
"""
from __future__ import annotations

import inspect
import json

import numpy as np
import pytest

from muru.paper_benchmark.calibration_contract import (
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
    N_CALIBRATION_WORLDS,
    N_COMPOUNDS,
    N_SCAFFOLD_GROUPS,
    all_world_ids,
    derive_calibration_seeds,
)
from muru.paper_benchmark.generator import _synthetic_compounds, derive_seed
from muru.paper_benchmark import rc3_calibration_worlds as worlds_mod
from muru.paper_benchmark.rc3_calibration_worlds import (
    BASE_TARGET_ALGORITHM,
    BASE_TARGET_SEED_NAMESPACE,
    CALIBRATION_SCAFFOLD_COUNTS,
    COMPOUNDS_PER_SCAFFOLD,
    EXPECTED_SPLIT_COUNTS,
    SPLIT_ALGORITHM,
    SPLIT_ORDER,
    SPLIT_SEED_NAMESPACE,
    ExcludedConstructionError,
    ScaffoldGeometryError,
    assign_calibration_split,
    build_world,
    frozen_law_target,
)

CONSTRUCTIONS = tuple(CONSTRUCTION_ALLOCATION)


def sample_worlds(n: int = 6):
    for construction in CONSTRUCTIONS:
        for index in range(n):
            yield build_world(construction, index)


# =======================================================================
# DECISION 1 - base target
# =======================================================================

# --- A. exact multiset equality -----------------------------------------

@pytest.mark.parametrize("construction", CONSTRUCTIONS)
@pytest.mark.parametrize("index", [0, 1, 7])
def test_A_permuted_target_is_an_exact_multiset_of_the_frozen_law(construction, index):
    """The marginal distribution is preserved value for value."""
    world_id = f"PB|NCAL|{construction}|r{index:03d}"
    compounds, _ = _synthetic_compounds(world_id)
    law = frozen_law_target(world_id, compounds)
    base = worlds_mod._base_target(world_id, compounds, worlds_mod.BASE_TARGET_KIND)

    assert np.array_equal(np.sort(law), np.sort(base))
    # bitwise, not merely close: no numerical alteration is permitted
    assert np.sort(law).tobytes() == np.sort(base).tobytes()


def test_A_permutation_actually_reorders():
    """A permutation that changed nothing would preserve the defect."""
    reordered = 0
    for construction in CONSTRUCTIONS:
        for index in range(5):
            world_id = f"PB|NCAL|{construction}|r{index:03d}"
            compounds, _ = _synthetic_compounds(world_id)
            law = frozen_law_target(world_id, compounds)
            base = worlds_mod._base_target(world_id, compounds, worlds_mod.BASE_TARGET_KIND)
            if not np.array_equal(law, base):
                reordered += 1
    assert reordered == 15


# --- E. nothing duplicated or lost --------------------------------------

@pytest.mark.parametrize("construction", CONSTRUCTIONS)
def test_E_no_value_duplicated_or_lost(construction):
    world_id = f"PB|NCAL|{construction}|r000"
    compounds, _ = _synthetic_compounds(world_id)
    law = frozen_law_target(world_id, compounds)
    base = worlds_mod._base_target(world_id, compounds, worlds_mod.BASE_TARGET_KIND)

    assert len(base) == len(law) == N_COMPOUNDS
    assert sorted(base.tolist()) == sorted(law.tolist())
    # multiplicity preserved, not just the value set
    from collections import Counter
    assert Counter(base.tolist()) == Counter(law.tolist())
    assert float(base.sum()) == pytest.approx(float(law.sum()), rel=0, abs=1e-12)


def test_E_no_numerical_alteration():
    """Every permuted value is bit-identical to some frozen-law value."""
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    law = frozen_law_target(world_id, compounds)
    base = worlds_mod._base_target(world_id, compounds, worlds_mod.BASE_TARGET_KIND)
    law_bits = {v.tobytes() for v in law}
    assert all(v.tobytes() in law_bits for v in base)


# --- B. deterministic same-world reproducibility -------------------------

@pytest.mark.parametrize("construction", CONSTRUCTIONS)
def test_B_same_world_reproduces_bitwise(construction):
    a = build_world(construction, 2)
    b = build_world(construction, 2)
    assert a.target.tobytes() == b.target.tobytes()
    assert a.compounds.equals(b.compounds)
    assert a.seeds == b.seeds
    assert np.array_equal(a.compounds["split"], b.compounds["split"])


# --- C. independent per-world seeds --------------------------------------

def test_C_every_world_has_a_distinct_base_target_seed():
    seeds = {
        wid: derive_seed(wid, BASE_TARGET_SEED_NAMESPACE) for wid in all_world_ids()
    }
    assert len(set(seeds.values())) == N_CALIBRATION_WORLDS


def test_C_base_target_seed_uses_the_canonical_api_and_namespace():
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    expected = derive_seed(world_id, "BASE_TARGET")
    assert BASE_TARGET_SEED_NAMESPACE == "BASE_TARGET"
    assert derive_seed(world_id, BASE_TARGET_SEED_NAMESPACE) == expected

    compounds, _ = _synthetic_compounds(world_id)
    law = frozen_law_target(world_id, compounds)
    expected_target = law[np.random.default_rng(expected).permutation(len(law))]
    actual = worlds_mod._base_target(world_id, compounds, worlds_mod.BASE_TARGET_KIND)
    assert np.array_equal(expected_target, actual)


def test_C_different_worlds_permute_differently():
    a_id = "PB|NCAL|target_permuted_across_compounds|r000"
    b_id = "PB|NCAL|target_permuted_across_compounds|r001"
    ca, _ = _synthetic_compounds(a_id)
    order_a = np.random.default_rng(derive_seed(a_id, BASE_TARGET_SEED_NAMESPACE)).permutation(N_COMPOUNDS)
    order_b = np.random.default_rng(derive_seed(b_id, BASE_TARGET_SEED_NAMESPACE)).permutation(N_COMPOUNDS)
    assert not np.array_equal(order_a, order_b)


# --- 7. seed independence ------------------------------------------------

def test_seed_namespaces_are_mutually_independent():
    """Base-target, split, null-family, law and search seeds must not coincide."""
    for wid in list(all_world_ids())[:20]:
        derived = {
            "base_target": derive_seed(wid, BASE_TARGET_SEED_NAMESPACE),
            "split": derive_seed(wid, SPLIT_SEED_NAMESPACE),
            "null_construction": derive_seed(wid, "null_construction"),
            "law": derive_seed(wid, "law"),
        }
        assert len(set(derived.values())) == 4, wid
        # and none collides with any PySR search seed for that world
        assert not set(derived.values()) & set(derive_calibration_seeds(wid))


def test_base_target_seed_is_not_a_smoke_or_bootstrap_seed():
    from muru.paper_benchmark.calibration_contract import BOOTSTRAP_SEED
    from muru.paper_benchmark.rc3_provenance import smoke_seed

    smoke = {smoke_seed(w, k) for w in range(20) for k in range(20)}
    for wid in list(all_world_ids())[:20]:
        seed = derive_seed(wid, BASE_TARGET_SEED_NAMESPACE)
        assert seed not in smoke
        assert seed != BOOTSTRAP_SEED


# --- D. the permutation consults nothing ---------------------------------

def test_D_the_reassignment_step_consults_nothing():
    """The permutation order is a function of world_id alone.

    The frozen law itself reads mass and descriptor - that is the frozen
    law's business, and A3.2 leaves it unchanged. What A3.2 constrains is the
    *reassignment*: that step must not condition on descriptors, scaffold,
    mass, split, or search output. So the invariant tested here is that the
    same index permutation is applied whatever the frame contains.
    """
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    order = np.random.default_rng(
        derive_seed(world_id, BASE_TARGET_SEED_NAMESPACE)
    ).permutation(N_COMPOUNDS)

    scrambled = compounds.copy()
    rng = np.random.default_rng(999)
    for column in ("mass", "descriptor", "descriptor2",
                   "distractor", "correlated_distractor"):
        scrambled[column] = np.abs(rng.normal(size=len(scrambled))) + 1.0
    scrambled["scaffold_id"] = ["Z%02d" % (i % 30) for i in range(len(scrambled))]
    scrambled["split"] = ["test"] * len(scrambled)

    for frame in (compounds, scrambled):
        law = frozen_law_target(world_id, frame)
        base = worlds_mod._base_target(world_id, frame, worlds_mod.BASE_TARGET_KIND)
        # the very same index permutation, regardless of frame content
        assert np.array_equal(base, law[order])


def test_D_permutation_order_depends_only_on_world_id():
    """The permutation index array is built from the seed alone."""
    source = inspect.getsource(worlds_mod._base_target)
    # the only rng call is a permutation over a length, not over data
    assert "rng.permutation(len(values))" in source
    assert "sort" not in source
    assert "argsort" not in source


def test_D_base_target_precedes_the_split_assignment():
    """A3.2 point 6: reassignment happens before any partition use."""
    source = inspect.getsource(worlds_mod.build_world)
    assert source.index("_base_target(") < source.index("assign_calibration_split(")


def test_D_base_target_precedes_the_null_transformation():
    source = inspect.getsource(worlds_mod.build_world)
    assert source.index("_base_target(") < source.index("null_construction")


# --- F. cannot reach the sealed generators -------------------------------

FORBIDDEN = ("generate_partition", "iter_case_ids", "resolve_case_id", "generate_case")


def test_F_world_module_cannot_reach_partitioned_case_generators():
    assert not set(FORBIDDEN) & set(vars(worlds_mod))
    source = inspect.getsource(worlds_mod)
    for name in FORBIDDEN:
        assert name not in source


def test_F_world_ids_are_always_the_ncal_namespace():
    """No calibration world id can name a real case partition.

    The partition names come from the frozen registry rather than string
    literals, so this stays true if the registry ever changes.
    """
    from muru.paper_benchmark.registry import PARTITIONS

    for wid in all_world_ids():
        assert wid.startswith("PB|NCAL|")
        for partition in PARTITIONS:
            assert f"|{partition}|" not in wid


# --- G. provenance records the algorithm identity ------------------------

def test_G_provenance_binds_the_a3_2_identities():
    from muru.paper_benchmark.rc3_provenance import a3_2_world_construction

    record = a3_2_world_construction()
    assert record["amendment"] == "A3.2"
    assert record["base_target_algorithm"] == BASE_TARGET_ALGORITHM
    assert record["base_target_seed_namespace"] == "PB|NCAL|<world_id>|BASE_TARGET"
    assert record["split_algorithm"] == SPLIT_ALGORITHM
    assert record["split_seed_namespace"] == "PB|NCAL|<world_id>|SPLIT"
    assert record["canonical_seed_api"].endswith("generator.derive_seed")
    assert record["scaffold_counts"] == {"train": 18, "validation": 6, "test": 6}
    assert record["compound_counts"] == {"train": 108, "validation": 36, "test": 36}


def test_G_manifest_and_run_result_carry_the_identity():
    from muru.paper_benchmark.rc3_calibration_runner import CalibrationRunResult
    from muru.paper_benchmark.rc3_provenance import build_provenance_manifest

    payload = build_provenance_manifest(strict=True).to_payload()
    assert payload["world_construction"]["base_target_algorithm"] == BASE_TARGET_ALGORITHM
    json.dumps(payload)  # must stay serializable

    result = CalibrationRunResult(
        validity=None, failed_worlds=0, clean_worlds=0,
        world_statistics={}, thresholds=None, bootstrap=None,
    )
    assert result.world_construction["split_algorithm"] == SPLIT_ALGORITHM


# =======================================================================
# DECISION 2 - scaffold split
# =======================================================================

# --- A. exactly 18/6/6 scaffold groups -----------------------------------

@pytest.mark.parametrize("construction", CONSTRUCTIONS)
@pytest.mark.parametrize("index", [0, 3, 11])
def test_A_scaffold_counts_are_eighteen_six_six(construction, index):
    world = build_world(construction, index)
    per_split = world.compounds.groupby("split")["scaffold_id"].nunique().to_dict()
    assert per_split == {"train": 18, "validation": 6, "test": 6}
    assert sum(per_split.values()) == N_SCAFFOLD_GROUPS


# --- B. exactly 108/36/36 compounds --------------------------------------

@pytest.mark.parametrize("construction", CONSTRUCTIONS)
@pytest.mark.parametrize("index", [0, 3, 11])
def test_B_compound_counts_are_one_hundred_eight_thirty_six_thirty_six(construction, index):
    world = build_world(construction, index)
    counts = world.compounds["split"].value_counts().to_dict()
    assert counts == {"train": 108, "validation": 36, "test": 36}
    assert counts == EXPECTED_SPLIT_COUNTS
    assert sum(counts.values()) == N_COMPOUNDS


def test_B_follows_from_six_compounds_per_scaffold():
    assert COMPOUNDS_PER_SCAFFOLD == 6
    for name, scaffolds in CALIBRATION_SCAFFOLD_COUNTS.items():
        assert EXPECTED_SPLIT_COUNTS[name] == scaffolds * COMPOUNDS_PER_SCAFFOLD


def test_B_the_frozen_generator_really_has_thirty_equal_scaffolds():
    """The assumption A3.2 Decision 2 point 7 makes conditional."""
    for wid in list(all_world_ids())[:10]:
        compounds, _ = _synthetic_compounds(wid)
        sizes = compounds["scaffold_id"].value_counts()
        assert len(sizes) == N_SCAFFOLD_GROUPS == 30
        assert set(sizes.to_dict().values()) == {6}


# --- C. zero scaffold overlap --------------------------------------------

def test_C_no_scaffold_appears_in_two_partitions():
    for world in sample_worlds(4):
        groups = world.compounds.groupby("scaffold_id")["split"].nunique()
        assert groups.max() == 1, world.world_id

        sets = {
            name: set(world.compounds.loc[world.compounds["split"] == name, "scaffold_id"])
            for name in SPLIT_ORDER
        }
        assert sets["train"] & sets["validation"] == set()
        assert sets["train"] & sets["test"] == set()
        assert sets["validation"] & sets["test"] == set()
        assert len(sets["train"] | sets["validation"] | sets["test"]) == N_SCAFFOLD_GROUPS


# --- D. deterministic same-seed assignment -------------------------------

def test_D_split_is_deterministic():
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    a = assign_calibration_split(world_id, compounds)
    b = assign_calibration_split(world_id, compounds)
    assert np.array_equal(a, b)


def test_D_split_is_independent_of_row_order():
    """Shuffled rows must give each compound the same partition."""
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    straight = dict(zip(compounds["compound_id"],
                        assign_calibration_split(world_id, compounds)))

    shuffled = compounds.sample(frac=1.0, random_state=5).reset_index(drop=True)
    mixed = dict(zip(shuffled["compound_id"],
                     assign_calibration_split(world_id, shuffled)))
    assert straight == mixed


# --- E. a different split seed moves assignment, not counts --------------

def test_E_a_different_world_moves_assignment_but_not_counts():
    a = build_world("target_permuted_across_compounds", 0)
    b = build_world("target_permuted_across_compounds", 1)

    counts_a = a.compounds["split"].value_counts().to_dict()
    counts_b = b.compounds["split"].value_counts().to_dict()
    assert counts_a == counts_b == EXPECTED_SPLIT_COUNTS

    train_a = set(a.compounds.loc[a.compounds["split"] == "train", "scaffold_id"])
    train_b = set(b.compounds.loc[b.compounds["split"] == "train", "scaffold_id"])
    assert train_a != train_b


def test_E_split_differs_from_the_frozen_generator_column():
    """The calibration split replaces, not echoes, the 20/5/5 column."""
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    frozen_counts = compounds["split"].value_counts().to_dict()
    assert frozen_counts == {"train": 120, "validation": 30, "test": 30}

    replaced = assign_calibration_split(world_id, compounds)
    import collections
    assert dict(collections.Counter(replaced)) == EXPECTED_SPLIT_COUNTS


# --- F. the split consults nothing but scaffold identity -----------------

def test_F_split_ignores_targets_descriptors_mass_and_the_frozen_column():
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    baseline = assign_calibration_split(world_id, compounds)

    scrambled = compounds.copy()
    rng = np.random.default_rng(4242)
    for column in ("mass", "descriptor", "descriptor2",
                   "distractor", "correlated_distractor"):
        scrambled[column] = rng.normal(size=len(scrambled))
    scrambled["split"] = "train"

    assert np.array_equal(baseline, assign_calibration_split(world_id, scrambled))


def test_F_split_source_never_reads_a_value_column():
    """Check the executable body, not the prose that describes it."""
    source = inspect.getsource(assign_calibration_split)
    # everything after the docstring's closing quotes is executable code
    body = source.split('"""')[2]
    for column in ("mass", "descriptor", "distractor", "target"):
        assert column not in body, column
    assert "scaffold_id" in body


# --- 7. STOP rather than approximate -------------------------------------

def test_wrong_scaffold_count_stops_instead_of_approximating():
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    trimmed = compounds[compounds["scaffold_id"] != "S00"].copy()
    with pytest.raises(ScaffoldGeometryError, match="exactly 30 scaffolds"):
        assign_calibration_split(world_id, trimmed)


def test_unequal_scaffolds_stop_instead_of_approximating():
    world_id = "PB|NCAL|target_permuted_across_compounds|r000"
    compounds, _ = _synthetic_compounds(world_id)
    lopsided = compounds.drop(index=compounds.index[:2]).copy()
    with pytest.raises(ScaffoldGeometryError, match="equal scaffolds"):
        assign_calibration_split(world_id, lopsided)


# =======================================================================
# The defect A3.2 exists to remove
# =======================================================================

def constant_model_validation_r2(world) -> float:
    masks = world.split_masks()
    train, validation = world.target[masks["train"]], world.target[masks["validation"]]
    ss_tot = float(np.sum((validation - validation.mean()) ** 2))
    return 1.0 - float(np.sum((validation - train.mean()) ** 2)) / ss_tot


def test_no_null_family_is_systematically_non_null():
    """The descriptors_permuted family was at -0.246; it must now match.

    This is a property of world construction. It runs no search and produces
    no threshold.
    """
    means = {}
    for construction in CONSTRUCTIONS:
        values = [
            constant_model_validation_r2(build_world(construction, i))
            for i in range(12)
        ]
        means[construction] = float(np.mean(values))

    depressed = means["descriptors_permuted_across_compounds"]
    others = [
        means["target_permuted_across_compounds"],
        means["gaussian_targets_with_observed_variance"],
    ]
    # Was -0.246 against -0.055 and -0.077 before A3.2.
    assert depressed > -0.12, means
    assert abs(depressed - float(np.mean(others))) < 0.10, means


# =======================================================================
# A3.2 changes nothing else
# =======================================================================

def test_null_family_allocation_is_unchanged():
    assert dict(CONSTRUCTION_ALLOCATION) == {
        "target_permuted_across_compounds": 34,
        "descriptors_permuted_across_compounds": 33,
        "gaussian_targets_with_observed_variance": 33,
    }
    assert sum(CONSTRUCTION_ALLOCATION.values()) == N_CALIBRATION_WORLDS == 100


def test_within_compound_energy_permutation_remains_impossible():
    assert "within_compound_energy_permutation" in EXCLUDED_CONSTRUCTIONS
    with pytest.raises(ExcludedConstructionError):
        build_world("within_compound_energy_permutation", 0)
    # not a branch anywhere in the module
    source = inspect.getsource(worlds_mod)
    assert source.count("within_compound_energy_permutation") <= 2
    # and the worlds carry no energy dimension at all to permute
    world = build_world("target_permuted_across_compounds", 0)
    assert "energy" not in world.compounds.columns
    assert world.target.shape == (N_COMPOUNDS,)


def test_search_seeds_are_untouched_by_a3_2():
    for wid in list(all_world_ids())[:20]:
        seeds = derive_calibration_seeds(wid)
        assert len(seeds) == 30
        assert len(set(seeds)) == 30


# =======================================================================
# Records must be bound to the world construction that produced them
# =======================================================================

from muru.paper_benchmark.calibration_contract import (  # noqa: E402
    SEARCH_SETTINGS, SeedResult, SeedStatus,
)
from muru.paper_benchmark.rc3_calibration_runner import (  # noqa: E402
    FROZEN_SETTINGS_DIGEST, SearchOutcome, SeedRecordStore, run_calibration,
    run_world,
)


class _Backend:
    @property
    def effective_settings(self):
        return dict(SEARCH_SETTINGS)

    def __init__(self):
        self.calls = 0

    def search(self, world, seed):
        self.calls += 1
        return SearchOutcome(
            best_valid_r2_by_complexity={c: 0.2 for c in range(1, 21)},
            n_candidates=3,
        )


def test_world_construction_digest_distinguishes_worlds():
    a = build_world("target_permuted_across_compounds", 0)
    b = build_world("target_permuted_across_compounds", 1)
    c = build_world("descriptors_permuted_across_compounds", 0)
    digests = {a.construction_digest(), b.construction_digest(), c.construction_digest()}
    assert len(digests) == 3
    # stable for the same world
    assert a.construction_digest() == build_world(
        "target_permuted_across_compounds", 0).construction_digest()


def test_every_record_carries_the_world_construction_digest(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    run_world(world, _Backend(), store, seeds=[world.seeds[0]])
    line = json.loads(store.path_for(world.world_id).read_text().splitlines()[0])
    assert line["world_construction_digest"] == world.construction_digest()
    assert line["search_settings_digest"] == FROZEN_SETTINGS_DIGEST


def test_a_record_from_a_different_world_construction_is_refused(tmp_path):
    """The pre-A3.2 resume exploit.

    A record store written before A3.2 carries the same frozen search
    settings digest, so nothing in the settings check stops it. Its R2
    values were computed on a different base target and a different
    validation partition, and adopting them would corrupt the threshold.
    """
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    path = store.path_for(world.world_id)
    path.write_text(json.dumps({
        "world_id": world.world_id,
        "seed": world.seeds[0],
        "status": "COMPLETED_WITH_CANDIDATES",
        "best_valid_r2_by_complexity": {"1": 0.99},
        "error_message": "",
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
        "world_construction_digest": "pre-a3.2-world",
    }) + "\n")

    with pytest.raises(RuntimeError, match="construction digest"):
        store.load(world.world_id, world_digest=world.construction_digest())

    backend = _Backend()
    with pytest.raises(RuntimeError, match="construction digest"):
        run_world(world, backend, store, seeds=[world.seeds[0]])
    assert backend.calls == 0


def test_a_record_missing_the_world_digest_is_refused(tmp_path):
    """An RC3-era record has no world digest at all."""
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    store.path_for(world.world_id).write_text(json.dumps({
        "world_id": world.world_id, "seed": world.seeds[0],
        "status": "COMPLETED_NO_CANDIDATE",
        "best_valid_r2_by_complexity": None, "error_message": "",
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
    }) + "\n")
    with pytest.raises(RuntimeError, match="construction digest"):
        run_world(world, _Backend(), store, seeds=[world.seeds[0]])


def test_resume_still_works_for_a_matching_world(tmp_path):
    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    seeds = list(world.seeds[:3])

    first = _Backend()
    run_world(world, first, store, seeds=seeds)
    assert first.calls == 3

    second = _Backend()
    run_world(world, second, store, seeds=seeds)
    assert second.calls == 0


# =======================================================================
# The settings gate must fail closed
# =======================================================================

def test_a_backend_that_cannot_declare_its_settings_is_refused(tmp_path):
    """An undeclarable backend evaded the gate entirely before this."""
    class Undeclared:
        def search(self, world, seed):
            return SearchOutcome(best_valid_r2_by_complexity={1: 0.2}, n_candidates=1)

    world = build_world("target_permuted_across_compounds", 0)
    store = SeedRecordStore(tmp_path / "records")
    with pytest.raises(RuntimeError, match="effective_settings"):
        run_world(world, Undeclared(), store, seeds=[world.seeds[0]])

    specs = [(c, i) for c, n in CONSTRUCTION_ALLOCATION.items() for i in range(n)]
    with pytest.raises(RuntimeError, match="effective_settings"):
        run_calibration(Undeclared(), SeedRecordStore(tmp_path / "b"), world_specs=specs)


def test_shadowing_effective_settings_with_none_is_refused(tmp_path):
    """The exact evasion review executed: shadow the property with None."""
    from muru.paper_benchmark.rc3_calibration_runner import PySRBackend

    class Evasive(PySRBackend):
        effective_settings = None

    backend = Evasive(niterations_override=1, engineering_smoke=True)
    specs = [(c, i) for c, n in CONSTRUCTION_ALLOCATION.items() for i in range(n)]
    with pytest.raises(RuntimeError, match="effective_settings"):
        run_calibration(backend, SeedRecordStore(tmp_path / "records"), world_specs=specs)


def test_records_are_stamped_from_the_backend_not_the_store(tmp_path):
    """The store records what ran, not what it was told."""
    class Reduced(_Backend):
        @property
        def effective_settings(self):
            return {**SEARCH_SETTINGS, "niterations": 2}

    world = build_world("target_permuted_across_compounds", 0)
    # store claims frozen settings; backend actually runs reduced ones
    store = SeedRecordStore(tmp_path / "records")
    run_world(world, Reduced(), store, seeds=[world.seeds[0]])

    line = json.loads(store.path_for(world.world_id).read_text().splitlines()[0])
    assert line["search_settings_digest"] != FROZEN_SETTINGS_DIGEST
    # and that record is then unreadable by a frozen-settings store
    with pytest.raises(RuntimeError, match="search settings"):
        store.load(world.world_id)


def test_base_target_kind_cannot_be_varied_per_world():
    """A parameter that changed the numbers but not the world_id is gone."""
    with pytest.raises(TypeError):
        build_world("target_permuted_across_compounds", 0, "mass_only")
