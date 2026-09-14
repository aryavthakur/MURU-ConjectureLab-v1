"""MSnLib confirmation study 2, protocol V2 section 5: the clean eligible scaffold-group universe.

design 12b scaffold groups (census) minus every group in the committed, pinned exposure registry. Identity and
structure only. Writes the sorted eligible group list and its manifest; both are committed and hashed in the
protocol BEFORE the randomness pulse exists. Deterministic: a rerun must reproduce the same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import msnlib_design as MD        # noqa: E402

OUT = ROOT / "artifacts/wur_v2_confirmation_v2/population"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msnlib-home", default=os.environ.get("MURU_MSNLIB_HOME", str(Path.home() / "muru-msnlib")))
    args = ap.parse_args()
    home = Path(args.msnlib_home)
    reg_manifest = ROOT / DA.REGISTRY_MANIFEST
    if MD.sha256_file(reg_manifest) != DA.REGISTRY_MANIFEST_SHA256:
        raise SystemExit("exposure registry manifest is not the pinned one")
    design = MD.load_design(home / "merlin_metadata", home / "cache" / "confirmation_v2")
    keys12b, key_scaf, groups12b = MD.design12b(design)
    excluded_groups = set((ROOT / DA.EXCLUDED_GROUPS).read_text().split("\n")) - {""}
    excluded_keys = set((ROOT / DA.EXCLUDED_KEYS).read_text().split("\n")) - {""}
    by_group: dict[str, set] = {}
    for k in keys12b:
        by_group.setdefault(key_scaf[k], set()).add(k)
    eligible = sorted(g for g in groups12b if g not in excluded_groups and not (by_group[g] & excluded_keys))
    eligible_keys = sorted(k for g in eligible for k in by_group[g])
    if set(eligible) & excluded_groups or set(eligible_keys) & excluded_keys:
        raise SystemExit("eligible universe intersects the exposure registry")
    OUT.mkdir(parents=True, exist_ok=True)
    text = "\n".join(eligible) + "\n"
    target = OUT / "eligible_scaffold_groups.txt"
    if target.exists() and target.read_text() != text:
        raise SystemExit("an eligible group list with different content already exists; it is committed once")
    target.write_text(text)
    manifest = {
        "study_id": DA.STUDY_ID_V2,
        "definition": "sorted(design-12b census scaffold groups) minus every scaffold group in the exposure registry; "
                      "a group is kept only if none of its 12b compounds is an excluded key",
        "n_eligible_groups": len(eligible),
        "eligible_groups_sha256_sorted_newline_joined": MD.sha256_lines(eligible),
        "eligible_scaffold_groups_txt_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "n_eligible_compounds": len(eligible_keys),
        "eligible_compounds_sha256_sorted_newline_joined": MD.sha256_lines(eligible_keys),
        "registry_manifest_sha256": DA.REGISTRY_MANIFEST_SHA256,
        "design12b_keys_sha256": MD.DESIGN12B_SHA256, "design12b_groups_sha256": MD.DESIGN12B_GROUPS_SHA256,
        "n_design12b_groups": len(groups12b),
    }
    (OUT / "eligible_universe_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
