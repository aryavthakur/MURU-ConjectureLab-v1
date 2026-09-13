"""Builds artifacts/wur_v2_confirmation/eligible_population.csv: one row per
compound that survived header-only eligibility (key, smiles, mh, scaffold_group),
used by 11_run_one_look.py and 12_external_analysis.py. Written as its own
auditable step (statistics-review finding: this file previously had no builder
in the tracked tree) -- a trivial, verifiable restriction of the frozen sampled
population to header_eligibility.json's eligible_keys. Contains ONLY MSnLib
validation-population keys: it is built by filtering sampled_compound_wells.parquet
(itself built only from the nine MSnLib library identity tables, never merged
with any exposed/development population) down to eligible_keys.
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")


def main():
    header_elig = json.loads((REPO / "artifacts/wur_v2_confirmation/header_eligibility.json").read_text())
    eligible_keys = set(header_elig["eligible_keys"])

    dsub = pd.read_parquet(MD / "sampled_compound_wells.parquet")
    pop = dsub[dsub.key.isin(eligible_keys)].drop_duplicates("key")[["key", "smiles", "mh", "scaffold_group"]].reset_index(drop=True)

    assert set(pop.key) == eligible_keys, "eligible_population must contain exactly the eligible keys, no more, no fewer"
    assert pop.scaffold_group.isna().sum() == 0
    assert pop.mh.isna().sum() == 0

    # sanity: no exposed/development population key can appear here, since the source table
    # (sampled_compound_wells.parquet) was built purely from the 9 MSnLib identity tables and
    # DESIGN 12b (itself already scaffold-new vs v2 development, per the census's own step 10/10b)
    dev = pd.read_csv(REPO / "artifacts/wur_v2/data/compounds.csv", usecols=["group_key"])
    overlap = set(pop.key) & set(dev.group_key)
    assert not overlap, f"MSnLib validation keys overlap MURU development keys: {overlap}"

    outp = REPO / "artifacts/wur_v2_confirmation/eligible_population.csv"
    pop.to_csv(outp, index=False)
    print(f"eligible_population: {len(pop)} compounds, {pop.scaffold_group.nunique()} scaffold groups")
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
