"""Step 7 (pre-look, structure-only): maximum Morgan-count Tanimoto similarity of each
sampled validation compound to the 1,325-compound development population, and the
frozen novelty bins. Computed and frozen BEFORE any outcome is seen -- never used to
exclude primary compounds."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

RDLogger.DisableLog("rdApp.*")

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")

FIXED_BINS = [(0.0, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 1.0001)]
FIXED_LABELS = ["<0.30", "0.30-0.50", "0.50-0.70", ">=0.70"]
MIN_BIN_COUNT = 30


def count_fp(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    return gen.GetCountFingerprint(m)


def main():
    dev = pd.read_csv(REPO / "artifacts/wur_v2/data/compounds.csv", usecols=["group_key", "smiles"])
    dev_fps = [fp for fp in (count_fp(s) for s in dev.smiles) if fp is not None]
    print(f"development fingerprints: {len(dev_fps)} of {len(dev)}", file=sys.stderr)

    dsub = pd.read_parquet(MD / "sampled_compound_wells.parquet")
    sampled = dsub.drop_duplicates("key")[["key", "smiles", "scaffold_group"]]
    print(f"sampled compounds: {len(sampled)}", file=sys.stderr)

    maxsim = {}
    for r in sampled.itertuples(index=False):
        fp = count_fp(r.smiles)
        maxsim[r.key] = float(max(DataStructs.BulkTanimotoSimilarity(fp, dev_fps))) if fp is not None else float("nan")

    sampled = sampled.assign(max_similarity_to_dev=sampled.key.map(maxsim))
    counts = {label: int(sampled.max_similarity_to_dev.between(lo, hi, inclusive="left").sum())
              for (lo, hi), label in zip(FIXED_BINS, FIXED_LABELS)}
    print("fixed bin counts:", counts, file=sys.stderr)

    inadequate = [label for label, n in counts.items() if n < MIN_BIN_COUNT]
    bins_used = "fixed"
    final_bins = FIXED_BINS
    final_labels = FIXED_LABELS
    if inadequate:
        print(f"fixed bins with <{MIN_BIN_COUNT} compounds: {inadequate} -- falling back to quantile bins per protocol", file=sys.stderr)
        qs = sampled.max_similarity_to_dev.quantile([0, 0.25, 0.5, 0.75, 1.0]).to_numpy().copy()
        qs[0], qs[-1] = 0.0, 1.0001
        final_bins = list(zip(qs[:-1], qs[1:]))
        final_labels = [f"Q{i+1} [{lo:.3f},{hi:.3f})" for i, (lo, hi) in enumerate(final_bins)]
        counts = {label: int(sampled.max_similarity_to_dev.between(lo, hi, inclusive="left").sum())
                  for (lo, hi), label in zip(final_bins, final_labels)}
        bins_used = "quantile_fallback"
        print("quantile bin counts:", counts, file=sys.stderr)

    sampled["novelty_bin"] = pd.cut(sampled.max_similarity_to_dev, bins=[b[0] for b in final_bins] + [final_bins[-1][1]],
                                     labels=final_labels, right=False, include_lowest=True)

    out = {"bins_used": bins_used, "bin_definitions": [{"label": l, "lo": float(lo), "hi": float(hi)}
                                                        for (lo, hi), l in zip(final_bins, final_labels)],
           "counts": counts, "quantiles_of_max_similarity": {str(q): float(sampled.max_similarity_to_dev.quantile(q))
                                                              for q in (0.1, 0.25, 0.5, 0.75, 0.9)}}
    (REPO / "artifacts/wur_v2_confirmation").mkdir(parents=True, exist_ok=True)
    (REPO / "artifacts/wur_v2_confirmation/novelty_bins.json").write_text(json.dumps(out, indent=2))
    sampled[["key", "scaffold_group", "max_similarity_to_dev", "novelty_bin"]].to_csv(
        REPO / "artifacts/wur_v2_confirmation/novelty_bins_per_compound.csv", index=False)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
