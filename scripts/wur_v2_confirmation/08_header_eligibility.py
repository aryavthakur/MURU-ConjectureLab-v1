"""Step 4/5: frozen header-only eligibility pass over the 2,402 required files,
using ONLY the repo's existing, already-tested muru.wur_v2.external_msnlib /
external_mzml functions (fixed_rung_scans, match_compounds, eligible,
scan_headers). No new eligibility logic is invented here. Binary <binary>
arrays are never decoded: scan_headers() removes binaryDataArrayList before
reading any cvParam.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
sys.path.insert(0, str(REPO / "src"))
from muru.wur_v2 import external_mzml as X          # noqa: E402
from muru.wur_v2 import external_msnlib as L        # noqa: E402

MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
DL = REPO / "data/external/msnlib_mzml"
MIN_GROUPS = 500


def build_wells_table() -> pd.DataFrame:
    """key, unique_sample_id, fn (basename on disk), mh, scaffold_group -- one required file per well."""
    massive = pd.read_csv(REPO / "MSnLib_required_mzML_downloads.csv")
    massive = massive.rename(columns={"filename": "massive_path"})
    massive["fn"] = massive.massive_path.str.rsplit("/", n=1).str[-1]
    massive = massive[["scaffold_group", "compound_key", "unique_sample_id", "fn"]]

    zprov = json.loads((REPO / "artifacts/wur_v2/external_msnlib/zenodo_extraction_provenance.json").read_text())
    zrows = []
    dsub = pd.read_parquet(MD / "sampled_compound_wells.parquet")
    scaf_by_key = dsub.drop_duplicates("key").set_index("key").scaffold_group
    unavail = pd.read_csv(MD / "unavailable_wells.csv")
    for m in zprov["members"]:
        usid = m["unique_sample_id"]
        keys_here = unavail[unavail.unique_sample_id == usid].compound_key.unique()
        for k in keys_here:
            zrows.append({"scaffold_group": scaf_by_key.get(k), "compound_key": k,
                           "unique_sample_id": usid, "fn": m["member_name"].rsplit("/", 1)[-1]})
    zdf = pd.DataFrame(zrows)

    wells = pd.concat([massive, zdf], ignore_index=True)
    wells = wells.rename(columns={"compound_key": "key"})

    mh_map = pd.read_parquet(MD / "sampled_compound_wells.parquet").drop_duplicates("key").set_index("key").mh
    wells["mh"] = wells.key.map(mh_map)
    return wells


def compute_header_eligibility() -> dict:
    """Callable, reusable core: recomputes header-only eligibility fresh from whatever
    files are on disk right now. Used both by this script's CLI entry point AND by
    11_run_one_look.py immediately before constructing the guard, so the guard's hash
    cross-check reflects a live recomputation rather than a stale cached JSON read."""
    wells = build_wells_table()
    print(f"wells table: {len(wells)} (key, well) rows, {wells.key.nunique()} distinct compounds, "
          f"{wells.fn.nunique()} distinct files", file=sys.stderr)

    missing_files = sorted(set(wells.fn) - {p.name for p in DL.glob("*.mzML")})
    if missing_files:
        print(f"WARNING: {len(missing_files)} required files not yet on disk (download incomplete): "
              f"{missing_files[:5]}", file=sys.stderr)

    headers = {}
    n_headers_read = 0
    for fn in sorted(set(wells.fn) - set(missing_files)):
        rows = X.scan_headers(DL / fn)
        h = pd.DataFrame(rows)
        if "index" not in h.columns or h.empty:
            headers[fn] = pd.DataFrame(columns=["index", "ms_level", "selected_ion_mz", "collision_energy",
                                                 "spectrum_id", "scan_window_lower_limit", "scan_window_upper_limit", "rung"])
            continue
        headers[fn] = L.fixed_rung_scans(h)
        n_headers_read += 1

    print(f"headers read for {n_headers_read} files", file=sys.stderr)

    matched = L.match_compounds(wells[["key", "unique_sample_id", "fn", "mh"]].dropna(subset=["mh"]), headers)
    eligible_keys = L.eligible(matched)
    print(f"compounds with both rungs matched, window ok: {len(eligible_keys)}", file=sys.stderr)

    scaf_by_key = wells.drop_duplicates("key").set_index("key").scaffold_group
    eligible_groups = sorted({scaf_by_key.get(k) for k in eligible_keys if scaf_by_key.get(k) is not None})
    print(f"surviving scaffold groups: {len(eligible_groups)}", file=sys.stderr)

    if len(eligible_groups) < MIN_GROUPS:
        print(f"STOP: only {len(eligible_groups)} scaffold groups survive header-only eligibility "
              f"(< frozen floor {MIN_GROUPS}). Reporting inadequate population, not proceeding.", file=sys.stderr)

    validation_key_hash = hashlib.sha256("\n".join(sorted(eligible_keys)).encode()).hexdigest()
    scaffold_group_hash = hashlib.sha256("\n".join(eligible_groups).encode()).hexdigest()
    ok_matched = matched[matched.key.isin(eligible_keys) & matched.window_ok]
    spectrum_manifest_entries = sorted(f"{r.file}:{r.spectrum_id}" for r in ok_matched.itertuples(index=False))
    spectrum_manifest_hash = hashlib.sha256("\n".join(spectrum_manifest_entries).encode()).hexdigest()

    attrition = {
        "sampled_compounds": int(wells.key.nunique()),
        "sampled_groups": len(set(scaf_by_key.reindex(wells.key.unique()).dropna())),
        "compounds_with_required_file_on_disk": int(wells[~wells.fn.isin(missing_files)].key.nunique()),
        "compounds_surviving_header_eligibility": len(eligible_keys),
        "groups_surviving_header_eligibility": len(eligible_groups),
        "n_missing_files": len(missing_files),
    }

    out = {
        "eligible_keys": sorted(eligible_keys), "eligible_groups": eligible_groups,
        "validation_key_hash": validation_key_hash, "scaffold_group_hash": scaffold_group_hash,
        "spectrum_manifest_hash": spectrum_manifest_hash,
        "n_eligible_spectra": len(spectrum_manifest_entries), "attrition": attrition,
        "min_groups_floor": MIN_GROUPS, "passes_floor": len(eligible_groups) >= MIN_GROUPS,
    }
    matched.to_parquet(MD / "matched_scans.parquet")   # side effect: needed by run_one_look.py's decode step
    return out


def main():
    out = compute_header_eligibility()
    outp = REPO / "artifacts/wur_v2_confirmation/header_eligibility.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("eligible_keys", "eligible_groups")}, indent=2))
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
