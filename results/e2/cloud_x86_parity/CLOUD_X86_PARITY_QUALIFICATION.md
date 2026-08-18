# MURU v2 — New Cloud Host (x86_64) Results-Blind Parity Qualification

**Verdict: `NEW_CLOUD_HOST_PARITY_FAILED`.** E2 was not resumed. Zero prospective worlds executed.

**Date (UTC)**: 2026-08-18
**Host**: Linux x86_64, Intel Xeon Platinum 8581C @ 2.30GHz, 24 logical CPUs (12 cores × 2 threads), 47 GiB RAM
**Previously qualified host**: Linux aarch64, 16 vCPU, 31.29 GiB
**Branch / HEAD**: `claude/e2-rescue-v2-computational` @ `ee7026d`

---

## 1. Phase 1 — repository reconciliation: PASS

After the local-host artifact recovery (`ee7026d`), the repository reconciles to the pushed checkpoint
exactly:

| Check | Required | Observed |
|---|---:|---:|
| Authoritative manifest files matching sha256 | 31 | **31** |
| Unique completed worlds | 530 | **530** |
| Duplicate world IDs | 0 | **0** |
| Torn JSONL records | 0 | **0** |
| Candidate rows | 186,314 | **186,314** |
| Remaining ordinary + poison absent from completed set | yes | **yes** |
| 530 + 9 + 1 | 540 | **540** |

## 2. Phase 2 — environment reconstruction: EXACT

Every value independently verified from repository locks and provenance, not taken from the prompt.

| Component | Frozen | This host |
|---|---|---|
| Python | 3.13.5 | 3.13.5 |
| SymPy | 1.14.0 | 1.14.0 |
| Julia | 1.12.6 | 1.12.6 |
| PySR | 1.5.10 | 1.5.10 |
| SymbolicRegression.jl | 1.11.3 | 1.11.3 |
| PythonCall.jl | 0.9.26 | 0.9.26 |
| Dependency lock | 50 pins | **50/50 exact, 0 deviations** |
| Julia `Manifest.toml` sha256 | `75fc2d89…b280705` | **identical, unchanged after `instantiate`** |
| Classifier version | `90a3b5ea…7089e7a` | **identical** |
| Threading | `JULIA_NUM_THREADS=OMP=MKL=OPENBLAS=1` | set |

Two independent corroborations that the reconstruction is faithful:

- The persistent classify cache seeded to **143,232 rows / 119,448 distinct expressions** — *exactly* the
  counts the ARM host recorded.
- `tests/test_raw_search_identity.py` **PASSES** on x86: a real PySR fit on
  `mass_power|low|noiseless|r000` seed 0, every structural field byte-identical between
  `e2_search.run_seed_search` and `raw_search.run_seed_search_raw`. The PySR/Julia bridge is sound.

## 3. Phase 3 — full results-blind parity qualification: **FAIL**

Because this host is x86_64 and the qualified host was ARM64, the full (not reduced) qualification was
run: `full_corpus_parity_audit.py`, unmodified, over **all 530** completed worlds — not a sample —
against a single frozen snapshot partitioned across 12 shards.

| Quantity | Value |
|---|---:|
| N_REPLAYABLE | 530 |
| N_MATCH | 527 |
| **N_MISMATCH** | **1** |
| ERROR_COUNT (timeouts, not disagreements) | 2 |
| N_DETERMINISM_CHECKED / MATCH | 30 / **30** |
| **PARITY_PASS** | **false** |

Determinism on x86 is intact. Parity with the sealed corpus is not.

### 3.1 The mismatch

`V2C|E2|mass_saturating_descriptor|c_low|n_default|r007` — `first_loss_stage`: sealed **A**, x86 **B**.
Representative fields both matched. Five consecutive x86 replays returned **B** every time: a stable,
reproducible disagreement, not flakiness.

Stage semantics make the disagreement substantive: **A** means *no row on any front is G2-correct*
(a universal negative); **B** means *a correct row exists on a front but no retained row is correct*.

### 3.2 Root cause — a wall-clock timeout, not floating point

The witness is seed `2104507054`, front rank 11:

```
square(sqrt(square(cube(square(square(sqrt(1.1143143 - (2.5876136 / (x1 + sqrt(x0 + x1)))))))) + 0.4475443))
  canonical: (1.1143143 - 2.5876136/(descriptor + sqrt(descriptor + mass)))**12 + 0.4475443
```

| | ARM64 (sealed) | x86_64 (observed) |
|---|---|---|
| `canonicalization_status` | `SIMPLIFY_TIMEOUT` | `OK` |
| `discovered_family` | — | `mass_saturating_descriptor` |
| `effective_support` | `SUPPORT_UNRESOLVED` | `{descriptor, mass}` |
| `g2_correct` | `False` | **`True`** |

Measured directly on this host: that classification takes **4.80 s** against the frozen
`SIMPLIFY_TIMEOUT_SECONDS = 5` budget — a **200 ms margin**.

The expression expands to degree 12 with ~90-digit integer coefficients; its canonicalization is
dominated by Python integer GCD reduction (`_PyLong_GCD` → `x_divrem`) — the *same cost class* as the
stalled world `V2C|E2|mass_interaction|c_high|n_noiseless|r004`, which sampled in that exact stack.

**`SIMPLIFY_TIMEOUT_SECONDS` is a wall-clock budget, so host speed determines a scientific label.**
The faster host finishes what the slower host abandoned.

This is **not** floating point, and **not** a lazy-versus-exhaustive algorithm difference: the sealed
candidate row itself carries `canonicalization_status=SIMPLIFY_TIMEOUT` from the **old exhaustive**
run, and the same unmodified `e2_classify.classify_expression` returns `OK` on x86. Same classifier,
same input string, different outcome — speed alone.

The affected field, `first_loss_stage`, is routing-relevant: it is consumed by Gate 2 of the frozen
E4a routing rule.

### 3.3 Exposure — the observed count is a lower bound

| Quantity | Value |
|---|---:|
| Candidate rows carrying `SIMPLIFY_TIMEOUT` | **834** |
| Distinct worlds containing ≥1 such row | **237** |
| As a fraction of the 530 completed worlds | **44.7 %** |

Every one of those 834 rows is a point where a faster host may resolve what the sealed run abandoned.
The audit observed only one mismatch because the **lazy** replay short-circuits on the first correct
row and therefore never classifies most of those rows. **1/530 measures what this audit reached, not
the divergence rate under full reclassification.**

### 3.4 Two unresolved audit timeouts

`mass_exponential_descriptor|c_mid|n_strong|r008` and `…|r011` exceeded the 90 s per-world audit cap.
The protocol's prescribed isolated patient retry at 600 s was run — **both timed out again**, unlike
the ARM run where all four of its timeout worlds matched on retry. These are errors, not
disagreements, so conclusive parity coverage is **528/530**.

## 4. Consequence

Per the frozen protocol, scientifically relevant parity failure halts execution. Nothing downstream
ran: no E2a worlds, no E2b, no poison-world retry, no E2a seal, no E4a gate, no E4a, no M2/M3, no
integration, no E6. **Zero worlds were executed on this host.** No scientific definition, frozen
artifact, or result file was modified.

Resuming here would have produced an E2a corpus in which the *same expression* carries a different
scientific label depending on which machine happened to classify it — with 237 of 530 worlds
structurally exposed to that mechanism.

## 5. What this finding is really about

This is not merely "x86 is not ARM." The qualification surfaced a **latent defect in the frozen
protocol itself**: a scientific classification boundary defined by wall-clock time. It is
host-dependent on *any* change of machine, and in principle on load, thermal state, or a CPU
generation change on the *same* architecture. The existing corpus is internally consistent only
because it was produced on one machine at one speed.

Resolving it is a scientific-governance decision, not an execution one, and is explicitly outside
what may be done autonomously. Options a governance decision would have to choose between:

1. **Re-run E2a in full on one host** under the existing 5 s budget — restores internal consistency,
   discards 530 completed worlds, and leaves the boundary in place for any future host.
2. **Replace the wall-clock cap with a deterministic bound** (operation/step count, or an explicit
   complexity ceiling) — removes host-dependence permanently, but changes a frozen definition and
   invalidates the existing corpus.
3. **Formally accept `SIMPLIFY_TIMEOUT` as a machine-dependent status** and quarantine the 237
   exposed worlds — preserves the corpus, narrows the claim, requires an amendment.

None of these may be selected without an explicit scientific decision. This host is ready to execute
whichever is chosen: the environment reconstructs exactly and determinism on x86 is 30/30.
