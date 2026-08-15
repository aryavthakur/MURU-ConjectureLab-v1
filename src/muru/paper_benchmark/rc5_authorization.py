"""Engineering RC5: what A3.5 authorises RC5 to open, in one place.

A3.5 section 14.2: "RC5 may implement sections 4-8 against engineering parent
``69e33c7`` ... and may execute the **Development** partition only.  RC5 is
**not** authorized to open Held-out, construct or execute Challenge, open
Confirmation, rerun calibration, or alter any binding in section 12."

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

#: The only partition RC5 may open.
AUTHORISED_PARTITIONS: frozenset[str] = frozenset({"development"})


class PartitionNotAuthorised(RuntimeError):
    """A3.5 section 14.2 does not authorise opening this partition."""


def assert_partition_authorised(partition: str) -> None:
    """Refuse any partition A3.5 section 14.2 does not authorise.

    Raises :class:`ValueError` for a name the frozen registry does not know and
    :class:`PartitionNotAuthorised` for one it knows but RC5 may not open, so a
    typo and a boundary violation are never confused.
    """
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    if partition not in AUTHORISED_PARTITIONS:
        raise PartitionNotAuthorised(
            f"A3.5 section 14.2 authorises the Development partition only; RC5 is "
            f"not authorised to open Held-out, construct or execute Challenge, or "
            f"open Confirmation. Refusing {partition!r}."
        )
