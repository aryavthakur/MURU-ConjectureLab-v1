"""MSnLib confirmation study 2, protocol V2 section 8: header-only eligibility of the drawn population.

Reads ZIP members of the nine authenticated archives in memory (never extracted) and parses them only with
external_mzml.scan_headers_rung_only: fixed-rung MS2 rows, no collision energy value, no Assisted scan, no MS3+
row is ever returned. No binary array is decoded. Writes the population and frozen scan allowlist for the freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import external_msnlib as L       # noqa: E402
from muru.wur_v2 import external_mzml as X         # noqa: E402
from muru.wur_v2 import msnlib_design as MD        # noqa: E402

POP = ROOT / "artifacts/wur_v2_confirmation_v2/population"
FREEZE = ROOT / "artifacts/wur_v2_confirmation_v2/freeze"
MIN_GROUPS = 500


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msnlib-home", default=os.environ.get("MURU_MSNLIB_HOME", str(Path.home() / "muru-msnlib")))
    args = ap.parse_args()
    home = Path(args.msnlib_home)
    record = json.loads((ROOT / "artifacts/wur_v2_confirmation_v2/randomness/randomness_and_draw_record.json").read_text())
    sampled = [g for g in (POP / "sampled_scaffold_groups.txt").read_text().split("\n") if g]
    if DA.sha256_lines(sampled) != record["sampled_groups_sha256_sorted_newline_joined"] or len(sampled) != 2000:
        raise SystemExit("sampled group list does not match the randomness record")
    design = MD.load_design(home / "merlin_metadata", home / "cache" / "confirmation_v2")
    keys12b, key_scaf, _ = MD.design12b(design)
    excluded_keys = set((ROOT / DA.EXCLUDED_KEYS).read_text().split("\n")) - {""}
    sset = set(sampled)
    sampled_keys = sorted(k for k in keys12b if key_scaf[k] in sset)
    if set(sampled_keys) & excluded_keys:
        raise SystemExit("a sampled compound is in the exposure registry")
    log(f"sampled: {len(sampled)} groups, {len(sampled_keys)} compounds")

    wells = MD.conflict_free_dev_wells(design, set(sampled_keys))
    members = MD.zip_members(home / "zenodo", verify_zip_sha=True)
    wm = wells.merge(members, on="unique_sample_id", how="left")
    unavailable = wm[wm.member.isna()]
    wm = wm.dropna(subset=["member"])
    exposed_wells = {r["unique_sample_id"] for r in DA._rows(ROOT, DA.EXPOSED_FILES)}
    if set(wm.unique_sample_id) & exposed_wells:
        raise SystemExit("a required well is an exposed well")
    log(f"conflict-free dev-range wells: {len(wells)} rows; with a ZIP member: {len(wm)}; members to read: {wm.member.nunique()}")

    headers, shas = {}, {}
    todo = wm.drop_duplicates("member")[["source_zip", "member", "file"]].sort_values(["source_zip", "member"])
    for zname, g in todo.groupby("source_zip"):
        with zipfile.ZipFile(home / "zenodo" / zname) as zf:
            for i, r in enumerate(g.itertuples(index=False)):
                data = zf.read(r.member)
                shas[r.file] = hashlib.sha256(data).hexdigest()
                rows = X.scan_headers_rung_only(data)
                headers[r.file] = pd.DataFrame(rows, columns=list(X.RUNG_ONLY_COLUMNS))
                del data
        log(f"  {zname}: {len(g)} members read (headers only)")

    matched = L.match_compounds(wm.rename(columns={"file": "fn"})[["key", "unique_sample_id", "fn", "mh"]], headers)
    elig = L.eligible(matched) if not matched.empty else set()
    ok = matched[matched.key.isin(elig) & matched.window_ok].copy()
    sel = {(f, r.spectrum_id): r.selected_ion_mz for f, h in headers.items() for r in h.itertuples(index=False)}
    ok["selected_ion_mz"] = [sel[(f, s)] for f, s in zip(ok.file, ok.spectrum_id)]
    minfo = wm.drop_duplicates("file").set_index("file")
    ok["source_zip"] = ok.file.map(minfo.source_zip)
    ok["member"] = ok.file.map(minfo.member)
    ok["file_sha256"] = ok.file.map(shas)
    ok["rung"] = ok.energy.astype(float).astype(int).astype(str)
    allow = ok[["source_zip", "member", "file", "file_sha256", "unique_sample_id", "spectrum_id", "selected_ion_mz", "key",
                "rung"]].drop_duplicates(["file", "spectrum_id"]).sort_values(["file", "spectrum_id"])
    if allow.duplicated(["file", "spectrum_id"]).any() or ok.duplicated(["file", "spectrum_id"]).sum() != 0:
        raise SystemExit("a scan matches more than one population compound")

    eligible_keys = sorted(elig)
    groups = sorted({key_scaf[k] for k in eligible_keys})
    plated = design.dropna(subset=["key", "unique_sample_id"]).groupby("key").unique_sample_id.apply(lambda s: ";".join(sorted(set(s))))
    first = design.dropna(subset=["key"]).drop_duplicates("key").set_index("key")
    pop = pd.DataFrame({"key": eligible_keys, "scaffold_group": [key_scaf[k] for k in eligible_keys],
                        "mh": [repr(float(first.mh[k])) for k in eligible_keys], "wells": [plated[k] for k in eligible_keys],
                        "smiles": [first.smiles[k] for k in eligible_keys]})
    FREEZE.mkdir(parents=True, exist_ok=True)
    pop.to_csv(ROOT / DA.POPULATION_CSV, index=False)
    allow.to_csv(ROOT / DA.SCAN_ALLOWLIST, index=False)
    required = wm.drop_duplicates("member")[["unique_sample_id", "source_zip", "member", "file", "n_candidates"]].copy()
    required["file_sha256"] = required.file.map(shas)
    required.sort_values("member").to_csv(POP / "required_members.csv", index=False)

    out = {
        "study_id": DA.STUDY_ID_V2,
        "sampled_groups_sha256": record["sampled_groups_sha256_sorted_newline_joined"],
        "sampled_compounds_sha256": DA.sha256_lines(sampled_keys),
        "attrition": {
            "sampled_groups": len(sampled), "sampled_compounds": len(sampled_keys),
            "compounds_with_conflict_free_dev_range_well": int(wells.key.nunique()),
            "compounds_with_a_zip_member": int(wm.key.nunique()),
            "wells_without_zip_member": int(unavailable.unique_sample_id.nunique()),
            "members_read_headers_only": len(headers),
            "compounds_matched_any_rung": int(matched.key.nunique()) if not matched.empty else 0,
            "eligible_compounds": len(eligible_keys), "eligible_scaffold_groups": len(groups),
            "allowlisted_scans": int(len(allow)), "files_with_allowlisted_scans": int(allow.file.nunique()),
        },
        "population_key_hash": DA.sha256_lines(eligible_keys),
        "scaffold_group_hash": DA.sha256_lines(groups),
        "spectrum_manifest_hash": DA.sha256_lines(f"{f}:{s}" for f, s in zip(allow.file, allow.spectrum_id)),
        "min_scaffold_group_floor": MIN_GROUPS, "passes_floor": len(groups) >= MIN_GROUPS,
        "header_reader": "external_mzml.scan_headers_rung_only (no collision energy, Assisted scan or MS3+ row returned)",
        "zip_sha256_verified": MD.ZIPS,
    }
    (POP / "header_eligibility_manifest.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "zip_sha256_verified"}, indent=1))
    if not out["passes_floor"]:
        print(f"STOP: only {len(groups)} scaffold groups survive (< {MIN_GROUPS}); no outcome access", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
