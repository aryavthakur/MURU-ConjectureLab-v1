# MURU RC5 — final hostile review record

**Document ID:** `MURU-AUDIT-RC5-FINAL-HOSTILE-REVIEW-01`
**Status:** `REVIEW_ROUND_1_COMPLETE — REPAIRS_APPLIED — RE-REVIEW NOT YET RUN`
**Engineering branch:** `eng/muru-rc5-a3-5`
**Engineering parent:** `69e33c778efb14362439941d25ebbfcfb1068284` (tag `engineering-rc4-2-1-integrity-closure`)
**Science freeze implemented:** `560bf28568e2762c60edc994aac7f2b6de14081f` (tag `benchmark-content-freeze-a3-5`, tag object `533777b73748e3c45dd1ecbda07098ba9837c587`)

---

## 1. Method

Seven independent reviewers were dispatched **against primary source**, not
against any summary produced by the implementation. Each was given the frozen
A3.5 amendment to read in full and told to find defects, to write and run its
own probes rather than read code, and to return `PASS` or `BLOCK` with an exact
file, function, line, quoted authority, and required repair. Each was bound by
the same prohibitions as the implementation: no partition execution, no sealed
outcome read, no Held-out or Challenge case generation.

The reviewers were told explicitly that a single valid blocking defect blocks
the freeze and that findings would not be majority-voted away.

## 2. Dispositions, round 1

| Lens | Verdict | Blocking findings |
|---|---|---|
| Science contract (A3.5 line by line) | `BLOCK` | 1 |
| Gate 7 / Gate 8 (independent Boolean reconstruction of D1–D4) | `BLOCK` | 2 |
| Identity and search | `BLOCK` | 1 |
| Reproducibility (seeds, manifest, resume, atomicity, provenance) | `BLOCK` | 2 |
| Sealed boundary | **`PASS`** | 0 |
| Schema and backward compatibility | `BLOCK` | 1 |
| Hostile implementation | `BLOCK` | 1 |

Six of the seven blocking findings were distinct; two lenses independently
found the same unwired schema guard, and two independently found the missing F1
driver. **Every blocking finding was valid.** None was argued away.

## 3. Blocking findings and their repairs

### B1 — F1_REPRODUCIBILITY had no production driver
*Found independently by the hostile-implementation and science-contract lenses.*

`execute_case` defaulted `reexecute` to `lambda: None`, and `run_partition`
never supplied one. `run_f1_reproducibility` therefore returned `FAIL` for every
case, and because `check_gate8` is fail-closed, **`STRUCTURAL_ACCEPTED` was
unreachable for every case in the only partition RC5 is authorised to run.**
Worse, the record could not distinguish "the pipeline is non-deterministic"
from "no re-execution was ever attempted".

A3.5 §6.1 forecloses this in terms: *"F1 runs for **every** case reaching Gate
8 … The compute cost — one full 30-seed re-execution per Gate-8-reaching case —
is a consequence of frozen contract, not an open decision."*

**Repaired.** The driver replays the same 30 seeds verbatim through the same
backend and design, regroups, and compares the representative under the frozen
identity rule. The replay writes nothing to the seed store — it is a
determinism probe, not a second result. Pinned by four tests, including one
proving a deliberately drifting backend genuinely fails F1 and one proving the
replay leaves exactly 30 seed records.

### B2 — the identity path never saw the feature names PySR emits
*Found by the identity-and-search lens.*

The runner fits PySR on a bare design matrix, so every emitted
`equations_["equation"]` string is in `x0..x4`. Grouping parsed those strings
with `identity_contract.parse_candidate`'s default binding, which covers only
the five primitive names — so `x0` parsed to a symbol literally named `"x0"`,
and the contract's positivity step, which asserts `positive=True` on the symbol
*literally named* `mass`, never fired. Reproduced exactly:

```
log(square(mass)) == log(mass)   ->  True
log(square(x0))   == log(x0)     ->  False
```

with an end-to-end consequence on identical content of `selection_count` 20 vs
10 and Gate 3 `True` vs `False`. A bound step of the frozen identity rule was
silently inert in production.

**Repaired.** Production strings now parse through `g2_contract._safe_parse`,
which aliases `x{i}` onto the **same `Symbol` object** as
`GRAMMAR_PRIMITIVES[i]`. The byte-frozen `identity_contract` module is
untouched. Pinned by six tests including a stability-verdict equivalence check
across both namings.

### B3 — resume never loaded recorded seeds
*Found by the reproducibility lens, which demonstrated the flip.*

`execute_case` only ever appended to the seed store; `CaseSeedRecordStore.load`
had no caller in `src/`. An interruption partway through a case therefore
re-executed all 30 seeds, and a fresh clean result silently superseded a
recorded `EXECUTION_FAILURE` — the retry A3.5 §8.2 and §12 forbid by name, and
precisely the case that matters, since transient failures do not recur.

**Repaired.** Resume is seed-granular. The store now carries each retained
candidate's own decided values (`complexity`, `valid_r2`, `invalid_fraction`)
so a resumed run reconstructs the seed's outcome rather than recomputing a
number the original run already decided; a record that cannot be resumed from
without recomputation is refused at write time.

### B4 — duplicate seed records were writable
*Found by the reproducibility lens.*

The duplicate guard fired only on `load`, so the runner could commit the
violation and continue — and the file then became permanently unreadable by its
only reader, destroying the evidence an auditor would need to reconstruct the
seed history.

**Repaired.** `append` refuses a duplicate at write time. The load-side guard
remains for out-of-band writes.

### B5 — `rc3_ceiling` still implemented the superseded Gate-7 rule
*Found by the Gate-7/Gate-8 lens.*

`CeilingEstimate.ceiling_satisfied` returned `gate_passed or waiver_applied`,
was exported, was docstringed *"Gate 7 of the frozen acceptance predicate"*, and
was entrenched by a passing test. It is acceptance-favouring wherever the
candidate floor fails, and obligation 17 names this module's unconditional form
as **precisely what must not be implemented**. Neither the module nor its test
had been reviewed under the amendment because neither was in the RC5 delta
ledger.

**Repaired.** `ceiling_satisfied` is deleted; `waiver_applied` is renamed
`waiver_regime` because it is only the *ceiling half* of the amended waiver.
Gate 7 is decided solely by `evaluate_structural_acceptance`, which has the
threshold table and the complexity this module deliberately does not. Both files
are now in the ledger.

### B6 — the schema guard was never wired
*Found independently by the schema and Gate-7/Gate-8 lenses.*

`record_schema_generation` had **zero production callers**. A
`muru-rc3-case-record-1.0.0` record — or one with no `schema_version` at all —
on disk was silently counted as a completed case, so resume skipped it
permanently and a verdict scored under the superseded six-rung Gate 8 stood and
was never re-executed under the amended rules.

**Repaired.** `completed_case_ids` and `load_case_record_payload` classify every
payload and refuse anything that is not the current generation.

## 4. Non-blocking findings repaired in the same pass

A record could be written under a foreign `schema_version`; hard gates could
carry `NOT_APPLICABLE` in the record (now checked by membership, and for the
hard gates too, not only F9); `f9_acceptance_calibration_status` could
self-declare `PROVEN`, which would have laundered §12's promotion prohibition
into a report; the RC3-era `FALSIFICATION_RUNG_ORDER` alias silently meant a
four-member tuple (deleted, so an old importer breaks loudly at import time);
a corrupt interior line in a seed file was dropped like a truncated tail, which
could hide a recorded failure; `_unevaluable_record` discarded the predicate's
own verdict and so failed its own re-derivation check; `run_partition` skipped
`check_preconditions` entirely and built its store without the plan digest; a
tampered global plan verified self-consistently; commit-typed manifest fields
were unvalidated; obligation 10 did not cover a plan loaded from disk;
`REQUIRED_HARD_GATES` and `MAX_COMPLEXITY` were re-declared rather than imported
or cross-asserted; F4/F7/F9/F10 reported replicate counts without asserting
them; `_run_one_seed` let unlisted exceptions abort the whole partition.

Authorisation was centralised into one object imported by every module that
could open a partition — the runner, `run_preflight`, and the Layer-2 manifest
builder — rather than a convention the runner happened to enforce.
`derive_partition_science` is deliberately left unguarded so an independent
verifier can still re-derive any partition's science block.

A3.5 obligation 16 was implemented: per-endpoint execution-failure-poisoned
counts, derived from `per_seed_status` so they cannot disagree with it,
disclosed and never deducted from a denominator.

## 5. The sealed-boundary lens returned PASS

Recorded in full because a negative finding here is load-bearing. Byte-identical
synthetic content driven under development, held-out and challenge labels
produced byte-identical scientific payloads except `case_id`,
`partition_label`, `seeds_used` and `per_seed_status`. A `TruthRecord` read-spy
plus a `case_acceptance` call-spy showed the first planted-truth read strictly
follows the last acceptance evaluation on all three paths; mutating truth seven
ways moved zero acceptance-relevant fields. With `generate_case` replaced by a
tripwire, the tripwire never fired for a held-out or challenge ID: every entry
point refuses before materialising. A full transitive import-graph walk of all
RC5 roots reaches `analysis.classify_negative_control` from nowhere.

## 6. Open findings NOT repaired, and why they matter

These are recorded as blockers to the freeze, not dismissed.

| # | Lens | Finding | Status |
|---|---|---|---|
| O1 | all | **The round-1 repairs have not been re-reviewed.** Six blocking defects were repaired after the reviewers finished; the mission requires affected reviews to be rerun. | **BLOCKING** |
| O2 | science contract | **A3.5 obligation 8 is not discharged.** §7.4's two mandatory non-gating class-heterogeneity diagnostics are *computed* by `CrossSeedSelection` but are not *recorded* on `CaseExecutionRecord`. §7.4 requires them recorded "so class heterogeneity cannot hide behind `selection_count`". | **BLOCKING** |
| O3 | identity | The identity contract's docstring claim that the in-process-scaling failure mode "occurs nowhere" is **operationally false**: `sp.sympify` folds literal-over-literal arithmetic *inside* `parse_candidate`, giving 26.8% under-merge on division-bearing pairs the frozen grammar produces freely. Direction is conservative (under-merge → harder Gate 3). The module is byte-frozen, so the repair is a corrected quantification, not code. | Open, disclosed |
| O4 | hostile impl | A1.2's **"shrink 10" composition rule is an RC5 choice with a competing reading** that changes `MAE_0,i`, `trajectory_mae` and therefore G1 per case. Disclosed in the module docstring but not prospectively frozen. §12 will forbid changing it once Development runs, so it must be bound *before*. | Open, must be recorded in the global plan |
| O5 | science contract | `A_LO`/`A_HI` are bound to `Phi`'s own clamp values by RC5; A1 gives them no numeric definition. Under that binding the clip is provably inert, so §5.2's "not a bare `Phi` evaluation" distinction is vacuous. Needs the same prospective recording as O4. | Open |
| O6 | identity | A3.5 §13's correction register — whose stated purpose is that no superseded statement is silently carried into RC5 — has **no row retiring §7.4's merge binding**, which the frozen identity contract refuses in all five cases. Needs a prospective erratum. | Open, amendment-text action |
| O7 | sealed boundary | A3.5 §2's *"no challenge-partition case has been generated"* is **already false at the engineering parent**: pre-existing A2/A2.1 integrity tests call `generate_case` on challenge IDs and `pb_32` builds all three partitions. Inherited, not introduced by RC5; the accurate predicate is "not executed, scored, or inspected for outcome". | Open, pre-existing, amendment-text action |
| O8 | sealed boundary | `seed_band_registry` puts `muru.synth.truth` (self-declared quarantined) into the import closure of every `rc5_*` module. No violation occurs — zero module-scope IO — but the structural guarantee `test_p3_import_graph` provides for `muru.discovery` has no RC5 counterpart. | Open |
| O9 | hostile impl | The runner's two guard tests cannot see the defect class they exist to prevent: one walks only `tree.body`, the other greps a fixed string list that omitted the one constant actually restated. | Open |
| O10 | all | **The A1 M1/M2/M3 adequacy engine does not exist.** `adequacy.py` owns the decision contract and contains no fitter; no D-item covers building one. `a1_case_adequacy_status` is a required input the runner refuses to invent. Development cannot be executed until it exists. | Open, disclosed scope boundary |

## 7. Verdict

**Round 1 is complete and its blocking defects are repaired. The review as a
whole is NOT closed.**

Six blocking defects were found and repaired; the repairs have not been
re-reviewed, and O2 is an undischarged A3.5 obligation. Under the mission's own
rule — *a single valid blocking defect blocks the RC5 freeze* — RC5 is not
freezable in this state.

```
======================================================================
RC5 HOSTILE REVIEW ROUND 1 CLOSED — REPAIRS APPLIED — RE-REVIEW REQUIRED
======================================================================
```
