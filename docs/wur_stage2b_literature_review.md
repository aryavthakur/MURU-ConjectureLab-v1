# Stage 2B literature review: prior art for the candidate axes

Compiled 2026-09-12 by an independent literature-review agent from PubMed,
Consensus and web search, before any Stage 2B candidate was fitted. DOIs
and PMIDs were returned by the tools unless marked "unverified". Items the
agent could not verify are listed at the end and are not cited as
precedent.

## Compact fragmentation-extent summaries vs collision energy

- Kertesz, Hall, Hill, Grant (2009) JASMS 20:1759, PMID 19616966,
  doi:10.1016/j.jasms.2009.06.002. CE50 from survival-yield curves, regressed
  on Molconn topological descriptors for 54 compounds; reported as
  orthogonal to compound mass. The closest precedent to a descriptor law
  for a per-compound energy scale.
- Yevdokimov et al. (2026) Molecules 31:370, PMID 41599418,
  doi:10.3390/molecules31020370. Near-continuous NCE ramps, four-parameter
  logistic breakdown fits (FR50, Hill slope), breakdown energy dependence
  on ion population and injection time.
- Kuki et al. (2013) JASMS 24:1064, PMID 23661424,
  doi:10.1007/s13361-013-0635-8. Survival-yield curves fitted with an RRK
  model; effective degrees of freedom about one fifth of the total.
- Cao et al. (2019) J Chromatogr A 1609:460515, PMID 31522803; Guan et al.
  (2021) Anal Chem 93:15381, PMID 34775745. Optimal collision energy per
  fragment as a molecular descriptor.
- Cho et al. (2021) Anal Chim Acta 1149:338210, PMID 33551064. Orbitrap
  ID-X "assisted CE" using remaining-precursor thresholds on the fly.
- Li, Kind, Folz, Vaniya, Mehta, Fiehn (2021) Nat Methods 18:1524,
  PMID 34857935, doi:10.1038/s41592-021-01331-z. Spectral entropy rises
  monotonically with CE; normalised entropy above 0.8 flags poor spectra.

No precedent was found for the intensity-weighted mean fragment m/z
normalised by precursor m/z (this project's mu) as a survival statistic.

## Molecular properties and fragmentation energy

- Laskin and Futrell (2003) Mass Spectrom Rev 22:158, PMID 12838543;
  (2005) 24:135, PMID 15389858. Degrees-of-freedom effect and kinetic shift.
- Rubino (2020) Molecules 25:2250, PMID 32397650. Centre-of-mass conversion.
- Haller, Mirza, Chait (1996) JASMS 7:677, PMID 24203483. Optimal CE linear
  in m/z, the origin of rolling collision energy.
- Thermo NCE formula, from Révész group J Proteome Res 2022,
  doi:10.1021/acs.jproteome.2c00519: CE(eV) = NCE x (m/z)/500 x charge
  factor. The same paper states that Orbitrap models differ even in NCE
  terms. Because NCE is already affine in m/z, a law g proportional to
  precursor m/z on NCE-labelled data partly absorbs the instrument's own
  normalisation.
- Bremer et al. (2022) JCIM 62:4049, PMID 36043939; King et al. (2022)
  JCIM 62:3724, PMID 35905451. CE matching matters for in-silico tools;
  spectra can be interpolated across CE from few energies.

## Cross-instrument NCE comparability

- Szabó et al. (2020) J Mass Spectrom 56:e4693, PMID 33277714; Nagy et al.
  (2025) JASMS 36:299, PMID 39803703; Oberacher et al. (2018) Metabolites
  9:3, PMID 30583579. Affine eV-to-NCE equivalences across vendors.

No published Q Exactive to IQ-X NCE map for small molecules was found; the
Stage 1 affine map is new in that specific sense.

## Modelling energy-resolved trajectories

- Sigmoid / logistic breakdown fits (Kertesz 2009, Yevdokimov 2026), RRK
  kinetic fits (Kuki 2013).
- Functional data analysis registration with a shared shape and per-unit
  warping: Ramsay and Li (1998) JRSS-B 60:351 (DOI unverified); Carroll,
  Müller, Kneip (2018) Biometrics, cross-component registration
  (shift-warping, one parameter per unit).

No precedent was found for an explicit scaling collapse mu_i(E) = Phi(E/g_i)
in MS, for isotonic breakdown fits, or for mixed-effects CE-curve models.

## Validation and abstention

- MassSpecGym (Bushuiev et al. 2024, arXiv 2410.23326): MCES-distance folds,
  stricter than Murcko scaffolds. Fooladi et al. (2025) JCIM 65:9871,
  PMID 40947919: Bemis-Murcko splits are close to random splits for many
  MS models; cluster splits are the hard case.
- Hoffmann et al. (2022) Nat Biotechnol 40:411, PMID 34650271 (COSMIC):
  calibrated confidence with controlled abstention.

## Symbolic regression in analytical chemistry

No precedent for symbolic regression applied to MS/MS fragmentation or
collision energy was found; nearest is Lou et al. (2026) Adv Sci on TLC
retention (DOI not returned).

## Summary

| Idea | Precedent | Best citation |
|---|---|---|
| Survival yield / CE50 as descriptor | established | Kertesz 2009 |
| Descriptor regression for CE50 | partial | Kertesz 2009 |
| mu (this project) | none found | nearest: survival yield |
| Spectral entropy vs CE | established | Li 2021 |
| Logistic breakdown fits | established | Yevdokimov 2026 |
| DOF / kinetic shift | established | Laskin and Futrell 2003 |
| Affine cross-vendor CE map | established | Szabó 2020, Oberacher 2018 |
| Orbitrap-to-Orbitrap NCE map | none found | nearest: Nagy 2025 |
| Shared shape + per-compound scale | none in MS; FDA template | Carroll 2018 |
| Scaffold-disjoint validation | established, and known weak | Fooladi 2025 |
| Abstention with calibrated confidence | established | Hoffmann 2022 |
| Symbolic regression from spectra | none found | |

Unverified by the agent: Ramsay and Li DOI, Srivastava 2011 arXiv id, Makke
and Chenna review DOI, PySR arXiv id, Nguyen 2024 DOI, the ICEBERG
scaffold-split claim, the Révész 2023 review wording (paywalled).
