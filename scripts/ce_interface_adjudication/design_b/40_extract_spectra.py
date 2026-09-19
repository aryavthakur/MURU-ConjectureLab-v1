"""Design B step 40: frozen observed-spectrum extraction from acquired mzML (centroid mode).

One compound per injection. For each (compound, NCE) cell of one injection:
  1. MS1 extracted-ion chromatogram (XIC) of the theoretical [M+H]+ at +-5 ppm (sum of centroid intensities).
     Apex = highest XIC scan. Peak window = the maximal contiguous run of MS1 scans around the apex whose XIC is
     >= 50% of the apex XIC; its retention-time span is the window.
  2. Qualifying MS2 scan: MS level 2; isolation target within 0.01 m/z of the theoretical [M+H]+; collision
     energy equal to the cell's NCE (within 0.01); its nearest preceding MS1 scan (its acquisition cycle) lies
     inside the window; precursor purity of that MS1 scan >= 0.80, where purity = XIC intensity / total MS1 centroid intensity in
     [mh - 0.5, mh + 0.5].
  3. A cell passes with >= 3 qualifying scans. Its observed spectrum is the concatenation of the centroid peak
     lists of all qualifying scans, unmodified: no noise filter, no intensity threshold, no deduplication. The
     frozen similarity layer bins at its fixed grid and pools by addition, so concatenation equals summation.
An injection passes when all five cells pass. A compound whose primary injection fails is re-injected once
(longer gradient); if that injection passes, all five cells come from it; otherwise the compound is excluded as
ACQUISITION_FAILURE. Cells are never mixed across injections. Reproducibility re-injections never enter the
primary analysis.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

XIC_PPM = 5.0
APEX_FRACTION = 0.50
ISOLATION_TOL_MZ = 0.01
NCE_TOL = 0.01
PURITY_HALF_WIDTH_MZ = 0.5
PURITY_MIN = 0.80
MIN_QUALIFYING_SCANS = 3


def xic(mz: np.ndarray, it: np.ndarray, target: float) -> float:
    tol = target * XIC_PPM * 1e-6
    return float(it[np.abs(mz - target) <= tol].sum())


def purity(mz: np.ndarray, it: np.ndarray, target: float) -> float:
    win = it[np.abs(mz - target) <= PURITY_HALF_WIDTH_MZ].sum()
    return float(xic(mz, it, target) / win) if win > 0 else 0.0


def peak_window(ms1: list, target: float):
    """ms1: list of scans in acquisition order. Returns (rt_lo, rt_hi, apex_xic) or None if not detected."""
    x = np.array([xic(s["mz"], s["it"], target) for s in ms1])
    if len(x) == 0 or x.max() <= 0:
        return None
    a = int(x.argmax())
    lo = hi = a
    while lo - 1 >= 0 and x[lo - 1] >= APEX_FRACTION * x[a]:
        lo -= 1
    while hi + 1 < len(x) and x[hi + 1] >= APEX_FRACTION * x[a]:
        hi += 1
    return ms1[lo]["rt"], ms1[hi]["rt"], float(x[a])


def extract_injection(scans: list, target: float, nce_grid=C.NCE_GRID) -> dict:
    """scans: acquisition-ordered dicts {level, rt, mz, it, [isolation, nce]}. Returns per-cell results."""
    ms1 = [s for s in scans if s["level"] == 1]
    w = peak_window(ms1, target)
    cells = {}
    for nce in nce_grid:
        if w is None:
            cells[nce] = {"pass": False, "n_qualifying": 0, "reason": "precursor_not_detected"}
            continue
        q, last_ms1 = [], None
        for s in scans:
            if s["level"] == 1:
                last_ms1 = s
                continue
            if (s["level"] == 2 and abs(s["isolation"] - target) <= ISOLATION_TOL_MZ and abs(s["nce"] - nce) <= NCE_TOL
                    and last_ms1 is not None and w[0] <= last_ms1["rt"] <= w[1]
                    and purity(last_ms1["mz"], last_ms1["it"], target) >= PURITY_MIN):
                q.append(s)
        ok = len(q) >= MIN_QUALIFYING_SCANS
        cells[nce] = {"pass": ok, "n_qualifying": len(q),
                      "reason": "" if ok else f"fewer_than_{MIN_QUALIFYING_SCANS}_qualifying_scans",
                      "mz": [float(v) for s in q for v in s["mz"]] if ok else [],
                      "intensity": [float(v) for s in q for v in s["it"]] if ok else []}
    return {"pass": all(c["pass"] for c in cells.values()), "window": w, "cells": cells}


def compound_outcome(primary: dict, reinjection: dict | None) -> dict:
    if primary["pass"]:
        return {"status": "ANALYSABLE", "source": "primary", "cells": primary["cells"]}
    if reinjection is not None and reinjection["pass"]:
        return {"status": "ANALYSABLE", "source": "reinjection", "cells": reinjection["cells"]}
    return {"status": "ACQUISITION_FAILURE", "source": None, "cells": {}}


def read_mzml(path: Path) -> list:
    """Thin reader. Collision energy is read from the mzML 'collision energy' cvParam (MS:1000045) as the NCE."""
    import pymzml  # noqa: PLC0415
    out = []
    for sp in pymzml.run.Reader(str(path)):
        lvl = sp.ms_level
        peaks = sp.peaks("centroided")
        rec = {"level": lvl, "rt": float(sp.scan_time_in_minutes()) * 60.0,
               "mz": np.asarray(peaks[:, 0], float) if len(peaks) else np.zeros(0),
               "it": np.asarray(peaks[:, 1], float) if len(peaks) else np.zeros(0)}
        if lvl == 2:
            rec["isolation"] = float(sp.get("MS:1000827") or sp.selected_precursors[0]["mz"])
            rec["nce"] = float(sp.get("MS:1000045"))
        out.append(rec)
    return out


ROOT = HERE.parents[2]
OBS = ROOT / "artifacts/ce_interface_adjudication/design_b/observed"
SHEET_COLUMNS = ("injection_id", "parent_key", "injection_type", "mzml_path", "mzml_sha256")


REPRO_PER_STRATUM = 9   # 27 = about 15% of 198, balanced


def reproducibility_set(man) -> set:
    """Deterministic: per stratum, the 9 accepted compounds with the smallest sha256(study|repro|parent_key)."""
    import hashlib  # noqa: PLC0415
    k = man.assign(_h=[hashlib.sha256(f"{C.STUDY_ID}|repro|{p}".encode()).hexdigest() for p in man["parent_key"]])
    return set(k.sort_values("_h").groupby("stratum").head(REPRO_PER_STRATUM)["parent_key"])


def _git_ref(ref: str) -> str | None:
    import subprocess  # noqa: PLC0415
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", ref], capture_output=True, text=True)
    return r.stdout.strip() or None


def run(sheet_path: Path) -> dict:
    import hashlib  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    for ref in (C.FREEZE_REF, C.PROCUREMENT_REF):
        if not _git_ref(ref):
            raise SystemExit(f"refusing: {ref} does not resolve")
    man = pd.read_csv(ROOT / "artifacts/ce_interface_adjudication/design_b/procurement/procurement_manifest.csv")
    sheet = pd.read_csv(sheet_path, dtype=str)
    if list(sheet.columns[:5]) != list(SHEET_COLUMNS):
        raise SystemExit(f"refusing: acquisition sheet columns must start with {SHEET_COLUMNS}")
    if set(sheet["parent_key"]) - set(man["parent_key"]):
        raise SystemExit("refusing: acquisition sheet names a compound outside the procurement manifest")
    res, outcomes = {}, []
    for r in man.to_dict("records"):
        inj = {}
        for t in ("primary", "reinjection"):
            rows = sheet[(sheet["parent_key"] == r["parent_key"]) & (sheet["injection_type"] == t)]
            if len(rows) > 1:
                raise SystemExit(f"refusing: more than one {t} injection for {r['parent_key']}")
            if len(rows):
                row = rows.iloc[0]
                if hashlib.sha256(Path(row["mzml_path"]).read_bytes()).hexdigest() != row["mzml_sha256"]:
                    raise SystemExit(f"refusing: mzML hash mismatch for {row['injection_id']}")
                inj[t] = extract_injection(read_mzml(Path(row["mzml_path"])), float(r["mh"]))
        if "primary" not in inj:
            outcomes.append({"parent_key": r["parent_key"], "stratum": r["stratum"], "status": "NOT_ACQUIRED"})
            continue
        if inj["primary"]["pass"] and "reinjection" in inj:
            raise SystemExit(f"refusing: {r['parent_key']} was re-injected although its primary injection passed")
        o = compound_outcome(inj["primary"], inj.get("reinjection"))
        outcomes.append({"parent_key": r["parent_key"], "stratum": r["stratum"], "status": o["status"],
                         "source": o["source"]})
        if o["status"] == "ANALYSABLE":
            res[r["parent_key"]] = {str(n): {"mz": c["mz"], "intensity": c["intensity"],
                                             "n_qualifying": c["n_qualifying"]} for n, c in o["cells"].items()}
    repro, want = {}, reproducibility_set(man)
    for row in sheet[sheet["injection_type"] == "reproducibility"].to_dict("records"):
        if row["parent_key"] not in want:
            raise SystemExit(f"refusing: {row['parent_key']} is not in the frozen reproducibility set")
        if hashlib.sha256(Path(row["mzml_path"]).read_bytes()).hexdigest() != row["mzml_sha256"]:
            raise SystemExit(f"refusing: mzML hash mismatch for {row['injection_id']}")
        mh = float(man.set_index("parent_key").loc[row["parent_key"], "mh"])
        e = extract_injection(read_mzml(Path(row["mzml_path"])), mh)
        repro[row["parent_key"]] = {str(n): {"mz": c["mz"], "intensity": c["intensity"]} for n, c in e["cells"].items() if c["pass"]}
    OBS.mkdir(parents=True, exist_ok=True)
    (OBS / "reproducibility_spectra.json").write_text(json.dumps(repro, sort_keys=True) + "\n")
    (OBS / "observed_spectra.json").write_text(json.dumps(res, sort_keys=True) + "\n")
    pd.DataFrame(outcomes).to_csv(OBS / "acquisition_outcomes.csv", index=False)
    return {"analysable": len(res), "outcomes": pd.DataFrame(outcomes)["status"].value_counts().to_dict()}


def main(argv=None) -> int:
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", type=Path, required=True)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.sheet), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
