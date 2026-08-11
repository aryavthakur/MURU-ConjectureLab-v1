"""Corpus-wide BLOCKER assertions against the built trajectory table.

These are the checks that would catch a silent corruption between acquisition
and analysis: hash drift, wrong energy assignment, wrong grouping, a broken
decomposition, or a coverage figure that does not match the census.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TRAJ = ROOT / "artifacts" / "trajectories.parquet"
MANIFEST = ROOT / "artifacts" / "MANIFEST_massbank.json"

requires_artifacts = pytest.mark.skipif(
    not TRAJ.exists(), reason="trajectories.parquet not built"
)
pytestmark = requires_artifacts


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet(TRAJ)


@pytest.fixture(scope="module")
def base(df):
    return df[df.is_base_cell].copy()


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def test_manifest_hashes_still_verify():
    """BLOCKER: manifest hash mismatch on acquired scientific data."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from muru.io.manifest import Manifest

    problems = Manifest.read(MANIFEST).verify()
    assert problems == [], f"acquired data changed since acquisition: {problems[:5]}"


def test_manifest_covers_every_record(base):
    man = json.loads(MANIFEST.read_text())
    assert man["n_files"] == len(base)


# ---------------------------------------------------------------------------
# Energy assignment
# ---------------------------------------------------------------------------
def test_every_energy_in_expected_set(base):
    """BLOCKER: wrong collision energy assignment."""
    assert set(base.ce_numeric.dropna().unique()) == {15, 30, 45, 60, 75, 90}


def test_no_energy_silently_missing(base):
    assert base.ce_numeric.notna().all()


def test_energy_type_never_claims_a_unit_the_record_lacks(base):
    """The corpus declares no unit; energy_type must say so, every row."""
    assert (base.ce_energy_type == "NCE_ASSUMED_FROM_PUBLICATION").all()
    assert base.ce_unit.isna().all()


def test_slot_convention_holds_corpus_wide(base):
    """BLOCKER: incorrect trajectory coverage / wrong energy assignment.

    Master plan A3, verified on 373 records, asserted here on all of them.
    """
    assert (base.ion_mode_raw.str.upper() == base.slot_expected_mode).all()
    assert (base.ce_numeric == base.slot_expected_ce).all()


def test_all_precursors_singly_charged(base):
    """Master plan A5. If this ever fails, f(z) must be applied per record."""
    assert set(base.precursor_charge.dropna().unique()) == {1}
    assert base.precursor_charge.notna().all()


def test_derived_energies_present_and_ordered(base):
    """E_lab and E_com must exist and increase with NCE at fixed mass."""
    assert base.e_lab_ev_derived.notna().all()
    assert base.e_com_ev_derived.notna().all()
    med = base.groupby("ce_numeric").e_com_ev_derived.median()
    assert med.is_monotonic_increasing


# ---------------------------------------------------------------------------
# Grouping and identity
# ---------------------------------------------------------------------------
def test_no_group_spans_both_ion_modes(base):
    """BLOCKER: wrong compound grouping. Polarities must never pool."""
    spans = base.groupby("group_key").ion_mode_raw.nunique()
    assert (spans == 1).all()


def test_every_record_has_a_group_key(base):
    assert base.group_key.notna().all()


def test_no_duplicate_energy_within_a_group_internal_id(base):
    """BLOCKER: identity collision. One internal ID must not carry two records
    at the same energy in the same mode."""
    d = base.groupby(["internal_id_accession", "ion_mode_raw", "ce_numeric"]).size()
    assert (d == 1).all(), f"{int((d > 1).sum())} duplicated (id, mode, energy) cells"


def test_identity_checks_all_usable(base):
    """Corpus-specific: every record's SMILES regenerates its recorded InChIKey."""
    assert base.identity_usable.all()


# ---------------------------------------------------------------------------
# Peak integrity
# ---------------------------------------------------------------------------
def test_declared_and_parsed_peak_counts_agree(base):
    """BLOCKER: corrupted peak parsing."""
    assert (base.n_peaks_declared == base.n_peaks_parsed).all()


def test_no_parse_failures(base):
    assert (base.parse_status == "OK").all()


# ---------------------------------------------------------------------------
# The decomposition -- BLOCKER per the session brief
# ---------------------------------------------------------------------------
def test_exact_decomposition_holds_to_floating_point(df):
    r = df.decomp_residual_exact.dropna()
    assert r.max() < 1e-12, f"max exact-form residual {r.max():.3e}"


def test_plan_decomposition_residual_is_ppm_scale_not_zero(df):
    """The master plan's stated form mu = SY + (1-SY)*phi does NOT hold to
    floating point, because the observed precursor m/z differs from the
    declared PRECURSOR_M/Z after RMassBank recalibration.

    This test pins the documented magnitude so that a future change which
    accidentally 'fixes' it (e.g. by snapping peak masses to the declared
    precursor) is caught.
    """
    r = df.decomp_residual_plan.dropna()
    assert r.max() > 1e-12, "plan-form residual unexpectedly at floating point"
    assert r.max() < 1e-4, f"plan-form residual larger than ppm scale: {r.max():.3e}"


def test_precursor_mass_ratio_within_ppm_of_one(df):
    r = df.precursor_mass_ratio.dropna()
    assert np.abs(1 - r).max() < 1e-4


# ---------------------------------------------------------------------------
# No silent missing-value coercion
# ---------------------------------------------------------------------------
def test_degenerate_spectra_are_nan_not_zero(df):
    """BLOCKER: silent missing-value coercion. A spectrum with no fragments
    must give NaN fragment_depth, not 0.0."""
    only_prec = df[(df.peak_count == 1) & df.survival_yield.eq(1.0)]
    if len(only_prec):
        assert only_prec.fragment_depth.isna().all()


def test_endpoints_within_mathematical_bounds(base):
    for col in ["survival_yield", "base_peak_fraction"]:
        v = base[col].dropna()
        assert v.between(0, 1).all(), f"{col} outside [0,1]"
    e = base.spectral_entropy.dropna()
    assert (e >= 0).all()
    n = base.normalized_entropy.dropna()
    assert n.between(0, 1 + 1e-9).all()


def test_entropy_respects_ln_n_bound(base):
    """S <= ln(n) is a mathematical identity; violation means a broken
    implementation or a corrupted peak count."""
    s = base[(base.peak_count > 1) & base.spectral_entropy.notna()]
    assert (s.spectral_entropy <= np.log(s.peak_count) + 1e-9).all()
