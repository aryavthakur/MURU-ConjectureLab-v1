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

### 1.3 The control ledger and the checkpoint volume

Both are created automatically on first use
(`create_if_missing=True` in `modal_app.py`), but you can create them
explicitly:

```bash
modal dict create muru-modal-control-ledger    # cost/run-status records
modal volume create muru-modal-checkpoints     # rescue_execute output only
```

The Dict is what all cost and run-status tracking actually uses now (see
§4). The Volume is mounted only on `rescue_execute`, for whatever the
caller's own `command` wants to persist.

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

Produces and prints a JSON readiness manifest (also recorded as a
`readiness` event in the `muru-modal-control-ledger` Dict, under its own
unique key — see §4.1). This proves the ~96 GiB environment can be
scheduled and reports its actual CPU/RAM/arch/Python/NumPy/SymPy/Julia/
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

Reduces every immutable `cost` entry in the `muru-modal-control-ledger`
Dict and prints the total against the stated $50 budget and the $45 soft
cap. `rescue_execute` refuses to start a new run once the ledger shows
≥$45 spent. This is a best-effort trip-wire, not a hard billing cap —
check the Modal dashboard (https://modal.com/apps) for authoritative
spend.

### Inspect the raw control ledger

```bash
modal run modal_app.py::inspect_control_ledger
modal run modal_app.py::inspect_control_ledger --event-type cost --limit 20
```

Dumps entries directly from the Dict (locally, no container needed, no
cost). Filter by `event_type` (`cost`, `readiness`, `started`,
`completed`).

### Adversarial concurrency test

```bash
modal run modal_app.py::concurrency_test --n-workers 50 --n-cross-function-calls 5
```

Fires 50+ concurrent control-ledger writes (see §4.2) and verifies zero
missing, zero duplicates, and an exact recomputed cost total. Exits
non-zero on any failure. Safe to re-run any time — it only touches its
own freshly-generated `run_id`.

---

## 3. App and image design

Three separate `modal.App` objects live in `modal_app.py`, on purpose:
Modal validates every Secret referenced anywhere in an App before that
App can sync, even to run one unrelated function in it. Splitting apps is
what makes "no secret needed for sidecar/readiness, one secret gates
execution" actually true rather than aspirational.

| App | Functions | Image | Secrets |
|---|---|---|---|
| `muru-v2-modal-sidecar` | `report_environment_sidecar`, `sidecar_verify_artifact_hashes`, `sidecar_run_tests`, `sidecar_static_analysis`, `sidecar_find_duplicate_records`, `sidecar_run_command`, `cost_ledger_total`, `_ledger_stress_probe` (test-only) | `sidecar_image` | none |
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

## 4. Checkpointing / resumability / concurrency control

**Control records (cost ledger, rescue run-status, readiness audit
entries) live in a Modal Dict, `muru-modal-control-ledger`, not a file on
a Volume.** This replaced an earlier Volume-file design after a real
concurrency defect showed up in live testing (see §4.2) — Volume commits
are whole-snapshot, not merges, so two containers writing the same file
concurrently could silently clobber each other. A Dict's `put()` is one
independent RPC per key with nothing to race on.

### 4.1 Key schema

Every event is written under its own unique, never-reused key:

```
<run_id>:<job_id>:<event_type>:<timestamp_ns>:<nonce>
```

- `run_id` — the caller's `run_id` for `rescue_execute`; an
  auto-generated UUID12 for everything else (still gives every call its
  own traceable identity even without one).
- `job_id` — the function name (`report_environment_sidecar`,
  `rescue_execute`, ...).
- `event_type` — `cost` (every job), `readiness` (the readiness probe's
  audit entry), `started`/`completed` (rescue_execute's audit trail).
- `timestamp_ns:nonce` — `time.time_ns()` plus an 8-hex-char random
  nonce, so two events can never collide on a key even under heavy
  concurrency. `put(..., skip_if_exists=True)` is a second, independent
  guarantee: if a collision ever did happen, the loser is dropped, never
  silently merged into or overwriting the winner.

There is **no shared read-modify-write aggregate counter anywhere in this
file.** The authoritative cost total (`cost_ledger_total`,
`_read_cost_ledger_total`) is computed by reducing over every immutable
`cost` entry at read time, from scratch, every call.

`rescue_execute`'s resumability uses one exception to the nonce pattern by
design: the canonical "is this run_id done" marker is written to a
**deterministic** key (`<run_id>:rescue_execute:completed:FINAL`) with
`skip_if_exists=True`, so the first container to finish a given run_id
wins that key permanently and a second concurrent attempt with the same
run_id can never overwrite it — it instead reads back and returns the
winner's own result (`race_lost_locally: true`), so both callers observe
one truth. The full nonce-keyed `started`/`completed` audit trail is
still recorded separately for every attempt.

### 4.2 Adversarial concurrency test (executed live)

`modal run modal_app.py::concurrency_test --n-workers 50` fires 50
concurrent `_ledger_stress_probe` sidecar invocations (via `.spawn()`,
not `.map()`, so every call is in flight before any result is awaited)
plus 5 concurrent `report_environment_sidecar` calls — two genuinely
distinct sidecar functions writing to the ledger in the same overlapping
window — then independently re-reads the raw Dict and verifies:

```json
{
  "n_submitted": 50, "n_persisted": 50,
  "missing_worker_ids": [], "duplicate_worker_ids": [], "unexpected_worker_ids": [],
  "expected_total_usd": 0.000196, "persisted_total_usd": 0.000196,
  "total_matches_exactly": true,
  "cross_function_calls_ok": true, "cross_function_n_results": 5,
  "RESULT": "PASS"
}
```

50 submitted, 50 persisted, zero missing, zero duplicates, exact
independently-recomputed total, both functions' concurrent writes intact.
Run this again any time to re-verify: it only touches its own
freshly-generated `run_id`, never any other entry.

### 4.3 What the Volume still does

`/checkpoints` (the `muru-modal-checkpoints` Volume) is now mounted **only
on `rescue_execute`**, purely as an immutable per-run output directory —
`/checkpoints/rescue/<run_id>/output/` — for whatever the caller's own
`command` wants to persist. No control record is written there by this
file anymore. Two different `run_id`s never share a path, so as long as
`run_id` is unique per rescue attempt (which the Dict-based completion
marker also depends on), no two containers ever modify the same file
here. True mid-command checkpointing for whatever `rescue_execute` runs
still depends on that command writing its own progress — this wrapper
checkpoints *around* the command, not inside someone else's process.

### 4.4 Residual limitation

None known for the control ledger itself after §4.2's live test. The one
remaining, explicitly out of this file's control: if a future sidecar or
rescue job is given a `command` that writes to a *shared* path inside
`/checkpoints/rescue/<run_id>/output/` from multiple concurrent
sub-processes of its own, that's the command's own concurrency problem,
not something this wrapper can prevent — the guidance for any such
command is the same as §2's rule: give every concurrent writer its own
immutable output path, never a shared mutable file.

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
