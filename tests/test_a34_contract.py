"""Frozen A3.4 reference-covariate contract checks."""

from __future__ import annotations

import json
from collections import Counter

import pytest

from muru.paper_benchmark import a34_contract
from muru.paper_benchmark.generator import derive_seed


FROZEN_FRAME_SEEDS = {
    "PB|PRED_EQUIV|FRAME|000": 10159460000043340500,
    "PB|PRED_EQUIV|FRAME|001": 6369442522185596642,
    "PB|PRED_EQUIV|FRAME|002": 10285077022068351075,
    "PB|PRED_EQUIV|FRAME|003": 12287309645523585205,
    "PB|PRED_EQUIV|FRAME|004": 10093203124591748778,
    "PB|PRED_EQUIV|FRAME|005": 11744644982560049663,
    "PB|PRED_EQUIV|FRAME|006": 16102535362459587545,
    "PB|PRED_EQUIV|FRAME|007": 11399441919836473429,
    "PB|PRED_EQUIV|FRAME|008": 6117612182649873844,
    "PB|PRED_EQUIV|FRAME|009": 1323825430146244524,
    "PB|PRED_EQUIV|FRAME|010": 16921266869593996090,
    "PB|PRED_EQUIV|FRAME|011": 10286422724919074315,
}

FROZEN_FRAME_DIGESTS = {
    "PB|PRED_EQUIV|FRAME|000": "4bd545ba3fa8e2538096d9cc9245ba79021d9089cd739c8a4d048e41e8332e7e",
    "PB|PRED_EQUIV|FRAME|001": "a45c217b297166f0689ce61b1602db33c41719813895de6441b314e326656ec7",
    "PB|PRED_EQUIV|FRAME|002": "8f18bc0a6d4e7a299b8aada901877cc15bab7d5b953b5b2bbe66fa3ca055f747",
    "PB|PRED_EQUIV|FRAME|003": "4b48e62e8d347e48a5d04791c50092a2dca861bd3395f921c7ed25e57ab7d92e",
    "PB|PRED_EQUIV|FRAME|004": "de717d3baec939534ee20072cb9335e78c8c9fba32674b0b07bb389ea1e74bb3",
    "PB|PRED_EQUIV|FRAME|005": "0919b84e1200316e3a2d396a20791f43f19a452bf14e4e858d8acf21d7655e7e",
    "PB|PRED_EQUIV|FRAME|006": "ae5cd95f57b935e5faeeae0d8273c48ef028c8353282a6a64575420d68d6dda6",
    "PB|PRED_EQUIV|FRAME|007": "282fd2d1279c4040f35c1ba779291df1879df7fd39a71813c15ee6e8b9920030",
    "PB|PRED_EQUIV|FRAME|008": "c1f4cdf75dbb108e7407d6f5e6e9b80addc55050a90f206d2e25066b6035654b",
    "PB|PRED_EQUIV|FRAME|009": "ea93b8a18af342f3f1995ef1cafa47992e2d3e1245fb98fe5c776c4d70e63689",
    "PB|PRED_EQUIV|FRAME|010": "7b93c136145a8e0bc2d83116d8c65881aa8a83bc087c3745ad0bbd2dd05bbdb7",
    "PB|PRED_EQUIV|FRAME|011": "9224ac40d4a73d1a1437d0a0aed3b32c398039e16d54ca808e11da09b3bced26",
}

FROZEN_REFERENCE_DIGEST = "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"
FRAME_IDS = tuple(FROZEN_FRAME_DIGESTS)
REFERENCE_COLUMNS = {
    "compound_id",
    "correlated_distractor",
    "descriptor",
    "descriptor2",
    "distractor",
    "frame_id",
    "mass",
    "scaffold_id",
    "split",
}


def test_all_twelve_frame_hashes_and_aggregate_digest_match_a34():
    """Changing a frozen covariate value or hash must break the contract."""
    rows, frame_digests = a34_contract.build_reference_rows()

    assert len(rows) == 2160
    assert a34_contract.EXPECTED_FRAME_DIGESTS == FROZEN_FRAME_DIGESTS
    assert frame_digests == FROZEN_FRAME_DIGESTS
    assert a34_contract.EXPECTED_REFERENCE_DIGEST == FROZEN_REFERENCE_DIGEST
    assert a34_contract.reference_digest(rows) == FROZEN_REFERENCE_DIGEST
    assert a34_contract.reference_digest() == FROZEN_REFERENCE_DIGEST


def test_reference_frame_manifest_uses_the_exact_ids_and_compound_seeds():
    """A changed frame namespace or generator seed changes the frozen frames."""
    assert a34_contract.REFERENCE_FRAME_IDS == FRAME_IDS
    assert a34_contract.EXPECTED_FRAME_SEEDS == FROZEN_FRAME_SEEDS
    assert {
        frame_id: derive_seed(frame_id, "compounds")
        for frame_id in FRAME_IDS
    } == FROZEN_FRAME_SEEDS


def test_a34_denominator_and_evaluation_thresholds_are_frozen():
    """Changing a threshold silently changes the secondary endpoint contract."""
    assert a34_contract.PREDICTIVE_EQUIVALENCE_DENOMINATOR == 144
    assert a34_contract.REFERENCE_FRAME_COUNT == 12
    assert a34_contract.REFERENCE_ROWS_PER_FRAME == 180
    assert a34_contract.REFERENCE_SCAFFOLDS_PER_FRAME == 30
    assert a34_contract.REFERENCE_COMPOUNDS_PER_SCAFFOLD == 6
    assert a34_contract.REFERENCE_ROW_COUNT == 2160
    assert a34_contract.VALID_FRACTION_THRESHOLD == 0.995
    assert a34_contract.MIN_VALID_REFERENCE_ROWS == 2150
    assert a34_contract.REL_RMSE_THRESHOLD == 0.05
    assert a34_contract.CORRELATION_THRESHOLD == 0.990


def test_builds_only_the_twelve_frozen_frame_ids_through_the_covariate_primitive(
    monkeypatch: pytest.MonkeyPatch,
):
    """An extra or substituted frame changes the reference distribution."""
    observed_frame_ids: list[str] = []
    original = a34_contract._synthetic_compounds

    def record_frame(frame_id: str):
        observed_frame_ids.append(frame_id)
        return original(frame_id)

    monkeypatch.setattr(a34_contract, "_synthetic_compounds", record_frame)

    a34_contract.build_reference_rows()

    assert observed_frame_ids == list(FRAME_IDS)


def test_reference_rows_preserve_the_frozen_frame_geometry_and_order():
    """A row loss, reordered compound, or scaffold mutation changes coverage."""
    rows, _ = a34_contract.build_reference_rows()

    assert [(row["frame_id"], row["compound_id"]) for row in rows] == [
        (frame_id, f"C{compound_index:03d}")
        for frame_id in FRAME_IDS
        for compound_index in range(180)
    ]
    assert {frozenset(row) for row in rows} == {frozenset(REFERENCE_COLUMNS)}

    for frame_id in FRAME_IDS:
        frame_rows = [row for row in rows if row["frame_id"] == frame_id]
        scaffold_counts = Counter(str(row["scaffold_id"]) for row in frame_rows)
        split_counts = Counter(str(row["split"]) for row in frame_rows)

        assert len(frame_rows) == 180
        assert len(scaffold_counts) == 30
        assert set(scaffold_counts.values()) == {6}
        assert split_counts == {"train": 120, "validation": 30, "test": 30}


def test_canonical_reference_json_sorts_frames_and_compounds_with_compact_utf8():
    """Input ordering must not alter the canonical reference payload."""
    rows, _ = a34_contract.build_reference_rows()
    canonical = a34_contract.canonical_reference_json(rows)

    assert canonical == a34_contract.canonical_reference_json(tuple(reversed(rows)))
    assert canonical == json.dumps(
        sorted(rows, key=lambda row: (str(row["frame_id"]), str(row["compound_id"]))),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert b", " not in canonical
    assert b": " not in canonical


def test_f09_reference_domain_never_hits_the_descriptor_minus_one_pole():
    """The saturating F09 law is undefined at descriptor == -1."""
    rows, _ = a34_contract.build_reference_rows()
    descriptors = [float(row["descriptor"]) for row in rows]

    assert all(descriptor > -1.0 for descriptor in descriptors)
    assert all(descriptor != -1.0 for descriptor in descriptors)


def test_verify_reference_distribution_raises_a_dedicated_error_for_digest_mismatch(
    monkeypatch: pytest.MonkeyPatch,
):
    """A digest mismatch must halt rather than silently continue."""
    monkeypatch.setattr(a34_contract, "EXPECTED_REFERENCE_DIGEST", "0" * 64)

    with pytest.raises(
        a34_contract.ReferenceDigestMismatchError,
        match="aggregate reference digest mismatch",
    ):
        a34_contract.verify_reference_distribution()
