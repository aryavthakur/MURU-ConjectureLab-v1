# MURU v2 E2 Rescue-v2 Checkpoint 530 Diagnostic and Migration Report

**Date/Time**: 2026-08-17T20:27:00-04:00 (UTC: 2026-08-18T00:27:00Z)  
**Host**: Local macOS ARM64  
**Branch**: `claude/e2-rescue-v2-computational`  
**Checkpoint Artifact**: [`results/e2/rescue_v2_migration/LOCAL_E2_RESCUE_V2_CHECKPOINT_530.json`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/e2-rescue-v2-computational/results/e2/rescue_v2_migration/LOCAL_E2_RESCUE_V2_CHECKPOINT_530.json)

---

## 1. Bounded Diagnosis of Stalled Shard 0 World

### 1.1 Exact Active World ID
- `V2C|E2|mass_interaction|c_high|n_noiseless|r004` (Cell: `mass_interaction|c_high|n_noiseless`, Replicate 4, Ordinal 148).

### 1.2 Wall-Clock Time Spent
- **Total Duration**: 10,916 seconds (~3 hours 2 minutes).
- **Expected Normal World Runtime**: 100 – 240 seconds.
- **Factor Exceeded**: >36× standard world execution budget.

### 1.3 Process Tree & Resources at Diagnosis
- **Parent Process**: PID `77974` (`python3.13 e2_run_shard_lazy.py --shard-index 0 ...`), State: `RN`, CPU: `99.6%`, RSS: `1.6 GB`.
- **Child Process**: PID `79722`, State: `SN`, CPU: `0.0%`.
- **Julia/PySR Runtime**: In-process via `sys.dylib` embedded in Python PID `77974`.

### 1.4 Stack Sample Signature
Stack sampling (`sample 77974 1`) confirmed 100% of samples in Python main thread executing:
```
PyEval_EvalCode -> _PyEval_EvalFrameDefault -> _PyLong_GCD -> l_mod -> x_divrem
```
The process was stuck in an unbounded integer greatest common divisor reduction during SymPy expression processing.

### 1.5 File Activity Audit (Last 10+ Minutes)
- `log_shard_000.txt` mtime: `2026-08-17 17:24:34` (unchanged for 182 minutes).
- `shard_0.out` mtime: `2026-08-17 17:26:36` (unchanged for 180 minutes).
- **Bytes written in last 10 minutes**: 0 bytes.

### 1.6 Forward Progress & Runtime Limit Determination
- **Genuine Forward Progress**: FALSE. The worker was stalled in a non-terminating SymPy integer GCD reduction loop.
- **Runtime Limit**: CROSSED. Exceeded the normal per-world execution upper bound by over 36×.

---

## 2. Worker Termination & Process Verification

Per Rescue-v2 governance:
1. Sent `SIGTERM` to PID `77974` and PID `79722`. Both processes terminated cleanly.
2. Verified with `ps -ef | grep -E "e2_run_shard|raw_search|julia|lazy_classify|pysr"`:
   - **Local Workers Remaining**: 0
   - **Local Child Processes Remaining**: 0

---

## 3. Authoritative Result File Integrity & Completed Set

Authoritative scan across all result directories:
- `/tmp/e2_rescue_v2_production_out`
- `results/e2/run`
- `results/e2/run_shard1_healthy`
- `results/e2/run_shard3_healthy`
- `results/e2/run_shard4_healthy`
- `results/e2/run_shard5_healthy`
- `/tmp/e2_rescue_v2_smoke_output`

### Audit Results:
- **Total Unique Worlds Completed**: **530 / 540** (98.15%)
- **Total World Records Read**: 530
- **Torn World Records**: **0**
- **Total Candidate Rows Read**: 186,314
- **Torn Candidate Rows**: **0**
- **Result Schema Integrity**: 100% Valid JSONL

---

## 4. Remaining Worlds Manifest

### 4.1 Remaining Ordinary Worlds (9 Worlds)
1. `V2C|E2|mass_interaction|c_high|n_noiseless|r004` (interrupted/stalled on local host)
2. `V2C|E2|mass_interaction|c_high|n_default|r004`
3. `V2C|E2|mass_exponential_descriptor|c_low|n_default|r004`
4. `V2C|E2|mass_exponential_descriptor|c_low|n_strong|r004`
5. `V2C|E2|mass_exponential_descriptor|c_mid|n_noiseless|r004`
6. `V2C|E2|mass_exponential_descriptor|c_mid|n_default|r004`
7. `V2C|E2|mass_exponential_descriptor|c_high|n_noiseless|r004`
8. `V2C|E2|mass_exponential_descriptor|c_high|n_default|r004`
9. `V2C|E2|mass_exponential_descriptor|c_high|n_strong|r000`

### 4.2 Quarantined Poison World (1 World)
1. `V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000` (retained in quarantine per forensic protocol)

---

## 5. Downstream Action Safeguards
- **E2b Hard Replay Gate**: NOT EXECUTED (held pending 540 population completion).
- **E4a Policy Comparison**: NOT EXECUTED (held pending E2b and 540 population completion).
- **Poison World Retry**: NOT EXECUTED.
- **Local Replacement Workers**: NOT STARTED.
- **Cloud Resume Safety**: `CLOUD_RESUME_SAFE: YES`. The 530 completed worlds and 10 remaining worlds are fully frozen, validated, and ready for clean resumption on the validated Google Cloud ARM64 host.
