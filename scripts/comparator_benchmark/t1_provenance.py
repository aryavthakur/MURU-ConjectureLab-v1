"""T1: record immutable provenance of the downloaded comparator code, checkpoints and environments.

Hashes are computed from the files under $MURU_COMPARATORS_HOME (default ~/muru-comparators), which hold the git
clones at the pinned commits, the Dropbox archives and their safely extracted contents, and the Modal environment
freezes. Re-running verifies every recorded hash.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOME = Path(os.environ.get("MURU_COMPARATORS_HOME", str(Path.home() / "muru-comparators")))
OUT = ROOT / "artifacts/comparator_benchmark/technical/t1"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(repo: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    R = HOME / "repos"
    CK = HOME / "checkpoints"
    rec = {
        "recorded": "2026-09-14",
        "execution_platform": "Modal, Linux x86_64 (gVisor), Python 3.11.12, CPU only; images defined in scripts/comparator_benchmark/modal_app.py",
        "fiora": {
            "repository": "https://github.com/BAMeScience/fiora",
            "license": "MIT (LICENSE in repository; no separate weight licence)",
            "release_code_for_benchmark": {
                "tag": "v0.1.2", "commit": git(R / "fiora_v0.1.2", "rev-parse", "HEAD"),
                "minimal_patch": "fiora/MS/SimulationFramework.py line 124: '==' replaced by '=' (the intended assignment of the squared, max-normalised intensity); see fiora_v0.1.2_minimal_patch.diff",
                "patched_file_sha256": sha(R / "fiora_v0.1.2_patched/fiora/MS/SimulationFramework.py"),
                "unpatched_file_sha256": sha(R / "fiora_v0.1.2/fiora/MS/SimulationFramework.py"),
                "cli": "scripts/fiora-predict", "cli_sha256": sha(R / "fiora_v0.1.2_patched/scripts/fiora-predict"),
            },
            "comparison_code": {"ref": "main HEAD = v1.1.0", "commit": git(R / "fiora_head", "rev-parse", "HEAD")},
            "checkpoint": {"name": "FIORA-OS v0.1.0",
                           "files": {f.name: {"sha256": sha(f), "bytes": f.stat().st_size}
                                     for f in sorted((R / "fiora_v0.1.2_patched/models").glob("fiora_OS_v0.1.0*"))},
                           "identical_in_head_resources_models": all(
                               sha(f) == sha(R / "fiora_head/fiora/resources/models" / f.name)
                               for f in (R / "fiora_v0.1.2_patched/models").glob("fiora_OS_v0.1.0*"))},
            "excluded_checkpoint": {"name": "FIORA-OS v1.0.0",
                                    "sha256": sha(R / "fiora_head/fiora/resources/models/fiora_OS_v1.0.0.pt"),
                                    "reason": "compound-level MSnLib split not reconstructible; all PR #7 compounds in its training universe"},
        },
        "ms_pred": {
            "repository": "https://github.com/coleygroup/ms-pred",
            "license": "MIT (LICENSE in repository); checkpoints: no separate licence stated",
            "commit": git(R / "ms-pred", "rev-parse", "HEAD"),
            "commit_date": git(R / "ms-pred", "log", "-1", "--format=%cI"),
            "install": "uv sync --extra cpu (upstream README), UV_EXCLUDE_NEWER=2026-09-04T05:12:22Z",
            "iceberg_2_1": {
                "source_url": "https://www.dropbox.com/scl/fo/mcj0ngdvuj2xkhr983frb/ABGLrS8ZCeyYUWhzRfxPtRg?rlkey=rccvo52cehh75ma1yy8jji46t&dl=1",
                "readme_label": "Pretrained ICEBERG 2.1 Model Weights on MassSpecGym: msg_simulation",
                "archive_sha256": sha(CK / "iceberg21_msg_simulation.zip"),
                "files": {str(f.relative_to(CK / "iceberg21_msg_simulation")): {"sha256": sha(f), "bytes": f.stat().st_size}
                          for f in sorted((CK / "iceberg21_msg_simulation").rglob("*")) if f.is_file()},
                "note": "the archive contains only gen/ and inten_contr/ (contrastive-finetuned intensity model); no non-contrastive intensity checkpoint is published for msg_simulation, so inten_contr is the checkpoint used",
                "hparams": {p: (CK / "iceberg21_msg_simulation" / p).read_text() for p in ("gen/hparams.yaml", "inten_contr/hparams.yaml")},
            },
            "glacier": {
                "source_url": "https://www.dropbox.com/scl/fo/ta99j0mp1w7qzek5zvy3w/AFCLQNO8W2EP7ZDMOj9nxWI?rlkey=563zxtyvvhwfu1uyz6n10n2ui&dl=1",
                "readme_label": "GLACIER checkpoint trained on the MassSpecGym dataset",
                "archive_sha256": sha(CK / "glacier_msg.zip"),
                "files": {"best.ckpt": {"sha256": sha(CK / "glacier_msg/best.ckpt"), "bytes": (CK / "glacier_msg/best.ckpt").stat().st_size}},
                "paper": "arXiv:2606.29161 v1",
            },
        },
        "environment_freezes": {"fiora": "fiora_env_freeze.txt", "ms_pred": "mspred_env_freeze.txt"},
    }
    # hyperparameters embedded in the GLACIER checkpoint (read from the Lightning file header via the ms-pred image)
    shutil.copy(HOME / "runs/fiora_env.txt", OUT / "fiora_env_freeze.txt")
    shutil.copy(HOME / "runs/mspred_env.txt", OUT / "mspred_env_freeze.txt")
    shutil.copy(HOME / "fiora_v0.1.2_minimal_patch.diff", OUT / "fiora_v0.1.2_minimal_patch.diff")
    for k in rec["environment_freezes"].values():
        rec.setdefault("environment_freeze_sha256", {})[k] = sha(OUT / k)
    (OUT / "t1_provenance.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({"fiora_commit": rec["fiora"]["release_code_for_benchmark"]["commit"],
                      "ms_pred_commit": rec["ms_pred"]["commit"],
                      "iceberg": rec["ms_pred"]["iceberg_2_1"]["files"], "glacier": rec["ms_pred"]["glacier"]["files"],
                      "fiora_ckpt": rec["fiora"]["checkpoint"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
