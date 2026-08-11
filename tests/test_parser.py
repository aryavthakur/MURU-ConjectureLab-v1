"""BLOCKER-class tests for the MassBank parser.

The failure modes that matter: losing peaks, corrupting numeric values,
silently coercing missing metadata, and mis-assigning identity. Formatting and
logging are not tested.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from muru.identity import check_identity, first_block, group_key
from muru.io.massbank import parse_file, parse_record

ROOT = Path(__file__).resolve().parents[1]
LCSB = ROOT / "data" / "massbank" / "MassBank-data" / "LCSB"

MINIMAL = """ACCESSION: MSBNK-LCSB-LU003301
RECORD_TITLE: Isoproturon; LC-ESI-QFT; MS2; CE: 15; R=17500; [M+H]+
COMMENT: CONFIDENCE standard compound
COMMENT: INTERNAL_ID 33
COMMENT: DATASET 20200303_ENTACT_RP_MIX506
CH$NAME: Isoproturon
CH$NAME: 1,1-dimethyl-3-(4-propan-2-ylphenyl)urea
CH$FORMULA: C12H18N2O
CH$SMILES: CC(C)C1=CC=C(NC(=O)N(C)C)C=C1
CH$LINK: INCHIKEY PUIYMUZLKQOUOZ-UHFFFAOYSA-N
AC$MASS_SPECTROMETRY: ION_MODE POSITIVE
AC$MASS_SPECTROMETRY: COLLISION_ENERGY 15
MS$FOCUSED_ION: PRECURSOR_M/Z 207.1492
MS$FOCUSED_ION: PRECURSOR_TYPE [M+H]+
PK$NUM_PEAK: 2
PK$PEAK: m/z int. rel.int.
  72.0443 5981849.5 445
  207.1491 13413768 999
//
"""


# ---------------------------------------------------------------------------
# Round-trip fidelity
# ---------------------------------------------------------------------------
def test_peak_values_parsed_exactly():
    r = parse_record(MINIMAL)
    assert r.parse_status == "OK"
    assert len(r.peaks) == 2
    assert r.peaks[0].mz == 72.0443
    assert r.peaks[0].intensity == 5981849.5
    assert r.peaks[1].mz == 207.1491
    assert r.peaks[1].intensity == 13413768.0


def test_repeated_tags_are_all_retained():
    """CH$NAME appears twice; neither may be dropped."""
    r = parse_record(MINIMAL)
    assert len(r.get_all("CH$NAME")) == 2
    assert len(r.get_all("COMMENT")) == 3


def test_raw_text_survives_parsing():
    r = parse_record(MINIMAL)
    assert r.raw_text == MINIMAL


def test_subtag_values_extracted():
    r = parse_record(MINIMAL)
    assert r.sub("AC$MASS_SPECTROMETRY", "COLLISION_ENERGY") == "15"
    assert r.sub("MS$FOCUSED_ION", "PRECURSOR_TYPE") == "[M+H]+"
    assert r.sub("COMMENT", "DATASET") == "20200303_ENTACT_RP_MIX506"


def test_accession_decomposes_to_internal_id_and_slot():
    r = parse_record(MINIMAL)
    assert r.internal_id == 33
    assert r.slot == "01"


def test_accession_internal_id_agrees_with_comment():
    """Two independent encodings of the same fact must agree."""
    r = parse_record(MINIMAL)
    assert str(r.internal_id) == r.sub("COMMENT", "INTERNAL_ID")


def test_missing_field_returns_none_not_empty_string():
    r = parse_record(MINIMAL)
    assert r.get("PUBLICATION") is None
    assert r.sub("AC$CHROMATOGRAPHY", "RETENTION_TIME") is None


# ---------------------------------------------------------------------------
# Malformed input must be rejected, never silently accepted (IMPORTANT-class)
# ---------------------------------------------------------------------------
def test_peak_count_mismatch_is_a_parse_failure():
    """Declared 5 peaks, supplied 2. Losing peaks silently is the worst
    possible parser bug, so this must fail loudly."""
    bad = MINIMAL.replace("PK$NUM_PEAK: 2", "PK$NUM_PEAK: 5")
    r = parse_record(bad)
    assert r.parse_status == "FAILED"
    assert any("PK$NUM_PEAK" in w for w in r.warnings)


def test_non_numeric_peak_is_warned_and_not_invented():
    bad = MINIMAL.replace("72.0443 5981849.5 445", "72.0443 NOT_A_NUMBER 445")
    r = parse_record(bad)
    assert len(r.peaks) == 1
    assert any("non-numeric" in w for w in r.warnings)
    assert r.parse_status == "FAILED"  # count mismatch follows


def test_missing_accession_fails():
    r = parse_record(MINIMAL.replace("ACCESSION: MSBNK-LCSB-LU003301\n", ""))
    assert r.parse_status == "FAILED"


def test_truncated_peak_line_does_not_crash():
    bad = MINIMAL.replace("  72.0443 5981849.5 445", "  72.0443 5981849.5")
    r = parse_record(bad)
    assert r.parse_status == "FAILED"
    assert len(r.peaks) == 1


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
def test_identity_match_for_known_compound():
    ic = check_identity("X", "CC(C)C1=CC=C(NC(=O)N(C)C)C=C1",
                        "PUIYMUZLKQOUOZ-UHFFFAOYSA-N")
    assert ic.status == "MATCH"
    assert ic.usable


def test_identity_mismatch_is_reported_not_repaired():
    """Ethanol SMILES against isoproturon's key must be flagged, not fixed."""
    ic = check_identity("X", "CCO", "PUIYMUZLKQOUOZ-UHFFFAOYSA-N")
    assert ic.status == "MISMATCH"
    assert not ic.usable
    assert ic.inchikey_recorded == "PUIYMUZLKQOUOZ-UHFFFAOYSA-N"
    assert ic.inchikey_from_smiles is not None  # both kept


def test_unparseable_smiles_flagged():
    ic = check_identity("X", "this is not smiles", "AAAAAAAAAAAAAA-UHFFFAOYSA-N")
    assert ic.status == "SMILES_UNPARSEABLE"


def test_first_block_is_connectivity_layer():
    assert first_block("PUIYMUZLKQOUOZ-UHFFFAOYSA-N") == "PUIYMUZLKQOUOZ"
    assert first_block("garbage") is None
    assert first_block(None) is None


def test_group_key_separates_ion_modes():
    """Pooling polarities is forbidden; the key must keep them apart."""
    pos = group_key("PUIYMUZLKQOUOZ-UHFFFAOYSA-N", "POSITIVE")
    neg = group_key("PUIYMUZLKQOUOZ-UHFFFAOYSA-N", "NEGATIVE")
    assert pos != neg


def test_group_key_ignores_stereo_layer():
    """MS/MS cannot resolve stereochemistry, so stereoisomers must group."""
    a = group_key("PUIYMUZLKQOUOZ-UHFFFAOYSA-N", "POSITIVE")
    b = group_key("PUIYMUZLKQOUOZ-QWERTYUISA-N", "POSITIVE")
    assert a == b


# ---------------------------------------------------------------------------
# Corpus-level assertions (skipped when the corpus is not present)
# ---------------------------------------------------------------------------
requires_corpus = pytest.mark.skipif(
    not LCSB.exists(), reason="MassBank corpus not acquired"
)


@requires_corpus
def test_corpus_round_trip_on_50_records():
    """Master plan T1.4: round-trip on 50 records. Deterministic selection."""
    files = sorted(LCSB.glob("MSBNK-LCSB-LU*.txt"))[:50]
    assert len(files) == 50
    for f in files:
        r = parse_file(f)
        assert r.parse_status == "OK", f"{f.name}: {r.warnings}"
        assert r.num_peak_declared == len(r.peaks)
        assert r.accession == f.stem
        # every peak line in the raw text is represented in the parsed list
        assert r.raw_text.count("\n  ") >= len(r.peaks)


@requires_corpus
def test_grouping_invariant_to_file_order():
    """Master plan T1.4: grouping must not depend on record ordering."""
    files = sorted(LCSB.glob("MSBNK-LCSB-LU*.txt"))[:200]
    fwd = [group_key(parse_file(f).inchikey,
                     parse_file(f).sub("AC$MASS_SPECTROMETRY", "ION_MODE"))
           for f in files]
    rev = [group_key(parse_file(f).inchikey,
                     parse_file(f).sub("AC$MASS_SPECTROMETRY", "ION_MODE"))
           for f in reversed(files)]
    assert set(fwd) == set(rev)
    assert sorted(fwd, key=str) == sorted(rev, key=str)
