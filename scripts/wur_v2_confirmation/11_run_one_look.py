"""Step 10: the one and only validation look. Requires MURU_V2_MSNLIB_CONFIRMATION_FREEZE.md
and its JSON manifest already committed on a clean tree. Constructs ConfirmationAccessGuard
(writes the access record BEFORE any decode), then decodes exactly the eligible, frozen
(file, spectrum_id) population via the existing external_mzml.decode_selected /
external_multims2.spectrum_mu -- nothing else.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
SCRATCH = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(SCRATCH))
from muru.wur_v2 import external_mzml as X                    # noqa: E402
from muru.wur_v2 import external_multims2 as MM                # noqa: E402
from muru.wur_v2.confirmation_guard import ConfirmationAccessGuard  # noqa: E402
from muru.wur_v2.candidate import sha256_of                    # noqa: E402
from header_eligibility import compute_header_eligibility      # noqa: E402

DL = REPO / "data/external/msnlib_mzml"
OUTDIR = REPO / "artifacts/wur_v2_confirmation"


def main():
    freeze_manifest = json.loads((OUTDIR / "freeze_manifest.json").read_text())
    # LIVE recomputation, not a cached-file read: this is what makes the guard's
    # population/scaffold/spectrum-manifest hash cross-check meaningful rather than
    # tautological (a governance-review finding, fixed before the guard is constructed).
    header_elig = compute_header_eligibility()
    assert header_elig["validation_key_hash"] == freeze_manifest["population_key_hash"], (
        "live header-eligibility recomputation no longer matches the frozen population_key_hash "
        "-- the underlying files or eligibility code have drifted since the freeze; STOP")
    assert header_elig["scaffold_group_hash"] == freeze_manifest["scaffold_group_hash"]
    assert header_elig["spectrum_manifest_hash"] == freeze_manifest["spectrum_manifest_hash"]
    matched = pd.read_parquet(SCRATCH / "msnlib_metadata/matched_scans.parquet")

    eligible_keys = set(header_elig["eligible_keys"])
    ok = matched[matched.key.isin(eligible_keys) & matched.window_ok]
    allowed = {(r.file, r.spectrum_id) for r in ok.itertuples(index=False)}

    candidate = json.loads((REPO / "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json").read_text())
    ta_ridge = json.loads((REPO / "artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json").read_text())

    # The freeze commit cannot be a field *inside* freeze_manifest.json (a commit's hash is a
    # function of its own tree, so no commit can embed its own resultant SHA -- a governance-
    # review finding). Resolve it live instead: this script must be run immediately after the
    # freeze commit, with nothing else committed in between ("simpler is better: freeze commit
    # == validation-access HEAD" -- the master mandate's own stated preference). The guard's
    # _bind_to_freeze_commit still independently verifies the on-disk freeze doc/manifest are
    # byte-identical to what is actually committed at this HEAD, which is the real protection
    # against an uncommitted edit slipping through.
    expected_freeze_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                                             text=True, check=True).stdout.strip()

    guard = ConfirmationAccessGuard(
        record_path=OUTDIR / "validation_access.json",
        freeze_doc_path=REPO / "MURU_V2_MSNLIB_CONFIRMATION_FREEZE.md",
        freeze_manifest_path=OUTDIR / "freeze_manifest.json",
        expected_freeze_commit=expected_freeze_commit,
        actual_candidate_hash=sha256_of(candidate), actual_comparator_hash=sha256_of(ta_ridge),
        actual_population_key_hash=header_elig["validation_key_hash"],
        actual_scaffold_group_hash=header_elig["scaffold_group_hash"],
        actual_spectrum_manifest_hash=header_elig["spectrum_manifest_hash"],
        allowed_spectrum_keys=allowed,
        code_allowlist=set(freeze_manifest.get("code_allowlist", [])),
        root=REPO,
    )
    print("GUARD AUTHORIZED -- population is now permanently EXPOSED", file=sys.stderr)

    vals = []
    for fn, g in ok.groupby("file"):
        peaks = X.decode_selected(DL / fn, g.spectrum_id.tolist(), guard)
        mh_by_key = pd.read_csv(OUTDIR / "eligible_population.csv").set_index("key").mh
        for r in g.itertuples(index=False):
            mz, it = peaks[r.spectrum_id]
            m_prec = float(mh_by_key.loc[r.key])
            vals.append({"key": r.key, "energy": r.energy, "file": fn, "spectrum_id": r.spectrum_id,
                         "mu": MM.spectrum_mu(mz, it, m_prec), "n_peaks": int(mz.size)})
    v = pd.DataFrame(vals)
    agg = v.dropna(subset=["mu"]).groupby(["key", "energy"]).agg(mu=("mu", "median"), n_spectra=("mu", "size")).reset_index()
    # CSV, not parquet: *.parquet is globally gitignored in this repo (would otherwise silently
    # drop the actual one-look outcome data from the tracked/auditable record).
    agg.to_csv(OUTDIR / "measured_mu.csv", index=False)
    v.to_csv(OUTDIR / "measured_mu_raw_per_spectrum.csv", index=False)
    print(f"decoded {len(v)} spectra, {agg.key.nunique()} compounds with >=1 measured rung", file=sys.stderr)
    print(f"empty/nonpositive mu: {int(v.mu.isna().sum())}", file=sys.stderr)


if __name__ == "__main__":
    main()
