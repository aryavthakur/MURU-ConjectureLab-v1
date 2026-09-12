"""The M0-to-M3 adequacy ladder for a test population of any size.

Preregistration `wur-real-data-1.0` section 7 (erratum E-1) turns the frozen
contract's 30 / 24 / 20 into fractions of the realized test population:
evaluable >= 0.80 of test compounds, practical wins >= 2/3 of test
compounds, both denominators the test compounds. The comparisons are done in
integer arithmetic so that N = 30 reproduces 24 and 20 exactly and no
binary64 rounding of 0.8 * N can move a threshold.

Everything below the case level is the frozen engine, untouched:
`evaluate_compound_contrast`, `classify_compound_contrast`, the practical-win
test, the precedence of statuses, and the severity order of indeterminate
states.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd

from muru.paper_benchmark.adequacy import (
    DETECTORS,
    INDETERMINATE_SEVERITY,
    MIN_EVALUABLE_COMPOUNDS,
    MIN_PRACTICAL_WINS,
    N_TEST_COMPOUNDS_EXPECTED,
    REQUIRED_CONTRASTS,
    CaseAdequacyResult,
    CaseAdequacyStatus,
    CompoundContrastRecord,
    CompoundContrastStatus,
    ContractFailure,
    ContrastResult,
    EVALUABLE_STATUSES,
    classify_compound_contrast,
    directional_null_tail,
)
from muru.paper_benchmark.rc5_adequacy import (
    ProfileShape,
    evaluate_compound_contrast,
)
from muru.paper_benchmark.rc5_estimate import FrozenPhi

EVALUABLE_NUM, EVALUABLE_DEN = 4, 5      # evaluable >= 4/5 of test compounds
WIN_NUM, WIN_DEN = 2, 3                  # wins      >= 2/3 of test compounds

_REJECTION_BY_DETECTOR = {
    "M1": CaseAdequacyStatus.M0_REJECTED_M1,
    "M2": CaseAdequacyStatus.M0_REJECTED_M2,
    "M3": CaseAdequacyStatus.M0_REJECTED_M3,
}


def evaluable_sufficient(evaluable: int, n_test: int) -> bool:
    return EVALUABLE_DEN * evaluable >= EVALUABLE_NUM * n_test


def wins_sufficient(wins: int, n_test: int) -> bool:
    return WIN_DEN * wins >= WIN_NUM * n_test


def min_evaluable(n_test: int) -> int:
    """Smallest evaluable count that is sufficient at this N."""
    return -(-EVALUABLE_NUM * n_test // EVALUABLE_DEN)


def min_wins(n_test: int) -> int:
    return -(-WIN_NUM * n_test // WIN_DEN)


assert min_evaluable(N_TEST_COMPOUNDS_EXPECTED) == MIN_EVALUABLE_COMPOUNDS
assert min_wins(N_TEST_COMPOUNDS_EXPECTED) == MIN_PRACTICAL_WINS


def evaluate_contrast_fraction(detector: str,
                               records: Sequence[CompoundContrastRecord]
                               ) -> ContrastResult:
    """One detector's contrast over a test population of any positive size."""
    if detector not in DETECTORS:
        raise ContractFailure(f"unknown detector: {detector}")
    count = len(records)
    if count == 0:
        raise ContractFailure("a contrast needs at least one test compound")
    identifiers = {r.compound_id for r in records}
    if len(identifiers) != count:
        raise ContractFailure("duplicate test compound in a single contrast")
    counts = {status.value: 0 for status in CompoundContrastStatus}
    evaluable = wins = 0
    for record in records:
        if record.detector != detector:
            raise ContractFailure(
                f"record for detector {record.detector} supplied to the {detector} contrast")
        status = classify_compound_contrast(record)
        counts[status.value] += 1
        if status in EVALUABLE_STATUSES:
            evaluable += 1
        if status is CompoundContrastStatus.PRACTICAL_WIN:
            wins += 1
    sufficient = evaluable_sufficient(evaluable, count)
    return ContrastResult(
        detector=detector, compound_count=count, evaluable=evaluable,
        practical_wins=wins, status_counts=counts,
        evaluable_sufficient=sufficient,
        fired=sufficient and wins_sufficient(wins, count),
    )


def _indeterminate_status(contrasts: Mapping[str, ContrastResult]) -> CaseAdequacyStatus:
    present = set()
    for result in contrasts.values():
        if result.evaluable_sufficient:
            continue
        for status in INDETERMINATE_SEVERITY:
            if result.status_counts.get(status.value, 0) > 0:
                present.add(status)
    for status in INDETERMINATE_SEVERITY:
        if status in present:
            return status
    return CaseAdequacyStatus.INSUFFICIENT_DATA


def decide_case_adequacy_fraction(
    case_id: str,
    contrast_records: Mapping[str, Sequence[CompoundContrastRecord]],
) -> CaseAdequacyResult:
    """`adequacy.decide_case_adequacy` with the fraction rule at the case level."""
    missing = [n for n in REQUIRED_CONTRASTS if n not in contrast_records]
    if missing:
        return CaseAdequacyResult(case_id=case_id,
                                  status=CaseAdequacyStatus.CONTRACT_FAILURE,
                                  contrasts={}, fired=(),
                                  blocker=f"required contrast(s) absent: {', '.join(missing)}")
    contrasts: dict[str, ContrastResult] = {}
    for detector in REQUIRED_CONTRASTS:
        try:
            contrasts[detector] = evaluate_contrast_fraction(
                detector, list(contrast_records[detector]))
        except ContractFailure as failure:
            return CaseAdequacyResult(case_id=case_id,
                                      status=CaseAdequacyStatus.CONTRACT_FAILURE,
                                      contrasts=dict(contrasts), fired=(),
                                      blocker=str(failure))
    boundary_counts = {
        d: r.status_counts[CompoundContrastStatus.BOUNDARY_LIMITED.value]
        for d, r in contrasts.items()}
    fired = tuple(d for d in REQUIRED_CONTRASTS if contrasts[d].fired)
    if len(fired) > 1:
        status, blocker = CaseAdequacyStatus.M0_REJECTED_MULTIPLE, ""
    elif len(fired) == 1:
        status, blocker = _REJECTION_BY_DETECTOR[fired[0]], ""
    elif all(r.evaluable_sufficient for r in contrasts.values()):
        status, blocker = CaseAdequacyStatus.M0_NOT_REJECTED, ""
    else:
        status = _indeterminate_status(contrasts)
        n = next(iter(contrasts.values())).compound_count
        insufficient = [d for d, r in contrasts.items() if not r.evaluable_sufficient]
        blocker = (f"contrast(s) below the {min_evaluable(n)}-of-{n} evaluability "
                   f"floor: {', '.join(insufficient)}")
    return CaseAdequacyResult(case_id=case_id, status=status, contrasts=contrasts,
                              fired=fired, blocker=blocker,
                              boundary_counts=boundary_counts)


def run_case_adequacy_fraction(
    case_id: str,
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    phi: FrozenPhi,
) -> tuple[CaseAdequacyResult, dict[str, list[CompoundContrastRecord]]]:
    """`rc5_adequacy.run_case_adequacy` without the hard N = 30 requirement.

    Returns the verdict and every compound-level record, so the run can
    persist the evidence the verdict rests on.
    """
    shape = ProfileShape.from_phi(phi)
    test_ids = [str(c) for c in compounds.loc[compounds["split"] == "test", "compound_id"]]
    if not test_ids:
        raise ContractFailure(f"case {case_id} has no test compounds")
    records: dict[str, list[CompoundContrastRecord]] = {d: [] for d in DETECTORS}
    for detector in DETECTORS:
        for cid in test_ids:
            subset = trajectories[trajectories["compound_id"] == cid]
            records[detector].append(evaluate_compound_contrast(
                compound_id=cid, detector=detector,
                energies=subset["energy"].to_numpy(),
                mu=subset["mu"].to_numpy(), shape=shape))
    return decide_case_adequacy_fraction(case_id, records), records


def contrast_summary(result: ContrastResult) -> dict:
    n = result.compound_count
    return {
        "detector": result.detector,
        "n_test": n,
        "evaluable": result.evaluable,
        "evaluable_fraction": result.evaluable / n,
        "min_evaluable": min_evaluable(n),
        "evaluable_sufficient": result.evaluable_sufficient,
        "practical_wins": result.practical_wins,
        "win_fraction_of_test": result.practical_wins / n,
        "win_fraction_of_evaluable": (result.practical_wins / result.evaluable
                                      if result.evaluable else None),
        "min_wins": min_wins(n),
        "fired": result.fired,
        "status_counts": dict(result.status_counts),
        "directional_null_tail": (directional_null_tail(result.practical_wins,
                                                        result.evaluable)
                                  if result.evaluable else None),
    }
