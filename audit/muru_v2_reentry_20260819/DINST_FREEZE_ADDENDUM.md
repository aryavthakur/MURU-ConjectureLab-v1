# D-INST freeze addendum: post-repair instrument hash and checkpoint unification

## 1. Why this addendum exists

`DINST_FREEZE_SHA256.txt` was written at commit `7e99830` (2026-08-19 01:04:32Z) and
records:

    5b2d2ae549241fbef993b928807a52122a7c8bc7cba73dff4eb63ee9ca71b646  MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md
    14a50d51da41a15d96f4b33ce682e6a0e0034c72aa28ec99043f41868eea005a  scripts/e2a_instrument_diagnostic.py

The **protocol** hash is unchanged and still verifies. The **tool** hash does not,
because the tool was subsequently repaired twice, on the record:

| commit | time (UTC) | change to the tool |
|---|---|---|
| `7e99830` | 01:04:32 | freeze v1 (`14a50d51`) |
| `4e36f93` | 01:25:35 | repair of D1,D2,D3,D4,D6,D9,D10 after `DINST_HOSTILE_REVIEW.md` returned FAIL |
| `479656b` | 02:45:23 | `ADDRESS_SPACE_BYTES` 8 GiB -> 6 GiB (D1 tightening) |

Executed tool hash, worktree == `HEAD`:

    a3f97e38e7efa6c760b318fc2563bcbf009e2acba604887e6d2ff7c65e65bebb  scripts/e2a_instrument_diagnostic.py

The freeze file was never updated to follow the repairs. That is a provenance gap,
and this addendum closes it rather than silently editing the frozen file.

## 2. What the repairs did and did not change

Every repair is **engineering**. The `git diff 7e99830 479656b -- scripts/e2a_instrument_diagnostic.py`
touches resource bounding, error typing, output discipline, terminal-state naming
and input hashing. It changes **no** threshold, **no** classification definition,
**no** case population, **no** denominator and **no** decision rule. The protocol
document that fixes all of those is byte-identical and still verifies against
`5b2d2ae5...`.

The one change that could in principle move a result is D1's memory bound, and it
can only move it in one direction: a **stricter** address-space limit can convert a
verdict that would have been CORRECT or INCORRECT into UNRESOLVED/MEMORY. It can
never convert UNRESOLVED into a class, and it can never flip CORRECT to INCORRECT.
So the tightening is conservative with respect to the diagnostic's own bounds.

## 3. Checkpoint unification (the reason 22 checkpoints were archived)

22 checkpoints were written between 02:42:45 and 02:55:33. The 6 GiB tightening
landed at 02:45:23. Those checkpoints therefore straddle two instrument
configurations: some were produced under an 8 GiB bound, some under 6 GiB, and the
file records do not carry the bound they were produced under.

By §2 above the disagreement is bounded and one-directional, so no *scientific*
contradiction can arise from it. But a diagnostic whose whole subject matter is
"did an instrument's resource bound manufacture a classification?" must not itself
report results measured under two different resource bounds. Mixing them would
reproduce the defect under test.

Action taken, results-blind (no verdict was inspected before deciding this):

* all 22 checkpoints moved to `_ckpt_dinst_ARCHIVED_8GB_BOUND/`, retained in full
  and still present in git history at `3eb2bd7`;
* `_ckpt_dinst/` emptied;
* Stage 0 re-executed from zero under the single frozen 6 GiB tool `a3f97e38...`.

Nothing is discarded: the archived directory is committed. Re-execution cost is a
few minutes, so there is no incentive to prefer the contaminated set.

## 4. Binding statement for the executed run

Stage 0 (D-INST) results are admissible **only** if produced by tool
`a3f97e38e7efa6c760b318fc2563bcbf009e2acba604887e6d2ff7c65e65bebb` under protocol
`5b2d2ae549241fbef993b928807a52122a7c8bc7cba73dff4eb63ee9ca71b646`, with
`ADDRESS_SPACE_BYTES = 6 GiB` and `ESCALATION_SECONDS = 1500`. Any checkpoint not
produced under that pair is archival only and enters no count, no denominator and
no terminal-state determination.

---

## 5. Incident: a null Stage 0 run caused by the wrong interpreter (recorded, not hidden)

### What happened

After the archival in §3, Stage 0 was relaunched as:

    python3 scripts/e2a_instrument_diagnostic.py --workers 6

It reported `evaluation complete: 396/396` and emitted a complete, well-formed
result object, including `TERMINAL: "D-INST-NO-WORLD-MOVED"`.

**That result was an artifact and has been discarded.** Every one of the 396
records was:

    {"verdict": "UNRESOLVED", "reason": "SUBPROCESS_DIED_rc1", "wall_seconds": 0.0}

`wall_seconds == 0.0` for all 396 is the tell: nothing was computed. The cause was
the driver interpreter. `python3` on this host resolves to `/usr/bin/python3`,
which has neither `numpy` nor the `muru` package. The driver itself only needs the
stdlib, so it started happily; but `eval_one` spawns its payload with
`sys.executable`, which inherited that same dependency-less interpreter, so every
payload died on `import numpy` before evaluating anything. The correct interpreter
is `/home/aryav_thakur/venv/bin/python3` (numpy 2.5.2, sympy 1.14.0), which the
pre-context-break runs had used.

This was an operator error on relaunch, not a protocol defect and not a defect in
the 6 GiB bound.

### What it proves about the tool (the one good outcome)

The D2 repair **held under a fault it was never designed for**. A total
environment failure was recorded as `UNRESOLVED`, never as `INCORRECT`. Had the
pre-repair tool been running, 396 environment failures would have been booked as
396 INCORRECT verdicts, silently and with a plausible-looking terminal state. The
prohibition "a timeout / OOM must never become a classification" survived contact
with a failure mode outside its design envelope.

### Two real tool defects this exposed, now repaired

* **D11 — a dead subprocess did not say why.** `eval_one` discarded `stderr` and
  recorded only `SUBPROCESS_DIED_rc{n}`. That makes an environment failure
  formally indistinguishable from a kernel OOM kill, which is *precisely the
  attribution this diagnostic exists to make*. FIX: `stderr` tail is captured into
  the record, and the reason is typed — `KERNEL_OOM_KILL` (rc -9/137),
  `ENVIRONMENT_IMPORT_FAILURE`, or `SUBPROCESS_DIED_rc{n}` otherwise.
* **D12 — no preflight.** The tool would evaluate all 396 pairs against a broken
  interpreter and emit a complete-looking null result. FIX: `preflight()` runs the
  payload's import prologue under the real `RLIMIT_AS` before any pair is
  evaluated, and **exits non-zero** if it fails. Verified: under
  `/usr/bin/python3` the tool now refuses to run at all.

Both are engineering repairs. No threshold, classification definition, case
population, denominator or decision rule is touched.

### Bound verification (the 6 GiB limit was never actually tested before)

Because every payload died at import, the 6 GiB `RLIMIT_AS` from `479656b` had
never been exercised. Measured directly under the correct interpreter, the import
prologue succeeds at every level tested down to 2 GiB:

    2GiB rc=0 OK    3GiB rc=0 OK    4GiB rc=0 OK    6GiB rc=0 OK    8GiB rc=0 OK

So 6 GiB admits the interpreter with ~3 GiB of headroom and still bounds the tail
(the pathological pair measured 44.4 GB). With 6 workers the worst-case committed
address space is 36 GiB on a 47 GB host. The frozen scientific parameter is
unchanged; only the operator's interpreter changed.

### Disposition of checkpoints

| set | n | status |
|---|---|---|
| `_ckpt_dinst_ARCHIVED_8GB_BOUND/` | 22 | archival only — produced under the superseded 8 GiB bound (§3) |
| `_ckpt_dinst_ARCHIVED_ENVFAIL/` | 396 | archival only — null records from the interpreter fault above |
| `_ckpt_dinst/` | live | the only admissible set; produced under tool `9826cefe...` with the venv interpreter |

Nothing is deleted. Both archives are committed so the incident is auditable.

### Binding amendment to §4

Stage 0 results are admissible only if produced by tool
`9826cefeb6b79a4ff8384d09b46b1169c8dd292d50cb6e102db1371035fef4cb` (v3 = v2 + D11
+ D12) under protocol `5b2d2ae5...`, with `ADDRESS_SPACE_BYTES = 6 GiB`,
`ESCALATION_SECONDS = 1500`, executed by `/home/aryav_thakur/venv/bin/python3`,
and with a passing preflight line in the run log. Any record with
`wall_seconds == 0.0` and a reason of `ENVIRONMENT_IMPORT_FAILURE` is inadmissible
by construction.

## 6. Stage 0 concurrency change, recorded

Stage 0 was started at `--workers 6` and restarted at `--workers 12` after 21 pairs had
completed. Recorded because a resource parameter changed mid-run and silence about that
would be exactly the kind of undisclosed operational drift this programme forbids.

**Why it is scientifically inert here.** Each pair is evaluated in its own subprocess under
identical bounds (`RLIMIT_AS = 6 GiB`, `ESCALATION_SECONDS = 1500`). Concurrency can only
reach a verdict through host memory pressure, i.e. by causing a kernel OOM kill that would
otherwise not occur. Measured peak RSS was **1.65 GiB per worker** against **42 GiB free**,
and **zero** OOM kills occurred at 6 workers. At 12 workers the expected footprint is
~20 GiB. Had an OOM occurred it would now be typed `KERNEL_OOM_KILL` by the D11 repair and
routed to `UNRESOLVED`, which widens the LOWER/UPPER bounds but cannot produce a label.

**Why it was necessary.** The archived 22-pair sample suggested a mean cost of ~68 s, but
that sample was biased: it consisted of the pairs that *finished first* before the run was
torn down. The live tail (six payloads simultaneously between 188 s and 516 s, against a
1500 s budget) implied 15-25 h at 6 workers on a 24-core host that was 75% idle.

**Cross-check on the discarded 8 GiB archive.** The 21 pairs re-executed under 6 GiB
reproduce the 8 GiB archive almost exactly:

    6 GiB : 0.6, 2.8, 2.9, 3.2, 3.2, 3.3, 3.4, 3.4, 3.5, 3.5, 3.9, 4.1, 19.7, 20.0, 20.4, 24.3, 33.3, 105.2, 117.3, 198.6, 266.1
    8 GiB : 0.6, 2.8, 2.8, 3.1, 3.2, 3.4, 3.5, 3.5, 3.6, 3.6, 3.9, 4.2, 19.8, 19.9, 20.3, 24.3, 33.4, 106.1, 117.0, 196.9, 262.2

with the same verdict multiset (19 INCORRECT/RESOLVED, 1 CORRECT/RESOLVED, and one pair at
`MEMORY_SIMPLIFY`). This is evidence that the 8 GiB -> 6 GiB tightening was immaterial in
practice, and it independently demonstrates run-to-run reproducibility of the instrument.
The archive remains inadmissible on process grounds regardless (section 3); it is used here
only as a consistency check, never as a count.
