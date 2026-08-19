# MURU v2 — Modal Infrastructure (Sidecar + Rescue), 2026-08-19

**Status: INFRASTRUCTURE LIVE AND VERIFIED.** Both the sidecar environment
report and the 96 GiB rescue readiness probe ran live on Modal and
returned real results (see §5). The rescue-authorization safety gate was
also verified live: `rescue_execute` still refuses to run with no
`muru-rescue-authorization` Secret present. No scientific code has run —
readiness and sidecar jobs are structurally incapable of it (see §3–4).
This document is operational infrastructure, not a scientific finding, and
makes no scientific claim.

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
| [`modal_app.py`](scripts/cloud_modal/modal_app.py) | Three Modal Apps, two images, 10 functions, 6 CLI entrypoints. |
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
| `cost_ledger_total` | sidecar | — | Reads the shared cost ledger. |

### 2.3 Checkpointing

Shared Modal Volume **`muru-modal-checkpoints`**, mounted at
`/checkpoints` in every function:

- `cost_ledger.jsonl` — append-only, one line per job invocation.
- `rescue_readiness_manifest.json` — latest readiness-probe result.
- `rescue/<run_id>/state.json` — `started`/`completed` state; a repeated
  call with the same `run_id` that already shows `completed` short-circuits
  and returns the prior result instead of re-running (resumability).

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

## 5. Readiness status (as of 2026-08-19, live-verified)

- **Modal authentication**: ✅ live — profile `aryav-thakur`, confirmed via
  `modal app list` returning successfully against the real API.
- **`modal_app.py`**: ✅ imports cleanly, all 10 functions register across
  the 3 Apps, all Modal SDK calls checked against the installed
  `modal==1.5.4` client.
- **Sidecar readiness — PASS.** `modal run modal_app.py::report_env_sidecar`
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
  Run: https://modal.com/apps/aryav-thakur/main/ap-fdSPbr4rAIIAQuPLR8ZZwU
- **`import pysr` fails in the sidecar image — CONFIRMED.** Ran
  `python -c 'import pysr'` inside `sidecar_image` via `sidecar_run_command`
  (a real, explicit check, not inferred from the report skipping the
  import): `returncode=0` for the wrapper, actual command `RC=1`,
  `ModuleNotFoundError: No module named 'pysr'`. The structural safety
  property is not just claimed, it is exercised.
- **Rescue readiness — PASS.** `modal run modal_app.py::readiness_check`
  ran live, needing **no secret**, and returned:
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
  Run: https://modal.com/apps/aryav-thakur/main/ap-1EZKeKRVxtq1gKzIm1zP7r.
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
- **`rescue_execute` safety gate — CONFIRMED.** Invoked live with dummy
  arguments and no `muru-rescue-authorization` Secret created:
  ```
  NotFoundError: Secret 'muru-rescue-authorization' not found in
  environment 'main'. ...
  ```
  Exit code 1. No repository was cloned, no command ran — the App-level
  Secret check fails before any function body executes, because
  `rescue_execute` lives alone in `muru-v2-modal-rescue-execute`.
- **Sidecar jobs against real repo content**: ✅ ready — no setup needed.
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

### 6.1 Known limitation — checkpoint volume is not concurrency-safe

Observed live during this build: Modal Volume commits are whole-snapshot,
not merges. Running the sidecar report, the pysr-absence check, and the
rescue readiness probe close together in time caused one ledger entry
(`sidecar_run_command`) to go missing — a later commit from a different
container overwrote it rather than merging. `cost_ledger_total` and the
readiness/rescue-state files on `/checkpoints` should be treated as
approximate whenever multiple jobs run concurrently; the Modal billing
dashboard is the authoritative cost source (§7), and `rescue_execute`'s
own `run_id` resume check is unaffected as long as only one rescue job
runs at a time. This is a real gap, not a hypothetical one, and worth
fixing (e.g. moving the ledger to a `modal.Dict` instead of a Volume file)
before this infrastructure is used for anything where exact concurrent
accounting matters.

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
track this from the Modal side (subject to §6.1's concurrency caveat); the
Modal billing dashboard (https://modal.com/apps) is the authoritative
source.

**Actual observed spend from this build's live validation** (per the
ledger, itself subject to §6.1): `report_environment_sidecar` cost
$0.000009 (0.6s); `rescue_readiness_check` cost $0.0357 (112s, including
the ~2 minutes of in-container Julia precompilation noted in §5). Total
logged: **$0.0357** — negligible against the $50 budget.
