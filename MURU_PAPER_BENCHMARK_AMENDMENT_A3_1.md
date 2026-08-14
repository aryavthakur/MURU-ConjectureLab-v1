# Amendment A3.1: G2/G3 Structural Endpoints and Calibration Contract

## Status

POST-DEVELOPMENT, PRE-HELD-OUT SCIENTIFIC CONTRACT FREEZE.

## Lineage

| Artifact | Commit |
|---|---|
| Benchmark V1 | `d94d2c9` |
| Amendment A1 (adequacy) | `2ac86c5` |
| Amendment A2 governance | `4dae072` |
| Amendment A2 (F16 repair) | `03cc4d3` |
| Amendment A2.1 (generator version) | `80a7803` |
| G2/G3 contract audit | `34dee8e` |
| Engineering RC2 | `c7c2332` |
| Development record | `d9e2795` |
| Adequacy diagnostic | `bc741e3` |
| **This amendment (A3.1)** | *this commit* |

## Temporal position

- The 80 Development cases had already been executed before A3.1.
- G2 and G3 were not producible during that execution.
- No candidate G2/G3 rule was scored against Development before A3.1.
- No Development outcome was used to choose A3.1 rules.
- Fresh structural-null calibration is required before structural acceptance
  becomes operational.
- Held-out remained sealed throughout.

## Scope

A3.1 adds the scientific contracts for:

1. **G2** - structural-family endpoint (support and family match)
2. **Structural acceptance** - truth-blind acceptance predicate with typed states
3. **Structural-null calibration** - protocol, seeds, failure semantics, thresholds
4. **G3** - structural-safety endpoint (unsafe-event detection)

A3.1 does NOT modify any content from V1, A1, A2, or A2.1.

## G2 contract

### Primary event

G2 success requires BOTH:

- `support_status == MATCH`
- `family_status == MATCH`

### Effective support

Deterministic extraction from symbolic expressions:

- Parse under protected grammar
- Deterministic algebraic normalization via SymPy simplify
- Cancelled variables do not count
- Exact-zero terms do not count
- Constants contribute no support
- Duplicated primitive variables count once
- Nested transforms preserve primitive dependence
- Interactions contribute every primitive input
- Correlated proxy variables remain distinct
- F12 proxy (correlated_distractor) is NOT interchangeable with descriptor
- No new magnitude threshold invented

Unresolvable expressions produce `SUPPORT_UNRESOLVED`.

### Truth family taxonomy

Preserved exactly:

- `mass_affine_descriptor`
- `mass_power`
- `mass_saturating_descriptor`
- `mass_interaction`
- `mass_exponential_descriptor`

Discovered-side classification is structural and coefficient-agnostic.
Algebraic reorderings classify identically.
Degenerate exact family intersection: `FAMILY_AMBIGUOUS`.

### G2 criterion

Held-out denominator: 144.
Gate: lower 95% Wilson >= 0.70.

## Structural acceptance

Truth-blind. Family correctness is NOT part of acceptance.

Ordered predicate:

1. A1 adequacy: only `M0_NOT_REJECTED` proceeds.
   Rejection states produce `REJECTED_A1_INADEQUATE`.
   Failure/timeout/contract states produce `UNEVALUABLE`.
2. `valid_r2 > null_threshold[min(complexity, 20)]`
3. `selection_fraction >= 20/30`
4. `complexity <= 20`
5. `invalid_fraction <= 0.005`
6. Effective support non-empty
7. `ceiling_fraction >= 0.80` OR `ceiling_r2 < 0.05` (waiver)
8. Reduced falsification harness passes

### Ceiling estimator

Bound to `scikit-learn==1.9.0` (from `requirements.lock.txt` at RC2 `c7c2332`,
predates Development).

```
HistGradientBoostingRegressor(
    max_iter=150,
    max_depth=3,
    min_samples_leaf=20,
    random_state=0,
)
```

Train on train partition. Score on test partition. Frozen covariate order.

### Reduced falsification harness

Required rungs:

- F1 reproducibility
- F4 compound holdout
- F5 scaffold holdout
- F7 influence-drop component only
- F9 energy-subset stability
- F10 negative control

F8 is structural labelling, not an acceptance gate.
`NOT_APPLICABLE` is never counted as `PASS`.

## Structural-null calibration

### Contract only - NOT EXECUTED in A3.1

100 calibration worlds:

| Construction | Count |
|---|---|
| target_permuted_across_compounds | 34 |
| descriptors_permuted_across_compounds | 33 |
| gaussian_targets_with_observed_variance | 33 |

Within-compound energy permutation is EXCLUDED (preserves compound mean level).

Each world: 180 compounds, 30 scaffold groups, same five synthetic covariates,
same frozen correlation structure, scaffold-disjoint 60/20/20 split.

### Search settings (frozen)

- PySR 1.5.10
- binary: +, -, *, /
- unary: sqrt, log, square, cube, inv
- exp excluded, trig excluded
- max complexity 20
- niterations 40, populations 15, population_size 33
- parsimony 0.0032, adaptive_parsimony_scaling 20.0
- deterministic, serial
- 30 seeds/world

### Seed derivation

```
PB_SEED_BASE = 2_110_000_000
PB_SEED_SPREAD = 370_000

h = int.from_bytes(
    hashlib.sha256(world_id.encode("utf-8")).digest()[:4],
    byteorder="big", signed=False)
base = PB_SEED_BASE + (h % PB_SEED_SPREAD) * 100
seeds = [base + k for k in range(30)]
```

World ID: `PB|NCAL|{construction_name}|r{index:03d}`, index 0..99.

Verified invariants: 100 unique world IDs, 100 unique base buckets,
3000 unique seeds, signed 32-bit safe.

### Per-seed failure semantics

Three explicit statuses:

- `COMPLETED_WITH_CANDIDATES` - search returned candidates
- `COMPLETED_NO_CANDIDATE` - search completed, no candidates (contributes -inf)
- `EXECUTION_FAILURE` - crash/timeout/OOM/malformed

`np.isfinite` alone does NOT determine status.

If ANY seed has `EXECUTION_FAILURE`, the world's entire S(w,1..20) becomes +1.0.
Conservative: cannot lower threshold, may lose power.

### Calibration validity

At least 95/100 worlds must have zero execution-failure seeds.
More than 5 failed worlds: `CALIBRATION_INVALID`, no threshold table activated.
No selective retries or replacement worlds.

### Null statistic

S(w,c) = max over 30 seeds of best validation R2 at complexity <= c.
Per-seed curves are prefix-monotone (cumulative max).
Contract canary: once finite at c, cannot become non-finite at larger c.

### Threshold table

`numpy.quantile(..., 0.95, method="linear")`.
For N=100: Q95 = x[94] + 0.05 * (x[95] - x[94]).
Then `np.maximum.accumulate` to enforce non-decreasing.

Bootstrap: 2000 world-level resamples, seed 20260812, uncertainty reporting only.

## G3 contract

36 Held-out G3 opportunities (F19 + F20, 3 variants each, 12 held-out per family).

### Event rules

- Unsafe structural acceptance: 1
- Safe evaluable non-acceptance: 0
- UNEVALUABLE: G3 VIOLATION (remains in denominator)

### F19 variant semantics

- **F19A**: mass-only acceptance permitted; unsupported non-mass structure unsafe
- **F19B**: mass-only permitted; accepted non-mass structure unsafe
- **F19C**: accepted structural claim unsafe; legitimate non-acceptance safe;
  unevaluable is violation

### F20 variant semantics

- **F20A**: accepted structural claim unsafe (latent driver)
- **F20B**: accepted structural claim unsafe (measurement coupling)
- **F20C**: accepted structural claim unsafe (out-of-grammar trap)

### G3 criterion

Upper 95% Wilson <= 0.15.

## Immutability

A3.1 does not modify:

- Benchmark case rows, generator payload, truth payload, seeds, partitions
- G1, A1 adequacy, M0/M1/M2/M3, F16
- G2 denominator (144), G2 threshold (0.70)
- G3 denominator (36), G3 threshold (0.15)

## Implementation

Reference-contract Python modules in `src/muru/paper_benchmark/`:

- `g2_contract.py` - G2 support/family classification
- `structural_acceptance.py` - acceptance predicate with typed states
- `calibration_contract.py` - calibration protocol and failure semantics
- `g3_contract.py` - G3 unsafe-event classification

Constructed tests in `tests/`:

- `test_a3_1_g2_contract.py`
- `test_a3_1_structural_acceptance.py`
- `test_a3_1_calibration_contract.py`
- `test_a3_1_g3_contract.py`

Machine-readable artifact: `artifacts/paper_benchmark_amendment_a3_1.json`.
Integrity script: `scripts/pb_33_amendment_a3_1_integrity.py`.
