# MURU v2 Pre-E6 Governance Amendment

**Status:** SEALED synthesis, results-blind to E2.

**CRITICAL RULE preserved throughout:** no historical frozen document is edited in place. Every change below is a new, versioned amendment record. Original artifacts remain untouched (verified: this reconciliation made zero edits to any file outside this branch's own new deliverables — see `MURU_V2_RECONCILIATION_PROVENANCE.json`).

---

## AMENDMENT 1 — `MURU_V2_E6_FINAL_VALIDATION_PREREGISTRATION.md` (+ its 3 JSON/companion docs)

**Disposition: `ERRATUM` (freeze-status correction) + `VERSIONED_SEMANTIC_AMENDMENT` (n_rec dependency disclosure).**

- **Old definition:** Document header states `Status: FROZEN_DESIGN_ONLY`, `Date frozen: 2026-08-17`, freeze parent commit `9940034`.
- **New definition:** Status is `DESIGN_COMPLETE_UNCOMMITTED` until the four core documents (`MURU_V2_E6_FINAL_VALIDATION_PREREGISTRATION.md`, `MURU_V2_E6_SAMPLE_SIZE_ANALYSIS.md`, `MURU_V2_E6_MANIFEST_TEMPLATE.json`, `MURU_V2_E6_ACCEPTANCE_RULES.json`) and `scripts/e6_design/` are actually committed to a named branch and the manifest's `protocol_freeze_commit`/`protocol_document_sha256` fields are populated from that commit — at which point, and only then, the document may correctly self-report `FROZEN_DESIGN_ONLY`.
- **Reason:** Direct git inspection (`L-E6-01`) shows all four documents are untracked (`??`), with no commit anywhere in the repository's history containing any of them, and the manifest's provenance fields are literal unfilled `<FILL>` placeholders. This is a factual correction of the document's own self-report, not a scientific change.
- **Evidence available before E2 unblinding:** Yes — this is a pure git-state fact, independent of any E2 outcome.
- **Effect on denominators/endpoints:** None directly. But see the second sub-amendment below.
- **Second sub-amendment (VERSIONED_SEMANTIC_AMENDMENT):** Add an explicit, pre-declared disclosure to §5.3/§6.1: "`n_rec≥320` is derived from binomial power arithmetic alone and is not anchored to any already-measured recoverable-denominator value; the sealed recoverability-ceiling document's four ceilings (132.00/118.62/12.00/118.61-or-61.63) are computed against a different, 240-case v1-scale population and are not unit-compatible with this document's fresh 840-case/462-representable-symbolic population without an explicit, not-yet-performed translation. This dependency must be checked against E6's own realized `n_rec` once available, before P1–P4 are adjudicated." (`L-E6-04`)
- **Historical numbers change?** No — R=42, N=840, the OC/power tables, and every gate threshold in §6/§8 are unaffected; they are internally correct given their own stated inputs.
- **Prospective evaluation changes?** Yes — E6 must not be executed, and its freeze must not be finalized, until (a) the commit step above is done and (b) the `n_rec` dependency disclosure is added. Both are mechanical, non-scientific, results-blind, and performable immediately.

---

## AMENDMENT 2 — `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` (+ `PROTOCOL.json`, hostile-review checklist)

**Disposition: `ERRATUM`.**

- **Old definition:** §7 / `required_metrics[1].population` / hostile-review checklist §4.3 all state the `mass_power`-truth `V2C_RET_EVAL` population is **36** cases.
- **New definition:** **90** cases (9 (regime,noise) cells × 10 EVAL replicates), independently re-derived from the already-frozen `MURU_V2_E2_PREDECLARATION.md` §4 population/split definitions.
- **Reason:** `L-RET-05` — a propagated arithmetic transcription error, confirmed by direct re-derivation from definitions already frozen before this correction; no new assumption introduced.
- **Evidence available before E2 unblinding:** Yes — pure arithmetic on already-frozen population definitions, zero E2a data required.
- **Effect on denominators/endpoints:** Widens metric-2's Wilson interval precision by a factor of ~2.4 (upper bound at zero events: 0.041 at n=90 vs. 0.096 at n=36). Both clear the 0.15 adoption ceiling, so this is **non-blocking** for the specific zero-events screen the preregistration's own worked prediction assumes.
- **Historical numbers change?** No results exist yet to change (E4a is unexecuted).
- **Prospective evaluation changes?** Yes — any real Wilson-interval computation for this metric, once E4a runs, must use 90, not 36. Correct this before execution, not after.

**Second, optional, non-required sub-amendment (`CLARIFICATION_ONLY`):** correct PRR-1's hedged phrasing ("near 1.0 except for `mass_saturating_descriptor`") to state `conditional_retention_recall(R3)=1.0` is an exact tautology with no family exception (`L-RET-04`). Does not change any adoption decision.

---

## AMENDMENT 3 — `MURU_V2_THEORETICAL_RECOVERABILITY_CEILING.md` (+ schema)

**Disposition: `NO_CHANGE` to the four headline numbers; `CLARIFICATION_ONLY` for one cross-reference; the three blocking disambiguations remain explicitly open, per the mission's own instruction not to force a resolution.**

- **Old definition:** §3.1.1 cross-references "Section 9.5" for blocking disambiguation DA5.
- **New definition:** §9.4 (the section renumbering left a stale pointer after the DA5 amendment inserted a new §9.4 and pushed the old Dimension-I section to §9.5).
- **Reason:** A cosmetic cross-reference bug found during this reconciliation's independent read (`L-REC-02`'s source entry); does not affect any number.
- **Evidence available before E2 unblinding:** Yes.
- **Effect on denominators/endpoints:** None.
- **Historical numbers change?** No.
- **Prospective evaluation changes?** No — cosmetic fix only.

**Not amended, deliberately left as `UNRESOLVED_TENSION` for a separate governance ratification act (see Amendments 4 and 5 below), per the mission's explicit instruction that this reconciliation must not choose based on which reading raises the ceiling.**

---

## AMENDMENT 4 — Dimension A of `MURU_V2_CORRECTNESS_CONFIDENCE_SPEC.md` / `PROTOCOL.md` (DA5, the measure question)

**Disposition: `GOVERNANCE_RATIFICATION_REQUIRED` — not resolved by this document.**

- **Old definition:** §2.1 declares the uniform product measure over `Ω=[120,550]×[0,1]×[0,1]` for Dimension A's Δ_L2 distance, with no reference to the generator's realized covariate distribution.
- **Proposed new definition (NOT adopted, presented for ratification):** Either (a) retain the uniform measure explicitly, acknowledging it is a deliberate reference-space convention, not a claim about operational recoverability; or (b) switch Dimension A's distance computation to the realized-covariate measure, accepting `UNIQUE_RECOVERY_CEILING` becomes 0/undefined and Recovery Efficiency requires a redefinition.
- **Reason for flagging now, not adopting:** `L-REC-02` — the realized-measure reading (AMCS-v2, design-stage) directly and irreconcilably tensions against E3's fully-executed empirical finding that `mass_interaction` is the *most* identifiable family. Neither reading is favored by this reconciliation on the merits of raising or lowering the ceiling; a ratification decision by whoever owns the frozen Dimension A specification is required, using the frozen spec's own literal text (uniform) versus AMCS-v2's operational argument (realized) as the two positions to adjudicate — informed also by the standing E3-vs-realized-measure tension neither document resolves.
- **Evidence available before E2 unblinding:** Yes — everything needed (SIM's proofs, E3's sealed results, AMCS-v2's design-stage figures) is already sealed or design-only; nothing here requires E2.
- **Effect on denominators/endpoints:** `UNIQUE_RECOVERY_CEILING`: 12.00 cases (uniform) vs. 0.00/undefined (realized) — the single largest binary swing in the framework.
- **Historical numbers change?** No historical MURU evaluation has been scored against this denominator yet.
- **Prospective evaluation changes?** Yes, materially — E6-R's endpoint 6.1 (recovery efficiency) cannot report a single unique-recovery number until this is ratified.

---

## AMENDMENT 5 — Dimension E of `MURU_V2_CORRECTNESS_CONFIDENCE_SPEC.md` (scale convention)

**Disposition: `GOVERNANCE_RATIFICATION_REQUIRED`, with a reasoned recommendation offered (not imposed).**

- **Old definition:** §6 computes Functional Recovery RelRMSE **RAW** (no positive-scale requoting).
- **Recommended new definition:** SCALED (positive-multiplicative-scale-quotiented) as the **primary** reported criterion, RAW retained as a **mandatory secondary diagnostic**, never silently dropped.
- **Reason:** `L-COR-02` — every other correctness mechanism already in the frozen codebase (`equivalence.py`'s docstring, `a34_predictive_equivalence.py`'s `c_star` refit, G1's scale-invariant log-g correlation, and the SPEC's *own* §4 exact-equivalence oracle) already commits to "equivalence up to a positive multiplicative constant." RAW is the sole exception, with no stated rationale in the SPEC for the exception. This recommendation is grounded in consistency with the system's own already-declared convention; it is disclosed explicitly that it also happens to raise `SET_VALUED_ACCEPTABLE_RECOVERY_CEILING` from 61.63 to 118.61 cases, and that this numeric fact is a *consequence*, not the justification, of the recommendation. RAW must never be dropped because it is exactly what surfaces F18's proven "safety trap" (a wrong-family candidate scoring 0.026–0.125% RelRMSE).
- **Evidence available before E2 unblinding:** Yes.
- **Effect on denominators/endpoints:** `SET_VALUED_ACCEPTABLE_RECOVERY_CEILING`: 118.61 (scaled, recommended primary) vs. 61.63 (raw, current literal text) — a 1.92×, 57-case swing.
- **Historical numbers change?** No prior evaluation has been scored against this criterion.
- **Prospective evaluation changes?** Yes — same governance-owner ratification required as Amendment 4, ideally resolved together since both feed E6-R's endpoint 6.1.

---

## AMENDMENT 6 — `MURU_V2_STRUCTURAL_IDENTIFIABILITY_MAP.md` / correctness-confidence SPEC's Dimension A condition-number clause

**Disposition: `GOVERNANCE_RATIFICATION_REQUIRED` — the framework's own internal reading conflict, not a change to SIM's proofs.**

- **Old definition:** `kappa<10⁴` with no stated Jacobian scope (joint-pairwise vs. within-family).
- **Proposed new definition (NOT adopted):** Explicitly scope the clause to the **within-family design Jacobian** — the only reading under which the clause is ever satisfiable for any descriptor family and the only one consistent with the frozen spec's own worked example (aff vs. exp at c≤0.25 ⇒ MARGINAL, not NONIDENTIFIABLE).
- **Reason:** `L-REC-03` — SIM's own LEMMA 2 (exact) proves the joint-pairwise Jacobian has a null direction at every parameter value; taken literally, this reading makes `kappa` infinite for every descriptor family, contradicting the framework's own example. This is a tension inside the frozen framework's own text, disclosed by the recoverability-ceiling document, not between two independent studies.
- **Evidence available before E2 unblinding:** Yes.
- **Effect on denominators/endpoints:** If ratified toward the joint-pairwise reading, every Dimension-A-gated ceiling collapses toward zero — this is a live, high-stakes governance decision.
- **Historical numbers change?** No.
- **Prospective evaluation changes?** Yes, potentially total — this is the highest-leverage unresolved item in the entire framework and should be ratified alongside Amendments 4/5.

---

## AMENDMENT 7 — `MURU_V2_M2_INFORMATION_SCALING_THEORY.md`

**Disposition: `PROSPECTIVE_REPLACEMENT` of its provenance status — commit it, do not edit its content.**

- **Old definition (provenance status):** Untracked working-tree file on `claude/m2-repair-information-theory-125035` (HEAD still `5049a1a`).
- **New definition:** Commit the file verbatim, unaltered, to its own branch, and subject it to the same hostile-audit process every other sealed theory document in this program received before any of its predictions (e.g. the 6-of-13-M2R1-arms-inert prediction) are treated as more than `PROSPECTIVE_THEORY_PREDICTION`.
- **Reason:** `L-M2-07`/`L-M2-10`/`L-M2-11` — the content is real, careful, internally rigorous analysis (its exact-algebra subsections independently verified against production source in this reconciliation), but it is the only theory document in the entire v2 program that was never committed, and it disagrees by ~14% with an independently-committed sibling document (the detectability lower bound) on the exact magnitude of one reconciliation (efficiency-ratio correction) without either citing the other.
- **Evidence available before E2 unblinding:** Yes — this is a repository-hygiene action, not a scientific one.
- **Effect on denominators/endpoints:** None directly; it affects only how confidently its predictions may be cited (as sealed vs. unsealed theory).
- **Historical numbers change?** No.
- **Prospective evaluation changes?** No, until item 1 of `MURU_V2_FINAL_REMAINING_PROGRAM.md` runs, at which point this theory's predictions become directly testable.

---

## AMENDMENT 8 — `MURU_V2_MATHEMATICAL_CORRECTNESS_AUDIT.md` / `MURU_V2_SYMBOLIC_EQUIVALENCE_AUDIT.md` — `discovery/equivalence.py`

**Disposition: `NO_CHANGE` to either audit document; `CLARIFICATION_ONLY` recommended for a future patch record (not created here, since patching `equivalence.py` is out of scope for a results-blind reconciliation).**

- **Old definition:** Two audits, using the same finding label ("E1"/"E-1") for two mechanistically different, both-unpatched defects in the same function.
- **New definition:** No change to either audit's own findings. Recommend (not perform) a disambiguating relabel the next time either document is touched, so the shared identifier does not cause future confusion (`L-COR-03`, `L-RET-08`).
- **Reason:** Bookkeeping collision, not a scientific conflict.
- **Evidence available before E2 unblinding:** Yes.
- **Effect on denominators/endpoints:** None — both defects are already correctly excluded from the newer correctness/confidence SPEC's own oracle definition, which independently does not inherit either bug.
- **Historical numbers change?** No.
- **Prospective evaluation changes?** Low priority — relevant only once E4a's stage C/D split or PRR-5 executes at scale.

---

## AMENDMENT 9 — `discovery/equivalence.py` production module

**Disposition: `PROSPECTIVE_REPLACEMENT` — a scoped code fix, not performed by this document (out of scope: this reconciliation must not alter production scientific code).**

- **Old definition:** `numeric_relation()` accepts sign-unconstrained least-squares scale as proof of equivalence; a separate nan-ratio path also produces a false positive.
- **New definition (recommended, not implemented here):** Both audits' own proposed patches (explicit `k>0`/non-nan checks at every stage) should be applied, mirroring what the newer correctness/confidence SPEC's own oracle already does correctly.
- **Reason:** `L-COR-03`, `L-RET-08` — confirmed, reproducible, low-reachability-on-their-own-corpora defects, relevant to E4a's future stage C/D split and PRR-5.
- **Evidence available before E2 unblinding:** Yes.
- **Effect on denominators/endpoints:** None of the denominators derived in this reconciliation depend on this function (they use E3's/E-STAB's closed-form-oracle fits, not the symbolic equivalence oracle) — see Part VIII's explicit note. E4a's future stage C/D metrics do depend on it.
- **Historical numbers change?** No.
- **Prospective evaluation changes?** Only for E4a's stage C/D metrics, once built and run.

---

## AMENDMENT 10 — Cross-document compatibility check for the E6-S/E6-R single-shot re-scoping

**Disposition: `CLARIFICATION_ONLY` (an action item, not a document edit) — added after hostile review found this required check, named by the reconciliation doc itself (`L-E6-05`), had no corresponding entry anywhere in this amendment list.**

- **Old definition:** No amendment tracked the compatibility question `L-E6-05` raises.
- **New definition:** Before E6 is committed/frozen, explicitly check every repair-lane preregistration written against the *original* per-candidate-change E6 register (`befca0d`) for compatibility with the *new* single-shot E6-S/E6-R design (`ST-1`: "E6 executes once... cannot be re-run"). Starting point: the retention-remediation preregistration's own clause "a change satisfying every retention criterion and failing E6 is not adopted" (already confirmed, per the E6 document's own §0.3 table, to be discharged by the new design) — verify this and any similarly-worded clause in the M2R1 preregistration or any future repair-lane document.
- **Reason:** `L-E6-05` — the re-scoping is disclosed and reasoned through in the E6 document itself, but no document in this reconciliation's deliverable set had tracked it as a required pre-freeze action, an omission a hostile-review pass specifically caught.
- **Evidence available before E2 unblinding:** Yes — this is a cross-document text-compatibility check, not a scientific one.
- **Effect on denominators/endpoints:** None directly; failure to perform this check risks a repair lane believing it has an E6 safety discharge path that no longer operates the way its own text describes.
- **Historical numbers change?** No.
- **Prospective evaluation changes?** Only insofar as it is a precondition for freeze, alongside Amendment 1's other three required items.

---

## Documents receiving `NO_CHANGE`

`MURU_V2_CAUSAL_DECISION_TREE.md`, `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md`, `MURU_V2_A1_STUDY_DESIGN.md`, `MURU_V2_G2_PARETO_STUDY_DESIGN.md`, `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md`, `adequacy.py`/`generator.py`/`g2_contract.py`/`g3_contract.py`/`registry.py`/`grammar.py` (production source — every study's own hostile audit plus this reconciliation's independent `git diff` re-verification confirms zero drift, see `L-GOV-01..07`), the E0/E1 results and hostile reviews, the M1/M2/M3 diagnosis and repair-tournament results, F09's results, SIM/E3/E-STAB/math-correctness/symbolic-equivalence audits, the coefficient-recovery-ceiling and F05-boundary-diagnosis results, and `MURU_V2_MASTER_FIRST_LOSS_SCHEMA.json`/`MURU_V2_CONFIDENCE_SEMANTICS.md` (both consistent with everything cited against them in this reconciliation).

## Summary table

| Document | Disposition |
|---|---|
| E6 final validation preregistration (+companions) | ERRATUM (freeze status) + VERSIONED_SEMANTIC_AMENDMENT (n_rec disclosure) |
| Retention remediation preregistration (+companions) | ERRATUM (36→90) + CLARIFICATION_ONLY (PRR-1 phrasing) |
| Recoverability ceiling doc | CLARIFICATION_ONLY (stale cross-ref) |
| Correctness/confidence SPEC, Dimension A (DA5) | GOVERNANCE_RATIFICATION_REQUIRED |
| Correctness/confidence SPEC, Dimension E | GOVERNANCE_RATIFICATION_REQUIRED (recommendation offered) |
| Correctness/confidence SPEC, Dimension A kappa clause | GOVERNANCE_RATIFICATION_REQUIRED |
| M2 information-scaling theory | PROSPECTIVE_REPLACEMENT (commit, hostile-audit; content unaltered) |
| Math-correctness / symbolic-equivalence audits | NO_CHANGE (relabel recommended, not performed) |
| `discovery/equivalence.py` | PROSPECTIVE_REPLACEMENT (patch recommended, not performed) |
| E6-S/E6-R re-scoping cross-document compatibility | CLARIFICATION_ONLY (action item, added after hostile review) |
| Everything else listed above | NO_CHANGE |

**None of the above requires reading unfinished E2 outcomes. None alters frozen thresholds to manufacture a 95% headline. Every ratification-required item is presented as a genuine open choice, not resolved by this document.**
