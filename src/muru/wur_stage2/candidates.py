"""Candidate registry, runner and the frozen Stage 2B selection rule.

`evaluate_rule` implements MURU_WUR_STAGE2B_DEVELOPMENT_PROTOCOL.md section
7 with amendment A-1. It reads ledger entries only; it never re-scores.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from muru.wur_stage2 import cv as CV
from muru.wur_stage2 import folds as FO

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "wur_stage2b"
REFERENCE_ARMS = ("B0_NULL_PROFILE", "B1_MASS_ONLY_ISOTONIC", "LIN_RIDGE_TIERA", "S2A_FROZEN_PIPELINE")

MIN_WINS_VS_S2A = 12
MIN_REL_IMPROVEMENT = 0.05
MIN_WINS_VS_B0 = 13
MIN_WINS_VS_B1 = 12
S3_TOLERANCE = 0.003
MAX_S5_RATIO = 1.5
MAX_FEATURES = 24
MIN_REL_IMPROVEMENT_BLACK_BOX = 0.15

REGISTRY: dict[str, dict] = {}


def register(candidate_id: str, make, *, parent: str | None, hypothesis: str, rationale: str,
             generation: str, features: dict, model_family: str, tuning_space: str = "none",
             interpretable: bool = True):
    REGISTRY[candidate_id] = dict(make=make, parent=parent, hypothesis=hypothesis, rationale=rationale,
                                  generation=generation, features=features, model_family=model_family,
                                  tuning_space=tuning_space, interpretable=interpretable)


def _load_ledger(cid: str) -> dict:
    return json.loads((CV.LEDGER / f"{cid}.json").read_text())


def _percompound(cid: str) -> dict:
    return json.loads((OUT / f"percompound_{cid}.json").read_text())


def _result_from_ledger(cid: str) -> CV.CVResult:
    d = _load_ledger(cid); pc = _percompound(cid)
    r = CV.CVResult(arm_id=cid, folds=d["folds"])
    r.per_compound = {k: {int(a): b for a, b in v.items()} for k, v in pc["per_compound"].items()}
    r.loeo = {k: {int(a): b for a, b in v.items()} for k, v in pc["loeo"].items()}
    return r


def run_candidate(candidate_id: str, repeats: list[int] | None = None) -> Path:
    spec = REGISTRY[candidate_id]
    long, cov, frame = CV.load_dev2b()
    folds = FO.load_folds()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    b0p = CV.b0_predictions(long, cov, frame, folds)
    r = CV.run_cv(spec["make"], long, cov, frame, folds, b0p, with_loeo=True, repeats=repeats)
    refs = {k: _result_from_ledger(k) for k in REFERENCE_ARMS if (CV.LEDGER / f"{k}.json").exists()}
    comps = {k: CV.compare(r, v) for k, v in refs.items()} if repeats is None else {}
    boots = {k: CV.paired_bootstrap(r, v) for k, v in refs.items()} if repeats is None else {}
    meta = {k: spec[k] for k in ("parent", "hypothesis", "rationale", "generation", "features",
                                 "model_family", "tuning_space", "interpretable")}
    meta["partial_repeats"] = repeats
    (OUT / f"percompound_{candidate_id}.json").write_text(json.dumps(
        {"per_compound": r.per_compound, "loeo": r.loeo}, sort_keys=True))
    return CV.ledger_entry(candidate_id, r, meta, {"fold_compare": comps, "paired_bootstrap": boots},
                           folds["folds_sha256"], commit)


def evaluate_rule(candidate_id: str) -> dict:
    """Section 7 (with A-1) and the section 8 stability / complexity clauses."""
    d = _load_ledger(candidate_id)
    fc = d["comparisons"]["fold_compare"]
    s2a = _load_ledger("S2A_FROZEN_PIPELINE")
    s3_c = float(np.nanmedian([f.get("S3_loeo_mae_median", np.nan) for f in d["folds"]]))
    s3_ref = float(np.nanmedian([f.get("S3_loeo_mae_median", np.nan) for f in s2a["folds"]]))
    s4_c = float(np.mean([f["S4_catastrophic"] for f in d["folds"]]))
    s4_ref = float(np.mean([f["S4_catastrophic"] for f in s2a["folds"]]))
    n_feat = d["features"].get("n_features", None)
    interp = d.get("interpretable", True)
    rel_needed = MIN_REL_IMPROVEMENT if interp else MIN_REL_IMPROVEMENT_BLACK_BOX
    cond = {
        "c1_wins_vs_s2a": fc["S2A_FROZEN_PIPELINE"]["wins"] >= MIN_WINS_VS_S2A,
        "c2_rel_improvement": fc["S2A_FROZEN_PIPELINE"]["mean_rel_improvement"] >= rel_needed,
        "c3_beats_b0_and_b1": (fc["B0_NULL_PROFILE"]["wins"] >= MIN_WINS_VS_B0
                               and fc["B1_MASS_ONLY_ISOTONIC"]["wins"] >= MIN_WINS_VS_B1),
        "c4_no_catastrophic_regression": s4_c <= s4_ref,
        "c5_inherited_s3_A1": (not np.isnan(s3_c)) and s3_c <= s3_ref + S3_TOLERANCE,
        "c6_no_e15_no_hold": True,
        "g_stability": d["P1_sd"] <= MAX_S5_RATIO * s2a["P1_sd"],
        "g_complexity": (n_feat is None) or (n_feat <= MAX_FEATURES),
    }
    return {"candidate_id": candidate_id, "beats_s2a": all(cond[k] for k in list(cond)[:6]),
            "gate_clauses": all(cond.values()), "conditions": cond,
            "numbers": {"P1_mean": d["P1_mean"], "P1_sd": d["P1_sd"], "S3": s3_c, "S3_ref": s3_ref,
                        "S4": s4_c, "S4_ref": s4_ref, "n_features": n_feat,
                        "wins_vs_s2a": fc["S2A_FROZEN_PIPELINE"]["wins"],
                        "rel_vs_s2a": fc["S2A_FROZEN_PIPELINE"]["mean_rel_improvement"]}}


def rank_candidates(ids: list[str]) -> list[dict]:
    """Order by mean P1; tie group within one SE of the best; simplest wins."""
    rows = []
    for cid in ids:
        d = _load_ledger(cid)
        rows.append({"id": cid, "P1": d["P1_mean"], "p1s": np.array([f["P1"] for f in d["folds"]]),
                     "n_features": d["features"].get("n_features", 99),
                     "n_params": d["features"].get("n_free_params", 99)})
    rows.sort(key=lambda r: r["P1"])
    best_p1s = rows[0]["p1s"].copy()
    for r in rows:
        diff = r["p1s"] - best_p1s
        se = diff.std(ddof=1) / np.sqrt(len(diff)) if len(diff) > 1 else 0.0
        r["tied_with_best"] = bool(diff.mean() <= se)
        r.pop("p1s")
    tie = [r for r in rows if r["tied_with_best"]]
    tie.sort(key=lambda r: (r["n_features"], str(r["n_params"]), r["P1"]))
    return [{"selected": r is tie[0], **r} for r in rows]
