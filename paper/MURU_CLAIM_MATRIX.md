# MURU prospective manuscript claim matrix

Companion to `MURU_MANUSCRIPT_PRE_RESULTS.md`. Successor in scope, not
replacement, to `MURU_HISTORICAL_CLAIM_MATRIX.md` on
`science/historical-synthetic-consolidation`, which governs CLASS A material and
remains authoritative for it.

**Status semantics.** "Current status" describes what the repository record
supports **today**, before calibration, Development rescoring, Held-out and
Confirmation. It is not a prediction. `PENDING` means the evidence that would
decide the claim does not yet exist.

**Wording rule.** The "allowed wording" column is the ceiling, not a target. If
the evidence comes in weaker, the wording must come down with it. The
"forbidden overclaim" column is binding regardless of outcome.

Governance base: `07c64c8` (`engineering-rc3-1-a3-2`).

---

## C1. Molecule-specific horizontal scale estimation

| Field | Content |
|---|---|
| **Potential claim** | MURU can estimate a molecule-specific horizontal energy scale under controlled synthetic truth. |
| **Required evidence** | G1 success on scalar-applicable Held-out cases: Spearman between true and fold-local estimated log-`g` at least 0.80, held-out trajectory MAE at most 0.80 of the per-energy-mean baseline, and `M0_NOT_REJECTED`. |
| **Relevant endpoint** | G1 scalar competence (PRIMARY); supported by scalar target yield, trajectory prediction, profile stability, boundary hit. |
| **Relevant partition** | Held-out, denominator 164. |
| **Current status** | **PENDING.** Historically, target recoverability was demonstrated only under a transductive estimator (FM-06), so no non-transductive rate is established by any prior artifact. |
| **Allowed wording if supported** | "Under prospectively frozen synthetic conditions, a molecule-specific horizontal energy scale was estimable on scaffold-disjoint held-out compounds, with G1 satisfied in n of 164 cases (Wilson 95% [lo, hi])." |
| **Forbidden overclaim** | That a molecule-specific energy scale exists in real spectra; that `g` is a physical or chemical property; that the estimate transfers across instruments or energy conventions; that historical held-out scale estimates were fold-local. |

## C2. Rejecting scalar adequacy violations

| Field | Content |
|---|---|
| **Potential claim** | MURU can reject scalar adequacy violations, and can do so without rejecting M0 where it holds. |
| **Required evidence** | Both directions. Specificity: `M0_NOT_REJECTED` where M0 truth holds. Sensitivity: the correct detector fires for M1, M2, M3 and, independently per detector, for F16. Detector identity must be preserved: a wrong alternative firing may reject M0 but never satisfies another detector's endpoint. |
| **Relevant endpoint** | M0 specificity, M1 / M2 / M3 sensitivity (SECONDARY); feeds G1's adequacy component. |
| **Relevant partition** | Held-out; denominators 164 / 36 / 24 / 24. |
| **Current status** | **PENDING.** The decision rule itself was only bound prospectively by Amendment A1, which closed a specification gap in content freeze V1. A separate development adequacy diagnostic was closed with the finding of low discrimination, which is recorded as a scientific outcome rather than a defect. |
| **Allowed wording if supported** | "The adequacy ladder rejected M0 in the frozen violation families at the stated sensitivities, and did not reject it in the M0-truth families at the stated specificity, under the Amendment A1 decision rule." |
| **Forbidden overclaim** | That the collapse model is adequate for real fragmentation data; that failing to reject M0 establishes that M0 is true; that an indeterminate adequacy state is evidence of adequacy. |

## C3. Recovering relevant variable support

| Field | Content |
|---|---|
| **Potential claim** | MURU can recover the relevant variable support of the generating relationship. |
| **Required evidence** | `support_status == MATCH` under the frozen effective-support contract, including that `correlated_distractor` is not accepted as interchangeable with `descriptor` (F12) and that independent nuisance variables are excluded (F11). |
| **Relevant endpoint** | Support recovery (SECONDARY); a necessary component of G2. |
| **Relevant partition** | Held-out, denominator 144. |
| **Current status** | **PENDING.** Historically supported narrowly: Type 2 recovered block-level support in 20 of 20 G1B moderate worlds, but on a real descriptor frame where proxy ambiguity required block-level rather than variable-string interpretation. |
| **Allowed wording if supported** | "Effective variable support, extracted deterministically under the frozen grammar with algebraic normalisation, matched the planted support in n of 144 held-out cases." |
| **Forbidden overclaim** | That the recovered variables are the causal drivers of fragmentation; that support recovery implies the functional form is identified; that a proxy variable and its principal are interchangeable. |

### C4. Recovering mathematical family structure

| Field | Content |
|---|---|
| **Potential claim** | MURU can recover the mathematical family structure of the generating relationship. |
| **Required evidence** | `support_status == MATCH` **and** `family_status == MATCH` against the frozen five-member truth taxonomy, with structural, coefficient-agnostic classification on the discovered side. |
| **Relevant endpoint** | **G2 family recovery (PRIMARY).** |
| **Relevant partition** | Held-out, denominator 144; gate Wilson lower 95% at least 0.70. |
| **Current status** | **PENDING.** Historically supported narrowly: Type 2 G1B moderate dense-lattice family recovery was 16 of 20, measured rather than gated; the study's composite success gate, which used support, exponent and shape rather than family identity, passed 17 of 20. Neither number is the G2 definition (support MATCH and family MATCH), both are CLASS A, and neither is eligible as, or comparable to, the prospective endpoint. |
| **Allowed wording if supported** | "Under prospectively frozen synthetic truth, the pipeline recovered both the correct effective support and the correct mathematical family in n of 144 held-out cases (Wilson 95% [lo, hi]), satisfying the pre-specified G2 gate." |
| **Forbidden overclaim** | That the family is the equation; that family recovery means the generating law was discovered; that family recovery implies exact algebraic recovery; that the family generalises to real fragmentation; any use of "law", "universal", or "mechanistic". |

## C4a. Recovering physical parameters and exponents

| Field | Content |
|---|---|
| **Potential claim** | MURU can recover the dimensionless mass scaling exponent and descriptor coupling coefficient of the generating relationship. |
| **Required evidence** | Discovered expression derivatives at canonical anchor $\mathbf{x}_0 = (250, 0, 0, 0, 0)$ satisfying $|p_{\text{mass}}(\hat{g}) - p_{\text{truth}}| \le 0.15$ on 156 held-out cases and $|c_{\text{desc}}(\hat{g}) - c_{\text{truth}}| \le 0.10$ on 84 descriptor-dependent cases under the frozen derivative operators (Amendment A3.4). |
| **Relevant endpoint** | **Parameter recovery (SECONDARY, ungated).** Reported as Joint recovery (/156), Mass exponent recovery (/156), and Descriptor coupling recovery (/84), all with Wilson 95% intervals. |
| **Relevant partition** | Held-out, denominator 156 (joint / mass), 84 (descriptor). |
| **Current status** | **PENDING.** Historically supported narrowly: Type 2 mass exponent recovery was 18 of 20 within +/-0.15 at moderate noise (CLASS A). |
| **Allowed wording if supported** | "At the frozen benchmark anchor, the discovered expressions recovered the planted mass exponent within 0.15 in n of 156 cases (Wilson 95% [lo, hi]) and the descriptor coupling coefficient within 0.10 in m of 84 cases (Wilson 95% [lo, hi])." |
| **Forbidden overclaim** | That parameter recovery implies exact algebraic identification; that parameters are "coordinate-free" (descriptor coupling has dimension $[d]^{-1}$); that recovering synthetic exponents establishes physical mass scaling in real MS/MS. |

## C4b. Achieving predictive equivalence on the reference distribution

| Field | Content |
|---|---|
| **Potential claim** | MURU discovers expressions that are predictively equivalent to the planted law over an independent prospective reference sample from the synthetic covariate generator. |
| **Required evidence** | Discovered expression $\hat{g}$ evaluated across 2,160 reference points (12 frames $\times$ 180 rows, digest `4fef2379...`), achieving $\text{valid\_fraction} \ge 0.995$, least-squares positive scale $c^* > 0$, relative RMSE $\le 0.05$, and Pearson $r \ge 0.990$ with zero-variance failure semantics (Amendment A3.4). |
| **Relevant endpoint** | **Predictive equivalence (SECONDARY, ungated).** |
| **Relevant partition** | Held-out, denominator 144. |
| **Current status** | **PENDING.** This is the first design in which a generator-consistent prospective reference distribution is evaluated. |
| **Allowed wording if supported** | "Across 2,160 reference points sampled from the frozen synthetic covariate generator, discovered expressions achieved relative RMSE <= 0.05 and Pearson r >= 0.990 in n of 144 held-out cases (Wilson 95% [lo, hi])." |
| **Forbidden overclaim** | That predictive equivalence implies mathematical family recovery or exact algebra recovery; describing the reference distribution as a "physical domain", "chemical domain", or "realistic molecular domain"; claiming predictive equivalence on real molecules. |

## C5. Recovering exact generating algebra

| Field | Content |
|---|---|
| **Potential claim** | MURU can recover the exact generating algebra. |
| **Required evidence** | Symbolic equivalence between the reported expression and the planted law, on the cases where exact algebra is an applicable endpoint. |
| **Relevant endpoint** | Exact algebra recovery (SECONDARY, **ungated**, never merged into G2). |
| **Relevant partition** | Held-out, denominator 60 (F01, F08, F09, F10, F17). |
| **Current status** | **PENDING, and historically UNSUPPORTED.** Phase 3 selected-form functional and symbolic recovery was 0% at every G1B noise regime. Type 2 symbolic equivalence was 0 across all positive-control blocks (G1A, G1B, G1C, G3), with a median of 8.5 distinct functional-equivalence classes inside a single reported family. No prospective success may be assumed from G2 success. |
| **Allowed wording if supported** | "Symbolic equivalence to the planted law was observed in n of 60 held-out cases (Wilson 95% [lo, hi]) under the frozen grammar and normalisation." Any positive statement must also report the number of distinct functional-equivalence classes, because a single equivalent expression among many does not identify the algebra. |
| **Forbidden overclaim** | "The equation was recovered"; "the law was discovered"; presenting a single expression as the generating relationship; inferring exact recovery from family recovery or predictive equivalence; treating a low rate as a G2 failure or repairing it by loosening the equivalence definition. |

## C6. Avoiding false discoveries under tested nulls

| Field | Content |
|---|---|
| **Potential claim** | MURU avoids false structural discoveries under the tested null and adversarial worlds. |
| **Required evidence** | G3 unsafe-event rate across the 36 opportunities, with `UNEVALUABLE` counted as a violation, plus the three component rates reported separately; and calibration validity, without which no threshold table is active and no acceptance is meaningful. |
| **Relevant endpoint** | **G3 principal structural safety (PRIMARY)**, with F07, F19 and F20 components. |
| **Relevant partition** | Held-out, denominator 36; gate Wilson upper 95% at most 0.15. Precondition: calibration valid on at least 95 of 100 worlds. |
| **Current status** | **PENDING.** Historically supported narrowly for the tested constructions: 0 of 100 accepted pure-null worlds in both Phase 3 and Type 2, Clopper-Pearson 95% [0.0000, 0.0362]. Those are bounded constructions on a different world family and are CLASS A. |
| **Allowed wording if supported** | "Across the 36 frozen structural-safety opportunities, n unsafe acceptances occurred (Wilson 95% upper bound u), satisfying the pre-specified gate of 0.15. This applies to the tested F07, F19 and F20 constructions and to the frozen pipeline." |
| **Forbidden overclaim** | "The false discovery rate is zero" or any `p = 0` phrasing for a finite simulation count; that the pipeline is safe against untested confounding or coupling mechanisms; that a good G3 result licenses real-data discovery. |

## C7. Detecting structure beyond mass

| Field | Content |
|---|---|
| **Potential claim** | MURU detects genuine non-mass structure and does not invent it where truth is mass-only. |
| **Required evidence** | Two directions, both required. Positive: support and family recovery in the families whose truth includes a non-mass carrier. Negative: F07 (mass-only truth) producing no accepted non-mass structure, and F20A / F20B not producing accepted structural claims. F8 structural labelling reported as a label, never as a gate. |
| **Relevant endpoint** | G2 (positive direction); F07 false extra structure and F20A/F20B (negative direction). |
| **Relevant partition** | Held-out; 144 for G2, 12 for F07, 4 each for F20A and F20B. |
| **Current status** | **PENDING, and historically WEAK in the positive direction.** Type 2's F8 rung certified structure beyond mass in only 1 of 19 accepted G1B moderate worlds despite support recovery in 20 of 20; on a fully synthetic covariate frame with independent descriptors the same rung fired 3 of 6. Phase 2's mass-coupling audit separately showed rho = -0.4791 arising from a stipulated cutoff with no chemistry. |
| **Allowed wording if supported** | "In families whose planted truth contains a non-mass carrier, the recovered support included that carrier in n of m cases; in mass-only families, non-mass structure was accepted in k of 12 cases." Both numbers must appear together. |
| **Forbidden overclaim** | That non-mass structure exists in real fragmentation data; that a recovered non-mass carrier is chemically meaningful; that a mass association implies chemistry; quoting the positive direction without the negative one. |

## C8. Generalizing to held-out compounds

| Field | Content |
|---|---|
| **Potential claim** | MURU generalizes to held-out compounds within the synthetic benchmark. |
| **Required evidence** | Scaffold-disjoint held-out performance under the frozen execution boundary, where all shared objects are fitted from training trajectories only and each test compound is estimated independently. Trajectory prediction against the per-energy-mean baseline, and predictive equivalence to the planted law on the declared domain. |
| **Relevant endpoint** | G1's MAE component; trajectory prediction (164); predictive equivalence (144). |
| **Relevant partition** | Held-out. |
| **Current status** | **PENDING.** Historical predictive results were obtained under a transductive estimator (FM-06) and therefore do not establish a fold-local generalization rate. This is the first design in which such a rate is measurable. |
| **Allowed wording if supported** | "On scaffold-disjoint held-out compounds, with all shared objects fitted from training trajectories only, trajectory MAE was at most 0.80 of the per-energy-mean baseline in n of 164 cases, and predictive equivalence to the planted law held in m of 144." |
| **Forbidden overclaim** | Generalization to real compounds, to other instruments, to other energy conventions, or to chemistry outside the synthetic covariate space; describing historical held-out metrics as fold-local. |

## C9. Identifying a real collision energy law

| Field | Content |
|---|---|
| **Potential claim** | MURU identifies a real collision energy law. |
| **Required evidence** | Real-data symbolic discovery on an authorized Phase 4, validated on the sealed real-data Confirmation set, with independent replication. None of this exists or is authorized. |
| **Relevant endpoint** | None in this benchmark. |
| **Relevant partition** | None. The real-data Confirmation set (110 compounds, 82 scaffold groups) remains sealed at SHA-256 `d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07`. |
| **Current status** | **UNSUPPORTED, and unsupportable by this work.** Phase 3 is `STOP BEFORE PHASE 4`. Type 2 is `DO NOT AUTHORIZE PHASE 4`. The real-data claims ladder stands at L3. No real-data symbolic search has ever been executed. |
| **Allowed wording if supported** | None. This claim is not available from this manuscript under any prospective outcome. |
| **Forbidden overclaim** | Every form of it. Including softened variants: "consistent with a real collision energy law", "suggests a universal scaling law", "the first equation for collision-energy scaling", or presenting the synthetic benchmark as evidence about real spectra. |

## C10. Establishing mechanism

| Field | Content |
|---|---|
| **Potential claim** | MURU establishes a mechanism of fragmentation. |
| **Required evidence** | Interventional or independently identified causal evidence. Nothing in this project's design, synthetic or real, is capable of producing it. |
| **Relevant endpoint** | None. |
| **Relevant partition** | None. |
| **Current status** | **UNSUPPORTED, and unsupportable by this work.** The synthetic laws are chosen functional forms over synthetic covariates. On the real-data side, the mass-coupling audit is explicitly a sensitivity construction and identifies no artifactual fraction; the retention-time stress test resolves no causality. |
| **Allowed wording if supported** | None. |
| **Forbidden overclaim** | Every form of it. Including: "explains", "is driven by", "the physical basis of", "mechanistic law", "RRKM-consistent", or any causal verb applied to a recovered expression. |

---

## Cross-cutting wording rules

These apply to every claim above and to every section of the manuscript.

1. **Never call a discovered expression a law.** Not universal, not physical,
   not mechanistic, not biological. This holds for every prospective outcome.
2. **Never infer exact algebra from family recovery, or family recovery from
   predictive equivalence, or exact law identification from parameter recovery.**
   The four endpoints represent distinct epistemic levels with separate
   denominators (G2 family 144, exact algebra 60, parameter recovery 156,
   predictive equivalence 144) and must be reported independently. Any positive
   secondary result remains subordinate to the primary benchmark gates (G1, G2, G3).
3. **Never quote a zero count as a zero rate.** Report the interval. `p = 0`
   language is not used for a finite simulation count.
4. **Never present a historical result as prospective evidence.** CLASS A
   material is labelled as background, method development, or supporting
   synthetic evidence, and never enters a prospective denominator.
5. **Never rewrite a historical failure as a success.** Phase 3 remains
   `STOP BEFORE PHASE 4`; Type 2 remains `DO NOT AUTHORIZE PHASE 4`. The Type 2
   corroboration gate failed. The later competence audit narrows what that
   failure implies about PySR's candidates; it does not convert the failed gate
   into a pass, and `DO NOT AUTHORIZE PHASE 4` remains binding.
6. **Never describe a corrected defect as still active, or an active limitation
   as corrected.** Table 10 of `MURU_TABLE_SHELLS.md` is the authority on which
   is which.
7. **Never state a prospective number before its artifact exists.** Use
   `[PROSPECTIVE RESULT TO INSERT]`.
8. **Never adjust a denominator, a gate, or a success definition after
   execution.** All are frozen and hashed.
9. **Engineering smoke is not scientific evidence** and is never cited as such.
10. **A failed gate blocks the positive claim.** It is not replaced by a weaker
    claim selected after the fact; the descriptive endpoint tables stand on
    their own. Secondary endpoints never rescue a failed primary gate.

## Claim status summary

| Claim | Prospective status | Historical status | Available from this work at all |
|---|---|---|---|
| C1 molecule-specific horizontal scale | PENDING | narrow, transductive only | Yes |
| C2 reject scalar adequacy violations | PENDING | rule bound prospectively by A1 | Yes |
| C3 recover variable support | PENDING | supported narrowly | Yes |
| C4 recover mathematical family | PENDING | supported narrowly (CLASS A) | Yes (PRIMARY gate G2) |
| C4a recover physical parameters and exponents | PENDING | supported narrowly (CLASS A) | Yes, as ungated secondary endpoint |
| C4b achieve predictive equivalence | PENDING | unmeasured on generator distribution | Yes, as ungated secondary endpoint |
| C5 recover exact generating algebra | PENDING | **unsupported** | Yes, as ungated secondary endpoint |
| C6 avoid false discoveries under tested nulls | PENDING | supported narrowly for tested constructions | Yes (PRIMARY gate G3) |
| C7 detect structure beyond mass | PENDING | **weak** | Yes, both directions required |
| C8 generalize to held-out compounds | PENDING | not established fold-locally | Yes |
| C9 identify a real collision energy law | **UNSUPPORTED** | unsupported | **No** |
| C10 establish mechanism | **UNSUPPORTED** | unsupported | **No** |
