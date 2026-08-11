"""T1.11-T1.13 -- extract MS2 from raw mzML, compute endpoints, compare branches.

For each target compound x mix x collision energy:
  * find MS2 scans whose precursor matches on m/z and RT,
  * compute endpoints on each individual scan (within-run scan variability),
  * compute endpoints on the merged scan set (comparable to the curated record).

Output feeds REPEATABILITY.md (variance across mixes) and the branch comparison
(curated RMassBank vs raw mzML on the same compound-energy cells).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.features import COVARIATES, ENDPOINTS  # noqa: E402
from muru.io.mzml import iter_ms2, match_scans, merged_spectrum  # noqa: E402

MZML = ROOT / "data" / "massive" / "mzml"
NAME_RE = re.compile(r"20200303_ENTACT_RP_mix(\d{3})_(pos|neg)_CE(\d+)\.mzML$")


def main() -> None:
    targets = pd.read_csv(ROOT / "artifacts" / "raw_branch_targets.csv")
    files = sorted(MZML.glob("*.mzML"))
    if not files:
        print("no mzML files present; nothing to do")
        return
    print(f"{len(targets)} targets x {len(files)} files")

    rows, scan_rows = [], []
    for f in files:
        m = NAME_RE.search(f.name)
        if not m:
            print(f"  SKIP unrecognised filename: {f.name}")
            continue
        mix, mode, ce = int(m.group(1)), m.group(2), int(m.group(3))
        scans = list(iter_ms2(f))
        print(f"  {f.name}: {len(scans)} MS2 scans", flush=True)

        for t in targets.itertuples():
            hits = match_scans(scans, t.precursor_mz, t.rt_min)
            if not hits:
                rows.append({"inchikey_first_block": t.inchikey_first_block,
                             "mix": mix, "ce_numeric": ce, "n_scans": 0,
                             "source_branch": "raw_mzml"})
                continue
            spec = merged_spectrum(hits, t.precursor_mz)
            row = {"inchikey_first_block": t.inchikey_first_block, "mix": mix,
                   "ce_numeric": ce, "n_scans": len(hits),
                   "precursor_mz": t.precursor_mz, "rt_min": t.rt_min,
                   "source_branch": "raw_mzml"}
            for name, fn in ENDPOINTS.items():
                row[name] = fn(spec)
            for name, fn in COVARIATES.items():
                row[name] = fn(spec)
            rows.append(row)

            for s in hits:
                sp = s.to_spectrum(t.precursor_mz)
                sr = {"inchikey_first_block": t.inchikey_first_block, "mix": mix,
                      "ce_numeric": ce, "scan_id": s.scan_id, "rt_min": s.rt_min}
                for name, fn in ENDPOINTS.items():
                    sr[name] = fn(sp)
                sr["peak_count"] = sp.n_peaks
                scan_rows.append(sr)

    out = ROOT / "artifacts"
    pd.DataFrame(rows).to_parquet(out / "raw_branch_merged.parquet", index=False)
    pd.DataFrame(scan_rows).to_parquet(out / "raw_branch_scans.parquet", index=False)
    print(f"\nmerged rows: {len(rows):,}   individual scan rows: {len(scan_rows):,}")


if __name__ == "__main__":
    main()
