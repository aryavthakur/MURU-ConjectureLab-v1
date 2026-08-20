# MURU ACCURACY OPTIMIZATION

**Mode**: RAPID_EXPLORATORY, NOT CONFIRMATORY
**Objective**: maximize actual scientific accuracy of MURU using the existing checkpoint data
**New PySR searches run**: **0**
**Data surface used**: 323 worlds x 30 seeds = 9,690 existing search outputs; 26,600 Pareto-band candidates scored individually against truth

---

## 1. Headline

| Metric | Owner's stated current (6 seeds) | BASELINE_30 (existing selector, all 30 seeds) | **Selected architecture (pooled held-out CV)** |
|---|---|---|---|
| Support recovery | 92.9% (52/56) | 100.0% (56/56) | 98.2% (55/56) ungated, 96.4% (54/56) after gate |
| Family recovery | 71.4% (40/56) | 75.0% (42/56) | **83.9% (47/56)** |
| Exact/form recovery | not reported | 41.1% (23/56) | 39.3% (22/56) |
| Null worlds reporting a candidate | 230/230 (100%) | 230/230 (100%) | **7/230 (3.0%)** |
| G1A support / family | 6/6 / 6/6 | 6/6 / 6/6 | 6/6 / 6/6 |
| G1B support / family | 39/40 / 30/40 | 40/40 / 32/40 | 39/40 / **35/40** |
| G1C support / family | 7/10 / 4/10 | 10/10 / 4/10 | 10/10 / **6/10** |

Two separate things improved. Using all 30 seeds instead of 6 fixes support recovery on its own (92.9% -> 100%). The new aggregation architecture is what moves **family recovery, 75.0% -> 83.9%**, and it does so entirely by better use of candidates that were already in the pool. The refusal gate takes null reporting from 100% to 3.0% at a cost of one true support recovery.

**Targets set by the brief**: support >= 95% met (98.2% ungated / 96.4% end-to-end); family >= 80% met (83.9%); null held-out FPR <= 5% met (3.0%).

---

## 2. Experimental discipline

* Deterministic stratified **5-fold cross-validation by WORLD**. All 30 seeds of a world are in the same fold. Strata are `block x noise_regime x category`, worlds ordered inside a stratum by `sha256(world_id)` and dealt round-robin.
* No seed of a test-fold world participates in threshold fitting or variant selection for that fold.
* All five architectures, all three family votes, both representative rules and the gate feature set were written down in `scripts/accopt_selectors.py` **before** any cross-validated number was computed. No variant was added after seeing a fold result.
* Selectors read only outcome-independent candidate statistics. Truth fields are present in the candidate cache but are used only to score a selection after it is made.
* This remains exploratory. Aggregate outcomes from this benchmark have already been inspected in prior work, so nothing here is confirmatory.

### 2.1 Method that made this cheap

Every Pareto-band member of every seed of every world was scored against the planted law once, in a single 165-second pass, and cached. Scoring **all 26,600 candidates** rather than only the one the selector picked is what makes every selector variant free to evaluate and makes the oracle ceiling mechanically computable rather than estimated.

---

## 3. Architecture comparison, pooled held-out

| Architecture | Support | Family | Exact | G1A fam | G1B fam | G1C fam |
|---|---|---|---|---|---|---|
| BASELINE_30 | 56/56 | 42/56 (75.0%) | 23/56 | 6/6 | 32/40 | 4/10 |
| SUPPORT_CONSENSUS | 55/56 | 41/56 (73.2%) | 23/56 | 6/6 | 31/40 | 4/10 |
| SUPPORT_PLUS_FAMILY_CONSENSUS | 55/56 | 45/56 (80.4%) | 27/56 | 6/6 | 35/40 | 4/10 |
| CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE | 55/56 | **47/56 (83.9%)** | 22/56 | 6/6 | 35/40 | 6/10 |
| **CONSENSUS_PLUS_REPRESENTATIVE_PLUS_REFUSAL_GATE** | 54/56 | **47/56 (83.9%)** | 22/56 | 6/6 | 35/40 | 6/10 |

95% Wilson intervals on the selected architecture: support 98.2% [90.6%, 99.7%], family 83.9% [72.2%, 91.3%].

**Family vote chosen: B2, the validation-quality-weighted vote.** All 5 folds chose it independently. B1 (unweighted seed majority) gives 41/56 and B3 (stability-weighted over 200 deterministic 15-seed subsets) gives 38/56, worse than the baseline. Weighting the family vote by how well each seed's best member in that family actually validates is the single largest gain in the study: +4 worlds.

**Representative rule chosen: R1, highest validation R^2 inside the selected support-and-family group.** All 5 folds chose it independently. R1 beats R2 (near-best band within 0.01 absolute R^2, then lowest complexity) by +2 family worlds, both in G1C. R2 is better for exact-form recovery (28/56 vs 22/56 at the B2 vote), so the two rules trade family recovery against exact-form recovery. The brief ranks family recovery first, so R1 is selected; this trade is real and is stated rather than hidden.

**SUPPORT_CONSENSUS alone is a small net negative** (-1 support, -1 family). Modal-support voting costs one G1B world where the modal support carries a spurious extra `n_S` block. It is kept because it is the substrate the family vote runs on and because the refusal gate correctly suppresses that exact world.

---

## 4. Null and refusal gate

**Rule (2 quantities, interpretable):**

```
REPORT  iff  median_over_seeds(best validation R^2)  >= t1
       AND  selection_fraction(reported family)      >= t2
```

Calibrated inside each training fold only, maximizing positive sensitivity subject to training null FPR <= 5%. Fitted thresholds were stable: `t1` = 0.595 in 4 of 5 folds (0.725 in one), `t2` = 0.2 in 4 of 5 folds (0.433 in one).

### Pooled held-out performance (null = NCAL + G4 + G4M, n = 230; positive = G1A + G1B + G1C, n = 56)

| Quantity | Value |
|---|---|
| Sensitivity | **96.4%** (54/56), 95% CI [87.9%, 99.0%] |
| Specificity | **97.0%** (223/230) |
| False-positive rate | **3.0%** (7/230), 95% CI [1.5%, 6.1%] |
| False-negative rate | 3.6% (2/56) |
| Balanced accuracy | **96.7%** |
| ROC AUC (median seed best R^2) | 0.9991 |
| PR AUC (median seed best R^2) | 0.9968 |
| ROC AUC (selection fraction) | 0.9124 |
| PR AUC (selection fraction) | 0.8398 |

At the selection stage the prior system reported a candidate on 230/230 null worlds, so report/refusal discrimination there was not weak, it was absent. It is now 97.0% specific at 96.4% sensitivity, using only candidate statistics and without the full NCAL sweep or falsification harness that the downstream acceptance stage would require.

### Refusal worlds, evaluated separately

Null and refusal are **not** combined, because they answer different scientific questions.

| Block | n | Reported | Reported with non-mass structure | Correct behaviour |
|---|---|---|---|---|
| G4 (pure null) | 100 | **0** | 0 | refuse |
| NCAL (link destroyed) | 100 | 6 | 5 | refuse |
| GC (cutoff artefact, no descriptor law) | 9 | 2 | 1 | refuse |
| G4M (mass-conditional null) | 30 | 1 | **0** | mass-only or refuse |
| G3 (mass-only world) | 8 | 8 | **0** | mass-only, refuse any non-mass claim |
| G5 (true driver unobserved) | 8 | **0** | 0 | refuse |
| GRT (retention-time surrogate) | 4 | 1 | 1 | refuse |
| G2 (predictable, not compressible) | 8 | 5 | 4 | refuse |

Grouped by scientific semantics:

* **No descriptor law exists at all** (NCAL + G4 + GC, n=209): 8 reported, 3.8%; 6 of those claim non-mass structure. This is the false-discovery surface and it is at 3.8%.
* **Mass-only worlds** (G3 + G4M, n=38): 9 reported, and **0 of them claim any structure beyond mass**. The K5 threat, promoting a non-mass structural claim in a mass-only world, is realized **zero times in 38 worlds**. G3's 8/8 report rate is correct behaviour, not a failure: G3 has a real `c * m^p` law, and the architecture recovers its support 8/8 and its family 8/8 with no invented non-mass term.
* **Confounded / non-compressible** (G5 + GRT + G2, n=20): 6 reported, 5 with non-mass structure. **G5 is 0/8**, the hardest and most important case, where the true driver is never supplied. G2 at 5/8 is the weakest cell: a regime-switched world is genuinely predictable over most of the domain, and a two-quantity gate on validation quality cannot see the switch.

Validation-R^2 separation (median over 30 seeds of each seed's best validated R^2):

| Population | n | mean | median | p95 |
|---|---|---|---|---|
| positive | 56 | 0.938 | 0.966 | 0.997 |
| null | 230 | 0.080 | -0.001 | 0.595 |
| refusal | 37 | 0.622 | 0.722 | 0.934 |
| no-law subset | 209 | 0.046 | -0.002 | 0.619 |
| mass-only subset | 38 | 0.487 | 0.464 | 0.929 |
| confounded subset | 20 | 0.667 | 0.653 | 0.923 |

Positives and nulls separate almost perfectly (AUC 0.999). Refusal worlds sit in between by construction, which is exactly why a validation-quality gate cannot fully solve them and why they are reported separately.

---

## 5. Oracle ceilings

Computed mechanically over every one of the 26,600 band members, not estimated.

| Population | n | **Oracle support ceiling** | **Oracle family ceiling** | Oracle exact ceiling |
|---|---|---|---|---|
| All positives | 56 | **56/56 = 100.0%** | **54/56 = 96.4%** | 45/56 = 80.4% |
| G1A | 6 | 6/6 | 6/6 | 5/6 |
| G1B | 40 | 40/40 | **40/40** | 34/40 |
| G1C | 10 | 10/10 | 8/10 | 6/10 |
| G3 | 8 | 8/8 | 8/8 | 8/8 |
| G4M | 30 | 30/30 | 22/30 | 16/30 |

Seed-level availability of the correct structure among the 30 seeds:

| Block | worlds | median seeds with correct support | min | median seeds with correct family | min | worlds with 0 family-correct seeds |
|---|---|---|---|---|---|---|
| G1A | 6 | 30 | 30 | 30 | 29 | 0 |
| G1B | 40 | 30 | 11 | 30 | 2 | 0 |
| G1C | 10 | 30 | 30 | 17.5 | 0 | **2** |

**Every G1B world has a family-correct candidate in the pool, in a median of 30 of 30 seeds.** The search is not failing to find the law. The selector is failing to promote it.

Achieved family recovery is 47 of a reachable 54. **Seven of the nine remaining errors are selection errors, not search errors.**

---

## 6. Failure analysis

Every failed positive world was checked mechanically for whether a correct candidate exists anywhere among its 30 seeds.

| Failure type | Count (of 56 positives) |
|---|---|
| Correct (family recovered and reported) | **47** |
| SEARCH_FAILURE | **2** |
| SUPPORT_SELECTION_FAILURE | **0** |
| FAMILY_SELECTION_FAILURE | 3 |
| REPRESENTATIVE_FAILURE | 2 |
| NULL_GATE_FAILURE | 2 |
| ALGEBRAIC_ADJUDICATION_FAILURE (re-classification of 2 of the 7 above) | 2 |

`ALGEBRAIC_ADJUDICATION_FAILURE` is a lens on the same failures, not a disjoint bucket. It counts cases where the adjudicator's verdict is decided by a knife-edge threshold crossing.

### The two SEARCH_FAILURE worlds are a representability limit, not a budget limit

`OV|G1C|r001|moderate` and `OV|G1C|r002|moderate`. Across all 30 seeds and every band member, the **best achievable relative RMSE against truth is 0.165 and 0.157**. The frozen family tolerance is 0.10. Nothing in the pool is close, and nothing gets close.

G1C plants `g = s * sqrt(m) * exp(a*(x - xbar))`. `exp` is **not an operator in the frozen grammar** (DEVIATIONS_P3 D1); the truth is deliberately outside the hypothesis space. Doubling `niterations` from 40 to 80 searches the same space harder and cannot represent a function the space does not contain. In the other 8 G1C worlds the first-order expansion happens to land inside tolerance; in these 2 it does not.

### The seven selection failures

For all seven, the best member in the pool sits at **rel_rmse 0.0008 to 0.075** against truth, well inside the 0.10 family tolerance, with **2 to 35 family-correct members present**. In every one of the seven, the correct **support** was selected. The error is downstream of support.

| World | Type | Family-correct members in pool | Best member rel_rmse | Chosen representative rel_rmse | Adjudicator's stated reason |
|---|---|---|---|---|---|
| `OV\|G1B\|r005\|adverse` | REPRESENTATIVE | 30 | 0.0108 | 0.0751 | exponent in `n_O` differs by 0.156 |
| `OV\|G1C\|r008\|moderate` | REPRESENTATIVE | 17 | 0.0164 | 0.0978 | exponent in `n_O` differs by 0.153 |
| `OV\|G1B\|r004\|adverse` | FAMILY_SELECTION | 18 | 0.0092 | 0.0997 | predictions disagree, rel_rmse 0.0997 |
| `OV\|G1B\|r007\|adverse` | FAMILY_SELECTION | 4 | 0.0240 | 0.1024 | exponent in `rotatable_bonds` differs by 0.169 |
| `OV\|G1C\|r007\|moderate` | FAMILY_SELECTION | 2 | 0.0752 | 0.1960 | exponents in MASS and `rotatable_bonds` differ |
| `OV\|G1B\|r009\|adverse` | NULL_GATE (false negative) | 3 | 0.0129 | 0.0967 | gate: median seed R^2 = 0.596 vs t1 = 0.595-0.725 |
| `OV\|G1B\|r015\|moderate` | NULL_GATE (correct refusal of a wrong report) | 35 | 0.0008 | 0.1525 | support included a spurious `n_S` block |

Five of these seven are **adverse or hard-regime worlds**, which is where the practical accuracy limit now lives.

### Adjudication boundary cases

Four of the seven selection failures are decided by a threshold crossing of under 15% of the threshold's own value:

* exponent differences of **0.153, 0.156, 0.169** against a frozen tolerance of **0.15**
* a numeric rejection at **rel_rmse 0.0997** against a frozen tolerance of **0.10**

`OV|G1C|r008` is the cleanest case: numerics are *inside* the family band (rel_rmse 0.0978, r = 0.9908) and the rejection rests entirely on a single block exponent being 0.003 over tolerance. **These tolerances were not moved.** Moving a frozen tolerance after seeing which worlds it fails is exactly the arbitrary substitution the protocol exists to prevent. They are recorded here as the candidate list for a later targeted CAS experiment.

**Expression list for a future targeted Wolfram experiment** (do not replace the CAS blindly; these are the specific expressions where SymPy-side elasticity estimation and the frozen tolerance jointly decide the verdict):

```
OV|G1C|r008|moderate  sqrt(precursor_mz) * (square((n_O * 0.21075006) + 0.68927985) + 0.43984783)
OV|G1B|r005|adverse   sqrt(((-0.11378239 + precursor_mz) * n_O) + precursor_mz)
OV|G1B|r004|adverse   precursor_mz + (((total_atom_count * (rotatable_bonds * 0.3312732)) + 0.093993716) / total_atom_count)
OV|G1B|r007|adverse   (sqrt(precursor_mz) + (square(rotatable_bonds) * 0.0136330975)) * ((rotatable_bonds * 0.38231987) + 0.9201102)
```

The block exponents at issue are estimated numerically by central log-difference on a 2,000-point lattice, not symbolically. Whether a symbolic-exact exponent would place these inside tolerance is a real, answerable question and is the correct scope for a Wolfram comparison.

---

## 7. Is new PySR search necessary?

**No.**

| Evidence | Value |
|---|---|
| Oracle support ceiling | 100.0% (56/56) |
| Oracle family ceiling | 96.4% (54/56) |
| Achieved family recovery | 83.9% (47/56) |
| Reachable but unreached | **7 worlds, all selection errors** |
| Genuine SEARCH_FAILURE worlds | **2**, both G1C |
| Median seeds per G1B world already producing a family-correct candidate | **30 of 30** |
| Best achievable rel_rmse in the 2 search-failure worlds | 0.165, 0.157 vs a 0.10 tolerance |

The conditional in the brief is not triggered. Genuine search failure is 2 of 56 positive worlds (3.6%), and both are worlds whose planted law is provably outside the frozen grammar because `exp` is not an available operator. Doubling `niterations` from 40 to 80 explores the same hypothesis space and cannot represent a function outside it, so the preferred intervention is specifically ineffective against the only search failures that exist. **No ACCURACY_RESCUE_EXPLORATORY search was run and none is warranted.** The one search-side change that could move these 2 worlds is a grammar change (adding `exp`), which is out of scope here and would change five things at once.

---

## 8. Where is the accuracy bottleneck?

**REPRESENTATIVE SELECTION and FAMILY AGGREGATION**, with **ALGEBRAIC ADJUDICATION** as a secondary and now-quantified contributor.

**Not** SEARCH. **Not** SUPPORT AGGREGATION.

### Evidence

1. **SUPPORT AGGREGATION is solved.** Oracle support ceiling 100%, achieved 98.2%. Zero SUPPORT_SELECTION_FAILURE worlds. Every one of the nine failures had the correct support selected except the one the gate correctly refused.
2. **SEARCH is not the bottleneck.** Every G1B world has a family-correct candidate present, in a median of 30 of 30 seeds; the worst case is 2 of 30. Only 2 of 56 worlds lack one, and those 2 fail for representability, not budget.
3. **FAMILY AGGREGATION is worth +4 worlds and was being left on the table.** Simply reweighting the family vote by validation quality (B2) instead of raw seed count moved family recovery from 41/56 to 45/56 with no other change. Separately, the *selection* stage `muru.objval.select.select()` returns `families[0]` unconditionally: the frozen `MIN_SELECTION_FRACTION = 20/30` is defined in that module but is not applied inside it, which is exactly why selection reports on every null world. A downstream acceptance stage does exist (`muru.objval.adjudicate.accept`, which applies `MIN_SELECTION_FRACTION`, a calibrated null threshold, a ceiling fraction and a falsification harness), but it needs the full NCAL sweep and the falsification harness, was not part of the rapid path, and is not what this study measured. The gate here is a deliberately lightweight substitute that lives at the selection stage and needs only candidate statistics.
4. **REPRESENTATIVE SELECTION is worth a further +2 and is the largest remaining lever.** In `OV|G1B|r005|adverse` **30 members of the chosen family are family-correct** and the rule still promoted a wrong one. The representative rule adjudicates the scientific claim, yet it currently ranks on a scalar (R^2 or complexity) that is blind to the structural quantity being adjudicated. Choosing the *structurally modal* member of a family, rather than its best-fitting or simplest member, is the obvious untested next lever. It was deliberately **not** tested here because it was not in the pre-defined variant set and adding it after seeing these failures would be the overfitting the brief forbids.
5. **ALGEBRAIC ADJUDICATION decides 4 of the 7 selection failures at the margin.** Exponent differences of 0.153 / 0.156 / 0.169 against a 0.15 tolerance, and a numeric rejection at 0.0997 against a 0.10 tolerance. These are knife-edge crossings on numerically estimated exponents. This is a real contributor, it is now measured, and it is the correct scope for the later Wolfram experiment.
6. **NULL/REFUSAL GATE is no longer a bottleneck for nulls and is one for G2.** Null FPR is 3.0% held-out against a 5% budget, K5 violations are 0/38 in mass-only worlds, and G5 is 0/8. The residual is G2 at 5/8, where a validation-quality gate is structurally unable to detect a regime switch.

---

## 9. Reproducibility

```
scripts/accopt_build_cache.py   # 165 s, 323 worlds, 26,600 band members scored against truth
scripts/accopt_selectors.py     # all architectures, gate and CV design, frozen before comparison
scripts/accopt_run.py           # baseline, nested CV, gate calibration, failure taxonomy
scripts/accopt_diagnose.py      # targeted re-derivation of adjudication reasons
scripts/accopt_report.py        # architecture comparison, R^2 distributions
scripts/accopt_write.py         # MURU_ACCURACY_OPTIMIZATION.json
```

Artifacts: `artifacts/accopt/{candidate_cache,run_result,architecture_comparison,failure_diagnosis,held_out_selections,variant_summary}.json`.

Source checkpoint data read read-only from `artifacts/ov_ckpt` (9,690 PySR seed-runs). No checkpoint was written to and no new search was run.
