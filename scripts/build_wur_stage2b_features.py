"""Extended per-spectrum summaries for DEV2B, both corpora, base cell.

Reads WUR-DEV-ANALYSIS spectra only (HOLD forbidden, seal guarded) and the
LCSB-DEV MassBank records. Writes artifacts/wur_stage2b/features_{wur,lcsb}.csv
plus a census of defects. Diagnostic inputs for the Stage 2A failure
analysis and candidate features for Stage 2B; no model is fitted here.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.wur_stage2 import population as POP            # noqa: E402
from muru.wur_stage2 import spectral_features as SF       # noqa: E402

OUT = ROOT / "artifacts" / "wur_stage2b"

if __name__ == "__main__":
    data_dir = ROOT / "data" / "external" / "wur"
    dev = POP.wur_dev_partition(data_dir)
    acc, ident = POP.wur_analysis_accepted(data_dir, dev)
    hold = set(POP.load_internal_holdout()["hold"]["connectivity_keys"])
    wur, cw = SF.wur_feature_table(acc, data_dir, forbidden=hold)
    lcsb_keys = set(POP.lcsb_dev_mu_table()["connectivity_key"])
    lcsb, cl = SF.lcsb_feature_table(lcsb_keys)
    OUT.mkdir(parents=True, exist_ok=True)
    wur.to_csv(OUT / "features_wur.csv", index=False)
    lcsb.to_csv(OUT / "features_lcsb.csv", index=False)
    (OUT / "features_census.json").write_text(json.dumps(
        {"wur": {"n_cells": int(len(wur)), "n_keys": int(wur.connectivity_key.nunique()), "defects": cw},
         "lcsb": {"n_cells": int(len(lcsb)), "n_keys": int(lcsb.connectivity_key.nunique()), "defects": cl}},
        indent=1))
    print("wur", wur.shape, "lcsb", lcsb.shape, "defects", len(cw), len(cl))
