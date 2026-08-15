"""Engineering RC5: the production case runner.

**Composition only.**  This module defines no scientific threshold, no
denominator, no gate, and no special case.  Every rule it applies is imported
from the module that owns it, and every constant it touches is frozen
elsewhere.  If a number appears here that is not a loop bound or an index, it
is a defect.

**No branch changes scientific behaviour on partition identity.**  The
partition name is used for exactly three administrative things -- deciding
whether execution is *authorised at all*, materialising the right case
content, and routing output paths -- and for nothing else.  Every scientific
call below receives the same arguments it would receive for any other
partition with the same content.  The property test in
``tests/test_rc5_partition_identity.py`` proves it end to end.

**Authorisation.**  A3.5 section 14.2 authorises RC5 to execute the
**Development** partition only.  :func:`assert_partition_authorised` refuses
every other partition before any content is materialised, so Held-out and
Challenge cannot be executed by this runner even by mistake.

**What this module deliberately does not compute.**  ``a1_case_adequacy_status``
is a **required input**, never derived here.  A1 owns the adequacy decision
contract, and ``adequacy.py`` states its own scope boundary: it "deliberately
contains no fitter, no optimiser, and no numerical model evaluation", and the
M1/M2/M3 contrast records are reported to it by the locked engine.  No D-item
of the RC5 map covers building that engine, so RC5 consumes the adequacy verdict
rather than inventing one.  Supplying it is the Development execution session's
job; a caller that cannot supply it cannot run a case, which is the safe
failure.
"""
from __future__ import annotations

import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

import numpy as np
import pandas as pd

from muru.discovery.grammar import finite_mask

from .adequacy import CaseAdequacyStatus
from .artifacts import verify_hash_inventory
from .calibration_contract import SeedStatus
from .g2_contract import (
    classify_discovered_family,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
    extract_effective_support,
    truth_support_for_case,
)
from .generator import generate_case
from .governance import ImplementationLock
from .preflight import run_preflight
from .rc3_ceiling import estimate_ceiling
from .rc3_record import CaseExecutionRecord, PerSeedStatusEntry, ProvenanceSidecar
from .registry import PARTITIONS, resolve_case_id
from .rc5_adapter import (
    CaseDesign,
    assert_grammar_settings,
    assert_selected_complexity_in_range,
    build_case_design,
    build_case_regressor,
    candidate_r2_on,
    row_complexity,
    row_position,
)
from .rc5_case_scoring import case_acceptance, case_g3_event, score_case_secondaries
from .rc5_estimate import (
    N_VALIDATION_COMPOUNDS,
    TEST_SPLIT,
    VALIDATION_SPLIT,
    fit_case_scalars,
    invalid_fraction,
    invalid_fraction_passes,
)
from .rc5_falsify import FalsificationInputs, candidate_test_r2, run_falsification
from .rc5_manifest import verify_partition_manifest
from .rc5_seeds import case_search_seeds
from .rc5_selection import (
    RetainedCandidate,
    SeedExecutionFailure,
    SeedNoCandidate,
    SeedSelection,
    group_and_select,
    select_row_label,
)
from .rc5_store import (
    CaseSeedRecordStore,
    append_provenance,
    resume_plan,
    write_case_record,
)
from .structural_acceptance import AcceptanceStatus, StructuralCandidate

__all__ = [
    "AUTHORISED_PARTITIONS",
    "PartitionNotAuthorised",
    "assert_partition_authorised",
    "CaseContent",
    "materialize_case",
    "SeedSearchOutcome",
    "CaseSearchBackend",
    "PySRCaseBackend",
    "RunnerPreconditions",
    "check_preconditions",
    "execute_case",
    "run_partition",
]

#: A3.5 section 14.2: "RC5 may execute the **Development** partition only."
AUTHORISED_PARTITIONS: frozenset[str] = frozenset({"development"})


class PartitionNotAuthorised(RuntimeError):
    """A3.5 section 14.2 does not authorise executing this partition."""


def assert_partition_authorised(partition: str) -> None:
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    if partition not in AUTHORISED_PARTITIONS:
        raise PartitionNotAuthorised(
            f"A3.5 section 14.2 authorises the Development partition only; RC5 is "
            f"not authorised to open Held-out, construct or execute Challenge, or "
            f"open Confirmation. Refusing {partition!r}."
        )


# -----------------------------------------------------------------------
# Case content
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseContent:
    """One case's materialised inputs and truth."""

    case_id: str
    compounds: pd.DataFrame
    trajectories: pd.DataFrame
    truth: Any
    content_hash: str


def materialize_case(case_id: str) -> CaseContent:
    """Materialise one authorised case.

    The partition is re-derived from the case ID and re-checked here, so a
    caller cannot materialise an unauthorised partition's content by handing
    this function a bare ID.
    """
    _family, _variant, _replicate = resolve_case_id(case_id)
    assert_partition_authorised(case_id.split("|")[1])
    generated = generate_case(case_id)
    return CaseContent(
        case_id=case_id,
        compounds=generated.inputs.compounds,
        trajectories=generated.inputs.trajectories,
        truth=generated.truth,
        content_hash=generated.content_hash,
    )


# -----------------------------------------------------------------------
# The search backend
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class SeedSearchOutcome:
    """One seed's raw engine output."""

    equations: pd.DataFrame | None
    model: Any


class CaseSearchBackend(Protocol):
    def search(self, design: CaseDesign, seed: int) -> SeedSearchOutcome: ...


class PySRCaseBackend:
    """PySR under the frozen settings, fitted on the case's train rows.

    Fitted without sample weights, exactly as ``PySRBackend.search`` does.
    ``model_selection`` is never set on the regressor; retention is applied to
    the emitted frame by :mod:`rc5_selection`.
    """

    def __init__(self, work_dir: Path | None = None):
        assert_grammar_settings()
        self.work_dir = work_dir

    def search(self, design: CaseDesign, seed: int) -> SeedSearchOutcome:
        train = design.train_mask
        if not train.any():
            raise RuntimeError("case has an empty train partition")
        model = build_case_regressor(seed, work_dir=self.work_dir)
        model.fit(design.design[train], design.target[train])
        equations = getattr(model, "equations_", None)
        return SeedSearchOutcome(equations=equations, model=model)


# -----------------------------------------------------------------------
# Preconditions
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class RunnerPreconditions:
    """What the runner verified before touching any case."""

    partition: str
    hash_inventory: Mapping[str, str]
    preflight: Mapping[str, object]
    manifest_verification: Mapping[str, str]
    grammar: Mapping[str, object]


def check_preconditions(
    partition: str,
    artifact_dir: Path,
    lock: ImplementationLock,
    plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> RunnerPreconditions:
    """Every gate that must hold before the first case is materialised.

    Ordered so the cheapest, most structural refusal comes first: an
    unauthorised partition is rejected before any artifact is read.
    """
    assert_partition_authorised(partition)
    grammar = assert_grammar_settings()
    inventory = verify_hash_inventory(Path(artifact_dir))
    report = run_preflight(Path(artifact_dir), lock, partition)
    verification = verify_partition_manifest(plan, manifest)
    if verification["partition"] != partition:
        raise ValueError(
            f"manifest is for {verification['partition']!r}, not {partition!r}"
        )
    return RunnerPreconditions(
        partition=partition,
        hash_inventory=inventory,
        preflight=report.to_dict(),
        manifest_verification=verification,
        grammar=grammar,
    )


# -----------------------------------------------------------------------
# One seed
# -----------------------------------------------------------------------

def _run_one_seed(
    design: CaseDesign,
    backend: CaseSearchBackend,
    k: int,
    seed: int,
) -> SeedSelection:
    """Search one seed and retain at most one candidate from its front.

    Every degenerate state is A3.5 section 7.6's, applied in its order.  There
    is no fallback to another row anywhere.
    """
    try:
        outcome = backend.search(design, seed)
    except Exception as error:
        return SeedSelection(
            k=k, seed=seed, status=SeedStatus.EXECUTION_FAILURE,
            error_message=f"{type(error).__name__}: {error}",
        )

    try:
        label = select_row_label(outcome.equations)
    except SeedNoCandidate:
        return SeedSelection(k=k, seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE)
    except SeedExecutionFailure as error:
        return SeedSelection(
            k=k, seed=seed, status=SeedStatus.EXECUTION_FAILURE,
            error_message=f"{type(error).__name__}: {error}",
        )

    equations = outcome.equations
    try:
        position = row_position(equations, label)
        complexity = row_complexity(equations, label)
        assert_selected_complexity_in_range(complexity)
        expression = str(equations["equation"].iloc[position])
        valid_r2 = candidate_r2_on(
            outcome.model, equations, label, design.design, design.target,
            design.validation_mask,
        )
        predictions = np.asarray(
            outcome.model.predict(
                design.design[design.validation_mask], index=position
            ),
            dtype=np.float64,
        )
    except Exception as error:
        return SeedSelection(
            k=k, seed=seed, status=SeedStatus.EXECUTION_FAILURE,
            error_message=f"{type(error).__name__}: {error}",
        )

    if extract_effective_support(expression) is None:
        return SeedSelection(k=k, seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE)

    fraction = invalid_fraction(predictions, N_VALIDATION_COMPOUNDS)
    if not invalid_fraction_passes(fraction):
        # No fallback to the next row (section 7.6).
        return SeedSelection(k=k, seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE)

    return SeedSelection(
        k=k,
        seed=seed,
        status=SeedStatus.COMPLETED_WITH_CANDIDATES,
        candidate=RetainedCandidate(
            k=k,
            seed=seed,
            expression_string=expression,
            complexity=complexity,
            valid_r2=float(valid_r2),
            invalid_fraction=float(fraction),
            # Filled once, at case level, from the representative only.
            candidate_test_r2=float("-inf"),
        ),
    )


# -----------------------------------------------------------------------
# One case
# -----------------------------------------------------------------------

def _unevaluable_record(
    content: CaseContent,
    a1_status: CaseAdequacyStatus,
    selections: Sequence[SeedSelection],
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    gate: str,
) -> CaseExecutionRecord:
    acceptance = case_acceptance(a1_status, None, null_threshold)
    _family, variant, _replicate = resolve_case_id(content.case_id)
    return CaseExecutionRecord(
        case_id=content.case_id,
        family_id=variant.code,
        partition_label=content.case_id.split("|")[1],
        truth_family=content.truth.mathematical_family,
        truth_support=frozenset(content.truth.active_variables or ()),
        discovered_expression_string=None,
        effective_support=None,
        support_status=classify_support(None, frozenset()),
        family_status=classify_family_match(None, content.truth.mathematical_family),
        discovered_family=None,
        g2_event=evaluate_g2_event(
            classify_support(None, frozenset()),
            classify_family_match(None, content.truth.mathematical_family),
        ),
        a1_case_adequacy_status=a1_status,
        valid_r2=float("-inf"),
        complexity=0,
        selection_count=0,
        selection_denominator=30,
        invalid_fraction=1.0,
        ceiling_r2=float("-inf"),
        ceiling_fraction=float("-inf"),
        falsification_results={},
        acceptance_status=AcceptanceStatus.UNEVALUABLE,
        acceptance_gate_reached=gate,
        per_seed_status=[
            PerSeedStatusEntry(
                seed=s.seed,
                status=s.status,
                selected_expression_string=(
                    s.candidate.expression_string if s.candidate else None
                ),
                error_message=s.error_message,
            )
            for s in selections
        ],
        seeds_used=[s.seed for s in selections],
        engine_versions=dict(engine_versions),
        null_threshold_digest=acceptance.null_threshold_digest,
    )


def execute_case(
    content: CaseContent,
    a1_status: CaseAdequacyStatus,
    backend: CaseSearchBackend,
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    seed_store: CaseSeedRecordStore | None = None,
    reexecute: Callable[[], str | None] | None = None,
) -> CaseExecutionRecord:
    """Execute one case end to end and return its record.

    ``a1_status`` is required: RC5 consumes A1's adequacy verdict and never
    derives one (see the module docstring).
    """
    seeds = case_search_seeds(content.case_id)

    scalars = fit_case_scalars(content.compounds, content.trajectories)
    design = build_case_design(content.compounds, scalars)

    selections: list[SeedSelection] = []
    for k, seed in enumerate(seeds):
        selection = _run_one_seed(design, backend, k, seed)
        selections.append(selection)
        if seed_store is not None:
            seed_store.append(
                content.case_id,
                PerSeedStatusEntry(
                    seed=selection.seed,
                    status=selection.status,
                    selected_expression_string=(
                        selection.candidate.expression_string
                        if selection.candidate else None
                    ),
                    error_message=selection.error_message,
                ),
                content.content_hash,
            )

    # Section 8.2: any one seed's EXECUTION_FAILURE poisons the whole case.
    if any(s.status is SeedStatus.EXECUTION_FAILURE for s in selections):
        return _unevaluable_record(
            content, a1_status, selections, null_threshold, engine_versions,
            gate="no_candidate",
        )

    selection = group_and_select(selections)
    if selection.representative is None:
        return _unevaluable_record(
            content, a1_status, selections, null_threshold, engine_versions,
            gate="no_candidate",
        )

    representative = selection.representative
    inputs = FalsificationInputs(
        case_id=content.case_id,
        discovered_expression_string=representative.expression_string,
        complexity=representative.complexity,
        effective_support=extract_effective_support(representative.expression_string),
        target=scalars.g,
        compounds=content.compounds,
        trajectories=content.trajectories,
        null_threshold=null_threshold,
    )

    # ONE computation, shared by both consumers (A3.5 obligation 13).
    test_r2 = candidate_test_r2(inputs)
    ceiling = estimate_ceiling(content.compounds, scalars.g, test_r2)

    effective_support = inputs.effective_support

    def _candidate(results: Mapping[Any, Any]) -> StructuralCandidate:
        return StructuralCandidate(
            valid_r2=representative.valid_r2,
            complexity=representative.complexity,
            selection_fraction=selection.selection_fraction,
            invalid_fraction=representative.invalid_fraction,
            effective_support=effective_support,
            ceiling_fraction=ceiling.ceiling_fraction,
            ceiling_r2=ceiling.ceiling_r2,
            falsification_results=results,
            candidate_test_r2=test_r2,
        )

    # Phase A: Gates 1-7, using an empty Gate-8 mapping.  `check_gate8({})`
    # fails closed on the missing rungs, so this run either stops at an earlier
    # gate -- in which case the case never reaches Gate 8 and A3.5 section 6.9.4
    # says it produced no rung results -- or it stops at "falsification",
    # which is exactly the condition "reached Gate 8".  No new rule: the frozen
    # predicate's own gate order defines what reaching Gate 8 means.
    probe = case_acceptance(a1_status, _candidate({}), null_threshold)
    reached_gate8 = probe.result.gate_reached == "falsification"

    if not reached_gate8:
        acceptance = probe
        falsification = None
    else:
        # Phase B: only now is falsification run.  Section 6.1 binds F1 to
        # "every case reaching Gate 8" -- one full 30-seed re-execution each --
        # so running it for a case already rejected at Gate 2 would be both
        # wasted compute and a departure from the bound scope.
        falsification = run_falsification(inputs, reexecute or (lambda: None))
        acceptance = case_acceptance(
            a1_status, _candidate(falsification.hard), null_threshold
        )

    discovered_family = classify_discovered_family(representative.expression_string)
    truth_support = (
        truth_support_for_case(content.truth)
        if content.truth.symbolic_truth_kind == "defined"
        else frozenset(content.truth.active_variables or ())
    )
    support_status = classify_support(effective_support, truth_support)
    family_status = classify_family_match(
        discovered_family, content.truth.mathematical_family
    )

    _family, variant, _replicate = resolve_case_id(content.case_id)

    return CaseExecutionRecord(
        case_id=content.case_id,
        family_id=variant.code,
        partition_label=content.case_id.split("|")[1],
        truth_family=content.truth.mathematical_family,
        truth_support=truth_support,
        discovered_expression_string=representative.expression_string,
        effective_support=effective_support,
        support_status=support_status,
        family_status=family_status,
        discovered_family=discovered_family,
        g2_event=evaluate_g2_event(support_status, family_status),
        a1_case_adequacy_status=a1_status,
        valid_r2=representative.valid_r2,
        complexity=representative.complexity,
        selection_count=selection.selection_count,
        selection_denominator=selection.selection_denominator,
        invalid_fraction=representative.invalid_fraction,
        ceiling_r2=ceiling.ceiling_r2,
        ceiling_fraction=ceiling.ceiling_fraction,
        falsification_results=(falsification.hard if falsification else {}),
        acceptance_status=acceptance.result.status,
        acceptance_gate_reached=acceptance.result.gate_reached,
        per_seed_status=[
            PerSeedStatusEntry(
                seed=s.seed,
                status=s.status,
                selected_expression_string=(
                    s.candidate.expression_string if s.candidate else None
                ),
                error_message=s.error_message,
            )
            for s in selections
        ],
        seeds_used=[s.seed for s in selections],
        engine_versions=dict(engine_versions),
        null_threshold_digest=acceptance.null_threshold_digest,
        candidate_test_r2=test_r2,
        f9_stress_test_result=(
            falsification.f9_stress_test_result if falsification else None
        ),
        f9_stress_test_metric=(
            falsification.f9_stress_test_metric if falsification else None
        ),
    )


# -----------------------------------------------------------------------
# One partition
# -----------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_partition(
    partition: str,
    case_ids: Sequence[str],
    a1_status_by_case: Mapping[str, CaseAdequacyStatus],
    backend: CaseSearchBackend,
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    output_root: Path,
    run_commit: str,
) -> dict[str, Any]:
    """Execute the authorised partition's cases, resuming deterministically.

    Cases already carrying a written record are skipped, never re-executed
    (A3.5 section 12).  Provenance is appended to a separate, append-only file
    and never merged into the scientific record.
    """
    assert_partition_authorised(partition)
    output_root = Path(output_root)
    plan = resume_plan(output_root, case_ids)
    seed_store = CaseSeedRecordStore(output_root / "seed_records")

    executed: list[str] = []
    for case_id in plan.to_execute:
        started = _utc_now()
        content = materialize_case(case_id)
        try:
            a1_status = a1_status_by_case[case_id]
        except KeyError:
            raise ValueError(
                f"no A1 adequacy status supplied for {case_id}; RC5 consumes "
                f"A1's verdict and never derives one"
            ) from None
        record = execute_case(
            content=content,
            a1_status=a1_status,
            backend=backend,
            null_threshold=null_threshold,
            engine_versions=engine_versions,
            seed_store=seed_store,
        )
        digest = write_case_record(record, output_root)
        append_provenance(
            ProvenanceSidecar(
                case_id=case_id,
                scientific_digest=digest,
                started_utc=started,
                finished_utc=_utc_now(),
                wall_seconds=0.0,
                host_platform=platform.platform(),
                commit=run_commit,
            ),
            output_root,
        )
        executed.append(case_id)

    return {
        "partition": partition,
        "requested": list(plan.requested),
        "already_complete": list(plan.already_complete),
        "executed": executed,
    }
