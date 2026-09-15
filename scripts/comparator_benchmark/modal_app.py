"""Pinned Linux x86_64 CPU execution environments for the three comparator models (Modal).

Images (built once, content-addressed by Modal):
  fiora  : Python 3.11, torch 2.6.0 CPU, FIORA HEAD constraints.txt pins for the packages FIORA imports;
           /opt/fiora_v0.1.2 (release tag, unpatched), /opt/fiora_v0.1.2_patched (the one-character '==' -> '='
           correction only), /opt/fiora_head (e19ef82). Model files are the repo-shipped checkpoints.
  mspred : Python 3.11, ms-pred ed8311f installed with the upstream command `uv sync --extra cpu`, resolution
           bounded by UV_EXCLUDE_NEWER = the pinned commit's committer time; /ckpt/iceberg21_msg_simulation and
           /ckpt/glacier_msg are the downloaded Dropbox checkpoints.

Nothing here reads MURU data. Inputs are passed in explicitly by the local driver scripts.
"""
from __future__ import annotations

import os
from pathlib import Path

import modal

HOME = Path(os.environ.get("MURU_COMPARATORS_HOME", str(Path.home() / "muru-comparators")))
MSPRED_EXCLUDE_NEWER = "2026-09-04T05:12:22Z"   # committer time of ms-pred ed8311f

app = modal.App("muru-comparator-technical")

FIORA_PINS = [  # subset of fiora e19ef82 constraints.txt: everything fiora imports, at the pinned versions
    "numpy==2.1.3", "pandas==2.2.3", "scipy==1.15.2", "torch-geometric==2.6.1", "rdkit==2024.9.6", "dill==0.3.9",
    "treelib==1.7.1", "spectrum-utils==0.4.2", "seaborn==0.13.2", "matplotlib==3.10.1", "scikit-learn==1.6.1",
    "lightning-fabric==2.6.1", "torchmetrics==1.8.1", "regex==2024.11.6", "ipython==8.34.0", "networkx==3.4.2",
    "numba==0.61.0", "llvmlite==0.44.0", "pyteomics==4.7.5", "tqdm==4.67.1",
]

fiora_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libxrender1", "libxext6")   # system libraries required by rdkit.Chem.Draw, imported by FIORA
    .pip_install("torch==2.6.0", index_url="https://download.pytorch.org/whl/cpu")
    .pip_install(*FIORA_PINS)
    .add_local_dir(HOME / "repos/fiora_v0.1.2", "/opt/fiora_v0.1.2", ignore=[".git", "notebooks", "images", "lib_loader"])
    .add_local_dir(HOME / "repos/fiora_v0.1.2_patched", "/opt/fiora_v0.1.2_patched", ignore=["notebooks", "images", "lib_loader"])
    .add_local_dir(HOME / "repos/fiora_head", "/opt/fiora_head", ignore=[".git", "notebooks", "images", "lib_loader"])
)

mspred_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "build-essential", "libcairo2", "libxrender1", "libxext6")
    .pip_install("uv==0.8.12")
    .add_local_dir(HOME / "repos/ms-pred", "/opt/ms-pred", copy=True, ignore=[".git", "webui", "notebooks"])
    .run_commands(
        f"cd /opt/ms-pred && UV_EXCLUDE_NEWER={MSPRED_EXCLUDE_NEWER} uv sync --extra cpu",
        "cd /opt/ms-pred && uv pip freeze > /opt/mspred_freeze.txt",
    )
    .add_local_dir(HOME / "checkpoints/iceberg21_msg_simulation", "/ckpt/iceberg21_msg_simulation")
    .add_local_dir(HOME / "checkpoints/glacier_msg", "/ckpt/glacier_msg")
)


def _run(cmd: str, files: dict[str, bytes], cwd: str, env: dict | None = None, collect: list[str] | None = None) -> dict:
    import hashlib
    import platform
    import subprocess
    import tempfile

    work = Path(tempfile.mkdtemp(prefix="run_"))
    for name, data in files.items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    full_env = dict(os.environ, WORK=str(work), **(env or {}))
    r = subprocess.run(cmd, shell=True, cwd=cwd, env=full_env, capture_output=True, text=True)
    out = {}
    for rel in collect or []:
        for p in sorted(work.glob(rel)):
            out[str(p.relative_to(work))] = p.read_bytes()
    return {"cmd": cmd, "returncode": r.returncode, "stdout": r.stdout[-20000:], "stderr": r.stderr[-20000:],
            "outputs": out, "platform": platform.platform(), "machine": platform.machine(),
            "output_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in out.items()}}


@app.function(image=fiora_image, cpu=4, memory=8192, timeout=3600)
def fiora_run(cmd: str, files: dict[str, bytes], collect: list[str]) -> dict:
    return _run(cmd, files, cwd="/opt", env={"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}, collect=collect)


@app.function(image=mspred_image, cpu=4, memory=16384, timeout=3600)
def mspred_run(cmd: str, files: dict[str, bytes], collect: list[str]) -> dict:
    # torch 2.6 (the upstream `uv sync --extra cpu` resolution) defaults torch.load to weights_only=True, which rejects
    # the pathlib.PosixPath stored in the official Lightning checkpoints' hyperparameters. The documented torch
    # override restores full unpickling of these trusted upstream checkpoints; no model code is changed.
    return _run(cmd, files, cwd="/opt/ms-pred", env={"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                                                      "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"}, collect=collect)


@app.function(image=fiora_image, timeout=600)
def fiora_env() -> str:
    import subprocess
    return subprocess.run("pip freeze; python -V; uname -a", shell=True, capture_output=True, text=True).stdout


@app.function(image=mspred_image, timeout=600)
def mspred_env() -> str:
    import subprocess
    return subprocess.run("cat /opt/mspred_freeze.txt; /opt/ms-pred/.venv/bin/python -V; uname -a", shell=True,
                          capture_output=True, text=True).stdout
