"""Stage 2A execution: the frozen pre-WUR MURU on WUR development data.

Implements MURU_WUR_STAGE2A_EXECUTION_PROTOCOL.md sections 4 to 8. Every
step is frozen code called through thin glue; the only Stage-2-specific
logic is population assembly (population.py, world.py), the fraction rule
(adequacy_fraction.py) and reporting.
"""
from __future__ import annotations

import hashlib
import json
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from muru.discovery import engine, grammar, protocol
from muru.discovery.checkpoint import Store
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.paper_benchmark.adequacy import CompoundContrastRecord
from muru.paper_benchmark.rc5_estimate import fit_case_phi
from muru.wur_stage2 import adequacy_fraction as AF
from muru.wur_stage2 import population as POP
from muru.wur_stage2 import selection as SEL
from muru.wur_stage2 import world as W

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"
OUT = ART / "wur_stage2a"
BOOT_N = 1000
BOOT_SEED = 20260911
ANALYSES = ("A_POOLED_ALIGNED", "B_WUR_NATIVE", "C_LCSB_NATIVE")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=_json_default) + "\n")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(type(o))


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(max(0.0, c - h)), float(min(1.0, c + h))]


# ------------------------------------------------------------ populations --
def assemble(data_dir: Path) -> dict:
    """Every input table for the three analyses, with the population census."""
    gate = json.loads((ART / "wur_bridge_gate.json").read_text())
    a, b = float(gate["alignment"]["a"]), float(gate["alignment"]["b"])

    lcsb_mu = POP.lcsb_dev_mu_table()
    lcsb_cov = POP.lcsb_dev_covariates()
    dev = POP.wur_dev_partition(data_dir)
    acc, ident = POP.wur_analysis_accepted(data_dir, dev)
    wur_mu = POP.wur_mu(acc, data_dir)
    wur_cov, cov_failures = POP.wur_covariates(acc, ident)

    pop_b = json.loads((ART / "wur_bridge_gate.json").read_text())["population_b"]
    pop_b_keys = set(pop_b.get("connectivity_keys", []))
    ana_keys = set(ident["connectivity_key"])
    # population B lies entirely in touching groups, hence entirely in ANALYSIS
    if pop_b_keys and not pop_b_keys <= ana_keys:
        raise POP.PopulationError("population B is not entirely inside WUR-DEV-ANALYSIS")

    wur_aligned = W.aligned_wur_long(wur_mu, a, b)
    lcsb_long = W.native_long(lcsb_mu, "LCSB")
    pooled, pool_census = W.pooled_long(lcsb_long, wur_aligned)
    pooled_cov = W.pooled_covariates(lcsb_cov, wur_cov, set(pooled["group_key"]))

    census = {
        "lcsb_dev": {"n_keys": int(lcsb_mu["connectivity_key"].nunique()),
                     "n_scaffold_groups": int(lcsb_cov["scaffold_group"].nunique()),
                     "keys_sha256": canonical_key_hash(sorted(set(lcsb_mu["connectivity_key"]))),
                     "rungs_per_key": lcsb_mu.groupby("connectivity_key").size().value_counts().to_dict()},
        "wur_dev_analysis": {"n_keys": int(wur_mu["connectivity_key"].nunique()),
                             "n_scaffold_groups": int(ident["scaffold_group"].nunique()),
                             "keys_sha256": canonical_key_hash(sorted(set(wur_mu["connectivity_key"]))),
                             "n_spectra": int(len(acc)),
                             "n_cells": int(len(wur_mu)),
                             "spectra_per_cell": wur_mu["n_spectra"].value_counts().to_dict(),
                             "descriptor_failures": cov_failures},
        "population_b_in_analysis": int(len(pop_b_keys & ana_keys)),
        "pooled": pool_census,
        "energy_map": {"a": a, "b": b, "direction": gate["alignment"]["form"],
                       "pooled_rungs": list(W.POOLED_ENERGIES),
                       "mapped_targets": {str(e): a + b * e for e in W.POOLED_ENERGIES}},
    }
    return {"lcsb_mu": lcsb_mu, "lcsb_cov": lcsb_cov, "wur_mu": wur_mu,
            "wur_cov": wur_cov, "wur_ident": ident, "pooled": pooled,
            "pooled_cov": pooled_cov, "census": census, "map": (a, b)}


def analysis_inputs(name: str, T: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    if name == "A_POOLED_ALIGNED":
        return T["pooled"], T["pooled_cov"]
    if name == "B_WUR_NATIVE":
        return W.native_long(T["wur_mu"], "WUR"), T["wur_cov"]
    if name == "C_LCSB_NATIVE":
        return W.native_long(T["lcsb_mu"], "LCSB"), T["lcsb_cov"]
    raise ValueError(name)


# ----------------------------------------------------------------- steps --
def collapse_record(wd: protocol.WorldData) -> dict:
    f = wd.fit
    return {"n_compounds": int(len(f.compounds)), "resid_sd": float(f.resid_sd),
            "hmain": f.hmain, "n_energies_per_compound": np.bincount(f.n_energies).tolist(),
            "g_hat_summary": {"min": float(f.g_hat.min()), "median": float(np.median(f.g_hat)),
                              "max": float(f.g_hat.max()),
                              "log_sd": float(np.std(np.log(f.g_hat)))},
            "weights_summary": {"min": float(f.weights.min()), "max": float(f.weights.max())},
            "phi_u": [float(x) for x in f.phi_u], "phi_v": [float(x) for x in f.phi_v]}


def ladder(name: str, wd: protocol.WorldData, frame: pd.DataFrame) -> dict:
    compounds = pd.DataFrame({"compound_id": frame["group_key"], "split": frame["split"]})
    traj = wd.long.rename(columns={"group_key": "compound_id", "ce_numeric": "energy"})
    traj = traj[["compound_id", "energy", "mu"]]
    phi = fit_case_phi(compounds, traj)
    result, records = AF.run_case_adequacy_fraction(name, compounds, traj, phi)
    per_detector = {d: AF.contrast_summary(r) for d, r in result.contrasts.items()}
    for d in per_detector:
        n, k = per_detector[d]["n_test"], per_detector[d]["practical_wins"]
        per_detector[d]["win_fraction_wilson95"] = wilson(k, n)
        per_detector[d]["evaluable_fraction_wilson95"] = wilson(per_detector[d]["evaluable"], n)
    recs = {d: [r.__dict__ for r in rs] for d, rs in records.items()}
    # per-energy M0 LOEO absolute error on test compounds is not exposed by the
    # frozen contrast; the M0 mae over held-out energies is, per compound.
    return {"status": result.status.value, "fired": list(result.fired),
            "blocker": result.blocker, "boundary_counts": dict(result.boundary_counts),
            "n_train_for_phi": phi.n_training_compounds,
            "phi": phi.identity(), "per_detector": per_detector, "records": recs}


def search(wd: protocol.WorldData, store: Store, block: str) -> tuple[dict, list[int], list[dict]]:
    seeds = protocol.seed_list(wd.world_id)
    failures = []
    for s in store.pending(block, wd.world_id, seeds):
        try:
            cands = protocol.run_seed(wd, s, which="pysr")
        except Exception:
            failures.append({"seed": int(s), "error": traceback.format_exc()})
            continue
        store.write(block, wd.world_id, s, {"seed": int(s), "engine": "pysr",
                                            "candidates": [c.as_dict() for c in cands]})
    per_seed = {}
    for s in seeds:
        if not store.done(block, wd.world_id, s):
            continue
        data = store.read(block, wd.world_id, s)
        cands = []
        for c in data["candidates"]:
            try:
                expr = grammar.parse(c["expr_str"], list(wd.variables))
            except Exception:
                continue
            cands.append(engine.Candidate(
                expr_str=c["expr_str"], expr=expr, complexity=grammar.complexity(expr),
                support=tuple(c["support"]), engine=c["engine"], seed=c["seed"],
                train_r2=float(c["train_r2"]), valid_r2=float(c["valid_r2"]),
                invalid_fraction=float(c["invalid_fraction"]), valid=bool(c["valid"])))
        per_seed[s] = cands
    return per_seed, seeds, failures


def bootstrap(wd: protocol.WorldData, frame: pd.DataFrame, lad: dict, sel: dict) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    test_ids = list(frame.loc[frame["split"] == "test", "group_key"])
    n = len(test_ids)
    out = {"n_boot": BOOT_N, "seed": BOOT_SEED, "n_test": n}
    # ladder fractions
    for d, recs in lad["records"].items():
        from muru.paper_benchmark.adequacy import classify_compound_contrast, CompoundContrastStatus
        st = np.array([classify_compound_contrast(CompoundContrastRecord(**r)).value for r in recs])
        ev = np.isin(st, ["PRACTICAL_WIN", "NO_PRACTICAL_WIN"]).astype(float)
        wn = (st == "PRACTICAL_WIN").astype(float)
        idx = rng.integers(0, n, size=(BOOT_N, n))
        out[d] = {"evaluable_fraction_ci95": np.percentile(ev[idx].mean(1), [2.5, 97.5]).tolist(),
                  "win_fraction_ci95": np.percentile(wn[idx].mean(1), [2.5, 97.5]).tolist()}
    # representative test R2
    if sel.get("expr"):
        X, y, w = wd.part("test")
        expr = grammar.parse(sel["expr"], list(wd.variables))
        pred, ok = grammar.evaluate(expr, list(wd.variables), X)
        vals = []
        for _ in range(BOOT_N):
            idx = rng.integers(0, n, size=n)
            vals.append(engine.weighted_r2(y[idx], pred[idx], w[idx], ok[idx]))
        vals = np.array(vals, float)
        vals = vals[np.isfinite(vals)]
        out["rep_test_r2_weighted_ci95"] = (np.percentile(vals, [2.5, 97.5]).tolist()
                                            if len(vals) else None)
    return out


def descriptives(wd: protocol.WorldData, name: str, T: dict) -> dict:
    long = wd.long
    per_e = {}
    for e, g in long.groupby("ce_numeric"):
        per_e[str(float(e))] = {"n": int(len(g)), "median": float(g["mu"].median()),
                                "q25": float(g["mu"].quantile(.25)),
                                "q75": float(g["mu"].quantile(.75)),
                                "by_source": g.groupby("source")["mu"].median().to_dict()}
    out = {"per_energy_mu": per_e}
    if name == "A_POOLED_ALIGNED":
        w15 = T["wur_mu"][T["wur_mu"]["ce_numeric"] == 15.0]["mu"]
        l15 = T["lcsb_mu"][T["lcsb_mu"]["ce_numeric"] == 15.0]["mu"]
        out["e15_separate"] = {
            "note": "E = 15 is excluded from every pooled fit (erratum E-3); "
                    "native values reported descriptively only",
            "wur_native_e15": {"n": int(len(w15)), "median": float(w15.median()),
                               "q25": float(w15.quantile(.25)), "q75": float(w15.quantile(.75))},
            "lcsb_native_e15": {"n": int(len(l15)), "median": float(l15.median()),
                                "q25": float(l15.quantile(.25)), "q75": float(l15.quantile(.75))}}
    return out


# ------------------------------------------------------------------ main --
def run_analysis(name: str, T: dict, out_dir: Path) -> dict:
    t0 = time.time()
    long, cov = analysis_inputs(name, T)
    wd, frame = W.build_world(name, long, cov)
    frame.to_csv(out_dir / "compounds.csv", index=False)
    wd.long.to_csv(out_dir / "long_mu.csv", index=False)
    wd.cov.to_csv(out_dir / "covariates.csv", index=False)
    pd.DataFrame({"group_key": wd.fit.compounds, "g_hat": wd.fit.g_hat,
                  "g_var": wd.fit.g_var, "weight": wd.w, "split": wd.split}
                 ).to_csv(out_dir / "collapse_g.csv", index=False)
    rec = {"analysis": name, "world_id": wd.world_id,
           "population": {"n_compounds": int(len(frame)),
                          "n_scaffold_groups": int(frame["scaffold_group"].nunique()),
                          "keys_sha256": canonical_key_hash(sorted(frame["group_key"])),
                          "split_counts": frame["split"].value_counts().to_dict(),
                          "split_groups": frame.groupby("split")["scaffold_group"].nunique().to_dict(),
                          "by_source": frame["source"].value_counts().to_dict(),
                          "energies": sorted(float(e) for e in wd.long["ce_numeric"].unique())},
           "collapse": collapse_record(wd), "descriptives": descriptives(wd, name, T)}
    _dump(out_dir / "collapse.json", rec["collapse"])

    rec["ladder"] = ladder(name, wd, frame)
    _dump(out_dir / "ladder.json", rec["ladder"])

    store = Store(out_dir / "ckpt")
    per_seed, seeds, failures = search(wd, store, "stage2a_pysr")
    cache = SEL.candidate_cache(wd.world_id, wd, per_seed, seeds)
    _dump(out_dir / "candidate_cache.json", cache)
    sel = SEL.select_and_gate(cache)
    if sel.get("expr"):
        sel["heldout_test"] = SEL.score_on_part(sel["expr"], wd, "test")
        sel["heldout_valid"] = SEL.score_on_part(sel["expr"], wd, "valid")
        sel["train"] = SEL.score_on_part(sel["expr"], wd, "train")
    band_test = []
    for m in cache["members"]:
        try:
            band_test.append({"seed": m["seed"], "expr": m["expr"], "complexity": m["complexity"],
                              "valid_r2": m["valid_r2"], "cluster": m["cluster"],
                              **{f"test_{k}": v for k, v in SEL.score_on_part(m["expr"], wd, "test").items()
                                 if k in ("r2_weighted", "r2_unweighted", "spearman")}})
        except Exception as exc:  # reporting only; never alters selection
            band_test.append({"seed": m["seed"], "expr": m["expr"], "error": repr(exc)})
    rec["search"] = {"n_seeds_planned": len(seeds), "n_seeds_done": len(per_seed),
                     "failures": failures, "seeds": seeds}
    rec["selection"] = sel
    rec["band_members_heldout"] = band_test
    rec["bootstrap"] = bootstrap(wd, frame, rec["ladder"], sel)
    rec["seconds"] = time.time() - t0
    _dump(out_dir / "selection.json", {"selection": sel, "band_members_heldout": band_test,
                                       "bootstrap": rec["bootstrap"]})
    return rec


def main(data_dir: Path | None = None) -> dict:
    data_dir = data_dir or ROOT / "data" / "external" / "wur"
    OUT.mkdir(parents=True, exist_ok=True)
    T = assemble(data_dir)
    _dump(OUT / "population_census.json", T["census"])
    results = {"protocol": "wur-stage2a-1.0", "analyses": {}, "census": T["census"]}
    for name in ANALYSES:
        out_dir = OUT / name
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            rec = run_analysis(name, T, out_dir)
        except Exception:
            rec = {"analysis": name, "failed": True, "traceback": traceback.format_exc()}
        rec_light = {k: v for k, v in rec.items() if k not in ("ladder", "band_members_heldout")}
        if "ladder" in rec:
            rec_light["ladder"] = {k: v for k, v in rec["ladder"].items() if k != "records"}
        results["analyses"][name] = rec_light
        _dump(out_dir / "result.json", rec)
        print(f"[stage2a] {name}: "
              f"{'FAILED' if rec.get('failed') else rec['ladder']['status']} "
              f"gate={rec.get('selection', {}).get('report')} "
              f"{rec.get('seconds', 0):.0f}s", flush=True)
    manifest = {"environment": environment_provenance(ROOT),
                "files": {str(p.relative_to(ROOT)): _sha(p)
                          for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != "manifest.json"}}
    _dump(OUT / "manifest.json", manifest)
    results["manifest_sha256"] = _sha(OUT / "manifest.json")
    _dump(OUT / "stage2a_results.json", results)
    return results
