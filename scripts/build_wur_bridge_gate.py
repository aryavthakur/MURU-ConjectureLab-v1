"""CLI: Stage 1, the cross-instrument bridge gate.

Writes artifacts/wur_bridge_gate.json. No logic lives here -- the gate is
muru.wur_bridge and the mu builder is muru.io.wur_spectra, both of which
have their own tests. This script wires them to real files, asserts the
lineage claims that cannot be tested on synthetic input, and runs once.
"""
import json
import sys
from pathlib import Path

import pandas as pd

from muru.io import wur_raw
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_identity import accepted_rows
from muru.io.wur_partition import (
    apply_d6, partition, sealed_scaffold_groups,
)
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.io.wur_spectra import build_mu_table
from muru.synth.generators import sealed_keys
from muru.wur_bridge import build_population_b, decide
from muru.wur_bridge_constants import (
    BASE_CELL, LADDER_ENERGIES, MEDIAN_ABS_DELTA_MAX, MIN_PAIRS_FOR_CORRELATION,
    MIN_PASSING_ENERGIES, MIN_POPULATION_B, OFFSET_MAX, PRECURSOR_MATCH_PPM,
    SPEARMAN_MIN,
)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def lcsb_mu_table() -> pd.DataFrame:
    """The LCSB development corpus at the base preprocessing cell.

    The corpus is asserted to be base-cell and single-valued per
    (compound, energy) rather than assumed: its lineage is checked against
    trajectories.parquet, which carries the cell columns the aggregated
    corpus drops.
    """
    dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    dev = dev.rename(columns={"inchikey_first_block": "connectivity_key"})

    counts = dev.groupby(["connectivity_key", "ce_numeric"]).size()
    assert counts.max() == 1, \
        f"LCSB corpus has {int((counts > 1).sum())} duplicated (compound, energy) cells"

    traj = pd.read_parquet(ART / "trajectories.parquet")
    base = traj[traj["is_base_cell"]]
    assert (base["cell_relative_cutoff"] == BASE_CELL["relative_cutoff"]).all()
    assert (base["cell_include_precursor"] == BASE_CELL["include_precursor"]).all()
    assert (base["cell_intensity_transform"] == BASE_CELL["intensity_transform"]).all()

    lineage = base[base["ion_mode_raw"].str.upper() == "POSITIVE"].groupby(
        ["inchikey_first_block", "ce_numeric"])["mu"].mean()
    check = dev.set_index(["connectivity_key", "ce_numeric"])["mu"]
    shared = check.index.intersection(lineage.index)
    assert len(shared) == len(check), \
        "an LCSB corpus row has no base-cell ancestor in trajectories.parquet"
    assert (check.loc[shared] - lineage.loc[shared]).abs().max() < 1e-9, \
        "LCSB corpus mu does not reproduce the base-cell value"

    return dev[["connectivity_key", "ce_numeric", "mu"]]


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"

    pre_d6 = partition(load_annotated_trajectories(data_dir))
    partitioned = apply_d6(pre_d6, sealed_scaffold_groups(pre_d6["POS"]))
    pos = partitioned["POS"]
    wur_dev_keys = set(pos.loc[pos["side"] == "WUR-DEV", "connectivity_key"])

    wur_sealed = set(json.loads(
        (ART / "wur_sealed_partition.json").read_text())["connectivity_keys"])
    lcsb = lcsb_mu_table()
    population_b = build_population_b(
        wur_dev_keys, set(lcsb["connectivity_key"]), wur_sealed, sealed_keys())

    assert not (set(population_b) & wur_sealed), "a WUR sealed key reached population B"
    assert not (set(population_b) & sealed_keys()), "an LCSB sealed key reached population B"
    print(f"Population B realized: {len(population_b)} compounds")
    if len(population_b) != 124:
        print(f"NOTE: realized population B is {len(population_b)}, not the "
              f"expected 124. Reporting the realized population.", file=sys.stderr)
    if len(population_b) < MIN_POPULATION_B:
        print(f"Population B ({len(population_b)}) is below the preregistered "
              f"floor of {MIN_POPULATION_B}. The gate will return NO_POOL.",
              file=sys.stderr)

    accepted = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    accepted_b = accepted[accepted["connectivity_key"].isin(set(population_b))]
    wur_mu, census = build_mu_table(accepted_b, data_dir)

    if census:
        print(f"HALT: {len(census)} population-B spectra carry a peak defect",
              file=sys.stderr)
        for entry in census[:20]:
            print(f"  {entry}", file=sys.stderr)
        sys.exit(1)

    for key, grp in wur_mu.groupby("connectivity_key"):
        assert set(grp["ce_numeric"]) == set(LADDER_ENERGIES), \
            f"{key}: incomplete WUR ladder after mu construction"

    result = decide(wur_mu, lcsb, population_b)
    result["stage"] = "Stage 1: cross-instrument bridge gate"
    result["preprocessing_cell"] = dict(BASE_CELL,
                                        precursor_match_ppm=PRECURSOR_MATCH_PPM)
    result["duplicate_aggregator"] = "median"
    result["wur_mu_provenance"] = {
        "n_population_b_spectra": int(accepted_b.shape[0]),
        "n_mu_cells": int(len(wur_mu)),
        "n_cells_with_duplicates": int((wur_mu["n_spectra"] > 1).sum()),
        "max_spectra_per_cell": int(wur_mu["n_spectra"].max()),
        "peak_defect_census": census,
    }
    result["population_b"]["connectivity_keys_sha256"] = canonical_key_hash(population_b)
    result["environment"] = environment_provenance(ROOT)
    result["min_population_b"] = MIN_POPULATION_B
    result["gate_thresholds"] = {
        "median_abs_delta_max": MEDIAN_ABS_DELTA_MAX,
        "spearman_min": SPEARMAN_MIN,
        "min_passing_energies": MIN_PASSING_ENERGIES,
        "offset_max": OFFSET_MAX,
        "min_pairs_for_correlation": MIN_PAIRS_FOR_CORRELATION,
    }
    result["preregistration"] = "wur-real-data-1.0, errata E-1 and E-2"

    (ART / "wur_bridge_gate.json").write_text(json.dumps(result, indent=2) + "\n")

    print(f"Wrote wur_bridge_gate.json")
    print(f"  OUTCOME: {result['outcome']}")
    for stat in result["pre_alignment"]["per_energy"]:
        print(f"  E{stat['ce_numeric']:>5.1f}  n={stat['n']:>3}  "
              f"median|delta|={stat['median_abs_delta']}  "
              f"signed={stat['median_signed_delta']}  "
              f"rho={stat['spearman_rho']}  passes={stat['passes']}")
