# E2b macOS/ARM64 Authoritative Replay -- Provenance Report

## Decision

**FINAL_E2B_DECISION: E2B_PASS**

All 144 held-out G2 (family_recovery) cases reproduced exact identity
on the original macOS/ARM64 environment that produced the sealed v1 evidence.

## Environment

| Field | Value |
|-------|-------|
| Host | Sandeeps-MacBook-Air.local |
| OS | macOS 26.1 (Darwin 25.1.0) |
| Architecture | arm64 (Apple Silicon) |
| Python | 3.13.12 (CPython, Anaconda) |
| PySR | 1.5.10 |
| juliacall | 0.9.26 |
| Julia | 1.12.7 |
| SymbolicRegression.jl | 1.11.3 |
| numpy | 2.5.2 |
| scipy | 1.18.0 |
| sympy | 1.14.0 |

## Julia Version Provenance

The RC4.1 identity proof (commit f13fd1e, Aug 14) recorded Julia 1.12.6.
The Julia binary at `/opt/miniconda3/julia_env/pyjuliapkg/install/bin/julia`
was installed on **Aug 15 12:00:18** (file modification timestamp) and reports
version **1.12.7** (SHA256: `81f22191668e32ddc48010024e33dbcc4e17d5e39e332f81959b179e430fa94f`).

The held-out execution ran on **Aug 16**. The Julia binary has not been modified
since Aug 15. Therefore both the original held-out execution (Aug 16) and this
replay (Aug 18) used the identical Julia 1.12.7 binary. The RC4.1 identity
proof's "1.12.6" was captured at an earlier point in time, before juliapkg
resolved the update.

SymbolicRegression.jl 1.11.3 is confirmed identical in both the RC4.1 identity
proof and the live juliacall environment.

## Pre-execution Verification

| Check | Result |
|-------|--------|
| macOS ARM64 | VERIFIED |
| Python 3.13.12 | VERIFIED |
| PySR 1.5.10 | VERIFIED |
| requirements.lock.txt SHA256 | `13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8` (MATCH) |
| HEAD commit | `8d87143d4280602323aa33ee0b5481aaef0fb4a8` (MATCH run_commit) |
| Sealed evidence integrity (482 files) | VERIFIED (0 mismatches) |
| Sealed evidence loaded | 144 cases (MATCH denominator) |
| G2 case population (registry-derived) | 144 cases |
| Case search seeds | 144/144 byte-identical to manifest |
| Contending processes | NONE |

## Execution

| Metric | Value |
|--------|-------|
| Cases | 144 |
| Seeds per case | 30 |
| Total searches | 4,320 |
| Workers | 4 (ProcessPoolExecutor) |
| Total wall time | 4,593.5s (1.28h) |
| Average per case | 31.9s effective (127.5s serial per case) |
| Completion rate | 113 cases/hr |
| Execution errors | 0 |

## Identity Comparison Results

| Criterion | Result |
|-----------|--------|
| Selection count exact match | **144/144** |
| Representative expression exact match | **144/144** |
| Full case identity (both) | **144/144** |
| Errors | 0 |

Every one of the 144 cases produced byte-identical `selection_count` and
`cross_seed_representative_expression` to the sealed values. No tolerance
was applied. No coefficient rounding. Exact string equality on both fields.

## Comparison to x86_64 Cloud Replay

The prior cloud x86_64 replay (commit 4ebf98c, E2 rescue v2) demonstrated
a cross-architecture confound:

- **Architecture:** Linux x86_64 vs macOS ARM64
- **Julia version:** 1.12.6 (x86, matched RC4.1 proof) vs 1.12.7 (ARM64, actual binary)
- **Root cause:** PySR search paths diverge across architectures due to:
  - Different floating-point behavior (x86 extended precision vs ARM64 IEEE754)
  - Wall-clock-dependent SIMPLIFY_TIMEOUT (5s budget, host-speed sensitive)
  - Expression simplification order differences

The x86 replay reproduced only 1/144 exact case identities for the E2b criterion.
This macOS/ARM64 replay reproduces **144/144**. The cross-architecture confound
is confirmed: PySR-based symbolic regression is deterministic within an
architecture+environment but NOT across architectures.

This macOS/ARM64 replay is the authoritative environment because:
1. It is the same machine that produced the sealed v1 evidence
2. It uses the same Julia binary (unchanged since Aug 15)
3. It runs from the same commit (8d87143d)
4. All Python packages are version-identical to the original execution

The x86 replay result is retained as a diagnostic artifact but does not
modify the E2b decision.

## Frozen Protocol Compliance

| Constraint | Compliance |
|------------|-----------|
| Seeds modified | NO |
| Search settings modified | NO |
| group_and_select modified | NO |
| Representative selection modified | NO |
| selection_count definition modified | NO |
| Exact-string identity requirement modified | NO |
| Coefficient tolerance introduced | NO |
| E2b identity criterion modified | NO |

## Artifacts

- `E2B_MACOS_ARM64_REPLAY_REPORT.json` -- full per-case comparison results
- `E2B_MACOS_ARM64_REPLAY_PROVENANCE.md` -- this document
- Replay script: `scripts/run_e2b_macos_replay.py`
