"""Design B step 90: freeze manifest. Hashes every governing file, the sourcing frame, the ordered queues, the
exclusion sets, the pinned Design A modules and the three checkpoints (file IO only; no model is loaded)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
A = "artifacts/ce_interface_adjudication"
FILES = [
    "MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_PREREGISTRATION.md",
    "MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_PLAN.md",
    "MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_SOURCING_SCREEN.md",
    f"{A}/design_b/sourcing/eligible_universe.csv",
    f"{A}/design_b/sourcing/candidate_ledger_in_windows.csv.gz",
    f"{A}/design_b/sourcing/sourcing_screen_summary.json",
    f"{A}/design_b/sourcing/vendor_spot_check.csv",
    f"{A}/design_b/grid_support_audit.json",
    f"{A}/design_b/procurement/ordered_queues.csv",
    f"{A}/exclusion/msg15_keys_all.txt",
    f"{A}/exclusion/msg15_parent_keys_all.txt",
    f"{A}/exclusion/comparator_common_population_keys.txt",
    f"{A}/design_a/population/design_a_compounds.csv",
    "scripts/ce_interface_adjudication/scaffold_key.py",
    "scripts/ce_interface_adjudication/design_a/spectrum_similarity.py",
    "scripts/ce_interface_adjudication/design_a/30_run_predictions.py",
    "scripts/ce_interface_adjudication/design_a/40_score_spectra.py",
] + sorted(str(p.relative_to(ROOT)) for p in HERE.rglob("*.py") if "__pycache__" not in p.parts)
CHECKPOINTS = {
    "iceberg21_msg_simulation/gen/best.ckpt": "1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70",
    "iceberg21_msg_simulation/inten_contr/best.ckpt": "e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58",
    "glacier_msg/best.ckpt": "5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    files = {f: sha(ROOT / f) for f in FILES}
    assert files[C.FRAME_REL] == C.FRAME_SHA256
    ck = Path.home() / "muru-comparators/checkpoints"
    ckpt = {k: {"sha256": v, "verified_on_disk": sha(ck / k) == v} for k, v in CHECKPOINTS.items()}
    assert all(c["verified_on_disk"] for c in ckpt.values())
    import rdkit  # noqa: PLC0415
    m = {
        "study_id": C.STUDY_ID, "freeze_ref": C.FREEZE_REF,
        "statement": ("Design B freeze. No Design B MS/MS spectrum has been acquired or read, no compound has been "
                      "ordered or verified, and no prediction has been generated for any candidate."),
        "git_head_at_build": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "governing_plan_commit": "f7825e2", "sourcing_commit": "fa536bb",
        "sourcing_frame": {"path": C.FRAME_REL, "sha256": C.FRAME_SHA256, "rdkit": rdkit.__version__},
        "ordering_algorithm": "sha256(study_id|frame_sha256|stratum|parent_key) hex ascending within stratum; "
                              "walk strata N,H,L; one compound per scaffold group across strata; 66 per stratum",
        "procurement_skip_reasons": C.SKIP_REASONS,
        "models": {"ms_pred_commit": "ed8311f22958cb37f055b663b5f56c5c77a2ee33", "checkpoints": ckpt},
        "mappings": {"K1": "float(NCE)", "K2": "float(NCE) * theoretical_mh / 500.0", "K3": "floor(K2), descriptive"},
        "endpoint": {"primary": "untransformed full-spectrum cosine", "robustness": "jensen_shannon",
                     "similarity_frozen_config_sha256": C.SIMILARITY_FROZEN_CONFIG_SHA256},
        "acquisition": {"strata": C.STRATA, "nce_grid": C.NCE_GRID, "isolation_width_mz": 1.0,
                        "ms2_first_mass_mz": 50, "ms2_resolution": "instrument 15,000 at m/z 200 setting or nearest, one for all",
                        "one_compound_per_injection": True, "reinjection": "once, doubled gradient",
                        "extraction": {"xic_ppm": 5.0, "apex_fraction": 0.5, "purity_min": 0.8,
                                       "purity_half_width_mz": 0.5, "min_qualifying_scans": 3,
                                       "combination": "concatenate centroid peaks of qualifying scans"}},
        "analysis": {"reduction": "d_i = mean over 5 NCE x 2 models of cos(K1)-cos(K2)",
                     "primary": "D_div = (mean_L + mean_H)/2", "bootstrap_B": C.BOOT_B, "bootstrap_seed": C.BOOT_SEED,
                     "alpha_two_sided": C.ALPHA,
                     "identifying": "fixed sequence; I = D_div - mean_N, two-sided 95%; sign(I)=sign(D_div); sign(mean_L)=sign(mean_H)=sign(D_div)",
                     "verdicts": ["K1/K2 SUPPORTED AND IDENTIFIED", "K1/K2 FAVOURED, NOT IDENTIFIED", "INTERFACE UNRESOLVED"],
                     "descriptive_only": ["K3", "JS", "per model", "per NCE", "per stratum", "q95 support sensitivity",
                                          "reproducibility QC"]},
        "power": "about 90% at a true divergent effect of 0.0385-0.040; not designed to resolve substantially smaller effects",
        "n_files": len(files), "files": files,
    }
    out = ROOT / f"{A}/design_b/freeze/freeze_manifest.json"
    out.write_text(json.dumps(m, indent=1) + "\n")
    print(sha(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
