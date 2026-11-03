"""Frozen A3.4 reference-covariate distribution contract.

The reference rows are prospective covariates only.  They are regenerated
directly from the frozen generator primitive and verified against the A3.4
frame and aggregate SHA-256 digests before use.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Mapping, Sequence

from .generator import _synthetic_compounds


PREDICTIVE_EQUIVALENCE_DENOMINATOR = 144
REFERENCE_FRAME_COUNT = 12
REFERENCE_ROWS_PER_FRAME = 180
REFERENCE_SCAFFOLDS_PER_FRAME = 30
REFERENCE_COMPOUNDS_PER_SCAFFOLD = 6
REFERENCE_ROW_COUNT = REFERENCE_FRAME_COUNT * REFERENCE_ROWS_PER_FRAME

VALID_FRACTION_THRESHOLD = 0.995
MIN_VALID_REFERENCE_ROWS = 2150
REL_RMSE_THRESHOLD = 0.05
CORRELATION_THRESHOLD = 0.990

REFERENCE_FRAME_IDS = tuple(
    f"PB|PRED_EQUIV|FRAME|{index:03d}"
    for index in range(REFERENCE_FRAME_COUNT)
)
EXPECTED_FRAME_SEEDS = {
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
EXPECTED_FRAME_DIGESTS = {
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
EXPECTED_REFERENCE_DIGEST = "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"

_COVARIATE_COLUMNS = (
    "compound_id",
    "scaffold_id",
    "split",
    "mass",
    "descriptor",
    "descriptor2",
    "distractor",
    "correlated_distractor",
)


class ReferenceDistributionError(RuntimeError):
    """The regenerated A3.4 reference distribution violates its contract."""


class ReferenceDigestMismatchError(ReferenceDistributionError):
    """A regenerated reference frame or aggregate has the wrong digest."""


def canonical_reference_json(rows: Sequence[Mapping[str, object]]) -> bytes:
    """Serialize reference rows in the frozen A3.4 canonical form."""
    ordered = sorted(
        rows,
        key=lambda row: (str(row["frame_id"]), str(row["compound_id"])),
    )
    return json.dumps(
        ordered,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def reference_digest(rows: Sequence[Mapping[str, object]] | None = None) -> str:
    """Return the canonical SHA-256 digest for supplied or regenerated rows."""
    if rows is None:
        rows, _ = build_reference_rows()
    return hashlib.sha256(canonical_reference_json(rows)).hexdigest()


def _validate_frame_geometry(
    frame_id: str,
    rows: Sequence[Mapping[str, object]],
) -> None:
    if len(rows) != REFERENCE_ROWS_PER_FRAME:
        raise ReferenceDistributionError(
            f"{frame_id}: expected {REFERENCE_ROWS_PER_FRAME} rows, got {len(rows)}"
        )

    compound_ids = tuple(sorted(str(row["compound_id"]) for row in rows))
    expected_compound_ids = tuple(
        f"C{index:03d}" for index in range(REFERENCE_ROWS_PER_FRAME)
    )
    if compound_ids != expected_compound_ids:
        raise ReferenceDistributionError(
            f"{frame_id}: compound IDs do not match the frozen frame shape"
        )

    scaffold_counts = Counter(str(row["scaffold_id"]) for row in rows)
    if (
        len(scaffold_counts) != REFERENCE_SCAFFOLDS_PER_FRAME
        or set(scaffold_counts.values()) != {REFERENCE_COMPOUNDS_PER_SCAFFOLD}
    ):
        raise ReferenceDistributionError(
            f"{frame_id}: scaffold geometry does not match the frozen frame shape"
        )


def _rows_for_frame(frame_id: str) -> tuple[Mapping[str, object], ...]:
    compounds, seeds = _synthetic_compounds(frame_id)
    actual_seed = seeds.get("compounds")
    expected_seed = EXPECTED_FRAME_SEEDS[frame_id]
    if actual_seed != expected_seed:
        raise ReferenceDistributionError(
            f"{frame_id}: compound seed mismatch; expected {expected_seed}, got {actual_seed}"
        )

    if tuple(compounds.columns) != _COVARIATE_COLUMNS:
        raise ReferenceDistributionError(
            f"{frame_id}: covariate columns do not match the frozen contract"
        )

    rows = tuple(
        {"frame_id": frame_id, **record}
        for record in compounds.to_dict(orient="records")
    )
    _validate_frame_geometry(frame_id, rows)
    return rows


def build_reference_rows() -> tuple[tuple[Mapping[str, object], ...], dict[str, str]]:
    """Regenerate and validate all twelve frozen A3.4 reference frames."""
    rows: list[Mapping[str, object]] = []
    frame_digests: dict[str, str] = {}

    for frame_id in REFERENCE_FRAME_IDS:
        frame_rows = _rows_for_frame(frame_id)
        actual_digest = reference_digest(frame_rows)
        expected_digest = EXPECTED_FRAME_DIGESTS[frame_id]
        if actual_digest != expected_digest:
            raise ReferenceDigestMismatchError(
                f"{frame_id}: frame digest mismatch; "
                f"expected {expected_digest}, got {actual_digest}"
            )
        rows.extend(frame_rows)
        frame_digests[frame_id] = actual_digest

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (str(row["frame_id"]), str(row["compound_id"])),
        )
    )
    if len(ordered_rows) != REFERENCE_ROW_COUNT:
        raise ReferenceDistributionError(
            f"expected {REFERENCE_ROW_COUNT} reference rows, got {len(ordered_rows)}"
        )

    actual_reference_digest = reference_digest(ordered_rows)
    if actual_reference_digest != EXPECTED_REFERENCE_DIGEST:
        raise ReferenceDigestMismatchError(
            "aggregate reference digest mismatch; "
            f"expected {EXPECTED_REFERENCE_DIGEST}, got {actual_reference_digest}"
        )
    return ordered_rows, frame_digests


def verify_reference_distribution() -> None:
    """Raise on any A3.4 reference-frame or aggregate integrity failure."""
    build_reference_rows()
