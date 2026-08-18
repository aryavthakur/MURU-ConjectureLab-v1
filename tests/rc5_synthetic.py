"""Shared synthetic fixtures for the RC5 runner tests.

**Dedicated synthetic content only.**  Nothing here calls ``generate_case`` or
reads any benchmark artifact, so no partition is materialised, the development
engineering-fixture footprint does not grow, and A3.5 section 2's "no
challenge-partition case has been generated" attestation is unaffected.

The case IDs used are registry-valid strings so ``resolve_case_id`` resolves a
family and variant, which is metadata only -- section 8.4 is explicit that
naming a case ID does not open its partition.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from muru.paper_benchmark.registry import ENERGY_GRID
from muru.paper_benchmark.rc5_adapter import CaseDesign
from muru.paper_benchmark.rc5_runner import CaseContent, SeedSearchOutcome
from muru.paper_benchmark.truth import TruthRecord

N_SCAFFOLDS = 30
PER_SCAFFOLD = 6
N = N_SCAFFOLDS * PER_SCAFFOLD
MU_INF, PHI_P = 0.22, 1.45

NULL_THRESHOLD = {c: 0.10 for c in range(1, 21)}
ENGINE_VERSIONS = {"pysr": "1.5.10", "scikit-learn": "1.9.0"}


def _splits() -> list[str]:
    by_group = ["train"] * 20 + ["validation"] * 5 + ["test"] * 5
    return [by_group[i // PER_SCAFFOLD] for i in range(N)]


def synthetic_content(case_id: str, seed: int = 3) -> CaseContent:
    """A synthetic case obeying the frozen M0 law, with a mass-driven target.

    The content is a pure function of ``seed`` -- **not** of ``case_id`` -- so
    two differently-labelled cases can be given byte-identical inputs.
    """
    rng = np.random.default_rng(seed)
    mass = rng.uniform(200.0, 400.0, N)
    g = np.clip(1.0 + 0.004 * (mass - 300.0), 0.4, 2.5)

    compounds = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N)],
            "scaffold_id": [f"S{i // PER_SCAFFOLD:02d}" for i in range(N)],
            "split": _splits(),
            "mass": mass,
            "descriptor": rng.uniform(0, 1, N),
            "descriptor2": rng.uniform(0, 1, N),
            "distractor": rng.normal(0, 1, N),
            "correlated_distractor": rng.normal(0, 1, N),
        }
    )
    energies = np.asarray(ENERGY_GRID, dtype=float)
    u = (energies[None, :] / 45.0) / g[:, None]
    mu = MU_INF + (1 - MU_INF) * np.exp(-(u**PHI_P))
    trajectories = pd.DataFrame(
        [
            {"compound_id": c, "energy": float(e), "mu": float(mu[i, j])}
            for i, c in enumerate(compounds.compound_id)
            for j, e in enumerate(energies)
        ]
    )
    truth = TruthRecord(
        case_id=case_id,
        partition=case_id.split("|")[1],
        family="F01",
        variant="F01",
        seeds={"compounds": 1, "law": 2, "response": 3},
        phi={"family": "stretched_exponential", "mu_inf": MU_INF, "phi_p": PHI_P},
        g_definition="sqrt(mass) * (1 + coefficient * descriptor)",
        g_by_compound={c: float(v) for c, v in zip(compounds.compound_id, g)},
        descriptor_relationship="sqrt(mass) * (1 + coefficient * descriptor)",
        active_variables=["mass"],
        mathematical_family="mass_power",
        coefficients={"scale": 1.0},
        exponents={"mass": 0.5},
        noise={"mechanism": "additive_gaussian", "sd": 0.0},
        missingness={"mechanism": "none", "rate": 0.0},
        scalar_truth_defined=True,
        m0_adequacy_truth="M0",
        symbolic_truth_kind="mass_only",
        applicable_endpoints=["scalar_competence"],
        expected_behavior="recover scalar",
    )
    return CaseContent(
        case_id=case_id,
        compounds=compounds,
        trajectories=trajectories,
        truth=truth,
        content_hash="s" * 64,
    )


# -----------------------------------------------------------------------
# A stub engine
# -----------------------------------------------------------------------

@dataclass
class _StubModel:
    """Predicts a scaled copy of one design column, chosen by row position."""

    columns: tuple[int, ...]
    scales: tuple[float, ...]

    def predict(self, design: np.ndarray, index: int) -> np.ndarray:
        column = self.columns[index]
        return np.asarray(design[:, column], dtype=np.float64) * self.scales[index]


class StubBackend:
    """A deterministic engine stand-in.

    Its output is a pure function of the **design**, never of the seed, so a
    test can hold the science fixed while the seed values legitimately differ
    between two case identities.  ``seed_behaviour`` optionally overrides one
    seed's outcome so degenerate paths can be exercised.
    """

    #: The front is A3.5 section 7.1's own worked example: ``argmax(score)``
    #: selects **complexity 4**, not 13.  The emitted string at that row is
    #: ``"mass"`` so the string and the stub model agree about what was found.
    def __init__(
        self,
        expressions: tuple[str, ...] = ("descriptor2", "mass", "mass * descriptor"),
        complexities: tuple[int, ...] = (1, 4, 13),
        losses: tuple[float, ...] = (1.0, 0.2, 0.19),
        columns: tuple[int, ...] = (2, 0, 0),
        scales: tuple[float, ...] = (1.0, 0.004, 0.004),
        seed_behaviour: dict[int, str] | None = None,
    ):
        self.expressions = expressions
        self.complexities = complexities
        self.losses = losses
        self.columns = columns
        self.scales = scales
        self.seed_behaviour = seed_behaviour or {}
        self.seen: list[int] = []

    def _frame(self) -> pd.DataFrame:
        scores = []
        last_loss = None
        last_complexity = 0
        for complexity, loss in zip(self.complexities, self.losses):
            if last_loss is None:
                scores.append(0.0)
            elif loss > 0.0:
                scores.append(-np.log(loss / last_loss) / (complexity - last_complexity))
            else:
                scores.append(np.inf)
            last_loss, last_complexity = loss, complexity
        return pd.DataFrame(
            {
                "complexity": list(self.complexities),
                "loss": list(self.losses),
                "score": scores,
                "equation": list(self.expressions),
            },
            index=[100 + 7 * i for i in range(len(self.expressions))],
        )

    def search(self, design: CaseDesign, seed: int) -> SeedSearchOutcome:
        self.seen.append(seed)
        behaviour = self.seed_behaviour.get(seed)
        if behaviour == "raise":
            raise RuntimeError("stub engine failure")
        if behaviour == "empty":
            return SeedSearchOutcome(equations=self._frame().iloc[0:0], model=None)
        if behaviour == "no_score":
            return SeedSearchOutcome(
                equations=self._frame().drop(columns=["score"]),
                model=_StubModel(self.columns, self.scales),
            )
        return SeedSearchOutcome(
            equations=self._frame(),
            model=_StubModel(self.columns, self.scales),
        )
