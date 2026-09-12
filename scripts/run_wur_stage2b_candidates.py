"""Stage 2B: run every registered candidate on the frozen folds and ledger it."""
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_stage2 import arms_v1  # noqa: E402,F401  (registers)
from muru.wur_stage2 import candidates as CA  # noqa: E402

if __name__ == "__main__":
    ids = sys.argv[1:] or list(CA.REGISTRY)
    for cid in ids:
        if (CA.CV.LEDGER / f"{cid}.json").exists():
            print(f"[2b] {cid}: ledger entry exists, skipped"); continue
        p = CA.run_candidate(cid)
        d = json.loads(p.read_text())
        print(f"[2b] {cid}: P1 {d['P1_mean']:.4f} sd {d['P1_sd']:.4f} "
              f"wins vs S2A {d['comparisons']['fold_compare']['S2A_FROZEN_PIPELINE']['wins']} "
              f"rel {d['comparisons']['fold_compare']['S2A_FROZEN_PIPELINE']['mean_rel_improvement']:.3f}", flush=True)
    for cid in ids:
        print(json.dumps(CA.evaluate_rule(cid), default=str))
