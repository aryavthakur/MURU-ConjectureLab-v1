"""Stage 2B cross-validation harness: frozen folds, metrics, reference arms.

Every arm and candidate implements `Arm`: fit on a training fold, predict a
held-out compound's mu at the pooled rungs from descriptors alone. Metrics
are those of MURU_WUR_STAGE2B_DEVELOPMENT_PROTOCOL.md section 5. The ledger
is append-only.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge

from muru.discovery import engine, grammar, protocol
from muru.discovery.estimate import ENERGY_SCALE, _fit_phi, _phi_eval, fit_collapse
from muru.paper_benchmark.adequacy import PRACTICAL_WIN_RATIO
from muru.paper_benchmark.rc5_adequacy import ProfileShape, fit_model, predict_model
from muru.paper_benchmark.rc5_estimate import FrozenPhi
from muru.wur_stage2 import folds as FO
from muru.wur_stage2 import selection as SEL
from muru.wur_stage2.world import POOLED_ENERGIES

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"
LEDGER = ART / "wur_stage2b" / "ledger"
CATASTROPHIC_FACTOR = 2.0
BOOT_N = 1000
BOOT_SEED = 20260911


# --------------------------------------------------------------- data --
def load_dev2b() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(long, cov, frame) of the Stage 2A pooled world, from committed CSVs."""
    d = ART / "wur_stage2a" / "A_POOLED_ALIGNED"
    long = pd.read_csv(d / "long_mu.csv")
    cov = pd.read_csv(d / "covariates.csv")
    frame = pd.read_csv(d / "compounds.csv")
    return long, cov, frame


def wide(long: pd.DataFrame, keys: list[str], energies=POOLED_ENERGIES) -> np.ndarray:
    p = long.pivot_table(index="group_key", columns="ce_numeric", values="mu")
    p = p.reindex(index=list(keys), columns=list(energies))
    return p.to_numpy(float)


# ---------------------------------------------------------------- arms --
class Arm:
    id: str = "ARM"
    complexity: dict = {"n_features": 0, "n_free_params": 0}

    def fit(self, long: pd.DataFrame, cov: pd.DataFrame, ctx: dict) -> None:
        raise NotImplementedError

    def predict_mu(self, cov: pd.DataFrame, energies=POOLED_ENERGIES) -> np.ndarray:
        raise NotImplementedError

    def confidence(self, cov: pd.DataFrame):
        return None

    def loeo_mae(self, keys: list[str], Y: np.ndarray, energies=POOLED_ENERGIES):
        """Within-compound leave-one-energy-out MAE of the arm's profile model."""
        return None

    def diagnostics(self) -> dict:
        return {}


class CollapseArm(Arm):
    """Shared profile from the training fold; g of a held-out compound from a
    descriptor model. Subclasses implement `fit_g` / `predict_log_g`."""

    def fit(self, long, cov, ctx):
        self.fit_ = fit_collapse(long, with_hmain=False)
        self.cov_train_ = cov.set_index("group_key").loc[self.fit_.compounds]
        self.log_g_train_ = np.log(self.fit_.g_hat)
        self.fit_g(self.cov_train_, self.log_g_train_, self.fit_.weights, ctx)

    def phi(self, u):
        return _phi_eval(self.fit_.phi_u, self.fit_.phi_v, u)

    def predict_mu(self, cov, energies=POOLED_ENERGIES):
        g = np.exp(self.predict_log_g(cov.set_index("group_key")))
        u = (np.asarray(energies, float) / ENERGY_SCALE)[None, :] / g[:, None]
        return self.phi(u)

    def frozen_phi(self) -> FrozenPhi:
        return FrozenPhi(knots=self.fit_.phi_u, values=self.fit_.phi_v, e_ref=ENERGY_SCALE,
                         n_knots=len(self.fit_.phi_u), n_training_compounds=len(self.fit_.compounds),
                         alternations=3)

    def loeo_mae(self, keys, Y, energies=POOLED_ENERGIES):
        shape = ProfileShape.from_phi(self.frozen_phi())
        e_all = np.asarray(energies, float)
        out = np.full(len(keys), np.nan)
        if not shape.usable:
            return out
        for i in range(len(keys)):
            obs = np.isfinite(Y[i])
            if obs.sum() < 3:
                continue
            e, y = e_all[obs], Y[i][obs]
            errs = []
            for j in range(len(e)):
                keep = np.ones(len(e), bool); keep[j] = False
                f = fit_model("M0", shape, e[keep], y[keep])
                if not f.ok:
                    errs = None; break
                errs.append(abs(y[j] - float(predict_model("M0", shape, np.array([e[j]]), f.params)[0])))
            if errs:
                out[i] = float(np.mean(errs))
        return out

    def fit_g(self, cov, log_g, w, ctx):
        raise NotImplementedError

    def predict_log_g(self, cov):
        raise NotImplementedError


class B0NullProfile(Arm):
    id = "B0_NULL_PROFILE"
    complexity = {"n_features": 0, "n_free_params": 5}

    def fit(self, long, cov, ctx):
        self.mean_ = long.groupby("ce_numeric")["mu"].mean()

    def predict_mu(self, cov, energies=POOLED_ENERGIES):
        m = np.array([self.mean_.get(float(e), np.nan) for e in energies])
        return np.tile(m, (len(cov), 1))

    def loeo_mae(self, keys, Y, energies=POOLED_ENERGIES):
        # a per-energy constant has nothing per compound to leave out; report
        # the plain absolute error so the number exists on the same scale
        m = np.array([self.mean_.get(float(e), np.nan) for e in energies])
        return np.nanmean(np.abs(Y - m[None, :]), axis=1)


class B1MassOnly(CollapseArm):
    id = "B1_MASS_ONLY_ISOTONIC"
    complexity = {"n_features": 1, "n_free_params": "isotonic"}

    def fit_g(self, cov, log_g, w, ctx):
        self.iso_ = IsotonicRegression(increasing="auto", out_of_bounds="clip")
        self.iso_.fit(cov["precursor_mz"].to_numpy(float), log_g, sample_weight=w)

    def predict_log_g(self, cov):
        return self.iso_.predict(cov["precursor_mz"].to_numpy(float))


class LinRidge(CollapseArm):
    id = "LIN_RIDGE_TIERA"
    complexity = {"n_features": 12, "n_free_params": 13}
    ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)

    def _X(self, cov):
        return np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c] for c in protocol.FEATURES])

    def fit_g(self, cov, log_g, w, ctx):
        X = self._X(cov)
        inner = FO.inner_folds(cov.reset_index(), ctx["outer_fold"]).to_numpy()
        best = None
        for a in self.ALPHAS:
            sse = 0.0
            for k in range(FO.INNER_K):
                tr, va = inner != k, inner == k
                m = Ridge(alpha=a).fit(X[tr], log_g[tr], sample_weight=w[tr])
                sse += float(np.sum(w[va] * (log_g[va] - m.predict(X[va])) ** 2))
            if best is None or sse < best[0]:
                best = (sse, a)
        self.alpha_ = best[1]
        self.model_ = Ridge(alpha=self.alpha_).fit(X, log_g, sample_weight=w)

    def predict_log_g(self, cov):
        return self.model_.predict(self._X(cov))

    def diagnostics(self):
        return {"alpha": self.alpha_}


class S2AFrozen(CollapseArm):
    """The pre-WUR pipeline per fold: inner 60/20/20-style split of the
    training fold by protocol.group_split, 30-seed PySR, frozen selector and
    gate. The representative predicts held-out g. A refusal or an empty
    front falls back to g = 1 (the geometric-mean scale), and is recorded."""
    id = "S2A_FROZEN_PIPELINE"
    complexity = {"n_features": 12, "n_free_params": "symbolic<=20"}

    def __init__(self, store_dir: Path, n_seeds: int | None = None):
        self.store_dir = store_dir
        self.n_seeds = n_seeds

    def fit_g(self, cov, log_g, w, ctx):
        from muru.discovery.checkpoint import Store
        wid = f"WUR2B|S2A|r{ctx['repeat']}f{ctx['outer_fold']}"
        cov = cov.reset_index()
        X = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c] for c in protocol.FEATURES])
        groups = cov["scaffold_group"].to_numpy()
        wd = protocol.WorldData(world_id=wid, variables=list(protocol.FEATURES), X=X,
                                y=np.exp(log_g), w=w, groups=groups,
                                split=protocol.group_split(groups, wid), fit=self.fit_,
                                long=None, cov=cov)
        seeds = protocol.seed_list(wid)
        if self.n_seeds:
            seeds = seeds[:self.n_seeds]
        store = Store(self.store_dir)
        per_seed = {}
        for s in seeds:
            if not store.done("s2a", wid, s):
                cands = protocol.run_seed(wd, s, which="pysr")
                store.write("s2a", wid, s, {"seed": s, "candidates": [c.as_dict() for c in cands]})
            data = store.read("s2a", wid, s)
            cands = []
            for c in data["candidates"]:
                try:
                    expr = grammar.parse(c["expr_str"], list(wd.variables))
                except Exception:
                    continue
                cands.append(engine.Candidate(
                    expr_str=c["expr_str"], expr=expr, complexity=grammar.complexity(expr),
                    support=tuple(c["support"]), engine="pysr", seed=c["seed"],
                    train_r2=float(c["train_r2"]), valid_r2=float(c["valid_r2"]),
                    invalid_fraction=float(c["invalid_fraction"]), valid=bool(c["valid"])))
            per_seed[s] = cands
        cache = SEL.candidate_cache(wid, wd, per_seed, seeds)
        self.sel_ = SEL.select_and_gate(cache)
        self.expr_ = grammar.parse(self.sel_["expr"], list(protocol.FEATURES)) if self.sel_.get("expr") else None

    def predict_log_g(self, cov):
        if self.expr_ is None:
            return np.zeros(len(cov))
        X = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c] for c in protocol.FEATURES])
        pred, ok = grammar.evaluate(self.expr_, list(protocol.FEATURES), X)
        pred = np.where(ok & np.isfinite(pred) & (pred > 0), pred, 1.0)
        return np.log(pred)

    def diagnostics(self):
        return {"report": self.sel_["report"], "expr": self.sel_.get("expr"),
                "gate": self.sel_["gate"]["features"], "complexity": self.sel_.get("complexity"),
                "valid_r2": self.sel_.get("valid_r2")}


# ------------------------------------------------------------- metrics --
def per_compound_rmse(pred: np.ndarray, Y: np.ndarray) -> np.ndarray:
    d = np.where(np.isfinite(Y), pred - Y, np.nan)
    return np.sqrt(np.nanmean(d ** 2, axis=1))


def fold_metrics(pred: np.ndarray, Y: np.ndarray, pred_b0: np.ndarray,
                 sources: np.ndarray, energies=POOLED_ENERGIES) -> dict:
    d = np.where(np.isfinite(Y), pred - Y, np.nan)
    rc = per_compound_rmse(pred, Y)
    rb = per_compound_rmse(pred_b0, Y)
    out = {"P1": float(np.sqrt(np.nanmean(d ** 2))),
           "n_compounds": int(len(Y)), "n_cells": int(np.isfinite(Y).sum()),
           "S1_per_energy": {str(float(e)): float(np.sqrt(np.nanmean(d[:, j] ** 2)))
                             for j, e in enumerate(energies)},
           "S1_per_source": {str(s): float(np.sqrt(np.nanmean(d[sources == s] ** 2)))
                             for s in np.unique(sources)},
           "S2_descriptor_practical_win": float(np.nanmean(rc <= PRACTICAL_WIN_RATIO * rb)),
           "S4_catastrophic": float(np.nanmean(rc > CATASTROPHIC_FACTOR * rb)),
           "median_compound_rmse": float(np.nanmedian(rc))}
    return out


# ------------------------------------------------------------- runner --
@dataclass
class CVResult:
    arm_id: str
    folds: list[dict] = field(default_factory=list)
    per_compound: dict = field(default_factory=dict)      # key -> {repeat: rmse}
    loeo: dict = field(default_factory=dict)              # key -> {repeat: mae}
    seconds: float = 0.0

    def p1_vector(self) -> np.ndarray:
        return np.array([f["P1"] for f in self.folds], float)


def run_cv(make_arm, long: pd.DataFrame, cov: pd.DataFrame, frame: pd.DataFrame,
           folds: dict, b0_preds: dict | None = None, with_loeo: bool = True,
           repeats: list[int] | None = None) -> CVResult:
    """Run one arm over the frozen folds. `b0_preds[(repeat, fold)]` supplies
    the null-profile predictions the S2/S4 metrics are relative to; when
    absent the arm is B0 itself."""
    t0 = time.time()
    res = CVResult(arm_id=make_arm().id)
    keys_all = frame["group_key"].to_numpy()
    src = frame.set_index("group_key")["source"]
    for rep in folds["repeats"]:
        if repeats is not None and rep["repeat"] not in repeats:
            continue
        assign = pd.Series(rep["assignment"])
        for k in range(folds["k"]):
            held = sorted(assign.index[assign == k])
            train = sorted(assign.index[assign != k])
            arm = make_arm()
            arm.fit(long[long["group_key"].isin(train)],
                    cov[cov["group_key"].isin(train)],
                    {"repeat": rep["repeat"], "outer_fold": k})
            cov_h = cov.set_index("group_key").loc[held].reset_index()
            Y = wide(long, held)
            pred = arm.predict_mu(cov_h)
            pb0 = b0_preds[(rep["repeat"], k)] if b0_preds else pred
            m = fold_metrics(pred, Y, pb0, src.loc[held].to_numpy())
            m.update(repeat=rep["repeat"], fold=k, diagnostics=arm.diagnostics())
            rc = per_compound_rmse(pred, Y)
            for key, v in zip(held, rc):
                res.per_compound.setdefault(key, {})[rep["repeat"]] = float(v)
            conf = arm.confidence(cov_h)
            if conf is not None:
                conf = np.asarray(conf, float)
                ok = np.isfinite(conf) & np.isfinite(rc)
                from scipy.stats import spearmanr
                rho = float(spearmanr(conf[ok], rc[ok]).statistic) if ok.sum() >= 3 else float("nan")
                thr = np.quantile(conf[ok], 0.2)
                keep = ok & (conf >= thr)
                d_keep = np.where(np.isfinite(Y[keep]), pred[keep] - Y[keep], np.nan)
                m["S8_confidence"] = {"spearman_conf_vs_rmse": rho,
                                      "P1_top80": float(np.sqrt(np.nanmean(d_keep ** 2))),
                                      "abstained_fraction": float(1 - keep.sum() / max(1, ok.sum()))}
            if with_loeo:
                lo = arm.loeo_mae(held, Y)
                if lo is not None:
                    m["S3_loeo_mae_median"] = float(np.nanmedian(lo))
                    for key, v in zip(held, lo):
                        res.loeo.setdefault(key, {})[rep["repeat"]] = float(v)
            res.folds.append(m)
            if b0_preds is not None and arm.id == "B0_NULL_PROFILE":
                pass
            res._last_pred = (rep["repeat"], k, pred)
    res.seconds = time.time() - t0
    return res


def b0_predictions(long, cov, frame, folds) -> dict:
    out = {}
    for rep in folds["repeats"]:
        assign = pd.Series(rep["assignment"])
        for k in range(folds["k"]):
            held = sorted(assign.index[assign == k])
            train = sorted(assign.index[assign != k])
            arm = B0NullProfile()
            arm.fit(long[long["group_key"].isin(train)], None, {})
            out[(rep["repeat"], k)] = arm.predict_mu(cov.set_index("group_key").loc[held].reset_index())
    return out


# ------------------------------------------------------------ compare --
def compare(c: CVResult, ref: CVResult) -> dict:
    """Paired fold comparison per protocol section 7."""
    pc, pr = c.p1_vector(), ref.p1_vector()
    d = pc - pr
    rel = (pr - pc) / pr
    return {"ref": ref.arm_id, "n_folds": int(len(d)),
            "wins": int((pc < pr).sum()),
            "mean_rel_improvement": float(rel.mean()),
            "mean_diff": float(d.mean()), "se_diff": float(d.std(ddof=1) / np.sqrt(len(d))),
            "mean_P1": float(pc.mean()), "ref_mean_P1": float(pr.mean()),
            "sd_P1": float(pc.std(ddof=1)), "ref_sd_P1": float(pr.std(ddof=1))}


def paired_bootstrap(c: CVResult, ref: CVResult, seed: int = BOOT_SEED, n: int = BOOT_N,
                     level: float = 0.95) -> dict:
    keys = sorted(set(c.per_compound) & set(ref.per_compound))
    reps = sorted({r for k in keys for r in c.per_compound[k]})
    rng = np.random.default_rng(seed)
    out = {}
    for r in reps:
        dc = np.array([c.per_compound[k][r] - ref.per_compound[k][r] for k in keys if r in c.per_compound[k] and r in ref.per_compound[k]])
        idx = rng.integers(0, len(dc), size=(n, len(dc)))
        m = dc[idx].mean(1)
        a = (1 - level) / 2 * 100
        out[str(r)] = {"mean_diff": float(dc.mean()), "ci": np.percentile(m, [a, 100 - a]).tolist(), "n": int(len(dc))}
    return out


# ------------------------------------------------------------- ledger --
def ledger_entry(candidate_id: str, result: CVResult, meta: dict, comparisons: dict,
                 folds_sha: str, code_commit: str) -> Path:
    LEDGER.mkdir(parents=True, exist_ok=True)
    path = LEDGER / f"{candidate_id}.json"
    if path.exists():
        raise FileExistsError(f"ledger entry {candidate_id} exists; entries are immutable")
    payload = {"candidate_id": candidate_id, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "code_commit": code_commit, "folds_sha256": folds_sha, **meta,
               "folds": result.folds, "P1_mean": float(result.p1_vector().mean()),
               "P1_sd": float(result.p1_vector().std(ddof=1)) if len(result.folds) > 1 else None,
               "comparisons": comparisons, "seconds": result.seconds}
    text = json.dumps(payload, indent=1, sort_keys=True, default=_default)
    path.write_text(text + "\n")
    return path


def _default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))
