"""Stage 2B: run the four reference arms on the frozen folds, ledger them."""
import json
import os
import subprocess
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.wur_stage2 import cv as CV          # noqa: E402
from muru.wur_stage2 import folds as FO       # noqa: E402

OUT = ROOT / "artifacts" / "wur_stage2b"


def main():
    long, cov, frame = CV.load_dev2b()
    folds = FO.load_folds()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    b0p = CV.b0_predictions(long, cov, frame, folds)
    results = {}
    arms = [("B0_NULL_PROFILE", CV.B0NullProfile, "no descriptors; per-energy training mean"),
            ("B1_MASS_ONLY_ISOTONIC", CV.B1MassOnly, "log g isotonic in precursor m/z"),
            ("LIN_RIDGE_TIERA", CV.LinRidge, "ridge log g ~ 12 scaled Tier A descriptors"),
            ("S2A_FROZEN_PIPELINE", lambda: CV.S2AFrozen(OUT / "ckpt_s2a"), "the pre-WUR pipeline per fold")]
    for cid, make, desc in arms:
        r = CV.run_cv(make, long, cov, frame, folds, b0p, with_loeo=True)
        results[cid] = r
        comps = {k: CV.compare(r, results[k]) for k in results if k != cid}
        boots = {k: CV.paired_bootstrap(r, results[k]) for k in results if k != cid}
        CV.ledger_entry(cid, r, {"parent": None, "hypothesis": "reference arm", "rationale": desc,
                                 "features": make().complexity if cid != "S2A_FROZEN_PIPELINE" else CV.S2AFrozen.complexity,
                                 "model_family": cid, "generation": "reference"},
                        {"fold_compare": comps, "paired_bootstrap": boots},
                        folds["folds_sha256"], commit)
        (OUT / f"percompound_{cid}.json").write_text(json.dumps(
            {"per_compound": r.per_compound, "loeo": r.loeo}, sort_keys=True))
        print(f"[2b-ref] {cid}: P1 mean {r.p1_vector().mean():.4f} sd {r.p1_vector().std(ddof=1):.4f} "
              f"{r.seconds:.0f}s", flush=True)


if __name__ == "__main__":
    main()
