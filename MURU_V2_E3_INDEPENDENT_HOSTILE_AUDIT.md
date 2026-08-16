# MURU v2 E3: Independent Hostile Audit

**Status:** COMPLETE. This audit is a second, independent pass over the already-executed
E3 identifiability oracle study. It does not redesign E3, does not run symbolic search,
and does not move any threshold. It reads the frozen design first, then independently
inspects the raw artifacts, the implementation, and the reported results — recomputing
every load-bearing statistic from scratch, without importing or trusting
`aggregate_e3.py` (the primary aggregator) anywhere in this audit.

**Auditor branch/worktree:** `audit/v2-e3-independent`,
`.claude/worktrees/audit-v2-e3-independent/`, rooted at `main` (`5049a1a`).

**Object under audit:** branch `exp/v2-e3-identifiability`, commit `1d20731`
(`.claude/worktrees/muru-v2-e3-identifiability-b23a7b/`), specifically
`E3_RESULTS.md`/`.json`, `results/e3_identifiability/*`, and
`scripts/e3_identifiability/*.py`.

**Method.** Every number in section 2 below was recomputed by fresh code written for
this audit, reading only `results/e3_identifiability/e3_worlds.jsonl` (the raw
per-world records written by `run_e3.py`) or by re-executing E3's own data-generation
code (`v2c_generator.py` + the frozen `rc5_estimate.fit_case_scalars`, which are data
generation, not the aggregator) and independently re-fitting the five candidate models
with a different optimizer, different bounds, and different initial guesses than
`oracle_models.py` uses. `aggregate_e3.py`, `e3_aggregate.json`, and
`e3_per_world_table.csv` (the aggregator and its outputs) were never imported or read
by any of the audit's own recomputation code — they are used only as the *comparison
target* to detect discrepancies, and only after the independent number was already
computed. All audit scripts are checked in under `scripts/audit_e3/`; all raw audit
outputs are under `results/audit_e3/`.

---

## 1. Verdict, up front

**The E3 execution is real, complete, and its headline arithmetic is correct.**
Independent recomputation from raw per-world records reproduces essentially every
reported number in `E3_RESULTS.md` exactly — the 10,000/200-cell manifest bijection,
zero PySR imports (confirmed with a broader static+dynamic net than the original
check), the frozen estimator's byte-identical provenance back to the sealed run
commit, the full 5×5 confusion matrix at the frozen operating point (exact match, cell
for cell), the F02/F03/F09/F18 special table (exact match to one decimal percent), the
per-family and per-coefficient recovery tables (exact match), and the c* table. An
independent re-fit of 240 worlds spanning every family, every noise level, both energy
grids, and three coefficients — using a **different, bounded** optimizer
(`scipy.optimize.least_squares`, Trust Region Reflective) with **different** initial
guesses than the original's bounds-free Levenberg-Marquardt `curve_fit` — selected the
identical model 240/240 times, with a maximum BIC disagreement of 0.00019 (Raftery's
"weak evidence" scale starts at 2). The per-world fits are not an artifact of a
particular optimizer or initialization choice.

**One material, non-blocking statistical finding survives:** the STUDY_INVALID gate's
own supplementary confidence framing ("Wilson upper bound sits right at the boundary,
0.109... a narrow pass, not a comfortable one") is computed on an inflated effective
sample size. `mass_power`'s truth law does not consume the coefficient `c`, so the
five `c`-labeled worlds within each `(noise, grid, replicate)` triple are literally
byte-identical draws — confirmed for all 400 of 400 such groups. The nominal `n=2000`
control population is therefore only **400 statistically independent draws**, each
replicated exactly 5 times. Recomputed correctly on the true independent sample size
(`k=38, n=400`), the Wilson 95% upper bound is **0.128**, not 0.109 — clearly past the
frozen 0.10 gate. This does **not** flip the study's formal `VALID` verdict, because
the pre-registered decision rule is written on the **point estimate**
(`false_structure_oracle > 0.10` triggers `STUDY_INVALID`), and the point estimate
(0.095) is unaffected by the duplication (it is the same ratio whether computed on
n=2000 or the true n=400 independent geometries). But the report's own volunteered
uncertainty framing around that pass materially understates how marginal the pass is,
and the same non-independence quietly inflates the apparent precision of every other
pooled `mass_power` statistic in the report. See section 3.1 for the full derivation
and section 4 for why this does not change any conclusion, but does change how much
confidence the "narrow pass" language should be given.

**No other blocking or study-invalidating finding was found.** Two minor,
non-numeric findings are recorded in section 5.

**On the question the goal asks directly:** the F09 search-limited finding — and its
license for E4b/c/d to target `mass_saturating_descriptor` specifically — **survives
independent review in full**. No E3 conclusion needs retraction. One conclusion needs
a precised weakening, stated in section 4.3: the STUDY_INVALID gate should be read as
a genuinely marginal, less-comfortable pass than the report's own Wilson framing
communicates, not a newly-failing one.

---

## 2. Independent recomputation tables

All of the following were computed by `scripts/audit_e3/independent_recompute.py`,
which parses `e3_worlds.jsonl` directly with hand-written aggregation code (grouping,
rate, and Wilson-interval logic re-typed from the frozen design document's own stated
definitions, not copied from `aggregate_e3.py`). Full machine-readable output:
`results/audit_e3/independent_recompute.json`.

### 2.1 Study validity gate (section 1 of `E3_RESULTS.md`)

| Criterion | k | n | rate | Wilson upper | Reported | Match |
|---|---:|---:|---:|---:|---|---|
| BIC | 190 | 2000 | 0.0950 | 0.1086 | 0.095, 0.109 | ✅ exact |
| Validation R2 | 1370 | 2000 | 0.6850 | 0.7050 | 0.685, 0.705 | ✅ exact |

The reported numbers are arithmetically correct **given n=2000**. Section 3.1 shows
why n=2000 is the wrong denominator for the Wilson bound specifically.

### 2.2 Overall recovery

| Population | n | BIC rate | Reported | Match |
|---|---:|---:|---|---|
| All 5 families | 10,000 | 0.8264 | 0.8264 | ✅ exact |
| Descriptor only | 8,000 | 0.80675 (displays 0.8067 or 0.8068 depending on rounding convention) | 0.8068 | ✅ (last-digit display rounding of a `...75` boundary value, k=6454/n=8000, not a computation error) |

### 2.3 Recovery by family (pooled over the whole 200-cell grid, n=2000 each)

| Family | BIC rate (independent) | R2 rate (independent) | Reported | Match |
|---|---:|---:|---|---|
| `mass_interaction` | 0.9855 | 0.9325 | 0.9855 / 0.9325 | ✅ exact |
| `mass_power` (specificity) | 0.9050 | 0.3150 | 0.9050 / 0.3150 | ✅ exact |
| `mass_saturating_descriptor` | 0.8430 | 0.7410 | 0.8430 / 0.7410 | ✅ exact |
| `mass_affine_descriptor` | 0.7300 | 0.6065 | 0.7300 / 0.6065 | ✅ exact |
| `mass_exponential_descriptor` | 0.6685 | 0.5610 | 0.6685 / 0.5610 | ✅ exact |

### 2.4 Recovery by coefficient (pooled over 4 descriptor families, n=1600 each)

| c | BIC rate | R2 rate | Reported | Match |
|---:|---:|---:|---|---|
| 0.25 | 0.6681 | 0.5769 | 0.6681 / 0.5769 | ✅ exact |
| 0.40 | 0.7569 | 0.6581 | 0.7569 / 0.6581 | ✅ exact |
| 0.55 | 0.8094 | 0.6944 | 0.8094 / 0.6944 | ✅ exact |
| 1.10 | 0.88125 (displays 0.8812/0.8813) | 0.7856 | 0.8813 / 0.7856 | ✅ (same last-digit `...25`/`...75` rounding note as 2.2) |
| 2.20 | 0.9181 | 0.8363 | 0.9181 / 0.8363 | ✅ exact |

### 2.5 Frozen operating point headline table (c∈{0.25,0.40,0.55}, noise=0.02, grid=6, n=150 per family)

| Family | n | k | rate | Wilson lower | Classification | c* | Reported | Match |
|---|---:|---:|---:|---:|---|---:|---|---|
| `mass_interaction` | 150 | 150 | 1.0000 | 0.9750 | IDENTIFIABLE | 0.25 | 1.000 / 0.975 / IDENTIFIABLE / 0.25 | ✅ exact |
| `mass_saturating_descriptor` | 150 | 123 | 0.8200 | 0.7508 | IDENTIFIABLE | 0.40 | 0.820 / 0.751 / IDENTIFIABLE / 0.40 | ✅ exact |
| `mass_affine_descriptor` | 150 | 83 | 0.5533 | 0.4734 | MARGINAL | 1.1 | 0.553 / 0.473 / MARGINAL / 1.1 | ✅ exact |
| `mass_exponential_descriptor` | 150 | 79 | 0.5267 | 0.4471 | MARGINAL | 1.1 | 0.527 / 0.447 / MARGINAL / 1.1 | ✅ exact |

Classification was computed by an independently-typed `classify()` function
(`rate >= 0.80 → IDENTIFIABLE`, `0.50 <= rate < 0.80 → MARGINAL`, else
`WEAKLY_IDENTIFIABLE`) applied to the independently-computed rate — the decision tree
was applied mechanically and reproduces every classification exactly.

### 2.6 Confusion matrix at the frozen operating point, BIC (750 worlds)

Independently reconstructed via `pandas` crosstab on raw per-world records, compared
cell-for-cell against the reported table:

**Result: exact match, all 25 cells, `confusion_matrix_matches_reported = True`.**

The report's own derived claim — "98 of 183 total off-diagonal errors are the
affine↔exponential pair, 53.6%" — was independently recomputed from this matrix:
750 − (132+83+123+79+150) = 183 off-diagonal; 60+38 = 98; 98/183 = 53.6%. Confirmed.

### 2.7 F02 / F03 / F09 / F18 special analysis

| Case | Family | Noise | n | E3 oracle rate (independent) | Reported |
|---|---|---:|---:|---:|---|
| F02 | `mass_affine_descriptor` | 0.0295 | 150 | 48.7% | 48.7% ✅ |
| F03 | `mass_affine_descriptor` | 0.06 | 150 | 36.0% | 36.0% ✅ |
| F09 | `mass_saturating_descriptor` | 0.02 | 150 | 82.0% | 82.0% ✅ |
| F18 | `mass_exponential_descriptor` | 0.02 | 150 | 52.7% | 52.7% ✅ |

### 2.8 F18 intended-geometry table (section 10)

| | n | BIC rate (independent) | Reported |
|---|---:|---:|---|
| grid=6 | 150 | 0.5267 | 0.527 ✅ |
| grid=12 | 150 | 0.5400 | 0.540 ✅ |

### 2.9 c* table (native noise 0.02, grid 6)

| Family | curve (c=0.25→2.2) | c* |
|---|---|---:|
| `mass_interaction` | 1.00, 1.00, 1.00, 1.00, 1.00 | 0.25 |
| `mass_saturating_descriptor` | 0.68, 0.84, 0.94, 1.00, 1.00 | 0.40 |
| `mass_affine_descriptor` | 0.44, 0.60, 0.62, 0.96, 0.88 | 1.10 |
| `mass_exponential_descriptor` | 0.44, 0.58, 0.56, 0.80, 0.90 | 1.10 |

All four match the reported `c_star_table` exactly, including the non-monotone dip at
`c=2.2` for `mass_affine_descriptor` (0.96 → 0.88) — this is not a computation error on
either side; it is real Monte Carlo noise at n=50 per cell (a ±0.07-ish SE band at
p≈0.9), and both the original report and this independent recomputation reproduce the
same dip from the same underlying per-world records, which is itself a useful
cross-check that neither pipeline silently smoothed or reprocessed the curve.

### 2.10 Noise-free arm (H_id_noise), grid=6

Independently confirms: at `noise_sd=0.0`, every family reaches ≥0.98 oracle-selection
at every tested coefficient, including the smallest (`c=0.25`: affine 1.00, exponential
0.98, saturating 1.00, interaction 1.00). This directly falsifies H_id_noise / PE3-2 as
originally stated, exactly as the report concludes.

---

## 3. Discrepancy ledger

| # | Item | Independent result | Reported result | Status |
|---|---|---|---|---|
| D1 | Study validity Wilson upper bound (BIC) | Correctly requires n=400 (independent draws); recomputed upper = 0.128 | 0.109 (computed on n=2000, which is 5×-duplicated) | **DISCREPANCY — see 3.1.** Not an arithmetic error given the n it used; the n itself is not the number of independent observations. |
| D2 | All other headline rates/tables (§2.2–2.10) | Exact match | Exact match | No discrepancy |
| D3 | Manifest/execution completeness | 10,000/10,000, 200/200 cells, 0 dup, 0 missing, 0 failures | Same | No discrepancy |
| D4 | PySR absence | 0 static hits (broader file net), 0 dynamic modules (broader substring net) | Same conclusion | No discrepancy |
| D5 | Frozen estimator byte-identity | `git diff 8d87143..HEAD` empty for `generator.py`, `rc5_estimate.py`, and all 6 transitive deps | Claimed unmodified | No discrepancy |
| D6 | `registry.resolve_case_id` static check (design §2.2) | Not implemented in E3's own code (grep: 0 hits) | Design document describes this check as part of the governance frame | **Gap — see §5, MINOR.** Practically inert (ID formats cannot collide) but the specific check the design promised was not built. |
| D7 | Confusion matrix @ frozen operating point | Exact cell-for-cell match | — | No discrepancy |
| D8 | BIC formula convention | `n·ln(RSS/n) + k·ln(n)`, valid since all 5 models share n_train=120 (verified for all 50,000 fits) | Same | No discrepancy |
| D9 | Fit convergence | 50,000/50,000 converged | "0 execution failures" | No discrepancy |
| D10 | Artifact hashes (`e3_hashes.json`) | `shasum -a 256` on all 15 files matches exactly | — | No discrepancy |
| D11 | v1-observed F02/F03/F09/F18 reference counts | Traced to `MURU_V1_ROOT_CAUSE_RANKING.md` lines 153–226, exact match | Same | No discrepancy |
| D12 | Design-precedes-execution ancestry | `git merge-base --is-ancestor befca0d 1d20731` → true | Claimed | No discrepancy |

### 3.1 D1 in full: the `mass_power` control's Wilson interval rests on 400 draws, not 2,000

`mass_power`'s truth law (`v2c_generator.law_v2`, `generator.py::_law` `"mass_only"`
branch) does not use the coefficient `c` at all — it draws its own `exponent`
independent of `c`. But E3's seed convention deliberately shares covariate/noise seeds
across the `c` ladder within a `(family, noise, grid)` cell (`geometry_id` excludes
`c`; design doc §3.4 control 3, "paired seeds across the c ladder") — a legitimate,
disclosed choice that gives the *descriptor* families a clean paired identifiability
curve. For `mass_power` specifically, the interaction of these two facts means the five
`c`-labeled worlds within each `(noise, grid, replicate)` triple are not just
correlated — they are **literally the same draw**, five times.

Verified directly (`scripts/audit_e3/check_control_duplication.py`): grouping all 2,000
control rows by `(noise_sd, grid_points, replicate)` yields exactly 400 groups; **all
400/400 groups have identical seeds and identical `false_structure_bic` outcomes**
across their 5 `c`-labeled members. `E3_RESULTS.md` §13 discloses the redundancy exists
("this is why the manifest still totals 10,000 exactly... the redundancy for the
control is disclosed rather than silently collapsed") but does not connect it to the
Wilson-interval computation used two sections earlier for the STUDY_INVALID gate.

| | k | n | rate | Wilson 95% CI |
|---|---:|---:|---:|---|
| As reported (raw row count) | 190 | 2000 | 0.0950 | [0.0829, 0.1086] |
| Correct (unique independent geometries) | 38 | 400 | 0.0950 | [0.0700, **0.1277**] |

The point estimate is identical either way (190/2000 = 38/400 exactly, since each
unique geometry's outcome is replicated 5× consistently) — **the pass/fail point
estimate is not in question.** What changes is the precision claim: a proportion's
Wilson interval is only valid when computed on the number of *independent* Bernoulli
trials behind it. Computed correctly, the upper bound is 0.128, comfortably past the
frozen 0.10 gate, not "right at the boundary" as reported.

**A concrete instance of the same pattern**, found while checking the confusion
matrix: the reported "`mass_power` leaks 15/150 (10%) into `mass_interaction` at the
frozen operating point" is, on inspection, 5 independent replicate-geometries (out of
50 truly independent draws at that noise/grid slice) each tripled by the 3
frozen-support `c`-labels — literally `replicate ∈ {12, 19, 24, 36, 41}` each selecting
`M_inter`, ×3. The 10% point estimate survives untouched; the implied precision (a
denominator of 150) does not. This same inflation factor (up to 5×, or 3× at the
frozen-operating-point slice specifically) applies to every other pooled `mass_power`
statistic in the report: `recovery_by_family`'s control row, `control_breakdown_by_noise_grid`,
and the control's rows in `full_cell_classification_200_cells`.

**Why this does not change the study's formal verdict.** The frozen decision
criterion (design doc §3.7) is written on the point estimate: *"If
`false_structure_oracle` on the `mass_power` control exceeds 0.10 the study is
INVALID."* It does not reference a confidence interval. The point estimate (0.095) is
below 0.10 regardless of which `n` is used for its CI, so the study remains formally
`VALID` under the literal, pre-registered rule. What is wrong is only the
*supplementary* confidence language `E3_RESULTS.md` added on top of that literal rule
("Wilson upper... sits right at the boundary... narrow pass, not a comfortable one")
— that language is itself miscalibrated, in the direction of overstating confidence,
not understating it. A hostile reader should treat the STUDY_INVALID gate as resting on
weaker footing than the report's own words suggest.

---

## 4. Answers to the audit's specific questions

1. **Were exactly 10,000 authorized worlds executed with correct 200-cell coverage?**
   Yes — independently re-derived from the design document's stated factor levels
   (not copied from `manifest.py`), confirmed bijective against both `e3_worlds.jsonl`
   and `e3_manifest.json`: 10,000/10,000, 200/200 cells, 0 missing, 0 extra, 0
   duplicates, 0 non-`OK` statuses.
2. **Are seed namespaces, partitions, families, coefficient regimes, noise regimes,
   and model candidates exactly design-compliant?** Yes. Families, `c ∈
   {0.25,0.40,0.55,1.1,2.2}`, noise ∈ {0.0,0.02,0.0295,0.06}, grid ∈ {6,12}, 50
   replicates — all match the frozen design document's §3.2/§3.6 text, transcribed
   independently rather than taken from the code under audit. `V2C_SEED_PREFIX` /
   `BENCHMARK_SEED_PREFIX` disjointness is enforced by assertion and holds.
3. **Is there any benchmark/Held-out/Challenge leakage?** No file read anywhere in
   the E3 code path touches Held-out, Challenge, or Development partition data. The
   only "frozen evidence" reused is four read-only reference numbers (F02/F03/F09/F18
   v1-observed rates) for side-by-side display, traced exactly to the already-sealed
   `MURU_V1_ROOT_CAUSE_RANKING.md`, never used to select an E3 parameter.
4. **Is PySR completely absent?** Yes, confirmed independently with a broader net
   than the original check: a grep of the *entire* frozen source tree (not just the
   original check's 8-file allowlist) finds `pysr`/`gplearn` imports elsewhere in
   that tree, but all are **lazy, function-local** imports inside functions E3 never
   calls (`engine.run_pysr`, `rc5_adapter`'s regressor builder, `rc3_calibration_runner.PySRBackend`).
   A fresh dynamic subprocess probe running a real E3 world and inspecting
   `sys.modules` for `pysr|gplearn|julia|symbolicregression|operon|deap` found only
   `sympy.printing.julia` (an unrelated sympy code-printer submodule, a false-positive
   substring match, not a Julia/PySR runtime).
5. **Is the frozen scalar estimator used exactly as claimed?** Yes. `generator.py`,
   `rc5_estimate.py`, and every module they transitively import
   (`registry.py`, `truth.py`, `adequacy.py`, `structural_acceptance.py`,
   `discovery/estimate.py`, `discovery/grammar.py`) are byte-identical
   (`git diff` empty) between the sealed run commit `8d87143` and the frozen-src
   worktree's current HEAD; the worktree's only divergence from that commit anywhere
   in `src/` is 7 wholly new files (additions only). `fit_case_scalars`'s documented
   contract (fold-local `Phi` on 120 training compounds, no re-centring after freeze,
   `E_REF=45.0`) is called correctly by `run_e3.py`.
6. **Are nonlinear fits and parameter bounds implemented correctly?** The BIC-selected
   model and BIC values are robust to a materially different fitting procedure: an
   independent 240-world stratified re-fit using a **bounded** `least_squares`/TRF
   optimizer with different initial guesses agreed with the original's **unbounded**
   `curve_fit`/LM on 240/240 model selections, max |ΔBIC| = 0.00019. The absence of
   explicit bounds in `oracle_models.py` is a design choice, not observed to produce
   pathological fits in this dataset.
7. **Is BIC computed with the correct likelihood/sample-size/parameter-count
   convention?** Yes. `n·ln(RSS/n) + k·ln(n)` is the standard simplified Gaussian BIC
   for OLS, valid for comparing models fit on identical `n` (the model-invariant
   `n·ln(2π) + n` terms drop). `n_train=120` was independently confirmed identical
   across all 50,000 individual model fits — no world used a different sample count.
8. **Is the `mass_power` false-structure control really 0.095, and a valid pass
   against the frozen 0.10 gate?** The point estimate is exactly 0.095 (190/2000 =
   38/400), independently confirmed, and it passes the frozen, point-estimate-based
   gate. See §3.1 for the qualification on how comfortably.
9. **Is that narrow pass sensitive to ties, fit failures, numerical tolerances, or
   bookkeeping?** The pass itself (point estimate 0.095) is insensitive to all of
   those — see §4.6/§6 robustness appendix (zero fit failures, zero exact BIC ties,
   optimizer-independent). But the pass's *reported confidence interval* is sensitive
   to a bookkeeping issue: an inflated, non-independent sample size (§3.1). That is
   the one substantive sensitivity finding in this audit.
10. **Does independent recomputation reproduce every family recovery rate and
    disposition?** Yes, exactly (to floating-point/last-digit-rounding precision) —
    see §2.
11. **F09 ~82%, `mass_affine` ~55%, F18 ~53%, interaction ~100%?** Reproduced exactly:
    82.0%, 55.3%, 52.7%, 100.0%.
12. **Confusion matrices and F02/F03/F09/F18 analyses?** Exact match, cell-for-cell
    and percentage-for-percentage — see §2.6–2.7.
13. **Do c* and the IDENTIFIABLE/MARGINAL/WEAKLY_IDENTIFIABLE classification
    mechanically follow the frozen decision tree?** Yes — an independently-typed
    classifier applied to independently-computed rates reproduces every reported
    classification. (The goal's phrasing says "NONIDENTIFIABLE"; the frozen design's
    actual third tier is named `WEAKLY_IDENTIFIABLE` — noted for precision, not a
    discrepancy in the artifact.)
14. **Is "F09 search-limited, affine/F18 data-limited" fully licensed by E3?** F09
    "search-limited" — yes, fully: an IDENTIFIABLE 82% oracle ceiling against an
    observed 0/12 real-search rate is exactly the pattern that licenses attributing the
    gap to search/retention rather than to the benchmark, and the report is
    appropriately careful not to claim *which* search-side factor (that is E4's job,
    left open). affine/F18 "data-limited" — licensed in the qualified sense the report
    itself uses (MARGINAL classification plus the noise-free arm showing near-100%
    recovery at zero noise, which is genuine additional evidence beyond the bare
    MARGINAL tier), but see §5 MINOR-2: the report's phrasing is slightly more
    assertive than the frozen tree's own "MARGINAL licenses nothing on its own"
    language technically supports on its own; it should be read as "not attributable
    to search from this cell alone," which is what the report's own hedges (the
    difficulty-guard language) already say when read carefully.

---

## 5. Findings, classified

| ID | Classification | Summary |
|---|---|---|
| **F-1** | **MATERIAL_NONBLOCKING** | The STUDY_INVALID gate's Wilson-interval framing (§1 of `E3_RESULTS.md`) is computed on `n=2000`, but only 400 of those 2,000 `mass_power` control rows are statistically independent (verified: 400/400 `(noise,grid,replicate)` groups have byte-identical seeds and outcomes across their 5 `c`-labels, because `mass_power`'s law does not consume `c`). Correctly computed on the true independent sample size, the Wilson 95% upper bound is 0.128, not 0.109 — past the 0.10 gate. Does not change the formal `VALID` verdict (which the frozen criterion defines on the point estimate, unaffected: 0.095 either way), but the report's own "narrow pass, not comfortable" framing should read as *more* marginal, not less, than stated, and the same inflation understates the uncertainty on every other pooled `mass_power` statistic in the report (control breakdown table, the control row of the full 200-cell classification, and the frozen-operating-point confusion matrix's `mass_power` row, concretely verified: its reported 15/150 "leak" to `mass_interaction" is 5 independent geometries out of 50, not 15 out of 150). |
| **F-2** | **MINOR** | The frozen design document (§2.2) describes the v2 governance frame's static check as asserting both seed-prefix disjointness *and* that no `V2C\|`-namespaced identifier resolves through `registry.resolve_case_id`. E3's own code (`v2c_generator.py`) implements only the prefix-disjointness half; no test in the E3 codebase actually calls `registry.resolve_case_id` on a `V2C\|`-prefixed string. Practically inert — the ID formats are structurally incompatible (verified by inspection of `registry.resolve_case_id`'s expected format) — but the specific mechanism the design document describes as protecting against collision was not built as stated. |
| **F-3** | **MINOR** | §12 of `E3_RESULTS.md` labels `mass_affine_descriptor`/`mass_exponential_descriptor` "DATA-LIMITED" and recommends against more search compute as the "primary remedy." The frozen decision tree's own language for a MARGINAL cell is that it "licenses nothing on its own" — neither a search-side nor a data-limited attribution. The report's stronger framing is substantively earned by the additional noise-free-arm evidence it cites (H_id_noise, §8.2), but reads more dispositive than the bare classification tier supports; it should be understood as "not attributable to search from this cell's evidence alone." No numbers are wrong; this is a phrasing/interpretation note. |
| **F-4** | **NONE (confirmed correct)** | Every other checked item in §4 (completeness, namespace, PySR absence, estimator provenance, transcription fidelity, BIC convention, fit robustness, artifact hashes, headline numbers, confusion matrices, special-case table, c* table, disposition classifications, F09 remediation license) reproduced exactly under independent, from-scratch recomputation. |

---

## 6. Robustness appendix

Sensitivity checks below test **numerical/implementation robustness only**. No
scientific criterion (the 0.80/0.50/0.10 thresholds, the five families, the `c`/noise/
grid levels, the BIC-vs-R2 dual-report rule) was moved, substituted, or re-derived.
Full data: `results/audit_e3/robustness_scan.json`,
`results/audit_e3/independent_refit_sample*.json`.

| Check | Result |
|---|---|
| **Optimizer convergence** | 50,000/50,000 individual model fits converged (`converged=True`). Zero failures anywhere in the run. |
| **Failed-fit handling** | The code path that persists a `converged=False` / `bic=null` record was never exercised by this run (0 occurrences), so its correctness could not be tested empirically; it was reviewed by inspection only (`oracle_models.fit_one_model`'s `try/except` around `curve_fit`, and `select_by_bic`'s filtering of non-finite/non-converged candidates before taking the min) and appears sound, but carries no empirical evidence either way. |
| **Initialization sensitivity** | An independent 240-world stratified sample, refit with `c0=0.5` (vs. the original's `c0=0.3`) and a crude median-ratio `(a0,b0)` init (vs. the original's log-log OLS init), selected the identical model 240/240 times. |
| **Optimizer/method sensitivity** | Same 240-world sample, refit with `scipy.optimize.least_squares` (Trust Region Reflective, **with** explicit parameter bounds `a∈[1e-6,1e6]`, `b∈[-5,5]`, `c∈[-50,50]`) vs. the original's bounds-free `curve_fit` (Levenberg-Marquardt): 240/240 identical selections, max｜ΔBIC｜= 0.00019. |
| **BIC near-ties** | 26.3% of the 10,000 worlds have a BIC margin under 2.0 between the winning and runner-up model (Raftery 1995's "weak evidence" convention); 4.3% are under 0.1. These concentrate almost exactly where expected: `mass_exponential_descriptor` (48.6% of its 2,000 worlds are weak-evidence) and `mass_affine_descriptor` (35.6%) — the two families independently confirmed MARGINAL — versus `mass_interaction` (2.1%), confirmed IDENTIFIABLE at 100%. This is a mechanistic explanation *for*, not a threat to, the MARGINAL classification. |
| **Exact BIC ties** | Zero worlds have an exact tie (margin `== 0.0`) between the top two models, out of 10,000; the smallest observed margin anywhere exceeds 1e-6. `oracle_models.select_by_bic`'s `min(candidates, key=...)` would silently break an exact tie in dict-insertion order (favoring `M_mass` over `M_affine` over `M_sat` over `M_exp` over `M_inter`) — this is a latent code-smell (undocumented, order-dependent tie-break) but it never activates anywhere in the executed 10,000-world grid, so it had zero effect on any reported number. |
| **Floating-point tolerance** | The original hostile audit's own reproducibility check (D) used a `1e-9` absolute BIC tolerance across 40 re-run worlds; this audit's independent-optimizer re-fit (a strictly harder test — different code, not just a re-run of the same code) used no tolerance at all on the *selection* comparison (exact string equality of the selected model ID) across 240 worlds, and a max BIC deviation of 0.00019, five orders of magnitude below the weak-evidence scale. |
| **Sample-count convention** | `n_train=120` verified identical across all 50,000 individual fits (5 models × 10,000 worlds) — no cell used a different training-sample count, so the BIC comparisons within every world are apples-to-apples. |
| **Candidate parameterization** | Re-parameterizing with explicit bounds (above) did not change any selection outcome, so the report's conclusions do not depend on the specific unconstrained parameterization `oracle_models.py` uses. |

---

## 7. What this audit did not do

Per the goal's own scope: no symbolic search was run, no E3 threshold was moved, no
new model-selection rule was substituted, and E3 was not redesigned. This audit did
not re-verify E0, E1, E2, or any experiment other than E3. It did not attempt a formal
clustered/robust-variance re-analysis of every downstream statistic affected by the
`mass_power` non-independence (§3.1) beyond the two instances quantified directly (the
study-validity gate itself, and the frozen-operating-point confusion matrix's
`mass_power` row) — a full accounting of every pooled control statistic in
`e3_aggregate.json` is a bounded follow-up, not performed here, and is not needed to
answer the goal's questions since the point estimates themselves are all confirmed
correct regardless.

---

## 8. Deliverables

| File | Contents |
|---|---|
| `MURU_V2_E3_INDEPENDENT_HOSTILE_AUDIT.md` | This document |
| `MURU_V2_E3_INDEPENDENT_HOSTILE_AUDIT.json` | Machine-readable twin |
| `scripts/audit_e3/independent_completeness.py` | Q1/Q2 manifest+execution bijection, independently re-derived factor levels |
| `scripts/audit_e3/independent_pysr_probe.py` | Q4, broadened static+dynamic PySR/symbolic-engine absence probe |
| `scripts/audit_e3/check_control_duplication.py` | §3.1's `mass_power` duplication finding, from raw data |
| `scripts/audit_e3/independent_recompute.py` | §2's full recomputation of every headline table, reading only raw `e3_worlds.jsonl` |
| `scripts/audit_e3/robustness_scan.py` | §6's convergence/BIC-margin/sample-count scan |
| `scripts/audit_e3/independent_refit_sample.py` + `..._broad.py` | §6's independent-optimizer re-fit (75-world then 240-world stratified samples) |
| `results/audit_e3/*.json` | Raw output of every script above |

---

**E3 INDEPENDENT HOSTILE AUDIT COMPLETE**

**F09 remediation license:** survives independent review in full — `mass_saturating_descriptor`
is confirmed IDENTIFIABLE (82.0%, Wilson lower 0.751) at the frozen operating point
against an observed 0/12 real-search rate, licensing E4b/c/d to target it specifically.

**Conclusions requiring weakening:** one. The STUDY_INVALID gate's "narrow pass, not
comfortable" characterization should be read as *more* marginal than stated — a
correctly-computed Wilson upper bound (accounting for `mass_power`'s true 400
independent draws, not the nominal 2,000 row count) is 0.128, past the 0.10 line,
though the formal point-estimate-based pass (0.095 < 0.10) itself stands unchanged. No
other E3 conclusion requires retraction or weakening.
