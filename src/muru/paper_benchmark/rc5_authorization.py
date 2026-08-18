"""Engineering RC5.1: what Amendment A3.6 authorises RC5.1 to open, in one place.

Amendment A3.6: "authorises execution of the already-frozen Held-out partition
under the exact existing RC5/A3.5 machinery ... RC5.1 is not authorized to
construct or execute Challenge, or open Confirmation."

Declared here, and imported by every module that could open a partition, so the
refusal is one object rather than one convention per call site.  A guard that
lives only in the runner makes every other entry point -- the preflight reader,
the Layer-2 manifest builder -- a matter of caller discipline.
"""
from __future__ import annotations

from .registry import PARTITIONS

__all__ = [
    "AUTHORISED_PARTITIONS",
    "PartitionNotAuthorised",
    "assert_partition_authorised",
]

#: The partitions RC5.1 may open.
AUTHORISED_PARTITIONS: frozenset[str] = frozenset({"development", "held_out"})


class PartitionNotAuthorised(RuntimeError):
    """Amendment A3.6 does not authorise opening this partition."""


def assert_partition_authorised(partition: str) -> None:
    """Refuse any partition Amendment A3.6 does not authorise.

    Raises :class:`ValueError` for a name the frozen registry does not know and
    :class:`PartitionNotAuthorised` for one it knows but RC5.1 may not open, so a
    typo and a boundary violation are never confused.
    """
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    if partition not in AUTHORISED_PARTITIONS:
        raise PartitionNotAuthorised(
            f"Amendment A3.6 authorises the Development and Held-out partitions only; RC5.1 is "
            f"not authorised to construct or execute Challenge, or "
            f"open Confirmation. Refusing {partition!r}."
        )

