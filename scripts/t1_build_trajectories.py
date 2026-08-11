"""T1.4-T1.8 -- parse the corpus into trajectories.parquet with full provenance.

One row per (record x preprocessing cell). Raw metadata strings are carried
through so that every downstream number can be traced back to the bytes it came
from. Nothing is imputed; missing values stay missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.energy import (  # noqa: E402
    e_com_ev, e_lab_ev, infer_charge_from_precursor_type, ion_mass,
    parse_collision_energy,
)
from muru.features import (  # noqa: E402
    COVARIATES, ENDPOINTS, decomposition_residual_exact,
    decomposition_residual_plan, precursor_mass_ratio,
)
from muru.identity import check_identity, group_key  # noqa: E402
from muru.io.massbank import iter_records  # noqa: E402
from muru.spectra import spectrum_from_record  # noqa: E402

DATA = ROOT / "data" / "massbank" / "MassBank-data" / "LCSB"
ART = ROOT / "artifacts"


def _f(x):
    """float() that yields None rather than raising or defaulting."""
    if x is None:
        return None
    try:
        return float(str(x).split()[0])
    except (ValueError, IndexError):
        return None


def main() -> None:
    cfg = yaml.safe_load((ROOT / "configs" / "dataset.yaml").read_text())
    pcfg = yaml.safe_load((ROOT / "configs" / "preprocessing.yaml").read_text())
    slot_map = cfg["massbank"]["slot_map"]
    ppm = pcfg["precursor_match_ppm"]

    cells = [
        {"relative_cutoff": rc, "include_precursor": ip, "intensity_transform": it}
        for rc in pcfg["grid"]["relative_cutoff"]
        for ip in pcfg["grid"]["include_precursor"]
        for it in pcfg["grid"]["intensity_transform"]
    ]
    base = pcfg["base_cell"]

    rows, ident_rows = [], []
    for rec in iter_records(DATA):
        acc = rec.accession
        slot = rec.slot
        smiles = rec.get("CH$SMILES")
        ik = rec.inchikey

        ic = check_identity(acc, smiles, ik)
        ident_rows.append({
            "accession": acc, "status": ic.status, "note": ic.note,
            "smiles": ic.smiles_raw, "inchikey_recorded": ic.inchikey_recorded,
            "inchikey_from_smiles": ic.inchikey_from_smiles,
            "n_fragments": ic.n_fragments, "has_stereo": ic.has_stereo,
        })

        ion_mode = rec.sub("AC$MASS_SPECTROMETRY", "ION_MODE")
        ce_raw = rec.sub("AC$MASS_SPECTROMETRY", "COLLISION_ENERGY")
        ce = parse_collision_energy(ce_raw)
        prec_type = rec.sub("MS$FOCUSED_ION", "PRECURSOR_TYPE")
        charge, charge_prov = infer_charge_from_precursor_type(prec_type)
        prec_mz = _f(rec.sub("MS$FOCUSED_ION", "PRECURSOR_M/Z"))
        rt = _f(rec.sub("AC$CHROMATOGRAPHY", "RETENTION_TIME"))

        # Derived energies. Computed only when every input is present AND the
        # charge state was actually determined -- never on a defaulted charge.
        e_lab = e_com = None
        if ce.numeric_value is not None and prec_mz and charge:
            e_lab = e_lab_ev(ce.numeric_value, prec_mz, charge)
            e_com = e_com_ev(e_lab, ion_mass(prec_mz, charge))

        spec = spectrum_from_record(rec, ppm=ppm)
        expected = slot_map.get(slot) if slot else None

        common = {
            "accession": acc,
            "internal_id_accession": rec.internal_id,
            "internal_id_comment": rec.sub("COMMENT", "INTERNAL_ID"),
            "slot": slot,
            "record_title": rec.get("RECORD_TITLE"),
            "dataset_raw": rec.sub("COMMENT", "DATASET"),
            "confidence_raw": rec.sub("COMMENT", "CONFIDENCE"),
            # identity
            "inchikey_recorded": ik,
            "inchikey_first_block": (ik or "").split("-")[0] if ik else None,
            "smiles_raw": smiles,
            "formula_raw": rec.get("CH$FORMULA"),
            "exact_mass": _f(rec.get("CH$EXACT_MASS")),
            "identity_status": ic.status,
            "identity_usable": ic.usable,
            "group_key": group_key(ik, ion_mode),
            # acquisition
            "ion_mode_raw": ion_mode,
            "instrument_raw": rec.get("AC$INSTRUMENT"),
            "instrument_type_raw": rec.get("AC$INSTRUMENT_TYPE"),
            "fragmentation_mode_raw": rec.sub("AC$MASS_SPECTROMETRY",
                                              "FRAGMENTATION_MODE"),
            "resolution_raw": rec.sub("AC$MASS_SPECTROMETRY", "RESOLUTION"),
            "ms_type_raw": rec.sub("AC$MASS_SPECTROMETRY", "MS_TYPE"),
            "retention_time_min": rt,
            # collision energy -- five separate fields, never collapsed
            "ce_raw": ce.raw_value,
            "ce_numeric": ce.numeric_value,
            "ce_energy_type": ce.energy_type,
            "ce_unit": ce.unit,
            "ce_parse_status": ce.parse_status,
            "ce_provenance": ce.provenance,
            "ce_warning": ce.warning,
            "e_lab_ev_derived": e_lab,
            "e_com_ev_derived": e_com,
            # precursor
            "precursor_type_raw": prec_type,
            "precursor_mz": prec_mz,
            "precursor_charge": charge,
            "charge_provenance": charge_prov,
            "precursor_intensity_raw": _f(
                rec.sub("MS$FOCUSED_ION", "PRECURSOR_INTENSITY")),
            # slot-convention assertion inputs
            "slot_expected_mode": expected["mode"] if expected else None,
            "slot_expected_ce": expected["ce"] if expected else None,
            "n_peaks_declared": rec.num_peak_declared,
            "n_peaks_parsed": len(rec.peaks),
            "n_annotation_rows": len(rec.annotation_rows),
            "parse_status": rec.parse_status,
            "parse_warnings": "; ".join(rec.warnings) if rec.warnings else None,
            "source_branch": "massbank_curated",
        }

        for cell in cells:
            s = spec.preprocess(ppm=ppm, **cell)
            is_base = all(cell[k] == base[k] for k in cell)
            row = dict(common)
            row.update({
                "cell_relative_cutoff": cell["relative_cutoff"],
                "cell_include_precursor": cell["include_precursor"],
                "cell_intensity_transform": cell["intensity_transform"],
                "is_base_cell": is_base,
            })
            for name, fn in ENDPOINTS.items():
                row[name] = fn(s)
            for name, fn in COVARIATES.items():
                row[name] = fn(s)
            row["precursor_mass_ratio"] = precursor_mass_ratio(s, ppm)
            row["decomp_residual_exact"] = decomposition_residual_exact(s, ppm)
            row["decomp_residual_plan"] = decomposition_residual_plan(s, ppm)
            rows.append(row)

    df = pd.DataFrame(rows)
    ART.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ART / "trajectories.parquet", index=False)
    pd.DataFrame(ident_rows).to_parquet(ART / "identity_checks.parquet", index=False)

    n_rec = df["accession"].nunique()
    print(f"records: {n_rec}  rows: {len(df):,}  cells/record: {len(cells)}")
    print(f"written: artifacts/trajectories.parquet ({len(df):,} rows)")
    print(f"         artifacts/identity_checks.parquet ({len(ident_rows):,} rows)")


if __name__ == "__main__":
    main()
