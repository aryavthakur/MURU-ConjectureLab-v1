"""Engineering RC3.1: structural-null calibration world generator, under A3.2.

Builds the 100 calibration worlds declared in Amendment A3.1, with the two
corrections Amendment A3.2 makes to the null design.  Every count,
allocation, world ID and search seed still comes from the frozen
``calibration_contract`` module; nothing here re-declares a frozen value.

Each world reuses the frozen benchmark covariate machinery
(``generator._synthetic_compounds``) unchanged, so a calibration world has
exactly the paper's five synthetic covariates, its frozen correlation
structure, and its 180 compounds in 30 scaffold groups of 6.

A3.2 Decision 1 - base target
-----------------------------
A3.1 fixes the world geometry, the covariates and the three constructions,
but does not pin the pre-permutation target.  Using the frozen synthetic
law's target vector directly left it *scaffold-structured*, because the law
``scale*sqrt(mass/250)*(1 + c*descriptor)`` depends on ``mass`` and
``descriptor``, both driven by ``group_latent[scaffold]``.

That structure survives ``descriptors_permuted_across_compounds``, which
permutes only the covariates.  Against a scaffold-disjoint split it produced
a systematic train/validation mean shift, making one of three nominal null
families non-null (measured constant-model validation R2: -0.055
target_permuted, -0.077 gaussian, **-0.246** descriptors_permuted) and
biasing the pooled Q95 threshold in the permissive direction.

A3.2 rejects that base target.  The corrected construction, implemented in
:func:`_base_target`:

1. generate the frozen-law target vector, law unchanged
2. globally permute its values across all 180 compound identities, under a
   dedicated world-specific seed, BEFORE any null-family transformation and
   BEFORE any partition use
3. only then apply the frozen 34/33/33 null-family transformation

The permutation is a true permutation: the multiset of target values is
preserved exactly, so the marginal distribution is the frozen law's, value
for value.  What is destroyed is the *assignment* of those values to
compound, scaffold, mass and descriptor.

Residual finite-sample correlation arising by chance is permitted and is
never tuned away.  One deterministic permutation per world, no rejection
sampling, no reshuffling until a correlation looks small.

A3.2 Decision 2 - scaffold split
--------------------------------
A3.1 specifies a scaffold-disjoint 60/20/20 split.  The frozen generator's
own ``split`` column is 20/5/5 scaffold groups (120/30/30 compounds,
66.7/16.7/16.7 percent).  A3.2 holds 60/20/20 authoritative and does NOT
amend the contract to match the generator.

RC3.1 therefore ignores the frozen generator's ``split`` column for
calibration worlds and assigns its own 18/6/6 scaffold split
(108/36/36 compounds) in :func:`assign_calibration_split`, from a dedicated
seed, consulting nothing but scaffold identity.  The frozen generator is not
edited; it remains byte-identical.  This split applies to calibration worlds
only and changes no benchmark case partition.

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

Seed independence
-----------------
Five distinct namespaces, all through the canonical
``generator.derive_seed``, none derived from another:

===========================  ==================================
purpose                      namespace
===========================  ==================================
base-target permutation      ``PB|NCAL|<world_id>|BASE_TARGET``
calibration scaffold split   ``PB|NCAL|<world_id>|SPLIT``
null-family transformation   ``PB|NCAL|<world_id>|null_construction``
frozen-law draw              ``PB|NCAL|<world_id>|law``
PySR search seeds            ``calibration_contract.derive_calibration_seeds``
===========================  ==================================
"""
from __future__ import annotations

import hashlib
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
    "BASE_TARGET_ALGORITHM",
    "BASE_TARGET_SEED_NAMESPACE",
    "SPLIT_ALGORITHM",
    "SPLIT_SEED_NAMESPACE",
    "CALIBRATION_SCAFFOLD_COUNTS",
    "COMPOUNDS_PER_SCAFFOLD",
    "EXPECTED_SPLIT_COUNTS",
    "SPLIT_ORDER",
    "CALIBRATION_COVARIATE_ORDER",
    "CalibrationWorld",
    "ScaffoldGeometryError",
    "ExcludedConstructionError",
    "frozen_law_target",
    "assign_calibration_split",
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

# -----------------------------------------------------------------------
# A3.2 algorithm identities and seed namespaces
# -----------------------------------------------------------------------

BASE_TARGET_ALGORITHM = "muru-a3.2-base-target-global-permutation-1.0.0"
BASE_TARGET_SEED_NAMESPACE = "BASE_TARGET"

SPLIT_ALGORITHM = "muru-a3.2-calibration-scaffold-split-1.0.0"
SPLIT_SEED_NAMESPACE = "SPLIT"

#: A3.2 Decision 2.  60/20/20 of 30 scaffolds.
CALIBRATION_SCAFFOLD_COUNTS: dict[str, int] = {
    "train": 18, "validation": 6, "test": 6,
}

#: Follows from 30 equal scaffolds of 6, which is asserted at build time
#: rather than assumed.
COMPOUNDS_PER_SCAFFOLD = N_COMPOUNDS // N_SCAFFOLD_GROUPS
EXPECTED_SPLIT_COUNTS: dict[str, int] = {
    name: count * COMPOUNDS_PER_SCAFFOLD
    for name, count in CALIBRATION_SCAFFOLD_COUNTS.items()
}

#: Deterministic partition emission order.  Never a set, never dict order.
SPLIT_ORDER: tuple[str, ...] = ("train", "validation", "test")

if sum(CALIBRATION_SCAFFOLD_COUNTS.values()) != N_SCAFFOLD_GROUPS:
    raise ImportError(
        f"A3.2 scaffold split {CALIBRATION_SCAFFOLD_COUNTS} does not partition "
        f"{N_SCAFFOLD_GROUPS} scaffolds"
    )


class ScaffoldGeometryError(RuntimeError):
    """The frozen generator's scaffold geometry is not what A3.2 assumes.

    A3.2 Decision 2 point 7: if the assumption of exactly 30 equal-size
    scaffolds is false in the frozen code, STOP and report.  Do not silently
    approximate 60/20/20.
    """


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
        return {name: splits == name for name in SPLIT_ORDER}

    def construction_digest(self) -> str:
        """Identity of the world's actual scientific content.

        Binds the base-target values, the split labels and the scaffold
        labels, so a seed record can prove it was produced on THIS world.
        A record made before A3.2 - different base target, different split -
        cannot match, and is therefore not adoptable on resume.
        """
        payload = hashlib.sha256()
        payload.update(self.world_id.encode("utf-8"))
        payload.update(BASE_TARGET_ALGORITHM.encode("utf-8"))
        payload.update(SPLIT_ALGORITHM.encode("utf-8"))
        payload.update(np.asarray(self.target, dtype=np.float64).tobytes())
        for column in ("scaffold_id", "split"):
            values = "|".join(str(v) for v in self.compounds[column])
            payload.update(values.encode("utf-8"))
        return payload.hexdigest()


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


def frozen_law_target(
    world_id: str, compounds: pd.DataFrame, kind: str = BASE_TARGET_KIND
) -> np.ndarray:
    """The frozen-law target vector, before A3.2's global permutation.

    Exposed so tests can prove multiset equality against the permuted
    target.  This is NOT the base target: see :func:`_base_target`.
    """
    rng = np.random.default_rng(derive_seed(world_id, "law"))
    g, _family, _active, _relationship, _coeffs, _exps = _law(kind, compounds, rng)
    if g is None:
        raise RuntimeError(f"frozen law {kind!r} produced no target")
    return np.asarray(g, dtype=np.float64)


def _base_target(
    world_id: str, compounds: pd.DataFrame, kind: str
) -> np.ndarray:
    """The A3.2 base target: frozen-law values, globally reassigned.

    Amendment A3.2 Decision 1.  The frozen law is evaluated unchanged, then
    its values are reassigned across the complete set of compound identities
    under a dedicated seed, before any null-family transformation and before
    any partition use.

    This is a true permutation.  ``np.random.Generator.permutation`` on an
    index array yields a bijection on ``0..179``, so every value appears
    exactly once: nothing is added, removed, or altered numerically.  The
    marginal distribution is the frozen law's, value for value.

    The permutation consults nothing.  It is a function of ``world_id``
    alone - not of descriptors, scaffold, mass, split, or search output.
    Note that the index array being permuted carries no data, only positions.
    """
    values = frozen_law_target(world_id, compounds, kind)

    # Dedicated namespace, canonical derivation, independent of every other
    # seed this module or the contract derives.
    rng = np.random.default_rng(derive_seed(world_id, BASE_TARGET_SEED_NAMESPACE))
    order = rng.permutation(len(values))
    permuted = values[order]

    if permuted.shape != values.shape:  # pragma: no cover - permutation is total
        raise RuntimeError("base-target permutation changed the vector length")
    return permuted


def assign_calibration_split(
    world_id: str, compounds: pd.DataFrame
) -> np.ndarray:
    """A3.2 Decision 2: the 18/6/6 scaffold-disjoint calibration split.

    Replaces the frozen generator's own 20/5/5 ``split`` column for
    calibration worlds only.  The frozen generator is not edited.

    Scaffold identity is atomic: scaffolds are shuffled as whole units and
    sliced 18/6/6, so a scaffold cannot straddle two partitions by
    construction rather than by later check.

    Consults scaffold identity and nothing else - no target, no descriptor,
    no mass, no search output, no null-family outcome.  The sorted scaffold
    list makes the assignment independent of row order.

    Returns a per-compound array of partition labels aligned to
    ``compounds`` row order.
    """
    scaffolds = np.asarray(compounds["scaffold_id"], dtype=object)
    # Sort only after confirming the labels are mutually comparable, so a
    # NaN or a mixed int/str scaffold column raises ScaffoldGeometryError
    # rather than escaping as a bare TypeError from sorted().
    try:
        unique = np.array(sorted(set(scaffolds)), dtype=object)
    except TypeError as exc:
        raise ScaffoldGeometryError(
            f"scaffold labels are not mutually comparable ({exc}); "
            f"refusing to approximate 60/20/20"
        ) from exc

    if len(unique) != N_SCAFFOLD_GROUPS:
        raise ScaffoldGeometryError(
            f"A3.2 requires exactly {N_SCAFFOLD_GROUPS} scaffolds, found "
            f"{len(unique)}; refusing to approximate 60/20/20"
        )
    sizes = {s: int((scaffolds == s).sum()) for s in unique}
    if set(sizes.values()) != {COMPOUNDS_PER_SCAFFOLD}:
        raise ScaffoldGeometryError(
            f"A3.2 assumes {N_SCAFFOLD_GROUPS} equal scaffolds of "
            f"{COMPOUNDS_PER_SCAFFOLD}; found sizes {sorted(set(sizes.values()))}. "
            f"STOP: do not silently approximate 60/20/20"
        )

    rng = np.random.default_rng(derive_seed(world_id, SPLIT_SEED_NAMESPACE))
    shuffled = unique[rng.permutation(len(unique))]

    assignment: dict[object, str] = {}
    start = 0
    for name in SPLIT_ORDER:
        count = CALIBRATION_SCAFFOLD_COUNTS[name]
        for scaffold in shuffled[start:start + count]:
            assignment[scaffold] = name
        start += count

    return np.array([assignment[s] for s in scaffolds], dtype=object)


def build_world(construction: str, index: int) -> CalibrationWorld:
    """Build one calibration world, under Amendment A3.2.

    The world is a pure function of ``(construction, index)``: identical
    inputs give bitwise-identical covariates, targets, split and seeds.

    Order matters and is fixed by A3.2: frozen law, then global target
    permutation, then the calibration split, then the null-family
    transformation.  The base target is randomized before any partition
    exists, so the split cannot have informed it.

    There is deliberately no ``base_target_kind`` parameter.  A3.2 pins the
    base target, and a parameter that changed a world's numbers while leaving
    its ``world_id`` unchanged would let two different worlds share one seed
    record file.
    """
    _check_construction(construction)
    if index < 0 or index >= CONSTRUCTION_ALLOCATION[construction]:
        raise ValueError(
            f"index {index} outside 0..{CONSTRUCTION_ALLOCATION[construction] - 1} "
            f"for construction {construction!r}; the frozen allocation is "
            f"{dict(CONSTRUCTION_ALLOCATION)}"
        )
    kind = BASE_TARGET_KIND
    world_id = derive_world_id(construction, index)

    compounds, _seeds = _synthetic_compounds(world_id)
    if len(compounds) != N_COMPOUNDS:  # pragma: no cover - frozen generator
        raise RuntimeError(
            f"expected {N_COMPOUNDS} compounds, got {len(compounds)}"
        )
    if compounds["scaffold_id"].nunique() != N_SCAFFOLD_GROUPS:  # pragma: no cover
        raise ScaffoldGeometryError(
            f"expected {N_SCAFFOLD_GROUPS} scaffold groups, got "
            f"{compounds['scaffold_id'].nunique()}"
        )

    # A3.2 Decision 1: global reassignment of the frozen-law target values,
    # before the split is assigned and before the null transformation.
    target = _base_target(world_id, compounds, kind)

    # A3.2 Decision 2: the calibration split replaces the frozen generator's
    # own 20/5/5 column.  The generator itself is untouched.
    compounds = compounds.copy()
    compounds["split"] = assign_calibration_split(world_id, compounds)

    actual_split = compounds["split"].value_counts().to_dict()
    if actual_split != EXPECTED_SPLIT_COUNTS:  # pragma: no cover - constructed above
        raise RuntimeError(
            f"calibration split is {actual_split}, expected {EXPECTED_SPLIT_COUNTS}"
        )
    if compounds.groupby("scaffold_id")["split"].nunique().max() != 1:  # pragma: no cover
        raise RuntimeError("calibration split is not scaffold-disjoint")

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


def build_all_worlds() -> list[CalibrationWorld]:
    """Build all 100 worlds in the frozen allocation order.

    Materializing all 100 worlds is cheap; *executing* them is not, and this
    function performs no search.

    The RC3 acknowledgement gate is gone: A3.2 resolved the base target, so
    there is no longer an unresolved science decision to acknowledge.
    """
    worlds: list[CalibrationWorld] = []
    for construction in CONSTRUCTION_ALLOCATION:
        for index in range(CONSTRUCTION_ALLOCATION[construction]):
            worlds.append(build_world(construction, index))
    if len(worlds) != N_CALIBRATION_WORLDS:  # pragma: no cover - frozen sum
        raise RuntimeError(
            f"expected {N_CALIBRATION_WORLDS} worlds, built {len(worlds)}"
        )
    return worlds
