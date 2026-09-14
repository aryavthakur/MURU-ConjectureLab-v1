"""MSnLib confirmation study 2, protocol V2 section 2 (structural novelty), frozen before the look.

Maximum Morgan-count Tanimoto similarity (radius 2, 2048, stereo removed) of every sampled compound to the 1,325
development compounds; fixed bands, replaced by quartile bins if any band has fewer than 30 compounds. Structure
only; the same rule and computation as study 1 (scripts/wur_v2_confirmation/09_novelty_bins.py).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import msnlib_design as MD        # noqa: E402

RDLogger.DisableLog("rdApp.*")
POP = ROOT / "artifacts/wur_v2_confirmation_v2/population"
FREEZE = ROOT / "artifacts/wur_v2_confirmation_v2/freeze"
FIXED_BINS = [(0.0, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 1.0001)]
FIXED_LABELS = ["<0.30", "0.30-0.50", "0.50-0.70", ">=0.70"]
MIN_BIN_COUNT = 30


def count_fp(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    return rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048).GetCountFingerprint(m)


def main() -> int:
    home = Path(os.environ.get("MURU_MSNLIB_HOME", str(Path.home() / "muru-msnlib")))
    dev = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv", usecols=["group_key", "smiles"])
    dev_fps = [fp for fp in (count_fp(s) for s in dev.smiles) if fp is not None]
    design = MD.load_design(home / "merlin_metadata", home / "cache" / "confirmation_v2")
    keys12b, key_scaf, _ = MD.design12b(design)
    sampled = set(g for g in (POP / "sampled_scaffold_groups.txt").read_text().split("\n") if g)
    keys = sorted(k for k in keys12b if key_scaf[k] in sampled)
    first = design.dropna(subset=["key"]).drop_duplicates("key").set_index("key")
    rows = []
    for k in keys:
        fp = count_fp(first.smiles[k])
        sim = float(max(DataStructs.BulkTanimotoSimilarity(fp, dev_fps))) if fp is not None else float("nan")
        rows.append({"key": k, "scaffold_group": key_scaf[k], "max_similarity_to_dev": sim})
    df = pd.DataFrame(rows)
    counts = {lab: int(df.max_similarity_to_dev.between(lo, hi, inclusive="left").sum()) for (lo, hi), lab in zip(FIXED_BINS, FIXED_LABELS)}
    bins, labels, used = FIXED_BINS, FIXED_LABELS, "fixed"
    if any(n < MIN_BIN_COUNT for n in counts.values()):
        qs = df.max_similarity_to_dev.quantile([0, 0.25, 0.5, 0.75, 1.0]).to_numpy().copy()
        qs[0], qs[-1] = 0.0, 1.0001
        bins = list(zip(qs[:-1], qs[1:]))
        labels = [f"Q{i + 1} [{lo:.3f},{hi:.3f})" for i, (lo, hi) in enumerate(bins)]
        counts = {lab: int(df.max_similarity_to_dev.between(lo, hi, inclusive="left").sum()) for (lo, hi), lab in zip(bins, labels)}
        used = "quantile_fallback"
    df["novelty_bin"] = pd.cut(df.max_similarity_to_dev, bins=[b[0] for b in bins] + [bins[-1][1]], labels=labels, right=False,
                               include_lowest=True)
    FREEZE.mkdir(parents=True, exist_ok=True)
    df.to_csv(FREEZE / "novelty_bins_per_compound.csv", index=False)
    out = {"bins_used": used, "bin_definitions": [{"label": l, "lo": float(lo), "hi": float(hi)} for (lo, hi), l in zip(bins, labels)],
           "counts": counts, "n_compounds": len(df), "fixed_band_counts_before_fallback": None if used == "fixed" else
           {lab: int(df.max_similarity_to_dev.between(lo, hi, inclusive="left").sum()) for (lo, hi), lab in zip(FIXED_BINS, FIXED_LABELS)}}
    (FREEZE / "novelty_bins.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
