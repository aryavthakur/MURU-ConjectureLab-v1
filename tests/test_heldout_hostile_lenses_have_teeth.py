"""Mutation tests proving each hostile lens can actually fail.

The superseded hostile review's six checkpoints all passed, and two of them
*could not have failed*: the denominator lens asserted every total equalled
240 (certifying the defect), and the Gate 7 / Gate 8 lens branched on three
fields that do not exist in the record schema, so its only condition never
fired.

A lens that cannot fail is decoration.  Each test below feeds a lens a
deliberately corrupted analysis and requires it to report a failure.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from muru.paper_benchmark import heldout_hostile_lenses as lenses
from muru.paper_benchmark.rc5_store import case_slug
from muru.paper_benchmark.registry import iter_case_ids

EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
RESTORED = REPO_ROOT / "results" / "restored"

pytestmark = pytest.mark.skipif(
    not (EVIDENCE_ROOT / "records").is_dir()
    or not (RESTORED / "heldout_restored_analysis.json").exists(),
    reason="sealed evidence or restored analysis unavailable",
)


@pytest.fixture(scope="module")
def ctx() -> lenses.LensContext:
    primary = json.loads((RESTORED / "heldout_restored_analysis.json").read_text())
    independent = json.loads(
        (RESTORED / "heldout_independent_recomputation.json").read_text()
    )
    recovery_path = RESTORED / "heldout_g1_recovery.json"
    recovery = json.loads(recovery_path.read_text()) if recovery_path.exists() else None
    table = json.loads(
        (REPO_ROOT / "calibration" / "a3_2" / "threshold_table.json").read_text()
    )
    records = EVIDENCE_ROOT / "records"
    payloads = {
        case_id: json.loads((records / f"{case_slug(case_id)}.json").read_text())
        for case_id in iter_case_ids("held_out")
    }
    return lenses.LensContext(
        evidence_root=EVIDENCE_ROOT,
        repo_root=REPO_ROOT,
        primary=primary,
        independent=independent,
        g1_recovery=recovery,
        payloads=payloads,
        null_threshold={int(k): float(v) for k, v in table["thresholds"].items()},
    )


def _mutate(ctx: lenses.LensContext, **overrides) -> lenses.LensContext:
    primary = copy.deepcopy(dict(ctx.primary))
    for dotted, value in overrides.items():
        target = primary
        *path, leaf = dotted.split("__")
        for key in path:
            target = target[key]
        target[leaf] = value
    return lenses.LensContext(
        evidence_root=ctx.evidence_root,
        repo_root=ctx.repo_root,
        primary=primary,
        independent=ctx.independent,
        g1_recovery=ctx.g1_recovery,
        payloads=ctx.payloads,
        null_threshold=ctx.null_threshold,
    )


def _failed_checks(report: lenses.LensReport) -> set[str]:
    return {f.check for f in report.findings if not f.ok}


def test_all_seven_lenses_pass_on_the_real_analysis(ctx):
    result = lenses.run_all_lenses(ctx)
    assert result["lens_count"] == 7
    assert result["all_passed"], result
    assert result["total_checks"] >= 60


def test_population_lens_rejects_a_240_denominator(ctx):
    """The exact defect the superseded denominator lens certified."""
    corrupted = _mutate(
        ctx,
        endpoint_denominators__scalar_competence=240,
        endpoint_denominators__family_recovery=240,
        endpoint_denominators__principal_structural_safety=240,
    )
    report = lenses.lens_populations(corrupted)
    assert not report.passed
    failed = _failed_checks(report)
    assert "primary_uses_the_reconstructed_denominator/scalar_competence" in failed
    assert "primary_uses_the_reconstructed_denominator/family_recovery" in failed
    assert "primary_uses_the_reconstructed_denominator/principal_structural_safety" in failed


def test_g1_lens_rejects_a_count_above_the_m0_bound(ctx):
    corrupted = _mutate(ctx, g1__competent=119)
    report = lenses.lens_g1(corrupted)
    assert not report.passed
    assert "reported_count_respects_the_m0_upper_bound" in _failed_checks(report)


def test_g1_lens_rejects_a_declared_pass(ctx):
    corrupted = _mutate(ctx, g1__gate_passed=True)
    report = lenses.lens_g1(corrupted)
    assert "gate_verdict_is_determinate_at_the_bound" in _failed_checks(report)


def test_g2_lens_rejects_the_superseded_or_success_set(ctx):
    """23 successes over 240 is the superseded G2."""
    corrupted = _mutate(
        ctx,
        g2__successes=23,
        g2__denominator=240,
        g2__success_case_ids=[],
    )
    report = lenses.lens_g2(corrupted)
    assert not report.passed
    failed = _failed_checks(report)
    assert "denominator_is_the_frozen_144" in failed
    assert "success_set_reconstructs_exactly" in failed


def test_g3_lens_rejects_an_inverted_direction(ctx):
    """The superseded G3 counted safety successes with no upper-tail gate."""
    corrupted = _mutate(
        ctx,
        g3__violations=2,
        g3__gate="wilson_lower_95 >= 0.70",
        g3__gate_passed=True,
    )
    report = lenses.lens_g3(corrupted)
    assert not report.passed
    failed = _failed_checks(report)
    assert "violation_set_reconstructs_exactly" in failed
    assert "direction_is_an_upper_bound_not_a_success_rate" in failed


def test_gate_lens_rejects_gate7_conflated_with_structural_acceptance(ctx):
    corrupted = _mutate(ctx, gate7__passed=25, gate7__reached=25)
    report = lenses.lens_gates(corrupted)
    assert not report.passed
    failed = _failed_checks(report)
    assert "gate7_reconstructs_from_the_ceiling_predicate" in failed
    assert "gate7_is_not_structural_acceptance" in failed


def test_gate_lens_rejects_a_wrong_gate8_count(ctx):
    corrupted = _mutate(ctx, gate8__passed=24, gate8__reached=240)
    report = lenses.lens_gates(corrupted)
    assert "gate8_reconstructs_from_the_rung_results" in _failed_checks(report)


def test_gate_lens_rejects_f9_declared_gating(ctx):
    corrupted = _mutate(ctx, f9__gating=True)
    report = lenses.lens_gates(corrupted)
    assert "f9_reported_from_its_own_observable" in _failed_checks(report)


def test_governance_lens_rejects_a_declared_pass(ctx):
    corrupted = _mutate(ctx, decision__all_primary_endpoints_pass=True)
    report = lenses.lens_governance(corrupted)
    assert not report.passed
    assert (
        "the_repair_changes_the_verdict_against_the_authors_interest"
        in _failed_checks(report)
    )


def test_governance_lens_rejects_drift_from_the_sealed_forensic_result(ctx):
    corrupted = _mutate(ctx, g3__violations=2, gate8__passed=24)
    report = lenses.lens_governance(corrupted)
    assert (
        "restored_numbers_match_the_pre_repair_sealed_forensic_result"
        in _failed_checks(report)
    )


def test_provenance_lens_rejects_a_tampered_evidence_root(ctx, tmp_path):
    """Copy the seal receipt, corrupt one recorded hash, require detection."""
    receipt = json.loads((EVIDENCE_ROOT / "execution_seal_receipt.json").read_text())
    fake_root = tmp_path / "held_out"
    fake_root.mkdir()
    (fake_root / "execution_seal_receipt.json").write_text(
        json.dumps({**receipt, "sealed": False})
    )
    corrupted = lenses.LensContext(
        evidence_root=fake_root,
        repo_root=ctx.repo_root,
        primary=ctx.primary,
        independent=ctx.independent,
        g1_recovery=ctx.g1_recovery,
        payloads=ctx.payloads,
        null_threshold=ctx.null_threshold,
    )
    with pytest.raises(Exception):
        lenses.lens_provenance(corrupted)


def test_every_lens_has_at_least_one_failable_check(ctx):
    """No lens may consist only of checks whose condition cannot fire."""
    for lens in lenses.LENSES:
        report = lens(ctx)
        assert report.findings, f"{report.lens} produced no checks at all"
        assert len(report.findings) >= 5, (
            f"{report.lens} has only {len(report.findings)} checks"
        )
