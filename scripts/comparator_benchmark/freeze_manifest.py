"""Write artifacts/comparator_benchmark/freeze/freeze_manifest.json: SHA-256 of every file the preregistration depends on."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md", "MURU_COMPARATOR_FEASIBILITY_AUDIT.md",
    "scripts/comparator_benchmark/modal_app.py", "scripts/comparator_benchmark/run_predictions.py",
    "scripts/comparator_benchmark/analysis.py", "scripts/comparator_benchmark/container/seeded_run.py",
    "scripts/comparator_benchmark/container/mspred_h5_to_json.py", "scripts/comparator_benchmark/container/t4_fiora.py",
    "scripts/comparator_benchmark/container/t4_mspred.py", "scripts/comparator_benchmark/t4_acceptance.py",
    "scripts/comparator_benchmark/t2_t3_smoke.py", "scripts/comparator_benchmark/t2b_seeded_determinism.py",
    "scripts/comparator_benchmark/t1_provenance.py", "tests/comparator_benchmark/test_analysis_rules.py",
    "artifacts/comparator_benchmark/population/common_population.csv",
    "artifacts/comparator_benchmark/population/common_population_keys.txt",
    "artifacts/comparator_benchmark/population/t4_summary.json", "artifacts/comparator_benchmark/population/t4_exclusions.csv",
    "artifacts/comparator_benchmark/technical/t1/t1_provenance.json",
    "artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl",
    "artifacts/comparator_benchmark/technical/t1/fiora_v0.1.2_minimal_patch.diff",
    "artifacts/comparator_benchmark/technical/t1/fiora_env_freeze.txt",
    "artifacts/comparator_benchmark/technical/t1/mspred_env_freeze.txt",
    "artifacts/comparator_benchmark/technical/t2_t3/t2_t3_report.json",
    "artifacts/comparator_benchmark/technical/t2b_seeded/t2b_report.json",
    "artifacts/comparator_feasibility/overlap_support_per_compound.csv",
]
GIT_BLOBS_AT_PR7_HEAD = [  # frozen PR #7 inputs, recorded by git object id (not opened here)
    "artifacts/wur_v2_confirmation_v2/result/measured_mu.csv",
    "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv",
    "artifacts/wur_v2_confirmation_v2/freeze/novelty_bins_per_compound.csv",
    "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json",
    "src/muru/wur_v2/metrics.py", "src/muru/wur_v2/external_multims2.py", "src/muru/wur_v2/candidate.py",
    "src/muru/wur_v2/identity.py",
]
out = {"prereg_id": "muru-v2-comparator-benchmark-1.0", "pr7_head": "f9e4ea1a79d575d8c468e290cee9508120df6f34",
       "bootstrap": {"B": 10000, "seed": 20260915}, "population_key_list_sha256": "dbdba9ca7edd4c6532b1e88b556f6fadcb582dd14d5c50a78f05c5bf04a52514",
       "sha256": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
       "git_blob_at_pr7_head": {}}
for f in GIT_BLOBS_AT_PR7_HEAD:
    line = subprocess.run(["git", "ls-tree", out["pr7_head"], f], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    out["git_blob_at_pr7_head"][f] = line[2]
    assert subprocess.run(["git", "diff", "--quiet", out["pr7_head"], "--", f], cwd=ROOT).returncode == 0, f"{f} changed since PR #7"
p = ROOT / "artifacts/comparator_benchmark/freeze/freeze_manifest.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, indent=1) + "\n")
print(p, len(out["sha256"]), "files")
