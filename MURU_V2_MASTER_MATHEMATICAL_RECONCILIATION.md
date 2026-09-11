# MURU v2 Master Mathematical Reconciliation

**Status:** SEALED synthesis, results-blind to E2. Every claim below cites a ledger entry (`L-<ID>`) in `MURU_V2_MASTER_EVIDENCE_LEDGER.md`; nothing here is asserted without a traceable source.

---

## PART IV — M1

### 1–2. What is identifiable, and what is exactly absorbed by M0?

`L-M1-02` (Theorem 1, exact, symbolically verified): the across-compound **common** M1 amplitude is exactly unidentifiable against the shared M0 profile — a reparameterization identity, not an estimation-difficulty claim. At the frozen amplitude, **~92.6%** of the planted deviation's mean-square sits in this unidentifiable component. The identifiable share (compound-specific heterogeneity around the shared warp) brackets to **[6.7%, 19.4%]** across plausible descriptor-law assumptions.

### 3. What fraction of the planted reference signal is theoretically observable?

**~7–19%**, per the same theorem. This is a property of the benchmark's own generative law (a horizontal-scaling model whose common warp is definitionally a reparameterization of any admissible M0 profile) — not fixable by any statistic, estimator, or coordinate choice.

### 4. Nuisance-adjusted information

The theory's nuisance-projected efficient-score statistic has an **exact** `F₂₆,₁₂₀` null distribution (level 0.049369, matched to the frozen `Binomial(30,0.5)` tail so no new magnitude constant is introduced).

### 5. Best justified oracle power ceiling

**0.188 (exact F) to 0.218 (known sigma)** at the frozen reference cell (alpha=1.0, noise=0.02, N=30, n_e=6) — for a statistic that is *deliberately descriptor-blind* (reading `descriptor` would encode the planted law into the detector, refused per the causal decision tree's B.4/O4 precedent). `L-M1-02`.

### 6. Additional loss from the current LOEO statistic

Severe, and separately confirmed on two independent tracks. `L-M1-01`: under **oracle parameters**, the frozen LOEO practical-win contrast scores 0/1,200 practical wins and *below-coin-flip* directional accuracy — worse than the honest ~19–23% ceiling would allow, not merely below the 80% bar. `L-M1-03`: every genuinely descriptor-blind M1R1 candidate (S1, S2, S3, S5 — Rao score, cross-fitted projection, fixed-nuisance contrast, orthogonalized C(alpha)) measures **exactly 0.0%** power at the reference cell, again below the theory's own ceiling. The frozen statistic is not merely capped by identifiability — it is additionally, independently, statistic-limited (CM1 fitted-parameter bias and CM4 isotonic-profile flatness, both `CONFIRMED` in M1CD).

**The apparent contradiction with M1R1's S4 candidate (36.0% power, nearly double the theory's ceiling) is resolved, not left open** (`L-M1-03`, ledger cross-check): S4 is verified — by reading its actual implementation (`git show ec3a974`, `scripts/m1r_common.py:48`, `scripts/m1r_fit.py:172,311`) — to hard-code the generator's own amplitude constant (`generator.M1_HORIZONTAL_AMPLITUDE`) and functional form (`tanh(descriptor)`). It is a near-oracle, descriptor-informed 1-df directional test, exactly the construction the theory explicitly derives would have "materially higher power" and explicitly refuses to build on governance grounds (encoding the planted law is "information about the benchmark, not a license"). S4 additionally fails its own tournament's Gates 1–3. The two numbers measure different questions and do not contradict each other; **every genuinely descriptor-blind candidate in the M1R1 tournament (S1, S2, S3, S5) measures exactly 0.0% power at the reference cell** — below, not merely "consistent with," the theory's 0.188–0.218 ceiling. (S1 and S5's *full-grid-averaged* power of 10.5% is not a reference-cell number — it is dominated by a disclosed noise=0.0 "any extra free parameter wins" artifact that collapses to 0.0% the moment noise is turned on; citing it as a reference-cell figure would be a synthesis error, not a source-evidence one, and is avoided here.)

**One closely-related puzzle from the same candidate set remains genuinely open, not resolved by the above**: S1 and S5 also use `descriptor` (as a case-aggregation weight) yet still measure exactly 0.0% at the reference cell, unlike S4 — an asymmetry neither M1R1 nor the theory explains (`L-M1-07`, tagged `UNRESOLVED_TENSION`, not settled by this reconciliation). This does not affect the S4-vs-theory resolution above, which turns on S4's specific hard-coded construction, independently verified.

### 7. Was FI1's WELL_CONDITIONED label mathematically justified?

**Not fully.** `L-M1-05`: FI1's `theoretical_snr=7.89` was computed against the full, uncentered amplitude. Restricted to the Theorem-1-identifiable component, the SNR falls to ~2.15 — *below* FI1's own INFO_OK bar of 3.0 — which under FI1's own mechanical rule reclassifies M1 as INFORMATION_LIMITED. The EST_OK half (low estimator variance around a biased mean) remains true. FI1's own downstream recommendation ("decontamination should recover it strongly") is independently contradicted by SA1's measured 32.0% ceiling under full oracle-clean-training decontamination — "real but insufficient," not "recovers strongly."

### 8. Is M1 STATISTIC_LIMITED, INFORMATION_LIMITED, IDENTIFIABILITY_LIMITED, or MIXED?

**MIXED, with an orderable structure, not an unresolved ambiguity:**

- **Primarily IDENTIFIABILITY_LIMITED** — Theorem 1 (exact) caps any conceivable statistic at ~7–19% of the planted signal.
- **Secondarily INFORMATION_LIMITED** for the identifiable residual — even a hypothetical, correctly-specified, descriptor-blind, exactly-sized efficient-score test caps at 0.188–0.218, because of (a) the isotonic profile estimator's slope-fidelity loss relative to the analytic profile (~63% of remaining information lost) and (b) the small N=30/n_e=6 design.
- **Additionally, independently, STATISTIC_LIMITED** for the *currently deployed* statistic — it performs *worse* than the honest ceiling would allow (0.0% vs. ~19–23%), a genuine defect layered on top of, not merely a symptom of, the identifiability ceiling.

### 9. Can any statistic redesign reach the historical 0.80 target under the current benchmark?

**No — closed empirically as well as theoretically.** `L-M1-03` (executed, 1,500 fresh worlds, hostile-audited 13/13): `NO_M1_STATISTIC_REPAIR_LICENSED`. Combined with `L-M1-04` (RC1, coordinate reparameterization), `L-M1-06` (A1PR profile-architecture redesign, PCL localized-component ablation): **every investigated M1 repair axis is closed** (`CONTRA` for the identifiability-bound component, `CLOSED_NEGATIVE` empirically for every tested axis). No statistic redesign under the current benchmark's planted amplitude and acquisition geometry can reach 0.80.

### 10. The scientifically correct treatment of M1 in the final benchmark

Three options were named in the mission; the evidence licenses a specific one, not an arbitrary choice among them:

- **Removing M1 from the denominator to improve performance is explicitly not licensed** — this would be post hoc goalpost movement, and no sealed document argues for it.
- **M1 remains a documented impossible control under the current planted amplitude/geometry** — supported directly: the amplitude Theorem 1 targets is a property of the benchmark's own generative law, and the theory's own §21 prospective experiment (never executed, `PROSP`) is the only sealed path that could test whether the *identifiable* ~7–19% residual is practically reachable by a correctly-built statistic — no sealed result currently confirms this is achievable in practice (every genuinely descriptor-blind candidate measured exactly 0.0%, not ~19%).
- **The correct treatment is: M1 stays in raw benchmark reporting (RAW_RECOVERY_RATE, unaffected), but is excluded from any headline "uniquely recoverable sensitivity" claim that implicitly assumes the planted amplitude is fully identifiable** — because it is not, provably. This is not goalpost-moving because the exclusion is licensed by an exact algebraic proof about the *benchmark's own construction*, established *before* any M1 evaluation number was known, not selected after the fact to improve a score. The frozen scientific intent (a genuinely descriptor-blind adequacy statistic) is preserved; what changes is only the honesty of the claim made about M1's achievable ceiling.
- A residual-contrast evaluation of M1 (scoring against the theory's derived, identifiable-only ceiling rather than the full planted amplitude) remains a legitimate, not-yet-executed prospective option (`L-M1-02` §21) — but it requires new governance authorization and is not retroactively applicable to any already-sealed M1 number.

---

## PART V — M2

### The complete information-flow diagram

```
[1] Observations (6 energies, sigma=0.02/compound)
        | Fisher content bounded by aliasing rho(log_g,a_i): median 0.968-0.99+ (exact-response)
        v
[2] Null-nuisance fit (log_g, jointly optimized with a_i)          } PARAMETER ESTIMATION
        | VIF = 1/(1-rho^2) ~ 15.8-32                              } POWER: ~98% realized,
        v                                                          } efficiency_ratio ~1.0-1.2
[3] M2 parameter estimate a_i (closed-form WLS)                    } (near-CRLB-efficient)
        v
[4] LOEO held-out comparison (mae_alt vs mae_m0)      } FROZEN DETECTOR POWER: dominant loss.
        | P6 (exact): both MAEs share the SAME       } An oracle (zero-variance) estimator still
        | irreducible held-out noise floor            } has efficacy ~0 here (L-M2-05).
        v
[5] Practical-win margin (<=0.90x)  -- needs standardized separation nu>=0.48; measured ~0.14-0.15
        v
[6] Per-compound binary vote  -- discards continuous margin size (near-null-compound drag, P7 exact)
        v
[7] 20-of-30 independent-threshold aggregation  -- retention factor r^2=0.346 vs a pooled statistic
        v
[8] Case verdict: power_case = 0.0000 (measured, all 5 grids, L-M2-04)
```

**POOLED CONTINUOUS CASE-LEVEL POWER** is not a pipeline stage — it is an *alternative* decision rule applied to the identical stage-[1]–[3] information: summing per-compound efficient scores directly (no LOEO, no margin threshold, no independent vote) reaches **0.734 (production grid) / 0.824 (E-optimal grid)** power at the same 6 energies (`L-M2-05`).

### Reconciling the three headline statements

**They are not contradictory — they are three decision rules applied to identical information (`L-M2-06`, exact reconciliation):**

- "Pooling can exceed 0.80 power at six energies" (claim A) and "geometry cannot make the frozen detector fire" (claim B, `L-M2-04`, executed) differ by **decision architecture**, not information budget: same six energies, same Fisher content, different statistic.
- "Perfect parameter estimation cannot make the frozen detector pass" (the oracle ceiling 0.29–0.31 vs. required 0.72, `L-M2-05`) and claim B are the **same finding at two estimator-quality levels of the same architecture** — B is what the real estimator achieves (0.0000); the oracle ceiling is what a *hypothetically perfect* estimator achieves under the identical LOEO+margin+vote rule (0.29–0.31, still far below 0.72). This is exactly why M2GV1's five Fisher-optimal-vs-production grids all tied at *exactly* 0.0000 rather than differing slightly: geometry reduces variance (a stage-[2]–[3] quantity); the margin test is blind to that reduction because both its numerator and denominator share the same noise floor (a stage-[4]–[5] property, P6 exact).

### Where information is lost, quantified

- **Parameter estimation power**: already ~98% realized; OEG1's real 27–34% empirical variance gains translate to only a ~1.2× efficacy factor (`L-M2-01`, `L-M2-03`, `L-M2-04`) — far short of what closing the gap needs.
- **Frozen detector power** (decision-architecture loss): the dominant loss. The LOEO margin's shared-noise-floor mechanism (P6, exact) alone reduces even a perfect estimator's efficacy to ~0; the 20-of-30 independent-vote aggregation additionally requires a 3.5–4.7× larger per-compound efficacy than the design delivers.
- **Pooled continuous case-level power** recovers essentially the information stages [4]–[7] discard, using the identical budget — strong evidence the ceiling is architectural, not physical, for the dominant part of the gap (the pooled-power figures 0.734/0.824 are themselves `NUMDER`, not a formal proof; the genuinely exact result underneath them is P6's identity that both arms of the frozen margin share the same noise floor). A smaller, genuine Fisher-geometry ceiling (full-info, non-LOEO case power = 0.416 at 6 energies) remains even for a pooled test.

### The exact algebraic relationship, `d mu/d a_i` vs. `d mu/d mu_inf`

**Proven exact** (`L-M2-02`, P2, verified to `1.7e-10` against finite differences): `d(mu_ij)/d(a_i) = d(mu_ij)/d(mu_inf) = 1 - S(u_ij)`, identically, for every compound/energy/parameter value — an algebraic identity, not a linearized approximation. Consequence, also exact: the case-mean `mean_i(a_i - mu_inf)` is not identifiable at any noise level or estimator; only *centered* contrasts carry identifiable information. Because M2's planted deviation is constructed to be exactly centered, only ~2.4% of its mean-square lives in this unidentifiable common mode (vs. ~85–93% for M1's analogous mechanism) — the identity is exact, but its *practical* cost to M2 is small, unlike its dominant cost to M1.

### What should the next M2 study test?

**Neither A (descriptor-conditional pooling only) nor B (pooled case-level evidence only) alone, and not "another theorem closes the space" either — the evidence licenses a specific minimal design, not a menu:**

- **Descriptor-conditional pooling on the existing 6-energy budget is the only repair route the evidence supports as potentially licensable** — it needs *zero additional acquisition* (`L-M2-05`, `L-M2-07` [unsealed]), because the frozen architecture's information loss is decision-rule-driven, not physical.
- A **pooled continuous case-level statistic** (escaping LOEO+margin+per-compound-vote entirely) is the mechanism that actually closes the 0.30→0.73–0.82 gap in the exact algebra (`L-M2-06`) — but *replacing the decision rule itself* is a governance question (the same class of change the frozen decision tree gates at branch A.1(d)), not a parameter-estimation experiment.
- **Both should be tested together, with an oracle/negative-control reference arm**, because the (unsealed) information-scaling theory's own prediction — that 6 of M2R1's 13 registered shrinkage arms will be provably inert (`L-M2-07`, exact shrinkage-SNR-invariance identity) — means a bare re-run of M2R1 as currently designed would waste roughly half its arms on a class already shown, by exact algebra, to be unable to help. The minimal licensed design is a **pooled/descriptor-conditional estimator plus an oracle-ceiling reference arm**, evaluated against a **decision-architecture change** (pooled statistic) as the primary lever, not a parameter-estimator change as the primary lever.

**Is extra distinct-energy measurement still justified? No** — three independent lines converge (`L-M2-03` §7, `L-M2-05` T6, `L-M2-07` §7.1–7.2): 12 energies raise the *information ceiling* only from 0.416 to 0.523 while the frozen statistic's actual power stays near zero; under the frozen margin, **no finite N reaches 0.80 at all**; and the info-scaling theory measures the practical-win rate *falling* monotonically (0.305→0.173) as distinct energies increase from 6 to 24, because averaging away noise removes the spurious below-margin-by-luck wins that were propping the null rate up. **Replicating** the existing 6 energies (lowering `sigma_eff` at the held-out point) is the only acquisition-side lever that helps, at 30–44× the current budget — dwarfed by the zero-cost decision-rule change.

### M2 classification

**DECISION_RULE_LIMITED, dominant, with a secondary, smaller, already-~98%-realized INFORMATION_LIMITED (Fisher-geometry/aliasing) component.** This refines, not reverses, FI1's original INFORMATION_LIMITED label (`L-M2-09`): FI1 was correct that estimator variance headroom is essentially exhausted; "information-limited" undersells the finding because the dominant quantity limiting case power (the 0.30→0.73–0.82 gap) is a property of *which statistic and aggregation rule* is applied to that information, not of the information itself.

---

## PART VI — M3

### The complete causal chain

**(a) `log_g` localization error** — `L-M3-01`: REFUTED as a driver (`EMP-S`, not proof). At zero noise, `log_g` localizes to the dense-grid optimum within 5e-5 at every alpha, yet the target residual stays 0.036–0.058.

**(b) Phi profile-estimation error (Pathology 1)** — real but non-dominant for parameter bias, dominant for LOEO *predictive* power. SA1 (`L-M3-06`): decontamination recovers M3's LOEO power 1.3%→90.7%. PCL/A1PR (`L-M3-04`): no single component or architecture reaches 50% of the parameter-bias-adjacent gap. The Phi-bias theory reconciles this: Pathology 1 affects predictive power but "mostly no" effect on the parameter bias floor, because the floor is a common multiplicative gain that largely cancels in an M3-vs-M0 predictive ratio.

**(c) Finite-grid endpoint/asymptote error (Pathology 2, the floor)** — the newly-identified **dominant** mechanism. `L-M3-02` (exact, under idealization: perfect Phi, true g, zero noise): a finite-support normalization floor, matching **87–113%** of M3D1's own empirical zero-noise residual.

**(d) Parameter identifiability** — `L-M3-02` §3.2 (exact, cross-validated to 2 decimals against FI1's own independently-measured Fisher numbers) and §7.2 (exact impossibility theorem: identification of the plateau and orthogonality to `a_lo` are the *same* inner product, required to be both zero and nonzero). This is a *different, stronger* statement than M3D1's own GM5 (`log_g`↔target correlation, moderate 0.53) — the two concern different variable pairs and should not be conflated (`L-M3-07`).

**(e) Target-estimator bias** — `L-M3-01` GM7, CONFIRMED, 67.9% pooled share, now attributed 87–113% (at zero noise) to (c).

**(f) Decision-statistic behavior** — the frozen M3 decision does *not* read the biased parameter at all; it reads a leave-one-energy-out MAE ratio against M0. This is exactly why SA1's predictive-power story and M3D1's parameter-bias story "never reconciled" before this document: they measure different objects, and the floor — a common multiplicative gain — mostly cancels in the predictive ratio while dominating the parameter's own bias.

### 1. What caused the zero-noise residual?

Predominantly (c), the finite-support endpoint-normalization floor — proven to exist under idealization and empirically matching 87–113% of the measured residual, with a disclosed, unexplained non-monotone residual (`L-M3-03`).

### 2. What fraction can be explained by endpoint attenuation?

**87–113%** at zero noise (not 100% exactly at every alpha — the theory's own §6 discloses a non-monotone gap it does not yet explain).

### 3. Is generic Phi decontamination still justified?

**No, and this is now proven, not merely empirically discouraged.** `L-M3-04`: the impossibility theorem holds even at a *perfectly-estimated* Phi — no improvement to Phi-estimation quality, however sophisticated, can remove the `a_lo` channel or the finite-support floor, because the channel is a definitional consequence of `ProfileShape` measuring knot-grid endpoint evaluations, not an estimation-error channel. A 4th profile-estimator study is **CONTRA_INDICATED**, not merely unlicensed.

### 4. Is log_g optimization closed?

Yes — `L-M3-01`: log_g search mechanics (GM1/GM2/GM6) are refuted/near-zero-share as a cause, and `L-M3-05` (RC1) independently forecloses coordinate reparameterization of `(log_g, target)` as a repair (`NO_ARM_ADMISSIBLE`, worsens conditioning +109% and aliasing +63.8% on the one arm designed to attack it).

### 5. What exactly does the relative-plateau construction fix?

It targets a **different estimand** (the relative plateau `tau=(b-a_hi)/D`, not the absolute plateau `b`) via a Neyman-orthogonal semiparametric score with free case-level nuisances — this is structurally distinct from RC1's "orthogonalized" coordinate shear, despite the shared word (`L-M3-05` naming-collision note). It is designed to escape the §7.2 impossibility theorem, which is specific to the absolute-plateau estimand as literally coded.

### 6. Is the construction algebraically exact, first-order, or empirical?

**Mixed, and the theory's own labeling is honest about which parts are which** (`L-M3-02`/`L-M3-03`): the *mechanism* (existence, sign, target-proportionality of the floor) is exact under the stated idealization; the *87–113% dominance share* is a comparison of a proven quantity to an independently-measured empirical quantity, not itself part of the proof, and is not a 100%-exact account (disclosed non-monotone gap).

### 7. What variance cost is expected?

**~1.22×** (`L-M3-02` §7.7, a [NUMERIC] deterministic evaluation at nominal constants, not a measured-under-replication figure).

### 8. Does fixing parameter bias necessarily improve the actual detector?

**No, not automatically, and the theory is explicit about this** — per (f) above, the frozen M3 decision does not read `b_hat` at all. Fixing the parameter-level bias is a *different object* from fixing detector power; the two must be evaluated separately (see §5 below).

### 9. The smallest prospective experiment that could answer that

The theory names (does not run) a minimal design: a control arm (`A0`, production), two diagnostic-only isolator arms (`A1`/`A2`, non-adoptable, testing the floor's predicted magnitude in isolation), two candidate adoptable arms (`A4`/`A5`, the relative-plateau construction at increasing sophistication), and a non-adoptable coupling-sensitivity arm (`A6`). It reuses M3D1's own grid/seed/replicate structure. **Critically, before this can even be designed as a power-repair experiment, a decision-architecture question must be resolved first**: whether to (route A) add a new target-*contrast* decision statistic that actually reads the orthogonalized `tau_i` — itself an escalation to the adequacy statistic requiring its own preregistration and safety pass — or (route B) measure parameter recovery only, making no power claim. The frozen adoption rule already specified requires `bias_share_pathology2≥0.5`, zero-tolerance on the four named-direction gains under `A4`/`A5`, a power-Wilson-bound beat in ≥3 of 4 alphas, ≤1.5× variance penalty (the theory's own estimate has margin at 1.22×), and ≤0.05 false rejection. **Not executed here; execution requires separate authorization.**

---

## PART VII — Retention / E4a

*(E2's frozen routing gate is preserved throughout; nothing below inspects unfinished E2 scientific outcomes.)*

### 1. Exact mathematical definition of PySR score

Verified **independently against the actually-installed source** (`L-RET-01`), not merely cited: `score_j = -log(L_j/L_{j-1})/(c_j-c_{j-1})` for `j≥2` (`+inf` if `L_j=0`), `score_1=0`; the front is strictly loss-decreasing by PySR's own frontier-construction guarantee (`HallOfFame.jl`). Production retention is literally `argmax(score)` over this column.

### 2. Implicit complexity-price interpretation

`L-RET-02` (independently re-derived, not just quoted): under a Gaussian-likelihood/node-count-prior model, `argmax(score)` is exactly the MAP transition point at implicit price `beta_eff = (n/2)·max_j score_j` — the *largest* price at which anything beyond row 1 is retained. This is `PROVEN_UNDER_STATED_ASSUMPTIONS` (the modeling choice itself is not independently verified against real MURU loss distributions); the outcome-blind E2 interim's `score_complexity_correlation` (median −0.385) is weak, directional, non-conclusive corroboration of the front-monotonicity assumption Corollary 2.1 additionally needs.

### 3. Do R1, R3, R5 have identical downstream votes under the current resolver?

**Yes, conditional on one explicitly-stated, checkable caveat** (`L-RET-03`): no `valid_r2` ties at a seed's front maximum. Verified against the frozen protocol text and production `rc5_selection.group_and_select` directly. **Important caveat**: this is currently a sound design-time algebraic claim only — no E4a scoring implementation exists anywhere in the repository (confirmed by grep/glob across both retention worktrees), so it has not yet been code-verified against a real run; it is independently corroborated by the E2 interim characterization's own architecture-gap finding (McNemar/paired-comparison code is "NOT PRESENT" in the report scripts).

### 4. Is R3's conditional retention recall tautologically 1?

**Yes, exactly, with zero exceptions including `mass_saturating_descriptor`** (`L-RET-04`) — a tautology by set-membership construction (R3 retains every row of a front that, by the eligible-pool definition itself, must already contain a correct row). This corrects the preregistration's own PRR-1 text, which hedges this as a near-1 empirical finding with a family carve-out — a documentation imprecision, not a scientific disagreement.

### 5. The true EVAL denominator — 90 vs 36

**90 is correct; 36 is a propagated transcription error** in three frozen artifacts (`L-RET-05`), independently re-derived from the frozen population/split definition (9 (regime,noise) cells × 10 EVAL replicates). Non-blocking for the specific zero-events adoption screen the preregistration's own worked prediction assumes (both Wilson upper bounds clear the 0.15 ceiling), but a live wrong instruction that must be corrected before any real Wilson-interval computation uses it.

### 6. Classification of the found issues

| Issue | Classification |
|---|---|
| 36-vs-90 EVAL count | **Documentation-only** — pure arithmetic transcription, derivable and correctable from already-frozen definitions with zero E2a data |
| PRR-1/PRR-4's hedged phrasing of R3=1.0 | **Documentation-only** — imprecise prose, not a design defect |
| R1=R3=R5 vote identity (not stated explicitly) | **Not an issue** — a correct, derivable-but-unstated consequence of already-frozen text; worth adding as an explicit zero-cost self-consistency control |
| Missing E4a scoring/McNemar implementation | **Implementation gap**, a precondition never yet built, not a defect — expected given the design's own "EXECUTION NOT AUTHORIZED" status |
| Two unpatched `equivalence.py` defects (`L-RET-08`) | **Implementation error (upstream, inherited)** — real, confirmed, low-reachability-on-their-own-corpora, relevant to E4a's future stage C/D split and PRR-5, not blocking the primary A/B endpoint |

### F09's classification, precisely

`L-RET-06`: seed-level front-reach 15.00%, but **case-level (world) front-reach is 12/12 at every one of 8 arms**, while **`P_retain_given_front=0.0` exactly, zero exceptions**, across 306–330 correct-containing seeds. This reverses v1's own frozen `GENERATION` classification — the true first-loss stage, under the frozen A–E taxonomy, is **stage B (`LOST_IN_RETENTION`)**. No E4b/E4c/E4d change can move F09's real endpoint; the licensed next step is E4a specifically, not further search-side work.

The outcome-blind E2 interim (`L-RET-07`) provides only a *directional*, non-replicating cross-check (pipeline-wide median retention margin comfortably above F09's derived floor; 99.9% of argmax winners structurally distinct from the runner-up) — consistent with, not proof of, the mechanism, and explicitly cannot be checked against F09's own per-family counts since those fields are exactly what the blinding layer drops.

### What a results-blind amendment would need to fix — described only, none proposed for execution

1. Correct "36"→"90" in the three cited locations — derivable entirely from already-frozen definitions, requires zero E2a data, remains fully results-blind if made before E2a seals.
2. Build the missing E4a scoring implementation (R0–R6 within-seed retention, the vote-reduction function, McNemar/paired-bootstrap comparison) — a precondition for E4a to run at all, executable "immediately after E2a seals" per the frozen protocol, not before.
3. *(Optional, non-required)* Add the R1=R3=R5 identity as an explicit, zero-cost, pre-declared self-consistency control alongside the existing R0-replay control.
4. Flag, do not pre-emptively patch, the two unpatched `equivalence.py` defects as a residual risk specifically for E4a's stage C/D metrics and PRR-5 — patching would touch `src/muru/discovery/equivalence.py`, out of scope for a results-blind retention-only amendment.

**No E4a arm change, no threshold change, and no gate re-derivation is licensed by anything above.**

---

## PART VIII — The recoverability / denominator crisis

*(Highest priority, per the mission's own framing.)*

### The three distance/measure notions, kept explicitly separate

- **`REFERENCE_FUNCTION_SPACE_DISTANCE`** — SIM's uniform-product-measure L2 distance over the declared domain, zero-noise, infinite-precision. Used by Dimensions A and E of the frozen correctness/confidence SPEC.
- **`EXPECTED_DISTANCE_UNDER_BENCHMARK_DISTRIBUTION`** — AMCS-v2's realized-covariate-measure distance, computed on the actual sample the generator produces (correlated, sub-uniform-variance).
- **`OBSERVATIONAL_DISTINGUISHABILITY_UNDER_NOISE`** — E3's/E-STAB's noise-perturbed, finite-sample empirical oracle rate.

**Where the framework substitutes one for another** (`L-COR-01`): Dimension I's recoverable-denominator gate uses the *first* (a zero-noise structural label) as an entry criterion for a population later scored partly by the *third* (a noise/data-conditional rate). SIM's own §8 explains that Dimension A's zero-noise label and E3's empirical rate coincide for `aff`/`exp` only because their 0.62–1.13% structural minimum distance happens to sit at or below the 2% noise sd — a numerical coincidence at the frozen noise level, never disclosed by the SPEC/PROTOCOL text as noise-level-specific. This is not an error in either measurement, but it is a substitution the frozen text does not flag, and a reader could wrongly treat Dimension A's label as evidence about production-noise recoverability in general.

**A second, independent instance of the same substitution pattern** lives in **Dimension G** (the ambiguity trigger): it fires on "`ΔBIC≤2.0`" (`OBSERVATIONAL_DISTINGUISHABILITY_UNDER_NOISE`, a noise-conditional data-fit statistic) **OR** "`RelRMSE≤0.02`" (`REFERENCE_FUNCTION_SPACE_DISTANCE`, the same zero-noise uniform-LHC quantity Dimension E uses) — folded into one ambiguity-set predicate via a bare OR, with the SPEC never stating these measure different things. This is not a hypothetical concern: Dimension G's ambiguity-credit route is exactly the mechanism `SET_VALUED_ACCEPTABLE_RECOVERY`'s formula (below) invokes for every `MARGINAL`-classified pair.

**The single most severe substitution**: `REFERENCE_FUNCTION_SPACE_DISTANCE` (uniform) stands in for `EXPECTED_DISTANCE_UNDER_BENCHMARK_DISTRIBUTION` (realized) throughout the frozen SPEC, because the SPEC was frozen (`ab40112`) before AMCS-v2 ever computed the realized-measure figures (`b4d1678`, later). The SPEC is internally consistent with its own declared convention (§2.1 explicitly declares uniform) — the declared convention was simply never checked against the measure MURU's pipeline actually operates on, and it disagrees materially and denominator-flippingly for `mass_interaction` (DA5, `L-REC-02`). The correctness/confidence SPEC/PROTOCOL/SCHEMA files were never amended after this finding; only the separate recoverability-ceiling document was retroactively amended to carry the tension forward.

### RAW vs. positive-scale-quotiented functional error

**The frozen SPEC's Dimension E is the sole exception to the rest of the system's own already-declared invariance group.** Every other correctness mechanism in the codebase (`equivalence.py`'s docstring, `a34_predictive_equivalence.py`'s `c_star` refit, G1's scale-invariant `log g` rank correlation, and the SPEC's *own* §4 exact-equivalence oracle) commits to "equivalence up to a positive multiplicative constant." Dimension E computes RelRMSE **RAW** with no stated rationale (`L-COR-02`). (SIM's own Dimension A distance is a *related but not identical* case worth distinguishing precisely: it already minimizes over each family's own free `scale∈[1.1,1.8]` parameter — a form of scale quotienting — but *bounded to the authorized box* rather than fully unconstrained; AMCS-v2 independently checked that an unconstrained-scale version of the same distance reproduces SIM's box-constrained numbers to within 0.14–0.84% for the three descriptor-only pairs, but this closeness has not been separately verified for the interaction-involving pairs where DA5's much larger, cutoff-crossing swing lives. Dimension A's bounded convention is therefore a distinct, smaller-magnitude open question from Dimension E's RAW-vs-SCALED gap, not simply "already scale-quotiented, unlike E" — flagged here rather than left implicit.)

**The scientifically coherent invariance group, defined once**: **positive-multiplicative-scale-quotiented, as primary; RAW retained as a mandatory secondary diagnostic, never silently dropped.** This is justified by consistency with the rest of the system's own already-declared scientific convention (`g`, and any candidate law built from it, is identified only up to scale by design) — not by which reading raises the ceiling, though it happens to (118.61 vs. 61.63 cases, a 1.92× swing). RAW must be retained because it is exactly what surfaces F18's proven "safety trap" (a wrong-family candidate scoring 0.026–0.125% RelRMSE) — dropping RAW would hide a real, proof-backed hazard.

### Exact treatment of the named families/pairs

| Family/pair | Treatment | Basis |
|---|---|---|
| **F05 boundary regimes** | Same bucket as F01 in all four ceilings; `boundary_hit` expected empty (0/20,000 authorized-box worlds); any real firing = fitter false positive, never a benchmark property | `L-F05-01..05` |
| **F07** | Excluded from every symbolic-recovery denominator (proven, probability-0 representability); own `parameter_recovery` ceiling tracked separately at 1.000 — **this 1.000 is a tolerance-based match by a structurally wrong closed form (a pure `sqrt(mass)` or `mass^0.75`) against a true continuous exponent that lands there with probability 0, the same class of hazard as F18's safety trap; it is never folded into any of the four headline recovery-efficiency denominators, but must never be cited as evidence F07's true exponent was recovered** | `L-COR-10` |
| **F18** | Symbolic-recovery ceiling exactly 0.000 (proven transcendence), but *inside* the G2-144 denominator (unlike F07) — raw G2 rates must be reported against both 144 and 132; predictive/functional success alone must never be cited as F18 recovery evidence (proven safety trap) | `L-COR-11` |
| **mass_interaction (F10)** | **BLOCKING, unratified** (DA5): sole `UNIQUE_RECOVERY_CEILING` member (12.00 cases) under the uniform measure the SPEC declares; 0 cases / undefined under the realized measure AMCS-v2 computes, where `exp/int` contracts to 0.016226 (below the 0.020 cutoff) **and `aff/int` contracts to 0.0213 (essentially on the cutoff, a second near-miss under the same measure, not a clear second violation)** — directly tensioned against E3's fully-executed empirical finding that F10 is the *most* identifiable family | `L-REC-02` |
| **The 3 LOCALLY_WEAKLY_IDENTIFIABLE pairs** (aff/sat, aff/exp, sat/exp) | Excluded from the strict unique-recovery denominator; included via the ambiguity-credit route in `SET_VALUED_ACCEPTABLE_RECOVERY_CEILING`, where `P(truth∈A)` reaches 0.87–1.00 | `L-COR-07`, `L-REC-01` |
| aff/exp tangency-outside-box (`L-COR-12`) | Does **not** move any classification or in-box minimum distance; explains those figures are genuine box-conditional ceilings, settles they cannot be "fixed" by re-sampling within the frozen box | `L-COR-12` |

### Explicit denominator definitions (no dependence on MURU's own output)

```
RAW_RECOVERY_RATE
  = |{acceptable cases}| / 240                          [denominator: pure held-out case count]

MATHEMATICAL_RECOVERY_EFFICIENCY
  = Acceptable / 132.00                                 [denominator: pure proof+registry predicate:
                                                           excludes F07/F18 (proven unrepresentable);
                                                           structural recovery only, never exact
                                                           coefficient algebra (proven 0.000 everywhere)]

DATA_CONDITIONAL_RECOVERY_EFFICIENCY
  = Acceptable / 118.62                                 [denominator: closed-form re-aggregation of
                                                           sealed, results-blind E3 records at each
                                                           case's own noise sd + 6-pt grid; route-agnostic]

UNIQUE_RECOVERY_EFFICIENCY
  = Acceptable_Unique / {12.00 (uniform) | 0/undefined (realized)}   [BLOCKING on DA5 ratification]

SET_VALUED_ACCEPTABLE_RECOVERY
  = Acceptable / {118.61 (scale-quotiented, RECOMMENDED PRIMARY) | 61.63 (raw, SPEC's literal text)}
```

Every denominator above is built from `registry.py`/`generator.py` (static, truth-side), SIM's proofs/distances (closed-form truth functions, never a candidate), and E3's/E-STAB's closed-form-oracle fits against `g_hat` (the frozen, non-search `fit_case_scalars` estimator output — E3/E-STAB never invoke PySR/gplearn, confirmed). One precision worth stating exactly: "no dependence on MURU's own output" means no dependence on the **discovery/search engine's candidate output** — `g_hat` is produced by frozen MURU production code (`rc5_estimate.py`), and every definition above necessarily depends on that estimation pipeline, which is a different and much weaker claim than "no dependence on any MURU-authored code."

**Three items in this framework are currently blocking, unratified, and this reconciliation does not resolve them** (per the mission's own instruction not to force a resolution), matching the frozen recoverability-ceiling document's own count of "3 blocking disambiguations":

1. `UNIQUE_RECOVERY_CEILING` (DA5, the measure question: 12.00 vs. 0/undefined).
2. `SET_VALUED_ACCEPTABLE_RECOVERY_CEILING`'s scale convention (118.61 vs. 61.63, where this document *recommends* but does not unilaterally ratify the scaled reading).
3. **Dimension A's condition-number clause (`kappa<10⁴`)** — read as the *joint-pairwise* Jacobian, SIM's own LEMMA 2 (exact) proves `kappa` is infinite and *every* descriptor family becomes NONIDENTIFIABLE, collapsing the Dimension-A-gated ceiling structure toward zero — directly contradicting the frozen spec's own worked example (aff vs. exp at c≤0.25 ⇒ MARGINAL, not NONIDENTIFIABLE). Read as the *within-family* design Jacobian, the clause is satisfiable and matches the example; CRC measures `cond(J^TJ)=618–1,065` for all 11 families at nominal regimes (`L-REC-03`). The recoverability-ceiling document adopts the within-family reading as a working default (the only reading under which the clause is ever satisfiable) but explicitly flags it for ratification — this is arguably the **highest-leverage** unresolved item in the entire framework, since a ratification toward the joint-pairwise reading would collapse every Dimension-A-gated denominator, not just `UNIQUE_RECOVERY_CEILING`.

---

## PART IX — The g-grid reachability issue

**The exact relation, verified directly against production source** (`L-COR-04`):

- Declared adequacy bound: `LOG_G_BOUNDS=(-2.0,2.0)` → g∈[0.1353, 7.389].
- Actual `g_hat` estimator search grid (`rc5_estimate.fit_case_scalars`): `A35_LOG_G_GRID = linspace(-1.6,1.6,241)` → g∈[0.2019, 4.953] (refinement clipped to ±1 grid-step).
- A **second, separate** log_g estimator (used for the M0–M3 adequacy hypothesis tests themselves, a pre-existing v1 amendment) spans the *full* declared bound — the gap is specific to the `fit_case_scalars` pathway that feeds E3/M3D1/FI1/OEG1, not universal to every g-estimation code path.

1. **Is there an unreachable declared region?** Yes: g∈[0.1353,0.2019)∪(4.953,7.389] is representable to the adequacy model but unreachable to this specific estimator.
2. **Can nominal worlds enter it?** Partially — the recoverability ceiling's own 20,000-world authorized-box simulation realizes g up to 5.208, already past 4.953 in the sample's upper tail. **No sealed document quantifies the exact tail fraction** landing in the unreachable region specifically — a genuinely open, currently-unmeasured gap (`L-COR-05`), not answered here.
3. **Did sealed, executed studies actually sample truth values in it?** Yes, by construction — CRC's `PROFILE_BOUNDARY_LOW/HIGH` regimes deliberately targeted exactly this boundary (per the recoverability-ceiling doc's restatement; not independently re-opened from CRC's own source in this pass — flagged), and E0 independently established the same estimator/fitter-boundary-contact mechanism from a different direction (`L-COR-06`).
4. **Is this only a specification mismatch?** As characterized by every document read: currently a **disclosed specification gap**, newly named by AMCS-v2 (design-only, unexecuted), not yet shown operationally material at scale — F05's own registry-level trigger for this condition is empirically empty across the full authorized box.
5. **Does it require repair before E6?** Cannot be answered with confidence without the one measurement no sealed document supplies (item 2 above). This is named as a genuine open gap in the already-identified follow-up list, not a call to run anything.
6. **Does it invalidate any prior conclusion?** No. E3/FI1/OEG1/M3D1 all operate near the generator's default g, which lands in the estimator-grid gap only on an essentially-never (>4.5σ) event. CRC's own boundary findings already correctly attributed the pathology to the fitter ceiling, cross-validated by E0 independently.
7. **Does full impact assessment require unfinished E2 outcomes?** **No** — every source needed here is frozen source code, an already-sealed result, or a design-only, zero-instances-materialized specification. This reconciliation stopped at the boundary of CRC's own source document (out of assigned scope, unrelated to the E2 prohibition) rather than at any E2 boundary.

---

## PART X — F05

**Both halves of the mission's compound claim are true and fully reconcile, not in tension** (`L-F05-01..05`):

1. F05 has a mathematically valid, **proven** (Theorems 1–3, exact) finite-information-collapse boundary regime, empirically confirmed (142 cells, hostile-audited 9/9) — but only at constructed, out-of-box stress values (scale∈{0.05,0.12,0.35,3.5,6.0,10.0}, 1.9×–22× outside the authorized `U(1.1,1.8)`).
2. The nominal generator's authorized box never reaches those regimes — verified both by direct source inspection (F05's generative branch is byte-identical to F01's; the generator has no code path that can draw the pathological values) and by a 20,000-world Monte Carlo simulation over the full authorized box (0/20,000 compounds plateau, worst-world margin 4.6× the threshold).

**Classification: `ADVERSARIAL_STRESS_SCOPE` only — not `NOMINAL_BENCHMARK_SCOPE`, and not "both under different scopes" in the sense of the pathology being reachable in both.** It is reachable in exactly one (the constructed stress box) and provably/empirically absent from the other. A reader of the F05 diagnosis study *alone* could wrongly conclude this is a live production risk — that study's own scope never claims otherwise, it simply never states the regimes are out-of-box; the recoverability-ceiling document is the one that closes this gap explicitly. Any real F05 `boundary_hit` observed in the actual 240-case evaluation should be attributed to the fitter's `MU_CEIL`, per E0 (independently corroborating mechanism), never to a genuine benchmark-side plateau.

---

## PART XI — E6

### Does E6's current draft remain valid?

**No single item invalidates E6's design content, but its self-reported freeze status is factually wrong, and one core dependency (`n_rec≥320`) is not yet checked against the reconciled denominator — both must be fixed before any freeze.**

- **`L-E6-01/02` (verified by direct git inspection, not inferred): E6 is NOT frozen.** The four core documents and `scripts/e6_design/` are untracked; no commit anywhere contains them; the manifest's own provenance fields are unfilled placeholders. The document's self-declared `Status: FROZEN_DESIGN_ONLY` and stated freeze-parent commit are **incorrect as of this reconciliation**. Positive finding: the design content itself is internally consistent, and its "no production code touched"/frozen-source-hash claims are independently verified true.
- **`R=42/family, N=840, n_rec≥320`, the 0.90 vs. 0.95 hypothesis, the per-family floor, E6-S/E6-R, truth-side adequacy, ambiguity accounting** (`L-E6-03..08`): all internally self-consistent and each traceable to a specific upstream sealed study — **except one load-bearing gap**. `n_rec≥320` is derived from **pure binomial-power arithmetic** (the smallest n surviving a plausible worst-case retention fraction `rho` at R=42), **not anchored to any already-measured recoverable-denominator value**. The recoverability-ceiling document's four sealed ceilings (132.00/118.62/12.00/118.61-or-61.63, `L-REC-01`) are framed against a **different, 240-case v1-scale population** — not unit-compatible with E6's fresh 840-case/462-representable-symbolic framing without an explicit translation this reconciliation does not have license to perform (E6's own population is prospective and un-generated; no sealed study has run E3/E-STAB-style oracle measurements against it). **This is a genuine, currently-unresolved dependency, not a defect — it must be explicitly checked, not assumed transferable, before E6 executes.**
- **E6-S/E6-R re-scoping** (`L-E6-05`): a disclosed, reasoned expansion from the original per-candidate-change register into a single-shot terminal exam. Legitimate, but every *other* repair-lane preregistration written against the original conception (e.g. the retention-remediation prereg's own "a change failing E6 is not adopted" clause) should be confirmed compatible with the new single-shot mechanism before freeze — a bookkeeping check, not a scientific one.
- **A practical blocker independent of both of the above**: as of this reconciliation, essentially every M1/M2/M3 diagnosis/repair study returned `NO_ARM_ADMISSIBLE`/`NO_..._LICENSED` (M1CD, M1R1, A1PR, PCL, M2GV1, RC1 — see Part XIII). **There may currently be no concrete `C_impl` repair candidate for E6 to run against at all.** This is a scope observation for governance, not a defect in E6's own design.

### Should E6 be frozen now?

**No — do not freeze the current E6 draft as-is.** Not because its statistical design is wrong, but because (a) it is not actually committed to git despite claiming to be, and (b) its central adjudicability floor (`n_rec≥320`) has an explicitly-acknowledged-by-the-document-itself dependency on a truth-side retention fraction that no sealed study currently measures against E6's own population. Freezing a document that already believes itself frozen, without correcting either fact, would compound rather than resolve the ambiguity the mission asked this reconciliation to close.

### Exact changes needed (preserving the design's strong parts)

**Preserve unchanged**: family-stratified protection against Simpson's paradox (the P2/P3 joint gate, quantified via the 200,000-replicate Monte Carlo), RAW→SEALED→ANALYSIS lifecycle, cryptographic manifests, prospective partitions, truth-side denominator definitions (Deviation D-1's `Adq*`), safety vetoes (E6-S, unmodified from the original register), first-loss accounting.

**Required before freeze**:
1. **Commit the four E6 documents and `scripts/e6_design/`** to a named branch, fill the manifest's `protocol_freeze_commit`/`protocol_document_sha256` fields, and only then treat the document as frozen — a mechanical, non-scientific fix.
2. **Explicitly check `n_rec≥320`'s adjudicability against E6's own (not the v1-scale) population**, once such a check becomes possible (i.e., not by importing the 240-case ceiling numbers directly) — flag this dependency in the document itself rather than leaving it implicit.
3. **Confirm every dependent repair-lane's own preregistration is compatible with the single-shot E6-S/E6-R re-scoping.**
4. **Resolve, or explicitly carry forward as a pre-declared open item, DA5 and the Dimension E scale convention** (Part VIII) before E6-R's endpoint 6.1 (recovery efficiency) can report a single number rather than two disputed ones.

### What should final headline claims be based on?

**A hierarchy, not a single number, and not a headline invented to hit a historically-desired 95%:**

1. **Primary**: `DATA_CONDITIONAL_RECOVERY_EFFICIENCY` (denominator 118.62-equivalent, translated to E6's own population) — the honest, noise-and-grid-conditional recoverable set.
2. **Secondary, always reported alongside**: `SET_VALUED_ACCEPTABLE_RECOVERY` (with both scale-quotiented and raw readings shown, per Part VIII, until DA5's sibling disambiguation is ratified) and per-family recovery (the Simpson's-paradox-safe view).
3. **Structural recovery**, reported separately from functional/predictive recovery, with F18's proven safety trap disclosed by name wherever functional/predictive numbers are cited.
4. **`UNIQUE_RECOVERY_EFFICIENCY` reported only once DA5 is ratified** — reporting it as a single number today would silently pick a side in an unresolved, denominator-flipping tension.

**Is the current 95% objective still mathematically meaningful?** As a *statistical alternative* in E6's hypothesis test (`pi_1=0.95` vs. `H0: pi≤0.90`), yes — it is pure binomial-power arithmetic, self-consistent regardless of the denominator debate. As an *implicit claim about what fraction of the 240-case (or E6's 462-case) population is recoverable in an absolute sense*, **no** — it was never checked against the reconciled denominators this document derives, several of which (UNIQUE at 12/240 = 5%, or 0/undefined under DA5's realized reading) are nowhere near 95%, while others (DATA_CONDITIONAL at 118.62/144 = 82.4% of the G2 population) are closer but still short. The 95% figure should survive only as E6's *hypothesis-test alternative*, explicitly decoupled from any claim that 95% of cases are recoverable.
