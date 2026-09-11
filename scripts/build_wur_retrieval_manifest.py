"""Verify the WUR raw files and write artifacts/wur_retrieval_manifest.json.

Usage: python scripts/build_wur_retrieval_manifest.py [data/external/wur]
"""
import json
import sys
from pathlib import Path

from muru.io.wur_retrieval import build_manifest

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    manifest = build_manifest(data_dir)
    out = ROOT / "artifacts" / "wur_retrieval_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    if manifest["missing"] or manifest["hash_mismatches"]:
        print(f"WARNING: {len(manifest['missing'])} missing, "
              f"{len(manifest['hash_mismatches'])} hash mismatches",
              file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {out} ({manifest['n_files']} files verified)")
