"""Build every fresh validation world and freeze its manifests.

Two manifests are written, and the separation is the study's blinding mechanism:

* `artifacts/ov_worlds.json` — world identity, seeds, split counts, output
  hashes. **Contains no planted law.** This is what search-side code may read.
* `artifacts/ov_truth_manifest.json` — the planted law, its drawn parameters and
  its support, for every world. **Quarantined**: opened only by
  `ov_45_recovery.py`, after candidate selection is complete and frozen.

Both are hashed; the hashes appear in `TYPE2_VALIDATION_DECISION.md`.

    python scripts/ov_10_build_worlds.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"


def main() -> int:
    from muru.objval.generators2 import (GENERATOR2_VERSION, build_null_world2,
                                         build_world2, write_truth_manifest)
    from muru.objval.plan2 import (PLAN2_VERSION, N_SEEDS, all_worlds2,
                                   seed_list2)
    from muru.objval.truth2 import TRUTH2_VERSION
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    cov = load_dev_covariates()
    specs = all_worlds2()
    if a.limit:
        specs = specs[:a.limit]

    worlds, truths, seeds = [], [], {}
    t0 = time.time()
    for i, s in enumerate(specs, 1):
        if s.null_construction:
            w = build_null_world2(s.replicate, s.null_construction, cov)
        else:
            w = build_world2(s.family, s.replicate, s.noise_regime,
                             cov=None if s.family == "G1A" else cov,
                             cutoff_da=s.cutoff_da)
        assert w.world_id == s.world_id, (w.world_id, s.world_id)
        m = w.manifest()
        m.update({"block": s.block, "cutoff_da": s.cutoff_da,
                  "null_construction": s.null_construction})
        worlds.append(m)
        truths.append(w.truth_record())
        seeds[s.world_id] = seed_list2(s.world_id)
        if i % 25 == 0 or i == len(specs):
            print(f"[ov10] {i:4d}/{len(specs)} built "
                  f"[{(time.time()-t0)/60:.1f}m]", flush=True)

    hashes = [w["output_sha256"] for w in worlds]
    assert len(set(hashes)) == len(hashes), "two worlds produced identical data"

    truth_sha = write_truth_manifest(truths)

    wpayload = {"plan_version": PLAN2_VERSION,
                "generator_version": GENERATOR2_VERSION,
                "truth_version": TRUTH2_VERSION,
                "n_worlds": len(worlds), "n_distinct_output_hashes": len(set(hashes)),
                "worlds": worlds}
    wtext = json.dumps(wpayload, indent=1, sort_keys=True, default=str)
    (ART / "ov_worlds.json").write_text(wtext)

    allseeds = [x for v in seeds.values() for x in v]
    spayload = {"derivation": ("OV_SEED_BASE + (sha256(world_id)[:4] mod "
                              "OV_SEED_SPREAD) * 100 + k, k = 0..29"),
                "seed_schedule_version": "ov-seeds-1.0.0",
                "n_seeds_per_world": N_SEEDS, "n_worlds": len(seeds),
                "seed_min": min(allseeds), "seed_max": max(allseeds),
                "phase3_seed_theoretical_max": 1_678_621_529,
                "seeds": seeds}
    stext = json.dumps(spayload, indent=1, sort_keys=True)
    (ART / "ov_seed_manifest.json").write_text(stext)

    out = {"worlds_sha256": hashlib.sha256(wtext.encode()).hexdigest(),
           "truth_manifest_sha256": truth_sha,
           "seed_manifest_sha256": hashlib.sha256(stext.encode()).hexdigest(),
           "n_worlds": len(worlds), "seed_min": min(allseeds),
           "seed_max": max(allseeds)}
    (ART / "ov_manifest_hashes.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
