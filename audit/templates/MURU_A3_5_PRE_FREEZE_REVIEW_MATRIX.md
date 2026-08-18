# MURU ConjectureLab v1 — A3.5 Pre-Freeze Hostile Review Matrix
**Document ID:** `MURU-AUDIT-TEMPLATE-A35-PREFREEZE-MATRIX-01`
**Status:** `TEMPLATE_PREPARATION_ONLY` — REVIEW DESIGN ONLY, no A3.5 draft exists yet
**Classification:** `HOSTILE_PRE_FREEZE_REVIEW_MATRIX`
**Governing Authority:**
- Amendment A3.1 Structural Endpoints & Calibration Contract (`c8938e8` / `benchmark-content-freeze-a3-1`)
- Amendment A3.2 Null Calibration Base Target & Scaffold Split (`363b517` / `benchmark-content-freeze-a3-2`)
- Amendment A3.3 Secondary Endpoints Contract (`363e1c5` / `benchmark-content-freeze-a3-3`)
- Amendment A3.4 (`326727d` / `benchmark-content-freeze-a3-4`), Engineering RC4 (`14259f8` / `engineering-rc4-a3-4`), Temporal Provenance Erratum (`3cb26f3` / `a3-4-temporal-provenance-erratum`)
- [`MURU_RC5_EXECUTION_SEMANTICS_AUTHORITY_AUDIT.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_RC5_EXECUTION_SEMANTICS_AUTHORITY_AUDIT.md) — final conclusion: **`RC5 HAS UNFROZEN SCIENTIFIC EXECUTION SEMANTICS`**, 12 items classified `UNFROZEN_SCIENTIFIC_DECISION`

---

## 1. Charter

This matrix is the **review framework**, not the review. It exists so that whenever a draft of Amendment A3.5 is produced, an auditor has a pre-built, adversarial checklist to apply to it — before RC5 engineering (the executable Development/Held-out case-execution path) is authorized to begin.

This document does not draft A3.5, does not choose between competing execution semantics, does not implement any RC5 code, and does not run Development or Held-out. It only specifies what a conforming A3.5 must contain and how to hostilely score it.

### Why now
The RC5 execution semantics authority audit (`07f43d3`) independently confirmed that RC4 has no executable production-case path and classified **12 of 40 execution semantics as `UNFROZEN_SCIENTIFIC_DECISION`** — real scientific design surfaces, not engineering gaps. A3.5's job is to resolve them. This matrix's job is to hostilely check that it actually did, rather than merely appearing to.

### Verdict values
- **`PASS`** — Unambiguous, singular, prospectively-justified textual or code-level evidence satisfies the requirement completely.
- **`FAIL`** — The A3.5 draft directly contradicts the requirement, leaves two live readings, or shows evidence of outcome-informed selection.
- **`NOT_PROVEN`** — The requirement is unaddressed, addressed only informally, or its independence from observed results cannot be checked.

### Classification values
- **`BLOCKING`** — A `FAIL` or `NOT_PROVEN` verdict on this criterion **prohibits RC5 engineering authorization**.
- **`NONBLOCKING`** — Recorded for completeness; never gates the authorization decision. Reserved for `OPTIONAL_HARDENING` items so a reviewer has an explicit place to record them instead of inventing a blocking version.

### Epistemic categories (assigned per criterion, independent of verdict)
| Category | Meaning |
|---|---|
| `FROZEN_SCIENTIFIC_REQUIREMENT` | A binding scientific contract already frozen upstream (A1/A3.1/A3.2/A3.3/A3.4, or the governance charter's outcome-blindness clause) that A3.5 must state, preserve, or correctly extend. |
| `ENGINEERING_REQUIREMENT` | A valid derived consequence of frozen rules or established repository patterns, not itself a new scientific claim. |
| `OPTIONAL_HARDENING` | Legitimate reproducibility hardening that is **never** a binding pre-freeze gate. Its absence must never by itself block A3.5. |

### Authorization rule
$$\text{Authorize RC5 Engineering} \iff \forall\, i \in \{\text{BLOCKING criteria}\},\ \text{Criterion}_i = \text{PASS}$$

If any `BLOCKING` criterion is `FAIL` or `NOT_PROVEN`:
$$\implies \mathbf{RC5\ ENGINEERING\ AUTHORIZATION\ REFUSED}$$

`NONBLOCKING` criteria never enter this rule.

---

## 2. Key Blockers (must reject A3.5 if present)

| ID | Rejection trigger | Primary domain(s) |
|---|---|---|
| KB-01 | Any required semantic remains undefined | R2 |
| KB-02 | Two materially different choices remain but one was selected without prospective scientific rationale | R10 |
| KB-03 | Historical performance was used to choose a rule | R1 |
| KB-04 | Development or Held-out was inspected | R1 |
| KB-05 | Selection semantics are implicitly tuned for G2 | R3 |
| KB-06 | The symbolic target does not correspond to the stated scientific estimand | R3 |
| KB-07 | Validation/test data influence Phi or fitting | R4 |
| KB-08 | Seed derivation permits collision or reseeding | R5 |
| KB-09 | `invalid_fraction` is ambiguous | R6 |
| KB-10 | Falsification PASS/FAIL semantics remain underspecified | R7 |
| KB-11 | A3.2 calibration compatibility is asserted but not demonstrated | R8 |
| KB-12 | Development and Held-out could use different scientific behavior | R9 |

Every key blocker maps to at least one `BLOCKING` criterion below; none is left as prose-only guidance.

---

## 3. Do Not Overreach

We previously caught this failure mode in the held-out preparation pack ([`MURU_HELDOUT_PREPARATION_SPEC_AUDIT.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/MURU_HELDOUT_PREPARATION_SPEC_AUDIT.md), DEF-08 and DEF-09): OS kernel, LLVM/Clang compiler build, hardware allocation envelope, process-ID monotonicity, and filesystem inode-creation-time monotonicity were all invented as `BLOCKING` gates with no prospective requirement behind them.

This matrix does not omit that category — it gives it an explicit **`NONBLOCKING`** home (criteria R1.5, R5.5, R9.4) so a future reviewer has somewhere to record it without being tempted to promote it. Unless already prospectively required elsewhere, the following are **not** valid blocking criteria for A3.5:

- specific hardware model
- OS kernel version
- compiler build identity
- PID monotonicity
- inode creation-time monotonicity

---

## 4. Complete 37-Criterion Domain Matrix

### R1 — Prospective governance / temporal cleanliness

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R1.1** | Freeze-before-execution ordering | `ENGINEERING_REQUIREMENT` | A3.5's freeze commit/tag must precede, in immutable git history, the first Development/Held-out execution artifact that consumes its semantics (mirrors the A3.4 temporal provenance erratum precedent). | **`BLOCKING`** |
| **R1.2** | No historical-performance-informed rule choice (KB-03) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Every A3.5 semantic choice traces to a rationale stated independently of any observed Development/calibration outcome. | **`BLOCKING`** |
| **R1.3** | Development/Held-out non-inspection during drafting (KB-04) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Zero read access to Development/Held-out content or derived outputs occurred while A3.5's semantics were chosen. | **`BLOCKING`** |
| **R1.4** | Amendment self-binds its creation commit | `ENGINEERING_REQUIREMENT` | A3.5 states its own creation commit hash, following the A3.1/A3.2/A3.3 pattern, and it matches the introducing commit. | **`BLOCKING`** |
| **R1.5** | Environment/hardware footprint recorded | `OPTIONAL_HARDENING` | Descriptive only; absence never blocks. | **`NONBLOCKING`** |

### R2 — Statistical degrees of freedom

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R2.1** | `valid_r2` single deterministic definition (KB-01) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Scope (validation-only vs +test), formula, and aggregation level stated with no alternative reading, and equal to what calibration was computed against. | **`BLOCKING`** |
| **R2.2** | `selection_count` / cross-seed selection as a pure function (KB-01) | `FROZEN_SCIENTIFIC_REQUIREMENT` | One equivalence rule (string/SymPy-equal/family-equal) and one `selection_count` computation, compatible with the frozen `k/30 >= 20/30` gate. | **`BLOCKING`** |
| **R2.3** | Zero remaining `UNFROZEN_SCIENTIFIC_DECISION` items (KB-01) | `FROZEN_SCIENTIFIC_REQUIREMENT` | All 12 items the RC5 authority audit flagged (adapter, target, covariates, seed derivation, namespace, band, per-seed retention, cross-seed selection, `selection_count`, `valid_r2`, `invalid_fraction`, rung execution) are each singularly resolved. | **`BLOCKING`** |
| **R2.4** | New degrees of freedom preserve calibrated gate meaning | `FROZEN_SCIENTIFIC_REQUIREMENT` | New quantities feeding G1/G2/G3 or the null threshold are demonstrated to be what the existing calibration was set against. | **`BLOCKING`** |

### R3 — Symbolic-regression target and selection bias

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R3.1** | Exact target matches the scientific estimand (KB-06) | `FROZEN_SCIENTIFIC_REQUIREMENT` | A3.5 names one target representation (raw mu / log_g scalar / per-energy trajectory) with a prospective argument it is the estimand G1/G2/G3 claims are about. | **`BLOCKING`** |
| **R3.2** | Symbolic covariates bound to one rule | `FROZEN_SCIENTIFIC_REQUIREMENT` | Design-matrix columns, order, and representation for real case search are stated, distinct from A3.1's calibration-world-only covariate statement. | **`BLOCKING`** |
| **R3.3** | Selection not tuned for G2 (KB-05) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Per-seed and cross-seed selection rules are justified independently of G2/G3 pass-rate effects, stated before any execution under A3.5's semantics. | **`BLOCKING`** |
| **R3.4** | Selection uniform across families/partitions | `ENGINEERING_REQUIREMENT` | Zero conditionals keyed on family ID or partition name in the selection procedure. | **`BLOCKING`** |

### R4 — Fold-local / non-transductive construction

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R4.1** | Adapter builds train-fold-only | `FROZEN_SCIENTIFIC_REQUIREMENT` | The case→execution adapter reuses `fit_training_scalar`'s train-only, fold-local construction (FM-06), not a transductive shortcut. | **`BLOCKING`** |
| **R4.2** | No validation/test leakage into Phi or fitting (KB-07) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Neither the scalar-competence fit nor the symbolic search fit reads validation/test rows at any stage. | **`BLOCKING`** |
| **R4.3** | Split scope stated per new computation | `ENGINEERING_REQUIREMENT` | Every new quantity (`valid_r2`, `invalid_fraction`, `selection_count`, falsification rungs) carries an explicit split-scope statement matching the frozen 20/5/5 scaffold split. | **`BLOCKING`** |

### R5 — Seed identity and randomness

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R5.1** | Search-seed derivation is a pure function of (partition, case_id, seed_index) (KB-08) | `FROZEN_SCIENTIFIC_REQUIREMENT` | A Development/Held-out seed rule is defined, since only calibration- and smoke-band derivations currently exist and neither reduces to a case-based rule. | **`BLOCKING`** |
| **R5.2** | Namespace disjoint, reseeding prohibited (KB-08) | `FROZEN_SCIENTIFIC_REQUIREMENT` | A declared Development/Held-out seed band, numerically disjoint from smoke (1.9e9+) and calibration (2.11e9–2.147e9) bands; reseeding forbidden once a seed record exists. | **`BLOCKING`** |
| **R5.3** | Band disjointness import-time checkable | `ENGINEERING_REQUIREMENT` | Extends `assert_seed_band_separation()`-style enforcement to the new band; not a documentation-only claim. | **`BLOCKING`** |
| **R5.4** | 30-seeds/case count unchanged | `FROZEN_SCIENTIFIC_REQUIREMENT` | `STABILITY_DENOMINATOR = 30` is inherited, not silently redefined. | **`BLOCKING`** |
| **R5.5** | PID/inode telemetry is descriptive only | `OPTIONAL_HARDENING` | Never a blocking seed-integrity gate (DEF-09 precedent). | **`NONBLOCKING`** |

### R6 — `invalid_fraction` and strict-evaluator consistency

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R6.1** | Single numerator/denominator definition (KB-09) | `FROZEN_SCIENTIFIC_REQUIREMENT` | States whether the numerator counts invalid seeds, invalid candidates within a seed's Pareto front, or invalid evaluations, with one denominator, no alternative reading. | **`BLOCKING`** |
| **R6.2** | Uses the frozen FM-07 strict evaluator | `FROZEN_SCIENTIFIC_REQUIREMENT` | Validity judgment routes through the existing typed-rejection evaluator (`contract.py`/`g2_contract.py`); zero divergent parsing path. | **`BLOCKING`** |
| **R6.3** | Frozen 0.005 threshold unchanged | `FROZEN_SCIENTIFIC_REQUIREMENT` | Gate 5 (`invalid_fraction <= 0.005`) consumed as-is; the numerator/denominator definition and the threshold value are not revised together. | **`BLOCKING`** |

### R7 — Falsification-rung completeness

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R7.1** | All six rungs get a concrete pass/fail procedure (KB-10) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Exact tolerance, perturbation magnitude, and pass/fail rule for each of F1/F4/F5/F7/F9/F10; no free parameter left to implementer discretion. | **`BLOCKING`** |
| **R7.2** | Rung membership/order unchanged | `FROZEN_SCIENTIFIC_REQUIREMENT` | Matches `FALSIFICATION_RUNG_ORDER` exactly; no rung added, dropped, reordered, or renamed. | **`BLOCKING`** |
| **R7.3** | No rung is vacuously satisfiable | `ENGINEERING_REQUIREMENT` | Each rung has a real, reachable failure mode; a worked failing example exists for each. | **`BLOCKING`** |

### R8 — Calibration compatibility

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R8.1** | Search settings demonstrated identical, not asserted (KB-11) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Development/Held-out search imports the identical `SEARCH_SETTINGS` object the calibration runner uses, via a mechanism that would fail on divergence — not prose assertion. | **`BLOCKING`** |
| **R8.2** | Complexity computed identically | `FROZEN_SCIENTIFIC_REQUIREMENT` | Real search consumes `equations['complexity']` the same way calibration does, under the same grammar/version pin, before null-threshold lookup. | **`BLOCKING`** |
| **R8.3** | New computations shown compatible with calibration | `FROZEN_SCIENTIFIC_REQUIREMENT` | `valid_r2`, `invalid_fraction`, `selection_count` as newly defined are shown to be the quantities calibration actually computed, not same-named different quantities. | **`BLOCKING`** |

### R9 — Development/Held-out path identity

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R9.1** | Zero partition-conditional branching (KB-12) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Adapter, search, and scoring contain no branch keyed on `development` vs `held_out`; differs only by manifest path and seed values. | **`BLOCKING`** |
| **R9.2** | Failure/resume semantics partition-independent | `ENGINEERING_REQUIREMENT` | One shared `SeedStatus`/`SeedStore`-style failure-handling and resume mechanism across both partitions. | **`BLOCKING`** |
| **R9.3** | Execution manifest locks identical settings across partitions | `ENGINEERING_REQUIREMENT` | Manifest's settings/grammar digest is computed the same way regardless of partition. | **`BLOCKING`** |
| **R9.4** | Hardware/OS identity not required | `OPTIONAL_HARDENING` | Path identity binds settings/grammar/rules/thresholds/representation/endpoints/failure semantics — not hardware or OS. | **`NONBLOCKING`** |

### R10 — Exact-algebra endpoint disposition

| # | Criterion | Category | Requirement | Blocker |
|---|---|---|---|---|
| **R10.1** | Descriptive-only disposition explicitly restated | `FROZEN_SCIENTIFIC_REQUIREMENT` | A3.5 explicitly states the exact-algebra endpoint (60-case denominator, A3.4) is descriptive-only and cannot rescue a failed primary gate. | **`BLOCKING`** |
| **R10.2** | No silent promotion without prospective rationale (KB-02) | `FROZEN_SCIENTIFIC_REQUIREMENT` | Any change from descriptive to blocking status carries an explicit, outcome-independent rationale. | **`BLOCKING`** |
| **R10.3** | Consistent "law" representation with primary search | `ENGINEERING_REQUIREMENT` | Exact-algebra scoring operates on the same target representation R3.1 fixes for primary search, or states an explicit, justified mapping. | **`BLOCKING`** |

---

## 5. Summary

| Metric | Value |
|---|---|
| Total domains | 10 |
| Total criteria | 37 |
| Blocking criteria | 34 |
| Nonblocking criteria | 3 |
| Key blockers mapped | 12 / 12 |

This matrix currently scores nothing — every criterion defaults to `NOT_PROVEN` because no A3.5 draft exists. To score an actual draft, use [`MURU_A3_5_HOSTILE_REVIEW_TEMPLATE.md`](file:///Users/aryav/Documents/MURU-ConjectureLab-v1/audit/templates/MURU_A3_5_HOSTILE_REVIEW_TEMPLATE.md).
