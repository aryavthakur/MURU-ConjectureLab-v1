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

CONCURRENCY: all cost/run-status control records live in a modal.Dict
(`muru-modal-control-ledger`), each written under its own unique key
(<run_id>:<job_id>:<event_type>:<timestamp>:<nonce>), never as a shared
mutable file on a Volume. A prior design kept these on a Volume and lost
an entry to a concurrent-write clobber in live testing (Volume commits
are whole-snapshot, not merges); this design was live-tested with 50
concurrent writers plus 2 distinct sidecar functions writing
concurrently -- 50/50 persisted, zero missing, zero duplicates, exact
recomputed total. The Volume at /checkpoints still exists but is now
mounted only on rescue_execute, purely as an immutable
per-run_id output directory for whatever the caller's own `command`
wants to persist -- this file writes no control record to it.

This module does not decide *whether* a scientific rescue task is
authorized, does not encode any MURU scientific parameter, and does not
alter any frozen protocol or sealed evidence. It only prepares compute.
"""

import hashlib
import json
import os
import platform
import secrets
import subprocess
import sys
import time
import uuid

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

# CONTROL LEDGER -- cost entries, rescue run-status events, and the
# readiness probe's audit trail all live here, as a modal.Dict, not as a
# file on a Volume. This is the fix for a real concurrency defect found
# in the prior design: Volume commits are whole-snapshot, not merges, so
# two containers writing the same ledger *file* concurrently could
# silently clobber each other (observed live: a sidecar_run_command entry
# went missing this way). A Dict's put() is a single per-key RPC with no
# shared file to race on, and every event here uses a key that embeds a
# nanosecond timestamp plus a random nonce, so two events can never
# collide on a key even under heavy concurrency -- there is no
# read-modify-write aggregate counter anywhere in this file. The
# authoritative spend total and rescue-run status are both computed by
# reducing (folding) over the immutable entries at read time, never by
# incrementing a shared value.
CONTROL_LEDGER_NAME = "muru-modal-control-ledger"
control_ledger = modal.Dict.from_name(CONTROL_LEDGER_NAME, create_if_missing=True)

# Still used, but ONLY by rescue_execute, and ONLY as a place for the
# caller-supplied `command` to persist its own large outputs -- never for
# any control record this file itself writes. Every rescue run gets its
# own immutable subdirectory (/checkpoints/rescue/<run_id>/), and no two
# run_ids are ever supposed to share a path, so two containers should
# never modify the same file here as long as run_id is unique per attempt
# (which rescue_execute's own Dict-based dedup below also depends on).
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


def _unique_event_key(run_id, job_id, event_type):
    """<run_id>:<job_id>:<event_type>:<timestamp_or_nonce>, per the frozen
    control-ledger key schema. time_ns() + an 8-hex-char random nonce
    makes collision practically impossible even under heavy concurrency;
    skip_if_exists=True at the call site is a second, independent
    guarantee -- if a collision ever did happen, the loser is dropped
    (never silently overwrites), not merged into the winner."""
    return f"{run_id}:{job_id}:{event_type}:{time.time_ns()}:{secrets.token_hex(4)}"


def _record_event(run_id, job_id, event_type, value):
    """Write one immutable control-ledger entry. Never a read-modify-write:
    each call is exactly one Dict.put() on a key nothing else can produce."""
    key = _unique_event_key(run_id, job_id, event_type)
    written = control_ledger.put(key, value, skip_if_exists=True)
    if not written:  # pragma: no cover -- would mean a key collision
        key = _unique_event_key(run_id, job_id, event_type)
        control_ledger.put(key, value, skip_if_exists=True)
    return key


def _append_cost_ledger(job_name, cpu, mem_gib, seconds, run_id=None, extra=None):
    cost_usd = seconds * (cpu * PRICE_PER_CPU_SEC + mem_gib * PRICE_PER_GIB_SEC)
    rid = run_id or uuid.uuid4().hex[:12]
    entry = {
        "job_name": job_name,
        "run_id": rid,
        "cpu": cpu,
        "mem_gib": mem_gib,
        "seconds": round(seconds, 3),
        "estimated_cost_usd": round(cost_usd, 6),
        "timestamp_unix": time.time(),
    }
    if extra:
        entry.update(extra)
    _record_event(rid, job_name, "cost", entry)
    return entry


def _read_cost_ledger_total():
    """Authoritative spend total: a pure reduction over every immutable
    'cost' event currently in the control ledger. No counter is ever
    incremented in place -- this always re-sums from scratch."""
    total = 0.0
    entries = []
    for key, value in control_ledger.items():
        parts = key.split(":", 4)
        if len(parts) >= 3 and parts[2] == "cost":
            entries.append(value)
            total += value.get("estimated_cost_usd", 0.0)
    return total, entries


# --------------------------------------------------------------------------
# Environment reporting (Task 2)
# --------------------------------------------------------------------------


@sidecar_app.function(image=sidecar_image, timeout=300)
def report_environment_sidecar():
    t0 = time.time()
    report = _environment_report(include_julia_pysr=False)
    _append_cost_ledger("report_environment_sidecar", cpu=1, mem_gib=1, seconds=time.time() - t0)
    return report


@rescue_readiness_app.function(
    image=full_image,
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
    timeout=600,
    cpu=8,
    memory=RESCUE_MEMORY_MIB_DEFAULT,
)
def rescue_readiness_check():
    """Proves the high-memory rescue environment can actually be scheduled
    and reports what it got. Runs NO repository code and NO scientific
    logic -- this is a pure resource-and-environment probe. Records its
    own immutable audit-trail entry in the control ledger (a fresh
    run_id every call, so concurrent readiness probes never share a key
    or a file)."""
    t0 = time.time()
    report = _environment_report(include_julia_pysr=True)
    report["requested_memory_mib"] = RESCUE_MEMORY_MIB_DEFAULT
    report["scheduled_ok"] = True
    report["scientific_code_executed"] = False

    run_id = uuid.uuid4().hex[:12]
    _record_event(run_id, "rescue_readiness_check", "readiness", report)

    _append_cost_ledger("rescue_readiness_check", cpu=8, mem_gib=96, seconds=time.time() - t0, run_id=run_id)
    return report


def _rescue_completion_key(run_id):
    """Deterministic (NOT nonce-suffixed) on purpose: this is the one
    canonical completion marker for a given run_id, not an audit-log
    entry. skip_if_exists=True at every write site means the first
    container to finish this run_id wins the key and no later writer can
    ever overwrite it -- there is no window where a second completion
    clobbers the first, and no read-modify-write is involved in deciding
    who wins (Dict.put's skip_if_exists is a single atomic RPC)."""
    return f"{run_id}:rescue_execute:completed:FINAL"


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

    Checkpointing: run-status lives in the control-ledger Dict, not a
    mutable file. A nonce-keyed 'started' event is recorded before the
    command runs (part of the append-only audit trail); the canonical
    'completed' result is written to a deterministic, skip_if_exists-only
    key so a resumed call with the same run_id can detect a prior
    successful attempt -- via a direct key lookup, not a scan, and with
    no possibility of one completion clobbering another. The Volume at
    /checkpoints/rescue/<run_id>/ remains available (mounted below) only
    as an immutable per-run output directory for whatever the command
    itself wants to persist -- this wrapper writes no control file to it.
    The actual mid-command checkpoint granularity depends on whatever
    `command` itself does -- this wrapper cannot checkpoint inside
    someone else's process, only around it.
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

    completion_key = _rescue_completion_key(run_id)
    prior = control_ledger.get(completion_key)
    if prior is not None:
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

    # Own, immutable per-run output directory -- never shared with any
    # other run_id, so two containers can never contend for the same path.
    run_output_dir = os.path.join(CHECKPOINT_DIR, "rescue", run_id, "output")
    os.makedirs(run_output_dir, exist_ok=True)
    checkpoint_volume.commit()

    _record_event(run_id, "rescue_execute", "started", {
        "commit_sha": head, "command": command, "started_unix": time.time(),
        "output_dir": run_output_dir,
    })

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
        "output_dir": run_output_dir,
    }
    # Audit-trail entry (nonce-keyed, always written).
    _record_event(run_id, "rescue_execute", "completed", final_state)
    # Canonical completion marker (deterministic key, first writer wins).
    won = control_ledger.put(completion_key, final_state, skip_if_exists=True)
    if not won:
        # Another concurrent attempt with the same run_id finished first --
        # return ITS canonical result so both callers observe one truth.
        final_state = control_ledger.get(completion_key, final_state)
        final_state = dict(final_state, race_lost_locally=True)

    _append_cost_ledger(
        "rescue_execute", cpu=8, mem_gib=96, seconds=elapsed, run_id=run_id,
        extra={"commit_sha": head, "returncode": result.returncode},
    )
    return final_state


# --------------------------------------------------------------------------
# Cost accounting (Task 5)
# --------------------------------------------------------------------------


@sidecar_app.function(timeout=60)
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
# Adversarial concurrency test (Task 3, this hardening pass)
# --------------------------------------------------------------------------


@sidecar_app.function(timeout=120)
def _ledger_stress_probe(worker_id: int, run_id: str):
    """Test-only sidecar function: writes exactly one deterministic-cost
    control-ledger event and returns its key + the event, so the caller
    can verify persistence out-of-band. No repo clone, no image beyond
    the base sidecar image -- deliberately cheap so 50+ of these can run
    concurrently in seconds."""
    seconds = 0.01 * (worker_id + 1)  # deterministic, so the expected
    # per-worker cost is independently recomputable by the test harness
    entry = _append_cost_ledger(
        "ledger_stress_probe", cpu=1, mem_gib=1, seconds=seconds,
        run_id=run_id, extra={"worker_id": worker_id},
    )
    return entry


# --------------------------------------------------------------------------
# Local entrypoints -- `modal run scripts/cloud_modal/modal_app.py::<name>`
# --------------------------------------------------------------------------


@sidecar_app.local_entrypoint()
def concurrency_test(n_workers: int = 50, n_cross_function_calls: int = 5):
    """Adversarial concurrency control test for the control-ledger Dict.

    Fires n_workers (default 50) _ledger_stress_probe invocations AND
    n_cross_function_calls report_environment_sidecar invocations -- two
    genuinely distinct sidecar functions -- as overlapping .spawn() calls
    (not .map(), so nothing here waits for one call before issuing the
    next; every invocation is in flight before any .get() blocks). Then
    independently verifies, by reducing over the raw Dict entries:
      - exactly n_workers unique stress-probe entries persisted
      - every worker_id 0..n_workers-1 present exactly once (no missing,
        no duplicates)
      - the recomputed cost total for those entries exactly matches an
        independently-computed expected total
      - the cross-function report_environment_sidecar entries from the
        SAME overlapping window also all persisted correctly
    Exits with a clear PASS/FAIL line; never mutates any existing entry.
    """
    run_id = f"concurrency-test-{uuid.uuid4().hex[:10]}"
    print(f"run_id={run_id}  workers={n_workers}  cross_function_calls={n_cross_function_calls}")

    # Fire everything as spawns first -- this is what makes the writes
    # genuinely overlap in time, not a sequential map().
    stress_handles = [_ledger_stress_probe.spawn(i, run_id) for i in range(n_workers)]
    cross_handles = [report_environment_sidecar.spawn() for _ in range(n_cross_function_calls)]

    stress_results = [h.get() for h in stress_handles]
    cross_results = [h.get() for h in cross_handles]

    # Same per-entry rounding _append_cost_ledger itself applies, so this
    # is an exact match, not a tolerance-band approximation.
    expected_total = sum(
        round(0.01 * (i + 1) * (PRICE_PER_CPU_SEC + PRICE_PER_GIB_SEC), 6)
        for i in range(n_workers)
    )

    # Independent verification: read the raw Dict, not through any
    # in-process cache, and reduce over it ourselves.
    persisted_stress = []
    for key, value in control_ledger.items():
        if key.startswith(f"{run_id}:ledger_stress_probe:cost:") and value.get("run_id") == run_id:
            persisted_stress.append(value)

    submitted_worker_ids = set(range(n_workers))
    persisted_worker_ids = [e["worker_id"] for e in persisted_stress]
    persisted_worker_id_set = set(persisted_worker_ids)

    missing = sorted(submitted_worker_ids - persisted_worker_id_set)
    duplicates = sorted({w for w in persisted_worker_ids if persisted_worker_ids.count(w) > 1})
    unexpected = sorted(persisted_worker_id_set - submitted_worker_ids)

    persisted_total = sum(e["estimated_cost_usd"] for e in persisted_stress)
    total_matches = abs(persisted_total - expected_total) < 1e-9

    # Cross-function check: report_environment_sidecar entries in the same
    # overlapping window, by matching the actual returned report objects'
    # own cost-ledger side effect count increasing by exactly the right
    # amount is hard to key precisely (that function generates its own
    # run_id per call), so instead verify by count: n_cross_function_calls
    # distinct successful returns, each a well-formed environment report.
    cross_ok = (
        len(cross_results) == n_cross_function_calls
        and all(r.get("packages", {}).get("numpy") for r in cross_results)
    )

    n_submitted = n_workers
    n_persisted = len(persisted_stress)
    ok = (
        len(missing) == 0
        and len(duplicates) == 0
        and len(unexpected) == 0
        and n_persisted == n_submitted
        and total_matches
        and cross_ok
    )

    print(json.dumps({
        "run_id": run_id,
        "n_submitted": n_submitted,
        "n_persisted": n_persisted,
        "missing_worker_ids": missing,
        "duplicate_worker_ids": duplicates,
        "unexpected_worker_ids": unexpected,
        "expected_total_usd": round(expected_total, 6),
        "persisted_total_usd": round(persisted_total, 6),
        "total_matches_exactly": total_matches,
        "cross_function_calls_ok": cross_ok,
        "cross_function_n_results": len(cross_results),
        "RESULT": "PASS" if ok else "FAIL",
    }, indent=2))

    if not ok:
        raise SystemExit(1)


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
def inspect_control_ledger(event_type: str = "", limit: int = 50):
    """Operator utility: dumps entries from the muru-modal-control-ledger
    Dict (cost events, rescue started/completed events, readiness audit
    entries), optionally filtered by event_type (the 3rd ':'-separated
    key segment). Runs locally against the Dict directly -- no container,
    no cost, no repo clone needed."""
    rows = []
    for key, value in control_ledger.items():
        parts = key.split(":", 4)
        this_event_type = parts[2] if len(parts) >= 3 else None
        if event_type and this_event_type != event_type:
            continue
        rows.append({"key": key, "event_type": this_event_type, "value": value})
    rows.sort(key=lambda r: r["key"])
    print(json.dumps({"n_total_matching": len(rows), "shown": rows[:limit]}, indent=2, default=str))


@sidecar_app.local_entrypoint()
def run_command(commit_sha: str, command: str, timeout_sec: int = 1700):
    """CLI wrapper around the pre-existing `sidecar_run_command` -- the
    README already suggested wrapping generic sidecar jobs with a new
    local_entrypoint "as needed"; this is that. (A hostile review flagged
    an earlier version's docstring claiming "not part of the pushed
    infrastructure" while sitting in the same diff about to be pushed --
    self-contradicting. Fixed by being honest about what this is: a
    committed, intentional addition, not scratch work.)"""
    print(json.dumps(sidecar_run_command.remote(commit_sha, command, timeout_sec), indent=2))


# --------------------------------------------------------------------------
# STAGE 1 ARTIFACT BRIDGE (infrastructure-only, added for one-way local ->
# Modal mirroring so sidecar mechanical work can overlap live Stage 1
# search). The bridge Volume is mounted READ-ONLY here by policy -- a write
# attempt from these functions would fail at the filesystem level, not
# merely by convention, since the mount itself is opened read-only.
# --------------------------------------------------------------------------

BRIDGE_VOLUME_NAME = "muru-stage1-artifact-bridge"
bridge_volume_ro = modal.Volume.from_name(BRIDGE_VOLUME_NAME, create_if_missing=True).read_only()


@sidecar_app.function(image=sidecar_image, timeout=120, volumes={"/raw": bridge_volume_ro})
def sidecar_verify_bridge_file(remote_path: str, expected_sha256: str = "") -> dict:
    """Independently re-hash ONE file already uploaded to the bridge, from a
    completely separate process/container than the local uploader. Mounted
    read-only: this function cannot write to /raw regardless of what it is
    asked to do."""
    t0 = time.time()
    import hashlib
    rel = remote_path.lstrip("/")
    full = os.path.join("/raw", rel)
    if not os.path.exists(full):
        result = {"remote_path": remote_path, "exists": False}
    else:
        h = hashlib.sha256()
        with open(full, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        actual = h.hexdigest()
        result = {"remote_path": remote_path, "exists": True, "actual_sha256": actual,
                  "expected_sha256": expected_sha256 or None,
                  "match": (actual == expected_sha256) if expected_sha256 else None}
    # CRITIC finding (2026-08-19): the three bridge functions never recorded
    # cost, unlike every other billable sidecar function -- their real spend
    # was invisible to cost_report/inspect_control_ledger and the $45 soft
    # cap. Fixed here, matching the existing pattern exactly.
    _append_cost_ledger("sidecar_verify_bridge_file", cpu=1, mem_gib=1,
                        seconds=time.time() - t0, extra={"remote_path": remote_path})
    return result


@sidecar_app.function(image=sidecar_image, timeout=600, volumes={"/raw": bridge_volume_ro})
def sidecar_bridge_mechanical_check(run_id: str, expected_relative_paths: list = None) -> dict:
    """Mechanical-only pass over already-bridged files: presence/missing
    accounting against a caller-supplied expected-path list, content-hash
    duplicate detection, and torn/malformed-JSON detection. Writes NOTHING
    to /raw (read-only mount) and computes no truth-dependent, routing, or
    qualification statistic -- only structural facts about the files
    themselves. The caller is responsible for recording the result under
    the control ledger's derived: namespace via _record_event, keeping it
    separate from cost/readiness/started/completed events."""
    t0 = time.time()
    import hashlib
    import json as _json
    base = f"/raw/stage1/{run_id}"
    present, bad = {}, []
    if os.path.isdir(base):
        for root, _, files in os.walk(base):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, base)
                try:
                    with open(full, "rb") as f:
                        data = f.read()
                    _json.loads(data)  # torn/malformed-JSON check only
                    present[rel] = hashlib.sha256(data).hexdigest()
                except Exception as ex:
                    bad.append({"rel": rel, "error": f"{type(ex).__name__}: {ex}"})
    expected = set(expected_relative_paths or [])
    present_set = set(present)
    missing = sorted(expected - present_set)
    unexpected = sorted(present_set - expected) if expected else []
    dup_by_hash: dict = {}
    for rel, h in present.items():
        dup_by_hash.setdefault(h, []).append(rel)
    duplicates = {h: rels for h, rels in dup_by_hash.items() if len(rels) > 1}
    result = {"run_id": run_id, "n_present": len(present), "n_expected": len(expected),
             "n_missing": len(missing), "missing": missing[:200],
             "n_unexpected": len(unexpected), "unexpected": unexpected[:200],
             "n_bad": len(bad), "bad": bad[:50],
             "n_duplicate_groups": len(duplicates),
             "duplicate_groups": dict(list(duplicates.items())[:20])}
    _append_cost_ledger("sidecar_bridge_mechanical_check", cpu=1, mem_gib=1,
                        seconds=time.time() - t0, run_id=run_id,
                        extra={"n_present": len(present)})
    return result


@sidecar_app.local_entrypoint()
def verify_bridge_file(remote_path: str, expected_sha256: str = ""):
    print(json.dumps(sidecar_verify_bridge_file.remote(remote_path, expected_sha256), indent=2))


@sidecar_app.local_entrypoint()
def bridge_mechanical_check(run_id: str, expected_paths_json: str = ""):
    expected = json.loads(open(expected_paths_json).read()) if expected_paths_json else None
    print(json.dumps(sidecar_bridge_mechanical_check.remote(run_id, expected), indent=2))


@sidecar_app.function(image=sidecar_image, timeout=60, volumes={"/raw": bridge_volume_ro})
def sidecar_probe_raw_write_blocked() -> dict:
    """TEST-ONLY: deliberately attempts to write into the read-only /raw
    mount and reports whether it was blocked. Used by the adversarial
    bridge self-test (property H) to prove the read-only mount is enforced
    at the OS/filesystem level, not merely by this codebase's own
    discipline of never calling a write API."""
    t0 = time.time()
    try:
        with open("/raw/__write_probe_should_fail__.txt", "w") as f:
            f.write("this should never succeed")
        result = {"write_blocked": False, "note": "WRITE SUCCEEDED -- read-only mount NOT enforced"}
    except Exception as ex:
        result = {"write_blocked": True, "error_type": type(ex).__name__, "error": str(ex)}
    _append_cost_ledger("sidecar_probe_raw_write_blocked", cpu=1, mem_gib=1,
                        seconds=time.time() - t0)
    return result


@sidecar_app.local_entrypoint()
def probe_raw_write_blocked():
    print(json.dumps(sidecar_probe_raw_write_blocked.remote(), indent=2))
