# MURU v2 Experiment E3: Descriptor Identifiability — Results

**Status:** EXECUTED. 10,000/10,000 preregistered worlds, 0 missing, 0 duplicates, 0 execution failures, 0 symbolic searches, 0 PySR imports. Hostile audit: `OVERALL_PASS = true` (six independent checks, see section 15).

**Authority:** `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` (frozen at commit `befca0d`, design-only, dated before this execution) is the sole source of hypotheses, factors, metrics, and decision thresholds. Nothing in this document changes a threshold, a factor level, or a criterion after seeing a result. Every number in this report is a measurement against that frozen design.

**Branch / worktree:** `exp/v2-e3-identifiability`, rooted at `befca0d` (V2 remediation experiments prospectively designed — the commit containing the frozen E3 design, the v1 G1/G2/G3 failure taxonomy, and the root-cause ranking).

**Question answered.** Given the five correct parametric families in closed form, handed directly to a model-selection oracle with no search, no grammar, and no complexity budget: can the benchmark's data (noise, sample size, energy grid, covariate geometry) tell the planted family apart from a mass-only null and from its structured rivals? This is a hard ceiling on what any symbolic search could achieve on the same data — not a symbolic-search result, and none was run.

---

## 1. Study validity (checked first, per the frozen decision tree)

The design's own gate: *"If `false_structure_oracle` on the `mass_power` control exceeds 0.10, the study is INVALID and must be redesigned before any cell is used."* Computed on the full 2,000-world control population, before any other cell is interpreted:

| Selection criterion | False-structure rate | Wilson upper | Verdict |
|---|---:|---:|---|
| **BIC** | **0.095** (190/2000) | 0.109 | **VALID** — point estimate under 0.10, but the Wilson upper bound sits right at the boundary. Treated as a narrow pass, not a comfortable one. |
| **Validation R2 alone** | **0.685** (1370/2000) | 0.705 | **STUDY_INVALID** — a validation-R2-only criterion, with no complexity penalty, selects a spurious descriptor model on pure mass-only truth more than two-thirds of the time. |

**Consequence for the rest of this report.** Per the design's own rule ("Both selection criteria are reported. They are not combined into a single number, and neither is chosen after seeing the results"), both are reported throughout. But R2-alone is disclosed here as an invalid oracle-selection criterion in this setting, and no licensing conclusion in this report is drawn from it. **BIC is the criterion used for every classification decision below.** This is itself a finding, not a methodological adjustment made after the fact: BIC and validation R2 were pre-declared as the two criteria before any world was generated; the invalidity of one of them is a measured property of the design, not a change to it.

Why R2-alone fails here: at near-zero training/validation RSS (a well-fit case with any noise level, and trivially at `noise_sd=0`), the four descriptor models — each with one more free parameter than `M_mass` — can post a marginally higher validation R2 purely from fitting noise, since R2 has no term penalizing the extra parameter. BIC's `k*log(n)` penalty is exactly what R2 lacks, and it is what keeps the false-structure rate near the boundary rather than far past it.

---

## 2. Required output 1 — oracle family-recovery rate, overall

| Population | n | BIC rate | BIC 95% Wilson lower | Classification |
|---|---:|---:|---:|---|
| All 5 families (including the `mass_power` control, scored as "not-a-descriptor-model") | 10,000 | **0.8264** | 0.8189 | IDENTIFIABLE |
| Descriptor families only (excludes the control) | 8,000 | **0.8068** | 0.7980 | IDENTIFIABLE |

These are pooled across the **entire tested grid**, including coefficient levels (`c` up to 2.2) and noise levels far outside the frozen benchmark's actual operating point. They are ceiling measurements over the whole design space E3 was asked to sweep, not a statement about the benchmark as built. Section 5 gives the number that actually matters for v1 attribution: the rate **at the frozen coefficient support and the family's real production noise**.

---

## 3. Required output 2 — recovery by family (pooled over the whole grid)

| Family | n | BIC rate | R2 rate | BIC classification | R2 classification |
|---|---:|---:|---:|---|---|
| `mass_interaction` | 2000 | 0.9855 | 0.9325 | IDENTIFIABLE | IDENTIFIABLE |
| `mass_power` (control; rate = specificity, not recovery) | 2000 | 0.9050 | 0.3150 | — | — |
| `mass_saturating_descriptor` | 2000 | 0.8430 | 0.7410 | IDENTIFIABLE | MARGINAL |
| `mass_affine_descriptor` | 2000 | 0.7300 | 0.6065 | MARGINAL | MARGINAL |
| `mass_exponential_descriptor` | 2000 | 0.6685 | 0.5610 | MARGINAL | MARGINAL |

Two results contradict the pre-registered predictions (section 9 discusses this directly): `mass_interaction` was predicted MARGINAL (PE3-5) and measures as the *most* identifiable family tested; `mass_affine_descriptor` was predicted cleanly IDENTIFIABLE (PE3-1) and measures MARGINAL when pooled, and MARGINAL-to-WEAK at the actual frozen coefficient range (section 5).

---

## 4. Required output 3 — recovery by coefficient / effect-size regime

Pooled across all four descriptor families (excludes control), at each planted coefficient:

| `c` | n | BIC rate | R2 rate |
|---:|---:|---:|---:|
| 0.25 | 1600 | 0.6681 | 0.5769 |
| 0.40 | 1600 | 0.7569 | 0.6581 |
| 0.55 | 1600 | 0.8094 | 0.6944 |
| 1.10 | 1600 | 0.8813 | 0.7856 |
| 2.20 | 1600 | 0.9181 | 0.8363 |

Monotone increasing in `c`, as required for the measurement to be trusted (identifiability should rise with signal strength; a flat or non-monotone curve would have been a red flag for a harness bug). The **frozen benchmark's actual planted range is `c ~ U(0.25, 0.55)`** — the bottom three rows. Full per-family-per-coefficient breakdown: `results/e3_identifiability/e3_aggregate.json` → `recovery_by_family_and_coefficient`; every one of the 200 preregistered cells individually classified in `full_cell_classification_200_cells` (160 descriptor cells + 40 control cells).

---

## 5. Identifiability at the frozen benchmark operating point (the number that licenses or forbids search-side attribution)

`c` restricted to `{0.25, 0.40, 0.55}` (the actual `U(0.25,0.55)` support), `noise_sd = 0.02` (the default production noise for F01/F09/F10/F18-style cases), `grid = 6` (the frozen `ENERGY_GRID`). 150 worlds per family (n=50 × 3 coefficients).

| Family | n | BIC rate | BIC 95% Wilson lower | **Classification** | `c*` (BIC, smallest `c` reaching 0.80) |
|---|---:|---:|---:|---|---|
| `mass_interaction` | 150 | **1.000** | 0.975 | **IDENTIFIABLE** | 0.25 (bottom of ladder) |
| `mass_saturating_descriptor` | 150 | **0.820** | 0.751 | **IDENTIFIABLE** | 0.40 |
| `mass_affine_descriptor` | 150 | **0.553** | 0.473 | **MARGINAL** | 1.1 (above the frozen support) |
| `mass_exponential_descriptor` | 150 | **0.527** | 0.447 | **MARGINAL** | 1.1 (above the frozen support) |

**This is the headline table.** Two of the four descriptor families (`mass_interaction`, `mass_saturating_descriptor`) are cleanly IDENTIFIABLE within the benchmark's own planted range — G2 failures on those two families, wherever they occur, are attributable to the search or to retention (E2's and E4's territory), not to the benchmark. The other two (`mass_affine_descriptor`, `mass_exponential_descriptor`) are only MARGINAL at the frozen range: **per the frozen decision criterion, no search-side change may be justified from these two cells alone**, and both only cross the 0.80 bar at `c=1.1` — double the top of the frozen coefficient support.

---

## 6. Required output 4 — confusion matrix (rows = truth, columns = oracle-selected)

### At the frozen operating point (750 worlds: 150 × 5 families), BIC criterion

| Truth ↓ / Selected → | `mass_power` | `mass_affine` | `mass_saturating` | `mass_exponential` | `mass_interaction` |
|---|---:|---:|---:|---:|---:|
| `mass_power` | **132** | 0 | 0 | 3 | 15 |
| `mass_affine_descriptor` | 0 | **83** | 7 | 60 | 0 |
| `mass_saturating_descriptor` | 0 | 20 | **123** | 6 | 1 |
| `mass_exponential_descriptor` | 2 | 38 | 23 | **79** | 8 |
| `mass_interaction` | 0 | 0 | 0 | 0 | **150** |

**The single dominant error mode is bidirectional affine↔exponential confusion**: 60/150 affine worlds are mistaken for exponential, and 38/150 exponential worlds are mistaken for affine — by far the largest off-diagonal mass in the matrix (98 of 183 total off-diagonal errors across the full 750-world slice, 53.6%). `mass_saturating_descriptor` leaks moderately into both neighbors (20 to affine, 23 from exponential truth into saturating). `mass_interaction` has **zero** off-diagonal error in either direction — it is never mistaken for anything, and nothing is ever mistaken for it. `mass_power` leaks 15/150 (10%) into `mass_interaction` under BIC specifically at this noise level (the pooled 2,000-world control rate is 9.5%; this 750-world, noise=0.02-only slice runs slightly higher, consistent with sampling variation across the noise axis).

Full matrices (this slice and the full 10,000-world grid, both criteria) as machine-readable data: `results/e3_identifiability/e3_confusion_matrices.csv` and `e3_aggregate.json` → `confusion_matrix_frozen_operating_point` / `confusion_matrix_full_grid`.

---

## 7. Required output 5 & 6 — separation from mass-only and from the best wrong family

**Truth vs. mass-only** (`delta_r2_vs_mass`, validation split, at default noise/6-point grid): every descriptor family separates from `M_mass` in expectation at every tested coefficient, and the separation grows monotonically with `c` — mean deltas at `c=0.25` are small (0.007–0.038 across the four families) and grow to 0.18–0.30 at `c=2.2` (interaction 0.299, affine 0.270, saturating 0.187, exponential 0.182). The full per-cell distribution (mean/median/min/max/n) is in `e3_aggregate.json` → `truth_vs_mass_separation`. This confirms a synthesis point: **detecting that *some* descriptor effect exists (vs. mass-only) is almost never the problem, even at the smallest planted coefficient.** The problem, where one exists, is entirely in separating the *family* from its structured rivals (section 6).

**Truth vs. best wrong family** (`delta_r2_vs_best_wrong`, the empirically closest of the four wrong candidates, not just the pre-declared "nearest rival"): the identity of the closest wrong model confirms the confusion matrix directly —

| Truth family | Modal best-wrong model | Share of worlds |
|---|---|---:|
| `mass_affine_descriptor` | `M_exp` | 72.1% |
| `mass_exponential_descriptor` | `M_affine` | 69.4% |
| `mass_interaction` | `M_exp` (still loses to truth in 100% of frozen-range worlds) | 76.5% |
| `mass_saturating_descriptor` | `M_affine` | 79.9% |

Affine and exponential are each other's dominant confusion partner in both directions — this is not an artifact of one family being intrinsically "close to everything"; it is a specific, symmetric pair.

---

## 8. Required output 7 — identifiability curves

Oracle-selection rate (BIC) vs. planted coefficient `c`, at three reference slices. Full data: `e3_aggregate.json` → `identifiability_curves`.

**8.1 Default noise (0.02), 6-point grid — the frozen production regime:**

| `c` | affine | exponential | saturating | interaction |
|---:|---:|---:|---:|---:|
| 0.25 | 0.44 | 0.44 | 0.68 | 1.00 |
| 0.40 | 0.60 | 0.58 | 0.84 | 1.00 |
| 0.55 | 0.62 | 0.56 | 0.94 | 1.00 |
| 1.10 | 0.96 | 0.80 | 1.00 | 1.00 |
| 2.20 | 0.88 | 0.90 | 1.00 | 1.00 |

**8.2 Zero response noise, 6-point grid — H_id_noise (structural closeness vs. measurement error):**

| `c` | affine | exponential | saturating | interaction |
|---:|---:|---:|---:|---:|
| 0.25 | 1.00 | 0.98 | 1.00 | 1.00 |
| 0.40–2.20 | 1.00 | 1.00 | 1.00 | 1.00 |

**Every family is essentially perfectly identifiable at zero response noise, at every coefficient tested, including the smallest one.** This directly falsifies H_id_noise / PE3-2 as stated ("the failure survives at zero response noise, meaning it is structural closeness rather than measurement error"): the failure at the default noise level does **not** survive removing the noise. The confusability measured in section 5 is driven by the 0.02 response-noise sd propagating through the frozen `Phi`/`g` estimator, not by the affine and exponential curves being fundamentally inseparable shapes. This is a materially different and more optimistic remedy space than the pre-registered prediction implied: options that reduce estimation noise (more compounds, more energies, a tighter estimator) are live, not just coefficient re-specification.

**8.3 12-point energy grid, default noise — H_id_geometry:**

| `c` | affine (6pt → 12pt) | exponential (6pt → 12pt) | saturating (6pt → 12pt) |
|---:|---:|---:|---:|
| 0.25 | 0.44 → 0.60 | 0.44 → 0.50 | 0.68 → 0.78 |
| 0.40 | 0.60 → 0.72 | 0.58 → 0.44 | 0.84 → 0.90 |
| 0.55 | 0.62 → 0.88 | 0.56 → 0.68 | 0.94 → 0.96 |

Doubling energy resolution **materially helps affine** (crosses IDENTIFIABLE at `c=0.55` under 12 points, vs. needing `c=1.1` at 6 points) and **helps saturating modestly** (already identifiable at 6 points across most of the range, incrementally better at 12). It does **not** reliably help exponential (one point improves, one is flat/worse, within the ±0.07 sampling noise band at n=50) — see section 9. H_id_geometry is confirmed for affine and saturating; **not confirmed for exponential**.

---

## 9. Required output 8 — special analysis: F02, F03, F09, F18

Cross-referencing each family's E3 oracle ceiling (at the frozen coefficient support, `grid=6`) against v1's own **observed search-generation rate** — `truth_equivalent_ever_generated`, i.e. whether *any* of the 30 PySR seeds ever retained a correct candidate, independent of whether cross-seed voting then kept it. This is the correct comparison for RC4's question (identifiability vs. generation), as distinct from RC3's retention question.

| Case | Truth family | Noise sd | v1 observed (any-seed generation) | E3 oracle ceiling (BIC) | E3 classification |
|---|---|---:|---:|---:|---|
| **F02** | `mass_affine_descriptor` | 0.0295 | 3/12 (25.0%) | **48.7%** | WEAKLY_IDENTIFIABLE |
| **F03** | `mass_affine_descriptor` | 0.06 | 1/12 (8.3%) | **36.0%** | WEAKLY_IDENTIFIABLE |
| **F09** | `mass_saturating_descriptor` | 0.02 | 0/12 (0.0%) | **82.0%** | **IDENTIFIABLE** |
| **F18** | `mass_exponential_descriptor` | 0.02 | 0/12 (0.0%) | **52.7%** | MARGINAL |

(For reference, `g2_success` — final case-level pass after cross-seed voting — is 0/12 for all four, and 2/12 even for F01, the default-noise affine case whose seeds generate the correct candidate in 12/12 cases; that F01 gap is RC3's retention/voting problem, outside E3's scope.)

**Reading each row:**

- **F02** (moderate noise, `sd=0.0295`): oracle ceiling is under 50% even before any search runs. The search's 25% observed generation rate is *below* the ~49% ceiling but in the same regime — some of the shortfall is data-limited (a perfect oracle would still fail roughly half the time), and there may be additional room the search is leaving on the table below that ceiling, but the cell itself is WEAKLY_IDENTIFIABLE and **forbids citing it alone to justify a search-side change**.
- **F03** (strong noise, `sd=0.06`): same pattern, worse — 36% ceiling vs. 8.3% observed. Primarily data-limited; `c*` does not exist anywhere on the tested ladder at this noise level (does not reach 0.80 even at `c=2.2` — see `e3_aggregate.json` → `c_star_table`).
- **F09** (saturating, default noise): **the clean search-limited case in this study.** The oracle ceiling is a strong 82%, comfortably IDENTIFIABLE — the signal is there and separable — yet the observed any-seed generation rate across 360 real searches is exactly zero. Per the goal's own critical-interpretation rule, this is squarely a search-generation problem, not a benchmark-construction fact. E4b/c/d are licensed for this family.
- **F18** (exponential, default noise): the oracle ceiling is 52.7%, MARGINAL — below the 0.80 bar needed to license search-side attribution, but also well above zero, and (section 8.2) driven almost entirely by response noise rather than fundamental inseparability. v1's observed 0/12 is **not informative here regardless**: RC6 (the grammar excludes `exp`) makes generation mechanically impossible for F18 under the current grammar no matter how identifiable the family is, so the 0/12 figure reflects the grammar gap, not identifiability. Section 10 resolves the E5 question this was designed to gate.

---

## 10. Required output 9 — is F18's exponential family distinguishable under its intended geometry?

"Intended geometry" = the family's actual production design point: `grid=6` (frozen `ENERGY_GRID`), `noise_sd=0.02` (F18's real noise), `c` in the frozen `{0.25, 0.40, 0.55}` support.

| | n | BIC rate | R2 rate | Classification (BIC) |
|---|---:|---:|---:|---|
| **Intended geometry (grid=6)** | 150 | **0.527** | 0.347 | **MARGINAL** |
| 12-point grid, same `c`/noise | 150 | 0.540 | 0.380 | MARGINAL (unchanged) |

**Answer: no, not reliably — but not cleanly unidentifiable either.** F18 sits in the MARGINAL band under its intended geometry, and does not move out of it under a doubled energy grid (0.527 → 0.540, within sampling noise). Per the design's own decision rule, MARGINAL both licenses nothing and forbids nothing on its own; but E5 section 5.3 requires an **IDENTIFIABLE** verdict (Test 2) before evaluating whether admitting `exp` to the grammar is worth its safety cost (Test 3). A MARGINAL verdict does not clear that bar. Applying the design's decision tree conservatively (the same "no attribution from a MARGINAL cell alone" rule used everywhere else in this study): **admitting `exp` to the grammar is not licensed by this measurement.** The resolution space for F18 remains O5 (remove F18 from the family-recovery population), O6 (re-specify its coefficient under the difficulty guard — `c*` for F18 is `1.1`, double the current planted value), or O7 (replace F18's truth with an algebraically difficult but grammar-expressible form). This is a **partial**, not full, confirmation of the pre-registered PE5-1 (which predicted an unambiguous WEAKLY_IDENTIFIABLE, ruling out O2/O3/O4 outright) — the measured result is softer than predicted (MARGINAL, not WEAK), for the same reason section 8.2 gives: the confusability is noise-driven, not purely structural, so it is closer to the identifiability boundary than the design-time arithmetic anticipated.

---

## 11. Every G2 truth family — explicit identifiability disposition

| Family | Frozen-range oracle rate (BIC) | Disposition | `c*` (BIC) | Search-side attribution licensed at frozen range? |
|---|---:|---|---:|---|
| `mass_power` (specificity control, not a G2 truth family) | 90.5% specificity (pooled), false-structure 9.5% | Control passes at the boundary (see section 1) | — | N/A |
| `mass_affine_descriptor` | 55.3% | **MARGINAL** | 1.1 | **No** |
| `mass_saturating_descriptor` (F09) | 82.0% | **IDENTIFIABLE** | 0.40 | **Yes** |
| `mass_interaction` | 100.0% | **IDENTIFIABLE** | 0.25 | **Yes** |
| `mass_exponential_descriptor` (F18) | 52.7% | **MARGINAL** | 1.1 | **No** |

---

## 12. Search-limited vs. data-limited — the interpretation the goal asks for directly

Applying the rule stated in the task: *if the oracle cannot reliably distinguish a family, more search compute is not the primary remedy; if oracle discrimination is strong but search recovery was weak, it is a search problem.*

- **DATA-LIMITED (do not recommend more search compute or a looser search as the primary remedy): `mass_affine_descriptor`, `mass_exponential_descriptor`.** Both sit at MARGINAL (53–55%) at the frozen coefficient range and both only reach IDENTIFIABLE at `c=1.1`, double the planted support. Section 8.2 adds a specific, actionable qualifier: for both families this ceiling is driven by response-measurement noise propagating through the `g`-estimator, not by fundamental shape-inseparability (noise-free recovery is ~100% for both) — so the benchmark-side remedy space includes noise/precision-side changes (more compounds, more replicate energies within the frozen grid range, a tighter estimator), not only raising the planted coefficient. Any change to either family's planted magnitude is subject to the difficulty guard (external scientific rationale required, not just "E3 measured a floor").
- **SEARCH-LIMITED (a genuine engine target): `mass_saturating_descriptor` (F09).** 82% oracle ceiling against 0% observed generation across 360 real searches is the largest oracle-ceiling-vs-observed-search gap in this study, and it clears the IDENTIFIABLE bar cleanly. E4b (budget), E4c (objective/parsimony), and E4d (grammar) are licensed to investigate this family specifically.
- **GRAMMAR-LIMITED FIRST, THEN MARGINAL: `mass_exponential_descriptor` (F18).** Mechanically capped at zero by RC6 regardless of identifiability, and even if that cap were lifted, MARGINAL (52.7%) does not clear the bar E5 requires before the grammar change is worth its safety cost. F18's problem is not fixable by search-side changes at its current coefficient; whether it is worth a grammar change is foreclosed by the identifiability finding here, independent of RC6.
- **NOT ASSESSED FOR SEARCH-VS-DATA ATTRIBUTION HERE: `mass_interaction`.** 100% oracle ceiling at every tested coefficient (the strongest result in the study) makes this family unambiguously IDENTIFIABLE; any G2 shortfall on interaction-family cases, wherever it exists, is entirely a search or retention question (E2/E4's territory), never a benchmark-construction one. This study did not measure v1's actual interaction-family search-generation rate (outside the preregistered F02/F03/F09/F18 special-analysis list), so no specific search-vs-retention split is claimed for it here.

**Explicitly not claimed:** this study does not determine *why* F09's search generation is zero despite an 82% oracle ceiling (budget, objective, grammar, or something else) — that is E4's job, gated open by this result, not answered by it. Likewise, RC3 (within-seed retention losing correct candidates the search already found, documented for `mass_affine_descriptor`/F01 in the frozen root-cause ranking) is a separate, already-identified factor for the affine family that this study neither re-measures nor attributes to; E3 measures only whether the signal exists to be found at all.

---

## 13. Methodology notes (what a reviewer needs to check the numbers)

- **Generation.** Every world's covariates (`mass`, `descriptor`, `descriptor2`, scaffold/split structure) are generated by a line-for-line transcription of the frozen `generator._synthetic_compounds` algorithm, seeded under a namespace (`muru-v2-calibration|`) disjoint from the frozen benchmark's own (`paper-benchmark-v1|`) — asserted disjoint at import time, per `MURU_V2_A1_STUDY_DESIGN.md` section 5. The five truth laws are the frozen generator's exact closed forms (`generator.py::_law`), with the planted coefficient taken as an explicit per-cell parameter `c` instead of the frozen `rng.uniform(0.25,0.55)` draw (which cannot be overridden in place), and the M0 collapse-response branch of `generator.py::_response_matrix`, with noise sd and the energy grid as explicit parameters instead of a kind-keyed lookup. E3 never generates M1/M2/M3 adequacy deviations — every world is true M0. Code: `scripts/e3_identifiability/v2c_generator.py`.
- **Estimation.** `Phi`/`g` are estimated by the **frozen, unmodified** `rc5_estimate.fit_case_scalars` (imported read-only from the sealed run's own source tree, `.claude/worktrees/heldout-analysis-restoration/src`) — the exact two-stage fold-local isotonic-Phi-then-grid-search-plus-parabolic-refinement estimator the real symbolic search consumes. E3 measures identifiability on `g_hat`, the estimated quantity, never on the planted truth `g`.
- **Oracle fitting.** Five closed-form models fit by nonlinear least squares (`scipy.optimize.curve_fit`) against `g_hat`, on the 120 training-scaffold compounds; scored on the 30-compound validation and 30-compound test splits. No search, no grammar, no complexity budget beyond the two model-selection criteria themselves. Code: `scripts/e3_identifiability/oracle_models.py`.
- **Selection statistics.** BIC = `n*log(RSS_train/n) + k*log(n)` on training residuals (`n=120`); validation R2 = `1 - SS_res/SS_tot` on the validation split. LRT p-values: classical nested chi-square LRT for each descriptor family against `M_mass` (every one of the four reduces exactly to `M_mass` at `c=0`, so all four comparisons are genuinely nested, df=1); Vuong's (1989) non-nested test for the three same-parameter-count rival comparisons (`M_sat`/`M_exp`/`M_inter` vs. `M_affine`, which are not nested in each other).
- **The 12-point energy grid** (H_id_geometry's "double the resolution" arm) is not numerically specified in the design docs beyond "12 points" — the disclosed, stated choice made here is 12 points evenly spaced over the same `[15, 90]` range the frozen 6-point grid covers (`np.linspace(15, 90, 12)`), isolating resolution from range.
- **The `mass_power` control's coefficient axis.** The control's law does not consume `c` at all, so its five "`c`-label" cells within a fixed `(noise, grid, replicate)` are content-identical by construction (same seed, since seeds derive from `geometry_id`, which excludes `c`, exactly the "paired seeds across the `c` ladder" control the design specifies for the descriptor families). This is why the manifest still totals the pre-registered 10,000 worlds exactly as declared, not 8,400 — the Cartesian product is generated in full as pre-registered, and the redundancy for the control is disclosed rather than silently collapsed.
- **Storage.** `e3_worlds.jsonl` (30.4 MB) + `e3_per_world_table.csv` (4.8 MB) + `e3_manifest.json` (2.5 MB) ≈ 37.7 MB, under the declared 100 MB budget. Runtime: 55.6 seconds wall-clock on 7 worker processes (design estimate: 2–4 CPU-hours; the measured cost is well under that estimate).

---

## 14. Deliverables

| File | Contents |
|---|---|
| `E3_RESULTS.md` | This document |
| `results/e3_identifiability/e3_manifest.json` | All 10,000 preregistered `(family, c, noise, grid, replicate)` cells + completeness verification |
| `results/e3_identifiability/e3_worlds.jsonl` | Per-world record: truth family, all 5 model fits (params, SE, BIC, R2 train/val/test), oracle decisions under both criteria, LRT/Vuong p-values, seeds |
| `results/e3_identifiability/e3_per_world_table.csv` | Flat per-world table (the "per-world table" deliverable) |
| `results/e3_identifiability/e3_aggregate.json` | Every aggregate in this report, machine-readable |
| `results/e3_identifiability/e3_confusion_matrices.csv` | Confusion matrices (full grid + frozen operating point, both criteria), flat data |
| `results/e3_identifiability/e3_hostile_audit.json` | Section 8 below, machine-readable |
| `results/e3_identifiability/e3_hashes.json` | SHA-256 + byte size of every artifact and script |
| `scripts/e3_identifiability/*.py` | `v2c_generator.py`, `oracle_models.py`, `manifest.py`, `run_e3.py`, `aggregate_e3.py`, `hostile_audit_e3.py`, `_bootstrap.py` |

---

## 15. Hostile audit summary

Full detail in `results/e3_identifiability/e3_hostile_audit.json`. All six checks pass (`OVERALL_PASS: true`):

| Check | Result |
|---|---|
| **A/B — 100% of 200 preregistered cells / 10,000 worlds executed** | Manifest ⟷ executed world-ID sets are an exact bijection. 0 missing, 0 extra, 0 duplicates, 0 execution failures (10,000/10,000 `status=OK`). |
| **C — 0 PySR imports** | Static grep of every touched file (the six E3 scripts + `generator.py`, `rc5_estimate.py`, `adequacy.py`, `structural_acceptance.py`, `registry.py`, `truth.py`, `discovery/estimate.py`, `discovery/grammar.py`): zero `import pysr` / `from pysr` statements. Dynamic check: ran a real world through the actual worker in a fresh subprocess and inspected `sys.modules` — zero pysr-named modules loaded. |
| **D — Reproducibility** | 40 worlds sampled at random and re-run from `world_id` alone through the identical harness: every persisted decision (BIC-selected model, R2-selected model, oracle-correctness flags) and every model's BIC to 1e-9 absolute tolerance reproduced exactly. 0 mismatches. |
| **E — No post-result criterion changes** | The 0.80/0.50/0.10 thresholds, the five truth families, the `c`/noise/grid levels, and the 10,000-world/0-search case count used by the code are verified, by direct text/JSON comparison, to be exactly what `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` and `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json` declared before this run. |
| **F — Aggregate counts reconcile exactly** | 10,000 total = 5 families × 2,000 each; 200 cells × 50 replicates = 10,000; every confusion-matrix row at the frozen operating point sums to exactly 150; descriptor-only population is exactly 8,000; control population is exactly 2,000. |

---

## 16. What this study does not do

Per the frozen prohibitions: no PySR was imported or run; no search-budget parameter exists anywhere in this code; no v1 Held-out result was read to select any E3 parameter (every factor level — `c` ladder, noise levels, grid points, replicate count — is copied verbatim from the frozen design document, itself written before this execution); no post-result effect-size or threshold change was made (section 15, check E); no Challenge or Confirmation data was read, generated, or referenced. This experiment does not choose a v2 architecture, does not license E4's engine-side ablations by itself (it only opens or closes that door per family), and does not resolve E5 (it answers E5's Test 2 gate for F18 specifically: MARGINAL, not IDENTIFIABLE).

---

**E3 COMPLETE - G2 IDENTIFIABILITY CEILING ESTABLISHED**
