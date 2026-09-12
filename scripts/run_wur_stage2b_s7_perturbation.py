"""Stage 2B metric S7: preprocessing robustness of the selected candidate.

Recomputes mu for both corpora under two alternative preprocessing cells
(relative_cutoff 0.01; include_precursor false), rebuilds the pooled-aligned
DEV2B world with the FROZEN Stage 1 map (not refitted), and reruns V1C, LIN
and B0 on repeat 1 of the frozen folds. Reports the change in P1 against
the base-cell repeat-1 values in the ledger. HOLD is forbidden, the seal
guard runs before any blob.
"""
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402
from muru import features as F                         # noqa: E402
from muru.io.massbank import parse_file                # noqa: E402
from muru.io.wur_raw import LIBRARY_DB_FILES           # noqa: E402
from muru.io.wur_spectra import assert_no_sealed_key, read_spectrum_peaks_censused  # noqa: E402
from muru.spectra import Spectrum, spectrum_from_record  # noqa: E402
from muru.wur_bridge_constants import PRECURSOR_MATCH_PPM  # noqa: E402
from muru.wur_stage2 import arms_v1, candidates as CA, cv as CV, folds as FO, population as POP, world as W  # noqa: E402
from muru.wur_stage2.spectral_features import LCSB_DIR  # noqa: E402

CELLS = {"cutoff_0.01": dict(relative_cutoff=0.01, include_precursor=True, intensity_transform="raw"),
         "no_precursor": dict(relative_cutoff=0.0, include_precursor=False, intensity_transform="raw")}
OUT = ROOT / "artifacts" / "wur_stage2b"


def wur_mu_cell(acc, data_dir, hold, cell):
    assert_no_sealed_key(acc, forbidden=hold)
    rows = []
    for (lib, pf), grp in acc.groupby(["source_library", "source_polarity_file"], sort=True):
        peaks, _ = read_spectrum_peaks_censused(data_dir / f"{LIBRARY_DB_FILES[(lib, pf)]}.db", grp["spectrum_id"])
        for r in grp.itertuples(index=False):
            if int(r.spectrum_id) not in peaks:
                continue
            mz, it = peaks[int(r.spectrum_id)]
            o = np.argsort(mz)
            s = Spectrum(mz=mz[o], intensity=it[o], precursor_mz=float(r.precursor_mass))
            rows.append({"connectivity_key": r.connectivity_key, "ce_numeric": float(r.energy),
                         "mu": F.mu(s.preprocess(ppm=PRECURSOR_MATCH_PPM, **cell))})
    d = pd.DataFrame(rows)
    return d.groupby(["connectivity_key", "ce_numeric"], as_index=False)["mu"].median()


def lcsb_mu_cell(keys, cell):
    traj = pd.read_parquet(ROOT / "artifacts" / "trajectories.parquet")
    base = traj[traj["is_base_cell"] & (traj["ion_mode_raw"].str.upper() == "POSITIVE")
                & traj["inchikey_first_block"].isin(keys)]
    rows = []
    for r in base[["accession", "inchikey_first_block", "ce_numeric"]].drop_duplicates().itertuples(index=False):
        s = spectrum_from_record(parse_file(LCSB_DIR / f"{r.accession}.txt"))
        rows.append({"connectivity_key": r.inchikey_first_block, "ce_numeric": float(r.ce_numeric),
                     "mu": F.mu(s.preprocess(ppm=PRECURSOR_MATCH_PPM, **cell))})
    d = pd.DataFrame(rows)
    return d.groupby(["connectivity_key", "ce_numeric"], as_index=False)["mu"].mean()


def main():
    data_dir = ROOT / "data" / "external" / "wur"
    gate = json.loads((ROOT / "artifacts" / "wur_bridge_gate.json").read_text())["alignment"]
    a, b = float(gate["a"]), float(gate["b"])
    dev = POP.wur_dev_partition(data_dir)
    acc, ident = POP.wur_analysis_accepted(data_dir, dev)
    hold = set(POP.load_internal_holdout()["hold"]["connectivity_keys"])
    lcsb_keys = set(POP.lcsb_dev_mu_table()["connectivity_key"])
    base_long, cov, frame = CV.load_dev2b()
    folds = FO.load_folds()
    report = {"cells": CELLS, "repeat": 1, "arms": {}}
    base = {cid: json.loads((CV.LEDGER / f"{cid}.json").read_text()) for cid in ("V1C_RICH_RIDGE_24", "LIN_RIDGE_TIERA", "B0_NULL_PROFILE")}
    for cid, d in base.items():
        report["arms"][cid] = {"base_P1_repeat1": float(np.mean([f["P1"] for f in d["folds"] if f["repeat"] == 1]))}
    for name, cell in CELLS.items():
        wur = wur_mu_cell(acc, data_dir, hold, cell)
        lc = lcsb_mu_cell(lcsb_keys, cell)
        wur = wur.dropna(); lc = lc.dropna()
        pooled, census = W.pooled_long(W.native_long(lc, "LCSB"), W.aligned_wur_long(wur, a, b))
        pooled = pooled[pooled["group_key"].isin(set(frame["group_key"]))]
        keys = sorted(set(pooled["group_key"]))
        sub = frame[frame["group_key"].isin(keys)]
        cov_s = cov[cov["group_key"].isin(keys)]
        b0p = CV.b0_predictions(pooled, cov_s, sub, folds)
        for cid, make in (("V1C_RICH_RIDGE_24", arms_v1.RichRidge), ("LIN_RIDGE_TIERA", CV.LinRidge), ("B0_NULL_PROFILE", CV.B0NullProfile)):
            r = CV.run_cv(make, pooled, cov_s, sub, folds, b0p, with_loeo=False, repeats=[1])
            p1 = float(r.p1_vector().mean())
            report["arms"][cid][name] = {"P1_repeat1": p1, "n_compounds": len(keys),
                                        "delta_vs_base": p1 - report["arms"][cid]["base_P1_repeat1"],
                                        "rel_delta": (p1 - report["arms"][cid]["base_P1_repeat1"]) / report["arms"][cid]["base_P1_repeat1"]}
            print(f"[s7] {name} {cid}: P1 {p1:.4f} (base {report['arms'][cid]['base_P1_repeat1']:.4f}) n={len(keys)}", flush=True)
    (OUT / "s7_preprocessing_perturbation.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
