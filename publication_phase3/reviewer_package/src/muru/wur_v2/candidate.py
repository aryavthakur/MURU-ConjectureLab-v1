"""The v2 final candidate and its fair comparators, fit on the whole v2 population and serialized.

A serialized model is plain JSON (profile knots, standardization, coefficients,
configuration, provenance) plus nothing else, so it can be hashed and reloaded
without pickles. `predict_mu(model, smiles, precursor_mz, energies_lcsb)` needs only
structures, precursor m/z and energies in the LCSB nominal coordinate; an
external instrument supplies its own frozen adapter to that coordinate.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge

from muru.discovery import protocol
from muru.discovery.estimate import ENERGY_SCALE, _phi_eval
from muru.molecules import tier_a_descriptors
from muru.wur_v2 import engine as EN, folds as FO, models as MO, representations as R

CANDIDATE_ID = "V2_TA_MORGAN_JOINT"
CANARY_SMILES = ("CCN(CC)CC(=O)Nc1c(C)cccc1C", "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "CN1CCC[C@H]1c1cccnc1",
                 "CC(C)Cc1ccc(C(C)C(=O)O)cc1", "O=C(O)c1ccccc1O")
CANARY_MZ = (235.1805, 195.0877, 163.1230, 207.1380, 139.0390)


def feature_spec() -> dict:
    import rdkit
    return {"tier_a_features": list(protocol.FEATURES), "tier_a_scale": {k: protocol.SCALE[k] for k in protocol.FEATURES},
            "morgan": {"radius": R.MORGAN_RADIUS, "fp_size": R.FP_SIZE, "counts": True, "chirality": False, "transform": "log1p"},
            "rdkit_version": rdkit.__version__}


class ProvenanceError(RuntimeError):
    pass


def verify(model: dict) -> None:
    """Refuse to predict if the feature definition or the canary predictions no longer reproduce (review I-2)."""
    if "feature_spec" not in model:
        return
    spec = feature_spec()
    for k in ("tier_a_features", "tier_a_scale", "morgan"):
        if spec[k] != model["feature_spec"][k]:
            raise ProvenanceError(f"feature definition changed: {k}")
    got = _predict_log_g_raw(model, CANARY_SMILES, CANARY_MZ)
    if not np.allclose(got, model["canary_log_g"], rtol=0, atol=1e-9):
        raise ProvenanceError("canary log g predictions do not reproduce")


def _select(model, data, keys):
    """The engine's nested selection on the full population (inner grouped folds, inner collapse refits)."""
    ts = EN.trainset(data, keys, "scaffold_group", 0)
    fr = EN.run_fold(model, data, ts.keys, ts.keys[:1], "scaffold_group", 0)  # the test key is irrelevant to selection
    return ts, fr.cfg, fr.inner_loss


def fit_all(data: EN.Data) -> dict:
    keys = list(data.cov.index)
    out = {}
    joint = MO.JointRidge("MORGAN", "TA_MORGAN_JOINT")
    ts, cfg, loss = _select(joint, data, keys)
    m, stats, bw = joint.fit(ts, cfg)
    base = {"profile": {"knots_log_u": ts.fit.phi_u.tolist(), "values": ts.fit.phi_v.tolist(), "energy_scale": ENERGY_SCALE},
            "n_training": len(ts.keys), "training_keys_sha256": hashlib.sha256("\n".join(sorted(ts.keys)).encode()).hexdigest()}
    out[CANDIDATE_ID] = {**base, "kind": "joint_ridge", "cfg": {"alpha": cfg[0], "block_weight": cfg[1]}, "inner_loss": loss,
                         "tier_a_mean": stats[0].tolist(), "tier_a_sd": stats[1].tolist(),
                         "coef_tier_a": m.coef_[:12].tolist(), "coef_morgan": m.coef_[12:].tolist(), "intercept": float(m.intercept_)}
    ta = MO.RidgeModel("TIER_A", model_id="TA_RIDGE")
    ts2, cfg2, loss2 = _select(ta, data, keys)
    m2 = ta.fit(ts2, cfg2)
    out["V2_REF_TA_RIDGE"] = {**base, "kind": "tier_a_ridge", "cfg": {"alpha": cfg2}, "inner_loss": loss2,
                              "coef_tier_a": m2.coef_.tolist(), "intercept": float(m2.intercept_)}
    iso = IsotonicRegression(increasing="auto", out_of_bounds="clip").fit(
        data.cov.loc[ts.keys, "precursor_mz"].to_numpy(float), ts.log_g, sample_weight=ts.w)
    out["V2_REF_B1_MASS"] = {**base, "kind": "mass_isotonic", "x": iso.X_thresholds_.tolist(), "y": iso.y_thresholds_.tolist()}
    for name in ("V2_TA_MORGAN_JOINT", "V2_REF_TA_RIDGE", "V2_REF_B1_MASS"):
        out[name]["feature_spec"] = feature_spec()
        out[name]["canary_smiles"] = list(CANARY_SMILES)
        out[name]["canary_log_g"] = _predict_log_g_raw(out[name], CANARY_SMILES, CANARY_MZ).tolist()
    out["V2_REF_B0_NULL"] = {"kind": "null", "energies_lcsb": EN.POOLED_ENERGIES.tolist(),
                             "rung_means": data.Y.loc[keys].mean(0).tolist(), "n_training": len(keys)}
    return out


def features_for(smiles: list[str], precursor_mz: list[float]) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    for s, pm in zip(smiles, precursor_mz):
        d = tier_a_descriptors(s)
        if not d:
            raise ValueError(f"descriptor failure: {s}")
        d["precursor_mz"] = float(pm)
        rows.append([d[c] / protocol.SCALE[c] for c in protocol.FEATURES])
    mg = np.log1p(R.morgan_counts(pd.Series(smiles)).to_numpy())
    return np.array(rows, float), mg


def predict_log_g(model: dict, smiles, precursor_mz) -> np.ndarray:
    verify(model)
    return _predict_log_g_raw(model, smiles, precursor_mz)


def _predict_log_g_raw(model: dict, smiles, precursor_mz) -> np.ndarray:
    A, mg = features_for(list(smiles), list(precursor_mz))
    k = model["kind"]
    if k == "joint_ridge":
        Z = (A - np.array(model["tier_a_mean"])) / np.array(model["tier_a_sd"])
        return Z @ np.array(model["coef_tier_a"]) + model["cfg"]["block_weight"] * (mg @ np.array(model["coef_morgan"])) + model["intercept"]
    if k == "tier_a_ridge":
        return A @ np.array(model["coef_tier_a"]) + model["intercept"]
    if k == "mass_isotonic":
        return np.interp(np.asarray(precursor_mz, float), model["x"], model["y"])
    raise ValueError(k)


def predict_mu(model: dict, smiles, precursor_mz, energies_lcsb) -> np.ndarray:
    """mu at LCSB-coordinate energies; rows = compounds, columns = energies (a per-compound matrix is allowed)."""
    E = np.asarray(energies_lcsb, float)
    if model["kind"] == "null":
        grid = np.array(model["energies_lcsb"])
        means = np.array(model["rung_means"])
        vals = np.interp(E, grid, means)
        return np.broadcast_to(vals, (len(list(smiles)),) + E.shape[-1:]).copy() if E.ndim == 1 else vals
    lg = predict_log_g(model, smiles, precursor_mz)
    if E.ndim == 1:
        E = np.broadcast_to(E, (len(lg), len(E)))
    u = (E / model["profile"]["energy_scale"]) / np.exp(lg)[:, None]
    return _phi_eval(np.array(model["profile"]["knots_log_u"]), np.array(model["profile"]["values"]), u)


def supported(model: dict, smiles, precursor_mz, energies_lcsb) -> np.ndarray:
    """True where u = (E/30)/g_hat lies inside the frozen profile's knot range (review M-6)."""
    E = np.asarray(energies_lcsb, float)
    lg = predict_log_g(model, smiles, precursor_mz)
    if E.ndim == 1:
        E = np.broadcast_to(E, (len(lg), len(E)))
    u = (E / model["profile"]["energy_scale"]) / np.exp(lg)[:, None]
    lo, hi = profile_support_u(model)
    return (u >= lo) & (u <= hi)


def profile_support_u(model: dict) -> tuple[float, float]:
    k = np.array(model["profile"]["knots_log_u"])
    return float(np.exp(k[0])), float(np.exp(k[-1]))


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()
