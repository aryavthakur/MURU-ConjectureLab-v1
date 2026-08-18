"""PySR against the gplearn comparison arm.

Master plan 13.3: "If two engines with different search dynamics converge on
equivalent expressions, that is evidence. If they do not, the expression is a
search artifact."

gplearn cannot rescue a failing PySR calibration and is not being asked to.
Engine disagreement is reported as measured.

Writes `artifacts/p3_engine_comparison.json`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                        # noqa: E402
import sympy as sp                                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"

TRUTH = {
    "G1B": "1.7017*sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)",
    "G3": "1.7017*precursor_mz**0.6",
}


def compare(spec) -> dict:
    from muru.discovery import equivalence, grammar, protocol
    from muru.discovery.checkpoint import Store
    from muru.synth.generators import build_world, load_dev_covariates
    from muru.discovery.engine import Candidate

    cov = None if spec.family == "GA" else load_dev_covariates()
    world = build_world(spec.family, spec.replicate, spec.noise_regime,
                        cov=cov, cutoff_da=spec.cutoff_da)
    wd = protocol.build_world_data(spec.world_id, world.long, world.cov)
    V = wd.variables
    store = Store(ART / "p3_ckpt")

    def selected(engine_name):
        units = store.read_world(f"{spec.block}_{engine_name}", spec.world_id)
        per = {}
        for k, payload in units.items():
            if k == "_world":
                continue
            cs = []
            for c in payload["candidates"]:
                try:
                    e = sp.sympify(c["expr"])
                except Exception:
                    continue
                cs.append(Candidate(
                    expr_str=c["expr_str"], expr=e, complexity=int(c["complexity"]),
                    support=tuple(c["support"]), engine=c["engine"],
                    seed=int(c["seed"]), train_r2=float(c["train_r2"]),
                    valid_r2=float(c["valid_r2"]),
                    invalid_fraction=float(c["invalid_fraction"]),
                    valid=bool(c["valid"])))
            per[int(k)] = cs
        if not per:
            return None, None
        res = protocol.aggregate(wd, per, which=engine_name)
        return res.candidate, res.stability

    p_cand, p_stab = selected("pysr")
    g_cand, g_stab = selected("gplearn")
    if p_cand is None or g_cand is None:
        return {"world_id": spec.world_id, "block": spec.block,
                "status": "incomplete"}

    D = equivalence.latin_hypercube(equivalence.domain_bounds(wd.X, V), V,
                                    equivalence.N_LHC_ADJUDICATE, seed=99)
    agree = equivalence.equivalence(p_cand.expr, g_cand.expr, V, D)
    out = {
        "world_id": spec.world_id, "block": spec.block, "family": spec.family,
        "noise_regime": spec.noise_regime, "status": "ok",
        "pysr": {"expr": p_cand.expr_str, "complexity": p_cand.complexity,
                 "valid_r2": p_cand.valid_r2, "support": list(p_cand.support),
                 "selection_fraction": p_stab["fraction"]},
        "gplearn": {"expr": g_cand.expr_str, "complexity": g_cand.complexity,
                    "valid_r2": g_cand.valid_r2, "support": list(g_cand.support),
                    "selection_fraction": g_stab["fraction"]},
        "engines_agree": bool(agree["functionally_equivalent"]),
        "agreement_rel_rmse": agree["numeric"]["rel_rmse"],
        "support_match": bool(agree["support_match"]),
    }
    if spec.family in TRUTH:
        truth = grammar.parse(TRUTH[spec.family], V)
        for name, cand in (("pysr", p_cand), ("gplearn", g_cand)):
            e = equivalence.equivalence(cand.expr, truth, V, D)
            out[name]["matches_planted"] = bool(e["functionally_equivalent"])
            out[name]["rel_rmse_vs_planted"] = e["numeric"]["rel_rmse"]
    return out


def main() -> int:
    import multiprocessing as mp
    from muru.synth import plan

    specs = plan.gplearn_worlds()
    ctx = mp.get_context("spawn")
    with ctx.Pool(4) as pool:
        recs = [r for r in pool.imap_unordered(compare, specs)
                if r.get("status") == "ok"]
    recs.sort(key=lambda r: r["world_id"])

    summary = {}
    for block in sorted({r["block"] for r in recs}):
        sub = [r for r in recs if r["block"] == block]
        summary[block] = {
            "n_worlds": len(sub),
            "engines_agree_rate": sum(r["engines_agree"] for r in sub) / len(sub),
            "support_match_rate": sum(r["support_match"] for r in sub) / len(sub),
            "pysr_median_complexity": float(np.median(
                [r["pysr"]["complexity"] for r in sub])),
            "gplearn_median_complexity": float(np.median(
                [r["gplearn"]["complexity"] for r in sub])),
            "pysr_median_valid_r2": float(np.median(
                [r["pysr"]["valid_r2"] for r in sub])),
            "gplearn_median_valid_r2": float(np.median(
                [r["gplearn"]["valid_r2"] for r in sub])),
        }
        if "matches_planted" in sub[0]["pysr"]:
            summary[block]["pysr_matches_planted_rate"] = sum(
                r["pysr"]["matches_planted"] for r in sub) / len(sub)
            summary[block]["gplearn_matches_planted_rate"] = sum(
                r["gplearn"]["matches_planted"] for r in sub) / len(sub)

    out = {
        "role": ("gplearn is a comparison arm on T2, not a tournament entrant. "
                 "It cannot rescue a failing PySR calibration; switching engines "
                 "after seeing a result would require an explicit deviation and "
                 "independent recalibration."),
        "scope": "pre-registered limited subset (DEVIATIONS_P3 D5)",
        "summary": summary,
        "worlds": recs,
    }
    (ART / "p3_engine_comparison.json").write_text(json.dumps(out, indent=1))
    for b, s in summary.items():
        extra = (f", planted-match PySR {s.get('pysr_matches_planted_rate', 0):.0%} "
                 f"vs gplearn {s.get('gplearn_matches_planted_rate', 0):.0%}"
                 if "pysr_matches_planted_rate" in s else "")
        print(f"[t3_46] {b:5s} n={s['n_worlds']:3d} agree "
              f"{s['engines_agree_rate']:.0%}, support match "
              f"{s['support_match_rate']:.0%}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
