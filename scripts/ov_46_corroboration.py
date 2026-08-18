"""Independent-engine corroboration at the claim-relevant level.

Phase 3 measured corroboration as agreement on the *expression*, and found 3%
on `G1` and 0% on `G3`. That is the wrong question for a Type 2 claim: an
empirical family claim is about support and scaling, not about which string an
engine emits. It is also the wrong question given what this corpus can identify.

The frozen standard compares what the claim is made of:

1. **effective support at block level** — the mass block counts as one slot,
   because `precursor_mz`, `total_atom_count` and `rdbe` are near-collinear and
   `DESCRIPTORS.md` already treats them as one block;
2. **the mass-block scaling exponent**, within the master plan's ±0.15;
3. **the sign of every shared effect**;
4. **full Type 2 family membership**, the same predicate used everywhere else.

Exact-expression agreement is measured too, and reported, so the comparison with
Phase 3's number stays available.

    python scripts/ov_46_corroboration.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"
SEL = ART / "ov_sel"

# Frozen corroboration standard. Stated on the G1B moderate-regime worlds — the
# block where a real molecule-conditional relationship exists and where
# corroboration is therefore meaningful.
CORROBORATION_BLOCK = "G1B"
CORROBORATION_REGIME = "moderate"
MIN_SUPPORT_AGREEMENT = 0.50
MIN_EXPONENT_AGREEMENT = 0.50


def main() -> int:
    import numpy as np
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store
    from muru.objval import equiv, select as selmod, signature
    from muru.objval.equiv import EXPONENT_TOL
    from muru.objval.plan2 import gplearn_worlds2
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ART / "ov_engine_corroboration.json"))
    a = ap.parse_args()

    store = Store(SEL)
    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8,
                                              size=(len(Xreal), len(variables)))

    rows = []
    for s in gplearn_worlds2():
        if not (store.done(s.block, s.world_id, "pysr")
                and store.done(s.block, s.world_id, "gplearn")):
            continue
        p = store.read(s.block, s.world_id, "pysr")["reported"]
        g = store.read(s.block, s.world_id, "gplearn")["reported"]
        row = {"world_id": s.world_id, "block": s.block,
               "noise_regime": s.noise_regime,
               "pysr_reported": bool(p), "gplearn_reported": bool(g)}
        if not (p and g):
            rows.append(row)
            continue

        import sympy as sp
        X = Xsynth if s.family == "G1A" else Xreal
        Z = selmod.lattice(X, variables)
        ep = sp.sympify(p["representative"]["expr"].replace("^", "**"))
        eg = sp.sympify(g["representative"]["expr"].replace("^", "**"))
        sp_, sg = (signature.signature(ep, variables, Z),
                   signature.signature(eg, variables, Z))
        vp, okp = signature._eval(ep, variables, Z)
        vg, okg = signature._eval(eg, variables, Z)
        ok = okp & okg

        bp, bg = set(sp_["effective_support_blocks"]), set(sg["effective_support_blocks"])
        mp, mg = signature.mass_exponent(sp_), signature.mass_exponent(sg)
        shared = bp & bg
        fam = equiv.same_family(sp_, sg, vp, vg, ok)
        fc = equiv.functional_class(vp, vg, ok)

        row.update({
            "pysr_blocks": sorted(bp), "gplearn_blocks": sorted(bg),
            "pysr_variables": sp_["effective_support"],
            "gplearn_variables": sg["effective_support"],
            "block_support_match": bool(bp == bg),
            "variable_support_match": bool(set(sp_["effective_support"])
                                           == set(sg["effective_support"])),
            "pysr_mass_exponent": mp, "gplearn_mass_exponent": mg,
            "mass_exponent_agree": bool(np.isfinite(mp) and np.isfinite(mg)
                                        and abs(mp - mg) <= EXPONENT_TOL),
            "sign_agreement": bool(shared) and all(
                sp_["block_signs"].get(v) == sg["block_signs"].get(v)
                for v in shared),
            "same_type2_family": fam["same_family"],
            "family_disagreement_reasons": fam["reasons"],
            "functionally_equivalent_expressions": fc["functionally_equivalent"],
            "pysr_expr": p["representative"]["expr"],
            "gplearn_expr": g["representative"]["expr"],
        })
        rows.append(row)

    def rate(rs, key):
        rs = [r for r in rs if key in r]
        return (sum(bool(r[key]) for r in rs) / len(rs)) if rs else float("nan")

    by_block = {}
    for b in sorted({r["block"] for r in rows}):
        rs = [r for r in rows if r["block"] == b]
        by_block[b] = {
            "n": len(rs),
            "block_support_match": rate(rs, "block_support_match"),
            "variable_support_match": rate(rs, "variable_support_match"),
            "mass_exponent_agree": rate(rs, "mass_exponent_agree"),
            "sign_agreement": rate(rs, "sign_agreement"),
            "same_type2_family": rate(rs, "same_type2_family"),
            "functionally_equivalent_expressions":
                rate(rs, "functionally_equivalent_expressions"),
        }

    gate = [r for r in rows if r["block"] == CORROBORATION_BLOCK
            and r["noise_regime"] == CORROBORATION_REGIME]
    sup, exp = rate(gate, "block_support_match"), rate(gate, "mass_exponent_agree")
    verdict = {
        "standard": (f"on {CORROBORATION_BLOCK} {CORROBORATION_REGIME} worlds: "
                     f"block-level effective support agrees in "
                     f">= {MIN_SUPPORT_AGREEMENT:.0%} of worlds AND the "
                     f"mass-block exponent agrees within +/-{EXPONENT_TOL} in "
                     f">= {MIN_EXPONENT_AGREEMENT:.0%}"),
        "n_worlds": len(gate),
        "block_support_agreement": sup,
        "mass_exponent_agreement": exp,
        "satisfied": bool(np.isfinite(sup) and np.isfinite(exp)
                          and sup >= MIN_SUPPORT_AGREEMENT
                          and exp >= MIN_EXPONENT_AGREEMENT),
    }

    Path(a.out).write_text(json.dumps(
        {"n": len(rows), "by_block": by_block, "gate": verdict, "rows": rows},
        indent=1, default=str))
    print(json.dumps({"by_block": by_block, "gate": verdict}, indent=1),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
