"""STAGE 3: one look at WUR-SEALED. Refuses to run twice or before the freeze."""
import json
import os
import subprocess
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    out = ROOT / "artifacts" / "wur_stage3" / "stage3_result.json"
    if out.exists() or (ROOT / "artifacts" / "wur_stage3" / "first_sealed_access.json").exists():
        raise SystemExit("Stage 3 has already accessed WUR-SEALED; a second look is prohibited")
    if not (ROOT / "MURU_WUR_FINAL_CANDIDATE_FREEZE.md").exists():
        raise SystemExit("no freeze document; Stage 3 not authorized")
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "MURU_WUR_FINAL_CANDIDATE_FREEZE.md"], cwd=ROOT, capture_output=True)
    if tracked.returncode != 0:
        raise SystemExit("freeze document is not committed; Stage 3 not authorized")
    from muru.wur_stage2 import stage3
    res = stage3.run(ROOT / "data" / "external" / "wur")
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({"principal_claim_survives": res["principal_claim_survives"], "success_conditions": res["success_conditions"],
                      "P1": {k: round(v["P1"], 4) for k, v in res["arms"].items()}}, indent=1))
