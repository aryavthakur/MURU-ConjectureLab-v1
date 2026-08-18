#!/usr/bin/env python
"""Verify the generated E0 corpus against the committed design, before analysis.

`MURU_V2_E0_PROTOCOL.md` section 6.7: mismatch aborts.  Every check below is a
hard gate; the script exits non-zero and writes `passed: false` if any fails, and
`scripts/analyse_e0.py` refuses to run on a corpus that has not passed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from muru.v2_calibration import e0_cells  # noqa: E402
from muru.v2_calibration.e0_seeds import assert_namespace_disjoint  # noqa: E402
from muru.v2_calibration.e0_worlds import E0_LAW_KIND, E0_NOISE_SD  # noqa: E402

OUT = REPO / "artifacts" / "e0"
DESIGN_REF = REPO / "v2_design_reference"

#: `v2_design_reference/DESIGN_PROVENANCE.md`, recorded against commit befca0d.
DESIGN_BLOBS = {
    "MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md": "05d3dabdbf52adc458f679efa267f858f6038d01",
    "MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json": "25a665a9a1b819011c46b00bf5f4a3d192a0c14f",
    "MURU_V2_A1_STUDY_DESIGN.md": "28846cbd5465f891dc9631a254c9902e5d34ad74",
    "MURU_V2_CAUSAL_DECISION_TREE.md": "52e6b0548c4a3fa841aac3fd7417b5ab571592a9",
    "MURU_V1_G1_FAILURE_TAXONOMY.csv": "ff8120f2fd6c9daf994be72332bc64d40bcc8637",
}


def check(results: list[dict], name: str, passed: bool, detail: object = "") -> None:
    results.append({"check": name, "passed": bool(passed), "detail": detail})


def main() -> int:
    worlds = pd.read_csv(OUT / "e0_worlds.csv")
    fits = pd.read_parquet(OUT / "e0_fits.parquet")
    contrasts = pd.read_parquet(OUT / "e0_contrasts.parquet")
    manifest = json.loads((OUT / "e0_run_manifest.json").read_text())

    r: list[dict] = []

    # --- design documents unmodified -------------------------------------
    for name, expected in DESIGN_BLOBS.items():
        actual = subprocess.run(
            ["git", "hash-object", str(DESIGN_REF / name)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        check(r, f"design artifact unmodified: {name}", actual == expected,
              {"expected": expected, "actual": actual})

    # --- grid shape -------------------------------------------------------
    check(r, "9 cells crossed 3x3", len(e0_cells.CELLS) == 9)
    check(r, "cell ids in corpus match the design grid",
          set(worlds.cell_id) == {c.cell_id for c in e0_cells.CELLS},
          sorted(set(worlds.cell_id)))
    check(r, "60 worlds per cell", (worlds.groupby("cell_id").size() == 60).all(),
          dict(worlds.groupby("cell_id").size()))
    check(r, "540 worlds total", len(worlds) == 540, len(worlds))
    check(r, "60 replicates, each present in all 9 cells",
          (worlds.groupby("replicate").size() == 9).all() and worlds.replicate.nunique() == 60)

    # --- factor levels ----------------------------------------------------
    for cell in e0_cells.CELLS:
        sub = worlds[worlds.cell_id == cell.cell_id]
        clip_ok = (
            sub.generator_clip.isna().all() if cell.generator_clip is None
            else np.allclose(sub.generator_clip.to_numpy(), cell.generator_clip, rtol=0, atol=0)
        )
        check(r, f"factor levels exact in {cell.cell_id}",
              clip_ok and np.allclose(sub.fitter_mu_ceil.to_numpy(), cell.fitter_mu_ceil, rtol=0, atol=0))
    check(r, "generator clip levels are exactly the design's three",
          sorted({round(v, 12) for v in worlds.generator_clip.dropna().unique()}) == [0.999, 0.9999]
          and worlds.generator_clip.isna().sum() == 180)
    check(r, "fitter ceiling levels are exactly the design's three",
          sorted({round(v, 12) for v in worlds.fitter_mu_ceil.unique()}) == [0.999, 0.9999, 1.01])

    # --- shared draws -----------------------------------------------------
    per_replicate = worlds.groupby("replicate").base_fingerprint.nunique()
    check(r, "all nine cells of a replicate share one draw fingerprint",
          (per_replicate == 1).all(), dict(per_replicate[per_replicate != 1]))
    check(r, "distinct replicates have distinct draws",
          worlds.base_fingerprint.nunique() == 60, worlds.base_fingerprint.nunique())
    for column in ("mu_inf", "phi_p"):
        spread = worlds.groupby("replicate")[column].nunique()
        check(r, f"{column} identical across cells within a replicate", (spread == 1).all())

    # --- world geometry and truth ----------------------------------------
    check(r, "true M0 everywhere: no planted deviation in the world configuration",
          manifest["world_configuration"]["truth"] == "M0"
          and manifest["world_configuration"]["law"] == E0_LAW_KIND
          and manifest["world_configuration"]["noise_sd"] == E0_NOISE_SD)
    check(r, "30 test compounds and 6 energies per world",
          manifest["world_configuration"]["test_compounds"] == 30
          and manifest["world_configuration"]["energies"] == 6)
    check(r, "1,080 fit records per world", len(fits) == 540 * 1080, len(fits))
    check(r, "90 contrast records per world", len(contrasts) == 540 * 90, len(contrasts))
    check(r, "every world contributed exactly 1,080 fits",
          (fits.groupby("world_id").size() == 1080).all())
    check(r, "fit records cover 3 detectors x 30 compounds x 6 folds x 2 models",
          fits.detector.nunique() == 3 and fits.compound_id.nunique() == 30
          and fits.fold_index.nunique() == 6 and set(fits.model) == {"M0", "M1", "M2", "M3"})

    # --- isolation --------------------------------------------------------
    check(r, "every world id is in the V2C namespace", worlds.world_id.str.startswith("V2C|E0|").all())
    check(r, "no benchmark case id anywhere in the corpus",
          not worlds.world_id.str.contains("PB|", regex=False).any())
    check(r, "every world is separately identified and hashed",
          worlds.content_hash.nunique() == 540 and worlds.world_id.nunique() == 540,
          {"hashes": worlds.content_hash.nunique(), "ids": worlds.world_id.nunique()})
    check(r, "response geometry shared across the three cells of a clip level",
          (worlds.groupby(["replicate", "generator_clip"], dropna=False)
                 .mu_max_test.nunique() == 1).all())
    check(r, "seed namespace disjoint from the benchmark", assert_namespace_disjoint()["disjoint"])
    check(r, "no symbolic search executed",
          manifest["symbolic_search_runs"] == 0 and manifest["pysr_imported"] is False)

    # --- clip semantics ---------------------------------------------------
    unclipped = worlds[worlds.generator_clip.isna()]
    check(r, "the no-clip level applied no clip",
          (unclipped.ceiling_clip_activations == 0).all() and (unclipped.floor_clip_activations == 0).all())
    check(r, "the response floor never binds, so the manipulation is purely the ceiling",
          int(worlds.floor_clip_activations.sum()) == 0, int(worlds.floor_clip_activations.sum()))

    passed = all(item["passed"] for item in r)
    report = {
        "verified": "E0 generated corpus against the committed design",
        "passed": passed,
        "n_checks": len(r),
        "n_failed": sum(1 for item in r if not item["passed"]),
        "failed": [item for item in r if not item["passed"]],
        "checks": r,
    }
    (OUT / "e0_design_fidelity.json").write_text(json.dumps(report, indent=2, default=str))
    for item in r:
        print(f"{'PASS' if item['passed'] else 'FAIL'}  {item['check']}")
    print(f"\n{report['n_checks'] - report['n_failed']}/{report['n_checks']} checks passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
