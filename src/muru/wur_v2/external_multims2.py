"""MultiMS2 external validation: outcome-blind population definition, anchor calibration and the one look.

Population definition reads identity tables, the public file listing and
allowlisted mzML scan headers only (`external_mzml.scan_headers`). Peak arrays
are decoded only through `external_mzml.decode_selected` under an
`external_guard.AccessGuard`: kind ANCHOR_CALIBRATION for anchor spectra, kind
VALIDATION for the single validation run. Rules are those of
MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors

from muru.io.wur_provenance import canonical_key_hash
from muru.molecules import tier_a_descriptors
from muru.wur_v2 import external_mzml as X
from muru.wur_v2 import identity as ID

ROOT = Path(__file__).resolve().parents[3]
MZML = ROOT / "data/external/multims2_mzml"
OUT = ROOT / "artifacts/wur_v2/external"
PROTON = 1.007276
ADDUCT_SHIFTS = {"[M+H]+": 1.007276, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158}
C13 = 1.003355
ENERGIES = (20.0, 40.0, 60.0)
R2_TOL = 0.05
R3_TOL = 0.7
R4_LOWER_MAX = 50.0
R5_RANGE = (70.0, 1042.6)


def census_module():
    spec = importlib.util.spec_from_file_location("multims2_census", ROOT / "scripts/wur_v2/census/multims2_census.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_NOXIDE_O = Chem.MolFromSmarts("[O-;$([O-][N+;!$([N+]=O)])]")


def neutral_scaffold(smiles: str, key: str) -> str:
    """Scaffold after removing N-oxide oxygens and formal charges (rule R7, leakage finding L-03)."""
    m = ID.parent_mol(smiles)
    if m is None:
        return f"__UNPARSED__{key}"
    try:
        m = Chem.DeleteSubstructs(m, _NOXIDE_O)
        for a in m.GetAtoms():
            if a.GetFormalCharge() != 0:
                a.SetFormalCharge(0)
                a.SetNoImplicit(False)
                a.SetNumExplicitHs(0)
        Chem.SanitizeMol(m)
        return ID.scaffold_group_v2(Chem.MolToSmiles(m), key)
    except Exception:
        return ID.scaffold_group_v2(smiles, key)


def mh(smiles: str) -> float:
    m = ID.parent_mol(smiles)
    return float(Descriptors.ExactMolWt(m)) + PROTON if m is not None else float("nan")


def file_index() -> pd.DataFrame:
    rows = []
    for p in sorted(MZML.rglob("*.mzML")):
        s = p.stem
        coll = "NEXUS" if "_nexus_" in s.lower() else ("SELLECK" if "_selleck_" in s.lower() else "OTHER")
        e = re.search(r"_CID_(\d+)(?:ev|eV)", s)
        rows.append({"path": str(p.relative_to(ROOT)), "file": p.name, "stem": s, "collection": coll,
                     "energy": float(e.group(1)) if e else np.nan, "blank": "blank" in s.lower()})
    return pd.DataFrame(rows)


def build_headers(files: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for r in files.itertuples(index=False):
        h = pd.DataFrame(X.scan_headers(ROOT / r.path))
        h["file"] = r.file
        parts.append(h)
    return pd.concat(parts, ignore_index=True)


def populations(headers: pd.DataFrame, files: pd.DataFrame) -> dict:
    cm = census_module()
    listing = cm.load_listing()
    design, _ = cm.load_design(listing)
    census = json.loads((ROOT / "artifacts/wur_v2/external_census/multims2_census.json").read_text())
    surv = census["design_frame"]["chains"]["CID_3RUNG_20_40_60"]["survivors"]
    s10 = set(surv["step10_scaffold_new"]["keys"] if isinstance(surv["step10_scaffold_new"], dict) else surv["step10_scaffold_new"])
    s8 = set(surv["step8_no_exact_overlap"]["keys"] if isinstance(surv["step8_no_exact_overlap"], dict) else surv["step8_no_exact_overlap"])
    v2 = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv").set_index("group_key")
    long = pd.read_csv(ROOT / "artifacts/wur_v2/data/long_aligned.csv")
    five = set(long.groupby("group_key").ce_numeric.nunique().pipe(lambda s: s[s == 5]).index)
    dev_scaffolds = set(v2.scaffold_group) | {neutral_scaffold(s, k) for k, s in v2.smiles.items()}

    d = design[design.collection.isin(["NEXUS", "SELLECK"]) & design.parse_ok].copy()
    d["mh"] = d.smiles.map(mh)
    ms2 = headers[(headers.ms_level == 2)].copy()
    ms2 = ms2.merge(files[["file", "stem", "collection", "energy", "blank"]], on="file")
    ms2 = ms2[~ms2.blank]
    # positions -> files (boundary-aware, as the census)
    pos_files = {}
    for (coll, pos), _ in d.groupby(["collection", "position"]):
        rx = cm.position_regex(pos)
        pos_files[(coll, pos)] = files[(files.collection == coll) & files.stem.map(lambda s: bool(rx.search(s)))]
    rows, spectra = [], []
    npos = d.groupby(["collection", "key"]).position.nunique()
    for r in d.itertuples(index=False):
        rec = {"key": r.key, "collection": r.collection, "position": r.position, "smiles": r.smiles, "mh": r.mh}
        pf = pos_files[(r.collection, r.position)]
        e_files = {e: pf[pf.energy == e] for e in ENERGIES}
        rec["R1_single_position_all_energies"] = bool(npos.loc[(r.collection, r.key)] == 1 and all(len(e_files[e]) == 1 for e in ENERGIES))
        others = d[(d.collection == r.collection) & (d.position == r.position) & (d.key != r.key)]
        cand = np.concatenate([[m + (s - PROTON) for s in ADDUCT_SHIFTS.values()] + [m + C13] for m in others.mh.to_numpy()]) if len(others) else np.array([])
        rec["R3_no_isolation_conflict"] = bool(not np.any(np.abs(cand - r.mh) <= R3_TOL))
        matched = {}
        ok2, ok4 = rec["R1_single_position_all_energies"], True
        if ok2:
            for e in ENERGIES:
                fn = e_files[e].file.iloc[0]
                sp = ms2[(ms2.file == fn) & ((ms2.selected_ion_mz - r.mh).abs() <= R2_TOL)]
                if len(sp) == 0:
                    ok2 = False
                    break
                if ((sp.scan_window_lower_limit > R4_LOWER_MAX) | (sp.scan_window_upper_limit < r.mh + 1)).any():
                    ok4 = False
                if (sp.collision_energy != e).any():
                    ok4 = False
                matched[e] = (fn, sp.spectrum_id.tolist())
        rec["R2_ms2_all_energies"] = ok2
        rec["R4_window_and_ce"] = bool(ok2 and ok4)
        rec["R5_mass_range"] = bool(R5_RANGE[0] <= r.mh <= R5_RANGE[1])
        rec["R6_features"] = bool(tier_a_descriptors(r.smiles))
        rec["R7_neutral_scaffold_new"] = neutral_scaffold(r.smiles, r.key) not in dev_scaffolds
        rec["scaffold_group"] = ID.scaffold_group_v2(r.smiles, r.key)
        rec["in_step10"] = r.key in s10
        rec["in_step8"] = r.key in s8
        rec["in_v2_five_rung"] = r.key in v2.index and r.key in five
        rows.append(rec)
        for e, (fn, ids) in matched.items():
            for sid in ids:
                spectra.append({"key": r.key, "collection": r.collection, "position": r.position, "energy": e, "file": fn, "spectrum_id": sid})
    t = pd.DataFrame(rows)
    base = t.R1_single_position_all_energies & t.R2_ms2_all_energies & t.R3_no_isolation_conflict & t.R4_window_and_ce & t.R5_mass_range & t.R6_features
    t["VALIDATION"] = base & t.in_step10 & t.R7_neutral_scaffold_new
    t["ANCHOR"] = base & t.in_v2_five_rung
    t["SECONDARY"] = base & t.in_step8 & ~t.in_step10
    # a key can appear in both collections; keep one row per key per population, preferring NEXUS
    pops = {}
    for name in ("VALIDATION", "ANCHOR", "SECONDARY"):
        sub = t[t[name]].sort_values(["key", "collection"]).drop_duplicates("key")
        pops[name] = sub
    sp = pd.DataFrame(spectra)
    return {"table": t, "populations": pops, "spectra": sp}


def summarize(res: dict) -> dict:
    t = res["table"]
    out = {"n_design_rows_nexus_selleck": int(len(t)),
           "attrition_step10": {}, "attrition_anchor": {}}
    m = t.in_step10.copy()
    out["attrition_step10"]["step10_keys"] = int(t[m].key.nunique())
    for rule in ("R1_single_position_all_energies", "R3_no_isolation_conflict", "R2_ms2_all_energies", "R4_window_and_ce", "R5_mass_range", "R7_neutral_scaffold_new"):
        m = m & t[rule]
        out["attrition_step10"][rule] = int(t[m].key.nunique())
    a = t.in_v2_five_rung.copy()
    out["attrition_anchor"]["v2_five_rung_keys"] = int(t[a].key.nunique())
    for rule in ("R1_single_position_all_energies", "R3_no_isolation_conflict", "R2_ms2_all_energies", "R4_window_and_ce", "R5_mass_range"):
        a = a & t[rule]
        out["attrition_anchor"][rule] = int(t[a].key.nunique())
    for name, sub in res["populations"].items():
        out[name] = {"n_compounds": int(len(sub)), "n_scaffold_groups": int(sub.scaffold_group.nunique()),
                     "keys_sha256": canonical_key_hash(sub.key), "by_collection": sub.collection.value_counts().to_dict(),
                     "n_matched_spectra": int(res["spectra"].merge(sub[["key", "collection", "position"]], on=["key", "collection", "position"]).shape[0])}
    return out


# --------------------------------------------------------------------------- outcome access (guarded)
def spectrum_mu(mz: np.ndarray, intensity: np.ndarray, m_prec: float) -> float:
    """Protocol section 3: all centroid peaks, precursor included, theoretical [M+H]+ normalizer."""
    if mz.size == 0 or intensity.sum() <= 0:
        return float("nan")
    return float((intensity * mz).sum() / intensity.sum() / m_prec)


def measured_mu(spectra: pd.DataFrame, pop: pd.DataFrame, guard) -> pd.DataFrame:
    """Median mu per (key, energy) over matched spectra of `pop`, decoded under `guard`."""
    sp = spectra.merge(pop[["key", "collection", "position", "mh"]], on=["key", "collection", "position"])
    files = file_index().set_index("file")
    vals = []
    for fn, g in sp.groupby("file"):
        peaks = X.decode_selected(ROOT / files.loc[fn, "path"], g.spectrum_id.tolist(), guard)
        for r in g.itertuples(index=False):
            mz, inten = peaks[r.spectrum_id]
            vals.append({"key": r.key, "energy": r.energy, "spectrum_id": r.spectrum_id, "file": fn,
                         "mu": spectrum_mu(mz, inten, r.mh), "n_peaks": int(mz.size)})
    v = pd.DataFrame(vals)
    agg = v.dropna(subset=["mu"]).groupby(["key", "energy"]).agg(mu=("mu", "median"), n_spectra=("mu", "size")).reset_index()
    return agg, {"n_spectra_decoded": int(len(v)), "n_empty_or_nonpositive": int(v.mu.isna().sum())}


def adapter_energy(e, m_prec, k, gamma=1.0):
    return k * np.asarray(e, float) * (500.0 / np.asarray(m_prec, float)) ** gamma


def _phi(model, u):
    from muru.discovery.estimate import _phi_eval
    return _phi_eval(np.array(model["profile"]["knots_log_u"]), np.array(model["profile"]["values"]), u)


def anchor_reference_scales(model: dict, keys) -> pd.Series:
    """g* per anchor: the frozen profile fitted to the anchor's exposed aligned trajectory."""
    from types import SimpleNamespace
    from muru.wur_v2 import scale as SC
    long = pd.read_csv(ROOT / "artifacts/wur_v2/data/long_aligned.csv")
    W = long.pivot(index="group_key", columns="ce_numeric", values="mu").loc[list(keys), [30.0, 45.0, 60.0, 75.0, 90.0]]
    fit = SimpleNamespace(phi_u=np.array(model["profile"]["knots_log_u"]), phi_v=np.array(model["profile"]["values"]))
    return pd.Series(SC.fit_scale(fit, np.array([30.0, 45.0, 60.0, 75.0, 90.0]), W.to_numpy()), index=W.index)


K_GRID = np.exp(np.linspace(np.log(0.2), np.log(5.0), 2001))
GAMMA_GRID = np.linspace(0.0, 2.0, 201)


def fit_adapter(mu_anchor: pd.DataFrame, pop: pd.DataFrame, model: dict, gammas=(1.0,)) -> dict:
    g = anchor_reference_scales(model, sorted(mu_anchor.key.unique()))
    t = mu_anchor.merge(pop[["key", "mh"]], on="key")
    t["lg"] = g.loc[t.key].to_numpy()
    best = None
    for gam in gammas:
        E = adapter_energy(t.energy.to_numpy()[None, :], t.mh.to_numpy()[None, :], K_GRID[:, None], gam)
        ref = _phi(model, (E / 30.0) / np.exp(t.lg.to_numpy())[None, :])
        sse = ((ref - t.mu.to_numpy()[None, :]) ** 2).sum(1)
        i = int(np.argmin(sse))
        if best is None or sse[i] < best["sse"]:
            best = {"k": float(K_GRID[i]), "gamma": float(gam), "sse": float(sse[i])}
    t["mu_ref"] = _phi(model, (adapter_energy(t.energy, t.mh, best["k"], best["gamma"]) / 30.0) / np.exp(t.lg))
    return {**best, "cells": t}


def gate(cells: pd.DataFrame) -> dict:
    from scipy.stats import spearmanr
    per = {}
    for e, g in cells.groupby("energy"):
        per[str(e)] = {"n": int(len(g)), "median_abs_delta": float(np.median(np.abs(g.mu - g.mu_ref))),
                       "spearman": float(spearmanr(g.mu, g.mu_ref).statistic), "median_signed_delta": float(np.median(g.mu - g.mu_ref))}
    rmsd = float(np.sqrt(np.mean((cells.mu - cells.mu_ref) ** 2)))
    n_anchor = int(cells.key.nunique())
    passes = (all(v["median_abs_delta"] <= 0.05 and v["spearman"] >= 0.80 for v in per.values())
              and len(per) == 3 and rmsd <= 0.08 and n_anchor >= 30)
    return {"per_energy": per, "pooled_rmsd": rmsd, "n_anchors": n_anchor, "passes": bool(passes)}


MODEL_FILES = {"CANDIDATE": "V2_TA_MORGAN_JOINT.json", "TA_RIDGE": "V2_REF_TA_RIDGE.json", "B1_MASS": "V2_REF_B1_MASS.json",
               "B0_NULL": "V2_REF_B0_NULL.json", "V1_FROZEN": "V1B_RIDGE_TIERA_FROZEN.json"}
BOOT_B = 10_000
BOOT_SEED = 20261001


def load_models() -> dict:
    d = ROOT / "artifacts/wur_v2/candidate"
    return {k: json.loads((d / v).read_text()) for k, v in MODEL_FILES.items()}


def score_population(mu: pd.DataFrame, pop: pd.DataFrame, adapter: dict, models: dict, boot: bool = True) -> dict:
    """Protocol section 6. `mu` has key, energy, mu; one row per measured cell."""
    from muru.wur_v2 import candidate as CA, metrics as M
    W = mu.pivot(index="key", columns="energy", values="mu").reindex(columns=list(ENERGIES))
    p = pop.set_index("key").loc[W.index]
    E = np.vstack([adapter_energy(np.array(ENERGIES), m, adapter["k"], adapter["gamma"]) for m in p.mh])
    preds, sup = {}, {}
    for name, m in models.items():
        preds[name] = CA.predict_mu(m, p.smiles, p.mh, E)
        if m["kind"] != "null":
            sup[name] = CA.supported(m, p.smiles, p.mh, E)
    complete = np.isfinite(W.to_numpy()).all(1)
    supported = sup["CANDIDATE"].all(1) & sup["TA_RIDGE"].all(1)
    keep = complete & supported
    Y = W.to_numpy()[keep]
    groups = p.scaffold_group.to_numpy()[keep]
    out = {"n_measured": int(len(W)), "n_incomplete": int((~complete).sum()), "n_unsupported": int((complete & ~supported).sum()),
           "n_scored": int(keep.sum()), "n_scaffold_groups_scored": int(len(set(groups))),
           "model_energy_quantiles": {str(e): np.quantile(E[keep][:, j], [0, .1, .5, .9, 1]).round(2).tolist() for j, e in enumerate(ENERGIES)},
           "models": {}, "comparisons": {}}
    for name in models:
        s = M.summary(preds[name][keep], Y, preds["B0_NULL"][keep])
        s["per_energy"] = M.per_rung(preds[name][keep], Y, ENERGIES)
        out["models"][name] = s
    if boot:
        for ref in ("TA_RIDGE", "B1_MASS", "B0_NULL", "V1_FROZEN"):
            out["comparisons"][f"CANDIDATE_vs_{ref}"] = M.cluster_bootstrap(preds["CANDIDATE"][keep], preds[ref][keep], Y, groups,
                                                                            n=BOOT_B, seed=BOOT_SEED)
        # sensitivity: include unsupported cells (profile clamped)
        k2 = complete
        out["sensitivity_including_unsupported"] = {
            "n": int(k2.sum()), "P1_candidate": M.p1(M.errors(preds["CANDIDATE"][k2], W.to_numpy()[k2])),
            "P1_ta": M.p1(M.errors(preds["TA_RIDGE"][k2], W.to_numpy()[k2]))}
        out["sensitivity_including_unsupported"]["ratio"] = (out["sensitivity_including_unsupported"]["P1_candidate"]
                                                             / out["sensitivity_including_unsupported"]["P1_ta"])
        strata = {}
        pk = p[keep]
        for label, mask in {"NEXUS": pk.collection == "NEXUS", "SELLECK": pk.collection == "SELLECK",
                            "mh_below_median": pk.mh <= pk.mh.median(), "mh_above_median": pk.mh > pk.mh.median()}.items():
            mk = mask.to_numpy()
            if mk.sum() >= 10:
                strata[label] = {"n": int(mk.sum()), "P1_candidate": M.p1(M.errors(preds["CANDIDATE"][keep][mk], Y[mk])),
                                 "P1_ta": M.p1(M.errors(preds["TA_RIDGE"][keep][mk], Y[mk]))}
                strata[label]["ratio"] = strata[label]["P1_candidate"] / strata[label]["P1_ta"]
        out["strata"] = strata
    return out


def decide(primary: dict) -> dict:
    c = primary["comparisons"]["CANDIDATE_vs_TA_RIDGE"]
    supported = c["P1_ratio_ci"][1] < 1.0
    out = {"primary_supported": bool(supported), "practical_target_met": bool(supported and c["P1_ratio"] <= 0.95),
           "P1_ratio": c["P1_ratio"], "P1_ratio_ci95": c["P1_ratio_ci"],
           "n_scored": primary["n_scored"], "n_groups": primary["n_scaffold_groups_scored"],
           "limited_transfer_study": bool(primary["n_scored"] < 400 or primary["n_scaffold_groups_scored"] < 250)}
    if supported:
        out["af_noninferior_3pp"] = bool(c["AF_diff_ci"][1] <= 0.03)
    return out
