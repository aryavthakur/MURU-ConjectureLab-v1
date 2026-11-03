"""The E0 design grid: the crossed 3 x 3 and the preregistered decision rule.

Every constant in this module is transcribed from the committed design
(`MURU_V2_A1_STUDY_DESIGN.md` section 2.2, 2.5, 2.6) and its executable
operationalisation (`MURU_V2_E0_PROTOCOL.md` sections 3 and 4).  Nothing here
was chosen after a result was seen; `scripts/verify_e0_design_fidelity.py`
re-derives the grid from this module and checks the generated corpus against it.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "GENERATOR_CLIP_LEVELS",
    "FITTER_MU_CEIL_LEVELS",
    "CELLS",
    "CELLS_BY_ID",
    "N_REPLICATES",
    "CONTROL_CELL",
    "DECOUPLED_CELL",
    "GEN_ONLY_CELL",
    "FIT_ONLY_CELL",
    "V1_MATCHED_REFERENCE",
    "DECISION_BANDS",
    "Cell",
    "classify_delta",
]

#: Factor 1, `MURU_V2_A1_STUDY_DESIGN.md` section 2.2.  `None` is "no clip".
GENERATOR_CLIP_LEVELS: tuple[tuple[str, float | None], ...] = (
    ("1e4", 1.0 - 1e-4),
    ("1e3", 1.0 - 1e-3),
    ("none", None),
)

#: Factor 2, same section.  The third level is the design's "open" ceiling.
FITTER_MU_CEIL_LEVELS: tuple[tuple[str, float], ...] = (
    ("1e4", 1.0 - 1e-4),
    ("1e3", 1.0 - 1e-3),
    ("open", 1.0 + 1e-2),
)

#: Design section 2.5.
N_REPLICATES = 60


@dataclass(frozen=True)
class Cell:
    cell_id: str
    generator_clip_level: str
    fitter_ceil_level: str
    generator_clip: float | None
    fitter_mu_ceil: float

    @property
    def is_control(self) -> bool:
        return self.cell_id == CONTROL_CELL

    @property
    def coupled(self) -> bool:
        """True iff the generator clip and the fitter ceiling are one constant."""
        return self.generator_clip is not None and self.generator_clip == self.fitter_mu_ceil


CELLS: tuple[Cell, ...] = tuple(
    Cell(
        cell_id=f"c_gen_{gen_name}__ceil_{ceil_name}",
        generator_clip_level=gen_name,
        fitter_ceil_level=ceil_name,
        generator_clip=gen_value,
        fitter_mu_ceil=ceil_value,
    )
    for gen_name, gen_value in GENERATOR_CLIP_LEVELS
    for ceil_name, ceil_value in FITTER_MU_CEIL_LEVELS
)

CELLS_BY_ID: dict[str, Cell] = {cell.cell_id: cell for cell in CELLS}

#: Design section 2.2: the v1 arm, which must reproduce v1 boundary behaviour.
CONTROL_CELL = "c_gen_1e4__ceil_1e4"
#: Protocol section 4: the cell in which the coincidence is broken on both sides.
DECOUPLED_CELL = "c_gen_none__ceil_open"
#: Protocol section 4: the two single-factor decouplings.
GEN_ONLY_CELL = "c_gen_none__ceil_1e4"
FIT_ONLY_CELL = "c_gen_1e4__ceil_open"

#: Protocol section 3, computed from `MURU_V1_G1_FAILURE_TAXONOMY.csv` before
#: any E0 world existed.  The 60 Held-out G1 cases of variants F05, F08, F11,
#: F12 and F17 -- E0's exact generative configuration at E0's sample size.
V1_MATCHED_REFERENCE = {
    "variants": ("F05", "F08", "F11", "F12", "F17"),
    "n": 60,
    "boundary_limited": 37,
    "boundary_limited_rate": 37 / 60,
    "wilson_lower_95": 0.4902,
    "wilson_upper_95": 0.7291,
    "modal_dominant_bound": "M3:low_energy_plateau@upper",
    "modal_dominant_bound_count": 55,
    "detectors_fired": 0,
}

#: Design section 2.6, with the mixed band closed at both endpoints so the three
#: outcomes are exhaustive and disjoint (protocol section 4).
DECISION_BANDS = (
    ("H_clip", "delta > 0.50"),
    ("H_clip_and_H_alias", "0.10 <= delta <= 0.50"),
    ("H_null", "delta < 0.10"),
)


def classify_delta(delta: float) -> str:
    """The preregistered band `delta` falls in.  No other rule may be applied."""
    if delta > 0.50:
        return "H_clip"
    if delta >= 0.10:
        return "H_clip_and_H_alias"
    return "H_null"
