# Amendment A3.2: Null Calibration Base Target and Scaffold Split

## Status

PROSPECTIVE CORRECTION. PRE-CALIBRATION, PRE-HELD-OUT.

A3.2 is narrow. It changes exactly two things in the structural-null
calibration design and nothing else.

## Lineage

| Artifact | Commit |
|---|---|
| Amendment A2.1 (generator version) | `80a7803` |
| **Amendment A3.1 (content freeze)** | `c8938e8` (tag `benchmark-content-freeze-a3-1`) |
| Engineering RC3 | `adfdec0` (tag `engineering-rc3-a3-1`) |
| **This amendment (A3.2)** | *this commit* |

## Temporal position, and why this correction is legitimate

- The 100 calibration worlds have **NOT** been executed.
- No threshold table exists.
- Development G2/G3 have **NOT** been scored.
- Held-out is **SEALED** and was not opened.
- Confirmation is **SEALED** and was not opened.

The defect corrected here was found by read-only review of the Engineering
RC3 implementation, from the construction of the null itself. It was **not**
found by looking at a result, because there is no result to look at. No
threshold, no Development outcome, no Held-out outcome and no Confirmation
outcome informed this correction, and none could have: none of them exists
in a readable form at this point in the sequence.

This is therefore a prospective correction to a design defect, made before
the design produced any number. It is the permitted kind of amendment.

## Decision 1: null calibration base target

### The defect

A3.1 fixes the world geometry, the covariates and the three null-family
constructions, but does not pin the pre-permutation target. Engineering RC3
provisionally used the frozen synthetic law's target vector directly.

That vector is **scaffold-structured**: the frozen law
`scale * sqrt(mass/250) * (1 + c * descriptor)` depends on `mass` and
`descriptor`, both of which are driven by the per-scaffold latent
`group_latent[scaffold]`.

Under `target_permuted_across_compounds` and
`gaussian_targets_with_observed_variance` that structure is destroyed. Under
`descriptors_permuted_across_compounds` only the covariates are permuted, so
the target keeps its scaffold structure, and against a scaffold-disjoint
split that produces a systematic train/validation mean shift.

Measured constant-model validation R2, 20 worlds per construction:

| Construction | Mean validation R2 of the train-mean constant model |
|---|---|
| `target_permuted_across_compounds` | -0.055 |
| `gaussian_targets_with_observed_variance` | -0.077 |
| `descriptors_permuted_across_compounds` | **-0.246** (min -1.28) |

So one of the three nominal null families was systematically non-null. The
33 depressed worlds drag the pooled Q95 over 100 worlds **below** what a
homogeneous null would give, making the resulting acceptance threshold more
permissive than intended. A more permissive null threshold admits structural
claims that should have been rejected, which is the one direction of error
this benchmark may not take.

### The corrected construction

The provisional direct use of the frozen-law target is **REJECTED**.

The A3.2 base target is:

1. Generate the frozen-law target vector exactly as the existing frozen
   synthetic law defines it. The law is unchanged.
2. Preserve that vector's values, and therefore its exact marginal
   distribution.
3. **Before** applying any of the three A3.1 null-family transformations,
   randomly reassign the target values across the complete set of compound
   identities, using one dedicated deterministic world-specific seed.
4. The reassignment is a **true permutation**: no value added, none removed,
   no numerical alteration, no re-estimation, and no conditioning on
   descriptors, scaffold, mass, split, or symbolic-search results.
5. The permutation seed is derived through the repository's canonical
   deterministic seed derivation (`generator.derive_seed`) from the namespace

   ```
   PB|NCAL|<world_id>|BASE_TARGET
   ```

6. Reassignment is global across all 180 compounds, and happens **before**
   any train/validation/test partition use.
7. The base-target seed is independent of the null-family transformation
   seed, the split seed, the PySR search seeds, the bootstrap seed, and the
   engineering-smoke seeds.
8. The frozen A3.1 34/33/33 null-family allocation then applies **exactly**
   as already specified, unchanged.
9. Within-compound energy permutation remains **forbidden** and is not
   restored.

### What this is and is not

This amendment does **not** invent a new target distribution. The marginal
distribution of the target is exactly the frozen law's, value for value.
What is destroyed is the *assignment* of those values to compound, scaffold,
mass and descriptor. That is precisely the association a structural null must
not contain.

Residual finite-sample correlation arising by chance after a valid random
permutation is **permitted and expected**. It must not be tuned away. One
deterministic permutation per world means one permutation per world: no
reshuffling until a correlation looks small, no rejection sampling, no
selection among candidate permutations.

No calibration result may be used to select or revise this design. At the
time of writing, none exists.

## Decision 2: scaffold split

### The defect

A3.1 specifies a scaffold-disjoint **60/20/20** split. The inherited
protected generator produces a 20/5/5 scaffold-group split, i.e. 120/30/30
compounds, i.e. 66.7/16.7/16.7 percent.

### The decision

The A3.1 written specification of **60/20/20 remains authoritative**. The
scientific contract is **not** amended to 66.7/16.7/16.7 merely because the
inherited generator currently produces that.

For the 30-scaffold, 180-compound calibration worlds, A3.2 requires:

| Partition | Scaffolds | Compounds |
|---|---|---|
| train | 18 | 108 |
| validation | 6 | 36 |
| test | 6 | 36 |

The compound counts follow because the frozen generator constructs exactly
30 equal scaffolds of 6 compounds each; this was verified against the frozen
code rather than assumed.

Requirements:

1. Scaffold identity is **atomic**: a scaffold appears in exactly one
   partition.
2. Split assignment is deterministic from a dedicated derived seed, namespace

   ```
   PB|NCAL|<world_id>|SPLIT
   ```

3. Split assignment does not depend on target values, descriptor values,
   mass, symbolic-search output, or null-family outcome.
4. The A3.1 protected generator remains **byte-identical**. It is not edited.
5. The corrected split is implemented through a new calibration-specific
   partition helper, additive to the RC3 lineage.
6. Development, Held-out, Confirmation and historical benchmark partition
   logic are untouched.

This split applies to **calibration worlds only**. It does not change the
partitioning of any benchmark case.

## What A3.2 does not change

Everything else in A3.1 stands unchanged:

- G2 denominator 144, Wilson lower gate 0.70
- G3 denominator 36, Wilson upper gate 0.15
- the structural acceptance predicate, its gate order and its typed states
- stability 20/30, max complexity 20, invalid fraction 0.005
- ceiling gate 0.80, ceiling waiver 0.05
- the 34/33/33 null-family allocation
- the exclusion of within-compound energy permutation
- 100 worlds, 30 seeds per world, seed derivation, `PB_SEED_BASE`,
  `PB_SEED_SPREAD`
- per-seed failure semantics and world aggregation
- quantile level 0.95, `method="linear"`, cumulative max
- bootstrap 2000 resamples at seed 20260812, reporting only
- the 95/100 calibration validity floor
- the search settings, PySR 1.5.10, the operator grammar
- the ceiling estimator and its dependency pin
- the truth family taxonomy

All A3.1 protected content remains historically preserved and
byte-identical. A3.2 is additive and prospective.

## Status of sealed material at the time of this amendment

| Partition | Status |
|---|---|
| Calibration | `NOT_EXECUTED` |
| Development | `NOT_OPENED` |
| Held-out | `SEALED_NOT_OPENED` |
| Confirmation | `SEALED_NOT_OPENED` |
