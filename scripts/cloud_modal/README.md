# MURU v2 — Modal External Compute Layer

Infrastructure-only. See `MURU_V2_MODAL_INFRASTRUCTURE.md` at the repo root
for the full governance writeup (scope, safety gates, cost). This README is
the operational how-to.

Modal is authorized for exactly three roles:

1. a non-scientific **sidecar** — hashing, schema validation, test suites,
   static analysis, provenance checks, report generation;
2. a **high-memory rescue** environment, gated behind explicit
   authorization, for when the frozen protocol permits larger-host
   resumption;
3. prospective **E6 compute**, only if the main scientific Claude session
   later authorizes it.

Primary scientific execution stays on the existing Google Cloud VM in
another session. Nothing here runs a Stage 1 scientific search.

---

## 1. One-time setup

### 1.1 Authenticate Modal

Already done for this account (`aryav-thakur` profile, confirmed live
against the API with `modal app list`). If you ever need to re-auth on a
new machine:

```bash
modal token new
```

This opens a browser to link the CLI to your Modal account and writes
`~/.modal.toml`. No credentials are ever typed into chat or handled by
Claude — this is a browser OAuth flow you run yourself.

### 1.2 Create the one required Modal Secret

`aryavthakur/MURU-ConjectureLab-v1` is a **public** repository, so every
clone in `modal_app.py` uses plain anonymous HTTPS — no GitHub token is
needed or used anywhere in this infrastructure, for either the sidecar or
the rescue image.

Only one secret is required, and it holds a value this infrastructure
code never sees or sets. Run this yourself in a terminal:

```bash
# The rescue-job authorization passphrase. Only the main scientific Claude
# session (or you) should know this value — it is the gate that keeps
# rescue_execute from running without explicit sign-off.
modal secret create muru-rescue-authorization PASSPHRASE=<a-passphrase-you-choose>
```

This is the *only* place this secret is required: it belongs to its own
Modal App (`muru-v2-modal-rescue-execute`, see §3 below), so sidecar jobs
and the rescue *readiness* probe run with no secrets at all. You do not
need to create this secret to use anything except `rescue_execute`.

### 1.3 Create the checkpoint volume

Created automatically on first use (`create_if_missing=True` in
`modal_app.py`), but you can create it explicitly:

```bash
modal volume create muru-modal-checkpoints
```

---

## 2. Everyday commands

All commands run from `scripts/cloud_modal/`.

### Report the environment (Task 2)

```bash
# Lean image — no Julia/PySR
modal run modal_app.py::report_env_sidecar

# Full image — with Julia/PySR
modal run modal_app.py::report_env_full
```

### Run the test suite against an exact commit (sidecar)

```bash
modal run modal_app.py::run_tests --commit-sha <sha> --pytest-args "-q tests/"
```

### Verify artifact hashes (sidecar)

```bash
cat > /tmp/expected_hashes.json <<'EOF'
{"results/e6/some_artifact.json": "abc123...sha256"}
EOF
modal run modal_app.py::verify_hashes --commit-sha <sha> --hashes-json-path /tmp/expected_hashes.json
```

### Verify the sidecar image cannot run PySR

```bash
modal run modal_app.py::verify_pysr_absent
```

Explicitly runs `python -c 'import pysr'` inside `sidecar_image` and
prints the result. Expected: `ModuleNotFoundError: No module named 'pysr'`
— confirmed live 2026-08-19.

### Other sidecar jobs (invoke via `modal.Function.lookup` or the Modal
Python client, or wrap with a new `@sidecar_app.local_entrypoint` as
needed):

- `sidecar_static_analysis(commit_sha, command)` — default is a
  syntax-only `py_compile` sweep.
- `sidecar_find_duplicate_records(commit_sha, glob_pattern)` — hash-based
  duplicate/torn-record detection.
- `sidecar_run_command(commit_sha, command)` — generic runner for schema
  validation, critic-bundle construction, report generation,
  expression-index prep, or provenance checks whose exact invocation the
  main scientific session supplies. Runs in `sidecar_image`, which has no
  Julia/PySR installed, so it cannot execute a symbolic-regression search
  no matter what command string it is given.

### Rescue readiness (Task 4 — no scientific code runs)

```bash
modal run modal_app.py::readiness_check
```

Produces and prints a JSON readiness manifest (also written to
`/checkpoints/rescue_readiness_manifest.json` on the
`muru-modal-checkpoints` volume). This proves the ~96 GiB environment can
be scheduled and reports its actual CPU/RAM/arch/Python/NumPy/SymPy/Julia/
PySR versions. **It does not clone the repo or run any repo code.**

### Rescue execution — gated, do not invoke without explicit sign-off

`rescue_execute` is not wired to a bare CLI entrypoint on purpose — it
takes five required arguments (`commit_sha`, `work_set_manifest_sha256`,
`authorization_phrase`, `command`, `run_id`) that must come from the main
scientific session's explicit instruction, not be guessed or defaulted
here. Invoke it with the Modal Python client or `modal run` with a small
wrapper script once those five values are in hand — see
`MURU_V2_MODAL_INFRASTRUCTURE.md` §4 for the exact invocation contract.

### Cost report

```bash
modal run modal_app.py::cost_report
```

Reads the shared JSONL ledger on the checkpoint volume and prints total
estimated spend against the stated $50 budget and the $45 soft cap.
`rescue_execute` refuses to start a new run once the ledger shows ≥$45
spent. This is a best-effort trip-wire, not a hard billing cap — check the
Modal dashboard (https://modal.com/apps) for authoritative spend.

---

## 3. App and image design

Three separate `modal.App` objects live in `modal_app.py`, on purpose:
Modal validates every Secret referenced anywhere in an App before that
App can sync, even to run one unrelated function in it. Splitting apps is
what makes "no secret needed for sidecar/readiness, one secret gates
execution" actually true rather than aspirational.

| App | Functions | Image | Secrets |
|---|---|---|---|
| `muru-v2-modal-sidecar` | `report_environment_sidecar`, `sidecar_verify_artifact_hashes`, `sidecar_run_tests`, `sidecar_static_analysis`, `sidecar_find_duplicate_records`, `sidecar_run_command`, `cost_ledger_total` | `sidecar_image` | none |
| `muru-v2-modal-rescue-readiness` | `report_environment_full`, `rescue_readiness_check` | `full_image` | none |
| `muru-v2-modal-rescue-execute` | `rescue_execute` (only) | `full_image` | `muru-rescue-authorization` |

- `sidecar_image`: `debian_slim` (Python 3.13) + git + the pinned packages
  in `requirements_sidecar.txt` (everything in the repo's
  `requirements.lock.txt` except `juliacall`, `juliapkg`, `pysr`). No
  Julia is ever installed in this image.
- `full_image`: `sidecar_image` + `juliacall`/`juliapkg`/`pysr`, with the
  Julia toolchain install forced at **image build time** (via
  `run_commands("python -c 'import juliacall'")`) so a cold container
  doesn't re-download Julia on first call.

Both images are commit-independent: the repo is cloned and checked out to
an exact SHA **inside each function call**, not baked into the image. One
build serves any number of commits. `rescue_execute` living alone in its
own App is also a safety property: nothing else in that App could ever
run instead of it, so getting past the secret gate only ever grants the
one narrowly-defined capability, never anything broader.

---

## 4. Checkpointing / resumability

All jobs write to the shared `muru-modal-checkpoints` Modal Volume mounted
at `/checkpoints`:

- `cost_ledger.jsonl` — append-only cost-accounting log, every job.
- `rescue_readiness_manifest.json` — latest readiness probe result.
- `rescue/<run_id>/state.json` — rescue-job state (`started` /
  `completed`); a call with a `run_id` that already shows `completed`
  returns the prior result instead of re-running.

**Known limitation, observed live 2026-08-19**: Modal Volume commits are
whole-snapshot, not merges. Two jobs that write to `/checkpoints`
concurrently (e.g. two sidecar jobs, or a sidecar job racing the readiness
probe) can silently clobber each other's writes — during testing, a
`sidecar_run_command` ledger entry went missing after it ran concurrently
with `report_environment_sidecar` and `rescue_readiness_check`. Don't rely
on the volume for exact concurrent accounting; run cost-sensitive jobs
serially, or treat `cost_ledger_total` and the Modal billing dashboard
(https://modal.com/apps) as an approximation, not an exact count, whenever
multiple jobs have run close together in time. `rescue_execute`'s
`run_id`-based resume check is unaffected in the common case (one rescue
job at a time), but don't launch two `rescue_execute` calls with different
`run_id`s concurrently without keeping this in mind.

True mid-command checkpointing for whatever `rescue_execute` runs depends
on that command writing its own progress to `/checkpoints` — this wrapper
checkpoints *around* the command, not inside someone else's process.

---

## 5. Cost

Modal on-demand pricing (checked 2026-08-19, see
https://modal.com/pricing): $0.0000131/core/sec, $0.00000222/GiB/sec.

| Job | CPU | RAM | Approx $/hr |
|---|---|---|---|
| `report_environment_sidecar` | 1 | 1 GiB | ~$0.06 |
| `sidecar_run_tests` / `sidecar_run_command` | 2–4 | 4–8 GiB | ~$0.30–$0.90 |
| `rescue_readiness_check` / `rescue_execute` | 8 | 96 GiB | ~$3.14 |

The 96 GiB rescue tier is the expensive one — at ~$3.14/hr, the $50 budget
buys roughly **16 hours** of rescue-tier compute (or far more sidecar-tier
compute, which is 3–10x cheaper per hour). Image builds themselves are
cheap and mostly one-time (cached by Modal after the first build).
