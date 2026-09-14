"""MSnLib confirmation study 2, protocol V2 section 9 (part 2): parser preflight on exposed anchors only.

Decodes only through AnchorPreflightAuthority (already-decoded anchor spectra in exposed files). Each allowlisted
spectrum is decoded twice and compared bit for bit; array lengths are checked against defaultArrayLength inside
the decoder; the endpoint must be finite. Prints and writes counts and pass/fail only, never a value.
"""
from __future__ import annotations

import argparse
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

OUT = ROOT / "artifacts/wur_v2_confirmation_v2/anchor_preflight"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor-mzml-dir", required=True)
    args = ap.parse_args()
    auth = DA.AnchorPreflightAuthority(log_path=OUT / "anchor_preflight_decode_log.jsonl")
    allow = pd.DataFrame(DA._rows(ROOT, DA.ANCHOR_ALLOWLIST))
    n_files = n_spec = n_nondet = n_fail = n_nonfinite = n_prec = 0
    failures = []
    for fn, g in allow.groupby("file"):
        path = Path(args.anchor_mzml_dir) / fn
        ids = g.spectrum_id.tolist()
        try:
            a = X.decode_selected(path, ids, auth)
            b = X.decode_selected(path, ids, auth)
        except Exception as e:                           # noqa: BLE001
            n_fail += 1
            failures.append({"file": fn, "error": type(e).__name__})
            continue
        n_files += 1
        for r in g.itertuples(index=False):
            (mz1, it1), (mz2, it2) = a[r.spectrum_id], b[r.spectrum_id]
            n_spec += 1
            if not (np.array_equal(mz1, mz2) and np.array_equal(it1, it2)):
                n_nondet += 1
            if not np.isfinite(MM.spectrum_mu(mz1, it1, float(r.anchor_mh))):
                n_nonfinite += 1
            n_prec += bool(np.any(np.isclose(mz1, float(r.selected_ion_mz), atol=0.02)))
    result = {"n_allowlisted_spectra": int(len(allow)), "n_files_decoded": n_files, "n_spectra_checked": n_spec,
              "n_nondeterministic": n_nondet, "n_decode_failures": n_fail, "decode_failures": failures,
              "n_nonfinite_endpoint": n_nonfinite, "n_spectra_with_precursor_peak": n_prec,
              "passes": n_fail == 0 and n_nondet == 0 and n_nonfinite == 0 and n_spec == len(allow),
              "note": "anchor spectra only, already decoded by the original anchor gate; counts only, no values"}
    (OUT / "anchor_preflight_result.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0 if result["passes"] else 1


if __name__ == "__main__":
    sys.exit(main())
