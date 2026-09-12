"""Prove the freeze commit precedes the first WUR-SEALED outcome access."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    acc = json.loads((ROOT / "artifacts" / "wur_stage3" / "first_sealed_access.json").read_text())
    freeze_commit = git("log", "-1", "--format=%H", "--diff-filter=A", "--", "MURU_WUR_FINAL_CANDIDATE_FREEZE.md")
    freeze_time = git("log", "-1", "--format=%cI", freeze_commit)
    head_at_access = acc["git_head"]
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", freeze_commit, head_at_access], cwd=ROOT).returncode == 0
    grep = subprocess.run(["git", "grep", "-l", "allow_sealed=True", "--", "src", "scripts"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    stage3_paths = [p for p in grep if not p.endswith("wur_spectra.py")]
    report = {"freeze_commit": freeze_commit, "freeze_committed_at": freeze_time,
              "first_sealed_access_utc": acc["utc"], "git_head_at_access": head_at_access,
              "git_tree_dirty_at_access": acc["git_tree_dirty"],
              "freeze_is_ancestor_of_head_at_access": ancestor,
              "files_passing_allow_sealed": stage3_paths,
              "only_stage3_passes_allow_sealed": stage3_paths == ["src/muru/wur_stage2/stage3.py"],
              "verdict": "PASS" if (ancestor and not acc["git_tree_dirty"] and stage3_paths == ["src/muru/wur_stage2/stage3.py"]) else "FAIL"}
    (ROOT / "artifacts" / "wur_stage3" / "freeze_precedes_access_audit.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    sys.exit(0 if report["verdict"] == "PASS" else 1)
