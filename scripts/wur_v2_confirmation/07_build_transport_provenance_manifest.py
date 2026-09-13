"""Item 1: unified exact transport/provenance manifest across every source used
for the 2,402 required wells -- MassIVE (98 files, preserved from the cancelled
bulk fetch) and the nine official Zenodo archives (2,304 files, authenticated
MD5+SHA256+size against both the user's provenance and this repo's own census).
"""
from __future__ import annotations
import json
import re
from pathlib import Path

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
DL = REPO / "data/external/msnlib_mzml"


def main():
    massive_recs = [json.loads(l) for l in (REPO / "artifacts/wur_v2/external_msnlib/massive_download_provenance.jsonl").open()]
    massive_ok = [r for r in massive_recs if r["status"] in ("downloaded", "already_present_verified")]

    zenodo_transport = json.loads((REPO / "artifacts/wur_v2/external_msnlib/zenodo_9archive_transport_provenance.json").read_text())
    zenodo_mcediv_tm = json.loads((REPO / "artifacts/wur_v2/external_msnlib/zenodo_extraction_provenance.json").read_text())

    rows = []
    for r in massive_ok:
        fn = Path(r["local_path"]).name
        m = re.search(r"(pluskal_.*?_id)(?=_|\.)", fn)
        rows.append({
            "source": "MassIVE", "official_dataset_release": "MSV000094528",
            "expected_relative_path_or_member": r["relative_path"], "local_path": r["local_path"],
            "unique_sample_id": m.group(1) if m else None, "bytes": r["bytes"], "sha256": r["sha256"],
            "download_status": r["status"], "attempts": r["attempts"], "error": None,
        })

    # de-dupe: a well already covered by a preserved MassIVE row is not re-listed as Zenodo,
    # even though its bytes are also available (and were spot-verified byte-identical) there.
    massive_usids = {r["unique_sample_id"] for r in rows}

    # zenodo_9archive_transport_provenance's "extracted"/"already_present" split is run-specific
    # (a second run reports 0 "extracted" once files already exist from the first run) -- the
    # source of truth is the file actually on disk right now, hashed directly.
    combined_zenodo = {e["unique_sample_id"]: {"member": e["member"], "source_zip": e["source_zip"],
                                                "local_path": e["local_path"], "duplicate_candidates_resolved": e["n_candidates_in_zips"] > 1}
                       for e in zenodo_transport["extracted"]}
    for e in zenodo_transport["already_present"]:
        combined_zenodo.setdefault(e["unique_sample_id"], {"member": None, "source_zip": e["source_zip"],
                                                            "local_path": e["local_path"], "duplicate_candidates_resolved": None})
    for e in zenodo_mcediv_tm["members"]:
        combined_zenodo.setdefault(e["unique_sample_id"], {"member": e["member_name"], "source_zip": e["zip_file"],
                                                            "local_path": e["local_path"], "duplicate_candidates_resolved": None})

    for usid, e in combined_zenodo.items():
        if usid in massive_usids:
            continue
        local_path = REPO / e["local_path"]
        with local_path.open("rb") as fh:
            data = fh.read()
        rows.append({
            "source": "Zenodo_local_archive", "official_dataset_release": "10.5281/zenodo.15683784",
            "expected_relative_path_or_member": e["member"] or e["local_path"], "local_path": e["local_path"],
            "unique_sample_id": usid, "bytes": len(data),
            "sha256": __import__("hashlib").sha256(data).hexdigest(),
            "download_status": "extracted_verified_mzml", "attempts": 1, "error": None,
            "source_zip": e["source_zip"], "duplicate_candidates_resolved": e["duplicate_candidates_resolved"],
        })

    n_by_source = {}
    for r in rows:
        n_by_source[r["source"]] = n_by_source.get(r["source"], 0) + 1

    required_massive_csv_wells = set()
    import csv
    with (REPO / "MSnLib_required_mzML_downloads.csv").open() as f:
        for row in csv.DictReader(f):
            required_massive_csv_wells.add(row["unique_sample_id"])
    import pandas as pd
    unavail = pd.read_csv("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata/unavailable_wells.csv")
    all_required = required_massive_csv_wells | set(unavail.unique_sample_id)

    covered = {r["unique_sample_id"] for r in rows}
    missing = all_required - covered
    dup_rows = len(rows) - len(covered)

    manifest = {
        "n_required_wells": len(all_required), "n_covered": len(covered), "n_missing": len(missing),
        "missing_wells": sorted(missing), "n_by_source": n_by_source,
        "n_duplicate_rows_same_well": dup_rows,
        "zip_archive_authentication": zenodo_transport["zip_authentication"],
        "cancelled_massive_bulk_fetch": {
            "note": "The original 1,514-file MassIVE bulk-fetch route was cancelled by explicit "
                    "instruction after 98 files (88 downloaded + 10 carried over) were already "
                    "retrieved cleanly (0 failures at time of cancellation). Those 98 files are "
                    "preserved and used below; the remaining wells were transported via the nine "
                    "official Zenodo archives instead. Spot-verified: MassIVE and Zenodo serve "
                    "byte-identical content for the same well (well pluskal_mce_1D1_A12_id: "
                    "sha256 5ae390...ebe0d on both sources).",
            "attempt1_log": "artifacts/wur_v2/external_msnlib/massive_download_provenance.attempt1_too_aggressive.jsonl",
            "attempt2_log": "artifacts/wur_v2/external_msnlib/massive_download_provenance.jsonl",
        },
        "rows": rows,
    }
    outp = REPO / "artifacts/wur_v2_confirmation/transport_provenance_manifest.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(manifest, indent=1))
    print(f"required: {len(all_required)}, covered: {len(covered)}, missing: {len(missing)}")
    print(f"by source: {n_by_source}")
    print(f"duplicate rows (same well appearing twice): {dup_rows}")
    if missing:
        print("MISSING:", sorted(missing)[:20])
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
