"""FRESH HOLDOUT — build the population, prove disjointness, quarantine truth."""
from __future__ import annotations

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
MAIN = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
ART = ROOT / "artifacts" / "fresh_holdout"
ART.mkdir(parents=True, exist_ok=True)

import fh_lib as fh  # noqa: E402


def _collect_historical():
    """Every historical world identity and symbolic seed reachable in the repo."""
    ids, seeds, sources = set(), set(), []

    def add_ids(vals, src):
        n0 = len(ids)
        ids.update(vals)
        sources.append({"source": src, "kind": "world_ids", "n": len(vals),
                        "new_union": len(ids) - n0})

    # objective-validation population (the 323-world development population)
    for base in (ROOT, MAIN):
        p = base / "artifacts" / "ov_worlds.json"
        if p.exists():
            d = json.loads(p.read_text())
            add_ids([w["world_id"] for w in d["worlds"]], str(p))
        p = base / "artifacts" / "ov_seed_manifest.json"
        if p.exists():
            d = json.loads(p.read_text())
            k = 0
            for v in d["seeds"].values():
                seeds.update(int(x) for x in v); k += len(v)
            sources.append({"source": str(p), "kind": "seeds", "n": k,
                            "new_union": len(seeds)})
        p = base / "artifacts" / "ov_truth_manifest.json"
        if p.exists():
            d = json.loads(p.read_text())
            add_ids([w["world_id"] for w in d["worlds"]], str(p))

    # sprint / accuracy-optimisation development identities
    p = ROOT / "artifacts" / "sprint" / "outer_fold_predictions.json"
    if p.exists():
        d = json.loads(p.read_text())
        for arch, rows in d.items():
            add_ids(list(rows), f"{p}::{arch}")

    # the checkpoint store itself: every world directory actually searched
    for base in (ROOT, MAIN):
        ck = base / "artifacts" / "ov_ckpt"
        if not ck.exists():
            continue
        found = set()
        for blockdir in sorted(ck.iterdir()):
            if not blockdir.is_dir():
                continue
            for wd in sorted(blockdir.iterdir()):
                if wd.is_dir():
                    found.add(wd.name)
        if found:
            sources.append({"source": str(ck), "kind": "checkpoint_dir_names",
                            "n": len(found), "note": "sha1-hashed dir names"})
            ids.update(found)

    # programmatic regeneration of the frozen development plan
    from muru.objval.plan2 import all_worlds2, seed_list2
    specs = all_worlds2()
    add_ids([s.world_id for s in specs], "muru.objval.plan2.all_worlds2()")
    k = 0
    for s in specs:
        v = seed_list2(s.world_id)
        seeds.update(v); k += len(v)
    sources.append({"source": "muru.objval.plan2.seed_list2()", "kind": "seeds",
                    "n": k, "new_union": len(seeds)})
    return ids, seeds, sources


def main() -> int:
    from muru.synth.generators import load_dev_covariates

    specs = fh.all_worlds()
    cov = load_dev_covariates()

    worlds, truths, seedmap = [], [], {}
    t0 = time.time()
    for i, s in enumerate(specs, 1):
        w = fh.build_fh_world(s, cov)
        m = w.manifest()
        m.update({"block": s.block, "family": s.family, "index": s.index,
                  "replicate": s.replicate, "noise_regime": s.noise_regime,
                  "cutoff_da": s.cutoff_da,
                  "null_construction": s.null_construction,
                  "category": fh.category(s.block)})
        worlds.append(m)
        tr = w.truth_record()
        tr.update({"block": s.block, "noise_regime": s.noise_regime,
                   "category": fh.category(s.block)})
        truths.append(tr)
        seedmap[s.world_id] = fh.fh_seed_list(s.world_id)
        if i % 16 == 0 or i == len(specs):
            print(f"[fh10] {i:3d}/{len(specs)} [{time.time()-t0:.0f}s]", flush=True)

    # ------------------------------------------------- disjointness proof --
    hist_ids, hist_seeds, sources = _collect_historical()
    new_ids = [w["world_id"] for w in worlds]
    new_seeds = [x for v in seedmap.values() for x in v]
    new_hashes = [w["output_sha256"] for w in worlds]

    hist_gen_seeds = set()
    from muru.objval.plan2 import all_worlds2
    from muru.objval.generators2 import world_seed2
    for s in all_worlds2():
        tag = (s.noise_regime if s.cutoff_da is None
               else f"{s.noise_regime}|cut{s.cutoff_da:g}")
        if s.null_construction:
            hist_gen_seeds.add(world_seed2(f"NULL|{s.null_construction}",
                                           s.replicate, s.noise_regime))
            hist_gen_seeds.add(world_seed2("G1B", 50_000 + s.replicate,
                                           s.noise_regime))
        else:
            hist_gen_seeds.add(world_seed2(s.family, s.replicate, tag))
    new_gen_seeds = [w["seed"] for w in worlds]

    dis = {
        "n_new_worlds": len(new_ids),
        "n_historical_world_ids_compared": len(hist_ids),
        "n_historical_symbolic_seeds_compared": len(hist_seeds),
        "n_historical_generator_seeds_compared": len(hist_gen_seeds),
        "sources_compared": sources,
        "checks": {
            "duplicate_new_world_ids": len(new_ids) - len(set(new_ids)),
            "overlapping_world_ids": sorted(set(new_ids) & hist_ids),
            "duplicate_new_symbolic_seeds": len(new_seeds) - len(set(new_seeds)),
            "overlapping_symbolic_seeds": sorted(set(new_seeds) & hist_seeds)[:20],
            "n_overlapping_symbolic_seeds": len(set(new_seeds) & hist_seeds),
            "duplicate_new_generator_seeds":
                len(new_gen_seeds) - len(set(new_gen_seeds)),
            "n_overlapping_generator_seeds":
                len(set(new_gen_seeds) & hist_gen_seeds),
            "duplicate_new_output_hashes": len(new_hashes) - len(set(new_hashes)),
            "n_overlapping_output_hashes_with_ov": None,
            "symbolic_seed_min": min(new_seeds),
            "symbolic_seed_max": max(new_seeds),
            "symbolic_band_above_ov_max":
                bool(min(new_seeds) > fh.OV_SEED_THEORETICAL_MAX),
            "symbolic_band_above_p3_max":
                bool(min(new_seeds) > fh.P3_SEED_THEORETICAL_MAX),
            "symbolic_band_within_int32": bool(max(new_seeds) <= fh.INT32_MAX),
        },
    }
    # world DATA hashes vs the development population's data hashes
    ovh = set()
    for base in (ROOT, MAIN):
        p = base / "artifacts" / "ov_worlds.json"
        if p.exists():
            ovh.update(w["output_sha256"]
                       for w in json.loads(p.read_text())["worlds"])
    dis["checks"]["n_overlapping_output_hashes_with_ov"] = len(set(new_hashes) & ovh)
    dis["checks"]["n_ov_output_hashes_compared"] = len(ovh)

    c = dis["checks"]
    dis["VERDICT"] = ("DISJOINT" if (c["duplicate_new_world_ids"] == 0
                                     and not c["overlapping_world_ids"]
                                     and c["duplicate_new_symbolic_seeds"] == 0
                                     and c["n_overlapping_symbolic_seeds"] == 0
                                     and c["duplicate_new_generator_seeds"] == 0
                                     and c["n_overlapping_generator_seeds"] == 0
                                     and c["duplicate_new_output_hashes"] == 0
                                     and c["n_overlapping_output_hashes_with_ov"] == 0
                                     and c["symbolic_band_above_ov_max"]
                                     and c["symbolic_band_within_int32"])
                      else "NOT_DISJOINT")

    wpayload = {"plan_version": fh.FH_PLAN_VERSION,
                "generator_version": worlds[0]["generator_version"],
                "truth_version": worlds[0]["truth_version"],
                "n_worlds": len(worlds),
                "n_distinct_output_hashes": len(set(new_hashes)),
                "seed_derivation": ("FH_SEED_BASE + (sha256(world_id)[:4] mod "
                                    "FH_SEED_SPREAD) * 100 + k, k = 0..5"),
                "seeds": seedmap, "worlds": worlds}
    wtext = json.dumps(wpayload, indent=1, sort_keys=True, default=str)
    (ROOT / "fresh_holdout_world_manifest.json").write_text(wtext)

    tpayload = {"truth_version": worlds[0]["truth_version"],
                "generator_version": worlds[0]["generator_version"],
                "QUARANTINE": ("Opened only after "
                               "fresh_holdout_predictions_frozen.json exists "
                               "and is hashed."),
                "n_worlds": len(truths), "worlds": truths}
    ttext = json.dumps(tpayload, indent=1, sort_keys=True, default=str)
    (ROOT / "fresh_holdout_truth_manifest.json").write_text(ttext)

    dis["world_manifest_sha256"] = hashlib.sha256(wtext.encode()).hexdigest()
    dis["truth_manifest_sha256"] = hashlib.sha256(ttext.encode()).hexdigest()
    dtext = json.dumps(dis, indent=1, sort_keys=True, default=str)
    (ROOT / "fresh_holdout_disjointness.json").write_text(dtext)

    print(json.dumps({"VERDICT": dis["VERDICT"], "n_worlds": len(worlds),
                      "checks": {k: v for k, v in c.items()
                                 if not isinstance(v, list)},
                      "world_manifest_sha256": dis["world_manifest_sha256"],
                      "truth_manifest_sha256": dis["truth_manifest_sha256"]},
                     indent=1))
    return 0 if dis["VERDICT"] == "DISJOINT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
