"""MSnLib two-rung external validation: header rules, anchor gate and (later) the one look.

Rules are frozen in MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md. Headers come from
`external_mzml.scan_headers`; peaks are decoded only under an
`external_guard.AccessGuard`.

Fixed-rung identification. Every precursor selection produces a run of
consecutive MS2 scans with the same selected-ion m/z: Exp.1 fixed NCE 20,
Exp.2 Assisted (outcome-adaptive, 15 to 75), Exp.3 fixed NCE 60. A scan is the
fixed-20 rung only if it is the first scan of such a run and its collision
energy is 20; the fixed-60 rung only if it is the last scan of a run of at
least two and its energy is 60. The Assisted scan is never used, even when its
energy happens to equal 20 or 60.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from muru.wur_v2 import external_mzml as X
from muru.wur_v2 import external_multims2 as MM

ROOT = Path(__file__).resolve().parents[3]
DL = ROOT / "data/external/msnlib_mzml"
OUT = ROOT / "artifacts/wur_v2/external_msnlib"
RUNGS = (20.0, 60.0)
SEL_TOL = 0.01
FIRST_MASS_MAX = 40.0
WUR_MAP = (-5.95552603907965, 0.8618030610784555)


def fixed_rung_scans(h: pd.DataFrame) -> pd.DataFrame:
    """Label fixed-20 and fixed-60 scans by run position (see module docstring)."""
    h = h.sort_values("index").reset_index(drop=True)
    ms2 = h[h.ms_level == 2].copy()
    if ms2.empty:
        return ms2.assign(rung=np.nan)
    prev_idx = ms2["index"].shift(1)
    prev_mz = ms2["selected_ion_mz"].shift(1)
    new_run = ~((ms2["index"] - prev_idx == 1) & ((ms2["selected_ion_mz"] - prev_mz).abs() <= 1e-4))
    ms2["run"] = new_run.cumsum()
    ms2["pos"] = ms2.groupby("run").cumcount()
    ms2["run_len"] = ms2.groupby("run")["index"].transform("size")
    first20 = (ms2.pos == 0) & (ms2.collision_energy == 20.0)
    last60 = (ms2.pos == ms2.run_len - 1) & (ms2.run_len >= 2) & (ms2.collision_energy == 60.0)
    ms2["rung"] = np.where(first20, 20.0, np.where(last60, 60.0, np.nan))
    return ms2


def match_compounds(wells: pd.DataFrame, headers: dict) -> pd.DataFrame:
    """wells: key, unique_sample_id, fn, mh, smiles. Returns matched fixed-rung scans (identity only)."""
    rows = []
    for r in wells.itertuples(index=False):
        h = headers.get(r.fn)
        if h is None:
            continue
        s = h[h.rung.notna() & ((h.selected_ion_mz - r.mh).abs() <= SEL_TOL)]
        for c in s.itertuples(index=False):
            rows.append({"key": r.key, "unique_sample_id": r.unique_sample_id, "file": r.fn, "spectrum_id": c.spectrum_id,
                         "energy": c.rung, "window_ok": bool(c.scan_window_lower_limit <= FIRST_MASS_MAX and c.scan_window_upper_limit >= r.mh + 1)})
    return pd.DataFrame(rows)


def eligible(matched: pd.DataFrame) -> set:
    ok = matched[matched.window_ok]
    per = ok.groupby("key").energy.apply(lambda e: set(e))
    bad = set(matched[~matched.window_ok].key)
    return {k for k, e in per.items() if set(RUNGS) <= e and k not in bad}


def measured_mu(matched: pd.DataFrame, pop: pd.DataFrame, guard) -> tuple[pd.DataFrame, dict]:
    mh = pop.drop_duplicates("key").set_index("key").mh
    vals = []
    for fn, g in matched.groupby("file"):
        peaks = X.decode_selected(DL / fn, g.spectrum_id.tolist(), guard)
        for r in g.itertuples(index=False):
            mz, it = peaks[r.spectrum_id]
            vals.append({"key": r.key, "energy": r.energy, "file": fn, "spectrum_id": r.spectrum_id,
                         "mu": MM.spectrum_mu(mz, it, float(mh.loc[r.key])), "n_peaks": int(mz.size)})
    v = pd.DataFrame(vals)
    agg = v.dropna(subset=["mu"]).groupby(["key", "energy"]).agg(mu=("mu", "median"), n_spectra=("mu", "size")).reset_index()
    return agg, {"n_spectra_decoded": int(len(v)), "n_empty_or_nonpositive": int(v.mu.isna().sum())}


def adapter_energy(nce, family: str, params: dict):
    nce = np.asarray(nce, float)
    if family == "A0":
        return (nce - WUR_MAP[0]) / WUR_MAP[1]
    if family == "A1":
        return params["k"] * nce
    if family == "A2":
        return params["a"] + params["b"] * nce
    raise ValueError(family)


def fit_and_gate(mu: pd.DataFrame, model: dict) -> dict:
    """A0 (no free parameter), then A1 (k), then A2 (a, b); the first family that passes is used."""
    g = MM.anchor_reference_scales(model, sorted(mu.key.unique()))
    t = mu.reset_index(drop=True).copy()
    t["lg"] = g.loc[t.key].to_numpy()
    nce, y, scale = t.energy.to_numpy(), t.mu.to_numpy(), np.exp(t.lg.to_numpy())
    res = {}
    fams = [("A0", [{}]),
            ("A1", [{"k": k} for k in np.exp(np.linspace(np.log(0.5), np.log(3.0), 1001))]),
            ("A2", [{"a": a, "b": b} for a in np.linspace(-40, 40, 161) for b in np.exp(np.linspace(np.log(0.3), np.log(3.0), 161))])]
    for fam, grid in fams:
        best = None
        for start in range(0, len(grid), 2000):
            chunk = grid[start:start + 2000]
            E = np.vstack([adapter_energy(nce, fam, prm) for prm in chunk])
            ref = MM._phi(model, (E / 30.0) / scale[None, :])
            sse = ((ref - y[None, :]) ** 2).sum(1)
            i = int(np.argmin(sse))
            if best is None or sse[i] < best[0]:
                best = (float(sse[i]), chunk[i])
        c = t.copy()
        c["mu_ref"] = MM._phi(model, (adapter_energy(c.energy, fam, best[1]) / 30.0) / np.exp(c.lg))
        gt = MM.gate(c, n_energies=len(RUNGS))
        res[fam] = {"params": {k: float(v) for k, v in best[1].items()}, "sse": best[0], "gate": gt}
        if gt["passes"]:
            res["adapter"] = {"family": fam, **{k: float(v) for k, v in best[1].items()}}
            res["cells"] = c
            break
    res["qualified"] = "adapter" in res
    return res
