"""Experiment 5 supplement (diagnostic, not a candidate): how much pooled error is
the source x mass acquisition effect? TA_RIDGE plus a WUR indicator and a WUR x
scaled-mass column. Not deployable to a new instrument."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.discovery import protocol
from muru.wur_v2 import runner as RU, models as MO, ledger as LG
ROOT = Path(__file__).resolve().parents[2]
d = RU.load_data(False)
is_w = (d.cov.primary_source == "WUR").astype(float)
TA = MO.tier_a_scaled(d.cov)
d.features["TIER_A"] = TA
d.features["TIER_A_SOURCE"] = TA.assign(is_wur=is_w, wur_x_mass=is_w * d.cov.precursor_mz / protocol.SCALE["precursor_mz"])
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
sa = RU.run(MO.RidgeModel("TIER_A_SOURCE", model_id="DIAG_TA_RIDGE_SOURCE_X_MASS"), d, "PRIMARY")
b0 = RU.b0(d, "PRIMARY")
c = RU.compare(d, sa.pred, ta.pred, "PRIMARY", b0)
st = RU.strata(d, sa.pred, ta.pred)
out = {"compare": c, "strata": st}
(ROOT / "artifacts/wur_v2/exp05/exp05b_source_adapter.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(round(c["cand"]["P1"], 4), round(c["ref"]["P1"], 4), c["bootstrap"]["P1_ratio_ci"], {k: round(v["P1_ratio"], 3) for k, v in st.items()})
LG.append({"experiment_id": "V2-EXP05B-SOURCE-X-MASS-DIAGNOSTIC", "generation": "v2-G0", "parent_model": "TA_RIDGE",
 "hypothesis": "The source x mass acquisition effect found in the paired analysis accounts for a material part of pooled development error.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "TIER_A + is_WUR + is_WUR x mass (diagnostic only)",
 "endpoint": "aligned mu 30-90", "hyperparameters_and_space": "alpha in {0.01,0.1,1,10,100}", "tuning_process": "nested trajectory loss",
 "results": {"P1": c["cand"]["P1"], "P1_ref": c["ref"]["P1"], "strata": st}, "uncertainty": c["bootstrap"],
 "tail_metrics": {"AF": c["cand"]["AF"], "AF_ref": c["ref"]["AF"]},
 "interpretation": "diagnostic of acquisition-driven error in the pooled development data; a source indicator cannot be used for an unseen instrument",
 "decision": "diagnostic", "reason": "not deployable", "informed_later_decisions": "decision gate question on acquisition effects"})
