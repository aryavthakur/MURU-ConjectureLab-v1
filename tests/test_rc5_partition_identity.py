"""The architecturally-required Development vs Held-out identity property test.

Identical **synthetic** content is driven through the whole non-executing
pipeline twice, changing only the partition label, and the scientific payload
must be byte-identical except for explicitly administrative identity fields.

**No sealed content is touched.**  The fixtures are hand-built
(``tests/rc5_synthetic.py``); ``generate_case`` is never called, so no
Development case is materialised beyond the pre-existing frozen footprint and
no Held-out or Challenge case is generated at all.  The case IDs are registry
metadata only, which A3.5 section 8.4 explicitly distinguishes from opening a
partition.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.rc5_estimate import fit_case_scalars
from muru.paper_benchmark.rc5_falsify import (
    FalsificationInputs,
    candidate_test_r2,
    run_falsification,
)
from muru.paper_benchmark.rc5_runner import execute_case
from muru.paper_benchmark.rc5_seeds import case_ordinal, case_search_seeds

from rc5_synthetic import (
    ENGINE_VERSIONS,
    NULL_THRESHOLD,
    StubBackend,
    synthetic_content,
)

DEV = "PB|development|F01|r000"
HELD = "PB|held_out|F01|r000"

#: The only fields allowed to differ.  Everything else is scientific and must
#: be byte-identical for identical content.
ADMINISTRATIVE_FIELDS = {
    "case_id",
    "partition_label",
    "seeds_used",
    "per_seed_status",
}

_SRC = Path(__file__).resolve().parents[1] / "src" / "muru" / "paper_benchmark"


def _payload(case_id: str) -> dict:
    outcome = execute_case(
        content=synthetic_content(case_id),
        a1_status=CaseAdequacyStatus.M0_NOT_REJECTED,
        backend=StubBackend(),
        null_threshold=NULL_THRESHOLD,
        engine_versions=ENGINE_VERSIONS,
    )
    return outcome.record.scientific_payload()


def test_the_two_fixtures_carry_byte_identical_content():
    """The premise: only the label differs, not the data."""
    development = synthetic_content(DEV)
    held_out = synthetic_content(HELD)
    assert development.compounds.equals(held_out.compounds)
    assert development.trajectories.equals(held_out.trajectories)
    assert development.content_hash == held_out.content_hash


def test_the_scientific_payload_is_identical_except_administrative_fields():
    development = _payload(DEV)
    held_out = _payload(HELD)

    assert set(development) == set(held_out)
    differing = {k for k in development if development[k] != held_out[k]}
    assert differing <= ADMINISTRATIVE_FIELDS, (
        f"partition identity changed scientific fields {sorted(differing - ADMINISTRATIVE_FIELDS)}"
    )


def test_every_scientific_field_is_byte_identical():
    development = _payload(DEV)
    held_out = _payload(HELD)
    scientific_dev = {k: v for k, v in development.items() if k not in ADMINISTRATIVE_FIELDS}
    scientific_held = {k: v for k, v in held_out.items() if k not in ADMINISTRATIVE_FIELDS}
    assert json.dumps(scientific_dev, sort_keys=True) == json.dumps(
        scientific_held, sort_keys=True
    )


def test_the_gate_verdict_and_every_gate_input_match():
    development = _payload(DEV)
    held_out = _payload(HELD)
    for field in (
        "acceptance_status",
        "acceptance_gate_reached",
        "valid_r2",
        "complexity",
        "selection_count",
        "selection_denominator",
        "selection_fraction",
        "invalid_fraction",
        "ceiling_r2",
        "ceiling_fraction",
        "candidate_test_r2",
        "falsification_results",
        "f9_stress_test_result",
        "f9_stress_test_metric",
        "discovered_expression_string",
        "effective_support",
        "support_status",
        "family_status",
        "discovered_family",
        "g2_event",
        "null_threshold_digest",
    ):
        assert development[field] == held_out[field], field


def test_the_only_seed_difference_is_the_frozen_ordinal_offset():
    """Seeds differ because the case ordinal differs, not because of a branch.

    A3.5 section 8.1: one shared band across partitions is correct, since
    partition identity is already the second field of the case ID that
    determines ``case_ordinal``, and no consumer infers a partition from a bare
    seed value.
    """
    development = _payload(DEV)
    held_out = _payload(HELD)
    offset = (case_ordinal(HELD) - case_ordinal(DEV)) * 30
    assert offset != 0
    assert [s + offset for s in development["seeds_used"]] == held_out["seeds_used"]
    assert development["seeds_used"] == list(case_search_seeds(DEV))
    assert held_out["seeds_used"] == list(case_search_seeds(HELD))


def test_the_per_seed_statuses_differ_only_in_their_seed_values():
    development = _payload(DEV)
    held_out = _payload(HELD)
    for a, b in zip(development["per_seed_status"], held_out["per_seed_status"]):
        assert a["status"] == b["status"]
        assert a["selected_expression_string"] == b["selected_expression_string"]
        assert a["error_type"] == b["error_type"]
        assert a["seed"] != b["seed"]


# -----------------------------------------------------------------------
# No falsification rung reads partition_label
# -----------------------------------------------------------------------

def test_no_falsification_rung_reads_partition_label_statically():
    import muru.paper_benchmark.rc5_falsify as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "partition_label" not in names
    assert "partition" not in names
    # And the rung inputs type has no slot it could be read from.
    assert "partition_label" not in FalsificationInputs.__dataclass_fields__
    assert "partition" not in FalsificationInputs.__dataclass_fields__


def test_no_falsification_rung_changes_its_answer_with_the_partition_label():
    """Behavioural companion to the static check.

    Every rung sees identical content under two different case IDs; F10 is the
    only rung that consumes ``case_id`` at all, and only as a ``derive_seed``
    namespace, which is exactly what section 6.0 permits.
    """
    content = synthetic_content(DEV)
    scalars = fit_case_scalars(content.compounds, content.trajectories)

    def _inputs(case_id: str) -> FalsificationInputs:
        return FalsificationInputs(
            case_id=case_id,
            discovered_expression_string="mass",
            complexity=4,
            effective_support=frozenset({"mass"}),
            target=scalars.g,
            compounds=content.compounds,
            trajectories=content.trajectories,
            null_threshold=NULL_THRESHOLD,
        )

    development = run_falsification(_inputs(DEV), lambda: "mass")
    held_out = run_falsification(_inputs(HELD), lambda: "mass")

    from muru.paper_benchmark.structural_acceptance import FalsificationRung

    for rung in (
        FalsificationRung.F1_REPRODUCIBILITY,
        FalsificationRung.F4_COMPOUND_HOLDOUT,
        FalsificationRung.F7_INFLUENCE_DROP,
    ):
        assert development.hard[rung] is held_out.hard[rung]
    assert development.f9_stress_test_result is held_out.f9_stress_test_result
    assert development.f9_stress_test_metric == held_out.f9_stress_test_metric
    for key in ("f4_r2", "f7_min_loso_r2", "f9_min_loeo_r2"):
        assert development.metrics[key] == held_out.metrics[key]


def test_candidate_test_r2_does_not_depend_on_the_partition_label():
    content = synthetic_content(DEV)
    scalars = fit_case_scalars(content.compounds, content.trajectories)

    def _value(case_id: str) -> float:
        return candidate_test_r2(
            FalsificationInputs(
                case_id=case_id,
                discovered_expression_string="mass",
                complexity=4,
                effective_support=frozenset({"mass"}),
                target=scalars.g,
                compounds=content.compounds,
                trajectories=content.trajectories,
                null_threshold=NULL_THRESHOLD,
            )
        )

    assert _value(DEV) == _value(HELD)


# -----------------------------------------------------------------------
# Static sweep across the whole RC5 science path
# -----------------------------------------------------------------------

SCIENCE_MODULES = [
    "rc5_estimate.py",
    "rc5_adapter.py",
    "rc5_selection.py",
    "rc5_falsify.py",
    "rc5_g1_bridge.py",
]


@pytest.mark.parametrize("name", SCIENCE_MODULES)
def test_no_rc5_science_module_names_the_partition_at_all(name):
    tree = ast.parse((_SRC / name).read_text(encoding="utf-8"))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in ("partition_label", "partition", "PARTITIONS", "iter_case_ids"):
        assert forbidden not in names, f"{name} reaches {forbidden}"


def test_only_the_runner_and_the_manifest_know_about_partitions():
    """Where partition identity is allowed to appear, and why.

    ``rc5_runner`` uses it for authorisation, content materialisation, and
    output routing.  ``rc5_manifest`` uses it to name a partition manifest and
    to select that partition's case IDs.  ``rc5_seeds`` uses it only to build
    the frozen enumeration order.  No other module may see it.
    """
    allowed = {
        "rc5_runner.py",
        "rc5_manifest.py",
        "rc5_seeds.py",
        # The single authorisation object A3.5 section 14.2 is expressed in;
        # every module that could open a partition imports it rather than
        # restating the refusal.
        "rc5_authorization.py",
    }
    for path in sorted(_SRC.glob("rc5_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        touches = "PARTITIONS" in names or "partition_label" in names
        if touches:
            assert path.name in allowed, f"{path.name} unexpectedly sees partitions"
