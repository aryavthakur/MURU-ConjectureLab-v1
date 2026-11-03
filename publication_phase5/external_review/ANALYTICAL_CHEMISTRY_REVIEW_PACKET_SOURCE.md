# Analytical chemistry review packet: MURU-WUR-v2 energy interface

**Purpose.** This source document is prepared for optional review by an external analytical chemist or mass-spectrometry instrument specialist. It presents the exact evidence and unresolved questions concerning the energy coordinate used in MURU-WUR-v2. It is not a request already sent to a reviewer, not an expert opinion, and not a human peer review.

## Study question requiring adjudication

MURU-WUR-v2 predicts a scalar fragmentation-extent trajectory from molecular structure. The trajectory is evaluated at a frozen numerical energy coordinate inherited from WUR/LCSB development. The evaluation compares the frozen MURU candidate and a frozen Tier A reference on selected external spectra whose numeric collision-energy values are 20 and 60. The central physical question is whether those values and the development values denote compatible collision-energy settings across the specific historical Thermo Orbitrap IQ-X and ID-X acquisitions. The computational comparison is fixed; physical compatibility is not established.

## What the records establish

### WUR source and records

- The WUR source library publication reports an HCD ladder of normalized collision-energy settings 15, 30, 45, 60, 75, and 90, plus stepped collision-energy settings 25, 38, and 59. Citation: Padilla-González et al., *Analytical Chemistry* (2025), DOI [10.1021/acs.analchem.5c03020](https://doi.org/10.1021/acs.analchem.5c03020).
- Local acquisition metadata identifies Orbitrap IQ-X HCD; filter strings include `@hcd15.00`.
- The generic MassBank `AC$MASS_SPECTROMETRY: COLLISION_ENERGY` record field carries a numeric value without unit/convention metadata. In `src/muru/energy.py::parse_collision_energy`, a bare value is retained with `unit=None`, status `NO_UNIT_IN_RECORD`, and type `NCE_ASSUMED_FROM_PUBLICATION`. The source paper/context supplies the interpretation; the field itself does not.
- The Phase 4 manuscript §2.6 currently overstates this by saying “WUR development records label” HCD settings NCE and stepped settings SCE. Recommended distinction: the publication/acquisition context identifies the convention; the generic exported field is unitless.

### MSnLib source and selected evaluation records

- The Phase 4 and frozen project protocols identify the evaluation rungs as HCD NCE 20 and 60. `src/muru/wur_v2/external_msnlib.py` defines numeric `RUNGS=(20.0,60.0)` and chooses MS2 scans by matching the header's numeric `collision_energy` value to 20/60 and by scan sequence position. This code does not parse a unit-type field or infer physical NCE/eV semantics.
- The evaluation frame was constructed from nine positive-mode mzML ZIP sources. See `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` §6, `src/muru/wur_v2/msnlib_design.py::ZIPS`, and `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv`.
- The primary MSnLib paper reports flow-injection MSn on a Thermo Orbitrap ID-X and says its MS2 energies were 20 eV and 60 eV, with assisted energy in 15 eV increments: Brungs et al., *Nature Methods* 22, 2028–2031 (2025), DOI [10.1038/s41592-025-02813-0](https://doi.org/10.1038/s41592-025-02813-0).
- Thermo ID-X Method Editor documentation says HCD may use normalized collision energy set as a percentage or absolute accelerating voltage set in volts: [official documentation](https://docs.thermofisher.com/r/Orbitrap-ID-X-Method-Editor-Help/2912190859v1en-US2912274187). It proves both modes exist; it does not identify the mode for each sampled archive.
- No archive-specific native method file, acquisition log, or instrument export establishing the energy mode for all nine sampled ZIP sources was found among the accessible frozen records reviewed for this packet. Thus the primary-paper method and the project protocol use incompatible unit labels, and file-level semantics remain unresolved. Do not claim that the selected external values are certainly NCE, or certainly eV, until the exact source archives are tied to method evidence.

### Frozen coordinate transforms

The fixed map parameters are (a=-5.95552603907965) and (b=0.8618030610784555).

- In development, an LCSB nominal coordinate (E) is mapped to a WUR nominal coordinate (T(E)=a+bE). WUR observations are interpolated at (T(E)). Evidence: `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` §2; `src/muru/wur_v2/population.py` module docstring/`build`; `src/muru/wur_bridge.py::apply_energy_map`.
- In the external evaluation, numeric rung (c) is mapped back to model coordinate (E=(c-a)/b). Evidence: `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` §2; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md` §3; `src/muru/wur_v2/external_msnlib.py::adapter_energy`.
- The transform is frozen and uses zero parameters fit to the external outcome. It is an empirical computational bridge; no committed derivation makes it a physical conversion to eV or deposited internal energy.
- Phase 4 wording “WUR-to-LCSB development bridge used T(E)” reverses or obscures the forward direction; for clarity, describe development as LCSB→WUR via (T), with external input using (T^{-1}).

### Anchor gate and cross-instrument assumption

The original external protocol's A0 map says it “assumes ID-X NCE equals IQ-X NCE” (`MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md` §2). The later confirmation record explicitly reports the absolute-agreement anchor gate failed under A0, A1, and A2 by narrow margins: A0 NCE20 median |Δμ| 0.0501 against 0.05; A1 pooled RMSD 0.0811 against 0.08; A2 NCE20 median 0.0506 (`MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md` §9; `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` §7). The final comparative study proceeded under A0 only. This is separate from the 33-compound Design A study, whose adjusted contrasts crossed zero and whose decision was `INTERFACE_UNRESOLVED`.

Phase 4 mentions a nonphysical map and unresolved interface but does not prominently report the ID-X=IQ-X assumption and failed absolute-agreement gate. A reader should be told that the comparative error analysis was carried out under this frozen input convention, while absolute trajectory agreement was not established by the anchor gate.

## What can be concluded without physical adjudication

1. The fixed models can be scored against the frozen measured endpoint at the selected numeric rung labels using the published calculation and frozen adapter.
2. The candidate/reference contrast and scaffold bootstrap are conditional on those numeric labels, population, support rule, model artifacts, and map.
3. This supports a computational comparison on a separately sampled external dataset, subject to the documented exposure history.
4. It does not establish physical equivalence of collision energy across the IQ-X and ID-X records, universal NCE/eV conversion, calibrated cross-instrument trajectory transfer, or convention-independent comparator ranking.
5. The endpoint is a scalar precursor-including intensity-weighted mass statistic, not a measure of bond cleavage, a mechanistic assignment, or complete spectral prediction.

## Questions for the external specialist

Please answer only where the supplied records support an answer, and identify the source file or manual/version used for each conclusion.

1. **WUR unit semantics:** For the cited WUR IQ-X publication and the local acquisition metadata/filter strings, do the WUR values 15/30/45/60/75/90 and stepped 25/38/59 denote normalized HCD/SCE settings? Does the generic exported `Collision_energy` field retain any convention marker, or must the interpretation be attached from the publication/method?
2. **MSnLib paper versus archive records:** The MSnLib primary paper describes 20 eV and 60 eV MS2 settings, whereas the MURU protocol labels the sampled numeric rungs NCE 20 and 60. Can the nine exact mzML archive sources in `msnlib_design.ZIPS` be mapped to the paper's acquisition method? For each archive, do native instrument method records establish normalized (%) or absolute (V/eV) HCD mode?
3. **Instrument-method semantics:** Which specific Orbitrap ID-X software/method versions were used in those source runs? What native Thermo fields or method files reliably discriminate NCE percentage from absolute voltage in the corresponding mzML/export?
4. **Cross-instrument relationship:** If both instruments used NCE, does that alone establish equivalent deposited energy or comparable fragmentation response for this compound/mass/charge distribution? What calibration or matched-compound experiment would be needed to support a physical transfer claim?
5. **Interpretation of the affine bridge:** Is there a scientifically defensible physical interpretation for (T(E)= -5.95552603907965 + 0.8618030610784555E) from the available acquisition records? If not, confirm that it should remain described strictly as an empirical coordinate adapter.
6. **Anchor gate:** Does the narrow failure of the predeclared absolute-agreement anchor gate at A0/A1/A2 rule out an absolute trajectory-transfer claim while leaving the preplanned paired model-comparison calculation interpretable under A0? Identify any additional qualification required.
7. **Safe terminology:** Given the evidence, should the manuscript use “numeric collision-energy rung,” “nominal instrument setting,” “NCE,” “eV,” or another term for the external 20/60 records until source-specific methods are recovered?

## Recommended manuscript correction before external circulation

Replace unqualified “MSnLib HCD NCE 20 and 60” and “not values in eV” with a bounded statement such as:

> The frozen external analysis selected MS2 records with numeric collision-energy values 20 and 60. Project protocols refer to these as NCE rungs, but the MSnLib primary paper describes its library acquisition at 20 and 60 eV. The available frozen archive records do not resolve whether every source file in the sampled evaluation used normalized or absolute HCD energy. The affine adapter therefore defines a fixed computational input convention; it is not evidence of physical cross-instrument calibration.

Also disclose the failed absolute-agreement anchor gate and the explicit ID-X=IQ-X NCE-semantics assumption. If source-specific method evidence later resolves the unit conflict, revise the passage with archive IDs, method/version details, and hashes. Retain the distinction between (a) numeric reproducibility of the model comparison and (b) physical interpretation of the energy coordinate.

## Source index

| Evidence | Repository location / stable source | Use in review |
|---|---|---|
| Unitless WUR energy field parser | `src/muru/energy.py::CollisionEnergy`, `parse_collision_energy` | Shows bare record numeric has no unit; NCE is publication-derived assumption. |
| Frozen LCSB→WUR development mapping | `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` §2; `src/muru/wur_v2/population.py`; `src/muru/wur_bridge.py` | Establishes forward map direction and coefficients. |
| Frozen external inverse | `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` §2; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md` §3; `src/muru/wur_v2/external_msnlib.py::adapter_energy` | Establishes external numeric transform and absence of fitted parameters. |
| Numeric rung selection | `src/muru/wur_v2/external_msnlib.py::fixed_rung_scans`; `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv` | Header values matched numerically; selection code has no unit conversion. |
| Nine archive design | `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` §6; `src/muru/wur_v2/msnlib_design.py::ZIPS`; `MSnLib_required_mzML_downloads.csv` | Needed for method-file provenance audit. |
| Gate failure / A0 assumption | `MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md` §2; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md` §9 | Records cross-instrument NCE equality assumption and failed anchor thresholds. |
| MSnLib primary acquisition description | Brungs et al. 2025, DOI `10.1038/s41592-025-02813-0` | Reports 20/60 eV in the public library's MS2 method. |
| Thermo available modes | Orbitrap ID-X Method Editor Help, Activation parameters | Establishes normalized-% and absolute-voltage choices exist; not which was used historically. |

**Review status:** The issue is not resolved by this packet. It documents the discrepancy for expert examination and prevents the manuscript from asserting a unit interpretation that the accessible source artifacts do not establish.
