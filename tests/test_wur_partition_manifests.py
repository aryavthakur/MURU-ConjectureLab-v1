import json

import pandas as pd

from muru.io.wur_partition import build_sealed_partition, build_split_manifest, partition


def _annotated():
    pos = pd.DataFrame({
        "connectivity_key": [f"K{i}" for i in range(20)],
        "scaffold_group": [f"g{i}" for i in range(20)],
        "in_lcsb_dev": [False] * 20,
        "in_lcsb_sealed": [False] * 20,
    })
    neg = pd.DataFrame({
        "connectivity_key": ["N0"], "scaffold_group": ["ng0"],
        "in_lcsb_dev": [False], "in_lcsb_sealed": [False],
    })
    return {"POS": pos, "NEG": neg}


def test_split_manifest_reports_both_sides_and_floor_check():
    manifest = build_split_manifest(partition(_annotated()))
    assert set(manifest["polarities"]["POS"]) >= {
        "WUR-DEV", "WUR-SEALED", "sealed_floor_check"}
    assert manifest["polarities"]["NEG"]["WUR-DEV"]["n_trajectories"] == 1


def test_sealed_partition_keys_disjoint_from_dev_side():
    partitioned = partition(_annotated())
    sealed = build_sealed_partition(partitioned["POS"])
    dev_keys = set(partitioned["POS"].loc[
        partitioned["POS"]["side"] == "WUR-DEV", "connectivity_key"])
    assert not (set(sealed["connectivity_keys"]) & dev_keys)


def test_sealed_partition_is_json_serializable_with_only_identifiers():
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    json.dumps(sealed)  # must not raise
    assert set(sealed) == {
        "purpose", "constructed_utc", "seed", "selection_unit", "environment",
        "n_scaffold_groups", "n_compounds", "connectivity_keys",
        "connectivity_keys_sha256", "disclosure",
    }


def test_sealed_partition_hash_matches_its_own_key_list():
    from muru.io.wur_provenance import canonical_key_hash
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    assert sealed["connectivity_keys_sha256"] == canonical_key_hash(
        sealed["connectivity_keys"])


def test_sealed_partition_environment_carries_no_compound_identity():
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    env_text = json.dumps(sealed["environment"])
    for key in sealed["connectivity_keys"]:
        assert key not in env_text
