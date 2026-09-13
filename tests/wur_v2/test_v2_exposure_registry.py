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
