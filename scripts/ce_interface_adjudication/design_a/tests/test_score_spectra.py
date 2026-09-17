"""Tests for the Design A step 40 scoring step.

SYNTHETIC ONLY. Every MassBank-format record in this file is hand written here, every prediction dump is
hand written here. No real MassBank record, spectrum file or peak list is downloaded, opened, parsed or
inspected anywhere in this module, and no real prediction output, benchmark result or *_RESULT.md is
read. Nothing here contacts the network or loads a checkpoint.

Style note: ordinary hyphens only, no em dashes or en dashes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

import pandas as pd
import pytest

DESIGN_A = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, DESIGN_A / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load("ce_design_a_40_score_spectra", "40_score_spectra.py")
A = _load("ce_design_a_50_analysis_for_schema_test", "50_analysis.py")


# ------------------------------------------------------------------------------------------------
# synthetic MassBank-format record builder
# ------------------------------------------------------------------------------------------------

CANONICAL_HEADER = "m/z int. rel.int."

# Peaks chosen so that the max-normalised absolute intensities are exact binary64 powers of two
# (1.0, 0.25, 0.0625); their square roots are then exact too, which the sqrt round-trip test needs.
DEFAULT_PEAKS = ((100.0, 16.0, 999), (200.0, 4.0, 250), (300.0, 1.0, 62))


def record_text(accession="MSBNK-Test-TT000001", peaks=DEFAULT_PEAKS, num_peak=None,
                precursor="500.1234", peak_block=True, num_peak_line=True,
                header=CANONICAL_HEADER, peak_lines=None, newline="\n", indent="  ",
                trailing="", terminator=True):
    """Build a synthetic record in the MassBank text format. Every defect is opt in."""
    if num_peak is None:
        num_peak = len(peaks) if peak_lines is None else len(peak_lines)
    lines = [
        f"ACCESSION: {accession}",
        "RECORD_TITLE: Synthetic fixture; LC-ESI-QFT; MS2",
        "AC$MASS_SPECTROMETRY: MS_TYPE MS2",
        "AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE HCD",
    ]
    if precursor is not None:
        lines.append(f"MS$FOCUSED_ION: PRECURSOR_M/Z {precursor}")
    lines.append("MS$FOCUSED_ION: PRECURSOR_TYPE [M+H]+")
    lines.append("PK$SPLASH: splash10-0000-0000000000-000000000000000000")
    if num_peak_line:
        lines.append(f"PK$NUM_PEAK: {num_peak}")
    if peak_block:
        lines.append(f"PK$PEAK: {header}")
        if peak_lines is None:
            peak_lines = [f"{mz} {inten} {rel}" for mz, inten, rel in peaks]
        lines.extend(indent + line for line in peak_lines)
    if terminator:
        lines.append("//")
    return newline.join(lines) + newline + trailing


def dump_entry(spec, mz, inten, prefix=True):
    return {
        "name": ("pred_" + spec) if prefix else spec,
        "remark": None,
        "collision_key": "collision 30",
        "stored_collision_energy": 30.0,
        "root_canonical_smiles": "CCO",
        "adduct": "[M+H]+",
        "natoms": 3,
        "masses_float32": list(mz),
        "intens_float32": list(inten),
        "is_root_fragment": [False] * len(mz),
        "frag_popcount": [1] * len(mz),
    }


# ------------------------------------------------------------------------------------------------
# synthetic repository builder
# ------------------------------------------------------------------------------------------------

DEFAULT_MH = 500.0


def make_root(tmp_path, records, texts, spectra, freeze=True, hashes="correct", entry_override=None):
    """A throwaway repo carrying a population, a record directory and the six prediction dumps.

    records      list of (record_id, compound_id, scaffold_group, nce, theoretical_mh, source_file)
    texts        source_file -> record text, or None to leave the file absent
    spectra      spec id -> (mz list, inten list), used for every (model, mapping) dump
    entry_override  optional callable (model_label, mapping, spec, entry) -> entry or None (drop it)
    """
    root = Path(tmp_path) / "repo"
    (root / "artifacts/ce_interface_adjudication/design_a/population").mkdir(parents=True, exist_ok=True)
    pred_dir = root / M.PRED_DIR_REL
    pred_dir.mkdir(parents=True, exist_ok=True)
    records_dir = root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    header = "record_id,compound_id,scaffold_group,nce,theoretical_mh,source_file\n"
    body = "".join(f"{r[0]},{r[1]},{r[2]},{float(r[3])},{r[4]!r},{r[5]}\n" for r in records)
    csv_path = root / M.RECORDS_CSV_REL
    csv_path.write_text(header + body, encoding="utf-8")

    sha = M.sha256_file(csv_path)
    if hashes == "mismatch":
        sha = hashlib.sha256(b"not the frozen population").hexdigest()
    (root / M.POP_MANIFEST_REL).write_text(
        json.dumps({"script": "synthetic", "outputs_written": {M.RECORDS_CSV_REL: sha}}, indent=1)
        + "\n", encoding="utf-8")

    for name, text in texts.items():
        if text is not None:
            (records_dir / name).write_text(text, encoding="utf-8")

    for model_key, model_label in M.MODEL_KEYS:
        for mapping in M.MAPPINGS:
            payload = []
            for spec, (mz, inten) in sorted(spectra.items()):
                entry = dump_entry(spec, mz, inten)
                if entry_override is not None:
                    entry = entry_override(model_label, mapping, spec, entry)
                if entry is not None:
                    payload.append(entry)
            (pred_dir / M.dump_filename(model_key, mapping)).write_text(
                json.dumps(payload), encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "--allow-empty", "-m", "init"], cwd=root, check=True, capture_output=True)
    if freeze:
        subprocess.run(["git", "update-ref", M.FREEZE_REF, "HEAD"], cwd=root, check=True,
                       capture_output=True)
    return root, records_dir


EXEC_OK = {M.EXECUTE_ENV_VAR: "1"}

ONE_RECORD = [("MSBNK-Test-TT000001", "CMPD0000000001", "SG_A", 30, DEFAULT_MH,
               "MSBNK-Test-TT000001.txt")]
ONE_SPEC = {"CMPD0000000001_NCE30": ([100.0, 200.0, 300.0], [1.0, 0.5, 0.25])}


def run_one(tmp_path, text, **kwargs):
    """Score a single synthetic record whose text is `text`, returning the six rows."""
    root, records_dir = make_root(tmp_path, ONE_RECORD, {"MSBNK-Test-TT000001.txt": text}, ONE_SPEC,
                                  **kwargs)
    return M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]


# ------------------------------------------------------------------------------------------------
# 1. the parser on a well formed record
# ------------------------------------------------------------------------------------------------

def test_well_formed_record_parses_to_the_exact_expected_peaks_precursor_and_accession():
    parsed = M.parse_massbank_record(record_text())
    assert parsed["accession"] == "MSBNK-Test-TT000001"
    assert parsed["deposited_precursor_mz"] == 500.1234
    assert parsed["n_peak_declared"] == 3
    assert parsed["mz"] == [100.0, 200.0, 300.0]
    assert parsed["intensity"] == [16.0, 4.0, 1.0]
    assert parsed["relative_intensity"] == [999.0, 250.0, 62.0]


def test_observed_spectrum_uses_the_absolute_intensity_column():
    parsed = M.parse_massbank_record(record_text())
    mz, inten = M.observed_spectrum(parsed)
    assert M.OBSERVED_INTENSITY_COLUMN_INDEX == 1
    assert mz == [100.0, 200.0, 300.0]
    assert inten == parsed["intensity"] == [16.0, 4.0, 1.0]
    assert inten != parsed["relative_intensity"]


def test_absolute_and_relative_columns_give_the_same_similarity_because_both_endpoints_rescale():
    """The frozen column choice cannot change a number when the two columns are proportional."""
    peaks = ((100.0, 16.0, 1000.0), (200.0, 4.0, 250.0), (300.0, 1.0, 62.5))
    parsed = M.parse_massbank_record(record_text(peaks=peaks))
    pred = ([100.0, 200.0, 300.0], [1.0, 0.6, 0.2])
    abs_scores = M.score_pair(pred, (parsed["mz"], parsed["intensity"]), DEFAULT_MH)
    rel_scores = M.score_pair(pred, (parsed["mz"], parsed["relative_intensity"]), DEFAULT_MH)
    assert abs_scores[0] == pytest.approx(rel_scores[0], abs=1e-15)
    assert abs_scores[1] == pytest.approx(rel_scores[1], abs=1e-15)


# ------------------------------------------------------------------------------------------------
# 2. line endings, whitespace, trailing blank line
# ------------------------------------------------------------------------------------------------

def test_crlf_extra_whitespace_and_a_trailing_blank_line_parse_identically():
    reference = M.parse_massbank_record(record_text())

    crlf = M.parse_massbank_record(record_text(newline="\r\n"))
    cr = M.parse_massbank_record(record_text(newline="\r"))
    trailing = M.parse_massbank_record(record_text(trailing="\n"))
    trailing_crlf = M.parse_massbank_record(record_text(newline="\r\n", trailing="\r\n"))

    padded = M.parse_massbank_record(record_text(
        accession=" MSBNK-Test-TT000001",
        peak_lines=["100.0   16.0    999", "\t200.0  4.0  250  ", "300.0 1.0 62   "],
        indent="    ", trailing="   \n\n"))

    for other in (crlf, cr, trailing, trailing_crlf, padded):
        assert other == reference


def test_a_record_without_a_terminator_still_parses():
    assert M.parse_massbank_record(record_text(terminator=False)) == \
        M.parse_massbank_record(record_text())


# ------------------------------------------------------------------------------------------------
# 3. each malformed case yields its documented drop reason and no score value
# ------------------------------------------------------------------------------------------------

MALFORMED_CASES = {
    "no_pk_peak_block": (dict(peak_block=False), M.DROP_MISSING_PK_PEAK_BLOCK),
    "peak_line_with_two_fields": (dict(peak_lines=["100.0 16.0", "200.0 4.0 250", "300.0 1.0 62"]),
                                  M.DROP_MALFORMED_PEAK_LINE),
    "non_numeric_field": (dict(peak_lines=["100.0 sixteen 999", "200.0 4.0 250", "300.0 1.0 62"]),
                          M.DROP_MALFORMED_PEAK_LINE),
    "num_peak_disagrees": (dict(num_peak=7), M.DROP_MALFORMED_PEAK_LINE),
    "num_peak_missing": (dict(num_peak_line=False), M.DROP_MALFORMED_PEAK_LINE),
    "num_peak_not_an_integer": (dict(num_peak="three"), M.DROP_MALFORMED_PEAK_LINE),
    "non_canonical_peak_header": (dict(header="m/z rel.int."), M.DROP_MALFORMED_PEAK_LINE),
    "zero_peaks": (dict(peaks=(), peak_lines=[]), M.DROP_ZERO_PEAKS),
    "no_accession": (dict(accession=""), M.DROP_UNREADABLE_RECORD),
}


@pytest.mark.parametrize("case", sorted(MALFORMED_CASES))
def test_malformed_record_raises_its_documented_drop_reason(case):
    kwargs, expected = MALFORMED_CASES[case]
    with pytest.raises(M.RecordParseError) as exc:
        M.parse_massbank_record(record_text(**kwargs))
    assert exc.value.reason == expected
    assert exc.value.reason in M.DROP_REASONS


@pytest.mark.parametrize("case", sorted(MALFORMED_CASES))
def test_malformed_record_produces_drop_rows_with_no_similarity_value(tmp_path, case):
    kwargs, expected = MALFORMED_CASES[case]
    rows = run_one(tmp_path / case, record_text(**kwargs))
    assert len(rows) == len(M.MODEL_KEYS) * len(M.MAPPINGS) == 6
    for row in rows:
        assert row["drop_reason"] == expected
        assert row["cosine"] is None and row["js"] is None
        assert M.format_value(row["cosine"]) == "" and M.format_value(row["js"]) == ""


def test_an_absent_record_file_is_an_unreadable_record(tmp_path):
    root, records_dir = make_root(tmp_path, ONE_RECORD, {"MSBNK-Test-TT000001.txt": None}, ONE_SPEC)
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    assert {r["drop_reason"] for r in rows} == {M.DROP_UNREADABLE_RECORD}


def test_the_parser_never_returns_a_partial_spectrum(tmp_path):
    """A block whose second line is malformed yields nothing at all, not its first peak."""
    with pytest.raises(M.RecordParseError):
        M.parse_massbank_record(record_text(peak_lines=["100.0 16.0 999", "200.0 4.0", "300.0 1.0 62"]))


def test_a_missing_or_unparseable_precursor_is_not_a_drop():
    """PRECURSOR_M/Z gates nothing, because the frozen parent mass never comes from it."""
    assert M.parse_massbank_record(record_text(precursor=None))["deposited_precursor_mz"] is None
    assert M.parse_massbank_record(record_text(precursor="n/a"))["deposited_precursor_mz"] is None
    assert M.parse_massbank_record(record_text(precursor=None))["mz"] == [100.0, 200.0, 300.0]


# ------------------------------------------------------------------------------------------------
# 4. prediction side drop reasons
# ------------------------------------------------------------------------------------------------

def test_a_missing_prediction_spec_id_yields_missing_prediction(tmp_path):
    root, records_dir = make_root(
        tmp_path, ONE_RECORD, {"MSBNK-Test-TT000001.txt": record_text()},
        {"CMPD0000000001_NCE60": ([100.0], [1.0])})   # the NCE 30 cell is simply not in the dump
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    assert {r["drop_reason"] for r in rows} == {M.DROP_MISSING_PREDICTION}
    assert all(r["cosine"] is None and r["js"] is None for r in rows)


def test_an_empty_predicted_peak_list_yields_empty_prediction(tmp_path):
    root, records_dir = make_root(
        tmp_path, ONE_RECORD, {"MSBNK-Test-TT000001.txt": record_text()},
        {"CMPD0000000001_NCE30": ([], [])})
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    assert {r["drop_reason"] for r in rows} == {M.DROP_EMPTY_PREDICTION}
    assert all(r["cosine"] is None and r["js"] is None for r in rows)


def test_an_unparseable_dump_entry_yields_missing_prediction():
    with pytest.raises(M.PredictionError) as exc:
        M.prediction_spectrum({"masses_float32": [1.0, 2.0], "intens_float32": [1.0]})
    assert exc.value.reason == M.DROP_MISSING_PREDICTION
    with pytest.raises(M.PredictionError) as exc:
        M.prediction_spectrum({"masses_float32": [1.0], "intens_float32": ["x"]})
    assert exc.value.reason == M.DROP_MISSING_PREDICTION
    with pytest.raises(M.PredictionError) as exc:
        M.prediction_spectrum({})
    assert exc.value.reason == M.DROP_MISSING_PREDICTION


def test_the_dump_name_prefix_is_stripped_and_both_spellings_index_the_same_cell(tmp_path):
    path = tmp_path / "dump.json"
    path.write_text(json.dumps([dump_entry("A_NCE30", [100.0], [1.0], prefix=True),
                                dump_entry("B_NCE60", [100.0], [1.0], prefix=False)]))
    index = M.load_prediction_dump(path)
    assert sorted(index) == ["A_NCE30", "B_NCE60"]


def test_a_missing_dump_file_is_a_refusal_not_a_drop(tmp_path):
    with pytest.raises(SystemExit) as exc:
        M.load_prediction_dump(tmp_path / "absent_spectra.json")
    assert "does not exist" in str(exc.value)


def test_a_duplicated_spec_id_in_a_dump_is_a_refusal(tmp_path):
    path = tmp_path / "dump.json"
    path.write_text(json.dumps([dump_entry("A_NCE30", [100.0], [1.0]),
                                dump_entry("A_NCE30", [200.0], [1.0])]))
    with pytest.raises(SystemExit) as exc:
        M.load_prediction_dump(path)
    assert "more than once" in str(exc.value)


# ------------------------------------------------------------------------------------------------
# 5. the single square inverse, applied to the prediction side only and exactly once
# ------------------------------------------------------------------------------------------------

def test_a_prediction_equal_to_the_square_root_of_the_observed_spectrum_scores_cosine_exactly_one(tmp_path):
    """obs abs intensities 16, 4, 1 max-normalise to 1, 0.25, 0.0625, all exact binary64 powers of two.

    The prediction is their exact square root (1, 0.5, 0.25). The frozen layer squares the prediction
    side once, recovering 1, 0.25, 0.0625 bit for bit, so the two prepared spectra are identical and the
    cosine is exactly 1.0. If the square were applied twice, or to the observed side as well, or not at
    all, the two prepared vectors would differ and the value would not be 1.0; the two companion
    assertions below hold the other two cases down.
    """
    mz = [100.0, 200.0, 300.0]
    root, records_dir = make_root(
        tmp_path, ONE_RECORD, {"MSBNK-Test-TT000001.txt": record_text()},
        {"CMPD0000000001_NCE30": (mz, [1.0, 0.5, 0.25])})
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    assert len(rows) == 6
    for row in rows:
        assert row["drop_reason"] == ""
        assert row["cosine"] == 1.0
        assert row["js"] == 1.0

    obs = (mz, [16.0, 4.0, 1.0])
    # no inverse at all on the prediction side would mean pred == max-normalised obs scores 1.0
    assert M.score_pair((mz, [1.0, 0.25, 0.0625]), obs, DEFAULT_MH)[0] != 1.0
    # a second inverse would mean the fourth root scores 1.0
    assert M.score_pair((mz, [1.0, 0.25 ** 0.25, 0.0625 ** 0.25]), obs, DEFAULT_MH)[0] != 1.0


# ------------------------------------------------------------------------------------------------
# 6. a hand computed two peak example, recomputed here from first principles
# ------------------------------------------------------------------------------------------------

def test_two_peak_example_matches_an_independently_computed_value():
    """Recomputed in the test with plain arithmetic, never by calling the module's own helpers.

    Two peaks at m/z 100 and 200. With the frozen grid scale (15000 - 1) / 1500 they land in bins 1000
    and 2000, so no pooling happens and the prepared vectors are simply the max-normalised intensities.

      prediction stored (sqrt scale) [0.5, 1.0] -> squared [0.25, 1.0] -> max-normalised [0.25, 1.0]
      observed absolute              [100.0, 50.0]                    -> max-normalised [1.0, 0.5]

    cosine = (0.25 * 1.0 + 1.0 * 0.5) / (sqrt(0.25^2 + 1^2) * sqrt(1^2 + 0.5^2))
    js: L1 normalise each side, m = (p + q) / 2, JSD in nats, JSS = 1 - JSD / ln 2.

    Every intermediate is an exact binary64 value, so the comparison hides no rounding step.
    """
    mz = [100.0, 200.0]
    pred = (mz, [0.5, 1.0])
    obs = (mz, [100.0, 50.0])

    # the bins, computed here and not by the module
    scale = (15000 - 1) / 1500.0
    assert [math.floor(m * scale) + 1 for m in mz] == [1000, 2000]

    p = [0.5 ** 2, 1.0 ** 2]
    p = [v / max(p) for v in p]
    q = [100.0, 50.0]
    q = [v / max(q) for v in q]
    assert p == [0.25, 1.0] and q == [1.0, 0.5]

    dot = sum(a * b for a, b in zip(p, q))
    expected_cosine = dot / (math.sqrt(sum(a * a for a in p)) * math.sqrt(sum(b * b for b in q)))

    pp = [v / sum(p) for v in p]
    qq = [v / sum(q) for v in q]
    mm = [0.5 * (a + b) for a, b in zip(pp, qq)]
    kl_p = sum(a * math.log(a / c) for a, c in zip(pp, mm))
    kl_q = sum(b * math.log(b / c) for b, c in zip(qq, mm))
    expected_js = 1.0 - (0.5 * (kl_p + kl_q)) / math.log(2.0)

    cosine, js = M.score_pair(pred, obs, 500.0)
    assert cosine == pytest.approx(expected_cosine, abs=1e-15)
    assert js == pytest.approx(expected_js, abs=1e-15)
    # the same two numbers written out, so a silent change to either endpoint is visible here
    assert cosine == pytest.approx(0.6507913734559685, abs=1e-12)
    assert js == pytest.approx(0.8329741900987396, abs=1e-12)


def test_the_parent_mass_is_the_population_theoretical_mh_not_the_deposited_precursor(tmp_path):
    """A peak above theoretical_mh + 1 is cut by the frozen mass cutoff; the deposited PRECURSOR_M/Z in
    the record text is deliberately far away and must have no effect."""
    peaks = ((100.0, 16.0, 999), (400.0, 4.0, 250))
    records = [("MSBNK-Test-TT000001", "CMPD0000000001", "SG_A", 30, 150.0,
                "MSBNK-Test-TT000001.txt")]
    text = record_text(peaks=peaks, precursor="9999.0")
    spectra = {"CMPD0000000001_NCE30": ([100.0, 400.0], [1.0, 1.0])}
    root, records_dir = make_root(tmp_path, records, {"MSBNK-Test-TT000001.txt": text}, spectra)
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    # both sides lose the 400 Da peak, so the single surviving peak matches exactly
    assert all(r["cosine"] == 1.0 for r in rows)
    # with the deposited precursor as the parent mass nothing would be cut and the value would differ
    assert M.score_pair(([100.0, 400.0], [1.0, 1.0]), ([100.0, 400.0], [16.0, 4.0]), 9999.0)[0] != 1.0


# ------------------------------------------------------------------------------------------------
# 7. the output schema is exactly what 50_analysis.py consumes
# ------------------------------------------------------------------------------------------------

FULL_COMPOUNDS = ("CMPD0000000001", "CMPD0000000002", "CMPD0000000003")
SCAFFOLDS = {"CMPD0000000001": "SG_A", "CMPD0000000002": "SG_A", "CMPD0000000003": "SG_B"}


def full_grid(tmp_path, **kwargs):
    records, texts, spectra = [], {}, {}
    for i, cid in enumerate(FULL_COMPOUNDS):
        for nce in M.NCE_CELLS:
            rid = f"MSBNK-Test-TT{i:04d}{nce:02d}"
            source = f"{rid}.txt"
            records.append((rid, cid, SCAFFOLDS[cid], nce, DEFAULT_MH, source))
            texts[source] = record_text(accession=rid,
                                        peaks=((100.0, 16.0, 999), (200.0 + nce, 4.0, 250),
                                               (300.0, 1.0, 62)))
            spectra[M.spec_id(cid, nce)] = ([100.0, 200.0 + nce, 300.0],
                                            [1.0, 0.5 + 0.001 * i, 0.25])
    return make_root(tmp_path, records, texts, spectra, **kwargs)


def test_output_schema_is_accepted_and_mechanically_complete_for_the_analysis(tmp_path):
    root, records_dir = full_grid(tmp_path)
    res = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    scores = pd.read_csv(res["out_path"])

    assert list(scores.columns) == list(M.OUTPUT_COLUMNS)
    for col in A.REQUIRED_SCORE_COLUMNS:
        assert col in scores.columns
    assert A.OPTIONAL_DROP_REASON_COLUMN in scores.columns
    assert len(scores) == 6 * len(M.MODEL_KEYS) * len(M.MAPPINGS) == 36
    assert not scores["record_id"].duplicated().any()
    assert set(scores["model"]) == set(A.MODELS)
    assert set(scores["mapping"]) == set(A.MAPPINGS)
    assert set(int(v) for v in scores["nce"]) == set(A.NCE_CELLS)

    population = pd.DataFrame({"compound_id": list(FULL_COMPOUNDS),
                               "scaffold_group": [SCAFFOLDS[c] for c in FULL_COMPOUNDS]})
    prep = A.prepare_records(scores, population, metric=A.PRIMARY_METRIC)
    report = prep["report"]
    assert report["mechanically_complete"] is True
    assert report["n_records_submitted"] == 36
    assert report["n_records_dropped"] == 0
    assert report["n_cells_absent_from_score_table"] == 0
    assert report["n_compounds_dropped"] == 0
    assert report["n_compounds_analysed"] == len(FULL_COMPOUNDS)

    js_prep = A.prepare_records(scores, population, metric=A.ROBUSTNESS_METRIC)
    assert js_prep["report"]["mechanically_complete"] is True
    assert js_prep["report"]["n_records_dropped"] == 0


def test_a_dropped_row_is_reported_by_the_analysis_with_the_scoring_steps_own_reason(tmp_path):
    root, records_dir = full_grid(tmp_path)
    (records_dir / "MSBNK-Test-TT000030.txt").write_text(record_text(peak_block=False),
                                                         encoding="utf-8")
    res = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    scores = pd.read_csv(res["out_path"])
    population = pd.DataFrame({"compound_id": list(FULL_COMPOUNDS),
                               "scaffold_group": [SCAFFOLDS[c] for c in FULL_COMPOUNDS]})
    report = A.prepare_records(scores, population)["report"]
    assert report["n_records_dropped"] == 6
    assert {d["reason"] for d in report["dropped_records"]} == {M.DROP_MISSING_PK_PEAK_BLOCK}
    assert report["mechanically_complete"] is True          # the cells are present, just emptied
    assert report["n_compounds_dropped"] == 1


def test_the_row_key_is_unique_per_record_model_and_mapping():
    assert M.row_id("REC", "GLACIER", "K2") == "REC__GLACIER__K2"
    keys = {M.row_id("REC", label, mapping)
            for _k, label in M.MODEL_KEYS for mapping in M.MAPPINGS}
    assert len(keys) == 6


# ------------------------------------------------------------------------------------------------
# 8. determinism and the frozen configuration pin
# ------------------------------------------------------------------------------------------------

def test_the_score_table_is_byte_identical_across_runs(tmp_path):
    root, records_dir = full_grid(tmp_path)
    first = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    first_bytes = Path(first["out_path"]).read_bytes()
    first_sidecar = Path(first["sidecar_path"]).read_bytes()
    second = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    assert Path(second["out_path"]).read_bytes() == first_bytes
    assert Path(second["sidecar_path"]).read_bytes() == first_sidecar
    assert second["score_table_sha256"] == first["score_table_sha256"]
    assert second["score_table_sha256"] == hashlib.sha256(first_bytes).hexdigest()


def test_row_order_is_record_then_model_then_mapping(tmp_path):
    root, records_dir = full_grid(tmp_path)
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    labels = [label for _k, label in M.MODEL_KEYS]
    expected = [(label, mapping) for label in labels for mapping in M.MAPPINGS]
    assert [(r["model"], r["mapping"]) for r in rows[:6]] == expected
    ids = [r["record_id"].split(M.ROW_ID_SEP)[0] for r in rows]
    assert ids == sorted(ids)


def test_similarity_columns_are_written_at_full_precision(tmp_path):
    root, records_dir = full_grid(tmp_path)
    res = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    text = Path(res["out_path"]).read_text(encoding="utf-8")
    rows = M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)["rows"]
    for row in rows:
        if row["drop_reason"]:
            continue
        assert repr(row["cosine"]) in text
        assert float(repr(row["cosine"])) == row["cosine"]
        assert float(repr(row["js"])) == row["js"]


def test_frozen_similarity_config_sha256_regression():
    assert M.SIMILARITY_FROZEN_CONFIG_SHA256 == \
        "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"
    assert M.SS.frozen_config_sha256() == M.SIMILARITY_FROZEN_CONFIG_SHA256
    assert M.SS.FROZEN_CONFIG_SHA256 == M.SIMILARITY_FROZEN_CONFIG_SHA256


def test_the_sidecar_records_the_similarity_config_sha256(tmp_path):
    root, records_dir = full_grid(tmp_path)
    res = M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    sidecar = json.loads(Path(res["sidecar_path"]).read_text())
    assert sidecar["similarity_layer"]["frozen_config_sha256"] == M.SIMILARITY_FROZEN_CONFIG_SHA256
    assert sidecar["similarity_layer"]["frozen_config_sha256_pinned"] == \
        M.SIMILARITY_FROZEN_CONFIG_SHA256
    assert sidecar["drop_reason_constants"] == list(M.DROP_REASONS)
    assert sidecar["schema"]["columns"] == list(M.OUTPUT_COLUMNS)
    assert sidecar["outputs"]["score_table"]["sha256"] == res["score_table_sha256"]


def test_the_six_drop_reasons_are_fixed_and_exhaustive():
    assert M.DROP_REASONS == (
        "unreadable_record", "missing_pk_peak_block", "malformed_peak_line",
        "zero_peaks_after_parsing", "missing_prediction", "empty_prediction")
    assert len(set(M.DROP_REASONS)) == 6


# ------------------------------------------------------------------------------------------------
# 9. the governance refusals, each separately
# ------------------------------------------------------------------------------------------------

def test_refuses_without_the_execute_environment_variable(tmp_path):
    root, records_dir = full_grid(tmp_path)
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env={}, records_dir=records_dir)
    assert "precondition 1 of 4" in str(exc.value)
    assert M.EXECUTE_ENV_VAR in str(exc.value)
    assert not (root / M.SCORES_REL).exists()


def test_refuses_when_the_freeze_ref_does_not_resolve(tmp_path):
    root, records_dir = full_grid(tmp_path, freeze=False)
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    assert "precondition 2 of 4" in str(exc.value)
    assert M.FREEZE_REF in str(exc.value)
    assert not (root / M.SCORES_REL).exists()


def test_refuses_when_the_population_sha256_does_not_match(tmp_path):
    root, records_dir = full_grid(tmp_path, hashes="mismatch")
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    assert "precondition 3 of 4" in str(exc.value)
    assert "sha256 mismatch" in str(exc.value)
    assert not (root / M.SCORES_REL).exists()


def test_refuses_when_the_similarity_frozen_config_sha256_does_not_match(tmp_path, monkeypatch):
    root, records_dir = full_grid(tmp_path)
    monkeypatch.setattr(M, "SIMILARITY_FROZEN_CONFIG_SHA256", "0" * 64)
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env=EXEC_OK, records_dir=records_dir)
    assert "precondition 4 of 4" in str(exc.value)
    assert not (root / M.SCORES_REL).exists()


def test_refuses_when_the_record_directory_does_not_exist(tmp_path):
    root, records_dir = full_grid(tmp_path)
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env=EXEC_OK, records_dir=root / "no_such_directory")
    assert "does not exist" in str(exc.value)
    assert not (root / M.SCORES_REL).exists()


def test_refuses_on_a_duplicated_population_record_id(tmp_path):
    root, records_dir = make_root(
        tmp_path, ONE_RECORD + ONE_RECORD, {"MSBNK-Test-TT000001.txt": record_text()}, ONE_SPEC)
    with pytest.raises(SystemExit) as exc:
        M.run(root=root, env=EXEC_OK, records_dir=records_dir, write=False)
    assert "duplicate record_id" in str(exc.value)
