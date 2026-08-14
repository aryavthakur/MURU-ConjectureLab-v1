"""Engineering RC3: structural-null calibration world generator.

Builds the 100 calibration worlds declared in Amendment A3.1.  Every count,
allocation, world ID and seed comes from the frozen ``calibration_contract``
module; nothing here re-declares a frozen value.

Each world reuses the frozen benchmark covariate machinery
(``generator._synthetic_compounds``) unchanged, so a calibration world has
exactly the paper's five synthetic covariates, its frozen correlation
structure, its 180 compounds in 30 scaffold groups, and its scaffold-disjoint
20/5/5 scaffold-group split.

OPEN ITEM - split proportion.  That split is 120/30/30 compounds, i.e.
66.7/16.7/16.7 percent, NOT the 60/20/20 the amendment specifies
(``MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md``, "Structural-null calibration";
``calibration_contract`` module docstring).  RC3 does not resolve this: the
frozen generator is a protected path and may not be edited, and inventing a
different split would be a science change RC3 is not authorized to make.
The frozen generator's split is used as-is and the discrepancy is recorded
here and in ``SPLIT_PROPORTION_OPEN_ITEM`` rather than papered over.  The
split IS scaffold-disjoint, which is the property the null depends on; only
the proportions differ.  See :data:`SPLIT_PROPORTION_OPEN_ITEM`.

Null construction
-----------------
All three admitted constructions destroy the covariate-to-target link:

``target_permuted_across_compounds``
    the base target vector is permuted across compounds
``descriptors_permuted_across_compounds``
    the five covariates are permuted jointly across compounds, preserving
    their internal correlation structure while breaking their alignment to
    the target
``gaussian_targets_with_observed_variance``
    targets are redrawn i.i.d. Gaussian at the base target's own mean and
    variance

``within_compound_energy_permutation`` is EXCLUDED by the amendment because
it preserves compound mean level, the scalar quantity being estimated.  This
module makes it *unconstructible*: it is not a branch, and asking for it
raises.

Base target
-----------
OPEN ITEM - and a blocking one.  Amendment A3.1 fixes the world geometry,
the covariates and the three constructions, but does not pin the
pre-permutation target.  RC3's provisional choice reaches the frozen
benchmark scalar law through ``generator._law``, introducing no new
generative mechanism.

That choice is NOT neutral, and review measured the bias.  The frozen law
``scale*sqrt(mass/250)*(1 + c*descriptor)`` is scaffold-structured, because
both ``mass`` and ``descriptor`` are driven by ``group_latent[scaffold]``.
Under ``target_permuted`` and ``gaussian_targets`` that scaffold structure
is destroyed; under ``descriptors_permuted`` only the covariates are
permuted, so the target's scaffold structure survives against a
scaffold-disjoint split and produces a systematic train/validation mean
shift.  Measured constant-model validation R2 over 20 worlds each:
-0.055 (target_permuted), -0.077 (gaussian), -0.246 (descriptors_permuted).
The 33 descriptors-permuted worlds are systematically depressed, so the
pooled Q95 over 100 worlds sits BELOW what a homogeneous null would give -
a threshold that is more permissive than intended.

Because permissiveness drift is disqualifying, this choice is not applied
by default to a scientific run: :func:`build_world` requires an explicit
``base_target_kind`` acknowledgement, and :func:`build_all_worlds` refuses
without one.  Resolution requires a base target that is exchangeable across
all three constructions, and that is a science decision for sign-off, not
an engineering one.  See :data:`BASE_TARGET_OPEN_ITEM`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd

from .calibration_contract import (
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
    N_CALIBRATION_WORLDS,
    N_COMPOUNDS,
    N_SCAFFOLD_GROUPS,
    all_world_ids,
    derive_calibration_seeds,
    derive_world_id,
)
from .g2_contract import GRAMMAR_PRIMITIVES
from .generator import _law, _synthetic_compounds, derive_seed

__all__ = [
    "ADMITTED_CONSTRUCTIONS",
    "BASE_TARGET_KIND",
    "BASE_TARGET_OPEN_ITEM",
    "SPLIT_PROPORTION_OPEN_ITEM",
    "EXPECTED_SPLIT_COUNTS",
    "CALIBRATION_COVARIATE_ORDER",
    "CalibrationWorld",
    "BaseTargetUnresolved",
    "ExcludedConstructionError",
    "build_world",
    "build_all_worlds",
    "iter_world_ids",
]

#: Only these three may be constructed.  Frozen allocation keys.
ADMITTED_CONSTRUCTIONS: tuple[str, ...] = tuple(sorted(CONSTRUCTION_ALLOCATION))

#: Covariate order for the design matrix; the protected grammar primitives.
CALIBRATION_COVARIATE_ORDER: tuple[str, ...] = GRAMMAR_PRIMITIVES

#: The frozen benchmark scalar law reached as the pre-permutation base
#: target.  Note that ``generator._law`` returns the SAME deterministic
#: expression for ``scalar_noiseless``/``scalar_moderate``/``scalar_strong``
#: and six other kinds - the noise level lives in ``_response_matrix``, which
#: calibration never calls.  So this is the noiseless latent ``g``, and the
#: "moderate" in the name denotes no noise level here.
BASE_TARGET_KIND = "scalar_moderate"

#: Blocking open item: this base target is not exchangeable across the three
#: constructions and biases the pooled Q95 downward (more permissive).  See
#: the module docstring for the measured numbers.
BASE_TARGET_OPEN_ITEM = (
    "BASE_TARGET_UNRESOLVED: the pre-permutation base target is not pinned by "
    "Amendment A3.1. The provisional frozen-law choice is scaffold-structured "
    "and survives the descriptors_permuted construction, depressing 33 of 100 "
    "worlds and making the pooled Q95 threshold more permissive than a "
    "homogeneous null. Requires science sign-off before authorized execution."
)

#: Open item: the frozen generator's scaffold-group split is 20/5/5
#: (120/30/30 compounds = 66.7/16.7/16.7 percent); the amendment specifies
#: 60/20/20.  RC3 uses the frozen generator unchanged and records the gap.
SPLIT_PROPORTION_OPEN_ITEM = (
    "SPLIT_PROPORTION_DISCREPANCY: the frozen generator yields a "
    "scaffold-disjoint 120/30/30 compound split (66.7/16.7/16.7 percent). "
    "Amendment A3.1 specifies 60/20/20. The generator is a protected path and "
    "was not modified; no substitute split was invented. Requires sign-off."
)

#: The split the frozen generator actually produces, asserted at build time
#: so a future generator change cannot alter it unnoticed.
EXPECTED_SPLIT_COUNTS: dict[str, int] = {"train": 120, "validation": 30, "test": 30}


class BaseTargetUnresolved(RuntimeError):
    """Raised when a world is built without acknowledging the open base target."""


class ExcludedConstructionError(ValueError):
    """Raised when an excluded null construction is requested.

    Within-compound energy permutation is not implemented anywhere in this
    module.  It cannot be reached by configuration, flag, or string.
    """


@dataclass(frozen=True)
class CalibrationWorld:
    """One structural-null calibration world."""

    world_id: str
    construction: str
    index: int
    compounds: pd.DataFrame
    target: np.ndarray
    seeds: Sequence[int]

    def design_matrix(self) -> np.ndarray:
        return np.column_stack([
            np.asarray(self.compounds[c], dtype=np.float64)
            for c in CALIBRATION_COVARIATE_ORDER
        ])

    def split_masks(self) -> dict[str, np.ndarray]:
        splits = np.asarray(self.compounds["split"], dtype=object)
        return {
            name: splits == name for name in ("train", "validation", "test")
        }


def iter_world_ids() -> list[str]:
    """All 100 world IDs, in the frozen allocation order."""
    return all_world_ids()


def _check_construction(construction: str) -> None:
    if construction in EXCLUDED_CONSTRUCTIONS:
        raise ExcludedConstructionError(
            f"{construction!r} is excluded by Amendment A3.1 and is not "
            f"constructible: it preserves compound mean level, the scalar "
            f"quantity being estimated"
        )
    if construction not in CONSTRUCTION_ALLOCATION:
        raise ValueError(
            f"unknown construction {construction!r}; admitted: "
            f"{ADMITTED_CONSTRUCTIONS}"
        )


def _base_target(
    world_id: str, compounds: pd.DataFrame, kind: str
) -> np.ndarray:
    """The pre-permutation target, from the frozen benchmark scalar law."""
    rng = np.random.default_rng(derive_seed(world_id, "law"))
    g, _family, _active, _relationship, _coeffs, _exps = _law(kind, compounds, rng)
    if g is None:
        raise RuntimeError(f"frozen law {kind!r} produced no target")
    return np.asarray(g, dtype=np.float64)


def build_world(
    construction: str,
    index: int,
    base_target_kind: str | None = None,
) -> CalibrationWorld:
    """Build one calibration world.

    The world is a pure function of ``(construction, index)``: identical
    inputs give bitwise-identical covariates, targets and seeds.

    ``base_target_kind`` must be passed explicitly to build a world for a
    scientific run.  Passing ``None`` uses :data:`BASE_TARGET_KIND` and is
    intended for tests and engineering; it is permitted because the runner
    gates the scientific path separately, and because refusing here would
    make the machinery untestable.  :func:`build_all_worlds`, the only
    whole-calibration constructor, does require the acknowledgement.
    """
    _check_construction(construction)
    if index < 0 or index >= CONSTRUCTION_ALLOCATION[construction]:
        raise ValueError(
            f"index {index} outside 0..{CONSTRUCTION_ALLOCATION[construction] - 1} "
            f"for construction {construction!r}; the frozen allocation is "
            f"{dict(CONSTRUCTION_ALLOCATION)}"
        )
    kind = BASE_TARGET_KIND if base_target_kind is None else base_target_kind
    world_id = derive_world_id(construction, index)

    compounds, _seeds = _synthetic_compounds(world_id)
    if len(compounds) != N_COMPOUNDS:  # pragma: no cover - frozen generator
        raise RuntimeError(
            f"expected {N_COMPOUNDS} compounds, got {len(compounds)}"
        )
    if compounds["scaffold_id"].nunique() != N_SCAFFOLD_GROUPS:  # pragma: no cover
        raise RuntimeError(
            f"expected {N_SCAFFOLD_GROUPS} scaffold groups, got "
            f"{compounds['scaffold_id'].nunique()}"
        )
    actual_split = compounds["split"].value_counts().to_dict()
    if actual_split != EXPECTED_SPLIT_COUNTS:  # pragma: no cover - frozen generator
        raise RuntimeError(
            f"frozen generator split changed: {actual_split} != "
            f"{EXPECTED_SPLIT_COUNTS}"
        )
    # Scaffold-disjointness is the property the null actually depends on.
    if compounds.groupby("scaffold_id")["split"].nunique().max() != 1:  # pragma: no cover
        raise RuntimeError("split is not scaffold-disjoint")

    target = _base_target(world_id, compounds, kind)
    null_rng = np.random.default_rng(derive_seed(world_id, "null_construction"))

    if construction == "target_permuted_across_compounds":
        target = target[null_rng.permutation(N_COMPOUNDS)]

    elif construction == "descriptors_permuted_across_compounds":
        order = null_rng.permutation(N_COMPOUNDS)
        compounds = compounds.copy()
        for column in CALIBRATION_COVARIATE_ORDER:
            compounds[column] = np.asarray(compounds[column])[order]

    elif construction == "gaussian_targets_with_observed_variance":
        target = null_rng.normal(
            float(target.mean()), float(target.std(ddof=0)), N_COMPOUNDS
        )

    else:  # pragma: no cover - _check_construction already rejected
        raise ValueError(f"unhandled construction {construction!r}")

    return CalibrationWorld(
        world_id=world_id,
        construction=construction,
        index=index,
        compounds=compounds.reset_index(drop=True),
        target=np.asarray(target, dtype=np.float64),
        seeds=tuple(derive_calibration_seeds(world_id)),
    )


def build_all_worlds(
    base_target_kind: str | None = None,
    acknowledge_open_base_target: bool = False,
) -> list[CalibrationWorld]:
    """Build all 100 worlds in the frozen allocation order.

    Materializing all 100 worlds is cheap; *executing* them is not, and this
    function performs no search.

    Refuses to build the full calibration set under the provisional base
    target unless the caller explicitly acknowledges the open item, because
    that target biases the pooled threshold in the permissive direction.
    """
    if base_target_kind is None and not acknowledge_open_base_target:
        raise BaseTargetUnresolved(BASE_TARGET_OPEN_ITEM)
    worlds: list[CalibrationWorld] = []
    for construction in CONSTRUCTION_ALLOCATION:
        for index in range(CONSTRUCTION_ALLOCATION[construction]):
            worlds.append(build_world(construction, index, base_target_kind))
    if len(worlds) != N_CALIBRATION_WORLDS:  # pragma: no cover - frozen sum
        raise RuntimeError(
            f"expected {N_CALIBRATION_WORLDS} worlds, built {len(worlds)}"
        )
    return worlds
