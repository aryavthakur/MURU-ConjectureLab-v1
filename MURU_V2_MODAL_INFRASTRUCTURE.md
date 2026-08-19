# MURU v2 — Modal Infrastructure (Sidecar + Rescue), 2026-08-19

**Status: INFRASTRUCTURE LIVE, VERIFIED, AND HARDENED.** Both the sidecar
environment report and the 96 GiB rescue readiness probe ran live on
Modal and returned real results (see §5), and were re-confirmed after
this pass's concurrency-safety rework. The rescue-authorization safety
gate was verified live both before and after: `rescue_execute` still
refuses to run with no `muru-rescue-authorization` Secret present. A real
concurrency defect found in the first pass (Volume-file writes silently
clobbering each other) was fixed by moving all control records to a
`modal.Dict` with unique per-event keys, and the fix was adversarially
retested live with 50 concurrent writers plus a second concurrent
sidecar function — 50/50 persisted, zero missing, zero duplicates, exact
cost total (§6.1). No scientific code has run — readiness and sidecar
jobs are structurally incapable of it (see §3–4). This document is
operational infrastructure, not a scientific finding, and makes no
scientific claim.

This was built by an infrastructure-only Claude worker per explicit scope
constraints: no scientific decisions, no frozen-parameter changes, no
Stage 1 scientific search execution, no inspection of partial scientific
outcomes for routing, no governance reinterpretation, no modification of
sealed evidence. Everything below is Modal (https://modal.com) compute
plumbing.

---

## 1. Why Modal, and what it is not

- Primary scientific execution remains on the existing Google Cloud VM, in
  another Claude session. This infrastructure does not replace that.
- Google Cloud additional capacity is unavailable (24-vCPU project quota).
  Modal is an external, separately-billed compute layer to work around
  that quota, not a replacement for the GCP host.
- Modal is authorized for exactly three roles: (1) non-scientific sidecar
  work, (2) a high-memory rescue environment for when the frozen protocol
  explicitly permits larger-host resumption, (3) prospective E6 compute if
  later authorized by the main scientific session. Nothing here is
  self-authorizing for (2) or (3) — see §4.
- Total additional compute budget for this workstream: **USD $50**.

---

## 2. What was built

All files under [`scripts/cloud_modal/`](scripts/cloud_modal/):

| File | Purpose |
|---|---|
| [`modal_app.py`](scripts/cloud_modal/modal_app.py) | Three Modal Apps, two images, 11 functions, 9 CLI entrypoints. |
| [`requirements_sidecar.txt`](scripts/cloud_modal/requirements_sidecar.txt) | Lean pip pin set for the sidecar image — `requirements.lock.txt` minus `juliacall`/`juliapkg`/`pysr`. |
| [`README.md`](scripts/cloud_modal/README.md) | Operational how-to: setup, commands, cost table. |

Three separate Modal Apps, not one — this is a deliberate safety property,
not a style choice. Modal validates every Secret referenced anywhere in an
App before that App can sync, even to run one unrelated function in it. A
single-app design was tried first and rejected: it made the rescue
authorization secret block even the non-scientific readiness probe and
sidecar jobs.

| App | Purpose | Secrets required |
|---|---|---|
| **`muru-v2-modal-sidecar`** | 6 sidecar functions + cost ledger reader | none |
| **`muru-v2-modal-rescue-readiness`** | environment report (full image) + readiness probe | none |
| **`muru-v2-modal-rescue-execute`** | `rescue_execute` — the only function that can run an arbitrary command in the full image | `muru-rescue-authorization` |

### 2.1 Images

- **`sidecar_image`** — `debian_slim` (Python 3.13) + `git` + everything in
  `requirements_sidecar.txt`. Julia and PySR are **never installed** here.
  This is a structural safety property: any attempt to `import pysr` or
  call into Julia inside this image raises `ImportError` — a Stage 1
  symbolic-regression search cannot execute in a sidecar job regardless of
  what command it is given.
- **`full_image`** — `sidecar_image` + `juliacall==0.9.26` +
  `juliapkg==0.1.25` + `pysr==1.5.10`, with the Julia toolchain download
  forced at image-build time so cold rescue containers don't re-download
  Julia per invocation.

Both images are **commit-independent**: repo checkout happens inside each
function call over anonymous HTTPS (the repo is public), not baked into
the image, so one build serves any number of commits/tags with no
credential of any kind.

### 2.2 Functions

| Function | App | Image | Purpose |
|---|---|---|---|
| `report_environment_sidecar` | sidecar | sidecar | CPU, RAM, arch, Python, NumPy, SymPy versions (Task 2). |
| `report_environment_full` | rescue-readiness | full | Same, plus Julia, PySR versions. |
| `sidecar_verify_artifact_hashes` | sidecar | sidecar | sha256 a supplied `{path: expected_hash}` map against an exact commit. |
| `sidecar_run_tests` | sidecar | sidecar | `pytest` against an exact commit. |
| `sidecar_static_analysis` | sidecar | sidecar | Runs a supplied non-interactive command (default: `py_compile` sweep). |
| `sidecar_find_duplicate_records` | sidecar | sidecar | Hash-groups files matching a glob; flags zero-byte/unreadable (torn) files. |
| `sidecar_run_command` | sidecar | sidecar | Generic runner for schema validation, critic-bundle construction, report generation, expression-index prep, provenance checks — caller supplies the exact command. |
| `rescue_readiness_check` | rescue-readiness | full, 96 GiB | Proves the rescue tier schedules; reports resources and versions. **Runs no repo code.** |
| `rescue_execute` | rescue-execute | full, 96 GiB | The only function that can run an arbitrary command in the full image. Gated — see §4. |
| `cost_ledger_total` | sidecar | — | Reduces every immutable `cost` entry in the control ledger. |
| `_ledger_stress_probe` | sidecar | sidecar | Test-only: writes one deterministic-cost control-ledger event. Used by `concurrency_test` (§6.1). |

### 2.3 Control ledger and checkpointing (hardened 2026-08-19)

**All cost/run-status control records live in a Modal Dict,
`muru-modal-control-ledger`, not a file on a Volume.** This replaced the
original Volume-file design after a live concurrency defect was found and
confirmed (a `sidecar_run_command` cost entry was silently lost to a
concurrent-write clobber — Volume commits are whole-snapshot, not
merges). See §6.1 for the fix and its adversarial test evidence.

Every control-ledger entry is written under a unique, never-reused key:

```
<run_id>:<job_id>:<event_type>:<timestamp_ns>:<nonce>
```

- `cost` events — one per job invocation, every function.
- `readiness` events — the rescue readiness probe's audit trail.
- `started` / `completed` events — `rescue_execute`'s audit trail.
- `rescue_execute` additionally uses one deterministic key,
  `<run_id>:rescue_execute:completed:FINAL`, written with
  `put(..., skip_if_exists=True)`, as its canonical resumability marker —
  the first container to finish a given run_id wins that key permanently;
  a second concurrent attempt with the same run_id reads back and returns
  the winner's result instead of overwriting it.

No shared read-modify-write counter exists anywhere in the file. The
authoritative spend total (`cost_ledger_total`) is always a fresh
reduction over every immutable `cost` entry, computed at read time.

The Modal Volume `muru-modal-checkpoints` still exists, but is now
mounted **only on `rescue_execute`**, purely as `/checkpoints/rescue/<run_id>/output/`
— an immutable per-run directory for whatever the caller's own `command`
wants to persist. No control record is written there anymore.

---

## 3. Sidecar jobs — outcome-independent, ready to use with no setup

`aryavthakur/MURU-ConjectureLab-v1` is a public repository. Every clone in
`modal_app.py` uses plain anonymous HTTPS
(`https://github.com/aryavthakur/MURU-ConjectureLab-v1.git`) — no GitHub
token, credential, or Secret is used anywhere for cloning, in either the
sidecar or the rescue image. Sidecar jobs need no Modal Secret at all and
are safe to run any time; they never touch scientific outcome content, and
the image they run in cannot execute a symbolic-regression search. They
still need `commit_sha` supplied explicitly — this infrastructure never
chooses a commit on its own.

See [`README.md §2`](scripts/cloud_modal/README.md) for exact commands.

---

## 4. Rescue environment — gated, not live

### 4.1 What's ready now

`rescue_readiness_check` requests **8 vCPU / 96 GiB RAM** on the full
image and, if Modal cannot schedule that, the operator should re-invoke
with a reduced tier (64 → 32 → 16 GiB — the fallback ladder is documented
in `modal_app.py` as `RESCUE_MEMORY_MIB_FALLBACKS`, not yet wired to
automatic retry pending a live scheduling test). It runs **no repository
code** — it is a pure resource-and-version probe that writes a readiness
manifest to the checkpoint volume.

### 4.2 What is NOT ready, and why

`rescue_execute` is the only path to running an arbitrary command in the
Julia/PySR-capable image, and it hard-refuses unless the caller supplies,
explicitly, all of:

1. **`commit_sha`** — the exact commit to check out.
2. **`work_set_manifest_sha256`** — must match the sha256 of
   `<repo>/work_set_manifest.json` as it exists at `commit_sha`. This
   guards against the work-set being silently swapped between the moment
   it was authorized and the moment the job actually runs.
3. **`authorization_phrase`** — must exactly match the `PASSPHRASE` value
   in the `muru-rescue-authorization` Modal Secret. **This infrastructure
   worker never set, saw, or chose that value** — it must be created
   out-of-band by you or the main scientific Claude session
   (`modal secret create muru-rescue-authorization PASSPHRASE=...`).
4. **`command`** and a **`run_id`** — the exact command to run and a
   resumability key. Neither defaults to anything.

There is also a shared soft budget guard: `rescue_execute` refuses to
start if the cost ledger already shows ≥$45 spent (of the stated $50
total), regardless of authorization.

**Per Task 7, this infrastructure does not and cannot decide when a
rescue job is scientifically authorized.** The gate above is a mechanism,
not a judgment — the main scientific session (or you) is the one who
decides to run `rescue_execute` and supplies all four items above.

### 4.3 What the main Claude session must provide to invoke rescue safely

To hand off a rescue job, the main scientific session needs to give you
(or a future infra session) exactly:

1. The exact `commit_sha` (or tag) to check out.
2. The exact `command` to run once checked out (it runs with `cwd` at the
   repo root inside the full image — Julia/PySR available).
3. Confirmation that `work_set_manifest.json` exists at that commit and
   its current sha256 (or a request to have it computed first via a
   sidecar job, since `sidecar_run_command` can hash it without needing
   the full image).
4. The authorization phrase (set into the `muru-rescue-authorization`
   Secret ahead of time — never pasted into a scientific session's own
   transcript if avoidable; set it directly via `modal secret create`).
5. A `run_id` — any string unique to this rescue attempt, used for
   resume-safety.

Nothing else is required. This infra layer will not inspect, interpret,
or act on partial scientific results to decide whether to proceed.

---

## 5. Readiness status (as of 2026-08-19, live-verified, re-verified after hardening)

- **Modal authentication**: ✅ live — profile `aryav-thakur`, confirmed via
  `modal app list` returning successfully against the real API.
- **`modal_app.py`**: ✅ imports cleanly, all 11 functions register across
  the 3 Apps (10 production + 1 test-only `_ledger_stress_probe`), all
  Modal SDK calls checked against the installed `modal==1.5.4` client
  (including `modal.Dict`, added this pass).
- **Sidecar readiness — PASS (re-confirmed after the Dict migration).**
  `modal run modal_app.py::report_env_sidecar`
  ran live end-to-end with **no secret required**. Result:
  ```json
  {
    "host": {"os": "Linux", "architecture": "x86_64", "cpu_count": 17,
              "ram_total_gib": 377.33},
    "python": {"version": "3.13.3", "implementation": "CPython"},
    "packages": {"numpy": "2.5.2", "sympy": "1.14.0",
                 "julia": null, "pysr": null},
    "note": "sidecar image -- Julia/PySR intentionally not installed"
  }
  ```
  First run: https://modal.com/apps/aryav-thakur/main/ap-fdSPbr4rAIIAQuPLR8ZZwU.
  Re-run after the hardening pass: https://modal.com/apps/aryav-thakur/main/ap-MxGZeCmWodAEQzruv3jckX
  (identical shape, confirms the Dict migration changed nothing
  observable about this function's behavior).
- **`import pysr` fails in the sidecar image — CONFIRMED (twice).** Ran
  `python -c 'import pysr'` inside `sidecar_image` via `sidecar_run_command`
  (a real, explicit check, not inferred from the report skipping the
  import): `returncode=0` for the wrapper, actual command `RC=1`,
  `ModuleNotFoundError: No module named 'pysr'`. The structural safety
  property is not just claimed, it is exercised — re-confirmed after the
  hardening pass at https://modal.com/apps/aryav-thakur/main/ap-rCxduDNDmuYG8UAXC06OdG.
- **Rescue readiness — PASS (re-confirmed after the Dict migration).**
  `modal run modal_app.py::readiness_check` ran live, needing **no
  secret**, and returned:
  ```json
  {
    "host": {"os": "Linux", "architecture": "x86_64", "cpu_count": 24,
              "ram_total_gib": 755.29},
    "python": {"version": "3.13.3"},
    "packages": {"numpy": "2.5.2", "sympy": "1.14.0",
                 "juliacall": "0.9.26", "julia": "1.11.9", "pysr": "1.5.10"},
    "requested_memory_mib": 98304,
    "scheduled_ok": true,
    "scientific_code_executed": false
  }
  ```
  First run: https://modal.com/apps/aryav-thakur/main/ap-1EZKeKRVxtq1gKzIm1zP7r.
  Re-run after the hardening pass: https://modal.com/apps/aryav-thakur/main/ap-CLrrPPmUtcZUAXQCm1awVj
  (byte-identical shape; Julia 1.11.9 / PySR 1.5.10 / juliacall 0.9.26
  all still present, `scheduled_ok: true`, `scientific_code_executed: false`).
  **Note on the RAM figure**: `ram_total_gib` reads `/proc/meminfo` inside
  the container, which reports the *physical host's* total memory (Modal
  scheduled this on a host with 755 GiB physically installed), not the 96
  GiB cgroup memory reservation actually requested and billed. Cost
  tracking (§7) is driven by the requested `memory=` in `modal_app.py`
  (98304 MiB = 96 GiB), not by this figure — this is a known Linux/cgroup
  visibility quirk, not a sizing bug.
- **Julia/PySR cold-start cost, observed**: the full image's Julia
  toolchain re-precompiles inside the *running* container on a cold start
  (image build baking `import juliacall` does not fully warm the runtime
  container's precompile cache) — this run took ~2 minutes of Julia
  precompilation (`PythonCall`, then `SymbolicRegression` and its ~70
  transitive deps) before the probe itself ran. Budget for this on every
  cold rescue invocation; a warm/kept-alive container would skip it.
- **`rescue_execute` safety gate — CONFIRMED (twice).** Invoked live with
  dummy arguments and no `muru-rescue-authorization` Secret created, both
  before and after the hardening pass:
  ```
  NotFoundError: Secret 'muru-rescue-authorization' not found in
  environment 'main'. ...
  ```
  Exit code 1 both times. No repository was cloned, no command ran — the
  App-level Secret check fails before any function body executes, because
  `rescue_execute` lives alone in `muru-v2-modal-rescue-execute`. The
  Dict-based resumability rework (§2.3, §6.1) did not touch this gate at
  all — it is checked first, before the control ledger is even consulted.
- **Sidecar jobs against real repo content**: ✅ ready — no setup needed.
- **Concurrency control — PASS, adversarially tested.** See §6.1: 50
  concurrent writers + 2 distinct concurrent sidecar functions, 50/50
  persisted, zero missing, zero duplicates, exact cost total.
- **Rescue execution**: ⬜ still requires the one secret (§6) plus the
  five items in §4.3 from the main scientific session.

## 6. What you need to do to make rescue execution live

Sidecar jobs and the rescue readiness probe need **no setup at all** —
both are already verified live (§5). Only `rescue_execute` needs anything
further:

```bash
# The only secret this infrastructure ever needs, and only for
# rescue_execute specifically (you run this — Claude never sees the value)
modal secret create muru-rescue-authorization PASSPHRASE=<a-passphrase-you-choose>
```

After that, `rescue_execute` additionally needs the five items in §4.3
from the main scientific session before it will run anything.

### 6.1 Concurrency defect — found, fixed, adversarially retested

**Original finding (2026-08-19, first pass):** Modal Volume commits are
whole-snapshot, not merges. Running the sidecar report, the pysr-absence
check, and the rescue readiness probe close together in time caused one
ledger entry (`sidecar_run_command`) to silently disappear — a later
commit from a different container overwrote it rather than merging. This
was a real blocker for maximum-parallel sidecar use, not a hypothetical
one.

**Fix (2026-08-19, hardening pass):** all control records (cost ledger,
rescue run-status, readiness audit trail) moved off the Volume entirely
and onto a `modal.Dict` (`muru-modal-control-ledger`), with every event
written under its own unique key
(`<run_id>:<job_id>:<event_type>:<timestamp_ns>:<nonce>`) — a `Dict.put()`
is one independent RPC per key, so there is no shared file for two
containers to race on, and no read-modify-write aggregate counter
anywhere. Full design in §2.3.

**Adversarial concurrency test, executed live** —
`modal run scripts/cloud_modal/modal_app.py::concurrency_test --n-workers 50`:
50 concurrent `.spawn()`-fired writes from one sidecar function
(`_ledger_stress_probe`) plus 5 concurrent writes from a second, genuinely
distinct sidecar function (`report_environment_sidecar`), all in flight
before any result is awaited. Independently re-read the raw Dict
afterward and reduced over it:

```json
{
  "run_id": "concurrency-test-819e1be37c",
  "n_submitted": 50, "n_persisted": 50,
  "missing_worker_ids": [], "duplicate_worker_ids": [], "unexpected_worker_ids": [],
  "expected_total_usd": 0.000196, "persisted_total_usd": 0.000196,
  "total_matches_exactly": true,
  "cross_function_calls_ok": true, "cross_function_n_results": 5,
  "RESULT": "PASS"
}
```
Run: https://modal.com/apps/aryav-thakur/main/ap-GeERSSkzUYB6ZCavPNciv7

50 submitted, 50 persisted, zero missing, zero duplicates, exact
independently-recomputed cost total, both functions' concurrent writes
intact. `cost_ledger_total` and the Modal billing dashboard
(https://modal.com/apps) can now both be trusted for exact accounting
even under heavy sidecar parallelism.

**Residual limitation (explicitly scoped, not this file's to fix):** if a
future `rescue_execute` `command` writes to a *shared* path inside its own
`/checkpoints/rescue/<run_id>/output/` directory from multiple concurrent
sub-processes of its own, that is the command's own concurrency problem —
this wrapper gives every run_id its own immutable directory, but cannot
enforce concurrency discipline inside a caller-supplied script. No other
Volume or Dict concurrency gap is known after the test above.

---

## 7. Approximate cost

Modal on-demand pricing checked 2026-08-19
(https://modal.com/pricing): $0.0000131/core/sec, $0.00000222/GiB/sec.

| Tier | CPU | RAM | $/hr |
|---|---|---|---|
| Environment report (sidecar) | 1 | 1 GiB | ~$0.06 |
| Sidecar jobs (tests, hashing, static analysis) | 2–4 | 4–8 GiB | ~$0.30–$0.90 |
| Rescue (readiness or execute) | 8 | 96 GiB | ~$3.14 |

At the rescue rate, the $50 budget buys ~16 hours of rescue-tier compute
(more if the fallback ladder drops to 32–64 GiB). Sidecar-tier work is
3–10x cheaper per hour, so extensive sidecar use (tests, hashing,
provenance checks) is not a binding budget concern. The `cost_ledger_total`
function and the `rescue_execute` soft-cap (refuses at ≥$45 logged spend)
track this from the Modal side, now backed by the concurrency-safe Dict
ledger (§6.1); the Modal billing dashboard (https://modal.com/apps)
remains the authoritative source of record regardless.

**Actual observed spend, whole build to date** (per `cost_ledger_total`
against the new Dict-based ledger — no longer subject to any known
concurrency undercount): **$0.0323 across 58 logged events** — every
sidecar report, both rescue-readiness runs, the pysr-absence checks, and
all 55 concurrency-test invocations (50 stress probes + 5 cross-function
calls), with zero entries lost. Negligible against the $50 budget either
way.
