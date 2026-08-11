# PHASE1_DECISION.md

# RESTRICT AND GO TO PHASE 2

Generated 2026-08-11 23:18 UTC. Phase 1 of MURU ConjectureLab v1.

---

## The restriction, in one paragraph

All three Phase 1 kill criteria are cleared and the corpus is cleaner than the master plan assumed. The verdict is **RESTRICT** rather than an unqualified GO for three measured reasons, each of which narrows what Phase 2 may claim rather than whether it may run: (1) the energy response of the primary endpoint carries a large and growing association with precursor mass (Spearman -0.10 at NCE 15 to -0.68 at NCE 90), so the mass-only baseline B2 is the real competitor and kill criterion K5 is live before any model is fitted; (2) repeatability was measured only in positive mode and only as an inter-mixture upper bound, so negative-mode noise is **UNKNOWN**; (3) survival yield is unusable as a continuous response above NCE 30 (85.3% of NCE 90 records sit at exactly zero), which caps any survival-based claim regardless of endpoint choice.

---

## Acceptance criteria (master plan section 20)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | >= 400 compound-by-mode groups with >= 5 of 6 energies, positive mode | **PASS** | 549 groups |
| 2 | CE semantics documented; zero ambiguous or out-of-set values silently retained | **PASS** | 0 of 5,582 records outside {15,30,45,60,75,90}; every record carries `energy_type=NCE_ASSUMED_FROM_PUBLICATION` with a provenance string; `CE_AUDIT.md` |
| 3 | Repeatability estimate delivered, or documented impossibility with the consequence for H-MAIN stated | **PASS (restricted)** | inter-mixture SD for mu = 0.0295 from mixes [499, 503, 505], positive mode only; negative mode UNKNOWN; `REPEATABILITY.md` |
| 4 | At least one endpoint monotone in >= 70% of trajectories with within-compound range exceeding replicate SD by >= 3x | **PASS** | mu: 84.5% monotone, range/SD = 15.2x |
| 5 | Preprocessing-branch disagreement quantified for every candidate endpoint | **PASS** | 12-cell grid + curated-vs-raw comparison; `ENDPOINT_SCREEN.md`, `REPEATABILITY.md` |
| 6 | `PHASE1_DECISION.md` states GO or STOP with numbered evidence | **PASS** | this document |

## Kill criteria

### K1 — Insufficient usable compounds: **DOES NOT FIRE**

*Trigger:* fewer than 250 positive-mode groups with >= 5 of 6 energies after quality filtering.

- Positive-mode groups with >= 5 energies: **549**
- Positive-mode groups with all 6: **517**
- Compounds excluded on identity grounds: **0**
- Margin over trigger: 299 groups (2.2x)

### K2 — Collision energy semantics unresolvable: **DOES NOT FIRE**

*Trigger:* more than 5% of records carry energy values that cannot be assigned a convention, or evidence that the six settings were not applied as documented.

- Records outside the expected set: **0 (0.000%)** vs a 5% trigger
- Records where the accession slot disagrees with the energy field: **0**
- Six-setting design confirmed in the publication text: **yes** (verbatim quote in `CE_AUDIT.md`)
- Residual ambiguity: the *unit*, not the value. Documented, provenance-tracked, and confined to derived E_lab/E_com columns that no Phase 1 conclusion uses.

### K3 — Signal below noise: **DOES NOT FIRE**

*Trigger:* within-compound endpoint range fails to exceed replicate SD by >= 3x **for every** candidate endpoint.

| Endpoint | median within-compound range (raw branch) | inter-mixture SD | ratio | clears 3x |
|---|---|---|---|---|
| mu | 0.4489 | 0.0295 | **15.2x** | yes |
| survival_yield | 0.6174 | 0.0337 | **18.3x** | yes |
| fragment_depth | 0.2995 | 0.0410 | **7.3x** | yes |
| spectral_entropy | 1.5238 | 0.1427 | **10.7x** | yes |

4 of 4 endpoints clear the bar; the criterion requires failure for all of them. Highest ratio: **survival_yield** at **18.3x**; mu at **15.2x**.

**This ratio does not choose the endpoint.** Survival yield scores highly because it collapses from ~0.62 to exactly zero -- a wide excursion produced by censoring, not by resolving power. K3 asks only whether signal exceeds noise; endpoint selection is made on the full criterion set in `ENDPOINT_SCREEN.md`.

**Caveat carried forward:** the noise estimate is an *upper bound* (inter-mixture, not injection-replicate), so these ratios are conservative -- the true margin over technical noise is larger, not smaller. See `PROPOSED_DEVIATION_FROM_MASTER_PLAN.md` D6.

---

## The fourteen questions

**1. What dataset do we actually have?**

MassBank LCSB records at release `2026.03`, commit `705afb7bccc3b2c42410a744eef73674716a60ef`: **5,582 records**, 25,501,603 bytes, corpus digest `27f6499ec4672191039e91df78115e3d...`. Energy-resolved HCD MS/MS of ENTACT mixture compounds on one Q Exactive Orbitrap at resolution 17500, six nominal collision energies, two adducts ([M+H]+ 3,411, [M-H]- 2,171), one confidence class, 781 unique compounds. Counts reconcile with the publication to within 0.34% (see `DATA_CENSUS.md`). Plus **3 raw mzML mixes** in positive mode from MassIVE MSV000091754, campaign 20200303.

**2. How many usable positive-mode trajectories remain?**

**549** with >= 5 of 6 energies; **517** complete six-energy trajectories; 588 groups in total. No compound is excluded on identity grounds.

**3. How many usable negative-mode trajectories remain?**

**349** with >= 5 of 6 energies; **330** complete; 379 groups in total. Census only -- deep negative-mode analysis is deferred per master plan section 20.

**4. Are collision energy semantics sufficiently resolved?**

**Yes for the value; qualified for the unit.** Every one of the 5,582 records carries an integer from the documented set, cross-validated against the independent accession-slot encoding with zero disagreement, and every precursor is singly charged so the Thermo charge factor never varies. The unit is *not* stated in any record; it comes from the publication, which calls it "nominal collision energy (NCE)" and never says "normalized". MURU stores this as an assumption with provenance rather than a fact. Since Phase 1 uses NCE itself as the energy axis and treats E_lab/E_com as descriptive, nothing downstream depends on resolving it. **A1: SUPPORTED, not VERIFIED.**

**5. What is the measured repeatability?**

Inter-mixture SD, positive mode, raw mzML branch, mixes [499, 503, 505]: **mu 0.0295**, survival yield 0.0337, fragment depth 0.0410, spectral entropy 0.1427. This is an **upper bound** on technical repeatability because the three mixes differ in matrix complexity (95 / 185 / 365 substances). Negative-mode repeatability is **UNKNOWN**.

**6. How large is the RMassBank versus raw-processing disagreement?**

Large, and very unequal across endpoints. Median peak count is 62 raw against 24 curated. Mean absolute difference: **mu 0.0194** (0.66x its replicate SD -- *smaller* than the measurement's own noise) versus **spectral entropy 0.3105** (2.2x its replicate SD). The formula filter substantially determines entropy and barely touches mu. This is risk R1 measured, and it is the strongest single argument for mu.

**7. Which endpoint is now primary, and why?**

**mu**, the intensity-weighted normalized spectrum mass. On 517 complete positive-mode trajectories it is strictly monotone in **84.5%** (vs 27.9% for entropy), has the largest within-compound range relative to inter-mixture noise (**15.2x**), has 0% missingness, keeps resolving power across the whole grid where survival yield dies by NCE 45, survives the formula-filter branch change within its own noise, shows no significant mixture-identity effect at any energy, and decomposes exactly into survival and fragment depth. The choice follows the measured evidence; the master plan's recommendation was treated as hypothesis A13 and independently re-tested at 517 trajectories rather than 56.

**8. Which endpoints were rejected, and why?**

- **spectral entropy** -- rejected as primary. Monotone in only 27.9%; Spearman rho against peak count rises to **+0.89**, and peak count here is set by RMassBank's annotator, not the detector; branch disagreement is 2.2x its own replicate SD; shows significant mixture-identity effects at 4 of 6 energies. Retained as a robustness endpoint only.
- **survival yield** -- retained but demoted to censored secondary. Weakly monotone in 95.4% but strictly monotone in 20.1% because it ties at exactly zero. 85.3% of NCE 90 records are at zero.
- **fragment depth** -- retained as secondary; monotone 67.1%, ratio 7.3x, undefined for precursor-only spectra.
- **normalized entropy** -- diagnostic only.
- **base-peak fraction** -- rejected; monotone in ~9%.
- **peak count** -- covariate only; range/SD below 1.

**9. Does the collision-energy response exceed measurement noise?**

**Yes, by a wide margin, for mu.** Median within-compound range is 15.2x the inter-mixture SD, against a 3x bar, using a noise estimate that is deliberately inflated. Three further endpoints also clear it.

**10. What important confounders were found?**

Four, in descending order of consequence:

1. **Precursor mass, for mu.** Spearman rho moves from -0.10 at NCE 15 to **-0.68** at NCE 90. mu is already normalized by precursor m/z, so this is *residual* mass dependence. Risk R4 fires before any modelling; kill criterion K5 is live.
2. **Peak count, for entropy.** rho +0.75 to **+0.89**. Decisive against entropy.
3. **Abundance (log TIC), at low energy.** rho(mu, log TIC) = +0.53 at NCE 15, decaying to +0.02 by NCE 75.
4. **Retention time.** |rho| up to 0.36 for mu, partly real chemistry and partly co-elution; NC7 must separate them.

**Mixture identity does not confound mu** (Kruskal-Wallis p > 0.05 at every energy) but does confound entropy (p < 0.05 at 4 of 6 energies).

**11. Which assumptions in the master plan were confirmed?**

| # | Assumption | Outcome |
|---|---|---|
| A2 | Records contain only formula-assignable peaks | **CONFIRMED** — raw branch carries ~10x more peaks |
| A3 | Accession slot convention holds corpus-wide | **CONFIRMED** — 0 violations in 5,582 |
| A4 | Only [M+H]+ and [M-H]- appear | **CONFIRMED** |
| A5 | All precursors singly charged | **CONFIRMED** |
| A6 | Precursor peak retained when detected | **CONFIRMED** |
| A7 | Mixes 499/503/505 share a replicate set | **CONFIRMED**, 92 compounds (plan said ~95) |
| A8 | MassIVE filenames map to mix/mode/NCE | **CONFIRMED** — plan had this UNKNOWN; risk R13 does not materialise |
| A9 | CH$SMILES chemically correct | **CONFIRMED** — all 5,582 regenerate their recorded InChIKey exactly |
| A10 | RESOLUTION 17500 constant | **CONFIRMED** |
| A12 | >= 400 positive groups with >= 5 energies | **CONFIRMED** — 549 |
| A13 | mu's superiority holds at full n | **CONFIRMED** at 517 trajectories |

**12. Which were contradicted?**

| Claim | Master plan | Measured | Severity |
|---|---|---|---|
| `mu = SY + (1-SY)*phi` holds to floating point | stated as an identity | fails on 10,588 rows at up to 5.9e-6; the exact form with the observed/declared mass ratio holds to 4.4e-16 | IMPORTANT (D1) |
| Curated layer has zero duplicate InChIKeys | "VERIFIED" on 373 records | 6 of 967 compound-by-mode keys map to two internal IDs | MINOR (D3) |
| E_com spread under 13% across the mass range | from a 151-526 m/z sample | larger at full corpus mass range | MINOR (D2) |
| "Roughly 95 compounds injected three times" | replicate framing | 92 compounds, and they are three different mixture preparations at three matrix complexities, not injection replicates | IMPORTANT (D6) |
| Technical replicates available | listed as FAILED in section 3.3 | correct for the curated layer, but obtainable from raw mzML as planned | — |

**13. Which remain unknown?**

- **Negative-mode repeatability.** Only positive-mode mzML was acquired. UNKNOWN.
- **True technical (injection) repeatability.** Bounded above by the inter-mixture estimate (0.0295 for mu) and below by within-run scan variability. Not separated.
- **Whether the NCE unit is 'nominal' or 'normalized'.** Immaterial to Phase 1; matters for any cross-instrument work.
- **Whether formula-annotation success depends on collision energy** in a way that biases trajectory shape. Peak counts rise with energy in both branches, but the branch-difference-versus-energy interaction was not modelled.
- **Whether the mass association in mu is chemistry or artifact.** Requires the Phase 2 descriptor ablation (F8).
- **A14, mixture identity as a confounder of trajectory *shape*.** Tested here at fixed energy only; the full NC6 test is Phase 2 work.

**14. Is Phase 2 scientifically authorized?**

**Yes, with the restrictions above.** K1, K2 and K3 are all cleared with margin; every acceptance criterion passes; the primary endpoint is chosen on measured evidence rather than inherited from the plan; and the two mechanisms most likely to have made the whole exercise an artifact -- the formula filter (R1) and preprocessing choice (R8) -- were measured and found not to move mu beyond its own noise.

Phase 2 is authorized **subject to** the following being carried in as binding, not optional:

1. The mass-only baseline **B2 is the primary competitor**, not a formality. K5 must be evaluated before any structure claim.
2. No negative-mode claim may assert a noise floor until negative-mode repeatability is measured.
3. Survival yield may not be used as a continuous response above NCE 30.
4. Every headline result must be reported under both preprocessing branches, since the branch gap for entropy exceeds its replicate SD by an order of magnitude.
5. H-MAIN's "residual within measurement repeatability" clause must use the inter-mixture bound and state that it is an upper bound.

---

## What this is not

Phase 1 established that a dataset exists, that its metadata are what they claim to be, that one endpoint moves with collision energy by more than the measurement varies, and that this survives a change of preprocessing branch. That is a data audit. It is not a discovery, it is not novel, and the underlying qualitative relationship (fragmentation increases with collision energy) is published. On the master plan's claims ladder this supports **L0 (pipeline verified)** and provides the measurements L1 will need; it does not itself establish L1, which requires out-of-sample comparison that Phase 1 deliberately did not perform.
