# MURU v2 Master Causal Architecture

**Status:** SEALED synthesis, results-blind to E2. Cites `MURU_V2_MASTER_EVIDENCE_LEDGER.md` (`L-<ID>`) and `MURU_V2_MASTER_MATHEMATICAL_RECONCILIATION.md`.

## Classification legend

`BENCHMARK_IDENTIFIABILITY_LIMIT` · `OBSERVATION_INFORMATION_LIMIT` · `ESTIMATOR_LIMIT` · `DECISION_RULE_INFORMATION_LOSS` · `SEARCH_GENERATION_LIMIT` · `RETENTION_LIMIT` · `CLASSIFICATION_LIMIT` · `FUNCTIONAL_EQUIVALENCE_LIMIT` · `GRAMMAR_LIMIT` · `CALIBRATION_LIMIT` · `IMPLEMENTATION_DEFECT` · `GOVERNANCE_DEFINITION_DEFECT` · `ADVERSARIAL_ONLY_LIMIT`

Every limitation gets exactly one PRIMARY classification and, where applicable, secondary contributors. "Primary" means: if only one cause could be fixed, this is the one whose removal would change the outcome most.

---

## M1

**PRIMARY: `BENCHMARK_IDENTIFIABILITY_LIMIT`.**
Theorem 1 (`L-M1-02`, exact) proves ~92.6% of the planted common amplitude is unidentifiable against the shared M0 profile — a property of the benchmark's own generative law, true for *any* statistic or parameterization. This is upstream of and dominates every other contributor.

**Secondary contributors:**
- `OBSERVATION_INFORMATION_LIMIT` — even the identifiable ~7–19% residual caps a correctly-specified statistic at 0.188–0.218 power, driven by the small N=30/n_e=6 design and the isotonic profile's slope-fidelity loss (`L-M1-02` §19.4).
- `ESTIMATOR_LIMIT` — the *currently deployed* LOEO statistic measures 0.0% even against oracle parameters (`L-M1-01`), performing *worse* than the honest identifiability ceiling would allow — a genuine defect layered on top of, not merely downstream of, the identifiability limit.

**Explicitly NOT the cause**: coordinate/parameterization choice (`L-M1-04`, RC1 `NO_ARM_ADMISSIBLE`), profile-estimator architecture or localized contamination (`L-M1-06`, A1PR/PCL both closed).

---

## M2

**PRIMARY: `DECISION_RULE_INFORMATION_LOSS`.**
`L-M2-06` (exact reconciliation): the LOEO-holdout construction alone reduces even a *perfect*-variance estimator's efficacy to ~0 (P6, exact — both arms of the practical-win margin share the same irreducible held-out noise floor); the 20-of-30 independent-vote aggregation additionally discards continuous margin information (near-null-compound drag, P7 exact). Retention factor r²=0.346: the frozen architecture keeps ~35% of the information a pooled statistic would use. A pooled statistic at the *identical* 6-energy budget reaches 0.734–0.824 power — direct proof the dominant loss is architectural.

**Secondary contributor:**
- `OBSERVATION_INFORMATION_LIMIT` — a genuine, smaller, already-~98%-realized Fisher-geometry ceiling remains even for a pooled/full-information test (0.416 case power at 6 energies via aliasing rho~0.97–0.99, `L-M2-01/03`); would need 8.7–165× more energies to close on its own.

**Explicitly NOT the cause**: estimator inefficiency (near-CRLB-efficient after correction, `L-M2-09`), grid geometry (`L-M2-04`, M2GV1 `NO_M2_GEOMETRY_REPAIR_LICENSED`, 0.0000 vs 0.0000 despite real variance reduction), coordinate reparameterization (`L-M2-08`, RC1).

---

## M3

**PRIMARY: `ESTIMATOR_LIMIT`.**
`L-M3-02` (exact under idealization): the finite-support endpoint-normalization floor is a definitional consequence of *how the target estimator is constructed* — `ProfileShape` reads knot-grid endpoint *evaluations* as stand-ins for the profile's *asymptotes* — present even at a perfectly-estimated Phi and true g, matching 87–113% of the empirical residual. The §7.2 impossibility theorem (exact) proves identification of the plateau and orthogonality to `a_lo` are the same inner product under the *current* estimand definition, foreclosing any profile-estimation-*quality* fix while leaving an estimator-*redesign* fix (the relative-plateau construction, Part VI item 5) open — this asymmetry (escapable by redesigning the estimator, unlike M1's Theorem-1 unidentifiability which is not fixable by any statistic or estimator whatsoever) is exactly why this is classified as an estimator limit rather than a benchmark-identifiability limit. (An earlier draft of this document classified M3 as `FUNCTIONAL_EQUIVALENCE_LIMIT`, a category that does not actually match this mechanism — that category properly describes a *different* hazard, e.g. F18's "safety trap" where a structurally wrong family scores well on a predictive metric; M3's floor is a bias in the *target parameter estimator itself*, not a family-confusion/functional-equivalence issue. Corrected here after hostile review.)

**Secondary contributors:**
- The target-estimator's Fisher condition-ratio penalty (`1/(1-c²)`) is a second, related `ESTIMATOR_LIMIT` mechanism, cross-validated to FI1's own numbers (`L-M3-02` §3.2) — a consequence of the aliasing geometry, distinct from the endpoint-normalization floor above.
- `CLASSIFICATION_LIMIT` (decision-statistic behavior) — the frozen M3 *decision* reads a predictive MAE ratio, not the biased parameter itself, so fixing the estimator's bias does not automatically fix detector power; this is why the fix requires a separate decision-architecture question (route A vs. B in Part VI).

**Explicitly NOT the cause of the parameter-bias floor specifically**: log_g search mechanics (`L-M3-01`, GM1/GM2/GM6 refuted), generic Phi-estimation *quality* (`L-M3-04`, provably foreclosed for the floor — the impossibility theorem holds even at a perfectly-estimated Phi), coordinate reparameterization (`L-M3-05`, RC1). **This scoping matters and must not be over-read**: Phi quality remains the single largest lever found anywhere in the M3 investigation for the *detector's* (LOEO/predictive) power specifically — `L-M3-06` (SA1): oracle-clean-training Phi recovers M3's LOEO power from 1.3% to 90.7%. "Generic Phi decontamination cannot fix the parameter-bias floor" and "Phi quality is irrelevant to M3" are different claims; only the first is established. A 4th *profile-estimator-architecture* study remains `CONTRA_INDICATED` regardless (it targets the foreclosed floor, not the still-live detector-power lever), but this does not mean Phi quality is causally inert for M3 overall.

---

## F05

**PRIMARY: `ADVERSARIAL_ONLY_LIMIT`.**
`L-F05-01..04`: the finite-information-collapse boundary regime is mathematically real (proven, Theorems 1–3) but reachable *only* at constructed out-of-box stress values (1.9–22× outside the authorized `U(1.1,1.8)`); 0/20,000 authorized-box Monte Carlo worlds ever approach it. Not a nominal-benchmark limitation at all.

**Secondary contributor:**
- `ESTIMATOR_LIMIT` — any real `boundary_hit` observed in production is attributable to the fitter's own `MU_CEIL` (E0, `L-GOV-04`/`L-F05-05`), an estimator-side boundary-contact issue unrelated to F05's own generative construction.

---

## F09

**PRIMARY: `RETENTION_LIMIT`.**
`L-RET-06` (executed, decisive): case-level front-reach is 12/12 (100%) at every tested arm; `P_retain_given_front=0.0` exactly, zero exceptions, across 306–330 correct-containing seeds. Reverses v1's own `SEARCH_GENERATION_LIMIT` classification directly.

**Explicitly NOT the cause**: search/generation mechanics — truth-equivalent structure reaches the front reliably regardless of the 8 tested arms (budget, parsimony, adaptive-parsimony-scaling, unguarded-`exp` grammar).

---

## Retention (general, E4a scope)

**PRIMARY: `DECISION_RULE_INFORMATION_LOSS`.**
`L-RET-01/02` (exact): PySR's `score` is an adjacent-front chord slope; `argmax(score)` is the MAP rule at an implicit price `beta_eff`, discarding every candidate below that price regardless of whether a correct structure sits among them. This is a property of the *scalar resolution rule*, not of search coverage.

**Secondary contributor:**
- `GOVERNANCE_DEFINITION_DEFECT` — `L-RET-03/04`: under the current resolver, three of seven registered retention policies (R1/R3/R5) are downstream-identical by construction, meaning the frozen vote-reduction rule limits how much a set-valued retention policy alone can help without also changing the resolver; and `L-RET-05` (36-vs-90 EVAL denominator) is a live, uncorrected documentation defect in the frozen artifacts.

---

## Symbolic equivalence

**PRIMARY: `IMPLEMENTATION_DEFECT`.**
`L-COR-03`/`L-RET-08`: two independently-discovered, mechanistically different, both-unpatched defects in `discovery/equivalence.py`'s `algebraically_equivalent`/`numeric_relation` (a sign-unconstrained-scale false positive, 9.09% measured on an 11-case corpus, and a separate nan-ratio false positive), both real, low-reachability-on-their-own-corpora, and relevant to E4a's future stage C/D split.

**Secondary contributor:**
- `GOVERNANCE_DEFINITION_DEFECT` — the newer, frozen correctness/confidence SPEC's own §4 oracle already specifies the fix (explicit `k>0` checks) and does **not** inherit the sign bug — the defect is confined to the older, still-unpatched `equivalence.py`, not to the framework's current definition.

---

## Confidence / calibration

**PRIMARY: `CALIBRATION_LIMIT`** *(bands themselves are sound; the risk is in what they're applied to)*.
`L-COR-09`: E-STAB's calibration bands (0.210/0.500/0.742/0.860/1.000) are real, hostile-audited, and correctly distinguish structural from exact-coefficient recoverability — but 0/1,560 replicates ever achieve exact algebraic equivalence even at zero noise, meaning any confidence claim that implicitly promises exact-coefficient certainty is definitionally uncalibratable.

**Secondary contributor:**
- `GRAMMAR_LIMIT` — F07 (probability-0 exponent representability, `L-COR-10`) and F18 (proven transcendence, `L-COR-11`) are structural grammar limits that must be excluded from, not smoothed into, any calibration claim.

---

## E6 denominator

**PRIMARY: `GOVERNANCE_DEFINITION_DEFECT`.**
`L-E6-01/04`: (a) the E6 preregistration self-reports a freeze status ("FROZEN_DESIGN_ONLY") that direct git inspection shows is false — the documents are uncommitted; (b) the design's central adjudicability floor (`n_rec≥320`) is derived from abstract binomial power arithmetic with no anchor to any already-measured recoverable-denominator value, and the one sealed denominator study that exists (`L-REC-01`) is framed against a population E6's own design does not state is unit-compatible with its fresh 840-case population.

**Secondary contributor:**
- `BENCHMARK_IDENTIFIABILITY_LIMIT` — DA5 (`L-REC-02`) and the Dimension A kappa-clause tension (`L-REC-03`) are genuine identifiability-measure ambiguities that propagate directly into whatever `n_rec` turns out to be, independent of the governance/commit defect above.

---

## Summary table

| Item | Primary | Secondary |
|---|---|---|
| M1 | BENCHMARK_IDENTIFIABILITY_LIMIT | OBSERVATION_INFORMATION_LIMIT, ESTIMATOR_LIMIT |
| M2 | DECISION_RULE_INFORMATION_LOSS | OBSERVATION_INFORMATION_LIMIT |
| M3 | ESTIMATOR_LIMIT | CLASSIFICATION_LIMIT |
| F05 | ADVERSARIAL_ONLY_LIMIT | ESTIMATOR_LIMIT |
| F09 | RETENTION_LIMIT | — |
| Retention (general) | DECISION_RULE_INFORMATION_LOSS | GOVERNANCE_DEFINITION_DEFECT |
| Symbolic equivalence | IMPLEMENTATION_DEFECT | GOVERNANCE_DEFINITION_DEFECT (already closed in newer SPEC) |
| Confidence | CALIBRATION_LIMIT | GRAMMAR_LIMIT |
| E6 denominator | GOVERNANCE_DEFINITION_DEFECT | BENCHMARK_IDENTIFIABILITY_LIMIT |

## Cross-cutting observation

**Seven of nine items above have their primary cause in a category other than raw estimator/search quality** (`DECISION_RULE_INFORMATION_LOSS` ×2, `BENCHMARK_IDENTIFIABILITY_LIMIT`, `ADVERSARIAL_ONLY_LIMIT`, `RETENTION_LIMIT`, `CALIBRATION_LIMIT`, `GOVERNANCE_DEFINITION_DEFECT` ×1 [E6-denominator; symbolic equivalence's secondary `GOVERNANCE_DEFINITION_DEFECT` is already closed by the newer SPEC, per its own row]). Two items — **M3 and symbolic equivalence** — have their primary cause inside the estimator/implementation layer, but these two are not alike in kind: symbolic equivalence is a genuine, straightforwardly patchable `IMPLEMENTATION_DEFECT` (a sign-check bug in existing code); M3's `ESTIMATOR_LIMIT` is a **structural design floor** in how the target estimator's endpoint normalization is defined — proven to hold even at a perfectly-estimated Phi and true `g` (`L-M3-02`), fixable only by redesigning the estimand itself (Part VI item 5), not by a code patch. This is the single clearest structural fact this reconciliation surfaces: **the v2 program's remaining failures are overwhelmingly architectural (what the frozen decision rule computes, what the benchmark's own construction permits, and — for M3 specifically — how the estimator's own normalization is defined), and only one item (symbolic equivalence) is a simple code bug** — consistent with, and now given a precise causal map for, the standing "evaluability and detector power are separate failures" finding this reconciliation was asked to preserve.
