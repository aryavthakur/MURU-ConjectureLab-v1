"""Collision energy: parsing, provenance, and the laboratory/CoM transforms.

THE CENTRAL FACT ABOUT THIS FIELD (master plan section 4.4, verified in T1.7):

    AC$MASS_SPECTROMETRY: COLLISION_ENERGY 15

carries a bare integer. No unit. No convention marker. Nothing inside the
record identifies it as normalized collision energy. Only the publication does.

MURU therefore never collapses the following into one `energy` field:

    ce_raw          the literal string from the record
    ce_numeric      the parsed number
    energy_type     NCE_ASSUMED_FROM_PUBLICATION -- an assumption, so named
    e_lab_ev        derived, conditional on the NCE reading being right
    e_com_ev        derived, single-collision approximation

Downstream code that wants "the energy" must name which of these it means.

--------------------------------------------------------------------------
FORMULA PROVENANCE
--------------------------------------------------------------------------
The master plan (section 6.2) states:

    E_lab(eV) = NCE(%) * (mz_precursor / 500) * f(z)
    f(1)=1, f(2)=0.9, f(3)=0.85, f(4)=0.8, f(5+)=0.75

and attributes it to Revesz et al. 2023 (Mass Spectrom Rev), Thermo PSB 104.

Per the session instruction "Do NOT treat the planning document itself as an
authority for instrument physics", this module records the formula's status as
SUPPORTED-BY-CITED-SOURCE rather than VERIFIED. The citation chain was read
from the master plan; the primary sources (Thermo Product Support Bulletin 104
and Revesz et al.) were NOT retrieved and re-read during this implementation.
That limitation is stated in CE_AUDIT.md and is the reason every E_lab and
E_com value in this project is labelled derived-and-conditional.

What IS independently verifiable here, and is verified in T1.7:
  - the value set actually present in the corpus,
  - that every precursor is singly charged (so f(z) = 1 and the charge factor
    never actually varies in this corpus -- the one place the formula could
    have introduced an error is inert),
  - the algebraic identity between the two E_com forms below.

The center-of-mass transform is standard two-body kinematics and does not
depend on Thermo:

    E_com = E_lab * m_gas / (m_gas + M_ion)

with m_gas = 28 Da (N2). Substituting E_lab and m_gas = 28, and noting that for
a singly charged ion M_ion is numerically the precursor m/z:

    E_com = NCE * (M_ion/500) * 28/(28 + M_ion) = 0.056 * NCE * M_ion/(M_ion+28)

CAVEAT (master plan section 6.2, risk R12): HCD is a multi-collision regime.
The single-collision CoM energy is an approximation and is used descriptively
only. No Phase 1 conclusion rests on it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NCE_REFERENCE_MASS = 500.0  # Da, Thermo normalization reference
N2_MASS = 28.0  # Da
CHARGE_FACTOR = {1: 1.00, 2: 0.90, 3: 0.85, 4: 0.80}
CHARGE_FACTOR_5PLUS = 0.75

ENERGY_TYPE_ASSUMED = "NCE_ASSUMED_FROM_PUBLICATION"
ENERGY_PROVENANCE = (
    "Elapavalore et al. 2023, Environ Sci Process Impacts 25:1788-1801, "
    "DOI 10.1039/D3EM00181D, methods section. The record itself carries no unit."
)

_INT_RE = re.compile(r"^\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<trailing>\S*)\s*$")


@dataclass(frozen=True)
class CollisionEnergy:
    """A parsed collision energy with its ambiguity preserved, not resolved."""

    raw_value: str | None
    numeric_value: float | None
    energy_type: str
    unit: str | None            # None means the record declared no unit.
    parse_status: str           # OK | NO_UNIT_IN_RECORD | UNPARSEABLE | ABSENT
    source_field: str
    provenance: str
    warning: str | None = None


def parse_collision_energy(
    raw: str | None,
    source_field: str = "AC$MASS_SPECTROMETRY: COLLISION_ENERGY",
) -> CollisionEnergy:
    """Parse the record's collision-energy string without inventing a unit.

    A bare integer yields parse_status="NO_UNIT_IN_RECORD" -- this is the
    normal, expected case for this corpus and is NOT an error. It is the
    honest label for a number whose unit is supplied by a publication rather
    than by the data.
    """
    if raw is None:
        return CollisionEnergy(
            raw_value=None, numeric_value=None, energy_type="UNKNOWN", unit=None,
            parse_status="ABSENT", source_field=source_field,
            provenance=ENERGY_PROVENANCE, warning="field absent from record",
        )

    m = _INT_RE.match(raw)
    if not m:
        return CollisionEnergy(
            raw_value=raw, numeric_value=None, energy_type="UNKNOWN", unit=None,
            parse_status="UNPARSEABLE", source_field=source_field,
            provenance=ENERGY_PROVENANCE,
            warning=f"could not parse a number from {raw!r}",
        )

    value = float(m.group("value"))
    trailing = m.group("trailing") or ""

    if trailing:
        # The record DID declare something after the number. Keep it verbatim;
        # do not map it onto an assumed convention.
        return CollisionEnergy(
            raw_value=raw, numeric_value=value, energy_type="DECLARED_IN_RECORD",
            unit=trailing, parse_status="OK", source_field=source_field,
            provenance=f"unit {trailing!r} read directly from the record",
            warning=None,
        )

    return CollisionEnergy(
        raw_value=raw, numeric_value=value, energy_type=ENERGY_TYPE_ASSUMED,
        unit=None, parse_status="NO_UNIT_IN_RECORD", source_field=source_field,
        provenance=ENERGY_PROVENANCE,
        warning="record declares no unit; NCE reading comes from the publication",
    )


def charge_factor(z: int) -> float:
    """Thermo NCE charge-state factor f(z). SUPPORTED, not independently verified."""
    if z < 1:
        raise ValueError(f"charge state must be >= 1, got {z}")
    return CHARGE_FACTOR.get(z, CHARGE_FACTOR_5PLUS)


def e_lab_ev(nce: float, precursor_mz: float, charge: int = 1) -> float:
    """Laboratory-frame collision energy in eV.

        E_lab = NCE * (m/z / 500) * f(z)

    DERIVED and CONDITIONAL on the NCE reading (see module docstring).
    """
    if precursor_mz <= 0:
        raise ValueError(f"precursor m/z must be positive, got {precursor_mz}")
    return nce * (precursor_mz / NCE_REFERENCE_MASS) * charge_factor(charge)


def ion_mass(precursor_mz: float, charge: int = 1) -> float:
    """Ion mass in Da from m/z and charge. For z=1 these are numerically equal."""
    return precursor_mz * charge


def e_com_ev(e_lab: float, m_ion: float, m_gas: float = N2_MASS) -> float:
    """Single-collision center-of-mass energy.

        E_com = E_lab * m_gas / (m_gas + M_ion)

    Standard two-body kinematics; independent of the Thermo formula.
    APPROXIMATE for HCD, which is multi-collision. Descriptive use only.
    """
    if m_ion <= 0:
        raise ValueError(f"ion mass must be positive, got {m_ion}")
    return e_lab * m_gas / (m_gas + m_ion)


def e_com_direct(nce: float, m_ion: float, charge: int = 1,
                 m_gas: float = N2_MASS) -> float:
    """E_com computed in one step. For z=1 this equals

        0.056 * NCE * M_ion / (M_ion + 28)

    A test asserts this agrees with e_com_ev(e_lab_ev(...)) to floating point.
    """
    return e_com_ev(e_lab_ev(nce, m_ion / charge, charge), m_ion, m_gas)


def infer_charge_from_precursor_type(precursor_type: str | None) -> tuple[int | None, str]:
    """Charge state from the adduct string. Returns (charge, provenance).

    Returns (None, reason) when the adduct is not recognised. NEVER defaults to
    1 -- an unrecognised adduct must surface, because a wrong charge silently
    corrupts every derived energy.
    """
    if precursor_type is None:
        return None, "PRECURSOR_TYPE absent"
    t = precursor_type.strip()
    singly = {
        "[M+H]+", "[M-H]-", "[M+Na]+", "[M+K]+", "[M+NH4]+",
        "[M+Cl]-", "[M+HCOO]-", "[M+CH3COO]-", "[M]+", "[M]-",
    }
    if t in singly:
        return 1, f"adduct {t!r} is singly charged by inspection"
    m = re.search(r"\](?P<n>\d*)(?P<sign>[+-])$", t)
    if m:
        n = int(m.group("n")) if m.group("n") else 1
        return n, f"charge {n} read from adduct suffix of {t!r}"
    return None, f"unrecognised adduct {t!r}"
