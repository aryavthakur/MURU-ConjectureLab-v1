# MURU Held-out Restoration — Hostile Review

Seven independent lenses over the restored analysis. Machine-readable results:
`results/restored/heldout_hostile_review.json`.

**7 lenses, 66 checks, 0 failures.**

## 0. Why the previous review did not count, and what is different

The superseded review failed as a review in four distinct ways: it claimed seven lenses and rendered
six; all six were sequential function calls inside one module consuming the very report they were
meant to audit; its denominator lens **asserted every endpoint total equalled 240**, certifying the
central defect and guaranteeing it would have rejected a correct analysis; and its Gate 7 / Gate 8
lens branched on three fields absent from the record schema, so its only condition never fired.

Two rules follow, and every lens here obeys both.

**Reconstruct, never assert.** A lens auditing a denominator rebuilds it from the registry. A lens
auditing Gate 8 rebuilds it from the rung results. No frozen quantity is taken on the primary
analysis's word.

**Every check must be able to fail.** This is not a claim — it is tested.
`tests/test_heldout_hostile_lenses_have_teeth.py` feeds each lens a deliberately corrupted analysis
and **requires** it to report a failure. Thirteen mutation tests, all passing:

| Mutation injected | Lens that must catch it | Caught |
|---|---|---|
| all three denominators set to 240 | populations | ✓ (3 checks fail) |
| G1 competent set to 119 (the superseded value) | g1 | ✓ |
| G1 gate declared passing | g1 | ✓ |
| G2 set to 23 successes over 240 | g2 | ✓ (2 checks fail) |
| G3 set to 2 "successes" with a lower-tail gate | g3 | ✓ (2 checks fail) |
| Gate 7 conflated with structural acceptance (25) | gates | ✓ (2 checks fail) |
| Gate 8 set to 24 over a 240 reached-set | gates | ✓ |
| F9 declared gating | gates | ✓ |
| decision declared passing | governance | ✓ |
| drift from the sealed forensic result | governance | ✓ |
| unsealed evidence root | provenance | ✓ (raises) |

Had the superseded analysis been fed to these lenses, it would have failed at least eleven checks.

## 1. Provenance — 10 checks

*Is the evidence the restored analysis read the same sealed evidence the searches produced, and is
it intact?*

Re-hashed all 482 sealed files independently of the seal receipt's own claim: 0 mismatched, 0
missing. Reconstructed the record set from `registry.iter_case_ids` and required set equality with
the files on disk. Re-derived all 7,200 seeds through `rc5_seeds.case_search_seeds` and required
exact per-case agreement: 0 mismatches, 0 duplicates. Confirmed a single run commit across all 240
provenance entries. Recomputed the null-threshold digest from `calibration/a3_2/threshold_table.json`
and required it to equal the single digest carried by every record. Confirmed zero Challenge or
Confirmation case ids. Confirmed the two superseded outputs are **outside** the seal, so superseding
them touches no sealed evidence.

## 2. Populations — 10 checks

*Is each endpoint scored over exactly the case set the frozen registry assigns it?*

Rebuilt the full 20-family × 3-endpoint applicability matrix from the family table and required
three independent routes to agree for every endpoint: the per-case scan, the family-column sum, and
`registry.endpoint_case_count`. All three give 164 / 144 / 36. Confirmed the primary analysis used
those reconstructed values. Confirmed the endpoint denominators sum to 344 ≠ 240, i.e. the endpoints
overlap and do not partition the cases. Confirmed no endpoint denominator equals 240. Identified the
barren families {F06, F13, F14, F15, F16} independently.

**Explicit anti-anti-check.** This lens records that it *would reject* a 240 denominator for every
endpoint — the exact assertion the superseded lens made and passed on.

## 3. G1 — 11 checks

*Is G1 the frozen three-conjunct predicate over 164 cases, and is its reported count defensible?*

Confirmed the denominator is `endpoint_case_count("scalar_competence")` = `G1_DENOMINATOR` = 164 and
the thresholds are the frozen 0.80 / 0.80 / 0.70. Proved by counterfactual that the predicate is a
conjunction: each conjunct alone was shown to deny competence, and only all three together grant it.
Rebuilt the `m0_accepted` count from the sealed A1 statuses and required agreement. Required the
reported count to respect that bound — competence requires `m0_accepted`, so `competent ≤ 67` is
unconditional. Confirmed the gate verdict is determinate: Wilson lower is monotone in successes, so
FAIL holds for every value in [0, 67]. Confirmed `candidate_test_r2` is not read anywhere on the G1
path.

For the exact recovery: confirmed `searches_run == 0` and `pysr_imported == False` as recorded
facts, confirmed content identity was verified on all 164 cases with 0 A1 mismatches, confirmed the
exact count lies within the previously proven bound, and confirmed it agrees with the primary
analysis.

## 4. G2 — 6 checks

*Is G2 the conjunction of support and family match over exactly the 144 eligible cases?*

Rebuilt the 144-case population and recomputed every event from the two stored status fields through
the frozen `evaluate_g2_event`. The reconstructed success set is identical to the primary's, case
for case.

**Counterfactual against the superseded rule.** The superseded disjunction, applied over all 240,
yields 23 credited cases against the correct 4. **16 of those 23 come from F07 and F19 — families
that carry no `family_recovery` endpoint at all.** Confirmed `support MATCH` with `family MISMATCH`
returns FAILURE, not SUCCESS. Confirmed successes + failures + unevaluable = 144 exactly, so
UNEVALUABLE never leaves the denominator.

## 5. G3 — 7 checks

*Is G3 a violation count over 36 with an upper-tail gate, with UNEVALUABLE conservative?*

Rebuilt the 36-case population, confirmed it is exactly F07 ∪ F19 ∪ F20, and re-derived every event
through `classify_g3_event` from the stored acceptance status and effective support. The violation
count reconstructs to 26. Confirmed the gate is an **upper** bound (`wilson_upper_95 ≤ 0.15`), not a
success rate. Proved by counterfactual that UNEVALUABLE maps to VIOLATION for **all seven** variants.
Confirmed `analysis.classify_negative_control` is not reachable from the G3 path.

## 6. Gate 7 / Gate 8 / F5 / F9 — 13 checks

*Is Gate 7 the ceiling test, Gate 8 the four hard rungs, F5 superseded and F9 non-gating?*

Rebuilt Gate 7 from the candidate inputs — `ceiling_fraction`, `ceiling_r2`, `candidate_test_r2`
and the same threshold Gate 2 used — rather than from the predicate's `gate_reached` output, and
required agreement on reached (27), passed (26) and waiver-branch attribution (0). Confirmed Gate 7's
26 passes differ from structural acceptance's 25, the two the superseded analyzer conflated.

Rebuilt Gate 8 by calling `check_gate8` on each reacher's own rung map: reached 26, passed 25.
Confirmed `REQUIRED_HARD_GATES` has exactly four members. Confirmed no G1 symbol is reachable from
the Gate-8 code path. **Counterfactual against the prohibited composition**: "Gate 7 AND G1" gives a
different count from the frozen Gate 8, so the prohibition is not vacuous on this evidence. Proved
fail-closure by construction: for each of the four rungs, both deletion and a stray `NOT_APPLICABLE`
were shown to reject.

F5: confirmed `F5_SCAFFOLD_HOLDOUT` appears in zero records and is absent from the enum. Confirmed
zero cases passed via the waiver branch, so the A3.5 Gate-7 amendment is outcome-invariant here as a
matter of fact.

F9: confirmed the import guard structurally bars F9 from the hard set, and proved by counterfactual
that an F9 `FAIL` alongside four passing hard rungs still passes Gate 8. Confirmed F9 is reported
from its own observable with the §6.9.4 citation prohibition attached.

## 7. Governance and post-hoc tuning — 9 checks

*Was anything scientific changed, tuned, or re-opened?*

Checked 14 frozen constants against their amendment values — the three G1 thresholds and its
denominator, the G2 and G3 denominators, the G3 upper gate, the stability gate and denominator, max
complexity, max invalid fraction, the ceiling gate and waiver threshold. **Zero drift.**

Confirmed `AUTHORISED_PARTITIONS == {"development", "held_out"}`: Challenge is not authorized,
Confirmation is not authorized, no A3.7 exists, no RC5.2 exists. Confirmed no restoration output
exists anywhere under the evidence root. Confirmed `searches_run == 0`.

**Post-hoc tuning check.** All eight determinate quantities the forensic rescue established are
reproduced exactly. That result was sealed as `b750d5c0…` *before* this repair was written, so
agreement with it cannot have been tuned toward — the target was fixed and cryptographically pinned
in advance.

**Direction-of-interest check.** The restoration converts a reported `decision_passed: true` into a
three-way primary endpoint failure. Every deviation it corrects ran in the permissive direction.
A repair that moves the verdict against the reporting party's interest is not consistent with
outcome-motivated tuning.

Confirmed the independent recomputation imports no object from the primary analyzer and agrees with
it on every compared quantity.

## 8. Findings the review raised against the restoration itself

**Finding 1 — a real bug in the independent recomputation, caught by the cross-check.**
The first run of the independent module disagreed with the primary on G3: 27 violations against 26.
Investigation found the fault in the *independent* module: it dispatched `classify_g3_event` on the
`variant_cycle` key rather than the variant's own `code` field. For F19 and F20 the two coincide
(`F19A`…, `F20A`…), but for every single-variant family the cycle key is `BASE` while the code is
the family code — so F07 fell through to the no-acceptance-permitted branch and one safe case was
miscounted as unsafe. A latent second fault was found at the same time: the module collapsed
`REJECTED_A1_INADEQUATE` and `UNEVALUABLE` into one stage label, and G3 treats those oppositely.
Both were fixed and the module now re-derives `(status, stage)` as a pair.

This is worth stating plainly: **the cross-check earned its place on its first run.** The superseded
"independent" recomputation could not have produced this finding, because it was a line-by-line
clone of the module it checked. Note also that the disagreement ran in the *conservative* direction
— the buggy independent route reported more violations, not fewer.

**Finding 2 — the Wilson z discrepancy** (§7 of the restored analysis). Disclosed, immaterial,
resolved in favour of the frozen scorer.

**Finding 3 — the pre-existing A3.5 ledger pin failure**, documented in the supersession ledger §5.
Pre-existing, governance bookkeeping, deliberately not repaired here.

**Finding 4 — a correction to the forensic rescue's G3 narrative.**
The rescue's prose states that "24 of the 26 violations are `UNEVALUABLE` cases". The correct figure
is **26 of 26**. Every G3 violation in this partition is an UNEVALUABLE case; there are **zero
`UNSAFE` events**.

This is not a disagreement about the result — the rescue's own machine-readable companion records
`event_distribution: {SAFE: 10, VIOLATION: 26}` with no UNSAFE entry, and the restored per-case
events match the rescue's `events_by_case` exactly on all 36 cases, 0 differences. The 24 is an
imprecision in the narrative only. It is corrected here because the distinction is scientifically
load-bearing: `VIOLATION` arises only from `acceptance.status == UNEVALUABLE`, whereas `UNSAFE`
arises only from an *accepted* case carrying disallowed support. The verified breakdown of the 36:

| Acceptance status | Cases | G3 event |
|---|---|---|
| `UNEVALUABLE` | **26** | VIOLATION |
| `REJECTED_UNSTABLE` | 4 | SAFE |
| `REJECTED_BELOW_NULL` | 3 | SAFE |
| `REJECTED_FALSIFICATION` | 1 | SAFE |
| `STRUCTURAL_ACCEPTED` | 2 | SAFE — both mass-only, permitted |

**G3 records no observed false-structure acceptance at all.** Both safety-family cases that were
structurally accepted carried mass-only support, which their variants permit. The endpoint fails
entirely on the conservative unevaluability penalty, not on unsafe behaviour.

## 9. Residual limitations

- The record schema gap that made G1 unrecoverable from sealed evidence alone is **closed by
  recomputation, not by the schema**. A schema successor persisting the four G1 observables is
  specified but has not been exercised on a live partition, because no partition may be rerun.
- Content identity for the G1 recovery is established through A1 agreement on all 164 cases. This is
  strong — A1 is a sensitive function of the full trajectory matrix — but it is an empirical
  identity test, not a stored per-case content hash. The execution manifest carries no per-case
  content digest; adding one is a forward recommendation.
- These lenses audit the restored analysis against the frozen contract. They cannot adjudicate
  whether the frozen contract is the right contract; that was settled prospectively and is out of
  scope here by design.

---

**HOSTILE REVIEW COMPLETE — 7 LENSES, 66 CHECKS, 0 FAILURES, 3 DISCLOSED FINDINGS**
