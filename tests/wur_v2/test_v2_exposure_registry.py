"""The committed study-2 exposure registry is internally consistent and never shrinks below its hard floors:
sample 1's 2,000 groups, every decoded file and well, every anchor, and every registered exposed population."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "artifacts/wur_v2_confirmation_v2/exposure_registry"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _lines_sha(items):
    return hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()


def _rows(name):
    with open(REG / name, newline="") as f:
        return list(csv.DictReader(f))


def test_output_file_hashes_match_manifest():
    m = json.loads((REG / "registry_manifest.json").read_text())
    for name, want in m["output_file_sha256"].items():
        assert _sha(REG / name) == want, name


def test_key_and_group_lists_match_their_hashes_and_csvs():
    m = json.loads((REG / "registry_manifest.json").read_text())
    keys = (REG / "excluded_compound_keys.txt").read_text().split("\n")[:-1]
    groups = (REG / "excluded_scaffold_groups.txt").read_text().split("\n")[:-1]
    assert keys == sorted(set(keys)) and groups == sorted(set(groups))
    assert _lines_sha(keys) == m["hashes_sorted_newline_joined"]["excluded_compound_keys_sha256"]
    assert _lines_sha(groups) == m["hashes_sorted_newline_joined"]["excluded_scaffold_groups_sha256"]
    assert {r["key"] for r in _rows("excluded_compounds.csv")} == set(keys)
    assert {r["scaffold_group"] for r in _rows("excluded_scaffold_groups.csv")} == set(groups)
    assert all(r["reasons"] for r in _rows("excluded_compounds.csv"))


def test_hard_floors():
    comp = {r["key"]: set(r["reasons"].split(";")) for r in _rows("excluded_compounds.csv")}
    groups = {r["scaffold_group"] for r in _rows("excluded_scaffold_groups.csv")}
    nb = list(csv.DictReader(open(ROOT / "artifacts/wur_v2_confirmation/novelty_bins_per_compound.csv", newline="")))
    assert {r["scaffold_group"] for r in nb} <= groups and len({r["scaffold_group"] for r in nb}) == 2000
    assert {r["key"] for r in nb} <= set(comp)
    census = json.loads((ROOT / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    assert set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"]) <= set(comp)
    em = json.loads((ROOT / "artifacts/wur_v2/exposure_manifest.json").read_text())
    for p in em["populations"].values():
        assert set(p["connectivity_keys"]) <= set(comp)
    aw = list(csv.DictReader(open(ROOT / "artifacts/wur_v2/external_msnlib/anchor_wells.csv", newline="")))
    exposed = _rows("exposed_files.csv")
    assert {r["fn"] for r in aw} == {r["file"] for r in exposed}
    assert all(len(r["file_sha256"]) == 64 for r in exposed)
    q = ROOT / "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/incident_record.json"
    assert set(json.loads(q.read_text())["affected_validation_compound_keys"]) <= set(comp)


def test_every_decoded_spectrum_of_the_incident_is_listed():
    dec = {(r["file"], r["spectrum_id"]) for r in _rows("decoded_spectra.csv") if r["event"] == "E_buggy_preflight"}
    aff = list(csv.DictReader(open(ROOT / "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/"
                                         "affected_spectra_full_list.csv", newline="")))
    assert len(dec) == 3366 and {(r["file"], r["spectrum_id"]) for r in aff} <= dec


# ------------------------------------------------------------------------------- pinned registry (review REG-4)
# A rebuild with a narrower rule regenerates consistent manifest hashes; these literals make any change to the
# registry contents a deliberate, reviewed test edit. They must equal the values the decode authority is bound to.
PINNED = {
    "registry_manifest_sha256": "ef64541d71be977f65e880c616a8cb895b6c9f3657ff8d8019797ca7d69a9675",
    "excluded_compound_keys_sha256": "bf103796a9415f8447cc3f27b0692ea57d8d9f2431427975842d19f84953b000",
    "excluded_scaffold_groups_sha256": "261bb8dd96803dbaf61c1a326bb90ed69c97dae1fe90f0d4d7f0e376db521b31",
    "excluded_design12b_keys_sha256": "be27fc50bd207d946d4618eb376921f3b21a99a011017706388791e9696bf505",
    "excluded_design12b_groups_sha256": "8a54ee5465124182db49152705a9e4b38cfe522616484ffcc6d56dd8c67262fd",
    "counts": {"excluded_compound_keys_all_sources": 31507, "excluded_scaffold_groups_all_sources": 18402,
               "excluded_design12b_keys": 23703, "excluded_design12b_groups": 15163,
               "remaining_design12b_groups_count_only": 14399, "decoded_msnlib_spectra_unique": 4927},
}
# compounds the pre-sampling reviews showed were decoded or printed but missed by the first registry build
MUST_BE_EXCLUDED = {
    "ZVXNYZWXUADSRV", "SXNJFOWDRLKDSF", "BJCJYEYYYGBROF", "FYDWDCIFZSGNBU", "VWAMTBXLZPEDQO", "VJKCWFZTSDXOBS",
    "CDTCEMOVQWPDDS",                                     # REG-1 multiply charged / in-source carryover owners
    "FATBGEAMYMYZAF", "WWUZIQQURGPMPG", "HXYVTAGFYLMHSO",   # REG-2 owners of printed spectra
    "GBFLZEXEOZUWRN", "WTGMGRFVBFDHGQ", "XBJWOGLKABXFJE", "ZZKNRXZVGOYGJT",   # F-03 new-anchor-decode carryover
    "OECUWHDVQIITIS", "MURAVORBGFDSMA",                   # same-well owner missed by the incident list; printed value
    "ITKWBJOJBMUWRV", "ZUCUYBFQLSBQCB",                   # REG-5 tautomer / MultiMS2-variant scaffold split
    "IZSBMDHDBLUZOI", "GAZRAIBCFIZVCH", "WYPOXKFQFNGLOX",   # round-2 precautions (orphan owner; enamine_5008 H11-H14)
}


def test_registry_contents_are_pinned():
    m = json.loads((REG / "registry_manifest.json").read_text())
    assert _sha(REG / "registry_manifest.json") == PINNED["registry_manifest_sha256"]
    for k in ("excluded_compound_keys_sha256", "excluded_scaffold_groups_sha256", "excluded_design12b_keys_sha256",
              "excluded_design12b_groups_sha256"):
        assert m["hashes_sorted_newline_joined"][k] == PINNED[k], k
    for k, v in PINNED["counts"].items():
        assert m["counts"][k] == v, k
    from muru.wur_v2.decode_authority import REGISTRY_MANIFEST_SHA256
    assert REGISTRY_MANIFEST_SHA256 == PINNED["registry_manifest_sha256"]


def test_review_identified_exposures_are_excluded():
    keys = set((REG / "excluded_compound_keys.txt").read_text().split())
    assert MUST_BE_EXCLUDED <= keys, sorted(MUST_BE_EXCLUDED - keys)


def test_every_reason_component_is_non_empty():
    m = json.loads((REG / "registry_manifest.json").read_text())
    for reason in ("SAMPLE1_DRAW_GROUP", "DECODED_SAME_WELL_ION_0p7", "DECODED_SAME_PLATE_ION_0p01",
                   "DECODED_SAME_PLATE_EXTENDED_ION_5PPM", "COPLATED_IN_DECODED_WELL", "SURFACED_VALUE_ATTRIBUTED_WELL",
                   "SURFACED_VALUE_ANY_LIBRARY_OWNER_5PPM", "ORPHAN_SPECTRUM_SAME_LIBRARY_OWNER_3PPM",
                   "HEADER_READ_WELL_STUDY1", "MSNLIB_ANCHOR_CENSUS_DESIGN", "MSNLIB_ANCHOR_GATE_CALIBRATION",
                   "MULTIMS2_ANCHOR_CALIBRATION", "SCAFFOLD_GROUP_EXCLUDED"):
        assert m["counts"]["per_reason_compounds"].get(reason, 0) > 0, reason
