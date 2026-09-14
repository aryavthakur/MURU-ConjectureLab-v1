"""MSnLib confirmation study 2, protocol V2 section 9 (part 1): the anchor parser-preflight allowlist.

Only spectra the original anchor gate already decoded (registry decoded_spectra.csv, E_anchor_gate_attempt2), in
exposed files, whose precursor is within 0.01 Da of exactly one census anchor plated in that well, in an
admissible anchor scope (no co-plated ion or isomer that could share the isolation). Identity and registry data only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import anchor_scope as AS         # noqa: E402
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import msnlib_design as MD        # noqa: E402


def main() -> int:
    home = Path(os.environ.get("MURU_MSNLIB_HOME", str(Path.home() / "muru-msnlib")))
    design = MD.load_design(home / "merlin_metadata", home / "cache" / "confirmation_v2")
    census = json.loads((ROOT / DA.CENSUS).read_text())
    anchors = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
    dec = pd.DataFrame(DA._rows(ROOT, DA.DECODED_SPECTRA))
    dec = dec[dec.event == "E_anchor_gate_attempt2"].drop_duplicates(["file", "spectrum_id"])
    exposed = {r["file"]: r["file_sha256"] for r in DA._rows(ROOT, DA.EXPOSED_FILES)}
    ok = design.dropna(subset=["key"])
    by_well = {u: g for u, g in ok.groupby("unique_sample_id")}
    rows, skipped = [], {"no_admissible_anchor": 0, "ambiguous": 0}
    for r in dec.itertuples(index=False):
        g = by_well.get(r.unique_sample_id)
        well_rows = [{"key": x.key, "mh": x.mh, "m_plus": x.m_plus, "parent_charge": x.parent_charge,
                      "parent_formula": x.parent_formula} for x in g.itertuples(index=False)] if g is not None else []
        admitted, _ = AS.admissible_anchor_scopes(well_rows, anchors)
        mz = float(r.selected_ion_mz)
        hits = [a for a in admitted if abs(a["mh"] - mz) <= DA.SEL_TOL]
        if len(hits) != 1:
            skipped["ambiguous" if hits else "no_admissible_anchor"] += 1
            continue
        rows.append({"file": r.file, "file_sha256": exposed[r.file], "spectrum_id": r.spectrum_id,
                     "selected_ion_mz": r.selected_ion_mz, "anchor_key": hits[0]["key"], "anchor_mh": repr(float(hits[0]["mh"]))})
    out = ROOT / DA.ANCHOR_ALLOWLIST
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["file", "spectrum_id"]).to_csv(out, index=False)
    summary = {"n_gate_spectra": int(len(dec)), "n_allowlisted": len(rows), "n_files": len({r["file"] for r in rows}),
               "n_anchor_keys": len({r["anchor_key"] for r in rows}), "skipped": skipped}
    (out.parent / "anchor_allowlist_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
