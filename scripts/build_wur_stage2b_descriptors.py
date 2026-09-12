"""Tier A2 descriptors for every DEV2B key (and, later, HOLD / sealed at freeze time).

Identity only: SMILES from p2_compounds (LCSB) and the WUR accepted rows.
Writes artifacts/wur_stage2b/descriptors_a2.csv.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_stage2 import population as POP                # noqa: E402
from muru.wur_stage2.descriptors2 import TIER_A2, tier_a2_descriptors  # noqa: E402

if __name__ == "__main__":
    data_dir = ROOT / "data" / "external" / "wur"
    frame = pd.read_csv(ROOT / "artifacts" / "wur_stage2a" / "A_POOLED_ALIGNED" / "compounds.csv")
    lcsb = pd.read_parquet(ROOT / "artifacts" / "p2_compounds.parquet")
    lcsb = lcsb[~lcsb.in_confirmation][["inchikey_first_block", "smiles"]].rename(
        columns={"inchikey_first_block": "connectivity_key"})
    dev = POP.wur_dev_partition(data_dir)
    _, ident = POP.wur_analysis_accepted(data_dir, dev)
    wur = ident[["connectivity_key", "smiles"]]
    smiles = pd.concat([lcsb, wur[~wur.connectivity_key.isin(set(lcsb.connectivity_key))]])
    smiles = smiles.set_index("connectivity_key")["smiles"]
    rows, fail = [], []
    for k in frame.group_key:
        d = tier_a2_descriptors(smiles.loc[k])
        if not d:
            fail.append(k); continue
        rows.append({"group_key": k, **d})
    out = pd.DataFrame(rows, columns=["group_key", *TIER_A2])
    out.to_csv(ROOT / "artifacts" / "wur_stage2b" / "descriptors_a2.csv", index=False)
    print(out.shape, "failures", fail)
