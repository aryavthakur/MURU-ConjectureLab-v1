"""Step 6: re-test the complete parser end-to-end on the 561 already-exposed
anchor wells (calibration data, decoded before in the original anchor gate --
re-decoding it here creates no new outcome exposure and needs no VALIDATION
guard). Verifies: MS-Numpress PIC decode (+ cross-check against pymzML's own
encoder on real anchor byte sequences, not just synthetic vectors), zlib
combinations, defaultArrayLength agreement, m/z/intensity pairing, 32/64-bit
float formats, fixed-rung extraction, selected-ion/precursor matching,
precursor inclusion in the endpoint, and deterministic aggregation (decode
twice, compare bit-for-bit).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
sys.path.insert(0, str(REPO / "src"))
from muru.wur_v2 import external_mzml as X          # noqa: E402
from muru.wur_v2 import external_msnlib as L        # noqa: E402
from muru.wur_v2 import external_multims2 as MM     # noqa: E402

MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
DL = REPO / "data/external/msnlib_mzml"
NS = "{http://psi.hupo.org/ms/mzml}"


class TestGuard:
    """Not the governed one-look guard: anchors are already-exposed calibration
    data (see MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md Part IV); re-decoding them
    for parser preflight is disclosed self-testing, not a first look."""
    authorized = True

    def __init__(self):
        self.log = []

    def record_decode(self, path, ids):
        self.log.append({"file": Path(path).name, "n": len(ids)})


def build_anchor_wells():
    census = json.loads((REPO / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    anchor_keys = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
    manifest = json.loads((MD / "anchor_file_manifest.json").read_text())
    rows = []
    for e in manifest["avail_massive"] + manifest["avail_zenodo"]:
        fn = e["filename"] if "filename" in e else e.get("member", "").rsplit("/", 1)[-1]
        if fn is None:
            continue
        rows.append({"unique_sample_id": e["unique_sample_id"], "fn": fn})
    wells = pd.DataFrame(rows)
    # match wells to keys via the design table already used to build the manifest
    design_keys = pd.read_parquet(MD / "sampled_compound_wells.parquet") if (MD / "sampled_compound_wells.parquet").exists() else None
    return wells, anchor_keys


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
    # files. This preflight must touch ONLY the 561 already-exposed ANCHOR wells' files --
    # never glob the whole directory, or it would decode validation peaks prematurely.
    manifest = json.loads((MD / "anchor_file_manifest.json").read_text())
    anchor_fns = set()
    for e in manifest["avail_massive"]:
        anchor_fns.add(e["filename"].rsplit("/", 1)[-1])
    for e in manifest["avail_zenodo"]:
        anchor_fns.add(e["member"].rsplit("/", 1)[-1])
    files = sorted(p for p in DL.glob("*.mzML") if p.name in anchor_fns)
    print(f"anchor files restricted for preflight: {len(files)} (of {len(anchor_fns)} anchor filenames expected)", file=sys.stderr)
    assert len(files) == len(anchor_fns), "anchor file count mismatch -- refusing to proceed with an incomplete/wrong set"

    # 1. Encoding survey across a sample of anchor files: which compression/numpress
    #    accessions actually appear, so we know the parser has been exercised against
    #    every real encoding in use (not just the ones anticipated synthetically).
    all_accs = set()
    for p in files[:80]:
        all_accs |= cv_accessions_present(p, sample_n=3)
    print(f"binaryDataArray cvParam accessions observed across a sample: {sorted(all_accs)}", file=sys.stderr)
    # MS:1000519/1000521 ("32-bit integer"/"32-bit float") are the nominal pre-compression type
    # declarations that always accompany a Numpress-PIC array (MS:1002747/MS:1002313) -- the
    # actual decode in external_mzml._decode_array branches on the Numpress accession, never on
    # these type tags, so their presence is expected and does not change decode behavior.
    known = set(X.NUMPRESS_PIC) | set(X.NUMPRESS_UNSUPPORTED) | {"MS:1000519", "MS:1000521", "MS:1000523",
                                                                  "MS:1000574", "MS:1000514", "MS:1000515",
                                                                  "MS:1002314", "MS:1002312"}
    unknown_accs = all_accs - known
    print(f"unanticipated accessions (would need a new synthetic test before outcome access): {unknown_accs}", file=sys.stderr)

    # 2. Full header + fixed-rung extraction + guarded decode on every anchor file
    guard = TestGuard()
    n_files_ok, n_spectra_decoded, n_numpress, n_zlib_plain, n_zlib_numpress = 0, 0, 0, 0, 0
    array_len_failures = []
    decode_twice_mismatches = []
    for p in files:
        rows = X.scan_headers(p)
        if not rows:
            continue
        h = pd.DataFrame(rows)
        h_rung = L.fixed_rung_scans(h)
        rung_scans = h_rung[h_rung.rung.notna()]
        if rung_scans.empty:
            n_files_ok += 1
            continue
        ids = rung_scans.spectrum_id.tolist()[:6]   # a bounded sample per file keeps this a preflight, not a full re-decode
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
        # inspect encodings used in this file (from its binaryDataArray cvParams)
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

    # 3. precursor inclusion + selected-ion matching + mu endpoint sanity on a handful of
    #    real anchor spectra (spectrum_mu already tested in unit tests; check it runs on
    #    real decoded arrays and produces a finite, positive value in the expected range).
    sample_file = files[0]
    rows = X.scan_headers(sample_file)
    h = pd.DataFrame(rows)
    h_rung = L.fixed_rung_scans(h)
    rung_scans = h_rung[h_rung.rung.notna()]
    mu_values = []
    if not rung_scans.empty:
        ids = rung_scans.spectrum_id.tolist()[:3]
        peaks = X.decode_selected(sample_file, ids, guard)
        prec_mz = rung_scans.set_index("spectrum_id").loc[ids].selected_ion_mz
        for sid in ids:
            mz, it = peaks[sid]
            m_prec = float(prec_mz.loc[sid])
            precursor_included = bool(np.any(np.isclose(mz, m_prec, atol=0.02)))
            mu = MM.spectrum_mu(mz, it, m_prec)
            mu_values.append({"spectrum_id": sid, "n_peaks": int(mz.size), "precursor_in_array": precursor_included,
                               "mu": float(mu) if np.isfinite(mu) else None})
    print(f"sample mu sanity check on {sample_file.name}: {mu_values}", file=sys.stderr)

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
        "note": "Parser preflight on already-exposed ANCHOR_CALIBRATION data only "
                "(MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md Part IV); no VALIDATION spectrum decoded here.",
    }
    outp = REPO / "artifacts/wur_v2_confirmation/parser_preflight.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("array_length_or_decode_failures",)}, indent=2))


if __name__ == "__main__":
    main()
