"""Zero-search recovery of the exact G1 observables for the Held-out partition.

Rescue requirement 9: *"Persist G1 observables … Recompute G1 for Held-out
without any search."*

The sealed record schema ``muru-rc5-case-record-2.0.0`` persists no G1
observable — no ``g_spearman``, no ``trajectory_mae``, no
``per_energy_mean_mae``.  That is a **record-schema gap, not an execution
defect**: A3.5 §8.2 records that G1's inputs are search-independent, so every
one of them is recomputable from frozen case content and the frozen
training-only ``Phi``.

**No search is rerun and PySR is never imported.**  The recomputation path is

    materialize_case  ->  fit_case_scalars  ->  score_case_g1  ->  score_g1

and none of those four touches the symbolic-regression engine.  The 7,200
sealed searches are neither consulted nor repeated.

## Content identity

A recomputation is only as good as its claim to be operating on the *same*
case content the run used.  That claim is not assumed here, it is tested:
``run_case_adequacy`` is itself search-independent, so re-deriving each case's
A1 adequacy status from the regenerated content and comparing it against the
sealed ``a1_case_adequacy_status`` is a direct, frozen-code test of content
identity.  A regenerated case that differed from the executed one in any way
A1 can see would show up as a mismatch.

## What this cannot change

``scalar_competent`` is a conjunction whose third term is ``m0_accepted``, and
``m0_accepted`` is read from the sealed A1 status.  The exact count is
therefore bounded above by the sealed ``M0_NOT_REJECTED`` count no matter what
the two recovered observables turn out to be.  Recovery sharpens the point
estimate; it cannot move the gate verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .adequacy import CaseAdequacyStatus
from .heldout_endpoint_populations import build_endpoint_population
from .rc5_adequacy import run_case_adequacy
from .rc5_estimate import fit_case_scalars
from .rc5_g1_bridge import CaseG1, score_case_g1
from .rc5_record_payload import load_sealed_record
from .rc5_runner import materialize_case

__all__ = [
    "ContentIdentityFailure",
    "G1RecoveryRecord",
    "G1Recovery",
    "recover_g1_observables",
]


class ContentIdentityFailure(RuntimeError):
    """Regenerated case content does not reproduce the sealed A1 verdict."""


@dataclass(frozen=True)
class G1RecoveryRecord:
    """One case's recovered G1 observables and its identity evidence."""

    case_id: str
    content_hash: str
    sealed_a1_status: str
    recomputed_a1_status: str
    outcome: CaseG1

    @property
    def content_identity_ok(self) -> bool:
        return self.sealed_a1_status == self.recomputed_a1_status

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "content_hash": self.content_hash,
            "sealed_a1_status": self.sealed_a1_status,
            "recomputed_a1_status": self.recomputed_a1_status,
            "content_identity_ok": self.content_identity_ok,
            "g_spearman": self.outcome.g_spearman,
            "trajectory_mae": self.outcome.trajectory_mae,
            "per_energy_mean_mae": self.outcome.per_energy_mean_mae,
            "m0_accepted": self.outcome.m0_accepted,
            "spearman_pass": self.outcome.spearman_pass,
            "trajectory_pass": self.outcome.trajectory_pass,
            "contract_failure": self.outcome.contract_failure,
            "scalar_competent": self.outcome.scalar_competent,
        }


@dataclass(frozen=True)
class G1Recovery:
    """The recovered G1 population, ready for ``score_g1``."""

    records: tuple[G1RecoveryRecord, ...]
    searches_run: int = 0
    pysr_imported: bool = False

    @property
    def outcomes(self) -> Mapping[str, CaseG1]:
        return {record.case_id: record.outcome for record in self.records}

    def to_dict(self) -> dict[str, Any]:
        competent = [r for r in self.records if r.outcome.scalar_competent]
        return {
            "method": (
                "materialize_case -> fit_case_scalars -> score_case_g1; "
                "search-independent per A3.5 §8.2"
            ),
            "searches_run": self.searches_run,
            "pysr_imported": self.pysr_imported,
            "cases": len(self.records),
            "content_identity_checked": len(self.records),
            "content_identity_mismatches": sum(
                1 for r in self.records if not r.content_identity_ok
            ),
            "competent": len(competent),
            "conjunct_failures": {
                "spearman_only": sum(
                    1 for r in self.records
                    if not r.outcome.spearman_pass
                    and r.outcome.trajectory_pass and r.outcome.m0_accepted
                ),
                "trajectory_only": sum(
                    1 for r in self.records
                    if not r.outcome.trajectory_pass
                    and r.outcome.spearman_pass and r.outcome.m0_accepted
                ),
                "m0_only": sum(
                    1 for r in self.records
                    if not r.outcome.m0_accepted
                    and r.outcome.spearman_pass and r.outcome.trajectory_pass
                ),
                "contract_failure": sum(
                    1 for r in self.records if r.outcome.contract_failure
                ),
            },
            "per_case": [r.to_dict() for r in self.records],
        }


def recover_g1_observables(
    results_root: Path,
    progress: Any = None,
) -> G1Recovery:
    """Recover exact G1 observables for all 164 G1-applicable Held-out cases.

    Reads the sealed records only for ``a1_case_adequacy_status``; every other
    quantity is regenerated from frozen deterministic inputs.
    """
    import sys

    population = build_endpoint_population("scalar_competence")
    records_dir = Path(results_root) / "records"

    recovered: list[G1RecoveryRecord] = []
    for index, case_id in enumerate(population.case_ids, start=1):
        sealed = load_sealed_record(records_dir, case_id)
        sealed_status = CaseAdequacyStatus(sealed.require("a1_case_adequacy_status"))

        content = materialize_case(case_id)
        scalars = fit_case_scalars(content.compounds, content.trajectories)

        # Content-identity test: A1 is search-independent, so it must
        # reproduce the sealed verdict from the regenerated content.
        recomputed = run_case_adequacy(
            case_id, content.compounds, content.trajectories, scalars.frozen_phi
        )
        recomputed_status = recomputed.status

        truth_g = content.truth.g_by_compound
        if not truth_g:
            raise ContentIdentityFailure(
                f"{case_id} carries the scalar_competence endpoint but its "
                f"generated truth has no g_by_compound"
            )

        outcome = score_case_g1(
            case_id,
            sealed_status,
            scalars.frozen_phi,
            content.compounds,
            content.trajectories,
            scalars.g,
            truth_g,
        )
        recovered.append(
            G1RecoveryRecord(
                case_id=case_id,
                content_hash=content.content_hash,
                sealed_a1_status=sealed_status.value,
                recomputed_a1_status=CaseAdequacyStatus(recomputed_status).value,
                outcome=outcome,
            )
        )
        if progress is not None:
            progress(index, len(population.case_ids), case_id)

    mismatches = [r.case_id for r in recovered if not r.content_identity_ok]
    if mismatches:
        raise ContentIdentityFailure(
            f"{len(mismatches)} regenerated cases do not reproduce their sealed "
            f"A1 verdict; the recomputation is not operating on the executed "
            f"content: {mismatches[:5]}"
        )

    return G1Recovery(
        records=tuple(recovered),
        searches_run=0,
        pysr_imported="pysr" in sys.modules,
    )
