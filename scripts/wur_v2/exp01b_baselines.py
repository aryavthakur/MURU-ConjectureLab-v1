"""Experiment 1, part B: refit the v1 family under v2 nesting on the v2
population; compare v2 trajectory-loss alpha selection with v1's selection."""
import json, os, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
from pathlib import Path
from muru.wur_v2 import runner as RU, models as MO
parts = sys.argv[1:] or ["PRIMARY"]
d = RU.load_data()
for part in parts:
    b0 = RU.b0(d, part)
    for m in (MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), MO.RidgeV1Selection(), MO.MassIsotonic()):
        t = time.time(); r = RU.run(m, d, part)
        s = RU.compare(d, r.pred, b0, part, b0, boot=False)["cand"]
        print(part, m.id, "P1 %.4f MRMSE %.4f AF %.3f S4 %.3f" % (s["P1"], s["MRMSE"], s["AF"], s.get("S4", float('nan'))), r.cfgs, "%.0fs" % (time.time() - t))
    s = RU.compare(d, b0, b0, part, b0, boot=False)["cand"]; print(part, "B0 P1 %.4f AF %.3f" % (s["P1"], s["AF"]))
