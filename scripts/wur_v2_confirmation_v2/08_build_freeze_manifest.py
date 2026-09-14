"""MSnLib confirmation study 2, protocol V2 section 10: the machine-readable freeze manifest.

Run after the freeze document is written and before the freeze commit; the manifest and the document are then
committed together (both must be ADDED by that single commit). Records every frozen file's sha256 and the
semantic hashes that ConfirmationV2Authority recomputes."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402

V2 = "artifacts/wur_v2_confirmation_v2"
EXTRA_FROZEN = (
    f"{V2}/population/eligible_scaffold_groups.txt", f"{V2}/population/eligible_universe_manifest.json",
    f"{V2}/randomness/randomness_and_draw_record.json", f"{V2}/randomness/nist_beacon_pulse_raw.json",
    f"{V2}/randomness/nist_beacon_certificate.pem", f"{V2}/population/sampled_scaffold_groups.txt",
    f"{V2}/population/header_eligibility_manifest.json", f"{V2}/population/required_members.csv",
    f"{V2}/freeze/novelty_bins.json", f"{V2}/freeze/novelty_bins_per_compound.csv",
    f"{V2}/anchor_preflight/anchor_preflight_allowlist.csv", f"{V2}/anchor_preflight/anchor_preflight_result.json",
    f"{V2}/anchor_preflight/anchor_preflight_log_audit.json", "MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2_AMENDMENT_A1.md",
    f"{V2}/randomness/nist_beacon_pulse_canonical_uri_raw.json",
    "scripts/wur_v2_confirmation_v2/10_one_look.py", "scripts/wur_v2_confirmation_v2/11_external_analysis.py",
    "src/muru/wur_v2/decode_authority.py", "src/muru/wur_v2/external_mzml.py", "src/muru/wur_v2/metrics.py",
    "src/muru/wur_v2/candidate.py", "src/muru/wur_v2/external_msnlib.py", "src/muru/wur_v2/external_multims2.py",
)


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def main() -> int:
    if not (ROOT / DA.FREEZE_DOC).is_file():
        raise SystemExit("write the freeze document first")
    elig = json.loads((ROOT / "artifacts/wur_v2_confirmation_v2/population/header_eligibility_manifest.json").read_text())
    rows = DA._rows(ROOT, DA.SCAN_ALLOWLIST)
    pop = DA._rows(ROOT, DA.POPULATION_CSV)
    hashes = {
        "candidate_hash": DA.canonical_json_sha256(json.loads((ROOT / DA.CANDIDATE_JSON).read_bytes())),
        "comparator_hash": DA.canonical_json_sha256(json.loads((ROOT / DA.COMPARATOR_JSON).read_bytes())),
        "population_key_hash": DA.sha256_lines({r["key"] for r in pop}),
        "scaffold_group_hash": DA.sha256_lines({r["scaffold_group"] for r in pop}),
        "spectrum_manifest_hash": DA.sha256_lines({f"{r['file']}:{r['spectrum_id']}" for r in rows}),
        "registry_manifest_sha256": DA.sha256_file(ROOT / DA.REGISTRY_MANIFEST),
    }
    for k in ("population_key_hash", "scaffold_group_hash", "spectrum_manifest_hash"):
        if hashes[k] != elig[k]:
            raise SystemExit(f"{k} differs from the header eligibility manifest")
    if hashes["candidate_hash"] != "11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b" or \
            hashes["comparator_hash"] != "3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32":
        raise SystemExit("candidate or comparator is not the frozen model")
    frozen = {rel: sha(rel) for rel in sorted(set(DA.REQUIRED_FROZEN) | set(EXTRA_FROZEN))}
    import numpy, pandas, rdkit, scipy, sklearn, lxml
    manifest = {
        "study_id": DA.STUDY_ID_V2, **hashes, "frozen_files": frozen,
        "n_population_compounds": len(pop), "n_population_groups": len({r["scaffold_group"] for r in pop}),
        "n_allowlisted_scans": len(rows), "n_allowlisted_files": len({r["file"] for r in rows}),
        "a0_map": {"a_WUR": -5.95552603907965, "b_WUR": 0.8618030610784555, "free_parameters": 0},
        "bootstrap": {"unit": "scaffold_group", "B": 10000, "seed": 20261011},
        "af_thresholds": {"AF_rmse": 0.20, "AF_max": 0.30, "tail_tolerance_upper95": 0.03},
        "decision_rule": "FAILED if ratio>=1.00 or AF_diff upper95>+0.03; else if ratio upper95<1.00: PRACTICALLY "
                         "MEANINGFUL if ratio<=0.95 else MODEST; else DIRECTIONALLY FAVORABLE BUT INCONCLUSIVE",
        "environment": {"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pandas.__version__,
                        "rdkit": rdkit.__version__, "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
                        "lxml": lxml.__version__},
    }
    out = ROOT / DA.FREEZE_MANIFEST
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "frozen_files"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
