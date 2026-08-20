"""FRESH HOLDOUT — SINGLE TRUTH REVEAL and scoring.

Runs exactly once, only after fresh_holdout_predictions_frozen.json exists and
is hashed. Nothing in the algorithm may change after this point.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "artifacts" / "fresh_holdout"

SCORABLE_BLOCKS = {"G1A", "G1B", "G1C", "G3", "G4M"}


def main() -> int:
    import accopt_selectors as S
    import fh_lib as fh
    from muru.discovery import grammar, protocol
    from muru.objval import equiv, recovery as recmod, select as selmod, signature
    from muru.synth.generators import load_dev_covariates

    pred_path = ROOT / "fresh_holdout_predictions_frozen.json"
    assert pred_path.exists(), "predictions must be frozen before the reveal"
    pred_sha = hashlib.sha256(pred_path.read_bytes()).hexdigest()
    hashrec = json.loads((OUT / "predictions_frozen_hash.json").read_text())
    assert hashrec["sha256"] == pred_sha, "prediction freeze hash mismatch"

    preds = json.loads(pred_path.read_text())["predictions"]

    # ---------------------------- THE REVEAL -------------------------------
    truth = {w["world_id"]: w for w in json.loads(
        (ROOT / "fresh_holdout_truth_manifest.json").read_text())["worlds"]}

    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8,
                                              size=(len(Xreal), len(variables)))
    Zreal = selmod.lattice(Xreal, variables)
    Zsynth = selmod.lattice(Xsynth, variables)

    scored = {}
    for wid, p in sorted(preds.items()):
        tr = truth[wid]
        Z = Zsynth if p["family"] == "G1A" else Zreal
        row = dict(p)
        row["planted_expr"] = tr["planted_expr"]
        row["planted_support"] = tr["planted_support"]
        row["exactly_representable"] = tr.get("exactly_representable")
        row["scorable"] = False
        row["t_support"] = row["t_family"] = row["t_exact"] = False
        row["t_rel_rmse"] = float("nan")
        row["planted_blocks"] = None

        if p["block"] in SCORABLE_BLOCKS:
            params = recmod.freeze_constants(tr["family"], tr["params"],
                                             variables, Z)
            psig = recmod.planted_signature(tr["family"], params, variables, Z)
            if psig is not None:
                row["scorable"] = True
                row["planted_blocks"] = sorted(set(psig["effective_support_blocks"]))
                row["planted_variables"] = sorted(set(psig["effective_support"]))
                ev, _ = recmod.planted_evaluator(tr["family"], params, variables)
                pv, pok = ev(Z)
                if p["expr"] is not None:
                    e = grammar.parse(p["expr"], variables)
                    sg = signature.signature(e, variables, Z)
                    v, ok0 = signature._eval(e, variables, Z)
                    if sg["usable"]:
                        row["t_support"] = bool(
                            set(psig["effective_support_blocks"])
                            == set(sg["effective_support_blocks"]))
                        ok = pok & ok0
                        row["t_family"] = bool(equiv.same_family(
                            sg, psig, v, pv, ok)["same_family"])
                        fc = equiv.functional_class(pv, v, ok)
                        row["t_exact"] = bool(fc["functionally_equivalent"])
                        row["t_rel_rmse"] = float(fc["numeric"]["rel_rmse"])
        scored[wid] = row

    # ------------------------------ metrics --------------------------------
    def sub(**kw):
        out = []
        for wid, r in scored.items():
            if all(r.get(k) in (v if isinstance(v, (set, list)) else {v})
                   for k, v in kw.items()):
                out.append(r)
        return out

    pos = [r for r in scored.values() if r["category"] == "positive"]
    nul = [r for r in scored.values() if r["category"] == "null"]
    ref = [r for r in scored.values() if r["category"] == "refusal"]

    tp = sum(r["report"] for r in pos)
    fp = sum(r["report"] for r in nul)
    sens = tp / len(pos)
    fpr = fp / len(nul)
    sc = [r["gate"]["median_seed_best_r2"] for r in pos + nul]
    lab = [1] * len(pos) + [0] * len(nul)
    auc = S.auc_roc(sc, lab)

    rng = np.random.default_rng(20260820)
    boots = []
    scn, labn = np.asarray(sc, float), np.asarray(lab, int)
    for _ in range(2000):
        idx = rng.integers(0, len(scn), len(scn))
        if 0 < labn[idx].sum() < len(idx):
            boots.append(S.auc_roc(scn[idx], labn[idx]))
    auc_ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]

    def stratum(name, blocks, noise=None):
        ids = [r for r in scored.values() if r["block"] in blocks
               and r["scorable"] and (noise is None or r["noise_regime"] == noise)]
        d = {"n": len(ids)}
        for met in ("t_support", "t_family", "t_exact"):
            k = sum(1 for r in ids if r[met])
            kg = sum(1 for r in ids if r[met] and r["report"])
            d[met] = k
            d[met + "_rate"] = k / len(ids) if ids else float("nan")
            d[met + "_ci"] = S.wilson(k, len(ids)) if ids else [None, None]
            d[met + "_gated"] = kg
            d[met + "_gated_rate"] = kg / len(ids) if ids else float("nan")
            d[met + "_gated_ci"] = S.wilson(kg, len(ids)) if ids else [None, None]
        d["reported"] = sum(r["report"] for r in ids)
        d["median_rep_valid_r2"] = float(np.median(
            [r["valid_r2"] for r in ids if r["valid_r2"] is not None])) if ids else None
        return name, d

    strata = dict([
        stratum("all_positive", {"G1A", "G1B", "G1C"}),
        stratum("G1A", {"G1A"}), stratum("G1B", {"G1B"}), stratum("G1C", {"G1C"}),
        stratum("G1B_low", {"G1B"}, "low"),
        stratum("G1B_moderate", {"G1B"}, "moderate"),
        stratum("G1B_adverse", {"G1B"}, "adverse"),
        stratum("G1A_low", {"G1A"}, "low"),
        stratum("G1A_moderate", {"G1A"}, "moderate"),
        stratum("G1A_adverse", {"G1A"}, "adverse"),
    ])

    nulls_detail = {}
    for b in sorted({r["block"] for r in nul}):
        ids = [r for r in nul if r["block"] == b]
        nulls_detail[b] = {
            "n": len(ids), "reported": sum(r["report"] for r in ids),
            "fpr": sum(r["report"] for r in ids) / len(ids),
            "reported_with_non_mass_structure": sum(
                1 for r in ids if r["report"] and r["eff_blocks"]
                and set(r["eff_blocks"]) - {"MASS"}),
            "median_seed_best_r2_median": float(np.median(
                [r["gate"]["median_seed_best_r2"] for r in ids])),
        }
    ncal_by_construction = {}
    for wid, r in scored.items():
        if r["block"] != "NCAL":
            continue
        c = wid.split("|")[2]
        d = ncal_by_construction.setdefault(c, {"n": 0, "reported": 0,
                                                "reported_non_mass": 0})
        d["n"] += 1
        d["reported"] += int(r["report"])
        if r["report"] and r["eff_blocks"] and set(r["eff_blocks"]) - {"MASS"}:
            d["reported_non_mass"] += 1

    refusal_detail = {}
    for b in sorted({r["block"] for r in ref}):
        ids = [r for r in ref if r["block"] == b]
        refusal_detail[b] = {
            "n": len(ids), "reported": sum(r["report"] for r in ids),
            "reported_with_non_mass_structure": sum(
                1 for r in ids if r["report"] and r["eff_blocks"]
                and set(r["eff_blocks"]) - {"MASS"}),
            "support_recovered": sum(1 for r in ids if r["scorable"] and r["t_support"]),
            "n_scorable": sum(1 for r in ids if r["scorable"]),
        }

    # ---------------------------- failure taxonomy -------------------------
    for wid, r in scored.items():
        r["world_id"] = wid
    taxonomy, fail_rows = {}, []
    for wid, r in sorted(scored.items()):
        if r["category"] == "positive":
            if r["computational_failure"]:
                lbl = "COMPUTATIONAL_FAILURE"
            elif not r["scorable"]:
                lbl = "OTHER_UNSCORABLE"
            elif r["t_family"] and r["report"]:
                lbl = "OK"
            elif r["t_family"] and not r["report"]:
                lbl = "NULL_GATE_FALSE_NEGATIVE"
            elif not r["t_support"]:
                lbl = ("SEARCH_REPRESENTABILITY_FAILURE"
                       if not r.get("exactly_representable", True)
                       else "SUPPORT_ERROR")
            elif r["t_support"] and not r["t_family"]:
                lbl = ("FAMILY_AGGREGATION_ERROR" if r["n_clusters"] > 1
                       else "FAMILY_TOLERANCE_BOUNDARY_ERROR")
            else:
                lbl = "OTHER"
        elif r["category"] == "null":
            lbl = "NULL_FALSE_POSITIVE" if r["report"] else "OK_NULL_REJECTED"
        else:
            lbl = "REFUSAL_REPORTED" if r["report"] else "REFUSAL_WITHHELD"
        r["failure_class"] = lbl
        taxonomy[lbl] = taxonomy.get(lbl, 0) + 1
        if lbl not in ("OK", "OK_NULL_REJECTED", "REFUSAL_WITHHELD"):
            fail_rows.append({"world_id": wid, "class": lbl, "block": r["block"],
                              "noise": r["noise_regime"], "report": r["report"],
                              "expr": r["expr"], "eff_blocks": r["eff_blocks"],
                              "planted_blocks": r["planted_blocks"],
                              "planted_expr": r["planted_expr"],
                              "valid_r2": r["valid_r2"],
                              "t_support": r["t_support"],
                              "t_family": r["t_family"],
                              "gate": r["gate"]})

    ap = strata["all_positive"]
    ncf = sum(r["computational_failure"] for r in scored.values())
    primary = {
        "n_worlds": len(scored),
        "support_recovery_ungated": [ap["t_support"], ap["n"]],
        "support_recovery_ungated_rate": ap["t_support_rate"],
        "support_recovery_ungated_ci": ap["t_support_ci"],
        "support_recovery_end_to_end": [ap["t_support_gated"], ap["n"]],
        "support_recovery_end_to_end_rate": ap["t_support_gated_rate"],
        "support_recovery_end_to_end_ci": ap["t_support_gated_ci"],
        "family_recovery_ungated": [ap["t_family"], ap["n"]],
        "family_recovery_ungated_rate": ap["t_family_rate"],
        "family_recovery_ungated_ci": ap["t_family_ci"],
        "family_recovery_end_to_end": [ap["t_family_gated"], ap["n"]],
        "family_recovery_end_to_end_rate": ap["t_family_gated_rate"],
        "family_recovery_end_to_end_ci": ap["t_family_gated_ci"],
        "exact_recovery_ungated": [ap["t_exact"], ap["n"]],
        "G1A_family": [strata["G1A"]["t_family"], strata["G1A"]["n"]],
        "G1B_family": [strata["G1B"]["t_family"], strata["G1B"]["n"]],
        "G1C_family": [strata["G1C"]["t_family"], strata["G1C"]["n"]],
        "null_false_positive_rate": fpr,
        "null_fpr_counts": [fp, len(nul)],
        "null_fpr_ci": S.wilson(fp, len(nul)),
        "sensitivity": sens, "sensitivity_counts": [tp, len(pos)],
        "sensitivity_ci": S.wilson(tp, len(pos)),
        "specificity": 1 - fpr,
        "specificity_ci": S.wilson(len(nul) - fp, len(nul)),
        "balanced_accuracy": 0.5 * (sens + 1 - fpr),
        "roc_auc": auc, "roc_auc_bootstrap_ci": auc_ci,
        "pr_auc": S.auc_pr(sc, lab),
        "computational_failure_rate": ncf / len(scored),
        "computational_failures": ncf,
    }

    DEV = {"support_ungated": 55 / 56, "support_end_to_end": 54 / 56,
           "family_recovery": 47 / 56, "G1A_family": 6 / 6,
           "G1B_family": 35 / 40, "G1C_family": 6 / 10,
           "null_fpr": 7 / 230, "sensitivity": 0.9642857142857143,
           "specificity": 0.9695652173913043,
           "balanced_accuracy": 0.9669254658385094,
           "roc_auc": 0.9990683229813665}
    hold = {"support_ungated": ap["t_support_rate"],
            "support_end_to_end": ap["t_support_gated_rate"],
            "family_recovery": ap["t_family_rate"],
            "G1A_family": strata["G1A"]["t_family_rate"],
            "G1B_family": strata["G1B"]["t_family_rate"],
            "G1C_family": strata["G1C"]["t_family_rate"],
            "null_fpr": fpr, "sensitivity": sens, "specificity": 1 - fpr,
            "balanced_accuracy": 0.5 * (sens + 1 - fpr), "roc_auc": auc}
    comparison = {k: {"development": DEV[k], "fresh_holdout": hold[k],
                      "delta_pp": (hold[k] - DEV[k]) * 100}
                  for k in DEV}

    R = plan_rubric = json.loads(
        (ROOT / "FRESH_HOLDOUT_PLAN.json").read_text())["success_rubric"][
        "STRONG_GENERALIZATION_EVIDENCE"]
    rub = {
        "support_end_to_end_ge_0.90": hold["support_end_to_end"] >= R["support_end_to_end_ge"],
        "family_recovery_ge_0.70": hold["family_recovery"] >= R["family_recovery_ge"],
        "G1B_family_ge_0.75": hold["G1B_family"] >= R["G1B_family_ge"],
        "null_fpr_le_0.05": fpr <= R["null_fpr_le"],
        "roc_auc_ge_0.95": auc >= R["roc_auc_ge"],
        "comp_failure_rate_le_0.02":
            primary["computational_failure_rate"] <= R["computational_failure_rate_le"],
    }
    rub["all_numeric_criteria_met"] = all(rub.values())

    payload = {
        "phase": "SINGLE_TRUTH_REVEAL",
        "revealed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predictions_frozen_sha256": pred_sha,
        "truth_manifest_sha256": hashlib.sha256(
            (ROOT / "fresh_holdout_truth_manifest.json").read_bytes()).hexdigest(),
        "primary_metrics": primary,
        "development_vs_holdout": comparison,
        "strata": strata,
        "nulls": {"by_block": nulls_detail,
                  "ncal_by_construction": ncal_by_construction,
                  "overall_reported": fp, "overall_n": len(nul)},
        "refusal": refusal_detail,
        "failure_taxonomy": taxonomy,
        "failure_rows": fail_rows,
        "strong_rubric": rub,
        "r2_distributions": {
            "positive_median_seed_best_r2": sorted(
                round(r["gate"]["median_seed_best_r2"], 4) for r in pos),
            "null_median_seed_best_r2": sorted(
                round(r["gate"]["median_seed_best_r2"], 4) for r in nul),
            "refusal_median_seed_best_r2": sorted(
                round(r["gate"]["median_seed_best_r2"], 4) for r in ref),
        },
        "per_world": scored,
    }
    text = json.dumps(payload, indent=1, sort_keys=True, default=str)
    (OUT / "fresh_holdout_scored.json").write_text(text)
    print(json.dumps({"primary": primary, "comparison": comparison,
                      "rubric": rub, "taxonomy": taxonomy},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
