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
from .registry import resolve_case_id
from .rc5_authorization import (
    AUTHORISED_PARTITIONS,
    PartitionNotAuthorised,
    assert_partition_authorised,
)
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
from .rc5_case_scoring import (
    case_acceptance,
    case_g3_event,
    execution_failure_poisoned_counts,
    score_case_secondaries,
    score_partition_g2,
    score_partition_g3,
)
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
    StoredSeedOutcome,
    append_provenance,
    resume_plan,
    write_case_record,
)
from .rc5_g1_bridge import score_case_g1, score_g1
from .structural_acceptance import (
    STABILITY_DENOMINATOR,
    AcceptanceResult,
    AcceptanceStatus,
    StructuralCandidate,
)

__all__ = [
    "AUTHORISED_PARTITIONS",
    "PartitionNotAuthorised",
    "ResumeRequiresFullReexecution",
    "assert_partition_authorised",
    "CaseContent",
    "materialize_case",
    "SeedSearchOutcome",
    "CaseSearchBackend",
    "PySRCaseBackend",
    "RunnerPreconditions",
    "check_preconditions",
    "CaseOutcome",
    "execute_case",
    "run_partition",
    "score_partition_endpoints",
]

class ResumeRequiresFullReexecution(RuntimeError):
    """A resumed case cannot be completed without recomputing a decided value."""


# -----------------------------------------------------------------------
# Case content
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseOutcome:
    """One case's record plus the per-case endpoint inputs it produced.

    A3.5 obligations 12 and 16 are scoring-pass obligations, and the endpoint
    denominators (G1's 164, G2's 144, G3's 36) are **held-out** counts, so the
    aggregate is computed by :func:`score_partition_endpoints` over a complete
    partition's records rather than per case.  What the runner owes each case is
    its *inputs* to those endpoints, computed here so they are never re-derived
    from a record later.
    """

    record: CaseExecutionRecord
    g1: Any | None
    g3_event: Any | None
    secondaries: Any | None


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
    except Exception as error:
        # Section 7.6: "Any exception during fit or equation retrieval ->
        # EXECUTION_FAILURE".  A malformed frame must poison its own seed, not
        # abort the whole partition with no record for the case at all.
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

    try:
        unparseable = extract_effective_support(expression) is None
        fraction = invalid_fraction(predictions, N_VALIDATION_COMPOUNDS)
    except Exception as error:
        return SeedSelection(
            k=k, seed=seed, status=SeedStatus.EXECUTION_FAILURE,
            error_message=f"{type(error).__name__}: {error}",
        )

    if unparseable:
        return SeedSelection(k=k, seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE)

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

def _selection_from_record(k: int, stored: StoredSeedOutcome) -> SeedSelection:
    """Rebuild a seed's outcome from its record, re-executing nothing.

    A recorded ``EXECUTION_FAILURE`` or ``COMPLETED_NO_CANDIDATE`` reaches the
    section 8.2 poisoning check exactly as it did on the original run.  A
    recorded candidate is restored from its own decided values -- the record
    carries them precisely so a resumed run never recomputes a number the
    original run already decided.
    """
    entry = stored.entry
    if entry.status is not SeedStatus.COMPLETED_WITH_CANDIDATES:
        return SeedSelection(
            k=k, seed=entry.seed, status=entry.status,
            error_message=entry.error_message,
        )
    if (
        entry.selected_expression_string is None
        or stored.complexity is None
        or stored.valid_r2 is None
        or stored.invalid_fraction is None
    ):
        raise ResumeRequiresFullReexecution(
            f"seed {entry.seed} recorded a retained candidate without its own "
            f"decided values; resuming would have to recompute a number the "
            f"original run already decided, which A3.5 sections 8.2 and 12 "
            f"forbid. Re-run this partition into a fresh output root."
        )
    return SeedSelection(
        k=k,
        seed=entry.seed,
        status=entry.status,
        candidate=RetainedCandidate(
            k=k,
            seed=entry.seed,
            expression_string=entry.selected_expression_string,
            complexity=int(stored.complexity),
            valid_r2=float(stored.valid_r2),
            invalid_fraction=float(stored.invalid_fraction),
            candidate_test_r2=float("-inf"),
        ),
    )


def _with_endpoints(
    record: CaseExecutionRecord,
    content: CaseContent,
    a1_status: CaseAdequacyStatus,
    scalars: Any,
    acceptance: Any,
) -> CaseOutcome:
    """Attach this case's per-case endpoint inputs to its record.

    Truth is read only HERE, strictly after ``record.acceptance_status``has been
    derived from the truth-blind path -- the ordering A3.5 requires of every
    post-hoc scoring endpoint.
    """
    verdict = acceptance or AcceptanceResult(
        record.acceptance_status, record.acceptance_gate_reached
    )
    # G3 applies only to the safety families; asking the frozen dispatcher
    # about any other variant is a contract error, not a missing event.
    _family, variant, _replicate = resolve_case_id(record.case_id)
    g3_event = (
        case_g3_event(record.case_id, verdict, record.effective_support)
        if "principal_structural_safety" in variant.endpoint_names
        else None
    )
    secondaries = score_case_secondaries(
        record.case_id, record.discovered_expression_string, content.truth, verdict
    )
    g1 = None
    if content.truth.g_by_compound:
        g1 = score_case_g1(
            record.case_id,
            a1_status,
            scalars.frozen_phi,
            content.compounds,
            content.trajectories,
            scalars.g,
            content.truth.g_by_compound,
        )
    return CaseOutcome(record=record, g1=g1, g3_event=g3_event, secondaries=secondaries)


def _unevaluable_record(
    content: CaseContent,
    a1_status: CaseAdequacyStatus,
    selections: Sequence[SeedSelection],
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    gate: str,
) -> CaseExecutionRecord:
    """Build the record for a case that produced no usable representative."""
    acceptance = case_acceptance(a1_status, None, null_threshold)
    _family, variant, _replicate = resolve_case_id(content.case_id)
    # Take the verdict from the frozen predicate, never from a hardcoded pair.
    # With `candidate=None` the predicate reports UNEVALUABLE at `no_candidate`
    # for a permitted A1 status, and REJECTED_A1_INADEQUATE at `a1_adequacy`
    # when A1 rejected -- and a record that hardcoded the former would then
    # contradict its own re-derivation and fail `verify_record_acceptance`.
    del gate
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
        # Imported, never restated: the frozen denominator lives in
        # structural_acceptance and a copy here could silently stop tracking it.
        selection_denominator=STABILITY_DENOMINATOR,
        invalid_fraction=1.0,
        ceiling_r2=float("-inf"),
        ceiling_fraction=float("-inf"),
        falsification_results={},
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
    )


def execute_case(
    content: CaseContent,
    a1_status: CaseAdequacyStatus,
    backend: CaseSearchBackend,
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    seed_store: CaseSeedRecordStore | None = None,
) -> CaseOutcome:
    """Execute one case end to end and return its record and endpoint inputs.

    ``a1_status`` is required: RC5 consumes A1's adequacy verdict and never
    derives one (see the module docstring).
    """
    seeds = case_search_seeds(content.case_id)

    scalars = fit_case_scalars(content.compounds, content.trajectories)
    design = build_case_design(content.compounds, scalars)

    # Seed-granular resume.  A recorded seed is ADOPTED, never re-executed:
    # A3.5 section 8.2 forbids "any retry that erases a prior failure", and
    # section 12 forbids re-running a seed whose result already exists.  Without
    # this load, an interruption partway through a case would re-run all 30
    # seeds and a transient EXECUTION_FAILURE -- exactly the kind that does not
    # recur -- would be silently superseded by a clean second result.
    recorded: Mapping[int, StoredSeedOutcome] = (
        seed_store.load(content.case_id, content.content_hash)
        if seed_store is not None
        else {}
    )

    selections: list[SeedSelection] = []
    for k, seed in enumerate(seeds):
        previous = recorded.get(seed)
        if previous is not None:
            selections.append(_selection_from_record(k, previous))
            continue
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
                complexity=(
                    selection.candidate.complexity if selection.candidate else None
                ),
                valid_r2=(
                    selection.candidate.valid_r2 if selection.candidate else None
                ),
                invalid_fraction=(
                    selection.candidate.invalid_fraction
                    if selection.candidate else None
                ),
            )

    # Section 8.2: any one seed's EXECUTION_FAILURE poisons the whole case.
    if any(s.status is SeedStatus.EXECUTION_FAILURE for s in selections):
        record = _unevaluable_record(
            content, a1_status, selections, null_threshold, engine_versions,
            gate="no_candidate",
        )
        return _with_endpoints(record, content, a1_status, scalars, None)

    selection = group_and_select(selections)
    if selection.representative is None:
        record = _unevaluable_record(
            content, a1_status, selections, null_threshold, engine_versions,
            gate="no_candidate",
        )
        return _with_endpoints(record, content, a1_status, scalars, None)

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
        # A3.5 section 6.1: F1 re-executes the case pipeline from byte-identical
        # inputs under the byte-identical 30 already-derived seeds, with the
        # identity perturbation.  Universal scope, no sampling -- the one full
        # 30-seed re-execution per Gate-8-reaching case is "a consequence of
        # frozen contract, not an open decision".  The replay writes nothing to
        # the seed store: it is a determinism probe, not a second result.
        def _reexecute() -> str | None:
            replayed = group_and_select(
                [_run_one_seed(design, backend, k, seed)
                 for k, seed in enumerate(seeds)]
            )
            representative = replayed.representative
            return None if representative is None else representative.expression_string

        falsification = run_falsification(inputs, _reexecute)
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

    record = CaseExecutionRecord(
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
        winning_class_distinct_expression_strings=selection.distinct_expression_strings,
        winning_class_distinct_coefficient_vectors=selection.distinct_coefficient_vectors,
    )
    return _with_endpoints(record, content, a1_status, scalars, acceptance.result)


# -----------------------------------------------------------------------
# One partition
# -----------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_partition(
    partition: str,
    plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    a1_status_by_case: Mapping[str, CaseAdequacyStatus],
    backend: CaseSearchBackend,
    null_threshold: Mapping[int, float],
    engine_versions: Mapping[str, str],
    artifact_dir: Path,
    output_root: Path,
    lock: ImplementationLock,
    run_commit: str,
) -> dict[str, Any]:
    """Execute the authorised partition's cases, resuming deterministically.

    The preconditions are **not** optional decoration: the global plan's own
    digest, the partition manifest's pure-derivation property, the artifact
    hash inventory and preflight are all verified here, before the first case
    is materialised.  The case list comes from the *verified manifest*, never
    from a caller-supplied sequence, so a run cannot quietly execute a
    different population than the one the manifest committed to.

    Cases already carrying a written record are skipped, never re-executed
    (A3.5 section 12).  Provenance is appended to a separate, append-only file
    and never merged into the scientific record.
    """
    preconditions = check_preconditions(
        partition, Path(artifact_dir), lock, plan, manifest
    )
    output_root = Path(output_root)
    case_ids = list(manifest["science"]["case_ids"])
    resume = resume_plan(output_root, case_ids)
    # The store carries the verified plan digest, so a seed record written under
    # a different global plan is refused rather than adopted.
    seed_store = CaseSeedRecordStore(
        output_root / "seed_records", plan_digest=str(plan["digest"])
    )

    executed: list[str] = []
    outcomes: list[CaseOutcome] = []
    for case_id in resume.to_execute:
        started = _utc_now()
        content = materialize_case(case_id)
        try:
            a1_status = a1_status_by_case[case_id]
        except KeyError:
            raise ValueError(
                f"no A1 adequacy status supplied for {case_id}; RC5 consumes "
                f"A1's verdict and never derives one"
            ) from None
        outcome = execute_case(
            content=content,
            a1_status=a1_status,
            backend=backend,
            null_threshold=null_threshold,
            engine_versions=engine_versions,
            seed_store=seed_store,
        )
        record = outcome.record
        outcomes.append(outcome)
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
        "global_plan_digest": plan["digest"],
        "manifest_digest": preconditions.manifest_verification["manifest_digest"],
        "requested": list(resume.requested),
        "already_complete": list(resume.already_complete),
        "executed": executed,
        # A3.5 obligation 16: the poisoned count is DISCLOSED, never subtracted
        # from any denominator.
        "execution_failure_poisoned": execution_failure_poisoned_counts(
            [o.record for o in outcomes]
        ).to_payload(),
    }


# -----------------------------------------------------------------------
# The partition-level scoring pass
# -----------------------------------------------------------------------

def score_partition_endpoints(
    outcomes: Sequence[CaseOutcome],
) -> dict[str, Any]:
    """Aggregate the primary endpoints over a COMPLETE partition's outcomes.

    Separate from execution on purpose.  Every endpoint denominator is a
    **held-out** count computed from the frozen registry -- G1's 164, G2's 144,
    G3's 36 -- so an aggregate is only meaningful once that partition's whole
    population exists.  Running it over a partial set would silently change the
    denominator, which is exactly what A3.5 obligation 12's length assertion
    exists to prevent.

    G3 is scored through ``g3_contract`` alone (section 8.3); the permissive
    ``analysis.classify_negative_control`` path is not reachable from here.
    Obligation 16's poisoned counts are returned alongside, disclosed rather
    than deducted.
    """
    records = [outcome.record for outcome in outcomes]
    disclosure = execution_failure_poisoned_counts(records)

    g2_events = [record.g2_event for record in records]
    g3_events = [o.g3_event for o in outcomes if o.g3_event is not None]
    g1_cases = [o.g1 for o in outcomes if o.g1 is not None]

    return {
        "g1": score_g1(g1_cases),
        "g2": score_partition_g2(g2_events),
        "g3": score_partition_g3(g3_events),
        "execution_failure_poisoned": disclosure.to_payload(),
    }
