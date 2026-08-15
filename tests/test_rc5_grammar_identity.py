"""The frozen five-primitive grammar: identity, order, and count.

A3.5 section 4.3 binds the search covariates to "exactly the five
``GRAMMAR_PRIMITIVES``, in frozen order".  Section 9's preconditions state that
Gate 2's conservatism argument holds only while the grammar is unchanged, so a
silent reordering or an added column would invalidate the null threshold table
without raising anything.  This file pins all three properties, and pins that
every consumer of the order is literally the same tuple object rather than a
copy that could drift.

**Sealed-boundary note.**  No benchmark case is generated here.  The covariate
frame is probed through ``generator._synthetic_compounds`` on *synthetic,
non-registry* identifier strings: that function is a pure function of the
string it is handed, produces the covariate frame alone, and computes no law,
no response, and no truth.  Materialising a real case would enlarge the
development engineering-fixture footprint A3.5 section 2 records, and would
break section 2's "no challenge-partition case has been generated" attestation
outright.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS
from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES
from muru.paper_benchmark.generator import N_COMPOUNDS, _synthetic_compounds
from muru.paper_benchmark.rc3_calibration_worlds import CALIBRATION_COVARIATE_ORDER
from muru.paper_benchmark.rc3_ceiling import CEILING_COVARIATE_ORDER

FROZEN_ORDER = (
    "mass",
    "descriptor",
    "descriptor2",
    "distractor",
    "correlated_distractor",
)

#: Deliberately not benchmark case IDs.  ``resolve_case_id`` rejects every one
#: of these, so none of them can name a real case.
SYNTHETIC_PROBES = (
    "RC5-SYNTHETIC-COLUMN-PROBE-A",
    "RC5-SYNTHETIC-COLUMN-PROBE-B",
)


def test_the_probes_are_not_benchmark_case_ids():
    from muru.paper_benchmark.registry import resolve_case_id

    for probe in SYNTHETIC_PROBES:
        with pytest.raises(ValueError):
            resolve_case_id(probe)


def test_identity_order_and_count_are_frozen():
    assert GRAMMAR_PRIMITIVES == FROZEN_ORDER
    assert len(GRAMMAR_PRIMITIVES) == 5
    assert len(set(GRAMMAR_PRIMITIVES)) == 5
    assert isinstance(GRAMMAR_PRIMITIVES, tuple)


def test_positional_identity_is_pinned_index_by_index():
    # An alias mapping x0..x4 keys off position, so a swap of two names would
    # silently re-label two columns rather than fail.
    for index, name in enumerate(FROZEN_ORDER):
        assert GRAMMAR_PRIMITIVES[index] == name


def test_every_consumer_shares_the_one_frozen_order_object():
    # `= GRAMMAR_PRIMITIVES`, not a copy: identity, not just equality.
    assert CALIBRATION_COVARIATE_ORDER is GRAMMAR_PRIMITIVES
    assert CEILING_COVARIATE_ORDER is GRAMMAR_PRIMITIVES


@pytest.mark.parametrize("probe", SYNTHETIC_PROBES)
def test_the_covariate_frame_carries_exactly_these_columns_in_this_order(probe):
    frame, _ = _synthetic_compounds(probe)
    assert list(frame.columns) == [
        "compound_id",
        "scaffold_id",
        "split",
        *FROZEN_ORDER,
    ]
    assert len(frame) == N_COMPOUNDS == 180


def test_no_sixth_primitive_and_no_dropped_primitive():
    frame, _ = _synthetic_compounds(SYNTHETIC_PROBES[0])
    numeric_columns = {
        c for c in frame.columns if c not in {"compound_id", "scaffold_id", "split"}
    }
    assert numeric_columns == set(FROZEN_ORDER)


def test_column_identity_does_not_depend_on_the_identifier():
    # The frame's *values* are a deterministic function of the identifier; its
    # *schema* is not a function of it at all. A partition label appearing in a
    # real case ID therefore cannot change the column set or its order.
    first, _ = _synthetic_compounds(SYNTHETIC_PROBES[0])
    second, _ = _synthetic_compounds(SYNTHETIC_PROBES[1])
    assert list(first.columns) == list(second.columns)
    assert not first[list(FROZEN_ORDER)].equals(second[list(FROZEN_ORDER)])


def test_the_grammar_operator_set_is_frozen_and_excludes_exp():
    # A3.5 section 10.2 discloses that F18 needs `exp` and that the frozen
    # grammar cannot produce it -- and section 10.2's bound response is "none".
    assert list(SEARCH_SETTINGS["binary_operators"]) == ["+", "-", "*", "/"]
    assert list(SEARCH_SETTINGS["unary_operators"]) == [
        "sqrt",
        "log",
        "square",
        "cube",
        "inv",
    ]
    assert list(SEARCH_SETTINGS["excluded_unary"]) == ["exp", "sin", "cos", "tan"]
    assert "exp" not in SEARCH_SETTINGS["unary_operators"]
    assert not set(SEARCH_SETTINGS["excluded_unary"]) & set(
        SEARCH_SETTINGS["unary_operators"]
    )
