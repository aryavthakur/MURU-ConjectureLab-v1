"""Regression test for the 2026-09-13 leakage incident
(artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/): the
parser preflight must be structurally incapable of selecting a spectrum that
belongs to a co-plated, non-anchor compound in a pooled well -- even when that
compound's own scan happens to sort earlier (by position/index) than the
anchor compound's scan in the same file. The original bug selected
`rung_scans.spectrum_id.tolist()[:6]` directly from a file's rung-tagged scans
with no per-compound restriction; the fix restricts every candidate spectrum
id through `match_compounds`, which filters by selected-ion m/z within 0.01 Da
of a specific compound's OWN theoretical [M+H]+.

This test builds a synthetic pooled well containing one ANCHOR compound and
one NON-ANCHOR ("validation-like") compound, with the non-anchor compound's
scans positioned FIRST in scan order (index 0-1, reproducing the exact
positional-selection failure mode) and the anchor's scans positioned later.
It asserts that scoping through match_compounds (as the fixed preflight now
does) never returns the non-anchor compound's spectrum ids, regardless of
position -- proving the fix, not just the input data of this one incident.
"""
import numpy as np
import pandas as pd

from muru.wur_v2 import external_msnlib as L


def _headers():
    """One pooled well: two precursors interleaved. The NON-ANCHOR compound's
    fixed-20/fixed-60 pair sits at index 0-1 (would be picked first by any
    positional `[:6]` selection); the ANCHOR compound's pair sits later."""
    rows = [
        # non-anchor ("validation-like") compound: m/z 500.0, positioned FIRST
        dict(index=0, ms_level=2, selected_ion_mz=500.0, collision_energy=20.0,
             spectrum_id="scan=1", scan_window_lower_limit=40, scan_window_upper_limit=600),
        dict(index=1, ms_level=2, selected_ion_mz=500.0, collision_energy=60.0,
             spectrum_id="scan=2", scan_window_lower_limit=40, scan_window_upper_limit=600),
        # anchor compound: m/z 300.0, positioned LATER
        dict(index=2, ms_level=2, selected_ion_mz=300.0, collision_energy=20.0,
             spectrum_id="scan=3", scan_window_lower_limit=40, scan_window_upper_limit=400),
        dict(index=3, ms_level=2, selected_ion_mz=300.0, collision_energy=60.0,
             spectrum_id="scan=4", scan_window_lower_limit=40, scan_window_upper_limit=400),
    ]
    return pd.DataFrame(rows)


def test_match_compounds_never_selects_a_co_plated_non_anchor_spectrum():
    h_rung = L.fixed_rung_scans(_headers())
    headers = {"pooled_well.mzML": h_rung}

    # the preflight only ever knows about the ANCHOR compound -- it must never see, and
    # therefore never be ABLE to select, the non-anchor compound's spectra, no matter
    # their position in the file.
    anchor_only_wells = pd.DataFrame([
        {"key": "ANCHOR_KEY", "unique_sample_id": "well_1", "fn": "pooled_well.mzML", "mh": 300.0},
    ])
    matched = L.match_compounds(anchor_only_wells, headers)
    selected_ids = set(matched[matched.window_ok].spectrum_id)

    assert selected_ids == {"scan=3", "scan=4"}, selected_ids
    assert "scan=1" not in selected_ids and "scan=2" not in selected_ids

    # sanity: if the (buggy, pre-fix) positional selection were used instead -- the first 6
    # rung-tagged scan ids straight from fixed_rung_scans, no match_compounds restriction at
    # all -- it WOULD include the non-anchor compound's spectra. This documents exactly what
    # the incident's root cause looked like and that the fix (match_compounds scoping) is
    # what prevents it, not an accident of this particular test's data.
    buggy_positional_selection = h_rung[h_rung.rung.notna()].spectrum_id.tolist()[:6]
    assert "scan=1" in buggy_positional_selection and "scan=2" in buggy_positional_selection


def test_match_compounds_respects_mz_tolerance_even_for_a_close_but_wrong_compound():
    """A non-anchor compound whose m/z is within a few Da (but outside the frozen 0.01 Da
    matching tolerance) of the anchor's m/z must still never be selected."""
    rows = [
        dict(index=0, ms_level=2, selected_ion_mz=300.05, collision_energy=20.0,
             spectrum_id="scan=near_1", scan_window_lower_limit=40, scan_window_upper_limit=400),
        dict(index=1, ms_level=2, selected_ion_mz=300.05, collision_energy=60.0,
             spectrum_id="scan=near_2", scan_window_lower_limit=40, scan_window_upper_limit=400),
        dict(index=2, ms_level=2, selected_ion_mz=300.0, collision_energy=20.0,
             spectrum_id="scan=exact_1", scan_window_lower_limit=40, scan_window_upper_limit=400),
        dict(index=3, ms_level=2, selected_ion_mz=300.0, collision_energy=60.0,
             spectrum_id="scan=exact_2", scan_window_lower_limit=40, scan_window_upper_limit=400),
    ]
    h_rung = L.fixed_rung_scans(pd.DataFrame(rows))
    headers = {"pooled_well.mzML": h_rung}
    wells = pd.DataFrame([{"key": "ANCHOR_KEY", "unique_sample_id": "well_1", "fn": "pooled_well.mzML", "mh": 300.0}])
    matched = L.match_compounds(wells, headers)
    selected_ids = set(matched[matched.window_ok].spectrum_id)
    assert selected_ids == {"scan=exact_1", "scan=exact_2"}, selected_ids
