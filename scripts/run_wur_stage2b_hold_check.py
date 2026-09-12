"""ONE LOOK at WUR-DEV-HOLD. Refuses to run twice."""
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_stage2 import holdcheck  # noqa: E402

if __name__ == "__main__":
    out = ROOT / "artifacts" / "wur_stage2b" / "hold_check.json"
    if out.exists():
        raise SystemExit("hold_check.json exists: HOLD is already EXPOSED; a second look is prohibited")
    res = holdcheck.run(ROOT / "data" / "external" / "wur")
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({"passed": res["passed"], "conditions": res["conditions"],
                      "P1": {k: round(v["P1"], 4) for k, v in res["arms"].items()}}, indent=1))
