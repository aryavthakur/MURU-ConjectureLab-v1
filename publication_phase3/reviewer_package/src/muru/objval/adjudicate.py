"""Type 2 acceptance: the frozen rule a reported family must satisfy.

Every condition is either taken unchanged from Phase 3 or taken from the master
plan's own definition of `L4` and §14.4. Two conditions are NEW relative to
Phase 3's acceptance rule, and both make acceptance HARDER:

* **ceiling fraction** — master plan §16.2 defines L4 as reaching "≥ 80% of the
  Tier B ceiling", and §14.4 declares the same minimum effect size. Phase 3's
  §20 explicitly waived it. It is reinstated here because a Type 2 claim that a
  compact expression captures the relationship is empty if a flexible predictor
  on the same descriptors does far better.
* **H-MAIN adequacy** — the Type 2 claim *is* `mu = Phi(E/g(z))`. If the
  collapse model is rejected out of sample against a freed per-compound shape,
  the family claim is contradicted by the data and must not be accepted, however
  well the symbolic stage fits the estimated scale.

This module reads data and candidates. It never reads a planted law.
"""
from __future__ import annotations

import numpy as np

from muru.discovery import falsify, grammar
from muru.discovery.protocol import WorldData
from muru.objval import signature

ADJUDICATE_VERSION = "ov-adjudicate-1.0.0"

MIN_SELECTION_FRACTION = 20.0 / 30.0     # master plan L4, unchanged
MAX_COMPLEXITY = grammar.MAX_COMPLEXITY  # 20, unchanged
MAX_INVALID_FRACTION = grammar.MAX_INVALID_FRACTION  # 0.005, unchanged

# Master plan §14.4: "the symbolic expression must reach >= 80% of the Tier B
# ceiling's held-out R^2 at complexity <= 20".
MIN_CEILING_FRACTION = 0.80
# Below this the ceiling itself carries no signal and the ratio is meaningless,
# so the condition is recorded not-applicable rather than silently passed or
# silently failed.
CEILING_MIN_R2 = 0.05


def flexible_ceiling(wd: WorldData) -> float:
    """Held-out R^2 of a flexible predictor on ALL descriptors.

    The synthetic analogue of the Phase 2 Tier B ceiling: the most a model can
    extract from the same inputs the symbolic search is given. Constructed
    exactly like `falsify._mass_only_reference` but without the mass-block
    restriction, so the two are directly comparable.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor
    tr, te = wd.split == "train", wd.split == "test"
    m = HistGradientBoostingRegressor(max_iter=150, max_depth=3,
                                      min_samples_leaf=20, random_state=0)
    m.fit(wd.X[tr], wd.y[tr], sample_weight=wd.w[tr])
    pred = m.predict(wd.X[te])
    yy, ww = wd.y[te], wd.w[te]
    mean = np.average(yy, weights=ww)
    ss_tot = float(np.sum(ww * (yy - mean) ** 2))
    if ss_tot <= 0:
        return -np.inf
    return 1.0 - float(np.sum(ww * (yy - pred) ** 2)) / ss_tot


def accept_type2(wd: WorldData, reported: dict | None, expr, complexity: int,
                 null_threshold: np.ndarray, harness: dict | None,
                 ceiling_r2: float) -> dict:
    """The frozen Type 2 acceptance rule. All conditions are necessary."""
    if reported is None:
        return {"accepted": False, "reason": "no reported Type 2 family",
                "conditions": {}, "claims_non_mass_structure": False}

    rep = reported["representative"]
    thr = float(null_threshold[min(complexity, len(null_threshold) - 1)])
    Xtr, ytr, wtr = wd.part("train")
    Xte, yte, wte = wd.part("test")
    test_r2 = falsify.r2_after_refit(expr, wd.variables, Xtr, ytr, wtr,
                                     Xte, yte, wte)

    ceiling_applicable = bool(np.isfinite(ceiling_r2) and ceiling_r2 > CEILING_MIN_R2)
    ceiling_fraction = (float(test_r2 / ceiling_r2) if ceiling_applicable
                        else float("nan"))

    support = list(reported["effective_support"])
    blocks = list(reported.get("effective_support_blocks",
                               [signature.block_of(v) for v in support]))
    hmain = wd.fit.hmain or {}
    cond = {
        "exceeds_null_threshold": bool(rep["valid_r2"] > thr),
        "seed_stability": bool(reported["selection_fraction"] >= MIN_SELECTION_FRACTION),
        "complexity_within_budget": bool(complexity <= MAX_COMPLEXITY),
        "numerically_valid": bool(rep["invalid_fraction"] <= MAX_INVALID_FRACTION),
        "non_empty_effective_support": bool(support),
        "reaches_ceiling_fraction": bool(
            (not ceiling_applicable) or ceiling_fraction >= MIN_CEILING_FRACTION),
        "h_main_not_rejected": bool(not hmain.get("h_main_rejected", False)),
        "falsification_passed": bool(harness["passed"]) if harness else False,
    }

    non_mass = bool(set(blocks) - {signature.MASS_BLOCK_NAME})
    claims_structure = bool(
        non_mass and harness is not None
        and harness.get("structural_beyond_mass_supported", False))

    return {
        "accepted": all(cond.values()),
        "conditions": cond,
        "failed_conditions": [k for k, v in cond.items() if not v],
        "null_threshold": thr,
        "valid_r2": rep["valid_r2"],
        "test_r2": float(test_r2),
        "ceiling_r2": float(ceiling_r2),
        "ceiling_fraction": ceiling_fraction,
        "ceiling_applicable": ceiling_applicable,
        "complexity": complexity,
        "selection_fraction": reported["selection_fraction"],
        "effective_support": support,
        "effective_support_blocks": blocks,
        "symbolic_support": list(reported["symbolic_support"]),
        "exponents": reported["exponents"],
        "block_exponents": reported.get("block_exponents", {}),
        "signs": reported["signs"],
        "expr": rep["expr"],
        "n_distinct_algebraic_forms": reported["n_distinct_algebraic_forms"],
        "algebraic_form_identified": reported["algebraic_form_identified"],
        "h_main": hmain,
        "claims_non_mass_structure": claims_structure,
        "has_non_mass_support": non_mass,
        "mass_only": bool(support) and not non_mass,
    }
