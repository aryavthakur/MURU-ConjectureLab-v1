# PENDING_EXECUTION_DIAGNOSIS: V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000

**Status as of 2026-08-17 09:51 EDT: quarantined, retries stopped on the production host. NOT scientifically classified as failed. NOT omitted from the population. NOT substituted.**

## Identity
- world_id: `V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000`
- world_ordinal: 0
- family/regime/noise/replicate: mass_affine_descriptor / low / noiseless / replicate 0
- Execution commit: `4892c76` (and subsequent execution-only commits on top; no scientific file among them -- see `E2_EXECUTION_DEVIATION.md`)
- Seed derivation, search budget, grammar, classifier, `SIMPLIFY_TIMEOUT_SECONDS=5`: unchanged, frozen, byte-identical to every other world in the population.

## Attempt history (all on the production host)
- As shard 0's ordinal-0 (first-in-order) world under the original 6-shard assignment: **76 consecutive attempts**, 2026-08-17 ~01:24 through ~09:29, every single one killed with exit code 137 (SIGKILL), cadence consistently ~6-6.5 minutes. Zero successful completions. Full attempt-by-attempt log in `results/e2/run/supervisor_shard_000.log` (that shard now runs its other 89 worlds only, `--only-worlds-file` restricted; see `E2_EXECUTION_DEVIATION.md` \S13).
- Isolated to its own dedicated one-world supervisor (`results/e2/run_poison_world/`), 2026-08-17 09:30-09:51: **3 further attempts**, again SIGKILLed at ~6.9, 6.7, and 7.4 minutes respectively (attempt 4 was still in flight when retries were stopped -- see below). Preserved read-only in this directory: `log_shard_000.txt`, `supervisor_shard_000.log`.
- **Total: 80 attempts, 0 successes, 100% SIGKILL rate, remarkably consistent ~6-7.5 minute time-to-kill regardless of which supervisor process, which attempt number, or (mostly) which point in the day.**

## Why retries were stopped here (not because the world "failed")
At the time retries were stopped: system load average had risen to 111 (1-minute), CPU usage was 100% (0% idle), and this world's retry loop was continuously consuming a full CPU core for ~7 minutes at a time, indefinitely (its supervisor was configured for up to 2000 attempts). Per explicit instruction, a retry loop that materially consumes CPU/increases system load on the shared production host is to be stopped and the world quarantined rather than retried further there -- this is an execution-resource decision, not a scientific determination about the world itself.

## What is NOT true
- This is **not** a scientific failure, first-loss classification, or A/B/C/D/E label of any kind -- no search was ever completed for this world, so it cannot be scored.
- It has **not** been dropped from the 540-world population. It remains outstanding, exactly one world, pending re-attempt under different execution conditions.
- No substitute seed, replicate, or world was generated in its place. There is no scientific workaround.
- The frozen manifest (`results/e2/manifest.json`), search settings, classifier, and timeout are untouched and remain authoritative.

## What resolves this
Per the standing plan (`E2_EXECUTION_DEVIATION.md` \S13's disposition, refined here): once sufficient uncontended compute is available, re-attempt this single world alone, in a clean one-worker environment with minimal competing load, using exactly commit `4892c76`, the same dependency/environment lock, the same PySR/Julia versions, the same seed, the same search budget, the same classifier, the same `SIMPLIFY_TIMEOUT_SECONDS=5`. If run on a different host/environment, first replay several already-completed ordinary rescue worlds there and confirm exact scientific parity before trusting any output from that environment. If it succeeds, merge its single world-outcome and candidate records into `results/e2/run/` only after that parity check and a world_id-uniqueness check against the rest of the population. If it repeatedly fails even in a clean, uncontended, isolated environment, stop retrying entirely and produce a dedicated execution diagnosis -- not a scientific workaround, not a fabricated result.

E2 completion accounting must treat this world as **539 ordinary + 1 pending** until one of the above outcomes occurs. No scientific analysis proceeds on a corpus that omits it as though it were absent by design.
