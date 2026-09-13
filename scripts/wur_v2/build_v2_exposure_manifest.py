"""Machine-readable v2 exposure manifest: every compound/spectrum population
MURU has touched, with its exposure class. Identity only."""
import json, time
from pathlib import Path
import pandas as pd
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.wur_v2.exposure import lcsb_confirmation_keys

ROOT = Path(__file__).resolve().parents[2]; ART = ROOT / "artifacts"
D = ART / "wur_v2" / "data"
cov = pd.read_csv(D / "compounds.csv")
conf = lcsb_confirmation_keys()
hold_d = json.loads((ART / "wur_dev_internal_holdout.json").read_text())
sealed = set(json.loads((ART / "wur_sealed_partition.json").read_text())["connectivity_keys"])
pre = partition(load_annotated_trajectories(ROOT / "data" / "external" / "wur"))
part = apply_d6(pre, sealed_scaffold_groups(pre["POS"]))
neg = part["NEG"]
t = pd.read_parquet(ART / "trajectories.parquet", columns=["inchikey_first_block", "ion_mode_raw", "is_base_cell"])
lneg = set(t[(t.ion_mode_raw.str.upper() == "NEGATIVE") & t.is_base_cell].inchikey_first_block)
lpos_all = set(t[(t.ion_mode_raw.str.upper() == "POSITIVE") & t.is_base_cell].inchikey_first_block)
p2 = pd.read_parquet(ART / "p2_compounds.parquet"); lcsb_dev = set(p2[~p2.in_confirmation].inchikey_first_block)
rb = pd.read_parquet(ART / "raw_branch_scans.parquet")

def entry(keys, cls, note):
    keys = sorted(keys)
    return {"exposure_class": cls, "n_keys": len(keys), "connectivity_keys_sha256": canonical_key_hash(keys),
            "connectivity_keys": keys, "note": note}

pops = {
 "LCSB-DEV": entry(lcsb_dev, "development-exposed", "MassBank LCSB Q Exactive positive mode, Phase 2 development corpus; fitted and scored since Phase 2"),
 "WUR-DEV-ANALYSIS": entry(hold_d["analysis"]["connectivity_keys"], "development-exposed", "Stage 2A/2B development; 124 keys also in LCSB-DEV (population B, used to fit the Stage 1 bridge)"),
 "WUR-DEV-HOLD": entry(hold_d["hold"]["connectivity_keys"], "historical-holdout-now-exposed", "one look 2026-09-12 (hold_check.json), EXPOSED"),
 "WUR-SEALED": entry(sealed, "historical-external-validation-now-exposed", "one look at 69ca1a6, 2026-09-12T19:55:23Z; EXPOSED permanently; can never again support an independent external claim"),
 "LCSB-CONFIRMATION": entry(conf, "prohibited-excluded", "Phase 2 sealed confirmation set, never used for fitting or scoring; Phase 1 endpoint screen saw the full corpus. 41 keys are also WUR-SEALED: their WUR copies are v2 development data, their LCSB spectra stay excluded. Same acquisition campaign as LCSB-DEV and n=110: cannot support an independent external claim; kept excluded to preserve status"),
 "WUR-NEG-DEV": entry(neg[neg.side == "WUR-DEV"].connectivity_key, "prohibited-excluded", "negative mode, identity/header accessed in Stage 0; peaks never decoded by any stage; outside the v2 positive-ion domain"),
 "WUR-NEG-D6-EXCLUDED": entry(neg[neg.side == "EXCLUDED"].connectivity_key, "prohibited-excluded", "rule D6 exclusions (scaffold groups sealed on the positive side)"),
 "LCSB-NEG": entry(lneg, "prohibited-excluded", "LCSB negative-mode records; Phase 1 descriptive endpoint census only; outside the v2 domain"),
 "LCSB-RAW-MIXES-499-503-505": entry(set(rb.inchikey_first_block), "development-exposed", "raw mzML scans (MSV000091754) used for Phase 1 inter-mixture repeatability; 39 compounds"),
}
v2 = {"V2-DEVELOPMENT-POPULATION": {"n_keys": int(len(cov)), "connectivity_keys_sha256": canonical_key_hash(cov.group_key),
      "definition": "LCSB-DEV union WUR-DEV-ANALYSIS union WUR-DEV-HOLD union WUR-SEALED, positive mode, full six-rung WUR ladder or LCSB dev trajectory",
      "historical_class_counts": cov.historical_class.value_counts().to_dict()}}
assert set(cov.group_key) == lcsb_dev | set(hold_d["analysis"]["connectivity_keys"]) | set(hold_d["hold"]["connectivity_keys"]) | sealed
assert not (set(cov.group_key) - sealed) & conf
external = {
 "MultiMS2": {"exposure_class": "potential-future-external-not-outcome-accessed", "doi": "10.1093/gigascience/giag069", "status": "outcome-blind identity/metadata census only; no peak, mu or residual may be read before a committed final-candidate freeze"},
 "MSnLib": {"exposure_class": "potential-future-external-not-outcome-accessed", "doi": "10.1038/s41592-025-02813-0", "status": "conditional backup; not accessed"},
 "MetaSci": {"exposure_class": "potential-future-external-not-outcome-accessed", "doi": "10.25983/3011933", "status": "conditional calibration/mechanism panel; not accessed"},
 "BMDMS-NP": {"exposure_class": "potential-future-external-not-outcome-accessed", "doi": "10.1016/j.phytochem.2020.112427", "status": "conditional backup; not accessed"},
 "MassBank/MoNA contributor cohorts (non-LCSB)": {"exposure_class": "potential-future-external-not-outcome-accessed", "status": "not accessed; the LCSB contributor is exposed"},
}
spectra = {"wur_pos_accepted_spectra_rows": 12432, "wur_pos_cells": 6060,
           "note": "the WUR combined library repeats sub-library spectra with identical SpectrumId and bytes: 5,580 cells are two archive copies of one acquisition, 234 cells one row, 222 cells carry 2-5 distinct acquisitions and in 41 of the 42 affected keys those are different stereoisomers or E/Z isomers of one connectivity key, not technical repeats"}
out = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "environment": environment_provenance(ROOT),
       "populations": pops, "v2": v2, "external_candidates": external, "spectra": spectra}
(ART / "wur_v2" / "exposure_manifest.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print(json.dumps({k: (v["exposure_class"], v["n_keys"]) for k, v in pops.items()}, indent=1)); print(v2)
