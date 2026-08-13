"""Amendment A1: the prospectively frozen M0/M1/M2/M3 adequacy decision rule.

Content freeze V1 (`d94d2c9`) defined M0 and the M1/M2/M3 generative
alternatives but never bound the rule that converts their fits into
`M0 REJECTED` or `M0 NOT REJECTED`.  This module binds that rule, and nothing
else, before any Development or Held-out scientific outcome exists.

Scope boundary.  This module owns the *decision contract*.  It deliberately
contains no fitter, no optimiser, and no numerical model evaluation: the
locked engine supplied by Engineering RC 2 performs the leave-one-energy-out
fits and reports :class:`CompoundContrastRecord` values back here.  Like the
registry, it cannot load inputs, truth values, or outcomes.

The extra parameter carried by each alternative is handled by within-compound
leave-one-energy-out prediction, never by an in-sample loss comparison and
never by an information-criterion parameter-count penalty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import comb, isfinite, log
from typing import Iterable, Mapping, Sequence

from .registry import endpoint_applies_to_variant, endpoint_case_count, resolve_case_id

AMENDMENT_ID = "A1"
ADEQUACY_CONTRACT_VERSION = "paper-benchmark-adequacy-1.0.0"
ORIGINAL_CONTENT_FREEZE_COMMIT = "d94d2c9"

# --------------------------------------------------------------------------
# Frozen scalar constants.  Every value below is fixed prospectively from the
# frozen registry, the frozen training-side support, or the frozen generator
# constants.  None of them was chosen from a Development or Held-out outcome.
# --------------------------------------------------------------------------

#: Test compounds per case (5 test scaffold groups x 6 compounds), from the
#: frozen generator split.
N_TEST_COMPOUNDS_EXPECTED = 30
#: Section 7A: minimum evaluable test compounds for a contrast to decide.
MIN_EVALUABLE_COMPOUNDS = 24
#: Section 7B: minimum practical wins for an alternative detector to fire.
MIN_PRACTICAL_WINS = 20
#: Section 6: the alternative must cut leave-one-energy-out error by >= 10%.
PRACTICAL_WIN_RATIO = 0.90
#: Section 10: a compound needs five observed distinct energies to be evaluable.
MIN_OBSERVED_ENERGIES = 5

#: Inherited unchanged from the frozen training-side scalar support.
LOG_G_BOUNDS = (-2.0, 2.0)
#: A factor-of-two horizontal warp in either direction; symmetric in log space.
LOG_SHAPE_BOUNDS = (-log(2.0), log(2.0))
#: The frozen generator response clip, reused as the admissible response range.
MU_FLOOR = 1e-4
MU_CEIL = 1.0 - 1e-4
#: Smallest admissible vertical span; keeps the normalised shape conditioned.
MIN_VERTICAL_AMPLITUDE = 0.05
#: The frozen generator horizontal normalisation energy.
E_REF = 45.0

#: Deterministic coarse-to-fine search protocol, identical for every model.
COARSE_LOG_G_POINTS = 81
COARSE_LOG_SHAPE_POINTS = 29
REFINEMENT_ROUNDS = 3
REFINEMENT_POINTS = 21
REFINEMENT_SHRINK = 10
FIT_OBJECTIVE = "unweighted_sum_of_squared_mu_residuals"

#: Absolute tolerance for declaring that a fitted parameter touches a bound.
BOUNDARY_CONTACT_TOL = 1e-9
#: Outward probe used to decide whether boundary contact is unresolved.
BOUNDARY_OUTWARD_PROBE = 1e-3

DETECTORS: tuple[str, ...] = ("M1", "M2", "M3")
REQUIRED_CONTRASTS: tuple[str, ...] = DETECTORS


class ContractFailure(RuntimeError):
    """The supplied records violate the frozen benchmark contract."""


# --------------------------------------------------------------------------
# Section 4 - model definitions and frozen fitting parameterisation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterSpec:
    """One compound-specific free parameter and its frozen admissible range."""

    name: str
    scale: str
    lower: str
    upper: str
    coarse_points: int
    solved_in_closed_form: bool = False


@dataclass(frozen=True)
class ModelSpec:
    """A frozen adequacy model written against the training-side shape S."""

    code: str
    deviation: str
    formula: str
    free_parameters: tuple[ParameterSpec, ...]
    reduces_to_m0_when: str
    generative_source: str
    objective: str = FIT_OBJECTIVE


_LOG_G = ParameterSpec("log_g", "natural_log", "-2.0", "+2.0", COARSE_LOG_G_POINTS)

ADEQUACY_MODELS: Mapping[str, ModelSpec] = {
    "M0": ModelSpec(
        code="M0",
        deviation="none",
        formula="mu_i(E) = A_HI + (A_LO - A_HI) * S(E / g_i)",
        free_parameters=(_LOG_G,),
        reduces_to_m0_when="",
        generative_source="generator._response_matrix shared branch: mu = mu_inf + (1 - mu_inf) * exp(-u**phi_p), u = (E / 45) / g",
    ),
    "M1": ModelSpec(
        code="M1",
        deviation="horizontal_shape",
        formula="mu_i(E) = A_HI + (A_LO - A_HI) * S(E_REF * (E / (E_REF * g_i)) ** s_i)",
        free_parameters=(
            _LOG_G,
            ParameterSpec("log_shape", "natural_log", "-ln(2)", "+ln(2)", COARSE_LOG_SHAPE_POINTS),
        ),
        reduces_to_m0_when="s_i = 1 (log_shape = 0)",
        generative_source="generator._response_matrix kinds no_scalar / m1_horizontal: exponent phi_p scaled per compound",
    ),
    "M2": ModelSpec(
        code="M2",
        deviation="high_energy_vertical_asymptote",
        formula="mu_i(E) = a_i + (A_LO - a_i) * S(E / g_i)",
        free_parameters=(
            _LOG_G,
            ParameterSpec("high_energy_asymptote", "response", "MU_FLOOR", "A_LO - MIN_VERTICAL_AMPLITUDE", 0, solved_in_closed_form=True),
        ),
        reduces_to_m0_when="a_i = A_HI",
        generative_source="generator._response_matrix kind m2_high_energy: compound-specific floor replaces mu_inf",
    ),
    "M3": ModelSpec(
        code="M3",
        deviation="low_energy_vertical_plateau",
        formula="mu_i(E) = A_HI + (b_i - A_HI) * S(E / g_i)",
        free_parameters=(
            _LOG_G,
            ParameterSpec("low_energy_plateau", "response", "A_HI + MIN_VERTICAL_AMPLITUDE", "MU_CEIL", 0, solved_in_closed_form=True),
        ),
        reduces_to_m0_when="b_i = A_LO",
        generative_source="generator._response_matrix kind m3_low_energy: compound-specific ceiling replaces the unit low-energy plateau",
    ),
}


# --------------------------------------------------------------------------
# Sections 6, 10, 11, 12 - compound-level status
# --------------------------------------------------------------------------


class CompoundContrastStatus(str, Enum):
    """Status of one test compound under one M0-vs-Mk contrast."""

    PRACTICAL_WIN = "PRACTICAL_WIN"
    NO_PRACTICAL_WIN = "NO_PRACTICAL_WIN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    BOUNDARY_LIMITED = "BOUNDARY_LIMITED"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    MODEL_FIT_FAILURE = "MODEL_FIT_FAILURE"
    TIMEOUT = "TIMEOUT"


EVALUABLE_STATUSES = frozenset({CompoundContrastStatus.PRACTICAL_WIN, CompoundContrastStatus.NO_PRACTICAL_WIN})

_EXECUTION_STATES = {
    "OK": None,
    "TIMEOUT": CompoundContrastStatus.TIMEOUT,
    "MODEL_FIT_FAILURE": CompoundContrastStatus.MODEL_FIT_FAILURE,
    "NUMERICAL_FAILURE": CompoundContrastStatus.NUMERICAL_FAILURE,
}


@dataclass(frozen=True)
class CompoundContrastRecord:
    """One test compound's leave-one-energy-out result for one contrast.

    The locked engine reports these; this module never computes them.
    """

    compound_id: str
    detector: str
    observed_energy_count: int
    mae_m0: float | None
    mae_alt: float | None
    execution_state: str = "OK"
    boundary_contact: bool = False
    unresolved_boundary: bool = False


def is_practical_win(mae_m0: float, mae_alt: float) -> bool:
    """Section 6 win test with the frozen binary64 comparison semantics.

    The product is the binary64 multiplication of the literal ``0.90`` by
    ``mae_m0``; the comparison is the binary64 ``<=`` operator; no epsilon is
    added or subtracted.  A perfect M0 fit leaves no 10% margin to win, so it
    can never be beaten, and an exact tie is therefore never a win.
    """
    for value in (mae_m0, mae_alt):
        if value is None or not isfinite(value):
            raise ContractFailure("leave-one-energy-out loss must be finite")
        if value < 0.0:
            raise ContractFailure("leave-one-energy-out loss must be non-negative")
    if mae_m0 == 0.0:
        return False
    return mae_alt <= PRACTICAL_WIN_RATIO * mae_m0


def classify_compound_contrast(record: CompoundContrastRecord) -> CompoundContrastStatus:
    """Resolve one compound's contrast status under the frozen precedence.

    Structural data adequacy is decided before any fit is attempted, then
    execution state, then unresolved boundary contact, then numerical
    validity, and only then the practical-win comparison.
    """
    if record.execution_state not in _EXECUTION_STATES:
        raise ContractFailure(f"unknown execution state: {record.execution_state}")
    if record.observed_energy_count < MIN_OBSERVED_ENERGIES:
        return CompoundContrastStatus.INSUFFICIENT_DATA
    failure = _EXECUTION_STATES[record.execution_state]
    if failure is not None:
        return failure
    if record.unresolved_boundary:
        return CompoundContrastStatus.BOUNDARY_LIMITED
    try:
        won = is_practical_win(record.mae_m0, record.mae_alt)
    except ContractFailure:
        return CompoundContrastStatus.NUMERICAL_FAILURE
    return CompoundContrastStatus.PRACTICAL_WIN if won else CompoundContrastStatus.NO_PRACTICAL_WIN


# --------------------------------------------------------------------------
# Section 7 - case-level aggregation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ContrastResult:
    """The M0-vs-Mk verdict for one case."""

    detector: str
    compound_count: int
    evaluable: int
    practical_wins: int
    status_counts: Mapping[str, int]
    evaluable_sufficient: bool
    fired: bool

    @property
    def indeterminate(self) -> bool:
        return not self.evaluable_sufficient


def evaluate_contrast(detector: str, records: Sequence[CompoundContrastRecord]) -> ContrastResult:
    """Aggregate one contrast over the frozen 30-compound test population."""
    if detector not in DETECTORS:
        raise ContractFailure(f"unknown detector: {detector}")
    count = len(records)
    if count > N_TEST_COMPOUNDS_EXPECTED:
        raise ContractFailure(
            f"{count} test compounds exceed the frozen population of {N_TEST_COMPOUNDS_EXPECTED}: contract failure, not a threshold change"
        )
    if count < N_TEST_COMPOUNDS_EXPECTED:
        raise ContractFailure(
            f"{count} test compounds fall short of the frozen population of {N_TEST_COMPOUNDS_EXPECTED}: registry inconsistency"
        )
    identifiers = {record.compound_id for record in records}
    if len(identifiers) != count:
        raise ContractFailure("duplicate test compound in a single contrast")
    counts = {status.value: 0 for status in CompoundContrastStatus}
    evaluable = wins = 0
    for record in records:
        if record.detector != detector:
            raise ContractFailure(f"record for detector {record.detector} supplied to the {detector} contrast")
        status = classify_compound_contrast(record)
        counts[status.value] += 1
        if status in EVALUABLE_STATUSES:
            evaluable += 1
        if status is CompoundContrastStatus.PRACTICAL_WIN:
            wins += 1
    sufficient = evaluable >= MIN_EVALUABLE_COMPOUNDS
    return ContrastResult(
        detector=detector,
        compound_count=count,
        evaluable=evaluable,
        practical_wins=wins,
        status_counts=counts,
        evaluable_sufficient=sufficient,
        fired=sufficient and wins >= MIN_PRACTICAL_WINS,
    )


def directional_null_tail(wins: int, evaluable: int) -> float:
    """P[X >= wins | X ~ Binomial(evaluable, 0.5)], the equal-probability null."""
    if evaluable < 0 or wins < 0:
        raise ContractFailure("binomial tail requires non-negative counts")
    if wins > evaluable:
        return 0.0
    return sum(comb(evaluable, k) for k in range(wins, evaluable + 1)) / float(2 ** evaluable)


# --------------------------------------------------------------------------
# Sections 8 and 12 - case adequacy status
# --------------------------------------------------------------------------


class CaseAdequacyStatus(str, Enum):
    """Every terminal adequacy state a case may reach."""

    M0_NOT_REJECTED = "M0_NOT_REJECTED"
    M0_REJECTED_M1 = "M0_REJECTED_M1"
    M0_REJECTED_M2 = "M0_REJECTED_M2"
    M0_REJECTED_M3 = "M0_REJECTED_M3"
    M0_REJECTED_MULTIPLE = "M0_REJECTED_MULTIPLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    BOUNDARY_LIMITED = "BOUNDARY_LIMITED"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    MODEL_FIT_FAILURE = "MODEL_FIT_FAILURE"
    TIMEOUT = "TIMEOUT"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"


#: Most severe first.  An indeterminate case is reported under the most severe
#: cause present, so an execution failure can never hide behind a declared
#: structural limitation.
INDETERMINATE_SEVERITY: tuple[CaseAdequacyStatus, ...] = (
    CaseAdequacyStatus.CONTRACT_FAILURE,
    CaseAdequacyStatus.TIMEOUT,
    CaseAdequacyStatus.MODEL_FIT_FAILURE,
    CaseAdequacyStatus.NUMERICAL_FAILURE,
    CaseAdequacyStatus.BOUNDARY_LIMITED,
    CaseAdequacyStatus.INSUFFICIENT_DATA,
)

_REJECTION_BY_DETECTOR = {
    "M1": CaseAdequacyStatus.M0_REJECTED_M1,
    "M2": CaseAdequacyStatus.M0_REJECTED_M2,
    "M3": CaseAdequacyStatus.M0_REJECTED_M3,
}


@dataclass(frozen=True)
class CaseAdequacyResult:
    """The frozen adequacy verdict for one benchmark case."""

    case_id: str
    status: CaseAdequacyStatus
    contrasts: Mapping[str, ContrastResult]
    fired: tuple[str, ...]
    blocker: str = ""
    boundary_counts: Mapping[str, int] = field(default_factory=dict)

    @property
    def m0_not_rejected(self) -> bool:
        return self.status is CaseAdequacyStatus.M0_NOT_REJECTED

    @property
    def satisfies_g1_adequacy(self) -> bool:
        return adequacy_satisfies_g1(self.status)


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


def decide_case_adequacy(
    case_id: str,
    contrast_records: Mapping[str, Sequence[CompoundContrastRecord]],
) -> CaseAdequacyResult:
    """Apply the Amendment A1 adequacy rule to one case.

    M0 is rejected when any required alternative fires.  When none fires, M0
    may be recorded as not rejected only if all three required contrasts are
    evaluable; otherwise the case takes an indeterminate state.  No
    non-success execution state can become M0 acceptance.
    """
    missing = [name for name in REQUIRED_CONTRASTS if name not in contrast_records]
    if missing:
        return CaseAdequacyResult(
            case_id=case_id,
            status=CaseAdequacyStatus.CONTRACT_FAILURE,
            contrasts={},
            fired=(),
            blocker=f"required contrast(s) absent: {', '.join(missing)}",
        )
    contrasts: dict[str, ContrastResult] = {}
    for detector in REQUIRED_CONTRASTS:
        try:
            contrasts[detector] = evaluate_contrast(detector, list(contrast_records[detector]))
        except ContractFailure as failure:
            return CaseAdequacyResult(
                case_id=case_id,
                status=CaseAdequacyStatus.CONTRACT_FAILURE,
                contrasts=dict(contrasts),
                fired=(),
                blocker=str(failure),
            )
    boundary_counts = {
        detector: result.status_counts[CompoundContrastStatus.BOUNDARY_LIMITED.value]
        for detector, result in contrasts.items()
    }
    fired = tuple(detector for detector in REQUIRED_CONTRASTS if contrasts[detector].fired)
    if len(fired) > 1:
        status, blocker = CaseAdequacyStatus.M0_REJECTED_MULTIPLE, ""
    elif len(fired) == 1:
        status, blocker = _REJECTION_BY_DETECTOR[fired[0]], ""
    elif all(result.evaluable_sufficient for result in contrasts.values()):
        status, blocker = CaseAdequacyStatus.M0_NOT_REJECTED, ""
    else:
        status = _indeterminate_status(contrasts)
        insufficient = [name for name, result in contrasts.items() if not result.evaluable_sufficient]
        blocker = f"contrast(s) below the {MIN_EVALUABLE_COMPOUNDS}-compound evaluability floor: {', '.join(insufficient)}"
    return CaseAdequacyResult(
        case_id=case_id,
        status=status,
        contrasts=contrasts,
        fired=fired,
        blocker=blocker,
        boundary_counts=boundary_counts,
    )


# --------------------------------------------------------------------------
# Sections 9 and 14 - detector-specific sensitivity and M0 specificity
# --------------------------------------------------------------------------


def detector_endpoint_name(detector: str) -> str:
    if detector not in DETECTORS:
        raise ContractFailure(f"unknown detector: {detector}")
    return f"m{detector[1]}_sensitivity"


def detector_sensitivity_success(result: CaseAdequacyResult, detector: str) -> bool:
    """Detector identity is preserved: only Mk firing satisfies Mk sensitivity."""
    if detector not in DETECTORS:
        raise ContractFailure(f"unknown detector: {detector}")
    return detector in result.fired


def m0_specificity_success(result: CaseAdequacyResult) -> bool:
    """M0 specificity succeeds only on an outright M0_NOT_REJECTED case."""
    return result.m0_not_rejected


@dataclass(frozen=True)
class EndpointScore:
    """A case-level endpoint numerator against its frozen denominator."""

    endpoint: str
    numerator: int
    applicable_supplied: int
    denominator: int

    @property
    def complete(self) -> bool:
        return self.applicable_supplied == self.denominator


def _held_out_applicable(endpoint: str, results: Iterable[CaseAdequacyResult]) -> list[CaseAdequacyResult]:
    selected = []
    for result in results:
        if not result.case_id.startswith("PB|held_out|"):
            continue
        _, variant, _ = resolve_case_id(result.case_id)
        if endpoint_applies_to_variant(endpoint, variant):
            selected.append(result)
    return selected


def sensitivity_score(detector: str, results: Iterable[CaseAdequacyResult]) -> EndpointScore:
    """Score one detector-specific sensitivity endpoint deterministically."""
    endpoint = detector_endpoint_name(detector)
    applicable = _held_out_applicable(endpoint, results)
    return EndpointScore(
        endpoint=endpoint,
        numerator=sum(detector_sensitivity_success(result, detector) for result in applicable),
        applicable_supplied=len(applicable),
        denominator=endpoint_case_count(endpoint),
    )


def m0_specificity_score(results: Iterable[CaseAdequacyResult]) -> EndpointScore:
    """Score M0 specificity against its frozen 164-case denominator."""
    applicable = _held_out_applicable("m0_specificity", results)
    return EndpointScore(
        endpoint="m0_specificity",
        numerator=sum(m0_specificity_success(result) for result in applicable),
        applicable_supplied=len(applicable),
        denominator=endpoint_case_count("m0_specificity"),
    )


# --------------------------------------------------------------------------
# Section 13 - G1 interaction
# --------------------------------------------------------------------------


def adequacy_satisfies_g1(status: CaseAdequacyStatus | str) -> bool:
    """Only M0_NOT_REJECTED satisfies the adequacy component of G1.

    Every indeterminate or failure state leaves G1 unsatisfied.  The frozen G1
    rank, trajectory, and Wilson thresholds are untouched by this amendment.
    """
    return CaseAdequacyStatus(status) is CaseAdequacyStatus.M0_NOT_REJECTED
