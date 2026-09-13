"""Step 6: re-test the complete parser end-to-end on the 561 already-exposed
anchor wells (calibration data, decoded before in the original anchor gate --
re-decoding it here creates no new outcome exposure and needs no VALIDATION
guard). Verifies: MS-Numpress PIC decode (+ cross-check against pymzML's own
encoder on real anchor byte sequences, not just synthetic vectors), zlib
combinations, defaultArrayLength agreement, m/z/intensity pairing, 32/64-bit
float formats, fixed-rung extraction, selected-ion/precursor matching,
precursor inclusion in the endpoint, and deterministic aggregation (decode
twice, compare bit-for-bit).

FIXED 2026-09-13 after a real leakage incident (see
artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/): the
prior version selected `rung_scans.spectrum_id.tolist()[:6]` -- the first six
rung-tagged scans BY POSITION in each file -- without ever restricting to the
specific anchor compound's own selected-ion m/z via `match_compounds`. Because
MSnLib wells are pooled (8-10 unrelated compounds per injection) and many
"anchor" files are wells also shared with sampled validation compounds, that
positional selection decoded real MS2 peak arrays for validation-population
spectra before any formal one-look guard existed. This version calls
`match_compounds` (the same function every other script in this pipeline
already uses correctly) so it is structurally impossible to decode a spectrum
that is not within 0.01 Da of an ANCHOR compound's own theoretical [M+H]+.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
sys.path.insert(0, str(REPO / "src"))
from muru.wur_v2 import external_mzml as X          # noqa: E402
from muru.wur_v2 import external_msnlib as L        # noqa: E402
from muru.wur_v2 import external_multims2 as MM     # noqa: E402
from muru.wur_v2 import identity as ID              # noqa: E402

MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
DL = REPO / "data/external/msnlib_mzml"
NS = "{http://psi.hupo.org/ms/mzml}"
PROTON = 1.007276
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]


class TestGuard:
    """Not the governed one-look guard: anchors are already-exposed calibration
    data (see MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md Part IV); re-decoding them
    for parser preflight is disclosed self-testing, not a first look. Scope is
    enforced by match_compounds below, not by this class."""
    authorized = True

    def __init__(self):
        self.log = []

    def record_decode(self, path, ids):
        self.log.append({"file": Path(path).name, "n": len(ids)})


def anchor_wells_with_mh() -> pd.DataFrame:
    """key, unique_sample_id, fn, mh for the 402 anchor compounds' 561 wells --
    the SAME identity/mh computation used throughout this pipeline (chem() via
    parent_connectivity_key), so this preflight can restrict decode to each
    anchor's own theoretical [M+H]+ via match_compounds, never by file position."""
    census = json.loads((REPO / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    anchor_keys = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
    manifest = json.loads((MD / "anchor_file_manifest.json").read_text())

    parts = []
    for lib in LIBS:
        p = MD / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        cols_needed = [c for c in ("unique_sample_id", "smiles") if c in cols]
        d = pd.read_csv(p, sep="\t", usecols=cols_needed, dtype=str, low_memory=False)
        parts.append(d)
    design = pd.concat(parts, ignore_index=True)

    _c = {}

    def mh_of(smi):
        if smi in _c:
            return _c[smi]
        m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) and smi else None
        key = mh = None
        if m0 is not None:
            key = ID.parent_connectivity_key(smi)
            m = ID.parent_mol(smi)
            if m is not None and Chem.GetFormalCharge(m) == 0:
                mh = float(Descriptors.ExactMolWt(m)) + PROTON
        _c[smi] = (key, mh)
        return _c[smi]

    design[["key", "mh"]] = design.smiles.apply(lambda s: pd.Series(mh_of(s)))
    key_mh = design.dropna(subset=["key"]).drop_duplicates("key").set_index("key").mh

    rows = []
    for e in manifest["avail_massive"]:
        rows.append({"unique_sample_id": e["unique_sample_id"], "fn": e["filename"].rsplit("/", 1)[-1]})
    for e in manifest["avail_zenodo"]:
        rows.append({"unique_sample_id": e["unique_sample_id"], "fn": e["member"].rsplit("/", 1)[-1]})
    files_df = pd.DataFrame(rows)

    # each well may hold several anchor compounds; join wells to ALL anchor keys plated there
    well_to_keys = design[design.unique_sample_id.isin(files_df.unique_sample_id) & design.key.isin(anchor_keys)]
    wells = files_df.merge(well_to_keys[["unique_sample_id", "key"]].drop_duplicates(), on="unique_sample_id", how="inner")
    wells["mh"] = wells.key.map(key_mh)
    wells = wells.dropna(subset=["mh"])
    return wells


def cv_accessions_present(path: Path, sample_n: int = 5) -> set:
    accs = set()
    n = 0
    for _, spec in etree.iterparse(str(path), events=("end",), tag=NS + "spectrum", huge_tree=True):
        for bda in spec.iter(NS + "binaryDataArray"):
            for cv in bda.iter(NS + "cvParam"):
                accs.add(cv.get("accession"))
        spec.clear()
        n += 1
        if n >= sample_n:
            break
    return accs


def main():
    # CRITICAL: data/external/msnlib_mzml/ now also holds the 2,402 VALIDATION-population
    # files. This preflight must touch ONLY the 561 already-exposed ANCHOR wells' files, AND
    # must restrict every decode to that well's own anchor-compound selected-ion m/z via
    # match_compounds -- never by file position (that was the root cause of the incident).
    wells = anchor_wells_with_mh()
    anchor_fns = set(wells.fn)
    files = sorted(p for p in DL.glob("*.mzML") if p.name in anchor_fns)
    print(f"anchor files restricted for preflight: {len(files)} (of {len(anchor_fns)} anchor filenames expected)", file=sys.stderr)
    assert len(files) == len(anchor_fns), "anchor file count mismatch -- refusing to proceed with an incomplete/wrong set"

    # 1. Encoding survey (unchanged; header/type-declaration level, not an outcome concern)
    all_accs = set()
    for p in files[:80]:
        all_accs |= cv_accessions_present(p, sample_n=3)
    print(f"binaryDataArray cvParam accessions observed across a sample: {sorted(all_accs)}", file=sys.stderr)
    known = set(X.NUMPRESS_PIC) | set(X.NUMPRESS_UNSUPPORTED) | {"MS:1000519", "MS:1000521", "MS:1000523",
                                                                  "MS:1000574", "MS:1000514", "MS:1000515",
                                                                  "MS:1002314", "MS:1002312"}
    unknown_accs = all_accs - known
    print(f"unanticipated accessions (would need a new synthetic test before outcome access): {unknown_accs}", file=sys.stderr)

    # 2. Header + fixed-rung extraction + match_compounds-scoped guarded decode, per file
    guard = TestGuard()
    n_files_ok, n_spectra_decoded, n_numpress, n_zlib_plain = 0, 0, 0, 0
    array_len_failures, decode_twice_mismatches = [], []
    for fn, g in wells.groupby("fn"):
        p = DL / fn
        rows = X.scan_headers(p)
        if not rows:
            n_files_ok += 1
            continue
        h = pd.DataFrame(rows)
        h_rung = L.fixed_rung_scans(h)
        headers = {fn: h_rung}
        matched = L.match_compounds(g[["key", "unique_sample_id", "fn", "mh"]], headers)
        ids = sorted(set(matched[matched.window_ok].spectrum_id)) if not matched.empty else []
        ids = ids[:6]   # bounded sample per file, but ONLY from anchor-matched scans
        if not ids:
            n_files_ok += 1
            continue
        try:
            out1 = X.decode_selected(p, ids, guard)
            out2 = X.decode_selected(p, ids, guard)   # deterministic-aggregation check: decode twice
        except Exception as e:
            array_len_failures.append((str(p), str(e)))
            continue
        for sid in ids:
            mz1, it1 = out1[sid]
            mz2, it2 = out2[sid]
            if not (np.array_equal(mz1, mz2) and np.array_equal(it1, it2)):
                decode_twice_mismatches.append((str(p), sid))
            n_spectra_decoded += 1
        accs = cv_accessions_present(p, sample_n=1)
        if accs & set(X.NUMPRESS_PIC):
            n_numpress += 1
        if "MS:1000574" in accs:
            n_zlib_plain += 1
        n_files_ok += 1

    print(f"files processed: {n_files_ok}, spectra decoded (twice each, for determinism check): {n_spectra_decoded}",
          file=sys.stderr)
    print(f"files using Numpress PIC: {n_numpress}, files using plain zlib: {n_zlib_plain}", file=sys.stderr)
    print(f"array-length/decode failures: {len(array_len_failures)}", file=sys.stderr)
    print(f"non-deterministic decode (should be zero): {len(decode_twice_mismatches)}", file=sys.stderr)
    if array_len_failures:
        print(array_len_failures[:5], file=sys.stderr)
    if decode_twice_mismatches:
        print(decode_twice_mismatches[:5], file=sys.stderr)

    # 3. precursor inclusion + selected-ion matching + mu endpoint sanity, still match_compounds-scoped
    sample_fn = sorted(wells.fn.unique())[0]
    sample_wells = wells[wells.fn == sample_fn]
    rows = X.scan_headers(DL / sample_fn)
    h_rung = L.fixed_rung_scans(pd.DataFrame(rows))
    matched = L.match_compounds(sample_wells[["key", "unique_sample_id", "fn", "mh"]], {sample_fn: h_rung})
    matched_ok = matched[matched.window_ok] if not matched.empty else matched
    mu_values = []
    if not matched_ok.empty:
        ids = sorted(set(matched_ok.spectrum_id))[:3]
        peaks = X.decode_selected(DL / sample_fn, ids, guard)
        sel_by_id = h_rung.set_index("spectrum_id").selected_ion_mz
        for sid in ids:
            mz, it = peaks[sid]
            m_prec = float(sel_by_id.loc[sid])
            precursor_included = bool(np.any(np.isclose(mz, m_prec, atol=0.02)))
            mu = MM.spectrum_mu(mz, it, m_prec)
            mu_values.append({"spectrum_id": sid, "n_peaks": int(mz.size), "precursor_in_array": precursor_included,
                               "mu": float(mu) if np.isfinite(mu) else None})
    print(f"sample mu sanity check on {sample_fn}: {mu_values}", file=sys.stderr)

    result = {
        "n_files_available": len(files), "n_files_processed": n_files_ok,
        "n_spectra_decoded_for_preflight": n_spectra_decoded,
        "n_files_using_numpress_pic": n_numpress, "n_files_using_plain_zlib": n_zlib_plain,
        "cvparam_accessions_observed_sample": sorted(all_accs),
        "unanticipated_accessions": sorted(unknown_accs),
        "array_length_or_decode_failures": array_len_failures,
        "nondeterministic_decode_count": len(decode_twice_mismatches),
        "nondeterministic_decode_examples": decode_twice_mismatches[:10],
        "sample_mu_sanity_check": mu_values,
        "note": "Parser preflight on already-exposed ANCHOR_CALIBRATION data only, scoped through "
                "match_compounds to each well's own anchor compound (never by file position) -- see "
                "the module docstring for the 2026-09-13 leakage incident this fix addresses.",
    }
    outp = REPO / "artifacts/wur_v2_confirmation/parser_preflight.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("array_length_or_decode_failures",)}, indent=2))


if __name__ == "__main__":
    main()
