# MURU paper-grade prospective synthetic benchmark: design

## Status and scope

This specification defines a new prospective synthetic benchmark for the MURU
paper. It is a computational validation study under controlled synthetic
conditions. It makes no biological, instrumental, or real-world validation
claim.

The benchmark is separate from all historical studies. In particular:

- Phase 3 remains `STOP BEFORE PHASE 4`.
- Type 2 remains `DO NOT AUTHORIZE PHASE 4`; it is not rescored or amended.
- The confirmation set remains sealed and is never read by this benchmark.
- No unresolved real-data symbolic discovery is allowed.
- `science/synthetic-benchmark-suite` is historical development evidence only.
  It is neither merged nor used as this benchmark's primary denominator.

The work starts from `adf7b3b` on an isolated branch named
`science/muru-paper-benchmark`. It must not merge engineering, evaluator-audit,
public-data, acquisition-design, or prior synthetic-consolidation branches.

## Claim

The sole primary paper claim is:

> Under controlled, prospectively frozen synthetic conditions, MURU can recover
> meaningful family-level mathematical structure while rejecting specified null
> and adversarial worlds.

This claim is conditional on the case-generating distributions frozen below.
It is not a claim of exact equation discovery, biological truth, or real-world
performance. Exact algebra recovery is a separately reported secondary metric.

## Design population and partitions

There are 380 independent synthetic cases, all generated from a single frozen
case registry.

| Partition | Cases | Construction | Use |
|---|---:|---|---|
| Development | 80 | 4 cases in each of 20 families | Code, serialization, evaluator-contract, and runtime checks only |
| Held-out | 240 | 12 cases in each of 20 families | One primary evaluation only |
| Challenge | 60 | 3 cases in each of 20 families | Descriptive robustness only; never in a primary denominator |

Every case contains 180 fully synthetic compounds assigned before response
generation to 30 scaffold groups of six compounds. Case-local scaffold groups
are partitioned into 20 training groups (120 compounds), five validation groups
(30 compounds), and five test groups (30 compounds). Each compound is observed
on the frozen six-energy grid `{15, 30, 45, 60, 75, 90}` unless its family
defines missingness.

The 240 held-out cases are the overall benchmark population. Every endpoint has
its own applicable subset declared below; no endpoint silently treats an
inapplicable world as a failure or a success.

## Common synthetic data model

The generator creates synthetic covariates, synthetic scaffold correlation, and
synthetic response trajectories. It does not read any real compound, descriptor,
response, confirmation identifier, or historical generated case.

For M0 cases, the response is generated as

`mu_i(E) = Phi(E / g_i) + epsilon_i(E)`,

where `Phi(u) = mu_inf + (1 - mu_inf) * exp(-(u ** p))`, with `0 < mu_inf < 1`
and `p > 0`. Per-case `mu_inf`, `p`, scale and law coefficients are drawn from
declared bounded ranges. The response is clipped only to the physical interval
`[1e-4, 1 - 1e-4]`, with the number of clips recorded.

Each case has a machine-readable truth record including:

- case and partition identifiers, family, variant, and all derived seeds;
- `Phi`, its parameters, `g` definition and per-compound true `g` where one
  exists;
- descriptor relationship, active support, mathematical family, coefficients
  and exponents, and whether symbolic/exact recovery is defined;
- response-noise and missingness mechanisms;
- true adequacy class (`M0`, `M1`, `M2`, or `M3`), expected qualitative result,
  and target-specific endpoint applicability.

The generator uses a root seed of `20260813`. Every pseudo-random stream is
derived with SHA-256 from `paper-benchmark-v1|partition|family|replicate|stage`;
therefore changing execution order cannot change a case. Generator, truth,
manifest, metric, and evaluator-contract versions are each explicit constants.

## Case families

| Code | Family | Scientific question | Adequacy truth | Scalar truth | Symbolic truth |
|---|---|---|---|---|---|
| F01 | Noiseless scalar collapse | Can the pipeline recover an unambiguous collapse? | M0 | yes | yes |
| F02 | Moderate-noise scalar collapse | Does recovery survive a realistic noise level? | M0 | yes | yes |
| F03 | Stronger realistic noise | How does degradation appear before a catastrophic regime? | M0 | yes | yes |
| F04 | Missing-one-energy | Is recovery robust when each affected compound lacks one declared energy? | M0 | yes | yes |
| F05 | Boundary-scale | Are clipped/profile-boundary cases identified and reported? | M0 | yes | yes |
| F06 | No molecule-specific scalar truth | Does the pipeline reject a shared-scalar interpretation when none exists? | M1 | no | no |
| F07 | Mass-only `g` truth | Is non-mass structure avoided when mass alone explains `g`? | M0 | yes | yes |
| F08 | Simple descriptor law | Can a monotone mass-plus-descriptor law be recovered? | M0 | yes | yes |
| F09 | Nonlinear descriptor law | Can a saturating descriptor effect be recognized? | M0 | yes | yes |
| F10 | Interaction law | Can an interpretable two-variable interaction be recognized? | M0 | yes | yes |
| F11 | Irrelevant distractors | Are independent inactive variables excluded from support? | M0 | yes | yes |
| F12 | Correlated distractors | Is structural support distinguished from correlated nuisance variables? | M0 | yes | yes |
| F13 | Horizontal-shape violation | Does M1 detect compound-specific horizontal shape changes? | M1 | diagnostic only | no |
| F14 | High-energy vertical violation | Does M2 detect an asymptotic/floor deviation? | M2 | diagnostic only | no |
| F15 | Low-energy vertical violation | Does M3 detect a ceiling/low-energy deviation? | M3 | diagnostic only | no |
| F16 | Combined mild non-scalar violation | Are jointly mild violations flagged rather than accepted as M0? | M1+M2+M3 | diagnostic only | no |
| F17 | Equivalent symbolic forms | Do algebraically equivalent representations receive one family-level score? | M0 | yes | yes |
| F18 | Algebraically difficult, predictively simple | Is predictive equivalence kept distinct from exact recovery? | M0 | yes | yes, exact secondary |
| F19 | Null worlds | Does a target-specific null produce no structural acceptance? | M0 | yes | no |
| F20 | Adversarial worlds | Are latent-driver, artefact, and out-of-grammar traps rejected or labelled? | mixed | no | no |

F19 is balanced across three predeclared null mechanisms: independent scalar
targets, mass-preserving/non-mass-destroying targets, and response-cell
resampling that explicitly reports its trajectory degeneration. The historical
within-compound energy permutation is never an F19 scalar-target null; a test
must demonstrate the information destroyed by every selected null. F20 is
balanced across unobserved-driver, measurement-coupling, and out-of-grammar
adversaries.

## Evaluation chronology and isolation

The scalar estimator is evaluated before symbolic discovery and follows this
fixed order for every case:

1. Assign all compound/scaffold splits before fitting any response object.
2. Fit `Phi`, support, normalization, residual weighting, constants, and profile
   bounds using training trajectories only.
3. Estimate training `g` values against those training-side objects.
4. Freeze those fitted objects.
5. Estimate each validation or test compound's `g` independently against the
   frozen objects.
6. Send only permitted training-side scalar targets and covariates to symbolic
   discovery; use validation for predeclared candidate selection and the test
   fold only for final scoring.

Mutating test compound B must not alter the fitted `g`, trajectory prediction,
weight, or profile diagnostic for test compound A. Tests enforce this canary.

The model-adequacy ladder compares M0 with M1 (horizontal shape), M2
(high-energy vertical/asymptotic), and M3 (low-energy vertical) using the same
held-out compound split. A non-firing alternative detector cannot by itself
make M0 pass: the analysis must report detector power/identifiability from
obvious simulated truths, and label a six-energy limitation if a class cannot
be distinguished.

## Evaluator and engine contract

The new analysis uses the modern strict evaluator contract. It cannot use the
historical complex-cast semantics. The contract requires finite real-valued
evaluation, protected operations, a frozen grammar and complexity scale,
canonical treatment of defensible algebraic equivalents, and identical
candidate validity and prediction checks for every search output.

The exact evaluated MURU implementation commit, engine versions, grammar,
selection rule, runtime limit, and strict-evaluator version are intentionally
recorded as `PENDING_LOCK` until the parallel engineering track supplies its
locked commit. A held-out runner must refuse to execute while any of those
fields remain pending. The benchmark generator, inputs, truths, denominators,
metrics, and refusal guard can nonetheless be content-frozen first.

## Endpoints and frozen denominators

All rates carry the exact numerator, denominator, and a Wilson 95% interval.
Medians carry a stratified bootstrap interval at the case level. Challenge cases
are excluded from every endpoint below.

| Endpoint | Role | Held-out applicable families | Denominator |
|---|---|---|---:|
| Valid scalar-target yield | Primary scalar | F01–F05, F07–F12, F17–F19 | 168 cases; compound-level count also reported |
| Held-out `g` rank recovery and log-scale error | Primary scalar | F01–F05, F07–F12, F17–F19 | 168 cases |
| Held-out energy prediction and profile stability | Primary scalar | F01–F05, F07–F12, F17–F19 | 168 cases |
| Boundary-hit rate | Primary scalar safety | F05 | 12 cases; applicable-compound count reported |
| Family-level recovery | Primary symbolic | F01–F05, F08–F12, F17–F18 | 144 cases |
| Variable support recovery | Secondary symbolic | F01–F05, F08–F12, F17–F18 | 144 cases |
| Parameter/exponent recovery | Secondary symbolic | F01–F05, F07–F12, F17 | 144 cases |
| Predictive equivalence | Secondary symbolic | F01–F05, F08–F12, F17–F18 | 144 cases |
| Exact algebra recovery | Secondary only | F01, F08–F10, F17 | 60 cases |
| M0 specificity | Primary adequacy | F01–F05, F07–F12, F17–F19 | 168 cases |
| M1 sensitivity | Primary adequacy | F06, F13, F16 | 36 cases |
| M2 sensitivity | Primary adequacy | F14, F16 | 24 cases |
| M3 sensitivity | Primary adequacy | F15, F16 | 24 cases |
| Null rejection | Primary safety | F19 | 12 cases, balanced by null mechanism |
| Adversarial rejection/flagging | Primary safety | F20 | 12 cases, balanced by adversary mechanism |

Family-level recovery requires correct active block support and mathematical
family, with directionality and exponents/parameters assessed separately. A
function can be predictively equivalent without being family-equivalent; a
family can be correct without exact algebra. Exact algebra is never substituted
for the primary claim.

The primary paper claim is supported only if the locked evaluation completes
without governance failure, reports all primary denominators, has a lower 95%
Wilson bound of at least 0.50 for family-level recovery, and an upper 95%
Wilson bound no greater than 0.25 for false structural acceptance across the
predeclared mass-only, null, and adversarial negative controls. Otherwise the
paper reports conditional endpoint estimates without the positive umbrella
claim. This rule is not an authorization for Phase 4.

## Development-only preflight and freeze gate

Before the final content freeze, a development-only preflight runs all 80
development cases through the available strict evaluator path. It may collect
wall and CPU time, peak memory, engine failures, candidate counts, output sizes,
and stage-specific timing. It records case identities only from Development and
must reject every path that enumerates, reads, scores, or summarizes held-out
responses, truths, outcomes, or case-level identities.

The preflight projects a held-out burden from observed development medians and
upper quantiles, separately for scalar fitting, adequacy, search, selection, and
scoring. It is operationally feasible only if the projected 240-case serial
runtime fits within the frozen runtime budget, projected peak memory fits the
available memory, and failures are below the frozen tolerance. If infeasible,
the process stops before final benchmark freeze and proposes the smallest
scientifically neutral reduction: reduce replicated seeds or runtime per engine
uniformly across all three partitions before reducing the 20-family or
held-out-case design. Development scientific performance may never change case
counts, coefficients, grammar, metrics, or thresholds.

Because the evaluated implementation commit is currently pending, the first
preflight may validate only generator, estimator-contract, serialization, and
refusal-path costs. The complete engine runtime preflight and final executable
freeze are blocked until that commit is supplied; this must be reported rather
than estimated from historical or parallel-branch results.

## Artifacts, integrity, and tests

The implementation will create the required protocol, family, metric, and
freeze documents plus these tracked artifacts:

- `artifacts/paper_benchmark_partition_manifest.json`
- `artifacts/paper_benchmark_case_manifest.json`
- `artifacts/paper_benchmark_truth_manifest.json`
- `artifacts/paper_benchmark_hash_inventory.json`

It will also record generated inputs by partition, a content-only freeze
manifest, development preflight records, evaluator-lock status, and SHA-256
hashes for every frozen artifact. Held-out truth and input artifacts are written
at generation time but are not opened by development code. Source-level import
tests enforce this separation.

Required tests cover deterministic re-generation; seed separation; partition
sizes; family coverage; scaffold and fold disjointness; held-out leakage
canaries; truth schema/serialization; hash reconstruction; strict evaluator
semantics; equivalent-expression canonicalization; target-specific null
information destruction; M0/M1/M2/M3 obvious-truth behavior; endpoint
denominator reconstruction; held-out access refusal; and development-only
preflight quarantine.

## Non-goals

This benchmark neither opens the confirmation set nor acquires mass-spectrometer
data. It does not run a primary held-out evaluation, publish a primary result,
authorize Phase 4, merge a parallel branch, or claim exact symbolic truth.
