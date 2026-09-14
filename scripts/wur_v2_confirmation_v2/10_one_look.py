"""MSnLib confirmation study 2, protocol V2 section 11: the one and only validation look.

Constructs ConfirmationV2Authority (which writes, commits and pushes the access record before anything else can be
decoded), then decodes exactly the frozen allowlisted scans from their frozen ZIP members and computes the frozen
endpoint. Writes per-spectrum and per-(compound, rung) mu; prints counts only. Population 2 is EXPOSED from the first
decode intent onward, whatever happens next."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import external_multims2 as MM    # noqa: E402
from muru.wur_v2 import external_mzml as X         # noqa: E402

OUT = ROOT / "artifacts/wur_v2_confirmation_v2/result"


def main() -> int:
    auth = DA.ConfirmationV2Authority()
    print("ACCESS RECORD COMMITTED AND PUSHED; population 2 is now EXPOSED", file=sys.stderr)
    allow = pd.DataFrame(DA._rows(ROOT, DA.SCAN_ALLOWLIST))
    mh = {r["key"]: float(r["mh"]) for r in DA._rows(ROOT, DA.POPULATION_CSV)}
    vals = []
    for (zname, member), g in allow.groupby(["source_zip", "member"]):
        peaks = X.decode_selected(X.ZipMember(DA.DEFAULT_ZIP_DIR / zname, member), g.spectrum_id.tolist(), auth)
        for r in g.itertuples(index=False):
            mz, it = peaks[r.spectrum_id]
            vals.append({"key": r.key, "energy": float(r.rung), "file": r.file, "spectrum_id": r.spectrum_id,
                         "mu": MM.spectrum_mu(mz, it, mh[r.key]), "n_peaks": int(mz.size)})
    v = pd.DataFrame(vals)
    OUT.mkdir(parents=True, exist_ok=True)
    v.to_csv(OUT / "measured_mu_per_spectrum.csv", index=False)
    agg = (v.dropna(subset=["mu"]).groupby(["key", "energy"])
             .agg(mu=("mu", "median"), n_spectra=("mu", "size")).reset_index())
    agg.to_csv(OUT / "measured_mu.csv", index=False)
    summary = {"access_record_commit": auth.record.get("access_record_commit"), "n_spectra_decoded": int(len(v)),
               "n_empty_or_nonpositive": int(v.mu.isna().sum()), "n_compounds_with_mu": int(agg.key.nunique())}
    (OUT / "one_look_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
