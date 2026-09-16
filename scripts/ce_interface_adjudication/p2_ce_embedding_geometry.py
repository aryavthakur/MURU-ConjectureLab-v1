#!/usr/bin/env python3
"""P2: closed-form geometry of the ms-pred collision-energy sinusoidal embedding.

Pure formula analysis (no checkpoint weights, no model, no inference):
  e(c) = concat_i sin(c / d_i), concat_i cos(c / d_i),  d_i = 10000 ** (2 i / 64), i = 0..31
  (common.COLLISION_PE_DIM = 64, common.COLLISION_PE_SCALAR = 10000; gen_model.py:142-147, 283-288)

Identity: ||e(a) - e(b)||^2 = 2 * sum_i (1 - cos((a - b) / d_i)), so the metric depends only on
delta = a - b (translation invariant). The script reports distances, near-alias minima,
per-band contributions, and the NCE-vs-eV input gap delta = NCE * (1 - mz / 500).

Usage: p2_ce_embedding_geometry.py OUT_JSON
"""
import json
import sys

import numpy as np

PE_DIM = 64
SCALAR = 10000.0
I = np.arange(PE_DIM // 2)
DEN = SCALAR ** (2 * I / PE_DIM)


def emb(c):
    c = np.asarray(c, dtype=np.float64)[..., None]
    return np.concatenate([np.sin(c / DEN), np.cos(c / DEN)], axis=-1)


def dist(a, b):
    return float(np.linalg.norm(emb(a) - emb(b)))


def dist_delta(delta):
    delta = np.asarray(delta, dtype=np.float64)[..., None]
    return np.sqrt(2 * np.sum(1 - np.cos(delta / DEN), axis=-1))


def band_share(delta, bands):
    per = 2 * (1 - np.cos(delta / DEN))
    tot = per.sum()
    return {name: float(per[lo:hi].sum() / tot) if tot > 0 else 0.0 for name, (lo, hi) in bands.items()}


def main(out_path):
    out = {}
    out["denominators"] = DEN.tolist()
    out["periods_2pi_d"] = (2 * np.pi * DEN).tolist()
    out["local_lipschitz_norm_de_dc"] = float(np.sqrt(np.sum(1 / DEN ** 2)))
    out["max_possible_distance"] = float(np.sqrt(2 * 2 * 32))  # all cos terms = -1
    out["expected_distance_random_phases"] = float(np.sqrt(2 * 32))
    # monotonic regime: sin(c/d) monotone for c <= pi/2 * d
    for cmax in (100, 150, 200, 358.4):
        out[f"n_freqs_monotone_sin_up_to_{cmax}"] = int(np.sum(np.pi / 2 * DEN >= cmax))
        out[f"first_monotone_index_up_to_{cmax}"] = int(np.argmax(np.pi / 2 * DEN >= cmax))

    bands = {
        "i0-7": (0, 8),
        "i8-15": (8, 16),
        "i16-23": (16, 24),
        "i24-31": (24, 32),
    }
    out["band_denominator_ranges"] = {k: [float(DEN[lo]), float(DEN[hi - 1])] for k, (lo, hi) in bands.items()}

    pairs = {
        "20_vs_60": (20, 60),
        "20_vs_30": (20, 30),
        "20_vs_21": (20, 21),
        "20_vs_20.5 (rounding half step)": (20, 20.5),
        "NCE20_raw_vs_eV_at_mz300 (20 vs 12)": (20, 12),
        "NCE60_raw_vs_eV_at_mz300 (60 vs 36)": (60, 36),
        "NCE40_raw_vs_eV_at_mz800 (40 vs 64)": (40, 64),
        "NCE90_raw_vs_eV_at_mz150 (90 vs 27)": (90, 27),
        "NCE30_raw_vs_eV_at_mz500 (30 vs 30)": (30, 30),
        "12_vs_36 (eV ladder at mz300 NCE20/60)": (12, 36),
        "0_vs_358.4 (MSG label min vs max)": (0, 358.4),
        "150_vs_156.28 (one period of i0)": (150, 150 + 2 * np.pi),
    }
    rows = {}
    for k, (a, b) in pairs.items():
        d = b - a
        rows[k] = {
            "a": a,
            "b": b,
            "delta": d,
            "distance": dist(a, b),
            "distance_over_random_phase_expectation": dist(a, b) / np.sqrt(64),
            "band_share_of_squared_distance": band_share(d, bands),
            "low_band_only_distance_i16_31": float(np.sqrt(np.sum((emb(a) - emb(b))[[*range(16, 32), *range(48, 64)]] ** 2))),
        }
    out["pairs"] = rows

    # distance as function of delta; local minima (near-aliases) for delta in (0, 400]
    deltas = np.round(np.arange(0.05, 400.0001, 0.05), 4)
    dd = dist_delta(deltas)
    mins = [(float(deltas[j]), float(dd[j])) for j in range(1, len(dd) - 1) if dd[j] < dd[j - 1] and dd[j] <= dd[j + 1]]
    mins_sorted = sorted([m for m in mins if m[0] >= 2.0], key=lambda t: t[1])[:10]
    out["near_alias_local_minima_delta_ge2_lowest10"] = [{"delta": a, "distance": b} for a, b in mins_sorted]
    out["distance_at_delta"] = {str(x): float(dist_delta(x)) for x in (0.5, 1, 2, 3, 5, 6.283, 8, 10, 20, 24, 40, 60, 100, 200, 300)}
    # smallest distance among all integer deltas 1..400 and where
    ints = np.arange(1, 401)
    di = dist_delta(ints)
    out["min_distance_integer_delta_1_400"] = {"delta": int(ints[np.argmin(di)]), "distance": float(di.min())}
    out["distance_integer_delta_1"] = float(dist_delta(1))

    # NCE vs eV interface gap: delta = NCE * (1 - mz/500)
    grid = {}
    for mz in (150, 200, 300, 400, 500, 600, 800, 1000):
        for nce in (10, 20, 30, 45, 60, 90):
            ev = nce * mz / 500
            grid[f"mz{mz}_nce{nce}"] = {"eV": ev, "delta_raw_minus_eV": nce - ev, "embedding_distance": dist(nce, ev)}
    out["nce_vs_ev_gap_grid"] = grid
    with open(out_path, "w") as f:
        f.write(json.dumps(out, indent=1) + "\n")
    brief = {k: v for k, v in out.items() if k not in ("denominators", "periods_2pi_d", "nce_vs_ev_gap_grid")}
    print(json.dumps(brief, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
