"""
MURU v2 -- Modal external compute layer. INFRASTRUCTURE ONLY.

Scope (see MURU_V2_MODAL_INFRASTRUCTURE.md at repo root for the full
governance writeup):

  1. A reproducible image builder: clone the exact repo, checkout an exact
     commit/tag, install exact Python deps, install Julia/PySR only in the
     image that actually needs them, verify supplied artifact hashes,
     report the resulting environment.
  2. SIDECAR jobs: outcome-independent, non-scientific work -- hashing,
     schema validation, duplicate/torn-record detection, test suites,
     static analysis, critic-bundle construction, report generation,
     expression-index preparation, provenance checks. These run in
     `sidecar_image`, which never installs Julia or PySR, so a symbolic
     regression search cannot execute there even if something tried --
     the `import pysr` call fails.
  3. RESCUE readiness: a high-memory (default 96 GiB) environment
     definition. `rescue_readiness_check` only proves the environment can
     be built and reports its resources -- it runs no repo code and no
     scientific logic. `rescue_execute` is the only function in this file
     that can run an arbitrary supplied command in the full (Julia+PySR)
     image, and it hard-refuses unless the caller supplies commit_sha,
     work_set_manifest_sha256, and an authorization_phrase that matches a
     Modal Secret set out-of-band by the user or the main scientific
     Claude session. This file never sets, guesses, or embeds that phrase.

The repo (aryavthakur/MURU-ConjectureLab-v1) is PUBLIC: every clone in
this file uses plain anonymous HTTPS. No GitHub token or credential of any
kind is used, stored, or required anywhere here -- the only secret this
file ever reads is `muru-rescue-authorization`, and only inside
`rescue_execute`.

This module does not decide *whether* a scientific rescue task is
authorized, does not encode any MURU scientific parameter, and does not
alter any frozen protocol or sealed evidence. It only prepares compute.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time

import modal

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

REPO_URL_HTTPS = "https://github.com/aryavthakur/MURU-ConjectureLab-v1.git"

# Three separate Modal Apps, not one. This matters: Modal validates every
# Secret referenced anywhere in an App object before that App can be
# synced, even to invoke one unrelated function in it. Putting
# rescue_execute in its own App means the muru-rescue-authorization
# Secret only has to exist to run rescue_execute -- sidecar jobs and the
# (non-scientific) rescue readiness probe need zero secrets at all.
SIDECAR_APP_NAME = "muru-v2-modal-sidecar"
RESCUE_READINESS_APP_NAME = "muru-v2-modal-rescue-readiness"
RESCUE_EXECUTE_APP_NAME = "muru-v2-modal-rescue-execute"

CHECKPOINT_DIR = "/checkpoints"
WORKDIR = "/work/repo"

# Modal on-demand pricing as published at https://modal.com/pricing
# (checked 2026-08-19). Used only for the cost-accounting ledger below --
# not authoritative billing, Modal's own invoice is authoritative.
PRICE_PER_CPU_SEC = 0.0000131
PRICE_PER_GIB_SEC = 0.00000222

# Soft budget guard. The user's stated total additional compute budget for
# this workstream is USD $50. This is a best-effort trip-wire read from the
# shared cost ledger before a new job is *launched* -- it cannot stop a
# single already-running job from overshooting, so it is not a substitute
# for watching `modal app list` / the Modal billing dashboard.
SOFT_BUDGET_CAP_USD = 45.00  # leaves a $5 buffer under the stated $50 cap

# --------------------------------------------------------------------------
# Secrets and volumes (created out-of-band by the user -- see README.md)
# --------------------------------------------------------------------------

# The repo (aryavthakur/MURU-ConjectureLab-v1) is PUBLIC, so cloning uses
# plain anonymous HTTPS -- no GitHub token/secret is needed or used
# anywhere in this file, for either the sidecar or the rescue image.
rescue_auth_secret = modal.Secret.from_name(
    "muru-rescue-authorization", required_keys=["PASSPHRASE"]
)

checkpoint_volume = modal.Volume.from_name(
    "muru-modal-checkpoints", create_if_missing=True
)

# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
# Images are generic and commit-independent on purpose: the repo is cloned
# and checked out to an exact commit *inside* the function body at call
# time, not baked into the image. That lets one built image be reused
# across many commits without rebuilding, and it is what makes "checkout an
# exact supplied commit/tag" a runtime parameter rather than an image
# property.

PYTHON_VERSION = "3.13"  # matches the recorded cloud ARM64 host (3.13.5)

sidecar_image = (
    modal.Image.debian_slim(python_version=PYTHON_VERSION)
    .apt_install("git", "coreutils", "findutils")
    .pip_install_from_requirements("requirements_sidecar.txt")
)

# The full image adds the Julia/PySR triad on top of the sidecar image, and
# forces the Julia install to happen at *image build time* (not first
# invocation) by importing juliacall during the build -- this bakes Julia
# into the image layer so a cold rescue container does not need to
# re-download Julia on every invocation.
full_image = (
    sidecar_image
    .pip_install(
        "juliacall==0.9.26",
        "juliapkg==0.1.25",
        "pysr==1.5.10",
    )
    .run_commands("python -c 'import juliacall; print(juliacall.__version__)'")
)

sidecar_app = modal.App(SIDECAR_APP_NAME)
rescue_readiness_app = modal.App(RESCUE_READINESS_APP_NAME)
rescue_execute_app = modal.App(RESCUE_EXECUTE_APP_NAME)

# --------------------------------------------------------------------------
# Shared helpers (run inside the container)
# --------------------------------------------------------------------------


def _sh(cmd, cwd=None, check=True, timeout=None):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, check=False,
        capture_output=True, text=True, timeout=timeout,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {cmd}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _clone_and_checkout(commit_sha, dest=WORKDIR):
    """Clone the exact (public) repo anonymously over HTTPS and checkout
    the exact commit/tag. Verifies the resulting HEAD matches what was
    asked for -- fails loudly rather than silently running a different
    commit than requested. No credential of any kind is used here: the
    repo is public, so plain REPO_URL_HTTPS is fetchable with no auth."""
    if os.path.isdir(dest):
        _sh(f"rm -rf {dest}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    _sh(f"git clone --no-checkout {REPO_URL_HTTPS} {dest}")
    _sh(f"git fetch --depth 1 origin {commit_sha}", cwd=dest, check=False)
    # Shallow fetch of an arbitrary SHA fails on some hosts; fall back to a
    # full fetch if the shallow one did not land the commit.
    checkout = _sh(f"git checkout --detach {commit_sha}", cwd=dest, check=False)
    if checkout.returncode != 0:
        _sh("git fetch --unshallow origin || git fetch origin", cwd=dest, check=False)
        _sh(f"git checkout --detach {commit_sha}", cwd=dest)

    head = _sh("git rev-parse HEAD", cwd=dest).stdout.strip()
    if not head.startswith(commit_sha) and not commit_sha.startswith(head):
        raise RuntimeError(
            f"checkout verification failed: asked for {commit_sha}, HEAD is {head}"
        )
    return dest, head


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _environment_report(include_julia_pysr):
    import numpy
    import sympy

    try:
        cpu_count = len(os.sched_getaffinity(0))
    except AttributeError:
        cpu_count = os.cpu_count()

    mem_total_bytes = None
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total_bytes = int(line.split()[1]) * 1024
                    break
    except FileNotFoundError:
        pass

    report = {
        "timestamp_unix": time.time(),
        "host": {
            "os": platform.system(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": cpu_count,
            "ram_total_bytes": mem_total_bytes,
            "ram_total_gib": round(mem_total_bytes / (1 << 30), 2) if mem_total_bytes else None,
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "packages": {
            "numpy": numpy.__version__,
            "sympy": sympy.__version__,
        },
    }

    if include_julia_pysr:
        try:
            import juliacall
            import pysr

            jl_version = str(juliacall.Main.seval("string(VERSION)"))
            report["packages"]["juliacall"] = getattr(juliacall, "__version__", "unknown")
            report["packages"]["julia"] = jl_version
            report["packages"]["pysr"] = pysr.__version__
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["packages"]["julia_pysr_error"] = repr(exc)
    else:
        report["packages"]["julia"] = None
        report["packages"]["pysr"] = None
        report["note"] = "sidecar image -- Julia/PySR intentionally not installed"

    return report


def _append_cost_ledger(job_name, cpu, mem_gib, seconds, extra=None):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    cost_usd = seconds * (cpu * PRICE_PER_CPU_SEC + mem_gib * PRICE_PER_GIB_SEC)
    entry = {
        "job_name": job_name,
        "cpu": cpu,
        "mem_gib": mem_gib,
        "seconds": round(seconds, 3),
        "estimated_cost_usd": round(cost_usd, 6),
        "timestamp_unix": time.time(),
    }
    if extra:
        entry.update(extra)
    ledger_path = os.path.join(CHECKPOINT_DIR, "cost_ledger.jsonl")
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    checkpoint_volume.commit()
    return entry


def _read_cost_ledger_total():
    ledger_path = os.path.join(CHECKPOINT_DIR, "cost_ledger.jsonl")
    if not os.path.exists(ledger_path):
        return 0.0, []
    entries = []
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return sum(e["estimated_cost_usd"] for e in entries), entries


# --------------------------------------------------------------------------
# Environment reporting (Task 2)
# --------------------------------------------------------------------------


@sidecar_app.function(image=sidecar_image, volumes={CHECKPOINT_DIR: checkpoint_volume}, timeout=300)
def report_environment_sidecar():
    t0 = time.time()
    report = _environment_report(include_julia_pysr=False)
    _append_cost_ledger("report_environment_sidecar", cpu=1, mem_gib=1, seconds=time.time() - t0)
    return report


@rescue_readiness_app.function(
    image=full_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=600,
    cpu=2,
    memory=4096,
)
def report_environment_full():
    t0 = time.time()
    report = _environment_report(include_julia_pysr=True)
    _append_cost_ledger("report_environment_full", cpu=2, mem_gib=4, seconds=time.time() - t0)
    return report


# --------------------------------------------------------------------------
# SIDECAR jobs (Task 3) -- all run in sidecar_image, no Julia/PySR present
# --------------------------------------------------------------------------


@sidecar_app.function(
    image=sidecar_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=1800,
    cpu=2,
    memory=4096,
)
def sidecar_verify_artifact_hashes(commit_sha, expected_hashes: dict):
    """expected_hashes: {relative/path/in/repo: expected_sha256_hex}."""
    t0 = time.time()
    dest, head = _clone_and_checkout(commit_sha)
    results = {}
    for rel_path, expected in expected_hashes.items():
        full_path = os.path.join(dest, rel_path)
        if not os.path.isfile(full_path):
            results[rel_path] = {"status": "MISSING", "expected": expected, "actual": None}
            continue
        actual = _sha256_file(full_path)
        results[rel_path] = {
            "status": "MATCH" if actual == expected else "MISMATCH",
            "expected": expected,
            "actual": actual,
        }
    summary = {
        "commit_sha_requested": commit_sha,
        "commit_sha_resolved": head,
        "results": results,
        "all_match": all(r["status"] == "MATCH" for r in results.values()),
    }
    _append_cost_ledger(
        "sidecar_verify_artifact_hashes", cpu=2, mem_gib=4, seconds=time.time() - t0,
        extra={"commit_sha": head, "n_files": len(expected_hashes)},
    )
    return summary


@sidecar_app.function(
    image=sidecar_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=3600,
    cpu=4,
    memory=8192,
)
def sidecar_run_tests(commit_sha, pytest_args=""):
    t0 = time.time()
    dest, head = _clone_and_checkout(commit_sha)
    result = _sh(f"python -m pytest {pytest_args}", cwd=dest, check=False, timeout=3300)
    summary = {
        "commit_sha_resolved": head,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-4000:],
    }
    _append_cost_ledger(
        "sidecar_run_tests", cpu=4, mem_gib=8, seconds=time.time() - t0,
        extra={"commit_sha": head, "returncode": result.returncode},
    )
    return summary


@sidecar_app.function(
    image=sidecar_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=1800,
    cpu=2,
    memory=4096,
)
def sidecar_static_analysis(commit_sha, command="python -m py_compile $(git ls-files '*.py')"):
    """Runs a supplied, non-interactive static-analysis command against the
    exact checked-out commit. Defaults to a syntax-only compile check so it
    works even when no linter is pinned in requirements_sidecar.txt."""
    t0 = time.time()
    dest, head = _clone_and_checkout(commit_sha)
    result = _sh(command, cwd=dest, check=False, timeout=1700)
    summary = {
        "commit_sha_resolved": head,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-4000:],
    }
    _append_cost_ledger(
        "sidecar_static_analysis", cpu=2, mem_gib=4, seconds=time.time() - t0,
        extra={"commit_sha": head, "returncode": result.returncode},
    )
    return summary


@sidecar_app.function(
    image=sidecar_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=1800,
    cpu=2,
    memory=4096,
)
def sidecar_find_duplicate_records(commit_sha, glob_pattern):
    """Hash-based duplicate/torn-record detection: sha256's every file
    matching glob_pattern under the checked-out repo, groups by hash, and
    flags zero-byte or truncated (torn) files separately. Outcome-
    independent -- it never reads or interprets result *content*, only
    file identity and integrity."""
    import glob

    t0 = time.time()
    dest, head = _clone_and_checkout(commit_sha)
    matches = glob.glob(os.path.join(dest, glob_pattern), recursive=True)
    by_hash = {}
    torn = []
    for path in matches:
        size = os.path.getsize(path)
        if size == 0:
            torn.append({"path": os.path.relpath(path, dest), "reason": "zero_byte"})
            continue
        try:
            digest = _sha256_file(path)
        except Exception as exc:
            torn.append({"path": os.path.relpath(path, dest), "reason": f"unreadable: {exc}"})
            continue
        by_hash.setdefault(digest, []).append(os.path.relpath(path, dest))
    duplicates = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
    summary = {
        "commit_sha_resolved": head,
        "n_files_scanned": len(matches),
        "n_duplicate_groups": len(duplicates),
        "duplicates": duplicates,
        "torn_or_unreadable": torn,
    }
    _append_cost_ledger(
        "sidecar_find_duplicate_records", cpu=2, mem_gib=4, seconds=time.time() - t0,
        extra={"commit_sha": head, "n_files_scanned": len(matches)},
    )
    return summary


@sidecar_app.function(
    image=sidecar_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=1800,
    cpu=2,
    memory=4096,
)
def sidecar_run_command(commit_sha, command, timeout_sec=1700):
    """Generic sidecar runner: clones the exact commit and runs one
    non-interactive shell command in the checked-out tree. Intended for
    schema validation, critic-bundle construction, report generation,
    expression-index preparation, and provenance checks whose exact
    invocation is supplied by the caller (the main scientific session),
    not decided here. Because this runs in sidecar_image, `import pysr`
    and any Julia call fail -- this function cannot execute a Stage 1
    symbolic-regression search regardless of what command string it is
    given."""
    t0 = time.time()
    dest, head = _clone_and_checkout(commit_sha)
    result = _sh(command, cwd=dest, check=False, timeout=timeout_sec)
    summary = {
        "commit_sha_resolved": head,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-4000:],
    }
    _append_cost_ledger(
        "sidecar_run_command", cpu=2, mem_gib=4, seconds=time.time() - t0,
        extra={"commit_sha": head, "command": command, "returncode": result.returncode},
    )
    return summary


# --------------------------------------------------------------------------
# RESCUE readiness + gated execution (Task 4)
# --------------------------------------------------------------------------

RESCUE_MEMORY_MIB_DEFAULT = 96 * 1024  # ~96 GiB, per the task spec
RESCUE_MEMORY_MIB_FALLBACKS = [96 * 1024, 64 * 1024, 32 * 1024, 16 * 1024]


@rescue_readiness_app.function(
    image=full_image,
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=600,
    cpu=8,
    memory=RESCUE_MEMORY_MIB_DEFAULT,
)
def rescue_readiness_check():
    """Proves the high-memory rescue environment can actually be scheduled
    and reports what it got. Runs NO repository code and NO scientific
    logic -- this is a pure resource-and-environment probe. Writes a
    readiness manifest to the checkpoint volume and returns it."""
    t0 = time.time()
    report = _environment_report(include_julia_pysr=True)
    report["requested_memory_mib"] = RESCUE_MEMORY_MIB_DEFAULT
    report["scheduled_ok"] = True
    report["scientific_code_executed"] = False

    manifest_path = os.path.join(CHECKPOINT_DIR, "rescue_readiness_manifest.json")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(report, f, indent=2)
    checkpoint_volume.commit()

    _append_cost_ledger("rescue_readiness_check", cpu=8, mem_gib=96, seconds=time.time() - t0)
    return report


@rescue_execute_app.function(
    image=full_image,
    secrets=[rescue_auth_secret],
    volumes={CHECKPOINT_DIR: checkpoint_volume},
    timeout=6 * 3600,
    cpu=8,
    memory=RESCUE_MEMORY_MIB_DEFAULT,
)
def rescue_execute(commit_sha, work_set_manifest_sha256, authorization_phrase, command, run_id):
    """The ONLY function in this file that can run an arbitrary command in
    the full (Julia+PySR) image. Hard-refuses unless:

      1. authorization_phrase exactly matches the `PASSPHRASE` value in the
         `muru-rescue-authorization` Modal Secret (set out-of-band by the
         user or the main scientific Claude session -- this infra worker
         never sets or knows that value);
      2. work_set_manifest_sha256 matches the sha256 of
         `<repo>/work_set_manifest.json` as it exists at commit_sha (guards
         against a silently swapped work-set between authorization and
         execution);
      3. commit_sha, work_set_manifest_sha256, authorization_phrase, and
         command are all explicitly supplied by the caller -- none of them
         default to a value chosen by this file.

    Checkpointing: writes /checkpoints/rescue/<run_id>/state.json before
    and after the command runs, so a resumed call with the same run_id can
    detect a prior attempt. The actual mid-command checkpoint granularity
    depends on whatever `command` itself does -- this wrapper cannot
    checkpoint inside someone else's process, only around it.
    """
    expected_phrase = os.environ.get("PASSPHRASE")
    if not expected_phrase or authorization_phrase != expected_phrase:
        raise PermissionError(
            "rescue_execute refused: authorization_phrase does not match the "
            "muru-rescue-authorization Modal Secret. No command was run."
        )

    ledger_total, _ = _read_cost_ledger_total()
    if ledger_total >= SOFT_BUDGET_CAP_USD:
        raise RuntimeError(
            f"rescue_execute refused: cost ledger already shows "
            f"${ledger_total:.2f} spent, at or above the ${SOFT_BUDGET_CAP_USD:.2f} "
            f"soft cap (stated total budget is $50). No command was run. "
            "Raise SOFT_BUDGET_CAP_USD explicitly to override."
        )

    run_dir = os.path.join(CHECKPOINT_DIR, "rescue", run_id)
    os.makedirs(run_dir, exist_ok=True)
    state_path = os.path.join(run_dir, "state.json")
    if os.path.exists(state_path):
        with open(state_path) as f:
            prior = json.load(f)
        if prior.get("status") == "completed":
            return {"resumed": True, "prior_result": prior}

    dest, head = _clone_and_checkout(commit_sha)

    manifest_path = os.path.join(dest, "work_set_manifest.json")
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(
            f"rescue_execute refused: work_set_manifest.json not found at "
            f"{manifest_path} for commit {head}. No command was run."
        )
    actual_manifest_hash = _sha256_file(manifest_path)
    if actual_manifest_hash != work_set_manifest_sha256:
        raise ValueError(
            "rescue_execute refused: work_set_manifest_sha256 mismatch. "
            f"expected={work_set_manifest_sha256} actual={actual_manifest_hash}. "
            "No command was run."
        )

    with open(state_path, "w") as f:
        json.dump({
            "status": "started", "commit_sha": head, "command": command,
            "started_unix": time.time(),
        }, f, indent=2)
    checkpoint_volume.commit()

    t0 = time.time()
    result = _sh(command, cwd=dest, check=False, timeout=6 * 3600 - 120)
    elapsed = time.time() - t0

    final_state = {
        "status": "completed",
        "commit_sha": head,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-4000:],
        "completed_unix": time.time(),
    }
    with open(state_path, "w") as f:
        json.dump(final_state, f, indent=2)
    checkpoint_volume.commit()

    _append_cost_ledger(
        "rescue_execute", cpu=8, mem_gib=96, seconds=elapsed,
        extra={"commit_sha": head, "run_id": run_id, "returncode": result.returncode},
    )
    return final_state


# --------------------------------------------------------------------------
# Cost accounting (Task 5)
# --------------------------------------------------------------------------


@sidecar_app.function(volumes={CHECKPOINT_DIR: checkpoint_volume}, timeout=60)
def cost_ledger_total():
    total, entries = _read_cost_ledger_total()
    return {
        "total_estimated_cost_usd": round(total, 4),
        "stated_budget_usd": 50.0,
        "soft_cap_usd": SOFT_BUDGET_CAP_USD,
        "over_soft_cap": total >= SOFT_BUDGET_CAP_USD,
        "n_entries": len(entries),
    }


# --------------------------------------------------------------------------
# Local entrypoints -- `modal run scripts/cloud_modal/modal_app.py::<name>`
# --------------------------------------------------------------------------


@sidecar_app.local_entrypoint()
def report_env_sidecar():
    print(json.dumps(report_environment_sidecar.remote(), indent=2))


@rescue_readiness_app.local_entrypoint()
def report_env_full():
    print(json.dumps(report_environment_full.remote(), indent=2))


@rescue_readiness_app.local_entrypoint()
def readiness_check():
    print(json.dumps(rescue_readiness_check.remote(), indent=2))


@sidecar_app.local_entrypoint()
def cost_report():
    print(json.dumps(cost_ledger_total.remote(), indent=2))


@sidecar_app.local_entrypoint()
def run_tests(commit_sha: str, pytest_args: str = "-q"):
    print(json.dumps(sidecar_run_tests.remote(commit_sha, pytest_args), indent=2))


@sidecar_app.local_entrypoint()
def verify_hashes(commit_sha: str, hashes_json_path: str):
    with open(hashes_json_path) as f:
        expected = json.load(f)
    print(json.dumps(sidecar_verify_artifact_hashes.remote(commit_sha, expected), indent=2))


@sidecar_app.local_entrypoint()
def verify_pysr_absent(commit_sha: str = "716cf977202fad90b3091e4feff24b5677282a0b"):
    """Explicit structural-safety check: proves `import pysr` (and Julia)
    fail inside sidecar_image, not merely that the environment report
    chose not to attempt them."""
    result = sidecar_run_command.remote(
        commit_sha, "python -c 'import pysr' ; echo RC=$?"
    )
    print(json.dumps(result, indent=2))


@sidecar_app.local_entrypoint()
def inspect_checkpoints(commit_sha: str = "716cf977202fad90b3091e4feff24b5677282a0b"):
    """Operator utility: prints the raw contents of the shared checkpoint
    volume (cost ledger, readiness manifest, rescue run states). Useful
    for auditing what other Apps in this file have written, since Volume
    reads can lag a moment behind a writer in a different App/container."""
    result = sidecar_run_command.remote(
        commit_sha,
        "echo '--- cost_ledger.jsonl ---'; cat /checkpoints/cost_ledger.jsonl 2>&1; "
        "echo '--- ls /checkpoints ---'; ls -la /checkpoints/ 2>&1; "
        "echo '--- readiness manifest ---'; cat /checkpoints/rescue_readiness_manifest.json 2>&1",
    )
    print(json.dumps(result, indent=2))
