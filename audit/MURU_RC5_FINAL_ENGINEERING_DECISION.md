# MURU RC5 — final engineering decision

**Document ID:** `MURU-AUDIT-RC5-FINAL-ENGINEERING-DECISION-01`
**Decision:** `RC5 NOT FROZEN`
**Branch:** `eng/muru-rc5-a3-5`
**Engineering parent:** `69e33c778efb14362439941d25ebbfcfb1068284` (tag `engineering-rc4-2-1-integrity-closure`)
**Science contract implemented:** `560bf28568e2762c60edc994aac7f2b6de14081f` (tag `benchmark-content-freeze-a3-5`, tag object `533777b73748e3c45dd1ecbda07098ba9837c587`)

---

## 1. Decision

**RC5 is not frozen, and no `engineering-rc5-a3-5` tag is created.**

The mission's freeze conditions are evaluated honestly below. Two are not met.
The mission's own rule governs: *a single valid blocking defect blocks the RC5
freeze.*

| # | Freeze condition | Met | Evidence |
|---|---|---|---|
| 1 | Implementation complete | **NO** | A3.5 obligation 8 undischarged (§3, O2). The A1 M1/M2/M3 adequacy engine does not exist (O10) |
| 2 | Full tests acceptable | YES | 1643 collected, 17 failing, **all 17** traced to the gitignored, never-tracked `artifacts/p2_compounds.parquet` — byte-for-byte the RC4.2.1 baseline |
| 3 | No unexplained paper-benchmark regression | YES | Every failure traced; two independent full-suite runs produced the identical failing set |
| 4 | Calibration unchanged | YES | `git diff 69e33c7 -- calibration/` empty across 104 files |
| 5 | Threshold table unchanged | YES | `threshold_table.json` = `f36864aaec1b0afb10b6d6b691ace07ab71cda4a1e6d337885390e8de27ae3d3` at both the parent and HEAD |
| 6 | **Hostile review has no unresolved block** | **NO** | Five of seven lenses returned `BLOCK`; six blocking defects repaired; **repairs not re-reviewed** |
| 7 | Sealed state preserved | YES | §5 below; the sealed-boundary lens returned `PASS` |
| 8 | Global pre-execution plan generated and hashed | **NOT DONE** | Deliberately withheld — see §4 |
| 9 | Documentation synchronised without results | YES | Paper package rebound to A3.5; placeholder counts identical; no result populated |
| 10 | Git working tree clean | YES | `git status --porcelain` empty |

## 2. What was built

Implemented against the frozen A3.5, on a branch rooted exactly at the
engineering parent, with the science lineage **never merged**:

* **D14** `rc5_estimate` — two-stage `Phi`/`g` fit, training-fold-only profile then
  frozen, `E_REF = 45.0` parameterised rather than inheriting
  `ENERGY_SCALE = 30.0`, no post-freeze re-centring, `invalid_fraction` over
  denominator 30.
* **D12 / adapter** `rc5_adapter` — one row per compound, the five frozen
  covariates as the same tuple object, raw `g`, no weights, no row filtering,
  Gate-2 inputs from the calibration path, the mandatory label→position
  conversion, and a grammar guard that refuses `exp`.
* **D11 + D5 + D13** `rc5_selection` — engine-native `argmax(score)` retention,
  grouping through the frozen positive-scale identity contract, one seed one
  vote, largest class, lowest-ordinal tie-break, verbatim representative.
* **D7** `rc5_falsify` — five procedures (F1, F4, F7, F9, F10), section 6.0's
  two-parameter affine refit, `-inf` for every degeneracy, no validity floor,
  hard set and reported secondary kept structurally apart.
* **D8** `rc5_g1_bridge` — A1.3 within-compound leave-one-energy-out `MAE_0,i`
  under A1.2's own protocol; the struck in-sample reading provably unreachable.
* **D9** `rc5_manifest` — two layers; the global plan takes no partition
  argument, and a partition manifest's science block is a verified pure
  derivation of `(plan, partition)`.
* **D1–D4** — Gate 7's amended waiver reading the same threshold Gate 2 used;
  `REQUIRED_HARD_GATES = {F1, F4, F7, F10}`; `check_gate8`'s `result != PASS`
  fail-closed predicate; the record schema bumped to `muru-rc5-case-record-2.0.0`
  with an enforced anti-reinterpretation guard.
* **D6, D10, mechanical tranche** — injective ordinal `search_seed` with the
  mandatory hard-failing invariant guard, the G3-authority guard, partition-aware
  preflight, case-scoped store, atomic writes, deterministic resume.
* `rc5_runner` — composition only; declares no scientific constant; refuses
  every partition A3.5 §14.2 does not authorise, before materialising anything.

Three findings the implementation surfaced by execution and recorded rather
than absorbed: §7.4's five parameter-sharing merges do not hold under the frozen
identity contract (they were properties of the superseded §7.3 recipe; the
narrower relation is acceptance-harder); the `ENERGY_SCALE` leak is invisible
end-to-end and detectable only at the `_best_log_g` boundary; and A1.2's fit
protocol exists as a specification with no implemented fitter.

## 3. Why RC5 is not frozen

**Blocker 1 — the hostile-review repairs have not been re-reviewed.**
Six blocking defects were found by five independent lenses and repaired in this
branch. The mission requires affected reviews to be rerun after repair. They
have not been. The repairs are substantial — a new F1 re-execution driver, a
changed identity parse path, seed-granular resume, a deleted Gate-7 property —
and each is exactly the kind of change that warrants a fresh adversarial look.

**Blocker 2 — A3.5 obligation 8 is undischarged.**
§7.4 requires two non-gating class-heterogeneity diagnostics **recorded** so
class heterogeneity cannot hide behind `selection_count`. `CrossSeedSelection`
computes both; `CaseExecutionRecord` records neither. The obligation says
recorded, and it is not.

**Blocker 3 — Development cannot in fact be executed.**
The A1 M1/M2/M3 adequacy engine does not exist. `adequacy.py` states its own
scope boundary — it "deliberately contains no fitter, no optimiser, and no
numerical model evaluation" — and no D-item of the RC5 map covers building one.
`a1_case_adequacy_status` is therefore a required input the runner refuses to
invent, which is the safe failure but leaves the pipeline unrunnable. Freezing
RC5 as the executable implementation of A3.5 would overstate what exists.

Four further open items (O3–O6 in the hostile-review record) are prospective
bindings that must be written **before** the first Development seed executes,
because §12 forbids changing them afterwards: the identity contract's corrected
parse-fold quantification, A1.2's "shrink 10" composition rule, the `A_LO`/`A_HI`
binding, and a §13 erratum retiring §7.4's merge statement.

## 4. Why the global pre-execution plan was not sealed

The mission conditions it on *"once RC5 code and hostile review are clean"*.
The review is not clean. The plan builder is implemented, tested, and was
exercised to a scratch path — it produced a complete, verified, byte-reproducible
plan — but writing it into `artifacts/` would create the object that binds the
scientific execution, under a code identity that is about to change when O2 and
the O3–O6 bindings land. A pre-execution plan is written once and never amended;
sealing one now would either be wrong or would have to be broken.

The dry-run digest is recorded for continuity only, and is **not** a sealed
artifact: canonical `269e191257fcc194c71784470b2a2b5a2e09751a689b2f5252039ef91725ddda`
over 380 cases and 11,400 derived seeds.

## 5. Sealed-state attestation

| Object | State |
|---|---|
| Current-contract Development symbolic execution | **NOT RUN** |
| Held-out (240 cases) | **SEALED, NOT OPENED** |
| Challenge (60 cases) | **NOT EXECUTED, NOT SCORED, NOT INSPECTED** (see the pre-existing inaccuracy at O7) |
| Confirmation (110 real compounds) | **SEALED, NOT OPENED** — `artifacts/confirmation_set_sealed.json` byte-identical to the parent |
| Calibration | **NOT RERUN**; threshold table read-only and byte-identical |
| Falsification v1/v2 sealed populations | **NOT READ**; their fixtures deliberately not imported |
| Historical Development outcomes | **NOT INSPECTED** |

No RC5 test generates a Held-out or Challenge case. The only `generate_case`
reachable from RC5 code is `materialize_case`, which re-derives the partition
from the case ID and refuses anything but Development before generating. The
independent sealed-boundary lens tripwired `generate_case` and confirmed it
never fired for a sealed partition.

## 6. What must happen before RC5 can be frozen

1. Record the two §7.4 diagnostics on `CaseExecutionRecord` (obligation 8).
2. Author the prospective bindings for O3–O6 in the global plan, before any
   Development seed executes.
3. Build the A1 M1/M2/M3 adequacy engine under its own prospective
   authorisation, or explicitly re-scope RC5 to exclude it and say so in the
   freeze record.
4. Re-run the affected hostile reviews against the repaired tree.
5. Only then generate, hash and seal the global pre-execution science plan.
6. Only then tag.

```
======================================================================
RC5 NOT FROZEN — STOP BEFORE CURRENT CONTRACT DEVELOPMENT
======================================================================
```
