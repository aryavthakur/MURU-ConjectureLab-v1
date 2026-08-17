# E2 Execution Deviation: Rescue of the Stalled Pareto-Observability Run

**Status:** IN PROGRESS -- this document is updated in place as the rescue proceeds. Do not treat any section as final until the closing "Rescue Outcome" section at the bottom reads COMPLETE.

## 1. Original frozen commit and scope

- Branch: `exp/v2-e2-pareto-observability`
- Original frozen HEAD at time of stall: `25f589d8c496ee9f7d010ec34de1ff34edbbfd54`
- Manifest-declared scientific source hashes (`results/e2/manifest.json` -> `source_provenance.frozen_file_git_blob_hashes`, 17 files: `discovery/engine.py`, `discovery/equivalence.py`, `discovery/estimate.py`, `discovery/grammar.py`, `paper_benchmark/calibration_contract.py`, `paper_benchmark/g2_contract.py`, `paper_benchmark/generator.py`, `paper_benchmark/identity_contract.py`, `paper_benchmark/rc3_calibration_runner.py`, `paper_benchmark/rc5_adapter.py`, `paper_benchmark/rc5_case_scoring.py`, `paper_benchmark/rc5_estimate.py`, `paper_benchmark/rc5_selection.py`, `paper_benchmark/registry.py`, `paper_benchmark/seed_band_registry.py`, `paper_benchmark/structural_acceptance.py`, `paper_benchmark/truth.py`) -- **verified byte-identical (git blob hash match) before and after this rescue.** None of these 17 files is touched by the rescue diff.
- This rescue touches exactly two files, both orchestration/plumbing layers built on top of the frozen scientific primitives, neither on the frozen-hash list: `src/muru/v2_calibration/e2_classify.py` and `scripts/e2_run_shard.py`, plus one new file, `scripts/e2_shard_supervisor.sh`.

## 2. Symptoms observed at rescue start (2026-08-16, ~20:00 EDT)

Population: 540 worlds planned, sharded 3 ways (`--n-shards 3`), launched ~13:18-13:21.

| Shard | Process | Last output write | Completed |
|---|---|---|---|
| 0 | dead (no PID) | 13:18 (header only) | 0 / 180 |
| 1 | alive, progressing | 19:29:38 | 34 / 180 |
| 2 | alive, CPU-spinning | 13:28:58 (6.5h stale) | 3 / 180 |

Total completed and persisted: **37 / 540**. One recovered per-world error: `mass_affine_descriptor|c_mid|n_noiseless|r001` (shard 1) hit `PermissionError: [Errno 1] Operation not permitted` writing `candidates_shard_001.jsonl`; caught by the existing per-world `try/except` in `run_shard()`, logged to `errors_shard_001.jsonl`, and the shard continued to the next world.

## 3. Pre-intervention snapshot

Taken before any file was touched. Preserved read-only (chmod 444) at `/tmp/e2_rescue_snapshot/preserved_37/`, with a SHA-256 manifest at `/tmp/e2_rescue_snapshot/05_preserved_sha256.txt`: `manifest.json`, `retention_identity_control.json`, `worlds_shard_00{1,2}.jsonl` (the 37 persisted world outcomes), `candidates_shard_00{1,2}.jsonl`, `errors_shard_001.jsonl`, `log_shard_00{0,1,2}.txt`, `stdout_shard_{0,1,2}.log`. The 37 completed world IDs are enumerated in `/tmp/e2_rescue_snapshot/06_completed_world_ids.txt`. Git working tree and process state were also captured at that time (`/tmp/e2_rescue_snapshot/00_git_state.txt`, `03_process_state.txt`); frozen-file blob hashes were independently re-verified against the manifest at snapshot time (`04_hash_verify.txt`) and matched exactly.

## 4. Root causes

Two independent failure modes, diagnosed separately.

### 4a. Shard 2: unbounded sympy classification (the F09-class hang)

`src/muru/v2_calibration/e2_classify.py` already declared, in its own docstring, the exact mitigation this class of failure needs: *"memoise by expression string ... apply a per-expression wall-clock cap with the timeout recorded as an explicit SIMPLIFY_TIMEOUT status rather than silently becoming None."* It implemented that cap with `signal.alarm(5)` around only the `sympy.simplify()` call.

Live diagnosis (process still running, not yet killed) via macOS `sample` on PID 46829, two independent 3-second captures a minute apart: 2137/2137 and comparable sample counts, both entirely inside `_PyEval_EvalFrameDefault` -> `bounded_lru_cache_wrapper` (sympy's own `@cacheit`) -> `type_call`/`slot_tp_new`/`slot_tp_init` (sympy `Basic.__new__` object construction) -> `set_update`/`builtin_all`/`gen_iternext` (assumption/`free_symbols`-style set-building over a generator). No native/BLAS frames anywhere in either sample -- pure-Python the whole way down, and this venv has no `gmpy2` (`mpmath==1.3.0`, pure Python), so a C-extension swallowing the `SIGALRM` before it reaches the interpreter is not the mechanism. The process had produced zero output for 6.5+ hours against a largest-ever-observed legitimate single-world wall time of 7305s (~2h, shard 1's own log) -- three orders of magnitude past the declared 5s cap.

Reproduced directly: a synthetic `sympy.simplify` replacement that runs a `while` loop wrapped in `try/except Exception: continue` (mimicking sympy's own internal broad-except fallback strategies) defeats the original `_with_timeout`/SIGALRM guard completely -- the alarm fires once, is caught and discarded by the loop's own `except`, and the call never returns. This is a known, documented class of Python gotcha (a one-shot `SIGALRM`-raised exception can be caught and discarded by any `except Exception` between the raise point and the caller), not specific to this codebase.

Also found, while diagnosing: `sympy.simplify` was the *only* call in `classify_expression`'s pipeline under any timeout. `extract_effective_support`, `classify_discovered_family`, `parse_production_candidate`, `template_key`, `template_key_string`, and `coefficient_vector` -- all of which do further sympy manipulation on the same parsed expression -- ran completely unguarded. The live hang cannot be attributed with certainty to `sympy.simplify()` specifically rather than one of these; the stack signature is generic to sympy's object-construction/caching machinery, which all of these touch.

### 4b. Shard 0: silent process death, cause not fully forensically determined

No traceback anywhere (stdout capture is 0 bytes for the shard's entire life), no entry in an errors file (none was ever created for shard 0), and no macOS crash report (`~/Library/Logs/DiagnosticReports/`) in the relevant window -- consistent with an external `SIGKILL`-class termination (uncatchable, no traceback possible, no crash report generated) rather than an in-process exception or native fault. It died at the same point (immediately after the shard-assignment header, before completing world 1) on both of its two launches (once under `--n-shards 5`, once under `--n-shards 3`).

To test whether this is a reproducible code defect specific to shard 0's first-assigned world, that exact world (`mass_affine_descriptor|low|noiseless|r000`, ordinal 0) was re-run in complete isolation, in a scratch directory, under full stdout+stderr capture, using the unmodified frozen pipeline (`build_world` -> `run_seed_search` x30 -> `evaluate_world`). It progressed cleanly through at least 12 of 30 seeds (each logging normally) and then **also died silently**, with the identical signature: no traceback, no error, process simply gone. `log show` for the relevant window turned up no jetsam/memorystatus kill record either (though this may reflect log retention/redaction rather than absence of such an event; root cause is not claimed to be fully proven).

**Conclusion:** shard 0's death is not attributable to a reproducible logic defect in the per-world computation pipeline -- the same pipeline, run in isolation, completed 12+ seeds of identical work twice before also dying with the same untraceable signature. It is treated as an external-kill-class failure requiring supervision (retry-on-death), not a code fix.

## 5. Rescue diff

Both changes live entirely outside the manifest's 17 frozen scientific files. Blob hashes of all 17 re-verified unchanged after the diff (see `04_hash_verify.txt` vs. a post-diff re-run).

### 5a. `src/muru/v2_calibration/e2_classify.py`

The pre-declared cap (`SIMPLIFY_TIMEOUT_SECONDS = 5`, unchanged) and the pre-declared status name it reports on a cap-out (`SIMPLIFY_TIMEOUT`, unchanged) are now enforced at a process boundary instead of an in-process signal:

- The full per-expression computation (parse through `coefficient_vector`, i.e. everything `classify_expression` used to do directly) is unchanged in content, only relocated verbatim into `_classify_compute`.
- A single **persistent** forked worker process (`_get_worker`/`_worker_loop`) services every `classify_expression` call for the life of the shard process, exactly as the original single in-process design did -- this specifically preserves sympy's own internal `@cacheit` memoization warming up across thousands of calls over a shard's lifetime, which a first (rejected) fork-per-call design discarded, manufacturing new near-boundary timeouts that do not occur in the original code (caught by a before/after parity check, see \S6).
- The parent enforces the cap with `conn.poll(SIMPLIFY_TIMEOUT_SECONDS)` and, on timeout, `Process.kill()` (`SIGKILL`) -- unlike `SIGALRM`, this cannot be caught, delayed, or discarded by any exception handler anywhere in the call graph, including inside sympy's own internals. On a genuine timeout the (possibly wedged) worker is killed outright and a fresh one is lazily spawned on the next call; the pre-declared `SIMPLIFY_TIMEOUT` fallback record is returned, field-for-field identical in shape to the one the original code already produced for this status.
- `template_key_value` (a tuple that can hold live, deeply-nested sympy objects for pathological candidates) is never marshalled back across the worker's pipe. This field is verified dead for E2's purposes by exhaustive grep across `e2_search.py`, `e2_scoring.py`, `e2_aggregate.py`, `rc5_selection.py`, `scripts/`, and `tests/`: nothing reads `classification.template_key_value`. `FrontRow` only ever carries `template_key_repr` (the string form, sent in full, unchanged). The actual scientific consumer of template keys -- `rc5_selection.py`'s cross-seed equivalence classing (frozen, untouched) -- independently recomputes `template_key(parse_production_candidate(...))` directly from the raw expression string; it never reads anything `classify_expression` returns for this field. Pickling a large sympy tree turned out to re-trigger close to the same expensive object-construction machinery paid to build it in the first place, which was itself large enough to manufacture false timeouts on IPC cost alone for a small number of pathological-shaped candidates -- stripping this genuinely-unread field removes that cost with no observable effect anywhere in the pipeline.

Net effect for every expression whose true classification cost stays within `_classify_compute`'s own wall time (the overwhelming majority): identical output to the original code, memoization-warm performance included. For an expression that hangs anywhere in the pipeline (not just inside `sympy.simplify`): guaranteed termination at 5s instead of an unbounded hang. See \S6 for the one identified category of narrow, deliberate, and here-verified-inert exception to "identical output."

### 5b. `scripts/e2_run_shard.py`

One additive, backward-compatible CLI option: `--only-worlds-file PATH`, taking a JSON list of world IDs. When given, `run_shard` restricts its normal shard assignment to the intersection with that list; when omitted (the default, used by every non-rescue invocation), behavior is byte-identical to before. Used only to drive the replay gate (\S6) and the targeted single-world verification in \S6 -- never to change which worlds a production shard run computes.

### 5c. `scripts/e2_shard_supervisor.sh` (new)

A restart-on-death wrapper around `e2_run_shard.py`. It launches the shard, and if the process exits without a `shard N COMPLETE` marker in its log, restarts it (up to `--max-restarts`, default 20), relying entirely on `run_shard`'s own unmodified `_already_done()` checkpoint to resume rather than repeat completed worlds. It adds no new computation and makes no decision about world content, ordering, or classification -- it only notices a shard process is gone and tries again. This is the mitigation for \S4b (shard 0's untraceable external-kill-class death): whatever kills a shard process externally, a restarted shard resumes from its own persisted checkpoint.

## 6. Why this is computational, not scientific

- None of the 17 frozen-hash scientific files change (byte-identical blobs, re-verified post-diff).
- No classification, equivalence, canonicalization, retention, aggregation, family-classifier, grammar, seed, world-definition, partition, or threshold *semantics* change. `SIMPLIFY_TIMEOUT_SECONDS` keeps its pre-declared value (5); `SIMPLIFY_TIMEOUT` keeps its pre-declared meaning and is still produced by exactly the same triggering condition family (a per-expression cost cap being exceeded) -- only *where* (process boundary, not signal) and *how completely* (the whole pipeline, not just one call inside it) that pre-existing, pre-declared cap is enforced.
- `_classify_compute`'s own body is a verbatim relocation of the original `classify_expression` computation; nothing about *how* an expression is classified changed, only *where* that computation runs and how its result crosses back to the caller.
- The one identified, non-trivial behavioral difference -- documented in full below rather than glossed over -- is that the original cap only ever bounded the `sympy.simplify()` sub-call, never the full pipeline (`extract_effective_support`, `classify_discovered_family`, `template_key`, `coefficient_vector` were always unguarded). Closing that coverage gap is *necessary* to actually guarantee termination against a hang located anywhere in the pipeline (the live shard-2 hang's exact location within the pipeline was not pinned down with certainty -- see \S4a) but it does mean an expression whose `sympy.simplify()` sub-call finishes under 5s while its *total* classification cost exceeds 5s will now correctly report `SIMPLIFY_TIMEOUT`, where the original's incomplete coverage let it run unbounded and eventually report `OK`. This was caught empirically (\S7) rather than reasoned about only in the abstract, and is reported honestly against the replay gate below rather than argued around it.

## 7. Replay gate: FAILED

**Verdict: the hard replay gate did not pass. The 37-world partial run is INVALIDATED. All 540 worlds are restarted from the rescue commit under the original seed/world mapping, per the pre-registered fallback.**

### 7a. What was run

Before committing to the expensive full production replay (re-running all 30 PySR searches per world for all 37 worlds), a cheaper, decisive pre-check was run first: for every one of the 37 completed worlds, extract its front-candidate expression strings in true first-appearance order (exactly the order the real shard process encountered them) and classify each one under (a) the original pre-rescue `e2_classify.py` and (b) the rescued one, each in its own fresh process (mirroring a shard's cold start), then diff every `canonicalization_status`.

One full production single-world replay was also run end-to-end (`mass_affine_descriptor|low|noiseless|r010`, via `e2_run_shard.py --only-worlds-file`) and diffed field-for-field against the preserved original candidate rows and world-outcome row, to confirm the classify-layer check's finding actually propagates to persisted, scientifically-relevant output (it does: `n_seeds_correct_on_front` 19->18, `n_seeds_retained_correct` 9->8, and multiple candidate rows flip `support_status_vs_truth`/`family_status_vs_truth`/`g2_event`, not just internal classify-layer bookkeeping).

### 7b. A load-contention confound, isolated and controlled for

This host was, for much of the diagnosis window, extremely oversubscribed by unrelated concurrent processes (other sessions on the same shared machine -- confirmed via `ps aux`: unrelated `miniconda3`-based `multiprocessing.spawn` workers and an unrelated `pytest` run, neither started by this rescue). Load average peaked at 220 on an 8-core host. Under that load, the *first* single-world replay attempt showed cascading `SIMPLIFY_TIMEOUT`s even for trivially simple candidates (e.g. `x1 + 0.5505815`), which reproduced as `OK` in isolation and did not recur once load dropped -- consistent with OS scheduling starvation of the forked worker rather than a mechanism defect. This was verified directly: the same 272-expression true-order sequence for that world, re-run once load fell to a comparable range for both the original and rescued code, dropped from cascading failures to a small, stable, non-load-sensitive set. **The load-contention effect is real and was isolated and excluded from the finding below** -- what remains, checked under calm conditions with load consistently under ~20 on an 8-core host, is not attributable to it.

### 7c. The confirmed, reproducible finding

31 of 37 worlds checked at the classify layer under calm conditions (the remaining 6 were still checking when this section was written; see the live log for the final count -- the verdict below does not depend on them, since the gate already fails at 31/37):

- **24 worlds: 0 status flips.**
- **7 worlds: 12 total status flips, all `OK -> SIMPLIFY_TIMEOUT`, every one of them a heavily/multiply-nested candidate** (e.g. `cube(inv(square(square((91.283775 / (x1 + x0)) - -1.104039))) + 0.79000676)`, `square(square(square(square(cube(((x1 * -0.012647588) - 0.99806005) + inv(x0))))))`, `sqrt(sqrt(cube(sqrt(cube(cube(log(log(sqrt(x0))) - 0.06393476)) + square(x1)))))` -- see the full log for all 12).

Mechanistically understood, not just observed: the *original* code's `signal.alarm`-based cap only ever bounded the `sympy.simplify()` sub-call (\S4a) -- `extract_effective_support`, `classify_discovered_family`, `template_key`, `template_key_string`, and `coefficient_vector` ran completely unguarded, so an expression whose `simplify()` call finished under 5s but whose *total* classification cost ran over could complete unbounded and eventually report `OK`. The rescue's process-boundary cap necessarily bounds the *whole* `_classify_compute` pipeline -- bounding only `simplify()`, matching the original's exact (incomplete) scope, was considered and rejected: the live shard-2 hang's stack signature (\S4a) was generic to sympy's object-construction/caching machinery used throughout the pipeline, not proven to sit specifically inside `simplify()`, so narrowing the guard back to the original's scope would risk reopening the exact vulnerability this rescue exists to close.

This is a real, reproducible, understood difference in output for specific pathological-shaped candidates -- not an artifact, not noise, and not something to argue around. It is exactly the class of thing this hard gate exists to catch.

### 7d. Disposition

Per the pre-registered rule: **any confirmed scientific mismatch invalidates the 37-world partial run outright; no merging of old and new results.** The 37 completed worlds' persisted output was moved (not deleted; `git mv`-tracked where previously tracked) to `results/e2/run_PRERESCUE_INVALIDATED_2026-08-16/` -- retained only as a forensic/provenance artifact of the pre-rescue state, alongside the separately-preserved, SHA-256-recorded, read-only copy at `/tmp/e2_rescue_snapshot/preserved_37/`. **Neither is part of, or seeds, the final E2 population.**

## 8. Restart: all 540 worlds from the rescue commit

The rescue diff (\S5), the invalidated-run archive move, and this document were committed together as `4892c76` on `exp/v2-e2-pareto-observability`. `scripts/e2_preflight.py` was re-run against that commit and passed (`PREFLIGHT PASS`), regenerating `results/e2/manifest.json` with `source_provenance.head_commit = 4892c760117e460d08681f51a237345738510345` and the same 17 frozen-file blob hashes as the original manifest (byte-identical, re-verified).

All 540 worlds, 0 already done, are now running from a clean `results/e2/run/` directory, 3-way sharded exactly as the original launch (`world_ordinal % 3`, unchanged assignment logic), each shard under `scripts/e2_shard_supervisor.sh` (restart-on-death, up to 30 attempts per shard) rather than a bare, unsupervised process this time -- the direct mitigation for \S4b. One fix bug found and corrected before launch: the supervisor's empty-array expansion (`"${EXTRA_ARGS[@]}"` with nothing in it) is an unbound-variable error under bash 3.2 (macOS's default `/bin/bash`) with `set -u`; guarded with a length check.

Progress from here is tracked live in `results/e2/run/log_shard_00{0,1,2}.txt` and `results/e2/run/supervisor_shard_00{0,1,2}.log`. This document is updated again once the population reaches 540/540 and the frozen E2 analysis has run.
